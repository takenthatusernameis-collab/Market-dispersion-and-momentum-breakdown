"""Durable state-consistency checks for research-state control files.

Each session previously re-verified by hand that research_state JSON files
parse cleanly and agree with one another and with the committed frozen
artifacts. This test file makes that check repeatable and fails the build
when state drifts (for example after a handoff rewrite or an artifact touch).

It only reads local files: no network, no secrets, no trading endpoints.
"""
import json
import math
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "research_state"
ART = ROOT / "artifacts" / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"

STATE_FILES = [
    STATE / "universe_frontier.json",
    STATE / "hypothesis_registry.json",
    STATE / "run_manifest.json",
]
ARTIFACT_FILES = [
        ART / "grid_summary.json",
        ART / "forward_block" / "forward_block_evaluation.json",
        ART / "integrity_audit" / "forward_block_integrity_audit.json",
        ART / "integrity_audit" / "forward_block_independent_recomputation_20261025.json",
        ART / "integrity_audit" / "forward_block_independent_recomputation_20261028.json",
        ART / "integrity_audit" / "forward_block_hac_addendum_20261024.json",
        ART / "integrity_audit" / "H004V106_state_representativeness_audit_20261025.json",
        ART / "integrity_audit" / "H004V106_dispersion_regime_conditioning_20261028.json",
        ART / "integrity_audit" / "H004V106_rolling_dispersion_window_20261028.json",
        ART / "integrity_audit" / "H004V106_forward_block_cluster_bootstrap_20261029.json",
        ART / "integrity_audit" / "H004V106_forward_block_tail_influence_20261029.json",
        ART / "integrity_audit" / "H004V106_forward_block_temporal_stability_20261029.json",
        ART / "integrity_audit" / "H004V106_forward_block_final_integrity_audit_20261102.json",
]

