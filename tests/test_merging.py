"""The merge two worktrees produce in a file only this tool may write (RK120).

The acceptance test is the case that has no textual answer: two branches derive the same
next id, each append under the same block heading, and git offers conflict markers in a
file the guard denies a hand edit to. One call has to merge the two additions that are
different work, and refuse — by name — the one address they both spent.

Everything else here is a refusal, and each is about the same thing: the driver writes a
file only when it can prove it, and hands the reviewer git's own markers when it cannot.
"""

from __future__ import annotations

import shlex
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import git, git_commit, git_init

from roadkeep.cli import EXIT_GATE, EXIT_OK, EXIT_USAGE, main
from roadkeep.config import Config
from roadkeep.history import HistoryUnavailable
from roadkeep.merging import (
    ABSENT,
    CURRENT,
    DRIVER,
    DRIVER_KEY,
    MOVED,
    PARTIAL,
    UNKNOWN,
    UNRUNNABLE,
    UNSPECIFIED,
    Attributes,
    attributed,
    config_command,
    driver_value,
    merge,
    register,
    registered,
    role_of,
    wiring,
)
from roadkeep.provenance import persisted
from roadkeep.schema import SchemaError

ROADMAP = "docs/ROADMAP.md"
CHANGELOG = "docs/CHANGELOG.md"
IMPROVEMENTS = "docs/IMPROVEMENTS.md"

CONFIG = (
    'prefix = "RK"\n[files]\n'
    f'roadmap = "{ROADMAP}"\nchangelog = "{CHANGELOG}"\nimprovements = "{IMPROVEMENTS}"\n'
)

BASE = """# Roadmap

## Block A — The model

- 📋 **RK1** (deps: —) **the line both branches started from** — Because it was there. → §RK1

## Block B — Authoring

- 📋 **RK2** (deps: —) **a second block, so a branch can touch one alone** — Because blocks part. → §RK2
"""


def line(task_id: str, symptom: str, why: str, block: str = "A") -> str:
    return f"- 📋 **{task_id}** (deps: —) **{symptom}** — {why} → §{task_id}\n"


def under(text: str, block: str, *added: str) -> str:
    """The file with lines appended under a block — how `add` leaves it."""
    out: list[str] = []
    heads = {"A": "## Block A — The model", "B": "## Block B — Authoring"}
    lines = text.splitlines(keepends=True)
    for index, raw in enumerate(lines):
        out.append(raw)
        last = raw.startswith("- ") and (
            index + 1 == len(lines) or not lines[index + 1].startswith("- ")
        )
        if last and _block_above(lines, index) == heads[block]:
            out.extend(added)
    return "".join(out)


def _block_above(lines: list[str], index: int) -> str:
    for raw in reversed(lines[: index + 1]):
        if raw.startswith("## "):
            return raw.rstrip("\r\n")
    return ""


def project(tmp_path: Path) -> Config:
    (tmp_path / "roadkeep.toml").write_text(CONFIG, encoding="utf-8")
    for name in (ROADMAP, CHANGELOG, IMPROVEMENTS):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(BASE if name == ROADMAP else "# File\n", encoding="utf-8")
    return Config.discover(tmp_path)


def three(tmp_path: Path, base: str, ours: str, theirs: str) -> list[str]:
    """The three files git hands a driver, on disk, in its argument order."""
    names = ("base", "ours", "theirs")
    for name, text in zip(names, (base, ours, theirs)):
        (tmp_path / name).write_text(text, encoding="utf-8", newline="")
    return [str(tmp_path / name) for name in names]


# -- the measured case -------------------------------------------------------


def test_two_additions_under_one_heading_are_two_additions(tmp_path):
    # The case a textual merge calls a conflict: both branches appended under Block A.
    config = project(tmp_path)
    ours = under(BASE, "A", line("RK3", "what this branch filed", "Because it did."))
    theirs = under(BASE, "A", line("RK4", "what the other filed", "Because it did too."))

    merged = merge(config, "roadmap", BASE, ours, theirs)

    assert merged.clean and merged.text is not None
    assert "**RK3**" in merged.text and "**RK4**" in merged.text
    assert merged.took == ("RK4",)
    assert merged.doubled == () and merged.contested == ()


def test_one_address_two_branches_spent_is_named_and_never_picked(tmp_path):
    # The collision itself. Refused rather than resolved: `renumber` moves one of them,
    # and a driver that picked a side would be choosing whose task disappears.
    config = project(tmp_path)
    ours = under(BASE, "A", line("RK3", "what this branch filed", "Because it did."))
    theirs = under(BASE, "A", line("RK3", "what the other filed", "Because it did too."))

    merged = merge(config, "roadmap", BASE, ours, theirs)

    assert not merged.clean and merged.text is None
    assert merged.doubled == ("RK3",)
    assert "renumber" in merged.reason


def test_a_line_only_one_side_edited_is_taken_from_that_side(tmp_path):
    config = project(tmp_path)
    theirs = BASE.replace("Because it was there.", "Because it was rewritten.")

    merged = merge(config, "roadmap", BASE, BASE, theirs)

    assert merged.clean and merged.took == ("RK1",)
    assert "Because it was rewritten." in (merged.text or "")


