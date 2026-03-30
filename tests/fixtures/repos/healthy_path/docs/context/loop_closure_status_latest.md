# Loop Closure Validation

- GeneratedAtUTC: 2026-03-30T06:33:26Z
- Result: NOT_READY
- ExitCode: 1
- FreshnessHours: 72.00

| Check | Status | Message |
|---|---|---|
| required_dossier_json | PASS | Required artifact found. |
| required_calibration_json | PASS | Required artifact found. |
| required_go_signal_md | PASS | Required artifact found. |
| required_startup_card_md | FAIL | Required artifact missing. |
| required_exec_memory_json | PASS | Required artifact found. |
| go_signal_action_gate | FAIL | Recommended action must be GO (actual=HOLD). |
| startup_gate_status | FAIL | Required startup_intake_latest.json not found. |
| tdd_contract_gate | FAIL | TDD contract gate failed. |
| domain_falsification_gate | SKIP | DOMAIN_FALSIFICATION_REQUIRED is NO (or omitted); domain falsification gate skipped for non-semantic round. |
| done_when_checks_gate | PASS | DONE_WHEN checks gate passed. |
| counterexample_gate | PASS | Counterexample gate passed. |
| dual_judge_gate | PASS | Dual-judge gate passed. |
| refactor_mock_policy_gate | PASS | Refactor/mock policy gate passed. |
| review_checklist_gate | SKIP | Review checklist artifact not found; gate skipped. |
| interface_contract_gate | SKIP | Interface contract manifest not found; gate skipped. |
| parallel_fanin_gate | PASS | Parallel fan-in gate passed (no active parallel shards). |
| freshness_gate | PASS | All checked artifacts are within freshness threshold (72.00h). |
| go_signal_truth_gate | PASS | Go-signal truth-check passed. |
| weekly_summary_truth_gate | PASS | Weekly summary truth-check passed. |
| exec_memory_truth_gate | PASS | Exec memory truth-check passed. |

## Summary

- Pass: 13
- Fail: 4
- Error: 0
- Skip: 3
