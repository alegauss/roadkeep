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
2. **The declared priority.** A `## Priority` section of the roadmap, or `priority =
   ["RK14", "Block D"]` in `roadkeep.toml` (L6), applied in the order written. The section
   wins where both exist, and `roadkeep.queueing` is the reader — the objection this tier
   used to state, that Shio's "## Priority queue" is a paragraph about why reachability
   comes first, is about *interpreting prose* (L4) and does not reach a list this tool
   renders (RK325). What the move buys is that the queue's tokens name work that **leaves**,
   and the file the plan is in is the one every departure already rewrites.
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

**One backlog and two workers is one answer too few** (RK119). Every tier above is a pure
function of the file, so a second caller reading an unchanged roadmap is handed the line the
first one took — tier 1 most confidently of all, since a 🛠 line is *evidence* somebody
started. So a claim that is still live is stepped around before the tiers see it, and
:func:`take` is the door that makes one: it answers and flips the marker inside a single
serialised transaction, because a pick that answered and then wrote would be two steps with
the race in the middle. What a claim is, how it expires and why it names nobody is
:mod:`roadkeep.claiming`; what is here is that a held line is **named** in the answer rather
than silently absent, which is the same rule ``designed`` follows for the lines it sets
aside — and the only way a caller can recognise a claim as its own.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from enum import StrEnum

from roadkeep import claiming
from roadkeep.authoring import StatusChange, set_status
from roadkeep.backlog import Backlog, DepStatus, Readiness, Stage, Standing, id_order
from roadkeep.claiming import Held
from roadkeep.config import Config
from roadkeep.kernel.document import Entry, declares, shading
from roadkeep.locking import exclusive
from roadkeep.queueing import declared
from roadkeep.kernel.schema import IN_PROGRESS, Dep

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
    #: The live claim on this line, where there is one (RK152). Its own field and not
    #: :attr:`Choice.held`, which is the ready lines a claim kept out of the ranking: one word
    #: for both facts is how this report came to be silent about the second. The two states it
    #: separates are "somebody started this and hit a wall", which invites unblocking it, and
    #: "somebody is on this now, and the dep is what they are waiting for", which does not.
    claimed: Held | None = None


#: How many releasing ids a waiting row names (RK1304), bounded for RK1301's reason: a
#: priority waiting on eleven things is one whose next step is a decision and not a command,
#: and the count says that where the roster would only spend the answer saying it.
RELEASES = 4


@dataclass(frozen=True, slots=True)
class Waiting:
    """A declared priority nothing ready answers, and what would release it (RK1304).

    Observed over four consecutive sessions on a port whose roadmap declares Priority as
    Block H then Block I. Every line in both was blocked, so the pick fell through to the
    lowest ready id and said so: *the roadmap's queue names nothing ready*. True, and one step
    short — Block H held one line, blocked on a single task in another block, and nothing in
    the answer said which. The caller who wanted the priority had to open the roadmap, read
    the queue, find the block's lines, read their deps and look each one up, which is the
    reading this verb exists to replace, done by hand, at the moment it was least obvious.

    Beside the pick and never instead of it: the pick may still be the right call when the
    blocker is expensive. The case that makes this worth having is the other one, where it is
    cheap and nobody looked.
    """

    #: The queue token, as the queue spells it — a `Block X` or an id.
    token: str
    #: Open lines the token names. Every one of them blocked, or this row would not exist.
    lines: int
    #: The ids whose shipping would release one of those lines: their unsatisfied deps,
    #: deduplicated and in id order, bounded by :data:`RELEASES`.
    releases: tuple[str, ...] = ()
    #: How many there are in all, so a cut roster is never read as a short one.
    of: int = 0


