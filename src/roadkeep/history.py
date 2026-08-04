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
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path

from roadkeep.config import PROSE_ROLES, Config
from roadkeep.schema import Schema
from roadkeep.sections import find

_UNIT = "\x1f"  # between fields
_RECORD = "\x1e"  # between commits — a body may hold newlines, so lines will not do
_FORMAT = _UNIT.join(["%H", "%h", "%aI", "%an", "%s", "%b"]) + _RECORD
_TIMEOUT = 20
#: What `-z` separates paths by, on both ends of `check-ignore` (RK213).
_NUL = chr(0)


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
    return _bytes(root, *args).decode("utf-8", errors="replace")


def _bytes(root: Path, *args: str) -> bytes:
    """The raw output, because one caller reads a file and not a report (RK84).

    Bytes and not ``text=True``: universal newlines would translate CRLF to LF, and a
    baseline that read the file at a revision through that translation would report every
    ending as changed — on the two things `lint` measures in bytes, the round-trip (L3)
    and a budget (RK30). Text callers decode here instead, which is the same string
    `text=True` gave them minus the rewriting.
    """
    if not git_available():
        raise HistoryUnavailable("git is not on PATH")
    try:
        # Fixed argv and shell=False: nothing here interpolates into a shell.
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            timeout=_TIMEOUT,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise HistoryUnavailable(str(error)) from error
    if result.returncode != 0:
        raise HistoryUnavailable(
            result.stderr.decode("utf-8", errors="replace").strip() or "git failed"
        )
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


