# Init-Phase Brainstorm Framework (Lean)

Owner: PM  
Status: ACTIVE  
Last Updated: 2026-03-05  
Applies To: Startup -> PM requirement framing -> Worker/Auditor loop entry

## 1) Why This Exists

This framework defines how to run the **init phase** so decisions are strong without creating analysis bloat.

Goals:
- Convert ambiguous requests into a clear, scoped delivery contract.
- Allow CEO and CTO to compare options before execution starts.
- Activate extra experts only when triggers fire.
- Keep output immediately usable by Worker/Auditor/CEO flow.

Non-goals:
- No new gates/scripts/architecture in this document.
- No replacement of `docs/expert_invocation_policy.md` or `docs/round_contract_template.md`.

## 2) How Great Companies Decide (Operating Pattern)

Great companies usually separate decision work into three layers:

1. Strategy Layer (CEO + leadership)
- Decide which problem is worth solving now.
- Evaluate strategic fit, timing, downside, and opportunity cost.

2. Product Layer (PM + CTO/Principal support)
- Translate intent into scope, constraints, and measurable outcomes.
- Produce option set and choose one approach.

3. Delivery Layer (Engineer + QA/Auditor)
- Execute and verify with evidence.
- Loop until decision is paste-ready for executive go/no-go.

Key principle: **fast, high-quality loops with explicit owners**.

## 3) Init-Phase Sequence (Before Round 1)

0. Startup intake (required)
- Run startup helper and lock:
  - `ORIGINAL_INTENT`
  - `DELIVERABLE_THIS_SCOPE`
  - `NON_GOALS`
  - `DONE_WHEN`
  - `POSITIONING_LOCK`
  - `TASK_GRANULARITY_LIMIT` (`1` or `2`)
  - `DECISION_CLASS`
  - `EXECUTION_LANE`
  - `INTUITION_GATE` (`MACHINE_DEFAULT` or `HUMAN_REQUIRED`)
  - `INTUITION_GATE_RATIONALE`

0a. Init hard controls (required before round 1 execution)
- `POSITIONING_LOCK` must be captured and carried into round 1 contract fields before any execution command.
- `TASK_GRANULARITY_LIMIT` must be `1` or `2`; if work exceeds that cap, split into additional rounds before execution.
- `INTUITION_GATE` decision rule:
  - Use `MACHINE_DEFAULT` for reversible, evidence-backed, low-ambiguity tasks.
  - Use `HUMAN_REQUIRED` for high-ambiguity, high-impact, or low-reversibility tasks.
- If `INTUITION_GATE=HUMAN_REQUIRED`, record PM/CEO acknowledgment before worker execution starts.

1. CEO/CTO option brainstorming (time-boxed)
- Generate at most **3 options** (A/B/C).
- For each option include:
  - Value hypothesis
  - Main risk
  - Evidence needed
  - Reversibility (easy/medium/hard)

2. PM decision framing
- Choose one option as default path.
- Convert to round contract fields and acceptance checks.

3. Expert activation check
- Apply triggers from `docs/expert_invocation_policy.md`.
- Default: keep expert count low; only escalate when trigger exists.

4. Worker/Auditor loop starts
- Worker executes scope.
- Auditor validates scope/risk.
- Iterate until end-loop criteria are met.

## 4) Expert Jump-Out Rules (No Overcomplication)

Use existing policy as source of truth:
- `docs/expert_invocation_policy.md`

Operational caps:
- Max **3 experts per round** (security/infra exception allowed by policy).
- Max **5 total expert invocations per task** across rounds.
- If no trigger: no extra expert.

Default routing:
- Normal work: Worker + Auditor only.
- Architecture/system risk: add `principal` or `system_eng`.
- Safety/reliability risk: add `riskops`.
- Test/coverage risk: add `qa`.
- Security/regulatory risk: add `devsecops`.
- Interface/module boundary risk: add `architect`.

Anti-overengineering rule:
- Any expert suggestion that expands beyond `DELIVERABLE_THIS_SCOPE` moves to backlog, not current round.

## 5) Philosopher Lens Overlay (Optional, Controlled)

