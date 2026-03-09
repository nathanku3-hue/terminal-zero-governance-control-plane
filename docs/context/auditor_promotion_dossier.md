# Auditor Calibration Report (DOSSIER)

**Generated:** 2026-03-09T01:53:09.392605+00:00
**Runs included:** 14
**Time range:** N/A to N/A

## Summary

| Metric | Value |
|--------|-------|
| Items reviewed | 54 |
| CRITICAL | 1 |
| HIGH | 42 |
| MEDIUM | 34 |
| LOW | 0 |
| INFO | 0 |

## FP Analysis

| Metric | Value |
|--------|-------|
| Ledger loaded | True |
| C/H total | 43 |
| C/H annotated | 23 |
| C/H unannotated | 20 |
| C/H FP count | 0 |
| FP rate | 0.00% |
| Annotation coverage | 53.49% |

## Per-Rule Breakdown

| Rule ID | Total | C | H | M | L | I | FP |
|---------|-------|---|---|---|---|---|-----|
| AUD-R001 | 1 | 1 | 0 | 0 | 0 | 0 | 0 |
| AUD-R002 | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| AUD-R003 | 40 | 0 | 40 | 0 | 0 | 0 | 0 |
| AUD-R004 | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| AUD-R005 | 33 | 0 | 0 | 33 | 0 | 0 | 0 |
| AUD-R007 | 1 | 0 | 0 | 1 | 0 | 0 | 0 |

## Weekly Windows

| Week | Items | C | H | M | L | I |
|------|-------|---|---|---|---|---|
| 2026-W10 | 54 | 1 | 42 | 34 | 0 | 0 |

## Promotion Dossier

| Criterion | Met | Value |
|-----------|-----|-------|
| c0_infra_health | ✅ | 0 failures |
| c1_24b_close | ⚠️ | MANUAL_CHECK |
| c2_min_items | ✅ | 54 >= 30 |
| c3_min_weeks | ❌ | 1 consecutive weeks >= 2 |
| c4_fp_rate | ✅ | 0.00% |
| c4b_annotation_coverage | ❌ | 53.49% |
| c5_all_v2 | ✅ | 1 versions: ['2.0.0'] |
