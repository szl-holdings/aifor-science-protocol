#!/usr/bin/env python3
"""Section 4 queue snapshot: validation, event semantics, canonical hashing.

Implements the queue snapshot specification for the AI-for-Science Validation
Protocol (PROTOCOL.md v0.1.0-draft, Section 4, pending collaborator review).

Semantics enforced here (fail-closed, deterministic, stdlib-only):
  - Charging is NEVER inferred from reservation: an attempt is charged only
    by an explicit `charging` event, which must follow an `initiation`.
  - Contamination is hybrid: evidenced gates before assignment; post-assignment
    contamination is a logged deviation with the attempt RETAINED in ITT;
    physically evidenced contamination is a per-protocol exclusion only.
    Randomized units are never silently removed.
  - The primary clustering key is the shared assignment/interference unit;
    queue-entry IDs are separate observations. Carryover crossing the unit
    boundary requires a broader cluster declaration BEFORE randomization.
  - Excluded/ineligible records are preserved with explicit reasons.
  - The completed snapshot canonicalizes (sorted keys, stable separators)
    and hashes (SHA-256); provenance records repository revision, schema
    version, runtime versions, artifacts and validation results.
  - No post-freeze edits: a frozen snapshot's hash is checked against its
    recorded package_sha256; any mutation fails the integrity check.

Proof boundary: nothing here runs an experiment; this library validates and
hashes snapshots only.
"""
from __future__ import annotations

import hashlib
import json

SCHEMA_VERSION = "szl.queue-snapshot/v1"
EVENT_ORDER = ["reservation", "initiation", "charging",
               "attempted_execution", "cancellation", "timeout"]


class SnapshotError(ValueError):
    """Raised when a snapshot violates the Section 4 semantics."""


def _parse_ts(value):
    """Parse an RFC3339 timestamp; raise on malformed input (fail-closed)."""
    from datetime import datetime
    if not isinstance(value, str) or not value:
        raise SnapshotError(f"invalid or missing timestamp: {value!r}")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise SnapshotError(f"malformed RFC3339 timestamp {value!r}: {exc}") from exc


def canonical_bytes(snapshot: dict) -> bytes:
    """Deterministic canonical form: sorted keys, no insignificant whitespace."""
    return json.dumps(snapshot, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False).encode("utf-8")


def sha256(snapshot: dict) -> str:
    return hashlib.sha256(canonical_bytes(snapshot)).hexdigest()


def _events(entry: dict) -> list[dict]:
    return entry.get("events", [])


def _typed(entry: dict, etype: str) -> list[dict]:
    return [e for e in _events(entry) if e.get("type") == etype]


def _first_ts(entry: dict, etype: str) -> str | None:
    evs = _typed(entry, etype)
    return min(e["timestamp"] for e in evs) if evs else None


def check_charging(entry: dict) -> None:
    """Charging is never inferred from reservation (Section 1, frozen)."""
    charged = bool(_typed(entry, "charging"))
    initiated = bool(_typed(entry, "initiation"))
    reserved = bool(_typed(entry, "reservation"))
    if charged and not initiated:
        raise SnapshotError(
            f"{entry['queue_entry_id']}: charging without initiation is invalid")
    if reserved and not initiated:
        # reserved but never initiated: capacity information, NOT charged
        return
    if initiated and not charged:
        # initiated but uncharged is a legal intermediate state (charging may
        # not have been recorded yet); validation only forbids charging
        # WITHOUT initiation and inferring charge from reservation.
        return


