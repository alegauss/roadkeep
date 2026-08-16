"""The door that starts nowhere (RK41).

`ship` and both retirements begin from an open roadmap line, so work finished before it
was ever planned had exactly one route into the ledger: a fictitious roadmap line shipped
in the same breath. What is under test here is the *absence* — the roadmap is not written,
not even to the same bytes, because a moved mtime is an edit to every hook watching the
file and "touched nothing else" has to be true on disk rather than in a docstring.

The other two claims are the ones that would let the fourth door become a hole in the
first three: an id nothing else may already hold (RK4), and a ledger grammar that is the
same grammar (`as_ledger`) rather than a fourth one that happens to accept ✅.

**And the way back out** (RK67), which is under test for its refusals more than its write: a
ledger that lets one entry go is a ledger that can lose a decision, so what has to hold is that
the id must be there *twice*, that the entry the reader already found is the one that stays, and
that the write is still the ledger alone.

**And where an entry ends** (RK157), which is the one defect here that damaged a file rather
than refusing to. A ledger written before this tool existed wraps, the lines under a bullet
parse as nothing, and every write took the entry's *first* line for the whole of it — so an
insertion landed inside the previous entry and a removal stranded its paragraph. The tests
below hold all three directions: the new entry lands after the whole last one, a move carries
the lines the schema does not render, and a dropped duplicate takes its own and no others.

**And the move the update deliberately was not** (RK143). `amend` withheld `--block` because
filing an entry elsewhere relocates the line, and what the tests below hold is that the verb
which does it *says* so: two positions reported rather than one, a heading nothing declares
refused over an untouched file, and still the ledger alone opened.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from roadkeep.authoring import IdInUse, UnknownBlock
from roadkeep.backlog import Backlog
from roadkeep.cli import EXIT_OK, EXIT_USAGE, main
from roadkeep.config import Config
from roadkeep.kernel.document import Continuation
from roadkeep.history import gaps
from roadkeep.linting import lint
from roadkeep.kernel.schema import RETIRED, SHIPPED, SchemaError
from roadkeep.shipping import (
    Ambiguous,
    NoQualifier,
    NoSpan,
    NoSuchEntry,
    NotDuplicated,
    NotRecorded,
    NotRedundant,
    Unchosen,
    Wrapped,
    amend,
    drop,
    move,
    readdress,
    record,
)

ROADMAP = f"""# Roadmap

## Block A — The model

- 📋 **RK1** (deps: —) **A first symptom** — Because of a reason. → §RK1
- 📋 **RK2** (deps: RK1) **A second symptom** — Because of another. → §RK2
"""

LEDGER = """# Shipped

## Block A — The model

## Block B — Authoring
"""


#: The rules a ledger of hand-written history turns off (RK52), and the population RK1049
#: is about: an entry whose sentence wraps has a first line that ends mid-clause, so a role
#: enforcing the terminator is a role in which no wrapped entry can be written back at all.
UNGOVERNED_LEDGER = "[rules.changelog]\none_sentence = false\nterminator = false\n"


def project(
    tmp_path: Path, roadmap: str = ROADMAP, ledger: str = LEDGER, rules: str = ""
) -> Config:
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\nchangelog = "CHANGELOG.md"\n'
        + rules,
        encoding="utf-8",
    )
    for name, body in {"ROADMAP.md": roadmap, "CHANGELOG.md": ledger}.items():
        with (tmp_path / name).open("w", encoding="utf-8", newline="") as handle:
            handle.write(body)
    return Config.discover(tmp_path)


def read(tmp_path: Path, name: str) -> str:
    with (tmp_path / name).open("r", encoding="utf-8", newline="") as handle:
        return handle.read()


# -- the entry ---------------------------------------------------------------


def test_the_entry_arrives_with_no_roadmap_step_at_all(tmp_path):
    config = project(tmp_path)
    entry = record(
        config,
        block="B",
        symptom="A fix nobody planned",
        why="Because it was found on the way to something else.",
    )
    entry.save()

    assert entry.task_id == "RK3"  # one past the highest anywhere (RK4)
    assert entry.marker == SHIPPED
    assert read(tmp_path, "CHANGELOG.md") == LEDGER.replace(
        "## Block B — Authoring\n",
        "## Block B — Authoring\n\n- ✅ **RK3** **A fix nobody planned** "
        "— Because it was found on the way to something else.\n",
    )


def test_the_roadmap_is_not_written_not_even_to_the_same_bytes(tmp_path):
    # The one assertion the docstring cannot make: an untouched file with a moved mtime
    # reads as an edit to every hook watching it.
    config = project(tmp_path)
    before = (tmp_path / "ROADMAP.md").stat().st_mtime_ns
    record(config, block="B", symptom="A fix nobody planned", why="Because.").save()
    assert read(tmp_path, "ROADMAP.md") == ROADMAP
    assert (tmp_path / "ROADMAP.md").stat().st_mtime_ns == before


def test_the_recorded_id_satisfies_a_dep_like_any_other_shipped_one(tmp_path):
    # A record is a ✅ in the ledger and nothing about it is a special case downstream:
    # if it were, the fourth door would be a fourth notion of "done".
    config = project(tmp_path)
    record(config, block="A", symptom="A fix nobody planned", why="Because.").save()
    backlog = Backlog.load(Config.discover(tmp_path))
    assert "RK3" in backlog.shipped() and backlog.retired() == {}


def test_a_recorded_id_is_not_a_gap(tmp_path):
    # The gap report (RK32) is what an unrecorded fix used to become. Recording it is
    # exactly what stops the id reading as a botched hand-edit.
    config = project(tmp_path)
    record(config, block="A", symptom="A fix nobody planned", why="Because.").save()
    assert "RK3" not in [gap.id for gap in gaps(Config.discover(tmp_path))]


# -- what it refuses ---------------------------------------------------------


def test_an_id_the_roadmap_is_holding_is_refused(tmp_path):
    config = project(tmp_path)
    with pytest.raises(IdInUse):
        record(config, block="A", symptom="A fix", why="Because.", task_id="RK1")
    assert read(tmp_path, "CHANGELOG.md") == LEDGER


def test_a_block_no_heading_declares_is_refused(tmp_path):
    # A heading is the only thing that declares a block (RK37): a record filed under an
    # invented one is a shipped entry nothing looks for.
    config = project(tmp_path)
    with pytest.raises(UnknownBlock):
        record(config, block="Z", symptom="A fix", why="Because.")
    assert read(tmp_path, "CHANGELOG.md") == LEDGER


def test_the_fields_are_refused_at_input_against_the_ledger_grammar(tmp_path):
    config = project(tmp_path)
    with pytest.raises(SchemaError) as caught:
        record(
            config,
            block="A",
            symptom="A fix nobody planned",
            why="Two sentences. Which is the signal it belongs in a rationale file.",
        )
    assert [v.code for v in caught.value.violations] == ["why.sentences"]
    assert read(tmp_path, "CHANGELOG.md") == LEDGER


def test_a_symptom_that_is_a_sentence_is_refused_here_too(tmp_path):
    # The rule a schema *can* check, on the field whose rule it cannot: a symptom is a
    # phrase naming what did not work, and the door being new is no reason to soften it.
    config = project(tmp_path)
    with pytest.raises(SchemaError) as caught:
        record(config, block="A", symptom="The parser crashed.", why="Because.")
    assert [v.code for v in caught.value.violations] == ["symptom.sentence"]


# -- the id a sentence names and no line holds (RK1051) -----------------------

#: The Shio shape, minimised: RK4 shipped inside RK3's sentence and has no entry of its
#: own, and two further entries cite its rule — which is what a ledger of interlocking
#: decisions looks like when it works, and what the occupancy check read as an allocation.
CITED = f"""# Shipped

