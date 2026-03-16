# Operating Principles - Core Commandments

**Purpose**: Define the foundational rules that govern all work in the control plane.

## 1. Docs-as-Code

**Principle**: If behavior changes, update docs (PRD and product spec) and decision log in the same milestone.

**Rationale**: Documentation drift creates confusion, onboarding friction, and debugging overhead. Docs must stay synchronized with code.

**Implementation**:
- Code change → doc update in same commit/PR
- New feature → update phase brief + decision log
- Bug fix → update lessons learned if pattern emerges
- Architecture change → update AGENTS.md or workflow_wiring_detailed.md

**For Explicit Formulas**:
- Document the explicit formula in comments where used
- Reference the `.py` file location in `docs/notes.md`
- Include formula derivation if non-obvious

**Examples**:
- Add new skill → update `.codex/skills/README.md` + `docs/workflow_wiring_detailed.md`
- Change validation logic → update validator docstring + `docs/definition_of_done.md`
- Modify workflow weights → update phase brief template + decision log entry

**Enforcement**: Definition of Done includes "Docs updated".

---

## 2. Atomic Safety

**Principle**: Critical data writes must be atomic (temp → replace).

**Rationale**: Partial writes corrupt state. Atomic operations ensure all-or-nothing semantics.

**Implementation**:
```python
# Write to temp file first
temp_path = f"{target_path}.tmp"
with open(temp_path, 'w') as f:
    json.dump(data, f, indent=2)

# Atomic replace
os.replace(temp_path, target_path)
```

**Critical Files** (must use atomic writes):
- `docs/context/*_latest.json`
- `docs/context/*_latest.md`
- `docs/evidence/<phase>/*.json`
- Any file read by multiple processes

**Non-Critical Files** (direct write acceptable):
- Log files
- Temporary debug output
- Test fixtures

**Enforcement**: Code review checks for atomic write pattern on critical files.

---

## 3. Top-Down Delivery

**Principle**: Spec → Interface → Implementation → Test.

**Rationale**: Top-down prevents rework. Bottom-up leads to misaligned implementations.

**Workflow**:
1. **Spec**: Write phase brief with acceptance criteria
2. **Interface**: Define artifact contracts (JSON schema, Markdown template)
3. **Implementation**: Write code that produces/consumes artifacts
4. **Test**: Validate against acceptance criteria

**Example**:
```
Phase Brief: "Add workflow status aggregation"
    ↓
Interface: Define workflow_status_latest.json schema
    ↓
Implementation: Write workflow-status skill
    ↓
Test: Validate JSON output matches schema
```

**Anti-Pattern**:
- Writing code before defining acceptance criteria
- Implementing features not in phase brief
- Testing without clear success criteria

**Enforcement**: Milestone review gate checks for spec-first approach.

---

## 4. Defense in Depth

**Principle**: Assume API failures and NaN-heavy data; fail gracefully.

**Rationale**: External systems fail. Data is messy. Defensive code prevents cascading failures.

**Implementation**:

### API Calls
```python
try:
    response = api_client.fetch_data()
    if response.status_code != 200:
        logger.error(f"API error: {response.status_code}")
        return fallback_value
except RequestException as e:
    logger.error(f"API failure: {e}")
    return fallback_value
```

### Data Validation
```python
# Check for NaN/None before operations
if pd.isna(value) or value is None:
    logger.warning(f"Invalid value: {value}")
    return default_value

# Validate ranges
if not (0 <= score <= 100):
    logger.error(f"Score out of range: {score}")
    return None
```

### Graceful Degradation
- Missing optional data → use defaults, log warning
- Missing required data → fail fast with clear error
- Partial results → return what's available, flag incomplete

**Enforcement**: Code review checks for error handling on external calls and data operations.

---

## 5. Subagent-First

**Principle**: Default to subagents for non-trivial work (multi-file changes, ETL, strategy logic, runtime/ops risk paths).

**Rationale**: Subagents provide isolation, parallelization, and context protection. Main agent stays focused on orchestration.

