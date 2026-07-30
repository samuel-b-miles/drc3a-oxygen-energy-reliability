# DRC2 Survey Variable Exploration

Source file: `/Users/samuelmiles/Downloads/drc2 survey_ Enquête_sur_la_Qualité_et_la_Fiabilité_de_lÉlectricité__Établissements_de_Santé_en_RDC_-_latest_version_-_False_-_2026-04-07-21-25-03.xlsx - Enquête sur la Qualité et la... (2).csv`
Rows: 565
Columns: 128

## Domain Summary

| Domain | Variables | Median missing % | Ready descriptive | Ready numeric | Needs coding/review | Mostly missing |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Survey timing and notes | 6 | 50.0 | 0 | 0 | 3 | 3 |
| Facility identity and respondent metadata | 9 | 0.0 | 3 | 4 | 2 | 0 |
| Internet and grid electricity | 5 | 35.2 | 2 | 1 | 2 | 0 |
| Generator assets, use, and cost | 14 | 53.8 | 1 | 0 | 2 | 3 |
| Solar assets, finance, and quality | 13 | 37.2 | 3 | 4 | 2 | 2 |
| Charcoal use and cost | 9 | 37.2 | 6 | 1 | 1 | 1 |
| Outages, bad power days, and recall reliability | 18 | 8.8 | 8 | 8 | 1 | 0 |
| Maintenance and equipment failure | 8 | 8.8 | 7 | 0 | 0 | 1 |
| Medical oxygen equipment and oxygen access | 13 | 0.0 | 8 | 2 | 2 | 0 |
| Other derived or helper fields | 1 | 100.0 | 0 | 0 | 0 | 1 |
| Registers, mortality records, and morgue capacity | 15 | 43.7 | 10 | 0 | 3 | 1 |
| Willingness-to-pay, technical capacity, and operations | 6 | 4.0 | 3 | 1 | 2 | 0 |
| Submission metadata | 11 | 0.0 | 0 | 0 | 0 | 0 |

## First Analytical Reading

The DRC2 survey is analyzable as a facility-regime dataset. Its strongest immediate use for DRC3a is not one-off variables, but derived classifications that combine multiple variables into energy regimes, oxygen regimes, reliability burden, operating burden, and human infrastructure readiness.

Recommended first derived constructs:

- `facility_master`: province, health zone, facility type, facility identifier, catchment, respondent role.
- `energy_source_count`: grid, generator, solar, charcoal and other sources.
- `energy_regime`: no source, grid only, generator only, solar only, grid + generator, solar + generator, grid + solar, grid + solar + generator, other/hybrid.
- `backup_capacity`: generator count/capacity/autostart/use frequency plus solar battery presence/capacity.
- `reliability_burden`: outage days, outage hours, typical bad days, short-outage frequency, recall outage counts.
- `energy_cost_burden`: grid, generator, solar maintenance, charcoal cost variables after currency/outlier review.
- `oxygen_regime`: no oxygen, 5L/10L concentrators, cylinders/other oxygen sources where available, mixed oxygen access.
- `oxygen_energy_coupling`: oxygen regime crossed with energy regime, backup capacity, and reliability burden.
- `human_infrastructure`: technician availability, maintenance pathways, biomedical equipment failure variables, record/register availability.

## Existing Notebook Constructs To Preserve

The prior DRC2 notebook already contains several useful derived variables that should be ported into scripts rather than reinvented:

- `province_label`, `facility_type_label`, `role_label`, `wiring_label`, `solar_quality_label`: decoded labels from the Kobo/choice lists.
- `grid_type_code`, `grid_type_label`: grid provider/source type, with `B1_grid` treated as a grid-type variable rather than a yes/no field.
- `has_grid`: true grid connection, defined as any `B1_grid` value except `9 = No Grid`.
- `grid_architecture`: `Central Grid`, `Private / Concession Grid`, `Community Mini-grid`, `No Grid`, or `Other`.
- `has_generator`, `has_solar`: binary generator and solar indicators from `C1_gen` and `D1_solar`.
- `n_energy_sources`: count of grid, generator, and solar sources.
- `energy_profile`: combined source profile such as `Grid`, `Generator`, `Solar`, `Grid + Generator`, or `Grid + Generator + Solar`.
- `conc_5l`, `conc_10l`, `total_concentrators`, `has_concentrator`: oxygen concentrator stock variables.
- `has_psa_internal`, `has_psa_external`, `has_cylinders`: oxygen source indicators from the `H4_oxygen/*` select-multiple expansion.
- `oxygen_payment_label`, `oxygen_cost`: payment structure and reported oxygen cost.
- `grid_cost`, `generator_cost`, `solar_monthly_cost`, `solar_total_value`, `solar_maintenance_cost`: energy economics variables requiring unit/currency/outlier review.

These constructs line up well with the DRC3a result sequence: absence and hybridity, fragility, oxygen ecologies, oxygen-energy coupling, and operational burden.

## Priority Variable Domains For DRC3a

