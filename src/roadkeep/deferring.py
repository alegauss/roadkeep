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

from collections.abc import Sequence
from dataclasses import dataclass, replace
from pathlib import Path

from roadkeep import claiming, queueing
from roadkeep.authoring import Insertion, place, remove_entry
from roadkeep.backlog import Backlog, NotOpen, Whereabouts
from roadkeep.config import PROSE_ROLES, Config
from roadkeep.kernel.document import Document, Entry, save_all
from roadkeep.markers import refresh
from roadkeep.provenance import invocation
from roadkeep.kernel.schema import PAUSED_CLOSE, PAUSED_OPEN, Task, authored_why, pause_reason
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

#: What the derived prefix opens and closes. One spelling, and since RK1115 it lives in the
#: kernel: this module composes it, and the rule that measures a `why` has to know what part
#: of one it wrote — two spellings of that would be a limit disagreeing with the door about
#: which characters an author is charged for.
_OPEN = PAUSED_OPEN
_CLOSE = PAUSED_CLOSE


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


class NoPlacement(ValueError):
    """`--marker` on a resume that places no line (RK1083).

    The reconciling path removes the store's stale copy and leaves the roadmap alone, so the
    open marker a returned line would come back at has nothing to be about. Refused rather
    than ignored, which is `NoCompletion`'s and `NoSpan`'s rule: a flag accepted where it
    can take no effect is a flag the caller believes took one.

    The remedy is the ordinary one — `status <id> <marker>` writes the marker of a line that
    is already there — and it is named, because a refusal that only says no costs the reader
    the turn this one saves.
    """

    def __init__(self, task_id: str, where: str, lineno: int) -> None:
        self.task_id = task_id
        super().__init__(
            f"--marker names the marker a returned line comes back at, and this call places "
            f"none: {task_id} is already open at {where}:{lineno} and only the store's copy "
            f"is removed — `{invocation()} status {task_id} <marker>` writes the marker of a "
            f"line that is already there"
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

    def line(self, config: Config) -> str:
        """The one line saying where a paused design stayed (RK229).

        `kept in <file>` only where a file holds it. An absence spells itself instead of being
        dressed as a location: "kept in IMPROVEMENTS.md" about a section that is not there
        sends a reader to look, and the pause is right either way.

        On the record since RK1170, where `_defer` was composing it: which file this resolved
        to is what this type exists to carry, and a phrasing about it belongs with it.
        """
        if self.role is None:
            return f"{self.anchor} — {self.absence}"
        return f"{self.anchor} kept in {config.relative(config.path(self.role))}"


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
    #: The priority entry this pause took out (RK327), or `None` where the queue never
    #: named it. Taken and not kept, because a paused line is one `pick` can never offer;
    #: put back by the author at the `resume`, which is where the order is known again.
    dequeued: str | None = None
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
    #: Whether this call **reconciled** a contradiction rather than returning a line (RK1081):
    #: the roadmap already carried the id, so the store entry was the stale half and only it
    #: was removed. Reported rather than inferred — the caller printing "returned to Block A"
    #: over a line that never moved would be describing a write nobody made.
    reconciled: bool = False

    def save(self) -> tuple[Path, ...]:
        """Write both files, and answer every path that took (RK1130).

        The store first, for the reason the ledger goes first in a departure (RK118): the
        arrival is written before the removal, so a crash between them leaves the line in
        both files — visible, and a `resume` away — rather than in neither.
        """
        wrote = save_all(self.store.document, self.roadmap)
        if self.root is not None:
            # Last, and never a condition of the write: the worker who set this aside is not
            # holding it, and a claim left behind would greet the `resume` (RK156). The same
            # rule every marker write obeys (RK158), the marker here being ⏸.
            claiming.follow(self.root, self.task_id, self.marker, self.roadmap.entries)
        return wrote

    @property
    def block(self) -> str:
        return self.store.entry.task.block

    def event(self, config: Config) -> dict[str, object]:
        """What this pause did to the block it left (RK38), off the roadmap it wrote."""
        from roadkeep.rendering import _event  # noqa: PLC0415 - RK260

        return _event(self.task_id, self.block, self.roadmap, config)

    def stated(self, config: Config, wrote: Sequence[Path]) -> str:
        """Where the line went, and what the pause kept (RK229, RK327).

        Beside :meth:`payload` since RK1170. `wrote` is a parameter and not a field, because
        :meth:`save` is the caller's step: a record that named paths before they were written
        would be answering about a write that may not have happened.
        """
        from roadkeep.rendering import (  # noqa: PLC0415 - RK260
            _dequeued_rows,
            _event_rows,
            _staging_rows,
        )

        roadmap = config.relative(config.path("roadmap"))
        store = config.relative(config.path("deferred"))
        rows = [
            f"{self.task_id} {self.marker} {store}:{self.store.lineno} under Block {self.block}",
            f"  removed  {roadmap}:{self.removed_from}",
        ]
        if self.carried is not None:
            # Named, because every other door that moves a line deletes this section: silence
            # about a design that was kept reads exactly like the deletion (RK6). The *file* is
            # the pause's answer and never this line's (RK229) — composing it here from the
            # improvements default is what named a path a strategy-only project does not declare.
            rows.append(f"  carried  {self.carried.line(config)}")
        if self.dependents:
            rows.append(f"  still    {', '.join(self.dependents)} name {self.task_id}")
        if self.refreshed:
            rows.append(f"  derived  {', '.join(self.refreshed)} (dep annotations re-derived)")
        rows += _dequeued_rows(self.dequeued)
        rows += _staging_rows(config.relative(one) for one in wrote)
        rows += _event_rows(self.event(config), "  ", config=config)
        return "\n".join(rows)

    def payload(self, config: Config, wrote: Sequence[Path]) -> dict[str, object]:
        """The same answer as data, with the design this did not delete (RK229)."""
        from roadkeep.rendering import (  # noqa: PLC0415 - RK260
            _carried_json,
            _wrote_json,
        )

        return {
            "id": self.task_id,
            "marker": self.marker,
            "deferred": {
                "file": config.relative(config.path("deferred")),
                "line": self.store.lineno,
                "rendered": self.store.rendered,
            },
            "roadmap": {
                "file": config.relative(config.path("roadmap")),
                "removed": self.removed_from,
            },
            "carried": _carried_json(config, self.carried),
            "dequeued": self.dequeued,
            "dependents": list(self.dependents),
            "refreshed": list(self.refreshed),
            **_wrote_json(config, wrote),
            "event": self.event(config),
        }


@dataclass(frozen=True, slots=True)
class Resumption:
    """The same transaction read backwards: the line returns, the store lets it go."""

    task_id: str
    #: The roadmap as this write leaves it. A **document** and not an `Insertion` since
    #: RK1086: that type is a line and the file that now holds it, which is right for the
    #: act this verb was built for and wrong for the one RK1081 added. A reconciling call
    #: places nothing, so it had to point the field at the entry it left alone — and the
    #: third act, where the *ledger* is what already states the outcome, has no entry
    #: anywhere to point at. `Insertion(entry=None)` parses and the printer reads
    #: `.entry.task.block` two lines later, which is how RK1084 found this rather than
    #: shipping a verb.
    roadmap: Document
    #: The line this call put back, or `None` where it placed none. The two are different
    #: answers and the shape now says which: a caller printing "returned to Block A" over a
    #: line that never moved is describing a write nobody made (RK1083).
    placed: Entry | None
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
    #: Whether this call **reconciled** a contradiction rather than returning a line (RK1081):
    #: the roadmap already carried the id, so the store entry was the stale half and only it
    #: was removed. Reported rather than inferred — the caller printing "returned to Block A"
    #: over a line that never moved would be describing a write nobody made.
    reconciled: bool = False

    def save(self) -> tuple[Path, ...]:
        # The same rule read backwards: the roadmap is the arrival now, so it goes first
        # and the store's removal second (RK118). A line in both files is a state a reader
        # can see and a second `resume` can finish; a line in neither is one nobody can.
        wrote = save_all(self.roadmap, self.store)
        if self.root is not None:
            claiming.follow(
                self.root, self.task_id, self.marker, self.roadmap.entries
            )
        return wrote

    def standing(self, config: Config) -> Entry | None:
        """The line this call placed, or the one already there on a reconciling call (RK1086).

        Asked rather than faked: the shape says a reconciliation places nothing, so the entry
        being described has to be looked up where it already was.
        """
        return self.placed or config.document("roadmap").by_id().get(self.task_id)

    def event(self, config: Config) -> dict[str, object]:
        """What this return did to the block it landed in (RK38), off the roadmap it wrote."""
        from roadkeep.rendering import _event  # noqa: PLC0415 - RK260

        standing = self.standing(config)
        block = standing.task.block if standing else ""
        return _event(self.task_id, block, self.roadmap, config)

    def requeue(self, config: Config) -> str | None:
        """The `priority add` a resumed line may want, where this project has a queue (RK327).

        Offered and never done. `defer` took the entry out because a paused line is one `pick`
        can never offer; what it could not keep is **where in the order it sat**, the store
        holding a line and not a rank — so a resume that re-queued would be choosing a position
        nobody stated. Silent where no heading declares a section, which is most projects: a
        follow-up naming a list that does not exist is a command that cannot run.

        On the record since RK1170, with both registers that print it: this is the half of the
        pause the verb does not undo, which makes it part of what the transaction answers.
        """
        try:
            queue = queueing.declared(config)
        except (KeyError, OSError):  # a roadmap this command already reported on
            return None
        if queue.declared_in != "roadmap" or self.task_id in queue.tokens:
            return None
        return (
            f"`{invocation()} priority add {self.task_id}` if it goes back in the order — the "
            f"pause took it out, and where it sat is not something the store kept"
        )

    def stated(self, config: Config, wrote: Sequence[Path]) -> str:
        """Which of the two acts this was, and what came back with the line (RK1083).

        Beside :meth:`payload` since RK1170. `ship` answers the same shape the same way — `RK1
        closed` against `RK1 →` — because a caller holding an id should not have to know which
        of two states the files are in, and the *output* is where they find out.
        """
        from roadkeep.rendering import (  # noqa: PLC0415 - RK260
            _event_rows,
            _staging_rows,
        )

        roadmap = config.relative(config.path("roadmap"))
        store = config.relative(config.path("deferred"))
        standing = self.standing(config)
        if self.reconciled:
            rows = [
                f"{self.task_id} reconciled  {store}:{self.removed_from} removed, "
                f"already {self.marker} in {roadmap}:{standing.lineno}",
                "  roadmap  untouched: the open line is what the files should say",
            ]
        else:
            block = standing.task.block if standing else ""
            rows = [
                f"{self.task_id} {self.marker} {roadmap}:{self.placed.lineno} "
                f"under Block {block}",
                f"  removed  {store}:{self.removed_from}",
            ]
        if self.was is not None:
            # The last time the reason is visible: what comes back is a design, and the pause
            # it went through is history the commit states rather than the line.
            rows.append(f"  was      set aside: {self.was}")
        if self.refreshed:
            rows.append(f"  derived  {', '.join(self.refreshed)} (dep annotations re-derived)")
        follow = self.requeue(config)
        if follow is not None:
            rows.append(f"  requeue  {follow}")
        rows += _staging_rows(config.relative(one) for one in wrote)
        rows += _event_rows(self.event(config), "  ", config=config)
        return "\n".join(rows)

    def payload(self, config: Config, wrote: Sequence[Path]) -> dict[str, object]:
        """The same answer as data, saying which of the two acts it was (RK1083)."""
        from roadkeep.rendering import _wrote_json  # noqa: PLC0415 - RK260

        return {
            "id": self.task_id,
            "marker": self.marker,
            # Null on a reconciling call, which places no line — a `line` there would be an
            # address for a write nobody made (RK1086).
            "roadmap": None
            if self.placed is None
            else {
                "file": config.relative(config.path("roadmap")),
                "line": self.placed.lineno,
                "rendered": self.placed.raw,
            },
            "deferred": {
                "file": config.relative(config.path("deferred")),
                "removed": self.removed_from,
            },
            "was": self.was,
            # Which of the two acts this was (RK1083): a reconciliation removes the store's
            # stale copy and places nothing, so `roadmap.line` is where the line already was
            # rather than where one landed.
            "reconciled": self.reconciled,
            "refreshed": list(self.refreshed),
            # The half of the pause this does not undo (RK327): the entry the pause removed is
            # the author's to put back, because where in the order it belonged is not a fact
            # the store kept.
            "requeue": self.requeue(config),
            **_wrote_json(config, wrote),
            "event": self.event(config),
        }


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
            Whereabouts.of(config, task_id),
        )
    _refuse_recorded(config, task_id)
    store = config.document("deferred")
    held = store.by_id().get(task_id)
    if held is not None:
        raise SetAside(task_id, config.relative(config.path("deferred")), held.lineno)

    marker = config.schema.deferred_marker
    insertion = place(
        store,
        _as_paused(entry.task, marker, reason),
        role="deferred",
        config=config,
    )
    remaining = remove_entry(roadmap, entry)
    # And the queue entry, in the same rewrite (RK327). Worth naming apart from the two
    # terminal doors: the line is still work, so an entry naming it reads as live — and yet
    # `pick` can never offer a line the store holds, so the tier could only fire on nothing.
    remaining, dequeued = queueing.without(remaining, config, task_id)
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
        dequeued=dequeued,
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
        raise NotSetAside(task_id, where, elsewhere=Whereabouts.of(config, task_id).sentence)
    _refuse_recorded(config, task_id)

    backlog = Backlog.load(config)
    open_line = backlog.roadmap.by_id().get(task_id)
    if open_line is not None:
        if marker is not None:
            raise NoPlacement(
                task_id, config.relative(config.path("roadmap")), open_line.lineno
            )
        # The roadmap already says what a resume would write, so the store entry is the
        # stale half and this call removes it (RK1081). The mirror of RK1075 one file over:
        # two governed files disagreeing about one id, resolved towards the one that
        # already states the outcome — here the open line, there the ledger entry.
        #
        # Refusing was the earlier answer and it left the state with no verb at all: `defer`
        # refuses because the store holds it, `ship` and `retire` *succeed* and leave the id
        # recorded and still paused, and the gate said nothing. What a second line would be
        # — two answers to when the work comes back — is what this prevents rather than
        # what it creates, because no line is placed.
        remaining = remove_entry(store, held)
        derived = refresh(replace(backlog, store=remaining))
        return Resumption(
            task_id=task_id,
            roadmap=derived.document,
            placed=None,
            store=remaining,
            removed_from=held.lineno,
            refreshed=tuple(name for name in derived.changed if name != task_id),
            # The line's own, because no marker was chosen here: what this call did is
            # remove a copy, and reporting a marker it did not write would be the
            # placement the sentence above refuses to claim.
            marker=open_line.task.status,
            reconciled=True,
        )

    status = marker or config.schema.markers[0]
    insertion = place(
        backlog.roadmap,
        _as_open(held.task, status),
        role="roadmap",
        config=config,
    )
    remaining = remove_entry(store, held)
    # The store this write leaves behind, for `defer`'s reason read backwards: a dependent
    # still annotated ⏸ after the pause ended is the stale cache RK8 exists to prevent.
    derived = refresh(replace(backlog, roadmap=insertion.document, store=remaining))
    returned = next(e for e in derived.document.entries if e.task.id == task_id)
    return Resumption(
        task_id=task_id,
        roadmap=derived.document,
        placed=returned,
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


#: The reason a pause recorded, and the author's sentence without it. Both moved to the kernel
#: by RK1115, where the rule that measures a paused `why` reads them too — named here because
#: this module is where the wrapping is composed, and a reader of `defer` looks for them here.
_reason = pause_reason
_unwrapped = authored_why


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


