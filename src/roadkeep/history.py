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
from collections.abc import Sequence
from dataclasses import dataclass, replace
from pathlib import Path

from roadkeep.config import PROSE_ROLES, Config
from roadkeep.kernel.document import Document
from roadkeep.kernel.schema import ARROW, REF_SEPARATOR, Schema, split_ref
from roadkeep.sections import Section, anchored, find, owners

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


def revisions_of(
    config: Config, path: Path, first: int, last: int
) -> tuple[Commit, ...]:
    """Every commit that touched these lines of this file, oldest first (RK1163).

    `-L` and not `-G`, which is the difference between a *span* and a mention: a section's
    heading appears in the diff of the commit that wrote it and of nothing else, so a body-only
    `section amend` — the ordinary way a design is revised — is invisible to a needle. That is
    RK1126's finding one module over, and it is the whole reason this reads a range.

    The range is the section's own span, resolved through history by git rather than by this
    reader: `-L` follows the lines as the file moves around them, which no line number stored
    here could. `-s` suppresses the diffs, since what is wanted is the commits.
    """
    where = str(path if not path.is_absolute() else path.relative_to(config.root))
    return _parse(
        _run(
            config.root,
            "log",
            "--reverse",
            "-s",
            f"--format={_FORMAT}",
            f"-L{first},{last}:{where}",
        )
    )


def precedes(config: Config, earlier: str, later: str) -> bool:
    """Whether one commit is an ancestor of another — the ordering dates cannot give (RK1163).

    Two commits made in the same second carry the same ISO timestamp, so a date compare answers
    *no* about a design that plainly predates a ship; and a rebase can order dates against the
    history. What git already knows is the ancestry, which is the question actually being asked:
    was this written before that landed.

    A commit is its own ancestor, so an identical pair answers True and the caller excludes it —
    a design revised *in* the shipping commit has read what changed, which is the one case this
    must not report.
    """
    if not earlier or not later:
        return False
    try:
        _run(config.root, "merge-base", "--is-ancestor", earlier, later)
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


def changed_paths(config: Config, rev: str) -> frozenset[str]:
    """Every path this working tree changed against ``rev``, repo-relative (RK1228).

    The half `--since` already had for the governed files, asked of the **rest of the tree**:
    `touched_since` diffs one governed file to attribute a change to a section, and this is
    the mirror question — what source moved while the backlog stood still.

    Names and not hunks, because the question is *did anything under this task change* and a
    line count would invite a threshold nobody could defend. Repo-relative and forward-slashed,
    which is the spelling a section's own prose uses and what `paths_in` resolves to.

    Empty where git cannot answer, which keeps the note silent: this reports a coincidence
    worth a sentence, and a repository with no history has no coincidence to report.
    """
    try:
        found = _run(config.root, "diff", "--name-only", rev)
    except HistoryUnavailable:
        return frozenset()
    return frozenset(one.strip().replace("\\", "/") for one in found.splitlines() if one.strip())


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
    return status(config).changed


def status(config: Config) -> Status:
    """The porcelain read once, split by which side of the index each path changed on (RK1197).

    One process for both answers rather than two for one each: the columns are in the same
    record git already sent, and asking twice would be this module doing what it tells its
    callers not to.
    """
    try:
        listed = _run(config.root, "status", "--porcelain", "-z")
    except HistoryUnavailable:
        return Status()
    return Status(*_read_status(listed))


@dataclass(frozen=True, slots=True)
class Status:
    """A working tree as `git status` describes it, both sides kept apart (RK1197)."""

    #: Every path the tree has changed, staged or not, untracked included — what a `git add -A`
    #: would put in the next commit, which is the list a scope is subtracted from.
    changed: frozenset[str] = frozenset()
    #: The subset whose **index** already differs from `HEAD`. The half that was thrown away:
    #: a `git commit` takes these whether or not the author reads a diff, and the diff they are
    #: reading is the other side. Measured twice in one session as a version literal another
    #: process staged and this one would have committed.
    staged: frozenset[str] = frozenset()


def carrying(config: Config, task_id: str, paths: Iterable[str]) -> tuple[str, ...]:
    """Which of these paths have this id **in their working-tree diff** (RK342).

    The fact `claim <id>` was missing. A claim's own transaction writes governed files — the
    marker moves in the roadmap, and every governed write carries the README refresh RK188
    added — and the read-back then listed both as `loose`, which reads as *a file somebody
    else touched*. So the author declares the governed paths by hand to silence it, and the
    scope comes to carry paths that were never the work: the analysis this command exists to
    make, made wrong, on the first call of every task.

    **Not every dirty governed file**, which is the repair that was available and wrong: a
    roadmap the tree holds may hold another session's `add`, and handing it to whoever asks
    would be the two sessions RK294 separates each getting the other's files with this tool's
    signature on it. The distinction the files themselves carry is the id — a line whose
    marker this transaction moved is a changed line naming it, and a projection refreshed
    from that line reproduces it.

    Read off `git diff HEAD`, both sides, so a **removed** line counts: a ship takes the line
    out, and a diff read for additions alone would answer "no" about the departure that is
    most of the work. Whole-word, because `RK34` must not answer for `RK342` — the same care
    :func:`cited_origin` takes with an anchor, and the same reason.

    Empty where git cannot answer, the rule every reader here keeps.
    """
    wanted = tuple(dict.fromkeys(paths))
    if not wanted or not task_id:
        return ()
    try:
        # `-U0`, so only the changed lines are read: a context line naming the id belongs to
        # a neighbour this transaction did not touch, and counting it would claim the file
        # for whichever task happens to sit next to the one that moved.
        listed = _run(config.root, "diff", "HEAD", "-U0", "--", *wanted)
    except HistoryUnavailable:
        return ()
    found: list[str] = []
    current = ""
    pattern = re.compile(rf"(?<![\w-]){re.escape(task_id)}(?![\w-])")
    for line in listed.splitlines():
        if line.startswith("+++ b/"):
            current = line[6:]
        elif line[:1] in "+-" and not line.startswith(("+++", "---")) and current:
            if pattern.search(line):
                found.append(current)
                current = ""  # one hit settles the file; the rest of its hunks are noise
    # Answered in the caller's order and not git's, so two runs of the same tree read alike.
    return tuple(one for one in wanted if one in set(found))


def _read_status(listed: str) -> tuple[frozenset[str], frozenset[str]]:
    """The paths out of `status --porcelain -z`, whose records are not one per NUL.

    A rename spends **two** NUL-separated fields — `R  <to>\\0<from>` — so a naive split reads
    the origin as a record and its first two characters as a status code. Both ends are
    kept, because both are paths the commit touches.

    Two sets since RK1197, from the same records: `XY` is one column per side, and the first
    is the index. `?` is not one of them — an untracked file is in neither the index nor
    `HEAD`, so it changes the commit and is not something the commit already carries.
    """
    changed: list[str] = []
    staged: list[str] = []
    fields = [field for field in listed.split(_NUL) if field]
    index = 0
    while index < len(fields):
        record = fields[index]
        index += 1
        code, _, name = record[:2], record[2:3], record[3:]
        if not name:
            continue
        changed.append(name)
        # The **origin** of a rename is staged too, and by the same record: git states one
        # code for the pair, so both ends take it.
        renamed = code[0] in "RC" and index < len(fields)
        origin = fields[index] if renamed else ""
        if renamed:
            changed.append(origin)
            index += 1
        if code[0] not in " ?":
            staged.append(name)
            if origin:
                staged.append(origin)
    return frozenset(changed), frozenset(staged)


