#!/usr/bin/env python3
"""Build manuscript figures for the DRC3a v4 draft."""

from __future__ import annotations

from pathlib import Path
import textwrap

from PIL import Image, ImageOps
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
FACILITY_MASTER = ROOT / "outputs/drc2_facility_master/facility_master.csv"
SLIDE_DIR = ROOT / "outputs/air_liquide_deck_review/rendered"
OUTDIR = ROOT / "outputs/v4_figures"


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
    1: "HGR - General referral hospital",
    2: "CH - Hospital center",
    3: "CSR - Referral health center",
    5: "HP - Provincial hospital",
    6: "CM - Medical center",
}

FACILITY_TYPE_ORDER = [
    "HP - Provincial hospital",
    "HGR - General referral hospital",
    "CH - Hospital center",
    "CSR - Referral health center",
    "CM - Medical center",
]

PROVINCE_LABELS = {
    1: "North Kivu",
    2: "South Kivu",
    3: "Haut Katanga",
}

PROVINCE_ORDER = ["North Kivu", "South Kivu", "Haut Katanga"]

ENERGY_COLORS = {
    "No energy source": "#A4A4A4",
    "Grid": "#2C6FB2",
    "Generator": "#D95F02",
    "Solar": "#009E73",
    "Grid + Generator": "#756BB1",
    "Grid + Solar": "#66A61E",
    "Generator + Solar": "#E7298A",
    "Grid + Generator + Solar": "#4D4D4D",
}

OXYGEN_COLORS = {
    "No oxygen source": "#8F8F8F",
    "Concentrator": "#1F78B4",
    "Cylinders": "#33A02C",
    "Other oxygen": "#B15928",
    "Concentrator + Cylinders": "#6A3D9A",
    "Concentrator + Internal PSA": "#FB9A99",
    "Concentrator + External PSA": "#E31A1C",
    "Concentrator + Other oxygen": "#A6CEE3",
    "Concentrator + Cylinders + Internal PSA": "#FDBF6F",
    "Concentrator + Cylinders + External PSA": "#CAB2D6",
    "Concentrator + Cylinders + Other oxygen": "#FFED6F",
}


