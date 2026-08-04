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
from roadkeep.document import Document
from roadkeep.history import gaps, searchable
from roadkeep.markers import refresh
from roadkeep.picking import pick
from roadkeep.schema import DESIGNED, RETIRED, SHIPPED, Schema, SchemaError
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


# -- what it refuses ----------------------------------------------------------


def test_a_replacement_in_neither_file_is_refused(tmp_path):
    # A pointer to nothing is the exact defect being recorded against.
    config = project(tmp_path)
    with pytest.raises(NoSuchReplacement):
        retire(config, "RK1", reason="something else covers it.", superseded_by="RK99")
    assert (tmp_path / "CHANGELOG.md").read_text(encoding="utf-8") == LEDGER


def test_a_line_cannot_supersede_itself(tmp_path):
    config = project(tmp_path)
    with pytest.raises(NoSuchReplacement):
        retire(config, "RK1", reason="itself.", superseded_by="RK1")


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
    assert "still    RK4 name RK1" in out
    assert out.splitlines()[-1] == "  event    RK1  Block A  open"


def test_a_refused_retirement_writes_nothing_and_exits_two(tmp_path, capsys):
    project(tmp_path)
    assert (
        main(["-C", str(tmp_path), "retire", "RK1", "--superseded-by", "RK99",
              "--reason", "x."])
        == EXIT_USAGE
    )
    assert "in neither file" in capsys.readouterr().err
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
    assert "RK2    unresolvable" in out
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
