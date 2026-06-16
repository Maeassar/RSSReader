import os
import tempfile
import unittest
from pathlib import Path


class AIRagConfigTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"
        os.environ["RSSREADER_DB_PATH"] = str(self.db_path)

        from app import database
        database.DB_PATH = self.db_path
        database.initialize_database()

    def tearDown(self):
        os.environ.pop("RSSREADER_DB_PATH", None)
        self.temp_dir.cleanup()

    def test_rag_chat_uses_shared_ai_provider_config(self):
        from app.schemas import LLMProviderCreate
        from app.repositories.sqlite_repository import SQLiteRepository
        from app.services.rag_service import get_chat_provider_config

        repository = SQLiteRepository()
        repository.create_llm_provider(
            LLMProviderCreate(
                name="Shared Qwen",
                provider_type="ollama",
                base_url="http://127.0.0.1:11434/v1",
                api_key="ollama",
                model="qwen3:8b",
                enabled=True,
                is_default=True,
            )
        )

        provider = get_chat_provider_config()

        self.assertEqual(provider["name"], "Shared Qwen")
        self.assertEqual(provider["base_url"], "http://127.0.0.1:11434/v1")
        self.assertEqual(provider["api_key"], "ollama")
        self.assertEqual(provider["model"], "qwen3:8b")
        self.assertTrue(provider["enabled"])

    def test_rag_embedding_api_key_is_encrypted_at_rest(self):
        from app.database import get_connection
        from app.routers.rag import RagConfig, get_rag_config, save_rag_config

        save_rag_config(
            RagConfig(
                siliconflow_api_key="sf-secret",
                siliconflow_base_url="https://api.siliconflow.cn/v1",
                embedding_model="BAAI/bge-m3",
                embedding_dim=1024,
            )
        )

        cfg = get_rag_config()
        self.assertEqual(cfg.siliconflow_api_key, "")
        self.assertTrue(cfg.has_siliconflow_api_key)

        with get_connection() as conn:
            stored_api_key = conn.execute(
                "SELECT value FROM app_config WHERE key = 'rag_siliconflow_api_key'"
            ).fetchone()["value"]

        self.assertNotEqual(stored_api_key, "sf-secret")
        self.assertTrue(stored_api_key.startswith("enc:v1:"))


if __name__ == "__main__":
    unittest.main()
