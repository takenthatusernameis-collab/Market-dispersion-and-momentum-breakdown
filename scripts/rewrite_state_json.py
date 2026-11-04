#!/usr/bin/env python3
"""Re-serialise a research-state JSON file with its exact original formatting.

The durable state files (research_state/universe_frontier.json and
research_state/run_manifest.json) are hand-edited across sessions and carry
non-ASCII candidate identifiers (e.g. the CoinMetrics catalog entries
"\\u6211\\u8e0f\\u9a6c\\u6765\\u4e86"). A naive json.load -> json.dump round
trip is NOT byte-identical: the committed files use ensure_ascii=True, so
re-dumping with the default ensure_ascii=False would un-escape those entries
and rewrite 200 KB of the file for a one-line probe-record update. This script
detects the original formatting parameters and re-serialises with them, so an
edit stays a minimal diff.

Usage:
    python3 scripts/rewrite_state_json.py research_state/universe_frontier.json
"""
import json
import sys
from pathlib import Path


def detect_format(raw: bytes):
    """Return (indent, ensure_ascii, trailing_newline) that reproduces raw."""
    d = json.loads(raw)
    trailing = raw.endswith(b"\n")
    for indent in (None, 1, 2, 4):
        for ensure_ascii in (True, False):
            trial = json.dumps(d, indent=indent, ensure_ascii=ensure_ascii)
            if indent is not None:
                trial += "\n"
            if trial.encode() == raw:
                return indent, ensure_ascii, trailing
    raise SystemExit(
        "could not reproduce original formatting; refusing to rewrite "
        "because a byte-level diff is the only safe edit here"
    )


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    path = Path(sys.argv[1])
    raw = path.read_bytes()
    indent, ensure_ascii, trailing = detect_format(raw)
    d = json.loads(raw)
    out = json.dumps(d, indent=indent, ensure_ascii=ensure_ascii)
    if indent is not None:
        out += "\n"
    if not trailing:
        out = out.rstrip("\n")
    path.write_text(out, encoding="utf-8")
    print(f"{path}: re-serialised indent={indent} ensure_ascii={ensure_ascii} "
          f"trailing_newline={trailing}; bytes {len(raw)} -> {len(out.encode())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())