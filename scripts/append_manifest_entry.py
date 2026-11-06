#!/usr/bin/env python3
"""Append a session-record entry to research_state/run_manifest.json.

The manifest is a narrative JSON file whose session-record entries are indented
with ONE space (not two), so a plain json.load -> json.dump round trip would
re-indent the whole file and churn a frozen narrative for one new entry. This
script appends an entry by string manipulation, preserving the existing
formatting byte-for-byte.

Usage:
    python3 scripts/append_manifest_entry.py <key> '<json object string>'
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "research_state" / "run_manifest.json"


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: append_manifest_entry.py <key> '<json object>'")
        return 2
    key, obj_str = sys.argv[1], sys.argv[2]
    obj = json.loads(obj_str)
    raw = MANIFEST.read_text(encoding="utf-8")
    # verify the file still parses and the key is not already present
    d = json.loads(raw)
    if key in d:
        print(f"key {key!r} already present; refusing to duplicate")
        return 1
    # verify the serialised object round-trips
    if json.loads(json.dumps(obj)) != obj:
        print("object does not round-trip through json")
        return 1
    # the manifest's own entries are indented with one space; match that style
    block = json.dumps({key: obj}, indent=1, ensure_ascii=True)
    # strip the outer braces and re-wrap to match the file's existing shape:
    # entries appear as  <key>: <object>,\n  at one-space indent between the
    # outer { and }.
    inner = block[1:-1].rstrip()
    # inner now looks like  "key": {\n "k": "v",\n ...}
    # we want  "key": {\n "k": "v",\n ...},\n
    insertion = " " + inner + ",\n"
    # insert before the closing brace of the top-level object
    marker = "}\n"
    if not raw.endswith(marker):
        print("manifest does not end with a top-level closing brace; refusing")
        return 1
    new_raw = raw[: -len(marker)] + insertion + marker
    # sanity: must still parse and have one more top-level key
    d2 = json.loads(new_raw)
    if set(d2.keys()) != set(d.keys()) | {key}:
        print("key set changed unexpectedly")
        return 1
    MANIFEST.write_text(new_raw, encoding="utf-8")
    print(f"appended {key!r} to {MANIFEST.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())