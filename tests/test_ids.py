"""Deriving the next id, and the command that prints it (RK4).

Two claims are worth a test each, because both are the *opposite* of the obvious
implementation: the answer is one past the **highest** id and not the first free one,
and it is taken over **every** file including prose, not over the roadmap's task lines.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from roadkeep.cli import EXIT_OK, EXIT_USAGE, main
from roadkeep.config import Config
from roadkeep.ids import highest, id_scanner, next_id, scan

HERE = Path(__file__).resolve().parents[1]
ROADMAP = "docs/ROADMAP.md"


def project(
    tmp_path: Path,
    files: dict[str, str],
    *,
    prefix: str = "RK",
    roles: dict[str, str] | None = None,
    extras: list[str] | None = None,
) -> Config:
    """A throwaway project: a config, and the files it declares."""
    lines = [f'prefix = "{prefix}"']
    if extras:
        # Before the [files] table: a key written after it lands *inside* it, which the
        # config then refuses as files.id_sources — as this helper first did.
        lines.append("id_sources = [" + ", ".join(f'"{e}"' for e in extras) + "]")
    lines.append("[files]")
    for role, rel in (roles or {"roadmap": ROADMAP}).items():
        lines.append(f'{role} = "{rel}"')
    (tmp_path / "roadkeep.toml").write_text("\n".join(lines) + "\n", encoding="utf-8")

    for name, body in files.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    return Config.discover(tmp_path)


# -- this repository ---------------------------------------------------------


def test_the_next_id_here_is_one_past_the_highest():
    config = Config.discover(HERE)
    top = highest(config)
    assert next_id(config) == f"RK{top.number + 1}"
    assert top.number == max(ref.number for ref in scan(config))


def test_the_answer_says_which_file_it_came_from():
    # An answer an agent cannot audit gets verified by reading the file, which is the
    # cost the command exists to remove.
    top = highest(Config.discover(HERE))
    assert top.path.name in {"ROADMAP.md", "CHANGELOG.md", "IMPROVEMENTS.md", "agents.md"}
    assert top.lineno > 0


# -- highest, not first free -------------------------------------------------


def test_a_gap_left_by_a_retired_id_is_not_filled(tmp_path):
    config = project(tmp_path, {ROADMAP: "- RK1 exists\n- RK99 exists\n"})
    # RK2 is free and must stay free: reusing it would make `git log -S RK2` return two
    # unrelated designs.
    assert next_id(config) == "RK100"


def test_a_project_with_no_ids_starts_at_one(tmp_path):
    config = project(tmp_path, {ROADMAP: "# Roadmap\n"})
    assert highest(config) is None
    assert next_id(config) == "RK1"


# -- anywhere, including prose ----------------------------------------------


def test_an_id_mentioned_in_prose_still_reserves_the_number(tmp_path):
    config = project(
        tmp_path,
        {ROADMAP: "- RK4 exists\n", "agents.md": "RK500 replaces this file.\n"},
        extras=["agents.md"],
    )
    assert next_id(config) == "RK501"


def test_a_shipped_id_in_the_changelog_is_not_free(tmp_path):
    config = project(
        tmp_path,
        {ROADMAP: "- RK2 pending\n", "docs/CHANGELOG.md": "- RK7 shipped\n"},
        roles={"roadmap": ROADMAP, "changelog": "docs/CHANGELOG.md"},
    )
    assert next_id(config) == "RK8"


def test_a_source_that_does_not_exist_is_skipped_not_raised(tmp_path):
    config = project(
        tmp_path,
        {ROADMAP: "- RK3\n"},
        roles={"roadmap": ROADMAP, "strategy": "docs/STRATEGY.md"},
    )
    assert config.missing() == ("strategy",)
    assert next_id(config) == "RK4"


# -- what counts as an id ---------------------------------------------------


@pytest.mark.parametrize(
    ("prefix", "text", "expected"),
    [
        ("RK", "RK007 is padded", []),  # padding would be a second spelling of RK7
        ("RK", "RK0", []),
        ("RK", "see RK12.", ["RK12"]),
        ("RK", "(RK3)", ["RK3"]),
        ("RK", "RK12a", []),
        ("T", "T441 and T814", ["T441", "T814"]),
        ("T", "TU12 is another project", []),
        ("T", "UTF-8 encoding", []),
        ("RK", "SH341 belongs to Shio", []),
    ],
)
def test_the_scanner_reads_ids_and_not_lookalikes(prefix, text, expected):
    assert [m.group(0) for m in id_scanner(prefix).finditer(text)] == expected


def test_another_projects_prefix_does_not_leak_into_the_count(tmp_path):
    config = project(tmp_path, {ROADMAP: "- SH341 and RK999\n"}, prefix="SH")
    assert next_id(config) == "SH342"


# -- the command ------------------------------------------------------------


def test_the_command_prints_the_id_and_nothing_else(tmp_path, capsys):
    project(tmp_path, {ROADMAP: "- RK31\n"})
    assert main(["-C", str(tmp_path), "next-id"]) == EXIT_OK
    assert capsys.readouterr().out == "RK32\n"


def test_json_carries_the_provenance(tmp_path, capsys):
    project(
        tmp_path,
        {ROADMAP: "- RK1\n", "agents.md": "line one\nRK31 lives here\n"},
        extras=["agents.md"],
    )
    assert main(["-C", str(tmp_path), "next-id", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["next"] == "RK32"
    assert payload["highest"] == {"id": "RK31", "file": "agents.md", "line": 2}
    assert payload["sources"] == [ROADMAP, "agents.md"]


def test_a_broken_config_exits_two_and_names_every_problem(tmp_path, capsys):
    (tmp_path / "roadkeep.toml").write_text("nonsense = 1\nprefix = 2\n", encoding="utf-8")
    assert main(["-C", str(tmp_path), "next-id"]) == EXIT_USAGE
    err = capsys.readouterr().err
    assert "unknown key 'nonsense'" in err and "prefix must be a string" in err


def test_the_command_reads_the_config_from_a_subdirectory(tmp_path, capsys):
    project(tmp_path, {ROADMAP: "- RK9\n"})
    deep = tmp_path / "src" / "deep"
    deep.mkdir(parents=True)
    assert main(["-C", str(deep), "next-id"]) == EXIT_OK
    assert capsys.readouterr().out == "RK10\n"