@dataclass(frozen=True, slots=True)
class Cost:
    """What one commit changed: lines either side, and how many files (RK71).

    Both, because the two live corpora disagree about which one an author pays. Lines are
    what varies and files are what an agent holds in context, which is the comparison the
    "no size field" non-goal argues from — median to p90, 2.7× against 1.4×, a ratio
    holding where the ranges it was first stated as have not (RK367). A derivation that
    reported one would be picking the axis for the reader.
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
    # The qualifier a **partial** entry carries inside the bold span (RK121, RK1175): a search
    # for the bare id read `**RK1169 (the withheld reasons)**` as no id at all, so every partially
    # shipped entry was reported as one no commit accounts for — permanently, since the qualifier
    # stays until the completing ship. Optional here for the same reason the grammar has it.
    bold = re.compile(rf"\*\*({config.schema.id_fragment})(?: \([^)]+\))?\*\*")
    first: dict[str, str] = {}
    for head, rows in _records(output):
        added = "\n".join(
            row for row in rows if row.startswith("+") and not row.startswith("+++")
        )
        for task_id in bold.findall(added):
            first.setdefault(task_id, head.strip())
    return first


def ids_since(
    config: Config, rev: str, role: str, *, resolved: bool | None = None
) -> frozenset[str]:
    """Which ids this role's file **gained or lost a line for** since ``rev`` (RK1120).

    Two parses and never a diff heuristic, which is the whole of why this is decidable. RK1117
    subtracted whole *files* a departure could explain — the roadmap is always one, because
    the marker write that took the line is in the same diff — so another session's added line
    rode inside the staging the report printed. What tells them apart is not that a second id
    *appears* in the change: an annotation refresh (RK8) rewrites every dependent's deps field
    and names those ids in added lines, so a textual reading calls half the backlog somebody
    else's. What it is, is a line **arriving or leaving**, which only two parses can answer.

    The symmetric difference and not the additions, because both directions are a second
    session's work: a line added here is theirs, and a line removed is a ship of theirs that
    this commit would carry. The id being committed is the caller's to exclude — it is in this
    set on every ordinary departure, that being the line leaving.

    Empty where git cannot answer or the role is not declared, the rule every reader here
    keeps: a report is worth less than a session, and this feeds a report. :func:`resolves` is
    asked first and not left to the read below, because the two silences differ in the one way
    that matters here: :func:`content_at` answers `""` both for a file a revision did not carry
    and for a revision that does not exist, and comparing a *whole backlog* against nothing
    reports every id in it as newly arrived — which on a directory that is not a repository is
    every line the project has.

    ``resolved`` is that answer where the caller already has it (RK1124). Whether git knows a
    revision is a fact about the **repository**, and asking it per role made a caller looping
    over the carriers pay a `rev-parse` for something in hand: measured at 20.6ms each, 85.6ms
    for the pair this repository declares, against the 43ms floor RK176 set for a whole
    session-start read. A parameter and not a cache, the shape `plan(gauging=…)` already uses
    for the one expensive question a caller may decline — a cache keyed on a revision would be
    a second reader of git state with its own staleness, in a module that stores nothing.
    """
    if not config.has(role):
        return frozenset()
    if not (resolves(config, rev) if resolved is None else resolved):
        return frozenset()
    schema = config.schema_for(role)
    try:
        before = Document.parse(content_at(config, rev, role), schema=schema)
        now = config.document(role)
    except (HistoryUnavailable, OSError, ValueError):
        return frozenset()
    return frozenset(before.by_id()) ^ frozenset(now.by_id())


def designs_since(
    config: Config, rev: str, role: str, *, resolved: bool | None = None
) -> frozenset[str]:
    """Which designs this prose role's file **gained or lost a section for** since ``rev``.

    :func:`ids_since`'s unit one file over (RK1125). A rationale file holds no task lines, so
    that reading answers nothing about it — and the file a departure *wrote* is exactly where
    the silence hurt: one `section amend` earlier in the session puts this id in the diff, the
    file is then accounted for, and another session's new `### §RK-B` rides into the staging
    with nothing said. That is RK1117's defect and RK1120's fix, in the other unit.

    Labelled by the **id the heading names** where it names one, and by the anchor otherwise.
    Under the id scheme those are the same string; under an outline the anchor is `XVI.12` and
    the id lives in the title, so a label read off the anchor alone would report an address the
    reader then has to resolve. :meth:`~roadkeep.sections.Section.names` is that reading and it
    is the title's alone — a section quoting another id is discussing it, not being it.

    Two consequences worth stating, and both are the roadmap's reading in this unit. A section
    this project *moved* keeps its id, so it is not reported — the design did not arrive or
    leave, its address changed, which is what `section move` is for. And a **subsection added
    under a design that already existed** is that design changing rather than arriving, so it is
    not reported either: exactly as an amended task line is not an id arriving on the roadmap
    (RK1120), and for the same reason — this answers which work is in the file, not which
    paragraph somebody edited.
    """
    if role not in PROSE_ROLES or not config.has(role):
        return frozenset()
    if not (resolves(config, rev) if resolved is None else resolved):
        return frozenset()
    schema = config.schema_for(role)
    try:
        before = anchored(Document.parse(content_at(config, rev, role), schema=schema))
        now = anchored(config.document(role))
    except (HistoryUnavailable, OSError, ValueError):
        return frozenset()
    ids = config.schema.id_pattern()
    return _labels(before, ids) ^ _labels(now, ids)


def owned_edit(config: Config, rev: str, task_id: str, role: str) -> bool:
    """Whether this tree's changes to a prose file are inside a section this id owns (RK1126).

    The reading :func:`carrying` cannot make. It credits a path where an added or removed line
    **names the id**, which on a rationale file means a heading — so `section amend <id>
    --body` rewrites the paragraph under one, touches no line carrying the id, and the file the
    author just edited came back as `loose  (no claim names it)`. RK1117's sentence pointed at
    the author's own work, and RK342's defect from the other side: withholding a path is as
    wrong as handing it over, because the answer is then declared by hand and the scope carries
    what was never the work.

    Additions are read against the file **now** and removals against the file at ``rev``, which
    is RK36's split and the reason this is not one span lookup: a deleted paragraph's line
    numbers are the old file's, and judging them against the current parse attributes them to
    whichever section now sits over the hole. :func:`~roadkeep.sections.owners` decides
    ownership so the outline case answers too — there the id is in the heading's title and a
    sub-anchor belongs to the id its first segment spells.

    A blank line belongs to no section's prose, exactly as the gate reads it: counting one
    would credit a file for the trailing newline of somebody else's paragraph.
    """
    if role not in PROSE_ROLES or not config.has(role):
        return False
    ids = config.schema.id_pattern()
    try:
        edited = touched_since(config, rev, role)
        now = anchored(config.document(role))
        before = anchored(
            Document.parse(content_at(config, rev, role), schema=config.schema_for(role))
        )
    except (HistoryUnavailable, OSError, ValueError):
        return False
    for change in edited.changes:
        if not change.text.strip():
            continue
        for section in now if change.added else before:
            if section.first <= change.lineno <= section.last and task_id in owners(
                section, ids
            ):
                return True
    return False


def _labels(sections: Sequence[Section], ids: re.Pattern[str]) -> frozenset[str]:
    """Each section as **the task it belongs to**, or as its anchor where it belongs to none.

    :func:`~roadkeep.sections.owners` and not a second reading of a heading (RK1127). Labelling
    by the ids a *title* names left a sub-anchor labelled by its own address: `§RK2.1` is `RK2`'s
    subsection and the anchor says so segment by segment, so the exclusion `- {task_id}` did not
    remove it and a departure reported the design being shipped as somebody else's. `owners`
    already answers this for the gate and for the drop — under the id scheme the anchor is the
    id and a sub-anchor is its root's, and under an outline the id is in the title — so the one
    thing left here is the fallback: a section belonging to no task is labelled by the anchor,
    which is the only handle a reader has on prose that is nobody's.
    """
    out: set[str] = set()
    for section in sections:
        out.update(owners(section, ids) or (section.anchor,))
    return frozenset(out)


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
class Pending:
    """One open line, and the commits whose message already names it (RK1201).

    Not "the work is done" — which of a task's commits completed it is a judgement, and this
    tool has no model of one (L4). What this holds is the two facts a reader needs to decide:
    the line is open, and something in the history says otherwise.
    """

    id: str
    marker: str
    block: str
    #: The commits naming this id, newest first. Read from the **message** and not from a
    #: file's history: `origin` asks which commit touched the roadmap at this id, which is
    #: about the *line*, and the question here is about the work.
    commits: tuple[Commit, ...] = ()
    #: Whether the ledger already holds an entry for it — true on a partial (RK121), which is
    #: the state this deliberately does not report: a half recorded and a line still open is
    #: exactly what a partial is, and reporting it would be reporting the feature.
    recorded: bool = False

    @property
    def stale(self) -> bool:
        return bool(self.commits) and not self.recorded


def pending(config: Config) -> tuple[Pending, ...]:
    """Every open line with commits naming it and no ledger entry (RK1201).

    One `git log` for the whole backlog rather than one per id: the ids are matched against the
    subjects that come back, so a backlog of forty costs the same read as a backlog of one.

    Empty where git cannot answer, the rule every reader here keeps — a checkout with no git is
    one this reports nothing about, never one it refuses.
    """
    from roadkeep.backlog import Backlog  # noqa: PLC0415 - RK260

    backlog = Backlog.load(config)
    open_lines = list(backlog.roadmap.entries)
    if not open_lines:
        return ()
    recorded = (
        {entry.task.id for entry in backlog.ledger.entries}
        if backlog.ledger is not None
        else set()
    )
    try:
        # The module's own format and its own parser (RK1201): a second spelling of a commit
        # here would be a second thing to keep true, and the one already there carries every
        # field this needs.
        listed = _parse(_run(config.root, "log", "--no-merges", f"--format={_FORMAT}"))
    except HistoryUnavailable:
        return ()
    from roadkeep.ids import id_scanner  # noqa: PLC0415 - RK260

    naming: dict[str, list[Commit]] = {}
    # The **scanner** and not `id_pattern` (RK106): one matches an id as a whole string and the
    # other finds one inside running text, which is what a commit subject is.
    pattern = id_scanner(config.schema)
    for commit in listed:
        for token in {found.group(0) for found in pattern.finditer(commit.subject)}:
            naming.setdefault(token, []).append(commit)

    # **The oldest commit naming an id is the one that filed it**, and it is dropped: `add` is
    # what mints an id, so nothing could name one before the line existed. Measured before this
    # was written — without it the sweep reported seven lines and every one was its own filing,
    # where `docs: file RK1196` names the id and means the opposite of what the report said.
    #
    # Read off the log already in hand rather than by asking `origin` per id, which is the same
    # answer at one git call per open line. A **promise** (RK431) is the one shape this reads as
    # work: an id a sentence named before the line existed leaves the filing as the newest of
    # two, which errs toward reporting — the safe direction for a report.
    for named in naming.values():
        named.pop()

    return tuple(
        Pending(
            id=entry.task.id,
            marker=entry.task.status,
            block=entry.task.block,
            commits=tuple(naming.get(entry.task.id, ())),
            recorded=entry.task.id in recorded,
        )
        for entry in open_lines
    )


#: What one `git log` line carries, separated by a NUL. A NUL cannot appear in a subject,
#: which is what makes splitting safe where a subject may hold anything else — and it is
#: spelled `%x00` because an argv may not carry one: Windows refuses the process outright.


@dataclass(frozen=True, slots=True)
class Unclosed:
    """The sweep as one answer: which open lines the history already speaks for (RK1201).

    **A report and never a refusal.** The honest reading of a line with commits is sometimes
    "the work is under way and these are partial", which is what a partial entry is for — so
    this states the fact and leaves the verdict where it belongs.
    """

    rows: tuple[Pending, ...] = ()
    #: True where git answered at all. `()` means two different things otherwise, and a
    #: checkout with no history reading as a clean backlog is the silence RK10 is about.
    searched: bool = True

    @property
    def stale(self) -> tuple[Pending, ...]:
        return tuple(one for one in self.rows if one.stale)

    def stated(self) -> str:
        if not self.searched:
            return "no history to read, so nothing here says whether a line was left open"
        found = self.stale
        rows = [
            f"{len(found)} of {len(self.rows)} open line(s) already have commits naming them"
        ]
        for one in found:
            named = ", ".join(commit.short for commit in one.commits[:3])
            more = f" and {len(one.commits) - 3} more" if len(one.commits) > 3 else ""
            rows.append(
                f"  {one.marker} {one.id:<8} Block {one.block:<3} {named}{more}"
            )
        if found:
            # The door, as every finding this tool prints carries one (RK420): what closes a
            # line is `ship`, and what closes it *honestly* where only half landed is `--part`.
            rows.append(
                "  close    `ship <id> --why …` records the outcome, or `--part` where only "
                "half of it landed"
            )
        return chr(10).join(rows)

    def payload(self) -> dict[str, object]:
        return {
            "searched": self.searched,
            "open": len(self.rows),
            "unclosed": [
                {
                    "id": one.id,
                    "marker": one.marker,
                    "block": one.block,
                    "recorded": one.recorded,
                    "commits": [
                        {"sha": commit.sha, "short": commit.short, "subject": commit.subject}
                        for commit in one.commits
                    ],
                }
                for one in self.stale
            ],
        }


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

    def stated(self, where: str, *, why: bool = False) -> str:
        """Where the design behind this citation went, as the reader is told it (RK212).

        Beside :meth:`payload` since RK1170: these two were a printer inside the handler and a
        builder in the same function, so one answer had two spellings and the file that holds the
        fact held neither. `where` is passed rather than stored — the role is the fact and how a
        project spells that file is the caller's (RK75).

        The absences are three different answers and never one (RK95): a history nobody could
        search, a history searched to the root that never saw the address — which is what a typo
        looks like — and an address still in the file, where the citation simply resolves.
        """
        if not self.searched:
            return f"§{self.anchor}: no history to resolve against"
        if self.written_in is None:
            return f"§{self.anchor}: searched {where} to the root and nothing ever wrote it"
        rows = [
            f"§{self.anchor}  in {where}",
            f"  written  {self.written_in.short}  {self.written_in.date[:10]}  "
            f"{self.written_in.subject}",
        ]
        if self.removed_in is None:
            rows.append("  removed  — the section is still there, so the citation resolves")
        else:
            rows.append(
                f"  removed  {self.removed_in.short}  {self.removed_in.date[:10]}  "
                f"{self.removed_in.subject}"
            )
            if why:
                # The commit's own reasoning, only where it was asked for: it is the one field
                # here that is a paragraph, and a read that always printed it would be a read
                # nobody puts in a loop.
                rows += ["", self.removed_in.reasoning]
        return "\n".join(rows)

    def payload(self, *, whole: bool = True) -> dict[str, object]:
        """The same answer as data, with each end null where history answered nothing.

        `whole` keeps the commit's message: a caller asking about an address is asking about
        those two commits, so the body is the answer here rather than a paragraph riding along.
        """

        def commit(one: Commit | None) -> dict[str, str] | None:
            if one is None:
                return None
            said = {
                "sha": one.sha,
                "short": one.short,
                "date": one.date,
                "subject": one.subject,
            }
            return {**said, "body": one.body} if whole else said

        return {
            "anchor": self.anchor,
            "role": self.role,
            "searched": self.searched,
            "written": commit(self.written_in),
            "removed": commit(self.removed_in),
        }


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
    #: The task the **heading** names, or `""` where it names none (RK453). Under an outline
    #: that id is the ownership (RK262), and until this read it was visible only as `ship`'s
    #: `kept` field scrolling past. Empty on a retired anchor, which has no heading left.
    binds: str = ""
    #: Every **live line** pointing at this address, roadmap and deferred store, in the order
    #: those files hold them. Two facts and not one, because they come apart in both
    #: directions and each way is a different thing to do: a heading binding nobody that a
    #: line claims is RK452's write left undone on a corpus that predates it, and one binding
    #: a task no live line claims is prose whose task has shipped — what `ship` reports once
    #: and no reader has held since.
    claimed: tuple[str, ...] = ()

    @property
    def memo(self) -> bool:
        """A live heading that names no task and that no open line claims (RK461).

        The third state, and the one that is never a thing to do. RK236 settled that a
        heading naming no task is prose belonging to none, which a standing memo genuinely
        is — Turing's GEO memo is the case it was decided for, and this repository's own `§0`
        to `§0.4` are five more. Nothing closes it, because nothing is open.

        Named so the two states that *are* actionable can be told from it: reported beside
        them, it was five of the five rows this project's audit printed, and a list whose
        majority is noise is what teaches somebody to stop reading a report.
        """
        return self.live and not self.binds and not self.claimed

    @property
    def orphaned(self) -> bool:
        """A live heading bound to a task no open line claims — prose whose task has left.

        `binds` and not only the absence of a claimant (RK461): without it this was true of a
        memo too, which was never anybody's and so cannot have been left. Still not a
        violation, for RK236's reason; it is a fact this read states and the gate stays out of.
        """
        return self.live and bool(self.binds) and not self.claimed


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
    found += _spent_by_departure(config, roles, found)
    # Whether this file numbers in Roman is a fact about the whole set (RK293), so it is
    # settled once here and handed to the key — a per-segment decision would read `C` as 100
    # in a file whose families are letters, and sort a listing by an arithmetic nobody meant.
    # The namespace is not part of the numbering (RK340): `S:IX` spells nine in Roman, and a
    # set read with the prefix on it would answer "no numerals here" and sort as text.
    numbered = bool(found) and all(numeral(_family_of(one.anchor)) for one in found)
    wanted = [_claimed(config, one) for one in found if _within(one.anchor, family)]
    # The role breaks the tie, so an address two files declare comes out as two adjacent
    # rows in `[files]` order — which is the doubling, reported rather than collapsed.
    return tuple(sorted(wanted, key=lambda one: (_ordinal(one, numbered), one.role)))


def _claimed(config: Config, anchor: Anchor) -> Anchor:
    """Fill in who binds this address and who points at it (RK453).

    RK452 stops the unbound heading being created and does not reach the corpora already
    holding one — and no command listed them, so the fixture's §I.1 was found by reading
    `ship`'s `kept` field as it scrolled past, and Shio's the same way. `anchors` was the
    only verb that lists sections and its `live` answers a different question: RK247 built it
    about address *reuse*, so `live` means a heading declares the address now, and one
    written for a task that has since shipped is counted among the working ones.

    Both files a line can be open in, for :func:`families_of_block`'s reason: a design whose
    task is paused is claimed, and answering "nobody" about it would name prose to delete.

    Retired anchors are left alone. There is no heading to read an id off, and a claimant
    would be a live line pointing at an address nothing declares, which `lint` already
    refuses as `ref.unresolved` — a second reading of it here would be a second gate.
    """
    if not anchor.live:
        return anchor
    section = None
    if config.has(anchor.role):
        section = find(config.document(anchor.role), anchor.anchor)
    binds = ""
    if section is not None:
        named = owners(section, config.schema.id_pattern())
        binds = named[0] if named else ""
    claimed = tuple(
        entry.task.id
        for role in ("roadmap", "deferred")
        if config.has(role)
        for entry in config.document(role).entries
        if entry.task.ref == anchor.anchor
    )
    return replace(anchor, binds=binds, claimed=claimed)


def families_of_block(config: Config, block: str) -> tuple[str, ...]:
    """Which outline families a block's prose already lives under (RK312).

    The read that was derivable from no command at all. Under an outline a prose file
    declares no block headings — the address *is* the placement — so which numeral a block's
    designs sit in is written down nowhere, and the way to it was globbing pointers per block
    by hand: `list --block Q | grep -oE "§[IVXL]+"`, repeated once per block. It is a
    question, so it is a command (L5).

    Read off the **pointers** and never off the prose file, for the reason
    :func:`~roadkeep.sections.pointers` gives: a heading nested under another is that other's
    prose until a line names it, and a task line is the only place that says which block an
    address belongs to. Both files a line can be open in, because a block whose every live
    line is paused still has a family and answering "none" would send the caller to open a
    second one.

    More than one is a real answer and not a failure. A block that reopened under a fresh
    top-level has two, and returning both is what lets the caller see that before choosing —
    a single answer would pick one, which is the guess this exists to stop making.

    Spelled **with the namespace** where `[refs]` declares one (RK340), because that is how
    :func:`_within` and :func:`next_child` read a family: `S:IX` and `IX` are two subtrees on
    a project whose two files each number their own outline, and a family stripped of the
    prefix here would be handed back an address the sibling file already spent.
    """
    found: list[str] = []
    for role in ("roadmap", "deferred"):
        if not config.has(role) or not config.path(role).is_file():
            continue
        for entry in config.document(role).entries:
            if entry.task.block == block and entry.task.ref:
                family = entry.task.ref.split(".")[0]
                if family and family not in found:
                    found.append(family)
    return tuple(found)


def _spent_by_departure(
    config: Config, roles: Sequence[str], known: Sequence[Anchor]
) -> list[Anchor]:
    """Addresses no prose diff witnesses, read off the pointers that left with them (RK1178).

    The blind spot :func:`_pointed_at` covers, joined here so one listing answers for both kinds
    of evidence: a heading any committed tree held, and an address whose heading no tree ever did
    because the `section add` that wrote it and the `ship` that dropped it were one commit.

    **Outline only**, the rule :func:`~roadkeep.sections._refuse_reuse` keeps for the same reason:
    under `ref_scheme = "id"` the pointer *is* the id, retired-never-reused is the roadmap's own
    property (RK4), and every shipped task would arrive here as an address to refuse.

    Attributed to the file the address belongs to, which its namespace answers where `[refs]`
    declares one (RK340). Where none does, both files number into one space and the row goes to
    the first declared role: the address is spent either way — that is the fact this reports — and
    which file would have held the heading is a question no history can settle.
    """
    declared = [name for name in roles if config.has(name)]
    if not declared or config.schema_for(declared[0]).ref_scheme == "id":
        return []
    seen = {one.anchor for one in known}
    out: list[Anchor] = []
    for anchor, sha in _pointed_at(config).items():
        if anchor in seen:
            continue
        namespace, _ = split_ref(anchor)
        role = next(
            (name for name in declared if config.schema_for(name).ref_prefix == namespace),
            declared[0],
        )
        out.append(Anchor(anchor=anchor, role=role, live=False, written_in=sha))
        seen.add(anchor)
    return out


def _pointed_at(config: Config) -> dict[str, str]:
    """Every address a task line pointed at and **took with it**, by the commit that removed it.

    The witness for an address declared and dropped inside one commit (RK1178). `_anchors_written`
    reads the prose file's own diffs, which is the whole history of an address in every case but
    one: a task whose `section add` and whose `ship` land in the same commit leaves a net-zero
    diff there — the heading was never in any committed tree, so no diff of that file mentions it.
    Nothing in the ledger does either, `as_ledger` keeping no pointer.

    What does survive is the **roadmap**: that task's line was filed in an earlier commit carrying
    `→ §XIV.30`, and the ship removed the line. So the address is read off the pointer that left,
    which is a fact in the same history and about the same address.

    Worth fixing rather than tolerating because of which workflow produces it: a task that files
    its own rationale and ships in one commit is what a one-task-one-commit rule *requires*, so
    this is the normal path and not unusual sequencing.

    **Removed pointers only.** A pointer on a line still in the file is an address the two-command
    flow is halfway through spending — `add --ref I.3` then `section add I.3` — and counting it
    would make the second command refuse the address the first was told to take. A rewritten
    pointer (`amend --ref`) does register the one it abandoned: an address nothing wrote is still
    an address a reader saw cited, and they cost nothing.
    """
    out: dict[str, str] = {}
    for role in ("roadmap", "deferred"):
        if not config.has(role):
            continue
        try:
            output = _run(
                config.root,
                "log",
                "--reverse",
                f"--format={_RECORD}%H",
                "--no-color",
                "-U0",
                "--",
                str(config.relative(config.path(role))),
            )
        except HistoryUnavailable:
            continue
        # Read as `anchor_of` reads a heading's: whatever follows the sigil up to the space
        # that ends the pointer, which is the last thing a rendered line carries. The address is
        # then validated by the same reader the prose file's own scan uses, so a bullet that
        # merely contains an arrow contributes nothing.
        pointer = re.compile(rf"{ARROW} §(\S+)\s*$")
        for head, rows in _records(output):
            for row in rows:
                if not row.startswith("-") or row.startswith("---"):
                    continue
                found = pointer.search(row)
                if found:
                    out.setdefault(found[1], head.strip())
    return out


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


def namespaces(taken: Sequence[Anchor]) -> tuple[str, ...]:
    """Every namespace these addresses live in, `""` for the unprefixed one (RK340).

    Sorted with the unprefixed first, because it is the one a project has before it declares
    any and the one every listing had until this existed.
    """
    return tuple(sorted({split_ref(one.anchor)[0] for one in taken}))


def next_family(taken: Sequence[Anchor], namespace: str = "") -> str | None:
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

    **Per namespace** (RK340), which is what a namespace is for: `[refs]` makes two files two
    outlines, each numbering itself from `I`, so a maximum taken across both would answer
    with the taller file's number for the shorter one — and reading the mixed set as one
    sequence answers None, which is the useful answer withheld from exactly the projects
    that declared their way out of the collision. The default is the unprefixed namespace,
    which is every project that declares no `[refs]` at all.

    **One numbering means one system, and until RK1210 it meant one that reads as a number.**
    The guard below caught a segment that is no numeral at all and let `1` beside `I` through
    — they read as 1 and 1, so the key ties, and `max` returns whichever the iteration reached
    first. That order is a **set** comprehension's over strings, which is per-process hash
    randomisation: eight runs over one revision of one file answered `II`, `2`, `2`, `2`, `II`,
    `2`, `2`, `2`. The system the address is spelled in was the tie-break, so the address was
    too — and `ref.missing` carries it as `offered`, the string a retry substitutes, so a
    refusal and its own retry could name two different addresses. In one tree they did:
    `anchors` printed `next §2` where the refusal said `§II is its free top-level`.

    The fix is this function's own rule applied and never a tie-break invented — sorting the
    set would make the answer stable and still make it a coin the file did not toss. Two
    systems is two numberings, so it is None, exactly as `A`, `B`, `C` is; every caller
    already has an answer for None, `_where_a_top_level_is` naming `anchors` in place of an
    address for the undecidables it already knew about.
    """
    own = [one for one in taken if split_ref(one.anchor)[0] == namespace]
    read = {top: numeral(top) for top in {_family_of(one.anchor) for one in own}}
    if not read or any(value is None for value in read.values()):
        return None
    counted = [value for value in read.values() if value]
    if len({system for system, _ in counted}) > 1:
        # Roman in one family and decimal in another. Not a sequence to continue, and the one
        # shape where continuing it silently picked which of two conventions the project has.
        return None
    system, highest = max(counted, key=lambda one: one[1])
    top = spell(highest + 1, system)
    return f"{namespace}{REF_SEPARATOR}{top}" if namespace else top


