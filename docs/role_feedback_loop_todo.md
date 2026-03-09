# Role Feedback Loop TODO (Lean)

Status: Deferred (post-24C promotion)
Owner: PM
Created: 2026-03-04

## Decision
Implement a per-round feedback loop for Worker/Auditor/CEO, but keep a single lessons source of truth.

Do NOT split into separate `lessons.md` files per role at this stage.

Rationale:
- Multiple lesson files increase drift risk and review overhead.
- One source with role tags keeps history consistent and searchable.
- Current priority remains operational closure (C3 + C1), not process expansion.

## Scope (When Activated)
1. Keep `docs/lessonss.md` as canonical log.
2. Add role metadata to each new lesson entry:
   - `source_role`: `worker|auditor|ceo`
   - `round_id`: `<run_id or round tag>`
   - `severity`: `low|medium|high`
3. Require one compact lesson entry after each completed round:
   - Worker: implementation/process miss or efficiency gain.
   - Auditor: risk/scope miss and prevention rule.
   - CEO/PM: decision-quality or prioritization miss.

## Out of Scope (For This TODO)
- No new scripts/services.
- No separate per-role lesson files.
- No dashboard/UI.

## Minimal Operating Contract
Per round close, append up to 3 lines total (one per role) using this format:

| Date | Scope | Source Role | Round ID | Mistake/Miss | Root Cause | Guardrail | Evidence |
|---|---|---|---|---|---|---|---|
| YYYY-MM-DD | `<phase/task>` | `worker|auditor|ceo` | `<run_id>` | `<one line>` | `<one line>` | `<one line>` | `<path/test/log>` |

## Activation Criteria
Activate after:
1. C3 passes (2 qualifying weeks complete), and
2. C1 manual signoff prep is done, and
3. Canary enforce plan is queued.

## Success Metrics (Post-Activation)
- 100% rounds have at least Worker + Auditor entries.
- Repeated issue rate decreases over 4 weeks.
- HOLD/REFRAME root causes become more specific and trend down.

