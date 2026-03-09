# Profile Selection Ranking (Advisory)

## Decision
- Source artifact: `docs/context/profile_selection_ranking_latest.json`.
- Generation mode: offline, deterministic, local evidence only (shipped-project outcomes).
- Usage mode: advisory recommendation only.

## Authority Boundary
- Startup intake and active `PROJECT_PROFILE` remain authoritative.
- Ranking output does not create a new gate, override, or approval path.
- Missing/invalid ranking artifact must not block startup execution.

## Minimal Expected Fields
- `recommended_profile`
- `score`
- `confidence`
- `evidence_summary`
- `generated_at_utc`
- `ranking`

## Corpus Input Shape
- Directory default: `docs/context/profile_outcomes_corpus/`
- Capture command (operator step before ranking build):
  - `.venv\Scripts\python scripts/capture_profile_outcome_record.py --repo-root . --project-profile "<project_profile>" --shipped "<true|false>" --rollback-status "<NO|PARTIAL|FULL>" --followup-changes-within-30d "<0+>" --semantic-issue-detected-after-merge "<NONE|PRESENT|I don't know yet>" --postmortem-note "<short_postmortem_note>"`
- Capture script writes one normalized JSON record per run under `docs/context/profile_outcomes_corpus/`.
- Record should minimally include: `project_profile`, `shipped`, `rollback_status`, `followup_changes_within_30d`, `semantic_issue_detected_after_merge`, `postmortem_note`, `captured_at_utc`.
- Record should bind current loop artifacts when available (for example `startup_intake_latest.json`, `loop_closure_status_latest.json`, `round_contract_latest.md`, `ceo_go_signal.md`).
- Optional evidence fields consumed by the scorer: `ready`, `board_reentry_required`, `unknown_domain_triggered`.
- Current scorer remains intentionally simple; the new shipped-outcome fields are captured now for broader optimality learning before any extra scoring is introduced.

## Operator Note
- Run corpus capture first, then build ranking:
  1. `.venv\Scripts\python scripts/capture_profile_outcome_record.py --repo-root . --project-profile "<project_profile>" --shipped "<true|false>" --rollback-status "<NO|PARTIAL|FULL>" --followup-changes-within-30d "<0+>" --semantic-issue-detected-after-merge "<NONE|PRESENT|I don't know yet>" --postmortem-note "<short_postmortem_note>"`
  2. `.venv\Scripts\python scripts/build_profile_selection_ranking.py --repo-root .`
- Treat this as decision-support evidence for profile choice discussions, not as an automatic profile switch.
