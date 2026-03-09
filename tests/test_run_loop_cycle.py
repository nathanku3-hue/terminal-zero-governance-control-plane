from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from textwrap import dedent

import pytest

from scripts import run_loop_cycle


POWERSHELL_EXE = Path("C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe")


def _write_text(path: Path, text: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _prepare_scripts_dir(path: Path, include_weekly_truth: bool = True) -> None:
    _write_text(path / "auditor_calibration_report.py", "print('ok')\n")
    _write_text(path / "generate_ceo_go_signal.py", "print('ok')\n")
    _write_text(path / "generate_ceo_weekly_summary.py", "print('ok')\n")
    _write_text(path / "evaluate_context_compaction_trigger.py", "print('ok')\n")
    _write_text(path / "build_exec_memory_packet.py", "print('ok')\n")
    _write_text(path / "validate_ceo_go_signal_truth.py", "print('ok')\n")
    _write_text(path / "validate_exec_memory_truth.py", "print('ok')\n")
    _write_text(path / "validate_round_contract_checks.py", "print('ok')\n")
    _write_text(path / "validate_counterexample_gate.py", "print('ok')\n")
    _write_text(path / "validate_dual_judge_gate.py", "print('ok')\n")
    _write_text(path / "validate_refactor_mock_policy.py", "print('ok')\n")
    _write_text(path / "validate_review_checklist.py", "print('ok')\n")
    _write_text(path / "validate_interface_contracts.py", "print('ok')\n")
    _write_text(path / "validate_parallel_fanin.py", "print('ok')\n")
    _write_text(path / "validate_loop_closure.py", "print('ok')\n")
    if include_weekly_truth:
        _write_text(path / "validate_ceo_weekly_summary_truth.py", "print('ok')\n")


def _repo_script_path(script_name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "scripts" / script_name


def _copy_script(script_name: str, target_dir: Path) -> None:
    source = _repo_script_path(script_name)
    target = target_dir / script_name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def _prepare_real_phase_end_scripts_dir(path: Path) -> None:
    _prepare_scripts_dir(path, include_weekly_truth=False)

    for script_name in [
        "phase_end_handover.ps1",
        "validate_traceability.py",
        "validate_evidence_hashes.py",
        "validate_worker_reply_packet.py",
        "validate_orphan_changes.py",
        "validate_dispatch_acks.py",
        "build_ceo_bridge_digest.py",
        "validate_digest_freshness.py",
    ]:
        _copy_script(script_name, path)

    _write_text(
        path / "build_context_packet.py",
        "from __future__ import annotations\n"
        "\n"
        "import json\n"
        "import sys\n"
        "from pathlib import Path\n"
        "\n"
        "\n"
        "def _arg(name: str, default: str = \"\") -> str:\n"
        "    if name in sys.argv:\n"
        "        idx = sys.argv.index(name)\n"
        "        if idx + 1 < len(sys.argv):\n"
        "            return sys.argv[idx + 1]\n"
        "    return default\n"
        "\n"
        "\n"
        "def main() -> int:\n"
        "    repo_root = Path(_arg(\"--repo-root\", \".\")).resolve()\n"
        "    context_dir = repo_root / \"docs\" / \"context\"\n"
        "    context_dir.mkdir(parents=True, exist_ok=True)\n"
        "    (context_dir / \"current_context.json\").write_text(\n"
        "        json.dumps(\n"
        "            {\n"
        "                \"schema_version\": \"1.0.0\",\n"
        "                \"generated_at_utc\": \"2026-03-09T00:00:00Z\",\n"
        "                \"what_was_done\": [\"Prepared phase-end test fixture\"],\n"
        "            },\n"
        "            indent=2,\n"
        "        ),\n"
        "        encoding=\"utf-8\",\n"
        "    )\n"
        "    (context_dir / \"current_context.md\").write_text(\n"
        "        \"# Current Context\\n\\n- Prepared phase-end test fixture.\\n\",\n"
        "        encoding=\"utf-8\",\n"
        "    )\n"
        "    gemini_path = repo_root / \"docs\" / \"handover\" / \"gemini\" / \"phase24_gemini_handover.md\"\n"
        "    gemini_path.parent.mkdir(parents=True, exist_ok=True)\n"
        "    gemini_path.write_text(\"# Gemini Handoff\\n\", encoding=\"utf-8\")\n"
        "    print(\"ok\")\n"
        "    return 0\n"
        "\n"
        "\n"
        "if __name__ == \"__main__\":\n"
        "    sys.exit(main())\n",
    )
    _write_text(
        path / "aggregate_worker_status.py",
        dedent(
            """
            from __future__ import annotations

            import json
            import sys
            from pathlib import Path


            def _arg(name: str, default: str = "") -> str:
                if name in sys.argv:
                    idx = sys.argv.index(name)
                    if idx + 1 < len(sys.argv):
                        return sys.argv[idx + 1]
                return default


            def main() -> int:
                output_path = Path(_arg("--output")).resolve()
                output_path.parent.mkdir(parents=True, exist_ok=True)
                payload = {
                    "generated_utc": "2026-03-09T00:00:00Z",
                    "workers": [],
                    "summary": {
                        "total_workers": 0,
                        "executing": 0,
                        "idle": 0,
                        "stale": 0,
                        "escalated": 0,
                        "overall_health": "OK",
                    },
                    "parse_failures": [],
                }
                output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
                escalation_output = _arg("--escalation-output")
                if escalation_output:
                    esc_path = Path(escalation_output).resolve()
                    esc_path.parent.mkdir(parents=True, exist_ok=True)
                    esc_path.write_text(json.dumps({"events": []}, indent=2), encoding="utf-8")
                print("ok")
                return 0


            if __name__ == "__main__":
                sys.exit(main())
            """
        ).strip()
        + "\n",
    )
    _write_text(
        path / "generate_ceo_go_signal.py",
        "from __future__ import annotations\n"
        "\n"
        "import sys\n"
        "from pathlib import Path\n"
        "\n"
        "\n"
        "def _arg(name: str, default: str = \"\") -> str:\n"
        "    if name in sys.argv:\n"
        "        idx = sys.argv.index(name)\n"
        "        if idx + 1 < len(sys.argv):\n"
        "            return sys.argv[idx + 1]\n"
        "    return default\n"
        "\n"
        "\n"
        "def main() -> int:\n"
        "    output_path = Path(_arg(\"--output\", \"docs/context/ceo_go_signal.md\")).resolve()\n"
        "    output_path.parent.mkdir(parents=True, exist_ok=True)\n"
        "    output_path.write_text(\"# CEO GO Signal\\n\\nStatus: GO\\n\", encoding=\"utf-8\")\n"
        "    print(\"ok\")\n"
        "    return 0\n"
        "\n"
        "\n"
        "if __name__ == \"__main__\":\n"
        "    sys.exit(main())\n",
    )


def _git(repo_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )


def _prepare_real_phase_end_repo(repo_root: Path) -> None:
    context_dir = repo_root / "docs" / "context"
    scripts_dir = repo_root / "scripts"
    _prepare_real_phase_end_scripts_dir(scripts_dir)

    _write_text(context_dir / "phase_end_logs" / ".keep", "")
    _write_text(context_dir / "evidence_hashes" / ".keep", "")
    _write_text(
        repo_root / "docs" / "phase_brief" / "phase24c-brief.md",
        dedent(
            """
            # Phase 24C Brief

            ## What Was Done
            - Prepared a production-like phase-end lane.

            ## What Is Locked
            - Real phase_end_handover contract remains in place.

            ## What Is Next
            - Verify the non-skip lane with real gates.

            ## First Command
            python scripts/run_loop_cycle.py --repo-root .

            ## Next Todos
            - Validate real phase-end gate wiring.
            """
        ).strip()
        + "\n",
    )
    _write_text(
        repo_root / "docs" / "handover" / "phase24_handover.md",
        dedent(
            """
            # Phase 24 Handover

            ## What Was Done
            - Prepared handoff notes for the phase-end test lane.

            ## What Is Locked
            - Phase-end gate contract is under test.

            ## What Is Next
            - Run the deterministic non-skip lane.

            ## First Command
            python scripts/run_loop_cycle.py --repo-root .
            """
        ).strip()
        + "\n",
    )
    _write_text(repo_root / "docs" / "decision log.md", "# Decision Log\n")
    _write_text(repo_root / "docs" / "lessonss.md", "# Lessons\n")
    _write_text(repo_root / "top_level_PM.md", "# Top Level PM\n")
    _write_text(
        repo_root / "docs" / "pm_to_code_traceability.yaml",
        dedent(
            """
            schema_version: "1.0.0"
            directives:
              - directive_id: DIR-001
                status: MAPPED
                traceability:
                  code_diffs:
                    - file: covered_change.py
                    - file: docs/covered_change.py
                  validators:
                    - id: TEST-001
                      status: PASS
            """
        ).strip()
        + "\n",
    )
    _write_text(repo_root / "docs" / "covered_change.py", "print('baseline')\n")
    _write_text(repo_root / "docs" / "reference_note.md", "# Reference Note\n")
    _write_text(
        context_dir / "worker_reply_packet.json",
        json.dumps(
            {
                "schema_version": "1.0.0",
                "worker_id": "worker-1",
                "phase": "execution",
                "generated_at_utc": "2026-03-09T00:00:00Z",
                "items": [
                    {
                        "task_id": "TASK-001",
                        "decision": "Proceed",
                        "dod_result": "PASS",
                        "evidence_ids": ["EV-001"],
                        "open_risks": [],
                        "citations": [
                            {
                                "type": "code",
                                "path": "docs/covered_change.py",
                                "locator": "line 1",
                                "claim": "The latest covered change is present.",
                            }
                        ],
                        "confidence": {
                            "score": 0.95,
                            "band": "HIGH",
                            "rationale": "Deterministic fixture.",
                        },
                    }
                ],
            },
            indent=2,
        ),
    )
    _write_text(
        context_dir / "dispatch_manifest.json",
        json.dumps(
            {
                "schema_version": "1.0.0",
                "command_plan_hash_sha256": "hash-123",
                "ack_deadline_utc": "2099-01-01T00:00:00Z",
                "tasks": [{"correlation_id": "corr-001"}],
            },
            indent=2,
        ),
    )
    _write_text(
        context_dir / "dispatch" / "dispatch_ack.json",
        json.dumps(
            {
                "correlation_id": "corr-001",
                "command_plan_hash_sha256": "hash-123",
                "current_state": "COMPLETED",
                "lifecycle": [
                    {"state": "STARTED", "utc": "2026-03-09T00:00:00Z"},
                    {
                        "state": "COMPLETED",
                        "utc": "2026-03-09T00:01:00Z",
                        "bound_artifacts": ["docs/covered_change.py"],
                        "bound_tests": ["tests/test_run_loop_cycle.py::test_run_loop_cycle_with_real_phase_end_handover_contract"],
                    },
                ],
            },
            indent=2,
        ),
    )

    _git(repo_root, "init")
    _git(repo_root, "config", "user.email", "test@example.com")
    _git(repo_root, "config", "user.name", "Test User")
    _git(repo_root, "add", ".")
    _git(repo_root, "commit", "-m", "Baseline fixture")

    _write_text(repo_root / "docs" / "covered_change.py", "print('baseline')\nprint('latest change')\n")
    _git(repo_root, "add", "docs/covered_change.py")
    _git(repo_root, "commit", "-m", "Covered change")


def _repo_root_convenience_paths(repo_root: Path) -> dict[str, Path]:
    return {
        "next_round_handoff": repo_root / "NEXT_ROUND_HANDOFF_LATEST.md",
        "expert_request": repo_root / "EXPERT_REQUEST_LATEST.md",
        "pm_ceo_research_brief": repo_root / "PM_CEO_RESEARCH_BRIEF_LATEST.md",
        "board_decision_brief": repo_root / "BOARD_DECISION_BRIEF_LATEST.md",
        "takeover": repo_root / "TAKEOVER_LATEST.md",
    }


def _fake_run_factory(
    calls: list[list[str]],
    *,
    closure_exit_code: int = 0,
    closure_result: str | None = None,
    dossier_exit_code: int = 0,
    dossier_stderr: str = "",
    next_round_handoff: dict[str, object] | None = None,
    expert_request: dict[str, object] | None = None,
    pm_ceo_research_brief: dict[str, object] | None = None,
    board_decision_brief: dict[str, object] | None = None,
    round_contract_observations: list[dict[str, object]] | None = None,
) -> callable:
    def _fake_run(
        command: list[str],
        cwd: str | None = None,
        capture_output: bool = True,
        text: bool = True,
        check: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        del cwd, capture_output, text, check
        calls.append(command)
        exit_code = 0
        stderr = ""
        if any("auditor_calibration_report.py" in token for token in command):
            if "--mode" in command:
                mode_index = command.index("--mode")
                mode = command[mode_index + 1] if mode_index + 1 < len(command) else ""
                if mode == "dossier":
                    exit_code = dossier_exit_code
                    stderr = dossier_stderr
        if any("build_exec_memory_packet.py" in token for token in command):
            if "--output-json" in command:
                output_index = command.index("--output-json")
                output_json = Path(command[output_index + 1])
                output_json.parent.mkdir(parents=True, exist_ok=True)
                output_payload: dict[str, object] = {
                    "schema_version": "1.0.0",
                    "generated_at_utc": "2026-03-07T00:00:00Z",
                }
                if next_round_handoff is not None:
                    output_payload["next_round_handoff"] = next_round_handoff
                if expert_request is not None:
                    output_payload["expert_request"] = expert_request
                if pm_ceo_research_brief is not None:
                    output_payload["pm_ceo_research_brief"] = pm_ceo_research_brief
                if board_decision_brief is not None:
                    output_payload["board_decision_brief"] = board_decision_brief
                output_json.write_text(
                    json.dumps(output_payload),
                    encoding="utf-8",
                )
            if "--output-md" in command:
                output_index = command.index("--output-md")
                output_md = Path(command[output_index + 1])
                output_md.parent.mkdir(parents=True, exist_ok=True)
                output_md.write_text("# Exec Memory Packet\n", encoding="utf-8")
        if any("validate_loop_closure.py" in token for token in command):
            exit_code = closure_exit_code
            if "--output-json" in command:
                output_index = command.index("--output-json")
                if output_index + 1 < len(command):
                    output_json = Path(command[output_index + 1])
                    output_json.parent.mkdir(parents=True, exist_ok=True)
                    output_json.write_text(
                        json.dumps({"result": closure_result or "READY"}),
                        encoding="utf-8",
                    )
        if any("validate_round_contract_checks.py" in token for token in command):
            observation: dict[str, object] = {}
            if "--loop-summary-json" in command:
                summary_index = command.index("--loop-summary-json")
                if summary_index + 1 < len(command):
                    loop_summary_path = Path(command[summary_index + 1])
                    observation["loop_summary_path"] = str(loop_summary_path)
                    observation["loop_summary"] = json.loads(
                        loop_summary_path.read_text(encoding="utf-8")
                    )
            if "--closure-json" in command:
                closure_index = command.index("--closure-json")
                if closure_index + 1 < len(command):
                    closure_json_path = Path(command[closure_index + 1])
                    observation["closure_json_path"] = str(closure_json_path)
                    observation["closure_exists"] = closure_json_path.exists()
                    if closure_json_path.exists():
                        observation["closure_payload"] = json.loads(
                            closure_json_path.read_text(encoding="utf-8")
                        )
            if round_contract_observations is not None:
                round_contract_observations.append(observation)
        return subprocess.CompletedProcess(command, exit_code, stdout="ok\n", stderr=stderr)

    return _fake_run


def test_run_loop_cycle_skip_phase_end_success_and_overdue_ledger_flag(
    tmp_path: Path, monkeypatch
) -> None:
    repo_root = tmp_path
    context = repo_root / "docs" / "context"
    scripts_dir = repo_root / "scripts"
    _prepare_scripts_dir(scripts_dir, include_weekly_truth=True)
    _write_text(context / "ceo_weekly_summary_latest.md", "# Weekly Summary\n")
    _write_text(context / "phase_end_logs" / ".keep", "")
    _write_text(
        context / "disagreement_ledger.jsonl",
        "\n".join(
            [
                json.dumps(
                    {
                        "round_id": "r1",
                        "task_id": "t1",
                        "code": "D03",
                        "severity": "HIGH",
                        "owner": "PM",
                        "due_utc": "2020-01-01T00:00:00Z",
                        "resolved": False,
                    }
                ),
                json.dumps(
                    {
                        "round_id": "r2",
                        "task_id": "t2",
                        "code": "D02",
                        "severity": "MEDIUM",
                        "owner": "Worker",
                        "due_utc": "2099-01-01T00:00:00Z",
                        "resolved": False,
                    }
                ),
            ]
        )
        + "\n",
    )

    calls: list[list[str]] = []
    round_contract_observations: list[dict[str, object]] = []
    monkeypatch.setattr(
        run_loop_cycle.subprocess,
        "run",
        _fake_run_factory(
            calls,
            closure_exit_code=0,
            round_contract_observations=round_contract_observations,
        ),
    )

    args = run_loop_cycle.parse_args(
        [
            "--repo-root",
            str(repo_root),
            "--scripts-dir",
            str(scripts_dir),
            "--skip-phase-end",
        ]
    )
    exit_code, payload, _ = run_loop_cycle.run_cycle(args)

    assert exit_code == 0
    assert payload["final_result"] == "PASS"
    assert payload["disagreement_ledger_sla"]["overdue_unresolved_count"] == 1

    step_names = [step["name"] for step in payload["steps"]]
    assert step_names == [
        "phase_end_handover",
        "refresh_weekly_calibration",
        "refresh_dossier",
        "generate_ceo_go_signal",
        "refresh_ceo_weekly_summary",
        "evaluate_context_compaction_trigger",
        "build_exec_memory_packet",
        "validate_ceo_go_signal_truth",
        "validate_ceo_weekly_summary_truth",
        "validate_exec_memory_truth",
        "validate_counterexample_gate",
        "validate_dual_judge_gate",
        "validate_refactor_mock_policy",
        "validate_review_checklist",
        "validate_interface_contracts",
        "validate_parallel_fanin",
        "validate_loop_closure",
        "validate_round_contract_checks",
    ]
    status_by_step = {step["name"]: step["status"] for step in payload["steps"]}
    assert status_by_step["phase_end_handover"] == "SKIP"
    assert status_by_step["validate_ceo_weekly_summary_truth"] == "PASS"
    assert status_by_step["validate_refactor_mock_policy"] == "PASS"
    assert status_by_step["validate_review_checklist"] == "SKIP"
    assert status_by_step["validate_interface_contracts"] == "SKIP"

    summary_json = context / "loop_cycle_summary_latest.json"
    summary_md = context / "loop_cycle_summary_latest.md"
    assert summary_json.exists()
    assert summary_md.exists()
    persisted = json.loads(summary_json.read_text(encoding="utf-8"))
    assert persisted["final_exit_code"] == 0
    assert persisted["disagreement_ledger_sla"]["overdue_unresolved_count"] == 1

    worker_lessons = context / "lessons_worker_latest.md"
    auditor_lessons = context / "lessons_auditor_latest.md"
    assert worker_lessons.exists()
    assert auditor_lessons.exists()
    assert "What delivery decision had the highest impact this cycle?" in worker_lessons.read_text(
        encoding="utf-8"
    )
    assert "Which gate caught the highest-risk issue this cycle?" in auditor_lessons.read_text(
        encoding="utf-8"
    )

    weekly_gen_command = next(
        command
        for command in calls
        if any("generate_ceo_weekly_summary.py" in token for token in command)
    )
    assert "--output" in weekly_gen_command

    weekly_truth_command = next(
        command
        for command in calls
        if any("validate_ceo_weekly_summary_truth.py" in token for token in command)
    )
    assert "--weekly-md" in weekly_truth_command
    assert "--weekly-summary-md" not in weekly_truth_command

    closure_command = next(
        command for command in calls if any("validate_loop_closure.py" in token for token in command)
    )
    round_contract_command = next(
        command
        for command in calls
        if any("validate_round_contract_checks.py" in token for token in command)
    )
    assert "--weekly-summary-md" in closure_command
    assert "--memory-json" in closure_command
    assert "--memory-truth-script" in closure_command
    assert "--refactor-mock-policy-script" in closure_command
    assert "--review-checklist-script" in closure_command
    assert "--interface-contracts-script" in closure_command
    assert calls.index(closure_command) < calls.index(round_contract_command)

    assert len(round_contract_observations) == 1
    temp_summary_payload = round_contract_observations[0]["loop_summary"]
    assert isinstance(temp_summary_payload, dict)
    assert temp_summary_payload["repo_root"] == str(repo_root)
    assert temp_summary_payload["context_dir"] == str(context)
    assert temp_summary_payload["artifacts"]["closure_output_json"] == str(
        context / "loop_closure_status_latest.json"
    )
    temp_step_names = [step["name"] for step in temp_summary_payload["steps"]]
    assert temp_step_names[-1] == "validate_loop_closure"
    assert "validate_round_contract_checks" not in temp_step_names
    assert temp_summary_payload["step_summary"]["total_steps"] == len(temp_step_names)
    assert temp_summary_payload["next_round_handoff"] is None
    assert temp_summary_payload["expert_request"] is None
    assert temp_summary_payload["pm_ceo_research_brief"] is None
    assert temp_summary_payload["board_decision_brief"] is None
    assert temp_summary_payload["repo_root_convenience"] == {}
    assert round_contract_observations[0]["closure_exists"] is True

    # 15 calls: weekly_calibration, dossier, go_signal, weekly_summary, compaction_trigger,
    # build_memory_packet, go_truth, weekly_truth, exec_memory_truth, counterexample_gate,
    # dual_judge_gate, refactor_mock_policy, parallel_fanin, closure, round_contract_checks
    assert len(calls) == 15

    temp_summary = context / "loop_cycle_summary_current.json"
    assert not temp_summary.exists(), "Temp summary should be cleaned up"


def test_run_loop_cycle_persists_next_round_handoff_artifacts(
    tmp_path: Path, monkeypatch
) -> None:
    repo_root = tmp_path
    context = repo_root / "docs" / "context"
    scripts_dir = repo_root / "scripts"
    _prepare_scripts_dir(scripts_dir, include_weekly_truth=True)
    _write_text(context / "ceo_weekly_summary_latest.md", "# Weekly Summary\n")
    _write_text(context / "phase_end_logs" / ".keep", "")

    calls: list[list[str]] = []
    monkeypatch.setattr(
        run_loop_cycle.subprocess,
        "run",
        _fake_run_factory(
            calls,
            closure_exit_code=0,
            next_round_handoff={
                "status": "ACTION_REQUIRED",
                "recommended_intent": "close remaining promotion blockers",
                "deliverable_this_scope": "refresh dossier and GO artifacts",
                "non_goals": "new architecture",
                "done_when": "blocking criteria reduced and artifacts refreshed",
                "done_when_checks": ["go_signal_action_gate", "freshness_gate"],
                "human_brief": "Close remaining promotion blockers by refreshing dossier and GO artifacts without adding new architecture.",
                "machine_view": "SURFACE: next_round_handoff\nSTATUS: ACTION_REQUIRED\nRECOMMENDED_INTENT: close remaining promotion blockers\nDELIVERABLE_THIS_SCOPE: refresh dossier and GO artifacts",
                "artifacts_to_refresh": [
                    "docs/context/auditor_promotion_dossier.json",
                    "docs/context/ceo_go_signal.md",
                ],
                "blocking_gap_codes": ["c3_min_weeks", "c4b_annotation_coverage"],
                "source_paths": [
                    "docs/context/auditor_promotion_dossier.json",
                    "docs/context/ceo_go_signal.md",
                ],
                "paste_ready_block": "ORIGINAL_INTENT: close remaining promotion blockers",
            },
            expert_request={
                "status": "ADVISORY",
                "target_expert": "qa",
                "trigger_reason": "Low confidence on remaining edge cases",
                "question": "Validate the ambiguous edge cases before escalation.",
                "requested_domain": "qa",
                "roster_fit": "APPROVED_MANDATORY",
                "milestone_id": "promotion-cutover",
                "board_reentry_required": "false",
                "board_reentry_reason_codes": ["none"],
                "expert_memory_status": "FRESH",
                "board_memory_status": "FRESH",
                "memory_reason_codes": ["none"],
                "human_brief": "Ask QA to resolve the remaining ambiguous edge cases before escalation.",
                "machine_view": "SURFACE: expert_request\nSTATUS: ADVISORY\nTARGET_EXPERT: qa\nREQUESTED_DOMAIN: qa\nROSTER_FIT: APPROVED_MANDATORY\nMILESTONE_ID: promotion-cutover\nBOARD_REENTRY_REQUIRED: false\nEXPERT_MEMORY_STATUS: FRESH\nBOARD_MEMORY_STATUS: FRESH\nQUESTION: Validate the ambiguous edge cases before escalation.",
                "source_artifacts": ["docs/context/exec_memory_packet_latest.json"],
                "paste_ready_block": "=== EXPERT REQUEST ===\nTargetExpert: qa",
            },
            pm_ceo_research_brief={
                "status": "ADVISORY",
                "delegated_to": "principal",
                "question": "What is the top tradeoff to resolve before promotion?",
                "human_brief": "Delegate principal-level tradeoff research on the top blocker before promotion.",
                "machine_view": "SURFACE: pm_ceo_research_brief\nSTATUS: ADVISORY\nDELEGATED_TO: principal\nQUESTION: What is the top tradeoff to resolve before promotion?",
                "required_tradeoff_dimensions": ["risk", "latency"],
                "evidence_required": ["docs/context/ceo_go_signal.md"],
                "paste_ready_block": "=== PM/CEO RESEARCH BRIEF ===\nDelegatedTo: principal",
            },
            board_decision_brief={
                "status": "ADVISORY",
                "decision_topic": "promotion readiness cutover",
                "recommended_option": "hold escalation until dossier evidence is refreshed",
                "lineup_decision_needed": "false",
                "lineup_gap_domains": ["none"],
                "approved_roster_snapshot": {
                    "mandatory": ["principal", "qa"],
                    "optional": ["riskops"],
                },
                "reintroduce_board_when": "when milestone scope changes",
                "board_reentry_required": "false",
                "board_reentry_reason_codes": ["none"],
                "expert_memory_status": "FRESH",
                "board_memory_status": "FRESH",
                "memory_reason_codes": ["none"],
                "human_brief": "Hold escalation until the dossier evidence is refreshed and final signoff is ready.",
                "machine_view": "SURFACE: board_decision_brief\nSTATUS: ADVISORY\nDECISION_TOPIC: promotion readiness cutover\nLINEUP_DECISION_NEEDED: false\nLINEUP_GAP_DOMAINS: none\nREINTRODUCE_BOARD_WHEN: when milestone scope changes\nBOARD_REENTRY_REQUIRED: false\nEXPERT_MEMORY_STATUS: FRESH\nBOARD_MEMORY_STATUS: FRESH\nRECOMMENDED_OPTION: hold escalation until dossier evidence is refreshed",
                "source_artifacts": [
                    "docs/context/auditor_promotion_dossier.json",
                    "docs/context/ceo_go_signal.md",
                ],
                "open_risks": ["stale evidence", "missing final signoff"],
                "paste_ready_block": "=== BOARD DECISION BRIEF ===\nDecisionTopic: promotion readiness cutover",
            },
        ),
    )

    args = run_loop_cycle.parse_args(
        [
            "--repo-root",
            str(repo_root),
            "--scripts-dir",
            str(scripts_dir),
            "--skip-phase-end",
        ]
    )
    exit_code, payload, markdown = run_loop_cycle.run_cycle(args)

    assert exit_code == 0
    assert payload["next_round_handoff"]["status"] == "ACTION_REQUIRED"

    handoff_json = context / "next_round_handoff_latest.json"
    handoff_md = context / "next_round_handoff_latest.md"
    expert_request_json = context / "expert_request_latest.json"
    expert_request_md = context / "expert_request_latest.md"
    pm_ceo_research_brief_json = context / "pm_ceo_research_brief_latest.json"
    pm_ceo_research_brief_md = context / "pm_ceo_research_brief_latest.md"
    board_decision_brief_json = context / "board_decision_brief_latest.json"
    board_decision_brief_md = context / "board_decision_brief_latest.md"
    root_convenience = _repo_root_convenience_paths(repo_root)
    assert handoff_json.exists()
    assert handoff_md.exists()
    assert expert_request_json.exists()
    assert expert_request_md.exists()
    assert pm_ceo_research_brief_json.exists()
    assert pm_ceo_research_brief_md.exists()
    assert board_decision_brief_json.exists()
    assert board_decision_brief_md.exists()
    assert root_convenience["next_round_handoff"].exists()
    assert root_convenience["expert_request"].exists()
    assert root_convenience["pm_ceo_research_brief"].exists()
    assert root_convenience["board_decision_brief"].exists()
    assert root_convenience["takeover"].exists()

    persisted = json.loads(handoff_json.read_text(encoding="utf-8"))
    assert persisted["next_round_handoff"]["recommended_intent"] == "close remaining promotion blockers"
    assert persisted["next_round_handoff"]["human_brief"].startswith("Close remaining promotion blockers")
    assert persisted["next_round_handoff"]["machine_view"].startswith("SURFACE: next_round_handoff")
    assert persisted["next_round_handoff"]["done_when_checks"] == [
        "go_signal_action_gate",
        "freshness_gate",
    ]

    expert_request_persisted = json.loads(expert_request_json.read_text(encoding="utf-8"))
    assert expert_request_persisted["expert_request"]["target_expert"] == "qa"
    assert expert_request_persisted["expert_request"]["human_brief"].startswith("Ask QA")

    research_brief_persisted = json.loads(pm_ceo_research_brief_json.read_text(encoding="utf-8"))
    assert research_brief_persisted["pm_ceo_research_brief"]["delegated_to"] == "principal"
    assert research_brief_persisted["pm_ceo_research_brief"]["machine_view"].startswith(
        "SURFACE: pm_ceo_research_brief"
    )

    board_brief_persisted = json.loads(board_decision_brief_json.read_text(encoding="utf-8"))
    assert board_brief_persisted["board_decision_brief"]["decision_topic"] == "promotion readiness cutover"
    assert (
        board_brief_persisted["board_decision_brief"]["recommended_option"]
        == "hold escalation until dossier evidence is refreshed"
    )
    assert board_brief_persisted["board_decision_brief"]["human_brief"].startswith(
        "Hold escalation until the dossier evidence"
    )

    handoff_markdown = handoff_md.read_text(encoding="utf-8")
    expert_request_markdown = expert_request_md.read_text(encoding="utf-8")
    research_brief_markdown = pm_ceo_research_brief_md.read_text(encoding="utf-8")
    board_brief_markdown = board_decision_brief_md.read_text(encoding="utf-8")
    assert "# Next Round Handoff" in handoff_markdown
    assert "## Human Brief" in handoff_markdown
    assert "## Machine View" in handoff_markdown
    assert "## Paste-Ready Block" in handoff_markdown
    assert "ORIGINAL_INTENT: close remaining promotion blockers" in handoff_markdown
    assert "# Expert Request" in expert_request_markdown
    assert "## Lineup" in expert_request_markdown
    assert "RequestedDomain: qa" in expert_request_markdown
    assert "## Memory" in expert_request_markdown
    assert "ExpertMemoryStatus: FRESH" in expert_request_markdown
    assert "## Human Brief" in expert_request_markdown
    assert "## Machine View" in expert_request_markdown
    assert "## Paste-Ready Block" in expert_request_markdown
    assert "TargetExpert: qa" in expert_request_markdown
    assert "# PM/CEO Research Brief" in research_brief_markdown
    assert "## Human Brief" in research_brief_markdown
    assert "## Machine View" in research_brief_markdown
    assert "## Paste-Ready Block" in research_brief_markdown
    assert "DelegatedTo: principal" in research_brief_markdown
    assert "# Board Decision Brief" in board_brief_markdown
    assert "## Lineup" in board_brief_markdown
    assert "LineupDecisionNeeded: false" in board_brief_markdown
    assert "## Memory" in board_brief_markdown
    assert "BoardMemoryStatus: FRESH" in board_brief_markdown
    assert "## Human Brief" in board_brief_markdown
    assert "## Machine View" in board_brief_markdown
    assert "## Paste-Ready Block" in board_brief_markdown
    assert "DecisionTopic: promotion readiness cutover" in board_brief_markdown
    assert root_convenience["next_round_handoff"].read_text(encoding="utf-8") == handoff_markdown
    assert root_convenience["expert_request"].read_text(encoding="utf-8") == expert_request_markdown
    assert root_convenience["pm_ceo_research_brief"].read_text(encoding="utf-8") == research_brief_markdown
    assert root_convenience["board_decision_brief"].read_text(encoding="utf-8") == board_brief_markdown
    takeover_markdown = root_convenience["takeover"].read_text(encoding="utf-8")
    assert "# Takeover Latest" in takeover_markdown
    assert "NEXT_ROUND_HANDOFF_LATEST.md" in takeover_markdown
    assert "docs" in takeover_markdown
    assert str(handoff_json) == payload["artifacts"]["next_round_handoff_json"]
    assert str(handoff_md) == payload["artifacts"]["next_round_handoff_md"]
    assert str(expert_request_json) == payload["artifacts"]["expert_request_json"]
    assert str(expert_request_md) == payload["artifacts"]["expert_request_md"]
    assert str(pm_ceo_research_brief_json) == payload["artifacts"]["pm_ceo_research_brief_json"]
    assert str(pm_ceo_research_brief_md) == payload["artifacts"]["pm_ceo_research_brief_md"]
    assert str(board_decision_brief_json) == payload["artifacts"]["board_decision_brief_json"]
    assert str(board_decision_brief_md) == payload["artifacts"]["board_decision_brief_md"]
    assert payload["expert_request"] == {
        "status": "ADVISORY",
        "json": str(expert_request_json),
        "md": str(expert_request_md),
        "target_expert": "qa",
    }
    assert payload["pm_ceo_research_brief"] == {
        "status": "ADVISORY",
        "json": str(pm_ceo_research_brief_json),
        "md": str(pm_ceo_research_brief_md),
        "delegated_to": "principal",
    }
    assert payload["board_decision_brief"] == {
        "status": "ADVISORY",
        "json": str(board_decision_brief_json),
        "md": str(board_decision_brief_md),
        "decision_topic": "promotion readiness cutover",
        "recommended_option": "hold escalation until dossier evidence is refreshed",
    }
    assert payload["repo_root_convenience"] == {
        "next_round_handoff": str(root_convenience["next_round_handoff"]),
        "expert_request": str(root_convenience["expert_request"]),
        "pm_ceo_research_brief": str(root_convenience["pm_ceo_research_brief"]),
        "board_decision_brief": str(root_convenience["board_decision_brief"]),
        "takeover": str(root_convenience["takeover"]),
    }
    assert "## Next Round Handoff" in markdown
    assert "## Expert Request" in markdown
    assert "## PM/CEO Research Brief" in markdown
    assert "## Board Decision Brief" in markdown


def test_run_loop_cycle_returns_nonzero_when_closure_fails(
    tmp_path: Path, monkeypatch
) -> None:
    repo_root = tmp_path
    context = repo_root / "docs" / "context"
    scripts_dir = repo_root / "scripts"
    _prepare_scripts_dir(scripts_dir, include_weekly_truth=False)
    _write_text(context / "phase_end_logs" / ".keep", "")

    calls: list[list[str]] = []
    monkeypatch.setattr(
        run_loop_cycle.subprocess,
        "run",
        _fake_run_factory(calls, closure_exit_code=1),
    )

    args = run_loop_cycle.parse_args(
        [
            "--repo-root",
            str(repo_root),
            "--scripts-dir",
            str(scripts_dir),
            "--skip-phase-end",
        ]
    )
    exit_code, payload, _ = run_loop_cycle.run_cycle(args)

    assert exit_code == 1
    assert payload["final_result"] == "FAIL"
    closure_step = next(step for step in payload["steps"] if step["name"] == "validate_loop_closure")
    assert closure_step["status"] == "FAIL"
    assert closure_step["exit_code"] == 1

    summary_json = context / "loop_cycle_summary_latest.json"
    persisted = json.loads(summary_json.read_text(encoding="utf-8"))
    root_convenience = _repo_root_convenience_paths(repo_root)
    assert persisted["final_exit_code"] == 1
    assert not (context / "expert_request_latest.json").exists()
    assert not (context / "expert_request_latest.md").exists()
    assert not (context / "pm_ceo_research_brief_latest.json").exists()
    assert not (context / "pm_ceo_research_brief_latest.md").exists()
    assert not (context / "board_decision_brief_latest.json").exists()
    assert not (context / "board_decision_brief_latest.md").exists()
    assert payload["repo_root_convenience"] == {}
    assert all(not path.exists() for path in root_convenience.values())


def test_run_loop_cycle_returns_hold_for_expected_dossier_shortfall_and_not_ready_closure(
    tmp_path: Path, monkeypatch
) -> None:
    repo_root = tmp_path
    context = repo_root / "docs" / "context"
    scripts_dir = repo_root / "scripts"
    _prepare_scripts_dir(scripts_dir, include_weekly_truth=False)
    _write_text(context / "phase_end_logs" / ".keep", "")

    calls: list[list[str]] = []
    monkeypatch.setattr(
        run_loop_cycle.subprocess,
        "run",
        _fake_run_factory(
            calls,
            dossier_exit_code=1,
            dossier_stderr=f"warning: {run_loop_cycle.DOSSIER_HOLD_MARKER}",
            closure_exit_code=1,
            closure_result="NOT_READY",
        ),
    )

    args = run_loop_cycle.parse_args(
        [
            "--repo-root",
            str(repo_root),
            "--scripts-dir",
            str(scripts_dir),
            "--skip-phase-end",
        ]
    )
    exit_code, payload, _ = run_loop_cycle.run_cycle(args)

    assert exit_code == 0
    assert payload["final_result"] == "HOLD"
    assert payload["step_summary"]["hold_count"] == 2
    assert payload["step_summary"]["fail_count"] == 0
    assert payload["step_summary"]["error_count"] == 0

    status_by_step = {step["name"]: step["status"] for step in payload["steps"]}
    assert status_by_step["refresh_dossier"] == "HOLD"
    assert status_by_step["validate_loop_closure"] == "HOLD"

    summary_json = context / "loop_cycle_summary_latest.json"
    persisted = json.loads(summary_json.read_text(encoding="utf-8"))
    assert persisted["final_result"] == "HOLD"
    assert persisted["final_exit_code"] == 0


def test_run_loop_cycle_disables_hold_when_allow_hold_is_false(
    tmp_path: Path, monkeypatch
) -> None:
    repo_root = tmp_path
    context = repo_root / "docs" / "context"
    scripts_dir = repo_root / "scripts"
    _prepare_scripts_dir(scripts_dir, include_weekly_truth=False)
    _write_text(context / "phase_end_logs" / ".keep", "")

    calls: list[list[str]] = []
    monkeypatch.setattr(
        run_loop_cycle.subprocess,
        "run",
        _fake_run_factory(
            calls,
            dossier_exit_code=1,
            dossier_stderr=f"warning: {run_loop_cycle.DOSSIER_HOLD_MARKER}",
            closure_exit_code=1,
            closure_result="NOT_READY",
        ),
    )

    args = run_loop_cycle.parse_args(
        [
            "--repo-root",
            str(repo_root),
            "--scripts-dir",
            str(scripts_dir),
            "--skip-phase-end",
            "--allow-hold",
            "false",
        ]
    )
    exit_code, payload, _ = run_loop_cycle.run_cycle(args)

    assert exit_code == 1
    assert payload["final_result"] == "FAIL"
    assert payload["step_summary"]["hold_count"] == 0
    assert payload["step_summary"]["fail_count"] == 2

    status_by_step = {step["name"]: step["status"] for step in payload["steps"]}
    assert status_by_step["refresh_dossier"] == "FAIL"
    assert status_by_step["validate_loop_closure"] == "FAIL"

    summary_json = context / "loop_cycle_summary_latest.json"
    persisted = json.loads(summary_json.read_text(encoding="utf-8"))
    assert persisted["final_result"] == "FAIL"
    assert persisted["final_exit_code"] == 1


def test_run_loop_cycle_with_phase_end_handover_execution(
    tmp_path: Path, monkeypatch
) -> None:
    """Test run_loop_cycle WITHOUT --skip-phase-end to verify phase_end_handover.ps1 executes."""
    repo_root = tmp_path
    context = repo_root / "docs" / "context"
    scripts_dir = repo_root / "scripts"
    _prepare_scripts_dir(scripts_dir, include_weekly_truth=False)
    _write_text(context / "phase_end_logs" / ".keep", "")

    # Create a mock phase_end_handover.ps1 that creates a marker file
    phase_end_marker = context / "phase_end_executed.marker"
    phase_end_script_content = f"""
param(
    [string]$RepoRoot = ".",
    [string]$LogsRelativeDir = "docs/context/phase_end_logs",
    [string]$AuditMode = "shadow"
)

$ErrorActionPreference = "Stop"

# Create marker file to prove execution
$markerPath = "{str(phase_end_marker).replace('\\', '/')}"
New-Item -ItemType Directory -Path (Split-Path $markerPath -Parent) -Force | Out-Null
Set-Content -Path $markerPath -Value "phase_end_handover executed" -Encoding UTF8

# Create required output files
$logsDir = Join-Path $RepoRoot $LogsRelativeDir
New-Item -ItemType Directory -Path $logsDir -Force | Out-Null

$runId = Get-Date -Format "yyyyMMdd_HHmmss"
$statusPath = Join-Path $logsDir "phase_end_handover_status_$runId.json"
$summaryPath = Join-Path $logsDir "phase_end_handover_summary_$runId.md"

$status = @{{
    schema_version = "1.0.0"
    run_id = $runId
    result = "PASS"
    failed_gate = ""
    gates = @()
}} | ConvertTo-Json -Depth 10

Set-Content -Path $statusPath -Value $status -Encoding UTF8
Set-Content -Path $summaryPath -Value "# Phase-End Summary`nResult: PASS" -Encoding UTF8

Write-Host "Phase-end handover completed successfully"
exit 0
"""
    _write_text(scripts_dir / "phase_end_handover.ps1", phase_end_script_content)

    calls: list[list[str]] = []
    original_run = subprocess.run

    def _selective_fake_run(
        command: list[str],
        cwd: str | None = None,
        capture_output: bool = True,
        text: bool = True,
        check: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        # Allow PowerShell scripts to execute normally
        if any("powershell" in str(token).lower() for token in command):
            return original_run(command, cwd=cwd, capture_output=capture_output, text=text, check=check)
        # Mock Python scripts
        return _fake_run_factory(calls, closure_exit_code=0)(command, cwd, capture_output, text, check)

    monkeypatch.setattr(run_loop_cycle.subprocess, "run", _selective_fake_run)

    # Run WITHOUT --skip-phase-end
    args = run_loop_cycle.parse_args(
        [
            "--repo-root",
            str(repo_root),
            "--scripts-dir",
            str(scripts_dir),
            # NOTE: --skip-phase-end is NOT included here
        ]
    )
    exit_code, payload, _ = run_loop_cycle.run_cycle(args)

    # Verify the cycle completed
    assert exit_code == 0, f"Expected success, got exit code {exit_code}"

    # Verify phase_end_handover step was executed (not skipped)
    phase_end_step = next(
        (step for step in payload["steps"] if step["name"] == "phase_end_handover"),
        None,
    )
    assert phase_end_step is not None, "phase_end_handover step not found"
    assert phase_end_step["status"] != "SKIP", "phase_end_handover should not be skipped"

    # Verify the PowerShell script actually executed by checking the marker file
    assert phase_end_marker.exists(), "phase_end_handover.ps1 did not execute (marker file not created)"
    marker_content = phase_end_marker.read_text(encoding="utf-8")
    assert "phase_end_handover executed" in marker_content, "Marker file has unexpected content"

    # Verify phase_end output files were created
    logs_dir = context / "phase_end_logs"
    status_files = list(logs_dir.glob("phase_end_handover_status_*.json"))
    assert len(status_files) > 0, "phase_end_handover status file not created"

    summary_files = list(logs_dir.glob("phase_end_handover_summary_*.md"))
    assert len(summary_files) > 0, "phase_end_handover summary file not created"


@pytest.mark.skipif(not POWERSHELL_EXE.exists(), reason="PowerShell not available")
def test_run_loop_cycle_with_real_phase_end_handover_contract(
    tmp_path: Path, monkeypatch
) -> None:
    """Exercise the real phase_end_handover.ps1 contract through run_loop_cycle."""
    repo_root = tmp_path
    context = repo_root / "docs" / "context"
    scripts_dir = repo_root / "scripts"
    _prepare_real_phase_end_repo(repo_root)

    calls: list[list[str]] = []
    original_run = subprocess.run
    fake_run = _fake_run_factory(calls, closure_exit_code=0)

    def _selective_fake_run(
        command: list[str],
        cwd: str | None = None,
        capture_output: bool = True,
        text: bool = True,
        check: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        if any("powershell" in str(token).lower() for token in command):
            return original_run(
                command,
                cwd=cwd,
                capture_output=capture_output,
                text=text,
                check=check,
            )
        return fake_run(command, cwd, capture_output, text, check)

    monkeypatch.setattr(run_loop_cycle.subprocess, "run", _selective_fake_run)

    args = run_loop_cycle.parse_args(
        [
            "--repo-root",
            str(repo_root),
            "--scripts-dir",
            str(scripts_dir),
            "--phase-end-audit-mode",
            "none",
        ]
    )
    exit_code, payload, _ = run_loop_cycle.run_cycle(args)

    assert exit_code == 0
    assert payload["final_result"] == "PASS"

    phase_end_step = next(
        step for step in payload["steps"] if step["name"] == "phase_end_handover"
    )
    assert phase_end_step["status"] == "PASS"
    assert any("powershell" in str(token).lower() for token in phase_end_step["command"])

    logs_dir = context / "phase_end_logs"
    status_files = sorted(logs_dir.glob("phase_end_handover_status_*.json"))
    summary_files = sorted(logs_dir.glob("phase_end_handover_summary_*.md"))
    assert len(status_files) == 1, "Expected one phase_end_handover status artifact"
    assert len(summary_files) == 1, "Expected one phase_end_handover summary artifact"

    status_data = json.loads(status_files[0].read_text(encoding="utf-8-sig"))
    assert status_data["result"] == "PASS"
    assert status_data["failed_gate"] == ""

    gate_results = {gate["gate"]: gate for gate in status_data["gates"]}
    required_pass_gates = [
        "G06_worker_reply_gate",
        "G07_orphan_change_gate",
        "G08_dispatch_lifecycle_gate",
        "G09_build_ceo_digest",
        "G10_digest_freshness_gate",
    ]
    for gate_name in required_pass_gates:
        assert gate_name in gate_results, f"Missing gate result for {gate_name}"
        assert gate_results[gate_name]["status"] == "PASS", gate_results[gate_name]

    gate_order = [gate["gate"] for gate in status_data["gates"]]
    assert gate_order.index("G09_build_ceo_digest") < gate_order.index(
        "G10_digest_freshness_gate"
    )

    digest_path = context / "ceo_bridge_digest.md"
    assert digest_path.exists(), "CEO bridge digest was not produced by the real phase-end lane"
    digest_text = digest_path.read_text(encoding="utf-8")
    assert "Generated:" in digest_text
    assert "TASK-001" in digest_text

    summary_text = summary_files[0].read_text(encoding="utf-8")
    assert "Result: PASS" in summary_text
    assert "G06_worker_reply_gate" in summary_text
