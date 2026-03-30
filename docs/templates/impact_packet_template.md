# Impact Packet Template

> **Canonical source:** src/sop/templates/impact_packet_template.md
> This copy in docs/templates/ is a workspace mirror. Do not edit here — edit the canonical source instead.

Status: Template
Authority: advisory-only integration artifact. This file does not authorize execution, promotion, or scope widening by itself.
Purpose: provide the planner with a compact view of what changed and what might be affected, without requiring full-repo rereads.

## Header
- `PACKET_ID`: `<YYYYMMDD-short-id>`
- `DATE_UTC`: `<ISO8601>`
- `SCOPE`: `<phase / round / feature / system slice>`
- `OWNER`: `<PM / architecture / operator>`

## Why This File Exists
- `<one line explaining why the planner needs an impact packet>`

## Changed Files

Files modified in this round:

```
<file path 1>
<file path 2>
<file path N>
```

## Owned Files

Files owned by the active stream/phase:

```
<file pattern 1 or key file 1>
<file pattern 2 or key file 2>
<file pattern N or key file N>
```

## Touched Interfaces

Interfaces modified or newly exposed in this round:

### Interface 1: `<interface name>`
- **Type**: `<API endpoint / function signature / data schema / event contract>`
- **Owner**: `<which stream/subsystem owns this interface>`
- **Changed**: `<what changed>`
- **Consumers**: `<which streams/subsystems consume this interface>`

### Interface 2: `<interface name>`
- **Type**: `<API endpoint / function signature / data schema / event contract>`
- **Owner**: `<which stream/subsystem owns this interface>`
- **Changed**: `<what changed>`
- **Consumers**: `<which streams/subsystems consume this interface>`

### Interface N or NONE
- `<NONE if no interfaces changed>`

## Failing Checks

### Test Failures

```
<test name 1>: <failure reason>
<test name 2>: <failure reason>
<test name N or NONE>
```

### Lint/Type Failures

```
<file path 1>: <lint/type error>
<file path 2>: <lint/type error>
<file path N or NONE>
```

### Smoke Test Failures

```
<smoke test name 1>: <failure reason>
<smoke test name 2>: <failure reason>
<smoke test N or NONE>
```

### CI/CD Failures

```
<pipeline stage 1>: <failure reason>
<pipeline stage 2>: <failure reason>
<pipeline stage N or NONE>
```

## Cross-Stream Impact

### Streams Affected

- **Stream 1**: `<stream name>`
  - **Why affected**: `<what changed that affects this stream>`
  - **Action required**: `<what this stream needs to do>`

- **Stream 2**: `<stream name>`
  - **Why affected**: `<what changed that affects this stream>`
  - **Action required**: `<what this stream needs to do>`

- **Stream N or NONE**

## Escalation Signals

### When This Impact Packet Is Insufficient

The planner should escalate to broader repo reads if:

1. **Changed files list is incomplete**: The planner suspects more files were affected but are not listed
2. **Interface ownership is unclear**: The touched interfaces list does not make it clear which subsystem owns a particular interface
3. **Failing checks are ambiguous**: The failure reasons do not provide enough context to diagnose the root cause
4. **Cross-stream impact is unclear**: The planner cannot determine which streams are affected from the current impact packet

## Evidence Used
- `<git diff output>`
- `<test run logs>`
- `<lint/type checker output>`
- `<smoke test results>`
- `<CI/CD pipeline logs>`
- `<multi-stream contract>`

## Writing Rules
- Keep this file compact and machine-readable.
- Prefer file paths and interface names over prose descriptions.
- Make the packet self-contained: the planner should not need to read the whole repo to understand impact.
- If the planner needs more context, that signals an escalation condition, not a packet deficiency.
- Keep the artifact thin: one current packet, not a growing archive.
