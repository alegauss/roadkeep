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
"""

from __future__ import annotations

import textwrap
from dataclasses import dataclass

from roadkeep.backlog import Backlog, Readiness, Resolution
from roadkeep.config import Config, Scope
from roadkeep.document import Document
from roadkeep.graph import Chain, Graph, Leverage
from roadkeep import scoping
from roadkeep.picking import pick
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
    """`pick` found no ready task, so there is nothing to start. Not a failure."""

    def __init__(self, reason: str) -> None:
        super().__init__(f"nothing to brief: {reason}")


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
    #: Set when the id came from `pick` rather than from the caller, with its reason.
    picked: str = ""

    @property
    def task(self) -> Task:
        return self.view.task


def brief(
    config: Config, task_id: str | None = None, block: str | None = None
) -> Brief:
    """Join every answer about one task. Reads four files at most; writes none.

    ``block`` scopes the pick when no id is given (RK40), so "start the next thing in
    Block C" is one call whose absence of an answer is about Block C.
    """
    picked = ""
    if task_id is None:
        choice = pick(config, block)
        if choice.entry is None:
            raise NothingToBrief(choice.reason)
        task_id, picked = choice.entry.task.id, choice.reason

    view = show(config, task_id)
    backlog = Backlog.load(config)
    graph = Graph.of(backlog)
    entry = backlog.entry(task_id)
    # A shipped task has no readiness and no deps left to resolve: the ledger carries
    # neither, which is the schema saying a shipped line has no dependency to state.
    task = entry.task if entry is not None else view.task
    readiness = backlog.readiness(task) if entry is not None else Readiness.READY
    return Brief(
        view=view,
        readiness=readiness,
        deps=backlog.resolve(task) if entry is not None else (),
        chains=graph.chains(task_id)[:CHAINS] if entry is not None else (),
        leverage=graph.leverage(task_id),
        non_goals=non_goals(config, backlog.roadmap),
        picked=picked,
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