def test_a_line_both_sides_rewrote_is_kept_apart_from_a_spent_id(tmp_path):
    # One line, two sentences — the wording is the reviewer's, and the remedy is not an
    # address, so it is reported under its own name.
    config = project(tmp_path)
    ours = BASE.replace("Because it was there.", "Because we say so.")
    theirs = BASE.replace("Because it was there.", "Because they say so.")

    merged = merge(config, "roadmap", BASE, ours, theirs)

    assert not merged.clean
    assert merged.contested == ("RK1",) and merged.doubled == ()


def test_a_line_one_side_removed_and_the_other_edited_is_neither_of_those(tmp_path):
    """RK482. `_decide`'s last branch is an `else` written for two rewordings, and it also
    caught the case where one of the three lines is **absent** — so a `ship` on one branch
    against an `amend` on the other answered *both branches rewrote RK1: one line, two
    sentences — the wording is the reviewer's*. Reproduced both ways on a scaffolded project.

    Nobody rewrote anything on the shipping side: the line left, and `ship` is the ordinary
    way a line leaves. So the message was wrong about what happened and named the wrong
    decision — a sentence, where the question is whether the removal stands."""
    config = project(tmp_path)
    gone = "".join(one for one in BASE.splitlines(keepends=True) if "**RK1**" not in one)
    edited = BASE.replace("Because it was there.", "Because it was corrected.")

    merged = merge(config, "roadmap", BASE, gone, edited)

    assert not merged.clean
    assert merged.withdrawn == ("RK1",)
    assert merged.contested == () and merged.doubled == ()
    assert "removed RK1" in merged.reason and "rewrote" not in merged.reason
    # Symmetric: which side shipped is not a fact about what the reviewer has to decide.
    other = merge(config, "roadmap", BASE, edited, gone)
    assert other.withdrawn == ("RK1",) and other.reason == merged.reason


def test_it_still_refuses_rather_than_taking_the_removal(tmp_path):
    """Taking it is defensible — `ship` is a decision somebody made — and it would delete the
    edit silently, which is the ground RK97 refuses to pick on for a doubled id. So what RK482
    changed is the sentence and never the verdict."""
    config = project(tmp_path)
    gone = "".join(one for one in BASE.splitlines(keepends=True) if "**RK1**" not in one)
    edited = BASE.replace("Because it was there.", "Because it was corrected.")

    merged = merge(config, "roadmap", BASE, gone, edited)

    assert merged.text is None and merged.reason


PROSE = """# Improvements

## Block A — The model

### §RK1 The first design

The reasoning the first line has no room for.

### §RK2 The second design

The reasoning the second line has no room for.

### §RK3 The third design

The reasoning the third line has no room for.
"""


def without(text: str, anchor: str) -> str:
    """The file with one §section taken out — how `ship` leaves a rationale file."""
    out, dropping = [], False
    for line in text.splitlines(keepends=True):
        if line.startswith("### §"):
            dropping = line.startswith(f"### §{anchor} ")
        if not dropping:
            out.append(line)
    return "".join(out)


def test_two_branches_that_each_shipped_merge_the_prose_file(tmp_path):
    """RK483. `_skeleton` is *every line that is not a task line* and a rationale file has
    none, so the skeleton was the whole file and `_frame` compared three whole files: any two
    differing sides refused. `ship` drops a section, so two branches that shipped anything at
    all landed there — measured on a scaffold as two disjoint drops answering *both branches
    changed the prose*, in a file the guard denies editing and the gate refuses.

    The address is what makes it decidable and this file has one: a §section is keyed by the
    anchor `section drop` takes."""
    config = project(tmp_path)
    ours, theirs = without(PROSE, "RK1"), without(PROSE, "RK3")

    merged = merge(config, "improvements", PROSE, ours, theirs)

    assert merged.clean, merged.reason
    assert "§RK1" not in (merged.text or "") and "§RK3" not in (merged.text or "")
    assert "§RK2 The second design" in (merged.text or "")


def test_the_prose_merge_gives_an_untouched_file_back_byte_for_byte(tmp_path):
    """L3 over the merge: nothing changed, so nothing may move. The first cut of the
    materializer put one blank line at EOF — every corpus it was run against came back one
    line longer, which is how the section separator turned out to be the frame's fact and
    not a constant."""
    config = project(tmp_path)
    assert merge(config, "improvements", PROSE, PROSE, PROSE).text == PROSE
    # And one side unchanged is the other side exactly, which is the ordinary rebase.
    ours = without(PROSE, "RK2")
    assert merge(config, "improvements", PROSE, ours, PROSE).text == ours
    assert merge(config, "improvements", PROSE, PROSE, ours).text == ours