## Block A — The model

- {SHIPPED} **RK3** **A first symptom** — Because it landed, and RK4 landed with it.
- {SHIPPED} **RK5** **A second symptom** — Because the rule RK4 states is what it obeys.

## Block B — Authoring
"""


def test_an_id_only_a_sentence_names_can_be_given_the_entry_it_lacks(tmp_path):
    # The defect: RK4 occurs three times, so `--id RK4` refused — the better documented a
    # decision was, the less repairable its record, and nothing was being *reused*.
    config = project(tmp_path, ledger=CITED)
    written = record(
        config, block="A", symptom="A folded symptom", why="Because it shipped too.", task_id="RK4"
    )
    written.save()

    body = read(tmp_path, "CHANGELOG.md")
    assert f"- {SHIPPED} **RK4** **A folded symptom**" in body
    # The two citing entries are untouched: repairing one record may not damage seven.
    assert "Because the rule RK4 states is what it obeys." in body
    # And the citation that made it refusable is reported rather than swallowed.
    assert written.mentioned is not None and written.mentioned.lineno == 5


def test_an_id_a_line_holds_is_still_refused_at_the_line_that_holds_it(tmp_path):
    # The rule that is actually at stake, unchanged: an entry already carries RK3, so a
    # second one would be two records of two different tasks under one number.
    config = project(tmp_path, ledger=CITED)
    with pytest.raises(IdInUse) as raised:
        record(config, block="A", symptom="A fix", why="Because.", task_id="RK3")
    # The address is the *entry's* and not the first occurrence's, which here is the same
    # line — the roadmap case below is where the two come apart.
    assert "CHANGELOG.md:5" in str(raised.value)
    assert read(tmp_path, "CHANGELOG.md") == CITED


def test_the_refusal_names_the_file_that_carries_the_line(tmp_path):
    # RK1 is a roadmap line and the ledger cites it; the refusal has to send the reader to
    # the line, because a sentence citing an id is not what makes the id unavailable.
    ledger = f"""# Shipped

## Block A — The model

- {SHIPPED} **RK9** **A symptom** — Because RK1 is what it waits on.
"""
    config = project(tmp_path, ledger=ledger)
    with pytest.raises(IdInUse) as raised:
        record(config, block="A", symptom="A fix", why="Because.", task_id="RK1")
    assert "ROADMAP.md:5" in str(raised.value)


def test_the_command_prints_the_sentence_that_already_named_the_id(tmp_path, capsys):
    project(tmp_path, ledger=CITED)
    assert (
        main(
            [
                "-C", str(tmp_path), "record", "add",
                "--id", "RK4",
                "--block", "A",
                "--symptom", "A folded symptom",
                "--why", "Because it shipped too.",
            ]
        )
        == EXIT_OK
    )
    out = capsys.readouterr().out
    assert "cited    CHANGELOG.md:5 already names RK4" in out


def test_the_json_carries_the_citation_and_is_null_without_one(tmp_path, capsys):
    project(tmp_path, ledger=CITED)
    main(
        [
            "-C", str(tmp_path), "record", "add", "--json",
            "--block", "A",
            "--symptom", "A fix nobody planned",
            "--why", "Because.",
        ]
    )
    assert json.loads(capsys.readouterr().out)["mentioned"] is None


# -- the command -------------------------------------------------------------


def test_the_command_names_the_absent_planning_step_and_the_event(tmp_path, capsys):
    project(tmp_path)
    assert (
        main(
            [
                "-C", str(tmp_path), "record", "add",
                "--block", "B",
                "--symptom", "A fix nobody planned",
                "--why", "Because it was found on the way to something else.",
            ]
        )
        == EXIT_OK
    )
    out = capsys.readouterr().out
    assert out.startswith(f"RK3 {SHIPPED} CHANGELOG.md:7 under Block B")
    # A reader has to be able to tell "there was no line" from "the roadmap edit was
    # forgotten", and only the command can say which one this was. About the write and not
    # about the work (RK1051): the same door gives a *planned* task the entry it lacks.
    assert "roadmap  no line to remove" in out
    # Block B holds no open line and the ledger now records one, which is what the hook is
    # told (RK38) — `finished` and not `empty` since RK438, those being two questions.
    assert out.splitlines()[-2] == "  event    RK3  Block B  finished"


def test_the_json_says_the_roadmap_was_not_touched(tmp_path, capsys):
    project(tmp_path)
    assert (
        main(
            [
                "-C", str(tmp_path), "record", "add", "--json",
                "--block", "A",
                "--symptom", "A fix nobody planned",
                "--why", "Because.",
            ]
        )
        == EXIT_OK
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["id"] == "RK3" and payload["marker"] == SHIPPED
    assert payload["roadmap"] == {"touched": False} and payload["refreshed"] == []
    # `standing` beside the stage since RK1164, on every mutator's event.
    assert payload["event"]["stage"] == "live" and payload["event"]["standing"]["open"] == 2


def test_a_refused_record_writes_nothing_and_exits_two(tmp_path, capsys):
    project(tmp_path)
    assert (
        main(["-C", str(tmp_path), "record", "add", "--block", "Z", "--symptom", "A fix",
              "--why", "Because."])
        == EXIT_USAGE
    )
    assert "Z" in capsys.readouterr().err
    assert read(tmp_path, "CHANGELOG.md") == LEDGER
    assert read(tmp_path, "ROADMAP.md") == ROADMAP


def test_the_ledger_still_round_trips_with_a_recorded_line_in_it(tmp_path):
    config = project(tmp_path)
    record(config, block="A", symptom="A fix nobody planned", why="Because.").save()
    reopened = Config.discover(tmp_path)
    document = reopened.document("changelog")
    assert document.render() == read(tmp_path, "CHANGELOG.md")  # L3
    assert document.non_canonical == () and document.rejects == ()


# -- the way back out, for a duplicate alone (RK67) --------------------------


#: One decision the ledger states twice — Shio's `SH347`, which `id.duplicate` reports and
#: nothing but a hand-edit could act on. The second copy is under another block on purpose:
#: a duplicate is written where the second author was looking, not beside the first entry.
DOUBLED = f"""# Shipped

## Block A — The model

- {SHIPPED} **RK1** **A first symptom** — Because of a reason.
- {SHIPPED} **RK2** **A second symptom** — Because of another.

## Block B — Authoring

- {SHIPPED} **RK1** **A first symptom** — Because of a reason.
"""

#: The same file with the later copy gone — and with the blank line the removal doubled
#: gone too, because a trailing paragraph break the file never had is still a change.
DEDUPED = f"""# Shipped

## Block A — The model

- {SHIPPED} **RK1** **A first symptom** — Because of a reason.
- {SHIPPED} **RK2** **A second symptom** — Because of another.

## Block B — Authoring
"""

BARE_ROADMAP = """# Roadmap

## Block A — The model

