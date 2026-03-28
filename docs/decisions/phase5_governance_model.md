# ADR-002: Phase 5 Governance Model

**Status**: Draft
**Date**: 2026-03-11
**Deciders**: PM, CEO
**Context**: Phase 5 adds plugin layer; must define how plugins interact with existing governance

---

## Decision

Phase 5 governance extends existing authority model without replacing it. Plugins are **advisory**, kernel is **authoritative**.

---

## Existing Governance Model (Unchanged)

### Authority Hierarchy
Per `loop_operating_contract.md` section 2:

1. **PM**: Scope/owner/checks governance, not implementation/review execution
2. **CEO**: GO/HOLD/REFRAME decisions, strategic direction, promotion decisions
3. **Auditor**: PASS/BLOCK decisions on scope/risk compliance
4. **Worker**: Implementation decisions within approved scope

**Phase 5 does not add new authorities.** No CTO, COO, or other roles with veto power.

### Source-of-Truth Hierarchy
Per `loop_operating_contract.md` section 2a:

1. Init baseline product artifacts (authoritative): `top_level_PM.md`, PRD
2. Governance baseline (authoritative): `docs/decision log.md`
3. Approved phase scope docs: `docs/phase_brief/*.md`
4. Generated execution artifacts: dossier, calibration, GO signal, startup card, exec memory
5. Worker-authored summaries: useful context, non-authoritative if conflicting

**Phase 5 does not change this hierarchy.** Plugins sit below worker-authored summaries (advisory only).

**IMPORTANT CLARIFICATION**: "Advisory" means plugins **recommend** actions but **kernel enforces** decisions. Example:
- Plugin risk assessment **recommends**: "This task is LOW risk, suggest auto-approve"
- Kernel approval gate **enforces**: Validates risk assessment, checks against policy, executes approval or escalation
- Plugin cannot bypass kernel enforcement (e.g., cannot auto-approve a task kernel classifies as HIGH risk)

### Decision Classes
Per `loop_operating_contract.md` section 2b:

- **ONE_WAY**: Hard to reverse, broad blast radius, external side effects
- **TWO_WAY**: Reversible with bounded blast radius

**Phase 5 does not change decision class requirements.** ONE_WAY HIGH still requires dual-judge, CEO GO signal, etc.

---

## Phase 5 Governance Extensions

### 1. Plugin Approval Process

**New Requirement**: All plugins/skills require PM/CEO approval before activation.

**Approval Flow**:
```
1. Plugin/skill authored (skill.yaml, guardrails.yaml, eval.yaml)
2. PM/CEO reviews:
   - Does skill weaken kernel guardrails? (REJECT if yes)
   - Does skill bypass truth gates? (REJECT if yes)
   - Does skill add value without risk? (APPROVE if yes)
3. Approval recorded in decision log.md
4. Plugin added to extension allowlist
5. Plugin available for project-local activation
```

**Rationale**: Prevents unapproved plugins from entering production.

---

### 2. Policy Change Approval Process

**New Requirement**: All adaptive policy changes require PM/CEO approval.

**Policy Change Flow**:
```
1. Benchmark harness detects model capability change (e.g., sql_accuracy drops from 0.78 to 0.65)
2. Adaptive guardrail system recommends policy change (sql_tasks: medium → tight)
3. System generates policy change proposal:
   - Current policy: sql_tasks=medium
   - Recommended policy: sql_tasks=tight
   - Rationale: model capability dropped below threshold
   - Impact: all SQL tasks now require tighter review
4. PM/CEO reviews proposal
5. If approved, record in decision log.md with:
   - Policy change description
   - Rationale (benchmark result)
   - Approver (PM/CEO)
   - Date
   - Impact scope (which tasks affected)
6. Policy applied to future rounds
```

**Rationale**: No silent policy changes. Humans approve all governance changes.

---

### 3. Extension Allowlist Mechanism

**New Artifact**: `quant_current_scope/.sop_config.yaml` (project-local config)

**Purpose**: Control which plugins/skills are active per project.

**Schema**:
```yaml
project_name: "production-api"
guardrail_strength: "tight"  # loose | medium | tight
active_skills:
  - safe-db-migration
  - zero-downtime-deploy
  - rollback-plan
disabled_skills:
  - react-component  # Not applicable to backend project
  - api-endpoint     # Not applicable to backend project
benchmark_profile: "opus_4_6_baseline"
approval_routing_policy:  # Policy only, kernel enforces
  low_risk: "auto_approve"      # Kernel validates, then auto-approves if policy allows
  medium_risk: "auditor_review" # Kernel routes to human auditor review
  high_risk: "ceo_go_signal"    # Kernel routes to CEO GO signal (always)
```

