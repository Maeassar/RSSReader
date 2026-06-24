import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.services.translation_agent import (
    Block,
    CancelEvent,
    Sentence,
    TranslationAgentError,
    TranslationCancelled,
    TranslationOptions,
    TranslationResult,
    build_translation_prompt,
    build_translation_source,
    extract_aligned_blocks_from_prompt,
    parse_blocks,
    split_sentences,
    _encode_prompt_with_aligned,
    _pack_aligned_chunks,
    _parse_aligned_response,
    _reassemble_translation,
    _build_aligned_prompt,
    translate_with_provider,
)


class BlockParsingTest(unittest.TestCase):
    """Test Step A: parse_blocks"""

    def test_heading_detected(self):
        blocks = parse_blocks("## My Title\n\nParagraph here.")
        self.assertGreaterEqual(len(blocks), 1)
        self.assertEqual(blocks[0].type, "heading")
        self.assertEqual(blocks[0].prefix, "## ")
        self.assertEqual(blocks[0].content, "My Title")

    def test_paragraph_detected(self):
        blocks = parse_blocks("First paragraph.\n\nSecond paragraph.")
        self.assertEqual(blocks[0].type, "paragraph")
        self.assertEqual(blocks[2].type, "paragraph")

    def test_list_item_preserves_indent(self):
        blocks = parse_blocks("  - item one\n  - item two")
        self.assertGreaterEqual(len(blocks), 1)
        self.assertEqual(blocks[0].type, "list_item")
        self.assertIn("  - ", blocks[0].prefix)

    def test_blockquote_prefix_preserved(self):
        blocks = parse_blocks("> quoted text")
        self.assertEqual(blocks[0].type, "blockquote")
        self.assertEqual(blocks[0].prefix, "> ")
        self.assertEqual(blocks[0].content, "quoted text")

    def test_code_block_not_translatable(self):
        blocks = parse_blocks("before\n```python\ncode here\n```\nafter")
        code_blocks = [b for b in blocks if b.type == "code_block"]
        self.assertGreaterEqual(len(code_blocks), 1)
        self.assertEqual(code_blocks[0].content, "")

    def test_hr_detected(self):
        blocks = parse_blocks("before\n---\nafter")
        hr_blocks = [b for b in blocks if b.type == "hr"]
        self.assertEqual(len(hr_blocks), 1)

    def test_blank_line(self):
        blocks = parse_blocks("a\n\nb")
        blank_blocks = [b for b in blocks if b.type == "blank"]
        self.assertEqual(len(blank_blocks), 1)

    def test_empty_markdown(self):
        blocks = parse_blocks("")
        self.assertEqual(blocks, [])

    def test_mixed_structure(self):
        md = "# Title\n\nIntro paragraph.\n\n## Section 1\n\n- first\n- second\n\n> quote\n\n```js\nvar x = 1;\n```\n\nFinal."
        blocks = parse_blocks(md)
        types = [b.type for b in blocks]
        self.assertIn("heading", types)
        self.assertIn("paragraph", types)
        self.assertIn("list_item", types)
        self.assertIn("blockquote", types)
        self.assertIn("code_block", types)


class SentenceSplittingTest(unittest.TestCase):
    """Test Step B: split_sentences"""

    def test_basic_sentences(self):
        sents = split_sentences("First sentence. Second sentence! Third?")
        self.assertEqual(len(sents), 3)
        self.assertIn("First sentence", sents[0].text)

    def test_chinese_sentences(self):
        sents = split_sentences("第一句。第二句！第三句？")
        self.assertEqual(len(sents), 3)

    def test_abbreviation_not_split(self):
        sents = split_sentences("I live in the U.S. and love it.")
        # Should be 1 sentence, not split at "U.S."
        self.assertEqual(len(sents), 1)

    def test_decimal_not_split(self):
        sents = split_sentences("Value is 3.14 and pi is 3.14.")
        self.assertEqual(len(sents), 1)

    def test_empty_content(self):
        sents = split_sentences("")
        self.assertEqual(sents, [])

    def test_markdown_inline_content(self):
        sents = split_sentences("This has **bold** and `code`. That is fine.")
        self.assertEqual(len(sents), 2)


