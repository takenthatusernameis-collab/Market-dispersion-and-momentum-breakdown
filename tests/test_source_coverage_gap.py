"""Regression test for the source-coverage gap audit (DISP-003-SOURCECOV-001).

Documents the 24 assets that have Binance USDT perpetual futures but lack
Coin Metrics market-cap data, preventing their inclusion in the point-in-time
expanding universe. This is a structural source-coverage limitation, not a
fixable data gap.
"""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
ART = ROOT / "artifacts" / EXP
AUDIT_PATH = ART / "integrity_audit" / "source_coverage_gap_binance_no_capmkt_20261114.json"
VAL_PATH = ART / "data" / "panels" / "candidate_batch_validation.json"


class SourceCoverageGapTests(unittest.TestCase):
    def test_audit_artifact_exists_and_has_expected_structure(self):
        """The source-coverage gap audit artifact must exist and have the
        expected fields, including the list of 24 assets with Binance but no
        Coin Metrics market-cap data."""
        self.assertTrue(AUDIT_PATH.exists(), f"Audit artifact not found: {AUDIT_PATH}")
        audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))

        required_fields = [
            "audit_id", "title", "description", "status", "method",
            "findings", "binance_without_capmkt", "implications",
            "source_data", "generated_utc", "artifact_sha256"
        ]
        for field in required_fields:
            self.assertIn(field, audit, f"Missing required field: {field}")

        self.assertEqual(audit["audit_id"], "DISP-003-SOURCECOV-001")
        self.assertEqual(audit["status"], "EXPLORATORY_ONLY")

    def test_audit_identifies_exactly_24_assets_with_binance_no_capmkt(self):
        """The audit must identify exactly 24 assets that have Binance
        perpetuals but no Coin Metrics market-cap data."""
        audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
        assets = audit["binance_without_capmkt"]
        self.assertEqual(len(assets), 24, "Expected exactly 24 assets with Binance but no CapMkt")

        expected_assets = {
            "1000sats", "agix", "ai", "amb", "bake", "bnx", "btcst",
            "cocos", "combo", "defi", "edu", "flm", "hook", "id",
            "lever", "lina", "luna2", "magic", "mav", "nfp", "one",
            "ong", "phb", "rif"
        }
        actual_assets = {a["asset"] for a in assets}
        self.assertEqual(actual_assets, expected_assets)

    def test_audit_findings_match_candidate_validation_data(self):
        """The audit's summary counts must match a fresh scan of the
        candidate_batch_validation.json source data."""
        audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
        val = json.loads(VAL_PATH.read_text(encoding="utf-8"))

        binance_yes_capmkt_no = 0
        binance_yes_capmkt_yes = 0
        binance_no_capmkt_yes = 0
        binance_no_capmkt_no = 0

        for c in val.get("candidates_processed", []):
            binance_exists = c.get("binance", {}).get("exists", False)
            capmkt_served = any(
                m.get("status") != "asset_not_served"
                for m in c.get("metrics", {}).values()
            )

            if binance_exists and not capmkt_served:
                binance_yes_capmkt_no += 1
            elif binance_exists and capmkt_served:
                binance_yes_capmkt_yes += 1
            elif not binance_exists and capmkt_served:
                binance_no_capmkt_yes += 1
            elif not binance_exists and not capmkt_served:
                binance_no_capmkt_no += 1

        findings = audit["findings"]
        self.assertEqual(findings["binance_yes_capmkt_no"], binance_yes_capmkt_no)
        self.assertEqual(findings["binance_yes_capmkt_yes"], binance_yes_capmkt_yes)
        self.assertEqual(findings["binance_no_capmkt_yes"], binance_no_capmkt_yes)
        self.assertEqual(findings["binance_no_capmkt_no"], binance_no_capmkt_no)

    def test_audit_artifact_sha256_matches_content(self):
        """The recorded artifact_sha256 must match the file content excluding
        the artifact_sha256 field itself (so the hash is stable and
        self-referential)."""
        import hashlib
        audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
        recorded_sha = audit["artifact_sha256"]

        audit_no_sha = {k: v for k, v in audit.items() if k != "artifact_sha256"}
        content = json.dumps(audit_no_sha, sort_keys=True, indent=2) + "\n"
        actual_sha = hashlib.sha256(content.encode()).hexdigest()
        self.assertEqual(recorded_sha, actual_sha)


if __name__ == "__main__":
    unittest.main()