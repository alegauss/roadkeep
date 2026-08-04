"""The merge git cannot make, in a file only this tool may write (RK120).

`renumber` (RK97) is the repair for two branches that spent one id. This is the door that
stops the collision from arriving as a hand edit. Two worktrees each scan their own tree,
each derive the same next id, and each append under the same block heading — so git sees
two insertions at one line and writes conflict markers into a file whose only legal writer
is this tool. Resolving them means editing the format by hand, which the guard (RK22)
denies and the gate (RK14) refuses. Worse is the case that does **not** conflict: two
branches touching different blocks merge clean, and the duplicate id lands in silence.

A textual merge guesses because it reads lines. This file is a schema, which makes the
merge **decidable**: a task line is keyed by its id and filed under a declared heading, so
"what changed" is a question about ids and never about line numbers.

* **Every id is decided on its own.** Against the ancestor: unchanged on one side takes the
  other side's line, identical on both sides takes either, absent from both is a deletion
  both sides made. Nothing here is a position in a file, so two branches appending under
  one heading is not a conflict at all — it is two additions.
* **Only what both sides spent is singled out.** An id **both branches created**, carrying
  different work, is the collision — reported by id, because `renumber` is what moves one
  of them and a driver that picked a side would be choosing whose task disappears. An id
  both sides *edited* differently is the ordinary content conflict, reported the same way
  and kept apart in the answer: one wants an address, the other wants a sentence.
* **The frame is one side's.** Headings, the preamble and the non-goals are prose, and the
  tool does not merge prose (L4). One side may have changed them — that side's file is the
  frame the entries are written into. Both, differently, and the merge is refused.
* **It gates its own output.** The merged file is held to :func:`~roadkeep.linting.within`,
  the half of the gate a driver holding three versions of one file can run, before it is
  offered as a result. A merge `lint` would refuse is not a merge — it is a file nobody
  reviewed, arriving with a clean exit code.

Anything refused falls back to git's own conflict markers, whole-file, and exits non-zero.
That is not a failure of the driver: it is the driver declining to write a file it cannot
prove, leaving the reviewer exactly where a repository with no driver would have left them.

Registered per file in `.gitattributes` and per checkout in `git config`, so it is opt-in
configuration and never a rule this tool assumes (L6): `merge --register` writes both, and
prints the two lines it wrote. The command it names is derived and absolute (RK255) — a
config value is executed by git months after the shell that printed it exited, so a name
that resolved on that shell's PATH is a driver that fails at the merge it was wired for.
"""

from __future__ import annotations

import shlex
import shutil
from dataclasses import dataclass
from pathlib import Path

from roadkeep.authoring import place, remove_entry
from roadkeep.config import Config
from roadkeep.document import Document, Entry
from roadkeep.linting import within
from roadkeep.provenance import invocation, persisted

__all__ = [
    "Driver",
    "Merge",
    "Registration",
    "merge",
    "markers",
    "register",
    "registered",
    "role_of",
]

#: Git's default conflict-marker width, and the labels this driver writes when it declines.
#: Whole-file rather than per-hunk: the driver made no decision, so it has no hunk to name,
#: and a marker pair around the whole file is the honest report of that.
MARKER = 7
OURS = "ours"
THEIRS = "theirs"

#: The line `.gitattributes` carries per governed file, and the driver's name in `git
#: config`. One name, so a project that registers twice registers the same thing.
DRIVER = "roadkeep"

#: The key `.gitattributes` sends git to, and the one :func:`registered` reads back.
DRIVER_KEY = f"merge.{DRIVER}.driver"

#: What `.git/config` holds for this driver, as five distinguishable facts (RK266). Kept apart
#: because the remedies differ and only one of them is a defect: `UNRUNNABLE` is a driver git
#: will call and fail, `MOVED` is one that still works and is not what this machine would write,
#: and reporting the second as the first would be crying wolf on every second checkout.
ABSENT = "absent"
CURRENT = "current"
MOVED = "moved"
UNRUNNABLE = "unrunnable"
#: Not an answer either way: no git, no repository, or a git too old for `config --default`.
UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class Merge:
    """The result of one three-way merge, and everything the answer has to say."""

    role: str
    #: The merged file, or None when it was refused — the whole clean/not-clean question.
    text: str | None
    #: Ids whose line came from the other side: added there, or edited there alone.
    took: tuple[str, ...] = ()
    #: Ids the other side removed, and this side did not touch.
    removed: tuple[str, ...] = ()
    #: Ids **both branches created**, carrying different work — the collision RK120 names.
    #: `renumber` moves one of them; a driver that picked would be deleting somebody's task.
    doubled: tuple[str, ...] = ()
    #: Ids both branches edited differently. A content conflict, kept apart from the above
    #: because the remedy is a sentence and not an address.
    contested: tuple[str, ...] = ()
    #: Why it was refused, empty when it was not. Printed, because a driver that exits 1
    #: with no reason is one the reviewer resolves without knowing what it saw.
    reason: str = ""

    @property
    def clean(self) -> bool:
        return self.text is not None


