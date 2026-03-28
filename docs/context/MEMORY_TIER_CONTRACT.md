# Memory Tier Contract

> Version: 1.0
> Updated: 2026-03-28
> Source of truth: `src/sop/scripts/utils/memory_tiers.py` (`_MEMORY_TIER_FAMILIES`)
> Do NOT parse this file at runtime — import `_MEMORY_TIER_FAMILIES` directly.

All artifacts in `docs/context/` are classified into exactly one of three tiers.
This document is the human-readable companion to the code-authoritative
`_MEMORY_TIER_FAMILIES` dict in `memory_tiers.py`.

---

## Tier Assignment Rules

1. An artifact is **hot** if the orchestrator needs it before the first step runs.
2. An artifact is **warm** if the planner or bridge needs it but workers do not.
3. Everything else is **cold**.

---

## Hot Tier (loaded every run)

Artifacts the orchestrator loads unconditionally on startup.

| Artifact | Family key |
|---|---|
| `docs/context/loop_cycle_summary_latest.json` | `loop_cycle_summary` |
| `docs/context/loop_cycle_summary_latest.md` | `loop_cycle_summary` |
| `docs/context/loop_cycle_summary_current.json` | `loop_cycle_summary` |
| `docs/context/exec_memory_packet_latest.json` | `exec_memory_packet` |
| `docs/context/exec_memory_packet_latest.md` | `exec_memory_packet` |
| `docs/context/exec_memory_packet_latest_current.json` | `exec_memory_packet` |
| `docs/context/exec_memory_packet_latest_current.md` | `exec_memory_packet` |
| `docs/context/exec_memory_packet_build_status_latest.json` | `exec_memory_build_status` |
| `docs/context/exec_memory_packet_build_status_current.json` | `exec_memory_build_status` |
| `docs/context/context_compaction_state_latest.json` | `context_compaction_state` |
| `docs/context/context_compaction_status_latest.json` | `context_compaction_status` |
| `docs/context/loop_run_trace_latest.json` | `loop_run_trace` |
| `docs/context/loop_cycle_checkpoint_latest.json` | `loop_cycle_checkpoint` |
| `docs/context/orchestrator_state_latest.json` | `orchestrator_state` |

---

## Warm Tier (loaded when referenced)

Artifacts the planner or bridge loads when needed; not loaded on every run.

| Artifact | Family key |
|---|---|
| `docs/context/auditor_promotion_dossier.json` | `auditor_promotion_dossier` |
| `docs/context/auditor_promotion_dossier.md` | `auditor_promotion_dossier` |
| `docs/context/auditor_calibration_report.json` | `auditor_calibration_report` |
| `docs/context/auditor_calibration_report.md` | `auditor_calibration_report` |
| `docs/context/ceo_go_signal.md` | `ceo_go_signal` |
| `docs/decision log.md` | `decision_log` |
| `docs/context/milestone_expert_roster_latest.json` | `milestone_expert_roster` |
| `.sop_config.yaml` | `project_skill_config` |
| `extension_allowlist.yaml` | `extension_allowlist` |
| `skills/registry.yaml` | `skill_registry` |
| `docs/context/next_round_handoff_latest.json` | `next_round_handoff` |
| `docs/context/next_round_handoff_latest.md` | `next_round_handoff` |
| `docs/context/expert_request_latest.json` | `expert_request` |
| `docs/context/expert_request_latest.md` | `expert_request` |
| `docs/context/pm_ceo_research_brief_latest.json` | `pm_ceo_research_brief` |
| `docs/context/pm_ceo_research_brief_latest.md` | `pm_ceo_research_brief` |
| `docs/context/board_decision_brief_latest.json` | `board_decision_brief` |
| `docs/context/board_decision_brief_latest.md` | `board_decision_brief` |
| `docs/context/skill_activation_latest.json` | `skill_activation` |
| `docs/context/phase_gate_a_latest.json` | `phase_gate_a` |
| `docs/context/phase_gate_b_latest.json` | `phase_gate_b` |
| `docs/context/phase_handoff_latest.json` | `phase_handoff` |
| `docs/context/run_drift_latest.json` | `run_drift` |
| `docs/context/rollback_latest.json` | `rollback` |
| `docs/context/bridge_contract_current.md` | `bridge_contract` |
| `docs/context/bridge_contract_current.json` | `bridge_contract` |
| `docs/context/planner_packet_current.md` | `planner_packet` |
| `docs/context/planner_packet_current.json` | `planner_packet` |

---

## Cold Tier (load on explicit demand only)

Historical or bulk artifacts loaded only when explicitly requested.

| Artifact | Family key |
|---|---|
| `docs/context/auditor_fp_ledger.json` | `auditor_fp_ledger` |
| `docs/context/loop_run_steps_latest.ndjson` | `loop_run_steps` |
| `docs/context/run_regression_baseline.ndjson` | `run_regression_baseline` |
| `docs/context/worker_merge_latest.json` | `worker_merge` |
| `docs/context/loop_run_trace_master_latest.json` | `loop_run_trace_master` |

---

## Compaction Rules by Tier

| Tier | Compaction rule |
|---|---|
| hot | Never compacted; always retained in full |
| warm | No-op in Phase 5 (in-place overwrite each run; no accumulation) |
| cold NDJSON | Rolling window: keep last N records (per-family default) |
| cold non-NDJSON | Retained until explicit archive trigger (`--prune`) |

### Default rolling windows (cold NDJSON)

| Family | Max records |
|---|---|
| `run_regression_baseline` | 100 |
| `loop_run_steps` | 500 |
| Any new cold NDJSON | 200 (unless overridden) |
