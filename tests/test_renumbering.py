"""The id a merge allocated twice, moved without a departure (RK97).

The acceptance test is the measured case and nothing smaller: a roadmap line and a ledger
entry carrying one id, which `lint` refuses and no command could act on. One call has to
leave that tree clean — the line, its `§id` section and every dep naming it — because the
alternative the session actually took was three hand-edits in the files the guard exists
to keep hands out of.

Everything else here is a refusal, and each is about the same thing: an address is a fact
about the whole backlog, so a move that any file would contradict is refused before the
first byte is written.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from roadkeep.authoring import IdInUse
from roadkeep.backlog import NotOpen
from roadkeep.cli import EXIT_OK, EXIT_USAGE, main
from roadkeep.config import Config
from roadkeep.linting import lint
from roadkeep.renumbering import NotAnId, SameId, renumber
from roadkeep.kernel.schema import SchemaError

ROADMAP = "docs/ROADMAP.md"
CHANGELOG = "docs/CHANGELOG.md"
IMPROVEMENTS = "docs/IMPROVEMENTS.md"
DEFERRED = "docs/DEFERRED.md"

# The merge, as it was: the branch's RK90 open, main's RK90 recorded, and a line filed
# beside the first that names it.
BACKLOG = """# Roadmap

## Block A — The model

- 📋 **RK90** (deps: —) **the branch's own line** — Because the merge kept both. → §RK90
- 📋 **RK91** (deps: RK90) **a line that waits on it** — Because it was filed alongside. → §RK91
"""

LEDGER = """# Shipped

## Block A — The model

- ✅ **RK90** **main's own line** — Because main shipped it first.
"""

DESIGN = """# Improvements

## Block A — The model

### §RK90 The branch's design

Because the prose has to travel with the address.

### §RK91 The dependent's design

Because it points somewhere too.
"""

STORE = """# Set aside

## Block A — The model
"""

# The subtree RK113 measured: the task's own `.1` numbering, and — nested at the same
# depth — a heading that belongs to the *other* line and must not move with this one.
SUBTREE = """# Improvements

## Block A — The model

### §RK90 The branch's design

Because the prose has to travel with the address.

#### §RK90.1 The measurement under it

Because a subsection is the same address, one segment longer.

#### §RK91 The dependent's design

