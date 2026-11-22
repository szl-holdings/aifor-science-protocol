"""Tests for execution_grading (ScienceAgentBench absorb). Stdlib only."""
from __future__ import annotations

from execution_grading import TaskContract, TaskRun, grade_run, grade_suite


def test_pass_when_contract_met():
    r = grade_run(
        TaskRun(task_id="t1", exit_code=0, artifact_sha256="d" * 64, network_used=False),
        TaskContract(task_id="t1", expected_artifact_sha256="d" * 64),
    )
    assert r["verdict"] == "PASS"
    assert r["failed_rules"] == []


def test_fail_on_exit_code_mismatch():
    r = grade_run(
        TaskRun(task_id="t1", exit_code=2, artifact_sha256="d" * 64),
        TaskContract(task_id="t1"),
    )
    assert r["verdict"] == "FAIL"
    assert "exit_code_mismatch" in r["failed_rules"]


def test_fail_on_network_used_when_forbidden():
    r = grade_run(
        TaskRun(task_id="t1", exit_code=0, artifact_sha256="d" * 64, network_used=True),
        TaskContract(task_id="t1"),
    )
    assert r["verdict"] == "FAIL"
    assert "network_used_but_forbidden" in r["failed_rules"]


def test_fail_on_digest_mismatch():
    r = grade_run(
        TaskRun(task_id="t1", exit_code=0, artifact_sha256="e" * 64),
        TaskContract(task_id="t1", expected_artifact_sha256="d" * 64),
    )
    assert r["verdict"] == "FAIL"
    assert "artifact_digest_mismatch" in r["failed_rules"]


def test_suite_requires_matching_contract():
    run = TaskRun(task_id="t9", exit_code=0, artifact_sha256="d" * 64)
    r = grade_suite([run], [TaskContract(task_id="t1")])
    assert r["verdict"] == "FAIL"
    assert r["rows"][0]["failed_rules"] == ["no_matching_contract"]


def test_suite_score_and_verdict():
    runs = [TaskRun(task_id=f"t{i}", exit_code=0, artifact_sha256="d" * 64) for i in (1, 2)]
    contracts = [TaskContract(task_id=f"t{i}") for i in (1, 2)]
    r = grade_suite(runs, contracts)
    assert r["score"] == 1.0
    assert r["verdict"] == "PASS"
