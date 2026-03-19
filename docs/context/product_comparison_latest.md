# Product Comparison (Authoritative Working Copy)

Authority: advisory-only authoritative working copy  
Purpose: record which researched products and patterns to copy, modify on top, or reject before implementation.  
Current state: combines the original Phase 5 reference snapshot with external ecosystem research and a third harness/governance research round on 2026-03-18.

## Header
- `COMPARISON_ID`: `20260318-phase5-reference-products-round2`
- `OWNER`: `PM`
- `DATE_UTC`: `2026-03-18T06:34:46.4299050Z`
- `SCOPE`: `Phase 5 and adjacent product-architecture comparison for orchestration, skills/plugins, delegation UX, and endgame shape`
- `PRIMARY_OBJECTIVE`: `Import useful product and technical patterns without importing authority violations, silent policy mutation, permissionless automation, or marketplace drift.`
- `NON_GOALS`: `This artifact does not approve implementation by itself and does not replace PM/CEO review for policy or control-plane changes.`
- `REVIEW_TRIGGER`: `architecture_choice`

## Comparison Lens
- `TRANSFER_BOUNDARY`: `Reuse pragmatic implementation and operator patterns, but keep repo-specific authority, audit, and advisory-only governance semantics intact.`
- `AUTHORITY_NOTE`: `Advisory only; final implementation and policy decisions still follow the normal PM/CEO approval path.`
- `SOURCE_ACCESS_NOTES`: `The two referenced X posts could not be retrieved in this environment, and the BestBlogs article rendered as a client-side loading shell. Conclusions below rely on accessible repo sources and clearly mark inaccessible references.`

## Round 1: Phase 5 Internal Reference Snapshot

### PRODUCT_1: `Goose`
- `WHY_RESEARCHED`: `Skills packaging, extension gating, and benchmarking patterns are directly relevant to the Phase 5 target shape.`
- `TECHNICAL_PERSPECTIVE`
  - `COPY`:
    - `Skills packaging`
    - `Extension allowlists`
    - `Model benchmarking`
  - `MODIFY_ON_TOP`:
    - `Lead/worker routing -> must respect existing authority and approval boundaries`
    - `Recipes -> must stay advisory rather than becoming an execution authority path`
  - `REJECT`:
    - `Dynamic extension loading that bypasses policy approval`
- `PRODUCT_PERSPECTIVE`
  - `COPY`:
    - `A visible skills surface that helps operators understand available capabilities`
  - `MODIFY_ON_TOP`:
    - `Capability discovery -> keep small and governance-aligned instead of becoming a plugin buffet`
  - `REJECT`:
    - `Any operator promise that implies unreviewed extensions are safe by default`
- `EVIDENCE_PATHS`:
  - `../../../docs/archive/program_history/phase5/phase5_pm_architecture_handoff.md`
- `OPEN_RISKS`: `Extension surfaces must remain explicit and allowlist-based as implementation proceeds.`

### PRODUCT_2: `OpenHands`
- `WHY_RESEARCHED`: `Execution sandboxing and GitHub automation patterns are useful reference points for an implementation-oriented agent surface.`
- `TECHNICAL_PERSPECTIVE`
  - `COPY`:
    - `Sandboxed execution`
    - `GitHub automation`
  - `MODIFY_ON_TOP`:
    - `Issue-to-PR workflows -> must include auditor review and existing governance checks`
  - `REJECT`:
    - `Headless always-approve semantics`
- `PRODUCT_PERSPECTIVE`
  - `COPY`:
    - `Tight execution loop around real repo work`
  - `MODIFY_ON_TOP`:
    - `Automation UX -> expose boundaries and review steps instead of hiding them`
  - `REJECT`:
    - `A product feel that encourages operators to hand over authority invisibly`
- `EVIDENCE_PATHS`:
  - `../../../docs/archive/program_history/phase5/phase5_pm_architecture_handoff.md`
- `OPEN_RISKS`: `Automation convenience must not erode human approval or auditor review boundaries.`

