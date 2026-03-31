# Phase 8 GA Readiness Runbook

## Purpose
Define deterministic GA burn-in execution and sign-off interpretation for Phase 8.

## Locked Scenario Matrix
- Runs: 30 total (5 scenarios × 6 runs each)
- Scenario fixture mapping is pinned in code (`sop.phase8_ga_readiness.SCENARIO_FIXTURE_MAP`)
- No dynamic scenario substitution is allowed.

### Scenario IDs and expected terminal results
- `healthy-pass-path` → expected `PASS`
- `policy-shadow-block-path` → expected `PASS` (non-blocking completion with shadow/block evidence)
- `gate-hold-path` → expected `HOLD`
- `plugin-warn-path` → expected `PASS` (non-terminal completion with plugin WARN evidence)
- `failure-artifact-path` → expected `FAIL`

## Execution Commands
- Burn-in + artifact generation:
  - `python scripts/phase8_ga_readiness.py --repo-root .`
- Optional CLI path:
  - `sop phase8-ga-readiness --repo-root .`
- Contract tests:
  - `pytest tests/test_phase8_ga_readiness.py tests/test_phase8_ga_readiness_cli.py`

## Unexpected Failure Rule (Authoritative)
A run is an unexpected failure iff any are true:
1. `actual_final_result != expected_final_result`
2. Process exits non-zero when scenario contract expects normal completion
3. Required summary artifacts are missing:
   - loop summary (`loop_cycle_summary_latest.json`)
   - closure/status artifact (`loop_closure_status_latest.json`)
4. Terminal decision artifact is missing (loop summary terminal result unavailable)

Unexpected failure rate:
- `unexpected_failure_rate = unexpected_failures / total_runs`

## Drift Comparison Contract
- Compare pinned fields only.
- Ignore variable fields only.
- Pinned fields and ignore-list are emitted in `burnin_report_latest.json`.

## Required Artifacts
- `docs/context/burnin_report_latest.json`
- `docs/context/slo_baseline_latest.json`
- `docs/context/ga_signoff_packet_latest.md`

## Sign-off Criteria (PASS/FAIL only)
- Final verdict enum is strictly `PASS` or `FAIL`.
- `PASS`: unexpected failure count is 0 and no contract-evidence failures.
- `FAIL`: any unexpected failure or contract-evidence failure exists.

## Operational Burn-In Interpretation
- `policy-shadow-block-path` must include `SHADOW_BLOCK` evidence in audit trail.
- `plugin-warn-path` must include plugin `WARN` entry in audit trail.
- `gate-hold-path` is valid when terminal result remains `HOLD`.
- `failure-artifact-path` is valid when terminal result remains `FAIL`.
