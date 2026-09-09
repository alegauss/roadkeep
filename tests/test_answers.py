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
import json
import os
from pathlib import Path

import pytest

from roadkeep.cli import EXIT_OK, EXIT_USAGE, main
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
    # The seventh role and its two doors (RK1618), declared here rather than in the fixture for
    # the reason the row above it exists: `declare` is the only way this store is ever opened,
    # so the sweep drives the sequence an adopter actually runs. The id is named because the
    # row below it has to address the entry, and a derived one is not knowable from a table.
    (("declare", "dismissed"), "the store a finding nobody filed goes into"),
    (("dismiss", "--block", "B", "--symptom", "A symptom traced and left", "--why", "The path is unreachable.", "--premise", "the caller validates first", "--id", "RK20"), "what was looked at and deliberately not filed"),
    (("reopen", "RK20"), "and the way back, for the day the premise breaks"),
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


# -- the answer a refusal has, which was prose alone (RK1584) ------------------


def _refusal(root: Path, argv: tuple[str, ...]) -> tuple[dict[str, object], str]:
    """One refused call's payload and the text beside it, from the same run.

    Both, because the claim is that they are two channels over one composition: a test that
    read only the JSON could not see the sentence drift away from it.
    """
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(["-C", str(root), *argv])
    assert code == EXIT_USAGE, f"{' '.join(argv)} exited {code}"
    return json.loads(out.getvalue()), err.getvalue()


def test_a_refused_call_publishes_the_rules_that_refused_it(project):
    """RK1584. `add --json`, `lint --json` and `brief --json` all answer in fields, and the one
    answer an agent meets most often came back as English on stderr with nothing on stdout —
    so which field, which rule and which of two ceilings were a paragraph to match.

    The keys are the record's own (`code`, `field`, `bound`, `message`), because a payload
    that renamed them would be a second vocabulary for one fact."""
    payload, _ = _refusal(project, (
        "add", "--block", "A", "--symptom", "A symptom plainly long enough to read",
        "--why", "y " * 200 + "z.", "--json",
    ))
    # `doors` since RK1642: a `why` over its limit is one of the seven codes a read predicts,
    # so this refusal carries the preventive command beside the rules that decided it.
    assert set(payload) == {"refused", "beside", "about", "doors", "said"}
    (first, *_) = payload["refused"]
    assert set(first) == {"code", "field", "bound", "message"}
    assert first["code"] == "why.too-long"
    assert first["field"] == "why"


def test_the_payload_is_beside_the_sentence_and_never_instead_of_it(project):
    """The transport's founding argument is that the refusal an agent reads over MCP is
    byte-identical to the one a terminal reads, so this adds a channel rather than replacing
    one — and `said` carries the whole sentence, so a caller holding the payload has not lost
    the prose it came from."""
    payload, said = _refusal(project, (
        "add", "--block", "A", "--symptom", "A symptom plainly long enough to read",
        "--why", "y " * 200 + "z.", "--json",
    ))
    assert payload["said"] == said.rstrip("\n").split("\nIf roadkeep itself")[0]
    assert "roadkeep: refused, nothing written:" in payload["said"]


def test_a_refusal_carrying_no_rules_publishes_an_empty_list(project):
    """`[]` and not a missing key: a `show` on an id nothing carries is a sentence and no
    violation, and *no rule decided this* is an answer where an absent field says only that
    nobody wrote one."""
    payload, _ = _refusal(project, ("show", "RK9999", "--json"))
    assert payload["refused"] == []
    assert "RK9999" in payload["said"]


# -- the two streams, in the order they are read (RK1612) ---------------------


def test_a_note_lands_under_the_answer_it_is_about_off_a_terminal(tmp_path):
    """RK1612. Off a terminal Python buffers stdout fully and leaves stderr unbuffered, so a
    verb printing an answer and then a note into one pipe emits them in the wrong order — the
    note above the report it is about, and a line out of order is a line misread.

    Run as a **subprocess with both streams merged into one pipe**, because that is the only
    arrangement where the defect exists: `capsys` records two separate buffers and would pass
    whatever the flush did. RK1561 found this by hand and `_report` had found it earlier, and
    what neither left behind was a run that says so.

    Both directions, since a fix that cannot fail proves nothing: the same two writes without
    the helper come back reversed, which is the defect, and through it they do not."""
    import subprocess
    import sys as _sys

    def ran(body: str) -> str:
        out = subprocess.run(
            [_sys.executable, "-c", body],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")},
        )
        return out.stdout

    said = ran(
        "\n".join(
            (
                "from roadkeep.verbs.refusing import beneath",
                "print('the answer')",
                "beneath('the note about it')",
            )
        )
    )
    assert said.index("the answer") < said.index("the note about it"), said
    # And the defect, so the assertion above is known to be able to fail.
    reversed_ = ran(
        "\n".join(
            (
                "import sys",
                "print('the answer')",
                "print('the note about it', file=sys.stderr)",
            )
        )
    )
    assert reversed_.index("the note about it") < reversed_.index("the answer"), reversed_


