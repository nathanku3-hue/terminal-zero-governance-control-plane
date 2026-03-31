from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _ensure_src_on_path() -> None:
    current = Path(__file__).resolve()
    for parent in (current,) + tuple(current.parents):
        src_dir = parent / "src"
        if (src_dir / "sop" / "__init__.py").exists():
            candidate = str(src_dir)
            if candidate not in sys.path:
                sys.path.insert(0, candidate)
            return


try:
    from sop.phase8_ga_readiness import run_burnin, validate_ga_verdict
except ModuleNotFoundError:
    _ensure_src_on_path()
    from sop.phase8_ga_readiness import run_burnin, validate_ga_verdict


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _write_signoff(path: Path, burnin: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    verdict = validate_ga_verdict(str(burnin["final_ga_verdict"]))
    summary = burnin["unexpected_failure_summary"]
    mapping = burnin["scenario_fixture_mapping"]

    lines = [
        "# GA Signoff Packet (Latest)",
        "",
        "## Final GA Verdict",
        verdict,
        "",
        "## Burn-In Summary",
        f"- Total Runs: {burnin['total_runs']}",
        f"- Scenario Count: {burnin['scenario_count']}",
        f"- Runs per Scenario: {burnin['runs_per_scenario']}",
        f"- Unexpected Failures: {summary['unexpected_failures']}",
        f"- Unexpected Failure Rate: {summary['unexpected_failure_rate']:.6f}",
        "",
        "## Scenario-to-Fixture Mapping (Pinned)",
    ]

    for scenario_id, fixture in mapping.items():
        lines.append(f"- `{scenario_id}` → `{fixture}`")

    lines.extend(
        [
            "",
            "## Signoff Criteria",
            "- PASS only if unexpected_failure_rate == 0 and no contract failures.",
            "- FAIL otherwise.",
            "",
            "## Notes",
            "- Verdict enum is locked to PASS|FAIL only.",
        ]
    )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate Phase 8 GA readiness artifacts.")
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--burnin-report", type=Path, default=Path("docs/context/burnin_report_latest.json"))
    parser.add_argument("--slo-baseline", type=Path, default=Path("docs/context/slo_baseline_latest.json"))
    parser.add_argument("--ga-signoff", type=Path, default=Path("docs/context/ga_signoff_packet_latest.md"))
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    burnin = run_burnin(repo_root)

    burnin_report_path = repo_root / args.burnin_report
    _write_json(burnin_report_path, burnin)

    slo_baseline = {
        "schema_version": "1.0.0",
        "generated_at_utc": burnin["generated_at_utc"],
        "command_set": {
            "burnin": "python scripts/phase8_ga_readiness.py --repo-root .",
            "test": "pytest tests/test_phase8_ga_readiness.py",
        },
        "baseline": {
            "total_runs": burnin["total_runs"],
            "unexpected_failures": burnin["unexpected_failure_summary"]["unexpected_failures"],
            "unexpected_failure_rate": burnin["unexpected_failure_summary"]["unexpected_failure_rate"],
            "final_ga_verdict": burnin["final_ga_verdict"],
        },
    }
    slo_baseline_path = repo_root / args.slo_baseline
    _write_json(slo_baseline_path, slo_baseline)

    signoff_path = repo_root / args.ga_signoff
    _write_signoff(signoff_path, burnin)

    print(f"wrote {burnin_report_path}")
    print(f"wrote {slo_baseline_path}")
    print(f"wrote {signoff_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
