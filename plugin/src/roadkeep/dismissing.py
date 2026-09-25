"""What was traced and deliberately not filed, as a record (RK1618).

`delivered` states what a block shipped and `reversals` what it undid, and both are named as
the read before an `add`. Neither answers the third question a proposal meets: **was this
looked at already and left?** A repository that cannot say so re-traces it, and the tracing is
the whole cost — pportal keeps twenty-five such findings in a per-user memory directory outside
its git, so a second machine, agent or person pays it again.

A free-prose reason cannot carry it. *Checked, fine* is unfalsifiable and gets re-traced; what
makes one durable is the **premise** it names, because that is what a later commit breaks. So
the entry is a subject, a reason, and a premise the entry holds while — and the premise is
required, this being the field the whole role exists for.

It is none of the three doors that were there. `retire` is for a line that was filed, `defer`
for work still waiting, `reversals` for a decision undone — and not the decisions file either:
a decision is a constraint the project chose and a dismissal a finding it ruled out, and one
list holding both makes *we decided X* and *we checked Y* one kind of sentence.

**On the deferred store's shape** (RK96), with the two differences the record forces:

* **The entry is composed, not moved.** A pause takes an open line out of the roadmap; this
  files something that was never a line, so :func:`dismiss` mints an id the way `add` does. It
  is an id and not a heading-and-a-bullet because :func:`reopen` has to address one, and
  because an id the derivation could hand out twice would put a dismissal and a task at one
  address — which is RK4's rule and the one thing this store may not break.
* **The premise is the derived half.** `defer` wraps the *reason* around the design the line
  carries forward; here both fields are new, so what is wrapped is the premise — the claim a
  commit falsifies — and the author's sentence is the reason underneath it. :func:`reopen`
  unwraps exactly what this module wrote, and the prefix ends at the first ``): ``, so a
  premise that spells that sequence is refused rather than stored.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from pathlib import Path

from roadkeep.authoring import (
    Insertion,
    Rationale,
    _unopened,
    _unresolved,
    _with_section,
    follow_ups,
    owed_rows,
    place,
    prose_role,
    remove_entry,
)
from roadkeep.backlog import Backlog, Whereabouts
from roadkeep.config import Config, role_door
from roadkeep.ids import Derivation, Promise, derivation
from roadkeep.kernel.document import Document, Entry, save_all
from roadkeep.markers import refresh
from roadkeep.provenance import invocation
from roadkeep.sections import Section
from roadkeep.kernel.schema import (
    DISMISSED_CLOSE,
    DISMISSED_OPEN,
    SchemaError,
    Task,
    authored_why,
    dismissal_premise,
)

__all__ = [
    "Dismissal",
    "NoStore",
    "NotDismissed",
    "Reopening",
    "UnrecoverablePremise",
    "dismiss",
    "reopen",
]

_OPEN = DISMISSED_OPEN
_CLOSE = DISMISSED_CLOSE


class NoStore(ValueError):
    """A dismissal with nowhere to go: this project declares no dismissed file (RK1618).

    Refused and not scaffolded on the way past, which is :class:`~roadkeep.deferring.NoStore`'s
    rule and its reason: a governed file is a path in `roadkeep.toml` (L6), and a store a
    `dismiss` invented at the moment it needed one would be a format decided by a verb.

    It names the verb that opens one, because that verb exists (RK1264): the remedy this
    refusal would otherwise read out is a toml key and a skeleton by hand, which over MCP is
    the hand edit the guard denies and so no remedy at all.
    """

    def __init__(self, what: str) -> None:
        super().__init__(
            f"{what}: this project declares no dismissed store — "
            f"{role_door('dismissed')} together, and a finding worth recording is worth a "
            f"store that outlives the session that traced it"
        )


class AlreadyDismissed(ValueError):
    """The store already holds this id, so there is nothing here to file."""

    def __init__(self, task_id: str, where: str, lineno: int) -> None:
        self.task_id = task_id
        self.lineno = lineno
        super().__init__(
            f"{task_id} is already in {where}:{lineno}: a second entry would be two "
            f"premises for one finding, and nothing says which one still holds"
        )


class NotDismissed(KeyError):
    """`reopen` against an id the store does not hold.

    Names where it *is*, for :class:`~roadkeep.deferring.NotSetAside`'s reason: "not in the
    store" is the same sentence for an id that is open, one that shipped and one that never
    existed, and only the last is a typo.
    """

    def __init__(self, task_id: str, where: str, *, elsewhere: str = "") -> None:
        self.task_id = task_id
        found = f" ({elsewhere})" if elsewhere else ""
        super().__init__(
            f"{task_id} is not in {where}{found}: reopen files work the store ruled out, "
            f"and a finding nobody dismissed has nothing to come back from"
        )


class UnrecoverablePremise(ValueError):
    """A premise spelling the sequence that ends the derived prefix.

    Refused at input rather than stored, because the damage is invisible until the reopen: the
    unwrap stops at the first ``): ``, so the author's own reason would come back with the tail
    of the premise glued to its front — and `lint` cannot see a `why` that is merely wrong.
    """

    def __init__(self, premise: str) -> None:
        super().__init__(
            f"the premise may not contain {_CLOSE!r}: it is what closes the derived prefix, "
            f"and reopen would restore a sentence the dismissal rewrote — {premise!r}"
        )


class NoPlacement(ValueError):
    """`--marker` on a reopen that places no line (RK1083's rule, one store over).

    The reconciling path removes the store's stale copy and leaves the roadmap alone, so the
    open marker a filed line would arrive at has nothing to be about. Refused rather than
    ignored: a flag accepted where it can take no effect is a flag the caller believes took one.

    Both steps and in order, which is what makes the sentence runnable: `status` will not write
    a marker for an id the store still holds, status living in exactly one file, so the removal
    this call was going to make has to come first.
    """

    def __init__(self, task_id: str, where: str, lineno: int) -> None:
        self.task_id = task_id
        super().__init__(
            f"--marker names the marker a filed line arrives at, and this call places none: "
            f"{task_id} is already open at {where}:{lineno} and only the store's copy would "
            f"go — `{invocation()} reopen {task_id}` without the flag removes it, and "
            f"`{invocation()} status {task_id} <marker>` then writes the marker of a line "
            f"that is already there"
        )


class NoSectionHere(ValueError):
    """`--section` on a reopen that places no line (RK1655), which is `NoPlacement`'s rule.

    The reconciling path removes the store's stale copy and leaves the roadmap alone, so there
    is no pointer of this call's to answer. The open line has a design or owes one either way,
    and writing it is `section add`'s — addressed to the anchor that line already carries.
    """

    def __init__(self, task_id: str, where: str, lineno: int) -> None:
        self.task_id = task_id
        super().__init__(
            f"--section writes the design the line this call files would point at, and this "
            f"call files none: {task_id} is already open at {where}:{lineno} and only the "
            f"store's copy would go — `{invocation()} section add {task_id} --title …` writes "
            f"a design for the line that is already there"
        )


@dataclass(frozen=True, slots=True)
class Dismissal:
    """Everything filing one finding writes, as data, before it is written."""

    task_id: str
    #: The entry as the store now holds it: 🚫, the subject, and the premise around the reason.
    store: Insertion
    marker: str = ""
    #: The premise this entry holds while — echoed back because it is the field the record
    #: exists for, and the one an author has just been refused over if it was missing.
    premise: str = ""
    #: The id a sentence promised that deriving this one stepped over (RK431), where the id
    #: was derived. Carried for `add`'s reason exactly: a promise nothing states is an address
    #: somebody wrote down and nothing will ever occupy.
    promise: Promise | None = None

    def save(self) -> tuple[Path, ...]:
        """One file, which is the whole difference from a pause: nothing was moved."""
        return save_all(self.store.document)

    @property
    def block(self) -> str:
        return self.store.entry.task.block

    def stated(self, config: Config, wrote: Sequence[Path]) -> str:
        from roadkeep.rendering import _staging_rows  # noqa: PLC0415 - RK260

        from roadkeep.kernel.schema import width  # noqa: PLC0415 - RK260

        store = config.relative(config.path("dismissed"))
        schema = config.schema_for("dismissed")
        rows = [
            f"{self.task_id} {self.marker} {store}:{self.store.lineno} "
            f"under Block {self.block}",
            f"  holds    while {self.premise}",
            # The figure and never the rule, which is `defer`'s own arrangement (RK1583): the
            # premise is derived, so `[limits] why` is not what bounds it and the caller who
            # declared that number would otherwise learn the answer by inference.
            f"  line     {width(schema.render(self.store.entry.task))} of {schema.line_max}"
            f"  the rendered line, which is what bounds a premise",
            # Named on every dismissal, because it is the one thing this record is *not*: no
            # id is spent on work, no block gains a line, and a reader who thinks otherwise
            # will go looking in the roadmap for something that was never filed there.
            f"  reopen   `{invocation()} reopen {self.task_id}` if the premise breaks",
        ]
        rows += _staging_rows(config.relative(one) for one in wrote)
        return "\n".join(rows)

    def payload(self, config: Config, wrote: Sequence[Path]) -> dict[str, object]:
        from roadkeep.kernel.schema import width  # noqa: PLC0415 - RK260
        from roadkeep.rendering import _promise_json, _wrote_json  # noqa: PLC0415 - RK260

        schema = config.schema_for("dismissed")
        return {
            "id": self.task_id,
            "marker": self.marker,
            "block": self.block,
            "premise": self.premise,
            "dismissed": {
                "file": config.relative(config.path("dismissed")),
                "line": self.store.lineno,
                "rendered": self.store.rendered,
                "characters": width(schema.render(self.store.entry.task)),
                "limit": schema.line_max,
            },
            "promise": _promise_json(self.promise),
            **_wrote_json(config, wrote),
        }


@dataclass(frozen=True, slots=True)
class Reopening:
    """The finding filed as work: the roadmap gains the line, the store lets it go."""

    task_id: str
    #: The roadmap as this write leaves it — a document and not an `Insertion`, for
    #: :class:`~roadkeep.deferring.Resumption`'s reason: the reconciling call places nothing.
    roadmap: Document
    #: The line this call filed, or `None` where it placed none.
    placed: Entry | None
    store: Document
    removed_from: int
    refreshed: tuple[str, ...] = ()
    marker: str = ""
    #: The premise the dismissal held while, reported once — the last place it is visible,
    #: because what arrives in the roadmap is work and not the history of a decision.
    was: str | None = None
    #: Whether this call **reconciled** a contradiction rather than filing work: the roadmap
    #: already carried the id, so the store entry was the stale half and only it was removed.
    reconciled: bool = False
    #: The prose file as this write leaves it and the section it gained, both `None` unless
    #: `--section` was passed (RK1655) — `Insertion`'s own pair, carried here because the
    #: transaction is the same one: a line whose pointer answers, or neither.
    prose: Document | None = None
    section: Section | None = None
    #: The anchor nothing answers, where no section was written — and the prose role it would
    #: be written in. `Insertion.needs`' pair exactly: a dismissal carries no design, so every
    #: `reopen` without a section leaves a pointer the gate reports, and the write that made it
    #: is where a caller reads about it rather than one run later (RK420's rule at this door).
    needs: str | None = None
    needs_role: str | None = None
    #: The address one level up, where the family the anchor sits in is not open yet.
    opens: str | None = None

    def save(self) -> tuple[Path, ...]:
        # The roadmap first and the store's removal second, which is `resume`'s order and its
        # reason (RK118): a line in both files is a state a reader can see and a second
        # `reopen` can finish, and a line in neither is one nobody can.
        #
        # The prose **first of all** where there is any (RK1655), which is `Insertion.save`'s
        # own order: a section written whose line never landed is a paragraph somebody deletes,
        # and a line pointing at a section that was not written is the dangling pointer this
        # flag exists to close.
        if self.prose is not None:
            return save_all(self.prose, self.roadmap, self.store)
        return save_all(self.roadmap, self.store)

    def standing(self, config: Config) -> Entry | None:
        return self.placed or config.document("roadmap").by_id().get(self.task_id)

    def event(self, config: Config) -> dict[str, object]:
        from roadkeep.rendering import _event  # noqa: PLC0415 - RK260

        standing = self.standing(config)
        block = standing.task.block if standing else ""
        return _event(self.task_id, block, self.roadmap, config)

    def stated(self, config: Config, wrote: Sequence[Path]) -> str:
        from roadkeep.rendering import (  # noqa: PLC0415 - RK260
            _event_rows,
            _staging_rows,
        )

        roadmap = config.relative(config.path("roadmap"))
        store = config.relative(config.path("dismissed"))
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
        # The design, or the pointer that owes one (RK1655), in `add`'s own two spellings and
        # above the premise: what the caller does next is write the section, and the premise is
        # the last place a decision's history is visible rather than something to act on.
        if self.section is not None:
            rows.append(
                f"  design   §{self.section.anchor} → "
                f"{config.relative(config.path(prose_role(config) or 'improvements'))}:"
                f"{self.section.first}  {self.section.words} words"
            )
        elif self.needs is not None:
            rows += owed_rows(self.needs, follow_ups(self.needs, self.needs_role, self.opens))
            # The flag that would have needed none of them, which is RK1218's row at this
            # door: a dismissal carries no design by definition, so **every** reopen without
            # this flag leaves a pointer the gate reports — the one write here where the
            # two-command path is the default rather than the omission.
            rows.append(
                '  or       pass `--section "<its title>"` to `reopen` next time: both halves '
                "in one transaction, under the same limits"
            )
        if self.was is not None:
            rows.append(f"  was      ruled out while {self.was}")
        if self.refreshed:
            rows.append(f"  derived  {', '.join(self.refreshed)} (dep annotations re-derived)")
        rows += _staging_rows(config.relative(one) for one in wrote)
        rows += _event_rows(self.event(config), "  ")
        return "\n".join(rows)

    def payload(self, config: Config, wrote: Sequence[Path]) -> dict[str, object]:
        from roadkeep.rendering import _wrote_json  # noqa: PLC0415 - RK260

        return {
            "id": self.task_id,
            "marker": self.marker,
            "roadmap": None
            if self.placed is None
            else {
                "file": config.relative(config.path("roadmap")),
                "line": self.placed.lineno,
                "rendered": self.placed.raw,
            },
            "dismissed": {
                "file": config.relative(config.path("dismissed")),
                "removed": self.removed_from,
            },
            "was": self.was,
            "reconciled": self.reconciled,
            "refreshed": list(self.refreshed),
            # The design or the pointer owing one, as fields (RK1655): the plain register's
            # rows are prose and a consumer reading this payload had no way to tell a reopen
            # that closed its own pointer from one that left `ref.unresolved` behind.
            "section": None
            if self.section is None
            else {
                "anchor": self.section.anchor,
                "line": self.section.first,
                "words": self.section.words,
            },
            # `absent` and never a null pair, which is `rendering._reading_door`'s rule for a
            # door: a consumer reading the key at all is one that acts on it.
            **(
                {}
                if self.needs is None
                else {
                    "needs": self.needs,
                    "doors": [
                        {"argv": one.split(), "what": "the design this pointer resolves to"}
                        for one in follow_ups(self.needs, self.needs_role, self.opens)
                    ],
                }
            ),
            **_wrote_json(config, wrote),
            "event": self.event(config),
        }


def dismiss(
    config: Config,
    *,
    block: str,
    symptom: str,
    reason: str,
    premise: str,
    task_id: str | None = None,
    family: str | None = None,
) -> Dismissal:
    """File one finding that was traced and deliberately not filed. Validates before writing.

    The premise is **required** and refused empty, which is the whole rule: an entry without
    one is the unfalsifiable note this store replaces, and a store of them costs the re-trace
    it exists to save. Held here as well as by the gate for L1's reason — the refusal has to
    arrive before a reason is composed to fill it.
    """
    if not config.has("dismissed"):
        raise NoStore(f"{symptom!r} cannot be dismissed")
    if _CLOSE in premise:
        raise UnrecoverablePremise(premise)
    store = config.document("dismissed")
    derived: Derivation | None = None
    if task_id is None:
        derived = derivation(config, family)
        task_id = derived.id
    held = store.by_id().get(task_id)
    if held is not None:
        raise AlreadyDismissed(
            task_id, config.relative(config.path("dismissed")), held.lineno
        )
    marker = config.schema.dismissed_marker
    entry = Task(
        id=task_id,
        status=marker,
        block=block,
        symptom=symptom,
        why=f"{_OPEN}{premise}{_CLOSE}{reason}",
    )
    # Under the store's own grammar and not the project's shared one (RK1479's rule at this
    # door): the wrapper widens the rendered line, so a premise that pushed it past
    # `[limits.dismissed]` would land as a line the gate then refuses — which is L1 unapplied
    # to the one write that composes prose here.
    over = [
        one
        for one in config.schema_for("dismissed").validate(entry)
        if one.code == "line.too-long"
    ]
    if over:
        raise SchemaError(tuple(over))
    insertion = place(store, entry, role="dismissed", config=config)
    return Dismissal(
        task_id=task_id,
        store=insertion,
        marker=marker,
        premise=premise,
        promise=derived.promise if derived is not None else None,
    )


def reopen(
    config: Config,
    task_id: str,
    *,
    marker: str | None = None,
    ref: str | None = None,
    section: Rationale | None = None,
) -> Reopening:
    """File a ruled-out finding as work. The premise broke, so the entry stops holding.

    `marker` is the open one the line arrives at, defaulting to the project's first exactly as
    `add`'s does: the store holds 🚫 and nothing else, so which kind of work this is was never
    a fact any file had.

    `ref` is the anchor, on a project whose pointers are addresses rather than ids. Nothing
    derives one here — the dismissal carries no design, that being what a dismissal *is* — so
    under `ref_scheme = "outline"` the line would be refused for a pointer no verb could
    supply, and the store would hold an entry with no door out.

    ``section`` is that absence closed in the same transaction (RK1655), and it is `add`'s
    flag by the same reader: a dismissal carries no design, so the line this filed pointed at
    `§<id>` and **nothing answered it** — `ref.unresolved` on every reopen this tool would ever
    perform, arriving one run later as the file's problem rather than at the door that made it.
    Where none is passed the anchor is reported instead, which is `Insertion.needs` and already
    the shape every door that leaves a pointer owing uses. The prose stays the author's (L4).
    """
    if not config.has("dismissed"):
        raise NoStore(f"{task_id} cannot be reopened")

    where = config.relative(config.path("dismissed"))
    store = config.document("dismissed")
    held = store.by_id().get(task_id)
    if held is None:
        raise NotDismissed(task_id, where, elsewhere=Whereabouts.of(config, task_id).sentence)

    backlog = Backlog.load(config)
    open_line = backlog.roadmap.by_id().get(task_id)
    if open_line is not None:
        if marker is not None:
            raise NoPlacement(
                task_id, config.relative(config.path("roadmap")), open_line.lineno
            )
        if section is not None:
            # `NoPlacement`'s rule for the other flag (RK1655): this call places no line, so
            # there is no pointer of its own for a section to answer — and the open line's
            # design is `section add`'s, that line having been filed by something else.
            raise NoSectionHere(
                task_id, config.relative(config.path("roadmap")), open_line.lineno
            )
        # The roadmap already says what a reopen would write, so the store entry is the stale
        # half and this call removes it (RK1081's resolution, one store over): two governed
        # files disagreeing about one id, settled towards the one that states the outcome.
        remaining = remove_entry(store, held)
        refreshed = refresh(replace(backlog, dismissals=remaining))
        return Reopening(
            task_id=task_id,
            roadmap=refreshed.document,
            placed=None,
            store=remaining,
            removed_from=held.lineno,
            refreshed=tuple(name for name in refreshed.changed if name != task_id),
            marker=open_line.task.status,
            reconciled=True,
        )

    status = marker or config.schema.markers[0]
    insertion = place(
        backlog.roadmap,
        _as_open(held.task, status, config, ref),
        role="roadmap",
        config=config,
    )
    # After the roadmap's own refusal, which is `add`'s order and its reason (RK380, RK381):
    # every refusal the prose file has — the word budget, an undeclared block, an anchor
    # already taken — arrives before either file is written, so a run that filed the line and
    # then refused the section cannot leave the dangling pointer this closes.
    owing: dict[str, str | None] = {}
    if section is not None:
        insertion = _with_section(config, insertion, *section)
    elif insertion.entry.task.ref and (
        role := _unresolved(config, insertion.entry.task.ref)
    ):
        owing = {
            "needs": insertion.entry.task.ref,
            "needs_role": role,
            "opens": _unopened(config, role, insertion.entry.task.ref),
        }
    remaining = remove_entry(store, held)
    refreshed = refresh(
        replace(backlog, roadmap=insertion.document, dismissals=remaining)
    )
    filed = next(e for e in refreshed.document.entries if e.task.id == task_id)
    return Reopening(
        task_id=task_id,
        roadmap=refreshed.document,
        placed=filed,
        store=remaining,
        removed_from=held.lineno,
        refreshed=tuple(name for name in refreshed.changed if name != task_id),
        marker=status,
        was=dismissal_premise(held.task.why),
        prose=insertion.prose,
        section=insertion.section,
        **owing,
    )


def _as_open(task: Task, marker: str, config: Config, ref: str | None) -> Task:
    """The entry as a roadmap line: the marker chosen, the premise taken back off.

    The pointer is **derived where the scheme derives one** and the caller's otherwise, which
    is `add`'s rule and not a second one: what comes back is a line with no design written yet,
    exactly as a fresh `add` leaves one, and the section it owes is named by the gate in the
    words every un-answered pointer gets.
    """
    return replace(
        task,
        status=marker,
        why=authored_why(task.why),
        ref=task.id if config.schema.ref_scheme == "id" else ref,
        # At column zero, for `ship`'s reason (RK49): an indent names a line this one is nested
        # under, and the store holds no such line.
        indent="",
    )
