# Post-Phase Alignment Template

Status: Template
Authority: advisory-only integration artifact. This file does not authorize execution, promotion, or scope widening by itself.
Purpose: update the multi-stream map after a major round or phase so the next round starts from current truth instead of stale assumptions.

## Header
- `ALIGNMENT_ID`: `<YYYYMMDD-short-id>`
- `DATE_UTC`: `<ISO8601>`
- `SCOPE`: `<phase / round / feature / system slice>`
- `PREVIOUS_PHASE`: `<what phase just completed>`
- `NEXT_PHASE`: `<what phase is next>`
- `OWNER`: `<PM / architecture / operator>`

## Why This File Exists
- `<one line explaining why this phase needs a post-phase alignment>`

## Static Truth Inputs
- `<top-level PM / PRD / product spec / architecture docs>`
- `<decision log / contract docs>`
- `<phase brief or milestone brief>`
- `<multi-stream contract>`

## What Changed This Round

### System Shape Delta
- `<what changed in the actual system shape>`
- `<what new capabilities exist>`
- `<what old assumptions are now invalid>`

### Execution Delta
- `<what changed in code/evidence/ops terms>`
- `<what files changed>`
- `<what interfaces changed>`
- `<what tests changed>`

### No Change
- `<what still did not change>`
- `<what assumptions remain valid>`

## Stream Status Update

### Stream 1: `<stream-name>`
- **Previous Status**: `<active|deferred|blocked|complete>`
- **Current Status**: `<active|deferred|blocked|complete>`
- **What Changed**: `<what changed in this stream>`
- **What Remains**: `<what still needs to happen in this stream>`

### Stream 2: `<stream-name>`
- **Previous Status**: `<active|deferred|blocked|complete>`
- **Current Status**: `<active|deferred|blocked|complete>`
- **What Changed**: `<what changed in this stream>`
- **What Remains**: `<what still needs to happen in this stream>`

### Stream N: `<stream-name>`
- **Previous Status**: `<active|deferred|blocked|complete>`
- **Current Status**: `<active|deferred|blocked|complete>`
- **What Changed**: `<what changed in this stream>`
- **What Remains**: `<what still needs to happen in this stream>`

## Current Bottleneck
- `<which stream is now the bottleneck>`
- `<why it is the bottleneck>`
- `<what unblocks it>`

## Interface Drift
- `<what interface assumptions changed>`
- `<what cross-stream contracts need updating>`
- `<NONE if no interface drift>`

## Next Stream Active
- `<which stream should be active next>`
- `<why this stream is highest leverage>`

## PM Decision Required
- `<what PM decision is now required>`
- `<what evidence supports this decision>`
- `<NONE if no PM decision required>`

## What Should Not Be Done Next
- `<what not to do next and why>`
- `<what is intentionally deferred>`

## Open Risks
- `<risk 1>`
- `<risk 2 or NONE>`

## Evidence Used
- `<current context>`
- `<phase brief>`
- `<review / SAW / handover>`
- `<bridge contract>`
- `<multi-stream contract>`
- `<key runtime or evidence artifacts>`

## Writing Rules
- Keep this file top-level and PM-readable.
- Prefer system language over file-changelog language.
- Make stream status updates explicit: what changed, what remains, what is blocked.
- If the bottleneck changed, say why.
- If an interface drifted, say what contract needs updating.
- Keep the artifact thin: one current alignment, not a growing archive.
