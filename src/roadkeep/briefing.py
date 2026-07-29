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

import re
from dataclasses import dataclass

from roadkeep.backlog import Backlog, Readiness, Resolution
from roadkeep.config import Config
from roadkeep.document import Document
from roadkeep.graph import Chain, Graph, Leverage
from roadkeep.picking import pick
from roadkeep.schema import Task
from roadkeep.showing import View, show

#: How many blocker chains a brief carries. Lower than the graph's own limit on purpose:
#: a brief is read to start work, and the second chain is already context, not an answer.
CHAINS = 2

#: Any heading whose text starts like this holds the non-goals. A prefix match rather than
#: a config key, because both live corpora already write it and neither writes it exactly:
#: this repository has "## Non-goals", Shio has "## Non-goals (do NOT add as tasks)".
_NON_GOALS = re.compile(r"^non-goals?\b", re.IGNORECASE)
_BOLD_LEAD = re.compile(r"\*\*(.+?)\*\*")
_BULLET = re.compile(r"^[-*+] (?P<rest>.*)$")


class NothingToBrief(KeyError):
    """`pick` found no ready task, so there is nothing to start. Not a failure."""

    def __init__(self, reason: str) -> None:
        super().__init__(f"nothing to brief: {reason}")


@dataclass(frozen=True, slots=True)
class Brief:
    """One task, and every derived fact needed to start it."""

    view: View
    readiness: Readiness
    deps: tuple[Resolution, ...]
    chains: tuple[Chain, ...]
    leverage: Leverage
    non_goals: tuple[str, ...]
    #: Set when the id came from `pick` rather than from the caller, with its reason.
    picked: str = ""

    @property
    def task(self) -> Task:
        return self.view.task


def brief(config: Config, task_id: str | None = None) -> Brief:
    """Join every answer about one task. Reads four files at most; writes none."""
    picked = ""
    if task_id is None:
        choice = pick(config)
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
        non_goals=non_goals(backlog.roadmap),
        picked=picked,
    )


def non_goals(document: Document) -> tuple[str, ...]:
    """The lead of each bullet under the non-goals heading, in file order.

    The lead and not the bullet: what keeps a proposal inside scope is *that* the line
    exists, and the sentence arguing it is already in the file the caller can open.
    """
    heading = next((h for h in document.headings if _NON_GOALS.match(h.text)), None)
    if heading is None:
        return ()
    out: list[str] = []
    for line in document.lines[heading.lineno :]:
        body = line.rstrip("\r\n")
        if body.startswith("#"):
            break  # the next heading ends the section, whatever its level
        bullet = _BULLET.match(body)
        if bullet is None:
            continue
        out.append(_lead(bullet.group("rest")))
    return tuple(out)


def _lead(text: str) -> str:
    """The bolded head of a bullet, or its first sentence — never a rewrite of either."""
    bold = _BOLD_LEAD.search(text)
    if bold:
        return bold.group(1).rstrip(".")
    head, _, _ = text.partition(". ")
    return head.rstrip(".")
