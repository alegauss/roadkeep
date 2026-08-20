"""The roadmap's third list: what must be **true** for a block to be finished (RK1265).

`test_scoping` is this file's twin and the reading is the same one pointed the other way — a
non-goal says what is not built, and until this nothing said what would make a block done. What
is asserted here beyond that module's rules is the two things this list has of its own: the
address is the **pair** `(block, lead)`, and the heading a block's list lives under is one the
document reader must never take for a block declaration.

That second one is the whole reason this grammar has a heading of its own rather than a
sub-heading under a block: `document._block_label` anchors at the start of a heading's text and
never asks its level, so `### Block A` under any other section declares that label a second time
— `block.repeated` to the gate, and refused by every write.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from roadkeep import criteria
from roadkeep.cli import EXIT_OK, EXIT_USAGE, main
from roadkeep.config import Config
from roadkeep.kernel.schema import SchemaError
from roadkeep.linting import lint

ROADMAP = "docs/ROADMAP.md"
CHANGELOG = "docs/CHANGELOG.md"

BACKLOG = """# Roadmap

## Block A — The model

- 📋 **RK1** (deps: —) **A first symptom** — Because of a reason. → §RK1

## Block B — Authoring

## Non-goals

- **No web UI and no server.** Files and a CLI.
"""

LEDGER = """# Changelog

## Block A — The model

