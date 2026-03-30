"""Phase 4 — Container artifact tests.

Acceptance gates:
  1. test_dockerfile_exists_and_has_non_root_user
  2. test_helm_chart_yaml_valid

Path convention: tests/ lives in quant_current_scope/tests/, so
  Path(__file__).parent.parent resolves to quant_current_scope/
which is where the Dockerfile and charts/ directory live.
"""
from __future__ import annotations

from pathlib import Path

# Repo package root: quant_current_scope/
_REPO_ROOT = Path(__file__).parent.parent


class TestDockerfileExistsAndHasNonRootUser:
    """GAP 6 acceptance: Dockerfile exists at the correct path and runs as non-root."""

    def test_dockerfile_exists_and_has_non_root_user(self) -> None:
        dockerfile = _REPO_ROOT / "Dockerfile"
        assert dockerfile.exists(), (
            f"Dockerfile not found at {dockerfile}. "
            "Phase 4 delivery requires quant_current_scope/Dockerfile."
        )

        content = dockerfile.read_text(encoding="utf-8")

        # Must use pinned python:3.12-slim base (not floating tag)
        assert "python:3.12-slim" in content, (
            "Dockerfile must pin python:3.12-slim in both stages "
            "(PYTHONPATH hardcodes python3.12 — floating tag breaks it)."
        )

        # Must create and switch to a non-root user
        assert "USER governance" in content, (
            "Dockerfile must switch to non-root 'governance' user "
            "before CMD/HEALTHCHECK."
        )

        # Must install the full package into /install (not deps-only)
        assert "pip install" in content and "/install" in content, (
            "Dockerfile builder stage must use "
            "'pip install --prefix=/install .' to install the full package."
        )

        # Must expose sop on PATH
        assert "PATH=/install/bin" in content, (
            "Dockerfile runtime stage must set PATH=/install/bin:$PATH "
            "so the sop entrypoint is reachable."
        )

        # Must have a HEALTHCHECK instruction (separate from CMD)
        assert "HEALTHCHECK" in content, (
            "Dockerfile must include a HEALTHCHECK instruction "
            "(not just CMD) for Docker daemon health monitoring."
        )


class TestHelmChartYamlValid:
    """GAP 4 acceptance: Helm chart files exist and contain required fields."""

    def test_helm_chart_yaml_valid(self) -> None:
        chart_dir = _REPO_ROOT / "charts" / "terminal-zero-governance"
        chart_yaml = chart_dir / "Chart.yaml"
        values_yaml = chart_dir / "values.yaml"
        job_template = chart_dir / "templates" / "job.yaml"
        helpers_tpl = chart_dir / "templates" / "_helpers.tpl"

        # All four files must exist
        for path in (chart_yaml, values_yaml, job_template, helpers_tpl):
            assert path.exists(), (
                f"Required Helm chart file not found: {path}. "
                "Phase 4 delivery requires a complete chart under "
                "quant_current_scope/charts/terminal-zero-governance/."
            )

        # Chart.yaml must declare apiVersion and name
        chart_content = chart_yaml.read_text(encoding="utf-8")
        assert "apiVersion:" in chart_content, "Chart.yaml must contain 'apiVersion:'"
        assert "name:" in chart_content, "Chart.yaml must contain 'name:'"
        assert "terminal-zero-governance" in chart_content, (
            "Chart.yaml 'name:' must be 'terminal-zero-governance'."
        )

        # job.yaml must include restartPolicy: Never
        # (kubectl will reject a Job manifest without it)
        job_content = job_template.read_text(encoding="utf-8")
        assert "restartPolicy: Never" in job_content, (
            "templates/job.yaml must contain 'restartPolicy: Never' "
            "on the Pod spec — kubectl apply rejects Job manifests without it."
        )

        # values.yaml must define image and workspace sections
        values_content = values_yaml.read_text(encoding="utf-8")
        assert "image:" in values_content, "values.yaml must define 'image:' section."
        assert "workspace:" in values_content, "values.yaml must define 'workspace:' section."
        assert "pvcName:" in values_content, "values.yaml must define 'workspace.pvcName'."
