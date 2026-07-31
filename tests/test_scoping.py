"""The one bullet in the roadmap that is not a task line (RK70).

What is under test is mostly the *seam*: this is the only content of the governed files whose
grammar did not exist, so the claims worth holding are that the door refuses what a task line's
door refuses (a field over its limit, an address already taken), that the gate says nothing at
all until a project declares the list governed, and that the write path and the gate agree on
what "the same lead" means — a duplicate the writer accepted and `lint` then failed on would be
the L1 split this closes.

The other half is the fixture: this repository's five non-goals are the corpus the grammar was
measured against, so they parse, they are the leads a reader sees, and `lint` passes on them
with the opt-in declared. A grammar that could not express them would be the wrong grammar.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from roadkeep.cli import EXIT_OK, EXIT_USAGE, main
from roadkeep.config import Config, ConfigError, Scope
from roadkeep.linting import lint
from roadkeep.schema import SchemaError
from roadkeep.scoping import (
    DuplicateLead,
    NoNonGoals,
    NotGoverned,
    add,
    address,
    read,
    rejects,
    render,
)

HERE = Path(__file__).resolve().parents[1]

ROADMAP = """# Roadmap

## Block A — The model

- 📋 **RK1** (deps: —) **A symptom** — Because of a reason. → §RK1

## Non-goals

Deliberately **not** built — check this list before proposing work:

- **No web UI and no server.** Files and a CLI. The store is the repository.
- **No issue-tracker sync** (Jira, Linear, GitHub Issues). A backlog that lives in a
  service is a backlog an agent cannot `Grep`.
