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

**One transaction, one budget** (RK301). `add --section` writes a line *and* a body, the body
has its own limit, and it refuses the whole `add` — so a read that named only the line's two
fields was silent about half of what it was asked about. Thirteen refusals in one session,
each the entire paragraph re-sent to learn a config value; over MCP there is no pipe, so the
retry is the whole payload. The body rides here as a field and not as a second verb, and its
aim sits **under** its limit rather than on it: composing to exactly the declared number is
what four of those refusals were.

**The pointer is part of the structure, and under an outline it is the caller's** (RK265).
Under ``ref_scheme = "id"`` the anchor is derived, so a budget asked before the prose knows
it exactly. Under ``"outline"`` the anchor is *chosen*, and a budget that composed the line
without one measured a structure the `add` would not have — over-reporting the room by the
anchor's width, and refusing the sentence it had just approved. So ``ref`` is an argument
here for the same reason it is one on `add`, and where the caller names none the assumption
is the **widest anchor the roadmap already carries** rather than no anchor at all: a number
that cannot be exact is at least never optimistic, and :attr:`Budget.ref_assumed` says which
of the two the caller is reading.

**Three writes carry a prose limit, and this answers for all three** (RK283). The task line
was the only one served, and it is the smallest: `non-goal add --why` is capped by
`[non_goals]`, and a section body by `section = <n>` in words — the longest thing an author
writes, and the one whose refusal costs the most to obey. Measured filing four tasks after a
block emptied: two refusals on a non-goal `why` at 286 and 234 against 200, one on a section
body at 366 words against 300. Both limits are facts about the file and the role, known
before a word, so both are read here rather than met at the door. Not a `--dry-run` on the
write verbs, which would want the prose first — the whole point is to be answerable without it.

**And the draft is measured here too, which is the half RK190 left** (RK1190). Every number
above is knowable before the first word, and *none of them measures the words that then get
written* — so the only thing that ever compared a paragraph against its limit was the write
that refused it. Measured on one session driving another project: eight refusals on length,
several of them three and four retries for a single task, each costing the whole field again.
The refusals are good; none of them is reachable until something has been sent.

So every subject that has a limit takes the draft it is for — `--why` and `--symptom` on a
line, `--body` beside `--anchor` — and answers with the overrun rather than with the refusal.
It is **counted by the writer's own counter**: :func:`~roadkeep.kernel.schema.width` for a
field and the section reader's own words for a body, because a second counter that disagreed
with the door by one would be worse than no read at all. Nothing is composed and nothing is
validated — a draft twice its limit is a **number**, where an `add` carrying it is a refusal,
and that difference is the whole verb. Over MCP it is the same read: `isError` where the draft
is over, because a caller gating on the answer should not have to parse prose for the one bit
it asked for.

Stdin is accepted here and nowhere else in this shape (RK329's objection, and why it does not
apply): a pipe does not rewind, so the writing verbs read one late and refuse the paragraph
back to the caller — this writes nothing, so a refusal costs a re-send of something that was
never going to land.

**Validated in characters, published in words** (RK185). A model has no characters: the
tokenizer exposes tokens, so "200 characters" is a target reached by trial and every retry
is a re-guess. Words survive tokenization well enough to be aimed at, so every number above
is also stated as one — the aim, beside the gate. They are not in conflict, because the
character figure is what refuses and the word figure is what an author can act on before a
sentence exists; publishing only the first is the arrangement L1 exists to end. The
conversion itself lives in :mod:`roadkeep.kernel.schema` and is read from here (RK201), because
the refusal an author reaches *after* an overrun states its surplus in words off the same
constant — one arithmetic in two directions, and not two constants that can disagree.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Sequence

from pathlib import Path

from roadkeep.authoring import compose, prose_role
from roadkeep.config import Budget as ConfigBudget
from roadkeep.config import Config, spent, translated
from roadkeep.ids import next_id
from roadkeep.kernel.schema import (
    CHARS_PER_WORD,
    UTF16_UNITS,
    Schema,
    Task,
    body_aim,
    width,
    words,
)
from roadkeep.scoping import NoSuchNonGoal, NotGoverned, address, leads, read
#: `words` here is the char-to-word conversion this module publishes as an aim; the section
#: reader's `words` is what a body is actually charged. Two arithmetics, so the import that
#: would have shadowed one is aliased rather than the two being reconciled (RK1190).
from roadkeep.sections import binding, declaring, find, words as prose_words

#: Re-exported, not re-declared (RK201). The conversion moved down to `schema`, where the
#: refusal that states a surplus can reach it: the aim and the surplus are the same
#: arithmetic in opposite directions, and two constants would be two answers.
__all__ = [
    "CHARS_PER_WORD",
    "AmbiguousAnchor",
    "Body",
    "Budget",
    "Cost",
    "Load",
    "Share",
    "body_budget",
    "budget",
    "budget_of",
    "file_budget",
    "non_goal_budget",
    "words",
]


class AmbiguousAnchor(ValueError):
    """Two prose files declare one anchor, so no file is the one being budgeted (RK303).

    A `ValueError` and deliberately not the `KeyError` this module already raises: that one
    means "no prose file to be a fact about" and is swallowed where a line's own budget is
    being read, and swallowing this one would put the answer back to a number about a file
    nobody named. `show` and `ship` state the same finding in their own words; this is the
    third door reaching it, and `--role` is what resolves it, the caller naming which of the
    two they mean being the only thing that can.
    """

    def __init__(self, anchor: str, files: Sequence[str]) -> None:
        self.anchor, self.files = anchor, tuple(files)
        super().__init__(
            f"§{anchor} is declared by {' and '.join(self.files)}: one anchor names one "
            f"section, and a budget for the first of two prices a section the pointer does "
            f"not reach — `budget --anchor {anchor} --role <role>` is which of the two "
            f"you mean"
        )


