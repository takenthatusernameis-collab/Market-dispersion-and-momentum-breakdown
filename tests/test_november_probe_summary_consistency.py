"""Guard: the two durable November 2026 probe summaries agree with each other,
with the record they name, and with every probe that predates the summary.

Two durable state files -- research_state/universe_frontier.json and
research_state/run_manifest.json -- each carry a hand-written
``latest_november_2026_probe`` summary of the live Binance archive probe for the
month the H10 fresh sealed block waits on. The existing guard
(tests/test_latest_probe_record_pinned.py) checks each summary against the single
record it names, but nothing checks that the TWO summaries agree with one another,
nor that the named record is representative of the other November probes on disk.
A one-sided hand edit (frontier updated, manifest not, or vice versa) would pass
every existing guard while leaving the durable state self-contradictory -- the
same single-source-of-truth hazard class the pinned-record guard exists for.

This guard is deliberately read-only and stdlib-only. It does NOT require the
summary to name the newest record: the pointer legitimately lags (the frontier and
manifest are updated in separate batches, and the durable task message forbids
altering the frontier this session), so the guard asserts agreement, unanimity of
the evidence the summary could have seen, representativeness, and a freshness
sanity check (the summary may never quote a record from the future), not
"must be newest".
"""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "research_state"
PROBE_DIR = STATE / "cutoff_probe"

SUMMARY_FIELDS = ("record", "probe_utc", "probe_month", "target_published", "cutoff_gate")


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _real_november_records():
    """Every committed, non-MOCK cutoff probe record whose probe_month is 2026-11."""
    out = []
    for p in sorted(PROBE_DIR.glob("cutoff_probe_*.json")):
        if "MOCK" in p.name:
            continue
        rec = _load(p)
        if rec.get("probe_month") == "2026-11":
            out.append((p, rec))
    return out


class NovemberProbeSummaryConsistencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = _real_november_records()
        cls.frontier = _load(STATE / "universe_frontier.json")["latest_november_2026_probe"]
        cls.manifest = _load(STATE / "run_manifest.json")["latest_november_2026_probe"]

    def _summaries(self):
        return [
            ("universe_frontier.json", self.frontier),
            ("run_manifest.json", self.manifest),
        ]

    def test_there_are_multiple_november_records(self):
        self.assertGreaterEqual(
            len(self.records), 2,
            "expected multiple November 2026 probe records on disk",
        )

    def test_frontier_and_manifest_summaries_agree(self):
        for field in SUMMARY_FIELDS:
            with self.subTest(field=field):
                self.assertEqual(
                    self.frontier[field], self.manifest[field],
                    f"frontier and manifest disagree on latest_november_2026_probe.{field}",
                )

    def test_summary_record_exists_and_is_a_november_record(self):
        for label, summary in self._summaries():
            with self.subTest(file=label):
                path = ROOT / summary["record"]
                self.assertTrue(path.exists(), f"{label} names missing record {path}")
                rec = _load(path)
                self.assertEqual(
                    rec.get("probe_month"), "2026-11",
                    f"{label} summary does not name a November 2026 record",
                )

    def test_summary_describes_the_unpublished_november_probe(self):
        for label, summary in self._summaries():
            with self.subTest(file=label):
                self.assertEqual(summary["probe_month"], "2026-11")
                self.assertFalse(
                    summary["target_published"],
                    f"{label} summary claims November 2026 is published",
                )
                self.assertEqual(summary["cutoff_gate"], "BLOCKED")

    def test_summary_is_not_newer_than_any_record_on_disk(self):
        newest = max(rec["probe_utc"] for _p, rec in self.records)
        for label, summary in self._summaries():
            with self.subTest(file=label):
                self.assertLessEqual(
                    summary["probe_utc"], newest,
                    f"{label} summary probe_utc {summary['probe_utc']} is newer than "
                    f"the newest record on disk {newest} -- it cannot quote a future probe",
                )

    def test_summary_verdict_is_unanimous_across_evidence_it_could_have_seen(self):
        for label, summary in self._summaries():
            with self.subTest(file=label):
                upto = [
                    rec for _p, rec in self.records
                    if rec["probe_utc"] <= summary["probe_utc"]
                ]
                self.assertGreater(
                    len(upto), 0,
                    f"{label} summary timestamp {summary['probe_utc']} predates every "
                    f"November record",
                )
                for rec in upto:
                    self.assertEqual(
                        rec["target_published"], summary["target_published"],
                        f"{label} summary is not representative: record {rec['probe_utc']} "
                        f"reports target_published={rec['target_published']}",
                    )
                    self.assertEqual(
                        rec["cutoff_gate"], summary["cutoff_gate"],
                        f"{label} summary is not representative: record {rec['probe_utc']} "
                        f"reports cutoff_gate={rec['cutoff_gate']}",
                    )

    def test_if_november_publishes_the_summary_must_track_the_newest_verdict(self):
        """Tripwire for the date-gated transition: once any real November probe
        reports the month published, the durable summaries must follow the newest
        record (and may no longer claim BLOCKED). This test is skipped while every
        November record still reports the month unpublished."""
        newest_path, newest = max(self.records, key=lambda kv: kv[1]["probe_utc"])
        if not newest["target_published"]:
            self.skipTest("November 2026 still unpublished on every on-disk record")
        for label, summary in self._summaries():
            with self.subTest(file=label):
                self.assertTrue(
                    summary["target_published"],
                    f"{label} still claims November 2026 unpublished after "
                    f"{newest_path.name} reported it published",
                )
                self.assertGreaterEqual(
                    summary["probe_utc"], newest["probe_utc"],
                    f"{label} summary has not caught up to the newest published probe",
                )


if __name__ == "__main__":
    unittest.main()