@dataclass(frozen=True, slots=True)
class Driver:
    """What this checkout's `git config` holds for the driver, against what it would hold now.

    RK255 made the stored command absolute and named the condition that ends it. This is the
    other half: naming an expiry is not observing one, and the value lives in `.git/config`,
    which nothing in this tool read — so the first evidence a driver rotted was git writing
    conflict markers into the file whose whole point is that its merge is decidable.
    """

    #: The command found under :data:`DRIVER_KEY`, empty when the key is not set.
    stored: str
    #: The command :func:`register` would write now, from :func:`~roadkeep.provenance.persisted`.
    wanted: str
    #: False when git could not be asked at all — the answer is absent, not negative, the same
    #: reading :class:`~roadkeep.history.HistoryUnavailable` gets everywhere else.
    known: bool = True

    @property
    def state(self) -> str:
        """One of the five above. Runnability is asked before equality, deliberately.

        A driver that differs from what this machine would write is not thereby broken: a
        checkout registered where the console script was on PATH keeps working after this
        package also grows a launcher. What git cannot execute is the defect; what merely
        moved is a fact, and answering the second question first would report both as one.
        """
        if not self.known:
            return UNKNOWN
        if not self.stored:
            return ABSENT
        if not _resolves(self.stored):
            return UNRUNNABLE
        return CURRENT if self.stored == self.wanted else MOVED

    @property
    def wired(self) -> bool:
        """Whether git has a driver here it can actually run — the one yes/no a caller needs."""
        return self.state in (CURRENT, MOVED)


@dataclass(frozen=True, slots=True)
class Registration:
    """What `merge --register` wrote: the attribute lines, and the config it needs."""

    attributes: Path
    added: tuple[str, ...]
    #: Already present, so not written again — re-running is not an accumulating file.
    present: tuple[str, ...]
    #: `git config merge.roadkeep.driver <…>`, as it must be set. Printed and not run: a
    #: driver command is a path into somebody's checkout, and running `git config` for them
    #: would be this tool writing outside the files it was given (L2).
    command: str
    #: What would stop that command resolving later (RK255) — the half of the answer a value
    #: this tool prints once and git executes months afterwards cannot leave to the reader.
    invalidated_by: str = ""
    #: What `git config` holds **now** (RK266), read after the attribute lines were written:
    #: the re-run that reports three lines already there is exactly the one where the config
    #: is the half that moved, so the answer that says nothing changed must not be the whole
    #: answer. `None` only where a caller constructed this without asking.
    driver: Driver | None = None


def merge(config: Config, role: str, base: str, ours: str, theirs: str) -> Merge:
    """Merge three versions of one governed file, or refuse with a reason.

    Refuses — text None — when any version carries a line this tool cannot reproduce (L3),
    when both sides changed the prose around the entries, when an id was spent or edited
    twice, or when the result is a file the gate would refuse.
    """
    schema = config.schema_for(role)
    versions = {
        "the ancestor": Document.parse(base, schema),
        OURS: Document.parse(ours, schema),
        THEIRS: Document.parse(theirs, schema),
    }
    for name, document in versions.items():
        if document.non_canonical:
            named = ", ".join(e.task.id for e in document.non_canonical)
            return Merge(role, None, reason=_unreadable(name, named))
    ancestor, mine, yours = versions["the ancestor"], versions[OURS], versions[THEIRS]

    decided, doubled, contested = _decide(ancestor, mine, yours)
    if doubled or contested:
        return Merge(role, None, doubled=doubled, contested=contested, reason=_spent(doubled, contested))

    frame, source = _frame(ancestor, mine, yours)
    if frame is None:
        return Merge(role, None, reason=_both_sides_moved_the_prose())

    took = tuple(
        task_id
        for task_id, entry in decided.items()
        if entry is not None and _raw(frame, task_id) != entry.raw
    )
    removed = tuple(
        task_id for task_id, entry in decided.items() if entry is None and _raw(frame, task_id)
    )
    result = _materialize(frame, decided)
    findings = within(config, role, result)
    if findings:
        return Merge(role, None, took=took, removed=removed, reason=_refused(findings))
    return Merge(
        role,
        result.render(),
        took=took,
        removed=removed,
        reason="" if source is None else f"prose taken from {source}",
    )