def commits_touching(
    root: Path, needle: str, path: Path | None = None, *, literal: bool = True
) -> tuple[Commit, ...]:
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

    ``literal`` off hands the needle to git as the pattern it already is, for the one
    caller with a shape rather than a string to find (RK212): a heading is spelled two ways
    across live outline projects — `### VIII.1` in Shio and Turing, `### §I.1` in
    claude-tray — and an escaped literal would answer for one of them and silently miss the
    other, which a reader would read as "nobody ever wrote it".
    """
    args = ["log", "--reverse", f"--format={_FORMAT}"]
    if not literal:
        # git reads `-G` as a *basic* regex, where `?` is a literal character rather than a
        # quantifier — so the optional sigil below would be searched for as a `?`.
        args.append("--extended-regexp")
    args += ["-G", re.escape(needle) if literal else needle]
    if path is not None:
        args += ["--", str(path)]
    return _parse(_run(root, *args))


def check_ignore(root: Path, paths: Sequence[str]) -> frozenset[str]:
    """Which of these paths the repository has declared it will never track (RK213).

    `check-ignore` and not a table of directory names, because the repository already
    carries the declaration: the same `.gitignore`, `.git/info/exclude` and
    `core.excludesFile` a developer's own `git status` reads, so the gate and the author
    cannot disagree about what is tracked here (L6, answered by the project rather than by
    this tool). Exit 1 means *none matched*, which is an answer and not a failure — the only
    reason this cannot go through :func:`_run`.

    `-z` on both ends: a path holding a quote or a non-ASCII byte arrives as itself rather
    than as git's escaped rendering, which is :func:`tracked_at`'s reason one command along.
    """
    if not paths:
        return frozenset()
    if not git_available():
        raise HistoryUnavailable("git is not on PATH")
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "check-ignore", "--stdin", "-z"],
            input=_NUL.join(paths).encode("utf-8"),
            capture_output=True,
            timeout=_TIMEOUT,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise HistoryUnavailable(str(error)) from error
    if result.returncode not in (0, 1):
        raise HistoryUnavailable(
            result.stderr.decode("utf-8", errors="replace").strip() or "git failed"
        )
    listed = result.stdout.decode("utf-8", errors="replace")
    return frozenset(name for name in listed.split(_NUL) if name)


#: What `check-attr` answers where a path has no value for the attribute at all.
UNSPECIFIED = "unspecified"


def check_attr(root: Path, attribute: str, paths: Sequence[str]) -> dict[str, str]:
    """What git resolves `attribute` to for each of these paths (RK273).

    `check-attr` and not a read of `<root>/.gitattributes`, because that file is not where the
    answer lives: git consults a `.gitattributes` in every directory from the path upward, then
    `$GIT_DIR/info/attributes`, then `core.attributesFile`, with the deepest rule winning. A
    read of the root file alone reports files unsent that git sends — measured, with
    `.git/info/attributes` carrying the line. The repository already holds the declaration, so
    it is asked rather than guessed at, the same choice :func:`check_ignore` makes (L6).

    The value is git's own word: a driver's name where one is set, or :data:`UNSPECIFIED`,
    `set`, `unset`. Richer than the boolean a string comparison yields — a path sent to a
    *different* driver is a deliberate act, and invisible to a read looking only for one name.

    `-z`, for the reason :func:`check_ignore` gives one command along: a path holding a quote
    or a non-ASCII byte arrives as itself and not as git's escaped rendering. The paths go as
    arguments rather than down `--stdin`, because a project declares a handful of governed
    files and that keeps this on :func:`_bytes` — the package's one place with a timeout, an
    encoding and a single failure type.
    """
    if not paths:
        return {}
    listed = _bytes(root, "check-attr", "-z", attribute, "--", *paths).decode(
        "utf-8", errors="replace"
    )
    # Triples, `<path>\0<attribute>\0<value>\0`, so the walk is by threes and not by lines —
    # a value is one field of a record here, never a line of output.
    fields = [field for field in listed.split(_NUL) if field != ""]
    return {
        fields[index]: fields[index + 2]
        for index in range(0, len(fields) - 2, 3)
        if fields[index + 1] == attribute
    }


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


def changed_lines(config: Config, rev: str, path: Path) -> frozenset[int] | None:
    """Line numbers this working tree changed in one file against ``rev`` (RK60).

    ``None`` means git cannot narrow this file — no history, no `git`, or a file it does not
    track yet — and the caller then judges all of it, because a file nothing can diff is a
    file nobody can be excused from.

    A path and not a role, because the `Stop` gate also holds the instruction files a
    `[budgets]` entry names (RK30), and those are governed by nothing.
    """
    try:
        relative = path.resolve().relative_to(config.root)
    except ValueError:
        relative = path
    try:
        if not _run(config.root, "ls-files", "--", str(relative)).strip():
            return None  # untracked: every line of it arrived without a commit
        output = _run(config.root, "diff", "--no-color", "-U0", rev, "--", str(relative))
    except HistoryUnavailable:
        return None
    return frozenset(
        change.lineno for change in _read_diff(output).changes if change.added
    )


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
    raw = blob_at(config, rev, config.path(role))
    return "" if raw is None else raw.decode("utf-8", errors="replace")


def blob_at(config: Config, rev: str, path: Path) -> bytes | None:
    """One file's bytes as of ``rev``, or ``None`` when that tree did not carry it (RK84).

    The two answers are kept apart because a baseline turns on the difference: an empty
    file was there and said nothing, and an absent one is a file the change *added* — so
    crediting it with the findings of a file it did not have would forgive every line of
    it. Bytes, because the caller measuring a budget is counting them (RK30).
    """
    try:
        relative = path.resolve().relative_to(config.root)
    except ValueError:
        relative = path
    try:
        return _bytes(config.root, "show", f"{rev}:{relative.as_posix()}")
    except HistoryUnavailable:
        return None


def tracked_at(config: Config, rev: str) -> frozenset[str]:
    """Every path in the tree at ``rev``, as git spells them (RK84).

    One `ls-tree` rather than a question per path: a ledger names 886 of them on the corpus
    this was measured against, and a subprocess each is the difference between a check and
    a thing nobody runs. `-z`, so a path holding a quote or a non-ASCII byte arrives as
    itself instead of as git's escaped rendering of it.
    """
    try:
        output = _run(config.root, "ls-tree", "-r", "--name-only", "-z", rev)
    except HistoryUnavailable:
        return frozenset()
    return frozenset(name for name in output.split("\0") if name)


def indexed(config: Config) -> frozenset[str]:
    """Every path the index carries, including one deleted from the working tree (RK217).

    :func:`tracked_now` without its subtraction, because the two answer different questions.
    *Does the repository still have this artefact* must not credit a file somebody deleted
    and did not stage — that is the finding the path check exists for. *Is this a directory
    the repository knows about* must: a ledger naming `lib/gone.py` after `lib/` was removed
    is precisely the case worth reporting, and a listing that had already forgotten `lib/`
    would make the token stop being a claim rather than become a finding.
    """
    try:
        listed = _run(config.root, "ls-files", "-z")
    except HistoryUnavailable:
        return frozenset()
    return frozenset(name for name in listed.split(chr(0)) if name)


def tracked_now(config: Config) -> frozenset[str]:
    """Every tracked path the working tree still **has**, as git spells them (RK173).

    :func:`tracked_at`'s answer for the run that has no revision, and asked for the same
    reason: two processes rather than a walk of the repository or a stat per path, so a
    check over a ledger naming hundreds of artefacts stays a check rather than a thing
    nobody runs. Git's own list, so a build directory nobody committed cannot satisfy a
    claim about the source.

    Minus what git calls deleted, which is the whole reason this is not `ls-files` alone:
    the index still carries a file removed from the tree and not yet staged, and crediting
    one would forgive exactly the finding this check exists for — an artefact that was there
    at the revision and is gone now. :func:`indexed` is the same listing without that
    subtraction, for the caller asking the other question.
    """
    listed = indexed(config)
    if not listed:
        return frozenset()
    try:
        removed = _run(config.root, "ls-files", "--deleted", "-z")
    except HistoryUnavailable:
        return frozenset()
    gone = {name for name in removed.split(chr(0)) if name}
    return frozenset(name for name in listed if name not in gone)


def dirty(config: Config) -> frozenset[str]:
    """Every path the working tree has changed, staged or not, untracked included (RK280).

    What a `git add -A` would put in the next commit, which is the list a scope is subtracted
    from — so it has to be exactly that list and not a tidier one: an untracked file is the
    new test somebody's session just wrote, and leaving it out would answer *your commit is
    clean* about the tree that carried the defect this exists for.

    `status --porcelain -z` and not a diff: one process, git's own spelling on every platform,
    and the rename case arrives as both its ends, which is the honest reading when the
    question is what a commit would touch. Empty where git cannot answer, the rule every
    reader here keeps — a checkout with no git is one this reports nothing about, never one
    it refuses.
    """
    try:
        listed = _run(config.root, "status", "--porcelain", "-z")
    except HistoryUnavailable:
        return frozenset()
    return frozenset(_dirty_paths(listed))


def _dirty_paths(listed: str) -> Iterator[str]:
    """The paths out of `status --porcelain -z`, whose records are not one per NUL.

    A rename spends **two** NUL-separated fields — `R  <to>\\0<from>` — so a naive split reads
    the origin as a record and its first two characters as a status code. Both ends are
    yielded, because both are paths the commit touches.
    """
    fields = [field for field in listed.split(_NUL) if field]
    index = 0
    while index < len(fields):
        record = fields[index]
        index += 1
        code, _, name = record[:2], record[2:3], record[3:]
        if not name:
            continue
        yield name
        if code[0] in "RC" and index < len(fields):
            yield fields[index]
            index += 1


@dataclass(frozen=True, slots=True)
class Cost:
    """What one commit changed: lines either side, and how many files (RK71).

    Both, because the two live corpora disagree about which one an author pays. Lines are
    what varies — 40 to 1384 here — and files are what an agent holds in context, which the
    "no size field" non-goal measured at 4 to 14. A derivation that reported one would be
    picking the axis for the reader.
    """

    sha: str
    short: str
    lines: int
    files: int


def added_ids(config: Config, role: str) -> dict[str, str]:
    """Which commit first added each id to one governed file: id → sha, oldest wins.

    One `git log -U0` over the file, not one pickaxe per id: 69 ids is 69 processes, which
    is the difference between a query and a thing nobody runs twice. The trade is that this
    reads *added lines* rather than asking about an id, so an id the file never carried is
    absent here where :func:`origin_of` would say so — which is why both exist.
    """
    if not config.has(role):
        return {}
    try:
        relative = config.path(role).relative_to(config.root)
    except ValueError:
        relative = config.path(role)
    output = _run(
        config.root,
        "log",
        "--reverse",
        f"--format={_RECORD}%H",
        "--no-color",
        "-U0",
        "--",
        str(relative),
    )
    bold = re.compile(rf"\*\*({config.schema.id_fragment})\*\*")
    first: dict[str, str] = {}
    for head, rows in _records(output):
        added = "\n".join(
            row for row in rows if row.startswith("+") and not row.startswith("+++")
        )
        for task_id in bold.findall(added):
            first.setdefault(task_id, head.strip())
    return first


def costs_of(config: Config, shas: tuple[str, ...]) -> dict[str, Cost]:
    """The size of each named commit, across every file it touched, in one call.

    `--no-walk`, so the argument list is the commit list and not a range: the commits that
    wrote a ledger entry are scattered through history and a range would count what sits
    between them. A binary file's numstat is `-`, and it counts as a file and no lines.
    """
    if not shas:
        return {}
    output = _run(
        config.root,
        "log",
        "--no-walk",
        f"--format={_RECORD}{_UNIT.join(['%H', '%h'])}",
        "--numstat",
        *shas,
    )
    out: dict[str, Cost] = {}
    for head, rows in _records(output):
        sha, _, short = head.partition(_UNIT)
        counted = [
            changed for changed in (_numstat(row) for row in rows) if changed is not None
        ]
        out[sha] = Cost(
            sha=sha, short=short or sha[:7], lines=sum(counted), files=len(counted)
        )
    return out


def _numstat(row: str) -> int | None:
    """One numstat row as the lines it changed, or None when the row is not one.

    A binary file reports `-` for both sides: it is a file that changed and no lines that
    did, which is what the caller counts it as rather than dropping it.
    """
    columns = row.split("\t")
    if len(columns) != 3:
        return None
    added, removed = columns[0], columns[1]
    return (int(added) if added.isdigit() else 0) + (
        int(removed) if removed.isdigit() else 0
    )


def _records(output: str) -> tuple[tuple[str, tuple[str, ...]], ...]:
    """Split a `--format=<record>…` log into (head line, following rows) pairs.

    The record separator and not newlines, for :data:`_FORMAT`'s reason: a subject or a diff
    line can hold anything, so only a byte no message carries can end a record.
    """
    out: list[tuple[str, tuple[str, ...]]] = []
    for record in output.split(_RECORD):
        rows = record.strip("\n").splitlines()
        if rows:
            out.append((rows[0], tuple(rows[1:])))
    return tuple(out)


def origin_of(config: Config, task_id: str) -> Origin:
    """The commit that proposed the task and the one that shipped it, if each exists."""
    needle = f"**{task_id}**"  # the bold id, so RK1 does not match RK10
    proposed = _first_touching(config, needle, "roadmap")
    shipped = _first_touching(config, needle, "changelog")
    return Origin(task_id=task_id, proposed_in=proposed, shipped_in=shipped)


@dataclass(frozen=True, slots=True)
class Cited:
    """An anchor somebody's prose still names, resolved against history (RK212)."""

    anchor: str
    #: The prose role the address was searched in, and the commits at each end.
    role: str
    written_in: Commit | None
    removed_in: Commit | None
    #: Whether the log that came back empty was a log worth trusting — :class:`Gap`'s split.
    searched: bool = False

    @property
    def live(self) -> bool:
        """Written and never removed: the section is still there and this is a live cite."""
        return self.written_in is not None and self.removed_in is None


