# AI-for-Science Validation Protocol Package

**Version: v0.1.0-draft** | **Status: PARTIALLY FROZEN** (accounting rule and MRD frozen; queue snapshot spec pending collaborator)

**Collaborators:** betterwithage (Stephen P. Lutar Jr., SZL Holdings) + ankitjha2519020708

**Locked decisions (2026-11-05):**
1. **Randomization unit:** Cluster randomization (by batch/instrument slot) as primary unit
2. **Attempt accounting:** Intention-to-treat (primary) + per-protocol (secondary), frozen pre-outcome
3. **MRD:** Defined on the validated-outcome scale with rationale + interval rule
4. **Adjudication:** Stopping-rule owner and inconclusive adjudicator named separately in the protocol ledger

---

## 1. Accounting Rule (frozen)

**Epistemic status: FROZEN — pre-declared, not to be modified after outcome review begins.**

### Primary Analysis: Intention-to-Treat (ITT)

Every initiated attempt is charged at the moment its first reserved resource is consumed, under one pre-declared unit definition:

> **An attempt is "initiated" when the candidate enters the instrument queue with a reserved slot, and remains charged regardless of abort, failure, contamination, or early termination.**

No post-hoc reclassification of initiated attempts.

### Secondary Analysis: Per-Protocol

Exclusions limited to:
- (a) Instrument malfunction documented before outcome review
- (b) Contamination events with recorded physical evidence
- (c) Queue entries cancelled before any resource consumption

Protocol-deviation rules frozen before outcome review; deviations recorded but not excluded from ITT.

### Coupled Resource Ledger — four disjoint states, reported separately:

| State | Definition | Treatment |
|---|---|---|
| `reserved` | Slot held, not yet consumed | Capacity information |
| `consumed` | Instrument time used by an initiated attempt | Charged to ITT |
| `failed` | Consumed time producing no valid characterization | Charged to ITT; a negative scientific outcome |
| `unavailable` | Capacity loss not attributable to any attempt (maintenance, calibration, third-party use) | **Capacity information, never a negative outcome** |

### Decision Ledger — nine mutually exclusive states:

`chosen` → `deferred` → `rejected` → `attempted` → `failed` → `unattempted` → `characterization-pending` → `validated` → `inconclusive`

---

## 2. Minimum Relevant Difference (MRD) (frozen)

**Epistemic status: FROZEN — pre-declared, not to be modified after outcome review begins.**

Not a percentage. Defined on the **validated-outcome scale** as:

> *The smallest effect that would change a scientific or allocation decision* — concretely, the smallest improvement in validated-outcome rate that would justify reallocating instrument budget from the current policy to the candidate policy.

Recorded before queue freeze with:
- (a) The decision it would change
- (b) Baseline validated-outcome rate and its observed variability from historical data
- (c) Assessment window
- (d) Uncertainty target

**Interpretation rule:** "Not statistically significant" is uninterpretable unless the confidence interval also excludes effects at the MRD boundary. An interval containing the MRD is reported as *inconclusive*, not as no-difference.

---

## 3. Adjudication Roles (named in the protocol ledger)

| Role | Responsibility |
|---|---|
| **Stopping-rule owner** | Declares trigger, with evidence and timestamp recorded in the protocol ledger |
| **Inconclusive adjudicator** | Adjudicates results whose confidence intervals include the MRD boundary |

Both roles named separately, with trigger evidence and timestamp recorded before any experiment runs.

---

## 4. Queue Snapshot Spec (pending collaborator)

**Epistemic status: DRAFT — ankitjha2519020708 to provide.**

The queue snapshot spec must include:
- Eligibility criteria
- Exclusion criteria
- Contamination controls
- Cluster/block fields
- The two ledgers (ITT + per-protocol) with pre-declared fields
- MRD definition (from Section 2)
- Stopping rules (from Section 3)
- Adjudicator roles (from Section 3)

**Format:** Versioned JSON + human-readable README, committed to this repository.

---

## 5. Framing Note (preserved from discussion)

> This protocol can test whether a proposed policy improves validated outcomes at equal budgets — it **cannot** by itself establish that the current policy is failing. Those are different claims, and keeping that distinction explicit protects the result.

---

## 6. Version Freeze Mechanism

This package is versioned via git tags. Once the queue snapshot spec is contributed and both parties agree:
1. Tag as `v1.0.0-frozen`
2. The tag hash is recorded as the pre-declared protocol version
3. Any post-freeze changes require a new version tag and explicit justification in the protocol ledger

---

## License

CC-BY-4.0 — shared protocol package, freely usable with attribution.