### PRODUCT_3: `Aider`
- `WHY_RESEARCHED`: `Repo map compression and lint/test repair loops are directly useful implementation patterns.`
- `TECHNICAL_PERSPECTIVE`
  - `COPY`:
    - `Repo map compression`
    - `Lint/test repair loop`
  - `MODIFY_ON_TOP`:
    - `NONE`
  - `REJECT`:
    - `Treating the coding loop as sufficient governance`
- `PRODUCT_PERSPECTIVE`
  - `COPY`:
    - `A simple “fix the repo” interaction style`
  - `MODIFY_ON_TOP`:
    - `Fast repair UX -> keep subordinate to explicit closure criteria`
  - `REJECT`:
    - `Any product framing where coding velocity is mistaken for governance quality`
- `EVIDENCE_PATHS`:
  - `../../../docs/archive/program_history/phase5/phase5_pm_architecture_handoff.md`
- `OPEN_RISKS`: `Keep repair loops subordinate to governance and closure criteria instead of treating them as self-justifying.`

### PRODUCT_4: `LangChain`
- `WHY_RESEARCHED`: `Memory ownership and worker isolation patterns are relevant to hierarchical memory work.`
- `TECHNICAL_PERSPECTIVE`
  - `COPY`:
    - `Supervisor-owned memory`
    - `Stateless workers`
    - `Context isolation`
  - `MODIFY_ON_TOP`:
    - `NONE`
  - `REJECT`:
    - `Generic graph complexity before policy stabilizes`
- `PRODUCT_PERSPECTIVE`
  - `COPY`:
    - `A clear distinction between central coordination and delegated execution`
  - `MODIFY_ON_TOP`:
    - `Workflow visualizations -> only after the underlying policy and authority model stay simple`
  - `REJECT`:
    - `Graph-first product complexity that exceeds operator maturity`
- `EVIDENCE_PATHS`:
  - `../../../docs/archive/program_history/phase5/phase5_pm_architecture_handoff.md`
- `OPEN_RISKS`: `Avoid importing graph machinery that exceeds the current policy and operator maturity.`

### PRODUCT_5: `Promptfoo`
- `WHY_RESEARCHED`: `Eval/config patterns are directly relevant to benchmark harness and policy proposal work.`
- `TECHNICAL_PERSPECTIVE`
  - `COPY`:
    - `Config/assertion matrix`
    - `Target-specific policy generation`
  - `MODIFY_ON_TOP`:
    - `Adaptive guardrails -> require explicit human approval for any policy change`
  - `REJECT`:
    - `Auto-updating policy without review`
- `PRODUCT_PERSPECTIVE`
  - `COPY`:
    - `A visible evidence surface for eval-driven decisions`
  - `MODIFY_ON_TOP`:
    - `Policy suggestion UX -> make recommendations legible without implying auto-enforcement`
  - `REJECT`:
    - `A product feel where scores silently rewrite behavior`
- `EVIDENCE_PATHS`:
  - `../../../docs/archive/program_history/phase5/phase5_pm_architecture_handoff.md`
- `OPEN_RISKS`: `Benchmark feedback must stay evidence-producing rather than policy-mutating by itself.`

### PRODUCT_6: `Inspect`
- `WHY_RESEARCHED`: `Eval object model and sandboxing patterns are useful low-risk reference points for evaluation infrastructure.`
- `TECHNICAL_PERSPECTIVE`
  - `COPY`:
    - `Eval object model`
    - `Docker sandboxing`
    - `Tool-based eval`
  - `MODIFY_ON_TOP`:
    - `NONE`
  - `REJECT`:
    - `NONE`
- `PRODUCT_PERSPECTIVE`
  - `COPY`:
    - `Low-drama, infrastructure-first evaluation surfaces`
  - `MODIFY_ON_TOP`:
    - `Operator exposure -> keep lean rather than over-productizing internal eval plumbing`
  - `REJECT`:
    - `NONE`