def left_the_repository(root: Path, token: str) -> bool:
    """Whether this repository once held ``token`` and no longer does, as committed (RK1217).

    The tree a shipped entry's paths are about is **not this afternoon's**. Turing's `T759`
    names `frontend/apps/site/scripts/emit-model-catalog.mjs`, a script that existed when the
    work shipped and was later extracted into its own repository with the model catalog it
    built. The entry is accurate, the file is gone, and the gate reported it every run and
    would have kept reporting it.

    `Tree.anywhere` already forgives a path that moved **within** the repository, so what was
    left was the one that left it entirely — a correct statement about the past, read as drift.
    And the door made it worse than noise: the remedy rewrites the entry's sentence, which on
    that entry is about 1,500 characters of as-built record. The offered fix for a stale path
    was deleting the thing that made the entry worth keeping, so nobody took it and the finding
    sat forgiven by a baseline for ever.

    **Two questions, and the first one is what keeps this narrow.** *Is it in `HEAD`* — because
    a file somebody deleted in their working tree and has not committed is still the
    repository's, and forgiving that would stop the gate reporting a deletion at exactly the
    moment it is worth reporting. Only then *did any commit ever hold it*, over all refs, which
    is the reading that answers `T759`.

    Not `--follow`, which needs a single surviving path and answers about a rename chain rather
    than about existence.

    **What this deliberately stops catching** is a rename the ledger did not follow, which was
    the one true finding this check produced on a live corpus: the old path was held once, so
    it is now forgiven. RK1217 takes that trade knowingly — the alternative is a correct
    statement about the past reported for ever, with a door whose only effect is to delete the
    as-built record that made the entry worth keeping. What is left is the reading the rule was
    always for: **a path this repository never had.**

    Cheap because it is asked **last** (see :func:`~roadkeep.linting._paths`): the working tree
    answers first, so a healthy repository asks this nothing at all and a corpus with stale
    entries pays at most two calls per token that already failed every other reading.

    False where git cannot be reached, which keeps the finding: this is a *forgiveness*, and an
    unavailable history is not evidence that a path was ever there.
    """
    try:
        if _run(root, "ls-tree", "HEAD", "--", token).strip():
            return False
        found = _run(root, "log", "--all", "--max-count=1", "--format=%H", "--", token)
    except HistoryUnavailable:
        return False
    return bool(found.strip())


