# Compaction Behavior Contract

This contract defines C2 compaction behavior hardening for the current loop.

It is separate from:

- `docs/ARTIFACT_POLICY.md` (authority and git policy)
- `docs/memory_tier_contract.md` (hot/warm/cold loading tiers)

## Decision Split

- `should_compact`: recommendation signal from existing triggers (thresholds, action/criteria changes, staleness).
- `can_compact`: permission signal after guardrail checks.
- `decision_mode`:
  - `no_action`: no compaction recommendation
  - `recommend_compact`: recommendation exists and guardrails pass
  - `blocked_guardrail`: recommendation exists but required retention guardrails fail

## Source Of Truth

- Code mapping: `scripts/utils/compaction_retention.py`
- Trigger application: `scripts/evaluate_context_compaction_trigger.py`
- Loop summary surfacing: `scripts/run_loop_cycle.py`

## Retention Rules

### Required Always

These packet sections must be present before compaction is allowed:

- `next_round_handoff`
- `expert_request`
- `pm_ceo_research_brief`
- `board_decision_brief`

### Required If Present

These packet sections are retained when present, but do not block compaction if absent:

- `replanning`
- `automation_uncertainty_status`

### Cold Manual Fallback

These remain manual-load evidence and are not default compaction context:

- `auditor_fp_ledger` (`docs/context/auditor_fp_ledger.json`)

## C2 Scope Limits

- No threshold-value changes.
- No routing or skill-execution changes.
- No autonomous compaction executor in C2.
- Focus is deterministic rationale and retention guardrails only.
