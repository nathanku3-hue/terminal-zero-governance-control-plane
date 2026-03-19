---
name: saw
description: Subagents-After-Work execution and review protocol for non-trivial changes. Use when a work round finishes and Codex must run implementer/reviewer passes, reconcile findings, and publish a PASS/BLOCK report with document-change visibility, GitHub-optimized doc sorting, and project-init hierarchy confirmation.
---

# SAW Skill

Execute this workflow after each work round.
When the round closes a phase, execute Section 6 in the same round before publishing final status.

## 0. Project Init Hierarchy Confirmation (Hard Stop)
1. Call `$hierarchy-init` to load templates, render the locked table, and gate on approval.
2. Before each SAW round, re-check that a hierarchy confirmation exists in the current thread.
3. Ensure the hierarchy audit stamp is included at the top of the SAW report.

**Reference**: For system wiring and validation chain details, see `AGENTS.md` Section 3 and `docs/workflow_wiring_detailed.md`.

## 1. Scope and Ownership
1. Declare the work round scope in one line.
2. List owned files changed in this round.
3. List acceptance checks for this round.
4. Echo confirmed hierarchy and audit stamp at the top of the SAW report.
5. Assign and print:
   - `RoundID` (for this SAW cycle),
   - `ScopeID` (for this round scope).
6. Convert acceptance checks into stable IDs (`CHK-01`, `CHK-02`, ...).

## 2. Subagent Passes
1. Implementer pass: validate requirements were implemented.
2. Reviewer A pass: strategy correctness and regression risks.
3. Reviewer B pass: runtime and operational resilience.
4. Reviewer C pass: data integrity and performance path.
5. Record ownership check: implementer and reviewers must be different agents.
6. Timeout/retry/escalation:
   - if a reviewer pass times out, retry once,
   - if retry also times out, mark reviewer status `Unavailable`, escalate in `Open Risks`, and set `SAW Verdict: BLOCK` unless user accepts proceeding risk.

## 3. Reconciliation Rules
1. Mark each finding with `Severity`, `Impact`, `Fix`, `Owner`, `TargetDate`, `Status`.
2. Missing `Owner` or `Severity` on Critical/High findings → `SAW Verdict: BLOCK`.
3. In-scope Critical findings: auto `SAW Verdict: BLOCK`, no user override. The finding must be resolved before the round can close.
4. In-scope High findings: do not close SAW while unresolved unless user explicitly accepts risk.
5. Inherited out-of-scope Critical/High findings: carry in `Open Risks` with `Owner` + `TargetDate` + target milestone. User acceptance is allowed before milestone close.
6. **Worker to PM/Planner Return Loop Check (Mandatory):**
   - After bounded execution, verify that execution truth was converted into planner truth:
     - `impact_packet_current.md` refreshed in the target working repo when active (changed files, owned files, touched interfaces, failing checks)
     - `bridge_contract_current.md` refreshed in the target working repo when active (SYSTEM_DELTA, PM_DELTA, OPEN_DECISION, RECOMMENDED_NEXT_STEP, DO_NOT_REDECIDE)
     - `post_phase_alignment_current.md` refreshed in the target working repo when multi-stream or system-shaping work completes
   - If any required artifact is missing or stale, emit `ReturnLoopCheck: BLOCK` and add to `Open Risks`.
   - If all required artifacts are refreshed, emit `ReturnLoopCheck: PASS`.
7. **Organic Integration Check (Mandatory when new surface added):**
   - If this round added a new view/report/tab/surface, verify:
     - New surface is explicitly classified as: core surface, temporary diagnostic surface, or replacement surface
     - If temporary, system names what should absorb or replace it later
     - If replacement, system names what older surface should be deprecated
     - Round states whether overall system shape became: more integrated, unchanged, or more fragmented
     - Round names one explicit next simplification step
   - If new surface was added but organic integration check is missing, emit `OrganicIntegrationCheck: BLOCK` and add to `Open Risks`.
   - If no new surface was added, emit `OrganicIntegrationCheck: N/A`.
   - If new surface was added and organic integration check exists, emit `OrganicIntegrationCheck: PASS`.
