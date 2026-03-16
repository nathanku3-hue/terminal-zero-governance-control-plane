# AGENTS.md

> SYSTEM CONTEXT: Fixture repo for fresh worker navigation testing
> ROOT PATH: tests/fixtures/repos/fresh_worker_happy_path

## 0. Navigation Hub

**Fresh Worker Start**: Read this file first, then load `.codex/skills/README.md` (skill registry).

**Path Resolution Rule**: All paths in AGENTS.md and skill files are **repo-root relative** (root = fixture repo root). Validator scripts must be executed with repo root as the working directory.

**Deep Dives Available**:
- [Tech Stack & Constraints](docs/tech_stack.md)
- [Workflow Wiring](docs/workflow_wiring_detailed.md)

## 1. Quick Start

**Primary Entrypoints**:
- `scripts/startup_codex_helper.py` - Initialize a round

## 2. Directory Map

- `scripts/` - Control plane orchestration only
- `docs/context/` - Authoritative `_latest` artifacts
- `.codex/skills/` - Canonical skill definitions

## 3. Workflow Wiring

### Session Lifecycle
```
Fresh Worker Start
    ↓
Read AGENTS.md (this file)
    ↓
Load .codex/skills/README.md
    ↓
$project-guider activated
    ↓
Load context: project_init_latest.md
```

### Skill Activation Matrix

| Skill | Trigger | Validator |
|-------|---------|-----------|
| project-guider | Session start | N/A |
| saw | Workflow invoked | validate_saw_report_blocks.py |
| research-analysis | Workflow invoked | validate_research_claims.py |
