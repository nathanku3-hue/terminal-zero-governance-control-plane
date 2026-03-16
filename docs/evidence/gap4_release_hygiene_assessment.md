# Gap #4: Release Hygiene Assessment for Phase 24C Beta

**Date**: 2026-03-16
**Objective**: Assess worktree cleanliness and prepare for beta candidate tag
**Target**: Clean commit suitable for `phase24c-beta-1` tag

---

## Current Worktree Status

### Modified Files (38 files)
**Category: Core Skills**
- `.codex/skills/README.md`
- `.codex/skills/architect-review/agents/openai.yaml`
- `.codex/skills/research-analysis/SKILL.md`
- `.codex/skills/research-analysis/agents/openai.yaml`
- `.codex/skills/saw/SKILL.md`
- `.codex/skills/saw/agents/openai.yaml`
- `.codex/skills/se-executor/agents/openai.yaml`

**Category: Navigation & Documentation**
- `AGENTS.md`
- `OPERATOR_LOOP_GUIDE.md`
- `README.md`
- `docs/ARTIFACT_POLICY.md`

**Category: Context Artifacts (Authoritative)**
- `docs/context/auditor_calibration_report.json`
- `docs/context/auditor_calibration_report.md`
- `docs/context/auditor_findings.json`
- `docs/context/auditor_fp_ledger.json`
- `docs/context/auditor_promotion_dossier.json`
- `docs/context/auditor_promotion_dossier.md`
- `docs/context/ceo_bridge_digest.md`
- `docs/context/ceo_go_signal.md`
- `docs/context/current_context.json`
- `docs/context/current_context.md`
- `docs/context/worker_status_aggregate.json`

**Category: Handover & Traceability**
- `docs/handover/gemini/phase24_gemini_handover.md`
- `docs/pm_to_code_traceability.yaml`
- `docs/runbook_ops.md`

**Category: Build Configuration**
- `pyproject.toml`
- `.gitignore`

**Category: Scripts (Loop Cycle Refactor)**
- `scripts/loop_cycle_artifacts.py`
- `scripts/loop_cycle_runtime.py`
- `scripts/phase_end_handover.ps1`
- `scripts/print_takeover_entrypoint.py`
- `scripts/run_fast_checks.py`
- `scripts/validate_round_contract_checks.py`

**Category: Tests**
- `tests/test_loop_cycle_artifacts.py`
- `tests/test_print_takeover_entrypoint.py`
- `tests/test_run_fast_checks.py`
- `tests/test_validate_round_contract_checks.py`

### Untracked Files (94 files/directories)

**Category: New Skills (Phase 24C Deliverables)**
- `.codex/skills/_shared/confidence-gate/`
- `.codex/skills/_shared/hierarchy-init/`
- `.codex/skills/_shared/role-injection/`
- `.codex/skills/_shared/scripts/validate_workflow_status.py`
- `.codex/skills/_shared/field_templates/software_engineering.md`
- `.codex/skills/context-bootstrap/agents/`
- `.codex/skills/doc-draft/`
- `.codex/skills/expert-researcher/`
- `.codex/skills/project-guider/`
- `.codex/skills/quick-gate/`
- `.codex/skills/web-search/`
- `.codex/skills/workflow-status/`

**Category: Configuration Files**
- `.sop_config.yaml`
- `extension_allowlist.yaml`
- `skills/registry.yaml`

**Category: Documentation (Phase 24C)**
- `docs/agents_md_refactor_complete.md`
- `docs/definition_of_done.md`
- `docs/directory_structure.md`
- `docs/operating_principles.md`
- `docs/operator_reference.md`
- `docs/tech_stack.md`
- `docs/workflow_wiring_detailed.md`
- `docs/next_phase_plan.md`

**Category: Evidence & Decisions**
- `docs/evidence/` (directory - contains gap closure evidence)
- `docs/decisions/` (directory)

**Category: Templates**
- `docs/templates/phase_brief_template.md`
- `docs/templates/plan_snapshot.txt`
- `docs/phase_brief/phase24c-brief-workflow.md`

**Category: Phase End Logs (Timestamped Artifacts)**
- `docs/context/phase_end_logs/` (20+ log files from 2026-03-15 runs)

**Category: Benchmark & Validation**
- `benchmark/` (directory)
- `scripts/measure_context_reduction.py`
- `scripts/run_baseline_benchmark.py`
- `scripts/test_policy_proposal.py`
- `scripts/validate_baseline.py`
- `scripts/validate_extension_allowlist.py`
- `scripts/validate_routing_matrix.py`
- `scripts/validate_skill_activation.py`
- `scripts/validate_skill_manifest.py`
- `scripts/validate_skill_registry.py`
- `scripts/utils/path_validator.py`
- `scripts/utils/skill_resolver.py`

