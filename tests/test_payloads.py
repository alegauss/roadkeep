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

**And the population of lists is derived** (RK1645). `INSIDE` was written when every payload
carried one list of objects, so it mapped a verb to *the* one — and `config` now carries three.
RK1603 met that with a second table and a second sweep beside the first, and neither noticed
`fixed`, published since RK1381 and named nowhere: a consumer reading `fixed[0].reading`
depended on a field nothing here held. The tables are one again, one row per list, and the
lists a promised payload actually answers with are read off the payloads — which found
`engines.gates` the same way, unpromised for as long.

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
    # The shape of the config file itself (RK1270), which a completion list reads key by key
    # (RK1271) — and `version`, because what is offered is what *this* build accepts.
    # `tables` joined when the note moved off the key rows (RK1603): it was on every one of
    # them, so a hover's sentence now joins on `table`, and both halves are keys a reader
    # outside this process depends on.
    # `governed` and `files` since RK1631: *is this path governed* had no door, and a
    # client was branching on `source: null` — a fact expressed as an absence, with no
    # root, no roles and no reason beside it.
    "config": ("version", "source", "governed", "files", "keys", "tables"),
}

#: The keys inside **every** object a payload here carries a list of. Held apart from the top
#: level because a client walks into these, and a rename here is exactly as breaking.
#:
#: A tuple of lists per verb since RK1645, and that is the whole of that task. This mapped a
#: verb to *the* object it holds a list of — one per verb, true of every payload until `config`
#: — so RK1603 met the limit and worked around it with a second table and a second sweep
#: beside this one. Two tables and two tests for one claim, and neither of them noticed the
#: list already there: `config.fixed` has been published since RK1381 and was named nowhere, so
#: a consumer reading `fixed[0].reading` depended on a field nothing here held.
#:
#: :func:`test_every_list_of_objects_a_promised_payload_carries_has_a_row` is what makes that
#: impossible twice: the population is derived from the payloads, so a fourth list is a red
#: with one question in it rather than a table somebody has to remember.
INSIDE = {
    "list": ((
        "tasks",
        ("id", "block", "status", "symptom", "why", "deps", "line"),
    ),),
    # `column` and `remedy` joined when the gate became a problems panel (RK1007): a
    # diagnostic is anchored by the first and a quick fix is composed from the second, so
    # both are keys a reader outside this process now depends on.
    "lint": ((
        "findings",
        ("code", "file", "line", "column", "message", "remedy"),
    ),),
    "stats": (("blocks", ("block", "counted")),),
    # The second list the derived reading found (RK1645): every workflow step calling the
    # action, and the ref each pins it at — which is what an editor shows when it says a
    # checkout gates on a copy other than the one answering, and what nothing here promised.
    "engines": (("gates", ("file", "ref")),),
    # `left`, `limit`, `aim` and `unit` are what a prompt counts down beside the words
    # somebody is typing — the whole of L1 arriving before the sentence exists.
    "budget": ((
        "fields",
        ("field", "limit", "left", "aim", "unit"),
    ),),
    "config": (
        # `address` is what a completion inserts, so it is a key a reader outside this process
        # now depends on (RK1271). `note` was here beside it and is not any more (RK1603): it
        # is a sentence about the *table*, so it was the same paragraph on every key under one
        # — six copies for `[files]` — and it now rides `tables`, joined on `table`.
        # `set` joined when the shape learned what a declared key says (RK1278): a hover shows
        # the number in use, so it is a key a reader outside this process now depends on.
        (
            "keys",
            (
                "table",
                "key",
                "address",
                "type",
                "default",
                "declared",
                "set",
                # RK1282. How many addresses wrote one, which is the fact where the value is
                # not.
                "addresses",
            ),
        ),
        # The table each key joins to for the sentence a hover shows (RK1603).
        ("tables", ("table", "note")),
        # And the figure a limit was chosen against (RK1381, named by RK1645): a reading, what
        # it was taken over, and why that number — which is what an editor shows beside a
        # ceiling somebody is about to change, and what nothing here promised for four
        # hundred tasks.
        ("fixed", ("name", "at", "sample", "percentile", "reading", "why")),
    ),
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


@pytest.mark.parametrize("verb", sorted(PROMISED))
def test_every_payload_says_which_project_and_which_build(verb, dirty, populated):
    """RK1630. `lint` led with `root` and `config` with `version`; the reads a client loops
    over carried neither, and every path on them is relative to a root the payload never
    stated. Run from a subdirectory the answer is identical, so a caller that passed `-C`
    could not join what it got back to what it asked about.

    Survivable for one project in one terminal, where the caller is standing in the answer,
    and not for a client holding many — three checkouts may answer for three projects, and
    `engines` says outright that they are allowed to differ.

    **Leading**, because a key a client reads first is the one it dispatches on, and
    **absolute**, because a relative path is only an address once something names what it is
    relative to."""
    where, code = (dirty, EXIT_GATE) if verb == "lint" else (populated, EXIT_OK)
    got = payload(*_argv(verb, where), root=where, expected=code)
    assert list(got)[:2] == ["root", "version"] or {"root", "version"} <= set(got)
    assert Path(got["root"]).is_absolute()
    assert Path(got["root"]) == Path(where).resolve()
    assert got["version"]


def test_one_call_says_whether_a_path_is_governed_and_what_it_declares(tmp_path):
    """RK1631. Asking whether a path is governed had no door: `config --json` answered
    `source: null`, `engines` exits 0 on a directory with no config anywhere above it, and
    `lint` was the only read carrying a root — reached by parsing every governed file, which
    is a file's work to answer a directory's question.

    The caller is any client that meets a **path** before it meets a project: an editor
    opening a folder, a gate deciding whether to run, a surface over a machine's checkouts.
    Each was reconstructing the discovery rule in its own language, which is wrong the first
    time discovery changes.

    One call, and after RK1630 the root and the build are already on it."""
    bare = tmp_path / "ungoverned"
    bare.mkdir()
    got = payload("config", root=bare, expected=EXIT_OK)
    assert got["governed"] is False
    # An absence stated rather than inferred: `source` is still null and no longer the signal.
    assert got["source"] is None
    # And no roles, which is the same answer — never `Config.default()`'s three, which would
    # be this read answering about a layout nobody declared.
    assert got["files"] == {}
    # The two RK1630 leads with are there either way, so a client has the path it asked about.
    assert Path(got["root"]) == bare.resolve()
    assert got["version"]


def test_a_governed_path_says_so_and_names_the_roles_it_declares(populated):
    from roadkeep.config import Config

    got = payload("config", root=populated, expected=EXIT_OK)
    assert got["governed"] is True
    assert got["source"]
    # The project's own spelling, relative to the root beside it — which is every other `file`
    # key here, and two conventions in one payload is the join a consumer gets wrong.
    config = Config.discover(populated)
    assert got["files"] == {
        role: config.relative(config.path(role))
        for role in config.paths
    }
    assert "roadmap" in got["files"]
    assert not Path(got["files"]["roadmap"]).is_absolute()


def test_a_payload_that_already_named_one_keeps_its_own(dirty):
    """Leading and never replacing (RK1630): the two verbs whose subject *is* the root or the
    build have said it their way for longer than this has existed, and a second spelling of a
    fact is what this removes rather than adds."""
    from roadkeep.provenance import engine

    got = payload(*_argv("lint", dirty), root=dirty, expected=EXIT_GATE)
    # One `root`, and it is the gate's own — which was already the absolute project root.
    assert Path(got["root"]) == Path(dirty).resolve()
    assert got["version"] == engine().version


def test_a_list_payload_is_handed_back_as_the_list_it_is(populated):
    """The decision the helper states rather than the oversight it would otherwise be: there
    is nowhere in an array to put a key, and wrapping `explain`'s would change the shape every
    consumer already reads — the compatibility this whole task is about, broken to fix it."""
    got = payload("explain", root=populated, expected=EXIT_OK)
    assert isinstance(got, list)
    assert got, "explain answered with no codes: this asserts nothing"


@pytest.mark.parametrize(
    "verb, field, keys",
    [(verb, field, keys) for verb, lists in sorted(INSIDE.items()) for field, keys in lists],
)
def test_the_keys_inside_a_row_are_there_too(verb, field, keys, dirty, populated):
    """A client walks into `tasks` and `findings`, so a rename one level down breaks it just
    as hard — and one level is where it stops: nothing here reads a remedy's doors, so those
    stay free to move until something outside says otherwise.

    The rows have to exist for any of that to be a claim, and `docs/` stopped producing them
    the day a block shipped its last line (RK1098) — so the root is `populated`, which is this
    repository whenever it has an open line and a stand-in when it does not.

    One sweep over every list since RK1645, where there were two over one each: `config` holds
    three, so a table shaped *one per verb* wanted a second of itself the moment a second list
    arrived, and a third would have wanted a third.
    """
    where, code = (dirty, EXIT_GATE) if verb == "lint" else (populated, EXIT_OK)
    rows = payload(*_argv(verb, where), root=where, expected=code)[field]
    assert rows, f"{verb}: the fixture produced no {field} to read"
    missing = [key for key in keys if key not in rows[0]]
    assert not missing, f"{verb}.{field} no longer carries {missing}"


def test_every_list_of_objects_a_promised_payload_carries_has_a_row(dirty, populated):
    """RK1645. `config.fixed` was published for four hundred tasks and named in no table here,
    because the population was a list somebody maintained: `INSIDE` was written when every
    payload carried one list, RK1603 added a second table beside it when `config` grew a
    second, and the third — already there — was in neither.

    So the population is **derived**. Every key of every promised payload whose value is a
    non-empty list of objects is a list a client can walk into, which is the claim `INSIDE`
    makes — and a fourth is a red here with one question in it: which of its keys does a
    reader outside this process depend on.

    Read off the same fixtures the sweep above uses, so what is quantified over is the payloads
    this build actually answers with rather than a second reading of what they should hold."""
    unpromised: dict[str, list[str]] = {}
    for verb in sorted(PROMISED):
        where, code = (dirty, EXIT_GATE) if verb == "lint" else (populated, EXIT_OK)
        got = payload(*_argv(verb, where), root=where, expected=code)
        named = {field for field, _ in INSIDE.get(verb, ())}
        for field, value in sorted(got.items()):
            if not isinstance(value, list) or not value:
                continue
            if not isinstance(value[0], dict) or field in named:
                continue
            unpromised.setdefault(verb, []).append(field)
    assert unpromised == {}, (
        "these payloads carry a list of objects nothing here promises, so a client walking "
        f"into one depends on keys no test holds: {unpromised}"
    )


def test_the_derived_reading_finds_the_lists_the_table_names():
    """The half that makes the sweep above worth having: a reader that found no list at all
    would pass while covering nothing. Held on the table, because the two answers have to
    agree in both directions — the assertion above is *derived ⊆ named*, and this is that the
    named set is not simply everything."""
    assert sum(len(lists) for lists in INSIDE.values()) >= 7, INSIDE
    assert len(INSIDE["config"]) == 3, INSIDE["config"]


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
        "opened": "opened",
        "promise": "promise",
        "bound": "bound",
        "wrote": "wrote",
        # The read this write volunteers (RK1370), under its own key: `[]` where the block has
        # delivered nothing, never omitted, so a consumer tells that from an older build.
        "near": "near",
        # And what that block holds against what the list shows (RK1374): three rows and no
        # total read as a three-entry block, which is the guarantee RK442 made about the
        # bounded listing this one volunteers.
        "near_recorded": "near_recorded",
        # And what it holds open (RK1495), counted apart because a duplicate of shipped work
        # wastes a task and a duplicate of open work wastes two sessions at once.
        "near_open": "near_open",
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