@dataclass(frozen=True, slots=True)
class Share:
    """One prose field: its own declared limit, what this line leaves it, and what it took."""

    field: str
    #: The field's own declared maximum — `[limits]`, and what the MCP schema publishes.
    limit: int
    #: What *this* line allows it, which is the smaller of the two and the one that binds.
    allowed: int
    taken: int
    #: Where that maximum was declared, as `Schema.source_of` spells it (RK1067, RK1071).
    #: The refusal carries this and the read did not, which is the wrong way round: this is
    #: the earlier of the two moments, and the one the whole tool is built on — the number
    #: arriving before the prose does. Carried on the share rather than composed by the
    #: printer, because a per-role limit means the answer differs by which file is asked
    #: about, and only the reader that resolved the schema knows which one that was.
    source: str = ""
    #: Whether :attr:`taken` is prose the caller handed over to be measured rather than prose
    #: the file holds (RK1190). It changes no arithmetic — a draft is measured against the same
    #: allowance the write enforces, which is the whole claim — and it changes every word of the
    #: answer: "153 written" about a paragraph that exists nowhere is a report about the wrong
    #: file, and the caller cannot tell the two apart from the number.
    drafted: bool = False

    @property
    def left(self) -> int:
        return max(0, self.allowed - self.taken)

    @property
    def over(self) -> int:
        """What this field exceeds its allowance by — 0 where it fits (RK1190).

        The number :attr:`left` cannot carry, because that one floors at zero: a symptom of 200
        against 120 reported `200 written, 0 left`, and the deficit an author has to cut was the
        subtraction between two figures on the same row. Not the refusal's arithmetic borrowed —
        the refusal states this same surplus from the other side, off :attr:`allowed`, which is
        the one number both moments are derived from.
        """
        return max(0, self.taken - self.allowed)

    @property
    def aim(self) -> int:
        """What this field allows, in the unit an author can count (RK185).

        Derived from :attr:`allowed` and not from :attr:`limit`, which is the whole reason
        it waited on RK183: an aim computed from the published ceiling would inherit the
        overrun and send the author at prose the line has no room for.
        """
        return words(self.allowed)

    @property
    def aimed(self) -> str:
        """The word figure, about the room the author actually has (RK245).

        Beside a partly written field the whole-field aim answers a question nobody asked, and
        read next to a remainder in characters it invites the reading that thirty words are
        available when three are. So the two are never printed together: what is stated is the
        aim for what is left, and `--json` keeps both.
        """
        return f"aim {self.room} more words" if self.taken else f"aim {self.aim} words"

    def payload(self) -> dict[str, object]:
        """One prose field in both units, shared with the non-goal's two (RK283).

        The same shape and the same arithmetic at both doors: a second spelling of it here would
        be a second answer, and the whole reason this verb exists is that there is only one.
        """
        return {
            "field": self.field,
            "limit": self.limit,
            "allowed": self.allowed,
            "aim": self.aim,
            "taken": self.taken,
            "left": self.left,
            # What `left` floors away (RK1190). Published always and not only when non-zero, for
            # the reason `stats` prints `uncounted` at zero: a field that appears only when it
            # is set is a field a reader learns to stop looking for.
            "over": self.over,
            # Whether `taken` is the file's prose or the caller's draft (RK1190): the same
            # number means two different things and only this says which.
            "drafted": self.drafted,
            # Beside `left` and not instead of it (RK245): the characters are still what
            # refuses, and this is the same remainder in the unit an author can count.
            "room": self.room,
            # Declared, as the section budget declares `words` (RK430). A number published
            # without its unit is what let a consumer counting UTF-16 and a tool counting code
            # points both be right about one line and disagree by one.
            "unit": UTF16_UNITS,
            "bound_by_line": self.bound_by_line,
            # Where `limit` was set (RK1071), so a surface serving this can answer *why is it
            # 200* without a second call — the read that otherwise costs a turn. Beside the
            # number rather than under the payload, because a per-role limit makes it a fact
            # about this field and not about the answer.
            "source": self.source.strip(" ()"),
        }

    @property
    def room(self) -> int:
        """What is *left*, in that same unit (RK245).

        The figure an `amend` is actually bounded by, and the one number RK185 skipped:
        beside a partly written field, :attr:`aim` describes the whole of it, so `18 left
        aim 30 words` invites the reading that thirty words are available when about three
        are. Floored by :func:`~roadkeep.kernel.schema.words`, which is the right rounding here for
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
    #: The **other half of the same transaction** (RK301). `add --section` writes a line and
    #: a body, the body has its own limit, and it refused the whole `add` while this read
    #: mentioned only the line. None where the project declares no prose file, which is the
    #: only state in which that write does not exist.
    section: Body | None = None
    #: Why there is no section budget, where the absence is a **defect** (RK303): an anchor
    #: two prose files declare has no one file to be priced against, and a silent None reads
    #: as the project that declares no prose file at all. Empty in every other state,
    #: including that one, for the reason `show` states its absences apart.
    section_absence: str = ""

    def share(self, field: str) -> Share:
        return next(one for one in self.shares if one.field == field)

    def __str__(self) -> str:
        """What this line has for prose, one field per row — the register a reader scans.

        Beside :meth:`payload` since RK1170, and for that task's reason: these two were a printer
        inside the handler and a builder in `rendering.py`, so one answer was spelled in two files
        and neither held both. What the payload publishes is now what this shows, by construction
        rather than by a test.
        """
        state = "open line" if self.open_line else "the line add would write next"
        deps = ", ".join(dep.render() for dep in self.task.deps) or "—"
        rows = [
            f"{self.task.id}  {self.task.status}  deps {deps}  ({state})",
            f"  line       {self.line_max}, of which {self.structure} is structure",
        ]
        # Only where the caller could have named the anchor and did not (RK265). Said beside the
        # structure it moved, because a number resting on a guess and one resting on the id read
        # identically otherwise — and the guess is the one an `add --ref` can still correct.
        if self.ref_assumed:
            assumed = (
                f"§{self.ref} assumed, the widest this roadmap carries"
                if self.ref
                else "none on this roadmap, so the structure counts no pointer"
            )
            rows.append(f"  pointer    {assumed} — pass --ref for the anchor this line will use")
        rows.append(f"  prose      {self.prose}")
        for share in self.shares:
            # The field's own limit is what the schema publishes; what this line allows is what
            # refuses. Both, and which one binds, because that difference is the whole finding.
            bound = "  ← the line binds, not the field" if share.bound_by_line else ""
            # "drafted" and not "written" where the prose is the caller's (RK1190): the number
            # is the same and the two sentences are about different files, one of which has
            # nothing in it yet. And the surplus rather than a floored `0 left`, which is what
            # made a field three words over read as one exactly full.
            held = "drafted" if share.drafted else "written"
            spent = f", {share.over} over" if share.over else f", {share.left} left"
            taken = f", {share.taken} {held}{spent}" if share.taken else ""
            # The aim, beside the gate (RK185): the characters are what refuses and the words
            # are what a model can count towards, so both are stated and neither is converted.
            rows.append(
                f"  {share.field:<11}{share.allowed} of {share.limit}{taken}"
                f"  {share.aimed}{bound}"
            )
        rows += sourced(self.shares)
        # The other half of the same transaction (RK301): `add --section` writes a body too, and
        # the body's limit refused the whole `add` while this read named only the line's fields.
        if self.section is not None:
            rows.append(f"  section    {self.section.stated()}")
        elif self.section_absence:
            # An absence that is a defect is said, never left as a missing row (RK303): the
            # line's own two figures are still right, and the half nobody can price is the half
            # a caller would otherwise read as "this project keeps no rationale file".
            rows.append(f"  section    none — {self.section_absence}")
        return "\n".join(rows)

    def payload(self) -> dict[str, object]:
        return {
            "id": self.task.id,
            "status": self.task.status,
            "deps": [dep.render() for dep in self.task.deps],
            "open_line": self.open_line,
            "line_max": self.line_max,
            "structure": self.structure,
            # The pointer the structure was measured with, and whether anybody chose it (RK265):
            # a client comparing this budget against its own `add` needs to know the difference.
            "ref": self.ref,
            "ref_assumed": self.ref_assumed,
            "prose": self.prose,
            "fields": [share.payload() for share in self.shares],
            # The write this line is half of (RK301). Null where no prose file is declared,
            # which is the only project on which `add --section` does not exist.
            "section": None if self.section is None else self.section.payload(),
            # Why it is null, where that is a defect rather than a project shape (RK303). Empty
            # otherwise, so a client can tell the two nulls apart without a second call.
            "section_absence": self.section_absence,
        }


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
    why: str | None = None,
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

    ``why`` is the draft of that field (RK1190), and it is the one argument here that is
    **measured rather than composed**: `symptom` goes through
    :func:`~roadkeep.authoring.compose` because it is structure to the `why` — what it takes is
    what the other loses — while a `why` moves no other number, so putting it through the
    composer would buy nothing and cost the refusal this read exists to replace. ``None`` means
    no draft, which the empty string is not: `--why ""` asks what an empty field costs.
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
    return budget_of(
        config, task, open_line=open_line, ref_assumed=assumed, why=why
    )


def budget_of(
    config: Config,
    task: Task,
    *,
    open_line: bool,
    ref_assumed: bool = False,
    schema: Schema | None = None,
    why: str | None = None,
) -> Budget:
    """The same answer about a task the caller already holds — what `brief` hands over.

    Separate from :func:`budget` because the caller that has the line does not want it
    looked up again, and because a shipped one has no budget to state: the ledger is a
    different grammar, and the line an `amend` would rewrite is the open one.

    ``schema`` is which grammar the answer is about (RK1174). The roadmap's is the default and
    was the only one, which made the number `brief` printed the wrong one for the write an
    author was usually about to make: a `ship` writes a **ledger** line, whose allowance comes
    from `[limits.changelog]` and from a structure with no deps and no pointer in it. Measured
    on one task: 162 characters for the line that exists and 172 for the line it ships to.

    ``why`` is a draft to measure and not a field to set (RK1190): it changes what the answer
    *reports* about that share and nothing it is derived from, which is why it arrives here
    rather than on the task. ``None`` leaves the reading every caller before it had — the line's
    own prose, which is what `brief` wants and what an `amend` is about to replace.
    """
    schema = schema or config.schema
    prose = schema.prose_budget(task)
    # The structure is derived from the budget rather than measured again: `prose_budget` is
    # the one place that renders the emptied line, and a second measurement is a second answer.
    shares: list[Share] = []
    if schema.symptom_field:
        shares.append(
            Share(
                "symptom",
                schema.symptom_max,
                min(schema.symptom_max, prose),
                width(task.symptom),
                schema.source_of("symptom_max"),
                # A symptom on a line the roadmap does not hold came from the caller: there is
                # no file it could have come from, and `_subject` composed the task out of it.
                drafted=not open_line and bool(task.symptom),
            )
        )
    shares.append(
        Share(
            "why",
            schema.why_max,
            schema.why_budget(task),
            width(task.why if why is None else why),
            schema.source_of("why_max"),
            drafted=why is not None,
        )
    )
    section, absence = _section_of(config, task.ref or task.id, assumed=ref_assumed)
    return Budget(
        task=task,
        open_line=open_line,
        line_max=schema.line_max,
        structure=schema.line_max - prose,
        prose=prose,
        shares=tuple(shares),
        ref=task.ref,
        ref_assumed=ref_assumed,
        # The same anchor the line points at, which makes this one read for both halves of
        # the transaction (RK301): before the `add` it is the body about to be written, and
        # on an open line it is what a `section amend` has left.
        section=section,
        section_absence=absence,
    )


def _section_of(
    config: Config, anchor: str, *, assumed: bool = False
) -> tuple[Body | None, str]:
    """This anchor's body budget, or None and why there is none.

    Swallowing the refusal :func:`body_budget` raises rather than propagating it, because
    the caller asked about a *line*: a project that declares no rationale file has a legal
    `add` with no `--section` in it, and turning that into an error would refuse the read
    every other project uses. The same holds for an anchor two files declare (RK303) — the
    line's own two fields are unaffected by it — but that one is a defect and the other is
    not, so the reason rides back with the absence rather than the two reading identically.

    ``assumed`` says the anchor was **not chosen by anybody** — RK265's stand-in, the widest
    pointer the roadmap already carries, used so the *structure* of an unwritten line is
    never under-measured. Its occupancy is another task's, and reporting it answered the
    question backwards (RK1041): `296 written, 4 left` about a section this task will not
    write into, where what it gets is a fresh anchor and the whole limit. Measured twice in
    one session — once an under-written section, once three retries of `add` against a
    number bearing no relation to the limit enforced.

    So the guess is kept where it is honest and dropped where it is not: the line's own two
    fields still take the wider structure, and the section reads as the one an `add --section`
    would create. Naming a `--ref` makes the anchor the caller's and this branch is not taken,
    which is the read a child address wants (RK1029).
    """
    try:
        answer = body_budget(config, anchor)
    except AmbiguousAnchor as error:
        return None, str(error)
    except KeyError:
        return None, ""
    if assumed:
        answer = replace(answer, taken=0, subtree=0, written=False, under="", under_taken=0)
    return answer, ""


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


@dataclass(frozen=True, slots=True)
class Body:
    """A section body's budget, declared and counted in the unit it is declared in (RK283).

    Not a :class:`Share`, and deliberately: that one converts characters into an aim, and
    `section = <n>` is **already** in words — running it through the conversion would state
    a second number for a limit the config spells outright, which is RK258's finding at the
    other door. So this carries no `aim`: the limit is the aim.
    """

    anchor: str
    role: str
    limit: int
    #: This section's **own** prose, which is the argument an `amend` is about to replace.
    taken: int
    #: The same count over the subtree (RK287). Equal to :attr:`taken` on a leaf, and larger
    #: on a parent — reported beside it and never instead of it, because charging a container
    #: for its children names a figure the author cannot act on by editing the paragraph.
    subtree: int
    #: Whether the anchor names a section that exists. False is the pre-`section add` read,
    #: where the whole limit is free; True is the `amend`, which is where it matters — there
    #: the author holds a body and the number nobody has stated is what it has to fit inside.
    written: bool
    #: The ancestor address whose budget binds this one, and what it already spends (RK1029).
    #: `("", 0)` where none does — a top level, or a parent that is a container nothing points
    #: at, which the gate charges its own prose and not its children's.
    #:
    #: A **row and not a substitution**: the field's own limit is still the first number,
    #: because that is what the paragraph in front of the author has to fit, and this is the
    #: second one that decides whether the `add` after it lands. Before RK1029 there was
    #: nowhere to put it, so `budget --anchor IX.1` answered `30 words, aim 28` about a parent
    #: with one word of room — the pre-`add` read, wrong in the generous direction, on the one
    #: question this whole tool is built to answer before the prose exists.
    under: str = ""
    under_taken: int = 0
    #: A body the caller handed over to be measured, in words (RK1190). ``None`` is every call
    #: before this argument existed and means "no draft", which is not the same as an empty one.
    #:
    #: Its own field and never folded into :attr:`taken`, which is the difference from
    #: :class:`Share`: there, `allowed` is derived from the line and a draft can simply stand in
    #: for what is written. Here `allowed` is derived from :attr:`taken` — a replacement body is
    #: charged what its subsections spend and credited what its own prose gives back — so a
    #: draft written into that field would move the allowance it is being measured against.
    draft: int | None = None

    @property
    def over(self) -> int:
        """What the draft exceeds the replacement allowance by — 0 where it fits (RK1190).

        Against :attr:`allowed`, which is exactly what a write here accepts: the declared limit,
        less what this section's own subsections spend, less what a binding ancestor has taken
        elsewhere. Not against :attr:`left`, which asks a different question — how much *more*
        a written section could hold — and would price an amend as though it were an insert.
        """
        return 0 if self.draft is None else max(0, self.draft - self.allowed)

    @property
    def draft_left(self) -> int:
        """What the allowance still has under the draft — 0 where the draft is over."""
        return 0 if self.draft is None else max(0, self.allowed - self.draft)

    @property
    def under_left(self) -> int:
        """What the binding ancestor leaves this body, which is what the next write accepts.

        **Less what this section already contributes** (RK1035). The ancestor's total is
        billed with everything under it, this section included, so quoting it raw answered a
        written child with the room an *insert* would have — two figures and the subtraction
        between them, which is the analysis this door exists to remove rather than move.

        :attr:`taken` and not :attr:`subtree`: a write replaces this section's **own** prose
        and leaves its subsections where they are, so what comes back is what a replacement
        body may say and not what deleting the whole subtree would free. On an unwritten
        anchor both are zero and the answer is what it always was.
        """
        return max(0, self.limit - (self.under_taken - self.taken))

    @property
    def allowed(self) -> int:
        """The limit that actually binds this body — :attr:`Share.allowed` for a section.

        Every other field in this module reports the smaller of its own declared maximum and
        what the line leaves it, and until RK1036 this was the one that reported the larger.
        Measured on a parent whose subtree sat exactly at its limit: `30 words, 10 written,
        20 left … aim 18 more words`, an eighteen-word body refused, and ten what landed —
        both figures on the line and the subtraction between them the reader's.

        Two claims on one budget and the tighter wins. **Its own subtree**: a write replaces
        this section's prose and its subsections stay, so what they spend is gone before a
        word is composed. **Its binding ancestor** (RK1029): a subsection is charged to the
        address that owns it. On a leaf with no ancestor both are the declared limit, which
        is every section in a flat file and why this was invisible for so long.

        The declared limit stays :attr:`limit` and is still what a reader is shown first —
        RK1029's "a row and not a substitution" — and this is what the aim is derived from.
        """
        own = self.limit - (self.subtree - self.taken)
        ancestor = self.under_left if self.under else self.limit
        return max(0, min(self.limit, own, ancestor))

    @property
    def left(self) -> int:
        return max(0, self.allowed - self.taken)

    @property
    def aim(self) -> int:
        """What the body may be composed to, which is under what refuses (RK301)."""
        return body_aim(self.allowed)

    @property
    def room(self) -> int:
        """The same headroom applied to what is *left*, which is an amend's figure (RK245)."""
        return body_aim(self.left)

    @property
    def nests(self) -> bool:
        """Whether the section carries subsections, so the two counts are two numbers."""
        return self.subtree != self.taken

    def stated(self, named: bool = True) -> str:
        """A section body's budget as one line, shared by both doors that print it (RK283/301).

        Words throughout and no character figure beside them (RK258) — this limit is declared in
        words. The aim sits **under** the limit rather than on it (RK301): composing to exactly
        the declared number is what the thirteen measured refusals did.
        """
        spent = f", {self.taken} written, {self.left} left" if self.written else ""
        nested = f", {self.subtree} with subsections" if self.nests else ""
        aim = (
            f"aim {self.room} more words" if self.written else f"aim {self.aim} words"
        )
        where = f" ({self.role})" if named else ""
        # The row RK1029 added, and it is a row: the field's own limit stays the first number,
        # because that is what the paragraph has to fit — and this is the one that decides
        # whether the `add` after it lands.
        # The verb is the one that follows this read (RK1035): a written anchor's next write is
        # an `amend`, and naming an `add` there priced a section the caller is not about to
        # insert. The number changed with the sentence — `under_left` is now what a replacement
        # body may say, this section's own prose already discounted.
        door = "amend" if self.written else "add"
        binds = (
            f"\n  under      §{self.under} spends {self.under_taken} of {self.limit}"
            f", so {self.under_left} is what an `{door}` here accepts"
            if self.under
            else ""
        )
        # The draft last, because it is the only row that is a verdict (RK1190): everything
        # above is a fact about the file and this is what the paragraph in hand costs against it.
        return f"{self.limit} words{where}{spent}{nested}  {aim}{binds}{self._drafted()}"

    def _drafted(self) -> str:
        """The row the draft adds, or nothing where none was handed over (RK1190)."""
        if self.draft is None:
            return ""
        verdict = (
            f"{self.over} over — cut about {self.over} word(s)"
            if self.over
            else f"fits, {self.draft_left} word(s) spare"
        )
        return f"\n  draft      {self.draft} words against {self.allowed}: {verdict}"

    def payload(self) -> dict[str, object]:
        """One shape at both doors (RK301): the standalone read and the field on a line's own."""
        return {
            "anchor": self.anchor,
            "role": self.role,
            "written": self.written,
            # `unit` because this is the one budget already declared in words, and a client
            # reading `limit` beside a task's characters would otherwise compare the two.
            "unit": "words",
            "limit": self.limit,
            # What actually binds, which is `Share.allowed`'s field one door over (RK1036): the
            # smaller of the declared limit, what this section's own subsections spend, and what
            # a binding ancestor leaves. Equal to `limit` on a leaf in a flat file.
            "allowed": self.allowed,
            # Under the limit, not on it (RK301): the aim is what a body may be composed to.
            "aim": self.aim,
            "taken": self.taken,
            "left": self.left,
            "room": self.room,
            # Both figures, as `section show` carries both (RK287): `taken` is the argument and
            # this is what a reader pays for the whole subtree.
            "subtree": self.subtree,
            # The ancestor that binds, where one does (RK1029). Null and not omitted: a client
            # reading a missing key cannot tell "no ancestor" from "this server is older".
            "under": self.under or None,
            "under_taken": self.under_taken,
            "under_left": self.under_left if self.under else None,
            # The body the caller handed over, measured against `allowed` (RK1190). Null and not
            # zero where none was: an empty draft is a body of no words, which is a different
            # answer from no draft at all.
            "draft": self.draft,
            "over": self.over,
        }


