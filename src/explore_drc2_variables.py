#!/usr/bin/env python3
"""Profile the DRC2 survey variables for DRC3a analysis planning."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import pandas as pd


SECTION_DOMAINS = {
    "A": "Facility identity and respondent metadata",
    "B": "Internet and grid electricity",
    "C": "Generator assets, use, and cost",
    "D": "Solar assets, finance, and quality",
    "E": "Charcoal use and cost",
    "F": "Outages, bad power days, and recall reliability",
    "G": "Maintenance and equipment failure",
    "H": "Medical oxygen equipment and oxygen access",
    "I": "Willingness-to-pay, technical capacity, and operations",
    "J": "Registers, mortality records, and morgue capacity",
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


def column_domain(column: str) -> str:
    if column.startswith("_") or column.startswith("meta/"):
        return "Submission metadata"
    if column in {"start", "end", "intro", "date", "outage_note", "recall_note"}:
        return "Survey timing and notes"
    match = re.match(r"([A-J])\d", column)
    if match:
        return SECTION_DOMAINS.get(match.group(1), "Survey variables")
    return "Other derived or helper fields"


def variable_family(column: str) -> str:
    if "/" in column:
        return "select-multiple expansion"
    if re.search(r"_o($|_)", column):
        return "free-text other"
    if column.startswith("_") or column.startswith("meta/"):
        return "metadata"
    if re.search(r"(date|start|end)", column, re.I):
        return "date/time"
    if re.search(r"(cost|capac|panel|batt|count|days|hrs|num|time|catchment)", column, re.I):
        return "numeric or count"
    return "single response"


def infer_kind(series: pd.Series) -> str:
    non_null = series.dropna()
    if non_null.empty:
        return "empty"
    numeric = pd.to_numeric(non_null, errors="coerce")
    numeric_share = numeric.notna().mean()
    unique_count = non_null.astype(str).nunique(dropna=True)
    if numeric_share > 0.95:
        if unique_count <= 12:
            return "coded categorical numeric"
        return "continuous/count numeric"
    if unique_count <= 15:
        return "categorical text"
    return "free text / identifier"


def top_values(series: pd.Series, max_items: int = 5) -> str:
    counts = series.dropna().astype(str).value_counts().head(max_items)
    return " | ".join(f"{idx}: {val}" for idx, val in counts.items())


def analytical_readiness(row: dict) -> str:
    missing = row["missing_pct"]
    kind = row["inferred_kind"]
    family = row["variable_family"]
    domain = row["domain"]
    if domain == "Submission metadata":
        return "exclude from substantive analysis"
    if missing >= 90:
        return "low readiness: mostly missing"
    if family == "free-text other":
        return "needs coding: free-text other"
    if kind == "free text / identifier" and domain != "Facility identity and respondent metadata":
        return "needs text review/coding"
    if missing >= 50:
        return "conditional analysis: high missingness"
    if kind in {"coded categorical numeric", "categorical text"}:
        return "ready for descriptive/cross-tab analysis"
    if kind == "continuous/count numeric":
        return "ready for distribution/outlier analysis"
    return "review"


def suggested_use(row: dict) -> str:
    domain = row["domain"]
    col = row["column"]
    if domain == "Facility identity and respondent metadata":
        return "stratification, joining, facility master table"
    if domain == "Internet and grid electricity":
        return "energy regime classification; grid access/source analysis"
    if domain == "Generator assets, use, and cost":
        return "backup regime, operational burden, diesel/generator dependence"
    if domain == "Solar assets, finance, and quality":
        return "solar/autonomy regime; finance and quality analysis"
    if domain == "Charcoal use and cost":
        return "energy substitution and facility operations context"
    if domain == "Outages, bad power days, and recall reliability":
        return "power reliability, fragility, outage-burden indices"
    if domain == "Maintenance and equipment failure":
        return "human infrastructure and repair capacity"
    if domain == "Medical oxygen equipment and oxygen access":
        return "oxygen regime classification and oxygen-energy coupling"
    if domain == "Willingness-to-pay, technical capacity, and operations":
        return "affordability, technical readiness, operational capacity"
    if domain == "Registers, mortality records, and morgue capacity":
        return "data quality, mortality-record availability, denominator readiness"
    if "uuid" in col.lower() or col.startswith("_"):
        return "audit/provenance only"
    return "review"


def build_inventory(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    n = len(df)
    for idx, column in enumerate(df.columns, start=1):
        series = df[column]
        non_missing = int(series.notna().sum())
        missing = n - non_missing
        row = {
            "order": idx,
            "column": column,
            "domain": column_domain(column),
            "variable_family": variable_family(column),
            "inferred_kind": infer_kind(series),
            "non_missing": non_missing,
            "missing": missing,
            "missing_pct": round(missing / n * 100, 1) if n else 0,
            "unique_values": int(series.dropna().astype(str).nunique()),
            "top_values": top_values(series),
        }
        row["analytical_readiness"] = analytical_readiness(row)
        row["suggested_drc3a_use"] = suggested_use(row)
        rows.append(row)
    return pd.DataFrame(rows)


def build_domain_summary(inventory: pd.DataFrame) -> pd.DataFrame:
    grouped = []
    for domain, g in inventory.groupby("domain", sort=False):
        grouped.append(
            {
                "domain": domain,
                "variables": len(g),
                "median_missing_pct": round(float(g["missing_pct"].median()), 1),
                "ready_descriptive": int(
                    g["analytical_readiness"].str.contains("ready for descriptive").sum()
                ),
                "ready_numeric": int(
                    g["analytical_readiness"].str.contains("ready for distribution").sum()
                ),
                "needs_coding_or_review": int(
                    g["analytical_readiness"].str.contains("needs|review", regex=True).sum()
                ),
                "mostly_missing": int(
                    g["analytical_readiness"].str.contains("mostly missing").sum()
                ),
            }
        )
    return pd.DataFrame(grouped)


def write_report(
    df: pd.DataFrame,
    inventory: pd.DataFrame,
    domain_summary: pd.DataFrame,
    out_path: Path,
    source_path: Path,
) -> None:
    priority_domains = [
        "Internet and grid electricity",
        "Generator assets, use, and cost",
        "Solar assets, finance, and quality",
        "Outages, bad power days, and recall reliability",
        "Maintenance and equipment failure",
        "Medical oxygen equipment and oxygen access",
        "Willingness-to-pay, technical capacity, and operations",
        "Registers, mortality records, and morgue capacity",
    ]

    lines = [
        "# DRC2 Survey Variable Exploration",
        "",
        f"Source file: `{source_path}`",
        f"Rows: {len(df):,}",
        f"Columns: {len(df.columns):,}",
        "",
        "## Domain Summary",
        "",
        "| Domain | Variables | Median missing % | Ready descriptive | Ready numeric | Needs coding/review | Mostly missing |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for _, row in domain_summary.iterrows():
        lines.append(
            f"| {row['domain']} | {row['variables']} | {row['median_missing_pct']} | "
            f"{row['ready_descriptive']} | {row['ready_numeric']} | "
            f"{row['needs_coding_or_review']} | {row['mostly_missing']} |"
        )

    lines.extend(
        [
            "",
            "## First Analytical Reading",
            "",
            "The DRC2 survey is analyzable as a facility-regime dataset. Its strongest immediate use for DRC3a is not one-off variables, but derived classifications that combine multiple variables into energy regimes, oxygen regimes, reliability burden, operating burden, and human infrastructure readiness.",
            "",
            "Recommended first derived constructs:",
            "",
            "- `facility_master`: province, health zone, facility type, facility identifier, catchment, respondent role.",
            "- `energy_source_count`: grid, generator, solar, charcoal and other sources.",
            "- `energy_regime`: no source, grid only, generator only, solar only, grid + generator, solar + generator, grid + solar, grid + solar + generator, other/hybrid.",
            "- `backup_capacity`: generator count/capacity/autostart/use frequency plus solar battery presence/capacity.",
            "- `reliability_burden`: outage days, outage hours, typical bad days, short-outage frequency, recall outage counts.",
            "- `energy_cost_burden`: grid, generator, solar maintenance, charcoal cost variables after currency/outlier review.",
            "- `oxygen_regime`: no oxygen, 5L/10L concentrators, cylinders/other oxygen sources where available, mixed oxygen access.",
            "- `oxygen_energy_coupling`: oxygen regime crossed with energy regime, backup capacity, and reliability burden.",
            "- `human_infrastructure`: technician availability, maintenance pathways, biomedical equipment failure variables, record/register availability.",
            "",
            "## Priority Variable Domains For DRC3a",
            "",
        ]
    )

    for domain in priority_domains:
        g = inventory[inventory["domain"] == domain]
        if g.empty:
            continue
        lines.append(f"### {domain}")
        top = g.sort_values(["missing_pct", "order"]).head(12)
        for _, row in top.iterrows():
            lines.append(
                f"- `{row['column']}`: {row['inferred_kind']}; "
                f"missing {row['missing_pct']}%; {row['suggested_drc3a_use']}."
            )
        lines.append("")

    lines.extend(
        [
            "## Cautions",
            "",
            "- Numeric coded categorical variables need labels/decoders before publication-grade interpretation.",
            "- Slash columns such as `E1_a_charc_use/1` are select-multiple expansions and should be recombined carefully.",
            "- Free-text `other` variables should be manually coded into controlled categories if used.",
            "- Cost variables need currency, unit, and outlier review before substantive claims.",
            "- Mortality/register variables should be treated first as data-readiness variables unless linked to validated mortality datasets.",
            "",
            "## Suggested Next Script",
            "",
            "`src/build_drc2_facility_master.py` should create a cleaned facility-level table with stable IDs, labels, and first-pass regime classifications.",
            "",
        ]
    )
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, default=None)
    parser.add_argument("--out-dir", type=Path, default=Path("outputs/drc2_variable_exploration"))
    args = parser.parse_args()

    source = args.csv or find_default_csv()
    df = pd.read_csv(source, low_memory=False)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    Path("docs").mkdir(exist_ok=True)

    inventory = build_inventory(df)
    summary = build_domain_summary(inventory)

    inventory_path = args.out_dir / "drc2_variable_inventory.csv"
    summary_path = args.out_dir / "drc2_domain_summary.csv"
    json_path = args.out_dir / "drc2_profile_summary.json"
    report_path = Path("docs/drc2-variable-exploration.md")

    inventory.to_csv(inventory_path, index=False)
    summary.to_csv(summary_path, index=False)
    json_path.write_text(
        json.dumps(
            {
                "source": str(source),
                "rows": len(df),
                "columns": len(df.columns),
                "outputs": {
                    "inventory": str(inventory_path),
                    "domain_summary": str(summary_path),
                    "report": str(report_path),
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    write_report(df, inventory, summary, report_path, source)

    print(json_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