"""

GOVERNED = 'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\n[non_goals]\nlead = 60\nwhy = 200\n'
PROSE = 'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\n'


def project(tmp_path: Path, roadmap: str = ROADMAP, config: str = GOVERNED) -> Config:
    (tmp_path / "roadkeep.toml").write_text(config, encoding="utf-8")
    with (tmp_path / "ROADMAP.md").open("w", encoding="utf-8", newline="") as handle:
        handle.write(roadmap)
    return Config.discover(tmp_path)


def text(tmp_path: Path) -> str:
    with (tmp_path / "ROADMAP.md").open("r", encoding="utf-8", newline="") as handle:
        return handle.read()


# -- reading what is already there -------------------------------------------


def test_a_wrapped_bullet_is_one_non_goal_and_not_two(tmp_path):
    # A filled bullet spans lines, and a reader that counted lines would report the
    # continuation as a second non-goal with no lead at all.
    config = project(tmp_path)
    found = read(config.document("roadmap"))
    assert [n.lead for n in found] == ["No web UI and no server.", "No issue-tracker sync"]
    assert (found[1].first, found[1].last) == (12, 13)
    assert found[1].why.endswith("an agent cannot `Grep`.")


def test_the_lead_keeps_the_punctuation_its_author_wrote(tmp_path):
    # One of the two carries its stop inside the bold and the other is followed by a
    # parenthetical. Normalizing either would be the tool rewriting prose (L4).
    config = project(tmp_path)
    first, second = read(config.document("roadmap"))
    assert first.lead.endswith(".") and first.why.startswith("Files and a CLI")
    assert not second.lead.endswith(".") and second.why.startswith("(Jira")


def test_a_bullet_with_no_bold_lead_is_reported_and_never_guessed_at(tmp_path):
    config = project(tmp_path, roadmap=ROADMAP + "- No dates, because a marker is maturity.\n")
    assert len(read(config.document("roadmap"))) == 2
    assert rejects(config.document("roadmap")) == (
        (14, "- No dates, because a marker is maturity."),
    )


def test_the_intro_sentence_is_not_a_non_goal(tmp_path):
    # It carries bold text and sits under the heading, which is every property but the one
    # that matters: it is not a bullet.
    config = project(tmp_path)
    assert all("Deliberately" not in n.lead for n in read(config.document("roadmap")))


# -- the address --------------------------------------------------------------


def test_the_write_path_and_the_gate_mean_the_same_lead(tmp_path):
    # The bug this closes: `add` compared leads verbatim while `lint` folded them, so
    # "no web UI and no server" was inserted and then failed the gate it had just passed.
    config = project(tmp_path)
    with pytest.raises(DuplicateLead) as caught:
        add(config, lead="no web UI and no server", why="Again.")
    assert ":11 already leads" in str(caught.value)
    assert text(tmp_path) == ROADMAP
    assert address("No web UI and no server.") == address("no web ui and no server")


# -- writing ------------------------------------------------------------------


def test_the_bullet_lands_after_the_last_one_filled_to_the_prose_width(tmp_path):
    config = project(tmp_path)
    written = add(
        config,
        lead="No plugin marketplace",
        why="A registry of formats is a second place the schema lives, and the point is "
        "that it lives in roadkeep.toml.",
    )
    written.save()

    assert written.lineno == 14
    assert len(written.rendered) == 2
    assert all(len(line) <= config.schema.prose_width for line in written.rendered)
    assert written.rendered[1].startswith("  ")
    assert text(tmp_path) == ROADMAP + "\n".join(written.rendered) + "\n"


def test_the_first_non_goal_goes_below_the_prose_and_not_above_it(tmp_path):
    # The section opens with a sentence telling a reader to check the list. A bullet glued
    # above it would make the instruction read as a footnote to the first non-goal.
    bare = ROADMAP.split("- **No web UI")[0]
    config = project(tmp_path, roadmap=bare)
    add(config, lead="No dates", why="A marker is maturity, not a schedule.").save()
    # A blank line in front of it, and the one the section already ended with left where the
    # author had it: what separated this section from what follows still does.
    assert text(tmp_path) == bare + "- **No dates** A marker is maturity, not a schedule.\n\n"


def test_the_render_is_the_only_writer_of_the_shape(tmp_path):
    config = project(tmp_path)
    assert render(config, " No dates ", "A marker is\n  maturity.") == (
        "- **No dates** A marker is maturity.",
    )


def test_the_roadmap_still_round_trips_with_a_written_non_goal(tmp_path):
    config = project(tmp_path)
    add(config, lead="No dates", why="A marker is maturity, not a schedule.").save()
    document = Config.discover(tmp_path).document("roadmap")
    assert document.render() == text(tmp_path)  # L3
    assert document.non_canonical == () and document.rejects == ()
    assert len(document.entries) == 1  # and the task line is still the only task line


# -- what it refuses ---------------------------------------------------------


def test_a_project_that_has_not_opted_in_is_refused_and_not_defaulted(tmp_path):
    # RK66's lesson: Shio and Turing wrote their lists years before this grammar, so a
    # default would judge every existing bullet on the first call.
    config = project(tmp_path, config=PROSE)
    with pytest.raises(NotGoverned):
        add(config, lead="No dates", why="A marker is maturity.")
    assert text(tmp_path) == ROADMAP


def test_a_lead_over_the_limit_is_refused_at_input(tmp_path):
    config = project(tmp_path)
    with pytest.raises(SchemaError) as caught:
        add(config, lead="No " + "x" * 70, why="Because.")
    assert [v.code for v in caught.value.violations] == ["non-goal.lead"]
    assert text(tmp_path) == ROADMAP


def test_both_fields_are_reported_at_once(tmp_path):
    # A refusal that reports one problem per run turns a single fix into a conversation.
    config = project(tmp_path)
    with pytest.raises(SchemaError) as caught:
        add(config, lead="No " + "x" * 70, why="Because. " * 40)
    assert [v.code for v in caught.value.violations] == ["non-goal.lead", "non-goal.why"]


def test_a_lead_carrying_its_own_bold_is_refused(tmp_path):
    # The renderer bolds the lead, so a lead with `*` in it renders as a shape nothing
    # parses — the field would be accepted and the line would be unreadable.
    config = project(tmp_path)
    with pytest.raises(SchemaError):
        add(config, lead="No **web** UI", why="Because.")


def test_a_roadmap_with_no_heading_has_no_list_to_write_to(tmp_path):
    config = project(tmp_path, roadmap=ROADMAP.split("## Non-goals")[0])
    with pytest.raises(NoNonGoals):
        add(config, lead="No dates", why="A marker is maturity.")


def test_a_non_goals_table_that_is_not_one_is_a_config_problem(tmp_path):
    with pytest.raises(ConfigError):
        Config.parse({"non_goals": {"lead": 0}}, root=tmp_path)
    with pytest.raises(ConfigError):
        Config.parse({"non_goals": {"leed": 60}}, root=tmp_path)
    # Declared and empty is the shortest way to opt in: what it declares is *that* the
    # list is a schema, and the numbers are what a project may then also tune (L6).
    assert Config.parse({"non_goals": {}}, root=tmp_path).non_goals == Scope()


# -- the gate ----------------------------------------------------------------


def test_the_gate_says_nothing_until_the_project_opts_in(tmp_path):
    broken = ROADMAP + "- No lead at all here.\n- **No web UI and no server** Twice.\n"
    assert lint(project(tmp_path, roadmap=broken, config=PROSE)).findings == ()
    codes = [f.code for f in lint(project(tmp_path, roadmap=broken)).findings]
    assert codes == ["non-goal.shape", "non-goal.duplicate"]


def test_the_gate_reports_a_field_over_the_limit_where_the_bullet_is(tmp_path):
    long_why = "Because it is. " * 20
    config = project(tmp_path, roadmap=ROADMAP + f"- **No dates** {long_why}\n")
    finding = next(f for f in lint(config).findings if f.code == "non-goal.why")
    assert finding.lineno == 14 and "limit 200" in finding.message


# -- this repository is the fixture ------------------------------------------


def test_this_repository_declares_its_own_list_governed_and_passes():
    config = Config.discover(HERE)
    assert config.non_goals is not None
    roadmap = config.document("roadmap")
    assert rejects(roadmap) == ()
    # The five the grammar was measured against, each addressed by a lead a `brief` prints.
    found = read(roadmap)
    assert len(found) >= 5 and all(n.lead and n.why for n in found)
    assert [f for f in lint(config).findings if f.code.startswith("non-goal.")] == []


# -- the command -------------------------------------------------------------


def test_the_command_prints_where_the_bullet_landed_and_what_it_wrote(tmp_path, capsys):
    project(tmp_path)
    assert (
        main(
            [
                "-C", str(tmp_path), "non-goal", "add",
                "--lead", "No dates",
                "--why", "A marker is maturity, not a schedule.",
            ]
        )
        == EXIT_OK
    )
    out = capsys.readouterr().out
    assert out.startswith("ROADMAP.md:14  1 line(s)")
    assert "- **No dates** A marker is maturity, not a schedule." in out


def test_the_command_json_carries_the_line_and_the_rendering(tmp_path, capsys):
    project(tmp_path)
    assert (
        main(
            [
                "-C", str(tmp_path), "non-goal", "add", "--json",
                "--lead", "No dates",
                "--why", "A marker is maturity, not a schedule.",
            ]
        )
        == EXIT_OK
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["lead"] == "No dates" and payload["line"] == 14
    assert payload["file"] == "ROADMAP.md"
    assert payload["rendered"] == ["- **No dates** A marker is maturity, not a schedule."]


def test_a_refused_command_writes_nothing_and_exits_two(tmp_path, capsys):
    project(tmp_path, config=PROSE)
    assert (
        main(["-C", str(tmp_path), "non-goal", "add", "--lead", "No dates", "--why", "Because."])
        == EXIT_USAGE
    )
    assert "[non_goals]" in capsys.readouterr().err
    assert text(tmp_path) == ROADMAP
