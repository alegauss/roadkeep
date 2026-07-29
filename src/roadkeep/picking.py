"""What to work on next, and the reason it was chosen (RK11).

"What do I work on" is the question a roadmap is asked most often and answers worst: the
rule — *lowest-numbered task whose deps are all shipped* — is a join over two files that
costs reading both of them, every session, to learn one line. So it is a command, and the
answer carries **why**, because an unexplained pick cannot be checked and a pick nobody
checks is a pick nobody trusts (L5).

Three tiers, in this order, and each one is a fact rather than a taste:

1. **Work already in progress.** A 🛠 line says someone started; picking something else
   leaves it half-done, and half-done work is the one state the marker set can express
   and no count can repair. This tier is why `pick` does not simply mean "lowest".
2. **The declared priority.** `priority = ["RK14", "Block D"]` in `roadkeep.toml` (L6),
   applied in the order written. Declared, and not read out of a "## Priority queue"
   section: Shio has one and it is prose — a paragraph about why reachability comes
   first. A tool that ranked work by reading it would be interpreting prose (L4).
3. **The lowest ready id**, numerically. Blocks are ordered by dependency, so the id
   order already follows the build order and needs no second opinion.

What never gets offered: anything :class:`Readiness.BLOCKED`, and — the distinction that
makes this useful — anything :class:`Readiness.OUTSIDE`. A task waiting on work this
backlog does not track never becomes ready by shipping tasks, so offering it as "next"
sends the caller at something that cannot be finished (RK28).

The stalled list is the other half of the same honesty: a 🛠 task that is *blocked* is
reported beside the answer, because that is the state a reader most needs to know about
and the one tier 1 cannot pick.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from roadkeep.backlog import Backlog, Readiness, number_of
from roadkeep.config import Config
from roadkeep.document import Entry
from roadkeep.schema import IN_PROGRESS, Dep

#: How many runners-up an answer carries. Bounded on purpose: the value of `pick` is that
#: its output fits in a tool result, and a ranked list of everything is the file again.
ALTERNATIVES = 3


class Tier(StrEnum):
    """Which rule produced the answer. Printed, so the pick can be argued with."""

    STARTED = "in-progress"
    PRIORITY = "declared-priority"
    LOWEST = "lowest-ready-id"


@dataclass(frozen=True, slots=True)
class Stalled:
    """A started task that cannot be continued, and what is holding it."""

    id: str
    blockers: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Choice:
    """The answer, or the reasoned absence of one."""

    entry: Entry | None
    tier: Tier | None
    reason: str
    #: The next few ready tasks, in the same order the pick came from.
    alternatives: tuple[str, ...] = ()
    ready: int = 0
    blocked: int = 0
    outside: int = 0
    stalled: tuple[Stalled, ...] = ()

    @property
    def found(self) -> bool:
        return self.entry is not None

    @property
    def counts(self) -> str:
        """All three numbers, always: a zero is the fact a reader is checking for."""
        return (
            f"{self.ready} ready, {self.blocked} blocked, "
            f"{self.outside} blocked outside the backlog"
        )


def pick(config: Config) -> Choice:
    """Apply the three tiers to the roadmap, and say which one answered."""
    backlog = Backlog.load(config)
    prefix = config.schema.prefix
    ready: list[Entry] = []
    blocked = outside = 0
    stalled: list[Stalled] = []

    for entry in backlog.roadmap.entries:
        readiness = backlog.readiness(entry.task)
        if readiness is Readiness.READY:
            ready.append(entry)
            continue
        if readiness is Readiness.OUTSIDE:
            outside += 1
        else:
            blocked += 1
        if entry.task.status == IN_PROGRESS:
            stalled.append(
                Stalled(
                    id=entry.task.id,
                    blockers=tuple(
                        r.dep.id for r in backlog.resolve(entry.task) if not r.satisfied
                    ),
                )
            )

    ordered = sorted(ready, key=lambda e: (number_of(e.task.id, prefix) or 0, e.task.id))
    if not ordered:
        return Choice(
            entry=None,
            tier=None,
            reason="every open task is blocked, so there is nothing to start",
            blocked=blocked,
            outside=outside,
            stalled=tuple(stalled),
        )

    chosen, tier, why = _first(ordered, config)
    rest = tuple(e.task.id for e in ordered if e is not chosen)[:ALTERNATIVES]
    return Choice(
        entry=chosen,
        tier=tier,
        reason=why,
        alternatives=rest,
        ready=len(ready),
        blocked=blocked,
        outside=outside,
        stalled=tuple(stalled),
    )


def _first(ordered: list[Entry], config: Config) -> tuple[Entry, Tier, str]:
    """The three tiers, in order, each returning the reason it fired."""
    started = [e for e in ordered if e.task.status == IN_PROGRESS]
    if started:
        return (
            started[0],
            Tier.STARTED,
            f"{started[0].task.id} is already in progress and ready to continue",
        )

    for token in config.priority:
        # Typed by the code that types a dep, so `Block X` cannot come to mean two things.
        label = config.schema.block_of_dep(Dep(token))
        if label is not None:
            inside = [e for e in ordered if e.task.block == label]
            if inside:
                return (
                    inside[0],
                    Tier.PRIORITY,
                    f"declared priority names Block {label}, whose lowest ready id it is",
                )
            continue
        match = next((e for e in ordered if e.task.id == token), None)
        if match is not None:
            return match, Tier.PRIORITY, f"declared priority names {token} and it is ready"

    if config.priority:
        return (
            ordered[0],
            Tier.LOWEST,
            "lowest ready id; the declared priority names nothing ready",
        )
    return ordered[0], Tier.LOWEST, "lowest ready id"