## Block B — Authoring
"""


def test_the_later_entry_goes_and_the_first_one_answers(tmp_path):
    # Which of the two goes is not a preference: the first is where a reader who already
    # found this decision found it, so a link or a memory of the line stays true.
    config = project(tmp_path, roadmap=BARE_ROADMAP, ledger=DOUBLED)
    dropped = drop(config, "RK1")
    dropped.save()

    assert (dropped.removed_from, dropped.kept) == (10, 5)
    assert dropped.marker == SHIPPED and dropped.block == "A"
    assert read(tmp_path, "CHANGELOG.md") == DEDUPED


def test_the_write_is_the_ledger_and_nothing_else(tmp_path):
    # No annotation can have changed: the id is still recorded, so every `(deps: RK1 ✅)`
    # elsewhere is still true — which is why this door opens one file.
    config = project(tmp_path, ledger=DOUBLED)
    before = (tmp_path / "ROADMAP.md").stat().st_mtime_ns
    drop(config, "RK1").save()
    assert read(tmp_path, "ROADMAP.md") == ROADMAP
    assert (tmp_path / "ROADMAP.md").stat().st_mtime_ns == before


def test_the_duplicate_lint_reported_is_the_one_this_closes(tmp_path):
    # The loop RK67 closes: `lint` names the defect, and until now no command could act on
    # what it named. A finding with no door is a finding that teaches the hand-edit.
    config = project(tmp_path, roadmap=BARE_ROADMAP, ledger=DOUBLED)
    assert "id.duplicate" in [finding.code for finding in lint(config).findings]
    drop(config, "RK1").save()
    assert lint(Config.discover(tmp_path)).findings == ()


def test_a_third_copy_takes_a_second_call(tmp_path):
    # Convergent rather than clever: each call removes the last entry, so "how many" is the
    # author's decision every time instead of one command's guess.
    tripled = DOUBLED + f"- {SHIPPED} **RK1** **A first symptom** — Because of a reason.\n"
    config = project(tmp_path, roadmap=BARE_ROADMAP, ledger=tripled)
    drop(config, "RK1").save()
    reopened = Config.discover(tmp_path)
    assert [e.task.id for e in reopened.document("changelog").entries] == ["RK1", "RK2", "RK1"]
    drop(reopened, "RK1").save()
    assert read(tmp_path, "CHANGELOG.md") == DEDUPED


def test_two_entries_that_disagree_about_the_door_are_not_dropped_by_guess(tmp_path):
    # A ✅ and a 🗑 for one id are two claims, not one written twice (RK127). This used to
    # remove one and *report* the difference afterwards, which is the wrong file and a
    # success message: now the two lines are named and the reader says which goes.
    config = project(
        tmp_path,
        roadmap=BARE_ROADMAP,
        ledger=DOUBLED.replace(f"- {SHIPPED} **RK1**", f"- {RETIRED} **RK1**", 1),
    )
    with pytest.raises(NotRedundant) as caught:
        drop(config, "RK1")
    assert "5, 10" in str(caught.value) and "record renumber" in str(caught.value)

    dropped = drop(config, "RK1", lineno=10)
    dropped.save()
    assert (dropped.kept_marker, dropped.marker) == (RETIRED, SHIPPED)
    assert dropped.kept == 5


def test_the_only_entry_for_an_id_is_refused(tmp_path):
    # The whole safety of the door: removing this one would be deleting history, which is a
    # decision the author states in a commit and not a command the tool offers.
    config = project(tmp_path, ledger=DEDUPED)
    with pytest.raises(NotDuplicated) as caught:
        drop(config, "RK2")
    assert "once, at line 6" in str(caught.value)
    assert read(tmp_path, "CHANGELOG.md") == DEDUPED


def test_an_id_the_ledger_never_recorded_is_refused_and_says_so(tmp_path):
    # "Not a duplicate" and "no such entry" are different problems, and the second one is
    # usually a typo in the id: a message naming the count is what tells them apart.
    config = project(tmp_path, ledger=DEDUPED)
    with pytest.raises(NotDuplicated) as caught:
        drop(config, "RK9")
    assert "nowhere" in str(caught.value)


def test_the_ledger_still_round_trips_after_a_drop(tmp_path):
    config = project(tmp_path, roadmap=BARE_ROADMAP, ledger=DOUBLED)
    drop(config, "RK1").save()
    document = Config.discover(tmp_path).document("changelog")
    assert document.render() == read(tmp_path, "CHANGELOG.md")  # L3
    assert document.non_canonical == () and document.rejects == ()


# -- the command -------------------------------------------------------------


def test_the_drop_command_names_both_lines_and_the_event(tmp_path, capsys):
    project(tmp_path, roadmap=BARE_ROADMAP, ledger=DOUBLED)
    assert main(["-C", str(tmp_path), "record", "drop", "RK1"]) == EXIT_OK
    out = capsys.readouterr().out
    assert out.startswith(f"RK1 {SHIPPED} CHANGELOG.md:10 removed, duplicate of CHANGELOG.md:5")
    assert "roadmap  untouched" in out
    # Named rather than counted back to (RK1130): the staging line sits between the report
    # and the event, so an index into the tail is an assertion about the wrong sentence.
    assert "  event    RK1  Block A  finished" in out.splitlines()
    assert any("stage    git add --" in line for line in out.splitlines())


def test_the_drop_json_says_which_line_answers_now(tmp_path, capsys):
    project(tmp_path, roadmap=BARE_ROADMAP, ledger=DOUBLED)
    assert main(["-C", str(tmp_path), "record", "drop", "--json", "RK1"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["changelog"] == {
        "file": "CHANGELOG.md",
        "removed": 10,
        "marker": SHIPPED,
    }
    assert payload["kept"] == {"line": 5, "marker": SHIPPED}
    assert payload["roadmap"] == {"touched": False}


def test_a_refused_drop_writes_nothing_and_exits_two(tmp_path, capsys):
    project(tmp_path, ledger=DEDUPED)
    assert main(["-C", str(tmp_path), "record", "drop", "RK2"]) == EXIT_USAGE
    assert "once, at line 6" in capsys.readouterr().err
    assert read(tmp_path, "CHANGELOG.md") == DEDUPED


# -- the update the pair was not (RK124) --------------------------------------

#: One entry, and a partial beside it — the two shapes a correction lands on.
RECORDED = f"""# Shipped

## Block A — The model

- {SHIPPED} **RK1** **A first symptom** — Because of a resaon.
- {SHIPPED} **RK2 (local half)** **A second symptom** — Because half of it landed.

