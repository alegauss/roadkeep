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
    #: How many sentences this field accepts, or 0 where nothing bounds it (RK1225). A
    #: **rule** and not a width, and it belongs here for the reason every width does: it is
    #: knowable before a word exists and it refuses after one has been composed.
    sentences: int = 0
    #: Whether the field must end in a stop — the second rule over the same prose, published
    #: with it because `--why`'s own help says *one sentence, ending in a stop* while this
    #: read said only 200 and the line maximum. Two descriptions of one field disagreeing
    #: about what binds it is the state RK1225 is about.
    terminated: bool = False
    #: Whether the write this budget is about **replaces** this field rather than adding to it
    #: (RK1366). Every write that reaches one does — `amend --why`, `restate --symptom`,
    #: `non-goal amend --why`, and the two sentences RK1365 fixed a file over — so the room for
    #: the next one is the whole allowance and never the allowance less prose it deletes.
    #:
    #: :attr:`taken` is untouched by it and stays what the file holds, which is what
    #: :attr:`over` is measured on: an adopting corpus's standing drift is exactly the finding
    #: that number exists for, and zeroing the field to fix the remainder would take it out.
    #: False wherever the prose *is* carried forward — a retirement's derived prefix, which the
    #: author's reason is appended to (RK1305) — and false against a draft, where `taken` is
    #: the prospective prose and the remainder is the overrun the write will be refused by.
    replaced: bool = False

    @property
    def bounded(self) -> str:
        """The rules this field is held to beyond its width, as one clause or `""` (RK1225).

        Composed here rather than at the printer for :attr:`aimed`'s reason: which rules a
        field has is a fact about the share, and a second reader spelling them would be a
        second answer about what `add` will refuse.
        """
        said = []
        if self.sentences:
            said.append(f"{self.sentences} sentence" + ("s" if self.sentences > 1 else ""))
        if self.terminated:
            said.append("ending in a stop")
        return ", ".join(said)

    @property
    def left(self) -> int:
        """The room the *next* write has, which is the whole allowance where it replaces.

        RK1365 found this arithmetic wrong for the ledger's sentence and RK1366 for the line
        above it: nothing extends a one-sentence field, so `allowed - taken` described a write
        nobody makes. On one line here the two readings were 55 and 200, and the word aims
        beside them 8 against 31 — a quarter of the real figure, which is worse than none,
        because an author either composes to it or stops believing the row.
        """
        return self.allowed if self.replaced else max(0, self.allowed - self.taken)

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

        "More" only where there is prose to add to (RK1366): on a replaced field the whole
        figure *is* the remainder, and `aim 26 more words` beside a sentence about to be
        deleted reads as twenty-six on top of the twenty-one already there.
        """
        return (
            f"aim {self.room} more words"
            if self.taken and not self.replaced
            else f"aim {self.aim} words"
        )

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
            # And whether the write replaces it (RK1366), which is what makes `left` the whole
            # allowance rather than the difference. Published for `drafted`'s reason: a consumer
            # given `127 taken, 160 left` against a 160 allowance cannot otherwise tell an
            # arithmetic it should not reproduce from one it should.
            "replaced": self.replaced,
            # The rules that are not widths (RK1225). `0` is *unbounded* and not *one*, which
            # is what a project switching `[rules.<role>] one_sentence` off gets.
            "sentences": self.sentences,
            "terminated": self.terminated,
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

        Off :attr:`left` and not off `allowed - taken`, so RK1366's correction reaches the
        unit an author actually composes in: the characters are what refuses and this is the
        figure a sentence is written towards, so a wrong remainder here is the expensive half.
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
    #: The flags whose value came from the caller rather than from the line (RK1221). Empty on
    #: every call that named none, which is `brief`'s and every read of a line as it stands.
    stated: tuple[str, ...] = ()
    #: Prose **this tool writes into a field before the caller's** (RK1305), where a write does
    #: that. One write does: a retirement's `why` is a derived prefix plus the author's own
    #: sentence, and the prefix is counted against the same limit the reason is refused by. So
    #: it is neither structure — it is inside a prose field — nor the caller's, and a reader
    #: handed `21 written` on a field nobody has drafted has no way to tell which. Empty
    #: everywhere else, which is every budget about a line and every one about a ship.
    derived: str = ""
    #: The **departure** this budget is about, as the verb that makes it — `retire`, `ship` —
    #: or `""` for a line as it stands (RK1458). Its own field and no longer read off
    #: :attr:`derived`: that discriminator worked while a retirement was the only departure
    #: priced here, and a ship writes no prefix, so the second one arrived reporting itself as
    #: *the line add would write next*. Which write a figure is about is a fact about the call,
    #: and inferring it from a field that happens to be empty is how the two came apart.
    departure: str = ""

    def share(self, field: str) -> Share:
        return next(one for one in self.shares if one.field == field)

    def __str__(self) -> str:
        """What this line has for prose, one field per row — the register a reader scans.

        Beside :meth:`payload` since RK1170, and for that task's reason: these two were a printer
        inside the handler and a builder in `rendering.py`, so one answer was spelled in two files
        and neither held both. What the payload publishes is now what this shows, by construction
        rather than by a test.
        """
        # Three states and not two (RK1305): `open_line=False` meant *the line `add` would
        # write next* while this record now also answers for a line a **departure** writes, and
        # a retirement's figures under that sentence describe the wrong write entirely. Read off
        # the departure since RK1458, which is the fact rather than a proxy for it.
        if self.open_line:
            state = "open line"
        elif self.departure:
            state = f"the ledger line {self.departure} writes"
        else:
            state = "the line add would write next"
        deps = ", ".join(dep.render() for dep in self.task.deps) or "—"
        rows = [
            f"{self.task.id}  {self.task.status}  deps {deps}  ({state})",
            f"  line       {self.line_max}, of which {self.structure} is structure",
        ]
        if self.stated:
            # Said, because the number now depends on it (RK1221): a caller who passed
            # `--symptom` and reads an allowance has to be able to see that it was theirs, and
            # one whose flag matched the file changed nothing and is not told they did.
            rows.append(
                f"  yours      {', '.join(self.stated)} — measured as the line an `amend` "
                f"carrying them would write, not as the line on file"
            )
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
        if self.derived:
            # Before the field rows, because it is what those numbers are already carrying
            # (RK1305): `21 written` on a field nobody has drafted reads as the caller's prose
            # and is the tool's, and the remainder underneath is the one that binds either way.
            rows.append(
                f"  derived    `{self.derived}` — written into the why before a word of "
                f"yours, and counted against the same limit"
            )
        rows.append(f"  prose      {self.prose}")
        # One row and not a clause per field (RK1366), which is where `derived` puts the same
        # kind of note: what a remainder below means depends on this, and a reader handed
        # `127 written, 160 left` against a 160 allowance reads the two as adding up.
        if any(share.replaced and share.taken for share in self.shares):
            rows.append(
                "  replacing  what is written below, so each remainder is the whole allowance "
                "and not what is left beside it — no write extends one of these fields"
            )
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
            # The rules beside the widths (RK1225): a `why` that fits every number here and
            # arrives as two sentences is still refused, so a read that published only the
            # figures cost the composition it exists to save.
            held = f", {share.bounded}" if share.bounded else ""
            rows.append(
                f"  {share.field:<11}{share.allowed} of {share.limit}{taken}{held}"
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
            # Which flags the caller's own values came from (RK1221), so a consumer comparing
            # this against the file can tell an answer about the line from an answer about the
            # line an `amend` would write.
            "stated": list(self.stated),
            # What the tool wrote into a prose field before the caller's own (RK1305). Empty
            # and never omitted, for `section_absence`'s reason: a client can then tell a write
            # that derives nothing from a build that did not know the field existed.
            "derived": self.derived,
            # Which write this answers about (RK1458): `""` for a line as it stands, and the
            # verb otherwise. Beside `open_line` and not folded into it, the two answering
            # different questions — whether the line exists, and which write is being priced.
            "departure": self.departure,
        }

    def delta(self, base: "Budget | None", against: str | None) -> dict[str, object]:
        """This budget as what it **changes** about another, never as a second copy (RK1298).

        A brief prices three writes off one line — the line an `amend` rewrites, the ledger
        entry a `ship` composes, and the decision a `--decides` files — and published all three
        as whole tables. They differ in a handful of values; everything else repeats, per prose
        field and with the section sub-object byte-identical. That repetition is the largest
        thing in the payload which is not information, and it grows with every field a project
        declares a limit on — against a read whose whole claim is that it costs less than
        opening the file (RK1286).

        So the second and third tables are stated as their difference from the first: ``against``
        names the budget this was measured from, and ``changed`` carries only what moved. The
        figures stay reachable by overlay and none of them is published twice.

        Diffed off :meth:`payload` rather than off the fields, which is what keeps the two from
        drifting: a key added there is diffed here without this method learning its name. Fields
        are keyed by name because a delta addresses rows rather than ordering them, and a field
        that moved in nothing is absent — as is ``section``, whose whole point is that it is the
        same object. ``against`` of None means there was no base, and then ``changed`` is the
        whole table: one shape, whichever it is.
        """
        mine = self.payload()
        theirs = base.payload() if base is not None else {}
        changed = {
            key: value
            for key, value in mine.items()
            if key not in ("fields", "section") and theirs.get(key) != value
        }
        was = {row["field"]: row for row in theirs.get("fields", ())}  # type: ignore[union-attr]
        fields = {}
        for row in mine["fields"]:  # type: ignore[union-attr]
            before = was.get(row["field"], {})
            moved = {k: v for k, v in row.items() if k != "field" and before.get(k) != v}
            if moved:
                fields[row["field"]] = moved
        if fields:
            changed["fields"] = fields
        if mine["section"] != theirs.get("section"):
            changed["section"] = mine["section"]
        return {"against": against, "changed": changed}


def budget(
    config: Config,
    task_id: str | None = None,
    *,
    block: str = "",
    deps: Sequence[str] = (),
    requires: Sequence[str] = (),
    status: str | None = None,
    symptom: str = "",
    family: str | None = None,
    ref: str | None = None,
    why: str | None = None,
    body: str | None = None,
    retire: str | None = None,
    ship: bool = False,
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

    ``retire`` asks the **third** shape of the same question (RK1305): what a retirement's
    reason has, which is the one write this read did not answer for. `""` is an abandonment and
    an id is a supersession, because the two spend different amounts of the field before the
    author starts — and `None` is a caller who did not ask. Measured in an adopting project at
    three refusals in a row, 250 then 212 then 205 against 200, each rewrite cutting a clause
    out of the one field whose job is to carry evidence.

    ``ship`` is the **fourth** shape (RK1458), and the one two limits made necessary. The `why`
    on an open roadmap line and the `why` a `ship` writes to the ledger are different numbers,
    because the two lines carry different structure and what is left for prose differs. `brief`
    says both — it quoted `why 171 on this line` and, on the next line, `why 190 on the ledger
    line a ship writes` — and this read knew only the first. So a caller pricing a ship sentence
    read the number out of an earlier brief, or wrote to the stricter of the two and spent
    characters that were there, or to the looser and spent a refusal.

    **A subject and not a number**: `budget <id>` prices the line the id is on, and this asks
    about the line a departure would write instead. `defer` is the third such subject and is not
    here: its sentence is *wrapped around* the design the store carries forward rather than
    written before it, so what it carries is neither a prefix nor a replacement, and pricing it
    honestly needs a shape :class:`Budget` does not have yet.

    ``requires`` is the group `add --requires` puts on the line (RK1461), and this read had no
    way to be told it was coming. The gap is exact: `budget --block C --symptom … --why …`
    answered `why 165 of 200`, and the same sentence written with `add --block C --requires
    upstream` was refused `why: 158 characters, limit is 144` — 21 apart, which is the width of
    `(requires: upstream) `. Not a new idea about what this verb is: `--marker` is already a
    flag here and is the same kind of fact, something that changes what surrounds the prose
    rather than the prose.

    **Repeatable, like `deps`**, because two requirements cost two words and a separator and a
    flag taking one would answer the common case and quietly mis-price the rest — which is the
    failure being removed rather than a smaller version of it. Through
    :func:`~roadkeep.authoring.compose`, so the group the write reads back and the group priced
    here are one function's answer (RK1297). And it matters most where it is least reliable: a
    requirement is written by somebody filing work they cannot do, which is the moment the
    sentence has to say what is missing as well as what is wrong.
    """
    task, open_line, assumed = _subject(
        config,
        task_id,
        block=block,
        deps=deps,
        requires=requires,
        status=status,
        symptom=symptom,
        family=family,
        ref=ref,
    )
    if retire is not None:
        return _retirement(config, task, retire, why=why, body=body)
    if ship:
        return _shipment(config, task, why=why, body=body)
    answer = budget_of(
        config,
        task,
        open_line=open_line,
        ref_assumed=assumed,
        # The one caller that knows (RK1320): `--symptom` is prose this call was handed, and
        # a line the roadmap holds carries prose nobody typed here. `or None` and not the
        # string, because `--symptom ""` is not a draft — it is the absence of one, and the
        # tri-state `why` has is bought by an argument this one does not take.
        symptom=symptom or None,
        why=why,
        body=body,
    )
    # Named here and not inside `_subject`, which answers with a task: which flags the caller
    # supplied is a fact about the *call*, and the record that publishes it is this one.
    held = config.document("roadmap").by_id().get(task_id or "")
    return (
        answer
        if held is None
        else replace(
            answer,
            stated=_stated(
                held.task, block, deps, status, symptom, ref, requires
            ),
        )
    )


