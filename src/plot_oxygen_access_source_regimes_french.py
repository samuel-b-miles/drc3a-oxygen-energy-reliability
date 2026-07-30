#!/usr/bin/env python3
"""Create French multipanel figure for no oxygen access and oxygen-source regimes."""

from __future__ import annotations

from pathlib import Path
from textwrap import fill

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "outputs/drc2_facility_master/facility_master.csv"
FIG_DIR = ROOT / "outputs/drc2_high_n_mockup/figures"
TAB_DIR = ROOT / "outputs/drc2_high_n_mockup/tables"


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

ENERGY_FR = {
    "No energy source": "Aucune\nsource",
    "Grid": "Réseau",
    "Generator": "Groupe",
    "Solar": "Solaire",
    "Grid + Generator": "Réseau\n+ groupe",
    "Grid + Solar": "Réseau\n+ solaire",
    "Generator + Solar": "Groupe\n+ solaire",
    "Grid + Generator + Solar": "Réseau\n+ groupe\n+ solaire",
}

PROVINCE_LABELS = {
    1: "Nord-Kivu",
    2: "Sud-Kivu",
    3: "Haut-Katanga",
}

PROVINCE_ORDER = ["Nord-Kivu", "Sud-Kivu", "Haut-Katanga"]

FACILITY_TYPE_LABELS = {
    1: "HGR - Hôpital général de référence",
    2: "CH - Centre hospitalier",
    3: "CSR - Centre de santé de référence",
    5: "HP - Hôpital provincial",
    6: "CM - Centre médical",
}

FACILITY_TYPE_ORDER = [
    "HP - Hôpital provincial",
    "HGR - Hôpital général de référence",
    "CH - Centre hospitalier",
    "CSR - Centre de santé de référence",
    "CM - Centre médical",
]

SOURCE_ORDER = [
    "Concentrateur seul",
    "Bouteilles seules",
    "Autre oxygène seul",
    "Concentrateur + bouteilles",
    "Concentrateur + PSA",
    "Concentrateur + autre",
    "Concentrateur + bouteilles + PSA/autre",
]

SOURCE_COLORS = {
    "Concentrateur seul": "#2F80B7",
    "Bouteilles seules": "#2CA25F",
    "Autre oxygène seul": "#B7791F",
    "Concentrateur + bouteilles": "#6A3D9A",
    "Concentrateur + PSA": "#E66F6B",
    "Concentrateur + autre": "#9FD0E3",
    "Concentrateur + bouteilles + PSA/autre": "#F3C85B",
}


def french_decimal(value: float, digits: int = 1) -> str:
    return f"{value:.{digits}f}".replace(".", ",")


def source_regime(profile: str) -> str:
    if profile == "Concentrator":
        return "Concentrateur seul"
    if profile == "Cylinders":
        return "Bouteilles seules"
    if profile == "Other oxygen":
        return "Autre oxygène seul"
    if profile == "Concentrator + Cylinders":
        return "Concentrateur + bouteilles"
    if profile in {"Concentrator + Internal PSA", "Concentrator + External PSA"}:
        return "Concentrateur + PSA"
    if profile == "Concentrator + Other oxygen":
        return "Concentrateur + autre"
    if profile in {
        "Concentrator + Cylinders + Internal PSA",
        "Concentrator + Cylinders + External PSA",
        "Concentrator + Cylinders + Other oxygen",
    }:
        return "Concentrateur + bouteilles + PSA/autre"
    return "Autre oxygène seul"


def clean_axis(ax: plt.Axes, grid_axis: str = "x") -> None:
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color("#A9B5BF")
    ax.grid(axis=grid_axis, color="#D6DEE5", linewidth=0.75)
    ax.set_axisbelow(True)
    ax.tick_params(colors="#2D3C48")


def panel_label(ax: plt.Axes, label: str) -> None:
    ax.text(
        -0.09,
        1.08,
        label,
        transform=ax.transAxes,
        fontsize=15.5,
        fontweight="bold",
        color="#102D44",
        ha="left",
        va="bottom",
    )


