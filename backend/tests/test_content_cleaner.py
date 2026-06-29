import unittest

from bs4 import BeautifulSoup

from app.services.content_cleaner import _has_noise_marker, clean_html


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

    def test_clean_html_keeps_first_srcset_image_candidate(self):
        result = clean_html(
            """
            <article>
              <p>Image post</p>
              <img srcset="https://example.com/small.jpg 320w, https://example.com/large.jpg 1200w" />
            </article>
            """
        )

        self.assertIn('src="https://example.com/small.jpg"', result["cleaned_html"])

    def test_clean_html_removes_related_sidebar_blocks(self):
        result = clean_html(
            """
            <article>
              <div class="article-body">
                <p>Main article body stays visible.</p>
                <img src="https://example.com/body.jpg" alt="body" />
              </div>
              <aside class="related-sidebar">
                <img src="https://example.com/sidebar.jpg" alt="sidebar" />
                <p>Side illustration should be removed.</p>
              </aside>
              <div class="share-tools">
                <a href="https://example.com/x">Share A</a>
                <a href="https://example.com/y">Share B</a>
                <a href="https://example.com/z">Share C</a>
              </div>
            </article>
            """
        )

        self.assertIn("Main article body stays visible.", result["cleaned_html"])
        self.assertIn('src="https://example.com/body.jpg"', result["cleaned_html"])
        self.assertNotIn("sidebar.jpg", result["cleaned_html"])
        self.assertNotIn("Side illustration should be removed.", result["cleaned_html"])
        self.assertNotIn("Share A", result["cleaned_html"])

    def test_clean_html_replaces_embedded_video_with_source_link(self):
        result = clean_html(
            """
            <article>
              <p>Video summary</p>
              <iframe src="https://www.youtube.com/embed/demo123" title="Demo video"></iframe>
              <video controls>
                <source src="https://cdn.example.com/video.mp4" type="video/mp4" />
              </video>
            </article>
            """
        )

        self.assertIn('href="https://www.youtube.com/embed/demo123"', result["cleaned_html"])
        self.assertIn("打开视频：Demo video", result["cleaned_html"])
        self.assertIn('href="https://cdn.example.com/video.mp4"', result["cleaned_html"])
        self.assertNotIn("<iframe", result["cleaned_html"])
        self.assertNotIn("<video", result["cleaned_html"])

    def test_has_noise_marker_tolerates_missing_attrs_dict(self):
        node = BeautifulSoup("<div>content</div>", "html.parser").div
        node.attrs = None

        self.assertFalse(_has_noise_marker(node))


if __name__ == "__main__":
    unittest.main()
