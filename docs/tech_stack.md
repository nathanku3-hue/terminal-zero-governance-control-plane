# Tech Stack - Hard Constraints

**Purpose**: Define runtime requirements, forbidden patterns, and dependency management rules.

## Runtime Requirements

### Python Version
- **Required**: Python 3.12+
- **Preference**: Repo-local `.venv` when available
- **Fallback**: Compatible system Python when `.venv` unavailable
- **Evidence**: Record interpreter used in validation evidence

### Core Architecture
- **Script-first orchestration**: No complex frameworks
- **JSON/Markdown contracts**: Artifact exchange format
- **Subprocess-driven validators**: External validation scripts
- **Atomic operations**: Critical writes use temp → replace pattern

## Primary Operator Entrypoints

### Startup and Execution
- `scripts/startup_codex_helper.py` - Initialize a round
- `scripts/run_loop_cycle.py` - Execute main worker/auditor/CEO loop

### Closure and Supervision
- `scripts/validate_loop_closure.py` - Close the loop
- `scripts/supervise_loop.py` - Monitor loop health
- `scripts/print_takeover_entrypoint.py` - Print takeover guidance

## Testing Framework

### Test Runner
- **Primary**: `pytest` for all test execution
- **Coverage**: Script behavior, contract validation, orchestration flows

### Test Count Baseline
- **Historical snapshots**:
  - Stream 2 merge-gate: 303 passed
  - Post-blocker baseline: 308 passed
- **Current HEAD**: Always quote freshly rerun repo-wide `pytest` count
- **Evidence**: Record run date + interpreter used (never reuse prior totals)

## Forbidden Patterns (Without Explicit Approval)

### Databases
- ❌ SQLite
- ❌ PostgreSQL
- ❌ MySQL
- ❌ Any SQL database without explicit approval

### Web Frameworks
- ❌ Flask
- ❌ Django
- ❌ FastAPI
- ❌ Any web framework without explicit approval

### ORMs
- ❌ SQLAlchemy
- ❌ Django ORM
- ❌ Peewee
- ❌ Any complex ORM without explicit approval

### Rationale
These patterns introduce:
- Deployment complexity
- State management overhead
- Migration burden
- Testing complexity

The control plane is script-driven by design. Use JSON/Markdown artifacts for state.

## Dependency Management

### Canonical Source
- **Primary**: `pyproject.toml` - Canonical dependency declaration
- **Must stay in sync**: All imports must be declared in `pyproject.toml`

### Pinned Installs
- **Production**: `constraints.txt` - Validated, pinned versions
- **Development**: `constraints-dev.txt` - Dev-only pinned versions

### Compatibility Shims
- **Legacy**: `requirements*.txt` - Compatibility only
- **Do NOT treat as canonical**: These are shims, not source of truth

### Dependency Addition Rules
1. Add to `pyproject.toml` first
2. Justify the dependency (why needed, alternatives considered)
3. Keep dependencies minimal
4. Update constraints files after validation
5. Document in decision log if significant

## Environment Hygiene

### Virtual Environment
- Use repo-local `.venv` when possible
- Activate before running scripts: `source .venv/bin/activate` (Unix) or `.venv\Scripts\activate` (Windows)
- Keep environment clean: no global package pollution

### Dependency Sync
- After adding dependencies: `pip install -e .`
- After updating constraints: `pip install -c constraints.txt -e .`
- Verify imports work before committing

### Evidence Requirements
- Record Python version used
- Record interpreter path
- Record installed package versions (for reproducibility)
- Include in validation evidence footer

## Performance Expectations

### Script Execution
- Startup scripts: < 5 seconds
- Loop cycle: < 30 seconds (excluding worker execution)
- Validators: < 2 seconds each
- Supervision: < 10 seconds per check

### Resource Limits
- Memory: < 500MB for control plane scripts
- CPU: Single-threaded by default (parallel where beneficial)
- Disk: Atomic writes only, no large temp files

## Compatibility

### Operating Systems
- Linux: Primary target
- macOS: Supported
- Windows: Supported (use Unix shell syntax in bash)

### Shell
- Bash: Primary shell
- Use Unix conventions: `/dev/null` not `NUL`, forward slashes in paths

## Upgrade Policy

### Python Version
- Stay on 3.12+ for now
- Upgrade to 3.13+ only after:
  - All dependencies compatible
  - Test suite passes
  - Explicit approval in decision log

### Dependencies
- Pin versions in constraints files
- Test upgrades in isolation
- Document breaking changes
- Update decision log for major version bumps