def add_no_oxygen_heatmap(ax: plt.Axes, df: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        df.groupby(["province_fr", "energy_profile"])
        .agg(total=("A8_FOSA", "count"), no_oxygen=("no_oxygen", "sum"))
        .reset_index()
    )
    grouped["pct_no_oxygen"] = grouped["no_oxygen"] / grouped["total"] * 100
    grouped.to_csv(TAB_DIR / "no_oxygen_by_province_energy_regime.csv", index=False)

    pct = grouped.pivot(index="province_fr", columns="energy_profile", values="pct_no_oxygen")
    no = grouped.pivot(index="province_fr", columns="energy_profile", values="no_oxygen")
    total = grouped.pivot(index="province_fr", columns="energy_profile", values="total")
    pct = pct.reindex(index=PROVINCE_ORDER, columns=ENERGY_ORDER)
    no = no.reindex(index=PROVINCE_ORDER, columns=ENERGY_ORDER)
    total = total.reindex(index=PROVINCE_ORDER, columns=ENERGY_ORDER)

    data = pct.to_numpy(dtype=float)
    im = ax.imshow(data, cmap="OrRd", vmin=0, vmax=80, aspect="auto")
    ax.set_xticks(np.arange(len(ENERGY_ORDER)))
    ax.set_xticklabels([ENERGY_FR[x] for x in ENERGY_ORDER], fontsize=8.8)
    ax.set_yticks(np.arange(len(PROVINCE_ORDER)))
    ax.set_yticklabels(PROVINCE_ORDER, fontsize=10.5)
    ax.tick_params(axis="both", length=0, colors="#1F2D3A")
    ax.set_title("Sans oxygène par province et régime énergétique", loc="left", fontsize=13.6, fontweight="bold", color="#102D44", pad=11)
    panel_label(ax, "A")

    for i in range(len(PROVINCE_ORDER)):
        for j in range(len(ENERGY_ORDER)):
            if np.isnan(data[i, j]):
                text = "NA"
                color = "#2D3C48"
            else:
                n_val = int(no.iloc[i, j])
                t_val = int(total.iloc[i, j])
                text = f"{data[i, j]:.0f}%\n{n_val}/{t_val}"
                color = "white" if data[i, j] >= 45 else "#1F2D3A"
            ax.text(j, i, text, ha="center", va="center", fontsize=7.5, color=color, fontweight="bold")

    for spine in ax.spines.values():
        spine.set_visible(False)
    cbar = plt.colorbar(im, ax=ax, fraction=0.04, pad=0.02)
    cbar.set_label("% sans oxygène", fontsize=9.2, color="#2D3C48")
    cbar.ax.tick_params(labelsize=8.5, colors="#2D3C48")
    return grouped


def add_no_oxygen_by_province(ax: plt.Axes, df: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        df.groupby("province_fr")
        .agg(total=("A8_FOSA", "count"), no_oxygen=("no_oxygen", "sum"))
        .reindex(PROVINCE_ORDER)
        .reset_index()
    )
    grouped["pct_no_oxygen"] = grouped["no_oxygen"] / grouped["total"] * 100
    grouped.to_csv(TAB_DIR / "no_oxygen_by_province.csv", index=False)

    plot = grouped.iloc[::-1].copy()
    bars = ax.barh(plot["province_fr"], plot["pct_no_oxygen"], color="#C7502B", height=0.62)
    ax.set_xlim(0, max(50, grouped["pct_no_oxygen"].max() + 9))
    ax.set_xlabel("% des FOSA", fontsize=10.8, color="#2D3C48")
    ax.set_title("Part des FOSA sans source d'oxygène", loc="left", fontsize=13.6, fontweight="bold", color="#102D44", pad=11)
    clean_axis(ax, "x")
    ax.tick_params(axis="y", length=0, labelsize=10.8)
    panel_label(ax, "B")

    for bar, (_, row) in zip(bars, plot.iterrows()):
        pct = french_decimal(row["pct_no_oxygen"])
        label = f"{int(row['no_oxygen'])}/{int(row['total'])} ({pct} %)"
        ax.text(
            row["pct_no_oxygen"] + 1.2,
            bar.get_y() + bar.get_height() / 2,
            label,
            va="center",
            ha="left",
            fontsize=10,
            color="#2D3C48",
        )
    return grouped


def source_percent_table(df: pd.DataFrame, row: str, row_order: list[str], output_name: str) -> pd.DataFrame:
    ox = df.loc[df["has_oxygen"]].copy()
    counts = ox[row].value_counts()
    tab = pd.crosstab(ox[row], ox["source_regime"], normalize="index").mul(100)
    tab = tab.reindex(index=[x for x in row_order if x in tab.index], columns=SOURCE_ORDER).fillna(0)
    out = tab.copy()
    out.insert(0, "n_with_oxygen", [int(counts.get(idx, 0)) for idx in out.index])
    out.to_csv(TAB_DIR / output_name)
    return tab