- `EVIDENCE_PATHS`:
  - `../../../docs/archive/program_history/phase5/phase5_pm_architecture_handoff.md`
- `OPEN_RISKS`: `NONE`

### PRODUCT_7: `OpenAI`
- `WHY_RESEARCHED`: `Simple-evals provides a lean seed for baseline eval structure.`
- `TECHNICAL_PERSPECTIVE`
  - `COPY`:
    - `Simple-evals as baseline seed`
  - `MODIFY_ON_TOP`:
    - `NONE`
  - `REJECT`:
    - `NONE`
- `PRODUCT_PERSPECTIVE`
  - `COPY`:
    - `A minimal baseline before adding more complexity`
  - `MODIFY_ON_TOP`:
    - `Operator visibility -> expose just enough to support decisions`
  - `REJECT`:
    - `NONE`
- `EVIDENCE_PATHS`:
  - `../../../docs/archive/program_history/phase5/phase5_pm_architecture_handoff.md`
- `OPEN_RISKS`: `Keep the seed lean and repo-specific rather than growing a second evaluation control plane.`

## Round 1 Synthesis
- `TECHNICAL_KEEP_THESE_PATTERNS`: `allowlist-based extension control, sandboxed execution, benchmark and eval harnesses, repo-map compression, supervisor-owned memory, stateless workers, context isolation, and tool-based evaluation`
- `PRODUCT_KEEP_THESE_PATTERNS`: `simple capability discovery, clear separation between coordination and execution, and evidence-visible benchmarking`
- `DO_NOT_IMPORT`: `always-approve execution semantics, auto-updating policy, generic graph complexity before policy stabilizes, and any pattern that treats the coding loop as sufficient governance`
- `BIGGEST_DECISION_RISK`: `Importing strong implementation patterns without preserving the repo's human approval and authority boundaries`
- `NEXT_ACTION`: `Use this internal reference set as the baseline and compare newer products against it from both technical and product/operator lenses.`

## Round 2: External Ecosystem Research (2026-03-18)

### PRODUCT_8: `paperclipai/paperclip`
- `WHY_RESEARCHED`: `Paperclip is a visible example of orchestration shifting from single-agent coding into a business/control-plane product.`
- `TECHNICAL_PERSPECTIVE`
  - `COPY`:
    - `Control-plane invariants such as atomic task checkout, budget enforcement, persistent agent state, and approval gates with rollback`
    - `Goal ancestry carried with tasks so execution stays tied to intent`
    - `Company-scoped isolation and explicit separation between operator access and agent execution`
  - `MODIFY_ON_TOP`:
    - `Runtime skill injection -> allow context/workflow injection, but never silent policy mutation`
    - `Full-control operator context -> remap to the repo's PM/CEO and advisory-vs-authoritative boundaries`
  - `REJECT`:
    - `Adopting a full hosted Node server + React dashboard as the primary technical center of gravity unless the product explicitly pivots into a hosted orchestrator`
- `PRODUCT_PERSPECTIVE`
  - `COPY`:
    - `“Manage business goals, not pull requests” as a north-star framing`
    - `One-screen control-plane UX: org chart, goals, budgets, governance, and agent coordination in one place`
  - `MODIFY_ON_TOP`:
    - `Zero-human-company promise -> keep the ambition, but pair it with explicit human-required gates and stop conditions`
    - `Dashboard monitoring -> show advisory and authoritative lanes separately so visibility is not mistaken for approval`
  - `REJECT`:
    - `A product promise that implies the operator should disappear`
    - `Clipmart-style one-click company imports for governance-critical surfaces before approval and compatibility rules exist`
- `EVIDENCE_PATHS`:
  - `https://github.com/paperclipai/paperclip`
- `OPEN_RISKS`: `The product can over-invite hosted-orchestrator scope and autonomy overclaim if imported naively.`

