# Terminal Zero Governance Control Plane

`quant_current_scope` is a local, script-driven AI engineering control plane.

Its job is simple:

- turn vague AI work into explicit, checkable work,
- run that work inside a bounded process,
- and leave behind evidence that another human or agent can trust.

This is not a hosted agent platform or consumer app.
It is a repo-native governance system for running AI-assisted engineering work with explicit boundaries, closure, and handoff.

## Release Status

- Current release: targeting **1.0**
- This repository is the shipped product boundary for the control-plane surface.
- Root `SOP/` docs remain canonical kernel/program/history docs for maintainers.

## 1.0 Release Boundary

**Shipped:**
- `sop` CLI and subcommands (`startup`, `run`, `validate`, `takeover`, `supervise`, `init`)
- Kernel templates for truth surfaces
- Startup → run → validate → takeover loop
- PyPI install path (`pip install terminal-zero-governance`)

**Supported platforms:**
- Python 3.12+
- Windows, Linux

**Not promised (future work):**
- Hosted service
- npm/npx scaffolding
- GitHub Action
- VS Code extension
- Zero-human autopilot

## What Problem This System Solves

Most AI engineering systems fail for one of six top-level reasons:

- the task is unclear,
- the authority boundary is unclear,
- execution happens in chat instead of in artifacts,
- “done” is asserted without verification,
- handoff is weak,
- or nobody can explain what happened afterward.

This repository solves those problems in a fixed order.

## P0 to P5

Read this as a top-down PM map.
Each level answers one question:

- `P0`: what is allowed?
- `P1`: what exactly are we trying to do?
- `P2`: what is happening now?
- `P3`: is it actually ready?
- `P4`: what does the next person need?
- `P5`: what do we keep as long-term truth?

### P0. Governance Boundary
**Problem Category**
- uncontrolled AI execution

**Problem**
- AI work is dangerous when nobody knows the goal, risk, owner, non-goals, or approval threshold.

**Solution**
- force every round to start inside an explicit execution boundary.

**Concrete Layers**
- entrypoint:
  - `scripts/startup_codex_helper.py`
- core artifacts:
  - `docs/context/startup_intake_latest.json`
  - `docs/context/startup_intake_latest.md`
  - `docs/context/init_execution_card_latest.md`
  - `docs/context/round_contract_seed_latest.md`

**What This Produces**
- one explicit statement of intent
- one explicit risk lane
- one explicit done-when contract

**PM Handoff**
- check whether the round is solving the right problem
- check whether the declared risk lane matches the real business risk
- stop the round here if the goal, owner, or boundary is wrong

### P1. Planning Truth
**Problem Category**
- vague work and drifting requirements

**Problem**
- AI systems often start coding before the task is decomposed into something reviewable.

**Solution**
- convert top-level intent into structured, inspectable planning truth.

**Concrete Layers**
- startup interrogation captures:
  - scope
  - non-goals
  - interfaces
  - owned files
  - closure checks
- authoritative docs:
  - `top_level_PM.md`
  - `docs/decision log.md`
  - `docs/loop_operating_contract.md`

**What This Produces**
- a round starts from declared constraints instead of prompt residue
- planning truth is anchored to durable docs, not only the current chat

**PM Handoff**
- confirm the round is solving the correct business/system problem
- confirm what is intentionally out of scope
- decide whether the plan should proceed, narrow, or be reframed

### P2. Execution Truth
**Problem Category**
- invisible work and context drift

**Problem**
- chat-only work is hard to resume, hard to audit, and easy to derail.

**Solution**
- run one bounded loop that refreshes working artifacts instead of hiding state in conversation history.

**Concrete Layers**
- entrypoint:
  - `scripts/run_loop_cycle.py`
- core artifacts:
  - `docs/context/loop_cycle_summary_latest.json`
  - `docs/context/loop_cycle_summary_latest.md`
  - `docs/context/exec_memory_packet_latest.json`
  - `docs/context/exec_memory_packet_latest.md`

**What This Produces**
- current execution state
- current advisory outputs
- current machine-readable memory for the next step

**PM Handoff**
- read this layer to understand what the system is actually doing now
- do not use it to redefine scope; use it to judge whether execution matches plan
- if execution drifts, redirect the round before closure

### P3. Readiness Truth
**Problem Category**
- false completion

**Problem**
- AI systems can sound complete before the work is actually safe to escalate or ship.

**Solution**
- create an explicit readiness decision instead of relying on confidence or fluent narrative.

**Concrete Layers**
- entrypoint:
  - `scripts/validate_loop_closure.py`
