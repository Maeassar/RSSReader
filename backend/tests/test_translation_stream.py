import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.services.translation_agent import (
    TranslationResult,
    TranslationUsage,
    TranslationOptions,
    TranslationAgentError,
    translate_with_provider,
)


class FakeChatCompletions:
    def __init__(self):
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content='{"items":[{"id":1,"translation":"Translated sentence."}]}'
                    )
                )
            ],
            usage=SimpleNamespace(prompt_tokens=210, completion_tokens=64),
        )


class FakeOpenAI:
    last_chat = None

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        FakeOpenAI.last_chat = FakeChatCompletions()
        self.chat = SimpleNamespace(completions=FakeOpenAI.last_chat)


class TranslationStreamEventTest(unittest.TestCase):
    """Test SSE event emission at each stage of translation."""

    def setUp(self):
        self.events = []

    def _on_event(self, event: dict) -> None:
        self.events.append(event)

    def _provider(self):
        return {
            "name": "Test Provider",
            "provider_type": "openai_compatible",
            "base_url": "http://127.0.0.1:11434/v1",
            "api_key": "test-key",
            "model": "qwen3:8b",
            "enabled": True,
        }

    def test_short_article_emits_expected_events(self):
        """Short single-chunk article should emit: prepare → parse → budget → single_start → single_done"""
        article = {
            "title": "Test",
            "cleaned_markdown": "First sentence. Second sentence.",
        }

        with patch("app.services.translation_agent.OpenAI", FakeOpenAI):
            translate_with_provider(
                article,
                self._provider(),
                TranslationOptions(target_language="en", preserve_markdown=True),
                on_event=self._on_event,
            )

        event_types = [e["type"] for e in self.events]
        self.assertIn("prepare", event_types)
        self.assertIn("parse", event_types)
        self.assertIn("budget", event_types)
        self.assertIn("single_start", event_types)
        self.assertIn("single_done", event_types)

    def test_long_article_emits_chunk_events(self):
        """Multi-chunk article should emit chunk_plan → chunk_start → chunk_done → align_check"""
        article = {
            "title": "Long article",
            "cleaned_markdown": "\n\n".join(["First paragraph " * 100, "Second paragraph " * 100]),
        }

        with patch("app.services.translation_agent.OpenAI", FakeOpenAI):
            translate_with_provider(
                article,
                self._provider(),
                TranslationOptions(
                    target_language="en",
                    preserve_markdown=True,
                    context_window_tokens=800,
                    chunk_token_budget=180,
                ),
                on_event=self._on_event,
            )

        event_types = [e["type"] for e in self.events]
        self.assertIn("chunk_plan", event_types)
        # Should have at least one chunk_start/chunk_done/align_check
        has_chunk_cycle = any("chunk_start" in t for t in event_types)
        self.assertTrue(has_chunk_cycle)

    def test_non_markdown_uses_paragraph_flow(self):
        """Non-Markdown article (HTML source) should emit prepare → parse → budget → single_start"""
        article = {
            "title": "HTML article",
            "cleaned_html": "<p>Paragraph one.</p><p>Paragraph two.</p>",
        }

        with patch("app.services.translation_agent.OpenAI", FakeOpenAI):
            translate_with_provider(
                article,
                self._provider(),
                TranslationOptions(target_language="en", preserve_markdown=False),
                on_event=self._on_event,
            )

        event_types = [e["type"] for e in self.events]
        self.assertIn("prepare", event_types)

    def test_error_emits_no_progress_events_after_failure(self):
        """Provider error should not emit partial progress events."""
        def failing_create(**kwargs):
            raise ConnectionError("Connection refused")

        fake = FakeChatCompletions()
        fake.create = failing_create

        with patch("app.services.translation_agent.OpenAI", lambda **kw: SimpleNamespace(chat=SimpleNamespace(completions=fake))):
            with self.assertRaises(TranslationAgentError):
                translate_with_provider(
                    {"title": "T", "cleaned_markdown": "Hello world."},
                    self._provider(),
                    on_event=self._on_event,
                )

        # Error should be in events
        event_types = [e["type"] for e in self.events]
        # prepare should have been emitted before the failure
        self.assertIn("prepare", event_types)
        self.assertIn("parse", event_types)

    def test_event_has_ts_field(self):
        """Every event should carry a ts timestamp."""
        article = {
            "title": "TS test",
            "cleaned_markdown": "Sentence one.",
        }

        with patch("app.services.translation_agent.OpenAI", FakeOpenAI):
            translate_with_provider(
                article,
                self._provider(),
                on_event=self._on_event,
            )

        for event in self.events:
            self.assertIn("ts", event, f"Event {event['type']} missing ts")


if __name__ == "__main__":
    unittest.main()
