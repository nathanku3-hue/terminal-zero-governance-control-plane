---
name: quick-gate
description: Fast validation gate for common checks (schema version, test pass/fail, file existence). Use before committing or deploying.
---

# Quick-Gate Skill

Perform fast validation checks before proceeding with risky operations.

## 0. Activation Triggers
- Before git commit/push
- Before deployment or release
- User says "validate", "check before commit", "run gates"
- Project-guider routes pre-commit checks here

## 1. Standard Gate Checks
Run all applicable checks:

### Schema Version Check
- Scan for schema_version fields in JSON/YAML
- Verify all match expected version (default: v2.0.0)
- Exit code 2 if version mismatch

### Test Suite Check
- Run test suite if tests/ directory exists
- Parse test results for pass/fail counts
- Exit code 1 if any tests fail

### File Existence Check
- Verify all evidence paths from phase brief exist
- Check for required artifacts (project_init, workflow_status)
- Exit code 2 if required files missing

### Workflow Weight Check
- If phase brief exists, validate workflow weight sums to 100%
- Exit code 1 if weight mismatch

### Git Status Check
- Check for uncommitted changes
- Check for untracked files that should be tracked
- Warn if working directory is dirty

## 2. Execution Flow
1. Identify applicable checks based on context
2. Run checks in parallel where possible
3. Aggregate results
4. Emit summary with pass/fail counts

## 3. Output Contract
1. Emit check results:
   ```
   QuickGate Results:
   - Schema Version: PASS (all v2.0.0)
   - Test Suite: PASS (51/51 tests)
   - File Existence: PASS (all evidence found)
   - Workflow Weight: PASS (100%)
   - Git Status: WARN (3 untracked files)

   Overall: PASS (1 warning)
   ```
2. If any check fails, emit:
   - `QuickGate: BLOCK`
   - List failing checks with details
   - Suggest remediation actions
3. If all pass:
   - `QuickGate: PASS`
   - Safe to proceed

## 4. Exit Codes
- 0: All checks pass
- 1: Validation failures (fixable)
- 2: Infrastructure errors (missing files, invalid JSON)

## 5. Model Routing
Use `codex-5.2` model for fast execution.
