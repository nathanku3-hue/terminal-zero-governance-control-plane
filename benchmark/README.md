# Benchmark Harness

Phase 5A.1 benchmark artifacts live here.

Structure:
- `suites/`: Promptfoo configs.
- `results/`: raw Promptfoo JSON outputs.
- `baselines/`: persisted baseline summaries.

Usage:
```bash
python scripts/run_baseline_benchmark.py --env-file benchmark/.env
python scripts/validate_baseline.py
python scripts/test_policy_proposal.py
```

## Current Baseline

- **Model**: anthropic:claude-opus-4-6
- **Suite**: sql_accuracy
- **Score**: 0.91 (median of 3 runs)
- **Established**: 2026-03-12

## Notes

- The suite uses `anthropic:claude-opus-4-6` provider via Promptfoo.
- Requires `.env` file with `ANTHROPIC_API_KEY` and `ANTHROPIC_BASE_URL`.
- `run_baseline_benchmark.py` fails closed on provider/API errors and distinguishes assertion failures from transport errors.
- Promptfoo JSON exports use `results.results` array (Promptfoo 0.121.1).
- `contains-any` assertions use `value` field (not `values`) in this Promptfoo version.
