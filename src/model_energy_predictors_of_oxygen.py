#!/usr/bin/env python3
"""Explore whether DRC2 energy variables predict oxygen outcomes."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency, fisher_exact, kruskal
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "outputs/drc2_facility_master/facility_master.csv"
UPTIME_INPUT = ROOT / "outputs/drc2_uptime/tables/facility_master_with_reconstructed_uptime.csv"
OUT = ROOT / "outputs/drc2_energy_predictors"
TAB = OUT / "tables"


FACILITY_TYPE_LABELS = {
    1: "HGR",
    2: "CH",
    3: "CSR",
    5: "HP",
    6: "CM",
}
PROVINCE_LABELS = {
    1: "Nord-Kivu",
    2: "Sud-Kivu",
    3: "Haut Katanga",
}


def odds_ratio(exposure: pd.Series, outcome: pd.Series) -> dict:
    tab = pd.crosstab(exposure.astype(int), outcome.astype(int)).reindex(index=[0, 1], columns=[0, 1], fill_value=0)
    values = tab.values.astype(float)
    corrected = values + 0.5
    log_or = np.log((corrected[1, 1] * corrected[0, 0]) / (corrected[1, 0] * corrected[0, 1]))
    se = np.sqrt((1 / corrected).sum())
    _, p = fisher_exact(values)
    return {
        "unexposed_no": int(values[0, 0]),
        "unexposed_yes": int(values[0, 1]),
        "exposed_no": int(values[1, 0]),
        "exposed_yes": int(values[1, 1]),
        "odds_ratio": float(np.exp(log_or)),
        "ci_low": float(np.exp(log_or - 1.96 * se)),
        "ci_high": float(np.exp(log_or + 1.96 * se)),
        "p_value": float(p),
        "n": int(values.sum()),
    }


def chi_square(row: pd.Series, col: pd.Series) -> dict:
    tab = pd.crosstab(row, col)
    stat, p, dof, expected = chi2_contingency(tab)
    return {"chi2": float(stat), "dof": int(dof), "p_value": float(p), "n": int(tab.values.sum())}


def cv_auc(df: pd.DataFrame, outcome: str, predictors: list[str], numeric: list[str], categorical: list[str]) -> dict:
    model_df = df[[outcome] + predictors].copy()
    model_df = model_df[model_df[outcome].notna()]
    y = model_df[outcome].astype(int)
    if y.nunique() < 2 or y.value_counts().min() < 10:
        return {"outcome": outcome, "predictor_set": " + ".join(predictors), "cv_auc": np.nan, "n": len(model_df), "note": "too few events"}

    pre = ColumnTransformer(
        transformers=[
            ("num", Pipeline([("imputer", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), numeric),
            ("cat", Pipeline([("imputer", SimpleImputer(strategy="most_frequent")), ("onehot", OneHotEncoder(handle_unknown="ignore"))]), categorical),
        ],
        remainder="drop",
    )
    clf = Pipeline(
        [
            ("pre", pre),
            ("model", LogisticRegression(max_iter=2000, penalty="l2", C=1.0, class_weight="balanced")),
        ]
    )
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=20260727)
    probs = cross_val_predict(clf, model_df[predictors], y, cv=cv, method="predict_proba")[:, 1]
    return {"outcome": outcome, "predictor_set": " + ".join(predictors), "cv_auc": float(roc_auc_score(y, probs)), "n": len(model_df), "note": ""}


def fit_coefficients(df: pd.DataFrame, outcome: str, predictors: list[str], numeric: list[str], categorical: list[str]) -> pd.DataFrame:
    model_df = df[[outcome] + predictors].copy()
    model_df = model_df[model_df[outcome].notna()]
    y = model_df[outcome].astype(int)
    if y.nunique() < 2:
        return pd.DataFrame()
    pre = ColumnTransformer(
        transformers=[
            ("num", Pipeline([("imputer", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), numeric),
            ("cat", Pipeline([("imputer", SimpleImputer(strategy="most_frequent")), ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))]), categorical),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )
    x = pre.fit_transform(model_df[predictors])
    names = pre.get_feature_names_out()
    clf = LogisticRegression(max_iter=2000, penalty="l2", C=1.0, class_weight="balanced")
    clf.fit(x, y)
    return pd.DataFrame(
        {
            "outcome": outcome,
            "term": names,
            "coef": clf.coef_[0],
            "odds_ratio_per_scaled_or_indicator": np.exp(clf.coef_[0]),
        }
    ).sort_values("coef", key=lambda s: s.abs(), ascending=False)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    TAB.mkdir(parents=True, exist_ok=True)
    if UPTIME_INPUT.exists():
        df = pd.read_csv(UPTIME_INPUT)
    else:
        df = pd.read_csv(INPUT)
    df["facility_type"] = df["A7_type"].map(FACILITY_TYPE_LABELS)
    df["province"] = df["A5_province"].map(PROVINCE_LABELS)
    df["has_any_oxygen"] = (df["n_oxygen_sources"] > 0).astype(int)
    df["has_multi_oxygen"] = (df["n_oxygen_sources"] >= 2).astype(int)
    df["has_psa_any"] = ((df["has_psa_internal"] == 1) | (df["has_psa_external"] == 1)).astype(int)
    df["concentrator_no_cylinder"] = ((df["has_concentrator"] == 1) & (df["has_cylinders"] == 0)).astype(int)
    df["cylinder_any"] = (df["has_cylinders"] == 1).astype(int)
    df["cylinder_no_concentrator"] = ((df["has_cylinders"] == 1) & (df["has_concentrator"] == 0)).astype(int)
    df["concentrator_vs_cylinder_among_oxygen"] = np.where(
        (df["has_concentrator"] == 1) | (df["has_cylinders"] == 1),
        df["has_concentrator"].astype(int),
        np.nan,
    )
    df["two_plus_energy_sources"] = (df["n_energy_sources"] >= 2).astype(int)
    df["three_energy_sources"] = (df["n_energy_sources"] == 3).astype(int)
    df["grid_plus_backup"] = ((df["has_grid"] == 1) & ((df["has_generator"] == 1) | (df["has_solar"] == 1))).astype(int)
    df["bad_power_high"] = (df["bad_power_days_median"] > df["bad_power_days_median"].median()).astype(int)
    df["outage_hours_high"] = (df["outage_hours_median"] > df["outage_hours_median"].median()).astype(int)

    outcomes = [
        "has_any_oxygen",
        "has_concentrator",
        "has_multi_oxygen",
        "has_psa_any",
        "cylinder_any",
        "concentrator_no_cylinder",
        "concentrator_vs_cylinder_among_oxygen",
        "equipment_damage_binary",
    ]
    exposures = [
        "has_grid",
        "has_generator",
        "has_solar",
        "two_plus_energy_sources",
        "three_energy_sources",
        "grid_plus_backup",
        "bad_power_high",
        "outage_hours_high",
        "short_outages_median",
    ]
    if "reliable_v1_917" in df.columns:
        exposures.extend(["reliable_v1_917", "reliable_v3_917"])
    rows = []
    for exposure in exposures:
        for outcome in outcomes:
            tmp = df[[exposure, outcome]].dropna()
            if tmp[exposure].nunique() == 2 and tmp[outcome].nunique() == 2:
                row = odds_ratio(tmp[exposure], tmp[outcome])
                row.update({"exposure": exposure, "outcome": outcome})
                rows.append(row)
    or_df = pd.DataFrame(rows)
    or_df.to_csv(TAB / "binary_energy_predictor_odds_ratios.csv", index=False)

    chi_rows = []
    for row_var in ["n_energy_sources", "energy_profile", "grid_architecture"]:
        for outcome in outcomes:
            tmp = df[[row_var, outcome]].dropna()
            if tmp[row_var].nunique() > 1 and tmp[outcome].nunique() > 1:
                row = chi_square(tmp[row_var], tmp[outcome])
                row.update({"row_var": row_var, "outcome": outcome})
                chi_rows.append(row)
    pd.DataFrame(chi_rows).to_csv(TAB / "categorical_energy_predictor_tests.csv", index=False)

    # Reliability by oxygen modality, for the "grid reliability predicts mix" hypothesis.
    reliability_rows = []
    for metric in ["outage_days_median", "outage_hours_median", "bad_power_days_median"]:
        for group in ["oxygen_profile", "grid_architecture", "energy_profile"]:
            tmp = df[[metric, group]].dropna()
            samples = [g[metric].values for _, g in tmp.groupby(group) if len(g) >= 3]
            if len(samples) > 1:
                stat, p = kruskal(*samples)
                reliability_rows.append({"metric": metric, "group": group, "kruskal_stat": float(stat), "p_value": float(p), "n": len(tmp)})
    pd.DataFrame(reliability_rows).to_csv(TAB / "reliability_by_regime_tests.csv", index=False)

    summary_tabs = {}
    summary_tabs["oxygen_by_generator_solar_grid"] = pd.concat(
        {
            "generator": df.groupby("has_generator")[["has_any_oxygen", "has_concentrator", "has_cylinders", "has_multi_oxygen", "has_psa_any"]].mean().mul(100),
            "solar": df.groupby("has_solar")[["has_any_oxygen", "has_concentrator", "has_cylinders", "has_multi_oxygen", "has_psa_any"]].mean().mul(100),
            "grid": df.groupby("has_grid")[["has_any_oxygen", "has_concentrator", "has_cylinders", "has_multi_oxygen", "has_psa_any"]].mean().mul(100),
        }
    )
    summary_tabs["oxygen_by_generator_solar_grid"].round(1).to_csv(TAB / "oxygen_by_generator_solar_grid_percent.csv")
    pd.crosstab(df["grid_architecture"], df["oxygen_profile"], normalize="index").mul(100).round(1).to_csv(
        TAB / "oxygen_profile_by_grid_architecture_percent.csv"
    )
    df.groupby("oxygen_profile")[["outage_days_median", "outage_hours_median", "bad_power_days_median"]].median().round(2).to_csv(
        TAB / "reliability_medians_by_oxygen_profile.csv"
    )

    predictor_sets = [
        (
            "source_flags",
            ["has_grid", "has_generator", "has_solar"],
            ["has_grid", "has_generator", "has_solar"],
            [],
        ),
        (
            "source_flags_plus_reliability",
            ["has_grid", "has_generator", "has_solar", "outage_days_median", "outage_hours_median", "bad_power_days_median", "short_outages_median"],
            ["has_grid", "has_generator", "has_solar", "outage_days_median", "outage_hours_median", "bad_power_days_median", "short_outages_median"],
            [],
        ),
        (
            "source_flags_reliability_context",
            ["has_grid", "has_generator", "has_solar", "outage_days_median", "outage_hours_median", "bad_power_days_median", "short_outages_median", "facility_type", "province"],
            ["has_grid", "has_generator", "has_solar", "outage_days_median", "outage_hours_median", "bad_power_days_median", "short_outages_median"],
            ["facility_type", "province"],
        ),
        (
            "energy_profile_context",
            ["energy_profile", "grid_architecture", "facility_type", "province"],
            [],
            ["energy_profile", "grid_architecture", "facility_type", "province"],
        ),
    ]
    if "uptime_v1_reconstructed" in df.columns:
        predictor_sets.append(
            (
                "source_flags_uptime_context",
                [
                    "has_grid",
                    "has_generator",
                    "has_solar",
                    "uptime_v1_reconstructed",
                    "reliable_v1_917",
                    "facility_type",
                    "province",
                ],
                ["has_grid", "has_generator", "has_solar", "uptime_v1_reconstructed", "reliable_v1_917"],
                ["facility_type", "province"],
            )
        )
    auc_rows = []
    coef_rows = []
    for label, predictors, numeric, categorical in predictor_sets:
        for outcome in outcomes:
            if outcome == "has_psa_any" and int(df[outcome].sum()) < 25:
                continue
            auc = cv_auc(df, outcome, predictors, numeric, categorical)
            auc["predictor_set_label"] = label
            auc_rows.append(auc)
            coef = fit_coefficients(df, outcome, predictors, numeric, categorical)
            if not coef.empty:
                coef.insert(1, "predictor_set_label", label)
                coef_rows.append(coef)
    pd.DataFrame(auc_rows).to_csv(TAB / "cross_validated_prediction_auc.csv", index=False)
    pd.concat(coef_rows, ignore_index=True).to_csv(TAB / "regularized_logistic_coefficients.csv", index=False)

    print("Wrote", TAB)
    print("Top odds ratios:")
    print(
        or_df[or_df["outcome"].isin(["has_any_oxygen", "has_concentrator", "has_multi_oxygen", "cylinder_any", "equipment_damage_binary"])]
        .sort_values("p_value")
        .head(20)[["exposure", "outcome", "odds_ratio", "ci_low", "ci_high", "p_value", "n"]]
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
