from __future__ import annotations

import ast
import json
import re
from pathlib import Path

import pytest

TOP_ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = TOP_ROOT / "MULTISTREAM_EXECUTION_PLAN.md"
MATRIX_PATH = TOP_ROOT / "docs" / "context" / "phase_status_matrix_latest.json"
RUNBOOK_PATH = TOP_ROOT / "docs" / "runbooks" / "program-closeout.md"

_REQUIRED_ARTIFACTS = [PLAN_PATH, MATRIX_PATH, RUNBOOK_PATH]
if not all(path.exists() for path in _REQUIRED_ARTIFACTS):
    pytestmark = pytest.mark.skip(
        reason="Phase 10 governance artifacts are not present in this checkout."
    )

VALID_PHASE_IDS = {f"phase{i}" for i in range(1, 11)}
VALID_STATUS = {"not_started", "in_progress", "blocked", "complete"}


def _read_text(path: Path) -> str:
    assert path.exists(), f"File not found: {path}"
    return path.read_text(encoding="utf-8")


def _phase_sections(plan_text: str) -> list[tuple[str, str]]:
    matches = re.findall(r"^## Phase (\d+) \((phase\d+)\)$", plan_text, flags=re.MULTILINE)
    return [(n, phase_id) for n, phase_id in matches]


def _parse_plan_phase_data(plan_text: str) -> dict[str, dict[str, list[str]]]:
    pattern = re.compile(
        r"^## Phase (\d+) \((phase\d+)\)$([\s\S]*?)(?=^## Phase \d+ \(phase\d+\)$|\Z)",
        flags=re.MULTILINE,
    )
    parsed: dict[str, dict[str, list[str]]] = {}

    for _, phase_id, block in pattern.findall(plan_text):
        data: dict[str, list[str]] = {
            "hard_dependencies": [],
            "soft_dependencies": [],
            "parallel_safe_with": [],
            "owns_artifacts": [],
            "consumes_artifacts": [],
        }

        for key in data:
            line_match = re.search(rf"- {key}:\s*(\[[^\n]*\])", block)
            if line_match:
                data[key] = list(ast.literal_eval(line_match.group(1)))

        parsed[phase_id] = data

    return parsed


def _has_hard_dependency_cycle(graph: dict[str, list[str]]) -> bool:
    visiting: set[str] = set()
    visited: set[str] = set()

    def dfs(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False

        visiting.add(node)
        for neighbor in graph.get(node, []):
            if dfs(neighbor):
                return True
        visiting.remove(node)
        visited.add(node)
        return False

    return any(dfs(node) for node in graph)


def test_phase_status_matrix_schema_valid() -> None:
    payload = json.loads(_read_text(MATRIX_PATH))

    assert payload.get("schema_version") == "phase-status-matrix/v1"
    assert payload.get("generated_at_utc")

    phases = payload.get("phases")
    assert isinstance(phases, dict), "phases must be an object keyed by phase id"

    for phase_id, entry in phases.items():
        assert phase_id in VALID_PHASE_IDS, f"Invalid phase id in matrix: {phase_id}"
        assert isinstance(entry, dict), f"Phase entry for {phase_id} must be an object"
        status = entry.get("status")
        assert status in VALID_STATUS, f"Invalid status for {phase_id}: {status}"


def test_phase_status_matrix_complete_for_all_phases() -> None:
    payload = json.loads(_read_text(MATRIX_PATH))
    phases = payload["phases"]

    assert set(phases.keys()) == VALID_PHASE_IDS


def test_multistream_plan_has_canonical_phase_sections() -> None:
    plan_text = _read_text(PLAN_PATH)
    sections = _phase_sections(plan_text)

    expected = [(str(i), f"phase{i}") for i in range(1, 11)]
    assert sections == expected


def test_artifact_paths_have_single_canonical_owner() -> None:
    plan_text = _read_text(PLAN_PATH)
    phase_data = _parse_plan_phase_data(plan_text)

    owner_for_artifact: dict[str, str] = {}
    for phase_id, data in phase_data.items():
        for artifact in data["owns_artifacts"]:
            assert artifact not in owner_for_artifact, (
                f"Artifact {artifact} is owned by both {owner_for_artifact[artifact]} and {phase_id}"
            )
            owner_for_artifact[artifact] = phase_id

    for phase_id, data in phase_data.items():
        for artifact in data["consumes_artifacts"]:
            assert artifact in owner_for_artifact, (
                f"Consumed artifact {artifact} has no canonical owner"
            )
            assert owner_for_artifact[artifact] != phase_id, (
                f"Phase {phase_id} consumes artifact {artifact} that it already owns"
            )


def test_phase_dependencies_are_consistent() -> None:
    plan_text = _read_text(PLAN_PATH)
    phase_data = _parse_plan_phase_data(plan_text)

    hard_graph: dict[str, list[str]] = {}

    for phase_id, data in phase_data.items():
        hard = data["hard_dependencies"]
        soft = data["soft_dependencies"]
        parallel = data["parallel_safe_with"]

        for bucket_name, bucket in (
            ("hard_dependencies", hard),
            ("soft_dependencies", soft),
            ("parallel_safe_with", parallel),
        ):
            for ref in bucket:
                assert ref in VALID_PHASE_IDS, f"{phase_id}.{bucket_name} has invalid reference: {ref}"
                assert ref != phase_id, f"{phase_id}.{bucket_name} contains self-reference"

        hard_graph[phase_id] = list(hard)

    assert not _has_hard_dependency_cycle(hard_graph), "Hard dependency cycle detected"


def test_program_closeout_runbook_has_required_sections() -> None:
    text = _read_text(RUNBOOK_PATH)

    required_headers = [
        "## Purpose",
        "## Preconditions",
        "## Execution Steps",
        "## Validation Checklist",
        "## Escalation and Ownership Conflict Resolution",
        "## Sign-off",
    ]

    for header in required_headers:
        assert header in text, f"Missing required runbook section: {header}"
