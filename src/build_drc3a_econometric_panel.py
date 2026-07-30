#!/usr/bin/env python3
"""Build DRC3a econometric-style result panels from analysis outputs."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
PANEL_DIR = OUT / "drc3a_econometric_panel"


OUTCOMES = [
    ("has_any_oxygen", "Any O2"),
    ("has_concentrator", "Conc."),
    ("has_multi_oxygen", "Multi O2"),
    ("has_psa_any", "PSA O2"),
    ("cylinder_any", "Cyl."),
    ("concentrator_no_cylinder", "Conc. only"),
    ("concentrator_vs_cylinder_among_oxygen", "Conc. vs cyl."),
    ("equipment_damage_binary", "Equip. damage"),
]

EXPOSURES = [
    ("has_grid", "Grid present"),
    ("has_generator", "Generator present"),
    ("has_solar", "Solar present"),
    ("two_plus_energy_sources", "2+ energy sources"),
    ("three_energy_sources", "3 energy sources"),
    ("grid_plus_backup", "Grid + backup"),
    ("bad_power_high", "Bad-power days > median"),
    ("outage_hours_high", "Outage hours > median"),
    ("reliable_v1_917", "Reliable v1"),
    ("reliable_v3_917", "Reliable 3-day"),
]

CAT_ROWS = [
    ("n_energy_sources", "Energy source count"),
    ("energy_profile", "Energy profile"),
    ("grid_architecture", "Grid architecture"),
]


def stars(p: float | None) -> str:
    if p is None or pd.isna(p):
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


def p_text(p: float | None) -> str:
    if p is None or pd.isna(p):
        return ""
    if p < 0.001:
        return "p<.001"
    return f"p={p:.3f}".replace("0.", ".")


def or_cell(row: pd.Series | None) -> str:
    if row is None:
        return ""
    return f"{row.odds_ratio:.2f}{stars(row.p_value)}\n[{row.ci_low:.2f}, {row.ci_high:.2f}]\n{p_text(row.p_value)}"


def chi_cell(row: pd.Series | None) -> str:
    if row is None:
        return ""
    return f"chi2={row.chi2:.1f}{stars(row.p_value)}\n{p_text(row.p_value)}"


def markdown_escape(value: object) -> str:
    text = str(value) if value is not None else ""
    return text.replace("|", "\\|").replace("\n", "<br>")


def write_markdown_table(panel: pd.DataFrame, path: Path) -> None:
    lines = []
    header = "| " + " | ".join(markdown_escape(col) for col in panel.columns) + " |"
    divider = "| " + " | ".join("---" for _ in panel.columns) + " |"
    lines.extend([header, divider])
    for _, row in panel.iterrows():
        lines.append("| " + " | ".join(markdown_escape(row[col]) for col in panel.columns) + " |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    PANEL_DIR.mkdir(parents=True, exist_ok=True)

    binary = pd.read_csv(OUT / "drc2_energy_predictors/tables/binary_energy_predictor_odds_ratios.csv")
    categorical = pd.read_csv(OUT / "drc2_energy_predictors/tables/categorical_energy_predictor_tests.csv")
    reliability = pd.read_csv(OUT / "drc2_uptime/tables/energy_architecture_vs_reliable_v1_tests.csv")
    rel_auc = pd.read_csv(OUT / "drc2_uptime/tables/energy_architecture_predicts_reliable_v1_auc.csv")
    uptime_r2 = pd.read_csv(OUT / "drc2_uptime/tables/energy_architecture_predicts_uptime_v1_r2.csv")
    cv_auc = pd.read_csv(OUT / "drc2_energy_predictors/tables/cross_validated_prediction_auc.csv")

    rows: list[dict[str, str]] = []
    columns = ["Panel / test"] + [label for _, label in OUTCOMES] + ["Reliability / uptime"]

    for exposure, label in EXPOSURES:
        out = {"Panel / test": f"Panel A. OR: {label}"}
        for outcome, out_label in OUTCOMES:
            match = binary[(binary["exposure"] == exposure) & (binary["outcome"] == outcome)]
            out[out_label] = or_cell(match.iloc[0]) if not match.empty else ""
        out["Reliability / uptime"] = ""
        rows.append(out)

    for predictor, label in CAT_ROWS:
        out = {"Panel / test": f"Panel B. chi2: {label}"}
        for outcome, out_label in OUTCOMES:
            match = categorical[(categorical["row_var"] == predictor) & (categorical["outcome"] == outcome)]
            out[out_label] = chi_cell(match.iloc[0]) if not match.empty else ""
        rel_match = reliability[reliability["predictor"] == predictor]
        if not rel_match.empty:
            r = rel_match.iloc[0]
            out["Reliability / uptime"] = f"V={r.cramers_v:.2f}{stars(r.p_value)}\n{p_text(r.p_value)}"
        else:
            out["Reliability / uptime"] = ""
        rows.append(out)

    for predictor, label in [
        ("has_grid", "Grid present"),
        ("has_generator", "Generator present"),
        ("has_solar", "Solar present"),
        ("two_plus_energy_sources", "2+ energy sources"),
        ("three_energy_sources", "3 energy sources"),
        ("grid_plus_backup", "Grid + backup"),
    ]:
        out = {"Panel / test": f"Panel C. reliable v1: {label}"}
        for _, out_label in OUTCOMES:
            out[out_label] = ""
        match = reliability[reliability["predictor"] == predictor]
        if not match.empty:
            r = match.iloc[0]
            out["Reliability / uptime"] = f"chi2={r.chi2:.1f}{stars(r.p_value)}; V={r.cramers_v:.2f}\n{p_text(r.p_value)}"
        rows.append(out)

    for pred_label, row_label in [
        ("source_flags", "Panel D. CV AUC: source flags"),
        ("source_flags_plus_reliability", "Panel D. CV AUC: + reliability recall"),
        ("source_flags_reliability_context", "Panel D. CV AUC: + facility/province"),
        ("energy_profile_context", "Panel D. CV AUC: energy/grid profile + context"),
        ("source_flags_uptime_context", "Panel D. CV AUC: + uptime + context"),
    ]:
        out = {"Panel / test": row_label}
        for outcome, out_label in OUTCOMES:
            match = cv_auc[(cv_auc["predictor_set_label"] == pred_label) & (cv_auc["outcome"] == outcome)]
            out[out_label] = f"AUC={match.iloc[0].cv_auc:.2f}" if not match.empty else ""
        out["Reliability / uptime"] = ""
        rows.append(out)

    out = {"Panel / test": "Panel E. reliable v1 prediction"}
    for _, out_label in OUTCOMES:
        out[out_label] = ""
    auc_bits = [f"{r.model}: AUC={r.cv_auc:.2f}" for _, r in rel_auc.iterrows()]
    out["Reliability / uptime"] = "; ".join(auc_bits)
    rows.append(out)

    out = {"Panel / test": "Panel E. uptime v1 prediction"}
    for _, out_label in OUTCOMES:
        out[out_label] = ""
    r2_bits = [f"{r.model}: R2={r.cv_r2:.3f}" for _, r in uptime_r2.iterrows()]
    out["Reliability / uptime"] = "; ".join(r2_bits)
    rows.append(out)

    panel = pd.DataFrame(rows, columns=columns)
    panel.to_csv(PANEL_DIR / "drc3a_econometric_style_matrix.csv", index=False)
    write_markdown_table(panel, PANEL_DIR / "drc3a_econometric_style_matrix.md")

    print(PANEL_DIR / "drc3a_econometric_style_matrix.csv")
    print(f"{len(panel)} rows x {len(panel.columns)} columns")


if __name__ == "__main__":
    main()
