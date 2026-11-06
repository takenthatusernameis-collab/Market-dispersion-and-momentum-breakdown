#!/usr/bin/env python3
"""Append a session-record entry to research_state/run_manifest.json.

The manifest is a narrative JSON file whose top-level entries are indented
with two spaces and whose last top-level value is the ``session_history``
array. A plain json.load -> json.dump round trip would re-indent the whole
file and churn a frozen narrative for one new entry, so this script appends
by string manipulation that preserves the existing formatting byte-for-byte.

History note: the previous version of this script assumed the manifest's
final top-level value closed with ``}`` and emitted a trailing comma before
the top-level ``}`` (illegal JSON). Against the real manifest -- whose last
value is the ``session_history`` array closing with ``]`` -- it produced
unparseable output. It had also never been executed against the committed
manifest; it was only added to the .py inventory. This version locates the
final top-level closing brace, inserts the new entry with a single leading
comma separator immediately after the previous value's close token, and
emits no trailing comma.

Usage:
    python3 scripts/append_manifest_entry.py <key> '<json object string>'
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "research_state" / "run_manifest.json"


def _detect_indent(raw: str) -> str:
    """Return the indentation of the first top-level key (e.g. '  ')."""
    m = re.search(r"\n([ \t]*)\"", raw)
    return m.group(1) if m else "  "


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: append_manifest_entry.py <key> '<json object>'")
        return 2
    key, obj_str = sys.argv[1], sys.argv[2]
    try:
        obj = json.loads(obj_str)
    except json.JSONDecodeError as e:
        print(f"object is not valid JSON: {e}")
        return 1
    # verify the serialised object round-trips
    if json.loads(json.dumps(obj)) != obj:
        print("object does not round-trip through json")
        return 1

    raw = MANIFEST.read_text(encoding="utf-8")
    d = json.loads(raw)
    if key in d:
        print(f"key {key!r} already present; refusing to duplicate")
        return 1

    indent = _detect_indent(raw)
    indent_n = len(indent) or 2
    # Build the entry at the file's top-level indent. json.dumps with
    # indent=indent_n nests object keys one level deeper, matching the
    # file's existing 2-space-per-level style.
    inner_obj = json.dumps(obj, indent=indent_n, ensure_ascii=True)
    entry = f'{indent}"{key}": {inner_obj}'

    # Locate the final top-level closing brace, walking back over trailing
    # whitespace/newlines. The character before that whitespace is the close
    # of the last top-level value (']' for an array, '}' for an object, '"'
    # for a string, a digit for a scalar). A comma separator is always
    # required between top-level entries; insert it immediately before the
    # top-level '}', which closes the whole document. No trailing comma is
    # emitted, which would be illegal JSON.
    i = len(raw) - 1
    while i >= 0 and raw[i] in " \t\r\n":
        i -= 1
    if i < 0 or raw[i] != "}":
        print("manifest does not end with a top-level closing brace; refusing")
        return 1

    insertion = ",\n" + entry
    new_raw = raw[:i] + insertion + raw[i:]
    # sanity: must still parse and have exactly one more top-level key
    try:
        d2 = json.loads(new_raw)
    except json.JSONDecodeError as e:
        print(f"appended text is not valid JSON: {e}")
        return 1
    if set(d2.keys()) != set(d.keys()) | {key}:
        print("key set changed unexpectedly")
        return 1
    if d2[key] != obj:
        print("appended value does not match the supplied object")
        return 1
    MANIFEST.write_text(new_raw, encoding="utf-8")
    try:
        shown = MANIFEST.relative_to(ROOT)
    except ValueError:
        shown = MANIFEST
    print(f"appended {key!r} to {shown}")
    return 0


if __name__ == "__main__":
    sys.exit(main())