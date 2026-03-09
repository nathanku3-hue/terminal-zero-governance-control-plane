# Automation Boundary Registry

Status: ACTIVE  
Scope: Advisory exec-memory artifacts only  
Control plane impact: None — this registry does not add gates or change authority.

## Canonical Boundaries

| Boundary ID | Machine may do | Escalate when | Human / Expert lane | Retirement criteria |
|---|---|---|---|---|
| ABR-01 | Summarize current artifacts and suggest next-round handoff | `replanning.status=ACTION_REQUIRED` or `next_round_handoff.status=ACTION_REQUIRED` | PM | `replanning.status=CLEAR` and `next_round_handoff.status=CLEAR` |
| ABR-02 | Assemble a tradeoff brief from current artifacts | `pm_ceo_research_brief.status=ACTION_REQUIRED` | PM/CEO | `pm_ceo_research_brief.status=OPTIONAL` |
| ABR-03 | Prepare a specialist question and source bundle | `expert_request.status=ACTION_REQUIRED` | Named expert in packet | `expert_request.status=OPTIONAL` or refreshed evidence clears the blocker |
| ABR-04 | Summarize likely UX or operational readiness from artifacts | Real UX validation, manual signoff, or desktop/manual evidence is still required | Human QA / PM / CEO | Manual evidence is captured or a trustworthy automated UX harness exists for the task class |
| ABR-05 | Propose expert domain assignment using the current milestone roster | `roster_fit in {ROSTER_MISSING, UNKNOWN_EXPERT_DOMAIN}` or `BOARD_LINEUP_REVIEW_REQUIRED` | PM/CEO board reentry | Roster is present and requested domain is in approved lineup |

## Notes

- Machine output remains advisory even when the status is `CLEAR`.
- Human and expert escalation here means "request help for judgment or evidence quality," not "change the authority model."
- `ROSTER_MISSING`, `UNKNOWN_EXPERT_DOMAIN`, and `BOARD_LINEUP_REVIEW_REQUIRED` are fail-closed advisory statuses, not automatic authority changes.
- Retire or narrow a boundary here when models improve; prefer deleting stale rows over adding new control-plane logic.
- This file is the canonical reference for retiring advisory uncertainty flags in the exec-memory packet.
