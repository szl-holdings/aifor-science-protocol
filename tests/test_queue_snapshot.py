"""Section 4 queue snapshot contract tests (all twelve required cases).

Proof boundary: nothing here tests an experiment, a dataset or a result.
A passing run shows the snapshot semantics enforce the protocol's frozen
accounting rule and the Section 4 requirements - nothing more.
"""
from __future__ import annotations

import copy

import pytest

import queue_snapshot as qs


def base_snapshot() -> dict:
    """A minimal valid snapshot: one randomized cluster, one clean entry."""
    return {
        "schema_version": "szl.queue-snapshot/v1",
        "protocol_version": "v0.1.0-draft",
        "snapshot_id": "qs-example-001",
        "generated_at": "2026-11-07T00:00:00Z",
        "eligibility": [{"id": "e1", "statement": "candidate passes pre-checks"}],
        "exclusions": [{"id": "x1", "statement": "instrument malfunction before review",
                        "applies_to": "per_protocol_only"}],
        "contamination_controls": {
            "pre_assignment_gates": [{"id": "g1", "evidence_required":
                                      "objective_physical_evidence",
                                      "timing": "before_assignment"}],
            "residual_risk_covariates": ["baseline_instrument_drift"],
            "sensitivity_analyses": ["re-run primary with drift covariate removed"],
        },
        "clustering": {
            "primary_key": "shared_assignment_interference_unit",
            "assignment_unit": "batch-instrument-slot",
            "interference_unit": "batch-instrument-slot",
            "aligned_with": ["batch", "instrument_slot"],
            "carryover_rule": ("carryover_crossing_the_unit_requires_a_broader_"
                               "cluster_declaration_before_randomization"),
            "queue_entry_ids_are": "separate_observations",
        },
        "cluster_roster": [
            {"cluster_id": "cl-1", "arm": "candidate",
             "randomized_at": "2026-11-07T01:00:00Z", "status": "randomized",
             "batch": "b1", "instrument_slots": ["s1"]},
        ],
        "queue_entries": [
            {"queue_entry_id": "qe-1", "cluster_id": "cl-1", "eligible": True,
             "events": [
                 {"type": "reservation", "timestamp": "2026-11-07T01:10:00Z"},
                 {"type": "initiation", "timestamp": "2026-11-07T01:20:00Z"},
                 {"type": "charging", "timestamp": "2026-11-07T01:21:00Z"},
             ]},
        ],
    }


def entry(s):
    return s["queue_entries"][0]


# ---- 1. contamination BEFORE assignment: evidenced gate passes ----
def test_contamination_before_assignment():
    s = base_snapshot()
    entry(s)["contamination"] = {
        "status": "pre_assignment_evidenced",
        "evidence": "swab assay positive, lab notebook p.12",
        "detected_at": "2026-11-07T00:30:00Z",
        "handling": "gate_before_assignment",
        "covariate_recorded": "baseline_instrument_drift",
    }
    receipt = qs.validate(s)
    assert receipt["valid"] and "contamination_handling" in receipt["checks"]


def test_pre_assignment_gate_requires_evidence():
    s = base_snapshot()
    entry(s)["contamination"] = {"status": "pre_assignment_evidenced",
                                 "detected_at": "2026-11-07T00:30:00Z",
                                 "handling": "gate_before_assignment"}
    with pytest.raises(qs.SnapshotError, match="requires evidence"):
        qs.validate(s)


# ---- 2. contamination AFTER assignment: logged deviation, ITT retained ----
def test_contamination_after_assignment():
    s = base_snapshot()
    entry(s)["contamination"] = {
        "status": "post_assignment_deviation",
        "evidence": "physical evidence recorded",
        "detected_at": "2026-11-07T02:00:00Z",
        "handling": "logged_deviation_itt_retained",
    }
    qs.validate(s)


def test_post_assignment_must_be_logged_deviation():
    s = base_snapshot()
    entry(s)["contamination"] = {"status": "post_assignment_deviation",
                                 "detected_at": "2026-11-07T02:00:00Z",
                                 "handling": "gate_before_assignment"}
    with pytest.raises(qs.SnapshotError, match="logged deviation"):
        qs.validate(s)


def test_pre_assignment_detected_after_randomization_is_a_deviation():
    s = base_snapshot()
    entry(s)["contamination"] = {
        "status": "pre_assignment_evidenced",
        "evidence": "swab assay",
        "detected_at": "2026-11-07T03:00:00Z",
        "handling": "gate_before_assignment",
    }
    with pytest.raises(qs.SnapshotError, match="post-assignment deviation"):
        qs.validate(s)


# ---- 3/4. initiated-but-uncharged and reserved-but-never-initiated ----
def test_initiated_but_uncharged_is_a_legal_state():
    s = base_snapshot()
    entry(s)["events"] = [
        {"type": "reservation", "timestamp": "2026-11-07T01:10:00Z"},
        {"type": "initiation", "timestamp": "2026-11-07T01:20:00Z"},
    ]
    qs.validate(s)


def test_reserved_but_never_initiated_is_not_charged():
    s = base_snapshot()
    entry(s)["events"] = [
        {"type": "reservation", "timestamp": "2026-11-07T01:10:00Z"},
    ]
    qs.validate(s)
    assert qs.sha256(s)


