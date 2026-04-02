# Phase E D4 Validation Gates (Conformance + Negative-Path)

**Date:** 2026-04-01  
**Phase:** Phase E (`phase5`)  
**Status:** PASS

---

## Gate Set

### Gate E-D4-1 — v2 metadata and kind conformance
Validation ensures v2 plugins declare valid metadata and allowed kinds.

Command:
```bash
python -m pytest tests/test_plugin_api_v2_capabilities.py -q
```

### Gate E-D4-2 — capability allowlist and mismatch rejection
Validation ensures unknown, missing, malformed, and cross-kind capability declarations are rejected.

Command:
```bash
python -m pytest tests/test_plugin_api_v2_capabilities.py -q
```

### Gate E-D4-3 — coexistence + chain semantics
Validation ensures v1 plugins still operate, mixed v1/v2 ordering remains deterministic, and BLOCK short-circuit is preserved.

Command:
```bash
python -m pytest tests/test_plugin_api_v1.py tests/test_plugin_api_v2_capabilities.py -q
```

### Gate E-D4-4 — reference integration conformance
Validation ensures all three D3 reference plugins are discoverable, capability-valid, contract-conforming, and bounded to approved classes.

Command:
```bash
python -m pytest tests/test_phase_e_d3_reference_plugins.py -q
```

---

## Closure-Grade Focused Run

```bash
python -m pytest tests/test_plugin_api_v1.py tests/test_plugin_api_v2_capabilities.py tests/test_phase_e_d3_reference_plugins.py -q
```

Result: **25 passed**

---

## Contract Result Rule

Phase E D4 gate status is PASS only when all E-D4-1..E-D4-4 checks pass in focused validation runs.
Any failure keeps D4 in BLOCK.
