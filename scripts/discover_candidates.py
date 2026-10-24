#!/usr/bin/env python3
"""Discover and rank candidate assets beyond the mapped legacy 28-asset set.

The CoinMetrics Community API exposes a free asset catalog at
GET /v4/reference-data/assets (paginated via next_page_url). This script:

  1. Walks the full catalog, collecting every asset id.
  2. Excludes assets already in the legacy set or already processed
     (verified / blocked) in research_state/universe_frontier.json.
  3. Records the discovered queue in candidates_discovered and advances
     candidate_page_cursor by the number of newly discovered ids.

No cap/funding fetch, no Binance probe, no eligibility decision: this is
catalog discovery only. Validation (cap history + perpetual existence) is
performed separately by scripts/validate_candidate_batch.py.

Free-data-only: keyless CoinMetrics Community API. No API keys, no secrets,
no paid sources, no trading.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTIER_PATH = ROOT / "research_state" / "universe_frontier.json"

CM_BASE = "https://community-api.coinmetrics.io/v4/reference-data/assets"
REQUEST_TIMEOUT = 30
MAX_RETRIES = 5
BACKOFF_BASE = 2.0
POLL_SLEEP = 0.5  # respect community 10 req / 6 s rate limit


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def cm_get_json(url: str) -> dict:
    last_err: str | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                import hashlib
                raw = resp.read()
                return json.loads(raw.decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", "replace") if hasattr(exc, "read") else str(exc)
            last_err = f"HTTP {exc.code}: {body[:200]}"
            if exc.code in (429, 502, 503, 504):
                time.sleep(BACKOFF_BASE ** attempt)
                continue
            raise RuntimeError(f"non-retryable {last_err}") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_err = f"{type(exc).__name__}: {exc}"
            time.sleep(BACKOFF_BASE ** attempt)
            continue
    raise RuntimeError(f"exhausted retries: {last_err}")


def walk_catalog() -> list[str]:
    """Return every asset id in the CoinMetrics community catalog."""
    url = CM_BASE
    ids: list[str] = []
    seen = 0
    while url:
        payload = cm_get_json(url)
        data = payload.get("data", [])
        for entry in data:
            asset = entry.get("asset")
            if asset:
                ids.append(asset)
        seen += len(data)
        url = payload.get("next_page_url")
        time.sleep(POLL_SLEEP)
    print(f"[catalog] walked {seen} entries, {len(ids)} unique-ish asset ids",
          flush=True)
    return ids


def main() -> int:
    frontier = json.loads(FRONTIER_PATH.read_text(encoding="utf-8"))

    legacy = set()
    for p in (ROOT / "scripts" / "refresh_free_data.py").read_text().splitlines():
        pass
    # The legacy 28 mapped set is the canonical ASSETS list head in
    # scripts/refresh_free_data.py; derive it from the committed SYMBOL_MAP
    # instead of hardcoding so the exclusion set stays in sync.
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "rfd", ROOT / "scripts" / "refresh_free_data.py")
    rfd = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rfd)
    legacy = set(rfd.ASSETS)

    verified = set(frontier.get("candidates_verified", []))
    blocked = set(frontier.get("candidates_blocked", []))
    already = legacy | verified | blocked

    fetch_utc = now_utc()
    try:
        all_ids = walk_catalog()
    except Exception as exc:  # noqa: BLE001 - record blocker, keep program alive
        frontier["catalog_discovery"] = {
            "status": "BLOCKED",
            "error": f"{type(exc).__name__}: {exc}",
            "fetch_utc": fetch_utc,
        }
        FRONTIER_PATH.write_text(
            json.dumps(frontier, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(f"[catalog] BLOCKED: {exc}", flush=True)
        return 1

    new_ids = [a for a in all_ids if a not in already]

    frontier["candidates_discovered"] = new_ids
    frontier["candidate_page_cursor"] = len(all_ids)
    frontier["catalog_discovery"] = {
        "status": "ok",
        "endpoint": CM_BASE,
        "fetch_utc": fetch_utc,
        "catalog_entries_walked": len(all_ids),
        "legacy_excluded": sorted(legacy),
        "verified_excluded": sorted(verified),
        "blocked_excluded": sorted(blocked),
        "newly_discovered": len(new_ids),
        "first_20": new_ids[:20],
    }
    frontier["last_updated_utc"] = fetch_utc
    FRONTIER_PATH.write_text(
        json.dumps(frontier, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    print(f"[catalog] legacy={len(legacy)} verified={len(verified)} "
          f"blocked={len(blocked)}", flush=True)
    print(f"[catalog] total catalog ids={len(all_ids)} "
          f"newly_discovered={len(new_ids)}", flush=True)
    print(f"[catalog] first 20: {new_ids[:20]}", flush=True)
    print(f"[catalog] frontier -> {FRONTIER_PATH.relative_to(ROOT)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())