@dataclass(frozen=True, slots=True)
class Lacking:
    """A ready line this caller cannot finish, and what it would take (RK1297).

    Named and never merely counted, for the reason :attr:`Choice.held` is: a number the
    caller cannot read is a line it asks about twice. Here the id is not even the actionable
    half — :attr:`missing` is, because what closes this is somebody with a DualSense on the
    desk rather than any command the caller could run.
    """

    id: str
    #: The declared requirements this caller did not say it has, in the line's own order.
    missing: tuple[str, ...]
    #: The line's own symptom (RK1490). Carried because the decision this row now supports is
    #: *does the part I want need that word*, and an id cannot be judged: the caller who reads
    #: `requires upstream` and knows their half is in the repository they have could only get
    #: there by opening the roadmap, which is the reading this verb exists to replace. Empty
    #: where the reader never needs it, which is every call that found a line to offer.
    symptom: str = ""


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
    #: The ready lines a live claim kept out of the ranking (RK119). Named and not counted,
    #: because a claim names nobody: a caller can only tell one of these is its own by
    #: reading the id, and a number it cannot read is a line it will ask about twice.
    held: tuple[Held, ...] = ()
    #: The ready lines a requirement this caller does not have kept out of the ranking
    #: (RK1297). Beside `held` and `undesigned` because it is the third thing that narrows an
    #: offer without narrowing the truth — `ready` still counts these — and apart from both
    #: because it is the only one nothing the caller does will change: a claim expires and a
    #: design gets written, and a PS5 does not arrive because a command was run.
    lacking: tuple[Lacking, ...] = ()
    #: What the declared priority is waiting on, where nothing ready answers it (RK1304).
    #: Empty on every other call — a queue the pick came *from* has nothing to be waiting for,
    #: and a project that declares none has no queue to ask about.
    waiting: tuple[Waiting, ...] = ()
    #: What became of the block the question was scoped to (RK429). Absent on an unscoped
    #: pick, where there is no label to have a state — and carried even when a line *was*
    #: chosen, so a caller reading the payload never has to ask a second command what the
    #: scope it just picked from is.
    standing: Standing | None = None

    @property
    def found(self) -> bool:
        return self.entry is not None

    @property
    def stage(self) -> Stage | None:
        """The scope's state as the one word a caller branches on, or None if unscoped."""
        return None if self.standing is None else self.standing.stage

    @property
    def counts(self) -> str:
        """All four numbers, always: a zero is the fact a reader is checking for."""
        return (
            f"{self.ready} ready, {self.blocked} blocked, "
            f"{self.outside} blocked outside the backlog, "
            f"{self.paused} blocked on paused work"
        )


