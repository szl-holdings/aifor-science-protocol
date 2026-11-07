# Section 4 — Queue Snapshot Specification (contribution, pending collaborator review)

**Epistemic status: CONTRIBUTION — offered toward PROTOCOL.md Section 4, which is
declared draft/pending collaborator (ankitjha2519020708). This document does not
modify the protocol, does not freeze anything, and is offered for the
collaborator's review, amendment or replacement. No frozen decision is touched.**

This package implements the queue snapshot as versioned JSON
(`schema.json`) plus this human-readable README, per the protocol's Section 4
format requirement.

## Contamination — hybrid handling

- **Before assignment:** objective, evidenced contamination gates. A gate
  requires `objective_physical_evidence` and must fire `before_assignment`;
  a "pre-assignment" contamination detected after randomization is
  reclassified as a post-assignment deviation, never a gate.
- **Residual baseline risks** are recorded as covariates
  (`residual_risk_covariates`), with sensitivity analyses declared before
  analysis (`sensitivity_analyses`).
- **After assignment:** contamination is logged as a deviation with the
  attempt **retained in primary intention-to-treat accounting**. Physically
  evidenced contamination is handled separately in per-protocol analysis
  (exclusion (b) of the frozen Section 1 rule).
- **Never silently remove randomized units.** Excluded/ineligible records are
  preserved on the roster with explicit reasons.

## Clustering

- The **primary clustering key is the shared assignment/interference unit**,
  aligned with batch and instrument-slot design.
- **Queue-entry IDs remain separate observations.**
- If carryover crosses the unit boundary, a **broader cluster declaration is
  required before randomization**; `check_carryover()` fails closed otherwise.

## Snapshot fields

Eligibility criteria, exclusion criteria, contamination controls,
cluster/block fields, assignment/interference unit, queue-entry ID,
reserved-slot state, initiation state, charging state, timestamps, and the
**complete randomized cluster roster** — excluded/ineligible records preserved
with explicit reasons. See `schema.json`.

## Events — reservation is not charging

Queue entry with a reserved slot is **distinct** from first resource
consumption. Exact events with mandatory timestamps:

| Event | Meaning |
|---|---|
| `reservation` | Slot held; capacity information only — **never charged** |
| `initiation` | Candidate enters the queue with a reserved slot (the frozen ITT definition) |
| `charging` | First reserved resource consumed; charged to ITT |
| `cancellation` | Entry cancelled; not charged if before any resource consumption |
| `timeout` | Initiated attempt exceeded its window; charged to ITT |
| `attempted_execution` | Execution attempt recorded |

**Charging is never inferred from reservation.** `charging` without
`initiation` is invalid; `initiation` without `charging` is a legal
intermediate state (the charge may not be recorded yet).

## Canonicalization, hashing, provenance

The completed snapshot canonicalizes deterministically (sorted keys, stable
separators) and hashes with SHA-256 (`queue_snapshot.py`). `freeze()` records
the repository revision, schema version, runtime/tool versions, generated
artifacts, and validation results. **No post-freeze edits**: `verify_frozen()`
fails on any mutation; every later change requires a new tag, a new hash, and
written justification (Section 6).

## Proof boundary

Nothing in this package runs an experiment or establishes a result. The
library validates and hashes snapshots only. Passing tests show the semantics
hold; they do not show the protocol is scientifically sound.

## Tests

`tests/test_queue_snapshot.py` covers all twelve required cases:
contamination before/after assignment, initiated-but-uncharged,
reserved-but-never-initiated, cancellation, timeout, carryover requiring a
broader cluster, exclusions, duplicate queue-entry IDs, missing timestamps,
hash mismatch, and post-freeze mutation.