def cited_origin(config: Config, anchor: str) -> Cited:
    """Where the design behind a dangling citation was written, and what took it away.

    The half of RK206 a verb cannot reach. `ship` names the sections left citing what it
    deleted, at the moment it deletes it; a reader meeting `§XVIII.12` a year later has no
    such moment, and the files hold no answer — `as_ledger` keeps no pointer, so nothing
    records which anchor a shipped design had.

    Measured before choosing this over a gate: 37 such references across this repository,
    claude-tray, Shio and Turing, and 36 of them are in `ref_scheme = "outline"` projects
    where the anchor carries no id at all. A finding would fail four files whose prose is
    correct; a *note* would be 28 of them in one Turing report, which is the output nobody
    reads that this project refuses elsewhere (RK16). So the answer is a question instead
    (L5) — it costs nothing until somebody meets the reference and asks.

    Both ends, because they are different facts: the commit that *wrote* the section says
    what the design was, and the one that *removed* it says which task took it. `-G` finds
    both (:func:`commits_touching`), so a history that cannot be searched answers neither —
    reported as :attr:`searched` rather than as an anchor nobody ever wrote, which is
    :class:`Gap`'s split and made for the same reason.
    """
    # The **heading**, not the citation. `§RK15` alone matches every commit that touched
    # somebody's prose about it, so the last one was RK206's ship — which deleted a
    # sentence citing §RK15 and never went near the section. `anchor_text` is the one
    # place a heading's spelling is decided (RK44), so the two schemes agree here for
    # free, and the trailing space keeps `§RK1` from answering for `§RK15`.
    # Grouped, not `§?`: git matches bytes, so an unparenthesised `?` would make the
    # *second* byte of the two-byte sigil optional and the pattern would match neither
    # spelling. Two live outline projects disagree about the sigil in a heading — Shio and
    # Turing write `### VIII.1`, claude-tray writes `### §I.1` and `### XVIII.12` in the
    # same file — so both are admitted, and the trailing space keeps `§I.1` from answering
    # for `§I.12`.
    needle = "# (§)?" + re.escape(anchor) + " "
    for role in ("improvements", "strategy"):
        if not config.has(role):
            continue
        try:
            found = _touching_role(config, needle, role, literal=False)
        except HistoryUnavailable:
            return Cited(anchor=anchor, role=role, written_in=None, removed_in=None)
        if not found:
            continue
        # Oldest first (`--reverse`), so the first wrote it. The last removed it only if
        # the address is gone now: a section still in the file has a last commit that
        # edited it, and calling that a removal would invent a deletion nobody made.
        gone = find(config.document(role), anchor) is None if config.path(role).is_file() else True
        return Cited(
            anchor=anchor,
            role=role,
            written_in=found[0],
            removed_in=found[-1] if gone else None,
            searched=True,
        )
    return Cited(anchor=anchor, role=PROSE_ROLES[0], written_in=None, removed_in=None, searched=True)


