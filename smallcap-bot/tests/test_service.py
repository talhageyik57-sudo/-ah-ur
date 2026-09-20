"""service modülü: manuel girdi ve canlı verinin birleştirilmesi."""

import unittest
from unittest import mock

from smallcap import service
from smallcap.config import Settings
from smallcap.models import Quote
from smallcap.parser import ParseError

LIVE = Quote(
    ticker="RKLB",
    price=4.10,
    change_pct=28.0,
    day_high=4.40,
    day_low=3.05,
    prev_close=3.20,
    source="finnhub",
)


class ManualOnlyTest(unittest.TestCase):
    def test_no_fetch_when_disabled(self):
        settings = Settings(auto_fetch=False)
        with mock.patch.object(service, "fetch_quote") as fetch:
            quote = service.build_quote("RKLB 4.25 %32 haber", settings)
        fetch.assert_not_called()
        self.assertEqual(quote.price, 4.25)
        self.assertEqual(quote.source, "manuel")

    def test_missing_price_without_fetch_raises(self):
        with self.assertRaises(ParseError):
            service.build_quote("RKLB", Settings(auto_fetch=False))


class LiveDataTest(unittest.TestCase):
    def test_manual_values_win_over_live(self):
        settings = Settings(auto_fetch=True)
        with mock.patch.object(service, "fetch_quote", return_value=LIVE):
            quote = service.build_quote("RKLB 4.25 %32 hod=4.48 haber=Sözleşme", settings)
        self.assertEqual(quote.price, 4.25, "elle girilen fiyat korunmalı")
        self.assertEqual(quote.change_pct, 32.0)
        self.assertEqual(quote.day_high, 4.48, "elle girilen tepe korunmalı")
        self.assertEqual(quote.day_low, 3.05, "eksik alan canlı veriden gelmeli")
        self.assertIn("finnhub", quote.source)

    def test_ticker_only_uses_live_quote(self):
        settings = Settings(auto_fetch=True)
        with mock.patch.object(service, "fetch_quote", return_value=LIVE):
            quote = service.build_quote("RKLB", settings)
        self.assertEqual(quote.price, 4.10)
        self.assertEqual(quote.source, "finnhub")

    def test_ticker_only_with_catalyst_override(self):
        settings = Settings(auto_fetch=True)
        with mock.patch.object(service, "fetch_quote", return_value=LIVE):
            quote = service.build_quote("RKLB haber=Uydu sözleşmesi", settings)
        self.assertEqual(quote.catalyst, "Uydu sözleşmesi")
        self.assertEqual(quote.price, 4.10)

    def test_fetch_failure_falls_back_to_manual(self):
        settings = Settings(auto_fetch=True)
        with mock.patch.object(service, "fetch_quote", return_value=None):
            quote = service.build_quote("RKLB 4.25 %32", settings)
        self.assertEqual(quote.price, 4.25)
        self.assertEqual(quote.source, "manuel")

    def test_fetch_failure_without_price_raises(self):
        settings = Settings(auto_fetch=True)
        with mock.patch.object(service, "fetch_quote", return_value=None):
            with self.assertRaises(ParseError):
                service.build_quote("RKLB", settings)


class RenderTest(unittest.TestCase):
    def test_analyze_returns_post(self):
        text = service.analyze("RKLB 4.25 %32 haber", Settings(auto_fetch=False), "plain")
        self.assertIn("US SMALL-CAP", text)
        self.assertIn("$RKLB", text)

    def test_analyze_details_returns_notes(self):
        text = service.analyze_details("RKLB 4.25 %32", Settings(auto_fetch=False), "plain")
        self.assertIn("HESAP NOTU", text)


if __name__ == "__main__":
    unittest.main()
