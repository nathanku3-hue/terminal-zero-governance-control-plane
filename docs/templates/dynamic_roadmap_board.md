# Dynamic Roadmap Board Template v1.0

> **Canonical source:** src/sop/templates/dynamic_roadmap_board.md
> This copy in docs/templates/ is a workspace mirror. Do not edit here — edit the canonical source instead.

## 1) Board Metadata

**Week:** `<YYYY-Www>`  
**Program / Stream:** `<name>`  
**Board Owner:** `<name>`  
**Last Updated (UTC):** `<timestamp>`  
**Current Phase Closing:** `<phase_id>`

---

## 2) Band Rules (10-Phase Horizon)

| Band | Phase Window | Planning Posture | Change Policy | Update Cadence |
|---|---|---|---|---|
| Committed | 1-2 | Delivery lock | Changes require explicit leadership approval | Weekly + phase close |
| Adaptive | 3-5 | Planned but adjustable | PM can re-sequence within guardrails | Weekly |
| Exploratory | 6-10 | Option pipeline | Can add/remove options based on evidence | Weekly |

**Guardrails:**  
1. Keep exactly 2 phases in `Committed`.  
2. Any slip in `Committed` must name owner, cause, and recovery action in the same update.  
3. Keep at least 2 viable options in `Exploratory` at all times.

---

## 3) Dynamic Roadmap Board

| Phase | Band | Objective | Scope Lock | Status | Confidence | Key KPI Link | Decision Gate | Planned Close | Actual Close | Owner |
|---|---|---|---|---|---|---|---|---|---|---|
| P01 | Committed | `<objective>` | `locked` | `<not started/in progress/at risk/done>` | `<H/M/L>` | `<kpi>` | `<gate>` | `<YYYY-Www>` | `<YYYY-Www or ->` | `<owner>` |
| P02 | Committed | `<objective>` | `locked` | `<status>` | `<H/M/L>` | `<kpi>` | `<gate>` | `<YYYY-Www>` | `<YYYY-Www or ->` | `<owner>` |
| P03 | Adaptive | `<objective>` | `bounded` | `<status>` | `<H/M/L>` | `<kpi>` | `<gate>` | `<YYYY-Www>` | `<YYYY-Www or ->` | `<owner>` |
| P04 | Adaptive | `<objective>` | `bounded` | `<status>` | `<H/M/L>` | `<kpi>` | `<gate>` | `<YYYY-Www>` | `<YYYY-Www or ->` | `<owner>` |
| P05 | Adaptive | `<objective>` | `bounded` | `<status>` | `<H/M/L>` | `<kpi>` | `<gate>` | `<YYYY-Www>` | `<YYYY-Www or ->` | `<owner>` |
| P06 | Exploratory | `<objective>` | `open` | `<status>` | `<H/M/L>` | `<kpi>` | `<gate>` | `<YYYY-Www>` | `<YYYY-Www or ->` | `<owner>` |
| P07 | Exploratory | `<objective>` | `open` | `<status>` | `<H/M/L>` | `<kpi>` | `<gate>` | `<YYYY-Www>` | `<YYYY-Www or ->` | `<owner>` |
| P08 | Exploratory | `<objective>` | `open` | `<status>` | `<H/M/L>` | `<kpi>` | `<gate>` | `<YYYY-Www>` | `<YYYY-Www or ->` | `<owner>` |
| P09 | Exploratory | `<objective>` | `open` | `<status>` | `<H/M/L>` | `<kpi>` | `<gate>` | `<YYYY-Www>` | `<YYYY-Www or ->` | `<owner>` |
| P10 | Exploratory | `<objective>` | `open` | `<status>` | `<H/M/L>` | `<kpi>` | `<gate>` | `<YYYY-Www>` | `<YYYY-Www or ->` | `<owner>` |

---

## 4) Phase-Close Update Protocol

1. Confirm phase outcome against objective (`met`, `partial`, or `missed`) with one-line evidence.
2. Record KPI impact, including `Decision Latency (p50)` movement during the phase.
3. Capture unresolved risks, exceptions, and carry-over actions with named owners and due dates.
4. Recompute `Governance Adoption Score` and log sub-scores.
5. Move horizon forward:
   - Close completed phase.
   - Promote next phase so `Committed` remains phases 1-2.
   - Re-rank phases 3-10 by current constraints and evidence.
6. Publish update within 24 hours of phase close and link it in the weekly CEO summary.

---

## 5) Governance Adoption Scorecard (0-100)

| Component | Weight | Score | Evidence | Owner |
|---|---:|---:|---|---|
| Decision log completeness | 30 | `<0-100>` | `<link or note>` | `<owner>` |
| Phase-close updates on time | 25 | `<0-100>` | `<link or note>` | `<owner>` |
| Risk and exception register currency | 20 | `<0-100>` | `<link or note>` | `<owner>` |
| Action owner and due-date clarity | 15 | `<0-100>` | `<link or note>` | `<owner>` |
| Policy and process compliance | 10 | `<0-100>` | `<link or note>` | `<owner>` |

**Total Governance Adoption Score:** `<weighted total>/100`

---

## 6) Weekly CEO Readout (Paste-Ready)

```text
ROADMAP STATUS: committed(P01-P02)=<status>; adaptive(P03-P05)=<status>; exploratory(P06-P10)=<status>
PHASE CLOSE: <phase_id> => <met/partial/missed>; next committed phases=<Pxx,Pyy>
DECISION LATENCY P50: <x.x>d (delta=<+/-x.x>d)
GOVERNANCE ADOPTION: <x>/100 (delta=<+/-x>)
KEY GATES NEXT 2 WEEKS: <gate>, <gate>
```