@dataclass(frozen=True, slots=True)
class Anchor:
    """One outline address a prose file declares, or used to (RK247)."""

    anchor: str
    role: str
    #: Whether a heading declares it *now*. False is retired: the section was deleted by a
    #: ship or a retirement, and every entry whose prose cited it still says `§<anchor>`.
    live: bool
    #: The first commit that wrote the heading, where history reaches it — a file older than
    #: the clone has live anchors nothing here can date, and that is not a state to hide.
    written_in: str = ""


def anchors(config: Config, role: str = "", family: str = "") -> tuple[Anchor, ...]:
    """Every anchor this **project** declares or ever declared, in outline order (RK247).

    The read `section add` could not make. Its refusals list the anchors that **exist**, so
    after a fully-shipped family that is none of them and the next free number looks like
    `.1` — while the ledger entries whose prose cited `.1` are still in the file, addressing
    a section that will now say something else. Observed on a project where §XXXVII.1 to
    §XXXVII.16 were all retired and all still cited, and the safe number was found by
    grepping the ledger by hand.

    So the source is the diff and not the file: an anchor is *used* once a heading declared
    it, and `ship` deleting that heading does not give the address back — the same rule
    `add` applies to ids, where retired-never-reused is the roadmap's own property. One
    `git log -U0` over the file, on :func:`added_ids`' reasoning: one process, not one
    pickaxe per anchor.

    Both sides of the diff are read. An anchor added before the clone's history and removed
    inside it appears only as a **removed** line, and that is exactly the retired address
    this exists to name; a live one the log cannot reach is still reported, off the file,
    with no commit to point at.

    ``family`` narrows to one subtree by segments — `XXXVII` gives `XXXVII.1` and
    `XXXVII.1.a` and never `XXXVIII.1`, the care :func:`~roadkeep.sections._extends` takes
    about where an anchor ends. Empty is the whole file.

    **Every declared prose role, unless ``role`` names one** (RK297). An address is spent
    once a heading used it, and a project declaring two files has one outline across both:
    reading the first alone answered `IX.5` on a project whose sibling file had spent to
    `IX.12`, so the read made to avoid spending an address twice handed back one already
    taken — and writing it is the doubled anchor `ref.ambiguous` reports at both headings.
    The direction `_pointers` took at RK172, one read over. ``role`` stays as the narrower
    question, and it narrows the *listing*: :func:`next_child` and :func:`next_family` are
    taken over whatever they are handed, so a caller that means the free address hands them
    the project.
    """
    roles = (role,) if role else PROSE_ROLES
    found = [
        one
        for name in roles
        if config.has(name)
        for one in _role_anchors(config, name)
    ]
    # Whether this file numbers in Roman is a fact about the whole set (RK293), so it is
    # settled once here and handed to the key — a per-segment decision would read `C` as 100
    # in a file whose families are letters, and sort a listing by an arithmetic nobody meant.
    numbered = bool(found) and all(numeral(one.anchor.split(".")[0]) for one in found)
    wanted = [one for one in found if _within(one.anchor, family)]
    # The role breaks the tie, so an address two files declare comes out as two adjacent
    # rows in `[files]` order — which is the doubling, reported rather than collapsed.
    return tuple(sorted(wanted, key=lambda one: (_ordinal(one, numbered), one.role)))


