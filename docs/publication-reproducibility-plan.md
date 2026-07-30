# Publication Reproducibility Plan

## Private Repository

The private repository should support active analysis and writing. It can contain controlled references to raw data locations, private local data paths, interim audit notes, and generated outputs that are not yet publication-approved.

Primary responsibilities:

- preserve analytical history
- rebuild current tables and figures
- keep private data out of tracked files
- document choices while the manuscript evolves
- stage a clean public release later

## Public Publication Clone

The public clone should be a stripped, stable repository associated with the submitted or accepted manuscript.

Primary responsibilities:

- reproduce final published tables and figures
- explain data restrictions without exposing sensitive records
- include only approved aggregate/anonymized data
- support reviewer or reader inspection
- freeze package versions and run commands

## Release Gates

Before copying anything to a public clone:

1. Run `python checks/check_repo_hygiene.py`.
2. Confirm no raw or row-level private files are tracked.
3. Confirm every public dataset has a dictionary and provenance note.
4. Confirm every figure in the manuscript maps to `config/figure_manifest.yml`.
5. Confirm every table in the manuscript maps to a script or documented manual derivation.
6. Remove links to non-public Drive documents unless they are intentionally cited as controlled access materials.

## Reviewer-Facing Reproducibility Target

The final public README should let a reviewer do three things quickly:

- inspect the exact inputs used for each published figure/table
- rerun the analysis from approved data
- compare regenerated outputs to the manuscript figures and tables
