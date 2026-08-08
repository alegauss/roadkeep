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

import corpora
from roadkeep.cli import EXIT_OK, EXIT_USAGE, main
from roadkeep.config import Config, ConfigError, Scope
from roadkeep.provenance import invocation
from roadkeep.guarding import Refusal
from roadkeep.linting import lint
from roadkeep.schema import SchemaError
from roadkeep.scoping import (
    DuplicateLead,
    NoNonGoals,
    NoSuchNonGoal,
    NotGoverned,
    Unshaped,
    add,
    address,
    amend,
    drop,
    leads,
    read,
    rejects,
    render,
)
from roadkeep.serving import TOOLS, descriptor

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


def test_a_bullet_with_no_bold_lead_is_read_and_still_reported(tmp_path):
    # RK233: read, so it has an address and therefore a door; reported, because being
    # addressable is not being in the format. The two answers used to be two readers.
    config = project(tmp_path, roadmap=ROADMAP + "- No dates, because a marker is maturity.\n")
    found = read(config.document("roadmap"))
    assert len(found) == 3 and [n.shaped for n in found] == [True, True, False]
    assert found[-1].lead == "No dates, because a marker is maturity."
    assert rejects(config.document("roadmap")) == (
        (14, "- No dates, because a marker is maturity."),
    )


def test_the_lead_brief_prints_is_the_address_drop_takes(tmp_path):
    # The defect, as the pair a caller actually runs: `brief` printed a constraint by its
    # first sentence and `non-goal drop` answered that no such non-goal exists — while `Edit`
    # is denied and the gate's remedy for the bullet is a rewrite. Every door closed.
    plain = "- Don't refactor the router, the SSE bus or the A/B assignment. Only execution.\n"
    config = project(tmp_path, roadmap=ROADMAP + plain)
    (lead,) = [n.lead for n in read(config.document("roadmap")) if not n.shaped]
    assert lead == "Don't refactor the router, the SSE bus or the A/B assignment"
    dropped = drop(config, lead)
    dropped.save()
    assert dropped.lines == (plain.rstrip("\n"),)  # the span, verbatim — nothing re-rendered
    assert text(tmp_path) == ROADMAP


def test_the_shape_is_the_only_finding_an_unshaped_bullet_earns(tmp_path):
    # The lengths are charged where the shape held. A sentence-lead charged against `lead` as
    # well is a second finding the first subsumes, and Turing's `is **not** a path` would add
    # a third for the `*` of a bold run this module never wrote.
    over = "- " + "Structured output (LLM → JSON) is **not** a path. " * 3 + "\n"
    config = project(tmp_path, roadmap=ROADMAP + over)
    codes = [f.code for f in lint(config).findings]
    assert codes == ["non-goal.shape"]


def test_two_bullets_of_different_shapes_are_still_one_address(tmp_path):
    # The address is checked for every bullet because every bullet now has one: `drop` would
    # take the later of the two either way, so a gate silent about it would be the split again.
    twin = "- No web UI and no server. Said once more, without the bold.\n"
    config = project(tmp_path, roadmap=ROADMAP + twin)
    # Both on the one line, so the report orders them by code (RK14).
    codes = [f.code for f in lint(config).findings]
    assert codes == ["non-goal.duplicate", "non-goal.shape"]


def test_the_corpus_that_named_this_has_a_door_for_every_lead_it_prints():
    """Turing's list is what RK139 measured and RK233 was filed from: 0 parsed, 7 unread.

    The count `adopt` reports is unchanged, because being addressable is not being in the
    format — what changed is that all seven now resolve to a bullet, so nothing `brief` prints
    is a constraint `drop` denies the existence of. Shio's nine hold the shape and are the
    other half of the claim: a reader that accepts more must not accept them differently.
    """
    corpora.require(corpora.TURING)
    document = corpora.document(corpora.TURING, "roadmap")
    found = read(document)
    assert len(found) == 7 and not any(goal.shaped for goal in found)
    assert len(rejects(document)) == 7  # still the gate's finding, and still seven
    addresses = {address(goal.lead) for goal in found}
    assert {address(lead) for lead in leads(document)} == addresses
    assert len(addresses) == 7  # seven bullets, seven addresses, none colliding


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
    # Through `over_by` now (RK430), which is the one composer of a length refusal — so
    # the surplus and the word aim arrive here as they do on every other field.
    assert finding.lineno == 14 and "limit is 200" in finding.message
    assert "delete 99 characters" in finding.message


# -- this repository is the fixture ------------------------------------------


def test_this_repository_declares_its_own_list_governed_and_passes(governed):
    config = Config.discover(governed)
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


