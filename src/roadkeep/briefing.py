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
from collections.abc import Sequence
from dataclasses import dataclass, field

from roadkeep.backlog import Backlog, DepStatus, Readiness, Resolution, Standing
from roadkeep.budgeting import Budget, budget_of
from roadkeep.config import Config, Scope
from roadkeep.kernel.document import Document
from roadkeep.graph import Chain, Graph, Leverage
from roadkeep.history import Commit
from roadkeep import criteria, scoping
from roadkeep.claiming import Held
from roadkeep.locking import exclusive
from roadkeep.picking import Choice, Claim, Lacking, Waiting, hold, pick, take
from roadkeep.kernel.schema import Task
from roadkeep.remaining import Clause
from roadkeep.shipping import as_recorded, recording_cost, supersession_cost
from roadkeep.showing import View, show

#: How many blocker chains a brief carries. Lower than the graph's own limit on purpose:
#: a brief is read to start work, and the second chain is already context, not an answer.
CHAINS = 2

#: How many non-goals a brief carries, for the same reason (RK68): the list binds what may be
#: proposed, and a section long enough to need scrolling is the file back. Two live corpora
#: write seven and eight, so this is headroom over both rather than a cut anyone will meet.
NON_GOALS = 12

#: How many of the ids a task unblocks a brief carries (RK1301). The **count** is the answer —
#: it ranks this line against every other one and a caller reads it once — and the roster is
#: the file back: measured on quickshell, a fresh eighty-one-line backlog, where the first task
#: answered with seventy-nine ids spelled out, in a read RK29 bounded to a tool result and
#: RK1286 gave a ceiling. The case where the list is longest is exactly the case where it says
#: least, a task early in the graph unblocking essentially everything.
#:
#: `deps <id>` answers the roster whole and is where a caller who wants it goes. This number
#: bounds the printed row too, so the two registers cannot come to disagree about how much of
#: it a brief shows — it was the printer's own constant before it was a bound on the payload.
UNBLOCKS = 4

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
        lacking: tuple[Lacking, ...] = (),
    ) -> None:
        self.held = held
        #: The ready lines this caller has no way to finish, and what each would take
        #: (RK1297). Carried for `held`'s reason and one further: a claim ends by itself,
        #: and this absence ends only when the ids reach somebody who has the thing — so a
        #: caller that cannot name them cannot even hand the work over.
        self.lacking = lacking
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
        # Beside the held ids and on the same line, because this register is one string
        # (RK1297): the sentence already says a requirement is missing, and these are the
        # lines it is missing *for* — the half a caller needs to hand the work to somebody.
        short = ", ".join(f"{one.id} ({', '.join(one.missing)})" for one in lacking)
        super().__init__(
            f"nothing to brief: {reason}"
            + (f" — held: {named}" if named else "")
            + (f" — absent: {short}" if short else "")
        )


@dataclass(frozen=True, slots=True)
class DoneWhen:
    """What would finish this task and what would finish its block (RK1265, RK1268).

    :class:`NonGoals`' two fields for its reason, and a third thing this one has to state
    without a field — **an empty list is not an empty answer here**. A block nobody wrote a
    criterion for and a block whose criteria were all dropped are different facts, and `brief`
    prints neither row rather than inventing a sentence about which: the difference is
    `criterion list`'s to report, where a caller went to ask.

    Two lists and not one, because they are two altitudes and the answer would otherwise
    conflate them: the block's says when the body of work is finished and the task's own says
    when this line is, and an agent starting the line is asking the second.
    """

    leads: tuple[str, ...] = ()
    #: How many the block's list held beyond the ones carried. 0 means these are all.
    elided: int = 0
    #: The task's own list, addressed by its id (RK1268), bounded the same way.
    own: tuple[str, ...] = ()
    #: How many the task's own list held beyond the ones carried. 0 means these are all.
    own_elided: int = 0


