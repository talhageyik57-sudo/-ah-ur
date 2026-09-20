"""market_data modülü: sağlayıcı davranışı ve hata toleransı."""

import io
import json
import unittest
from unittest import mock

from smallcap import market_data


def _response(payload):
    body = io.BytesIO(json.dumps(payload).encode("utf-8"))
    context = mock.MagicMock()
    context.__enter__.return_value = body
    context.__exit__.return_value = False
    return context


class FinnhubTest(unittest.TestCase):
    def test_maps_payload_to_quote(self):
        payload = {"c": 4.25, "dp": 32.1, "h": 4.48, "l": 3.10, "pc": 3.22}
        with mock.patch.object(market_data.urllib.request, "urlopen", return_value=_response(payload)):
            quote = market_data.fetch_quote("rklb", finnhub_api_key="key")
        self.assertEqual(quote.ticker, "RKLB")
        self.assertEqual(quote.price, 4.25)
        self.assertEqual(quote.change_pct, 32.1)
        self.assertEqual(quote.day_high, 4.48)
        self.assertEqual(quote.source, "finnhub")

    def test_empty_price_is_skipped(self):
        payload = {"c": 0, "dp": 0}
        with mock.patch.object(market_data.urllib.request, "urlopen", return_value=_response(payload)):
            self.assertIsNone(market_data.fetch_quote("RKLB", finnhub_api_key="key"))

    def test_network_error_does_not_propagate(self):
        with mock.patch.object(market_data.urllib.request, "urlopen", side_effect=OSError("boom")):
            with self.assertLogs(market_data.logger, level="WARNING"):
                self.assertIsNone(market_data.fetch_quote("RKLB", finnhub_api_key="key"))

    def test_no_key_means_no_request(self):
        with mock.patch.object(market_data.urllib.request, "urlopen") as urlopen:
            market_data.fetch_quote("RKLB", finnhub_api_key=None)
        urlopen.assert_not_called()


if __name__ == "__main__":
    unittest.main()
