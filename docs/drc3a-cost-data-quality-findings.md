# DRC3a Cost Data Quality Findings

## Purpose

This pass audits whether facility-reported cost and spend variables can be used responsibly in DRC3a analyses. The goal is to preserve clear signals without letting ambiguous units, structural missingness, or extreme values drive the results.

## Cost Variables Reviewed

- `grid_cost_median`
- `generator_cost_median`
- `oxygen_cost_median`
- `solar_total_value_median`
- `solar_maintenance_adhoc_median`
- `I2_wtp_median`

## Conservative Cleaning Rule

For each cost variable, a value is retained in the conservative analysis set only when it is:

- numeric;
- positive;
- source-consistent, where applicable;
- not above the positive-value 95th percentile.

Zeros are preserved in the audit file but not treated as positive spend. Values above the 95th percentile are flagged for review rather than deleted from the raw audit trail.

## Retained Sample Sizes

| Variable | Positive N | Conservative N | Positive median | Conservative median | Conservative max |
| --- | ---: | ---: | ---: | ---: | ---: |
| Grid cost | 294 | 260 | 54 | 50 | 1,800 |
| Generator cost | 229 | 217 | 130 | 120 | 1,250 |
| Oxygen cost | 86 | 81 | 5 | 5 | 60 |
| Solar total value | 309 | 293 | 2,000 | 2,000 | 34,000 |
| Solar ad hoc maintenance | 189 | 179 | 50 | 50 | 900 |
| WTP for improved electricity | 465 | 446 | 50 | 50 | 300 |

## Main Interpretation

The cost variables are usable for exploratory analysis when treated as ranked or grouped indicators, not as clean continuous currency measures. Medians are plausible, but the upper tail is too extreme to use uncritically. For example, grid cost has a conservative median of 50 but raw maximum of 600,000; oxygen cost has a conservative median of 5 but raw maximum of 15,000.

## Findings After Conservative Cleaning

Higher grid cost remains strongly associated with oxygen capacity:

- multiple concentrators: OR 6.48, p<0.001;
- 10L concentrators: OR 5.29, p<0.001;
- concentrator access: OR 4.76, p<0.001;
- any oxygen: OR 4.21, p<0.001;
- cylinders: OR 3.30, p<0.001.

Higher generator cost remains associated with concentrator capacity:

- multiple concentrators: OR 4.32, p<0.001;
- 5L concentrators: OR 2.70, p<0.001.

Higher solar total value is associated with oxygen access and capacity:

- concentrator access: OR 3.72, p<0.001;
- any oxygen: OR 3.19, p<0.001;
- 10L concentrators: OR 2.86, p<0.001;
- multiple concentrators: OR 2.61, p<0.001.

Solar maintenance cost is more suggestive of fragility:

- oxygen-device damage mentions: OR 3.66, p=0.001;
- multiple concentrators: OR 2.36, p=0.007;
- cylinders: OR 2.60, p=0.008.

WTP is associated with oxygen capacity but should be interpreted cautiously:

- 10L concentrators: OR 2.70, p<0.001;
- multiple concentrators: OR 2.67, p<0.001;
- concentrator access: OR 2.52, p<0.001;
- equipment damage: OR 1.74, p=0.010.

## Strongest Correlations

Spearman rank correlations show that reported energy spend tracks oxygen equipment scale:

- grid cost vs total concentrators: rho=0.55, p<0.001;
- grid cost vs 10L concentrators: rho=0.52, p<0.001;
- generator cost vs total concentrators: rho=0.45, p<0.001;
- solar total value vs total concentrators: rho=0.37, p<0.001;
- solar maintenance vs total concentrators: rho=0.40, p<0.001.

## Cautions

The cost data should not yet be used to make precise affordability or expenditure claims. Units and currencies need confirmation, and some values likely mix monthly costs, total costs, local currency, USD, or reporting errors.

The safest substantive wording is: higher reported energy spending and investment are associated with larger oxygen systems and greater equipment exposure. This supports an infrastructure-intensity story, not a clean cost-effectiveness or affordability estimate.

## Output Files

- `outputs/drc3a_cost_quality/cost_value_audit_long.csv`
- `outputs/drc3a_cost_quality/cost_quality_summary.csv`
- `outputs/drc3a_cost_quality/clean_cost_high_binary_tests.csv`
- `outputs/drc3a_cost_quality/clean_cost_continuous_group_tests.csv`
- `outputs/drc3a_cost_quality/clean_cost_by_group_tests.csv`
- `outputs/drc3a_cost_quality/clean_cost_spearman_correlations.csv`
