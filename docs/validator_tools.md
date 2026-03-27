# Validator Tool Wrapper Design

**Stream**: 2 (Validator Tool Wrapper)  
**Date**: Saturday, March 28, 2026  
**Status**: Complete

---

## Factory Pattern

The validator tool wrappers use a factory pattern where concrete classes 
(ClosurePacketTool, ArchitectCalibrationTool, SawReportBlocksTool) return 
base ValidatorTool instances, not their own subclass types.

### Rationale

- These classes are factory shims, not subclasses with additional behavior
- The factory pattern is sufficient for the current use case
- Descriptor metadata is loaded from JSON files in `.codex/skills/_shared/scripts/`
- Each factory method creates a ValidatorTool with the correct descriptor and script path

### Future Enhancement

If concrete subclasses need additional behavior (e.g., custom validation, 
logging, or caching), they can be implemented as subclasses in future streams.

---

## Stream 1 Contract Preservation

ValidatorTool.execute() calls `self.validate_input(**kwargs)` BEFORE marshalling,
preserving the Stream 1 contract where:

- **Tool.validate_input()**: Enforces all constraints (required, enum, oneOf)
- **ArgumentMarshaller**: Handles CLI formatting only (boolean flags, string values)

This separation of concerns ensures validation happens before any subprocess execution.

---

## Implementation Details

### ValidatorTool Base Class

Located in `src/sop/tools/validators/validator_tool.py`:

```python
class ValidatorTool(Tool):
    def __init__(self, validator_script_path: str, descriptor, repo_root: Path):
        # Initialize with descriptor metadata
        
    def execute(self, **kwargs) -> dict:
        # 1. Call self.validate_input(**kwargs) — Stream 1 contract
        # 2. Use ArgumentMarshaller to format CLI args
        # 3. Execute validator subprocess
        # 4. Return structured result
```

### Factory Methods

Each validator tool has a static `create()` factory method:

```python
@staticmethod
def create(repo_root: Path) -> ValidatorTool:
    # Load descriptor from JSON file
    # Create ValidatorTool instance
    # Return tool
```

### Descriptor Loading

Descriptors are loaded from JSON files using:
```python
with open(descriptor_path, 'r') as f:
    descriptor_data = json.load(f)
descriptor = ValidatorDescriptor.from_dict(descriptor_data)
```

---

## Validators Wrapped

### 1. ClosurePacketTool
- **Script**: `.codex/skills/_shared/scripts/validate_closure_packet.py`
- **Descriptor**: `.codex/skills/_shared/scripts/validate_closure_packet.descriptor.json`
- **Required Input**: `packet` (ClosurePacket line)
- **Optional Input**: `require_open_risks_when_block`, `require_next_action_when_block` (booleans)

### 2. ArchitectCalibrationTool
- **Script**: `.codex/skills/_shared/scripts/validate_architect_calibration.py`
- **Descriptor**: `.codex/skills/_shared/scripts/validate_architect_calibration.descriptor.json`
- **Required Input**: `history_csv`, `active_profile`
- **Optional Input**: `min_rows` (integer, default 5), `tolerance` (number, default 0.1)

### 3. SawReportBlocksTool
- **Script**: `.codex/skills/_shared/scripts/validate_saw_report_blocks.py`
- **Descriptor**: `.codex/skills/_shared/scripts/validate_saw_report_blocks.descriptor.json`
- **Input Contract**: oneOf (exactly one required):
  - `report` (string): SAW report text supplied inline
  - `report_file` (string): Path to a SAW report text file

---

## Test Coverage

**17 Integration Tests** in `tests/test_validator_tools.py`:

- **ClosurePacketTool**: 6 tests (creation, valid input, optional flags, error cases, descriptor roundtrip)
- **ArchitectCalibrationTool**: 4 tests (creation, valid input, error cases, descriptor roundtrip)
- **SawReportBlocksTool**: 4 tests (creation, valid input, error cases, descriptor roundtrip)
- **ValidatorTool Contract**: 2 tests (validate_input before execution, constraint validation)
- **Backward Compatibility**: 1 test (full repo suite verification)

**Full Repo Suite**: Passes (full pytest suite passes)

---

## Backward Compatibility

- Original validators still work independently
- Tool wrapper is additive, not replacing
- No breaking changes to existing code
- Full repo test suite passes

---

## Design Decisions

1. **Factory Pattern**: Concrete classes return base ValidatorTool instances
   - Rationale: Factory shims only; sufficient for current use case
   - Future: Can add subclass behavior if needed

2. **Descriptor Loading**: JSON files in `.codex/skills/_shared/scripts/`
   - Rationale: Centralized descriptor storage
   - Benefit: Single source of truth for validator contracts

3. **Stream 1 Contract**: validate_input() before marshalling
   - Rationale: Ensures validation happens before subprocess execution
   - Benefit: Clear separation of concerns (validation vs formatting)

---

## Future Enhancements

- Add concrete subclasses with custom behavior if needed
- Enhance success-path test coverage for ArchitectCalibrationTool and SawReportBlocksTool
- Add caching or logging if performance becomes a concern
- Extend to wrap additional validators as they are created
