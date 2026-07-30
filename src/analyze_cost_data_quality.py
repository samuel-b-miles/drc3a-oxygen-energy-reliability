#!/usr/bin/env python3
"""Audit and conservatively analyze DRC2 cost/spend variables."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import fisher_exact, kruskal, mannwhitneyu, spearmanr


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "drc3a_cost_quality"


COST_VARS = {
    "grid_cost_median": {
        "label": "Grid cost",
        "source_flag": "has_grid",
        "condition": "facility reports grid access",
    },
    "generator_cost_median": {
        "label": "Generator cost",
        "source_flag": "has_generator",
        "condition": "facility reports generator access",
    },
    "oxygen_cost_median": {
        "label": "Oxygen cost",
        "source_flag": "has_any_oxygen",
        "condition": "facility reports any oxygen source",
    },
    "solar_total_value_median": {
        "label": "Solar total value",
        "source_flag": "has_solar",
        "condition": "facility reports solar access",
    },
    "solar_maintenance_adhoc_median": {
        "label": "Solar ad hoc maintenance",
        "source_flag": "has_solar",
        "condition": "facility reports solar access",
    },
    "I2_wtp_median": {
        "label": "WTP for improved electricity",
        "source_flag": None,
        "condition": "all facilities",
    },
}


OUTCOMES = [
    "has_any_oxygen",
    "has_concentrator",
    "has_10l_conc",
    "has_5l_conc",
    "has_multi_conc",
    "has_cylinders",
    "has_multi_oxygen",
    "equipment_damage_binary",
    "Oxygen concentrator / oxygen device",
    "reliable_v1_917",
]


GROUPS = [
    "province",
    "facility_type",
    "grid_architecture",
    "energy_profile",
    "oxygen_profile",
]


def stars(p: float) -> str:
    if pd.isna(p):
        return ""
    if p < 0.001:
        return "***"
    if p < 0.01:
        return "**"
    if p < 0.05:
        return "*"
    if p < 0.10:
        return "~"
    return ""


def add_derived(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in COST_VARS:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out["has_any_oxygen"] = (out["n_oxygen_sources"].fillna(0) > 0).astype(int)
    out["has_10l_conc"] = (out["conc_10l_max"].fillna(0) > 0).astype(int)
    out["has_5l_conc"] = (out["conc_5l_max"].fillna(0) > 0).astype(int)
    out["has_multi_conc"] = (out["total_concentrators_max"].fillna(0) >= 2).astype(int)
    return out


def source_consistent_mask(df: pd.DataFrame, cost_col: str) -> pd.Series:
    flag = COST_VARS[cost_col]["source_flag"]
    if flag is None:
        return pd.Series(True, index=df.index)
    return df[flag].fillna(0).astype(int).eq(1)


def build_long_cost_table(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for col, meta in COST_VARS.items():
        values = df[col]
        positive = values > 0
        source_consistent = source_consistent_mask(df, col)
        pos_values = values[positive]
        p95 = pos_values.quantile(0.95) if len(pos_values) else np.nan
        p99 = pos_values.quantile(0.99) if len(pos_values) else np.nan
        for idx, value in values.items():
            if pd.isna(value):
                status = "missing"
            elif value < 0:
                status = "invalid_negative"
            elif value == 0:
                status = "reported_zero"
            elif not source_consistent.loc[idx]:
                status = "positive_but_source_absent"
            elif pd.notna(p99) and value > p99:
                status = "above_positive_p99"
            elif pd.notna(p95) and value > p95:
                status = "above_positive_p95"
            else:
                status = "analysis_ready_positive"
            rows.append(
                {
                    "A8_FOSA": df.loc[idx, "A8_FOSA"],
                    "variable": col,
                    "label": meta["label"],
                    "value": value,
                    "source_condition": meta["condition"],
                    "source_consistent": bool(source_consistent.loc[idx]),
                    "status": status,
                    "keep_conservative": status == "analysis_ready_positive",
                    "keep_sensitivity_p99": status
                    in {"analysis_ready_positive", "above_positive_p95"},
                    "province": df.get("province", pd.Series(index=df.index)).loc[idx],
                    "facility_type": df.get("facility_type", pd.Series(index=df.index)).loc[idx],
                    "energy_profile": df.loc[idx, "energy_profile"],
                    "oxygen_profile": df.loc[idx, "oxygen_profile"],
                }
            )
    return pd.DataFrame(rows)


def summarize_cost_quality(long: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for var, g in long.groupby("variable"):
        positive = g[g["value"] > 0]["value"]
        ready = g[g["keep_conservative"]]["value"]
        rows.append(
            {
                "variable": var,
                "label": g["label"].iloc[0],
                "n_total_facilities": int(g["A8_FOSA"].nunique()),
                "n_missing": int(g["status"].eq("missing").sum()),
                "n_zero": int(g["status"].eq("reported_zero").sum()),
                "n_positive": int((g["value"] > 0).sum()),
                "n_positive_source_absent": int(
                    g["status"].eq("positive_but_source_absent").sum()
                ),
                "n_above_positive_p95": int(
                    g["status"].eq("above_positive_p95").sum()
                ),
                "n_above_positive_p99": int(
                    g["status"].eq("above_positive_p99").sum()
                ),
                "n_analysis_ready_positive": int(g["keep_conservative"].sum()),
                "median_positive": positive.median(),
                "p95_positive": positive.quantile(0.95) if len(positive) else np.nan,
                "p99_positive": positive.quantile(0.99) if len(positive) else np.nan,
                "max_positive": positive.max() if len(positive) else np.nan,
                "median_conservative": ready.median(),
                "max_conservative": ready.max() if len(ready) else np.nan,
            }
        )
    return pd.DataFrame(rows)


def binary_or(df: pd.DataFrame, x: str, y: str) -> dict[str, object] | None:
    d = df[[x, y]].dropna()
    if len(d) < 30 or d[x].nunique() != 2 or d[y].nunique() != 2:
        return None
    tab = pd.crosstab(d[x].astype(int), d[y].astype(int))
    for v in [0, 1]:
        if v not in tab.index:
            tab.loc[v] = 0
        if v not in tab.columns:
            tab[v] = 0
    tab = tab.sort_index().sort_index(axis=1)
    a, b, c, dd = tab.loc[1, 1], tab.loc[1, 0], tab.loc[0, 1], tab.loc[0, 0]
    odds_ratio = ((a + 0.5) * (dd + 0.5)) / ((b + 0.5) * (c + 0.5))
    p = fisher_exact([[a, b], [c, dd]])[1]
    return {
        "predictor": x,
        "outcome": y,
        "n": int(len(d)),
        "exposed_n": int((d[x] == 1).sum()),
        "outcome_n": int((d[y] == 1).sum()),
        "odds_ratio": odds_ratio,
        "p_value": p,
        "stars": stars(p),
    }


def analyze_cleaned_costs(df: pd.DataFrame, long: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    wide = df.copy()
    for var in COST_VARS:
        ready_ids = set(
            long[(long["variable"] == var) & (long["keep_conservative"])]["A8_FOSA"]
        )
        p99_ids = set(
            long[(long["variable"] == var) & (long["keep_sensitivity_p99"])]["A8_FOSA"]
        )
        wide[f"{var}_clean"] = wide[var].where(wide["A8_FOSA"].isin(ready_ids))
        wide[f"{var}_p99_sensitivity"] = wide[var].where(wide["A8_FOSA"].isin(p99_ids))
        median_clean = wide[f"{var}_clean"].median()
        wide[f"{var}_high_clean"] = np.where(
            wide[f"{var}_clean"].notna(),
            (wide[f"{var}_clean"] > median_clean).astype(int),
            np.nan,
        )

    binary_rows = []
    continuous_rows = []
    for var in COST_VARS:
        clean = f"{var}_clean"
        high = f"{var}_high_clean"
        for outcome in OUTCOMES:
            if outcome not in wide:
                continue
            result = binary_or(wide, high, outcome)
            if result:
                result["cost_variable"] = var
                binary_rows.append(result)
            d = wide[[clean, outcome]].dropna()
            if len(d) >= 30 and d[outcome].nunique() == 2:
                g0 = d.loc[d[outcome] == 0, clean]
                g1 = d.loc[d[outcome] == 1, clean]
                if len(g0) >= 5 and len(g1) >= 5:
                    stat, p = mannwhitneyu(g1, g0, alternative="two-sided")
                    continuous_rows.append(
                        {
                            "cost_variable": var,
                            "outcome": outcome,
                            "n": int(len(d)),
                            "median_if_outcome_1": g1.median(),
                            "median_if_outcome_0": g0.median(),
                            "mean_if_outcome_1": g1.mean(),
                            "mean_if_outcome_0": g0.mean(),
                            "p_value": p,
                            "stars": stars(p),
                        }
                    )

    group_rows = []
    for var in COST_VARS:
        clean = f"{var}_clean"
        for group in GROUPS:
            d = wide[[group, clean]].dropna()
            if len(d) < 30 or d[group].nunique() < 2:
                continue
            samples = [g[clean].values for _, g in d.groupby(group) if len(g) >= 3]
            if len(samples) < 2:
                continue
            stat, p = kruskal(*samples)
            group_rows.append(
                {
                    "cost_variable": var,
                    "group": group,
                    "n": int(len(d)),
                    "levels": int(d[group].nunique()),
                    "kruskal_h": stat,
                    "p_value": p,
                    "stars": stars(p),
                }
            )
    return pd.DataFrame(binary_rows), pd.DataFrame(continuous_rows), pd.DataFrame(group_rows)


def correlations(df: pd.DataFrame, long: pd.DataFrame) -> pd.DataFrame:
    wide = df.copy()
    for var in COST_VARS:
        ids = set(long[(long["variable"] == var) & (long["keep_conservative"])]["A8_FOSA"])
        wide[f"{var}_clean"] = wide[var].where(wide["A8_FOSA"].isin(ids))
    targets = [
        "total_concentrators_max",
        "conc_10l_max",
        "conc_5l_max",
        "outage_days_median",
        "outage_hours_median",
        "bad_power_days_median",
        "I2_wtp_median_clean",
    ]
    rows = []
    for var in COST_VARS:
        clean = f"{var}_clean"
        for target in targets:
            if target == clean or target not in wide:
                continue
            d = wide[[clean, target]].dropna()
            if len(d) < 30:
                continue
            rho, p = spearmanr(d[clean], d[target])
            rows.append(
                {
                    "cost_variable": var,
                    "target": target,
                    "n": int(len(d)),
                    "spearman_rho": rho,
                    "p_value": p,
                    "stars": stars(p),
                }
            )
    return pd.DataFrame(rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(ROOT / "outputs/drc2_uptime/tables/facility_master_with_reconstructed_uptime.csv")
    failures = pd.read_csv(ROOT / "outputs/drc2_equipment_failure/tables/equipment_failure_coded_facility_mentions.csv")
    oxygen_damage = failures[["A8_FOSA", "Oxygen concentrator / oxygen device"]]
    df = df.merge(oxygen_damage, on="A8_FOSA", how="left")
    df["Oxygen concentrator / oxygen device"] = (
        df["Oxygen concentrator / oxygen device"].fillna(0).astype(int)
    )
    df = add_derived(df)

    long = build_long_cost_table(df)
    quality = summarize_cost_quality(long)
    binary, continuous, group_tests = analyze_cleaned_costs(df, long)
    corr = correlations(df, long)

    long.to_csv(OUT / "cost_value_audit_long.csv", index=False)
    quality.to_csv(OUT / "cost_quality_summary.csv", index=False)
    binary.to_csv(OUT / "clean_cost_high_binary_tests.csv", index=False)
    continuous.to_csv(OUT / "clean_cost_continuous_group_tests.csv", index=False)
    group_tests.to_csv(OUT / "clean_cost_by_group_tests.csv", index=False)
    corr.to_csv(OUT / "clean_cost_spearman_correlations.csv", index=False)

    print(OUT)
    print("\nCost quality summary")
    print(quality.to_string(index=False))
    print("\nTop high-cost binary associations")
    print(binary.sort_values("p_value").head(25).to_string(index=False))
    print("\nTop continuous cost group differences")
    print(continuous.sort_values("p_value").head(25).to_string(index=False))
    print("\nTop cost group tests")
    print(group_tests.sort_values("p_value").head(20).to_string(index=False))
    print("\nTop correlations")
    print(corr.sort_values("p_value").head(20).to_string(index=False))


if __name__ == "__main__":
    main()
