# W11 Communication Protocol v1.0

**Owner:** PM
**Status:** ACTIVE
**Last Updated:** 2026-03-04
**Applies To:** W11 execution window (March 9-15, 2026)

---

## Purpose

Standardize communication format, frequency, and escalation paths during W11 execution to ensure clear status visibility and rapid response to issues.

Use this protocol for:
- Daily status reporting during W11 window
- Checkpoint reminder scheduling
- Escalation message templates
- Stakeholder notification

---

## Communication Roles

| Role | Responsibility | Frequency |
|------|----------------|-----------|
| **Worker** | Execute cycles, report status, escalate issues | Per cycle + daily summary |
| **PM** | Monitor progress, respond to escalations, approve exceptions | Daily review + on-demand |
| **CEO** | Review weekly summary, approve strategic decisions | Weekly + escalations only |

---

## Daily Status Packet Format

**Mandatory Fields:**

```text
=== W11 DAY <N> STATUS ===
Date: <YYYY-MM-DD>
Day: <Mon|Tue|Wed|Thu|Fri|Sat|Sun>

Cycles Run Today: <count>
W11 Items (cumulative): <count>
W11 Target: <checkpoint_target>
On Track: YES|NO

C3 Status: PASS|FAIL
Annotation Coverage: <XXX%>
FP Rate: <X.XX%>
Infra Errors: <count>

Next Checkpoint: <date and target>
Action Required: <none or specific action>
Escalation: <none or trigger>
===========================
```

**Field Definitions:**

- **Date:** YYYY-MM-DD format (Asia/Macau timezone)
- **Day:** Day of week (Mon-Sun)
- **Cycles Run Today:** Number of shadow cycles executed today
- **W11 Items (cumulative):** Total items collected in W11 so far
- **W11 Target:** Checkpoint target for current date (see W11 run card)
- **On Track:** YES if cumulative >= target, NO if behind
- **C3 Status:** PASS if 2 consecutive weeks met, FAIL otherwise
- **Annotation Coverage:** Percentage of C/H findings annotated (must be 100%)
- **FP Rate:** False positive rate (FP findings / total C/H findings)
- **Infra Errors:** Count of exit 2 errors today (must be 0)
- **Next Checkpoint:** Date and target for next checkpoint (March 10/12/14)
- **Action Required:** Specific action if behind or issue detected
- **Escalation:** Escalation trigger if any (see escalation matrix)

**Delivery:**
- Worker posts daily status packet to shared location (e.g., decision log, status file)
- PM reviews daily status packet by end of day
- CEO reviews weekly summary only (not daily packets)

---

## Per-Cycle Status Report

**After each shadow cycle, Worker reports:**

```text
=== W11 CYCLE STATUS ===
Date: <YYYY-MM-DD>
Run ID: <run_id>
W11 Items (cumulative): <count>
W11 Target: <checkpoint_target>
C3 Status: PASS|FAIL
Annotation Coverage: <XXX%>
FP Rate: <X.XX%>
Next Checkpoint: <date and target>
========================
```

**Delivery:**
- Worker posts per-cycle status after completing all 7 steps (shadow run → annotate → refresh artifacts → report)
- PM reviews on-demand (not required for every cycle)
- Used for intra-day progress tracking
- If `docs/context/next_round_handoff_latest.md` exists after artifact refresh, Worker should attach or link it with the per-cycle packet as the recommended acceleration input for the next round.
- The advisory handoff is for faster restart only; it does not replace startup interrogation, the startup go/no-go card, or required PM/CEO acknowledgments.
- When the advisory handoff conflicts with same-day startup intake or other authoritative artifacts, the startup intake and source-of-truth hierarchy win.
- If `docs/context/board_decision_brief_latest.md` exists, PM may attach or link it only when a strategic tradeoff needs structured framing for CEO review.
- The board brief is advisory only: CEO remains final authority, while any CTO/COO sections are analytic lenses rather than additional decision owners.

---

## Checkpoint Reminder Schedule

**W11 Checkpoints (from W11 execution plan):**

| Date | Checkpoint | Target | Reminder Time |
|------|------------|--------|---------------|
| March 10 (Tue) | Checkpoint 1 | >=4 items | March 10, 18:00 Asia/Macau |
| March 12 (Thu) | Checkpoint 2 | >=8 items | March 12, 18:00 Asia/Macau |
| March 14 (Sat) | Checkpoint 3 | >=10 items | March 14, 18:00 Asia/Macau |

**Reminder Message Template:**

```text
=== W11 CHECKPOINT REMINDER ===
Checkpoint: <1|2|3>
Date: <YYYY-MM-DD>
Target: >=<count> items
Current: <count> items
Status: ON_TRACK|AT_RISK|BEHIND

Action Required:
- If ON_TRACK: Continue normal cadence
- If AT_RISK: Consider adding 1 extra cycle today
- If BEHIND: Add 2 extra cycles today, escalate to PM

Next Checkpoint: <date and target>
================================
```

