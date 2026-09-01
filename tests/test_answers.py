"""The shape a write's answer has, over every verb that writes one (RK1376).

RK1372 found `add` printing `design`, `near` and `event` at column 0 while the `stage` row
beside them sat at 2 — one answer at two columns, in the verb this tool prints most. Its cause
was a shared printer with a default indent that one caller of ten took by not passing one, and
its ledger entry states the reach: *every other write is already one column*.

What held that was an assertion over `add`. A claim about a family checked on a member is
RK1369's shape one surface along, and the defect it admits is the one that produced RK1372 —
a row composed in a printer instead of through the shared helper, which is a line of code and
no refusal, in a report an agent parses.

**The indent and not the label field.** Every write indents its rows by two, and that is what
this quantifies over. The nine-wide label column is narrower than the family: a `block add`
names three files in a path column and a `criterion add` renders a bullet, and neither is a
labelled row — asserting one width across them would claim a shape this surface does not have,
or keep a list of labels that goes stale the next time one is added.

**Read off the helper and never spelled here.** The figure comes from `_staging_rows`, which
every write below reaches, so a project that reindented its answers moves this test by moving
the printer — and a copy of the number here would be the second declaration RK1169 is about.

**And the tables are closed.** :data:`ELSEWHERE` is why a write is in neither, one sentence
per verb, so a verb added tomorrow is a red here with one question in it: drive it, or say why
not. An exclusion with no reason is the state this file exists to make impossible.

**Two projects, because four exclusions were about the fixture** (RK1377). This began with one
and six exclusions, and only two of those sentences were about the verbs — the rest named an
outline, a queue still in `roadkeep.toml`, and a heading stated twice, which are shapes a
second project has rather than properties a verb lacks. A reason cheaper than the fixture it
excuses is RK1369's shape with the exemption visible, and what is left is the two that are
about what the verb answers with.
"""

from __future__ import annotations

import contextlib
import io
from pathlib import Path

import pytest

from roadkeep.cli import EXIT_OK, main
from roadkeep.rendering import _staging_rows

ROADMAP = """# Roadmap

## Block A — The model

- 📋 **RK1** (deps: —) **A first symptom** — Because of a reason. → §RK1
- 📋 **RK2** (deps: —) **A second symptom** — Because of another. → §RK2

## Non-goals
"""

#: Two pairs the fixture arrives with, because two verbs are only reachable from a ledger that
#: already states one id twice — the state a textual merge leaves and no write here produces.
#: RK5's entries say one thing, which is what `record drop` refuses to act without; RK6's say
#: two, which is what makes them two deliveries and `record renumber`'s to address.
LEDGER = """# Shipped

## Block A — The model

- ✅ **RK5** **A symptom recorded twice, identically** — It works.
- ✅ **RK5** **A symptom recorded twice, identically** — It works.
- ✅ **RK6** **One id and two deliveries** — It works.
- ✅ **RK6** **One id and two deliveries** — It works differently.
"""

IMPROVEMENTS = """# Improvements

## Block A — The model

### §RK1 A first design

The reasoning, which names nothing else.

### §RK2 A second design

More reasoning.

### §RK4 A design no line points at

Left behind, which is the one state a `section drop` is reachable from here.
"""

DECISIONS = """# Decisions

## Block A — The model
"""

DEFERRED = """# Deferred

## Block A — The model
"""

CONFIG = """prefix = "RK"
[files]
roadmap = "docs/ROADMAP.md"
changelog = "docs/CHANGELOG.md"
improvements = "docs/IMPROVEMENTS.md"
decisions = "docs/DECISIONS.md"
deferred = "docs/DEFERRED.md"
[non_goals]
lead = 60
why = 200
[criteria]
lead = 60
why = 200
"""

