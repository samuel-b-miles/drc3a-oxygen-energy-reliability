#!/usr/bin/env python3
"""Explore correlates of any equipment damage and oxygen-specific damage."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency, fisher_exact, mannwhitneyu
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "drc3a_damage_associations"
FAILURE_FILE = ROOT / "outputs/drc2_equipment_failure/tables/equipment_failure_coded_facility_mentions.csv"
MASTER_FILE = ROOT / "outputs/drc2_uptime/tables/facility_master_with_reconstructed_uptime.csv"


OXYGEN_DAMAGE = "Oxygen concentrator / oxygen device"
FAILURE_CAUSES = [
    "Voltage instability / fluctuation",
    "Power cuts / abrupt restoration",
    "Short circuit / burned electronics",
    "Insufficient power / no energy",
    "Lightning / atmospheric discharge",
    "Poor installation",
]
FAILURE_CATEGORIES = [
    "Sterilization equipment",
    "Ultrasound / echography",
    "Computer / printer / office electronics",
    "Lighting / surgical theatre electrical devices",
    "Laboratory equipment",
    "Refrigeration / cold chain / morgue",
    "Maternal / neonatal equipment",
    "Patient monitoring / bedside clinical devices",
    "Radiography / X-ray",
    "Electrical components / power system",
    "Laundry / water / utility equipment",
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
    numeric_cols = [
        "conc_10l_max",
        "conc_5l_max",
        "total_concentrators_max",
        "C1_a_gencount_max",
        "C2_1_gencapac_max",
        "grid_cost_median",
        "generator_cost_median",
        "oxygen_cost_median",
        "solar_total_value_median",
        "solar_maintenance_adhoc_median",
        "I2_wtp_median",
        "outage_days_median",
        "outage_hours_median",
        "bad_power_days_median",
        "short_outages_median",
        "uptime_v1_reconstructed",
        "uptime_v3_three_day_recall",
    ]
    for col in numeric_cols:
        if col in out:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    out["has_any_oxygen"] = (out["n_oxygen_sources"].fillna(0) > 0).astype(int)
    out["has_10l_conc"] = (out["conc_10l_max"].fillna(0) > 0).astype(int)
    out["has_5l_conc"] = (out["conc_5l_max"].fillna(0) > 0).astype(int)
    out["has_multi_conc"] = (out["total_concentrators_max"].fillna(0) >= 2).astype(int)
    out["has_oxygen_damage"] = out[OXYGEN_DAMAGE].fillna(0).astype(int)
    out["has_nonoxygen_damage"] = (
        out[FAILURE_CATEGORIES].fillna(0).sum(axis=1).gt(0).astype(int)
    )
    out["any_failure_cause_coded"] = (
        out[FAILURE_CAUSES].fillna(0).sum(axis=1).gt(0).astype(int)
    )
    out["multi_category_damage"] = (
        out[[OXYGEN_DAMAGE] + FAILURE_CATEGORIES].fillna(0).sum(axis=1).ge(2).astype(int)
    )
    return out


def odds_ratio(df: pd.DataFrame, predictor: str, outcome: str, universe: str) -> dict[str, object] | None:
    d = df[[predictor, outcome]].dropna()
    if len(d) < 30 or d[predictor].nunique() != 2 or d[outcome].nunique() != 2:
        return None
    tab = pd.crosstab(d[predictor].astype(int), d[outcome].astype(int))
    for value in [0, 1]:
        if value not in tab.index:
            tab.loc[value] = 0
        if value not in tab.columns:
            tab[value] = 0
    tab = tab.sort_index().sort_index(axis=1)
    a, b, c, dd = tab.loc[1, 1], tab.loc[1, 0], tab.loc[0, 1], tab.loc[0, 0]
    or_value = ((a + 0.5) * (dd + 0.5)) / ((b + 0.5) * (c + 0.5))
    se = np.sqrt(1 / (a + 0.5) + 1 / (b + 0.5) + 1 / (c + 0.5) + 1 / (dd + 0.5))
    ci_low = np.exp(np.log(or_value) - 1.96 * se)
    ci_high = np.exp(np.log(or_value) + 1.96 * se)
    p = fisher_exact([[a, b], [c, dd]])[1]
    return {
        "universe": universe,
        "predictor": predictor,
        "outcome": outcome,
        "n": int(len(d)),
        "predictor_yes_n": int((d[predictor] == 1).sum()),
        "outcome_yes_n": int((d[outcome] == 1).sum()),
        "odds_ratio": or_value,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "p_value": p,
        "stars": stars(p),
    }


def categorical_test(df: pd.DataFrame, predictor: str, outcome: str, universe: str) -> dict[str, object] | None:
    d = df[[predictor, outcome]].dropna()
    if len(d) < 30 or d[predictor].nunique() < 2 or d[outcome].nunique() != 2:
        return None
    tab = pd.crosstab(d[predictor], d[outcome])
    chi2, p, dof, _ = chi2_contingency(tab)
    n = tab.to_numpy().sum()
    v = np.sqrt(chi2 / (n * (min(tab.shape) - 1)))
    return {
        "universe": universe,
        "predictor": predictor,
        "outcome": outcome,
        "n": int(n),
        "levels": int(d[predictor].nunique()),
        "chi2": chi2,
        "dof": int(dof),
        "cramers_v": v,
        "p_value": p,
        "stars": stars(p),
    }


def continuous_test(df: pd.DataFrame, predictor: str, outcome: str, universe: str) -> dict[str, object] | None:
    d = df[[predictor, outcome]].dropna()
    if len(d) < 30 or d[outcome].nunique() != 2:
        return None
    g0 = d.loc[d[outcome] == 0, predictor]
    g1 = d.loc[d[outcome] == 1, predictor]
    if len(g0) < 5 or len(g1) < 5:
        return None
    _, p = mannwhitneyu(g1, g0, alternative="two-sided")
    return {
        "universe": universe,
        "predictor": predictor,
        "outcome": outcome,
        "n": int(len(d)),
        "median_if_outcome_yes": g1.median(),
        "median_if_outcome_no": g0.median(),
        "mean_if_outcome_yes": g1.mean(),
        "mean_if_outcome_no": g0.mean(),
        "p_value": p,
        "stars": stars(p),
    }


def prediction_auc(df: pd.DataFrame, outcome: str, predictor_sets: dict[str, list[str]], universe: str) -> pd.DataFrame:
    rows = []
    for label, predictors in predictor_sets.items():
        cols = [c for c in predictors if c != outcome and c in df.columns]
        d = df[[outcome] + cols].dropna(subset=[outcome])
        d = d[d[outcome].isin([0, 1])]
        if len(d) < 80 or d[outcome].sum() < 10 or d[outcome].nunique() != 2:
            continue
        X = d[cols]
        y = d[outcome].astype(int)
        cat = [c for c in cols if X[c].dtype == "object"]
        num = [c for c in cols if c not in cat]
        pre = ColumnTransformer(
            [
                ("num", Pipeline([("imp", SimpleImputer(strategy="median")), ("sc", StandardScaler())]), num),
                (
                    "cat",
                    Pipeline(
                        [
                            ("imp", SimpleImputer(strategy="most_frequent")),
                            ("oh", OneHotEncoder(handle_unknown="ignore")),
                        ]
                    ),
                    cat,
                ),
            ]
        )
        model = Pipeline(
            [
                ("pre", pre),
                ("lr", LogisticRegression(max_iter=1000, class_weight="balanced")),
            ]
        )
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        try:
            pred = cross_val_predict(model, X, y, cv=cv, method="predict_proba")[:, 1]
            auc = roc_auc_score(y, pred)
        except Exception:
            auc = np.nan
        rows.append(
            {
                "universe": universe,
                "outcome": outcome,
                "predictor_set": label,
                "n": int(len(d)),
                "outcome_yes_n": int(y.sum()),
                "cv_auc": auc,
            }
        )
    return pd.DataFrame(rows)


def summaries(df: pd.DataFrame, outcome: str, universe: str) -> pd.DataFrame:
    predictors = [
        "province",
        "facility_type",
        "grid_architecture",
        "energy_profile",
        "oxygen_profile",
        "has_generator",
        "has_grid",
        "has_solar",
        "reliable_v1_917",
        "I5_tech",
    ]
    rows = []
    for predictor in predictors:
        if predictor not in df:
            continue
        for level, g in df.groupby(predictor, dropna=False):
            if len(g) < 3:
                continue
            rows.append(
                {
                    "universe": universe,
                    "outcome": outcome,
                    "predictor": predictor,
                    "level": level,
                    "n": int(len(g)),
                    "outcome_yes_n": int(g[outcome].sum()),
                    "outcome_pct": 100 * g[outcome].mean(),
                }
            )
    return pd.DataFrame(rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    master = pd.read_csv(MASTER_FILE)
    failures = pd.read_csv(FAILURE_FILE)
    failure_cols = ["A8_FOSA", OXYGEN_DAMAGE] + FAILURE_CAUSES + FAILURE_CATEGORIES
    df = master.merge(failures[failure_cols], on="A8_FOSA", how="left")
    for col in failure_cols:
        if col != "A8_FOSA":
            df[col] = df[col].fillna(0).astype(int)
    df = add_derived(df)

    universes = {
        "all_facilities": df,
        "damage_reporting_facilities": df[df["equipment_damage_binary"] == 1].copy(),
        "oxygen_facilities": df[df["has_any_oxygen"] == 1].copy(),
        "concentrator_facilities": df[df["has_concentrator"] == 1].copy(),
    }
    outcomes = {
        "all_facilities": ["equipment_damage_binary", "has_oxygen_damage"],
        "damage_reporting_facilities": ["has_oxygen_damage"],
        "oxygen_facilities": ["has_oxygen_damage"],
        "concentrator_facilities": ["has_oxygen_damage"],
    }
    binary_predictors = [
        "has_any_oxygen",
        "has_concentrator",
        "has_10l_conc",
        "has_5l_conc",
        "has_multi_conc",
        "has_cylinders",
        "has_psa_internal",
        "has_psa_external",
        "has_other_oxygen",
        "has_multi_oxygen",
        "has_generator",
        "has_grid",
        "has_solar",
        "has_charcoal",
        "reliable_v1_917",
        "reliable_v3_917",
        "I5_tech",
        "Voltage instability / fluctuation",
        "Power cuts / abrupt restoration",
        "Short circuit / burned electronics",
        "Insufficient power / no energy",
        "Lightning / atmospheric discharge",
        "Poor installation",
        "Electrical components / power system",
        "multi_category_damage",
    ]
    categorical_predictors = [
        "province",
        "facility_type",
        "grid_architecture",
        "energy_profile",
        "oxygen_profile",
    ]
    continuous_predictors = [
        "total_concentrators_max",
        "conc_10l_max",
        "conc_5l_max",
        "n_oxygen_sources",
        "n_energy_sources",
        "C1_a_gencount_max",
        "C2_1_gencapac_max",
        "outage_days_median",
        "outage_hours_median",
        "bad_power_days_median",
        "short_outages_median",
        "uptime_v1_reconstructed",
        "grid_cost_median",
        "generator_cost_median",
        "oxygen_cost_median",
        "solar_total_value_median",
        "solar_maintenance_adhoc_median",
        "I2_wtp_median",
    ]

    binary_rows = []
    categorical_rows = []
    continuous_rows = []
    summary_rows = []
    for universe, data in universes.items():
        for outcome in outcomes[universe]:
            summary_rows.append(summaries(data, outcome, universe))
            for predictor in binary_predictors:
                if predictor in data and predictor != outcome:
                    result = odds_ratio(data, predictor, outcome, universe)
                    if result:
                        binary_rows.append(result)
            for predictor in categorical_predictors:
                if predictor in data:
                    result = categorical_test(data, predictor, outcome, universe)
                    if result:
                        categorical_rows.append(result)
            for predictor in continuous_predictors:
                if predictor in data:
                    result = continuous_test(data, predictor, outcome, universe)
                    if result:
                        continuous_rows.append(result)

    predictor_sets = {
        "context": ["province", "facility_type"],
        "oxygen_capacity": [
            "has_concentrator",
            "has_10l_conc",
            "has_5l_conc",
            "has_multi_conc",
            "has_cylinders",
            "n_oxygen_sources",
            "total_concentrators_max",
        ],
        "energy_reliability": [
            "has_grid",
            "has_generator",
            "has_solar",
            "grid_architecture",
            "reliable_v1_917",
            "outage_days_median",
            "outage_hours_median",
            "bad_power_days_median",
        ],
        "operations_cost": [
            "I5_tech",
            "grid_cost_median",
            "generator_cost_median",
            "solar_total_value_median",
            "solar_maintenance_adhoc_median",
            "I2_wtp_median",
        ],
        "combined_without_failure_text": [
            "province",
            "facility_type",
            "has_grid",
            "has_generator",
            "has_solar",
            "grid_architecture",
            "reliable_v1_917",
            "bad_power_days_median",
            "I5_tech",
            "has_10l_conc",
            "has_5l_conc",
            "has_multi_conc",
            "total_concentrators_max",
        ],
        "failure_context_text": FAILURE_CAUSES + ["Electrical components / power system", "multi_category_damage"],
    }
    aucs = []
    for universe, data in universes.items():
        for outcome in outcomes[universe]:
            aucs.append(prediction_auc(data, outcome, predictor_sets, universe))

    binary = pd.DataFrame(binary_rows).sort_values(["outcome", "p_value"])
    categorical = pd.DataFrame(categorical_rows).sort_values(["outcome", "p_value"])
    continuous = pd.DataFrame(continuous_rows).sort_values(["outcome", "p_value"])
    summary = pd.concat(summary_rows, ignore_index=True)
    auc = pd.concat(aucs, ignore_index=True).sort_values(["universe", "outcome", "cv_auc"], ascending=[True, True, False])

    binary.to_csv(OUT / "damage_binary_odds_ratios.csv", index=False)
    categorical.to_csv(OUT / "damage_categorical_tests.csv", index=False)
    continuous.to_csv(OUT / "damage_continuous_tests.csv", index=False)
    summary.to_csv(OUT / "damage_group_summaries.csv", index=False)
    auc.to_csv(OUT / "damage_prediction_auc.csv", index=False)

    print(OUT)
    print("\nTop binary tests")
    print(binary.head(60).to_string(index=False))
    print("\nTop categorical tests")
    print(categorical.head(40).to_string(index=False))
    print("\nTop continuous tests")
    print(continuous.head(60).to_string(index=False))
    print("\nPrediction AUC")
    print(auc.to_string(index=False))


if __name__ == "__main__":
    main()