**Reminder Delivery:**
- Worker sets reminder for 18:00 Asia/Macau on checkpoint dates
- Worker checks current W11 items vs target
- Worker takes action based on status (ON_TRACK/AT_RISK/BEHIND)
- If BEHIND: Worker escalates to PM immediately

---

## Escalation Message Templates

### Escalation 1: Annotation Coverage <100%

**Trigger:** Annotation coverage drops below 100%

**Severity:** HIGH

**Message Template:**

```text
=== ESCALATION: ANNOTATION COVERAGE <100% ===
Date: <YYYY-MM-DD HH:MM UTC>
Run ID: <run_id>
Annotation Coverage: <XXX%>
Unannotated Findings: <count>

Immediate Action:
- Stopped cycle execution
- Identifying unannotated findings
- Will repair annotations before reporting

Expected Resolution: <YYYY-MM-DD HH:MM UTC>
Escalated To: PM
================================================
```

**Delivery:**
- Worker sends to PM immediately (within 1 hour of detection)
- PM acknowledges receipt and monitors resolution
- Worker reports resolution when coverage = 100%

### Escalation 2: FP Rate >5%

**Trigger:** FP rate reaches or exceeds 5%

**Severity:** CRITICAL

**Message Template:**

```text
=== ESCALATION: FP RATE >5% ===
Date: <YYYY-MM-DD HH:MM UTC>
FP Rate: <X.XX%>
FP Count: <count>
Total C/H: <count>

FP Pattern:
- Rule: <AUD-R00X>
- Occurrences: <count>
- Root Cause: <rule_bug|annotation_error|systemic>

Immediate Action:
- Stopped execution
- Reverted to shadow mode
- Reviewing all FP annotations

Evidence:
- FP Ledger: docs/context/auditor_fp_ledger.json
- Dossier: docs/context/auditor_promotion_dossier.json

Escalated To: PM → CEO
Expected Resolution: <YYYY-MM-DD>
================================
```

**Delivery:**
- Worker sends to PM immediately (within 1 hour of detection)
- PM reviews and escalates to CEO within 4 hours
- CEO reviews and approves recovery plan
- Worker reports resolution when FP rate <5%

### Escalation 3: Infra Error (Exit 2)

**Trigger:** Phase-end handover exits with code 2

**Severity:** CRITICAL

**Message Template:**

```text
=== ESCALATION: INFRA ERROR (EXIT 2) ===
Date: <YYYY-MM-DD HH:MM UTC>
Run ID: <run_id>
Exit Code: 2

Error Description:
<one-line error from phase-end summary>

Immediate Action:
- Stopped execution
- Captured error context
- Reverted to shadow mode

Evidence:
- Summary: docs/context/phase_end_logs/phase_end_handover_summary_<run_id>.md
- Logs: <path_to_logs>

Escalated To: PM
Expected Resolution: <YYYY-MM-DD>
=========================================
```

**Delivery:**
- Worker sends to PM immediately (within 1 hour of detection)
- PM reviews error context and decides recovery path
- PM communicates decision to Worker and CEO
- Worker reports resolution when infra issue fixed

### Escalation 4: Checkpoint Miss

**Trigger:** W11 items fall below checkpoint target

**Severity:** MEDIUM

**Message Template:**

```text
=== ESCALATION: CHECKPOINT MISS ===
Date: <YYYY-MM-DD>
Checkpoint: <1|2|3>
Target: >=<count> items
Actual: <count> items
Gap: <count> items

Immediate Action:
- Increased run frequency to <count> cycles/day
- Will add <count> extra cycles today

Expected Recovery:
- Next checkpoint: <date and target>
- Projected items by next checkpoint: <count>

Escalated To: PM (if gap >4 items)
====================================
```

**Delivery:**
- Worker sends to PM same day if gap >4 items
- PM reviews and approves increased frequency or window extension
- Worker reports progress at next checkpoint

### Escalation 5: Repeated HIGH Findings

**Trigger:** Same HIGH finding code appears 3+ times in 7 days

**Severity:** MEDIUM

**Message Template:**

```text
=== ESCALATION: REPEATED HIGH FINDINGS ===
Date: <YYYY-MM-DD>
Rule: <AUD-R00X>
Occurrences: <count> in 7 days
Root Cause: <Worker error|Rule too strict|Systemic>

Pattern Analysis:
<one-line description of pattern>

Immediate Action:
- Reviewed root cause
- <Fixed process|Requesting rule tuning|Escalating for strategic review>

Evidence:
- Findings: docs/context/phase_end_logs/auditor_findings_*.json
- Pattern: <description>

Escalated To: PM
Expected Resolution: <YYYY-MM-DD>
===========================================
```

**Delivery:**
- Worker sends to PM within 1 business day of detection
- PM reviews root cause and decides action
- PM communicates decision to Worker
- Worker reports resolution when pattern stops

