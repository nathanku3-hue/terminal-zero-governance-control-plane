"""Phase 4 -- LoopOrchestrator with Bridge/Planner/State writers.
Phase 3 -- RollbackManager, Production Validation, Distributed Coordination.
D-183: scripts/orchestrator.py must be byte-identical to this file.
"""
from __future__ import annotations
import json, os, tempfile, statistics, sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_iso(ts: datetime) -> str:
    return ts.strftime("%Y-%m-%dT%H:%M:%SZ")


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tmp_", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as h:
            h.write(content)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass
        raise


def _atomic_write_json(path: Path, data: Any) -> None:
    _atomic_write_text(path, json.dumps(data, indent=2) + "\n")


try:
    from rollback_manager import RollbackManager
except ModuleNotFoundError:
    try:
        from scripts.rollback_manager import RollbackManager  # type: ignore[no-redef]
    except ModuleNotFoundError:
        from sop.scripts.rollback_manager import RollbackManager  # type: ignore[no-redef]

try:
    from tier_aware_compactor import TierAwareCompactor
except ModuleNotFoundError:
    try:
        from scripts.tier_aware_compactor import TierAwareCompactor  # type: ignore[no-redef]
    except ModuleNotFoundError:
        from sop.scripts.tier_aware_compactor import TierAwareCompactor  # type: ignore[no-redef]

try:
    from artifact_lifecycle_manager import ArtifactLifecycleManager, check_context_overflow
except ModuleNotFoundError:
    try:
        from scripts.artifact_lifecycle_manager import ArtifactLifecycleManager, check_context_overflow  # type: ignore[no-redef]
    except ModuleNotFoundError:
        from sop.scripts.artifact_lifecycle_manager import ArtifactLifecycleManager, check_context_overflow  # type: ignore[no-redef]

try:
    from utils.memory_tiers import _MEMORY_TIER_FAMILIES
except ModuleNotFoundError:
    try:
        from scripts.utils.memory_tiers import _MEMORY_TIER_FAMILIES  # type: ignore[no-redef]
    except ModuleNotFoundError:
        try:
            from sop.scripts.utils.memory_tiers import _MEMORY_TIER_FAMILIES  # type: ignore[no-redef]
        except ModuleNotFoundError:
            _MEMORY_TIER_FAMILIES = {}  # type: ignore[assignment]

try:
    from bridge_contract_writer import BridgeContractWriter
except ModuleNotFoundError:
    try:
        from scripts.bridge_contract_writer import BridgeContractWriter  # type: ignore[no-redef]
    except ModuleNotFoundError:
        from sop.scripts.bridge_contract_writer import BridgeContractWriter  # type: ignore[no-redef]

try:
    from planner_packet_writer import PlannerPacketWriter
except ModuleNotFoundError:
    try:
        from scripts.planner_packet_writer import PlannerPacketWriter  # type: ignore[no-redef]
    except ModuleNotFoundError:
        from sop.scripts.planner_packet_writer import PlannerPacketWriter  # type: ignore[no-redef]

try:
    from orchestrator_state_writer import OrchestratorStateWriter, _load_orchestrator_state
except ModuleNotFoundError:
    try:
        from scripts.orchestrator_state_writer import OrchestratorStateWriter, _load_orchestrator_state  # type: ignore[no-redef]
    except ModuleNotFoundError:
        from sop.scripts.orchestrator_state_writer import OrchestratorStateWriter, _load_orchestrator_state  # type: ignore[no-redef]

try:
    from utils.compaction_retention import _compact_ndjson_rolling
except ModuleNotFoundError:
    try:
        from scripts.utils.compaction_retention import _compact_ndjson_rolling  # type: ignore[no-redef]
    except ModuleNotFoundError:
        try:
            from sop.scripts.utils.compaction_retention import _compact_ndjson_rolling  # type: ignore[no-redef]
        except ModuleNotFoundError:
            def _compact_ndjson_rolling(path: Any, max_records: int = 500) -> None:  # type: ignore[misc]
                pass


def _load_json_or_empty(path: Path) -> dict:
    """Return parsed JSON dict from path, or {} if file missing or unreadable."""
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError:
        return {}
    except Exception:
        return {}


