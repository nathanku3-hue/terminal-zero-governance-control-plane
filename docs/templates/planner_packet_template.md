# Planner Packet Template

> **Canonical source:** src/sop/templates/planner_packet_template.md
> This copy in docs/templates/ is a workspace mirror. Do not edit here — edit the canonical source instead.

Status: Template
Authority: advisory-only integration artifact. This file does not authorize execution, promotion, or scope widening by itself.
Purpose: provide the planner with a compact, fresh world model without requiring full-repo rereads.

## Header
- `PACKET_ID`: `<YYYYMMDD-short-id>`
- `DATE_UTC`: `<ISO8601>`
- `SCOPE`: `<phase / round / feature / system slice>`
- `OWNER`: `<PM / architecture / operator>`

## Why This File Exists
- `<one line explaining why the planner needs a compact fresh-context packet>`

## Current Context

### What System Exists Now
- `<one sentence: what system exists now>`

### Active Scope
- `<what is active right now>`

### Blocked Scope
- `<what remains blocked>`

## Active Brief

### Current Phase/Round
- `<phase number or round identifier>`

### Goal
- `<what this phase/round is trying to accomplish>`

### Non-Goals
- `<what is intentionally out of scope>`

### Owned Files
- `<file patterns or key files this phase/round owns>`

### Interfaces
- `<what this phase/round exposes to other parts of the system>`

## Bridge Truth

### System Delta
- `<what changed in the actual system shape>`

### PM Delta
- `<what assumption is now more/less credible>`

### Open Decision
- `<the one planning question that now matters most>`

### Recommended Next Step
- `<the one integration step that should happen next>`

### Why This Next
- `<why this next step is the highest leverage>`

### Not Recommended Next
- `<what not to do next and why>`

## Decision Tail

Recent decisions (last 5-10 entries from decision log):

- `D-XXX`: `<decision summary>`
- `D-XXX`: `<decision summary>`
- `D-XXX`: `<decision summary>`

## Blocked Next Step

### What Is Blocked
- `<what cannot proceed right now>`

### Why Blocked
- `<what is blocking it>`

### What Unblocks It
- `<what needs to happen to unblock>`

## Active Bottleneck

### Current Bottleneck
- `<which stream or subsystem is now the bottleneck>`

### Why It Is The Bottleneck
- `<why this is the highest-priority constraint>`

### What Unblocks It
- `<what needs to happen to resolve the bottleneck>`

## Escalation Rules

### When To Read Wider Surfaces

The planner should escalate to broader repo reads only when:

1. **Impact surface is unclear**: The planner packet + impact packet do not contain enough information to identify which files/interfaces are affected
2. **Interface ownership is unclear**: The owned files list does not make it clear which subsystem owns a particular interface
3. **Evidence conflicts**: The bridge truth and decision tail contain conflicting information that cannot be resolved from current artifacts
4. **Bottleneck cannot be named**: The active bottleneck is not clear from current context and requires broader system inspection

### Default Read Strategy

By default, the planner should:

1. Load this planner packet first
2. Load the impact packet (changed files, owned files, touched interfaces, failing checks)
3. Propose next step from these small packets
4. Only escalate to wider reads if one of the four escalation conditions applies

## Evidence Used
- `<current context>`
- `<active brief>`
- `<bridge contract>`
- `<decision log tail>`
- `<multi-stream contract>`
- `<post-phase alignment>`

## Writing Rules
- Keep this file compact and PM-readable.
- Prefer system language over file-changelog language.
- Make the packet self-contained: the planner should not need to read the whole repo to propose a next step.
- If the planner needs more context, that signals an escalation condition, not a packet deficiency.
- Keep the artifact thin: one current packet, not a growing archive.