@dataclass(frozen=True, slots=True)
class NonGoals:
    """The scope a proposal has to stay inside: the leads carried, and what was left.

    Two fields because a bounded list that does not say it is bounded reads as the whole
    list — the failure this is the fix for, one level up (RK68).
    """

    leads: tuple[str, ...] = ()
    #: How many bullets the section held beyond the ones carried. 0 means these are all.
    elided: int = 0

    def stated(self, config: Config) -> str:
        """The list at the moment a task is proposed (RK69), as a reader is told it.

        Beside :meth:`payload` since RK1170. The rows take the shape `brief` prints, so the
        list is recognisable as the same list and not as a second one that happens to agree
        today — which is what a second projection of a scope would be.
        """
        where = config.relative(config.path("roadmap"))
        if not self.leads:
            return f"{where}: no non-goals — nothing here says what may not be proposed"
        # A project that has not opted in can still be read (RK70), and the report says which
        # it is: `add` is what `[non_goals]` gates, and a listing that hid the difference would
        # let a reader take an ungoverned list for an enforced one.
        ungoverned = "" if config.non_goals is not None else "  read-only: no [non_goals]"
        rows = [f"{where}  {len(self.leads)} non-goal(s){ungoverned}"]
        rows += [f"  not      {lead}" for lead in self.leads]
        if self.elided:
            rows.append(f"  not      … and {self.elided} more under Non-goals")
        return "\n".join(rows)

    def payload(self, config: Config) -> dict[str, object]:
        return {
            "file": config.relative(config.path("roadmap")),
            # A project that has not opted in can still be read — `add` is what `[non_goals]`
            # gates (RK70), and refusing the read too would leave the scope of two live corpora
            # unaskable.
            "governed": config.non_goals is not None,
            "non_goals": list(self.leads),
            "non_goals_elided": self.elided,
        }


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
    #: What would finish **this task's block** (RK1265), as leads in file order and bounded
    #: the way the non-goals are. Beside them because they are the same kind of statement
    #: pointed opposite ways — one binds what may be proposed, the other says when the body
    #: of work is done — and a task starts against both or against neither.
    done_when: DoneWhen = field(default_factory=lambda: DoneWhen())
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
    #: What the **decision** that same ship may file will have for prose (RK1275). Its own
    #: field and not a clause of the row above, because it is not that sentence at all: a
    #: `--decides` writes a line in the decisions role, under that role's own limits, and the
    #: one sentence this format asked an author to compose blind was the one recording what
    #: outlives the code. None where the project declares no such role.
    deciding: Budget | None = None
    #: What this line has left for prose (RK190). Here because a brief is the call that
    #: starts a task, and the next write on the line it handed over is an `amend` — so the
    #: number that would otherwise arrive as a refusal is already on the desk. None for a
    #: shipped task: the ledger is a different grammar and holds no line to amend.
    budget: Budget | None = None
    #: What this task's design says would prove it done, and how many sites each clause
    #: matches **now** (RK1184, RK1185). A count and a quotation, never the files behind
    #: them: this answer is bounded to a tool result, and the addresses are what `evidence`
    #: is for once the work is under way.
    #:
    #: Empty where the design declares no criterion, and that is answered with silence: most
    #: tasks state one in prose and always have, so printing an absence every turn is a nag
    #: this tool has no standing to make.
    criterion: tuple[tuple[Clause, int], ...] = ()
    #: What has already **landed** of this task, as the ledger records it (RK1226). One string
    #: per `ship --part`, in the order the ledger holds them, and empty for the ordinary line
    #: that has shipped nothing.
    #:
    #: `ship --part` records the half that landed and leaves the line open, which is the right
    #: shape: the ledger gains an entry qualified by what shipped and the roadmap keeps a task
    #: whose sentence is still partly true. What nothing held was the **other** half. Reading
    #: the ⏳ line said the problem was not solved and reading the ledger said what was done, so
    #: the remainder was reconstructed by subtracting one from the other — across two files,
    #: from prose written for different purposes, by whoever picked the line up. That
    #: reconstruction happened here several sessions later and needed the whole design read to
    #: recover a remainder the person shipping had known precisely.
    #:
    #: The subtraction is still the reader's; what changes is that both sides of it are on one
    #: answer. Naming the remainder as *data* is the stronger version and a change to the
    #: model — a second field on the entry — which RK1226 leaves open rather than guessing at.
    landed: tuple[str, ...] = ()
    #: The shipped entries whose own sentences name this **open** id, in ledger order — the
    #: work that was done *against* this line rather than on it (RK1439).
    #:
    #: Observed in a port: one line — delete two libraries from a C core — was the answer to
    #: `pick` for many sessions running, and no session worked it. What each did instead is in
    #: the ledger: seven entries name that id in their own sentences, all shipped, and the
    #: parent is still open. Seven children, one parent, and `pick` offered the parent every
    #: time, because every tier is a function of the file and nothing in the file had changed.
    #:
    #: RK1297 answered the neighbouring case — a line needing a console reads as ready, so
    #: `[requirements]` was declared and `pick` learned to set it aside. This is the same
    #: sentence with a different absence: nothing is missing, the line is simply larger than a
    #: session, and each caller finds that out by reading the criteria and filing a child. The
    #: dep graph cannot say so and is right not to: a child does not exist when the parent is
    #: offered, and by the time it does the parent is already answered.
    #:
    #: **A reading and never a verdict**, which is why it is not a marker and does not narrow
    #: what `pick` offers. Seven children is evidence a line is an epic; it is also what a
    #: genuinely central task looks like, and deciding between those needs meaning this tool
    #: has none of (L4). What it removes is the eighth session discovering it by repeating it.
    against: tuple[str, ...] = ()

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

    def _clauses(self) -> list[dict[str, object]]:
        """What `ship`'s two optional flags spend out of the ledger sentence (RK1306).

        Derived from the anchor and nothing else, which is the whole reason a number exists to
        publish: `--superseded-design` parenthesises a note beside the pointer the line already
        carries and `--recorded-in` wraps a path beside it, so the brackets and the address are
        knowable before either is written and only the caller's own prose is not.

        `[]` where there is no ship to compose for, or where the line points at nothing — both
        figures are measured off an anchor, and inventing one would price a clause the write
        cannot append. A record per flag rather than two keys, so `yours` can say **what the
        number leaves out**: a consumer that added neither its note nor its path would
        under-count by exactly the prose it is holding while it reads this.
        """
        if self.shipping is None or self.task.ref is None:
            return []
        return [
            {
                "flag": "--superseded-design",
                "wrapper": supersession_cost(self.task.ref, self.task.id),
                "yours": "the note",
            },
            {
                "flag": "--recorded-in",
                "wrapper": recording_cost(self.task.ref, self.task.id),
                "yours": "the path",
            },
        ]

    @property
    def waiting(self) -> tuple[Waiting, ...]:
        """What the declared priority is waiting on, where nothing ready answered it (RK1304).

        Off the choice for :attr:`held`'s reason: it is a fact about the pick this brief came
        from, so a brief called with an id has none — nothing was ranked and no queue was
        consulted, and inventing the reading here would answer a question nobody asked.
        """
        return () if self.choice is None else self.choice.waiting

    @property
    def revised(self) -> Commit | None:
        """The one commit every settled dep was measured against, or None (RK1463).

        :func:`_settled` compares every dep to `written[-1]` — the last commit that touched
        this design — so the revision is a fact about the *brief* and never about a dep. It was
        carried on each :class:`Settled` and restated under each one, which on a six-dep task
        was six identical dates in the register and six identical four-field records in the
        payload: 2,628 characters of 5,671, measured, of which the duplicate was half.

        A property and not a field, so there is one answer and it cannot go out of step with
        the rows it heads.
        """
        return self.settled[0].revised if self.settled else None

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
            _waiting_rows,
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
            # What the declared priority is waiting on, where nothing ready answered it
            # (RK1304). Beside `picked` because that is the sentence it completes: *the queue
            # names nothing ready* is true and does not say which task would change it.
            rows += _waiting_rows(self.choice)
            # The ids a live claim was stepped around (RK154), on the door a session starts a task
            # with: without them the caller cannot tell one of them is its own.
            rows += _held_rows(self.choice)
        taken = _claim_rows(self.claim, config)
        rows += taken
        event = _claim_event(self.claim, config)
        if taken and event is not None:
            # Beside the claim and not at the end: the rationale section closes this output, and
            # an event line after a paragraph of prose is one a hook reader has to hunt for.
            rows += _event_rows(event, "  ")
        rows.append(f"  symptom  {task.symptom}")
        rows.append(f"  why      {task.why}")
        if self.budget is not None:
            # One line, and only the field an amend rewrites (RK190): the whole table is
            # `budget`'s answer, and a brief that grew one would stop being a bounded one.
            why = self.budget.share("why")
            # The same figure `budget` states, off the same `Share` (RK245): a brief that named
            # the whole field's aim beside this line's remainder would be the second answer.
            #
            # `allowed`, and `on <the line>` in the words the two rows under it use (RK1375).
            # These three exist to be **compared** — RK1174 prints the second only where it
            # differs, because two numbers for one field is the fact worth seeing — and a
            # reader made to translate `left` into `for the ledger line` before subtracting
            # pays that cost through the phrasing instead of through the repetition. Since
            # RK1366 neither figure is what is left beside anything, so `left` was the word
            # that had stopped describing either, and the branch spelling it for a draft was
            # unreachable from here: this budget is always the line as it stands.
            rows.append(
                f"  budget   why {why.allowed} on this line, {why.aimed}, "
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
                # And what a supersession takes out of the same sentence (RK1261). The other
                # hedge stays a hedge because a qualifier is prose this cannot know; this one
                # is *derived*, the anchor being the pointer the line already carries — and a
                # task about to lose its design is exactly when this allowance is read, so an
                # answer that omitted it was wrong precisely when it was asked for.
                rows.append(
                    f"  shipping why {ship.allowed} on the ledger line a `ship` writes, which "
                    f"is the limit that refuses it — the whole of it, that sentence replacing "
                    f"this line's rather than extending it (RK1365) — less a `--part` "
                    f"qualifier, which is structure this cannot know you will pass"
                )
                # Both clauses and no longer one (RK1275): two flags landed in that sentence
                # after this row learned to name the first, so the figure was wrong by an
                # amount this tool knows. A row of their own rather than a third subordinate
                # clause — the line above is already the longest a brief prints.
                if task.ref is not None:
                    rows.append(
                        f"  shipping less {supersession_cost(task.ref, task.id)} for a "
                        f"`--superseded-design` clause and {recording_cost(task.ref, task.id)} for a "
                        f"`--recorded-in` wrapper, both into that same sentence — the note "
                        f"and the path are yours and are not in either number"
                    )
        if self.deciding is not None:
            # The third write, and the one that is not that sentence at all (RK1275): a
            # `--decides` files a line in the decisions role under that role's own limits, so
            # a reader given only the ledger's number was composing the durable half blind.
            decided = self.deciding.share("why")
            rows.append(
                f"  deciding why {decided.allowed} on the line `--decides` files, which is "
                f"the decisions role's own limit and not the ledger's — the constraint that "
                f"outlives the code, refused by that number"
            )
            # The **claim** that line inherits, where the decisions file is narrower than the
            # roadmap (RK1281): `--decides` writes no symptom, so a ship refused over one is
            # refused for a field no flag on the call reaches — and the read that could have
            # said so beforehand priced the `why` and stopped. Printed only where it binds,
            # which is two numbers for one field being the fact worth seeing (RK1174).
            claim = self.deciding.share("symptom")
            if self.budget is not None and claim.allowed < self.budget.share("symptom").allowed:
                rows.append(
                    f"  deciding symptom {claim.taken} of {claim.allowed} there, inherited "
                    f"from this line's own claim — `--decides` does not write one, so "
                    f"`restate` or a wider limit are the two doors if it does not fit"
                )
        settled = {one.dep: one for one in self.settled}
        if self.revised is not None:
            # **Once, and above the deps** (RK1463). The revision is one commit for the whole
            # brief — `_settled` compares every dep against `written[-1]` — and it was restated
            # under each one, six identical dates on a six-dep task. What is per dep is the
            # ship; what this is, is the line the reader measures all of them against.
            rows.append(
                f"  design   last written {self.revised.date[:10]} in "
                f"{self.revised.short}, before the dep(s) marked below landed"
            )
        for resolution in self.deps:
            # The ordering and never a claim about the prose (RK1163): the design named above
            # was last written before this dep shipped, so a trade-off it argues may already be
            # decided — and what decided it is in that commit, which is what this names.
            #
            # On the dep's own row since RK1463, and not under it: what was two lines per dep is
            # two facts about one dep, and the sentence joining them was the revision date said
            # again — six times on the task this was measured on.
            landed = settled.get(resolution.dep.id)
            since = (
                ""
                if landed is None
                else f"  — {landed.shipped.short}, {landed.shipped.date[:10]}"
            )
            rows.append(
                f"  dep      {resolution.dep.id}  {resolution.status}  "
                f"{resolution.detail}{since}"
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
        # Before the criterion and after the deps, which is where a fact about *this* line's
        # own history belongs (RK1226): what already landed is the other side of the
        # subtraction whoever picks a partial up has to make, and the design is what they
        # would otherwise read in full to make it.
        rows += [f"  landed   {one}" for one in self.landed]
        # Beside it, because it is the same question about the same line from the other side
        # (RK1439): `landed` says what shipped *as* this task and this says what shipped
        # *against* it. Silent at zero, which is every ordinary line — a row saying nothing
        # was filed against this one is the nag `landed` is deliberately not.
        if self.against:
            rows.append(
                f"  against  {len(self.against)} shipped entr"
                f"{'y' if len(self.against) == 1 else 'ies'} name this line and it is still "
                f"open: {', '.join(self.against)}"
            )
        for clause, found in self.criterion:
            # Before the design and after the deps, which is where the claim belongs: the
            # order is the whole point (RK1185) — what the work will be measured against
            # arrives before the first edit rather than at the `ship`. Never a verdict: `0`
            # is the ordinary state of a task about to start.
            rows.append(f"  proves   {clause}  ({found} site(s) now)")
        # The task's own first and the block's under it, each carrying its address (RK1268):
        # two altitudes printed as one list is a reader taking the block's finish line for
        # this line's, which is the conflation the second address exists to end.
        rows += [f"  done     {self.view.task.id}: {lead}" for lead in self.done_when.own]
        if self.done_when.own_elided:
            rows.append(
                f"  done     {self.view.task.id}: ... and {self.done_when.own_elided} more "
                f"under Done when"
            )
        named = config.schema.block_named(self.view.task.block)
        rows += [f"  done     {named}: {lead}" for lead in self.done_when.leads]
        if self.done_when.elided:
            rows.append(
                f"  done     {named}: ... and {self.done_when.elided} more under Done when"
            )
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
                    # Where this dep shipped after the design was last written (RK1163), the
                    # commit that says so — beside the resolution rather than in a list of its
                    # own, because it is a fact *about* this dep and a consumer reading the row
                    # would otherwise join two arrays to find it.
                    #
                    # **The ship alone** (RK1463). What it was compared against is one commit
                    # for the whole brief and is published once, below: repeated here it was
                    # the same four fields per dep — half of `deps_resolved`, which on a six-dep
                    # task measured 2,628 characters of a 5,671-character answer.
                    **{
                        "settled_since": {"shipped": _dated_json(one.shipped)}
                        for one in self.settled
                        if one.dep == r.dep.id
                    },
                }
                for r in self.deps
            ],
            # The line every `settled_since` above is measured against (RK1463), once: it is
            # the last commit that touched this design, which is a fact about the brief and
            # not about any dep. Null where nothing settled, which is every task whose deps
            # landed before its design was written and every project git cannot answer for.
            "revised": None if self.revised is None else _dated_json(self.revised),
            "chains": [
                {
                    "path": [self.task.id, *(hop.target for hop in c.hops)],
                    "end": str(c.end),
                    "detail": c.detail,
                }
                for c in self.chains
            ],
            # The count whole and the roster bounded (RK1301), which is what the non-goals list
            # in this same payload already does: a handful of ids, and how many were left, so a
            # caller can tell a short list from a cut one without a second call. `deps <id>` is
            # where the whole roster lives, and it is the read that answers that question.
            "unblocks": {
                "count": self.leverage.count,
                "of": self.leverage.of,
                "transitive": list(self.leverage.transitive[:UNBLOCKS]),
                "transitive_elided": max(0, self.leverage.count - UNBLOCKS),
            },
            "non_goals": list(self.non_goals.leads),
            "non_goals_elided": self.non_goals.elided,
            "done_when": list(self.done_when.leads),
            "done_when_elided": self.done_when.elided,
            # The task's own, as its own key (RK1268): a caller merging the two would be
            # asserting the block's finish line about this line.
            "done_when_own": list(self.done_when.own),
            "done_when_own_elided": self.done_when.own_elided,
            # What the design says would prove this done, with what each clause matches now
            # (RK1185). The clauses and the counts and never the sites: this answer is bounded
            # to a tool result, and the addresses are `evidence`'s once the work is under way.
            # `[]` where the design declares none, which is an answer and not an absence.
            # What the ledger already records as landed, per `ship --part` (RK1226). `[]` on
            # the ordinary line, which is an answer rather than an absence.
            "landed": list(self.landed),
            # And what shipped *against* it (RK1439). Published always and printed only where
            # it is non-empty, which is `Split.payload`'s rule for its reason: a key costs a
            # client nothing to skip, where a row costs every reader the same attention.
            "against": list(self.against),
            "criterion": [
                {"pathspec": one.pathspec, "pattern": one.pattern, "sites": found}
                for one, found in self.criterion
            ],
            # The whole table here and one line on stdout (RK190): a tool result is read by
            # something that can hold it, and this is the number the next write is measured on.
            "budget": None if self.budget is None else self.budget.payload(),
            # The write about to be made (RK1174), as its **difference** from the table above
            # rather than as a second copy of it (RK1298). Always published where it exists —
            # unlike the printed line, which is silent when the two agree: a consumer comparing
            # them wants the numbers present, and what it never wanted is five rows repeated to
            # say nothing. `against` names the base, so the overlay needs no convention.
            "shipping": None
            if self.shipping is None
            else self.shipping.delta(self.budget, "budget" if self.budget else None),
            # The third write (RK1275), diffed against the second where there is one: a project
            # declaring both roles usually declares them the same limits, so `changed: {}` is the
            # answer — and it is a fact, where a third identical table was the same fact spelled
            # in every row it has.
            "deciding": None
            if self.deciding is None
            else self.deciding.delta(
                self.shipping or self.budget,
                "shipping" if self.shipping else ("budget" if self.budget else None),
            ),
            # And what the two optional clauses spend **out of** that allowance (RK1306). The
            # row above stdout has carried them since RK1261 and RK1275 and the payload never
            # did, so the caller this project is built for — the one on the other end of the
            # served tool — composed a `why` against the published number and was refused by
            # arithmetic it had no way to do. Measured on quickshell at five ships out of five:
            # QS8, QS9, QS10, QS87 and QS88 each took a `why.too-long` first, and every one
            # passed `--recorded-in` or `--superseded-design` or both.
            #
            # The **wrappers** and never the whole clause, which is what makes them knowable:
            # the anchor is the pointer the line already carries, so only the note and the path
            # are the caller's — and those the caller is holding while it reads this. `[]`
            # where the line points at nothing, both figures being derived from the anchor.
            #
            # **Not `doors`, and the name now says so** (RK1324). These are *costs* and not
            # calls: RK1324's falsification asked whether the four names were four facts,
            # and this is the one that was — so it keeps its own key and stops reading as
            # the class a consumer looks for a runnable command in.
            "clause_costs": self._clauses(),
            # Same key and same shape as `pick`'s (RK154): one fact spelled two ways is two facts.
            "held": [{"id": h.id, "age": round(h.age), "since": h.since} for h in self.held],
            # And the same for what the priority is waiting on (RK1304), by the same rule: this
            # verb answers the pick's question too, so it answers it in the pick's words.
            "waiting": [
                {
                    "token": one.token,
                    "lines": one.lines,
                    "releases": list(one.releases),
                    "of": one.of,
                }
                for one in self.waiting
            ],
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
    available: Sequence[str] = (),
) -> Brief:
    """Join every answer about one task, and take it where the caller asked to.

    ``block`` scopes the pick when no id is given (RK40), so "start the next thing in
    Block C" is one call whose absence of an answer is about Block C. ``designed`` narrows
    it to work whose design is written (RK83) — the two flags together are what "execute
    Block C" means, and neither reaches a brief the caller addressed by id.

    ``available`` is what this caller has (RK1297), and it reaches the pick for the reason
    the two above do: a brief is the call that *starts* work, so the one filter whose answer
    is "not by you" belongs where the line is chosen and not where it is described.

    ``claim`` moves the marker to in-progress (RK149). One lock covers the write **and** the
    reading that follows it, so the brief describes the line as it was taken rather than as
    some later state found it — the four reads being milliseconds, which is what makes
    holding the write lock across them free.
    """
    if claim:
        with exclusive(config.root):
            return _gather(config, *_claimed(config, task_id, block, designed, available))
    if task_id is None:
        chosen = pick(config, block, designed, available=available)
        if chosen.entry is None:
            raise NothingToBrief(
                chosen.reason, chosen.held, chosen.standing, chosen.lacking
            )
        return _gather(config, chosen.entry.task.id, chosen, None)
    return _gather(config, task_id, None, None)


