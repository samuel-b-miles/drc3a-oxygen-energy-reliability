# DRC3 Oxygen Analysis

Reproducible analysis workspace for the DRC health-facility energy, reliability, equipment damage, and oxygen-access results used in the DRC3a manuscript draft.

## Current Status

This public repository contains analysis code, credited source manifests, deidentified electrical records, and aggregate survey results for DRC3a. Original survey answers, personal identifiers, raw facility/sensor crosswalks, and controlled source files remain outside Git. A named hospital case and canonical source references limit anonymity; the released electrical packages are deidentified rather than irreversibly anonymous.

Google Drive remains the human-readable source of truth for manuscript drafts, canonical seed documents, and controlled source data. This repository is the executable source of truth for reproducible calculations and manuscript figures.

## Auditable data collections

- [Ndosho collection](data/collections/ndosho/README.md): Charlie Huang's preserved kWh workbook, generator/fuel registers, all 13 available HOPmeter load files, and paired PowerWatch references.
- [Goma event exports](data/collections/goma/powerwatch/README.md): five unformatted dashboard exports covering 14 January–8 February 2025, with source hashes and 430,560 pseudonymous measurement records.
- [First descriptive event figure](outputs/event_figure/figure_1_event_descriptive.pdf) and [updated collection timeline](outputs/data_timeline/drc3a_collection_timeline.pdf).
- [DRC2 equipment-answer audit](outputs/drc2_failure_audit/README.md): reproduced legacy coding, a narrower concentrator category, and controlled answer-to-label provenance.

Start with [reproduction commands and evidence limits](docs/auditable-data-packages.md). The event figure describes exported voltage; it does not establish oxygen flow or uninterrupted clinical service. Full paired PowerWatch coverage from 2022 to the present remains an acquisition and coverage-audit target.

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

## Repository Organization

The public repository separates released research packages from controlled inputs:

- `data/`: local data staging, with raw and private row-level files ignored by git
- `src/`: analysis code for facility master construction, uptime, energy-oxygen models, equipment failure, and figures
- `scripts/`: thin workflow runners, including `scripts/run_all.py`
- `outputs/`: generated aggregate result tables and manuscript-facing figures
- `figures/`: literature and conceptual figures not directly produced by the DRC2 data pipeline
- `sources/`: lightweight source indexes and claim maps; bulky PDFs stay in Drive
- `config/`: analysis, figure, data-source, and release manifests
- `checks/`: reproducibility and privacy checks
- `public_release/`: staging notes for the later public clone
- `docs/`: pipeline notes, decisions, Drive links, and reproducibility planning

Start with:

- `docs/repository-architecture.md`
- `docs/analysis-inventory.md`
- `docs/publication-reproducibility-plan.md`
- `config/analysis_manifest.yml`
- `config/figure_manifest.yml`

Run the first hygiene check with:

```bash
python checks/check_repo_hygiene.py
```

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
