from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

import yaml


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "validate_evidence_hashes.py"
)


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _sha256_hex(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _write_evidence_file(evidence_dir: Path, hash_hex: str, content: bytes) -> None:
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / f"{hash_hex}.log").write_bytes(content)


def _run_validator(traceability_path: Path, evidence_dir: Path) -> subprocess.CompletedProcess[str]:
    command = [
        sys.executable,
        str(SCRIPT_PATH),
        "--input",
        str(traceability_path),
        "--evidence-dir",
        str(evidence_dir),
    ]
    return subprocess.run(command, capture_output=True, text=True, check=False)


def test_validate_evidence_hashes_passes_with_matching_signoff_and_validator_hashes(
    tmp_path: Path,
) -> None:
    evidence_dir = tmp_path / "evidence_hashes"
    signoff_content = b"signoff proof"
    validator_content = b"validator output"
    signoff_hash = _sha256_hex(signoff_content)
    validator_hash = _sha256_hex(validator_content)
    _write_evidence_file(evidence_dir, signoff_hash, signoff_content)
    _write_evidence_file(evidence_dir, validator_hash, validator_content)

    traceability_path = tmp_path / "pm_to_code_traceability.yaml"
    _write_yaml(
        traceability_path,
        {
            "directives": [
                {
                    "directive_id": "D-OK",
                    "actual_signoff_experts": [
                        {
                            "signoff_by": "@reviewer-a",
                            "evidence_hash": f"sha256:{signoff_hash}",
                        }
                    ],
                    "traceability": {
                        "validators": [
                            {
                                "name": "tests/test_example.py::test_ok",
                                "output_hash_sha256": f"sha256:{validator_hash}",
                            }
                        ]
                    },
                }
            ]
        },
    )

    result = _run_validator(traceability_path, evidence_dir)
    assert result.returncode == 0, result.stdout + result.stderr


def test_validate_evidence_hashes_fails_when_hash_backing_file_does_not_match_contents(
    tmp_path: Path,
) -> None:
    evidence_dir = tmp_path / "evidence_hashes"
    declared_hash = _sha256_hex(b"expected content")
    _write_evidence_file(evidence_dir, declared_hash, b"different content")

    traceability_path = tmp_path / "pm_to_code_traceability.yaml"
    _write_yaml(
        traceability_path,
        {
            "directives": [
                {
                    "directive_id": "D-BAD-HASH",
                    "traceability": {
                        "validators": [
                            {
                                "name": "tests/test_example.py::test_bad",
                                "output_hash_sha256": f"sha256:{declared_hash}",
                            }
                        ]
                    },
                }
            ]
        },
    )

    result = _run_validator(traceability_path, evidence_dir)
    assert result.returncode == 1
    combined = result.stdout + result.stderr
    assert "Hash mismatch" in combined
    assert "D-BAD-HASH" in combined
