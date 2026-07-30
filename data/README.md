# Data Directory

This repository is the private analytical workspace for DRC3a. Data are separated by sensitivity and reproducibility role.

## Layout

- `raw/`: original controlled inputs copied or restored from Google Drive. These are not committed.
- `intermediate/`: script-generated working files used between raw inputs and clean analytical files.
- `clean/`: analysis-ready datasets. Private row-level files are not committed unless explicitly approved.
- `external/`: public reference datasets, boundary files, or lookup tables.
- `dictionaries/`: variable dictionaries, coding maps, de-identification notes, and provenance records.

## Rules

- Do not commit respondent names, phone numbers, exact facility identifiers, raw submissions, or unrestricted free text.
- Prefer aggregated tables in `outputs/` for manuscript-facing results.
- Any dataset intended for a later public clone needs a provenance note, de-identification decision, and rebuild path.