def test_a_section_arriving_last_is_not_lost_while_being_reported_as_taken(tmp_path):
    """The bug the first cut of `_written` had: a new section with no frame anchor after it
    fell through the placement loop and never reached the file, while `took` said it had.
    Silent loss is the one thing this driver exists to refuse, so it is asserted at all three
    positions — before every anchor, between two, and after the last."""
    config = project(tmp_path)
    added = PROSE + "\n### §RK4 The fourth design\n\nThe reasoning the fourth has no room for.\n"

    merged = merge(config, "improvements", PROSE, PROSE, added)

    assert merged.clean, merged.reason
    assert "§RK4 The fourth design" in (merged.text or "")
    assert merged.took == ("RK4",)


def test_a_section_both_sides_rewrote_is_still_the_reviewers(tmp_path):
    """L4 is not weakened by RK483: taking a whole section from one side is the decision the
    roadmap already makes, and merging *inside* one is prose."""
    config = project(tmp_path)
    ours = PROSE.replace("The reasoning the second line has no room for.", "Ours rewrote it.")
    theirs = PROSE.replace("The reasoning the second line has no room for.", "Theirs rewrote it.")

    merged = merge(config, "improvements", PROSE, ours, theirs)

    assert not merged.clean
    assert merged.contested == ("RK2",)


def test_a_section_one_side_dropped_and_the_other_rewrote_is_withdrawn(tmp_path):
    """RK482's third category, one file over: `ship` against a `section amend` is the same
    pair as `ship` against an `amend`, and it asks the same question."""
    config = project(tmp_path)
    ours = without(PROSE, "RK2")
    theirs = PROSE.replace("The reasoning the second line has no room for.", "Theirs rewrote it.")

    merged = merge(config, "improvements", PROSE, ours, theirs)

    assert not merged.clean
    assert merged.withdrawn == ("RK2",) and merged.contested == ()


def test_a_line_the_other_side_removed_goes(tmp_path):
    config = project(tmp_path)
    theirs = "".join(l for l in BASE.splitlines(keepends=True) if "**RK2**" not in l)

    merged = merge(config, "roadmap", BASE, BASE, theirs)

    assert merged.clean and merged.removed == ("RK2",)
    assert "**RK2**" not in (merged.text or "")


def test_the_same_line_added_on_both_sides_is_one_line(tmp_path):
    config = project(tmp_path)
    same = under(BASE, "A", line("RK3", "the same work, filed twice", "Because a cherry-pick."))

    merged = merge(config, "roadmap", same[: len(same)], same, same)

    assert merged.clean and (merged.text or "").count("**RK3**") == 1


# -- what it will not merge --------------------------------------------------


def test_prose_changed_on_both_sides_is_the_reviewers(tmp_path):
    # Headings and the paragraphs around the entries are what this tool does not write
    # (L4), so a merge of them is not this driver's to make.
    config = project(tmp_path)
    ours = BASE.replace("# Roadmap", "# Roadmap (ours)")
    theirs = BASE.replace("# Roadmap", "# Roadmap (theirs)")

    merged = merge(config, "roadmap", BASE, ours, theirs)

    assert not merged.clean and "prose" in merged.reason


def test_prose_changed_on_one_side_is_carried(tmp_path):
    config = project(tmp_path)
    theirs = BASE.replace("# Roadmap", "# Roadmap (theirs)")
    ours = under(BASE, "A", line("RK3", "what this branch filed", "Because it did."))

    merged = merge(config, "roadmap", BASE, ours, theirs)

    assert merged.clean
    assert "# Roadmap (theirs)" in (merged.text or "")
    assert "**RK3**" in (merged.text or "")


def test_a_version_this_tool_cannot_reproduce_is_refused(tmp_path):
    # L3, at the one door where three files arrive at once: a merge of lines the schema
    # would render differently normalises work nobody reviewed.
    config = project(tmp_path)
    # The pointer is derived under `ref_scheme = "id"`, so a line carrying the wrong
    # anchor is exactly a line the schema would render differently from how it is written.
    theirs = BASE.replace("→ §RK1\n", "→ §RK9\n")

    merged = merge(config, "roadmap", BASE, BASE, theirs)

    assert not merged.clean and "reproduce" in merged.reason
    assert "RK1" in merged.reason


def test_a_merge_the_gate_would_refuse_is_not_offered(tmp_path):
    # It gates its own output: a clean exit on a file `lint` refuses is the one outcome
    # worse than a conflict, because nobody reads it.
    config = project(tmp_path)
    over = "x" * 400
    theirs = BASE.replace("Because it was there.", f"Because {over}.")

    merged = merge(config, "roadmap", BASE, BASE, theirs)

    assert not merged.clean and "the gate refuses" in merged.reason


# -- the driver's contract with git ------------------------------------------


def test_the_command_writes_the_result_into_ours_and_exits_zero(tmp_path, capsys):
    project(tmp_path)
    ours = under(BASE, "A", line("RK3", "what this branch filed", "Because it did."))
    theirs = under(BASE, "B", line("RK4", "what the other filed", "Because it did too.", "B"))
    paths = three(tmp_path, BASE, ours, theirs)

    assert main(["-C", str(tmp_path), "merge", *paths, "--path", ROADMAP]) == EXIT_OK
    written = (tmp_path / "ours").read_text(encoding="utf-8")
    assert "**RK3**" in written and "**RK4**" in written
    assert "took RK4" in capsys.readouterr().out


