from __future__ import annotations

__test__ = False

import argparse
import json
from pathlib import Path

from run_baseline_benchmark import load_suite_provider_id


NO_CHANGE_THRESHOLD = 0.05


def load_baseline(suite_name: str, repo_root: Path) -> dict:
    """Load the persisted baseline for a suite."""
    suite_path = repo_root / "benchmark" / "suites" / f"{suite_name}.yaml"
    model_id = load_suite_provider_id(suite_path)
    baseline_path = (
        repo_root
        / "benchmark"
        / "baselines"
        / f"{model_id.replace(':', '_')}_{suite_name}_baseline.json"
    )
    return json.loads(baseline_path.read_text(encoding="utf-8"))


def compare_to_baseline(current_score: float, baseline: dict) -> str:
    """Classify capability change against the approved 5% noise band."""
    delta = current_score - baseline["baseline_score"]
    if abs(delta) < NO_CHANGE_THRESHOLD:
        return "no_change"
    if delta > 0:
        return "improvement"
    return "degradation"


def generate_policy_proposal(current_score: float, baseline: dict) -> dict | None:
    """Create an additive-only policy proposal from a benchmark delta."""
    comparison = compare_to_baseline(current_score=current_score, baseline=baseline)
    if comparison == "no_change":
        return None

    suite = baseline["suite"]
    if comparison == "degradation":
        recommended_policy = {
            "sql_tasks": {
                "recommended_guardrail_strength": "tight",
                "min_review_level": "auditor",
                "min_approval_level": "ceo" if current_score < 0.60 else "auditor",
            }
        }
        rationale = (
            f"Model capability degraded: {suite} score dropped from "
            f"{baseline['baseline_score']:.2f} to {current_score:.2f}"
        )
    else:
        recommended_policy = {
            "sql_tasks": {
                "recommended_guardrail_strength": "medium",
                "min_review_level": "none",
            }
        }
        rationale = (
            f"Model capability improved: {suite} score increased from "
            f"{baseline['baseline_score']:.2f} to {current_score:.2f}"
        )

    return {
        "comparison": comparison,
        "current_score": current_score,
        "baseline_score": baseline["baseline_score"],
        "recommended_policy": recommended_policy,
        "rationale": rationale,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Exercise the Phase 5 policy proposal logic.")
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
    baseline = load_baseline(suite_name=args.suite_name, repo_root=args.repo_root.resolve())
    scenarios = {
        "degradation": baseline["baseline_score"] - 0.13,
        "improvement": baseline["baseline_score"] + 0.12,
        "no_change": baseline["baseline_score"] + 0.02,
    }

    for label, score in scenarios.items():
        proposal = generate_policy_proposal(score, baseline)
        print(f"SCENARIO: {label}")
        if proposal is None:
            print("NO_PROPOSAL")
            continue
        print(json.dumps(proposal, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
