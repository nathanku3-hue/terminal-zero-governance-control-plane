# Changelog

All notable changes to this repository are documented in this file.

This project is a script-first local governance control plane. Entries focus on repository changes and operator-facing behavior, not hosted service releases.

The format follows Keep a Changelog principles, with a pre-release `Unreleased` section until a tagged public release exists.

## [Unreleased]

### Added

- Public beta kernel-completion surface:
  - `KERNEL_FINAL_NORMALIZATION_REPORT.md` and `KERNEL_CLOSURE_MEMO.md` at the root program level now record kernel closure, normalization, and the explicit rule that future governance changes should be driven by real operating drift rather than planned kernel expansion.
- Canonical project metadata and dependency model in `pyproject.toml` with:
  - runtime dependency: `PyYAML>=6,<7`,
  - dev/test extra: `pytest>=8,<10`.
- Reproducibility constraints:
  - `constraints.txt` (runtime pin),
  - `constraints-dev.txt` (dev pin + runtime base constraints).
- OSS contributor/community surface:
  - `CONTRIBUTING.md`,
  - `CODE_OF_CONDUCT.md`,
  - `SUPPORT.md`,
  - `GOVERNANCE.md`,
  - `CODEOWNERS`,
  - `.github/pull_request_template.md`,
  - `.github/ISSUE_TEMPLATE/config.yml`.
- Release note draft for the first public beta:
  - `RELEASE_NOTES_v0.1.0_PUBLIC_BETA.md`

### Changed

- Kernel completion and rollout proof are now reflected in the shipped control-plane story:
  - Quant loop wiring aligned across agent/skill/operator paths,
  - startup pre-flight contract layer now carries product-directed fields,
  - total-loop dry-build walkthrough exists,
  - Quant, Eureka, and ToolLauncher rollout patterns are validated for their intended repo shapes,
  - root/kernel docs now make canonical vs operational-only boundaries explicit.
- `requirements.txt` and `requirements-dev.txt` now act as compatibility shims that point to canonical `pyproject.toml` installs.
- CI install commands in:
  - `.github/workflows/fast-checks.yml`,
  - `.github/workflows/full-test.yml`,
  now install from canonical metadata with constraints.
- `README.md` doc routing now separates public/external docs from internal operator docs and includes a start-here reader map.
- `OPERATOR_LOOP_GUIDE.md` and `GOVERNANCE.md` include thin bridges to clarify README/public quickstart vs deeper internal operator contract details.
