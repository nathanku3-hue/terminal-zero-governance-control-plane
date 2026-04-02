# Phase D Validation Gates (Machine-Checkable)

**Date:** 2026-04-01  
**Phase:** Phase D (`phase4` + `phase6`)  
**Status:** Active

---

## Gate Set

### Gate D4-1 — Canonical scenario docs exist
Required files:
- `docs/examples/cicd-pipeline-governance.md`
- `docs/examples/kubernetes-admission-governance.md`
- `docs/examples/multi-service-rollout-governance.md`

Validation command:
```bash
python -m pytest tests/test_phase5_docs.py::test_examples_docs_complete -q
```

### Gate D4-2 — Scenario section completeness
Each canonical scenario doc must include:
- `## Context`
- `## Inputs`
- `## Commands`
- `## Output`
- `## Expected Decision`

Validation command:
```bash
python -m pytest tests/test_phase5_docs.py::test_examples_docs_complete -q
```

### Gate D4-3 — Output fidelity
Each canonical scenario doc must include concrete fenced output with realistic governance markers.

Validation command:
```bash
python -m pytest tests/test_phase5_docs.py::test_examples_docs_complete -q
```

### Gate D4-4 — Troubleshooting minimum matrix
Troubleshooting must include at least 10 cases with exact fields:
- `Symptom`
- `Likely cause`
- `Check`
- `Fix`

Validation command:
```bash
python -m pytest tests/test_phase6_tutorials.py::test_troubleshooting_has_min_10_failure_modes -q
```

### Gate D4-5 — Tutorial integrity
Tutorial docs must include required headers and realistic output blocks.

Validation command:
```bash
python -m pytest tests/test_phase6_tutorials.py -q
```

---

## Contract Result Rule

Phase D validation gate status is PASS only when all D4-1 to D4-5 checks pass.
Any single failure keeps Phase D closure in BLOCK state.
