"""Every state a governed file can reach, and the verb that leaves it (RK1077).

The barrier denies every hand edit to a governed file, and that trade is only honest while
the verb surface is **complete**. It has not been, six times: RK65 a line that could be
created and removed but never corrected, RK123 a rationale no verb could amend, RK141 a
block heading only a hand edit could write, RK143 an entry filed under the wrong block,
RK403 a heading declared twice, RK1075 a partial line beside an entry recording the whole.
Each was found by the project that walked into it, and each cost a capture report, a session
or a hand edit before it was named — which is the same defect six times rather than six
defects.

So the states are written down, and the door is **executed** rather than asserted. A table
naming `ship` beside a state proves nothing; running it against a file actually in that
state, and finding the state gone, is the claim. That is `test_remedying`'s rule about a
remedy — *a promise nothing runs is prose* — applied to the surface instead of to a message.

Enumerable from the model and not from imagination: a roadmap marker crossed with what the
ledger holds for that id, and — since RK1079 — whether the deferred store carries it too.
:data:`DOORS` fills every reachable cell, :data:`UNREADABLE` names the markers whose lines
the roadmap cannot hold at all (a 🗑 line is `line.unparsed`, not a task in a state), and
:data:`NO_DOOR` is where a reachable cell with no verb goes.

**Sweeping the third axis found a state with no verb, and closing it is why.** RK1077
measured marker against ledger and found a door everywhere; RK1079 added the store and found
an id both files can carry, where `resume` refused, `lint` said nothing and `ship`
*succeeded* — leaving the work recorded as gone and still paused, with the gate calling that
tree clean. RK1081 gave it `resume`, a code and a refusal. That is the cycle: enumerate,
find, close, and hold closed. Two axes said the surface was complete; the third said where
it was not, which is the argument for enumerating rather than believing.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from roadkeep.cli import EXIT_OK, main
from roadkeep.config import Config
from roadkeep.kernel.schema import DEFERRED, DESIGNED, PARTIAL, RETIRED, SHIPPED

#: What the ledger holds for the id, which is the axis that decides most of the table.
NOTHING, WHOLE, HALF = "nothing", "whole", "half"


@dataclass(frozen=True, slots=True)
class Door:
    """One reachable state, and the argv that leaves it.

    `argv` is run against a project built into this state, and `gone` is asked afterwards —
    so a door that stops working fails here rather than in somebody's adoption.
    """

    #: What the roadmap line carries, or `""` where there is no line.
    marker: str
    #: What the ledger holds for the same id: :data:`NOTHING`, :data:`WHOLE` or :data:`HALF`.
    recorded: str
    #: Why this pairing exists at all, in the words the state is recognised by.
    because: str
    #: The command that leaves it, after `-C <root>`.
    argv: tuple[str, ...]
    #: Whether the deferred store carries the id too — the third axis (RK1079). Off on every
    #: row above it, which is the shape of a project that declares no store at all.
    paused: bool = False
    #: Which file must no longer name the id once the door has been used. The roadmap for
    #: every row that starts from a line; the store for the one that starts from a pause.
    leaves: str = "R.md"


DOORS: tuple[Door, ...] = (
    Door(
        marker=DESIGNED,
        recorded=NOTHING,
        because="ordinary open work, which is what every other row is measured against",
        argv=("ship", "RK1", "--why", "It landed."),
    ),
    Door(
        marker=DESIGNED,
        recorded=NOTHING,
        because="work decided against, which leaves by the other terminal door (RK32)",
        argv=("retire", "RK1", "--reason", "Nobody will do it."),
    ),
    Door(
        marker=PARTIAL,
        recorded=HALF,
        because="a live partial: the entry names the half that landed (RK121)",
        argv=("ship", "RK1", "--why", "All of it landed."),
    ),
    Door(
        marker=PARTIAL,
        recorded=WHOLE,
        because=(
            "the state that had no verb at all until RK1075 — the line says a half landed "
            "and the entry says the whole did, and the ledger is what records a delivery"
        ),
        argv=("ship", "RK1"),
    ),
    Door(
        marker=SHIPPED,
        recorded=WHOLE,
        because="adoption's leftover: the entry moved by hand and the line stayed (RK62)",
        argv=("ship", "RK1"),
    ),
    Door(
        marker=SHIPPED,
        recorded=NOTHING,
        because=(
            "a line wearing a marker the roadmap may not carry and nothing recorded — the "
            "half of RK62 where the entry was never written either"
        ),
        argv=("ship", "RK1", "--why", "It landed."),
    ),
    Door(
        marker=DESIGNED,
        recorded=WHOLE,
        because=(
            "an interrupted departure: RK118 orders the ledger first, so stopping between "
            "the two writes leaves the entry and an ordinary open line (RK130)"
        ),
        argv=("ship", "RK1"),
    ),
    Door(
        marker=SHIPPED,
        recorded=HALF,
        because="adoption's leftover where the entry it was moved from named a half",
        argv=("ship", "RK1"),
    ),
    Door(
        marker=DESIGNED,
        recorded=HALF,
        because=(
            "a project that declares no partial marker: the qualifier is what says a half "
            "landed, so the completion is reached from the marker that file does write"
        ),
        argv=("ship", "RK1", "--why", "All of it landed."),
    ),
    Door(
        marker=PARTIAL,
        recorded=NOTHING,
        because=(
            "`ship --part` interrupted before its entry, or a marker set by hand: nothing "
            "is recorded, so this is ordinary open work wearing the partial marker"
        ),
        argv=("ship", "RK1", "--why", "It landed."),
    ),
    Door(
        marker=DESIGNED,
        recorded=NOTHING,
        paused=True,
        because=(
            "an id both files carry, which RK1079 found by sweeping this axis and RK1081 "
            "closed: the roadmap already says the work is open, so the store's copy is the "
            "stale half and a resume removes it without placing a line"
        ),
        argv=("resume", "RK1"),
        leaves="D.md",
    ),
    Door(
        marker="",
        recorded=NOTHING,
        paused=True,
        because=(
            "work set aside: the store holds the line and the roadmap does not, which is "
            "the one state that is not a roadmap marker at all (RK96)"
        ),
        argv=("resume", "RK1"),
        leaves="D.md",
    ),
)


#: The markers whose lines the roadmap **cannot hold at all**, which is a different answer
#: from a state with no door. `[markers] open` does not declare 🗑, so such a line is not a
#: task in a state — it is `line.unparsed`, and the gate says exactly that with the codepoint
#: and the declared set. Named here rather than left out, because "no row" reads as an
#: oversight and this is a decision: a roadmap that could say *retired* is a roadmap holding
#: work nobody will do, which is the sentence `[markers] retired` exists to prevent.
UNREADABLE = {
    RETIRED: (
        "not an open marker this project declares, so the parser reads no task and `lint` "
        "reports `line.unparsed` naming the codepoint and the five that are declared"
    ),
}


#: A cell deliberately left empty, with the reason there is none. Empty today, and kept
#: because the closure needs somewhere to put a state that is reachable and has no verb —
#: which is the six-times defect this file was written from, and the shape a seventh takes.
NO_DOOR: dict[tuple[str, str], str] = {}


LEDGERS = {
    NOTHING: "# C\n\n## Block A — x\n",
    WHOLE: "# C\n\n## Block A — x\n\n- ✅ **RK1** **A symptom** — All of it landed.\n",
    HALF: "# C\n\n## Block A — x\n\n- ✅ **RK1 (local half)** **A symptom** — Half landed.\n",
}


#: One line, spelled once for whichever file a row puts it in.
LINE = "- {marker} **RK1** (deps: —) **A symptom** — Because of a reason.\n"


def built(root: Path, door: Door) -> Path:
    # The store is declared on every fixture and empty on most, which is the honest shape:
    # a project that declares `deferred` has the axis whether or not it has used it (RK1079).
    (root / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "R.md"\nchangelog = "C.md"\n'
        'deferred = "D.md"\n[rules.roadmap]\nref = false\n[rules.deferred]\nref = false\n',
        encoding="utf-8",
    )
    roadmap = LINE.format(marker=door.marker) if door.marker else ""
    (root / "R.md").write_text(f"# R\n\n## Block A — x\n\n{roadmap}", encoding="utf-8")
    (root / "C.md").write_text(LEDGERS[door.recorded], encoding="utf-8")
    paused = LINE.format(marker=DEFERRED) if door.paused else ""
    (root / "D.md").write_text(
        f"# Deferred\n\n## Block A — x\n\n{paused}", encoding="utf-8"
    )
    return root


@pytest.mark.parametrize("door", DOORS, ids=lambda d: f"{d.marker}-{d.recorded}-{d.argv[0]}")
def test_every_reachable_state_is_left_by_the_verb_the_table_names(door, tmp_path, capsys):
    # Executed and not asserted: a table naming `ship` beside a state proves nothing, and a
    # door that quietly stopped working is exactly what the six tasks above each were.
    root = built(tmp_path, door)
    assert main(["-C", str(root), *door.argv]) == EXIT_OK, capsys.readouterr()
    assert "**RK1**" not in (root / door.leaves).read_text(encoding="utf-8")


def test_the_table_and_the_empty_cells_together_cover_the_cross_product():
    # The closure, which is the deliverable: a state nobody classified fails here rather
    # than in an adoption. A new marker or a new ledger shape adds cells, and each one is a
    # row with a door or an entry saying why there is none — never a silence.
    markers = {DESIGNED, PARTIAL, SHIPPED, RETIRED}
    every = {
        (marker, held)
        for marker in markers
        for held in (NOTHING, WHOLE, HALF)
        # A marker the roadmap cannot hold is not a state of a task, so it has no cells:
        # the line is `line.unparsed` and the gate names the codepoint (see UNREADABLE).
        if marker not in UNREADABLE
    }
    doored = {(door.marker, door.recorded) for door in DOORS if not door.paused}
    assert doored.isdisjoint(NO_DOOR), doored & set(NO_DOOR)
    missing = every - doored - set(NO_DOOR)
    assert missing == set(), missing
    # The store is the third axis (RK1079), and it is two cells rather than a cross product:
    # a paused id the roadmap does not carry, which `resume` takes, and one it does — which
    # is the first entry `NO_DOOR` has ever had, and it was found by looking.
    assert {(door.paused, bool(door.marker)) for door in DOORS} >= {(True, False), (True, True)}
    # `NO_DOOR` is empty again, and this time it was emptied rather than never filled: RK1079
    # put the pair in it by measuring and RK1081 gave it a verb, which is the cycle the table
    # exists to run — a state found by enumeration, closed, and held closed here.
    assert NO_DOOR == {}


def test_every_declaration_argues_rather_than_asserts():
    # A reason and not a bare list: "no door" and "not a state" are both claims about the
    # model, and one that does not argue it is a cell somebody added to make this green.
    for cell, because in (*NO_DOOR.items(), *UNREADABLE.items()):
        assert len(because.split()) >= 12, cell
    for door in DOORS:
        assert len(door.because.split()) >= 8, door.argv


def test_the_gate_and_the_verb_read_one_predicate_and_not_two(tmp_path):
    """RK1080. Both decide *is this a live partial*, and the gate's used to restate the
    verb's while its docstring said it applied it. They agreed for the whole time they were
    wrong — a drifting duplicate is loud, and one that stays in step is a rule whose second
    copy nobody can find — so the question moved onto the record both of them hold.

    Held by reading the source rather than by two behaviours agreeing, because agreeing is
    exactly what the duplicate did.
    """
    from surface import address, modules

    everywhere = {
        module.where: module.text
        for module in modules()
        if module.where in (address("linting"), address("shipping"))
    }
    for where, text in everywhere.items():
        assert "in_halves" in text, where
    # The gate asks and never reads the field: a `.task.part` here is the restatement coming
    # back. The verb still reads it — it *writes* the qualifier and puts it in messages —
    # which is the difference between holding a value and re-deciding a question.
    assert ".task.part" not in everywhere[address("linting")]


def test_the_state_the_table_was_written_from_is_gone_afterwards(tmp_path):
    # RK1075's own state, end to end: the one that cost three capture reports. `lint` is what
    # says it is a state at all, and the door is what makes reporting it worth doing (RK1076).
    from roadkeep.linting import lint

    root = built(tmp_path, next(d for d in DOORS if d.marker == PARTIAL and d.recorded == WHOLE))
    assert not lint(Config.discover(root)).clean
    assert main(["-C", str(root), "ship", "RK1"]) == EXIT_OK
    assert lint(Config.discover(root)).clean


def test_a_closure_names_the_file_it_removed_from(tmp_path, capsys):
    """RK1088. `removed_in` was added by RK1086 so the store leftover becomes writable, and
    every construction left it at its default while the printer named the roadmap by having
    only one file to name — a default nothing varies reads as a constant somebody forgot.

    Read now, so the next act's output is already correct rather than quietly wrong.
    """
    import json

    from roadkeep.shipping import Closure

    root = built(tmp_path, next(d for d in DOORS if d.marker == SHIPPED and d.recorded == WHOLE))
    assert main(["-C", str(root), "ship", "RK1", "--json"]) == EXIT_OK
    closed = json.loads(capsys.readouterr().out)["closed"]
    # The role beside the path, because a consumer acting on it wants the name the config
    # uses and a reader wants the file — and deriving one from the other is a second table.
    assert closed["role"] == "roadmap" and closed["file"] == "R.md"

    # And the field is the printer's only source, so a closure over another pair says so
    # without another edit here.
    assert "removed_in" in Closure.__dataclass_fields__
    assert "remaining" in Closure.__dataclass_fields__, "the document is named for the role"