def non_goal_budget(config: Config, lead: str | None = None) -> tuple[Share, ...]:
    """The two limits `non-goal add` enforces, before either field is composed (RK283).

    Both are characters and both are the list's own (RK70), so a caller reading a task's
    `why_max` here would be told a number this door does not use. Refused where the project
    has not opted in, for the reason the write is: a budget for a list nobody governs is a
    limit invented, and it would read as one the file is already held to.

    ``lead`` names a bullet that exists, which makes this the `add`'s answer or the rewrite's:
    what is taken comes off that bullet, so what is left is what a longer argument may still
    say. Neither field takes room from the other — a non-goal is two fields on two lines with
    no shared line limit — so :attr:`Share.allowed` is each one's own throughout.
    """
    if config.non_goals is None:
        raise NotGoverned(config.relative(config.source or config.root))
    scope = config.non_goals
    taken = {"lead": 0, "why": 0}
    if lead is not None:
        document = config.document("roadmap")
        wanted = address(lead)
        found = next((goal for goal in read(document) if address(goal.lead) == wanted), None)
        if found is None:
            raise NoSuchNonGoal(
                lead, config.relative(config.path("roadmap")), leads(document)
            )
        taken = {
            "lead": width(found.lead.strip()),
            "why": width(" ".join(found.why.split())),
        }
    return tuple(
        Share(field, limit, limit, taken[field])
        for field, limit in (("lead", scope.lead), ("why", scope.why))
    )


