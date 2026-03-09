# Logic Spine Index (Canonical)

Status: Canonical index  
Purpose: Maintain one auditable logic spine for major governance/architecture decisions.

## Spine Records

| SpineID | Domain | Canonical Source | Owner Role | Notes |
|---|---|---|---|---|
| LS-001 | Loop governance and authority | `docs/loop_operating_contract.md` | PM/Orchestrator | Source-of-truth for loop authority and escalation semantics. |
| LS-002 | Pragmatic change discipline | `docs/pragmatic_sop.md` | PM/Orchestrator | Five-rule policy (manifest-first, single spine, role split, lifecycle tiers, boundary coding). |
| LS-003 | Runtime operations procedure | `docs/runbook_ops.md` | Ops | Command-level operations and troubleshooting guidance. |

## Update Rule

- Any big change (cross-module/architecture/high-risk) must update this index before coding starts.
- If a proposal cannot map to one existing spine record, add a new `SpineID` first.
