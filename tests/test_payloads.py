"""The keys a `--json` payload promises a reader outside this process (RK1005).

Every query prints `--json`, and inside the package that is enough: the test reading a
payload is the test that wrote it, so a renamed key moves both ends in one commit. A reader
outside the process breaks that arrangement — another language, its own clock, reading
`list`, `deps`, `lint` and `pick` as data — and the first rename here lands as a broken view
there and a green suite here.

**Not a schema file**, which would be a second declaration to drift from the first. This is a
test that reads the payloads the way a client does: by key, over this repository's own
`docs/` as the fixture, asserting the keys a client is *promised* rather than the whole
shape. A payload that gains a field is compatible and stays green; one that loses a promised
key goes red. What this file reads **is** the contract, and every key it does not read stays
free to move — which is the point of listing them rather than snapshotting the object.

The one fixture that is not `docs/` is a finding: this repository's own gate passes, by law
(`lint` must be clean here), so a payload carrying a finding has to be produced by a project
that has one. It is the smallest possible: one line waiting on an id nothing carries.
"""

from __future__ import annotations

import contextlib
import io
import json
import shutil
import tempfile
from pathlib import Path

import pytest

from roadkeep.cli import EXIT_GATE, EXIT_OK, main

HERE = Path(__file__).resolve().parents[1]

#: What each command promises at the top level. A client reads these by name, so removing
#: one is a breaking change and adding one is not — which is why this is a subset check and
#: never an equality: the payloads carry more, and the more is free to move.
PROMISED = {
    "list": ("file", "tasks", "total"),
    "deps": ("id", "deps", "blockers", "unblocks", "readiness"),
    "pick": ("pick", "reason", "tier", "ready", "blocked"),
    "lint": ("root", "clean", "problems", "findings", "codes"),
    # The two the write door reads (RK1008): which blocks a task may be filed under, and
    # what each field has left on the line `add` is about to derive.
    "stats": ("file", "blocks", "total"),
    "budget": ("id", "fields", "line_max", "prose"),
    # Which copy answered, which an editor shows above the rows it answered with (RK1009).
    "engines": ("writing", "verdict", "agree"),
}

#: The keys inside the one object each of those carries a list of. Held apart from the top
#: level because a client walks into these, and a rename here is exactly as breaking.
INSIDE = {
    "list": ("tasks", ("id", "block", "status", "symptom", "why", "deps", "line")),
    # `column` and `remedy` joined when the gate became a problems panel (RK1007): a
    # diagnostic is anchored by the first and a quick fix is composed from the second, so
    # both are keys a reader outside this process now depends on.
    "lint": ("findings", ("code", "file", "line", "column", "message", "remedy")),
    "stats": ("blocks", ("block", "counted")),
    # `left`, `limit`, `aim` and `unit` are what a prompt counts down beside the words
    # somebody is typing — the whole of L1 arriving before the sentence exists.
    "budget": ("fields", ("field", "limit", "left", "aim", "unit")),
}


def payload(*argv: str, root: Path | None = None, expected: int = EXIT_OK) -> dict:
    """One command's `--json`, read the way a client reads it: parse stdout, nothing else."""
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = main(["-C", str(root or HERE), *argv, "--json"])
    assert code == expected, f"{argv}: exited {code}"
    return json.loads(out.getvalue())


@pytest.fixture(scope="module")
def dirty() -> Path:
    """A project with exactly one finding, for the payload `docs/` cannot produce."""
    root = Path(tempfile.mkdtemp())
    (root / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\n', encoding="utf-8"
    )
    (root / "ROADMAP.md").write_text(
        "# Roadmap\n\n## Block A — The model\n\n"
        "- 📋 **RK1** (deps: RK9) **A symptom** — Because of a reason. → §RK1\n",
        encoding="utf-8",
        newline="",
    )
    yield root
    shutil.rmtree(root, ignore_errors=True)


