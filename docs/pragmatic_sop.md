# Pragmatic SOP (中英双语 / CN-EN)

Status: Active  
Scope: Governance and operator behavior (docs/process only)  
Authority: Advisory process contract; does not add runtime control-plane gates.

## Five Rules (CN/EN)

1) **大改先审变更清单，再写代码**  
   **Big changes require change-manifest review before coding.**  
   - Trigger: cross-module change, architecture-impacting change, or high-risk/one-way change.
   - Artifact: `docs/templates/change_manifest_template.md` copied into working docs context.

2) **只维护一个逻辑主干索引**  
   **Maintain one canonical logic-spine index.**  
   - Canonical file: `docs/logic_spine_index.md`.
   - Any new major logic branch must be registered there first.

3) **主理人负责治理，不负责实现与评审**  
   **Principal/main orchestrator governs but does not code/review.**  
   - Orchestrator sets boundaries, owners, and acceptance checks.
   - Implementation and review execution stay with delegated workers/reviewers.

4) **文档分层并有生命周期**  
   **Docs have lifecycle tiers.**  
   - Tier A (canonical): long-lived contracts and indexes.
   - Tier B (operational): round/phase docs that evolve with milestones.
   - Tier C (ephemeral): generated snapshots and convenience mirrors.

5) **AI仅在显式模块边界与非目标约束内编码**  
   **AI codes only inside explicit module boundaries and non-goals.**  
   - Require explicit `OWNED_FILES`, `INTERFACE_INPUTS`, `INTERFACE_OUTPUTS`, and `NON_GOALS`.
   - Out-of-bound changes must be routed back to planning/manifest review first.

## Minimal Adoption Flow

1. For big changes, fill a change manifest before coding.
2. Register/update affected line in `docs/logic_spine_index.md`.
3. Confirm orchestrator role remains governance-only.
4. Classify docs touched by lifecycle tier.
5. Keep execution inside declared module boundaries/non-goals.
