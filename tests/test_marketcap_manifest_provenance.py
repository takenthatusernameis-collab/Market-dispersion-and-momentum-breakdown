"""Regression tests for the CoinMetrics market-cap panel manifest provenance.

2026-10-30 finding: ``scripts/refresh_free_data.py`` recorded ``time_first`` /
``time_last`` as ``rows[0]`` / ``rows[-1]`` of the raw CoinMetrics payload. The
CoinMetrics timeseries endpoint paginates in DESCENDING time order, so those
fields were inverted for 49 of 51 ok metric entries in the committed manifest
(e.g. btc CapMrktEstUSD time_first 2026-07-16 > time_last 2023-04-02). The same
bug left the per-entry ``rows`` count stale for 35 entries (the API returned
more observations than the truncated panel consumed) and would mislead any
downstream point-in-time eligibility check that reads the manifest instead of
the panel CSV.

The migration in ``scripts/fix_marketcap_manifest_boundaries.py`` recomputes
these fields from the files on disk. This test pins the corrected invariants so
the manifest can never drift back into an inverted, stale, or internally
inconsistent state:

  1. every ok metric entry has time_first <= time_last (no inverted boundary);
  2. every ok entry's ``rows`` equals the record count in its archived raw file;
  3. every ok entry's ``raw_sha256`` equals sha256 of the concatenation of its
     ``page_shas`` (the provenance hash is page-derived, not a file hash);
  4. the manifest's ``panel_sha256`` and ``panel_rows`` match the panel CSV on
     disk, and its ``start``/``end`` match the CSV's min/max date;
  5. the manifest's top-level ``assets_with_data`` equals the set of assets
     actually present in the panel CSV.

Read-only: no files are written.
"""
import csv
import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
ART = ROOT / "artifacts" / EXP
MANIFEST = ART / "data" / "panels" / "marketcap_panel_manifest.json"
PANEL = ART / "data" / "panels" / "marketcap_panel.csv"


def _manifest():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def _panel_rows():
    with PANEL.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


class MarketcapManifestProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.manifest = _manifest()
        self.rows = _panel_rows()

    def test_no_inverted_time_boundaries(self):
        bad = []
        for asset, entry in self.manifest["asset_results"].items():
            for metric, m in entry.get("metrics", {}).items():
                if m.get("status") != "ok" or not m.get("raw_path"):
                    continue
                tf, tl = m.get("time_first"), m.get("time_last")
                if tf is None or tl is None:
                    if m.get("rows", 0) != 0:
                        bad.append((asset, metric, "null boundary with rows"))
                    continue
                if tf > tl:
                    bad.append((asset, metric, tf, tl))
        self.assertEqual(bad, [], msg=f"inverted time_first/time_last: {bad}")

    def test_rows_count_matches_archived_raw_file(self):
        bad = []
        for asset, entry in self.manifest["asset_results"].items():
            for metric, m in entry.get("metrics", {}).items():
                if m.get("status") != "ok" or not m.get("raw_path"):
                    continue
                raw = ROOT / m["raw_path"]
                if not raw.exists():
                    bad.append((asset, metric, "MISSING"))
                    continue
                actual = len(json.loads(raw.read_text(encoding="utf-8")))
                if m.get("rows") != actual:
                    bad.append((asset, metric, m.get("rows"), actual))
        self.assertEqual(bad, [], msg=f"rows != raw record count: {bad}")

    def test_raw_sha256_matches_page_shas(self):
        bad = []
        for asset, entry in self.manifest["asset_results"].items():
            for metric, m in entry.get("metrics", {}).items():
                if m.get("status") != "ok" or not m.get("raw_path"):
                    continue
                pages = m.get("page_shas")
                if not pages:
                    bad.append((asset, metric, "no page_shas"))
                    continue
                calc = hashlib.sha256("".join(pages).encode()).hexdigest()
                if calc != m.get("raw_sha256"):
                    bad.append((asset, metric))
        self.assertEqual(bad, [], msg=f"raw_sha256 != sha256(page_shas): {bad}")

    def test_panel_sha256_and_rows_match_csv(self):
        actual_sha = hashlib.sha256(PANEL.read_bytes()).hexdigest()
        self.assertEqual(self.manifest["panel_sha256"], actual_sha,
                         msg="manifest panel_sha256 must match the panel CSV")
        self.assertEqual(self.manifest["panel_rows"], len(self.rows),
                         msg="manifest panel_rows must match the CSV row count")

    def test_panel_start_end_match_csv_min_max(self):
        dates = [r["date"] for r in self.rows if r.get("date")]
        self.assertEqual(self.manifest["start"], min(dates),
                         msg="manifest start must equal the panel CSV min date")
        self.assertEqual(self.manifest["end"], max(dates),
                         msg="manifest end must equal the panel CSV max date")

    def test_assets_with_data_matches_panel(self):
        panel_assets = sorted({r["asset"] for r in self.rows if r.get("asset")})
        self.assertEqual(sorted(self.manifest["assets_with_data"]), panel_assets,
                         msg="assets_with_data must equal the assets in the panel CSV")


if __name__ == "__main__":
    unittest.main()