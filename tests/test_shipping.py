"""Three edits or none, and the shape of the files they leave behind (RK6).

The failure this task exists to remove is not a crash: it is a backlog where the line
left the roadmap and the ledger entry never arrived, which no test of one file can see.
So the assertions here are whole-file comparisons across all three files, and the
refusal cases assert that *nothing* changed anywhere.

The second thing under test is a shape the round-trip cannot catch, because both
spellings round-trip: a removed line leaves a doubled blank behind, and a deleted
section leaves either an orphaned blank line or the next section glued to the previous
one. Those are the assertions that look pedantic and are the reason the diff of a
shipped task is one line long instead of four.
"""

from __future__ import annotations

import io
import json
from pathlib import Path

import pytest

from roadkeep.provenance import invocation

from roadkeep import claiming
from roadkeep.kernel import document
from roadkeep.authoring import UnknownBlock, add, set_status
from roadkeep.backlog import Backlog, DepStatus
from roadkeep.cli import EXIT_GATE, EXIT_OK, EXIT_USAGE, main
from roadkeep.config import Config
from roadkeep.kernel.document import Document, RoundTripError, StaleFile
from roadkeep.linting import lint
from roadkeep.kernel.schema import (
    DESIGNED,
    IN_PROGRESS,
    PARTIAL,
    SHIPPED,
    Dep,
    Schema,
    SchemaError,
    width,
)
from roadkeep.shipping import AlreadyRecorded, NoQualifier, NoSuchPath, SecondPartial
from roadkeep.sections import SectionOccupied
from roadkeep.shipping import (
    AlreadySuperseded,
    Divergent,
    InheritedClaim,
    NoCompletion,
    NoDesign,
    NoOutcome,
    NoSupersession,
    PartRecorded,
    AlreadyShipped,
    Closure,
    NoRestatement,
    NoDecision,
    NotDecided,
    NotOpen,
    RecordingCrowded,
    RemainderRefused,
    SupersessionCrowded,
    Wrapped,
    record,
    retire,
    recording_cost,
    ship,
    supersede,
    supersession_cost,
)
from roadkeep.shipping import amend as amend_record

ROADMAP = "docs/ROADMAP.md"
CHANGELOG = "docs/CHANGELOG.md"
IMPROVEMENTS = "docs/IMPROVEMENTS.md"

RK1 = "- 📋 **RK1** (deps: —) **A first symptom** — Because of a reason. → §RK1"
RK2 = "- 📋 **RK2** (deps: RK1) **A second symptom** — Because of another reason. → §RK2"
RK3 = "- 📋 **RK3** (deps: RK1) **A third symptom** — Because of a third reason. → §RK3"
SHIPPED_RK1 = "- ✅ **RK1** **A first symptom** — Because of a reason."

BACKLOG = f"""# Roadmap

## Block A — The model

{RK1}
{RK2}

## Block B — Authoring

{RK3}

## Non-goals

- not a task line
"""

LEDGER = """# Shipped

## Block A — The model

## Block B — Authoring
"""

RATIONALE = """# Improvements

## Block A — The model

### §RK1 A first design

The reasoning that the line has no room for.

#### §RK1.1 A subsection of it

Which belongs to the section above and not to the next one.

### §RK2 A second design

The reasoning for the second one.

## Block B — Authoring

### §RK3 A third design

The last section in the file.
"""


def project(
    tmp_path: Path,
    *,
    roadmap: str = BACKLOG,
    changelog: str | None = LEDGER,
    improvements: str | None = RATIONALE,
    extra_config: str = "",
) -> Config:
    """A throwaway project with the files it declares, and only those.

    ``extra_config`` follows the `[files]` table, for the tables a test declares whole.
    """
    declared = {ROADMAP: roadmap, CHANGELOG: changelog, IMPROVEMENTS: improvements}
    lines = ['prefix = "RK"', "[files]"]
    lines += [
        f'{role} = "{path}"'
        for role, path in (
            ("roadmap", ROADMAP),
            ("changelog", CHANGELOG),
            ("improvements", IMPROVEMENTS),
        )
        if declared[path] is not None
    ]
    (tmp_path / "roadkeep.toml").write_text(
        "\n".join(lines) + "\n" + extra_config, encoding="utf-8"
    )
    for path, body in declared.items():
        if body is None:
            continue
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8", newline="") as handle:
            handle.write(body)
    return Config.discover(tmp_path)


def read(config: Config, name: str) -> str:
    with (config.root / name).open("r", encoding="utf-8", newline="") as handle:
        return handle.read()


def files(config: Config) -> tuple[str, str, str]:
    return read(config, ROADMAP), read(config, CHANGELOG), read(config, IMPROVEMENTS)


# -- the three edits ---------------------------------------------------------


def test_the_line_leaves_the_roadmap_and_arrives_in_the_ledger(tmp_path):
    config = project(tmp_path)
    shipment = ship(config, "RK1", why="Because of a reason.")
    shipment.save()
    roadmap, ledger, _ = files(config)
    # The line is gone and the two lines that named it now say so (RK8): the fourth edit
    # of the four this task exists to make into one.
    assert roadmap == BACKLOG.replace(f"{RK1}\n", "").replace(
        "(deps: RK1)", "(deps: RK1 ✅)"
    )
    assert ledger == LEDGER.replace(
        "## Block A — The model\n\n", f"## Block A — The model\n\n{SHIPPED_RK1}\n\n"
    )
    assert shipment.removed_from == 5
    assert shipment.ledger.rendered == SHIPPED_RK1


def test_the_ledger_entry_drops_the_deps_and_the_pointer(tmp_path):
    # Both are refused by the ledger schema: a shipped line has no dependency left to
    # state, and the section its pointer named is deleted in this same command.
    config = project(tmp_path)
    shipment = ship(config, "RK2", why="Because of another reason.")
    assert shipment.ledger.entry.task.deps == ()
    assert shipment.ledger.entry.task.ref is None
    assert shipment.ledger.rendered == (
        "- ✅ **RK2** **A second symptom** — Because of another reason."
    )


def test_the_ledger_entry_drops_the_requirements_too(tmp_path):
    # RK1297, and the deps' own reason one group over: a requirement says what has to be
    # present for work to be finishable, and a line that left has nothing to finish — the
    # DualSense was on the desk, or this never shipped.
    from roadkeep.shipping import as_recorded

    from roadkeep.kernel.schema import SHIPPED, Task

    line = Task(
        id="RK9",
        status="📋",
        block="A",
        symptom="A symptom",
        why="Because of a reason.",
        requires=("ps5",),
        ref="RK9",
    )
    assert as_recorded(line, SHIPPED, None).requires == ()


def test_the_rationale_section_is_deleted_with_its_subsections(tmp_path):
    config = project(tmp_path)
    shipment = ship(config, "RK1", why="Because of a reason.")
    shipment.save()
    _, _, rationale = files(config)
    assert "§RK1" not in rationale
    assert "A subsection of it" not in rationale
    # The next section is neither glued to the heading above it nor left with an extra
    # blank line: what the file looked like before is what it looks like after.
    assert rationale == RATIONALE.replace(
        """### §RK1 A first design

The reasoning that the line has no room for.

#### §RK1.1 A subsection of it

Which belongs to the section above and not to the next one.

""",
        "",
    )
    assert shipment.dropped.anchor == "RK1"
    assert (shipment.dropped.first, shipment.dropped.last) == (5, 12)


def test_the_last_section_in_the_file_leaves_no_trailing_blank(tmp_path):
    config = project(tmp_path)
    ship(config, "RK3", why="Because of a third reason.").save()
    _, _, rationale = files(config)
    assert rationale.endswith("## Block B — Authoring\n")


def test_removing_the_last_task_of_a_block_leaves_one_blank_line(tmp_path):
    config = project(tmp_path)
    ship(config, "RK3", why="Because of a third reason.").save()
    roadmap, _, _ = files(config)
    # The block is left as an empty block reads everywhere else — heading, one blank,
    # next heading — and not as a paragraph break the file never had.
    assert "\n\n\n" not in roadmap
    assert roadmap == BACKLOG.replace(f"{RK3}\n\n", "")


def test_shipping_the_last_line_of_the_file_leaves_no_trailing_blank(tmp_path):
    config = project(tmp_path, roadmap=f"## Block A — The model\n\n{RK1}\n")
    ship(config, "RK1", why="Because of a reason.").save()
    assert read(config, ROADMAP) == "## Block A — The model\n"


def test_the_files_keep_their_line_endings(tmp_path):
    config = project(
        tmp_path,
        roadmap=BACKLOG.replace("\n", "\r\n"),
        changelog=LEDGER.replace("\n", "\r\n"),
        improvements=RATIONALE.replace("\n", "\r\n"),
    )
    ship(config, "RK1", why="Because of a reason.").save()
    for name in (ROADMAP, CHANGELOG, IMPROVEMENTS):
        assert "\n" not in read(config, name).replace("\r\n", ""), name


# -- the fourth edit ---------------------------------------------------------


def test_every_line_that_named_the_task_is_re_derived(tmp_path):
    # In the same transaction, because `(deps: RK1)` becomes false at exactly the moment
    # this command runs and nothing else would ever revisit it (RK8).
    config = project(tmp_path)
    assert ship(config, "RK1", why="Because of a reason.").refreshed == ("RK2", "RK3")


def test_a_task_that_nothing_depends_on_re_derives_nothing(tmp_path):
    config = project(tmp_path)
    assert ship(config, "RK3", why="Because of a third reason.").refreshed == ()


def test_the_design_sentence_is_kept_unless_the_author_restates_it(tmp_path):
    config = project(tmp_path)
    assert ship(config, "RK1", why="Because of a reason.").ledger.entry.task.why == "Because of a reason."
    restated = ship(config, "RK1", why="Which is now the outcome.")
    assert restated.ledger.rendered.endswith("— Which is now the outcome.")


def test_a_restated_why_is_validated_like_any_other(tmp_path):
    config = project(tmp_path)
    with pytest.raises(SchemaError) as raised:
        ship(config, "RK1", why="Two sentences. Which is one too many.")
    assert [v.code for v in raised.value.violations] == ["why.sentences"]
    assert files(config) == (BACKLOG, LEDGER, RATIONALE)


# -- refusing, with three untouched files ------------------------------------


def test_a_task_that_is_not_open_is_refused(tmp_path):
    config = project(tmp_path)
    with pytest.raises(NotOpen) as raised:
        ship(config, "RK9", why="Because of a reason.")
    assert "nothing there carries that id" in str(raised.value)
    assert files(config) == (BACKLOG, LEDGER, RATIONALE)


def test_a_task_already_in_the_ledger_says_so(tmp_path):
    # The two ways of not being open are different answers, and reporting "no such task"
    # for one that shipped yesterday sends the reader to the wrong file.
    config = project(
        tmp_path,
        roadmap=BACKLOG.replace(f"{RK1}\n", ""),
        changelog=LEDGER + f"\n{SHIPPED_RK1}\n",
    )
    with pytest.raises(NotOpen) as raised:
        ship(config, "RK1", why="Because of a reason.")
    assert "already in the changelog" in str(raised.value)


def half_shipped(tmp_path, marker: str = "✅"):
    """The state adoption produces: the entry moved to the ledger by hand, the line left
    behind wearing the marker a roadmap may not carry. Shio's `- ✅ **SH22** …` is this, and it
    was four findings with no door (RK62)."""
    return project(
        tmp_path,
        roadmap=BACKLOG.replace(RK1, RK1.replace("📋", marker, 1)),
        changelog=LEDGER.replace(
            "## Block A — The model\n", f"## Block A — The model\n\n{SHIPPED_RK1}\n"
        ),
    )


def test_shipping_twice_is_refused_by_the_ledger(tmp_path):
    config = project(tmp_path)
    ship(config, "RK1", why="Because of a reason.").save()
    # The roadmap line is gone, so the second call is refused by NotOpen — there is no line
    # to close and nothing to record.
    with pytest.raises(NotOpen):
        ship(config, "RK1", why="Because of a reason.")


# -- a section more than one line points at (RK64) ----------------------------


SHARED = RATIONALE.replace("### §RK2 A second design", "### §RK1.epic A shared design")


def outline_project(tmp_path):
    """A project that numbers by hand, where two lines may name one section — which is what
    Shio's tenant epic does with four of them (§VI.1)."""
    shared = """# Improvements

## Block A — The model

### §I.1 A design two tasks share (RK1, RK2)

The reasoning both lines point at.

## Block B — Authoring

### §I.2 A third design (RK3)

Which only one line points at.
"""
    config = project(
        tmp_path,
        roadmap=BACKLOG.replace("→ §RK1", "→ §I.1")
        .replace("→ §RK2", "→ §I.1")
        .replace("→ §RK3", "→ §I.2"),
        improvements=shared,
    )
    declared = (tmp_path / "roadkeep.toml").read_text(encoding="utf-8")
    (tmp_path / "roadkeep.toml").write_text(
        declared.replace('prefix = "RK"', 'prefix = "RK"\nref_scheme = "outline"'),
        encoding="utf-8",
    )
    return Config.discover(tmp_path)


def test_a_section_another_open_line_points_at_is_kept(tmp_path):
    # Shio's §VI.1 is one design for SH44–SH47; shipping the first deleted it and left three
    # live pointers resolving to nothing, with a lint finding as the only trace (RK64).
    config = outline_project(tmp_path)
    shipment = ship(config, "RK1", why="Because of a reason.")
    shipment.save()
    assert shipment.dropped is None
    assert shipment.kept == "§I.1 is also pointed at by RK2"
    assert "§I.1" in read(config, IMPROVEMENTS)


def test_the_last_line_pointing_at_a_shared_section_still_drops_it(tmp_path):
    # Not a permanent exemption: when the last owner leaves, the section leaves with it.
    config = outline_project(tmp_path)
    ship(config, "RK1", why="Because of a reason.").save()
    shipment = ship(Config.discover(tmp_path), "RK2", why="Because of another reason.")
    shipment.save()
    assert shipment.dropped is not None and shipment.dropped.anchor == "I.1"
    assert "§I.1" not in read(config, IMPROVEMENTS)


# -- a section nesting another line's (RK78) ----------------------------------


NESTING = """# Improvements

## Block A — The model

## §I.1 An epic (RK1)

The reasoning the epic itself has.

### §I.2 A design under it (RK2)

Which belongs to RK2 and is only nested under the epic.

### §I.3 A second design under it (RK3)

Which belongs to RK3, and is the other one a drop would take.

## Block B — Authoring
"""


def nesting_project(tmp_path):
    """Shio's SH326: a level-2 epic whose level-3 children are other open tasks' designs."""
    config = project(
        tmp_path,
        roadmap=BACKLOG.replace("→ §RK1", "→ §I.1")
        .replace("→ §RK2", "→ §I.2")
        .replace("→ §RK3", "→ §I.3"),
        improvements=NESTING,
    )
    declared = (tmp_path / "roadkeep.toml").read_text(encoding="utf-8")
    (tmp_path / "roadkeep.toml").write_text(
        declared.replace('prefix = "RK"', 'prefix = "RK"\nref_scheme = "outline"'),
        encoding="utf-8",
    )
    return Config.discover(tmp_path)


def test_a_subtree_holding_another_line_s_design_is_refused(tmp_path):
    # The measured failure: 160 lines deleted by a transaction that reported dropping one
    # section, leaving two live pointers resolving to nothing and `git checkout` on the
    # whole file as the only remedy — which discards the part of the ship that was correct.
    config = nesting_project(tmp_path)
    before = files(config)
    with pytest.raises(SectionOccupied) as raised:
        ship(config, "RK1", why="Because of a reason.")
    # Every claim, not the first: a refusal that names one of two turns a single lift into
    # a conversation, which is the same argument the schema's violations make.
    assert "§I.2 (RK2)" in str(raised.value) and "§I.3 (RK3)" in str(raised.value)
    assert files(config) == before


def test_the_refusal_lifts_once_the_nested_lines_have_shipped(tmp_path):
    # Not a permanent exemption either: the epic is droppable the moment nothing else claims
    # anything under it, and the two ships that get there each drop their own section.
    config = nesting_project(tmp_path)
    ship(config, "RK2", why="Because of another reason.").save()
    ship(Config.discover(tmp_path), "RK3", why="Because of a third reason.").save()
    shipment = ship(Config.discover(tmp_path), "RK1", why="Because of a reason.")
    shipment.save()
    assert shipment.dropped is not None and shipment.dropped.anchor == "I.1"
    assert "§I.1" not in read(config, IMPROVEMENTS)


