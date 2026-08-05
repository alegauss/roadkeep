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

import json
from pathlib import Path

import pytest

from roadkeep.provenance import invocation

from roadkeep import claiming, document
from roadkeep.authoring import UnknownBlock
from roadkeep.cli import EXIT_GATE, EXIT_OK, EXIT_USAGE, main
from roadkeep.config import Config
from roadkeep.document import Document, RoundTripError, StaleFile
from roadkeep.linting import lint
from roadkeep.schema import IN_PROGRESS, PARTIAL, Schema, SchemaError
from roadkeep.shipping import SecondPartial
from roadkeep.sections import SectionOccupied
from roadkeep.shipping import (
    Divergent,
    NoCompletion,
    NoOutcome,
    PartRecorded,
    AlreadyShipped,
    Closure,
    NoRestatement,
    NotOpen,
    Wrapped,
    retire,
    ship,
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
        assert claiming._read(claiming.path(tmp_path)) == {}  # noqa: SLF001
    finally:
        claiming.path(tmp_path).unlink(missing_ok=True)


def test_a_restated_why_is_refused_where_the_ledger_is_not_written(tmp_path):
    config = half_shipped(tmp_path)
    before = files(config)
    with pytest.raises(NoRestatement) as raised:
        ship(config, "RK1", why="Which the ledger already says.")
    assert "the ledger is not written here" in str(raised.value)
    assert files(config) == before


def test_an_open_line_whose_id_the_ledger_mentions_is_not_closed(tmp_path):
    # The condition that is easy to miss, and cost a real deletion before it was added:
    # Shio's `⏳ SH238` names the half that has not shipped while the ledger records the half
    # that did. That is `id.two-files` for `lint` to report — not a line for `ship` to delete.
    config = half_shipped(tmp_path, marker="⏳")
    before = files(config)
    with pytest.raises(AlreadyShipped) as raised:
        ship(config, "RK1", why="Because of a reason.")
    assert "disagree with itself" in str(raised.value)
    assert files(config) == before


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

    monkeypatch.setattr("roadkeep.document.stage", racing)
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

    monkeypatch.setattr("roadkeep.cli.ship", racing)
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

    monkeypatch.setattr("roadkeep.document.commit", watched)
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


def test_a_live_partial_is_still_not_a_leftover(tmp_path):
    # The case that cost a real task and a 224-word section: an open line whose id the
    # ledger also mentions is a live task where the marker says the work is in halves.
    config = project(
        tmp_path,
        roadmap=BACKLOG.replace("- 📋 **RK1**", "- ⏳ **RK1**"),
        changelog=INTERRUPTED,
    )
    with pytest.raises(AlreadyShipped):
        ship(config, "RK1", why="Because of a reason.")
    assert "⏳ **RK1**" in read(config, ROADMAP)
    assert "§RK1 A first design" in read(config, IMPROVEMENTS)


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
