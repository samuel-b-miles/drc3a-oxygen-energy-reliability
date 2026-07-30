#!/usr/bin/env python3
"""Create a multi-panel figure for equipment-failure free-text layers."""

from __future__ import annotations

from pathlib import Path
from textwrap import fill

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "drc3a_equipment_failure_layers"
FIG = OUT / "figures"


CATEGORY_SHORT = {
    "Oxygen concentrator / oxygen device": "Oxygen devices",
    "Lighting / surgical theatre electrical devices": "Lighting / theatre",
    "Electrical components / power system": "Electrical / power",
    "Ultrasound / echography": "Ultrasound",
    "Patient monitoring / bedside clinical devices": "Monitoring / bedside",
    "Computer / printer / office electronics": "Computers / printers",
    "Sterilization equipment": "Sterilization",
    "Laboratory equipment": "Laboratory",
    "Refrigeration / cold chain / morgue": "Cold chain / morgue",
    "Maternal / neonatal equipment": "Maternal / neonatal",
    "Laundry / water / utility equipment": "Utility equipment",
    "Radiography / X-ray": "Radiography",
}


CAUSE_SHORT = {
    "Voltage instability / fluctuation": "Voltage instability",
    "Power cuts / abrupt restoration": "Power cuts / restart",
    "Insufficient power / no energy": "Insufficient power",
    "Short circuit / burned electronics": "Short circuit / burned",
    "Poor installation": "Poor installation",
    "Lightning / atmospheric discharge": "Lightning",
}


def panel_label(ax, label: str) -> None:
    ax.text(
        -0.12,
        1.05,
        label,
        transform=ax.transAxes,
        fontsize=13,
        fontweight="bold",
        va="bottom",
        ha="left",
    )


def style_axis(ax) -> None:
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="x", color="#d8d8d8", linewidth=0.7, alpha=0.8)
    ax.set_axisbelow(True)


def plot_ranked_bars(ax, data: pd.DataFrame, value_col: str, label_col: str, color: str, title: str, n: int = 10) -> None:
    plot = data.head(n).iloc[::-1].copy()
    labels = [fill(CATEGORY_SHORT.get(x, CAUSE_SHORT.get(x, x)), 22) for x in plot[label_col]]
    bars = ax.barh(labels, plot[value_col], color=color)
    ax.set_title(title, fontsize=12, fontweight="bold", loc="left")
    ax.set_xlabel("Facilities")
    style_axis(ax)
    for bar in bars:
        width = bar.get_width()
        ax.text(width + 0.8, bar.get_y() + bar.get_height() / 2, f"{int(width)}", va="center", fontsize=8)


def plot_heatmap(ax, matrix: pd.DataFrame) -> None:
    pivot = matrix.pivot_table(
        index="equipment_category",
        columns="cause_category",
        values="cause_mentions_with_equipment",
        aggfunc="sum",
        fill_value=0,
    )
    row_order = [
        "Oxygen concentrator / oxygen device",
        "Patient monitoring / bedside clinical devices",
        "Electrical components / power system",
        "Ultrasound / echography",
        "Lighting / surgical theatre electrical devices",
        "Sterilization equipment",
        "Laboratory equipment",
        "Refrigeration / cold chain / morgue",
        "Maternal / neonatal equipment",
        "Computer / printer / office electronics",
    ]
    col_order = [
        "Voltage instability / fluctuation",
        "Short circuit / burned electronics",
        "Insufficient power / no energy",
        "Power cuts / abrupt restoration",
        "Poor installation",
    ]
    pivot = pivot.reindex(index=row_order, columns=col_order).fillna(0)
    pivot.index = [CATEGORY_SHORT.get(x, x) for x in pivot.index]
    pivot.columns = [CAUSE_SHORT.get(x, x) for x in pivot.columns]
    sns.heatmap(
        pivot,
        ax=ax,
        cmap=sns.light_palette("#3268a8", as_cmap=True),
        linewidths=0.5,
        linecolor="#ffffff",
        annot=True,
        fmt=".0f",
        cbar_kws={"label": "Facility mentions", "shrink": 0.75},
    )
    ax.set_title("Device categories by coded cause/context", fontsize=12, fontweight="bold", loc="left")
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.tick_params(axis="x", labelrotation=35, labelsize=8)
    ax.tick_params(axis="y", labelsize=8)


def plot_province_facets(ax, cat_group: pd.DataFrame) -> None:
    top_cats = [
        "Oxygen concentrator / oxygen device",
        "Electrical components / power system",
        "Lighting / surgical theatre electrical devices",
        "Ultrasound / echography",
        "Sterilization equipment",
    ]
    province = cat_group[
        (cat_group["group"] == "province")
        & (cat_group["equipment_category"].isin(top_cats))
        & (cat_group["level"].isin(["Nord-Kivu", "Sud-Kivu", "Haut Katanga"]))
    ].copy()
    province["category_short"] = province["equipment_category"].map(CATEGORY_SHORT)
    province["level"] = pd.Categorical(
        province["level"], ["Sud-Kivu", "Nord-Kivu", "Haut Katanga"], ordered=True
    )
    province["category_short"] = pd.Categorical(
        province["category_short"], [CATEGORY_SHORT[c] for c in top_cats], ordered=True
    )
    sns.barplot(
        data=province,
        x="pct_damage_reporting_facilities",
        y="category_short",
        hue="level",
        ax=ax,
        palette=["#3268a8", "#48a078", "#d08a36"],
    )
    ax.set_title("Damage ecology differs by province", fontsize=12, fontweight="bold", loc="left")
    ax.set_xlabel("% of damage-reporting facilities")
    ax.set_ylabel("")
    style_axis(ax)
    ax.legend(title="", frameon=False, fontsize=8, loc="lower right")


