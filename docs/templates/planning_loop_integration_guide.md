# Planning Loop Integration Guide

Status: Template
Authority: advisory-only integration artifact. This file does not authorize execution, promotion, or scope widening by itself.
Purpose: define how pre-flight planning, worker/auditor execution, and post-phase alignment integrate into one recurring planning loop.

## Philosophy

The worker/auditor loop is good at bounded execution and bounded review.

It is not the right place to solve cross-stream coordination by itself.

For multi-stream work, separate the static part from the dynamic part:

- **Pre-flight planning** defines the map before execution starts
- **Worker/auditor loop** moves one bounded piece on the map
- **Post-phase alignment** updates the map after a major round or phase

This is the least-drifty design for complex systems.

## Planning Loop Stages

### Stage 1: Pre-Flight Planning

**When**: Before execution begins on a new phase, round, or feature

**Purpose**: Define the multi-stream map

**Artifacts created**:
- `multi_stream_contract_current.md`
- `planner_packet_current.md` (initial)
- `impact_packet_current.md` (initial, may be empty)

**What gets defined**:
- What streams exist (Backend, Frontend/UI, Data, Docs/Ops, etc.)
- Why they exist
- What each stream must deliver
- How streams connect
- What the shared success condition is
- Which stream is active now
- Which streams are deferred
- What must be true before execution begins

**Success criteria**:
- Multi-stream contract exists and is approved
- All streams understand their boundaries and dependencies
- Active stream is clear
- Shared success condition is explicit

### Stage 2: Bounded Execution

**When**: During active phase/round execution

**Purpose**: Move one bounded piece on the map

**Artifacts updated**:
- `planner_packet_current.md` (refreshed after each execution cycle)
- `impact_packet_current.md` (refreshed after each execution cycle)
- `bridge_contract_current.md` (refreshed after execution completes)
- `done_checklist_current.md` (checked after execution completes)

**What happens**:
- Worker executes bounded scope
- Auditor reviews execution
- Planner proposes next step from small packets (planner packet + impact packet)
- Planner escalates to wider reads only when escalation conditions apply

**Success criteria**:
- Execution stays within bounded scope
- Planner proposes next step from small packets first
- Whole-repo reread becomes exception, not default
- Bridge contract stays fresh

### Stage 3: Post-Phase Alignment

**When**: After a major round or phase completes

**Purpose**: Update the multi-stream map

**Artifacts created/updated**:
- `post_phase_alignment_current.md`
- `multi_stream_contract_current.md` (updated if stream status changed)
- `planner_packet_current.md` (refreshed with new bottleneck/blocked scope)

**What gets updated**:
- What changed this round (system shape delta, execution delta, no change)
- Stream status update (what changed, what remains, what is blocked)
- Current bottleneck (which stream is now the bottleneck, why, what unblocks it)
- Interface drift (what interface assumptions changed, what cross-stream contracts need updating)
- Next stream active (which stream should be active next, why)
- PM decision required (what PM decision is now required, what evidence supports it)
- What should not be done next

**Success criteria**:
- Post-phase alignment exists and is approved
- All streams understand the new bottleneck
- Next active stream is clear
- PM decision is explicit (if required)

## Integration Pattern

### Pattern 1: New Phase/Round Kickoff

```
1. PM/CEO approves new phase/round scope
2. Create pre-flight planning artifacts:
   - multi_stream_contract_current.md
   - planner_packet_current.md (initial)
   - impact_packet_current.md (initial)
3. Approve pre-flight planning
4. Begin bounded execution (Stage 2)
```

### Pattern 2: Bounded Execution Cycle

```
1. Planner loads small packets:
   - planner_packet_current.md
   - impact_packet_current.md
2. Planner proposes next step from small packets
3. If escalation condition applies:
   - Name the condition
   - Name the gap
   - Name the read strategy
   - Execute targeted read
   - Update proposal
4. Worker executes bounded scope
5. Auditor reviews execution
6. Update artifacts:
   - planner_packet_current.md (refresh)
   - impact_packet_current.md (refresh)
   - bridge_contract_current.md (refresh)
   - done_checklist_current.md (check)
7. If phase/round complete, proceed to Stage 3
8. If phase/round not complete, repeat from step 1
```

