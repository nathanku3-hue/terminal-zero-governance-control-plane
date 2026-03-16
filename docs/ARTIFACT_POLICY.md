# Artifact Policy: Active Control-Plane Artifact Classes

## Purpose

This policy defines the approved artifact boundary for the current governance control plane.
It separates three different questions that were previously conflated:

1. **Authority status**: whether an artifact is canonical, a convenience mirror, a generated intermediate, an optional overlay, or invalid drift.
2. **Retention class**: whether the artifact is meant to persist as current-state runtime output, short-lived staging state, optional operator visibility, or archive-only history.
3. **Git policy**: whether the artifact should be ignored, selectively retained, or treated as invalid and removed.

Canonical authority does **not** imply committed source. Most active control-plane artifacts are generated runtime state even when they are authoritative for the latest run.

## Source Files (Committed)

These files remain human-authored source of truth and are expected to be committed:

- **Scripts**: `scripts/*.py`, `scripts/*.ps1`, `scripts/*.sh`
- **Tests**: `tests/**/*.py`
- **Documentation**: `AGENTS.md`, `README.md`, `OPERATOR_LOOP_GUIDE.md`, `docs/*.md`, `docs/templates/*.md`, `docs/phase_brief/*.md`
- **Configuration**: `*.yaml`, `*.toml`, and hand-authored `*.json`
- **Skills**: `.codex/skills/**/*`, `skills/**/*`
- **Curated operator docs**: files intentionally maintained by humans as operator-facing source documents rather than machine-written runtime output

## Active Control-Plane Rules

- Canonical runtime authority stays under `docs/context` unless a table row says otherwise.
- Repo-root mirrors are convenience-only and must be limited to the approved set.
- `*_current` files and build-status files are generated intermediates and are never authoritative.
- Workflow overlays are optional, non-authoritative operator visibility outputs.
- The nested `quant_current_scope/...` tree is invalid generated drift unless it is explicitly reclassified later as fixture or archive material.
- The **Git policy** column below describes the intended steady-state boundary for P0.3 enforcement, even when current `.gitignore` coverage is not yet aligned.

## Active Control-Plane Artifact Inventory

This table covers the active startup -> loop -> closure -> takeover path plus optional overlays and optional supervision.

