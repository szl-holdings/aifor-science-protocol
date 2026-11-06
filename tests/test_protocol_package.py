"""Consistency tests for the AI-for-Science Validation Protocol package.

The repository ships a human-readable protocol (PROTOCOL.md), a
machine-readable JSON Schema (protocol.schema.json), a README and citation
metadata (CITATION.cff). These tests check that those artifacts agree with
each other, and that the schema accepts and rejects what it claims to.

Proof boundary: nothing here tests an experiment, a dataset or a result;
none exists in this repository. A passing run shows internal consistency of
the package only, not that the protocol is scientifically sound.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
REPO_URL = "https://github.com/szl-holdings/aifor-science-protocol"
NUMBER_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
}


def _read(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


PROTOCOL_MD = _read("PROTOCOL.md")
README_MD = _read("README.md")
SCHEMA = json.loads(_read("protocol.schema.json"))
CITATION = yaml.safe_load(_read("CITATION.cff"))
VALIDATOR = Draft202012Validator(SCHEMA)
VERSION_VALIDATOR = Draft202012Validator(SCHEMA["properties"]["protocol_version"])
LEDGER_PROPERTIES = SCHEMA["properties"]["accounting_rule"]["properties"]


# --------------------------------------------------------------------------
# Helpers that read the numbers and names the prose states
# --------------------------------------------------------------------------


def _heading_section(markdown: str, heading_pattern: str) -> tuple[str, str]:
    """Return (heading line, body up to the next heading or horizontal rule)."""
    match = re.search(rf"^#+ {heading_pattern}.*$", markdown, flags=re.MULTILINE)
    assert match, f"no heading matching {heading_pattern!r}"
    rest = markdown[match.end() :]
    end = re.search(r"^(?:#+ |---\s*$)", rest, flags=re.MULTILINE)
    return match.group(0), rest[: end.start()] if end else rest


def _stated_count(text: str) -> int:
    """Return the single number word ("four", "nine", ...) used in text."""
    words = [w for w in re.findall(r"[a-z]+", text.lower()) if w in NUMBER_WORDS]
    assert len(words) == 1, f"expected exactly one number word in {text!r}"
    return NUMBER_WORDS[words[0]]


def _numbered_items(block: str) -> list[str]:
    return re.findall(r"^\d+\.\s+(.+)$", block, flags=re.MULTILINE)


def _protocol_version() -> str:
    match = re.search(r"\*\*Version: (v[^*\s]+)\*\*", PROTOCOL_MD)
    assert match, "PROTOCOL.md must state **Version: v...**"
    return match.group(1)


def _protocol_resource_states() -> tuple[int, list[str]]:
    heading, body = _heading_section(PROTOCOL_MD, "Coupled Resource Ledger")
    return _stated_count(heading), re.findall(
        r"^\|\s*`([^`]+)`\s*\|", body, flags=re.MULTILINE
    )


def _protocol_decision_states() -> tuple[int, list[str]]:
    heading, body = _heading_section(PROTOCOL_MD, "Decision Ledger")
    return _stated_count(heading), re.findall(r"`([^`]+)`", body)


def _protocol_locked_decisions() -> list[str]:
    match = re.search(
        r"^\*\*Locked decisions[^\n]*\n(?P<body>.*?)^---\s*$",
        PROTOCOL_MD,
        flags=re.MULTILINE | re.DOTALL,
    )
    assert match, "PROTOCOL.md must contain a **Locked decisions** block"
    return _numbered_items(match.group("body"))


def _collaborators(markdown: str) -> str:
    match = re.search(r"^\*\*Collaborators:\*\* (.+)$", markdown, flags=re.MULTILINE)
    assert match, "missing **Collaborators:** line"
    # Drop Markdown link targets so README and PROTOCOL.md compare as text.
    return re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", match.group(1)).strip()


def _synthetic_instance() -> dict:
    """Return a minimal document shaped like the current draft.

    This is a test fixture, not a protocol artifact: the ledger states come
    from PROTOCOL.md and every free-text field is a placeholder.
    """
    _, resource_states = _protocol_resource_states()
    _, decision_states = _protocol_decision_states()
    return {
        "protocol_version": _protocol_version(),
        "locked_decisions": {
            "randomization_unit": "cluster",
            "attempt_accounting": "itt_primary_perprotocol_secondary",
            "mrd_definition": "validated_outcome_scale_decision_anchored",
            "adjudication": "separate_stopping_and_inconclusive",
        },
        "accounting_rule": {
            "primary": {
                "name": "intention-to-treat",
                "unit_definition": "placeholder",
                "exclusions": [],
            },
            "secondary": {"name": "per-protocol", "exclusions": ["placeholder"]},
            "resource_ledger": {"states": resource_states},
            "decision_ledger": {"states": decision_states},
        },
        "mrd": {"definition": "placeholder", "interpretation_rule": "placeholder"},
        "adjudication": {
            "stopping_rule_owner": {"name": "placeholder"},
            "inconclusive_adjudicator": {"name": "placeholder"},
        },
        "queue_snapshot_spec": {"status": "pending"},
        "framing_note": "placeholder",
    }


def _error_summary(errors: list) -> list[tuple[list, str]]:
    return [(list(e.absolute_path), e.message) for e in errors]


# --------------------------------------------------------------------------
# The schema itself
# --------------------------------------------------------------------------


def test_schema_declares_and_satisfies_json_schema_2020_12() -> None:
    assert SCHEMA["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    Draft202012Validator.check_schema(SCHEMA)


# --------------------------------------------------------------------------
# PROTOCOL.md <-> schema <-> README <-> CITATION.cff
# --------------------------------------------------------------------------


def test_resource_ledger_states_match_protocol() -> None:
    stated, states = _protocol_resource_states()
    schema_states = LEDGER_PROPERTIES["resource_ledger"]["properties"]["states"][
        "items"
    ]["enum"]
    assert len(states) == stated, f"PROTOCOL.md says {stated} states, lists {states}"
    assert len(set(schema_states)) == len(schema_states)
    assert sorted(schema_states) == sorted(states)


def test_decision_ledger_states_match_protocol() -> None:
    stated, states = _protocol_decision_states()
    schema_states = LEDGER_PROPERTIES["decision_ledger"]["properties"]["states"][
        "items"
    ]["enum"]
    assert len(states) == stated, f"PROTOCOL.md says {stated} states, lists {states}"
    assert len(set(states)) == len(states), "decision states must be distinct"
    assert sorted(schema_states) == sorted(states)


def test_locked_decisions_agree_across_protocol_schema_and_readme() -> None:
    protocol_items = _protocol_locked_decisions()
    schema_keys = SCHEMA["properties"]["locked_decisions"]["required"]
    readme_heading, readme_body = _heading_section(
        README_MD, r"The \w+ locked decisions"
    )
    readme_items = _numbered_items(readme_body)

    assert (
        len(protocol_items)
        == len(schema_keys)
        == len(readme_items)
        == _stated_count(readme_heading)
    )
    for item in protocol_items:
        label = re.match(r"\*\*([^*]+?):\*\*", item)
        assert label, f"locked decision without a bold label: {item!r}"
        key_prefix = label.group(1).lower().replace(" ", "_")
        assert any(key.startswith(key_prefix) for key in schema_keys), (
            f"no schema key for locked decision {label.group(1)!r}"
        )


@pytest.mark.parametrize("kind", ["primary", "secondary"])
def test_analysis_names_match_protocol_headings(kind: str) -> None:
    match = re.search(
        rf"^### {kind.title()} Analysis: (.+)$", PROTOCOL_MD, flags=re.MULTILINE
    )
    assert match, f"PROTOCOL.md has no '{kind.title()} Analysis' heading"
    prose_name = re.sub(r"\s*\(.*?\)", "", match.group(1)).strip().lower()
    schema_name = LEDGER_PROPERTIES[kind]["properties"]["name"]["const"]
    assert schema_name == prose_name.replace(" ", "-")


def test_versions_agree_across_files() -> None:
    version = _protocol_version()
    assert VERSION_VALIDATOR.is_valid(version), f"{version} fails the schema pattern"
    assert re.search(rf"\*\*Status:\*\* {re.escape(version)}(?![\w.-])", README_MD)
    assert CITATION["version"] == version.removeprefix("v")


def test_planned_freeze_tag_is_a_valid_protocol_version() -> None:
    match = re.search(r"Tag as `([^`]+)`", PROTOCOL_MD)
    assert match, "PROTOCOL.md section 6 must name the freeze tag"
    assert VERSION_VALIDATOR.is_valid(match.group(1))


def test_collaborators_agree_across_readme_protocol_and_citation() -> None:
    collaborators = _collaborators(PROTOCOL_MD)
    assert _collaborators(README_MD) == collaborators
    parties = [party.strip() for party in collaborators.split(" + ")]
    authors = [author["name"] for author in CITATION["authors"]]
    assert len(authors) == len(parties)
    for author, party in zip(authors, parties):
        assert author in party, f"CITATION author {author!r} not in {party!r}"
    assert CITATION["repository-code"] == REPO_URL


MARKDOWN_FILES = sorted(p.name for p in ROOT.glob("*.md"))
LINK_TARGET = re.compile(r"\]\(([^)\s]+)[^)]*\)|(?:href|src)=\"([^\"]+)\"")


@pytest.mark.parametrize("name", MARKDOWN_FILES)
def test_relative_links_resolve(name: str) -> None:
    targets = [a or b for a, b in LINK_TARGET.findall(_read(name))]
    relative = [
        t
        for t in targets
        if not re.match(r"[a-z][a-z0-9+.-]*:", t) and not t.startswith("#")
    ]
    broken = [t for t in relative if not (ROOT / t.split("#", 1)[0]).exists()]
    assert not broken, f"{name}: broken relative links {broken}"


# --------------------------------------------------------------------------
# What the schema accepts and rejects
# --------------------------------------------------------------------------


def test_synthetic_instance_from_protocol_md_is_valid() -> None:
    errors = list(VALIDATOR.iter_errors(_synthetic_instance()))
    assert not errors, _error_summary(errors)


@pytest.mark.parametrize(
    ("path", "value"),
    [
        pytest.param(("protocol_version",), "0.1.0-draft", id="version-without-v"),
        pytest.param(("protocol_version",), "v0.1", id="version-not-semver"),
        pytest.param(
            ("locked_decisions", "randomization_unit"),
            "individual",
            id="unknown-randomization-unit",
        ),
        pytest.param(
            ("accounting_rule", "primary", "name"), "per-protocol", id="primary-not-itt"
        ),
        pytest.param(
            ("accounting_rule", "secondary", "name"),
            "intention-to-treat",
            id="secondary-not-per-protocol",
        ),
        pytest.param(
            ("queue_snapshot_spec", "status"), "done", id="unknown-queue-status"
        ),
    ],
)
def test_schema_rejects_invalid_values(path: tuple[str, ...], value: str) -> None:
    doc = _synthetic_instance()
    target = doc
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    errors = list(VALIDATOR.iter_errors(doc))
    assert any(tuple(e.absolute_path) == path for e in errors), _error_summary(errors)


@pytest.mark.parametrize(
    ("ledger", "state"), [("resource_ledger", "lost"), ("decision_ledger", "abandoned")]
)
def test_schema_rejects_unknown_ledger_states(ledger: str, state: str) -> None:
    doc = _synthetic_instance()
    states = doc["accounting_rule"][ledger]["states"]
    states.append(state)
    errors = list(VALIDATOR.iter_errors(doc))
    expected = ("accounting_rule", ledger, "states", len(states) - 1)
    found = any(tuple(e.absolute_path) == expected for e in errors)
    assert found, _error_summary(errors)


@pytest.mark.parametrize("key", SCHEMA["required"])
def test_schema_requires_each_top_level_section(key: str) -> None:
    doc = _synthetic_instance()
    del doc[key]
    errors = list(VALIDATOR.iter_errors(doc))
    assert any(
        e.validator == "required" and e.message == f"{key!r} is a required property"
        for e in errors
    ), _error_summary(errors)
