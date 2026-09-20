"""parser modülü: serbest metin girdisinin çözümlenmesi."""

import unittest

from smallcap.parser import ParseError, parse_fields, parse_input


class PositionalTest(unittest.TestCase):
    def test_full_line(self):
        quote = parse_input("RKLB 4.25 %32 FDA onayı sonrası hacim patlaması")
        self.assertEqual(quote.ticker, "RKLB")
        self.assertEqual(quote.price, 4.25)
        self.assertEqual(quote.change_pct, 32.0)
        self.assertEqual(quote.catalyst, "FDA onayı sonrası hacim patlaması")

    def test_dollar_prefix_and_signed_pct(self):
        quote = parse_input("$abcd 0.4523 +118% ortaklık duyurusu")
        self.assertEqual(quote.ticker, "ABCD")
        self.assertEqual(quote.change_pct, 118.0)

    def test_negative_change(self):
        quote = parse_input("SOUN 12.40 -3.2 kar realizasyonu")
        self.assertEqual(quote.change_pct, -3.2)

    def test_comma_decimal(self):
        quote = parse_input("RKLB 4,25 %32 haber")
        self.assertEqual(quote.price, 4.25)

    def test_catalyst_optional(self):
        quote = parse_input("RKLB 4.25 %32")
        self.assertIsNone(quote.catalyst)

    def test_numeric_catalyst_is_not_eaten(self):
        quote = parse_input("RKLB 4.25 %32 3 milyar dolarlık sözleşme")
        self.assertEqual(quote.price, 4.25)
        self.assertEqual(quote.catalyst, "3 milyar dolarlık sözleşme")


class KeyValueTest(unittest.TestCase):
    def test_extra_fields(self):
        quote = parse_input(
            "ABCD 0.4523 +118% hod=0.52 lod=0.31 pm=0.49 vol=48M avgvol=6M "
            "float=14M short=%24 haber=Ortaklık duyurusu"
        )
        self.assertEqual(quote.day_high, 0.52)
        self.assertEqual(quote.day_low, 0.31)
        self.assertEqual(quote.premarket_high, 0.49)
        self.assertEqual(quote.volume, 48_000_000)
        self.assertEqual(quote.avg_volume, 6_000_000)
        self.assertEqual(quote.float_shares, 14_000_000)
        self.assertEqual(quote.short_float, 24.0)
        self.assertEqual(quote.catalyst, "Ortaklık duyurusu")
        self.assertAlmostEqual(quote.rvol, 8.0)

    def test_colon_separator_and_turkish_aliases(self):
        quote = parse_input("RKLB 4.25 %32 tepe:4.48 dip:3.10 hacim:48M")
        self.assertEqual(quote.day_high, 4.48)
        self.assertEqual(quote.day_low, 3.10)
        self.assertEqual(quote.volume, 48_000_000)

    def test_catalyst_with_colon_is_preserved(self):
        quote = parse_input("RKLB 4.25 %32 FDA: hızlandırılmış onay")
        self.assertEqual(quote.catalyst, "FDA: hızlandırılmış onay")

    def test_price_can_come_from_key(self):
        parsed = parse_fields("RKLB fiyat=4.25 degisim=%32")
        self.assertTrue(parsed.has_price)
        self.assertEqual(parsed.to_quote().price, 4.25)


class ErrorTest(unittest.TestCase):
    def test_empty(self):
        with self.assertRaises(ParseError):
            parse_input("   ")

    def test_bad_ticker(self):
        with self.assertRaises(ParseError):
            parse_input("12345 4.25 %32")

    def test_missing_price(self):
        with self.assertRaises(ParseError):
            parse_input("RKLB hacim patlaması")

    def test_ticker_only_is_parsed_without_price(self):
        parsed = parse_fields("RKLB")
        self.assertEqual(parsed.ticker, "RKLB")
        self.assertFalse(parsed.has_price)


if __name__ == "__main__":
    unittest.main()
