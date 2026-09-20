"""numbers modülü: tick bandı, yuvarlama ve biçimlendirme."""

import unittest

from smallcap.numbers import (
    fmt_pct,
    fmt_price,
    fmt_volume,
    parse_number,
    psych_round,
    round_to,
    tick_size,
)


class TickSizeTest(unittest.TestCase):
    def test_bands(self):
        self.assertEqual(tick_size(0.45), 0.01)
        self.assertEqual(tick_size(4.25), 0.05)
        self.assertEqual(tick_size(12.40), 0.10)
        self.assertEqual(tick_size(35.0), 0.10)
        self.assertEqual(tick_size(120.0), 0.25)
        self.assertEqual(tick_size(450.0), 0.50)


class RoundToTest(unittest.TestCase):
    def test_modes(self):
        self.assertEqual(round_to(4.53, 0.05, "nearest"), 4.55)
        self.assertEqual(round_to(4.51, 0.05, "up"), 4.55)
        self.assertEqual(round_to(4.59, 0.05, "down"), 4.55)

    def test_no_float_artifacts(self):
        self.assertEqual(round_to(0.1 + 0.2, 0.01), 0.3)

    def test_rejects_bad_step(self):
        with self.assertRaises(ValueError):
            round_to(1.0, 0)
        with self.assertRaises(ValueError):
            round_to(1.0, 0.05, "sideways")


class PsychRoundTest(unittest.TestCase):
    def test_snaps_to_clean_level(self):
        self.assertEqual(psych_round(4.4912), 4.50)
        self.assertEqual(psych_round(9.98), 10.0)

    def test_keeps_already_clean_level(self):
        # 4.30 zaten 0.10'un katı; gereksiz yere 4.25'e kaydırılmamalı.
        self.assertEqual(psych_round(4.30), 4.30)

    def test_respects_max_drift(self):
        # 8.90 -> 9.00 sapması %1.1; kabul edilir.
        self.assertEqual(psych_round(8.90), 8.90)
        # 0.4523 -> 0.50 sapması %10'un üzerinde; kaba adım reddedilir.
        self.assertEqual(psych_round(0.4523), 0.45)

    def test_zero_is_passthrough(self):
        self.assertEqual(psych_round(0.0), 0.0)


class FormatTest(unittest.TestCase):
    def test_price(self):
        self.assertEqual(fmt_price(4.25), "4.25")
        self.assertEqual(fmt_price(0.4523), "0.4523")
        self.assertEqual(fmt_price(0.45), "0.45")
        self.assertEqual(fmt_price(128.5), "128.50")

    def test_pct(self):
        self.assertEqual(fmt_pct(32.4), "%+32.4")
        self.assertEqual(fmt_pct(32.0), "%+32")
        self.assertEqual(fmt_pct(-3.25), "%-3.25")

    def test_volume(self):
        self.assertEqual(fmt_volume(1_250_000), "1.25M")
        self.assertEqual(fmt_volume(48_000_000), "48M")
        self.assertEqual(fmt_volume(950), "950")


class ParseNumberTest(unittest.TestCase):
    def test_variants(self):
        self.assertEqual(parse_number("$4.25"), 4.25)
        self.assertEqual(parse_number("4,25"), 4.25)
        self.assertEqual(parse_number("%32"), 32.0)
        self.assertEqual(parse_number("32%"), 32.0)
        self.assertEqual(parse_number("+118%"), 118.0)
        self.assertEqual(parse_number("12.5M"), 12_500_000)
        self.assertEqual(parse_number("850k"), 850_000)

    def test_invalid(self):
        with self.assertRaises(ValueError):
            parse_number("FDA")


if __name__ == "__main__":
    unittest.main()