def test_a_subsection_of_the_line_s_own_prose_is_dropped_and_reported(tmp_path):
    # The other half of the rule: ownership bounds the deletion, not depth — §RK1.1 is RK1's
    # own and still goes, and the transaction states its real size rather than the anchor's.
    config = project(tmp_path)
    shipment = ship(config, "RK1", why="Because of a reason.")
    assert shipment.nested == ("RK1.1",)
    shipment.save()
    assert "§RK1.1" not in read(config, IMPROVEMENTS)


def test_ship_prints_what_the_subtree_took(tmp_path, capsys):
    project(tmp_path)
    assert main(["-C", str(tmp_path), "ship", "RK1", "--why", "Because of a reason."]) == EXIT_OK
    assert "nested   §RK1.1 went with it" in capsys.readouterr().out


def test_a_refused_subtree_exits_two_and_writes_nothing(tmp_path, capsys):
    config = nesting_project(tmp_path)
    before = files(config)
    assert main(["-C", str(tmp_path), "ship", "RK1", "--why", "Because of a reason."]) == EXIT_USAGE
    assert "resolving to nothing" in capsys.readouterr().err
    assert files(config) == before


# -- the line the ledger already recorded (RK62) ------------------------------


def test_a_line_whose_id_the_ledger_holds_is_closed_and_the_ledger_is_untouched(tmp_path):
    config = half_shipped(tmp_path)
    before = read(config, CHANGELOG)
    closure = ship(config, "RK1")
    assert isinstance(closure, Closure)
    assert closure.marker == "✅" and closure.recorded.task.id == "RK1"
    closure.save()
    # The one edit that was missing, and not a second entry: the ledger is byte-identical,
    # and the roadmap no longer carries the line.
    assert read(config, CHANGELOG) == before
    assert "RK1" not in config.document("roadmap").by_id()


def test_closing_drops_the_section_and_re_derives_the_dependents(tmp_path):
    config = half_shipped(tmp_path)
    closure = ship(config, "RK1")
    closure.save()
    assert closure.dropped is not None and closure.dropped.anchor == "RK1"
    assert "§RK1" not in read(config, IMPROVEMENTS)
    # RK2 and RK3 wait on RK1, and both annotations were written when RK1 was open.
    assert closure.refreshed == ("RK2", "RK3")


def test_a_closure_releases_the_claim_its_departure_would_have(tmp_path):
    # RK306: `Departure.save` obeys RK162 and this shape — the same departure minus the ledger
    # edit — skipped it, so the line closed and the dated row and its scope stayed behind.
    config = half_shipped(tmp_path, marker=IN_PROGRESS)
    try:
        claiming.follow(tmp_path, "RK1", IN_PROGRESS, config.document("roadmap").entries)
        claiming.scope(config, "RK1", ["src/a.py"])
        closure = ship(config, "RK1")
        assert isinstance(closure, Closure)
        # Read while it is still live, as the departure reads it (RK294).
        assert closure.scope is not None and closure.scope.mine == ("src/a.py",)
        closure.save()
        assert claiming._read(tmp_path) == {}  # noqa: SLF001
    finally:
        claiming.path(tmp_path).unlink(missing_ok=True)


def test_a_restated_why_is_refused_where_the_ledger_is_not_written(tmp_path):
    config = half_shipped(tmp_path)
    before = files(config)
    with pytest.raises(NoRestatement) as raised:
        ship(config, "RK1", why="Which the ledger already says.")
    assert "the ledger is not written here" in str(raised.value)
    assert files(config) == before


def test_a_partial_marker_beside_an_unqualified_entry_is_closed(tmp_path):
    # Reversed by RK1075, and the reason is the ledger. This read a ⏳ line as a live partial
    # whatever the entry said, so the one state where the two files *disagree* — a partial
    # marker beside an entry naming no half — had no verb at all: `ship` and `retire` refused
    # here, `defer` refused as a pause between open and terminal, and the gate is silent by
    # design (RK121). Shio filed three capture reports on it and closed it with the editor.
    #
    # The entry is the record of what shipped, and it says the whole did. So the line is what
    # is stale, and closing removes it and writes nothing to the ledger (RK62).
    config = half_shipped(tmp_path, marker="⏳")
    ship(config, "RK1").save()
    assert "**RK1**" not in read(config, ROADMAP)
    # The ledger is untouched: this call closes a line, it does not record anything.
    assert read(config, CHANGELOG).count("**RK1**") == 1


def test_retiring_a_line_the_ledger_recorded_is_still_refused(tmp_path):
    # Closing is not retiring: the work shipped, and a 🗑 entry beside the ✅ would be the
    # ledger disagreeing with itself about how the line left.
    config = half_shipped(tmp_path)
    with pytest.raises(AlreadyShipped) as raised:
        retire(config, "RK1", reason="Nobody will do it.")
    assert "disagree with itself" in str(raised.value)


def test_a_ledger_with_no_heading_for_the_block_is_refused(tmp_path):
    config = project(tmp_path, changelog="# Shipped\n\n## Block A — The model\n")
    with pytest.raises(UnknownBlock) as raised:
        ship(config, "RK3", why="Because of a third reason.")
    assert "Block B" in str(raised.value)
    assert read(config, ROADMAP) == BACKLOG


def test_that_refusal_names_the_file_it_read(tmp_path):
    # RK257: the roadmap plainly declares Block B, so a refusal naming no file reads as "your
    # label is wrong" — which is the one thing it is not. RK296 dropped the list that went
    # with it: 90 labels bury the two clauses that are the remedy.
    config = project(tmp_path, changelog="# Shipped\n\n## Block A — The model\n")
    with pytest.raises(UnknownBlock) as raised:
        ship(config, "RK3", why="Because of a third reason.")
    assert f"Block B in {CHANGELOG}:" in str(raised.value)
    assert "declares: A" not in str(raised.value)


def test_that_refusal_spells_the_one_command_that_repairs_it(tmp_path):
    # The recovery is `block add`, which declares the heading in every governed file still
    # missing it and skips the roadmap that already has it. The refusal knows enough to say so.
    config = project(tmp_path, changelog="# Shipped\n\n## Block A — The model\n")
    with pytest.raises(UnknownBlock) as raised:
        ship(config, "RK3", why="Because of a third reason.")
    assert '`block add B --title "<its title>"`' in str(raised.value)


def test_a_drifted_roadmap_is_not_rewritten(tmp_path):
    drifted = BACKLOG.replace("→ §RK1", "→ §7.1")
    config = project(tmp_path, roadmap=drifted)
    with pytest.raises(RoundTripError):
        ship(config, "RK2", why="Because of another reason.")
    assert files(config) == (drifted, LEDGER, RATIONALE)


def test_a_missing_section_is_reported_and_not_an_error(tmp_path):
    # A task can ship without a rationale section; failing at the moment the author is
    # finishing would be an obstacle, and silence would read as a section that was there.
    config = project(tmp_path, improvements="# Improvements\n\n## Block A — The model\n")
    shipment = ship(config, "RK1", why="Because of a reason.")
    assert shipment.dropped is None
    assert "no §RK1 section" in shipment.kept
    shipment.save()
    assert read(config, IMPROVEMENTS) == "# Improvements\n\n## Block A — The model\n"


def test_a_project_with_no_improvements_file_ships_two_edits(tmp_path):
    config = project(tmp_path, improvements=None)
    shipment = ship(config, "RK1", why="Because of a reason.")
    assert shipment.prose is None
    # Every prose role, because a project declaring only a strategy file declares one (RK196):
    # the old sentence named the improvements file and was the reason a strategy section
    # outlived the line pointing at it.
    assert shipment.kept == "this project declares no improvements or strategy file"
    shipment.save()
    assert read(config, ROADMAP) == BACKLOG.replace(f"{RK1}\n", "").replace(
        "(deps: RK1)", "(deps: RK1 ✅)"
    )


# -- the command -------------------------------------------------------------


def test_the_command_reports_every_edit_it_made(tmp_path, capsys):
    config = project(tmp_path)
    assert main(["-C", str(tmp_path), "ship", "RK1", "--why", "Because of a reason."]) == EXIT_OK
    out = capsys.readouterr().out
    assert f"RK1 → {CHANGELOG}:5 under Block A" in out
    assert f"removed  {ROADMAP}:5" in out
    assert f"dropped  §RK1 (5-12) from {IMPROVEMENTS}" in out
    assert "derived  RK2, RK3" in out
    assert SHIPPED_RK1 in read(config, CHANGELOG)


