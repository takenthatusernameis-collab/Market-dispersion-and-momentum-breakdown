import csv, json, unittest
from pathlib import Path

root = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-001"
ART = root / "artifacts" / EXP


def _json(name):
    return json.loads((ART / name).read_text())


class DataPipeline(unittest.TestCase):
    def test_data_gate_pass(self):
        dg = _json("data_gate.json")
        self.assertEqual(dg["status"], "PASS")
        self.assertTrue(all(c["status"] == "pass" for c in dg["checks"]))

    def test_data_gate_free_data(self):
        dg = _json("data_gate.json")
        acc = dg["free_data_access"]
        self.assertEqual(acc["coinmetrics_community_api"], "accessible")
        self.assertEqual(acc["binance_public_data_archive"], "accessible")
        self.assertEqual(acc["funding_source"], "accessible")

    def test_universe_coverage_columns(self):
        p = ART / "data" / "panels" / "universe_coverage.csv"
        self.assertTrue(p.exists())
        with p.open() as fh:
            header = fh.readline().strip().split(",")
        required = ["date", "rank", "asset_id", "contract_symbol",
                    "CapMrktEstUSD", "CapMrktCurUSD", "eligible",
                    "has_price", "has_funding", "included", "exclusion_reason"]
        for col in required:
            self.assertIn(col, header)

    def test_universe_ranking_monotonic(self):
        p = ART / "data" / "panels" / "universe_coverage.csv"
        with p.open() as fh:
            rows = list(csv.DictReader(fh))
        by_date = {}
        for r in rows:
            by_date.setdefault(r["date"], []).append(r)
        for date, group in by_date.items():
            elig = [r for r in group if r["eligible"] == "yes" and r["rank"] != ""]
            ranks = [int(r["rank"]) for r in elig]
            self.assertEqual(ranks, list(range(1, len(ranks) + 1)))

    def test_formation_returns_columns(self):
        p = ART / "formation_returns.csv"
        self.assertTrue(p.exists())
        with p.open() as fh:
            header = fh.readline().strip().split(",")
        required = ["formation_date", "n_assets", "dispersion",
                    "momentum_spread_gross", "momentum_spread_net_1x"]
        for col in required:
            self.assertIn(col, header)

    def test_marketcap_primary_full_coverage(self):
        mcm = _json("data/panels/marketcap_panel_manifest.json")
        cap_results = mcm["asset_results"]
        est_ok = sum(1 for v in cap_results.values()
                     if v["metrics"].get("CapMrktEstUSD", {}).get("status") == "ok")
        self.assertEqual(est_ok, len(mcm["assets_requested"]))


if __name__ == "__main__":
    unittest.main()
