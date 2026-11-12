# Coding protocol v0.1

## Automated screen (implemented)
The code defines its exact regex rules in `PATTERNS`. Text undergoes Unicode NFKC normalization, whitespace normalization and case folding, with accent folding for coding only (not deduplication). Whole answer text is searched rather than split on commas inside option labels. Categories are concentrator-explicit; resuscitation-broad; sterilization; refrigeration/cold-chain; imaging; laboratory; surgery; maternal/neonatal. These overlap and remain **unreviewed dictionary flags**. Negation, absence and option-list prompting are not reliably resolved by lexical matching.

The long private evidence file retains record ID, tab/row, question context, verbatim text, code and review status. The same retained answer may flag multiple codes; MCZ first/second responses within one context are combined and counted once per submission. Original source field indices are in `FIELDS`. Mortality-related questions are elicited priorities, not observed mortality effects. TECH rankings are not converted into scores until answer order and coding are validated.

## Qualitative adjudication matrix (not yet coded exhaustively)
| Theme | Include only when explicit | Hypothesis/measurement consequence |
|---|---|---|
| Interruptions/intermittency | Outages, repeated interruptions, lost operating time | Measure outage frequency and duration separately from connection |
| Voltage/power quality | Stated fluctuation, undervoltage, spikes | Do not infer voltage quality from uptime alone |
| Backup and switching | Alternative source, automatic/manual switching, continuity during failure | Distinguish installed backup from functional redundancy |
| Installed vs functional stock | Equipment present but unavailable/unused/nonfunctional | Separate ownership from operational oxygen capacity |
| Concentrator fragility | Concentrator named, failure circumstances documented | Distinguish generic equipment failures from oxygen-specific reports |
| Attribution | Generic failure vs respondent-suspected electrical cause | Preserve attribution uncertainty, avoid causal claim |
| Maintenance/repair | Spare parts, skills, repair delay, servicing | Identify plausible modifiers of failure and recovery |
| Clinical workaround | Service delay, interruption, relocation, alternatives | Measure care disruption separately from equipment damage |
| Cost and fuel | Affordability, fuel shortage, operating cost | Test supply sufficiency vs nominal installed assets |
| Conflict/access | Insecurity, travel/logistics, remoteness | Context and potential selection/confounding, not assumed universal |

For each reviewed excerpt, retain French original, any translation, elicitation field, prompted/spontaneous status, positive/negative/nonapplicable polarity, coder confidence, both coders' decisions and adjudication. Restrict quotations and identities to controlled storage. Audio is unobserved until transcribed. A broad resuscitation label must not be recoded into an explicit oxygen-concentrator mention.

TECH peak/energy rankings containing the resuscitation composite option are conservatively suppressed from concentrator-specific counts; these composite choices do not independently establish concentrator prioritization.