@dataclass(frozen=True, slots=True)
class Cost:
    """One unit of an always-loaded file's budget: what it may cost, and what it costs.

    Neither unit is converted into the other and neither carries an aim (RK345). Lines and
    bytes are what the loader pays and what `[budgets]` declares, so a word figure here
    would be this module inventing a third number for a limit the config spells outright —
    RK258's finding at the one budget whose units were never characters to begin with.
    """

    unit: str
    limit: int
    taken: int

    @property
    def left(self) -> int:
        return max(0, self.limit - self.taken)

    @property
    def over(self) -> int:
        """What the gate would refuse, which is the same subtraction the other way (RK30)."""
        return max(0, self.taken - self.limit)


@dataclass(frozen=True, slots=True)
class Part:
    """One `##` section of an every-turn file, and what it costs (RK1092).

    The read `budget --tools` makes about the served surface, made about the resident file:
    that one ranks tools so an author cutting the schema knows where the size went, and this
    one had only a total. `agents.md` reached 8,392 of 8,400 bytes and the next compression
    was a preference — RK203 says compress the prose rather than the Layout index, which was
    an argument made when the prose had slack and nothing re-measured since.

    Sections and not paragraphs, because a `##` is what the file itself declares and a
    paragraph is where a reader happened to stop. What this deliberately does not answer is
    which of them a turn *uses*: that needs a model of the reading, which is L4's own line,
    and a number invented for it would be worse than the total it replaced.
    """

    #: The heading, verbatim, or `""` for whatever stands above the first one.
    heading: str
    lines: int
    bytes: int


