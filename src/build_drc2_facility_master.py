#!/usr/bin/env python3
"""Build raw, respondent-level, and facility-level DRC2 survey tables.

The raw survey contains multiple submissions for some facilities. This script
keeps three levels of evidence:

1. raw_submissions: every submitted row with standard helper fields.
2. respondent_sample: speed-run notebook deduplication, one row per
   phone_clean + A8_FOSA, preserving multiple facility actors.
3. facility_master: one row per A8_FOSA with variable-family-specific
   reconciliation and conflict flags.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Iterable

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

GRID_DECODER = {
    1: "SNEL",
    2: "SOCODE",
    3: "VIRUNGA",
    4: "NURU",
    5: "ENK",
    6: "Equatorial Power",
    7: "Community Hydro",
    8: "Community Solar",
    9: "No Grid",
    99: "Other Grid",
}

OXYGEN_PAYMENT_DECODER = {
    1: "Included in treatment",
    2: "Paid separately",
    3: "Free",
}


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


def numeric(df: pd.DataFrame, column: str) -> pd.Series:
    if column not in df:
        return pd.Series(np.nan, index=df.index)
    return pd.to_numeric(df[column], errors="coerce")


def clean_phone(series: pd.Series) -> pd.Series:
    out = (
        series.astype(str)
        .str.replace(r"\.0$", "", regex=True)
        .str.replace(r"\D", "", regex=True)
        .str.strip()
    )
    out.loc[out.str.len() < 6] = np.nan
    return out


def grid_architecture(code: float) -> str | float:
    if pd.isna(code):
        return np.nan
    code = int(code)
    if code == 1:
        return "Central Grid"
    if code in [2, 3, 4, 5, 6]:
        return "Private / Concession Grid"
    if code in [7, 8]:
        return "Community Mini-grid"
    if code == 9:
        return "No Grid"
    return "Other"


def add_standard_fields(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["raw_row_id"] = np.arange(1, len(out) + 1)
    out["A8_FOSA_num"] = numeric(out, "A8_FOSA")
    out["phone_clean"] = clean_phone(out["A3_phone"])
    out["submission_time_parsed"] = pd.to_datetime(
        out.get("_submission_time"), errors="coerce"
    )
    out["completeness_score"] = out[CORE_VARS].notna().sum(axis=1)

    out["grid_type_code"] = numeric(out, "B1_grid")
    out["grid_type_label"] = out["grid_type_code"].map(GRID_DECODER)
    out["grid_architecture"] = out["grid_type_code"].map(grid_architecture)
    out["has_grid"] = (
        out["grid_type_code"].notna() & (out["grid_type_code"] != 9)
    ).astype(int)
    out["has_generator"] = (numeric(out, "C1_gen") == 1).astype(int)
    out["has_solar"] = (numeric(out, "D1_solar") == 1).astype(int)
    out["has_charcoal"] = (numeric(out, "E1_charc") == 1).astype(int)
    out["n_energy_sources"] = out[
        ["has_grid", "has_generator", "has_solar"]
    ].sum(axis=1)
    out["energy_profile"] = out.apply(classify_energy_profile, axis=1)

    out["conc_10l"] = numeric(out, "H2_10Lo2").fillna(0)
    out["conc_5l"] = numeric(out, "H3_5Lo2").fillna(0)
    out["total_concentrators"] = out["conc_10l"] + out["conc_5l"]
    out["has_concentrator"] = (out["total_concentrators"] > 0).astype(int)
    out["has_cylinders"] = (numeric(out, "H4_oxygen/1") == 1).astype(int)
    out["has_psa_internal"] = (numeric(out, "H4_oxygen/2") == 1).astype(int)
    out["has_psa_external"] = (numeric(out, "H4_oxygen/3") == 1).astype(int)
    out["has_other_oxygen"] = (numeric(out, "H4_oxygen/99") == 1).astype(int)
    out["n_oxygen_sources"] = out[
        [
            "has_concentrator",
            "has_cylinders",
            "has_psa_internal",
            "has_psa_external",
            "has_other_oxygen",
        ]
    ].sum(axis=1)
    out["oxygen_profile"] = out.apply(classify_oxygen_profile, axis=1)
    out["oxygen_payment_label"] = numeric(out, "H5_o2_pay").map(
        OXYGEN_PAYMENT_DECODER
    )

    out["outage_days"] = numeric(out, "F1_outagedays")
    out["outage_hours"] = numeric(out, "F2_outagehrs")
    out["bad_power_days"] = numeric(out, "F4_baddays")
    out["short_outages"] = numeric(out, "F6_shortoutage")
    out["grid_cost"] = numeric(out, "B3_grid_cost")
    out["generator_cost"] = numeric(out, "C5_gen_cost")
    out["oxygen_cost"] = numeric(out, "H5_o2_cost")
    out["solar_total_value"] = numeric(out, "D6_a_solar_totval")
    out["solar_maintenance_adhoc"] = numeric(out, "D6_d_solar_maintadhoc")
    out["equipment_damage_binary"] = (numeric(out, "H1_medequip") == 1).astype(int)
    return out


def classify_energy_profile(row: pd.Series) -> str:
    parts = []
    if row.get("has_grid") == 1:
        parts.append("Grid")
    if row.get("has_generator") == 1:
        parts.append("Generator")
    if row.get("has_solar") == 1:
        parts.append("Solar")
    return " + ".join(parts) if parts else "No energy source"


def classify_oxygen_profile(row: pd.Series) -> str:
    parts = []
    if row.get("has_concentrator") == 1:
        parts.append("Concentrator")
    if row.get("has_cylinders") == 1:
        parts.append("Cylinders")
    if row.get("has_psa_internal") == 1:
        parts.append("Internal PSA")
    if row.get("has_psa_external") == 1:
        parts.append("External PSA")
    if row.get("has_other_oxygen") == 1:
        parts.append("Other oxygen")
    return " + ".join(parts) if parts else "No oxygen source"


def make_respondent_sample(df: pd.DataFrame) -> pd.DataFrame:
    # Preserve the notebook rule exactly: completeness sort, then first
    # phone_clean + A8_FOSA pair. This remains respondent-level, not facility-level.
    return (
        df.sort_values(by=["completeness_score"], ascending=False)
        .drop_duplicates(subset=["phone_clean", "A8_FOSA_num"], keep="first")
        .reset_index(drop=True)
    )


def mode_or_first(series: pd.Series):
    values = series.dropna()
    if values.empty:
        return np.nan
    modes = values.mode(dropna=True)
    if not modes.empty:
        return modes.iloc[0]
    return values.iloc[0]


def joined_unique(series: pd.Series, limit: int = 12) -> str:
    values = []
    for value in series.dropna().astype(str):
        if value and value not in values:
            values.append(value)
    return " | ".join(values[:limit])


def non_null_unique_count(series: pd.Series) -> int:
    return int(series.dropna().astype(str).nunique())


def conflict_flag(series: pd.Series) -> int:
    return int(non_null_unique_count(series) > 1)


def max_numeric(series: pd.Series):
    nums = pd.to_numeric(series, errors="coerce").dropna()
    return nums.max() if not nums.empty else np.nan


def median_numeric(series: pd.Series):
    nums = pd.to_numeric(series, errors="coerce").dropna()
    return nums.median() if not nums.empty else np.nan


def latest_non_null(group: pd.DataFrame, column: str):
    if column not in group:
        return np.nan
    ordered = group.sort_values(
        ["submission_time_parsed", "completeness_score"],
        ascending=[False, False],
        na_position="last",
    )
    values = ordered[column].dropna()
    if values.empty:
        return np.nan
    return values.iloc[0]


def any_binary(group: pd.DataFrame, column: str):
    if column not in group:
        return np.nan
    values = pd.to_numeric(group[column], errors="coerce").dropna()
    if values.empty:
        return np.nan
    return int((values == 1).any())


def build_facility_master(respondent_sample: pd.DataFrame) -> pd.DataFrame:
    records = []
    for fosa, g in respondent_sample.groupby("A8_FOSA_num", dropna=False):
        record: dict[str, object] = {
            "A8_FOSA": fosa,
            "facility_rows": len(g),
            "respondent_phones": non_null_unique_count(g["phone_clean"]),
            "respondent_names": joined_unique(g.get("A2_name", pd.Series(dtype=str))),
            "respondent_roles": joined_unique(g.get("A4_role", pd.Series(dtype=str))),
            "raw_row_ids": joined_unique(g["raw_row_id"]),
            "submission_times": joined_unique(g.get("_submission_time", pd.Series(dtype=str))),
            "max_completeness_score": max_numeric(g["completeness_score"]),
            "multi_respondent_flag": int(len(g) > 1),
        }

        identity_cols = ["A5_province", "A6_zone", "A7_type", "A9_catchment"]
        for col in identity_cols:
            record[col] = mode_or_first(g[col]) if col in g else np.nan
            record[f"{col}_conflict"] = conflict_flag(g[col]) if col in g else 0

        for col in ["facility_name", "grid_type_label", "grid_architecture"]:
            if col in g:
                record[col] = mode_or_first(g[col])
                record[f"{col}_conflict"] = conflict_flag(g[col])

        binary_cols = [
            "has_grid",
            "has_generator",
            "has_solar",
            "has_charcoal",
            "has_concentrator",
            "has_cylinders",
            "has_psa_internal",
            "has_psa_external",
            "has_other_oxygen",
            "equipment_damage_binary",
            "I5_tech",
            "J1_ptreg",
            "J3_deathreg",
            "J4_morgue",
        ]
        for col in binary_cols:
            if col in g:
                record[col] = any_binary(g, col)
                record[f"{col}_conflict"] = conflict_flag(g[col])

        count_max_cols = [
            "conc_10l",
            "conc_5l",
            "total_concentrators",
            "C1_a_gencount",
            "C2_1_gencapac",
            "C2_2_gencapac",
            "C2_3_gencapac",
            "D3_solar_panel",
            "D4_solar_batt",
            "D4_solar_capac",
        ]
        for col in count_max_cols:
            if col in g:
                record[f"{col}_max"] = max_numeric(g[col])
                record[f"{col}_median"] = median_numeric(g[col])
                record[f"{col}_conflict"] = conflict_flag(g[col])

        median_cols = [
            "outage_days",
            "outage_hours",
            "bad_power_days",
            "short_outages",
            "grid_cost",
            "generator_cost",
            "oxygen_cost",
            "solar_total_value",
            "solar_maintenance_adhoc",
            "I2_wtp",
        ]
        for col in median_cols:
            if col in g:
                record[f"{col}_median"] = median_numeric(g[col])
                record[f"{col}_max"] = max_numeric(g[col])
                record[f"{col}_latest"] = latest_non_null(g, col)
                record[f"{col}_conflict"] = conflict_flag(g[col])

        # Recompute profiles from reconciled binary/count values.
        record["n_energy_sources"] = sum(
            int(record.get(col, 0) == 1)
            for col in ["has_grid", "has_generator", "has_solar"]
        )
        record["energy_profile"] = classify_energy_profile(pd.Series(record))
        record["n_oxygen_sources"] = sum(
            int(record.get(col, 0) == 1)
            for col in [
                "has_concentrator",
                "has_cylinders",
                "has_psa_internal",
                "has_psa_external",
                "has_other_oxygen",
            ]
        )
        record["oxygen_profile"] = classify_oxygen_profile(pd.Series(record))
        record["oxygen_energy_profile"] = (
            f"{record['energy_profile']} :: {record['oxygen_profile']}"
        )

        conflict_cols = [k for k, v in record.items() if k.endswith("_conflict") and v == 1]
        record["conflict_flag_count"] = len(conflict_cols)
        record["conflict_fields"] = " | ".join(
            k.removesuffix("_conflict") for k in conflict_cols[:24]
        )
        records.append(record)

    return pd.DataFrame(records).sort_values("A8_FOSA").reset_index(drop=True)


def write_rules_doc(out_path: Path, summary: dict) -> None:
    lines = [
        "# DRC2 Facility Master Build",
        "",
        "## Tables Created",
        "",
        "- `raw_submissions.csv`: all raw survey submissions with helper fields.",
        "- `respondent_sample.csv`: speed-run notebook deduplication, one row per `phone_clean + A8_FOSA`.",
        "- `facility_master.csv`: one row per `A8_FOSA`, reconciled from `respondent_sample`.",
        "- `facility_master_conflicts.csv`: facilities with multiple respondent rows or at least one reconciled-field conflict.",
        "",
        "## Row Counts",
        "",
        f"- Raw submissions: {summary['raw_rows']}",
        f"- Respondent sample rows: {summary['respondent_rows']}",
        f"- Facility master rows: {summary['facility_rows']}",
        f"- Facilities with multiple respondent rows: {summary['multi_respondent_facilities']}",
        f"- Facilities with at least one conflict flag: {summary['facilities_with_conflicts']}",
        "",
        "## Reconciliation Rules",
        "",
        "- Identity fields use mode/first non-missing value and carry a conflict flag when respondents disagree.",
        "- Binary infrastructure/access fields use `any yes`, equivalent to max across respondent rows, and carry conflict flags.",
        "- Asset counts and capacities retain max, median, and conflict flags. The headline facility-master value should generally use max for stock/capacity.",
        "- Reliability and cost variables retain median, max, latest, and conflict flags. Median is the safer descriptive default unless a role-priority rule is later approved.",
        "- Free text and respondent identity fields are concatenated for audit, not treated as clean analytical categories.",
        "- Energy and oxygen profiles are recomputed after reconciliation.",
        "",
        "## Important Caveats",
        "",
        "- The Kobo choice-list labels and facility-key file were not present locally in this session. This build therefore preserves coded province, role, and facility-type fields, while decoding only the grid and oxygen-payment fields reconstructed from the notebook.",
        "- Facility names are only included if present in the source table or added later from a facility key.",
        "- This is a first facility-master build for analysis planning. Publication-grade analysis should review conflict facilities and add label files when available.",
        "",
    ]
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, default=None)
    parser.add_argument("--out-dir", type=Path, default=Path("outputs/drc2_facility_master"))
    args = parser.parse_args()

    source = args.csv or find_default_csv()
    raw_input = pd.read_csv(source, low_memory=False)
    raw_submissions = add_standard_fields(raw_input)
    respondent_sample = make_respondent_sample(raw_submissions)
    facility_master = build_facility_master(respondent_sample)
    conflicts = facility_master[
        (facility_master["multi_respondent_flag"] == 1)
        | (facility_master["conflict_flag_count"] > 0)
    ].copy()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    Path("docs").mkdir(exist_ok=True)
    raw_submissions.to_csv(args.out_dir / "raw_submissions.csv", index=False)
    respondent_sample.to_csv(args.out_dir / "respondent_sample.csv", index=False)
    facility_master.to_csv(args.out_dir / "facility_master.csv", index=False)
    conflicts.to_csv(args.out_dir / "facility_master_conflicts.csv", index=False)

    summary = {
        "source": str(source),
        "raw_rows": int(len(raw_submissions)),
        "respondent_rows": int(len(respondent_sample)),
        "facility_rows": int(len(facility_master)),
        "raw_unique_fosa": int(raw_submissions["A8_FOSA_num"].nunique(dropna=True)),
        "respondent_unique_fosa": int(respondent_sample["A8_FOSA_num"].nunique(dropna=True)),
        "multi_respondent_facilities": int(
            facility_master["multi_respondent_flag"].sum()
        ),
        "facilities_with_conflicts": int((facility_master["conflict_flag_count"] > 0).sum()),
        "output_dir": str(args.out_dir),
    }
    (args.out_dir / "facility_master_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    write_rules_doc(Path("docs/drc2-facility-master-build.md"), summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
