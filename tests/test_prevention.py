"""Which of the gate's findings a write refuses, and which are the gate's alone (RK498).

L1 says the schema is enforced **where the text is created** and `lint` is only the backstop.
Nothing said which findings that covers. So the family was found one at a time, by somebody
meeting it: RK147 (a prose file's limits), RK412 (the seam every line write passes), RK497 (a
ledger sentence naming a path the repository lacks) — the last of them by a bad commit.

:data:`PREVENTION` is the enumeration. One row per code `remedying.codes()` can emit, in one
of three states, and the closure below is the deliverable rather than the rows: a code added
tomorrow with no row is red here until somebody says which side it is on.

**A row is measured or declared, and the absence of a probe is how you tell.** `refused` and
`open` rows carry an argv this suite actually runs against a throwaway project — `refused`
means the write refuses that input and writes nothing, `open` means the write accepts it and
the gate then reports the code. `gate` rows carry a sentence and no probe: they are a claim,
not a measurement, and the way to upgrade one is to add a probe and watch which way it goes.

What the first run found. The task was filed naming two open codes; probing 30 of the 84
found **five** — the whole `char.*` family a caller's prose can carry (a tab, a zero-width
codepoint, a space that is not one), a dep on an id nothing carries, and a `Block X` dep on
the block the line is being filed into, which writes a line that can never start. That is
the argument for the register: the estimate was low by more than half, in the direction that
costs commits, and the two it named were the two somebody happened to trip. RK499 then
closed the three `char.*` rows and RK500 the other two, which is what a row moving from
`open` to `refused` looks like: the same probe, the other outcome, and a re-opened door
turns it red. :data:`OPEN` is empty now, and that is a statement about the 30 codes this
file probes — never about the 54 it declares, which is the number the next pass raises.

A `refused` row claims the write refuses **the input that would create the finding**, not
that it refuses under that code's name — the door is a schema violation with its own
message, and asserting the gate's vocabulary at the write would tie two surfaces together
that RK423 deliberately keeps apart.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from roadkeep.cli import EXIT_OK, main
from roadkeep.config import Config
from roadkeep.linting import lint
from roadkeep.remedying import codes

#: About the file rather than about a line: no write of this tool composes a file's bytes,
#: its encoding, its line endings or whether it is on disk at all.
FILE = "about the file and not a line: no write composes its bytes, its endings or its existence"
#: A state a *later* write, or a change elsewhere, creates about a line that already exists.
#: The write that composed it was right when it ran, so there was nothing to refuse.
LATER = "a later write makes it true of an earlier line, which was correct when it was written"
#: Reachable only by a hand edit or a textual merge — which is the state the gate exists for.
#: Every verb here either derives the field or refuses the shape.
HAND = "only a hand edit or a merge reaches it: every verb derives this field or refuses it"
#: A state a write creates on purpose, and names the door for in its own answer.
MEANT = "a write creates it deliberately and names the door for it in the same answer"
#: About the served schema, which no write of this tool composes either — a tool's
#: description is `cli.py`'s prose and the `TOOLS` table, so what spends this budget is a
#: source edit and the door is a read (RK1059).
SURFACE = "about the served schema: what spends it is a source edit, not a write of a line"
#: About the **rule** and not about any record it judged (RK1068). No write composes a
#: grammar either — `[grammar.<role>]` is the author's declaration (L6) — and the finding is
#: an inference over a whole file, which no single write is in a position to make.
RULE = "about the declared rule, inferred from every record at once: no write sees the set"
#: About a **vendored copy of this tool's own surfaces** (RK1192). Not `FILE`, which says no
#: write composes the bytes — `install` composes exactly these — and not `LATER`, which is about
#: a line an earlier write left correct. What makes this true is the *engine* moving past a copy
#: that was right when it was written, which is a fact about two versions and about no record at
#: all, so there is no write of a line that could have refused it.
WIRED = "about a vendored surface: the install that wrote it was right, and the engine moved on"

SYMPTOM = "A second symptom that is plainly long enough"
WHY = "Because of some other reason."
LONG = "x" * 400


@dataclass(frozen=True)
class Prevented:
    """One code the gate can emit, and whether the write path holds it."""

    code: str
    #: `refused` — the write refuses the input. `open` — the write accepts it and the gate
    #: reports. `gate` — the gate's alone, and :attr:`because` says why.
    state: str
    #: The argv, after `-C <root>`. Required on `refused` and `open`, absent on `gate`: it is
    #: what makes those two rows a measurement instead of an opinion.
    probe: tuple[str, ...] = ()
    #: Why no write could hold it. Required on `gate` and empty on the other two.
    because: str = ""


def _add(*flags: str) -> tuple[str, ...]:
    return ("add", "--block", "A", *flags)


PREVENTION: tuple[Prevented, ...] = (
    # -- the fields a caller writes, which is where L1 already holds ----------
    Prevented("why.empty", "refused", _add("--symptom", SYMPTOM, "--why", "")),
    Prevented("why.too-long", "refused", _add("--symptom", SYMPTOM, "--why", LONG + ".")),
    Prevented("why.no-terminator", "refused", _add("--symptom", SYMPTOM, "--why", "Because it does")),
    Prevented("why.sentences", "refused", _add("--symptom", SYMPTOM, "--why", "One thing. Two things.")),
    Prevented("why.newline", "refused", _add("--symptom", SYMPTOM, "--why", "Because\nof it.")),
    Prevented("why.control", "refused", _add("--symptom", SYMPTOM, "--why", "Because\x07of it.")),
    Prevented("why.whitespace", "refused", _add("--symptom", SYMPTOM, "--why", "Because of it. ")),
    Prevented("symptom.empty", "refused", _add("--symptom", "", "--why", WHY)),
    Prevented("symptom.too-long", "refused", _add("--symptom", LONG, "--why", WHY)),
    Prevented("symptom.markup", "refused", _add("--symptom", "**A bold symptom of a kind**", "--why", WHY)),
    Prevented("symptom.sentence", "refused", _add("--symptom", "A symptom ending in a stop.", "--why", WHY)),
    Prevented("symptom.newline", "refused", _add("--symptom", "A symptom\nin two", "--why", WHY)),
    Prevented("symptom.control", "refused", _add("--symptom", "A symptom\x07of a kind", "--why", WHY)),
    Prevented("symptom.whitespace", "refused", _add("--symptom", SYMPTOM + " ", "--why", WHY)),
    Prevented("line.too-long", "refused", _add("--symptom", "x" * 110, "--why", "y" * 190 + ".")),
    Prevented("part.blank", "refused", ("ship", "RK1", "--part", "", "--why", "Half of it works.")),
    Prevented("part.too-long", "refused", ("ship", "RK1", "--part", "y" * 200, "--why", "Half works.")),
    Prevented("status.unknown", "refused", _add("--marker", "\U0001f937", "--symptom", SYMPTOM, "--why", WHY)),
    Prevented("block.missing", "refused", ("add", "--block", "Z", "--symptom", SYMPTOM, "--why", WHY)),
    Prevented("path.missing", "refused", ("ship", "RK1", "--why", "It works, in `src/gone.py`.")),
    Prevented("deps.duplicate", "refused", _add("--dep", "RK1", "--dep", "RK1", "--symptom", SYMPTOM, "--why", WHY)),
    Prevented("deps.compound", "refused", _add("--dep", "RK1+RK5", "--symptom", SYMPTOM, "--why", WHY)),
    Prevented("deps.range", "refused", _add("--dep", "RK1..RK5", "--symptom", SYMPTOM, "--why", WHY)),
    Prevented("deps.marker", "refused", _add("--dep", "RK1(x)", "--symptom", SYMPTOM, "--why", WHY)),
    Prevented("deps.self", "refused", ("amend", "RK1", "--dep", "RK1")),
    # The two RK1012 gave the gate, refused at the door since `section add` existed: a
    # section with no prose is a heading, and a section is named by its heading.
    Prevented(
        "body.empty",
        "refused",
        _add("--symptom", SYMPTOM, "--why", WHY, "--section", "A design", "--section-body", "  "),
    ),
    Prevented(
        "title.empty",
        "refused",
        _add("--symptom", SYMPTOM, "--why", WHY, "--section", " ", "--section-body", "A paragraph."),
    ),
    Prevented(
        "body.promise",
        "refused",
        _add(
            "--symptom", SYMPTOM,
            "--why", WHY,
            "--section", "A design",
            "--section-body", "A paragraph naming RK999 as an example of the shape.",
        ),
    ),
    # Closed by RK499, which is why the rows are here rather than under `open`: the same
    # probes now measure a refusal, and a re-opened door turns one of them red.
    Prevented("char.tab", "refused", _add("--symptom", SYMPTOM, "--why", "Because\tof it.")),
    Prevented("char.invisible", "refused", _add("--symptom", SYMPTOM, "--why", "Because​of it.")),
    Prevented("char.space", "refused", _add("--symptom", SYMPTOM, "--why", "Because of it.")),
    # Closed by RK500, the pair a write can decide about the backlog in front of it.
    Prevented("deps.unknown", "refused", _add("--dep", "RK999", "--symptom", SYMPTOM, "--why", WHY)),
    Prevented("deps.cycle", "refused", _add("--dep", "Block A", "--symptom", SYMPTOM, "--why", WHY)),
    # -- the file itself ------------------------------------------------------
    Prevented("char.bom", "gate", because=FILE),
    Prevented("char.mixed-endings", "gate", because=FILE),
    Prevented("file.missing", "gate", because=FILE),
    Prevented("file.not-text", "gate", because=FILE),
    Prevented("budget.absent", "gate", because=FILE),
    # `FILE` names this one exactly — *its endings* (RK1105). A checkout's convention is the
    # one property of a governed file no write of this tool has any say in.
    Prevented("budget.translated", "gate", because=FILE),
    Prevented("budget.tool", "gate", because=SURFACE),
    Prevented("budget.session", "gate", because=SURFACE),
    # RK1106. `LATER` and not `HAND`: the write that put the citation in was right when it ran,
    # and what made it dangle is a `ship` or a `section drop` somewhere else — which those two
    # verbs do report, at the moment they create it. This is the backstop for the caller who
    # was told and did not act, so there is nothing here for an `add` to have refused.
    Prevented("ref.dangling", "gate", because=LATER),
    # RK1168. `LATER` for the same reason and by a different write: the citation was local and
    # correct when it was written, and declaring `[refs]` re-addressed every heading in its file
    # at once — an edit to `roadkeep.toml`, which no door of this tool makes and none can refuse.
    Prevented("ref.crossed", "gate", because=LATER),
    Prevented("grammar.unreadable", "gate", because=RULE),
    Prevented("block.unorganised", "gate", because=FILE),
    Prevented("export.unmarked", "gate", because=FILE),
    Prevented("priority.config", "gate", because=FILE),
    Prevented("priority.unmigrated", "gate", because=FILE),
    Prevented("engine.disagreement", "gate", because=FILE),
    Prevented("install.stale", "gate", because=WIRED),
    # -- true of an earlier line because of a later write ---------------------
    Prevented("id.paused-and-open", "gate", because=LATER),
    Prevented("id.paused-and-gone", "gate", because=LATER),
    Prevented("block.emptied", "gate", because=LATER),
    Prevented("block.reopened", "gate", because=LATER),
    Prevented("deps.retired", "gate", because=LATER),
    Prevented("deps.stale", "gate", because=LATER),
    Prevented("export.stale", "gate", because=LATER),
    Prevented("id.two-files", "gate", because=LATER),
    # RK1031. The write path already refuses `add --id <reserved>` — a reservation is in
    # `scan`, so `refuse_reuse` sees it like any other occurrence — which means this code is
    # never what a write creates. What reaches it is the declaration arriving *after* the
    # line: somebody reserves an address the backlog already carries.
    Prevented("id.reserved", "gate", because=LATER),
    Prevented("part.unexpected", "gate", because=LATER),
    Prevented("ref.mismatch", "gate", because=LATER),
    Prevented("section.orphan", "gate", because=LATER),
    Prevented("section.stale", "gate", because=LATER),
    Prevented("section.unpaired", "gate", because=LATER),
    Prevented("section.unreachable", "gate", because=LATER),
    Prevented("priority.block", "gate", because=LATER),
    Prevented("priority.block-empty", "gate", because=LATER),
    Prevented("priority.block-paused", "gate", because=LATER),
    Prevented("priority.block-unstarted", "gate", because=LATER),
    Prevented("priority.deferred", "gate", because=LATER),
    Prevented("priority.retired", "gate", because=LATER),
    Prevented("priority.shipped", "gate", because=LATER),
    Prevented("priority.unknown", "gate", because=LATER),
    # -- a hand edit or a merge ------------------------------------------------
    Prevented("block.format", "gate", because=HAND),
    Prevented("block.repeated", "gate", because=HAND),
    Prevented("block.unrecorded", "gate", because=HAND),
    Prevented("deps.format", "gate", because=HAND),
    Prevented("deps.unexpected", "gate", because=HAND),
    Prevented("id.duplicate", "gate", because=HAND),
    Prevented("id.format", "gate", because=HAND),
    Prevented("line.non-canonical", "gate", because=HAND),
    Prevented("line.unparsed", "gate", because=HAND),
    Prevented("priority.duplicate", "gate", because=HAND),
    Prevented("priority.shape", "gate", because=HAND),
    Prevented("ref.ambiguous", "gate", because=HAND),
    Prevented("ref.format", "gate", because=HAND),
    Prevented("ref.sigil", "gate", because=HAND),
    Prevented("section.ambiguous", "gate", because=HAND),
    Prevented("section.duplicate", "gate", because=HAND),
    Prevented("status.shipped", "gate", because=HAND),
    Prevented("status.unrepresentable", "gate", because=HAND),
    Prevented("remaining.format", "gate", because=HAND),
    Prevented("section.too-long", "gate", because=HAND),
    # -- created on purpose, with the door named in the same answer -----------
    Prevented("ref.unresolved", "gate", because=MEANT),
    Prevented("ref.missing", "gate", because=MEANT),
    Prevented("deps.block", "gate", because=MEANT),
    Prevented("deps.collective", "gate", because=MEANT),
)

#: The codes a write could refuse and does not. Asserted against the rows in both
#: directions, so closing one is a decision somebody writes down rather than a row quietly
#: changing state — RK491's rule for :data:`UNHELD`, applied to the other half of L1.
OPEN = frozenset()

CONFIG = """prefix = "RK"
[files]
roadmap = "ROADMAP.md"
changelog = "CHANGELOG.md"
improvements = "IMPROVEMENTS.md"
"""
#: Two open lines under Block A, because `deps.collective` is *many* and one member is not
#: many: the probe adds a third and the finding is about what `Block A` then expands to.
ROADMAP = """# Roadmap

