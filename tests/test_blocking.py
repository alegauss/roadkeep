"""The key to a door both halves of this tool were right to lock (RK141).

Measured shipping the first task of a new block: `ship` refused an undeclared block and
wrote nothing, which is correct — naming a block is editorial, and a heading the tool
guesses is a heading nobody looks under. The guard then denied the one-line edit that would
declare it, listing every verb that may write there, none of which adds a heading.

So the test of this module is not that a heading can be written. It is that **neither
refusal had to be weakened**: the label and the title are the author's, and the level, the
separator and the place are the file's own.

**And that appended was a placement rather than the placement** (RK145). `--after <label>` is
under test as a *neighbour* and not an index: two files ordering their blocks differently each
place the heading after their own copy of that one, and a file that cannot find it is refused
rather than appended, because falling back there orders one file by a rule the others ignored.

**And that the key can close the door** (RK144). The verb that writes a heading was the only
one, so a label typed wrongly was three headings only a hand-edit could remove. What the
removal is tested for is its narrowness: a heading is taken out only where its subtree is
blank, anything filed under the label is **named** in a refusal that writes nothing, and the
ledger keeps its heading because history is filed under it.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from roadkeep.blocking import (
    BlockExists,
    BlockOccupied,
    NoSuchBlock,
    NoSuchNeighbour,
    NotALabel,
    NotOrganisable,
    NothingToDrop,
    drop_block,
    open_block,
)
from roadkeep.authoring import place
from roadkeep.cli import EXIT_OK, EXIT_USAGE, main
from roadkeep.config import Config
from roadkeep.deferring import defer
from roadkeep.linting import lint
from roadkeep.shipping import ship

ROADMAP = "docs/ROADMAP.md"
CHANGELOG = "docs/CHANGELOG.md"
IMPROVEMENTS = "docs/IMPROVEMENTS.md"

BACKLOG = """# Roadmap

## Block A — The model

- 📋 **RK1** (deps: —) **A first symptom** — Because of a reason. → §RK1

## Block B — Authoring

- 📋 **RK2** (deps: —) **A second symptom** — Because of another. → §RK2

## Non-goals

- **No web UI.** Files and a CLI.
"""

LEDGER = """# Shipped

## Block A — The model

## Block B — Authoring
"""

RATIONALE = """# Improvements

## Block A — The model

### §RK1 A first design

The reasoning the line has no room for.

## Block B — Authoring

### §RK2 A second design

The reasoning for the other one.
"""


def project(
    tmp_path: Path,
    *,
    roadmap: str = BACKLOG,
    changelog: str = LEDGER,
    improvements: str = RATIONALE,
    config: str = "",
) -> Config:
    (tmp_path / "roadkeep.toml").write_text(
        config
        or (
            'prefix = "RK"\n[files]\n'
            f'roadmap = "{ROADMAP}"\nchangelog = "{CHANGELOG}"\n'
            f'improvements = "{IMPROVEMENTS}"\n'
        ),
        encoding="utf-8",
    )
    for name, body in {
        ROADMAP: roadmap,
        CHANGELOG: changelog,
        IMPROVEMENTS: improvements,
    }.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            handle.write(body)
    return Config.discover(tmp_path)


def read(config: Config, name: str) -> str:
    with (config.root / name).open("r", encoding="utf-8", newline="") as handle:
        return handle.read()


# -- the deadlock -------------------------------------------------------------


def test_a_block_no_file_declares_can_be_opened_and_then_shipped_into(tmp_path):
    # The whole task, end to end: the refusal `ship` gives is right, and this is what makes
    # it survivable without the edit the guard denies.
    config = project(tmp_path)
    from roadkeep.kernel.document import UnknownBlock

    open_block(config, "C", "Query").save()

    config = Config.discover(tmp_path)
    assert "## Block C — Query" in read(config, CHANGELOG)
    # And the roadmap can now carry a line under it, which `ship` can move across.
    from roadkeep.authoring import add as add_task

    add_task(
        config,
        block="C",
        symptom="A third symptom",
        why="Because of a third reason.",
        section=("A third design", "The reasoning for it."),
    )
    ship(Config.discover(tmp_path), "RK3", why="It works now.").save()
    assert "**RK3**" in read(Config.discover(tmp_path), CHANGELOG)
    assert lint(Config.discover(tmp_path)).clean
    assert UnknownBlock  # imported to name what this test exists to stop happening


def test_the_heading_lands_after_the_last_block_and_never_at_the_end(tmp_path):
    # The roadmap's `## Non-goals` follows the blocks, so appending would file the first
    # task of the new block under a heading that is not a block at all.
    config = project(tmp_path)
    open_block(config, "C", "Query").save()

    lines = read(config, ROADMAP).splitlines()
    assert lines.index("## Block C — Query") < lines.index("## Non-goals")
    assert lines.index("## Block B — Authoring") < lines.index("## Block C — Query")
    # The line that belonged to Block B is still under Block B.
    assert lines.index("- 📋 **RK2** (deps: —) **A second symptom** — Because of another. → §RK2") < lines.index(
        "## Block C — Query"
    )


def test_every_file_organised_by_blocks_gets_it(tmp_path):
    config = project(tmp_path)
    opened = open_block(config, "C", "Query")
    opened.save()

    assert set(opened.documents) == {"roadmap", "changelog", "improvements"}
    for name in (ROADMAP, CHANGELOG, IMPROVEMENTS):
        assert "## Block C — Query" in read(config, name)


def test_a_file_that_is_not_organised_by_blocks_is_named_and_left_alone(tmp_path):
    # A heading here would be the first of its kind, which is a decision about the file's
    # shape rather than about a block — and a file skipped in silence is one the author
    # discovers was skipped by the next command that refuses on it.
    config = project(tmp_path, improvements="# Improvements\n\n### §0.1 A preface\n\nProse.\n")
    opened = open_block(config, "C", "Query")
    opened.save()

    assert set(opened.documents) == {"roadmap", "changelog"}
    # And the reason names the argument that writes it anyway (RK405), so the author does
    # not learn the way out from the next command that refuses.
    assert opened.skipped == (
        (IMPROVEMENTS, "declares no block; --organise improvements writes the first one"),
    )
    assert "Block C" not in read(config, IMPROVEMENTS)


# -- the duplicate one of two headings the removal may take (RK417) ----------

ONLY_B = """# Improvements