def pick(
    config: Config,
    block: str | None = None,
    designed: bool = False,
    *,
    backlog: Backlog | None = None,
    claims: bool = True,
    available: Sequence[str] = (),
) -> Choice:
    """Apply the three tiers to the roadmap, and say which one answered.

    ``block`` scopes every part of the answer — the tiers, the counts, the alternatives —
    so that "nothing to pick" is a statement about *that* block (RK40). Unscoped, the
    lowest ready id can live in another block, and reading that as "this block is
    finished" is a mistake the ids being non-sequential makes easy.

    ``designed`` sets aside the ready lines whose marker says the design is unwritten
    (RK83), for a caller who asked to *execute* rather than to plan. It narrows what may
    be chosen and nothing else: ``ready`` still counts every ready line, because the
    number of lines this backlog could start is not a fact the caller's intent changes.

    ``available`` is what the caller says it has, and it is the axis the other two are not
    (RK1297): a line whose `(requires: …)` names anything absent from it is set aside, counted
    and **named**. Empty by default, and that default is the decision — the caller who
    cannot press a button is the one who does not think to say so, and a `pick` that offered
    hardware work to it was the five identical answers this exists to stop. A person at the
    desk says `--have`, and gets the line the agent could not have.

    ``backlog`` answers over files somebody else read — the state a transaction is about to
    write, or a revision (RK104) — and ``claims = False`` asks the question the tiers were
    before RK119: *what do the files alone say*. Both exist for the projection (RK39), which
    is published, has to be idempotent, and is derived from the repository — so a next-ready
    line that moved because a claim in one checkout expired would put a README permanently
    one temp file away from stale, with nothing in any commit to explain it.
    """
    if backlog is None:
        backlog = Backlog.load(config)
    if block is not None and block not in backlog.declared_blocks():
        declared = sorted(backlog.declared_blocks())
        raise KeyError(
            f"no heading declares {config.schema.block_named(block)}"
            # And not every label that is declared (RK296): the caller typed a block, they are
            # not choosing from a menu of the other eighty-nine.
            f"{declares(declared)}"
            # As at the write refusal (RK216): scoping a pick to `A` where `AJ` is declared
            # would otherwise read as "that block is empty" dressed as "that block is absent".
            f"{shading(block, declared)}"
        )
    scope = f" in {config.schema.block_named(block)}" if block else ""
    # Read before the survey and kept whatever the answer is (RK429): the ledger is what
    # tells a finished block from a heading opened before its lines, and the tiers below
    # cannot see it — they rank open lines, and both of those states have none.
    standing = None if block is None else backlog.standing(block)
    considered = [
        entry
        for entry in backlog.roadmap.entries
        if block is None or entry.task.block == block
    ]
    # Over every line in scope and not only the ready ones (RK152): a blocked 🛠 line was
    # never a candidate and is still the line a reader most needs to know somebody is on.
    claimed = (
        {entry.id: entry for entry in claiming.live(config, considered)} if claims else {}
    )
    survey = _survey(backlog, considered, claimed)
    ordered = sorted(survey.ready, key=lambda e: id_order(e.task.id, config.schema))
    # Before the tiers and before `designed`, because a claim is a fact about the checkout
    # while the flag is the caller's intent (RK119) — and because tier 1 would otherwise
    # prefer exactly the held line, its premise being that a 🛠 line is work to continue.
    held = tuple(claimed[e.task.id] for e in ordered if e.task.id in claimed)
    if held:
        ordered = [e for e in ordered if e.task.id not in claimed]
    # Before the tiers, for the claim's own reason (RK1297): tier 1 prefers a 🛠 line, and a
    # started line whose hardware is not on this desk is exactly the one that comes back
    # every call — somebody began it where the controller was, and this caller cannot
    # continue it. Stepped around here, so the tiers rank only what could actually be done.
    has = frozenset(available)
    lacking = tuple(
        # The symptom rides along (RK1490): where this list turns out to be the whole answer,
        # the caller has to judge the line and an id is not a line.
        Lacking(entry.task.id, missing, entry.task.symptom or "")
        for entry in ordered
        if (missing := tuple(one for one in entry.task.requires if one not in has))
    )
    if lacking:
        short = {one.id for one in lacking}
        ordered = [e for e in ordered if e.task.id not in short]
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
        "held": held,
        "lacking": lacking,
        "standing": standing,
        # Asked of the whole survey and not of `ordered` alone (RK1304): the question is what
        # the queue's *blocked* lines are waiting on, and `ordered` is by construction the
        # lines that are waiting on nothing.
        "waiting": _waiting(backlog, config, ordered, considered),
    }
    # **Before the absence, and only where there is nothing else** (RK1490). RK1297 stops
    # offering a line whose requirement is not on this desk and RK1467 made the refusal
    # legible, and between them the caller who can see the half they want needs nothing still
    # has no move but to disbelieve the sentence. So the line is put in front of them, under a
    # tier that says what it is. Not a widening of `--have`: that vocabulary stays a contract,
    # and a caller claiming a requirement it lacks is what would make every later refusal
    # meaningless. What this offers is the reading, and `take` refuses to claim it.
    if not ordered:
        return Choice(
            entry=None,
            tier=None,
            reason=_absence(
                scope,
                open_lines=bool(considered),
                held=held,
                set_aside=set_aside,
                lacking=lacking,
                standing=standing,
                # What each of those words was declared to mean (RK1467), where the project
                # said: a refusal naming a token nobody defined can only be believed.
                means=config.requirement_means,
            ),
            ready=len(survey.ready),
            **counts,
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
class Claim:
    """A line taken, and the marker change that took it (RK119)."""

    #: Absent where the caller named the id (RK149): there was no choice, so there is no tier
    #: and no runner-up to report, and inventing an empty one would read as a pick that found
    #: nothing rather than a pick that never happened.
    choice: Choice | None
    #: Absent when there was nothing to claim — an empty answer, not a refused write.
    change: StatusChange | None = None

    @property
    def taken(self) -> bool:
        return self.change is not None


def take(
    config: Config,
    block: str | None = None,
    designed: bool = False,
    *,
    available: Sequence[str] = (),
) -> Claim:
    """Answer and claim in one indivisible step (RK119).

    The lock is around **both**, and that is the whole mechanism: a pick that answered and
    then flipped the marker would be two commands with the race between them, which is the
    defect one layer along rather than the fix. What the claim consists of is the 🛠 the
    roadmap now carries — durable, and git's to move — plus its date in
    :mod:`roadkeep.claiming`, which is neither.

    Nothing ready is not a failure: the empty answer comes back exactly as `pick` gave it,
    because a caller asking for work and being told there is none got the fact it asked for.
    The marker is written through `set_status`, so every refusal that guards a marker guards
    this one too — a sibling file already stating status, a duplicated id — and a line
    already at 🛠 whose claim expired is re-dated without a write it does not need.

    **The claim is that marker write and nothing else** (RK159). Dating it here as well would
    be a second writer of the one rule this design states out loud — a claim follows the
    marker — and two writers of one rule is how the doors came to disagree to begin with.
    """
    with exclusive(config.root):
        choice = pick(config, block, designed, available=available)
        if choice.entry is None:
            return Claim(choice=choice)
        change = set_status(config, choice.entry.task.id, IN_PROGRESS)
        # The entry is replaced by the line as written, so the answer shows the marker the
        # caller now holds rather than the one it was chosen under.
        return Claim(choice=replace(choice, entry=change.entry), change=change)


def hold(config: Config, task_id: str) -> Claim:
    """Claim the line a caller named, refusing one another worker is already holding (RK149).

    The second door, because a *named* claim is a different act from a chosen one, and the
    difference is only visible on a collision: :func:`take` steps around a live claim because
    it was choosing anyway, and here there is nowhere to step — so the answer is
    :class:`~roadkeep.claiming.AlreadyHeld`, and never a second worker sent at one line.

    What it does not do is judge the line. `pick` never offers blocked work, and a caller
    that named an id may be about to unblock it; the marker door this goes through has always
    allowed that, and a policy here would be this command re-deciding what `status` decides.

    It neither writes the registry nor reads it (RK159, RK160): the claim *and* the refusal
    both belong to the marker write, which is one name for one rule — and the refusal had to
    move there anyway, `status <id> 🛠` being the same write with nothing guarding it.
    """
    with exclusive(config.root):
        return Claim(choice=None, change=set_status(config, task_id, IN_PROGRESS))


def _absence(
    scope: str,
    *,
    open_lines: bool,
    held: tuple[Held, ...],
    set_aside: int,
    lacking: tuple[Lacking, ...] = (),
    standing: Standing | None = None,
    means: Mapping[str, str] | None = None,
) -> str:
    """Why nothing was offered — five sentences, because they are five different states.

    Telling them apart is the whole point of the scope (RK40): a block with nothing left is
    finished, one whose lines are all blocked is not, one whose ready lines are all ideas is
    waiting on a design session, and one whose ready lines are all claimed is waiting on the
    workers holding them — which is the only one of the four that ends by itself.

    The first of those four was itself two (RK429). "Nothing is open in Block C" is what a
    finished block and a heading opened before its lines both produce, and the caller who
    typed the wrong letter reads the same words — so where a label was named, the sentence
    is :attr:`Standing.sentence` and states which. Unscoped there is no label to have a
    state, and the old sentence is still the whole truth.

    The fifth is the one whose remedy is a **person** and not a command (RK1297). Every
    other sentence here ends by somebody shipping, resuming, designing or letting a claim
    go; this one ends by whoever has the hardware asking for the same line, which is why it
    names what is missing rather than what to run — and why it goes first, being the only
    one that tells the caller reading it that the work is not theirs to do.
    """
    if lacking and not held and not set_aside:
        return (
            f"every ready task{scope} needs something this caller does not have: "
            f"{_missing(lacking, means)} — `--have` is how a caller that has one says so"
        )
    if held and not set_aside:
        return f"every ready task{scope} is claimed by a worker who has not finished it"
    if set_aside:
        return (
            f"every ready task{scope} still needs designing, so there is nothing "
            "to implement"
        )
    if not open_lines:
        return f"nothing is open{scope}" if standing is None else standing.sentence
    return f"every open task{scope} is blocked, so there is nothing to start"


def _missing(lacking: Sequence[Lacking], means: Mapping[str, str] | None = None) -> str:
    """Every requirement standing between this caller and the ranking, once each.

    The union and not a line-by-line list: the sentence is about what the caller has to
    acquire, and one word repeated across six lines is one thing to go and get. Which lines
    those are is :attr:`Choice.lacking`, printed under it and named there.

    **With what the project declared each one to be** (RK1467), where it declared anything: a
    requirement is one word on a line, and one word is what a caller then has to decide about
    a whole task. Measured on a project whose `requires: upstream` set aside every ready line;
    what the work needed was a step in an action already in the repository the caller had, and
    the upstream half shrank to a pin bump — which nobody could see, because the word stood
    alone. Once each and never per line, so the sentence stays the size of the vocabulary.
    """
    said = dict.fromkeys(one for entry in lacking for one in entry.missing)
    stated = means or {}
    return ", ".join(
        f"{one} ({stated[one]})" if stated.get(one) else one for one in said
    )


@dataclass(frozen=True, slots=True)
class _Survey:
    """One pass over the lines in scope: who is ready, and who is not and why not."""

    ready: tuple[Entry, ...]
    blocked: int
    outside: int
    stalled: tuple[Stalled, ...]
    paused: int = 0


def _survey(
    backlog: Backlog, considered: list[Entry], claimed: Mapping[str, Held]
) -> _Survey:
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
                    claimed=claimed.get(entry.task.id),
                )
            )
    return _Survey(
        ready=tuple(ready),
        blocked=blocked,
        outside=outside,
        stalled=tuple(stalled),
        paused=paused,
    )


