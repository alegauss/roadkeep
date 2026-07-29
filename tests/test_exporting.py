"""The backlog projected onto another file, without a second author (RK39).

Two properties carry this task, and both are the kind that rot quietly:

* **Idempotence.** The same input must yield the same bytes, or every refresh is a diff and
  the diff stops being readable exactly when it matters. That is also why no timestamp is
  emitted — the test that would catch a regression is the one that runs it twice.
* **No new sentence.** Task lines appear verbatim and block titles come from the headings,
  so `lint` still proves the artefact and L4 holds. A projection that summarised would be
  a generator, and a generator would reintroduce the drift the tool exists to stop.

The third is structural: the block is replaced *between markers the author put there*, and
everything outside them survives byte for byte, endings included.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from roadkeep.cli import EXIT_OK, EXIT_USAGE, main
from roadkeep.config import Config
from roadkeep.exporting import BEGIN, END, NoMarkers, project, splice
from roadkeep.schema import DESIGNED, RETIRED, SHIPPED
from roadkeep.shipping import retire

HERE = Path(__file__).resolve().parents[1]

ROADMAP = f"""# Roadmap

## Block A — The model (a task is data first)

- {DESIGNED} **RK1** (deps: —) **A first symptom** — Because of a reason. → §RK1
- {DESIGNED} **RK4** (deps: RK1) **A fourth symptom** — Because of another. → §RK4

## Block B — Authoring
"""

LEDGER = f"""# Shipped

## Block A — The model

- {SHIPPED} **RK2** **A shipped symptom** — it was done.

## Block B — Authoring
"""

README = f"""# A project

Prose the author owns.

{BEGIN}
stale text nobody re-derived
{END}