**IMPORTANT**: `approval_routing_policy` is a **policy declaration**, not executable code. The kernel approval gate reads this policy and enforces it. Plugins cannot execute approvals directly.

**Approval Requirement**: `.sop_config.yaml` changes require PM/CEO approval in decision log.md.

**Rationale**: Project-local config allows tuning without global changes, but still requires approval.

---

### 4. Benchmark → Policy Feedback Loop

**New Process**: Benchmark results inform policy, but humans approve changes.

**Feedback Loop**:
```
1. Benchmark harness runs (weekly or per model version)
2. Results compared to previous baseline
3. If capability change detected:
   a. Generate policy change proposal
   b. Route to PM/CEO for approval
   c. If approved, update policy in decision log.md
   d. Apply to future rounds
4. If no capability change:
   a. Log "no change" result
   b. Continue with existing policy
```

**Approval Threshold**: Any policy change that affects guardrail strength or approval routing requires PM/CEO approval.

**Rationale**: Adaptive system learns from benchmarks, but humans remain in control.

---

### 5. Skill Guardrail Merge Logic

**New Requirement**: Skill guardrails merge with kernel guardrails (kernel is floor).

**Merge Logic**:
```python
def merge_guardrails(kernel_guardrails, skill_guardrails):
    """
    Merge skill guardrails with kernel guardrails.
    Kernel is floor (cannot be weakened).
    Skill can only add gates, not remove.
    """
    merged = kernel_guardrails.copy()

    for gate in skill_guardrails:
        if gate.weakens(kernel_guardrails):
            raise GuardrailViolation(
                f"Skill cannot weaken kernel guardrail: {gate}"
            )

        if gate.adds_requirement():
            merged.add(gate)  # Skill adds extra requirement

    return merged
```

**Example**:
```
Kernel says: HIGH risk requires CEO GO signal
Skill says: safe-db-migration also requires rollback plan + auditor review

Merged result:
- CEO GO signal (kernel minimum)
- Rollback plan (skill addition)
- Auditor review (skill addition)

Invalid example:
Kernel says: HIGH risk requires CEO GO signal
Skill says: safe-db-migration does NOT require CEO GO signal

Result: REJECT skill (cannot weaken kernel)
```

**Rationale**: Skills can add safety, never remove it.

---

## Governance Artifact Updates

### 1. Decision Log Entry Format (Extended)

**New Fields for Phase 5**:
```markdown
### [Decision ID] - [Short Title]
**Date**: YYYY-MM-DD
**Type**: Plugin Approval | Policy Change | Config Change | Architecture Decision
**Status**: Pending | Approved | Rejected
**Approver**: PM | CEO | Both
**Context**: Brief description
**Decision**: Approved decision or rejection reason
**Impact**: What this enables or blocks
**Scope**: Which projects/tasks affected (for policy changes)
**Rationale**: Why this change (for policy changes, include benchmark result)
**References**: Links to relevant docs/ADRs
```

**Example - Plugin Approval**:
```markdown
### D5.1.1 - Approve safe-db-migration Skill
**Date**: 2026-03-15
**Type**: Plugin Approval
**Status**: Approved
**Approver**: PM/CEO
**Context**: New skill for database schema changes with rollback plan
**Decision**: Approved for production use
**Impact**: Enables safe DB migrations with enforced rollback plans
**Scope**: All projects with database changes
**Rationale**: Adds safety without weakening kernel guardrails
**References**: quant_current_scope/skills/safe_db_migration/skill.yaml
```

**Example - Policy Change**:
```markdown
### D5.2.3 - Tighten SQL Task Guardrails
**Date**: 2026-03-20
**Type**: Policy Change
**Status**: Approved
**Approver**: CEO
**Context**: Benchmark detected sql_accuracy drop from 0.78 to 0.65
**Decision**: Change sql_tasks guardrail from medium → tight
**Impact**: All SQL tasks now require auditor review + CEO GO signal
**Scope**: All tasks with SQL changes (migrations, queries, schema)
**Rationale**: Model capability dropped below 0.70 threshold
**References**: quant_current_scope/benchmark/results/opus_4_6_baseline.json
```

---

### 2. Round Contract Extensions (Optional Fields)

**New Optional Fields**:
```markdown
## Phase 5 Extensions (Optional)

ACTIVE_SKILLS: safe-db-migration, rollback-plan
BENCHMARK_PROFILE: opus_4_6_baseline
GUARDRAIL_STRENGTH: tight
ADAPTIVE_POLICY_APPLIED: D5.2.3 (sql_tasks=tight)
```

**Rationale**: Round contract can reference active plugins/policies for traceability.

---

### 3. Startup Intake Extensions (Optional Fields)

