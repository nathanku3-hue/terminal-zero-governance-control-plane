# Artifact Pruning Rules

Status: Template
Authority: advisory-only integration artifact. This file does not authorize execution, promotion, or scope widening by itself.
Purpose: define explicit rules for when to prune, archive, or consolidate artifacts to prevent status sprawl.

## Philosophy

Status should be as small as possible while still preventing drift.

The target status model is:

- one static truth layer
- one live truth layer
- one bridge truth layer
- one evidence truth layer

That is enough.

Avoid:

- many overlapping summaries
- many "current" files with unclear precedence
- status surfaces that differ only in wording

If two artifacts answer the same top-level question, one of them should probably disappear or be downgraded to archive/supporting evidence.

## Pruning Rules

### Rule 1: One Current Artifact Per Truth Layer

**Static Truth:**
- Keep: `top_level_PM.md`, `docs/decision log.md`, active phase brief
- Prune: old phase briefs (archive after phase closes)
- Prune: duplicate PM docs (consolidate into top_level_PM.md)

**Live Truth:**
- Keep: `docs/context/current_context.md`
- Prune: old context snapshots (archive after phase closes)
- Prune: duplicate status files (consolidate into current_context.md)

**Bridge Truth:**
- Keep: `docs/context/bridge_contract_current.md`
- Prune: old bridge contracts (archive after phase closes)
- Prune: duplicate bridge files (consolidate into bridge_contract_current.md)

**Evidence Truth:**
- Keep: `docs/context/done_checklist_current.md`, `docs/context/multi_stream_contract_current.md`, `docs/context/post_phase_alignment_current.md`
- Prune: old checklists/contracts/alignments (archive after phase closes)
- Prune: duplicate evidence files (consolidate or archive)

**Planner Truth:**
- Keep: `docs/context/planner_packet_current.md`, `docs/context/impact_packet_current.md`
- Prune: old planner/impact packets (archive after phase closes)
- Prune: duplicate planner files (consolidate into planner_packet_current.md)

### Rule 2: Archive Closed Phase Artifacts

When a phase closes:

1. **Move phase-specific artifacts to archive:**
   - `docs/phase_brief/phaseN-brief.md` → keep (immutable SSOT)
   - `docs/handover/phaseN_*.md` → keep (immutable SSOT)
   - `docs/saw_reports/saw_phaseN_*.md` → keep (immutable SSOT)
   - `docs/context/e2e_evidence/phaseN_*.{txt,csv,json}` → archive or prune (large evidence files)

2. **Update current artifacts:**
   - `docs/context/current_context.md` → update to next phase
   - `docs/context/bridge_contract_current.md` → update to next phase
   - `docs/context/planner_packet_current.md` → update to next phase
   - `docs/context/impact_packet_current.md` → reset for next phase

3. **Prune stale artifacts:**
   - Old `*_current.md` files that are no longer current
   - Duplicate status files
   - Temporary evidence files (unless needed for audit)

### Rule 3: Consolidate Overlapping Summaries

If two artifacts answer the same question:

1. **Identify the canonical artifact:**
   - Which artifact is referenced by other artifacts?
   - Which artifact is updated more frequently?
   - Which artifact is more machine-readable?

2. **Consolidate or prune:**
   - If one artifact is clearly canonical, prune the other
   - If both artifacts are useful, consolidate into one
   - If consolidation is not possible, make precedence explicit in README

3. **Update references:**
   - Update all references to point to canonical artifact
   - Add deprecation notice to pruned artifact (if kept for transition period)

### Rule 4: Prune Large Evidence Files

Evidence files can grow large over time. Prune or archive:

- **Test run logs**: Keep summary, archive full logs after phase closes
- **Replay evidence**: Keep summary, archive full CSV after phase closes
- **E2E evidence**: Keep status files, archive full logs after phase closes
- **Research data**: Keep manifest, archive full data after phase closes (or move to external storage)

### Rule 5: Prune Temporary Artifacts

Temporary artifacts should be pruned after use:

- **Planning drafts**: Prune after plan is approved
- **Review drafts**: Prune after review is complete
- **Execution memos**: Keep final version, prune drafts
- **Temporary scripts**: Prune after execution completes (unless needed for audit)

## Pruning Schedule

### After Each Phase Closes
- Archive phase-specific artifacts
- Update current artifacts
- Prune stale artifacts
- Consolidate overlapping summaries

### After Each Major Milestone (e.g., every 5 phases)
- Prune large evidence files
- Archive old phase briefs (keep last 5 phases accessible)
- Consolidate decision log (keep full log, create summary for quick reference)

### After Each Quarter
- Review all artifacts for redundancy
- Prune temporary artifacts
- Update README routing if artifact structure changed

## Pruning Checklist

Before pruning an artifact, verify:

- [ ] Artifact is not referenced by other current artifacts
- [ ] Artifact is not needed for audit or compliance
- [ ] Artifact is not the canonical source of truth for any question
- [ ] Artifact has been archived (if needed for historical reference)
- [ ] All references to artifact have been updated

## Anti-Patterns

Do NOT prune:

- **Immutable SSOT**: Phase briefs, handover memos, SAW reports, decision log entries
- **Current artifacts**: Any `*_current.md` file that is still current
- **Canonical sources**: Any artifact that is the canonical source of truth
- **Audit trail**: Any artifact needed for audit or compliance

## Success Criteria

The pruning rules are working when:

- Status remains thin (one artifact per truth layer)
- No overlapping summaries (each artifact answers a distinct question)
- No stale artifacts (all `*_current.md` files are actually current)
- No large evidence files in active workspace (archived or pruned)
- README routing is clear (no ambiguity about which artifact to read)

## Writing Rules
- Keep this file compact and PM-readable.
- Make pruning rules explicit and checkable.
- Make pruning schedule explicit and repeatable.
- Keep the artifact thin: one current ruleset, not a growing archive.
