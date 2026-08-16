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

Two fixtures are not `docs/`, and both are states this repository cannot be in. A **finding**
is one: the gate passes here by law (`lint` must be clean), so a payload carrying one has to
come from a project that has one, and it is the smallest possible — a line waiting on an id
nothing carries. An **open line** is the other, which sounds backwards until a block ships its
last one: `conftest.populated` is this repository whenever the backlog has something in it and
a stand-in when it does not, so an emptied roadmap changes which files are read and never
whether the contract is asserted (RK1098).
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
    # `total`, `uncounted` and `markers` are what the tree's header renders (RK1018) — it
    # computes none of them, so a project's own marker set is its own numbers.
    "stats": ("file", "blocks", "total", "uncounted", "markers"),
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


def _argv(verb: str, root: Path | None = None) -> tuple[str, ...]:
    """The command, with the one subject `deps` needs read off the backlog rather than typed.

    Derived for the reason every id in this project is (RK4): a test naming a line spells an
    id that ships, and a skip that fires for ever is a test that stopped testing.
    """
    if verb == "engines":
        return ("engines",)
    if verb == "budget":
        # A block that exists, read off the backlog for `deps`' reason: a letter typed here
        # is a letter that stops being declared.
        blocks = payload("stats", root=root)["blocks"]
        return ("budget", "--block", blocks[0]["block"])
    if verb != "deps":
        return (verb,)
    tasks = payload("list", root=root)["tasks"]
    # No skip any more (RK1098): `populated` is the root that guarantees a line to walk, so an
    # emptied backlog changes which files are read and never whether the contract is asserted.
    return ("deps", tasks[0]["id"])


@pytest.mark.parametrize("verb", sorted(PROMISED))
def test_the_top_level_keys_a_client_is_promised_are_there(verb, dirty, populated):
    """Read by name and never compared whole: a payload that gained a field is compatible,
    and asserting the object would make every addition a breaking change in this suite."""
    where, code = (dirty, EXIT_GATE) if verb == "lint" else (populated, EXIT_OK)
    got = payload(*_argv(verb, where), root=where, expected=code)
    missing = [key for key in PROMISED[verb] if key not in got]
    assert not missing, f"{verb} no longer carries {missing}"


@pytest.mark.parametrize("verb", sorted(INSIDE))
def test_the_keys_inside_a_row_are_there_too(verb, dirty, populated):
    """A client walks into `tasks` and `findings`, so a rename one level down breaks it just
    as hard — and one level is where it stops: nothing here reads a remedy's doors, so those
    stay free to move until something outside says otherwise.

    The rows have to exist for any of that to be a claim, and `docs/` stopped producing them
    the day a block shipped its last line (RK1098) — so the root is `populated`, which is this
    repository whenever it has an open line and a stand-in when it does not.
    """
    field, keys = INSIDE[verb]
    where, code = (dirty, EXIT_GATE) if verb == "lint" else (populated, EXIT_OK)
    rows = payload(*_argv(verb, where), root=where, expected=code)[field]
    assert rows, f"{verb}: the fixture produced no {field} to read"
    missing = [key for key in keys if key not in rows[0]]
    assert not missing, f"{verb}.{field} no longer carries {missing}"


def test_a_payload_is_the_whole_of_stdout_and_parses_as_one_object(populated):
    """The property a client depends on before any key: `--json` prints a document and not a
    document with a sentence above it. Held over every verb promised, because a status line
    that leaked onto stdout would break the parse and no key assertion would ever run."""
    for verb in sorted(PROMISED):
        if verb == "lint":
            continue
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            main(["-C", str(populated), *_argv(verb, populated), "--json"])
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