**New Optional Fields**:
```json
{
  "phase5_extensions": {
    "active_skills": ["safe-db-migration", "rollback-plan"],
    "benchmark_profile": "opus_4_6_baseline",
    "guardrail_strength": "tight",
    "adaptive_policies": ["D5.2.3"]
  }
}
```

**Rationale**: Startup intake can capture Phase 5 config for audit trail.

---

## Authority Boundaries (Explicit)

### What Plugins CAN Do
1. **Recommend** guardrail strength based on benchmark results
2. **Add** extra safety requirements (e.g., rollback plan for DB migrations)
3. **Optimize** memory usage via subagent routing
4. **Recommend** automation for low-risk, high-volume tasks (dependency updates, test generation)
5. **Measure** model capability via benchmark harness

**CLARIFICATION**: "Recommend automation" means plugin risk assessment suggests a task is low-risk and suitable for automation. The kernel approval gate validates this recommendation and enforces the actual approval/execution decision.

### What Plugins CANNOT Do
1. **Override** PM/CEO/Auditor decisions
2. **Weaken** kernel guardrails (kernel is floor)
3. **Bypass** truth gates or closure validation
4. **Auto-approve** high-risk tasks (ONE_WAY HIGH always requires CEO GO signal)
5. **Change policy** without PM/CEO approval in decision log.md

### Enforcement
- Code-level checks (reject list in plugin loader)
- Runtime validation (authority checks before execution)
- Audit trail (all policy changes logged in decision log.md)
- Supervision (supervise_loop.py detects unauthorized changes)

---

## Conflict Resolution

### Plugin vs Kernel Conflict
**Rule**: Kernel always wins.

**Example**:
```
Kernel: HIGH risk requires CEO GO signal
Plugin: Benchmark says model is highly capable, recommend loose guardrails

Resolution: CEO GO signal still required (kernel floor cannot be lowered)
```

### Plugin vs Plugin Conflict
**Rule**: Most restrictive wins.

**Example**:
```
Skill A: safe-db-migration requires rollback plan
Skill B: zero-downtime-deploy requires blue-green deployment

If both skills active: Require BOTH rollback plan AND blue-green deployment
```

### Policy Change vs Active Round
**Rule**: Policy changes apply to future rounds, not active rounds.

**Example**:
```
Active round started with guardrail_strength=medium
Policy change approved: guardrail_strength=tight

Resolution: Active round continues with medium, next round uses tight
```

---

## Rollback & Emergency Override

### Emergency Override (CEO Authority)
**Scenario**: Adaptive policy causes production issue.

**Override Process**:
```
1. CEO declares emergency override
2. Record override in decision log.md:
   - Override reason (e.g., "adaptive policy blocked critical hotfix")
   - Override scope (e.g., "disable adaptive guardrails for next 24h")
   - Override approver (CEO)
   - Override expiration (e.g., "2026-03-21 23:59 UTC")
3. Apply override (temporarily disable adaptive policy)
4. Fix root cause
5. Remove override after expiration
6. Post-mortem: Why did adaptive policy fail? Update policy logic.
```

**Rationale**: CEO retains ultimate authority for emergency situations.

### Policy Rollback
**Scenario**: Policy change causes unintended consequences.

**Rollback Process**:
```
1. PM/CEO identifies issue with policy change
2. Record rollback in decision log.md:
   - Rollback reason (e.g., "policy too restrictive, blocking valid work")
   - Rollback scope (e.g., "revert D5.2.3, restore sql_tasks=medium")
   - Rollback approver (PM/CEO)
3. Revert policy to previous state
4. Post-mortem: Why did policy change fail? Update recommendation logic.
```

**Rationale**: Policy changes are reversible if they cause issues.

---

## Open Questions for PM/CEO

1. **Plugin approval delegation**: Can PM approve plugins without CEO, or always require both?
   - Recommendation: PM can approve LOW-risk plugins, CEO required for MEDIUM/HIGH-risk

2. **Policy change approval delegation**: Can PM approve policy changes without CEO?
   - Recommendation: PM can approve minor tuning (loose ↔ medium), CEO required for major changes (medium ↔ tight)

3. **Emergency override authority**: Only CEO, or can PM also override in emergencies?
   - Recommendation: CEO only, to maintain clear authority hierarchy

4. **Benchmark frequency**: Weekly, monthly, or per model version?
   - Recommendation: Per model version + monthly for stability

5. **Skill versioning**: How to handle skill updates (v1.0 → v1.1)?
   - Recommendation: Treat as new plugin approval (require PM/CEO review)

---

## Next Steps

1. PM/CEO review and approve this ADR
2. Record approval in `quant_current_scope/docs/decision log.md`
3. Proceed to ADR-003: Extension Loading Policy
4. Proceed to ADR-004: Benchmark → Policy Feedback Loop

---

**Status**: Awaiting PM/CEO approval