### Internet and grid electricity
- `B1_grid`: coded categorical numeric; missing 0.0%; energy regime classification; grid access/source analysis.
- `B2_grid_date`: free text / identifier; missing 35.2%; energy regime classification; grid access/source analysis.
- `B3_grid_cost`: continuous/count numeric; missing 35.2%; energy regime classification; grid access/source analysis.
- `B1_internet`: coded categorical numeric; missing 38.9%; energy regime classification; grid access/source analysis.
- `B1_grid_o`: free text / identifier; missing 87.6%; energy regime classification; grid access/source analysis.

### Generator assets, use, and cost
- `C1_gen`: coded categorical numeric; missing 0.0%; backup regime, operational burden, diesel/generator dependence.
- `C1_a_gencount`: coded categorical numeric; missing 53.6%; backup regime, operational burden, diesel/generator dependence.
- `C5_gen_cost`: continuous/count numeric; missing 53.6%; backup regime, operational burden, diesel/generator dependence.
- `C6_gen_frequse`: coded categorical numeric; missing 53.6%; backup regime, operational burden, diesel/generator dependence.
- `C7_gen_qual`: coded categorical numeric; missing 53.6%; backup regime, operational burden, diesel/generator dependence.
- `C2_1_gencapac`: continuous/count numeric; missing 53.8%; backup regime, operational burden, diesel/generator dependence.
- `C3_1_gen_date`: free text / identifier; missing 53.8%; backup regime, operational burden, diesel/generator dependence.
- `C4_1_gen_auto`: coded categorical numeric; missing 53.8%; backup regime, operational burden, diesel/generator dependence.
- `C2_2_gencapac`: continuous/count numeric; missing 85.5%; backup regime, operational burden, diesel/generator dependence.
- `C3_2_gen_date`: free text / identifier; missing 85.5%; backup regime, operational burden, diesel/generator dependence.
- `C4_2_genauto`: coded categorical numeric; missing 85.5%; backup regime, operational burden, diesel/generator dependence.
- `C2_3_gencapac`: coded categorical numeric; missing 97.5%; backup regime, operational burden, diesel/generator dependence.

### Solar assets, finance, and quality
- `D1_solar`: coded categorical numeric; missing 0.0%; solar/autonomy regime; finance and quality analysis.
- `D2_solar_date`: free text / identifier; missing 37.2%; solar/autonomy regime; finance and quality analysis.
- `D3_solar_panel`: continuous/count numeric; missing 37.2%; solar/autonomy regime; finance and quality analysis.
- `D4_solar_batt`: continuous/count numeric; missing 37.2%; solar/autonomy regime; finance and quality analysis.
- `D5_solar_qual`: coded categorical numeric; missing 37.2%; solar/autonomy regime; finance and quality analysis.
- `D6_solar_finance`: coded categorical numeric; missing 37.2%; solar/autonomy regime; finance and quality analysis.
- `D6_a_solar_totval`: continuous/count numeric; missing 37.2%; solar/autonomy regime; finance and quality analysis.
- `D4_a_solar_batt_age`: continuous/count numeric; missing 37.5%; solar/autonomy regime; finance and quality analysis.
- `D6_d_solar_maintadhoc`: continuous/count numeric; missing 61.1%; solar/autonomy regime; finance and quality analysis.
- `D4_solar_capac`: continuous/count numeric; missing 65.3%; solar/autonomy regime; finance and quality analysis.
- `D6_solar_funder`: free text / identifier; missing 86.2%; solar/autonomy regime; finance and quality analysis.
- `D6_c_solar_monthmaint`: continuous/count numeric; missing 91.0%; solar/autonomy regime; finance and quality analysis.

### Outages, bad power days, and recall reliability
- `F0_outage_sara`: coded categorical numeric; missing 8.8%; power reliability, fragility, outage-burden indices.
- `F1_outagedays`: coded categorical numeric; missing 8.8%; power reliability, fragility, outage-burden indices.
- `F2_outagehrs`: continuous/count numeric; missing 8.8%; power reliability, fragility, outage-burden indices.
- `F3_typicaldays`: coded categorical numeric; missing 8.8%; power reliability, fragility, outage-burden indices.
- `F4_baddays`: continuous/count numeric; missing 8.8%; power reliability, fragility, outage-burden indices.
- `F5_baddays_freq`: coded categorical numeric; missing 8.8%; power reliability, fragility, outage-burden indices.
- `F6_shortoutage`: coded categorical numeric; missing 8.8%; power reliability, fragility, outage-burden indices.
- `F8a_1_numout`: continuous/count numeric; missing 8.8%; power reliability, fragility, outage-burden indices.
- `F8a_2_timeout`: continuous/count numeric; missing 8.8%; power reliability, fragility, outage-burden indices.
- `F8a_3_typeday`: coded categorical numeric; missing 8.8%; power reliability, fragility, outage-burden indices.
- `F8b_1_numout`: continuous/count numeric; missing 8.8%; power reliability, fragility, outage-burden indices.
- `F8b_2_timeout`: continuous/count numeric; missing 8.8%; power reliability, fragility, outage-burden indices.

