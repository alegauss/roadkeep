"""The queue that outranks the id order, in a file something governs (RK325).

What is under test is the *move* rather than a new grammar: `priority` already existed and
already worked, and what it did not have was a home anything watched. So the claims worth
holding are that the section is read in file order, that the two doors refuse what a task
line's doors refuse (an entry that is not a token, an address already taken, a token nothing
carries), that `pick` reads the section over the config and **says which**, and that a
heading with nothing under it is a queue that is empty rather than one that is absent —
which is the case where falling back would silently restore an order the author had just
finished dismantling.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from roadkeep.cli import EXIT_OK, EXIT_USAGE, main
from roadkeep.config import Config
from roadkeep.guarding import Refusal
from roadkeep.linting import lint
from roadkeep.picking import pick
from roadkeep.queueing import (
    DuplicateEntry,
    NoQueue,
    NoSuchEntry,
    NotAnEntry,
    add,
    declared,
    drop,
    read,
    render,
    tokens,
    typed,
)
from roadkeep.serving import TOOLS

ROADMAP = """# Roadmap

## Priority

What jumps the id order.

- RK2
- Block D

## Block A — The model

- 📋 **RK1** (deps: —) **A first symptom** — Because of a reason. → §RK1
- 📋 **RK2** (deps: —) **A second symptom** — Because of a reason. → §RK2

## Block D — Later

