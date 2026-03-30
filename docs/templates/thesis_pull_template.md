# Thesis Pull Template

> **Canonical source:** src/sop/templates/thesis_pull_template.md
> This copy in docs/templates/ is a workspace mirror. Do not edit here — edit the canonical source instead.

Status: Template  
Authority: advisory-only; instantiate into `docs/context/thesis_pull_latest.md`.  
Purpose: pull one possible philosophy or heuristic refinement from another repo only when live operating evidence exists there.

## Eligibility
- `THESIS_PULL_STATUS`: `<NOT_ACTIVE|ACTIVE>`
- `TRIGGER_BASIS`: `<ACTIVE_SOP_IN_OTHER_REPO|FRESH_REAL_OPERATING_EVIDENCE>`
- `SOURCE_REPO`: `<repo_name_or_path>`
- `WHY_NOW`: `<why this repo is eligible now>`
- `EVIDENCE_FRESHNESS_WINDOW`: `<freshness window for the operating evidence, if helpful>`
- `IF_NOT_ACTIVE`: `<why the pull should not run yet>`

## Realm Lens
- `REALM_LENS`: `<domain + user + risk + workflow lens for this repo>`
- `TRANSFER_BOUNDARY`: `<what may transfer / what should remain realm-specific>`

## Local Repo Evidence (Primary)
- `LOCAL_EVIDENCE_SUMMARY`: `<data-driven pattern from the source repo>`
- `EVIDENCE_ITEMS`:
  - `<artifact, metric, shipped outcome, incident, or repeated operating signal 1>`
  - `<artifact, metric, shipped outcome, incident, or repeated operating signal 2>`
  - `<artifact, metric, shipped outcome, incident, or repeated operating signal 3>`

## Academic Inputs (1-3 Only)
- `ACADEMIC_INPUT_1`:
  - `TITLE`: `<paper or source title>`
  - `LINK`: `<url>`
  - `CLASSIFICATION`: `<SUPPORTS|CANDIDATE|FRONTIER|NOT_ACTIONABLE>`
  - `WHY_THIS_CLASSIFICATION`: `<one short reason>`
- `ACADEMIC_INPUT_2`: `<optional; same fields>`
- `ACADEMIC_INPUT_3`: `<optional; same fields>`

## Pulled Thesis
- `PULLED_THESIS`: `<one sentence or NONE>`
- `WHY_IT_FITS_THIS_REALM`: `<why the thesis fits the source repo lens>`
- `WHY_LOCAL_EVIDENCE_LEADS`: `<why local evidence matters more than paper novelty>`

## Recommended Outcome
- `RECOMMENDED_OUTCOME`: `<NO_CHANGE|WATCH|HUMAN_REVIEW_HEURISTIC_UPDATE>`
- `ABSTENTION_REASON_CODE`: `<NONE|NEEDS_MORE_OPERATING_EVIDENCE|SURFACE_EVIDENCE_TOO_WEAK|REALM_TRANSFER_UNCLEAR|I don't know yet>`
- `PROPOSED_HEURISTIC_UPDATE`: `<if any>`
- `WHY_NOT_AUTO_MUTATE`: `Any philosophy or heuristic change requires explicit human review and a separate docs update.`
- `NEXT_EVIDENCE_TO_WAIT_FOR`: `<what would justify revisiting this pull>`

## References
- `LOCAL_EVIDENCE_PATHS`:
  - `<path 1>`
  - `<path 2>`
- `ACADEMIC_LINKS`:
  - `<link 1>`
  - `<link 2>`
