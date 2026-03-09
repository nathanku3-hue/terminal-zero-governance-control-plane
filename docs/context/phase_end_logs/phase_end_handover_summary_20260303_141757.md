# Phase-End Handover Gate Summary

- RunID: 20260303_141757
- Result: BLOCK
- FailedGate: G07_orphan_change_gate
- RepoRoot: E:\code\SOP\quant_current_scope
- RepoProfile: default
- StartedUTC: 2026-03-03T06:17:57Z
- EndedUTC: 2026-03-03T06:17:59Z

## Resolved Config

- repo_profile: default
- repo_root: E:\code\SOP\quant_current_scope
- scan_root: E:\code\SOP\quant_current_scope\docs
- traceability_path: E:\code\SOP\quant_current_scope\docs\pm_to_code_traceability.yaml
- dispatch_manifest_path: E:\code\SOP\quant_current_scope\docs\context\dispatch_manifest.json
- worker_reply_path: E:\code\SOP\quant_current_scope\docs\context\worker_reply_packet.json
- worker_aggregate_path: E:\code\SOP\quant_current_scope\docs\context\worker_status_aggregate.json
- escalation_path: E:\code\SOP\quant_current_scope\docs\context\escalation_events.json
- digest_path: E:\code\SOP\quant_current_scope\docs\context\ceo_bridge_digest.md
- orphan_include: *.py, *.ps1, *.ts, *.tsx, *.js, *.jsx, *.yaml, *.yml
- skip_orphan_gate: False
- skip_dispatch_gate: False

| Gate | Status | Exit | Log |
|------|--------|------|-----|
| G01_context_build | PASS | 0 | E:\code\SOP\quant_current_scope\docs\context\phase_end_logs\20260303_141757_G01_context_build.log |
| G02_context_validate | PASS | 0 | E:\code\SOP\quant_current_scope\docs\context\phase_end_logs\20260303_141757_G02_context_validate.log |
| G03_worker_status_aggregate | PASS | 0 | E:\code\SOP\quant_current_scope\docs\context\phase_end_logs\20260303_141757_G03_worker_status_aggregate.log |
| G04_traceability_gate | PASS | 0 | E:\code\SOP\quant_current_scope\docs\context\phase_end_logs\20260303_141757_G04_traceability_gate.log |
| G05_evidence_hash_gate | PASS | 0 | E:\code\SOP\quant_current_scope\docs\context\phase_end_logs\20260303_141757_G05_evidence_hash_gate.log |
| G05b_cross_repo_readiness | SKIPPED | 0 | - |
| G06_worker_reply_gate | PASS | 0 | E:\code\SOP\quant_current_scope\docs\context\phase_end_logs\20260303_141757_G06_worker_reply_gate.log |
| G07_orphan_change_gate | BLOCK | 1 | E:\code\SOP\quant_current_scope\docs\context\phase_end_logs\20260303_141757_G07_orphan_change_gate.log |
| G11_auditor_review | PASS | 0 | E:\code\SOP\quant_current_scope\docs\context\phase_end_logs\20260303_141757_G11_auditor_review.log |
| G09b_rebuild_ceo_digest | PASS | 0 | E:\code\SOP\quant_current_scope\docs\context\phase_end_logs\20260303_141757_G09b_rebuild_ceo_digest.log |
| G10b_digest_freshness_revalidation | PASS | 0 | E:\code\SOP\quant_current_scope\docs\context\phase_end_logs\20260303_141757_G10b_digest_freshness_revalidation.log |