def _role_anchors(config: Config, role: str) -> list[Anchor]:
    """One prose file's share of the answer, live rows first and retired ones behind them."""
    live = _declared(config, role) if config.path(role).is_file() else ()
    first = _anchors_written(config, role, config.schema_for(role))
    return [
        Anchor(anchor=anchor, role=role, live=True, written_in=first.get(anchor, ""))
        for anchor in live
    ] + [
        Anchor(anchor=anchor, role=role, live=False, written_in=sha)
        for anchor, sha in first.items()
        if anchor not in live
    ]


def doubled(taken: Sequence[Anchor]) -> tuple[tuple[str, tuple[str, ...]], ...]:
    """Every address more than one prose file **declares now**, with the files (RK297).

    Reported here because this is the read that would otherwise hand one back as free: an
    author asking which address to take is the one who needs to know that two already answer
    to it. `lint` says the same thing as `ref.ambiguous`, and a gate is not a question — by
    the time it speaks, both headings exist and four verbs refuse to resolve between them.

    Live only. A retired address in two files is two histories of one outline and nothing to
    act on; two *headings* are the state a pointer cannot resolve against.
    """
    by_anchor: dict[str, list[str]] = {}
    for one in taken:
        if one.live:
            by_anchor.setdefault(one.anchor, []).append(one.role)
    return tuple(
        (anchor, tuple(roles)) for anchor, roles in by_anchor.items() if len(roles) > 1
    )


