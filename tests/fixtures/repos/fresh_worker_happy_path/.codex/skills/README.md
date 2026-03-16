# Canonical Skill Layout

This is the canonical agent-skill root for this project.

## Hard Stop
- Always load skills from `.codex/skills/`.

## Path Resolution Rule
- All paths in skill files are **repo-root relative** (root = fixture repo root).
- When executing validator scripts, ensure working directory is repo root.
- Example: `python .codex/skills/_shared/scripts/validate_closure_packet.py` assumes `pwd` is repo root.

## Structure
- `_shared/`: shared validators
- `project-guider/`: session orchestration
- `saw/`: SAW execution/review skill
- `research-analysis/`: research evidence skill
