# DRC2 Asset Schema Audit

Generated for repository seeding and anonymization planning.

## raw_survey_csv
- Path: `/Users/samuelmiles/Downloads/drc2 survey_ Enquête_sur_la_Qualité_et_la_Fiabilité_de_lÉlectricité__Établissements_de_Santé_en_RDC_-_latest_version_-_False_-_2026-04-07-21-25-03.xlsx - Enquête sur la Qualité et la... (2).csv`
- Exists: True
- Size: 357,574 bytes
- Shape: 565 rows x 128 columns
- Identifier-like columns: 25
  - start; end; date; A1_email; A2_name; A3_phone; A5_province; A6_zone; A8_FOSA; B1_grid; B1_grid_o; B2_grid_date; B3_grid_cost; C3_1_gen_date; C3_2_gen_date; C3_3_gen_date; D2_solar_date; F8a_2_timeout; F8b_2_timeout; F8c_2_timeout
- Value-pattern risk columns: 15
  - `A1_email`: email_pattern, high_cardinality; non-null=565; unique=519
  - `A2_name`: email_pattern, high_cardinality; non-null=565; unique=527
  - `A3_phone`: phone_pattern, high_cardinality; non-null=565; unique=512
  - `A8_FOSA`: phone_pattern; non-null=565; unique=491
  - `F5_o_baddays_freq`: high_cardinality; non-null=71; unique=64
  - `H1_a_medequip`: high_cardinality; non-null=263; unique=245
  - `J1_o_ptreg`: high_cardinality; non-null=24; unique=22
  - `J2_o_wardreg`: high_cardinality; non-null=92; unique=84
  - `J3_death_o`: high_cardinality; non-null=119; unique=113
  - `I2_wtp`: phone_pattern; non-null=565; unique=46
  - `I3_otherprob`: high_cardinality; non-null=545; unique=513
  - `_id`: phone_pattern, high_cardinality; non-null=565; unique=565
  - `_uuid`: phone_pattern, high_cardinality; non-null=565; unique=565
  - `meta/rootUuid`: phone_pattern, high_cardinality; non-null=565; unique=565
  - `_index`: phone_pattern, high_cardinality; non-null=565; unique=565

## facility_master
- Path: `/Users/samuelmiles/Documents/DRC3 - Oxygen/outputs/drc2_facility_master/facility_master.csv`
- Exists: True
- Size: 218,203 bytes
- Shape: 491 rows x 126 columns
- Identifier-like columns: 22
  - A8_FOSA; facility_rows; respondent_phones; respondent_names; respondent_roles; raw_row_ids; submission_times; multi_respondent_flag; A5_province; A5_province_conflict; A6_zone; A6_zone_conflict; grid_type_label; grid_type_label_conflict; grid_architecture; grid_architecture_conflict; has_grid; has_grid_conflict; grid_cost_median; grid_cost_max
- Value-pattern risk columns: 6
  - `A8_FOSA`: phone_pattern, high_cardinality; non-null=491; unique=491
  - `respondent_names`: email_pattern, high_cardinality; non-null=491; unique=488
  - `raw_row_ids`: phone_pattern, high_cardinality; non-null=491; unique=491
  - `I2_wtp_max`: phone_pattern; non-null=491; unique=45
  - `I2_wtp_latest`: phone_pattern; non-null=491; unique=45
  - `conflict_fields`: high_cardinality; non-null=24; unique=24

## facility_master_conflicts
- Path: `/Users/samuelmiles/Documents/DRC3 - Oxygen/outputs/drc2_facility_master/facility_master_conflicts.csv`
- Exists: True
- Size: 18,319 bytes
- Shape: 24 rows x 126 columns
- Identifier-like columns: 22
  - A8_FOSA; facility_rows; respondent_phones; respondent_names; respondent_roles; raw_row_ids; submission_times; multi_respondent_flag; A5_province; A5_province_conflict; A6_zone; A6_zone_conflict; grid_type_label; grid_type_label_conflict; grid_architecture; grid_architecture_conflict; has_grid; has_grid_conflict; grid_cost_median; grid_cost_max
- Value-pattern risk columns: 6
  - `A8_FOSA`: phone_pattern, high_cardinality; non-null=24; unique=24
  - `respondent_names`: high_cardinality; non-null=24; unique=24
  - `raw_row_ids`: high_cardinality; non-null=24; unique=24
  - `I2_wtp_max`: phone_pattern; non-null=24; unique=12
  - `I2_wtp_latest`: phone_pattern; non-null=24; unique=11
  - `conflict_fields`: high_cardinality; non-null=24; unique=24

## raw_submissions_derived
- Path: `/Users/samuelmiles/Documents/DRC3 - Oxygen/outputs/drc2_facility_master/raw_submissions.csv`
- Exists: True
- Size: 495,640 bytes
- Shape: 565 rows x 163 columns
- Identifier-like columns: 34
  - start; end; date; A1_email; A2_name; A3_phone; A5_province; A6_zone; A8_FOSA; B1_grid; B1_grid_o; B2_grid_date; B3_grid_cost; C3_1_gen_date; C3_2_gen_date; C3_3_gen_date; D2_solar_date; F8a_2_timeout; F8b_2_timeout; F8c_2_timeout
- Value-pattern risk columns: 18
  - `A1_email`: email_pattern, high_cardinality; non-null=565; unique=519
  - `A2_name`: email_pattern, high_cardinality; non-null=565; unique=527
  - `A3_phone`: phone_pattern, high_cardinality; non-null=565; unique=512
  - `A8_FOSA`: phone_pattern; non-null=565; unique=491
  - `F5_o_baddays_freq`: high_cardinality; non-null=71; unique=64
  - `H1_a_medequip`: high_cardinality; non-null=263; unique=245
  - `J1_o_ptreg`: high_cardinality; non-null=24; unique=22
  - `J2_o_wardreg`: high_cardinality; non-null=92; unique=84
  - `J3_death_o`: high_cardinality; non-null=119; unique=113
  - `I2_wtp`: phone_pattern; non-null=565; unique=46
  - `I3_otherprob`: high_cardinality; non-null=545; unique=513
  - `_id`: phone_pattern, high_cardinality; non-null=565; unique=565
  - `_uuid`: phone_pattern, high_cardinality; non-null=565; unique=565
  - `meta/rootUuid`: phone_pattern, high_cardinality; non-null=565; unique=565
  - `_index`: phone_pattern, high_cardinality; non-null=565; unique=565

## dedup_summary
- Path: `/Users/samuelmiles/Documents/DRC3 - Oxygen/outputs/drc2_dedup_audit/dedup_summary.json`
- Exists: True
- Size: 652 bytes

## variable_inventory
- Path: `/Users/samuelmiles/Documents/DRC3 - Oxygen/outputs/drc2_variable_exploration/drc2_variable_inventory.csv`
- Exists: True
- Size: 31,819 bytes
- Shape: 128 rows x 12 columns
- Identifier-like columns: 0
- Value-pattern risk columns: 6
  - `order`: phone_pattern, high_cardinality; non-null=128; unique=128
  - `column`: high_cardinality; non-null=128; unique=128
  - `non_missing`: phone_pattern; non-null=128; unique=33
  - `missing`: phone_pattern; non-null=128; unique=33
  - `unique_values`: phone_pattern; non-null=128; unique=59
  - `top_values`: email_pattern, high_cardinality; non-null=120; unique=119
