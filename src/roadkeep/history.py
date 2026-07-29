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


@dataclass(frozen=True, slots=True)
class Change:
    """One changed line, numbered **on the side it exists on**.

    Which side matters, and getting it wrong is what makes a diff-based check cry wolf: a
    deleted paragraph has no line number in the file as it is now, so attributing it to
    the new-side position lands it in whichever section happens to precede the hole.
    """

    lineno: int
    text: str
    #: True for a line the diff added (new side), False for one it removed (old side).
    added: bool


@dataclass(frozen=True, slots=True)
class Touched:
    """Every line a diff changed in one file (RK36)."""

    changes: tuple[Change, ...] = ()

    @property
    def lines(self) -> tuple[str, ...]:
        """The changed text, either side — added, removed or reworded.

        All three mean somebody had the line open, which is the only thing the check is
        entitled to conclude: deciding whether the edit was *responsive* would be reading
        prose (L4).
        """
        return tuple(change.text for change in self.changes)


_HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def resolves(config: Config, rev: str) -> bool:
    """Does git know this revision? False for `HEAD` in a repository with no commits."""
    try:
        _run(config.root, "rev-parse", "--verify", "--quiet", f"{rev}^{{commit}}")
    except HistoryUnavailable:
        return False
    return True


def touched_since(config: Config, rev: str, role: str) -> Touched:
    """The diff of one governed file from ``rev`` to the working tree.

    `-U0`, because context lines would put a neighbouring section inside the span and the
    whole value of this check is that it names the section somebody actually opened.
    """
    if not config.has(role) or not config.path(role).is_file():
        return Touched()
    try:
        relative = config.path(role).relative_to(config.root)
    except ValueError:
        relative = config.path(role)
    output = _run(config.root, "diff", "--no-color", "-U0", rev, "--", str(relative))
    return _read_diff(output)


def _read_diff(output: str) -> Touched:
    """Walk a `-U0` diff, numbering each changed line on its own side."""
    changes: list[Change] = []
    old = new = 0
    for raw in output.splitlines():
        hunk = _HUNK_RE.match(raw)
        if hunk:
            old, new = int(hunk.group(1)), int(hunk.group(3))
            continue
        if raw.startswith(("+++", "---")):
            continue
        if raw.startswith("+"):
            changes.append(Change(lineno=new, text=raw[1:], added=True))
            new += 1
        elif raw.startswith("-"):
            changes.append(Change(lineno=old, text=raw[1:], added=False))
            old += 1
    return Touched(changes=tuple(changes))


def content_at(config: Config, rev: str, role: str) -> str:
    """One governed file as of ``rev``, or empty when it was not there yet.

    Needed because a removal has to be attributed to the section that *held* it, and that
    section may no longer exist — which is exactly the case `ship` produces, and the one a
    check must not report (RK36).
    """
    if not config.has(role):
        return ""
    try:
        relative = config.path(role).relative_to(config.root)
    except ValueError:
        relative = config.path(role)
    try:
        return _run(config.root, "show", f"{rev}:{relative.as_posix()}")
    except HistoryUnavailable:
        return ""


def origin_of(config: Config, task_id: str) -> Origin:
    """The commit that proposed the task and the one that shipped it, if each exists."""
    needle = f"**{task_id}**"  # the bold id, so RK1 does not match RK10
    proposed = _first_touching(config, needle, "roadmap")
    shipped = _first_touching(config, needle, "changelog")
    return Origin(task_id=task_id, proposed_in=proposed, shipped_in=shipped)


@dataclass(frozen=True, slots=True)
class Gap:
    """An id that is in neither file, and the commit that took it out (RK32).

    ``removed_in`` is None when history cannot answer — a squash, a shallow clone, a line
    that never reached a commit. That prints as *unresolvable* and not as retired, on
    RK28's reasoning: an absent answer and a negative one are different answers, and
    collapsing them here would invent a decision nobody recorded.
    """

    id: str
    number: int
    removed_in: Commit | None

    @property
    def resolved(self) -> bool:
        return self.removed_in is not None


def gaps(config: Config) -> tuple[Gap, ...]:
    """Every id below the highest that no line carries, oldest number first.

    The gaps are computed from the *entries* of both files rather than from a text scan:
    an id mentioned in prose — `agents.md` cites plenty — is still a gap, because what is
    missing is the record of a decision and not the string.
    """
    from roadkeep.ids import highest  # here, because ids.py reads this module's config

    top = highest(config)
    if top is None:
        return ()
    recorded: set[int] = set()
    for role in ("roadmap", "changelog"):
        if not config.has(role) or not config.path(role).is_file():
            continue
        for task_id in config.document(role).by_id():
            number = _number(task_id, config.schema.prefix)
            if number is not None:
                recorded.add(number)
    return tuple(
        Gap(
            id=f"{config.schema.prefix}{number}",
            number=number,
            removed_in=_last_touching(config, f"**{config.schema.prefix}{number}**"),
        )
        for number in range(1, top.number + 1)
        if number not in recorded
    )


def _number(task_id: str, prefix: str) -> int | None:
    tail = task_id[len(prefix) :] if task_id.startswith(prefix) else ""
    return int(tail) if tail.isdigit() else None


def _last_touching(config: Config, needle: str) -> Commit | None:
    """The last commit whose roadmap diff mentions the id — where the line left.

    The last and not the first: the first added it. A removal is not distinguished from a
    rewording here, because a line that was reworded and is now absent still left in that
    commit, and the commit message is what the reader is being sent to read.
    """
    try:
        found = _touching_role(config, needle, "roadmap")
    except HistoryUnavailable:
        return None
    return found[-1] if found else None


def _first_touching(config: Config, needle: str, role: str) -> Commit | None:
    found = _touching_role(config, needle, role)
    return found[0] if found else None


def _touching_role(config: Config, needle: str, role: str) -> tuple[Commit, ...]:
    if not config.has(role):
        return ()
    try:
        relative = config.path(role).relative_to(config.root)
    except ValueError:
        relative = config.path(role)
    return commits_touching(config.root, needle, relative)
