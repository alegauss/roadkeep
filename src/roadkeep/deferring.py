"""The two doors the store needs, one of them the way back (RK91).

RK96 built the state and stopped there: a fifth marker in a fifth governed file, read by
the parser and the gate, and nothing that could put a line in it. So a pause was still
spelled as a retirement, which is terminal by construction — the resolver reads a retired
dep as never (RK28), and a re-add cannot reclaim the id, because retired-never-reused is
enforced (RK4). Recording "not now" that way destroys exactly what makes it not-now: the
id every dependent names, the `§id` rationale, and the thread `origin` and `deps` key on.

:func:`defer` is the transaction `ship` and `retire` are, with two differences that are the
whole point:

* **The section is carried, not deleted.** A departure removes the design because a shipped
  line has none left to state; a pause keeps it, and the gate already knows to leave a
  section the store points at alone rather than reporting it as an orphan.
* **The destination is revivable.** :func:`resume` is the return direction the ledger's
  doors lack, and it is the same all-or-nothing shape read backwards. That is not a reused
  id: a deferred id was never retired, so the same work coming back under its own number is
  the pause working, not the non-goal being crossed.

Two things this deliberately does not preserve, both because the file *is* the state (RK96):

* **The open marker.** The store holds ⏸ and nothing else, so 📋 and ⏳ are indistinguishable
  the moment a line lands there. `resume --marker` is where the author says which it was —
  the default is the project's first, exactly as `add`'s is, and a marker invented from the
  word "resume" would be this tool holding an opinion about someone else's maturity.
* **The indent.** A nested line said which roadmap line it belonged under (RK49), and that
  line is not in the store — the same reason `ship` files its entry at column zero.

The reason is a **derived prefix on the `why`**, which is `retire`'s shape one door over: the
author's sentence is never rewritten (L4), it is wrapped, and :func:`resume` unwraps exactly
what this module wrote. The prefix ends at the first ``): ``, so a reason that spells that
sequence is refused rather than stored — a pause the return trip cannot undo is a pause that
silently became a rewrite of the design sentence.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from roadkeep import claiming
from roadkeep.authoring import Insertion, place, remove_entry
from roadkeep.backlog import Backlog, NotOpen
from roadkeep.config import PROSE_ROLES, Config
from roadkeep.document import Document, save_all
from roadkeep.markers import refresh
from roadkeep.schema import Task
from roadkeep.sections import declaring

__all__ = [
    "Carried",
    "NoStore",
    "NotSetAside",
    "Pause",
    "Resumption",
    "SetAside",
    "UnrecoverableReason",
    "defer",
    "resume",
]

#: What the derived prefix opens and closes. One spelling, one writer — the same rule the
#: line format itself obeys, applied to the one field this module composes.
_OPEN = "set aside ("
_CLOSE = "): "


class NoStore(ValueError):
    """A pause with nowhere to go: this project declares no deferred file (RK96).

    Refused and not scaffolded on the way past. A governed file is a path in
    `roadkeep.toml` (L6) and `init` is what writes one — a store a `defer` invented at the
    moment it needed one would be a format decided by a verb, which is the thing Block A
    exists to prevent.
    """

    def __init__(self, task_id: str) -> None:
        self.task_id = task_id
        super().__init__(
            f"{task_id} cannot be set aside: no deferred store is declared — add "
            f'`deferred = "<path>"` under [files] and create the file with its block '
            f"headings, or retire the line if the pause is really an abandonment"
        )


class SetAside(ValueError):
    """The store already holds this id, so there is no line here to pause."""

    def __init__(self, task_id: str, where: str, lineno: int) -> None:
        self.task_id = task_id
        self.lineno = lineno
        super().__init__(
            f"{task_id} is already set aside in {where}:{lineno}: a second line would be "
            f"two answers to when this work comes back, and nothing says which is right"
        )


class NotSetAside(KeyError):
    """`resume` against an id the store does not hold.

    Names where it *is*, because "not in the store" is the same sentence for a task that is
    open, one that shipped and one that never existed — and only the last is a typo.
    """

    def __init__(self, task_id: str, where: str, *, elsewhere: str = "") -> None:
        self.task_id = task_id
        found = f" ({elsewhere})" if elsewhere else ""
        super().__init__(
            f"{task_id} is not in {where}{found}: resume returns a line the store holds, "
            f"and a task that never paused has nothing to come back from"
        )


class UnrecoverableReason(ValueError):
    """A reason spelling the sequence that ends the derived prefix.

    Refused at input rather than stored, because the damage is invisible until the return
    trip: the unwrap stops at the first ``): ``, so the author's own sentence would come
    back with the tail of the reason glued to its front, and `lint` cannot see a `why` that
    is merely wrong.
    """

    def __init__(self, reason: str) -> None:
        super().__init__(
            f"the reason may not contain {_CLOSE!r}: it is what closes the derived prefix, "
            f"and resume would restore a sentence the pause rewrote — {reason!r}"
        )


@dataclass(frozen=True, slots=True)
class Carried:
    """The design a pause kept, and the file that actually declares it (RK229).

    RK196 taught `ship` to resolve an anchor across the declared prose roles and to report
    the file it wrote; this is the same sentence one verb over, and the reason it is a type
    rather than a string is that the anchor alone is what let the CLI supply the rest — a
    project declaring `strategy` was told its design was kept in an `improvements` file it
    does not have, and the KeyError that named it arrived *after* both writes.

    `role` is None where no declared prose file holds the anchor, or where two do, and
    `absence` is the sentence saying which — never resolved by picking, for the reason a ship
    does not pick either: which of two a line meant is `ref.ambiguous`, and a pointer
    resolving to nothing is a `lint` finding this door has no business answering.
    """

    #: As the line spells it, `§` included — the pointer, not the id it usually equals.
    anchor: str
    #: The prose role holding it, where exactly one does. `Config.path` takes it from here.
    role: str | None = None
    #: Why no role answered, ready to print. Empty exactly when `role` is not None.
    absence: str = ""


@dataclass(frozen=True, slots=True)
class Pause:
    """Every edit setting one line aside makes, as data, before it is written."""

    task_id: str
    #: The line as the store now holds it: ⏸, and every other slot kept.
    store: Insertion
    #: The roadmap without it, with every annotation re-derived (RK8).
    roadmap: Document
    removed_from: int
    refreshed: tuple[str, ...] = ()
    marker: str = ""
    #: The section this did **not** delete, named — silence about a carried design reads
    #: exactly like the deletion a departure makes. Resolved here and not by the caller
    #: (RK229): the role is a fact about the files this transaction read.
    carried: Carried | None = None
    #: Open lines that still name this id. Reported and not refused: waiting on paused work
    #: is a legitimate state, and it is what `deps` and RK92 are for.
    dependents: tuple[str, ...] = ()

    #: The checkout, so a claim on the paused line can be dropped (RK156). Every other door
    #: releases one by moving the marker; this one takes the line out of the file the marker
    #: is read in, which no later read can tell from a claim still held.
    root: Path | None = None

    def save(self) -> None:
        """Write both files. Nothing here can fail on the format — that was decided.

        The store first, for the reason the ledger goes first in a departure (RK118): the
        arrival is written before the removal, so a crash between them leaves the line in
        both files — visible, and a `resume` away — rather than in neither.
        """
        save_all(self.store.document, self.roadmap)
        if self.root is not None:
            # Last, and never a condition of the write: the worker who set this aside is not
            # holding it, and a claim left behind would greet the `resume` (RK156). The same
            # rule every marker write obeys (RK158), the marker here being ⏸.
            claiming.follow(self.root, self.task_id, self.marker, self.roadmap.entries)


@dataclass(frozen=True, slots=True)
class Resumption:
    """The same transaction read backwards: the line returns, the store lets it go."""

    task_id: str
    #: The line as the roadmap holds it again, under its own block and its own id.
    roadmap: Insertion
    store: Document
    removed_from: int
    refreshed: tuple[str, ...] = ()
    marker: str = ""
    #: The reason the pause recorded, removed from the `why` and reported once — the last
    #: place it is visible, because the line that comes back is a design and not a history.
    was: str | None = None
    #: The checkout, so the claim can follow the marker this returns the line at (RK158): a
    #: `resume --marker 🛠` is an assertion that somebody is on it, like every other 🛠 write.
    #: What it did is not a field here — the command prints the marker, which is the fact, and
    #: a second copy of it would be a second thing to keep true.
    root: Path | None = None

    def save(self) -> None:
        # The same rule read backwards: the roadmap is the arrival now, so it goes first
        # and the store's removal second (RK118). A line in both files is a state a reader
        # can see and a second `resume` can finish; a line in neither is one nobody can.
        save_all(self.roadmap.document, self.store)
        if self.root is not None:
            claiming.follow(
                self.root, self.task_id, self.marker, self.roadmap.document.entries
            )


def defer(config: Config, task_id: str, *, reason: str) -> Pause:
    """Move one open line to the store. Validates both edits before writing either.

    Refused when the id is already terminal: an entry in the ledger says the work shipped or
    was abandoned, and pausing it afterwards would make two files disagree about a decision
    that is already recorded. That check is the ledger's own, so it holds whether the entry
    is a ✅ or a 🗑.
    """
    if not config.has("deferred"):
        raise NoStore(task_id)
    if _CLOSE in reason:
        raise UnrecoverableReason(reason)

    backlog = Backlog.load(config)
    roadmap = backlog.roadmap
    entry = roadmap.by_id().get(task_id)
    if entry is None:
        raise NotOpen(
            task_id,
            config.relative(config.path("roadmap")),
            shipped=task_id in backlog.shipped(),
        )
    _refuse_recorded(config, task_id)
    store = config.document("deferred")
    held = store.by_id().get(task_id)
    if held is not None:
        raise SetAside(task_id, config.relative(config.path("deferred")), held.lineno)

    marker = config.schema.deferred_marker
    insertion = place(store, _as_paused(entry.task, marker, reason))
    remaining = remove_entry(roadmap, entry)
    # Derived against the state this write *creates* — the line is out of the roadmap — for
    # the same reason a departure does it (RK8): an annotation left un-derived by one door
    # is one nothing else revisits.
    # Both halves of the new state, not just the roadmap: the dependents' annotations are
    # derived from where this id now *is* (RK92), and a refresh reading the store from disk
    # would annotate against a file this transaction has not written yet.
    derived = refresh(replace(backlog, roadmap=remaining, store=insertion.document))
    return Pause(
        task_id=task_id,
        store=insertion,
        roadmap=derived.document,
        removed_from=entry.lineno,
        refreshed=derived.changed,
        marker=marker,
        carried=_carried(config, entry.task.ref),
        dependents=tuple(
            e.task.id for e in derived.document.entries if task_id in e.task.dep_ids
        ),
        root=config.root,
    )


def resume(config: Config, task_id: str, *, marker: str | None = None) -> Resumption:
    """Return one line from the store to its block. The same transaction, backwards.

    `marker` is the open one the line comes back with, and it defaults to the project's
    first exactly as `add`'s does: the store holds ⏸ and nothing else (RK96), so which open
    marker the pause set aside is not a fact any file still has, and inventing one would be
    this tool stating a maturity it cannot read.
    """
    if not config.has("deferred"):
        raise NoStore(task_id)

    where = config.relative(config.path("deferred"))
    store = config.document("deferred")
    held = store.by_id().get(task_id)
    if held is None:
        raise NotSetAside(task_id, where, elsewhere=_whereabouts(config, task_id))
    _refuse_recorded(config, task_id)

    backlog = Backlog.load(config)
    open_line = backlog.roadmap.by_id().get(task_id)
    if open_line is not None:
        raise SetAside(task_id, config.relative(config.path("roadmap")), open_line.lineno)

    status = marker or config.schema.markers[0]
    insertion = place(backlog.roadmap, _as_open(held.task, status))
    remaining = remove_entry(store, held)
    # The store this write leaves behind, for `defer`'s reason read backwards: a dependent
    # still annotated ⏸ after the pause ended is the stale cache RK8 exists to prevent.
    derived = refresh(replace(backlog, roadmap=insertion.document, store=remaining))
    returned = next(e for e in derived.document.entries if e.task.id == task_id)
    return Resumption(
        task_id=task_id,
        roadmap=Insertion(document=derived.document, entry=returned),
        store=remaining,
        removed_from=held.lineno,
        refreshed=tuple(name for name in derived.changed if name != task_id),
        marker=status,
        was=_reason(held.task.why),
        root=config.root,
    )


def _carried(config: Config, ref: str | None) -> Carried | None:
    """Where the design this pause kept actually is (RK229).

    Answered on the way past rather than reported as an anchor for the CLI to place, because
    the line naming a file is the one line in the answer whose job is to say where a reader
    goes looking — and RK96's whole argument for keeping the section is that they can.

    Every outcome is a sentence and none is a refusal: nothing is being deleted here, so a
    pointer that resolves to nothing or to two files is a pause that worked and a `lint`
    finding the author already owes. Saying so beats a path composed out of the default.
    """
    if ref is None:
        return None
    anchor = f"§{ref}"
    roles = declaring(config, ref)
    if len(roles) == 1:
        return Carried(anchor=anchor, role=roles[0])
    if roles:
        both = " and ".join(config.relative(config.path(role)) for role in roles)
        return Carried(
            anchor=anchor,
            absence=f"declared by {both}, so the pointer names neither",
        )
    declared = tuple(role for role in PROSE_ROLES if config.has(role))
    if not declared:
        return Carried(
            anchor=anchor,
            absence=f"this project declares no {' or '.join(PROSE_ROLES)} file",
        )
    named = " or ".join(config.relative(config.path(role)) for role in declared)
    return Carried(anchor=anchor, absence=f"not in {named}, so nothing was carried")


def _as_paused(task: Task, marker: str, reason: str) -> Task:
    """The same task as the store states it: ⏸, the reason wrapped around the design."""
    return replace(
        task,
        status=marker,
        why=f"{_OPEN}{reason}{_CLOSE}{task.why}",
        # At column zero, for `ship`'s reason (RK49): the indent named a roadmap line this
        # one was nested under, and that line is not in the store.
        indent="",
    )


def _as_open(task: Task, marker: str) -> Task:
    """The same task as the roadmap states it again, with this module's prefix removed."""
    return replace(task, status=marker, why=_unwrapped(task.why))


