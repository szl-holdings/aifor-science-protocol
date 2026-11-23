# Leader-Study Upgrade Plan - W27 loop-4 - 2026-11-23

Status: PROPOSE-ONLY DRAFT - DO NOT MERGE. Owner-gated: merging requires governing approval and the estate signature-wall owner unlock.

Repo: aifor-science-protocol - Pre-registered, version-frozen protocol package for AI-for-Science validation experiments. ITT accounting + decision-anchored MRD + named adjudication. The validation bottleneck, solved.

Frame: OUROBOROS loop-4 leader study. Governing seat: Kimi kimi-k3.1-pro (json_ok, think off). Advisory seats: Astra/Sol/Claude community rails (provenance unverified, advisory only). Leader evidence web-verified 2026-11-23.

## Leader moats to absorb
- OSF preregistration: Time-stamped, read-only registrations with explicit contingencies, estimand specificity, and transparent deviation reporting. Moat: Immutable public provenance plus a recognized disclosure standard for separating planned analyses from later interpretation.
- AEA RCT registry: Registry-based pre-analysis planning for randomized experiments, including design and outcome declarations before results. Moat: Discipline-specific registry norms and discoverability that make prospective commitments externally legible.
- CONSORT/SPIRIT: Established protocol and reporting standards for trials, including participant flow, outcomes, deviations, and analysis populations. Moat: Comprehensive, field-tested checklists and broad reviewer familiarity that reduce ambiguity in execution and reporting.
- Cluster-randomized trial methods (Hayes and Moulton): Design and analysis methods that treat clusters as the randomization unit and address within-cluster dependence. Moat: A mature statistical foundation for valid inference, precision assessment, and interpretation under clustering.
- Minimum relevant difference in study design: Anchoring design choices to a difference that would matter for a decision rather than to statistical significance alone. Moat: Decision relevance: the threshold is tied to practical action and can be declared before outcomes are observed.
- AI-assisted hypothesis generation with human design authority: Using AI to propose candidates while retaining human accountability for experimental design and validation decisions. Moat: A governance boundary that preserves human responsibility while allowing machine-generated search and ideation.

## Honest gaps (grounded in repo facts)
- The README explicitly says the queue snapshot spec in PROTOCOL.md section 4 is pending, so the package is not yet a complete executable protocol package.
- Status is v0.1.0-draft: only the accounting rule and MRD are described as frozen, while the queue snapshot specification remains unfinished.
- The facts describe a version-freeze mechanism but provide no evidence of an external timestamp, immutable registration, signed release, or public deviation log comparable to OSF or AEA registration.
- Cluster randomization is named as a locked decision, but the supplied facts do not establish documented dependence-aware analysis, precision, or sample-size procedures.
- ITT and per-protocol ledgers are named, but the facts do not show a participant or cluster flow template, deviation taxonomy, or reconciliation report comparable to CONSORT/SPIRIT practice.
- Named stopping-rule and inconclusive-adjudication roles are claimed, but the facts do not establish conflict-of-interest handling, escalation timing, evidence access, or an auditable decision record.
- The schema and consistency tests establish machine-readable structure and cross-file checks, but the facts do not demonstrate validation of real experiment artifacts, rendered reports, or end-to-end execution.
- The README names collaborators and human design authority in the framing, but the facts do not specify how AI-generated hypotheses are approved, versioned, or separated from outcome-aware changes.

## Dosed upgrade plan
- Dose 1: Finish the pending queue snapshot spec with the collaborator; define required fields, immutability expectations, timing relative to outcomes, and worked examples without changing the frozen accounting rule or MRD.
- Dose 2: Add a protocol-registration and deviation package: release identifier, content hash, optional external timestamp, estimand and outcome checklist, contingency fields, and a deviation ledger linked to ITT and per-protocol reporting.
- Dose 3: Add cluster-trial execution templates covering cluster flow, dependence-aware analysis assumptions, precision inputs, MRD decision context, named-role decisions, and AI-hypothesis approval provenance; extend tests only to validate these documented artifacts.
- Dose 4: After review, publish one synthetic end-to-end example and its expected outputs, then propose a versioned release candidate with explicit compatibility and deviation notes.
- Risk note: The main risk is governance theater: adding registry-like fields and templates without immutable timing, complete execution records, or valid cluster-aware inference could make the protocol look more rigorous than its evidence warrants. Expanding scope before the pending queue spec is resolved could also create cross-file inconsistency or pressure to revise frozen decisions after outcomes are known.
- Propose-only note: This audit proposes changes only; it does not assert that any file, registration, analysis method, or collaborator contribution already exists. Frozen decisions should not be altered silently: any substantive amendment should be separately versioned, justified, and approved by the named human authority.

## Advisory notes (unverified rails, non-binding)
- astra: acoustic-validation: Proprietary high-fidelity benchmark datasets for PDE solver verification. ayllu: Formal verification proofs for multi-agent consensus and evidence-binding. aifor-science-protocol: Institutional adoption as the standard for AI-driven research pre-registration.
- sol: acoustic-validation: Proprietary high-fidelity synthetic datasets for benchmark validation. ayllu: Formal verification proofs for multi-agent consensus and evidence-binding. aifor-science-protocol: Standardized, machine-readable registration schema adopted by major journals.
- claude: acoustic-validation: Proprietary benchmark datasets of verified physical ground-truth measurements. ayllu: A standardized, cryptographically verifiable audit trail for multi-agent consensus. aifor-science-protocol: Institutional endorsement and integration into peer-review submission pipelines.

## DO NOT MERGE
This plan is a proposal artifact of the 10-pass OUROBOROS loop (loop-4 of 10). No code, no CI, no behavior changes in this file. A reviewer with authority may convert to a work order later.