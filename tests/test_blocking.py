"""The key to a door both halves of this tool were right to lock (RK141).

Measured shipping the first task of a new block: `ship` refused an undeclared block and
wrote nothing, which is correct — naming a block is editorial, and a heading the tool
guesses is a heading nobody looks under. The guard then denied the one-line edit that would
declare it, listing every verb that may write there, none of which adds a heading.

So the test of this module is not that a heading can be written. It is that **neither
refusal had to be weakened**: the label and the title are the author's, and the level, the
separator and the place are the file's own.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from roadkeep.blocking import BlockExists, NotALabel, open_block
from roadkeep.cli import EXIT_OK, EXIT_USAGE, main
from roadkeep.config import Config
from roadkeep.linting import lint
from roadkeep.shipping import ship

ROADMAP = "docs/ROADMAP.md"
CHANGELOG = "docs/CHANGELOG.md"
IMPROVEMENTS = "docs/IMPROVEMENTS.md"

BACKLOG = """# Roadmap

## Block A — The model

- 📋 **RK1** (deps: —) **A first symptom** — Because of a reason. → §RK1

## Block B — Authoring

- 📋 **RK2** (deps: —) **A second symptom** — Because of another. → §RK2

## Non-goals

- **No web UI.** Files and a CLI.
"""

LEDGER = """# Shipped

## Block A — The model

## Block B — Authoring
"""

RATIONALE = """# Improvements

## Block A — The model

### §RK1 A first design

The reasoning the line has no room for.

## Block B — Authoring

### §RK2 A second design