def _waiting(
    backlog: Backlog, config: Config, ordered: list[Entry], considered: list[Entry]
) -> tuple[Waiting, ...]:
    """What the declared priority is waiting on, where nothing ready answers it (RK1304).

    Empty the moment **any** token names a ready line, which is the state `_first`'s second
    tier fires in: the queue was answered, the pick came from it, and a row about what some
    other token is blocked on would be a cost quoted against a question nobody asked. So this
    is the sentence for exactly one state — the one the fall-through already names in prose
    and stopped short of making actionable.

    The blockers are read through :meth:`Backlog.resolve`, which is where :class:`Stalled`
    reads its own: an unsatisfied dep is one answer in this tool and a second walk here would
    be a second answer about what is holding a line.

    **Only the open ones**, unlike :class:`Stalled`, and the difference is what the two rows
    claim: that one names what is holding a line and this one names what would *release* it.
    Nothing now open satisfies an `UNRESOLVABLE` dep by construction (RK432), a `DEFERRED` one
    needs a `resume` before any ship, and an `UNKNOWN` id is a finding rather than a target —
    so naming any of them here would be an offer nothing answers, which is worse than the
    count on its own (RK16). A token left with no id says exactly that.
    """
    queue = declared(config)
    if not queue:
        return ()
    ready = {entry.task.id for entry in ordered}
    named: list[tuple[str, list[Entry]]] = []
    for token in queue.tokens:
        label = config.schema.block_of_dep(Dep(token))
        under = [
            entry
            for entry in considered
            if (entry.task.block == label if label is not None else entry.task.id == token)
        ]
        if any(entry.task.id in ready for entry in under):
            return ()
        if under:
            named.append((token, under))
    out: list[Waiting] = []
    for token, under in named:
        blockers = sorted(
            {
                resolution.dep.id
                for entry in under
                for resolution in backlog.resolve(entry.task)
                if resolution.status is DepStatus.OPEN
            },
            key=lambda one: id_order(one, config.schema),
        )
        out.append(
            Waiting(
                token=token,
                lines=len(under),
                releases=tuple(blockers[:RELEASES]),
                of=len(blockers),
            )
        )
    return tuple(out)


