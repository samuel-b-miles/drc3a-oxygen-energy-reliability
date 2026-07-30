# DRC2 Anonymization and Seed Architecture

## What Is Present Now

Observed local DRC2 assets include:

- Raw survey CSV: 565 submissions x 128 columns.
- Facility master: 491 facility rows x 126 columns.
- Deduplication audit summary: raw submissions, phone+FOSA deduplication, and remaining multi-respondent facilities.
- Variable inventory and domain summaries.
- Aggregate outputs for energy regimes, oxygen regimes, uptime/reliability, equipment failure, and energy-oxygen models.

The current repo is strongest as a private working repository, not yet a public release repository. It has enough structure for Sam G to understand the DRC3a high-N foundation and start DRC3b design thinking, but raw and facility-level data still need controlled handling.

## Identifier and Anonymization Findings

Direct identifiers are present in the raw survey export:

- `A1_email`
- `A2_name`
- `A3_phone`
- `_id`
- `_uuid`
- `meta/rootUuid`
- `_index`

Quasi-identifiers and linkage keys are also present:

- `A8_FOSA`
- `A5_province`
- `A6_zone`
- start/end/date/submission-time fields
- facility type and geographic strata when combined with oxygen/energy variables

Facility-level derived files are not automatically anonymous. `outputs/drc2_facility_master/facility_master.csv` still includes `A8_FOSA`, respondent names, raw row IDs, submission times, conflict fields, and other audit metadata. It should remain private/local until transformed.

Free-text/high-cardinality fields need review before sharing:

- medical equipment failure free text
- other problem descriptions
- registry fields
- rare cost or willingness-to-pay values
- any open response that may mention people, facilities, places, brands, or events

## Missing Anonymization Keys

The important missing piece is a formal linkage system:

- stable anonymous facility ID, for example `drc2_facility_0001`
- private crosswalk from anonymous ID to `A8_FOSA` or official facility name
- respondent-level anonymous ID if respondent-level disagreement is analyzed
- variable-level release class
- cell-size suppression policy for province x facility type x oxygen/energy strata
- free-text redaction and coding protocol
- role-priority or reconciliation policy for multi-respondent facilities

The crosswalk should live outside git, ideally in controlled Drive or a secure local/private store. The repo should contain only the rules, not the key.

## Recommended Data Products

Create three distinct DRC2 datasets, each with a different access policy:

1. `raw_submissions_private`
   - one row per submitted survey
   - contains direct identifiers and raw Kobo metadata
   - private only, never committed

2. `respondent_sample_private`
   - one row per phone-clean + facility pair after the speedrun deduplication rule
   - useful for respondent disagreement and human-infrastructure questions
   - private only unless heavily de-identified

3. `facility_master_private`
   - one row per facility after variable-family reconciliation
   - core high-N DRC3a analytical dataset
   - may later produce an anonymized or aggregate public version

Potential public/reviewer dataset:

4. `facility_master_release`
   - anonymous facility ID
   - no respondent identifiers
   - no direct facility name or raw `A8_FOSA`
   - generalized geography if needed
   - coded/aggregated free-text variables
   - cell-size and rare-category suppression applied

A first internal release candidate now exists at `data/clean/drc2_facility_master_release_candidate.csv`. It uses anonymous facility IDs and excludes direct respondent identifiers, raw facility IDs, facility zone, catchment population, raw row IDs, submission times, and conflict-field detail strings. It is useful for Sam G's private DRC3b spin-up, but it is not yet approved as a public publication dataset.

## Seed Architecture for Sam G / DRC3b

For Sam G, the most useful seed is not raw data first. It is a legible bridge from DRC3a to DRC3b:

- `docs/analysis-inventory.md`: what analyses exist and where outputs live.
- `docs/drc2-anonymization-and-seed-architecture.md`: what can and cannot be shared.
- `config/data_sources.yml`: where controlled assets live and how they should be treated.
- `config/analysis_manifest.yml`: current pipeline map.
- `config/figure_manifest.yml`: current figure map.
- `data/dictionaries/drc2_anonymization_variable_map.csv`: variable-level release risk map.
- `outputs/drc2_data_ingestion_audit/`: schema-level audit without exposed values.
- `outputs/drc2_high_n_mockup/`, `outputs/drc2_uptime/`, `outputs/drc2_energy_predictors/`, `outputs/drc2_equipment_failure/`: aggregate outputs Sam can inspect immediately.

This gives Sam a human-readable and machine-readable launchpad while keeping sensitive files out of git.

## Recommendation on Ingesting Raw Data Into the Repo

Do not commit raw DRC2 data to git, even private GitHub, until the sharing and publication posture is settled.

Do stage raw data locally under ignored folders when needed:

- `data/raw/private/`
- `data/intermediate/private/`
- `data/clean/private/`

Then use tracked manifests and dictionaries to tell collaborators what exists, where to obtain access, and what scripts expect. That makes the repo useful without turning GitHub into the data vault.

## Immediate Next Steps

1. Create a private facility crosswalk outside git.
2. Generate `data/clean/private/facility_master_private.csv` from the current facility master.
3. Review `data/clean/drc2_facility_master_release_candidate.csv` for rare strata and cell-size suppression.
4. Add a data dictionary for the high-N DRC3a variables used in figures and regressions.
5. Add checks that fail if direct identifiers appear in release-candidate files.
