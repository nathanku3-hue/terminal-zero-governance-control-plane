# Top Level PM and Thinker Compass

Date: 2026-03-01
Owner: PM / Architecture Office
Status: ACTIVE

## Why This File Exists
- Consolidate top-level thinking models used for PM, architecture, and execution governance.
- Keep one source-of-truth for philosophy updates that must propagate to worker repos first, then migrate to main SOP governance artifacts.
- Avoid silent drift between strategic language and engineering behavior.

## Core Base (Already Adopted)
- McKinsey-style decomposition
- MECE
- 5W1H
- Pyramid Principle
- Top-Level PM operating lens

## Top-Level Thinker Expansion Pack

## 1. Systems Dynamics and Cybernetics
Core concept:
- Do not only optimize nodes; control feedback loops.
- Ashby's Law: only variety can absorb variety.
- Control plane complexity must match or exceed environment complexity.

Application pattern:
- Prefer adaptive control (for example EWMA + hysteresis) over rigid threshold-only throttles.
- Design to absorb volatility and prevent livelock oscillation.

## 2. Axiomatic Design and Design by Contract
Core concept:
- Build systems on invariants, not hope.
- Define non-negotiable pre/post conditions and failure semantics.

Application pattern:
- Encode invariants first in tests and runtime contracts.
- Keep critical safety assertions explicit and fail-fast.

## 3. Antifragility
Core concept:
- Fragile systems break under stress.
- Resilient systems survive stress.
- Antifragile systems improve because of stress.

Application pattern:
- Capture quality debt and replay deferred heavy work in controlled windows.
- Use controlled chaos/sandbox signals to strengthen future behavior.

## 4. TPS Jidoka (Automation with Human Touch)
Core concept:
- On abnormality, stop the line and surface the problem.
- Never allow defects to flow silently downstream.

Application pattern:
- Prefer loud failures over silent degradation in build/test/runtime pipelines.
- Treat hidden failures as systemic defects, not acceptable trade-offs.

## 5. OODA Loop
Core concept:
- Observe -> Orient -> Decide -> Act.
- Advantage comes from fast and accurate loops in uncertain environments.

Application pattern:
- Instrument latency/error/state signals (Observe).
- Filter noise and infer regime (Orient).
- Choose utility-maximizing action (Decide).
- Execute control/degrade/recover action (Act).

## 6. Theory of Constraints (Eliyahu M. Goldratt)
Core concept:
- Every system is limited by a very small number of bottlenecks (often one).
- Optimizing non-bottlenecks creates the illusion of progress.

Application pattern:
- Continuously identify the current throughput bottleneck and align optimization there.
- In data pipelines, prioritize eliminating O(N) staging/copy bottlenecks before micro-optimizing compute.

## 7. Cynefin Framework (Dave Snowden)
Core concept:
- Problems belong to domains: Clear, Complicated, Complex, Chaotic, Confusion.
- Decision method must match domain type.

Application pattern:
- For Complex/Chaotic domains, use probe-sense-respond instead of rigid best-practice scripts.
- Keep QoS and ingestion control policies adaptive and evidence-driven.

## 8. Ergodicity and Survival Logic (Ole Peters)
Core concept:
- Ensemble average is not time average.
- Non-zero ruin probability destroys long-term compounding for a single entity.

Application pattern:
- Place survival constraints ahead of nominal expected return.
- Keep fail-closed data/update controls and strict lock discipline to minimize ruin pathways.

## Operational Synthesis
- MECE and decomposition reduce blind spots ("did we miss a failure mode?").
- Cybernetics, Jidoka, and contract design define how the system survives and reacts when failure modes happen.
- TOC, Cynefin, and Ergodicity enforce resource focus, domain-correct decisions, and long-horizon survival.

## Governance Rules
- Philosophy updates must be synced local-first:
  - update worker repo local feedback loop artifacts first.
  - only after all targeted worker updates pass, migrate summary to SOP main governance artifacts.
- Any partial worker failure blocks main migration (`fail-closed`).