### PRODUCT_9: `gsd-build/get-shit-done`
- `WHY_RESEARCHED`: `GSD is a current example of spec-driven, multi-runtime workflow scaffolding explicitly marketed as solving context rot.`
- `TECHNICAL_PERSPECTIVE`
  - `COPY`:
    - `File-backed state and planning artifacts rather than chat-only persistence`
    - `Thin orchestrator with planner/researcher/checker/executor/verifier role split`
    - `A real discuss -> plan -> execute -> verify loop with requirement-to-verification mapping`
    - `Atomic commits per task so work is reversible and auditable`
  - `MODIFY_ON_TOP`:
    - `Fresh-context strategy -> enforce via role-based artifact routing and bounded packets, not by assuming bigger contexts solve everything`
    - `Quick mode -> keep the speed, but preserve explicit closure semantics when work matters`
  - `REJECT`:
    - `Permissionless default automation`
    - `Skip-permissions posture as intended mode`
- `PRODUCT_PERSPECTIVE`
  - `COPY`:
    - `Few-command onboarding and install flow`
    - `A workflow that feels like a practical operating system rather than a bag of prompts`
    - `A strong brownfield onramp such as map-the-codebase-first`
  - `MODIFY_ON_TOP`:
    - `“If you know clearly what you want, this WILL build it for you” -> keep the confidence, but add explicit distrust-by-default for authority, permissions, and external side effects`
    - `Human verification -> encode as authoritative closure artifacts rather than just a narrative step`
  - `REJECT`:
    - `Trust-the-workflow messaging that weakens approval awareness`
- `EVIDENCE_PATHS`:
  - `https://github.com/gsd-build/get-shit-done`
- `OPEN_RISKS`: `The strongest upside is workflow shape; the strongest downside is permission posture inversion.`

### PRODUCT_10: `FradSer/dotclaude`
- `WHY_RESEARCHED`: `dotclaude is a live example of a plugin/skills marketplace plus multi-agent review surface for a coding-agent environment.`
- `TECHNICAL_PERSPECTIVE`
  - `COPY`:
    - `Manifested plugin structure, marketplace metadata, and explicit install surfaces`
    - `Hard tool-boundary conventions and validation-oriented packaging`
    - `Hierarchical and selective multi-agent review modes`
  - `MODIFY_ON_TOP`:
    - `Plugin marketplace model -> keep package discipline, but constrain distribution for governance-critical skills to an allowlisted, repo-controlled path`
    - `Multi-agent review -> keep advisory unless explicitly wired into existing auditor and approval gates`
  - `REJECT`:
    - `Third-party plugin sprawl without a strong approval and compatibility story`
    - `Letting plugin validation stand in for policy review`
- `PRODUCT_PERSPECTIVE`
  - `COPY`:
    - `Marketplace mental model for discovering extensions`
    - `Install-by-name UX for optional capability layers`
    - `Review superpowers as a visible operator capability`
    - `First-class user-invocable commands that package a capability bundle instead of exposing raw prompts`
  - `MODIFY_ON_TOP`:
    - `Plugin catalog -> provide a very small recommended set and compatibility notes instead of a buffet`
    - `Review product surface -> separate “analysis complete” from “approved to proceed”`
  - `REJECT`:
    - `A product feel where plugin abundance becomes the value proposition`
- `EVIDENCE_PATHS`:
  - `https://github.com/FradSer/dotclaude/`
- `OPEN_RISKS`: `Marketplace UX is strong, but governance-critical capabilities should not depend on external catalog drift.`

### PRODUCT_11: `msitarzewski/agency-agents`
- `WHY_RESEARCHED`: `agency-agents shows a broad specialist-roster model with multi-tool conversion and installation scripts.`
- `TECHNICAL_PERSPECTIVE`
  - `COPY`:
    - `Single-source agent definitions with conversion/install pipelines across runtimes`
    - `Explicit tool-specific install targets and scripts`
  - `MODIFY_ON_TOP`:
    - `Agent portability -> keep the portability tooling, but restrict the core set to a small governance-aligned roster`
    - `Agent definitions -> prioritize contracts, deliverables, and verification over personality bulk`
  - `REJECT`:
    - `Treating a large agent library as a replacement for the control plane`
    - `Using prompt mass or personality volume as the memory system`