def test_the_stand_in_carries_what_an_emptied_backlog_takes_away(tmp_path):
    """The fallback, exercised on the day it is not needed (RK1098).

    `populated` returns this repository while the backlog has a line in it, so on almost every
    run the stand-in is dead code — and dead code in a fixture is what the two tests it exists
    for would discover the hard way, on the one run where it fires. So it is read here
    directly, and against the properties those tests assert rather than against its text: rows
    to walk, two blocks so grouping is a claim, and a line waiting on another so blocked
    against ready is one too.
    """
    from conftest import _MINIMAL

    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\n', encoding="utf-8"
    )
    (tmp_path / "ROADMAP.md").write_text(_MINIMAL, encoding="utf-8", newline="")

    tasks = payload("list", root=tmp_path)["tasks"]
    assert len(tasks) == 3
    assert len({task["block"] for task in tasks}) == 2, "grouping is only a claim over two"
    waiting = payload("deps", tasks[0]["id"], root=tmp_path)
    assert any(payload("deps", task["id"], root=tmp_path)["blockers"] for task in tasks), (
        "no line waits on another, so blocked-against-ready would be vacuous"
    )
    assert waiting["id"] == tasks[0]["id"]
    # And it is a project this tool would accept, not just one it can parse: a stand-in the
    # gate refuses is a fixture that tests the wrong thing.
    assert payload("lint", root=tmp_path)["clean"] is True


def test_an_emptied_backlog_is_not_a_failure(tmp_path):
    """The state that made two tests red, asserted as the ordinary answer it is (RK1098).

    `ship` prints `block drop` when a block loses its last line, so a roadmap with nothing open
    is what this tool is built to reach. The payloads say so in their own shape — an empty list
    and a zero — rather than by refusing.
    """
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\n', encoding="utf-8"
    )
    (tmp_path / "ROADMAP.md").write_text(
        "# Roadmap\n\n## Block A - The model\n", encoding="utf-8", newline=""
    )
    listed = payload("list", root=tmp_path)
    assert listed["tasks"] == [] and listed["total"] == 0
    assert payload("lint", root=tmp_path)["clean"] is True


def test_the_roadmaps_other_bullet_is_not_read_as_an_open_line(tmp_path):
    """The false positive the first `populated` had, held so it cannot come back (RK1098).

    Its predicate read the file for a line starting with `- `, and the roadmap's non-goals are
    bullets — so a backlog with nothing open but a Non-goals section answered "populated", and
    the two tests it defends went red on the exact day it was written for. Asked of the tool
    now: `entries` is what the parser calls a task line, and a non-goal is not one.
    """
    from roadkeep.config import Config

    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\n[non_goals]\nlead = 60\nwhy = 200\n',
        encoding="utf-8",
    )
    (tmp_path / "ROADMAP.md").write_text(
        "# Roadmap\n\n## Block A — The model\n\n"
        "## Non-goals\n\n- **No model** — Because the tool renders and never writes prose.\n",
        encoding="utf-8",
        newline="",
    )
    assert not Config.discover(tmp_path).document("roadmap").entries
    assert payload("list", root=tmp_path)["tasks"] == []


# -- the records a write answers with, bound to the keys they become (RK1131) ----

#: Per record, which payload key each field becomes — or `None` and the reason it becomes
#: none. RK1123 bound `Scope` this way and the argument was general; RK1130 then added `wrote`
#: to four records and twelve payloads **by hand**, and the only thing that made that right was
#: a human checking twelve times. Asserted in both directions, which is RK491's rule for a code
#: nothing reports: a field with no entry is red, and an entry naming no field is red too, so
#: the table cannot outlive the record it describes.
#:
#: A `None` is not an omission. Three of these fields are *documents* — the parsed file, the
#: entry inside it, the prose file beside it — and a payload carrying one would be handing a
#: client this process's objects. What a reader gets instead is the address: `file` and `line`.
RECORDS: dict[str, dict[str, str | None]] = {
    "Insertion": {
        "document": None,
        "entry": None,
        "prose": None,
        "section": "section",
        "needs": "needs",
        "needs_role": None,
        "opens": "needs_path",
        "promise": "promise",
        "bound": "bound",
        "wrote": "wrote",
    },
    "StatusChange": {
        "document": None,
        "entry": None,
        "before": "from",
        "refreshed": "refreshed",
        "claim": "claim",
        "wrote": "wrote",
    },
    "Amendment": {
        "document": None,
        "entry": None,
        "before": "was",
        "refreshed": "refreshed",
        "wrote": "wrote",
    },
    "Restatement": {
        "document": None,
        "entry": None,
        "before": "was",
        "refreshed": "refreshed",
        "typo": "typo",
        "wrote": "wrote",
        "design": "premise",
        "design_role": "premise",
    },
}