def _declared(config: Config, role: str) -> tuple[str, ...]:
    from roadkeep.sections import anchored  # noqa: PLC0415 - RK260

    return tuple(section.anchor for section in anchored(config.document(role)))


def _anchors_written(config: Config, role: str, schema: Schema) -> dict[str, str]:
    """Anchor → the first sha whose diff on this file carries its heading, oldest first."""
    from roadkeep.sections import anchor_of, qualified  # noqa: PLC0415 - RK260

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
                # The project's address and not the heading's (RK340) — the same
                # qualification `anchored` makes of a live one, so the two halves of this
                # listing are addresses of one kind and a retired `S:I` is not a second `I`.
                first.setdefault(qualified(schema, anchor), head.strip())
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
        # The first segment carries the namespace where a project declares one (RK340), and
        # it is read off for the same reason `numbered` is: the number is what orders a
        # listing, and a prefix in front of it is the file's name and not part of the number.
        for part in _unprefixed(anchor.anchor).split(".")
    )


def _family_of(anchor: str) -> str:
    """The top-level segment, with any namespace taken off — `S:IX.2` → `IX` (RK340)."""
    return _unprefixed(anchor).split(".")[0]


def _unprefixed(anchor: str) -> str:
    """The address without the namespace `[refs]` put in front of it (RK340)."""
    return split_ref(anchor)[1]


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