class ChunkPackingTest(unittest.TestCase):
    """Test Step C: _pack_aligned_chunks"""

    def test_does_not_cross_block_boundary(self):
        blocks = [
            Block("heading", "## ", "Title", "## Title"),
            Block("paragraph", "", "First sentence here. Second sentence there.", ""),
            Block("heading", "### ", "Sub", "### Sub"),
        ]
        chunks = _pack_aligned_chunks(blocks, token_budget=30000)
        # Each block's sentences should be in separate chunks
        block_indices = set(c.block_index for c in chunks)
        self.assertIn(0, block_indices)
        self.assertIn(1, block_indices)
        self.assertIn(2, block_indices)

    def test_code_blocks_skipped(self):
        blocks = [
            Block("paragraph", "", "Hello world.", ""),
            Block("code_block", "", "", "code"),
        ]
        chunks = _pack_aligned_chunks(blocks, token_budget=30000)
        self.assertEqual(len(chunks), 1)

    def test_hr_and_blank_skipped(self):
        blocks = [
            Block("paragraph", "", "Some text.", ""),
            Block("hr", "", "", "---"),
            Block("blank", "", "", ""),
        ]
        chunks = _pack_aligned_chunks(blocks, token_budget=30000)
        self.assertEqual(len(chunks), 1)


class AlignedPromptTest(unittest.TestCase):
    """Test Step D: _build_aligned_prompt"""

    def test_line_number_format(self):
        class FakeChunk:
            block_index = 1
            sentences = [
                Sentence(0, "First sentence."),
                Sentence(1, "Second sentence."),
            ]

        system_prompt, user_prompt = _build_aligned_prompt(
            {"title": "Test"},
            FakeChunk(),
            TranslationOptions(target_language="en"),
        )
        self.assertIn("|1| First sentence.", user_prompt)
        self.assertIn("|2| Second sentence.", user_prompt)
        self.assertIn("严格逐行翻译", system_prompt)
        self.assertIn("2 行", system_prompt)


class AlignedResponseParsingTest(unittest.TestCase):
    """Test Step F: _parse_aligned_response"""

    def test_parse_valid_response(self):
        response = "|1| First translated\n|2| Second translated\n"
        result = _parse_aligned_response(response, 2)
        self.assertIsNotNone(result)
        if result:
            self.assertEqual(result[0], "First translated")
            self.assertEqual(result[1], "Second translated")

    def test_parse_with_blank_lines(self):
        response = "|1| First\n\n|2| Second\n"
        result = _parse_aligned_response(response, 2)
        self.assertIsNotNone(result)

    def test_too_few_lines_returns_none(self):
        response = "|1| Only one line\n"
        result = _parse_aligned_response(response, 3)
        self.assertIsNone(result)

    def test_empty_translation_line_returns_none(self):
        """An empty |N| line means the model skipped it — alignment failed."""
        result = _parse_aligned_response("|1| first\n|2| \n|3| third", 3)
        self.assertIsNone(result)

    def test_no_70pct_partial_fill(self):
        """Regression: previously 70% threshold returned a list with empty strings,
        which injected blank lines into the translation. Must return None instead."""
        result = _parse_aligned_response("|1| a\n|2| b\n|3| c\n|4| d", 5)
        self.assertIsNone(result)


class SentenceSplittingEdgeCasesTest(unittest.TestCase):
    """Regression tests for sentence boundary detection."""

    def test_period_at_end_of_text_no_space(self):
        """Period at end of text (no trailing space) must still end the sentence."""
        sents = split_sentences("End here.")
        self.assertEqual(len(sents), 1)
        self.assertEqual(sents[0].text, "End here.")

    def test_decimal_at_end_of_sentence(self):
        """3.14 inside a sentence must not be split, but trailing period ends it."""
        sents = split_sentences("Value 3.14 is pi.")
        self.assertEqual(len(sents), 1)
        self.assertIn("3.14", sents[0].text)

    def test_period_followed_by_space(self):
        sents = split_sentences("Hello. World continues")
        self.assertEqual(len(sents), 2)
        self.assertEqual(sents[0].text, "Hello.")

    def test_exclamation_at_end(self):
        sents = split_sentences("Wow! Next sentence here.")
        self.assertEqual(len(sents), 2)


