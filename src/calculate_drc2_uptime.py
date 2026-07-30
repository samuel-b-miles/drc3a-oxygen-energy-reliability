#!/usr/bin/env python3
"""Reconstruct DRC2 survey-based uptime measures using Ryan's DRC2 definitions."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RESPONDENT = ROOT / "outputs/drc2_facility_master/respondent_sample.csv"
MASTER = ROOT / "outputs/drc2_facility_master/facility_master.csv"
OUT = ROOT / "outputs/drc2_uptime"
TAB = OUT / "tables"
FIG = OUT / "figures"


FACILITY_TYPE_LABELS = {1: "HGR", 2: "CH", 3: "CSR", 5: "HP", 6: "CM"}
PROVINCE_LABELS = {1: "Nord-Kivu", 2: "Sud-Kivu", 3: "Haut Katanga"}


def num(df: pd.DataFrame, col: str) -> pd.Series:
    return pd.to_numeric(df[col], errors="coerce")


def clamp(series: pd.Series, low: float, high: float) -> pd.Series:
    return series.clip(lower=low, upper=high)


def weighted_uptime(perfect_days: pd.Series, typical_weight: pd.Series, bad_weight: pd.Series, typical_out_hours: pd.Series, bad_out_hours: pd.Series) -> pd.Series:
    """Perfect days fixed; non-perfect days split by normalized typical/bad weights."""
    perfect_days = clamp(perfect_days, 0, 7)
    perfect_fraction = perfect_days / 7
    remaining_fraction = 1 - perfect_fraction
    typical_uptime = (24 - clamp(typical_out_hours, 0, 24)) / 24
    bad_uptime = (24 - clamp(bad_out_hours, 0, 24)) / 24
    typical_weight = clamp(typical_weight, 0, 7)
    bad_weight = clamp(bad_weight, 0, 7)
    denom = typical_weight + bad_weight
    nonperfect_uptime = pd.Series(np.where(denom > 0, (typical_weight * typical_uptime + bad_weight * bad_uptime) / denom, typical_uptime), index=perfect_days.index)
    return (perfect_fraction + remaining_fraction * nonperfect_uptime).clip(0, 1)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    TAB.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)

    respondents = pd.read_csv(RESPONDENT)
    master = pd.read_csv(MASTER)
    df = respondents.copy()

    # Ryan DRC2 paper: v1 prioritizes the respondent count of "perfect" power days,
    # then calculates remaining uptime from a weighted average of typical and bad days.
    # Provisional column mapping until the XLSForm choices/labels are restored:
    # F1_outagedays = perfect-day count, F3_typicaldays = typical-day weight,
    # F2_outagehrs = outage hours on typical days, F4_baddays = outage hours on bad days.
    perfect_days_v1 = num(df, "F1_outagedays")
    typical_weight_v1 = num(df, "F3_typicaldays")
    bad_weight_v1 = (7 - clamp(perfect_days_v1, 0, 7) - clamp(typical_weight_v1, 0, 7)).clip(lower=0)
    df["uptime_v1_reconstructed"] = weighted_uptime(
        perfect_days_v1,
        typical_weight_v1,
        bad_weight_v1,
        num(df, "F2_outagehrs"),
        num(df, "F4_baddays"),
    )

    # Ryan v3: three-day recall. The survey has reported outage duration for three recalled days.
    recall_outage_hours = pd.concat(
        [
            clamp(num(df, "F8a_2_timeout"), 0, 24),
            clamp(num(df, "F8b_2_timeout"), 0, 24),
            clamp(num(df, "F8c_2_timeout"), 0, 24),
        ],
        axis=1,
    )
    df["uptime_v3_three_day_recall"] = (1 - recall_outage_hours.sum(axis=1) / 72).clip(0, 1)
    df["reliable_v1_917"] = (df["uptime_v1_reconstructed"] > 0.917).astype("Int64")
    df["reliable_v3_917"] = (df["uptime_v3_three_day_recall"] > 0.917).astype("Int64")

    facility_uptime = (
        df.groupby("A8_FOSA")
        .agg(
            uptime_v1_reconstructed=("uptime_v1_reconstructed", "median"),
            uptime_v3_three_day_recall=("uptime_v3_three_day_recall", "median"),
            reliable_v1_917=("reliable_v1_917", "max"),
            reliable_v3_917=("reliable_v3_917", "max"),
        )
        .reset_index()
    )
    out = master.merge(facility_uptime, on="A8_FOSA", how="left")
    out["facility_type"] = out["A7_type"].map(FACILITY_TYPE_LABELS)
    out["province"] = out["A5_province"].map(PROVINCE_LABELS)
    out["has_any_oxygen"] = (out["n_oxygen_sources"] > 0).astype(int)
    out["has_multi_oxygen"] = (out["n_oxygen_sources"] >= 2).astype(int)
    out.to_csv(TAB / "facility_master_with_reconstructed_uptime.csv", index=False)

    summary = out[
        [
            "uptime_v1_reconstructed",
            "uptime_v3_three_day_recall",
            "reliable_v1_917",
            "reliable_v3_917",
        ]
    ].describe().T
    summary.to_csv(TAB / "uptime_summary.csv")

    by_energy = (
        out.groupby("energy_profile")[
            ["uptime_v1_reconstructed", "uptime_v3_three_day_recall", "reliable_v1_917", "reliable_v3_917"]
        ]
        .agg(["count", "median", "mean"])
        .round(3)
    )
    by_energy.to_csv(TAB / "uptime_by_energy_profile.csv")

    by_oxygen = (
        out.groupby("oxygen_profile")[
            ["uptime_v1_reconstructed", "uptime_v3_three_day_recall", "reliable_v1_917", "reliable_v3_917"]
        ]
        .agg(["count", "median", "mean"])
        .round(3)
    )
    by_oxygen.to_csv(TAB / "uptime_by_oxygen_profile.csv")

    oxygen_outcomes = ["has_any_oxygen", "has_concentrator", "has_cylinders", "has_multi_oxygen", "equipment_damage_binary"]
    assoc_rows = []
    for outcome in oxygen_outcomes:
        for uptime_col in ["reliable_v1_917", "reliable_v3_917"]:
            tab = pd.crosstab(out[uptime_col], out[outcome]).reindex(index=[0, 1], columns=[0, 1], fill_value=0)
            vals = tab.values.astype(float) + 0.5
            or_value = (vals[1, 1] * vals[0, 0]) / (vals[1, 0] * vals[0, 1])
            assoc_rows.append(
                {
                    "uptime_predictor": uptime_col,
                    "outcome": outcome,
                    "unreliable_no": int(tab.loc[0, 0]),
                    "unreliable_yes": int(tab.loc[0, 1]),
                    "reliable_no": int(tab.loc[1, 0]),
                    "reliable_yes": int(tab.loc[1, 1]),
                    "odds_ratio": round(float(or_value), 3),
                }
            )
    pd.DataFrame(assoc_rows).to_csv(TAB / "uptime_oxygen_binary_associations.csv", index=False)

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5), constrained_layout=True)
    axes[0].hist(out["uptime_v1_reconstructed"].dropna(), bins=20, color="#3268a8", alpha=0.85)
    axes[0].axvline(0.917, color="#c43c39", linewidth=2)
    axes[0].set_title("Reconstructed uptime v1")
    axes[0].set_xlabel("Uptime")
    axes[0].set_ylabel("Facilities")
    axes[1].hist(out["uptime_v3_three_day_recall"].dropna(), bins=20, color="#4b8f5a", alpha=0.85)
    axes[1].axvline(0.917, color="#c43c39", linewidth=2)
    axes[1].set_title("Three-day recall uptime v3")
    axes[1].set_xlabel("Uptime")
    fig.suptitle("DRC2 survey-based uptime reconstructions", fontsize=15, weight="bold")
    fig.savefig(FIG / "fig_uptime_distributions.png", dpi=250, bbox_inches="tight")
    plt.close(fig)

    print(summary.to_string())
    print(TAB / "facility_master_with_reconstructed_uptime.csv")
    print(FIG / "fig_uptime_distributions.png")


if __name__ == "__main__":
    main()
