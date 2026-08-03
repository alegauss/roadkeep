"""What *taken* means, dated outside the repository (RK119).

`pick` (RK11) is a pure function of two files, so N callers reading an unchanged backlog get
N identical answers — and tier 1, which prefers a 🛠 line so one worker finishes what they
started, hands the second agent to ask exactly the line the first one is holding, with the
tier name saying so. The answer to that is that answering becomes a **write**: the marker
flips inside the same serialised transaction that chose the line
(:func:`roadkeep.picking.take`), so the next caller reads a file that has already moved.

That leaves the half a marker cannot carry. 🛠 says the work is under way; it does not say
whether the claim is still live, and a claim held by nobody is a task nobody can pick. So
**when** a claim was taken is recorded here — and here is deliberately the same place the
write lock lives (RK117), for the same three reasons:

* **Not a second store (L2).** It holds no fact about any task. What is durable is
  *claimed* — the 🛠 the roadmap carries, which git moves between checkouts — and this file
  only dates it. Delete it while nothing is running and every claim reads as expired, which
  is precisely the behaviour before this existed: a 🛠 line nobody holds is offered again.
* **An expiry, not a lock.** Past :data:`HELD` seconds a claim is stepped over and the line
  is offered as ordinary half-done work. There is no portable way to ask whether the worker
  is still alive, and an agent that was killed must not take a task out of the backlog for
  ever — a claim nobody can break is the failure, not the fix.
* **No owner.** An owner field would be a schema change carrying a fact that lives outside
  the repository; the identity behind a claim belongs in the commit. So a claim is
  recognised and never attributed, which is why `pick` *names* the ids it stepped around
  rather than only counting them: recognising one's own claim is the caller's to do, and it
  cannot be done against a number.

A claim is only ever read against a 🛠 line, so **releasing one is a marker change that
already has a door**: `status <id> 📋`, `defer`, `ship`, `retire`. Nothing here is told, and
nothing here can go stale by not being told.
"""

from __future__ import annotations

import os
import time
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path

from roadkeep.document import Entry
from roadkeep.locking import sidecar
from roadkeep.schema import IN_PROGRESS

#: How long a claim reads as held before it reads as abandoned. Three orders of magnitude
#: above the write lock's own :data:`~roadkeep.locking.STALE`, because the two measure
#: different spans: a lock covers one command and a claim covers the work. Generous on
#: purpose — expiring on a worker who is still going costs the duplicate answer this exists
#: to stop, while expiring late costs one line staying unoffered for an hour.
#:
#: A constant and not configuration, unlike every limit in `roadkeep.toml` (L6): this dates
#: a transient file outside the repository, so it is a property of the mechanism rather than
#: of the format a project declares — and being wrong about it degrades to the old
#: behaviour instead of to a wrong file.
HELD = 3600.0


class AlreadyHeld(ValueError):
    """A named line is already claimed, so taking it would be the two workers again (RK149).

    Only the *named* door raises it. A pick was choosing anyway, so it steps around a live
    claim and answers with something else; a caller that said which id it wants has nothing
    to step to, and a claim that quietly re-dated itself would send a second worker at one
    line, which is the defect and not the door.

    Says what to do, because a claim names nobody and this one may be the caller's own: the
    read is one call without the flag, and the release is a marker.
    """

    def __init__(self, task_id: str, since: str, marker: str) -> None:
        self.task_id = task_id
        super().__init__(
            f"{task_id} was claimed {since} ago and a claim names nobody, so it may be "
            f"yours: brief it without --claim to read it, or move the marker off {marker} "
            f"to release it"
        )


@dataclass(frozen=True, slots=True)
class Held:
    """One claim a caller was not offered: which line, and how long it has been held."""

    id: str
    age: float

    @property
    def since(self) -> str:
        """`14m`, `2h05m` — the figure a reader checks against how long the work should take."""
        minutes = int(self.age // 60)
        return f"{minutes}m" if minutes < 60 else f"{minutes // 60}h{minutes % 60:02d}m"


def path(root: Path | str) -> Path:
    """Where this checkout's claims are dated — beside its lock, and outside it."""
    return sidecar(root, "claims")


def live(root: Path | str, entries: Iterable[Entry]) -> tuple[Held, ...]:
    """The claims still held, over the lines given, in the order they were given.

    Read *against the lines* and never alone: a claim is a statement about a 🛠 line, so an
    id whose marker has moved on is not held — which is what makes every existing marker
    door a release, with nothing to wire and nothing to forget to call.
    """
    dated = _read(path(root))
    if not dated:
        return ()
    now = time.time()
    return tuple(
        Held(entry.task.id, now - when)
        for entry in entries
        if entry.task.status == IN_PROGRESS
        and (when := dated.get(entry.task.id)) is not None
        and now - when < HELD
    )


def record(root: Path | str, task_id: str, entries: Iterable[Entry]) -> None:
    """Date one claim, and forget every id the roadmap has moved past.

    Pruned on each write rather than on a schedule: the current lines are in front of us
    anyway, and a registry nobody prunes grows for the lifetime of a temp directory. Called
    inside the write lock, so the read-modify-write is not a race — and a claim only ever
    accompanies a marker this transaction just wrote, which is why the id is dated whether
    or not the marker changed: re-taking a line whose claim expired is a new claim.
    """
    target = path(root)
    still = {entry.task.id for entry in entries if entry.task.status == IN_PROGRESS}
    dated = {name: when for name, when in _read(target).items() if name in still}
    dated[task_id] = time.time()
    _write(target, dated)


def _read(target: Path) -> dict[str, float]:
    """The registry as it is on disk — `<id> <epoch>` a line — and empty when unreadable.

    Unreadable is *empty* and never an error: the file is transient, a caller that cannot
    read it loses the dates and not the backlog, and refusing to answer `pick` because a
    temp file went missing would make the answer depend on the one thing that is allowed to
    disappear. A line this cannot parse is skipped for the same reason.
    """
    try:
        raw = target.read_text(encoding="utf-8")
    except OSError:
        return {}
    dated: dict[str, float] = {}
    for line in raw.splitlines():
        task_id, _, when = line.partition(" ")
        try:
            dated[task_id] = float(when)
        except ValueError:
            continue
    return dated


def _write(target: Path, dated: Mapping[str, float]) -> None:
    """Replace the registry in one step, and never fail the command that was answering.

    Written aside and renamed because the *readers* take no lock — `pick` is a query (RK117)
    — so a reader catching a half-written file would lose the tail of it, which is claims
    read as expired and lines handed out twice. Sorted, so a human reading the file sees a
    stable order, and best-effort: an OSError here loses a date, never a task.
    """
    body = "".join(f"{task_id} {when:.6f}\n" for task_id, when in sorted(dated.items()))
    staged = target.parent / f"{target.name}.writing"
    try:
        staged.write_text(body, encoding="utf-8")
        os.replace(staged, target)
    except OSError:
        pass