class EmptyAlignedChunksTest(unittest.TestCase):
    """Regression: article with only code blocks used to crash with IndexError."""

    def setUp(self):
        from types import SimpleNamespace

        class FakeChat:
            def create(self, **kwargs):
                return SimpleNamespace(
                    choices=[SimpleNamespace(message=SimpleNamespace(content="|1| x"))],
                    usage=SimpleNamespace(prompt_tokens=10, completion_tokens=5),
                )

        class FakeOpenAI:
            def __init__(self, **kwargs):
                self.chat = SimpleNamespace(completions=FakeChat())

        self.FakeOpenAI = FakeOpenAI

    def _provider(self):
        return {
            "name": "p", "provider_type": "openai_compatible",
            "base_url": "http://x/v1", "model": "m", "enabled": True,
        }

    def test_code_only_article_does_not_crash(self):
        from unittest.mock import patch
        article = {"title": "T", "cleaned_markdown": "```python\nprint(1)\n```"}
        with patch("app.services.translation_agent.OpenAI", self.FakeOpenAI):
            result = translate_with_provider(article, self._provider(), TranslationOptions())
        # Should return the original code block as-is, not crash
        self.assertIn("print(1)", result.text)
        # No model call should have been made
        self.assertEqual(result.usage.input_tokens, 0)
        self.assertEqual(result.usage.output_tokens, 0)


class CancellationTest(unittest.TestCase):
    """Test SSE cancel support (Limitation 2 optimization)."""

    def setUp(self):
        from types import SimpleNamespace

        class FakeChat:
            def __init__(self):
                self.calls = 0

            def create(self, **kwargs):
                self.calls += 1
                return SimpleNamespace(
                    choices=[SimpleNamespace(message=SimpleNamespace(content="|1| translated"))],
                    usage=SimpleNamespace(prompt_tokens=10, completion_tokens=5),
                )

        class FakeOpenAI:
            def __init__(self, **kwargs):
                self.chat = SimpleNamespace(completions=FakeChat())

        self.FakeOpenAI = FakeOpenAI

    def _provider(self):
        return {
            "name": "p", "provider_type": "openai_compatible",
            "base_url": "http://x/v1", "model": "m", "enabled": True,
        }

    def test_cancel_before_start_raises_cancelled(self):
        """Pre-set cancel event → translate_with_provider raises TranslationCancelled immediately."""
        cancel = CancelEvent()
        cancel.set()
        article = {"title": "T", "cleaned_markdown": "Hello world."}
        with patch("app.services.translation_agent.OpenAI", self.FakeOpenAI):
            with self.assertRaises(TranslationCancelled):
                translate_with_provider(
                    article, self._provider(), TranslationOptions(),
                    cancel_event=cancel,
                )

    def test_cancel_between_chunks_aborts_early(self):
        """Multi-chunk translation: set cancel after first chunk → aborts before second."""
        cancel = CancelEvent()
        events = []

        article = {
            "title": "Long",
            "cleaned_markdown": "\n\n".join(["paragraph one " * 100, "paragraph two " * 100]),
        }
        fake_instance_holder = {}

        class FakeChat:
            def __init__(self):
                self.calls = 0

            def create(self, **kwargs):
                self.calls += 1
                # After the first chunk completes, signal cancel.
                if self.calls >= 1:
                    cancel.set()
                return SimpleNamespace(
                    choices=[SimpleNamespace(message=SimpleNamespace(content="|1| translated"))],
                    usage=SimpleNamespace(prompt_tokens=10, completion_tokens=5),
                )

        class FakeOpenAI:
            def __init__(self, **kwargs):
                self.chat = SimpleNamespace(completions=FakeChat())

        with patch("app.services.translation_agent.OpenAI", FakeOpenAI):
            with self.assertRaises(TranslationCancelled):
                translate_with_provider(
                    article, self._provider(),
                    TranslationOptions(
                        context_window_tokens=800,
                        chunk_token_budget=180,
                    ),
                    on_event=lambda e: events.append(e),
                    cancel_event=cancel,
                )

    def test_no_cancel_event_works_normally(self):
        """Without a cancel_event, translation proceeds as usual."""
        article = {"title": "T", "cleaned_markdown": "Hello world."}
        with patch("app.services.translation_agent.OpenAI", self.FakeOpenAI):
            result = translate_with_provider(article, self._provider(), TranslationOptions())
        self.assertIn("translated", result.text)