@dataclass(frozen=True, slots=True)
class Load:
    """What one every-turn file costs against what it declared it may (RK345)."""

    #: As the project spells it, which is how `[budgets]` addresses it and how `lint` names it.
    path: str
    costs: tuple[Cost, ...]
    #: Where the size is, by section, largest first (RK1092). Empty where the file is not on
    #: disk, which is the one state that has no content to attribute.
    parts: tuple[Part, ...] = ()
    #: False is the state `lint` reports as `budget.absent`: a budget with nothing under it.
    #: Said rather than answered as a free file, because the whole limit being available is
    #: the one reading that would make a missing file look like room.
    present: bool = True
    #: Bytes this checkout carries that the count above left out — one per `\r\n` (RK1105).
    #: Reported and never charged: the ceiling is the commit's, so the number that decides is
    #: normalised, and this is the honest remainder a loader on *this* machine really pays.
    #: 0 on an LF checkout, which is every question about the two being the same question.
    translated: int = 0

    @property
    def over(self) -> bool:
        return any(cost.over for cost in self.costs)

    @property
    def bytes(self) -> int:
        """What a loader pays for this file, or 0 where no byte budget was declared.

        A property and not a sum at the call site (RK1096): `budget --session` re-derived it
        by walking `costs` for the unit it wanted, which is this record's own arithmetic
        performed by a reader — the shape RK345 removed from the two that count the file.
        """
        return next((cost.taken for cost in self.costs if cost.unit == "bytes"), 0)


