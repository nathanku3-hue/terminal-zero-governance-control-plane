# Scripts Utilities Migration Guide

This guide documents the migration of common utility functions from individual scripts to shared modules in `scripts/utils/`.

## Time Utilities Migration

### Overview

Time utility functions have been extracted to `scripts/utils/time_utils.py` to provide canonical implementations and eliminate code duplication across scripts.

### Available Functions

```python
from scripts.utils.time_utils import utc_now, utc_iso, utc_now_iso

# Get current UTC datetime
now = utc_now()  # Returns: datetime with UTC timezone

# Convert datetime to ISO string
timestamp = utc_iso(now)  # Returns: "2026-03-09T15:30:45Z"

# Get current UTC as ISO string (convenience)
timestamp = utc_now_iso()  # Returns: "2026-03-09T15:30:45Z"
```

### Migration Pattern

**Before:**
```python
from datetime import datetime, timezone

def _utc_now() -> datetime:
    return datetime.now(timezone.utc)

def _utc_iso(ts: datetime) -> str:
    return ts.strftime("%Y-%m-%dT%H:%M:%SZ")

def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# Usage
now = _utc_now()
timestamp = _utc_iso(now)
```

**After:**
```python
from datetime import datetime, timezone
from pathlib import Path
import sys

# Add parent directory to path for imports
_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR.parent) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR.parent))

from scripts.utils.time_utils import utc_now, utc_iso, utc_now_iso

# Usage
now = utc_now()
timestamp = utc_iso(now)
```

### Migrated Scripts

- ✅ `scripts/aggregate_worker_status.py` - Migrated and tested (Phase 3)

### Scripts Pending Migration

The following scripts contain local time utility implementations that should be migrated:

1. `scripts/run_loop_cycle.py` - Contains `_utc_now()`, `_utc_iso()`
2. `scripts/evaluate_context_compaction_trigger.py` - Contains `_utc_now()`, `_utc_iso()`
3. `scripts/supervise_loop.py` - Contains `_utc_now()`, `_utc_iso()`
4. `scripts/validate_loop_clo.py` - Contains `_utc_now()`, `_utc_iso()`
5. `scripts/generate_ceo_go_signal.py` - Contains `_utc_now_iso()`
6. `scripts/generate_ceo_weekly_summary.py` - Contains `_utc_now_iso()`
7. `scripts/build_profile_selection_ranking.py` - Contains `_utc_now_iso()`
8. `scripts/run_fast_checks.py` - Contains `_utc_now_iso()`
9. `scripts/startup_codex_helper.py` - Contains `_utc_iso()`

### Migration Steps

For each script:

1. Add the path setup code at the top (after imports but before using the utilities)
2. Import the shared utilities: `from scripts.utils.time_utils import utc_now, utc_iso, utc_now_iso`
3. Replace local function calls:
   - `_utc_now()` → `utc_now()`
   - `_utc_iso(dt)` → `utc_iso(dt)`
   - `_utc_now_iso()` → `utc_now_iso()`
4. Remove local time utility function definitions
5. Run tests to verify no regressions

### Benefits

- **Consistency**: All scripts use the same timestamp format
- **Maintainability**: Single source of truth for time utilities
- **Testability**: Shared utilities can be tested once
- **Reduced duplication**: Eliminates ~10 duplicate implementations

## Atomic I/O Utilities Migration

### Overview

Atomic write utilities have been extracted to `scripts/utils/atomic_io.py` to eliminate code duplication across scripts. These utilities use the temp file + rename pattern to ensure file consistency.

### Available Functions

```python
from scripts.utils.atomic_io import atomic_write_text, atomic_write_json

# Write text atomically
atomic_write_text(Path("output.txt"), "content")

# Write JSON atomically (with 2-space indent + trailing newline)
atomic_write_json(Path("output.json"), {"key": "value"})
```

### Migration Pattern

**Before:**
```python
import os
import tempfile
from pathlib import Path

def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, prefix=".tmp_", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except FileNotFoundError:
            pass
        raise

# Usage
_atomic_write_text(output_path, content)
```

