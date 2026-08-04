"""A block emptying, said where a later reader can see it (RK269).

`ship` computes it — `event T282 Block AI empty` — and says it once, to a console. Nothing
records it, and `lint` reported a clean tree either way. Measured in a repository keeping a
per-block index beside its ledger: two ships emptied a block and two adds reopened it across
four commits, every row was flipped by hand, and every time `lint` passed on the wrong one.

Two properties are what the tests are about. It is a **transition** and not a state — `lint
--since HEAD` is what the shipped pre-commit hook runs, and "Block A is empty" is true of this
repository forever — and it is a **note**, because emptying a block is what finishing one looks
like and a gate that failed the commit finishing a block would be the wrong gate entirely.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from roadkeep.cli import EXIT_OK, main
from roadkeep.config import Config
from roadkeep.history import git_available
from roadkeep.linting import lint

pytestmark = pytest.mark.skipif(not git_available(), reason="git is not on PATH")

#: Two blocks, so a run can say something about one of them and nothing about the other.
ROADMAP = """# Roadmap

## Block A — The model

- 📋 **RK1** (deps: —) **A first symptom** — Because of a reason.

## Block B — Authoring

- 📋 **RK2** (deps: —) **A second symptom** — Because of another reason.
- 📋 **RK3** (deps: —) **A third symptom** — Because of a third reason.
"""

LEDGER = """# Changelog

## Block A — The model