#: Every write this fixture can drive, in an order each one's own refusals allow: a `resume`
#: needs the `defer` above it, a `supersede` needs two decisions filed, and every withdrawal
#: comes after the thing it withdraws. The note says what the row is for, so a verb added here
#: is a line a reviewer reads rather than an argv they decode.
WRITES: tuple[tuple[tuple[str, ...], str], ...] = (
    (("block", "add", "B", "--title", "Authoring"), "a heading in every file that carries one"),
    (("block", "amend", "B", "--title", "Authoring, corrected"), "its words, the label staying"),
    (("block", "add", "C", "--title", "Query"), "a second, kept empty for the withdrawal below"),
    (("non-goal", "add", "--lead", "No web UI.", "--why", "Files and a CLI."), "the other bullet"),
    (("non-goal", "amend", "No web UI.", "--why", "Files, and a CLI."), "its reason, in place"),
    (("criterion", "add", "--block", "A", "--lead", "It works", "--why", "Because it does."), "what finishes a block"),
    (("criterion", "amend", "It works", "--why", "Because it demonstrably does."), "the same, corrected"),
    (("priority", "add", "RK1"), "the queue, which is a section and not a config line"),
    (("priority", "drop", "RK1"), "and out of it again"),
    (("add", "--block", "B", "--symptom", "A third symptom", "--why", "Because of a third reason.", "--section", "A third design", "--section-body", "The reasoning."), "the verb RK1372 was about"),
    (("add", "--block", "B", "--symptom", "A fourth symptom", "--why", "Because of a fourth reason."), "and the shape that owes a follow-up"),
    (("status", "RK1", "🛠"), "a marker, and the claim that follows it"),
    (("amend", "RK1", "--why", "Because of a corrected reason."), "the fields that are a fact"),
    (("restate", "RK1", "--symptom", "A first symptom, restated"), "the claim the line is"),
    (("claim", "RK1", "--path", "src/roadkeep/authoring.py"), "what this commit owns"),
    (("section", "amend", "RK1", "--replace", "nothing else", "--with", "no other file"), "a live design"),
    (("defer", "RK2", "--reason", "Waiting on something outside."), "the pause that is no departure"),
    (("resume", "RK2", "--marker", "📋"), "and the return the ledger has none of"),
    (("renumber", "RK2", "--to", "RK9"), "an id, its section and every dep naming it"),
    (("ship", "RK9", "--why", "It works now.", "--decides", "A constraint that outlives the code."), "the entry, the line, the section, the decision"),
    (("ship", "RK7", "--why", "It works too.", "--decides", "A second constraint, replacing the first."), "and a second, so the file has two"),
    (("supersede", "RK9", "--by", "RK7"), "a decision leaving the one way it can"),
    (("revise", "RK9", "--decides", "A constraint that outlives the code, corrected."), "its sentence, the clause carried"),
    (("record", "add", "--block", "A", "--symptom", "A symptom nobody filed", "--why", "It works."), "an entry with no line"),
    (("record", "move", "RK10", "--to-block", "B"), "one filed under the wrong heading"),
    (("record", "amend", "RK10", "--why", "It works, corrected."), "its sentence, where it sits"),
    (("record", "drop", "RK5"), "the later of two entries saying one thing"),
    (("record", "renumber", "RK6", "--line", "7"), "one of two deliveries under one id"),
    (("section", "add", "RK8", "--title", "A design filed after its line", "--body", "The reasoning."), "the rationale a line points at"),
    (("section", "drop", "RK4"), "and one nothing points at, out again"),
    (("retire", "RK1", "--reason", "The work is not coming back."), "the other terminal door"),
    (("criterion", "drop", "It works"), "the definition of done"),
    (("non-goal", "drop", "No web UI."), "the constraint"),
    (("declare", "strategy"), "a role a project declined at scaffold time"),
    (("govern", "limits.symptom", "120", "--because", "Measured on the lines that read well."), "a number in roadkeep.toml"),
    (("block", "drop", "C"), "a label opened by mistake, last, its subtree still blank"),
)

