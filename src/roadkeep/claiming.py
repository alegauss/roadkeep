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

What a claim *says its commit owns* is the one field here that is not about the line at all
(RK280), and :func:`departing` is what finally calls it (RK294): a scope declared and never
read back at the moment of committing is the advice `agents.md` already carried.

A claim is only ever read against a 🛠 line, so **the marker is what a claim follows** — which
:func:`follow` makes true in both directions (RK158) rather than leaving half of it to be
inferred by the read: a write that puts a line in progress dates a claim, and a write that
takes it out of progress drops one. Two doors change a claim without moving that marker at all
(RK156): `renumber` moves the *address* (:func:`rename`), and `defer` takes the line out of the
file the marker is read in, which the same rule then reads as a release. :func:`follow` is the
only thing that writes a *claim*, and every write it makes is a reconciliation against the lines
it was given (RK163) — one door, so the rule cannot come to have two behaviours. :func:`rename`
touches the same file and is not a second door to that rule: it moves an **address**, which is
the one thing about a claim the marker cannot express.
"""

from __future__ import annotations

import time
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from roadkeep.backlog import Backlog
from roadkeep.config import PROSE_ROLES, ROLES, Config
from roadkeep.ids import CARRIERS
from roadkeep.kernel.document import Entry
from roadkeep.locking import exclusive
from roadkeep.kernel.schema import IN_PROGRESS, Task
from roadkeep.storing import Claim, Store, read, write
from roadkeep.storing import path as store_path


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


#: One registry row as it is on disk. Defined in :mod:`roadkeep.storing` and named here,
#: because the row is the store's to spell (RK330) and the *meaning* of its date is this
#: module's alone — a claim is a date read against a 🛠 line and a window.
Dating = Claim


@dataclass(frozen=True, slots=True)
class Held:
    """One claim a caller was not offered: which line, and how long it has been held."""

    id: str
    age: float
    #: The paths this claim says are its commit's (RK280). Empty where none were declared,
    #: which is every claim taken before the holder said — silence is not a claim to nothing.
    paths: tuple[str, ...] = ()

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
    #: marker write reconciles it away.
    STALE = "stale"


class Where(StrEnum):
    """Where the id is now — the *cause* a stale row used to report as its consequence (RK164).

    "No line carries this id" is true of four different situations and useful in one of them.
    The other three left the roadmap by a door and are recorded: the reader scanning this
    column is deciding whether to act, and only the last of these is anything to act on.
    """

    #: A line in the roadmap. Its own marker and block say the rest.
    OPEN = "open"
    SHIPPED = "shipped"
    RETIRED = "retired"
    PAUSED = "set aside"
    #: In no governed file at all — the leftover, and the one row worth a second look. What
    #: removed it is `gaps`' answer (RK31) and stays one command away: this resolves against
    #: the files it already has open, and history is not one of them.
    NOWHERE = "in no file at all"


@dataclass(frozen=True, slots=True)
class Dated:
    """One entry in the registry, and what the files make of it (RK161)."""

    id: str
    age: float
    state: State
    #: Where the id is now (RK164) — a roadmap line, or which door it left by.
    where: Where = Where.OPEN
    #: The marker the line carries, or empty where no line carries the id.
    marker: str = ""
    block: str = ""
    #: The paths this row says its commit owns (RK280), in the order they were declared.
    paths: tuple[str, ...] = ()

    @property
    def since(self) -> str:
        return since(self.age)

    @property
    def placed(self) -> str:
        """Where this row is, in one column (RK164).

        An open line says so with its own marker and block; anything else says which **door**
        it left by, which is the cause and not the consequence — and the marker column is
        dropped rather than left blank, a gap reading as something that failed.

        On the record since RK1170: the listing and the row's payload are two readings of one
        fact, and a function in the door was where only one of them could reach it.
        """
        if self.where is Where.OPEN:
            return f"{self.marker} Block {self.block}"
        return str(self.where)

    def payload(self) -> dict[str, object]:
        """The same row as data. `marker` and `block` are null rather than empty where no line
        carries the id, so a consumer tells "absent" from "blank"."""
        return {
            "id": self.id,
            "state": str(self.state),
            "where": str(self.where),
            "age": round(self.age),
            "since": self.since,
            "marker": self.marker or None,
            "block": self.block or None,
            "paths": list(self.paths),
        }

    def listed(self, pruned: bool = False) -> str:
        """One line of the registry listing (RK161, RK280).

        The scope is **counted** here and named by `claim <id>`: this listing ranks nothing and
        offers nothing, and four paths per row would make it the other command.
        """
        scoped = f"  {len(self.paths)} path(s)" if self.paths else ""
        state = "pruned" if pruned else str(self.state)
        return f"  {state:<8} {self.id}  claimed {self.since} ago  {self.placed}{scoped}"


def survey(backlog: Backlog) -> tuple[Dated, ...]:
    """Every dated id, oldest first, with what the files make of it (RK161).

    The one question about a claim that was not a command: `pick` names the ready lines it
    stepped around and its stalled list annotates a started one, so seeing *all* of them meant
    two questions and a union — and neither reaches an entry on a line that is neither, which
    is exactly the one somebody is looking for.

    Takes the whole backlog and not the roadmap alone (RK164), because "no line carries this id"
    is true of four situations and worth acting on in one: the ledger and the store say which
    door the other three left by, and the reader scanning the column is deciding exactly that.

    Oldest first, because the axis a reader is scanning is age: the entry most likely to belong
    to a worker who is gone is the one at the top. It **ranks nothing and offers nothing** —
    `pick` decides what to work on, and a listing that answered that would be a fourth tier
    nobody declared. Deliberately not an MCP tool for the same reason: `pick` and `brief`
    already name the claims an agent's own answer stepped around, and this is the read a person
    makes about a checkout.
    """
    config = backlog.config
    dated = _read(config.root)
    if not dated:
        return ()
    tasks = {entry.task.id: entry.task for entry in backlog.roadmap.entries}
    elsewhere = (
        (Where.SHIPPED, backlog.shipped()),
        (Where.RETIRED, backlog.retired()),
        (Where.PAUSED, backlog.deferred()),
    )
    now, held = time.time(), window(config)
    rows = [
        _row(task_id, now - row.when, tasks.get(task_id), elsewhere, held, row.paths)
        for task_id, row in dated.items()
    ]
    return tuple(sorted(rows, key=lambda row: -row.age))


def _row(
    task_id: str,
    age: float,
    task: Task | None,
    elsewhere: tuple[tuple[Where, object], ...],
    held: float,
    paths: tuple[str, ...] = (),
) -> Dated:
    """One registry entry as the two questions a reader is asking: is it a claim, and where."""
    if task is None:
        return Dated(
            id=task_id,
            age=age,
            state=State.STALE,
            where=next((name for name, ids in elsewhere if task_id in ids), Where.NOWHERE),  # type: ignore[operator]
            paths=paths,
        )
    if task.status != IN_PROGRESS:
        state = State.STALE
    else:
        state = State.HELD if age < held else State.EXPIRED
    return Dated(
        id=task_id,
        age=age,
        state=state,
        where=Where.OPEN,
        marker=task.status,
        block=task.block,
        paths=paths,
    )


@dataclass(frozen=True, slots=True)
class Pruning:
    """What a prune left and what it dropped (RK165). Both, because a filter that hides its
    own effect is how "the registry is clean" gets read off a command that emptied it."""

    kept: tuple[Dated, ...] = ()
    dropped: tuple[Dated, ...] = ()


def prune(config: Config) -> Pruning:
    """Drop every row that is not a claim, and leave every row that is (RK165).

    Loads the backlog inside its own lock (RK167), the way :func:`roadkeep.picking.take` does:
    the read decides what is dropped, so a read outside the lock would decide from a state the
    write no longer applies to. Re-entrant, so the dispatcher declaring the same thing about the
    argv costs nothing twice — and a library caller gets the guarantee either way.

    The reconciliation :func:`follow` performs, reachable without a marker to write. It exists
    because the other remedy is the whole file: a checkout between tasks has no marker to move,
    so clearing one row nobody can act on meant deleting the claims of every worker beside it —
    a blast radius the size of the checkout for a problem the size of an id.

    So it decides nothing new. What it keeps is what `follow` keeps: every id the roadmap still
    carries at 🛠, which is a **live claim and an expired one alike** — an expired row is still a
    statement about a started line, and the caller that wants it gone moves the marker. A live
    claim is never dropped here; taking a line from a worker is a marker, and the door that
    refuses it is the one RK160 closed.
    """
    with exclusive(config.root):
        rows = survey(Backlog.load(config))
        dropped = tuple(row for row in rows if row.state is State.STALE)
        if dropped:
            gone = {row.id for row in dropped}
            kept = {n: r for n, r in _read(config.root).items() if n not in gone}
            _write(config.root, kept)
    return Pruning(
        kept=tuple(row for row in rows if row.state is not State.STALE), dropped=dropped
    )


def path(root: Path | str) -> Path:
    """Where this checkout's claims are dated — in the shared store, beside its lock (RK330)."""
    return store_path(root)