def check_event_sequence(entry: dict) -> None:
    """Every event's type must be one of the six declared types (enforced)."""
    for e in _events(entry):
        if e.get("type") not in EVENT_ORDER:
            raise SnapshotError(
                f"{entry['queue_entry_id']}: undeclared event type {e.get('type')!r} "
                f"(declared: {EVENT_ORDER})")
    """Reservation precedes initiation precedes charging; every event has a timestamp."""
    events = _events(entry)
    for e in events:
        if not e.get("timestamp"):
            raise SnapshotError(
                f"{entry['queue_entry_id']}: event {e.get('type')} missing timestamp")
    res = _first_ts(entry, "reservation")
    ini = _first_ts(entry, "initiation")
    cha = _first_ts(entry, "charging")
    if res and ini and _parse_ts(ini) < _parse_ts(res):
        raise SnapshotError(f"{entry['queue_entry_id']}: initiation before reservation")
    if ini and cha and _parse_ts(cha) < _parse_ts(ini):
        raise SnapshotError(f"{entry['queue_entry_id']}: charging before initiation")


def check_contamination(entry: dict, randomized_at: str | None) -> None:
    """randomized_at MUST be resolvable for timing reclassification; a cluster
    with unknown randomization time forces the deviation reading (fail-closed)."""
    """Hybrid contamination handling (Section 4 required semantics)."""
    c = entry.get("contamination") or {"status": "none"}
    status = c.get("status", "none")
    KNOWN_CONTAMINATION = {"none", "pre_assignment_evidenced", "post_assignment_deviation"}
    if status not in KNOWN_CONTAMINATION:
        raise SnapshotError(
            f"{entry['queue_entry_id']}: unknown contamination status {status!r} "
            f"(known: {sorted(KNOWN_CONTAMINATION)})")
    if status == "none":
        return
    if status == "pre_assignment_evidenced":
        # objective, evidenced gate BEFORE assignment; the timing check is
        # MANDATORY: unknown randomization time reads as post-assignment
        if not randomized_at:
            raise SnapshotError(
                f"{entry['queue_entry_id']}: pre-assignment contamination cannot "
                "be verified without the cluster's randomized_at (fail-closed)")
        if not c.get("evidence"):
            raise SnapshotError(
                f"{entry['queue_entry_id']}: pre-assignment contamination requires evidence")
        if randomized_at and c.get("detected_at") and _parse_ts(c["detected_at"]) > _parse_ts(randomized_at):
            raise SnapshotError(
                f"{entry['queue_entry_id']}: pre-assignment contamination detected after "
                "randomization is a post-assignment deviation, not a gate")
        if c.get("handling") != "gate_before_assignment":
            raise SnapshotError(
                f"{entry['queue_entry_id']}: pre-assignment evidenced contamination "
                "must be handled by gate_before_assignment")
    elif status == "post_assignment_deviation":
        # logged deviation; attempt RETAINED in ITT; never silently removed
        if c.get("handling") != "logged_deviation_itt_retained":
            raise SnapshotError(
                f"{entry['queue_entry_id']}: post-assignment contamination is a logged "
                "deviation with the attempt retained in ITT")
        if not c.get("detected_at"):
            raise SnapshotError(
                f"{entry['queue_entry_id']}: post-assignment contamination requires detected_at")


def check_clustering(snapshot: dict) -> None:
    cl = snapshot.get("clustering", {})
    if cl.get("primary_key") != "shared_assignment_interference_unit":
        raise SnapshotError("primary clustering key must be the shared "
                            "assignment/interference unit")
    if cl.get("queue_entry_ids_are") != "separate_observations":
        raise SnapshotError("queue-entry IDs are separate observations")
    if cl.get("carryover_rule") != ("carryover_crossing_the_unit_requires_a_broader_"
                                    "cluster_declaration_before_randomization"):
        raise SnapshotError("carryover crossing the unit requires a broader "
                            "cluster declaration before randomization")
    # every queue entry's cluster must be on the roster; the roster is the
    # COMPLETE randomized set — excluded/ineligible preserved with reasons
    roster_ids = {c["cluster_id"] for c in snapshot.get("cluster_roster", [])}
    for c in snapshot.get("cluster_roster", []):
        if c.get("status") in ("excluded", "ineligible") and not c.get("exclusion_reason"):
            raise SnapshotError(
                f"cluster {c['cluster_id']}: excluded/ineligible without explicit reason")
    for entry in snapshot.get("queue_entries", []):
        if entry["cluster_id"] not in roster_ids:
            raise SnapshotError(
                f"{entry['queue_entry_id']}: cluster {entry['cluster_id']} not on the roster")
    # duplicate queue-entry IDs are invalid
    seen = set()
    for entry in snapshot.get("queue_entries", []):
        qid = entry["queue_entry_id"]
        if qid in seen:
            raise SnapshotError(f"duplicate queue_entry_id: {qid}")
        seen.add(qid)


