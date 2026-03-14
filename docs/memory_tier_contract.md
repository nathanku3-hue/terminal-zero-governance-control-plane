# Memory Tier Contract

This contract defines memory-loading tiers for the current loop artifacts consumed or emitted by:

- `scripts/build_exec_memory_packet.py`
- `scripts/evaluate_context_compaction_trigger.py`

This document is intentionally separate from `docs/ARTIFACT_POLICY.md`.
Artifact authority answers which file is canonical.
Memory tiers answer what should stay hot, what may stay warm, and what must remain cold or manual-load only.

## Tier Definitions

- `hot`: current loop execution state or machine state that the active loop reads or writes directly.
- `warm`: latest validated governance artifacts or derived handoff surfaces that the active loop uses by default.
- `cold`: deep-dive or historical evidence that remains reachable, but is not part of the default packet/compaction context.

## Shared Source Of Truth

- Code-owned mapping: `scripts/utils/memory_tiers.py`
- This document describes that same model in prose/table form.
- If the table and code drift, the code mapping wins until the doc is updated.

## Active Families

| Family | Representative paths | Tier | Access | Why |
|---|---|---|---|---|
| `loop_cycle_summary` | `docs/context/loop_cycle_summary_latest.json`, `docs/context/loop_cycle_summary_current.json` | `hot` | `default_input` | Current loop execution state and blockers. |
| `exec_memory_packet` | `docs/context/exec_memory_packet_latest.json`, `docs/context/exec_memory_packet_latest_current.json` | `hot` | `derived_output` | Current machine memory packet consumed by later loop stages and compaction checks. |
| `exec_memory_build_status` | `docs/context/exec_memory_packet_build_status_latest.json`, `docs/context/exec_memory_packet_build_status_current.json` | `hot` | `derived_output` | Build-integrity state for the current packet. |
| `context_compaction_state` | `docs/context/context_compaction_state_latest.json` | `hot` | `default_input` | Rolling compaction state reused by the next trigger evaluation. |
| `context_compaction_status` | `docs/context/context_compaction_status_latest.json` | `hot` | `derived_output` | Latest compaction-trigger verdict. |
| `auditor_promotion_dossier` | `docs/context/auditor_promotion_dossier.json` | `warm` | `default_input` | Promotion criteria, FP summary, and per-rule breakdown used by default. |
| `auditor_calibration_report` | `docs/context/auditor_calibration_report.json` | `warm` | `default_input` | Current calibration totals and weekly audit summary. |
| `ceo_go_signal` | `docs/context/ceo_go_signal.md` | `warm` | `default_input` | Current action state and blocking reasons. |
| `decision_log` | `docs/decision log.md` | `warm` | `default_input` | Recent governance decisions currently summarized into PM memory. |
| `milestone_expert_roster` | `docs/context/milestone_expert_roster_latest.json` | `warm` | `default_input` | Current approved roster for expert-lineup decisions. |
| `project_skill_config` | `.sop_config.yaml` | `warm` | `default_input` | Project-local skill activation context. |
| `extension_allowlist` | `extension_allowlist.yaml` | `warm` | `default_input` | Allowlist backing skill activation visibility. |
| `skill_registry` | `skills/registry.yaml` | `warm` | `default_input` | Skill metadata backing the activation surface. |
| `next_round_handoff` | `docs/context/next_round_handoff_latest.json` | `warm` | `derived_output` | Latest handoff surface derived from current loop artifacts. |
| `expert_request` | `docs/context/expert_request_latest.json` | `warm` | `derived_output` | Latest specialist request surface derived from current loop artifacts. |
| `pm_ceo_research_brief` | `docs/context/pm_ceo_research_brief_latest.json` | `warm` | `derived_output` | Latest PM/CEO research brief derived from current loop artifacts. |
| `board_decision_brief` | `docs/context/board_decision_brief_latest.json` | `warm` | `derived_output` | Latest board decision brief derived from current loop artifacts. |
| `skill_activation` | `docs/context/skill_activation_latest.json` | `warm` | `derived_output` | Current skill-activation view derived from config and allowlist inputs. |

## Cold Manual Fallback

| Family | Representative paths | Tier | Access | Why |
|---|---|---|---|---|
| `auditor_fp_ledger` | `docs/context/auditor_fp_ledger.json` | `cold` | `manual_fallback` | Ledger-level deep dives stay reachable for human investigation, but they are not part of the default packet or compaction path. |

## C1 Boundaries

- This first pass covers only the active memory families used or emitted by the two scripts above.
- This contract does not change thresholds, trigger semantics, routing, or autonomous compaction behavior.
- Cold/manual families remain reachable through explicit human review paths; they are not default packet context.
