# CEO Weekly Summary Template v1.1

> **Canonical source:** src/sop/templates/ceo_weekly_summary.md
> This copy in docs/templates/ is a workspace mirror. Do not edit here — edit the canonical source instead.

## 1) Executive Snapshot

**Week:** `<YYYY-Www>`  
**Date Range:** `<YYYY-MM-DD>` to `<YYYY-MM-DD>`  
**Current Phase:** `<phase_id>`  
**Program Status:** `GO` | `HOLD` | `REFRAME`  
**Top Message (1 sentence):** `<plain-language summary for CEO>`

---

## 2) KPI Card (Non-Technical, Weekly)

| KPI | Current | Target | Trend | Status |
|---|---:|---:|---|---|
| Total Items Reviewed | `<n>` | `>=30` | `up/down/flat` | `GREEN/YELLOW/RED` |
| Weekly Qualified Windows | `<n>` | `>=2` | `up/down/flat` | `GREEN/YELLOW/RED` |
| Critical+High FP Rate | `<x.xx%>` | `<5.00%` | `up/down/flat` | `GREEN/YELLOW/RED` |
| Annotation Coverage (C/H) | `<x.xx%>` | `100%` | `up/down/flat` | `GREEN/YELLOW/RED` |
| Infra Failures | `<n>` | `0` | `up/down/flat` | `GREEN/YELLOW/RED` |
| Decision Latency (p50 days) | `<x.x>` | `<=5.0` | `up/down/flat` | `GREEN/YELLOW/RED` |
| Governance Adoption Score (0-100) | `<x>` | `>=80` | `up/down/flat` | `GREEN/YELLOW/RED` |

**Overall KPI Verdict:** `ON_TRACK` | `AT_RISK` | `OFF_TRACK`

**Metric Notes:**  
`Decision Latency` = median calendar days from logged request to final decision.  
`Governance Adoption Score` = weighted score for decision log quality, phase-close discipline, and risk/exception hygiene.

---

## 3) Promotion Criteria Snapshot

| Criterion | Meaning (Business) | Status | Current Value | Threshold |
|---|---|---|---|---|
| C0 | System reliability | `PASS/FAIL` | `<value>` | `0 failures` |
| C1 | Readiness signoff | `MANUAL_CHECK/PASS/FAIL` | `<value>` | `PM approval` |
| C2 | Evidence volume | `PASS/FAIL` | `<value>` | `>=30 items` |
| C3 | Stability over time | `PASS/FAIL` | `<value>` | `>=2 qualifying weeks` |
| C4 | False positives controlled | `PASS/FAIL` | `<value>` | `<5%` |
| C4b | Review discipline | `PASS/FAIL` | `<value>` | `100% C/H annotated` |
| C5 | Schema consistency | `PASS/FAIL` | `<value>` | `All v2.0.0` |

**Automated Criteria Pass Count:** `<x>/6`  
**Recommendation:** `GO` | `HOLD` | `REFRAME`

---

## 4) What Changed This Week

1. `<major change 1>`
2. `<major change 2>`
3. `<major change 3>`

**Delta vs Last Week (plain language):**  
`<what improved, what regressed, why it matters>`

---

## 5) Top-3 Recurring Finding Burn-Down

| Rank | Recurring Finding | This Week | Last Week | Burn-Down (count) | Trend | Owner | Closure ETA |
|---|---|---:|---:|---:|---|---|---|
| 1 | `<finding>` | `<n>` | `<n>` | `<last - current>` | `improving/flat/worsening` | `<owner>` | `<date>` |
| 2 | `<finding>` | `<n>` | `<n>` | `<last - current>` | `improving/flat/worsening` | `<owner>` | `<date>` |
| 3 | `<finding>` | `<n>` | `<n>` | `<last - current>` | `improving/flat/worsening` | `<owner>` | `<date>` |

**CEO Readout (2 lines max):**  
`<is recurring risk shrinking fast enough, and what decision/support is needed>`

---

## 6) Blockers and Risks

| Type | Description | Impact | Owner | Due Date | Mitigation |
|---|---|---|---|---|---|
| Blocker | `<short blocker>` | `High/Medium/Low` | `<owner>` | `<date>` | `<action>` |
| Risk | `<short risk>` | `High/Medium/Low` | `<owner>` | `<date>` | `<action>` |

**Escalations Needed This Week:**  
1. `<decision/escalation needed from CEO/PM>`
2. `<decision/escalation needed from CEO/PM>`

---

## 7) Decisions Requested (CEO)

