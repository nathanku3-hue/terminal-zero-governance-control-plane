# AGENTS.md

> SYSTEM CONTEXT: You are a contributor to Terminal Zero (T0), a script-driven AI engineering governance control plane.
> ROOT PATH: `E:\Code\SOP\quant_current_scope`

## 1. Tech Stack (Hard Constraints)
- Runtime: Python 3.12+; prefer the repo-local `.venv`, but a compatible system Python is acceptable when `.venv` is unavailable. Record the interpreter used in validation evidence.
- Core: script-first orchestration, JSON/Markdown artifact contracts, and subprocess-driven validators.
- Primary operator entrypoints: `scripts/startup_codex_helper.py`, `scripts/run_loop_cycle.py`, `scripts/supervise_loop.py`, `scripts/print_takeover_entrypoint.py`.
- Testing: `pytest` for script, contract, and orchestration coverage.
- Current-head note: historical handoffs may cite `303 passed` (Stream 2 merge-gate snapshot) or `308 passed` (post-blocker / pre-hardening baseline). For current `HEAD`, always quote a freshly rerun repo-wide `pytest` count and record the run date plus interpreter used, rather than reusing a prior total.
- Forbidden without explicit approval: SQLite, Flask, Django, or complex ORMs.

## 2. Directory Map
Keep strict separation of concerns:
- `scripts/`: orchestration, validation, supervision, reporting, and handoff entrypoints for the control plane.
- `scripts/startup_codex_helper.py`, `scripts/run_loop_cycle.py`: initialize a round and execute the main worker/auditor/CEO loop.
- `scripts/validate_loop_closure.py`, `scripts/supervise_loop.py`, `scripts/print_takeover_entrypoint.py`: close the loop, monitor loop health, and print takeover guidance.
- `docs/context/`: authoritative `_latest` artifacts exchanged between startup, execution, closure, supervision, and takeover steps.
- `docs/`: operating contracts, phase briefs, runbooks, decision records, and repo procedures.
- `tests/`: test suites covering script behavior and control-plane contracts.
- `data/`, `strategies/`, `views/`: legacy quant-era surfaces; do not treat them as primary operator entrypoints unless a current brief explicitly scopes them in.
- `docs/lessonss.md`: self-learning loop log for mistakes and guardrails.
- `docs/research/`: domain research PDFs and synthesized findings.
- `.codex/skills/`: canonical repo-local Codex skills (including `saw` and `research-analysis`).
- `skills/`: reserved for project deliverables; not the canonical agent-skill source.
- `OPERATOR_LOOP_GUIDE.md`: canonical operator walkthrough for the current startup -> loop -> closure -> takeover flow.

## 3. Operating Principles (Core Commandments)
1. Docs-as-Code: if behavior changes, update docs (prd and product spec) and decision log in the same milestone. for explicit formulas used, document the explicit formula and where .py used ,in notes.md, 
2. Atomic Safety: critical data writes must be atomic (temp -> replace).
3. Top-Down Delivery: spec -> interface -> implementation -> test.
4. Defense in Depth: assume API failures and NaN-heavy data; fail gracefully.
5. Subagent-First: default to subagents for non-trivial work (multi-file changes, ETL, strategy logic, runtime/ops risk paths).
6. Guardrailed Delegation: each subagent must have bounded scope (owned files/tasks), explicit acceptance checks, and no destructive operations without user confirmation.
7. Review Gated: no milestone is done without subagent review (Section 5).
8. Self-Learning: after each work/review round, record mistakes, root causes, and guardrails in `docs/lessonss.md`.

## 4. Delivery Workflow
1. Brief: create or update `docs/<phase>-brief.md` with acceptance criteria and live loop state.
2. Plan: propose concrete file-level implementation steps using the mandatory contract in Section 11.
3. Orchestrate: assign subagents with clear ownership (`Implementer`, `Reviewer A/B/C`) and acceptance checks.
4. Execute: run the current control-plane flow (`startup_codex_helper.py` -> `run_loop_cycle.py` -> closure/supervision/takeover) with bounded worker ownership.
5. Verify: run `pytest` and runtime smoke checks (for example `python scripts/startup_codex_helper.py --help`, `python scripts/run_loop_cycle.py --help`, and `python scripts/supervise_loop.py --max-cycles 1`).
6. Review: execute the Section 5 milestone gate.
7. Report: include observability rating, evidence footer (Section 9), and top-down snapshot (Section 11).
8. SAW round: run Subagents-After-Work protocol from Section 12.

## 5. Milestone Review Gate (Mandatory)
Before closing a milestone, spawn reviewer subagents using this prompt:
- Use the Section 12 reviewer mapping/schema and Section 14 interaction contract; do not duplicate prompt variants.