## Block A — The model

- 📋 **RK1** (deps: —) **A first symptom that is long enough** — Because of a reason. → §RK1
- 📋 **RK2** (deps: —) **A second symptom that is long enough** — Because of one more. → §RK2

## Block B — Authoring
"""
LEDGER = """# Shipped

## Block A — The model

- ✅ **RK5** **An earlier symptom of some kind** — Because it was done.

## Block B — Authoring
"""
PROSE = """# Design rationale

## Block A — The model

### §RK1 The first design

A paragraph about the first thing, long enough to read as a rationale for it.

### §RK2 The second design

A paragraph about the second thing, long enough to read as a rationale for it too.
"""
GOVERNED = ("ROADMAP.md", "CHANGELOG.md", "IMPROVEMENTS.md")


def project(root: Path) -> Config:
    """A throwaway project, plus the one `src/` a path claim is decided against (RK217)."""
    (root / "roadkeep.toml").write_text(CONFIG, encoding="utf-8", newline="")
    for name, body in zip(GOVERNED, (ROADMAP, LEDGER, PROSE)):
        (root / name).write_text(body, encoding="utf-8", newline="")
    (root / "src").mkdir()
    (root / "src" / "kept.py").write_text("x = 1\n", encoding="utf-8")
    return Config.discover(root)


def _probed() -> tuple[Prevented, ...]:
    return tuple(one for one in PREVENTION if one.probe)


# -- the closure, which is the deliverable ------------------------------------


def test_every_code_the_gate_can_emit_has_a_row():
    """A set any code can be missing from is one more docstring. `remedying.codes()` is the
    authoritative list — RK421 already holds it total over what the gate emits — so a code
    added tomorrow fails here until somebody says which side of L1 it falls on."""
    stated = set(codes())
    assert stated, "the remedy table stopped yielding codes: the closure is reading nothing"
    covered = {one.code for one in PREVENTION}
    assert covered == stated, {"emitted, no row": stated - covered, "row, not emitted": covered - stated}


def test_every_row_is_addressed_once_and_is_measured_or_declared():
    """The distinction the whole file rests on: a probe is a measurement and a sentence is a
    claim, and a row that carried both would let an opinion ride on a green test."""
    addressed = [one.code for one in PREVENTION]
    assert len(addressed) == len(set(addressed)), addressed
    for one in PREVENTION:
        assert one.state in ("refused", "open", "gate"), one.code
        if one.state == "gate":
            assert one.because and not one.probe, f"{one.code}: a gate row is a sentence alone"
        else:
            assert one.probe and not one.because, f"{one.code}: {one.state} needs a probe"


def test_the_open_rows_are_the_ones_named():
    assert {one.code for one in PREVENTION if one.state == "open"} == OPEN


def test_how_much_of_the_register_is_measured():
    """The number the next pass reads before it trusts a `gate` row. Stated as a bound, not a
    count: what matters is that a third of the table is measured and the rest is declared, so
    a reader knows which half they are standing on. Raising it is adding probes."""
    share = len(_probed()) * 100 // len(PREVENTION)
    assert 30 <= share <= 60, share


# -- the measurements themselves ----------------------------------------------


@pytest.mark.parametrize("row", _probed(), ids=lambda one: one.code)
def test_the_probe_measures_what_its_row_claims(row, tmp_path, capsys):
    project(tmp_path)
    before = {name: (tmp_path / name).read_text(encoding="utf-8") for name in GOVERNED}
    code = main(["-C", str(tmp_path), *row.probe])
    capsys.readouterr()
    if row.state == "refused":
        assert code != EXIT_OK, f"{row.code}: the write accepted it"
        after = {name: (tmp_path / name).read_text(encoding="utf-8") for name in GOVERNED}
        assert after == before, f"{row.code}: refused and wrote anyway"
        return
    # `open` is the other measurement, and it has to be both halves: the write accepted the
    # input *and* the gate reports this code about what it left. Either alone would let the
    # row survive a change that closed it.
    assert code == EXIT_OK, f"{row.code}: the write refused it — the row is now `refused`"
    # Re-read: a `Config` caches the documents it parsed, and the gate has to judge what the
    # write left rather than what it found.
    reported = {finding.code for finding in lint(Config.discover(tmp_path)).findings}
    assert row.code in reported, f"{row.code}: the gate no longer reports it — {sorted(reported)}"