def _ownership(one: Anchor) -> str:
    """Who binds this address and who points at it, where either is worth saying (RK453).

    Silent on the ordinary row — a heading bound to the one line that claims it is the state
    every write produces, and repeating it on every address would bury the two that are not.
    What it names is exactly the two ways they come apart, and each is a different act: an
    unbound heading a line claims is `section amend --title` away from bound, and a bound
    heading nothing claims is prose whose task has left, which is the reader's to keep or
    delete.

    Three silences and not one (RK461). A retired address has no heading to have an opinion
    about; the bound-and-claimed row is what every write produces; and a **memo** — naming no
    task and claimed by none — is the state RK236 protects and nothing ever closes. Reported
    beside the two that are actionable, that third one was five of the five rows this
    project's audit printed, and a list whose majority is noise is what teaches somebody to
    stop reading a report.
    """
    if not one.live or one.memo:
        return ""
    if one.binds and one.claimed == (one.binds,):
        return ""
    if not one.binds:
        return f"  binds nobody, claimed by {', '.join(one.claimed)}"
    if not one.claimed:
        return f"  binds {one.binds}, which no open line claims"
    return f"  binds {one.binds}, claimed by {', '.join(one.claimed)}"


def opens(family: str) -> str:
    """The sentence a free top-level owes, and the command that makes it a section (RK1140)."""
    from roadkeep.provenance import invocation  # noqa: PLC0415 - RK260

    return (
        f"§{family} is free and not yet a section, so `{invocation()} add --ref {family}.1` "
        f"refuses until one exists — `{invocation()} section add {family} --title \"…\"` "
        f"opens it"
    )


