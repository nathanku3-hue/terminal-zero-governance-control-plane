"""sop init command - bootstrap a new governed repository."""

import shutil
import sys
from importlib import resources
from pathlib import Path
from typing import List


TEMPLATES = [
    "bridge_contract_template.md",
    "done_checklist_template.md",
    "multi_stream_contract_template.md",
    "post_phase_alignment_template.md",
    "planner_packet_template.md",
    "impact_packet_template.md",
    "planner_escalation_rules_template.md",
    "observability_pack_template.md",
    "artifact_pruning_rules_template.md",
    "planning_loop_integration_guide.md",
]


def _get_templates_dir() -> Path:
    """Get templates directory.

    Priority:
    1. Development: repo-root/docs/templates/
    2. Installed: package data sop/templates/
    """
    # Try development path first
    dev_templates = Path(__file__).parent.parent.parent / "docs" / "templates"
    if dev_templates.exists():
        return dev_templates

    # Fall back to package data
    try:
        return Path(str(resources.files("sop.templates")))
    except (TypeError, ModuleNotFoundError):
        pass

    # Last resort
    pkg_templates = Path(__file__).parent / "templates"
    if pkg_templates.exists():
        return pkg_templates

    raise FileNotFoundError(
        "Could not locate sop templates directory.\n"
        "  If installed: try reinstalling with 'pip install --force-reinstall terminal-zero-governance'\n"
        "  If in dev: ensure you're running from the repository root"
    )


def _copy_templates(target_templates_dir: Path) -> List[str]:
    """Copy templates from kernel to target directory."""
    source_dir = _get_templates_dir()
    copied = []

    if not source_dir.exists():
        print(f"Warning: Templates source not found: {source_dir}", file=sys.stderr)
        return copied

    target_templates_dir.mkdir(parents=True, exist_ok=True)

    for template_name in TEMPLATES:
        src = source_dir / template_name
        dst = target_templates_dir / template_name
        if src.exists():
            shutil.copy2(src, dst)
            copied.append(template_name)
        else:
            print(f"Warning: Template not found: {template_name}", file=sys.stderr)

    return copied



def _get_schemas_dir() -> Path:
    """Get schemas directory.

    Priority:
    1. Development: src/sop/schemas/ (adjacent to this file)
    2. Installed: package data sop/schemas/
    """
    dev_schemas = Path(__file__).parent / "schemas"
    if dev_schemas.exists():
        return dev_schemas

    try:
        return Path(str(resources.files("sop.schemas")))
    except (TypeError, ModuleNotFoundError):
        pass

    raise FileNotFoundError(
        "Could not locate sop schemas directory.\n"
        "  If installed: try reinstalling with 'pip install --force-reinstall terminal-zero-governance'\n"
        "  If in dev: ensure you're running from the repository root"
    )


def _copy_schemas(target_schemas_dir: Path) -> List[str]:
    """Copy JSON schemas from kernel to docs/context/schemas/ in the target directory."""
    try:
        source_dir = _get_schemas_dir()
    except FileNotFoundError as exc:
        print(f"Warning: {exc}", file=sys.stderr)
        return []

    if not source_dir.exists():
        print(f"Warning: Schemas source not found: {source_dir}", file=sys.stderr)
        return []

    target_schemas_dir.mkdir(parents=True, exist_ok=True)
    copied = []

    for schema_file in source_dir.glob("*.json"):
        dst = target_schemas_dir / schema_file.name
        shutil.copy2(schema_file, dst)
        copied.append(schema_file.name)

    return copied

def _create_config(target_config: Path) -> None:
    """Create minimal .sop/config.yaml."""
    target_config.parent.mkdir(parents=True, exist_ok=True)

    config_content = """# SOP Governance Configuration
# This file marks the repository as governed by Terminal Zero.

version: "1.0"

# Kernel activation matrix - which capabilities are active
# Uncomment as needed based on repo shape:
# capabilities:
#   bridge_contract: true
#   done_checklist: true
#   multi_stream: false
#   observability: true

# Context directory for generated artifacts
context_dir: docs/context
"""

    target_config.write_text(config_content, encoding="utf-8")


def _create_readme(target_readme: Path, project_name: str) -> None:
    """Create minimal README pointing to USER_GUIDE."""
    readme_content = f"""# {project_name}

This repository is governed by the [Terminal Zero](https://github.com/terminal-zero/sop) governance control plane.

## Quick Links

- [User Guide](https://github.com/terminal-zero/sop/blob/main/USER_GUIDE.md)
- [SOP Repository](https://github.com/terminal-zero/sop)

## Getting Started

```bash
# Install sop CLI
pip install terminal-zero-governance

# Initialize a round
sop startup --repo-root .

# Run the loop
sop run --repo-root . --skip-phase-end

# Validate readiness
sop validate --repo-root .
```

## Structure

```
docs/
  context/        # Generated artifacts (startup intake, loop summaries, etc.)
  templates/      # Kernel templates for truth surfaces
.sop/
  config.yaml     # Governance configuration
```
"""

    target_readme.write_text(readme_content, encoding="utf-8")


def _create_gitignore(target_gitignore: Path) -> None:
    """Create .gitignore for SOP artifacts."""
    gitignore_content = """# SOP generated artifacts (optional - uncomment if you don't want to track)
# docs/context/*.json
# docs/context/*.md

# Python
__pycache__/
*.py[cod]
.venv/
venv/

# IDE
.idea/
.vscode/
*.swp
"""

    target_gitignore.write_text(gitignore_content, encoding="utf-8")


def do_init(args) -> int:
    """Execute sop init command."""
    target_dir = Path(args.target_dir).resolve()
    minimal = getattr(args, "minimal", False)

    # Check if target exists
    if target_dir.exists():
        print(
            f"Error: Target directory already exists: {target_dir}\n"
            f"  Choose a different directory or remove the existing one first.",
            file=sys.stderr,
        )
        return 1

    print(f"Creating governed repository: {target_dir}")

    # Create directory structure
    dirs_to_create = [
        target_dir / "docs" / "context",
    ]

    if not minimal:
        dirs_to_create.append(target_dir / "docs" / "templates")

    for d in dirs_to_create:
        d.mkdir(parents=True, exist_ok=True)
        print(f"  Created: {d.relative_to(target_dir)}")

    # Copy templates
    if not minimal:
        templates_dir = target_dir / "docs" / "templates"
        copied = _copy_templates(templates_dir)
        if copied:
            print(f"  Copied {len(copied)} templates")
        else:
            print("  Warning: No templates copied")

    # Copy schemas into docs/context/schemas/
    schemas_dir = target_dir / "docs" / "context" / "schemas"
    schema_files = _copy_schemas(schemas_dir)
    if schema_files:
        print(f"  Copied {len(schema_files)} schemas to docs/context/schemas/")
    else:
        print("  Warning: No schemas copied to docs/context/schemas/")

    # Create config
    config_path = target_dir / ".sop" / "config.yaml"
    _create_config(config_path)
    print(f"  Created: {config_path.relative_to(target_dir)}")

    # Create README
    readme_path = target_dir / "README.md"
    project_name = target_dir.name
    _create_readme(readme_path, project_name)
    print(f"  Created: {readme_path.relative_to(target_dir)}")

    # Create .gitignore
    gitignore_path = target_dir / ".gitignore"
    _create_gitignore(gitignore_path)
    print(f"  Created: {gitignore_path.relative_to(target_dir)}")

    print()
    print("Repository initialized successfully.")
    print()
    print("Next steps:")
    print(f"  cd {target_dir}")
    print("  sop startup --repo-root .")
    print()

    return 0
