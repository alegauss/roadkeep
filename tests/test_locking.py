"""Serialising the write path (RK117).

The defect is a race, so the tests stage it rather than hope for it: the second process
is a lock file written by hand, or a real command run from inside the window the first one
occupies. What is asserted is never timing — it is that the second writer is *refused*
rather than served, and that a query is never refused at all.

The three properties that make the lock usable rather than merely correct are here too:
a lock nobody released is reaped by age, a process that already holds it does not deadlock
on itself, and the write path an agent actually uses — MCP — takes it.
"""

from __future__ import annotations

import argparse
import os
import time
from pathlib import Path

import pytest

from roadkeep import locking
from roadkeep.cli import EXIT_GATE, EXIT_OK, main
from roadkeep.locking import LockBusy, exclusive, lock_path

RK1 = "- 📋 **RK1** (deps: —) **A first symptom** — Because of a reason. → §RK1"

BACKLOG = f"""# Roadmap

## Block A — The model

{RK1}

## Non-goals

- not a task line
"""


def project(tmp_path: Path) -> Path:
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "docs/ROADMAP.md"\n', encoding="utf-8"
    )
    target = tmp_path / "docs" / "ROADMAP.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="") as handle:
        handle.write(BACKLOG)
    return tmp_path


def seize(root: Path, *, age: float = 0.0) -> Path:
    """Another process's lock, as it would be on disk — optionally already old."""
    target = lock_path(root)
    target.write_text("pid 999999 at 1.0\n", encoding="utf-8")
    if age:
        when = time.time() - age
        os.utime(target, (when, when))
    return target


@pytest.fixture(autouse=True)
def _no_leftover_lock(tmp_path):
    yield
    lock_path(tmp_path).unlink(missing_ok=True)


@pytest.fixture(autouse=True)
def _quick(monkeypatch):
    # The durations are the one thing not under test: a suite that spent five seconds
    # proving a timeout would be a suite nobody runs. What is kept is the *gap* — a wait far
    # below the staleness — because that is what makes a busy lock refuse instead of reap.
    monkeypatch.setattr(locking, "STALE", 5.0)
    monkeypatch.setattr(locking, "WAIT", 0.05)
    monkeypatch.setattr(locking, "POLL", 0.01)


# -- the lock itself ---------------------------------------------------------


def test_the_lock_lives_outside_the_checkout_it_guards(tmp_path):
    # A file the tool creates in a project's root is a file every adopting project has to
    # gitignore before its first `git status` reads as dirty.
    target = lock_path(tmp_path)
    assert tmp_path not in target.parents
    assert target.name.startswith("roadkeep-")


def test_two_checkouts_of_one_project_lock_independently(tmp_path):
    (tmp_path / "one").mkdir()
    (tmp_path / "two").mkdir()
    assert lock_path(tmp_path / "one") != lock_path(tmp_path / "two")


def test_a_held_lock_refuses_the_second_writer_rather_than_serving_it(tmp_path):
    seize(tmp_path)
    with pytest.raises(LockBusy, match="another roadkeep process"):
        with exclusive(tmp_path):
            pytest.fail("the lock was handed to a second holder")


def test_the_refusal_names_the_file_to_delete(tmp_path):
    seize(tmp_path)
    with pytest.raises(LockBusy) as refused:
        with exclusive(tmp_path):
            pass
    assert str(lock_path(tmp_path)) in str(refused.value)
    assert "pid 999999" in str(refused.value)


def test_a_lock_nobody_released_is_reaped_by_age_and_the_waiter_proceeds(tmp_path):
    # The holder may have been killed, and there is no portable way to ask whether a pid is
    # alive. A lock nobody will ever release is an unusable checkout, so age decides.
    seize(tmp_path, age=locking.STALE * 3)
    with exclusive(tmp_path) as held:
        assert held.exists()


def test_the_lock_is_released_when_the_command_raises(tmp_path):
    with pytest.raises(ValueError):
        with exclusive(tmp_path):
            raise ValueError("the command refused")
    assert not lock_path(tmp_path).exists()


def test_a_process_that_already_holds_it_does_not_deadlock_on_itself(tmp_path):
    # `report` and `replay` re-enter the CLI in this process to run the command they are
    # about (RK85), and a lock that deadlocked there would make the capture tool unusable
    # against exactly the commands worth capturing.
    with exclusive(tmp_path):
        with exclusive(tmp_path):
            assert lock_path(tmp_path).exists()
        # The inner exit must not hand the outer one's lock to a waiter.
        assert lock_path(tmp_path).exists()
    assert not lock_path(tmp_path).exists()


def test_a_holder_that_was_reaped_does_not_delete_the_next_holders_lock(tmp_path):
    # Release checks that the lock is still the one this process took. Without it, a holder
    # slow enough to be declared abandoned hands a third process a checkout two are writing.
    with exclusive(tmp_path) as held:
        held.unlink()
        seize(tmp_path)  # somebody reaped ours and took their own
    assert lock_path(tmp_path).read_text(encoding="utf-8").startswith("pid 999999")