Risk tier checks:
- Low: touched-module unit tests and static checks.
- Medium: Low + integration/smoke checks.
- High: Medium + data integrity checks (atomic write path, row-count/sanity assertions) and rollback note.
- Critical: High + dry-run evidence and explicit user sign-off before any production-impacting operation.

## 6. Engineering Standards
- Vectorization first: avoid loops over DataFrame rows/columns when a vectorized path exists.
- PIT discipline: never leak future data; fundamentals align by `release_date`.
- Restartability: long ETL/update jobs should be resumable/checkpointed.
- Explainability: scoring outputs must expose human-readable reasoning in UI.
- Environment hygiene: `pyproject.toml` is the canonical dependency declaration and must stay in sync with imports; use `constraints.txt` / `constraints-dev.txt` for pinned, validated installs, and keep `requirements*.txt` as compatibility shims only (do not treat them as canonical).

## 7. Change Discipline
- No destructive operations without explicit user confirmation.
- Never revert unrelated local changes.
- Read files before overwriting; preserve surrounding architecture style.
- Keep new dependencies minimal and justified.

## 8. Definition of Done
- Code implemented with acceptance criteria met.
- Tests and smoke checks pass.
- A task remains `Incomplete` if proof it works is missing, even when code changes are finished.
- Docs updated (`docs/...` and `decision log.md`).
- Milestone review gate passes.
- Operational impact and rollback path are documented.

## 9. Observability and Reporting (Mandatory)
- Every normal report/conversation must include one rating:
- `Progress: X/100` for execution status updates.
- `Confidence: Y/10` for proposals/analysis.
- For strict-schema subagent review outputs, the rating may be emitted once in the parent orchestration summary for that round.
- If `Confidence < 7/10`, include `Unknowns:` and `Next verification step:`.
- Score thresholds: confidence < 0.70 blocks execution (HOLD); relatability < 0.75 blocks dispatch (REFRAME). Machine-enforced via `--enforce-score-thresholds` in G06; visually rendered in digest score gate section.
- Milestone report footer format is required:
- `Evidence:`
- `Assumptions:`
- `Open Risks:`
- `Rollback Note:`

## 10. Self-Learning Feedback Loop (Mandatory)
- Source of truth: `docs/lessonss.md`.
- At session start for the relevant project: review recent lessons before proposing a plan.
- After each execution/review round: append one lesson entry with:
  - Date
  - Mistake or miss
  - Root cause
  - Fix applied
  - Guardrail for next time
  - Evidence paths (`.py`, `.md`, test output)
- If the same mistake repeats, promote the guardrail into this file (`AGENTS.md`) in the same milestone.

## 11. Plan Response Contract (Mandatory for Every Plan Request)
Every plan response must contain these sections:
1. High Confidence Items
   - One line per item + one-line reason.
   - Reason must be one of: `industry standard`, `given repo constraints`, or `research evidence via skill`.
2. Not Clear / Low Certainty
   - One line per item + one-line reason.
   - For each low-certainty item, propose more than one method, then state preferred method + one-line reason.
3. Out of Boundary / Need Extra Help
   - One line per item + one-line reason.
