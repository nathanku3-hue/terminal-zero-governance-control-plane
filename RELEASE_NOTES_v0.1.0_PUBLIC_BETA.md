# v0.1.0 — Public Beta

Release owner: `<fill before publish>`

## What It Is

The first public beta of the Terminal Zero governance kernel.

This release ships `quant_current_scope/` as a script-first, repo-native control plane for AI-assisted engineering work.

## What It Proves

- A bounded `startup -> planning -> execution -> closure -> takeover` loop
- Activation-gated kernel artifacts instead of always-on ceremony
- Planner-first entry from small current-truth packets
- Worker -> planner return through refreshed bridge/planner/evidence surfaces
- Repo-shape-specific rollout patterns:
  - Quant as mature multi-stream
  - Eureka as single-stream planner-first
  - ToolLauncher as minimal-subset single-stream

## Release Boundary

This beta ships the `quant_current_scope/` surface only.

That includes:
- `scripts/startup_codex_helper.py`
- `scripts/run_loop_cycle.py`
- `scripts/validate_loop_closure.py`
- `scripts/print_takeover_entrypoint.py`
- `scripts/supervise_loop.py`
- supporting operator docs, tests, and artifact contracts for that flow

The root `SOP/` repository remains canonical kernel/program/history truth for maintainers. It is not the primary shipped product entry.

## Validation Snapshot

- Quant: validated for the intended mature multi-stream shape
- Eureka: validated for the intended planner-first subset after current-truth freshness repair
- ToolLauncher: validated for the intended minimal subset in a real smoke/maintenance round

Release-candidate validation commands run from `quant_current_scope/`:

```powershell
python scripts/startup_codex_helper.py --help
python scripts/run_loop_cycle.py --help
python scripts/supervise_loop.py --max-cycles 1
python scripts/run_fast_checks.py --repo-root .
python -m pytest -q
```

## What It Does Not Promise

- A hosted agent platform
- Zero-human autopilot
- Universal rollout to every repo shape
- Fully automated freshness of all repo-local operational surfaces
- Automatic expansion of the governance kernel without new real-use drift evidence

## Known Limitations

- Some repo-local operational surfaces still rely on manual freshness discipline.
- Eureka current-truth surfaces remain repo-local operational truth rather than version-controlled canonical repo truth.
- Downstream repos may still carry local working changes unrelated to the kernel decision.

## Operator Framing

Use this beta when you want:
- explicit startup boundaries,
- bounded execution,
- mechanical closure checks,
- deterministic takeover,
- and a repo-native governance surface instead of chat-only execution.

Do not use this beta as if it were:
- a hosted fleet product,
- a permissionless automation layer,
- or a replacement for human direction and approval.
