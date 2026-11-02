"""Every declared runtime dependency in requirements.txt must be importable.

The bare ubuntu-24.04 runner image ships without numpy/pandas even though
scripts/ and most tests import them (see requirements.txt). Without this
guard the suite degrades into scattered ModuleNotFoundError tracebacks
instead of one clear, actionable failure, which has previously caused a
session to record a false "161 OK" claim. Run:

    python3 -m pip install -r requirements.txt

before `python3 -m unittest discover -s tests`.
"""

import importlib
import os
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _declared_requirements():
    """Parse requirements.txt into a list of bare distribution names."""
    path = os.path.join(REPO_ROOT, "requirements.txt")
    names = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            names.append(line.split()[0])
    return names


class RequirementsImportableTests(unittest.TestCase):
    def test_every_declared_requirement_imports(self):
        missing = []
        for name in _declared_requirements():
            try:
                importlib.import_module(name)
            except ImportError as exc:  # pragma: no cover - environment dependent
                missing.append(f"{name} ({exc})")
        if missing:
            self.fail(
                "Declared requirements are not installed in this interpreter: "
                + "; ".join(missing)
                + ". Install with: python3 -m pip install -r requirements.txt"
            )


if __name__ == "__main__":
    unittest.main()