- `PRODUCT_PERSPECTIVE`
  - `COPY`:
    - `Curated specialist roster with predictable deliverables`
    - `A delegation UX where the operator can pick the right specialist for the job`
  - `MODIFY_ON_TOP`:
    - `Roster experience -> reduce to a small default team with clear default lanes`
    - `Identity/personality -> keep as optional garnish, not the core trust surface`
  - `REJECT`:
    - `Personality-first branding as the primary product value`
    - `Agent sprawl that increases cognitive load and configuration risk`
- `EVIDENCE_PATHS`:
  - `https://github.com/msitarzewski/agency-agents/`
- `OPEN_RISKS`: `The portability idea is strong, but the library size and personality emphasis can overwhelm the real control plane.`

### PRODUCT_12: `Referenced X posts and BestBlogs article`
- `WHY_RESEARCHED`: `These references may contain current product/operator takes adjacent to the repo ecosystem above.`
- `TECHNICAL_PERSPECTIVE`
  - `COPY`:
    - `NONE_YET`
  - `MODIFY_ON_TOP`:
    - `NONE_YET`
  - `REJECT`:
    - `Making technical conclusions from unreadable or inaccessible sources`
- `PRODUCT_PERSPECTIVE`
  - `COPY`:
    - `NONE_YET`
  - `MODIFY_ON_TOP`:
    - `NONE_YET`
  - `REJECT`:
    - `Treating inaccessible social or client-rendered content as if it were verified evidence`
- `EVIDENCE_PATHS`:
  - `https://x.com/trq212/status/2033949937936085378`
  - `https://x.com/nash_su/status/2033806469796167758`
  - `https://www.bestblogs.dev/article/a39df55f`
- `OPEN_RISKS`: `These sources remain unresolved and should be revisited only when retrievable.`

## Round 2 Synthesis
- `TECHNICAL_KEEP_THESE_PATTERNS`: `thin orchestrator plus delegated specialists, explicit artifact-backed state, goal-linked execution, atomic execution/budget rules, atomic commits, portable agent packaging, and validation-oriented install surfaces`
- `PRODUCT_KEEP_THESE_PATTERNS`: `one-screen control plane, manage-goals-not-PRs framing, few-command onboarding, curated specialist delegation, and visible review/verification surfaces`
- `DO_NOT_IMPORT`: `permissionless automation, zero-human default positioning, plugin marketplace sprawl, personality-first agent libraries, and any surface where visibility is mistaken for approval`
- `BIGGEST_DECISION_RISK`: `Letting attractive autonomy UX outrun the system's authority model and safety posture`
- `NEXT_ACTION`: `Build the smallest integrated control-plane product that keeps the Paperclip goal layer, the GSD workflow discipline, the dotclaude packaging discipline, and the agency-agents specialist portability idea without inheriting their scope or trust-model excesses.`

## Round 3: Harness, Skills Governance, Spec Workflow, and Observability

### PRODUCT_13: `Architecture evolution and selection ladder`
- `WHY_RESEARCHED`: `This source cluster is useful because it frames architecture choices as compensations for specific model deficits rather than status symbols.`
- `TECHNICAL_PERSPECTIVE`
  - `COPY`:
    - `A clear escalation ladder: Single Agent -> Skills -> Multi-Agent -> Teams`
    - `Treat communication bandwidth, routing accuracy, and context fragmentation as explicit architecture constraints`
    - `Use Teams only as an uncertainty mode for parallel exploration`
  - `MODIFY_ON_TOP`:
    - `Escalation ladder -> encode as a governance decision contract tied to risk tier, uncertainty level, and closure requirements`
    - `Skills -> package not only knowledge but also policy, verification steps, and templates`
  - `REJECT`:
    - `Treating benchmark heuristics like the 45 percent threshold as hard law`
    - `Treating RAG as obsolete rather than complementary`
