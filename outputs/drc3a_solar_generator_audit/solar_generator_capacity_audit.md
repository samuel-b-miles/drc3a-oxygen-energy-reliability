# Solar and Generator Capacity Audit

## Cleaning Rules

- Solar panel count: kept when solar was reported, the median reconciled panel count was positive, <=500, and the facility-level conflict flag was zero.
- Solar capacity: inferred from `D4_solar_capac_median` using reported panel count. Values were accepted only when either a W or kW interpretation implied 50-750 W per panel. Values <100 were preferentially treated as kW; values >=100 were preferentially treated as W.
- First generator capacity: kept when generator was reported, first-generator capacity was >=1 kVA after cleaning, and the conflict flag was zero. Values >500 and <=10,000 were treated as VA/W-like entries and divided by 1,000; values >10,000 would be excluded.
- Solar kWp and generator kVA are compared only as facility-level scale indicators; they are not equivalent measures of firm power.

## Headline Results

- Solar present: 315/491 facilities.
- Generator present: 231/491 facilities.
- Both solar and generator: 173/491 facilities.
- Solar panels, clear count: n=304, median 6,0 panels [IQR 4,0-11,0], p90 24,0, max 400,0.
- Solar capacity, inferred clean: n=120, median 1,0 kWp [IQR 0,5-3,0], p90 7,1, max 50,0.
- First generator capacity, clean: n=222, median 11,2 kVA [IQR 5,0-24,0], p90 66,9, max 425,0.
- Paired clean capacity comparison: n=65, median solar 2,0 kWp vs median first-generator 12,0 kVA; median ratio 0,20.

## Statistical Checks

- solar panel count by generator presence: Mann-Whitney U, statistic=16647,500, p=6.928e-12.
- clean solar kWp by generator presence: Mann-Whitney U, statistic=2429,000, p=0.000364.
- clean solar kWp vs clean first-generator kVA among paired facilities: Spearman rank correlation, statistic=0,314, p=0.01095.
- clean solar panel count vs clean first-generator kVA among paired facilities: Spearman rank correlation, statistic=0,308, p=7.023e-05.

## Interpretation

The panel-count field is substantially more reliable than the capacity field. Cleaned panel counts are available for most solar-reporting facilities, while clean installed solar capacity is available for a much smaller subset because the raw capacity field mixes scales and contains physically implausible panel/capacity combinations.

The capacity field also has a clear geographic missingness problem: Sud-Kivu has solar panel counts but no non-missing solar-capacity entries in the facility master. Solar capacity should therefore not be used for province-level inference without revisiting the source instrument or raw collection history.

The cleaned comparison suggests that solar installations are present at many facilities but are typically small relative to generator capacity. Among paired clean observations, the median solar/generator capacity ratio is well below 1. Generator-backed sites also report larger solar arrays, suggesting that solar is often layered onto larger, more energy-complex facilities rather than substituting for generator capacity.

## Outputs

- `tables/facility_solar_generator_capacity_clean.csv`
- `tables/capacity_records_to_review.csv`
- `tables/capacity_distribution_summary.csv`
- `tables/capacity_summary_by_group.csv`
- `tables/capacity_comparison_tests.csv`
- `figures/fig_solar_generator_capacity_audit.png`