Philosopher lenses are for **decision quality**, not for adding scope.

Default usage:
- Routine tasks: **0 philosopher lens**
- Important but bounded decision: **1 lens**
- Strategic/cross-repo decision: **max 2 lenses**

Hard limit:
- Never exceed 2 philosopher lenses in one init cycle.

### Priority Lens Table

| Priority | Thinker | High-value use for doers | Practical trigger |
|---|---|---|---|
| 1 | Rene Girard | Detect imitation traps, rivalry-driven roadmap drift | Competing via imitation without differentiated value |
| 2 | Leo Strauss | Regime/power narrative and statecraft framing | Public-sector, geopolitical, or institutional power constraints |
| 3 | Jurgen Habermas | Legitimacy and communication quality across stakeholders | High-trust coordination and cross-team buy-in risks |
| 4 | Karl Popper | Falsifiability and anti-dogma test framing | Claims are strong but weakly testable |
| 5 | Hannah Arendt | Responsibility and power consequences | High external impact or governance-sensitive decisions |
| 6 | Aristotle | Causality and first-principles decomposition | Problem framing is muddled or category boundaries unclear |
| 7 | Claude Shannon | Information bottleneck and signal-to-noise clarity | Data/communication overload is blocking decisions |
| 8 | Herbert Simon | Bounded rationality and satisficing design | Decision needs practical heuristics under time constraints |

Use rule:
- Each selected lens contributes exactly:
  - one decision question,
  - one risk check,
  - one acceptance check.
- If a lens adds extra deliverables, drop that output from current scope.

## 6) Decision Packet for PM (Paste-Ready)

```text
INIT_DECISION_PACKET
DATE_UTC: <timestamp>
ORIGINAL_INTENT: <one sentence>
DELIVERABLE_THIS_SCOPE: <one sentence>
NON_GOALS: <explicit list>
DONE_WHEN: <objective completion criteria>
POSITIONING_LOCK: <explicit stance to keep fixed through round 1>
TASK_GRANULARITY_LIMIT: <1|2 atomic tasks>
INTUITION_GATE: <MACHINE_DEFAULT|HUMAN_REQUIRED>
INTUITION_GATE_RATIONALE: <why this gate mode is selected>
INTUITION_GATE_ACK: <PM_ACK|CEO_ACK|N/A>
INTUITION_GATE_ACK_AT_UTC: <ISO8601|N/A>

OPTIONS:
- A: <summary> | VALUE: <...> | RISK: <...> | REVERSIBILITY: <easy/medium/hard>
- B: <summary> | VALUE: <...> | RISK: <...> | REVERSIBILITY: <easy/medium/hard>
- C: <summary> | VALUE: <...> | RISK: <...> | REVERSIBILITY: <easy/medium/hard>

DECISION_OWNER: <PM|CEO>
CHOSEN_OPTION: <A|B|C>
RATIONALE: <short evidence-based reason>

EXPERTS_TRIGGERED_THIS_INIT:
- <expert>: <trigger reason>
CAP_APPLIED: <x/3 round, y/5 task>

PHILOSOPHER_LENSES_USED:
- <thinker>: <1 question | 1 risk | 1 acceptance check>

NEXT_STEP: Worker starts round contract and execution.
```

## 7) Who This Is Better/Worse For

Better for:
- CEO/PM: clearer strategic tradeoffs before execution starts.
- CTO/Principal: better architecture decision hygiene at low process cost.
- Auditor/QA: fewer ambiguous scopes and less rework.

Worse for:
- Very small one-line fixes: adds modest upfront framing overhead.
- Teams optimizing only for immediate speed over decision quality.

Net recommendation:
- Keep this framework always-on for medium/high-impact work.
- Allow lightweight bypass for trivial changes with PM approval.

## 8) Integration References

- Startup intake and readiness: `scripts/startup_codex_helper.py`
- Loop contract: `docs/loop_operating_contract.md`
- Expert triggers and caps: `docs/expert_invocation_policy.md`
- Round contract handoff: `docs/round_contract_template.md`
- Authority boundaries: `docs/decision_authority_matrix.md`