The reasoning for the other one.
"""


def project(
    tmp_path: Path,
    *,
    roadmap: str = BACKLOG,
    changelog: str = LEDGER,
    improvements: str = RATIONALE,
    config: str = "",
) -> Config:
    (tmp_path / "roadkeep.toml").write_text(
        config
        or (
            'prefix = "RK"\n[files]\n'
            f'roadmap = "{ROADMAP}"\nchangelog = "{CHANGELOG}"\n'
            f'improvements = "{IMPROVEMENTS}"\n'
        ),
        encoding="utf-8",
    )
    for name, body in {
        ROADMAP: roadmap,
        CHANGELOG: changelog,
        IMPROVEMENTS: improvements,
    }.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            handle.write(body)
    return Config.discover(tmp_path)


def read(config: Config, name: str) -> str:
    with (config.root / name).open("r", encoding="utf-8", newline="") as handle:
        return handle.read()


# -- the deadlock -------------------------------------------------------------


def test_a_block_no_file_declares_can_be_opened_and_then_shipped_into(tmp_path):
    # The whole task, end to end: the refusal `ship` gives is right, and this is what makes
    # it survivable without the edit the guard denies.
    config = project(tmp_path)
    from roadkeep.document import UnknownBlock

    open_block(config, "C", "Query").save()

    config = Config.discover(tmp_path)
    assert "## Block C — Query" in read(config, CHANGELOG)
    # And the roadmap can now carry a line under it, which `ship` can move across.
    from roadkeep.authoring import add as add_task

    add_task(
        config,
        block="C",
        symptom="A third symptom",
        why="Because of a third reason.",
        section=("A third design", "The reasoning for it."),
    )
    ship(Config.discover(tmp_path), "RK3", why="It works now.").save()
    assert "**RK3**" in read(Config.discover(tmp_path), CHANGELOG)
    assert lint(Config.discover(tmp_path)).clean
    assert UnknownBlock  # imported to name what this test exists to stop happening


def test_the_heading_lands_after_the_last_block_and_never_at_the_end(tmp_path):
    # The roadmap's `## Non-goals` follows the blocks, so appending would file the first
    # task of the new block under a heading that is not a block at all.
    config = project(tmp_path)
    open_block(config, "C", "Query").save()

    lines = read(config, ROADMAP).splitlines()
    assert lines.index("## Block C — Query") < lines.index("## Non-goals")
    assert lines.index("## Block B — Authoring") < lines.index("## Block C — Query")
    # The line that belonged to Block B is still under Block B.
    assert lines.index("- 📋 **RK2** (deps: —) **A second symptom** — Because of another. → §RK2") < lines.index(
        "## Block C — Query"
    )


def test_every_file_organised_by_blocks_gets_it(tmp_path):
    config = project(tmp_path)
    opened = open_block(config, "C", "Query")
    opened.save()

    assert set(opened.documents) == {"roadmap", "changelog", "improvements"}
    for name in (ROADMAP, CHANGELOG, IMPROVEMENTS):
        assert "## Block C — Query" in read(config, name)


def test_a_file_that_is_not_organised_by_blocks_is_named_and_left_alone(tmp_path):
    # A heading here would be the first of its kind, which is a decision about the file's
    # shape rather than about a block — and a file skipped in silence is one the author
    # discovers was skipped by the next command that refuses on it.
    config = project(tmp_path, improvements="# Improvements\n\n### §0.1 A preface\n\nProse.\n")
    opened = open_block(config, "C", "Query")
    opened.save()

    assert set(opened.documents) == {"roadmap", "changelog"}
    assert opened.skipped == ((IMPROVEMENTS, "declares no block, so there is none to open beside"),)
    assert "Block C" not in read(config, IMPROVEMENTS)


# -- what is derived, per file ------------------------------------------------


def test_the_level_and_the_separator_are_the_files_own(tmp_path):
    # A project writing `### Fase 2 - Execução` gets one more of those: a tool answering
    # with its own punctuation writes a second convention into a file that has one.
    config = project(
        tmp_path,
        roadmap="# Roadmap\n\n### Fase 1 - Começo\n\n### Fase 2 - Execução\n",
        config='prefix = "RK"\n[headings]\nword = "Fase"\n[files]\n'
        f'roadmap = "{ROADMAP}"\nchangelog = "{CHANGELOG}"\n',
        changelog="# Shipped\n\n### Fase 1 - Começo\n",
    )
    opened = open_block(config, "3", "Entrega")
    opened.save()

    assert opened.rendered["roadmap"] == "### Fase 3 - Entrega"
    assert "### Fase 3 - Entrega" in read(config, ROADMAP)


def test_a_heading_with_no_separator_still_gets_one(tmp_path):
    config = project(
        tmp_path,
        roadmap="# Roadmap\n\n## Block A The model\n",
        changelog="# Shipped\n\n## Block A The model\n",
        improvements="# Improvements\n\n## Block A The model\n",
    )
    opened = open_block(config, "B", "Authoring")
    opened.save()
    assert opened.rendered["roadmap"] == "## Block B Authoring"


def test_the_heading_gets_the_blank_lines_a_heading_needs(tmp_path):
    config = project(tmp_path)
    open_block(config, "C", "Query").save()
    lines = read(config, CHANGELOG).splitlines()
    at = lines.index("## Block C — Query")
    assert lines[at - 1] == "" and lines[at + 1] == ""


def test_the_file_still_round_trips_and_lints_clean(tmp_path):
    config = project(tmp_path)
    open_block(config, "C", "Query").save()
    after = Config.discover(tmp_path)
    assert after.document("roadmap").non_canonical == ()
    assert lint(after).clean


# -- the refusals -------------------------------------------------------------


def test_a_label_the_format_cannot_read_is_refused(tmp_path):
    config = project(tmp_path)
    with pytest.raises(NotALabel):
        open_block(config, "a label with spaces", "Query")
    assert read(config, ROADMAP) == BACKLOG


def test_an_empty_title_is_refused_rather_than_written(tmp_path):
    config = project(tmp_path)
    with pytest.raises(NotALabel):
        open_block(config, "C", "   ")
    assert read(config, ROADMAP) == BACKLOG


def test_a_label_every_file_already_declares_is_refused(tmp_path):
    # A command that exits 0 having written nothing teaches that it wrote something.
    config = project(tmp_path)
    with pytest.raises(BlockExists) as caught:
        open_block(config, "B", "Authoring again")
    assert ROADMAP in str(caught.value)
    assert read(config, ROADMAP) == BACKLOG


def test_a_label_only_one_file_lacks_is_written_only_there(tmp_path):
    # The half-declared state the pair used to leave: `add` works and `ship` fails on one
    # label, which is the deadlock again with one more step in it.
    config = project(tmp_path, changelog="# Shipped\n\n## Block A — The model\n")
    opened = open_block(config, "B", "Authoring")
    opened.save()

    assert set(opened.documents) == {"changelog"}
    assert "## Block B — Authoring" in read(config, CHANGELOG)
    assert read(config, ROADMAP) == BACKLOG


# -- the command --------------------------------------------------------------


def test_the_command_names_every_file_it_wrote(tmp_path, capsys):
    project(tmp_path)
    assert main(["-C", str(tmp_path), "block", "add", "C", "--title", "Query"]) == EXIT_OK
    printed = capsys.readouterr().out
    assert printed.startswith("Block C declared: Query")
    assert f"{CHANGELOG}   :7  ## Block C — Query" in printed


def test_the_command_refuses_with_two_and_writes_nothing(tmp_path, capsys):
    config = project(tmp_path)
    code = main(["-C", str(tmp_path), "block", "add", "B", "--title", "Again"])
    assert code == EXIT_USAGE
    assert "already declared" in capsys.readouterr().err
    assert read(config, ROADMAP) == BACKLOG


def test_json_says_what_was_written_and_what_was_not(tmp_path, capsys):
    project(tmp_path, improvements="# Improvements\n\n### §0.1 A preface\n\nProse.\n")
    code = main(
        ["-C", str(tmp_path), "block", "add", "C", "--title", "Query", "--json"]
    )
    assert code == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["label"] == "C" and payload["title"] == "Query"
    assert [w["role"] for w in payload["written"]] == ["roadmap", "changelog"]
    assert payload["skipped"][0]["file"] == IMPROVEMENTS