4. Top-Down Snapshot
   - Use a project-based hierarchy (not technical layers).
   - Initialize/confirm at project start:
     - `L1`: Project Pillar (example: `Backtest Engine (Signal System)`).
     - `L2`: Streams (`Backend`, `Frontend/UI`, `Data`, `Ops`).
     - `L3`: Stage flow (`Planning -> Executing -> Iterate Loop -> Final Verification -> CI/CD`).
   - For each plan output, include this hierarchy header block:
     - `L1: <project pillar>`
     - `L2 Active Streams: <list>`
     - `L2 Deferred Streams: <list or none>`
     - `L3 Stage Flow: Planning -> Executing -> Iterate Loop -> Final Verification -> CI/CD`
     - `Active Stream: <one stream>`
     - `Active Stage Level: <L2|L3|L4>`
   - Main table must show only stage rows under the active stage level and selected active stream.
   - Stage set must be MECE under the same parent scope.
   - Use terminal-safe fixed-width ASCII format (not Markdown tables).
   - Use compact columns only: `Stage`, `Current Scope`, `Rating`, `Next Scope`.
   - Stage rows must be specific to the selected active stream.
   - Planning stage must confirm stream boundary, owner/handoff, and acceptance checks before execution starts.
   - Planning row must explicitly include `Boundary`, `Owner/Handoff`, and `Acceptance Checks` (concise tokens are acceptable).
   - Keep each row single-line (no wrapped cells). If needed, shorten/truncate text to fit.
   - Primary next step goes inside `Next Scope` and should include rating plus one-line reason.
   - Guardrail: if all rows share the same scope, show `L1: <scope>` as the top-left header line and do not repeat `L1` as a table row or column.
   - Secondary next suggestion must be outside the table as `Remark:` and is optional.
   - Show the secondary suggestion only when both are true:
     - `next_step_certainty < 75`
     - `rating_diff_between_top_next_steps < 20`
   - Scoring rubric:
     - `Rating`: `0-100` progress/readiness for the current stage row.
     - `next_step_certainty`: `0-100` confidence for the next-step recommendation.
     - `rating_diff_between_top_next_steps`: absolute delta between primary and secondary next-step ratings.
   - One-stage expansion rule:
     - Keep the main table at the active stage level.
     - Expand only one stage row (the top next step) into the next depth (`L4`) when needed.
     - Expansion triggers:
       - two or more plausible sub-steps are blocking start, or
       - `next_step_certainty < 75`, or
       - high-payoff but ambiguous path, or
       - handoff risk.
     - Expanded mini-table must have 3-5 MECE children with concrete artifact and done condition.
     - After action, collapse back to the active level when certainty is `>= 75`; if still `< 75`, keep the expanded set capped at 5 and replace (do not append).
   - Canonical policy is documented in `docs/spec.md`; live loop state is tracked in active `docs/phase*-brief.md`.
   - Canonical sample format lives in `docs/templates/plan_snapshot.txt`.

## 12. SAW: Subagents After Work (Mandatory)
SAW must run after each work round (even docs-only rounds):
- SAW reconciliation/report publication is terminal for the round and does not recursively trigger another SAW round.
1. Implementer pass
   - Owned files, acceptance checks, and non-destructive constraints.
2. Reviewer A/B/C pass (independent from implementer ownership)
   - Reviewer A: strategy correctness and regression risks.
   - Reviewer B: runtime and operational resilience.
   - Reviewer C: data integrity and performance path.
   - Record ownership check: implementer and reviewers must be different agents; include this check in the SAW report.
3. Reconciliation pass
   - Fix all Critical/High findings in current-round scope.
   - In-scope Critical findings: auto-BLOCK, no user override. Must be resolved before round close.
   - In-scope High findings: do not close while unresolved unless user explicitly accepts risk.
   - For inherited out-of-scope Critical/High findings, carry them in `Open Risks` with owner, TargetDate, and target milestone. User acceptance is allowed before milestone close.
4. SAW report format
   - `SAW Verdict: PASS/BLOCK`
   - Findings table (Severity, Impact, Fix, Owner, Status)
   - Hierarchy Confirmation stamp (`Approved | Session | Trigger | Domains`)
   - Document Changes Showing: path + change summary + reviewer status
   - Document sorting order is maintained in `docs/checklist_milestone_review.md`.

## 13. Skill Hooks (Mandatory)
- Call `$saw` (`.codex/skills/saw/SKILL.md`) for SAW rounds and reporting structure.
- Call `$research-analysis` (`.codex/skills/research-analysis/SKILL.md`) when plan confidence should be backed by external research evidence.
- Optional trigger-based skills (not mandatory on day 1):
  - `$se-executor` (`.codex/skills/se-executor/SKILL.md`) for software-engineering execution rigor on multi-file/high-risk changes.
  - `$architect-review` (`.codex/skills/architect-review/SKILL.md`) for architecture/coupling/scaling/security tradeoff reviews.
- Trigger policy for optional skills:
  - Invoke by trigger (`high complexity`, `architecture-impacting change`, `handoff risk`, or `elevated operational risk`), not by default.
  - If the same trigger recurs for `>= 2` rounds in the same milestone/session, propose upgrading that skill to mandatory for the milestone and request explicit user approval before enforcing.
- Project-init hierarchy confirmation policy (driven by shared skill templates):
  - confirm once per project session (hard stop before execution)
  - retrigger only when a new domain appears or user explicitly says `change hierarchy` / `new scope`
  - if in-thread confirmation stamp is missing during non-interactive reviewer passes, use persisted fallback from `docs/spec.md` + active `docs/phase*-brief.md`, mark `FallbackSource`, and request explicit reconfirmation at the next interactive planning step
- Research workflow requirements:
  - Pull/read relevant PDFs from `docs/research/`.
  - Analyze core methodology and key findings.
  - Cross-reference against existing `researches*.md` files for novel deltas.
  - End with one-line logic chain and one-line explicit formula summary.
