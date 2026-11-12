# Original FOSA and MCZ surveys: reproducible formative reanalysis

## Status and reproducibility
This is a first **conservative deduplication and dictionary-assisted coding pass**, not a finished qualitative reanalysis. Run `python src/analyze_original_surveys.py` from the repository, then `python -m unittest discover -s tests -p test_original_surveys.py`. Python standard library only.

Two controlled source exports must be staged at `data/private/original_surveys/fosa.json` and `mcz.json`. Each JSON contains `spreadsheet_id`, `extracted_date`, and a `sheets` mapping whose entries contain `values` (Google Sheets rows). The run manifest records content hashes. Original Sheets are unchanged. This public repository intentionally excludes the source exports, cleaned submissions, names, phone numbers, facility names, audio/photo URLs, verbatim quotations and row-level audits. An authorized researcher with the source Sheets can regenerate those private files. No raw-data access is granted by this code.

Extraction on 12 November 2026 covered every populated tab; rows after 250 were checked and empty. The original survey dates are substantially earlier than the extraction date.

## Deduplication decisions
- FOSA MED: 30 rows -> **29 retained submissions**, removing one exact copy.
- FOSA TECH: **34 retained submissions**, no exact row copies.
- MCZ Responses: **34 submissions**. The trailing Total row is excluded; it is not a respondent.
- All 34 Copy of Responses sessions match the primary MCZ table. Four rows have at least one differing cell (including formatting). These differences are captured privately, not silently substituted. Sheet3 contains two primary-table sessions, both unchanged.
- Tracker, Questions and DRC1 Annex are supporting metadata, not additional observations.
- MED contains one substantive response with a blank export counter (`b`); it is retained. A nonblank-counter sensitivity is provided, not endorsed as the primary cohort.
- A participant ID can appear at different facilities. A facility may have multiple genuine roles/respondents or repeated submissions with different answers. Neither field establishes duplicate identity. The private same-label review tables are candidates, not deletion instructions.
- Exact deduplication compares cells, permitting only trailing empty-cell differences. No fuzzy, facility-wide or participant-wide deletion is applied. Original data remain recoverable.

## Preliminary findings
The strict lexical screen flags explicit concentrator wording in **19/29** MED general-failure responses and **20/29** MED power-attributed failure responses. It flags concentrators in **19/34** MCZ submissions across the two failure fields, counting a submission only once. These are **mentions among retained responses**, not independent facility damage prevalence. MED contains an explicit nonapplicable/cannot-answer response; all nonempty-answer denominators are displayed, not asserted to be substantive eligible denominators.

TECH's strict rule flags 13/34 failure responses; obvious spelling variants remain for manual review rather than silent expansion. Four TECH failure responses and three mortality-priority responses contain numeric-only rankings whose option key has not been recovered. Treat them as unmapped, not absence of concentrator failure. Any final percentage requires adjudicating these categories and nonapplicable answers.

The aggregate table also shows unique normalized location-label counts. These are a sensitivity to repeat reporting, **not validated facility linkage**: spelling aliases and respondent identity still require review. Multiple equipment codes can occur in one answer, so percentages do not sum to 100. The output does not infer rank from arbitrary comma splitting.

## What this contributes to the hypothesis
The formative material supports a rationale for investigating power reliability, electricity-dependent equipment and oxygen readiness. Medical, technical and zone-level perspectives must remain separate. Concentrator-specific failure reports can motivate oxygen-specific measurement; broad resuscitation prioritization alone cannot establish concentrator failure. Reports of suspected power-related failure are respondent attribution, not independently verified causation.

Suggested manuscript wording, pending human coding review:

> The formative medical, technical and health-zone surveys identified oxygen concentrators among equipment respondents associated with failures and highlighted the dependence of clinical services on electricity. These observations motivated closer examination of electricity reliability and oxygen-service readiness, while distinguishing unavailable equipment, interruptions in use and suspected electrical damage.

This is a **retrospective reconstruction of the formative rationale**, not proof the later hypothesis was prospectively prespecified. The original selected small samples cannot establish representative provincial estimates, mortality effects, or causal power-to-damage effects. The later DRC2/DRC3a regressions have not been rerun using these fundamentally different observations, and these responses must not be appended to that analysis population.

## Next adjudication pass
1. Confirm repeated submissions/roles, explicit duplicate annotations and facility aliases; retain each decision with source row and reason. Compare alternative justified inclusion rules only after this identity review.
2. Recover the TECH numeric option mapping, adjudicate spelling variants and nonapplicable responses, and have a second coder review evidence and disagreements.
3. Retrieve/transcribe authorized audio context before claiming exhaustive mechanism coding. The present pass does not listen to audio, inspect photos, or treat their URLs as evidence.
4. Separate MCZ primary generator/solar supply counts from grid connection counts; they are not mutually exclusive denominators. Do not sum zone totals into a representative facility universe without reconciliation.
5. Link reviewed formative codes to later hypotheses and variables through the matrix below, keeping dated provenance rather than post-hoc claims of prespecification.