## Block B — Authoring
"""


def test_the_sentence_is_corrected_where_the_line_already_is(tmp_path):
    # The whole claim: `drop` + `add` would move the entry to the end of its block, so a
    # ledger read in the order work landed stops being one over a spelling.
    config = project(tmp_path, roadmap=BARE_ROADMAP, ledger=RECORDED)
    corrected = amend(config, "RK1", why="Because of a reason.")
    corrected.save()

    assert corrected.changed == ("why",) and corrected.lineno == 5
    body = read(tmp_path, "CHANGELOG.md")
    assert "Because of a reason." in body and "resaon" not in body
    # The line kept its place, and the entry after it kept theirs.
    assert body.splitlines()[5].startswith(f"- {SHIPPED} **RK2 (local half)**")


def test_a_partials_qualifier_is_the_other_field(tmp_path):
    # The phrase that stops being true (RK121), which is why `_partial` said `amend` all
    # along: only a command knows when "local half" became "local and remote".
    config = project(tmp_path, roadmap=BARE_ROADMAP, ledger=RECORDED)
    corrected = amend(config, "RK2", part="local and remote")
    corrected.save()

    assert corrected.changed == ("part",)
    assert "**RK2 (local and remote)**" in read(tmp_path, "CHANGELOG.md")


def test_a_qualifier_is_corrected_and_never_invented(tmp_path):
    config = project(tmp_path, roadmap=BARE_ROADMAP, ledger=RECORDED)
    with pytest.raises(NoQualifier):
        amend(config, "RK1", part="local half")
    assert read(tmp_path, "CHANGELOG.md") == RECORDED


def test_an_id_the_ledger_states_twice_is_refused(tmp_path):
    # Which of two entries a `--why` was written about is the one thing this transaction
    # cannot read — and the two may be different work sharing an id (RK127).
    config = project(tmp_path, roadmap=BARE_ROADMAP, ledger=DOUBLED)
    with pytest.raises(Ambiguous) as raised:
        amend(config, "RK1", why="Because of a reason.")
    assert "5, 10" in str(raised.value)
    assert read(tmp_path, "CHANGELOG.md") == DOUBLED


def test_an_id_the_ledger_does_not_carry_says_where_it_is(tmp_path):
    config = project(tmp_path, ledger=LEDGER)
    with pytest.raises(NotRecorded) as raised:
        amend(config, "RK1", why="Because of a reason.")
    assert "open roadmap line" in str(raised.value)


def test_the_sentence_is_refused_at_input_the_way_add_refuses_it(tmp_path):
    # L1 at the one door that rewrites: a limit reported after the prose exists is a limit
    # discovered too late to save the tokens it was meant to save.
    config = project(tmp_path, roadmap=BARE_ROADMAP, ledger=RECORDED)
    with pytest.raises(SchemaError):
        amend(config, "RK1", why="Because " + "x" * 400 + ".")
    assert read(tmp_path, "CHANGELOG.md") == RECORDED


def test_an_entry_that_already_reads_that_way_is_not_rewritten(tmp_path):
    config = project(tmp_path, roadmap=BARE_ROADMAP, ledger=RECORDED)
    corrected = amend(config, "RK1", why="Because of a resaon.")
    corrected.save()
    assert corrected.changed == () and read(tmp_path, "CHANGELOG.md") == RECORDED


def test_the_command_prints_the_line_it_left_in_place(tmp_path, capsys):
    project(tmp_path, roadmap=BARE_ROADMAP, ledger=RECORDED)
    code = main(
        ["-C", str(tmp_path), "record", "amend", "RK1", "--why", "Because of a reason."]
    )
    assert code == EXIT_OK
    printed = capsys.readouterr().out
    assert "RK1 amended  CHANGELOG.md:5  (why)" in printed
    assert "Because of a reason." in printed


def test_an_amend_with_neither_field_is_a_usage_error(tmp_path, capsys):
    project(tmp_path, roadmap=BARE_ROADMAP, ledger=RECORDED)
    assert main(["-C", str(tmp_path), "record", "amend", "RK1"]) == EXIT_USAGE
    assert "nothing to amend" in capsys.readouterr().err
    assert read(tmp_path, "CHANGELOG.md") == RECORDED


def test_the_amend_json_says_the_line_did_not_move(tmp_path, capsys):
    project(tmp_path, roadmap=BARE_ROADMAP, ledger=RECORDED)
    code = main(
        [
            "-C",
            str(tmp_path),
            "record",
            "amend",
            "RK1",
            "--why",
            "Because of a reason.",
            "--json",
        ]
    )
    assert code == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["line"] == 5 and payload["changed"] == ["why"]
    assert payload["file"] == "CHANGELOG.md"


# -- the half of a sentence the parse never held (RK179) ----------------------

#: Shio's shape, minimised: a hand-written entry whose sentence runs onto two more lines
#: the grammar reads nothing from. `RK2` beneath it is the neighbour a span that overran
#: would damage, and it is deliberately one line — the wrap is per entry, not per file.
CONTINUED = f"""# Shipped

## Block A — The model

- {SHIPPED} **RK1** **A first symptom** — Because a sentence starts here,
  continues on a second line, and finishes
  on a third one.
- {SHIPPED} **RK2** **A second symptom** — Because of another.
"""


def test_correcting_a_wrapped_sentence_is_refused_until_the_count_is_given(tmp_path):
    # The defect itself: rewriting the first line alone left `continues on a second line`
    # and `on a third one.` beneath the new sentence, and the command called it amended.
    config = project(tmp_path, roadmap=BARE_ROADMAP, ledger=CONTINUED)
    with pytest.raises(Wrapped) as raised:
        amend(config, "RK1", why="It works now.")
    message = str(raised.value)
    assert "CHANGELOG.md:5" in message and "lines 5-7" in message
    assert "--lines 3" in message
    # And the second permission the count carries on a ledger (RK1057): a message naming
    # only the deletion teaches the loss it is reporting, which is where RK1049 came from.
    assert "writes them back instead of collapsing them" in message
    assert read(tmp_path, "CHANGELOG.md") == CONTINUED


def test_the_count_replaces_the_whole_sentence_and_stops_at_the_next_entry(tmp_path):
    config = project(tmp_path, roadmap=BARE_ROADMAP, ledger=CONTINUED)
    corrected = amend(config, "RK1", why="It works now.", lines=3)
    corrected.save()

    body = read(tmp_path, "CHANGELOG.md")
    assert "It works now." in body
    assert "continues on a second line" not in body and "on a third one" not in body
    # The neighbour is exactly where it was, one line up: a span that overran by one would
    # have taken it, which is the deletion the count exists to make the caller's.
    assert body.splitlines()[5] == f"- {SHIPPED} **RK2** **A second symptom** — Because of another."


def test_a_count_that_is_not_the_span_is_refused_rather_than_trusted(tmp_path):
    # An off-by-one here is somebody's paragraph, so the number is checked and not taken.
    config = project(tmp_path, roadmap=BARE_ROADMAP, ledger=CONTINUED)
    with pytest.raises(Wrapped) as raised:
        amend(config, "RK1", why="It works now.", lines=2)
    assert "--lines 2 is not that count" in str(raised.value)
    assert read(tmp_path, "CHANGELOG.md") == CONTINUED


def test_an_entry_that_does_not_wrap_needs_no_count(tmp_path):
    # The count is the door out of a refusal and not a new field on every correction: a
    # governed ledger has no wrapped entry at all, so nothing changes for one.
    config = project(tmp_path, roadmap=BARE_ROADMAP, ledger=CONTINUED)
    corrected = amend(config, "RK2", why="It also works.")
    corrected.save()
    assert corrected.changed == ("why",)
    assert "It also works." in read(tmp_path, "CHANGELOG.md")


def test_an_amend_that_changes_nothing_is_never_asked_for_a_count(tmp_path):
    config = project(tmp_path, roadmap=BARE_ROADMAP, ledger=CONTINUED)
    corrected = amend(config, "RK1", why="Because a sentence starts here,")
    assert corrected.changed == () and read(tmp_path, "CHANGELOG.md") == CONTINUED


def test_the_flag_reaches_the_command_line(tmp_path, capsys):
    project(tmp_path, roadmap=BARE_ROADMAP, ledger=CONTINUED)
    assert (
        main(
            [
                "-C",
                str(tmp_path),
                "record",
                "amend",
                "RK1",
                "--why",
                "It works now.",
                "--lines",
                "3",
            ]
        )
        == EXIT_OK
    )
    assert "RK1 amended  CHANGELOG.md:5  (why)" in capsys.readouterr().out
    assert "on a third one" not in read(tmp_path, "CHANGELOG.md")


# -- and the span written back rather than collapsed (RK1049) -----------------


def test_the_count_lets_the_sentence_be_written_back_over_the_span(tmp_path):
    # The defect: the parser accepts a three-line entry, `--lines 3` says the caller read
    # it, and the only outcome the verb could produce was one line — so correcting a typo
    # in the first sentence deleted two paragraphs of history.
    config = project(
        tmp_path, roadmap=BARE_ROADMAP, ledger=CONTINUED, rules=UNGOVERNED_LEDGER
    )
    corrected = amend(
        config,
        "RK1",
        why="Because a sentence starts here,\n  runs on a corrected line, and finishes\n  on a third one.",
        lines=3,
    )
    corrected.save()

    body = read(tmp_path, "CHANGELOG.md").splitlines()
    assert body[4] == f"- {SHIPPED} **RK1** **A first symptom** — Because a sentence starts here,"
    assert body[5] == "  runs on a corrected line, and finishes"
    assert body[6] == "  on a third one."
    # The neighbour is still one line past the span, which is the whole span arithmetic.
    assert body[7] == f"- {SHIPPED} **RK2** **A second symptom** — Because of another."
    assert corrected.below == 2


def test_a_tail_alone_is_a_change_even_where_the_sentence_did_not_move(tmp_path):
    # `changed` is about fields and the tail is not one, so the no-op path cannot be asked
    # about it: reporting "already reads that way" here would collapse the entry silently.
    config = project(
        tmp_path, roadmap=BARE_ROADMAP, ledger=CONTINUED, rules=UNGOVERNED_LEDGER
    )
    corrected = amend(
        config, "RK1", why="Because a sentence starts here,\n  and stops on this one.", lines=3
    )
    corrected.save()

    assert corrected.changed == () and corrected.below == 1
    body = read(tmp_path, "CHANGELOG.md")
    assert "and stops on this one." in body and "on a third one" not in body


def test_a_tail_line_that_would_come_back_as_a_bullet_is_refused(tmp_path):
    # The one thing L3 cannot catch: `- ✅ **RK9** …` under the bullet round-trips
    # perfectly and is a second entry, filed under an id no verb wrote.
    config = project(tmp_path, roadmap=BARE_ROADMAP, ledger=CONTINUED)
    with pytest.raises(Continuation) as raised:
        amend(
            config,
            "RK1",
            why=f"It works now.\n- {SHIPPED} **RK9** **A smuggled symptom** — Because of a reason.",
            lines=3,
        )
    assert "1 continuation line(s) were offered and 0 came back" in str(raised.value)
    assert read(tmp_path, "CHANGELOG.md") == CONTINUED


def test_a_blank_tail_line_is_refused_because_it_ends_the_entry(tmp_path):
    # A blank breaks the run the parser reads a span from, so everything under it becomes
    # the block's prose — an entry silently cut in half by a command asked to correct it.
    config = project(tmp_path, roadmap=BARE_ROADMAP, ledger=CONTINUED)
    with pytest.raises(Continuation) as raised:
        amend(config, "RK1", why="It works now.\n\n  and this is orphaned.", lines=3)
    assert "a blank line ends the entry" in str(raised.value)
    assert read(tmp_path, "CHANGELOG.md") == CONTINUED


def test_a_newline_without_the_count_is_still_the_refusal_that_names_the_shell(tmp_path):
    # The door is `--lines`, deliberately: everywhere else a newline in a one-line field is
    # PowerShell expanding `` `n ``, and passing it through would grow an entry silently.
    config = project(tmp_path, roadmap=BARE_ROADMAP, ledger=CONTINUED)
    with pytest.raises(SchemaError) as raised:
        amend(config, "RK2", why="It works now.\nand this was never typed.")
    assert any(v.code == "why.newline" for v in raised.value.violations)
    assert read(tmp_path, "CHANGELOG.md") == CONTINUED


def test_a_span_written_back_from_a_crlf_pipe_carries_no_carriage_return(tmp_path):
    # The terminator is the pipe's and the endings are the file's, so a stream written on
    # Windows must not leave `\r` at the end of every continuation line.
    config = project(tmp_path, roadmap=BARE_ROADMAP, ledger=CONTINUED)
    corrected = amend(
        config, "RK1", why="It works now.\r\n  and so does the rest.", lines=3
    )
    corrected.save()
    assert "\r" not in read(tmp_path, "CHANGELOG.md")


# -- correcting an outcome that did not hold (RK1042, RK1052) -----------------

#: RK1 shipped and RK2 reverted it, so RK1's sentence carries the forward pointer
#: `record add --supersedes` writes. RK3 is the neighbour that was never undone.
REVERTED = f"""# Shipped

