"""Execution-based task grading (absorb implementation).

Absorbs, at harness level only (source card: docs/LEADERS-STUDY.md,
leader-study PR aifor-science-protocol#12): ScienceAgentBench
(arXiv:2410.05080, ICLR'25, OSU-NLP-Group) -- execution-based grading
of runs supplied to this module, never grading by description or by
model claim.

HONEST SCOPE: this module grades run RECORDS a caller supplies
(exit codes, artifact digests, network flags). It executes nothing,
calls no model, fetches nothing, and a PASS means "the supplied
evidence satisfies the execution contract", nothing more.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

SCHEMA = "szl.aifor-science.execution-grading/v1"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass
class TaskRun:
    """One recorded execution of a task."""
    task_id: str
    exit_code: int
    artifact_sha256: str
    network_used: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "exit_code": self.exit_code,
            "artifact_sha256": self.artifact_sha256,
            "network_used": self.network_used,
        }


@dataclass
class TaskContract:
    """The execution contract a run is graded against."""
    task_id: str
    expected_exit_code: int = 0
    expected_artifact_sha256: str | None = None
    network_forbidden: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "expected_exit_code": self.expected_exit_code,
            "expected_artifact_sha256": self.expected_artifact_sha256,
            "network_forbidden": self.network_forbidden,
        }


def grade_run(run: TaskRun, contract: TaskContract) -> dict[str, Any]:
    """Grade one run against its contract; fail-closed, receipted."""
    reasons: list[str] = []
    if run.task_id != contract.task_id:
        reasons.append("task_id_mismatch")
    if not SHA256_RE.match(run.artifact_sha256 or ""):
        reasons.append("artifact_sha256_not_sha256_hex")
    if run.exit_code != contract.expected_exit_code:
        reasons.append("exit_code_mismatch")
    if contract.expected_artifact_sha256 is not None and run.artifact_sha256 != contract.expected_artifact_sha256:
        reasons.append("artifact_digest_mismatch")
    if contract.network_forbidden and run.network_used:
        reasons.append("network_used_but_forbidden")
    passed = reasons == []
    return {
        "schema": SCHEMA,
        "task_id": run.task_id,
        "verdict": "PASS" if passed else "FAIL",
        "failed_rules": reasons,
        "grading": "execution_based",
        "not": ["description_based", "model_claim_based", "self_executed"],
    }


def grade_suite(
    runs: list[TaskRun], contracts: list[TaskContract]
) -> dict[str, Any]:
    """Grade a suite; every run must have exactly one matching contract."""
    by_id: dict[str, TaskContract] = {c.task_id: c for c in contracts}
    rows: list[dict[str, Any]] = []
    for run in runs:
        contract = by_id.get(run.task_id)
        if contract is None:
            rows.append({
                "schema": SCHEMA,
                "task_id": run.task_id,
                "verdict": "FAIL",
                "failed_rules": ["no_matching_contract"],
                "grading": "execution_based",
            })
            continue
        rows.append(grade_run(run, contract))
    n = len(rows)
    hits = sum(1 for r in rows if r["verdict"] == "PASS")
    return {
        "schema": SCHEMA,
        "kind": "suite",
        "n": n,
        "hits": hits,
        "score": (hits / n) if n else None,
        "verdict": "PASS" if n and hits == n else "FAIL",
        "rows": rows,
        "note": "PASS means the supplied evidence satisfied the execution contract.",
    }
