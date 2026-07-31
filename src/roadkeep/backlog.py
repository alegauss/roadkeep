"""Resolving a dep against the backlog it names (RK28).

A dep is a claim about other work, and there are four different answers to "is it
done?" — shipped, still open, no such task, and *unanswerable*. Collapsing the last
one into "still open" is what makes a permanently blocked task read like the next one
to start, which is the whole reason this module exists rather than a boolean.

The interesting case is the one the corpora already write. Shio has `(deps: Block P)`
and Turing has `(deps: real design partners)`: real work does wait on a whole block,
and on things that are not tracked work at all. So:

* a **task** dep resolves against the roadmap and the ledger;
* a **block** dep resolves against that block's own emptiness — a block with open
  tasks is not done, and a block with none left is — but only once a heading
  declares the block, because blocks are discovered and never registered, so a
  block nothing declares is empty for a reason that is not completion (RK37);
* an **external** dep is :attr:`DepStatus.UNRESOLVABLE` forever, and a task carrying
  one is never *ready*, it is blocked outside the backlog. Naming that is the
  difference between an answer and a guess.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

from roadkeep.config import Config
from roadkeep.document import Document, Entry
from roadkeep.schema import Dep, DepKind, Task


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


class DepStatus(StrEnum):
    """How a single dep resolved."""

    SHIPPED = "shipped"
    OPEN = "open"
    #: An id of this project that exists in neither file. A lint error (RK8), not a
    #: rendering choice: nothing downstream can tell whether it is done.
    UNKNOWN = "unknown"
    #: Outside the backlog by construction. Never becomes shipped by waiting.
    UNRESOLVABLE = "unresolvable"


class Readiness(StrEnum):
    """Whether a task can be started, and if not, in which of two senses."""

    READY = "ready"
    BLOCKED = "blocked"
    #: Blocked by something the backlog does not track, so no amount of shipping
    #: tasks unblocks it. `pick` (RK11) must not offer these as next work.
    OUTSIDE = "blocked-outside"


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

    @classmethod
    def load(cls, config: Config) -> Backlog:
        # A declared file that is not on disk yet is absent, not empty — `init` (RK18)
        # creates it, and refusing every question until then would be an obstacle.
        declared = config.has("changelog") and config.path("changelog").is_file()
        ledger = config.document("changelog") if declared else None
        return cls(config=config, roadmap=config.document("roadmap"), ledger=ledger)

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
        schema = self.config.schema
        label = schema.block_of_dep(dep)
        if label not in self.declared_blocks():
            # Not UNKNOWN: an undeclared block is not a gap in a file, it is a dep
            # this backlog cannot answer at all — the same answer an external dep
            # gets, so that neither is ever counted as done by being empty.
            return Resolution(
                dep,
                kind,
                DepStatus.UNRESOLVABLE,
                f"no heading declares {schema.block_named(label)}: a block nothing declares is "
                f"not a block with nothing open",
            )
        still_open = self.open_in_block(label)
        if still_open:
            return Resolution(
                dep,
                kind,
                DepStatus.OPEN,
                f"{schema.block_named(label)}: {_open_detail(still_open)}",
            )
        return Resolution(
            dep, kind, DepStatus.SHIPPED, f"{schema.block_named(label)} has nothing open"
        )

    def _resolve_task(self, dep: Dep, kind: DepKind) -> Resolution:
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
            if (number := number_of(entry.task.id, family)) is not None
            and first <= number <= last
        )

    def resolve(self, task: Task) -> tuple[Resolution, ...]:
        return tuple(self.resolve_dep(dep) for dep in task.deps)

    def readiness(self, task: Task) -> Readiness:
        """Ready, blocked, or blocked by something this backlog cannot resolve."""
        resolutions = self.resolve(task)
        if any(r.status is DepStatus.UNRESOLVABLE for r in resolutions):
            return Readiness.OUTSIDE
        if all(r.satisfied for r in resolutions):
            return Readiness.READY
        return Readiness.BLOCKED


def number_of(task_id: str, prefixes: str | Sequence[str]) -> int | None:
    """The numeric part of an id of this project, or None if it is not one.

    Public because `pick` (RK11) orders by it: "lowest id" is a numeric comparison, and
    a second implementation of it would sort RK9 after RK10 in exactly one of the two.

    Takes every family the project numbers (RK74), longest first so that a `C` declared
    beside a `CX` cannot claim `CX7` — which :func:`~roadkeep.schema._check_prefixes`
    already refuses, this being the second place that would have to know it.
    """
    if isinstance(prefixes, str):
        prefixes = (prefixes,)
    for prefix in sorted(prefixes, key=lambda p: (-len(p), p)):
        if not task_id.startswith(prefix):
            continue
        tail = task_id[len(prefix) :]
        if tail.isdigit():
            return int(tail)
    return None


def family_of(task_id: str, prefixes: Sequence[str]) -> str | None:
    """Which family an id belongs to (RK74), or None if it belongs to none.

    Separate from :func:`number_of` because `next-id` asks a different question of the
    same string: not "how high does this backlog count" but "how high does *this track*",
    two tracks sharing a counter being two tracks that renumber each other.
    """
    for prefix in sorted(prefixes, key=lambda p: (-len(p), p)):
        tail = task_id[len(prefix) :] if task_id.startswith(prefix) else ""
        if tail.isdigit():
            return prefix
    return None


def _clip(sentence: str, limit: int = 90) -> str:
    """One line of detail. The whole sentence is one `show <id>` away."""
    return sentence if len(sentence) <= limit else sentence[: limit - 1].rstrip() + "…"


def _open_detail(still_open: tuple[str, ...]) -> str:
    """`n open: a, b, c …` — bounded, because a detail line nobody reads is noise."""
    shown = ", ".join(still_open[:4])
    return f"{len(still_open)} open: {shown}" + (" …" if len(still_open) > 4 else "")