def _argv(verb: str) -> tuple[str, ...]:
    """The command, with the one subject `deps` needs read off the backlog rather than typed.

    Derived for the reason every id in this project is (RK4): a test naming a line spells an
    id that ships, and a skip that fires for ever is a test that stopped testing.
    """
    if verb == "engines":
        return ("engines",)
    if verb == "budget":
        # A block that exists, read off the backlog for `deps`' reason: a letter typed here
        # is a letter that stops being declared.
        blocks = payload("stats")["blocks"]
        return ("budget", "--block", blocks[0]["block"])
    if verb != "deps":
        return (verb,)
    tasks = payload("list")["tasks"]
    if not tasks:
        pytest.skip("the backlog is empty: the graph read needs an open line to walk")
    return ("deps", tasks[0]["id"])


@pytest.mark.parametrize("verb", sorted(PROMISED))
def test_the_top_level_keys_a_client_is_promised_are_there(verb, dirty):
    """Read by name and never compared whole: a payload that gained a field is compatible,
    and asserting the object would make every addition a breaking change in this suite."""
    where, code = (dirty, EXIT_GATE) if verb == "lint" else (None, EXIT_OK)
    got = payload(*_argv(verb), root=where, expected=code)
    missing = [key for key in PROMISED[verb] if key not in got]
    assert not missing, f"{verb} no longer carries {missing}"


@pytest.mark.parametrize("verb", sorted(INSIDE))
def test_the_keys_inside_a_row_are_there_too(verb, dirty):
    """A client walks into `tasks` and `findings`, so a rename one level down breaks it just
    as hard — and one level is where it stops: nothing here reads a remedy's doors, so those
    stay free to move until something outside says otherwise."""
    field, keys = INSIDE[verb]
    where, code = (dirty, EXIT_GATE) if verb == "lint" else (None, EXIT_OK)
    rows = payload(verb, root=where, expected=code)[field]
    assert rows, f"{verb}: the fixture produced no {field} to read"
    missing = [key for key in keys if key not in rows[0]]
    assert not missing, f"{verb}.{field} no longer carries {missing}"


def test_a_payload_is_the_whole_of_stdout_and_parses_as_one_object():
    """The property a client depends on before any key: `--json` prints a document and not a
    document with a sentence above it. Held over every verb promised, because a status line
    that leaked onto stdout would break the parse and no key assertion would ever run."""
    for verb in sorted(PROMISED):
        if verb == "lint":
            continue
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            main(["-C", str(HERE), *_argv(verb), "--json"])
        assert isinstance(json.loads(out.getvalue()), dict), verb


#: What a remedy carries, one level further in than any other promise here — because a code
#: action is built from it: the doors, whether each is runnable as it stands, and its argv.
REMEDY = ("kind", "doors")
DOOR = ("argv", "what", "complete")


def test_a_remedy_carries_the_doors_a_quick_fix_is_built_from(dirty):
    """Two levels down, and the only place this contract goes that deep. `complete` is the
    key that decides whether an editor may offer the action at all: a door with a marked
    blank is prose only the author can write, and an action that ran one would be the tool
    composing it (L4)."""
    findings = payload("lint", root=dirty, expected=EXIT_GATE)["findings"]
    remedies = [one["remedy"] for one in findings if one.get("remedy")]
    assert remedies, "the fixture produced no remedy to read"
    for remedy in remedies:
        assert not [key for key in REMEDY if key not in remedy], remedy
        for door in remedy["doors"]:
            assert not [key for key in DOOR if key not in door], door


def test_the_gate_exits_one_and_still_prints_a_payload(dirty):
    """The pairing a client cannot discover from the keys: `lint --json` answers *and* exits
    non-zero, so a reader that treats a non-zero exit as no output loses the findings."""
    got = payload("lint", root=dirty, expected=EXIT_GATE)
    assert got["clean"] is False and got["problems"] >= 1
