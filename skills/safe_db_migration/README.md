# Skill: safe-db-migration

## Overview

Execute database schema changes with rollback plan, backup verification, and zero data loss guarantees. This skill provides a structured approach to database migrations that prioritizes safety and recoverability.

## When to Use

- Adding or removing columns
- Creating or dropping indexes
- Modifying constraints (foreign keys, unique constraints, check constraints)
- Data migrations between tables
- Schema refactoring with data preservation
- Any production database schema change

## Guardrails

This skill enforces strict safety gates:

### Pre-Execution Gates
- **Backup verified**: Recent backup (<24h) exists and is restorable
- **Rollback plan approved**: Rollback script reviewed and approved by auditor
- **Test coverage adequate**: Test coverage ≥80% for affected code paths
- **Staging validation passed**: Migration successfully executed in staging
- **Auditor review required**: Auditor has reviewed migration plan
- **CEO GO signal required**: CEO approval obtained for production execution

### During-Execution Monitoring
- Lock duration monitoring (prevent service disruption)
- Application error rate monitoring
- Query performance degradation checks

### Post-Execution Validation
- Data integrity verification (row counts, constraints)
- Application health checks
- Performance baseline maintained

## Benchmark Requirements

This skill requires the model to meet minimum capability thresholds:

- **sql_accuracy ≥ 0.85**: Model must demonstrate high SQL competency

**Current Baseline**: Claude Opus 4.6 achieves sql_accuracy = 0.91 (exceeds requirement)

## Execution Steps

1. **Analyze schema change**: Assess impact and risks
2. **Generate migration script**: Create forward migration SQL
3. **Generate rollback script**: Create recovery script
4. **Validate data integrity**: Test migration in staging
5. **Verify backup**: Confirm backup exists and is restorable
6. **Execute migration**: Run in production with monitoring
7. **Post-migration validation**: Verify success and data integrity
8. **Rollback if needed**: Execute rollback on failure

## Failure Handling

- **Rollback required**: Yes (automatic on failure)
- **Escalation path**: PM/CEO
- **Max retry attempts**: 0 (no automatic retries)

## Examples

See `examples/` directory for:
- PostgreSQL: Add column with default value
- MySQL: Add index without locking table (coming soon)
- SQL Server: Migrate data between tables (coming soon)

## Approval

- **Risk Level**: HIGH
- **Approved By**: PM/CEO
- **Approval Decision**: D-176
- **Approval Date**: 2026-03-13
- **Status**: Active
