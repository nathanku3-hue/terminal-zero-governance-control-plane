# Observability Pack Template

Status: Template
Authority: advisory-only integration artifact. This file does not authorize execution, promotion, or scope widening by itself.
Purpose: make drift visible early without bloating process through minimal observability markers.

## Header
- `PACK_ID`: `<YYYYMMDD-short-id>`
- `DATE_UTC`: `<ISO8601>`
- `SCOPE`: `<phase / round / feature / system slice>`
- `OWNER`: `<PM / architecture / operator>`

## Why This File Exists
- `<one line explaining why this scope needs observability markers>`

## High-Risk Attempts

### Definition
High-risk attempts are operations that could cause data loss, production outages, or irreversible state changes.

### Markers
- **Destructive git operations**: `git reset --hard`, `git push --force`, `git clean -f`, `git branch -D`
- **Production deployments**: any deployment to production environment
- **Database migrations**: schema changes, data migrations, DROP operations
- **Credential changes**: API key rotation, password changes, permission updates
- **Infrastructure changes**: server provisioning, network changes, DNS updates

### Observability Rule
Log all high-risk attempts with:
- Timestamp
- Operation type
- Operator (human or agent)
- Approval status (approved / denied / skipped)
- Outcome (success / failure / rolled back)

### Drift Signal
If high-risk attempts are happening without explicit approval, the governance boundary is weak.

## Stuck Session

### Definition
A stuck session is one where the planner/worker cannot make progress for N consecutive cycles (default: 3).

### Markers
- **Same error repeated**: Same test failure, lint error, or runtime error appears in 3+ consecutive cycles
- **No file changes**: No files modified in 3+ consecutive cycles despite active scope
- **Circular reasoning**: Planner proposes same next step in 3+ consecutive cycles
- **Escalation loop**: Planner escalates to wider reads in 3+ consecutive cycles without resolving gap

### Observability Rule
Log stuck session markers with:
- Timestamp
- Cycle count
- Stuck reason (same error / no changes / circular / escalation loop)
- Last proposed next step
- Last error message (if applicable)

### Drift Signal
If stuck sessions are frequent, the planner packet or impact packet is insufficient, or the escalation rules are too permissive.

## Skill Activation / Under-Triggering

### Definition
Skills are specialized capabilities that should trigger automatically when certain conditions are met. Under-triggering means the skill should have triggered but didn't.

### Markers
- **Commit skill**: Should trigger when user asks to commit changes, or when done checklist is complete
- **Review skill**: Should trigger when user asks for code review, or when phase closeout begins
- **Test skill**: Should trigger when user asks to run tests, or when implementation is complete
- **Deploy skill**: Should trigger when user asks to deploy, or when tests pass and approval is granted

### Observability Rule
Log skill activation with:
- Timestamp
- Skill name
- Trigger condition (explicit user request / automatic condition met)
- Activation status (triggered / skipped / failed)

### Drift Signal
If skills are under-triggering (should have triggered but didn't), the trigger conditions are too narrow or the planner is not checking them.

## Budget Pressure

### Definition
Budget pressure is when the session is approaching token limits, time limits, or cost limits.

### Markers
- **Token budget**: Session has used >80% of token budget
- **Time budget**: Session has run for >80% of time budget
- **Cost budget**: Session has incurred >80% of cost budget
- **Context window**: Conversation history is approaching context window limit

### Observability Rule
Log budget pressure with:
- Timestamp
- Budget type (token / time / cost / context)
- Current usage (absolute and percentage)
- Remaining budget
- Projected exhaustion time (if trend continues)

### Drift Signal
If budget pressure is frequent, the planner is reading too much, the worker is doing too much per cycle, or the scope is too large.

## Compaction / Hallucination Pressure Markers

### Definition
Compaction pressure is when the system is compressing conversation history to fit context limits. Hallucination pressure is when the system is making claims that are not supported by evidence.

### Markers
- **Compaction events**: Conversation history was compressed N times
- **Stale artifact references**: Planner references artifact that was compacted out of context
- **Unsupported claims**: Planner claims file exists / test passes / feature works without evidence
- **Contradictory claims**: Planner makes claim that contradicts earlier evidence

### Observability Rule
Log compaction/hallucination pressure with:
- Timestamp
- Pressure type (compaction / stale reference / unsupported claim / contradiction)
- Artifact or claim in question
- Evidence status (missing / contradictory / stale)

### Drift Signal
If compaction/hallucination pressure is frequent, the planner is not using small packets, the artifacts are not being refreshed, or the session is too long.

## Observability Pack Summary

At the end of each phase/round, generate a summary:

```
High-Risk Attempts: <count> (<approved> / <denied> / <skipped>)
Stuck Sessions: <count> (<same error> / <no changes> / <circular> / <escalation loop>)
Skill Under-Triggering: <count> (<commit> / <review> / <test> / <deploy>)
Budget Pressure Events: <count> (<token> / <time> / <cost> / <context>)
Compaction/Hallucination Events: <count> (<compaction> / <stale> / <unsupported> / <contradiction>)
```

## Drift Guardrails

When observability markers exceed thresholds, create explicit guardrails:

### High-Risk Attempts
- **Threshold**: >3 high-risk attempts without approval in one phase
- **Guardrail**: Require explicit approval for all high-risk operations

### Stuck Sessions
- **Threshold**: >2 stuck sessions in one phase
- **Guardrail**: Require planner to escalate to human after 3 consecutive stuck cycles

### Skill Under-Triggering
- **Threshold**: >3 under-trigger events in one phase
- **Guardrail**: Make trigger conditions more explicit, or add reminder prompts

### Budget Pressure
- **Threshold**: >2 budget pressure events in one phase
- **Guardrail**: Reduce scope, increase budget, or split phase into smaller rounds

### Compaction/Hallucination Pressure
- **Threshold**: >3 compaction/hallucination events in one phase
- **Guardrail**: Refresh artifacts more frequently, use smaller packets, or split session

## Writing Rules
- Keep this file compact and machine-readable.
- Make markers explicit and checkable.
- Make thresholds explicit and adjustable.
- Keep the artifact thin: one current pack, not a growing archive.
