# Bridge Contract Template

Status: Template  
Authority: advisory-only integration artifact. This file does not authorize execution, promotion, or scope widening by itself.  
Purpose: bridge technical execution truth back to planner truth and PM/product/system truth.

## Header
- `BRIDGE_ID`: `<YYYYMMDD-short-id>`
- `DATE_UTC`: `<ISO8601>`
- `SCOPE`: `<phase / round / feature / system slice>`
- `STATUS`: `<planning-only|active|review|closed>`
- `OWNER`: `<PM / architecture / operator>`

## Why This File Exists
- `<one line explaining why the current execution state needs a PM/planner bridge>`

## Static Truth Inputs
- `<top-level PM / PRD / product spec / architecture docs>`
- `<decision log / contract docs>`
- `<phase brief or milestone brief>`

## Live Truth Now
- `SYSTEM_NOW`: `<what system exists now in one sentence>`
- `ACTIVE_SCOPE`: `<what is active right now>`
- `BLOCKED_SCOPE`: `<what remains blocked>`

## What Changed This Round
- `SYSTEM_DELTA`: `<what changed in the actual system shape>`
- `EXECUTION_DELTA`: `<what changed in code/evidence/ops terms>`
- `NO_CHANGE`: `<what still did not change>`

## PM / Product Delta
- `STRONGER_NOW`: `<what assumption is now more credible>`
- `WEAKER_NOW`: `<what assumption is now less credible>`
- `STILL_UNKNOWN`: `<what still needs PM judgment or more evidence>`

## Planner Bridge
- `OPEN_DECISION`: `<the one planning question that now matters most>`
- `RECOMMENDED_NEXT_STEP`: `<the one integration step that should happen next>`
- `WHY_THIS_NEXT`: `<why this next step is the highest leverage>`
- `NOT_RECOMMENDED_NEXT`: `<what not to do next and why>`

## Locked Boundaries
- `DO_NOT_REDECIDE`:
  - `<stable lock 1>`
  - `<stable lock 2>`
- `BLOCKED_UNTIL`:
  - `<what requires a new explicit approval or evidence packet>`

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
- If nothing changed at the PM/product/system layer, say that explicitly.
- Keep the artifact thin: one current bridge, not a growing archive.
