import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.services.tag_agent import TagAgentError, parse_tag_candidates, suggest_tags_with_provider


EXISTING_TAGS = [
    {"id": 1, "name": "AI", "color": "#8b5cf6"},
    {"id": 2, "name": "Engineering", "color": "#10b981"},
]


class FakeTagChatCompletions:
    def create(self, **kwargs):
        self.kwargs = kwargs
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content='{"candidates":['
                        '{"name":"AI","tag_id":1,"reason":"The article discusses model behavior."},'
                        '{"name":"Engineering","tag_id":2,"reason":"Implementation details are central."},'
                        '{"name":"RSS","reason":"RSS reader workflow."},'
                        '{"name":"Automation","reason":"Automated tagging is relevant."},'
                        '{"name":"Local Models","reason":"Mentions local providers."},'
                        '{"name":"AI","tag_id":1,"reason":"Duplicate should be removed."}'
                        "]}"
                    )
                )
            ],
            usage=SimpleNamespace(prompt_tokens=123, completion_tokens=45),
        )


class FakeOpenAI:
    last_chat = None

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        FakeOpenAI.last_chat = FakeTagChatCompletions()
        self.chat = SimpleNamespace(completions=FakeOpenAI.last_chat)


class TagAgentTest(unittest.TestCase):
    def test_parse_tag_candidates_matches_existing_tags_and_deduplicates(self):
        candidates = parse_tag_candidates(
            {
                "candidates": [
                    {"name": "ai", "reason": "existing"},
                    {"name": "New Topic", "reason": "new"},
                    {"name": "AI", "reason": "duplicate"},
                    {"name": "Engineering"},
                    {"name": "RSS"},
                    {"name": "Automation"},
                ]
            },
            EXISTING_TAGS,
        )

        self.assertEqual([item.name for item in candidates], ["AI", "New Topic", "Engineering", "RSS", "Automation"])
        self.assertEqual(candidates[0].tag_id, 1)
        self.assertEqual(candidates[2].tag_id, 2)

    def test_parse_tag_candidates_allows_fewer_than_five_candidates(self):
        candidates = parse_tag_candidates('{"candidates":[{"name":"AI"}]}', EXISTING_TAGS)

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].name, "AI")
        self.assertEqual(candidates[0].tag_id, 1)

    def test_parse_tag_candidates_limits_to_first_eight_usable_candidates(self):
        payload = {"candidates": [{"name": f"Topic {index}"} for index in range(1, 12)]}

        candidates = parse_tag_candidates(payload, EXISTING_TAGS)

        self.assertEqual(len(candidates), 8)
        self.assertEqual(candidates[-1].name, "Topic 8")

    def test_suggest_tags_with_provider_uses_openai_compatible_client_and_usage(self):
        article = {"title": "AI tagging", "cleaned_markdown": "Use AI to suggest RSS article tags."}
        provider = {
            "name": "Local Ollama",
            "provider_type": "ollama",
            "base_url": "http://127.0.0.1:11434/v1",
            "api_key": "",
            "model": "qwen3:8b",
            "enabled": True,
        }

        with patch("app.services.tag_agent.OpenAI", FakeOpenAI):
            result = suggest_tags_with_provider(article, EXISTING_TAGS, provider)

        self.assertEqual(len(result.candidates), 5)
        self.assertEqual(result.candidates[0].name, "AI")
        self.assertEqual(result.candidates[0].tag_id, 1)
        self.assertIn("Suggest up to 8 candidate tags", result.prompt)
        self.assertEqual(result.usage.input_tokens, 123)
        self.assertEqual(result.usage.output_tokens, 45)
        self.assertEqual(FakeOpenAI.last_chat.kwargs["model"], "qwen3:8b")
        self.assertEqual(FakeOpenAI.last_chat.kwargs["reasoning_effort"], "none")


if __name__ == "__main__":
    unittest.main()
