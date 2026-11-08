"""Durable-state guard: latest_archive_probe must name a real cutoff-probe record.

The durable state files (research_state/universe_frontier.json and
research_state/run_manifest.json) each carry a `latest_archive_probe` object
hand-summarising the most recent live Binance archive probe. Those summaries
are prose + a few fields, and they are the only copy of the gate decision in
the durable state: a hand-rewritten summary that drifts from the record it
claims to quote is a single-source-of-truth hazard exactly like the stale
canonical-block sha256 that once propagated for several sessions.

This guard pins the summary to the record file it names, so the durable state
cannot silently point at a probe that does not exist, that has been deleted,
or that reports a different gate than the summary claims.

It is deliberately read-only and stdlib-only: it parses the two JSON state
files and the probe record JSON, and asserts field agreement. It makes no
network call and touches no artifact.
"""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "research_state"
PROBE_DIR = STATE / "cutoff_probe"


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


class LatestProbeRecordPinnedTests(unittest.TestCase):
    def _summaries(self):
        frontier = _load(STATE / "universe_frontier.json")
        manifest = _load(STATE / "run_manifest.json")
        return [
            ("universe_frontier.json", frontier["latest_archive_probe"]),
            ("run_manifest.json", manifest["latest_archive_probe"]),
        ]

    def _record_path(self, summary):
        rel = summary.get("record")
        self.assertIsNotNone(rel, "latest_archive_probe carries no record path")
        return ROOT / rel

    def test_record_path_is_under_cutoff_probe_dir(self):
        for label, summary in self._summaries():
            with self.subTest(file=label):
                path = self._record_path(summary)
                self.assertTrue(
                    str(path).startswith(str(PROBE_DIR)),
                    f"{label} latest_archive_probe.record {path} is not under "
                    f"research_state/cutoff_probe/",
                )

    def test_record_exists_and_parses(self):
        for label, summary in self._summaries():
            with self.subTest(file=label):
                path = self._record_path(summary)
                self.assertTrue(path.exists(), f"probe record missing on disk: {path}")
                record = _load(path)
                self.assertIn("cutoff_gate", record)
                self.assertIn("target_published", record)
                self.assertIn("probe_utc", record)

    def test_summary_gate_matches_record(self):
        for label, summary in self._summaries():
            with self.subTest(file=label):
                record = _load(self._record_path(summary))
                self.assertEqual(
                    summary["cutoff_gate"],
                    record["cutoff_gate"],
                    f"{label} claims gate {summary['cutoff_gate']} but its named "
                    f"record {record['record'] if 'record' in record else ''} "
                    f"reports {record['cutoff_gate']}",
                )
                self.assertEqual(
                    summary["target_published"],
                    record["target_published"],
                    f"{label} claims target_published "
                    f"{summary['target_published']} but its named record reports "
                    f"{record['target_published']}",
                )

    def test_summary_probe_utc_matches_record(self):
        for label, summary in self._summaries():
            with self.subTest(file=label):
                record = _load(self._record_path(summary))
                self.assertEqual(
                    summary["probe_utc"],
                    record["probe_utc"],
                    f"{label} claims probe_utc {summary['probe_utc']} but its "
                    f"named record reports {record['probe_utc']}",
                )

    def test_summary_probe_month_matches_record(self):
        for label, summary in self._summaries():
            with self.subTest(file=label):
                record = _load(self._record_path(summary))
                self.assertEqual(
                    summary["probe_month"],
                    record["probe_month"],
                    f"{label} claims probe_month {summary['probe_month']} but "
                    f"its named record reports {record['probe_month']}",
                )

    def test_summary_does_not_quote_a_record_that_does_not_exist(self):
        """A hand-rewritten summary pointing at a probe timestamp that was never
        written to disk must fail the build, rather than being accepted as a
        fresh gate decision.
        """
        for label, summary in self._summaries():
            with self.subTest(file=label):
                path = self._record_path(summary)
                self.assertTrue(
                    path.exists(),
                    f"{label} latest_archive_probe names {path}, which does not "
                    f"exist -- the gate decision has no auditable record",
                )


