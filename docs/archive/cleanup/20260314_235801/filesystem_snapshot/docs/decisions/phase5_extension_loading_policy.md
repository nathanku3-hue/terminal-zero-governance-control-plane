# ADR-003: Phase 5 Extension Loading Policy

**Status**: Approved (Amended)
**Date**: 2026-03-12
**Deciders**: PM, CEO
**Approval**: D-165 (decision log.md)
**Amendments**: D-168 (approval authority), D-169 (benchmark interim rule), D-171 (risk_level required field)
**Context**: Phase 5 adds plugin/skill system; must define how extensions are loaded, activated, and controlled

---

## Decision

Extensions (plugins/skills) use **explicit allowlist** with **PM/CEO approval** before activation. No dynamic loading without governance.

---

## Extension Loading Model

### 1. Extension Types

**Skills**: Reusable software engineering patterns
- Location: `quant_current_scope/skills/`
- Examples: safe-db-migration, react-component, zero-downtime-deploy
- Structure: skill.yaml (definition) + guardrails.yaml (gates) + eval.yaml (benchmark requirements)

**Plugins**: Broader system extensions
- Location: `quant_current_scope/plugins/` (future)
- Examples: custom benchmark suites, alternative routing strategies, specialized validators
- Structure: plugin.yaml (definition) + implementation code

**Phase 5A.0 Scope**: Skills only. Plugins are future extension point.

---

## Extension Lifecycle

### Phase 1: Authoring
```
1. Author creates skill directory: quant_current_scope/skills/my-skill/
2. Author writes skill.yaml (name, version, description, steps)
3. Author writes guardrails.yaml (gates, failure_handling)
4. Author writes eval.yaml (benchmark requirements)
5. Author creates examples/ (usage examples)
```

**Authoring Authority**: Internal team only for Phase 5. Community contributions in Phase 6.

---

### Phase 2: Review & Approval
```
1. PM/CEO reviews skill:
   - Does skill weaken kernel guardrails? (REJECT if yes)
   - Does skill bypass truth gates? (REJECT if yes)
   - Does skill add value without risk? (APPROVE if yes)
   - Does skill meet benchmark requirements? (check eval.yaml)
2. PM/CEO records approval in decision log.md:
   - Decision ID (e.g., D5.1.5)
   - Skill name and version
   - Approval rationale
   - Impact scope (which projects/tasks affected)
3. Skill added to extension allowlist
```

**Approval Authority**:
- **PM alone**: Can approve LOW-risk skills (no kernel changes, additive only, limited scope)
- **CEO required**: MEDIUM/HIGH-risk skills (kernel interactions, broad scope, security implications)
- **Both required**: Skills that modify approval routing or policy feedback loops

**Risk Classification**:
- **LOW**: Declarative patterns, no code execution, narrow scope (e.g., react-component)
- **MEDIUM**: Broader scope, multiple projects affected (e.g., api-endpoint)
- **HIGH**: Kernel interactions, security implications, approval routing changes (e.g., safe-db-migration)

**Approval Criteria**:
- **MUST NOT** weaken kernel guardrails
- **MUST NOT** bypass truth gates or closure validation
- **MUST NOT** override PM/CEO/Auditor authority
- **MUST** have clear value proposition
- **MUST** meet benchmark requirements (if applicable)

**Interim Rule for Benchmark Requirements**:
- Until benchmark harness is operational (Phase 5A.1+), eval.yaml is declarative only (documents intended requirements but not enforced)
- Skills requiring benchmark validation must include benchmark-waiver entry in decision log.md explaining why approval proceeds without benchmark evidence
- After benchmark harness is operational, new skills must pass benchmark requirements before approval

---

### Phase 3: Allowlist Registration
```
1. Add skill to global allowlist: quant_current_scope/extension_allowlist.yaml
2. Allowlist entry includes:
   - skill_name: safe-db-migration
   - version: 1.0.0
   - approved_by: PM/CEO
   - approval_decision_id: D5.1.5
   - approval_date: 2026-03-15
   - status: active | deprecated | disabled
```

