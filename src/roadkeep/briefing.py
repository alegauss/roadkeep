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

from roadkeep.backlog import Backlog, DepStatus, Readiness, Resolution, Standing
from roadkeep.budgeting import Budget, budget_of
from roadkeep.config import Config, Scope
from roadkeep.kernel.document import Document
from roadkeep.graph import Chain, Graph, Leverage
from roadkeep.history import Commit
from roadkeep import scoping
from roadkeep.claiming import Held
from roadkeep.locking import exclusive
from roadkeep.picking import Choice, Claim, hold, pick, take
from roadkeep.kernel.schema import Task
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

    def __init__(
        self,
        reason: str,
        held: tuple[Held, ...] = (),
        standing: Standing | None = None,
    ) -> None:
        self.held = held
        #: What became of the block this was scoped to (RK429), where one was named. The
        #: sentence above already states it; this is the same fact as a word, so a loop
        #: driving a block to completion branches on `finished` rather than on English.
        self.standing = standing
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
class Settled:
    """A dep that shipped **after** this design was last revised (RK1163).

    Measured on a real run. A task asked whether a check should widen, and its rationale argued
    both sides — widening risks a report full of findings about work somebody is still writing,
    which is the noise that gets a check switched off. Its dep then shipped a unique index, and
    that deleted one side of the trade-off: what was left to report could no longer be anybody's
    unfinished draft. The section still read as an open question, and `brief` handed it over
    verbatim beside `deps_resolved: shipped`. Both facts were on screen and nothing joined them.

    **A date and not a judgement.** What changed is in the dep's own commit, and saying which
    part of a design it settles would be this tool writing prose about a trade-off (L4). So the
    fact is the ordering — the section predates the ship — and the reader decides.

    Empty wherever git cannot answer, which is a checkout with no history and a project whose
    prose file is untracked: a note that cannot be dated is a guess, and this is a query.
    """

    dep: str
    #: The commit that shipped it, so the reader can go straight to what changed.
    shipped: Commit
    #: The last commit that touched this design, which is what "predates" is measured against.
    revised: Commit


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
    #: Deps that shipped after this design was last revised (RK1163) — the question a
    #: dependency may have answered, said as an ordering and never as a claim about the prose.
    settled: tuple[Settled, ...] = ()
    #: What the **ship** this brief is starting will have for prose (RK1174). The same field of
    #: the same task, measured under the ledger's grammar: `[limits.changelog]` and a line with
    #: no deps and no pointer in it. Two numbers for what an author thinks of as one thing, and
    #: only the one that does not apply was shown before the write — measured across four ships
    #: in one session, three of them refused for `why.too-long` on the first attempt.
    #:
    #: None where the project declares no changelog, and on a shipped line, which has no ship
    #: left to compose for.
    shipping: Budget | None = None
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

    def stated(self, config: Config) -> str:
        """Everything needed to start this task, as a reader is told it (RK29).

        Beside :meth:`payload` since RK1170, and the last of the verbs that task measured: 20
        prints in the handler against a builder in `rendering.py`, one answer in two files with
        neither of them where the brief is composed. The five sentences shared with `pick` compose
        here because those produce rows, which is what the two prerequisite slices bought.

        **Bounded, and that is the claim this file exists to keep.** An answer that fits in a tool
        result costs nothing to consult twice; one that does not gets replaced by re-reading the
        file, which is the 5k tokens this verb exists to stop spending — so the non-goals are
        elided with a count and the budget is one line rather than the whole table.
        """
        from roadkeep.rendering import (  # noqa: PLC0415 - RK260, the cycle's one direction
            _claim_event,
            _claim_rows,
            _event_rows,
            _held_rows,
            _leverage_rows,
        )
        from roadkeep.sections import heading_of  # noqa: PLC0415 - RK260

        view, task = self.view, self.task
        rows = [
            f"{task.id}  Block {task.block}  {task.status}  {self.readiness}  "
            f"{view.file}:{view.entry.lineno}"
        ]
        if self.picked:
            rows.append(f"  picked   {self.picked}")
        if self.choice is not None:
            # The ids a live claim was stepped around (RK154), on the door a session starts a task
            # with: without them the caller cannot tell one of them is its own.
            rows += _held_rows(self.choice)
        taken = _claim_rows(self.claim, config)
        rows += taken
        event = _claim_event(self.claim, config)
        if taken and event is not None:
            # Beside the claim and not at the end: the rationale section closes this output, and
            # an event line after a paragraph of prose is one a hook reader has to hunt for.
            rows += _event_rows(event, "  ", config=config)
        rows.append(f"  symptom  {task.symptom}")
        rows.append(f"  why      {task.why}")
        if self.budget is not None:
            # One line, and only the field an amend rewrites (RK190): the whole table is
            # `budget`'s answer, and a brief that grew one would stop being a bounded one.
            why = self.budget.share("why")
            # The same figure `budget` states, off the same `Share` (RK245): a brief that named
            # the whole field's aim beside this line's remainder would be the second answer.
            rows.append(
                f"  budget   why {why.left} of {why.allowed} left, {why.aimed}, "
                f"{self.budget.prose} for prose"
            )
        if self.shipping is not None:
            # The allowance for the write this brief is starting, which is not the one above
            # (RK1174): a `ship` writes a ledger line, whose limit is `[limits.changelog]` and
            # whose structure carries no deps and no pointer. Measured across four ships in one
            # session, three refused for `why.too-long` on the first attempt — a refusal that
            # names the arithmetic and cannot arrive early, which is what this line is for.
            #
            # Printed only where it **differs**: two numbers for one field is the fact worth
            # seeing, and repeating the same one under another name teaches nobody anything.
            ship = self.shipping.share("why")
            if self.budget is None or ship.allowed != self.budget.share("why").allowed:
                rows.append(
                    f"  shipping why {ship.left} of {ship.allowed} left on the ledger line a "
                    f"`ship` writes, which is the limit that refuses it"
                )
        settled = {one.dep: one for one in self.settled}
        for resolution in self.deps:
            rows.append(
                f"  dep      {resolution.dep.id}  {resolution.status}  {resolution.detail}"
            )
            landed = settled.get(resolution.dep.id)
            if landed is not None:
                # The ordering and never a claim about the prose (RK1163): the design below was
                # last written before this dep shipped, so a trade-off it argues may already be
                # decided — and what decided it is in that commit, which is what this names.
                rows.append(
                    f"           shipped {landed.shipped.date[:10]} in "
                    f"{landed.shipped.short}, after this design was last written "
                    f"({landed.revised.date[:10]})"
                )
        rows += [f"  chain    {chain.render(task.id)}  — {chain.detail}" for chain in self.chains]
        if not view.shipped:
            # What shipping this would unblock, which a shipped line has already done (RK324):
            # `unblocks 0 of 14 open` beside a checkmark is a cost quoted for work that happened,
            # and the readiness word above is the whole answer a caller needs about it.
            rows += _leverage_rows(self.leverage)
        rows += [
            f"  path     {one.path}{'' if one.exists else '  (missing)'}" for one in view.paths
        ]
        rows += [f"  not      {lead}" for lead in self.non_goals.leads]
        if self.non_goals.elided:
            # Where the list was cut, and not silently: a bounded list that reads as the whole
            # one is a proposal made against a scope it never saw (RK68).
            rows.append(f"  not      … and {self.non_goals.elided} more under Non-goals")
        if view.section is not None:
            rows += ["", heading_of(config.schema, view.section), "", view.section.body]
        else:
            rows.append(f"  section  none — {view.section_absence}")
        return "\n".join(rows)

    def payload(self, config: Config) -> dict[str, object]:
        """The same answer as data, with the whole budget table and every count (RK29).

        Beside :meth:`stated` and deliberately wider: a tool result is read by something that
        can hold it, so what the printed register elides with a count this carries in full —
        the non-goals, both allowances, and the commits behind a settled dep.
        """
        from roadkeep.rendering import (  # noqa: PLC0415 - RK260
            _claim_event,
            _dated_json,
        )

        return {
            **self.view.payload(),
            "readiness": str(self.readiness),
            "picked": self.picked or None,
            "deps_resolved": [
                {
                    "dep": r.dep.id,
                    "kind": str(r.kind),
                    "status": str(r.status),
                    "detail": r.detail,
                    # Where this dep shipped after the design was last written (RK1163), the two
                    # commits that say so — beside the resolution rather than in a list of their
                    # own, because it is a fact *about* this dep and a consumer reading the row
                    # would otherwise join two arrays to find it.
                    **{
                        "settled_since": {
                            "shipped": _dated_json(one.shipped),
                            "revised": _dated_json(one.revised),
                        }
                        for one in self.settled
                        if one.dep == r.dep.id
                    },
                }
                for r in self.deps
            ],
            "chains": [
                {
                    "path": [self.task.id, *(hop.target for hop in c.hops)],
                    "end": str(c.end),
                    "detail": c.detail,
                }
                for c in self.chains
            ],
            "unblocks": {
                "count": self.leverage.count,
                "of": self.leverage.of,
                "transitive": list(self.leverage.transitive),
            },
            "non_goals": list(self.non_goals.leads),
            "non_goals_elided": self.non_goals.elided,
            # The whole table here and one line on stdout (RK190): a tool result is read by
            # something that can hold it, and this is the number the next write is measured on.
            "budget": None if self.budget is None else self.budget.payload(),
            # The same shape for the write about to be made (RK1174), and always published where it
            # exists — unlike the printed line, which is silent when the two agree: a key costs a
            # client nothing to skip and a consumer comparing them wants both numbers present.
            "shipping": None if self.shipping is None else self.shipping.payload(),
            # Same key and same shape as `pick`'s (RK154): one fact spelled two ways is two facts.
            "held": [{"id": h.id, "age": round(h.age), "since": h.since} for h in self.held],
            "claimed": None
            if self.claim is None or self.claim.change is None
            else {
                "taken": True,
                "from": self.claim.change.before,
                "to": self.claim.change.after,
            },
            "event": _claim_event(self.claim, config),
        }


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
            raise NothingToBrief(chosen.reason, chosen.held, chosen.standing)
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
        raise NothingToBrief(
            "" if taken.choice is None else taken.choice.reason,
            held,
            None if taken.choice is None else taken.choice.standing,
        )
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
        settled=_settled(config, view, backlog.resolve(task) if entry is not None else ()),
        budget=None if view.shipped else budget_of(config, task, open_line=True),
        shipping=None
        if view.shipped or not config.has("changelog")
        else budget_of(
            config, task, open_line=False, schema=config.schema_for("changelog")
        ),
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


