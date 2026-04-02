from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CampaignCheck:
    name: str
    status: str
    detail: str


@dataclass(frozen=True)
class CampaignValidationResult:
    decision: str
    reason: str
    checks: list[CampaignCheck]


_FORBIDDEN_PATTERNS = (
    "best-in-class",
    "guaranteed",
    "fully autonomous",
    "industry-leading",
)


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_campaign_claims(
    *,
    claims: list[dict[str, Any]],
    allowed_channels: set[str],
    allowed_assets: set[str],
    workspace_root: str,
) -> CampaignValidationResult:
    checks: list[CampaignCheck] = []

    if not isinstance(claims, list):
        return CampaignValidationResult(
            decision="BLOCK",
            reason="claims payload must be a list",
            checks=[CampaignCheck(name="payload-shape", status="BLOCK", detail="claims is not a list")],
        )

    if not claims:
        return CampaignValidationResult(
            decision="BLOCK",
            reason="claims payload is empty",
            checks=[CampaignCheck(name="payload-empty", status="BLOCK", detail="at least one claim is required")],
        )

    root = Path(workspace_root)

    for idx, claim in enumerate(claims):
        if not isinstance(claim, dict):
            return CampaignValidationResult(
                decision="BLOCK",
                reason="claim entry must be an object",
                checks=[CampaignCheck(name="claim-shape", status="BLOCK", detail=f"claim[{idx}] is not an object")],
            )

        text = claim.get("text")
        evidence_paths = claim.get("evidence_paths")
        channel = claim.get("channel")
        asset = claim.get("asset")

        if not _is_non_empty_string(text):
            return CampaignValidationResult(
                decision="BLOCK",
                reason="claim text is missing",
                checks=[CampaignCheck(name="claim-text", status="BLOCK", detail=f"claim[{idx}] text missing")],
            )

        text_normalized = str(text).lower()
        for pattern in _FORBIDDEN_PATTERNS:
            if pattern in text_normalized:
                return CampaignValidationResult(
                    decision="BLOCK",
                    reason="forbidden messaging pattern detected",
                    checks=[
                        CampaignCheck(
                            name="messaging-boundary",
                            status="BLOCK",
                            detail=f"claim[{idx}] contains forbidden pattern: {pattern}",
                        )
                    ],
                )

        if not _is_non_empty_string(channel) or str(channel) not in allowed_channels:
            return CampaignValidationResult(
                decision="BLOCK",
                reason="channel is not approved",
                checks=[
                    CampaignCheck(
                        name="channel-allowlist",
                        status="BLOCK",
                        detail=f"claim[{idx}] channel={channel!r} is not in approved channels",
                    )
                ],
            )

        if not _is_non_empty_string(asset) or str(asset) not in allowed_assets:
            return CampaignValidationResult(
                decision="BLOCK",
                reason="asset is not approved",
                checks=[
                    CampaignCheck(
                        name="asset-allowlist",
                        status="BLOCK",
                        detail=f"claim[{idx}] asset={asset!r} is not in approved assets",
                    )
                ],
            )

        if not isinstance(evidence_paths, list) or not evidence_paths:
            return CampaignValidationResult(
                decision="BLOCK",
                reason="claim evidence mapping missing",
                checks=[
                    CampaignCheck(
                        name="traceability",
                        status="BLOCK",
                        detail=f"claim[{idx}] missing evidence_paths",
                    )
                ],
            )

        missing_paths: list[str] = []
        for rel in evidence_paths:
            if not _is_non_empty_string(rel):
                missing_paths.append(str(rel))
                continue
            p = root / str(rel)
            if not p.exists():
                missing_paths.append(str(rel))

        if missing_paths:
            return CampaignValidationResult(
                decision="BLOCK",
                reason="claim evidence path does not exist",
                checks=[
                    CampaignCheck(
                        name="traceability",
                        status="BLOCK",
                        detail=f"claim[{idx}] has missing evidence paths: {missing_paths}",
                    )
                ],
            )

        checks.append(
            CampaignCheck(
                name="claim-validated",
                status="PASS",
                detail=f"claim[{idx}] passed traceability, boundary, and allowlist checks",
            )
        )

    return CampaignValidationResult(
        decision="PASS",
        reason="all campaign claims conform to Phase G boundaries",
        checks=checks,
    )
