#!/usr/bin/env python3
"""Read-only consistency audit over preregistration docs and h10_fresh artifacts.

Scans:
- artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/preregistrations/*.md for
  repo-relative artifact/research_state path references and 64-char SHA256 refs;
  verifies referenced paths exist on disk and frozen hashes match where applicable.
- artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/*
  JSON files for path/hash reference fields and frozen/git-HEAD consistency.

Writes a timestamped report under research_state/ by default. DOES NOT modify
any existing artifact, config, preregistration, or result.

Usage:
    python3 scripts/audit_prereg_and_h10_fresh_references.py [--out PATH]
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
PREREG_DIR = ROOT / "artifacts" / EXP / "preregistrations"
H10_DIR = ROOT / "artifacts" / EXP / "forward_block_h10_fresh"
STATE_DIR = ROOT / "research_state"

FROZEN = {
    "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json":
        "7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390",
    "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/forward_block_evaluation.json":
        "9bdee66f737e492b3302a730af29ab9f811611e5a908ccf6002d08eab3e8bc5a",
}

PATH_RE = re.compile(
    r"`?((?:artifacts|research_state|scripts|tests)/[A-Za-z0-9_./\-]+?\.(?:json|md|csv|py))`?"
)
HASH_RE = re.compile(r"\b([0-9a-f]{64})\b")
PATH_KEYS = (
    "audited_artifact", "artifact_path", "canonical_artifact", "fresh_artifact",
    "evaluation_json", "source_artifact", "archived_artifact", "target_artifact",
    "output_dir", "data_cutoff_source",
)
HASH_KEYS = (
    "artifact_sha256", "audited_artifact_sha256", "canonical_sha256",
    "fresh_sha256", "expected_sha256", "hash", "sha256", "input_hash",
)


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def git_head_sha256(repo_rel: str) -> str | None:
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


def _norm(v: str) -> str:
    return v.replace("\\", "/").lstrip("./")


def _path_like(v: str) -> bool:
    """True only when a string value names a repo artifact path.

    PATH_KEYS collects fields that *may* name artifacts, but several of them
    also carry free-text descriptions (e.g. ``data_cutoff_source`` =
    "derived from latest fully closed UTC daily Binance kline candle (or
    --data-cutoff)"). Without a shape guard every non-empty string in those
    fields is treated as a path reference and reported as a missing artifact,
    which is a false positive, not a defect. A genuine path reference must
    contain a forward slash and end with a known artifact extension; prose
    values fail both and are skipped. This is a tightening, not a loosening:
    if a prose field ever does name a real file it is still caught.
    """
    if not isinstance(v, str) or not v.strip():
        return False
    s = v.strip().replace("\\", "/")
    return "/" in s and s.lower().rsplit(".", 1)[-1] in {"json", "md", "csv", "py"}


def audit_prereg_md(p: Path) -> dict:
    text = p.read_text(encoding="utf-8")
    row = {
        "file": p.name,
        "kind": "preregistration_md",
        "path_refs": [],
        "hash_refs": [],
        "findings": [],
        "severity": "OK",
    }
    seen = set()
    for m in PATH_RE.finditer(text):
        raw = _norm(m.group(1))
        if raw in seen:
            continue
        seen.add(raw)
        fp = ROOT / raw
        exists = fp.exists() and fp.is_file()
        frozen_expected = FROZEN.get(raw)
        disk = sha256_file(fp) if exists else None
        ref = {"path": raw, "exists": exists, "disk_sha256": disk,
               "frozen_expected": frozen_expected,
               "matches_frozen": (frozen_expected is None or disk == frozen_expected)}
        row["path_refs"].append(ref)
        if not exists:
            # Known frozen canonical path typo pattern? report as finding.
            row["findings"].append(f"missing referenced path: {raw}")
        if frozen_expected and disk and disk != frozen_expected:
            row["findings"].append(
                f"FROZEN HASH MISMATCH: {raw} disk={disk} expected={frozen_expected}")
    for h in sorted(set(HASH_RE.findall(text))):
        frozen_path = next((k for k, v in FROZEN.items() if v == h), None)
        row["hash_refs"].append({"sha256": h, "matches_known_frozen": frozen_path})
    if any("FROZEN HASH MISMATCH" in f for f in row["findings"]):
        row["severity"] = "CRITICAL"
    elif row["findings"]:
        row["severity"] = "ERROR"
    return row


def audit_h10_json(p: Path) -> dict:
    row = {
        "file": p.name,
        "kind": "h10_fresh_json",
        "references": [],
        "recorded_hash_checks": [],
        "findings": [],
        "severity": "OK",
    }
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        row["findings"].append(f"JSON parse error: {e!r}")
        row["severity"] = "CRITICAL"
        return row
    for k in PATH_KEYS:
        v = d.get(k)
        if not _path_like(v):
            continue
        raw = _norm(v)
        fp = ROOT / raw if not raw.startswith("/") else Path(raw)
        exists = fp.exists() and fp.is_file()
        disk = sha256_file(fp) if exists else None
        frozen_expected = FROZEN.get(raw)
        git_hash = git_head_sha256(raw) if exists else None
        ref = {"key": k, "path": raw, "exists": exists, "disk_sha256": disk,
               "git_head_sha256": git_hash,
               "matches_git_head": (git_hash is None or disk == git_hash),
               "frozen_expected": frozen_expected,
               "matches_frozen": (frozen_expected is None or disk == frozen_expected)}
        row["references"].append(ref)
        if not exists:
            row["findings"].append(f"missing referenced artifact: {k}={raw}")
        if frozen_expected and disk and disk != frozen_expected:
            row["findings"].append(f"FROZEN HASH MISMATCH: {k}={raw}")
        if git_hash and disk and disk != git_hash:
            row["findings"].append(f"GIT HEAD HASH MISMATCH: {k}={raw}")
    disk_by_path = {r["path"]: r["disk_sha256"] for r in row["references"]}
    for hk in HASH_KEYS:
        if hk not in d:
            continue
        recorded = d[hk]
        if not isinstance(recorded, str) or not re.fullmatch(r"[0-9a-f]{64}", recorded):
            continue
        target = next((d[pk] for pk in ("audited_artifact", "canonical_artifact", "artifact_path", "fresh_artifact") if isinstance(d.get(pk), str)), None)
        target_n = _norm(target) if target else None
        disk = disk_by_path.get(target_n) if target_n else None
        match = (disk == recorded) if disk else None
        row["recorded_hash_checks"].append({"hash_key": hk, "recorded": recorded, "target_path": target_n, "disk_sha256": disk, "match": match})
        if match is False:
            row["findings"].append(f"recorded hash mismatch: {hk} for {target_n}")
    # frozen self-check for known file
    rel_self = str(p.relative_to(ROOT)).replace("\\", "/")
    if rel_self in FROZEN:
        actual = sha256_file(p)
        if actual != FROZEN[rel_self]:
            row["findings"].append(f"FROZEN SELF HASH MISMATCH: {rel_self}")
    if any("FROZEN HASH MISMATCH" in f or "GIT HEAD HASH MISMATCH" in f or "parse error" in f for f in row["findings"]):
        row["severity"] = "CRITICAL"
    elif any("missing referenced artifact" in f or "recorded hash mismatch" in f for f in row["findings"]):
        row["severity"] = "ERROR"
    elif row["findings"]:
        row["severity"] = "INFO"
    return row


def run_audit(prereg_dir: Path | None = None, h10_dir: Path | None = None) -> dict:
    prereg_dir = prereg_dir or PREREG_DIR
    h10_dir = h10_dir or H10_DIR
    prereg_rows = [audit_prereg_md(p) for p in sorted(prereg_dir.glob("*.md")) if p.is_file()] if prereg_dir.exists() else []
    h10_rows = [audit_h10_json(p) for p in sorted(h10_dir.glob("*.json")) if p.is_file()] if h10_dir.exists() else []
    rows = prereg_rows + h10_rows
    critical = [f"{r['file']}:{f}" for r in rows for f in r["findings"] if r["severity"] == "CRITICAL"]
    errors = [f"{r['file']}:{f}" for r in rows for f in r["findings"] if r["severity"] == "ERROR"]
    infos = [f"{r['file']}:{f}" for r in rows for f in r["findings"] if r["severity"] == "INFO"]
    frozen_checks = []
    for rel, expected in FROZEN.items():
        fp = ROOT / rel
        disk = sha256_file(fp) if fp.is_file() else None
        gh = git_head_sha256(rel)
        frozen_checks.append({"path": rel, "expected": expected, "disk_sha256": disk,
                              "git_head_sha256": gh,
                              "matches_frozen": disk == expected if disk else False,
                              "matches_git_head": (disk == gh) if (disk and gh) else None})
        if disk and disk != expected:
            critical.append(f"FROZEN_DRIFT:{rel}")
        if disk and gh and disk != gh:
            critical.append(f"GIT_HEAD_DRIFT:{rel}")
    return {
        "audit_id": "PREREG_AND_H10_FRESH_REFERENCE_CONSISTENCY",
        "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "prereg_dir": str(prereg_dir.relative_to(ROOT)) if prereg_dir.is_relative_to(ROOT) else str(prereg_dir),
        "h10_fresh_dir": str(h10_dir.relative_to(ROOT)) if h10_dir.is_relative_to(ROOT) else str(h10_dir),
        "prereg_files_scanned": len(prereg_rows),
        "h10_json_files_scanned": len(h10_rows),
        "files_scanned": len(rows),
        "critical": sorted(set(critical)),
        "errors": errors,
        "info": infos,
        "pass": len(set(critical)) == 0 and len(errors) == 0,
        "frozen_hashes_checked": FROZEN,
        "frozen_checks": frozen_checks,
        "rows": rows,
        "scope_note": (
            "Read-only scan of preregistration markdown and forward_block_h10_fresh JSONs "
            "for stale path refs, missing referenced files, and frozen/git-HEAD hash drift. "
            "Preregistration documents are frozen records and are never modified; findings "
            "are reported only. CRITICAL/ERROR indicate stale pointers or hash drift requiring "
            "investigation. Default output: research_state/."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=None)
    ap.add_argument("--prereg-dir", default=None)
    ap.add_argument("--h10-dir", default=None)
    args = ap.parse_args()
    res = run_audit(
        Path(args.prereg_dir) if args.prereg_dir else None,
        Path(args.h10_dir) if args.h10_dir else None,
    )
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    if args.out:
        out_path = Path(args.out)
        if not out_path.is_absolute():
            out_path = ROOT / out_path
    else:
        out_path = STATE_DIR / f"PREREG_AND_H10_FRESH_REFERENCE_CONSISTENCY_{stamp}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(res, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[prereg-h10-ref] pass={res['pass']} scanned={res['files_scanned']} "
          f"prereg={res['prereg_files_scanned']} h10={res['h10_json_files_scanned']} "
          f"critical={len(res['critical'])} errors={len(res['errors'])} info={len(res['info'])}")
    print(f"[prereg-h10-ref] wrote {out_path.relative_to(ROOT)}")
    return 0 if res["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
