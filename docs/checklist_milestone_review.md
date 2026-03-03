# Milestone Review Checklist

**Agent Instruction**: Act as a Senior Code Reviewer. Check the following before marking Phase [N] complete.

## 1. Code Quality
- [ ] **Vectorization**: Are there `for` loops iterating over DataFrames? (Reject if yes).
- [ ] **Safety**: Are file writes atomic? (Reject if direct write to `.parquet`).
- [ ] **Error Handling**: Does the code handle `NaN`, Empty DataFrames, or API failures gracefully?

## 2. Testing
- [ ] **Unit Tests**: Do `tests/` cover the new logic?
- [ ] **Integration**: Does `launch.py` still boot the app successfully?
- [ ] **Edge Cases**: What happens if the internet disconnects?

## 3. Documentation
- [ ] **Decision Log**: Is `decision log.md` updated with trade-offs?
- [ ] **Runbook**: Are there new ops commands (e.g., `python build_map.py`)?
- [ ] **Formula Log**: Are all new/changed formulas and derivations logged in `docs/notes.md` with source `.py` paths?
- [ ] **Phase Handover**: Is `docs/handover/phase<NN>_handover.md` published with PM summary + logic chain + formula register?
- [ ] **Lessons Loop**: Is `docs/lessonss.md` updated with date, mistake, root cause, fix, and guardrail?

## 4. Phase-End Closure (Mandatory at phase completion)
- [ ] **Subagent E2E Replay**: Did implementer and Reviewer B independently run an end-to-end phase path?
- [ ] **Full Regression**: Did `.venv\Scripts\python -m pytest -q` pass for the phase-close candidate?
- [ ] **Runtime Smoke**: Did one app boot smoke path pass (`launch.py` or headless `streamlit run app.py`)?
- [ ] **Data Integrity**: Are atomic write paths and artifact freshness/row-count sanity checks recorded with evidence artifact paths and observed values?
- [ ] **New Context Packet**: Is `/new` bootstrap summary prepared with `what was done`, `what is next`, `ConfirmationRequired: YES`, and `NextPhaseApproval: PENDING`?
- [ ] **Context Artifact Refresh**: Did `.venv\Scripts\python scripts/build_context_packet.py` refresh `docs/context/current_context.json` and `docs/context/current_context.md`, and did `.venv\Scripts\python scripts/build_context_packet.py --validate` pass?
- [ ] **Gemini Handover Refresh**: Did `scripts/build_context_packet.py` also refresh `docs/handover/gemini/phase<NN>_gemini_handover.md` with `top_level_PM.md` + context sources?
- [ ] **Philosophy Local-First Loop**: Did `.venv\Scripts\python scripts/sync_philosophy_feedback.py --scan-root E:\Code --main-repo <this_repo>` pass, and was main migration blocked on any local worker failure?

## 5. Document Sorting (GitHub-optimized)
- [ ] Present changed docs in this order:
  1. `AGENTS.md`
  2. `docs/prd.md`, `docs/spec.md`
  3. `docs/phase*-brief.md` (numeric phase order)
  4. `docs/handover/*.md` (phase order)
  5. `docs/runbook_ops.md`, `docs/checklist_milestone_review.md`
  6. `docs/notes.md`, `docs/lessonss.md`, `docs/decision log.md`
  7. `docs/research/*.md` (date/name ascending)