@dataclass(frozen=True, slots=True)
class Addresses:
    """Live and retired addresses across a project's prose, as one answer (RK247, RK297).

    The result this read had none of (RK1170). The door narrowed the listing, derived the free
    address from a *wider* set than the one it listed, split the outline out of the ids, and
    then composed four readings from those four values — two payloads and two reports, each
    subtracting the same things again.

    **The narrowing and the derivation are not the same set, and that is the whole of RK297.**
    `--role` narrows :attr:`found`; the free address is computed from :attr:`whole`, because
    where no `[refs]` declares a namespace both files number into one and a `next` taken from
    a single file is the answer this read exists to stop somebody acting on.
    """

    #: The role a caller narrowed to, or `""` for every declared prose file.
    role: str
    #: The roles actually read, which is what a listing names its files from.
    read: tuple[str, ...]
    #: The family a caller narrowed to, or `""`. Under `--block` it is resolved from the
    #: pointers rather than given (RK312).
    family: str
    #: The block asked about, and every family its open lines point into. Both, because one of
    #: them narrowed the listing and two did not, and a caller cannot tell those apart.
    block: str = ""
    spans: tuple[str, ...] = ()
    found: tuple[Anchor, ...] = ()
    #: The same read over the project, whatever the listing was narrowed to.
    whole: tuple[Anchor, ...] = ()
    #: :attr:`found` and :attr:`whole` with the task ids taken out. An address that is an id is
    #: a question already answered — `add` refuses to reuse one (RK4) and every shipped task
    #: leaves its section retired, so on this project they are 287 of 307 rows and none of them
    #: is a choice anybody makes.
    outline: tuple[Anchor, ...] = ()
    spread: tuple[Anchor, ...] = ()

    @classmethod
    def of(
        cls,
        config: Config,
        role: str,
        family: str,
        read: Sequence[str],
        block: str = "",
        spans: Sequence[str] = (),
    ) -> Addresses:
        found = anchors(config, role, family)
        whole = found if not role else anchors(config, "", family)
        ids = config.schema_for(role or read[0]).id_pattern()
        outside = lambda rows: tuple(  # noqa: E731 - one predicate, read twice
            one for one in rows if not ids.match(one.anchor.split(".")[0])
        )
        return cls(
            role=role,
            read=tuple(read),
            family=family,
            block=block,
            spans=tuple(spans),
            found=tuple(found),
            whole=tuple(whole),
            outline=outside(found),
            spread=outside(whole),
        )

    @property
    def retired(self) -> tuple[Anchor, ...]:
        return tuple(one for one in self.found if not one.live)

    @property
    def spent(self) -> int:
        """How many of the listed addresses are task ids rather than outline numerals."""
        return len(self.found) - len(self.outline)

    def files(self, config: Config) -> str:
        return ", ".join(config.relative(config.path(one)) for one in self.read)

    def families(self) -> list[dict[str, object]]:
        """One row per top-level address, in numeral order (RK293), with the files it spans.

        The counts are the project's and so is `next` (RK297): a family declared in two prose
        files is one family, and a per-file count would be the number this read exists to stop
        somebody taking. `files` is what a row says once it spans two — named rather than
        summed away, because which file spent an address is what a reader checks it against.
        """
        out: dict[str, dict[str, object]] = {}
        for one in self.outline:
            top = one.anchor.split(".")[0]
            row = out.setdefault(top, {"family": top, "live": 0, "retired": 0, "files": []})
            key = "live" if one.live else "retired"
            row[key] = int(row[key]) + 1
            if one.role not in row["files"]:  # type: ignore[operator]
                row["files"].append(one.role)  # type: ignore[attr-defined]
        for top, row in out.items():
            row["next"] = next_child(self.outline, top)
        return list(out.values())

    def doubled_rows(self) -> list[str]:
        """The addresses two prose files both declare, named here and not only at the gate.

        `lint` reports them as `ref.ambiguous`, and by then both headings exist and four verbs
        refuse to resolve between them (RK297). This is the read an author makes *before*
        choosing, so it is where the state is cheapest to hear about.
        """
        return [
            f"  doubled  §{anchor} is declared by {' and '.join(roles)}"
            for anchor, roles in doubled(self.whole)
        ]

    def room_left(self, config: Config) -> str:
        """What the parent of an offered child address has left, where it has too little.

        An address `add` will refuse is an address this listing should not hand over silently
        (RK1024). Measured: `anchors --block AJ` offered `§L.1`, `§L` was 299 words of its own
        300, and every child of it — the empty one included — was over before a word was
        composed. Said and never refused, because `anchors` is a read (L5): the caller may be
        about to shorten the parent, which is a plan no count can see.
        """
        from roadkeep.kernel.schema import body_aim  # noqa: PLC0415 - RK260
        from roadkeep.sections import binding  # noqa: PLC0415 - RK260

        for role in self.read:
            answer = binding(config, role, self.family)
            if answer is None:
                continue
            taken, limit = answer
            if taken >= body_aim(limit):
                return (
                    f", but §{self.family} already spends {taken} of its {limit} words, "
                    f"so a child of it is charged over the limit before it is written"
                )
        return ""

    # -- the free address alone (RK410) ------------------------------------

    def freely(self) -> tuple[list[str], list[str]]:
        """The next address and nothing else, as `(stdout, stderr)`.

        `anchors` answers two questions at once: which addresses a family has spent, asked
        once before reopening a shipped subtree, and which one nothing ever used, asked by
        every `add --ref`. Under a 27-anchor family the second answer was the 28th row — and
        on a tool result the rows are what gets truncated first, which made the one line that
        mattered the one most likely to be cut.

        Two streams, for `next-id`'s reason: stdout is the address, because this is captured
        in a shell. **No note where a family was named** and the difference is the whole of
        RK1140: a free *child* is placeable the moment it is answered, the family's heading
        already existing. It is the top-level below that is an address and not yet a section.
        """
        if self.family:
            return [f"§{next_child(self.whole, self.family)}"], []
        out: list[str] = []
        notes: list[str] = []
        for space in namespaces(self.spread):
            fresh = next_family(self.spread, space)
            named = f"  {space}" if space else ""
            # The same refusal the wide read gives, in one line: a namespace whose top-levels
            # are not one numbering derives nothing, and a blank row would read as an address.
            out.append(
                f"§{fresh}{named}" if fresh else f"—{named}  not one numbering, so none derives"
            )
            if fresh:
                notes.append(f"roadkeep: {opens(fresh)}")
        return out, notes

    def free_payload(self) -> dict[str, object]:
        """The narrow read in the narrow shape (RK410).

        `family` and `namespace` are kept because the answer is meaningless without saying
        which numbering it continues — everything else in the wide payload is the listing this
        flag exists to leave out.
        """
        return {
            "family": self.family or None,
            "next": next_child(self.whole, self.family) if self.family else None,
            "next_families": []
            if self.family
            else [
                {
                    "namespace": space or None,
                    "next": next_family(self.spread, space),
                    # The same sentence the reader gets, as the command it names (RK1140): a
                    # client composing `add --ref <next>.1` walks into the refusal a person
                    # now reads about, and two answers to one question is what a payload
                    # beside a report must not be.
                    "opens": None
                    if not (fresh := next_family(self.spread, space))
                    else f"section add {fresh} --title …",
                }
                for space in namespaces(self.spread)
            ],
        }

    # -- the wide read -----------------------------------------------------

    def stated(self, config: Config, claims: bool) -> str:
        from roadkeep.provenance import invocation  # noqa: PLC0415 - RK260

        where = self.files(config)
        if claims:
            # Its own header and not a second one under the totals (RK459): this listing is
            # the exceptions, so the number a reader wants first is how many there are.
            rows = [one for one in self.found if _ownership(one)]
            # The memos are counted and not listed (RK461): "five of them and none needing
            # anything" is a different answer from silence, and it is the answer an adopting
            # corpus most often has.
            memos = sum(1 for one in self.found if one.memo)
            counted = f", {memos} standing memo(s)" if memos else ""
            said = [
                f"{len(rows)} of {len(self.found)} address(es) say something about "
                f"ownership{counted}  ({where})"
            ]
            said += [
                f"  {one.anchor}"
                + (f"  in {one.role}" if len(self.read) > 1 else "")
                + _ownership(one)
                for one in rows
            ]
            return chr(10).join(said + self.doubled_rows())

        said = [f"{len(self.found)} anchor(s), {len(self.retired)} retired  ({where})"]
        if self.block:
            # Said whichever way it went (RK312): one family is the narrowing the rest of this
            # output is already about, and two is the answer itself — the caller picks, because
            # which subtree a new line belongs under is a judgement no file holds.
            named = ", ".join(f"§{one}" for one in self.spans)
            # The whole command and not the flag alone (RK1022): a caller arrives here from an
            # `add` refusal that named `--ref`, so a bare `--family` reads as a second flag of
            # the verb they were writing.
            picked = (
                ""
                if len(self.spans) == 1
                else f" — pick one, e.g. `{invocation()} anchors --family {self.spans[0]}`"
            )
            said.append(f"  block    Block {self.block}'s prose is under {named}{picked}")
        if self.family:
            for one in self.found:
                written = f"  written in {one.written_in[:7]}" if one.written_in else ""
                # The file, wherever the project has more than one: two rows spelling the same
                # address are the doubling, and unlabelled they read as one row printed twice.
                named = f"  in {one.role}" if len(self.read) > 1 else ""
                said.append(
                    f"  {'live' if one.live else 'retired':<8} {one.anchor}{named}"
                    f"{written}{_ownership(one)}"
                )
            said.append(
                f"  next     §{next_child(self.whole, self.family)} — nothing ever used it"
                f"{self.room_left(config)}"
            )
            return chr(10).join(said + self.doubled_rows())

        # Beside the totals and above the rows, because it is the question a reused block asks
        # first and the listing cannot be read for it (RK293): the rows are per family, and the
        # last one is only the maximum once they are ordered by the number a numeral spells.
        for space in namespaces(self.spread) if self.spread else ():
            # One line per namespace (RK340). Where a project declares no `[refs]` this is the
            # one line it always printed; where it does, the two files each continue their own
            # numbering, and a single answer would give one file the other's next address.
            fresh = next_family(self.spread, space)
            named = f" in {space}" if space else ""
            said.append(
                f"  next     §{fresh} — no family{named} ever used it"
                if fresh
                else f"  next     — these families{named} are not one numbering, so none derives"
            )
        for family in self.families():
            # The files only where there is more than one to name (RK297): on the single-file
            # project that is every project until it declares a second, it would be noise.
            across = family["files"]
            spans = f"  ({', '.join(across)})" if len(across) > 1 else ""  # type: ignore[arg-type]
            said.append(
                f"  {family['family']:<8} {family['live']} live, {family['retired']} retired"
                f"  next §{family['next']}{spans}"
            )
        if self.spent:
            said.append(
                f"  {self.spent} address(es) are task ids, which `add` already refuses to reuse"
            )
        said += self.doubled_rows()
        if self.outline:
            # Named because the listing above is per family and the addresses are what the
            # caller came for: one flag away, and never printed by the hundred unasked.
            said.append(
                f"  `{invocation()} anchors --family <anchor>` lists the addresses under one"
            )
        return chr(10).join(said)

    def payload(self, config: Config, claims: bool) -> dict[str, object]:
        return {
            "role": self.role or None,
            # Every file the answer was read from, and not one (RK297): a client comparing two
            # runs needs to know which outline it was handed.
            "files": [config.relative(config.path(one)) for one in self.read],
            "family": self.family or None,
            "block": self.block or None,
            "block_families": list(self.spans),
            "live": len(self.found) - len(self.retired),
            "retired": len(self.retired),
            # The rows are the answer where a family was named, and the families are the answer
            # where none was (RK264's rule): 287 retired addresses is not a listing anybody
            # reads. Under `--claims` the rows *are* the answer whatever the family (RK459).
            "anchors": [
                _anchor_row(one)
                for one in self.found
                if self.family or (claims and _ownership(one))
            ],
            "families": [] if self.family else self.families(),
            "id_anchors": self.spent,
            # Both free addresses are the **project's** even where the listing was narrowed
            # (RK297): the field an author acts on may not be per file.
            "next": next_child(self.whole, self.family) if self.family else None,
            # The question one line up, asked **per namespace** and nowhere else (RK340,
            # RK346). One row where a project declares no `[refs]`, whose `namespace` is null,
            # and one per namespace where it does; `next` is null inside a row where those
            # top-levels are not one numbering, which is an answer and not an absence.
            #
            # Without `opens`, which the narrow payload carries and this one does not: there
            # the free address is the whole answer and the command that makes it a section is
            # what it owes (RK1140); here the listing already names every family, and a client
            # reading this one is not composing an `add --ref` off a single line.
            "next_families": []
            if self.family
            else [
                {"namespace": space or None, "next": next_family(self.spread, space)}
                for space in namespaces(self.spread)
            ],
            # What no question asked and only the gate said (RK297): an address two headings
            # answer to is one no pointer resolves against.
            "doubled": [
                {"anchor": anchor, "files": list(roles)}
                for anchor, roles in doubled(self.whole)
            ],
        }