**After:**
```python
import os
import tempfile
from pathlib import Path

try:
    from scripts.utils.atomic_io import atomic_write_text
except ModuleNotFoundError:
    # Fallback for direct script execution
    def atomic_write_text(path: Path, content: str, encoding: str = "utf-8") -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(dir=path.parent, prefix=".tmp_", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding=encoding, newline="\n") as handle:
                handle.write(content)
            os.replace(tmp_path, path)
        except Exception:
            try:
                os.unlink(tmp_path)
            except FileNotFoundError:
                pass
            raise

# Usage
atomic_write_text(output_path, content)
```

**Note:** The try/except fallback is necessary because scripts are often run directly (`python scripts/script.py`) rather than as modules.

### Migrated Scripts

- ✅ `scripts/supervise_loop.py` - Migrated and tested (2026-03-09)

### Scripts Pending Migration

The following scripts contain local atomic write implementations:

1. `scripts/build_context_packet.py` - `_atomic_write_text()`
2. `scripts/auditor_calibration_report.py` - `_atomic_write_text()`
3. `scripts/aggregate_worker_status.py` - `_atomic_write_json()`
4. `scripts/build_ceo_bridge_digest.py` - `_atomic_write_text()`
5. `scripts/evaluate_context_compaction_trigger.py` - `_atomic_write_text()`
6. `scripts/build_profile_selection_ranking.py` - `_atomic_write_text()`
7. `scripts/generate_ceo_weekly_summary.py` - `_atomic_write_text()`
8. `scripts/generate_ceo_go_signal.py` - `_atomic_write_text()`
9. `scripts/capture_profile_outcome_record.py` - `_atomic_write_json()`
10. `scripts/build_exec_memory_packet.py` - `_atomic_write_text()`
11. `scripts/manual_capture_watcher.py` - `_atomic_write_text()` and `_atomic_write_json()`
12. `scripts/sync_philosophy_feedback.py` - `_atomic_write_text()`
13. `scripts/startup_codex_helper.py` - `_atomic_write_text()`
14. `scripts/run_auditor_review.py` - `_atomic_write_text()`
15. `scripts/run_loop_cycle.py` - `_atomic_write_text()`
16. `scripts/validate_loop_closure.py` - `_atomic_write_text()`

### Migration Steps

For each script:

1. Add the import with fallback (see pattern above)
2. Replace `_atomic_write_text()` calls with `atomic_write_text()`
3. Replace `_atomic_write_json()` calls with `atomic_write_json()`
4. Remove local function definitions
5. Run tests: `python -m pytest tests/test_<script_name>.py -v`

### Benefits

- **DRY Principle**: Single source of truth for atomic write logic
- **Consistency**: All scripts use the same implementation
- **Maintainability**: Bug fixes apply to all scripts
- **Testability**: Shared utilities can be tested independently

## JSON Utilities Migration

### Overview

JSON loading utilities have been extracted to `scripts/utils/json_utils.py` to provide canonical implementations with consistent error handling and eliminate code duplication across scripts.

### Available Functions

```python
from scripts.utils.json_utils import safe_load_json_object

# Load JSON file that must contain an object at root
data, error = safe_load_json_object(Path("config.json"))
if data is None:
    print(f"Failed to load: {error}")
else:
    # Use data
```

### Function Signature

```python
def safe_load_json_object(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    """
    Safely load a JSON file that must contain an object at the root.

    Returns:
        Tuple of (data, error_message):
        - On success: (dict, None)
        - On failure: (None, error_message)

    Error types:
        - "file_not_found": File does not exist
        - "read_error: {exc}": File read failed
        - "json_error: {exc}": JSON parsing failed
        - "json_error: root must be object": JSON root is not an object
    """
```

### Migration Pattern

**Before (Pattern 1 - Simple None return):**
```python
def _load_json_safe(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None

# Usage
data = _load_json_safe(some_path)
if data is None:
    # Handle missing/invalid
```

