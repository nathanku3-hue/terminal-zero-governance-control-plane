# Terminal Zero User Guide

**For new users.** If you are a maintainer, see `CONTRIBUTING.md` and `docs/loop_operating_contract.md`.

---

## What Is This?

Terminal Zero is a **governance control plane** for AI-assisted engineering work.

It helps you:

- Turn vague AI tasks into explicit, checkable work
- Run that work inside a bounded process
- Leave behind evidence that another human or agent can trust

It is **not**:

- A hosted agent platform
- A consumer chat product
- A zero-human autopilot

You stay in control. The system provides structure.

---

## What Problem Does It Solve?

Most AI engineering fails for one of these reasons:

1. The task is unclear
2. The authority boundary is unclear
3. Execution happens in chat instead of in artifacts
4. "Done" is asserted without verification
5. Handoff is weak
6. Nobody can explain what happened afterward

Terminal Zero solves these in order through a **governance loop**:

```
startup → run → validate → takeover
```

Each step produces artifacts. Each artifact is inspectable. Each handoff is deterministic.

---

## What Is Shipped (1.0)

**Included:**

- `sop` CLI with subcommands: `startup`, `run`, `validate`, `takeover`, `supervise`, `init`
- Kernel templates for truth surfaces
- Startup → run → validate → takeover loop
- PyPI install path

**Supported platforms:**

- Python 3.12+
- Windows, Linux (macOS best-effort)

**Not promised (future work):**

- Hosted service
- npm/npx scaffolding
- GitHub Action
- VS Code extension
- Zero-human autopilot

---

## Installation

### Prerequisites

- Python 3.12 or later
- pip

### Install

```bash
pip install terminal-zero-governance
```

### Verify

```bash
sop --help
sop version
```

You should see the usage help and version number.

---

## First 5 Minutes

### 1. Initialize a new governed repository

```bash
sop init my-project
cd my-project
```

This creates:

```
my-project/
  docs/
    context/       # Generated artifacts go here
    templates/     # Kernel templates
  .sop/
    config.yaml    # Governance configuration
  README.md        # Project README
  .gitignore
```

### 2. Start a round

```bash
sop startup --repo-root .
```

This creates startup artifacts under `docs/context/`:
- `startup_intake_latest.md` — your intent for this round
- `init_execution_card_latest.md` — concise execution card

### 3. Run the loop

```bash
sop run --repo-root . --skip-phase-end
```

This executes one bounded loop pass and refreshes:
- `loop_cycle_summary_latest.md` — what happened
- `exec_memory_packet_latest.md` — current state

### 4. Validate readiness

```bash
sop validate --repo-root .
```

This checks closure readiness. Exit codes:
- `0` = `READY_TO_ESCALATE`
- `1` = `NOT_READY`
- `2` = input/infra error

### 5. Get takeover guidance

```bash
sop takeover --repo-root .
```

This prints deterministic next-step guidance for the next operator or agent.

---

## Common Workflows

### Starting fresh

```bash
sop init my-project
cd my-project
sop startup --repo-root .
sop run --repo-root . --skip-phase-end
sop validate --repo-root .
```

### Continuing an existing round

```bash
cd existing-project
sop takeover --repo-root .    # Read where you left off
sop run --repo-root .         # Continue
sop validate --repo-root .    # Check readiness
```

### Supervising a long-running loop

```bash
sop supervise --repo-root . --max-cycles 5 --check-interval-seconds 60
```

### Minimal init (no templates)

```bash
sop init my-project --minimal
```

Creates structure without copying templates. Useful when you already have templates elsewhere.

---

## The Main Loop Explained

### startup

Captures your intent before work begins.

**What it produces:**
- Startup intake (your goals, non-goals, done-when)
- Init execution card (concise summary)
- Round contract seed (prefilled checks)

**Key questions you answer:**
- What is the product problem this round?
- What is out of scope?
- What does "done" look like?

### run

Executes one bounded pass.

**What it does:**
- Refreshes execution artifacts
- Runs truth checks
- Updates loop summary

**What it produces:**
- Loop cycle summary
- Exec memory packet
- Closure support artifacts

### validate

Checks if the work is ready.

**What it checks:**
- Artifact freshness
- Closure criteria
- Evidence completeness

**Exit codes tell you:**
- `0` — Ready to escalate
- `1` — Not ready (see output for why)
- `2` — Input/infra error

### takeover

Prints guidance for the next step.

**What it gives you:**
- Current state summary
- Recommended next action
- Handoff artifacts

---

## `sop init` Details

### Full mode (default)

```bash
sop init my-project
```

Creates:
- `docs/context/` — artifact directory
- `docs/templates/` — 10 kernel templates copied
- `.sop/config.yaml` — governance config
- `README.md` — generated, points to this guide
- `.gitignore`

### Minimal mode

```bash
sop init my-project --minimal
```

Creates:
- `docs/context/` — artifact directory
- `.sop/config.yaml` — governance config
- `README.md`
- `.gitignore`

Skips template copying. Use when you have templates elsewhere or want a lighter start.

### Generated structure

```
my-project/
├── docs/
│   ├── context/              # Generated artifacts
│   │   ├── startup_intake_latest.md
│   │   ├── loop_cycle_summary_latest.md
│   │   └── ...
│   └── templates/            # (full mode only)
│       ├── bridge_contract_template.md
│       ├── done_checklist_template.md
│       └── ...
├── .sop/
│   └── config.yaml           # Governance configuration
├── README.md
└── .gitignore
```

---

## Troubleshooting

### `sop: command not found`

Make sure you installed the package:

```bash
pip install terminal-zero-governance
sop --help
```

If using a virtual environment, ensure it's activated.

### `Script not found: .../scripts/xyz.py`

You're running `sop` from outside the installed package context. Make sure you:
1. Installed via pip, or
2. Are in the repository root with `pip install -e .`

### `Error: Target directory already exists`

`sop init` refuses to overwrite. Choose a different directory name or remove the existing one.

### `validate` returns NOT_READY

Run `sop validate --repo-root .` and read the output. It will tell you which criteria failed.

Common causes:
- Artifacts are stale (run `sop run` first)
- Missing required files (run `sop startup` first)
- Closure checks failing (fix the underlying issues)

### Tests fail after installation

Make sure you're using Python 3.12+:

```bash
python --version
```

---

## Compatibility Paths

If you have existing scripts or workflows that call the old entrypoints directly, they still work:

```bash
python scripts/startup_codex_helper.py --repo-root .
python scripts/run_loop_cycle.py --repo-root .
python scripts/validate_loop_closure.py --repo-root .
python scripts/print_takeover_entrypoint.py --repo-root .
python scripts/supervise_loop.py --repo-root .
```

These are preserved for backward compatibility. New users should prefer `sop <command>`.

---

## Reference

### Commands

| Command | Purpose |
|---------|---------|
| `sop startup` | Initialize a round |
| `sop run` | Execute one loop cycle |
| `sop validate` | Check closure readiness |
| `sop takeover` | Print takeover guidance |
| `sop supervise` | Monitor loop health |
| `sop init` | Bootstrap new governed repo |
| `sop version` | Print version |

### Exit Codes (validate)

| Code | Meaning |
|------|---------|
| 0 | READY_TO_ESCALATE |
| 1 | NOT_READY |
| 2 | Input/infra error |

---

## Getting Help

- **Issues:** https://github.com/terminal-zero/sop/issues
- **Documentation:** This guide + `README.md`
- **Contributing:** See `CONTRIBUTING.md`