| Decision | Why Needed | Options | Recommended | Aging (days) | Needed By |
|---|---|---|---|---:|---|
| `<decision name>` | `<one line>` | `<A/B/C>` | `<A>` | `<n>` | `<date>` |
| `<decision name>` | `<one line>` | `<A/B/C>` | `<B>` | `<n>` | `<date>` |

**Decision SLA:** `<=5 days standard, <=2 days for critical-path decisions`

---

## 8) Dynamic Roadmap Board (10-Phase Horizon)

**Band Policy:**  
`Committed` = phases `1-2` (scope and staffing locked)  
`Adaptive` = phases `3-5` (adjust within guardrails)  
`Exploratory` = phases `6-10` (hypothesis-driven options)

| Phase | Band | Goal / Outcome | Status | Confidence | Planned Close | Notes / Decision Gate |
|---|---|---|---|---|---|---|
| P01 | Committed | `<goal>` | `<not started/in progress/at risk/done>` | `<H/M/L>` | `<YYYY-Www>` | `<note>` |
| P02 | Committed | `<goal>` | `<not started/in progress/at risk/done>` | `<H/M/L>` | `<YYYY-Www>` | `<note>` |
| P03 | Adaptive | `<goal>` | `<status>` | `<H/M/L>` | `<YYYY-Www>` | `<note>` |
| P04 | Adaptive | `<goal>` | `<status>` | `<H/M/L>` | `<YYYY-Www>` | `<note>` |
| P05 | Adaptive | `<goal>` | `<status>` | `<H/M/L>` | `<YYYY-Www>` | `<note>` |
| P06 | Exploratory | `<goal>` | `<status>` | `<H/M/L>` | `<YYYY-Www>` | `<note>` |
| P07 | Exploratory | `<goal>` | `<status>` | `<H/M/L>` | `<YYYY-Www>` | `<note>` |
| P08 | Exploratory | `<goal>` | `<status>` | `<H/M/L>` | `<YYYY-Www>` | `<note>` |
| P09 | Exploratory | `<goal>` | `<status>` | `<H/M/L>` | `<YYYY-Www>` | `<note>` |
| P10 | Exploratory | `<goal>` | `<status>` | `<H/M/L>` | `<YYYY-Www>` | `<note>` |

**Phase-Close Update Protocol (run at each phase close):**
1. Log actual outcomes, KPI deltas, and misses for the phase being closed.
2. Roll the board forward and keep exactly two `Committed` phases.
3. Re-prioritize `Adaptive` and `Exploratory` phases based on new evidence.
4. Update decision aging/latency and governance adoption inputs for the closed phase.
5. Publish updated board owner and timestamp within 24 hours of phase close.

---

## 9) Next 7 Days Plan

1. `<priority action 1>`
2. `<priority action 2>`
3. `<priority action 3>`
4. `<priority action 4>`

**Expected Outcome by Next Report:**  
`<quantified expectation>`

---

## 10) Source-of-Truth Artifacts

- Weekly Calibration Report: `docs/context/auditor_calibration_report.json`
- Promotion Dossier: `docs/context/auditor_promotion_dossier.json`
- CEO GO Signal: `docs/context/ceo_go_signal.md`
- Dynamic Roadmap Board: `docs/context/dynamic_roadmap_board.md` (template: `docs/templates/dynamic_roadmap_board.md`)
- Latest Phase-End Summary: `docs/context/phase_end_logs/phase_end_handover_summary_<run_id>.md`

---

## 11) Approval Block

**Prepared By:** `<name>`  
**Prepared At (UTC):** `<timestamp>`  
**Reviewed By:** `<name>`

**Weekly Executive Decision:**  
`[ ] Continue Current Plan`  
`[ ] Increase Execution Intensity`  
`[ ] Reframe Scope`  
`[ ] Escalate for Intervention`

**Comments:**  
`<optional>`

---

## Paste-Ready Minimal Version

```text
WEEK: <YYYY-Www> | STATUS: GO/HOLD/REFRAME
TOP MESSAGE: <one sentence>
KPI: items=<x>/<30>, windows=<x>/<2>, fp=<x.xx%>, coverage=<x.xx%>, infra=<n>, decision_latency_p50=<x.x>d, governance=<x>/100
CRITERIA: C0=<>, C1=<>, C2=<>, C3=<>, C4=<>, C4b=<>, C5=<>
TOP-3 RECURRING FINDINGS: #1 <finding>(<delta>), #2 <finding>(<delta>), #3 <finding>(<delta>)
DECISIONS NEEDED: <decision>(age=<n>d), <decision>(age=<n>d)
ROADMAP: committed(P01-P02)=<status>; adaptive(P03-P05)=<status>; exploratory(P06-P10)=<status>
NEXT 7 DAYS: <list>
RECOMMENDATION: <GO/HOLD/REFRAME>
```
