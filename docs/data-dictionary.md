# Released data dictionary

## PowerWatch readings

One row is one metric cell from a downloaded dashboard CSV. It is a **120-second bucket**, not necessarily an individual sensor sample. `source_export_id` plus `source_row_number` refers to the unchanged controlled source; the controlled deployment crosswalk identifies the original column.

| Field | Meaning |
|---|---|
| time_source / time_utc | Original epoch milliseconds / explicit UTC conversion. Source dashboard is Africa/Kigali (CAT, UTC+2). |
| site_id / sensor_id / circuit_id | Public pseudonyms. Sensor IDs label deployment aliases, not guaranteed unique physical hardware. A circuit label is a placement reference, not verified oxygen connection. |
| metric / unit | Voltage in V or frequency in Hz. Voltage is source grid_voltage divided by 1.414. |
| raw_value / value | Original cell string / parsed number. Zero remains a measurement. |
| observation_status | numeric_observation, missing_measurement, or invalid_value. Missing is never classified as an outage. |
| qa_flags | Negative voltage, low-voltage candidate, implausible frequency screen, time-grid problems or conflicting duplicates. Flags retain the original record. |

The dashboard averages energized (>23 V) sub-readings when any are present; otherwise it averages <=23 V readings. The 23 V split is a source query/display rule, not a concentrator operating threshold. Frequency during low voltage is not interpreted as grid quality. Coverage denominators describe expected bucket slots in an export window, not guaranteed scheduled sensor transmissions or oxygen availability. Conflicting duplicate observations are excluded from unambiguous numeric coverage.

## Historical workbook

`cell_ledger.csv.gz` contains sheet, cell, cell_type, literal_or_cached_value, formula and style_id. Formula caches are source caches, preserved without recalculation. Empty cells are omitted. `sheet_inventory.json`, `preservation_audit.json` and `redaction_ledger.csv` document sheet dimensions, invariant numeric/formula signatures and privacy transformations. Original private annotation text is represented by a hash, not published. Units remain those in source headings; generator runtime-derived kWh is an estimate under source load assumptions.

## HOPmeter

The public inventory contains source filename, pinned URL/hash, row count, timestamp span, interval/gap and duplicate diagnostics. Controlled row-preserving files contain source_row_number, time_source, time_parsed_naive, timezone_status, power_source, power_W and power_factor. Original W/kW strings remain available; explicit kW is multiplied by 1000. Timestamps have no verified timezone. Device labels follow filenames until physical meter assignments are audited. No duration-weighted energy, oxygen flow or clinical endpoint is calculated.

## DRC2 equipment mentions

Aggregates count unique retained facilities with at least one matched answer. Categories overlap. The source question asks about damage attributed to poor electricity; categories measure reports, not independently verified failures. Strict concentrator mentions exclude generic oxygen references and pulse oximeters. Denominators are all 491 facilities and the 235 facilities represented by nonempty damage answers. Original answers, exact match spans, deduplication identifiers and expert review fields remain controlled. Automated rule labels are provisional; they are not training truth for the optional supervised model.