- `PRODUCT_PERSPECTIVE`
  - `COPY`:
    - `A simple “start simple and escalate only when necessary” product story`
  - `MODIFY_ON_TOP`:
    - `Expose the ladder as an operator policy choice rather than hidden backend magic`
  - `REJECT`:
    - `Architecture complexity as a product selling point`
- `EVIDENCE_PATHS`:
  - `thread source: Agent/Skills/Teams 架构演进过程及技术选型之道`
- `OPEN_RISKS`: `If the escalation ladder stays implicit, teams will drift into multi-agent and team modes too early.`

### PRODUCT_14: `OpenClaw observability and runtime evidence plane`
- `WHY_RESEARCHED`: `This source cluster makes the strongest case that “controlled run” must be mechanically answerable, not assumed.`
- `TECHNICAL_PERSPECTIVE`
  - `COPY`:
    - `A canonical session audit log for user -> assistant -> toolCall -> toolResult -> assistant chains`
    - `Separate behavior audit logs from application runtime logs`
    - `OTel-first metrics and traces for token burn, stuck sessions, latency, and tool failure rates`
    - `A stable session or thread correlation key across all telemetry`
  - `MODIFY_ON_TOP`:
    - `Behavior logging -> redact or suppress sensitive tool results by default`
    - `Cost telemetry -> feed budget caps and escalation behavior, not just dashboards`
    - `Skill activation -> emit auditable activation and under-triggering events`
  - `REJECT`:
    - `Treating observability as a substitute for preventive controls`
    - `Vendor-specific backend choices as architecture`
    - `Logging raw tool results indiscriminately`
- `PRODUCT_PERSPECTIVE`
  - `COPY`:
    - `The product should be able to answer who triggered the run, what it did, and what it cost`
  - `MODIFY_ON_TOP`:
    - `Turn dashboards into evidence views, not approval surfaces`
  - `REJECT`:
    - `A product pitch that implies the run is controlled without behavioral evidence`
- `EVIDENCE_PATHS`:
  - `thread source: 以 OpenClaw 为案例，从行业威胁态势与运行时防护的固有局限出发`
- `OPEN_RISKS`: `Audit logs can become a new exfiltration surface if redaction is weak.`

### PRODUCT_15: `Open SWE as harness blueprint`
- `WHY_RESEARCHED`: `Open SWE is a useful reference for internal coding-agent framework seams and where to draw the line between framework and product.`
- `TECHNICAL_PERSPECTIVE`
  - `COPY`:
    - `Composable harness over a maintained agent foundation`
    - `One task or thread per isolated workspace`
    - `Curated tool registry with deliberate extension points`
    - `Deterministic middleware for must-happen behaviors`
    - `Stable thread identity for follow-up routing`
  - `MODIFY_ON_TOP`:
    - `Sandbox permissions -> risk-tiered, not default-full`
    - `Context hydration -> progressive disclosure instead of large injected manuals`
    - `PR safety nets -> subordinate to explicit closure criteria`
  - `REJECT`:
    - `Assuming sandboxing removes the need for governance`
    - `Becoming a full Slack or Linear lifecycle platform unless we explicitly choose that product`
    - `Tool sprawl justified by peer examples`
- `PRODUCT_PERSPECTIVE`
  - `COPY`:
    - `Workflow adapters that meet engineers where they already work`
  - `MODIFY_ON_TOP`:
    - `Treat Slack, Linear, and GitHub as adapters over the same control plane rather than the source of truth`
  - `REJECT`:
    - `Chat surfaces becoming the authority plane`
- `EVIDENCE_PATHS`:
  - `thread source: Open SWE: An Open-Source Framework for Internal Coding Agents`
- `OPEN_RISKS`: `Framework convenience can quietly pull the product toward platform scope.`

