#!/usr/bin/env python
"""Run this repository's suite the way the gate does. Standard library only.

Four tasks in one session were defects the suite could not see and CI could — RK1153, RK1154,
RK1155, RK1158 — and they were not four problems. They were **one** difference: the workflow
installs the package and runs it on a machine with no git identity, no plugin cache and, for one
of its two jobs, the oldest interpreter this package supports. Nothing here ran the suite that
way, so each was found by pushing, waiting, and reading a log (RK1159).

    python scripts/like_ci.py             # apply every difference this machine can
    python scripts/like_ci.py --dry-run   # say what it would do, and what it cannot

**What it cannot apply, it names.** A run that quietly covered three differences of four would
report a clean suite about an environment nobody chose — the failure `adopt`'s scope line already
refuses one command over. So :func:`differences` answers per difference, the summary prints each
with its state, and the exit code is pytest's own.

It creates a throwaway venv and installs the project into it, because that is the difference the
other three ride on: `pip install` puts the console script on PATH, which makes `invocation()`
the spelling every adopter sees and the one RK1154's three assertions were never read under.
Deleted at the end, and never inside the repository — a script that wrote into the tree it is
measuring would be the arrangement RK105 removes from the corpora, with the arrow reversed.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import venv
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]

#: What the workflow's `pip install` line installs, so the two cannot drift into different runs.
EXTRAS = ".[dev]"


@dataclass(frozen=True, slots=True)
class Difference:
    """One way CI's environment is not this one, and whether this run reproduced it."""

    #: What it is, in the words the task that found it used.
    name: str
    #: How it is applied here — or, where ``applied`` is false, what is missing.
    how: str
    applied: bool = True

    def __str__(self) -> str:
        return f"  {'applied ' if self.applied else 'skipped '} {self.name}: {self.how}"


def floor() -> tuple[int, int]:
    """The oldest Python this package supports, read from where it is declared.

    `requires-python` is what an installer enforces, so this reads it rather than restating it —
    the same rule `tests/test_invariants` applies to the calls above that floor (RK1158).
    """
    declared = re.search(
        r'requires-python\s*=\s*">=(\d+)\.(\d+)"',
        (HERE / "pyproject.toml").read_text(encoding="utf-8"),
    )
    if declared is None:
        raise SystemExit("pyproject.toml declares no requires-python floor")
    return int(declared[1]), int(declared[2])


def interpreter() -> tuple[str, Difference]:
    """The floor interpreter if this machine has one, and what that means for the run.

    Two spellings and no more: the version launcher Windows installs and the suffixed name every
    other platform uses. A third way of finding a Python is a guess about somebody's machine, and
    the honest answer where neither is here is the one this returns — the current interpreter, and
    a difference reported as skipped.
    """
    want = floor()
    tag = f"{want[0]}.{want[1]}"
    for argv in ([shutil.which("py") or "py", f"-{tag}"], [f"python{tag}"]):
        if shutil.which(argv[0]) is None:
            continue
        found = subprocess.run(
            [*argv, "-c", "import sys; print(sys.executable)"],
            capture_output=True,
            text=True,
            check=False,
        )
        if found.returncode == 0 and found.stdout.strip():
            return found.stdout.strip(), Difference(
                "the floor interpreter", f"Python {tag} at {found.stdout.strip()}"
            )
    running = ".".join(str(part) for part in sys.version_info[:2])
    return sys.executable, Difference(
        "the floor interpreter",
        f"no Python {tag} on this machine, so the suite runs on {running} — the one difference "
        f"this run cannot apply",
        applied=False,
    )


def _gitconfig(into: Path) -> Path:
    """A global config with **no identity and every `safe.directory`** the real one declares.

    Nulling the global config is the obvious way to reproduce a runner's missing `user.name`, and
    it is wrong by one fact: `safe.directory` lives there too, so the corpora — foreign checkouts
    somebody else owns — became unreadable and three pinned reads failed. That is this script's own
    red and not the gate's: on a runner those directories are absent and the tests skip.

    So the identity is what goes. Copied rather than passed through, because `GIT_CONFIG_GLOBAL`
    takes one path: a config listing only what makes another user's repository readable is the
    narrowest thing that keeps the difference honest.
    """
    listed = subprocess.run(
        ["git", "config", "--global", "--get-regexp", "^safe[.]"],
        capture_output=True,
        text=True,
        check=False,
    )
    lines = ["[safe]\n"]
    for row in listed.stdout.splitlines():
        key, _, value = row.partition(" ")
        if key.startswith("safe.") and value:
            lines.append(f"\t{key.removeprefix('safe.')} = {value}\n")
    written = into / "gitconfig"
    written.write_text("".join(lines), encoding="utf-8")
    return written


