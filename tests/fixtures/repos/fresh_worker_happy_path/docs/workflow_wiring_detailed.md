# Workflow Wiring - Detailed

## Session Lifecycle
1. Fresh worker reads AGENTS.md
2. Loads skill registry
3. Routes to appropriate skill

## Validation Chain
- Pre-commit: quick-gate
- Post-work: skill validators
- Phase-end: auditor
