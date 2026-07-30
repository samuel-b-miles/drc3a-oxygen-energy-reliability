# Analysis Inventory

This inventory links the analyses already performed to their current scripts and output folders.

| Analysis thread | Script(s) | Main outputs | Publication role |
| --- | --- | --- | --- |
| DRC2 facility master build | `src/build_drc2_facility_master.py` | `outputs/drc2_facility_master/` | Defines the high-N facility-level analysis frame and deduplication result |
| Variable exploration | `src/explore_drc2_variables.py` | `outputs/drc2_variable_exploration/` | Maps analyzable survey domains and candidate variables |
| Deduplication audit | `src/audit_drc2_dedup.py` | `outputs/drc2_dedup_audit/` | Documents duplicate submission logic and residual audit concerns |
| High-N energy/oxygen mockup | `src/analyze_drc2_high_n_mockup.py` | `outputs/drc2_high_n_mockup/` | Core descriptive tables and figures for facility type and province |
| Uptime reconstruction | `src/calculate_drc2_uptime.py` | `outputs/drc2_uptime/` | Links energy architecture to reliability and uptime |
| Energy predictors of oxygen | `src/model_energy_predictors_of_oxygen.py` | `outputs/drc2_energy_predictors/` | Tests associations between energy source architecture and oxygen regime |
| Equipment failure frequency | `src/analyze_equipment_failure_frequency.py` | `outputs/drc2_equipment_failure/` | Establishes equipment breakage as the practical energy-oxygen bridge |
| Equipment failure layers | `src/analyze_equipment_failure_layers.py` | `outputs/drc3a_equipment_failure_layers/` | Breaks failure reports down by energy, oxygen, reliability, and concentrator stock |
| Equipment damage associations | `src/analyze_equipment_damage_associations.py` | `outputs/drc3a_damage_associations/` | Tests damage/failure associations with energy and reliability variables |
| Solar/generator capacity audit | `src/audit_solar_generator_capacity.py` | `outputs/drc3a_solar_generator_audit/` | Checks technical plausibility of self-reported power capacity data |
| Cost data quality | `src/analyze_cost_data_quality.py` | `outputs/drc3a_cost_quality/` | Assesses whether cost fields are usable for DRC3a or need relegation |
| Econometric-style panel | `src/build_drc3a_econometric_panel.py` | `outputs/drc3a_econometric_panel/` | Condenses association results into a manuscript-style results matrix |
| v4 manuscript figures | `src/build_drc3a_v4_figures.py` | `outputs/v4_figures/` | Candidate figures for high-N/high-T DRC3a narrative |

## Near-Term Gaps

- formal data dictionary for DRC2 variables used in DRC3a
- explicit manifest tying raw inputs to each script
- figure manifest with final manuscript figure numbers
- reproducibility check that reruns the full pipeline from a clean local data restore
- public-release policy for aggregate tables versus de-identified analytical data
