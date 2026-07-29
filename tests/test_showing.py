"""One task, joined from the files that hold a piece of it (RK12).

The join is the feature, so the tests are about what the join must not do: invent a
field, hide the absence of a section, or turn a dotted name in prose into a missing file.

The three absences are the interesting part. A section can be gone because the task
shipped (correct), because nobody wrote it (a defect `lint` will gate: RK15), or because
the project declares no prose file at all (a configuration, not a fault) — and a report
that spelled all three "none" would be the same as not asking.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from roadkeep.cli import EXIT_OK, EXIT_USAGE, main
from roadkeep.config import Config
from roadkeep.schema import DESIGNED, SHIPPED
from roadkeep.showing import NoSuchTask, paths_in, show

HERE = Path(__file__).resolve().parents[1]

BACKLOG = f"""# Roadmap

## Block A — The model

- {DESIGNED} **RK1** (deps: —) **A first symptom** — Because of a reason. → §RK1
- {DESIGNED} **RK4** (deps: RK1) **A fourth symptom** — Because of another. → §RK4
"""

LEDGER = f"""# Shipped

## Block A — The model

- {SHIPPED} **RK2** **A shipped symptom** — it was done.
"""

RATIONALE = """# Improvements

## Block A — The model

### §RK1 A first design

The reasoning the line has no room for, which cites `docs/specs/first.md` and
`roadkeep.toml`.
"""


def project(
    tmp_path: Path,
    roadmap: str = BACKLOG,
    changelog: str = LEDGER,
    improvements: str | None = RATIONALE,
) -> Config:
    files = 'roadmap = "ROADMAP.md"\nchangelog = "CHANGELOG.md"\n'
    if improvements is not None:
        files += 'improvements = "IMPROVEMENTS.md"\n'
        (tmp_path / "IMPROVEMENTS.md").write_text(improvements, encoding="utf-8")
    (tmp_path / "roadkeep.toml").write_text(
        f'prefix = "RK"\n[files]\n{files}', encoding="utf-8"
    )
    (tmp_path / "ROADMAP.md").write_text(roadmap, encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(changelog, encoding="utf-8")
    return Config.discover(tmp_path)


# -- the join ----------------------------------------------------------------


def test_the_line_and_its_section_arrive_together(tmp_path):
    view = show(project(tmp_path), "RK1")
    assert view.entry.lineno == 5 and not view.shipped
    assert view.task.symptom == "A first symptom"
    assert view.section is not None and view.section.title == "A first design"
    assert view.section_absence == ""


def test_a_shipped_task_is_found_in_the_ledger(tmp_path):
    # "RK2 shipped" is an answer, and a different one from "no such task".
    view = show(project(tmp_path), "RK2")
    assert view.shipped and view.role == "changelog"
    assert view.task.status == SHIPPED and view.task.deps == ()


def test_the_roadmap_is_asked_before_the_ledger(tmp_path):
    # An id in both files is a lint error; until the gate lands, the open line wins,
    # because that is the one a reader can still act on.
    config = project(
        tmp_path,
        roadmap=BACKLOG + f"- {DESIGNED} **RK2** (deps: —) **Twice over** — a reason. → §RK2\n",
    )
    assert show(config, "RK2").role == "roadmap"


def test_an_id_in_neither_file_names_both_files(tmp_path):
    with pytest.raises(NoSuchTask) as caught:
        show(project(tmp_path), "RK99")
    assert "ROADMAP.md" in caught.value.args[0] and "CHANGELOG.md" in caught.value.args[0]


# -- the three absences ------------------------------------------------------


def test_a_section_deleted_on_ship_is_not_reported_as_a_defect(tmp_path):
    view = show(project(tmp_path), "RK2")
    assert view.section is None
    assert "deleted on ship" in view.section_absence


def test_a_pointer_that_resolves_to_nothing_says_so(tmp_path):
    view = show(project(tmp_path), "RK4")
    assert view.section is None
    assert "§RK4 is not in IMPROVEMENTS.md" in view.section_absence
    assert "resolves to nothing" in view.section_absence


def test_a_project_with_no_prose_file_is_a_configuration_not_a_fault(tmp_path):
    view = show(project(tmp_path, improvements=None), "RK1")
    assert view.section is None and view.section_file is None
    assert view.section_absence == "this project declares no improvements file"


# -- the paths its text names ------------------------------------------------


def test_the_paths_come_from_the_line_and_the_section(tmp_path):
    config = project(tmp_path)
    (config.root / "roadkeep.toml").exists()
    named = {p.path: p.exists for p in show(config, "RK1").paths}
    assert named == {"docs/specs/first.md": False, "roadkeep.toml": True}


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        # Really there, so worth reporting even without a slash.
        ("see `roadkeep.toml`", ["roadkeep.toml"]),
        # Slash-shaped: an explicit claim about the repository, missing or not.
        ("see `docs/specs/nope.md`", ["docs/specs/nope.md"]),
        # A dotted name in prose is not a broken file, and reporting it would make the
        # list noise — which is the failure mode of every report nobody reads.
        ("`Config.load` and `Schema.render`", []),
        # A URL is not a path in this repository.
        ("`https://example.com/a.md` and [x](https://example.com/b.md)", []),
        ("a [link](docs/specs/linked.md) counts", ["docs/specs/linked.md"]),
        # Slash-shaped and not this repository: a slash command, and an absolute path
        # that `roadkeep.toml` refuses for the same reason. RK25's line names four.
        ("`/roadkeep:add` and `/etc/hosts`", []),
        ("bare docs/specs/unquoted.md does not", []),
        # Quoted twice, reported once, in order of appearance.
        ("`a/b.md` then `a/b.md`", ["a/b.md"]),
    ],
)
def test_what_counts_as_a_path(text, expected):
    assert [p.path for p in paths_in(text, HERE)] == expected


# -- this repository ---------------------------------------------------------


def test_every_open_task_here_shows_its_own_section():
    config = Config.discover(HERE)
    absent = [
        entry.task.id
        for entry in config.document("roadmap").entries
        if show(config, entry.task.id).section is None
    ]
    # RK15 will make this a gate; until then it is the hand-verification agents.md names.
    assert absent == []


# -- the command -------------------------------------------------------------


def test_the_command_prints_the_line_then_the_prose(tmp_path, capsys):
    project(tmp_path)
    assert main(["-C", str(tmp_path), "show", "RK1"]) == EXIT_OK
    out = capsys.readouterr().out
    assert out.startswith("RK1  Block A  📋  open  ROADMAP.md:5")
    assert "  section  IMPROVEMENTS.md:5  §RK1, 13 words" in out
    assert "path     docs/specs/first.md  (missing)" in out
    assert out.rstrip().endswith("`roadkeep.toml`.")


def test_no_body_keeps_the_pointer_and_drops_the_prose(tmp_path, capsys):
    # `--no-body`, not `--brief`: `brief` is the command that starts a task (RK29), and
    # one word meaning two things is a word an agent guesses wrong.
    project(tmp_path)
    assert main(["-C", str(tmp_path), "show", "RK1", "--no-body"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "IMPROVEMENTS.md:5" in out
    assert "The reasoning the line has no room for" not in out


def test_json_carries_the_section_the_absence_and_the_paths(tmp_path, capsys):
    project(tmp_path)
    assert main(["-C", str(tmp_path), "show", "RK4", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["section"] is None
    assert "resolves to nothing" in payload["section_absence"]
    assert payload["deps"] == ["RK1"] and payload["ref"] == "RK4"
    assert payload["paths"] == []

    assert main(["-C", str(tmp_path), "show", "RK1", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["section"]["words"] == 13
    assert payload["section"]["body"].startswith("The reasoning")


def test_json_no_body_drops_the_body_and_keeps_the_count(tmp_path, capsys):
    project(tmp_path)
    assert main(["-C", str(tmp_path), "show", "RK1", "--no-body", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["section"]["body"] is None and payload["section"]["words"] == 13


def test_an_unknown_id_exits_two(tmp_path, capsys):
    project(tmp_path)
    assert main(["-C", str(tmp_path), "show", "RK99"]) == EXIT_USAGE
    assert "no task RK99" in capsys.readouterr().err