#: The four writes the table above cannot reach, and the project each needs (RK1377). Not a
#: shape any of them has: an outline where the anchor is an address rather than the id, a queue
#: still in `roadkeep.toml`, and a heading stated twice — which is what a textual merge leaves
#: and every other write refuses to touch, so `block merge` runs first or nothing else runs.
OUTLINED_CONFIG = """prefix = "RK"
ref_scheme = "outline"
priority = ["RK1"]
[files]
roadmap = "docs/ROADMAP.md"
changelog = "docs/CHANGELOG.md"
improvements = "docs/IMPROVEMENTS.md"
"""

OUTLINED_ROADMAP = """# Roadmap

## Block A — The model

- 📋 **RK1** (deps: —) **A first symptom** — Because of a reason. → §I.1

## Block B — Authoring

- 📋 **RK2** (deps: —) **A second symptom** — Because of another. → §I.2

## Block B — Authoring

- 📋 **RK3** (deps: —) **A third symptom** — Because of a third. → §I.3
"""

OUTLINED_LEDGER = """# Shipped

## Block A — The model

## Block B — Authoring
"""

OUTLINED_IMPROVEMENTS = """# Improvements

### §I A family

Its introduction.

#### §I.1 A first design

The reasoning.

#### §I.2 A second design

More reasoning.

#### §I.3 A third design

Still more.
"""

#: In the one order they run in: the doubled heading is what every other write refuses, so it
#: goes first, and `refs` goes last because a namespace re-addresses what `section move` names.
OUTLINED_WRITES: tuple[tuple[tuple[str, ...], str], ...] = (
    (("block", "merge", "B"), "the state a textual merge leaves, which no other write will touch"),
    (("priority", "migrate"), "the queue out of the config and into the section that wins"),
    (("section", "move", "I.3", "--to", "I.9"), "an address, which only an outline has"),
    (("refs", "improvements", "--as", "IMP"), "a namespace, and every citation re-addressed with it"),
)

#: Why a write is in neither table, one sentence each. Two, and both about the verb rather than
#: about a fixture — which is RK1377's own finding: four of the six here were about the suite,
#: and a sentence had been cheaper than the project that reaches them.
ELSEWHERE: dict[str, str] = {
    "export": "its answer is a projection's and carries no rows: what it says is which file it rewrote",
    "repair": "its rows are `lint`'s report run back, so the shape asserted here is the gate's and held there",
}


@pytest.fixture
def project(tmp_path: Path) -> Path:
    (tmp_path / "docs").mkdir(parents=True, exist_ok=True)
    (tmp_path / "roadkeep.toml").write_text(CONFIG, encoding="utf-8")
    for name, body in {
        "ROADMAP.md": ROADMAP,
        "CHANGELOG.md": LEDGER,
        "IMPROVEMENTS.md": IMPROVEMENTS,
        "DECISIONS.md": DECISIONS,
        "DEFERRED.md": DEFERRED,
    }.items():
        with (tmp_path / "docs" / name).open("w", encoding="utf-8", newline="") as handle:
            handle.write(body)
    return tmp_path


@pytest.fixture
def outlined(tmp_path: Path) -> Path:
    """The project the four writes above need, which the first fixture is three ways not."""
    (tmp_path / "docs").mkdir(parents=True, exist_ok=True)
    (tmp_path / "roadkeep.toml").write_text(OUTLINED_CONFIG, encoding="utf-8")
    for name, body in {
        "ROADMAP.md": OUTLINED_ROADMAP,
        "CHANGELOG.md": OUTLINED_LEDGER,
        "IMPROVEMENTS.md": OUTLINED_IMPROVEMENTS,
    }.items():
        with (tmp_path / "docs" / name).open("w", encoding="utf-8", newline="") as handle:
            handle.write(body)
    return tmp_path