Because it points somewhere too.
"""

CONFIG = (
    'prefix = "RK"\n[files]\n'
    f'roadmap = "{ROADMAP}"\nchangelog = "{CHANGELOG}"\nimprovements = "{IMPROVEMENTS}"\n'
)


def project(tmp_path: Path, *, config: str = CONFIG, **files: str) -> Config:
    """The collision, on disk. `files` overrides or adds one by path."""
    (tmp_path / "roadkeep.toml").write_text(config, encoding="utf-8")
    written = {
        ROADMAP: BACKLOG,
        CHANGELOG: LEDGER,
        IMPROVEMENTS: DESIGN,
        **files,
    }
    for name, body in written.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            handle.write(body)
    return Config.discover(tmp_path)


def source(config: Config, role: str) -> str:
    with config.path(role).open("r", encoding="utf-8", newline="") as handle:
        return handle.read()


# -- the measured case -------------------------------------------------------


def test_the_collision_the_gate_reports_is_cleared_by_one_call(tmp_path):
    config = project(tmp_path)
    before = lint(config)
    assert {finding.code for finding in before.findings} == {"id.two-files", "deps.stale"}

    renumber(config, "RK90").save()

    # Exit 0 on the same tree: the whole claim of the task, and the reason a report
    # of the codes above is not enough — nothing could act on it.
    assert lint(Config.discover(tmp_path)).findings == ()


def test_the_line_its_section_and_its_dependents_move_together(tmp_path):
    config = project(tmp_path)
    moved = renumber(config, "RK90", "RK98")
    moved.save()

    assert moved.to == "RK98" and moved.role == "roadmap"
    assert moved.moved == ("RK91",)
    assert moved.section is not None and moved.section.anchor == "RK98"
    roadmap = source(config, "roadmap")
    assert "**RK98**" in roadmap and "**RK90**" not in roadmap
    assert "→ §RK98" in roadmap  # the pointer is the id, so it moves with it (RK27)
    assert "(deps: RK98)" in roadmap
    assert "### §RK98 The branch's design" in source(config, "improvements")
    # The prose under the heading is the author's, and is not touched (L4).
    assert "Because the prose has to travel with the address." in source(
        config, "improvements"
    )


def test_the_ledger_is_never_opened(tmp_path):
    # The id the other branch spent stays spent: renumbering a recorded decision is how a
    # `git log -S` starts returning two unrelated designs.
    config = project(tmp_path)
    before = source(config, "changelog")
    renumber(config, "RK90").save()
    assert source(config, "changelog") == before


def test_the_destination_is_derived_one_past_the_highest(tmp_path):
    config = project(tmp_path)
    assert renumber(config, "RK90").to == "RK92"


# -- the subtree (RK113) -----------------------------------------------------


def test_a_subsection_carries_the_address_it_extends(tmp_path):
    # The measured defect: the heading moved and `§RK90.1` stayed, nested under a heading
    # naming a different task and claiming one the backlog no longer has.
    config = project(tmp_path, **{IMPROVEMENTS: SUBTREE})
    moved = renumber(config, "RK90", "RK98")
    moved.save()

    assert moved.subsections == ("RK98.1",)
    prose = source(config, "improvements")
    assert "### §RK98 The branch's design" in prose
    assert "#### §RK98.1 The measurement under it" in prose
    assert "RK90" not in prose


def test_a_stranger_nested_in_the_subtree_keeps_its_own_address(tmp_path):
    # Bounded by ownership and not by depth: `§RK91` is inside the subtree `find` returns,
    # and it is the other line's address — moving it would be the collision this repairs.
    config = project(tmp_path, **{IMPROVEMENTS: SUBTREE})
    moved = renumber(config, "RK90", "RK98")
    moved.save()

    assert moved.subsections == ("RK98.1",)
    assert "#### §RK91 The dependent's design" in source(config, "improvements")


def test_the_command_names_the_nested_anchors_it_re_addressed(tmp_path, capsys):
    # Named for the same reason the moved deps are: a rewrite the author cannot see is one
    # they cannot check, and this one reaches headings they did not name in the call.
    project(tmp_path, **{IMPROVEMENTS: SUBTREE})
    assert main(["-C", str(tmp_path), "renumber", "RK90", "--to", "RK98"]) == EXIT_OK
    printed = capsys.readouterr().out
    assert "  nested   §RK98.1 (the id's own numbering)" in printed


def test_json_lists_the_nested_anchors(tmp_path, capsys):
    project(tmp_path, **{IMPROVEMENTS: SUBTREE})
    assert main(["-C", str(tmp_path), "renumber", "RK90", "--to", "RK98", "--json"]) == EXIT_OK
    assert json.loads(capsys.readouterr().out)["subsections"] == ["RK98.1"]


# -- the refusals ------------------------------------------------------------


def test_a_destination_anything_already_mentions_is_refused(tmp_path):
    config = project(tmp_path)
    with pytest.raises(IdInUse):
        renumber(config, "RK90", "RK91")
    assert source(config, "roadmap") == BACKLOG
    assert source(config, "improvements") == DESIGN


def test_a_destination_the_ledger_records_is_refused(tmp_path):
    # Including the id being moved away from: it is the number the other line kept.
    config = project(tmp_path)
    with pytest.raises(IdInUse):
        renumber(config, "RK91", "RK90")
    assert source(config, "roadmap") == BACKLOG


def test_a_destination_the_format_cannot_read_is_refused(tmp_path):
    config = project(tmp_path)
    with pytest.raises(NotAnId):
        renumber(config, "RK90", "90")
    assert source(config, "roadmap") == BACKLOG


def test_a_move_to_the_same_id_is_refused_rather_than_written(tmp_path):
    config = project(tmp_path)
    with pytest.raises(SameId):
        renumber(config, "RK90", "RK90")
    assert source(config, "roadmap") == BACKLOG


def test_an_id_no_line_file_holds_is_refused_and_says_where_it_is(tmp_path):
    config = project(tmp_path)
    with pytest.raises(NotOpen) as raised:
        renumber(config, "RK1", "RK99")
    assert "nothing there carries that id" in str(raised.value)


def test_a_line_the_move_would_render_over_the_limit_is_refused(tmp_path):
    # A longer number is two more characters, and the cap is the cap: refused whole, so
    # the section and the dependents are not left addressed to a line that never moved.
    config = project(
        tmp_path, config=CONFIG.replace("[files]", "[limits]\nline = 90\n[files]")
    )
    with pytest.raises(SchemaError):
        renumber(config, "RK90", "RK1000")
    assert source(config, "roadmap") == BACKLOG
    assert source(config, "improvements") == DESIGN


# -- the other line file (RK96) ----------------------------------------------


def test_a_paused_line_is_renumbered_by_the_same_door(tmp_path):
    # A line set aside carries an id like any other, and a collision does not wait for it
    # to come back — `resume` first would be a lie about the state of the work.
    config = project(
        tmp_path,
        config=CONFIG + f'deferred = "{DEFERRED}"\n',
        **{
            DEFERRED: STORE.replace(
                "## Block A — The model\n",
                "## Block A — The model\n\n"
                "- ⏸ **RK80** (deps: —) **a paused line** — Because it waits. → §RK80\n",
            )
        },
    )
    moved = renumber(config, "RK80", "RK99")
    moved.save()
    assert moved.role == "deferred"
    assert "**RK99**" in source(config, "deferred")
    # The roadmap holds no RK80 to move, and the only thing this write does to it is what
    # every other door does (RK8): make a stale annotation true, and name the line.
    assert "RK80" not in source(config, "roadmap")
    assert moved.refreshed == ("RK91",)


def test_a_dep_in_the_store_moves_with_the_line_it_names(tmp_path):
    config = project(
        tmp_path,
        config=CONFIG + f'deferred = "{DEFERRED}"\n',
        **{
            DEFERRED: STORE.replace(
                "## Block A — The model\n",
                "## Block A — The model\n\n"
                "- ⏸ **RK80** (deps: RK90) **a paused line** — Because it waits. → §RK80\n",
            )
        },
    )
    moved = renumber(config, "RK90", "RK99")
    moved.save()
    assert set(moved.moved) == {"RK91", "RK80"}
    assert "(deps: RK99)" in source(config, "deferred")


# -- the command -------------------------------------------------------------


def test_the_command_names_every_dep_it_moved(tmp_path, capsys):
    config = project(tmp_path)
    assert main(["-C", str(tmp_path), "renumber", "RK90", "--to", "RK98"]) == EXIT_OK
    printed = capsys.readouterr().out.splitlines()
    assert printed[0] == f"RK90 → RK98  {ROADMAP}:5"
    assert "**RK98**" in printed[1]
    assert printed[2] == f"  section  §RK98 → {IMPROVEMENTS}:5"
    # Named, because which of two collided ids a dep meant is the one thing this
    # transaction cannot read — and a silent rewrite is one the author cannot check.
    assert printed[3].startswith("  deps     RK91 now name RK98")
    assert printed[-1] == "  event    RK98  Block A  live"
    assert "**RK98**" in source(config, "roadmap")


def test_the_refusal_exits_two_and_writes_nothing(tmp_path, capsys):
    config = project(tmp_path)
    assert main(["-C", str(tmp_path), "renumber", "RK90", "--to", "RK91"]) == EXIT_USAGE
    assert "RK91 already occurs" in capsys.readouterr().err
    assert source(config, "roadmap") == BACKLOG


def test_json_says_which_files_the_transaction_touched(tmp_path, capsys):
    project(tmp_path)
    assert main(["-C", str(tmp_path), "renumber", "RK90", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["id"] == "RK90" and payload["to"] == "RK92"
    assert payload["moved"] == ["RK91"]
    assert payload["section"]["anchor"] == "RK92"
    assert payload["files"] == sorted([ROADMAP, IMPROVEMENTS])
    assert payload["event"] == {"id": "RK92", "block": "A", "stage": "live"}
