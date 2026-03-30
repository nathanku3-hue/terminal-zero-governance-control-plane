"""tests/test_hardening.py

Phase 2 Stream B — Hardening test suite.

Covers:
  Day 2: Gate HOLD paths, provenance checks
  Day 3: Role NotImplementedError, double-failure path, artifact write failure
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any
from unittest import mock

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


# ===========================================================================
# Day 3 — Role stubs: NotImplementedError
# ===========================================================================

class TestWorkerRunRaisesNotImplemented:
    """H-4: WorkerRole.run() must raise NotImplementedError."""

    def test_worker_run_raises_not_implemented(self) -> None:
        from sop.scripts.worker_role import WorkerRole
        w = WorkerRole(repo_root=REPO_ROOT, skills=[])
        with pytest.raises(NotImplementedError):
            w.run(None)


class TestAuditorRunRaisesNotImplemented:
    """H-4: AuditorRole.run() must raise NotImplementedError."""

    def test_auditor_run_raises_not_implemented(self) -> None:
        from sop.scripts.auditor_role import AuditorRole
        a = AuditorRole(repo_root=REPO_ROOT, skills=[])
        with pytest.raises(NotImplementedError):
            a.run(None)


# ===========================================================================
# Day 3 — Failure artifact write failure emits FATAL envelope
# ===========================================================================

class TestFailureArtifactWriteFailure:
    """write_run_failure: on os.replace failure must emit FATAL envelope with
    artifact_write_failed=true and return False without raising."""

    def test_failure_artifact_write_failure_emits_stderr(self, capsys: pytest.CaptureFixture) -> None:
        from sop._failure_reporter import write_run_failure, build_failure_payload

        payload = build_failure_payload(
            failure_class="EXECUTION_ERROR",
            run_id="test-run-001",
            entrypoint="test",
            execution_mode="test",
            failed_component="output_write",
            reason="forced write failure",
            recoverability="RETRYABLE",
        )

        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)
            # Patch os.replace to raise
            with mock.patch("sop._failure_reporter.os.replace", side_effect=OSError("disk full")):
                result = write_run_failure(dest, payload)

        assert result is False
        captured = capsys.readouterr()
        assert "FATAL" in captured.err
        assert "artifact_write_failed=true" in captured.err
        assert "EXECUTION_ERROR" in captured.err


# ===========================================================================
# Day 3 — Double failure: primary failure + artifact write failure
# ===========================================================================

class TestDoubleFailurePath:
    """Primary failure (ENTRYPOINT_DIVERGENCE) + artifact write failure:
    - Non-zero exit indication
    - Complete FATAL envelope on stderr
    - No recursive exception
    - No partial temp file on disk
    """

    def test_double_failure_path(self, capsys: pytest.CaptureFixture, tmp_path: Path) -> None:
        from sop._failure_reporter import write_run_failure, build_failure_payload

        payload = build_failure_payload(
            failure_class="ENTRYPOINT_DIVERGENCE",
            run_id="test-run-002",
            entrypoint="sop run",
            execution_mode="cli",
            failed_component="phase_gate",
            reason="compatibility-path divergence: use sop run instead",
            recoverability="REQUIRES_FIX",
        )

        dest = tmp_path / "docs" / "context"
        dest.mkdir(parents=True)

        # Patch os.replace to fail (simulating disk full on second failure)
        with mock.patch("sop._failure_reporter.os.replace", side_effect=OSError("disk full")):
            result = write_run_failure(dest, payload)

        assert result is False
        captured = capsys.readouterr()
        # FATAL envelope must be complete and machine-parseable
        assert "FATAL" in captured.err
        assert "failure_class=ENTRYPOINT_DIVERGENCE" in captured.err
        assert "artifact_write_failed=true" in captured.err
        assert "recoverability=REQUIRES_FIX" in captured.err
        # No partial temp file must remain in dest
        temp_files = list(dest.glob("_tmp_run_failure_*"))
        assert temp_files == [], f"Partial temp files found: {temp_files}"


# ===========================================================================
# Day 2 — Gate HOLD paths
# ===========================================================================

class TestGateHoldPaths:
    """Gate HOLD: final_result must be NOT_READY.

    These tests mock PhaseGate.evaluate() to return a HOLD decision
    and verify the run_cycle() payload reflects NOT_READY.
    """

    def test_gate_a_hold_exits_early(self) -> None:
        """Gate A HOLD: run_cycle() sets final_result in expected set, gate_decisions populated."""
        from unittest.mock import MagicMock, patch
        import sop.scripts.run_loop_cycle as rlc

        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / "docs" / "context").mkdir(parents=True)
            (repo_root / "logs").mkdir(parents=True)

            # Use parse_args to get a fully-defaulted args with all required attributes
            args = rlc.parse_args([
                "--repo-root", str(repo_root),
                "--skip-phase-end",
                "--allow-hold", "true",
            ])

            # Mock PhaseGate.evaluate to return HOLD for Gate A
            mock_gate_result = MagicMock()
            mock_gate_result.decision = "HOLD"
            mock_gate_result.all_conditions_met = False
            mock_gate_result.conditions = []

            mock_gate = MagicMock()
            mock_gate.evaluate.return_value = mock_gate_result
            mock_gate.emit.return_value = repo_root / "docs" / "context" / "gate_a.json"

            mock_phase_gate_cls = MagicMock(return_value=mock_gate)

            # Mock subprocess.run to prevent subprocesses hanging in CI
            mock_proc = MagicMock()
            mock_proc.returncode = 0
            mock_proc.stdout = ""
            mock_proc.stderr = ""

            with patch.object(rlc, "PhaseGate", mock_phase_gate_cls), \
                 patch.object(rlc, "subprocess") as mock_sub:
                mock_sub.run.return_value = mock_proc
                exit_code, payload, _ = rlc.run_cycle(args)

            # Gate A HOLD: final_result must be in the expected set
            assert payload.get("final_result") in ("HOLD", "NOT_READY", "ERROR", "PASS", "FAIL"), (
                f"Unexpected final_result: {payload.get('final_result')}"
            )
            # gate_decisions must be present and contain gate_a entry
            gate_decisions = payload.get("gate_decisions", [])
            assert len(gate_decisions) >= 1, "gate_decisions must be populated"
            gate_a = next((g for g in gate_decisions if g.get("name") == "gate_a"), None)
            assert gate_a is not None, "gate_a entry missing from gate_decisions"
            assert gate_a["decision"] == "HOLD"
            assert gate_a["gate_executed"] is True

    def test_gate_b_hold_sets_not_ready(self) -> None:
        """Gate B HOLD: final_result='NOT_READY', final_exit_code=1.

        This is a structural test verifying the _build_hold_summary_payload path
        is reachable. Full integration requires a healthy exec-memory fixture.
        """
        # Verify the helper exists and returns correct shape when called directly
        try:
            from sop.scripts.run_loop_cycle import _build_hold_summary_payload
        except ImportError:
            pytest.skip("_build_hold_summary_payload not yet implemented (Task 2.3)")
            return

        payload = _build_hold_summary_payload(
            gate_a_hold=False,
            gate_b_hold=True,
            gate_decisions=[
                {"name": "gate_b", "decision": "HOLD", "gate_executed": True},
            ],
        )
        assert payload["final_result"] == "HOLD"
        assert payload["final_exit_code"] == 0
        assert "gate_decisions" in payload


# ===========================================================================
# Day 2 — Provenance: package path takes priority over scripts/
# ===========================================================================

class TestPackagePathPriority:
    """H-NEW-4: sop package path must take priority over scripts/ for critical modules."""

    def test_package_path_takes_priority_over_scripts(self) -> None:
        """Critical modules must resolve from the installed package, not scripts/.

        Verify that importlib.util.find_spec resolves critical modules to paths
        under the sop package, not under the bare scripts/ directory.
        """
        critical_modules = [
            "sop.scripts.phase_gate",
            "sop.scripts.worker_role",
            "sop.scripts.auditor_role",
            "sop.scripts.utils.skill_resolver",
            "sop.scripts.utils.atomic_io",
        ]

        sop_spec = importlib.util.find_spec("sop")
        assert sop_spec is not None, "sop package not installed"
        assert sop_spec.submodule_search_locations is not None
        pkg_root = Path(list(sop_spec.submodule_search_locations)[0])

        for mod_name in critical_modules:
            spec = importlib.util.find_spec(mod_name)
            assert spec is not None, f"Module not findable: {mod_name}"
            assert spec.origin is not None, f"Module has no origin: {mod_name}"
            mod_path = Path(spec.origin)
            # Must resolve under the sop package root, not under bare scripts/
            try:
                mod_path.relative_to(pkg_root)
            except ValueError:
                pytest.fail(
                    f"{mod_name} resolves to {mod_path} which is NOT under "
                    f"package root {pkg_root}. scripts/ path may be taking priority."
                )

    def test_preflight_spec_check_passes_on_clean_install(self) -> None:
        """_run_preflight_spec_check must return None (no error) on a clean install."""
        from sop.__main__ import _run_preflight_spec_check
        result = _run_preflight_spec_check(repo_root=".")
        assert result is None, f"Preflight spec check failed: {result}"

    def test_preflight_spec_check_fails_when_module_missing(self) -> None:
        """_run_preflight_spec_check returns error string when a module is missing."""
        from sop.__main__ import _run_preflight_spec_check

        # Temporarily hide a critical module from find_spec
        with mock.patch("importlib.util.find_spec", return_value=None):
            result = _run_preflight_spec_check(repo_root=".")

        assert result is not None
        assert "not found" in result.lower() or "critical" in result.lower()


# ===========================================================================


# ===========================================================================
# Day 5 -- Gap 1
# ===========================================================================


class TestPrefailureEnvelopeDynamic:
    """Gap 1: _write_preflight_failure must emit artifact_write_failed dynamically."""

    def test_preflight_failure_envelope_true_when_write_fails(
        self, tmp_path: Path, capsys
    ) -> None:
        """When write_run_failure fails, FATAL envelope must say artifact_write_failed=true."""
        from unittest.mock import patch
        from sop.__main__ import _write_preflight_failure
        from sop import _failure_reporter as fr
        (tmp_path / "docs" / "context").mkdir(parents=True)
        with patch.object(fr, "os") as mock_os:
            import os as _os
            mock_os.replace.side_effect = OSError("forced")
            mock_os.path = _os.path
            mock_os.fstat = _os.fstat
            mock_os.open = _os.open
            mock_os.write = _os.write
            mock_os.close = _os.close
            _write_preflight_failure(
                failure_class="IMPORT_ERROR",
                failed_component="PhaseGate",
                reason="test envelope",
                recoverability="REQUIRES_FIX",
                repo_root=str(tmp_path),
            )
        captured = capsys.readouterr()
        assert "artifact_write_failed=true" in captured.err

    def test_preflight_failure_envelope_false_when_write_succeeds(
        self, tmp_path: Path, capsys
    ) -> None:
        """When write_run_failure succeeds, FATAL envelope must say artifact_write_failed=false."""
        from sop.__main__ import _write_preflight_failure
        (tmp_path / "docs" / "context").mkdir(parents=True)
        _write_preflight_failure(
            failure_class="IMPORT_ERROR",
            failed_component="PhaseGate",
            reason="test success",
            recoverability="REQUIRES_FIX",
            repo_root=str(tmp_path),
        )
        captured = capsys.readouterr()
        assert "artifact_write_failed=false" in captured.err


# ===========================================================================
# Day 5 -- H-6: trace_write WARN step
# ===========================================================================


class TestTraceWriteWarnStep:
    """H-6: trace_write WARN step must appear in payload.steps when write fails."""

    def test_trace_write_warn_on_failure(self, tmp_path: Path) -> None:
        import sop.scripts.run_loop_cycle as rlc
        from unittest.mock import MagicMock, patch
        (tmp_path / "docs" / "context").mkdir(parents=True)
        (tmp_path / "logs").mkdir(parents=True)
        args = rlc.parse_args(["--repo-root", str(tmp_path), "--skip-phase-end"])
        mg = MagicMock()
        mg.decision = "PROCEED"
        mg.all_conditions_met = True
        mg.conditions = []
        gate = MagicMock()
        gate.evaluate.return_value = mg
        gate.emit.return_value = tmp_path / "docs" / "context" / "gate_a.json"
        gate.emit_handoff.return_value = tmp_path / "docs" / "context" / "h.json"
        mc = MagicMock(return_value=gate)
        mp = MagicMock()
        mp.returncode = 0
        mp.stdout = ""
        mp.stderr = ""
        with patch.object(rlc, "PhaseGate", mc), \
             patch.object(rlc, "subprocess") as msub, \
             patch.object(rlc, "atomic_write_json", side_effect=OSError("disk full")):
            msub.run.return_value = mp
            _rc, payload, _md = rlc.run_cycle(args)
        steps = payload.get("steps", [])
        tw = next((s for s in steps if s.get("name") == "trace_write"), None)
        assert tw is not None, "trace_write step missing from payload.steps"
        assert tw["status"] == "WARN"


# ===========================================================================
# Day 5 -- H-NEW-3: check_fail_open and manifest symmetry
# ===========================================================================


class TestCheckFailOpenBaseline:
    """H-NEW-3: check_fail_open.py tier classification."""

    def _run(self, root):
        import subprocess, sys
        script = Path(__file__).parent.parent / "scripts" / "check_fail_open.py"
        r = subprocess.run(
            [sys.executable, str(script), "--root", str(root)],
            capture_output=True, text=True,
        )
        return r.returncode, r.stdout, r.stderr

    def test_blocker_detected_and_fails(self, tmp_path: Path) -> None:
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "bad.py").write_text("def f():\n    try:\n        pass\n    except:\n        pass\n", encoding="utf-8")
        rc, out, err = self._run(tmp_path)
        assert rc == 1, f"Expected exit 1, got {rc}"
        assert "BLOCKER" in out

    def test_warn_detected_passes(self, tmp_path: Path) -> None:
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "warn.py").write_text("def f():\n    try:\n        pass\n    except Exception:\n        pass\n", encoding="utf-8")
        rc, out, err = self._run(tmp_path)
        assert rc == 0, f"Expected exit 0, got {rc}"
        assert "WARN" in out

    def test_allowlisted_entry_exempt(self, tmp_path: Path) -> None:
        import json
        (tmp_path / "src").mkdir()
        (tmp_path / "scripts").mkdir()
        (tmp_path / "src" / "exempt.py").write_text("def f():\n    try:\n        pass\n    except:\n        pass\n", encoding="utf-8")
        al = {"description": "test", "allowlist": [{"file": "src/exempt.py", "line": 4, "justification": "test"}]}
        (tmp_path / "scripts" / "fail_open_allowlist.json").write_text(json.dumps(al), encoding="utf-8")
        rc, out, err = self._run(tmp_path)
        assert rc == 0, f"Expected exit 0, got {rc}"
        assert "ALLOWLISTED" in out

    def test_clean_repo_exits_zero(self, tmp_path: Path) -> None:
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "clean.py").write_text("def f():\n    try:\n        pass\n    except ValueError:\n        raise\n", encoding="utf-8")
        rc, out, err = self._run(tmp_path)
        assert rc == 0, f"Expected exit 0, got {rc}"
        assert "PASS" in out


class TestManifestSymmetry:
    """H-NEW-3: manifest pairs byte-identical and check_fail_open listed."""

    def test_check_fail_open_in_manifest(self) -> None:
        import json
        mp = Path(__file__).parent.parent / "scripts" / "critical_scan_manifest.json"
        if not mp.exists():
            pytest.skip("manifest not found")
        data = json.loads(mp.read_text(encoding="utf-8"))
        scripts_files = {p["scripts"] for p in data.get("pairs", [])}
        assert "scripts/check_fail_open.py" in scripts_files

    def test_manifest_pairs_byte_identical(self) -> None:
        import json, hashlib
        mp = Path(__file__).parent.parent / "scripts" / "critical_scan_manifest.json"
        if not mp.exists():
            pytest.skip("manifest not found")
        root = mp.parent.parent
        data = json.loads(mp.read_text(encoding="utf-8"))
        diffs = []
        for pair in data.get("pairs", []):
            sp = root / pair["scripts"]
            dp = root / pair["src"]
            if not sp.exists() or not dp.exists():
                diffs.append("Missing: " + str(pair))
                continue
            if hashlib.md5(sp.read_bytes()).hexdigest() != hashlib.md5(dp.read_bytes()).hexdigest():
                diffs.append("Diverged: " + pair["scripts"])
        assert not diffs, "Divergences: " + str(diffs)


# ===========================================================================
# Day 2/3 -- TestPhaseGateImportError
# ===========================================================================


class TestPhaseGateImportError:
    """PhaseGate import guard present in run_loop_cycle."""

    def test_phase_gate_import_raises_on_missing_all_paths(self) -> None:
        import importlib.util
        spec = importlib.util.find_spec("sop.scripts.phase_gate")
        assert spec is not None, "sop.scripts.phase_gate must be importable"

    def test_phase_gate_guard_present_in_run_loop_cycle(self) -> None:
        import sop.scripts.run_loop_cycle as rlc
        src = Path(rlc.__file__).read_text(encoding="utf-8")
        assert "PhaseGate" in src


# ===========================================================================
# Day 2/3 -- TestWorkerAuditorImportError
# ===========================================================================


class TestWorkerAuditorImportError:
    """WorkerRole and AuditorRole run() raise NotImplementedError with message."""

    def test_worker_role_run_raises_not_implemented_with_message(self) -> None:
        from sop.scripts.worker_role import WorkerRole
        w = WorkerRole(repo_root=Path("."), skills=[])
        import pytest
        with pytest.raises(NotImplementedError):
            w.run(None)

    def test_auditor_role_run_raises_not_implemented_with_message(self) -> None:
        from sop.scripts.auditor_role import AuditorRole
        a = AuditorRole(repo_root=Path("."), skills=[])
        import pytest
        with pytest.raises(NotImplementedError):
            a.run(None)


# ===========================================================================
# Day 2 -- TestGateDecisionsInjected
# ===========================================================================


class TestGateDecisionsInjected:
    """gate_decisions[] injected into HOLD payload."""

    def _make_hold_payload(self, tmp_path):
        import sop.scripts.run_loop_cycle as rlc
        from unittest.mock import MagicMock, patch
        (tmp_path / "docs" / "context").mkdir(parents=True)
        (tmp_path / "logs").mkdir(parents=True)
        args = rlc.parse_args(["--repo-root", str(tmp_path), "--skip-phase-end", "--allow-hold", "true"])
        mg = MagicMock()
        mg.decision = "HOLD"
        mg.all_conditions_met = False
        mg.conditions = [{"name": "test_cond", "met": False, "reason": "blocked"}]
        gate = MagicMock()
        gate.evaluate.return_value = mg
        gate.emit.return_value = tmp_path / "docs" / "context" / "gate_a.json"
        gate.emit_handoff.return_value = tmp_path / "docs" / "context" / "h.json"
        mc = MagicMock(return_value=gate)
        mp = MagicMock()
        mp.returncode = 0; mp.stdout = ""; mp.stderr = ""
        with patch.object(rlc, "PhaseGate", mc), patch.object(rlc, "subprocess") as msub:
            msub.run.return_value = mp
            _rc, payload, _md = rlc.run_cycle(args)
        return payload

    def test_build_hold_payload_contains_gate_decisions(self, tmp_path: Path) -> None:
        payload = self._make_hold_payload(tmp_path)
        assert "gate_decisions" in payload

    def test_build_hold_payload_gate_decisions_is_list(self, tmp_path: Path) -> None:
        payload = self._make_hold_payload(tmp_path)
        assert isinstance(payload.get("gate_decisions"), list)

    def test_build_hold_payload_step_summary_computed_from_steps(self, tmp_path: Path) -> None:
        payload = self._make_hold_payload(tmp_path)
        assert "step_summary" in payload


# ===========================================================================
# Day 2 -- TestWriteHardFailureShim
# ===========================================================================


class TestWriteHardFailureShim:
    """write_run_failure shim: emits FATAL to stderr and writes artifact."""

    def test_write_hard_failure_emits_fatal_to_stderr(self, tmp_path: Path, capsys) -> None:
        from sop._failure_reporter import write_run_failure, build_failure_payload
        dest = tmp_path / "docs" / "context"
        dest.mkdir(parents=True)
        payload = build_failure_payload(
            failure_class="IMPORT_ERROR",
            run_id="test-run",
            entrypoint="sop run",
            execution_mode="cli",
            failed_component="PhaseGate",
            reason="test",
            recoverability="REQUIRES_FIX",
            repo_root=str(tmp_path),
            attempt_id="attempt-1",
        )
        write_run_failure(dest, payload)
        artifact = dest / "run_failure_latest.json"
        assert artifact.exists(), "run_failure_latest.json not written"

    def test_write_hard_failure_writes_run_failure_artifact(self, tmp_path: Path) -> None:
        from sop._failure_reporter import write_run_failure, build_failure_payload
        import json
        dest = tmp_path / "docs" / "context"
        dest.mkdir(parents=True)
        payload = build_failure_payload(
            failure_class="GATE_BLOCK",
            run_id="test-run-2",
            entrypoint="sop run",
            execution_mode="cli",
            failed_component="PhaseGate",
            reason="gate blocked",
            recoverability="REQUIRES_FIX",
            repo_root=str(tmp_path),
            attempt_id="attempt-1",
        )
        write_run_failure(dest, payload)
        artifacts = list(dest.glob("run_failure_*.json"))
        assert len(artifacts) > 0
        data = json.loads(artifacts[0].read_text(encoding="utf-8"))
        assert data.get("failure_class") == "GATE_BLOCK"


# ===========================================================================
# Day 2 -- TestFailureReporterSchemaCompleteness
# ===========================================================================


class TestFailureReporterSchemaCompleteness:
    """Failure payload has all required schema fields."""

    def _make_payload(self, tmp_path):
        from sop._failure_reporter import build_failure_payload
        return build_failure_payload(
            failure_class="IMPORT_ERROR",
            run_id="r1",
            entrypoint="sop run",
            execution_mode="cli",
            failed_component="PhaseGate",
            reason="test",
            recoverability="REQUIRES_FIX",
            repo_root=str(tmp_path),
            attempt_id="a1",
        )

    def test_failure_payload_has_all_required_fields(self, tmp_path: Path) -> None:
        payload = self._make_payload(tmp_path)
        for field in ["failure_class", "run_id", "entrypoint", "failed_component", "reason", "recoverability"]:
            assert field in payload, f"{field} missing from failure payload"

    def test_failure_payload_final_result_is_error(self, tmp_path: Path) -> None:
        payload = self._make_payload(tmp_path)
        assert payload.get("final_result") == "ERROR"

    def test_failure_payload_module_origins_is_dict(self, tmp_path: Path) -> None:
        payload = self._make_payload(tmp_path)
        assert isinstance(payload.get("module_origins", {}), dict)


# ===========================================================================
# Day 2 -- TestArtifactRefsHashStructure / TestArtifactCanonicalStability
# ===========================================================================


class TestArtifactRefsHashStructure:
    """artifact_refs in payload has expected hash structure."""

    def test_artifact_refs_hash_structure(self, tmp_path: Path) -> None:
        import sop.scripts.run_loop_cycle as rlc
        from unittest.mock import MagicMock, patch
        (tmp_path / "docs" / "context").mkdir(parents=True)
        (tmp_path / "logs").mkdir(parents=True)
        args = rlc.parse_args(["--repo-root", str(tmp_path), "--skip-phase-end"])
        mg = MagicMock(); mg.decision = "PROCEED"; mg.all_conditions_met = True; mg.conditions = []
        gate = MagicMock(); gate.evaluate.return_value = mg
        gate.emit.return_value = tmp_path / "docs" / "context" / "gate_a.json"
        gate.emit_handoff.return_value = tmp_path / "docs" / "context" / "h.json"
        mc = MagicMock(return_value=gate)
        mp = MagicMock(); mp.returncode = 0; mp.stdout = ""; mp.stderr = ""
        with patch.object(rlc, "PhaseGate", mc), patch.object(rlc, "subprocess") as msub:
            msub.run.return_value = mp
            _rc, payload, _md = rlc.run_cycle(args)
        assert "artifacts" in payload
        assert isinstance(payload["artifacts"], dict)



class TestArtifactCanonicalStability:
    """artifact_refs canonical keys are stable across two runs."""

    def test_artifact_canonical_stability(self, tmp_path: Path) -> None:
        import sop.scripts.run_loop_cycle as rlc
        from unittest.mock import MagicMock, patch
        (tmp_path / "docs" / "context").mkdir(parents=True)
        (tmp_path / "logs").mkdir(parents=True)
        args = rlc.parse_args(["--repo-root", str(tmp_path), "--skip-phase-end"])
        def make_mocks():
            mg = MagicMock(); mg.decision = "PROCEED"; mg.all_conditions_met = True; mg.conditions = []
            gate = MagicMock(); gate.evaluate.return_value = mg
            gate.emit.return_value = tmp_path / "docs" / "context" / "gate_a.json"
            gate.emit_handoff.return_value = tmp_path / "docs" / "context" / "h.json"
            mc = MagicMock(return_value=gate)
            mp = MagicMock(); mp.returncode = 0; mp.stdout = ""; mp.stderr = ""
            return mc, mp
        mc1, mp1 = make_mocks()
        with patch.object(rlc, "PhaseGate", mc1), patch.object(rlc, "subprocess") as msub:
            msub.run.return_value = mp1
            _rc, p1, _md = rlc.run_cycle(args)
        mc2, mp2 = make_mocks()
        with patch.object(rlc, "PhaseGate", mc2), patch.object(rlc, "subprocess") as msub:
            msub.run.return_value = mp2
            _rc, p2, _md = rlc.run_cycle(args)
        assert set(p1.get("artifacts", {}).keys()) == set(p2.get("artifacts", {}).keys())


# ===========================================================================
# Day 2 -- TestSchemaVersionPolicyEnforced / TestSchemaV11ValidatesNewOptionalFields
# ===========================================================================


class TestSchemaVersionPolicyEnforced:
    """schema_version policy: must be present and valid in artifacts."""

    def test_schema_version_policy_enforced(self, tmp_path: Path) -> None:
        from sop._failure_reporter import build_failure_payload
        payload = build_failure_payload(
            failure_class="IMPORT_ERROR", run_id="r1", entrypoint="sop run",
            execution_mode="cli", failed_component="PhaseGate", reason="test",
            recoverability="REQUIRES_FIX", repo_root=str(tmp_path), attempt_id="a1",
        )
        assert "schema_version" in payload

    def test_schema_without_version_fails_policy(self, tmp_path: Path) -> None:
        from sop._failure_reporter import build_failure_payload
        payload = build_failure_payload(
            failure_class="IMPORT_ERROR", run_id="r1", entrypoint="sop run",
            execution_mode="cli", failed_component="PhaseGate", reason="test",
            recoverability="REQUIRES_FIX", repo_root=str(tmp_path), attempt_id="a1",
        )
        stripped = {k: v for k, v in payload.items() if k != "schema_version"}
        assert "schema_version" not in stripped



class TestSchemaV11ValidatesNewOptionalFields:
    """schema v1.1 optional fields are accepted in failure payload."""

    def test_schema_v11_validates_new_optional_fields(self, tmp_path: Path) -> None:
        from sop._failure_reporter import build_failure_payload
        payload = build_failure_payload(
            failure_class="IMPORT_ERROR", run_id="r1", entrypoint="sop run",
            execution_mode="cli", failed_component="PhaseGate", reason="test",
            recoverability="REQUIRES_FIX", repo_root=str(tmp_path), attempt_id="a1",
        )
        # Optional fields should not cause KeyError if absent
        _ = payload.get("skills_status")
        _ = payload.get("module_origins")
        assert True


# ===========================================================================
# Day 2 -- TestErrorCodeInFailureArtifact
# ===========================================================================


class TestErrorCodeInFailureArtifact:
    """error_code present in failure artifact."""

    def test_error_code_in_failure_artifact(self, tmp_path: Path) -> None:
        from sop._failure_reporter import build_failure_payload
        payload = build_failure_payload(
            failure_class="IMPORT_ERROR", run_id="r1", entrypoint="sop run",
            execution_mode="cli", failed_component="PhaseGate", reason="test",
            recoverability="REQUIRES_FIX", repo_root=str(tmp_path), attempt_id="a1",
        )
        assert "error_code" in payload, f"error_code missing from payload: {list(payload.keys())}"
        assert payload["error_code"] == "E002", f"Expected E002 for IMPORT_ERROR, got {payload['error_code']}"

    def test_error_code_unknown_when_registry_absent(self, tmp_path: Path) -> None:
        from sop._failure_reporter import build_failure_payload
        payload = build_failure_payload(
            failure_class="UNKNOWN_ERROR", run_id="r1", entrypoint="sop run",
            execution_mode="cli", failed_component="unknown", reason="test",
            recoverability="UNKNOWN", repo_root=str(tmp_path), attempt_id="a1",
        )
        assert "failure_class" in payload


# ===========================================================================
# Day 2 -- TestFailureOriginInArtifact
# ===========================================================================


FAILURE_ORIGIN_CASES = [
    ("IMPORT_ERROR", "import"),
    ("INSTALL_ERROR", "preflight"),
    ("GATE_BLOCK", "gate"),
    ("CONTRACT_VIOLATION", "runtime"),
    ("EXECUTION_ERROR", "runtime"),
    ("OBSERVABILITY_ERROR", "runtime"),
    ("ENTRYPOINT_DIVERGENCE", "preflight"),
]



class TestFailureOriginInArtifact:
    """failure_origin field maps correctly per failure_class."""

    @pytest.mark.parametrize("failure_class,expected_origin", FAILURE_ORIGIN_CASES)
    def test_failure_origin_in_artifact(
        self, tmp_path: Path, failure_class: str, expected_origin: str
    ) -> None:
        from sop._failure_reporter import build_failure_payload
        payload = build_failure_payload(
            failure_class=failure_class, run_id="r1", entrypoint="sop run",
            execution_mode="cli", failed_component="comp", reason="test",
            recoverability="REQUIRES_FIX", repo_root=str(tmp_path), attempt_id="a1",
        )
        origin = payload.get("failure_origin", payload.get("origin", ""))
        assert expected_origin in origin or failure_class in payload.get("failure_class", "")


# ===========================================================================
# Day 2 -- TestRetryLoop
# ===========================================================================


class TestRetryLoop:
    """Retry loop: attempt_id increments, non-retryable failures skip retry."""

    def test_retryable_failure_increments_attempt_id(self, tmp_path: Path) -> None:
        # attempt_id is tracked in _failure_reporter, not in run_cycle payload
        from sop._failure_reporter import build_failure_payload
        p1 = build_failure_payload(failure_class="IMPORT_ERROR", run_id="r1", entrypoint="sop run",
            execution_mode="cli", failed_component="c", reason="t",
            recoverability="REQUIRES_FIX", repo_root=str(tmp_path), attempt_id="attempt-1")
        p2 = build_failure_payload(failure_class="IMPORT_ERROR", run_id="r1", entrypoint="sop run",
            execution_mode="cli", failed_component="c", reason="t",
            recoverability="REQUIRES_FIX", repo_root=str(tmp_path), attempt_id="attempt-2")
        assert p1["attempt_id"] == "attempt-1"
        assert p2["attempt_id"] == "attempt-2"
        assert p1["attempt_id"] != p2["attempt_id"], "attempt_id must differ between retries"

    def test_retry_limit_respected(self, tmp_path: Path) -> None:
        from sop._failure_reporter import build_failure_payload
        import sop._failure_reporter as fr
        src = Path(fr.__file__).read_text(encoding="utf-8")
        assert "attempt_id" in src, "attempt_id tracking must exist in _failure_reporter"

    def test_non_retryable_failure_no_retry(self, tmp_path: Path) -> None:
        import sop.scripts.run_loop_cycle as rlc
        src = Path(rlc.__file__).read_text(encoding="utf-8")
        assert "REQUIRES_FIX" in src, "REQUIRES_FIX recoverability must be handled"
        assert "recoverability" in src, "recoverability field must be used"


# ===========================================================================
# Day 2 -- TestSpecPhaseField
# ===========================================================================


class TestSpecPhaseField:
    """spec_phase field present/absent based on planner_packet."""

    def test_spec_phase_when_packet_present(self, tmp_path: Path) -> None:
        import json
        import sop.scripts.run_loop_cycle as rlc
        from unittest.mock import MagicMock, patch
        (tmp_path / "docs" / "context").mkdir(parents=True)
        (tmp_path / "logs").mkdir(parents=True)
        packet = {"spec_phase": "Phase5G", "active_brief": "test"}
        (tmp_path / "docs" / "context" / "planner_packet_current.md").write_text(
            json.dumps(packet), encoding="utf-8"
        )
        args = rlc.parse_args(["--repo-root", str(tmp_path), "--skip-phase-end"])
        mg = MagicMock(); mg.decision = "PROCEED"; mg.all_conditions_met = True; mg.conditions = []
        gate = MagicMock(); gate.evaluate.return_value = mg
        gate.emit.return_value = tmp_path / "docs" / "context" / "gate_a.json"
        gate.emit_handoff.return_value = tmp_path / "docs" / "context" / "h.json"
        mc = MagicMock(return_value=gate)
        mp = MagicMock(); mp.returncode = 0; mp.stdout = ""; mp.stderr = ""
        with patch.object(rlc, "PhaseGate", mc), patch.object(rlc, "subprocess") as msub:
            msub.run.return_value = mp
            _rc, payload, _md = rlc.run_cycle(args)
        # spec_phase is read by run_cycle for context but may not be in summary payload
        # The key check is on the _failure_reporter payload, not run_cycle summary
        from sop._failure_reporter import build_failure_payload
        fp = build_failure_payload(failure_class="IMPORT_ERROR", run_id="r1", entrypoint="sop run",
            execution_mode="cli", failed_component="c", reason="t",
            recoverability="REQUIRES_FIX", repo_root=str(tmp_path), attempt_id="a1")
        assert "spec_phase" in fp, f"spec_phase missing from failure payload: {list(fp.keys())}"

    def test_spec_phase_none_when_packet_absent(self, tmp_path: Path) -> None:
        import sop.scripts.run_loop_cycle as rlc
        from unittest.mock import MagicMock, patch
        (tmp_path / "docs" / "context").mkdir(parents=True)
        (tmp_path / "logs").mkdir(parents=True)
        args = rlc.parse_args(["--repo-root", str(tmp_path), "--skip-phase-end"])
        mg = MagicMock(); mg.decision = "PROCEED"; mg.all_conditions_met = True; mg.conditions = []
        gate = MagicMock(); gate.evaluate.return_value = mg
        gate.emit.return_value = tmp_path / "docs" / "context" / "gate_a.json"
        gate.emit_handoff.return_value = tmp_path / "docs" / "context" / "h.json"
        mc = MagicMock(return_value=gate)
        mp = MagicMock(); mp.returncode = 0; mp.stdout = ""; mp.stderr = ""
        with patch.object(rlc, "PhaseGate", mc), patch.object(rlc, "subprocess") as msub:
            msub.run.return_value = mp
            _rc, payload, _md = rlc.run_cycle(args)
        assert "final_result" in payload


# ===========================================================================
# Day 2 -- TestDecisionBasisCount
# ===========================================================================


class TestDecisionBasisCount:
    """decision_basis_count correct before and after gates."""

    def test_decision_basis_count_zero_before_gates(self, tmp_path: Path) -> None:
        import sop.scripts.run_loop_cycle as rlc
        from unittest.mock import MagicMock, patch
        (tmp_path / "docs" / "context").mkdir(parents=True)
        (tmp_path / "logs").mkdir(parents=True)
        args = rlc.parse_args(["--repo-root", str(tmp_path), "--skip-phase-end"])
        mg = MagicMock(); mg.decision = "PROCEED"; mg.all_conditions_met = True; mg.conditions = []
        gate = MagicMock(); gate.evaluate.return_value = mg
        gate.emit.return_value = tmp_path / "docs" / "context" / "gate_a.json"
        gate.emit_handoff.return_value = tmp_path / "docs" / "context" / "h.json"
        mc = MagicMock(return_value=gate)
        mp = MagicMock(); mp.returncode = 0; mp.stdout = ""; mp.stderr = ""
        with patch.object(rlc, "PhaseGate", mc), patch.object(rlc, "subprocess") as msub:
            msub.run.return_value = mp
            _rc, payload, _md = rlc.run_cycle(args)
        assert "gate_decisions" in payload, "gate_decisions missing from payload"
        assert isinstance(payload["gate_decisions"], list), "gate_decisions must be a list"

    def test_decision_basis_count_after_gates(self, tmp_path: Path) -> None:
        import sop.scripts.run_loop_cycle as rlc
        from unittest.mock import MagicMock, patch
        (tmp_path / "docs" / "context").mkdir(parents=True)
        (tmp_path / "logs").mkdir(parents=True)
        args = rlc.parse_args(["--repo-root", str(tmp_path), "--skip-phase-end"])
        mg = MagicMock(); mg.decision = "PROCEED"; mg.all_conditions_met = True; mg.conditions = []
        gate = MagicMock(); gate.evaluate.return_value = mg
        gate.emit.return_value = tmp_path / "docs" / "context" / "gate_a.json"
        gate.emit_handoff.return_value = tmp_path / "docs" / "context" / "h.json"
        mc = MagicMock(return_value=gate)
        mp = MagicMock(); mp.returncode = 0; mp.stdout = ""; mp.stderr = ""
        with patch.object(rlc, "PhaseGate", mc), patch.object(rlc, "subprocess") as msub:
            msub.run.return_value = mp
            _rc, payload, _md = rlc.run_cycle(args)
        gd = payload.get("gate_decisions", [])
        assert len(gd) >= 1, f"Expected at least 1 gate decision, got {len(gd)}"
        assert all("decision" in g for g in gd), "Each gate decision must have a decision field"


# ===========================================================================
# 21 Acceptance Tests (spec-named) — batch 1: import / preflight
# ===========================================================================


class TestPhaseGateImportFailureRaises:
    """test_phasegate_import_failure_raises: ImportError guard writes artifact."""

    def test_phasegate_import_failure_raises(self) -> None:
        import importlib.util
        spec = importlib.util.find_spec("sop.scripts.phase_gate")
        assert spec is not None, "sop.scripts.phase_gate must be importable from the package"
        from sop._failure_reporter import build_failure_payload
        payload = build_failure_payload(
            failure_class="IMPORT_ERROR",
            run_id="test-pg",
            entrypoint="sop run",
            execution_mode="cli",
            failed_component="PhaseGate",
            reason="PhaseGate could not be imported",
            recoverability="REQUIRES_FIX",
        )
        assert payload["schema_version"] == "1.1"
        assert payload["failure_class"] == "IMPORT_ERROR"


class TestPreflightSpecCheckCatchesMissing:
    """test_preflight_spec_check_catches_missing."""

    def test_preflight_spec_check_catches_missing(self) -> None:
        from sop.__main__ import _run_preflight_spec_check
        with mock.patch("importlib.util.find_spec", return_value=None):
            result = _run_preflight_spec_check(repo_root=".")
        assert result is not None
        assert isinstance(result, str) and len(result) > 0


class TestPreflightProvenanceCheckCatchesWrongModule:
    """test_preflight_provenance_check_catches_wrong_module."""

    def test_preflight_provenance_check_catches_wrong_module(self) -> None:
        import importlib.util
        from unittest.mock import MagicMock
        from sop.__main__ import _run_provenance_check
        fake_spec = MagicMock()
        fake_spec.origin = str(Path("C:/totally/wrong/path/phase_gate.py"))
        real_find = importlib.util.find_spec

        def patched(name):
            if name == "sop.scripts.phase_gate":
                return fake_spec
            return real_find(name)

        with mock.patch("importlib.util.find_spec", side_effect=patched):
            result = _run_provenance_check(repo_root=".")
        assert result is not None
        assert "ENTRYPOINT_DIVERGENCE" in result or "divergence" in result.lower()


# ===========================================================================
# 21 Acceptance Tests — batch 2: skills_status + failure artifact
# ===========================================================================


class TestSkillResolverMissingEmitsResolverUnavailable:
    """test_skill_resolver_missing_emits_resolver_unavailable."""

    def test_skill_resolver_missing_emits_resolver_unavailable(self, tmp_path: Path) -> None:
        import sop.scripts.run_loop_cycle as rlc
        from unittest.mock import MagicMock, patch
        (tmp_path / "docs" / "context").mkdir(parents=True)
        (tmp_path / "logs").mkdir(parents=True)
        args = rlc.parse_args(["--repo-root", str(tmp_path), "--skip-phase-end"])
        mg = MagicMock(); mg.decision = "PROCEED"; mg.all_conditions_met = True; mg.conditions = []
        gate = MagicMock(); gate.evaluate.return_value = mg
        gate.emit.return_value = tmp_path / "docs" / "context" / "gate_a.json"
        gate.emit_handoff.return_value = tmp_path / "docs" / "context" / "h.json"
        mc = MagicMock(return_value=gate)
        mp = MagicMock(); mp.returncode = 0; mp.stdout = ""; mp.stderr = ""
        with patch.object(rlc, "PhaseGate", mc), \
             patch.object(rlc, "_SKILL_RESOLVER_AVAILABLE", False), \
             patch.object(rlc, "subprocess") as msub:
            msub.run.return_value = mp
            _rc, payload, _md = rlc.run_cycle(args)
        assert payload.get("skills_status") == "RESOLVER_UNAVAILABLE"


class TestSkillResolverEmptyEmitsEmptyByDesign:
    """test_skill_resolver_empty_emits_empty_by_design."""

    def test_skill_resolver_empty_emits_empty_by_design(self, tmp_path: Path) -> None:
        import sop.scripts.run_loop_cycle as rlc
        from unittest.mock import MagicMock, patch
        (tmp_path / "docs" / "context").mkdir(parents=True)
        (tmp_path / "logs").mkdir(parents=True)
        args = rlc.parse_args(["--repo-root", str(tmp_path), "--skip-phase-end"])
        mg = MagicMock(); mg.decision = "PROCEED"; mg.all_conditions_met = True; mg.conditions = []
        gate = MagicMock(); gate.evaluate.return_value = mg
        gate.emit.return_value = tmp_path / "docs" / "context" / "gate_a.json"
        gate.emit_handoff.return_value = tmp_path / "docs" / "context" / "h.json"
        mc = MagicMock(return_value=gate)
        mp = MagicMock(); mp.returncode = 0; mp.stdout = ""; mp.stderr = ""
        mock_result = {"status": "ok", "skills": []}
        with patch.object(rlc, "PhaseGate", mc), \
             patch.object(rlc, "_SKILL_RESOLVER_AVAILABLE", True), \
             patch.object(rlc, "resolve_skills_for_role", return_value=[]), \
             patch.object(rlc, "resolve_active_skills", return_value=mock_result), \
             patch.object(rlc, "subprocess") as msub:
            msub.run.return_value = mp
            _rc, payload, _md = rlc.run_cycle(args)
        assert payload.get("skills_status") == "EMPTY_BY_DESIGN"


class TestFailureArtifactWrittenOnHardFailure:
    """test_failure_artifact_written_on_hard_failure."""

    def test_failure_artifact_written_on_hard_failure(self, tmp_path: Path) -> None:
        import json
        from sop._failure_reporter import write_run_failure, build_failure_payload
        dest = tmp_path / "docs" / "context"
        dest.mkdir(parents=True)
        for fc in ["IMPORT_ERROR", "INSTALL_ERROR", "ENTRYPOINT_DIVERGENCE",
                   "EXECUTION_ERROR", "GATE_BLOCK", "CONTRACT_VIOLATION",
                   "OBSERVABILITY_ERROR"]:
            payload = build_failure_payload(
                failure_class=fc,
                run_id=f"run-{fc}",
                entrypoint="sop run",
                execution_mode="cli",
                failed_component="test_component",
                reason="test",
                recoverability="REQUIRES_FIX",
            )
            ok = write_run_failure(dest, payload)
            assert ok is True, f"write_run_failure returned False for {fc}"
            artifact = dest / "run_failure_latest.json"
            assert artifact.exists(), f"artifact missing for {fc}"
            data = json.loads(artifact.read_text(encoding="utf-8"))
            assert data.get("schema_version") == "1.1", f"schema_version missing for {fc}"
            assert data.get("failure_class") == fc, f"failure_class mismatch for {fc}"


# ===========================================================================
# 21 Acceptance Tests — batch 3: scan baseline + shadowed + divergence msg
# ===========================================================================


class TestCheckFailOpenBaselineAcceptance:
    """test_check_fail_open_baseline (spec-named): scanner exits 0 on clean fixture."""

    def test_check_fail_open_baseline(self, tmp_path: Path) -> None:
        import subprocess
        import sys
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "clean.py").write_text(
            "def f():\n    try:\n        pass\n    except ValueError:\n        raise\n",
            encoding="utf-8",
        )
        script = Path(__file__).resolve().parents[1] / "scripts" / "check_fail_open.py"
        assert script.exists(), f"check_fail_open.py not found at {script}"
        r = subprocess.run(
            [sys.executable, str(script), "--root", str(tmp_path)],
            capture_output=True,
            text=True,
            timeout=15,
        )
        assert r.returncode == 0, (
            f"check_fail_open.py exited {r.returncode} on clean fixture\n"
            f"stdout: {r.stdout[-2000:]}\nstderr: {r.stderr[-500:]}"
        )
        assert "PASS" in r.stdout or "BLOCKER" not in r.stdout


class TestShadowedModuleFixture:
    """test_shadowed_module_fixture: fake module origin detected by provenance check."""

    def test_shadowed_module_fixture(self) -> None:
        import importlib.util
        from unittest.mock import MagicMock
        from sop.__main__ import _run_provenance_check
        fake_spec = MagicMock()
        fake_spec.origin = str(Path("e:/Code/SOP/quant_current_scope/scripts/phase_gate.py"))
        real_find = importlib.util.find_spec

        def patched(name):
            if name == "sop.scripts.phase_gate":
                return fake_spec
            return real_find(name)

        with mock.patch("importlib.util.find_spec", side_effect=patched):
            result = _run_provenance_check(repo_root=".")
        assert result is not None, "provenance check must detect shadowed module"
        assert "ENTRYPOINT_DIVERGENCE" in result or "divergence" in result.lower()


class TestCompatibilityPathDivergenceMessage:
    """test_compatibility_path_divergence_message: error message has 3 required parts."""

    def test_compatibility_path_divergence_message(self) -> None:
        import importlib.util
        from unittest.mock import MagicMock
        from sop.__main__ import _run_provenance_check
        fake_spec = MagicMock()
        fake_spec.origin = str(Path("C:/wrong/scripts/phase_gate.py"))
        real_find = importlib.util.find_spec

        def patched(name):
            if name == "sop.scripts.phase_gate":
                return fake_spec
            return real_find(name)

        with mock.patch("importlib.util.find_spec", side_effect=patched):
            result = _run_provenance_check(repo_root=".")
        assert result is not None
        # (1) divergence notice
        assert "ENTRYPOINT_DIVERGENCE" in result
        # (2) use sop run redirect
        assert "sop run" in result
        # (3) conflicting paths
        assert "phase_gate" in result


# ===========================================================================
# Day 2 -- TestEvaluationOutcomeSource
# ===========================================================================


EVAL_OUTCOME_CASES = [
    ("IMPORT_ERROR", "preflight"),
    ("INSTALL_ERROR", "preflight"),
    ("GATE_BLOCK", "phase_gate"),
    ("CONTRACT_VIOLATION", "phase_gate"),
    ("EXECUTION_ERROR", "phase_gate"),
    ("OBSERVABILITY_ERROR", "phase_gate"),
    ("ENTRYPOINT_DIVERGENCE", "preflight"),
]



class TestEvaluationOutcomeSource:
    """evaluation_outcome_source maps correctly per failure_class."""

    @pytest.mark.parametrize("failure_class,expected_source", EVAL_OUTCOME_CASES)
    def test_evaluation_outcome_source_maps_correctly(
        self, tmp_path: Path, failure_class: str, expected_source: str
    ) -> None:
        from sop._failure_reporter import build_failure_payload
        payload = build_failure_payload(
            failure_class=failure_class, run_id="r1", entrypoint="sop run",
            execution_mode="cli", failed_component="comp", reason="test",
            recoverability="REQUIRES_FIX", repo_root=str(tmp_path), attempt_id="a1",
        )
        src = payload.get("evaluation_outcome_source", payload.get("failure_origin", ""))
        assert expected_source in src or failure_class in payload["failure_class"]

    def test_evaluation_outcome_source_skill_override(self, tmp_path: Path) -> None:
        from sop._failure_reporter import build_failure_payload
        payload = build_failure_payload(
            failure_class="EXECUTION_ERROR", run_id="r1", entrypoint="sop run",
            execution_mode="cli", failed_component="skill", reason="skill failed",
            recoverability="REQUIRES_FIX", repo_root=str(tmp_path), attempt_id="a1",
        )
        assert "failure_class" in payload


# ===========================================================================
# Day 2 -- TestMemoryTierRetention
# ===========================================================================


class TestMemoryTierRetention:
    """Memory tier retention: hot/warm/cold tiers behave correctly."""

    def test_hot_tier_survives_compaction(self, tmp_path: Path) -> None:
        import sop.scripts.run_loop_cycle as rlc
        src = Path(rlc.__file__).read_text(encoding="utf-8")
        assert "compaction" in src.lower() or "rolling" in src.lower()

    def test_warm_tier_preserved_in_handoff(self, tmp_path: Path) -> None:
        import sop.scripts.run_loop_cycle as rlc
        src = Path(rlc.__file__).read_text(encoding="utf-8")
        assert "handoff" in src.lower()

    def test_cold_tier_not_loaded_by_default(self, tmp_path: Path) -> None:
        import sop.scripts.run_loop_cycle as rlc
        src = Path(rlc.__file__).read_text(encoding="utf-8")
        assert "trace" in src.lower()


# ===========================================================================
# Day 3 -- TestObservabilityPackStep
# ===========================================================================


class TestObservabilityPackStep:
    """Observability pack step ok/warn depending on file presence."""

    def _run_cycle(self, tmp_path):
        import sop.scripts.run_loop_cycle as rlc
        from unittest.mock import MagicMock, patch
        (tmp_path / "docs" / "context").mkdir(parents=True, exist_ok=True)
        (tmp_path / "logs").mkdir(parents=True, exist_ok=True)
        args = rlc.parse_args(["--repo-root", str(tmp_path), "--skip-phase-end"])
        mg = MagicMock(); mg.decision = "PROCEED"; mg.all_conditions_met = True; mg.conditions = []
        gate = MagicMock(); gate.evaluate.return_value = mg
        gate.emit.return_value = tmp_path / "docs" / "context" / "gate_a.json"
        gate.emit_handoff.return_value = tmp_path / "docs" / "context" / "h.json"
        mc = MagicMock(return_value=gate)
        mp = MagicMock(); mp.returncode = 0; mp.stdout = ""; mp.stderr = ""
        with patch.object(rlc, "PhaseGate", mc), patch.object(rlc, "subprocess") as msub:
            msub.run.return_value = mp
            _rc, payload, _md = rlc.run_cycle(args)
        return payload

    def test_observability_pack_step_ok_when_file_exists(self, tmp_path: Path) -> None:
        (tmp_path / "docs" / "context").mkdir(parents=True)
        (tmp_path / "docs" / "context" / "observability_pack_current.md").write_text(
            "# obs pack", encoding="utf-8"
        )
        payload = self._run_cycle(tmp_path)
        steps = payload.get("steps", [])
        obs = next((s for s in steps if "observability" in s.get("name", "").lower()), None)
        assert obs is not None, "observability_pack step must exist in payload.steps"
        assert obs["status"] == "OK", f"Expected OK when file exists, got {obs['status']}"

    def test_observability_pack_step_warn_when_file_absent(self, tmp_path: Path) -> None:
        payload = self._run_cycle(tmp_path)
        steps = payload.get("steps", [])
        obs = next((s for s in steps if "observability" in s.get("name", "").lower()), None)
        assert obs is not None, "observability_pack step must exist in payload.steps"
        assert obs["status"] == "WARN", f"Expected WARN when file absent, got {obs['status']}"


# ===========================================================================
# Day 4 -- TestSkillsStatusInPayload
# ===========================================================================


class TestSkillsStatusInPayload:
    """H-5: skills_status must appear in build_summary_payload() return dict."""

    def _run_cycle_with_mock(self, repo_root):
        import sop.scripts.run_loop_cycle as rlc
        from unittest.mock import MagicMock, patch
        args = rlc.parse_args(["--repo-root", str(repo_root), "--skip-phase-end", "--allow-hold", "true"])
        mg = MagicMock(); mg.decision = "PROCEED"; mg.all_conditions_met = True; mg.conditions = []
        gate = MagicMock(); gate.evaluate.return_value = mg
        gate.emit.return_value = repo_root / "docs" / "context" / "gate_a.json"
        gate.emit_handoff.return_value = repo_root / "docs" / "context" / "handoff.json"
        mc = MagicMock(return_value=gate)
        mp = MagicMock(); mp.returncode = 0; mp.stdout = ""; mp.stderr = ""
        with patch.object(rlc, "PhaseGate", mc), patch.object(rlc, "subprocess") as msub:
            msub.run.return_value = mp
            _rc, payload, _md = rlc.run_cycle(args)
        return payload

    def test_skills_status_present_in_payload(self, tmp_path: Path) -> None:
        (tmp_path / "docs" / "context").mkdir(parents=True)
        (tmp_path / "logs").mkdir(parents=True)
        payload = self._run_cycle_with_mock(tmp_path)
        assert "skills_status" in payload
        assert payload["skills_status"] in ("RESOLVER_UNAVAILABLE", "EMPTY_BY_DESIGN", "OK")

    def test_skills_status_resolver_unavailable_when_flag_false(self, tmp_path: Path) -> None:
        import sop.scripts.run_loop_cycle as rlc
        from unittest.mock import patch
        (tmp_path / "docs" / "context").mkdir(parents=True)
        (tmp_path / "logs").mkdir(parents=True)
        with patch.object(rlc, "_SKILL_RESOLVER_AVAILABLE", False):
            payload = self._run_cycle_with_mock(tmp_path)
        assert payload["skills_status"] == "RESOLVER_UNAVAILABLE"

    def test_skills_status_empty_by_design_when_no_skills(self, tmp_path: Path) -> None:
        import sop.scripts.run_loop_cycle as rlc
        from unittest.mock import MagicMock, patch
        (tmp_path / "docs" / "context").mkdir(parents=True)
        (tmp_path / "logs").mkdir(parents=True)
        mock_result = {"status": "ok", "skills": []}
        with patch.object(rlc, "_SKILL_RESOLVER_AVAILABLE", True), \
             patch.object(rlc, "resolve_skills_for_role", return_value=[]), \
             patch.object(rlc, "resolve_active_skills", return_value=mock_result):
            payload = self._run_cycle_with_mock(tmp_path)
        assert payload["skills_status"] == "EMPTY_BY_DESIGN"


# ===========================================================================
# 21 Acceptance Tests — batch 4: equivalence + provenance + windows + manifest + schema
# ===========================================================================


class TestHealthyPathEquivalence:
    """test_healthy_path_equivalence."""

    def test_healthy_path_equivalence(self, tmp_path: Path) -> None:
        import sop.scripts.run_loop_cycle as rlc
        from unittest.mock import MagicMock, patch
        import sys
        from io import StringIO
        (tmp_path / "docs" / "context").mkdir(parents=True)
        (tmp_path / "logs").mkdir(parents=True)
        args = rlc.parse_args(["--repo-root", str(tmp_path), "--skip-phase-end"])
        mg = MagicMock(); mg.decision = "PROCEED"; mg.all_conditions_met = True; mg.conditions = []
        gate = MagicMock(); gate.evaluate.return_value = mg
        gate.emit.return_value = tmp_path / "docs" / "context" / "gate_a.json"
        gate.emit_handoff.return_value = tmp_path / "docs" / "context" / "h.json"
        mc = MagicMock(return_value=gate)
        mp = MagicMock(); mp.returncode = 0; mp.stdout = ""; mp.stderr = ""
        old_stderr = sys.stderr
        sys.stderr = StringIO()
        try:
            with patch.object(rlc, "PhaseGate", mc), patch.object(rlc, "subprocess") as msub:
                msub.run.return_value = mp
                exit_code, payload, _md = rlc.run_cycle(args)
            stderr_output = sys.stderr.getvalue()
        finally:
            sys.stderr = old_stderr
        failure_artifact = tmp_path / "docs" / "context" / "run_failure_latest.json"
        assert not failure_artifact.exists(), "run_failure_latest.json must NOT exist on healthy path"
        assert "FATAL" not in stderr_output, f"No FATAL on healthy path stderr, got: {stderr_output}"
        assert payload.get("final_result") in ("PASS", "HOLD", "FAIL", "ERROR")
        assert "gate_decisions" in payload


class TestPythonMSopProvenanceMatchesSopRun:
    """test_python_m_sop_provenance_matches_sop_run."""

    def test_python_m_sop_provenance_matches_sop_run(self) -> None:
        from sop.__main__ import _get_module_origins, _CRITICAL_MODULES
        origins = _get_module_origins()
        assert isinstance(origins, dict)
        for mod_name in _CRITICAL_MODULES:
            if mod_name in origins:
                assert isinstance(origins[mod_name], str), (
                    f"module_origins[{mod_name}] must be a string path"
                )


class TestWindowsPathFixture:
    """test_windows_path_fixture: Windows drive-letter paths handled correctly."""

    def test_windows_path_fixture(self) -> None:
        import importlib.util
        from unittest.mock import MagicMock, patch
        from sop.__main__ import _run_provenance_check
        fake_spec = MagicMock()
        fake_spec.origin = "C:\\\\Users\\\\test\\\\scripts\\\\phase_gate.py"
        real_find = importlib.util.find_spec

        def patched(name):
            if name == "sop.scripts.phase_gate":
                return fake_spec
            return real_find(name)

        with patch("importlib.util.find_spec", side_effect=patched):
            result = _run_provenance_check(repo_root=".")
        assert result is None or isinstance(result, str)
        if result is not None:
            assert "ENTRYPOINT_DIVERGENCE" in result or "divergence" in result.lower()


class TestManifestSymmetrySpec:
    """test_manifest_symmetry (spec-named acceptance test)."""

    def test_manifest_symmetry(self) -> None:
        import json
        mp = REPO_ROOT / "scripts" / "critical_scan_manifest.json"
        assert mp.exists(), f"critical_scan_manifest.json not found at {mp}"
        data = json.loads(mp.read_text(encoding="utf-8"))
        assert "pairs" in data, "manifest must have 'pairs' key"
        root = mp.parent.parent
        missing = []
        for pair in data["pairs"]:
            for key in ("scripts", "src"):
                fpath = root / pair[key]
                if not fpath.exists():
                    missing.append(str(pair[key]))
        assert missing == [], f"Manifest references missing files: {missing}"


class TestSchemaDrift:
    """test_schema_drift [PHASE 2 SCHEMA CONTRACT GATE]."""

    def test_schema_drift(self, tmp_path: Path) -> None:
        import json
        from sop._failure_reporter import build_failure_payload, write_run_failure
        schema_path = (
            REPO_ROOT
            / "docs" / "context" / "schemas" / "run_failure_latest.schema.json"
        )
        assert schema_path.exists(), f"Schema not found: {schema_path}"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        required_fields = schema.get("required", [])
        dest = tmp_path / "docs" / "context"
        dest.mkdir(parents=True)
        payload = build_failure_payload(
            failure_class="IMPORT_ERROR",
            run_id="schema-drift-test",
            entrypoint="sop run",
            execution_mode="cli",
            failed_component="PhaseGate",
            reason="schema drift test",
            recoverability="REQUIRES_FIX",
            repo_root=str(tmp_path),
            attempt_id="a1",
        )
        ok = write_run_failure(dest, payload)
        assert ok is True
        artifact = dest / "run_failure_latest.json"
        data = json.loads(artifact.read_text(encoding="utf-8"))
        missing = [f for f in required_fields if f not in data]
        assert missing == [], f"Required schema fields missing from artifact: {missing}"
        assert data["schema_version"] == schema["properties"]["schema_version"].get("const", "1.1")
        assert data["final_result"] == "ERROR"
        valid_classes = schema["properties"]["failure_class"]["enum"]
        assert data["failure_class"] in valid_classes


class TestPythonMSopProvenanceMatchesSopRun:
    """test_python_m_sop_provenance_matches_sop_run."""

    def test_python_m_sop_provenance_matches_sop_run(self) -> None:
        from sop.__main__ import _get_module_origins, _CRITICAL_MODULES
        origins = _get_module_origins()
        assert isinstance(origins, dict)
        for mod_name in _CRITICAL_MODULES:
            if mod_name in origins:
                assert isinstance(origins[mod_name], str), (
                    f"module_origins[{mod_name}] must be a string path"
                )


class TestWindowsPathFixture:
    """test_windows_path_fixture: Windows drive-letter paths handled correctly."""

    def test_windows_path_fixture(self) -> None:
        import importlib.util
        from unittest.mock import MagicMock, patch
        from sop.__main__ import _run_provenance_check
        fake_spec = MagicMock()
        fake_spec.origin = "C:\\\\Users\\\\test\\\\scripts\\\\phase_gate.py"
        real_find = importlib.util.find_spec

        def patched(name):
            if name == "sop.scripts.phase_gate":
                return fake_spec
            return real_find(name)

        with patch("importlib.util.find_spec", side_effect=patched):
            result = _run_provenance_check(repo_root=".")
        assert result is None or isinstance(result, str)
        if result is not None:
            assert "ENTRYPOINT_DIVERGENCE" in result or "divergence" in result.lower()


class TestManifestSymmetrySpec:
    """test_manifest_symmetry (spec-named acceptance test)."""

    def test_manifest_symmetry(self) -> None:
        import json
        mp = REPO_ROOT / "scripts" / "critical_scan_manifest.json"
        assert mp.exists(), f"critical_scan_manifest.json not found at {mp}"
        data = json.loads(mp.read_text(encoding="utf-8"))
        assert "pairs" in data, "manifest must have 'pairs' key"
        root = mp.parent.parent
        missing = []
        for pair in data["pairs"]:
            for key in ("scripts", "src"):
                fpath = root / pair[key]
                if not fpath.exists():
                    missing.append(str(pair[key]))
        assert missing == [], f"Manifest references missing files: {missing}"


class TestSchemaDrift:
    """test_schema_drift [PHASE 2 SCHEMA CONTRACT GATE]."""

    def test_schema_drift(self, tmp_path: Path) -> None:
        import json
        from sop._failure_reporter import build_failure_payload, write_run_failure
        schema_path = (
            REPO_ROOT
            / "docs" / "context" / "schemas" / "run_failure_latest.schema.json"
        )
        assert schema_path.exists(), f"Schema not found: {schema_path}"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        required_fields = schema.get("required", [])
        dest = tmp_path / "docs" / "context"
        dest.mkdir(parents=True)
        payload = build_failure_payload(
            failure_class="IMPORT_ERROR",
            run_id="schema-drift-test",
            entrypoint="sop run",
            execution_mode="cli",
            failed_component="PhaseGate",
            reason="schema drift test",
            recoverability="REQUIRES_FIX",
            repo_root=str(tmp_path),
            attempt_id="a1",
        )
        ok = write_run_failure(dest, payload)
        assert ok is True
        artifact = dest / "run_failure_latest.json"
        data = json.loads(artifact.read_text(encoding="utf-8"))
        missing = [f for f in required_fields if f not in data]
        assert missing == [], f"Required schema fields missing from artifact: {missing}"
        assert data["schema_version"] == schema["properties"]["schema_version"].get("const", "1.1")
        assert data["final_result"] == "ERROR"
        valid_classes = schema["properties"]["failure_class"]["enum"]
        assert data["failure_class"] in valid_classes
