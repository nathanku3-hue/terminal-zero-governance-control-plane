# Phase C Plan — Observability & Monitoring Exporters (Implementation Mode)

**Date:** 2026-04-01  
**Status:** In progress; D1-D4 implemented under approved C1-C5 contract, D5 closure pending review gates  
**Strategic Mapping:** Roadmap Phase C -> Locked `phase3`  
**Risk Tier:** Medium (runtime instrumentation + operational visibility changes)  
**Implementation GO:** GRANTED (auditor-approved under C1-C5 contract)

---

## Objective

Provide production-grade observability for governance decisions and loop health by standardizing metrics export, structured audit logging, and starter monitoring assets.

---

## Current Baseline (already implemented)

- Observability v1 exists via CLI metrics exporter:
  - `sop metrics --repo-root <path> --format prometheus`
- Current exporter reads `docs/context/audit_log.ndjson` and prints Prometheus exposition text.
- Existing metric families include:
  - `policy_decisions_total{decision,actor}`
  - `gate_evaluation_duration_seconds{gate}`
  - `failure_count_total`
- Structured audit NDJSON already carries `schema_version`.
- Existing evidence file present: `docs/evidence/phase3_observability_evidence.md`.
- Existing tests present: `tests/test_observability.py`.

---

## Strict Audit Ruling (current)

- Planning artifact quality: PASS
- Closure packet format: PASS
- Validator compatibility: PASS
- Implementation readiness: PASS
- Implementation GO: GRANTED

Implementation may begin under approved C1-C5 contract decisions. Phase closure remains blocked until D1-D5 are complete.

---

## Confirmed Gaps vs Phase C Roadmap

1. No HTTP metrics endpoint (CLI export only in v1).
2. Structured logging schema and audit event tagging are partially defined, not frozen as a Phase C contract.
3. No starter Grafana dashboard templates committed for operators.
4. CI checks cover current behavior but not full Phase C closure contract.

---

## Audit Decisions Required Before Coding

1. **C1 Exporter architecture decision**
   - Keep CLI-only exporter with documented bridge pattern, or add native HTTP `/metrics` endpoint.
   - **Auditor-approved default:** Option A (CLI canonical path).
2. **C2 Metrics contract scope**
   - Mandatory metric families/labels/types for Phase C closure.
   - **Auditor-approved default:** freeze current families/labels/types + explicit additive extension policy.
3. **C3 Structured log schema contract**
   - Canonical schema version and required audit event tags.
   - **Auditor-approved default:** freeze schema/tag contract now.
4. **C4 Dashboard deliverable scope**
   - Minimum Grafana assets required for acceptance.
   - **Auditor-approved default:** one starter dashboard + quickstart.
5. **C5 Backward compatibility strategy**
   - Handling for existing observability consumers and prior metric names.
   - **Auditor-approved default:** alias window + deprecation note.

These five decisions are approved implementation prerequisites.

---

## Likely Touched Surfaces

- `src/sop/__main__.py` (if endpoint/CLI contract changes)
- `src/sop/scripts/loop_cycle_runtime.py`
- `src/sop/_audit_log.py`
- `tests/test_observability.py`
- `docs/observability.md`
- `docs/evidence/phase3_observability_evidence.md`
- `docs/context/closure_packet_phase_c_observability.md`
- `docs/context/phase_c_implementation_audit_matrix.md`

---

## Phase C Deliverables

### D1 — Prometheus Export Path
- Implemented approved CLI-canonical exporter path (no HTTP endpoint added).
- Added compatibility alias-window output for deprecated metric names.

### D2 — Structured Logging Contract
- Implemented/frozen schema-tag emission via `event_tag` on audit entries.
- Enforced required tag set in tests and documentation.

### D3 — Monitoring Assets
- Starter Grafana dashboard retained at `docs/examples/grafana-dashboard.json`.
- Added operator quickstart at `docs/tutorials/quickstart-observability.md`.

### D4 — CI Observability Gates
- Expanded tests for alias-window compatibility and structured-log tag contract.
- Verified targeted observability and parity checks are passing.

### D5 — Evidence + Closure
- Refreshed `docs/evidence/phase3_observability_evidence.md` with fresh execution evidence.
- Closure remains BLOCK until review-gate completion and final closure synthesis.

---

## Acceptance Gates (must all pass)

1. Approved exporter path is implemented and documented.
2. Required metric families/labels/types are emitted correctly.
3. Structured JSON log schema + required audit tags are present and validated.
4. Monitoring template asset(s) are present and usable.
5. CI observability tests pass for exporter and schema contracts.
6. Evidence includes fresh metadata + validation tokens + closure packet update.

---

## Definition of Done / Closure Standards

Phase C closure must include:

- Evidence Footer
- validation tokens (`PASS/BLOCK/DRIFT/INSUFFICIENT` as applicable)
- fresh run metadata (date, interpreter, test count)
- review gate outcomes with performance review explicitly recorded
- rollback/compatibility note for observability contract changes

---

## Review Gate Expectations (Risk Tier: Medium)

Before closure, perform and record:

- architecture review
- code quality review
- test coverage review
- performance review (or explicit N/A rationale)
- compatibility/consumer impact review

---

## Audit-Wait Checklist

- [x] Audit approves exporter architecture (CLI-bridge vs HTTP endpoint).
- [x] Audit approves required metric contract (families/labels/types).
- [x] Audit approves structured log schema + tag set.
- [x] Audit approves minimum dashboard/template package.
- [x] Audit approves compatibility handling for existing consumers.
- [x] Audit approves closure evidence format and token set.

---

## Implementation GO Prerequisites (all required)

1. All five blocking contract decisions approved in `docs/context/phase_c_implementation_audit_matrix.md`.
2. Audit checklist above fully checked.
3. Closure packet remains machine-checkable and reflects current verdict.

Implementation is authorized under these approved prerequisites.

---

## Execution Order After Audit Approval

1. Implement D1 exporter path
2. Implement D2 structured log contract
3. Implement D3 monitoring assets
4. Implement D4 test/CI gates
5. Update docs and evidence
6. Finalize D5 closure packet decision

---

## Exit Criteria

Phase C is **implementation-complete** when D1-D5 ship and tests are green.  
Phase C is **fully closed** only when audit-approved evidence is appended and closure packet verdict is PASS.
