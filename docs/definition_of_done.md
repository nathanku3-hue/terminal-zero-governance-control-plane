# Definition of Done - Completion Checklist

**Purpose**: Define what "done" means for any task, feature, or milestone in the control plane.

## Core Principle

A task is NOT done until it's proven to work, documented, and reviewed. Code changes alone are insufficient.

## DoD Checklist

### 1. Code Implementation
- [ ] Acceptance criteria from phase brief are met
- [ ] Code follows project conventions and style
- [ ] Error handling implemented (defense in depth)
- [ ] Atomic writes used for critical files
- [ ] No forbidden patterns (SQLite, Flask, Django, ORMs) without approval
- [ ] Dependencies added to `pyproject.toml` if needed
- [ ] Code is readable and maintainable

**Incomplete Status Rule**: A task remains `Incomplete` if proof it works is missing, even when code changes are finished.

---

### 2. Tests Pass
- [ ] Unit tests written for new code
- [ ] Integration tests updated if needed
- [ ] All tests pass: `pytest` (record count + date)
- [ ] Smoke checks pass for affected scripts
- [ ] No regressions in existing functionality

**Test Coverage Requirements**:
- New functions: unit tests required
- New scripts: smoke test (`--help` flag works)
- Modified validators: contract tests updated

**Evidence**: Include pytest output with pass count, run date, and Python interpreter used.

---

### 3. Documentation Updated
- [ ] Phase brief updated if scope changed
- [ ] Decision log entry added if significant decision made
- [ ] Code comments added for non-obvious logic
- [ ] Docstrings updated for modified functions
- [ ] README.md updated if new skill/feature added
- [ ] Workflow wiring updated if integration points changed

**Docs-as-Code Rule**: Behavior changes require doc updates in the same milestone.

**Key Docs to Check**:
- `AGENTS.md` - If workflow/entrypoints changed
- `.codex/skills/README.md` - If skills added/modified
- `docs/workflow_wiring_detailed.md` - If integration changed
- `docs/decision_log.md` - If architectural decision made
- `docs/lessonss.md` - If mistake pattern emerged

---

### 4. Milestone Review Gate Passes
- [ ] Reviewer subagents spawned (Section 5 of AGENTS.md)
- [ ] Risk tier checks completed:
  - **Low**: Touched-module unit tests + static checks
  - **Medium**: Low + integration/smoke checks
  - **High**: Medium + data integrity checks + rollback note
  - **Critical**: High + dry-run evidence + explicit user sign-off
- [ ] Review findings addressed or explicitly deferred
- [ ] No blocking issues remain

**Reviewer Mapping** (from Section 12 of AGENTS.md):
- Architecture review
- Code quality review
- Test coverage review
- Performance review

---

### 5. Operational Impact Documented
- [ ] Deployment steps documented (if applicable)
- [ ] Rollback path documented (if risky change)
- [ ] Performance impact assessed (if data/compute intensive)
- [ ] Breaking changes flagged (if API/contract changed)
- [ ] Migration steps documented (if schema changed)

**Operational Checklist**:
- What changes in production behavior?
- What could go wrong?
- How do we roll back?
- What monitoring/alerts are needed?

---

### 6. Evidence Footer Included
- [ ] Observability rating (1-5 scale)
- [ ] Evidence paths listed
- [ ] Validation results included
- [ ] Run metadata recorded (date, interpreter, test count)

**Evidence Footer Template**:
```markdown
## Evidence Footer
**Observability**: 4/5
**Evidence Paths**:
- docs/evidence/phase24c/saw_report_001.json
- docs/evidence/phase24c/se_evidence_002.json

**Validation Results**:
- SAWBlockValidation: PASS
- EvidenceValidation: PASS
- QuickGate: PASS (51/51 tests)

**Run Metadata**:
- Date: 2026-03-16
- Python: 3.12.1 (.venv/bin/python)
- Test Count: 308 passed
```

---

### 7. Artifacts Generated
- [ ] Required artifacts created (per phase brief)
- [ ] Artifacts validate against schema
- [ ] Artifacts stored in correct location
- [ ] Artifact paths referenced in phase brief

**Artifact Locations**:
- Context: `docs/context/*_latest.{json,md}`
- Evidence: `docs/evidence/<phase>/*.json`
- Reports: `docs/context/*_report_latest.md`

---

### 8. Validation Tokens Emitted
- [ ] Skill validators run (if applicable)
- [ ] Validation tokens emitted: PASS/BLOCK/DRIFT/INSUFFICIENT
- [ ] Blocking issues resolved if BLOCK status
- [ ] Drift documented if DRIFT status

**Validator Mapping**:
- `$saw` → `validate_saw_report_blocks.py` → SAWBlockValidation: PASS/BLOCK
- `$research-analysis` → `validate_research_claims.py` → ClaimValidation: PASS/BLOCK
- `$se-executor` → `validate_se_evidence.py` → EvidenceValidation: PASS/BLOCK
- `$architect-review` → `validate_architect_calibration.py` → CalibrationValidation: PASS/DRIFT/INSUFFICIENT
- `$quick-gate` → Multiple validators → QuickGate: PASS/BLOCK

---

## Risk-Tier Specific Requirements

### Low Risk (Single-file edit, no external dependencies)
- Unit tests for touched module
- Static checks (linting, type hints)
- Code review

### Medium Risk (Multi-file changes, new features)
- Low risk requirements +
- Integration tests
- Smoke checks for affected workflows
- Documentation updates

### High Risk (Data operations, schema changes, critical paths)
- Medium risk requirements +
- Data integrity checks (atomic writes, row counts, sanity assertions)
- Rollback procedure documented
- Performance impact assessed

### Critical Risk (Production-impacting, irreversible operations)
- High risk requirements +
- Dry-run evidence with sample data
- Explicit user sign-off before execution
- Monitoring/alerting plan
- Incident response plan

---

## Common DoD Failures

### "Code is done but tests fail"
❌ NOT DONE. Fix tests or fix code.

### "Code works but docs not updated"
❌ NOT DONE. Update docs in same milestone.

### "Tests pass but no evidence footer"
❌ NOT DONE. Add evidence footer with validation results.

### "Feature complete but no review"
❌ NOT DONE. Run milestone review gate.

### "Everything works but rollback not documented"
❌ NOT DONE (if high/critical risk). Document rollback path.

---

## DoD Verification

### Self-Check
1. Read phase brief acceptance criteria
2. Verify each criterion is met
3. Check all DoD checklist items
4. Run validators and record results
5. Generate evidence footer

### Peer Review
1. Spawn reviewer subagents
2. Address findings
3. Re-run validators if code changed
4. Update evidence footer

### User Acceptance
1. Demo functionality to user
2. Confirm acceptance criteria met
3. Get explicit sign-off for critical changes
4. Close milestone

---

## DoD Enforcement

**Pre-Commit**: Run `$quick-gate` to catch common issues early.

**Pre-Merge**: Milestone review gate must pass.

**Pre-Deploy**: Auditor review must pass (shadow or enforce mode).

**Post-Deploy**: Monitor for issues, update lessons learned if problems emerge.