More prose the author owns.
"""


def project_files(tmp_path: Path, roadmap: str = ROADMAP, readme: str = README) -> Config:
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\nchangelog = "CHANGELOG.md"\n',
        encoding="utf-8",
    )
    for name, body in {
        "ROADMAP.md": roadmap,
        "CHANGELOG.md": LEDGER,
        "README.md": readme,
    }.items():
        with (tmp_path / name).open("w", encoding="utf-8", newline="") as handle:
            handle.write(body)
    return Config.discover(tmp_path)


# -- the projection -----------------------------------------------------------


def test_the_counts_are_per_block_and_from_both_files(tmp_path):
    projection = project(project_files(tmp_path))
    assert [(row.label, row.open, row.shipped) for row in projection.rows] == [
        ("A", 2, 1),
        ("B", 0, 0),
    ]
    assert (projection.totals.open, projection.totals.shipped) == (2, 1)


def test_a_block_title_comes_from_the_heading_that_declares_it(tmp_path):
    # Verbatim, and the roadmap's wording wins: the ledger's heading for the same block is
    # often the shorter one, and inventing a third would be authoring.
    projection = project(project_files(tmp_path))
    assert projection.rows[0].title == "A — The model (a task is data first)"


def test_the_next_ready_line_is_the_file_s_own_bytes(tmp_path):
    config = project_files(tmp_path)
    projection = project(config)
    assert projection.next_ready.task.id == "RK1"
    assert projection.next_ready.raw in projection.markdown()


def test_nothing_ready_projects_no_next(tmp_path):
    roadmap = ROADMAP.replace("(deps: —)", "(deps: RK9)")
    projection = project(project_files(tmp_path, roadmap=roadmap))
    assert projection.next_ready is None
    assert "Next ready" not in projection.markdown()
    assert projection.payload()["next"] is None


def test_the_retired_column_appears_only_once_something_is_retired(tmp_path):
    config = project_files(tmp_path)
    assert "Retired" not in project(config).markdown()

    retire(config, "RK4", reason="the premise stopped being true.").save()
    reopened = Config.discover(tmp_path)
    markdown = project(reopened).markdown()
    assert "Retired" in markdown
    # The count is per block and per marker, so a retirement is not counted as shipped.
    assert project(reopened).rows[0].retired == 1
    assert project(reopened).rows[0].shipped == 1


# -- idempotence --------------------------------------------------------------


def test_the_same_input_yields_the_same_bytes(tmp_path):
    config = project_files(tmp_path)
    assert project(config).markdown() == project(config).markdown()
    assert project(config).json() == project(config).json()


def test_the_payload_carries_no_stamp_that_would_diff_every_run(tmp_path):
    payload = project(project_files(tmp_path)).payload()
    assert not [key for key in payload if "date" in key or "time" in key]
    assert "generated" not in json.dumps(payload)


def test_splicing_twice_changes_nothing_the_second_time(tmp_path):
    config = project_files(tmp_path)
    body = project(config).markdown()
    once = splice(README, body, "README.md")
    assert splice(once, body, "README.md") == once


def test_the_command_writes_once_and_then_says_it_is_current(tmp_path, capsys):
    project_files(tmp_path)
    assert main(["-C", str(tmp_path), "export", "--readme"]) == EXIT_OK
    assert "refreshed" in capsys.readouterr().out
    written = (tmp_path / "README.md").read_text(encoding="utf-8")

    assert main(["-C", str(tmp_path), "export", "--readme"]) == EXIT_OK
    assert "already current" in capsys.readouterr().out
    assert (tmp_path / "README.md").read_text(encoding="utf-8") == written


# -- what is outside the markers is the author's ------------------------------


def test_everything_outside_the_markers_survives(tmp_path):
    config = project_files(tmp_path)
    spliced = splice(README, project(config).markdown(), "README.md")
    assert spliced.startswith("# A project\n\nProse the author owns.\n")
    assert spliced.endswith("More prose the author owns.\n")
    assert "stale text nobody re-derived" not in spliced


def test_the_files_line_endings_are_kept(tmp_path):
    crlf = README.replace("\n", "\r\n")
    spliced = splice(crlf, "one line", "README.md")
    assert "\n" not in spliced.replace("\r\n", "")


def test_a_file_with_no_markers_is_refused_with_the_lines_to_paste(tmp_path):
    with pytest.raises(NoMarkers) as caught:
        splice("# A project\n\nNo markers here.\n", "body", "README.md")
    message = caught.value.args[0]
    assert BEGIN in message and END in message and "no begin marker" in message


def test_markers_in_the_wrong_order_are_refused():
    with pytest.raises(NoMarkers):
        splice(f"{END}\n{BEGIN}\n", "body", "README.md")


def test_the_command_refuses_a_readme_without_markers(tmp_path, capsys):
    project_files(tmp_path, readme="# A project\n\nNo markers.\n")
    assert main(["-C", str(tmp_path), "export", "--readme"]) == EXIT_USAGE
    assert BEGIN in capsys.readouterr().err
    assert (tmp_path / "README.md").read_text(encoding="utf-8") == "# A project\n\nNo markers.\n"


# -- the two shapes on the command line --------------------------------------


def test_the_default_prints_the_markdown_and_writes_nothing(tmp_path, capsys):
    project_files(tmp_path)
    before = (tmp_path / "README.md").read_text(encoding="utf-8")
    assert main(["-C", str(tmp_path), "export"]) == EXIT_OK
    out = capsys.readouterr().out
    assert out.startswith("<!-- generated by")
    assert "| Block | Open | Shipped |" in out
    assert (tmp_path / "README.md").read_text(encoding="utf-8") == before


def test_json_carries_the_lines_and_the_totals(tmp_path, capsys):
    project_files(tmp_path)
    assert main(["-C", str(tmp_path), "export", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["totals"] == {"open": 2, "shipped": 1, "retired": 0}
    assert [task["id"] for task in payload["open"]] == ["RK1", "RK4"]
    assert payload["ledger"][0] == {
        "id": "RK2",
        "status": SHIPPED,
        "block": "A",
        "symptom": "A shipped symptom",
        "why": "it was done.",
        "deps": [],
        "ref": None,
        "line": 5,
    }
    assert payload["next"] == "RK1"


# -- this repository ----------------------------------------------------------


def test_this_repositorys_projection_matches_its_own_files():
    config = Config.discover(HERE)
    projection = project(config)
    census_open = len(config.document("roadmap").entries)
    assert projection.totals.open == census_open
    # Every open line appears in the payload exactly as the file spells it.
    payload_ids = [task["id"] for task in projection.payload()["open"]]
    assert payload_ids == [e.task.id for e in config.document("roadmap").entries]


def test_this_repositorys_readme_is_current():
    # The artefact proves the format: if this fails, run `roadkeep export --readme`.
    config = Config.discover(HERE)
    readme = (HERE / "README.md").read_text(encoding="utf-8", errors="strict")
    assert splice(readme, project(config).markdown(), "README.md") == readme