def _first(ordered: list[Entry], config: Config) -> tuple[Entry, Tier, str]:
    """The three tiers, in order, each returning the reason it fired."""
    started = [e for e in ordered if e.task.status == IN_PROGRESS]
    if started:
        return (
            started[0],
            Tier.STARTED,
            f"{started[0].task.id} is already in progress and ready to continue",
        )

    # The roadmap's section where one is declared, and `roadkeep.toml` otherwise (RK325).
    # Named in the reason rather than merely applied: a project that wrote a section and is
    # still being ordered by its config has a fact to learn, and the tier is where it reads.
    queue = declared(config)
    named = "the roadmap's queue" if queue.declared_in == "roadmap" else "declared priority"
    for token in queue.tokens:
        # Typed by the code that types a dep, so `Block X` cannot come to mean two things.
        label = config.schema.block_of_dep(Dep(token))
        if label is not None:
            inside = [e for e in ordered if e.task.block == label]
            if inside:
                return (
                    inside[0],
                    Tier.PRIORITY,
                    f"{named} names Block {label}, whose lowest ready id it is",
                )
            continue
        match = next((e for e in ordered if e.task.id == token), None)
        if match is not None:
            return match, Tier.PRIORITY, f"{named} names {token} and it is ready"

    if queue:
        return (
            ordered[0],
            Tier.LOWEST,
            f"lowest ready id; {named} names nothing ready",
        )
    return ordered[0], Tier.LOWEST, "lowest ready id"


