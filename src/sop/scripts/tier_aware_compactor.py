"""Phase 5.2 -- TierAwareCompactor: deterministic tier-aware compaction.

Applies retention rules to all artifacts in docs/context/ based on their
memory tier (hot/warm/cold) as defined in _MEMORY_TIER_FAMILIES.

Rules:
  hot   -- never compacted; always skipped.
  warm  -- no-op in Phase 5 (in-place overwrite; no accumulation).
  cold NDJSON -- rolling window (keep last N records).
  cold non-NDJSON -- retained until explicit archive trigger (see 5.3).

D-183: scripts/tier_aware_compactor.py must be byte-identical to this file.
"""
from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from sop.scripts.utils.memory_tiers import _MEMORY_TIER_FAMILIES
except ModuleNotFoundError:
    try:
        from scripts.utils.memory_tiers import _MEMORY_TIER_FAMILIES  # type: ignore[no-redef]
    except ModuleNotFoundError:
        from utils.memory_tiers import _MEMORY_TIER_FAMILIES  # type: ignore[no-redef]


COMPACTION_REPORT_SCHEMA_VERSION = "1.0"

# Default rolling window sizes for cold NDJSON families.
_COLD_NDJSON_MAX_RECORDS: dict[str, int] = {
    "run_regression_baseline": 100,
    "loop_run_steps": 500,
}
_COLD_NDJSON_DEFAULT_MAX_RECORDS = 200


@dataclass
class CompactionPolicy:
    """Retention policy for a single artifact."""
    artifact_path: str
    tier: str
    max_records: int | None
    superseded_by: str | None


@dataclass
class CompactionReport:
    """Result of TierAwareCompactor.run()."""
    schema_version: str = COMPACTION_REPORT_SCHEMA_VERSION
    generated_at_utc: str = ""
    blocked: bool = False
    compacted: list[str] = field(default_factory=list)
    retained: list[str] = field(default_factory=list)
    skipped_hot: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at_utc": self.generated_at_utc,
            "blocked": self.blocked,
            "compacted": list(self.compacted),
            "retained": list(self.retained),
            "skipped_hot": list(self.skipped_hot),
            "errors": list(self.errors),
        }


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _compact_ndjson_rolling_local(path: Path, max_records: int) -> bool:
    """Prune path to the last max_records non-empty lines (atomic). Returns True if pruned."""
    if not path.exists():
        return False
    try:
        lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    except OSError:
        return False
    if len(lines) <= max_records:
        return False
    kept = lines[-max_records:]
    try:
        fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tmp_compact_", suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(kept) + "\n")
        os.replace(tmp, path)
        return True
    except OSError:
        try:
            Path(tmp).unlink(missing_ok=True)  # type: ignore[possibly-undefined]
        except Exception:
            pass
        return False


def _build_policies() -> list[CompactionPolicy]:
    """Build CompactionPolicy list from _MEMORY_TIER_FAMILIES."""
    policies: list[CompactionPolicy] = []
    for family_key, family in _MEMORY_TIER_FAMILIES.items():
        tier = family["tier"]
        for artifact_path in family["artifact_paths"]:
            # Determine max_records for cold NDJSON
            max_records: int | None = None
            if tier == "cold" and artifact_path.endswith(".ndjson"):
                max_records = _COLD_NDJSON_MAX_RECORDS.get(
                    family_key, _COLD_NDJSON_DEFAULT_MAX_RECORDS
                )
            policies.append(
                CompactionPolicy(
                    artifact_path=artifact_path,
                    tier=tier,
                    max_records=max_records,
                    superseded_by=None,
                )
            )
    return policies


class TierAwareCompactor:
    """Apply tier-aware retention rules to artifacts in context_dir.

    Usage::

        report = TierAwareCompactor(
            context_dir=ctx.context_dir,
            tier_contract=_MEMORY_TIER_FAMILIES,
            blocked=(exit_code == 1),
        ).run()

    The compactor:
    - Skips all hot artifacts (never compacted).
    - Skips all warm artifacts (no-op; in-place overwrite model).
    - Applies rolling-window compaction to cold NDJSON artifacts.
    - Retains cold non-NDJSON artifacts without modification.
    - Does nothing when blocked=True (HOLD run without --force).
    """

    def __init__(
        self,
        context_dir: Path,
        tier_contract: dict,
        blocked: bool = False,
    ) -> None:
        self.context_dir = context_dir
        self.tier_contract = tier_contract
        self.blocked = blocked

    def run(self) -> CompactionReport:
        """Apply retention rules; return CompactionReport."""
        report = CompactionReport(
            generated_at_utc=_utc_now_iso(),
            blocked=self.blocked,
        )

        if self.blocked:
            # Compaction skipped for HOLD runs
            return report

        policies = _build_policies()

        for policy in policies:
            # Strip leading docs/context/ prefix to get filename relative to context_dir
            artifact_name = Path(policy.artifact_path).name
            artifact_abs = self.context_dir / artifact_name

            if policy.tier == "hot":
                # Never compact hot artifacts
                if artifact_abs.exists():
                    report.skipped_hot.append(policy.artifact_path)
                continue

            if policy.tier == "warm":
                # No-op: warm artifacts are in-place overwritten each run
                continue

            # cold tier
            if not artifact_abs.exists():
                continue

            if policy.max_records is not None:
                # Cold NDJSON: apply rolling window
                try:
                    pruned = _compact_ndjson_rolling_local(artifact_abs, policy.max_records)
                    if pruned:
                        report.compacted.append(policy.artifact_path)
                    else:
                        report.retained.append(policy.artifact_path)
                except Exception as exc:
                    report.errors.append(
                        f"{policy.artifact_path}: compaction error: {exc}"
                    )
            else:
                # Cold non-NDJSON: retain (archive handled by ArtifactLifecycleManager)
                report.retained.append(policy.artifact_path)

        return report