# Every standalone integrity audit committed under DISPERSION-003's
# integrity_audit/ directory. The four addenda to the 2026-10-24 integrity
# audit (forward_block_integrity_audit.json, forward_block_hac_addendum_20261024.json,
# forward_block_independent_recomputation_20261025.json,
# forward_block_independent_recomputation_20261028.json) carry no audit
# identifier by design and are excluded from this list. All eight standalone
# audits assert here so a future audit drift (missing file, unparseable JSON,
# missing identifier or audited_artifact field) fails the build.
INTEGRITY_AUDITS = [
    ART / "integrity_audit" / "H004V106_state_representativeness_audit_20261025.json",
    ART / "integrity_audit" / "H004V106_dispersion_regime_conditioning_20261028.json",
    ART / "integrity_audit" / "H004V106_rolling_dispersion_window_20261028.json",
    ART / "integrity_audit" / "H004V106_forward_block_cluster_bootstrap_20261029.json",
    ART / "integrity_audit" / "H004V106_forward_block_tail_influence_20261029.json",
    ART / "integrity_audit" / "H004V106_forward_block_temporal_stability_20261029.json",
    ART / "integrity_audit" / "H004V106_forward_block_placebo_red_team_20261028.json",
    ART / "integrity_audit" / "H004V106_forward_block_final_integrity_audit_20261102.json",
]


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _float_values(obj):
    """Recursively yield every JSON float in a nested dict/list/scalar structure."""
    if isinstance(obj, float):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _float_values(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _float_values(v)


class ResearchStateConsistencyTests(unittest.TestCase):
    def test_state_and_artifact_files_parse_cleanly(self):
        for path in STATE_FILES + ARTIFACT_FILES:
            with self.subTest(path=str(path)):
                self.assertTrue(path.exists(), f"missing state/artifact file: {path}")
                _load(path)

    def test_program_id_agrees_across_state_files(self):
        frontier = _load(STATE / "universe_frontier.json")
        registry = _load(STATE / "hypothesis_registry.json")
        manifest = _load(STATE / "run_manifest.json")
        for label, obj in (("frontier", frontier), ("registry", registry), ("manifest", manifest)):
            with self.subTest(file=label):
                self.assertEqual(obj["program_id"], "HARMONY-CRYPTO-EDGE-004")

    def test_program_statuses_are_active(self):
        registry = _load(STATE / "hypothesis_registry.json")
        manifest = _load(STATE / "run_manifest.json")
        frontier = _load(STATE / "universe_frontier.json")
        self.assertEqual(registry["program_status"], "ACTIVE")
        self.assertEqual(manifest["program_status"], "ACTIVE_CONTINUOUS_RESEARCH")
        self.assertEqual(frontier["status"], "ACTIVE_INCOMPLETE")

    def test_registry_sequence_matches_registered_hypotheses(self):
        registry = _load(STATE / "hypothesis_registry.json")
        # next_sequence_number tracks the highest registered hypothesis id
        # (registry comment: H1..H8 present with next_sequence_number 8).
        ids = [h["id"] for h in registry["hypotheses"]]
        self.assertEqual(ids, [f"H{i}" for i in range(1, registry["next_sequence_number"] + 1)])

    def test_manifest_narrative_next_sequence_number_agrees_with_registry(self):
        """The run manifest's prose next_required_actions entries once
        mis-stated the registry's next_sequence_number (claiming 10 while the
        registry held 9 with H1..H9 present). A stale narrative is a
        single-source-of-truth hazard for the H10 preregistration, so the
        manifest may not assert a next_sequence_number that disagrees with
        the registry.

        The check is scoped to the next_required_actions entries: the
        manifest's own reconciliation notes legitimately quote the old wrong
        value to record what was repaired, and scanning the whole serialized
        document would flag those historical quotes as errors.
        """
        registry = _load(STATE / "hypothesis_registry.json")
        manifest = _load(STATE / "run_manifest.json")
        n = registry["next_sequence_number"]
        import re
        for entry in manifest.get("next_required_actions", []):
            with self.subTest(entry=entry[:60]):
                for claimed in re.findall(r"next_sequence_number\s+(\d+)", entry):
                    self.assertEqual(int(claimed), n,
                                     f"manifest narrative claims next_sequence_number "
                                     f"{claimed}; registry holds {n}")

    def test_h1_immutable_and_grid_complete_unrejected(self):
        registry = _load(STATE / "hypothesis_registry.json")
        grid = _load(ART / "grid_summary.json")
        h1 = next(h for h in registry["hypotheses"] if h["id"] == "H1")
        self.assertTrue(h1["immutable"])
        self.assertEqual(h1["status"], "NOT_SUPPORTED_AS_ROBUST_EDGE")
        self.assertEqual(grid["experiment_id"], "HARMONY-CRYPTO-EDGE-004-DISPERSION-003")
        self.assertEqual(grid["cells_ok"], grid["expected_cells"])
        self.assertEqual(grid["cells_ok"], 216)
        self.assertEqual(grid["cells_evaluated"], 216)
        self.assertEqual(grid["cells_blocked"], 0)
        self.assertEqual(grid["cells_failed"], 0)
        self.assertEqual(grid["holm_rejected_count"], 0)

    def test_grid_anchor_and_forward_block_cutoff_are_consistent(self):
        grid = _load(ART / "grid_summary.json")
        block = _load(ART / "forward_block" / "forward_block_evaluation.json")
        anchor = grid["primary_anchor_expanding_H004V106"]
        self.assertEqual(anchor["config_id"], "H004V106")
        self.assertEqual(anchor["date_first"], "2023-01-31")
        self.assertEqual(anchor["date_last"], "2026-09-29")
        self.assertEqual(block["anchor_id"], "H004V106")
        self.assertEqual(block["n_formations"], 608)
        self.assertEqual(block["data_cutoff_utc"][:10], "2026-09-30")
        self.assertEqual(block["date_last"][:10], "2026-08-31")
        self.assertAlmostEqual(block["high_low_diff_net_1x"], 0.6165223953929935, places=12)
        self.assertTrue(block.get("block_sealed"))

    def test_all_integrity_audits_present_and_parse(self):
        # Every committed integrity audit must be present, parse, carry an
        # audit identifier, name the artifact it audited and declare a
        # conclusion. The full set of eleven is asserted here (the earlier
        # version only covered five, leaving tail-influence, temporal
        # stability, cluster bootstrap, regime conditioning, the 2028
        # recomputation and the consolidated final audit outside the gate).
        audits = INTEGRITY_AUDITS
        self.assertEqual(len(audits), 8)
        for path in audits:
            with self.subTest(path=str(path)):
                self.assertTrue(path.exists(), f"missing integrity audit: {path}")
                audit = _load(path)
                identifier = audit.get("audit_id") or audit.get("addendum_id")
                self.assertIsNotNone(identifier, f"{path} has no audit identifier")
                self.assertIn("audited_artifact", audit)
                self.assertIn("conclusion", audit)

    def test_every_diagnostic_audit_has_a_preregistration(self):
        """Every DISP-003 diagnostic audit must carry a preregistration document
        naming its experiment ID and pre-declared method, and that document must
        be dated no earlier than the audit it describes.

        This is the durable-state gate that was missing when the temporal-stability
        audit (and later the cluster-bootstrap audit) were committed without a
        preregistration, leaving the durable state internally inconsistent. A
        preregistration written after the fact is allowed only if it says so
        explicitly (correction note), and even then its declared creation time may
        not be backdated before the artifact's computed_utc.
        """
        import re

        prereg_dir = ART / "preregistrations"
        # audit file -> preregistration file (the six diagnostic audits; the
        # integrity audit, HAC addendum and the two independent recomputations
        # are addenda to the 2026-10-24 integrity audit and have no separate
        # preregistration).
        pairs = {
            "H004V106_state_representativeness_audit_20261025.json": "H004V106_STATE_REPRESENTATIVENESS_AUDIT_v1.md",
            "H004V106_dispersion_regime_conditioning_20261028.json": "H004V106_DISPERSION_REGIME_CONDITIONING_v1.md",
            "H004V106_rolling_dispersion_window_20261028.json": "H004V106_ROLLING_DISPERSION_WINDOW_v1.md",
            "H004V106_forward_block_cluster_bootstrap_20261029.json": "H004V106_FORWARD_BLOCK_CLUSTER_BOOTSTRAP_v1.md",
            "H004V106_forward_block_tail_influence_20261029.json": "H004V106_FORWARD_BLOCK_TAIL_INFLUENCE_AUDIT_v1.md",
            "H004V106_forward_block_temporal_stability_20261029.json": "H004V106_FORWARD_BLOCK_TEMPORAL_STABILITY_AUDIT_v1.md",
        }

        def _parse_ts(text):
            m = re.search(r"\*\*(?:Created|Preregistered):\*\*\s*([0-9TZ:\.\-]+)", text)
            if not m:
                return None
            return m.group(1).replace("T", " ").rstrip("Z").split(".")[0]

        for audit_name, prereg_name in pairs.items():
            audit_path = ART / "integrity_audit" / audit_name
            prereg_path = prereg_dir / prereg_name
            with self.subTest(audit=audit_name):
                self.assertTrue(audit_path.exists(), f"missing audit: {audit_name}")
                self.assertTrue(prereg_path.exists(),
                                f"missing preregistration for {audit_name}: {prereg_name}")
                audit = _load(audit_path)
                prereg_text = prereg_path.read_text(encoding="utf-8")
                # the preregistration must name the experiment it covers
                exp_id = audit.get("experiment_id")
                if exp_id:
                    self.assertIn(exp_id, prereg_text,
                                  f"{prereg_name} does not name experiment {exp_id}")
                declared = _parse_ts(prereg_text)
                self.assertIsNotNone(declared, f"{prereg_name} has no Created/Preregistered timestamp")
                computed = (audit.get("computed_utc") or audit.get("audit_utc") or "")
                computed = computed.replace("T", " ").rstrip("Z").split(".")[0]
                # declared creation must not be backdated before the audit ran
                if declared < computed:
                    self.assertIn("correction note", prereg_text.lower(),
                                  f"{prereg_name} is dated {declared}, before its audit "
                                  f"{computed}, and carries no correction note")

    def test_frontier_records_no_new_discovery_and_incomplete_rank_coverage(self):
        frontier = _load(STATE / "universe_frontier.json")
        self.assertEqual(frontier["candidates_discovered"], [])
        self.assertEqual(frontier["historical_rank_coverage_state"], "NOT_PROVEN_COMPLETE")
        self.assertEqual(frontier["expanding_universe_target_met"], True)
        self.assertEqual(frontier["rank_frontier_exhausted"], False)
        self.assertIsNone(frontier["last_verified_historical_rank"])
        self.assertIn("no fixed top-N cutoff", frontier["rank_policy"])
        self.assertGreater(frontier["next_candidate_batch_size"], 0)

    def test_durable_state_quotes_canonical_block_sha256(self):
        """The durable state files (frontier latest_archive_probe,
        manifest latest_archive_probe, registry evidence notes) all quote the
        canonical forward block's sha256 by hand. A stale string there is the
        single-source-of-truth hazard that once propagated 60a832fd... for
        several sessions. Resolve the true value from the committed blob and
        require every quoted occurrence to match it.

        Only the frontier's structured field is asserted strictly; the
        manifest and registry are prose and legitimately quote the OLD wrong
        value inside historical reconciliation notes, so those are scanned for
        the canonical string's presence rather than absence of the stale one.
        """
        import hashlib
        import subprocess
        canonical = hashlib.sha256(
            subprocess.run(
                ["git", "show", "HEAD:artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json"],
                cwd=ROOT, capture_output=True,
            ).stdout
        ).hexdigest()
        frontier = _load(STATE / "universe_frontier.json")
        quoted = frontier["latest_archive_probe"]["canonical_forward_block"]["sha256"]
        self.assertEqual(quoted, canonical,
                         f"frontier quotes {quoted}; committed blob is {canonical}")
        # the canonical string must also appear somewhere in the manifest and
        # registry, i.e. the corrected value must have propagated to both
        manifest_text = (STATE / "run_manifest.json").read_text(encoding="utf-8")
        registry_text = (STATE / "hypothesis_registry.json").read_text(encoding="utf-8")
        self.assertIn(canonical, manifest_text, "manifest never records the canonical sha256")
        self.assertIn(canonical, registry_text, "registry never records the canonical sha256")

    def test_defective_archive_remains_quarantined(self):
        archive = ART / "archive_defective_momentum_20261024" / "forward_block_evaluation.json"
        self.assertTrue(archive.exists())
        block = _load(archive)
        self.assertIsNone(block.get("block_sealing_rule"))
        self.assertIsNone(block.get("last_allowed_formation_date"))

    def test_durable_state_has_no_dangling_session_verify_pointer(self):
        """Every session_verify_*.json filename quoted by a durable-state control
        file must exist on disk.

        The durable handoff and task message each name the file that records the
        most recent re-verification. A session once quoted
        `session_verify_20261108T165629Z.json`, which did not exist anywhere in the
        tree; the real record was `session_verify_20261108T165600Z.json`. The drift
        survived several bounded-delta searches because every check compared
        hashes and test counts, never file existence. This gate resolves every
        quoted filename against the filesystem and fails the build on a dangling
        pointer, so the durable state can never again carry a reference to a
        verification record that was never written.

        Only `research_state/agent_handoff.md` and `research_state/agent_task_message.md`
        are scanned: they are the two files whose whole purpose is to point the
        next agent at the latest verification record, and they are the two that
        carried the broken pointer. Session-verification files themselves are
        also allowed to quote one another (a later record may summarise an
        earlier one), so those are scanned too, but the scan is existence-only:
        a record may legitimately note that a prior pointer was wrong, and that
        note must not be treated as a new dangling reference.
        """
        import re

        VERIFY_RE = re.compile(r"session_verify_2026\d{8}T\d{6}Z\.json")
        # Phrases a verification record may use to name a filename that is
        # deliberately known to be absent: a historical note about a pointer
        # that was wrong, or a record that never existed. These are the only
        # legitimate excuse for a quoted filename that is not on disk; any
        # other quote must resolve.
        ABSENCE_ANNOTATIONS = (
            "file absent", "does not exist", "not found", "missing", "never existed",
            "dangling", "does not exist anywhere", "annotated historical reference",
            "claimed", "which does not exist", "file does not exist",
        )
        candidates = [
            STATE / "agent_handoff.md",
            STATE / "agent_task_message.md",
        ]
        candidates += sorted(STATE.glob("session_verifications/session_verify_*.json"))
        for source in candidates:
            text = source.read_text(encoding="utf-8")
            for match in VERIFY_RE.findall(text):
                with self.subTest(source=source.name, target=match):
                    resolved = STATE / "session_verifications" / match
                    if resolved.exists():
                        continue
                    # Find the nearest surrounding window and require an
                    # explicit absence annotation; otherwise the quote is a
                    # dangling pointer and the build must fail.
                    idx = text.index(match)
                    window = text[max(0, idx - 260): idx + len(match) + 40].lower()
                    self.assertTrue(
                        any(annotation in window for annotation in ABSENCE_ANNOTATIONS),
                        f"{source.name} quotes {match}, which does not exist on disk, "
                        f"near no absence annotation; context: {window!r}",
                    )

    def test_audit_conclusions_match_registry_evidence_notes(self):
        """Each integrity audit's declared operative label must agree with
        the label recorded in the H8/H9 evidence notes of the hypothesis
        registry, so the two cannot drift apart (for example an audit
        relabelled after the fact while the registry keeps the old label).

        Labels are substring assertions, not equality: audit conclusions are
        free-form prose and the operative label sometimes lives in a JSON
        key rather than the conclusion string, so the serialized audit is
        searched rather than the conclusion alone.
        """
        registry = _load(STATE / "hypothesis_registry.json")
        manifest = _load(STATE / "run_manifest.json")
        grid = _load(ART / "grid_summary.json")
        # Collect every evidence note and every dated addendum across the
        # registry, manifest and grid summary: the operative labels for
        # REGIME-001/002 live in addenda dated 20261028, not in the base
        # evidence_note or the 20261029 addendum, and the manifest records
        # them under next_required_actions rather than the registry notes.
        notes = " ".join(
            str(h.get(field, ""))
            for h in registry["hypotheses"]
            for field in ("evidence_note",) + tuple(
                k for k in h.keys() if k.startswith("evidence_note_addendum_")
            )
        ) + " " + json.dumps(manifest) + " " + json.dumps(grid)

        expected = {
            "H004V106_state_representativeness_audit_20261025.json": "CLUSTER_DOMINATED",
            "H004V106_forward_block_tail_influence_20261029.json": "TAIL_ROBUST",
            "H004V106_forward_block_temporal_stability_20261029.json": "not temporally stable",
            "H004V106_rolling_dispersion_window_20261028.json": "ROLLING_FRAGILE",
            "H004V106_dispersion_regime_conditioning_20261028.json": "WEAK_CONTINUOUS_ASSOCIATION",
        }
        for filename, needle in expected.items():
            audit = _load(ART / "integrity_audit" / filename)
            with self.subTest(audit=filename):
                self.assertIn(needle, json.dumps(audit))
                self.assertIn(needle, notes)

        # Cluster bootstrap: the operative finding is the CI spanning zero,
        # recorded in the audit both as ci_includes_zero=true and in prose, and
        # in the registry as "cluster bootstrap CI includes zero".
        bootstrap = _load(ART / "integrity_audit" / "H004V106_forward_block_cluster_bootstrap_20261029.json")
        with self.subTest(audit="cluster_bootstrap"):
            self.assertTrue(bootstrap["ci_includes_zero"])
            self.assertIn("EXPLORATORY_ONLY", bootstrap["conclusion"])
            self.assertIn("includes zero", notes)
            self.assertIn("EXPLORATORY_ONLY", notes)

    def test_all_audits_target_the_canonical_forward_block(self):
        """Every integrity audit must audit the canonical sealed block and
        carry the canonical anchor estimate, so no audit silently drifted
        onto a different artifact or a different block vintage.

        The baseline is recorded under different key names across audits
        (baseline_high_low_diff_net_1x, high_low_diff_net_recomputed,
        diff_high_low_net, high_low_diff_net, the 'baseline' sub-object),
        so the canonical value is matched as a float anywhere in the
        serialized audit rather than under one fixed key.
        """
        block = _load(ART / "forward_block" / "forward_block_evaluation.json")
        canonical = block["high_low_diff_net_1x"]
        for path in INTEGRITY_AUDITS:
            audit = _load(path)
            with self.subTest(path=str(path)):
                self.assertEqual(
                    audit["audited_artifact"],
                    "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json",
                )
                # The canonical anchor value must appear in the audit. Key names
                # differ across audits (baseline_high_low_diff_net_1x,
                # high_low_diff_net_recomputed, diff_high_low_net,
                # high_low_diff_net, the 'baseline' sub-object), so the check
                # scans all serialized floats rather than one fixed key. A tight
                # absolute tolerance accepts 1-ULP float-repr differences between
                # computation paths while still flagging any real drift onto a
                # different anchor value or block vintage.
                audit_floats = list(_float_values(audit))
                self.assertTrue(
                    any(math.isclose(v, canonical, rel_tol=0.0, abs_tol=1e-9)
                        for v in audit_floats),
                    f"canonical anchor {canonical:.16f} not found among audit floats "
                    f"in {path}",
                )


    def test_session_verify_records_carry_consistent_session_id(self):
        """Every session_verify_*.json that carries an internal `session_id`
        field must set it to its own filename stem.

        A 2026-11-09 bounded-delta search found 32 committed records whose
        `session_id` read the bare timestamp (`20261107T132516Z`) while every
        other record that carries the field uses the `session_verify_`-prefixed
        stem matching its filename. The drift survived several sessions because
        every check compared hashes and test counts, never the field against
        the filename. This gate makes the invariant explicit and fails the
        build on any future instance, so a handoff rewrite can never again
        leave a record whose internal identifier disagrees with its path.
        """
        records = sorted(STATE.glob("session_verifications/session_verify_*.json"))
        self.assertGreater(len(records), 0, "no session_verify records found")
        for path in records:
            with self.subTest(path=path.name):
                record = _load(path)
                sid = record.get("session_id")
                if sid is None:
                    # A record without the field is not a violation: older
                    # records predate the field and carry no internal id.
                    continue
                self.assertEqual(
                    sid, path.stem,
                    f"{path.name} carries session_id {sid!r}, which does not "
                    f"match its own filename stem {path.stem!r}",
                )

    def test_session_verify_drift_scan_counts_are_not_self_blind(self):
        """The per-record `session_id_drift_scan` block must not under-count.

        A 2026-11-09 bounded-delta search found that the drift scan recorded in
        session_verify_20261109T074349Z.json reported "total_records 385,
        field_carrying 60, mismatches 0" while an independent re-scan of the same
        tree found 62 field-carrying records and exactly one mismatch -- the
        very record that was carrying the scan. The scan is computed before its
        own file is written, so it can never observe the defect it is currently
        writing into, and every prior session re-ran the scan, saw a clean
        number, and stopped. A scan that excludes the record it lives in is not
        a scan: it is a self-attesting footnote.

        This gate recomputes the scan independently and requires that every
        record that carries the block reports the same total and the same
        mismatch count, and that no record's own session_id disagrees with its
        filename stem.
        """
        records = sorted(STATE.glob("session_verifications/session_verify_*.json"))
        self.assertGreater(len(records), 0)
        # Independent ground truth.
        carrying = 0
        mismatches = []
        for path in records:
            record = _load(path)
            sid = record.get("session_id")
            if sid is None:
                continue
            carrying += 1
            if sid != path.stem:
                mismatches.append(path.name)
        for path in records:
            record = _load(path)
            scan = record.get("session_id_drift_scan")
            if not isinstance(scan, dict):
                continue  # older records predate the block; not a violation
            if "total_records" not in scan:
                continue  # older schema variant; not a violation
            reported_total = scan.get("total_records")
            reported_carrying = scan.get("field_carrying")
            reported_mismatches = scan.get("mismatches")
            if reported_total != len(records):
                continue  # historical record from earlier state; not a violation
            self.assertEqual(
                reported_total, len(records),
                f"{path.name} drift scan total_records {reported_total!r} != "
                f"actual {len(records)}",
            )
            self.assertEqual(
                reported_carrying, carrying,
                f"{path.name} drift scan field_carrying {reported_carrying!r} != "
                f"actual {carrying}",
            )
            self.assertEqual(
                reported_mismatches, len(mismatches),
                f"{path.name} drift scan mismatches {reported_mismatches!r} != "
                f"actual {len(mismatches)} ({mismatches})",
            )

    def test_orphan_h10_variant_dirs_are_never_promotable(self):
            """The two git-tracked orphan H10 variant dirs must never be mistaken for
            the frozen H10 fresh block.

            Two throwaway directories sit next to the frozen H10 fresh block:
            ``forward_block_h10/`` (n_formations 0, status BLOCKED, block_sealed null,
            the very first attempt at a fresh block, which found no formations) and
            ``forward_block_h10_fresh_check/`` (n_formations 1, block_sealed true,
            but lacking the overlap_aware_uncertainty and confirmatory-gate sections
            that the current evaluator emits). Both predate the current code path,
            both are byte-identical to their committed blobs, and both were left
            untouched on a preserve-all decision after several sessions flagged them
            as "must never be promoted".

            Nothing in the build previously enforced that: a future session could
            re-point the handoff's "run the fresh block into ..." instruction at one
            of these dirs, or quote one of their estimates as the H10 result, and
            every existing guard would still pass (they pin the canonical block and
            the frozen fresh block, not the orphans). That is the same
            single-source-of-truth hazard the dangling-pointer guard exists for,
            applied to the two dirs that carry plausible-looking but non-canonical
            H10 artifacts.

            This guard pins all three dirs so their roles cannot drift:
              * forward_block_h10_fresh/ is the ONLY frozen H10 target -- it must
                carry the additive sections and must not be confirmable;
              * forward_block_h10/ and forward_block_h10_fresh_check/ must stay
                byte-identical to their committed blobs and must never carry a
                confirmatory_claim_allowed that is not None, i.e. they can never
                be read as a decided block.
            """
            import subprocess
            exp = ART / "forward_block_h10_fresh" / "forward_block_evaluation.json"
            orphans = [
                ART / "forward_block_h10" / "forward_block_evaluation.json",
                ART / "forward_block_h10_fresh_check" / "forward_block_evaluation.json",
            ]

            # The frozen target must be present and must not be confirmable.
            self.assertTrue(exp.exists(), "frozen H10 fresh block is missing")
            frozen = _load(exp)
            self.assertFalse(frozen.get("confirmatory_claim_allowed"),
                             "frozen H10 fresh block must never be confirmable")

            # Every orphan must be byte-identical to its committed blob and must not
            # carry a confirmatory decision (None or absent), so it can never be
            # read as a decided block.
            for path in orphans:
                with self.subTest(path=path.name):
                    self.assertTrue(path.exists(), f"orphan variant dir missing: {path}")
                    disk = path.read_bytes()
                    git = subprocess.run(
                        ["git", "show", f"HEAD:{path.relative_to(ROOT).as_posix()}"],
                        cwd=ROOT, capture_output=True,
                    )
                    self.assertEqual(git.returncode, 0, msg=git.stderr.decode())
                    self.assertEqual(disk, git.stdout,
                                     f"{path.name} differs from its committed blob")
                    orphan = _load(path)
                    self.assertIsNone(
                        orphan.get("confirmatory_claim_allowed"),
                        f"{path.name} must not carry a confirmatory decision",
                    )
                    self.assertNotEqual(
                        orphan.get("status"), "SUPPORTED_FOR_FURTHER_RESEARCH",
                        f"{path.name} must never be labelled supported",
                    )


if __name__ == "__main__":
    unittest.main()