def _indent() -> str:
    """The indent every write's rows carry, read off the helper that composes one of them."""
    (row,) = _staging_rows(["x"])
    return row[: len(row) - len(row.lstrip())]


def _answer(root: Path, argv: tuple[str, ...]) -> list[str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(["-C", str(root), *argv])
    assert code == EXIT_OK, f"{' '.join(argv)} exited {code}: {err.getvalue().strip()[:200]}"
    return out.getvalue().splitlines()


def _swept(root: Path, table: tuple[tuple[tuple[str, ...], str], ...], indent: str) -> None:
    """Drive one table against one project, and report every row outside the shared column."""
    for argv, note in table:
        first, *rows = _answer(root, argv)
        assert not first.startswith(" "), (note, first)
        stray = [row for row in rows if row and not row.startswith(indent)]
        assert not stray, {"write": " ".join(argv), "for": note, "at column 0": stray}


def _declared() -> dict[str, object]:
    """Every command whose parser says it writes, indexed by its subcommand path."""
    from roadkeep.cli import build_parser

    def walk(parser, path=()):
        for action in parser._actions:  # noqa: SLF001 - argparse exposes no public reader
            choices = getattr(action, "choices", None)
            if isinstance(choices, dict):
                for name, sub in choices.items():
                    yield from walk(sub, (*path, name))
        if path and parser.get_default("handler") is not None:
            yield " ".join(path), parser

    return {
        command: parser
        for command, parser in walk(build_parser())
        # `reads_only` is the parser's own declaration (RK167), and `wiring` is what runs
        # before a project is governed or on its wiring — `init`, `adopt`, `install`.
        if not parser.get_default("reads_only") and not parser.get_default("wiring")
    }


def test_every_write_answers_with_its_rows_at_one_indent(project):
    """The property RK1372 closed for one verb, quantified over the family its entry claims.

    The first line is the subject — a header, or the line an `add` just rendered — and stands
    where every verb puts it. Everything under it is a row, and a row at column 0 beside a row
    at column 2 is the defect: neither the labels nor the values line up, and a reader scanning
    for a field finds it at one of two offsets depending on which branch of a printer wrote it.
    """
    indent = _indent()
    assert indent and not indent.strip(), "the helper stopped indenting, and this is about that"
    _swept(project, WRITES, indent)


def test_the_writes_the_first_project_cannot_reach_are_swept_by_the_second(outlined):
    """RK1377. Four of the six this file used to exclude were excluded for the fixture's shape
    and not for anything about the verb — an outline, a queue still in the config, a heading
    stated twice. A sentence had been cheaper than the project, and the closure passed over
    four printers nobody swept, which is RK1369's shape with the exemption visible."""
    _swept(outlined, OUTLINED_WRITES, _indent())


def test_the_table_is_closed_over_the_writes_this_package_declares():
    """The half that fails on the *next* verb rather than on this one, which is why it is here:
    a write added tomorrow is a printer nobody swept, and the sweep above is what would have
    caught RK1372. Read off the parsers and never listed twice — a verb declares whether it
    writes, and `reads_only` is that declaration (RK167).

    A verb reaches this file one of two ways and there is no third: driven, or named in
    :data:`ELSEWHERE` with the reason. An exclusion is a sentence somebody wrote."""
    every = (*WRITES, *OUTLINED_WRITES)
    driven = {" ".join(argv[:2]) for argv, _ in every} | {argv[0] for argv, _ in every}
    declared = set(_declared())
    assert set(ELSEWHERE) <= declared, sorted(set(ELSEWHERE) - declared)
    assert sorted(declared - driven - set(ELSEWHERE)) == []


def test_no_exclusion_is_left_as_a_placeholder():
    """`withheld`'s rule one file over: the cheapest way to make the closure pass is a row with
    no reason in it, so each is a sentence about *this* verb and long enough to be one."""
    for command, why in ELSEWHERE.items():
        assert len(why.split()) >= 8, f"{command} has no reason in it"
