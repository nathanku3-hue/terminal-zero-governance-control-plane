"""Phase 6 — Tutorials v1 acceptance tests.

Locked checks for operator onboarding tutorials.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

TUTORIAL_CONTAINER = REPO_ROOT / "docs" / "tutorials" / "quickstart-container.md"
TUTORIAL_HELM = REPO_ROOT / "docs" / "tutorials" / "quickstart-helm.md"
TUTORIAL_TROUBLESHOOTING = REPO_ROOT / "docs" / "tutorials" / "troubleshooting.md"
GETTING_STARTED = REPO_ROOT / "docs" / "getting-started.md"

REQUIRED_HEADERS_COMMON = [
    "## Context",
    "## Prerequisites",
    "## Commands",
    "## Output",
    "## Expected Decision",
]

REQUIRED_HEADERS_CONTAINER = REQUIRED_HEADERS_COMMON + ["## Next Steps"]
REQUIRED_HEADERS_HELM = REQUIRED_HEADERS_COMMON + ["## Rollback"]
REQUIRED_HEADERS_TROUBLESHOOTING = [
    "## Context",
    "## Failure Modes",
    "## Diagnostics",
    "## Remediation",
    "## Output",
    "## Escalation",
]

PUBLISHED_IMAGE_REFERENCE = "ghcr.io/<org>/terminal-zero-governance:latest"
HELM_LOCAL_CHART_SOURCE = "./charts/terminal-zero-governance"

RESULT_MARKERS = [
    "PASS",
    "HOLD",
    "FAIL",
    "BLOCK",
    "READY_TO_ESCALATE",
    "sop",
    "audit_log",
    "loop_cycle",
    "decision=",
    "status=",
]


def _read(path: Path) -> str:
    assert path.exists(), f"File not found: {path}"
    return path.read_text(encoding="utf-8")


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


def _is_likely_placeholder(line: str) -> bool:
    line = line.strip()
    if not line:
        return True
    if "<" in line and ">" in line:
        return True
    return False


def _is_yamlish_only(block: str) -> bool:
    lines = [line.strip() for line in block.splitlines() if line.strip()]
    if not lines:
        return True

    yaml_like = 0
    for line in lines:
        if line.startswith("#"):
            yaml_like += 1
        elif ":" in line and not any(token in line for token in ["$", "|", "PASS", "FAIL", "HOLD", "BLOCK"]):
            yaml_like += 1

    return yaml_like == len(lines)


def test_tutorials_docs_complete() -> None:
    files_and_headers = [
        (TUTORIAL_CONTAINER, REQUIRED_HEADERS_CONTAINER),
        (TUTORIAL_HELM, REQUIRED_HEADERS_HELM),
        (TUTORIAL_TROUBLESHOOTING, REQUIRED_HEADERS_TROUBLESHOOTING),
    ]

    for path, required_headers in files_and_headers:
        content = _read(path)
        for header in required_headers:
            assert header in content, f"{path} missing required header: {header}"


def test_tutorials_have_real_output_blocks() -> None:
    for path in [TUTORIAL_CONTAINER, TUTORIAL_HELM, TUTORIAL_TROUBLESHOOTING]:
        content = _read(path)
        output_body = _section_body(content, "## Output")
        output_blocks = _code_blocks(output_body)
        assert output_blocks, f"{path} must include at least one fenced output block under ## Output"

        has_qualifying_block = False
        for block in output_blocks:
            lines = [line.strip() for line in block.splitlines() if line.strip()]
            if not lines:
                continue
            if _is_yamlish_only(block):
                continue

            non_placeholder_lines = [line for line in lines if not _is_likely_placeholder(line)]
            if not non_placeholder_lines:
                continue

            if any(marker in line for line in non_placeholder_lines for marker in RESULT_MARKERS):
                has_qualifying_block = True
                break

        assert has_qualifying_block, (
            f"{path} ## Output must include at least one realistic output block with concrete ops result lines "
            "(config-only YAML does not qualify)"
        )


def test_getting_started_links_tutorials_section() -> None:
    content = _read(GETTING_STARTED)
    assert "## Tutorials" in content, "docs/getting-started.md must include exact header: ## Tutorials"
    assert "docs/tutorials/quickstart-container.md" in content, (
        "docs/getting-started.md must link to docs/tutorials/quickstart-container.md"
    )
    assert "docs/tutorials/quickstart-helm.md" in content, (
        "docs/getting-started.md must link to docs/tutorials/quickstart-helm.md"
    )


def test_troubleshooting_has_min_10_failure_modes() -> None:
    content = _read(TUTORIAL_TROUBLESHOOTING)
    failure_modes = _section_body(content, "## Failure Modes")

    pattern = re.compile(
        r"###\s+.+?\n"
        r"Symptom:\s+.+?\n"
        r"Likely cause:\s+.+?\n"
        r"Check:\s+.+?\n"
        r"Fix:\s+.+?(?=\n###\s+|\Z)",
        flags=re.DOTALL,
    )

    matches = pattern.findall(failure_modes)
    assert len(matches) >= 10, (
        "docs/tutorials/troubleshooting.md must contain at least 10 failure mode entries "
        "with exact per-item fields: Symptom, Likely cause, Check, Fix"
    )


def test_quickstart_helm_uses_local_chart_source() -> None:
    content = _read(TUTORIAL_HELM)
    assert HELM_LOCAL_CHART_SOURCE in content, (
        "docs/tutorials/quickstart-helm.md must use local chart source exactly: "
        "./charts/terminal-zero-governance"
    )


def test_quickstart_container_uses_published_image_convention() -> None:
    content = _read(TUTORIAL_CONTAINER)
    assert PUBLISHED_IMAGE_REFERENCE in content, (
        "docs/tutorials/quickstart-container.md must use published image reference exactly: "
        "ghcr.io/<org>/terminal-zero-governance:latest"
    )