- core artifacts:
  - `docs/context/loop_closure_status_latest.json`
  - `docs/context/loop_closure_status_latest.md`

**What This Produces**
- `READY_TO_ESCALATE`, `NOT_READY`, or infra/input failure
- evidence tied back to current artifacts

**PM Handoff**
- this is the main “go / not yet” surface
- if `NOT_READY`, the PM should ask what evidence is missing, not “why is the agent low confidence?”
- if `READY_TO_ESCALATE`, the PM still owns the decision to proceed

### P4. Handoff Truth
**Problem Category**
- expensive restarts and weak continuity

**Problem**
- the next operator or agent often starts cold, redoes context gathering, or inherits unclear state.

**Solution**
- turn takeover into a deterministic readout instead of an oral tradition.

**Concrete Layers**
- entrypoint:
  - `scripts/print_takeover_entrypoint.py`
- core artifacts:
  - `docs/context/next_round_handoff_latest.json`
  - `docs/context/next_round_handoff_latest.md`
- optional convenience mirrors:
  - repo-root `*_LATEST.md` files when present

**What This Produces**
- a clean next-step view
- clear handoff artifacts
- lower restart cost for the next round

**PM Handoff**
- this is the minimum surface the next human should read before continuing
- if the handoff feels unclear, the system has not really closed the round
- use this layer to preserve continuity between planning, execution, and the next decision

### P5. Evidence And Learning Truth
**Problem Category**
- no audit trail and repeated mistakes

**Problem**
- without evidence, you cannot audit the run; without learning, you repeat the same mistakes.

**Solution**
- preserve runtime evidence, optional supervision, and explicit lessons so the control plane improves over time.

**Concrete Layers**
- generated artifacts under `docs/context/`
- optional supervision:
  - `scripts/supervise_loop.py`
- long-lived truth records:
  - `docs/lessonss.md`
  - `docs/decision log.md`
  - `docs/ARTIFACT_POLICY.md`

**What This Produces**
- traceable runs
- explicit mistakes and guardrails
- an improving control plane instead of one-off sessions

**PM Handoff**
- review this layer to improve the system, not to micromanage one round
- convert repeated misses into clearer guardrails
- use this layer to reduce human friction over time, especially for non-technical operators

## In One Line

P0 defines the boundary.  
P1 defines the work.  
P2 shows what is happening.  
P3 decides readiness.  
P4 makes the next step legible.  
P5 keeps evidence and learning alive.

## PM View

If you are a non-technical PM or operator, you can read the system in this order:

1. `P0` — is this round allowed and correctly bounded?
2. `P1` — are we solving the right problem?
3. `P3` — is the work actually ready?
4. `P4` — what should happen next?
5. `P5` — what should we change in the system itself?

You usually do **not** need to inspect low-level scripts or generated machine artifacts unless something looks wrong.

## Optimization Direction

The current direction for this control plane is:

- build on top of the existing kernel,
- do not do a large refactor unless the same truth is duplicated and conflicting,
- make the orchestrator more state-aware through better artifacts, not more prompt text,
- and reduce human effort to the smallest set of decisions that still preserve product truth.

In plain terms:

- the human should mostly guard the spec,
- judge boundary or priority changes,
- and watch system drift.

The human should **not** need to micromanage implementation steps if the control plane is doing its job.

## What We Are Optimizing For

As systems grow, like `Eureka` and `Quant`, failure usually comes from one of these places:

- planning truth, execution truth, and PM/product truth drift apart,
- frontend/backend/data/ops become separate local loops instead of one system,
- approval becomes a slot machine around confidence rather than a decision about evidence and direction,
- technical optimization outruns product or PM feedback,
- status surfaces multiply until nobody knows which one matters,
- or the planner rereads too much of the repo and still misses the current bottleneck.

The optimization goal is therefore:

- minimal human friction,
- maximal state clarity,
- bounded execution,
- explicit planner bridge,
- and less guidance over time, not more.

## Build-On-Top Principle

The default strategy is additive, not destructive.

Use this rule:

- keep the existing `startup -> loop -> closure -> takeover` kernel,
- add thin integration artifacts on top,
- only refactor a subsystem after repeated evidence shows that the additive layer cannot resolve the conflict.

This follows Ockham's razor:

- if a thin bridge solves the problem, do not invent a new subsystem,
- if a small contract solves the drift, do not rebuild the workflow,
- if a simple artifact can make the system legible, do not add more prompts.

## Human Role

The target human role is:

- guard the spec,
- approve changes to direction, scope, or boundary,
- decide priorities and tradeoffs,
- and observe overall system health.

