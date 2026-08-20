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
    # And the argument, which the tool does not write (L4).
    assert "reason   yours" in wrote


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