**Category: Skill Infrastructure (Deferred Scope)**
- `skills/safe_db_migration/`
- `skills/schemas/`

**Category: Tests (New)**
- `tests/test_phase5_benchmark.py`
- `tests/test_skill_activation.py`
- `tests/test_skill_infrastructure.py`
- `tests/test_subagent_routing.py`

**Category: Working Documents**
- `agents_md_refactor_proposal.md`
- `skill_system_status.md`
- `test_workflow_integration.md`
- `tier1_skills_implementation_complete.md`
- `docs/archive/legacy_quant_runbook.md`
- `docs/context/w11_status.md`
- `docs/context/workflow_status_test.json`

---

## Release Hygiene Decision Matrix

### COMMIT (Phase 24C Deliverables)

**Core Skills & Navigation**
- ✓ All modified `.codex/skills/` files
- ✓ All new `.codex/skills/` directories (project-guider, workflow-status, etc.)
- ✓ AGENTS.md, README.md, OPERATOR_LOOP_GUIDE.md
- ✓ docs/ARTIFACT_POLICY.md

**Context Artifacts**
- ✓ All modified `docs/context/*.json` and `docs/context/*.md`
- ✓ docs/handover/gemini/phase24_gemini_handover.md
- ✓ docs/pm_to_code_traceability.yaml

**Scripts & Tests**
- ✓ All modified scripts/ files (loop cycle refactor)
- ✓ All modified tests/ files
- ✓ New validation scripts (validate_workflow_status.py, etc.)
- ✓ New test files (test_fresh_worker_navigation.py already committed)

**Documentation**
- ✓ docs/definition_of_done.md
- ✓ docs/directory_structure.md
- ✓ docs/operating_principles.md
- ✓ docs/tech_stack.md
- ✓ docs/workflow_wiring_detailed.md
- ✓ docs/phase_brief/phase24c-brief-workflow.md
- ✓ docs/templates/ (phase_brief_template.md)

**Evidence**
- ✓ docs/evidence/ (gap closure evidence)
- ✓ docs/path_validation_defects.md (already committed)
- ✓ references/phase_end_handover_template.md (already committed)
- ✓ docs/architect/profile_outcomes.csv (already committed)

**Configuration**
- ✓ pyproject.toml
- ✓ .gitignore

### IGNORE (Not Phase 24C Scope)

**Deferred Skill Infrastructure**
- ✗ skills/registry.yaml (deferred per phase24c_handover.md Section 7)
- ✗ skills/schemas/ (deferred)
- ✗ skills/safe_db_migration/ (deferred)
- ✗ .sop_config.yaml (deferred)
- ✗ extension_allowlist.yaml (deferred)
- ✗ scripts/validate_skill_registry.py (deferred)
- ✗ scripts/validate_skill_manifest.py (deferred)
- ✗ scripts/validate_extension_allowlist.py (deferred)
- ✗ tests/test_skill_infrastructure.py (deferred)

**Working Documents (Not Release Artifacts)**
- ✗ agents_md_refactor_proposal.md
- ✗ skill_system_status.md
- ✗ test_workflow_integration.md
- ✗ tier1_skills_implementation_complete.md
- ✗ docs/context/w11_status.md (working doc)
- ✗ docs/context/workflow_status_test.json (test artifact)
- ✗ docs/next_phase_plan.md (planning doc)

**Benchmark & Experimental**
- ✗ benchmark/ (experimental, not production)
- ✗ scripts/run_baseline_benchmark.py (experimental)
- ✗ scripts/measure_context_reduction.py (experimental)
- ✗ scripts/test_policy_proposal.py (experimental)
- ✗ scripts/validate_baseline.py (experimental)
- ✗ tests/test_phase5_benchmark.py (experimental)

**Phase End Logs (Timestamped, Not Source)**
- ✗ docs/context/phase_end_logs/ (operational logs, not source code)

**Archive**
- ✗ docs/archive/legacy_quant_runbook.md

### DECISION REQUIRED

**Routing & Validation Scripts**
- ? scripts/validate_routing_matrix.py
- ? scripts/validate_skill_activation.py
- ? scripts/utils/path_validator.py
- ? scripts/utils/skill_resolver.py
- ? tests/test_skill_activation.py
- ? tests/test_subagent_routing.py

**Rationale**: These may be part of the skill system infrastructure that was deferred, OR they may be validation utilities that support Phase 24C deliverables. Need to check if they're referenced by committed code.

**Operator Reference**
- ? docs/operator_reference.md

**Rationale**: May be a Phase 24C deliverable or a working document. Need to check if it's referenced in AGENTS.md or other committed docs.

**Decisions Directory**
- ? docs/decisions/

**Rationale**: May contain decision log entries. Need to check if this is the canonical decision log location or if it's docs/decision_log.md.

---

## Recommended Actions

