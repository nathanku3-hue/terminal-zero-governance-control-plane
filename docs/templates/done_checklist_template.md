# Done Checklist Template

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

## Explicit Non-Goals
- `<what is intentionally not done in this scope>`
- `<what is deferred to later>`

## Blocked Until
- `<what requires a new explicit approval or evidence packet>`
- `<NONE if nothing is blocked>`

## Machine-Checkable Rules

### Pass Conditions
```
<machine-readable pass condition 1>
<machine-readable pass condition 2>
<machine-readable pass condition N or NONE>
```

### Fail Conditions
```
<machine-readable fail condition 1>
<machine-readable fail condition 2>
<machine-readable fail condition N or NONE>
```

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
