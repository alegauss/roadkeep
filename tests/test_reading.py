"""What a read may refuse on, over every question this project has written down (RK1650).

*Reading is never refused* is a rule this project believes and had stated four times, each
about one verb: `block list`'s docstring, `criterion list`'s, a help string on `non-goal list`
and the sentence the guard prints to an agent that tried to hand-edit a governed file. RK1608
made it false, deliberately — `pick --have <word>` refuses where `[requirements] declared`
names a vocabulary the word is not in, because that is a caller who typed something this
project cannot mean — and the distinction that makes the refusal right lived in one verb's
docstring. Forty verbs are read-only; nothing said which of them may refuse or on what.

`roadkeep.verbs.refusing` states the rule now, where every verb already imports its exit
codes, and this is what holds it. Two grounds — the caller named something the declarations
exclude, or the read is about state that has to be made first — and never an empty answer,
which is the half the rule exists to protect: a caller refused on a list they have not opted
into cannot learn that the list is the thing they have not declared.

**The population is `asking.QUESTIONS`** and not a second list of reads. That inventory is L5's
own surface — every question this project has written down, joined to the argv that answers it
— and its rows say outright that the positionals are placeholders *never run*. So this runs
them, against the project a first-time adopter has: what a read does on a tree that declared
nothing is exactly the question those argvs were never asked. :data:`REFUSING` adds the four
reads whose subject is behind a flag rather than a verb, which no inventory of *questions*
reaches, and each row carries the ground and the word its refusal has to name.

What is asserted is that no read exits **2**, which is usage or configuration. A verdict is an
answer: `lint` returning 1 read the files and they did not pass, and `cli._may_offer` already
splits a verdict from a fault for the same reason.
"""

from __future__ import annotations

import contextlib
import io
import shutil
from pathlib import Path

import pytest

from asking import QUESTIONS, verbs
from conftest import git_commit, git_init

from roadkeep.cli import main
from roadkeep.verbs.refusing import EXIT_USAGE

#: The two grounds `roadkeep.verbs.refusing` states, as the rows below name one of.
EXCLUDED = "the caller named something this project's declarations exclude"
UNMADE = "the read is about state that has to be made before the question means anything"

#: Every read that refuses on a project which declared only the scaffold: the ground, and the
#: word its refusal has to name. Total against the sweep in both directions — a read that
#: starts refusing is a red with one question in it, and a row whose read in fact answers is an
#: exemption standing in front of a working one.
#:
#: Four rows and three subjects: the deferred store is reached by two different reads, and
#: naming both is the point rather than a redundancy — `budget --defer` refuses over the store
#: as a *subject* and `list --stale` over it as a *role*, which are the two grounds one absence
#: can be met on.
REFUSING: dict[tuple[str, ...], tuple[str, str]] = {
    ("claim", "RK1"): (UNMADE, "RK1"),
    ("budget", "--defer"): (UNMADE, "deferred"),
    ("list", "--stale"): (EXCLUDED, "deferred"),
    ("list", "--role", "deferred"): (EXCLUDED, "deferred"),
}

#: Questions this sweep parses and does not run, with why. One row: `merge`'s three paths are
#: git's `%O %A %B` and its exit code is the merge's own verdict written into `%A` — a driver
#: contract `test_registers` already names, and not an answer a caller reads.
NOT_RUN = {
    ("merge", "base.md", "ours.md", "theirs.md"): (
        "the three paths are git's and the code is the driver's verdict, not a read's answer"
    ),
}