### 1. Update .gitignore
Add patterns for deferred scope and working documents:
```
# Deferred skill infrastructure (Phase 24C scope freeze)
/skills/registry.yaml
/skills/schemas/
/skills/safe_db_migration/
/.sop_config.yaml
/extension_allowlist.yaml

# Working documents (not release artifacts)
agents_md_refactor_proposal.md
skill_system_status.md
test_workflow_integration.md
tier1_skills_implementation_complete.md
docs/next_phase_plan.md
docs/context/w11_status.md
docs/context/workflow_status_test.json

# Experimental/benchmark (not production)
/benchmark/
scripts/run_baseline_benchmark.py
scripts/measure_context_reduction.py
scripts/test_policy_proposal.py
scripts/validate_baseline.py
tests/test_phase5_benchmark.py

# Operational logs (timestamped, not source)
docs/context/phase_end_logs/

# Archive
docs/archive/
```

### 2. Stage Phase 24C Deliverables
```bash
# Modified files
git add .codex/skills/
git add AGENTS.md OPERATOR_LOOP_GUIDE.md README.md
git add docs/ARTIFACT_POLICY.md
git add docs/context/*.json docs/context/*.md
git add docs/handover/gemini/phase24_gemini_handover.md
git add docs/pm_to_code_traceability.yaml
git add docs/runbook_ops.md
git add pyproject.toml .gitignore
git add scripts/loop_cycle_*.py
git add scripts/phase_end_handover.ps1
git add scripts/print_takeover_entrypoint.py
git add scripts/run_fast_checks.py
git add scripts/validate_round_contract_checks.py
git add tests/test_loop_cycle_artifacts.py
git add tests/test_print_takeover_entrypoint.py
git add tests/test_run_fast_checks.py
git add tests/test_validate_round_contract_checks.py

# New documentation
git add docs/definition_of_done.md
git add docs/directory_structure.md
git add docs/operating_principles.md
git add docs/tech_stack.md
git add docs/workflow_wiring_detailed.md
git add docs/phase_brief/phase24c-brief-workflow.md
git add docs/templates/phase_brief_template.md

# Evidence
git add docs/evidence/
```

### 3. Commit with Phase 24C Message
```bash
git commit -m "feat(phase24c): complete beta deliverables

Phase 24C Beta Scope:
- Project-guider skill with workflow-status integration
- Workflow-status skill with red-status blocking
- Fresh worker navigation (AGENTS.md refactor)
- Loop cycle refactor (context/runtime/artifacts separation)
- Auditor calibration system (5 profile outcomes)
- Path validation defects resolved (D4, D5)
- Evidence collection for Gap #2 (Codex runtime flow)

Promotion Criteria Status:
- C0: PASS (0 failures)
- C1: PASS (D-174 recorded 2026-03-16)
- C2: PASS (60 >= 30 evidence items)
- C3: FAIL (1/2 qualifying weeks)
- C4: PASS (0.00% FP rate)
- C4b: PASS (100% annotation coverage)
- C5: PASS (v2.0.0 schema)

Test Status: 380 passing (validated 2026-03-16)

Deferred Scope (per phase24c_handover.md Section 7):
- Skill registry infrastructure
- Cross-repo readiness
- Enforce dry-run/canary/rollout
- Exec-memory truth mismatch resolution

Refs: docs/handover/phase24c_handover.md, docs/evidence/gap2_codex_runtime_demo.md"
```

### 4. Tag Beta Candidate
```bash
git tag -a phase24c-beta-1 -m "Phase 24C Beta 1

Promotion readiness: 6/7 criteria passing (C3 pending W11 completion)
Test suite: 380 passing
Fresh worker navigation: validated
Codex runtime flow: demonstrated

Next: W11 evidence collection, C3 closure, enforce dry-run"

git push origin phase24c-beta-1
```

---

## Verification Checklist

- [ ] All Phase 24C deliverables staged
- [ ] Deferred scope excluded from commit
- [ ] Working documents excluded from commit
- [ ] .gitignore updated
- [ ] Test suite passing (380 tests)
- [ ] Commit message references handover doc
- [ ] Tag message includes promotion status
- [ ] Worktree clean after commit (only ignored files remain)

---

## Open Questions

1. **Routing/validation scripts**: Are these Phase 24C deliverables or deferred infrastructure?
2. **docs/operator_reference.md**: Release artifact or working document?
3. **docs/decisions/**: Canonical decision log location?

**Recommendation**: Review these 3 items before final commit, or commit conservatively (exclude if uncertain) and add in a follow-up commit if needed.

---

## Next Steps After Beta Tag

1. Continue W11 evidence collection
2. Monitor C3 criterion (need 2nd qualifying week)
3. Prepare C1 signoff packet (already complete per D-174)
4. Plan enforce dry-run once C3 passes
5. Keep worktree clean for RC tag (phase24c-rc-1) after C3 closure