def markers(ours: str, theirs: str, *, width: int = MARKER) -> str:
    """The whole file, between conflict markers — what a refusal leaves in the worktree.

    Git's own fallback, written by this driver rather than left to it: once the driver runs,
    git has handed the merge over, and a non-zero exit with an untouched `%A` would leave the
    reviewer a file that looks like one side won.
    """
    mark = "<" * width, "=" * width, ">" * width
    return (
        f"{mark[0]} {OURS}\n{_terminated(ours)}{mark[1]}\n{_terminated(theirs)}"
        f"{mark[2]} {THEIRS}\n"
    )


def role_of(config: Config, path: str | Path) -> str | None:
    """Which governed file this pathname is, or None — the driver's one lookup.

    Compared as resolved paths, because git hands the driver `%P` as the path *in the
    repository* and the command may be run from anywhere inside it.
    """
    target = (config.root / Path(path)).resolve()
    for role in config.paths:
        if config.path(role).resolve() == target:
            return role
    return None


def register(config: Config) -> Registration:
    """Write one `.gitattributes` line per governed file, and name the config it needs.

    Additive and idempotent: a line already there is reported and not written twice, and
    every other line in the file is carried through untouched — it is the repository's file
    and this command owns three lines in it, the same contract `install` keeps (RK100).

    The driver command is :func:`~roadkeep.provenance.persisted` and never the console script
    literal (RK255). What is named here is stored in `.git/config` and **executed by git**
    when a governed file conflicts, so a name PATH happened to resolve in the terminal that
    ran `register` is a driver that fails at the one moment this file exists for — and git's
    fallback is conflict markers in the file whose whole point is that its merge is decidable.
    """
    path = config.root / ".gitattributes"
    existing = _attribute_lines(path)
    wanted = [f"{config.relative(config.path(role))} merge={DRIVER}" for role in config.paths]
    added = tuple(line for line in wanted if line not in existing)
    present = tuple(line for line in wanted if line in existing)
    if added:
        body = "".join(f"{line}\n" for line in added)
        current = path.read_text(encoding="utf-8") if path.is_file() else ""
        if current and not current.endswith("\n"):
            current += "\n"
        path.write_text(current + body, encoding="utf-8", newline="")
    stored = persisted()
    return Registration(
        attributes=path,
        added=added,
        present=present,
        command=f"git config {DRIVER_KEY} " f'"{driver_value(stored.command)}"',
        invalidated_by=stored.invalidated_by,
        driver=registered(config),
    )


def driver_value(command: str) -> str:
    """The `.git/config` value for a driver reached by `command` — git's four placeholders.

    One spelling, read by :func:`register` when it composes the line and by :func:`registered`
    when it compares what a checkout actually holds: two spellings would make every registered
    driver read as :data:`MOVED` the day one of them gained a placeholder.
    """
    return f"{command} merge %O %A %B --path %P"


def registered(config: Config) -> Driver:
    """Read this checkout's driver back out of `git config` (RK266).

    A read and never a write: setting somebody's git config is outside the files this tool was
    given (L2), which is why `register` prints that line rather than running it — and it is the
    same reason nothing had read it back until now.

    `--default ""` and not a bare `--get`, because git exits 1 for a key that is not set and
    exits 1 for a repository that is not there, and the two are a wired-nothing and a
    question-that-could-not-be-asked. A git too old for `--default` answers :data:`UNKNOWN`,
    which is the honest reading of a tool that could not tell us either way.
    """
    # Imported here and not at module level (RK260): the driver itself is on git's merge path
    # and every governed write reaches this module, while `history` pulls in `backlog` and
    # `sections` — modules a merge never asks anything of.
    from roadkeep.history import HistoryUnavailable, _run as _git  # noqa: PLC0415

    wanted = driver_value(persisted().command)
    try:
        stored = _git(config.root, "config", "--default", "", "--get", DRIVER_KEY).strip()
    except HistoryUnavailable:
        return Driver(stored="", wanted=wanted, known=False)
    return Driver(stored=stored, wanted=wanted)


def _resolves(command: str) -> bool:
    """Whether the thing a stored driver command names is still on this machine.

    Asked of the file and never by running it: a driver is invoked by git with three paths and
    a `--path`, and this tool executing somebody's recorded command to find out whether it
    executes is a side effect nobody asked for.

    `python <script>` is the launcher case, and there the interpreter is the part that stays
    while the script is the part a plugin update moves — so both halves are asked about, which
    is exactly the failure :func:`~roadkeep.provenance.persisted` names as the expiry.
    """
    try:
        argv = shlex.split(command)
    except ValueError:  # an unbalanced quote is a value no shell would run either
        return False
    if not argv:
        return False
    head = argv[0]
    if not Path(head).is_file() and not shutil.which(head):
        return False
    if len(argv) > 1 and Path(head).stem.startswith("python") and argv[1].endswith(".py"):
        return Path(argv[1]).is_file()
    return True


# -- the decision ------------------------------------------------------------