def test_the_refusal_leaves_conflict_markers_and_exits_one(tmp_path, capsys):
    project(tmp_path)
    ours = under(BASE, "A", line("RK3", "what this branch filed", "Because it did."))
    theirs = under(BASE, "A", line("RK3", "what the other filed", "Because it did too."))
    paths = three(tmp_path, BASE, ours, theirs)

    assert main(["-C", str(tmp_path), "merge", *paths, "--path", ROADMAP]) == EXIT_GATE
    written = (tmp_path / "ours").read_text(encoding="utf-8")
    assert written.startswith("<<<<<<< ours\n")
    assert "=======" in written and written.rstrip().endswith(">>>>>>> theirs")
    assert "renumber" in capsys.readouterr().err


def test_a_file_this_project_does_not_declare_is_declined(tmp_path, capsys):
    project(tmp_path)
    paths = three(tmp_path, BASE, BASE, BASE)
    code = main(["-C", str(tmp_path), "merge", *paths, "--path", "README.md"])
    assert code == EXIT_USAGE
    assert "not a file this project declares" in capsys.readouterr().err


def test_three_files_or_register_and_nothing_else(tmp_path, capsys):
    project(tmp_path)
    assert main(["-C", str(tmp_path), "merge"]) == EXIT_USAGE
    assert "three files" in capsys.readouterr().err


def test_the_role_is_read_off_the_pathname(tmp_path):
    config = project(tmp_path)
    assert role_of(config, ROADMAP) == "roadmap"
    assert role_of(config, CHANGELOG) == "changelog"
    assert role_of(config, "README.md") is None


# -- registration (L6: opt-in, per file) -------------------------------------


def test_register_writes_one_attribute_line_per_governed_file(tmp_path):
    config = project(tmp_path)
    written = register(config)
    body = (tmp_path / ".gitattributes").read_text(encoding="utf-8")
    assert f"{ROADMAP} merge=roadkeep" in body
    assert f"{IMPROVEMENTS} merge=roadkeep" in body
    assert len(written.added) == 3 and written.present == ()
    assert "git config merge.roadkeep.driver" in written.command


def test_the_driver_git_is_told_to_run_is_derived_and_not_a_bare_console_script(tmp_path):
    # RK255: the value lands in `.git/config` and git executes it when a governed file
    # conflicts, so a name that only PATH resolved is a driver that fails at the one moment
    # this file exists for — and git's fallback is conflict markers in a file whose merge is
    # decidable. What is stored is `persisted()`, and what it cannot promise is said beside it.
    config = project(tmp_path)
    stored = persisted()
    written = register(config)
    assert written.command == (
        f'git config merge.roadkeep.driver "{stored.command} merge %O %A %B --path %P"'
    )
    assert written.invalidated_by == stored.invalidated_by and written.invalidated_by
    # Never the console script literal, unless that is what this machine actually resolved to.
    assert '"roadkeep merge' not in written.command


def test_registering_twice_does_not_double_the_file(tmp_path):
    config = project(tmp_path)
    (tmp_path / ".gitattributes").write_text("* text=auto\n", encoding="utf-8")
    register(config)
    again = register(config)
    body = (tmp_path / ".gitattributes").read_text(encoding="utf-8")
    assert again.added == () and len(again.present) == 3
    assert body.count(f"{ROADMAP} merge=roadkeep") == 1
    # Somebody else's line in somebody else's file, carried through untouched.
    assert body.startswith("* text=auto\n")


def test_the_command_prints_what_it_wrote_and_what_it_did_not_run(tmp_path, capsys):
    project(tmp_path)
    assert main(["-C", str(tmp_path), "merge", "--register"]) == EXIT_OK
    printed = capsys.readouterr().out
    assert f"+ {ROADMAP} merge=roadkeep" in printed
    assert "then     git config merge.roadkeep.driver" in printed
    # And the expiry of the value it just told the reader to store (RK255).
    assert f"re-run   after {persisted().invalidated_by}" in printed
    # And what git actually holds right now (RK266), which is the half `.gitattributes`
    # reporting "already there" on a re-run cannot speak for.
    assert "config   merge.roadkeep.driver" in printed


# -- what git actually holds (RK266) -----------------------------------------


def repository(tmp_path: Path) -> Config:
    """A project that is also a git repository, because `.git/config` is what is being read."""
    config = project(tmp_path)
    git_init(tmp_path)
    return config


def set_driver(tmp_path: Path, value: str) -> None:
    git(tmp_path, "config", "--local", DRIVER_KEY, value)


def test_a_checkout_with_no_driver_says_so_rather_than_nothing(tmp_path):
    # RK266: `register` printed the line to set and never asked whether it was set, so a
    # repository wired on one side only looked exactly like a wired one.
    config = repository(tmp_path)
    driver = registered(config)
    assert driver.state == ABSENT and not driver.wired and driver.stored == ""
    assert driver.wanted == driver_value(persisted().command)


def test_the_driver_this_machine_would_write_reads_as_current(tmp_path):
    config = repository(tmp_path)
    set_driver(tmp_path, driver_value(persisted().command))
    driver = registered(config)
    assert driver.state == CURRENT and driver.wired


