# Operator Onboarding Checklist

End-to-end first-run guide for a new operator on a clean machine.
All commands use the primary `sop` CLI path.

## Prerequisites

- [ ] Python 3.12+ installed: `python --version` must show 3.12.x or higher
- [ ] pip available: `pip --version` exits 0
- [ ] Repository cloned to local machine

## Install

- [ ] `pip install terminal-zero-governance==0.1.0`
- [ ] Verify: `sop run --help` exits 0 and shows usage

## First Run

- [ ] `sop run --repo-root <path-to-repo>`
- [ ] Read `docs/context/loop_cycle_summary_latest.json` → `final_result`
  - `READY_TO_ESCALATE`: read `docs/context/next_round_handoff_latest.json`
  - `NOT_READY`: go to Gate HOLD section of `docs/context/operator_navigation_map.md`
  - Non-zero exit: go to Failure Triage below

## Failure Triage

- [ ] Read `docs/context/run_failure_latest.json`
- [ ] Check `failure_class` and `error_code`
- [ ] Navigate to `docs/context/operator_navigation_map.md` → Failure State Decision Tree
- [ ] Find your `failure_class` row and follow the action

## Skills Status

- [ ] Read `runtime.steps` in `loop_cycle_summary_latest.json`
- [ ] Find entry with `"step": "skill_resolution"` → check `skills_status`
- [ ] Navigate to `docs/context/skill_readiness_matrix.md` for routing

## Verification

- [ ] `sop run` exits 0 on healthy repo
- [ ] `run_failure_latest.json` present and contains `error_code` on non-zero exit
- [ ] All referenced docs use relative paths (no drive letters)
