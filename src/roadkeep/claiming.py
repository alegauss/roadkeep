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
* **An expiry, not a lock.** Past `[claims] held` a claim is stepped over and the line is
  offered as ordinary half-done work. There is no portable way to ask whether the worker is
  still alive, and an agent that was killed must not take a task out of the backlog for
  ever — a claim nobody can break is the failure, not the fix. How long that window is is
  the one number here that is a judgement about how long work takes, so it is the project's
  to declare (L6) and bounded at both ends where it is read (RK151).
* **No owner.** An owner field would be a schema change carrying a fact that lives outside
  the repository; the identity behind a claim belongs in the commit. So a claim is
  recognised and never attributed, which is why `pick` *names* the ids it stepped around
  rather than only counting them: recognising one's own claim is the caller's to do, and it
  cannot be done against a number.

What the registry holds is a **date**, and what that date *means* is three different things
depending on the line and the window — so :func:`survey` is the read that says which (RK161),
and where the file is. Every other question this tool answers is a command (L5); this was the
one that had to be answered by finding a temp file whose name is a digest.

A claim is only ever read against a 🛠 line, so **the marker is what a claim follows** — which
:func:`follow` makes true in both directions (RK158) rather than leaving half of it to be
inferred by the read: a write that puts a line in progress dates a claim, and a write that
takes it out of progress drops one. Two doors change a claim without moving that marker at all
(RK156): `renumber` moves the *address* (:func:`rename`), and `defer` takes the line out of the
file the marker is read in (:func:`release`).
"""

from __future__ import annotations

import os
import time
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from roadkeep.config import Config
from roadkeep.document import Entry
from roadkeep.locking import sidecar
from roadkeep.schema import IN_PROGRESS


def window(config: Config) -> float:
    """This project's claim window, in seconds (RK151).

    Orders of magnitude above the write lock's own :data:`~roadkeep.locking.STALE`, because
    the two measure different spans: a lock covers one command and a claim covers the work.
    Declared in minutes and used in seconds — the declaration is a judgement a person makes
    about a backlog, and the arithmetic is nobody's to repeat at a call site.
    """
    return config.held * 60.0


class AlreadyHeld(ValueError):
    """Taking a line a live claim already holds would be the two workers again (RK149).

    Raised by the **marker write** and therefore by every door that names an id (RK160): a
    pick was choosing anyway, so it steps around a live claim and answers with something else,
    while a caller that said which id it wants has nothing to step to. What made this one
    door's refusal rather than the rule's was that `status <id> 🛠` writes the same marker and
    took the claim in the holder's name, silently — two workers on one line arriving through
    the verb that exists to stop that.

    So **nothing re-dates a live claim**, which is the invariant worth having: the window is
    the expiry, not something a second call can postpone. Says what to do, because a claim
    names nobody and this one may be the caller's own: the read is one call without the flag,
    and the release is a marker.
    """

    def __init__(self, task_id: str, since: str, marker: str) -> None:
        self.task_id = task_id
        super().__init__(
            f"{task_id} was claimed {since} ago and a claim names nobody, so it may be "
            f"yours: read it without --claim, or move the marker off {marker} to release it"
        )


def since(age: float) -> str:
    """`14m`, `2h05m` — the figure a reader checks against how long the work should take.

    One formatter, because two would eventually disagree about the same number in two answers.
    """
    minutes = int(age // 60)
    return f"{minutes}m" if minutes < 60 else f"{minutes // 60}h{minutes % 60:02d}m"


@dataclass(frozen=True, slots=True)
class Held:
    """One claim a caller was not offered: which line, and how long it has been held."""

    id: str
    age: float

    @property
    def since(self) -> str:
        return since(self.age)


class State(StrEnum):
    """What the registry's entry for one id actually is (RK161).

    Three, because the registry holds one thing and means three: a claim is a *date* read
    against a 🛠 line and a window, so an entry outliving either is not a claim and is what an
    operator is hunting when a listing is what they wanted.
    """

    #: 🛠, inside the window: a line no answer will offer.
    HELD = "held"
    #: 🛠, past the window: stepped over, so the line is offered again as half-done work.
    EXPIRED = "expired"
    #: The marker moved on, or no line carries the id at all. Nothing reads it; the next
    #: claim prunes it.
    STALE = "stale"


@dataclass(frozen=True, slots=True)
class Dated:
    """One entry in the registry, and what the files make of it (RK161)."""

    id: str
    age: float
    state: State
    #: The marker the line carries, or empty where no line carries the id.
    marker: str = ""
    block: str = ""

    @property
    def since(self) -> str:
        return since(self.age)


def survey(config: Config, entries: Iterable[Entry]) -> tuple[Dated, ...]:
    """Every dated id, oldest first, with what the roadmap makes of it (RK161).

    The one question about a claim that was not a command: `pick` names the ready lines it
    stepped around and its stalled list annotates a started one, so seeing *all* of them meant
    two questions and a union — and neither reaches an entry on a line that is neither, which
    is exactly the one somebody is looking for.

    Oldest first, because the axis a reader is scanning is age: the entry most likely to belong
    to a worker who is gone is the one at the top. It **ranks nothing and offers nothing** —
    `pick` decides what to work on, and a listing that answered that would be a fourth tier
    nobody declared. Deliberately not an MCP tool for the same reason: `pick` and `brief`
    already name the claims an agent's own answer stepped around, and this is the read a person
    makes about a checkout.
    """
    dated = _read(path(config.root))
    if not dated:
        return ()
    tasks = {entry.task.id: entry.task for entry in entries}
    now, held = time.time(), window(config)
    rows = []
    for task_id, when in dated.items():
        task = tasks.get(task_id)
        if task is None or task.status != IN_PROGRESS:
            state = State.STALE
        else:
            state = State.HELD if now - when < held else State.EXPIRED
        rows.append(
            Dated(
                id=task_id,
                age=now - when,
                state=state,
                marker="" if task is None else task.status,
                block="" if task is None else task.block,
            )
        )
    return tuple(sorted(rows, key=lambda row: -row.age))


def path(root: Path | str) -> Path:
    """Where this checkout's claims are dated — beside its lock, and outside it."""
    return sidecar(root, "claims")


