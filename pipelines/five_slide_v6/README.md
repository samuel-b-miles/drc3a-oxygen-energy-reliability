# Five-slide production snapshot v6

Destination: https://github.com/samuel-b-miles/drc3a-oxygen-energy-reliability (public, verified 2026-10-12). Baseline commit: fe3ddf8cf17eb49563609fbe7458ca198bb2571d.

Install with Python 3.12.14: `python -m pip install -r pipelines/five_slide_v6/requirements.txt`.
Single build command, from repository root:

```sh
python pipelines/five_slide_v6/build.py
```

`--check-only` verifies every controlled input before execution. No source queries are made. Outputs go exclusively to ignored `data/private/five_slide_v6/workspace/final_five_slide_revision_20261012/`.

## Availability and limits

The tracked package is a checksum-verified interface to a controlled production bundle, not a self-contained public analysis reproduction. Exact scripts and inputs are locally available under ignored `data/private/five_slide_v6/`; a fresh public clone fails clearly until authorized inputs and scripts are provisioned. This is intentional: the recipe contains identifiable circuit context and unpublished text. Root paths were relocated in the runtime copy; original scripts are preserved byte-for-byte. Dependency installation is separate from the build command. Pinned versions record the production runtime, not a guarantee of availability from every package index.

Page 1 uses a frozen calendar, pages 2 and 4 are rebuilt from native summaries and survey plot inputs, pages 3 and 5 are preserved from a frozen predecessor PDF. Thus this reproduces the v6 assembly and its active figure calculations; it does not regenerate all five figures from raw surveys. Upstream calendar/device/damage builders must be parameterized and reviewed before a fully public executable release. PDF byte identity is not expected across runs because timestamps and output paths can vary; compare content, raster assets, page count and analysis assertions.

## Source-to-figure mapping

| Slide | v6 content | Recipe and provenance | Build boundary |
|---|---|---|---|
| 1 | Reporting calendar | task8/source_calendar_loads_20261012; build_source_calendar_revision.py | Frozen page and image; reporting is not uptime |
| 2 | Native voltage | task7/native and native_expansion; build_latest_five_slide_revision.py, constants from build_goma_native_event_figures.py | Unique series and cadence checks; gaps retained |
| 3 | Matched ward device counts | Frozen predecessor; original figure_pack builder and formal ward tables | Preserved page; pending per-bed update is excluded |
| 4 | Five-class uptime and nominal capacity ECDF | build_distribution_review.py; controlled DRC2 plot inputs | Separate valid-sample class denominators; reported zero capacity retained |
| 5 | Equipment mentions and damage contrasts | Frozen predecessor; build_damage_power_comparison_figure.py; task7/damage_comparisons | Preserved page; pending concentrator-specific outcome excluded |

Related upstream audits: task7/roles_audit and degradation_variables. They inform source limitations and are not consumed by this v6 assembly. The controlled handoff manifest is the precise file/hash map.

## Validation and disclosure

Preflight checks SHA256 and fails closed on missing or changed inputs. Production assertions check native cardinality, 120-second cadence, unique alias-time keys, temporal bounds, missing coverage, ECDF denominators and zero retention, five-page assembly, unchanged slide 3/5 content streams, and unchanged input hashes. Outputs require visual review after any recipe/input change. No automated test substitutes for assessment of captions and disclosure.

Never track raw private surveys, credentials, sensor crosswalks, identifiable circuit mappings, unpublished manuscript text or generated packet assets without explicit appropriate approval. Aggregates also require disclosure review. Public code/documentation publication was authorized on 2026-10-12; controlled input publication was not authorized. Do not merge or alter repository visibility. Store subsequent per-bed/device and concentrator-damage revisions separately; v6 is immutable.

The [portable workflow and gap list](PORTABILITY.md) adds safe schema-driven renderers for all five plot types, with invented fixtures and contract tests. It demonstrates a fresh-checkout interface after dependency installation, but does not yet replace the controlled v6 production recipe.
