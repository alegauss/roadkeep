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
from roadkeep.config import Config, ConfigError
from roadkeep.ids import carried, derivation, highest, id_scanner, next_id, scan
from roadkeep.kernel.schema import Schema

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


def test_the_next_id_here_is_one_past_the_highest(governed):
    config = Config.discover(governed)
    top = highest(config)
    assert next_id(config) == f"RK{top.number + 1}"
    assert top.number == max(ref.number for ref in scan(config))


def test_the_answer_says_which_file_it_came_from(governed):
    # An answer an agent cannot audit gets verified by reading the file, which is the
    # cost the command exists to remove.
    top = highest(Config.discover(governed))
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
    scanner = id_scanner(Schema(prefixes=(prefix,)))
    assert [m.group(0) for m in scanner.finditer(text)] == expected


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


# -- a backlog numbered by track (RK74) -------------------------------------


def multi(tmp_path: Path, body: str) -> Path:
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = ["C", "L", "V"]\n[files]\nroadmap = "docs/ROADMAP.md"\n', encoding="utf-8"
    )
    target = tmp_path / ROADMAP
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body, encoding="utf-8")
    return target


def test_each_track_counts_on_its_own(tmp_path):
    # Two tracks sharing a counter are two tracks that renumber each other: cursarei's
    # C## reaching 45 must not push V## past its 05.
    config = Config.discover(multi(tmp_path, "- C45 and C44\n- V5\n- L12\n"))
    assert next_id(config, "C") == "C46"
    assert next_id(config, "V") == "V6"
    assert next_id(config, "L") == "L13"


def test_the_first_declared_family_is_what_a_caller_naming_none_gets(tmp_path):
    config = Config.discover(multi(tmp_path, "- C45\n- V5\n"))
    assert next_id(config) == next_id(config, "C") == "C46"


def test_a_track_with_no_ids_yet_starts_at_one(tmp_path):
    # Not one past the highest *anywhere*, which would open a track at 46.
    config = Config.discover(multi(tmp_path, "- C45\n"))
    assert next_id(config, "V") == "V1"


def test_an_id_is_never_minted_outside_the_declared_families(tmp_path):
    config = Config.discover(multi(tmp_path, "- C45\n"))
    with pytest.raises(ValueError, match="not a family this project numbers"):
        next_id(config, "G")


def test_the_scan_reads_every_family_and_says_which_matched(tmp_path):
    config = Config.discover(multi(tmp_path, "- C45 waits on V5\n"))
    found = {ref.id: ref.family for ref in scan(config)}
    assert found == {"C45": "C", "V5": "V"}


# -- the shape the project declared (RK106) ---------------------------------


def shaped(tmp_path: Path, prefix: str, table: str, body: str) -> Config:
    (tmp_path / "roadkeep.toml").write_text(
        f'prefix = "{prefix}"\n[ids]\n{table}[files]\nroadmap = "{ROADMAP}"\n',
        encoding="utf-8",
    )
    target = tmp_path / ROADMAP
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body, encoding="utf-8")
    return Config.discover(tmp_path)


def test_a_padded_project_mints_a_padded_id(tmp_path):
    # A counter that answered `D10` here and `D9` one line earlier would be handing back
    # an id this project's own gate refuses.
    assert next_id(shaped(tmp_path, "D", "pad = 2\n", "- D01 and D09\n")) == "D10"


def test_a_padded_project_with_no_ids_yet_opens_at_the_declared_width(tmp_path):
    assert next_id(shaped(tmp_path, "D", "pad = 2\n", "# Roadmap\n")) == "D01"


def test_the_padding_is_only_the_spelling_and_never_the_count(tmp_path):
    config = shaped(tmp_path, "D", "pad = 2\n", "- D09\n")
    assert next_id(config) == "D10"
    assert highest(config).number == 9


def test_the_scan_reads_a_split_id_the_project_declares(tmp_path):
    # T24b is the number the next id has to clear. Read as no id at all it would be
    # invisible to the maximum, and 25 would be minted on a backlog that already spent 24.
    config = shaped(tmp_path, "T", "suffix = true\n", "- T24b is the split\n")
    assert [(ref.id, ref.number) for ref in scan(config)] == [("T24b", 24)]
    assert next_id(config) == "T25"