def _anchor_row(one: Anchor) -> dict[str, object]:
    return {
        "anchor": one.anchor,
        # Which file declared it, which is the whole of RK297 in one field: two rows with one
        # address are two headings, and unlabelled they read as a listing that repeated.
        "role": one.role,
        "live": one.live,
        "written_in": one.written_in or None,
        # The two facts RK453 adds, and they are two because they come apart in both
        # directions: a heading binding nobody that a line claims is RK452's write left undone
        # on an older corpus, and one binding a task no live line claims is prose whose task
        # has shipped. Null and `[]` on a retired address, which has no heading.
        "binds": one.binds or None,
        "claimed": list(one.claimed),
        "orphaned": one.orphaned,
        # The third state, told apart from the two that are (RK461): a memo is prose that was
        # never anybody's, so it is neither bound nor left behind, and a client filtering on
        # `orphaned` alone used to catch it.
        "memo": one.memo,
    }


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


@dataclass(frozen=True, slots=True)
class Gapped:
    """Every id below the highest that no file carries, as one result (RK1170).

    The second verb moved to the shape RK1170 asks for, and `weight`'s reasons hold unchanged:
    both registers are derived here, beside the numbers, so the payload carries what the printed
    answer showed by construction. What the handler keeps is the door — run it, and say which
    register was asked for.

    The two registers differ on purpose, and here that difference is the whole of RK1165: the
    printed one collapses a **contiguous run** of never-carried ids into a single row, because 499
    of this repository's own 503 lines were a numbering jump saying one sentence with a different
    number. The payload keeps every id, a key costing a client nothing to skip where a line costs
    every reader the same attention.
    """

    gaps: tuple[Gap, ...]

    def __str__(self) -> str:
        if not self.gaps:
            return "no gaps: every id below the highest is in one of the files"
        rows: list[tuple[str, str]] = []
        at = 0
        for gap, run in _runs(self.gaps):
            where = gap.id if run == 1 else f"{gap.id}–{self.gaps[at + run - 1].id}"
            at += run
            if gap.never_carried:
                # **Every** run and not a long one (RK1165): a threshold would be a number nobody
                # can re-read, and two consecutive ids in one row is the same information rather
                # than less. What decides the row is contiguity, which is a fact and not a
                # judgement about why the numbering skipped.
                counted = "" if run == 1 else f"  ({run} ids)"
                rows.append(
                    (where, f"never carried  the whole history mentions it nowhere{counted}")
                )
            elif gap.removed_in is None:
                rows.append((where, "unresolvable  no history here to search"))
            else:
                commit = gap.removed_in
                rows.append((where, f"{commit.short}  {commit.date[:10]}  {commit.subject}"))
        # Padded to the widest label, which a range is: a column sized for one id puts the
        # sentence of a collapsed row in a different place from every other one.
        width = max(len(label) for label, _ in rows)
        resolved = sum(1 for gap in self.gaps if gap.resolved)
        skipped = sum(1 for gap in self.gaps if gap.never_carried)
        tail = f", {skipped} never carried" if skipped else ""
        return "\n".join(
            [
                *(f"  {label:<{width}} {said}" for label, said in rows),
                f"{len(self.gaps)} gap(s), {resolved} resolved against history{tail}",
            ]
        )

    def payload(self) -> list[dict[str, object]]:
        """Every gap, one row each — the runs the printed answer collapses are the reader's cost.

        The commit is the four fields a caller reaches an id's departure by, and `None` where
        history was searched and answered nothing: *unresolvable* and *never carried* are two
        different absences (RK95), which the two flags beside it tell apart.
        """
        return [
            {
                "id": gap.id,
                "resolved": gap.resolved,
                "never_carried": gap.never_carried,
                "removed_in": None
                if gap.removed_in is None
                else {
                    "sha": gap.removed_in.sha,
                    "short": gap.removed_in.short,
                    "date": gap.removed_in.date,
                    "subject": gap.removed_in.subject,
                },
            }
            for gap in self.gaps
        ]