## Block A — The model

- {SHIPPED} **RK1** **A first symptom** — Because it landed. (superseded by RK2)
- {SHIPPED} **RK2** **The same symptom, again** — Because the first did not hold.
- {SHIPPED} **RK3** **A third symptom** — Because of another.
"""


def test_correcting_an_entry_the_ledger_undid_says_which_entry_undid_it(tmp_path, capsys):
    # The defect: the map was built above a comment citing RK1042 and read in neither
    # branch, so `delivered` marked the entry and the verb correcting it said nothing.
    project(tmp_path, roadmap=BARE_ROADMAP, ledger=REVERTED)
    assert (
        main(
            [
                "-C", str(tmp_path), "record", "amend", "RK1",
                "--why", "Because it landed and was reverted an hour later.",
            ]
        )
        == EXIT_OK
    )
    assert "undone   by RK2" in capsys.readouterr().out


def test_an_entry_nothing_undid_says_nothing(tmp_path, capsys):
    project(tmp_path, roadmap=BARE_ROADMAP, ledger=REVERTED)
    main(["-C", str(tmp_path), "record", "amend", "RK3", "--why", "Because of a reason."])
    assert "undone" not in capsys.readouterr().out


def test_the_clause_is_read_before_the_write_that_can_remove_the_mark(tmp_path, capsys):
    # The ordering is the whole correctness of it: `amend` replaces the sentence the mark
    # lives in, so a map built after the save would answer about an entry that no longer
    # carries it and the one correction that most needs the clause would print none.
    project(tmp_path, roadmap=BARE_ROADMAP, ledger=REVERTED)
    main(
        [
            "-C", str(tmp_path), "record", "amend", "RK1",
            "--why", "Because it landed, with no clause at all.",
        ]
    )
    out = capsys.readouterr().out
    assert "undone   by RK2" in out
    assert "(superseded by RK2)" not in read(tmp_path, "CHANGELOG.md")


def test_the_json_carries_the_reverting_id_and_is_null_without_one(tmp_path, capsys):
    project(tmp_path, roadmap=BARE_ROADMAP, ledger=REVERTED)
    main(
        [
            "-C", str(tmp_path), "record", "amend", "RK1", "--json",
            "--why", "Because it landed and was reverted an hour later.",
        ]
    )
    assert json.loads(capsys.readouterr().out)["undone_by"] == "RK2"

    project(tmp_path, roadmap=BARE_ROADMAP, ledger=REVERTED)
    main(
        [
            "-C", str(tmp_path), "record", "amend", "RK3", "--json",
            "--why", "Because of a reason.",
        ]
    )
    assert json.loads(capsys.readouterr().out)["undone_by"] is None


def test_a_tail_only_correction_is_not_reported_as_unchanged(tmp_path, capsys):
    # The no-op path asks about fields, and RK1049 made a write possible that moves none:
    # rewriting four paragraphs and printing `unchanged` is that task's defect, reported.
    project(tmp_path, roadmap=BARE_ROADMAP, ledger=CONTINUED, rules=UNGOVERNED_LEDGER)
    assert (
        main(
            [
                "-C", str(tmp_path), "record", "amend", "RK1",
                "--why", "Because a sentence starts here,\n  and stops on this one.",
                "--lines", "3",
            ]
        )
        == EXIT_OK
    )
    out = capsys.readouterr().out
    assert "unchanged" not in out and "amended" in out and "(tail)" in out


def test_the_span_reaches_the_command_line_and_the_tail_is_reported(tmp_path, capsys):
    project(tmp_path, roadmap=BARE_ROADMAP, ledger=CONTINUED)
    assert (
        main(
            [
                "-C",
                str(tmp_path),
                "record",
                "amend",
                "RK1",
                "--why",
                "It works now.\n  and the history under it survives.",
                "--lines",
                "3",
                "--json",
            ]
        )
        == EXIT_OK
    )
    payload = json.loads(capsys.readouterr().out)
    # `rendered` is the first line, which is why the count is a field and not an inference.
    assert payload["below"] == 1 and payload["rendered"].endswith("It works now.")
    assert "and the history under it survives." in read(tmp_path, "CHANGELOG.md")


#: Two entries for one id whose parsed fields are identical and whose wrapped tails are
#: not — the shape `_one_entry_twice` used to call one entry recorded twice.
DIVERGING = f"""# Shipped