def add_stacked_source_panel(ax: plt.Axes, tab: pd.DataFrame, counts: pd.Series, title: str, panel: str) -> list:
    y = np.arange(len(tab))
    left = np.zeros(len(tab))
    handles = []
    for category in SOURCE_ORDER:
        vals = tab[category].to_numpy()
        bars = ax.barh(
            y,
            vals,
            left=left,
            height=0.62,
            color=SOURCE_COLORS[category],
            edgecolor="white",
            linewidth=0.7,
            label=category,
        )
        handles.append(bars[0])
        left += vals

    labels = [f"{fill(idx, 25, break_long_words=False)}\n(n={int(counts.get(idx, 0))})" for idx in tab.index]
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9.3, color="#1F2D3A")
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xticks(np.arange(0, 101, 20))
    ax.set_xlabel("% parmi les FOSA avec oxygène", fontsize=10.3, color="#2D3C48")
    ax.set_title(title, loc="left", fontsize=13.6, fontweight="bold", color="#102D44", pad=11)
    clean_axis(ax, "x")
    ax.tick_params(axis="y", length=0)
    panel_label(ax, panel)
    return handles


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    TAB_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(INPUT)
    df["province_fr"] = df["A5_province"].map(PROVINCE_LABELS)
    df["facility_type_fr"] = df["A7_type"].map(FACILITY_TYPE_LABELS)
    df["has_oxygen"] = df["n_oxygen_sources"] > 0
    df["no_oxygen"] = (~df["has_oxygen"]).astype(int)
    df["source_regime"] = df["oxygen_profile"].map(source_regime)
    df = df.dropna(subset=["province_fr", "facility_type_fr", "energy_profile", "oxygen_profile"])

    ox = df.loc[df["has_oxygen"]].copy()
    province_counts = ox["province_fr"].value_counts()
    type_counts = ox["facility_type_fr"].value_counts()
    province_tab = source_percent_table(df, "province_fr", PROVINCE_ORDER, "oxygen_source_regime_among_oxygen_by_province.csv")
    type_tab = source_percent_table(df, "facility_type_fr", FACILITY_TYPE_ORDER, "oxygen_source_regime_among_oxygen_by_facility_type.csv")

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
        figsize=(16, 9),
        gridspec_kw={"left": 0.08, "right": 0.965, "top": 0.78, "bottom": 0.25, "wspace": 0.34, "hspace": 0.68},
    )

    add_no_oxygen_heatmap(axes[0, 0], df)
    add_no_oxygen_by_province(axes[0, 1], df)
    handles = add_stacked_source_panel(
        axes[1, 0],
        province_tab,
        province_counts,
        "Source d'oxygène parmi les FOSA équipées, par province",
        "C",
    )
    add_stacked_source_panel(
        axes[1, 1],
        type_tab,
        type_counts,
        "Source d'oxygène parmi les FOSA équipées, par type",
        "D",
    )

    fig.text(
        0.08,
        0.925,
        "Accès à l'oxygène et régimes de source déclarés",
        fontsize=22,
        fontweight="bold",
        color="#102D44",
        ha="left",
    )
    fig.text(
        0.08,
        0.875,
        "A-B : absence de source d'oxygène. C-D : composition des sources après exclusion des FOSA sans oxygène.",
        fontsize=12.6,
        color="#506476",
        ha="left",
    )
    fig.text(
        0.08,
        0.142,
        "Note : les cellules de la carte indiquent % sans oxygène et n sans oxygène / n total dans le groupe. Les régimes PSA internes et externes sont regroupés pour la lisibilité.",
        fontsize=9.6,
        color="#60727F",
        ha="left",
    )

    legend = fig.legend(
        handles,
        SOURCE_ORDER,
        title="Régime de source d'oxygène",
        loc="lower center",
        bbox_to_anchor=(0.55, 0.018),
        ncol=4,
        frameon=False,
        fontsize=9.6,
        title_fontsize=11.2,
        columnspacing=1.25,
        handlelength=1.4,
        labelspacing=0.7,
    )
    legend.get_title().set_fontweight("bold")
    legend.get_title().set_color("#102D44")

    for suffix in ("png", "pdf", "svg"):
        output = FIG_DIR / f"fig_oxygen_access_source_regimes_fr_multipanel.{suffix}"
        fig.savefig(output, dpi=300, bbox_inches="tight", pad_inches=0.15)

    plt.close(fig)
    print(FIG_DIR / "fig_oxygen_access_source_regimes_fr_multipanel.png")


if __name__ == "__main__":
    main()