**Allowlist Schema**:
```yaml
# quant_current_scope/extension_allowlist.yaml
schema_version: "1.0.0"
last_updated: "2026-03-15"

skills:
  - skill_name: safe-db-migration
    version: 1.0.0
    approved_by: PM/CEO
    approval_decision_id: D5.1.5
    approval_date: 2026-03-15
    status: active
    risk_level: HIGH
    applicable_projects: ["all"]  # or specific project list

  - skill_name: react-component
    version: 1.0.0
    approved_by: PM
    approval_decision_id: D5.1.6
    approval_date: 2026-03-16
    status: active
    risk_level: LOW
    applicable_projects: ["frontend-only"]

  - skill_name: legacy-skill
    version: 0.9.0
    approved_by: PM
    approval_decision_id: D5.1.1
    approval_date: 2026-03-10
    status: deprecated
    risk_level: LOW
    deprecation_reason: "Superseded by safe-db-migration v1.0.0"
    removal_date: "2026-06-01"
```

**Required Fields**:
- `skill_name`: Unique identifier
- `version`: Semantic version (major.minor.patch)
- `approved_by`: PM | CEO | PM/CEO
- `approval_decision_id`: Reference to decision log.md entry
- `approval_date`: ISO date
- `status`: active | deprecated | disabled
- `risk_level`: LOW | MEDIUM | HIGH (determines approval authority)
- `applicable_projects`: List of project names or ["all"]

**Allowlist Authority**: Only PM/CEO can modify allowlist. Changes require decision log entry.

---

### Phase 4: Project-Local Activation
```
1. Project config (.sop_config.yaml) declares active skills:
   active_skills:
     - safe-db-migration
     - zero-downtime-deploy
2. Kernel validates at startup:
   - Is skill in global allowlist? (REJECT if no)
   - Is skill status=active? (REJECT if deprecated/disabled)
   - Is project in applicable_projects? (REJECT if not applicable)
3. If validation passes, skill is loaded for this project
```

**Project Config Schema**:
```yaml
# quant_current_scope/.sop_config.yaml (project-local)
project_name: "production-api"
guardrail_strength: "tight"
active_skills:
  - safe-db-migration  # Must be in global allowlist
  - zero-downtime-deploy
disabled_skills:
  - react-component  # Explicitly disabled for this project
```

**Validation Rules**:
- Project can only activate skills from global allowlist
- Project cannot activate deprecated/disabled skills
- Project cannot activate skills not applicable to it
- Project config changes require PM/CEO approval (recorded in decision log.md)

---

### Phase 5: Runtime Loading
```
1. Kernel reads .sop_config.yaml at startup
2. Kernel validates each active_skill against allowlist
3. Kernel loads skill definitions (skill.yaml, guardrails.yaml, eval.yaml)
4. Kernel merges skill guardrails with kernel guardrails (kernel is floor)
5. Skill is now available for use in this project
```

**Loading Sequence**:
```python
def load_extensions(project_config_path, allowlist_path):
    """
    Load extensions for project.
    Kernel enforces allowlist and validation.
    """
    project_config = load_yaml(project_config_path)
    allowlist = load_yaml(allowlist_path)

    loaded_skills = []

    for skill_name in project_config.active_skills:
        # Validate against allowlist
        allowlist_entry = find_in_allowlist(skill_name, allowlist)

        if not allowlist_entry:
            raise ExtensionNotAllowed(
                f"Skill {skill_name} not in global allowlist"
            )

        if allowlist_entry.status != "active":
            raise ExtensionNotActive(
                f"Skill {skill_name} status is {allowlist_entry.status}"
            )

        if not is_applicable(project_config.project_name, allowlist_entry):
            raise ExtensionNotApplicable(
                f"Skill {skill_name} not applicable to {project_config.project_name}"
            )

        # Load skill definition
        skill = load_skill(skill_name, allowlist_entry.version)

        # Validate skill does not weaken kernel
        validate_guardrails(skill.guardrails, kernel_guardrails)

        # Merge guardrails (kernel is floor)
        merged_guardrails = merge_guardrails(kernel_guardrails, skill.guardrails)

        loaded_skills.append({
            "skill": skill,
            "guardrails": merged_guardrails
        })

    return loaded_skills
```

