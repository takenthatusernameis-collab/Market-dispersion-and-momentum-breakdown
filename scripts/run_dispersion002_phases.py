#!/usr/bin/env python3
"""
Follow-up experiment HARMONY-CRYPTO-EDGE-004-DISPERSION-002
Built on prior DISPERSION-001; follows same free-data, point-in-time controls.
"""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-002"
OUT_DIR = ROOT / "artifacts" / EXP
CONFIG_PATH = ROOT / "configs" / "dispersion_momentum_followup_v1.json"

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "data" / "panels").mkdir(parents=True, exist_ok=True)

    cfg = json.loads(CONFIG_PATH.read_text())

    # Write initial setup
    setup = {
        "experiment_id": EXP,
        "status": "initialized",
        "based_on": "HARMONY-CRYPTO-EDGE-004-DISPERSION-001",
        "config": str(CONFIG_PATH),
        "objective": "Follow-up robustness test of dispersion-conditioned momentum spread",
        "created_utc": "2026-10-23T10:30:00Z",
        "controls": {
            "free_data_only": True,
            "point_in_time_universe": True,
            "no_lookahead": True,
            "chronological_oos": True
        }
    }
    (OUT_DIR / "experiment_setup.json").write_text(json.dumps(setup, indent=2))
    print(f"Initialized {EXP}")
    print(json.dumps(setup, indent=2))

if __name__ == "__main__":
    main()
