---
name: se-executor
description: Trigger-based software engineering execution rigor for complex implementation rounds. Use when a change is multi-file, edge-case-heavy, or has elevated regression risk.
---

# SE Executor Skill

This skill is available by trigger and is not mandatory by default.

## 1. Trigger Conditions
Use this skill when one or more are true:
1. Multi-file change with cross-module impact.
2. Elevated edge-case or failure-path risk.
3. Handoff risk between implementer and reviewer.
4. Regression risk not covered by current tests.

## 2. Execution Contract
1. Load planner entry surfaces:
   - `docs/context/planner_packet_current.md` (current context, active brief, bridge truth, decision tail, blocked next step, active bottleneck)
   - `docs/context/impact_packet_current.md` (changed files, owned files, touched interfaces, failing checks)
   - `docs/context/done_checklist_current.md` (acceptance criteria)
2. Confirm active stream and active stage from project hierarchy (`L1/L2/L3`).
3. Convert scope into 3-5 concrete tasks:
   - each task has `TaskID` (`TSK-01`, `TSK-02`, ...),
   - artifact path(s),
   - acceptance check,
   - done condition.
4. Implement in smallest safe vertical slices.
5. Verify:
   - unit/integration checks relevant to touched modules,
   - runtime smoke checks for affected workflows.
6. Refresh impact packet:
   - Update `docs/context/impact_packet_current.md` with changed files, owned files, touched interfaces, failing checks.
7. Report:
   - what changed,
   - proof it works,
   - unresolved risks.

## 3. Output Schema
1. Scope line (`stream`, `stage`, `owner`, `round_exec_utc`).
2. Task table (`task_id`, `task`, `artifact`, `check`, `status`, `evidence_id`).
3. Verification evidence (`evidence_id`, `command`, `result`, `notes`, `evidence_utc`, `run_id`).
4. Machine maps:
   - `TaskEvidenceMap: TSK-01:EVD-01,TSK-02:EVD-02,...`
   - `EvidenceRows: EVD-01|<RoundID>|<evidence_utc>;EVD-02|<RoundID>|<evidence_utc>;...`
   - run `python .codex/skills/_shared/scripts/validate_se_evidence.py --round-id "<RoundID>" --round-exec-utc "<round_exec_utc>" --task-map "<TaskEvidenceMap values>" --evidence-map "<EvidenceRows values>"`.
   - emit `EvidenceValidation: PASS/BLOCK`.
5. Rollback note.
6. Closure block:
   - `ClosurePacket: RoundID=<...>; ScopeID=<...>; ChecksTotal=<int>; ChecksPassed=<int>; ChecksFailed=<int>; Verdict=<PASS|BLOCK>; OpenRisks=<...>; NextAction=<...>`
7. Closure count rule:
   - `ChecksTotal` = total acceptance checks in the task table.
   - `ChecksPassed` = checks with passing evidence.
   - `ChecksFailed` = checks failed, missing, or not verifiable.
8. Closure validation:
   - run `python .codex/skills/_shared/scripts/validate_closure_packet.py --packet "<ClosurePacket line>" --require-open-risks-when-block --require-next-action-when-block`
   - emit `ClosureValidation: PASS/BLOCK`

## 4. Loop-Close Criteria
1. `PASS` only when all are true:
   - all acceptance checks pass,
   - proof evidence is attached for each completed task (`TaskID` -> `EvidenceID` is 1:1),
   - no unresolved in-scope Critical/High risks.
2. `BLOCK` when any are true:
   - one or more acceptance checks failed/missing,
   - any completed task lacks an `EvidenceID` link,
   - any `run_id` in evidence rows does not match `RoundID`,
   - any `evidence_utc` is older than 24 hours relative to `round_exec_utc`,
   - required verification could not run (tooling/env/data unavailable) without accepted fallback,
   - unresolved in-scope Critical/High risk remains,
   - missing any required closure field (`RoundID`, `ScopeID`, `Checks*`),
   - failed evidence validation,
   - failed closure validation.
3. If blocked, include explicit owner, next action, and rollback note.

## 5. Escalation Rule
If the same trigger recurs for `>= 2` rounds in the same milestone/session, recommend upgrading this skill to mandatory for that milestone and request explicit user approval before enforcing.
