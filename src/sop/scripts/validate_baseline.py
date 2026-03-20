from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import median

from run_baseline_benchmark import load_suite_provider_id


def validate_baseline_payload(baseline: dict) -> list[str]:
    """Return validation errors for a persisted baseline payload."""
    errors: list[str] = []
    required_fields = ["model", "suite", "baseline_score", "baseline_runs", "established_at"]
    for field in required_fields:
        if field not in baseline:
            errors.append(f"missing required field: {field}")

    if errors:
        return errors

    runs = baseline["baseline_runs"]
    if not isinstance(runs, list) or len(runs) != 3:
        return ["baseline_runs must contain exactly 3 runs"]

    scores: list[float] = []
    for index, run in enumerate(runs):
        score = run.get("aggregate_score")
        if not isinstance(score, (int, float)) or isinstance(score, bool):
            errors.append(f"baseline run {index} missing numeric aggregate_score")
            continue
        scores.append(float(score))

    if errors:
        return errors

    baseline_score = baseline["baseline_score"]
    if not isinstance(baseline_score, (int, float)) or isinstance(baseline_score, bool):
        return ["baseline_score must be numeric"]

    expected_median = median(scores)
    if abs(float(baseline_score) - expected_median) > 1e-9:
        errors.append(f"baseline_score {baseline_score} does not match median {expected_median}")
    return errors


def validate_baseline(baseline_path: Path) -> tuple[bool, list[str]]:
    """Validate a baseline JSON file and return (ok, errors)."""
    if not baseline_path.exists():
        return False, [f"baseline file not found: {baseline_path}"]

    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    errors = validate_baseline_payload(baseline)
    return len(errors) == 0, errors


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate the Phase 5 Promptfoo baseline JSON.")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root containing benchmark and scripts directories.",
    )
    parser.add_argument("--suite-name", default="sql_accuracy")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = args.repo_root.resolve()
    suite_path = repo_root / "benchmark" / "suites" / f"{args.suite_name}.yaml"
    model_id = load_suite_provider_id(suite_path)
    baseline_path = (
        repo_root
        / "benchmark"
        / "baselines"
        / f"{model_id.replace(':', '_')}_{args.suite_name}_baseline.json"
    )
    is_valid, errors = validate_baseline(baseline_path)
    if not is_valid:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print(f"BASELINE_VALID: {baseline_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