def _decide(
    ancestor: Document, mine: Document, yours: Document
) -> tuple[dict[str, Entry | None], tuple[str, ...], tuple[str, ...]]:
    """One answer per id: the line it ends up with, None for gone, or a conflict.

    Read off the raw lines and not off the parsed fields, because "did this side change it"
    is a question about what was written — two spellings of one task are two lines, and the
    round-trip guarantee above is what makes comparing them exact.
    """
    decided: dict[str, Entry | None] = {}
    doubled: list[str] = []
    contested: list[str] = []
    was, here, there = ancestor.by_id(), mine.by_id(), yours.by_id()
    for task_id in dict.fromkeys((*was, *here, *there)):
        before, ours, theirs = was.get(task_id), here.get(task_id), there.get(task_id)
        if _raw(mine, task_id) == _raw(yours, task_id):
            decided[task_id] = ours
        elif _raw(mine, task_id) == _raw(ancestor, task_id):
            decided[task_id] = theirs
        elif _raw(yours, task_id) == _raw(ancestor, task_id):
            decided[task_id] = ours
        elif before is None:
            doubled.append(task_id)
        else:
            contested.append(task_id)
    return decided, tuple(doubled), tuple(contested)


def _frame(
    ancestor: Document, mine: Document, yours: Document
) -> tuple[Document | None, str | None]:
    """Whose headings and prose the merged file keeps, and None when both sides moved them.

    The skeleton is every line that is not a task line, which is exactly the part of a
    governed file this tool does not write (L4). One side changing it is a decision the
    merge can carry; both changing it differently is prose, and prose is the reviewer's.
    """
    was, here, there = _skeleton(ancestor), _skeleton(mine), _skeleton(yours)
    if there == was or here == there:
        return mine, None
    if here == was:
        return yours, THEIRS
    return None, None


def _skeleton(document: Document) -> tuple[str, ...]:
    """The file with its task lines taken out, endings normalised.

    Normalised because a branch checked out on Windows and one on Linux differ in every
    line, and refusing a merge over that is refusing every merge.
    """
    entries = {entry.lineno for entry in document.entries}
    return tuple(
        line.rstrip("\r\n")
        for number, line in enumerate(document.lines, start=1)
        if number not in entries
    )


def _materialize(frame: Document, decided: dict[str, Entry | None]) -> Document:
    """Write the decided lines into the frame: replace, remove, then place what is new.

    In that order and re-located by id at every step, because each edit reparses and a line
    number held across one is a line number that has already moved — the care every mutator
    in :mod:`roadkeep.document` takes, for the same reason.
    """
    result = frame
    for task_id, entry in decided.items():
        held = result.by_id().get(task_id)
        if entry is not None and held is not None and held.raw != entry.raw:
            result = result.replace_line(held.index, entry.raw)
    for task_id, entry in decided.items():
        held = result.by_id().get(task_id)
        if entry is None and held is not None:
            result = remove_entry(result, held)
    for task_id, entry in decided.items():
        if entry is not None and task_id not in result.by_id():
            # `place` re-renders from the task, which is the same bytes: every version was
            # held to the round-trip above, so nothing arrives here that would come back
            # spelled differently — and the blank-line and block rules are `add`'s, once.
            result = place(result, entry.task).document
    return result


def _raw(document: Document, task_id: str) -> str | None:
    entry = document.by_id().get(task_id)
    return entry.raw if entry is not None else None


def _attribute_lines(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    return {line.strip() for line in path.read_text(encoding="utf-8").splitlines()}


def _terminated(text: str) -> str:
    return text if text.endswith("\n") or not text else text + "\n"


# -- the reasons -------------------------------------------------------------


def _unreadable(version: str, named: str) -> str:
    return (
        f"{version} carries {named} written differently from what the schema renders: a "
        f"merge of lines this tool cannot reproduce would normalise work nobody reviewed"
    )


def _spent(doubled: tuple[str, ...], contested: tuple[str, ...]) -> str:
    out = []
    if doubled:
        out.append(
            f"both branches created {', '.join(doubled)}: one address, two tasks — "
            f"`{invocation()} renumber <id>` on one side, then merge again"
        )
    if contested:
        out.append(
            f"both branches rewrote {', '.join(contested)}: one line, two sentences — "
            f"the wording is the reviewer's and this driver does not pick one"
        )
    return "; ".join(out)


def _both_sides_moved_the_prose() -> str:
    return (
        "both branches changed the headings or the prose around the entries, and this "
        "tool does not merge prose (L4)"
    )


def _refused(findings: list) -> str:
    named = "; ".join(str(finding) for finding in findings[:3])
    more = f" (+{len(findings) - 3} more)" if len(findings) > 3 else ""
    return f"the merged file is one the gate refuses: {named}{more}"
