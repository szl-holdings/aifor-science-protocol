"""CI installs only hash-locked dependency closures.

requirements-test.txt and requirements-citation.txt carry the top-level pins
(README Quickstart). .github/workflows/ci.yml installs from
requirements/ci/test.txt, citation.txt and citation-build.txt instead:
complete closures compiled by ``uv pip compile --universal --generate-hashes``
and installed with ``pip install --require-hashes``. This contract fails when
a lock drifts from the top-level pins (for example after a Dependabot bump),
when a lock entry is unpinned or unhashed, or when CI installs anything
outside the hash-locked closures.

Proof boundary: these are static checks of files in this repository. They do
not show what a runner downloaded; the CI log does. Standard library, PyYAML
and pytest only; no network.
"""

from __future__ import annotations

import re
import shlex
from pathlib import Path
from typing import NamedTuple

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ".github/workflows/ci.yml"
# hash-locked closure -> the top-level pins it is compiled from
LOCKS = {
    "requirements/ci/test.txt": "requirements-test.txt",
    "requirements/ci/citation.txt": "requirements-citation.txt",
}
# setuptools only, installed before citation.txt so that the sdist-only
# docopt is built with a hash-checked build backend (--no-build-isolation)
BUILD_LOCK = "requirements/ci/citation-build.txt"
ALL_LOCKS = {*LOCKS, BUILD_LOCK}

_TOP_LEVEL = re.compile(r"([A-Za-z0-9][A-Za-z0-9._-]*)==([^\s;]+)")
_LOCKED = re.compile(
    r"([A-Za-z0-9][A-Za-z0-9._-]*)==([^\s;\\]+)\s*(?:;\s*([^\\]+?))?\s*\\?"
)
_HASH = re.compile(r"\s+--hash=sha256:([0-9a-f]{64})\s*\\?")
_PIP_INSTALL = re.compile(r"(?<![\w-])pip3?\s+install\b")
_SHELL_OPERATORS = {"&&", "||", ";", ";;", "|", "&"}
_OPTIONS_WITH_VALUE = {
    "-c",
    "--constraint",
    "-i",
    "--index-url",
    "--extra-index-url",
    "-f",
    "--find-links",
    "--only-binary",
    "--no-binary",
}


class LockEntry(NamedTuple):
    version: str
    marker: str
    hashes: frozenset[str]


class PipInstall(NamedTuple):
    step: str
    line: int
    args: tuple[str, ...]