def test_a_sub_letter_nobody_declared_is_still_not_an_id(tmp_path):
    config = shaped(tmp_path, "T", "", "- T24b is the split\n")
    assert scan(config) == ()


def test_a_single_family_scanner_is_the_pattern_it_always_was():
    # The list is what a backlog numbered by track needs; a project that numbers one
    # reads the same regex it always did, and `prefix = "RK"` stays a string in the file.
    # The groups are named because the schema joins them now (RK109) — one fragment, so
    # the scan cannot spell an id the gate refuses.
    assert (
        id_scanner(Schema()).pattern
        == r"\b(?P<family>RK)(?P<number>[1-9][0-9]*)(?P<sub>)\b"
    )


def test_the_scanner_is_the_schemas_own_join_and_not_a_second_copy():
    for schema in (Schema(), Schema(prefixes=("D",), id_pad=2), Schema(id_suffix=True)):
        assert id_scanner(schema).pattern == rf"\b{schema.id_groups}\b"


# -- the id a sentence spent (RK431) -----------------------------------------


def carrying(tmp_path: Path, ledger: str, prose: str = "") -> Config:
    """A project whose ledger carries lines and whose `agents.md` only mentions ids."""
    return project(
        tmp_path,
        {ROADMAP: "## Block A — The model\n", "docs/CHANGELOG.md": ledger, "agents.md": prose},
        roles={"roadmap": ROADMAP, "changelog": "docs/CHANGELOG.md"},
        extras=["agents.md"],
    )


ENTRY = "- ✅ **RK7** **A symptom** — Because it was done.\n"


def test_an_id_only_a_sentence_names_is_reported_when_the_next_one_steps_over_it(tmp_path):
    """SH614, reproduced. The ledger entry promised an id and `add` handed out the next.

    Nothing malfunctions: the entry was written into a file the scan reads, so the highest
    id in the corpus was the one the sentence promised to a task that did not exist yet.
    The deriver cannot tell a declared id from a mentioned one, and every id starts as a
    mention — so the derivation says which this was instead of being silent about it.
    """
    config = carrying(tmp_path, "## Block A — The model\n\n" + ENTRY, "Filed as RK8.\n")
    answer = derivation(config)
    assert answer.id == "RK9"
    assert answer.promise is not None
    assert (answer.promise.id, answer.promise.derived) == ("RK8", "RK9")
    assert answer.promise.where == "agents.md:1"
    assert "no line carries it" in answer.promise.sentence


def test_a_highest_id_some_line_carries_is_no_promise_at_all(tmp_path):
    # The overwhelming majority of derivations, and they must stay silent: RK7 is an
    # entry, so RK8 steps over nothing and there is nothing to say about it.
    config = carrying(tmp_path, "## Block A — The model\n\n" + ENTRY)
    answer = derivation(config)
    assert answer.id == "RK8" and answer.promise is None


def test_a_paused_line_carries_its_id_as_much_as_a_shipped_one_does(tmp_path):
    # The deferred store holds real lines (RK92): an id set aside is occupied, and
    # reporting it as a promise would send the author to correct a sentence nobody wrote.
    config = project(
        tmp_path,
        {
            ROADMAP: "## Block A — The model\n",
            "docs/CHANGELOG.md": "# Shipped\n",
            "docs/DEFERRED.md": "## Block A — The model\n\n"
            "- ⏸ **RK7** (deps: —) **A symptom** — set aside: waiting. → §RK7\n",
        },
        roles={
            "roadmap": ROADMAP,
            "changelog": "docs/CHANGELOG.md",
            "deferred": "docs/DEFERRED.md",
        },
    )
    assert derivation(config).promise is None