**Before (Pattern 2 - Tuple with error message):**
```python
def _safe_load_json_object(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        raw = path.read_text(encoding="utf-8-sig")
    except Exception as exc:
        return None, f"read_error: {exc}"
    try:
        payload = json.loads(raw)
    except Exception as exc:
        return None, f"json_error: {exc}"
    if not isinstance(payload, dict):
        return None, "json_error: root must be object"
    return payload, None
```

**After (Unified Pattern):**
```python
from pathlib import Path
import sys

# Add parent directory to path for direct script execution
if __name__ == "__main__":
    _script_dir = Path(__file__).resolve().parent
    _project_root = _script_dir.parent
    if str(_project_root) not in sys.path:
        sys.path.insert(0, str(_project_root))

from scripts.utils.json_utils import safe_load_json_object

# Usage
data, error = safe_load_json_object(some_path)
if data is None:
    # Handle error (error message available in 'error' variable)
    print(f"Failed to load: {error}")
```

### Migrated Scripts

- ✅ `scripts/build_exec_memory_packet.py` - Migrated and tested (Phase 3, 2026-03-09)
  - Replaced `_load_json_safe` with `safe_load_json_object`
  - All 23 tests passing
  - No regression in error handling

### Scripts Pending Migration

The following scripts contain local JSON loading implementations:

1. `scripts/supervise_loop.py` - Contains `_safe_load_json_object()` (already uses tuple return pattern)
2. `scripts/capture_profile_outcome_record.py` - Contains `_load_json_safe()` (returns None on error)

### Migration Steps

For each script:

1. Add sys.path setup for direct script execution (if `__name__ == "__main__"`)
2. Add import: `from scripts.utils.json_utils import safe_load_json_object`
3. Replace function calls:
   - `_load_json_safe(path)` → `safe_load_json_object(path)`
   - `_safe_load_json_object(path)` → `safe_load_json_object(path)`
4. Update error handling to use tuple unpacking: `data, error = safe_load_json_object(path)`
5. Update conditional checks to handle error messages if needed
6. Remove local function definitions
7. Run tests: `python -m pytest tests/test_<script_name>.py -v`

### Benefits

- **Code Reuse**: Single canonical implementation
- **Consistent Error Handling**: Standardized error messages and patterns
- **Easier Maintenance**: Fix bugs in one place
- **Better Testing**: Shared utilities can be tested independently
- **Type Safety**: Clear return type signatures with error information
- **UTF-8 BOM Support**: Handles `utf-8-sig` encoding automatically
- **Validation**: Ensures JSON root is an object, not array or primitive

## Known Remaining Duplicates

After Phase 4 pilot migration, the following local utility duplicates remain in the codebase:

### Atomic I/O Duplicates

1. **scripts/build_exec_memory_packet.py:181** - `_atomic_write_text()`
   - Status: Fallback implementation retained for direct script execution
   - Migration: Can be removed once all scripts use package imports

2. **scripts/aggregate_worker_status.py:34** - `_atomic_write_json()`
   - Status: Fallback implementation retained for direct script execution
   - Migration: Can be removed once all scripts use package imports

3. **scripts/supervise_loop.py:19** - Fallback implementation
   - Status: Fallback implementation retained for direct script execution
   - Migration: Can be removed once all scripts use package imports

### Estimated Migration Effort

**Full Migration (All Scripts):**
- Time utilities: 9 scripts × 15 min = 2.25 hours
- Atomic I/O utilities: 16 scripts × 20 min = 5.3 hours
- JSON utilities: 2 scripts × 15 min = 0.5 hours
- **Total: ~8 hours**

**Benefits of Full Migration:**
- Eliminate ~30 duplicate function implementations
- Single source of truth for all utilities
- Consistent error handling across all scripts
- Easier maintenance and bug fixes
- Better test coverage

**Recommendation:**
- Phase 5: Migrate remaining time utilities (highest ROI, simplest)
- Phase 6: Migrate remaining atomic I/O utilities
- Phase 7: Remove fallback implementations once all scripts migrated

## Future Utilities

Additional utility modules may be added for:
- Path resolution and validation
- Common data structures and transformations
