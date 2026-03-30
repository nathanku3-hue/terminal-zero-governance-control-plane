# Domain Falsification Pack (Template)

> **Canonical source:** src/sop/templates/domain_falsification_pack.md
> This copy in docs/templates/ is a workspace mirror. Do not edit here — edit the canonical source instead.

Use this only for high-semantic-risk claims before coding.

## Header
- PackID: `<YYYYMMDD-short-id>`
- RepoScope: `<repo/domain>`
- Owner: `<name>`
- DateUTC: `<ISO8601>`

## Claim Under Test
- Claim: `<one sentence>`
- Why high semantic risk: `<one sentence>`
- Expected decision impact: `<one sentence>`

## Canonical Sources
- Source 1: `<path>`
- Source 2: `<path>`
- Source 3: `<path|N/A>`

## Falsification Attempts
- Counterexample A: `<attempt + outcome>`
- Counterexample B: `<attempt + outcome>`
- Counterexample C: `<attempt + outcome|N/A>`

## Verdict
- Result: `<HOLD|REFRAME|PROCEED>`
- Boundaries/Non-Goals reaffirmed: `<one line>`
- Next action: `<single action>`

## Notes
- This pack does not change decision authority or role ownership.
- If the active round contract sets `DOMAIN_FALSIFICATION_REQUIRED=YES`, closure validates this pack structurally before escalation.