def _runs(found: Sequence[Gap]) -> list[tuple[Gap, int]]:
    """Each gap with how many **contiguous never-carried** ids start there (RK1165).

    Only that kind runs together: a gap resolved against history carries a commit of its own and
    two of them are two answers, however adjacent their numbers. What a run of never-carried ids
    carries is one sentence repeated, and this is what lets the row say it once.

    Contiguity is read off the numbers the ids spell, which `next_id` already treats as a
    sequence — a prefix change ends a run for free, two families being two sequences.
    """
    out: list[tuple[Gap, int]] = []
    index = 0
    while index < len(found):
        gap = found[index]
        run = 1
        if gap.never_carried:
            while index + run < len(found) and _follows(found[index + run - 1], found[index + run]):
                run += 1
        out.append((gap, run))
        index += run
    return out


def _follows(earlier: Gap, later: Gap) -> bool:
    """Whether one never-carried id is the next number after another, in the same family."""
    if not later.never_carried:
        return False
    one, two = _numbered(earlier.id), _numbered(later.id)
    return one is not None and two is not None and one[0] == two[0] and two[1] == one[1] + 1


def _numbered(task_id: str) -> tuple[str, int] | None:
    """An id as its family and its number, or None where it spells neither."""
    found = re.match(r"^([A-Za-z]+)(\d+)$", task_id)
    return (found[1], int(found[2])) if found else None
