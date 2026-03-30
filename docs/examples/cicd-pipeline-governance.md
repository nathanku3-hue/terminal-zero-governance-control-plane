# Example: CI/CD Pipeline Governance

This example shows how to use the Terminal Zero governance control plane inside
a CI/CD pipeline. The pattern wraps an AI agent task so that every run produces
an auditable, gated governance record.

**Use case:** An AI coding agent runs as part of a GitHub Actions workflow. The
governance loop ensures that every agent execution produces a structured audit
trail, and the CI job fails automatically if a governance gate blocks.

---

## Overview

The pipeline does five things:

1. Bootstrap the governance repo inside the CI workspace.
2. Run the governance loop cycle (wrapping the agent task).
3. Check the audit log for BLOCK decisions.
4. Fail the CI job if governance blocks.
5. Archive the audit artifacts.

---

## Step 1 — Bootstrap the governance repo

In CI, `sop init` creates the governed directory structure on a fresh runner.

```yaml
- name: Bootstrap governance repo
  run: |
    pip install terminal-zero-governance
    sop init governed-workspace
```

This produces `governed-workspace/` with `docs/context/` and all required
directories. No manual file editing is required for a `--skip-phase-end` run.

---

## Step 2 — Pre-populate the round contract (optional)

For a full governance run (without `--skip-phase-end`), the round contract must
be present before `sop run`. You can write it from CI environment variables:

```yaml
- name: Write round contract
  run: |
    cat > governed-workspace/docs/context/round_contract_latest.md << 'EOF'
    # Round Contract
    original_intent: "${{ github.event.inputs.task_description }}"
    risk_tier: low
    decision_class: autonomous
    owner: ci-pipeline
    EOF
```

For a smoke-test run, skip this step and pass `--skip-phase-end` in Step 3.

---

## Step 3 — Run the governance loop cycle

```yaml
- name: Run governance loop
  id: governance
  run: |
    sop run --repo-root governed-workspace --skip-phase-end
    echo "exit_code=$?" >> $GITHUB_OUTPUT
  continue-on-error: true
```

`continue-on-error: true` ensures the audit log is always archived even if the
governance cycle itself fails.

---

## Step 4 — Check audit log for BLOCK decisions

```yaml
- name: Check for governance blocks
  run: |
    BLOCKS=$(sop audit --repo-root governed-workspace --filter-outcome BLOCK | python3 -c "import sys; lines = sys.stdin.read().strip(); print(len([l for l in lines.split('\n') if l.strip()]) if lines else 0)")
    echo "Governance BLOCK count: $BLOCKS"
    if [ "$BLOCKS" -gt "0" ]; then
      echo "GOVERNANCE BLOCKED: ${BLOCKS} decision(s) require operator review."
      sop audit --repo-root governed-workspace --filter-outcome BLOCK
      exit 1
    fi
    echo "Governance: no blocks found."
```

This step reads `docs/context/audit_log.ndjson` and counts entries where
`decision == "BLOCK"`. Any BLOCK fails the CI job with a non-zero exit code.

---

## Step 5 — Archive audit artifacts

```yaml
- name: Archive governance artifacts
  if: always()
  uses: actions/upload-artifact@v4
  with:
    name: governance-audit-${{ github.run_id }}
    path: |
      governed-workspace/docs/context/audit_log.ndjson
      governed-workspace/docs/context/audit_metrics_latest.json
      governed-workspace/docs/context/loop_cycle_summary_latest.json
      governed-workspace/docs/context/loop_cycle_summary_latest.md
      governed-workspace/docs/context/loop_closure_status_latest.json
    retention-days: 90
```

`if: always()` ensures artifacts are uploaded even when the job fails.
Retain audit records for at least 90 days for compliance purposes.

---

## Complete workflow

Paste this into `.github/workflows/governed-agent-task.yml`:

```yaml
name: Governed Agent Task

on:
  workflow_dispatch:
    inputs:
      task_description:
        description: "What should the agent do?"
        required: true
        default: "Run governance smoke test"

jobs:
  govern:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install Terminal Zero
        run: pip install terminal-zero-governance

      - name: Bootstrap governance workspace
        run: sop init governed-workspace

      # Optional: write a real round contract from inputs
      # - name: Write round contract
      #   run: |
      #     cat > governed-workspace/docs/context/round_contract_latest.md << 'EOF'
      #     # Round Contract
      #     original_intent: "${{ github.event.inputs.task_description }}"
      #     risk_tier: low
      #     decision_class: autonomous
      #     owner: ci-pipeline
      #     EOF

      - name: Run governance loop
        id: governance
        run: sop run --repo-root governed-workspace --skip-phase-end
        continue-on-error: true

      - name: Fail if governance blocked
        run: |
          EXIT=$(sop status --repo-root governed-workspace | python3 -c "
import sys, json
data = json.load(sys.stdin)
result = data.get('final_result', 'ERROR')
print(result)
exit(0 if result in ('PASS', 'HOLD') else 1)
")
          echo "Governance result: $EXIT"

      - name: Check for BLOCK decisions
        run: |
          sop audit --repo-root governed-workspace --filter-outcome BLOCK > /tmp/blocks.txt 2>&1
          BLOCK_COUNT=$(wc -l < /tmp/blocks.txt | tr -d ' ')
          if [ "$BLOCK_COUNT" -gt "0" ]; then
            echo "GOVERNANCE BLOCKED:"
            cat /tmp/blocks.txt
            exit 1
          fi
          echo "No governance blocks found."

      - name: Archive governance artifacts
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: governance-audit-${{ github.run_id }}
          path: |
            governed-workspace/docs/context/audit_log.ndjson
            governed-workspace/docs/context/audit_metrics_latest.json
            governed-workspace/docs/context/loop_cycle_summary_latest.json
            governed-workspace/docs/context/loop_cycle_summary_latest.md
            governed-workspace/docs/context/loop_closure_status_latest.json
          retention-days: 90
```

---

## What the artifacts prove

After a successful governed run, you have:

| Artifact | What it proves |
|---|---|
| `audit_log.ndjson` | Every gate decision with timestamp, actor, and trace ID |
| `audit_metrics_latest.json` | Aggregate PASS/BLOCK/HOLD counts for the run |
| `loop_cycle_summary_latest.json` | Overall result with per-step breakdown |
| `loop_closure_status_latest.json` | Explicit readiness verdict (READY_TO_ESCALATE / NOT_READY) |

These artifacts can be attached to a PR review, a change ticket, or a
compliance record. The audit log is append-only and cannot be retroactively
modified without rewriting the file (detectable in git history).

---

## See also

- [Getting Started](../getting-started.md) — install and first run
- [Architecture](../architecture.md) — how the loop and gates work
- [API Reference](../api-reference.md) — full `sop audit` and `sop run` options
- `docs/operator_reference.md` — full startup intake workflow
