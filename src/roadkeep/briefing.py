"""Everything it costs to start one task, in one call (RK29).

Starting RK1 in this repository cost reading `ROADMAP.md` and `IMPROVEMENTS.md` end to end
— some 5k tokens to learn one task, of which one line and one paragraph mattered. `pick`
(RK11) and `show` (RK12) each answer half; this composes them with the resolved deps
(RK28), the blocker chain (RK13) and the non-goals, so the answer to "start work" is a
single tool result.

**Bounded output is the point**, not a side effect: an answer that fits in a tool result
is an answer that costs nothing to consult twice, and one that does not fit gets replaced
by re-reading the file — which is the cost this removes. So the section is capped by its
own word budget (RK9), the chains by the graph's own limit, and the non-goals are carried
as *leads only*: enough to keep a proposal inside scope, not the paragraph that argues it.

Nothing here is stored and nothing is composed of new prose (L4): every field is another
module's answer, gathered in one place. Call it with no id and it briefs whatever `pick`
would choose, which makes the first call of a session the only one.

What it carries of the pick is the pick's own :class:`~roadkeep.picking.Choice` and not a
sentence copied out of it (RK154): a held line has to be *named* here for the reason it is
named there — a claim carries no owner, so an id is the only thing a caller recognises its own
by — and a field lifted out one at a time is a second place to keep in step.

**Which is why the claim has to be reachable from here** (RK149). RK119 made answering "what
next" a write so two agents get two lines, and put the flag on `pick` — the command a session
following the skill does not call, this one being the door that starts a task in one call. So
``claim`` takes the line as well as describing it, and the module's promise narrows from
*writes none* to *writes one marker, and only when asked*. The two callers it serves are not
the same act: with no id the claim is `pick`'s, which steps around what somebody else holds,
and with an id it is the caller's own assertion, which is refused where a live claim already
answers for that line (:func:`roadkeep.picking.hold`).
"""

from __future__ import annotations

import textwrap
from dataclasses import dataclass

from roadkeep.backlog import Backlog, Readiness, Resolution
from roadkeep.budgeting import Budget, budget_of
from roadkeep.config import Config, Scope
from roadkeep.document import Document
from roadkeep.graph import Chain, Graph, Leverage
from roadkeep import scoping
from roadkeep.claiming import Held
from roadkeep.locking import exclusive
from roadkeep.picking import Choice, Claim, hold, pick, take
from roadkeep.schema import Task
from roadkeep.showing import View, show

#: How many blocker chains a brief carries. Lower than the graph's own limit on purpose:
#: a brief is read to start work, and the second chain is already context, not an answer.
CHAINS = 2

#: How many non-goals a brief carries, for the same reason (RK68): the list binds what may be
#: proposed, and a section long enough to need scrolling is the file back. Two live corpora
#: write seven and eight, so this is headroom over both rather than a cut anyone will meet.
NON_GOALS = 12

#: What a cut lead ends with. A space before it, so the mark reads as the tool's and not as
#: an author's ellipsis — the cut has to be visible where it happens, never silent.
ELLIPSIS = " …"


class NothingToBrief(KeyError):
    """`pick` found no ready task, so there is nothing to start. Not a failure.

    Carries the held ids where a claim is what emptied the answer (RK154): "every ready task
    is claimed by a worker who has not finished it" is the one absence in this design a
    caller cannot act on without them, a claim naming no owner and its own being the one it
    would otherwise ask about again next turn.
    """

    def __init__(self, reason: str, held: tuple[Held, ...] = ()) -> None:
        self.held = held
        #: The bare sentence, before this class wraps it (RK409). Kept as a field because
        #: `brief --json` answers this branch too now, and recovering it from `str(self)`
        #: means stripping a prefix and `KeyError`'s own quoting — two spellings of the
        #: reason, one of which goes wrong the first time either half is reworded.
        self.reason = reason
        named = ", ".join(f"{one.id} ({one.since} ago)" for one in held)
        super().__init__(f"nothing to brief: {reason}" + (f" — held: {named}" if named else ""))


@dataclass(frozen=True, slots=True)
class NonGoals:
    """The scope a proposal has to stay inside: the leads carried, and what was left.

    Two fields because a bounded list that does not say it is bounded reads as the whole
    list — the failure this is the fix for, one level up (RK68).
    """

    leads: tuple[str, ...] = ()
    #: How many bullets the section held beyond the ones carried. 0 means these are all.
    elided: int = 0


