from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from statistics import median

import yaml


def utc_now_iso() -> str:
    """Return an ISO-8601 UTC timestamp."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_suite_provider_id(suite_path: Path) -> str:
    """Read the configured provider id from a Promptfoo suite file."""
    suite_data = yaml.safe_load(suite_path.read_text(encoding="utf-8"))
    providers = suite_data.get("providers")
    if not isinstance(providers, list) or not providers:
        raise ValueError(f"Promptfoo suite missing providers list: {suite_path}")

    provider_id = providers[0].get("id")
    if not isinstance(provider_id, str) or not provider_id:
        raise ValueError(f"Promptfoo suite missing provider id: {suite_path}")
    return provider_id


def parse_promptfoo_outputs(output_data: dict) -> list[dict]:
    """Extract Promptfoo result entries from exported JSON."""
    results_obj = output_data.get("results")
    if not isinstance(results_obj, dict):
        raise ValueError("Promptfoo output missing results object")

    for key in ("results", "outputs"):
        outputs = results_obj.get(key)
        if isinstance(outputs, list) and outputs:
            return outputs
    raise ValueError("Promptfoo output missing results.results/results.outputs list")


def ensure_no_provider_errors(outputs: list[dict]) -> None:
    """Fail closed when Promptfoo captured provider or transport errors."""
    for index, output in enumerate(outputs):
        error = output.get("error")
        if not error:
            continue

        # Assertion failures are expected and should not block baseline establishment
        # Provider errors typically contain "API error", "timeout", "connection", etc.
        error_str = str(error).lower()
        if any(keyword in error_str for keyword in ["api error", "timeout", "connection", "authentication", "rate limit", "quota"]):
            raise RuntimeError(
                f"Promptfoo result at index {index} contains provider error; inspect raw JSON before continuing"
            )


def aggregate_output_scores(outputs: list[dict]) -> float:
    """Average numeric output scores so the 5% ADR threshold remains meaningful."""
    scores: list[float] = []
    for index, output in enumerate(outputs):
        score = output.get("score")
        if not isinstance(score, (int, float)) or isinstance(score, bool):
            raise ValueError(f"Promptfoo output at index {index} missing numeric score")
        scores.append(float(score))
    return sum(scores) / len(scores)


def resolve_promptfoo_command(promptfoo_exe: str) -> list[str]:
    """Resolve Promptfoo to a directly executable command for subprocess."""
    resolved = shutil.which(promptfoo_exe)
    if resolved:
        return [resolved]

    if promptfoo_exe == "promptfoo":
        npx = shutil.which("npx") or shutil.which("npx.cmd")
        if npx:
            return [npx, "promptfoo"]

    raise FileNotFoundError(f"Unable to resolve executable: {promptfoo_exe}")


def run_benchmark_suite(
    suite_name: str,
    run_number: int,
    repo_root: Path,
    promptfoo_exe: str = "promptfoo",
    env_file: Path | None = None,
) -> dict:
    """Run a single Promptfoo suite and return the aggregated score."""
    suite_path = repo_root / "benchmark" / "suites" / f"{suite_name}.yaml"
    results_dir = repo_root / "benchmark" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    output_path = results_dir / f"{suite_name}_run{run_number}.json"
    promptfoo_command = resolve_promptfoo_command(promptfoo_exe)

    cmd = [
        *promptfoo_command,
        "eval",
        "-c",
        str(suite_path),
        "-o",
        str(output_path),
        "--no-cache",
    ]
    if env_file:
        cmd.extend(["--env-file", str(env_file)])

    result = subprocess.run(
        cmd,
        capture_output=True,
        cwd=str(repo_root),
        text=True,
    )

    # Check if output file was created (Promptfoo may return non-zero on test failures)
    if not output_path.exists():
        raise RuntimeError(
            f"Promptfoo did not create output file for {suite_name} run {run_number}. "
            f"Exit code: {result.returncode}, stderr: {result.stderr.strip()}"
        )

    output_data = json.loads(output_path.read_text(encoding="utf-8"))
    outputs = parse_promptfoo_outputs(output_data)
    ensure_no_provider_errors(outputs)
    aggregate_score = aggregate_output_scores(outputs)
    passed_tests = sum(
        1 for output in outputs if output.get("success") is True or output.get("pass") is True
    )

    return {
        "run_number": run_number,
        "aggregate_score": aggregate_score,
        "passed_tests": passed_tests,
        "total_tests": len(outputs),
        "timestamp": utc_now_iso(),
        "output_file": str(output_path),
    }


def establish_baseline(
    suite_name: str,
    repo_root: Path,
    promptfoo_exe: str = "promptfoo",
    runs: int = 3,
    env_file: Path | None = None,
) -> dict:
    """Run repeated Promptfoo evaluations and persist the median baseline."""
    if runs < 1:
        raise ValueError("runs must be >= 1")

    suite_path = repo_root / "benchmark" / "suites" / f"{suite_name}.yaml"
    model_id = load_suite_provider_id(suite_path)
    run_summaries = [
        run_benchmark_suite(
            suite_name=suite_name,
            run_number=run_number,
            repo_root=repo_root,
            promptfoo_exe=promptfoo_exe,
            env_file=env_file,
        )
        for run_number in range(1, runs + 1)
    ]

    scores = [run["aggregate_score"] for run in run_summaries]
    baseline = {
        "model": model_id,
        "suite": suite_name,
        "baseline_score": median(scores),
        "baseline_runs": run_summaries,
        "established_at": utc_now_iso(),
    }

    baseline_dir = repo_root / "benchmark" / "baselines"
    baseline_dir.mkdir(parents=True, exist_ok=True)
    baseline_path = baseline_dir / f"{model_id.replace(':', '_')}_{suite_name}_baseline.json"
    baseline_path.write_text(json.dumps(baseline, indent=2), encoding="utf-8")
    return baseline


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Phase 5 Promptfoo baseline benchmark.")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root containing benchmark and scripts directories.",
    )
    parser.add_argument("--suite-name", default="sql_accuracy")
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--promptfoo-exe", default="promptfoo")
    parser.add_argument("--env-file", type=Path, help="Path to .env file for Promptfoo")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    env_file = args.env_file.resolve() if args.env_file else None
    baseline = establish_baseline(
        suite_name=args.suite_name,
        repo_root=args.repo_root.resolve(),
        promptfoo_exe=args.promptfoo_exe,
        runs=args.runs,
        env_file=env_file,
    )
    print(f"BASELINE_MODEL: {baseline['model']}")
    print(f"BASELINE_SUITE: {baseline['suite']}")
    print(f"BASELINE_SCORE: {baseline['baseline_score']:.4f}")
    print(f"BASELINE_RUNS: {len(baseline['baseline_runs'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