@dataclass(frozen=True, slots=True)
class Session:
    """Both halves of what a session pays, against the cadence each is paid at (RK1095).

    **Two figures and never a sum.** The schema is sent once at the handshake and a resident
    file is read on every turn, so adding them produces a number that is wrong for every
    session whose turn count is not one — which is all of them. What is honest is naming each
    against what it is paid for, and letting the reader multiply the half that repeats.

    A record since RK1170, and the refusal above is why it is worth one: the two registers
    each had to decline to add the same pair, in two places, by not writing a line.
    """

    #: The served schema, in characters — what the handshake costs, once.
    once: int
    #: How many tools that schema describes, which is what the figure is *of*.
    tools: int
    #: `(path, bytes)` per resident file, in the order `file_budget` answers.
    resident: tuple[tuple[str, int], ...] = ()

    @property
    def turn(self) -> int:
        return sum(cost for _path, cost in self.resident)

    def stated(self, unit: str) -> str:
        rows = [
            f"session    {self.once} {unit} once, {self.turn} bytes on every turn — "
            f"two cadences, so they are not added",
            f"  once     {self.once:>6}  {self.tools} tool(s) and the handshake, at connect",
        ]
        rows += [f"  turn     {cost:>6}  {path}" for path, cost in self.resident]
        if not self.resident:
            # The state `--file` raises on, said rather than left as an absent row: a project
            # with no `[budgets]` pays the schema and nothing else, which is a real answer.
            rows.append("  turn          0  this project declares no [budgets] file")
        return chr(10).join(rows)

    def payload(self, unit: str) -> dict[str, object]:
        return {
            # Named by cadence rather than by subject, because that is the fact a caller is
            # deciding against — and a `total` key would be the sum this read refuses.
            "once": {
                "characters": self.once,
                "unit": unit,
                "of": f"{self.tools} tool(s) and the handshake",
            },
            "each_turn": {
                "bytes": self.turn,
                "files": [
                    {"path": path, "bytes": cost} for path, cost in self.resident
                ],
            },
        }