## Block B — Authoring
"""


def project(tmp_path: Path, *, roadmap: str = BACKLOG, governed: bool = True) -> Config:
    (tmp_path / "roadkeep.toml").write_text(
        f'prefix = "RK"\n[files]\nroadmap = "{ROADMAP}"\nchangelog = "{CHANGELOG}"\n'
        + ("[criteria]\n" if governed else ""),
        encoding="utf-8",
    )
    for name, body in ((ROADMAP, roadmap), (CHANGELOG, LEDGER)):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            handle.write(body)
    return Config.discover(tmp_path)


def read(config: Config) -> str:
    with (config.root / ROADMAP).open("r", encoding="utf-8", newline="") as handle:
        return handle.read()


def written(where: Config | Path, block: str, lead: str, why: str) -> Config:
    """Write one criterion and hand back the config as it is *after* the write.

    Takes a tree or a config so a test can chain: every one of these reads the file back, and
    a helper that made the caller re-discover between calls would be the second reading this
    module is about keeping to one.
    """
    config = where if isinstance(where, Config) else project(where)
    criteria.add(config, block, lead, why).save()
    return Config.discover(config.root)


# -- the list, and the heading that is not a block ----------------------------


def test_the_first_criterion_opens_the_blocks_list(tmp_path):
    """`priority add`'s rule (RK427) and not `add`'s: a task line goes under a heading no write
    invents because a block is a decision about the plan, and a block's *criteria list* is
    opened by the act of writing the first one — there being nothing else the heading means."""
    config = project(tmp_path)
    out = criteria.add(config, "A", "Every governed file round-trips", "The gate holds it.")
    out.save()

    assert out.opened
    body = read(Config.discover(tmp_path))
    assert "## Done when — Block A" in body
    assert "- **Every governed file round-trips** The gate holds it." in body
    # And the second one does not open anything: it lands under the heading already there.
    again = criteria.add(
        Config.discover(tmp_path), "A", "No line is over its limit", "The gate exits 1."
    )
    assert not again.opened


def test_the_heading_is_never_read_as_a_second_block_declaration(tmp_path):
    """The reason this grammar has a heading of its own. `_block_label` anchors at the start of
    the text and never asks the level, so `### Block A` anywhere declares that label — which is
    `block.repeated` to the gate and refused by every write."""
    config = written(tmp_path, "A", "Every governed file round-trips", "The gate holds it.")
    document = config.document("roadmap")
    declared = [one.text for one in document.headings if one.label]

    assert declared == ["Block A — The model", "Block B — Authoring"]
    assert "Done when — Block A" in [one.text for one in document.headings]
    # And the gate agrees, which is the assertion that matters: a doubled label is a finding.
    assert not lint(config).findings


def test_the_list_is_placed_before_the_non_goals_and_after_every_block(tmp_path):
    """A heading ends the region above it, so one under a block's tasks would cut that block's
    subtree in two — which `block drop`, `block merge` and the gate all read as it ending
    there. And before the non-goals, which close the roadmap in both live corpora."""
    config = written(tmp_path, "B", "Every write has a door", "The guard denies the rest.")
    body = read(config)

    assert body.index("## Block B") < body.index("## Done when — Block B")
    assert body.index("## Done when — Block B") < body.index("## Non-goals")
    # The task line still belongs to Block A, which is the property the placement protects.
    assert config.document("roadmap").by_id()["RK1"].task.block == "A"


def test_the_two_lists_are_read_apart(tmp_path):
    """One grammar and two regions: a non-goal is not a criterion and neither reader may see
    the other's bullets, or the gate would judge each by the other's limits."""
    from roadkeep import scoping

    config = written(tmp_path, "A", "Every governed file round-trips", "The gate holds it.")

    assert [one.lead for one in criteria.read(config.document("roadmap"))] == [
        "Every governed file round-trips"
    ]
    assert scoping.leads(config.document("roadmap")) == ("No web UI and no server.",)


# -- the address is the pair --------------------------------------------------


def test_one_lead_under_two_blocks_is_two_claims(tmp_path):
    """The one place this differs from the non-goals: a criterion is about a body of work, so
    the same sentence under two blocks is two claims about two of them and not one written
    twice — which means neither the duplicate refusal nor the gate may see a collision."""
    config = written(tmp_path, "A", "Every write has a door", "The guard denies the rest.")
    config = written(config, "B", "Every write has a door", "The guard denies the rest.")

    assert [(one.about, one.lead) for one in criteria.read(config.document("roadmap"))] == [
        ("A", "Every write has a door"),
        ("B", "Every write has a door"),
    ]
    assert not lint(config).findings


def test_a_second_lead_in_one_block_is_refused(tmp_path):
    config = written(tmp_path, "A", "Every write has a door", "The guard denies the rest.")
    with pytest.raises(criteria.DuplicateLead) as caught:
        criteria.add(config, "A", "every write has a door.", "Said differently.")

    # Case-folded and without the stop, which is `scoping.address`' rule: two spellings of
    # "the same lead" would be a bullet the write path accepted and the gate then failed on.
    assert "already leads with" in str(caught.value)
    assert read(config).count("Every write has a door") == 1


def test_the_block_is_resolved_where_one_list_carries_the_lead(tmp_path):
    """`--block` optional on the two verbs that address an existing bullet, and required on the
    one that creates it. What it buys is a **complete door**: the gate's `criterion.duplicate`
    names the drop that closes it, and a remedy that could not spell the block would be the
    blank RK420 exists to remove."""
    config = written(tmp_path, "B", "Every write has a door", "The guard denies the rest.")
    out = criteria.drop(config, "", "every write has a door")
    out.save()

    assert out.criterion.about == "B"
    assert "Every write has a door" not in read(Config.discover(tmp_path))


def test_a_lead_two_blocks_carry_is_refused_without_the_block(tmp_path):
    """Refused rather than resolved to the first: a criterion is what finishes a body of work,
    and closing the wrong block's is the quiet corruption the grammar exists to prevent."""
    config = written(tmp_path, "A", "Every write has a door", "The guard denies the rest.")
    config = written(config, "B", "Every write has a door", "The guard denies the rest.")

    with pytest.raises(criteria.AmbiguousLead) as caught:
        criteria.drop(config, "", "every write has a door")
    assert "Block A, B" in str(caught.value)
    # Named, it lands — and takes the one it was told about.
    criteria.drop(config, "B", "every write has a door").save()
    body = read(Config.discover(tmp_path))
    assert body.count("Every write has a door") == 1
    assert body.index("Done when — Block A") < body.index("Every write has a door")


# -- the doors ----------------------------------------------------------------


