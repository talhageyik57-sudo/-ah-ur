"""markup modülü: kanonik işaretlemenin Telegram biçimlerine çevrilmesi."""

import unittest

from smallcap import markup


class PlainTest(unittest.TestCase):
    def test_strips_all_markers(self):
        self.assertEqual(markup.to_plain("**A** ve *b* ve `c`"), "A ve b ve c")

    def test_nested_bold_inside_italic(self):
        self.assertEqual(markup.to_plain("*dış **iç** dış*"), "dış iç dış")


class HtmlTest(unittest.TestCase):
    def test_tags(self):
        self.assertEqual(markup.to_html("**A**"), "<b>A</b>")
        self.assertEqual(markup.to_html("*A*"), "<i>A</i>")
        self.assertEqual(markup.to_html("`A`"), "<code>A</code>")

    def test_nested(self):
        self.assertEqual(markup.to_html("*dış **iç** dış*"), "<i>dış <b>iç</b> dış</i>")

    def test_escapes_html_special_chars(self):
        self.assertEqual(markup.to_html("5 < 6 & 7 > 6"), "5 &lt; 6 &amp; 7 &gt; 6")

    def test_escapes_inside_code(self):
        self.assertEqual(markup.to_html("`a<b`"), "<code>a&lt;b</code>")

    def test_lone_asterisk_is_literal(self):
        self.assertEqual(markup.to_html("2 * 3 = 6"), "2 * 3 = 6")


class MarkdownV2Test(unittest.TestCase):
    def test_tags(self):
        self.assertEqual(markup.to_markdown_v2("**A**"), "*A*")
        self.assertEqual(markup.to_markdown_v2("*A*"), "_A_")

    def test_escapes_special_chars(self):
        self.assertEqual(markup.to_markdown_v2("4.25!"), "4\\.25\\!")

    def test_nested(self):
        self.assertEqual(markup.to_markdown_v2("*dış **iç** dış*"), "_dış *iç* dış_")


class ConvertTest(unittest.TestCase):
    def test_dispatch(self):
        self.assertEqual(markup.convert("**A**", "html"), "<b>A</b>")
        self.assertEqual(markup.convert("**A**", "markdownv2"), "*A*")
        self.assertEqual(markup.convert("**A**", "plain"), "A")

    def test_unknown_mode(self):
        with self.assertRaises(ValueError):
            markup.convert("A", "wingdings")


if __name__ == "__main__":
    unittest.main()
