"""Phase 5 acceptance-gate tests — pure file existence and content checks.

Three tests, no subprocess, no imports outside stdlib.
"""
import pathlib

REPO_ROOT = pathlib.Path(__file__).parent.parent


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