## Block B — Authoring
"""


def test_the_empty_heading_is_taken_even_where_it_is_the_second(tmp_path):
    # Reading the first alone was right while a label had one heading. On a file declaring
    # it twice it refused over the occupied one while an empty one sat below — and the
    # corpus this was measured on happened to have them the other way round.
    doubled = BACKLOG.replace(
        "## Non-goals", "## Block A — The model again\n\n## Non-goals"
    )
    # The rationale file is left out of it: it declares Block A over a section, which is
    # work, and this removal is all-or-nothing across the governed set.
    config = project(tmp_path, roadmap=doubled, improvements=ONLY_B)
    closed = drop_block(config, "A")
    closed.save()

    text = read(config, ROADMAP)
    # The occupied one stayed, with its line under it; the empty one went.
    assert text.count("## Block A") == 1
    assert "**RK1**" in text and "## Block A — The model again" not in text


def test_a_label_whose_every_heading_holds_work_is_still_refused(tmp_path):
    doubled = BACKLOG.replace(
        "## Non-goals",
        "## Block A — The model again\n\n"
        "- 📋 **RK3** (deps: —) **A third symptom** — Because of a third. → §RK3\n\n"
        "## Non-goals",
    )
    config = project(tmp_path, roadmap=doubled, improvements=ONLY_B)
    with pytest.raises(BlockOccupied):
        drop_block(config, "A")
    # A heading over work is never removed: the rule is per heading, not per file.
    assert read(config, ROADMAP).count("## Block A") == 2


# -- the file organised by nothing, and the key to it (RK405) ----------------

FLAT = "# Shipped\n\nProse, and no block heading anywhere in it.\n"


def test_the_first_heading_is_written_where_the_author_asks_for_it(tmp_path):
    # Measured: `ship` refused naming this verb, this verb skipped the file, and a fresh
    # label skipped it too — so no argument to any command put a heading there.
    config = project(tmp_path, changelog=FLAT)
    opened = open_block(config, "A", "The model", organise=["changelog"])
    opened.save()

    ledger = read(config, CHANGELOG)
    # Spelled the project's way, not this module's, and at the end: there is no block
    # subtree to follow and no `--after` to resolve against.
    # The blank on either side is `_insert`'s, and the same one every other heading gets.
    assert ledger == FLAT + "\n## Block A — The model\n\n"
    assert opened.rendered["changelog"] == "## Block A — The model"


def test_the_first_heading_goes_before_the_section_the_blocks_precede(tmp_path):
    # RK413, measured: appended at the end, the roadmap's `## Non-goals` swallowed the new
    # block and every task added to it — the one placement the ordinary path refuses by name.
    config = project(
        tmp_path,
        roadmap="# Roadmap\n\n## Non-goals\n\n- **No web UI.** Files and a CLI.\n",
    )
    opened = open_block(config, "A", "The model", organise=["roadmap"])
    opened.save()

    assert read(config, ROADMAP) == (
        "# Roadmap\n\n## Block A — The model\n\n## Non-goals\n\n- **No web UI.** Files and a CLI.\n"
    )


def test_a_file_with_no_section_at_that_level_still_takes_the_end(tmp_path):
    # The flat ledger this door was built for: nothing marks where the region stops, so the
    # end of the file is right after all. One rule, both shapes.
    config = project(tmp_path, changelog=FLAT)
    open_block(config, "A", "The model", organise=["changelog"]).save()
    assert read(config, CHANGELOG) == FLAT + "\n## Block A — The model\n\n"


def test_the_ship_that_refused_goes_through_afterwards(tmp_path):
    config = project(tmp_path, changelog=FLAT)
    open_block(config, "A", "The model", organise=["changelog"]).save()
    shipped = ship(config, "RK1", why="It works now.")
    shipped.save()
    assert "**RK1**" in read(config, CHANGELOG)


def test_the_refusal_names_the_argument_that_opens_the_file(tmp_path):
    # The obligation is stated by the command that created it, never discovered from the
    # backstop: the bare `block add` skips this file, so naming it alone is one more refusal.
    config = project(tmp_path, changelog=FLAT)
    with pytest.raises(ValueError) as raised:
        ship(config, "RK1", why="It works now.")
    assert 'block add A --title "<its title>" --organise changelog' in str(raised.value)


def test_every_door_names_its_own_file_without_being_told_twice(tmp_path):
    # RK412: the path and the role were two arguments, and `defer` passed the first and not
    # the second — so a store organised by nothing got the bare `block add`, which skips it.
    # Derived from one role, the door that nobody remembered says the right thing.
    config = project(
        tmp_path,
        config=(
            'prefix = "RK"\n[files]\n'
            f'roadmap = "{ROADMAP}"\nchangelog = "{CHANGELOG}"\n'
            f'improvements = "{IMPROVEMENTS}"\ndeferred = "docs/DEFERRED.md"\n'
        ),
    )
    (tmp_path / "docs" / "DEFERRED.md").write_text(
        "# Deferred\n\nProse, and no block heading anywhere in it.\n", encoding="utf-8"
    )
    with pytest.raises(ValueError) as raised:
        defer(config, "RK1", reason="Waiting on something.")
    assert 'block add A --title "<its title>" --organise deferred' in str(raised.value)


def test_the_path_and_the_role_are_two_answers_to_one_question(tmp_path):
    # Refused, because the role derives the path: honouring either would let the two drift
    # in the one place this whole argument exists to keep them together.
    config = project(tmp_path)
    with pytest.raises(ValueError) as raised:
        place(
            config.document("roadmap"),
            config.document("roadmap").entries[0].task,
            where=ROADMAP,
            role="roadmap",
            config=config,
        )
    assert "not both" in str(raised.value)


def test_a_ledger_that_declares_blocks_hears_nothing_about_organising(tmp_path):
    # Spent where the file has a heading of its own: `block add` writes there already.
    config = project(tmp_path, changelog="# Shipped\n\n## Block Z — Something else\n")
    with pytest.raises(ValueError) as raised:
        ship(config, "RK1", why="It works now.")
    assert "--organise" not in str(raised.value)


def test_a_role_the_project_does_not_declare_is_refused_by_name(tmp_path):
    config = project(tmp_path, changelog=FLAT)
    with pytest.raises(NotOrganisable) as raised:
        open_block(config, "C", "Query", organise=["deferred"])
    message = str(raised.value)
    assert "--organise deferred" in message and "changelog, improvements, roadmap" in message
    assert read(config, CHANGELOG) == FLAT


def test_a_project_with_no_block_anywhere_is_init_s_and_not_this_verb_s(tmp_path):
    # There is no level and no separator to read, and punctuation invented here would be a
    # second convention in a project that has one.
    config = project(
        tmp_path,
        roadmap="# Roadmap\n\nProse.\n",
        changelog=FLAT,
        improvements="# Improvements\n\nProse.\n",
    )
    with pytest.raises(NotOrganisable) as raised:
        open_block(config, "A", "The model", organise=["changelog"])
    assert "`init` scaffolds" in str(raised.value)
    assert read(config, CHANGELOG) == FLAT


# -- what is derived, per file ------------------------------------------------


def test_the_level_and_the_separator_are_the_files_own(tmp_path):
    # A project writing `### Fase 2 - Execução` gets one more of those: a tool answering
    # with its own punctuation writes a second convention into a file that has one.
    config = project(
        tmp_path,
        roadmap="# Roadmap\n\n### Fase 1 - Começo\n\n### Fase 2 - Execução\n",
        config='prefix = "RK"\n[headings]\nword = "Fase"\n[files]\n'
        f'roadmap = "{ROADMAP}"\nchangelog = "{CHANGELOG}"\n',
        changelog="# Shipped\n\n### Fase 1 - Começo\n",
    )
    opened = open_block(config, "3", "Entrega")
    opened.save()

    assert opened.rendered["roadmap"] == "### Fase 3 - Entrega"
    assert "### Fase 3 - Entrega" in read(config, ROADMAP)


def test_a_heading_with_no_separator_still_gets_one(tmp_path):
    config = project(
        tmp_path,
        roadmap="# Roadmap\n\n## Block A The model\n",
        changelog="# Shipped\n\n## Block A The model\n",
        improvements="# Improvements\n\n## Block A The model\n",
    )
    opened = open_block(config, "B", "Authoring")
    opened.save()
    assert opened.rendered["roadmap"] == "## Block B Authoring"


def test_the_heading_gets_the_blank_lines_a_heading_needs(tmp_path):
    config = project(tmp_path)
    open_block(config, "C", "Query").save()
    lines = read(config, CHANGELOG).splitlines()
    at = lines.index("## Block C — Query")
    assert lines[at - 1] == "" and lines[at + 1] == ""


def test_the_file_still_round_trips_and_lints_clean(tmp_path):
    config = project(tmp_path)
    open_block(config, "C", "Query").save()
    after = Config.discover(tmp_path)
    assert after.document("roadmap").non_canonical == ()
    assert lint(after).clean


# -- the refusals -------------------------------------------------------------


def test_a_label_the_format_cannot_read_is_refused(tmp_path):
    config = project(tmp_path)
    with pytest.raises(NotALabel):
        open_block(config, "a label with spaces", "Query")
    assert read(config, ROADMAP) == BACKLOG


def test_an_empty_title_is_refused_rather_than_written(tmp_path):
    config = project(tmp_path)
    with pytest.raises(NotALabel):
        open_block(config, "C", "   ")
    assert read(config, ROADMAP) == BACKLOG


def test_a_label_every_file_already_declares_is_refused(tmp_path):
    # A command that exits 0 having written nothing teaches that it wrote something.
    config = project(tmp_path)
    with pytest.raises(BlockExists) as caught:
        open_block(config, "B", "Authoring again")
    assert ROADMAP in str(caught.value)
    assert read(config, ROADMAP) == BACKLOG


def test_a_label_only_one_file_lacks_is_written_only_there(tmp_path):
    # The half-declared state the pair used to leave: `add` works and `ship` fails on one
    # label, which is the deadlock again with one more step in it.
    config = project(tmp_path, changelog="# Shipped\n\n## Block A — The model\n")
    opened = open_block(config, "B", "Authoring")
    opened.save()

    assert set(opened.documents) == {"changelog"}
    assert "## Block B — Authoring" in read(config, CHANGELOG)
    assert read(config, ROADMAP) == BACKLOG


# -- the command --------------------------------------------------------------


def test_the_command_names_every_file_it_wrote(tmp_path, capsys):
    project(tmp_path)
    assert main(["-C", str(tmp_path), "block", "add", "C", "--title", "Query"]) == EXIT_OK
    printed = capsys.readouterr().out
    assert printed.startswith("Block C declared: Query")
    assert f"{CHANGELOG}   :7  ## Block C — Query" in printed


def test_the_command_refuses_with_two_and_writes_nothing(tmp_path, capsys):
    config = project(tmp_path)
    code = main(["-C", str(tmp_path), "block", "add", "B", "--title", "Again"])
    assert code == EXIT_USAGE
    assert "already declared" in capsys.readouterr().err
    assert read(config, ROADMAP) == BACKLOG


def test_json_says_what_was_written_and_what_was_not(tmp_path, capsys):
    project(tmp_path, improvements="# Improvements\n\n### §0.1 A preface\n\nProse.\n")
    code = main(
        ["-C", str(tmp_path), "block", "add", "C", "--title", "Query", "--json"]
    )
    assert code == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["label"] == "C" and payload["title"] == "Query"
    assert [w["role"] for w in payload["written"]] == ["roadmap", "changelog"]
    assert payload["skipped"][0]["file"] == IMPROVEMENTS


# -- a placement, not the placement (RK145) -----------------------------------


def test_a_block_can_be_opened_between_two_existing_ones(tmp_path):
    # Block order is what `list` reports and what a reader takes for the shape of the plan,
    # so a phase belonging between two existing ones had no route but reordering by hand.
    config = project(tmp_path)
    opened = open_block(config, "C", "Query", after="A")
    opened.save()

    assert opened.after == "A"
    lines = read(config, ROADMAP).splitlines()
    assert lines.index("## Block A — The model") < lines.index("## Block C — Query")
    assert lines.index("## Block C — Query") < lines.index("## Block B — Authoring")
    # And Block A keeps its own line: the heading goes after that block's whole subtree.
    assert lines.index("- 📋 **RK1** (deps: —) **A first symptom** — Because of a reason. → §RK1") < lines.index(
        "## Block C — Query"
    )


def test_the_order_a_list_reports_is_the_one_the_heading_was_opened_into(tmp_path):
    # The claim the argument exists for: this is a read, and it reads the headings' own order.
    config = project(tmp_path)
    open_block(config, "C", "Query", after="A").save()
    after = Config.discover(tmp_path)
    assert [h.label for h in after.document("roadmap").headings if h.label] == ["A", "C", "B"]
    assert lint(after).clean


def test_the_neighbour_is_resolved_in_every_file_that_wants_the_heading(tmp_path):
    config = project(tmp_path)
    open_block(config, "C", "Query", after="A").save()
    for name in (ROADMAP, CHANGELOG, IMPROVEMENTS):
        labels = [
            line for line in read(config, name).splitlines() if line.startswith("## Block")
        ]
        assert labels == ["## Block A — The model", "## Block C — Query", "## Block B — Authoring"]


def test_a_neighbour_is_read_per_file_and_not_as_a_position(tmp_path):
    # Two files that order their blocks differently each keep their own sequence, which is
    # what makes one argument honest across them: `--after A` is a neighbour, not an index.
    config = project(
        tmp_path,
        changelog="# Shipped\n\n## Block B — Authoring\n\n## Block A — The model\n",
        improvements="# Improvements\n\n## Block A — The model\n\n## Block B — Authoring\n",
    )
    open_block(config, "C", "Query", after="A").save()
    assert [
        line for line in read(config, CHANGELOG).splitlines() if line.startswith("## Block")
    ] == ["## Block B — Authoring", "## Block A — The model", "## Block C — Query"]
    assert [
        line for line in read(config, IMPROVEMENTS).splitlines() if line.startswith("## Block")
    ] == ["## Block A — The model", "## Block C — Query", "## Block B — Authoring"]


def test_a_neighbour_a_file_does_not_declare_is_refused_and_never_appended(tmp_path):
    # Falling back to the end in the one file that cannot resolve it would order that file by
    # a rule the others did not use — a disagreement both halves round-trip.
    config = project(tmp_path, changelog="# Shipped\n\n## Block A — The model\n")
    with pytest.raises(NoSuchNeighbour) as caught:
        open_block(config, "C", "Query", after="B")
    assert CHANGELOG in str(caught.value) and "declares: A" in str(caught.value)
    assert read(config, ROADMAP) == BACKLOG
    assert read(config, CHANGELOG) == "# Shipped\n\n## Block A — The model\n"


def test_a_block_opened_after_itself_is_refused(tmp_path):
    config = project(tmp_path)
    with pytest.raises(NotALabel):
        open_block(config, "C", "Query", after="C")
    assert read(config, ROADMAP) == BACKLOG


def test_omitting_the_neighbour_still_appends_and_says_it_derived_one(tmp_path):
    # The default is the whole of the old behaviour, so nothing about the common case moved.
    config = project(tmp_path)
    opened = open_block(config, "C", "Query")
    opened.save()
    assert opened.after is None
    lines = read(config, ROADMAP).splitlines()
    assert lines.index("## Block B — Authoring") < lines.index("## Block C — Query")


def test_the_heading_between_two_blocks_gets_its_blank_lines(tmp_path):
    config = project(tmp_path)
    open_block(config, "C", "Query", after="A").save()
    body = read(config, ROADMAP)
    assert "\n\n\n" not in body
    lines = body.splitlines()
    at = lines.index("## Block C — Query")
    assert lines[at - 1] == "" and lines[at + 1] == ""
    assert Config.discover(tmp_path).document("roadmap").non_canonical == ()


def test_the_command_names_the_neighbour_it_was_given(tmp_path, capsys):
    project(tmp_path)
    code = main(
        ["-C", str(tmp_path), "block", "add", "C", "--title", "Query", "--after", "A"]
    )
    assert code == EXIT_OK
    assert capsys.readouterr().out.startswith("Block C declared (after Block A): Query")


def test_the_add_json_carries_the_neighbour_or_null(tmp_path, capsys):
    project(tmp_path)
    assert main(
        ["-C", str(tmp_path), "block", "add", "C", "--title", "Query", "--after", "A", "--json"]
    ) == EXIT_OK
    assert json.loads(capsys.readouterr().out)["after"] == "A"
    assert main(
        ["-C", str(tmp_path), "block", "add", "D", "--title", "Gate", "--json"]
    ) == EXIT_OK
    assert json.loads(capsys.readouterr().out)["after"] is None


# -- the door the key could not close (RK144) ---------------------------------


def test_a_label_opened_by_mistake_is_withdrawn_from_every_file(tmp_path):
    # The whole task, and the inverse of the first test in this file: the heading a verb
    # wrote is one the same verb can take back, so the mistake costs a command.
    config = project(tmp_path)
    open_block(config, "C", "Qeury").save()
    closed = drop_block(Config.discover(tmp_path), "C")
    closed.save()

    assert set(closed.documents) == {"roadmap", "changelog", "improvements"}
    assert closed.rendered["roadmap"] == "## Block C — Qeury"
    # Byte-identical to the file before the label ever existed, which is the claim: the
    # blanks the heading was given come out with it.
    assert read(config, ROADMAP) == BACKLOG
    assert read(config, CHANGELOG) == LEDGER
    assert read(config, IMPROVEMENTS) == RATIONALE
    assert lint(Config.discover(tmp_path)).clean


def test_a_heading_over_an_open_line_is_refused_by_name(tmp_path):
    # The safety of the whole door: removing this heading files RK2 under Block A, silently
    # and in a way that round-trips, which is exactly why nothing downstream would catch it.
    config = project(tmp_path)
    with pytest.raises(BlockOccupied) as caught:
        drop_block(config, "B")
    assert "RK2" in str(caught.value) and ROADMAP in str(caught.value)
    assert read(config, ROADMAP) == BACKLOG


def test_a_rationale_section_is_work_the_same_way_a_line_is(tmp_path):
    # A block heading owns three kinds of thing, and a section orphaned by a removed heading
    # is the same silent misfiling as an orphaned task line.
    config = project(
        tmp_path,
        roadmap="# Roadmap\n\n## Block A — The model\n\n## Block B — Authoring\n",
        changelog="# Shipped\n\n## Block A — The model\n\n## Block B — Authoring\n",
    )
    with pytest.raises(BlockOccupied) as caught:
        drop_block(config, "B")
    assert "§RK2 A second design" in str(caught.value)
    assert read(config, IMPROVEMENTS) == RATIONALE


def test_a_blocks_own_prose_is_named_by_the_line_it_is_on(tmp_path):
    # Loose prose has no other address, and a paragraph left behind by a removed heading is
    # filed under the block above it (RK108's introduction, one block over).
    config = project(
        tmp_path,
        roadmap="# Roadmap\n\n## Block A — The model\n\n## Block B — Authoring\n\nWhat this block is for.\n",
        changelog="# Shipped\n\n## Block A — The model\n\n## Block B — Authoring\n",
        improvements="# Improvements\n\n## Block A — The model\n\n## Block B — Authoring\n",
    )
    with pytest.raises(BlockOccupied) as caught:
        drop_block(config, "B")
    assert "line 7" in str(caught.value)


# -- the note that had no door (RK237) ----------------------------------------

#: The shape adoption produces: a blockquote saying what the block is, and saying that
#: everything under it shipped. Turing's roadmap carried ten, four over blocks with no open
#: line left — so the block that most needed withdrawing was the one whose note said so.
NOTED = """# Roadmap