8. Publish `SAW Verdict: PASS` or `SAW Verdict: BLOCK`.
9. SAW report publication is terminal for the round and must not trigger nested SAW recursion.
10. Emit closure counts:
   - `ChecksTotal`, `ChecksPassed`, `ChecksFailed` from the `CHK-*` set.
   - `ChecksFailed` includes explicit fails and missing/not-run checks.
11. Emit one machine-check line:
   - `ClosurePacket: RoundID=<...>; ScopeID=<...>; ChecksTotal=<int>; ChecksPassed=<int>; ChecksFailed=<int>; Verdict=<PASS|BLOCK>; OpenRisks=<...>; NextAction=<...>`.
12. Validate closure packet with:
   - `python .codex/skills/_shared/scripts/validate_closure_packet.py --packet "<ClosurePacket line>" --require-open-risks-when-block --require-next-action-when-block`.
   - Record `ClosureValidation: PASS` or `ClosureValidation: BLOCK` in report.
13. Validate SAW report blocks with:
   - `python .codex/skills/_shared/scripts/validate_saw_report_blocks.py --report-file "<saw_report_path>"`.
   - Record `SAWBlockValidation: PASS` or `SAWBlockValidation: BLOCK` in report.
14. Hard close gate:
   - missing `RoundID`, `ScopeID`, or any `Checks*` field => `SAW Verdict: BLOCK`.
   - failed closure validation => `SAW Verdict: BLOCK`.
   - failed SAW block validation => `SAW Verdict: BLOCK`.
   - `ReturnLoopCheck: BLOCK` => `SAW Verdict: BLOCK`.
   - `OrganicIntegrationCheck: BLOCK` => `SAW Verdict: BLOCK`.
   - `SAW Verdict: PASS` only when `ChecksFailed=0` and no unresolved in-scope Critical/High findings and `ReturnLoopCheck: PASS` and `OrganicIntegrationCheck: PASS or N/A`.
15. No-change edge case:
   - if no files changed, still run reviewer passes, set `ChecksTotal>=1` (scope validation), and include one-line `NoChangeReason`.
16. Phase-end hard gate:
   - if this round closes a phase, require all Section 6 checks and artifacts.
   - missing phase-end checks/artifacts => `SAW Verdict: BLOCK`.

## 4. Required Report Blocks
1. Findings table.
2. Scope split summary:
   - in-scope findings/actions,
   - inherited out-of-scope findings/actions.
3. Document Changes Showing:
   - path
   - what changed
   - reviewer status
4. Document Sorting (GitHub-optimized):
   - follow canonical ordering from `docs/checklist_milestone_review.md`.
5. Closure packet:
   - `RoundID`, `ScopeID`, `ChecksTotal`, `ChecksPassed`, `ChecksFailed`, `SAW Verdict`.
6. Closure validation line:
   - `ClosureValidation: PASS/BLOCK`.
7. SAW block validation line:
   - `SAWBlockValidation: PASS/BLOCK`.
8. Phase-end block (required only when phase closes):
   - `PhaseEndValidation: PASS/BLOCK`
   - `PhaseEndChecks: CHK-PH-01..CHK-PH-0N`
9. Handover block (required only when phase closes):
   - `HandoverDoc: <path>`
   - `HandoverAudience: PM`
10. New-context block (required only when phase closes):
   - `ContextPacketReady: PASS/BLOCK`
   - `ConfirmationRequired: YES`

## 5. Top-Down Snapshot Guardrail
1. Use project-based hierarchy (`L1` project pillar, `L2` streams, `L3` stages).
2. Main table shows only active-level stages for the selected active stream.
3. Use `Stage | Current Scope | Rating | Next Scope` columns.
4. Planning row must explicitly include `Boundary`, `Owner/Handoff`, and `Acceptance Checks`.
5. Keep rows single-line; avoid wrapped cells.
6. Render the snapshot block inside a fenced `text` code block to preserve alignment.
7. Fix column widths to `Stage=14`, `Current Scope=16`, `Rating=7`, `Next Scope=38` (total width 80); pad or truncate content (use `...`) to keep the closing `|` aligned and prevent wrapping.
8. Secondary next suggestion must be outside the table as `Remark:` and only shown when `next_step_certainty < 75` and `rating_diff_between_top_next_steps < 20`.
9. Use delta-only snapshots on back-and-forth planning:
   - After the first full snapshot in-thread, emit `Snapshot Delta` with only changed header fields and changed rows.
   - Do not repeat the full snapshot/table unless the user asks or the hierarchy/active stream/stage level changes.
