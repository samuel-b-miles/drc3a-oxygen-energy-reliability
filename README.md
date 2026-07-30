# DRC3 Oxygen Analysis

Reproducible analysis workspace for the DRC health-facility energy, reliability, equipment damage, and oxygen-access results used in the DRC3a manuscript draft.

## Current Status

This repository contains the analysis scripts and generated aggregate tables/figures for the DRC3a manuscript workflow. Before any public release, confirm that the shared data bundle is anonymized and excludes respondent-level identifiers, raw submissions, phone numbers, precise facility identifiers, and free-text fields that could identify individuals or facilities.

Google Drive remains the human-readable source of truth for manuscript drafts, canonical seed documents, and controlled source data. This repository is the executable source of truth for reproducible calculations and manuscript figures.

## Reproduce The Main Tables

Run from the project root:

```bash
python src/build_drc2_facility_master.py
python src/calculate_drc2_uptime.py
python src/model_energy_predictors_of_oxygen.py
python src/analyze_equipment_failure_frequency.py
python src/build_drc3a_econometric_panel.py
```

The econometric-style result matrix is written to:

- `outputs/drc3a_econometric_panel/drc3a_econometric_style_matrix.csv`
- `outputs/drc3a_econometric_panel/drc3a_econometric_style_matrix.md`

## Data Access

Raw survey submissions and facility-level analytical files are intentionally excluded from git. Place approved local inputs under `data/` or restore them from the controlled Google Drive workspace before rebuilding the analysis.

## Interpretation Notes

The statistical tests are exploratory and cross-sectional. Odds ratios and chi-square tests describe associations, not causal effects. Cross-validated AUC and R2 summarize predictive performance only.

Significance notation:

- `***` p < 0.001
- `**` p < 0.01
- `*` p < 0.05
- `~` p < 0.10
- blank means not statistically clear or not tested for that outcome

## Public Release Checklist

- Replace private/raw inputs with a documented anonymized analytical dataset.
- Add a data dictionary for every variable used in the analysis scripts.
- Confirm that free-text equipment-damage fields are redacted or aggregated.
- Confirm that facility names, respondent names, phone numbers, GPS/location details, and internal IDs are excluded or transformed.
- Run the commands above from a fresh clone and confirm outputs match.
