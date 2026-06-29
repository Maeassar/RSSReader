import unittest
from unittest.mock import patch

from app.services.translation_agent import TranslationResult, TranslationUsage


class FakeTranslationRepository:
    def __init__(self):
        self.translation_provider_ids = []
        self.llm_provider_ids = []

    def get_article(self, article_id):
        return {"id": article_id, "title": "Article", "cleaned_markdown": "Hello world."}

    def get_translation_provider(self, provider_id):
        self.translation_provider_ids.append(provider_id)
        return {
            "id": provider_id,
            "name": "Dedicated Translation Provider",
            "provider_type": "openai_compatible",
            "base_url": "https://translation.example/v1",
            "api_key": "test-key",
            "model": "hy-mt2-pro",
            "enabled": True,
            "is_default": True,
        }

    def get_translation_llm_provider(self):
        return self.get_translation_provider(99)

    def get_llm_provider(self, provider_id):
        self.llm_provider_ids.append(provider_id)
        raise AssertionError("translation flow must not read llm_providers")

    def get_latest_ai_result(self, article_id, task_type):
        return None

    def create_ai_result(self, article_id, task_type, prompt, result, **kwargs):
        return {
            "id": 1,
            "entry_id": article_id,
            "task_type": task_type,
            "prompt": prompt,
            "result": result,
            "provider": kwargs.get("provider"),
            "model": kwargs.get("model"),
            "input_tokens": kwargs.get("input_tokens", 0),
            "output_tokens": kwargs.get("output_tokens", 0),
            "status": kwargs.get("status", "success"),
        }


class AIServiceTranslationProviderTest(unittest.TestCase):
    def test_article_translation_uses_dedicated_translation_provider_by_id(self):
        from app.services import ai_service

        fake_repository = FakeTranslationRepository()
        fake_result = TranslationResult(
            text="你好，世界。",
            usage=TranslationUsage(input_tokens=3, output_tokens=4),
            prompt="目标语言：中文\nPrompt trace",
            aligned_blocks=[{"type": "paragraph", "original": "Hello world.", "translated": "你好，世界。"}],
        )

        with patch.object(ai_service, "repository", fake_repository), patch.object(
            ai_service, "translate_with_provider", return_value=fake_result
        ) as translate_mock:
            saved = ai_service.translate(1, provider_id=42, refresh=True)

        self.assertEqual(fake_repository.translation_provider_ids, [42])
        self.assertEqual(fake_repository.llm_provider_ids, [])
        self.assertEqual(saved["provider"], "Dedicated Translation Provider")
        self.assertEqual(saved["model"], "hy-mt2-pro")
        translate_mock.assert_called_once()

    def test_segment_translation_uses_dedicated_translation_provider_by_id(self):
        from app.services import ai_service

        fake_repository = FakeTranslationRepository()
        fake_result = TranslationResult(
            text="你好。",
            usage=TranslationUsage(input_tokens=1, output_tokens=2),
            prompt="segment prompt",
        )

        with patch.object(ai_service, "repository", fake_repository), patch.object(
            ai_service, "translate_segment_with_provider", return_value=fake_result
        ) as translate_mock:
            result = ai_service.translate_segment("Hello.", provider_id=7)

        self.assertEqual(fake_repository.translation_provider_ids, [7])
        self.assertEqual(fake_repository.llm_provider_ids, [])
        self.assertEqual(result["text"], "你好。")
        translate_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
