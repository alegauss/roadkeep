"""The merge two worktrees produce in a file only this tool may write (RK120).

The acceptance test is the case that has no textual answer: two branches derive the same
next id, each append under the same block heading, and git offers conflict markers in a
file the guard denies a hand edit to. One call has to merge the two additions that are
different work, and refuse — by name — the one address they both spent.

Everything else here is a refusal, and each is about the same thing: the driver writes a
file only when it can prove it, and hands the reviewer git's own markers when it cannot.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from roadkeep.cli import EXIT_GATE, EXIT_OK, EXIT_USAGE, main
from roadkeep.config import Config
from roadkeep.history import HistoryUnavailable
from roadkeep.merging import (
    ABSENT,
    CURRENT,
    DRIVER_KEY,
    MOVED,
    UNKNOWN,
    UNRUNNABLE,
    driver_value,
    merge,
    register,
    registered,
    role_of,
)
from roadkeep.provenance import persisted

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
    subprocess.run(["git", "-C", str(tmp_path), "init", "-q"], check=True, capture_output=True)
    return config


def set_driver(tmp_path: Path, value: str) -> None:
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "--local", DRIVER_KEY, value],
        check=True,
        capture_output=True,
    )


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


def test_git_that_cannot_be_asked_is_unknown_and_not_absent(tmp_path, monkeypatch):
    # Absent means "nothing is wired" and unknown means "nobody could tell us", and reporting
    # the second as the first would name a repair for a question that was never resolved.
    config = repository(tmp_path)
    set_driver(tmp_path, driver_value(persisted().command))

    def refuse(*args, **kwargs):
        raise HistoryUnavailable("git is not on PATH")

    monkeypatch.setattr("roadkeep.history._run", refuse)
    driver = registered(config)
    assert driver.state == UNKNOWN and not driver.wired
    assert main(["-C", str(tmp_path), "merge", "--check"]) == EXIT_OK

