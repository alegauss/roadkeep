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

from dataclasses import dataclass
from enum import StrEnum

from roadkeep.config import Config
from roadkeep.document import Document, Entry
from roadkeep.schema import Dep, DepKind, Task


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
        ledger = config.document("changelog") if config.has("changelog") else None
        return cls(config=config, roadmap=config.document("roadmap"), ledger=ledger)

    # -- lookups -----------------------------------------------------------

    def entry(self, task_id: str) -> Entry | None:
        return self.roadmap.by_id().get(task_id)

    def shipped(self) -> frozenset[str]:
        if self.ledger is None:
            return frozenset()
        return frozenset(self.ledger.by_id())

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
        first, last = self.config.schema.range_of_dep(dep)
        prefix = self.config.schema.prefix
        still_open = tuple(
            e.task.id
            for e in self.roadmap.entries
            if (number := _number_of(e.task.id, prefix)) is not None
            and first <= number <= last
        )
        if still_open:
            return Resolution(dep, kind, DepStatus.OPEN, _open_detail(still_open))
        # A range with no open members is satisfied, not unknown: ids are
        # non-contiguous by design, so "nothing open in T451–T457" is the answer.
        return Resolution(dep, kind, DepStatus.SHIPPED, "nothing open in the range")

    def _resolve_block(self, dep: Dep, kind: DepKind) -> Resolution:
        label = self.config.schema.block_of_dep(dep)
        if label not in self.declared_blocks():
            # Not UNKNOWN: an undeclared block is not a gap in a file, it is a dep
            # this backlog cannot answer at all — the same answer an external dep
            # gets, so that neither is ever counted as done by being empty.
            return Resolution(
                dep,
                kind,
                DepStatus.UNRESOLVABLE,
                f"no heading declares Block {label}: a block nothing declares is "
                f"not a block with nothing open",
            )
        still_open = self.open_in_block(label)
        if still_open:
            return Resolution(
                dep, kind, DepStatus.OPEN, f"Block {label}: {_open_detail(still_open)}"
            )
        return Resolution(
            dep, kind, DepStatus.SHIPPED, f"Block {label} has nothing open"
        )

    def _resolve_task(self, dep: Dep, kind: DepKind) -> Resolution:
        if dep.id in self.shipped():
            return Resolution(dep, kind, DepStatus.SHIPPED, "in the changelog")
        found = self.entry(dep.id)
        if found is not None:
            detail = f"open in Block {found.task.block}" if found.task.block else "open"
            return Resolution(dep, kind, DepStatus.OPEN, detail)
        return Resolution(
            dep, kind, DepStatus.UNKNOWN, "in neither the roadmap nor the changelog"
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


def _number_of(task_id: str, prefix: str) -> int | None:
    """The numeric part of an id of this project, or None if it is not one."""
    if not task_id.startswith(prefix):
        return None
    tail = task_id[len(prefix) :]
    return int(tail) if tail.isdigit() else None


def _open_detail(still_open: tuple[str, ...]) -> str:
    """`n open: a, b, c …` — bounded, because a detail line nobody reads is noise."""
    shown = ", ".join(still_open[:4])
    return f"{len(still_open)} open: {shown}" + (" …" if len(still_open) > 4 else "")