### PRODUCT_16: `Spec Coding and governance-pack workflow`
- `WHY_RESEARCHED`: `This source cluster is useful because it turns AI coding from open-ended prompting into staged execution with explicit acceptance.`
- `TECHNICAL_PERSPECTIVE`
  - `COPY`:
    - `Spec-first flow for complex work: proposal -> design -> spec -> tasks`
    - `Task grouping with micro-acceptance and local verification for refactors`
    - `Three-layer guidance: constraints, exemplars, and visual references`
    - `Direct source access for API docs, design docs, and other canonical materials`
    - `Task-size routing instead of one workflow for everything`
  - `MODIFY_ON_TOP`:
    - `Specs -> advisory until promoted under PM or CEO authority`
    - `Rules -> backstop with mechanical checks instead of prose-only compliance`
    - `Doc connectors -> allowlisted and ordered by source-of-truth hierarchy`
  - `REJECT`:
    - `Everything needs a spec`
    - `Tool-call count or LOC as quality metrics`
    - `Assuming local success equals CI or production truth`
- `PRODUCT_PERSPECTIVE`
  - `COPY`:
    - `A user-facing story that the system scales workflow rigor with task complexity`
  - `MODIFY_ON_TOP`:
    - `Make “spec required” a visible lane decision, not hidden friction`
  - `REJECT`:
    - `Over-selling case-study productivity numbers as universal truth`
- `EVIDENCE_PATHS`:
  - `thread source: AI 编程能力边界探索：基于 Claude Code 的 Spec Coding 项目实战`
- `OPEN_RISKS`: `If task-size routing is unclear, the system will either over-specify trivial work or under-specify risky work.`

### PRODUCT_17: `Anthropic internal lessons on Skills`
- `WHY_RESEARCHED`: `This source cluster is the strongest operational guide for what makes skills useful at scale rather than decorative.`
- `TECHNICAL_PERSPECTIVE`
  - `COPY`:
    - `Treat skills as packages with scripts, assets, references, examples, and optional memory`
    - `Adopt a category taxonomy for skill design and catalog management`
    - `Require a Gotchas section for high-risk or high-repeat skills`
    - `Use progressive disclosure inside the skill itself`
    - `Use scripts as first-class leverage so the model composes instead of re-deriving`
    - `Support on-demand hooks for session-scoped safety modes`
    - `Instrument skill usage and under-triggering`
  - `MODIFY_ON_TOP`:
    - `Marketplace-ready packaging -> allowlist and decision-log approval for anything beyond low risk`
    - `Skill descriptions -> trigger predicates plus risk tier`
    - `Skill memory -> store only in stable, auditable locations aligned to artifact policy`
  - `REJECT`:
    - `Safety-critical skills as optional suggestions`
    - `Uncurated skill marketplace sprawl`
    - `Skills that mix too many categories without a clear trigger`
- `PRODUCT_PERSPECTIVE`
  - `COPY`:
    - `A small, legible skill catalog that maps to real operator jobs`
  - `MODIFY_ON_TOP`:
    - `Treat execution skills differently from knowledge skills in the UX`
  - `REJECT`:
    - `A product whose skill shelf is bigger than its governance model`
- `EVIDENCE_PATHS`:
  - `thread source: Lessons from Building Claude Code: How We Use Skills`
- `OPEN_RISKS`: `Without measurement and pruning, skill catalogs accrete redundancy and drift.`

### PRODUCT_18: `Harness / ACI / repository-as-record`
- `WHY_RESEARCHED`: `This source cluster sharpens the technical meaning of a harness and what the endgame architecture should optimize for.`
- `TECHNICAL_PERSPECTIVE`
  - `COPY`:
    - `Context is attention, not RAM; tool design must prevent self-flooding`
    - `Output-capped search and navigation tools as forcing functions`
    - `Stateful file viewing with line numbers and position semantics`
    - `Structured edits followed immediately by lint or typecheck`
    - `Repo as system of record for specs, decisions, progress, and verification`
    - `Git worktree isolation per task`
    - `Mechanical architecture enforcement with agent-readable remediation`
    - `Explicit done-checklists updated only after verification`
  - `MODIFY_ON_TOP`:
    - `Initializer plus progress log -> map into startup intake, round contract, done checklist, and closure artifacts`
    - `Minimal blocking merges -> risk-tiered merge posture rather than universal policy`
    - `Observability -> integrated evidence plane, not a second authority layer`
  - `REJECT`:
    - `One giant handbook`
    - `Just give it more context`
    - `Prompt-only enforcement of quality and architecture`
    - `Done without end-to-end verification`
    - `Assuming human review is the primary scaling mechanism`
