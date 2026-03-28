"""Skill Resolver - Surface active skills in subagent packets.

Phase 5B.2: Thin Skill-Activation Bridge
Resolves active skills from project config against global allowlist.

P3 extensions (D-191):
- P3.1: Surface rollback_state from skill manifest (memory/rollback for skills)
- P3.2: Surface installs from skill manifest (manifest-driven selective install)
- P3.3: Surface targets from skill manifest (canonical-to-multi-target)

Phase 1.2 extension (additive):
- resolve_skills_for_role(): per-role WorkerSkill list; resolve_active_skills() unchanged.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# Add parent directory to path for imports when run as script
if __name__ == "__main__":
    _script_dir = Path(__file__).resolve().parent
    _project_root = _script_dir.parent.parent
    if str(_project_root) not in sys.path:
        sys.path.insert(0, str(_project_root))

try:
    from sop.scripts.utils.json_utils import safe_load_json_object  # noqa: F401
except ModuleNotFoundError:
    # Fallback for direct script execution (development mode)
    pass

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore


def _load_yaml_safe(path: Path) -> dict[str, Any] | None:
    """Load YAML file, return None if missing or invalid."""
    if yaml is None:
        return None
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data if isinstance(data, dict) else None
    except Exception:
        return None


def _load_manifest(repo_root: Path, manifest_path: str) -> dict[str, Any]:
    """Load a skill manifest YAML. Returns empty dict on missing/invalid."""
    p = repo_root / manifest_path
    result = _load_yaml_safe(p)
    return result if result is not None else {}


def resolve_active_skills(repo_root: Path, project_name: str) -> dict[str, Any]:
    """Resolve active skills from project config against global allowlist.

    Semantics match validate_extension_allowlist.py:235:
    - Read .sop_config.yaml -> active_skills list
    - For each skill:
      - Check in extension_allowlist.yaml
      - Verify status == "active"
      - Verify project_name in applicable_projects or "all" in applicable_projects
      - Get version from allowlist
      - Get metadata from skills/registry.yaml
      - Derive manifest_path: skills/{name.replace('-', '_')}/skill.yaml
      - Load manifest and surface P3 fields: rollback_state, installs, targets

    Fail-soft: Return status + warnings on errors.

    NOTE: assigned_roles is intentionally NOT surfaced in the returned skill
    dicts.  Per-role filtering is a Worker instantiation concern handled by
    resolve_skills_for_role().  This function and the emitted skill_activation
    artifact remain project-global.  build_exec_memory_packet.py:1891 and
    validate_skill_activation.py:117 call this function without modification.

    Args:
        repo_root: Repository root path
        project_name: Project name from config

    Returns:
        Dictionary with:
        - status: "ok" | "degraded" | "failed"
        - skills: List of resolved skill metadata
        - warnings: List of warning messages
        - errors: List of error messages
    """
    warnings: list[str] = []
    errors: list[str] = []
    skills: list[dict[str, Any]] = []

    # Load .sop_config.yaml
    sop_config_path = repo_root / ".sop_config.yaml"
    sop_config = _load_yaml_safe(sop_config_path)
    if sop_config is None:
        errors.append(f"Failed to load {sop_config_path}")
        return {
            "status": "failed",
            "skills": [],
            "warnings": warnings,
            "errors": errors,
        }

    active_skills = sop_config.get("active_skills", [])
    if not isinstance(active_skills, list):
        errors.append("active_skills must be a list")
        return {
            "status": "failed",
            "skills": [],
            "warnings": warnings,
            "errors": errors,
        }

    # Load extension_allowlist.yaml
    allowlist_path = repo_root / "extension_allowlist.yaml"
    allowlist = _load_yaml_safe(allowlist_path)
    if allowlist is None:
        errors.append(f"Failed to load {allowlist_path}")
        return {
            "status": "failed",
            "skills": [],
            "warnings": warnings,
            "errors": errors,
        }

    # Build allowlist lookup
    allowlist_skills: dict[str, dict[str, Any]] = {}
    for skill in allowlist.get("skills", []):
        skill_name = skill.get("skill_name")
        if skill_name:
            allowlist_skills[skill_name] = skill

    # Load skills/registry.yaml
    registry_path = repo_root / "skills" / "registry.yaml"
    registry = _load_yaml_safe(registry_path)
    if registry is None:
        warnings.append(f"Failed to load {registry_path}, metadata will be incomplete")
        registry = {}

    # Build registry lookup
    registry_skills: dict[str, dict[str, Any]] = {}
    for skill in registry.get("skills", []):
        skill_name = skill.get("name")
        if skill_name:
            registry_skills[skill_name] = skill

    # Resolve each active skill
    for skill_name in active_skills:
        if not isinstance(skill_name, str):
            warnings.append(f"Skipping non-string skill name: {skill_name}")
            continue

        # Check in allowlist
        if skill_name not in allowlist_skills:
            warnings.append(f"Skill '{skill_name}' not in global allowlist")
            continue

        allowlist_entry = allowlist_skills[skill_name]

        # Check status
        status = allowlist_entry.get("status")
        if status != "active":
            warnings.append(f"Skill '{skill_name}' has status '{status}' (must be 'active')")
            continue

        # Check applicable_projects
        applicable_projects = allowlist_entry.get("applicable_projects", [])
        if not isinstance(applicable_projects, list):
            warnings.append(f"Skill '{skill_name}' has invalid applicable_projects")
            continue

        if "all" not in applicable_projects and project_name not in applicable_projects:
            warnings.append(
                f"Skill '{skill_name}' not applicable to project '{project_name}'"
            )
            continue

        # Get version from allowlist
        version = allowlist_entry.get("version", "unknown")

        # Get metadata from registry
        registry_entry = registry_skills.get(skill_name, {})

        # Derive manifest_path
        manifest_name = skill_name.replace("-", "_")
        manifest_path = f"skills/{manifest_name}/skill.yaml"

        # P3.1 / P3.2 / P3.3: Load manifest and surface rollback_state, installs, targets
        manifest = _load_manifest(repo_root, manifest_path)
        rollback_state: dict[str, Any] | None = manifest.get("rollback") or None
        installs: list[str] = manifest.get("installs", [])
        if not isinstance(installs, list):
            installs = []
        targets: list[str] = manifest.get("targets", [])
        if not isinstance(targets, list):
            targets = []

        # Build skill metadata.
        # NOTE: assigned_roles is intentionally excluded from this dict.
        # It is an allowlist-internal field used only by resolve_skills_for_role().
        skill_metadata: dict[str, Any] = {
            "name": skill_name,
            "version": str(version),
            "status": status,
            "manifest_path": manifest_path,
            "category": registry_entry.get("category", "unknown"),
            "description": registry_entry.get("description", ""),
            "approval_decision_id": allowlist_entry.get("approval_decision_id", ""),
            "risk_level": allowlist_entry.get("risk_level", "UNKNOWN"),
            # P3.1: rollback state from manifest
            "rollback_state": rollback_state,
            # P3.2: manifest-declared install surfaces
            "installs": installs,
            # P3.3: canonical-to-multi-target output surfaces
            "targets": targets,
        }

        skills.append(skill_metadata)

    # Determine overall status
    if errors:
        status = "failed"
    elif warnings:
        status = "degraded"
    else:
        status = "ok"

    return {
        "status": status,
        "skills": skills,
        "warnings": warnings,
        "errors": errors,
    }


def resolve_skills_for_role(
    repo_root: Path, project: str, role: str
) -> list[Any]:
    """Return WorkerSkill list for a given role.

    Filters the global allowlist by the skill's optional ``assigned_roles``
    field.  Skills that do not have ``assigned_roles`` default to ``[worker]``.

    ``resolve_active_skills()`` signature is UNCHANGED — this is an additive
    function only.  Per-role injection is a Worker instantiation concern;
    the emitted ``skill_activation`` artifact is NOT role-filtered.

    NOTE: validate_skill_activation.py:117 logic is unchanged.
    NOTE: build_exec_memory_packet.py:1891 call is unchanged.
    NOTE: assigned_roles does NOT appear in the emitted skill_activation artifact.

    Args:
        repo_root: Repository root path.
        project: Project name (matches applicable_projects in allowlist).
        role: Role name to filter for ("worker", "auditor", "planner").

    Returns:
        List of ``WorkerSkill`` instances whose ``assigned_roles`` include
        ``role`` (or whose ``assigned_roles`` is absent, defaulting to worker).
    """
    # Import WorkerSkill here to avoid top-level circular import concerns.
    try:
        from sop.scripts.worker_base import WorkerSkill  # type: ignore[import]
    except ModuleNotFoundError:
        try:
            from scripts.worker_base import WorkerSkill  # type: ignore[import]
        except ModuleNotFoundError:
            from worker_base import WorkerSkill  # type: ignore[import]

    # Re-use the project-global resolver to get the full resolved set.
    result = resolve_active_skills(repo_root, project)
    if result["status"] == "failed":
        return []

    worker_skills: list[Any] = []

    # Load allowlist once to read assigned_roles (not surfaced in result["skills"]).
    allowlist_path = repo_root / "extension_allowlist.yaml"
    allowlist = _load_yaml_safe(allowlist_path) or {}
    allowlist_map: dict[str, dict[str, Any]] = {}
    for entry in allowlist.get("skills", []):
        name = entry.get("skill_name")
        if name:
            allowlist_map[name] = entry

    for skill_meta in result["skills"]:
        name = skill_meta["name"]
        entry = allowlist_map.get(name, {})
        # Default assigned_roles to ["worker"] if absent.
        assigned_roles: list[str] = entry.get("assigned_roles", ["worker"])
        if not isinstance(assigned_roles, list) or not assigned_roles:
            assigned_roles = ["worker"]
        if role not in assigned_roles:
            continue
        worker_skills.append(
            WorkerSkill(
                name=name,
                version=skill_meta["version"],
                risk_level=skill_meta["risk_level"],
                approval_decision_id=skill_meta["approval_decision_id"],
                applicable_projects=entry.get("applicable_projects", []),
            )
        )

    return worker_skills


if __name__ == "__main__":
    import json

    if len(sys.argv) < 3:
        print("Usage: skill_resolver.py <repo_root> <project_name>", file=sys.stderr)
        sys.exit(1)

    repo_root = Path(sys.argv[1]).resolve()
    project_name = sys.argv[2]

    result = resolve_active_skills(repo_root, project_name)
    print(json.dumps(result, indent=2))

    sys.exit(0 if result["status"] in {"ok", "degraded"} else 1)