## Block B — Authoring
"""

#: `ref = false` (RK52) so the fixture is only about blocks: a project with no prose file is a
#: shape roadkeep supports, and carrying sections here would make every deletion below a
#: rationale edit as well — which is the *other* `since` note, and not the one under test.
CONFIG = (
    'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\nchangelog = "CHANGELOG.md"\n'
    "[rules.roadmap]\nref = false\n"
)


def git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    ).stdout


def repo(tmp_path: Path, committed: bool = True) -> Config:
    git(tmp_path, "init", "--quiet")
    git(tmp_path, "config", "user.email", "test@example.invalid")
    git(tmp_path, "config", "user.name", "Test")
    git(tmp_path, "config", "commit.gpgsign", "false")
    write(tmp_path, "roadkeep.toml", CONFIG)
    write(tmp_path, "ROADMAP.md", ROADMAP)
    write(tmp_path, "CHANGELOG.md", LEDGER)
    if committed:
        git(tmp_path, "add", "-A")
        git(tmp_path, "commit", "--quiet", "-m", "chore: bootstrap")
    return Config.discover(tmp_path)


def write(root: Path, name: str, body: str) -> None:
    with (root / name).open("w", encoding="utf-8", newline="") as handle:
        handle.write(body)


def notes(config: Config) -> list[str]:
    report = lint(config, since="HEAD")
    assert report.clean, [str(f) for f in report.findings]
    return [f"{note.code} {note.id}" for note in report.notes]


# -- the transition -----------------------------------------------------------


def test_a_block_this_change_emptied_is_reported(tmp_path):
    config = repo(tmp_path)
    write(tmp_path, "ROADMAP.md", ROADMAP.replace(
        "- 📋 **RK1** (deps: —) **A first symptom** — Because of a reason.\n", ""
    ))
    report = lint(config, since="HEAD")
    (note,) = report.notes
    assert note.code == "block.emptied" and note.id == "A"
    # At the heading, because the heading is what stayed: the line it is about is gone.
    assert note.lineno == 3 and note.file == "ROADMAP.md"
    assert "held 1 open line(s) at HEAD and holds none now" in note.message


def test_a_block_this_change_reopened_is_the_other_direction(tmp_path):
    config = repo(tmp_path)
    git(tmp_path, "rm", "--quiet", "ROADMAP.md")
    write(tmp_path, "ROADMAP.md", ROADMAP.replace(
        "- 📋 **RK1** (deps: —) **A first symptom** — Because of a reason.\n", ""
    ))
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "--quiet", "-m", "feat: finish A")
    write(tmp_path, "ROADMAP.md", ROADMAP)
    report = lint(config, since="HEAD")
    (note,) = report.notes
    assert note.code == "block.reopened" and note.id == "A"
    assert "holds 1 now" in note.message


def test_a_block_that_only_lost_one_of_its_lines_says_nothing(tmp_path):
    # The threshold is the transition and not the count: Block B keeps an open line, so a
    # projection stating which blocks are active has no row to move.
    config = repo(tmp_path)
    write(tmp_path, "ROADMAP.md", ROADMAP.replace(
        "- 📋 **RK3** (deps: —) **A third symptom** — Because of a third reason.\n", ""
    ))
    assert notes(config) == []


def test_a_block_that_was_already_empty_is_not_news(tmp_path):
    """The reason this rides `since` at all. `lint` with no revision would say it on every run
    for as long as the heading exists, and a line printed forever is a line nobody reads."""
    config = repo(tmp_path)
    write(tmp_path, "ROADMAP.md", ROADMAP.replace(
        "- 📋 **RK1** (deps: —) **A first symptom** — Because of a reason.\n", ""
    ))
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "--quiet", "-m", "feat: finish A")
    write(tmp_path, "CHANGELOG.md", LEDGER + "\n")
    assert notes(config) == []


def test_nothing_is_said_about_a_block_only_one_of_the_two_trees_declares(tmp_path):
    # A heading that arrived is `block add`'s own event and one that left is `block drop`;
    # neither is a block changing state, and reporting them would make every `block add`
    # print a row nobody has to move.
    config = repo(tmp_path)
    write(tmp_path, "ROADMAP.md", ROADMAP + "\n## Block C — Query\n")
    write(tmp_path, "CHANGELOG.md", LEDGER + "\n## Block C — Query\n")
    assert notes(config) == []


# -- what it is, and is not ---------------------------------------------------


def test_the_note_leaves_the_exit_code_alone(tmp_path, capsys):
    """Emptying a block is what finishing one looks like: this is the commit the author meant
    to make, and the note is a sentence read at the moment they make it."""
    repo(tmp_path)
    write(tmp_path, "ROADMAP.md", ROADMAP.replace(
        "- 📋 **RK1** (deps: —) **A first symptom** — Because of a reason.\n", ""
    ))
    assert main(["-C", str(tmp_path), "lint", "--since", "HEAD"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "block.emptied" in out and "clean" in out


def test_without_since_nothing_is_compared(tmp_path, capsys):
    repo(tmp_path)
    write(tmp_path, "ROADMAP.md", ROADMAP.replace(
        "- 📋 **RK1** (deps: —) **A first symptom** — Because of a reason.\n", ""
    ))
    assert main(["-C", str(tmp_path), "lint"]) == EXIT_OK
    assert "block.emptied" not in capsys.readouterr().out


def test_a_repository_with_no_commits_is_not_a_failure(tmp_path, capsys):
    repo(tmp_path, committed=False)
    assert main(["-C", str(tmp_path), "lint", "--since", "HEAD"]) == EXIT_OK
    assert "block.emptied" not in capsys.readouterr().out


def test_json_carries_the_note(tmp_path, capsys):
    repo(tmp_path)
    write(tmp_path, "ROADMAP.md", ROADMAP.replace(
        "- 📋 **RK1** (deps: —) **A first symptom** — Because of a reason.\n", ""
    ))
    assert main(["-C", str(tmp_path), "lint", "--since", "HEAD", "--json"]) == EXIT_OK
    (note,) = json.loads(capsys.readouterr().out)["notes"]
    assert note["code"] == "block.emptied" and note["id"] == "A"


def test_the_note_and_the_ship_event_answer_the_same_question(tmp_path, capsys):
    """The one thing that must not drift: `ship` prints `Block A empty` from
    `not roadmap.block(label)`, and this reads the same expression. Two answers to whether a
    block is empty is the defect RK269 names, with the arrow reversed.
    """
    repo(tmp_path)
    assert main(["-C", str(tmp_path), "ship", "RK1", "--why", "The first outcome."]) == EXIT_OK
    assert "event    RK1  Block A  empty" in capsys.readouterr().out
    assert main(["-C", str(tmp_path), "lint", "--since", "HEAD"]) == EXIT_OK
    assert "block.emptied" in capsys.readouterr().out
