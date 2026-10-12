# Portable workflow and production gaps

The portable renderer creates all five plots from prepared summary inputs, without private files, using invented fixtures by default:

```sh
python pipelines/five_slide_v6/portable.py --per-bed --output /tmp/drc3a-demo
python -m unittest discover -s pipelines/five_slide_v6 -p test_portable.py
```

Use the pinned requirements and Python version in README.md. The demonstration is a schema/plotting example, not production evidence or a faithful production layout. Outputs are a five-page PDF and five PNGs; no invented results should enter manuscript or production assets. Passing `--input approved-summary.json` supplies a controlled bundle. Omit `--per-bed` for counts. The original v6 build and frozen inputs remain separate.

## JSON schema contract

Each table key is a nonempty array; top-level `voltage_cadence_seconds` is a positive cadence in seconds. No identifiers, source paths, cohort sizes, facility names or circuit assignments are hard-coded in the renderer. Labels must already satisfy the intended disclosure scope. Prepared summaries can still be private.

| Key | Required row fields | Meaning and validation |
|---|---|---|
| calendar | label, start, end, reported | ISO dates, half-open ordered intervals, boolean record presence; prepare explicit absent intervals; never infer uptime |
| voltage | series, time, volts | ISO timestamps with explicit timezone; unique series/time; regular complete cadence; finite nonnegative volts or null; include every expected cadence slot, null for missing/invalid |
| devices | label, beds, concentrators, oximeters | Finite nonnegative matched-scope values; positive devices with zero beds require source resolution; zero-bed rates remain undefined |
| distribution | class, uptime_pct, capacity_lpm | Valid prepared recall uptime in [0,100] or null; nonnegative nominal capacity, reported zero retained; denominator differs per panel |
| damage | contrast, exposed_n, exposed_yes, reference_n, reference_yes | Positive integer denominators, integer numerators bounded by denominator; explicit outcome/cohort upstream |

Voltage validation rejects absent cadence slots and timezone-naive timestamps; adapters must supply null rows for gaps and confirm the source timezone convention. Group and missing-value handling is tested, but no causal, facility-wide availability, oxygen flow or clinical-service inference follows.

## Generalization map and remaining gaps

| Plot | Controlled production recipe | Safe generalization | Remaining production work |
|---|---|---|---|
| Calendar | build_source_calendar_revision.py plus task8 load/calendar preparation | Interval rendering and presence contracts; windows/labels/colours can be config | Port latest task8 calendar assembler, daily presence union and date-adoption provenance; preserve source windows and gaps; layout parity |
| Voltage | build_latest_five_slide_revision.py plus build_goma_native_event_figures.py constants | Generic null-preserving series rendering; styles, panel assignment and event windows can be private config | Port native status/evidence checks, panel layout and classification; quarantine all identity/circuit mappings and captions; require complete regular time grid |
| Devices | figure_pack_2026_10_11/build_figure_pack.py; pending task6 revision | Counts and matched-bed density functions; labels and cohort selection private | Extract formal report/table reconciliation, matched ward/cohort checks; obtain stable pending per-bed builder, provenance and layout; avoid copying original cohort narratives |
| ECDF | build_distribution_review.py | Separate valid-sample ECDFs; zero-preserving nominal capacity; class selection private | Parameterize selected marker and styling; keep upstream exact recall recodes, validity and multi-response stock aggregation audited separately; replicate approved layout |
| Damage | build_damage_power_comparison_figure.py; task7 damage comparisons and pending concentrator outcome | Numerator/denominator prevalence rendering; outcome and labels private | Port approved confidence intervals, overlapping mention ranks and cohort consistency checks; obtain stable concentrator-specific outcome coding/aggregate schema; no unreviewed survey text |

Original scripts may contain sensitive values inside strings, captions, lookup tables and assertions as well as paths. Replacing absolute paths alone is insufficient for disclosure. Extract functions selectively and supply confidential fields from ignored configs; do not track entire original scripts. Raw extraction and coding remain separate controlled upstream stages.

No production numerical output is introduced by this extension. Eight synthetic contract tests cover missing uptime, retained zeros, duplicate timestamps, missing cadence slots, null voltage, invalid outcome counts and undefined zero-bed rates. A full private-input production equivalence test remains necessary before this portable renderer can replace v6. Fresh dependency installation and CI have not been tested; local checks used the existing production environment. Public reusable code/documentation publication is authorized; private inputs and study outputs remain excluded.