def test_an_amend_keeps_the_bullet_where_it_sat(tmp_path):
    """`non-goal amend`'s whole argument: `add` appends, so drop-and-re-add moves a line in a
    list a reader takes for the shape of what finishing means."""
    config = written(tmp_path, "A", "Every governed file round-trips", "The gate holds it.")
    config = written(config, "A", "No line is over its limit", "The gate exits 1.")

    out = criteria.amend(config, "A", "every governed file round-trips", "docs/ holds it.")
    out.save()
    body = read(Config.discover(tmp_path))

    assert out.changed
    assert "docs/ holds it." in body
    # Still first, which is the property this verb exists for.
    assert body.index("Every governed file round-trips") < body.index("No line is over")


def test_an_amend_that_changes_nothing_writes_nothing(tmp_path):
    config = written(tmp_path, "A", "Every governed file round-trips", "The gate holds it.")
    before = read(config)
    out = criteria.amend(config, "A", "Every governed file round-trips", "The gate holds it.")

    assert not out.changed
    assert read(Config.discover(tmp_path)) == before


def test_the_heading_survives_the_last_criterion(tmp_path):
    """A block whose criteria all went is one somebody asked the question about, which is not a
    block nobody asked — and a verb that took the heading with the last bullet would erase that
    difference as a side effect of a correction."""
    config = written(tmp_path, "A", "Every governed file round-trips", "The gate holds it.")
    criteria.drop(config, "A", "every governed file round-trips").save()
    config = Config.discover(tmp_path)

    assert criteria.read(config.document("roadmap")) == ()
    assert criteria.blocks(config.document("roadmap")) == ("A",)
    assert "## Done when — Block A" in read(config)


def test_a_block_the_roadmap_does_not_plan_opens_no_list(tmp_path):
    """A heading nobody planned under is a list about work that does not exist, and the typo
    that produces one is invisible afterwards: the bullets read exactly like a block's."""
    config = project(tmp_path)
    with pytest.raises(KeyError) as caught:
        criteria.add(config, "Z", "Something is true", "Because of a reason.")

    assert "the labels declared here are A, B" in str(caught.value)
    assert "Done when" not in read(config)


def test_an_ungoverned_project_is_refused_at_the_write_and_read_anyway(tmp_path):
    """`scoping.NotGoverned`'s opt-in, and the read that is never refused beside it: a project
    that has not declared the table has to be able to discover that this is what it lacks."""
    config = project(tmp_path, governed=False)
    with pytest.raises(criteria.NotGoverned):
        criteria.add(config, "A", "Something is true", "Because of a reason.")
    assert criteria.read(config.document("roadmap")) == ()


# -- the limits and the gate --------------------------------------------------


def test_the_two_limits_are_the_criterias_own(tmp_path):
    """A criterion inheriting the non-goals' numbers would be judged by limits measured on a
    different corpus, which is why `[criteria]` is a table of its own."""
    (tmp_path / "roadkeep.toml").write_text(
        f'prefix = "RK"\n[files]\nroadmap = "{ROADMAP}"\nchangelog = "{CHANGELOG}"\n'
        "[criteria]\nlead = 20\nwhy = 40\n",
        encoding="utf-8",
    )
    for name, body in ((ROADMAP, BACKLOG), (CHANGELOG, LEDGER)):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            handle.write(body)
    config = Config.discover(tmp_path)

    with pytest.raises(SchemaError) as caught:
        criteria.add(config, "A", "A lead far past the twenty characters declared", "Short.")
    codes = [one.code for one in caught.value.violations]
    assert criteria.LEAD in codes
    assert config.criteria.lead == 20 and config.criteria.why == 40


def test_the_gate_reports_a_bullet_the_format_could_not_have_written(tmp_path):
    """The shape, and the door it names: the lead is the address, so a bullet whose head is its
    first sentence is repaired by removing it and writing one — an `amend` would impose the
    shape and move the address while doing it."""
    config = written(tmp_path, "A", "Every governed file round-trips", "The gate holds it.")
    body = read(config).replace(
        "- **Every governed file round-trips**",
        "- a bullet with no bold head. And a second sentence.\n- **Every governed file round-trips**",
    )
    (tmp_path / ROADMAP).write_text(body, encoding="utf-8", newline="")

    findings = lint(Config.discover(tmp_path)).findings
    assert [one.code for one in findings] == [criteria.SHAPE]
    # The subject is the lead as this file reads it, which is what makes the remedy a command.
    assert findings[0].token == "a bullet with no bold head"