@dataclass(frozen=True, slots=True)
class Picked:
    """What `pick` answers: the choice, and the claim where the call took one (RK1170).

    Three values reached the handler and were rendered there — the choice, the claim and the
    event — so this verb's two registers were a printer in `verbs/querying.py` and a builder in
    `rendering.py`, neither of them where the choice is made. One record carries both, and the
    five sentences it shares with `brief` compose here because those produce rows now.

    `config` is a field and not a parameter, unlike `View.stated`'s: every row this renders needs
    it — the file a line sits on, the claim window, the offer to withdraw a heading — and this
    record is built by the verb that already holds the project.
    """

    config: Config
    choice: Choice
    claim: Claim | None
    event: Mapping[str, object] | None

    def __str__(self) -> str:  # noqa: PLR0912 - the rows are a list, not a branch tree
        """The answer a reader scans, or the reasoned absence of one.

        Nothing ready is an answer and not a failure: the exit stays 0 and the reason carries the
        counts, so a caller can tell *backlog finished* from *everything is blocked*.
        """
        from roadkeep.rendering import (  # noqa: PLC0415 - RK260, the cycle's one direction
            _against_rows,
            _claim_rows,
            _event_rows,
            _held_rows,
            _lacking_rows,
            _stalled_rows,
            _undesigned_rows,
            _waiting_rows,
            _withheld_rows,
        )

        choice, config = self.choice, self.config
        if choice.entry is None:
            return "\n".join(
                [
                    f"nothing to pick: {choice.reason}",
                    f"  backlog  {choice.counts}",
                    *_undesigned_rows(choice),
                    *_lacking_rows(choice),
                    # Under the lines it is about (RK1490): those say which and what for, and
                    # this says what the caller may do about it — the move RK1467 left unbuilt.
                    *_withheld_rows(choice),
                    *_waiting_rows(choice),
                    *_held_rows(choice),
                    *_stalled_rows(choice),
                ]
            )
        entry = choice.entry
        where = f"{config.relative(config.path('roadmap'))}:{entry.lineno}"
        rows = [
            f"{entry.task.id}  Block {entry.task.block}  {entry.task.status}  {where}",
            f"  because  {choice.reason}",
            f"  backlog  {choice.counts}",
            f"  symptom  {entry.task.symptom}",
        ]
        if choice.alternatives:
            rows.append(f"  or       {', '.join(choice.alternatives)}")
        rows += _against_rows(config, entry.task.id)
        rows += _undesigned_rows(choice)
        rows += _lacking_rows(choice)
        # Beside the pick and never instead of it (RK1304): the fall-through is still the right
        # call when the blocker is expensive, and the caller is the one who knows which it is.
        rows += _waiting_rows(choice)
        rows += _held_rows(choice)
        rows += _stalled_rows(choice)
        taken = _claim_rows(self.claim, config)
        rows += taken
        if taken and self.event is not None:
            # Beside the claim and not at the end, which is where `brief` puts it too: an event
            # line after a paragraph of prose is one a hook reader has to hunt for.
            rows += _event_rows(dict(self.event), "  ")
        return "\n".join(rows)

    def payload(self) -> dict[str, object]:
        """The answer as one object, beside `Brief`'s and for the same reason it exists."""
        choice, config = self.choice, self.config
        entry = choice.entry
        return {
            "pick": None
            if entry is None
            else {
                "id": entry.task.id,
                "block": entry.task.block,
                "status": entry.task.status,
                "file": config.relative(config.path("roadmap")),
                "line": entry.lineno,
                "symptom": entry.task.symptom,
                "ref": entry.task.ref,
            },
            "tier": None if choice.tier is None else str(choice.tier),
            "reason": choice.reason,
            "scope": choice.block,
            # Beside `scope` and never instead of it (RK429): the label is what was asked and
            # this is what became of it, so a loop scoped to a block reads one word rather than
            # matching the sentence `reason` states it in.
            "standing": None if choice.standing is None else choice.standing.payload(),
            "alternatives": list(choice.alternatives),
            # What already shipped against the line being offered (RK1439). Published always
            # and printed only where it is non-empty: a key costs a client nothing to skip,
            # where a row costs every reader the same attention on every pick.
            "against": []
            if entry is None
            else list(Backlog.load(config).against(entry.task.id)),
            "ready": choice.ready,
            "blocked": choice.blocked,
            "outside": choice.outside,
            "paused": choice.paused,
            "needs_design": choice.needs_design,
            "undesigned": choice.undesigned,
            # `claimed` on a stalled line and `held` beside it are two facts with two names
            # (RK152): one is a line somebody is on that nothing could offer, the other is a
            # candidate the ranking stepped around.
            "stalled": [
                {
                    "id": one.id,
                    "blockers": list(one.blockers),
                    "claimed": None
                    if one.claimed is None
                    else {"age": round(one.claimed.age), "since": one.claimed.since},
                }
                for one in choice.stalled
            ],
            "held": [
                {"id": one.id, "age": round(one.age), "since": one.since}
                for one in choice.held
            ],
            # The ready lines this caller cannot finish, and what each would take (RK1297).
            # A list and not a count, for `held`'s reason and one more: a loop that hands
            # work back to a person has to be able to say *which* work and *what for*.
            # `symptom` beside them (RK1490), for the reason the row carries it: where this
            # list is the whole answer, the question in front of the caller is whether the
            # part they want needs the word, and that is a judgement about the line.
            "lacking": [
                {"id": one.id, "missing": list(one.missing), "symptom": one.symptom}
                for one in choice.lacking
            ],
            # What the declared priority is waiting on (RK1304), where nothing ready answers
            # it. `[]` on every other call and never omitted: a consumer reading a missing key
            # cannot tell "the queue was answered" from "an older server".
            "waiting": [
                {
                    "token": one.token,
                    "lines": one.lines,
                    "releases": list(one.releases),
                    # The roster bounded and the count whole, which is RK1301's rule: a cut
                    # list is never read as a short one.
                    "of": one.of,
                }
                for one in choice.waiting
            ],
            "claimed": None
            if self.claim is None
            else {
                "taken": self.claim.taken,
                "from": None if self.claim.change is None else self.claim.change.before,
                "to": None if self.claim.change is None else self.claim.change.after,
            },
            "event": None if self.event is None else dict(self.event),
        }