# -- the other half of the door ----------------------------------------------


def test_the_bullet_a_lead_addresses_goes_whole(tmp_path):
    # Wrapped lines included: removing the first line of a filled bullet would leave its
    # continuation behind as prose nothing governs.
    config = project(tmp_path)
    dropped = drop(config, "no issue-tracker sync")
    dropped.save()
    assert (dropped.non_goal.first, dropped.non_goal.last) == (12, 13)
    assert dropped.carried == 1
    assert text(tmp_path) == ROADMAP.split("- **No issue-tracker sync**")[0].rstrip(" ")
    assert read(Config.discover(tmp_path).document("roadmap"))[0].lead.startswith("No web UI")


def test_the_stop_inside_the_bold_does_not_have_to_be_typed(tmp_path):
    # The address is the lead folded and without its trailing stop, so a constraint is looked
    # up by the words a reader remembers rather than by punctuation they cannot see.
    config = project(tmp_path)
    drop(config, "NO WEB UI AND NO SERVER").save()
    assert [n.lead for n in read(Config.discover(tmp_path).document("roadmap"))] == [
        "No issue-tracker sync"
    ]


def test_dropping_the_only_bullet_leaves_no_doubled_blank(tmp_path):
    one = ROADMAP.split("- **No issue-tracker sync**")[0]
    config = project(tmp_path, roadmap=one + "\n## After — a heading below the list\n")
    drop(config, "No web UI and no server").save()
    assert text(tmp_path).endswith("proposing work:\n\n## After — a heading below the list\n")
    assert Config.discover(tmp_path).document("roadmap").render() == text(tmp_path)  # L3


def test_a_lead_that_addresses_nothing_names_the_ones_that_exist(tmp_path):
    # A refusal that only says "not found" sends the caller to read the file, which is the
    # cost the command exists to remove (L5).
    config = project(tmp_path)
    with pytest.raises(NoSuchNonGoal) as caught:
        drop(config, "No dates")
    assert "No issue-tracker sync" in str(caught.value)
    assert text(tmp_path) == ROADMAP


def test_a_duplicate_lead_is_dropped_from_the_later_bullet(tmp_path):
    # The repair for `lint`'s non-goal.duplicate, and the same rule `record drop` follows:
    # what stays is the first, where the reader already found the decision.
    twice = ROADMAP + "- **No web UI and no server** Written a second time.\n"
    config = project(tmp_path, roadmap=twice)
    dropped = drop(config, "No web UI and no server")
    dropped.save()
    assert dropped.carried == 2 and dropped.non_goal.first == 14
    assert text(tmp_path) == ROADMAP
    assert lint(Config.discover(tmp_path)).findings == ()


def test_a_project_that_has_not_opted_in_cannot_drop_either(tmp_path):
    config = project(tmp_path, config=PROSE)
    with pytest.raises(NotGoverned):
        drop(config, "No web UI and no server")
    assert text(tmp_path) == ROADMAP


def test_the_drop_command_names_the_span_and_the_lead(tmp_path, capsys):
    project(tmp_path)
    assert main(["-C", str(tmp_path), "non-goal", "drop", "no issue-tracker sync"]) == EXIT_OK
    assert capsys.readouterr().out.startswith(
        "ROADMAP.md:12-13  dropped  **No issue-tracker sync**"
    )


