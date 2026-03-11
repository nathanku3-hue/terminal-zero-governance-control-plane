from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Literal, cast


StatusColor = Literal["green", "yellow", "red", "gray", "blue"]
ProgressState = Literal[
    "READY",
    "IN_PROGRESS",
    "BLOCKED",
    "NOT_STARTED",
    "ACTIVE",
    "COMPLETE",
    "ERROR",
]
OwnerRole = Literal["PM", "CEO", "Worker", "Auditor", "QA"]

_KNOWN_STATUS_COLORS = {"green", "yellow", "red", "gray", "blue"}
_KNOWN_PROGRESS_STATES = {
    "READY",
    "IN_PROGRESS",
    "BLOCKED",
    "NOT_STARTED",
    "ACTIVE",
    "COMPLETE",
    "ERROR",
}
_KNOWN_OWNER_ROLES = {"PM", "CEO", "Worker", "Auditor", "QA"}


@dataclass(slots=True)
class ArtifactInput:
    path: str
    updated_at_utc: str


@dataclass(slots=True)
class WorkflowNode:
    node_id: str
    title: str
    status_color: StatusColor
    progress_state: ProgressState
    owner_role: OwnerRole
    blockers: list[str] = field(default_factory=list)
    source_of_truth: str = ""
    updated_at_utc: str | None = None
    advisory_roles: list[str] = field(default_factory=list)
    complexity_band: str = ""
    rigor_mode: str = ""
    capability_band: str = ""
    supporting_artifacts: list[str] = field(default_factory=list)
    key_signals: list[str] = field(default_factory=list)
    next_action: str | None = None


@dataclass(slots=True)
class WorkflowOverlayMetadata:
    generator: str
    advisory_only: bool
    description: str | None = None


@dataclass(slots=True)
class WorkflowStatusOverlay:
    schema_version: str
    generated_at_utc: str
    repo_root: str
    source_of_truth_policy: str
    overall_status: StatusColor
    overall_summary: str
    artifact_inputs: list[ArtifactInput] = field(default_factory=list)
    nodes: list[WorkflowNode] = field(default_factory=list)
    role_views: dict[str, list[str]] = field(default_factory=dict)
    metadata: WorkflowOverlayMetadata | None = None


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return str(value)


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _status_color(value: Any) -> StatusColor:
    candidate = str(value or "gray")
    if candidate in _KNOWN_STATUS_COLORS:
        return cast(StatusColor, candidate)
    return cast(StatusColor, candidate)


def _progress_state(value: Any) -> ProgressState:
    candidate = str(value or "NOT_STARTED")
    if candidate in _KNOWN_PROGRESS_STATES:
        return cast(ProgressState, candidate)
    return cast(ProgressState, candidate)


def _owner_role(value: Any) -> OwnerRole:
    candidate = str(value or "Worker")
    if candidate in _KNOWN_OWNER_ROLES:
        return cast(OwnerRole, candidate)
    return cast(OwnerRole, candidate)


def artifact_input_from_mapping(payload: Mapping[str, Any]) -> ArtifactInput:
    return ArtifactInput(
        path=str(payload.get("path", "")),
        updated_at_utc=str(payload.get("updated_at_utc", "unknown")),
    )


def artifact_input_to_dict(artifact: ArtifactInput) -> dict[str, str]:
    return {
        "path": artifact.path,
        "updated_at_utc": artifact.updated_at_utc,
    }


def workflow_node_from_mapping(payload: Mapping[str, Any]) -> WorkflowNode:
    return WorkflowNode(
        node_id=str(payload.get("node_id", "unknown")),
        title=str(payload.get("title", payload.get("node_id", "Unknown"))),
        status_color=_status_color(payload.get("status_color")),
        progress_state=_progress_state(payload.get("progress_state")),
        owner_role=_owner_role(payload.get("owner_role")),
        blockers=_string_list(payload.get("blockers")),
        source_of_truth=str(payload.get("source_of_truth", "N/A")),
        updated_at_utc=_optional_str(payload.get("updated_at_utc")),
        advisory_roles=_string_list(payload.get("advisory_roles")),
        complexity_band=str(payload.get("complexity_band", "")),
        rigor_mode=str(payload.get("rigor_mode", "")),
        capability_band=str(payload.get("capability_band", "")),
        supporting_artifacts=_string_list(payload.get("supporting_artifacts")),
        key_signals=_string_list(payload.get("key_signals")),
        next_action=_optional_str(payload.get("next_action")),
    )


