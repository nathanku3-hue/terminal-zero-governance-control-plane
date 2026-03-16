# Auditor Calibration Report (DOSSIER)

**Generated:** 2026-03-15T12:22:58.184046+00:00
**Runs included:** 16
**Time range:** 2026-03-03T00:00:00Z to 2026-03-17T00:00:00Z

## Summary

| Metric | Value |
|--------|-------|
| Items reviewed | 66 |
| CRITICAL | 1 |
| HIGH | 52 |
| MEDIUM | 42 |
| LOW | 0 |
| INFO | 0 |

## FP Analysis

| Metric | Value |
|--------|-------|
| Ledger loaded | True |
| C/H total | 53 |
| C/H annotated | 53 |
| C/H unannotated | 0 |
| C/H FP count | 0 |
| FP rate | 0.00% |
| Annotation coverage | 100.00% |

## Per-Rule Breakdown

| Rule ID | Total | C | H | M | L | I | FP |
|---------|-------|---|---|---|---|---|-----|
| AUD-R001 | 1 | 1 | 0 | 0 | 0 | 0 | 0 |
| AUD-R002 | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| AUD-R003 | 50 | 0 | 50 | 0 | 0 | 0 | 0 |
| AUD-R004 | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| AUD-R005 | 41 | 0 | 0 | 41 | 0 | 0 | 0 |
| AUD-R007 | 1 | 0 | 0 | 1 | 0 | 0 | 0 |

## Weekly Windows

| Week | Items | C | H | M | L | I |
|------|-------|---|---|---|---|---|
| 2026-W10 | 54 | 1 | 42 | 34 | 0 | 0 |
| 2026-W11 | 12 | 0 | 10 | 8 | 0 | 0 |

## Promotion Dossier

| Criterion | Met | Value |
|-----------|-----|-------|
| c0_infra_health | ✅ | 0 failures |
| c1_24b_close | ⚠️ | MANUAL_CHECK |
| c2_min_items | ✅ | 66 >= 30 |
| c3_min_weeks | ✅ | 2 consecutive weeks >= 2 |
| c4_fp_rate | ✅ | 0.00% |
| c4b_annotation_coverage | ✅ | 100.00% |
| c5_all_v2 | ✅ | 1 versions: ['2.0.0'] |