def test_the_drop_command_json_carries_what_was_removed(tmp_path, capsys):
    project(tmp_path)
    assert (
        main(["-C", str(tmp_path), "non-goal", "drop", "--json", "No web UI and no server"])
        == EXIT_OK
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["removed"] == [11, 11] and payload["carried"] == 1
    assert payload["rendered"] == [
        "- **No web UI and no server.** Files and a CLI. The store is the repository."
    ]


def test_a_refused_drop_writes_nothing_and_exits_two(tmp_path, capsys):
    project(tmp_path)
    assert main(["-C", str(tmp_path), "non-goal", "drop", "No dates"]) == EXIT_USAGE
    assert "leads with 'No dates'" in capsys.readouterr().err
    assert text(tmp_path) == ROADMAP


# -- the list at the moment one is proposed (RK69) ----------------------------


def test_the_list_is_a_command_and_not_only_a_field_of_a_brief(tmp_path, capsys):
    # The roadmap says to check the list before proposing work, and until this command the
    # only thing that printed it was `brief <id>` — the moment a task *starts*.
    project(tmp_path)
    assert main(["-C", str(tmp_path), "non-goal", "list"]) == EXIT_OK
    out = capsys.readouterr().out
    assert out.startswith("ROADMAP.md  2 non-goal(s)")
    # The shape `brief` prints, from the same reader: two projections of one list are two
    # answers about scope (RK68).
    assert "  not      No web UI and no server." in out
    assert "  not      No issue-tracker sync" in out


def test_reading_the_list_is_never_refused_for_not_being_governed(tmp_path, capsys):
    # `[non_goals]` gates the *write* (RK70). Refusing the read as well would leave the
    # scope of every project that has not opted in unaskable, which is the sentence-in-a-
    # file arrangement this replaces.
    project(tmp_path, config=PROSE)
    assert main(["-C", str(tmp_path), "non-goal", "list"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "read-only: no [non_goals]" in out
    assert "  not      No web UI and no server." in out


def test_an_empty_list_says_so_rather_than_printing_nothing(tmp_path, capsys):
    project(tmp_path, roadmap="# Roadmap\n\n## Non-goals\n")
    assert main(["-C", str(tmp_path), "non-goal", "list"]) == EXIT_OK
    assert "no non-goals" in capsys.readouterr().out


def test_the_json_carries_the_leads_the_file_and_whether_it_is_governed(tmp_path, capsys):
    project(tmp_path)
    assert main(["-C", str(tmp_path), "non-goal", "list", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["file"] == "ROADMAP.md" and payload["governed"] is True
    assert payload["non_goals"][0] == "No web UI and no server."
    assert payload["non_goals_elided"] == 0


def test_nothing_is_enforced_because_enforcing_it_would_take_a_model(tmp_path):
    # Stated as a test so nothing later promises it: the write door takes a lead and a
    # reason and nothing that acknowledges the list — an agent passes any flag it is asked
    # to pass, and judging whether a proposal violates a constraint is meaning (L4).
    described = descriptor(
        next(t for t in TOOLS if t.name == "non_goal_add"), project(tmp_path)
    )
    assert set(described["inputSchema"]["properties"]) == {"lead", "why"}
    assert described["inputSchema"]["additionalProperties"] is False


def test_the_read_is_served_over_stdio_and_named_by_the_guard():
    # RK69's other two surfaces: the same tool a session already has (RK24), and the denial
    # that teaches the check beside the writes (RK22) — advice that names only the write
    # teaches half of what the roadmap asks for.
    assert "non_goal_list" in {tool.name for tool in TOOLS}
    assert not next(t for t in TOOLS if t.name == "non_goal_list").writes
    reason = str(Refusal(tool="Edit", path="docs/ROADMAP.md", role="roadmap"))
    assert f"{invocation()} non-goal list" in reason
    assert "mcp__roadkeep__non_goal_list" in reason


# -- the bound a client validates against ------------------------------------


def test_the_tool_schema_reads_the_non_goals_own_limits(tmp_path):
    # `why` is a field two tables name, so a client validating a bullet against the *task*
    # limit would refuse prose the tool accepts — right-looking and wrong (RK24).
    config = project(
        tmp_path,
        config='prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\n'
        "[limits]\nwhy = 200\n[non_goals]\nlead = 40\nwhy = 400\n",
    )
    described = descriptor(next(t for t in TOOLS if t.name == "non_goal_add"), config)
    properties = described["inputSchema"]["properties"]
    assert properties["why"]["maxLength"] == 400
    assert properties["lead"]["maxLength"] == 40
    assert described["inputSchema"]["required"] == ["lead", "why"]


# -- the correction that is not a move (RK368) --------------------------------


def body(config: Config) -> str:
    with config.path("roadmap").open("r", encoding="utf-8", newline="") as handle:
        return handle.read()


def test_a_reworded_reason_keeps_the_bullet_where_it_was(tmp_path):
    # Measured at RK367: the only door was drop-and-re-add, and `add` inserts after the last
    # bullet — so a constraint that sat fifth of eight moved to eighth, and a reviewer read a
    # deletion and an addition where a word changed.
    config = project(tmp_path)
    before = read(config.document("roadmap"))
    amended = amend(config, "No web UI and no server", "Files and a CLI, and nothing else.")
    amended.save()

    after = read(Config.discover(tmp_path).document("roadmap"))
    assert [one.lead for one in after] == [one.lead for one in before]
    assert after[0].first == before[0].first
    assert after[0].why == "Files and a CLI, and nothing else."


def test_the_reason_is_the_only_field_and_the_lead_is_the_address(tmp_path):
    config = project(tmp_path)
    amend(config, "no web ui and no server.", "A corrected reason.").save()

    # Addressed case-folded and without the stop, and the head the file spells is what is
    # written back — composing from the argument would rewrite the address this verb keeps.
    assert "- **No web UI and no server.** A corrected reason." in body(
        Config.discover(tmp_path)
    )


def test_a_reason_that_already_reads_that_way_writes_nothing(tmp_path):
    config = project(tmp_path)
    was = body(config)
    amended = amend(config, "No web UI and no server", "Files and a CLI. The store is the repository.")

    assert not amended.changed
    amended.save()
    assert body(Config.discover(tmp_path)) == was


def test_the_corrected_reason_is_filled_to_the_same_width(tmp_path):
    # One renderer, so a correction cannot produce a bullet `add` would not have written.
    config = project(tmp_path)
    amended = amend(config, "No web UI and no server", "one two three four five six " * 5)
    amended.save()

    assert len(amended.rendered) > 1
    assert all(len(line) <= 88 for line in amended.rendered)
    assert all(line.startswith("  ") for line in amended.rendered[1:])


def test_a_reason_over_the_limit_is_refused_and_nothing_moves(tmp_path):
    config = project(tmp_path)
    was = body(config)
    with pytest.raises(SchemaError) as raised:
        amend(config, "No web UI and no server", "word " * 60)

    assert [v.code for v in raised.value.violations] == ["non-goal.why"]
    assert body(config) == was


def test_a_lead_the_list_does_not_carry_is_refused(tmp_path):
    config = project(tmp_path)
    with pytest.raises(NoSuchNonGoal):
        amend(config, "No telemetry", "A reason for a constraint nobody filed.")


def test_a_project_that_never_opted_in_is_refused_like_the_other_two(tmp_path):
    config = project(tmp_path, config=PROSE)
    with pytest.raises(NotGoverned):
        amend(config, "No web UI and no server", "A corrected reason.")


def test_a_bullet_with_no_bold_lead_is_sent_to_the_pair_that_is_honest(tmp_path):
    # `read` accepts it so every constraint has an address (RK233), and that is safe because
    # nothing renders one back. An amend would be the first thing that does, and on this shape
    # the render imposes the bold head — which moves the lead, and the lead is the address.
    roadmap = ROADMAP + "- A bullet whose head is its first sentence. And its reason.\n"
    config = project(tmp_path, roadmap=roadmap)
    with pytest.raises(Unshaped) as raised:
        amend(config, "A bullet whose head is its first sentence", "A corrected reason.")

    assert "`non-goal drop`" in str(raised.value)
    assert body(config) == roadmap


def test_the_first_of_two_bullets_sharing_a_lead_is_the_one_corrected(tmp_path):
    # `drop` removes the later copy because the first is where the reader already found it
    # (RK67), so the one that stays is the one a correction is about.
    roadmap = ROADMAP + "- **No web UI and no server.** A second copy of the same address.\n"
    config = project(tmp_path, roadmap=roadmap)
    amend(config, "No web UI and no server", "The corrected reason.").save()

    written = read(Config.discover(tmp_path).document("roadmap"))
    same = [one for one in written if address(one.lead) == address("No web UI and no server")]
    assert [one.why for one in same] == [
        "The corrected reason.",
        "A second copy of the same address.",
    ]


def test_the_command_prints_the_bullet_it_rewrote(tmp_path, capsys):
    config = project(tmp_path)
    argv = ["-C", str(config.root), "non-goal", "amend", "No web UI and no server"]
    assert main([*argv, "--why", "A corrected reason."]) == EXIT_OK

    out = capsys.readouterr().out
    assert "amended  1 line(s)" in out
    assert "- **No web UI and no server.** A corrected reason." in out


def test_the_command_answers_in_json_with_both_readings(tmp_path, capsys):
    config = project(tmp_path)
    argv = ["-C", str(config.root), "non-goal", "amend", "No web UI and no server", "--json"]
    assert main([*argv, "--why", "A corrected reason."]) == EXIT_OK

    answer = json.loads(capsys.readouterr().out)
    assert answer["was"] == "Files and a CLI. The store is the repository."
    assert answer["now"] == "A corrected reason." and answer["changed"]


def test_a_refusal_exits_two_and_writes_nothing(tmp_path, capsys):
    config = project(tmp_path)
    was = body(config)
    argv = ["-C", str(config.root), "non-goal", "amend", "No telemetry", "--why", "A reason."]
    assert main(argv) == EXIT_USAGE

    assert body(config) == was


def test_the_gate_passes_the_bullet_this_verb_wrote(tmp_path):
    # The rule every door here holds: what the write path accepts, the gate accepts (L1).
    config = project(tmp_path)
    amend(config, "No web UI and no server", "A corrected reason for the constraint.").save()

    assert [f.code for f in lint(Config.discover(tmp_path)).findings] == []
