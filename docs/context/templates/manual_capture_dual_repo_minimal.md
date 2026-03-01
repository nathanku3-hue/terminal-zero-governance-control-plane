# Manual Capture Dual Repo Minimal

## Goal
Run manual-capture closure for at most two active repos without building a global multi-tenant orchestrator.

## Required Artifacts
- `docs/context/e2e_evidence/index.md` (generated from `e2e_evidence_index.md.template`)
- `docs/context/e2e_evidence/manual_capture_queue.json`
- `docs/context/e2e_evidence/manual_capture_alerts.json`

## Repo Onboarding
1. Initialize each repo evidence structure:
   - `powershell -ExecutionPolicy Bypass -File scripts/init_manual_capture_repo.ps1 -RepoRoot <REPO_PATH> -TaskId T12`
2. Create one drop zone per repo (do not share one folder):
   - Quant example: `Evidence_Drop_Quant`
   - Film example: `Evidence_Drop_Film`
3. Register one watcher task per repo at logon:
   - `powershell -ExecutionPolicy Bypass -File scripts/register_dual_repo_manual_capture_tasks.ps1 ...`

## Naming Contract
- `T<id>_manual1_<context>_<YYYYMMDD>.<ext>`
- `T<id>_manual2_<context>_<YYYYMMDD>.<ext>`
- `T<id>_manual3_<context>_<YYYYMMDD>.<ext>`

## SLA
- `<15m`: `Machine PASS + Manual Pending`
- `>=15m`: `WARNED`
- `>=30m`: `BLOCK`
