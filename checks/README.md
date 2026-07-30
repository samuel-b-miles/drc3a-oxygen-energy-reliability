# Reproducibility Checks

Checks should confirm that the pipeline is rebuildable, privacy-preserving, and publication-ready.

Planned checks:

- raw/private files are not tracked by git
- expected aggregate outputs exist
- manuscript figures are regenerated from scripted analyses
- public-release manifest excludes controlled source data
- high-level tables match the manuscript draft

Current checks:

- `python checks/check_repo_hygiene.py`
- `python checks/check_release_candidate.py`
