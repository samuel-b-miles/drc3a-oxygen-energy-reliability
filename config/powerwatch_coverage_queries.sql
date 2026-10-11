-- Read-only templates for the existing nLine Grafana Timescale datasource.
-- Run via Grafana Explore (Table format). Replace :from_utc / :to_utc with
-- explicit ISO8601 bounds. Prefer <=7-day chunks when longer queries time out.
-- Do not save over shared dashboards. Original query CSVs remain controlled.

-- Recorded deployment validity. Timezone-naive dates are not silently converted.
SELECT d.respondent_id AS source_series_id, d.site_id, d.core_id,
       d.department_type, d.room_type_label, d.flex_system,
       d.deployment_start_time::text AS deployment_start_source,
       d.deployment_end_time::text AS deployment_end_source,
       pg_typeof(d.deployment_start_time)::text AS deployment_time_type
FROM deployment_pwdata d
WHERE d.site_id='ch cbca bethesda ndosho'
ORDER BY d.deployment_start_time;

-- Measurement span and observed slots within one bounded chunk.
-- This does not infer outages from unobserved slots or estimate oxygen uptime.
SELECT d.respondent_id AS source_series_id,
       pg_typeof(p.time)::text AS measurement_time_type,
       MIN(p.time)::text AS first_time_source,
       MAX(p.time)::text AS last_time_source,
       COUNT(*) AS raw_rows,
       COUNT(DISTINCT time_bucket('120 seconds',p.time)) AS observed_2min_buckets
FROM powerwatch_anonymous p
INNER JOIN deployment_pwdata d ON d.core_id=p.core_id
WHERE p.time >= :from_utc AND p.time < :to_utc
  AND d.site_id='ch cbca bethesda ndosho' AND p.time_source='particle'
  AND p.time>d.deployment_start_time
  AND (p.time<d.deployment_end_time OR d.deployment_end_time IS NULL)
GROUP BY d.respondent_id,pg_typeof(p.time)::text
ORDER BY d.respondent_id;
