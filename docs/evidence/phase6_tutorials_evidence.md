# Phase 6 Tutorials Evidence

- date: 2026-03-31
- python/interpreter: Python 3.14.0 (`C:\Python314\python.exe`)

## Exact Commands Run

```bash
python -m pytest tests/test_phase6_tutorials.py -q -x
python -m pytest tests/test_phase6_tutorials.py -q
python -m pytest -q
python --version && python -c "import sys; print(sys.executable)"
```

## Pytest Count

- Targeted Phase 6 tutorial suite: `6 passed`
- Full suite: collection interrupted with `1 error` in unrelated `tests/test_phase8_ga_readiness.py` (`ModuleNotFoundError: No module named 'sop.phase8_ga_readiness'`)

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
- [x] `## Tutorials` section added to `docs/getting-started.md`
- [x] Image convention followed: `ghcr.io/<org>/terminal-zero-governance:latest`
- [x] Helm chart source convention followed: `./charts/terminal-zero-governance`

## Notes

- Tutorials include required locked headers per file.
- Each tutorial contains concrete fenced output under `## Output`.
- Troubleshooting contains 10 failure modes with exact `Symptom`, `Likely cause`, `Check`, `Fix` structure.