def _norm(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


# --------------------------------------------------------------------------
# Parsers
# --------------------------------------------------------------------------


def top_level_pins(text: str) -> dict[str, str]:
    """{normalized name: version}; every requirement must be an exact pin."""
    pins: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        match = _TOP_LEVEL.fullmatch(line)
        if match is None:
            raise ValueError(f"top-level requirement is not an exact pin: {line!r}")
        pins[_norm(match.group(1))] = match.group(2)
    return pins


def locked_entries(text: str) -> dict[str, LockEntry]:
    """{normalized name: entry}; every entry must be an exact pin with hashes."""
    entries: dict[str, tuple[str, str, set[str]]] = {}
    current: str | None = None
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        hash_line = _HASH.fullmatch(raw)
        if hash_line:
            if current is None:
                raise ValueError("hash line without a requirement")
            entries[current][2].add(hash_line.group(1))
            continue
        match = _LOCKED.fullmatch(raw.rstrip())
        if match is None:
            raise ValueError(f"lock line is not an exact hashed pin: {raw!r}")
        current = _norm(match.group(1))
        if current in entries:
            raise ValueError(f"duplicate lock entry: {current}")
        entries[current] = (match.group(2), (match.group(3) or "").strip(), set())
    unhashed = sorted(name for name, (_, _, hashes) in entries.items() if not hashes)
    if unhashed:
        raise ValueError(f"lock entries without hashes: {unhashed}")
    return {
        name: LockEntry(version, marker, frozenset(hashes))
        for name, (version, marker, hashes) in entries.items()
    }


def drift(pins: dict[str, str], lock: dict[str, LockEntry]) -> list[str]:
    problems = []
    for name, version in sorted(pins.items()):
        if name not in lock:
            problems.append(f"{name}=={version} is missing from the lock")
        elif lock[name].version != version:
            problems.append(f"{name}=={version} is locked at {lock[name].version}")
    return problems


def pip_installs(workflow_text: str) -> list[PipInstall]:
    """Every ``pip install`` in a ``run:`` step, with its arguments."""
    installs = []
    for job in yaml.safe_load(workflow_text)["jobs"].values():
        for step in job.get("steps", []):
            script = step.get("run")
            if not script:
                continue
            # Join shell line continuations so that wrapped commands count.
            lines = script.replace("\\\n", " ").splitlines()
            for number, line in enumerate(lines):
                if not _PIP_INSTALL.search(line):
                    continue
                lexer = shlex.shlex(line, posix=True, punctuation_chars=True)
                lexer.whitespace_split = True
                tokens = list(lexer)
                for i in range(len(tokens) - 1):
                    if tokens[i] in ("pip", "pip3") and tokens[i + 1] == "install":
                        args = []
                        for token in tokens[i + 2 :]:
                            if token in _SHELL_OPERATORS:
                                break
                            args.append(token)
                        installs.append(
                            PipInstall(step.get("name", "?"), number, tuple(args))
                        )
    return installs


def requirement_files(args: tuple[str, ...]) -> tuple[list[str], list[str]]:
    """(requirement files, positional package arguments) of one pip install."""
    files: list[str] = []
    packages: list[str] = []
    takes_value = False
    for i, arg in enumerate(args):
        if takes_value:
            takes_value = False
            continue
        if arg in ("-r", "--requirement"):
            if i + 1 < len(args):
                files.append(args[i + 1])
            takes_value = True
        elif arg.startswith("--requirement="):
            files.append(arg.split("=", 1)[1])
        elif arg.startswith("-r") and len(arg) > 2 and not arg.startswith("--"):
            files.append(arg[2:])
        elif arg in _OPTIONS_WITH_VALUE:
            takes_value = True
        elif not arg.startswith("-"):
            packages.append(arg)
    return files, packages


def install_problems(args: tuple[str, ...]) -> list[str]:
    """Why one pip install is not a wheel-only install of hash-locked closures."""
    files, packages = requirement_files(args)
    problems = []
    if "--require-hashes" not in args:
        problems.append("no --require-hashes")
    if "--only-binary=:all:" not in args:
        problems.append("not wheel-only (--only-binary=:all:)")
    if not files:
        problems.append("installs no requirement file")
    outside = [f for f in files if f not in ALL_LOCKS]
    if outside:
        problems.append(f"requirement files outside requirements/ci/: {outside}")
    if packages:
        problems.append(f"packages outside a lock: {packages}")
    if any(a.startswith("--no-binary") for a in args) and (
        "--no-build-isolation" not in args
    ):
        problems.append("builds an sdist in an isolated (unhashed) build environment")
    return problems


# --------------------------------------------------------------------------
# The locks
# --------------------------------------------------------------------------


@pytest.mark.parametrize("lock", sorted(LOCKS))
def test_lock_matches_its_top_level_pins(lock: str) -> None:
    pins = top_level_pins(_read(LOCKS[lock]))
    assert pins, f"{LOCKS[lock]} pins nothing"
    assert drift(pins, locked_entries(_read(lock))) == []


def test_build_lock_is_the_setuptools_of_the_citation_lock() -> None:
    build = locked_entries(_read(BUILD_LOCK))
    citation = locked_entries(_read("requirements/ci/citation.txt"))
    assert sorted(build) == ["setuptools"]
    assert build["setuptools"] == citation["setuptools"]


def test_every_lock_has_an_in_file_that_names_it() -> None:
    for lock in sorted(ALL_LOCKS):
        source = Path(lock).with_suffix(".in").as_posix()
        assert (ROOT / source).is_file(), f"{lock} has no {source}"
        assert f"-o {lock}" in _read(source), f"{source} does not say how to build {lock}"
        assert f"-o {lock}" in _read(lock).split("\n", 3)[1], f"{lock} header"


# --------------------------------------------------------------------------
# What CI installs
# --------------------------------------------------------------------------


def test_ci_installs_only_hash_locked_closures() -> None:
    installs = pip_installs(_read(WORKFLOW))
    assert installs, f"{WORKFLOW} installs nothing"
    problems = {
        f"{i.step!r} line {i.line}": install_problems(i.args)
        for i in installs
        if install_problems(i.args)
    }
    assert problems == {}
    used = {f for i in installs for f in requirement_files(i.args)[0]}
    assert used == ALL_LOCKS, "every lock is installed by CI, and only those"


def test_sdists_are_built_only_with_the_hash_locked_setuptools() -> None:
    installs = pip_installs(_read(WORKFLOW))
    for position, install in enumerate(installs):
        if "--no-build-isolation" not in install.args:
            continue
        earlier = [
            i
            for i in installs[:position]
            if i.step == install.step and BUILD_LOCK in requirement_files(i.args)[0]
        ]
        assert earlier, (
            f"{install.step!r}: --no-build-isolation without installing "
            f"{BUILD_LOCK} first"
        )


def test_dependabot_watches_the_hash_locked_closures() -> None:
    updates = yaml.safe_load(_read(".github/dependabot.yml"))["updates"]
    pip_dirs = {u["directory"] for u in updates if u["package-ecosystem"] == "pip"}
    assert {"/", "/requirements/ci"} <= pip_dirs


# --------------------------------------------------------------------------
# Negative controls: the checks above can fail
# --------------------------------------------------------------------------


def test_negative_control_parsers_reject_drift_and_unhashed_entries() -> None:
    lock = locked_entries(
        "pyyaml==6.0.3 \\\n"
        "    --hash=sha256:" + "a" * 64 + "\n"
        "colorama==0.4.6 ; sys_platform == 'win32' \\\n"
        "    --hash=sha256:" + "b" * 64 + " \\\n"
        "    --hash=sha256:" + "c" * 64 + "\n"
        "    # via pytest\n"
    )
    assert lock["colorama"].marker == "sys_platform == 'win32'"
    assert len(lock["colorama"].hashes) == 2
    assert drift({"pyyaml": "6.0.4"}, lock) == ["pyyaml==6.0.4 is locked at 6.0.3"]
    assert drift({"pytest": "9.2.0"}, lock) == ["pytest==9.2.0 is missing from the lock"]
    with pytest.raises(ValueError, match="without hashes"):
        locked_entries("pytest==9.2.0\n")
    with pytest.raises(ValueError, match="not an exact hashed pin"):
        locked_entries("pytest>=9 \\\n    --hash=sha256:" + "d" * 64 + "\n")
    with pytest.raises(ValueError, match="not an exact pin"):
        top_level_pins("pytest>=9\n")


def test_negative_control_unhashed_ci_installs_are_reported() -> None:
    # The two install commands .github/workflows/ci.yml ran before the locks.
    workflow = """
jobs:
  validate:
    steps:
      - name: Install pinned test dependencies
        run: >-
          python -m pip install --disable-pip-version-check --no-cache-dir
          -r requirements-test.txt
      - name: Validate CITATION.cff
        run: |
          python -m venv "$RUNNER_TEMP/cffconvert"
          "$RUNNER_TEMP/cffconvert/bin/python" -m pip install \\
            --disable-pip-version-check --no-cache-dir -r requirements-citation.txt
          "$RUNNER_TEMP/cffconvert/bin/cffconvert" --validate -i CITATION.cff
      - name: Ad-hoc tool
        run: >-
          pip install --require-hashes --only-binary=:all:
          -r requirements/ci/test.txt pytest && pytest
"""
    installs = pip_installs(workflow)
    assert [i.step for i in installs] == [
        "Install pinned test dependencies",
        "Validate CITATION.cff",
        "Ad-hoc tool",
    ]
    old_test, old_citation, ad_hoc = (install_problems(i.args) for i in installs)
    assert "no --require-hashes" in old_test
    assert "requirement files outside requirements/ci/: ['requirements-test.txt']" in old_test
    assert "no --require-hashes" in old_citation
    assert ad_hoc == ["packages outside a lock: ['pytest']"]
    assert install_problems(
        ("--require-hashes", "--only-binary=:all:", "--no-binary=docopt",
         "-r", "requirements/ci/citation.txt")
    ) == ["builds an sdist in an isolated (unhashed) build environment"]
