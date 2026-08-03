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

**Validated in characters, published in words** (RK185). A model has no characters: the
tokenizer exposes tokens, so "200 characters" is a target reached by trial and every retry
is a re-guess. Words survive tokenization well enough to be aimed at, so every number above
is also stated as one — the aim, beside the gate. They are not in conflict, because the
character figure is what refuses and the word figure is what an author can act on before a
sentence exists; publishing only the first is the arrangement L1 exists to end.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from roadkeep.authoring import compose
from roadkeep.config import Config
from roadkeep.ids import next_id
from roadkeep.schema import Task

#: Characters per word, for turning a budget that refuses into one that can be aimed at
#: (RK185). Measured over this repository's 392 written `symptom` and `why` fields: the
#: median is 5.5 and the 95th percentile 6.36, so this is the first round number above it
#: — an author who lands on the word aim clears the character gate about nineteen times in
#: twenty, and the twentieth is the refusal that already names the surplus (RK184).
#:
#: Not configuration (L6). A project declares how long its lines may be; this is a property
#: of the prose those lines are written in, and a `roadkeep.toml` field for it would be a
#: project declaring a fact about English. The corpus that fixes it is the one the format is
#: proven by, and `tests/test_budgeting.py` re-measures it rather than trusting this comment.
CHARS_PER_WORD = 6.5


def words(chars: int) -> int:
    """A character budget as the word count it is safe to aim at.

    Floored, never rounded: an aim that rounds up is an aim that lands over the gate half
    the time it is hit exactly, which is the retry this exists to remove.
    """
    return max(0, int(chars // CHARS_PER_WORD))


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
) -> Budget:
    """The prose budget of a line, named by id or described by the fields an `add` takes.

    An id that is not in the roadmap is not an error here: it is the third question, "what
    would a line with *this* id have", which is what a caller checking a split (`RK9b`) is
    asking. Only an id that resolves changes the answer, and then it changes it entirely —
    the symptom, marker and deps come off the file rather than off the arguments.
    """
    task, open_line = _subject(
        config, task_id, block=block, deps=deps, status=status, symptom=symptom, family=family
    )
    return budget_of(config, task, open_line=open_line)


def budget_of(config: Config, task: Task, *, open_line: bool) -> Budget:
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
) -> tuple[Task, bool]:
    """The line the budget is about, and whether it is one the roadmap already holds."""
    if task_id is not None:
        entry = config.document("roadmap").by_id().get(task_id)
        if entry is not None:
            return entry.task, True
    return (
        compose(
            config,
            task_id=task_id if task_id is not None else next_id(config, family),
            block=block,
            symptom=symptom,
            why="",
            status=status,
            deps=deps,
        ),
        False,
    )