def test_json_carries_every_edit(tmp_path, capsys):
    project(tmp_path)
    assert main(["-C", str(tmp_path), "ship", "RK2", "--why", "Because of another reason.", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["changelog"]["file"] == CHANGELOG
    assert payload["roadmap"] == {"file": ROADMAP, "removed": 6}
    assert payload["improvements"]["dropped"]["anchor"] == "RK2"
    assert payload["refreshed"] == []


def test_a_refusal_exits_two_and_writes_nothing(tmp_path, capsys):
    config = project(tmp_path)
    assert main(["-C", str(tmp_path), "ship", "RK9", "--why", "Because of a reason."]) == EXIT_USAGE
    assert "no open task RK9" in capsys.readouterr().err
    assert files(config) == (BACKLOG, LEDGER, RATIONALE)


def test_a_drifted_file_exits_one_because_the_gate_says_no(tmp_path, capsys):
    project(tmp_path, roadmap=BACKLOG.replace("→ §RK1", "→ §7.1"))
    assert main(["-C", str(tmp_path), "ship", "RK2", "--why", "Because of another reason."]) == EXIT_GATE
    assert "will not be rewritten" in capsys.readouterr().err


# -- the file that moved under the writer (RK116) ----------------------------


def test_a_ship_whose_ledger_moved_under_it_writes_none_of_the_three(tmp_path):
    # The all-or-nothing claim, taken one layer down. `save` writes the ledger first, so a
    # check made per file would refuse the roadmap *after* the ledger had already landed —
    # the half-applied state RK6 exists to prevent, produced by the fix for RK116.
    config = project(tmp_path)
    shipment = ship(config, "RK1", why="Because of a reason.")
    moved = LEDGER.replace("## Block B", f"{SHIPPED_RK1.replace('RK1', 'RK8')}\n\n## Block B")
    with (config.root / CHANGELOG).open("w", encoding="utf-8", newline="") as handle:
        handle.write(moved)

    with pytest.raises(StaleFile, match="changed since it was read"):
        shipment.save()
    assert files(config) == (BACKLOG, moved, RATIONALE)


def test_a_ship_whose_roadmap_moved_under_it_leaves_the_ledger_alone(tmp_path):
    config = project(tmp_path)
    shipment = ship(config, "RK1", why="Because of a reason.")
    moved = BACKLOG.replace(f"{RK2}\n", "")
    with (config.root / ROADMAP).open("w", encoding="utf-8", newline="") as handle:
        handle.write(moved)

    with pytest.raises(StaleFile):
        shipment.save()
    assert files(config) == (moved, LEDGER, RATIONALE)


def test_a_writer_landing_after_the_first_file_is_staged_still_writes_none(tmp_path, monkeypatch):
    # The window the pre-flight left open (RK131): asking every target and *then* rendering
    # and writing each one puts the second file's question after the first file's write, so
    # a writer landing between them produces the half-applied state the question exists to
    # prevent. Staged first, asked second, renamed last — and the intruder is caught with
    # nothing of this transaction on disk.
    config = project(tmp_path)
    shipment = ship(config, "RK1", why="Because of a reason.")
    moved = BACKLOG.replace(f"{RK2}\n", "")
    real = document.stage

    def racing(target: Path, text: str) -> Path:
        staged = real(target, text)
        if target.name == "CHANGELOG.md":  # the first file the transaction stages
            with (config.root / ROADMAP).open("w", encoding="utf-8", newline="") as handle:
                handle.write(moved)
        return staged

    monkeypatch.setattr("roadkeep.kernel.document.stage", racing)
    with pytest.raises(StaleFile, match="changed since it was read"):
        shipment.save()
    assert files(config) == (moved, LEDGER, RATIONALE)


def test_a_second_writer_exits_one_and_says_to_re_run(tmp_path, capsys, monkeypatch):
    # Through the CLI, because the exit code is the contract: a lost line that exits 0 is
    # the whole symptom, and a gate refusal is exit 1 (RK116). The other process is staged
    # in the window it actually occupies — after this command read the files, before it
    # wrote them — which is the only place the race exists.
    config = project(tmp_path)

    def racing(*args, **kwargs):
        shipment = ship(*args, **kwargs)
        with (config.root / CHANGELOG).open("a", encoding="utf-8", newline="") as handle:
            handle.write(SHIPPED_RK1.replace("RK1", "RK8") + "\n")
        return shipment

    monkeypatch.setattr("roadkeep.verbs.shipping.ship", racing)
    assert main(["-C", str(tmp_path), "ship", "RK1", "--why", "Because of a reason."]) == EXIT_GATE
    assert "re-run the command" in capsys.readouterr().err
    # Nothing of this transaction landed, and the other writer's line is untouched.
    assert read(config, ROADMAP) == BACKLOG
    assert read(config, IMPROVEMENTS) == RATIONALE
    assert "RK8" in read(config, CHANGELOG)
    assert "**RK1**" not in read(config, CHANGELOG)


# -- which halfway state a crash can leave (RK118) ---------------------------


def written_in_order(config: Config, monkeypatch) -> list[str]:
    """The three files in the order the transaction renames them into place (RK131)."""
    order: list[str] = []
    real = document.commit

    def watched(scratch, target):
        order.append(config.relative(target))
        return real(scratch, target)

    monkeypatch.setattr("roadkeep.kernel.document.commit", watched)
    return order


def test_the_ledger_is_written_first_and_the_rationale_file_last(tmp_path, monkeypatch):
    # Three renames are three moments even when each one lands whole (RK118), so the order
    # decides which halfway states a crash can leave. This is the sequence the two tests
    # below are about; asserted here so a reordering fails loudly rather than quietly.
    config = project(tmp_path)
    shipment = ship(config, "RK1", why="Because of a reason.")
    order = written_in_order(config, monkeypatch)
    shipment.save()
    assert order == [CHANGELOG, ROADMAP, IMPROVEMENTS]


def test_stopping_after_the_ledger_loses_nothing_and_is_reported(tmp_path):
    # The property the order buys, run rather than asserted: write only the first of the
    # three and everything is still on disk — the line, the entry and the design — with the
    # id in two files, which `lint` names. Loud and lossless is the whole bar for a state a
    # crash can leave.
    config = project(tmp_path)
    shipment = ship(config, "RK1", why="Because of a reason.")
    shipment.ledger.document.save()  # and then the process dies

    roadmap, ledger, improvements = files(config)
    assert RK1 in roadmap
    assert SHIPPED_RK1 in ledger
    assert "The reasoning that the line has no room for." in improvements
    codes = {f.code for f in lint(Config.discover(tmp_path)).findings}
    assert "id.two-files" in codes


def test_the_order_reversed_would_lose_the_task_silently(tmp_path):
    # Why the ledger goes first, stated as the thing that does not happen. Writing the
    # roadmap alone removes the line while no file records that it shipped: the task is
    # gone, and `lint` has nothing to report because a roadmap with one fewer line is a
    # roadmap. That is the one state no gate can see, and it is what the order avoids.
    config = project(tmp_path)
    shipment = ship(config, "RK1", why="Because of a reason.")
    shipment.roadmap.save()  # the order this transaction deliberately does not use

    roadmap, ledger, _ = files(config)
    assert RK1 not in roadmap and "**RK1**" not in ledger
    assert "id.two-files" not in {f.code for f in lint(Config.discover(tmp_path)).findings}


def test_the_rationale_file_is_written_last_because_its_write_is_a_deletion(tmp_path):
    # Stopping before it leaves a section nothing points at, which `lint` reports and
    # `section drop` removes — with the design still on disk. The reverse would delete the
    # design while the line still named it: a pointer to nothing, recoverable only from git.
    config = project(tmp_path)
    shipment = ship(config, "RK1", why="Because of a reason.")
    shipment.ledger.document.save()
    shipment.roadmap.save()  # and then the process dies

    improvements = read(config, IMPROVEMENTS)
    assert "§RK1 A first design" in improvements
    assert "The reasoning that the line has no room for." in improvements


# -- a task delivered in halves (RK121) --------------------------------------


PARTIAL_RK1 = "- ✅ **RK1 (local half)** **A first symptom** — Because of a reason."


def test_a_partial_records_what_landed_and_leaves_the_line_open(tmp_path):
    # The third state the model did not have: open in the roadmap and recorded in the
    # ledger were the only two, so work delivered in halves was neither.
    config = project(tmp_path)
    landed = ship(config, "RK1", part="local half", why="Because of a reason.")
    landed.save()
    roadmap, ledger, improvements = files(config)
    assert PARTIAL_RK1 in ledger
    assert RK1.replace("📋", "⏳") in roadmap
    # The design stays: it still has the rest of the work to describe.
    assert "§RK1 A first design" in improvements


def test_a_partial_marks_the_line_as_partial_where_the_project_declares_that_marker():
    assert PARTIAL in Schema().markers  # the default set, which is where ⏳ comes from


def test_a_line_a_project_cannot_mark_partial_keeps_the_marker_it_had(tmp_path):
    # The marker set is the project's (L6), so a command that invented one would write a
    # line the project's own gate refuses. The line still stays open, which is the claim.
    config = project(tmp_path)
    (tmp_path / "roadkeep.toml").write_text(
        (tmp_path / "roadkeep.toml").read_text(encoding="utf-8")
        + '\n[markers]\nopen = ["📋"]\n',
        encoding="utf-8",
    )
    config = Config.discover(tmp_path)
    landed = ship(config, "RK1", part="local half", why="Because of a reason.")
    assert landed.status == "📋"
    landed.save()
    assert RK1 in read(config, ROADMAP)


def test_completing_a_partial_replaces_the_entry_instead_of_adding_a_second(tmp_path):
    # The half that can be *maintained*: only a verb knows when "local half" stops being
    # true, and five of the corpus's thirteen qualifiers name work that has since finished.
    config = project(tmp_path)
    ship(config, "RK1", part="local half", why="Because of a reason.").save()
    ship(Config.discover(tmp_path), "RK1", why="All of it landed.").save()

    roadmap, ledger, improvements = files(config)
    assert ledger.count("**RK1") == 1
    assert "local half" not in ledger
    assert "- ✅ **RK1** **A first symptom** — All of it landed." in ledger
    assert RK1 not in roadmap  # the line finally leaves
    assert "§RK1 A first design" not in improvements  # and the design goes with it


def test_the_completing_entry_keeps_the_line_the_partial_took(tmp_path):
    # Replaced in place, not removed and re-added: an entry that moved to the end of its
    # block on completion would reorder history for a reason that is not chronology.
    config = project(tmp_path)
    ship(config, "RK2", part="the first half", why="Because of another reason.").save()
    ship(Config.discover(tmp_path), "RK1", why="Because of a reason.").save()  # a later shipment lands after it
    before = read(config, CHANGELOG).splitlines().index(
        "- ✅ **RK2 (the first half)** **A second symptom** — Because of another reason."
    )
    ship(Config.discover(tmp_path), "RK2", why="Because of another reason.").save()
    after = read(config, CHANGELOG).splitlines().index(
        "- ✅ **RK2** **A second symptom** — Because of another reason."
    )
    assert before == after


def test_a_second_partial_for_one_id_is_refused(tmp_path):
    # It would state the id twice in the ledger, which is `id.duplicate` and the shape
    # RK127 is about. One partial, then a completion.
    config = project(tmp_path)
    ship(config, "RK1", part="local half", why="Because of a reason.").save()
    with pytest.raises(SecondPartial, match="already records a half"):
        ship(Config.discover(tmp_path), "RK1", part="the other half", why="Half of it.")


def test_the_second_partial_names_the_id_the_next_step_takes(tmp_path):
    # RK191: the check is right and its sentence was not. `AlreadyRecorded` names the entry
    # in the way, which is the whole answer at the door it was written for — an id the
    # ledger closed — and here leaves the caller to invent the id a step is filed under.
    config = project(tmp_path)
    ship(config, "RK1", part="local half", why="Because of a reason.").save()
    with pytest.raises(SecondPartial) as raised:
        ship(Config.discover(tmp_path), "RK1", part="the other half", why="Half of it.")
    message = str(raised.value)
    assert "CHANGELOG.md:5 (local half)" in message  # still where the first half is
    assert f"{invocation()} add --block <x>" in message and "names RK1" in message
    # And the two exits that are not a new line, because both are one word away from here.
    assert "ship RK1` instead" in message and "record amend RK1 --part" in message


def test_the_spelling_it_offers_is_the_one_this_project_declares(tmp_path):
    # L6: where `[ids] suffix` is declared the step keeps the number and takes a letter,
    # which is the one id a caller may choose — so the refusal spells it rather than
    # describing it, and on a project without the declaration it never mentions it.
    config = project(tmp_path, extra_config="[ids]\nsuffix = true\n")
    ship(config, "RK1", part="local half", why="Because of a reason.").save()
    with pytest.raises(SecondPartial) as raised:
        ship(Config.discover(tmp_path), "RK1", part="the other half", why="Half of it.")
    assert f"{invocation()} add --id RK1b" in str(raised.value)


def test_an_id_the_ledger_closed_still_gets_the_message_written_for_it(tmp_path):
    # The other half of the split, on the one state that reaches it with the line still
    # open: the interrupted transaction RK62 is about — ledger written, roadmap not. A
    # recorded entry carrying no qualifier is work that already left whole, and there
    # naming the entry in the way *is* the answer.
    config = project(
        tmp_path,
        changelog=LEDGER.replace(
            "## Block B",
            "- ✅ **RK1** **A first symptom** — Because it landed.\n\n## Block B",
        ),
    )
    with pytest.raises(AlreadyShipped, match="already recorded"):
        ship(config, "RK1", part="a half", why="Half of it.")


def test_a_partial_of_a_task_that_is_not_open_is_refused(tmp_path):
    config = project(tmp_path)
    with pytest.raises(NotOpen):
        ship(config, "RK9", part="a half", why="Because of a reason.")


def test_a_partial_and_its_completion_both_lint_clean(tmp_path):
    config = project(tmp_path)
    ship(config, "RK1", part="local half", why="Because of a reason.").save()
    # Both halves of the name are the assertion: open plus recorded is exactly what a
    # partial *is*, so the gate that once called it `id.two-files` now says nothing (RK122).
    assert lint(Config.discover(tmp_path)).clean
    ship(Config.discover(tmp_path), "RK1", why="Because of a reason.").save()
    assert lint(Config.discover(tmp_path)).clean


def test_a_dependent_of_a_partial_is_annotated_by_the_line_and_not_by_the_ledger(tmp_path):
    # Measured in Turing (RK396): T927 shipped `--part` and stayed ⏳, and T933 was written
    # `(deps: T927 ✅)` — the annotation read ledger membership, which `--part` grants while
    # the work is unfinished. A reader picking work is then blocked by what the roadmap said
    # was done, which is the one failure a dep annotation exists to prevent.
    config = project(tmp_path)
    ship(config, "RK1", part="local half", why="Because of a reason.").save()
    roadmap = read(Config.discover(tmp_path), ROADMAP)
    assert "(deps: RK1 ⏳)" in roadmap
    assert "RK1 ✅" not in roadmap


def test_the_completion_is_what_turns_that_annotation_into_the_shipped_one(tmp_path):
    # The other end of the same fact: ✅ is a claim about the *line*, so it arrives exactly
    # when the line does not, and not when half of it was recorded.
    config = project(tmp_path)
    ship(config, "RK1", part="local half", why="Because of a reason.").save()
    ship(Config.discover(tmp_path), "RK1", why="Because it all landed.").save()
    assert "(deps: RK1 ✅)" in read(Config.discover(tmp_path), ROADMAP)


def test_the_partial_a_dep_resolves_against_names_which_half_landed(tmp_path):
    # The marker says open and the detail says what already exists, so the reader deciding
    # whether to start does not have to open the ledger to find out which half is left.
    config = project(tmp_path)
    ship(config, "RK1", part="local half", why="Because of a reason.").save()
    found = Backlog.load(Config.discover(tmp_path)).resolve_dep(Dep("RK1"))
    assert found.status is DepStatus.OPEN
    assert "local half" in found.detail and "changelog" in found.detail


def test_the_cli_reports_the_qualifier_and_how_to_finish(tmp_path, capsys):
    project(tmp_path)
    argv = ["-C", str(tmp_path), "ship", "RK1", "--why", "Because of a reason.", "--part", "local half"]
    assert main(argv) == EXIT_OK
    out = capsys.readouterr().out
    assert "RK1 (local half)" in out
    assert f"{invocation()} ship RK1" in out


def test_the_cli_json_says_the_line_is_still_open(tmp_path, capsys):
    project(tmp_path)
    argv = ["-C", str(tmp_path), "ship", "RK1", "--why", "Because of a reason.", "--part", "local half", "--json"]
    assert main(argv) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["part"] == "local half"
    assert payload["roadmap"]["open"] is True
    assert payload["roadmap"]["status"] == "⏳"


# -- which prose file the drop is made against (RK196) ------------------------

STRATEGY = "docs/STRATEGY.md"

#: An outline project whose rationale lives in the strategy file — the shape RK172 taught
#: the gate and RK186 taught the reader, arriving at the third reader, the one that writes.
OUTLINED = """# Roadmap

## Block A — The model

- 📋 **RK1** (deps: —) **A first symptom** — Because of a reason. → §X.1
- 📋 **RK2** (deps: —) **A second symptom** — Because of another. → §X.2
"""

PLAN = """# Strategy

## Block A — The model

### §X.1 The first design (RK1)

Prose that belongs to RK1 and to nothing else.

### §X.2 The second design (RK2)

Prose that belongs to RK2.
"""


def outlined(tmp_path: Path, *, improvements: str | None = None, strategy: str | None = PLAN) -> Config:
    """A project declaring `strategy`, and `improvements` only when a test wants both."""
    lines = ['prefix = "RK"', 'ref_scheme = "outline"', "[files]"]
    written = {ROADMAP: OUTLINED, CHANGELOG: LEDGER}
    lines += [f'roadmap = "{ROADMAP}"', f'changelog = "{CHANGELOG}"']
    if improvements is not None:
        lines.append(f'improvements = "{IMPROVEMENTS}"')
        written[IMPROVEMENTS] = improvements
    if strategy is not None:
        lines.append(f'strategy = "{STRATEGY}"')
        written[STRATEGY] = strategy
    (tmp_path / "roadkeep.toml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    for path, body in written.items():
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8", newline="") as handle:
            handle.write(body)
    return Config.discover(tmp_path)


def test_shipping_drops_the_section_from_the_role_that_declares_it(tmp_path):
    # The defect: `_drop_section` opened the improvements file alone, so a project declaring
    # only a strategy file was told it declared no prose file at all — and the section the
    # departing line pointed at stayed, which is the prose file becoming a second changelog.
    config = outlined(tmp_path)
    shipment = ship(config, "RK1", why="It works now.")
    assert shipment.dropped is not None and shipment.dropped.anchor == "X.1"
    assert shipment.kept is None
    shipment.save()

    plan = read(config, STRATEGY)
    assert "§X.1" not in plan and "belongs to RK1" not in plan
    # The neighbour's design is untouched: a drop is one subtree, not the rest of the file.
    assert "### §X.2 The second design (RK2)" in plan
    assert lint(Config.discover(tmp_path)).clean


def test_the_report_names_the_file_it_actually_wrote(tmp_path, capsys):
    # The silent half: a command that dropped from STRATEGY.md and printed IMPROVEMENTS.md
    # sends the next reader to the wrong file, which is the defect one level up.
    outlined(tmp_path)
    argv = ["-C", str(tmp_path), "ship", "RK1", "--why", "It works now."]
    assert main(argv) == EXIT_OK
    out = capsys.readouterr().out
    assert "dropped  §X.1" in out and STRATEGY in out
    assert IMPROVEMENTS not in out


def test_the_json_carries_the_file_the_drop_was_made_against(tmp_path, capsys):
    outlined(tmp_path)
    argv = ["-C", str(tmp_path), "ship", "RK1", "--why", "It works now.", "--json"]
    assert main(argv) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["improvements"]["file"] == STRATEGY
    assert payload["improvements"]["dropped"]["anchor"] == "X.1"


def test_a_project_declaring_both_still_drops_from_the_one_that_has_it(tmp_path):
    # Declaring an improvements file must not shadow the strategy file: the anchor decides.
    empty = "# Improvements\n\n## Block A — The model\n"
    config = outlined(tmp_path, improvements=empty)
    shipment = ship(config, "RK1", why="It works now.")
    shipment.save()
    assert "§X.1" not in read(config, STRATEGY)
    assert read(config, IMPROVEMENTS) == empty  # untouched, and not reported as the source


def test_an_anchor_two_prose_files_declare_is_kept_and_named(tmp_path):
    # Which of the two the line meant is what `ref.ambiguous` asks the author, and a ship
    # that deleted one of them would be answering it by picking. So the ship is right, the
    # section stays, and the reason says both files.
    doubled = "# Improvements\n\n## Block A — The model\n\n### §X.1 Also here (RK1)\n\nA second copy.\n"
    config = outlined(tmp_path, improvements=doubled)
    shipment = ship(config, "RK1", why="It works now.")
    assert shipment.dropped is None
    assert shipment.kept is not None
    assert STRATEGY in shipment.kept and IMPROVEMENTS in shipment.kept
    shipment.save()
    # Neither file lost a section, and the line still left the roadmap.
    assert "§X.1" in read(config, STRATEGY) and "§X.1" in read(config, IMPROVEMENTS)
    assert "RK1" not in read(config, ROADMAP)


def test_an_anchor_no_prose_file_declares_names_every_file_it_looked_in(tmp_path):
    config = outlined(tmp_path, strategy="# Strategy\n\n## Block A — The model\n")
    shipment = ship(config, "RK1", why="It works now.")
    assert shipment.dropped is None
    assert shipment.kept == f"no §X.1 section in {STRATEGY}"


# -- a departure deletes the section it owns (RK236) ---------------------------

#: The shape this was filed from: a standing memo whose subsections are addresses in a file
#: the project already keeps, and whose headings name no task. Turing's Block O lines pointed
#: at two of these; the siblings survived only because no line happened to name them.
MEMO = """# Strategy

## Block A — The model

### §X.1 The thesis

Positioning nobody filed as work.

### §X.3 The content calendar

Prose that belongs to no task, and that a retirement took.
"""

STANDING = """# Roadmap

## Block A — The model

- 📋 **RK1** (deps: —) **A first symptom** — Because of a reason. → §X.3
- 📋 **RK2** (deps: —) **A second symptom** — Because of another. → §X.1
"""


def test_a_section_naming_no_task_is_kept_and_the_reason_says_why(tmp_path):
    # RK64 asks whether another *open line* points at the anchor — false at the last of them.
    # RK196 asks whether *two roles* declare it. Neither reaches a memo subsection one line
    # happens to name, so a departure deleted prose that was never anybody's design.
    config = outlined(tmp_path, strategy=MEMO)
    with (tmp_path / ROADMAP).open("w", encoding="utf-8", newline="") as handle:
        handle.write(STANDING)
    config = Config.discover(tmp_path)

    shipment = ship(config, "RK1", why="It works now.")
    assert shipment.dropped is None
    assert shipment.kept == (
        "§X.3 names no task in its heading, so it is prose belonging to none — the "
        "reading `lint` makes when it declines to report it orphaned"
    )
    shipment.save()
    assert read(config, STRATEGY) == MEMO  # every line of it, siblings included
    assert "RK1" not in read(config, ROADMAP)  # the ship is still right


def test_a_retirement_leaves_the_memo_it_pointed_at(tmp_path):
    # The verb it actually happened through: `retire` shares the drop, so it shares the rule.
    config = outlined(tmp_path, strategy=MEMO)
    with (tmp_path / ROADMAP).open("w", encoding="utf-8", newline="") as handle:
        handle.write(STANDING)
    config = Config.discover(tmp_path)

    departure = retire(config, "RK1", reason="Nobody will do it.")
    assert departure.dropped is None and departure.kept is not None
    departure.save()
    assert read(config, STRATEGY) == MEMO


def test_a_section_another_task_owns_is_kept_and_names_that_task(tmp_path):
    # The same rule where the heading does name somebody, and the case RK64 cannot see: the
    # owner holds no pointer at all — retired, or never filed — so nothing else points here
    # and the old reading called the section this line's to delete.
    owned = MEMO.replace("### §X.3 The content calendar", "### §X.3 Somebody else's (RK9)")
    config = outlined(tmp_path, strategy=owned)
    with (tmp_path / ROADMAP).open("w", encoding="utf-8", newline="") as handle:
        handle.write(STANDING)
    config = Config.discover(tmp_path)

    shipment = ship(config, "RK1", why="It works now.")
    assert shipment.dropped is None
    assert shipment.kept == "§X.3 belongs to RK9, so it is not this line's to delete"
    shipment.save()
    assert "### §X.3 Somebody else's (RK9)" in read(config, STRATEGY)


def test_a_line_still_takes_its_own_design_under_the_id_scheme(tmp_path):
    # The half that must not change: ownership is `lint`'s reading, and under the id scheme
    # the anchor *is* the id — so a line's own section is owned, and owned sections go.
    config = project(tmp_path)
    shipment = ship(config, "RK1", why="It works now.")
    assert shipment.dropped is not None and shipment.kept is None
    shipment.save()
    assert "§RK1" not in read(config, IMPROVEMENTS)


def test_a_line_still_takes_a_design_an_outline_heading_names_it_in(tmp_path):
    # And under an outline, where the heading is what says so — which is the fixture every
    # other test here uses, asserted once as the claim rather than assumed by all of them.
    config = outlined(tmp_path)
    shipment = ship(config, "RK1", why="It works now.")
    assert shipment.dropped is not None and shipment.kept is None


# -- the half RK179 did not reach (RK193) -------------------------------------

#: The shape adoption produces and RK179 measured: a hand-written partial whose sentence
#: runs past the line the parse holds — 10 of Shio's 12 partial entries do. `RK9` beneath
#: it is the neighbour a span that overran would take, and it deliberately does not wrap.
WRAPPED_PARTIAL = """# Shipped

## Block A — The model

- ✅ **RK1 (local half)** **A first symptom** — Because the local half landed,
  and the rest is still being written
  against the other end.
- ✅ **RK9** **A ninth symptom** — Because of another.

## Block B — Authoring
"""

#: The line that partial left open, which is what makes the next `ship` a completion.
PARTLY = BACKLOG.replace("- 📋 **RK1**", "- ⏳ **RK1**")


def test_completing_a_wrapped_partial_is_refused_until_the_count_is_given(tmp_path):
    # The defect: `replace_task` reproduces the first line and nothing below it, so the
    # entry stated the whole delivery followed by the tail of the half's old sentence —
    # and the command reported a completion.
    config = project(tmp_path, roadmap=PARTLY, changelog=WRAPPED_PARTIAL)
    with pytest.raises(Wrapped) as raised:
        ship(config, "RK1", why="All of it landed.")
    message = str(raised.value)
    assert "CHANGELOG.md:5" in message and "lines 5-7" in message
    # The verb is the caller's own, because a completion is not a correction (RK193).
    assert "completing it replaces all 3" in message and "--lines 3" in message
    # The count's other permission, on the file that has it (RK1057).
    assert "writes them back instead of collapsing them" in message
    assert files(config)[1] == WRAPPED_PARTIAL


def test_the_count_replaces_the_span_and_stops_at_the_next_entry(tmp_path):
    config = project(tmp_path, roadmap=PARTLY, changelog=WRAPPED_PARTIAL)
    ship(config, "RK1", why="All of it landed.", lines=3).save()

    roadmap, ledger, improvements = files(config)
    assert "- ✅ **RK1** **A first symptom** — All of it landed." in ledger
    # The qualifier goes *and* so does the tail it was written with, which is the pair the
    # first line alone could never move together.
    assert "local half" not in ledger
    assert "still being written" not in ledger and "the other end" not in ledger
    # The neighbour is untouched: a span that overran by one would have taken it.
    assert "- ✅ **RK9** **A ninth symptom** — Because of another." in ledger
    assert "⏳ **RK1**" not in roadmap  # the line finally leaves
    assert "§RK1 A first design" not in improvements
    assert lint(Config.discover(tmp_path)).clean


def test_the_completion_can_write_the_span_back_instead_of_collapsing_it(tmp_path):
    # RK1053: the count says the caller read the span, so `--why` may carry it. Without
    # this, finishing the majority-shape partial deleted the paragraphs under the bullet —
    # the RK1049 defect at the door that says the work is done.
    config = project(tmp_path, roadmap=PARTLY, changelog=WRAPPED_PARTIAL)
    ship(
        config,
        "RK1",
        why="All of it landed.\n  The remote end took a second protocol,\n  which is what the note below records.",
        lines=3,
    ).save()

    ledger = files(config)[1].splitlines()
    assert ledger[4] == "- ✅ **RK1** **A first symptom** — All of it landed."
    assert ledger[5] == "  The remote end took a second protocol,"
    assert ledger[6] == "  which is what the note below records."
    # The neighbour is still one line past the span, and the qualifier is still gone.
    assert ledger[7] == "- ✅ **RK9** **A ninth symptom** — Because of another."
    assert "local half" not in files(config)[1]
    assert lint(Config.discover(tmp_path)).clean


def test_a_completion_with_no_count_still_refuses_a_newline(tmp_path):
    # The door is the count, here as at `record amend`: on a governed ledger a newline in
    # the outcome is a shell that expanded something, and the refusal names it.
    config = project(tmp_path)
    ship(config, "RK1", part="local half", why="Because of a reason.").save()
    with pytest.raises(SchemaError) as caught:
        ship(Config.discover(tmp_path), "RK1", why="It landed.\nAnd this was never typed.")
    assert any(v.code == "why.newline" for v in caught.value.violations)


def test_a_count_that_is_not_the_span_is_refused_rather_than_trusted(tmp_path):
    # An off-by-one here is the neighbour's entry, so the number is checked and not taken.
    config = project(tmp_path, roadmap=PARTLY, changelog=WRAPPED_PARTIAL)
    with pytest.raises(Wrapped) as raised:
        ship(config, "RK1", why="All of it landed.", lines=2)
    assert "--lines 2 is not that count" in str(raised.value)
    assert files(config)[1] == WRAPPED_PARTIAL


def test_a_partial_this_tool_wrote_needs_no_count(tmp_path):
    # The count is the door out of a refusal and not a new field on every completion: a
    # governed ledger has no wrapped entry at all, so nothing changes for one.
    config = project(tmp_path)
    ship(config, "RK1", part="local half", why="Because of a reason.").save()
    ship(Config.discover(tmp_path), "RK1", why="All of it landed.").save()
    assert "- ✅ **RK1** **A first symptom** — All of it landed." in read(config, CHANGELOG)


def test_the_count_is_refused_where_the_ship_replaces_no_entry(tmp_path):
    # A flag silently dropped is a flag the caller believes took effect, and on all three
    # of these paths `ship` places a new entry rather than rewriting one.
    config = project(tmp_path)
    with pytest.raises(NoCompletion, match="records no partial for RK1"):
        ship(config, "RK1", why="Because of a reason.", lines=3)
    with pytest.raises(NoCompletion):
        ship(config, "RK1", why="Because of a reason.", part="local half", lines=3)
    assert files(config) == (BACKLOG, LEDGER, RATIONALE)


def test_the_count_beside_a_part_is_refused_for_the_rule_and_not_for_the_ledger(tmp_path):
    """RK1128, measured in Turing: `ship T898 --part … --lines 1` answered "records no partial
    for T898" over a `**T898 (the lint half)**` on line 693, sending the caller to look for an
    entry that was there. A call passing `--part` is not a completion whatever the ledger holds."""
    config = project(tmp_path, roadmap=PARTLY, changelog=WRAPPED_PARTIAL)
    with pytest.raises(NoCompletion) as raised:
        ship(config, "RK1", part="another half", lines=1)
    said = str(raised.value)
    assert "passes --part, so it is not one" in said
    assert "records no partial" not in said  # the sentence that was false here
    # And it names the call that does take a count, which is the advice the second refusal gave.
    assert "`ship RK1` with no --part" in said


def test_the_other_sentence_still_says_what_the_ledger_holds(tmp_path):
    # Held so the split is two states and not a rewrite: with no `--part`, an empty ledger is
    # exactly why nothing is replaced, and naming that is the answer.
    config = project(tmp_path)
    with pytest.raises(NoCompletion) as raised:
        ship(config, "RK1", why="Because of a reason.", lines=3)
    assert "records no partial for RK1" in str(raised.value)


def test_the_count_is_refused_on_the_line_a_crash_left_behind(tmp_path):
    # The closure path writes no entry at all (RK62) — it removes the line the ledger was
    # already written from — so there is nothing for a span count to be about.
    config = project(tmp_path)
    ship(config, "RK1", why="Because of a reason.").save()
    config = project(tmp_path, roadmap=BACKLOG, changelog=read(config, CHANGELOG))
    with pytest.raises(NoCompletion):
        ship(config, "RK1", lines=1)


def test_the_flag_reaches_the_command_line(tmp_path, capsys):
    project(tmp_path, roadmap=PARTLY, changelog=WRAPPED_PARTIAL)
    argv = ["-C", str(tmp_path), "ship", "RK1", "--why", "All of it landed.", "--lines", "3"]
    assert main(argv) == EXIT_OK
    assert "RK1" in capsys.readouterr().out
    assert "still being written" not in read(Config.discover(tmp_path), CHANGELOG)


def test_the_refusal_names_the_count_rather_than_writing_half_of_it(tmp_path, capsys):
    project(tmp_path, roadmap=PARTLY, changelog=WRAPPED_PARTIAL)
    argv = ["-C", str(tmp_path), "ship", "RK1", "--why", "All of it landed."]
    assert main(argv) == EXIT_USAGE
    assert "--lines 3" in capsys.readouterr().err


# -- retiring the rest is not a verdict on the half (RK129) -------------------


def test_retiring_a_task_whose_half_shipped_is_refused(tmp_path):
    # The completion path replaces the partial entry, and `retire` reached it with a
    # different marker: the ✅ naming what landed became a 🗑, and the sentence about the
    # shipped half left the only file whose job is to answer what happened to this.
    config = project(tmp_path)
    ship(config, "RK1", part="local half", why="Because of a reason.").save()

    with pytest.raises(PartRecorded) as caught:
        retire(Config.discover(tmp_path), "RK1", reason="The rest is not coming.")

    message = str(caught.value)
    assert "(local half)" in message and "ship RK1" in message
    ledger = read(config, CHANGELOG)
    assert "- ✅ **RK1 (local half)** **A first symptom** — Because of a reason." in ledger
    assert "🗑" not in ledger


def test_the_refusal_leaves_all_three_files_exactly_as_they_were(tmp_path):
    # All-or-nothing at the one door that could half-write it: the roadmap line stays open
    # and the design stays where it is, so the author still has every option.
    config = project(tmp_path)
    ship(config, "RK1", part="local half", why="Because of a reason.").save()
    before = files(Config.discover(tmp_path))

    with pytest.raises(PartRecorded):
        retire(Config.discover(tmp_path), "RK1", reason="The rest is not coming.")

    assert files(Config.discover(tmp_path)) == before


def test_a_supersession_is_refused_by_the_same_rule(tmp_path):
    # Superseded and abandoned are one transaction with two prefixes (RK32), so a half
    # already recorded stops both — the deletion is the same deletion.
    config = project(tmp_path)
    ship(config, "RK1", part="local half", why="Because of a reason.").save()
    with pytest.raises(PartRecorded):
        retire(
            Config.discover(tmp_path),
            "RK1",
            reason="RK2 does it instead.",
            superseded_by="RK2",
        )


def test_a_retirement_with_no_recorded_half_is_untouched(tmp_path):
    # The refusal is about the qualifier and nothing else: an ordinary retirement is the
    # same transaction it always was.
    config = project(tmp_path)
    retire(config, "RK1", reason="Nobody will do it.").save()
    assert "- 🗑 **RK1** **A first symptom** — abandoned: Nobody will do it." in read(
        config, CHANGELOG
    )


def test_the_command_refuses_with_two_and_writes_nothing(tmp_path, capsys):
    config = project(tmp_path)
    ship(config, "RK1", part="local half", why="Because of a reason.").save()
    before = files(Config.discover(tmp_path))
    code = main(["-C", str(tmp_path), "retire", "RK1", "--reason", "Not coming."])
    assert code == EXIT_USAGE
    assert "already records" in capsys.readouterr().err
    assert files(Config.discover(tmp_path)) == before


# -- the middle of a transaction has a door (RK130) ---------------------------

#: What a crash between the ledger write and the roadmap write leaves: the entry the
#: departure wrote, and the line it wrote it from, still open and still 📋.
INTERRUPTED = f"""# Shipped

## Block A — The model

{SHIPPED_RK1}

## Block B — Authoring
"""


def test_a_stopped_transaction_is_finished_by_the_command_that_started_it(tmp_path):
    # RK118 made the middle state loud and lossless and left no way out: `ship` refused the
    # id, `Closure` wanted a marker the line does not carry, `record drop` wants a second
    # entry — so the only exit was the edit the hook denies.
    config = project(tmp_path, changelog=INTERRUPTED)
    # `deps.stale` rides along: RK2 and RK3 name RK1, whose annotation the write that never
    # happened would have derived. Both are what the middle state is meant to look like.
    assert {f.code for f in lint(config).findings} == {"id.two-files", "deps.stale"}

    closed = ship(config, "RK1")
    closed.save()

    assert isinstance(closed, Closure)
    assert closed.marker == "✅" and closed.recorded.lineno == 5
    roadmap, ledger, improvements = files(Config.discover(tmp_path))
    assert RK1 not in roadmap  # the write that never happened
    assert ledger == INTERRUPTED  # and the one that did is not repeated
    assert "§RK1 A first design" not in improvements
    assert lint(Config.discover(tmp_path)).clean


def test_a_retirement_that_stopped_is_finished_the_same_way(tmp_path):
    # Which door the ledger recorded is the entry's to say, and `ship` is the verb for
    # "finish this": a 🗑 leftover closes to a 🗑, not to a second claim.
    retired = INTERRUPTED.replace(
        SHIPPED_RK1, "- 🗑 **RK1** **A first symptom** — abandoned: Nobody will do it."
    )
    config = project(tmp_path, changelog=retired)
    closed = ship(config, "RK1")
    closed.save()

    assert closed.marker == "🗑"
    assert read(config, CHANGELOG) == retired
    assert RK1 not in read(config, ROADMAP)


def test_an_entry_naming_a_half_is_completed_rather_than_closed(tmp_path):
    # The case that cost a real task and a 224-word section, narrowed to what actually says
    # it (RK1075): the **entry's** qualifier. A half is recorded and a half is not, so
    # closing the line would drop the one that never landed — and that is true whatever
    # marker the roadmap happens to carry, which is why the marker stopped deciding it.
    config = project(
        tmp_path,
        roadmap=BACKLOG.replace("- 📋 **RK1**", "- ⏳ **RK1**"),
        changelog=INTERRUPTED.replace("**RK1**", "**RK1 (local half)**"),
    )
    # And what it is instead of a closure is a **completion**: the entry is rewritten in
    # place and loses its qualifier, where a closure removes the line and writes nothing.
    # Two exits for two states, which is what the marker could not tell apart.
    ship(config, "RK1", why="All of it landed.").save()
    ledger = read(config, CHANGELOG)
    assert "(local half)" not in ledger and "All of it landed." in ledger
    assert "**RK1**" not in read(config, ROADMAP)
    assert "§RK1 A first design" not in read(config, IMPROVEMENTS)


def test_an_entry_naming_a_half_is_completed_and_never_closed(tmp_path):
    # The other half of the same distinction, read off the ledger: a project that declares
    # no ⏳ leaves the line's own marker, so the qualifier is what says it is a partial.
    config = project(
        tmp_path,
        changelog=INTERRUPTED.replace(
            "**RK1**", "**RK1 (local half)**"
        ),
    )
    completed = ship(config, "RK1", why="All of it landed.")
    completed.save()

    ledger = read(config, CHANGELOG)
    assert ledger.count("**RK1") == 1 and "local half" not in ledger
    assert "All of it landed." in ledger


def test_two_tasks_sharing_an_id_are_refused_rather_than_closed(tmp_path):
    # What widening the condition opened: an interrupted transaction wrote its entry *from*
    # the line, so the symptoms match — two that do not are the merge RK97 is about, and
    # closing one would delete work no crash touched.
    config = project(
        tmp_path,
        changelog=INTERRUPTED.replace("A first symptom", "What the other branch shipped"),
    )
    before = files(config)
    with pytest.raises(Divergent) as caught:
        ship(config, "RK1", why="Because of a reason.")
    assert "renumber RK1" in str(caught.value)
    assert files(Config.discover(tmp_path)) == before


def test_a_restatement_is_refused_on_the_path_that_writes_no_entry(tmp_path):
    config = project(tmp_path, changelog=INTERRUPTED)
    with pytest.raises(NoRestatement):
        ship(config, "RK1", why="A sentence with nowhere to go.")


def test_the_command_says_the_ledger_already_held_it(tmp_path, capsys):
    project(tmp_path, changelog=INTERRUPTED)
    assert main(["-C", str(tmp_path), "ship", "RK1"]) == EXIT_OK
    printed = capsys.readouterr().out
    assert "RK1" in printed and "✅" in printed


# -- the sentence written by omission (RK142) ---------------------------------


def test_the_ledger_never_inherits_the_roadmaps_problem_statement(tmp_path):
    # A roadmap line states a problem; a ledger entry states an outcome. Copying the first
    # into the second wrote the entry by omission — a defect report under a heading that
    # means "done" — and the default is what an author who does not know the flag gets.
    config = project(tmp_path)
    with pytest.raises(NoOutcome) as caught:
        ship(config, "RK1")

    assert "Because of a reason." in str(caught.value)
    assert "--why" in str(caught.value)
    assert files(Config.discover(tmp_path)) == files(config)


def test_the_half_that_landed_is_held_to_the_same_rule(tmp_path):
    # A partial states an outcome too — this much of it works — so it is no more entitled
    # to the problem statement than the whole.
    config = project(tmp_path)
    with pytest.raises(NoOutcome):
        ship(config, "RK1", part="local half")
    assert read(config, CHANGELOG) == LEDGER


def test_a_retirement_still_derives_its_own_sentence(tmp_path):
    # `retire` arrives with a sentence this module composed from `--reason`, so the rule
    # above is the ship path alone: the required argument is already required there.
    config = project(tmp_path)
    retire(config, "RK1", reason="Nobody will do it.").save()
    assert "abandoned: Nobody will do it." in read(config, CHANGELOG)


def test_closing_a_line_the_ledger_already_holds_needs_no_outcome(tmp_path):
    # The other path that writes no entry (RK62, RK130): there is no sentence to state,
    # which is why `--why` is refused there rather than required.
    config = project(tmp_path, changelog=INTERRUPTED)
    ship(config, "RK1").save()
    assert read(config, CHANGELOG) == INTERRUPTED


def test_the_command_refuses_at_input_and_writes_nothing(tmp_path, capsys):
    config = project(tmp_path)
    before = files(config)
    assert main(["-C", str(tmp_path), "ship", "RK1"]) == EXIT_USAGE
    assert "needs the outcome it shipped" in capsys.readouterr().err
    assert files(Config.discover(tmp_path)) == before


def test_an_entry_already_written_wrong_is_corrected_where_it_stands(tmp_path):
    # The other half of RK142, which RK124 closed one task earlier: an entry that inherited
    # the problem statement before this rule existed is reachable by `record amend`.
    config = project(tmp_path, changelog=INTERRUPTED)
    corrected = amend_record(config, "RK1", why="The first symptom no longer happens.")
    corrected.save()

    assert corrected.changed == ("why",) and corrected.lineno == 5
    assert "The first symptom no longer happens." in read(config, CHANGELOG)


# -- the design the deletion overtook (RK310) ---------------------------------


def test_the_ledger_records_which_design_this_shipment_overtook(tmp_path):
    # A section is written when a task is filed and read when somebody claims it, and in
    # between the codebase moves. `ship` deleted the reasoning either way, so the one reader
    # who could ever know it had been wrong was the one who had already done the work.
    config = project(tmp_path)
    shipment = ship(
        config,
        "RK1",
        why="The first symptom no longer happens.",
        superseded="the lookup it proposed already existed",
    )
    shipment.save()

    assert shipment.superseded == "the lookup it proposed already existed"
    # One sentence, and the author's own terminator closes it: a clause bolted on behind the
    # full stop is two, which `why.sentences` refuses at the door.
    assert (
        "- ✅ **RK1** **A first symptom** — The first symptom no longer happens "
        "(design §RK1 superseded: the lookup it proposed already existed)."
    ) in read(config, CHANGELOG)
    # The clause is the *only* trace: the three edits are the three edits, and the section
    # the entry now names is gone from the file exactly as it would otherwise be.
    assert "§RK1 A first design" not in read(config, IMPROVEMENTS)
    # And the `§RK1` the sentence now names is prose, not a pointer: the gate reads the
    # parsed `ref` field and the ledger's schema carries none, so the trace is not an
    # orphan the backstop then reports against a section this same call deleted.
    assert lint(config).findings == ()


def test_the_clause_names_the_anchor_and_never_the_id(tmp_path):
    # Under an outline the pointer is an address the caller chose, so the address is read off
    # the line that is leaving — the one fact about the deleted design that survives nowhere
    # else, and the one a caller restating it from the id would get wrong.
    outlined = BACKLOG
    rationale = RATIONALE
    for task_id, anchor in (("RK1", "I.2"), ("RK2", "I.3"), ("RK3", "II.1")):
        outlined = outlined.replace(f"→ §{task_id}", f"→ §{anchor}")
        rationale = rationale.replace(f"§{task_id} A", f"§{anchor} {task_id} A")
    rationale = rationale.replace("§RK1.1 A subsection", "§I.2.1 A subsection")
    project(tmp_path, roadmap=outlined, improvements=rationale)
    # `ref_scheme` is a top-level key, so it goes before the `[files]` table rather than
    # through `extra_config`, which appends after it.
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\nref_scheme = "outline"\n[files]\n'
        f'roadmap = "{ROADMAP}"\nchangelog = "{CHANGELOG}"\n'
        f'improvements = "{IMPROVEMENTS}"\n',
        encoding="utf-8",
    )
    config = Config.discover(tmp_path)
    ship(
        config,
        "RK1",
        why="The first symptom no longer happens.",
        superseded="the subsystem it called new had shipped",
    ).save()

    assert "(design §I.2 superseded: the subsystem it called new had shipped)" in read(
        config, CHANGELOG
    )


def test_a_line_that_pointed_at_no_design_has_none_to_supersede(tmp_path):
    # An entry saying a design was superseded, on a line that never had one, sends the next
    # reader of the ledger through git looking for prose nobody ever wrote.
    config = project(
        tmp_path,
        roadmap=BACKLOG.replace(" → §RK1", ""),
        extra_config="\n[rules.roadmap]\nref = false\n",
    )
    before = files(config)
    with pytest.raises(NoDesign) as caught:
        ship(config, "RK1", why="It works now.", superseded="nothing, there was none")

    assert "carries no pointer" in str(caught.value)
    assert files(Config.discover(tmp_path)) == before


def test_a_partial_keeps_its_design_so_it_has_not_been_overtaken_yet(tmp_path):
    # The section stays on a partial because the rest of the work still reads it (RK121), so
    # whether the premise held is not yet decided — and there is no second entry the clause
    # could be corrected onto. The refusal names the call that does delete the section.
    config = project(tmp_path)
    before = files(config)
    with pytest.raises(NoSupersession) as caught:
        ship(
            config,
            "RK1",
            why="Half of it works.",
            part="local half",
            superseded="too early to say",
        )

    assert "ship RK1" in str(caught.value) and "local half" in str(caught.value)
    assert files(Config.discover(tmp_path)) == before


def test_the_completion_is_where_the_partials_design_is_judged(tmp_path):
    # The other half of that refusal: the call the message names accepts the clause, because
    # it is the one that deletes the section.
    config = project(tmp_path)
    ship(config, "RK1", why="Half of it works.", part="local half").save()
    ship(
        config,
        "RK1",
        why="The first symptom no longer happens.",
        superseded="the second half needed none of it",
    ).save()

    ledger = read(config, CHANGELOG)
    assert "(local half)" not in ledger
    assert "(design §RK1 superseded: the second half needed none of it)" in ledger


def test_a_closure_writes_no_sentence_for_the_clause_to_join(tmp_path):
    # The ledger already holds the entry, so this call only closes the line (RK62) — and a
    # flag silently dropped is a flag the caller believes took effect.
    config = project(tmp_path, changelog=INTERRUPTED)
    before = files(config)
    with pytest.raises(NoRestatement) as caught:
        ship(config, "RK1", superseded="the design was overtaken")

    assert "--superseded-design" in str(caught.value)
    assert files(Config.discover(tmp_path)) == before


def test_the_clause_is_held_to_the_sentences_own_limit(tmp_path):
    # No second limit and no second field: the clause lands in the `why`, so the ledger's own
    # `why` limit is what refuses it — with the number, as every other over-length write is.
    # **And with the parts** (RK1261): the total is neither argument's, so a refusal naming only
    # `why` asked for an outcome shorter than any of it and pointed at the half that survives.
    config = project(tmp_path, extra_config="\n[limits]\nwhy = 80\n")
    before = files(config)
    with pytest.raises(SupersessionCrowded) as caught:
        ship(
            config,
            "RK1",
            why="The first symptom no longer happens.",
            superseded="a clause long enough to push the whole sentence past the limit",
        )

    said = str(caught.value)
    assert "80" in said
    # Each argument's own cost, and the wrapper's, so the three add up to the total refused.
    assert "--why took 36" in said
    assert "--superseded-design took 62" in said
    assert f"added {supersession_cost('RK1')}" in said
    assert "125 characters" in said and 36 + 62 + supersession_cost("RK1") == 125
    # And the edit, which is the whole finding: the outcome is what the entry keeps once the
    # design is deleted, so the deletion comes out of the note.
    assert "it is the note that gives way" in said
    assert files(Config.discover(tmp_path)) == before


def test_an_outcome_over_the_limit_on_its_own_is_still_reported_as_the_field(tmp_path):
    """`why_budget`'s rule one file over: an overrun in one field is never charged to another.

    A `--why` that does not fit without the clause is `why.too-long` about `--why`, and naming
    the supersession there would send the author to cut the half that was not the problem —
    which is this task's own finding, pointed the other way."""
    config = project(tmp_path, extra_config="\n[limits]\nwhy = 40\n")
    with pytest.raises(SchemaError) as caught:
        ship(
            config,
            "RK1",
            why="The first symptom no longer happens, and neither does the second one.",
            superseded="the lookup it proposed already existed",
        )

    said = str(caught.value)
    assert "why" in said and "40" in said
    assert "--superseded-design took" not in said


def test_the_note_is_told_how_much_room_it_has_and_when_it_has_none(tmp_path):
    # The room is the limit less the outcome and the wrapper, so a caller reading it composes
    # the retry once. Where the outcome alone leaves nothing, that is said instead of a `0`.
    config = project(tmp_path, extra_config="\n[limits]\nwhy = 80\n")
    with pytest.raises(SupersessionCrowded) as caught:
        ship(
            config,
            "RK1",
            why="The first symptom no longer happens.",
            superseded="a clause long enough to push the whole sentence past the limit",
        )
    # 80 less the 36-character outcome and the wrapper the anchor makes.
    assert f"has {80 - 36 - supersession_cost('RK1')} characters beside this --why" in str(
        caught.value
    )

    with pytest.raises(SupersessionCrowded) as crowded:
        ship(
            config,
            "RK1",
            why="The first symptom no longer happens, and that is the whole outcome here.",
            superseded="a short clause",
        )
    said = str(crowded.value)
    assert "has none beside this --why" in said
    assert "the outcome is what has to be shorter first" in said


def test_the_shipping_allowance_names_what_a_supersession_will_take(tmp_path, capsys):
    """RK1261's other half. A task about to lose its design is exactly when this figure is
    read, and it was quoted without knowing a clause would be appended to the same sentence.

    Derived and not hedged, unlike the `--part` qualifier beside it: the anchor is the pointer
    the line already carries, so only the note's own length is the caller's."""
    project(tmp_path, extra_config="\n[limits.changelog]\nwhy = 150\n")
    assert main(["-C", str(tmp_path), "brief", "RK1"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "shipping why" in out
    # ` (design §RK1 superseded: )` — measured through the composer, so a reworded clause
    # moves this number rather than leaving it behind.
    # Both clauses since RK1275, on a row of their own: two flags land in that sentence, and
    # the wrapper of each is derivable from the anchor the line already carries.
    assert f"less {supersession_cost('RK1')} for a `--superseded-design` clause" in out
    assert f"and {recording_cost('RK1')} for a `--recorded-in` wrapper" in out


def test_the_flag_reaches_the_command_line_and_reports_what_it_wrote(tmp_path, capsys):
    config = project(tmp_path)
    assert (
        main(
            [
                "-C",
                str(tmp_path),
                "ship",
                "RK1",
                "--why",
                "The first symptom no longer happens.",
                "--superseded-design",
                "the lookup it proposed already existed",
            ]
        )
        == EXIT_OK
    )
    out = capsys.readouterr().out
    assert "overtook the design it read: the lookup it proposed already existed" in out
    assert "(design §RK1 superseded:" in read(config, CHANGELOG)


def test_the_json_answers_the_clause_as_a_field(tmp_path, capsys):
    # Read off the transaction rather than parsed back out of the rendered sentence, which
    # is the rule every other half of this report already keeps.
    project(tmp_path)
    main(
        [
            "-C",
            str(tmp_path),
            "ship",
            "RK1",
            "--why",
            "The first symptom no longer happens.",
            "--superseded-design",
            "the lookup it proposed already existed",
            "--json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["improvements"]["superseded"] == "the lookup it proposed already existed"


# -- where the durable half of the deleted design went (RK1267) ---------------


def _with_module(tmp_path: Path) -> Config:
    """The fixture plus the file a design's decision would be recorded in.

    `src/` and not a bare name for `_with_source`'s reason (RK55, RK217): a token whose
    directory the repository has never heard of is not read as a path at all, so a fixture
    without one would prove the refusal by accident rather than by the rule.
    """
    config = project(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "engine.py").write_text(
        '"""The decision, above the code."""\n', encoding="utf-8"
    )
    return config


def test_the_deleted_designs_durable_half_gets_an_address(tmp_path):
    """The defect. `--superseded-design` types the deletion as *stale* and nothing typed it
    as *moved*, so a definition of done written as a design is deleted correctly and survives
    in zero places — RK1265's measurement, after which its block was reopened six times."""
    config = _with_module(tmp_path)
    ship(
        config,
        "RK1",
        why="The first symptom no longer happens.",
        recorded_in="src/engine.py",
    ).save()

    ledger = read(config, CHANGELOG)
    assert "(design §RK1 recorded in `src/engine.py`)." in ledger
    # The sentence still ends like one: the clause is inside the terminator, which is what
    # keeps the composed `why` legal under the rules that refuse two of them.
    assert "happens (design §RK1 recorded in `src/engine.py`)." in ledger
    assert "§RK1" not in read(config, IMPROVEMENTS)


def test_both_clauses_land_in_one_sentence_in_the_order_the_pair_reads(tmp_path):
    # What was wrong, then where the part that was right went — decided by the composer and
    # never by which flag the caller typed first.
    config = _with_module(tmp_path)
    ship(
        config,
        "RK1",
        why="The first symptom no longer happens.",
        superseded="the lookup it proposed already existed",
        recorded_in="src/engine.py",
    ).save()

    assert (
        "(design §RK1 superseded: the lookup it proposed already existed) "
        "(design §RK1 recorded in `src/engine.py`)." in read(config, CHANGELOG)
    )


def test_a_destination_the_repository_lacks_is_refused_and_writes_nothing(tmp_path):
    # The gate's `path.missing` asked before the entry lands (RK497, L1): an address recorded
    # into the one file that says the work is done has to resolve, or the trace points nowhere
    # and the next reader searches git for a file nobody wrote.
    config = _with_module(tmp_path)
    before = files(config)
    with pytest.raises(NoSuchPath) as refused:
        ship(
            config,
            "RK1",
            why="The first symptom no longer happens.",
            recorded_in="src/gone.py",
        )

    assert refused.value.named == "--recorded-in"
    assert refused.value.missing == ("src/gone.py",)
    assert files(Config.discover(tmp_path)) == before


def test_a_line_with_no_pointer_has_no_design_for_the_half_to_have_left(tmp_path):
    # The same absence `--superseded-design` is refused over, said about this clause: a
    # refusal naming the other flag reads as a bug in the tool rather than as an answer.
    config = project(
        tmp_path,
        roadmap=BACKLOG.replace(" → §RK1", ""),
        extra_config="\n[rules.roadmap]\nref = false\n",
    )
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "engine.py").write_text("x = 1\n", encoding="utf-8")
    before = files(config)
    with pytest.raises(NoDesign) as caught:
        ship(config, "RK1", why="It works now.", recorded_in="src/engine.py")

    said = str(caught.value)
    assert "--recorded-in names" in said and "--superseded-design" not in said
    assert files(Config.discover(tmp_path)) == before


def test_a_partial_has_not_decided_where_anything_went_yet(tmp_path):
    # The section stays while the rest of the work still reads it (RK121), so nothing has been
    # deleted and there is no half to have moved. The refusal names the call that does delete.
    config = _with_module(tmp_path)
    before = files(config)
    with pytest.raises(NoSupersession) as caught:
        ship(
            config,
            "RK1",
            why="Half of it works.",
            part="local half",
            recorded_in="src/engine.py",
        )

    assert "--recorded-in" in str(caught.value) and "ship RK1" in str(caught.value)
    assert files(Config.discover(tmp_path)) == before


def test_a_closure_writes_no_sentence_for_the_destination_to_join(tmp_path):
    # The ledger already holds the entry and this call only closes the line (RK62). Refused
    # rather than dropped: a flag silently ignored is a flag the caller believes took effect.
    config = _with_module(tmp_path)
    (tmp_path / CHANGELOG).write_text(INTERRUPTED, encoding="utf-8", newline="")
    before = files(Config.discover(tmp_path))
    with pytest.raises(NoRestatement) as caught:
        ship(config, "RK1", recorded_in="src/engine.py")

    assert "--recorded-in" in str(caught.value)
    assert files(Config.discover(tmp_path)) == before


def test_the_clause_that_cannot_be_cut_asks_the_outcome_to_give_way(tmp_path):
    """RK1261's finding with the halves swapped. There the note is the author's and can be
    shortened; here the clause is an address and a path, derived whole, so a message pointing
    at it would ask for an edit no argument on the call can make."""
    config = project(tmp_path, extra_config="\n[limits]\nwhy = 80\n")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "engine.py").write_text("x = 1\n", encoding="utf-8")
    before = files(config)
    with pytest.raises(RecordingCrowded) as caught:
        ship(
            config,
            "RK1",
            why="The first symptom no longer happens, and the second one has stopped too.",
            recorded_in="src/engine.py",
        )

    said = str(caught.value)
    assert "80" in said and "none of that is prose to cut" in said
    assert "the outcome is what gives way" in said
    assert files(Config.discover(tmp_path)) == before


def test_the_flag_reaches_the_command_line_and_answers_as_a_field(tmp_path, capsys):
    config = _with_module(tmp_path)
    assert (
        main(
            [
                "-C",
                str(tmp_path),
                "ship",
                "RK1",
                "--why",
                "The first symptom no longer happens.",
                "--recorded-in",
                "src/engine.py",
                "--json",
            ]
        )
        == EXIT_OK
    )
    payload = json.loads(capsys.readouterr().out)
    # Read off the transaction, never parsed back out of the rendered sentence.
    assert payload["improvements"]["recorded_in"] == "src/engine.py"
    assert "recorded in `src/engine.py`" in read(config, CHANGELOG)


def test_the_report_states_the_destination_beside_the_drop(tmp_path, capsys):
    # Where the deletion is reported, because the deletion is what makes the address the only
    # surviving trace of the section.
    config = _with_module(tmp_path)
    assert (
        main(
            [
                "-C",
                str(tmp_path),
                "ship",
                "RK1",
                "--why",
                "The first symptom no longer happens.",
                "--recorded-in",
                "src/engine.py",
            ]
        )
        == EXIT_OK
    )
    assert "recorded the part that outlives it: src/engine.py" in capsys.readouterr().out


# -- the parent a ship just emptied (RK400) -----------------------------------


def _outlined(tmp_path, prose=None):
    """A project numbering its prose by outline, with one family and one child."""
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "DX"\nref_scheme = "outline"\n[files]\nroadmap = "ROADMAP.md"\n'
        'changelog = "CHANGELOG.md"\nimprovements = "IMPROVEMENTS.md"\n',
        encoding="utf-8",
    )
    files = {
        "ROADMAP.md": "# Roadmap\n\n## Block A — The model\n\n"
        "- 📋 **DX1** (deps: —) **A first symptom** — Because of a reason. → §I.1\n",
        "CHANGELOG.md": "# Shipped\n\n## Block A — The model\n",
        "IMPROVEMENTS.md": prose
        or "# Improvements\n\n## I A family of designs\n\n"
        "The problem this family solves, in the present tense.\n\n"
        "### §I.1 DX1 The first design\n\nThe reasoning.\n",
    }
    for name, body in files.items():
        with (tmp_path / name).open("w", encoding="utf-8", newline="") as handle:
            handle.write(body)
    return Config.discover(tmp_path)


def test_the_parent_left_with_no_children_is_named(tmp_path):
    """`ship` deletes the task's own section and names what cited it. Under an outline it
    leaves the **parent** standing — an introduction to children that have all shipped, in
    the present tense, and the first thing anyone reads about that family."""
    config = _outlined(tmp_path)
    shipped = ship(config, "DX1", why="It works now.")
    assert shipped.emptied == "I"


def test_a_parent_that_still_holds_a_child_is_not_named(tmp_path):
    # The ordinary case, and not worth a line: the introduction still introduces something.
    config = _outlined(
        tmp_path,
        prose="# Improvements\n\n## I A family of designs\n\nThe problem.\n\n"
        "### §I.1 DX1 The first design\n\nThe reasoning.\n\n"
        "### §I.2 A second design\n\nThe reasoning.\n",
    )
    assert ship(config, "DX1", why="It works now.").emptied is None


def test_nothing_is_named_where_an_anchor_has_no_parent(tmp_path):
    # Under `ref_scheme = "id"` the anchor is the id and there is no parent to empty, so the
    # question is not asked rather than answered "none".
    config = project(tmp_path)
    assert ship(config, "RK1", why="It works now.").emptied is None


def test_the_introduction_is_never_rewritten(tmp_path):
    # Noticing is the tool's; what it should say instead is a judgement (L4). The paragraph
    # is exactly where it was, and the answer names the door.
    config = _outlined(tmp_path)
    ship(config, "DX1", why="It works now.")
    prose = (tmp_path / "IMPROVEMENTS.md").read_text(encoding="utf-8")
    assert "The problem this family solves, in the present tense." in prose
    assert "## I A family of designs" in prose


def test_the_answer_names_the_anchor_and_the_door(tmp_path, capsys):
    config = _outlined(tmp_path)
    assert main(["-C", str(config.root), "ship", "DX1", "--why", "It works."]) == EXIT_OK
    out = capsys.readouterr().out
    assert "emptied  §I now has no subsections" in out
    assert "section amend I --body -" in out


def test_the_payload_carries_it(tmp_path, capsys):
    config = _outlined(tmp_path)
    assert main(
        ["-C", str(config.root), "ship", "DX1", "--why", "It works.", "--json"]
    ) == EXIT_OK
    # Under the prose file's object and not at the top level: it is a fact about the drop,
    # and the caller reading `cited` beside it is the caller this answers.
    assert json.loads(capsys.readouterr().out)["improvements"]["emptied"] == "I"


# -- the gate's own path rule, held where the sentence is composed (RK497) -----


def _with_source(tmp_path: Path) -> Config:
    """The fixture plus a `src/` the repository knows, which is what makes `src/gone.py` a
    claim at all: a token whose directory nothing has heard of is not a path (RK55, RK217) —
    60 of Shio's 61 findings were a MIME type or a method name sharing a slash."""
    config = project(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "kept.py").write_text("x = 1\n", encoding="utf-8")
    return config


def test_a_why_naming_a_path_the_repository_lacks_is_refused_and_writes_nothing(tmp_path):
    """RK497. L1 puts the schema where the text is created, and this was the one ledger rule
    the gate held alone: a `ship --why` citing a path from its own reproduction reported
    success, the entry landed, the commit was made, and `path.missing` came off an unrelated
    run afterwards — repaired by a second commit describing nothing shipped."""
    config = _with_source(tmp_path)
    files = (ROADMAP, CHANGELOG, IMPROVEMENTS)
    before = {name: (tmp_path / name).read_text(encoding="utf-8") for name in files}
    with pytest.raises(NoSuchPath) as refused:
        ship(config, "RK1", why="It works now, in `src/gone.py`.")
    assert refused.value.missing == ("src/gone.py",)
    assert refused.value.named == "--why"
    # The flag and not the sentence, because the flag is what the caller retypes — and the
    # file, because "records work that is done" is the argument for refusing at all.
    assert "--why names src/gone.py" in str(refused.value)
    assert "docs/CHANGELOG.md records work that is done" in str(refused.value)
    assert {name: (tmp_path / name).read_text(encoding="utf-8") for name in files} == before


def test_the_path_that_resolves_ships_exactly_as_before(tmp_path):
    # The other half of a refusal worth having: the sentence anybody means to write costs a
    # stat per token and no subprocess at all (RK222).
    config = _with_source(tmp_path)
    ship(config, "RK1", why="It works now, in `src/kept.py`.").save()
    assert "in `src/kept.py`" in (tmp_path / CHANGELOG).read_text(encoding="utf-8")


def test_an_open_line_may_still_name_the_file_its_task_will_write(tmp_path):
    """The boundary, and the reason `_paths` reads the ledger alone: a roadmap line describes
    work that has *not* happened, so the paths in it are disproportionately the artefacts its
    task exists to create. Shio had eight such findings and all eight were false."""
    config = _with_source(tmp_path)
    from roadkeep.authoring import add

    add(
        config,
        block="A",
        symptom="A fourth symptom nothing answers yet",
        why="Because `src/not-yet.py` does not exist.",
    )
    assert "src/not-yet.py" in (tmp_path / ROADMAP).read_text(encoding="utf-8")
    assert [f for f in lint(config).findings if f.code == "path.missing"] == []


def test_every_verb_that_writes_ledger_prose_holds_the_rule(tmp_path):
    """One helper on four doors, asserted as the four rather than as the helper: a verb added
    tomorrow that writes an entry and skips it is the defect this task was filed about."""
    config = _with_source(tmp_path)
    absent = "Because `src/gone.py` says so."
    with pytest.raises(NoSuchPath):
        retire(config, "RK3", reason=absent)
    with pytest.raises(NoSuchPath):
        record(config, block="A", symptom="A symptom nobody planned for", why=absent)
    with pytest.raises(NoSuchPath):
        record(
            config,
            block="A",
            symptom="A symptom naming `src/gone.py` nobody planned for",
            why="Because it was done.",
        )
    ship(config, "RK1", why="It works now.")
    with pytest.raises(NoSuchPath):
        amend_record(config, "RK1", why=absent)


# -- the refusal that named no door (RK1044) ---------------------------------


def test_retire_on_an_already_recorded_id_names_the_verb_that_closes_it(tmp_path, capsys):
    """Reported as a state where every door was shut, and two of them were not: the gate
    reports this as `id.two-files`, and `ship <id>` with no `--why` closes the open line
    against the entry already there. What was missing was the refusal saying so — a caller
    who reaches it has already tried the verb whose whole job is a line leaving another way."""
    config = project(tmp_path)
    ledger = config.root / CHANGELOG
    ledger.write_text(
        ledger.read_text(encoding="utf-8").rstrip("\n")
        + "\n\n- ✅ **RK1** **A first symptom** — It shipped once already.\n",
        encoding="utf-8",
    )
    with pytest.raises(AlreadyRecorded) as raised:
        retire(Config.discover(tmp_path), "RK1", reason="It duplicates a closed id.")
    said = str(raised.value)
    # The invariant is still stated: what it protects is why it refuses at all.
    assert "a second entry would make the ledger disagree" in said
    assert "ship RK1" in said and "writing nothing to the ledger" in said


def test_the_door_it_names_is_the_one_that_works(tmp_path):
    """A refusal that hands over an argv hands over one that runs, which is the property
    `test_hinting` holds over the package — asked here because this sentence is composed."""
    config = project(tmp_path)
    ledger = config.root / CHANGELOG
    ledger.write_text(
        ledger.read_text(encoding="utf-8").rstrip("\n")
        + "\n\n- ✅ **RK1** **A first symptom** — It shipped once already.\n",
        encoding="utf-8",
    )
    done = ship(Config.discover(tmp_path), "RK1")
    # A `Closure` and not a `Departure`: the entry is somebody else's write and is the
    # evidence here, so the ledger is opened only to be read.
    assert isinstance(done, Closure) and done.recorded.task.id == "RK1"
    done.save()
    assert "**RK1**" not in read(Config.discover(tmp_path), ROADMAP)


# -- a remedy that was the command that failed (RK1045) ----------------------


def _recorded_beside(tmp_path: Path, marker: str) -> Config:
    """A roadmap line under ``marker`` whose id the ledger already closes with a full entry."""
    config = project(tmp_path)
    if marker != DESIGNED:
        set_status(config, "RK1", marker)
    ledger = config.root / CHANGELOG
    ledger.write_text(
        ledger.read_text(encoding="utf-8").rstrip("\n")
        + "\n\n- ✅ **RK1** **A first symptom** — It shipped once already.\n",
        encoding="utf-8",
    )
    return Config.discover(tmp_path)


def test_the_door_is_named_only_where_the_closure_path_takes_the_line(tmp_path):
    """RK1044 added the clause unconditionally and RK1045 narrowed it to the state the door
    is true of. What decides that is the **entry's** qualifier since RK1075, not the
    roadmap's marker: an entry naming a half is a live partial and `ship` completes it, so
    naming a closure there would hand the caller the wrong one of two exits.

    The ⏳ line this used to be about is now closable and is covered above — it was the state
    with no verb at all, which is why the suppression could not be the whole answer.
    """
    beside = _recorded_beside(tmp_path, PARTIAL)
    half = read(beside, CHANGELOG).replace("**RK1**", "**RK1 (local half)**")
    (beside.root / CHANGELOG).write_text(half, encoding="utf-8")
    config = Config.discover(beside.root)

    # `retire`, because it reaches the refusal with a derived sentence and needs no `--why`.
    with pytest.raises(PartRecorded) as refused:
        retire(config, "RK1", reason="Nobody will do the rest.")
    # Its own refusal and not this one, and it names `ship RK1` as the **completion** — the
    # exit that rewrites the entry. What it must never offer is the closure, which removes
    # the line against an entry recording only a half and drops the one that never landed.
    said = str(refused.value)
    assert "writing nothing to the ledger" not in said
    # Named as *the* exit and no longer as a conditional (RK1138): "if the rest landed after
    # all" read as advice for a different case, and the case the author was in had none.
    assert f"{invocation()} ship RK1 --why" in said
    assert "if the rest landed after all" not in said


def test_the_door_it_does_name_resolves_the_state(tmp_path):
    """The rule RK1045 argues for: a remedy is a promise, and a promise nothing runs is
    prose. So the sentence is not read here — the command it names is executed, against the
    state that raised it, and the state has to be gone afterwards."""
    config = _recorded_beside(tmp_path, DESIGNED)
    with pytest.raises(AlreadyRecorded) as refused:
        retire(config, "RK1", reason="It duplicates a closed id.")
    assert refused.value.closable and "ship RK1" in str(refused.value)

    done = ship(Config.discover(tmp_path), "RK1")
    assert isinstance(done, Closure) and done.recorded.task.id == "RK1"
    done.save()
    after = Config.discover(tmp_path)
    assert "**RK1**" not in read(after, ROADMAP)
    assert read(after, CHANGELOG).count("**RK1**") == 1, "the ledger was only read"
    assert not [one for one in lint(after).findings if one.code == "id.two-files"]


# -- the pair neither decision covers (RK1046) -------------------------------


def test_the_qualifier_may_be_written_where_the_line_is_a_live_partial(tmp_path):
    """The cycle. A ⏳ line beside an unqualified entry had every verb shut: `ship` and
    `retire` on one guard, the gate deliberately silent (RK121), and the two doors that
    remained naming each other — `record amend --part` sends the caller to `ship --part`,
    which sends them back. Each refusal correct about its own invariant."""
    config = _recorded_beside(tmp_path, PARTIAL)
    with pytest.raises(AlreadyRecorded):
        ship(config, "RK1", part="the first half", why="Half of it works.")

    # `NoQualifier` exists so an entry cannot claim a partial delivery while its line "is
    # gone or closed", which is the one thing this state is not.
    amended = amend_record(config, "RK1", part="the first half")
    amended.save()
    after = Config.discover(tmp_path)
    assert "**RK1 (the first half)**" in read(after, CHANGELOG)

    # And then the completion a partial already has closes it — no widening required.
    done = ship(after, "RK1", why="The rest of it works now.")
    done.save()
    closed = Config.discover(tmp_path)
    assert "**RK1**" not in read(closed, ROADMAP)
    assert lint(closed).findings == ()


def test_an_entry_whose_line_is_gone_still_refuses_the_qualifier(tmp_path):
    """The bound, and the reason `NoQualifier` was written: with no open line to have been
    written from, a qualifier added here is an entry claiming a delivery in halves that
    nothing in the roadmap says are coming."""
    config = project(tmp_path)
    ship(config, "RK2", why="It works now.").save()
    with pytest.raises(NoQualifier):
        amend_record(Config.discover(tmp_path), "RK2", part="the first half")


def test_a_plain_open_line_still_refuses_it_too(tmp_path):
    """Only a **live partial**, which is what the roadmap's ⏳ says: a 📋 line beside an
    entry is the leftover `id.two-files` reports and `ship <id>` closes, and writing a
    qualifier there would invent a half nobody shipped."""
    with pytest.raises(NoQualifier):
        amend_record(_recorded_beside(tmp_path, DESIGNED), "RK1", part="the first half")


# -- the exit a partial's abandonment actually has (RK1138) ----------------------


def test_the_abandonment_of_a_remainder_is_recorded_by_the_completion(tmp_path):
    """RK1138, observed on Shio's SH698: instrumented, the cure refuted, the remainder
    abandoned — and every door refused. The hint sent the author to `record amend --part`, which
    restates the entry and leaves the refusal standing, so the only verb that closed the line
    was one whose contract read as "the rest landed".

    Executed rather than argued, which is RK1045's rule for a remedy: the sentence names
    `ship <id> --why`, so this runs it and reads what the ledger then says.
    """
    beside = _recorded_beside(tmp_path, PARTIAL)
    half = read(beside, CHANGELOG).replace("**RK1**", "**RK1 (local half)**")
    (beside.root / CHANGELOG).write_text(half, encoding="utf-8", newline="")
    config = Config.discover(beside.root)

    with pytest.raises(PartRecorded):
        retire(config, "RK1", reason="Nobody will do the rest.")
    # The door the refusal names, with the author's own sentence about what happened.
    ship(
        Config.discover(beside.root),
        "RK1",
        why="The local half landed and the rest was abandoned as unreproducible.",
    ).save()
    ledger = read(Config.discover(beside.root), CHANGELOG)
    assert "the rest was abandoned as unreproducible" in ledger
    # The qualifier is gone, because nothing is outstanding any more — and the half that
    # shipped is still the reason this line left by the delivering door.
    assert "(local half)" not in ledger
    assert "✅ **RK1**" in ledger


def test_the_line_is_gone_and_the_gate_is_clean_afterwards(tmp_path):
    # The state RK1138 said had no exit, asserted as a state: no open line, one entry, and a
    # tree `lint` passes — which is what makes the door a door rather than a message.
    beside = _recorded_beside(tmp_path, PARTIAL)
    half = read(beside, CHANGELOG).replace("**RK1**", "**RK1 (local half)**")
    (beside.root / CHANGELOG).write_text(half, encoding="utf-8", newline="")
    ship(
        Config.discover(beside.root),
        "RK1",
        why="The local half landed and the rest was abandoned as unreproducible.",
    ).save()
    config = Config.discover(beside.root)
    assert config.document("roadmap").by_id().get("RK1") is None
    assert [f.code for f in lint(config).findings] == []


def test_a_second_entry_is_what_the_gate_calls_a_duplicate(tmp_path):
    """Why the door is not a second record, measured rather than asserted: the shape RK1138's
    design asked for first would leave the tree red on the gate's own `id.duplicate`."""
    beside = _recorded_beside(tmp_path, PARTIAL)
    half = read(beside, CHANGELOG).replace("**RK1**", "**RK1 (local half)**")
    (beside.root / CHANGELOG).write_text(
        half + "- 🗑 **RK1** **A first symptom** — abandoned: nobody will do the rest.\n",
        encoding="utf-8",
    )
    codes = {f.code for f in lint(Config.discover(beside.root)).findings}
    assert "id.duplicate" in codes


def test_appending_a_sentence_is_what_the_ledger_calls_two(tmp_path):
    # And the second shape: an entry holds one sentence, so the abandonment cannot be appended
    # to the one already there — and appending *inside* it would be this tool writing prose (L4).
    from roadkeep.kernel.schema import Schema, Task

    schema = Schema().as_ledger()
    task = Task(
        status="✅",
        id="RK1",
        block="A",
        symptom="A first symptom",
        why="Because the local half landed. The rest was abandoned: it never reproduced.",
        part="local half",
    )
    assert "why.sentences" in {v.code for v in schema.validate(task)}


# -- what is left in the block, said by the write (RK1164) --------------------


def test_a_ship_says_what_is_left_in_the_block_it_just_changed(tmp_path, capsys):
    """Measured over one block: six ships, six `list` calls immediately after, each asking the
    same question. `_event` had already read the standing to name the stage and reduced it to one
    word, so the second call re-read three files to recompute what the first one held.

    The **live** case is the one that costs the call, and it is the one `_print_standing` stays
    silent about in `list` — there an empty listing under a live block was the filter's doing,
    and here the count is the question: is this block finished, and is there another line.
    """
    config = project(tmp_path)  # Block A holds RK1 and RK2
    assert main(["-C", str(config.root), "ship", "RK1", "--why", "It works now."]) == EXIT_OK
    printed = capsys.readouterr().out
    assert "event    RK1  Block A  live" in printed
    assert "Block A has 1 open" in printed

    assert main(["-C", str(config.root), "ship", "RK2", "--why", "It works now."]) == EXIT_OK
    printed = capsys.readouterr().out
    assert "Block A is finished" in printed and "records 2 filed under it" in printed


def test_the_payload_carries_the_standing_in_the_shape_list_answers_with(tmp_path, capsys):
    """One shape and not a second (RK1164): `_standing_json` is what `list` and `pick` publish,
    so a caller acting on a ship reads the same fields it already knows. `stage` stays beside it
    — it is what the droppable offer branches on, and what every consumer written before this
    reads."""
    config = project(tmp_path)
    argv = ["-C", str(config.root), "ship", "RK1", "--why", "It works now.", "--json"]
    assert main(argv) == EXIT_OK
    event = json.loads(capsys.readouterr().out)["event"]
    assert event["stage"] == "live"
    assert event["standing"] == {
        "block": "A",
        "state": "live",
        "sentence": "Block A has 1 open",
        "open": 1,
        "recorded": 1,
        "paused": 0,
    }


def test_the_clause_arrives_on_the_pipe_like_every_other_prose_argument(tmp_path, capsys, monkeypatch):
    """RK1176. `-` is documented on every prose argument, and this one — added after the handler's
    own `_piped(args.why)` line was written — reached the ledger as a literal dash: published,
    valid to the gate, and wrong in a way only a reader notices.

    Which arguments read a pipe is now the parser's claim, resolved once in `dispatch` for both
    surfaces, so an argument added tomorrow is reached by the declaration rather than by whoever
    remembers the call site.
    """
    config = project(tmp_path)
    monkeypatch.setattr("sys.stdin", io.StringIO("the lookup it proposed already existed\n"))
    argv = [
        "-C", str(tmp_path), "ship", "RK1",
        "--why", "The first symptom no longer happens.",
        "--superseded-design", "-",
    ]
    assert main(argv) == EXIT_OK
    capsys.readouterr()
    ledger = read(config, CHANGELOG)
    assert "superseded: the lookup it proposed already existed)" in ledger
    assert "superseded: -)" not in ledger


def test_two_arguments_sent_to_one_pipe_are_refused_on_this_verb_too(tmp_path, capsys, monkeypatch):
    """The other half of RK1176, and the worse one: `_one_pipe` existed, was consulted in one
    handler, and this verb sent two arguments to one stream — the pipe going to the first that
    asked and the second keeping its dash. A refusal that is documented and never asked is worse
    than none, because the documentation promises it."""
    project(tmp_path)
    monkeypatch.setattr("sys.stdin", io.StringIO("one sentence for two fields\n"))
    argv = [
        "-C", str(tmp_path), "ship", "RK1", "--why", "-", "--superseded-design", "-",
    ]
    assert main(argv) == EXIT_USAGE
    said = capsys.readouterr().err
    assert "--why and --superseded-design both read stdin" in said
    # Spelled as the caller typed them, never as the dest: a refusal naming `superseded_design`
    # is about a flag nobody passed.
    assert "superseded_design" not in said


# -- a block that is a standing category (RK1180) -----------------------------


CATEGORIES = """prefix = "RK"
[blocks]
standing = ["N"]
[files]
roadmap = "ROADMAP.md"
changelog = "CHANGELOG.md"
"""


def categorised(tmp_path: Path) -> Config:
    """A project with one block that finishes and one that never does."""
    (tmp_path / "roadkeep.toml").write_text(CATEGORIES, encoding="utf-8")
    (tmp_path / "ROADMAP.md").write_text(
        "## Block A — The model\n\n## Block N — Realignment of what already shipped\n\n"
        f"- {DESIGNED} **RK9** (deps: —) **A realignment worth a line** — Because of a reason.\n",
        encoding="utf-8",
    )
    (tmp_path / "CHANGELOG.md").write_text(
        f"## Block A — The model\n\n- {SHIPPED} **RK1** **A symptom** — it was done.\n\n"
        "## Block N — Realignment of what already shipped\n\n"
        f"- {SHIPPED} **RK2** **An earlier realignment** — it was done.\n",
        encoding="utf-8",
    )
    return Config.discover(tmp_path)


def test_a_standing_block_is_caught_up_and_never_finished(tmp_path, capsys):
    """RK1180. Some blocks are not projects: a category titled *realignment of what already
    shipped* receives work forever and is empty only in the sense that nobody has filed the next
    one yet. Measured on such a block in one session: declared, emptied and dropped **three
    times**, each drop followed within the hour by a finding that re-declared it.

    The churn in the file was not the cost. A host project hangs a block-completion sweep off the
    signal — four public surfaces, a coverage matrix, a docs build — designed to run once per
    capability, and running it three times trains the reader to read completion as noise.
    """
    config = categorised(tmp_path)
    assert main(["-C", str(tmp_path), "ship", "RK9", "--why", "It is realigned now."]) == EXIT_OK
    printed = capsys.readouterr().out
    assert "caught up" in printed and "a standing category, which fills again" in printed
    assert "finished" not in printed
    # And no offer to withdraw a heading that fills again, which is the churn itself.
    assert "block drop" not in printed


def test_a_project_block_still_finishes(tmp_path, capsys):
    """The control, and the reason this is configuration and not a heuristic (L6): the two states
    have identical counts — nothing open, entries recorded — and only the plan knows which is
    which."""
    config = categorised(tmp_path)
    (config.root / "ROADMAP.md").write_text(
        "## Block A — The model\n\n"
        f"- {DESIGNED} **RK9** (deps: —) **A symptom worth a line** — Because of a reason.\n\n"
        "## Block N — Realignment of what already shipped\n",
        encoding="utf-8",
    )
    assert main(["-C", str(tmp_path), "ship", "RK9", "--why", "It works now."]) == EXIT_OK
    printed = capsys.readouterr().out
    assert "is finished" in printed and "caught up" not in printed


# -- the remainder as data, not as a subtraction (RK1233) ----------------------


def test_the_open_line_states_what_is_left(tmp_path):
    """RK1226 put the landed half on the brief and left the other one an inference: a reader
    handed `landed the parser half` beside a symptom describing the whole works out the rest.

    Better than reading two files, and still a reconstruction — done by whoever picks the line
    up, from prose written for another purpose. `--remainder` is the caller's own sentence for
    what is left, written into the line's `why` in the same transaction.
    """
    config = project(tmp_path)
    landed = ship(
        config, "RK1", part="the parser half", why="the parser reads it now.",
        remainder="The writer half is still to do.",
    )
    landed.save()
    line = config.path("roadmap").read_text(encoding="utf-8")
    assert "The writer half is still to do." in line
    # The symptom is untouched: a task half-delivered is still that symptom's task, and
    # narrowing the falsifiable claim is `restate`'s act and not a shipment's (RK7).
    assert "A first symptom" in line


def test_the_ledger_states_only_what_happened(tmp_path):
    """The decision RK1226 declined to take and this settles: the remainder goes on the
    **roadmap line** and never on the entry. A forward-looking clause in the ledger is history
    stating work that has not happened, and nothing would update it when the rest ships."""
    config = project(tmp_path)
    ship(
        config, "RK1", part="the parser half", why="the parser reads it now.",
        remainder="The writer half is still to do.",
    ).save()
    recorded = config.path("changelog").read_text(encoding="utf-8")
    assert "the parser half" in recorded
    assert "The writer half is still to do." not in recorded


def test_both_halves_are_fields_on_one_answer(tmp_path):
    """The property RK1226 named and this completes: resuming a partial should not require
    reading the rationale to learn what is left."""
    from roadkeep.briefing import brief

    config = project(tmp_path)
    ship(
        config, "RK1", part="the parser half", why="the parser reads it now.",
        remainder="The writer half is still to do.",
    ).save()
    gathered = brief(Config.discover(tmp_path), "RK1")
    assert gathered.landed == ("the parser half",)
    assert gathered.task.why == "The writer half is still to do."


def test_a_remainder_is_held_to_the_limits_a_why_is(tmp_path):
    """`replace_task` re-renders from data and checks nothing, so a remainder over its limit
    would land as a line the project's own gate refuses."""
    config = project(tmp_path)
    with pytest.raises(SchemaError) as refused:
        ship(config, "RK1", part="half", why="half works.", remainder="x" * 400)
    # Every rule a `why` has, not only its width: the remainder is that field.
    assert "why.too-long" in [one.code for one in refused.value.violations]
    # Nothing written, which is what "validates all three edits first" means.
    assert "RK1" not in config.path("changelog").read_text(encoding="utf-8")


def test_a_refused_remainder_is_reported_under_the_flag_that_carried_it(tmp_path):
    """RK1262. It is validated as the reopened line's `why`, because that is what it becomes —
    so the refusal read `why: why is a sentence: end it` with a correctly terminated `--why`
    adjacent on the same command line. True, and no help in deciding which string to fix."""
    config = project(tmp_path)
    with pytest.raises(RemainderRefused) as refused:
        ship(
            config,
            "RK1",
            part="half",
            why="Half of it works.",
            remainder="the other half is still open",
        )

    # The field is the flag, and the code is still the rule that was broken: one is what to
    # edit and the other is what anything greppable keys on.
    assert [(one.field, one.code) for one in refused.value.violations] == [
        ("remainder", "why.no-terminator")
    ]
    # And one sentence saying where a `why` rule came from, above the rows rather than in them.
    assert "--remainder becomes RK1's why when the partial lands" in refused.value.about
    assert "the --why on this call is the ledger entry's own sentence" in refused.value.about


def test_the_ledger_sentences_own_refusal_still_names_why(tmp_path):
    """The other half of the same distinction: `--why` *is* the field it is checked as, so
    renaming it would move the defect rather than close it."""
    config = project(tmp_path)
    with pytest.raises(SchemaError) as refused:
        ship(
            config,
            "RK1",
            part="half",
            why="Half of it works",
            remainder="The other half is still open.",
        )

    assert [one.field for one in refused.value.violations] == ["why"]
    assert not isinstance(refused.value, RemainderRefused)
    assert not refused.value.about


def test_a_line_already_carrying_drift_is_not_blamed_on_the_remainder(tmp_path):
    """The guard, which is this task's own defect pointed the other way: a rule broken by some
    field the caller never passed is not the remainder's, and framing it as one would send them
    to edit the string they had just written correctly."""
    # A pointer naming another line's anchor: refused on the roadmap, and invisible on the
    # ledger entry, whose pointer `as_recorded` drops — so this is a violation only the
    # re-validation of the reopened line can raise.
    config = project(tmp_path, roadmap=BACKLOG.replace(RK1, RK1.replace("→ §RK1", "→ §RK9")))
    with pytest.raises(SchemaError) as refused:
        ship(
            config,
            "RK1",
            part="half",
            why="Half of it works.",
            remainder="The other half is still open.",
        )

    assert not isinstance(refused.value, RemainderRefused)
    assert "ref" in [one.field for one in refused.value.violations]


def test_declining_it_leaves_the_sentence_the_line_had(tmp_path):
    """Every call before this argument, and every one that does not want it."""
    config = project(tmp_path)
    ship(config, "RK1", part="the parser half", why="the parser reads it now.").save()
    assert "Because of a reason." in config.path("roadmap").read_text(encoding="utf-8")


def test_a_remainder_without_a_part_is_refused(tmp_path, capsys):
    """A remainder on a whole shipment is a sentence about a line being removed, and honouring
    it silently would write the caller's words into a `why` the same transaction deletes."""
    project(tmp_path)
    argv = ["-C", str(tmp_path), "ship", "RK1", "--why", "It works.", "--remainder", "left"]
    assert main(argv) == EXIT_USAGE
    assert "--remainder is what is left after --part" in capsys.readouterr().err


# -- the decision the deleted design leaves behind (RK1269) -------------------

DECISIONS = "docs/DECISIONS.md"

DECIDED = """# Decisions

## Block A — The model

## Block B — Authoring
"""


def _deciding(tmp_path: Path, *, extra_config: str = "") -> Config:
    """The fixture plus a declared `decisions` role, which is the whole opt-in.

    The role's key is inserted into `[files]` rather than appended, so a caller passing an
    `extra_config` that opens a table does not land the path under it — which is a config that
    parses and declares something else, and the quietest possible fixture bug.
    """
    config = project(tmp_path, extra_config=extra_config)
    (tmp_path / "roadkeep.toml").write_text(
        (tmp_path / "roadkeep.toml")
        .read_text(encoding="utf-8")
        .replace(
            f'improvements = "{IMPROVEMENTS}"',
            f'improvements = "{IMPROVEMENTS}"\ndecisions = "{DECISIONS}"',
        ),
        encoding="utf-8",
    )
    with (tmp_path / DECISIONS).open("w", encoding="utf-8", newline="") as handle:
        handle.write(DECIDED)
    return Config.discover(tmp_path)


def test_a_decision_that_outlives_the_work_gets_a_governed_line(tmp_path):
    """The defect. A section holds three contents with three half-lives and `ship` deleted all
    three alike: the investigation dies with the ship, the criterion becomes a test, and the
    decision is the constraint that has to stay true after the code moves — kept by hand, in a
    file nothing governs, or not at all."""
    config = _deciding(tmp_path)
    departure = ship(
        config,
        "RK1",
        why="The first symptom no longer happens.",
        decides="The store is the repository: no database and no service.",
    )
    departure.save()

    decided = read(Config.discover(tmp_path), DECISIONS)
    # An ADR read as this format: an id, a marker, one falsifiable claim and a reason.
    assert (
        "- ✅ **RK1** **A first symptom** — The store is the repository: no database "
        "and no service." in decided
    )
    # No deps and no pointer, the section it survived being deleted in the same transaction.
    assert "(deps:" not in decided and "→ §" not in decided
    # And the other three edits are exactly what they were.
    assert "**RK1**" not in read(Config.discover(tmp_path), ROADMAP)
    assert "✅ **RK1**" in read(Config.discover(tmp_path), CHANGELOG)
    assert lint(Config.discover(tmp_path)).findings == ()


def test_a_project_with_no_decisions_role_is_refused_and_told_which_door(tmp_path):
    # Refused and never scaffolded on the way past, which is `defer`'s rule about the store:
    # a governed file invented at the moment one is needed is a format decided by a verb.
    config = project(tmp_path)
    before = files(config)
    with pytest.raises(KeyError) as caught:
        ship(config, "RK1", why="It works now.", decides="A constraint that outlives it.")

    assert "declare decisions" in str(caught.value)
    assert files(Config.discover(tmp_path)) == before


def test_a_partial_has_outlived_nothing_because_its_section_stays(tmp_path):
    # The section is still being read by the rest of the work, so no reading of it has
    # survived a deletion yet. The refusal names the call that does delete.
    config = _deciding(tmp_path)
    before = files(config)
    with pytest.raises(NoDecision) as caught:
        ship(
            config,
            "RK1",
            why="Half of it works.",
            part="local half",
            decides="Too early to say.",
        )

    assert "ship RK1" in str(caught.value) and "local half" in str(caught.value)
    assert files(Config.discover(tmp_path)) == before
    assert read(Config.discover(tmp_path), DECISIONS) == DECIDED


def test_a_closure_deletes_the_section_so_it_takes_the_decision_too(tmp_path):
    """The one flag of the three that reaches this door (RK62, RK1269): the other two restate
    a ledger sentence this path leaves alone, and a decision is a line in a file of its own —
    filed where the section is deleted, which this call does."""
    config = _deciding(tmp_path)
    (tmp_path / CHANGELOG).write_text(INTERRUPTED, encoding="utf-8", newline="")
    config = Config.discover(tmp_path)
    closure = ship(config, "RK1", decides="The reader keeps every source line verbatim.")
    closure.save()

    assert "The reader keeps every source line verbatim." in read(
        Config.discover(tmp_path), DECISIONS
    )
    assert "**RK1**" not in read(Config.discover(tmp_path), ROADMAP)


def test_a_decision_over_the_limit_costs_a_refusal_and_no_write(tmp_path):
    # The fourth edit is part of the same all-or-none: it is composed and validated before the
    # roadmap is touched, so a sentence past the role's own limit leaves four untouched files.
    config = _deciding(tmp_path)
    before = files(config)
    with pytest.raises(SchemaError):
        ship(
            config,
            "RK1",
            why="The first symptom no longer happens.",
            decides="A constraint " * 40,
        )

    assert files(Config.discover(tmp_path)) == before
    assert read(Config.discover(tmp_path), DECISIONS) == DECIDED


def test_the_flag_reaches_the_command_line_and_answers_as_a_write(tmp_path, capsys):
    config = _deciding(tmp_path)
    assert (
        main(
            [
                "-C",
                str(tmp_path),
                "ship",
                "RK1",
                "--why",
                "The first symptom no longer happens.",
                "--decides",
                "The store is the repository.",
                "--json",
            ]
        )
        == EXIT_OK
    )
    payload = json.loads(capsys.readouterr().out)
    # A file and a line, as the ledger's own block is: this is a write and not a note.
    assert payload["decisions"]["file"] == DECISIONS
    assert payload["decisions"]["line"] > 0
    assert "The store is the repository." in payload["decisions"]["rendered"]


# -- the door a decision leaves by (RK1274) -----------------------------------


def _decided(tmp_path: Path) -> Config:
    """The fixture with two decisions already filed, which is what a supersession needs."""
    config = _deciding(tmp_path)
    ship(config, "RK1", why="It works now.", decides="The store is the repository.").save()
    config = Config.discover(tmp_path)
    ship(config, "RK2", why="It works too.", decides="The store is a service after all.").save()
    return Config.discover(tmp_path)


def test_a_decision_that_stopped_holding_is_marked_and_never_deleted(tmp_path):
    """The defect. The grammar declared 🗑 legal in that file because `retire --superseded-by`
    is the ADR's Superseded-by read as this format, and nothing wrote it there — so the role
    recorded that a decision was made and never that it stopped holding, which is the half an
    ADR is kept for."""
    config = _decided(tmp_path)
    found = supersede(config, "RK1", by="RK2")
    found.save()

    decided = read(Config.discover(tmp_path), DECISIONS)
    assert "🗑 **RK1**" in decided
    assert "(superseded by RK2)." in decided
    # Both stay, which is the role's whole rule: the marker says which is live.
    assert "✅ **RK2**" in decided
    assert lint(Config.discover(tmp_path)).findings == ()


def test_the_reason_is_the_entry_that_replaced_it_and_not_a_field(tmp_path):
    # Derived end to end (RK8, L4): why one decision replaced another is the argument in the
    # replacing entry, already written and one line away, so there is nothing to compose.
    config = _decided(tmp_path)
    found = supersede(config, "RK1", by="RK2")

    assert found.replacement == "RK2"
    assert "superseded by RK2" in found.rendered
    assert "The store is the repository" in found.rendered, "the original sentence stays"


def test_a_decision_is_superseded_once_and_the_chain_reads_forwards(tmp_path):
    # Nothing here is deleted, so an entry carrying two forward pointers is a chain a reader
    # would have to date to walk — and this file records no dates, which is a non-goal.
    config = _decided(tmp_path)
    supersede(config, "RK1", by="RK2").save()
    config = Config.discover(tmp_path)
    before = read(config, DECISIONS)
    with pytest.raises(AlreadySuperseded) as caught:
        supersede(config, "RK1", by="RK2")

    assert "superseded once" in str(caught.value)
    assert read(Config.discover(tmp_path), DECISIONS) == before


def test_a_replacement_this_file_does_not_record_is_refused_by_name(tmp_path):
    """`NotRecorded` one file over, and separate for its reason: a caller holding a decision's
    address would be sent to the ledger by a message that was right about the other file."""
    config = _decided(tmp_path)
    with pytest.raises(NotDecided) as caught:
        supersede(config, "RK1", by="RK9")

    said = str(caught.value)
    assert "records no decision RK9" in said and "--by" in said
    assert "ship --decides" in said, "the door that files one is what a caller needs"


def test_a_decision_cannot_replace_itself_and_the_refusal_is_this_door_s(tmp_path):
    # `retire`'s message names that verb and its abandoned door, neither of which exists here.
    config = _decided(tmp_path)
    with pytest.raises(ValueError) as caught:
        supersede(config, "RK1", by="RK1")

    said = str(caught.value)
    assert "cannot supersede itself" in said
    assert "retire" not in said and "abandoned" not in said


def test_a_project_with_no_decisions_role_has_nothing_to_supersede(tmp_path):
    config = project(tmp_path)
    with pytest.raises(KeyError) as caught:
        supersede(config, "RK1", by="RK2")

    assert "declare decisions" in str(caught.value)


def test_the_verb_reaches_the_command_line_and_names_the_file_it_wrote(tmp_path, capsys):
    _decided(tmp_path)
    assert main(["-C", str(tmp_path), "supersede", "RK1", "--by", "RK2"]) == EXIT_OK
    said = capsys.readouterr().out

    assert "RK1 superseded by RK2" in said
    assert "nothing in this file is ever deleted" in said
    assert f"git add -- {DECISIONS}" in said


def test_the_allowance_prices_the_whole_transaction_and_not_one_line(tmp_path, capsys):
    """RK1275. Two flags landed in the ledger's sentence after this row learned to name the
    first, and a third writes a different file entirely — so the one sentence this format
    asked an author to compose blind was the one recording what outlives the code."""
    # The ledger's own limit, so the shipping row is printed at all: it is silent where the
    # two allowances agree, two numbers for one field being the fact worth seeing.
    config = _deciding(tmp_path, extra_config="\n[limits.changelog]\nwhy = 150\n")
    assert main(["-C", str(config.root), "brief", "RK1"]) == EXIT_OK
    out = capsys.readouterr().out

    # The ledger's sentence, and both clauses that compose into it.
    assert "shipping why" in out
    assert f"less {supersession_cost('RK1')} for a `--superseded-design` clause" in out
    assert f"and {recording_cost('RK1')} for a `--recorded-in` wrapper" in out
    # And the third write, which is not that sentence: its own role, its own limit.
    assert "deciding why" in out and "decisions role's own limit" in out


def test_a_project_with_no_decisions_role_is_quoted_no_number_for_one(tmp_path, capsys):
    # Absent and not zero: a role this project does not declare has no line to compose for,
    # which is the same silence every other absent role gets here.
    project(tmp_path)
    assert main(["-C", str(tmp_path), "brief", "RK1"]) == EXIT_OK
    assert "deciding why" not in capsys.readouterr().out


def test_the_recording_wrapper_is_measured_through_the_composer(tmp_path):
    """Never by counting brackets, which is `supersession_cost`'s rule: a reworded clause moves
    the number rather than leaving it behind."""
    from roadkeep.shipping import _recording

    assert recording_cost("RK1") == width(_recording("x.", "RK1", "")) - width("x.")
    # Longer anchors cost more, which is the whole reason it is derived per line.
    assert recording_cost("RK1000") > recording_cost("RK1")


def test_a_decision_refused_over_the_inherited_claim_names_the_doors_that_are_real(tmp_path):
    """RK1281. `--decides` composes the decision from the task's own claim, which is right —
    a decision is *about* the problem the line stated. What it inherits with it is the claim's
    length, measured against a limit no flag on that call reaches, and the refusal then offered
    the remedy every symptom overrun gets: the rationale section this ship is deleting."""
    config = _deciding(tmp_path, extra_config="\n[limits.decisions]\nsymptom = 10\n")
    before = files(config)
    with pytest.raises(InheritedClaim) as caught:
        ship(config, "RK1", why="It works now.", decides="The store is the repository.")

    # `about` and not `str`, which `RemainderRefused` established: the violations are the
    # schema's and this is the sentence saying which door they open (RK420).
    said = caught.value.about
    assert "--decides writes no symptom" in said
    # The two doors that are real, and never the one that is not.
    assert "restate RK1" in said and "govern limits.symptom" in said
    assert "carried into docs/DECISIONS.md whole" in said
    # The whole transaction costs nothing, which is every other refusal here.
    assert files(Config.discover(tmp_path)) == before
    assert read(Config.discover(tmp_path), DECISIONS) == DECIDED


def test_the_refusal_is_still_the_schema_s_and_carries_its_numbers(tmp_path):
    # A `SchemaError` subclass, so a caller catching that class keeps catching this: what
    # changed is what the refusal says, and never which class of refusal it is.
    config = _deciding(tmp_path, extra_config="\n[limits.decisions]\nsymptom = 10\n")
    with pytest.raises(SchemaError) as caught:
        ship(config, "RK1", why="It works now.", decides="A constraint.")

    assert any(one.code == "symptom.too-long" for one in caught.value.violations)


def test_a_why_over_the_limit_there_is_still_refused_as_itself(tmp_path):
    """The other half of that catch: only a *symptom* violation is the inherited one. A `why`
    the caller typed too long is prose they can shorten, and re-labelling it would send them
    to `restate` over a field they wrote on this very call."""
    config = _deciding(tmp_path, extra_config="\n[limits.decisions]\nwhy = 30\n")
    with pytest.raises(SchemaError) as caught:
        ship(config, "RK1", why="It works now.", decides="A constraint " * 10)

    assert not isinstance(caught.value, InheritedClaim)


def test_the_brief_prices_the_claim_the_decision_would_inherit(tmp_path, capsys):
    # The read that could have said it beforehand priced the `why` and stopped, so the refusal
    # arrived at the write with nothing before it.
    config = _deciding(tmp_path, extra_config="\n[limits.decisions]\nsymptom = 10\n")
    assert main(["-C", str(config.root), "brief", "RK1"]) == EXIT_OK
    said = capsys.readouterr().out

    assert "deciding symptom" in said and "of 10 there" in said
    assert "`--decides` does not write one" in said


def test_a_decisions_file_as_wide_as_the_roadmap_says_nothing(tmp_path, capsys):
    # Printed only where it binds: two numbers for one field is the fact worth seeing, and
    # repeating the same one under another name teaches nobody anything (RK1174).
    _deciding(tmp_path)
    assert main(["-C", str(tmp_path), "brief", "RK1"]) == EXIT_OK
    assert "deciding symptom" not in capsys.readouterr().out


def test_the_door_the_schema_appends_is_dropped_where_it_is_false(tmp_path):
    """RK1285. `RemainderRefused`'s shape at the other end of the same message: there the
    *field* a violation named was wrong for the call, and here the **door** is — the schema
    appends "the remainder belongs in the improvements section" to every over-long prose
    field, and this is the one call where that section is the thing being deleted."""
    from roadkeep.kernel.schema import ELSEWHERE

    config = _deciding(tmp_path, extra_config="\n[limits.decisions]\nsymptom = 10\n")
    with pytest.raises(InheritedClaim) as caught:
        ship(config, "RK1", why="It works now.", decides="A constraint.")

    said = str(caught.value)
    # The rule survives whole — a code, a count and a limit — and only the advice goes.
    assert "symptom.too-long" in said and "limit is 10" in said
    assert ELSEWHERE.strip("; ") not in said
    # Removed by identity and never by guessing at the words: one writer, and a rewording
    # moves both ends at once.
    assert ELSEWHERE not in said


def test_every_other_over_long_field_keeps_the_door_it_always_had(tmp_path):
    # The clause is right nearly everywhere, which is why it is appended at all: an `add`
    # whose symptom is too long has exactly that remedy.
    from roadkeep.kernel.schema import ELSEWHERE

    config = project(tmp_path, extra_config="\n[limits]\nsymptom = 10\n")
    with pytest.raises(SchemaError) as caught:
        add(config, block="A", symptom="A symptom far too long for this", why="Because.")

    assert ELSEWHERE in str(caught.value)