def wrap_label(label: str, width: int = 27) -> str:
    if "(n=" in label:
        name, count = label.rsplit(" (n=", 1)
        return "\n".join(textwrap.wrap(name, width=width, break_long_words=False)) + "\n(n=" + count
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
    legend_labels: dict[str, str],
    show_legend: bool = False,
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
            linewidth=0.65,
            height=0.68,
            label=legend_labels[category],
        )
        left += vals

    ax.set_yticks(y)
    ax.set_yticklabels([wrap_label(x) for x in tab.index], fontsize=10.5, color="#24313D")
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xticks(np.arange(0, 101, 20))
    ax.set_xlabel("% of facilities", fontsize=11.5, color="#24313D", labelpad=8)
    ax.set_title(title, loc="left", fontsize=15, fontweight="bold", color="#102D44", pad=12)
    ax.grid(axis="x", color="#D4DDE5", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color("#AAB7C2")
    ax.tick_params(axis="x", labelsize=10.5, colors="#24313D")
    ax.tick_params(axis="y", length=0, pad=6)
    if show_legend:
        ax.legend(
            title="Regime",
            loc="center left",
            bbox_to_anchor=(1.01, 0.5),
            frameon=False,
            fontsize=9.8,
            title_fontsize=10.5,
            handlelength=1.3,
            borderaxespad=0,
        )


def build_regime_figure() -> Path:
    df = pd.read_csv(FACILITY_MASTER)
    df["facility_type_label"] = df["A7_type"].map(FACILITY_TYPE_LABELS)
    df["province_label"] = df["A5_province"].map(PROVINCE_LABELS)
    df = df.dropna(subset=["facility_type_label", "province_label", "energy_profile", "oxygen_profile"])

    energy_legend = {
        "No energy source": "No source",
        "Grid": "Grid",
        "Generator": "Generator",
        "Solar": "Solar",
        "Grid + Generator": "Grid + gen.",
        "Grid + Solar": "Grid + solar",
        "Generator + Solar": "Gen. + solar",
        "Grid + Generator + Solar": "Grid + gen. + solar",
    }
    oxygen_legend = {
        "No oxygen source": "No source",
        "Concentrator": "Concentrator",
        "Cylinders": "Cylinders",
        "Other oxygen": "Other",
        "Concentrator + Cylinders": "Conc. + cyl.",
        "Concentrator + Internal PSA": "Conc. + internal PSA",
        "Concentrator + External PSA": "Conc. + external PSA",
        "Concentrator + Other oxygen": "Conc. + other",
        "Concentrator + Cylinders + Internal PSA": "Conc. + cyl. + internal PSA",
        "Concentrator + Cylinders + External PSA": "Conc. + cyl. + external PSA",
        "Concentrator + Cylinders + Other oxygen": "Conc. + cyl. + other",
    }

    panels = [
        (
            "facility_type_label",
            "energy_profile",
            FACILITY_TYPE_ORDER,
            ENERGY_ORDER,
            ENERGY_COLORS,
            "A. Energy regimes by facility type",
            energy_legend,
            True,
        ),
        (
            "facility_type_label",
            "oxygen_profile",
            FACILITY_TYPE_ORDER,
            OXYGEN_ORDER,
            OXYGEN_COLORS,
            "B. Oxygen regimes by facility type",
            oxygen_legend,
            True,
        ),
        (
            "province_label",
            "energy_profile",
            PROVINCE_ORDER,
            ENERGY_ORDER,
            ENERGY_COLORS,
            "C. Energy regimes by province",
            energy_legend,
            False,
        ),
        (
            "province_label",
            "oxygen_profile",
            PROVINCE_ORDER,
            OXYGEN_ORDER,
            OXYGEN_COLORS,
            "D. Oxygen regimes by province",
            oxygen_legend,
            False,
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

    fig, axes = plt.subplots(4, 1, figsize=(12.8, 14.2), constrained_layout=False)
    fig.subplots_adjust(left=0.24, right=0.72, top=0.94, bottom=0.07, hspace=0.62)

    for ax, panel in zip(axes.flat, panels):
        row, col, row_order, col_order, colors, title, legend_labels, show_legend = panel
        tab = panel_table(df, row, col, row_order, col_order)
        plot_panel(ax, tab, colors, title, legend_labels, show_legend=show_legend)

    fig.suptitle(
        "Reported energy and oxygen regimes by facility type and province",
        x=0.24,
        ha="left",
        fontsize=18.5,
        fontweight="bold",
        color="#0B1F33",
    )

    output = OUTDIR / "fig2_energy_oxygen_regimes_english.png"
    fig.savefig(output, dpi=300)
    fig.savefig(output.with_suffix(".pdf"))
    plt.close(fig)
    return output


def crop_slide(slide_name: str, box: tuple[int, int, int, int], output_name: str, border: int = 0) -> Path:
    image = Image.open(SLIDE_DIR / slide_name).convert("RGB")
    cropped = image.crop(box)
    if border:
        cropped = ImageOps.expand(cropped, border=border, fill="white")
    output = OUTDIR / output_name
    cropped.save(output, quality=95)
    return output


def build_psa_energy_figure() -> Path:
    labels = ["Reference\nwithout PSA", "With PSA"]
    other = np.array([510, 510])
    concentrators = np.array([90, 45])
    psa = np.array([0, 336])
    totals = other + concentrators + psa

    colors = {
        "Other hospital loads": "#4C78A8",
        "Oxygen concentrators": "#F58518",
        "PSA plant": "#54A24B",
    }

    fig, ax = plt.subplots(figsize=(8.4, 5.4))
    x = np.arange(len(labels))
    width = 0.52
    ax.bar(x, other, width, label="Other hospital loads", color=colors["Other hospital loads"])
    ax.bar(x, concentrators, width, bottom=other, label="Oxygen concentrators", color=colors["Oxygen concentrators"])
    ax.bar(x, psa, width, bottom=other + concentrators, label="PSA plant", color=colors["PSA plant"])

    for i, total in enumerate(totals):
        ax.text(x[i], total + 18, f"~{int(total)} kWh/day", ha="center", va="bottom", fontsize=12.5, fontweight="bold")

    ax.text(
        1,
        705,
        "Oxygen-related energy\n~15% to ~43%",
        ha="center",
        va="center",
        fontsize=11.5,
        color="#25313B",
        bbox={"boxstyle": "round,pad=0.25", "facecolor": "white", "edgecolor": "#B8C2CC", "linewidth": 0.8},
    )

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=12)
    ax.set_ylabel("Estimated electricity use (kWh/day)", fontsize=12)
    ax.set_title("Estimated daily facility energy before and after PSA installation", loc="left", fontsize=14.5, fontweight="bold")
    ax.set_ylim(0, 1010)
    ax.grid(axis="y", color="#D9E1E8", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(loc="upper left", bbox_to_anchor=(0, -0.16), ncol=3, frameon=False, fontsize=11)
    fig.subplots_adjust(left=0.13, right=0.95, top=0.88, bottom=0.25)

    output = OUTDIR / "fig4_psa_energy_scenario_english.png"
    fig.savefig(output, dpi=300)
    fig.savefig(output.with_suffix(".pdf"))
    plt.close(fig)
    return output


def main() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    outputs = [
        crop_slide("slide-1.png", (405, 130, 1020, 845), "fig1_study_area_map_from_slide1.png", border=14),
        build_regime_figure(),
        build_psa_energy_figure(),
        crop_slide("slide-31.png", (50, 120, 1190, 850), "fig5_kw_kwh_traces_from_slide31.png", border=10),
    ]
    for output in outputs:
        print(output)


if __name__ == "__main__":
    main()
