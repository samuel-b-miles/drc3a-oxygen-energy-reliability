"""Run the current DRC3a analysis scripts in dependency order.

This is intentionally a thin orchestrator. Individual scripts remain in `src/`
so each analysis can still be run and debugged independently.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

TASKS = [
    "src/build_drc2_facility_master.py",
    "src/explore_drc2_variables.py",
    "src/audit_drc2_dedup.py",
    "src/calculate_drc2_uptime.py",
    "src/analyze_drc2_high_n_mockup.py",
    "src/model_energy_predictors_of_oxygen.py",
    "src/analyze_equipment_failure_frequency.py",
    "src/analyze_equipment_failure_layers.py",
    "src/analyze_equipment_damage_associations.py",
    "src/audit_solar_generator_capacity.py",
    "src/analyze_cost_data_quality.py",
    "src/build_drc3a_econometric_panel.py",
    "src/build_drc3a_v4_figures.py",
]


def main() -> int:
    for task in TASKS:
        print(f"\n==> {task}", flush=True)
        result = subprocess.run([sys.executable, task], cwd=ROOT)
        if result.returncode != 0:
            print(f"\nStopped at {task} with exit code {result.returncode}", file=sys.stderr)
            return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
