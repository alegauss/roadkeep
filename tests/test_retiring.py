"""The two doors that recorded nothing (RK32).

A line leaves the roadmap three ways and only shipping reached a file, so a gap in the ids
was indistinguishable from a botched hand-edit. Two answers, tested here:

* **`retire`** writes the record at the moment of the decision — one ledger line under the
  block it belonged to, carrying the forward pointer and never the design it replaced;
* **`gaps`** resolves what was already lost against the commit that removed it, and says
  *unresolvable* where history cannot answer rather than inventing a decision — the third
  answer, *never carried*, is a complete history's own and is tested in `test_history.py`.

The third claim is the one that would rot silently: a retired id must **not** satisfy a
dep. The ledger holds it, so any reading of "in the changelog" as "done" would let a
cancelled task satisfy the work that waited on it.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from roadkeep.backlog import Backlog, DepStatus, Readiness
from roadkeep.cli import EXIT_OK, EXIT_USAGE, main
from roadkeep.config import Config, ConfigError
from roadkeep.deferring import defer
from roadkeep.kernel.document import Document
from roadkeep.history import gaps, searchable
from roadkeep.markers import refresh
from roadkeep.picking import pick
from roadkeep.kernel.schema import DESIGNED, RETIRED, SHIPPED, Schema, SchemaError
from roadkeep.shipping import AlreadyRecorded, NoSuchReplacement, NotOpen, retire, ship

HERE = Path(__file__).resolve().parents[1]

ROADMAP = f"""# Roadmap

## Block A — The model

- {DESIGNED} **RK1** (deps: —) **A first symptom** — Because of a reason. → §RK1
- {DESIGNED} **RK4** (deps: RK1) **A fourth symptom** — Because of another. → §RK4
- {DESIGNED} **RK7** (deps: —) **A replacement symptom** — Because of a third. → §RK7
"""

LEDGER = """# Shipped

## Block A — The model
"""

RATIONALE = """# Improvements

## Block A — The model

### §RK1 A first design