def _shipment(config: Config, task: Task, *, why: str | None, body: str | None) -> Budget:
    """What the sentence a `ship` writes has, before it is written (RK1458).

    Composed exactly as `brief`'s shipping row is and through the same function the write
    itself uses — :func:`~roadkeep.shipping.as_recorded` under `[limits.changelog]` — which is
    `_retirement`'s rule: a second computation of the ledger line's shape is how a figure and
    the write it describes come apart, and RK1199 is the task where they had.

    The `why` is **emptied** before the shape is composed (RK1365): `ship --why` is required
    and *replaces* the roadmap's sentence, so the room is the whole allowance, and pricing with
    the old one still in the field is what reported `37 of 200` against a ship that then
    accepted 145 — a number four times under the real one, failing in the direction that looks
    safe. Nothing is `derived` here, unlike a retirement: a ship writes no prefix, and a
    `--part` qualifier is structure this call cannot know will be passed.
    """
    from roadkeep.shipping import as_recorded  # noqa: PLC0415 - RK260

    schema = config.schema_for("changelog")
    return replace(
        budget_of(
            config,
            as_recorded(task, schema.shipped_marker, ""),
            open_line=False,
            schema=schema,
            why=why,
            body=body,
        ),
        departure="ship",
    )


def _retirement(
    config: Config, task: Task, superseded_by: str, *, why: str | None, body: str | None
) -> Budget:
    """What a retirement's reason has, before it is written (RK1305).

    Priced under the **changelog's** grammar for the reason `brief`'s shipping figure is
    (RK1199): a retirement writes a ledger line, whose limit is `[limits.changelog]` and whose
    structure carries no deps and no pointer. Through :func:`~roadkeep.shipping.as_recorded`,
    so the figure and the write cannot come apart.

    And the derived prefix goes **into the field** rather than beside it, which is the one
    thing this shape has that the other two do not: `abandoned:` and `superseded by RK41:` are
    written by `retire` before a word of the author's, and counted against the same limit the
    reason is refused by. So it is measured as prose the line already carries — `taken`, with
    `left` the remainder that binds — and named on :attr:`Budget.derived`, because a reader
    handed a non-zero `written` on a field nobody has drafted cannot tell whose it is.
    """
    from roadkeep.shipping import as_recorded, retiring  # noqa: PLC0415 - RK260

    prefix = retiring("", superseded_by or None)
    composed = f"{prefix}{why or ''}"
    return replace(
        budget_of(
            config,
            as_recorded(task, config.schema.retired_marker, composed),
            open_line=False,
            schema=config.schema_for("changelog"),
            # Drafted only where the caller drafted: the prefix is measured either way and is
            # the tool's, and `drafted` is the flag that says which of the two a number is.
            why=composed if why is not None else None,
            body=body,
        ),
        derived=prefix,
        departure="retire",
    )


