# Multi-Stream Contract Template

> **Canonical source:** src/sop/templates/multi_stream_contract_template.md
> This copy in docs/templates/ is a workspace mirror. Do not edit here — edit the canonical source instead.

Status: Template
Authority: advisory-only integration artifact. This file does not authorize execution, promotion, or scope widening by itself.
Purpose: coordinate frontend/backend/data/ops/docs/product streams so they stay connected instead of drifting into local loops.

## Header
- `CONTRACT_ID`: `<YYYYMMDD-short-id>`
- `DATE_UTC`: `<ISO8601>`
- `SCOPE`: `<phase / round / feature / system slice>`
- `STATUS`: `<planning-only|active|review|closed>`
- `OWNER`: `<PM / architecture / operator>`

## Why This File Exists
- `<one line explaining why this scope needs multi-stream coordination>`

## Static Truth Inputs
- `<top-level PM / PRD / product spec / architecture docs>`
- `<decision log / contract docs>`
- `<phase brief or milestone brief>`

## Stream Map

### Stream 1: `<stream-name>`
- **Purpose**: `<why this stream exists>`
- **Must Deliver**: `<what this stream must produce>`
- **Owned Files**: `<file patterns or key files>`
- **Interfaces**: `<what this stream exposes to other streams>`
- **Dependencies**: `<what this stream needs from other streams>`
- **Status**: `<active|deferred|blocked|complete>`

### Stream 2: `<stream-name>`
- **Purpose**: `<why this stream exists>`
- **Must Deliver**: `<what this stream must produce>`
- **Owned Files**: `<file patterns or key files>`
- **Interfaces**: `<what this stream exposes to other streams>`
- **Dependencies**: `<what this stream needs from other streams>`
- **Status**: `<active|deferred|blocked|complete>`

### Stream N: `<stream-name>`
- **Purpose**: `<why this stream exists>`
- **Must Deliver**: `<what this stream must produce>`
- **Owned Files**: `<file patterns or key files>`
- **Interfaces**: `<what this stream exposes to other streams>`
- **Dependencies**: `<what this stream needs from other streams>`
- **Status**: `<active|deferred|blocked|complete>`

## Typical Streams
- **frontend**: UI components, user-facing flows
- **backend**: API endpoints, business logic, data access
- **data**: schema, migrations, data pipelines
- **ops**: deployment, monitoring, infrastructure
- **docs**: user docs, API docs, runbooks
- **product**: PM artifacts, specs, decision log

## Active Stream Now
- `<which stream is active right now>`

## Deferred Streams
- `<which streams are intentionally deferred>`
- `<why they are deferred>`

## Blocked Streams
- `<which streams are blocked>`
- `<what they are blocked on>`

## Shared Success Condition
- `<what must be true across all streams for this scope to be complete>`

## Integration Checkpoints
- `<checkpoint 1: when streams must sync>`
- `<checkpoint 2: when streams must sync>`
- `<checkpoint N or NONE>`

## Cross-Stream Risks
- `<risk 1: what could cause streams to drift>`
- `<risk 2 or NONE>`

## Pre-Flight Conditions
- `<what must be true before execution begins>`
- `<NONE if no pre-flight conditions>`

## Evidence Used
- `<current context>`
- `<phase brief>`
- `<review / SAW / handover>`
- `<key runtime or evidence artifacts>`

## Writing Rules
- Keep this file top-level and PM-readable.
- Prefer system language over file-changelog language.
- Make stream boundaries explicit: what each stream owns, what it exposes, what it needs.
- If a stream is deferred, say why and when it becomes active.
- If a stream is blocked, say what unblocks it.
- Keep the artifact thin: one current contract, not a growing archive.
