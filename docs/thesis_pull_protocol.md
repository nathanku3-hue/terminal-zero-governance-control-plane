# Thesis Pull Protocol

Status: Advisory-only protocol  
Authority: no new gate, role, or subsystem; this protocol describes when a thesis pull is worth doing and how to keep it bounded.  
Purpose: refine repo heuristics from live external-repo evidence plus limited research, without automatic policy mutation.

## 1. When a Thesis Pull Is Allowed

A thesis pull should run only when at least one of these is true in another repo:
- SOP is actively operating there, or
- fresh real operating evidence exists there.

Fresh real operating evidence means lived signals such as shipped outcomes, repeated loop behavior, postmortems, incidents, correction patterns, or measurable operating drift. Paper-only curiosity or a dormant repo is not enough.

If active external-repo use or fresh real operating evidence is missing, do not run a thesis pull; record `NOT_ACTIVE` / `I don't know yet` and stop.

## 2. Evidence Mix

A thesis pull is evidence-led, not paper-led.

Required mix:
- local data-driven evidence from the source repo as the primary signal,
- plus `1-3` academic inputs only.

Academic inputs should interpret, challenge, or sharpen the local evidence. They do not replace it.

If local evidence and academic inputs conflict, local evidence leads unless an explicit human-reviewed philosophy update later says otherwise.

## 3. Realm-Specific Repo Lens

Every thesis pull must declare a realm-specific repo lens.

That lens should make clear:
- the domain,
- the user or operator reality,
- the risk profile,
- the workflow shape,
- and what is likely transferable versus realm-specific.

Without this lens, a thesis pull risks importing ideas that sound right but do not fit the target operating environment.

## 4. Research Classification

Each academic input must be classified as one of:
- `SUPPORTS` — reinforces a heuristic already suggested by local evidence.
- `CANDIDATE` — plausible and relevant, but still needs more local evidence.
- `FRONTIER` — interesting for future watching, but too early or too infrastructure-specific to shape heuristics now.
- `NOT_ACTIONABLE` — not transferable, not relevant enough, or not useful for current heuristic refinement.

This keeps research from carrying more authority than the live repo evidence deserves.

## 5. Outcome Discipline

A thesis pull should end in one of three outcomes:
- `NO_CHANGE`
- `WATCH`
- `HUMAN_REVIEW_HEURISTIC_UPDATE`

A thesis pull may suggest a heuristic refinement, but it must not mutate policy automatically.

Current self-learning loop is structurally sufficient for now.
- More shipped waves, postmortems, and repeated operating evidence are an operational evidence need, not a reason to add a new subsystem.
- A thesis pull may include an explicit `EVIDENCE_FRESHNESS_WINDOW` and `ABSTENTION_REASON_CODE` when that helps explain why the outcome stays conservative or incomplete.
- Those fields remain advisory-only and do not change gates, roles, or authority.

Any actual philosophy or heuristic update requires:
- explicit human review,
- a separate docs change,
- and an evidence trail showing why the refinement is worth keeping.

## 6. Artifacts and Authority

- Template: `docs/templates/thesis_pull_template.md`
- Authoritative working copy: `docs/context/thesis_pull_latest.md`
- Convenience mirror: `THESIS_PULL_LATEST.md`

Authority rules:
- `docs/context/thesis_pull_latest.md` is authoritative.
- `THESIS_PULL_LATEST.md` is convenience-only and intentionally thin.
- If wording differs, the `docs/context` file wins.
