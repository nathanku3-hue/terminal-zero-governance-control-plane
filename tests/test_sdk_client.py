"""Phase 3 -- test_sdk_client.py

Acceptance tests for GovernanceClient (src/sop/_client.py).

GAP resolutions implemented here:
  GAP 1: run() uses parse_args() delegation -- argv built from kwargs.
  GAP 2: status() returns None when file absent; test calls run() first.
  GAP 3: audit() derives dest_dir from repo_root; test calls run() first.
  GAP 4: test_openapi_spec_validates -- manual fallback with defined minimum.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from sop import GovernanceClient


# ---------------------------------------------------------------------------
# Helper: minimal governed repo fixture
# ---------------------------------------------------------------------------

def _make_repo(tmp_path: Path) -> Path:
    """Create the minimal directory structure run_cycle() requires."""
    (tmp_path / "docs" / "context").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs" / "plans").mkdir(parents=True, exist_ok=True)
    (tmp_path / "scripts").mkdir(parents=True, exist_ok=True)
    (tmp_path / "logs").mkdir(parents=True, exist_ok=True)
    return tmp_path


# ---------------------------------------------------------------------------
# Test 1 -- run() returns a dict with final_result key
# ---------------------------------------------------------------------------

def test_governance_client_run_returns_summary_dict(tmp_path: Path) -> None:
    """GovernanceClient.run() must return a dict containing 'final_result'.

    run() delegates to parse_args() with a constructed argv -- never builds
    a Namespace by hand. This test verifies that delegation is correct by
    checking the returned payload shape.
    """
    repo = _make_repo(tmp_path)
    client = GovernanceClient(repo_root=repo)

    result = client.run(skip_phase_end=True, allow_hold=True)

    assert isinstance(result, dict), "run() must return a dict"
    assert "final_result" in result, "run() result must contain 'final_result'"
    assert result["final_result"] in {
        "PASS", "HOLD", "FAIL", "ERROR"
    }, f"Unexpected final_result: {result['final_result']!r}"
    assert "final_exit_code" in result, "run() result must contain 'final_exit_code'"
    assert isinstance(result["final_exit_code"], int)


# ---------------------------------------------------------------------------
# Test 2 -- audit() returns a list (after run() populates the audit log)
# ---------------------------------------------------------------------------

def test_governance_client_audit_returns_list(tmp_path: Path) -> None:
    """GovernanceClient.audit() must return a list.

    The test calls run() first to ensure the audit log is populated,
    then verifies that audit() returns a list of dicts.
    dest_dir is derived as Path(repo_root) / 'docs' / 'context'.
    """
    repo = _make_repo(tmp_path)
    client = GovernanceClient(repo_root=repo)

    # Populate audit log by running one cycle
    client.run(skip_phase_end=True)

    entries = client.audit()

    assert isinstance(entries, list), "audit() must return a list"
    for entry in entries:
        assert isinstance(entry, dict), (
            f"Each audit entry must be a dict, got {type(entry)}"
        )


# ---------------------------------------------------------------------------
# Test 3 -- status() returns dict after run() writes the summary file
# ---------------------------------------------------------------------------

def test_governance_client_status_returns_dict(tmp_path: Path) -> None:
    """GovernanceClient.status() must return a dict when the summary file exists.

    GAP 2 resolution: test calls run() first to ensure the file exists,
    then calls status(). status() must NOT run a cycle automatically --
    it only reads the existing file.

    Also verifies the missing-file contract: status() returns None before
    any run.
    """
    repo = _make_repo(tmp_path)
    client = GovernanceClient(repo_root=repo)

    # GAP 2: status() must return None when file is absent
    assert client.status() is None, "status() must return None before any run"

    # Populate the summary file by running one cycle
    client.run(skip_phase_end=True)

    result = client.status()
    assert result is not None, (
        "status() must return a dict after run() writes the summary"
    )
    assert isinstance(result, dict), "status() must return a dict"
    assert "final_result" in result, "status() result must contain 'final_result'"


# ---------------------------------------------------------------------------
# Test 4 -- openapi.yaml validates (manual fallback, no optional dependency)
# ---------------------------------------------------------------------------

def test_openapi_spec_validates() -> None:
    """docs/api/openapi.yaml must satisfy minimum structural requirements.

    GAP 4 resolution: manual validation checks the defined minimum without
    any optional package. Deterministic regardless of whether
    openapi-spec-validator is installed.

    Minimum checks (always run):
      - Top-level 'openapi' key is a str starting with '3.'
      - info.title is a non-empty str
      - info.version is a non-empty str
      - paths is a dict
      - Required paths present: /run, /audit, /policy/validate, /status
      - Each required path has at least one HTTP method key (post or get)

    Optional check (when openapi-spec-validator is installed):
      - Full schema validation via the library
    """
    import yaml  # PyYAML is a declared runtime dependency

    spec_path = (
        Path(__file__).parent.parent / "docs" / "api" / "openapi.yaml"
    )
    assert spec_path.exists(), f"openapi.yaml not found at {spec_path}"

    with spec_path.open(encoding="utf-8") as fh:
        spec = yaml.safe_load(fh)

    assert isinstance(spec, dict), "openapi.yaml must parse to a dict"

    # --- Minimum: top-level openapi version string ---
    assert "openapi" in spec, "openapi.yaml must have top-level 'openapi' key"
    assert isinstance(spec["openapi"], str), "'openapi' must be a string"
    assert spec["openapi"].startswith("3."), (
        "'openapi' must start with '3.' (got " + repr(spec["openapi"]) + ")"
    )

    # --- Minimum: info.title and info.version ---
    assert "info" in spec, "openapi.yaml must have 'info' section"
    info = spec["info"]
    assert isinstance(info, dict), "'info' must be a dict"
    assert "title" in info and isinstance(info["title"], str) and info["title"].strip(), (
        "info.title must be a non-empty string"
    )
    assert "version" in info and isinstance(info["version"], str) and info["version"].strip(), (
        "info.version must be a non-empty string"
    )

    # --- Minimum: paths dict ---
    assert "paths" in spec, "openapi.yaml must have 'paths' section"
    paths = spec["paths"]
    assert isinstance(paths, dict), "'paths' must be a dict"

    # --- Minimum: required paths present with at least one HTTP method ---
    _required_paths = {"/run", "/audit", "/policy/validate", "/status"}
    _http_methods = {"get", "post", "put", "patch", "delete", "head", "options", "trace"}
    for required_path in _required_paths:
        assert required_path in paths, (
            f"Required path {required_path!r} missing from openapi.yaml paths"
        )
        path_item = paths[required_path]
        assert isinstance(path_item, dict), (
            f"Path item for {required_path!r} must be a dict"
        )
        methods_present = _http_methods.intersection(path_item.keys())
        assert methods_present, (
            f"Path {required_path!r} must have at least one HTTP method key, "
            f"got keys: {sorted(path_item.keys())}"
        )

    # --- Optional: full validation via openapi-spec-validator if installed ---
    try:
        from openapi_spec_validator import validate  # type: ignore[import]
        validate(spec)
    except ImportError:
        pass  # Optional dependency not installed -- manual checks above are sufficient
