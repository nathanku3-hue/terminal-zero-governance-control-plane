from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest


def _write_text(path: Path, text: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _prepare_minimal_repo(repo_root: Path) -> None:
    """Prepare minimal repository structure for phase_end_handover.ps1."""
    context = repo_root / "docs" / "context"
    scripts_dir = repo_root / "scripts"

    # Create required directories
    _write_text(context / "phase_end_logs" / ".keep", "")
    _write_text(context / "evidence_hashes" / ".keep", "")

    # Create minimal traceability file
    traceability = {
        "schema_version": "1.0.0",
        "entries": [
            {
                "pm_id": "PM-001",
                "code_paths": ["scripts/example.py"],
                "test_paths": ["tests/test_example.py"],
            }
        ],
    }
    _write_text(
        context / "pm_to_code_traceability.yaml",
        f"schema_version: '1.0.0'\nentries:\n  - pm_id: PM-001\n    code_paths:\n      - scripts/example.py\n    test_paths:\n      - tests/test_example.py\n",
    )

    # Create worker reply packet
    worker_reply = {
        "schema_version": "1.0.0",
        "worker_id": "test-worker",
        "confidence_score": 0.95,
        "citations": ["docs/context/pm_to_code_traceability.yaml"],
        "reply_text": "Task completed successfully.",
    }
    _write_text(context / "worker_reply_packet.json", json.dumps(worker_reply, indent=2))

    # Create dispatch manifest
    dispatch_manifest = {
        "schema_version": "1.0.0",
        "dispatches": [],
    }
    _write_text(context / "dispatch_manifest.json", json.dumps(dispatch_manifest, indent=2))

    # Create worker status aggregate
    worker_aggregate = {
        "schema_version": "1.0.0",
        "workers": [],
    }
    _write_text(context / "worker_status_aggregate.json", json.dumps(worker_aggregate, indent=2))

    # Create escalation events
    escalation = {
        "schema_version": "1.0.0",
        "events": [],
    }
    _write_text(context / "escalation_events.json", json.dumps(escalation, indent=2))

    # Create stub Python scripts that phase_end_handover.ps1 will invoke
    _write_stub_scripts(scripts_dir)

    # Create example code file referenced in tbility
    _write_text(scripts_dir / "example.py", "# Example code\nprint('hello')\n")
    _write_text(repo_root / "tests" / "test_example.py", "# Example test\ndef test_example():\n    assert True\n")


def _write_stub_scripts(scripts_dir: Path) -> None:
    """Create stub Python scripts that return success."""
    stub_scripts = [
        "build_context_packet.py",
        "aggregate_worker_status.py",
        "validate_traceability.py",
        "validate_evidence_hashes.py",
        "validate_worker_reply_packet.py",
        "validate_orphan_changes.py",
        "validate_dispatch_acks.py",
        "build_ceo_bridge_digest.py",
        "validate_digest_freshness.py",
        "run_auditor_review.py",
        "generate_ceo_go_signal.py",
    ]

    for script_name in stub_scripts:
        script_content = f"""#!/usr/bin/env python3
import sys
import json
from pathlib import Path

# Stub script for {script_name}
# Returns success (exit 0) and creates any required output files

if __name__ == "__main__":
    # Parse common arguments
    args = sys.argv[1:]

    # Handle --output argument
    if "--output" in args:
        idx = args.index("--output")
        if idx + 1 < len(args):
            output_path = Path(args[idx + 1])
            output_path.parent.mkdir(parents=True, exist_ok=True)
            if output_path.suffix == ".json":
                output_path.write_text(json.dumps({{"status": "ok"}}), encoding="utf-8")
            else:
                output_path.write_text("# Output\\nok\\n", encoding="utf-8")

    # Handle --escalation-output argument
    if "--escalation-output" in args:
        idx = args.index("--escalation-output")
        if idx + 1 < len(args):
            output_path = Path(args[idx + 1])
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps({{"events": []}}), encoding="utf-8")

    print("ok")
    sys.exit(0)
"""
        _write_text(scripts_dir / script_name, script_content)


def _write_failing_orphan_script(scripts_dir: Path) -> None:
    """Create validate_orphan_changes.py that fails (orphan changes detected)."""
    script_content = """#!/usr/bin/env python3
import sys

# Simulate orphan changes detected
print("ERROR: Orphan changes detected:")
print("  - scripts/orphan_file.py (not in traceability)")
sys.exit(1)
"""
    _write_text(scripts_dir / "validate_orphan_changes.py", script_content)


def _write_failing_dispatch_script(scripts_dir: Path) -> None:
    """Create validate_dispatch_acks.py that fails (missing dispatch acks)."""
    script_content = """#!/usr/bin/env python3
import sys

# Simulate missing dispatch acknowledgments
print("ERROR: Missing dispatch acknowledgments:")
print("  - dispatch-001: no ack found")
sys.exit(1)
"""
    _write_text(scripts_dir / "validate_dispatch_acks.py", script_content)


@pytest.mark.skipif(
    not Path("C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe").exists(),
    reason="PowerShell not available",
)
def test_phase_end_handover_happy_path(tmp_path: Path) -> None:
    """Test phase_end_handover.ps1 with all gates passing."""
    repo_root = tmp_path / "test_repo"
    repo_root.mkdir()
    _prepare_minimal_repo(repo_root)

    # Copy the actual phase_end_handover.ps1 script
    source_script = Path(__file__).parent.parent / "scripts" / "phase_end_handover.ps1"
    target_script = repo_root / "scripts" / "phase_end_handover.ps1"
    if source_script.exists():
        target_script.parent.mkdir(parents=True, exist_ok=True)
        target_script.write_text(source_script.read_text(encoding="utf-8"), encoding="utf-8")

    # Initialize git repo (required for orphan change detection)
    subprocess.run(["git", "init"], cwd=repo_root, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_root, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_root, check=True, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=repo_root, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_root, check=True, capture_output=True)

    # Run phase_end_handover.ps1
    result = subprocess.run(
        [
            "powershell.exe",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(target_script),
            "-RepoRoot",
            str(repo_root),
            "-SkipOrphanGate",  # Skip orphan gate for simplicity in happy path
            "-SkipDispatchGate",  # Skip dispatch gate for simplicity in happy path
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )

    # Verify execution
    assert result.returncode == 0, f"PowerShell script failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"

    # Verify output artifacts were created
    logs_dir = repo_root / "docs" / "context" / "phase_end_logs"
    assert logs_dir.exists(), "Logs directory not created"

    # Find the status JSON file
    status_files = list(logs_dir.glob("phase_end_handover_status_*.json"))
    assert len(status_files) > 0, "No status JSON file created"

    status_json = status_files[0]
    status_data = json.loads(status_json.read_text(encoding="utf-8-sig"))

    # Verify status structure
    assert status_data["result"] == "PASS", f"Expected PASS, got {status_data['result']}"
    assert status_data["failed_gate"] == "", f"Expected no failed gate, got {status_data['failed_gate']}"
    assert len(status_data["gates"]) > 0, "No gates executed"

    # Verify all gates passed or were skipped
    for gate in status_data["gates"]:
        assert gate["status"] in ["PASS", "SKIPPED"], f"Gate {gate['gate']} failed: {gate['status']}"

    # Verify summary markdown was created
    summary_files = list(logs_dir.glob("phase_end_handover_summary_*.md"))
    assert len(summary_files) > 0, "No summary markdown file created"

    summary_md = summary_files[0].read_text(encoding="utf-8")
    assert "# Phase-End Handover Gate Summary" in summary_md
    assert "Result: PASS" in summary_md


@pytest.mark.skipif(
    not Path("C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe").exists(),
    reason="PowerShell not available",
)
def test_phase_end_handover_orphan_changes_detected(tmp_path: Path) -> None:
    """Test phase_end_handover.ps1 when orphan changes are detected (gate :555 fails)."""
    repo_root = tmp_path / "test_repo"
    repo_root.mkdir()
    _prepare_minimal_repo(repo_root)

    # Replace validate_orphan_changes.py with failing version
    _write_failing_orphan_script(repo_root / "scripts")

    # Copy the actual phase_end_handover.ps1 script
    source_script = Path(__file__).parent.parent / "scripts" / "phase_end_handover.ps1"
    target_script = repo_root / "scripts" / "phase_end_handover.ps1"
    if source_script.exists():
        target_script.write_text(source_script.read_text(encoding="utf-8"), encoding="utf-8")

    # Initialize git repo
    subprocess.run(["git", "init"], cwd=repo_root, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_root, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_root, check=True, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=repo_root, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_root, check=True, capture_output=True)

    # Run phase_end_handover.ps1 WITHOUT skipping orphan gate
    result = subprocess.run(
        [
            "powershell.exe",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(target_script),
            "-RepoRoot",
            str(repo_root),
            "-SkipDispatchGate",  # Skip dispatch gate to isolate orphan gate failure
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )

    # Verify execution failed
    assert result.returncode == 1, f"Expected failure, but got success:\nstdout: {result.stdout}\nstderr: {result.stderr}"

    # Verify output artifacts
    logs_dir = repo_root / "docs" / "context" / "phase_end_logs"
    status_files = list(logs_dir.glob("phase_end_handover_status_*.json"))
    assert len(status_files) > 0, "No status JSON file created"

    status_data = json.loads(status_files[0].read_text(encoding="utf-8-sig"))

    # Verify failure status
    assert status_data["result"] == "BLOCK", f"Expected BLOCK, got {status_data['result']}"
    assert "orphan" in status_data["failed_gate"].lower(), f"Expected orphan gate failure, got {status_data['failed_gate']}"

    # Verify the orphan gate specifically failed
    orphan_gate = next((g for g in status_data["gates"] if "orphan" in g["gate"].lower()), None)
    assert orphan_gate is not None, "Orphan gate not found in results"
    assert orphan_gate["status"] == "BLOCK", f"Expected BLOCK status for orphan gate, got {orphan_gate['status']}"
    assert orphan_gate["exit_code"] == 1, f"Expected exit code 1, got {orphan_gate['exit_code']}"


@pytest.mark.skipif(
    not Path("C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe").exists(),
    reason="PowerShell not available",
)
def test_phase_end_handover_missing_dispatch_acks(tmp_path: Path) -> None:
    """Test phase_end_handover.ps1 when dispatch acks are missing (gate :567 fails)."""
    repo_root = tmp_path / "test_repo"
    repo_root.mkdir()
    _prepare_minimal_repo(repo_root)

    # Replace validate_dispatch_acks.py with failing version
    _write_failing_dispatch_script(repo_root / "scripts")

    # Copy the actual phase_end_handover.ps1 script
    source_script = Path(__file__).parent.parent / "scripts" / "phase_end_handover.ps1"
    target_script = repo_root / "scripts" / "phase_end_handover.ps1"
    if source_script.exists():
        target_script.write_text(source_script.read_text(encoding="utf-8"), encoding="utf-8")

    # Initialize git repo
    subprocess.run(["git", "init"], cwd=repo_root, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_root, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_root, check=True, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=repo_root, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_root, check=True, capture_output=True)

    # Run phase_end_handover.ps1 WITHOUT skipping dispatch gate
    result = subprocess.run(
        [
            "powershell.exe",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(target_script),
            "-RepoRoot",
            str(repo_root),
            "-SkipOrphanGate",  # Skip orphan gate to isolate dispatch gate failure
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )

    # Verify execution failed
    assert result.returncode == 1, f"Expected failure, but got success:\nstdout: {result.stdout}\nstderr: {result.stderr}"

    # Verify output artifacts
    logs_dir = repo_root / "docs" / "context" / "phase_end_logs"
    status_files = list(logs_dir.glob("phase_end_handover_status_*.json"))
    assert len(status_files) > 0, "No status JSON file created"

    status_data = json.loads(status_files[0].read_text(encoding="utf-8-sig"))

    # Verify failure status
    assert status_data["result"] == "BLOCK", f"Expected BLOCK, got {status_data['result']}"
    assert "dispatch" in status_data["failed_gate"].lower(), f"Expected dispatch gate failure, got {status_data['failed_gate']}"

    # Verify the dispatch gate specifically failed
    dispatch_gate = next((g for g in status_data["gates"] if "dispatch" in g["gate"].lower()), None)
    assert dispatch_gate is not None, "Dispatch gate not found in results"
    assert dispatch_gate["status"] == "BLOCK", f"Expected BLOCK status for dispatch gate, got {dispatch_gate['status']}"
    assert dispatch_gate["exit_code"] == 1, f"Expected exit code 1, got {dispatch_gate['exit_code']}"


@pytest.mark.skipif(
    not Path("C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe").exists(),
    reason="PowerShell not available",
)
def test_phase_end_handover_dry_run_mode(tmp_path: Path) -> None:
    """Test phase_end_handover.ps1 in dry-run mode."""
    repo_root = tmp_path / "test_repo"
    repo_root.mkdir()
    _prepare_minimal_repo(repo_root)

    # Copy the actual phase_end_handover.ps1 script
    source_script = Path(__file__).parent.parent / "scripts" / "phase_end_handover.ps1"
    target_script = repo_root / "scripts" / "phase_end_handover.ps1"
    if source_script.exists():
        target_script.write_text(source_script.read_text(encoding="utf-8"), encoding="utf-8")

    # Run phase_end_handover.ps1 in dry-run mode
    result = subprocess.run(
        [
            "powershell.exe",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(target_script),
            "-RepoRoot",
            str(repo_root),
            "-DryRun",
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )

    # Verify execution succeeded
    assert result.returncode == 0, f"Dry-run failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"

    # Verify dry-run output
    assert "[DRY-RUN]" in result.stdout, "Expected dry-run markers in output"

    # Verify no actual files were created (dry-run should not write files)
    logs_dir = repo_root / "docs" / "context" / "phase_end_logs"
    if logs_dir.exists():
        status_files = list(logs_dir.glob("phase_end_handover_status_*.json"))
        # In dry-run mode, status files should NOT be created
        assert len(status_files) == 0, "Status files should not be created in dry-run mode"