def workflow_node_to_dict(node: WorkflowNode) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "node_id": node.node_id,
        "title": node.title,
        "status_color": node.status_color,
        "progress_state": node.progress_state,
        "owner_role": node.owner_role,
        "blockers": list(node.blockers),
        "source_of_truth": node.source_of_truth,
        "updated_at_utc": node.updated_at_utc,
        "advisory_roles": list(node.advisory_roles),
        "complexity_band": node.complexity_band,
        "rigor_mode": node.rigor_mode,
        "capability_band": node.capability_band,
        "supporting_artifacts": list(node.supporting_artifacts),
        "key_signals": list(node.key_signals),
    }
    if node.next_action is not None:
        payload["next_action"] = node.next_action
    return payload


def workflow_overlay_metadata_from_mapping(payload: Mapping[str, Any]) -> WorkflowOverlayMetadata:
    return WorkflowOverlayMetadata(
        generator=str(payload.get("generator", "N/A")),
        advisory_only=bool(payload.get("advisory_only", True)),
        description=_optional_str(payload.get("description")),
    )


def workflow_overlay_metadata_to_dict(metadata: WorkflowOverlayMetadata | None) -> dict[str, Any]:
    if metadata is None:
        return {}
    payload: dict[str, Any] = {
        "generator": metadata.generator,
        "advisory_only": metadata.advisory_only,
    }
    if metadata.description is not None:
        payload["description"] = metadata.description
    return payload


def workflow_status_overlay_from_mapping(payload: Mapping[str, Any]) -> WorkflowStatusOverlay:
    raw_role_views = payload.get("role_views")
    role_views: dict[str, list[str]] = {}
    if isinstance(raw_role_views, Mapping):
        role_views = {
            str(role): _string_list(node_ids)
            for role, node_ids in raw_role_views.items()
        }

    raw_metadata = payload.get("metadata")
    metadata = None
    if isinstance(raw_metadata, Mapping):
        metadata = workflow_overlay_metadata_from_mapping(raw_metadata)

    raw_nodes = payload.get("nodes")
    nodes = []
    if isinstance(raw_nodes, list):
        nodes = [
            workflow_node_from_mapping(node)
            for node in raw_nodes
            if isinstance(node, Mapping)
        ]

    raw_artifact_inputs = payload.get("artifact_inputs")
    artifact_inputs = []
    if isinstance(raw_artifact_inputs, list):
        artifact_inputs = [
            artifact_input_from_mapping(artifact)
            for artifact in raw_artifact_inputs
            if isinstance(artifact, Mapping)
        ]

    return WorkflowStatusOverlay(
        schema_version=str(payload.get("schema_version", "1.0.0")),
        generated_at_utc=str(payload.get("generated_at_utc", "N/A")),
        repo_root=str(payload.get("repo_root", "")),
        source_of_truth_policy=str(payload.get("source_of_truth_policy", "N/A")),
        overall_status=_status_color(payload.get("overall_status")),
        overall_summary=str(payload.get("overall_summary", "")),
        artifact_inputs=artifact_inputs,
        nodes=nodes,
        role_views=role_views,
        metadata=metadata,
    )


def overlay_to_dict(overlay: WorkflowStatusOverlay) -> dict[str, Any]:
    return {
        "schema_version": overlay.schema_version,
        "generated_at_utc": overlay.generated_at_utc,
        "repo_root": overlay.repo_root,
        "source_of_truth_policy": overlay.source_of_truth_policy,
        "overall_status": overlay.overall_status,
        "overall_summary": overlay.overall_summary,
        "artifact_inputs": [
            artifact_input_to_dict(artifact)
            for artifact in overlay.artifact_inputs
        ],
        "nodes": [workflow_node_to_dict(node) for node in overlay.nodes],
        "role_views": {role: list(node_ids) for role, node_ids in overlay.role_views.items()},
        "metadata": workflow_overlay_metadata_to_dict(overlay.metadata),
    }


# Compatibility alias used by print_takeover_entrypoint workflow overlay adapters.
WorkflowStatusOverlayPayload = WorkflowStatusOverlay


def parse_workflow_overlay_payload(payload: Mapping[str, Any]) -> WorkflowStatusOverlayPayload:
    return workflow_status_overlay_from_mapping(payload)


def render_workflow_overlay_payload(payload: WorkflowStatusOverlayPayload) -> dict[str, Any]:
    return overlay_to_dict(payload)


def coerce_workflow_overlay_payload_dict(
    payload: Mapping[str, Any] | WorkflowStatusOverlayPayload,
) -> dict[str, Any]:
    if isinstance(payload, WorkflowStatusOverlay):
        return overlay_to_dict(payload)
    return overlay_to_dict(workflow_status_overlay_from_mapping(payload))
