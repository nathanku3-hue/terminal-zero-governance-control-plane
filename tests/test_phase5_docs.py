"""Phase 5 acceptance-gate tests — pure file existence and content checks.

Three tests, no subprocess, no imports outside stdlib.
"""
import pathlib
import re

REPO_ROOT = pathlib.Path(__file__).parent.parent

REQUIRED_EXAMPLE_HEADERS = [
    "## Context",
    "## Inputs",
    "## Commands",
    "## Output",
    "## Expected Decision",
]

EXAMPLE_DOCS = [
    REPO_ROOT / "docs" / "examples" / "cicd-pipeline-governance.md",
    REPO_ROOT / "docs" / "examples" / "kubernetes-admission-governance.md",
    REPO_ROOT / "docs" / "examples" / "multi-service-rollout-governance.md",
]

REALISTIC_OUTPUT_MARKERS = [
    "PASS",
    "HOLD",
    "FAIL",
    "BLOCK",
    "READY_TO_ESCALATE",
    "artifacts",
    "status=",
    "decision=",
    "final_result",
]


def _section_body(content: str, header: str) -> str:
    start = content.find(header)
    assert start != -1, f"Missing header: {header}"

    section_start = start + len(header)
    next_header = content.find("\n## ", section_start)
    if next_header == -1:
        return content[section_start:]
    return content[section_start:next_header]


def _code_blocks(text: str) -> list[str]:
    return re.findall(r"```(?:[a-zA-Z0-9_-]+)?\n([\s\S]*?)```", text)


def test_getting_started_covers_key_steps():
    """docs/getting-started.md must contain all five key command tokens."""
    path = REPO_ROOT / "docs" / "getting-started.md"
    assert path.exists(), f"File not found: {path}"
    content = path.read_text(encoding="utf-8")
    required = [
        "pip install",
        "sop init",
        "sop run",
        "sop audit",
        "sop validate",
    ]
    missing = [token for token in required if token not in content]
    assert not missing, (
        f"docs/getting-started.md is missing required tokens: {missing}"
    )


def test_architecture_md_has_component_overview():
    """docs/architecture.md must contain an ASCII diagram and key component names."""
    path = REPO_ROOT / "docs" / "architecture.md"
    assert path.exists(), f"File not found: {path}"
    content = path.read_text(encoding="utf-8")

    # ASCII diagram marker — at least one line of dashes or box-drawing chars
    has_ascii = any(
        marker in content
        for marker in ["---", "+--", "+-+", "| ", "-->"]
    )
    assert has_ascii, (
        "docs/architecture.md must contain an ASCII diagram "
        "(expected dashes, box chars, or arrows)"
    )

    required_tokens = ["audit_log", "gate", "run_loop_cycle"]
    missing = [t for t in required_tokens if t not in content]
    assert not missing, (
        f"docs/architecture.md is missing required component names: {missing}"
    )


def test_context_readme_separates_generated_vs_canonical():
    """docs/context/README.md must contain both 'Generated' and 'Canonical' sections."""
    path = REPO_ROOT / "docs" / "context" / "README.md"
    assert path.exists(), f"File not found: {path}"
    content = path.read_text(encoding="utf-8")
    assert "Generated" in content, (
        "docs/context/README.md must contain a 'Generated' classification section"
    )
    assert "Canonical" in content, (
        "docs/context/README.md must contain a 'Canonical' classification section"
    )


def test_examples_docs_complete():
    """Examples docs must be complete and include required workflow/output structure."""
    for path in EXAMPLE_DOCS:
        assert path.exists(), f"Missing examples doc: {path}"
        content = path.read_text(encoding="utf-8")

        for header in REQUIRED_EXAMPLE_HEADERS:
            assert header in content, f"{path} missing required header: {header}"

        output_section = _section_body(content, "## Output")
        output_blocks = _code_blocks(output_section)
        assert output_blocks, f"{path} must include at least one fenced output block under ## Output"

        all_output_lines: list[str] = []
        for block in output_blocks:
            lines = [line.strip() for line in block.splitlines() if line.strip()]
            all_output_lines.extend(lines)

        assert all_output_lines, f"{path} output block cannot be placeholder-only or empty"
        assert any("<" not in line and ">" not in line for line in all_output_lines), (
            f"{path} output block must include concrete output lines"
        )
        assert any(
            marker in line for line in all_output_lines for marker in REALISTIC_OUTPUT_MARKERS
        ), f"{path} output block must include at least one realistic governance result marker"

    getting_started_path = REPO_ROOT / "docs" / "getting-started.md"
    assert getting_started_path.exists(), f"File not found: {getting_started_path}"
    getting_started = getting_started_path.read_text(encoding="utf-8")

    assert "## Examples" in getting_started, "docs/getting-started.md must include exact header: ## Examples"
    assert "external adoption patterns" in getting_started, (
        "docs/getting-started.md ## Examples must frame examples as external adoption patterns"
    )
    assert "docs/examples/cicd-pipeline-governance.md" in getting_started, (
        "docs/getting-started.md must link to docs/examples/cicd-pipeline-governance.md"
    )
    assert (
        "docs/examples/kubernetes-admission-governance.md" in getting_started
        or "docs/examples/multi-service-rollout-governance.md" in getting_started
    ), "docs/getting-started.md must link to at least one new Phase 4 example"

    cicd_path = REPO_ROOT / "docs" / "examples" / "cicd-pipeline-governance.md"
    cicd = cicd_path.read_text(encoding="utf-8")
    yaml_blocks = re.findall(r"```yaml\n([\s\S]*?)```", cicd)
    assert yaml_blocks, "CI/CD example must include at least one YAML workflow block"

    has_complete_workflow = False
    for block in yaml_blocks:
        if (
            "name:" in block
            and "on:" in block
            and "jobs:" in block
            and "runs-on:" in block
            and "terminal-zero-governance" in block
            and "sop run" in block
            and (
                "docs/context/" in block
                or "upload-artifact" in block
                or "archive" in block
                or "artifacts" in block
            )
        ):
            has_complete_workflow = True
            break

    assert has_complete_workflow, (
        "CI/CD example YAML block must include name/on/jobs/runs-on and steps for install, sop run, "
        "and artifact inspection or archive"
    )
