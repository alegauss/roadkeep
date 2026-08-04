"""The one fact a test asserting about this checkout cannot get from its own assertion: whether
the tree moved under the run (RK263).

Observed while shipping RK261: one run reported six failures and the same source reported 1940
passed, with one genuine fix between them. Five of the six were not about the code. What ran
beside them was `git worktree add` and `git worktree remove` against this repository, and the
mechanism is not the point — the point is that nothing in the output said so, so a red about a
tree being written was indistinguishable from a red about a defect.

These tests are deliberate and stay. This repository is the format's conformance fixture, and
the version checks are what keep RK153's patch bump honest — moving them to a `tmp_path` copy
would assert about the copy. What they have in common is the shape of the comparison: the
process imported `roadkeep` at collection, and each of them holds that import against the live
tree. So a bump landing mid-run makes the disk right and the constant stale, and the test says
`0.1.236 != 0.1.237` as though a file had been forgotten.

:func:`checkout` is the answer, and its precedent is in the suite already:
`test_this_checkout_reports_the_commit_it_is_at` skips where git cannot place the tree, because
a machine without git is not a defect. A tree being written while the run reads it is the same
kind of not-a-defect. Two rules keep the skip from becoming a place failures hide:

* **Fingerprinted once, at session start, for a declared set** (:data:`WATCHED`). A test asking
  about anything else is an error and not a pass: the skip is only honest about facts that were
  recorded before the import it defends.
* **Loud.** Every skip is a `UserWarning` as well, which `pytest -W error` turns into the
  failure a run that wants to be told asks for — the same contract `test_corpora` states.
"""

from __future__ import annotations

import subprocess
import warnings
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[1]

#: What a test may ask about, relative to the repository root. Every entry is a file the
#: running process read at import and something asserts against on disk: `__init__.py` is the
#: version `roadkeep.__version__` came from, and the manifest is the only second place that
#: number is written (RK19). `pyproject.toml` is not one — it reads the module by AST, so it
#: states no number of its own to disagree.
WATCHED = (
    "src/roadkeep/__init__.py",
    ".claude-plugin/plugin.json",
)


def _stamp(path: Path) -> tuple[int, int] | None:
    """Size and mtime, which is what a rewrite moves. Not a digest: this is asked once per
    session and again per test, and hashing the tree to answer "did anything write here" is
    paying for a certainty the question does not have anyway."""
    try:
        stat = path.stat()
    except OSError:
        return None
    return (stat.st_size, stat.st_mtime_ns)


def _head() -> str | None:
    """The commit, or `None` where git cannot place the tree — the state
    `test_this_checkout_reports_the_commit_it_is_at` already skips on."""
    try:
        finished = subprocess.run(
            ["git", "-C", str(HERE), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    return finished.stdout.strip() or None


class Checkout:
    """The tree as it was when the process imported it, and whether it still is.

    Held by value and never re-read as a whole: `moved` compares the recorded fact against the
    live one at the moment a test asks, so a rewrite that happens between two tests is reported
    to the second and not to the first, which is exactly the resolution the defect has.
    """

    def __init__(self, stamps: dict[str, tuple[int, int] | None], head: str | None) -> None:
        self.stamps = stamps
        self.head = head

    def moved(self, *paths: str, head: bool = False) -> tuple[str, ...]:
        """Which of the named facts are not what the session started with."""
        drift = []
        for name in paths:
            if name not in self.stamps:
                raise AssertionError(
                    f"{name} is not in WATCHED, so nothing recorded it before the import "
                    f"this would defend: add it there or assert without this fixture"
                )
            now = _stamp(HERE / name)
            if now != self.stamps[name]:
                drift.append(f"{name} was rewritten during this run")
        if head and (now_head := _head()) != self.head:
            drift.append(f"HEAD moved from {self.head} to {now_head}")
        return tuple(drift)

    def steady(self, *paths: str, head: bool = False) -> None:
        """Skip — loudly — where the tree moved under the assertion about to be made."""
        drift = self.moved(*paths, head=head)
        if not drift:
            return
        reason = (
            f"the tree moved while this run read it ({'; '.join(drift)}): the process "
            f"imported one revision and the assertion is about another, so this says "
            f"nothing about the code"
        )
        warnings.warn(reason, UserWarning, stacklevel=2)
        pytest.skip(reason)


#: Read at conftest import, which is before pytest imports a test module and therefore before
#: the process imports `roadkeep` — the anchor the whole fixture is about. A session-scoped
#: fixture body would run at the *first test that asks*, which is late enough for a bump landing
#: between collection and that test to be recorded as the starting state and then never reported.
_AT_START = Checkout({name: _stamp(HERE / name) for name in WATCHED}, _head())


@pytest.fixture(scope="session")
def checkout() -> Checkout:
    """The tree as the run found it — see :class:`Checkout` and :data:`_AT_START`."""
    return _AT_START
