#!/usr/bin/env python3
"""Render a French, slide-ready version of the DRC2 energy/oxygen regimes figure."""

from __future__ import annotations

from pathlib import Path
import textwrap

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "outputs/drc2_facility_master/facility_master.csv"
OUTDIR = ROOT / "outputs/drc2_high_n_mockup/figures"


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

PROVINCE_LABELS = {
    1: "Nord-Kivu",
    2: "Sud-Kivu",
    3: "Haut-Katanga",
}

PROVINCE_ORDER = ["Nord-Kivu", "Sud-Kivu", "Haut-Katanga"]

ENERGY_FR = {
    "No energy source": "Aucune source",
    "Grid": "Réseau",
    "Generator": "Groupe",
    "Solar": "Solaire",
    "Grid + Generator": "Réseau + groupe",
    "Grid + Solar": "Réseau + solaire",
    "Generator + Solar": "Groupe + solaire",
    "Grid + Generator + Solar": "Réseau + groupe + solaire",
}

OXYGEN_FR = {
    "No oxygen source": "Aucune source d'oxygène",
    "Concentrator": "Concentrateur",
    "Cylinders": "Bouteilles",
    "Other oxygen": "Autre oxygène",
    "Concentrator + Cylinders": "Concentrateur + bouteilles",
    "Concentrator + Internal PSA": "Concentrateur + PSA interne",
    "Concentrator + External PSA": "Concentrateur + PSA externe",
    "Concentrator + Other oxygen": "Concentrateur + autre oxygène",
    "Concentrator + Cylinders + Internal PSA": "Conc. + bouteilles + PSA interne",
    "Concentrator + Cylinders + External PSA": "Conc. + bouteilles + PSA externe",
    "Concentrator + Cylinders + Other oxygen": "Conc. + bouteilles + autre oxygène",
}

ENERGY_COLORS = {
    "No energy source": "#8B9098",
    "Grid": "#2F6FAE",
    "Generator": "#D55E00",
    "Solar": "#009E73",
    "Grid + Generator": "#7867B1",
    "Grid + Solar": "#6AA84F",
    "Generator + Solar": "#D45087",
    "Grid + Generator + Solar": "#4A4A4A",
}

OXYGEN_COLORS = {
    "No oxygen source": "#8B9098",
    "Concentrator": "#2F80B7",
    "Cylinders": "#2CA25F",
    "Other oxygen": "#B7791F",
    "Concentrator + Cylinders": "#6A3D9A",
    "Concentrator + Internal PSA": "#F28E8C",
    "Concentrator + External PSA": "#D62728",
    "Concentrator + Other oxygen": "#9FD0E3",
    "Concentrator + Cylinders + Internal PSA": "#F6B55F",
    "Concentrator + Cylinders + External PSA": "#B8A3D6",
    "Concentrator + Cylinders + Other oxygen": "#F2D55C",
}


def wrap_label(label: str, width: int = 26) -> str:
    if "(n=" in label:
        name, count = label.rsplit(" (n=", 1)
        count = "(n=" + count
        return "\n".join(textwrap.wrap(name, width=width, break_long_words=False)) + f"\n{count}"
    return "\n".join(textwrap.wrap(label, width=width, break_long_words=False))


def panel_table(df: pd.DataFrame, row: str, col: str, row_order: list[str], col_order: list[str]) -> pd.DataFrame:
    tab = pd.crosstab(df[row], df[col], normalize="index").mul(100)
    tab = tab.reindex(index=[x for x in row_order if x in tab.index])
    tab = tab.reindex(columns=col_order).fillna(0)
    counts = df[row].value_counts()
    tab.index = [f"{idx} (n={int(counts.get(idx, 0))})" for idx in tab.index]
    return tab


def plot_panel(
    ax: plt.Axes,
    tab: pd.DataFrame,
    colors: dict[str, str],
    title: str,
    label_map: dict[str, str],
    legend_handles: list,
    legend_labels: list[str],
) -> None:
    y = np.arange(len(tab))
    left = np.zeros(len(tab))

    for category in tab.columns:
        vals = tab[category].to_numpy()
        bars = ax.barh(
            y,
            vals,
            left=left,
            color=colors[category],
            edgecolor="white",
            linewidth=0.55,
            height=0.68,
            label=label_map[category],
        )
        if not legend_handles:
            pass
        left += vals
        if category not in legend_labels:
            legend_handles.append(bars[0])
            legend_labels.append(category)

    ax.set_yticks(y)
    ax.set_yticklabels([wrap_label(x) for x in tab.index], fontsize=9.8, color="#1F2D3A")
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xticks(np.arange(0, 101, 20))
    ax.set_xlabel("% des FOSA", fontsize=10.8, color="#2D3C48", labelpad=7)
    ax.set_title(title, loc="left", fontsize=13.4, fontweight="bold", color="#102D44", pad=10)
    ax.grid(axis="x", color="#D6DEE5", linewidth=0.75)
    ax.set_axisbelow(True)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color("#A9B5BF")
    ax.tick_params(axis="x", labelsize=9.6, colors="#2D3C48")
    ax.tick_params(axis="y", length=0, pad=5)