def test_the_gate_is_silent_on_a_project_that_never_opted_in(tmp_path):
    """`scoping`'s adoption gate, one list over: an adopting project's `Done when` prose was
    written before this grammar, and a gate reporting on it before anybody opted in is one that
    gets bypassed rather than adopted."""
    body = BACKLOG.replace(
        "## Non-goals",
        "## Done when — Block A\n\n- a bullet nothing here could have written.\n\n## Non-goals",
    )
    config = project(tmp_path, roadmap=body, governed=False)
    assert not lint(config).findings
    # And with the table declared it is a finding, which is the other half of the opt-in.
    (tmp_path / "roadkeep.toml").write_text(
        (tmp_path / "roadkeep.toml").read_text(encoding="utf-8") + "[criteria]\n",
        encoding="utf-8",
    )
    assert lint(Config.discover(tmp_path)).findings


# -- the command line ---------------------------------------------------------


def test_the_commands_write_read_and_refuse(tmp_path, capsys):
    config = project(tmp_path)
    argv = ["-C", str(tmp_path), "criterion"]
    assert (
        main([*argv, "add", "--block", "A", "--lead", "Every file round-trips",
              "--why", "The gate holds it."])
        == EXIT_OK
    )
    out = capsys.readouterr().out
    assert "opened" in out and "Done when — Block A" in out

    assert main([*argv, "list", "--block", "A"]) == EXIT_OK
    assert "Every file round-trips" in capsys.readouterr().out

    assert main([*argv, "drop", "every file round-trips"]) == EXIT_OK
    capsys.readouterr()
    # The heading stays, and the listing says which empty this is.
    assert main([*argv, "list", "--block", "A"]) == EXIT_OK
    assert "declares a list and it is empty" in capsys.readouterr().out
    assert main(["-C", str(tmp_path), "lint"]) == EXIT_OK


def test_the_listing_tells_the_three_empties_apart(tmp_path, capsys):
    """Ungoverned, unasked, and all-dropped are three facts and not one: a reader who cannot
    tell them apart learns nothing from a blank list."""
    config = project(tmp_path, governed=False)
    assert main(["-C", str(tmp_path), "criterion", "list"]) == EXIT_OK
    assert "no [criteria]" in capsys.readouterr().out

    (tmp_path / "roadkeep.toml").write_text(
        (tmp_path / "roadkeep.toml").read_text(encoding="utf-8") + "[criteria]\n",
        encoding="utf-8",
    )
    assert main(["-C", str(tmp_path), "criterion", "list", "--block", "B"]) == EXIT_OK
    said = capsys.readouterr().out
    assert "no criteria for Block B" in said and "criterion add --block B" in said


