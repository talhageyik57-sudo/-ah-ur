"""template modülü: gönderi metninin bütünlüğü."""

import unittest

from smallcap.levels import compute_levels
from smallcap.models import Quote
from smallcap.numbers import fmt_price
from smallcap.template import DEFAULT_CATALYST, build_catalyst, render_details, render_post

QUOTE = Quote(
    ticker="RKLB",
    price=4.25,
    change_pct=32.0,
    catalyst="Uydu sözleşmesi haberi",
    day_high=4.48,
    day_low=3.10,
    volume=48e6,
    avg_volume=6e6,
)

REQUIRED_LINES = (
    "US SMALL-CAP | HACİMLİ MUM & HEDEF BÖLGELERİ",
    "Ticker:",
    "Son Fiyat:",
    "Katalizör / Haber:",
    "TEKNİK SEVİYELER VE AKSİYON PLANI:",
    "İlk Direnç:",
    "İlk Destek:",
    "KIRILIM & ALIM STRATEJİSİ:",
    "hacimli ilk mum kapanışı (5dk / 15dk)",
    "HEDEF SEVİYELERİ (KAR AL / TP):",
    "Hedef 1 (TP1):",
    "Hedef 2 (TP2):",
    "STOP-LOSS (RİSK ÇIKIŞI):",
    "HIZLI TÜYO:",
    "Fake-out",
    "slippage",
)


class PostTest(unittest.TestCase):
    def setUp(self):
        self.levels = compute_levels(QUOTE)
        self.post = render_post(QUOTE, self.levels, "plain")

    def test_contains_every_template_section(self):
        for line in REQUIRED_LINES:
            with self.subTest(line=line):
                self.assertIn(line, self.post)

    def test_no_placeholder_left(self):
        self.assertNotIn("[", self.post)
        self.assertNotIn("{", self.post)

    def test_ticker_and_price(self):
        self.assertIn("$RKLB", self.post)
        self.assertIn("$4.25 (%+32)", self.post)

    def test_all_levels_present(self):
        for value in (
            self.levels.resistance,
            self.levels.support,
            self.levels.breakout_entry,
            self.levels.tp1,
            self.levels.tp2,
            self.levels.stop,
        ):
            with self.subTest(value=value):
                self.assertIn(f"${fmt_price(value)}", self.post)

    def test_no_greeting_or_preamble(self):
        first_line = self.post.splitlines()[0]
        self.assertTrue(first_line.startswith("🇺🇸"), first_line)

    def test_html_output_is_tagged(self):
        html = render_post(QUOTE, self.levels, "html")
        self.assertIn("<b>Ticker:</b>", html)
        self.assertNotIn("**", html)

    def test_markdown_v2_output_is_escaped(self):
        md = render_post(QUOTE, self.levels, "markdownv2")
        self.assertIn("\\.", md)
        self.assertNotIn("**", md)


class CatalystTest(unittest.TestCase):
    def test_default_when_missing(self):
        self.assertEqual(build_catalyst(Quote(ticker="T", price=1.0)), DEFAULT_CATALYST)

    def test_rvol_appended(self):
        text = build_catalyst(Quote(ticker="T", price=1.0, volume=48e6, avg_volume=6e6))
        self.assertIn("RVOL ~8.0x", text)

    def test_squeeze_note_appended(self):
        text = build_catalyst(
            Quote(ticker="T", price=1.0, catalyst="Haber", float_shares=14e6, short_float=24.0)
        )
        self.assertIn("squeeze adayı", text)

    def test_low_rvol_is_not_noise(self):
        text = build_catalyst(Quote(ticker="T", price=1.0, volume=7e6, avg_volume=6e6))
        self.assertNotIn("RVOL", text)


class DetailsTest(unittest.TestCase):
    def test_contains_risk_reward(self):
        text = render_details(QUOTE, parse_mode="plain")
        self.assertIn("R/R", text)
        self.assertIn("Varsayımlar:", text)


class ChangeOptionalTest(unittest.TestCase):
    def test_price_line_without_change(self):
        post = render_post(Quote(ticker="T", price=4.25), parse_mode="plain")
        self.assertIn("Son Fiyat: $4.25\n", post)


if __name__ == "__main__":
    unittest.main()