### Pattern 3: Post-Phase Alignment

```
1. Create post_phase_alignment_current.md
2. Update multi_stream_contract_current.md (if stream status changed)
3. Update planner_packet_current.md (refresh with new bottleneck/blocked scope)
4. PM/CEO reviews post-phase alignment
5. If PM decision required:
   - PM/CEO makes decision
   - Record decision in decision log
   - Update planner_packet_current.md with decision outcome
6. If next phase/round approved, return to Pattern 1
7. If standby mode, wait for explicit approval packet
```

## Artifact Refresh Rules

### Planner Packet

**Refresh frequency**: After each bounded execution cycle

**What gets refreshed**:
- Current context (what system exists now, active scope, blocked scope)
- Bridge truth (system delta, PM delta, open decision, recommended next step)
- Decision tail (add new decisions from decision log)
- Blocked next step (update if unblocked or new blocker appears)
- Active bottleneck (update if bottleneck changes)

**What stays stable**:
- Active brief (only changes when phase/round changes)
- Escalation rules (only changes when governance rules change)

### Impact Packet

**Refresh frequency**: After each bounded execution cycle

**What gets refreshed**:
- Changed files (add new files modified in this cycle)
- Owned files (update if ownership changes)
- Touched interfaces (add new interfaces modified in this cycle)
- Failing checks (update with latest test/lint/smoke/CI results)
- Cross-stream impact (update if new streams affected)

**What stays stable**:
- Escalation signals (only changes when governance rules change)

### Bridge Contract

**Refresh frequency**: After bounded execution completes

**What gets refreshed**:
- Live truth now (system now, active scope, blocked scope)
- What changed this round (system delta, execution delta, no change)
- PM / product delta (stronger now, weaker now, still unknown)
- Planner bridge (open decision, recommended next step, why this next, not recommended next)

**What stays stable**:
- Static truth inputs (only changes when PM docs change)
- Locked boundaries (only changes when governance decisions change)

### Multi-Stream Contract

**Refresh frequency**: After post-phase alignment (when stream status changes)

**What gets refreshed**:
- Stream status (active, deferred, blocked, complete)
- Active stream now (which stream is active)
- Deferred streams (which streams are deferred, why)
- Blocked streams (which streams are blocked, what they are blocked on)

**What stays stable**:
- Stream map (only changes when new streams added or removed)
- Shared success condition (only changes when phase/round goal changes)

### Post-Phase Alignment

**Refresh frequency**: After each major round or phase completes

**What gets refreshed**:
- Everything (this is a new artifact for each phase/round)

**What stays stable**:
- Nothing (this is a snapshot artifact, not a living document)

## Success Criteria

The planning loop integration is working when:

- Pre-flight planning defines the map before execution starts
- Bounded execution moves one piece on the map without drifting
- Post-phase alignment updates the map after major rounds
- Planner proposes next step from small packets first
- Whole-repo reread becomes exception, not default
- Multi-stream work stays coordinated (no local loops)
- PM sees system truth instead of raw agent chatter

## Anti-Patterns

The planning loop integration is **not** working when:

- Execution starts without pre-flight planning
- Streams drift into local loops (no cross-stream coordination)
- Post-phase alignment is skipped (map becomes stale)
- Planner reads whole repo by default (small packets ignored)
- PM sees raw agent chatter instead of system truth
- Artifacts are not refreshed (planner works from stale data)

## Writing Rules
- Keep this file compact and PM-readable.
- Make the integration pattern explicit and repeatable.
- Make the artifact refresh rules explicit and checkable.
- Keep the artifact thin: one current guide, not a growing archive.