def environment(home: Path, cache: Path, config: Path, scripts: Path) -> dict[str, str]:
    """The environment CI has, composed rather than inherited.

    Every entry is a fact a task measured. The git config is RK1153's: a runner has no `user.name`,
    which is what made three fixture calls that spawned git around the suite's own runner pass here
    and fail there — see :func:`_gitconfig` for the one thing that stays. The two directories are
    RK1155's: the launcher resolves an engine through the cache and the plugin registry, so a
    developer who has installed the plugin cannot test the absence of one. `CLAUDE_PROJECT_DIR`
    goes because a session sets it and CI does not.

    `PATH` leads with the venv's scripts directory, which is the whole point of the venv: the
    console script has to be found for `invocation()` to be the spelling an adopter reads (RK254).
    """
    return {
        **{k: v for k, v in os.environ.items() if k != "CLAUDE_PROJECT_DIR"},
        "PATH": os.pathsep.join((str(scripts), os.environ.get("PATH", ""))),
        "HOME": str(home),
        "USERPROFILE": str(home),
        "GIT_CONFIG_GLOBAL": str(_gitconfig(home)),
        "GIT_CONFIG_SYSTEM": os.devnull,
        "XDG_CACHE_HOME": str(cache),
        "CLAUDE_CONFIG_DIR": str(config),
    }


def differences(interpreted: Difference) -> tuple[Difference, ...]:
    """Every way this run is CI and not a terminal, in the order the summary prints them.

    A tuple and not a log line per step: what a reader needs is the *set*, so that a difference
    added tomorrow is a row here and a difference this machine cannot apply is visible beside the
    three that were. The environment ones are stated as applied because :func:`environment`
    composes them unconditionally — there is nothing about a machine that can refuse them.
    """
    return (
        Difference("the installed package", f"pip install {EXTRAS} into a throwaway venv"),
        Difference("no ambient git identity", "a global config carrying safe.directory and no user"),
        Difference("no plugin cache or registry", "XDG_CACHE_HOME and CLAUDE_CONFIG_DIR in a temp"),
        interpreted,
        # The fifth, and it is a row *because* it cannot be applied: the corpora are absolute paths
        # in `tests/corpora.py` (RK105), so nothing in an environment can make them absent, and a
        # runner has neither. What that costs is stated rather than left in a count — the pinned
        # reads run here and skip there, so this run tests more than the gate does, not less.
        Difference(
            "the corpora absent",
            "Shio and Turing are on this machine and on no runner, so their pinned reads run here",
            applied=False,
        ),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="like_ci",
        description=__doc__.splitlines()[0],
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the differences and the commands, and run nothing",
    )
    parser.add_argument(
        "rest",
        nargs="*",
        help="arguments for pytest, e.g. tests/test_guarding.py -k served",
    )
    args = parser.parse_args(argv)

    python, interpreted = interpreter()
    print("like_ci: the gate's environment, as far as this machine reaches it")
    for one in differences(interpreted):
        print(one)
    if args.dry_run:
        return 0

    into = Path(tempfile.mkdtemp(prefix="roadkeep-like-ci-"))
    try:
        builder = venv.EnvBuilder(with_pip=True, symlinks=os.name != "nt")
        created = into / "venv"
        if python == sys.executable:
            builder.create(created)
        else:
            # A venv of *that* interpreter, which `venv.EnvBuilder` cannot make for another
            # Python: it builds one for the process running it, so the floor interpreter builds
            # its own.
            subprocess.run([python, "-m", "venv", str(created)], check=True)
        scripts = created / ("Scripts" if os.name == "nt" else "bin")
        inside = scripts / ("python.exe" if os.name == "nt" else "python")
        for command in (
            [str(inside), "-m", "pip", "install", "--quiet", "--upgrade", "pip"],
            [str(inside), "-m", "pip", "install", "--quiet", EXTRAS],
        ):
            subprocess.run(command, check=True, cwd=str(HERE))
        home = into / "home"
        for directory in ("home", "cache", "config"):
            (into / directory).mkdir(exist_ok=True)
        done = subprocess.run(
            [str(inside), "-m", "pytest", "-q", *args.rest],
            cwd=str(HERE),
            env=environment(home, into / "cache", into / "config", scripts),
            check=False,
        )
        return done.returncode
    finally:
        shutil.rmtree(into, ignore_errors=True)


if __name__ == "__main__":  # pragma: no cover - a developer's command
    raise SystemExit(main())