- Skill closure tokens (when invoked):
  - `$saw`: must output `SAW Verdict: PASS/BLOCK`; if `BLOCK`, include `Open Risks` and `Next action`.
  - `$se-executor`: must output `Verdict: PASS/BLOCK`; if `BLOCK`, include failed checks, `Open Risks`, and `Next action`.
  - `$research-analysis`: must output `Verdict: PASS/BLOCK`; if `BLOCK`, include `Open Risks` and `Next verification step`.
  - `$architect-review`: must output `Verdict: PASS/BLOCK`; if required architecture inputs are missing, output `BLOCK` with required inputs in `Open Risks`.
- Invocation-close packet (required for every invoked skill):
  - `RoundID`, `ScopeID`, `ChecksTotal`, `ChecksPassed`, `ChecksFailed`, `Verdict`.
  - Emit as single machine-check line:
    - `ClosurePacket: RoundID=<...>; ScopeID=<...>; ChecksTotal=<int>; ChecksPassed=<int>; ChecksFailed=<int>; Verdict=<PASS|BLOCK>; OpenRisks=<...>; NextAction=<...>`
  - Validate using:
    - `python .codex/skills/_shared/scripts/validate_closure_packet.py --packet "<ClosurePacket line>" --require-open-risks-when-block --require-next-action-when-block`
  - Any missing packet field forces `Verdict: BLOCK` for closure.
- Evidence-link minimums by skill:
  - `$se-executor`: every task must have `TaskID` and linked `EvidenceID`; unlinked task => `BLOCK`.
  - `$research-analysis`: every high-confidence claim must include `ClaimID` + source locator (`SourceID`, page/section); missing locator => `BLOCK`.
  - `$architect-review`: every option must include normalized score components (`impact`, `risk`, `effort`, `maintainability`) and computed `OptionScore`; missing score components => `BLOCK`.
- Validator tokens (required when invoked):
  - `$saw`: emit `SAWBlockValidation: PASS/BLOCK` from `validate_saw_report_blocks.py`.
  - `$se-executor`: emit `EvidenceValidation: PASS/BLOCK` from `validate_se_evidence.py`.
  - `$research-analysis`: emit `ClaimValidation: PASS/BLOCK` from `validate_research_claims.py`.
  - `$architect-review`: emit `CalibrationValidation: PASS/DRIFT/INSUFFICIENT` from `validate_architect_calibration.py`.

## 13b. Auditor Protocol
- Independent automated review of `worker_reply_packet.json` at phase-end via `scripts/run_auditor_review.py`.
- Shadow mode (default): policy findings logged, non-blocking. Infra/finalize failures still block. Severity is canonical (same in both modes).
- Enforce mode: Critical/High block handover (G11). Infra errors (exit 2) always block.
- Auditor is orthogonal to SAW: SAW reviews implementation process, auditor reviews final output packet.
- `dod_result=FAIL` is MEDIUM (informative), not CRITICAL. FAIL is valid data per validator contract.
- Calibration data tracked by `scripts/auditor_calibration_report.py` (weekly). Promotion verified by same script (dossier mode).
- Promotion gate (shadow → enforce):
  (a) 24B operational close complete.
  (b) Minimum 30 audited items across ≥ 2 consecutive weekly windows.
  (c) Critical+High false-positive rate < 5% (formula: false_positives among C/H findings / total C/H findings).
  (d) Explicit signoff by PM or designated owner in decision log.
  (e) All packets must be `schema_version=2.0.0`. Enforce mode rejects v1 packets (AUD-R000 is HIGH + blocking in enforce).

## 14. Interactive Review Protocol (Plan/Code Review Requests)
When the user asks for review-mode analysis (architecture/code quality/tests/performance), follow this sequence:
1. Start mode gate (required)
   - Ask user to pick exactly one:
     - `BIG CHANGE`: work section-by-section (`Architecture -> Code Quality -> Tests -> Performance`) with at most 4 top issues per section.
     - `SMALL CHANGE`: one issue/question per section.
   - If mode is already provided by parent/orchestrator (for example SAW reviewer passes), inherit that mode and do not ask the user again.
2. Per-issue response contract (required)
   - Number each issue (`1, 2, 3...`) and label options with letters (`A, B, C...`).
   - Include concrete file references for findings (`path:line`).
   - Provide 2-3 options (include `do nothing` when reasonable).
   - For each option, include: implementation effort, risk, impact on other code, and maintenance burden.
   - Put recommended option first and explain why in one line mapped to user preferences.
   - Ask explicit user confirmation before implementation.
3. Interaction cadence (required)
   - Pause after each section and ask for feedback before moving to the next section.
   - Do not assume user priorities for timeline or scope without explicit confirmation.
