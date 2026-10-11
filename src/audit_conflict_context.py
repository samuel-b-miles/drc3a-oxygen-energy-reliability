#!/usr/bin/env python3
"""Descriptive conflict-window sensitivity from immutable dashboard buckets."""
from pathlib import Path
import hashlib
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

def build():
    source = ROOT / 'data/collections/goma/powerwatch/readings.csv.gz'
    out = ROOT / 'data/collections/goma/powerwatch/conflict_audit'
    out.mkdir(parents=True, exist_ok=True)
    raw = pd.read_csv(source)
    raw = raw[raw.metric.eq('voltage')].copy()
    raw['local_time'] = pd.to_datetime(raw.time_utc, utc=True).dt.tz_convert('Africa/Kigali')
    if raw.duplicated(['sensor_id', 'local_time']).any():
        raise ValueError('Duplicate buckets require reconciliation')
    slots = pd.date_range('2025-01-14', '2025-02-09', freq='2min', inclusive='left', tz='Africa/Kigali')
    matrix = raw.pivot(index='local_time', columns='sensor_id', values='value').reindex(slots)
    daily = []
    for sensor in matrix:
        for day, values in matrix[sensor].groupby(matrix.index.date):
            daily.append(dict(sensor_id=sensor, date_local=str(day), expected_bins=len(values),
                              observed_bins=int(values.notna().sum()), missing_bins=int(values.isna().sum()),
                              observed_low_bins=int((values.ge(0) & values.le(23)).sum()),
                              observed_above_23V_bins=int(values.gt(23).sum()),
                              negative_review_bins=int(values.lt(0).sum())))
    pd.DataFrame(daily).to_csv(out / 'daily_measurement_states.csv', index=False)
    periods = [('pre_context', '2025-01-14', '2025-01-24'),
               ('conflict_calendar_context', '2025-01-24', '2025-01-31'),
               ('later_context', '2025-01-31', '2025-02-09'),
               ('register_four_calendar_days', '2025-01-26', '2025-01-30')]
    result = []
    for name, start, end in periods:
        selected = matrix.loc[(matrix.index >= pd.Timestamp(start, tz='Africa/Kigali')) &
                              (matrix.index < pd.Timestamp(end, tz='Africa/Kigali'))]
        for sensor in selected:
            values = selected[sensor]
            result.append(dict(period=name, start_local=start, end_exclusive_local=end, sensor_id=sensor,
                               expected_bins=len(values), observed_bins=int(values.notna().sum()),
                               missing_bins=int(values.isna().sum()),
                               low_bins=int((values.ge(0) & values.le(23)).sum()),
                               above_23V_bins=int(values.gt(23).sum()),
                               above_23V_percent_expected=round(100 * values.gt(23).sum() / len(values), 4)))
    pd.DataFrame(result).to_csv(out / 'period_measurement_states.csv', index=False)
    (out / 'run_provenance.json').write_text(json.dumps(dict(
        source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        periods=periods, interval_seconds=120,
        interpretation='Calendar contexts, not verified grid outage boundaries. Bucket proportions are not exact uptime. Missing measurements remain separate from low observations. Source voltage aggregation prefers energized readings. No generator classifier or kWh estimate is applied.'
    ), indent=2) + '\n')

if __name__ == '__main__':
    build()
