from __future__ import annotations

from pathlib import Path

from sop._campaign_claims import validate_campaign_claims


_ALLOWED_CHANNELS = {
    "repo-docs-post",
    "technical-community-post",
    "meetup-abstract",
    "external-review-outreach",
}
_ALLOWED_ASSETS = {
    "roadmap-status-brief",
    "phase-closure-snapshot",
    "governance-method-summary",
    "feedback-invitation-note",
}


def _workspace_root() -> str:
    return str(Path(__file__).resolve().parents[1])


def test_campaign_claims_pass_with_traceable_and_bounded_input() -> None:
    claims = [
        {
            "text": "Phase F is closed and evidence is documented.",
            "channel": "repo-docs-post",
            "asset": "roadmap-status-brief",
            "evidence_paths": [
                "docs/context/closure_packet_phase_f_operational_rollout.md",
            ],
        }
    ]

    result = validate_campaign_claims(
        claims=claims,
        allowed_channels=_ALLOWED_CHANNELS,
        allowed_assets=_ALLOWED_ASSETS,
        workspace_root=_workspace_root(),
    )
    assert result.decision == "PASS"


def test_campaign_claims_block_when_evidence_path_missing() -> None:
    claims = [
        {
            "text": "Phase Z is fully complete.",
            "channel": "repo-docs-post",
            "asset": "roadmap-status-brief",
            "evidence_paths": ["docs/context/does_not_exist.md"],
        }
    ]

    result = validate_campaign_claims(
        claims=claims,
        allowed_channels=_ALLOWED_CHANNELS,
        allowed_assets=_ALLOWED_ASSETS,
        workspace_root=_workspace_root(),
    )
    assert result.decision == "BLOCK"
    assert "does not exist" in result.reason


def test_campaign_claims_block_for_unapproved_channel() -> None:
    claims = [
        {
            "text": "Phase E is closed.",
            "channel": "random-social-channel",
            "asset": "roadmap-status-brief",
            "evidence_paths": ["docs/context/closure_packet_phase_e_extensions.md"],
        }
    ]

    result = validate_campaign_claims(
        claims=claims,
        allowed_channels=_ALLOWED_CHANNELS,
        allowed_assets=_ALLOWED_ASSETS,
        workspace_root=_workspace_root(),
    )
    assert result.decision == "BLOCK"
    assert result.reason == "channel is not approved"


def test_campaign_claims_block_for_unapproved_asset() -> None:
    claims = [
        {
            "text": "Phase C is closed.",
            "channel": "repo-docs-post",
            "asset": "viral-ad-campaign",
            "evidence_paths": ["docs/context/closure_packet_phase_c_observability.md"],
        }
    ]

    result = validate_campaign_claims(
        claims=claims,
        allowed_channels=_ALLOWED_CHANNELS,
        allowed_assets=_ALLOWED_ASSETS,
        workspace_root=_workspace_root(),
    )
    assert result.decision == "BLOCK"
    assert result.reason == "asset is not approved"


def test_campaign_claims_block_on_forbidden_overclaim_language() -> None:
    claims = [
        {
            "text": "This is the best-in-class autonomous governance system.",
            "channel": "repo-docs-post",
            "asset": "governance-method-summary",
            "evidence_paths": ["docs/context/closure_packet_phase_f_operational_rollout.md"],
        }
    ]

    result = validate_campaign_claims(
        claims=claims,
        allowed_channels=_ALLOWED_CHANNELS,
        allowed_assets=_ALLOWED_ASSETS,
        workspace_root=_workspace_root(),
    )
    assert result.decision == "BLOCK"
    assert result.reason == "forbidden messaging pattern detected"


def test_campaign_claims_block_on_missing_traceability_array() -> None:
    claims = [
        {
            "text": "Phase D is closed.",
            "channel": "repo-docs-post",
            "asset": "phase-closure-snapshot",
            "evidence_paths": [],
        }
    ]

    result = validate_campaign_claims(
        claims=claims,
        allowed_channels=_ALLOWED_CHANNELS,
        allowed_assets=_ALLOWED_ASSETS,
        workspace_root=_workspace_root(),
    )
    assert result.decision == "BLOCK"
    assert result.reason == "claim evidence mapping missing"


def test_campaign_claims_validation_is_deterministic() -> None:
    claims = [
        {
            "text": "Phase G is in execution and not closed.",
            "channel": "technical-community-post",
            "asset": "phase-closure-snapshot",
            "evidence_paths": ["docs/context/closure_packet_phase_g_community_adoption_campaign.md"],
        }
    ]

    one = validate_campaign_claims(
        claims=claims,
        allowed_channels=_ALLOWED_CHANNELS,
        allowed_assets=_ALLOWED_ASSETS,
        workspace_root=_workspace_root(),
    )
    two = validate_campaign_claims(
        claims=claims,
        allowed_channels=_ALLOWED_CHANNELS,
        allowed_assets=_ALLOWED_ASSETS,
        workspace_root=_workspace_root(),
    )

    assert one == two
