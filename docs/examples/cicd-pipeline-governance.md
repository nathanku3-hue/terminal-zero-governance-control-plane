# CI/CD Pipeline Governance

## Context
A platform team wants a copy-pasteable GitHub Actions workflow that runs Terminal Zero governance on every pull request and blocks merges when governance returns a failing decision.

## Inputs
- Repository with Python 3.12+ support.
- Governance package: `terminal-zero-governance`.
- Workflow trigger: `pull_request` to `main`.
- Artifact retention requirement for `docs/context/*` files.

## Commands
Use this workflow as `.github/workflows/governance-gate.yml`:

```yaml
name: Governance Gate

on:
  pull_request:
    branches: ["main"]

jobs:
  governance:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install terminal-zero-governance
        run: pip install terminal-zero-governance

      - name: Initialize governed workspace
        run: sop init governed-workspace

      - name: Run governance loop
        run: sop run --repo-root governed-workspace --skip-phase-end

      - name: Inspect governance status
        run: sop status --repo-root governed-workspace

      - name: Archive governance artifacts
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: governance-context-${{ github.run_id }}
          path: governed-workspace/docs/context/*
```

## Output
```text
$ sop run --repo-root governed-workspace --skip-phase-end
[loop] startup checks: PASS
[loop] worker execution: PASS
[loop] policy gate: PASS
[loop] closure gate: HOLD
final_result=HOLD
artifacts_written=governed-workspace/docs/context/loop_cycle_summary_latest.json

$ sop status --repo-root governed-workspace
final_result: HOLD
ready_to_escalate: false
latest_audit_decision: PASS
```

## Expected Decision
The CI job should complete with a governed decision artifact set. Teams typically treat `PASS` as merge-ready and `HOLD` as manual-review-required, with artifact evidence attached to the pull request.