def test_charging_without_initiation_is_invalid():
    s = base_snapshot()
    entry(s)["events"] = [
        {"type": "reservation", "timestamp": "2026-11-07T01:10:00Z"},
        {"type": "charging", "timestamp": "2026-11-07T01:21:00Z"},
    ]
    with pytest.raises(qs.SnapshotError, match="charging without initiation"):
        qs.validate(s)


def test_charging_never_inferred_from_reservation():
    s = base_snapshot()
    entry(s)["events"] = [{"type": "reservation", "timestamp": "2026-11-07T01:10:00Z"}]
    qs.validate(s)


# ---- 5/6. cancellation and timeout ----
def test_cancellation_before_consumption():
    s = base_snapshot()
    entry(s)["events"] = [
        {"type": "reservation", "timestamp": "2026-11-07T01:10:00Z"},
        {"type": "cancellation", "timestamp": "2026-11-07T01:15:00Z"},
    ]
    qs.validate(s)


def test_timeout():
    s = base_snapshot()
    entry(s)["events"] = [
        {"type": "reservation", "timestamp": "2026-11-07T01:10:00Z"},
        {"type": "initiation", "timestamp": "2026-11-07T01:20:00Z"},
        {"type": "timeout", "timestamp": "2026-11-07T02:20:00Z"},
    ]
    qs.validate(s)


# ---- 7. carryover requiring a broader cluster ----
def test_carryover_crossing_the_unit_requires_broader_cluster():
    s = base_snapshot()
    s["cluster_roster"].append(
        {"cluster_id": "cl-2", "arm": "control",
         "randomized_at": "2026-11-07T01:00:00Z", "status": "randomized",
         "batch": "b1", "instrument_slots": ["s2"]})
    with pytest.raises(qs.SnapshotError, match="broader cluster declaration"):
        qs.validate(s, carryover_pairs=[("cl-1", "cl-2")])


def test_carryover_with_broader_declaration_passes():
    s = base_snapshot()
    s["cluster_roster"].append(
        {"cluster_id": "cl-2", "arm": "control",
         "randomized_at": "2026-11-07T01:00:00Z", "status": "randomized",
         "batch": "b1", "instrument_slots": ["s2"]})
    s["clustering"]["broader_cluster_declared_at"] = "2026-11-07T00:50:00Z"
    qs.validate(s, carryover_pairs=[("cl-1", "cl-2")])


# ---- 8. exclusions preserved with explicit reasons ----
def test_excluded_cluster_requires_reason():
    s = base_snapshot()
    s["cluster_roster"].append(
        {"cluster_id": "cl-3", "arm": "control",
         "randomized_at": "2026-11-07T01:00:00Z", "status": "excluded"})
    with pytest.raises(qs.SnapshotError, match="explicit reason"):
        qs.validate(s)


def test_excluded_cluster_with_reason_is_preserved():
    s = base_snapshot()
    s["cluster_roster"].append(
        {"cluster_id": "cl-3", "arm": "control",
         "randomized_at": "2026-11-07T01:00:00Z", "status": "excluded",
         "exclusion_reason": "instrument malfunction documented pre-review"})
    qs.validate(s)


# ---- 9. duplicate queue-entry IDs ----
def test_duplicate_queue_entry_ids_invalid():
    s = base_snapshot()
    s["queue_entries"].append(copy.deepcopy(entry(s)))
    with pytest.raises(qs.SnapshotError, match="duplicate queue_entry_id"):
        qs.validate(s)


# ---- 10. missing timestamps ----
def test_missing_timestamp_invalid():
    s = base_snapshot()
    entry(s)["events"][0] = {"type": "reservation"}
    with pytest.raises(qs.SnapshotError, match="missing timestamp"):
        qs.validate(s)


# ---- 11. hash mismatch ----
def test_hash_changes_with_content():
    s = base_snapshot()
    h1 = qs.sha256(s)
    entry(s)["events"].append({"type": "timeout", "timestamp": "2026-11-07T05:00:00Z"})
    h2 = qs.sha256(s)
    assert h1 != h2 and len(h1) == 64


def test_canonical_form_is_deterministic():
    s = base_snapshot()
    a = qs.canonical_bytes(s)
    s2 = {k: s[k] for k in reversed(list(s.keys()))}
    b = qs.canonical_bytes(s2)
    assert a == b


# ---- 12. post-freeze mutation ----
def test_post_freeze_mutation_fails_integrity():
    s = base_snapshot()
    frozen = qs.freeze(s, repository_revision="643a67a5",
                       runtime_versions={"python": "3.12"})
    assert qs.verify_frozen(frozen) is True
    mutated = copy.deepcopy(frozen)
    mutated["queue_entries"][0]["events"].append(
        {"type": "attempted_execution", "timestamp": "2026-11-07T09:00:00Z"})
    assert qs.verify_frozen(mutated) is False


def test_freeze_records_provenance():
    s = base_snapshot()
    frozen = qs.freeze(s, repository_revision="643a67a5",
                      runtime_versions={"python": "3.12"})
    p = frozen["provenance"]
    assert p["repository_revision"] == "643a67a5"
    assert p["schema_version"] == qs.SCHEMA_VERSION
    assert p["validation"]["valid"] is True
    assert frozen["frozen"] is True
    assert len(frozen["package_sha256"]) == 64


def test_verify_frozen_requires_frozen_snapshot():
    s = base_snapshot()
    with pytest.raises(qs.SnapshotError, match="not frozen"):
        qs.verify_frozen(s)