def file_budget(config: Config, path: str | None = None) -> tuple[Load, ...]:
    """What the always-loaded files have left, before an edit is composed (RK345).

    The one limit this format holds that had no pre-write read. Every other budget here is
    answered from the id, the marker, the deps and the pointer; this one is answered from
    the file on disk and `roadkeep.toml`, and neither waited on the edit either — but the
    room was measured with two `wc` reads and a subtraction by hand, and the second spelling
    of a Layout entry was one line over. That is the analysis L1 exists to remove, one file
    over from the ones this tool governs.

    A tuple whether one file is named or none, so the shape does not depend on the question:
    unnamed is every declared budget, and named is the one — matched on the path the project
    declared *or* on any spelling that resolves to the same file, because the caller has the
    file open and not `roadkeep.toml`. Not a second gate (RK50): `lint` refuses the file that
    went over, this reports what is left, and both count through
    :func:`~roadkeep.config.spent`.
    """
    if not config.budgets:
        raise KeyError(
            f"{config.relative(config.source or config.root)} declares no [budgets]: "
            f"a budget for a file nobody declared is a limit invented here"
        )
    declared = config.budgets
    if path is not None:
        wanted = Path(path)
        resolved = (config.root / wanted).resolve()
        declared = tuple(
            one
            for one in config.budgets
            if config.relative(one.path) == str(wanted).replace("\\", "/")
            or one.path.resolve() == resolved
        )
        if not declared:
            named = ", ".join(config.relative(one.path) for one in config.budgets)
            raise KeyError(f"no [budgets] entry for {path}: this project budgets {named}")
    return tuple(_load(config, one) for one in declared)


def _load(config: Config, budget: ConfigBudget) -> Load:
    raw = budget.path.read_bytes() if budget.path.is_file() else None
    measured = spent(raw if raw is not None else b"")
    # Normalised before `_parts`, and not only in the total (RK1105): a breakdown counted off
    # the checkout sums past the number above it, and the reader comparing the two is deciding
    # what to cut. One convention, both figures.
    counted = b"" if raw is None else raw.replace(b"\r\n", b"\n")
    return Load(
        path=config.relative(budget.path),
        costs=tuple(
            Cost(unit, limit, measured[unit])
            for unit, limit in (("lines", budget.lines), ("bytes", budget.bytes))
            if limit is not None
        ),
        parts=_parts(counted) if raw is not None else (),
        present=raw is not None,
        translated=0 if raw is None else translated(raw),
    )


def _parts(raw: bytes) -> tuple[Part, ...]:
    """The file's `##` sections, largest first (RK1092).

    Bytes and never text, for the reason the budget itself is counted that way: an instruction
    file is not a format this tool decodes (L4). Handed the same normalised bytes the total is
    counted from (RK1105) — this sentence said the opposite while that was true of both, and a
    breakdown on the checkout's own terminator would sum past the number printed above it.

    Only `##`, because that is the level `agents.md` organises by — a `###` under one belongs
    to it, and splitting there would report a heading's own body as a sibling of its parent.
    """
    sections: list[tuple[str, list[bytes]]] = [("", [])]
    for line in raw.splitlines(keepends=True):
        if line.startswith(b"## "):
            sections.append((line.decode("utf-8", "replace").rstrip(), []))
        sections[-1][1].append(line)
    return tuple(
        sorted(
            (
                Part(heading=name, lines=len(body), bytes=sum(len(one) for one in body))
                for name, body in sections
                if body
            ),
            key=lambda part: (-part.bytes, part.heading),
        )
    )


