"""Independent auditor for worker reply packets.

Reads a worker_reply_packet.json, evaluates each item against governance
rules (AUD-R000 through AUD-R009), and writes auditor_findings.json.

Exit codes:
  0 — PASS  (shadow: non-blocking findings; enforce: no Critical/High)
  1 — BLOCK (enforce mode with Critical/High findings)
  2 — INFRA_ERROR (script crash / invalid input — always treated as error)

Output write contract:
  Exit 0 and 1 MUST write valid JSON before exiting.
  Exit 2 MAY skip output (infra failure may prevent writing).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime
from datetime import timezone
from pathlib import Path

# --- Constants ---------------------------------------------------------------

SUPPORTED_SCHEMA_VERSIONS = {"1.0.0", "2.0.0"}
REQUIRED_TRIAD = {"principal", "riskops", "qa"}
RISK_SENTINELS = {"none", "n/a", "na", "placeholder", "tbd", "todo", ""}
PLACEHOLDER_TOKENS = {"bootstrap placeholder", "replace before phase-end",
                      "placeholder scaffold", "bootstrap placeholder - replace before phase-end"}

ALLOWED_MODES = {"shadow", "enforce"}
ALLOWED_SEVERITIES = {"CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"}


# --- Helpers -----------------------------------------------------------------

def _as_str(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _is_substantive_risk(text: str) -> bool:
    t = text.strip().lower()
    if t in RISK_SENTINELS:
        return False
    if "placeholder" in t:
        return False
    return True


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, prefix=".", suffix=".tmp")
    try:
        with open(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


# --- Finding builder ---------------------------------------------------------

class FindingBuilder:
    """Accumulates auditor findings for one run."""

    def __init__(self, *, mode: str) -> None:
        self._mode = mode
        self._findings: list[dict] = []
        self._counter = 0
        self._items_reviewed = 0

    def set_items_reviewed(self, count: int) -> None:
        self._items_reviewed = count

    def add(
        self,
        *,
        rule_id: str,
        item_index: int,
        task_id: str,
        severity: str,
        category: str,
        description: str,
    ) -> None:
        self._counter += 1
        blocking = self._is_blocking(severity)
        self._findings.append({
            "finding_id": f"AUD-{self._counter:03d}",
            "rule_id": rule_id,
            "item_index": item_index,
            "task_id": task_id,
            "severity": severity,
            "category": category,
            "description": description,
            "blocking": blocking,
        })

    def _is_blocking(self, severity: str) -> bool:
        if self._mode == "shadow":
            return False
        return severity in ("CRITICAL", "HIGH")

    @property
    def findings(self) -> list[dict]:
        return list(self._findings)

    def summary(self) -> dict:
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        for f in self._findings:
            key = f["severity"].lower()
            if key in counts:
                counts[key] += 1
        has_blocking = any(f["blocking"] for f in self._findings)
        verdict = "BLOCK" if has_blocking else "PASS"
        return {
            "total_findings": len(self._findings),
            "items_reviewed": self._items_reviewed,
            **counts,
            "gate_verdict": verdict,
            "infra_error": False,
        }


# --- Auditor checks ---------------------------------------------------------

def _audit_item_v2(
    item: dict,
    *,
    item_index: int,
    fb: FindingBuilder,
    repo_root: Path,
) -> None:
    """Run AUD-R001 through AUD-R009 on a v2 item."""
    task_id = _as_str(item.get("task_id")) or f"items[{item_index}]"
    mo = item.get("machine_optimized")
    if not isinstance(mo, dict):
        mo = {}

    # AUD-R001: confidence < 0.70
    cl = mo.get("confidence_level")
    if isinstance(cl, dict):
        score = cl.get("score")
        if isinstance(score, (int, float)) and float(score) < 0.70:
            fb.add(
                rule_id="AUD-R001",
                item_index=item_index,
                task_id=task_id,
                severity="CRITICAL",
                category="confidence",
                description=f"confidence_level.score={score} below 0.70 threshold",
            )

    # AUD-R002: relatability < 0.75
    psa = mo.get("problem_solving_alignment_score")
    if isinstance(psa, (int, float)) and float(psa) < 0.75:
        fb.add(
            rule_id="AUD-R002",
            item_index=item_index,
            task_id=task_id,
            severity="HIGH",
            category="relatability",
            description=f"problem_solving_alignment_score={psa} below 0.75 threshold",
        )

    # AUD-R003: triad missing domains
    coverage = mo.get("expertise_coverage")
    found_domains: set[str] = set()
    if isinstance(coverage, list):
        for entry in coverage:
            if isinstance(entry, dict):
                found_domains.add(_as_str(entry.get("domain")).lower())
    missing = REQUIRED_TRIAD - found_domains
    if missing:
        fb.add(
            rule_id="AUD-R003",
            item_index=item_index,
            task_id=task_id,
            severity="HIGH",
            category="triad_missing",
            description=f"expertise_coverage missing required triad domains: {sorted(missing)}",
        )

    # AUD-R004: triad all-SKIPPED
    if not missing and isinstance(coverage, list):
        triad_verdicts = []
        for entry in coverage:
            if isinstance(entry, dict):
                d = _as_str(entry.get("domain")).lower()
                v = _as_str(entry.get("verdict")).upper()
                if d in REQUIRED_TRIAD:
                    triad_verdicts.append(v)
        if triad_verdicts and all(v == "SKIPPED" for v in triad_verdicts):
            fb.add(
                rule_id="AUD-R004",
                item_index=item_index,
                task_id=task_id,
                severity="HIGH",
                category="triad_skipped",
                description="all triad domains are SKIPPED; at least one must be APPLIED or NOT_REQUIRED",
            )

    # AUD-R005: citations < 2
    citations = item.get("citations")
    if isinstance(citations, list) and len(citations) < 2:
        fb.add(
            rule_id="AUD-R005",
            item_index=item_index,
            task_id=task_id,
            severity="MEDIUM",
            category="citations_count",
            description=f"citations count={len(citations)} below minimum 2",
        )

    # AUD-R006: citation paths missing on disk
    if isinstance(citations, list):
        for ci, cite in enumerate(citations):
            if not isinstance(cite, dict):
                continue
            cite_path = _as_str(cite.get("path"))
            if cite_path:
                abs_path = (repo_root / cite_path).resolve()
                if not abs_path.exists():
                    fb.add(
                        rule_id="AUD-R006",
                        item_index=item_index,
                        task_id=task_id,
                        severity="HIGH",
                        category="citation_path_missing",
                        description=f"citations[{ci}].path does not exist: {cite_path}",
                    )

    # AUD-R007: pm_first_principles placeholder text
    fp = item.get("pm_first_principles")
    if isinstance(fp, dict):
        for field in ("problem", "constraints", "logic", "solution"):
            val = _as_str(fp.get(field)).lower()
            if val and any(tok in val for tok in PLACEHOLDER_TOKENS):
                fb.add(
                    rule_id="AUD-R007",
                    item_index=item_index,
                    task_id=task_id,
                    severity="MEDIUM",
                    category="placeholder_text",
                    description=f"pm_first_principles.{field} contains placeholder text",
                )
                break  # one finding per item is enough

    # AUD-R008: dod_result = FAIL
    dod = _as_str(item.get("dod_result")).upper()
    if dod == "FAIL":
        fb.add(
            rule_id="AUD-R008",
            item_index=item_index,
            task_id=task_id,
            severity="MEDIUM",
            category="dod_fail",
            description="dod_result=FAIL (informative; FAIL is valid data per validator contract)",
        )

    # AUD-R009: open_risks non-empty + dod_result = PASS (sentinel-normalized)
    if dod == "PASS":
        risks = item.get("open_risks")
        if isinstance(risks, list):
            substantive = [r for r in risks if isinstance(r, str) and _is_substantive_risk(r)]
            if substantive:
                fb.add(
                    rule_id="AUD-R009",
                    item_index=item_index,
                    task_id=task_id,
                    severity="MEDIUM",
                    category="open_risks_with_pass",
                    description=f"dod_result=PASS with {len(substantive)} substantive open risk(s)",
                )


# --- Main --------------------------------------------------------------------

def run_audit(
    *,
    input_path: Path,
    repo_root: Path,
    output_path: Path,
    mode: str,
) -> int:
    """Core audit logic. Returns exit code."""
    if mode not in ALLOWED_MODES:
        print(f"Error: mode must be one of {sorted(ALLOWED_MODES)}", file=sys.stderr)
        return 2

    if not input_path.exists():
        print(f"Error: input file not found: {input_path}", file=sys.stderr)
        return 2

    try:
        raw = input_path.read_text(encoding="utf-8")
        payload = json.loads(raw)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"Error: cannot read input: {exc}", file=sys.stderr)
        return 2

    if not isinstance(payload, dict):
        print("Error: packet must be a JSON object", file=sys.stderr)
        return 2

    schema_version = _as_str(payload.get("schema_version"))
    if not schema_version or schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        print(f"Error: unsupported or missing schema_version: {schema_version!r}", file=sys.stderr)
        return 2

    fb = FindingBuilder(mode=mode)

    # AUD-R000: schema_version == "1.0.0"
    if schema_version == "1.0.0":
        # v1 packet — skip v2-only checks, emit one HIGH finding
        items = payload.get("items", [])
        fb.set_items_reviewed(len([i for i in items if isinstance(i, dict)]))
        for idx, item in enumerate(items):
            if not isinstance(item, dict):
                continue
            task_id = _as_str(item.get("task_id")) or f"items[{idx}]"
            fb.add(
                rule_id="AUD-R000",
                item_index=idx,
                task_id=task_id,
                severity="HIGH",
                category="schema_version",
                description="v1 packet — v2-only checks skipped",
            )
    elif schema_version == "2.0.0":
        items = payload.get("items", [])
        if not isinstance(items, list):
            items = []
        fb.set_items_reviewed(len([i for i in items if isinstance(i, dict)]))
        for idx, item in enumerate(items):
            if not isinstance(item, dict):
                continue
            _audit_item_v2(
                item,
                item_index=idx,
                fb=fb,
                repo_root=repo_root,
            )

    # Build output
    output = {
        "schema_version": "1.0.0",
        "auditor_id": "auditor-v1",
        "audit_timestamp_utc": _now_utc_iso(),
        "mode": mode,
        "reviewed_packet_path": str(input_path),
        "reviewed_packet_schema_version": schema_version,
        "findings": fb.findings,
        "summary": fb.summary(),
    }

    # Write output (contract: exit 0/1 MUST write valid JSON)
    _atomic_write_text(output_path, json.dumps(output, indent=2) + "\n")

    summary = fb.summary()
    gate = summary["gate_verdict"]
    print(
        f"Auditor [{mode}]: {summary['total_findings']} findings "
        f"(C={summary['critical']}/H={summary['high']}/M={summary['medium']}"
        f"/L={summary['low']}/I={summary['info']}), gate={gate}"
    )

    if gate == "BLOCK":
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Independent auditor for worker reply packets"
    )
    parser.add_argument(
        "--input", type=str, required=True,
        help="Path to worker_reply_packet.json",
    )
    parser.add_argument(
        "--repo-root", type=str, default=".",
        help="Repository root for resolving citation paths",
    )
    parser.add_argument(
        "--output", type=str, required=True,
        help="Output path for auditor_findings.json",
    )
    parser.add_argument(
        "--mode", type=str, required=True, choices=sorted(ALLOWED_MODES),
        help="Audit mode: shadow (non-blocking) or enforce (blocking on C/H)",
    )
    args = parser.parse_args()

    try:
        return run_audit(
            input_path=Path(args.input).resolve(),
            repo_root=Path(args.repo_root).resolve(),
            output_path=Path(args.output).resolve(),
            mode=args.mode,
        )
    except Exception as exc:
        print(f"Error: unhandled exception: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
