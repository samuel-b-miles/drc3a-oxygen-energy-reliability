# DRC2 Deduplication Audit

Source file: `/Users/samuelmiles/Downloads/drc2 survey_ Enquête_sur_la_Qualité_et_la_Fiabilité_de_lÉlectricité__Établissements_de_Santé_en_RDC_-_latest_version_-_False_-_2026-04-07-21-25-03.xlsx - Enquête sur la Qualité et la... (2).csv`

## Notebook Rule

The speed-run notebook does not deduplicate to one row per facility. It:

1. Cleans `A3_phone` into `phone_clean` by removing punctuation/non-digits and setting values shorter than 6 digits to missing.
2. Builds `completeness_score` as the count of non-missing values across ten core variables: `A5_province`, `A6_zone`, `A7_type`, `A8_FOSA`, `B1_grid`, `C1_gen`, `D1_solar`, `H2_10Lo2`, `H3_5Lo2`, and `H1_medequip`.
3. Sorts rows by `completeness_score` descending.
4. Drops duplicates on `phone_clean` + `A8_FOSA`, keeping the first row.

In plain language: it removes repeat submissions from the same phone number at the same facility, preferring the row with more complete core fields. It preserves multiple respondents at the same facility when they have different phone numbers.

## Notebook Version Check

The later file supplied as `DRc2 survey data speed run v3 (2) (1).ipynb` was checked against `DRc2 survey data speed run v3 (2).ipynb` and is byte-for-byte identical. The deduplication block and all audit conclusions therefore remain unchanged.

## Quantified Effect

- Raw rows: 565
- Raw unique FOSA IDs: 491
- Raw FOSA IDs with multiple rows: 65
- Notebook analytic rows: 518
- Notebook unique FOSA IDs: 491
- Rows removed by notebook rule: 47
- Rows remaining beyond one per FOSA: 27
- FOSA IDs still duplicated after notebook rule: 24

## Audit Judgment

The notebook rule is a useful first filter for exact or near-exact repeat submissions by the same respondent, but it is not sufficient for facility-level high-N analysis. DRC3a should not treat the notebook `analytic_sample` as a true facility master without a second reconciliation step.

Main risks:

- It preserves multiple actors at the same facility, which is useful for respondent-level disagreement but can double-count facilities in facility-level prevalence estimates.
- It does not use `_submission_time` as a tie-breaker, so equally complete repeated rows may not consistently keep the latest submission.
- It does not prioritize respondent role, even though some variables may be more reliable from technicians, administrators, or clinicians.
- It uses the same row-selection rule for all variables, but asset counts, outage perceptions, costs, and free-text comments may require different reconciliation rules.
- It does not create a transparent conflict flag for facilities where respondents disagree.

## Recommended Next Rule

Create three related tables:

- `raw_submissions`: all 565 raw rows.
- `respondent_sample`: notebook-style phone + FOSA deduplication, used for respondent-level perception and disagreement analysis.
- `facility_master`: one row per `A8_FOSA`, with variable-family-specific reconciliation rules and conflict flags.

Recommended facility-master reconciliation:

- Facility identity: use facility key / stable FOSA metadata.
- Binary infrastructure presence: use `max` across respondents, with a disagreement flag.
- Counts/capacities: use the most complete/latest respondent where plausible; also retain max and median audit fields.
- Costs/outage recall: use median across respondents or role-prioritized value; flag high disagreement.
- Free text: concatenate with respondent role and submission ID.
- Human infrastructure/perception variables: preserve respondent-level table and summarize disagreement rather than forcing a single truth too early.

## Audit Files

- `outputs/drc2_dedup_audit/raw_fosa_duplicate_clusters.csv`
- `outputs/drc2_dedup_audit/notebook_remaining_fosa_clusters.csv`
- `outputs/drc2_dedup_audit/phone_fosa_repeat_clusters.csv`
- `outputs/drc2_dedup_audit/dedup_summary.json`
