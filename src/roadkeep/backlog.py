"""Resolving a dep against the backlog it names (RK28).

A dep is a claim about other work, and there are five different answers to "is it
done?" — shipped, still open, *set aside*, no such task, and *unanswerable*. Collapsing
the last one into "still open" is what makes a permanently blocked task read like the next
one to start, which is the whole reason this module exists rather than a boolean.

The fifth is the same honesty one state further in (RK92). A deferred dep is none of the
other four: not shipped, not open — the store is not the roadmap — not unknown, since it
is recorded and findable, and not unresolvable, which is `retire`'s "never" and a pause
can end. Read as open, a task is offered whose blocker nobody is working; read as
unresolvable, a task is buried that unblocks the moment the dep resumes. So it is
:attr:`DepStatus.DEFERRED`, and the task waiting on it is
:attr:`Readiness.PAUSED` — blocked for now, which is neither of the two blocked already
told apart.

The interesting case is the one the corpora already write. Shio has `(deps: Block P)`
and Turing has `(deps: real design partners)`: real work does wait on a whole block,
and on things that are not tracked work at all. So:

* a **task** dep resolves against the roadmap and the ledger;
* a **block** dep resolves against that block's :class:`Stage` and against nothing else
  (RK432). "Nothing open" was two states and only one of them means waiting is over: a
  heading `block add` wrote before its first line resolved as done, so a task waiting on
  work nobody had filed was offered as ready. What makes a block finished is the ledger
  filing something under the label, never the heading — which every organised file gets at
  declaration time. `empty` and `unknown` are one answer about the *dep* and two facts
  about the *label*, and :attr:`Standing.sentence` is what says which;
* an **external** dep is :attr:`DepStatus.UNRESOLVABLE` forever, and a task carrying
  one is never *ready*, it is blocked outside the backlog. Naming that is the
  difference between an answer and a guess.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from roadkeep.config import Config
from roadkeep.kernel.document import Document, Entry
from roadkeep.kernel.schema import Dep, DepKind, Schema, Task


class NotOpen(ValueError):
    """Only an open task can be written to, and the two ways of not being one differ.

    Lives here rather than in the command that first needed it (RK6) because "is this
    id open?" is a question about the roadmap and the ledger together, and reporting
    "no such task" for one that shipped yesterday sends the reader to the wrong file.
    """

    def __init__(self, task_id: str, where: str, shipped: bool) -> None:
        self.task_id = task_id
        self.shipped = shipped
        detail = (
            "it is already in the changelog"
            if shipped
            else "nothing there carries that id"
        )
        super().__init__(f"no open task {task_id} in {where}: {detail}")


class Where(StrEnum):
    """Which absence an id is (RK240) — the question three refusals ask after "not here".

    Not a readiness and not a dep status: those rank work, and this only says where to
    look. The three are told apart because only the last one is a typo — an id that
    shipped, one that was abandoned and one nobody ever wrote are three different next
    actions, and a refusal that says "no such task" for all three sends two of the three
    authors to search a file that is right.
    """

    #: The roadmap carries it as an open line.
    OPEN = "open"
    #: The ledger carries it, shipped or retired — :attr:`Whereabouts.marker` says which.
    RECORDED = "recorded"
    NOWHERE = "nowhere"


@dataclass(frozen=True, slots=True)
class Whereabouts:
    """Where an id actually is, in one type and one sentence (RK240).

    Two modules composed this independently and in the same words — `deferring` for
    `resume`'s :class:`~roadkeep.deferring.NotSetAside`, `sections` for `anchor.unknown` —
    which is a resolution copied rather than called: the copy is what goes stale when the
    other is corrected. It lives here because the fact is about an **id**, and this module
    is where an id's state is already read from every file that can hold one.

    A type rather than the string both callers printed, because one of them *acts* on the
    state: `sections._unknown` offers `record amend` only for an id the ledger holds, and
    deciding that from the truthiness of a sentence is a branch that reads prose. So the
    marker is carried, :attr:`sentence` is the one spelling, and the door is chosen from
    :attr:`Where`.
    """

    where: Where
    #: The ledger's marker where it holds the id — ✅ or 🗑 — and empty otherwise.
    marker: str = ""

    @classmethod
    def of(cls, config: Config, task_id: str) -> Whereabouts:
        """Read the files, roadmap first, and the ledger only where it can still answer.

        The order is the answer's own: an id open in the roadmap is not looked for in a
        ledger of finished work, and a project that declares no changelog has two states
        rather than three.
        """
        if config.document("roadmap").by_id().get(task_id) is not None:
            return cls(Where.OPEN)
        if config.has("changelog") and config.path("changelog").is_file():
            recorded = config.document("changelog").by_id().get(task_id)
            if recorded is not None:
                return cls(Where.RECORDED, recorded.task.status)
        return cls(Where.NOWHERE)

    @property
    def recorded(self) -> bool:
        return self.where is Where.RECORDED

    @property
    def sentence(self) -> str:
        """The clause a refusal appends after naming where the id is not."""
        if self.where is Where.OPEN:
            return "it is open in the roadmap"
        if self.where is Where.RECORDED:
            return f"the changelog records it as {self.marker}"
        return "no file mentions it"


class Stage(StrEnum):
    """Which state a **block** is in (RK429) — :class:`Where` for a label.

    A block is discovered and never registered, so "nothing open in Block C" was the one
    answer four different facts produced: the work is done, its lines were all set aside,
    the heading was opened before any line, or the letter is a typo. One sentence for four
    states, and only the last is a mistake — which is why a query that collapses them sends
    three of the four readers to grep the ledger this tool exists to replace.

    The discriminator between `finished` and `empty` is **entries under the label** and
    never the heading: `block add` writes the heading into every organised file at
    declaration time, so a heading proves the label was declared and nothing more. The
    gate made that choice first, for a queue token (`priority.block-empty` against
    `priority.block-unstarted`), and reads it from here since RK434 —
    :func:`~roadkeep.linting._dead_block` maps a stage to a code and a tier, and decides no
    state of its own.

    :attr:`PAUSED` is here for the reason :attr:`Readiness.PAUSED` is (RK92): a block
    whose every line was deferred is not finished and not empty, and reading it as either
    loses the one fact about it that a `resume` would change.
    """

    #: The roadmap carries open lines under it. Nothing here is about them.
    LIVE = "live"
    #: Nothing open, and the ledger records entries filed under the label. Not "shipped":
    #: a retirement is filed there too, and the ledger having the last word is the claim.
    FINISHED = "finished"
    #: Nothing open, and the deferred store holds lines under it. Checked before the
    #: ledger, because a block that shipped half its work and set the rest aside has work.
    PAUSED = "paused"
    #: Declared, and no file files a task line under it — a heading before its lines.
    EMPTY = "empty"
    #: No heading in the roadmap or the ledger. The only one that is a typo, and the same
    #: oracle every other refusal about a label uses, so the four answers cannot disagree.
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class Standing:
    """What became of a block, in one type and one sentence (RK429).

    The block analogue of :class:`Whereabouts`, and here for its reason: the fact is about
    a label, and this module is already where a label is read from every file that can
    declare one. Not :class:`~roadkeep.blocking.Standing`, which is what one heading stands
    over inside one file.

    :attr:`sentence` is the one spelling, so `brief`, `pick` and `list` answer a finished
    block in the same words; callers that *act* on the state branch on :attr:`stage`, never
    on the prose — a `list` that read the sentence to decide its exit code would be the
    second reader of a rule this states once.

    **Every count is taken whatever the state is.** An early return would make `recorded`
    read 0 for a live block the ledger files thirty entries under, and a payload whose
    fields are only true in the branch that needed them is one a caller reads wrongly
    exactly once.
    """

    #: The label as the caller typed it, for a payload that has to name what was asked.
    label: str
    stage: Stage
    #: The label as this project spells one — `Block C`, or whatever `heading_word` says.
    named: str
    #: Open lines the roadmap files under it.
    open: int = 0
    #: Entries the ledger files under it — shipped **and** retired, which is what a ledger
    #: records. The count is the evidence for `finished`, so it is carried and not recomputed.
    recorded: int = 0
    #: Lines the deferred store holds under it (RK92) — the work a `resume` brings back.
    paused: int = 0

    @classmethod
    def of(cls, backlog: Backlog, label: str) -> Standing:
        """Read every file that can file a line under a label, and rank what they say.

        The order is the answer's own: open work outranks paused work, which outranks a
        ledger, because each of those is a reason the one below it is not the whole story.
        A block that shipped nine lines and deferred the tenth is not finished.
        """
        named = backlog.config.schema.block_named(label)
        if label not in backlog.declared_blocks():
            return cls(label, Stage.UNKNOWN, named)
        counts = {
            "open": len(backlog.open_in_block(label)),
            "recorded": 0 if backlog.ledger is None else len(backlog.ledger.block(label)),
            "paused": 0 if backlog.store is None else len(backlog.store.block(label)),
        }
        if counts["open"]:
            stage = Stage.LIVE
        elif counts["paused"]:
            stage = Stage.PAUSED
        elif counts["recorded"]:
            stage = Stage.FINISHED
        else:
            stage = Stage.EMPTY
        return cls(label, stage, named, **counts)

    @property
    def settled(self) -> bool:
        """Whether this is one of the states an empty answer needs explaining by.

        `live` is not: a listing that came back empty under a live block was emptied by
        the filter, and a sentence about the block would answer a question nobody asked.
        Neither is `unknown`, which every surface already refuses in its own words.
        """
        return self.stage in (Stage.FINISHED, Stage.PAUSED, Stage.EMPTY)

    @property
    def sentence(self) -> str:
        """What to print where "nothing is open in Block C" used to be the whole answer."""
        if self.stage is Stage.LIVE:
            return f"{self.named} has {self.open} open"
        if self.stage is Stage.FINISHED:
            return (
                f"{self.named} is finished: nothing open, and the ledger records "
                f"{self.recorded} filed under it"
            )
        if self.stage is Stage.PAUSED:
            return (
                f"{self.named} has nothing open: {self.paused} set aside, which a "
                f"resume brings back"
            )
        if self.stage is Stage.EMPTY:
            # "No task line" and not "nothing has ever been filed": a marker-bearing line
            # the parser rejected sits under the heading and is reported by `audit`, and an
            # absolute claim here would contradict the note printed on the next line.
            return f"{self.named} is empty: the heading is declared and no task line is filed under it"
        return f"no heading declares {self.named}"

    def payload(self) -> dict[str, object]:
        """What became of the block a query was scoped to (RK429).

        The counts ride with the state because they are its evidence: `finished` is a claim about
        the ledger, and a payload asserting it without saying how many entries it read is one a
        caller has to verify with a second command.

        Here since RK1170, with `delivered`: four payloads publish this record, and a builder in
        `rendering.py` was the fifth place the fact was spelled — where one of its keys had
        quietly been written twice.
        """
        return {
            "block": self.label,
            "state": str(self.stage),
            "sentence": self.sentence,
            "open": self.open,
            "recorded": self.recorded,
            "paused": self.paused,
        }


class DepStatus(StrEnum):
    """How a single dep resolved."""

    SHIPPED = "shipped"
    OPEN = "open"
    #: Held in the deferred store (RK92). Recorded, so not unknown; revivable, so not
    #: unresolvable; and not in the roadmap, so not open — the state `retire` has no
    #: door for and `resume` is the way out of.
    DEFERRED = "deferred"
    #: An id of this project that exists in neither file. A lint error (RK8), not a
    #: rendering choice: nothing downstream can tell whether it is done.
    UNKNOWN = "unknown"
    #: Nothing the roadmap now holds open will satisfy it (RK432). Three things are that:
    #: an external dep, by construction; a retired task, by decision; and a label with
    #: nothing filed under it, because there is no line to ship. Widened from "outside the
    #: backlog" when the third joined — a heading with no lines is declared *inside* the
    #: backlog, and what lifts the dependent is a first `add` under the label rather than
    #: a `ship` of anything now open.
    UNRESOLVABLE = "unresolvable"


class Readiness(StrEnum):
    """Whether a task can be started, and if not, in which of four senses."""

    READY = "ready"
    BLOCKED = "blocked"
    #: Blocked by something that is not an open line, so no `ship` of anything the roadmap
    #: now holds lifts it — what does is a `retire`, an `amend --dep`, or a first `add`
    #: under a label declared before its lines (RK432). `pick` (RK11) must not offer these
    #: as next work.
    OUTSIDE = "blocked-outside"
    #: Blocked on work somebody set aside (RK92). Not offered either — nobody is working
    #: the blocker — but unlike :attr:`OUTSIDE` the block lifts on a `resume`, so what has
    #: to change is a decision and not this line.
    PAUSED = "blocked-paused"
    #: Not startable because it is **done** (RK324) — the ledger's answer, never
    #: :meth:`Backlog.readiness`'s, which is asked only about lines the roadmap still holds.
    #: A fifth state rather than a reading of `ready`: every other value here says work
    #: remains, so a shipped id described with one of them is an invitation to redo it.
    SHIPPED = "shipped"


#: Which :class:`DepStatus` each *settled* :class:`Stage` is (RK432) — the whole of what a
#: block dep resolves to. A table and not four branches, because the resolver had grown its
#: own copy of the walk :meth:`Standing.of` already makes, and a mapping is what a test can
#: check for totality. :attr:`Stage.LIVE` is absent on purpose: it is the one stage whose
#: detail is not the standing's sentence, so :meth:`Backlog._resolve_block` answers it.
#:
#: `empty` and `unknown` share an answer because the question a status settles is whether
#: waiting is over, and under neither label is there work to wait for. Which of the two it
#: is stays on the printed line, :attr:`Standing.sentence` being the detail.
_SATISFIES = {
    Stage.FINISHED: DepStatus.SHIPPED,
    Stage.PAUSED: DepStatus.DEFERRED,
    Stage.EMPTY: DepStatus.UNRESOLVABLE,
    Stage.UNKNOWN: DepStatus.UNRESOLVABLE,
}

@dataclass(frozen=True, slots=True)
class Resolution:
    """One dep, what it names, how it resolved, and a sentence a human can read."""

    dep: Dep
    kind: DepKind
    status: DepStatus
    detail: str

    @property
    def satisfied(self) -> bool:
        return self.status is DepStatus.SHIPPED


@dataclass(frozen=True, slots=True)
class Backlog:
    """The roadmap and the ledger, read once, resolved together.

    Both files are needed for any question about status: the roadmap knows what is
    open and only the ledger knows what shipped. Loading them separately at each
    call site is how two commands come to disagree.
    """

    config: Config
    roadmap: Document
    ledger: Document | None = None
    #: The deferred store (RK96), read for the same reason the ledger is (RK92): a dep
    #: whose target is paused resolves against a file neither of the other two is, and
    #: loading it only where somebody remembered to is how a fifth status comes to mean
    #: "unknown" in every command that forgot.
    store: Document | None = None

    @classmethod
    def load(cls, config: Config) -> Backlog:
        return cls(
            config=config,
            roadmap=config.document("roadmap"),
            ledger=_present(config, "changelog"),
            store=_present(config, "deferred"),
        )

    @classmethod
    def during(
        cls,
        config: Config,
        *,
        roadmap: Document,
        ledger: Document | None = None,
        store: Document | None = None,
    ) -> Backlog:
        """A backlog mid-write: the documents this transaction creates, the rest from disk.

        A door and not a convenience (RK92). Every caller that resolves against a state not
        yet on disk used to build the dataclass by hand, which meant naming each file it
        cared about — so a file added later was absent in exactly the commands that never
        heard of it, and a deferred dep read as a missing id inside `ship` while reading
        correctly outside it. Named files override; the others are read.
        """
        return cls(
            config=config,
            roadmap=roadmap,
            ledger=ledger if ledger is not None else _present(config, "changelog"),
            store=store if store is not None else _present(config, "deferred"),
        )

    # -- lookups -----------------------------------------------------------

    def entry(self, task_id: str) -> Entry | None:
        return self.roadmap.by_id().get(task_id)

    def shipped(self) -> frozenset[str]:
        """Ids the ledger marks ✅ — never merely *present* in it.

        A retired line lives in the same file (RK32), so reading the ledger as a set of
        ids would make "this was abandoned" resolve as "this is done" — a dep satisfied
        by the record of its own cancellation.
        """
        if self.ledger is None:
            return frozenset()
        marker = self.config.schema.shipped_marker
        return frozenset(
            task_id
            for task_id, entry in self.ledger.by_id().items()
            if entry.task.status == marker
        )

    def partial(self, task_id: str) -> str:
        """Which half the ledger says landed, where this id shipped in halves (RK121, RK396).

        Empty for every other id, which is what makes it a *detail* and not a status: a
        partial is an open line whose ledger entry names the delivered part, so the answer
        about whether to start work stays the line's and this only says what already exists.
        """
        if self.ledger is None:
            return ""
        entry = self.ledger.by_id().get(task_id)
        if entry is None or entry.task.status != self.config.schema.shipped_marker:
            return ""
        return entry.task.part or ""

    def deferred(self) -> dict[str, Entry]:
        """Ids the store holds, with the line that says why they were set aside.

        Every line in it, and not the ones carrying ⏸: the store's own status *is* ⏸ and
        the schema refuses any other there (RK96), so filtering by marker would be this
        module re-deciding what the file already guarantees.
        """
        return {} if self.store is None else dict(self.store.by_id())

    def retired(self) -> dict[str, Entry]:
        """Ids the ledger marks 🗑, with the line that says why they left."""
        if self.ledger is None:
            return {}
        marker = self.config.schema.retired_marker
        return {
            task_id: entry
            for task_id, entry in self.ledger.by_id().items()
            if entry.task.status == marker
        }

    def open_in_block(self, label: str) -> tuple[str, ...]:
        return tuple(e.task.id for e in self.roadmap.block(label))

    def declared_blocks(self) -> frozenset[str]:
        """Every block label a heading declares, across both files.

        The ledger counts: a block whose last task shipped keeps its heading there
        and may have lost the one in the roadmap. This is the only record that a
        block exists at all — nothing registers one — which is why an undeclared
        block and a finished one are otherwise indistinguishable.
        """
        return frozenset(
            heading.label
            for document in (self.roadmap, self.ledger)
            if document is not None
            for heading in document.headings
            if heading.label
        )

    def standing(self, label: str) -> Standing:
        """Which of :class:`Stage`'s four states this label is in (RK429).

        The read every query makes after its own count comes back empty — and the gate's,
        resolving a queue entry that names a block (RK434), which is where the second copy
        of this walk had already drifted: it never opened the store, so a paused block was
        reported as an unstarted one. A method here rather than the same four lines at each
        call site: the files it joins are the three this class holds open.
        """
        return Standing.of(self, label)

    # -- resolving ---------------------------------------------------------

    def resolve_dep(self, dep: Dep) -> Resolution:
        """One dep, resolved by what it names. Four kinds, four resolvers."""
        kind = self.config.schema.classify_dep(dep)
        resolver = {
            DepKind.EXTERNAL: self._resolve_external,
            DepKind.RANGE: self._resolve_range,
            DepKind.BLOCK: self._resolve_block,
            DepKind.TASK: self._resolve_task,
        }[kind]
        return resolver(dep, kind)

    def _resolve_external(self, dep: Dep, kind: DepKind) -> Resolution:
        return Resolution(
            dep,
            kind,
            DepStatus.UNRESOLVABLE,
            "outside the backlog: nothing here will ever mark this done",
        )

    def _resolve_range(self, dep: Dep, kind: DepKind) -> Resolution:
        still_open = self._open_in_range(dep)
        if still_open:
            return Resolution(dep, kind, DepStatus.OPEN, _open_detail(still_open))
        # A range with no open members is satisfied, not unknown: ids are
        # non-contiguous by design, so "nothing open in T451–T457" is the answer.
        return Resolution(dep, kind, DepStatus.SHIPPED, "nothing open in the range")

    def _resolve_block(self, dep: Dep, kind: DepKind) -> Resolution:
        """What the label's own :class:`Stage` says, in this module's other vocabulary.

        This asked two questions of its own — is there a heading, is anything open — which
        is :meth:`Standing.of`'s walk with two of its settled answers missing, and the
        missing pair were the interesting ones (RK432). A heading `block add` wrote before
        a single line was filed under it resolved as `shipped`, so `pick` offered the
        dependent, `brief` printed a checkmark beside a blocker that did not exist yet, and
        the annotation cached that checkmark into the file — RK28's failure one level up
        from the id it was written about.

        `paused` is :attr:`DepStatus.DEFERRED` for RK92's three clauses, each of which
        holds of a label with nothing open and a line in the store: recorded, so not
        unknown; revivable, so not unresolvable; not in the roadmap, so not open. It
        outranks the ledger in :meth:`Standing.of`, so a block that shipped nine lines and
        set the tenth aside resolves deferred and not shipped — the pause is the fact a
        dependent's own line cannot show.

        `live` is the one stage :data:`_SATISFIES` does not carry, because its detail is
        not the standing's: the sentence is a header and names no ids, and the ids are the
        actionable half of an open dep. That is the one deliberate second read of the block
        — :class:`Standing` counted those lines and kept only the count.
        """
        label = self.config.schema.block_of_dep(dep)
        standing = self.standing(label)
        if standing.stage is Stage.LIVE:
            return Resolution(
                dep,
                kind,
                DepStatus.OPEN,
                f"{standing.named}: {_open_detail(self.open_in_block(label))}",
            )
        return Resolution(dep, kind, _SATISFIES[standing.stage], standing.sentence)

    def _resolve_task(self, dep: Dep, kind: DepKind) -> Resolution:
        # A **partial** is read before the ledger (RK396). `ship --part` writes an entry and
        # deliberately leaves the line open at ⏳, so membership stopped meaning the work is
        # finished — and the dependent was annotated ✅ by the half that landed rather than by
        # the half it waits on, which is the one thing this annotation exists to prevent.
        #
        # Narrowed to the qualifier the entry carries, and not to "open line wins", because
        # an id in both files with *no* qualifier is a ship that crashed between its writes:
        # there the intended end state is shipped, `deps.stale` on the dependents is part of
        # what makes that middle state loud (RK118), and reading it as open would quietly
        # complete the transaction's story in the one file that had not been written yet.
        landed = self.partial(dep.id)
        open_line = self.entry(dep.id)
        if landed and open_line is not None:
            where = f" in Block {open_line.task.block}" if open_line.task.block else ""
            return Resolution(
                dep, kind, DepStatus.OPEN, f"open{where}, the {landed} in the changelog"
            )
        if dep.id in self.shipped():
            return Resolution(dep, kind, DepStatus.SHIPPED, "in the changelog")
        gone = self.retired().get(dep.id)
        if gone is not None:
            # Unresolvable and not unknown: the record exists and says the work will not
            # happen, so waiting is over in the one direction that never satisfies. What
            # has to change is this line, and the retired line's own sentence says how.
            return Resolution(
                dep, kind, DepStatus.UNRESOLVABLE, f"retired — {_clip(gone.task.why)}"
            )
        found = self.entry(dep.id)
        if found is not None:
            detail = f"open in Block {found.task.block}" if found.task.block else "open"
            return Resolution(dep, kind, DepStatus.OPEN, detail)
        paused = self.deferred().get(dep.id)
        if paused is not None:
            # Checked after the roadmap and before "unknown" (RK92): the store is the one
            # place a recorded id can be that is neither open nor terminal, and reporting
            # it as a gap in the files would send the reader looking for a typo.
            return Resolution(
                dep, kind, DepStatus.DEFERRED, f"set aside — {_clip(paused.task.why)}"
            )
        return Resolution(
            dep, kind, DepStatus.UNKNOWN, "in neither the roadmap nor the changelog"
        )

    def expand(self, dep: Dep) -> tuple[str, ...]:
        """The open tasks a collective dep names, in file order; empty for the other kinds.

        `Block P` is one token and resolved to forty-eight open tasks in Shio; `T451–T457`
        is one token and names seven. Public and here rather than inside the graph because
        two callers need the same answer: the traversal, which would otherwise walk into a
        dep it treats as opaque, and the gate, which says out loud what the abbreviation
        costs whoever counts deps to judge how blocked a line is (RK35).
        """
        schema = self.config.schema
        kind = schema.classify_dep(dep)
        if kind is DepKind.BLOCK:
            label = schema.block_of_dep(dep)
            return self.open_in_block(label) if label else ()
        return self._open_in_range(dep) if kind is DepKind.RANGE else ()

    def _open_in_range(self, dep: Dep) -> tuple[str, ...]:
        """The still-open ids a range dep names — bounded by its numbers *and* its track.

        One implementation, because `resolve_dep` and `open_for` used to hold two and a
        range that counted one family in one of them would have been a dep whose detail
        line disagreed with its status.
        """
        schema = self.config.schema
        bounds = schema.range_of_dep(dep)
        family = schema.family_of_dep(dep)
        if bounds is None or family is None:
            return ()
        first, last = bounds
        return tuple(
            entry.task.id
            for entry in self.roadmap.entries
            # `number_of` against the *one* family, not all of them: `C14–C20` counts in
            # cursarei's product track and must not be satisfied by `V15` shipping.
            if (number := number_of(entry.task.id, schema, family)) is not None
            and first <= number <= last
        )

    def resolve(self, task: Task) -> tuple[Resolution, ...]:
        return tuple(self.resolve_dep(dep) for dep in task.deps)

    def readiness(self, task: Task) -> Readiness:
        """Ready, or blocked in one of the three senses that differ (RK28, RK92).

        Ordered by how permanent the answer is, so a line with two kinds of blocker
        reports the one nothing on this backlog's own path resolves: unresolvable outranks
        paused, because no line the roadmap now holds satisfies it while a paused one
        resumes; and paused outranks blocked, because an open blocker is somebody's next
        task while a deferred one is a decision nobody has revisited.
        """
        resolutions = self.resolve(task)
        if any(r.status is DepStatus.UNRESOLVABLE for r in resolutions):
            return Readiness.OUTSIDE
        if all(r.satisfied for r in resolutions):
            return Readiness.READY
        if any(r.status is DepStatus.DEFERRED for r in resolutions):
            return Readiness.PAUSED
        return Readiness.BLOCKED


def number_of(task_id: str, schema: Schema, family: str | None = None) -> int | None:
    """The numeric part of an id of this project, or None if it is not one.

    Public because a range dep is bounded by numbers: `C14–C20` asks which open lines fall
    between two of them, and that is a question about the number alone.

    Takes the :class:`~roadkeep.kernel.schema.Schema` and not `prefixes` plus a flag (RK109). The
    shape is one declaration — the families (RK74), the width and the sub-letter (RK106) —
    and a signature that let a caller pass two thirds of it is how the ordering came to
    read a `D1` its own gate refuses. ``family`` narrows the answer to one track, because
    `C14–C20` counts in cursarei's product track and must not be satisfied by `V15`.
    """
    parsed = schema.parse_id(task_id)
    if parsed is None or (family is not None and parsed.family != family):
        return None
    return parsed.number


def id_order(task_id: str, schema: Schema) -> tuple[int, int, str, str]:
    """How ids sort — the one answer `pick`, `lint` and `--fix` all order by (RK109).

    "Lowest id" is a numeric comparison, and three call sites each wrote it as
    ``number_of(...) or 0``, which put anything unreadable *first*: the split task a
    project deliberately numbered after `T24` would have been offered ahead of `T1`. Here
    an id this project cannot read sorts **last**, by its own text, because a string the
    gate refuses is not a claim on the front of the queue — and `T24b` sorts directly after
    `T24`, the sub-letter being the tie-break it was written to be.
    """
    parsed = schema.parse_id(task_id)
    if parsed is None:
        return (1, 0, "", task_id)
    return (0, parsed.number, parsed.sub, task_id)


def _present(config: Config, role: str) -> Document | None:
    """One optional governed file, or None where it is undeclared or not written yet.

    A declared file that is not on disk yet is absent, not empty — `init` (RK18) creates
    it, and refusing every question until then would be an obstacle.
    """
    if not config.has(role) or not config.path(role).is_file():
        return None
    return config.document(role)


def _clip(sentence: str, limit: int = 90) -> str:
    """One line of detail. The whole sentence is one `show <id>` away."""
    return sentence if len(sentence) <= limit else sentence[: limit - 1].rstrip() + "…"


def _open_detail(still_open: tuple[str, ...]) -> str:
    """`n open: a, b, c …` — bounded, because a detail line nobody reads is noise."""
    shown = ", ".join(still_open[:4])
    return f"{len(still_open)} open: {shown}" + (" …" if len(still_open) > 4 else "")
