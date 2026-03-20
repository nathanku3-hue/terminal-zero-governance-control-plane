# Changelog

All notable changes to this repository are documented in this file.

This project is a script-first local governance control plane. Entries focus on repository changes and operator-facing behavior, not hosted service releases.

The format follows [Keep a Changelog](https://keepachangelog.com/) principles.

## [0.1.0] - 2026-03-20

### Added

- Unified `sop` CLI entrypoint with subcommands: `startup`, `run`, `validate`, `takeover`, `supervise`, `init`, `version`
- PyPI distribution as `terminal-zero-governance` package
- Cross-platform CI (Windows + Linux; macOS best-effort)
- Automated release validation workflow with semver enforcement and changelog checks
- Trusted Publisher configuration for PyPI publishing (publish only after validation passes)
- `sop init <target-dir>` - Bootstrap a new governed repository with:
  - `docs/context/` and `docs/templates/` directories
  - `.sop/config.yaml` configuration file
  - Generated README pointing to USER_GUIDE
  - `.gitignore` for Python/SOP artifacts
- `USER_GUIDE.md` - User-facing documentation with:
  - What this system is/isn't
  - 1.0 release boundary
  - Installation instructions
  - First 5 minutes workflow
  - Common workflows and troubleshooting
- Release boundary clarity in README and RELEASING.md
- Post-phase git hygiene guardrail (lesson + done checklist check)
- Public beta kernel-completion surface:
  - `KERNEL_FINAL_NORMALIZATION_REPORT.md` and `KERNEL_CLOSURE_MEMO.md` at the root program level
- Canonical project metadata and dependency model in `pyproject.toml` with:
  - runtime dependency: `PyYAML>=6,<7`
  - dev/test extra: `pytest>=8,<10`
- Reproducibility constraints:
  - `constraints.txt` (runtime pin)
  - `constraints-dev.txt` (dev pin + runtime base constraints)
- OSS contributor/community surface:
  - `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SUPPORT.md`, `GOVERNANCE.md`
  - `CODEOWNERS`, `.github/pull_request_template.md`, `.github/ISSUE_TEMPLATE/config.yml`
- Release note draft: `RELEASE_NOTES_v0.1.0_PUBLIC_BETA.md`

### Changed

- Error messages now include actionable suggestions (reinstall hints, next steps)
- `pyproject.toml` now includes package data for scripts and templates
- CI workflows updated with cross-platform matrix strategy
- RELEASING.md updated with PyPI publish instructions (Trusted Publisher flow)
- Kernel completion and rollout proof reflected in shipped control-plane story
- `requirements.txt` and `requirements-dev.txt` now act as compatibility shims pointing to `pyproject.toml`
- CI install commands now install from canonical metadata with constraints
- `README.md` doc routing separates public/external docs from internal operator docs
- `OPERATOR_LOOP_GUIDE.md` and `GOVERNANCE.md` include bridges to clarify README/public quickstart vs internal details

### Fixed

- CLI now uses `importlib.resources` to find scripts/templates in both dev and installed modes
- Wheel smoke test now exercises actual script dispatch (not just `--help`)
- PyPI publish workflow now gated on release-validation success (all validation jobs must pass via `needs:` before publish step)

## [Unreleased]

### Added

- (Future releases will list changes here)
