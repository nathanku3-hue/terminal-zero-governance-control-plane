# Planner Escalation Rules

> **Canonical source:** src/sop/templates/planner_escalation_rules_template.md
> This copy in docs/templates/ is a workspace mirror. Do not edit here — edit the canonical source instead.

Status: Template
Authority: advisory-only integration artifact. This file does not authorize execution, promotion, or scope widening by itself.
Purpose: define explicit rules for when the planner should escalate from small packets to wider repo reads.

## Philosophy

The planner should be **ultra state aware** but **not repo-wide by default**.

The default strategy is:

1. Load planner packet (current context, active brief, bridge truth, decision tail, blocked next step, active bottleneck)
2. Load impact packet (changed files, owned files, touched interfaces, failing checks)
3. Propose next step from these small packets
4. Only escalate to wider reads when one of the four escalation conditions applies

## Escalation Conditions

### Condition 1: Impact Surface Is Unclear

**When to escalate:**
- The planner packet + impact packet do not contain enough information to identify which files/interfaces are affected
- The changed files list is incomplete or ambiguous
- The owned files list does not cover the files that need to be modified

**What to read:**
- Targeted file search (e.g., `grep` for interface usage, `glob` for file patterns)
- Module dependency graph (if available)
- Interface ownership map (if available)

**Do NOT read:**
- The entire codebase
- All files in a directory tree

### Condition 2: Interface Ownership Is Unclear

**When to escalate:**
- The touched interfaces list does not make it clear which subsystem owns a particular interface
- The multi-stream contract does not define ownership for a particular interface
- Multiple streams claim ownership of the same interface

**What to read:**
- Multi-stream contract
- Interface ownership map (if available)
- Targeted file search for interface definition

**Do NOT read:**
- All files that import/use the interface
- The entire codebase

### Condition 3: Evidence Conflicts

**When to escalate:**
- The bridge truth and decision tail contain conflicting information
- The planner packet says one thing, but the impact packet says another
- The done checklist says complete, but failing checks say not complete

**What to read:**
- Decision log (full, not just tail)
- Evidence artifacts (test results, review packets, runtime artifacts)
- Targeted file reads to resolve the conflict

**Do NOT read:**
- The entire codebase
- All evidence artifacts from all phases

### Condition 4: Bottleneck Cannot Be Named

**When to escalate:**
- The active bottleneck is not clear from current context
- The post-phase alignment does not identify the bottleneck
- Multiple streams claim to be the bottleneck

**What to read:**
- Multi-stream contract
- Post-phase alignment
- Targeted file search for failing checks or blocked work

**Do NOT read:**
- The entire codebase
- All stream status artifacts

## Non-Escalation Conditions

The planner should **NOT** escalate in these cases:

1. **Curiosity**: The planner wants to know more about the codebase but does not need it to propose a next step
2. **Completeness**: The planner wants to read all files in a directory to be thorough
3. **Verification**: The planner wants to verify that the packets are correct by reading the source files
4. **Exploration**: The planner wants to explore the codebase to understand the architecture

These are all valid activities, but they should be done **after** proposing a next step from the small packets, not before.

## Escalation Process

When an escalation condition is met:

1. **Name the condition**: Explicitly state which of the four escalation conditions applies
2. **Name the gap**: Explicitly state what information is missing from the small packets
3. **Name the read strategy**: Explicitly state what files/artifacts will be read and why
4. **Execute the read**: Read only the targeted files/artifacts, not the entire codebase
5. **Update the proposal**: Revise the next-step proposal based on the new information

## Success Criteria

The escalation rules are working when:

- The planner proposes a next step from small packets first (default case)
- Whole-repo rereads become the exception, not the default
- Escalations are explicit and justified (one of the four conditions applies)
- Escalations are targeted (read only what is needed, not the entire codebase)

## Anti-Patterns

The escalation rules are **not** working when:

- The planner reads the entire codebase by default
- The planner escalates without naming the condition or gap
- The planner escalates for curiosity, completeness, verification, or exploration
- The planner reads all files in a directory tree instead of targeted files

## Writing Rules
- Keep this file compact and PM-readable.
- Make the escalation conditions explicit and checkable.
- Make the non-escalation conditions explicit to prevent over-reading.
- Keep the artifact thin: one current ruleset, not a growing archive.