## Block A — The model

- {SHIPPED} **RK1** **A first symptom** — Because a sentence starts here,
  and ends by naming what it left open.
- {SHIPPED} **RK1** **A first symptom** — Because a sentence starts here,
  and ends by recording that the rest landed.
"""


def test_two_entries_that_differ_below_the_first_line_are_not_a_duplicate(tmp_path):
    # `drop`'s whole safety is that de-duplicating cannot lose a decision. Comparing the
    # parsed fields alone made that false on a wrapping ledger: the two say different
    # things two lines down, and the default would have deleted one of them.
    config = project(tmp_path, roadmap=BARE_ROADMAP, ledger=DIVERGING)
    with pytest.raises(NotRedundant):
        drop(config, "RK1")
    assert read(tmp_path, "CHANGELOG.md") == DIVERGING


# -- two deliveries under one id (RK127) --------------------------------------

#: Shio's SH347, in miniature: one entry records an unplanned fix and names what it left
#: open, the other records exactly that, shipped later. Two true entries, one id.
DELIVERIES = f"""# Shipped

## Block A — The model

- {SHIPPED} **RK1** **A ceiling nothing raised** — Raised to 64; the ceiling is silent.
- {SHIPPED} **RK1** **A ceiling nothing reports** — The test that makes the ceiling visible.
"""


def test_two_deliveries_under_one_id_are_never_dropped_by_default(tmp_path):
    # Running the old verb on this corpus produced the wrong file and reported success:
    # the entry it picks is the later one, which here is the one that earned the id.
    config = project(tmp_path, roadmap=BARE_ROADMAP, ledger=DELIVERIES)
    with pytest.raises(NotRedundant):
        drop(config, "RK1")
    assert read(tmp_path, "CHANGELOG.md") == DELIVERIES


def test_the_other_delivery_is_given_an_address_of_its_own(tmp_path):
    config = project(tmp_path, roadmap=BARE_ROADMAP, ledger=DELIVERIES)
    moved = readdress(config, "RK1", lineno=5, to="RK9")
    moved.save()

    assert (moved.to, moved.lineno, moved.kept) == ("RK9", 5, 6)
    body = read(tmp_path, "CHANGELOG.md")
    # It keeps its line: the ledger still reads in the order work landed.
    assert body.splitlines()[4].startswith(f"- {SHIPPED} **RK9** **A ceiling nothing raised**")
    assert body.splitlines()[5].startswith(f"- {SHIPPED} **RK1** **A ceiling nothing reports**")
    assert lint(Config.discover(tmp_path)).findings == ()


def test_the_destination_is_derived_and_refused_against_every_source(tmp_path):
    config = project(tmp_path, roadmap=ROADMAP, ledger=DELIVERIES)
    assert readdress(config, "RK1", lineno=5).to == "RK3"
    with pytest.raises(IdInUse) as raised:
        readdress(config, "RK1", lineno=5, to="RK2")
    # `--to`, this verb's own spelling (RK1212). The path is live and was inheriting `add`'s
    # flag, which the design filing that task left as an open question about this door.
    assert "omit --to and it is derived" in str(raised.value)
    assert raised.value.flag == "--to"


def test_which_entry_moves_is_named_and_never_defaulted(tmp_path):
    config = project(tmp_path, roadmap=BARE_ROADMAP, ledger=DELIVERIES)
    with pytest.raises(Unchosen) as caught:
        readdress(config, "RK1")
    assert "5, 6" in str(caught.value)
    with pytest.raises(NoSuchEntry):
        readdress(config, "RK1", lineno=7)
    assert read(tmp_path, "CHANGELOG.md") == DELIVERIES


def test_an_id_the_ledger_states_once_is_not_re_addressed(tmp_path):
    # The argument against renumbering a record still holds where there is no collision:
    # it is how a `git log -S` starts returning two unrelated designs.
    config = project(tmp_path, roadmap=BARE_ROADMAP, ledger=DEDUPED)
    with pytest.raises(NotDuplicated):
        readdress(config, "RK2", lineno=6, to="RK9")


def test_the_renumber_command_says_which_line_keeps_the_id(tmp_path, capsys):
    project(tmp_path, roadmap=BARE_ROADMAP, ledger=DELIVERIES)
    code = main(
        ["-C", str(tmp_path), "record", "renumber", "RK1", "--line", "5", "--to", "RK9"]
    )
    assert code == EXIT_OK
    printed = capsys.readouterr().out
    assert printed.startswith("RK1 → RK9  CHANGELOG.md:5")
    assert "line 6 still carries RK1" in printed


def test_the_drop_refusal_offers_both_doors(tmp_path, capsys):
    project(tmp_path, roadmap=BARE_ROADMAP, ledger=DELIVERIES)
    assert main(["-C", str(tmp_path), "record", "drop", "RK1"]) == EXIT_USAGE
    err = capsys.readouterr().err
    assert "record drop RK1 --line <n>" in err and "record renumber RK1" in err
    assert read(tmp_path, "CHANGELOG.md") == DELIVERIES


# -- the move `amend` would not call a correction (RK143) ---------------------

#: The same file with RK1 filed under the other heading, and the blank the removal doubled
#: gone: what "the wrong block, corrected" has to leave behind.
REFILED = f"""# Shipped

## Block A — The model

- {SHIPPED} **RK2 (local half)** **A second symptom** — Because half of it landed.

## Block B — Authoring