def _settled(config: Config, view: View, deps: tuple[Resolution, ...]) -> tuple[Settled, ...]:
    """Which shipped deps landed after this design was last written (RK1163).

    Only the **shipped** ones, because an open dep has settled nothing and its date would be a
    question about work in progress. Only where the task has a section: there is no design to
    predate otherwise, and `brief` on a line whose prose is unwritten already says so.

    Two git reads per shipped dep at most, on a command a session runs once to start a task —
    and none at all for the common case of a task whose deps are open or absent. A failure to
    read history is silence, never an error: `git_available` is the guard the rest of this
    package uses and a note nobody can date is the guess L4 keeps out.
    """
    if view.section is None or not deps:
        return ()
        # Deferred for RK260's reason: `history` runs git, and no successful write path reaches it.
    from roadkeep.history import (  # noqa: PLC0415
        HistoryUnavailable,
        git_available,
        origin_of,
        precedes,
        revisions_of,
    )

    if not git_available():
        return ()
    if view.section_role is None or not config.has(view.section_role):
        return ()
    prose = config.path(view.section_role)
    if not prose.is_file():
        return ()
    # The section's **span** and never a needle for its heading: a heading appears in the diff of
    # the commit that wrote it and of nothing else, so a body-only `section amend` — the ordinary
    # way a design is revised — would be invisible and every design would read as unrevised since
    # the day it was filed. RK1126 measured that asymmetry one verb over.
    try:
        written = revisions_of(config, prose, view.section.first, view.section.last)
    except (HistoryUnavailable, OSError):
        # A project git cannot answer for — no repository, a checkout too shallow — says
        # nothing rather than raising: this is a note on a query, and `brief` is the command a
        # session starts a task with.
        return ()
    if not written:
        return ()
    revised = written[-1]
    out: list[Settled] = []
    for one in deps:
        if one.status is not DepStatus.SHIPPED:
            continue
        try:
            shipped = origin_of(config, one.dep.id).shipped_in
        except (HistoryUnavailable, OSError):
            continue
        # Ancestry and not dates (RK1163): two commits in one second carry the same timestamp,
        # and a rebase can order dates against the history. `precedes` answers the question the
        # note is about — was this design written before that ship landed — and a design revised
        # *in* the shipping commit is excluded, having read what changed.
        if (
            shipped is not None
            and revised.sha != shipped.sha
            and precedes(config, revised.sha, shipped.sha)
        ):
            out.append(Settled(dep=one.dep.id, shipped=shipped, revised=revised))
    return tuple(out)
