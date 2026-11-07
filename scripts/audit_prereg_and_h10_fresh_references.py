#!/usr/bin/env python3
"""Read-only consistency audit over preregistration docs and forward-block artifacts.

Scans:
- DISP-003 preregistration markdown (default: artifacts/.../DISPERSION-003/preregistrations/*.md)
  for repo-relative artifact/research_state path references and 64-char SHA256 refs;
  verifies referenced paths exist on disk and frozen hashes match where applicable.
- DISP-003 forward_block_h10_fresh/*.json and (by default) forward_block/*.json
  for path/hash reference fields and frozen/git-HEAD consistency.
- Optionally, frozen pre-DISP-003 preregistration dirs (e.g. DISPERSION-002) can be
  scanned via --frozen-prereg-dirs. Missing path references in frozen pre-DISP-003
  prereg docs are reported as INFO (frozen_record_stale_pointer), NOT ERROR, because
  frozen/closed preregistration records must not be modified to "fix" historical
  prose; the finding is still surfaced for durable-state awareness.

Writes a timestamped report under research_state/ by default. DOES NOT modify
any existing artifact, config, preregistration, or result.

Usage:
    python3 scripts/audit_prereg_and_h10_fresh_references.py [--out PATH]
           [--include-disp002-preregs]
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
FORWARD_BLOCK_DIR = ROOT / "artifacts" / EXP / "forward_block"
DISP002_PREREG_DIR = ROOT / "artifacts" / "HARMONY-CRYPTO-EDGE-004-DISPERSION-002" / "preregistrations"
STATE_DIR = ROOT / "research_state"

FROZEN = {
    "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json":
        "7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390",
    "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/forward_block_evaluation.json":
        "324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f",
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


def audit_prereg_md(p: Path, *, frozen_record: bool = False) -> dict:
    """Audit a preregistration markdown file.

    When frozen_record=True (for immutable closed preregistrations such as
    DISPERSION-002), missing path references are reported as INFO findings
    tagged ``frozen_record_stale_pointer`` rather than ERROR. The pointer is
    still surfaced, but the audit does not fail the pass invariant because the
    record must not be modified.
    """
    text = p.read_text(encoding="utf-8")
    row = {
        "file": p.name,
        "kind": "preregistration_md",
        "frozen_record": frozen_record,
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
            if frozen_record:
                row["findings"].append(f"frozen_record_stale_pointer (INFO, not modified): {raw}")
            else:
                row["findings"].append(f"missing referenced path: {raw}")
        if frozen_expected and disk and disk != frozen_expected:
            row["findings"].append(
                f"FROZEN HASH MISMATCH: {raw} disk={disk} expected={frozen_expected}")
    for h in sorted(set(HASH_RE.findall(text))):
        frozen_path = next((k for k, v in FROZEN.items() if v == h), None)
        row["hash_refs"].append({"sha256": h, "matches_known_frozen": frozen_path})
    if any("FROZEN HASH MISMATCH" in f for f in row["findings"]):
        row["severity"] = "CRITICAL"
    elif any(f.startswith("missing referenced path:") for f in row["findings"]):
        row["severity"] = "ERROR"
    elif row["findings"]:
        row["severity"] = "INFO"
    return row


def audit_forward_block_json(p: Path, kind: str = "forward_block_json") -> dict:
    row = {
        "file": p.name,
        "kind": kind,
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
    try:
        rel_self = str(p.resolve().relative_to(ROOT)).replace("\\", "/")
    except Exception:  # noqa: BLE001
        rel_self = None
    if rel_self and rel_self in FROZEN:
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


# Backward-compatible alias used by existing tests/callers.
def audit_h10_json(p: Path) -> dict:
    return audit_forward_block_json(p, kind="h10_fresh_json")


def run_audit(
    prereg_dir: Path | None = None,
    h10_dir: Path | None = None,
    forward_block_dir: Path | None = None,
    frozen_prereg_dirs: list[Path] | None = None,
    include_h10_variants: bool = True,
) -> dict:
    prereg_dir = prereg_dir or PREREG_DIR
    h10_dir = h10_dir or H10_DIR
    forward_block_dir = forward_block_dir or FORWARD_BLOCK_DIR
    frozen_prereg_dirs = frozen_prereg_dirs or []

    prereg_rows = [audit_prereg_md(p) for p in sorted(prereg_dir.glob("*.md")) if p.is_file()] if prereg_dir.exists() else []
    frozen_prereg_rows: list[dict] = []
    for fd in frozen_prereg_dirs:
        if fd.exists():
            frozen_prereg_rows.extend(audit_prereg_md(p, frozen_record=True) for p in sorted(fd.glob("*.md")) if p.is_file())

    h10_rows = [audit_forward_block_json(p, kind="h10_fresh_json") for p in sorted(h10_dir.glob("*.json")) if p.is_file()] if h10_dir.exists() else []
    fb_rows = [audit_forward_block_json(p, kind="forward_block_json") for p in sorted(forward_block_dir.glob("*.json")) if p.is_file() and p.name != "forward_block_evaluation.json"] if forward_block_dir and forward_block_dir.exists() else []
    # Always include canonical forward_block_evaluation.json if present (self/frozen check).
    canon = (forward_block_dir or FORWARD_BLOCK_DIR) / "forward_block_evaluation.json"
    canon_rows = [audit_forward_block_json(canon, kind="forward_block_canonical_json")] if canon.is_file() else []

    # Non-frozen H10 variant dirs (e.g. forward_block_h10/, forward_block_h10_fresh_check/)
    # are scanned read-only as h10_variant_json. These are unreferenced throwaway outputs,
    # not frozen canonical targets (FROZEN pins only forward_block/ and forward_block_h10_fresh/);
    # findings are reported but they do not carry frozen self-hash expectations.
    variant_rows: list[dict] = []
    if include_h10_variants:
        exp_dir = h10_dir.parent if h10_dir else (ROOT / "artifacts" / EXP)
        h10_fresh_name = (h10_dir or H10_DIR).name
        for vd in sorted(exp_dir.glob("forward_block_h10*")) if exp_dir.exists() else []:
            if not vd.is_dir() or vd.name == h10_fresh_name:
                continue
            for p in sorted(vd.glob("*.json")):
                if p.is_file():
                    r = audit_forward_block_json(p, kind="h10_variant_json")
                    r["variant_dir"] = vd.name
                    variant_rows.append(r)

    rows = prereg_rows + frozen_prereg_rows + canon_rows + h10_rows + fb_rows + variant_rows
    critical = [f"{r['file']}:{f}" for r in rows for f in r["findings"] if r["severity"] == "CRITICAL"]
    errors = [f"{r['file']}:{f}" for r in rows for f in r["findings"] if r["severity"] == "ERROR"]
    infos = [f"{r['file']}:{f}" for r in rows for f in r["findings"] if r["severity"] == "INFO"]
    frozen_checks = []
    for rel, expected in FROZEN.items():
        fp = ROOT / rel
        disk = sha256_file(fp) if fp.is_file() else None
        gh = git_head_sha256(rel)
        git_head_drift = bool(disk and gh and disk != gh and gh == expected)
        frozen_checks.append({"path": rel, "expected": expected, "disk_sha256": disk,
                              "git_head_sha256": gh,
                              "matches_frozen": disk == expected if disk else False,
                              "matches_git_head": (disk == gh) if (disk and gh) else None,
                              "git_head_drift": git_head_drift})
        if disk and disk != expected:
            critical.append(f"FROZEN_DRIFT:{rel}")
        if git_head_drift:
            critical.append(f"GIT_HEAD_DRIFT:{rel}")
    return {
        "audit_id": "PREREG_AND_H10_FRESH_REFERENCE_CONSISTENCY",
        "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "prereg_dir": str(prereg_dir.relative_to(ROOT)) if prereg_dir.is_relative_to(ROOT) else str(prereg_dir),
        "h10_fresh_dir": str(h10_dir.relative_to(ROOT)) if h10_dir.is_relative_to(ROOT) else str(h10_dir),
        "forward_block_dir": str((forward_block_dir or FORWARD_BLOCK_DIR).relative_to(ROOT)) if (forward_block_dir or FORWARD_BLOCK_DIR).is_relative_to(ROOT) else str(forward_block_dir),
        "frozen_prereg_dirs": [str(d.relative_to(ROOT)) if d.is_relative_to(ROOT) else str(d) for d in frozen_prereg_dirs],
        "prereg_files_scanned": len(prereg_rows),
        "frozen_prereg_files_scanned": len(frozen_prereg_rows),
        "h10_json_files_scanned": len(h10_rows),
        "h10_variant_json_files_scanned": len(variant_rows),
        "forward_block_json_files_scanned": len(canon_rows) + len(fb_rows),
        "files_scanned": len(rows),
        "critical": sorted(set(critical)),
        "errors": errors,
        "info": infos,
        "pass": len(set(critical)) == 0 and len(errors) == 0,
        "frozen_hashes_checked": FROZEN,
        "frozen_checks": frozen_checks,
        "rows": rows,
        "scope_note": (
            "Read-only scan of preregistration markdown and forward-block JSONs "
            "(canonical forward_block/, forward_block_h10_fresh/, and non-frozen "
            "forward_block_h10* variant dirs) for stale path refs, missing referenced "
            "files, and frozen/git-HEAD hash drift. Frozen pre-DISP-003 preregistration "
            "docs (when scanned via --include-disp002-preregs) report missing refs as INFO "
            "(frozen_record_stale_pointer) because immutable records are never modified. "
            "Preregistration documents are frozen records and are never modified; findings "
            "are reported only. CRITICAL/ERROR indicate stale pointers or hash drift "
            "requiring investigation. Default output: research_state/."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=None)
    ap.add_argument("--prereg-dir", default=None)
    ap.add_argument("--h10-dir", default=None)
    ap.add_argument("--forward-block-dir", default=None)
    ap.add_argument("--include-disp002-preregs", action="store_true",
                    help="Scan DISPERSION-002 preregistration docs as frozen records (stale pointers reported as INFO).")
    args = ap.parse_args()
    frozen = [DISP002_PREREG_DIR] if args.include_disp002_preregs else []
    res = run_audit(
        Path(args.prereg_dir) if args.prereg_dir else None,
        Path(args.h10_dir) if args.h10_dir else None,
        Path(args.forward_block_dir) if args.forward_block_dir else None,
        frozen,
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
          f"prereg={res['prereg_files_scanned']} frozen_prereg={res['frozen_prereg_files_scanned']} "
          f"h10={res['h10_json_files_scanned']} forward_block={res['forward_block_json_files_scanned']} "
          f"critical={len(res['critical'])} errors={len(res['errors'])} info={len(res['info'])}")
    print(f"[prereg-h10-ref] wrote {out_path.relative_to(ROOT)}")
    return 0 if res["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