- 📋 **RK5** (deps: —) **A fifth symptom** — Because of a reason. → §RK5
"""

#: The same file with the heading and nothing under it: a queue that is declared and off.
EMPTY = ROADMAP.replace("- RK2\n- Block D\n\n", "")
#: And with no heading at all, which is the state every project is in before it writes one.
NONE = ROADMAP.replace("## Priority\n\nWhat jumps the id order.\n\n- RK2\n- Block D\n\n", "")

CONFIG = 'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\n'
DECLARED = CONFIG.replace('prefix = "RK"\n', 'prefix = "RK"\npriority = ["RK5"]\n')


def project(tmp_path: Path, roadmap: str = ROADMAP, config: str = CONFIG) -> Config:
    (tmp_path / "roadkeep.toml").write_text(config, encoding="utf-8")
    with (tmp_path / "ROADMAP.md").open("w", encoding="utf-8", newline="") as handle:
        handle.write(roadmap)
    return Config.discover(tmp_path)


def text(tmp_path: Path) -> str:
    with (tmp_path / "ROADMAP.md").open("r", encoding="utf-8", newline="") as handle:
        return handle.read()


# -- reading what is already there -------------------------------------------


def test_the_section_is_read_in_file_order(tmp_path):
    # File order *is* the order: an entry's place in the list is its whole content, so
    # nothing here sorts and nothing derives a rank.
    config = project(tmp_path)
    queue = read(config.document("roadmap"), config)
    assert queue.tokens == ("RK2", "Block D") and queue.declared_in == "roadmap"


def test_a_bullet_the_format_cannot_read_is_counted_and_not_dropped(tmp_path):
    # Being unreadable is not being absent, and a count that omitted these would read as a
    # complete one — the split `non-goal`'s rejects already make.
    config = project(tmp_path, roadmap=ROADMAP.replace("- Block D\n", "- Block D\n- RK2 first\n"))
    queue = read(config.document("roadmap"), config)
    assert queue.tokens == ("RK2", "Block D")
    assert queue.rejects == ((9, "- RK2 first"),)


def test_a_token_is_an_id_or_a_block_and_typed_by_the_code_that_types_a_dep(tmp_path):
    config = project(tmp_path)
    assert typed(config, "RK2") and typed(config, "Block D")
    assert not typed(config, "ZZ9") and not typed(config, "RK1-RK4")


def test_the_queue_bullets_are_prose_to_every_other_reader(tmp_path):
    # `- RK2` claims no marker slot and no bold id, so nothing counts it as a line and the
    # gate says nothing about it — the whole reason the section can live in this file.
    config = project(tmp_path)
    assert lint(config).findings == ()
    assert len(config.document("roadmap").entries) == 3


# -- the two doors -----------------------------------------------------------


def test_an_entry_is_appended_because_a_queue_grows_at_the_end(tmp_path):
    # "Everything new is most urgent" is the order nobody meant.
    config = project(tmp_path)
    written = add(config, "RK1")
    written.save()

    assert (written.position, written.length) == (3, 3)
    assert tokens(Config.discover(tmp_path)) == ("RK2", "Block D", "RK1")


def test_first_and_after_are_the_two_places_that_are_not_the_end(tmp_path):
    # Moving work up the order is the act the config file made unavailable.
    config = project(tmp_path)
    add(config, "RK1", first=True).save()
    assert tokens(Config.discover(tmp_path)) == ("RK1", "RK2", "Block D")

    config = Config.discover(tmp_path)
    written = add(config, "RK5", after="RK1")
    written.save()
    assert written.position == 2
    assert tokens(Config.discover(tmp_path)) == ("RK1", "RK5", "RK2", "Block D")


def test_the_first_entry_of_an_empty_section_lands_under_its_prose(tmp_path):
    # Never straight under the heading: a sentence saying what the queue is for would read
    # as a footnote to the first entry.
    config = project(tmp_path, roadmap=EMPTY)
    add(config, "RK1").save()
    assert "What jumps the id order.\n\n- RK1\n" in text(tmp_path)


def test_a_token_that_is_neither_an_id_nor_a_block_is_refused(tmp_path):
    config = project(tmp_path)
    with pytest.raises(NotAnEntry) as caught:
        add(config, "soon")
    assert "neither an id of this project nor 'Block X'" in str(caught.value)
    assert text(tmp_path) == ROADMAP


def test_a_token_the_queue_already_carries_is_refused(tmp_path):
    config = project(tmp_path)
    with pytest.raises(DuplicateEntry) as caught:
        add(config, "RK2")
    assert "already queues RK2" in str(caught.value)
    assert text(tmp_path) == ROADMAP


def test_after_a_token_nothing_carries_is_refused_before_anything_is_written(tmp_path):
    config = project(tmp_path)
    with pytest.raises(NoSuchEntry):
        add(config, "RK1", after="RK9")
    assert text(tmp_path) == ROADMAP


def test_a_project_with_no_heading_is_told_the_heading_declares_the_list(tmp_path):
    # A heading is the only thing that declares one, exactly as a block heading declares a
    # block (RK37) — so this is a refusal and never an invented section.
    config = project(tmp_path, roadmap=NONE)
    with pytest.raises(NoQueue) as caught:
        add(config, "RK1")
    assert "the heading declares the queue" in str(caught.value)


def test_dropping_takes_the_entry_out_and_leaves_no_doubled_blank(tmp_path):
    config = project(tmp_path)
    dropped = drop(config, "RK2")
    dropped.save()

    assert dropped.length == 1
    assert "What jumps the id order.\n\n- Block D\n\n## Block A" in text(tmp_path)


def test_dropping_the_last_entry_leaves_the_section_and_not_a_paragraph_break(tmp_path):
    config = project(tmp_path)
    drop(config, "RK2").save()
    drop(Config.discover(tmp_path), "Block D").save()

    assert "What jumps the id order.\n\n## Block A" in text(tmp_path)
    assert declared(Config.discover(tmp_path)).declared_in == "roadmap"


def test_dropping_a_token_nothing_carries_names_what_is_there(tmp_path):
    config = project(tmp_path)
    with pytest.raises(NoSuchEntry) as caught:
        drop(config, "RK1")
    assert "the queue holds RK2, Block D" in str(caught.value)


# -- which file declared it --------------------------------------------------


def test_the_section_wins_where_both_are_declared(tmp_path):
    # Two orders concatenated is a third order nobody wrote.
    config = project(tmp_path, config=DECLARED)
    queue = declared(config)
    assert queue.tokens == ("RK2", "Block D") and queue.declared_in == "roadmap"


def test_a_declared_and_empty_section_is_off_rather_than_absent(tmp_path):
    # Declaring the list and then removing every entry is how a project turns the tier off,
    # and falling back would make the last `priority drop` restore an order just dismantled.
    config = project(tmp_path, roadmap=EMPTY, config=DECLARED)
    queue = declared(config)
    assert queue.tokens == () and queue.declared_in == "roadmap"


def test_the_config_still_answers_where_no_heading_declares_a_section(tmp_path):
    # Shio and Turing may have declared one, and a move that silently emptied their queue
    # would be this tool changing what `pick` answers without being asked.
    config = project(tmp_path, roadmap=NONE, config=DECLARED)
    queue = declared(config)
    assert queue.tokens == ("RK5",) and queue.declared_in == "config"


def test_neither_is_an_answer_of_its_own(tmp_path):
    config = project(tmp_path, roadmap=NONE)
    assert declared(config).declared_in == ""


# -- what pick does with it --------------------------------------------------


def test_pick_applies_the_section_and_says_it_was_the_section(tmp_path):
    # A project that wrote a section and is still being ordered by its config has a fact to
    # learn, and the tier is where it reads.
    config = project(tmp_path, config=DECLARED)
    chosen = pick(config)
    assert chosen.entry is not None and chosen.entry.task.id == "RK2"
    assert "the roadmap's queue names RK2" in chosen.reason


def test_pick_falls_back_to_the_config_and_says_that_too(tmp_path):
    config = project(tmp_path, roadmap=NONE, config=DECLARED)
    chosen = pick(config)
    assert chosen.entry is not None and chosen.entry.task.id == "RK5"
    assert "declared priority names RK5" in chosen.reason


def test_an_entry_naming_nothing_ready_still_says_which_queue_was_read(tmp_path):
    config = project(tmp_path, roadmap=ROADMAP.replace("- RK2\n- Block D\n", "- RK9\n"))
    chosen = pick(config)
    assert chosen.entry is not None and chosen.entry.task.id == "RK1"
    assert "the roadmap's queue names nothing ready" in chosen.reason


# -- the surfaces ------------------------------------------------------------


def test_the_command_writes_reads_and_removes(tmp_path, capsys):
    project(tmp_path)
    assert main(["-C", str(tmp_path), "priority", "add", "RK1", "--first"]) == EXIT_OK
    assert "order    1 of 3" in capsys.readouterr().out

    assert main(["-C", str(tmp_path), "priority", "list", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["priority"] == ["RK1", "RK2", "Block D"]
    assert payload["declared_in"] == "roadmap" and payload["file"] == "ROADMAP.md"

    assert main(["-C", str(tmp_path), "priority", "drop", "RK1"]) == EXIT_OK
    assert "dropped  RK1" in capsys.readouterr().out


def test_first_and_after_are_one_choice(tmp_path):
    project(tmp_path)
    with pytest.raises(SystemExit):
        main(["-C", str(tmp_path), "priority", "add", "RK1", "--first", "--after", "RK2"])


def test_a_project_with_no_queue_at_all_reads_and_is_not_refused(tmp_path, capsys):
    # Reading is never refused, which is the rule `non-goal list` already keeps.
    project(tmp_path, roadmap=NONE)
    assert main(["-C", str(tmp_path), "priority", "list"]) == EXIT_OK
    printed = capsys.readouterr().out
    assert "no priority queue" in printed and "the id order stands either way" in printed


def test_a_refused_edit_to_the_roadmap_names_both_queue_verbs(tmp_path):
    # The reason this list moved at all: the guard denies the edit, so a denial that named
    # only the task-line writers would leave `sed` as the route (RK70's own argument).
    reason = str(Refusal(tool="Edit", path="ROADMAP.md", role="roadmap"))
    assert "priority add <token>" in reason and "priority drop <token>" in reason


def test_the_agent_that_ships_a_queued_id_can_take_it_out(tmp_path):
    # A door only the CLI can reach is no door on the surface this ships for.
    served = {tool.name for tool in TOOLS}
    assert {"priority_add", "priority_drop", "priority_list"} <= served


def test_the_renderer_is_the_only_writer_of_the_bullet():
    assert render(" RK1 ") == "- RK1"
    assert render("Block D") == "- Block D"
