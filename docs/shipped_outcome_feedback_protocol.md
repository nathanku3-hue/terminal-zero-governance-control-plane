# Shipped Outcome Feedback Protocol (Advisory)

Status: Active  
Scope: PM/operator learning loop (advisory)  
Authority: Advisory only; does not add a gate, override, or control-plane authority.

## Purpose

- Capture what happened after a decision or shipped wave, not just whether the round passed.
- Keep the learning loop lean and evidence-bound.
- Reuse the existing `profile_outcomes_corpus` so shipped-outcome learning stays machine-readable and locally auditable.

## Minimal Outcome Fields

- `project_profile`
- `shipped`
- `rollback_status` (`NO|PARTIAL|FULL`)
- `followup_changes_within_30d` (`0+`)
- `semantic_issue_detected_after_merge` (`NONE|PRESENT|I don't know yet`)
- `postmortem_note`
- `artifact_context`

## Capture Command

```powershell
.venv\Scripts\python scripts/capture_profile_outcome_record.py --repo-root . --project-profile "<project_profile>" --shipped "<true|false>" --rollback-status "<NO|PARTIAL|FULL>" --followup-changes-within-30d "<0+>" --semantic-issue-detected-after-merge "<NONE|PRESENT|I don't know yet>" --postmortem-note "<short_postmortem_note>"
```

## Working Artifact

- Corpus directory: `docs/context/profile_outcomes_corpus/`
- One additive JSON record per shipped wave or meaningful outcome update.
- Current minimal implementation intentionally reuses `capture_profile_outcome_record.py` and the same corpus used by advisory profile ranking.

## Operator Rules

- Capture once when the shipped wave outcome is known.
- Update once again around the 30-day mark if follow-up changes or semantic issues become clearer.
- If the outcome is still too fresh to judge, write `I don't know yet` rather than pretending certainty.
- Keep the note short and artifact-bound.

## Relationship To Ranking

- This protocol broadens the same local evidence corpus that already supports `docs/profile_selection_ranking_advisory.md`.
- Current profile ranking remains intentionally simple; not every new outcome field is scored yet.
- The main value of `R3` is learning from shipped reality before adding more scoring or automation.