## Block A — The model

- 📋 **RK1** (deps: —) **A first symptom** — Because of a reason. → §RK1

## Block B — Authoring

> Everything here shipped; see the changelog.
> Kept as a marker of where the work was.
"""

#: Block A's design kept, Block B's heading standing over nothing: the state a withdrawal
#: leaves behind, and the one `lint` has to call clean once the note is gone.
BARE = (
    "# Improvements\n\n## Block A — The model\n\n### §RK1 A first design\n\n"
    "The reasoning the line has no room for.\n\n## Block B — Authoring\n"
)


def noted(tmp_path: Path) -> Config:
    return project(
        tmp_path,
        roadmap=NOTED,
        changelog="# Shipped\n\n## Block A — The model\n\n## Block B — Authoring\n",
        improvements=BARE,
    )


def test_the_refusal_over_a_note_names_the_flag_that_takes_it(tmp_path):
    # Until this, the message was the whole exit from the corner: `block drop` refused, no verb
    # wrote or removed a note, and what was left was an `Edit` the guard denies and a `Bash`
    # write RK175 reports as unattested.
    config = noted(tmp_path)
    with pytest.raises(BlockOccupied) as caught:
        drop_block(config, "B")
    assert "loose prose and not work" in str(caught.value)
    assert "--prose" in str(caught.value)
    assert read(config, ROADMAP) == NOTED


def test_the_flag_takes_the_note_with_the_heading(tmp_path):
    config = noted(tmp_path)
    closed = drop_block(config, "B", prose=True)
    assert closed.notes == {"roadmap": 2}  # the improvements heading stood over nothing
    closed.save()
    body = read(config, ROADMAP)
    assert "Block B" not in body and "Everything here shipped" not in body
    # Block A is untouched, which is what a removal that took a paragraph has to prove.
    assert "- 📋 **RK1**" in body
    assert lint(Config.discover(tmp_path)).clean


def test_the_flag_never_takes_work(tmp_path):
    # Opt-in is about the *kind*, not about the caller's confidence: a task line or a nested
    # heading under the label is somebody's, and no flag makes a removal the right verb.
    config = project(tmp_path, improvements=BARE)
    with pytest.raises(BlockOccupied) as caught:
        drop_block(config, "B", prose=True)
    assert "RK2" in str(caught.value) and "--prose" not in str(caught.value)
    assert read(config, ROADMAP) == BACKLOG


def test_a_note_over_a_section_is_still_refused(tmp_path):
    # Prose *and* work under one heading is work under one heading: the flag has nothing to
    # do here, and taking the note alone would be a partial removal nobody asked for.
    config = project(tmp_path, roadmap=NOTED)
    with pytest.raises(BlockOccupied) as caught:
        drop_block(config, "B", prose=True)
    assert "§RK2 A second design" in str(caught.value)
    assert read(config, IMPROVEMENTS) == RATIONALE


def test_the_command_says_the_note_went(tmp_path, capsys):
    # The one line of the removal that took prose, said: the file no longer holds it to be
    # compared against, so silence about it reads exactly like a heading over nothing.
    noted(tmp_path)
    assert main(["-C", str(tmp_path), "block", "drop", "B", "--prose"]) == EXIT_OK
    assert "note     2 line(s) of prose taken with the heading" in capsys.readouterr().out


def test_the_json_carries_the_note_as_a_field(tmp_path, capsys):
    noted(tmp_path)
    argv = ["-C", str(tmp_path), "block", "drop", "B", "--prose", "--json"]
    assert main(argv) == EXIT_OK
    removed = {r["role"]: r["note"] for r in json.loads(capsys.readouterr().out)["removed"]}
    # Three files declared the label; only the roadmap's heading stood over anything.
    assert removed == {"roadmap": 2, "changelog": None, "improvements": None}


def test_the_refusal_without_the_flag_is_still_the_one_for_work(tmp_path):
    # The message every project already saw, unchanged where the heading stands over work.
    config = project(tmp_path, improvements=BARE)
    with pytest.raises(BlockOccupied) as caught:
        drop_block(config, "B")
    assert "a heading over work is not an empty heading" in str(caught.value)


def test_the_ledger_keeps_its_heading_and_the_others_lose_theirs(tmp_path):
    # The exception, and the reason it is not an inconsistency: history is filed under that
    # heading for ever, so entries there are neither a refusal nor a removal.
    config = project(
        tmp_path,
        roadmap="# Roadmap\n\n## Block A — The model\n\n## Block B — Authoring\n",
        changelog=LEDGER + "\n- ✅ **RK2** **A second symptom** — It works now.\n",
        improvements="# Improvements\n\n## Block A — The model\n\n## Block B — Authoring\n",
    )
    closed = drop_block(config, "B")
    closed.save()

    assert set(closed.documents) == {"roadmap", "improvements"}
    assert closed.skipped[0][0] == CHANGELOG and "1 entry" in closed.skipped[0][1]
    assert "Block B" not in read(config, ROADMAP)
    assert "## Block B — Authoring" in read(config, CHANGELOG)


def test_a_label_only_the_ledger_declares_is_refused_rather_than_reported_clean(tmp_path):
    config = project(
        tmp_path,
        roadmap="# Roadmap\n\n## Block A — The model\n",
        changelog=LEDGER + "\n- ✅ **RK2** **A second symptom** — It works now.\n",
        improvements="# Improvements\n\n## Block A — The model\n",
    )
    with pytest.raises(NothingToDrop) as caught:
        drop_block(config, "B")
    assert CHANGELOG in str(caught.value)


def test_a_label_no_file_declares_lists_the_ones_they_do(tmp_path):
    # The commonest reason this door is reached: a label spelled differently from the file's.
    config = project(tmp_path)
    with pytest.raises(NoSuchBlock) as caught:
        drop_block(config, "Z")
    assert "A, B" in str(caught.value)


def test_the_last_block_in_a_file_leaves_no_trailing_blank(tmp_path):
    # A paragraph break the file never had is still a change, and both spellings round-trip.
    config = project(
        tmp_path,
        roadmap="# Roadmap\n\n## Block A — The model\n\n## Block B — Authoring\n",
        changelog="# Shipped\n\n## Block A — The model\n\n## Block B — Authoring\n",
        improvements="# Improvements\n\n## Block A — The model\n\n## Block B — Authoring\n",
    )
    drop_block(config, "B").save()
    assert read(config, ROADMAP) == "# Roadmap\n\n## Block A — The model\n"


def test_a_middle_block_leaves_no_doubled_blank(tmp_path):
    config = project(
        tmp_path,
        roadmap="# Roadmap\n\n## Block A — The model\n\n## Block B — Authoring\n\n## Non-goals\n\n- **No web UI.** Files and a CLI.\n",
        changelog="# Shipped\n\n## Block A — The model\n\n## Block B — Authoring\n",
        improvements="# Improvements\n\n## Block A — The model\n\n## Block B — Authoring\n",
    )
    drop_block(config, "B").save()
    body = read(config, ROADMAP)
    assert "\n\n\n" not in body
    assert body == "# Roadmap\n\n## Block A — The model\n\n## Non-goals\n\n- **No web UI.** Files and a CLI.\n"
    assert Config.discover(tmp_path).document("roadmap").non_canonical == ()


def test_a_partial_removal_is_never_written(tmp_path):
    # All of the files or none of them, as `block add` has it: a heading gone from the ledger
    # while the roadmap keeps its open lines is `add` working and `ship` failing.
    config = project(tmp_path, changelog=LEDGER, improvements=RATIONALE)
    with pytest.raises(BlockOccupied):
        drop_block(config, "B")
    assert read(config, CHANGELOG) == LEDGER
    assert read(config, IMPROVEMENTS) == RATIONALE


def test_the_drop_command_names_every_heading_it_took_out(tmp_path, capsys):
    project(tmp_path)
    open_block(Config.discover(tmp_path), "C", "Query").save()
    assert main(["-C", str(tmp_path), "block", "drop", "C"]) == EXIT_OK
    printed = capsys.readouterr().out
    assert printed.startswith("Block C withdrawn")
    assert "## Block C — Query" in printed


def test_the_drop_command_refuses_with_two_and_writes_nothing(tmp_path, capsys):
    config = project(tmp_path)
    assert main(["-C", str(tmp_path), "block", "drop", "B"]) == EXIT_USAGE
    assert "RK2" in capsys.readouterr().err
    assert read(config, ROADMAP) == BACKLOG


def test_the_drop_json_says_which_heading_left_which_file(tmp_path, capsys):
    project(tmp_path)
    open_block(Config.discover(tmp_path), "C", "Query").save()
    assert main(["-C", str(tmp_path), "block", "drop", "C", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["label"] == "C"
    assert [r["role"] for r in payload["removed"]] == [
        "roadmap",
        "changelog",
        "improvements",
    ]
    assert payload["removed"][0]["rendered"] == "## Block C — Query"


# -- the key the pair never cut: a doubled heading folded into the first (RK403) ----------


def _entry(task_id: str, symptom: str, why: str) -> str:
    return f"- ✅ **{task_id}** **{symptom}** — {why}."


#: A ledger a textual git merge left: Block B declared twice, an entry under each, with an
#: unrelated block between them so the fold cannot be a matter of removing an adjacent heading.
DOUBLED = (
    "# Shipped\n\n## Block A — The model\n\n"
    + _entry("RK5", "A first thing fails", "because the first held")
    + "\n\n## Block B — Authoring\n\n"
    + _entry("RK6", "A second thing fails", "because the second held")
    + "\n\n## Block A — The model\n\n"  # the duplicate, of a different label, is left alone
    + _entry("RK4", "A fourth thing fails", "because the fourth held")
    + "\n"
)


def _doubled_on(label: str) -> str:
    """A ledger with two ``label`` headings and one entry under each, one block apart."""
    other = "A" if label != "A" else "B"
    return (
        "# Shipped\n\n"
        f"## Block {label} — First\n\n"
        + _entry("RK6", "A second thing fails", "because the second held")
        + f"\n\n## Block {other} — Between\n\n"
        + _entry("RK5", "A fifth thing fails", "because the fifth held")
        + f"\n\n## Block {label} — First\n\n"
        + _entry("RK4", "A fourth thing fails", "because the fourth held")
        + "\n"
    )


def test_a_doubled_changelog_heading_is_folded_into_the_first(tmp_path):
    from roadkeep.blocking import merge_block

    config = project(tmp_path, changelog=_doubled_on("B"))
    # The state the gate reports and every write refuses, before the fold.
    assert any(f.code == "block.repeated" for f in lint(config).findings)

    merge_block(config, "B").save()
    config = Config.discover(tmp_path)
    ledger = read(config, CHANGELOG)
    # One Block B heading now, and both entries under it in the order they were folded.
    assert ledger.count("## Block B — First") == 1
    assert ledger.index("RK6") < ledger.index("RK4")
    # The block between them is untouched, and the file passes its own gate.
    assert "## Block A — Between" in ledger
    assert not lint(config).findings


def test_the_fold_is_the_merge_the_write_path_refuses_by_hand(tmp_path):
    # End to end: the write path refuses a doubled heading (RepeatedHeading), the fold is the
    # tool's own answer to it, and after it a write the guard is the only other route to lands.
    from roadkeep.blocking import merge_block
    from roadkeep.kernel.document import RepeatedHeading
    from roadkeep.shipping import record

    config = project(tmp_path, changelog=_doubled_on("B"))
    with pytest.raises(RepeatedHeading):
        record(config, block="B", symptom="A new thing fails", why="because a new reason held.")

    merge_block(config, "B").save()
    config = Config.discover(tmp_path)
    written = record(
        config, block="B", symptom="A new thing fails", why="because a new reason held."
    )
    written.ledger.save()
    assert not lint(Config.discover(tmp_path)).findings


def test_a_label_declared_once_is_refused_rather_than_reported_clean(tmp_path):
    from roadkeep.blocking import NotRepeated, merge_block

    config = project(tmp_path)  # every file declares Block B exactly once
    with pytest.raises(NotRepeated):
        merge_block(config, "B")


def test_a_label_no_file_declares_is_the_other_refusal(tmp_path):
    from roadkeep.blocking import NoSuchBlock, merge_block

    config = project(tmp_path)
    with pytest.raises(NoSuchBlock):
        merge_block(config, "Z")


def test_a_nested_section_under_a_duplicate_is_section_moves_to_place(tmp_path):
    # A rationale file with Block B declared twice, a section nested under the second: folding
    # a subtree is `section move`'s editorial call, so `merge` refuses by name and writes nothing.
    from roadkeep.blocking import RegionOccupied, merge_block

    rationale = (
        "# Improvements\n\n## Block A — The model\n\n### §RK1 A first design\n\n"
        "The reasoning.\n\n## Block B — Authoring\n\n### §RK2 A second design\n\n"
        "The other reasoning.\n\n## Block B — Authoring\n\n### §RK9 A stray design\n\n"
        "A design under the duplicate.\n"
    )
    config = project(tmp_path, improvements=rationale)
    before = read(config, IMPROVEMENTS)
    with pytest.raises(RegionOccupied) as caught:
        merge_block(config, "B")
    assert "section move" in str(caught.value)
    assert read(Config.discover(tmp_path), IMPROVEMENTS) == before


def test_loose_prose_under_a_duplicate_needs_the_flag(tmp_path):
    from roadkeep.blocking import RegionOccupied, merge_block

    ledger = (
        "# Shipped\n\n## Block A — The model\n\n## Block B — Authoring\n\n"
        + _entry("RK6", "A second thing fails", "because the second held")
        + "\n\n## Block B — Authoring\n\nA stray note under the duplicate.\n\n"
        + _entry("RK4", "A fourth thing fails", "because the fourth held")
        + "\n"
    )
    config = project(tmp_path, changelog=ledger)
    with pytest.raises(RegionOccupied) as caught:
        merge_block(config, "B")
    assert "--prose" in str(caught.value)
    # The flag drops the note as the heading folds, and the file is clean after.
    merge_block(config, "B", prose=True).save()
    config = Config.discover(tmp_path)
    after = read(config, CHANGELOG)
    assert "stray note" not in after
    assert after.count("## Block B — Authoring") == 1
    assert not lint(config).findings


def test_three_headings_for_one_label_fold_into_one(tmp_path):
    from roadkeep.blocking import merge_block

    ledger = (
        "# Shipped\n\n## Block A — The model\n\n## Block B — Authoring\n\n"
        + _entry("RK6", "A sixth thing fails", "because the sixth held")
        + "\n\n## Block B — Authoring\n\n"
        + _entry("RK5", "A fifth thing fails", "because the fifth held")
        + "\n\n## Block B — Authoring\n\n"
        + _entry("RK4", "A fourth thing fails", "because the fourth held")
        + "\n"
    )
    config = project(tmp_path, changelog=ledger)
    merged = merge_block(config, "B")
    merged.save()
    config = Config.discover(tmp_path)
    after = read(config, CHANGELOG)
    assert after.count("## Block B — Authoring") == 1
    assert merged.moved["changelog"] == ("RK5", "RK4")
    assert len(merged.folded["changelog"]) == 2
    assert not lint(config).findings


def test_the_first_region_empty_still_receives_the_folded_entries(tmp_path):
    # The surviving heading has no entry of its own; the fold still lands under it, blanks intact.
    from roadkeep.blocking import merge_block

    ledger = (
        "# Shipped\n\n## Block A — The model\n\n## Block B — Authoring\n\n"
        "## Block A — The model\n\n"
        + _entry("RK4", "A fourth thing fails", "because the fourth held")
        + "\n"
    )
    config = project(tmp_path, changelog=ledger)
    merge_block(config, "A").save()
    config = Config.discover(tmp_path)
    after = read(config, CHANGELOG)
    assert after.count("## Block A — The model") == 1
    assert "RK4" in after
    assert not lint(config).findings


def test_nothing_is_written_when_a_second_file_refuses(tmp_path):
    # All of the files or none: a clean changelog fold is not written when the rationale file's
    # own duplicate holds a section the fold may not place.
    from roadkeep.blocking import RegionOccupied, merge_block

    rationale = (
        "# Improvements\n\n## Block A — The model\n\n### §RK1 A first design\n\n"
        "The reasoning.\n\n## Block B — Authoring\n\n### §RK2 A second design\n\n"
        "The other reasoning.\n\n## Block B — Authoring\n\n### §RK9 A stray design\n\n"
        "A design under the duplicate.\n"
    )
    config = project(tmp_path, changelog=_doubled_on("B"), improvements=rationale)
    ledger_before = read(config, CHANGELOG)
    with pytest.raises(RegionOccupied):
        merge_block(config, "B")
    assert read(Config.discover(tmp_path), CHANGELOG) == ledger_before


def test_the_merge_command_reports_what_moved(tmp_path, capsys):
    project(tmp_path, changelog=_doubled_on("B"))
    assert main(["-C", str(tmp_path), "block", "merge", "B"]) == EXIT_OK
    printed = capsys.readouterr().out
    assert "consolidated" in printed
    assert "RK4" in printed


def test_the_merge_json_says_which_ids_moved_where(tmp_path, capsys):
    project(tmp_path, changelog=_doubled_on("B"))
    assert main(["-C", str(tmp_path), "block", "merge", "B", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["label"] == "B"
    changelog = next(r for r in payload["merged"] if r["role"] == "changelog")
    assert changelog["moved"] == ["RK4"]
    assert changelog["folded"] == ["## Block B — First"]


# -- the heading inside the region (RK439) ------------------------------------


#: Shio's ledger, in miniature: `## Block B` with its entries grouped under `###` sub-headings
#: of the same label. 91 entries there, two field captures, and every write into the block
#: refused — the shape RK391 was never about.
NESTED = (
    "# Shipped\n\n## Block A — The model\n\n"
    + _entry("RK5", "A first thing fails", "because the first held")
    + "\n\n## Block B — Authoring\n\n"
    "### Block B follow-ups\n\n"
    + _entry("RK6", "A sixth thing fails", "because the sixth held")
    + "\n\n### Block B follow-ups\n\n"
    + _entry("RK4", "A fourth thing fails", "because the fourth held")
    + "\n"
)


def test_a_sub_heading_under_its_own_block_is_not_a_second_declaration(tmp_path):
    """RK391 refuses two headings that are two *addresses* for one label — the state where a
    write cannot know which region it files under. A heading inside another's subtree is not
    that state: its position already says which region owns it."""
    config = project(tmp_path, changelog=NESTED)
    assert not [f for f in lint(config).findings if f.code == "block.repeated"]
    document = config.document("changelog")
    declared = document.declaring("B")
    assert len(declared) == 1 and declared[0].level == 2


def test_the_write_the_nesting_used_to_refuse_lands_under_the_parent(tmp_path):
    """End to end, and the reason this is not a lint-only rule: `ship` could not file into
    that block at all. The entry goes after everything the region holds, which is what
    `subtree_end` has always meant."""
    from roadkeep.shipping import record

    config = project(tmp_path, changelog=NESTED)
    written = record(
        config, block="B", symptom="A new thing fails", why="because a new reason held."
    )
    written.save()
    ledger = read(Config.discover(tmp_path), CHANGELOG)
    assert ledger.count("## Block B — Authoring") == 1
    assert ledger.index("RK4") < ledger.index("A new thing fails")
    assert not lint(Config.discover(tmp_path)).findings


def test_two_headings_neither_inside_the_other_are_still_two_addresses(tmp_path):
    """The rule this narrows and does not remove: a nested heading is suppressed because its
    parent already owns the region, and two `##` under one label own two."""
    config = project(tmp_path, changelog=_doubled_on("B"))
    assert any(f.code == "block.repeated" for f in lint(config).findings)
    assert len(config.document("changelog").declaring("B")) == 2


def test_a_nested_heading_naming_another_label_still_declares_it(tmp_path):
    """The question §RK439 left open, answered by leaving it refused: a heading naming a
    label its parent does not is one declaration wherever it sits, and a second one anywhere
    else is a genuine second address."""
    changelog = (
        "# Shipped\n\n## Block A — The model\n\n"
        "### Block B — Nested under A\n\n"
        + _entry("RK6", "A sixth thing fails", "because the sixth held")
        + "\n\n## Block B — Authoring\n\n"
        + _entry("RK4", "A fourth thing fails", "because the fourth held")
        + "\n"
    )
    config = project(tmp_path, changelog=changelog)
    assert len(config.document("changelog").declaring("B")) == 2
    assert any(f.code == "block.repeated" for f in lint(config).findings)


# -- the named repair, and what it moves (RK425) ------------------------------


def test_the_repeated_heading_names_the_verb_and_what_it_moves(tmp_path):
    """The clause read *a merge by hand* until RK425 — prose left behind when RK403 shipped
    the verb. It named an edit the guard denies, and the obvious reading of it is a rename,
    which detaches every entry beneath the second heading: measured, renaming five headings
    produced 83 findings and had to be reverted."""
    from roadkeep.linting import lint

    config = _repeated(tmp_path)
    found = next(f for f in lint(config).findings if f.code == "block.repeated")
    assert "block merge A" in found.message
    assert "by hand" not in found.message
    # What the caller's next question is: whether their lines survive it, and how many move.
    assert "moving the 1 line(s) under it" in found.message
    assert "keeping the file's order" in found.message


def test_the_count_is_the_later_region_and_not_the_whole_label(tmp_path):
    # `document.block(label)` is every entry with that label anywhere in the file, which on
    # a repeated heading is both regions — a number that promised to move lines already in
    # the first one would be wrong in the direction that matters.
    from roadkeep.linting import lint

    config = _repeated(tmp_path, later="- 📋 **DX2** (deps: —) **A second** — A reason.\n"
                                       "- 📋 **DX4** (deps: —) **A fourth** — A reason.\n")
    found = next(f for f in lint(config).findings if f.code == "block.repeated")
    assert "moving the 2 line(s)" in found.message


def test_a_region_ends_at_the_next_heading_of_any_level(tmp_path):
    """The second fact RK425 is about: a `###` cannot group entries inside a block, so a
    subheading between two regions ends the first — and a count that ignored the level would
    promise to move lines the merge leaves where they are."""
    from roadkeep.linting import lint

    config = _repeated(
        tmp_path,
        later="- 📋 **DX2** (deps: —) **A second** — A reason.\n\n"
        "### A grouping title\n\n"
        "- 📋 **DX4** (deps: —) **A fourth** — A reason.\n",
    )
    found = next(f for f in lint(config).findings if f.code == "block.repeated")
    assert "moving the 1 line(s)" in found.message


def test_the_droppable_branch_states_no_count(tmp_path):
    # A region that holds nothing is removed rather than merged, and "moving the 0 line(s)"
    # is a sentence about the absence of a fact.
    from roadkeep.linting import lint

    config = _repeated(tmp_path, later="")
    found = next(f for f in lint(config).findings if f.code == "block.repeated")
    assert "block drop A" in found.message
    assert "moving the" not in found.message


def _repeated(tmp_path, later: str = "- 📋 **DX2** (deps: —) **A second** — A reason.\n"):
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "DX"\nref_scheme = "outline"\n[rules.roadmap]\nref = false\n'
        '[files]\nroadmap = "ROADMAP.md"\n',
        encoding="utf-8",
    )
    body = (
        "# Roadmap\n\n## Block A — The first block\n\n"
        "- 📋 **DX1** (deps: —) **A first** — A reason.\n\n"
        "## Block A — The first block, again\n\n" + later
    )
    with (tmp_path / "ROADMAP.md").open("w", encoding="utf-8", newline="") as handle:
        handle.write(body)
    return Config.discover(tmp_path)
