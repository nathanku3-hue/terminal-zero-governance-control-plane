"""tests/test_smoke_e.py — Stream E: Golden Path Proof"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest import mock

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def _run_sop(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    cmd = [sys.executable, "-m", "sop"] + list(args)
    return subprocess.run(cmd, capture_output=True, text=True, check=False,
                          cwd=str(cwd or REPO_ROOT))


# ---------------------------------------------------------------------------
# E.1 -- CLI reachable without ImportError
# ---------------------------------------------------------------------------

class TestCLIReachable:
    def test_sop_run_help_exits_zero(self):
        result = _run_sop("run", "--help")
        assert result.returncode == 0, (
            f"sop run --help exited {result.returncode} stderr: {result.stderr}"
        )

    def test_sop_help_no_import_error(self):
        result = _run_sop("--help")
        assert "ImportError" not in result.stderr
        assert "Traceback" not in result.stderr

    def test_sop_version_exits_zero(self):
        result = _run_sop("version")
        assert result.returncode == 0
        assert "sop" in result.stdout


# ---------------------------------------------------------------------------
# E.2 -- Preflight spec check on clean install
# ---------------------------------------------------------------------------

class TestPreflightSpecCheck:
    def test_returns_none_on_clean_install(self):
        from sop.__main__ import _run_preflight_spec_check
        assert _run_preflight_spec_check(repo_root=".") is None

    def test_returns_error_when_module_missing(self):
        from sop.__main__ import _run_preflight_spec_check
        with mock.patch("importlib.util.find_spec", return_value=None):
            result = _run_preflight_spec_check(repo_root=".")
        assert result is not None and len(result) > 0


# ---------------------------------------------------------------------------
# E.3 -- Provenance check on clean install
# ---------------------------------------------------------------------------

class TestProvenanceCheck:
    def test_returns_none_on_clean_install(self):
        from sop.__main__ import _run_provenance_check
        assert _run_provenance_check(repo_root=".") is None

    def test_all_critical_modules_under_pkg_root(self):
        sop_spec = importlib.util.find_spec("sop")
        assert sop_spec is not None
        assert sop_spec.submodule_search_locations is not None
        pkg_root = Path(list(sop_spec.submodule_search_locations)[0])
        from sop.__main__ import _CRITICAL_MODULES
        for mod_name in _CRITICAL_MODULES:
            spec = importlib.util.find_spec(mod_name)
            assert spec is not None, f"Not findable: {mod_name}"
            assert spec.origin is not None, f"No origin: {mod_name}"
            try:
                Path(spec.origin).relative_to(pkg_root)
            except ValueError:
                raise AssertionError(
                    f"{mod_name} at {spec.origin} not under {pkg_root}"
                )


# ---------------------------------------------------------------------------
# E.4 -- Healthy-path fixture
# ---------------------------------------------------------------------------

class TestHealthyPathFixture:
    def test_healthy_path_no_failure_artifact(self, tmp_path):
        """sop run on clean fixture: no FATAL ImportError envelope on stderr.

        An empty repo legitimately exits non-zero (HOLD / missing artifacts).
        What we verify is that the failure is NOT a package import failure:
        - No FATAL envelope with failure_class=IMPORT_ERROR or INSTALL_ERROR
        - No unhandled Traceback from the sop package itself
        If run_failure_latest.json is written, it must not be an IMPORT_ERROR.
        """
        (tmp_path / "docs" / "context").mkdir(parents=True)
        result = _run_sop(
            "run", "--repo-root", str(tmp_path),
            "--skip-phase-end", "--allow-hold", "true",
            cwd=tmp_path,
        )
        # No unhandled traceback from the package
        assert "Traceback (most recent call last)" not in result.stderr
        # If a failure artifact was written, it must not be an import/install error
        artifact = tmp_path / "docs" / "context" / "run_failure_latest.json"
        if artifact.exists():
            data = json.loads(artifact.read_text(encoding="utf-8"))
            assert data.get("failure_class") not in ("IMPORT_ERROR", "INSTALL_ERROR"), (
                f"Package import failure on clean run: {data.get('failure_class')} "
                f"reason: {data.get('reason')}"
            )

    def test_healthy_path_no_fatal_on_stderr(self, tmp_path):
        (tmp_path / "docs" / "context").mkdir(parents=True)
        result = _run_sop(
            "run", "--repo-root", str(tmp_path),
            "--skip-phase-end", "--allow-hold", "true",
            cwd=tmp_path,
        )
        fatal_lines = [l for l in result.stderr.splitlines() if l.startswith("FATAL")]
        assert fatal_lines == [], f"FATAL lines on healthy path: {fatal_lines}"


# ---------------------------------------------------------------------------
# E.5 -- Shadowed-module fixture
# ---------------------------------------------------------------------------

class TestShadowedModuleFixture:
    def test_provenance_check_detects_fake_module(self):
        from sop.__main__ import _run_provenance_check
        with tempfile.TemporaryDirectory() as fake_dir:
            fake_spec = mock.MagicMock()
            fake_spec.origin = str(Path(fake_dir) / "phase_gate.py")
            original = importlib.util.find_spec

            def patched(name, *a, **kw):
                if name == "sop.scripts.phase_gate":
                    return fake_spec
                return original(name, *a, **kw)

            with mock.patch("importlib.util.find_spec", side_effect=patched):
                result = _run_provenance_check(repo_root=".")

        assert result is not None
        assert "ENTRYPOINT_DIVERGENCE" in result or "divergence" in result.lower()

    def test_preflight_failure_writes_artifact(self, tmp_path):
        from sop.__main__ import _write_preflight_failure
        context_dir = tmp_path / "docs" / "context"
        context_dir.mkdir(parents=True)
        _write_preflight_failure(
            failure_class="ENTRYPOINT_DIVERGENCE",
            failed_component="provenance_check",
            reason="compatibility-path divergence: use sop run instead",
            recoverability="REQUIRES_FIX",
            repo_root=str(tmp_path),
        )
        artifact = context_dir / "run_failure_latest.json"
        assert artifact.exists()
        data = json.loads(artifact.read_text(encoding="utf-8"))
        assert data["failure_class"] == "ENTRYPOINT_DIVERGENCE"
        assert data["recoverability"] == "REQUIRES_FIX"
        assert data["schema_version"] in ("1.0", "1.1")
        assert data["final_result"] == "ERROR"

    def test_preflight_failure_emits_fatal_envelope(self, tmp_path, capsys):
        from sop.__main__ import _write_preflight_failure
        (tmp_path / "docs" / "context").mkdir(parents=True)
        _write_preflight_failure(
            failure_class="ENTRYPOINT_DIVERGENCE",
            failed_component="provenance_check",
            reason="compatibility-path divergence",
            recoverability="REQUIRES_FIX",
            repo_root=str(tmp_path),
        )
        captured = capsys.readouterr()
        assert "FATAL" in captured.err
        assert "ENTRYPOINT_DIVERGENCE" in captured.err
        assert "REQUIRES_FIX" in captured.err


# ---------------------------------------------------------------------------
# E.6 -- Windows path fixture
# ---------------------------------------------------------------------------

class TestWindowsPathFixture:
    def test_windows_path_triggers_divergence(self):
        from sop.__main__ import _run_provenance_check
        fake_spec = mock.MagicMock()
        fake_spec.origin = r"C:\Users\Lenovo\scripts\phase_gate.py"
        original = importlib.util.find_spec

        def patched(name, *a, **kw):
            if name == "sop.scripts.phase_gate":
                return fake_spec
            return original(name, *a, **kw)

        with mock.patch("importlib.util.find_spec", side_effect=patched):
            result = _run_provenance_check(repo_root=".")

        assert result is not None, "Divergence not detected for Windows path"
        assert "phase_gate" in result.lower() or "scripts" in result.lower()


# ---------------------------------------------------------------------------
# E.7 -- Package path takes priority over scripts/ (H-NEW-4)
# ---------------------------------------------------------------------------

class TestPackagePathPriority:
    def test_critical_modules_resolve_from_package_not_scripts(self):
        sop_spec = importlib.util.find_spec("sop")
        assert sop_spec is not None
        assert sop_spec.submodule_search_locations is not None
        pkg_root = Path(list(sop_spec.submodule_search_locations)[0])
        from sop.__main__ import _CRITICAL_MODULES
        for mod_name in _CRITICAL_MODULES:
            spec = importlib.util.find_spec(mod_name)
            assert spec is not None, f"Not findable: {mod_name}"
            assert spec.origin is not None
            try:
                Path(spec.origin).relative_to(pkg_root)
            except ValueError:
                raise AssertionError(
                    f"{mod_name} at {spec.origin} NOT under {pkg_root}. "
                    "scripts/ path may be taking priority."
                )

    def test_preflight_fails_if_package_not_findable(self):
        from sop.__main__ import _run_preflight_spec_check
        with mock.patch("importlib.util.find_spec", return_value=None):
            result = _run_preflight_spec_check(repo_root=".")
        assert result is not None, "Expected failure when package not findable"


# ---------------------------------------------------------------------------
# E.8 -- module_origins stable; failure artifact schema complete
# ---------------------------------------------------------------------------

class TestEntrypointConsistency:
    def test_module_origins_stable_across_calls(self):
        from sop.__main__ import _get_module_origins
        o1 = _get_module_origins()
        o2 = _get_module_origins()
        assert o1 == o2
        for mod_name, origin in o1.items():
            assert isinstance(origin, str) and len(origin) > 0

    def test_failure_artifact_schema_complete(self, tmp_path):
        from sop.__main__ import _write_preflight_failure
        (tmp_path / "docs" / "context").mkdir(parents=True)
        _write_preflight_failure(
            failure_class="INSTALL_ERROR",
            failed_component="test",
            reason="test reason",
            recoverability="REQUIRES_FIX",
            repo_root=str(tmp_path),
        )
        artifact = tmp_path / "docs" / "context" / "run_failure_latest.json"
        assert artifact.exists()
        data = json.loads(artifact.read_text(encoding="utf-8"))
        for field in ("schema_version", "failure_class", "module_origins",
                      "final_result", "recoverability", "failed_component"):
            assert field in data, f"Missing field: {field}"
        assert data["final_result"] == "ERROR"
