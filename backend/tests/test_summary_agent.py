import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.services.summary_agent import SummaryOptions, build_article_text, clean_model_output, summarize_with_provider


class FakeChatCompletions:
    def create(self, **kwargs):
        self.kwargs = kwargs
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content="<think>内部推理不应出现在结果里</think>\n一句话概览：本地 RSS 阅读器支持 AI 摘要。\n\n关键要点：\n- 支持 provider 切换\n- 记录 token 用量"
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


class SequencedChatCompletions:
    def __init__(self):
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        content = "最终整篇摘要：覆盖所有片段。\n\n可信度：高"
        if len(self.calls) == 1:
            content = "片段笔记 A：开头事实。"
        elif len(self.calls) == 2:
            content = "片段笔记 B：结尾事实。"
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=content))],
            usage=SimpleNamespace(prompt_tokens=100 + len(self.calls), completion_tokens=20 + len(self.calls)),
        )


class SequencedOpenAI:
    last_chat = None

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        SequencedOpenAI.last_chat = SequencedChatCompletions()
        self.chat = SimpleNamespace(completions=SequencedOpenAI.last_chat)


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
            result = summarize_with_provider(article, provider, SummaryOptions(mode="deep", language="zh", max_words=600))

        self.assertIn("本地 RSS 阅读器", result.text)
        self.assertNotIn("<think>", result.text)
        self.assertIn("agentic workflow", result.prompt)
        self.assertEqual(result.usage.input_tokens, 321)
        self.assertEqual(result.usage.output_tokens, 88)
        self.assertEqual(FakeOpenAI.last_chat.kwargs["model"], "Qwen/Qwen3-8B")
        self.assertEqual(FakeOpenAI.last_chat.kwargs["max_tokens"], 1080)

    def test_summarize_with_provider_disables_ollama_qwen_reasoning_output(self):
        article = {"title": "Ollama 摘要", "cleaned_markdown": "这是一篇测试文章。"}
        provider = {
            "name": "Local Ollama Qwen3 8B",
            "provider_type": "ollama",
            "base_url": "http://127.0.0.1:11434/v1",
            "api_key": "ollama",
            "model": "qwen3:8b",
            "enabled": True,
        }

        with patch("app.services.summary_agent.OpenAI", FakeOpenAI):
            summarize_with_provider(article, provider)

        self.assertEqual(FakeOpenAI.last_chat.kwargs["reasoning_effort"], "none")

    def test_long_article_runs_chunk_then_final_summary_loop(self):
        article = {
            "title": "Long context article",
            "cleaned_markdown": "\n\n".join(
                [
                    "第一部分：" + ("开头事实 " * 120),
                    "第二部分：" + ("结尾事实 " * 120),
                ]
            ),
        }
        provider = {
            "name": "Local Ollama Qwen3 8B",
            "provider_type": "ollama",
            "base_url": "http://127.0.0.1:11434/v1",
            "api_key": "ollama",
            "model": "qwen3:8b",
            "enabled": True,
        }
        options = SummaryOptions(
            mode="structured",
            language="zh",
            max_words=160,
            context_window_tokens=900,
            chunk_token_budget=180,
            chunk_overlap_tokens=0,
        )

        with patch("app.services.summary_agent.OpenAI", SequencedOpenAI):
            result = summarize_with_provider(article, provider, options)

        self.assertGreaterEqual(len(SequencedOpenAI.last_chat.calls), 3)
        self.assertIn("最终整篇摘要", result.text)
        self.assertIn("多轮上下文摘要流程", result.prompt)
        self.assertIn("chunk 1/", result.prompt)
        self.assertIn("final merge", result.prompt)
        self.assertGreater(result.usage.input_tokens, 300)

    def test_long_article_emits_real_agent_progress_events(self):
        article = {
            "title": "Long context article",
            "cleaned_markdown": "\n\n".join(
                [
                    "第一部分：" + ("开头事实 " * 120),
                    "第二部分：" + ("结尾事实 " * 120),
                ]
            ),
        }
        provider = {
            "name": "Local Ollama Qwen3 8B",
            "provider_type": "ollama",
            "base_url": "http://127.0.0.1:11434/v1",
            "api_key": "ollama",
            "model": "qwen3:8b",
            "enabled": True,
        }
        options = SummaryOptions(
            mode="structured",
            language="zh",
            max_words=160,
            context_window_tokens=900,
            chunk_token_budget=180,
            chunk_overlap_tokens=0,
        )
        events = []

        with patch("app.services.summary_agent.OpenAI", SequencedOpenAI):
            summarize_with_provider(article, provider, options, on_event=events.append)

        event_types = [event["type"] for event in events]
        self.assertIn("prepare", event_types)
        self.assertIn("budget", event_types)
        self.assertIn("chunk_plan", event_types)
        self.assertIn("chunk_start", event_types)
        self.assertIn("chunk_done", event_types)
        self.assertIn("final_start", event_types)
        self.assertIn("final_done", event_types)
        self.assertGreaterEqual(event_types.count("chunk_start"), 2)

    def test_clean_model_output_removes_qwen_thinking_blocks(self):
        text = clean_model_output("<think>分析过程</think>\n最终答案：摘要正文")

        self.assertEqual(text, "摘要正文")


if __name__ == "__main__":
    unittest.main()
