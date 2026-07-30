"""Check DRC2 release-candidate data for obvious identifier leakage."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "data/clean/drc2_facility_master_release_candidate.csv"

FORBIDDEN_COLUMNS = {
    "A1_email",
    "A2_name",
    "A3_phone",
    "A8_FOSA",
    "_id",
    "_uuid",
    "meta/rootUuid",
    "_index",
    "respondent_phones",
    "respondent_names",
    "raw_row_ids",
    "submission_times",
    "conflict_fields",
}

SENSITIVE_PATTERNS = {
    "email": re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"),
    "drc_phone": re.compile(r"(\+?243|0)[\s.-]?\d{2,3}[\s.-]?\d{3}[\s.-]?\d{3,4}"),
}


def main() -> int:
    if not RELEASE.exists():
        print(f"Missing release candidate: {RELEASE}")
        return 1

    df = pd.read_csv(RELEASE, low_memory=False)
    failures: list[str] = []

    forbidden_present = sorted(FORBIDDEN_COLUMNS.intersection(df.columns))
    if forbidden_present:
        failures.append("Forbidden columns present: " + ", ".join(forbidden_present))

    object_cols = df.select_dtypes(include=["object"]).columns
    for col in object_cols:
        sample = "\n".join(df[col].dropna().astype(str).head(1000).tolist())
        for name, pattern in SENSITIVE_PATTERNS.items():
            if pattern.search(sample):
                failures.append(f"Column `{col}` matched sensitive pattern `{name}`")

    if failures:
        print("Release-candidate check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(f"Release-candidate check passed: {len(df):,} rows x {len(df.columns):,} columns.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