---

## Security & Safety Mechanisms

### 1. No Dynamic Code Execution
**Rule**: Skills are declarative YAML, not executable code.

**Rationale**: Prevents arbitrary code execution. Skills define **what** to do (steps, gates), kernel defines **how** to execute.

**Example**:
```yaml
# ALLOWED: Declarative steps
steps:
  - analyze_schema_change
  - generate_rollback_script
  - validate_data_integrity

# REJECTED: Executable code
steps:
  - exec: "rm -rf /"  # Not allowed
```

**Enforcement**: Skill loader only reads YAML. No eval(), exec(), or dynamic imports.

---

### 2. Guardrail Floor Enforcement
**Rule**: Skills can only add gates, never remove kernel gates.

**Example**:
```python
def validate_guardrails(skill_guardrails, kernel_guardrails):
    """
    Validate skill does not weaken kernel.
    Kernel is floor, skill can only add.
    """
    for gate in kernel_guardrails:
        if gate.required and not skill_has_gate(skill_guardrails, gate):
            raise GuardrailViolation(
                f"Skill removes required kernel gate: {gate.name}"
            )

        if gate.threshold and skill_weakens_threshold(skill_guardrails, gate):
            raise GuardrailViolation(
                f"Skill weakens kernel threshold: {gate.name}"
            )
```

---

### 3. Version Pinning
**Rule**: Allowlist specifies exact version. No "latest" or wildcard versions.

**Rationale**: Prevents silent behavior changes. Skill updates require new approval.

**Example**:
```yaml
# ALLOWED: Exact version
- skill_name: safe-db-migration
  version: 1.0.0

# REJECTED: Wildcard version
- skill_name: safe-db-migration
  version: 1.*  # Not allowed
```

**Upgrade Process**:
1. Author releases safe-db-migration v1.1.0
2. PM/CEO reviews changes
3. If approved, add new allowlist entry for v1.1.0
4. Projects can opt-in to v1.1.0 via .sop_config.yaml update
5. Old v1.0.0 remains available until deprecated

---

### 4. Deprecation & Removal Policy
**Rule**: Deprecated skills remain available for 90 days, then removed.

**Deprecation Process**:
```
1. PM/CEO decides to deprecate skill (e.g., superseded by better version)
2. Update allowlist:
   - status: active → deprecated
   - deprecation_reason: "Superseded by v2.0.0"
   - removal_date: "2026-06-01" (90 days from now)
3. Record deprecation in decision log.md
4. Notify projects using deprecated skill
5. After removal_date, skill is removed from allowlist
6. Projects using removed skill will fail validation at next startup
```

**Grace Period**: 90 days allows projects to migrate without breaking.

---

### 5. Emergency Disable
**Rule**: PM/CEO can immediately disable skill if security issue discovered.

**Emergency Disable Process**:
```
1. Security issue discovered in skill (e.g., bypass found)
2. PM/CEO updates allowlist:
   - status: active → disabled
   - disable_reason: "Security issue: CVE-2026-1234"
3. Record emergency disable in decision log.md
4. All projects using disabled skill will fail validation at next startup
5. Projects must remove disabled skill from .sop_config.yaml
6. After fix, skill can be re-approved with new version
```

**No Grace Period**: Security issues require immediate action.

---

## Skill Discovery & Documentation

### 1. Skill Registry
**Location**: `quant_current_scope/skills/registry.yaml`

**Purpose**: Human-readable catalog of all available skills.

**Schema**:
```yaml
# quant_current_scope/skills/registry.yaml
schema_version: "1.0.0"
last_updated: "2026-03-15"

skills:
  - name: safe-db-migration
    version: 1.0.0
    category: database
    description: "Execute database schema changes with rollback plan and zero data loss"
    author: "Internal Team"
    approval_status: active
    approval_decision_id: D5.1.5
    documentation: "skills/safe_db_migration/README.md"
    examples:
      - "skills/safe_db_migration/examples/postgres_add_column.md"
      - "skills/safe_db_migration/examples/mysql_add_index.md"

  - name: react-component
    version: 1.0.0
    category: frontend
    description: "Create React functional components with hooks and TypeScript"
    author: "Internal Team"
    approval_status: active
    approval_decision_id: D5.1.6
    documentation: "skills/react_component/README.md"
    examples:
      - "skills/react_component/examples/functional_component.md"
```

