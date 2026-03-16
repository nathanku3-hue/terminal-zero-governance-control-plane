# Workflow Wiring - Detailed Reference

**Purpose**: Deep-dive into how all system components connect and interact during a Codex worker session.

**Audience**: Fresh Codex workers, system architects, debugging complex integration issues.

## Session Lifecycle Overview

```
Fresh Worker Start
    ↓
Read AGENTS.md (navigation hub)
    ↓
Load .codex/skills/README.md (skill registry)
    ↓
User invokes /new or "start session"
    ↓
$project-guider activated (Section 0: Session Start)
    ↓
Load context: project_init_latest.md + exec_memory_packet_latest.json
    ↓
$workflow-status invoked (Section 2.5: Workflow Status Check)
    ↓
Aggregate phase status by workflow type
    ↓
Check overall_color: green/yellow/red
    ↓
If red → emit StatusAlert: BLOCKED, ask user to resolve or proceed
    ↓
Route to appropriate skill based on task type
    ↓
Execute skill workflow
    ↓
Emit validation tokens (PASS/BLOCK)
    ↓
Generate worker_reply_packet.json
    ↓
Run auditor review (shadow/enforce mode)
    ↓
SAW protocol (if applicable)
    ↓
Phase closure
```

## Skill Activation Matrix

| Skill | Trigger | Model | Validator | Output |
|-------|---------|-------|-----------|--------|
| saw | Workflow invoked | codex-5.4 | validate_saw_report_blocks.py | SAWBlockValidation: PASS/BLOCK |
| research-analysis | Workflow invoked | claude | validate_research_claims.py | ClaimValidation: PASS/BLOCK |
| se-executor | Trigger-based | codex-5.2 | validate_se_evidence.py | EvidenceValidation: PASS/BLOCK |
| architect-review | Trigger-based | claude | validate_architect_calibration.py | CalibrationValidation: PASS/DRIFT/INSUFFICIENT |
| project-guider | Session start | claude | N/A | Session routing |
| workflow-status | Via project-guider | claude | N/A | workflow_status_latest.json |
| context-bootstrap | /new bootstrap | codex-5.2 | N/A | exec_memory_packet_latest.json |
| expert-researcher | Confidence < 80 | claude | N/A | Expert guidance |
| web-search | External info needed | claude | N/A | Search results with citations |
| quick-gate | Pre-commit | codex-5.2 | Multiple validators | QuickGate: PASS/BLOCK |
| doc-draft | Doc creation | claude | Template validators | Draft + validation |

## Validation Chain

### Pre-Commit Validation ($quick-gate)
```
User: "commit this"
    ↓
$quick-gate activated
    ↓
Run parallel checks:
    - Schema version check (all v2.0.0?)
    - Test suite check (pytest pass?)
    - File existence check (evidence paths exist?)
    - Workflow weight check (sums to 100%?)
    - Git status check (dirty working dir?)
    ↓
Aggregate results
    ↓
Emit: QuickGate: PASS/BLOCK (with details)
    ↓
If PASS → safe to commit
If BLOCK → list failing checks + remediation
```

### Post-Work Validation (Skill Validators)
```
Skill execution complete
    ↓
Run skill-specific validator:
    - $saw → validate_saw_report_blocks.py
    - $research-analysis → validate_research_claims.py
    - $se-executor → validate_se_evidence.py
    - $architect-review → validate_architect_calibration.py
    ↓
Emit validation token: PASS/BLOCK/DRIFT/INSUFFICIENT
    ↓
If BLOCK → halt workflow, emit remediation guidance
If PASS → proceed to closure packet generation
```

### Phase-End Validation (Auditor)
```
worker_reply_packet.json generated
    ↓
scripts/run_auditor_review.py invoked
    ↓
Check schema_version (must be v2.0.0)
    ↓
Validate closure packet fields
    ↓
Check arithmetic: ChecksPassed + ChecksFailed = ChecksTotal
    ↓
If Verdict=BLOCK → require OpenRisks + NextAction
    ↓
Emit findings with severity: CRITICAL/HIGH/MEDIUM/LOW
    ↓
Shadow mode: log findings, non-blocking
Enforce mode: CRITICAL/HIGH block handover
    ↓
Update calibration data
```

## Artifact Flow

### Input Artifacts (Session Start)
- **docs/context/project_init_latest.md**: L1 hot memory, project overview
- **docs/context/exec_memory_packet_latest.json**: Execution state from previous phase
- **docs/phase_brief/phase<N>-brief.md**: Current phase requirements
- **docs/context/workflow_status_latest.json**: Per-workflow-type status snapshot

### Working Artifacts (During Execution)
- **docs/evidence/<phase>/<artifact>.json**: Skill execution evidence
- **docs/context/hierarchy_confirmation_latest.md**: Domain hierarchy for current task
- **docs/context/confidence_gate_latest.json**: Confidence routing decisions

### Output Artifacts (Phase Closure)
- **docs/context/worker_reply_packet.json**: Phase completion report
- **docs/context/closure_packet_latest.json**: Validated closure data
- **docs/context/auditor_findings_latest.json**: Auditor review results
- **docs/context/saw_report_latest.md**: SAW protocol execution report

## Workflow Type Integration

