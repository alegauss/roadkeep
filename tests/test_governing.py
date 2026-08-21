"""A number that is a judgement, written where the reading that decides it is taken (RK1272).

`declare` retrofits a role and `priority migrate` moves the queue; every other table in
`roadkeep.toml` was a hand edit, which over the served surface is no edit at all. What is
asserted here is the three things that make this a verb rather than an editor: the reading and
the write arrive in one call, a limit the corpus already breaks is refused before it is
written, and the file keeps every byte the write did not address — the comments in it being the
arguments for its own numbers.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from roadkeep import governing
from roadkeep.cli import EXIT_OK, main
from roadkeep.config import Config

ROADMAP = "docs/ROADMAP.md"
CHANGELOG = "docs/CHANGELOG.md"

CONFIG = """# a comment somebody wrote
prefix = "RK"

[files]
roadmap = "docs/ROADMAP.md"
changelog = "docs/CHANGELOG.md"

# why 120 and not 130, argued here
[limits]
symptom = 120
why = 200
"""

BACKLOG = """# Roadmap

## Block A — The model

- 📋 **RK1** (deps: —) **A first symptom that is plainly long enough to read** — Because of a reason.
"""

LEDGER = """# Shipped

## Block A — The model
"""


def project(tmp_path: Path, *, config: str = CONFIG) -> Config:
    (tmp_path / "roadkeep.toml").write_text(config, encoding="utf-8", newline="")
    for name, body in ((ROADMAP, BACKLOG), (CHANGELOG, LEDGER)):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            handle.write(body)
    return Config.discover(tmp_path)


def written(config: Config) -> str:
    return (config.root / "roadkeep.toml").read_text(encoding="utf-8")


# -- the reading and the number, in one call ----------------------------------


def test_the_reading_arrives_with_the_write_and_alone_without_one(tmp_path):
    """The defect. Every one of these numbers already had the read that decides it, and the
    reading happened in one place while the number was defended in a comment somewhere else."""
    config = project(tmp_path)
    found = governing.reading(config, "limits.symptom")

    assert found.sites == 1
    assert found.worst == 51  # the one symptom this fixture carries
    assert found.declared == 120
    assert "widest 51" in found.stated()

    declared = governing.govern(Config.discover(tmp_path), "limits.symptom", 90)
    assert declared.before == 120
    assert declared.measured.worst == 51
    assert "symptom = 90" in written(Config.discover(tmp_path))


def test_a_limit_the_corpus_already_breaks_is_refused_and_writes_nothing(tmp_path):
    """The whole of what makes this a verb: a limit whose first act is a finding is one
    somebody lowers, reads the report, and raises again — three commits and a red gate for a
    decision that was measurable before the first of them."""
    config = project(tmp_path)
    before = written(config)
    with pytest.raises(governing.Violated) as caught:
        governing.govern(config, "limits.symptom", 20)

    said = str(caught.value)
    assert "measures 51" in said and "declare it at 51 or above" in said
    assert written(Config.discover(tmp_path)) == before


def test_the_file_keeps_every_byte_the_write_did_not_address(tmp_path):
    """Not a serialiser, which is `declare`'s rule and `bump_version`'s before it: a `tomllib`
    round-trip drops the comments a config is mostly made of — and here those comments are the
    arguments for the numbers this verb writes."""
    config = project(tmp_path)
    governing.govern(config, "limits.why", 150)

    after = written(Config.discover(tmp_path))
    assert "# a comment somebody wrote" in after
    assert "# why 120 and not 130, argued here" in after
    assert "why = 150" in after
    # In place and never appended: a second declaration of one number is a file `tomllib`
    # reads one way and a reader reads the other.
    assert after.count("why = ") == 1


def test_a_table_this_project_never_declared_is_opened_by_the_write(tmp_path):
    # `criterion add`'s rule about a heading: a project that declared none has no place for the
    # first number, and a verb that refused would send the author to the hand edit this ends.
    config = project(tmp_path)
    assert "[claims]" not in written(config)
    governing.govern(config, "claims.held", 90)

    after = written(Config.discover(tmp_path))
    assert "[claims]" in after and "held = 90" in after
    assert Config.discover(tmp_path).held == 90


# -- the four tables, and nothing else -----------------------------------------


def test_a_key_that_is_a_name_rather_than_a_measurement_is_refused(tmp_path):
    """The interesting half of that refusal: `[files] roadmap` and `[markers] shipped` are keys
    this build has and decisions with nothing to measure them against, so a verb that took one
    would print an empty reading beside a write `declare` already makes."""
    config = project(tmp_path)
    with pytest.raises(KeyError) as caught:
        governing.govern(config, "markers.shipped", 5)

    said = str(caught.value)
    assert "no governed number at 'markers.shipped'" in said
    assert "limits" in said and "claims" in said


def test_the_key_a_width_governs_is_measured_by_nobody_and_says_so(tmp_path):
    # `prose` is the one key in `[limits]` nothing refuses: it says how wide a section this
    # tool *writes* is filled, so an adopted file's wider lines are not a violation.
    found = governing.reading(project(tmp_path), "limits.prose")
    assert found.sites == 0
    assert "no gate refuses" in found.unmeasured
    # And a number under the widest line on disk is therefore accepted, which is the point.
    governing.govern(Config.discover(tmp_path), "limits.prose", 72)
    assert "prose = 72" in written(Config.discover(tmp_path))


def test_the_claim_window_is_a_judgement_no_file_holds_evidence_about(tmp_path):
    found = governing.reading(project(tmp_path), "claims.held")
    assert found.sites == 0
    assert "how long work takes" in found.unmeasured
    assert "reading  none" in found.stated()


def test_a_budget_for_a_file_that_is_not_there_would_be_a_limit_nothing_pays(tmp_path):
    # The same argument as the refusal above, for the other absence: a budget on an absent
    # file is `budget.absent` to the gate, so writing one is declaring a finding.
    config = project(tmp_path)
    before = written(config)
    with pytest.raises(ValueError) as caught:
        governing.govern(config, "budgets.lines", 100, file="nothing.md")

    assert "is not in this repository" in str(caught.value)
    assert written(Config.discover(tmp_path)) == before


def test_a_budget_entry_keeps_the_unit_the_other_call_declared(tmp_path):
    """The inline table is the value there, so the two numbers live inside one key — and a
    `bytes` declared last year is not something a `lines` call decided to drop."""
    config = project(tmp_path)
    (tmp_path / "agents.md").write_text("# Agents\n\nProse.\n", encoding="utf-8", newline="")
    governing.govern(config, "budgets.lines", 20, file="agents.md")
    governing.govern(Config.discover(tmp_path), "budgets.bytes", 400, file="agents.md")

    after = written(Config.discover(tmp_path))
    assert '"agents.md" = { lines = 20, bytes = 400 }' in after
    read = Config.discover(tmp_path).budgets
    assert (read[0].lines, read[0].bytes) == (20, 400)


# -- the verb ------------------------------------------------------------------


def test_the_verb_reads_with_no_value_and_writes_with_one(tmp_path, capsys):
    project(tmp_path)
    assert main(["-C", str(tmp_path), "govern", "limits.symptom"]) == EXIT_OK
    said = capsys.readouterr().out
    assert "reading" in said and "declared 120" in said
    assert "stage" not in said, "a read that staged nothing has nothing to stage"

    assert main(["-C", str(tmp_path), "govern", "limits.symptom", "100"]) == EXIT_OK
    wrote = capsys.readouterr().out
    assert "limits.symptom = 100 (was 120)" in wrote
    # The file, which is the half a reviewer would miss: a number moved here changes what
    # every other write is held to.
    assert "stage    git add -- roadkeep.toml" in wrote
    # And the argument, which the tool places and does not write (L4, RK1293).
    assert "reason   none" in wrote


def test_the_payload_carries_the_reading_the_number_was_written_against(tmp_path, capsys):
    project(tmp_path)
    assert main(["-C", str(tmp_path), "govern", "limits.why", "180", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)

    assert payload["address"] == "limits.why"
    assert payload["at"] == 180 and payload["was"] == 200
    assert payload["reading"]["worst"] == 20
    assert payload["file"] == "roadkeep.toml"


def test_a_project_with_no_config_is_told_which_command_writes_one(tmp_path, capsys):
    # The one state where there is no table to write into at all, and the door that makes one.
    assert main(["-C", str(tmp_path), "govern", "limits.symptom", "100"]) != EXIT_OK
    assert "init" in capsys.readouterr().err


def test_a_role_of_its_own_is_the_table_the_address_names(tmp_path):
    """`[limits.<role>]` is one table per role, so the heading is composed from what the caller
    passed and never from the placeholder the shape publishes."""
    config = project(tmp_path)
    governing.govern(config, "limits.why", 150, role="changelog")

    after = written(Config.discover(tmp_path))
    assert "[limits.changelog]" in after and "why = 150" in after
    # The shared table is untouched, which is the whole reason the role is an argument.
    assert "why = 200" in after
    assert Config.discover(tmp_path).schema_for("changelog").why_max == 150


def test_the_roles_a_line_reading_walks_are_the_declared_ones(tmp_path):
    """RK1279. A written-out tuple of the roles that carry lines was stale by construction —
    the sixth landed the same week — and it failed *quietly*: a role left out is a file the
    reading never opens, so a limit it already breaks is accepted and the gate reports it on
    the next run, which is the sequence this verb exists to prevent."""
    from roadkeep.config import PROSE_ROLES, ROLES

    project(
        tmp_path,
        config=CONFIG.replace(
            'changelog = "docs/CHANGELOG.md"',
            'changelog = "docs/CHANGELOG.md"\ndecisions = "docs/DECISIONS.md"',
        ),
    )
    # The declaration is the set, so this is the whole claim: every line role and no other.
    walked = tuple(one for one in ROLES if one not in PROSE_ROLES)
    assert "decisions" in walked and "improvements" not in walked

    # And the reading opens the sixth: a symptom only that file carries is what decides.
    (tmp_path / "docs" / "DECISIONS.md").write_text(
        "# Decisions\n\n## Block A — The model\n\n"
        "- ✅ **RK9** **A decision whose claim is very much wider than the roadmap's own one**"
        " — Because it is.\n",
        encoding="utf-8",
        newline="",
    )
    found = governing.reading(Config.discover(tmp_path), "limits.symptom")
    assert found.sites == 2
    assert found.where.endswith("DECISIONS.md:5"), found.where


# -- what a limit inherits, measured before it is declared (RK1284) -----------


def _with_decisions(tmp_path: Path, *, extra: str = "") -> Config:
    """The fixture plus a declared `decisions` role, which is what makes a claim carried."""
    config = project(
        tmp_path,
        config=CONFIG.replace(
            'changelog = "docs/CHANGELOG.md"',
            'changelog = "docs/CHANGELOG.md"\ndecisions = "docs/DECISIONS.md"',
        )
        + extra,
    )
    (tmp_path / "docs" / "DECISIONS.md").write_text(
        "# Decisions\n\n## Block A — The model\n", encoding="utf-8", newline=""
    )
    return Config.discover(config.root)


def test_the_reading_counts_the_claims_a_ship_would_carry_in(tmp_path):
    """RK1281 named three arms and built two; this is the third. A decisions file with nothing
    in it measured zero sites, so any number was accepted — and every `ship --decides`
    afterwards was refused over a claim the roadmap already carried."""
    found = governing.reading(_with_decisions(tmp_path), "limits.symptom", role="decisions")

    assert found.sites == 1, "the open line is the population, and the file holds none"
    assert found.worst == 51
    assert "(inherited)" in found.where and "ROADMAP" in found.where


def test_a_number_the_carried_claim_breaks_is_refused_at_declaration(tmp_path):
    config = _with_decisions(tmp_path)
    before = written(config)
    with pytest.raises(governing.Violated) as caught:
        governing.govern(config, "limits.symptom", 20, role="decisions")

    assert "(inherited) measures 51" in str(caught.value)
    assert written(Config.discover(tmp_path)) == before


def test_one_inheritance_is_counted_and_no_other(tmp_path):
    """`_decided` composes the record with `as_recorded`, which keeps the symptom and replaces
    the `why` — so the symptom is inherited whole and nothing else is. A reading of what
    *might* be written anywhere would be a guess; this is the one the code states."""
    config = _with_decisions(tmp_path)
    # The `why` is the author's on that call, so nothing is carried into its limit.
    assert governing.reading(config, "limits.why", role="decisions").sites == 0
    # And no other role inherits: the changelog's claim comes from the same line, but its
    # limit already measures that line under the shared table.
    assert governing.reading(config, "limits.symptom", role="changelog").sites == 0


def test_the_shared_table_counts_the_roadmap_once(tmp_path):
    # A call with no role already walks every line file, so counting the carried claims there
    # too would be one population reported twice.
    config = _with_decisions(tmp_path)
    assert governing.reading(config, "limits.symptom").sites == 1
    assert "(inherited)" not in governing.reading(config, "limits.symptom").where


# -- the argument for the number, placed and never written (RK1293) ------------


def test_the_argument_lands_above_the_key_in_the_author_s_own_words(tmp_path):
    """The decision this supersedes said the argument goes in the commit that wrote the
    number. On an agent session the commit body is composed by a tool this project does not
    own, and the number arrived in one whose body never named it — so the argument was kept
    nowhere. Here it is placed where the number is, which is where a reader takes it."""
    config = project(tmp_path)
    governing.govern(config, "limits.symptom", 90, because="P90 of the lines that read well.")

    after = written(Config.discover(tmp_path))
    assert "# P90 of the lines that read well.\nsymptom = 90\n" in after


def test_a_new_argument_stacks_on_the_one_that_argued_the_number_before(tmp_path):
    """A raise is a decision about the previous decision, and this project's own `[tools]`
    entry is five of them written that way by hand. Replacing would lose the reason the
    number was lower, which is the half a reader of a raise is actually looking for."""
    config = project(tmp_path)
    governing.govern(config, "limits.why", 150, because="First, because the fixture is short.")
    governing.govern(Config.discover(tmp_path), "limits.why", 160, because="Then, longer.")

    after = written(Config.discover(tmp_path))
    assert "# why 120 and not 130, argued here" in after
    assert "# First, because the fixture is short.\n# Then, longer.\nwhy = 160\n" in after


def test_the_argument_is_wrapped_to_the_width_this_project_declares(tmp_path):
    """Filled and never one long line, because the file it lands in is read by a person and
    every comment already in it wraps. The width is the project's, not this module's."""
    config = project(tmp_path)
    long = " ".join(["argument"] * 40)
    governing.govern(config, "limits.symptom", 90, because=long)

    lines = [line for line in written(Config.discover(tmp_path)).splitlines() if "argument" in line]
    assert len(lines) > 1
    assert all(line.startswith("# ") for line in lines)
    assert all(len(line) <= config.schema.prose_width for line in lines)


def test_a_table_opened_by_the_write_carries_the_argument_under_its_heading(tmp_path):
    config = project(tmp_path)
    governing.govern(config, "claims.held", 90, because="A day is what a session lasts here.")

    after = written(Config.discover(tmp_path))
    assert "[claims]\n# A day is what a session lasts here.\nheld = 90\n" in after
    assert Config.discover(tmp_path).held == 90


def test_the_line_reported_is_the_one_the_number_landed_on(tmp_path):
    """A reviewer reads the diff against it, and comments above the key move it down."""
    config = project(tmp_path)
    declared = governing.govern(config, "limits.symptom", 90, because="One line of argument.")

    lines = written(Config.discover(tmp_path)).splitlines()
    assert lines[declared.lineno - 1] == "symptom = 90"


def test_a_number_declared_with_no_argument_is_told_it_is_undated(tmp_path, capsys):
    """The other half, and the reason this is a field rather than a silence: a number with
    nothing beside it is one nobody can date, and the answer says so where it happened."""
    config = project(tmp_path)
    assert main(["-C", str(config.root), "govern", "limits.symptom", "90"]) == EXIT_OK
    said = capsys.readouterr().out
    assert "--because" in said and "nobody can date" in said

    assert (
        main(
            [
                "-C",
                str(config.root),
                "govern",
                "limits.why",
                "150",
                "--because",
                "The fixture's own reason.",
            ]
        )
        == EXIT_OK
    )
    said = capsys.readouterr().out
    assert "in your words" in said
    assert "# The fixture's own reason." in written(Config.discover(config.root))


def test_the_payload_says_whether_the_number_was_argued(tmp_path, capsys):
    config = project(tmp_path)
    argv = ["-C", str(config.root), "govern", "limits.symptom", "90", "--json"]
    assert main([*argv, "--because", "Because."]) == EXIT_OK
    assert json.loads(capsys.readouterr().out)["argued"] is True

    assert main(argv) == EXIT_OK
    assert json.loads(capsys.readouterr().out)["argued"] is False