@pytest.fixture(scope="session")
def scaffold(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """The project a first-time adopter has: `init`, one line, one commit.

    Nothing else, which is the whole point — every role but the three `init` writes is
    undeclared, both opt-in tables are unopened, and no vocabulary is declared. A fixture that
    declared more would answer about a project that had already opted in, which is the state
    the rule is *not* about.

    The line and the commit are what make the reads non-vacuous rather than what make them
    pass: `origin` resolves a task to the commit that wrote it, and a tree with no commits
    refuses for want of a history — which is git's absence and not this project's declaration.
    """
    root = tmp_path_factory.mktemp("scaffold")
    assert main(["-C", str(root), "init"]) == 0
    assert (
        main(
            [
                "-C", str(root), "add", "--block", "A",
                "--symptom", "a symptom plainly long enough to read",
                "--why", "Because a read needs one line to answer about.",
                "--section", "The first design",
                "--section-body", "The reasoning the line itself has no room for.",
            ]
        )
        == 0
    )
    git_init(root)
    git_commit(root, "the project, and the one line every read below is about")
    return root


def _ran(root: Path, argv: tuple[str, ...]) -> tuple[int, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = main(["-C", str(root), *argv])
        except SystemExit as leaving:  # argparse refused before a handler existed
            code = leaving.code if isinstance(leaving.code, int) else EXIT_USAGE
    return code, err.getvalue()


def test_every_question_answers_or_names_the_absence_it_met(scaffold):
    """RK1650's holder, over `QUESTIONS` and the flag-level reads beside it. A read that
    refuses has to be one of the rows, and its refusal has to name what was missing — the two
    halves of the rule, asked of the one project state that tells them apart."""
    for question in QUESTIONS:
        argv = question.answered_by
        if argv in NOT_RUN:
            continue
        code, said = _ran(scaffold, argv)
        if code != EXIT_USAGE:
            continue
        assert argv in REFUSING, (
            f"`{' '.join(argv)}` refuses on a project that declared only the scaffold: "
            f"either it is answering an empty question with a refusal, or it is a row in "
            f"REFUSING with its ground and the word it names — {said.strip()[:160]}"
        )
    for argv, (ground, names) in REFUSING.items():
        code, said = _ran(scaffold, argv)
        assert code == EXIT_USAGE, (
            f"`{' '.join(argv)}` answers here: the row is an exemption in front of a working "
            f"read, and the rule is what changed"
        )
        assert ground in (EXCLUDED, UNMADE), (argv, ground)
        assert names in said, (argv, names, said.strip()[:160])


def test_the_lists_a_project_has_not_opted_into_answer_rather_than_refuse(scaffold):
    """The half the rule protects, asserted where it is easiest to lose. Each of these reads a
    table or a role the scaffold never declared, and each answers — because a caller refused
    here would be one who cannot discover that the list is what they have not declared."""
    for argv in (
        ("non-goal", "list"),
        ("criterion", "list"),
        ("block", "list"),
        ("priority", "list"),
        ("reversals",),
        # RK1608's own protected half: no vocabulary is declared here, so a `--have` word is a
        # row saying the flag narrowed nothing rather than a refusal.
        ("pick", "--have", "gpu"),
    ):
        code, said = _ran(scaffold, argv)
        assert code != EXIT_USAGE, (f"`{' '.join(argv)}`", said.strip()[:160])


def test_a_word_outside_a_declared_vocabulary_is_the_ground_and_not_an_exception(
    scaffold, tmp_path
):
    """RK1608 read as the rule rather than as its first exception, which is what this task is
    about. The same flag, the same word, two projects: refused where the project declared a
    vocabulary that excludes it, answered where it declared none. Nothing about the *word*
    decides it — the declaration does."""
    assert _ran(scaffold, ("pick", "--have", "gpu"))[0] != EXIT_USAGE
    root = tmp_path / "declared"
    root.mkdir()
    for name in ("roadkeep.toml", "docs"):
        source = scaffold / name
        if source.is_dir():
            shutil.copytree(source, root / name)
        else:
            (root / name).write_bytes(source.read_bytes())
    config = root / "roadkeep.toml"
    config.write_text(
        config.read_text(encoding="utf-8") + '\n[requirements]\ndeclared = ["tpu"]\n',
        encoding="utf-8",
        newline="",
    )
    code, said = _ran(root, ("pick", "--have", "gpu"))
    assert code == EXIT_USAGE, said
    assert "gpu" in said, said


def test_every_row_names_a_read_this_cli_still_has():
    """The tables are addresses, so a verb renamed leaves a row that sweeps nothing — the
    failure `asking.verbs` is read for one file over."""
    declared = verbs()
    for argv in (*REFUSING, *NOT_RUN):
        assert argv[0] in declared, argv
        assert declared[argv[0]].get_default("reads_only") or argv[0] == "merge", argv
    assert all(reason for reason in NOT_RUN.values())
