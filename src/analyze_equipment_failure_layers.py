#!/usr/bin/env python3
"""Build layered descriptive tables for equipment-failure free-text coding."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from scipy.stats import chi2_contingency


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "drc3a_equipment_failure_layers"
FAILURE_FILE = ROOT / "outputs/drc2_equipment_failure/tables/equipment_failure_coded_facility_mentions.csv"
MASTER_FILE = ROOT / "outputs/drc2_uptime/tables/facility_master_with_reconstructed_uptime.csv"


EQUIPMENT_CATEGORIES = [
    "Oxygen concentrator / oxygen device",
    "Lighting / surgical theatre electrical devices",
    "Electrical components / power system",
    "Ultrasound / echography",
    "Patient monitoring / bedside clinical devices",
    "Computer / printer / office electronics",
    "Sterilization equipment",
    "Laboratory equipment",
    "Refrigeration / cold chain / morgue",
    "Maternal / neonatal equipment",
    "Laundry / water / utility equipment",
    "Radiography / X-ray",
]

CAUSE_CATEGORIES = [
    "Voltage instability / fluctuation",
    "Power cuts / abrupt restoration",
    "Insufficient power / no energy",
    "Short circuit / burned electronics",
    "Poor installation",
    "Lightning / atmospheric discharge",
]


def pct(num: float, den: float) -> float:
    return 100 * num / den if den else 0.0


def load() -> pd.DataFrame:
    fail = pd.read_csv(FAILURE_FILE)
    master = pd.read_csv(MASTER_FILE)
    keep = [
        "A8_FOSA",
        "province",
        "facility_type",
        "grid_architecture",
        "energy_profile",
        "oxygen_profile",
        "has_generator",
        "has_grid",
        "has_solar",
        "has_concentrator",
        "has_cylinders",
        "n_energy_sources",
        "n_oxygen_sources",
        "reliable_v1_917",
        "bad_power_days_median",
        "outage_hours_median",
        "total_concentrators_max",
        "conc_10l_max",
        "conc_5l_max",
    ]
    df = fail.merge(master[keep], on=["A8_FOSA", "province", "facility_type"], how="left")
    for col in EQUIPMENT_CATEGORIES + CAUSE_CATEGORIES:
        df[col] = df[col].fillna(0).astype(int)
    df["any_cause_coded"] = df[CAUSE_CATEGORIES].sum(axis=1).gt(0).astype(int)
    df["n_equipment_categories"] = df[EQUIPMENT_CATEGORIES].sum(axis=1)
    df["n_cause_categories"] = df[CAUSE_CATEGORIES].sum(axis=1)
    df["has_oxygen_damage"] = df["Oxygen concentrator / oxygen device"]
    df["has_nonoxygen_damage"] = df[EQUIPMENT_CATEGORIES[1:]].sum(axis=1).gt(0).astype(int)
    df["oxygen_damage_only"] = (
        df["has_oxygen_damage"].eq(1) & df["has_nonoxygen_damage"].eq(0)
    ).astype(int)
    df["oxygen_plus_other_damage"] = (
        df["has_oxygen_damage"].eq(1) & df["has_nonoxygen_damage"].eq(1)
    ).astype(int)
    df["reliability_class"] = df["reliable_v1_917"].map({1: "Reliable v1", 0: "Not reliable v1"})
    df["concentrator_stock"] = pd.cut(
        df["total_concentrators_max"].fillna(0),
        bins=[-0.1, 0, 1, 3, 999],
        labels=["0", "1", "2-3", "4+"],
    )
    return df


def category_cause_matrix(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    damaged = df[df["reported_damage"] == 1]
    for equipment in EQUIPMENT_CATEGORIES:
        eq = damaged[damaged[equipment] == 1]
        for cause in CAUSE_CATEGORIES:
            both = int((eq[cause] == 1).sum())
            rows.append(
                {
                    "equipment_category": equipment,
                    "cause_category": cause,
                    "equipment_mentions": int(len(eq)),
                    "cause_mentions_with_equipment": both,
                    "pct_of_equipment_mentions": pct(both, len(eq)),
                }
            )
    return pd.DataFrame(rows)


def category_by_group(df: pd.DataFrame) -> pd.DataFrame:
    group_cols = [
        "province",
        "facility_type",
        "grid_architecture",
        "energy_profile",
        "oxygen_profile",
        "reliability_class",
        "concentrator_stock",
    ]
    rows = []
    for group_col in group_cols:
        for level, g in df.groupby(group_col, dropna=False, observed=False):
            damaged = g[g["reported_damage"] == 1]
            for equipment in EQUIPMENT_CATEGORIES:
                mentions = int(g[equipment].sum())
                rows.append(
                    {
                        "group": group_col,
                        "level": level,
                        "facilities": int(len(g)),
                        "damage_reporting_facilities": int(len(damaged)),
                        "equipment_category": equipment,
                        "mentions": mentions,
                        "pct_all_facilities": pct(mentions, len(g)),
                        "pct_damage_reporting_facilities": pct(mentions, len(damaged)),
                    }
                )
    return pd.DataFrame(rows)


def cause_by_group(df: pd.DataFrame) -> pd.DataFrame:
    group_cols = [
        "province",
        "facility_type",
        "grid_architecture",
        "energy_profile",
        "oxygen_profile",
        "reliability_class",
        "concentrator_stock",
    ]
    rows = []
    for group_col in group_cols:
        for level, g in df.groupby(group_col, dropna=False, observed=False):
            damaged = g[g["reported_damage"] == 1]
            for cause in CAUSE_CATEGORIES:
                mentions = int(g[cause].sum())
                rows.append(
                    {
                        "group": group_col,
                        "level": level,
                        "facilities": int(len(g)),
                        "damage_reporting_facilities": int(len(damaged)),
                        "cause_category": cause,
                        "mentions": mentions,
                        "pct_all_facilities": pct(mentions, len(g)),
                        "pct_damage_reporting_facilities": pct(mentions, len(damaged)),
                    }
                )
    return pd.DataFrame(rows)


def oxygen_damage_profiles(df: pd.DataFrame) -> pd.DataFrame:
    oxygen = df[df["has_oxygen_damage"] == 1]
    rows = [
        {
            "profile": "oxygen_damage_facilities",
            "facilities": int(len(oxygen)),
            "oxygen_only": int(oxygen["oxygen_damage_only"].sum()),
            "oxygen_plus_other": int(oxygen["oxygen_plus_other_damage"].sum()),
            "pct_oxygen_only": pct(int(oxygen["oxygen_damage_only"].sum()), len(oxygen)),
            "pct_oxygen_plus_other": pct(
                int(oxygen["oxygen_plus_other_damage"].sum()), len(oxygen)
            ),
            "with_any_cause_coded": int(oxygen["any_cause_coded"].sum()),
            "pct_with_any_cause_coded": pct(int(oxygen["any_cause_coded"].sum()), len(oxygen)),
        }
    ]
    for cause in CAUSE_CATEGORIES:
        rows.append(
            {
                "profile": cause,
                "facilities": int(len(oxygen)),
                "oxygen_only": "",
                "oxygen_plus_other": "",
                "pct_oxygen_only": "",
                "pct_oxygen_plus_other": "",
                "with_any_cause_coded": int(oxygen[cause].sum()),
                "pct_with_any_cause_coded": pct(int(oxygen[cause].sum()), len(oxygen)),
            }
        )
    return pd.DataFrame(rows)


def contrast_tests(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for predictor in [
        "province",
        "facility_type",
        "grid_architecture",
        "energy_profile",
        "oxygen_profile",
        "reliability_class",
        "concentrator_stock",
    ]:
        for outcome in ["has_oxygen_damage", "oxygen_plus_other_damage", "any_cause_coded"]:
            d = df[[predictor, outcome]].dropna()
            if len(d) < 30 or d[predictor].nunique() < 2 or d[outcome].nunique() < 2:
                continue
            tab = pd.crosstab(d[predictor], d[outcome])
            chi2, p, dof, _ = chi2_contingency(tab)
            n = tab.to_numpy().sum()
            v = (chi2 / (n * (min(tab.shape) - 1))) ** 0.5
            rows.append(
                {
                    "predictor": predictor,
                    "outcome": outcome,
                    "n": int(n),
                    "levels": int(d[predictor].nunique()),
                    "chi2": chi2,
                    "dof": int(dof),
                    "cramers_v": v,
                    "p_value": p,
                }
            )
    return pd.DataFrame(rows).sort_values("p_value")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    df = load()
    matrix = category_cause_matrix(df)
    cat_group = category_by_group(df)
    cause_group = cause_by_group(df)
    oxygen_profile = oxygen_damage_profiles(df)
    tests = contrast_tests(df)

    matrix.to_csv(OUT / "equipment_category_by_cause_matrix.csv", index=False)
    cat_group.to_csv(OUT / "equipment_category_by_group_layers.csv", index=False)
    cause_group.to_csv(OUT / "damage_cause_by_group_layers.csv", index=False)
    oxygen_profile.to_csv(OUT / "oxygen_damage_profile.csv", index=False)
    tests.to_csv(OUT / "failure_layer_chisquare_tests.csv", index=False)

    print(OUT)
    print("\nOxygen damage profile")
    print(oxygen_profile.to_string(index=False))
    print("\nTop category/cause cells")
    print(
        matrix[matrix["cause_mentions_with_equipment"] > 0]
        .sort_values(["cause_mentions_with_equipment", "pct_of_equipment_mentions"], ascending=False)
        .head(40)
        .to_string(index=False)
    )
    print("\nTop group/category cells")
    print(
        cat_group[(cat_group["damage_reporting_facilities"] >= 10) & (cat_group["mentions"] > 0)]
        .sort_values(["pct_damage_reporting_facilities", "mentions"], ascending=False)
        .head(60)
        .to_string(index=False)
    )
    print("\nTop group/cause cells")
    print(
        cause_group[(cause_group["damage_reporting_facilities"] >= 10) & (cause_group["mentions"] > 0)]
        .sort_values(["pct_damage_reporting_facilities", "mentions"], ascending=False)
        .head(40)
        .to_string(index=False)
    )
    print("\nChi-square layer tests")
    print(tests.to_string(index=False))


if __name__ == "__main__":
    main()
