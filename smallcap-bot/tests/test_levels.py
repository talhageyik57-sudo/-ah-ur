"""levels modülü: seviye hesaplama kuralları ve değişmezler."""

import unittest

from smallcap.levels import compute_levels
from smallcap.models import Quote


class OrderingTest(unittest.TestCase):
    """Seviyeler her girdi için tutarlı sırada olmalı."""

    CASES = (
        Quote(ticker="RKLB", price=4.25, change_pct=32.0, day_high=4.48, day_low=3.10),
        Quote(ticker="ABCD", price=0.4523, change_pct=118.0, day_high=0.52, day_low=0.31),
        Quote(ticker="SOUN", price=12.40, change_pct=-3.2),
        Quote(ticker="XYZ", price=1.00, change_pct=0.0),
        Quote(ticker="HUGE", price=248.0, change_pct=9.5, day_high=252.0, day_low=230.0),
        Quote(ticker="TINY", price=0.0821, change_pct=240.0, day_high=0.11, day_low=0.02),
        Quote(ticker="FLAT", price=5.00, day_high=5.00, day_low=5.00),
        Quote(ticker="GAP", price=7.50, change_pct=-40.0, day_high=13.0, day_low=7.10),
    )

    def test_level_ordering(self):
        for quote in self.CASES:
            with self.subTest(ticker=quote.ticker):
                levels = compute_levels(quote)
                self.assertGreater(levels.support, levels.stop, "stop destek altında olmalı")
                self.assertGreater(quote.price, levels.support, "destek fiyat altında olmalı")
                self.assertGreater(levels.resistance, quote.price, "direnç fiyat üstünde olmalı")
                self.assertGreater(levels.breakout_entry, levels.resistance)
                self.assertGreater(levels.tp1, levels.breakout_entry)
                self.assertGreater(levels.tp2, levels.tp1)
                self.assertGreater(levels.stop, 0)

    def test_risk_reward_is_positive(self):
        for quote in self.CASES:
            with self.subTest(ticker=quote.ticker):
                levels = compute_levels(quote)
                self.assertGreater(levels.risk, 0)
                self.assertGreater(levels.rr_tp1, 0)
                self.assertGreater(levels.rr_tp2, levels.rr_tp1)


class MethodologyTest(unittest.TestCase):
    def test_resistance_uses_day_high(self):
        levels = compute_levels(Quote(ticker="T", price=4.25, day_high=4.50, day_low=4.00))
        self.assertEqual(levels.resistance, 4.50)

    def test_resistance_uses_premarket_high_when_higher(self):
        levels = compute_levels(
            Quote(ticker="T", price=4.25, day_high=4.40, premarket_high=4.75, day_low=4.00)
        )
        self.assertEqual(levels.resistance, 4.75)

    def test_resistance_ignores_stale_high_below_price(self):
        levels = compute_levels(Quote(ticker="T", price=5.00, day_high=4.50))
        self.assertGreater(levels.resistance, 5.00)

    def test_support_is_day_low_on_narrow_range(self):
        levels = compute_levels(Quote(ticker="T", price=10.40, day_high=10.50, day_low=10.00))
        self.assertEqual(levels.support, 10.00)

    def test_support_uses_fib_pivot_on_wide_range(self):
        # 3.10 - 4.50 bandı %31 geniş: destek dip değil, %38.2 düzeltme.
        levels = compute_levels(Quote(ticker="T", price=4.25, day_high=4.50, day_low=3.10))
        self.assertGreater(levels.support, 3.10)
        self.assertLess(levels.support, 4.25)

    def test_support_from_change_pct_when_no_low(self):
        # 10.00'dan 12.00'a hareketin %50 düzeltmesi ~11.00.
        levels = compute_levels(Quote(ticker="T", price=12.00, change_pct=20.0))
        self.assertAlmostEqual(levels.support, 11.00, places=2)

    def test_breakout_is_just_above_resistance(self):
        levels = compute_levels(Quote(ticker="T", price=4.90, day_high=5.00, day_low=4.60))
        self.assertEqual(levels.resistance, 5.00)
        self.assertEqual(levels.breakout_entry, 5.05)

    def test_targets_stay_in_methodology_bands(self):
        levels = compute_levels(Quote(ticker="T", price=9.80, day_high=10.00, day_low=9.40))
        tp1_margin = levels.tp1 / levels.resistance - 1
        tp2_margin = levels.tp2 / levels.resistance - 1
        self.assertTrue(0.04 <= tp1_margin <= 0.11, f"TP1 marjı: {tp1_margin:.3f}")
        self.assertTrue(0.14 <= tp2_margin <= 0.26, f"TP2 marjı: {tp2_margin:.3f}")

    def test_stop_is_two_to_three_percent_below_support(self):
        levels = compute_levels(Quote(ticker="T", price=10.40, day_high=10.50, day_low=10.00))
        drop = 1 - levels.stop / levels.support
        self.assertTrue(0.015 <= drop <= 0.035, f"stop sapması: {drop:.3f}")

    def test_assumptions_are_reported(self):
        levels = compute_levels(Quote(ticker="T", price=4.25, volume=48e6, avg_volume=6e6))
        self.assertTrue(levels.assumptions)
        self.assertTrue(any("RVOL" in note for note in levels.assumptions))


class SqueezeTest(unittest.TestCase):
    def test_squeeze_candidate_detection(self):
        quote = Quote(ticker="T", price=4.25, float_shares=14e6, short_float=24.0)
        self.assertTrue(quote.is_squeeze_candidate)
        self.assertTrue(
            any("squeeze" in note.lower() for note in compute_levels(quote).assumptions)
        )

    def test_large_float_is_not_squeeze(self):
        quote = Quote(ticker="T", price=4.25, float_shares=400e6, short_float=24.0)
        self.assertFalse(quote.is_squeeze_candidate)


class QuoteValidationTest(unittest.TestCase):
    def test_rejects_non_positive_price(self):
        with self.assertRaises(ValueError):
            Quote(ticker="T", price=0)

    def test_rejects_empty_ticker(self):
        with self.assertRaises(ValueError):
            Quote(ticker="  ", price=1.0)

    def test_normalizes_ticker(self):
        self.assertEqual(Quote(ticker=" $rklb ", price=1.0).ticker, "RKLB")

    def test_merge_only_fills_gaps(self):
        base = Quote(ticker="T", price=4.25, day_high=4.50)
        live = Quote(ticker="T", price=4.10, day_high=9.99, day_low=3.80)
        merged = base.merge(live)
        self.assertEqual(merged.day_high, 4.50, "kullanıcı verisi ezilmemeli")
        self.assertEqual(merged.day_low, 3.80, "eksik alan doldurulmalı")


if __name__ == "__main__":
    unittest.main()