def body_budget(
    config: Config, anchor: str, role: str | None = None, body: str | None = None
) -> Body:
    """What a section body may say, in words, before one is written (RK283).

    The longest thing an author composes and the limit that cost the most to meet at the
    door: 366 words against 300, discovered by writing 366. Everything it needs is the role's
    `section = <n>` and, for an `amend`, what the section already spends — both facts about
    the file, neither of which waited on the paragraph.

    The role is resolved the way every other reader resolves it (RK196) and never assumed to
    be `improvements`: the file that *holds* the anchor where one does, and otherwise the one
    a `section add` would write into — because an unwritten anchor is the pre-write question
    and the answer has to be about the file that write will land in. A named ``role`` wins.

    An anchor **two files declare is refused** (RK303), which is what every other reader of
    the same question does: `show` answers that the pointer resolves to neither, `ship`
    leaves the section rather than choosing which of the two the line meant, and the gate
    reports `section.ambiguous` at both headings. Answering with the first was the one door
    that had not learned it, and it priced a limit for a section the author cannot address —
    the number right about a file that was picked rather than named. ``role`` is the way
    through, because naming which of the two is meant is the only thing that resolves it and
    no verb here may resolve it by picking (L4).

    ``body`` is the draft this anchor is about to be given (RK1190), counted by the same reader
    the written prose is counted by rather than by a second one here: the gate, the write and
    this read all have to agree about what a word is, and the only way they can is by asking
    once. It is never composed and never validated — what comes back is
    :attr:`Body.over`, where an actual `section add` would come back a refusal.
    """
    named, where = role, config.relative(config.source or config.root)
    if role is None:
        # One resolver, called and not repeated (RK229) — the copy that lived here is the
        # copy that never learned what two declaring files mean.
        holders = declaring(config, anchor)
        if len(holders) > 1:
            raise AmbiguousAnchor(
                anchor, [config.relative(config.path(name)) for name in holders]
            )
        role = holders[0] if holders else prose_role(config)
    if role is None or not config.has(role):
        # Named or derived, and never the same sentence for both: a project that declares
        # `strategy` and was asked for it is a different mistake from one declaring neither.
        missing = f"declares no {named}" if named else "declares no prose file"
        raise KeyError(
            f"{where} {missing} to budget §{anchor} against: a section limit is a fact "
            f"about a role, and this one has no file to be a fact about"
        )
    section = find(config.document(role), anchor) if config.path(role).is_file() else None
    binds, spends = _binding(config, role, anchor)
    return Body(
        anchor=anchor,
        role=role,
        limit=config.schema_for(role).section_max,
        taken=0 if section is None else section.own_words,
        subtree=0 if section is None else section.words,
        written=section is not None,
        under=binds,
        under_taken=spends,
        # Counted by the reader that counts the written prose, never by a second one here.
        draft=None if body is None else prose_words(body),
    )


def _binding(config: Config, role: str, anchor: str) -> tuple[str, int]:
    """The ancestor whose budget decides what a body here may say, and what it spends (RK1029).

    Every ancestor and not the immediate one, because a parent with room under a grandparent
    with none is still a write the gate fails — and the *tightest* of them, since that is the
    one an `add` will actually be refused by. `("", 0)` where none binds.

    What binds is :func:`~roadkeep.sections.binding`, which is the same reading `add` now
    refuses on and the same one the gate bills: a container nothing points at is measured on
    its own prose, so it never binds a child, and reporting it here would price a body
    against a heading nobody charges (RK215).
    """
    tightest, spent = "", 0
    parent = anchor.rsplit(".", 1)[0] if "." in anchor else ""
    while parent:
        answer = binding(config, role, parent)
        if answer is not None and answer[0] > spent:
            tightest, spent = parent, answer[0]
        parent = parent.rsplit(".", 1)[0] if "." in parent else ""
    return tightest, spent


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


def sourced(shares: Sequence[Share]) -> list[str]:
    """Where the numbers above came from, as the one row that says it (RK1071).

    One line and not a parenthesis after each figure: the read is a column of small numbers
    and an address on every row drowns it, where the fact is almost always the same for all
    of them. Split only where the project declared some and not others, which is exactly
    when *which of these did I choose* is a live question — and silent where it declared
    none, because `this tool's default` five times over is the noise this avoids.
    """
    chosen = [share for share in shares if not share.source.endswith("default)")]
    if not chosen:
        return []
    # Grouped by the table, because that is what a reader opens: one file and one heading,
    # then the line each field is on. Two roles can differ (RK50), so the grouping is real
    # rather than cosmetic — a `[limits.changelog]` share sorts under its own key.
    tables: dict[str, list[str]] = {}
    for share in chosen:
        address, _, table = share.source.strip(" ()").partition(" ")
        file, _, lineno = address.partition(":")
        tables.setdefault(f"{file} {table.rsplit('.', 1)[0]}", []).append(
            f"{share.field}:{lineno}" if lineno else share.field
        )
    said = "; ".join(f"{table} {', '.join(fields)}" for table, fields in tables.items())
    fell_back = [share.field for share in shares if share not in chosen]
    rest = f"; {', '.join(fell_back)} is this tool's default" if fell_back else ""
    return [f"  declared   {said}{rest}"]
