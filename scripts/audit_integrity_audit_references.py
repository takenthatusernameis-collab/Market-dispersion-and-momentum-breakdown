#!/usr/bin/env python3
"""Read-only consistency audit over integrity_audit/ JSON artifacts.

Checks each audit JSON for:
- referenced artifact paths exist on disk (common pointer fields);
- recorded sha256/hash fields for audited artifacts match current disk bytes;
- basic ID/filename consistency hints (audit_id/addendum_id vs filename stem);
- JSON parseability and structural sanity.

Writes a new timestamped audit artifact under research_state/ by default.
Does NOT modify any existing artifact, config, or result.

Usage:
    python3 scripts/audit_integrity_audit_references.py [--out PATH]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
AUDIT_DIR = ROOT / "artifacts" / EXP / "integrity_audit"
STATE_DIR = ROOT / "research_state"

# Known frozen hashes (handoff-verified); mismatch is a critical finding.
FROZEN = {
    "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json":
        "7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390",
    "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/forward_block_evaluation.json":
        "9bdee66f737e492b3302a730af29ab9f811611e5a908ccf6002d08eab3e8bc5a",
}

PATH_KEYS = (
    "audited_artifact", "artifact_path", "canonical_artifact", "fresh_artifact",
    "evaluation_json", "source_artifact", "archived_artifact", "target_artifact",
)
HASH_KEYS = (
    "artifact_sha256", "audited_artifact_sha256", "canonical_sha256",
    "fresh_sha256", "expected_sha256", "hash", "sha256", "input_hash",
)
ID_KEYS = ("audit_id", "addendum_id", "experiment_id", "artifact_id")


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def git_head_sha256(repo_rel: str) -> str | None:
    """Return sha256 of `git show HEAD:<repo_rel>`, or None if not tracked/unavailable."""
    try:
        r = subprocess.run(
            ["git", "show", f"HEAD:{repo_rel}"],
            cwd=ROOT, capture_output=True, check=False,
        )
        if r.returncode != 0 or not r.stdout:
            return None
        return hashlib.sha256(r.stdout).hexdigest()
    except Exception:  # noqa: BLE001
        return None


def _norm_repo_path(v: str) -> Path:
    if v.startswith("/"):
        return Path(v)
    return ROOT / v


def audit_one(p: Path) -> dict:
    row = {
        "file": p.name,
        "parse_ok": False,
        "references": [],
        "recorded_hash_checks": [],
        "id_consistency": [],
        "findings": [],
        "severity": "OK",
    }
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        row["parse_ok"] = True
    except Exception as e:  # noqa: BLE001
        row["findings"].append(f"JSON parse error: {e!r}")
        row["severity"] = "CRITICAL"
        return row

    # Reference/path checks
    seen_paths = []
    for k in PATH_KEYS:
        v = d.get(k)
        if not isinstance(v, str):
            continue
        seen_paths.append((k, v))
        fp = _norm_repo_path(v)
        exists = fp.exists() and fp.is_file()
        disk_hash = sha256_file(fp) if exists else None
        frozen_expected = FROZEN.get(v.replace("\\", "/"))
        repo_rel = v.replace("\\", "/")
        git_hash = git_head_sha256(repo_rel) if exists else None
        ref = {"key": k, "path": v, "exists": exists, "disk_sha256": disk_hash,
               "git_head_sha256": git_hash,
               "matches_git_head": (git_hash is None or disk_hash == git_hash),
               "frozen_expected": frozen_expected,
               "matches_frozen": (frozen_expected is None or disk_hash == frozen_expected)}
        row["references"].append(ref)
        if not exists:
            row["findings"].append(f"missing referenced artifact: {k}={v}")
        if frozen_expected and disk_hash and disk_hash != frozen_expected:
            row["findings"].append(
                f"FROZEN HASH MISMATCH: {k}={v} disk={disk_hash} expected={frozen_expected}")
        if git_hash and disk_hash and disk_hash != git_hash:
            row["findings"].append(
                f"GIT HEAD HASH MISMATCH: {k}={v} disk={disk_hash} git_head={git_hash}")

    # Recorded hash checks (compare recorded hash to disk for any referenced path)
    disk_by_path = {r["path"]: r["disk_sha256"] for r in row["references"]}
    for hk in HASH_KEYS:
        if hk not in d:
            continue
        recorded = d[hk]
        if not isinstance(recorded, str) or not re.fullmatch(r"[0-9a-f]{64}", recorded):
            continue
        target = None
        for pk in ("audited_artifact", "canonical_artifact", "artifact_path", "fresh_artifact"):
            if isinstance(d.get(pk), str):
                target = d[pk]
                break
        disk = disk_by_path.get(target) if target else None
        match = (disk == recorded) if disk else None
        chk = {"hash_key": hk, "recorded": recorded, "target_path": target,
               "disk_sha256": disk, "match": match}
        row["recorded_hash_checks"].append(chk)
        if match is False:
            row["findings"].append(
                f"recorded hash mismatch: {hk} for {target} recorded={recorded} disk={disk}")

    # ID consistency (informational)
    stem = p.stem
    for ik in ID_KEYS:
        v = d.get(ik)
        if not isinstance(v, str):
            continue
        norm_v = re.sub(r"[^a-z0-9]+", "", v.lower())
        norm_s = re.sub(r"[^a-z0-9]+", "", stem.lower())
        consistent = norm_v in norm_s or norm_s in norm_v or norm_v[:20] in norm_s
        row["id_consistency"].append({"id_key": ik, "id_value": v, "filename_stem": stem,
                                      "loose_match": consistent})
        if not consistent:
            row["findings"].append(
                f"ID/filename loose mismatch (informational): {ik}={v} vs {stem}")

    if any("FROZEN HASH MISMATCH" in f or "GIT HEAD HASH MISMATCH" in f or "parse error" in f for f in row["findings"]):
        row["severity"] = "CRITICAL"
    elif any("missing referenced artifact" in f or "recorded hash mismatch" in f for f in row["findings"]):
        row["severity"] = "ERROR"
    elif row["findings"]:
        row["severity"] = "INFO"
    return row


def run_audit() -> dict:
    files = sorted(p for p in AUDIT_DIR.glob("*.json") if p.is_file())
    rows = [audit_one(p) for p in files]
    critical = [r["file"] for r in rows if r["severity"] == "CRITICAL"]
    errors = [r["file"] for r in rows if r["severity"] == "ERROR"]
    info = [r["file"] for r in rows if r["severity"] == "INFO"]
    frozen_git_checks = []
    for rel, expected in FROZEN.items():
        fp = ROOT / rel
        disk = sha256_file(fp) if fp.is_file() else None
        gh = git_head_sha256(rel)
        chk = {"path": rel, "expected_frozen": expected, "disk_sha256": disk,
               "git_head_sha256": gh,
               "matches_frozen": disk == expected if disk else False,
               "matches_git_head": (disk == gh) if (disk and gh) else None}
        frozen_git_checks.append(chk)
        if disk and disk != expected:
            critical.append(f"FROZEN_DRIFT:{rel}")
        if disk and gh and disk != gh:
            critical.append(f"GIT_HEAD_DRIFT:{rel}")
    return {
        "audit_id": "INTEGRITY_AUDIT_REFERENCE_CONSISTENCY",
        "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "audited_dir": str(AUDIT_DIR.relative_to(ROOT)),
        "files_scanned": len(rows),
        "critical": sorted(set(critical)),
        "errors": errors,
        "info": info,
        "pass": len(set(critical)) == 0 and len(errors) == 0,
        "frozen_hashes_checked": FROZEN,
        "frozen_git_head_checks": frozen_git_checks,
        "rows": rows,
        "scope_note": (
            "Read-only consistency scan over integrity_audit JSONs plus frozen/git-HEAD cross-checks. INFO findings "
            "(e.g. ID/filename loose mismatch for addenda or legacy naming) are "
            "recorded but do not fail the audit. CRITICAL/ERROR indicate stale "
            "pointers or hash mismatches requiring investigation. Does not modify "
            "any existing artifact/config/result. Default output: research_state/."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=None,
                    help="Output path (default: research_state/INTEGRITY_AUDIT_REFERENCE_CONSISTENCY_<ts>.json)")
    args = ap.parse_args()
    res = run_audit()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    if args.out:
        out_path = Path(args.out)
        if not out_path.is_absolute():
            out_path = ROOT / out_path
    else:
        out_path = STATE_DIR / f"INTEGRITY_AUDIT_REFERENCE_CONSISTENCY_{stamp}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(res, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[integrity-audit-ref] pass={res['pass']} scanned={res['files_scanned']} "
          f"critical={len(res['critical'])} errors={len(res['errors'])} info={len(res['info'])}")
    print(f"[integrity-audit-ref] wrote {out_path.relative_to(ROOT)}")
    return 0 if res["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