def _reason(why: str) -> str | None:
    """The reason a pause recorded, or None where the prefix is not this module's."""
    if not why.startswith(_OPEN) or _CLOSE not in why:
        return None
    return why[len(_OPEN) :].split(_CLOSE, 1)[0]


def _unwrapped(why: str) -> str:
    """The author's sentence, with the derived prefix taken back off.

    Left exactly as written when the prefix is not there: an `amend` may have replaced the
    whole sentence while the line was paused, and a resume that stripped a prefix it did not
    write would be editing prose (L4).
    """
    if _reason(why) is None:
        return why
    return why.split(_CLOSE, 1)[1]


def _refuse_recorded(config: Config, task_id: str) -> None:
    """A pause is between open and terminal, so an id the ledger holds has neither door."""
    if not config.has("changelog") or not config.path("changelog").is_file():
        return
    recorded = config.document("changelog").by_id().get(task_id)
    if recorded is None:
        return
    # Imported here rather than at module scope: the two write paths are peers, and this is
    # the one fact one of them owns about the other — the ledger's refusal, in its words.
    from roadkeep.shipping import AlreadyRecorded

    raise AlreadyRecorded(
        task_id,
        config.relative(config.path("changelog")),
        recorded.lineno,
        recorded.task.status,
    )


def _whereabouts(config: Config, task_id: str) -> str:
    """Where the id actually is, for a refusal that would otherwise name only where it is not."""
    if config.document("roadmap").by_id().get(task_id) is not None:
        return "it is open in the roadmap"
    if config.has("changelog") and config.path("changelog").is_file():
        recorded = config.document("changelog").by_id().get(task_id)
        if recorded is not None:
            return f"the changelog records it as {recorded.task.status}"
    return "no file mentions it"