- `PRODUCT_PERSPECTIVE`
  - `COPY`:
    - `A product story centered on harness quality rather than raw model cleverness`
  - `MODIFY_ON_TOP`:
    - `Translate “harness” into operator-facing promises: safer execution, clearer state, and more reliable handoffs`
  - `REJECT`:
    - `Model-centric marketing that ignores the environment`
- `EVIDENCE_PATHS`:
  - `thread source: The Harness Is Everything: What Cursor, Claude Code, and Perplexity Actually Built`
- `OPEN_RISKS`: `Without deliberate ACI design, better models will still underperform in complex repo work.`

## Round 3 Synthesis
- `TECHNICAL_KEEP_THESE_PATTERNS`: `governance-first harness design, explicit escalation from simple to complex architectures, packaged skills with gotchas and scripts, spec-first workflow for complex work, curated ACI tools that prevent context flooding, isolated workspaces, mechanical architecture enforcement, and a separate observability evidence plane`
- `PRODUCT_KEEP_THESE_PATTERNS`: `PM-first control plane framing, workflow rigor that scales with task complexity, explicit evidence surfaces, a small curated skill catalog, and adapters that meet engineers in existing tools without moving authority into chat`
- `DO_NOT_IMPORT`: `model-first thinking, monolithic handbooks, prompt-only governance, skill or plugin sprawl, autonomy theater, unredacted audit logging, benchmark heuristics presented as hard law, and local-success-only validation`
- `BIGGEST_DECISION_RISK`: `Building an impressive-looking agent platform that still lacks a coherent authority model, evidence plane, and done-state contract`
- `NEXT_ACTION`: `Converge the product around a single governance-first harness: add a machine-checkable done checklist, tighten skills governance and measurement, keep specs for complex work only, and treat observability as authoritative evidence about what happened.`

## Endgame
- `PRODUCT_ENDGAME`: `A PM-first operator control plane where a human sets intent, risk, approvals, and done criteria once, then delegates to a small visible team of specialists that return contract-shaped artifacts, not black-box magic. The product feels like one place to run engineering work with bounded autonomy: goals, active lane, current evidence, budget pressure, verification state, and open approvals are always visible, and chat surfaces remain adapters rather than sources of truth.`
- `TECHNICAL_ENDGAME`: `A governance-first harness over isolated workspaces and curated ACI tools: startup intake, round contract, and a machine-checkable done checklist define the execution envelope; progressive-disclosure docs and packaged skills load only the needed knowledge; execution occurs in sandboxed worktrees with capped-search, stateful file views, structured edits, and immediate lint or typecheck feedback; structural linters and closure validators enforce invariants mechanically; session audit logs plus runtime logs plus OTel traces provide authoritative evidence of what happened.`
- `WHAT_WE_ARE_NOT_BUILDING`: `Not a zero-human autopilot. Not a permissionless execution layer. Not a giant plugin marketplace or personality zoo. Not a monolithic handbook masquerading as a harness. Not a second authority plane where dashboards, chat surfaces, or reviewers silently override PM/CEO governance.`

## Notes
- `SOURCE_SNAPSHOT`: `The original Phase 5 handoff snapshot remains in ../../../docs/archive/program_history/phase5/phase5_pm_architecture_handoff.md.`
- `WORKING_RULE`: `When a source has strong UX but weak governance, copy the UX shape and modify the authority semantics. When a source has strong technical seams but permissive trust defaults, copy the seam and reject the trust default.`
- This artifact does not create a new gate or authority path.
