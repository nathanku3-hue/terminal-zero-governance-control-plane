# Operationalized Multi-Worker Concurrency TODO (Deferred)

Status: FROZEN (deferred by decision)  
Owner: PM  
Created: 2026-03-05  
Decision Ref: D-137  
Directive Ref: PM-24C-018

## Decision

Document multi-worker concurrency now, but freeze implementation.

Rationale:
- Current system is already high-elegance and operationally stable.
- Immediate value is execution quality, not additional orchestration complexity.
- Build only after real bottlenecks appear in live cycles.

## Unfreeze Criteria (Any One Trigger)

1. Cross-track blockers (`frontend/backend/qa`) repeat for 2+ cycles.
2. Manual merge/reconciliation consumes more than 20% of cycle time.
3. Disagreement codes tied to dependency conflicts recur for 2+ weeks.
4. CEO packet delays are caused by multi-track ambiguity, not missing evidence.

## Scope When Activated

1. Track-scoped round contracts:
   - one contract each for `frontend`, `backend`, `qa`
   - explicit dependency fields (`depends_on_tracks`, `blocks_tracks`)
2. Fan-out context packets:
   - generate one scoped context packet per track
   - include only required evidence and constraints for that track
3. Fan-in merge packet:
   - aggregate all track outcomes into a single auditor packet
   - deterministic conflict section for contradictions
4. Merge closure gate:
   - `INTEGRATION_READY` only when all required tracks are PASS and conflicts resolved
5. Memory partition:
   - short-term per-track memory (`*_latest`)
   - shared canonical memory for cross-track decisions only

## Out of Scope (Until Unfreeze)

- No new concurrency scheduler.
- No autonomous cross-track arbitration.
- No additional expert layers by default.
- No dashboard/UI expansion.

## Minimal Artifact Plan (When Activated)

- `docs/context/track_frontend_status_latest.json`
- `docs/context/track_backend_status_latest.json`
- `docs/context/track_qa_status_latest.json`
- `docs/context/track_merge_packet_latest.json`
- `docs/context/track_merge_packet_latest.md`
- `docs/context/track_dependency_map_latest.json`

## Context and Memory Flow (Target Model)

1. Startup captures one parent intent contract.
2. Parent contract splits into track contracts with bounded scope.
3. Fan-out context generated per track (least necessary context).
4. Worker execution happens independently per track.
5. Auditor validates each track independently.
6. Fan-in merge packet composes track results.
7. Merge gate decides `INTEGRATION_READY` vs `NOT_READY`.
8. CEO packet generated only from merge packet (single authority source).

## Anti-Overengineering Guardrails

- Cap active tracks to 3 (`frontend`, `backend`, `qa`) until proven need.
- No new governance role added for track orchestration.
- If one additional script cannot show measurable cycle-time reduction in 2 weeks, rollback.
- Keep closure authority unchanged: Auditor verdict + CEO GO/HOLD/REFRAME.

## Success Metrics (Post-Unfreeze)

- Integration lead time reduced by >=20%.
- Cross-track disagreement recurrence reduced by >=30% over 4 weeks.
- No increase in false escalation rate.
- CEO packet latency reduced by >=25%.

## First Command (When Unfreezing)

Use this only after unfreeze trigger confirmation:

```powershell
.venv\Scripts\python scripts/run_loop_cycle.py --repo-root . --skip-phase-end --allow-hold true
```