- {SHIPPED} **RK1** **A first symptom** — Because of a resaon.
"""


def test_the_entry_is_re_filed_under_the_named_heading(tmp_path):
    # The hole RK124 left: `ship` files an entry under the block its roadmap line sat in, so
    # a line filed wrongly ships wrongly, and every other verb here declined the repair.
    config = project(tmp_path, roadmap=BARE_ROADMAP, ledger=RECORDED)
    refiled = move(config, "RK1", to_block="B")
    refiled.save()

    assert (refiled.from_block, refiled.to_block) == ("A", "B")
    assert refiled.moved and read(tmp_path, "CHANGELOG.md") == REFILED


def test_both_positions_are_reported_because_the_line_does_not_keep_its_number(tmp_path):
    # The whole reason this is a verb and not a flag on `amend`: that one's claim is that the
    # line stays put, and a move reported as one position would be exactly that pretence.
    config = project(tmp_path, roadmap=BARE_ROADMAP, ledger=RECORDED)
    refiled = move(config, "RK1", to_block="B")
    assert (refiled.from_line, refiled.lineno) == (5, 9)
    assert refiled.rendered.startswith(f"- {SHIPPED} **RK1** **A first symptom**")


def test_a_heading_the_ledger_does_not_declare_is_refused_with_the_ones_it_does(tmp_path):
    # A block is declared by a heading and by nothing else (RK37), so this door cannot write
    # one — and the refusal has to name the labels, because "no such block" is the message a
    # caller answers by guessing.
    config = project(tmp_path, roadmap=BARE_ROADMAP, ledger=RECORDED)
    with pytest.raises(UnknownBlock) as caught:
        move(config, "RK1", to_block="Z")
    assert "A" in str(caught.value) and "B" in str(caught.value)
    assert read(tmp_path, "CHANGELOG.md") == RECORDED


def test_an_entry_already_filed_there_is_not_rewritten(tmp_path):
    # Not refused, and not written either: an unchanged file with a moved mtime reads as an
    # edit to every hook watching it, which is the rule `amend`'s no-op path holds too.
    config = project(tmp_path, roadmap=BARE_ROADMAP, ledger=RECORDED)
    before = (tmp_path / "CHANGELOG.md").stat().st_mtime_ns
    refiled = move(config, "RK1", to_block="A")
    assert not refiled.moved and refiled.from_line == refiled.lineno
    assert read(tmp_path, "CHANGELOG.md") == RECORDED
    assert (tmp_path / "CHANGELOG.md").stat().st_mtime_ns == before


def test_an_id_the_ledger_states_twice_is_not_moved_by_guess(tmp_path):
    # Which of two entries a `--to-block` was written about is the fact no file holds, which
    # is the same refusal `amend` makes and for the same reason (RK127).
    config = project(tmp_path, roadmap=BARE_ROADMAP, ledger=DOUBLED)
    with pytest.raises(Ambiguous) as caught:
        move(config, "RK1", to_block="B")
    assert "5, 10" in str(caught.value)
    assert read(tmp_path, "CHANGELOG.md") == DOUBLED


def test_an_id_the_ledger_does_not_carry_says_where_it_is_instead(tmp_path):
    config = project(tmp_path, ledger=LEDGER)
    with pytest.raises(NotRecorded) as caught:
        move(config, "RK1", to_block="B")
    assert "open roadmap line" in str(caught.value)


def test_the_move_is_the_ledger_and_nothing_else(tmp_path):
    # A block says where an entry is filed and not what it records, so no annotation and no
    # dep anywhere is derived from it — which is what keeps this door at one file.
    config = project(tmp_path, ledger=RECORDED)
    before = (tmp_path / "ROADMAP.md").stat().st_mtime_ns
    move(config, "RK1", to_block="B").save()
    assert read(tmp_path, "ROADMAP.md") == ROADMAP
    assert (tmp_path / "ROADMAP.md").stat().st_mtime_ns == before


def test_the_ledger_still_round_trips_after_a_move(tmp_path):
    config = project(tmp_path, roadmap=BARE_ROADMAP, ledger=DEDUPED)
    move(config, "RK1", to_block="B").save()
    document = Config.discover(tmp_path).document("changelog")
    assert document.render() == read(tmp_path, "CHANGELOG.md")  # L3
    assert document.non_canonical == () and document.rejects == ()
    assert lint(Config.discover(tmp_path)).findings == ()


def test_the_move_command_names_both_positions(tmp_path, capsys):
    project(tmp_path, roadmap=BARE_ROADMAP, ledger=RECORDED)
    code = main(["-C", str(tmp_path), "record", "move", "RK1", "--to-block", "B"])
    assert code == EXIT_OK
    out = capsys.readouterr().out
    assert out.startswith("RK1 moved  Block A → Block B  CHANGELOG.md:5 → :9")
    assert "roadmap  untouched" in out
    # Positional no longer (RK1130): the staging line sits between the report and the
    # event, so the assertion names the line it is about rather than counting back to it.
    assert "  event    RK1  Block B  finished" in out.splitlines()
    assert any("stage    git add --" in line for line in out.splitlines())


def test_the_move_json_carries_the_block_it_left(tmp_path, capsys):
    project(tmp_path, roadmap=BARE_ROADMAP, ledger=RECORDED)
    code = main(
        ["-C", str(tmp_path), "record", "move", "RK1", "--to-block", "B", "--json"]
    )
    assert code == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["from"] == {"block": "A", "line": 5}
    assert payload["to"] == {"block": "B", "line": 9}
    assert payload["moved"] is True and payload["roadmap"] == {"touched": False}


def test_a_refused_move_writes_nothing_and_exits_two(tmp_path, capsys):
    project(tmp_path, roadmap=BARE_ROADMAP, ledger=RECORDED)
    code = main(["-C", str(tmp_path), "record", "move", "RK1", "--to-block", "Z"])
    assert code == EXIT_USAGE
    assert "no heading" in capsys.readouterr().err
    assert read(tmp_path, "CHANGELOG.md") == RECORDED


# -- the line an entry starts on is not the line it ends on (RK157) -----------

#: Shio's shape, in miniature: `[rules.changelog]` turns off the one-sentence and terminator
#: rules so a ledger of history written by hand parses, and then every entry wraps.
WRAPPING_CONFIG = (
    'prefix = "SH"\n[files]\nroadmap = "ROADMAP.md"\nchangelog = "CHANGELOG.md"\n'
    "[rules.changelog]\none_sentence = false\nterminator = false\n"
)

WRAPPED_LEDGER = f"""# Shipped

## Block A — The model

- {SHIPPED} **SH1** **A first symptom** — Because of a reason that continues
  on a second line, and finishes
  on a third one.

## Block B — Authoring
"""


def wrapping(tmp_path: Path) -> Config:
    (tmp_path / "roadkeep.toml").write_text(WRAPPING_CONFIG, encoding="utf-8")
    for name, body in {
        "ROADMAP.md": "# Roadmap\n\n## Block A — The model\n\n## Block B — Authoring\n",
        "CHANGELOG.md": WRAPPED_LEDGER,
    }.items():
        with (tmp_path / name).open("w", encoding="utf-8", newline="") as handle:
            handle.write(body)
    return Config.discover(tmp_path)


def test_a_new_entry_lands_after_the_whole_last_entry(tmp_path):
    # The defect, reproduced: the new bullet went to line 6 and left the previous entry's
    # second and third lines below it, so one author's paragraph read as somebody else's
    # shipped sentence — and `lint` passed, both bullets round-tripping.
    config = wrapping(tmp_path)
    entry = record(config, block="A", symptom="A second symptom", why="It works now.")
    entry.save()

    lines = read(tmp_path, "CHANGELOG.md").splitlines()
    assert lines[4].startswith(f"- {SHIPPED} **SH1**")
    assert lines[5] == "  on a second line, and finishes"
    assert lines[6] == "  on a third one."
    assert lines[7].startswith(f"- {SHIPPED} **SH2**")
    assert entry.ledger.lineno == 8


def test_a_moved_entry_takes_its_continuation_lines_with_it(tmp_path):
    # The same fact in the other direction: the removal takes the whole entry, so the
    # re-placement has to carry the lines the schema does not render — a move that rendered
    # alone would take the paragraph out of the file in the name of re-filing it.
    config = wrapping(tmp_path)
    move(config, "SH1", to_block="B").save()

    body = read(tmp_path, "CHANGELOG.md")
    assert body == """# Shipped

## Block A — The model

## Block B — Authoring

- {marker} **SH1** **A first symptom** — Because of a reason that continues
  on a second line, and finishes
  on a third one.
