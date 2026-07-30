"""Basic repository hygiene checks for the private DRC3a workspace."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN_TRACKED_PATTERNS = [
    "data/raw/",
    "data/private/",
    "outputs/drc2_facility_master/raw_submissions.csv",
    "outputs/drc2_facility_master/facility_master.csv",
    "outputs/drc2_facility_master/respondent_sample.csv",
    "outputs/drc2_facility_master/facility_master_conflicts.csv",
    "outputs/drc2_dedup_audit/raw_fosa_duplicate_clusters.csv",
    "outputs/drc2_dedup_audit/phone_fosa_repeat_clusters.csv",
    "outputs/drc2_dedup_audit/notebook_remaining_fosa_clusters.csv",
]


def tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return result.stdout.splitlines()


def main() -> int:
    tracked = tracked_files()
    failures = []
    for pattern in FORBIDDEN_TRACKED_PATTERNS:
        matches = [path for path in tracked if path == pattern or path.startswith(pattern)]
        failures.extend(matches)

    if failures:
        print("Forbidden private files are tracked:")
        for path in failures:
            print(f"- {path}")
        return 1

    print("Repository hygiene check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