def test_a_driver_naming_something_gone_is_the_defect_and_exits_one(tmp_path, capsys):
    # The whole point: this is what a plugin update leaves behind, and until now the first
    # evidence of it was git writing conflict markers into a file whose merge is decidable.
    config = repository(tmp_path)
    set_driver(tmp_path, driver_value(f"python {tmp_path.as_posix()}/gone/roadkeep.py"))
    assert registered(config).state == UNRUNNABLE
    assert main(["-C", str(tmp_path), "merge", "--check"]) == EXIT_GATE
    printed = capsys.readouterr().out
    assert "no longer has" in printed and "gone/roadkeep.py" in printed
    assert "merge --register" in printed


def test_a_driver_that_runs_and_is_not_this_machine_s_is_not_a_failure(tmp_path, capsys):
    # Crying wolf here would make the check unusable on any repository two people registered
    # from — which is every repository a merge driver exists for. It runs, so it is a fact.
    config = repository(tmp_path)
    register(config)  # the attribute half, so the exit code is about the config half alone
    set_driver(tmp_path, driver_value(f"{Path(sys.executable).as_posix()} -m roadkeep.cli"))
    driver = registered(config)
    assert driver.state == MOVED and driver.wired
    assert main(["-C", str(tmp_path), "merge", "--check"]) == EXIT_OK
    printed = capsys.readouterr().out
    assert "is not this machine's" in printed and "merge --register" not in printed


def test_the_check_writes_nothing(tmp_path):
    # The one thing the flag promises, asserted rather than assumed: `--check` alongside
    # `--register` is the check, and a `.gitattributes` written here would be the whole bug.
    repository(tmp_path)
    assert main(["-C", str(tmp_path), "merge", "--register", "--check"]) == EXIT_GATE
    assert not (tmp_path / ".gitattributes").exists()


def test_the_json_form_is_refused_on_the_branches_that_cannot_answer_it(tmp_path, capsys):
    # RK317: argparse scopes a flag to the subparser and not to the branch, so `--json` parsed on
    # the driver line, was ignored, and exited as though the caller had been served — worse than a
    # refusal, which at least says the request was not understood.
    config = repository(tmp_path)
    assert main(["-C", str(tmp_path), "merge", "--register", "--json"]) == EXIT_USAGE
    assert "--json is the form of --check" in capsys.readouterr().err
    # Refused *before* the write, which is this tool's rule everywhere: nothing landed.
    assert not (tmp_path / ".gitattributes").exists()
    # And on the driver's own line, where git reads an exit code and the bytes it left in `%A`.
    # The three paths are git's to spell and are never read here — the flag is refused before
    # anything opens them, which is what the message rather than the code has to establish.
    driving = ["merge", "base", "ours", "theirs", "--path", config.relative(config.path("roadmap"))]
    assert main(["-C", str(tmp_path), *driving, "--json"]) == EXIT_USAGE
    assert "--json is the form of --check" in capsys.readouterr().err


def test_the_check_still_answers_as_json_because_it_is_whose_form_it_is(tmp_path):
    # The branch RK275 added the flag for, and the one the MCP surface reaches: that surface
    # passes `--json` on every call and never exposes it, so refusing it here would unserve the
    # tool. Asserted beside the refusal, because the pair is the whole decision.
    repository(tmp_path)
    assert main(["-C", str(tmp_path), "merge", "--check", "--json"]) == EXIT_GATE


def test_a_wired_config_over_no_attributes_is_not_a_wired_repository(tmp_path, capsys):
    # RK270: a driver is two writes. The config says what the name runs; `.gitattributes` is
    # what sends git to the name at all — so `config current` over an unwritten attribute file
    # is a true answer to the question nobody asked, and git merges the file textually.
    config = repository(tmp_path)
    set_driver(tmp_path, driver_value(persisted().command))
    assert registered(config).state == CURRENT
    assert attributed(config).state == ABSENT and not attributed(config).wired
    assert main(["-C", str(tmp_path), "merge", "--check"]) == EXIT_GATE
    printed = capsys.readouterr().out
    # Both halves reported, and the one that is missing named by file rather than counted away.
    assert "sends 0 of 3 governed files" in printed and ROADMAP in printed
    assert "would merge textually" in printed
    assert "config      merge.roadkeep.driver set to the command" in printed
    assert "merge --register" in printed


def test_a_role_declared_after_the_file_was_written_reads_as_partial(tmp_path, capsys):
    # The state a whole-file yes/no hides: `register` ran when two roles were declared, a third
    # arrived, and every line the file carries is correct — for the files it names.
    config = repository(tmp_path)
    register(config)
    lines = (tmp_path / ".gitattributes").read_text(encoding="utf-8").splitlines()
    (tmp_path / ".gitattributes").write_text(
        "".join(f"{line}\n" for line in lines if IMPROVEMENTS not in line), encoding="utf-8"
    )
    attributes = attributed(config)
    assert attributes.state == PARTIAL and not attributes.wired
    assert len(attributes.present) == 2 and len(attributes.missing) == 1
    assert main(["-C", str(tmp_path), "merge", "--check"]) == EXIT_GATE
    printed = capsys.readouterr().out
    assert "sends 2 of 3 governed files" in printed and IMPROVEMENTS in printed
    assert ROADMAP not in printed.split("attributes")[1].split("\n")[0]


