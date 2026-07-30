# DRC2 Facility Master Build

## Tables Created

- `raw_submissions.csv`: all raw survey submissions with helper fields.
- `respondent_sample.csv`: speed-run notebook deduplication, one row per `phone_clean + A8_FOSA`.
- `facility_master.csv`: one row per `A8_FOSA`, reconciled from `respondent_sample`.
- `facility_master_conflicts.csv`: facilities with multiple respondent rows or at least one reconciled-field conflict.

## Row Counts

- Raw submissions: 565
- Respondent sample rows: 518
- Facility master rows: 491
- Facilities with multiple respondent rows: 24
- Facilities with at least one conflict flag: 24

## Reconciliation Rules

- Identity fields use mode/first non-missing value and carry a conflict flag when respondents disagree.
- Binary infrastructure/access fields use `any yes`, equivalent to max across respondent rows, and carry conflict flags.
- Asset counts and capacities retain max, median, and conflict flags. The headline facility-master value should generally use max for stock/capacity.
- Reliability and cost variables retain median, max, latest, and conflict flags. Median is the safer descriptive default unless a role-priority rule is later approved.
- Free text and respondent identity fields are concatenated for audit, not treated as clean analytical categories.
- Energy and oxygen profiles are recomputed after reconciliation.

## Important Caveats

- The Kobo choice-list labels and facility-key file were not present locally in this session. This build therefore preserves coded province, role, and facility-type fields, while decoding only the grid and oxygen-payment fields reconstructed from the notebook.
- Facility names are only included if present in the source table or added later from a facility key.
- This is a first facility-master build for analysis planning. Publication-grade analysis should review conflict facilities and add label files when available.