def plot_concentrator_stock(ax, cat_group: pd.DataFrame) -> None:
    stock = cat_group[
        (cat_group["group"] == "concentrator_stock")
        & (cat_group["equipment_category"] == "Oxygen concentrator / oxygen device")
    ].copy()
    stock = stock[stock["level"].isin(["0", "1", "2-3", "4+"])]
    stock["level"] = pd.Categorical(stock["level"], ["0", "1", "2-3", "4+"], ordered=True)
    bars = ax.bar(
        stock["level"].astype(str),
        stock["pct_damage_reporting_facilities"],
        color=["#d5d9de", "#94b9d8", "#5b8fc0", "#3268a8"],
    )
    ax.set_ylim(0, max(stock["pct_damage_reporting_facilities"].max() * 1.22, 55))
    ax.set_title("Oxygen-device damage rises with concentrator stock", fontsize=12, fontweight="bold", loc="left")
    ax.set_xlabel("Total concentrators at facility")
    ax.set_ylabel("% of damage-reporting facilities")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#d8d8d8", linewidth=0.7, alpha=0.8)
    ax.set_axisbelow(True)
    for bar, n in zip(bars, stock["mentions"]):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 1.2,
            f"{bar.get_height():.0f}%\n(n={int(n)})",
            ha="center",
            va="bottom",
            fontsize=8,
        )


def plot_oxygen_callout(ax, oxygen_profile: pd.DataFrame) -> None:
    row = oxygen_profile.loc[oxygen_profile["profile"] == "oxygen_damage_facilities"].iloc[0]
    oxygen_only = int(row["oxygen_only"])
    oxygen_plus = int(row["oxygen_plus_other"])
    total = int(row["facilities"])
    ax.pie(
        [oxygen_only, oxygen_plus],
        startangle=90,
        colors=["#9ecae1", "#3268a8"],
        wedgeprops={"linewidth": 1, "edgecolor": "white"},
        autopct=lambda p: f"{p:.0f}%",
        textprops={"fontsize": 10, "fontweight": "bold", "color": "#202020"},
    )
    ax.set_title("Usually not isolated", fontsize=12, fontweight="bold", loc="left", pad=12)
    ax.legend(
        ["Oxygen only", "Oxygen + other equipment"],
        frameon=False,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.12),
        fontsize=8,
    )
    ax.text(
        0,
        -1.35,
        f"{total} facilities mention oxygen-device damage;\n{oxygen_plus} also mention another damaged category.",
        ha="center",
        va="top",
        fontsize=9,
    )


def main() -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    category_freq = pd.read_csv(ROOT / "outputs/drc2_equipment_failure/tables/equipment_failure_category_frequency.csv")
    cause_freq = pd.read_csv(ROOT / "outputs/drc2_equipment_failure/tables/equipment_failure_cause_frequency.csv")
    matrix = pd.read_csv(OUT / "equipment_category_by_cause_matrix.csv")
    cat_group = pd.read_csv(OUT / "equipment_category_by_group_layers.csv")
    oxygen_profile = pd.read_csv(OUT / "oxygen_damage_profile.csv")

    sns.set_theme(style="white", font="DejaVu Sans")
    fig = plt.figure(figsize=(15, 13.5), constrained_layout=False)
    gs = fig.add_gridspec(
        3,
        2,
        height_ratios=[1.0, 1.2, 1.0],
        width_ratios=[1.05, 1.0],
        hspace=0.42,
        wspace=0.34,
    )
    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    ax_c = fig.add_subplot(gs[1, :])
    ax_d = fig.add_subplot(gs[2, 0])
    right = gs[2, 1].subgridspec(1, 2, width_ratios=[1.2, 0.85], wspace=0.36)
    ax_e = fig.add_subplot(right[0, 0])
    ax_f = fig.add_subplot(right[0, 1])

    plot_ranked_bars(
        ax_a,
        category_freq,
        "facilities",
        "category",
        "#3268a8",
        "Most frequently mentioned damaged equipment",
        n=10,
    )
    plot_ranked_bars(
        ax_b,
        cause_freq,
        "facilities",
        "category",
        "#d08a36",
        "Coded causes/context in free text",
        n=6,
    )
    plot_heatmap(ax_c, matrix)
    plot_province_facets(ax_d, cat_group)
    plot_concentrator_stock(ax_e, cat_group)
    plot_oxygen_callout(ax_f, oxygen_profile)

    for ax, label in zip([ax_a, ax_b, ax_c, ax_d, ax_e, ax_f], list("ABCDEF")):
        panel_label(ax, label)

    fig.suptitle(
        "Free-text equipment damage reveals an electrical fragility ecology",
        fontsize=17,
        fontweight="bold",
        x=0.03,
        y=0.99,
        ha="left",
    )
    fig.text(
        0.03,
        0.965,
        "Facility-level coded mentions from DRC2 survey free text; counts are facilities mentioning a category, not device counts.",
        fontsize=10,
        ha="left",
        color="#444444",
    )

    png = FIG / "fig_equipment_failure_multipanel.png"
    pdf = FIG / "fig_equipment_failure_multipanel.pdf"
    fig.savefig(png, dpi=300, bbox_inches="tight")
    fig.savefig(pdf, bbox_inches="tight")
    plt.close(fig)
    print(png)
    print(pdf)


if __name__ == "__main__":
    main()
