# Crypto Season App

This repository now contains a small Python CLI app that checks Bitcoin market-cap dominance from **CoinGecko** and **CoinMarketCap**, then classifies the current market as:

- **Bitcoin Season** (BTC dominance >= 55%)
- **Altcoin Season** (BTC dominance <= 45%)
- **Transition Season** (between those levels)

## Run

```bash
python crypto_season.py
```

JSON output:

```bash
python crypto_season.py --json
```

## Tests

```bash
python -m unittest discover -s tests
```

## Notes

- The app uses CoinGecko's global endpoint and CoinMarketCap's frontend global-metrics endpoint.
- CoinMarketCap scraping includes a fallback parser against the homepage if the endpoint format changes.
