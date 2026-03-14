# Phase-End Handover Gate Summary

- RunID: 20260306_165856
- Result: BLOCK
- FailedGate: G07_orphan_change_gate
- RepoRoot: E:\Code\SOP\quant_current_scope
- RepoProfile: default
- StartedUTC: 2026-03-06T08:58:56Z
- EndedUTC: 2026-03-06T08:58:58Z

## Resolved Config

- repo_profile: default
- repo_root: E:\Code\SOP\quant_current_scope
- scan_root: E:\Code\SOP\quant_current_scope\docs
- traceability_path: E:\Code\SOP\quant_current_scope\docs\pm_to_code_traceability.yaml
- dispatch_manifest_path: E:\Code\SOP\quant_current_scope\docs\context\dispatch_manifest.json
- worker_reply_path: E:\Code\SOP\quant_current_scope\docs\context\worker_reply_packet.json
- worker_aggregate_path: E:\Code\SOP\quant_current_scope\docs\context\worker_status_aggregate.json
- escalation_path: E:\Code\SOP\quant_current_scope\docs\context\escalation_events.json
- digest_path: E:\Code\SOP\quant_current_scope\docs\context\ceo_bridge_digest.md
- orphan_include: *.py, *.ps1, *.ts, *.tsx, *.js, *.jsx, *.yaml, *.yml
- skip_orphan_gate: False
- skip_dispatch_gate: False

| Gate | Status | Exit | Log |
|------|--------|------|-----|
| G01_context_build | PASS | 0 | E:\Code\SOP\quant_current_scope\docs\context\phase_end_logs\20260306_165856_G01_context_build.log |
| G02_context_validate | PASS | 0 | E:\Code\SOP\quant_current_scope\docs\context\phase_end_logs\20260306_165856_G02_context_validate.log |
| G03_worker_status_aggregate | PASS | 0 | E:\Code\SOP\quant_current_scope\docs\context\phase_end_logs\20260306_165856_G03_worker_status_aggregate.log |
| G04_traceability_gate | PASS | 0 | E:\Code\SOP\quant_current_scope\docs\context\phase_end_logs\20260306_165856_G04_traceability_gate.log |
| G05_evidence_hash_gate | PASS | 0 | E:\Code\SOP\quant_current_scope\docs\context\phase_end_logs\20260306_165856_G05_evidence_hash_gate.log |
| G05b_cross_repo_readiness | SKIPPED | 0 | - |
| G06_worker_reply_gate | PASS | 0 | E:\Code\SOP\quant_current_scope\docs\context\phase_end_logs\20260306_165856_G06_worker_reply_gate.log |
| G07_orphan_change_gate | BLOCK | 1 | E:\Code\SOP\quant_current_scope\docs\context\phase_end_logs\20260306_165856_G07_orphan_change_gate.log |
| G11_auditor_review | PASS | 0 | E:\Code\SOP\quant_current_scope\docs\context\phase_end_logs\20260306_165856_G11_auditor_review.log |
| G09b_rebuild_ceo_digest | PASS | 0 | E:\Code\SOP\quant_current_scope\docs\context\phase_end_logs\20260306_165856_G09b_rebuild_ceo_digest.log |
| G10b_digest_freshness_revalidation | PASS | 0 | E:\Code\SOP\quant_current_scope\docs\context\phase_end_logs\20260306_165856_G10b_digest_freshness_revalidation.log |

