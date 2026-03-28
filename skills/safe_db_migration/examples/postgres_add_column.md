# Example: PostgreSQL Add Column with Default Value

## Scenario

Add a `status` column to the `orders` table with a default value of `pending`, ensuring zero downtime and data integrity.

## Context

- **Database**: PostgreSQL 14+
- **Table**: `orders` (production table with 10M+ rows)
- **Change**: Add `status VARCHAR(50) DEFAULT 'pending' NOT NULL`
- **Risk**: HIGH (large table, production traffic)

## Step 1: Analyze Schema Change

**Current Schema**:
```sql
CREATE TABLE orders (
    id BIGSERIAL PRIMARY KEY,
    customer_id BIGINT NOT NULL,
    order_date TIMESTAMP NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL
);
```

**Proposed Change**:
```sql
ALTER TABLE orders ADD COLUMN status VARCHAR(50) DEFAULT 'pending' NOT NULL;
```

**Impact Assessment**:
- Affected rows: 10M+
- Lock type: ACCESS EXCLUSIVE (blocks all operations)
- Estimated lock duration: 2-5 seconds (PostgreSQL 11+ optimizes DEFAULT with NOT NULL)
- Risk: MEDIUM (brief lock, but high-traffic table)

## Step 2: Generate Migration Script

**Forward Migration** (`migration_001_add_status_column.sql`):
```sql
-- Migration: Add status column to orders table
-- Author: safe-db-migration skill
-- Date: 2026-03-13
-- Risk: MEDIUM

BEGIN;

-- Add column with default (PostgreSQL 11+ optimizes this)
ALTER TABLE orders
ADD COLUMN status VARCHAR(50) DEFAULT 'pending' NOT NULL;

-- Verify column exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'orders' AND column_name = 'status'
    ) THEN
        RAISE EXCEPTION 'Column status was not added to orders table';
    END IF;
END $$;

-- Verify row count unchanged
DO $$
DECLARE
    expected_count BIGINT;
    actual_count BIGINT;
BEGIN
    SELECT COUNT(*) INTO expected_count FROM orders;
    SELECT COUNT(*) INTO actual_count FROM orders WHERE status IS NOT NULL;

    IF expected_count != actual_count THEN
        RAISE EXCEPTION 'Row count mismatch: expected %, got %', expected_count, actual_count;
    END IF;
END $$;

COMMIT;
```

## Step 3: Generate Rollback Script

**Rollback Script** (`rollback_001_add_status_column.sql`):
```sql
-- Rollback: Remove status column from orders table
-- Author: safe-db-migration skill
-- Date: 2026-03-13

BEGIN;

-- Verify column exists before dropping
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'orders' AND column_name = 'status'
    ) THEN
        RAISE EXCEPTION 'Column status does not exist, cannot rollback';
    END IF;
END $$;

-- Drop column
ALTER TABLE orders DROP COLUMN status;

-- Verify column removed
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'orders' AND column_name = 'status'
    ) THEN
        RAISE EXCEPTION 'Column status still exists after rollback';
    END IF;
END $$;

COMMIT;
```

## Step 4: Staging Validation

**Test in Staging**:
```bash
# Run migration in staging
psql -h staging-db -U app_user -d app_db -f migration_001_add_status_column.sql

# Verify data integrity
psql -h staging-db -U app_user -d app_db -c "
SELECT
    COUNT(*) as total_rows,
    COUNT(status) as status_not_null,
    COUNT(CASE WHEN status = 'pending' THEN 1 END) as default_values
FROM orders;
"

# Expected output:
#  total_rows | status_not_null | default_values
# ------------+-----------------+----------------
#    10000000 |        10000000 |       10000000

# Test rollback
psql -h staging-db -U app_user -d app_db -f rollback_001_add_status_column.sql

# Verify rollback success
psql -h staging-db -U app_user -d app_db -c "
SELECT column_name FROM information_schema.columns
WHERE table_name = 'orders' AND column_name = 'status';
"

# Expected output: (0 rows)
```

## Step 5: Pre-Execution Checklist

- [x] Backup verified: Latest backup from 2026-03-13 02:00 UTC (11h ago)
- [x] Backup restore tested: Successfully restored to test environment
- [x] Rollback script tested: Successfully rolled back in staging
- [x] Test coverage: 85% coverage on order processing code
- [x] Staging validation: Migration successful, no errors
- [x] Auditor review: Approved by auditor (see decision log D-176)
- [x] CEO GO signal: Obtained (see ceo_go_signal.md)
- [x] Maintenance window: Scheduled for 2026-03-13 22:00 UTC (low traffic)

## Step 6: Execute Migration

**Execution Plan**:
```bash
# 1. Enable monitoring
# Monitor lock duration, error rate, query performance

# 2. Execute migration
psql -h prod-db -U app_user -d app_db -f migration_001_add_status_column.sql

# 3. Monitor execution
# Expected duration: 2-5 seconds
# Expected lock: ACCESS EXCLUSIVE (brief)

# 4. Verify success
psql -h prod-db -U app_user -d app_db -c "
SELECT
    COUNT(*) as total_rows,
    COUNT(status) as status_not_null,
    COUNT(CASE WHEN status = 'pending' THEN 1 END) as default_values
FROM orders;
"
```

## Step 7: Post-Migration Validation

**Validation Queries**:
```sql
-- 1. Verify column exists with correct type
SELECT column_name, data_type, column_default, is_nullable
FROM information_schema.columns
WHERE table_name = 'orders' AND column_name = 'status';

-- Expected:
-- column_name | data_type         | column_default | is_nullable
-- ------------+-------------------+----------------+-------------
-- status      | character varying | 'pending'      | NO

-- 2. Verify all rows have default value
SELECT COUNT(*) as rows_without_status
FROM orders
WHERE status IS NULL OR status = '';

-- Expected: 0

-- 3. Verify application health
-- Run application smoke tests
-- Check error logs for database-related errors
-- Verify order creation still works
```

## Step 8: Rollback (If Needed)

**Rollback Trigger Conditions**:
- Migration execution time exceeds 10 seconds
- Application error rate increases >5%
- Data integrity checks fail
- Performance degradation >20%

**Rollback Execution**:
```bash
# Execute rollback immediately
psql -h prod-db -U app_user -d app_db -f rollback_001_add_status_column.sql

# Verify rollback success
psql -h prod-db -U app_user -d app_db -c "
SELECT column_name FROM information_schema.columns
WHERE table_name = 'orders' AND column_name = 'status';
"

# Expected output: (0 rows)

# Verify application recovery
# Run smoke tests
# Check error rate returns to baseline
```

## Outcome

**Success Criteria**:
- ✓ Migration completed in 3.2 seconds
- ✓ No application errors during migration
- ✓ All 10M rows have `status = 'pending'`
- ✓ Query performance within 5% of baseline
- ✓ Application health checks passed

**Lessons Learned**:
- PostgreSQL 11+ optimization for `DEFAULT` with `NOT NULL` worked as expected
- Brief ACCESS EXCLUSIVE lock (3.2s) was acceptable during low-traffic window
- Monitoring showed no impact on application error rate
- Rollback script tested and ready (not needed)

## References

- PostgreSQL Documentation: [ALTER TABLE](https://www.postgresql.org/docs/14/sql-altertable.html)
- PostgreSQL 11+ Optimization: [Fast DEFAULT](https://www.postgresql.org/docs/11/ddl-alter.html#DDL-ALTER-ADDING-A-COLUMN)
- Decision Log: D-176 (safe-db-migration skill approval)