def next_child(taken: Sequence[Anchor], family: str) -> str:
    """The lowest numbered child of ``family`` no anchor above has ever used (RK247).

    Derived one past the highest **ever** used and not one past the highest surviving, which
    is the whole difference: the surviving one is often none. Numeric children only — a
    lettered or roman segment is somebody's numbering and not this tool's to continue (L4) —
    and the answer is a suggestion a reader takes, never an anchor any verb writes.
    """
    used = {
        int(child)
        for anchor in taken
        for child in (anchor.anchor[len(family) + 1 :].split(".")[:1] or [""])
        if anchor.anchor.startswith(f"{family}.") and child.isdigit()
    }
    return f"{family}.{max(used) + 1 if used else 1}"


#: A well-formed Roman numeral, and only one: `IIII` and `IL` spell nothing here, because a
#: reader that accepted them would order a file by a spelling nobody wrote.
_ROMAN = re.compile(r"^M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$")
_DIGITS = (("M", 1000), ("CM", 900), ("D", 500), ("CD", 400), ("C", 100), ("XC", 90),
           ("L", 50), ("XL", 40), ("X", 10), ("IX", 9), ("V", 5), ("IV", 4), ("I", 1))


def numeral(text: str) -> tuple[str, int] | None:
    """The number a segment spells and the system it spells it in, or None for neither.

    Arithmetic and not prose (L4): `IX` is a number written a way this tool has to *read*
    to sort by, because a listing ordered by a numeral's spelling puts `IX` between `IV` and
    `V` and cannot be scanned for a gap (RK293). Reading it is also what lets the next free
    address be derived rather than guessed off the tail of the listing.

    Strict, because a permissive reader is worse than none: a segment that is not a numeral
    must come back as one, so the caller can put it beside its siblings as text instead of
    among them as a number nobody meant.
    """
    if text.isdigit():
        return "decimal", int(text)
    if text and _ROMAN.match(text):
        value, rest = 0, text
        for glyph, amount in _DIGITS:
            while rest.startswith(glyph):
                value, rest = value + amount, rest[len(glyph) :]
        return "roman", value
    return None


