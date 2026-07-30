#!/usr/bin/env python3
"""Render French panels A and B for the equipment damage figure."""

from __future__ import annotations

from pathlib import Path
from textwrap import fill

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TABLE_DIR = ROOT / "outputs/drc2_equipment_failure/tables"
FIG_DIR = ROOT / "outputs/drc2_equipment_failure/figures"


EQUIPMENT_FR = {
    "Oxygen concentrator / oxygen device": "Concentrateur / dispositif d'oxygène",
    "Lighting / surgical theatre electrical devices": "Éclairage / bloc opératoire",
    "Electrical components / power system": "Composants électriques / alimentation",
    "Ultrasound / echography": "Échographie",
    "Patient monitoring / bedside clinical devices": "Moniteurs / appareils au chevet",
    "Computer / printer / office electronics": "Ordinateurs / imprimantes",
    "Sterilization equipment": "Stérilisation",
    "Laboratory equipment": "Laboratoire",
    "Refrigeration / cold chain / morgue": "Réfrigération / chaîne du froid / morgue",
    "Maternal / neonatal equipment": "Maternité / néonatal",
    "Laundry / water / utility equipment": "Buanderie / eau / utilités",
    "Radiography / X-ray": "Radiographie",
}

CAUSE_FR = {
    "Voltage instability / fluctuation": "Instabilité / fluctuation de tension",
    "Power cuts / abrupt restoration": "Coupures / rétablissement brusque",
    "Insufficient power / no energy": "Puissance insuffisante / absence d'énergie",
    "Short circuit / burned electronics": "Court-circuit / composants brûlés",
    "Poor installation": "Mauvaise installation",
    "Lightning / atmospheric discharge": "Foudre / décharge atmosphérique",
}


def french_decimal(value: float) -> str:
    return f"{value:.1f}".replace(".", ",")


def style_axis(ax: plt.Axes) -> None:
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color("#A9B5BF")
    ax.grid(axis="x", color="#D6DEE5", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(axis="y", length=0, labelsize=11.5, colors="#1F2D3A")
    ax.tick_params(axis="x", labelsize=10.5, colors="#2D3C48")
    ax.set_xlabel("Nombre de FOSA", fontsize=11.5, color="#2D3C48", labelpad=8)


def plot_ranked_bar_panel(
    ax: plt.Axes,
    df: pd.DataFrame,
    label_map: dict[str, str],
    title: str,
    panel_letter: str,
    color: str,
    xmax_pad: int,
) -> None:
    plot_df = df.sort_values("facilities", ascending=True).copy()
    labels = [fill(label_map.get(x, x), 30, break_long_words=False) for x in plot_df["category"]]
    bars = ax.barh(labels, plot_df["facilities"], color=color, height=0.72)
    ax.set_title(title, loc="left", fontsize=15.2, fontweight="bold", color="#102D44", pad=12)
    ax.text(
        -0.12,
        1.08,
        panel_letter,
        transform=ax.transAxes,
        fontsize=16.5,
        fontweight="bold",
        color="#102D44",
        ha="left",
        va="bottom",
    )
    style_axis(ax)
    ax.set_xlim(0, plot_df["facilities"].max() + xmax_pad)

    for bar, (_, row) in zip(bars, plot_df.iterrows()):
        value = int(row["facilities"])
        pct = french_decimal(float(row["pct_facilities_reporting_damage"]))
        ax.text(
            value + 0.9,
            bar.get_y() + bar.get_height() / 2,
            f"{value} ({pct} %)",
            va="center",
            ha="left",
            fontsize=10.8,
            color="#2D3C48",
        )


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    equipment = pd.read_csv(TABLE_DIR / "equipment_failure_category_frequency.csv")
    causes = pd.read_csv(TABLE_DIR / "equipment_failure_cause_frequency.csv")
    summary = pd.read_csv(TABLE_DIR / "equipment_failure_summary.csv")

    n_damage = int(
        summary.loc[
            summary["metric"] == "facilities_reporting_medical_equipment_damage",
            "value",
        ].iloc[0]
    )

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "figure.facecolor": "white",
            "savefig.facecolor": "white",
        }
    )

    fig, (ax_a, ax_b) = plt.subplots(
        1,
        2,
        figsize=(16, 9),
        gridspec_kw={"width_ratios": [1.28, 0.95], "left": 0.24, "right": 0.96, "top": 0.78, "bottom": 0.16, "wspace": 0.48},
    )

    plot_ranked_bar_panel(
        ax_a,
        equipment,
        EQUIPMENT_FR,
        "Équipements endommagés mentionnés",
        "A",
        "#2F6FAE",
        xmax_pad=17,
    )
    plot_ranked_bar_panel(
        ax_b,
        causes,
        CAUSE_FR,
        "Causes ou contextes déclarés",
        "B",
        "#D55E00",
        xmax_pad=7,
    )

    fig.text(
        0.24,
        0.93,
        "Équipements endommagés et causes déclarées",
        fontsize=24,
        fontweight="bold",
        color="#102D44",
        ha="left",
    )
    fig.text(
        0.24,
        0.885,
        f"Mentions codées à partir du texte libre parmi les FOSA déclarant des dommages aux équipements médicaux (n = {n_damage})",
        fontsize=13.5,
        color="#506476",
        ha="left",
    )
    fig.text(
        0.24,
        0.055,
        "Note : les catégories ne sont pas mutuellement exclusives; une même FOSA peut mentionner plusieurs équipements ou causes.",
        fontsize=10.8,
        color="#60727F",
        ha="left",
    )

    for suffix in ("png", "pdf", "svg"):
        output = FIG_DIR / f"fig_equipment_failure_panels_ab_fr_slide.{suffix}"
        fig.savefig(output, dpi=300, bbox_inches="tight", pad_inches=0.15)

    plt.close(fig)
    print(FIG_DIR / "fig_equipment_failure_panels_ab_fr_slide.png")


if __name__ == "__main__":
    main()