### Maintenance and equipment failure
- `G1_maint`: categorical text; missing 8.8%; human infrastructure and repair capacity.
- `G1_maint/1`: coded categorical numeric; missing 8.8%; human infrastructure and repair capacity.
- `G1_maint/2`: coded categorical numeric; missing 8.8%; human infrastructure and repair capacity.
- `G1_maint/3`: coded categorical numeric; missing 8.8%; human infrastructure and repair capacity.
- `G1_maint/4`: coded categorical numeric; missing 8.8%; human infrastructure and repair capacity.
- `G1_maint/99`: coded categorical numeric; missing 8.8%; human infrastructure and repair capacity.
- `G2_wiring`: coded categorical numeric; missing 46.9%; human infrastructure and repair capacity.
- `G1_o_maint`: categorical text; missing 97.3%; human infrastructure and repair capacity.

### Medical oxygen equipment and oxygen access
- `H2_10Lo2`: continuous/count numeric; missing 0.0%; oxygen regime classification and oxygen-energy coupling.
- `H3_5Lo2`: continuous/count numeric; missing 0.0%; oxygen regime classification and oxygen-energy coupling.
- `H4_oxygen`: coded categorical numeric; missing 0.0%; oxygen regime classification and oxygen-energy coupling.
- `H4_oxygen/1`: coded categorical numeric; missing 0.0%; oxygen regime classification and oxygen-energy coupling.
- `H4_oxygen/2`: coded categorical numeric; missing 0.0%; oxygen regime classification and oxygen-energy coupling.
- `H4_oxygen/3`: coded categorical numeric; missing 0.0%; oxygen regime classification and oxygen-energy coupling.
- `H4_oxygen/4`: coded categorical numeric; missing 0.0%; oxygen regime classification and oxygen-energy coupling.
- `H4_oxygen/99`: coded categorical numeric; missing 0.0%; oxygen regime classification and oxygen-energy coupling.
- `H1_medequip`: coded categorical numeric; missing 8.8%; oxygen regime classification and oxygen-energy coupling.
- `H5_o2_pay`: coded categorical numeric; missing 31.9%; oxygen regime classification and oxygen-energy coupling.
- `H1_a_medequip`: free text / identifier; missing 53.5%; oxygen regime classification and oxygen-energy coupling.
- `H5_o2_cost`: continuous/count numeric; missing 83.4%; oxygen regime classification and oxygen-energy coupling.

### Willingness-to-pay, technical capacity, and operations
- `I2_wtp`: continuous/count numeric; missing 0.0%; affordability, technical readiness, operational capacity.
- `I5_tech`: coded categorical numeric; missing 0.0%; affordability, technical readiness, operational capacity.
- `I3_otherprob`: free text / identifier; missing 3.5%; affordability, technical readiness, operational capacity.
- `I4_comment`: free text / identifier; missing 4.6%; affordability, technical readiness, operational capacity.
- `I1_theft`: coded categorical numeric; missing 35.2%; affordability, technical readiness, operational capacity.
- `I6_internet`: coded categorical numeric; missing 36.8%; affordability, technical readiness, operational capacity.

### Registers, mortality records, and morgue capacity
- `J1_ptreg`: coded categorical numeric; missing 0.0%; data quality, mortality-record availability, denominator readiness.
- `J3_deathreg`: coded categorical numeric; missing 0.0%; data quality, mortality-record availability, denominator readiness.
- `J4_morgue`: coded categorical numeric; missing 0.0%; data quality, mortality-record availability, denominator readiness.
- `J2_wardreg`: free text / identifier; missing 43.7%; data quality, mortality-record availability, denominator readiness.
- `J2_wardreg/1`: coded categorical numeric; missing 43.7%; data quality, mortality-record availability, denominator readiness.
- `J2_wardreg/2`: coded categorical numeric; missing 43.7%; data quality, mortality-record availability, denominator readiness.
- `J2_wardreg/3`: coded categorical numeric; missing 43.7%; data quality, mortality-record availability, denominator readiness.
- `J2_wardreg/4`: coded categorical numeric; missing 43.7%; data quality, mortality-record availability, denominator readiness.
- `J2_wardreg/5`: coded categorical numeric; missing 43.7%; data quality, mortality-record availability, denominator readiness.
- `J2_wardreg/6`: coded categorical numeric; missing 43.7%; data quality, mortality-record availability, denominator readiness.
- `J2_wardreg/99`: coded categorical numeric; missing 43.7%; data quality, mortality-record availability, denominator readiness.
- `J3_death_o`: free text / identifier; missing 78.9%; data quality, mortality-record availability, denominator readiness.

## Cautions

- Numeric coded categorical variables need labels/decoders before publication-grade interpretation.
- Slash columns such as `E1_a_charc_use/1` are select-multiple expansions and should be recombined carefully.
- Free-text `other` variables should be manually coded into controlled categories if used.
- Cost variables need currency, unit, and outlier review before substantive claims.
- Mortality/register variables should be treated first as data-readiness variables unless linked to validated mortality datasets.

## Suggested Next Script

`src/build_drc2_facility_master.py` should create a cleaned facility-level table with stable IDs, labels, and first-pass regime classifications.
