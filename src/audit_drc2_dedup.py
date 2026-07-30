#!/usr/bin/env python3
"""Audit deduplication behavior in the DRC2 speed-run notebook."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


CORE_VARS = [
    "A5_province",
    "A6_zone",
    "A7_type",
    "A8_FOSA",
    "B1_grid",
    "C1_gen",
    "D1_solar",
    "H2_10Lo2",
    "H3_5Lo2",
    "H1_medequip",
]


def find_default_csv() -> Path:
    downloads = Path.home() / "Downloads"
    matches = [
        p
        for p in downloads.iterdir()
        if p.suffix.lower() == ".csv"
        and ("drc2 survey" in p.name.lower() or "enque" in p.name.lower())
    ]
    if not matches:
        raise FileNotFoundError("Could not find the DRC2 survey CSV in Downloads.")
    return max(matches, key=lambda p: p.stat().st_mtime)


def add_notebook_dedup_fields(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["A8_FOSA_num"] = pd.to_numeric(out["A8_FOSA"], errors="coerce")
    out["phone_clean"] = (
        out["A3_phone"]
        .astype(str)
        .str.replace(r"\.0$", "", regex=True)
        .str.replace(r"\D", "", regex=True)
        .str.strip()
    )
    out.loc[out["phone_clean"].str.len() < 6, "phone_clean"] = np.nan
    out["completeness_score"] = out[CORE_VARS].notna().sum(axis=1)
    return out


def notebook_analytic_sample(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.sort_values(by=["completeness_score"], ascending=False)
        .drop_duplicates(subset=["phone_clean", "A8_FOSA_num"], keep="first")
        .reset_index(drop=True)
    )


def cluster_text(values: pd.Series, limit: int = 8) -> str:
    vals = [str(v) for v in values.dropna().unique()[:limit]]
    return " | ".join(vals)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, default=None)
    parser.add_argument("--out-dir", type=Path, default=Path("outputs/drc2_dedup_audit"))
    args = parser.parse_args()

    source = args.csv or find_default_csv()
    raw = pd.read_csv(source, low_memory=False)
    audited = add_notebook_dedup_fields(raw)
    sample = notebook_analytic_sample(audited)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    Path("docs").mkdir(exist_ok=True)

    raw_fosa_clusters = (
        audited.groupby("A8_FOSA_num", dropna=False)
        .agg(
            raw_rows=("A8_FOSA_num", "size"),
            raw_phones=("phone_clean", pd.Series.nunique),
            roles=("A4_role", cluster_text),
            names=("A2_name", cluster_text),
            phones=("phone_clean", cluster_text),
            submission_times=("_submission_time", cluster_text),
        )
        .reset_index()
        .sort_values(["raw_rows", "A8_FOSA_num"], ascending=[False, True])
    )

    sample_fosa_clusters = (
        sample.groupby("A8_FOSA_num", dropna=False)
        .agg(
            sample_rows=("A8_FOSA_num", "size"),
            sample_phones=("phone_clean", pd.Series.nunique),
            roles=("A4_role", cluster_text),
            names=("A2_name", cluster_text),
            phones=("phone_clean", cluster_text),
            completeness_scores=("completeness_score", cluster_text),
            submission_times=("_submission_time", cluster_text),
        )
        .reset_index()
        .sort_values(["sample_rows", "A8_FOSA_num"], ascending=[False, True])
    )

    phone_fosa_clusters = (
        audited.groupby(["A8_FOSA_num", "phone_clean"], dropna=False)
        .agg(
            rows=("A8_FOSA_num", "size"),
            names=("A2_name", cluster_text),
            roles=("A4_role", cluster_text),
            completeness_scores=("completeness_score", cluster_text),
            submission_times=("_submission_time", cluster_text),
        )
        .reset_index()
        .sort_values(["rows", "A8_FOSA_num"], ascending=[False, True])
    )

    raw_fosa_clusters.to_csv(args.out_dir / "raw_fosa_duplicate_clusters.csv", index=False)
    sample_fosa_clusters.to_csv(
        args.out_dir / "notebook_remaining_fosa_clusters.csv", index=False
    )
    phone_fosa_clusters.to_csv(args.out_dir / "phone_fosa_repeat_clusters.csv", index=False)

    summary = {
        "source": str(source),
        "raw_rows": int(len(raw)),
        "raw_unique_fosa": int(audited["A8_FOSA_num"].nunique(dropna=True)),
        "raw_duplicate_fosa_clusters": int(
            (audited.groupby("A8_FOSA_num").size() > 1).sum()
        ),
        "notebook_sample_rows": int(len(sample)),
        "notebook_unique_fosa": int(sample["A8_FOSA_num"].nunique(dropna=True)),
        "rows_removed_by_notebook_phone_fosa_rule": int(len(raw) - len(sample)),
        "remaining_rows_beyond_one_per_fosa": int(
            len(sample) - sample["A8_FOSA_num"].nunique(dropna=True)
        ),
        "remaining_duplicate_fosa_clusters": int(
            (sample.groupby("A8_FOSA_num").size() > 1).sum()
        ),
        "raw_rows_missing_phone_clean": int(audited["phone_clean"].isna().sum()),
        "sample_rows_missing_phone_clean": int(sample["phone_clean"].isna().sum()),
    }
    (args.out_dir / "dedup_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    report = Path("docs/drc2-dedup-audit.md")
    report.write_text(
        "\n".join(
            [
                "# DRC2 Deduplication Audit",
                "",
                f"Source file: `{source}`",
                "",
                "## Notebook Rule",
                "",
                "The speed-run notebook does not deduplicate to one row per facility. It:",
                "",
                "1. Cleans `A3_phone` into `phone_clean` by removing punctuation/non-digits and setting values shorter than 6 digits to missing.",
                "2. Builds `completeness_score` as the count of non-missing values across ten core variables: `A5_province`, `A6_zone`, `A7_type`, `A8_FOSA`, `B1_grid`, `C1_gen`, `D1_solar`, `H2_10Lo2`, `H3_5Lo2`, and `H1_medequip`.",
                "3. Sorts rows by `completeness_score` descending.",
                "4. Drops duplicates on `phone_clean` + `A8_FOSA`, keeping the first row.",
                "",
                "In plain language: it removes repeat submissions from the same phone number at the same facility, preferring the row with more complete core fields. It preserves multiple respondents at the same facility when they have different phone numbers.",
                "",
                "## Quantified Effect",
                "",
                f"- Raw rows: {summary['raw_rows']}",
                f"- Raw unique FOSA IDs: {summary['raw_unique_fosa']}",
                f"- Raw FOSA IDs with multiple rows: {summary['raw_duplicate_fosa_clusters']}",
                f"- Notebook analytic rows: {summary['notebook_sample_rows']}",
                f"- Notebook unique FOSA IDs: {summary['notebook_unique_fosa']}",
                f"- Rows removed by notebook rule: {summary['rows_removed_by_notebook_phone_fosa_rule']}",
                f"- Rows remaining beyond one per FOSA: {summary['remaining_rows_beyond_one_per_fosa']}",
                f"- FOSA IDs still duplicated after notebook rule: {summary['remaining_duplicate_fosa_clusters']}",
                "",
                "## Audit Judgment",
                "",
                "The notebook rule is a useful first filter for exact or near-exact repeat submissions by the same respondent, but it is not sufficient for facility-level high-N analysis. DRC3a should not treat the notebook `analytic_sample` as a true facility master without a second reconciliation step.",
                "",
                "Main risks:",
                "",
                "- It preserves multiple actors at the same facility, which is useful for respondent-level disagreement but can double-count facilities in facility-level prevalence estimates.",
                "- It does not use `_submission_time` as a tie-breaker, so equally complete repeated rows may not consistently keep the latest submission.",
                "- It does not prioritize respondent role, even though some variables may be more reliable from technicians, administrators, or clinicians.",
                "- It uses the same row-selection rule for all variables, but asset counts, outage perceptions, costs, and free-text comments may require different reconciliation rules.",
                "- It does not create a transparent conflict flag for facilities where respondents disagree.",
                "",
                "## Recommended Next Rule",
                "",
                "Create three related tables:",
                "",
                "- `raw_submissions`: all 565 raw rows.",
                "- `respondent_sample`: notebook-style phone + FOSA deduplication, used for respondent-level perception and disagreement analysis.",
                "- `facility_master`: one row per `A8_FOSA`, with variable-family-specific reconciliation rules and conflict flags.",
                "",
                "Recommended facility-master reconciliation:",
                "",
                "- Facility identity: use facility key / stable FOSA metadata.",
                "- Binary infrastructure presence: use `max` across respondents, with a disagreement flag.",
                "- Counts/capacities: use the most complete/latest respondent where plausible; also retain max and median audit fields.",
                "- Costs/outage recall: use median across respondents or role-prioritized value; flag high disagreement.",
                "- Free text: concatenate with respondent role and submission ID.",
                "- Human infrastructure/perception variables: preserve respondent-level table and summarize disagreement rather than forcing a single truth too early.",
                "",
                "## Audit Files",
                "",
                "- `outputs/drc2_dedup_audit/raw_fosa_duplicate_clusters.csv`",
                "- `outputs/drc2_dedup_audit/notebook_remaining_fosa_clusters.csv`",
                "- `outputs/drc2_dedup_audit/phone_fosa_repeat_clusters.csv`",
                "- `outputs/drc2_dedup_audit/dedup_summary.json`",
                "",
            ]
        ),
        encoding="utf-8",
    )

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
