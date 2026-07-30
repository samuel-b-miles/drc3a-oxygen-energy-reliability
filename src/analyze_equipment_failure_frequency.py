#!/usr/bin/env python3
"""Code reported medical equipment failures from DRC2 free-text responses."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "outputs/drc2_facility_master/respondent_sample.csv"
MASTER_INPUT = ROOT / "outputs/drc2_facility_master/facility_master.csv"
OUT = ROOT / "outputs/drc2_equipment_failure"
TAB = OUT / "tables"
FIG = OUT / "figures"


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


CATEGORY_PATTERNS = {
    "Oxygen concentrator / oxygen device": [
        r"concentrat",
        r"concentret",
        r"conscent",
        r"contracteur d.?ox",
        r"oxygenat",
        r"oxyg[èe]ne",
    ],
    "Sterilization equipment": [
        r"autoclave",
        r"st[ée]ril",
        r"poup",
        r"popin",
        r"certauclave",
        r"conclave",
        r"casserole",
    ],
    "Ultrasound / echography": [
        r"[ée]chograph",
        r"echograph",
    ],
    "Computer / printer / office electronics": [
        r"ordinateur",
        r"imprim",
        r"photocop",
        r"serveur",
        r"informat",
        r"t[ée]l[ée]vision",
        r"unite centrale",
        r"unit[ée] centrale",
        r"chargeur",
    ],
    "Lighting / surgical theatre electrical devices": [
        r"lampe",
        r"scial",
        r"sial",
        r"cyal",
        r"sciat",
        r"bistouri",
        r"bloc",
        r"salle d.?op",
    ],
    "Laboratory equipment": [
        r"microscope",
        r"centrif",
        r"santrif",
        r"automate",
        r"spectro",
        r"analyseur",
        r"[ée]lectrophor",
        r"h[ée]matolog",
        r"balance",
        r"dop",
    ],
    "Refrigeration / cold chain / morgue": [
        r"frigo",
        r"r[ée]frig",
        r"cong[ée]lat",
        r"morgue",
        r"mortuaire",
    ],
    "Maternal / neonatal equipment": [
        r"couveuse",
        r"incubat",
        r"table chauff",
        r"n[ée]onat",
    ],
    "Patient monitoring / bedside clinical devices": [
        r"moniteur",
        r"monitoring",
        r"ecg",
        r"oxym",
        r"tensio",
        r"aspirat",
        r"ventilat",
        r"endoscope",
        r"gastroscope",
    ],
    "Radiography / X-ray": [
        r"radiograph",
        r"radio",
        r"\brx\b",
    ],
    "Electrical components / power system": [
        r"batter",
        r"stabilis",
        r"onduleur",
        r"disjonct",
        r"rallonge",
        r"adaptateur",
        r"ampoule",
        r"panneau",
        r"circuit",
        r"installation",
        r"prise",
        r"inverseur",
        r"\bfil",
        r"convertisseur",
        r"r[ée]gulateur",
        r"regulateur",
    ],
    "Laundry / water / utility equipment": [
        r"lessiv",
        r"buander",
        r"lave",
        r"pompe",
        r"traitement d.?eau",
        r"chauffe.?eau",
        r"fer [aà] repasser",
    ],
}


CAUSE_PATTERNS = {
    "Voltage instability / fluctuation": [
        r"instab",
        r"variation",
        r"fluct",
        r"chute de tension",
        r"tension",
        r"surtension",
        r"faible intensit",
        r"intensit[ée]",
        r"courant faible",
    ],
    "Power cuts / abrupt restoration": [
        r"coupure",
        r"interruption",
        r"r[ée]tablissement",
        r"courant discontinu",
    ],
    "Short circuit / burned electronics": [
        r"court.?circuit",
        r"cours circuit",
        r"brul",
        r"br[ûu]l",
        r"grill",
        r"carte",
    ],
    "Insufficient power / no energy": [
        r"manque d.?[ée]lect",
        r"manque d.?energie",
        r"pas de source",
        r"insuffisance",
        r"impossibilit",
        r"groupe.*pas",
    ],
    "Lightning / atmospheric discharge": [
        r"foudre",
        r"antifoudre",
        r"d[ée]charge atmos",
    ],
    "Poor installation": [
        r"mauvaise installation",
        r"installation",
    ],
}


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).lower().strip()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.replace("’", "'").replace("`", "'")
    return text


def match_any(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def make_frequency(df: pd.DataFrame, columns: list[str], denominator: int) -> pd.DataFrame:
    rows = []
    for col in columns:
        n = int(df[col].sum())
        rows.append(
            {
                "category": col,
                "facilities": n,
                "pct_all_facilities": round(n / denominator * 100, 1),
                "pct_facilities_reporting_damage": round(n / max(1, int(df["reported_damage"].sum())) * 100, 1),
            }
        )
    return pd.DataFrame(rows).sort_values(["facilities", "category"], ascending=[False, True])


def plot_frequency(freq: pd.DataFrame, title: str, output: Path, top_n: int = 14) -> None:
    plot_df = freq.head(top_n).sort_values("facilities")
    fig, ax = plt.subplots(figsize=(10, 7))
    bars = ax.barh(plot_df["category"], plot_df["facilities"], color="#3268a8")
    ax.set_xlabel("Facilities mentioning category")
    ax.set_title(title, fontsize=14, weight="bold", pad=12)
    ax.grid(axis="x", color="#d0d0d0", linewidth=0.7, alpha=0.7)
    ax.spines[["top", "right", "left"]].set_visible(False)
    for bar in bars:
        width = bar.get_width()
        ax.text(width + 1, bar.get_y() + bar.get_height() / 2, f"{int(width)}", va="center", fontsize=9)
    plt.tight_layout()
    fig.savefig(output, dpi=250, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    TAB.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(INPUT)
    master = pd.read_csv(MASTER_INPUT)
    master_labels = master[["A8_FOSA", "A5_province", "A7_type", "equipment_damage_binary"]].copy()
    master_labels["facility_type"] = master_labels["A7_type"].map(FACILITY_TYPE_LABELS)
    master_labels["province"] = master_labels["A5_province"].map(PROVINCE_LABELS)
    df["reported_damage"] = (pd.to_numeric(df["H1_medequip"], errors="coerce") == 1).astype(int)
    df["equipment_failure_text"] = df["H1_a_medequip"].fillna("").astype(str)
    df["text_norm"] = df["equipment_failure_text"].map(normalize_text)

    # Collapse to one facility row while retaining all non-empty mentions from deduplicated respondents.
    facility = (
        df.groupby("A8_FOSA")
        .agg(
            reported_damage=("reported_damage", "max"),
            equipment_failure_text=(
                "equipment_failure_text",
                lambda x: " | ".join(sorted(set(v.strip() for v in x if str(v).strip() and str(v).lower() != "nan"))),
            ),
        )
        .reset_index()
    )
    facility = facility.drop(columns=["reported_damage"]).merge(
        master_labels[["A8_FOSA", "province", "facility_type", "equipment_damage_binary"]],
        on="A8_FOSA",
        how="right",
    )
    facility["reported_damage"] = (facility["equipment_damage_binary"].fillna(0) == 1).astype(int)
    facility["equipment_failure_text"] = facility["equipment_failure_text"].fillna("")
    facility["text_norm"] = facility["equipment_failure_text"].map(normalize_text)

    category_cols = []
    for category, patterns in CATEGORY_PATTERNS.items():
        facility[category] = facility["text_norm"].map(lambda text, pats=patterns: int(match_any(text, pats)))
        category_cols.append(category)

    cause_cols = []
    for cause, patterns in CAUSE_PATTERNS.items():
        facility[cause] = facility["text_norm"].map(lambda text, pats=patterns: int(match_any(text, pats)))
        cause_cols.append(cause)

    equipment_freq = make_frequency(facility, category_cols, len(facility))
    cause_freq = make_frequency(facility, cause_cols, len(facility))
    equipment_freq.to_csv(TAB / "equipment_failure_category_frequency.csv", index=False)
    cause_freq.to_csv(TAB / "equipment_failure_cause_frequency.csv", index=False)

    facility[
        ["A8_FOSA", "province", "facility_type", "reported_damage", "equipment_failure_text"]
        + category_cols
        + cause_cols
    ].to_csv(TAB / "equipment_failure_coded_facility_mentions.csv", index=False)

    by_type = []
    for group, g in facility.groupby("facility_type"):
        freq = make_frequency(g, category_cols, len(g))
        freq.insert(0, "facility_type", group)
        by_type.append(freq)
    pd.concat(by_type, ignore_index=True).to_csv(TAB / "equipment_failure_category_by_facility_type.csv", index=False)

    by_province = []
    for group, g in facility.groupby("province"):
        freq = make_frequency(g, category_cols, len(g))
        freq.insert(0, "province", group)
        by_province.append(freq)
    pd.concat(by_province, ignore_index=True).to_csv(TAB / "equipment_failure_category_by_province.csv", index=False)

    plot_frequency(
        equipment_freq,
        "Reported medical equipment failures by equipment category",
        FIG / "fig_equipment_failure_categories.png",
    )
    plot_frequency(
        cause_freq,
        "Reported causes/context in equipment-failure descriptions",
        FIG / "fig_equipment_failure_causes.png",
    )

    summary = pd.DataFrame(
        [
            {"metric": "facilities", "value": len(facility)},
            {"metric": "facilities_reporting_medical_equipment_damage", "value": int(facility["reported_damage"].sum())},
            {
                "metric": "pct_facilities_reporting_medical_equipment_damage",
                "value": round(facility["reported_damage"].mean() * 100, 1),
            },
            {"metric": "facilities_with_nonempty_failure_text", "value": int((facility["text_norm"] != "").sum())},
        ]
    )
    summary.to_csv(TAB / "equipment_failure_summary.csv", index=False)
    print(summary.to_string(index=False))
    print(FIG / "fig_equipment_failure_categories.png")
    print(FIG / "fig_equipment_failure_causes.png")


if __name__ == "__main__":
    main()
