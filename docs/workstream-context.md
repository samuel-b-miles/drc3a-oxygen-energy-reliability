# DRC3 Workstream Context

Last updated: 2026-07-19

## Operating Model

Google Drive is the human-readable source of truth for DRC3 planning, seed documents, manuscript strategy, literature review artifacts, and team-facing coordination. This repo workspace is the executable source of truth for analysis code, figure generation, reproducible data cleaning, and manuscript-production logic.

Codex should begin future DRC3 work by reading this file, then `docs/drive-index.md`, then only opening linked Drive files when needed for the specific task.

## Current Manuscript Direction

DRC3a is being shaped as a Nature Energy-style paper about medical oxygen access as an electricity-conditioned health-system capability. The central high-N/high-T structure is:

- High-N: DRC2 survey analysis across DRC health facilities to classify energy regimes, oxygen regimes, reliability, costs, and facility capability.
- High-T: longitudinal monitoring and thick-description evidence from DRC1, Valentin's work, and the Bethesda/Ndosho narrative to show that energy regimes are temporal, human-operated, and clinically consequential.

The working claim is that oxygen access cannot be measured by equipment presence or grid connection alone. It needs electricity reliability, power quality, backup autonomy, energy affordability, maintenance capacity, and human infrastructure.

## Paper Sequence

- DRC3a: high-N/high-T oxygen-electricity regimes and the reliability gap in health facility electrification.
- DRC3b: volumetric oxygen gap assessment.
- DRC3c: design specifications for oxygen systems that fill the gap in low-resource and conflict-affected contexts.

## Authorship Strategy To Weigh

Two plausible journal/authorship pathways are open and should be considered with the team:

- Nature Energy submission: potentially Dan as final author, if the energy systems and health-facility electrification contribution becomes the lead framing.
- Lancet Global Health submission: potentially Layla as last author, if the global health, oxygen security, mortality, and health systems contribution becomes the lead framing.

This is not a final authorship decision. Treat it as a strategic branch to discuss transparently with the team.

## Durable Rules

- Keep Drive links stable in repo docs.
- Keep raw source files in Drive and/or `data/raw` only; never overwrite them.
- Do not store credentials, tokens, personal contact data, or sensitive access material in the repo.
- Use reproducible scripts for cleaning and figure generation.
- Every manuscript figure should have a named script, input table, output figure, and short provenance note.
- Treat generated literature maps as exploratory until manual coding has been reviewed.

