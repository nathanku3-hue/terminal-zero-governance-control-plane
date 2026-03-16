from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "evaluate_context_compaction_trigger.py"
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_go_signal(path: Path, action: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "# CEO GO Signal",
                "",
                f"- Recommended Action: {action}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _base_memory(pm_actual: int, pm_budget: int, ceo_actual: int, ceo_budget: int) -> dict:
    return {
        "schema_version": "1.0.0",
        "token_budget": {
            "pm_actual": pm_actual,
            "pm_budget": pm_budget,
            "ceo_actual": ceo_actual,
            "ceo_budget": ceo_budget,
        },
        "next_round_handoff": {"status": "ACTION_REQUIRED"},
        "expert_request": {"status": "ADVISORY"},
        "pm_ceo_research_brief": {"status": "ADVISORY"},
        "board_decision_brief": {"status": "ADVISORY"},
        "replanning": {"status": "BLOCKED"},
        "automation_uncertainty_status": {"status": "REVIEW"},
    }


def _base_dossier(c0=True, c1=None, c2=True, c3=True, c4=True, c4b=True, c5=True) -> dict:
    return {
        "schema_version": "1.0.0",
        "promotion_criteria": {
            "c0_infra_health": {"met": c0, "value": "0 failures"},
            "c1_24b_close": {
                "met": True if c1 is None else c1,
                "value": "APPROVED" if c1 in (None, True) else "MANUAL_CHECK",
            },
            "c2_min_items": {"met": c2, "value": "30 >= 30"},
            "c3_min_weeks": {"met": c3, "value": "2 consecutive weeks >= 2"},
            "c4_fp_rate": {"met": c4, "value": "0.00%"},
            "c4b_annotation_coverage": {"met": c4b, "value": "100.00%"},
            "c5_all_v2": {"met": c5, "value": "All v2.0.0"},
        },
    }


def _run(tmp_path: Path, *, extra: list[str] | None = None) -> subprocess.CompletedProcess[str]:
    memory_path = tmp_path / "memory.json"
    dossier_path = tmp_path / "dossier.json"
    go_signal_path = tmp_path / "go_signal.md"
    state_path = tmp_path / "state.json"
    output_path = tmp_path / "status.json"

    command = [
        sys.executable,
        str(SCRIPT_PATH),
        "--memory-json",
        str(memory_path),
        "--dossier-json",
        str(dossier_path),
        "--go-signal-md",
        str(go_signal_path),
        "--state-json",
        str(state_path),
        "--output-json",
        str(output_path),
    ]
    if extra:
        command.extend(extra)
    return subprocess.run(command, capture_output=True, text=True, check=False)


def test_trigger_on_warn_threshold(tmp_path: Path) -> None:
    _write_json(tmp_path / "memory.json", _base_memory(76, 100, 30, 100))
    _write_json(tmp_path / "dossier.json", _base_dossier())
    _write_go_signal(tmp_path / "go_signal.md", "HOLD")

    result = _run(tmp_path)

    assert result.returncode == 0
    payload = json.loads((tmp_path / "status.json").read_text(encoding="utf-8"))
    assert payload["should_compact"] is True
    assert payload["can_compact"] is True
    assert payload["decision_mode"] == "recommend_compact"
    assert "warn_threshold_exceeded" in payload["reasons"]
    assert payload["guardrail_violations"] == []
    assert payload["ratios"]["pm_ratio"] == 0.76


def test_trigger_on_action_change(tmp_path: Path) -> None:
    _write_json(tmp_path / "memory.json", _base_memory(10, 100, 10, 100))
    _write_json(tmp_path / "dossier.json", _base_dossier())
    _write_go_signal(tmp_path / "go_signal.md", "GO")
    _write_json(
        tmp_path / "state.json",
        {
            "schema_version": "1.0.0",
            "updated_at_utc": "2026-03-07T00:00:00Z",
            "action_current": "HOLD",
            "criteria_current": {
                "C0": True,
                "C1": True,
                "C2": True,
                "C3": True,
                "C4": True,
                "C4b": True,
                "C5": True,
            },
        },
    )

    result = _run(tmp_path)

    assert result.returncode == 0
    payload = json.loads((tmp_path / "status.json").read_text(encoding="utf-8"))
    assert payload["should_compact"] is True
    assert payload["can_compact"] is True
    assert payload["decision_mode"] == "recommend_compact"
    assert "recommended_action_changed" in payload["reasons"]
    assert payload["guardrail_violations"] == []
    assert payload["action_previous"] == "HOLD"
    assert payload["action_current"] == "GO"


def test_no_trigger_baseline(tmp_path: Path) -> None:
    _write_json(tmp_path / "memory.json", _base_memory(10, 100, 10, 100))
    _write_json(tmp_path / "dossier.json", _base_dossier())
    _write_go_signal(tmp_path / "go_signal.md", "HOLD")
    _write_json(
        tmp_path / "state.json",
        {
            "schema_version": "1.0.0",
            "updated_at_utc": "2026-03-07T00:00:00Z",
            "action_current": "HOLD",
            "criteria_current": {
                "C0": True,
                "C1": True,
                "C2": True,
                "C3": True,
                "C4": True,
                "C4b": True,
                "C5": True,
            },
            "last_compacted_at_utc": "2099-01-01T00:00:00Z",
        },
    )

    result = _run(tmp_path, extra=["--max-age-hours", "999999"])

    assert result.returncode == 0
    payload = json.loads((tmp_path / "status.json").read_text(encoding="utf-8"))
    assert payload["should_compact"] is False
    assert payload["can_compact"] is False
    assert payload["decision_mode"] == "no_action"
    assert payload["reasons"] == []
    assert payload["guardrail_violations"] == []
    assert payload["state_updated"] is True


def test_trigger_emits_shared_memory_tier_contract(tmp_path: Path) -> None:
    _write_json(tmp_path / "memory.json", _base_memory(10, 100, 10, 100))
    _write_json(tmp_path / "dossier.json", _base_dossier())
    _write_go_signal(tmp_path / "go_signal.md", "HOLD")

    result = _run(tmp_path)

    assert result.returncode == 0
    payload = json.loads((tmp_path / "status.json").read_text(encoding="utf-8"))
    contract = payload["memory_tier_contract"]
    bindings = payload["memory_tier_bindings"]

    assert contract["source_of_truth"] == "scripts/utils/memory_tiers.py"
    assert contract["documentation"] == "docs/memory_tier_contract.md"

    families = {item["family"]: item for item in contract["families"]}
    assert families["exec_memory_packet"]["tier"] == "hot"
    assert families["auditor_promotion_dossier"]["tier"] == "warm"
    assert families["context_compaction_state"]["tier"] == "hot"
    assert families["context_compaction_status"]["tier"] == "hot"

    cold = {item["family"]: item for item in contract["cold_manual_fallbacks"]}
    assert cold["auditor_fp_ledger"]["tier"] == "cold"
    assert cold["auditor_fp_ledger"]["access"] == "manual_fallback"

    input_bindings = {item["family"]: item for item in bindings["inputs"]}
    output_bindings = {item["family"]: item for item in bindings["outputs"]}
    assert input_bindings["exec_memory_packet"]["path"] == str(tmp_path / "memory.json")
    assert input_bindings["exec_memory_packet"]["tier"] == "hot"
    assert input_bindings["ceo_go_signal"]["tier"] == "warm"
    assert output_bindings["context_compaction_status"]["path"] == str(tmp_path / "status.json")
    assert output_bindings["context_compaction_status"]["tier"] == "hot"

    policy = payload["policy_snapshot"]
    plan = payload["retention_plan"]
    assert policy["source_of_truth"] == "scripts/utils/compaction_retention.py"
    assert policy["documentation"] == "docs/compaction_behavior_contract.md"
    assert [row["packet_section"] for row in plan["required_always"]] == [
        "next_round_handoff",
        "expert_request",
        "pm_ceo_research_brief",
        "board_decision_brief",
    ]
    assert plan["required_always"][0]["status"] == "retained"
    assert payload["guardrail_violations"] == []


def test_trigger_blocks_when_required_retention_surface_missing(tmp_path: Path) -> None:
    memory = _base_memory(76, 100, 10, 100)
    del memory["board_decision_brief"]
    _write_json(tmp_path / "memory.json", memory)
    _write_json(tmp_path / "dossier.json", _base_dossier())
    _write_go_signal(tmp_path / "go_signal.md", "HOLD")

    result = _run(tmp_path)

    assert result.returncode == 0
    payload = json.loads((tmp_path / "status.json").read_text(encoding="utf-8"))
    assert payload["should_compact"] is True
    assert payload["can_compact"] is False
    assert payload["decision_mode"] == "blocked_guardrail"
    assert "warn_threshold_exceeded" in payload["reasons"]
    assert "missing_required_surface:board_decision_brief" in payload["guardrail_violations"]