The target human role is **not**:

- line-by-line code supervisor,
- manual status compiler,
- prompt babysitter,
- or the only entity that keeps documents honest.

See `../ENDGAME.md` for the full endgame philosophy and target state.

## Truth Model

The system stays coherent through four truth layers:

1. **Static Truth** — long-lived intent and constraints
2. **Live Truth** — what is active now
3. **Bridge Truth** — what recent execution means for product/system and planner
4. **Evidence Truth** — what actually happened and what proves it

The system becomes reliable when these layers stay thin, distinct, and connected.

See `../ENDGAME.md` for detailed truth model, orchestrator state model, planner fresh-context model, and multi-stream coordination model.

## Roadmap

See `../ROADMAP.md` for the full delivery plan.

**Current status:** All roadmap waves (W0–W6) complete (2026-03-19). See `../ROADMAP.md` for details.

## What This Repository Is

This repository is primarily for:

- operators running the governance loop locally,
- engineers maintaining the loop scripts and artifact contracts,
- reviewers who need auditable startup, closure, and handoff outputs.

## What This Repository Is Not

This repository is not:

- a hosted autonomous agent platform,
- a consumer chat product,
- a plugin marketplace,
- a zero-human autopilot,
- or a second authority plane outside the documented control flow.

## Start Here

- Public/project orientation: this README
- Operational endgame: `../ENDGAME.md`
- Delivery roadmap: `../ROADMAP.md`
- Local operator flow: `OPERATOR_LOOP_GUIDE.md`
- Internal procedures: `docs/loop_operating_contract.md`, `docs/runbook_ops.md`, `docs/operator_reference.md`

## Entrypoints

### Primary (sop CLI)

```bash
sop startup --repo-root .      # Initialize a round
sop run --repo-root .          # Execute one loop cycle
sop validate --repo-root .     # Check closure readiness
sop takeover --repo-root .     # Print takeover guidance
sop supervise --max-cycles 1   # Loop health monitoring
sop init <target-dir>          # Bootstrap new governed repo
```

Install: `pip install terminal-zero-governance`

### Compatibility (scripts)

For existing workflows or local development:

```bash
python scripts/startup_codex_helper.py --repo-root .
python scripts/run_loop_cycle.py --repo-root .
python scripts/validate_loop_closure.py --repo-root .
python scripts/print_takeover_entrypoint.py --repo-root .
python scripts/supervise_loop.py --repo-root .
```

These are preserved for backward compatibility. New users should prefer `sop`.

## Quickstart

### 1. Install

```bash
pip install terminal-zero-governance
```

Or from source:

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # Windows
pip install -e .
```

### 2. Verify

```bash
sop --help
sop version
```

### 3. Initialize a new governed repository

```bash
sop init my-project
cd my-project
```

### 4. Run the main loop

```bash
sop startup --repo-root .
sop run --repo-root . --skip-phase-end
sop validate --repo-root .
sop takeover --repo-root .
```

### 5. Optional supervision

```bash
sop supervise --max-cycles 1
```

### 6. Run tests (from source)

```bash
python -m pytest -q
```

**New user?** See `USER_GUIDE.md` for a complete walkthrough.

## Platform Assumptions

- Python `3.12+`
- Windows PowerShell examples by default
- repo-local `.venv` preferred
- canonical dependency metadata in `pyproject.toml`
- pinned installs via `constraints.txt` and `constraints-dev.txt`

## Repository Layout

- `scripts/` — orchestration, validation, reporting, and takeover entrypoints
- `docs/` — contracts, runbooks, policy docs, and planning docs
- `docs/context/` — generated machine/human artifacts exchanged between loop stages
- `tests/` — control-plane and script coverage
- `.github/workflows/` — CI workflows

## Documentation Routing

### New Users (Start Here)

- `USER_GUIDE.md` — complete walkthrough for new users

### Public / External

- `README.md` (this file)
- `USER_GUIDE.md`
- `CHANGELOG.md`
- `RELEASING.md`
- `CONTRIBUTING.md`
- `SUPPORT.md`
- `CODE_OF_CONDUCT.md`
- `GOVERNANCE.md`
- `SECURITY.md`

### Internal Operator

- `OPERATOR_LOOP_GUIDE.md`
- `docs/runbook_ops.md`
- `docs/operator_reference.md`
- `docs/loop_operating_contract.md`
- `docs/security.md`
- `docs/ARTIFACT_POLICY.md`
- `docs/context/workflow_status_latest.{json,md}` when present

## License

MIT. See `LICENSE`.