The reasoning the line has no room for.
"""


def project(tmp_path: Path, roadmap: str = ROADMAP, declare: str = "") -> Config:
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\nchangelog = "CHANGELOG.md"\n'
        'improvements = "IMPROVEMENTS.md"\n' + declare,
        encoding="utf-8",
    )
    for name, body in {
        "ROADMAP.md": roadmap,
        "CHANGELOG.md": LEDGER,
        "IMPROVEMENTS.md": RATIONALE,
    }.items():
        with (tmp_path / name).open("w", encoding="utf-8", newline="") as handle:
            handle.write(body)
    return Config.discover(tmp_path)


def ledger_of(config: Config) -> Document:
    return config.document("changelog")


# -- the record ---------------------------------------------------------------


def test_a_supersession_writes_one_line_under_the_block_it_belonged_to(tmp_path):
    config = project(tmp_path)
    departure = retire(config, "RK1", reason="RK7 covers it.", superseded_by="RK7")
    departure.save()

    (entry,) = [e for e in ledger_of(config).entries if e.task.id == "RK1"]
    assert entry.task.status == RETIRED and entry.task.block == "A"
    # The symptom is moved verbatim: the tool relocates text, it does not author it.
    assert entry.task.symptom == "A first symptom"
    assert entry.task.why == "superseded by RK7: RK7 covers it."
    assert entry.task.deps == () and entry.task.ref is None
    assert "RK1" not in config.document("roadmap").by_id()


def test_the_rationale_section_goes_with_it(tmp_path):
    # What survives a retirement is one line, never the design it replaced: an accreting
    # rationale file is the 539 KB this project refuses.
    config = project(tmp_path)
    departure = retire(config, "RK1", reason="RK7 covers it.", superseded_by="RK7")
    departure.save()
    assert departure.dropped is not None and departure.dropped.anchor == "RK1"
    assert "§RK1" not in (tmp_path / "IMPROVEMENTS.md").read_text(encoding="utf-8")


def test_abandoning_needs_no_replacement(tmp_path):
    config = project(tmp_path)
    retire(config, "RK1", reason="the premise stopped being true.").save()
    (entry,) = [e for e in ledger_of(config).entries if e.task.id == "RK1"]
    assert entry.task.why == "abandoned: the premise stopped being true."


def test_the_dependents_are_reported_and_not_refused(tmp_path):
    # A supersession is legitimate; RK4's line is the author's next edit, and `lint` (RK14)
    # is what gates it. Refusing here would make the tool an obstacle at the decision.
    config = project(tmp_path)
    departure = retire(config, "RK1", reason="RK7 covers it.", superseded_by="RK7")
    assert departure.dependents == ("RK4",)


# -- the third file the replacement can be in (RK244) -------------------------


def paused(tmp_path: Path, task_id: str = "RK7") -> Config:
    """A project declaring the store, with one line already set aside in it."""
    config = project(tmp_path, declare='deferred = "DEFERRED.md"\n')
    with (tmp_path / "DEFERRED.md").open("w", encoding="utf-8", newline="") as handle:
        handle.write("# Set aside\n\n## Block A — The model\n")
    defer(config, task_id, reason="waiting on something else.").save()
    return Config.discover(tmp_path)


def test_a_paused_id_can_be_what_supersedes_a_retired_line(tmp_path):
    # The likely state, and the one that was refused: work is set aside because something
    # else will carry it, and the line that carries it is often the paused one.
    config = paused(tmp_path)
    departure = retire(config, "RK1", reason="RK7 covers it.", superseded_by="RK7")
    departure.save()

    (entry,) = [e for e in ledger_of(config).entries if e.task.id == "RK1"]
    assert entry.task.why == "superseded by RK7: RK7 covers it."


def test_the_answer_names_which_file_holds_the_replacement(tmp_path):
    # Three files are three promises: shipped is a supersession delivered, open is one
    # being worked, paused is one waiting on a `resume` nobody is holding.
    store = retire(paused(tmp_path), "RK1", reason="RK7 covers it.", superseded_by="RK7")
    assert store.replacement_in == "deferred"

    elsewhere = tmp_path / "open"
    elsewhere.mkdir()
    open_line = retire(
        project(elsewhere), "RK1", reason="RK7 covers it.", superseded_by="RK7"
    )
    assert open_line.replacement_in == "roadmap"


def test_the_ledger_line_says_only_the_id(tmp_path):
    # The state is not written into the entry: a pause ends, and a prefix saying "paused"
    # would be a claim the ledger keeps making after `resume` made it false.
    departure = retire(paused(tmp_path), "RK1", reason="RK7 covers it.", superseded_by="RK7")
    assert "paused" not in departure.ledger.entry.task.why
    assert "DEFERRED" not in departure.ledger.rendered


# -- what it refuses ----------------------------------------------------------


def test_a_replacement_no_file_holds_is_refused(tmp_path):
    # A pointer to nothing is the exact defect being recorded against.
    config = project(tmp_path)
    with pytest.raises(NoSuchReplacement) as caught:
        retire(config, "RK1", reason="something else covers it.", superseded_by="RK99")
    assert "deferred store" in caught.value.args[0]
    assert (tmp_path / "CHANGELOG.md").read_text(encoding="utf-8") == LEDGER


def test_a_line_cannot_supersede_itself(tmp_path):
    # Refused for a reason of its own, and said as one: RK1 *is* in a file, so the count
    # of files it was not found in was the wrong sentence to reuse here.
    config = project(tmp_path)
    with pytest.raises(NoSuchReplacement) as caught:
        retire(config, "RK1", reason="itself.", superseded_by="RK1")
    assert "cannot replace itself" in caught.value.args[0]
    assert "not the roadmap" not in caught.value.args[0]


def test_retiring_what_is_not_open_is_refused(tmp_path):
    config = project(tmp_path)
    with pytest.raises(NotOpen):
        retire(config, "RK99", reason="never existed.")


def test_a_line_in_both_files_names_the_door_the_record_took(tmp_path):
    # The drifted state this check exists for: a hand-edit put RK1 back in the roadmap
    # while the ledger still records how it left. Which door it took is the fact the
    # author needs, so the refusal names the marker rather than the file (RK7).
    config = project(tmp_path)
    retire(config, "RK1", reason="RK7 covers it.", superseded_by="RK7").save()
    with (tmp_path / "ROADMAP.md").open("a", encoding="utf-8", newline="") as handle:
        handle.write(ROADMAP.splitlines(keepends=True)[4])

    with pytest.raises(AlreadyRecorded) as caught:
        retire(Config.discover(tmp_path), "RK1", reason="again.")
    assert RETIRED in caught.value.args[0]
    assert "how it left" in caught.value.args[0]


# -- the claim that would rot silently ---------------------------------------


def test_a_retired_id_does_not_satisfy_a_dep(tmp_path):
    config = project(tmp_path)
    retire(config, "RK1", reason="RK7 covers it.", superseded_by="RK7").save()

    backlog = Backlog.load(Config.discover(tmp_path))
    assert backlog.shipped() == frozenset()  # present in the ledger is not shipped
    assert set(backlog.retired()) == {"RK1"}
    (resolution,) = backlog.resolve(backlog.entry("RK4").task)
    assert resolution.status is DepStatus.UNRESOLVABLE
    assert "retired — superseded by RK7" in resolution.detail


def test_a_task_waiting_on_a_retired_id_is_never_offered(tmp_path):
    config = project(tmp_path)
    retire(config, "RK1", reason="RK7 covers it.", superseded_by="RK7").save()
    reopened = Config.discover(tmp_path)
    backlog = Backlog.load(reopened)
    assert backlog.readiness(backlog.entry("RK4").task) is Readiness.OUTSIDE
    # RK7 is ready and RK4 is not: waiting cannot fix a line whose dep was cancelled.
    assert pick(reopened).entry.task.id == "RK7"


def test_a_retired_dep_gets_no_invented_marker(tmp_path):
    # Derivation never writes a status it cannot read (RK8): the annotation stays as the
    # author left it, and `deps` is where the retirement is reported.
    config = project(tmp_path)
    retire(config, "RK1", reason="RK7 covers it.", superseded_by="RK7").save()
    backlog = Backlog.load(Config.discover(tmp_path))
    derived = refresh(backlog)
    assert derived.changed == ()
    assert "(deps: RK1)" in backlog.roadmap.by_id()["RK4"].raw


# -- the grammar is the same grammar -----------------------------------------


def test_the_ledger_reads_both_markers_and_round_trips(tmp_path):
    config = project(tmp_path)
    retire(config, "RK1", reason="RK7 covers it.", superseded_by="RK7").save()
    reopened = Config.discover(tmp_path)
    source = (tmp_path / "CHANGELOG.md").read_text(encoding="utf-8")
    document = reopened.document("changelog")
    assert document.render() == source  # L3, with a 🗑 line in the file
    assert document.non_canonical == () and document.rejects == ()


def test_a_retired_marker_in_the_roadmap_is_not_silently_prose():
    # 🗑 is declared, but not for that file: it must be a reject with a reason (RK10),
    # never a line no count sees.
    text = f"# Roadmap\n\n## Block A — The model\n\n- {RETIRED} **RK1** (deps: —) **A symptom** — why.\n"
    document = Document.parse(text, Schema())
    assert document.entries == () and len(document.rejects) == 1
    assert "not a marker this project declares" in document.rejects[0].reason


def test_a_project_may_declare_its_own_retired_marker(tmp_path):
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[markers]\nretired = "⛔"\n', encoding="utf-8"
    )
    assert Config.discover(tmp_path).schema.retired_marker == "⛔"


#: A project whose ledger states the marker once instead of on every line (RK43).
NO_LEDGER_MARKER = "\n[ledger]\nmarker = false\n"


def test_retiring_into_a_ledger_that_declares_no_marker_is_a_door(tmp_path):
    # The declaration made the file readable and took a verb away with it (RK125). The way
    # through is the marker on that one line: the file states that every entry in it
    # shipped, so the entry that did not is the exception, and the line says which.
    config = project(tmp_path, declare=NO_LEDGER_MARKER)
    retire(config, "RK1", reason="Nobody will do it.").save()
    (entry,) = [e for e in config.document("changelog").entries if e.task.id == "RK1"]
    assert entry.raw == "- 🗑 **RK1** **A first symptom** — abandoned: Nobody will do it."
    # Read back off the line and not derived from the file, which is the difference between
    # a departure and the shipment `Backlog.retired` would otherwise have counted it as.
    assert entry.task.status == RETIRED
    assert "RK1" not in config.document("roadmap").by_id()


def test_a_ledger_that_declares_no_marker_still_takes_a_shipment(tmp_path):
    # The other half of the same declaration: shipped is the status the *file* states, so
    # it is the one departure a markerless ledger can record.
    config = project(tmp_path, declare=NO_LEDGER_MARKER)
    ship(config, "RK1", why="Because of a reason.").save()
    (entry,) = [e for e in config.document("changelog").entries if e.task.id == "RK1"]
    assert entry.task.status == SHIPPED  # derived from the file, not read off the line
    assert entry.raw == "- **RK1** **A first symptom** — Because of a reason."


def test_one_marker_for_two_doors_is_refused(tmp_path):
    (tmp_path / "roadkeep.toml").write_text(
        f'prefix = "RK"\n[markers]\nretired = "{SHIPPED}"\n', encoding="utf-8"
    )
    with pytest.raises(ConfigError) as caught:
        Config.discover(tmp_path)
    assert "cannot say whether the work was done" in str(caught.value)


# -- the gaps nobody recorded ------------------------------------------------


def test_a_contiguous_backlog_has_no_gaps(tmp_path):
    roadmap = (
        "# Roadmap\n\n## Block A — The model\n\n"
        + f"- {DESIGNED} **RK1** (deps: —) **A symptom** — a reason. → §RK1\n"
        + f"- {DESIGNED} **RK2** (deps: —) **A symptom** — a reason. → §RK2\n"
    )
    assert gaps(project(tmp_path, roadmap=roadmap)) == ()


def test_a_missing_id_is_a_gap_and_history_is_where_it_resolves(tmp_path):
    # tmp_path is not a repository, so the gap is *unresolvable* rather than retired —
    # an absent answer, which is the answer RK28 insists on keeping distinct. It is not
    # "never carried" either: nothing was searched, so nothing was found out (RK95).
    config = project(tmp_path)  # RK1, RK4, RK7: 2, 3, 5, 6 are gaps
    found = gaps(config)
    assert [gap.id for gap in found] == ["RK2", "RK3", "RK5", "RK6"]
    assert all(not gap.resolved and gap.removed_in is None for gap in found)
    assert not any(gap.never_carried for gap in found)


def test_a_retired_id_stops_being_a_gap(tmp_path):
    config = project(tmp_path)
    retire(config, "RK4", reason="the premise stopped being true.").save()
    assert "RK4" not in [gap.id for gap in gaps(Config.discover(tmp_path))]


def test_this_repositorys_own_gaps_are_each_accounted_for():
    # Two shapes, and this repo has one of each: RK33 left before this command existed, so
    # the record is the commit subject; RK80 was skipped when RK78-RK84 were allocated, so
    # no commit ever carried it and none ever will. What must never happen is a third
    # answer — a gap this checkout simply could not look up (RK95).
    config = Config.discover(HERE)
    if not searchable(config):
        pytest.skip("a shallow clone cannot tell a skipped id from a removed one")
    found = gaps(config)
    if not found:
        pytest.skip("this backlog has no gaps left")
    unaccounted = [gap.id for gap in found if not (gap.resolved or gap.never_carried)]
    assert not unaccounted, unaccounted
    assert any(gap.resolved and "retire" in gap.removed_in.subject for gap in found)


# -- the commands ------------------------------------------------------------


def test_the_command_reports_every_edit_and_the_event(tmp_path, capsys):
    project(tmp_path)
    assert (
        main(
            [
                "-C", str(tmp_path), "retire", "RK1",
                "--superseded-by", "RK7",
                "--reason", "RK7 covers it.",
            ]
        )
        == EXIT_OK
    )
    out = capsys.readouterr().out
    assert out.startswith(f"RK1 {RETIRED} CHANGELOG.md:")
    assert "removed  ROADMAP.md:5" in out
    assert "dropped  §RK1" in out
    assert "found    RK7 in ROADMAP.md" in out
    assert "still    RK4 name RK1" in out
    # The standing under the event since RK1164: a retirement resolves the block for the same
    # reason a ship does, and the caller driving one asked `list` next.
    assert out.splitlines()[-2] == "  event    RK1  Block A  live"
    assert out.splitlines()[-1] == "           Block A has 2 open"


def test_the_command_names_the_store_when_that_is_where_it_found_it(tmp_path, capsys):
    # The whole point of the line: the id alone reads as any other replacement, and this
    # one only becomes work again when somebody runs `resume`.
    paused(tmp_path)
    capsys.readouterr()
    assert (
        main(
            [
                "-C", str(tmp_path), "retire", "RK1",
                "--superseded-by", "RK7",
                "--reason", "RK7 covers it.",
                "--json",
            ]
        )
        == EXIT_OK
    )
    assert json.loads(capsys.readouterr().out)["replacement_in"] == "deferred"


def test_an_abandoned_line_reports_no_replacement(tmp_path, capsys):
    project(tmp_path)
    assert main(["-C", str(tmp_path), "retire", "RK1", "--reason", "gone.", "--json"]) == EXIT_OK
    assert json.loads(capsys.readouterr().out)["replacement_in"] is None


def test_a_refused_retirement_writes_nothing_and_exits_two(tmp_path, capsys):
    project(tmp_path)
    assert (
        main(["-C", str(tmp_path), "retire", "RK1", "--superseded-by", "RK99",
              "--reason", "x."])
        == EXIT_USAGE
    )
    assert "not the deferred store" in capsys.readouterr().err
    assert (tmp_path / "CHANGELOG.md").read_text(encoding="utf-8") == LEDGER


def test_the_reason_is_required_because_the_record_is_the_reason(tmp_path):
    project(tmp_path)
    with pytest.raises(SystemExit) as caught:
        main(["-C", str(tmp_path), "retire", "RK1"])
    assert caught.value.code == EXIT_USAGE


def test_gaps_prints_the_commit_or_says_unresolvable(tmp_path, capsys):
    project(tmp_path)
    assert main(["-C", str(tmp_path), "gaps"]) == EXIT_OK
    out = capsys.readouterr().out
    # The column is as wide as the widest label since RK1165, a range being one — so what is
    # asserted is the row and not the run of spaces that used to pad an id to six.
    assert any(
        line.split() == ["RK2", "unresolvable", "no", "history", "here", "to", "search"]
        for line in out.splitlines()
    ), out
    assert "4 gap(s), 0 resolved against history" in out


def test_gaps_json_carries_the_commit(capsys):
    assert main(["-C", str(HERE), "gaps", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    if not payload:
        pytest.skip("this backlog has no gaps left")
    assert payload[0]["resolved"] is True
    assert len(payload[0]["removed_in"]["sha"]) == 40


def test_no_gaps_says_so(tmp_path, capsys):
    roadmap = (
        "# Roadmap\n\n## Block A — The model\n\n"
        + f"- {DESIGNED} **RK1** (deps: —) **A symptom** — a reason. → §RK1\n"
    )
    project(tmp_path, roadmap=roadmap)
    assert main(["-C", str(tmp_path), "gaps"]) == EXIT_OK
    assert "no gaps" in capsys.readouterr().out


# -- the door a one-task-one-commit rule needs (RK1511) ------------------------

#: The opt-in a fold needs: a criterion is written under the absorbing task, and the list is
#: governed on its own declaration (RK1265) exactly as the non-goals are.
GOVERNED_CRITERIA = "[criteria]\nlead = 60\nwhy = 200\n"



def test_a_fold_writes_the_criterion_and_ends_the_line_in_one_write(tmp_path, capsys):
    """RK1511. A task that finds work inside its own sentence cannot do it — the commit is that
    task's — so it files a line, and the tree carries the half-built thing until the second
    line is worked. Measured in the port this tool governs: four of the nine idea-marked lines
    are that exact shape.

    The other reading is that they were never separate work, and had the finding been a
    criterion on the task that found it, the line would have shipped partial and finished under
    the same id. This is the move between the two shapes, and it is one transaction."""
    root = project(tmp_path, declare=GOVERNED_CRITERIA).root
    assert main([
        "-C", str(root), "retire", "RK1", "--folds-into", "RK7",
        "--reason", "It is a check RK7 has to make, not a task of its own.",
    ]) == EXIT_OK
    said = capsys.readouterr().out
    assert "folded   into RK7 as a criterion" in said
    written = (root / "ROADMAP.md").read_text(encoding="utf-8")
    # The departing line's own claim, moved rather than composed (L4).
    assert "## Done when — RK7" in written
    assert "**A first symptom**" in written
    assert "- 📋 **RK1**" not in written


def test_a_fold_into_a_line_that_has_left_is_refused(tmp_path, capsys):
    """`--superseded-by` accepts a shipped id and is right to: work that moved to a task which
    has since landed is a legitimate history. A fold is not that — it says *this was never
    separate work*, which is a claim about a line somebody is still going to do."""
    from composing import runs

    root = project(tmp_path, declare=GOVERNED_CRITERIA).root
    assert main([
        "-C", str(root), "ship", "RK7", "--why", "It works now."
    ]) == EXIT_OK
    capsys.readouterr()
    assert main([
        "-C", str(root), "retire", "RK1", "--folds-into", "RK7", "--reason", "A reason."
    ]) == EXIT_USAGE
    said = capsys.readouterr().err
    # And the door it names runs, which is the whole value of naming one (RK1209).
    ran = runs(root, said)
    assert ran and ran[0][:2] == ["retire", "RK1"], said


def test_the_two_answers_about_where_the_work_went_are_refused_together(tmp_path, capsys):
    # A fold says it was never separate and a supersession says it moved: two subjects, and a
    # call carrying both is a caller who has not decided which happened.
    #
    # Declared on the parser since RK1607. It was raised inside the handler, so `_one_answer`
    # let the pair through, the pair sweep read a correct exit as unaccounted for, and over MCP
    # the rule was reachable only by making the call.
    root = project(tmp_path, declare=GOVERNED_CRITERIA).root
    assert main([
        "-C", str(root), "retire", "RK1", "--folds-into", "RK7",
        "--superseded-by", "RK7", "--reason", "A reason.",
    ]) == EXIT_USAGE
    said = capsys.readouterr().err
    assert "one answer per call" in said
    assert "--folds-into" in said and "--superseded-by" in said


def test_the_payload_says_a_fold_happened_by_a_field(tmp_path, capsys):
    # A field and never a sentence to match: a consumer tells a fold from a supersession
    # without reading prose, which is what every other half of this record already gives it.
    root = project(tmp_path, declare=GOVERNED_CRITERIA).root
    assert main([
        "-C", str(root), "retire", "RK1", "--folds-into", "RK7",
        "--reason", "A reason.", "--json",
    ]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["folded"] == "A first symptom"
    assert payload["superseded_by"] == "RK7"


def test_an_ordinary_retirement_folds_nothing(tmp_path, capsys):
    root = project(tmp_path, declare=GOVERNED_CRITERIA).root
    assert main([
        "-C", str(root), "retire", "RK1", "--reason", "A reason.", "--json"
    ]) == EXIT_OK
    assert json.loads(capsys.readouterr().out)["folded"] == ""


# -- the criterion that was somebody's line (RK1546) ---------------------------


def test_the_brief_of_the_absorbing_task_names_where_the_criterion_came_from(
    tmp_path, capsys
):
    """RK1546, the half RK1511's design named and left. A fold writes the destination into the
    ledger and a criterion under the task, and the criterion says nothing — so RK7's list
    carries a claim whose id is spent and the only route back was `origin` over history.

    Answered where somebody is asking rather than by a field on the bullet: a criterion's
    grammar is a lead and a reason (RK1265), and an id in either is a reference outliving the
    work. `brief` already opens both files, so the join costs a lookup and the store is
    untouched (L2)."""
    root = project(tmp_path, declare=GOVERNED_CRITERIA).root
    assert main([
        "-C", str(root), "retire", "RK1", "--folds-into", "RK7",
        "--reason", "It is a check RK7 has to make, not a task of its own.",
    ]) == EXIT_OK
    capsys.readouterr()
    assert main(["-C", str(root), "brief", "RK7"]) == EXIT_OK
    said = capsys.readouterr().out
    assert "done     RK7: A first symptom  (folded from RK1)" in said, said


def test_a_criterion_nobody_folded_carries_no_origin(tmp_path, capsys):
    """The sparse half, which is nearly every criterion: a clause on a bullet somebody wrote
    directly would name an id that has nothing to do with it, and a reader who saw one
    everywhere would stop reading them."""
    root = project(tmp_path, declare=GOVERNED_CRITERIA).root
    assert main([
        "-C", str(root), "criterion", "add", "--task", "RK7",
        "--lead", "A check nobody folded in", "--why", "Because it is checked here.",
    ]) == EXIT_OK
    capsys.readouterr()
    assert main(["-C", str(root), "brief", "RK7"]) == EXIT_OK
    said = capsys.readouterr().out
    assert "done     RK7: A check nobody folded in" in said, said
    assert "folded from" not in said, said


def test_the_origin_is_published_beside_the_leads_it_is_about(tmp_path, capsys):
    """Keyed by the lead as the answer carries it, so a consumer joins without re-deriving the
    cut `[criteria] lead` makes — and `{}` on a task nothing was folded into, which is an
    answer rather than a build that did not look."""
    root = project(tmp_path, declare=GOVERNED_CRITERIA).root
    assert main([
        "-C", str(root), "retire", "RK1", "--folds-into", "RK7", "--reason", "A reason here.",
    ]) == EXIT_OK
    capsys.readouterr()
    assert main(["-C", str(root), "brief", "RK7", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["done_when_folded"] == {"A first symptom": "RK1"}, payload
    assert set(payload["done_when_folded"]) <= set(payload["done_when_own"])


def test_a_supersession_that_moved_no_criterion_names_nothing(tmp_path, capsys):
    """The other door of the same verb. `--superseded-by` says the work *moved* and writes no
    criterion, so the destination's list is unchanged and there is nothing to attribute — the
    join is on the symptom a fold copied, which a plain supersession never copies."""
    root = project(tmp_path, declare=GOVERNED_CRITERIA).root
    assert main([
        "-C", str(root), "retire", "RK1", "--superseded-by", "RK7", "--reason", "It moved.",
    ]) == EXIT_OK
    capsys.readouterr()
    assert main(["-C", str(root), "brief", "RK7", "--json"]) == EXIT_OK
    assert json.loads(capsys.readouterr().out)["done_when_folded"] == {}
