#!/usr/bin/env python3
"""Audit solar panel/capacity fields and compare with first-generator capacity."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu, spearmanr


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "outputs/drc2_facility_master/facility_master.csv"
OUT = ROOT / "outputs/drc3a_solar_generator_audit"
FIG = OUT / "figures"
TAB = OUT / "tables"


PROVINCE_LABELS = {
    1: "Nord-Kivu",
    2: "Sud-Kivu",
    3: "Haut-Katanga",
}

FACILITY_TYPE_LABELS = {
    1: "HGR",
    2: "CH",
    3: "CSR",
    5: "HP",
    6: "CM",
}


def stats(series: pd.Series) -> dict[str, float]:
    s = pd.to_numeric(series, errors="coerce").dropna()
    if s.empty:
        return {
            "n": 0,
            "mean": np.nan,
            "median": np.nan,
            "q25": np.nan,
            "q75": np.nan,
            "p90": np.nan,
            "max": np.nan,
        }
    return {
        "n": int(s.size),
        "mean": float(s.mean()),
        "median": float(s.median()),
        "q25": float(s.quantile(0.25)),
        "q75": float(s.quantile(0.75)),
        "p90": float(s.quantile(0.90)),
        "max": float(s.max()),
    }


def fr_num(value: float, digits: int = 1) -> str:
    if pd.isna(value):
        return "NA"
    return f"{value:.{digits}f}".replace(".", ",")


def infer_solar_capacity_kwp(raw: float, panels: float) -> tuple[float, str, float]:
    """Infer solar kWp from a raw field that mixes W and kW-like responses.

    A record is retained only when the raw value can imply a plausible module size
    between 50 W and 750 W per reported panel. Values below 100 are first treated
    as kW; values at/above 100 are first treated as W. A fallback interpretation
    is accepted if the preferred interpretation is physically implausible.
    """
    if pd.isna(raw) or pd.isna(panels) or raw <= 0 or panels <= 0:
        return np.nan, "missing_or_nonpositive", np.nan

    candidates: list[tuple[str, float, float]] = []

    kwp_if_kw = raw
    watts_per_panel_if_kw = raw * 1000 / panels
    if 50 <= watts_per_panel_if_kw <= 750 and 0.05 <= kwp_if_kw <= 500:
        candidates.append(("raw_as_kw", kwp_if_kw, watts_per_panel_if_kw))

    kwp_if_w = raw / 1000
    watts_per_panel_if_w = raw / panels
    if 50 <= watts_per_panel_if_w <= 750 and 0.05 <= kwp_if_w <= 500:
        candidates.append(("raw_as_w", kwp_if_w, watts_per_panel_if_w))

    if not candidates:
        return np.nan, "implausible_panel_capacity_ratio", np.nan

    preferred = "raw_as_w" if raw >= 100 else "raw_as_kw"
    for flag, kwp, watts_per_panel in candidates:
        if flag == preferred:
            return kwp, flag, watts_per_panel

    flag, kwp, watts_per_panel = candidates[0]
    return kwp, f"{flag}_fallback", watts_per_panel


def clean_generator_kva(raw: float) -> tuple[float, str]:
    """Clean first-generator capacity.

    Values are nominally kVA. Sub-1 kVA values are excluded for a
    health-facility first generator. Very large values between 500 and 10,000
    are treated as VA/W-like entries and divided by 1,000. Larger values are
    excluded.
    """
    if pd.isna(raw) or raw <= 0:
        return np.nan, "missing_or_nonpositive"
    if raw < 1:
        return np.nan, "implausible_low"
    if 500 < raw <= 10_000:
        return raw / 1000, "raw_as_va_or_w"
    if raw > 10_000:
        return np.nan, "implausible_high"
    if raw >= 100:
        return raw, "raw_as_kva_large"
    return raw, "raw_as_kva"


def add_clean_fields(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["province"] = out["A5_province"].map(PROVINCE_LABELS)
    out["facility_type"] = out["A7_type"].map(FACILITY_TYPE_LABELS)

    out["solar_panel_count_raw"] = pd.to_numeric(out["D3_solar_panel_median"], errors="coerce")
    out["solar_panel_count_clean"] = np.where(
        (out["has_solar"] == 1)
        & (out["solar_panel_count_raw"] > 0)
        & (out["solar_panel_count_raw"] <= 500)
        & (out["D3_solar_panel_conflict"] == 0),
        out["solar_panel_count_raw"],
        np.nan,
    )

    cap_results = out.apply(
        lambda row: infer_solar_capacity_kwp(
            pd.to_numeric(row["D4_solar_capac_median"], errors="coerce"),
            pd.to_numeric(row["D3_solar_panel_median"], errors="coerce"),
        ),
        axis=1,
        result_type="expand",
    )
    out["solar_capacity_kwp_inferred"] = cap_results[0]
    out["solar_capacity_unit_inferred"] = cap_results[1]
    out["solar_capacity_watts_per_panel"] = cap_results[2]
    out["solar_capacity_kwp_clear"] = np.where(
        (out["has_solar"] == 1)
        & (out["D3_solar_panel_conflict"] == 0)
        & (out["D4_solar_capac_conflict"] == 0),
        out["solar_capacity_kwp_inferred"],
        np.nan,
    )

    gen_results = out.apply(
        lambda row: clean_generator_kva(pd.to_numeric(row["C2_1_gencapac_median"], errors="coerce")),
        axis=1,
        result_type="expand",
    )
    out["gen1_capacity_kva_clean"] = gen_results[0]
    out["gen1_capacity_unit_flag"] = gen_results[1]
    out["gen1_capacity_kva_clear"] = np.where(
        (out["has_generator"] == 1)
        & (out["C2_1_gencapac_conflict"] == 0),
        out["gen1_capacity_kva_clean"],
        np.nan,
    )

    out["has_clean_solar_and_generator_capacity"] = (
        out["solar_capacity_kwp_clear"].notna() & out["gen1_capacity_kva_clear"].notna()
    )
    out["solar_kwp_to_gen1_kva_ratio"] = out["solar_capacity_kwp_clear"] / out["gen1_capacity_kva_clear"]
    return out


def write_summary_tables(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    rows = [
        {"metric": "facilities", "value": len(df)},
        {"metric": "has_solar", "value": int(df["has_solar"].sum())},
        {"metric": "has_generator", "value": int(df["has_generator"].sum())},
        {"metric": "has_solar_and_generator", "value": int(((df["has_solar"] == 1) & (df["has_generator"] == 1)).sum())},
        {"metric": "solar_panel_count_nonmissing", "value": int(df["D3_solar_panel_median"].notna().sum())},
        {"metric": "solar_panel_count_clear", "value": int(df["solar_panel_count_clean"].notna().sum())},
        {"metric": "solar_capacity_raw_nonmissing", "value": int(df["D4_solar_capac_median"].notna().sum())},
        {"metric": "solar_capacity_clear", "value": int(df["solar_capacity_kwp_clear"].notna().sum())},
        {"metric": "gen1_capacity_raw_nonmissing", "value": int(df["C2_1_gencapac_median"].notna().sum())},
        {"metric": "gen1_capacity_clear", "value": int(df["gen1_capacity_kva_clear"].notna().sum())},
        {"metric": "paired_clean_solar_capacity_and_gen1_capacity", "value": int(df["has_clean_solar_and_generator_capacity"].sum())},
    ]
    audit_summary = pd.DataFrame(rows)
    audit_summary.to_csv(TAB / "audit_retention_summary.csv", index=False)

    stat_rows = []
    for label, col in [
        ("Solar panels, clear count", "solar_panel_count_clean"),
        ("Solar capacity, inferred clean kWp", "solar_capacity_kwp_clear"),
        ("First generator capacity, clean kVA", "gen1_capacity_kva_clear"),
    ]:
        stat_rows.append({"measure": label, **stats(df[col])})
    distribution_summary = pd.DataFrame(stat_rows)
    distribution_summary.to_csv(TAB / "capacity_distribution_summary.csv", index=False)

    flag_tables = {
        "solar_capacity_unit_flags": df.loc[df["has_solar"] == 1, "solar_capacity_unit_inferred"].value_counts(dropna=False).rename_axis("flag").reset_index(name="facilities"),
        "gen1_capacity_unit_flags": df.loc[df["has_generator"] == 1, "gen1_capacity_unit_flag"].value_counts(dropna=False).rename_axis("flag").reset_index(name="facilities"),
    }
    for name, table in flag_tables.items():
        table.to_csv(TAB / f"{name}.csv", index=False)

    group_rows = []
    for group_name, group_col, levels in [
        ("province", "province", ["Nord-Kivu", "Sud-Kivu", "Haut-Katanga"]),
        ("facility_type", "facility_type", ["HP", "HGR", "CH", "CSR", "CM"]),
        ("generator_presence", "has_generator", [0, 1]),
    ]:
        for level in levels:
            sub = df.loc[df[group_col] == level]
            row = {
                "group": group_name,
                "level": level,
                "n_facilities": int(len(sub)),
                "has_solar_pct": float((sub["has_solar"] == 1).mean() * 100) if len(sub) else np.nan,
                "has_generator_pct": float((sub["has_generator"] == 1).mean() * 100) if len(sub) else np.nan,
                "solar_panel_count_clear_n": int(sub["solar_panel_count_clean"].notna().sum()),
                "solar_panel_count_clear_median": stats(sub["solar_panel_count_clean"])["median"],
                "solar_capacity_raw_n": int(sub["D4_solar_capac_median"].notna().sum()),
                "solar_capacity_raw_positive_n": int((sub["D4_solar_capac_median"] > 0).sum()),
                "solar_capacity_kwp_clear_n": int(sub["solar_capacity_kwp_clear"].notna().sum()),
                "solar_capacity_kwp_clear_median": stats(sub["solar_capacity_kwp_clear"])["median"],
                "gen1_capacity_kva_clear_n": int(sub["gen1_capacity_kva_clear"].notna().sum()),
                "gen1_capacity_kva_clear_median": stats(sub["gen1_capacity_kva_clear"])["median"],
            }
            group_rows.append(row)
    group_summary = pd.DataFrame(group_rows)
    group_summary.to_csv(TAB / "capacity_summary_by_group.csv", index=False)

    paired = df.loc[df["has_clean_solar_and_generator_capacity"]].copy()
    paired[
        [
            "A8_FOSA",
            "province",
            "facility_type",
            "energy_profile",
            "solar_panel_count_clean",
            "D4_solar_capac_median",
            "solar_capacity_kwp_clear",
            "solar_capacity_unit_inferred",
            "solar_capacity_watts_per_panel",
            "C1_a_gencount_median",
            "C2_1_gencapac_median",
            "gen1_capacity_kva_clear",
            "gen1_capacity_unit_flag",
            "solar_kwp_to_gen1_kva_ratio",
        ]
    ].sort_values("solar_capacity_kwp_clear", ascending=False).to_csv(TAB / "paired_clean_solar_generator_capacity.csv", index=False)

    outliers = df.loc[
        (df["D4_solar_capac_median"].notna() & df["solar_capacity_kwp_clear"].isna())
        | (df["C2_1_gencapac_median"].notna() & df["gen1_capacity_kva_clear"].isna())
        | (df["solar_panel_count_clean"].notna() & (df["solar_panel_count_clean"] > 100))
        | (df["gen1_capacity_kva_clear"].notna() & (df["gen1_capacity_kva_clear"] >= 100)),
        [
            "A8_FOSA",
            "province",
            "facility_type",
            "has_solar",
            "D3_solar_panel_median",
            "D3_solar_panel_conflict",
            "D4_solar_capac_median",
            "D4_solar_capac_conflict",
            "solar_capacity_kwp_clear",
            "solar_capacity_unit_inferred",
            "solar_capacity_watts_per_panel",
            "has_generator",
            "C2_1_gencapac_median",
            "C2_1_gencapac_conflict",
            "gen1_capacity_kva_clear",
            "gen1_capacity_unit_flag",
        ],
    ].sort_values(["solar_capacity_unit_inferred", "D4_solar_capac_median"], na_position="last")
    outliers.to_csv(TAB / "capacity_records_to_review.csv", index=False)

    clean_cols = [
        "A8_FOSA",
        "province",
        "facility_type",
        "has_solar",
        "has_generator",
        "energy_profile",
        "D3_solar_panel_median",
        "D3_solar_panel_conflict",
        "solar_panel_count_clean",
        "D4_solar_capac_median",
        "D4_solar_capac_conflict",
        "solar_capacity_kwp_clear",
        "solar_capacity_unit_inferred",
        "solar_capacity_watts_per_panel",
        "C1_a_gencount_median",
        "C2_1_gencapac_median",
        "C2_1_gencapac_conflict",
        "gen1_capacity_kva_clear",
        "gen1_capacity_unit_flag",
        "solar_kwp_to_gen1_kva_ratio",
    ]
    df[clean_cols].to_csv(TAB / "facility_solar_generator_capacity_clean.csv", index=False)

    return {
        "audit_summary": audit_summary,
        "distribution_summary": distribution_summary,
        "group_summary": group_summary,
        "paired": paired,
        **flag_tables,
    }


def test_rows(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    panels_gen = df.loc[(df["has_generator"] == 1) & df["solar_panel_count_clean"].notna(), "solar_panel_count_clean"]
    panels_no_gen = df.loc[(df["has_generator"] == 0) & df["solar_panel_count_clean"].notna(), "solar_panel_count_clean"]
    if len(panels_gen) and len(panels_no_gen):
        test = mannwhitneyu(panels_gen, panels_no_gen, alternative="two-sided")
        rows.append(
            {
                "test": "Mann-Whitney U",
                "comparison": "solar panel count by generator presence",
                "n_generator": len(panels_gen),
                "median_generator": panels_gen.median(),
                "n_no_generator": len(panels_no_gen),
                "median_no_generator": panels_no_gen.median(),
                "statistic": float(test.statistic),
                "p_value": float(test.pvalue),
            }
        )

    solar_gen = df.loc[(df["has_generator"] == 1) & df["solar_capacity_kwp_clear"].notna(), "solar_capacity_kwp_clear"]
    solar_no_gen = df.loc[(df["has_generator"] == 0) & df["solar_capacity_kwp_clear"].notna(), "solar_capacity_kwp_clear"]
    if len(solar_gen) and len(solar_no_gen):
        test = mannwhitneyu(solar_gen, solar_no_gen, alternative="two-sided")
        rows.append(
            {
                "test": "Mann-Whitney U",
                "comparison": "clean solar kWp by generator presence",
                "n_generator": len(solar_gen),
                "median_generator": solar_gen.median(),
                "n_no_generator": len(solar_no_gen),
                "median_no_generator": solar_no_gen.median(),
                "statistic": float(test.statistic),
                "p_value": float(test.pvalue),
            }
        )

    paired_cap = df.loc[df["solar_capacity_kwp_clear"].notna() & df["gen1_capacity_kva_clear"].notna()]
    if len(paired_cap) >= 3:
        rho, p_value = spearmanr(paired_cap["solar_capacity_kwp_clear"], paired_cap["gen1_capacity_kva_clear"])
        rows.append(
            {
                "test": "Spearman rank correlation",
                "comparison": "clean solar kWp vs clean first-generator kVA among paired facilities",
                "n_generator": len(paired_cap),
                "median_generator": paired_cap["gen1_capacity_kva_clear"].median(),
                "n_no_generator": np.nan,
                "median_no_generator": paired_cap["solar_capacity_kwp_clear"].median(),
                "statistic": float(rho),
                "p_value": float(p_value),
            }
        )

    paired_panel = df.loc[df["solar_panel_count_clean"].notna() & df["gen1_capacity_kva_clear"].notna()]
    if len(paired_panel) >= 3:
        rho, p_value = spearmanr(paired_panel["solar_panel_count_clean"], paired_panel["gen1_capacity_kva_clear"])
        rows.append(
            {
                "test": "Spearman rank correlation",
                "comparison": "clean solar panel count vs clean first-generator kVA among paired facilities",
                "n_generator": len(paired_panel),
                "median_generator": paired_panel["gen1_capacity_kva_clear"].median(),
                "n_no_generator": np.nan,
                "median_no_generator": paired_panel["solar_panel_count_clean"].median(),
                "statistic": float(rho),
                "p_value": float(p_value),
            }
        )

    tests = pd.DataFrame(rows)
    tests.to_csv(TAB / "capacity_comparison_tests.csv", index=False)
    return tests


def make_figure(df: pd.DataFrame) -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "figure.facecolor": "white",
            "savefig.facecolor": "white",
        }
    )
    fig, axes = plt.subplots(
        2,
        2,
        figsize=(15.5, 9),
        gridspec_kw={"left": 0.08, "right": 0.96, "top": 0.82, "bottom": 0.11, "wspace": 0.33, "hspace": 0.48},
    )
    fig.text(0.08, 0.94, "Audit des capacités solaires et groupes électrogènes", fontsize=21, fontweight="bold", color="#102D44")
    fig.text(
        0.08,
        0.895,
        "Données nettoyées au niveau FOSA; capacité solaire inférée en kWp, premier groupe en kVA.",
        fontsize=11.5,
        color="#506476",
    )

    ax = axes[0, 0]
    counts = [
        int((df["has_solar"] == 1).sum()),
        int(df["solar_panel_count_clean"].notna().sum()),
        int(df["D4_solar_capac_median"].notna().sum()),
        int(df["solar_capacity_kwp_clear"].notna().sum()),
        int((df["has_generator"] == 1).sum()),
        int(df["gen1_capacity_kva_clear"].notna().sum()),
    ]
    labels = [
        "Solaire\nprésent",
        "Panneaux\nclairs",
        "Capacité\nsolaire brute",
        "Capacité\nsolaire claire",
        "Groupe\nprésent",
        "1er groupe\nclair",
    ]
    colors = ["#6AA84F", "#6AA84F", "#9BC27B", "#6AA84F", "#D55E00", "#D55E00"]
    bars = ax.bar(labels, counts, color=colors)
    ax.set_ylabel("Nombre de FOSA")
    ax.set_title("A. Rétention des champs utilisables", loc="left", fontsize=12.5, fontweight="bold", color="#102D44")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#D6DEE5", linewidth=0.8)
    ax.set_axisbelow(True)
    for bar, value in zip(bars, counts):
        ax.text(bar.get_x() + bar.get_width() / 2, value + 6, str(value), ha="center", va="bottom", fontsize=9.5)

    ax = axes[0, 1]
    data = [
        df.loc[(df["has_generator"] == 0), "solar_panel_count_clean"].dropna(),
        df.loc[(df["has_generator"] == 1), "solar_panel_count_clean"].dropna(),
    ]
    parts = ax.boxplot(data, patch_artist=True, tick_labels=["Sans groupe", "Avec groupe"], showfliers=False)
    for patch, color in zip(parts["boxes"], ["#9BC27B", "#2F6FAE"]):
        patch.set_facecolor(color)
        patch.set_alpha(0.85)
    ax.set_ylabel("Nombre de panneaux")
    ax.set_title("B. Les sites avec groupe déclarent plus de panneaux", loc="left", fontsize=12.5, fontweight="bold", color="#102D44")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#D6DEE5", linewidth=0.8)
    ax.set_axisbelow(True)

    ax = axes[1, 0]
    paired = df.loc[df["solar_capacity_kwp_clear"].notna() & df["gen1_capacity_kva_clear"].notna()].copy()
    ax.scatter(
        paired["gen1_capacity_kva_clear"],
        paired["solar_capacity_kwp_clear"],
        s=44,
        color="#2F6FAE",
        alpha=0.75,
        edgecolor="white",
        linewidth=0.5,
    )
    max_lim = max(paired["gen1_capacity_kva_clear"].max(), paired["solar_capacity_kwp_clear"].max()) * 1.08
    ax.plot([0.1, max_lim], [0.1, max_lim], color="#A9B5BF", linestyle="--", linewidth=1)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Premier groupe, kVA")
    ax.set_ylabel("Solaire, kWp inféré")
    ax.set_title("C. Capacités appariées, échelles différentes", loc="left", fontsize=12.5, fontweight="bold", color="#102D44")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(True, color="#D6DEE5", linewidth=0.7, which="both")

    ax = axes[1, 1]
    ratio = paired["solar_kwp_to_gen1_kva_ratio"].dropna()
    ax.hist(ratio.clip(upper=2), bins=np.linspace(0, 2, 17), color="#6A3D9A", alpha=0.85)
    ax.axvline(ratio.median(), color="#102D44", linewidth=2)
    ax.text(ratio.median() + 0.03, ax.get_ylim()[1] * 0.84, f"médiane = {fr_num(ratio.median(), 2)}", fontsize=10, color="#102D44")
    ax.set_xlabel("Ratio kWp solaire / kVA du 1er groupe\n(valeurs >2 tronquées dans l'histogramme)")
    ax.set_ylabel("Nombre de FOSA")
    ax.set_title("D. Le solaire est souvent plus petit que le groupe", loc="left", fontsize=12.5, fontweight="bold", color="#102D44")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#D6DEE5", linewidth=0.8)
    ax.set_axisbelow(True)

    for suffix in ("png", "pdf", "svg"):
        fig.savefig(FIG / f"fig_solar_generator_capacity_audit.{suffix}", dpi=300, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)


def write_report(df: pd.DataFrame, tables: dict[str, pd.DataFrame], tests: pd.DataFrame) -> None:
    dist = tables["distribution_summary"].set_index("measure")
    paired = tables["paired"]
    ratio = paired["solar_kwp_to_gen1_kva_ratio"].dropna()

    def stat_line(measure: str, unit: str) -> str:
        row = dist.loc[measure]
        return (
            f"n={int(row['n'])}, median {fr_num(row['median'])} {unit} "
            f"[IQR {fr_num(row['q25'])}-{fr_num(row['q75'])}], p90 {fr_num(row['p90'])}, max {fr_num(row['max'])}"
        )

    rows = [
        "# Solar and Generator Capacity Audit",
        "",
        "## Cleaning Rules",
        "",
        "- Solar panel count: kept when solar was reported, the median reconciled panel count was positive, <=500, and the facility-level conflict flag was zero.",
        "- Solar capacity: inferred from `D4_solar_capac_median` using reported panel count. Values were accepted only when either a W or kW interpretation implied 50-750 W per panel. Values <100 were preferentially treated as kW; values >=100 were preferentially treated as W.",
        "- First generator capacity: kept when generator was reported, first-generator capacity was >=1 kVA after cleaning, and the conflict flag was zero. Values >500 and <=10,000 were treated as VA/W-like entries and divided by 1,000; values >10,000 would be excluded.",
        "- Solar kWp and generator kVA are compared only as facility-level scale indicators; they are not equivalent measures of firm power.",
        "",
        "## Headline Results",
        "",
        f"- Solar present: {int((df['has_solar'] == 1).sum())}/{len(df)} facilities.",
        f"- Generator present: {int((df['has_generator'] == 1).sum())}/{len(df)} facilities.",
        f"- Both solar and generator: {int(((df['has_solar'] == 1) & (df['has_generator'] == 1)).sum())}/{len(df)} facilities.",
        f"- Solar panels, clear count: {stat_line('Solar panels, clear count', 'panels')}.",
        f"- Solar capacity, inferred clean: {stat_line('Solar capacity, inferred clean kWp', 'kWp')}.",
        f"- First generator capacity, clean: {stat_line('First generator capacity, clean kVA', 'kVA')}.",
        f"- Paired clean capacity comparison: n={len(paired)}, median solar {fr_num(paired['solar_capacity_kwp_clear'].median())} kWp vs median first-generator {fr_num(paired['gen1_capacity_kva_clear'].median())} kVA; median ratio {fr_num(ratio.median(), 2)}.",
        "",
        "## Statistical Checks",
        "",
    ]
    if tests.empty:
        rows.append("- No statistical checks were possible after cleaning.")
    else:
        for _, row in tests.iterrows():
            rows.append(
                f"- {row['comparison']}: {row['test']}, statistic={fr_num(row['statistic'], 3)}, p={row['p_value']:.4g}."
            )

    rows += [
        "",
        "## Interpretation",
        "",
        "The panel-count field is substantially more reliable than the capacity field. Cleaned panel counts are available for most solar-reporting facilities, while clean installed solar capacity is available for a much smaller subset because the raw capacity field mixes scales and contains physically implausible panel/capacity combinations.",
        "",
        "The capacity field also has a clear geographic missingness problem: Sud-Kivu has solar panel counts but no non-missing solar-capacity entries in the facility master. Solar capacity should therefore not be used for province-level inference without revisiting the source instrument or raw collection history.",
        "",
        "The cleaned comparison suggests that solar installations are present at many facilities but are typically small relative to generator capacity. Among paired clean observations, the median solar/generator capacity ratio is well below 1. Generator-backed sites also report larger solar arrays, suggesting that solar is often layered onto larger, more energy-complex facilities rather than substituting for generator capacity.",
        "",
        "## Outputs",
        "",
        "- `tables/facility_solar_generator_capacity_clean.csv`",
        "- `tables/capacity_records_to_review.csv`",
        "- `tables/capacity_distribution_summary.csv`",
        "- `tables/capacity_summary_by_group.csv`",
        "- `tables/capacity_comparison_tests.csv`",
        "- `figures/fig_solar_generator_capacity_audit.png`",
    ]
    (OUT / "solar_generator_capacity_audit.md").write_text("\n".join(rows) + "\n")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)
    TAB.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(INPUT)
    clean = add_clean_fields(df)
    tables = write_summary_tables(clean)
    tests = test_rows(clean)
    make_figure(clean)
    write_report(clean, tables, tests)

    print(OUT / "solar_generator_capacity_audit.md")


if __name__ == "__main__":
    main()
