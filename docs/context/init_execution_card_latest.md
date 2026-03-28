# Init Execution Card

- GeneratedAtUTC: 2026-03-15T12:27:15Z
- StartupGateStatus: READY_TO_EXECUTE
- ReadinessPolicy: AUTHORITATIVE
- HandoffTarget: LOCAL_CLI
- WorkerHeader: (skills call upon worker)
- ProfileSelectionAdvisory: PROFILE_RECOMMENDED -> quant_default
- RiskTier: MEDIUM
- DoneWhenChecks: startup_gate_status,go_signal_action_gate,freshness_gate,go_signal_truth_gate
- RequiredContractFields: ORIGINAL_INTENT, DELIVERABLE_THIS_SCOPE, NON_GOALS, DONE_WHEN, DECISION_CLASS, EXECUTION_LANE, RISK_TIER, DONE_WHEN_CHECKS, POSITIONING_LOCK, TASK_GRANULARITY_LIMIT, REFACTOR_* controls, COUNTEREXAMPLE_TEST_*, MOCK_POLICY_*, OWNED_FILES, INTERFACE_* fields, INTUITION_GATE, INTUITION_GATE_RATIONALE
- AckStatus: N/A (MACHINE_DEFAULT)
- ReadinessProgress: 12/12 (100.0%)
- ReadinessStatus: READY

## Worker Kickoff Reference
```text
OPEN: docs\context\startup_intake_latest.md
SECTION: Paste-Ready Worker Kickoff
WORKER_HEADER: (skills call upon worker)
HANDOFF_TARGET: LOCAL_CLI
```
- NEXT_ACTION: Use the worker kickoff block reference to start execution.
