import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.services.summary_agent import build_article_text, summarize_with_provider


class FakeChatCompletions:
    def create(self, **kwargs):
        self.kwargs = kwargs
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content="一句话概览：本地 RSS 阅读器支持 AI 摘要。\n\n关键要点：\n- 支持 provider 切换\n- 记录 token 用量"
                    )
                )
            ],
            usage=SimpleNamespace(prompt_tokens=321, completion_tokens=88),
        )


class FakeOpenAI:
    last_chat = None

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        FakeOpenAI.last_chat = FakeChatCompletions()
        self.chat = SimpleNamespace(completions=FakeOpenAI.last_chat)


class SummaryAgentTest(unittest.TestCase):
    def test_build_article_text_prefers_cleaned_markdown(self):
        article = {
            "title": "Summary Agent",
            "summary": "rss summary",
            "cleaned_markdown": "# Heading\n\n正文内容",
            "cleaned_html": "<p>html content</p>",
        }

        text = build_article_text(article)

        self.assertIn("Summary Agent", text)
        self.assertIn("正文内容", text)
        self.assertNotIn("html content", text)

    def test_summarize_with_provider_uses_openai_compatible_client_and_usage(self):
        article = {"title": "Qwen 摘要", "cleaned_markdown": "这是一篇测试文章。"}
        provider = {
            "name": "Local vLLM Qwen3-8B",
            "provider_type": "vllm",
            "base_url": "http://127.0.0.1:8000/v1",
            "api_key": "",
            "model": "Qwen/Qwen3-8B",
            "enabled": True,
        }

        with patch("app.services.summary_agent.OpenAI", FakeOpenAI):
            result = summarize_with_provider(article, provider)

        self.assertIn("本地 RSS 阅读器", result.text)
        self.assertEqual(result.usage.input_tokens, 321)
        self.assertEqual(result.usage.output_tokens, 88)
        self.assertEqual(FakeOpenAI.last_chat.kwargs["model"], "Qwen/Qwen3-8B")


if __name__ == "__main__":
    unittest.main()