def test_both_halves_written_is_the_one_answer_that_exits_zero(tmp_path, capsys):
    config = repository(tmp_path)
    register(config)
    set_driver(tmp_path, driver_value(persisted().command))
    assert attributed(config).wired and registered(config).state == CURRENT
    assert main(["-C", str(tmp_path), "merge", "--check"]) == EXIT_OK
    printed = capsys.readouterr().out
    assert "sends 3 of 3 governed files to the roadkeep driver" in printed
    assert "merge --register" not in printed


def test_the_write_is_built_on_the_read_so_the_two_cannot_drift(tmp_path):
    # `register` computes nothing of its own about which lines a role wants: it asks
    # `attributed` and writes what is missing. Two computations would be how a check comes to
    # agree with nothing but itself, which is worse than having no check.
    config = repository(tmp_path)
    before = attributed(config)
    written = register(config)
    assert written.added == before.missing and before.state == ABSENT
    assert attributed(config).state == CURRENT
    assert register(config).added == ()


def test_an_attribute_git_honours_outside_the_root_file_is_not_unsent(tmp_path, capsys):
    # RK273, and the measurement the section was written from: git resolves `merge` from a
    # `.gitattributes` in every directory up, then `.git/info/attributes`, then
    # `core.attributesFile` — so a read of the root file alone reported three files unsent
    # while `check-attr` answered `roadkeep` for one of them.
    config = repository(tmp_path)
    info = tmp_path / ".git" / "info"
    info.mkdir(parents=True, exist_ok=True)
    (info / "attributes").write_text(f"{ROADMAP} merge={DRIVER}\n", encoding="utf-8")
    attributes = attributed(config)
    assert attributes.sent == (ROADMAP,) and attributes.state == PARTIAL
    # The root file carries nothing, and that stays true: it is what `register` writes.
    assert attributes.present == () and len(attributes.missing) == 3
    assert main(["-C", str(tmp_path), "merge", "--check"]) == EXIT_GATE
    printed = capsys.readouterr().out
    assert "git sends 1 of 3 governed files" in printed and ROADMAP not in printed


def test_a_governed_file_wired_to_another_driver_is_reported_and_not_argued_with(tmp_path, capsys):
    # The case a string comparison could not see at all: it could only find its own name, so a
    # file deliberately sent elsewhere read as nothing set.
    config = repository(tmp_path)
    register(config)
    (tmp_path / ".gitattributes").write_text(f"{CHANGELOG} merge=theirs\n", encoding="utf-8")
    attributes = attributed(config)
    assert attributes.claimed == ((CHANGELOG, "theirs"),)
    assert attributes.state == ABSENT
    assert main(["-C", str(tmp_path), "merge", "--check"]) == EXIT_GATE
    assert f"{CHANGELOG} → theirs" in capsys.readouterr().out


def test_registering_never_writes_over_a_file_another_driver_is_named_for(tmp_path, capsys):
    # RK274, and the acceptance test is the measurement: git takes the *last* matching rule, so
    # appending `merge=roadkeep` under `merge=theirs` won over it — the overridden line stayed
    # in the file, inert, which kept "every other line untouched" and none of its meaning.
    config = repository(tmp_path)
    (tmp_path / ".gitattributes").write_text(f"{CHANGELOG} merge=theirs\n", encoding="utf-8")
    written = register(config)

    assert written.left_alone == ((CHANGELOG, "theirs"),)
    assert all(CHANGELOG not in line for line in written.added)
    # The claim git resolves is the same one it resolved before the repair ran.
    assert attributed(config).claimed == ((CHANGELOG, "theirs"),)
    body = (tmp_path / ".gitattributes").read_text(encoding="utf-8")
    assert f"{CHANGELOG} merge=roadkeep" not in body and f"{CHANGELOG} merge=theirs" in body

    # And the skip is named where the writes are: one nobody is told about is one nobody meant.
    assert main(["-C", str(tmp_path), "merge", "--register"]) == EXIT_OK
    assert f"{CHANGELOG} → theirs (another driver, left alone)" in capsys.readouterr().out


def test_a_claimed_file_is_settled_and_does_not_hold_the_check_open(tmp_path, capsys):
    # The other half of RK274: reporting a deliberate wiring as work still to do left the check
    # failing forever on a repository that was finished. Decided is decided — just not for us.
    config = repository(tmp_path)
    (tmp_path / ".gitattributes").write_text(f"{CHANGELOG} merge=theirs\n", encoding="utf-8")
    register(config)
    set_driver(tmp_path, driver_value(persisted().command))

    attributes = attributed(config)
    assert attributes.state == CURRENT and attributes.wired
    assert attributes.unsent == () and attributes.sent == (ROADMAP, IMPROVEMENTS)
    assert main(["-C", str(tmp_path), "merge", "--check"]) == EXIT_OK
    printed = capsys.readouterr().out
    # Counted short of the total, with the reason on the same line: a count with an unexplained
    # gap reads as the failure this is not, and dropping the file would claim it after all.
    assert "git sends 2 of 3 governed files" in printed
    assert f"{CHANGELOG} → theirs, left alone" in printed and "fix" not in printed