| Artifact family | Writer seam | Canonical path | Mirror path | Authority status | Retention class | Git policy | Notes |
|---|---|---|---|---|---|---|---|
| Startup bundle | `scripts/startup_codex_helper.py` | `docs/context/startup_intake_latest.json`, `docs/context/startup_intake_latest.md`, `docs/context/init_execution_card_latest.md`, `docs/context/round_contract_seed_latest.md` | None | Canonical | Current-state startup outputs | Ignore as generated current-state | Latest startup run only |
| Loop summary latest | `scripts/run_loop_cycle.py` final summary write | `docs/context/loop_cycle_summary_latest.json`, `docs/context/loop_cycle_summary_latest.md` | None | Canonical | Current-state loop summary | Ignore as generated current-state | Latest loop-cycle contract summary |
| Loop summary current snapshot | `scripts/run_loop_cycle.py:670` and `scripts/loop_cycle_runtime.py:145` | `docs/context/loop_cycle_summary_current.json` | None | Generated intermediate, non-authoritative | Per-cycle staging / scratch | Ignore and do not commit | Input to exec-memory build only |
| Governance assessment outputs | `scripts/run_loop_cycle.py` via `auditor_calibration_report.py`, `generate_ceo_go_signal.py`, and `generate_ceo_weekly_summary.py` | `docs/context/auditor_calibration_report.json`, `docs/context/auditor_calibration_report.md`, `docs/context/auditor_promotion_dossier.json`, `docs/context/auditor_promotion_dossier.md`, `docs/context/ceo_go_signal.md`, `docs/context/ceo_weekly_summary_latest.md` | None | Canonical | Current-state governance assessment | Ignore as generated current-state | Supporting current-run governance state |
| Exec-memory latest outputs | `scripts/run_loop_cycle.py:535` promotion boundary | `docs/context/exec_memory_packet_latest.json`, `docs/context/exec_memory_packet_latest.md` | None | Canonical | Current-state executive memory | Ignore as generated current-state | Latest promoted exec-memory contract |
| Exec-memory current staging outputs | `scripts/run_loop_cycle.py` exec-memory build stage | `docs/context/exec_memory_packet_latest_current.json`, `docs/context/exec_memory_packet_latest_current.md` | None | Generated intermediate, non-authoritative | Per-cycle staging | Ignore and do not commit | Must never replace the promoted latest outputs |
| Exec-memory build status | `scripts/run_loop_cycle.py` via `build_exec_memory_packet.py` | `docs/context/exec_memory_packet_build_status_current.json` | None | Generated intermediate, non-authoritative | Per-cycle staging | Ignore and do not commit | Promotion-control artifact only |
| Closure outputs | `scripts/validate_loop_closure.py` via `scripts/run_loop_cycle.py` | `docs/context/loop_closure_status_latest.json`, `docs/context/loop_closure_status_latest.md` | None | Canonical | Current-state closure verdict | Ignore as generated current-state | Latest readiness signal |
| Advisory outputs under `docs/context` | `scripts/loop_cycle_artifacts.py:451` | `docs/context/next_round_handoff_latest.json`, `docs/context/next_round_handoff_latest.md`, `docs/context/expert_request_latest.json`, `docs/context/expert_request_latest.md`, `docs/context/pm_ceo_research_brief_latest.json`, `docs/context/pm_ceo_research_brief_latest.md`, `docs/context/board_decision_brief_latest.json`, `docs/context/board_decision_brief_latest.md` | Approved repo-root mirrors only | Canonical | Current-state advisory outputs | Ignore as generated current-state | `docs/context` remains authoritative |
| Skill activation output | `scripts/loop_cycle_artifacts.py` `_persist_skill_activation()` | `docs/context/skill_activation_latest.json` | None | Canonical | Current-state supporting artifact | Ignore as generated current-state | Derived from exec-memory payload |
| Repo-root advisory mirrors | `scripts/loop_cycle_artifacts.py:514` | Authority stays in `docs/context` advisory outputs | `NEXT_ROUND_HANDOFF_LATEST.md`, `EXPERT_REQUEST_LATEST.md`, `PM_CEO_RESEARCH_BRIEF_LATEST.md`, `BOARD_DECISION_BRIEF_LATEST.md` | Convenience mirror only | Convenience mirror | Ignore and limit to this approved set | No additional repo-root advisory mirror names are approved |
| Repo-root takeover index | `scripts/loop_cycle_artifacts.py:514` | No separate canonical authority; indexes canonical advisory outputs under `docs/context` | `TAKEOVER_LATEST.md` | Convenience mirror only | Convenience mirror | Ignore and limit to this approved file | Convenience-only index over approved repo-root mirrors |
| Workflow status overlays | `scripts/print_takeover_entrypoint.py:1188` | `docs/context/workflow_status_latest.json`, `docs/context/workflow_status_latest.md` when requested | None | Optional overlay, non-authoritative | Optional operator visibility output | Ignore when present | Overlay generation is non-fatal and not a separate authority path |
| Compaction state and status | `scripts/run_loop_cycle.py` via `evaluate_context_compaction_trigger.py` | `docs/context/context_compaction_state_latest.json`, `docs/context/context_compaction_status_latest.json` | None | Canonical supporting artifact | Current-state supporting output | Ignore as generated current-state | Internal operator signal only |
| Lessons outputs | `scripts/loop_cycle_runtime.py` lessons stub writer | `docs/context/lessons_worker_latest.md`, `docs/context/lessons_auditor_latest.md` | None | Canonical supporting artifact | Current-state supporting output | Ignore as generated current-state | Rewritten on loop initialization |
| Supervisor outputs | `scripts/supervise_loop.py` | `docs/context/supervisor_status_latest.json`, `docs/context/supervisor_alerts_latest.md` | None | Optional canonical output | Optional supervision output | Ignore when present | Only when supervision is explicitly run |
| Nested repo-like mirror tree | No approved writer seam; observed worktree drift | None | `quant_current_scope/` subtree | Invalid generated drift unless explicitly reclassified | Invalid drift | Must not be committed; remove or reclassify in enforcement work | Outside the approved active product surface |

## Archive and Historical Exceptions

Some generated artifacts are intentionally retained only when they serve as history rather than mutable current-state runtime output:

- **Phase-end logs**: timestamped files under `docs/context/phase_end_logs/` when intentionally retained for audit history
- **Dated weekly summaries**: files such as `docs/context/ceo_weekly_summary_YYYYMMDD.md`
- **Completed milestone records**: dated artifacts that capture a finished event instead of mutable latest state
- **Explicit archive or fixture material**: only when a doc row or fixture path says so directly

These exceptions do not change the rule that mutable current-state runtime artifacts belong under the active-control-plane table above.

## Verification

Use these checks while reviewing the artifact boundary:

```powershell
rg -n "loop_cycle_summary_current|exec_memory_packet_latest_current|exec_memory_packet_build_status_current|workflow_status_latest|TAKEOVER_LATEST|skill_activation_latest|quant_current_scope" docs/ARTIFACT_POLICY.md
git status --short
```

When P0.3b begins, expand verification to include `git check-ignore` against every family whose Git policy is `Ignore`.

## Maintenance

When adding or changing runtime artifacts:

1. Update this table first.
2. State the authority status, retention class, and Git policy explicitly.
3. Only then update writers and `.gitignore`.
4. Add or update regression tests so the approved boundary is enforced mechanically.
