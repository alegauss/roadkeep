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
sends the caller at something that cannot be finished (RK28). :class:`Readiness.PAUSED`
is the third (RK92) and gets its own number for the same reason: a backlog stuck on
deferred deps is stuck on a decision nobody revisited, which no amount of shipping moves.

The stalled list is the other half of the same honesty: a 🛠 task that is *blocked* is
reported beside the answer, because that is the state a reader most needs to know about
and the one tier 1 cannot pick.

**Ready and implementable are two different states** (RK83). The tiers rank by id and
never by marker, so a block holding both designs and ideas answers a caller who asked to
execute it with a design session. Two things follow, and neither is a fourth tier: the
answer *says* when the line it chose still needs designing, because the complaint was
never that it chose wrongly but that it chose silently; and ``designed`` sets those lines
aside, because the bias belongs to the caller's intent and not to the ranking — a block
whose ideas are never offered is a block whose ideas are never designed.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from roadkeep.backlog import Backlog, Readiness, id_order
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
    #: The block the question was scoped to, when it was (RK40). Every count and every
    #: alternative below is then about that block and nothing else.
    block: str | None = None
    #: The next few ready tasks, in the same order the pick came from.
    alternatives: tuple[str, ...] = ()
    ready: int = 0
    blocked: int = 0
    outside: int = 0
    #: Open lines waiting on work somebody set aside (RK92). Its own number for RK28's
    #: reason: a backlog stuck on paused deps is stuck on a decision, not on a task.
    paused: int = 0
    stalled: tuple[Stalled, ...] = ()
    #: Whether the chosen line still needs designing (RK83). Said, never acted on: it is
    #: the sentence that stops the pick being silent about which of the two states it is.
    needs_design: bool = False
    #: How many ready lines ``designed`` set aside. 0 whenever the flag was not passed, so
    #: a non-zero value is always the caller's own filter and never a fact about the file.
    undesigned: int = 0

    @property
    def found(self) -> bool:
        return self.entry is not None

    @property
    def counts(self) -> str:
        """All four numbers, always: a zero is the fact a reader is checking for."""
        return (
            f"{self.ready} ready, {self.blocked} blocked, "
            f"{self.outside} blocked outside the backlog, "
            f"{self.paused} blocked on paused work"
        )


def pick(config: Config, block: str | None = None, designed: bool = False) -> Choice:
    """Apply the three tiers to the roadmap, and say which one answered.

    ``block`` scopes every part of the answer — the tiers, the counts, the alternatives —
    so that "nothing to pick" is a statement about *that* block (RK40). Unscoped, the
    lowest ready id can live in another block, and reading that as "this block is
    finished" is a mistake the ids being non-sequential makes easy.

    ``designed`` sets aside the ready lines whose marker says the design is unwritten
    (RK83), for a caller who asked to *execute* rather than to plan. It narrows what may
    be chosen and nothing else: ``ready`` still counts every ready line, because the
    number of lines this backlog could start is not a fact the caller's intent changes.
    """
    backlog = Backlog.load(config)
    if block is not None and block not in backlog.declared_blocks():
        raise KeyError(
            f"no heading declares {config.schema.block_named(block)} (declares: "
            f"{', '.join(sorted(backlog.declared_blocks())) or 'none'})"
        )
    scope = f" in {config.schema.block_named(block)}" if block else ""
    considered = [
        entry
        for entry in backlog.roadmap.entries
        if block is None or entry.task.block == block
    ]
    survey = _survey(backlog, considered)
    ordered = sorted(survey.ready, key=lambda e: id_order(e.task.id, config.schema))
    # Narrowed after the ordering and not before it, so `ready` keeps counting what the
    # file holds: the caller's intent decides what may be offered, never what is true.
    offered = [e for e in ordered if not config.schema.needs_design(e.task.status)]
    set_aside = len(ordered) - len(offered) if designed else 0
    if designed:
        ordered = offered
    counts = {
        "block": block,
        "blocked": survey.blocked,
        "outside": survey.outside,
        "paused": survey.paused,
        "stalled": survey.stalled,
        "undesigned": set_aside,
    }
    if not ordered:
        # Three different absences now, and telling them apart is the whole point of the
        # scope: a block with nothing left is finished, one whose lines are all blocked is
        # not, and one whose ready lines are all ideas is waiting on a design session.
        if set_aside:
            reason = (
                f"every ready task{scope} still needs designing, so there is nothing "
                "to implement"
            )
        elif not considered:
            reason = f"nothing is open{scope}"
        else:
            reason = f"every open task{scope} is blocked, so there is nothing to start"
        return Choice(
            entry=None, tier=None, reason=reason, ready=len(survey.ready), **counts
        )

    chosen, tier, why = _first(ordered, config)
    rest = tuple(e.task.id for e in ordered if e is not chosen)[:ALTERNATIVES]
    needs_design = config.schema.needs_design(chosen.task.status)
    reason = f"{why}{scope}" if tier is Tier.LOWEST else why
    if needs_design:
        # Appended to the tier's own reason rather than replacing it: the tier still fired
        # and is still a fact, and what was missing was never the choice but the caveat.
        reason = f"{reason} — it still needs designing, which `--designed` skips"
    return Choice(
        entry=chosen,
        tier=tier,
        reason=reason,
        alternatives=rest,
        ready=len(survey.ready),
        needs_design=needs_design,
        **counts,
    )


@dataclass(frozen=True, slots=True)
class _Survey:
    """One pass over the lines in scope: who is ready, and who is not and why not."""

    ready: tuple[Entry, ...]
    blocked: int
    outside: int
    stalled: tuple[Stalled, ...]
    paused: int = 0


def _survey(backlog: Backlog, considered: list[Entry]) -> _Survey:
    ready: list[Entry] = []
    blocked = outside = paused = 0
    stalled: list[Stalled] = []
    for entry in considered:
        readiness = backlog.readiness(entry.task)
        if readiness is Readiness.READY:
            ready.append(entry)
            continue
        if readiness is Readiness.OUTSIDE:
            outside += 1
        elif readiness is Readiness.PAUSED:
            paused += 1
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
    return _Survey(
        ready=tuple(ready),
        blocked=blocked,
        outside=outside,
        stalled=tuple(stalled),
        paused=paused,
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
