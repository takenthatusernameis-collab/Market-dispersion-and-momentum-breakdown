# Free data sources and provenance

## Current source baseline
The existing experiments recorded:
- Coin Metrics Community API for historical market-cap metrics, subject to field-specific coverage and current community-tier rules.
- Binance Public Data Archive for daily price candles and historical USD-M perpetual funding-rate archives.

Official entry points:
- Coin Metrics API v4 documentation: https://docs.coinmetrics.io/api/v4/
- Coin Metrics Community API: https://community-api.coinmetrics.io/v4/
- Binance Public Data Archive: https://data.binance.vision/

A successful request or an earlier data-gate pass does not prove current reachability or complete history. Verify access and terms at execution time.

## Candidate-source policy
Prefer first-party public files/APIs and no-cost open datasets. A fallback is admissible only after verifying that it is genuinely free without trial, credit card or paid tier; documents historical timestamp/coverage/revision semantics; has cap/price observations available by formation time; supports stable identity and delisting mapping; and can be queried and hashed reproducibly.

Never blend market-cap definitions silently. Keep primary and robustness fields separate and validate coverage before computing outcomes.

## Required provenance
Record source URL/endpoint family, UTC retrieval time, request parameters, pagination/archive path, schema version, IDs, response/row counts, date range, missingness, mapping decisions, source terms/access classification, content hash and code version. Never store secret-bearing URLs or credentials.

## Handling failure
A missing/rate-limited source becomes a durable blocked frontier item with its error class and bounded retry policy. Continue to the next candidate or independent task. Never substitute today's rank, synthetic data, interpolation or unverified sources. If no adequate free point-in-time cap evidence exists, block the affected confirmatory cell.
