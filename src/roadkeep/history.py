"""Reaching the reasoning behind a shipped decision (RK31).

Shipping deletes the rationale section, the ledger keeps one line, and the argument
survives only in a commit message. That is not a bad place to keep it — it is the one
place that cannot drift from the code — but it is unreachable in practice: answering
"why is this like this" costs a `git log -S` over the whole history, so the question
goes unasked and the design gets re-litigated instead.

**The pointer is derived, not stored.** The obvious design — write the shipping commit's
hash into the ledger entry — is wrong, and the objection is decisive: `squash`, `amend`
and `rebase` rewrite that hash, and a dead hash reads exactly like a live one. A stored
pointer would rot silently, which is worse than no pointer at all.

So resolve it from git on demand. The commit that shipped a task is, by construction,
the commit that **added its id to the ledger**, and the commit that proposed it is the
one that added the id to the roadmap. Both are found with `git log -S` scoped to one
file, both are correct after any history rewrite, and neither costs a byte in the
documents. It also works retroactively: every task shipped before this module existed
is already addressable.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from roadkeep.config import Config

_UNIT = "\x1f"  # between fields
_RECORD = "\x1e"  # between commits — a body may hold newlines, so lines will not do
_FORMAT = _UNIT.join(["%H", "%h", "%aI", "%an", "%s", "%b"]) + _RECORD
_TIMEOUT = 20


class HistoryUnavailable(RuntimeError):
    """No git, or no repository — the answer is absent rather than negative."""


@dataclass(frozen=True, slots=True)
class Commit:
    sha: str
    short: str
    date: str
    author: str
    subject: str
    body: str

    @property
    def reasoning(self) -> str:
        """Subject plus body: the part a ledger line cannot hold."""
        return f"{self.subject}\n\n{self.body}".strip()


@dataclass(frozen=True, slots=True)
class Origin:
    """Where a task entered the backlog, and where it left it."""

    task_id: str
    proposed_in: Commit | None
    shipped_in: Commit | None


def git_available() -> bool:
    return shutil.which("git") is not None


def _run(root: Path, *args: str) -> str:
    if not git_available():
        raise HistoryUnavailable("git is not on PATH")
    try:
        # Fixed argv and shell=False: nothing here interpolates into a shell.
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=_TIMEOUT,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise HistoryUnavailable(str(error)) from error
    if result.returncode != 0:
        raise HistoryUnavailable(result.stderr.strip() or "git failed")
    return result.stdout


def _parse(output: str) -> tuple[Commit, ...]:
    commits: list[Commit] = []
    for record in output.split(_RECORD):
        record = record.strip("\n")
        if not record:
            continue
        fields = record.split(_UNIT)
        if len(fields) < 6:
            continue
        sha, short, date, author, subject, body = fields[:6]
        commits.append(
            Commit(
                sha=sha,
                short=short,
                date=date,
                author=author,
                subject=subject,
                body=body.strip(),
            )
        )
    return tuple(commits)


def commits_touching(root: Path, needle: str, path: Path | None = None) -> tuple[Commit, ...]:
    """Commits whose diff mentions ``needle`` at all, oldest first.

    Two deliberate choices:

    * **Not `--grep`.** Putting the id in the commit subject is a convention an author
      can forget; a commit that moved a task's line *must* contain the id in its diff.
    * **`-G`, not `-S`.** `-S` counts occurrences and reports only a *net* change, so
      rewording a line — the id present before and after — is invisible to it. `-G`
      matches any diff that mentions the id, which is what "every commit that touched
      this task" means.

    One thing neither flag can recover: if a task is proposed and shipped inside one
    commit, the roadmap ends the commit as it began and there is no diff to find. The
    squash destroyed that fact; the shipping commit, which is the one carrying the
    reasoning, still resolves.
    """
    args = ["log", "--reverse", f"--format={_FORMAT}", "-G", re.escape(needle)]
    if path is not None:
        args += ["--", str(path)]
    return _parse(_run(root, *args))


def origin_of(config: Config, task_id: str) -> Origin:
    """The commit that proposed the task and the one that shipped it, if each exists."""
    needle = f"**{task_id}**"  # the bold id, so RK1 does not match RK10
    proposed = _first_touching(config, needle, "roadmap")
    shipped = _first_touching(config, needle, "changelog")
    return Origin(task_id=task_id, proposed_in=proposed, shipped_in=shipped)


def _first_touching(config: Config, needle: str, role: str) -> Commit | None:
    if not config.has(role):
        return None
    try:
        relative = config.path(role).relative_to(config.root)
    except ValueError:
        relative = config.path(role)
    found = commits_touching(config.root, needle, relative)
    return found[0] if found else None