### Workflow Profile Declaration (Phase Brief)
```markdown
## Workflow Profile
**Workflow Weight**:
- Frontend: 20%
- Backend: 40%
- Governance: 20%
- Data: 10%
- Research: 10%
**Total: 100%**
```

### Status Aggregation ($workflow-status)
```
For each workflow type (frontend, backend, governance, data, research):
    1. Scan deliverables with matching workflow_type
    2. Check success criteria status
    3. Aggregate to color: green/yellow/red/n/a
    4. Emit per-workflow status

Calculate overall_color:
    - If any red → overall red
    - If any yellow (no red) → overall yellow
    - If all green/n/a → overall green

Emit workflow_status_latest.json with:
    - phase_id
    - workflow_weights (from phase brief)
    - per_workflow_status (color + blocking_issues)
    - overall_color
    - last_updated
```

### Blocking Logic ($project-guider Section 2.5)
```
Load workflow_status_latest.json
    ↓
Check overall_color
    ↓
If red:
    - Emit: StatusAlert: BLOCKED
    - List blocking issues from per_workflow_status
    - Ask user: "Resolve blockers first, or proceed anyway?"
    - If user says proceed → continue with warning
    - If user says resolve → route to blocker resolution
    ↓
If yellow:
    - Emit: StatusAlert: DEGRADED
    - List warnings
    - Proceed with caution
    ↓
If green:
    - Proceed normally
```

## Confidence-Based Routing

### Confidence Gate Flow
```
Skill execution in progress
    ↓
Skill emits confidence score (0-100)
    ↓
If confidence >= 80:
    - Proceed with skill output
    - No escalation needed
    ↓
If confidence < 80:
    - Emit: ConfidenceGate: ESCALATE
    - Log escalation reason
    - Invoke $expert-researcher
    - $expert-researcher loads domain-specific field template
    - $expert-researcher emits expert guidance
    - Original skill incorporates guidance
    - Re-emit confidence score
    ↓
If still < 80 after expert guidance:
    - Emit: ConfidenceGate: INSUFFICIENT
    - Recommend user consultation or external research
```

## Model Routing Strategy

### Worker Tier (codex-5.2)
Fast execution for deterministic tasks:
- se-executor: Code implementation with evidence tracking
- context-bootstrap: Context packet generation
- workflow-status: Status aggregation
- quick-gate: Pre-commit validation

### Audit Tier (codex-5.4)
Independent review with higher scrutiny:
- saw: Subagents-After-Work protocol execution

### Reasoning Tier (claude)
Complex reasoning and sensitive domains:
- research-analysis: Research evidence with citation validation
- architect-review: Architecture review with calibration
- expert-researcher: Domain expert guidance
- project-guider: Session orchestration
- web-search: External information synthesis
- doc-draft: Structured documentation generation

## Error Handling and Recovery

### Validator Exit Codes
- **0 (PASS)**: All checks passed, safe to proceed
- **1 (FAIL)**: Validation failures, fixable by user/worker
- **2 (ERROR)**: Infrastructure errors (missing files, invalid JSON), requires investigation

### Recovery Paths
- **Validation FAIL**: Emit remediation guidance, allow retry
- **Validation ERROR**: Halt workflow, emit diagnostic info, require manual intervention
- **Confidence INSUFFICIENT**: Escalate to expert-researcher or user consultation
- **Status BLOCKED**: List blockers, offer resolution or proceed-anyway options

## Integration Points

### AGENTS.md → Skills
- AGENTS.md: Navigation hub, shows wiring at a glance
- .codex/skills/README.md: Skill registry, activation policies, model routing
- .codex/skills/<skill>/SKILL.md: Individual skill contracts

### Skills → Validators
- Skills emit validation tokens (PASS/BLOCK/DRIFT/INSUFFICIENT)
- Validators run as subprocess: `python .codex/skills/_shared/scripts/validate_*.py`
- Exit codes determine workflow continuation

### Validators → Auditor
- Validators check individual skill outputs
- Auditor checks final worker_reply_packet.json
- Auditor is orthogonal to SAW (different concerns)

### Auditor → Calibration
- Auditor findings logged to calibration database
- Weekly calibration report: `scripts/auditor_calibration_report.py`
- Promotion gate (shadow → enforce) requires calibration data

## Debugging Integration Issues

### Common Issues
1. **Skill not activating**: Check activation policy in .codex/skills/README.md
2. **Validator failing**: Check exit code (0/1/2) and error message
3. **Status always red**: Check workflow_status_latest.json for blocking_issues
4. **Confidence always low**: Check if expert-researcher is being invoked
5. **Auditor blocking**: Check severity (CRITICAL/HIGH in enforce mode)

### Diagnostic Commands
```bash
# Check skill registry
cat .codex/skills/README.md

# Check workflow status
cat docs/context/workflow_status_latest.json

# Run validator manually
python .codex/skills/_shared/scripts/validate_closure_packet.py \
  --packet docs/context/worker_reply_packet.json

# Check auditor findings
cat docs/context/auditor_findings_latest.json

# Run calibration report
python scripts/auditor_calibration_report.py --mode weekly
```

## Next Steps

- For session orchestration details: see .codex/skills/project-guider/SKILL.md
- For SAW protocol: see docs/saw_protocol.md
- For auditor details: see docs/auditor_protocol.md
- For skill development: see .codex/skills/README.md
