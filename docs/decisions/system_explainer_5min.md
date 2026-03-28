# System Explainer — 5 Minutes

> Max 500 words. No phase-specific jargon. Cold-read target: anyone who has not read the codebase.
> Pending human sign-off per 7.2-G7 (async written review).

---

## What this system does

This system helps a small team run engineering work reliably when much of that work is done by AI models. The core problem: AI models lose context, drift from the plan, and produce output that nobody checks against the original goal. This system solves that with a structured loop and a small set of persistent documents.

## The loop

Every round of work follows the same cycle:

1. **Plan.** A planner reads a compact summary packet — not the whole codebase — and decides what to do next.
2. **Execute.** Workers carry out one bounded slice of work and write their results to disk.
3. **Translate.** After execution, the system automatically writes three documents: a bridge contract (what happened, in plain language), a planner packet (what the planner needs to know next), and an orchestrator state (the system's own memory of where it is).
4. **Compact.** Old artifacts are tiered by importance and pruned so the context stays small.
5. **Repeat.** The planner enters the next round from the packet, not from a full re-read.

This loop is the same regardless of what kind of work is being done.

## The three truth documents

- **Bridge contract:** Translates raw execution results into plain-language next-step guidance. Written after every run.
- **Planner packet:** The sole entry point for the next planning round. Contains just enough context to plan without re-reading the whole repo.
- **Orchestrator state:** The system's self-memory. Tracks what is active, what is blocked, and what changed.

These three documents are written unconditionally — even when a run is blocked or held. They survive rollbacks.

## What the human does

The human stays at the judgment layer:
- Decide what problem matters right now.
- Review output and decide whether to continue, change direction, or stop.
- Sign off on phase gates before work advances.

The human does not manually compile status, re-read raw logs, or chase down what happened. The bridge contract answers that.

## What keeps it honest

- **Governance gates:** Automated checks run after every cycle. They must pass before work advances.
- **Rollback:** If a run produces a blocked result, the context directory reverts to its prior state. The bridge/planner/state documents are written outside rollback scope so the planner always has a current view.
- **Lessons log:** Repeated mistakes are recorded with root cause and guardrail. The log is authoritative and append-only.
- **Artifact lifecycle:** Every file in the context directory is classified as hot, warm, or cold. Orphaned files are flagged and can be archived with a single flag.

## In one sentence

This is a structured loop that turns bounded AI execution into reliable, human-reviewable output — by keeping three truth documents current after every run and never letting context grow unchecked.

---

*Word count: ~430. Human reviewer: pass if (a) no phase-specific jargon and (b) loop structure is clear in one read.*
