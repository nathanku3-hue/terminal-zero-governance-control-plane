# Descriptor Consistency Validation

## Overview

The consistency validator provides read-only, non-authoritative validation of descriptor compliance. It checks that descriptors conform to the ValidatorDescriptor schema without enforcing permissions or blocking execution.

## Key Principles

✅ **Read-Only**: Validator performs checks but does NOT block execution  
✅ **Non-Authoritative**: `automation_boundary_registry.md` remains canonical authority  
✅ **Informational**: Exit codes and reports are for logging/monitoring only  
✅ **No Permission Gates**: Validator does NOT enforce permissions  

## Consistency Validator

### Location
```
quant_current_scope/scripts/validate_descriptor_consistency.py
```

### Class: DescriptorConsistencyValidator

Validates descriptor consistency without enforcing permissions.

#### Methods

**`__init__(descriptor_path: str)`**
- Initialize validator with descriptor path

**`validate() -> Tuple[bool, List[str], List[str]]`**
- Validate descriptor consistency
- Returns: (is_valid, errors, warnings)
- Note: Errors do NOT block execution

**`report() -> Dict`**
- Generate validation report
- Returns: Dictionary with validation results
- Note: Report is informational only

#### Validation Checks

1. **File Existence**: Descriptor file must exist
2. **JSON Validity**: File must be valid JSON
3. **Schema Compliance**: Must have 5 required fields
4. **Field Types**: Each field must have correct type
5. **Field Content**: Field values must be valid

### Usage

```python
from scripts.validate_descriptor_consistency import DescriptorConsistencyValidator

validator = DescriptorConsistencyValidator("path/to/descriptor.json")
is_valid, errors, warnings = validator.validate()

# Or get full report
report = validator.report()
print(report)
```

### Command Line

```bash
python scripts/validate_descriptor_consistency.py path/to/descriptor.json
```

Output:
```json
{
  "descriptor": "path/to/descriptor.json",
  "valid": true,
  "errors": [],
  "warnings": [],
  "note": "This is read-only consistency validation. Errors do NOT block execution. Authority: automation_boundary_registry.md"
}
```

## Validation Rules

### Required Fields (5)

| Field | Type | Validation |
|-------|------|-----------|
| `name` | string | Non-empty, alphanumeric + underscore |
| `description` | string | Non-empty |
| `input_schema` | object | Valid JSON Schema |
| `output_schema` | object | Valid JSON Schema |
| `declared_capabilities` | array | Array of strings |

### Error vs Warning

**Errors** (block validation):
- Missing required field
- Wrong field type
- Empty required field
- Invalid JSON

**Warnings** (do not block validation):
- Extra fields
- Non-alphanumeric characters in name
- Missing optional schema properties

## Test Coverage

14 comprehensive tests covering:

- ✅ Valid descriptor validation
- ✅ Missing file detection
- ✅ Invalid JSON detection
- ✅ Missing required fields
- ✅ Wrong field types
- ✅ Empty field values
- ✅ Extra fields (warnings)
- ✅ Report format
- ✅ Non-authoritative nature
- ✅ Actual descriptor validation
- ✅ Exit code informational nature

## Important Notes

### Non-Authoritative

The consistency validator is **read-only and non-authoritative**:
- ❌ Does NOT enforce permissions
- ❌ Does NOT block execution
- ❌ Does NOT create new authority
- ✅ Reports consistency issues for logging/monitoring

### Authority Hierarchy

1. **`automation_boundary_registry.md`** (canonical authority) — WINS
2. **`declared_capabilities` in descriptor** (informational)
3. **Actual skill invocation** (runtime truth)

### No CI Wiring

The consistency validator is **NOT wired into CI/CD**:
- ❌ Exit code does NOT block builds
- ❌ Errors do NOT fail tests
- ✅ Reports are informational only

## Integration with Skill Registry

The consistency validator can be used to:
- Monitor descriptor compliance
- Generate compliance reports
- Identify schema violations
- Support descriptor documentation

But it does NOT:
- Block skill execution
- Enforce permissions
- Create new registry authority
- Change skill invocation behavior

## Future Enhancements

Potential future uses (not in scope):
- Automated descriptor generation
- Descriptor migration tools
- Compliance dashboards
- Descriptor versioning

## References

- **Descriptor Schema**: `quant_current_scope/src/sop/descriptors/schema.json`
- **ValidatorDescriptor Class**: `quant_current_scope/src/sop/descriptors/validator_descriptor.py`
- **Authority**: `automation_boundary_registry.md`
- **Tests**: `quant_current_scope/tests/test_descriptor_consistency.py`
