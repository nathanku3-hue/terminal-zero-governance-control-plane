# Skills Path Policy

Canonical agent-skill source is:
- `.codex/skills/`

`skills/` is reserved for project deliverables and legacy references.

If both locations contain similarly named skills, treat `.codex/skills/` as source of truth.

Worker startup rule:
- load `.codex/skills/README.md` first,
- then resolve requested skill only under `.codex/skills/`,
- never execute mirror `skills/*/SKILL.md` unless explicit emergency fallback is requested.
