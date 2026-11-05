# AI-for-Science Validation Protocol

Versioned pre-declared protocol package for AI-for-Science validation experiments.

**Collaborators:** [betterwithage](https://huggingface.co/betterwithage) (Stephen P. Lutar Jr., SZL Holdings) + ankitjha2519020708

**Status:** v0.1.0-draft — accounting rule and MRD frozen; queue snapshot spec pending collaborator contribution.

## What this is

A pre-declared, versioned experimental protocol that separates:
- **Validated outcomes** (did the candidate actually work?)
- **Information gain** (did we learn something useful?)

...using intention-to-treat accounting, a decision-anchored minimum relevant difference, and named adjudication roles.

## Structure

- `PROTOCOL.md` — the full protocol package (accounting rule, MRD, adjudication, queue spec structure)
- Queue snapshot spec: pending from collaborator

## The four locked decisions

1. Cluster randomization as primary unit
2. ITT (primary) + per-protocol (secondary) ledgers frozen pre-outcome
3. MRD on the validated-outcome scale with interval rule
4. Named stopping-rule owner vs. inconclusive adjudicator

## Contributing

This is a two-party collaboration. The package freezes when both parties agree on all sections.