def spell(value: int, system: str) -> str:
    """``value`` written the way ``system`` writes it — the inverse of :func:`numeral`."""
    if system != "roman":
        return str(value)
    out, left = [], value
    for glyph, amount in sorted(_DIGITS, key=lambda pair: -pair[1]):
        while left >= amount:
            out.append(glyph)
            left -= amount
    return "".join(out)


def next_family(taken: Sequence[Anchor]) -> str | None:
    """The lowest top-level address no anchor has ever used, or None where none derives.

    The question one line up from :func:`next_child`, and the normal case rather than an edge
    one (RK293): a block reused after its family shipped needs a *new* top-level, and until
    this the number was read off the tail of a listing sorted by spelling — where the last row
    is not the maximum. Derived from the same walk, so it costs nothing the command did not
    already pay.

    None where the top-levels are not one numbering, which is the honest answer and not a
    fallback: a file whose families are `A`, `B` and `C` has a next nobody can derive, and a
    guess printed beside a total reads exactly like a fact. Spelled in the system of the
    family that holds the maximum, because that is the sequence being continued.
    """
    read = {top: numeral(top) for top in {one.anchor.split(".")[0] for one in taken}}
    if not read or any(value is None for value in read.values()):
        return None
    system, highest = max((value for value in read.values() if value), key=lambda one: one[1])
    return spell(highest + 1, system)


def _declared(config: Config, role: str) -> tuple[str, ...]:
    from roadkeep.sections import anchored  # noqa: PLC0415 - RK260

    return tuple(section.anchor for section in anchored(config.document(role)))


def _anchors_written(config: Config, role: str, schema: Schema) -> dict[str, str]:
    """Anchor → the first sha whose diff on this file carries its heading, oldest first."""
    from roadkeep.sections import anchor_of  # noqa: PLC0415 - RK260

    try:
        relative = config.path(role).relative_to(config.root)
    except ValueError:
        relative = config.path(role)
    try:
        output = _run(
            config.root,
            "log",
            "--reverse",
            f"--format={_RECORD}%H",
            "--no-color",
            "-U0",
            "--",
            str(relative),
        )
    except HistoryUnavailable:
        return {}
    first: dict[str, str] = {}
    for head, rows in _records(output):
        for row in rows:
            if row[:1] not in ("+", "-") or row.startswith(("+++", "---")):
                continue
            # A heading and not any line that starts with the anchor's spelling: under an
            # outline the anchor is a bare number, so a table row or a bullet beginning
            # `XXXVII.4` would otherwise register an address nobody declared.
            text = row[1:].lstrip()
            if not text.startswith("#"):
                continue
            # Read the way a parsed heading is read — `Heading.text` is what follows the
            # hashes, and :func:`anchor_of` is written against that.
            anchor = anchor_of(text.lstrip("#").lstrip(), schema)
            if anchor is not None:
                first.setdefault(anchor, head.strip())
    return first


def _within(anchor: str, family: str) -> bool:
    """Is this anchor the family or under it, segment by segment rather than by string."""
    if not family:
        return True
    segments, wanted = anchor.split("."), family.split(".")
    return segments[: len(wanted)] == wanted