def test_the_answer_carries_the_promise_and_the_bare_form_keeps_its_one_line(tmp_path, capsys):
    config = carrying(tmp_path, "## Block A — The model\n\n" + ENTRY, "Filed as RK8.\n")
    assert main(["-C", str(config.root), "next-id"]) == EXIT_OK
    out = capsys.readouterr()
    # stdout stays exactly the id: this command is captured in a shell, and a second line
    # in that capture is a broken id.
    assert out.out == "RK9\n"
    assert "RK8 is named at agents.md:1" in out.err

    assert main(["-C", str(config.root), "next-id", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["next"] == "RK9"
    # Beside `highest`, which says which occurrence set the maximum, and never folded
    # into it: this says the occurrence was a sentence rather than a line.
    assert payload["highest"]["id"] == "RK8"
    assert payload["promise"]["id"] == "RK8" and payload["promise"]["derived"] == "RK9"


def test_nothing_is_refused_and_nothing_is_reserved(tmp_path, capsys):
    """Which of the two ids the author wanted is a judgement about a sentence (L4).

    So the `add` succeeds, the derived id is the derived id, and what is reported is that
    a sentence somewhere else has stopped being true.
    """
    config = carrying(tmp_path, "## Block A — The model\n\n" + ENTRY, "Filed as RK8.\n")
    argv = ["-C", str(config.root), "add", "--block", "A",
            "--symptom", "A symptom that does not work", "--why", "Because of a reason."]
    assert main(argv) == EXIT_OK
    out = capsys.readouterr().out
    assert out.startswith("- 📋 **RK9**")
    assert "promise  RK8 is named at agents.md:1" in out
    # And the same derivation twice does not report it twice differently: RK9 is now a
    # line, so the next one steps over nothing.
    assert derivation(Config.discover(config.root)).promise is None


# -- a reserved id is not a spent id (RK1031) --------------------------------


def reserving(tmp_path: Path, *tokens: str) -> Config:
    """A project that speaks for an address without writing it as a line."""
    listed = ", ".join(f'"{token}"' for token in tokens)
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "SH"\n'
        f"reserved_ids = [\n    {listed},\n]\n"
        '[files]\nroadmap = "ROADMAP.md"\nchangelog = "CHANGELOG.md"\n'
        'improvements = "IMPROVEMENTS.md"\n',
        encoding="utf-8",
    )
    for name, body in (
        ("ROADMAP.md", "# Roadmap\n\n## Block A — The model\n"),
        ("CHANGELOG.md", "# Changelog\n\n## Block A — The model\n"),
        ("IMPROVEMENTS.md", "# Improvements\n\n## Block A — The model\n"),
    ):
        (tmp_path / name).write_text(body, encoding="utf-8")
    return Config.discover(tmp_path)


def test_a_reserved_id_is_taken_and_the_deriver_steps_past_it(tmp_path):
    """Shio reserves one id per epic — `SH25`, `SH62` — each owning a sub-range whose
    sub-tasks ship under their own numbers. The epic id is never a line, so a scan over the
    files alone would hand the next `add` an address the project has spoken for."""
    config = reserving(tmp_path, "SH25", "SH62")
    assert next_id(config) == "SH63"


def test_a_reservation_names_the_line_of_the_config_that_declares_it(tmp_path):
    """A refusal names `file:line` and a reader clicks it, so `roadkeep.toml:0` would be the
    one address in this tool that opens nothing."""
    config = reserving(tmp_path, "SH25", "SH62")
    found = {ref.id: ref for ref in scan(config) if ref.id in config.reserved}
    assert found["SH25"].lineno == 3 and found["SH62"].lineno == 3
    assert found["SH25"].path.name == "roadkeep.toml"


def test_a_design_naming_a_reservation_is_not_a_promise(tmp_path):
    """The gate that could never be clean: ten findings on Shio, none actionable, and the
    advice each gave — spell the example outside this project's prefix — refused by the
    convention it argued with. `carried` holds them because they *are* taken."""
    config = reserving(tmp_path, "SH25")
    assert "SH25" in carried(config)


def test_an_id_nothing_reserves_still_fails(tmp_path):
    """The check that this is a declaration and not a suppression: a token off the list is
    exactly what it was, which is what keeps a typo a typo."""
    config = reserving(tmp_path, "SH25")
    assert "SH900" not in carried(config)


def test_a_token_that_is_not_an_id_is_refused_at_the_config(tmp_path):
    """A word that is not an id would sit on the list looking like a reservation and reserve
    nothing — the silent state this declaration exists to replace, wearing its name."""
    with pytest.raises(ConfigError) as caught:
        reserving(tmp_path, "media-library")
    assert "reserved_ids" in str(caught.value)