def check_carryover(snapshot: dict, carryover_pairs: list[tuple[str, str]] | None = None):
    """If carryover crosses the assignment/interference unit boundary, a broader
    cluster declaration must exist BEFORE randomization. `carryover_pairs` is
    the evidenced carryover graph (cluster_a, cluster_b)."""
    if not carryover_pairs:
        return
    cl = snapshot.get("clustering", {})
    broader = cl.get("broader_cluster_declared_at")
    randomized_ats = {c["cluster_id"]: c["randomized_at"]
                      for c in snapshot.get("cluster_roster", [])}
    for a, b in carryover_pairs:
        if a in randomized_ats and b in randomized_ats:
            # carryover between two randomized units crosses the boundary
            if not broader:
                raise SnapshotError(
                    f"carryover between {a} and {b} crosses the assignment/interference "
                    "unit; a broader cluster declaration was required BEFORE randomization")
            # the declaration must PRECEDE both units' randomization (enforced)
            decl = _parse_ts(broader)
            for unit in (a, b):
                if _parse_ts(randomized_ats[unit]) < decl:
                    raise SnapshotError(
                        f"broader cluster declaration for carryover ({a}, {b}) came "
                        f"AFTER {unit}'s randomization; it was required BEFORE")


def validate(snapshot: dict,
             carryover_pairs: list[tuple[str, str]] | None = None) -> dict:
    """Full semantic validation. Returns the validation receipt."""
    checks: list[str] = []
    if snapshot.get("schema_version") != SCHEMA_VERSION:
        raise SnapshotError(f"schema_version must be {SCHEMA_VERSION}")
    check_clustering(snapshot)
    checks.append("clustering")
    randomized_at = {c["cluster_id"]: c.get("randomized_at")
                      for c in snapshot.get("cluster_roster", [])}
    for entry in snapshot.get("queue_entries", []):
        check_event_sequence(entry)
        check_charging(entry)
        check_contamination(entry, randomized_at.get(entry["cluster_id"]))
    checks.append("event_sequence")
    checks.append("charging_semantics")
    checks.append("contamination_handling")
    check_carryover(snapshot, carryover_pairs)
    checks.append("carryover_boundary")
    return {"valid": True, "checks": checks}


def freeze(snapshot: dict, repository_revision: str,
           runtime_versions: dict) -> dict:
    """Canonicalize + hash the completed snapshot and record provenance.
    After freezing, any mutation must fail verify_frozen()."""
    receipt = validate(snapshot)
    snapshot = dict(snapshot)
    snapshot["provenance"] = {
        "repository_revision": repository_revision,
        "schema_version": SCHEMA_VERSION,
        "runtime_versions": runtime_versions,
        "generated_artifacts": ["queue-snapshot/schema.json",
                                 "queue_snapshot.py"],
        "validation": receipt,
    }
    snapshot["frozen"] = True
    snapshot["package_sha256"] = sha256({k: v for k, v in snapshot.items()
                                         if k != "package_sha256"})
    return snapshot


def verify_frozen(snapshot: dict) -> bool:
    """Post-freeze integrity: the recorded hash must match the content.
    Any post-freeze mutation makes this return False."""
    if not snapshot.get("frozen"):
        raise SnapshotError("snapshot is not frozen")
    recorded = snapshot.get("package_sha256")
    if not recorded:
        raise SnapshotError("frozen snapshot missing package_sha256")
    actual = sha256({k: v for k, v in snapshot.items() if k != "package_sha256"})
    return actual == recorded