def _claimed(
    config: Config,
    task_id: str | None,
    block: str | None,
    designed: bool,
    available: Sequence[str] = (),
) -> tuple[str, Choice | None, Claim]:
    """Take a line, by the tiers or by the id the caller gave, and say which happened."""
    if task_id is not None:
        return task_id, None, hold(config, task_id)
    taken = take(config, block, designed, available=available)
    if taken.choice is None or taken.choice.entry is None:
        # The same absence `pick` reports and not a refusal: a caller asking for work and
        # being told there is none got the fact it asked for, and nothing was written.
        held = () if taken.choice is None else taken.choice.held
        raise NothingToBrief(
            "" if taken.choice is None else taken.choice.reason,
            held,
            None if taken.choice is None else taken.choice.standing,
            () if taken.choice is None else taken.choice.lacking,
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
        done_when=done_when(config, backlog.roadmap, task.block, task.id),
        choice=chosen,
        claim=claim,
        settled=_settled(config, view, backlog.resolve(task) if entry is not None else ()),
        budget=None if view.shipped else budget_of(config, task, open_line=True),
        criterion=_criterion(config, view),
        # A lookup this verb already performs (RK1226): the ledger is open because `shipping`
        # is measured against it, so surfacing what has already landed costs nothing.
        landed=_landed(backlog, task.id) if not view.shipped else (),
        # The same lookup one question over (RK1439), and free for the same reason: the ledger
        # is already open. Asked only of an **open** line — a shipped one's children are
        # history, and the reader of a shipped brief is not being offered anything.
        against=backlog.against(task.id) if not view.shipped else (),
        shipping=None
        if view.shipped or not config.has("changelog")
        else budget_of(
            config,
            # The task **as the ledger will hold it** and not as the roadmap holds it
            # (RK1199): `ship` drops the deps and the pointer before it renders, so pricing
            # the roadmap's task under the ledger's schema measured a structure ten
            # characters wider than the line — an allowance with ten it could not spend, and
            # a reader who trusted it and then watched `ship` accept more was told two things.
            # Through `ship`'s own function, so the figure and the write cannot come apart.
            #
            # With the `why` **emptied** and not inherited (RK1365). `Share.left` subtracts what
            # a field already holds, which is an `amend`'s question — and `ship --why` is
            # required and *replaces* the roadmap's sentence, so the room for it is the whole
            # allowance. Priced with that sentence still in the field, this read reported `37 of
            # 200` against a ship that then accepted 145: a number four times under the real one
            # fails in the direction that looks safe, and an advisory limit nobody believes still
            # costs a line of every brief.
            as_recorded(task, config.schema.shipped_marker, ""),
            open_line=False,
            schema=config.schema_for("changelog"),
        ),
        # The third write the same ship may make (RK1275), priced the same way and under the
        # role's own schema: `--decides` renders a decision the way `ship` renders an entry,
        # so the figure comes through `as_recorded` for the reason the one above does — and with
        # the `why` emptied for the reason that one is (RK1365), a `--decides` sentence being
        # written from nothing exactly as the entry's is.
        deciding=None
        if view.shipped or not config.has("decisions")
        else budget_of(
            config,
            as_recorded(task, config.schema_for("decisions").shipped_marker, ""),
            open_line=False,
            schema=config.schema_for("decisions"),
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



def done_when(
    config: Config, document: Document, block: str, task_id: str = ""
) -> DoneWhen:
    """What finishes this task and what finishes its block, in file order and bounded (RK1265).

    :func:`non_goals`' shape one list over, and bounded for its reasons: each lead is cut to
    the project's own `[criteria]` limit with the cut shown, and a list past :data:`NON_GOALS`
    reports how many it left. *Which* characters are the lead is `criteria`'s answer and not
    one guessed here — the module that writes a criterion says what its address is.

    Scoped to the task's own block and never to the backlog: a criterion is about a body of
    work, so printing another block's would be answering a question the caller did not ask
    with a claim about somebody else's finish line. And to the task's own list beside it
    (RK1268), which is the narrower version of exactly that argument: the line is the unit
    being executed, so what would finish *it* is the answer a brief was opened for.
    """
    limit = (config.criteria or Scope()).lead

    def bounded(every: tuple[str, ...]) -> tuple[tuple[str, ...], int]:
        return (
            tuple(
                textwrap.shorten(lead, width=limit, placeholder=ELLIPSIS)
                for lead in every[:NON_GOALS]
            ),
            max(0, len(every) - NON_GOALS),
        )

    leads, elided = bounded(criteria.leads(document, block))
    own, own_elided = bounded(criteria.leads(document, task_id) if task_id else ())
    return DoneWhen(leads=leads, elided=elided, own=own, own_elided=own_elided)


def _criterion(config: Config, view: View) -> tuple[tuple[Clause, int], ...]:
    """What this design says would prove the task done, counted now (RK1184, RK1185).

    The clause and its count, never the sites: a brief is bounded to a tool result, and the
    addresses are what `evidence` answers once the work is under way. **A criterion is read
    at the start and not at the ship** — the order is the whole point, since a claim the work
    will be measured against has to arrive before the first edit.

    Silent on three shapes, all of which are answers rather than failures: a task with no
    design, a design declaring no criterion, and a block this grammar cannot read. The last is
    `lint`'s to report (RK1184) and refusing a brief over it would take away the call that
    starts the work, on a fence the work has not touched yet.
    """
    from roadkeep.remaining import EVIDENCE, QueryError, count, declared  # noqa: PLC0415 - RK260

    if view.section is None:
        return ()
    try:
        clauses = declared(view.section.body, EVIDENCE)
    except QueryError:
        return ()
    if not clauses:
        return ()
    # Per clause and not one total: two clauses at 3 and 0 are a criterion half met, and a
    # single `3` says the same thing as both met — which is the shape RK10 is about, one
    # module over. One `count` each rather than attributing a joined answer afterwards: a
    # `Site` carries no clause, and giving it one to serve this reader would be a field on
    # the record that only a caller's arithmetic wanted.
    return tuple(
        (clause, count(config.root, view.task.id, (clause,), EVIDENCE).total)
        for clause in clauses
    )


def _landed(backlog: Backlog, task_id: str) -> tuple[str, ...]:
    """Every qualifier the ledger records for this open id, in file order (RK1226).

    **All of them and not the first.** Through this tool's own door there is at most one:
    `SecondPartial` refuses a second `ship --part` on one id, because one id carries one
    partial and then the completion. An **adopted** ledger is the other case, and it is the
    one that decides the reader — Turing's holds 755 entries written before the tool existed,
    and a history spelling two deliveries of one id is exactly what `adopt` takes in. `by_id`
    answers the first entry per id by design (a duplicate is a lint error, not a merge), which
    would name one of them and hide the other.

    Silent where nothing landed, which is every ordinary line: a row saying *nothing has
    shipped* on every brief is a nag this tool has no standing to make.
    """
    if backlog.ledger is None:
        return ()
    return tuple(
        entry.task.part
        for entry in backlog.ledger.entries
        if entry.task.id == task_id and entry.task.part
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
