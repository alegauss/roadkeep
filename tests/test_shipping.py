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

from roadkeep.authoring import UnknownBlock
from roadkeep.cli import EXIT_GATE, EXIT_OK, EXIT_USAGE, main
from roadkeep.config import Config
from roadkeep.document import RoundTripError
from roadkeep.schema import SchemaError
from roadkeep.shipping import (
    AlreadyShipped,
    Closure,
    NoRestatement,
    NotOpen,
    retire,
    ship,
)

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
) -> Config:
    """A throwaway project with the files it declares, and only those."""
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
    (tmp_path / "roadkeep.toml").write_text("\n".join(lines) + "\n", encoding="utf-8")
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
    shipment = ship(config, "RK1")
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
    shipment = ship(config, "RK2")
    assert shipment.ledger.entry.task.deps == ()
    assert shipment.ledger.entry.task.ref is None
    assert shipment.ledger.rendered == (
        "- ✅ **RK2** **A second symptom** — Because of another reason."
    )


def test_the_rationale_section_is_deleted_with_its_subsections(tmp_path):
    config = project(tmp_path)
    shipment = ship(config, "RK1")
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
    ship(config, "RK3").save()
    _, _, rationale = files(config)
    assert rationale.endswith("## Block B — Authoring\n")


def test_removing_the_last_task_of_a_block_leaves_one_blank_line(tmp_path):
    config = project(tmp_path)
    ship(config, "RK3").save()
    roadmap, _, _ = files(config)
    # The block is left as an empty block reads everywhere else — heading, one blank,
    # next heading — and not as a paragraph break the file never had.
    assert "\n\n\n" not in roadmap
    assert roadmap == BACKLOG.replace(f"{RK3}\n\n", "")


def test_shipping_the_last_line_of_the_file_leaves_no_trailing_blank(tmp_path):
    config = project(tmp_path, roadmap=f"## Block A — The model\n\n{RK1}\n")
    ship(config, "RK1").save()
    assert read(config, ROADMAP) == "## Block A — The model\n"


def test_the_files_keep_their_line_endings(tmp_path):
    config = project(
        tmp_path,
        roadmap=BACKLOG.replace("\n", "\r\n"),
        changelog=LEDGER.replace("\n", "\r\n"),
        improvements=RATIONALE.replace("\n", "\r\n"),
    )
    ship(config, "RK1").save()
    for name in (ROADMAP, CHANGELOG, IMPROVEMENTS):
        assert "\n" not in read(config, name).replace("\r\n", ""), name


# -- the fourth edit ---------------------------------------------------------


def test_every_line_that_named_the_task_is_re_derived(tmp_path):
    # In the same transaction, because `(deps: RK1)` becomes false at exactly the moment
    # this command runs and nothing else would ever revisit it (RK8).
    config = project(tmp_path)
    assert ship(config, "RK1").refreshed == ("RK2", "RK3")


def test_a_task_that_nothing_depends_on_re_derives_nothing(tmp_path):
    config = project(tmp_path)
    assert ship(config, "RK3").refreshed == ()


def test_the_design_sentence_is_kept_unless_the_author_restates_it(tmp_path):
    config = project(tmp_path)
    assert ship(config, "RK1").ledger.entry.task.why == "Because of a reason."
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
        ship(config, "RK9")
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
        ship(config, "RK1")
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
    ship(config, "RK1").save()
    # The roadmap line is gone, so the second call is refused by NotOpen — there is no line
    # to close and nothing to record.
    with pytest.raises(NotOpen):
        ship(config, "RK1")


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
    shipment = ship(config, "RK1")
    shipment.save()
    assert shipment.dropped is None
    assert shipment.kept == "§I.1 is also pointed at by RK2"
    assert "§I.1" in read(config, IMPROVEMENTS)


def test_the_last_line_pointing_at_a_shared_section_still_drops_it(tmp_path):
    # Not a permanent exemption: when the last owner leaves, the section leaves with it.
    config = outline_project(tmp_path)
    ship(config, "RK1").save()
    shipment = ship(Config.discover(tmp_path), "RK2")
    shipment.save()
    assert shipment.dropped is not None and shipment.dropped.anchor == "I.1"
    assert "§I.1" not in read(config, IMPROVEMENTS)


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
        ship(config, "RK1")
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
        ship(config, "RK3")
    assert "Block B" in str(raised.value)
    assert read(config, ROADMAP) == BACKLOG


def test_a_drifted_roadmap_is_not_rewritten(tmp_path):
    drifted = BACKLOG.replace("→ §RK1", "→ §7.1")
    config = project(tmp_path, roadmap=drifted)
    with pytest.raises(RoundTripError):
        ship(config, "RK2")
    assert files(config) == (drifted, LEDGER, RATIONALE)


def test_a_missing_section_is_reported_and_not_an_error(tmp_path):
    # A task can ship without a rationale section; failing at the moment the author is
    # finishing would be an obstacle, and silence would read as a section that was there.
    config = project(tmp_path, improvements="# Improvements\n\n## Block A — The model\n")
    shipment = ship(config, "RK1")
    assert shipment.dropped is None
    assert "no §RK1 section" in shipment.kept
    shipment.save()
    assert read(config, IMPROVEMENTS) == "# Improvements\n\n## Block A — The model\n"


def test_a_project_with_no_improvements_file_ships_two_edits(tmp_path):
    config = project(tmp_path, improvements=None)
    shipment = ship(config, "RK1")
    assert shipment.improvements is None
    assert shipment.kept == "this project declares no improvements file"
    shipment.save()
    assert read(config, ROADMAP) == BACKLOG.replace(f"{RK1}\n", "").replace(
        "(deps: RK1)", "(deps: RK1 ✅)"
    )


# -- the command -------------------------------------------------------------


def test_the_command_reports_every_edit_it_made(tmp_path, capsys):
    config = project(tmp_path)
    assert main(["-C", str(tmp_path), "ship", "RK1"]) == EXIT_OK
    out = capsys.readouterr().out
    assert f"RK1 → {CHANGELOG}:5 under Block A" in out
    assert f"removed  {ROADMAP}:5" in out
    assert f"dropped  §RK1 (5-12) from {IMPROVEMENTS}" in out
    assert "derived  RK2, RK3" in out
    assert SHIPPED_RK1 in read(config, CHANGELOG)


def test_json_carries_every_edit(tmp_path, capsys):
    project(tmp_path)
    assert main(["-C", str(tmp_path), "ship", "RK2", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["changelog"]["file"] == CHANGELOG
    assert payload["roadmap"] == {"file": ROADMAP, "removed": 6}
    assert payload["improvements"]["dropped"]["anchor"] == "RK2"
    assert payload["refreshed"] == []


def test_a_refusal_exits_two_and_writes_nothing(tmp_path, capsys):
    config = project(tmp_path)
    assert main(["-C", str(tmp_path), "ship", "RK9"]) == EXIT_USAGE
    assert "no open task RK9" in capsys.readouterr().err
    assert files(config) == (BACKLOG, LEDGER, RATIONALE)


def test_a_drifted_file_exits_one_because_the_gate_says_no(tmp_path, capsys):
    project(tmp_path, roadmap=BACKLOG.replace("→ §RK1", "→ §7.1"))
    assert main(["-C", str(tmp_path), "ship", "RK2"]) == EXIT_GATE
    assert "will not be rewritten" in capsys.readouterr().err
