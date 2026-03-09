from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "validate_domain_falsification_pack.py"
)


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _run(repo_root: Path, round_contract_path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--repo-root",
            str(repo_root),
            "--round-contract-md",
            str(round_contract_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def test_domain_falsification_pack_passes_when_required_and_complete(tmp_path: Path) -> None:
    round_contract = tmp_path / "docs/context/round_contract_latest.md"
    artifact = tmp_path / "docs/context/domain_falsification_pack_latest.json"
    _write_json(
        artifact,
        {
            "hypothesis": "Macro regime assumptions are stable.",
            "falsification_checks": ["rate-shock counterexample", "liquidity stress probe"],
            "status": "COMPLETED",
        },
    )
    _write_text(
        round_contract,
        "\n".join(
            [
                "# Round Contract",
                "- DOMAIN_FALSIFICATION_REQUIRED: YES",
                "- DOMAIN_FALSIFICATION_ARTIFACT: docs/context/domain_falsification_pack_latest.json",
                "- SEMANTIC_RISK_REASON: Macro interpretation risk in final recommendation.",
                "- SEMANTIC_EXPERT_DOMAIN: macro_econ",
                "- UNKNOWN_EXPERT_DOMAIN_POLICY: ESCALATE_TO_BOARD",
                "- BOARD_REENTRY_REQUIRED: NO",
                "- BOARD_REENTRY_REASON: N/A",
                "",
            ]
        ),
    )

    result = _run(tmp_path, round_contract)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "validation passed" in (result.stdout + result.stderr).lower()


def test_domain_falsification_pack_fails_when_required_but_artifact_missing(tmp_path: Path) -> None:
    round_contract = tmp_path / "docs/context/round_contract_latest.md"
    _write_text(
        round_contract,
        "\n".join(
            [
                "# Round Contract",
                "- DOMAIN_FALSIFICATION_REQUIRED: YES",
                "- DOMAIN_FALSIFICATION_ARTIFACT: docs/context/domain_falsification_pack_latest.json",
                "- SEMANTIC_RISK_REASON: Product meaning could be misread.",
                "- SEMANTIC_EXPERT_DOMAIN: product_ux",
                "",
            ]
        ),
    )

    result = _run(tmp_path, round_contract)
    assert result.returncode == 1
    assert "DOMAIN_FALSIFICATION_ARTIFACT missing" in (result.stdout + result.stderr)


def test_domain_falsification_pack_fails_for_unknown_domain_without_board_reentry(tmp_path: Path) -> None:
    round_contract = tmp_path / "docs/context/round_contract_latest.md"
    artifact = tmp_path / "docs/context/domain_falsification_pack_latest.json"
    _write_json(
        artifact,
        {"hypothesis": "Unknown semantic risk area", "status": "COMPLETED"},
    )
    _write_text(
        round_contract,
        "\n".join(
            [
                "# Round Contract",
                "- DOMAIN_FALSIFICATION_REQUIRED: YES",
                "- DOMAIN_FALSIFICATION_ARTIFACT: docs/context/domain_falsification_pack_latest.json",
                "- SEMANTIC_RISK_REASON: Domain boundary is unclear.",
                "- SEMANTIC_EXPERT_DOMAIN: unknown",
                "- UNKNOWN_EXPERT_DOMAIN_POLICY: ESCALATE_TO_BOARD",
                "- BOARD_REENTRY_REQUIRED: NO",
                "- BOARD_REENTRY_REASON: N/A",
                "",
            ]
        ),
    )

    result = _run(tmp_path, round_contract)
    assert result.returncode == 1
    output = result.stdout + result.stderr
    assert "BOARD_REENTRY_REQUIRED: YES" in output
    assert "BOARD_REENTRY_REASON" in output
