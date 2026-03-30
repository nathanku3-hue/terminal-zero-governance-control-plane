# Done Checklist Template

> **Canonical source:** src/sop/templates/done_checklist_template.md
> This copy in docs/templates/ is a workspace mirror. Do not edit here — edit the canonical source instead.

Status: Template
Authority: advisory-only integration artifact. This file does not authorize execution, promotion, or scope widening by itself.
Purpose: define machine-checkable done criteria for a phase, round, or feature.

## Header
- `CHECKLIST_ID`: `<YYYYMMDD-short-id>`
- `DATE_UTC`: `<ISO8601>`
- `SCOPE`: `<phase / round / feature / system slice>`
- `STATUS`: `<draft|active|complete|archived>`
- `OWNER`: `<PM / architecture / operator>`

## Why This File Exists
- `<one line explaining why this scope needs an explicit done checklist>`

## Static Truth Inputs
- `<top-level PM / PRD / product spec / architecture docs>`
- `<decision log / contract docs>`
- `<phase brief or milestone brief>`

## Done Criteria

### Functional Completeness
- [ ] `<criterion 1: what must work>`
- [ ] `<criterion 2: what must work>`
- [ ] `<criterion N or NONE>`

### Evidence Completeness
- [ ] `<criterion 1: what evidence must exist>`
- [ ] `<criterion 2: what evidence must exist>`
- [ ] `<criterion N or NONE>`

### Integration Completeness
- [ ] `<criterion 1: what must connect>`
- [ ] `<criterion 2: what must connect>`
- [ ] `<criterion N or NONE>`

### Documentation Completeness
- [ ] `<criterion 1: what must be documented>`
- [ ] `<criterion 2: what must be documented>`
- [ ] `<criterion N or NONE>`

### Handoff Completeness
- [ ] `<criterion 1: what next operator needs>`
- [ ] `<criterion 2: what next operator needs>`
- [ ] `<criterion N or NONE>`
- [ ] **Git hygiene:** All required current/evidence artifacts are committed, archived, pruned, or explicitly classified
- [ ] **If remote exists and push is expected for this repo, push or record why not.**

### Pass Conditions`

## Explicit Non-Goals
- `<what is intentionally not done in this scope>`
- `<what is deferred to later>`

## Blocked Until
- `<what requires a new explicit approval or evidence packet>`
- `<NONE if nothing is blocked>`

## Machine-Checkable Rules

### Pass Conditions
```bash
# Example: Evidence artifacts exist
test -f data/processed/phaseN_summary.json || exit 1
test -f data/processed/phaseN_evidence.csv || exit 1

# Example: Tests pass
pytest tests/test_phaseN.py -v || exit 1

# Example: Lint passes
flake8 src/ || exit 1
mypy src/ || exit 1

# Example: Immutable SSOT unchanged
git diff --exit-code data/processed/phase_M_ssot.json || exit 1

# Example: Required files exist
test -f docs/phase_brief/phaseN-brief.md || exit 1
test -f docs/handover/phaseN_handover.md || exit 1
```

### Fail Conditions
```bash
# Example: Forbidden files exist (should not exist)
! test -f data/processed/phaseN_promoted.json || exit 1

# Example: Forbidden changes (SSOT mutated)
git diff --quiet data/processed/phase_M_ssot.json || exit 1

# Example: Tests fail
pytest tests/test_phaseN.py -v && exit 0 || exit 1

# Example: Lint fails
flake8 src/ && exit 0 || exit 1
```

### Machine-Checkable Script

Create a `check_done.sh` script that runs all pass conditions:

```bash
#!/bin/bash
set -e

echo "Checking done criteria..."

# Pass conditions
test -f data/processed/phaseN_summary.json
test -f data/processed/phaseN_evidence.csv
pytest tests/test_phaseN.py -v
flake8 src/
mypy src/
git diff --exit-code data/processed/phase_M_ssot.json
test -f docs/phase_brief/phaseN-brief.md
test -f docs/handover/phaseN_handover.md

# Fail conditions (inverted)
! test -f data/processed/phaseN_promoted.json

echo "All done criteria passed."
```

Run with: `bash check_done.sh`

## Evidence Used
- `<current context>`
- `<phase brief>`
- `<review / SAW / handover>`
- `<key runtime or evidence artifacts>`

## Open Risks
- `<risk 1>`
- `<risk 2 or NONE>`

## Writing Rules
- Keep this file top-level and PM-readable.
- Prefer system language over file-changelog language.
- Make criteria checkable: prefer "X must pass" over "X should be good."
- If a criterion cannot be checked mechanically, say how a human checks it.
- Keep the artifact thin: one current checklist, not a growing archive.