""".format(marker=SHIPPED)
    assert lint(Config.discover(tmp_path)).findings == ()


def test_a_dropped_duplicate_takes_its_own_continuation_and_no_others(tmp_path):
    # A duplicate removed whole, and the entry the reader already found left untouched —
    # including the two lines it owns, which the old arithmetic would have left stranded
    # under the bullet the deletion put above them.
    config = wrapping(tmp_path)
    twin = WRAPPED_LEDGER.replace(
        "## Block B — Authoring\n",
        f"## Block B — Authoring\n\n- {SHIPPED} **SH1** **A first symptom** — "
        "Because of a reason that continues\n  on a second line, and finishes\n"
        "  on a third one.\n",
    )
    with (tmp_path / "CHANGELOG.md").open("w", encoding="utf-8", newline="") as handle:
        handle.write(twin)
    config = Config.discover(tmp_path)

    drop(config, "SH1").save()
    assert read(tmp_path, "CHANGELOG.md") == WRAPPED_LEDGER


# -- the revert the earlier entry knows about (RK395) -------------------------

#: A ledger holding a shipped decision that turned out not to hold, which is the state
#: Turing was in an hour after T922: `ship` had removed the roadmap line, so `retire` had
#: nothing to start from, and `record drop` refuses anything but a duplicate — rightly.
SHIPPED_LEDGER = """# Shipped

## Block A — The model

- ✅ **RK9** **A configuration change was read as an accident** — The reader takes the declared value.

## Block B — Authoring
"""


def test_the_revert_and_the_forward_pointer_are_one_write(tmp_path):
    # Both entries stay, because both happened. What is added is the pointer `retire
    # --superseded-by` already writes one file over, and it lands in *this* write rather than
    # in a second one a crash can lose.
    config = project(tmp_path, ledger=SHIPPED_LEDGER)
    entry = record(
        config,
        block="A",
        symptom="The change RK9 made was deliberate and the revert removed it",
        why="The declared value is honoured again and that reading is withdrawn.",
        supersedes="RK9",
    )
    entry.save()

    written = read(tmp_path, "CHANGELOG.md")
    assert "The reader takes the declared value (superseded by RK10)." in written
    assert "**RK10** **The change RK9 made was deliberate" in written
    assert entry.superseded is not None and entry.superseded.task.id == "RK9"


def test_the_clause_sits_inside_the_terminator(tmp_path):
    # A `why` is one sentence and has to end like one, so a clause bolted on behind the full
    # stop is two — `why.sentences` and `why.no-terminator`, the right refusal about the wrong
    # thing. One writer for both derived clauses, so neither can drift into that state.
    config = project(tmp_path, ledger=SHIPPED_LEDGER)
    record(
        config,
        block="A",
        symptom="The change was deliberate and the revert removed it",
        why="The declared value is honoured again.",
        supersedes="RK9",
    ).save()

    assert [f.code for f in lint(Config.discover(tmp_path)).findings] == []


#: The same shape one file over: the entry the pointer lands on wraps, and RK8 beneath it
#: is the neighbour a span that overran would take.
WRAPPED_TARGET = """# Shipped

## Block A — The model

- ✅ **RK9** **A configuration change was read as an accident** — The reader takes the declared value,
  which the deployment notes of the following week
  explain at length.
- ✅ **RK8** **An eighth symptom** — Because of another.

## Block B — Authoring
"""


def test_the_pointer_lands_on_the_first_line_and_leaves_the_tail_alone(tmp_path):
    # RK1053: this used to rewrite the whole span, so adding a derived pointer deleted two
    # paragraphs of somebody's history — by a call that asked to change no word of it.
    config = project(tmp_path, ledger=WRAPPED_TARGET, rules=UNGOVERNED_LEDGER)
    record(
        config,
        block="A",
        symptom="The change RK9 made was deliberate and the revert removed it",
        why="The declared value is honoured again and that reading is withdrawn.",
        supersedes="RK9",
    ).save()

    body = read(tmp_path, "CHANGELOG.md").splitlines()
    assert "(superseded by RK10)" in body[4]
    # The two lines no field of that task holds, exactly where their author left them.
    assert body[5] == "  which the deployment notes of the following week"
    assert body[6] == "  explain at length."
    assert body[7] == "- ✅ **RK8** **An eighth symptom** — Because of another."


def test_the_count_is_refused_because_the_pointer_replaces_no_span(tmp_path):
    # A flag accepted where nothing is deleted is a flag the caller believes took effect,
    # so the write getting narrower is said out loud rather than left to be assumed.
    config = project(tmp_path, ledger=WRAPPED_TARGET, rules=UNGOVERNED_LEDGER)
    was = read(tmp_path, "CHANGELOG.md")
    with pytest.raises(NoSpan) as raised:
        record(
            config,
            block="A",
            symptom="A revert carrying a count nothing needs",
            why="Because the pointer is appended to the first line.",
            supersedes="RK9",
            lines=3,
        )
    assert "replaces none" in str(raised.value)
    assert read(tmp_path, "CHANGELOG.md") == was


def test_an_id_the_ledger_does_not_carry_is_refused_and_nothing_lands(tmp_path):
    config = project(tmp_path, ledger=SHIPPED_LEDGER)
    was = read(tmp_path, "CHANGELOG.md")
    with pytest.raises(NotRecorded):
        record(
            config,
            block="A",
            symptom="A revert of something nobody recorded",
            why="Because the entry it names is not there.",
            supersedes="RK99",
        )

    # Not even the new entry: the two edits reach disk together or neither does.
    assert read(tmp_path, "CHANGELOG.md") == was


def test_an_id_the_ledger_states_twice_leaves_the_choice_unanswerable(tmp_path):
    doubled = SHIPPED_LEDGER.replace(
        "## Block B — Authoring",
        "- ✅ **RK9** **A second entry under one id** — Which of the two this names.\n\n"
        "## Block B — Authoring",
    )
    config = project(tmp_path, ledger=doubled)
    with pytest.raises(Ambiguous):
        record(
            config,
            block="A",
            symptom="A revert against an id stated twice",
            why="Because which entry it points at is not a fact any file holds.",
            supersedes="RK9",
        )


def test_an_open_roadmap_line_is_named_as_where_the_id_actually_is(tmp_path):
    config = project(tmp_path)
    with pytest.raises(NotRecorded) as raised:
        record(
            config,
            block="A",
            symptom="A revert against a line that never shipped",
            why="Because the entry it names is still an open line.",
            supersedes="RK1",
        )

    assert "open roadmap line" in str(raised.value)


def test_a_record_that_supersedes_nothing_carries_no_pointer(tmp_path):
    config = project(tmp_path, ledger=SHIPPED_LEDGER)
    entry = record(
        config,
        block="B",
        symptom="A fix nobody planned",
        why="Because it was found on the way to something else.",
    )
    entry.save()

    assert entry.superseded is None
    assert "superseded by" not in read(tmp_path, "CHANGELOG.md")


def test_the_command_prints_the_edit_the_caller_did_not_spell(tmp_path, capsys):
    config = project(tmp_path, ledger=SHIPPED_LEDGER)
    argv = [
        "-C", str(config.root), "record", "add", "--block", "A",
        "--symptom", "The change was deliberate and the revert removed it",
        "--why", "The declared value is honoured again.",
        "--supersedes", "RK9",
    ]
    assert main(argv) == EXIT_OK

    out = capsys.readouterr().out
    assert "pointed  CHANGELOG.md:5 RK9 now names RK10 as what replaced it" in out


def test_the_command_carries_the_superseded_entry_in_json(tmp_path, capsys):
    config = project(tmp_path, ledger=SHIPPED_LEDGER)
    argv = [
        "-C", str(config.root), "record", "add", "--block", "A",
        "--symptom", "The change was deliberate and the revert removed it",
        "--why", "The declared value is honoured again.",
        "--supersedes", "RK9", "--json",
    ]
    assert main(argv) == EXIT_OK

    answer = json.loads(capsys.readouterr().out)
    assert answer["superseded"]["id"] == "RK9"
    assert "(superseded by RK10)" in answer["superseded"]["rendered"]
