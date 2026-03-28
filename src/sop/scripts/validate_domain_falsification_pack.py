from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


KEY_VALUE_PATTERN = re.compile(r"^\s*-\s*([A-Za-z0-9_]+)\s*:\s*(.*?)\s*$")
ALLOWED_SEMANTIC_EXPERT_DOMAINS = {
    "macro_econ",
    "math_stats",
    "product_ux",
    "unknown",
    "none",
}
ALLOWED_UNKNOWN_DOMAIN_POLICIES = {
    "ESCALATE_TO_BOARD",
    "ESCALATE_TO_PM",
    "HOLD_AND_REQUEST_CLARIFICATION",
}


def _read_text(path: Path) -> tuple[str | None, str | None]:
    if not path.exists():
        return None, f"Missing input file: {path}"
    try:
        return path.read_text(encoding="utf-8-sig"), None
    except Exception as exc:
        return None, f"Failed to read file {path}: {exc}"


def _parse_markdown_fields(markdown: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in markdown.splitlines():
        match = KEY_VALUE_PATTERN.match(line)
        if match is None:
            continue
        key = match.group(1).strip().upper()
        value = match.group(2).strip()
        if key:
            fields[key] = value
    return fields


def _is_placeholder(value: str | None) -> bool:
    if not isinstance(value, str):
        return True
    text = value.strip()
    if not text:
        return True
    lowered = text.lower()
    if lowered in {"n/a", "na", "none", "null", "todo", "tbd"}:
        return True
    if lowered.startswith("todo(") or lowered.startswith("todo:"):
        return True
    return False


def _resolve_artifact_path(repo_root: Path, artifact_value: str) -> Path:
    candidate = Path(artifact_value)
    if candidate.is_absolute():
        return candidate
    return repo_root / candidate


def _validate_artifact_structure(path: Path) -> tuple[bool, str]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
        except Exception as exc:
            return False, f"DOMAIN_FALSIFICATION_ARTIFACT invalid JSON: {exc}"
        if not isinstance(payload, dict):
            return False, "DOMAIN_FALSIFICATION_ARTIFACT JSON root must be an object."
        if not payload:
            return False, "DOMAIN_FALSIFICATION_ARTIFACT JSON must not be empty."
        if not isinstance(payload.get("hypothesis") or payload.get("claim"), str):
            return False, "DOMAIN_FALSIFICATION_ARTIFACT JSON must include hypothesis or claim."
        if not isinstance(payload.get("status") or payload.get("result"), str):
            return False, "DOMAIN_FALSIFICATION_ARTIFACT JSON must include status or result."
        falsification_checks = payload.get("falsification_checks") or payload.get("counterexamples")
        if not isinstance(falsification_checks, list) or not falsification_checks:
            return False, "DOMAIN_FALSIFICATION_ARTIFACT JSON must include non-empty falsification_checks or counterexamples."
        return True, ""

    text, error = _read_text(path)
    if error:
        return False, error
    if text is None or not text.strip():
        return False, "DOMAIN_FALSIFICATION_ARTIFACT text content must not be empty."

    required_markers = (
        "## Claim Under Test",
        "## Canonical Sources",
        "## Falsification Attempts",
        "## Verdict",
        "- Claim:",
        "- Why high semantic risk:",
        "- Source 1:",
        "- Source 2:",
        "- Counterexample A:",
        "- Counterexample B:",
        "- Result:",
        "- Next action:",
    )
    missing_markers = [marker for marker in required_markers if marker not in text]
    if missing_markers:
        return (
            False,
            "DOMAIN_FALSIFICATION_ARTIFACT markdown missing required markers: "
            + ", ".join(missing_markers),
        )
    return True, ""


def _validate_unknown_domain_controls(fields: dict[str, str]) -> list[str]:
    errors: list[str] = []
    policy = fields.get("UNKNOWN_EXPERT_DOMAIN_POLICY", "").strip().upper()
    board_reentry_required = fields.get("BOARD_REENTRY_REQUIRED", "").strip().upper()
    board_reentry_reason = fields.get("BOARD_REENTRY_REASON", "")

    if policy not in ALLOWED_UNKNOWN_DOMAIN_POLICIES:
        errors.append(
            "SEMANTIC_EXPERT_DOMAIN=unknown requires a valid UNKNOWN_EXPERT_DOMAIN_POLICY."
        )
    if board_reentry_required != "YES":
        errors.append(
            "SEMANTIC_EXPERT_DOMAIN=unknown requires BOARD_REENTRY_REQUIRED: YES."
        )
    if _is_placeholder(board_reentry_reason):
        errors.append(
            "SEMANTIC_EXPERT_DOMAIN=unknown requires non-placeholder BOARD_REENTRY_REASON."
        )
    return errors


def _run_validation(repo_root: Path, round_contract_path: Path) -> tuple[int, str]:
    markdown, read_error = _read_text(round_contract_path)
    if read_error:
        return 2, f"[ERROR] {read_error}"

    fields = _parse_markdown_fields(markdown or "")
    required_raw = fields.get("DOMAIN_FALSIFICATION_REQUIRED", "NO").strip().upper()
    if required_raw not in {"YES", "NO"}:
        return (
            1,
            "[ERROR] DOMAIN_FALSIFICATION_REQUIRED must be YES or NO.",
        )

    if required_raw == "NO":
        return 0, "[OK] DOMAIN_FALSIFICATION_REQUIRED=NO (validation not required)."

    semantic_risk_reason = fields.get("SEMANTIC_RISK_REASON", "")
    semantic_expert_domain = fields.get("SEMANTIC_EXPERT_DOMAIN", "").strip().lower()
    artifact_value = fields.get("DOMAIN_FALSIFICATION_ARTIFACT", "")

    errors: list[str] = []
    if _is_placeholder(semantic_risk_reason):
        errors.append(
            "SEMANTIC_RISK_REASON must be non-placeholder when DOMAIN_FALSIFICATION_REQUIRED=YES."
        )
    if semantic_expert_domain not in ALLOWED_SEMANTIC_EXPERT_DOMAINS:
        errors.append(
            "SEMANTIC_EXPERT_DOMAIN must be one of macro_econ|math_stats|product_ux|unknown|none."
        )
    elif semantic_expert_domain == "none":
        errors.append(
            "SEMANTIC_EXPERT_DOMAIN cannot be none when DOMAIN_FALSIFICATION_REQUIRED=YES."
        )
    if _is_placeholder(artifact_value):
        errors.append(
            "DOMAIN_FALSIFICATION_ARTIFACT must be a concrete path when DOMAIN_FALSIFICATION_REQUIRED=YES."
        )

    artifact_path: Path | None = None
    if not errors:
        artifact_path = _resolve_artifact_path(repo_root, artifact_value.strip())
        if not artifact_path.exists():
            errors.append(
                f"DOMAIN_FALSIFICATION_ARTIFACT missing: {artifact_path}"
            )
        else:
            artifact_ok, artifact_error = _validate_artifact_structure(artifact_path)
            if not artifact_ok:
                errors.append(artifact_error)

    if semantic_expert_domain == "unknown":
        errors.extend(_validate_unknown_domain_controls(fields))

    if errors:
        return 1, "[ERROR] " + "; ".join(errors)

    artifact_text = str(artifact_path) if artifact_path is not None else artifact_value.strip()
    return (
        0,
        f"[OK] Domain falsification pack validation passed (domain={semantic_expert_domain}, artifact={artifact_text}).",
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate structural domain-falsification pack fields for semantic-risk rounds. "
            "Exit 0=pass, 1=validation fail, 2=input/infra error."
        )
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path("."),
        help="Repository root used to resolve relative artifact paths.",
    )
    parser.add_argument(
        "--round-contract-md",
        type=Path,
        default=Path("docs/context/round_contract_latest.md"),
        help="Round contract markdown path.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = args.repo_root.resolve()
    round_contract_path = (
        args.round_contract_md
        if args.round_contract_md.is_absolute()
        else repo_root / args.round_contract_md
    )
    exit_code, message = _run_validation(repo_root=repo_root, round_contract_path=round_contract_path)
    print(message)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
