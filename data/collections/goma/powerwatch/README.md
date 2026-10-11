# Goma event electrical records

Five unformatted nLine PowerWatch dashboard exports cover **14 January–8 February 2025** in CAT (UTC+2). The nine site filters were supplied by the user; 13 distinct respondent-alias series returned across the context window. A census of every additional facility or sensor in Goma has not been established.

The [released readings](readings.csv.gz) contain 430,560 voltage/frequency records with pseudonymous site, series and circuit IDs, original numerical values, source export IDs, source CSV row numbers, explicit UTC timestamps and QA flags. Original named CSVs, hardware mappings and deployment crosswalks remain ignored. Each exported row represents a dashboard bucket, not necessarily one underlying sensor reading.

The query inspector establishes these transformations:

- Windows of at most seven days use **120-second buckets**. Longer dashboard windows use dynamic averaging.
- Voltage is `grid_voltage / 1.414`. Each bucket prefers the average of readings above 23 V; it uses low readings only when no reading exceeds 23 V.
- Frequency is averaged without the same voltage-conditioned selection. Extreme values may reflect estimation/waveform artifacts and remain flagged for review.
- The query keeps scaled voltage above -0.5 V, `particle` time-source records, and records inside stored deployment-validity intervals.
- Eight-character metric labels come from deployment `respondent_id`; they are not independently established hardware serials.

A proportion of buckets above 23 V is a descriptive bucket statistic, not exact uptime. Missing or absent series do not prove an outage. Negative values, duplicate conflicts, frequency artifacts and gaps remain inspectable. No interpolation or source-of-power classification is applied.

[Figure 1](../../../../outputs/event_figure/figure_1_event_descriptive.pdf) shows the Ndosho pair and all returned series. Shaded calendar days come from the generator register, not independently verified cutoffs on four city grids. Kyeshero's user-supplied hardware identity has a candidate ARE-Virunga alias in deployment references; event-period validity needs reconciliation before a plant claim is made.

The released pseudonymous readings are sufficient to rebuild the figure and bucket table without raw identities. See [reproduction commands](../../../../docs/auditable-data-packages.md).

The [daily measurement-state audit](conflict_audit/daily_measurement_states.csv) and [calendar-context sensitivity table](conflict_audit/period_measurement_states.csv) compare pre-context, 24–30 January context, later context and the four register dates separately. They preserve low observations and missing bins as separate states and do not estimate exact outage hours or power-source identity. Regenerate with `python src/audit_conflict_context.py`. Grafana KPI Overview was inspected for the same 14 January–8 February window: its room-level panel summarizes the precomputed `saidi_respondent_id_day` table; the upstream SAIDI algorithm and missing-data treatment remain unverified. Context-window KPI summaries therefore cannot independently establish precise blackout onset/restoration.