class LatestNovember2026ProbeRecordPinnedTests(unittest.TestCase):
    """Same guard as above, for the November 2026 gate summary.

    The durable state carries TWO probe summaries per file: ``latest_archive_probe``
    (the most recent published month, currently October 2026 UNBLOCKED) and
    ``latest_november_2026_probe`` (the target month the H10 fresh sealed block
    actually waits on, currently BLOCKED). The guard above only covered
    ``latest_archive_probe``, so the operative gate for the current task --
    the November summary quoted by the handoff, the task message, the frontier's
    next_action and the manifest's next_required_actions -- had no pin at all:
    a hand-rewritten November summary pointing at a deleted, divergent or
    invented record would have passed the build and been read as a live gate
    decision. That is the same single-source-of-truth hazard the archive
    summary guard exists for, applied to the summary that actually decides
    whether this session may advance the forward block.
    """

    def _summaries(self):
        frontier = _load(STATE / "universe_frontier.json")
        manifest = _load(STATE / "run_manifest.json")
        return [
            ("universe_frontier.json", frontier["latest_november_2026_probe"]),
            ("run_manifest.json", manifest["latest_november_2026_probe"]),
        ]

    def _record_path(self, summary):
        rel = summary.get("record")
        self.assertIsNotNone(rel, "latest_november_2026_probe carries no record path")
        return ROOT / rel

    def test_summary_targets_november_2026(self):
        for label, summary in self._summaries():
            with self.subTest(file=label):
                self.assertEqual(summary["probe_month"], "2026-11")

    def test_record_path_is_under_cutoff_probe_dir(self):
        for label, summary in self._summaries():
            with self.subTest(file=label):
                path = self._record_path(summary)
                self.assertTrue(
                    str(path).startswith(str(PROBE_DIR)),
                    f"{label} latest_november_2026_probe.record {path} is not "
                    f"under research_state/cutoff_probe/",
                )

    def test_record_exists_and_parses(self):
        for label, summary in self._summaries():
            with self.subTest(file=label):
                path = self._record_path(summary)
                self.assertTrue(path.exists(), f"probe record missing on disk: {path}")
                record = _load(path)
                self.assertIn("cutoff_gate", record)
                self.assertIn("target_published", record)
                self.assertIn("probe_utc", record)

    def test_summary_gate_matches_record(self):
        for label, summary in self._summaries():
            with self.subTest(file=label):
                record = _load(self._record_path(summary))
                self.assertEqual(
                    summary["cutoff_gate"],
                    record["cutoff_gate"],
                    f"{label} claims gate {summary['cutoff_gate']} but its named "
                    f"record reports {record['cutoff_gate']}",
                )
                self.assertEqual(
                    summary["target_published"],
                    record["target_published"],
                    f"{label} claims target_published "
                    f"{summary['target_published']} but its named record reports "
                    f"{record['target_published']}",
                )

    def test_summary_probe_utc_matches_record(self):
        for label, summary in self._summaries():
            with self.subTest(file=label):
                record = _load(self._record_path(summary))
                self.assertEqual(
                    summary["probe_utc"],
                    record["probe_utc"],
                    f"{label} claims probe_utc {summary['probe_utc']} but its "
                    f"named record reports {record['probe_utc']}",
                )

    def test_summary_probe_month_matches_record(self):
        for label, summary in self._summaries():
            with self.subTest(file=label):
                record = _load(self._record_path(summary))
                self.assertEqual(
                    summary["probe_month"],
                    record["probe_month"],
                    f"{label} claims probe_month {summary['probe_month']} but "
                    f"its named record reports {record['probe_month']}",
                )

    def test_summary_does_not_quote_a_record_that_does_not_exist(self):
        """A hand-rewritten November summary pointing at a probe timestamp that
        was never written to disk must fail the build, rather than being
        accepted as a fresh gate decision.
        """
        for label, summary in self._summaries():
            with self.subTest(file=label):
                path = self._record_path(summary)
                self.assertTrue(
                    path.exists(),
                    f"{label} latest_november_2026_probe names {path}, which does "
                    f"not exist -- the gate decision has no auditable record",
                )


if __name__ == "__main__":
    unittest.main()