def budget_of(
    config: Config,
    task: Task,
    *,
    open_line: bool,
    ref_assumed: bool = False,
    schema: Schema | None = None,
    symptom: str | None = None,
    why: str | None = None,
    body: str | None = None,
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

    ``symptom`` says the same thing about the other field, and it is **said rather than
    derived** (RK1320). Unlike ``why`` it is not a value this measures: the symptom is
    structure to the `why` — what it takes is what the other loses — so it has to be on the
    task before the line is rendered, and :func:`_subject` puts it there. What arrives here is
    only *whose it is*, which is the one fact no reading of the task can recover.
    """
    # The **roadmap's** schema and not the base one (RK1225). `[limits.roadmap]` and
    # `[rules.roadmap]` are what that file is held to (RK50, RK52), and `config.schema` carries
    # neither — so on a project declaring either, this answered with numbers and rules nobody
    # is judged by. Found publishing the sentence rule: a roadmap that had switched it off was
    # still told `1 sentence`, and the widths beside it were wrong in the same direction. The
    # same defect RK1199 fixed one role over, and `schema_for` is the reader both now use.
    schema = schema or config.schema_for("roadmap")
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
                # **Said and no longer derived** (RK1320). This read `not open_line and
                # bool(task.symptom)`, on the reasoning that a symptom on a line the roadmap
                # does not hold came from the caller — true of the pre-`add` read the flag was
                # written for, and false of every shape added since. `brief`'s `shipping` and
                # `deciding` price a task read off the *file* under the ledger's grammar, and
                # RK1305's retirement does the same, so one call answered `drafted: false` and
                # `drafted: true` about the same 93 characters off the same line.
                #
                # `open_line` was a proxy for *the caller composed this* and stopped being one
                # the moment a second reason to pass False existed. The caller that composed
                # the prose is the caller that knows, which is the argument `why` already takes.
                drafted=symptom is not None,
                # `restate --symptom` is the one write that reaches this field and it replaces
                # it (RK1366) — and only on a line that exists: the pre-`add` read has nothing
                # written, and the ledger's inherited claim is carried forward rather than
                # rewritten, which is `open_line` saying both at once.
                replaced=open_line and symptom is None,
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
            # The two rules this field has beyond its width (RK1225), read off the schema
            # exactly as the numbers are: a `why` that fits every figure published here and is
            # written as two sentences is still refused, which is this verb costing a
            # composition it exists to save. Per role, because `[rules.<role>]` switches them.
            sentences=1 if schema.one_sentence else 0,
            terminated=schema.terminator,
            # The same for `amend --why` (RK1366). False where the prose is carried forward
            # instead: a retirement's derived prefix is written *into* this field and the
            # author's reason is appended to it, so there the remainder is the difference and
            # `_retirement` reaches this through `open_line=False`.
            replaced=open_line and why is None,
        )
    )
    section, absence = _section_of(
        config, task.ref or task.id, assumed=ref_assumed, body=body
    )
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
    config: Config, anchor: str, *, assumed: bool = False, body: str | None = None
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
        answer = body_budget(config, anchor, body=body)
    except AmbiguousAnchor as error:
        return None, str(error)
    except KeyError:
        return None, ""
    if assumed:
        answer = replace(answer, taken=0, subtree=0, written=False, under="", under_taken=0)
    return answer, ""


def _stated(
    task: Task,
    block: str,
    deps: Sequence[str],
    status: str | None,
    symptom: str,
    ref: str | None,
    requires: Sequence[str] = (),
) -> tuple[str, ...]:
    """Which of the caller's fields differ from the line's own, by flag name (RK1221).

    The answer names them, which is the half of RK465 a silent override would still be missing:
    a caller who passed `--symptom` and gets a number back has to be able to see that it was
    *their* symptom that produced it, and a caller who passed one identical to the file's has
    changed nothing and should not be told they did.
    """
    given = (
        ("--block", block, task.block),
        ("--symptom", symptom, task.symptom),
        ("--marker", status, task.status),
        ("--ref", ref, task.ref),
    )
    named = [flag for flag, stated, held in given if stated and stated != held]
    if deps and tuple(deps) != tuple(dep.render() for dep in task.deps):
        named.append("--dep")
    # The group the write adds and this read could not be told about (RK1461), named for the
    # reason every other flag here is: the caller has to see that the number is theirs.
    if requires and tuple(requires) != tuple(task.requires):
        named.append("--requires")
    return tuple(named)


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
    requires: Sequence[str] = (),
) -> tuple[Task, bool, bool]:
    """The line the budget is about, whether the roadmap holds it, and whether it guessed.

    **Every field the caller states wins over the file's** (RK1221), which until then was true
    of `--ref` alone. The other arm composes a line out of `--block`, `--dep`, `--marker` and
    `--symptom`; this one read all four and discarded them, so `budget RK12 --symptom "<a
    rewrite I am weighing>"` answered about the symptom already on the line and said so
    nowhere. RK465 named that shape — a narrowing flag nobody reads is worse than a refused
    one, because the caller reads a number believing it narrowed it — and RK1190 sharpened it,
    `--symptom` now being a draft to *measure*, which is exactly what an author weighing an
    `amend` passes.

    Honoured rather than refused, and all four rather than one: the deps and the marker move
    the allowance as the symptom does, so taking one and ignoring the others would make four
    flags mean two things. What comes back is the line an `amend` carrying those arguments
    would write, which is the question that was being asked.

    Re-composed and never `replace`d, so the rule each field is subject to is applied by the
    one function that owns it (RK265): a `--ref` under the id scheme is refused here exactly as
    the `amend` will refuse it, and so is a block no heading declares.
    """
    if task_id is not None:
        entry = config.document("roadmap").by_id().get(task_id)
        if entry is not None:
            task = entry.task
            stated = _stated(task, block, deps, status, symptom, ref, requires)
            if not stated:
                # Nothing of the caller's to apply, which is every call before RK1221 and the
                # one `brief` makes: the entry's own task, untouched and uncomposed.
                return task, True, False
            return (
                compose(
                    config,
                    task_id=task.id,
                    block=block or task.block,
                    symptom=symptom or task.symptom,
                    why=task.why,
                    status=status or task.status,
                    deps=tuple(deps) if deps else tuple(dep.render() for dep in task.deps),
                    requires=(
                        tuple(requires) if requires else tuple(task.requires)
                    ),
                    ref=ref if ref is not None else task.ref,
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
            requires=requires,
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
    what is taken comes off that bullet, and what is left is the whole allowance, because
    `non-goal amend --why` replaces that argument and a changed lead is a drop and an add
    (RK1366). Neither field takes room from the other — a non-goal is two fields on two lines
    with no shared line limit — so :attr:`Share.allowed` is each one's own throughout.
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
        Share(field, limit, limit, taken[field], replaced=lead is not None)
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

    The read `cost --tools` makes about the served surface, made about the resident file:
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
    #: The section in UTF-16 code units, or `None` where the file does not decode (RK1253).
    #: The reading :attr:`Load.characters` is, one level down — charged by nothing and
    #: **never ranked on**: the order is the ceiling's (RK1252), and a list sorted by a figure
    #: nothing refuses would answer a question the gate never asks while looking like the one
    #: that does. A column, so the author cutting to fit the served comparison has the weight
    #: of each section without the list changing what it is about.
    #:
    #: `None` for the whole file or for none of it, which :func:`_parts` enforces rather than
    #: discovers. One direction is free: a UTF-8 continuation byte is never a newline, so
    #: splitting on line boundaries cannot break a sequence, and a file that decodes has
    #: sections that all do. The other is not — one bad byte makes the *file* undecodable
    #: while its other sections read fine, and reporting those would be a breakdown that does
    #: not sum to the total above it. So the absence is the file's and never a section's.
    characters: int | None = None


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
    #: The same text in UTF-16 code units, or `None` where there is no answer — the file is
    #: absent, or it is not UTF-8 (RK1245). Beside `bytes` and never instead of it: `bytes` is
    #: what `[budgets]` declares and `lint` refuses on, and this is what a *reader* pays,
    #: which is the comparison `cost --session` exists to make against the served schema.
    #:
    #: Charged by nothing. :func:`~roadkeep.config.spent` stays bytes-only for the reason its
    #: own docstring gives — an instruction file is not a format this tool decodes (L4) — so
    #: this is a second reading of the same normalised bytes and never a second budget.
    characters: int | None = None

    @property
    def over(self) -> bool:
        return any(cost.over for cost in self.costs)

    @property
    def bytes(self) -> int:
        """What a loader pays for this file, or 0 where no byte budget was declared.

        A property and not a sum at the call site (RK1096): `cost --session` re-derived it
        by walking `costs` for the unit it wanted, which is this record's own arithmetic
        performed by a reader — the shape RK345 removed from the two that count the file.
        """
        return next((cost.taken for cost in self.costs if cost.unit == "bytes"), 0)

    @property
    def tightest(self) -> Cost | None:
        """The declared unit that will refuse first, or `None` where none is declared.

        The room in one clause (RK1248). `--file` prints a row per unit because it is *about*
        this file; `--session` prints a row per file because it is about the session, and a
        line carrying every unit's room would spend the comparison it exists for on a
        breakdown the other read already gives.

        **Tightest and not first**, measured as the share taken rather than the count left: a
        file 21 lines and 1494 bytes from its ceilings is nearer the first of them, and the
        one that refuses is the one to name. Ties go to the earlier unit, which is `lines`,
        because a tie is two right answers and picking is not this property's decision.
        """
        return min(
            (cost for cost in self.costs if cost.limit),
            key=lambda cost: (-(cost.taken / cost.limit), self.costs.index(cost)),
            default=None,
        )

    @property
    def ranked(self) -> tuple[Part, ...]:
        """The sections, largest first **in the unit that will refuse this file** (RK1252).

        :func:`_parts` sorted by bytes always, and RK1248 made the cost of that visible: the
        limit about to refuse may be `lines`, and a breakdown ranked by bytes then names a
        section that is not the one to cut. `agents.md` at 104 of 125 lines and 6906 of 8400
        bytes is a line problem, and its longest section by bytes is a table.

        Keyed on :attr:`tightest` and not on a preference, so the ranking and the room are one
        decision — which is what stops the report advising against the ceiling it just stated.
        Bytes where nothing is declared, which is the order this always had.

        Ties by heading, as :func:`_parts` does, because a tie is two right answers and the
        stable one is the one a second run reproduces.
        """
        cost = self.tightest
        unit = "bytes" if cost is None else cost.unit
        return tuple(
            sorted(self.parts, key=lambda part: (-getattr(part, unit), part.heading))
        )

    @property
    def room(self) -> str:
        """What the tightest declared limit has left, as the clause `--session` prints.

        Here and not at the reader for :attr:`bytes`' reason (RK1096): the subtraction is
        :class:`Cost`'s and the choice of which cost is this record's, so a caller composing
        either would be performing this record's arithmetic.
        """
        cost = self.tightest
        if cost is None:
            return ""
        if cost.over:
            return f"over by {cost.over} {cost.unit} of {cost.limit}"
        return f"{cost.left} {cost.unit} left of {cost.limit}"


def _resident(load: Load) -> str:
    """One every-turn file as a `--session` row: the figure, the path, and what they are.

    **Three states and not a reason with a default** (RK1251). RK1245 gave :class:`Load` a
    `characters` field and printed *bytes, because this file is not UTF-8* wherever it was
    `None` — which is true of a file that does not decode and false of a file that is not
    there, and `None` is what both leave. So a project whose declared `agents.md` is missing
    was told this tool could not read it.

    Both other surfaces already say it plainly: `budget --file` prints `not on disk — the
    entry holds nothing`, and `lint` reports `budget.absent`, a finding that exists precisely
    because a budget with nothing under it is the one reading that makes a missing file look
    like room. This row was the third statement of that state and the only wrong one.

    So the absent row **states no room either**, which is the other half RK1251 named: `10
    lines left of 10` is arithmetically true and is the sentence `budget.absent` exists to
    contradict. :attr:`Load.present` carries the distinction and always did.
    """
    if not load.present:
        return f"{0:>6}  {load.path}  not on disk — the entry holds nothing"
    figure = load.bytes if load.characters is None else load.characters
    said = f"{figure:>6}  {load.path}"
    if load.characters is None:
        said += "  (bytes: this file is not UTF-8)"
    # The room the project's own `[budgets]` line declares (RK1248), in the unit it declared
    # it in — which is named, because the figure to its left is not in it.
    return f"{said}  {load.room}" if load.room else said


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
    #: Every resident file, in the order `file_budget` answers. The records themselves since
    #: RK1248 and no longer a widening tuple of their fields: this read wanted a third of them
    #: and then a fourth, and a projection is what RK1244 had just finished removing one
    #: surface over — :class:`Load` already *is* what one every-turn file costs against what
    #: it declared, which is exactly what a row here is about.
    resident: tuple[Load, ...] = ()
    #: The `SessionStart` notice, in the same unit as :attr:`once` (RK1243). The third thing
    #: a session pays for, and the one nothing counted: it is resident for the whole session
    #: in every governed project, it has a ceiling, and until now the ceiling was a constant
    #: a test asserted a fixture against. Measured **without** the drift sentence (RK234),
    #: which is deliberately over that ceiling and goes away with one `install` — what is
    #: priced here is what every session gets.
    notice: int = 0
    #: What the notice may cost, so the room is stated beside the figure — RK345's pairing,
    #: and the reason this is a read rather than a second gate.
    notice_limit: int | None = None
    #: What the served surface may cost, for the row that had no such pairing (RK1333). The
    #: notice beside it derived `+15 of 320` while this one printed 64679 and stopped, though
    #: `[tools] session` declares the ceiling and `budget.session` is the single finding that
    #: refuses the total against it — so there was one number to name and the row named none.
    #: Measured at 21 characters of room, which is the next sentence added to any one of 66
    #: tool descriptions: the reader most likely to run this verb is the one it answered
    #: least. Same pairing as :attr:`notice_limit` and for the same reason it is a read.
    once_limit: int | None = None
    #: The part of :attr:`once` that names the checkout rather than the surface (RK1334) —
    #: counted in, because a session is sent it, and out of what the ceiling is measured on,
    #: because no author can edit it. Its own row so the subtraction is visible: a figure that
    #: silently differed from the one the gate used would be RK1333's defect rebuilt.
    provenance: int = 0

    @property
    def turn(self) -> int:
        """What a turn costs **a reader**, in the unit the once-per-session figures are in.

        Code units and not bytes (RK1245), which is the whole point of the read: this verb
        exists so an author can decide between cutting a tool description and cutting a
        paragraph, and until now it asked them to make that comparison across two units. On
        ASCII prose the two agree and the defect is invisible; on a paragraph carrying the
        status markers this tool writes, bytes are three times code units and the choice a
        reader makes from these numbers is the wrong one.

        A file that does not decode falls back to its bytes, which is the closest true thing
        available and is named as such in the row beneath.
        """
        return sum(
            load.bytes if load.characters is None else load.characters
            for load in self.resident
        )

    @property
    def declared(self) -> int:
        """The same files in the unit `[budgets]` declares, which is what `lint` refuses on.

        Stated and never converted into the figure above: the gate reads bytes for the reason
        :func:`~roadkeep.config.spent` gives — a budget is what a *loader* pays and an
        instruction file is not a format this tool decodes (L4). Two honest readings of one
        set of files, so the report can be compared without the gate being moved.
        """
        return sum(load.bytes for load in self.resident)

    @property
    def at_connect(self) -> int:
        """Everything paid once, which is the schema **and** the notice (RK1243).

        Added, where :attr:`once` and :attr:`turn` are not: the rule this record keeps is
        that two *cadences* may not be summed, and these two share one. A reader deciding
        whether to cut a tool description or a sentence from the notice is deciding inside
        one budget, which is exactly the arithmetic RK1095 removed from the pair above.
        """
        return self.once + self.notice

    @staticmethod
    def _room(taken: int, limit: int | None) -> str:
        """The room beside a figure, in the one spelling both once-rows use (RK1333).

        Shared rather than repeated because the defect was the two rows disagreeing about
        whether a ceiling gets named at all: a second copy is what let one of them keep a
        pairing the other never grew. A limit nothing declares stays silent, which is the
        state a project with no `[tools]` table is in and is not a finding.
        """
        return "" if limit is None else f", {limit - taken:+} of {limit}"

    def _measured_on(self) -> str:
        """What the room above was taken against, where that is not the figure beside it.

        RK1423. The row printed `64249 … +116 of 64300` on this repository, and those three
        numbers are about two totals: 65 of the 64249 names the checkout, no ceiling is about
        it, and the room is 64300 less the 64184 held. A reader subtracting the two numbers on
        the line got 51 — under half the truth, on the one read whose whole purpose is
        deciding whether another tool fits.

        The held figure is named **in the clause** rather than put in the leading column,
        which is where the row below it was already the answer and was not enough: that column
        is what each row costs, on every row, and swapping one of them for a smaller number
        makes the column mean two things and drops the total from the report entirely. Said
        here, the line reconciles on its own and the row below still says where the rest went.

        Silent with no provenance and with no ceiling, which are the two states where the
        figure beside the room is already the figure it was measured on.
        """
        held = self.once - self.provenance
        if not self.provenance or self.once_limit is None:
            return ""
        return f", on the {held} held"

    def stated(self, unit: str) -> str:
        rows = [
            f"session    {self.at_connect} {unit} once, {self.turn} on every turn — "
            f"two cadences, so they are not added",
            f"  once     {self.once:>6}  {self.tools} tool(s) and the handshake, at "
            f"connect{self._room(self.once - self.provenance, self.once_limit)}"
            f"{self._measured_on()}",
        ]
        if self.provenance:
            # Named under the figure it is inside, so the row above reads as a subtraction
            # somebody can check rather than as a number that disagrees with the total.
            rows.append(
                f"  once     {self.provenance:>6}  of that names the checkout — no ceiling "
                f"is about it"
            )
        if self.notice:
            rows.append(
                f"  once     {self.notice:>6}  the session-start notice"
                f"{self._room(self.notice, self.notice_limit)}"
            )
        rows += [f"  turn     {_resident(load)}" for load in self.resident]
        if not self.resident:
            # The state `--file` raises on, said rather than left as an absent row: a project
            # with no `[budgets]` pays the schema and nothing else, which is a real answer.
            rows.append("  turn          0  this project declares no [budgets] file")
        elif self.declared != self.turn:
            # Named once and not per row (RK1245): the conversion is one fact about the set,
            # and repeating it beside each file would spend the report on the difference
            # rather than on the comparison the reader came for. Silent where they agree,
            # which is every ASCII project and is where there is nothing to say.
            #
            # And it stops at the conversion (RK1249). It used to say bytes is *what `lint`
            # refuses on*, which is a third statement of the gate that neither the gate nor
            # the rows above agree with: `[budgets]` declares two units, `lint` emits
            # `budget.lines` and `budget.bytes` each naming its own, and the row above this
            # one already says which of them will refuse *this* file. A summary taking the
            # last word reads as the general rule, so what it may claim is only what it knows.
            rows.append(
                f"  bytes    {self.declared:>6}  the same files in the unit `[budgets]` counts"
            )
        return chr(10).join(rows)

    def payload(self, unit: str) -> dict[str, object]:
        return {
            # Named by cadence rather than by subject, because that is the fact a caller is
            # deciding against — and a `total` key would be the sum this read refuses.
            "once": {
                # The cadence's whole figure, with its two parts named under it (RK1243):
                # a caller acting on this is choosing which of them to cut.
                "characters": self.at_connect,
                "unit": unit,
                "of": f"{self.tools} tool(s) and the handshake, and the session-start notice",
                "schema": self.once,
                # Beside the figure it bounds, as the notice's is (RK1333): a consumer
                # reading `schema` to decide whether a description may grow was getting the
                # only number here that carried nothing to measure it against.
                "schema_limit": self.once_limit,
                # What the limit is actually measured on, beside what it is (RK1334): a
                # consumer subtracting these itself would be deriving the gate's number,
                # which is the duplication RK1096 removed one surface over.
                "schema_provenance": self.provenance,
                "schema_held": self.once - self.provenance,
                "notice": self.notice,
                "notice_limit": self.notice_limit,
            },
            "each_turn": {
                # The reader's unit, so the two cadences are comparable (RK1245) — with the
                # gate's own figure beside it rather than converted away.
                "characters": self.turn,
                "unit": unit,
                "bytes": self.declared,
                "files": [
                    {
                        "path": load.path,
                        "bytes": load.bytes,
                        "characters": load.characters,
                        # Which of the two absences a null `characters` is (RK1251): a file
                        # that is not there and one this could not decode are different
                        # states, and a caller reading only the null cannot tell them apart.
                        "present": load.present,
                        # The tightest declared limit and what it has left, so a caller acts
                        # on the one that refuses rather than on the first declared (RK1248).
                        "limit": None
                        if load.tightest is None
                        else {
                            "unit": load.tightest.unit,
                            "declared": load.tightest.limit,
                            "left": load.tightest.left,
                            "over": load.tightest.over,
                        },
                    }
                    for load in self.resident
                ],
            },
        }


@dataclass(frozen=True, slots=True)
class Skilled:
    """What the write path costs the turns that load it (RK1424).

    The fourth cadence, and the one nothing counted. `[budgets]` prices what loads on *every*
    turn and excludes this on purpose — pricing a trigger-loaded file as resident is the third
    figure `cost --session` exists to avoid inventing (RK23) — but that settles which table it
    is not in, not whether the number is worth having. Measured when this was filed:
    65,180 code units against a served schema of 64,258 with a ceiling of 64,300. The largest
    single thing a session is handed was the one thing no read named.

    **No limit, and that is the record's shape rather than an omission.** `govern` refuses a
    ceiling this corpus already breaks, so declaring one here would be a number chosen before
    the reading that decides it. This is the reading. What it reports is what `weight` and
    `adopt` report: the figure and where it went, with the judgement left to whoever takes it.
    """

    #: Where the copy answering lives, as a caller would say it: the project's own vendored
    #: file, or the checkout that is running. Named for `engines`' reason — three copies can
    #: be reachable and which one answered decides what the number is about.
    path: str
    #: ``project`` for a copy `install` vendored, ``checkout`` for the tree answering, and
    #: ``""`` where neither is there. A word and not a boolean: the two present states are
    #: different facts about a session, and a third is coming the day the plugin cache is read.
    origin: str
    bytes: int = 0
    lines: int = 0
    #: The reading a session is charged in, and the one comparable with the served schema —
    #: `None` where the file does not decode, which is :attr:`Load.characters`' own state.
    characters: int | None = None
    #: Where the size is, by `##` section and largest first — :func:`_parts`, unchanged. The
    #: whole of what an author cutting this file needs, and the reason the total alone would
    #: have been a number with nowhere to act on it (RK1092).
    parts: tuple[Part, ...] = ()
    #: The reference pages beside the file that answered, each as its own row (RK1437). A
    #: **third** cadence: the figure above is paid by every turn the skill loads on, and each
    #: of these by the turns that open that page — so they are reported beside it and never
    #: added to it, for the reason the served schema is not added either. Empty where the copy
    #: answering is one from before the split, which is a reading and not an error: an
    #: orientation with no pages beside it is a skill that still holds its own reference.
    pages: tuple[Part, ...] = ()

    @property
    def present(self) -> bool:
        return bool(self.origin)

    def stated(self, unit: str, schema: int) -> str:
        """The figure, what it is beside, and where it went — three sections and the rest.

        ``schema`` is what the tool schema costs, passed in rather than read here: the whole
        point of the number is the comparison, and a reader given this alone has to run a
        second command to know whether 65,180 is large.
        """
        from roadkeep.provenance import invocation  # noqa: PLC0415 - RK260

        if not self.present:
            return (
                "skill      absent — no vendored copy and none in the tree answering; the "
                f"plugin ships it, and `{invocation()} engines` names the copies"
            )
        counted = self.bytes if self.characters is None else self.characters
        # Counted rather than written: the sentence names how many cadences the rows below
        # actually show, so a skill with no pages beside it is not told about a third.
        cadences = "three" if self.pages else "two"
        rows = [
            f"skill      {counted} {unit} on every turn that loads it, against {schema} "
            f"for the served schema once at connect — {cadences} cadences, so they are not added",
            f"  {self.origin:<9}{self.path}  {self.lines} line(s), {self.bytes} bytes",
        ]
        rows += [
            f"  section  {(part.characters if part.characters is not None else part.bytes):>6}"
            f"  {part.heading or '(above the first heading)'}"
            for part in self.parts[:3]
        ]
        if len(self.parts) > 3:
            rows.append(
                f"  … and {len(self.parts) - 3} more — `--json` lists every one"
            )
        # The pages, every one of them and never a top three: there are two, and a reader
        # deciding whether to open one needs the price of the one they were about to open.
        rows += [
            f"  page     {(page.characters if page.characters is not None else page.bytes):>6}"
            f"  {page.heading}  on the turns that open it, not on every turn"
            for page in self.pages
        ]
        return chr(10).join(rows)

    def payload(self, unit: str, schema: int) -> dict[str, object]:
        return {
            "path": self.path,
            "origin": self.origin or None,
            "present": self.present,
            "characters": self.characters,
            "unit": unit,
            "bytes": self.bytes,
            "lines": self.lines,
            # Beside the figure and never subtracted from it: the two are paid at different
            # cadences, which is the sum `cost --session` refuses one surface over.
            "schema": schema,
            # No `limit` key. Nothing declares one, and publishing `null` would read as a
            # ceiling this build failed to find rather than as one nobody has argued for.
            "sections": [
                {
                    "heading": part.heading,
                    "lines": part.lines,
                    "bytes": part.bytes,
                    "characters": part.characters,
                }
                for part in self.parts
            ],
            # Its own key and never folded into `sections`: a section is part of the figure
            # above and a page is a separate charge, and one list would invite a sum that is
            # the reading this record exists to refuse (RK1437).
            "pages": [
                {
                    "path": page.heading,
                    "lines": page.lines,
                    "bytes": page.bytes,
                    "characters": page.characters,
                }
                for page in self.pages
            ],
        }


def skill_cost(config: Config) -> Skilled:
    """The skill this project's sessions would load, and what it costs them (RK1424).

    Two copies can answer and the order is what a session actually reads: a project that ran
    `install` has the skill vendored under `.claude/`, and that copy is the one its sessions
    load — stale or not, which is `install.stale`'s business and not this read's. Failing
    that, the tree answering is asked, which is the checkout's own shipped copy.

    A project using the plugin without vendoring has neither, and that is reported rather than
    guessed at: the file is inside a plugin cache this read does not resolve, `engines` is the
    verb that does, and a number taken from the wrong copy is worse than no number.

    Bytes off disk and the code units beside them, for :class:`Load`'s reason — the gate
    counts bytes and a reader pays characters, and this figure exists to be compared with the
    served schema, which is in code units.
    """
    from roadkeep.installing import PLUGIN_PAGES, PLUGIN_SKILL, PROJECT_SKILL  # noqa: PLC0415
    from roadkeep.provenance import engine  # noqa: PLC0415 - RK260

    candidates = (
        ("project", config.root / PROJECT_SKILL),
        ("checkout", engine().home.parent.parent / PLUGIN_SKILL),
    )
    for origin, path in candidates:
        try:
            raw = path.read_bytes()
        except OSError:
            continue
        counted = raw.replace(b"\r\n", b"\n")
        return Skilled(
            path=config.relative(path) if origin == "project" else path.as_posix(),
            origin=origin,
            bytes=len(counted),
            lines=counted.count(b"\n"),
            characters=_characters(counted),
            parts=_parts(counted),
            # Beside the file that answered, which is the directory a loader reads and the
            # only place the orientation's own pointers resolve (RK1437). Absent is silence:
            # a copy from before the split has none, and `install --check` is the read that
            # says a vendored skill is behind — not this one.
            pages=_pages(path.parent, PLUGIN_PAGES),
        )
    return Skilled(path=PROJECT_SKILL, origin="")


def _pages(home: Path, named: tuple[str, ...]) -> tuple[Part, ...]:
    """The reference pages present beside a skill, in the order the plugin declares them."""
    found = []
    for page in named:
        beside = home / page.rsplit("/", 1)[1]
        try:
            raw = beside.read_bytes().replace(b"\r\n", b"\n")
        except OSError:
            continue
        found.append(
            Part(
                heading=beside.name,
                lines=raw.count(b"\n"),
                bytes=len(raw),
                characters=_characters(raw),
            )
        )
    return tuple(found)


@dataclass(frozen=True, slots=True)
class Denied:
    """What one refused write costs the session that meets it (RK1428).

    `guarding.py` hands a session two texts and only the small one was measured: the
    session-start notice is held to `_NOTICE_BUDGET` and printed beside it by `cost
    --session`, while the denial — thirteen times larger on this project — was priced by
    nothing. It is also the one paid **per denial**, by a plugin whose whole purpose is to
    produce them.

    **Both spellings, because they are two different messages** (RK447). A session with a
    server for the tools is offered them and the shell table beside it; one without gets the
    shell alone. Neither is derivable from the other, so a single figure would be a number
    that is right for one caller and wrong for the other.

    No limit, for `Skilled`'s reason: `govern` refuses a ceiling this corpus already breaks,
    and what it should be is a reading nobody had taken. This is the reading.
    """

    #: The denial **this project's** sessions meet, in UTF-16 code units — composed with
    #: the prefix `provenance.served_by` says they get, so a project with no server is
    #: measured as the one it is rather than as the one this repository happens to be.
    here: int
    #: The same denial where nothing serves the tools — the shell table alone. Equal to
    #: :attr:`here` on a project with no server, which is not a duplicate but the answer.
    bare: int
    #: What the served denial spends re-spelling the write vocabulary as shell commands,
    #: which is the half a caller addressed by its MCP names has already been given (RK447,
    #: RK448). Reported and never judged: whether it is redundant there or is the fallback for
    #: an agent that has stopped trusting the tools is an argument, not an arithmetic.
    #:
    #: `0` where nothing is served, and that is the answer rather than an absence: with no
    #: tool table above it the shell one is not a second spelling, it is the only one.
    shell: int
    lines: int
    #: The other text this module hands a session, and the ceiling it is held to — beside the
    #: figure, because the whole finding is that one of the two is measured and one is not.
    notice: int = 0
    notice_limit: int | None = None

    def stated(self, unit: str) -> str:
        rows = [
            f"deny       {self.here} {unit} per refused write, {self.lines} lines — "
            f"no ceiling is declared for it",
            f"  bare     {self.bare:>6}  the same denial where nothing serves the tools",
        ]
        if self.shell:
            rows.insert(
                1,
                f"  shell    {self.shell:>6}  of that re-spells the write vocabulary for a shell",
            )
        if self.notice_limit is not None:
            rows.append(
                f"  notice   {self.notice:>6}  this module's other text, "
                f"{self.notice_limit - self.notice:+} of {self.notice_limit}"
            )
        return chr(10).join(rows)

    def payload(self, unit: str) -> dict[str, object]:
        return {
            "characters": self.here,
            "unit": unit,
            "of": "one write refused, as this project's sessions are told it",
            "lines": self.lines,
            "shell": self.shell,
            "bare": self.bare,
            # No `limit` key, for `Skilled`'s reason: a `null` there reads as a ceiling this
            # build failed to find rather than as one nobody has argued for.
            "notice": self.notice,
            "notice_limit": self.notice_limit,
        }


def deny_cost(config: Config) -> Denied:
    """Price the refusal off the record that composes it, never off a second spelling.

    :func:`notice_budget`'s rule one message over: it is measured from
    :func:`~roadkeep.guarding.announce` so a sentence reworded there moves the figure, and this
    builds a real :class:`~roadkeep.guarding.Refusal` for the same reason. A fixture pasted here
    would be a copy that agrees until somebody edits a door.

    The subject is an `Edit` on this project's roadmap, which is the denial every adopting
    session meets first — and the role is what decides which verbs the table names, so it is
    the one the whole plugin exists for rather than the widest one available.
    """
    from roadkeep.guarding import Refusal  # noqa: PLC0415 - RK260
    from roadkeep.provenance import served_by  # noqa: PLC0415 - RK260

    refused = Refusal(
        tool="Edit",
        path=config.relative(config.path("roadmap")),
        role="roadmap",
        served=served_by(config.root),
    )
    said = str(refused)
    bare = str(replace(refused, served=""))
    # The split exists only where the tools are served: with none, the shell table is not a
    # second spelling of anything — it is the only one, and a figure here would be the whole
    # answer reported as a redundancy.
    at = said.find(_SHELL_TABLE)
    shell = 0 if at < 0 else width(said[at:said.index(_READING)])
    resident, limit = notice_budget(config)
    return Denied(
        here=width(said),
        bare=width(bare),
        shell=shell,
        lines=said.count("\n") + 1,
        notice=resident,
        notice_limit=limit,
    )


#: The two sentences the split above is taken between. Matched rather than counted by line,
#: for `installing._skill`'s reason: a table that grew a row would move every number keyed on
#: a position, and a sentence that moved is a `ValueError` here rather than a wrong figure.
_SHELL_TABLE = "Or the same engine in a shell"
_READING = "Reading is never refused"


def notice_budget(config: Config) -> tuple[int, int | None]:
    """What this project's `SessionStart` line costs, and what it may (RK1243).

    The third thing a session pays for, and the one no command could ask about. `--tools`
    prices the schema and `--file` the resident files; the notice is resident too — one line
    handed to every session in every governed project — and its ceiling was a constant in
    `guarding.py` that a test asserted a fixture against. RK1242 raised that constant by 23%
    to fit a clause, which is a change to what every adopting session pays, made by editing a
    literal. RK30's own argument, one surface over: a limit nobody counts is a limit that
    moves.

    Measured off :func:`~roadkeep.guarding.announce` and never re-composed, which is
    :func:`~roadkeep.serving.surface`'s rule: it is the line *this* project's sessions get,
    with this project's paths in it, so a sentence reworded in `guarding.py` moves the figure.

    **Without the drift sentence** (RK234), which is deliberately over the ceiling and is not
    resident — it appears only while a vendored copy has drifted and goes away with one
    `install`. What is priced here is what every session pays.

    In UTF-16 code units, the unit every other figure in this module is in (RK430) — and the
    unit the ceiling is now held in, so this read and that gate cannot disagree about a line
    carrying a character outside the BMP.

    ``(0, None)`` where there is no notice: a project this cannot announce for pays nothing,
    which is a real answer rather than a missing row.
    """
    from roadkeep.guarding import _NOTICE_BUDGET, announce  # noqa: PLC0415 - RK260

    said = announce({"cwd": str(config.root)}, config.root)
    if said is None:
        return 0, None
    return width(str(replace(said, stale=()))), _NOTICE_BUDGET


@dataclass(frozen=True, slots=True)
class Briefed:
    """What one task's brief costs a tool result, in the unit a model is charged (RK1286)."""

    id: str
    characters: int

    def over(self, limit: int | None) -> bool:
        return limit is not None and self.characters > limit


@dataclass(frozen=True, slots=True)
class Unpriced:
    """One line whose brief would not compose, and what refused it (RK1288)."""

    id: str
    #: The tool's own answer, verbatim: what each unmeasured line was refused for is a
    #: sentence some module already wrote, so naming it costs a row and not a decision.
    because: str


@dataclass(frozen=True, slots=True)
class Reads:
    """Every open line's brief, widest first, against what one may cost (RK1286).

    The one read this project recommends over reading the file, and the one thing here with no
    figure. Every resident file has a budget and the served surface has two, on RK30's
    argument that a limit nobody counts is a limit that moves — and `brief` grew four
    arithmetic rows in one session with nothing counting any of them.

    **Widest first and not the median.** A brief that fits on the average task and not on the
    hardest one is a brief a session replaces by re-reading the file exactly when the file is
    longest, which is the cost RK29 removed. So the bound is the widest, and the listing is
    ordered to put it where a reader looks.
    """

    briefs: tuple[Briefed, ...] = ()
    #: The lines whose briefs would not compose (RK1288). Dropped by a bare `continue`
    #: before, which made the one number this read exists for wrong in the direction that
    #: matters: the widest is the bound, and a line that could not be composed is exactly the
    #: shape most likely to be it — so the ranking named the top of the rest and called it
    #: the answer. No silent caps, and the gate inherits that: `read.over` is derived from
    #: this ranking, so a project could be over its ceiling on a line nothing reported.
    unpriced: tuple[Unpriced, ...] = ()
    #: How many open lines this reading did **not** ask for (RK1287). Above zero only on the
    #: gate's bounded read, and never a silence: a listing that omits without saying so reads
    #: as one that covered everything, which is the law this project holds about every capped
    #: answer it gives.
    elided: int = 0
    #: How many open lines there are (RK1289). **Carried and never reconstructed**: the note
    #: added `elided` to what it priced and called that the backlog, which is the backlog only
    #: while every line it asked for answered — a line that refused leaves the ranking without
    #: ever being elided, so four wanted of ten with one refusing printed "3 of 9". Three
    #: numbers that add up beats two arranged so the sum is wrong, and this reading walked
    #: every open id to compute the bound in the first place.
    open_lines: int = 0
    #: `[reads] brief`, or `None` where the project declared none — opt-in, as every other
    #: table whose absence means *ungoverned* rather than *zero* is.
    limit: int | None = None

    @property
    def widest(self) -> Briefed | None:
        return self.briefs[0] if self.briefs else None

    @property
    def over(self) -> tuple[Briefed, ...]:
        return tuple(one for one in self.briefs if one.over(self.limit))


def brief_budget(
    config: Config, task_id: str | None = None, *, offered: bool = False
) -> Reads:
    """What a brief costs, per open line or for the one named (RK1286).

    Measured off :func:`~roadkeep.briefing.brief`'s own rendering and never re-composed, which
    is :func:`~roadkeep.serving.surface`'s rule one read over: a row added to that answer moves
    this figure, which is the whole reason the number is worth reading.

    In UTF-16 code units, the unit every other figure in this module is in (RK430) and the one
    a model is charged — so the read and the gate that refuses cannot disagree about an answer
    carrying a marker outside the BMP.

    Open lines only. A shipped id has no brief left to start work from, and a paused one is a
    line `pick` can never offer — pricing either would be measuring an answer nobody asks for.

    ``offered`` is the **bounded** reading, and it is the gate's (RK1287). A brief costs tens
    of milliseconds, so pricing every open line put a project that declared a ceiling at O(open)
    of them on every commit — six seconds on a two-hundred-line backlog, and the first thing
    anybody does with a gate that costs six seconds is stop running it. What this prices instead
    is the briefs a session is **about to ask for**: `pick`'s own answer and the alternatives it
    already names, which is a bound this module does not invent and one that moves with that
    verb. What it leaves out is :attr:`Reads.elided` — never dropped in silence.
    """
    from roadkeep.briefing import NothingToBrief, brief  # noqa: PLC0415 - RK260
    from roadkeep.picking import pick  # noqa: PLC0415 - RK260

    roadmap = config.document("roadmap")
    every = list(roadmap.by_id())
    if task_id is not None:
        # The named form keeps the rule the unnamed one states (RK1291): a shipped line has
        # no brief left to start work from and a paused one is a line `pick` can never offer,
        # so an id that is not open answers as the absence it is rather than with a figure
        # comparable to nothing — a shipped brief carries no allowances, no deps and no
        # design, because the ship deleted them. `Whereabouts` is the reader every other
        # refusal about a missing id already asks (RK1213, RK1276).
        if task_id not in roadmap.by_id():
            from roadkeep.backlog import Whereabouts  # noqa: PLC0415 - RK260

            return Reads(
                limit=config.brief_read,
                unpriced=(
                    Unpriced(
                        id=task_id,
                        because=(
                            f"not an open line — {Whereabouts.of(config, task_id).sentence}, "
                            f"and a brief is what starts work on one"
                        ),
                    ),
                ),
                open_lines=len(every),
            )
        wanted, elided = [task_id], 0
    elif offered:
        chosen = pick(config)
        named = [one.task.id for one in (chosen.entry,) if one is not None]
        # And the lines a live claim kept out of that ranking: a held line is one somebody is
        # working on, which is the strongest evidence there is that its brief gets asked for.
        # Without them a session holding the only open line priced nothing and said `0 of 1`,
        # which reads as a check doing nothing rather than as one that had nothing to do.
        held = [one.id for one in chosen.held]
        wanted = list(dict.fromkeys([*named, *chosen.alternatives, *held]))
        elided = max(0, len(every) - len(wanted))
    else:
        wanted, elided = every, 0
    out: list[Briefed] = []
    refused: list[Unpriced] = []
    for one in wanted:
        try:
            out.append(Briefed(id=one, characters=width(brief(config, one).stated(config))))
        except (NothingToBrief, KeyError, OSError) as error:
            # Named and never dropped (RK1288). An id no line carries is still not this
            # read's to *refuse* — it is asked about the backlog, and a caller naming a
            # shipped task is answered by `show` — but a line the ranking could not measure
            # is the one most likely to have been the widest, so its absence is the answer.
            refused.append(Unpriced(id=one, because=str(error) or type(error).__name__))
    return Reads(
        briefs=tuple(sorted(out, key=lambda one: one.characters, reverse=True)),
        limit=config.brief_read,
        elided=elided,
        unpriced=tuple(refused),
        open_lines=len(every),
    )


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
        characters=None if raw is None else _characters(counted),
    )


