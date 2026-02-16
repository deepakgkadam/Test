#!/usr/bin/env python3
"""Determine the current crypto market season from CoinGecko and CoinMarketCap data."""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

USER_AGENT = "Mozilla/5.0 (compatible; CryptoSeasonBot/1.0)"


@dataclass
class DominanceReading:
    source: str
    btc_dominance: float
    timestamp: str


def fetch_text(url: str, timeout: int = 20) -> str:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=timeout) as response:  # nosec B310: fixed URLs only
        return response.read().decode("utf-8", "ignore")


def fetch_json(url: str, timeout: int = 20) -> Any:
    return json.loads(fetch_text(url, timeout=timeout))


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_coingecko_reading() -> DominanceReading:
    payload = fetch_json("https://api.coingecko.com/api/v3/global")
    btc_dominance = float(payload["data"]["market_cap_percentage"]["btc"])
    return DominanceReading(source="CoinGecko", btc_dominance=btc_dominance, timestamp=now_iso())


def get_coinmarketcap_reading() -> DominanceReading:
    # Endpoint used by coinmarketcap.com frontend at the time of writing.
    try:
        payload = fetch_json("https://api.coinmarketcap.com/data-api/v3/global-metrics/quotes/latest")
        btc_dominance = float(payload["data"]["btcDominance"])
        return DominanceReading(source="CoinMarketCap", btc_dominance=btc_dominance, timestamp=now_iso())
    except (KeyError, ValueError, URLError, json.JSONDecodeError):
        pass

    # Fallback: scrape homepage embedded data.
    homepage = fetch_text("https://coinmarketcap.com/")
    match = re.search(r'"btcDominance"\s*:\s*([0-9]+(?:\.[0-9]+)?)', homepage)
    if not match:
        raise RuntimeError("Could not find btcDominance in CoinMarketCap response")
    return DominanceReading(source="CoinMarketCap", btc_dominance=float(match.group(1)), timestamp=now_iso())


def classify_season(btc_dominance: float) -> str:
    if btc_dominance >= 55:
        return "Bitcoin Season"
    if btc_dominance <= 45:
        return "Altcoin Season"
    return "Transition Season"


def build_report(readings: list[DominanceReading]) -> dict[str, Any]:
    avg_dominance = statistics.mean(r.btc_dominance for r in readings)
    spread = max(r.btc_dominance for r in readings) - min(r.btc_dominance for r in readings)
    confidence = "high" if spread <= 1.5 else "medium" if spread <= 3 else "low"

    return {
        "generated_at": now_iso(),
        "season": classify_season(avg_dominance),
        "average_btc_dominance": round(avg_dominance, 2),
        "source_spread": round(spread, 2),
        "confidence": confidence,
        "sources": [
            {
                "source": r.source,
                "btc_dominance": round(r.btc_dominance, 2),
                "timestamp": r.timestamp,
            }
            for r in readings
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Detect crypto market season from CoinGecko and CoinMarketCap")
    parser.add_argument("--json", action="store_true", help="Output raw JSON report")
    args = parser.parse_args()

    try:
        readings = [get_coingecko_reading(), get_coinmarketcap_reading()]
        report = build_report(readings)
    except Exception as exc:  # broad to provide useful CLI failure message
        print(f"Failed to build crypto season report: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(report, indent=2))
        return 0

    print(f"Season: {report['season']}")
    print(f"Average BTC dominance: {report['average_btc_dominance']}%")
    print(f"Confidence: {report['confidence']} (spread {report['source_spread']}%)")
    for source in report["sources"]:
        print(f"- {source['source']}: {source['btc_dominance']}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