10. Use this terminal-safe fixed-width ASCII template:

```text
Top-Down Snapshot
L1: <project pillar>
L2 Active Streams: <stream1, stream2, ...>
L2 Deferred Streams: <stream3, ... | none>
L3 Stage Flow: Planning -> Executing -> Iterate Loop -> Final Verification -> CI/CD
Active Stream: <one stream>
Active Stage Level: <L2|L3|L4>

+--------------+----------------+-------+--------------------------------------+
| Stage        | Current Scope  | Rating| Next Scope                           |
+--------------+----------------+-------+--------------------------------------+
| Planning     | B=.. OH=.. AC=.| 45/100| 1) <primary> [45/100]: <reason>...   |
+--------------+----------------+-------+--------------------------------------+
Remark: 2) <secondary item> [00/100]: <one-line reason> (optional; show only if next_step_certainty < 75 and rating_diff_between_top_next_steps < 20)

Snapshot Delta
- Active Stream: <old> -> <new> (only if changed)
- Row: Planning | Rating 45/100 -> 55/100 | Next Scope: 1) <primary> [55/100]: <reason>
```

## 6. Phase-End Closeout Protocol (Mandatory When Phase Closes)
1. Trigger:
   - run this protocol when user intent or active brief marks the phase as complete/closure-ready.
2. Subagent test matrix (all required):
   - `CHK-PH-01` Full regression: run repository test suite in `.venv` (`python -m pytest -q`).
   - `CHK-PH-02` Runtime smoke: run one end-to-end app boot smoke path (`launch.py` or headless `streamlit run app.py`) with `timeout_sec=180`; timeout or non-zero exit => fail.
   - `CHK-PH-03` End-to-end path replay: implementer executes 1-3 key phase runs from acceptance checks; Reviewer B independently reproduces the same runs with matching exit code and matching evidence artifacts (same output file presence + same row-count sanity values or explicitly documented acceptable delta).
   - `CHK-PH-04` Data integrity and atomic-write verification: Reviewer C confirms temp->replace path, key row-count sanity checks, and artifact freshness for this phase.
   - `CHK-PH-05` Docs-as-code gate: update active phase brief (`docs/phase_brief/phase<NN>-brief.md` or canonical equivalent) with live loop state + acceptance criteria, plus `docs/notes.md` formula registry, `docs/decision log.md`, and `docs/lessonss.md`.
   - `CHK-PH-06` Context artifact refresh gate: run `.venv\Scripts\python scripts/build_context_packet.py`, require fresh artifacts `docs/context/current_context.json` and `docs/context/current_context.md`, then run `.venv\Scripts\python scripts/build_context_packet.py --validate`; non-zero exit or missing artifacts => fail.
3. PM handover artifact (single source of truth):
   - write `docs/handover/phase<NN>_handoover.md`.
   - use `references/phase_end_handover_template.md`.
   - required blocks:
     - `Executive Summary (PM-friendly)`
     - `Delivered Scope vs Deferred Scope`
     - `Derivation and Formula Register` (explicit formulas + variable definitions + source paths)
     - `Logic Chain` (`Input -> Transform -> Decision -> Output`)
     - `Evidence Matrix` (command, result, artifact)
     - `Open Risks / Assumptions / Rollback`
     - `Next Phase Roadmap` (3-7 items with acceptance checks)
4. New-context bootstrap packet (for `/new`):
   - produce a compact `NewContextPacket` in the report and in the handover file footer:
     - `What was done`
     - `What is locked`
     - `What remains`
     - `Next-phase roadmap`
     - `Immediate first step`
   - end with:
     - `ConfirmationRequired: YES`
     - `Prompt: Reply "approve next phase" to start execution.`
     - `NextPhaseApproval: PENDING`
5. Stop condition:
   - do not start next-phase implementation in the same thread/round until explicit user confirmation token is present.
   - approval token contract:
     - approved: exact reply includes `approve next phase`.
     - rejected/edit: any other explicit response keeps `NextPhaseApproval` as `REJECTED` or `PENDING`.
