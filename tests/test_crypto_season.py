import json
import unittest
from unittest.mock import patch

import crypto_season


class CryptoSeasonTests(unittest.TestCase):
    @patch("crypto_season.fetch_json")
    def test_get_coingecko_reading(self, mock_fetch_json):
        mock_fetch_json.return_value = {"data": {"market_cap_percentage": {"btc": 53.12}}}
        reading = crypto_season.get_coingecko_reading()
        self.assertEqual(reading.source, "CoinGecko")
        self.assertAlmostEqual(reading.btc_dominance, 53.12)

    @patch("crypto_season.fetch_json")
    def test_get_coinmarketcap_reading_primary_endpoint(self, mock_fetch_json):
        mock_fetch_json.return_value = {"data": {"btcDominance": 54.5}}
        reading = crypto_season.get_coinmarketcap_reading()
        self.assertEqual(reading.source, "CoinMarketCap")
        self.assertAlmostEqual(reading.btc_dominance, 54.5)

    @patch("crypto_season.fetch_text")
    @patch("crypto_season.fetch_json")
    def test_get_coinmarketcap_reading_fallback_scrape(self, mock_fetch_json, mock_fetch_text):
        mock_fetch_json.side_effect = json.JSONDecodeError("err", "doc", 1)
        mock_fetch_text.return_value = '<html><script>{"btcDominance":49.9}</script></html>'
        reading = crypto_season.get_coinmarketcap_reading()
        self.assertAlmostEqual(reading.btc_dominance, 49.9)

    def test_build_report(self):
        readings = [
            crypto_season.DominanceReading("CoinGecko", 52.0, "t1"),
            crypto_season.DominanceReading("CoinMarketCap", 50.0, "t2"),
        ]
        report = crypto_season.build_report(readings)
        self.assertEqual(report["season"], "Transition Season")
        self.assertEqual(report["average_btc_dominance"], 51.0)
        self.assertEqual(report["confidence"], "medium")


if __name__ == "__main__":
    unittest.main()