def test_no_driver_is_demanded_where_no_governed_file_would_reach_it(tmp_path, capsys):
    # RK277, measured: `docs/*.md merge=theirs` routes every governed file elsewhere, so the
    # config half was exiting 1 asking for a value no merge in that repository would call.
    config = repository(tmp_path)
    (tmp_path / ".gitattributes").write_text("docs/*.md merge=theirs\n", encoding="utf-8")
    attributes = attributed(config)
    assert not attributes.routes_here and attributes.state == CURRENT

    assert main(["-C", str(tmp_path), "merge", "--check"]) == EXIT_OK
    printed = capsys.readouterr().out
    # Still reported — this narrows what the check demands, never what it says.
    assert "merge.roadkeep.driver not set" in printed
    assert "no governed file routes here" in printed and "fix" not in printed


def test_the_verb_and_the_check_say_the_same_thing_about_the_config(tmp_path, capsys):
    # RK278: on the repository RK277 was measured on, `--check` said "no governed file routes
    # here" and asked for nothing while `--register` printed `then git config …`, telling the
    # reader to wire a driver that repository would never call. One `Wiring`, one answer.
    config = repository(tmp_path)
    (tmp_path / ".gitattributes").write_text("docs/*.md merge=theirs\n", encoding="utf-8")
    assert not wiring(config).demands_driver

    assert main(["-C", str(tmp_path), "merge", "--check"]) == EXIT_OK
    checked = capsys.readouterr().out
    assert main(["-C", str(tmp_path), "merge", "--register"]) == EXIT_OK
    verb = capsys.readouterr().out

    for said in (checked, verb):
        assert "no governed file routes here" in said
    # Advice, withheld on both: the state line above is still printed on both.
    assert "then" not in verb and "fix" not in checked


def test_the_advice_returns_the_moment_a_file_routes_here(tmp_path, capsys):
    # The other direction, so the withholding above is a conjunction and not a mute button.
    config = repository(tmp_path)
    register(config)
    assert wiring(config).demands_driver
    assert main(["-C", str(tmp_path), "merge", "--register"]) == EXIT_OK
    assert "then     git config merge.roadkeep.driver" in capsys.readouterr().out


def test_a_project_declaring_no_governed_file_asks_for_no_driver_either(tmp_path):
    # The second case the same rule covers, stated rather than discovered: nothing is unsent,
    # so nothing is undecided, so there is no driver to want.
    empty = Attributes(path=tmp_path / ".gitattributes", wanted=(), present=(), resolved=())
    assert not empty.routes_here and empty.state == CURRENT


def test_an_unregistered_project_still_wants_the_driver(tmp_path):
    # The trap in the narrow reading: on a fresh project nothing is *sent* either, so a
    # `sent`-is-empty test would have withdrawn the config repair from the one repository whose
    # reader is in the middle of wiring it — and RK272 is the acceptance test that catches it.
    config = repository(tmp_path)
    attributes = attributed(config)
    assert attributes.sent == () and attributes.unsent and attributes.routes_here


def test_git_that_cannot_be_asked_leaves_the_attribute_half_unknown(tmp_path, capsys, monkeypatch):
    # The reading `Driver` already had, arriving in the half that never needed it before: a
    # question git could not answer names no repair, because nobody resolved it.
    config = repository(tmp_path)

    def refuse(*args, **kwargs):
        raise HistoryUnavailable("git is not on PATH")

    monkeypatch.setattr("roadkeep.history._bytes", refuse)
    monkeypatch.setattr("roadkeep.history._run", refuse)
    attributes = attributed(config)
    assert attributes.state == UNKNOWN and not attributes.wired
    # Nothing was established, so no repair is withdrawn either (RK277): the direction that
    # cannot be wrong by silence.
    assert attributes.routes_here
    assert main(["-C", str(tmp_path), "merge", "--check"]) == EXIT_OK
    printed = capsys.readouterr().out
    assert "could not be read" in printed and "merge --register" not in printed


def test_the_two_modules_spell_gits_word_the_same_way():
    # `merging` cannot import `history` at module level (RK260) and a property cannot pay a
    # lazy import, so the literal is in both places — and held together here.
    from roadkeep import history

    assert UNSPECIFIED == history.UNSPECIFIED


def test_following_the_repair_the_check_names_ends_the_check(tmp_path, capsys):
    # RK272, and the acceptance test is the reader's own path: take the advice, then ask again.
    # It used to answer `fix … merge --register` on a fresh project, and answer exactly that
    # again after the verb had run — because the verb writes one half and prints the other.
    config = repository(tmp_path)
    assert main(["-C", str(tmp_path), "merge", "--check"]) == EXIT_GATE
    first = capsys.readouterr().out
    assert "merge --register" in first and config_command() in first

    assert main(["-C", str(tmp_path), "merge", "--register"]) == EXIT_OK
    capsys.readouterr()
    assert main(["-C", str(tmp_path), "merge", "--check"]) == EXIT_GATE
    second = capsys.readouterr().out
    # The half that is still open, and only that one: repeating the verb would change nothing.
    assert config_command() in second and "merge --register" not in second

    subprocess.run(shlex.split(config_command()), cwd=tmp_path, check=True, capture_output=True)
    assert main(["-C", str(tmp_path), "merge", "--check"]) == EXIT_OK
    assert "fix" not in capsys.readouterr().out


