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
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from roadkeep.authoring import IdInUse, UnknownBlock
from roadkeep.backlog import Backlog
from roadkeep.cli import EXIT_OK, EXIT_USAGE, main
from roadkeep.config import Config
from roadkeep.history import gaps
from roadkeep.linting import lint
from roadkeep.schema import RETIRED, SHIPPED, SchemaError
from roadkeep.shipping import (
    Ambiguous,
    NoQualifier,
    NotDuplicated,
    NotRecorded,
    amend,
    drop,
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


def project(tmp_path: Path, roadmap: str = ROADMAP, ledger: str = LEDGER) -> Config:
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\nchangelog = "CHANGELOG.md"\n',
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
    # A reader has to be able to tell "nothing was planned" from "the roadmap edit was
    # forgotten", and only the command can say which one this was.
    assert "planned  never" in out
    # Block B holds no open line, and that is what the hook is told (RK38).
    assert out.splitlines()[-1] == "  event    RK3  Block B  empty"


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
    assert payload["event"] == {"id": "RK3", "block": "A", "block_empty": False}


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


def test_two_entries_that_disagree_about_the_door_still_leave_the_first(tmp_path):
    # A ✅ and a 🗑 for one id are two claims, not one written twice — and the reported
    # markers are how the author sees which one the ledger is left stating.
    config = project(
        tmp_path,
        roadmap=BARE_ROADMAP,
        ledger=DOUBLED.replace(f"- {SHIPPED} **RK1**", f"- {RETIRED} **RK1**", 1),
    )
    dropped = drop(config, "RK1")
    assert (dropped.kept_marker, dropped.marker) == (RETIRED, SHIPPED)


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
    assert out.splitlines()[-1] == "  event    RK1  Block A  empty"


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
