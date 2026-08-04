"""What a line has left for prose, asked before a word of it exists (RK190).

RK183 made the `why`'s limit the smaller of its own and what the line has left, and RK184
made the refusal state the surplus. Both act at the same moment: **after** a sentence has
been composed. The number they report is derived from the id, the marker, the deps and the
pointer — every one of which `add` knows before the prose exists — so nothing about it had
to wait for a draft.

That is the arrangement L1 exists to end, one layer in. A `maxLength` refuses before a
sentence is written to fill it; a derived budget delivered only as a refusal has the shape
of a linter again, and the author pays a retry to learn a number the tool could have handed
them. The saving is the analysis: "how long may this sentence be, under these deps" has an
answer, and asking it costs no context (L5).

Two moments and one door. Asked with no id, the budget is the line `add` is *about* to
write — the next id, this project's first marker, the deps the caller names. Asked with an
id, it is the line already on the desk, which an `amend` is about to rewrite; the symptom is
that line's own, so what comes back is the room the `why` really has.

Nothing here restates a limit. Every number is :meth:`Schema.prose_budget`,
:meth:`Schema.why_budget` or a field's own declared maximum, read off the schema — a
constant here would be one more thing to keep true, and the first slot to move would make
this the second opinion an author trusts.

**The pointer is part of the structure, and under an outline it is the caller's** (RK265).
Under ``ref_scheme = "id"`` the anchor is derived, so a budget asked before the prose knows
it exactly. Under ``"outline"`` the anchor is *chosen*, and a budget that composed the line
without one measured a structure the `add` would not have — over-reporting the room by the
anchor's width, and refusing the sentence it had just approved. So ``ref`` is an argument
here for the same reason it is one on `add`, and where the caller names none the assumption
is the **widest anchor the roadmap already carries** rather than no anchor at all: a number
that cannot be exact is at least never optimistic, and :attr:`Budget.ref_assumed` says which
of the two the caller is reading.

**Validated in characters, published in words** (RK185). A model has no characters: the
tokenizer exposes tokens, so "200 characters" is a target reached by trial and every retry
is a re-guess. Words survive tokenization well enough to be aimed at, so every number above
is also stated as one — the aim, beside the gate. They are not in conflict, because the
character figure is what refuses and the word figure is what an author can act on before a
sentence exists; publishing only the first is the arrangement L1 exists to end. The
conversion itself lives in :mod:`roadkeep.schema` and is read from here (RK201), because
the refusal an author reaches *after* an overrun states its surplus in words off the same
constant — one arithmetic in two directions, and not two constants that can disagree.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from roadkeep.authoring import compose
from roadkeep.config import Config
from roadkeep.ids import next_id
from roadkeep.schema import CHARS_PER_WORD, Task, words

#: Re-exported, not re-declared (RK201). The conversion moved down to `schema`, where the
#: refusal that states a surplus can reach it: the aim and the surplus are the same
#: arithmetic in opposite directions, and two constants would be two answers.
__all__ = ["CHARS_PER_WORD", "Budget", "Share", "budget", "budget_of", "words"]


@dataclass(frozen=True, slots=True)
class Share:
    """One prose field: its own declared limit, what this line leaves it, and what it took."""

    field: str
    #: The field's own declared maximum — `[limits]`, and what the MCP schema publishes.
    limit: int
    #: What *this* line allows it, which is the smaller of the two and the one that binds.
    allowed: int
    taken: int

    @property
    def left(self) -> int:
        return max(0, self.allowed - self.taken)

    @property
    def aim(self) -> int:
        """What this field allows, in the unit an author can count (RK185).

        Derived from :attr:`allowed` and not from :attr:`limit`, which is the whole reason
        it waited on RK183: an aim computed from the published ceiling would inherit the
        overrun and send the author at prose the line has no room for.
        """
        return words(self.allowed)

    @property
    def room(self) -> int:
        """What is *left*, in that same unit (RK245).

        The figure an `amend` is actually bounded by, and the one number RK185 skipped:
        beside a partly written field, :attr:`aim` describes the whole of it, so `18 left
        aim 30 words` invites the reading that thirty words are available when about three
        are. Floored by :func:`~roadkeep.schema.words`, which is the right rounding here for
        RK201's reason read from the other side — a remainder is an allowance, and an
        allowance that rounds up is the retry both figures exist to remove.
        """
        return words(self.left)

    @property
    def bound_by_line(self) -> bool:
        """Whether the line is what binds this field, rather than the field's own limit.

        The one thing a published `maxLength` cannot say: an author writing to the two
        numbers in the schema is refused by a third, measured on a string they never write.
        """
        return self.allowed < self.limit


@dataclass(frozen=True, slots=True)
class Budget:
    """What one line — written or about to be — has for prose, and how it is divided."""

    task: Task
    #: Whether the line exists. False means the id is the next one and the fields are the
    #: caller's, which is the pre-`add` question; True means an `amend`'s.
    open_line: bool
    line_max: int
    #: What the line costs before a word of prose: the marker, the bold id, the `(deps: …)`
    #: group, the em dashes and the pointer. Rendered, never added up a second time (L3).
    structure: int
    prose: int
    shares: tuple[Share, ...]
    #: The anchor the structure above was measured with, or None where the line carries no
    #: pointer at all. Under the id scheme it is the id and nobody chose it.
    ref: str | None = None
    #: Whether that anchor is an assumption rather than the caller's (RK265). True means the
    #: outline scheme is in force, no ``ref`` was named, and the width came off the file.
    ref_assumed: bool = False

    def share(self, field: str) -> Share:
        return next(one for one in self.shares if one.field == field)


def budget(
    config: Config,
    task_id: str | None = None,
    *,
    block: str = "",
    deps: Sequence[str] = (),
    status: str | None = None,
    symptom: str = "",
    family: str | None = None,
    ref: str | None = None,
) -> Budget:
    """The prose budget of a line, named by id or described by the fields an `add` takes.

    An id that is not in the roadmap is not an error here: it is the third question, "what
    would a line with *this* id have", which is what a caller checking a split (`RK9b`) is
    asking. Only an id that resolves changes the answer, and then it changes it entirely —
    the symptom, marker and deps come off the file rather than off the arguments.

    ``ref`` is the anchor the line would point at, and only the outline scheme has one to
    name: under the id scheme it is derived, so a caller passing a different one is refused
    by :func:`~roadkeep.authoring.compose` exactly as `add` refuses it. It rides here because
    the pointer is structure and the structure is what the prose is left over from — passing
    it late is how a budget approves a sentence the `add` then refuses (RK265). An id the
    roadmap holds keeps its own anchor unless this names another, which is the `amend` that
    moves the pointer and the prose in one call.
    """
    task, open_line, assumed = _subject(
        config,
        task_id,
        block=block,
        deps=deps,
        status=status,
        symptom=symptom,
        family=family,
        ref=ref,
    )
    return budget_of(config, task, open_line=open_line, ref_assumed=assumed)


def budget_of(
    config: Config, task: Task, *, open_line: bool, ref_assumed: bool = False
) -> Budget:
    """The same answer about a task the caller already holds — what `brief` hands over.

    Separate from :func:`budget` because the caller that has the line does not want it
    looked up again, and because a shipped one has no budget to state: the ledger is a
    different grammar, and the line an `amend` would rewrite is the open one.
    """
    schema = config.schema
    prose = schema.prose_budget(task)
    # The structure is derived from the budget rather than measured again: `prose_budget` is
    # the one place that renders the emptied line, and a second measurement is a second answer.
    shares: list[Share] = []
    if schema.symptom_field:
        shares.append(
            Share("symptom", schema.symptom_max, min(schema.symptom_max, prose), len(task.symptom))
        )
    shares.append(Share("why", schema.why_max, schema.why_budget(task), len(task.why)))
    return Budget(
        task=task,
        open_line=open_line,
        line_max=schema.line_max,
        structure=schema.line_max - prose,
        prose=prose,
        shares=tuple(shares),
        ref=task.ref,
        ref_assumed=ref_assumed,
    )


def _subject(
    config: Config,
    task_id: str | None,
    *,
    block: str,
    deps: Sequence[str],
    status: str | None,
    symptom: str,
    family: str | None,
    ref: str | None = None,
) -> tuple[Task, bool, bool]:
    """The line the budget is about, whether the roadmap holds it, and whether it guessed."""
    if task_id is not None:
        entry = config.document("roadmap").by_id().get(task_id)
        if entry is not None:
            if ref is None:
                return entry.task, True, False
            # Re-composed rather than `replace`d, so that a `--ref` under the id scheme is
            # refused here by the one function that owns the rule (RK265) instead of being
            # silently taken — the budget for an `amend` has to refuse what the `amend` will.
            task = entry.task
            return (
                compose(
                    config,
                    task_id=task.id,
                    block=task.block,
                    symptom=task.symptom,
                    why=task.why,
                    status=task.status,
                    deps=tuple(dep.render() for dep in task.deps),
                    ref=ref,
                ),
                True,
                False,
            )
    assumed = ref is None and config.schema.ref_scheme != "id"
    return (
        compose(
            config,
            task_id=task_id if task_id is not None else next_id(config, family),
            block=block,
            symptom=symptom,
            why="",
            status=status,
            deps=deps,
            ref=_widest_anchor(config) if assumed else ref,
        ),
        False,
        assumed and ref is None,
    )


def _widest_anchor(config: Config) -> str | None:
    """The longest pointer the roadmap already carries, or None on a file carrying none.

    The stand-in for an anchor the caller did not name (RK265). Widest and not narrowest,
    and not none: the whole defect is a budget that promised room the `add` then refused, so
    an assumption that can be wrong is made wrong in the direction that costs an author
    nothing — a sentence with characters to spare, rather than a second composition of it.

    A roadmap holding no pointer at all is the one case with no evidence to reason from, and
    None is that stated rather than papered over: the caller is told the structure counts no
    pointer, which is the honest form of the number this task found being reported silently.
    """
    return max(
        (entry.task.ref for entry in config.document("roadmap").entries if entry.task.ref),
        key=len,
        default=None,
    )
