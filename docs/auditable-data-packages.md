# DRC3a source packages and reproduction

Each collection manifest connects released artifacts to their source, modification date where available, retrieved-byte hash, exact sheet or CSV field, and processing code. Originals remain authoritative in Drive or the credited source repository. Local originals are unchanged; public derivatives have explicit privacy transformations.

| Question | Inputs and completed work | Limit before a stronger claim |
|---|---|---|
| How did electricity differ across the event? | Five PowerWatch exports, 14 Jan–8 Feb 2025; timezone/units, pseudonymous registry, gap/conflict flags, voltage figure and bucket summaries | Mixed buckets prefer energized samples. Reconcile dated hardware/circuit identities and grid cutoffs/restoration. |
| How did Ndosho sustain supply? | Register `ChCbNdosho 2025!A50:L54`: manual 96 h, separate model-derived 88.3667 h (`N37:Q40`), 600 L entered | Verify fuel-entry meaning, protection topology, oxygen-device connections and source transitions. No oxygen-service uptime is calculated. |
| What was earlier energy use? | Charlie Huang workbook preserved; 319,601-cell projection and 26-tab inventory | Mixed dates, 13 source errors, uncertain units and assumed runtime-to-kWh conversions require a separate correction layer. Source charts are existing analyses, not newly validated results. |
| What loads did concentrators and wards draw? | All 13 pinned HOPmeter files; row-preserving ingestion, W/kW conversion, source-line IDs, gap/duplicate/zero checks | Verify timezone, physical meter assignments and valid intervals before energy integration. No January 2025 overlap; power does not measure oxygen flow. |
| Which equipment is cited in damage reports? | Original DRC2 export and H1 wording; legacy coding reproduced, strict concentrator category and controlled answer-to-label ledger | Independent adjudication precedes supervised training. Mentions are not device-level failure rates or causal estimates. |

## Public figure reproduction

Python 3.12 is the audited runtime. Install `requirements-audit.txt` in a local virtual environment and run from the repository root:

```bash
python src/build_event_figure.py
python src/build_collection_timeline.py
python -m unittest discover -s tests -v
python checks/check_repo_hygiene.py
python checks/check_new_data_release.py
```

Figure 1 rebuilds from the released pseudonymous readings. The timeline reads released inventories and summaries. The optional model dependency is pinned for a future adjudicated-label run; model training was not performed in this build.

## Controlled source reproduction

Restore the original files into ignored paths listed in `config/data_sources.yml`, with hashes matching the collection manifests. The historical source snapshot deliberately avoids recalculation: an OOXML privacy transform preserves source formula/cached-value XML and native features. Ordinary workbook import/re-export or recalculation would alter the requested snapshot.

```bash
python src/build_workbook_privacy_rules.py
python src/preserve_source_workbook.py --source data/raw/private/ndosho/historical/source.xlsx --rules config/private/workbook_redactions.json --output data/collections/ndosho/historical/charlie_kwh_snapshot_deidentified.xlsx --audit-dir data/collections/ndosho/historical
python src/export_workbook_cell_ledger.py --source data/collections/ndosho/historical/charlie_kwh_snapshot_deidentified.xlsx --output data/collections/ndosho/historical/cell_ledger.csv.gz
python src/audit_ndosho_generator_register.py
python src/fetch_hopmeter_sources.py
python src/audit_hopmeter.py --source-repo data/raw/private/ndosho/hopmeter/source_repo
python src/audit_powerwatch_exports.py --manifest data/raw/private/goma/powerwatch/export_manifest.json --registry config/private/powerwatch_registry.json --out outputs/private/goma/powerwatch
python src/release_powerwatch_derivatives.py --normalized outputs/private/goma/powerwatch --manifest data/raw/private/goma/powerwatch/export_manifest.json --registry config/private/powerwatch_registry.json --destination data/collections/goma/powerwatch
python src/audit_powerwatch_history.py
python src/audit_drc2_failure_coding.py
```

HOPmeter retrieval is pinned to commit `c21987d8c0cb3d3653d6aad485ee32661e3a5565` and checks every hash. Originals remain in the credited repository rather than being relicensed or copied into this public repository. Its clinical SNIS file is excluded from device-load ingestion.

The equipment audit does not overwrite an existing human review queue. After independent adjudication of every nonempty answer and a reviewer ID for each label set, run `python src/train_reviewed_equipment_model.py`. Models, answer-level review and out-of-fold predictions remain under `outputs/private/`. Classes with insufficient labeled facilities are deferred.

## Next evidence checks

1. Reconcile Kyeshero's hardware identifier, candidate ARE-Virunga alias and dated deployment; establish the measured input/circuit during the event.
2. Confirm Ndosho's January 2025 laboratory/clinic placements and oxygen-device connections. Both electrical series are observed; an oxygen-serving connection is not yet established.
3. Complete bounded coverage/raw-history chunks for the 27 May 2022–present pair. Deployment records and first-week measurements confirm the two sensors in 2022; the October 2026 export returns only M004. Three long-history queries timed out. A short export is a window within monitoring, not the total deployment period.
4. Adjudicate all 240 nonempty survey answers, including uncoded answers, negatives and comparator categories, before treating the concentrator rank as validated.
5. Reconcile historical dates, fuel units, generator-II errors and runtime-to-energy assumptions in a separately versioned clean layer.

This build adds no measured oxygen flow, patient outcome linkage, verified PSA outage duration or causal regression result. Each stronger claim remains attached to its required evidence.

Variable definitions and observation boundaries are in [the data dictionary](data-dictionary.md). Read-only bounded query templates are in `config/powerwatch_coverage_queries.sql`.