#: Why a row above sends no key, one entry per row and addressed `Record.field`. Declared the
#: way `test_backstop` declares a code nothing reports: the absence is the claim, so it is
#: written down rather than left as a silence somebody has to interpret. Keyed per record and
#: not per field name, because `before` is three different answers — `from` on a marker write,
#: `was` on a restatement, and nothing on an amend, where what differs is `changed`.
UNSENT = {
    "Insertion.document": "the parsed roadmap; a payload carrying one hands out this process's objects",
    "Insertion.entry": "the line itself: its address is `file` and `line`, its text `rendered`",
    "Insertion.prose": "the rationale file, addressed inside `section`",
    "Insertion.needs_role": "folded into the `needs` command the answer already spells",
    "StatusChange.document": "the parsed roadmap, addressed by `file` and `line`",
    "StatusChange.entry": "the line, reported as `rendered`",
    "Amendment.document": "the parsed roadmap, addressed by `file` and `line`",
    "Amendment.entry": "the line, reported as `rendered`",
    "Restatement.document": "the parsed roadmap, addressed by `file` and `line`",
    "Restatement.entry": "the line, reported as `rendered`",
}

#: The command each record is the answer of, with the argv that produces one.
ANSWERS = {
    "Insertion": ("add", "--block", "A", "--symptom", "A second symptom", "--why", "Because."),
    "StatusChange": ("status", "RK1", "🛠"),
    "Amendment": ("amend", "RK1", "--why", "Because of a corrected reason."),
    "Restatement": ("restate", "RK1", "--symptom", "A corrected symptom"),
}


@pytest.fixture
def writable(tmp_path: Path) -> Path:
    """A project a write verb can be run against — `docs/` is this suite's read-only fixture."""
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\n[rules.roadmap]\nref = false\n',
        encoding="utf-8",
    )
    (tmp_path / "ROADMAP.md").write_text(
        "# Roadmap\n\n## Block A — The model\n\n"
        "- 📋 **RK1** (deps: —) **A symptom** — Because of a reason.\n",
        encoding="utf-8",
        newline="",
    )
    return tmp_path


def test_every_field_of_every_record_has_a_row():
    """The half that fails on the *next* field rather than on this one, which is why it exists:
    a fifth field added tomorrow reaches whichever payload its author remembered."""
    from dataclasses import fields

    from roadkeep import authoring

    for name, table in RECORDS.items():
        record = getattr(authoring, name)
        assert set(table) == {field.name for field in fields(record)}, name


def test_every_row_that_names_a_key_finds_it_in_the_payload(writable):
    # Executed rather than asserted (`test_doors`' rule): each record is produced by running
    # the command that answers with one, and the keys are read the way a client reads them.
    for name, argv in ANSWERS.items():
        answered = payload(*argv, root=writable)
        wanted = {key for key in RECORDS[name].values() if key is not None}
        assert wanted <= set(answered), (name, sorted(wanted - set(answered)))


def test_every_row_that_sends_no_key_says_why(the_table=RECORDS):
    """Both directions, which is what stops the reasons drifting from the rows: a field that
    stops being sent needs an entry, and an entry for a field that is sent again is stale
    prose about a decision nobody takes any more."""
    silent = {
        f"{record}.{field}"
        for record, table in the_table.items()
        for field, key in table.items()
        if key is None
    }
    assert silent == set(UNSENT), {"no reason": silent - set(UNSENT), "stale": set(UNSENT) - silent}
    assert all(reason.strip() for reason in UNSENT.values())


def test_the_path_list_is_one_key_in_every_one_of_them(writable):
    """RK1130's own field, held across all four: it is the list a `git add --` takes, so a
    record that answered it under a second name would be the drift RK1123 closed for `Scope`."""
    for name, argv in ANSWERS.items():
        assert RECORDS[name]["wrote"] == "wrote", name
        answered = payload(*argv, root=writable)
        assert "ROADMAP.md" in answered["wrote"], name
