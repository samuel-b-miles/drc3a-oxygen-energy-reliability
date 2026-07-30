# Repository Architecture

This private repository is the executable source of truth for DRC3a analysis. Google Drive remains the human-readable source of truth for canonical seed documents, drafts, source PDFs, and team coordination.

## Intended Shape

```text
drc3a-oxygen-energy-reliability/
├── README.md
├── requirements.txt
├── config/
├── data/
│   ├── raw/
│   ├── intermediate/
│   ├── clean/
│   ├── external/
│   └── dictionaries/
├── src/
├── scripts/
├── outputs/
├── figures/
├── sources/
├── docs/
├── checks/
└── public_release/
```

## What Each Layer Means

`data/raw/` stores controlled original inputs restored from Google Drive. It is private and ignored by git.

`data/intermediate/` stores row-level working products between raw input and analysis-ready datasets. Private intermediates are ignored unless explicitly approved.

`data/clean/` stores analysis-ready files. In this private repo, some approved clean files may be local only. In a public clone, this layer should be anonymized, minimized, or replaced by access instructions.

`data/dictionaries/` stores variable dictionaries, coding maps, and de-identification notes. This should become one of the most important publication assets.

`src/` stores the actual analysis code. Current scripts cover facility master construction, deduplication audit, uptime reconstruction, energy-oxygen associations, equipment failure, cost quality, solar/generator capacity, econometric panels, and figure builds.

`scripts/` stores thin workflow entrypoints, especially `scripts/run_all.py`.

`outputs/` stores generated tables and figures from analysis runs. Keep aggregate manuscript-facing outputs here. Avoid committing row-level outputs.

`figures/` stores literature-review and conceptual figures that are not direct outputs of the DRC2 data pipeline.

`sources/` stores source indexes and claim maps, not bulky PDFs or private manuscript files.

`checks/` stores reproducibility and privacy checks.

`public_release/` stages decisions for a later public clone associated with journal submission or publication.

## Private-to-Public Clone Logic

The private repo can be broad: it may reference controlled Drive docs, local raw inputs, and draft artifacts. The public clone should be narrow: enough to reproduce published claims without exposing raw survey records or controlled documents.

Recommended public clone contents:

- `src/`, `scripts/`, `checks/`
- `config/` manifests with private paths removed
- `data/dictionaries/`
- anonymized or aggregate data releases
- final manuscript figures and aggregate result tables
- `docs/reviewer-reproduction.md`

Recommended private-only contents:

- raw survey exports
- respondent-level data
- facility-level data with identifiable fields
- deduplication candidate clusters
- uncontrolled free-text responses
- copyrighted PDFs and draft manuscript exports

## Current Analysis Threads

- High-N descriptive structure: energy and oxygen regimes by facility type and province.
- Uptime and reliability reconstruction: outage definitions and v1 uptime/reliable indicators.
- Energy predictors of oxygen: logistic screens, cross-validated AUC, and association tests.
- Equipment failure bridge: frequency, categories, causes, and relationship to energy/oxygen regimes.
- Second-wave high-T bridge: framing what cross-sectional DRC2 can suggest but not resolve without longitudinal telemetry.

## Next Repository Hardening Steps

1. Add `config/analysis_manifest.yml` with every script, expected input, and expected output.
2. Add `data/dictionaries/drc2_variable_dictionary.csv`.
3. Move approved clean analytical datasets into `data/clean/private/` locally and keep them ignored.
4. Add a reviewer-facing `docs/reviewer-reproduction.md`.
5. Add tests that verify row counts, key denominators, and figure/table build completeness.
