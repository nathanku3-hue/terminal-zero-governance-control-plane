# Loop Closure Validation

- GeneratedAtUTC: 2026-03-29T07:32:42Z
- Result: INPUT_OR_INFRA_ERROR
- ExitCode: 2
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
| tdd_contract_gate | FAIL | Round contract artifact missing for TDD contract gate. |
| domain_falsification_gate | SKIP | Round contract missing; domain falsification gate skipped. |
| done_when_checks_gate | ERROR | DONE_WHEN checks gate had input/infra errors. |
| counterexample_gate | ERROR | Counterexample gate had input/infra errors. |
| dual_judge_gate | ERROR | Dual-judge gate had input/infra errors. |
| refactor_mock_policy_gate | ERROR | Refactor/mock policy gate had input/infra errors. |
| review_checklist_gate | SKIP | Review checklist artifact not found; gate skipped. |
| interface_contract_gate | SKIP | Interface contract manifest not found; gate skipped. |
| parallel_fanin_gate | PASS | Parallel fan-in gate passed (no active parallel shards). |
| freshness_gate | PASS | All checked artifacts are within freshness threshold (72.00h). |
| go_signal_truth_gate | PASS | Go-signal truth-check passed. |
| weekly_summary_truth_gate | PASS | Weekly summary truth-check passed. |
| exec_memory_truth_gate | PASS | Exec memory truth-check passed. |

## Summary

- Pass: 9
- Fail: 4
- Error: 4
- Skip: 3