class LoopOrchestrator:
    """Coordinates one loop cycle run. Phase 3 adds rollback (3.1), production
    validation (3.2), and distributed coordination (3.3)."""

    def __init__(self, ctx: Any, runtime: Any, helpers: dict[str, Any]) -> None:
        self.ctx = ctx
        self.runtime = runtime
        self._h = helpers
        # Phase 4.3: load prior orchestrator state for continuity
        self._prior_state: dict | None = _load_orchestrator_state(ctx.context_dir)

    # ------------------------------------------------------------------
    # Phase 3.1 -- run_single() with RollbackManager lifecycle
    # ------------------------------------------------------------------

    def run_single(self) -> int:
        """Execute one loop cycle with rollback protection.
        0=PASS, 1=HOLD, 2=write-error, 5=rollback.

        Phase 4 wiring order (CC-G3):
          1. _execute_loop_body()
          2. BridgeContractWriter.write()   -- outside rollback scope, always written
          3. PlannerPacketWriter.write()    -- outside rollback scope, always written
          4. OrchestratorStateWriter.write()-- outside rollback scope, always written
          5. rm.revert() or rm.cleanup()
          6. return exit_code (or 5 on rollback)
        """
        ctx = self.ctx
        schema_dir = ctx.context_dir.parent.parent / "src" / "sop" / "schemas"
        if not schema_dir.exists():
            # Fallback: look for schemas adjacent to script
            schema_dir = Path(__file__).resolve().parent.parent / "schemas"

        rm = RollbackManager(ctx.context_dir)
        rm.snapshot()
        try:
            exit_code = self._execute_loop_body()

            # --- Phase 4 writers (outside rollback scope; survive HOLD) ---
            trace = _load_json_or_empty(ctx.context_dir / "loop_run_trace_latest.json")
            gate_a = _load_json_or_empty(ctx.context_dir / "phase_gate_a_latest.json")
            gate_b = _load_json_or_empty(ctx.context_dir / "phase_gate_b_latest.json")
            drift = _load_json_or_empty(ctx.context_dir / "run_drift_latest.json")

            # 4.1 Bridge Contract
            try:
                bridge_json_path = BridgeContractWriter(ctx.context_dir, schema_dir).write(
                    trace=trace, gate_a=gate_a, gate_b=gate_b, drift=drift
                )
                bridge_dict = _load_json_or_empty(bridge_json_path)
            except Exception as exc:
                print(f"BridgeContractWriter failed: {exc}", file=sys.stderr)
                bridge_dict = {}

            # 4.2 Planner Packet
            prior_packet_path = ctx.context_dir / "planner_packet_current.json"
            prior_packet = _load_json_or_empty(prior_packet_path) or None
            try:
                planner_json_path = PlannerPacketWriter(ctx.context_dir, schema_dir).write(
                    trace=trace, bridge=bridge_dict, gate_a=gate_a, gate_b=gate_b,
                    prior_packet=prior_packet,
                )
                planner_dict = _load_json_or_empty(planner_json_path)
            except Exception as exc:
                print(f"PlannerPacketWriter failed: {exc}", file=sys.stderr)
                planner_dict = {}

            # 4.3 Orchestrator State
            try:
                OrchestratorStateWriter(ctx.context_dir, schema_dir).write(
                    trace=trace, bridge=bridge_dict, planner_packet=planner_dict,
                    prior_state=self._prior_state,
                )
            except Exception as exc:
                print(f"OrchestratorStateWriter failed: {exc}", file=sys.stderr)

            # --- Phase 5.2: TierAwareCompactor (last op before return) ---
            try:
                _prune = getattr(ctx, 'prune', False)
                _max_ctx = getattr(ctx, 'max_context_artifacts', 50)
                TierAwareCompactor(
                    context_dir=ctx.context_dir,
                    tier_contract=_MEMORY_TIER_FAMILIES,
                    blocked=(exit_code == 1),
                ).run()
                # Phase 5.3: ArtifactLifecycleManager
                _mgr = ArtifactLifecycleManager(ctx.context_dir, _MEMORY_TIER_FAMILIES)
                _mgr.archive_superseded(dry_run=not _prune)
                check_context_overflow(ctx.context_dir, max_artifacts=_max_ctx)
            except Exception as _exc:
                print(f"CompactionLifecycle error (non-fatal): {_exc}", file=sys.stderr)

            # --- Rollback/cleanup (after writers) ---
            if exit_code == 1:  # HOLD
                rm.revert(self.runtime.trace_id, trigger="gate_hold")
                return 5
            rm.cleanup()
            return exit_code
        except Exception:
            rm.revert(self.runtime.trace_id, trigger="exception")
            raise

    def _execute_loop_body(self) -> int:
        """Derive exit code from current runtime steps."""
        error_count = sum(1 for s in self.runtime.steps if s["status"] == "ERROR")
        hold_count = sum(1 for s in self.runtime.steps if s["status"] == "HOLD")
        if error_count > 0:
            return 2
        if hold_count > 0:
            return 1
        return 0

    # ------------------------------------------------------------------
    # Phase 3.2 -- baseline append and drift detection
    # ------------------------------------------------------------------

    def append_baseline_record(self, final_result: str) -> None:
        """Append compact record to run_regression_baseline.ndjson on PROCEED (capped at 100)."""
        if final_result != "PASS":
            return
        durations = [
            s["duration_seconds"]
            for s in self.runtime.steps
            if isinstance(s.get("duration_seconds"), (int, float))
        ]
        durations_sorted = sorted(durations)
        n = len(durations_sorted)
        if n == 0:
            p50, p95 = 0.0, 0.0
        elif n == 1:
            p50 = p95 = float(durations_sorted[0])
        else:
            p50 = statistics.median(durations_sorted)
            p95_idx = max(0, int(n * 0.95) - 1)
            p95 = float(durations_sorted[p95_idx])
        record = {
            "trace_id": self.runtime.trace_id,
            "run_at_utc": self.runtime.generated_at_utc,
            "final_result": final_result,
            "step_count": len(self.runtime.steps),
            "pass_count": sum(1 for s in self.runtime.steps if s["status"] == "PASS"),
            "error_count": sum(1 for s in self.runtime.steps if s["status"] == "ERROR"),
            "p50_duration_s": round(p50, 3),
            "p95_duration_s": round(p95, 3),
        }
        baseline_path = self.ctx.context_dir / "run_regression_baseline.ndjson"
        try:
            baseline_path.parent.mkdir(parents=True, exist_ok=True)
            with baseline_path.open("a", encoding="utf-8", newline="\n") as fh:
                fh.write(json.dumps(record, separators=(",", ":")) + "\n")
            _compact_ndjson_rolling(baseline_path, max_records=100)
        except Exception:
            pass

    def run_drift_check(self) -> None:
        """Compare current run against baseline; emit run_drift_latest.json.
        Alerts suppressed if <5 baseline records."""
        baseline_path = self.ctx.context_dir / "run_regression_baseline.ndjson"
        drift_path = self.ctx.context_dir / "run_drift_latest.json"
        alerts: list[dict[str, str]] = []
        records: list[dict[str, Any]] = []
        if baseline_path.exists():
            try:
                for line in baseline_path.read_text(encoding="utf-8").splitlines():
                    stripped = line.strip()
                    if stripped:
                        records.append(json.loads(stripped))
            except Exception:
                pass
        baseline_count = len(records)
        if baseline_count >= 5:
            last5 = records[-5:]
            error_counts = [r.get("error_count", 0) for r in last5]
            current_errors = sum(1 for s in self.runtime.steps if s.get("status") == "ERROR")
            if all(e == 0 for e in error_counts) and current_errors > 0:
                msg = f"error_count increased from 0 in last 5 runs to {current_errors}"
                alerts.append({"alert_type": "DRIFT_ALERT", "message": msg})
                print(f"DRIFT_ALERT: {msg}", file=sys.stderr)
            recent10 = records[-10:]
            p95_values = [
                r["p95_duration_s"]
                for r in recent10
                if isinstance(r.get("p95_duration_s"), (int, float))
            ]
            if p95_values:
                avg_p95 = sum(p95_values) / len(p95_values)
                durations = [
                    s["duration_seconds"]
                    for s in self.runtime.steps
                    if isinstance(s.get("duration_seconds"), (int, float))
                ]
                if durations:
                    nd = len(durations)
                    p95_idx = max(0, int(nd * 0.95) - 1)
                    current_p95 = sorted(durations)[p95_idx]
                    if avg_p95 > 0 and current_p95 > avg_p95 * 1.5:
                        msg = (
                            f"p95_duration_s {current_p95:.1f}s exceeds "
                            f"trailing 10-run avg {avg_p95:.1f}s by >50%"
                        )
                        alerts.append({"alert_type": "PERF_REGRESSION", "message": msg})
                        print(f"PERF_REGRESSION: {msg}", file=sys.stderr)
        payload: dict[str, Any] = {
            "schema_version": "1.0",
            "trace_id": self.runtime.trace_id,
            "generated_at_utc": _utc_iso(_utc_now()),
            "baseline_record_count": baseline_count,
            "alerts": alerts,
        }
        try:
            _atomic_write_json(drift_path, payload)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Phase 3.3 -- run_parallel() with quorum and conflict detection
    # ------------------------------------------------------------------

    def run_parallel(
        self,
        worker_fn: Any,
        n: int,
        *,
        quorum: str = "all",
        timeout_seconds: float = 600.0,
    ) -> int:
        """Run n parallel workers with quorum policy.
        0=PASS, 1=HOLD, 2=write-error, 3=conflict, 4=timeout, 5=rollback."""
        import concurrent.futures as _cf
        trace_id = self.runtime.trace_id
        master_trace_id = f"master-{trace_id}"
        worker_results: list[dict[str, Any]] = []
        timed_out = False

        with _cf.ThreadPoolExecutor(max_workers=n) as executor:
            futures: dict[_cf.Future[Any], int] = {
                executor.submit(worker_fn, i): i for i in range(n)
            }
            done, not_done = _cf.wait(list(futures.keys()), timeout=timeout_seconds)
            if not_done:
                timed_out = True
                for f in not_done:
                    f.cancel()

        for fut, worker_id in futures.items():
            if fut.cancelled() or not fut.done():
                worker_results.append({
                    "worker_id": worker_id,
                    "trace_id": f"{trace_id}-w{worker_id}",
                    "final_result": "TIMEOUT",
                })
            else:
                try:
                    res = fut.result()
                    worker_results.append({
                        "worker_id": worker_id,
                        "trace_id": f"{trace_id}-w{worker_id}",
                        "final_result": str(res),
                    })
                except Exception as exc:
                    worker_results.append({
                        "worker_id": worker_id,
                        "trace_id": f"{trace_id}-w{worker_id}",
                        "final_result": "ERROR",
                        "error": str(exc),
                    })

        results_list = [r["final_result"] for r in worker_results]
        conflicts: list[dict[str, Any]] = []
        aggregate_result, exit_code = self._apply_quorum(
            results_list, quorum, n, conflicts
        )
        if timed_out:
            aggregate_result = "TIMEOUT"
            exit_code = 4

        merge_payload: dict[str, Any] = {
            "schema_version": "1.0",
            "trace_id": master_trace_id,
            "triggered_at_utc": _utc_iso(_utc_now()),
            "quorum_policy": quorum,
            "worker_count": n,
            "workers": worker_results,
            "conflicts": conflicts,
            "aggregate_result": aggregate_result,
        }
        try:
            _atomic_write_json(
                self.ctx.context_dir / "worker_merge_latest.json", merge_payload
            )
        except Exception:
            return 2

        master_payload: dict[str, Any] = {
            "schema_version": "1.0",
            "trace_id": master_trace_id,
            "worker_count": n,
            "quorum_policy": quorum,
            "workers": worker_results,
            "aggregate_result": aggregate_result,
            "conflicts": conflicts,
        }
        try:
            _atomic_write_json(
                self.ctx.context_dir / "loop_run_trace_master_latest.json",
                master_payload,
            )
        except Exception:
            return 2

        return exit_code

    def _apply_quorum(
        self,
        results: list[str],
        quorum: str,
        n: int,
        conflicts: list[dict[str, Any]],
    ) -> tuple[str, int]:
        """Apply quorum policy; populate conflicts; return (aggregate_result, exit_code)."""
        pass_count = sum(1 for r in results if r == "PASS")
        unique = set(results)
        if quorum == "all":
            if unique == {"PASS"}:
                return "PASS", 0
            if len(unique) > 1:
                for i in range(len(results)):
                    for j in range(i + 1, len(results)):
                        if results[i] != results[j]:
                            conflicts.append({
                                "worker_ids": [i, j],
                                "field": "final_result",
                                "values": [results[i], results[j]],
                            })
                return "CONFLICT", 3
            return (results[0] if results else "HOLD"), 1
        elif quorum == "majority":
            threshold = n / 2  # strict majority: > n/2
            if pass_count > threshold:
                return "PASS", 0
            if len(unique) > 1:
                for i in range(len(results)):
                    for j in range(i + 1, len(results)):
                        if results[i] != results[j]:
                            conflicts.append({
                                "worker_ids": [i, j],
                                "field": "final_result",
                                "values": [results[i], results[j]],
                            })
                return "CONFLICT", 3
            return "HOLD", 1
        elif quorum == "first":
            if "PASS" in unique:
                return "PASS", 0
            return "HOLD", 1
        return "HOLD", 1

    # ------------------------------------------------------------------
    # Phase 2 closures (preserved)
    # ------------------------------------------------------------------

    def build_summary_payload(self, *, disagreement_sla: dict) -> dict:
        """Closure 1: build_summary_payload."""
        rt, ctx = self.runtime, self.ctx
        lcs = self._h["_load_compaction_status_summary"]
        sc = {
            "pass_count": sum(1 for s in rt.steps if s["status"]=="PASS"),
            "hold_count": sum(1 for s in rt.steps if s["status"]=="HOLD"),
            "fail_count": sum(1 for s in rt.steps if s["status"]=="FAIL"),
            "error_count": sum(1 for s in rt.steps if s["status"]=="ERROR"),
            "skip_count": sum(1 for s in rt.steps if s["status"]=="SKIP"),
            "total_steps": len(rt.steps),
        }
        fec = [s["exit_code"] for s in rt.steps if s["status"]=="FAIL" and isinstance(s.get("exit_code"),int)]
        if sc["error_count"]>0: fcode,fres=2,"ERROR"
        elif any(c==2 for c in fec): fcode,fres=2,"ERROR"
        elif fec: fcode,fres=1,"FAIL"
        elif sc["hold_count"]>0: fcode,fres=0,"HOLD"
        else: fcode,fres=0,"PASS"
        cstep = next((s for s in rt.steps if s.get("name")=="evaluate_context_compaction_trigger"),None)
        comp = lcs(step=cstep, status_json=ctx.compaction_status_json)
        rrc = rt.repo_root_convenience or {}
        return {
            "schema_version":"1.0.0","generated_at_utc":rt.generated_at_utc,
            "repo_root":str(ctx.repo_root),"context_dir":str(ctx.context_dir),
            "scripts_dir":str(ctx.script_dir),"skip_phase_end":ctx.skip_phase_end,
            "allow_hold":ctx.allow_hold,"freshness_hours":ctx.freshness_hours,
            "step_summary":sc,"steps":rt.steps,"disagreement_ledger_sla":disagreement_sla,
            "compaction":comp,"repo_root_convenience":{k:str(v) for k,v in rrc.items()},
            "final_result":fres,"final_exit_code":fcode,
        }

    def run_python_step(self, step_name: str, script_path: Path, script_args: list[str]) -> None:
        """Closure 2: run_python_step."""
        rt, ctx = self.runtime, self.ctx
        _rc = self._h["_run_command"]
        _asn = self._h.get("_append_step_ndjson")
        ndp = ctx.context_dir / "loop_run_steps_latest.ndjson"
        if not script_path.exists():
            ms = {"name":step_name,"status":"ERROR","exit_code":None,"command":[],
                  "started_utc":rt.generated_at_utc,"ended_utc":rt.generated_at_utc,
                  "duration_seconds":0.0,"stdout":"","stderr":"","message":f"Missing script: {script_path}"}
            rt.steps.append(ms)
            if _asn: _asn(ndp, rt.trace_id, ms)
            return
        cmd = [ctx.python_exe, str(script_path)] + script_args
        sr = _rc(step_name=step_name, command=cmd, cwd=ctx.repo_root)
        rt.steps.append(sr)
        if _asn: _asn(ndp, rt.trace_id, sr)

    def _step_by_name(self, step_name: str) -> dict | None:
        """Closure 3: _step_by_name."""
        return next((s for s in self.runtime.steps if s.get("name")==step_name), None)

    @staticmethod
    def _remove_if_exists(path: Path) -> None:
        """Closure 4: _remove_if_exists."""
        try: path.unlink()
        except (FileNotFoundError, OSError): pass

    def _promote_exec_memory_outputs(self, memory_step, build_status) -> bool:
        """Closure 5: _promote_exec_memory_outputs."""
        ctx = self.ctx; vep = self._h["_validate_exact_path"]
        if memory_step is None: return False
        for actual, expected, label in (
            (ctx.exec_memory_current_json, ctx.context_dir/"exec_memory_packet_latest_current.json", "exec-memory current JSON"),
            (ctx.exec_memory_current_md, ctx.context_dir/"exec_memory_packet_latest_current.md", "exec-memory current MD"),
            (ctx.exec_memory_latest_json, ctx.context_dir/"exec_memory_packet_latest.json", "exec-memory latest JSON"),
            (ctx.exec_memory_latest_md, ctx.context_dir/"exec_memory_packet_latest.md", "exec-memory latest MD"),
        ):
            err = vep(actual, expected, label)
            if err: memory_step["status"]="FAIL"; memory_step["exit_code"]=2; memory_step["message"]=err; return False
        if build_status is None:
            memory_step["status"]="FAIL"; memory_step["exit_code"]=2; memory_step["message"]="Build status missing."; return False
        if not bool(build_status.get("authoritative_latest_written")):
            reason=str(build_status.get("reason","")).strip() or "not_authoritative"
            if memory_step.get("status")=="PASS": memory_step["status"]="FAIL"; memory_step["exit_code"]=2
            memory_step["message"]=f"Not authoritative ({reason})."; return False
        if memory_step.get("status") not in {"PASS","FAIL"}: return False
        if not ctx.exec_memory_current_json.exists() or not ctx.exec_memory_current_md.exists():
            memory_step["status"]="FAIL"; memory_step["exit_code"]=2; memory_step["message"]="Outputs not produced."; return False
        try:
            _atomic_write_text(ctx.exec_memory_latest_json, ctx.exec_memory_current_json.read_text(encoding="utf-8-sig"))
            _atomic_write_text(ctx.exec_memory_latest_md, ctx.exec_memory_current_md.read_text(encoding="utf-8-sig"))
        except OSError as exc:
            memory_step["status"]="FAIL"; memory_step["exit_code"]=2; memory_step["message"]=f"Promote failed: {exc}"; return False
        return True

    def _write_temp_summary_snapshot(self) -> bool:
        """Closure 7: _write_temp_summary_snapshot."""
        rt,ctx = self.runtime,self.ctx
        _sds = self._h["_scan_disagreement_sla"]; _vep = self._h["_validate_exact_path"]
        td = self.build_summary_payload(disagreement_sla=_sds(path=ctx.disagreement_ledger_jsonl, now_utc=_utc_now()))
        err = _vep(rt.temp_summary_path, ctx.context_dir/"loop_cycle_summary_current.json", "temp summary")
        if err:
            rt.steps.append({"name":"write_temp_summary","status":"ERROR","exit_code":None,"command":[],
                "started_utc":rt.generated_at_utc,"ended_utc":rt.generated_at_utc,"duration_seconds":0.0,
                "stdout":"","stderr":err,"message":err})
            return False
        try: _atomic_write_text(rt.temp_summary_path, json.dumps(td, indent=2))
        except OSError as exc:
            rt.steps.append({"name":"write_temp_summary","status":"ERROR","exit_code":None,"command":[],
                "started_utc":rt.generated_at_utc,"ended_utc":rt.generated_at_utc,"duration_seconds":0.0,
                "stdout":"","stderr":str(exc),"message":f"Failed: {exc}"})
            return False
        return True

    def _write_round_contract_summary_snapshot(self) -> bool:
        """Closure 8: _write_round_contract_summary_snapshot."""
        rt,ctx = self.runtime,self.ctx
        _sds = self._h["_scan_disagreement_sla"]
        summary = self.build_summary_payload(disagreement_sla=_sds(path=ctx.disagreement_ledger_jsonl, now_utc=_utc_now()))
        try: _atomic_write_text(ctx.output_json, json.dumps(summary, indent=2) + "\n")
        except OSError as exc:
            rt.steps.append({"name":"write_round_contract_summary","status":"ERROR","exit_code":None,"command":[],
                "started_utc":rt.generated_at_utc,"ended_utc":rt.generated_at_utc,"duration_seconds":0.0,
                "stdout":"","stderr":str(exc),"message":f"Failed: {exc}"})
            return False
        return True