**When to Use Subagents**:
- Multi-file changes (> 3 files)
- ETL pipelines (data extraction, transformation, loading)
- Strategy logic (backtesting, scoring, ranking)
- Runtime/ops risk paths (deployment, migration, rollback)
- Research tasks (literature review, claim validation)
- Code review (architecture, quality, tests, performance)

**When NOT to Use Subagents**:
- Single-file edits
- Simple script execution
- Reading files
- Running validators

**Subagent Types**:
- `general-purpose`: Multi-step tasks, file search
- `Explore`: Codebase exploration, keyword search
- `Plan`: Implementation planning, architecture design

**Enforcement**: Milestone review gate checks for appropriate subagent usage.

---

## 6. Guardrailed Delegation

**Principle**: Each subagent must have bounded scope (owned files/tasks), explicit acceptance checks, and no destructive operations without user confirmation.

**Rationale**: Unbounded subagents cause scope creep, unintended changes, and data loss.

**Subagent Contract**:
1. **Bounded Scope**: List owned files/directories
2. **Acceptance Checks**: Define success criteria
3. **Destructive Operations**: Require user confirmation
4. **Output Contract**: Specify expected artifacts

**Example**:
```markdown
Subagent: Implementer A
Scope: scripts/run_loop_cycle.py, tests/unit/test_run_loop_cycle.py
Acceptance: Tests pass, exit codes correct
Destructive Ops: None
Output: Updated script + test file
```

**Anti-Pattern**:
- Subagent modifies files outside scope
- No acceptance criteria defined
- Destructive operations without confirmation

**Enforcement**: Subagent prompt includes scope + acceptance checks.

---

## 7. Review Gated

**Principle**: No milestone is done without subagent review (Section 5 of AGENTS.md).

**Rationale**: Self-review misses issues. Independent review catches bugs, architecture flaws, and test gaps.

**Review Types**:
- **Architecture Review**: Design patterns, coupling, extensibility
- **Code Quality Review**: Readability, maintainability, complexity
- **Test Review**: Coverage, edge cases, integration tests
- **Performance Review**: Bottlenecks, resource usage, scalability

**Review Workflow**:
1. Implementation complete
2. Spawn reviewer subagent with review prompt
3. Reviewer emits findings with severity (CRITICAL/HIGH/MEDIUM/LOW)
4. Address CRITICAL/HIGH findings
5. Document MEDIUM/LOW findings for future work
6. Milestone closure

**Enforcement**: Definition of Done includes "Milestone review gate passes".

---

## 8. Self-Learning

**Principle**: After each work/review round, record mistakes, root causes, and guardrails in `docs/lessonss.md`.

**Rationale**: Repeated mistakes waste time. Learning loops prevent recurrence.

**Lesson Format**:
```markdown
## Lesson: <Short Title>
**Date**: YYYY-MM-DD
**Phase**: <Phase ID>
**Mistake**: <What went wrong>
**Root Cause**: <Why it happened>
**Guardrail**: <How to prevent>
**Status**: Active/Resolved
```

**When to Record**:
- Bug introduced and caught in review
- Test failure due to missing edge case
- Architecture decision that caused rework
- Process violation (e.g., skipped docs update)

**Review Cadence**:
- Weekly: Review active lessons, update status
- Monthly: Archive resolved lessons, identify patterns

**Enforcement**: SAW protocol includes lessons learned check.

---

## Summary

| Principle | Key Action | Enforcement |
|-----------|-----------|-------------|
| Docs-as-Code | Update docs with code changes | DoD checklist |
| Atomic Safety | Use temp → replace for critical writes | Code review |
| Top-Down Delivery | Spec before implementation | Milestone gate |
| Defense in Depth | Handle errors gracefully | Code review |
| Subagent-First | Delegate non-trivial work | Milestone gate |
| Guardrailed Delegation | Bound scope + acceptance checks | Subagent prompt |
| Review Gated | Independent review before closure | DoD checklist |
| Self-Learning | Record mistakes + guardrails | SAW protocol |

These principles are non-negotiable. Violations require explicit approval and decision log entry.