---

## Escalation Recipients

| Escalation Type | First Recipient | Second Recipient | Response SLA |
|-----------------|-----------------|------------------|--------------|
| Annotation coverage <100% | PM | CEO (if pattern repeats) | 2 hours |
| FP rate >5% | PM | CEO (immediate) | 4 hours |
| Infra error (exit 2) | PM | CEO (if systemic) | 2 hours |
| Checkpoint miss | PM | CEO (if gap >4 items) | Same day |
| Repeated HIGH findings | PM | CEO (if systemic) | 1 business day |

**Escalation Paths:**
- Worker → PM: For all operational issues (annotation, checkpoint, repeated findings)
- PM → CEO: For strategic issues (FP rate, infra error, systemic problems)
- Direct to CEO: For D09 (premature promotion) or authority conflicts

---

## Weekly Summary (CEO-Level)

**Delivered:** End of W11 window (March 15, 2026)

**Format:** Use `docs/templates/ceo_weekly_summary.md` template

**Key Metrics:**
- W11 items collected (target: 12+)
- C3 status (PASS/FAIL)
- FP rate (target: <5%)
- Annotation coverage (target: 100%)
- Infra errors (target: 0)
- Escalations (count and type)

**Delivery:**
- Worker generates weekly summary using template
- PM reviews and adds recommendations
- PM may use `docs/context/board_decision_brief_latest.md` to package the decision topic, major tradeoffs, and recommended option before CEO review.
- CEO reviews and makes GO/HOLD/REFRAME decision
- CEO may use the board brief as analytic input, but the final decision still lands in the weekly summary, GO signal, and decision log.

---

## Communication Channels

**Primary Channel:** Decision log (`docs/decision log.md`)
- All escalations logged here
- All status packets appended here
- Provides audit trail

**Secondary Channel:** Status file (`docs/context/w11_status.md`)
- Daily status packets
- Per-cycle status reports
- Checkpoint reminders

**Escalation Channel:** Direct message to PM/CEO
- For CRITICAL escalations (FP rate, infra error)
- For time-sensitive issues requiring immediate response

---

## Status Packet Delivery Schedule

| Time | Packet Type | Recipient | Required |
|------|-------------|-----------|----------|
| After each cycle | Per-cycle status | PM (on-demand) | NO |
| End of day (20:00 Asia/Macau) | Daily status packet | PM | YES |
| Checkpoint dates (18:00 Asia/Macau) | Checkpoint reminder | Worker (self) | YES |
| End of W11 (March 15) | Weekly summary | CEO | YES |
| On escalation trigger | Escalation message | PM/CEO | YES |

---

## Paste-Ready Communication Blocks

### Daily Status (Minimal)
```text
W11 Day <N>: <count> items (target: <count>) | C3: <PASS|FAIL> | Coverage: <XXX%> | FP: <X.XX%> | Status: <ON_TRACK|AT_RISK|BEHIND>
```

### Checkpoint Status (Minimal)
```text
Checkpoint <N>: <count>/<target> items | Status: <ON_TRACK|AT_RISK|BEHIND> | Action: <none|add_cycles|escalate>
```

### Escalation (Minimal)
```text
ESCALATION: <type> | Severity: <HIGH|CRITICAL> | Action: <description> | ETA: <date>
```

---

## Communication Discipline

**Worker Responsibilities:**
- Post daily status packet by 20:00 Asia/Macau
- Post per-cycle status after each cycle
- Send escalation messages within SLA (1-4 hours depending on severity)
- Respond to PM queries within 4 hours

**PM Responsibilities:**
- Review daily status packets by end of day
- Respond to escalations within SLA (2-4 hours depending on severity)
- Approve exceptions and recovery plans within 1 business day
- Communicate decisions to Worker and CEO
- Use `docs/context/board_decision_brief_latest.md` only as an optional packaging aid for strategic tradeoffs; do not treat it as a new approval layer

**CEO Responsibilities:**
- Review weekly summary within 2 business days
- Respond to strategic escalations within 24 hours
- Make GO/HOLD/REFRAME decisions within 2 business days
- Treat CTO/COO/expert sections in `docs/context/board_decision_brief_latest.md` as advisory lenses only; CEO remains final authority

---

## Communication Failures

**If Worker misses daily status packet:**
- PM sends reminder within 2 hours
- If no response within 4 hours: PM escalates to CEO

**If PM misses escalation response SLA:**
- Worker sends reminder after SLA expires
- If no response within 2x SLA: Worker escalates to CEO

**If CEO misses strategic decision SLA:**
- PM sends reminder after SLA expires
- If no response within 2x SLA: PM makes decision with CEO approval deferred

---

## Governance Notes

- This protocol is authoritative for W11 communication
- Applies to W11 window only (March 9-15, 2026)
- Can be adapted for future execution windows (W12, W13, etc.)
- Updates require PM proposal + CEO approval
- Version incremented on each update