## 6. Closed Loop Verification
- [ ] **One-Click Phase-End Gate**: Did `scripts/phase_end_handover.ps1` exit `0` (or produce explicit `failed_gate` + log path on `BLOCK`)?
- [ ] **Worker Status Aggregation**: Did `aggregate_worker_status.py` run cleanly (`exit 0`), and is the overall health `OK` (no escalations/stale workers)?
- [ ] **Traceability Gate**: Did `validate_traceability.py --strict --require-test` pass (`exit 0`), ensuring no UNMAPPED directives and all diffs have validators?
- [ ] **Evidence Intactness**: Did `validate_evidence_hashes.py` pass (`exit 0`), verifying SHA-256 evidence matches and no self-signoffs occurred?
- [ ] **Gemini Bridge Freshness**: Is `ceo_bridge_digest.md` < 60 min old (`validate_digest_freshness.py` passed with `exit 0`)?
- [ ] **Orphan Change Gate**: Did `validate_orphan_changes.py` pass (`exit 0`), proving all production code changes map to PM directives?
- [ ] **Dispatch Lifecycle**: Did `validate_dispatch_acks.py` pass (`exit 0`), affirming all dispatched tasks reached COMPLETED state with bound artifacts/tests?
- [ ] **Worker Reply Gate**: Did `validate_worker_reply_packet.py` pass (`exit 0`), with mandatory confidence and citations for each task item, and (for v2 packets) `machine_optimized` and `pm_first_principles` blocks?
- [ ] **Triad Coverage (when `-EnforceScoreThresholds` enabled)**: Does each v2 item include all 3 triad domains (principal, riskops, qa) in `expertise_coverage`, with at least one marked APPLIED or NOT_REQUIRED?
- [ ] **Score Threshold Gate (when `-EnforceScoreThresholds` enabled)**: Does each v2 item have `confidence_level.score >= 0.70` and `problem_solving_alignment_score >= 0.75`?
- [ ] **Cross-Repo Readiness (when `-EnforceScoreThresholds` enabled)**: Did G05b pass with `-CrossRepoRoots` covering all active repos?
- [ ] **CEO Digest Generated**: Is `ceo_bridge_digest.md` updated, readable, and containing the latest First Principles Engineering Summary, Strategic Expertise Coverage, Expert Verdict Matrix, Per-Round Score Gates, and Worker Confidence/Citations?
- [ ] **Schema Version Declared**: Does `worker_reply_packet.json` declare `schema_version: 2.0.0` for Phase 24+ work?
- [ ] **Auditor Review (G11)**: Did `run_auditor_review.py` run in the configured `-AuditMode` (shadow/enforce/none)? If shadow: verify findings logged, no policy blocks. If enforce: verify Critical/High = 0 or justified. Infra errors (exit 2) always block regardless of mode.
- [ ] **Auditor Findings in Digest**: Does CEO digest Section IX contain fresh auditor findings from the current run (not stale from a previous run)? If `-AuditMode none`: Section IX should show "Auditor review not available."
- [ ] **Auditor FP Ledger**: Are all C/H findings annotated in `auditor_fp_ledger.json`?
- [ ] **Calibration Report**: Does `auditor_calibration_report.py` produce current report with no infra errors?

## 7. Manual Capture Policy (Strict Enforcement)
- **Rule 1 (No Mockups):** E2E evidence only accepts `REAL_CAPTURE` and script `.log`. AI-generated mockups are strictly prohibited.
- **Rule 2 (Trigger):** Manual screenshot requests trigger *only* when all automated script gates PASS and missing real captures are detected for web UI / terminal roundtrip interactions.
- **Rule 3 (SLA Reminder):** Missing manual evidence triggers a reminder at 15 minutes. At >30 minutes, it escalates to `BLOCK`.
- **Rule 4 (Verdict Gate):** Any missing `REAL_CAPTURE` enforces a state of `Machine PASS + Manual Pending`. The milestone cannot exit to `PASS` until the files are supplied by a human.
- **Rule 5 (Drop Zone Loop):** Evidence intake must run through `scripts/manual_capture_watcher.py` using Desktop `Evidence_Drop` (or explicitly approved equivalent path), so queue/index/alerts stay synchronized.
- **Rule 6 (File Naming):** Accepted files must match `T<id>_manual<id>_<context>_<YYYYMMDD>.<ext>` and pass header/size validation before status can switch to `PASS`.

**Verdict**: [PASS / Manual Pending / BLOCK]
