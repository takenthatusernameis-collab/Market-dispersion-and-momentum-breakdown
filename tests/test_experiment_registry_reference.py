"""Durable-state guard: artifact experiment ids resolve to the hypothesis registry.

Every committed artifact JSON under ``artifacts/`` that carries an
``experiment_id`` must name a hypothesis registered in
``research_state/hypothesis_registry.json`` (or a documented historical id that
predates / sits outside the registry). This is the same single-source-of-truth
hazard class previously repaired for H11/H16/H21: a committed artifact
referencing a hypothesis that was never allocated.

The check is deliberately id-explicit rather than prefix-based. A new experiment
id that is neither registered nor on the documented allowlist fails the build,
so a future id cannot silently fall outside the gate.

Scope: durable-state consistency only. No market data, no network, no secrets,
no trading endpoint. Reads local files only.
"""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
REGISTRY_PATH = ROOT / "research_state" / "hypothesis_registry.json"

# Ids that appear in committed artifacts but are intentionally not registry
# hypothesis experiment_ids. Each entry documents why. New ids must NOT be added
# here; they must be registered instead.
NON_REGISTRY_IDS = {
    # DISPERSION-001 IS registered (H1's experiment_id) and is intentionally not
    # listed here; only the closed DISPERSION-002 arm and the family id are.
    "HARMONY-CRYPTO-EDGE-004-DISPERSION-002": "DISPERSION-002 closed record; has no dedicated hypothesis entry.",
    # The DISPERSION-003 artifact family id itself (grid ledgers, panel manifests,
    # forward blocks). Individual sub-experiments carry their own registered ids.
    "HARMONY-CRYPTO-EDGE-004-DISPERSION-003": "DISPERSION-003 program-family id, not a single hypothesis.",
    # Diagnostic-audit slugs that differ textually from the registry's
    # experiment_id for the same audit (registry stores a descriptive id).
    "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-REGIME-001": "DISP-003-REGIME-001 slug; registry id is H004V106_DISPERSION_REGIME_CONDITIONING_20261028 (H14).",
    "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-REGIME-002": "DISP-003-REGIME-002 slug; registry id is H004V106_ROLLING_DISPERSION_WINDOW_20261028 (H20).",
    "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-TAILAUDIT-001": "DISP-003-TAILAUDIT-001 slug; registry id is H004V106_FORWARD_BLOCK_TAIL_INFLUENCE_AUDIT_20261029 (H18).",
    # Preserved-verbatim defective artifact: the first F1 repair audit recorded a
    # doubled program prefix before the 1-line id fix. Kept as history; the
    # operative audit uses the registered id.
    "HARMONY-CRYPTO-EDGE-004-HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1COVERAGE-001":
        "Defective doubled-prefix id preserved verbatim in the superseded F1 audit.",
}

DEFECTIVE_DOUBLED_ID = (
    "HARMONY-CRYPTO-EDGE-004-HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1COVERAGE-001"
)
DEFECTIVE_AUDIT_FILES = {
    "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1COVERAGE-001/"
    "integrity_audit/f1_panel_coverage_repair_20261112T172845Z.json",
    "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1COVERAGE-001/"
    "integrity_audit/f1_panel_coverage_repair_20261112T172913Z.json",
}
F1_OPERATIVE_AUDIT = (
    ARTIFACTS
    / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1COVERAGE-001"
    / "integrity_audit"
    / "f1_panel_coverage_repair_20261112T183449Z.json"
)


def iter_experiment_ids(obj):
    """Yield every string value stored under an ``experiment_id`` key."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == "experiment_id" and isinstance(value, str):
                yield value
            else:
                yield from iter_experiment_ids(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from iter_experiment_ids(item)


def scan_artifact_ids(root=ARTIFACTS):
    """Map experiment_id -> set of artifact paths (relative to repo root)."""
    found = {}
    for path in sorted(root.rglob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:  # pragma: no cover
            raise AssertionError(f"artifact is not valid JSON: {path}: {exc}")
        rel = path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else path.as_posix()
        for exp_id in iter_experiment_ids(data):
            found.setdefault(exp_id, set()).add(rel)
    return found


def load_registry():
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def check_artifact_ids(artifact_ids, registry_ids, allowlist):
    """Return the set of artifact ids that are neither registered nor allowlisted."""
    allowed = set(allowlist)
    return {i for i in artifact_ids if i not in registry_ids and i not in allowed}


class ExperimentRegistryReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = load_registry()
        cls.registry_ids = {
            h["experiment_id"] for h in cls.registry["hypotheses"] if h.get("experiment_id")
        }
        cls.artifact_ids = scan_artifact_ids()

    def test_registry_sequence_is_contiguous(self):
        n = self.registry["next_sequence_number"]
        ids = [h["id"] for h in self.registry["hypotheses"]]
        self.assertEqual(ids, [f"H{i}" for i in range(1, n + 1)])

    def test_every_artifact_experiment_id_is_registered_or_allowlisted(self):
        violations = check_artifact_ids(
            self.artifact_ids, self.registry_ids, NON_REGISTRY_IDS
        )
        self.assertEqual(
            violations,
            set(),
            "artifact experiment_id values are neither registered hypotheses nor "
            f"documented historical ids: {sorted(violations)}",
        )

    def test_allowlisted_ids_are_not_registered(self):
        overlap = set(NON_REGISTRY_IDS) & self.registry_ids
        self.assertEqual(
            overlap,
            set(),
            f"allowlist ids that are also registered (remove from allowlist): {sorted(overlap)}",
        )

    def test_unknown_id_is_flagged_by_the_check(self):
        violations = check_artifact_ids(
            {"HARMONY-CRYPTO-EDGE-004-DISPERSION-999-NEW"},
            self.registry_ids,
            NON_REGISTRY_IDS,
        )
        self.assertEqual(
            violations, {"HARMONY-CRYPTO-EDGE-004-DISPERSION-999-NEW"}
        )

    def test_defective_doubled_id_confined_to_known_historical_audits(self):
        locations = self.artifact_ids.get(DEFECTIVE_DOUBLED_ID, set())
        self.assertTrue(locations, "defective doubled-id audit is missing from disk")
        self.assertEqual(
            locations,
            DEFECTIVE_AUDIT_FILES,
            "defective doubled id must appear only in the two preserved historical F1 audits",
        )

    def test_no_registry_id_has_a_doubled_program_prefix(self):
        prefix = self.registry["program_id"] + "-"
        doubled = [i for i in self.registry_ids if i.startswith(prefix + self.registry["program_id"])]
        self.assertEqual(doubled, [], f"doubled-prefix registry ids: {doubled}")

    def test_operative_f1_audit_carries_registered_id(self):
        data = json.loads(F1_OPERATIVE_AUDIT.read_text(encoding="utf-8"))
        self.assertEqual(
            data["experiment_id"],
            "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1COVERAGE-001",
        )
        self.assertIn(data["experiment_id"], self.registry_ids)


if __name__ == "__main__":
    unittest.main()