def _ordinal(anchor: Anchor, numbered: bool = False) -> tuple[object, ...]:
    """File order is not sort order once retired addresses are back in the list, so the
    segments are compared as numbers where they are numbers and as text where they are not —
    `.2` before `.10`, and a lettered segment beside its siblings rather than among them.

    ``numbered`` reads a Roman segment as the number it spells (RK293), and is decided over
    the whole set rather than per segment: `C` and `D` are numerals on a file numbered in
    Roman and are letters on one whose families are `A` to `F`, and only the set says which.
    """
    return tuple(
        (0, int(part), "")
        if part.isdigit()
        else ((0, read[1], "") if numbered and (read := numeral(part)) else (1, 0, part))
        for part in anchor.anchor.split(".")
    )


@dataclass(frozen=True, slots=True)
class Gap:
    """An id that is in neither file, and the commit that took it out (RK32).

    ``removed_in`` is None for two unlike reasons, and RK95 is the record of them having
    read alike. A history that **cannot** be searched — no git, no repository, a shallow
    clone — answers nothing; a complete one that mentions the id nowhere answers that no
    line ever carried it, which is the shape of a number skipped when a batch was
    allocated. The first prints as *unresolvable* and the second as *never carried*, on
    RK28's reasoning: an absent answer and a negative one are different answers, and
    collapsing them here would invent a decision nobody recorded — or deny one that was.
    """

    id: str
    number: int
    removed_in: Commit | None
    #: Whether the log that came back empty was a log worth trusting.
    searched: bool = False

    @property
    def resolved(self) -> bool:
        return self.removed_in is not None

    @property
    def never_carried(self) -> bool:
        """Searched to the root commit and found nowhere: skipped, not removed."""
        return self.removed_in is None and self.searched


def gaps(config: Config) -> tuple[Gap, ...]:
    """Every id below the highest that no line carries, oldest number first.

    The gaps are computed from the *entries* of both files rather than from a text scan:
    an id mentioned in prose — `agents.md` cites plenty — is still a gap, because what is
    missing is the record of a decision and not the string.

    Per family, and in declared order (RK74): each track counts on its own, so a `C##`
    that reached 40 says nothing about which `V##` are missing, and one range walked over
    the highest id anywhere would report every unreached number of every other track.
    """
    searched = searchable(config)
    return tuple(
        gap
        for family in config.schema.prefixes
        for gap in _gaps_in(config, family, searched)
    )


def searchable(config: Config) -> bool:
    """Whether an empty `git log` here means *never* rather than *cannot tell* (RK95).

    A missing git, a directory that is not a repository and a shallow clone all return
    nothing for an id some commit does carry. Only a history that reaches its root commit
    makes the absence of a hit a fact about the id instead of one about the clone.

    Asked once per call and not per gap: it is a property of the checkout, and the answer
    is what separates the two ways :class:`Gap` has of holding no commit.
    """
    try:
        answer = _run(config.root, "rev-parse", "--is-shallow-repository").strip()
    except HistoryUnavailable:
        return False
    return answer == "false"


def _gaps_in(config: Config, family: str, searched: bool) -> tuple[Gap, ...]:
    from roadkeep.ids import highest  # here, because ids.py reads this module's config

    top = highest(config, family)
    if top is None:
        return ()
    recorded: set[int] = set()
    for role in ("roadmap", "changelog"):
        if not config.has(role) or not config.path(role).is_file():
            continue
        for task_id in config.document(role).by_id():
            number = _number(task_id, family)
            if number is not None:
                recorded.add(number)
    return tuple(
        Gap(
            id=f"{family}{number}",
            number=number,
            removed_in=_last_touching(config, f"**{family}{number}**"),
            searched=searched,
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


def _touching_role(
    config: Config, needle: str, role: str, *, literal: bool = True
) -> tuple[Commit, ...]:
    if not config.has(role):
        return ()
    try:
        relative = config.path(role).relative_to(config.root)
    except ValueError:
        relative = config.path(role)
    return commits_touching(config.root, needle, relative, literal=literal)
