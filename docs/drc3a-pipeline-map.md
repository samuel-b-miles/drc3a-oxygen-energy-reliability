# DRC3a Analytical Pipeline Map

## Manuscript Argument

DRC3a should move quickly from the literature gap to high-N evidence, then to high-T evidence:

1. Literature gap: oxygen studies often measure clinical outcomes and oxygen access, but under-measure electricity as a system variable.
2. High-N answer: DRC2 survey shows health facilities operate through hybrid energy regimes and layered oxygen regimes.
3. High-N implication: energy complexity correlates with oxygen capability but also signals fragility, cost, and compensation for unreliable infrastructure.
4. High-T answer: longitudinal monitoring shows that energy regimes are temporal; voltage, outages, generator switching, and human operation determine what oxygen access means in practice.
5. DRC3a contribution: oxygen access is a critical tracer load for health-facility electrification.

## Proposed Repo Structure

```text
data/
  raw/
  interim/
  processed/
docs/
  workstream-context.md
  drive-index.md
  drc3a-pipeline-map.md
  qa-checklist.md
notebooks/
  exploratory/
src/
  clean/
  classify/
  figures/
  tables/
outputs/
  figures/
  tables/
  manuscript/
```

## Figure Targets

- `fig_1_literature_gap_panel_g`: literature over time and oxygen-energy coupling gap.
- `fig_2_energy_regime_typology`: high-N facility energy regimes by province/facility type.
- `fig_3_oxygen_regime_typology`: high-N oxygen modalities and oxygen source complexity.
- `fig_4_energy_oxygen_coupling`: cross-tab of energy regimes and oxygen regimes.
- `fig_5_high_t_voltage_outage_case`: Bethesda/Ndosho voltage, outage, generator, and protected-circuit evidence.
- `fig_6_oxygen_load_scenario`: concentrator and PSA energy-load implications.
- `fig_7_human_infrastructure`: technician/maintenance/workflow evidence if defensible from source data.

## Tables

- `table_1_data_sources`: DRC2 survey, DRC1/high-T monitoring, Valentin thesis, Oxygen93, manuscript seed, literature table.
- `table_2_regime_definitions`: energy and oxygen regime classification rules.
- `supplement_variable_dictionary`: source variable names, cleaned names, labels, units, missingness rules.
- `supplement_literature_coding`: literature coding instrument and review status.

## Immediate Next Steps

1. Convert DRC2 notebook logic into scripts.
2. Create a facility master table.
3. Define energy regime classes.
4. Define oxygen regime classes.
5. Join energy and oxygen regime classes.
6. Reproduce the literature Panel G as a formal intro figure.
7. Integrate high-T monitoring data and Bethesda narrative.