**Usage**: Operators can browse registry to discover available skills.

---

### 2. Skill Documentation Standard
**Required Files**:
- `README.md`: Overview, usage, examples
- `skill.yaml`: Formal definition
- `guardrails.yaml`: Gates and failure handling
- `eval.yaml`: Benchmark requirements
- `examples/`: Real-world usage examples

**Documentation Template**:
```markdown
# Skill: safe-db-migration

## Overview
Execute database schema changes with rollback plan and zero data loss.

## When to Use
- Adding/removing columns
- Creating/dropping indexes
- Modifying constraints
- Data migrations

## Guardrails
- Requires rollback plan
- Requires backup verification
- Requires test coverage ≥80%
- Requires auditor review
- Requires CEO GO signal for production

## Benchmark Requirements
- sql_accuracy ≥ 0.70 (model must be competent at SQL)
- reasoning_depth ≥ 0.80 (model must understand data integrity)

## Examples
See examples/ directory for:
- PostgreSQL: Add column with default value
- MySQL: Add index without locking table
- SQL Server: Migrate data between tables
```

---

## Extension Allowlist Management

### 1. Allowlist Update Process
**Who**: PM/CEO only
**When**: After skill approval or status change
**How**: Direct edit of `extension_allowlist.yaml` + decision log entry

**Update Template**:
```markdown
### D5.1.X - Add/Update/Remove Skill: [skill-name]
**Date**: 2026-03-XX
**Type**: Extension Allowlist Update
**Status**: Approved
**Approver**: PM/CEO
**Context**: [Why this change]
**Decision**: [Add/update/remove skill-name v1.0.0]
**Impact**: [Which projects affected]
**Rationale**: [Why approved/deprecated/disabled]
**References**: quant_current_scope/skills/[skill-name]/
```

---

### 2. Allowlist Validation
**Automated Check**: Run on every startup and before skill loading.

**Validation Script**: `quant_current_scope/scripts/validate_extension_allowlist.py`

**Checks**:
- Schema version is current
- All skills have required fields (name, version, approved_by, approval_decision_id, status)
- All approval_decision_ids exist in decision log.md
- No duplicate skill entries (name + version must be unique)
- Deprecated skills have removal_date
- Disabled skills have disable_reason
- All skill directories exist in skills/

**Failure Behavior**: If validation fails, startup is blocked. Operator must fix allowlist.

---

### 3. Allowlist Audit Trail
**Requirement**: All allowlist changes tracked in git history + decision log.

**Git Commit Message Template**:
```
Extension allowlist: Add safe-db-migration v1.0.0

Approval: D5.1.5 (PM/CEO, 2026-03-15)
Rationale: Enables safe database schema changes with rollback plan
Impact: All projects with database changes

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```

---

## Open Questions for PM/CEO

1. **Skill authoring delegation**: Can PM approve LOW-risk skills without CEO, or always require both?
   - Recommendation: PM can approve LOW-risk, CEO required for MEDIUM/HIGH-risk

2. **Community contributions**: Phase 6 goal, but what approval process?
   - Recommendation: External skills require security review + PM/CEO approval + 30-day probation period

3. **Skill versioning policy**: Semantic versioning (major.minor.patch)?
   - Recommendation: Yes, use semver. Breaking changes require new major version + new approval.

4. **Allowlist location**: Global (quant_current_scope/) or per-project?
   - Recommendation: Global allowlist (approved skills), per-project activation (.sop_config.yaml)

5. **Skill testing requirements**: Must skills have automated tests?
   - Recommendation: Yes, skills with code must have tests. Declarative-only skills need examples.

---

## Next Steps

1. PM/CEO review and approve this ADR
2. Record approval in `quant_current_scope/docs/decision log.md`
3. Proceed to ADR-004: Benchmark → Policy Feedback Loop
4. After all 5A.0 ADRs approved, decide: implement or continue spec work

---

**Status**: Awaiting PM/CEO approval