def main() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(INPUT)
    df["facility_type_fr"] = df["A7_type"].map(FACILITY_TYPE_LABELS)
    df["province_fr"] = df["A5_province"].map(PROVINCE_LABELS)
    df = df.dropna(subset=["facility_type_fr", "province_fr", "energy_profile", "oxygen_profile"])

    panels = [
        (
            "facility_type_fr",
            "energy_profile",
            FACILITY_TYPE_ORDER,
            ENERGY_ORDER,
            ENERGY_COLORS,
            "Régimes énergétiques par type de FOSA",
            ENERGY_FR,
            "energy",
        ),
        (
            "facility_type_fr",
            "oxygen_profile",
            FACILITY_TYPE_ORDER,
            OXYGEN_ORDER,
            OXYGEN_COLORS,
            "Régimes d'oxygène par type de FOSA",
            OXYGEN_FR,
            "oxygen",
        ),
        (
            "province_fr",
            "energy_profile",
            PROVINCE_ORDER,
            ENERGY_ORDER,
            ENERGY_COLORS,
            "Régimes énergétiques par province",
            ENERGY_FR,
            "energy",
        ),
        (
            "province_fr",
            "oxygen_profile",
            PROVINCE_ORDER,
            OXYGEN_ORDER,
            OXYGEN_COLORS,
            "Régimes d'oxygène par province",
            OXYGEN_FR,
            "oxygen",
        ),
    ]

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "axes.titleweight": "bold",
            "figure.facecolor": "white",
            "savefig.facecolor": "white",
        }
    )

    fig, axes = plt.subplots(
        2,
        2,
        figsize=(17.2, 9.68),
        gridspec_kw={"wspace": 0.50, "hspace": 0.64, "left": 0.145, "right": 0.965, "top": 0.82, "bottom": 0.28},
    )

    handles_by_kind = {"energy": [], "oxygen": []}
    labels_by_kind = {"energy": [], "oxygen": []}

    for ax, spec in zip(axes.ravel(), panels):
        row, col, row_order, col_order, colors, title, label_map, kind = spec
        tab = panel_table(df, row, col, row_order, col_order)
        plot_panel(ax, tab, colors, title, label_map, handles_by_kind[kind], labels_by_kind[kind])

    fig.text(
        0.145,
        0.935,
        "Enquête DRC2 : régimes énergétiques et d'oxygène déclarés",
        fontsize=22,
        fontweight="bold",
        color="#102D44",
        ha="left",
    )
    fig.text(
        0.145,
        0.895,
        "Répartition en pourcentage par type de formation sanitaire et par province (n = 491)",
        fontsize=12.8,
        color="#506476",
        ha="left",
    )

    energy_labels = [ENERGY_FR[x] for x in labels_by_kind["energy"]]
    oxygen_labels = [OXYGEN_FR[x] for x in labels_by_kind["oxygen"]]

    legend1 = fig.legend(
        handles_by_kind["energy"],
        energy_labels,
        title="Régime énergétique",
        loc="lower left",
        bbox_to_anchor=(0.145, 0.035),
        ncol=2,
        frameon=False,
        fontsize=10.2,
        title_fontsize=11.4,
        handlelength=1.45,
        handleheight=0.9,
        columnspacing=1.25,
        labelspacing=0.58,
    )
    legend1.get_title().set_fontweight("bold")
    legend1.get_title().set_color("#102D44")

    legend2 = fig.legend(
        handles_by_kind["oxygen"],
        oxygen_labels,
        title="Régime d'oxygène",
        loc="lower left",
        bbox_to_anchor=(0.58, 0.013),
        ncol=2,
        frameon=False,
        fontsize=9.3,
        title_fontsize=11.4,
        handlelength=1.45,
        handleheight=0.9,
        columnspacing=1.05,
        labelspacing=0.58,
    )
    legend2.get_title().set_fontweight("bold")
    legend2.get_title().set_color("#102D44")

    for suffix in ("png", "pdf", "svg"):
        output = OUTDIR / f"fig_5_energy_oxygen_by_type_and_province_fr_slide.{suffix}"
        fig.savefig(output, dpi=300, bbox_inches="tight", pad_inches=0.16)

    plt.close(fig)

    print(OUTDIR / "fig_5_energy_oxygen_by_type_and_province_fr_slide.png")


if __name__ == "__main__":
    main()
