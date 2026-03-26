# Phase 5D / P4 Brief: Worker Loop Integration and Stream D Skill Pilot

**Date**: 2026-03-26  
**Status**: PLANNING — authorized by D-189, Phase 5C complete  
**Authority**: PM/CEO approval required before any Stream D execution semantics land  
**Predecessor**: Phase 5C (D-189, complete 2026-03-26)  
**Schema version**: v2.0.0 (locked)

---

## 1. Context and Authorization

Phase 5C delivered the Worker Inner Loop (5C.1 repo map, 5C.2 lint/test repair loops, 5C.3 Docker sandbox). D-189 explicitly states: "Enables P4+ planning per D-188 scope."

The D-183 P3 item — "Manifest-driven selective install, canonical-to-multi-target, memory/rollback, specialist delegation (Phase 5C+)" — is now unblocked.

The `next_phase_plan.md` Stream D (Skill Execution Pilot) entry gate requires:
- Kernel Stream (A): **COMPLETE** (D-186, D-187)
- Memory Reduction Stream (B): **STATUS UNKNOWN** — must be assessed before Stream D starts
- Tiered Memory Stream (C): **STATUS UNKNOWN** — must be assessed before Stream D starts

**This brief defines P4 planning only. No execution semantics are authorized until the Stream B/C gate check below is resolved.**

---

## 2. P4 Scope (Authorized)

### 2.1 Stream B/C Gate Assessment (P0 — COMPLETE)

Before any Stream D or P3 D-183 work begins, assess current state of:

| Stream | Exit Criteria | Current Status | Action Required |
|--------|--------------|----------------|-----------------|
| B — Memory Reduction | `execution_deputy` at/under budget; routing validator passes; context measurement rerun green | **GREEN** (2026-03-26): routing validator 6/6 roles OK; pm_actual=179/3000, ceo_actual=99/1800 | No action required |
| C — Tiered Memory | hot/warm/cold contract exists; compaction logic aligned; packet/handoff continuity verified | **GREEN** (2026-03-26): `memory_tier_contract.md` and `compaction_behavior_contract.md` both present; hot/warm/cold tiers defined; retention guardrails in `compaction_retention.py` | No action required |

**Gate rule**: Stream D and D-183 P3 work require B and C confirmed green OR explicit PM/CEO waiver. **B and C are both GREEN as of 2026-03-26. Stream D entry gate is OPEN pending PM/CEO pilot candidate selection (D-190).**

### 2.2 Stream D — Skill Execution Pilot (P3, blocked pending B/C gate)

Per `next_phase_plan.md` §Stream D:

- Choose **one narrow declarative skill** as the pilot
- Add execution semantics only for that pilot path
- Keep existing governance gates authoritative
- Hard limits: no full skill-execution engine; no forced routing; no auto-promotion of generated skills
- Rollback path must exist before any pilot lands

**Candidate pilot skills** (for PM/CEO selection):
1. `repo_map` — already implemented in 5C.1; pilot wiring it as a callable skill via `skill_resolver.py`
2. `lint_repair` — already implemented in 5C.2; pilot as a skill-dispatched repair request
3. A read-only research/analysis skill with no write authority

### 2.3 D-183 P3 Items (P3, blocked pending B/C gate and PM/CEO approval)

From the D-183 approved implementation sequence:

| Item | Description | Constraint |
|------|-------------|------------|
| Manifest-driven selective install | Skill manifest declares what surfaces it installs; operator can selectively apply | No new authority path; surface-only |
| Canonical-to-multi-target | Extend canonical skill outputs to multiple target surfaces | Via existing skill_resolver.py seam only |
| Memory/rollback for skills | Skills record rollback state before applying changes | Uses existing rollback_protocol.md pattern |
| Specialist delegation | Route narrow specialist tasks to dedicated skill workers | Via subagent_routing_matrix.yaml:7 seam only |

---

## 3. Non-Goals (Explicit Rejections)

Per D-183 rejection boundaries and `next_phase_plan.md` explicit deferrals:

- No full skill-execution engine (no mandatory routing for all work)
- No auto-promotion of generated/self-evolved skills into production
- No new authority plane or second control plane
- No broad kernel rewrite
- No cross-repo rollout (quant_current_scope closes first per D-186)
- No weakening of kernel guardrails or auditor/CEO-GO authority
- No EvoSkill-style skill evolution
- No package/hosted-service productization

---

## 4. Entry Gate Checklist

Before any P4 implementation work begins:

- [ ] Stream B assessed: run `python scripts/build_exec_memory_packet.py` and routing validator; confirm `execution_deputy` budget status
- [ ] Stream C assessed: confirm `docs/memory_tier_contract.md` exists and compaction behavior contract is aligned
- [ ] If B or C are not green: fix blockers first (do not skip the gate)
- [ ] If B and C are green or explicitly waived: PM/CEO records waiver in decision log before Stream D proceeds
- [ ] Pilot skill candidate selected and recorded in decision log (new D-190)
- [ ] Rollback plan for pilot documented before any execution semantics land

---

## 5. Immediate Next Steps

1. ~~Assess Stream B~~ **DONE**: routing validator 6/6 OK; pm_actual=179/3000, ceo_actual=99/1800. GREEN.
2. ~~Assess Stream C~~ **DONE**: `memory_tier_contract.md` and `compaction_behavior_contract.md` present and complete. GREEN.
3. **Report to PM/CEO**: B and C are both GREEN. Stream D entry gate is open. Select pilot skill candidate.
4. **PM/CEO records D-190**: Stream D authorization + pilot skill selection in decision log.
5. Do not implement any skill execution semantics before D-190 is committed.

---

## 6. Success Definition

P4 is successful when:

- Stream B and C gate status is confirmed (green or explicitly waived)
- One narrow pilot skill executes through the existing governance chain without introducing new authority paths
- Rollback path is documented and tested
- Full suite still passes (756+ tests)
- No kernel guardrails weakened
- D-190 decision log entry committed

---

## 7. Authority Boundary (Unchanged)

- Worker loop: operates within existing kernel guardrails
- Cannot bypass auditor review for high-risk changes
- Cannot bypass CEO GO signal for ONE_WAY decisions  
- Skill pilot: max scope is one narrow path; human escalation on any governance gap
- Repair loops: hard 5-iteration cap (MAX_ITERATIONS=5, enforced in code)

---

## Evidence Footer

**Predecessor evidence**: D-189, 756 passed 1 skipped, Phase 5C scoped 122 passed, 2026-03-26  
**Authorization chain**: D-183 (P3 unblocked) → D-188 (Phase 5C approved) → D-189 (Phase 5C complete) → P4 planning authorized  
**Next decision required**: D-190 (Stream D / pilot authorization after B/C gate check)
