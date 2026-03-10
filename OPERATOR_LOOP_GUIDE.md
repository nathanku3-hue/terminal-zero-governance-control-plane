# Operator Loop Guide

`README.md` is the minimal public quickstart; this guide is the fuller operator run sequence for local execution.

Run these commands from the repository root. The sequence below assumes PowerShell and a repo-local `.venv`.

## Recommended command sequence

```powershell
.venv\Scripts\python scripts/capture_profile_outcome_record.py --repo-root . --project-profile "<project_profile>" --shipped "<true|false>" --rollback-status "<NO|PARTIAL|FULL>" --followup-changes-within-30d "<0+>" --semantic-issue-detected-after-merge "<NONE|PRESENT|I don't know yet>" --postmortem-note "<short_postmortem_note>"
.venv\Scripts\python scripts/build_profile_selection_ranking.py --repo-root .
.venv\Scripts\python scripts/startup_codex_helper.py --repo-root .
.venv\Scripts\python scripts/run_loop_cycle.py --repo-root . --skip-phase-end --allow-hold true
.venv\Scripts\python scripts/validate_loop_closure.py --repo-root .
.venv\Scripts\python scripts/print_takeover_entrypoint.py --repo-root .
# Optional: Generate workflow status overlays
.venv\Scripts\python scripts/print_takeover_entrypoint.py --repo-root . --workflow-status-json-out docs/context/workflow_status_latest.json --workflow-status-md-out docs/context/workflow_status_latest.md
.venv\Scripts\python scripts/build_ceo_bridge_digest.py --sources "docs/context/worker_status_aggregate.json,docs/pm_to_code_traceability.yaml,docs/context/escalation_events.json,docs/context/worker_reply_packet.json,docs/context/auditor_findings.json,docs/context/exec_memory_packet_latest.json" --output docs/context/ceo_bridge_digest.md
```

## What this produces

- One normalized profile-outcome record in `docs/context/profile_outcomes_corpus/` combining current loop artifacts plus operator shipped/postmortem inputs and lean R3 fields (`rollback_status`, `followup_changes_within_30d`, `semantic_issue_detected_after_merge`).
- Refreshed advisory profile ranking in `docs/context/profile_selection_ranking_latest.json` and `docs/context/profile_selection_ranking_latest.md`.
- Startup intake and execution card for current round.
- One full loop pass (without phase-end handover) plus refreshed context artifacts.
- Closure verdict (`READY_TO_ESCALATE` or `NOT_READY`) in `docs/context/loop_closure_status_latest.json`.
- Deterministic takeover/advisory output from `scripts/print_takeover_entrypoint.py`.
- Optional workflow status overlays (JSON and/or Markdown) when flags are provided.
- Fresh CEO digest at `docs/context/ceo_bridge_digest.md`.

## Optional milestone-close optimality note

- Reuse `docs/templates/optimality_review_brief.md` and keep the working copy at `docs/context/milestone_optimality_review_latest.md`.
- Mirror family convention: repo-root mirrors are convenience-only, stay intentionally thin, point back to an authoritative `docs/context` source, and make no gate or authority change.
- Active quick-scan mirrors: `MILESTONE_OPTIMALITY_REVIEW_LATEST.md`, `THESIS_PULL_LATEST.md`.
- Keep a thin PM summary at `MILESTONE_OPTIMALITY_REVIEW_LATEST.md` for one-screen operator reading.
- Mirror format stays concise: milestone snapshot (`MILESTONE_ID`, `SHAPE_DELTA`, `KEEP_THIS_SHAPE_TODAY`, `ENTROPY_VERDICT`), recommended path, top regrets, next simplification, and evidence paths.
- `docs/context/milestone_optimality_review_latest.md` remains the authoritative source when any wording differs.
- The same brief may include an optional `ELEGANCE_ENTROPY_SNAPSHOT` with lean proxy fields such as `CONCEPT_SURFACE_DELTA`, `INTERFACE_SURFACE_DELTA`, `BOUNDARY_CROSSINGS_DELTA`, and `FUTURE_EDIT_SURFACE`.
- For live one-screen thesis-pull scan flow, use `THESIS_PULL_LATEST.md`; it is a convenience-only repo-root mirror and `docs/context/thesis_pull_latest.md` remains authoritative.
- Say `I don't know yet` when the integration is too fresh, concurrent changes still blur the boundary shape, or the future edit surface is not honestly visible yet.
- This remains advisory only and makes no gate or authority change.
