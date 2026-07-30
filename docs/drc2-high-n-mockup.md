# DRC2 High-N Mockup

This first-pass package uses the deduplicated `facility_master` table: one row per `A8_FOSA` facility. It is suitable for exploration and manuscript design, with the caveat that the Kobo choice labels and facility-key labels should be added before publication-grade tables.

## Dataset

- Facilities: 491
- Facilities with any oxygen source: 341 (69.5%)
- Facilities with concentrators: 313 (63.7%)
- Facilities with 2+ oxygen sources: 152 (31.0%)
- Facilities with 2+ energy sources: 324 (66.0%)

## Main Tables

- Sample profile: `/Users/samuelmiles/Documents/DRC3 - Oxygen/outputs/drc2_high_n_mockup/tables/table_1_sample_profile.csv`
- Energy profiles: `/Users/samuelmiles/Documents/DRC3 - Oxygen/outputs/drc2_high_n_mockup/tables/table_2_energy_profiles.csv`
- Oxygen profiles: `/Users/samuelmiles/Documents/DRC3 - Oxygen/outputs/drc2_high_n_mockup/tables/table_3_oxygen_profiles.csv`
- Energy by facility type: `/Users/samuelmiles/Documents/DRC3 - Oxygen/outputs/drc2_high_n_mockup/tables/table_4_energy_profile_by_facility_type_code.csv`
- Oxygen by facility type: `/Users/samuelmiles/Documents/DRC3 - Oxygen/outputs/drc2_high_n_mockup/tables/table_5_oxygen_profile_by_facility_type_code.csv`
- Association tests: `/Users/samuelmiles/Documents/DRC3 - Oxygen/outputs/drc2_high_n_mockup/tables/table_8_association_tests.csv`
- Logistic models: `/Users/samuelmiles/Documents/DRC3 - Oxygen/outputs/drc2_high_n_mockup/tables/table_9_logistic_models.csv`
- Binary odds-ratio screen: `/Users/samuelmiles/Documents/DRC3 - Oxygen/outputs/drc2_high_n_mockup/tables/table_10_binary_odds_ratio_screen.csv`

## Figures

- Energy regimes by facility type: `/Users/samuelmiles/Documents/DRC3 - Oxygen/outputs/drc2_high_n_mockup/figures/fig_1_energy_regimes_by_facility_type.png`
- Oxygen regimes by facility type: `/Users/samuelmiles/Documents/DRC3 - Oxygen/outputs/drc2_high_n_mockup/figures/fig_2_oxygen_regimes_by_facility_type.png`
- Oxygen access by energy-source complexity: `/Users/samuelmiles/Documents/DRC3 - Oxygen/outputs/drc2_high_n_mockup/figures/fig_3_oxygen_access_by_energy_complexity.png`
- Energy regime x oxygen regime heatmap: `/Users/samuelmiles/Documents/DRC3 - Oxygen/outputs/drc2_high_n_mockup/figures/fig_4_energy_oxygen_regime_heatmap.png`

## Association Tests

| Row variable | Column variable | chi-square | df | p-value | n |
| --- | --- | ---: | ---: | ---: | ---: |
| `n_energy_sources` | `has_any_oxygen` | 79.847 | 3 | 3.31e-17 | 491 |
| `n_energy_sources` | `has_concentrator` | 90.433 | 3 | 1.77e-19 | 491 |
| `n_energy_sources` | `has_multi_oxygen` | 43.042 | 3 | 2.41e-09 | 491 |
| `energy_profile` | `oxygen_profile` | 222.747 | 70 | 8.08e-18 | 491 |
| `grid_architecture` | `has_any_oxygen` | 30.907 | 4 | 3.2e-06 | 491 |
| `has_generator` | `has_psa_any` | 3.501 | 1 | 0.0613 | 491 |

## First Interpretation

The descriptive results should be read as facility-regime evidence. Energy-source complexity, energy profile, and grid architecture are visibly patterned with oxygen access, but this is not causal evidence. The association models test whether the relationship survives simple adjustment for facility type and province codes.

The key DRC3a move is to use this high-N package to show that oxygen access is patterned by energy regime, then use the high-T case work to show why cross-sectional source categories are incomplete without longitudinal voltage, outage, generator, load, and human-operation evidence.

## Caveats Before Manuscript Use

- Province and facility-type values are still coded because choice-list labels were not available locally.
- Facility-master reconciliation uses `any yes` for binary infrastructure presence and median/max/latest summaries for count/cost/reliability variables.
- Cost variables need currency and outlier review before substantive claims.
- Two adjusted logistic models failed in this first pass, likely because sparse coded province/type cells create separation; use the binary odds-ratio screen and chi-square tests as the current reliable association layer.
- Regression language should remain associational.
