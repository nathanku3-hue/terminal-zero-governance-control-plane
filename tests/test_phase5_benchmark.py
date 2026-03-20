from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml

try:
    from run_baseline_benchmark import (
        aggregate_output_scores,
        ensure_no_provider_errors,
        establish_baseline,
        load_suite_provider_id,
        parse_promptfoo_outputs,
        resolve_promptfoo_command,
    )
    from test_policy_proposal import compare_to_baseline, generate_policy_proposal
    from validate_baseline import validate_baseline_payload
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    from run_baseline_benchmark import (
        aggregate_output_scores,
        ensure_no_provider_errors,
        establish_baseline,
        load_suite_provider_id,
        parse_promptfoo_outputs,
        resolve_promptfoo_command,
    )
    from test_policy_proposal import compare_to_baseline, generate_policy_proposal
    from validate_baseline import validate_baseline_payload


# Benchmark suite files are gitignored (experimental Phase 5 work)
# Skip tests that require these files when they don't exist
BENCHMARK_SUITE_PATH = Path(__file__).resolve().parents[1] / "benchmark" / "suites" / "sql_accuracy.yaml"
requires_benchmark_suite = pytest.mark.skipif(
    not BENCHMARK_SUITE_PATH.exists(),
    reason="benchmark/suites/sql_accuracy.yaml is gitignored (experimental)"
)


@requires_benchmark_suite
def test_sql_accuracy_suite_uses_scoped_promptfoo_tests() -> None:
    suite = yaml.safe_load(BENCHMARK_SUITE_PATH.read_text(encoding="utf-8"))

    assert suite["providers"][0]["id"] == "anthropic:claude-opus-4-6"
    assert len(suite["prompts"]) == 5
    assert len(suite["tests"]) == 5
    assert all("raw" in prompt for prompt in suite["prompts"])
    assert all(isinstance(test["prompts"], list) and len(test["prompts"]) == 1 for test in suite["tests"])


@requires_benchmark_suite
def test_load_suite_provider_id_returns_provider() -> None:
    assert load_suite_provider_id(BENCHMARK_SUITE_PATH) == "anthropic:claude-opus-4-6"


def test_parse_promptfoo_outputs_rejects_missing_results_object() -> None:
    try:
        parse_promptfoo_outputs({})
    except ValueError as exc:
        assert "results object" in str(exc)
    else:
        raise AssertionError("expected ValueError for missing results object")


def test_parse_promptfoo_outputs_supports_current_promptfoo_results_array() -> None:
    outputs = parse_promptfoo_outputs({"results": {"results": [{"score": 1.0, "success": True}]}})

    assert outputs == [{"score": 1.0, "success": True}]


def test_aggregate_output_scores_uses_numeric_scores() -> None:
    outputs = [
        {"pass": True, "score": 1.0},
        {"pass": False, "score": 0.25},
        {"pass": True, "score": 0.75},
    ]

    assert aggregate_output_scores(outputs) == 2.0 / 3.0


def test_aggregate_output_scores_rejects_missing_numeric_score() -> None:
    try:
        aggregate_output_scores([{"pass": True, "score": None}])
    except ValueError as exc:
        assert "missing numeric score" in str(exc)
    else:
        raise AssertionError("expected ValueError for missing numeric score")


def test_ensure_no_provider_errors_rejects_provider_error() -> None:
    try:
        ensure_no_provider_errors(
            [
                {
                    "score": 0.0,
                    "success": False,
                    "error": "API error: 403 Forbidden",
                }
            ]
        )
    except RuntimeError as exc:
        assert "provider error" in str(exc)
    else:
        raise AssertionError("expected RuntimeError for provider error")


def test_resolve_promptfoo_command_falls_back_to_npx(monkeypatch) -> None:
    def fake_which(executable: str) -> str | None:
        if executable in {"npx", "npx.cmd"}:
            return "C:\\Users\\Lenovo\\AppData\\Roaming\\npm\\npx.cmd"
        return None

    monkeypatch.setattr("run_baseline_benchmark.shutil.which", fake_which)

    assert resolve_promptfoo_command("promptfoo") == [
        "C:\\Users\\Lenovo\\AppData\\Roaming\\npm\\npx.cmd",
        "promptfoo",
    ]


def test_establish_baseline_persists_median_score(tmp_path: Path, monkeypatch) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    benchmark_suites = repo_root / "benchmark" / "suites"
    benchmark_suites.mkdir(parents=True)
    suite_path = benchmark_suites / "sql_accuracy.yaml"
    suite_path.write_text(
        "providers:\n  - id: openai:gpt-5\n",
        encoding="utf-8",
    )

    scores = [0.70, 0.90, 0.80]

    def fake_run_benchmark_suite(
        suite_name: str,
        run_number: int,
        repo_root: Path,
        promptfoo_exe: str = "promptfoo",
        env_file: Path | None = None,
    ) -> dict:
        return {
            "run_number": run_number,
            "aggregate_score": scores[run_number - 1],
            "passed_tests": 4,
            "total_tests": 5,
            "timestamp": "2026-03-12T00:00:00Z",
            "output_file": f"run_{run_number}.json",
        }

    monkeypatch.setattr("run_baseline_benchmark.run_benchmark_suite", fake_run_benchmark_suite)

    baseline = establish_baseline(suite_name="sql_accuracy", repo_root=repo_root)

    assert baseline["model"] == "openai:gpt-5"
    assert baseline["baseline_score"] == 0.80
    persisted = json.loads(
        (
            repo_root
            / "benchmark"
            / "baselines"
            / "openai_gpt-5_sql_accuracy_baseline.json"
        ).read_text(encoding="utf-8")
    )
    assert persisted["baseline_score"] == 0.80


def test_validate_baseline_payload_rejects_wrong_median() -> None:
    payload = {
        "model": "openai:gpt-5",
        "suite": "sql_accuracy",
        "baseline_score": 0.70,
        "baseline_runs": [
            {"aggregate_score": 0.70},
            {"aggregate_score": 0.90},
            {"aggregate_score": 0.80},
        ],
        "established_at": "2026-03-12T00:00:00Z",
    }

    errors = validate_baseline_payload(payload)
    assert errors == ["baseline_score 0.7 does not match median 0.8"]


def test_compare_to_baseline_uses_five_percent_noise_band() -> None:
    baseline = {"baseline_score": 0.80}

    assert compare_to_baseline(0.84, baseline) == "no_change"
    assert compare_to_baseline(0.86, baseline) == "improvement"
    assert compare_to_baseline(0.74, baseline) == "degradation"


def test_generate_policy_proposal_uses_additive_only_format() -> None:
    baseline = {"suite": "sql_accuracy", "baseline_score": 0.80}

    proposal = generate_policy_proposal(0.62, baseline)

    assert proposal is not None
    policy = proposal["recommended_policy"]["sql_tasks"]
    assert policy["recommended_guardrail_strength"] == "tight"
    assert policy["min_review_level"] == "auditor"
    assert policy["min_approval_level"] == "auditor"
    assert "require_auditor_review" not in json.dumps(proposal)
