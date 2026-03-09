# Changelog

All notable changes to this repository are documented in this file.

This project is a script-first local governance control plane. Entries focus on repository changes and operator-facing behavior, not hosted service releases.

The format follows Keep a Changelog principles, with a pre-release `Unreleased` section until a tagged public release exists.

## [Unreleased]

### Added

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

### Changed

- `requirements.txt` and `requirements-dev.txt` now act as compatibility shims that point to canonical `pyproject.toml` installs.
- CI install commands in:
  - `.github/workflows/fast-checks.yml`,
  - `.github/workflows/full-test.yml`,
  now install from canonical metadata with constraints.
- `README.md` doc routing now separates public/external docs from internal operator docs and includes a start-here reader map.
- `OPERATOR_LOOP_GUIDE.md` and `GOVERNANCE.md` include thin bridges to clarify README/public quickstart vs deeper internal operator contract details.
