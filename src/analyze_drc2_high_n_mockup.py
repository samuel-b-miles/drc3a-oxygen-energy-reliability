#!/usr/bin/env python3
"""Create first-pass high-N DRC2 tables, figures, and association tests."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
import statsmodels.formula.api as smf
from scipy.stats import chi2_contingency, fisher_exact


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "outputs/drc2_facility_master/facility_master.csv"
OUT = ROOT / "outputs/drc2_high_n_mockup"
FIG = OUT / "figures"
TAB = OUT / "tables"
DOCS = ROOT / "docs"


ENERGY_ORDER = [
    "No energy source",
    "Grid",
    "Generator",
    "Solar",
    "Grid + Generator",
    "Grid + Solar",
    "Generator + Solar",
    "Grid + Generator + Solar",
]

OXYGEN_ORDER = [
    "No oxygen source",
    "Concentrator",
    "Cylinders",
    "Other oxygen",
    "Concentrator + Cylinders",
    "Concentrator + Internal PSA",
    "Concentrator + External PSA",
    "Concentrator + Other oxygen",
    "Concentrator + Cylinders + Internal PSA",
    "Concentrator + Cylinders + External PSA",
    "Concentrator + Cylinders + Other oxygen",
]

FACILITY_TYPE_LABELS = {
    1: 'HGR "Hopital General de Reference"',
    2: 'CH "Centre Hospitalier"',
    3: 'CSR "Centre de Sante de Reference"',
    5: 'HP "Hopital Provincial"',
    6: 'CM "Centre Medical"',
}

FACILITY_TYPE_ORDER = [
    'HP "Hopital Provincial"',
    'HGR "Hopital General de Reference"',
    'CH "Centre Hospitalier"',
    'CSR "Centre de Sante de Reference"',
    'CM "Centre Medical"',
]

PROVINCE_LABELS = {
    1: "Nord-Kivu",
    2: "Sud-Kivu",
    3: "Haut Katanga",
}

PROVINCE_ORDER = [
    "Nord-Kivu",
    "Sud-Kivu",
    "Haut Katanga",
]


def pct_table(df: pd.DataFrame, row: str, col: str, order: list[str] | None = None) -> pd.DataFrame:
    tab = pd.crosstab(df[row], df[col], normalize="index").mul(100)
    if order:
        tab = tab.reindex(columns=[c for c in order if c in tab.columns])
    return tab.round(1)


def count_pct(series: pd.Series) -> pd.DataFrame:
    counts = series.value_counts(dropna=False)
    out = pd.DataFrame({"n": counts, "pct": (counts / counts.sum() * 100).round(1)})
    return out.reset_index().rename(columns={"index": series.name or "value"})


def save_table(df: pd.DataFrame, name: str) -> Path:
    path = TAB / f"{name}.csv"
    df.to_csv(path, index=True)
    return path


def plot_stacked_percent(tab: pd.DataFrame, title: str, xlabel: str, output: Path) -> None:
    ax = tab.plot(kind="barh", stacked=True, figsize=(11, 6.5), width=0.82)
    ax.set_title(title, fontsize=14, weight="bold", pad=12)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("")
    ax.legend(
        title="Regime",
        bbox_to_anchor=(1.02, 1),
        loc="upper left",
        fontsize=8,
        title_fontsize=9,
        frameon=False,
    )
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="x", color="#d9d9d9", linewidth=0.7, alpha=0.8)
    plt.tight_layout()
    plt.savefig(output, dpi=250, bbox_inches="tight")
    plt.close()


def plot_energy_gradient(df: pd.DataFrame, output: Path) -> pd.DataFrame:
    grouped = (
        df.groupby("n_energy_sources")
        .agg(
            facilities=("A8_FOSA", "count"),
            has_any_oxygen=("has_any_oxygen", "mean"),
            has_concentrator=("has_concentrator", "mean"),
            has_multi_oxygen=("has_multi_oxygen", "mean"),
            mean_concentrators=("total_concentrators_max", "mean"),
            median_outage_days=("outage_days_median", "median"),
        )
        .reset_index()
    )
    for col in ["has_any_oxygen", "has_concentrator", "has_multi_oxygen"]:
        grouped[col] = grouped[col] * 100

    fig, ax1 = plt.subplots(figsize=(9.5, 6))
    x = grouped["n_energy_sources"].astype(str)
    width = 0.25
    idx = np.arange(len(grouped))
    ax1.bar(idx - width, grouped["has_any_oxygen"], width, label="Any oxygen source", color="#2ca02c")
    ax1.bar(idx, grouped["has_concentrator"], width, label="Concentrator", color="#1f77b4")
    ax1.bar(idx + width, grouped["has_multi_oxygen"], width, label="2+ oxygen sources", color="#ff7f0e")
    ax1.set_ylabel("% of facilities")
    ax1.set_xlabel("Number of reported energy sources")
    ax1.set_xticks(idx, x)
    ax1.set_ylim(0, 100)
    ax1.grid(axis="y", color="#d9d9d9", linewidth=0.7, alpha=0.8)
    ax1.spines[["top", "right"]].set_visible(False)
    ax1.legend(frameon=False, loc="upper left")
    ax1.set_title("Oxygen access by energy-source complexity", fontsize=14, weight="bold", pad=12)
    for i, n in enumerate(grouped["facilities"]):
        ax1.text(i, -8, f"n={n}", ha="center", va="top", fontsize=9)
    plt.tight_layout()
    plt.savefig(output, dpi=250, bbox_inches="tight")
    plt.close()
    return grouped.round(2)


def plot_heatmap(tab: pd.DataFrame, title: str, output: Path) -> None:
    fig, ax = plt.subplots(figsize=(12, 7.5))
    data = tab.values
    im = ax.imshow(data, cmap="YlGnBu", aspect="auto")
    ax.set_xticks(np.arange(tab.shape[1]), tab.columns, rotation=45, ha="right", fontsize=8)
    ax.set_yticks(np.arange(tab.shape[0]), tab.index, fontsize=9)
    ax.set_title(title, fontsize=14, weight="bold", pad=12)
    for i in range(tab.shape[0]):
        for j in range(tab.shape[1]):
            value = data[i, j]
            if value > 0:
                ax.text(j, i, f"{value:.0f}", ha="center", va="center", fontsize=8)
    fig.colorbar(im, ax=ax, label="Facilities")
    plt.tight_layout()
    plt.savefig(output, dpi=250, bbox_inches="tight")
    plt.close()


def labeled_group(series: pd.Series, order: list[str]) -> list[str]:
    counts = series.value_counts()
    return [f"{label} (n={int(counts.get(label, 0))})" for label in order if counts.get(label, 0) > 0]


def add_counts_to_labels(tab: pd.DataFrame, counts: pd.Series) -> pd.DataFrame:
    renamed = tab.copy()
    renamed.index = [f"{idx} (n={int(counts.get(idx, 0))})" for idx in renamed.index]
    return renamed


def plot_type_province_regimes(df: pd.DataFrame, output: Path) -> None:
    energy_colors = {
        "No energy source": "#7f7f7f",
        "Grid": "#2b6cb0",
        "Generator": "#d95f02",
        "Solar": "#1b9e77",
        "Grid + Generator": "#756bb1",
        "Grid + Solar": "#66a61e",
        "Generator + Solar": "#e7298a",
        "Grid + Generator + Solar": "#4d4d4d",
    }
    oxygen_colors = {
        "No oxygen source": "#7f7f7f",
        "Concentrator": "#1f78b4",
        "Cylinders": "#33a02c",
        "Other oxygen": "#b15928",
        "Concentrator + Cylinders": "#6a3d9a",
        "Concentrator + Internal PSA": "#fb9a99",
        "Concentrator + External PSA": "#e31a1c",
        "Concentrator + Other oxygen": "#a6cee3",
        "Concentrator + Cylinders + Internal PSA": "#fdbf6f",
        "Concentrator + Cylinders + External PSA": "#cab2d6",
        "Concentrator + Cylinders + Other oxygen": "#ffff99",
    }

    panels = [
        ("facility_type_label", "energy_profile", ENERGY_ORDER, energy_colors, "Energy regimes by facility type", FACILITY_TYPE_ORDER),
        ("facility_type_label", "oxygen_profile", OXYGEN_ORDER, oxygen_colors, "Oxygen regimes by facility type", FACILITY_TYPE_ORDER),
        ("province_label", "energy_profile", ENERGY_ORDER, energy_colors, "Energy regimes by province", PROVINCE_ORDER),
        ("province_label", "oxygen_profile", OXYGEN_ORDER, oxygen_colors, "Oxygen regimes by province", PROVINCE_ORDER),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(18, 12), constrained_layout=True)
    for ax, (row, col, order, colors, title, row_order) in zip(axes.ravel(), panels):
        tab = pd.crosstab(df[row], df[col], normalize="index").mul(100)
        tab = tab.reindex(index=[x for x in row_order if x in tab.index])
        tab = tab.reindex(columns=[x for x in order if x in tab.columns]).fillna(0)
        tab = add_counts_to_labels(tab, df[row].value_counts())
        y = np.arange(len(tab))
        left = np.zeros(len(tab))
        for category in tab.columns:
            vals = tab[category].values
            ax.barh(y, vals, left=left, color=colors.get(category), label=category, height=0.72)
            left += vals
        ax.set_yticks(y, tab.index)
        ax.set_xlim(0, 100)
        ax.set_xlabel("% of facilities")
        ax.set_title(title, fontsize=14, weight="bold")
        ax.grid(axis="x", color="#d0d0d0", alpha=0.7, linewidth=0.7)
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.invert_yaxis()

    axes[0, 0].legend(title="Energy regime", bbox_to_anchor=(1.02, 1), loc="upper left", frameon=False, fontsize=8, title_fontsize=9)
    axes[1, 0].legend(title="Energy regime", bbox_to_anchor=(1.02, 1), loc="upper left", frameon=False, fontsize=8, title_fontsize=9)
    axes[0, 1].legend(title="Oxygen regime", bbox_to_anchor=(1.02, 1), loc="upper left", frameon=False, fontsize=7, title_fontsize=9)
    axes[1, 1].legend(title="Oxygen regime", bbox_to_anchor=(1.02, 1), loc="upper left", frameon=False, fontsize=7, title_fontsize=9)
    fig.suptitle("DRC2 survey: reported energy and oxygen regimes by facility type and province", fontsize=18, weight="bold")
    fig.savefig(output, dpi=250, bbox_inches="tight")
    plt.close(fig)


def odds_ratio_2x2(table: pd.DataFrame) -> float:
    # Add 0.5 Haldane-Anscombe correction for zero cells.
    values = table.values.astype(float) + 0.5
    if values.shape != (2, 2):
        return np.nan
    return (values[1, 1] * values[0, 0]) / (values[1, 0] * values[0, 1])


def chi_square(row_var: str, col_var: str, df: pd.DataFrame) -> dict:
    tab = pd.crosstab(df[row_var], df[col_var])
    stat, p, dof, expected = chi2_contingency(tab)
    return {
        "test": "chi-square",
        "row_var": row_var,
        "col_var": col_var,
        "chi2": round(float(stat), 3),
        "dof": int(dof),
        "p_value": float(p),
        "n": int(tab.values.sum()),
    }


def binary_or(exposure: str, outcome: str, df: pd.DataFrame) -> dict:
    tab = pd.crosstab(df[exposure].astype(int), df[outcome].astype(int)).reindex(
        index=[0, 1], columns=[0, 1], fill_value=0
    )
    values = tab.values.astype(float)
    corrected = values + 0.5
    log_or = np.log((corrected[1, 1] * corrected[0, 0]) / (corrected[1, 0] * corrected[0, 1]))
    se = np.sqrt((1 / corrected).sum())
    _, p = fisher_exact(values)
    return {
        "exposure": exposure,
        "outcome": outcome,
        "unexposed_no": int(values[0, 0]),
        "unexposed_yes": int(values[0, 1]),
        "exposed_no": int(values[1, 0]),
        "exposed_yes": int(values[1, 1]),
        "odds_ratio": float(np.exp(log_or)),
        "ci_low": float(np.exp(log_or - 1.96 * se)),
        "ci_high": float(np.exp(log_or + 1.96 * se)),
        "fisher_p_value": float(p),
        "n": int(values.sum()),
    }


def fit_logit(formula: str, df: pd.DataFrame, label: str) -> pd.DataFrame:
    model = smf.logit(formula, data=df).fit(disp=False, maxiter=200)
    params = model.params
    conf = model.conf_int()
    out = pd.DataFrame(
        {
            "model": label,
            "term": params.index,
            "odds_ratio": np.exp(params.values),
            "ci_low": np.exp(conf[0].values),
            "ci_high": np.exp(conf[1].values),
            "p_value": model.pvalues.values,
            "n": int(model.nobs),
            "pseudo_r2": model.prsquared,
        }
    )
    return out


def safe_logit(formula: str, df: pd.DataFrame, label: str) -> pd.DataFrame:
    try:
        return fit_logit(formula, df, label)
    except Exception as exc:  # Keep analysis moving; document failure.
        return pd.DataFrame(
            [
                {
                    "model": label,
                    "term": "MODEL_FAILED",
                    "odds_ratio": np.nan,
                    "ci_low": np.nan,
                    "ci_high": np.nan,
                    "p_value": np.nan,
                    "n": len(df),
                    "pseudo_r2": np.nan,
                    "error": str(exc),
                }
            ]
        )


def write_report(paths: dict, association_summary: list[dict], model_rows: pd.DataFrame, df: pd.DataFrame) -> None:
    report = DOCS / "drc2-high-n-mockup.md"
    lines = [
        "# DRC2 High-N Mockup",
        "",
        "This first-pass package uses the deduplicated `facility_master` table: one row per `A8_FOSA` facility. It is suitable for exploration and manuscript design, with the caveat that the Kobo choice labels and facility-key labels should be added before publication-grade tables.",
        "",
        "## Dataset",
        "",
        f"- Facilities: {len(df)}",
        f"- Facilities with any oxygen source: {int(df['has_any_oxygen'].sum())} ({df['has_any_oxygen'].mean()*100:.1f}%)",
        f"- Facilities with concentrators: {int(df['has_concentrator'].sum())} ({df['has_concentrator'].mean()*100:.1f}%)",
        f"- Facilities with 2+ oxygen sources: {int(df['has_multi_oxygen'].sum())} ({df['has_multi_oxygen'].mean()*100:.1f}%)",
        f"- Facilities with 2+ energy sources: {int((df['n_energy_sources'] >= 2).sum())} ({(df['n_energy_sources'] >= 2).mean()*100:.1f}%)",
        "",
        "## Main Tables",
        "",
        f"- Sample profile: `{paths['sample_profile']}`",
        f"- Energy profiles: `{paths['energy_profile']}`",
        f"- Oxygen profiles: `{paths['oxygen_profile']}`",
        f"- Energy by facility type: `{paths['energy_by_type']}`",
        f"- Oxygen by facility type: `{paths['oxygen_by_type']}`",
        f"- Association tests: `{paths['association_tests']}`",
        f"- Logistic models: `{paths['logit_models']}`",
        f"- Binary odds-ratio screen: `{paths['binary_or']}`",
        "",
        "## Figures",
        "",
        f"- Energy regimes by facility type: `{paths['fig_energy_by_type']}`",
        f"- Oxygen regimes by facility type: `{paths['fig_oxygen_by_type']}`",
        f"- Oxygen access by energy-source complexity: `{paths['fig_energy_gradient']}`",
        f"- Energy regime x oxygen regime heatmap: `{paths['fig_heatmap']}`",
        "",
        "## Association Tests",
        "",
        "| Row variable | Column variable | chi-square | df | p-value | n |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for item in association_summary:
        lines.append(
            f"| `{item['row_var']}` | `{item['col_var']}` | {item['chi2']} | {item['dof']} | {item['p_value']:.3g} | {item['n']} |"
        )

    lines.extend(
        [
            "",
            "## First Interpretation",
            "",
            "The descriptive results should be read as facility-regime evidence. Energy-source complexity, energy profile, and grid architecture are visibly patterned with oxygen access, but this is not causal evidence. The association models test whether the relationship survives simple adjustment for facility type and province codes.",
            "",
            "The key DRC3a move is to use this high-N package to show that oxygen access is patterned by energy regime, then use the high-T case work to show why cross-sectional source categories are incomplete without longitudinal voltage, outage, generator, load, and human-operation evidence.",
            "",
            "## Caveats Before Manuscript Use",
            "",
            "- Province and facility-type values are still coded because choice-list labels were not available locally.",
            "- Facility-master reconciliation uses `any yes` for binary infrastructure presence and median/max/latest summaries for count/cost/reliability variables.",
            "- Cost variables need currency and outlier review before substantive claims.",
            "- Two adjusted logistic models failed in this first pass, likely because sparse coded province/type cells create separation; use the binary odds-ratio screen and chi-square tests as the current reliable association layer.",
            "- Regression language should remain associational.",
            "",
        ]
    )
    report.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)
    TAB.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(exist_ok=True)

    df = pd.read_csv(INPUT)
    df["has_any_oxygen"] = (df["n_oxygen_sources"] > 0).astype(int)
    df["has_multi_oxygen"] = (df["n_oxygen_sources"] >= 2).astype(int)
    df["has_psa_any"] = (
        (df["has_psa_internal"].fillna(0) == 1)
        | (df["has_psa_external"].fillna(0) == 1)
    ).astype(int)
    df["facility_type_code"] = df["A7_type"].astype("category")
    df["province_code"] = df["A5_province"].astype("category")
    df["facility_type_label"] = df["A7_type"].map(FACILITY_TYPE_LABELS)
    df["province_label"] = df["A5_province"].map(PROVINCE_LABELS)
    df["two_plus_energy_sources"] = (df["n_energy_sources"] >= 2).astype(int)
    df["three_energy_sources"] = (df["n_energy_sources"] == 3).astype(int)
    df["grid_plus_backup"] = (
        (df["has_grid"].fillna(0) == 1)
        & ((df["has_generator"].fillna(0) == 1) | (df["has_solar"].fillna(0) == 1))
    ).astype(int)

    # Core tables.
    sample_profile = pd.DataFrame(
        {
            "metric": [
                "facilities",
                "any_oxygen_source",
                "has_concentrator",
                "has_multi_oxygen",
                "has_grid",
                "has_generator",
                "has_solar",
                "two_plus_energy_sources",
                "median_outage_days",
                "median_outage_hours",
            ],
            "value": [
                len(df),
                int(df["has_any_oxygen"].sum()),
                int(df["has_concentrator"].sum()),
                int(df["has_multi_oxygen"].sum()),
                int(df["has_grid"].sum()),
                int(df["has_generator"].sum()),
                int(df["has_solar"].sum()),
                int((df["n_energy_sources"] >= 2).sum()),
                df["outage_days_median"].median(),
                df["outage_hours_median"].median(),
            ],
            "pct_or_stat": [
                "",
                round(df["has_any_oxygen"].mean() * 100, 1),
                round(df["has_concentrator"].mean() * 100, 1),
                round(df["has_multi_oxygen"].mean() * 100, 1),
                round(df["has_grid"].mean() * 100, 1),
                round(df["has_generator"].mean() * 100, 1),
                round(df["has_solar"].mean() * 100, 1),
                round((df["n_energy_sources"] >= 2).mean() * 100, 1),
                "median",
                "median",
            ],
        }
    )
    paths: dict[str, str] = {}
    paths["sample_profile"] = str(TAB / "table_1_sample_profile.csv")
    sample_profile.to_csv(paths["sample_profile"], index=False)

    energy_profile = count_pct(df["energy_profile"])
    paths["energy_profile"] = str(TAB / "table_2_energy_profiles.csv")
    energy_profile.to_csv(paths["energy_profile"], index=False)

    oxygen_profile = count_pct(df["oxygen_profile"])
    paths["oxygen_profile"] = str(TAB / "table_3_oxygen_profiles.csv")
    oxygen_profile.to_csv(paths["oxygen_profile"], index=False)

    energy_by_type = pct_table(df, "A7_type", "energy_profile", ENERGY_ORDER)
    oxygen_by_type = pct_table(df, "A7_type", "oxygen_profile", OXYGEN_ORDER)
    paths["energy_by_type"] = str(save_table(energy_by_type, "table_4_energy_profile_by_facility_type_code"))
    paths["oxygen_by_type"] = str(save_table(oxygen_by_type, "table_5_oxygen_profile_by_facility_type_code"))

    # Figures.
    paths["fig_energy_by_type"] = str(FIG / "fig_1_energy_regimes_by_facility_type.png")
    plot_stacked_percent(
        energy_by_type,
        "Energy regimes across facility-type codes",
        "% of facilities within facility-type code",
        Path(paths["fig_energy_by_type"]),
    )
    paths["fig_oxygen_by_type"] = str(FIG / "fig_2_oxygen_regimes_by_facility_type.png")
    plot_stacked_percent(
        oxygen_by_type,
        "Oxygen regimes across facility-type codes",
        "% of facilities within facility-type code",
        Path(paths["fig_oxygen_by_type"]),
    )
    paths["fig_energy_gradient"] = str(FIG / "fig_3_oxygen_access_by_energy_complexity.png")
    energy_gradient = plot_energy_gradient(df, Path(paths["fig_energy_gradient"]))
    energy_gradient.to_csv(TAB / "table_6_oxygen_access_by_energy_complexity.csv", index=False)

    heat = pd.crosstab(df["energy_profile"], df["oxygen_profile"])
    heat = heat.reindex(index=[x for x in ENERGY_ORDER if x in heat.index])
    heat = heat.reindex(columns=[x for x in OXYGEN_ORDER if x in heat.columns])
    paths["fig_heatmap"] = str(FIG / "fig_4_energy_oxygen_regime_heatmap.png")
    plot_heatmap(heat, "Energy regime x oxygen regime (facility counts)", Path(paths["fig_heatmap"]))
    heat.to_csv(TAB / "table_7_energy_oxygen_regime_counts.csv")

    paths["fig_type_province_regimes"] = str(FIG / "fig_5_energy_oxygen_by_type_and_province.png")
    plot_type_province_regimes(df, Path(paths["fig_type_province_regimes"]))

    # Association tests.
    association_summary = [
        chi_square("n_energy_sources", "has_any_oxygen", df),
        chi_square("n_energy_sources", "has_concentrator", df),
        chi_square("n_energy_sources", "has_multi_oxygen", df),
        chi_square("energy_profile", "oxygen_profile", df),
        chi_square("grid_architecture", "has_any_oxygen", df),
        chi_square("has_generator", "has_psa_any", df),
    ]
    assoc_df = pd.DataFrame(association_summary)
    paths["association_tests"] = str(TAB / "table_8_association_tests.csv")
    assoc_df.to_csv(paths["association_tests"], index=False)

    # Logistic associations, adjusted for coded facility type and province.
    model_df = df.dropna(subset=["A5_province", "A7_type", "n_energy_sources"]).copy()
    model_results = pd.concat(
        [
            safe_logit(
                "has_any_oxygen ~ C(n_energy_sources) + C(A7_type) + C(A5_province)",
                model_df,
                "Any oxygen ~ energy complexity + facility type + province",
            ),
            safe_logit(
                "has_concentrator ~ C(n_energy_sources) + C(A7_type) + C(A5_province)",
                model_df,
                "Concentrator ~ energy complexity + facility type + province",
            ),
            safe_logit(
                "has_multi_oxygen ~ C(n_energy_sources) + C(A7_type) + C(A5_province)",
                model_df,
                "Multi-source oxygen ~ energy complexity + facility type + province",
            ),
            safe_logit(
                "has_psa_any ~ has_generator + has_grid + has_solar + C(A7_type) + C(A5_province)",
                model_df,
                "PSA-linked oxygen ~ energy sources + facility type + province",
            ),
        ],
        ignore_index=True,
    )
    paths["logit_models"] = str(TAB / "table_9_logistic_models.csv")
    model_results.to_csv(paths["logit_models"], index=False)

    binary_rows = []
    for exposure in [
        "has_grid",
        "has_generator",
        "has_solar",
        "two_plus_energy_sources",
        "three_energy_sources",
        "grid_plus_backup",
    ]:
        for outcome in ["has_any_oxygen", "has_concentrator", "has_multi_oxygen", "has_psa_any"]:
            binary_rows.append(binary_or(exposure, outcome, df))
    binary_or_df = pd.DataFrame(binary_rows)
    paths["binary_or"] = str(TAB / "table_10_binary_odds_ratio_screen.csv")
    binary_or_df.to_csv(paths["binary_or"], index=False)

    write_report(paths, association_summary, model_results, df)

    summary = {
        "input": str(INPUT),
        "facilities": int(len(df)),
        "outputs": paths,
        "tables_dir": str(TAB),
        "figures_dir": str(FIG),
        "report": str(DOCS / "drc2-high-n-mockup.md"),
    }
    (OUT / "high_n_mockup_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