@dataclass(frozen=True, slots=True)
class Brief:
    """One task, and every derived fact needed to start it."""

    view: View
    readiness: Readiness
    deps: tuple[Resolution, ...]
    chains: tuple[Chain, ...]
    leverage: Leverage
    non_goals: NonGoals
    #: The pick that chose this id, absent where the caller named one (RK154). The whole
    #: answer and not the sentence it used to be: `held` is the ids a live claim was stepped
    #: around, and with no owner field a caller recognises its own only by reading them. One
    #: field rather than five, so the next question `pick` already answers is a field here and
    #: not a change — while what this *prints* stays bounded, which is why the counts are left
    #: to the command that is about them.
    choice: Choice | None = None
    #: The line taken, where the caller asked for it (RK149). Absent otherwise, so a brief
    #: that claimed nothing cannot be read as one that did.
    claim: Claim | None = None
    #: What this line has left for prose (RK190). Here because a brief is the call that
    #: starts a task, and the next write on the line it handed over is an `amend` — so the
    #: number that would otherwise arrive as a refusal is already on the desk. None for a
    #: shipped task: the ledger is a different grammar and holds no line to amend.
    budget: Budget | None = None

    @property
    def task(self) -> Task:
        return self.view.task

    @property
    def picked(self) -> str:
        """Why this id was chosen, or empty where the caller named it."""
        return "" if self.choice is None else self.choice.reason

    @property
    def held(self) -> tuple[Held, ...]:
        """The ready lines a live claim kept out of the pick this brief came from."""
        return () if self.choice is None else self.choice.held


def brief(
    config: Config,
    task_id: str | None = None,
    block: str | None = None,
    designed: bool = False,
    claim: bool = False,
) -> Brief:
    """Join every answer about one task, and take it where the caller asked to.

    ``block`` scopes the pick when no id is given (RK40), so "start the next thing in
    Block C" is one call whose absence of an answer is about Block C. ``designed`` narrows
    it to work whose design is written (RK83) — the two flags together are what "execute
    Block C" means, and neither reaches a brief the caller addressed by id.

    ``claim`` moves the marker to in-progress (RK149). One lock covers the write **and** the
    reading that follows it, so the brief describes the line as it was taken rather than as
    some later state found it — the four reads being milliseconds, which is what makes
    holding the write lock across them free.
    """
    if claim:
        with exclusive(config.root):
            return _gather(config, *_claimed(config, task_id, block, designed))
    if task_id is None:
        chosen = pick(config, block, designed)
        if chosen.entry is None:
            raise NothingToBrief(chosen.reason, chosen.held)
        return _gather(config, chosen.entry.task.id, chosen, None)
    return _gather(config, task_id, None, None)


def _claimed(
    config: Config, task_id: str | None, block: str | None, designed: bool
) -> tuple[str, Choice | None, Claim]:
    """Take a line, by the tiers or by the id the caller gave, and say which happened."""
    if task_id is not None:
        return task_id, None, hold(config, task_id)
    taken = take(config, block, designed)
    if taken.choice is None or taken.choice.entry is None:
        # The same absence `pick` reports and not a refusal: a caller asking for work and
        # being told there is none got the fact it asked for, and nothing was written.
        held = () if taken.choice is None else taken.choice.held
        raise NothingToBrief("" if taken.choice is None else taken.choice.reason, held)
    return taken.choice.entry.task.id, taken.choice, taken


def _gather(
    config: Config, task_id: str, chosen: Choice | None, claim: Claim | None
) -> Brief:
    """Every derived fact about one task, joined. This half reads and never writes."""
    view = show(config, task_id)
    backlog = Backlog.load(config)
    graph = Graph.of(backlog)
    entry = backlog.entry(task_id)
    # A shipped task has no deps left to resolve: the ledger carries none, which is the
    # schema saying a shipped line has no dependency to state. Its readiness is the ledger's
    # own answer and not `ready` (RK324) — this is the command a session starts work with, so
    # the one word it leads with is the one a caller acts on, and `show` already says shipped.
    task = entry.task if entry is not None else view.task
    readiness = backlog.readiness(task) if entry is not None else Readiness.SHIPPED
    return Brief(
        view=view,
        readiness=readiness,
        deps=backlog.resolve(task) if entry is not None else (),
        chains=graph.chains(task_id)[:CHAINS] if entry is not None else (),
        leverage=graph.leverage(task_id),
        non_goals=non_goals(config, backlog.roadmap),
        choice=chosen,
        claim=claim,
        budget=None if view.shipped else budget_of(config, task, open_line=True),
    )


def non_goals(config: Config, document: Document) -> NonGoals:
    """The lead of each bullet under the non-goals heading, in file order and bounded.

    The lead and not the bullet: what keeps a proposal inside scope is *that* the line
    exists, and the sentence arguing it is already in the file the caller can open. *Which*
    characters are the lead is `scoping`'s answer and not one guessed here (RK68) — the
    module that writes a non-goal is the one that says what its address is.

    Bounded twice, for the reason the chains stop at two and a section has a word budget:
    each lead is cut to the project's own `[non_goals]` limit (L6) with the cut *shown*, and
    a list past :data:`NON_GOALS` reports how many it left. A field with no limit at all is
    a forty-bullet section arriving in place of the file this call exists to replace.
    """
    limit = (config.non_goals or Scope()).lead
    every = scoping.leads(document)
    return NonGoals(
        leads=tuple(
            textwrap.shorten(lead, width=limit, placeholder=ELLIPSIS)
            for lead in every[:NON_GOALS]
        ),
        elided=max(0, len(every) - NON_GOALS),
    )