def live(config: Config, entries: Iterable[Entry]) -> tuple[Held, ...]:
    """The claims still held, over the lines given, in the order they were given.

    Read *against the lines* and never alone: a claim is a statement about a 🛠 line, so an
    id whose marker has moved on is not held — which is what makes every existing marker
    door a release, with nothing to wire and nothing to forget to call.
    """
    dated = _read(path(config.root))
    if not dated:
        return ()
    now, held = time.time(), window(config)
    return tuple(
        Held(entry.task.id, now - when)
        for entry in entries
        if entry.task.status == IN_PROGRESS
        and (when := dated.get(entry.task.id)) is not None
        and now - when < held
    )


def record(root: Path | str, task_id: str, entries: Iterable[Entry]) -> None:
    """Date one claim, and forget every id the roadmap has moved past.

    Pruned on each write rather than on a schedule: the current lines are in front of us
    anyway, and a registry nobody prunes grows for the lifetime of a temp directory. Called
    inside the write lock, so the read-modify-write is not a race — and a claim only ever
    accompanies a marker this transaction just wrote, which is why the id is dated whether
    or not the marker changed: re-taking a line whose claim expired is a new claim.

    The prune **stays** now that every door releases explicitly (RK162), and it is not RK159's
    second writer of one rule: a release is an *event* this tool performed, and this is
    reconciliation with the file, which git moves under the tool. A `checkout` onto a branch
    where the line reads 📋 fired no door at all, and the entry it leaves behind is one only a
    read of the roadmap can find.
    """
    target = path(root)
    still = {entry.task.id for entry in entries if entry.task.status == IN_PROGRESS}
    dated = {name: when for name, when in _read(target).items() if name in still}
    dated[task_id] = time.time()
    _write(target, dated)


class Followed(StrEnum):
    """What a marker write did to the claim on its line (RK158). Printed, so it is not silent."""

    CLAIMED = "claimed"
    RELEASED = "released"
    NEITHER = ""


def refuse_taken(
    config: Config, task_id: str, marker: str, entries: Iterable[Entry]
) -> None:
    """Refuse a marker write that would take a claim this line already carries (RK160).

    Called **before** the write and never from inside :func:`follow`, which runs after one: a
    refusal that arrives once the file has moved is a refusal about a state that already
    happened. Beside :func:`~roadkeep.authoring.refuse_reuse` in shape and for the same
    reason — the check that a write is allowed belongs at the write, not at whichever caller
    remembered it.

    Only the in-progress marker. Writing any other one is how a claim is *released*, and a
    release that could be refused is a line nobody can give back.
    """
    if marker != IN_PROGRESS:
        return
    for one in live(config, entries):
        if one.id == task_id:
            raise AlreadyHeld(task_id, one.since, IN_PROGRESS)


def follow(
    root: Path | str, task_id: str, marker: str, entries: Iterable[Entry]
) -> Followed:
    """Make the claim follow the marker, on any door that writes one (RK158).

    A claim is *read* against 🛠, so the marker is already the thing a claim is about — and
    until this existed, the door that writes exactly that marker was the one door that did not
    date it: `status <id> 🛠` is a legitimate way to say "I am on this", and the next `pick`
    read the line as work somebody abandoned and offered it with tier 1's own reason.

    Both directions, because half of this rule was already implicit: writing 🛠 dates a claim
    (again, if one had expired — a re-assertion is a new claim), and writing anything else
    drops it, which is the release the read used to infer. `add` is deliberately not one of
    these doors: the three ways to *start* work are the two `--claim` flags and this one, and a
    line being created is not one the backlog was handing out.
    """
    if marker == IN_PROGRESS:
        record(root, task_id, entries)
        return Followed.CLAIMED
    return Followed.RELEASED if release(root, task_id) else Followed.NEITHER


def rename(root: Path | str, old: str, new: str) -> bool:
    """Carry a claim to the id its line was moved to (RK156). True where one moved.

    The exception to "every marker door is a release": `renumber` does not move the marker,
    it moves the **address**, so the registry keeps an id no line carries while the new one
    reads as started work nobody holds — which is RK119's defect reopened by the one command
    that exists because a merge spent an id twice. The date travels rather than restarting:
    the work is the same age, and a claim that renewed itself on a rename would be an expiry
    a rename could postpone for ever.
    """
    target = path(root)
    dated = _read(target)
    when = dated.pop(old, None)
    if when is None:
        return False
    dated[new] = when
    _write(target, dated)
    return True


def release(root: Path | str, task_id: str) -> bool:
    """Drop a claim outright, for the door where the line leaves the roadmap (RK156).

    `defer` is the case: the worker who set a line aside is not holding it, and the marker
    that a claim is read against goes to the store with the line — so nothing would clear the
    entry until some later claim pruned it, and a `resume` inside the window would read as
    held by whoever gave it up. Every *other* release stays implicit, because every other door
    moves the marker and the marker is what a claim is read against.
    """
    target = path(root)
    dated = _read(target)
    if dated.pop(task_id, None) is None:
        return False
    _write(target, dated)
    return True


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
