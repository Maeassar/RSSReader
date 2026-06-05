import unittest

from app.services.content_cleaner import clean_html


class ContentCleanerTest(unittest.TestCase):
    def test_clean_html_removes_scripts_and_normalizes_lazy_images(self):
        result = clean_html(
            """
            <article>
              <h1>Title</h1>
              <p>Hello<script>alert(1)</script> world.</p>
              <img data-src="https://example.com/image.jpg" alt="cover" width="600" />
            </article>
            """
        )

        self.assertIn("<h1>Title</h1>", result["cleaned_html"])
        self.assertNotIn("script", result["cleaned_html"])
        self.assertIn('src="https://example.com/image.jpg"', result["cleaned_html"])
        self.assertIn("Title", result["cleaned_markdown"])

    def test_clean_html_unwraps_empty_links_and_drops_empty_blocks(self):
        result = clean_html(
            """
            <div>
              <p><a>plain text</a></p>
              <p> </p>
              <div class="wrapper"><span>kept</span></div>
            </div>
            """
        )

        self.assertIn("<p>plain text</p>", result["cleaned_html"])
        self.assertNotIn("<a>", result["cleaned_html"])
        self.assertNotIn("<p> </p>", result["cleaned_html"])
        self.assertIn("plain text", result["cleaned_markdown"])


if __name__ == "__main__":
    unittest.main()
