<!-- szl:header v1 -->
<!-- Native identity: szl-brand@4309f6fce89179331b0b3ed8c99494e76c5be256; Orbit v2 icon. -->
<p>
  <a href="https://github.com/szl-holdings">
    <img src="https://raw.githubusercontent.com/szl-holdings/szl-brand/4309f6fce89179331b0b3ed8c99494e76c5be256/kit/logos/orbit-v2/suite/szl-icon-32.svg" alt="SZL Holdings — Orbit v2" width="32" height="32" />
  </a>
</p>

**Control before action. Evidence after.**

[Product](https://a-11-oy.com) · [Proof](https://a11oy.net) · [GitHub organization](https://github.com/szl-holdings)
<!-- /szl:header -->

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

| Path | Contents |
|---|---|
| [`PROTOCOL.md`](PROTOCOL.md) | The full protocol package: accounting rule, MRD, adjudication roles, queue snapshot spec structure, framing note, version-freeze mechanism |
| [`protocol.schema.json`](protocol.schema.json) | JSON Schema (draft 2020-12) for a machine-readable protocol document |
| [`CITATION.cff`](CITATION.cff) | Citation metadata (CFF 1.2.0) |
| [`tests/`](tests/) | Consistency tests across `PROTOCOL.md`, the schema, this README and `CITATION.cff`, plus a contract test for CI's hash-locked installs |
| [`requirements-test.txt`](requirements-test.txt), [`requirements-citation.txt`](requirements-citation.txt) | Top-level pins of the validators used by the tests (Quickstart below) |
| [`requirements/ci/`](requirements/ci/) | Hash-locked closures of those pins (`uv pip compile --generate-hashes`); CI installs only these, with `pip install --require-hashes` |

The queue snapshot spec (`PROTOCOL.md` §4) is pending from the collaborator.

## The four locked decisions

1. Cluster randomization as primary unit
2. ITT (primary) + per-protocol (secondary) ledgers frozen pre-outcome
3. MRD on the validated-outcome scale with interval rule
4. Named stopping-rule owner vs. inconclusive adjudicator

## Quickstart

Run from the repository root. Tested with Python 3.12 and 3.13.

Install the pinned validators and run the consistency tests:

```bash
python -m venv .venv
.venv/bin/python -m pip install -r requirements-test.txt
.venv/bin/python -m pytest
```

Every test should pass (pytest exits with status 0).

Validate your own protocol document (here `my-protocol.json`) against the schema:

```bash
.venv/bin/python - my-protocol.json <<'PY'
import json, sys
from jsonschema import Draft202012Validator
schema = json.load(open("protocol.schema.json", encoding="utf-8"))
doc = json.load(open(sys.argv[1], encoding="utf-8"))
errors = list(Draft202012Validator(schema).iter_errors(doc))
for error in errors:
    print("/".join(map(str, error.absolute_path)) or "(root)", "-", error.message)
print("valid" if not errors else f"{len(errors)} error(s)")
sys.exit(1 if errors else 0)
PY
```

It prints `valid` and exits 0, or prints each error with its JSON path and exits 1. Passing the schema is not the same as following the protocol; see the proof boundary below.

Validate `CITATION.cff` strictly. cffconvert needs `jsonschema<4`, so it gets its own virtual environment:

```bash
python -m venv .venv-cff
.venv-cff/bin/python -m pip install -r requirements-citation.txt
.venv-cff/bin/cffconvert --validate -i CITATION.cff
```

Expected output: `Citation metadata are valid according to schema version 1.2.0.`

CI runs the same checks in [`.github/workflows/ci.yml`](.github/workflows/ci.yml) on every push to `main` and on every pull request. It installs the same pinned versions from the hash-locked closures in [`requirements/ci/`](requirements/ci/), so pip checks every downloaded file against a SHA-256 recorded in this repository. To install exactly what CI installs for the tests, use `.venv/bin/python -m pip install --require-hashes --only-binary=:all: -r requirements/ci/test.txt`.

## Proof boundary

- **What is here:** a protocol text and a JSON Schema for its machine-readable form. **What is not here:** any experiment, data, analysis or result. Nothing in this repository shows that a candidate policy improves validated outcomes, or that a current policy is failing; `PROTOCOL.md` §5 draws the same line.
- **What the tests show:** internal consistency only. The schema is a valid JSON Schema 2020-12 document; its ledger states and locked decisions match `PROTOCOL.md`; the version, collaborators and citation metadata agree across files; relative links resolve. `tests/test_ci_requirements_lock.py` reads the workflow and lock files and checks that every CI `pip install` uses `--require-hashes` with a lock in `requirements/ci/` that matches the top-level pins; it does not show what a runner downloaded (the CI log does).
- **What the schema does not check:** a document can pass the schema and still break `PROTOCOL.md`. The schema does not check that the ITT ledger has no exclusions, that per-protocol exclusions are limited to items (a)–(c), that each ledger lists its states exactly once, that the MRD record carries items (a)–(d), that both adjudication roles are named with trigger evidence and timestamp, or that a document has no unknown or misspelled keys. These need human review. `tests/` pins each of these gaps, so a stricter schema fails that test until this list is updated.
- **Freeze status:** `v0.1.0-draft` is a lightweight (unsigned) git tag on the initial protocol commit, made before `protocol.schema.json`, `CITATION.cff` and `LICENSE` were added. The `v1.0.0-frozen` tag described in `PROTOCOL.md` §6 does not exist yet. Git commit dates are set by the committer, so the repository on its own is not an independent timestamp for "pre-declared".

## Contributing

This is a two-party collaboration. The package freezes when both parties agree on all sections.

## Relation to the estate

Part of the [SZL Holdings](https://github.com/szl-holdings) GitHub estate; models, datasets and Spaces are published under the [SZLHOLDINGS](https://huggingface.co/SZLHOLDINGS) Hugging Face org.

## License

The [`LICENSE`](LICENSE) file is Apache-2.0. [`PROTOCOL.md`](PROTOCOL.md) (License section) and [`CITATION.cff`](CITATION.cff) declare CC-BY-4.0 for the protocol package. The two declarations conflict, and the collaborators have not yet reconciled them.

## Links

- Source and releases: [github.com/szl-holdings/aifor-science-protocol](https://github.com/szl-holdings/aifor-science-protocol) · release [v0.1.0-draft](https://github.com/szl-holdings/aifor-science-protocol/releases/tag/v0.1.0-draft)
- Hugging Face: no model, dataset or Space is published from this repository. SZL Holdings on Hugging Face: [huggingface.co/SZLHOLDINGS](https://huggingface.co/SZLHOLDINGS)
- Security reports: [`SECURITY.md`](SECURITY.md)