class AlignedBlocksPersistenceTest(unittest.TestCase):
    """Test aligned_blocks persistence in prompt field (Limitation 1 optimization)."""

    def test_encode_and_extract_roundtrip(self):
        blocks = [
            {"type": "paragraph", "original": "Hello.", "translated": "你好。"},
            {"type": "heading", "original": "Title", "translated": "标题"},
        ]
        prompt_trace = "[chunk 1/1]\nsystem\n\nuser"
        encoded = _encode_prompt_with_aligned(prompt_trace, blocks)
        # The trace should still be present after the marker block
        self.assertIn("[chunk 1/1]", encoded)
        # Extract should recover the blocks
        extracted = extract_aligned_blocks_from_prompt(encoded)
        self.assertEqual(extracted, blocks)

    def test_encode_none_aligned_returns_plain_prompt(self):
        """No aligned_blocks → prompt is returned unchanged (no marker added)."""
        prompt = "plain prompt trace"
        encoded = _encode_prompt_with_aligned(prompt, None)
        self.assertEqual(encoded, prompt)

    def test_extract_from_plain_prompt_returns_none(self):
        """Prompt without marker → None."""
        self.assertIsNone(extract_aligned_blocks_from_prompt("just a trace"))
        self.assertIsNone(extract_aligned_blocks_from_prompt(""))

    def test_extract_handles_malformed_marker(self):
        """Malformed JSON between markers → None, no exception."""
        malformed = "---aligned_blocks---\n{not valid json}\n---aligned_blocks-end---\ntrace"
        self.assertIsNone(extract_aligned_blocks_from_prompt(malformed))


class ReassemblyTest(unittest.TestCase):
    """Test Step E: _reassemble_translation"""

    def test_reassembly_with_prefix(self):
        blocks = [
            Block("heading", "## ", "Title", "## Title"),
            Block("paragraph", "", "Body.", "Body."),
        ]
        chunk_1 = type("Chunk", (), {"block_index": 0, "sentences": [Sentence(0, "Title")], "sentence_start": 0})
        chunk_2 = type("Chunk", (), {"block_index": 1, "sentences": [Sentence(0, "Body.")], "sentence_start": 0})
        result = _reassemble_translation(blocks, [
            (chunk_1, ["Translated Title"]),
            (chunk_2, ["Translated Body."]),
        ])
        self.assertIn("## Translated Title", result)
        self.assertIn("Translated Body.", result)

    def test_code_block_preserved(self):
        blocks = [
            Block("paragraph", "", "Hello.", "Hello."),
            Block("code_block", "", "", "```\ncode\n```"),
        ]
        chunk = type("Chunk", (), {"block_index": 0, "sentences": [Sentence(0, "Hello.")], "sentence_start": 0})
        result = _reassemble_translation(blocks, [(chunk, ["你好。"])])
        self.assertIn("你好。", result)
        self.assertIn("code", result)


class ExistingTests(unittest.TestCase):
    """Keep existing test coverage"""

    def provider(self, provider_type="openai_compatible"):
        return {
            "name": "Local Test Provider",
            "provider_type": provider_type,
            "base_url": "http://127.0.0.1:11434/v1",
            "api_key": "test-key",
            "model": "qwen3:8b",
            "enabled": True,
        }

    def test_build_translation_source_prefers_cleaned_markdown(self):
        article = {
            "title": "本地优先 RSS",
            "summary": "summary",
            "cleaned_markdown": "# 标题\n\n正文内容",
            "cleaned_html": "<p>html content</p>",
        }
        source = build_translation_source(article)
        self.assertIn("正文内容", source)
        self.assertNotIn("html content", source)

    def test_prompt_preserves_markdown_and_target_language(self):
        article = {"title": "Agent", "feed_title": "RSSReader"}
        system_prompt, user_prompt = build_translation_prompt(
            article,
            "# Title\n\nBody",
            TranslationOptions(target_language="en", source_language="zh", preserve_markdown=True),
        )
        self.assertIn("文章翻译智能体", system_prompt)
        self.assertIn("目标语言：English", user_prompt)
        self.assertIn("源语言：中文", user_prompt)
        self.assertIn("保留原文 Markdown 结构", user_prompt)

    def test_empty_article_raises_readable_error(self):
        with self.assertRaisesRegex(TranslationAgentError, "没有可翻译的正文"):
            translate_with_provider({"title": "Empty"}, self.provider())


if __name__ == "__main__":
    unittest.main()