def test_the_ordering_lives_in_one_function_and_not_in_two_disciplines():
    """The deliverable, and why it is not a flush at 34 sites. Most functions printing to both
    streams write an answer *or* a refusal — mutually exclusive, needing nothing — and no scan
    separates the ones that write both in one run. So the repair is the seam: two callers had
    each worked the rule out, and one of them carried the flush with no sentence saying why.

    Asserted as *nobody else flushes*, which is the claim a helper makes.

    **The call and not the characters** (RK1644). This read lines and skipped the ones opening
    with `#` or `*` — a hand-rolled exclusion for exactly the case a character scan cannot
    decide, and one that still counted a docstring's own `stdout.flush()` anywhere but the
    first column. `surface.calling` walks the calls, so the exclusion is not needed and cannot
    be got wrong."""
    from surface import calling, modules

    from roadkeep.verbs.refusing import beneath

    assert beneath.__doc__ and "stderr" in beneath.__doc__
    found = [
        f"{one.where}:{number}"
        for one in modules()
        if one.where != "verbs/refusing.py"
        for number in calling(one.text, "stdout.flush")
    ]
    assert not found, f"`beneath` is where the two streams are ordered: {found}"


# -- the argv inside the paragraph (RK1600) -----------------------------------


def _unanchored(root: Path) -> tuple[str, ...]:
    """An `add` on an outline project with no `--ref`: refused, with the free anchor derived.

    The one refusal shape that does the work and then hands it over as prose — which is the
    whole of RK1149, and the reason its retry is what RK1600 publishes.
    """
    return (
        "add", "--block", "A", "--symptom", "A symptom plainly long enough to read",
        "--why", "Because of a stated reason.", "--json",
    )


def test_a_refusal_that_derived_an_address_publishes_the_call_that_uses_it(outlined):
    """RK1600. RK1149 composes the caller's own call with the address this run worked out
    substituted in, and RK1584's payload published the rules, the clauses and the sentence —
    so the one part of a refusal a reader *executes* was in there as a line of a paragraph.

    An argv and not a string, because every argv this package publishes goes on the wire as a
    list: a consumer runs it. The address beside it because that is what this tool derived and
    the caller did not have — without it they would diff the retry against their own call to
    learn what changed."""
    payload, _ = _refusal(outlined, _unanchored(outlined))
    assert set(payload) == {"refused", "beside", "about", "retry", "said"}
    retry = payload["retry"]
    assert set(retry) == {"argv", "address"}
    assert retry["address"] == "I.4"
    assert retry["argv"][-2:] == ["--ref", "I.4"]
    # The caller's own call and not a command this tool composed: every token they typed is
    # still there, in order, which is what makes it a retry rather than an offer.
    typed = ["-C", str(outlined), *_unanchored(outlined)]
    assert retry["argv"][: len(typed)] == typed


def test_the_published_retry_is_the_call_the_sentence_spells(outlined):
    """Two channels over one composition, which is RK1584's founding rule and the thing a
    second rendering would quietly break. The row is quoted for a shell and the payload is a
    list, so they cannot be compared byte for byte — what is held is that every token of the
    argv is in the sentence, and that the sentence carries no address the payload lacks."""
    payload, said = _refusal(outlined, _unanchored(outlined))
    row = next(one for one in said.splitlines() if one.strip().startswith("retry"))
    for token in payload["retry"]["argv"]:
        assert token in row, (token, row)
    assert payload["retry"]["address"] in row