def test_the_brief_prints_the_block_this_task_is_in(tmp_path, capsys):
    """The design's own requirement: printed by `brief` for that block, and scoped to it —
    another block's finish line is a claim the caller did not ask about."""
    config = written(tmp_path, "A", "Every file round-trips", "The gate holds it.")
    written(config, "B", "Every write has a door", "The guard denies the rest.")

    assert main(["-C", str(tmp_path), "brief", "RK1"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "done     Block A: Every file round-trips" in out
    assert "Every write has a door" not in out


# -- the other unit: a criterion addressed to the task (RK1268) ---------------


def test_a_criterion_is_addressed_to_a_line_as_well_as_to_a_block(tmp_path):
    """The defect. The unit an agent executes is the task, and three quarters of the spec were
    already addressable per line — the symptom, the non-goals and the design — while the
    checkable sentence was per block, which is the wrong altitude for the one that is cheap to
    write and read."""
    config = project(tmp_path)
    criteria.add(config, "RK1", "The pointer resolves after the write", "The gate holds it.").save()

    body = read(Config.discover(tmp_path))
    assert "## Done when — RK1" in body
    assert "- **The pointer resolves after the write** The gate holds it." in body
    assert lint(Config.discover(tmp_path)).findings == ()


def test_the_two_addresses_are_two_lists_and_one_lead_may_lead_both(tmp_path):
    # The rule the list already had, one address wider: a lead is unique inside its own list,
    # so the same words under a block and under a line are two claims about two units.
    config = written(tmp_path, "A", "Every write has a door", "The guard denies the rest.")
    criteria.add(config, "RK1", "Every write has a door", "This line's own.").save()

    config = Config.discover(tmp_path)
    assert criteria.leads(config.document("roadmap"), "A") == ("Every write has a door",)
    assert criteria.leads(config.document("roadmap"), "RK1") == ("Every write has a door",)
    assert lint(config).findings == ()


def test_an_id_no_line_carries_opens_no_list(tmp_path):
    # `_addressed`'s rule for a block, held on the stricter half: a block outlives its lines
    # and a task *is* one, so a list about work the ledger already holds is a question
    # somebody answered by shipping.
    config = project(tmp_path)
    before = read(config)
    with pytest.raises(KeyError) as caught:
        criteria.add(config, "RK9", "Never true", "Nothing checks it.")

    assert "no open line RK9" in str(caught.value)
    assert read(Config.discover(tmp_path)) == before


def test_the_brief_prints_the_task_s_own_beside_its_block_s(tmp_path, capsys):
    """The design's requirement: the two altitudes side by side, each carrying its address —
    printed as one list they would read as one claim, which is the conflation this ends."""
    config = written(tmp_path, "A", "Every file round-trips", "The gate holds it.")
    criteria.add(config, "RK1", "The pointer resolves", "The gate holds that too.").save()

    assert main(["-C", str(tmp_path), "brief", "RK1"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "done     RK1: The pointer resolves" in out
    assert "done     Block A: Every file round-trips" in out


def test_the_line_takes_its_own_list_with_it_when_it_ships(tmp_path):
    """The queue entry's rule one list over (RK327): the heading is addressed by an id this
    write spends, so there is no state where the line has left and a heading still asks what
    would finish it. The block's list stays — that one outlives its lines."""
    from roadkeep.shipping import ship

    config = written(tmp_path, "A", "Every file round-trips", "The gate holds it.")
    criteria.add(config, "RK1", "The pointer resolves", "The gate holds that too.").save()
    config = Config.discover(tmp_path)
    departure = ship(config, "RK1", why="The first symptom no longer happens.")
    departure.save()

    body = read(Config.discover(tmp_path))
    assert "## Done when — RK1" not in body
    assert "## Done when — Block A" in body
    assert departure.unmet == ("The pointer resolves",)
    assert lint(Config.discover(tmp_path)).findings == ()


def test_naming_both_addresses_is_refused_before_anything_is_read(tmp_path, capsys):
    # Two addresses on one call is a caller who believes both took effect, and the wrong one
    # is a claim about somebody else's finish line.
    project(tmp_path)
    assert main(
        [
            "-C", str(tmp_path), "criterion", "add",
            "--block", "A", "--task", "RK1",
            "--lead", "Ambiguous", "--why", "Nothing decides it.",
        ]
    ) != EXIT_OK
    assert "--block and --task" in capsys.readouterr().err


def test_add_with_no_address_names_both_doors(tmp_path, capsys):
    # `add` writes the bullet, so there is no lead on file for the address to be looked up
    # from — refused here and not by argparse, the same rule reaching MCP where a required
    # group says nothing.
    project(tmp_path)
    assert main(
        ["-C", str(tmp_path), "criterion", "add", "--lead", "Nowhere", "--why", "Unplaced."]
    ) != EXIT_OK
    said = capsys.readouterr().err
    assert "--block <x> or --task <id>" in said


def test_the_listing_names_the_flag_that_opens_the_list_it_found_empty(tmp_path, capsys):
    # RK420's rule: a remedy is a command the caller can run, so an address that is an id is
    # reached by `--task` and never by `--block`.
    project(tmp_path)
    assert main(["-C", str(tmp_path), "criterion", "list", "--task", "RK1"]) == EXIT_OK
    assert "criterion add --task RK1" in capsys.readouterr().out
