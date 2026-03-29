# Observability Pack
Generated: 2026-03-29
Activation: Per KERNEL_ACTIVATION_MATRIX.md — Quant repo ✅ Active

## High-Risk Attempts
<!-- List attempts that touched critical paths or caused REQUIRES_FIX failures -->
<!-- Format: date | failure_class | error_code | outcome -->

## Stuck Sessions
<!-- List sessions that ran >3 cycles without progress -->
<!-- Format: date | session description | resolution -->

## Skill Under-Triggering
<!-- List skills that resolved to EMPTY_BY_DESIGN unexpectedly -->
<!-- Format: date | skill | expected | actual -->

## Budget Pressure
<!-- Note runs where context window or token budget approached limits -->

## Compaction/Hallucination Pressure
<!-- Note sessions where compaction triggered or hallucination suspected -->

## Drift Markers (machine-checkable)
- [ ] No FATAL envelope on last 3 runs
- [ ] `skills_status` = OK on last run
- [ ] `final_result` in [PASS, READY_TO_ESCALATE] on last run
- [ ] `check_fail_open.py` baseline green
- [ ] No new BLOCKERs in last scan
- [ ] `TestByteIdentityContract` green
