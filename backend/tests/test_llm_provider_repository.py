import os
import tempfile
import unittest
from datetime import datetime, timedelta


class LLMProviderRepositoryTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old_db_path = os.environ.get("RSSREADER_DB_PATH")
        os.environ["RSSREADER_DB_PATH"] = os.path.join(self.tmp.name, "rssreader-test.db")

        import app.database as database
        import app.repositories.sqlite_repository as sqlite_repository

        database.DB_PATH = database.Path(os.environ["RSSREADER_DB_PATH"])
        sqlite_repository.repository = sqlite_repository.SQLiteRepository()
        self.repository = sqlite_repository.repository

        with database.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO feeds (url, title, created_at, updated_at)
                VALUES ('https://example.com/feed.xml', 'Example Feed', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """
            )
            conn.execute(
                """
                INSERT INTO entries (feed_id, guid, title, link, summary, created_at)
                VALUES (1, 'entry-1', 'Provider Test', 'https://example.com/a', 'Body', CURRENT_TIMESTAMP)
                """
            )

    def tearDown(self):
        if self.old_db_path is None:
            os.environ.pop("RSSREADER_DB_PATH", None)
        else:
            os.environ["RSSREADER_DB_PATH"] = self.old_db_path
        self.tmp.cleanup()

    def test_provider_crud_and_usage_stats(self):
        from app.schemas import LLMProviderCreate

        provider = self.repository.create_llm_provider(
            LLMProviderCreate(
                name="Local Ollama",
                provider_type="ollama",
                base_url="http://127.0.0.1:11434/v1/",
                api_key="ollama",
                model="qwen3:8b",
                enabled=True,
                is_default=True,
            )
        )

        self.assertEqual(provider["base_url"], "http://127.0.0.1:11434/v1")
        self.assertTrue(provider["is_default"])
        self.assertTrue(provider["has_api_key"])

        default_provider = self.repository.get_default_llm_provider()
        self.assertEqual(default_provider["name"], "Local Ollama")
        self.assertEqual(default_provider["api_key"], "ollama")

        import app.database as database

        with database.get_connection() as conn:
            stored_api_key = conn.execute(
                "SELECT api_key FROM llm_providers WHERE id = ?",
                (provider["id"],),
            ).fetchone()["api_key"]

        self.assertNotEqual(stored_api_key, "ollama")
        self.assertTrue(stored_api_key.startswith("enc:v1:"))

        self.repository.create_ai_result(
            1,
            "summary",
            "prompt",
            "result",
            provider="Local Ollama",
            model="qwen3:8b",
            input_tokens=42,
            output_tokens=12,
        )

        stats = self.repository.stats()
        self.assertEqual(stats["total_calls"], 1)
        self.assertEqual(stats["input_tokens"], 42)
        self.assertEqual(stats["output_tokens"], 12)
        self.assertEqual(stats["by_feature"][0]["name"], "summary")
        self.assertEqual(stats["by_provider"][0]["provider"], "Local Ollama")

    def test_sync_logs_can_be_filtered_by_range(self):
        today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")

        import app.database as database

        with database.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO feed_fetch_logs (feed_id, url, status, message, fetched_at)
                VALUES (1, 'https://example.com/feed.xml', 'success', 'today log', ?)
                """,
                (today,),
            )
            conn.execute(
                """
                INSERT INTO feed_fetch_logs (feed_id, url, status, message, fetched_at)
                VALUES (1, 'https://example.com/feed.xml', 'success', 'old log', ?)
                """,
                (yesterday,),
            )

        today_logs = self.repository.list_logs("today")
        all_logs = self.repository.list_logs("all")

        self.assertEqual([log["message"] for log in today_logs], ["today log"])
        self.assertEqual({log["message"] for log in all_logs}, {"today log", "old log"})


if __name__ == "__main__":
    unittest.main()