def test_the_retry_runs_and_the_refused_call_lands(outlined):
    """The claim the payload makes, checked by making it. A published argv a consumer cannot
    run is worse than none, because they spend the turn finding out — which is RK16's rule and
    the reason RK1149 exists at all.

    The `-C` the caller typed is inside the argv, so this is dispatched exactly as published
    and nothing about the path is reconstructed here."""
    payload, _ = _refusal(outlined, _unanchored(outlined))
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(list(payload["retry"]["argv"]))
    assert code == EXIT_OK, err.getvalue()
    assert json.loads(out.getvalue())["ref"] == payload["retry"]["address"]


def test_a_refusal_that_derived_no_address_publishes_no_retry_key(project):
    """Absent and never `"retry": null`, which is `rendering._reading_door`'s rule for a door:
    a consumer reading the key at all is one that acts on it, and a null is a row it has to
    test before it can use.

    The other direction from `refused`, whose `[]` this file already holds — and the two are
    not in tension. `[]` answers *which rules decided this*, and no rule deciding it is an
    answer; there is no comparable question a null retry would be the answer to."""
    payload, said = _refusal(project, ("show", "RK9999", "--json"))
    assert "retry" not in payload
    assert "retry" not in said


# -- the other command in the same refusal (RK1642) ---------------------------


def _over(root: Path) -> tuple[str, ...]:
    """An `add` whose `why` is past its own limit: refused, with a read that predicts it.

    The `foresee` shape and not the retry's: nothing about the call is derived here, and what
    is offered is `budget --why <draft>` — the command that would have measured the same
    sentence and written nothing.
    """
    return (
        "add", "--block", "A", "--symptom", "A symptom plainly long enough to read",
        "--why", "Because of a reason that goes on and on " * 6 + "and it ends.",
        "--json",
    )


def test_the_preventive_read_is_published_as_a_door(project):
    """RK1642. A refused write can print two commands and RK1600 published one: the retry is
    the caller's own call with a token replaced, and the `foresee` read is what would have
    refused the same draft without writing. The second was a line of `said` and no field, so a
    caller reading fields got the rule that refused and never the read that prevents it.

    Under `doors`, which is RK1324's rule wherever a payload publishes a runnable command —
    and the side of the line a `foresee` read is on: the retry is an offer the caller already
    chose, and this is one they have not."""
    payload, said = _refusal(project, _over(project))
    assert "retry" not in payload, "nothing about this call was derived"
    (door,) = payload["doors"]
    assert door["argv"] == ["budget", "--why", "<draft>"]
    assert door["writes"] is False
    # The same composition in both channels, which is RK1584's founding rule.
    for token in door["argv"]:
        assert token in said, (token, said)


def test_the_published_read_says_its_argv_is_a_template(project):
    """The field the shape turns on, and a defect this task's own work exposed: `complete` read
    :data:`~roadkeep.remedying.BLANK` alone — a `…`, which is every remedy door — and a
    `foresee` argv is angled all through. `<draft>` is the caller's prose, so the row is a
    template, and the first door ever published in a refusal payload said it was a command.

    A consumer that ran it verbatim would be asking `budget` to price the literal string."""
    payload, _ = _refusal(project, _over(project))
    (door,) = payload["doors"]
    assert door["complete"] is False
    # And the other direction, off a door that really is complete: the two placeholders are
    # read together, so neither reading answers for the other.
    from roadkeep.remedying import Door

    assert Door(argv=("lint", "--fix"), what="").complete
    assert not Door(argv=("add", "--why", "…"), what="").complete


def test_a_refusal_nothing_predicts_publishes_no_doors_key(project):
    """Absent and never `"doors": []`, which is `rendering._reading_door`'s rule and the one
    the retry keeps beside it: a consumer reading the key at all is one that acts on it.

    Most refusals have none, and that is a fact about them — a duplicate id, a dep nothing
    satisfies and a marker the project does not declare are states no draft measurement would
    have caught, so a row offering one is the advice RK16 refuses."""
    payload, said = _refusal(project, ("show", "RK9999", "--json"))
    assert "doors" not in payload
    assert "foresee" not in said


def test_nothing_is_published_where_the_caller_asked_for_prose(project):
    """The flag is the whole condition, read off the argv this run recorded (RK1149's slot).
    A terminal caller who did not ask for JSON gets what they always got, and stdout on a
    refused write stays empty — which is what a `--ids` consumer downstream of one relies on.
    """
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        main(["-C", str(project), "show", "RK9999"])
    assert out.getvalue() == ""
    assert "RK9999" in err.getvalue()