def live(config: Config, entries: Iterable[Entry]) -> tuple[Held, ...]:
    """The claims still held, over the lines given, in the order they were given.

    Read *against the lines* and never alone: a claim is a statement about a 🛠 line, so an
    id whose marker has moved on is not held — which is what makes every existing marker
    door a release, with nothing to wire and nothing to forget to call.
    """
    dated = _read(config.root)
    if not dated:
        return ()
    now, held = time.time(), window(config)
    return tuple(
        Held(entry.task.id, now - row.when, row.paths)
        for entry in entries
        if entry.task.status == IN_PROGRESS
        and (row := dated.get(entry.task.id)) is not None
        and now - row.when < held
    )


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

    **Every direction reconciles** (RK163), and that is the whole of what a write here does:
    the entries are the truth, so what is kept is what they still carry at 🛠 — and the id being
    followed is dated on top of that, or left out by having stopped being one of them. Dropping
    a single key instead left every row *no door reported* in place, which a `git checkout`
    creates and only a later claim used to clear. Nothing else writes a claim, for the reason
    two entry points to one rule is how it comes to have two behaviours (RK159) —
    :func:`rename` is not one of them, moving an address rather than following a marker.

    It writes only when the result differs, so a project that never claims never gets a file:
    a `status` on a backlog with no registry is a read and a comparison.

    A **re-assertion keeps the paths** it was holding (RK280): the row is dated again, and the
    scope the holder declared is a statement about the same work, not one the clock revokes.
    A release drops the row and the paths with it, which is what makes a marker the only thing
    that has to be remembered.
    """
    dated = _read(root)
    started = {entry.task.id for entry in entries if entry.task.status == IN_PROGRESS}
    kept = {name: row for name, row in dated.items() if name in started}
    if marker == IN_PROGRESS:
        was = dated.get(task_id)
        kept[task_id] = Dating(time.time(), was.paths if was is not None else ())
    if kept != dated:
        _write(root, kept)
    if marker == IN_PROGRESS:
        return Followed.CLAIMED
    return Followed.RELEASED if task_id in dated else Followed.NEITHER


class NotHeld(ValueError):
    """Declaring a scope for a line nobody is holding (RK280).

    Refused rather than taken, because taking is a **marker** and this door writes no marker:
    a command that dated a claim as a side effect of naming files would be a second way to
    start work, which is the shape RK158 spent a task removing. Says the door that does open.
    """

    def __init__(self, task_id: str) -> None:
        self.task_id = task_id
        super().__init__(
            f"no live claim on {task_id}: a scope is what a claim carries, so take the "
            f"line first with `status {task_id} {IN_PROGRESS}` (or `pick --claim`)"
        )


def scope(
    config: Config, task_id: str, paths: Iterable[str], *, extend: bool = False
) -> tuple[str, ...]:
    """Record the paths a held line's commit owns, and answer them back (RK280).

    The write that was missing. RK117 locks a scan-to-save span and RK119 says who holds a
    line, and both did their job — no governed file corrupted, no id spent twice — while two
    sessions each committed a tree holding the other's source, because the commit step is a
    `git add -A` in a shell script and nothing in the contract could name what belonged to
    whom. `agents.md` carried the remedy as advice ("a tree holding unrelated work wants the
    task's paths staged"), which is where L1's argument says advice does not hold: it is an
    analysis to make at the moment of committing, out of a `git status` that shows both
    sessions' work and says nothing about which is which.

    So the claim carries it, because the claim is the one thing that already knows a line is
    being worked on and by one worker. What is stored is what the holder **said**, verbatim
    and in order: this never asks the disk whether a path exists, and never derives a path
    from the task's prose. A scope inferred from a sentence would be RK55's guessing put in
    charge of what a commit contains.

    The **third** writer of the registry, and the exception is the same one :func:`rename`
    takes: it writes no date. Dating is `follow`'s, so nothing here can start work, postpone
    an expiry or take a line from the worker holding it — the invariant RK160 closed stays
    exactly where it was. Refused on a line no live claim holds, for the same reason.

    Replaces rather than appends, and `extend` does not change that (RK307). A scope is the
    answer to *what is this commit*, and a call that only ever grew one would make a corrected
    answer unreachable without the file — which is RK165's argument, one row along. What
    `extend` changes is where the answer is composed: the caller that found a tenth path after
    declaring nine says *and this too* rather than retyping the nine, and the row is still
    replaced, with the whole scope. Measured across one block here: three of five tasks needed
    a second call, one of them ten paths long.

    **One door and a parameter, not a second function** (RK159): the two are distinguishable
    at the call site and identical at the write, so the invariants below — the refusal on a
    line nobody holds, the untouched date, the collapse — are stated once and cannot come to
    have two behaviours. The **existing paths come first**, because they were declared first
    and the answer is read in the order it will be staged.

    Duplicates collapse, order kept, because the answer is consumed by a `git add --` and a
    path staged twice is noise in a contract meant to be read.
    """
    named = tuple(one for one in paths if one)
    with exclusive(config.root):
        backlog = Backlog.load(config)
        if not any(one.id == task_id for one in live(config, backlog.roadmap.entries)):
            raise NotHeld(task_id)
        dated = _read(config.root)
        row = dated[task_id]
        # Read inside the lock, like everything else this decides from: a scope composed from
        # a row read outside it would drop whatever another call added in between.
        wanted = tuple(dict.fromkeys((*row.paths, *named) if extend else named))
        dated[task_id] = Dating(row.when, wanted)
        _write(config.root, dated)
    return wanted


def elsewhere(config: Config, task_id: str, entries: Iterable[Entry]) -> tuple[Held, ...]:
    """Every *other* live claim that has declared a scope, so a commit can leave it alone.

    The half a claim could not answer before (RK280). A claim names nobody by design (RK119),
    so no write can be refused on the grounds that it is somebody else's — the guard sees a
    path and not a worker, and a session cannot be told it is not itself. What *is* decidable
    is the reverse: given the id being committed, every path some other held line says is its
    own. That is a list the caller subtracts, and it is why this closes at the commit rather
    than at the write.

    Claims with no scope are left out, and the omission is the honest one: silence is a
    holder who has not said, not a holder claiming nothing, so a caller that treated it as
    the second would be answering with a confidence the registry does not carry.
    """
    return tuple(
        one for one in live(config, entries) if one.id != task_id and one.paths
    )


@dataclass(frozen=True, slots=True)
class Scope:
    """A dirty tree split by which claim speaks for each path (RK280, RK294).

    Three lists and not one, because the caller does three different things with them:
    stage :attr:`mine`, leave :attr:`theirs`, and *decide* about :attr:`loose`. The third is
    the list the incident was made of — a path in neither scope is one `git add -A` takes
    silently — so it is named rather than counted.
    """

    #: What the claim being committed says its commit owns, in the order it was declared.
    mine: tuple[str, ...] = ()
    #: `(path, holder)` for every changed path some *other* live claim covers. The **changed**
    #: path and never the declaration it fell under (RK495): what a caller leaves alone is a
    #: file, and a holder who scoped `src/` would otherwise be reported as holding nothing.
    theirs: tuple[tuple[str, str], ...] = ()
    #: Changed paths no live claim covers at all — by name or by the directory above them, and
    #: whose change this id does not already explain (`accounted`, RK1117).
    loose: tuple[str, ...] = ()
    #: Declared paths that would stage nothing right now (RK295) — in neither the dirty set
    #: nor the index. A subset of :attr:`mine`, in the order it was declared, because this is
    #: a reading *of* the declaration and not a fourth list beside it.
    idle: tuple[str, ...] = ()
    #: `(path, ids)` for a governed file whose change this id explains **and** that another
    #: session's line arrived in or left (RK1120). Not a fourth kind of ownership: the file is
    #: staged either way, so what this carries is the ids inside it that are nobody's business
    #: here — the half :attr:`loose` cannot reach, a roadmap always naming this id.
    shared: tuple[tuple[str, tuple[str, ...]], ...] = ()
    #: Which of :attr:`loose` the **index** already carries (RK1197). Not a sixth list: a
    #: staged loose path is the same finding one degree louder, because a `git commit` takes
    #: it whether or not the author reads a diff — and the diff they are reading is the other
    #: side. Measured twice in one session as a version literal another process staged.
    staged: tuple[str, ...] = ()

    @property
    def spoken(self) -> bool:
        """Whether any live claim declared a path — the condition a volunteered read has.

        `claim <id>` was *asked*, so it answers either way. A verb that reports this without
        being asked has nothing to subtract the tree from when no claim spoke, and its whole
        answer would be `git status` restated under a heading saying "loose".
        """
        return bool(self.mine or self.theirs)


def split(
    config: Config,
    task_id: str,
    entries: Iterable[Entry],
    changed: Iterable[str],
    tracked: Iterable[str] = (),
    accounted: Iterable[str] = (),
    shared: Iterable[tuple[str, tuple[str, ...]]] = (),
    staged: Iterable[str] = (),
) -> Scope:
    """Split the changed paths by whose claim names them (RK280, RK295).

    Pure over `changed` and `tracked`: git is the caller's to ask, because the two callers ask
    it under different conditions — one was told to, the other only where a claim spoke. What
    is shared, and the reason this is a function rather than a second composition at each call
    site, is the *subtraction* — lists that have to stay disjoint and stay in the same order
    in both answers.

    `accounted` is the third subtraction and the one RK1117 moved here: paths whose change
    **this id already explains**, so they are not reported as belonging to nobody. It used to
    be done by each printer, filtering `loose` against what the caller called written — and the
    two callers mean different things by that word. `claim <id>` means "its diff carries this
    id" (:func:`written`), which is the predicate; `ship` means "this transaction wrote it",
    which is not. So a governed file that a departure wrote *and* that was already dirty with
    another session's work was reported as written and never as loose, and the `git add --`
    line took both. Measured here: a filing of RK1116 landed inside RK1112's commit.

    `tracked` is the index, and it is what makes :attr:`Scope.idle` a fact rather than a
    guess: a declared path that is dirty stages itself, and one the index carries is a real
    file whose name was not mistyped. A caller that omits it gets no idle reading at all
    rather than one made against half the evidence — the empty default is the honest failure,
    since every path would otherwise read as staging nothing.

    `shared` is :func:`sharing`'s answer, passed in for the same reason `changed` is: it asks
    git, and this function's purity is what lets one caller be told to answer and the other
    answer only where a claim spoke. Carried through rather than composed by each caller so
    the whole :class:`Scope` is assembled in one place — five lists that have to stay
    consistent with each other, and two assemblies of them is how they come to differ.

    All three lists ask :func:`_covers`, which is the whole of RK495: they used to, between
    them, read a declared directory two ways — `idle` as the `git add --` it becomes, and the
    other two as a filename — so a claim on `src/` printed the staging line that takes
    `src/a.py` and, three lines below it, reported `src/a.py` as named by nobody.
    """
    entries = tuple(entries)
    rows = live(config, entries)
    mine = next((one.paths for one in rows if one.id == task_id), ())
    others = elsewhere(config, task_id, entries)
    changed = frozenset(changed)
    known = changed | frozenset(tracked)
    theirs = tuple(
        (one, other.id)
        for one in sorted(changed)
        for other in others
        if any(_covers(declared, one) for declared in other.paths)
    )
    named = (*mine, *(one for other in others for one in other.paths))
    explained = frozenset(accounted)
    adrift = tuple(
        one
        for one in sorted(changed)
        if one not in explained
        and not any(_covers(declared, one) for declared in named)
    )
    return Scope(
        mine=mine,
        theirs=theirs,
        loose=adrift,
        # A subset of `loose` and in its order (RK1197), which is what keeps it from being a
        # sixth list: the question is not *what else is staged* — `mine` is, and should be —
        # but which of the paths nobody claims the next commit already carries.
        staged=tuple(one for one in adrift if one in set(staged)),
        idle=() if not known else tuple(one for one in mine if not _stages(one, known)),
        shared=tuple(shared),
    )


def _covers(declared: str, path: str) -> bool:
    """Does a scope that declared ``declared`` speak for ``path`` (RK495)?

    One reading, asked by every list :func:`split` returns, because a scope is a `git add --`
    argument and that command answers this question the same way whichever list is about to
    quote it. A **directory** is a legitimate scope — git lists neither `status` nor
    `ls-files` by one, so a declared `docs/` compared as a filename matches nothing at all —
    and the trailing slash is the author's spelling rather than a fact, so it comes off before
    the prefix is built and `src` covers what `src/` does.

    Prefix and not `startswith` alone: `src/` must not answer for `srcfoo/a.py`, which is a
    different directory whose name begins the same way.

    And **either side may be the directory** (RK1137), which is RK495's question from the other
    end. Git collapses an untracked tree to its topmost new directory — `?? .claude/skills/` —
    so a claim naming the file the write created was compared against a shorter string and
    matched nothing: RK1136's own ship reported that file as `loose` *and* its declaration as
    staging nothing, two wrong lines about one path.

    The trailing slash is what makes the third case safe rather than a widening. Git spells a
    collapsed tree with one and a dirty **file** never carries one, so `declared.startswith(path)`
    fires exactly where the listed path is a directory standing for everything under it — and a
    claim on `src/a.py` still does not answer for a tracked `src/` holding somebody else's edit,
    because git lists that as `src/other.py`.
    """
    if path == declared or path.startswith(declared.rstrip("/") + "/"):
        return True
    return path.endswith("/") and declared.startswith(path)


def _stages(one: str, known: frozenset[str]) -> bool:
    """Would `git add -- <one>` put anything in the next commit (RK295)?

    The same question :func:`_covers` answers, asked over the whole tree instead of about one
    path: a declaration stages something exactly where it covers a path git already knows —
    dirty or in the index. Kept as its own name because what it reports is about the
    *declaration* (a scope that would stage nothing is a typo) and not about the file.
    """
    return any(_covers(one, other) for other in known)


def writable(config: Config) -> tuple[str, ...]:
    """Every path a verb of this tool can leave bytes in, as the project spells them (RK342).

    The governed files plus the projections RK188 refreshes with them. Narrow on purpose: the
    claim of :func:`written` is that *this tool wrote it*, and a source file whose diff cites
    the id is the author's work and not this tool's — calling it written would put the tool's
    signature on somebody's code. So the candidate set is what a verb could have produced, and
    the diff then says which of those this task's own transaction did.
    """
    # Deferred: `exporting` reaches the write path, which reaches this module (RK260).
    from roadkeep.exporting import DEFAULTS  # noqa: PLC0415

    out = [
        config.relative(config.path(role)) for role in ROLES if config.has(role)
    ]
    # A literal name only: a role's own file is already in the loop above, and listing it twice
    # would report one path as two scopes (RK1110).
    out += [kind.name for kind in DEFAULTS.values() if kind.name]
    return tuple(dict.fromkeys(out))


def written(config: Config, task_id: str, changed: Iterable[str]) -> tuple[str, ...]:
    """The changed paths this task's own transactions wrote (RK342).

    `ship` answers this off :meth:`~roadkeep.shipping.Departure.save`'s own return, which is
    the better source and only exists inside a transaction. `claim <id>` is asked *between*
    them, so the record it has is the files themselves: a claim moved a marker onto this line
    and the projections were refreshed from it, and both diffs therefore name the id.

    Two readings and not one, because the tool's signature is the whole point — a path is
    written only where it is both something a verb could have produced (:func:`writable`) and
    something whose diff carries this id (:func:`~roadkeep.history.carrying`). Either alone is
    the repair RK342 names and refuses: every dirty governed file hands one session another's
    `add`, and every dirty file carrying the id claims authorship of somebody's code.

    A **third** since RK1126, and it is the same claim through the one carrier where the id is
    not on the line: a rationale file edited inside this id's own section carries the id in no
    changed line, because a heading is what carries one. So
    :func:`~roadkeep.history.owned_edit` reads the span instead, and it is asked only of a prose
    path that is dirty and that the first reading did not already name — two subprocesses on the
    turn somebody edited a design, and none on any other.
    """
    # Deferred for RK260's reason, and because git belongs on no path that did not ask.
    from roadkeep.history import carrying, owned_edit  # noqa: PLC0415

    changed = frozenset(changed)
    candidates = [one for one in writable(config) if one in changed]
    named = set(carrying(config, task_id, candidates))
    named.update(
        config.relative(config.path(role))
        for role in PROSE_ROLES
        if config.has(role)
        and (where := config.relative(config.path(role))) in changed
        and where not in named
        and owned_edit(config, "HEAD", task_id, role)
    )
    # In `writable`'s order and never in the order the two readings answered: the list is read
    # against a `git add --` line, and a path's place in it is not a fact about which reading
    # found it.
    return tuple(one for one in candidates if one in named)


def departing(config: Config, task_id: str, entries: Iterable[Entry]) -> Scope | None:
    """The same split, asked at the moment a line leaves the roadmap (RK294).

    RK280 gave a claim the paths its commit owns and gave `claim <id>` the read that names
    what the tree holds for somebody else, and left it with no caller: the declaration was
    asked for in `agents.md` and in the skill, which is advice about what to do at the moment
    of committing — where the analysis is expensive and the author is already finishing. A
    departure *is* that moment, and it holds the id.

    `None` where **no live claim declared a path**, which is every project that has not
    adopted this. Silence and not an empty answer: there is nothing to subtract the tree
    from, so the honest report is no report — and the git process is not paid for either.

    It derives nothing. A departure that filed the dirty paths under the id that is leaving
    would answer the question the incident asked — which of these is mine — by assuming it,
    and the two sessions this exists to separate would each get the other's files with the
    tool's signature on it.

    What this id **already explains** is asked here and not left to the printer (RK1117), and
    asked of the tree *before* the transaction writes: a governed file dirty at this moment is
    dirty from something else, and :func:`written` says whether that something names this id.

    That reading is per **file**, and the roadmap is a file this task is always named in — the
    marker that took the line is in the same diff — so RK1117 left the id inside it unreachable.
    :attr:`Scope.shared` is that half (RK1120): for each carrier this id explains,
    :func:`~roadkeep.history.ids_since` says which *other* ids gained or lost a line since HEAD,
    which two parses answer and no textual reading can — an annotation refresh names every
    dependent in an added line and moves none of them.
    """
    entries = tuple(entries)
    if not any(one.paths for one in live(config, entries)):
        return None
    # Imported here for the reason :mod:`roadkeep.provenance` does it (RK260): this is the
    # only function in the file that asks git anything, and every other reader of a claim —
    # `pick`, `brief`, every marker write — would otherwise pay for the wrapper.
    from roadkeep.history import indexed, status  # noqa: PLC0415

    seen = status(config)
    accounted = written(config, task_id, seen.changed)
    return split(
        config,
        task_id,
        entries,
        seen.changed,
        indexed(config),
        accounted=accounted,
        shared=sharing(config, task_id, accounted),
        staged=seen.staged,
    )


def sharing(
    config: Config, task_id: str, accounted: Iterable[str]
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    """Per governed file this id explains, the other ids whose line moved in it (RK1120).

    Its own function since RK1122, because **both** readers of the commit contract want it and
    only one had it: `claim <id>` computed no `shared` at all — an empty list on every call —
    while being the read a commit is actually composed from, `--porcelain` existing to be piped
    into `git add --`. A departure *must* answer, the claim being released after it; this one is
    asked, so it answers either way, which makes it the cheaper place for the warning and not
    the one to leave it out of.

    Only the files this id already explains (`accounted`): one it does not is reported whole by
    :attr:`Scope.loose`, and naming the ids inside it as well would be one fact under two
    headings.

    Every governed file that can hold a record, in the unit that file keeps it in (RK1125): a
    carrier holds **lines** and :func:`~roadkeep.history.ids_since` reads them, a rationale file
    holds **sections** and :func:`~roadkeep.history.designs_since` reads those. Restricting this
    to the carriers left the prose file a departure wrote unreadable for the same reason the
    roadmap was — one `section amend` puts this id in its diff, and everything else inside it
    then went unnamed.
    """
    # Deferred for RK260's reason, and because git belongs off every path that did not ask.
    from roadkeep.history import designs_since, ids_since, resolves  # noqa: PLC0415

    readers = {
        **dict.fromkeys(CARRIERS, ids_since),
        **dict.fromkeys(PROSE_ROLES, designs_since),
    }
    explained = frozenset(accounted)
    wanted = [
        role
        for role in readers
        if config.has(role) and config.relative(config.path(role)) in explained
    ]
    if not wanted:
        # Nothing to compare, so nothing is asked of git at all — the common case on a tree
        # holding only this task's work, and the reason the loop is not entered to find out.
        return ()
    # Once, and passed down (RK1124): whether git knows `HEAD` is a fact about the repository,
    # and a `rev-parse` per role was 40.6ms of an answer already in hand.
    known = resolves(config, "HEAD")
    out: list[tuple[str, tuple[str, ...]]] = []
    for role in wanted:
        moved = readers[role](config, "HEAD", role, resolved=known) - {task_id}
        if moved:
            out.append((config.relative(config.path(role)), tuple(sorted(moved))))
    return tuple(out)


def rename(root: Path | str, old: str, new: str) -> bool:
    """Carry a claim to the id its line was moved to (RK156). True where one moved.

    The exception to "every marker door is a release": `renumber` does not move the marker,
    it moves the **address**, so the registry keeps an id no line carries while the new one
    reads as started work nobody holds — which is RK119's defect reopened by the one command
    that exists because a merge spent an id twice. The date travels rather than restarting:
    the work is the same age, and a claim that renewed itself on a rename would be an expiry
    a rename could postpone for ever.

    It re-addresses and does not reconcile, unlike :func:`follow` (RK163): the lines are not in
    hand here, and a rename is rare while the next marker write is not — so a row this leaves
    unpruned is cleared by the first `ship` or `status` after it.
    """
    dated = _read(root)
    row = dated.pop(old, None)
    if row is None:
        return False
    dated[new] = row
    _write(root, dated)
    return True


def _read(root: Path | str) -> dict[str, Dating]:
    """This checkout's claims, out of the shared store — empty where it cannot be read.

    The grammar, the atomic replace and the "unreadable is empty" rule all belong to
    :mod:`roadkeep.storing` now (RK330); what stays here is the one table this module owns.
    """
    return dict(read(root).claims)


def _write(root: Path | str, dated: Mapping[str, Dating]) -> None:
    """Replace the claims table, and leave every other table exactly as it was.

    Read-modify-write, which is safe for the reason it is safe everywhere else here: every
    writer of the store runs under the checkout's exclusive lock (:func:`roadkeep.cli.dispatch`),
    so nothing can land between the read and the replace. A claim that dropped the write
    record on its way past would be the digest sidecar's data lost to the registry's write —
    the failure a shared file has and two files did not, closed at the one door that writes.
    """
    write(root, Store(claims=dict(dated), writes=read(root).writes))