def _characters(counted: bytes) -> int | None:
    """The normalised bytes as UTF-16 code units, or `None` where they are not UTF-8 (RK1245).

    `None` and never a guess: a file this cannot decode is one where the question *what does
    a reader pay for it* has no answer here, and its bytes alone are then the honest row.
    Nothing is refused either way — the gate reads bytes and is untouched.

    The **normalised** bytes, which is the convention the total is counted on (RK1105): a
    figure counted off the checkout's own terminator would disagree with the number printed
    beside it on exactly the machines a budget is a fact about.
    """
    try:
        return width(counted.decode("utf-8"))
    except UnicodeDecodeError:
        return None


def _parts(raw: bytes) -> tuple[Part, ...]:
    """The file's `##` sections, largest first (RK1092).

    Bytes and never text, for the reason the budget itself is counted that way: an instruction
    file is not a format this tool decodes (L4). Handed the same normalised bytes the total is
    counted from (RK1105) — this sentence said the opposite while that was true of both, and a
    breakdown on the checkout's own terminator would sum past the number printed above it.

    The order here is the *record's* since RK1252: this one produces both figures and
    :attr:`Load.ranked` sorts them by whichever limit is about to refuse. Sorted at all,
    still, because a caller reading `Load.parts` directly gets a stable order rather than
    the accident of the file's own layout.

    Only `##`, because that is the level `agents.md` organises by — a `###` under one belongs
    to it, and splitting there would report a heading's own body as a sibling of its parent.
    """
    # The reading is the file's or nobody's (RK1253): one bad byte makes the whole undecodable
    # while its other sections read fine, and a column present on four rows of seven is a
    # breakdown that does not sum to the total it sits under.
    decodes = _characters(raw) is not None
    sections: list[tuple[str, list[bytes]]] = [("", [])]
    for line in raw.splitlines(keepends=True):
        if line.startswith(b"## "):
            sections.append((line.decode("utf-8", "replace").rstrip(), []))
        sections[-1][1].append(line)
    return tuple(
        sorted(
            (
                Part(
                    heading=name,
                    lines=len(body),
                    bytes=sum(len(one) for one in body),
                    characters=_characters(b"".join(body)) if decodes else None,
                )
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


#: The percentile the conversion follows, which is the sentence above `CHARS_PER_WORD`: an
#: author who lands on the word aim clears the character gate about nineteen times in twenty.
#: Stated here because the reading and the constant have to follow one number, and a second
#: spelling of it is what let the corpus grow past the figure with only a test to say so.
CONVERSION_AT = 95


@dataclass(frozen=True, slots=True)
class Fixed:
    """One number this build fixes from a corpus, with the reading that fixes it (RK1381).

    Here and not in `describing`, which is the module that prints it (RK1382): a record belongs
    with the reading that builds it, and declaring it beside the presenter made the two import
    each other inside functions — so neither import could sit at the top of its file and this
    module's own reading could not name its return type.

    What it holds is the reading and never only the figure, which is the whole of RK1381: every
    other number decided by one has a verb that states it — `govern <key>` with no value,
    `cost`, `budget --file` — and this one had a comment in source and an assertion in a suite,
    so a corpus that grew past it spoke through a red test and the new figure took a throwaway
    script to get.

    How it is *stated* stays the presenter's, which is the line this move does not cross: the
    two methods below are the same pair every record here carries (RK1170), one answer in two
    registers, and a `config` that composed its own row would be the second spelling of it.
    """

    name: str
    at: float
    #: The corpus it was taken over, as a count of the things measured.
    sample: int
    #: The percentile the figure follows, and the figure it follows it at.
    percentile: int
    reading: float
    why: str

    def stated(self) -> str:
        return (
            f"  {self.name:<12} {self.at}  p{self.percentile} {self.reading} over "
            f"{self.sample} — {self.why}"
        )

    def payload(self) -> dict[str, object]:
        return {
            "name": self.name,
            "at": self.at,
            "sample": self.sample,
            "percentile": self.percentile,
            "reading": self.reading,
            "why": self.why,
        }


def conversion(config: Config) -> Fixed:
    """The reading behind `CHARS_PER_WORD`, as a command rather than a script (RK1381).

    Every other number decided by a reading has a verb that states it — `govern <key>` with no
    value, `cost`, `budget --file`, `weight`. This one had a comment in source and an assertion
    in a suite, so a corpus that grew past it spoke through a red test and getting the new
    figure meant writing the same throwaway measurement twice in one session.

    The **same corpus the constant is fixed from**: this project's own written `symptom` and
    `why` fields, across the roadmap and the ledger, which is the prose the format is proven by
    (RK18). A field nobody wrote is left out rather than counted as zero characters per zero
    words, that being a division and not a reading.

    A read and never a write. There is nothing to declare — the conversion is a property of the
    prose those lines are written in and not a project's to configure (L6) — so what comes back
    is the percentile, the sample it was taken over, and the figure this build carries.
    """
    ratios = sorted(
        len(text) / len(text.split())
        for role in ("roadmap", "changelog")
        if config.has(role) and config.path(role).is_file()
        for entry in config.document(role).entries
        for text in (entry.task.symptom or "", entry.task.why or "")
        if text.split()
    )
    if not ratios:
        raise ValueError(
            "this project has written no symptom or why to measure, so the conversion has no "
            "corpus here: the figure this build carries is the one it was fixed from elsewhere"
        )
    at = ratios[min(int(len(ratios) * CONVERSION_AT / 100), len(ratios) - 1)]
    return Fixed(
        name="chars/word",
        at=CHARS_PER_WORD,
        sample=len(ratios),
        percentile=CONVERSION_AT,
        reading=round(at, 2),
        why=(
            "the first round number above this corpus's percentile, so a word aim clears the "
            "character gate about nineteen times in twenty"
        ),
    )