def test_git_itself_reaches_the_driver_and_reads_back_a_line_it_can_act_on(tmp_path):
    """The whole wiring, driven by git rather than called directly (RK484).

    Everything above hands `merge` three paths itself, which is the one way the driver is
    never actually used. Run through `git merge`, the arguments are `%O %A %B` — temporary
    files git deletes on return — so the capture line RK86 appends named three files that
    were gone before it finished printing, on the verb where the offer is worth most.

    Asserted here and not only over `offer`, because what makes it wrong is the caller: the
    argv is git's, and nothing in this package composes it.
    """
    repository(tmp_path)
    # The changelog needs the heading too, because `add` refuses to file under a block one
    # governed file declares and another does not.
    (tmp_path / CHANGELOG).write_text("# Shipped\n\n## Block A — The model\n", encoding="utf-8")
    assert main(["-C", str(tmp_path), "merge", "--register"]) == EXIT_OK
    subprocess.run(shlex.split(config_command()), cwd=tmp_path, check=True, capture_output=True)
    git_commit(tmp_path, "base")
    # Whatever this git calls its first branch — the name is a version's default and not a
    # fact this test is about.
    start = git(tmp_path, "rev-parse", "--abbrev-ref", "HEAD").strip()
    for branch, symptom in (("theirs", "theirs appended here"), ("ours", "ours appended here")):
        git(tmp_path, "checkout", "-q", "-B", branch, start)
        assert main(["-C", str(tmp_path), "add", "--block", "A", "--symptom",
                     f"A line {symptom} under one heading", "--why", "Because."]) == EXIT_OK
        git(tmp_path, "add", "-A")
        git_commit(tmp_path, f"{branch} adds")
    done = subprocess.run(
        ["git", "merge", "theirs"], cwd=tmp_path, capture_output=True, text=True, check=False
    )
    said = done.stdout + done.stderr
    assert "both branches created" in said, said
    assert ".merge_file_" not in said, said
    assert "git rev-parse HEAD MERGE_HEAD" in said, said


def test_the_repair_named_is_the_one_the_registration_prints(tmp_path):
    # One spelling (RK272): `register` prints it as what to do next and the check prints it as
    # what to do now, and two spellings would be two repairs — of which one would be wrong.
    config = repository(tmp_path)
    assert register(config).command == config_command()
    assert DRIVER_KEY in config_command() and driver_value(persisted().command) in config_command()


def test_git_that_cannot_be_asked_is_unknown_and_not_absent(tmp_path, monkeypatch):
    # Absent means "nothing is wired" and unknown means "nobody could tell us", and reporting
    # the second as the first would name a repair for a question that was never resolved.
    config = repository(tmp_path)
    register(config)  # before the patch, because `register` asks git the same question
    set_driver(tmp_path, driver_value(persisted().command))

    def refuse(*args, **kwargs):
        raise HistoryUnavailable("git is not on PATH")

    monkeypatch.setattr("roadkeep.history._run", refuse)
    driver = registered(config)
    assert driver.state == UNKNOWN and not driver.wired
    assert main(["-C", str(tmp_path), "merge", "--check"]) == EXIT_OK



# -- the refusal that named neither the id nor the file (RK361) ---------------


def test_a_merged_line_the_schema_refuses_names_the_id_and_the_file(tmp_path):
    """RK348's rule, at the one door that did not keep it.

    A length reported as a bare number is unreadable here for a reason the other three doors
    do not have: the line is one branch's, landing in the other's file, so the caller has two
    versions open and the count says which of them nothing.
    """
    (tmp_path / "roadkeep.toml").write_text(CONFIG + "[limits]\nline = 120\n", encoding="utf-8")
    for name in (ROADMAP, CHANGELOG, IMPROVEMENTS):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(BASE if name == ROADMAP else "# File\n", encoding="utf-8")
    config = Config.discover(tmp_path)
    theirs = under(
        BASE,
        "A",
        line("RK3", "a symptom the other branch wrote", "Because the reason it gave runs past the limit this project declares for a line."),
    )

    with pytest.raises(SchemaError) as raised:
        merge(config, "roadmap", BASE, BASE, theirs)

    (violation,) = raised.value.violations
    assert violation.code == "why.too-long"
    # Appended, never substituted: the limit is still what a repair needs to know.
    # 51 and not 52 since RK430: the structure this line renders carries a 📋, which is
    # two UTF-16 units and one code point, so the `why` has one fewer to spend.
    assert violation.message.startswith("80 characters, limit is 51")
    assert f"on RK3's line, merging {ROADMAP}" in violation.message