# -- what the commands do with it --------------------------------------------


def test_a_write_blocked_by_another_process_exits_one_and_writes_nothing(tmp_path):
    root = project(tmp_path)
    seize(root)
    argv = ["-C", str(root), "add", "--block", "A", "--symptom", "S", "--why", "A reason."]
    assert main(argv) == EXIT_GATE
    with (root / "docs" / "ROADMAP.md").open("r", encoding="utf-8", newline="") as handle:
        assert handle.read() == BACKLOG


def test_a_query_answers_while_another_process_holds_the_lock(tmp_path, capsys):
    # What keeps `pick` and `brief` usable during a write — and `guard`, which runs before
    # every write in the session and would otherwise wait on the one it was called about.
    root = project(tmp_path)
    seize(root)
    for query in (["pick"], ["list"], ["next-id"], ["lint", "--json"]):
        main(["-C", str(root), *query])
        # On the refusal and not on the exit code: `lint` answers 1 for a violation as well, and
        # it used to answer 1 for *this* — a busy checkout reading as a drifted format (RK168).
        assert "another roadkeep process" not in capsys.readouterr().err, query
    assert lock_path(root).exists()  # untouched by any of them


def test_a_write_takes_the_lock_and_gives_it_back(tmp_path, monkeypatch):
    root = project(tmp_path)
    seen: list[bool] = []
    real = locking.exclusive

    def watched(where):
        seen.append(True)
        return real(where)

    monkeypatch.setattr("roadkeep.cli.exclusive", watched)
    argv = ["-C", str(root), "add", "--block", "A", "--symptom", "S", "--why", "A reason."]
    assert main(argv) == EXIT_OK
    assert seen == [True]
    assert not lock_path(root).exists()


def test_an_mcp_write_takes_the_same_lock_a_cli_write_takes(tmp_path):
    # The path an agent actually uses (RK24). The MCP server dispatches parsed args
    # in-process and never goes through `main`, so a lock only `main` took would be one the
    # defect walks around.
    from roadkeep.serving import call, tool_named

    root = project(tmp_path)
    seize(root)
    answer = call(
        tool_named("add"),
        {"block": "A", "symptom": "A symptom", "why": "A reason."},
        directory=str(root),
    )
    assert answer.is_error
    assert "another roadkeep process" in answer.text


def test_an_mcp_query_is_not_blocked_by_a_held_lock(tmp_path):
    from roadkeep.serving import call, tool_named

    root = project(tmp_path)
    seize(root)
    answer = call(tool_named("pick"), {}, directory=str(root))
    assert "another roadkeep process" not in answer.text


# -- a read that can write says so, and the dispatcher decides (RK167) --------


def declared() -> dict[str, str]:
    """Every subcommand that declares itself a read with a flag that makes it a write."""
    from roadkeep.cli import build_parser

    return {
        name: parser.get_default("writes_when")
        for action in build_parser()._actions  # noqa: SLF001
        if isinstance(action, argparse._SubParsersAction)  # noqa: SLF001
        for name, parser in action.choices.items()
        if parser.get_default("writes_when")
    }


def test_the_reads_that_can_write_are_the_ones_that_say_so():
    # Named here rather than counted, because the list is the point: any further one is a
    # deliberate addition and not something a copied comment brought along. `lint` joined them
    # (RK168) — the gate is a read, and the write in it is the repair.
    assert declared() == {
        "pick": "claim",
        "brief": "claim",
        "claims": "prune",
        "lint": "fix",
    }


def test_every_declared_flag_is_one_its_own_parser_accepts():
    # The way this mechanism can be wrong is a renamed flag leaving `dispatch` reading an
    # attribute nobody sets — a lock silently not taken. Read off the real parser, so it fails
    # here instead.
    from roadkeep.cli import build_parser

    subparsers = {
        name: parser
        for action in build_parser()._actions  # noqa: SLF001
        if isinstance(action, argparse._SubParsersAction)  # noqa: SLF001
        for name, parser in action.choices.items()
    }
    for command, flag in declared().items():
        assert flag in {a.dest for a in subparsers[command]._actions}, command  # noqa: SLF001


@pytest.mark.parametrize(
    ("command", "flag"),
    [
        ("pick", "--claim"),
        ("brief", "--claim"),
        ("claims", "--prune"),
        ("lint", "--fix"),
    ],
)
def test_the_argv_that_writes_waits_and_the_one_that_reads_does_not(
    tmp_path, capsys, command, flag
):
    """The property RK167 asked for, and the one no call site could state: with the flag it is a
    write and a held lock refuses it; without, it answers while somebody else is writing.

    Asserted on the refusal and not on the exit code, because `lint` answers 1 for a violation
    too — and telling those two apart is the whole of RK168."""
    root = project(tmp_path)
    seize(root)
    main(["-C", str(root), command])
    assert "another roadkeep process" not in capsys.readouterr().err
    assert main(["-C", str(root), command, flag]) == EXIT_GATE
    assert "another roadkeep process" in capsys.readouterr().err
    assert lock_path(root).exists()  # somebody else's, and still theirs
