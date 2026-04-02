# Phase 6 Tutorials Evidence

- date: 2026-04-01
- python/interpreter: Python 3.14.0 (`C:\Python314\python.exe`)

## Exact Commands Run

```bash
python -m pytest tests/test_phase5_docs.py::test_examples_docs_complete -q
python -m pytest tests/test_phase6_tutorials.py -q
```

## Pytest Count

- examples docs contract: `1 passed`
- Phase 6 tutorial suite: `6 passed`
- Combined targeted checks in this run: `7 passed`

## Phase 6 Tutorial Test Summary

- `test_tutorials_docs_complete`: PASS
- `test_tutorials_have_real_output_blocks`: PASS
- `test_getting_started_links_tutorials_section`: PASS
- `test_troubleshooting_has_min_10_failure_modes`: PASS
- `test_quickstart_helm_uses_local_chart_source`: PASS
- `test_quickstart_container_uses_published_image_convention`: PASS

## Checklist

- [x] 3 tutorial files present:
  - `docs/tutorials/quickstart-container.md`
  - `docs/tutorials/quickstart-helm.md`
  - `docs/tutorials/troubleshooting.md`
- [x] `## Tutorials` section present in `docs/getting-started.md`
- [x] Image convention followed: `ghcr.io/<org>/terminal-zero-governance:latest`
- [x] Helm chart source convention followed: `./charts/terminal-zero-governance`
- [x] Troubleshooting minimum matrix categories remain covered:
  - registry/image access
  - local runtime environment
  - Kubernetes/Helm deployment path
  - governance runtime outcome path
  - rollback/recovery path

## D3 Status

D3 baseline hardening contract remains satisfied with minimum troubleshooting breadth and test-backed tutorial integrity.

**D3 Gate Recommendation:** PASS (subject to closure packet transition).
