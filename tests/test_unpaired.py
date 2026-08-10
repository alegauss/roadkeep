"""A section may not promise what the line does not (RK36).

RK15 refuses a pointer at a section that does not exist. This is the mirror, and the more
expensive direction: the line is the only thing `pick` reads and the section is deleted on
ship, so a requirement written only into the rationale cannot be picked, cannot be shipped,
and leaves with the section that held it. It happened three times in one session here.

Two properties are what the tests are about. The signal is **structural** — a section was
open and its line was not, with nothing semantic read — and it is a **note**: the check
cannot tell a typo in a paragraph from a smuggled requirement, and a gate that failed every
honest rationale edit would be bypassed inside a week.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from conftest import git, git_init

from roadkeep.cli import EXIT_OK, EXIT_USAGE, main
from roadkeep.config import Config
from roadkeep.history import git_available
from roadkeep.linting import lint

pytestmark = pytest.mark.skipif(not git_available(), reason="git is not on PATH")

ROADMAP = """# Roadmap

## Block A — The model

- 📋 **RK1** (deps: —) **A first symptom** — Because of a reason. → §RK1
- 💭 **RK2** (deps: —) **A second symptom** — Because of another reason. → §RK2
"""

PROSE = """# Design rationale

## §0 — Why this exists

### §0.1 The measured problem

The reading that started it.

## Block A — The model

### §RK1 The first design

The reasoning the first line has no room for.

### §RK2 The second design

The reasoning the second line has no room for.
"""




def repo(tmp_path: Path, committed: bool = True) -> Config:
    git_init(tmp_path)
    write(tmp_path, "roadkeep.toml", 'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\nimprovements = "IMPROVEMENTS.md"\n')
    write(tmp_path, "ROADMAP.md", ROADMAP)
    write(tmp_path, "IMPROVEMENTS.md", PROSE)
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


# -- the signal ---------------------------------------------------------------


def test_a_section_edited_alone_is_reported(tmp_path):
    config = repo(tmp_path)
    write(tmp_path, "IMPROVEMENTS.md", PROSE.replace(
        "The reasoning the first line has no room for.",
        "The reasoning the first line has no room for. And it must also do X.",
    ))
    report = lint(config, since="HEAD")
    (note,) = report.notes
    assert note.code == "section.unpaired" and note.id == "RK1"
    assert note.lineno == 11 and note.file == "IMPROVEMENTS.md"
    assert "only thing `pick` reads" in note.message


def test_a_section_edited_with_its_line_is_not(tmp_path):
    # The pair that means the requirement reached the one place status lives.
    config = repo(tmp_path)
    write(tmp_path, "IMPROVEMENTS.md", PROSE.replace("first design", "first design, restated"))
    write(tmp_path, "ROADMAP.md", ROADMAP.replace("Because of a reason.", "Because of X."))
    assert notes(config) == []


def test_touching_the_line_at_all_is_enough(tmp_path):
    # Not semantic, on purpose (§RK36): a status change is somebody having the line open,
    # and deciding whether the edit was *responsive* would be reading prose (L4).
    config = repo(tmp_path)
    write(tmp_path, "IMPROVEMENTS.md", PROSE.replace("first design", "first design, restated"))
    write(tmp_path, "ROADMAP.md", ROADMAP.replace("📋 **RK1**", "🛠 **RK1**"))
    assert notes(config) == []


def test_prose_that_belongs_to_no_task_is_not_paired_with_anything(tmp_path):
    # §0.1 is this repository's own preface: an anchor no line carries, so there is no
    # line it could have failed to touch.
    config = repo(tmp_path)
    write(tmp_path, "IMPROVEMENTS.md", PROSE.replace(
        "The reading that started it.", "The reading that started it, revised."
    ))
    assert notes(config) == []


def test_a_new_task_and_its_new_section_are_a_pair(tmp_path):
    config = repo(tmp_path)
    write(tmp_path, "ROADMAP.md", ROADMAP + "- 📋 **RK3** (deps: —) **A third symptom** — Because of a third reason. → §RK3\n")
    write(tmp_path, "IMPROVEMENTS.md", PROSE + "\n### §RK3 The third design\n\nThe reasoning it lacks.\n")
    assert notes(config) == []


def test_a_section_deleted_on_ship_is_nothing_to_pair(tmp_path):
    # `ship` removes the line and the section in one transaction, and there is no section
    # left to report — which is why this check never fires on the command that owns it.
    config = repo(tmp_path)
    write(tmp_path, "IMPROVEMENTS.md", PROSE.replace(
        "### §RK2 The second design\n\nThe reasoning the second line has no room for.\n", ""
    ))
    write(tmp_path, "ROADMAP.md", ROADMAP.replace(
        "- 💭 **RK2** (deps: —) **A second symptom** — Because of another reason. → §RK2\n", ""
    ))
    assert notes(config) == []


def test_a_paragraph_removed_from_a_section_still_counts_as_editing_it(tmp_path):
    # A pure deletion carries `+c,0` in the diff: nothing on the new side, and a span that
    # would be empty if it were not widened by one.
    config = repo(tmp_path)
    write(tmp_path, "IMPROVEMENTS.md", PROSE.replace(
        "The reasoning the second line has no room for.\n", ""
    ))
    assert notes(config) == ["section.unpaired RK2"]


# -- the contract -------------------------------------------------------------


def test_the_note_leaves_the_exit_code_alone(tmp_path, capsys):
    repo(tmp_path)
    write(tmp_path, "IMPROVEMENTS.md", PROSE.replace("first design", "first design, restated"))
    assert main(["-C", str(tmp_path), "lint", "--since", "HEAD"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "section.unpaired" in out and "clean" in out


def test_without_since_nothing_is_compared(tmp_path, capsys):
    # `lint` must keep working in a checkout with no history at all, so the check is opt-in
    # and every other one stays exactly as it was.
    repo(tmp_path)
    write(tmp_path, "IMPROVEMENTS.md", PROSE.replace("first design", "first design, restated"))
    assert main(["-C", str(tmp_path), "lint"]) == EXIT_OK
    assert "section.unpaired" not in capsys.readouterr().out


def test_a_repository_with_no_commits_is_not_a_failure(tmp_path, capsys):
    # HEAD is the shipped hook's default, and the initial commit is not the thing to fail.
    repo(tmp_path, committed=False)
    assert main(["-C", str(tmp_path), "lint", "--since", "HEAD"]) == EXIT_OK
    assert "section.unpaired" not in capsys.readouterr().out


def test_a_revision_that_is_not_one_is_a_usage_error(tmp_path, capsys):
    # A typo in a flag the caller passed is the caller's input, so it exits 2 and not 1.
    repo(tmp_path)
    assert main(["-C", str(tmp_path), "lint", "--since", "no-such-rev"]) == EXIT_USAGE
    assert "no history to resolve against" in capsys.readouterr().err


def test_json_carries_the_note(tmp_path, capsys):
    repo(tmp_path)
    write(tmp_path, "IMPROVEMENTS.md", PROSE.replace("first design", "first design, restated"))
    assert main(["-C", str(tmp_path), "lint", "--since", "HEAD", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    (note,) = payload["notes"]
    assert note["code"] == "section.unpaired" and note["line"] == 11
