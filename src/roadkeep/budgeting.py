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

from roadkeep.authoring import compose, prose_role
from roadkeep.config import Config
from roadkeep.ids import next_id
from roadkeep.schema import CHARS_PER_WORD, Task, body_aim, words
from roadkeep.scoping import NoSuchNonGoal, NotGoverned, address, leads, read
from roadkeep.sections import declaring, find

#: Re-exported, not re-declared (RK201). The conversion moved down to `schema`, where the
#: refusal that states a surplus can reach it: the aim and the surplus are the same
#: arithmetic in opposite directions, and two constants would be two answers.
__all__ = [
    "CHARS_PER_WORD",
    "AmbiguousAnchor",
    "Body",
    "Budget",
    "Share",
    "body_budget",
    "budget",
    "budget_of",
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
    section, absence = _section_of(config, task.ref or task.id)
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


def _section_of(config: Config, anchor: str) -> tuple[Body | None, str]:
    """This anchor's body budget, or None and why there is none.

    Swallowing the refusal :func:`body_budget` raises rather than propagating it, because
    the caller asked about a *line*: a project that declares no rationale file has a legal
    `add` with no `--section` in it, and turning that into an error would refuse the read
    every other project uses. The same holds for an anchor two files declare (RK303) — the
    line's own two fields are unaffected by it — but that one is a defect and the other is
    not, so the reason rides back with the absence rather than the two reading identically.
    """
    try:
        return body_budget(config, anchor), ""
    except AmbiguousAnchor as error:
        return None, str(error)
    except KeyError:
        return None, ""


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

    @property
    def left(self) -> int:
        return max(0, self.limit - self.taken)

    @property
    def aim(self) -> int:
        """What the body may be composed to, which is under what refuses (RK301)."""
        return body_aim(self.limit)

    @property
    def room(self) -> int:
        """The same headroom applied to what is *left*, which is an amend's figure (RK245)."""
        return body_aim(self.left)

    @property
    def nests(self) -> bool:
        """Whether the section carries subsections, so the two counts are two numbers."""
        return self.subtree != self.taken


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
        taken = {"lead": len(found.lead.strip()), "why": len(" ".join(found.why.split()))}
    return tuple(
        Share(field, limit, limit, taken[field])
        for field, limit in (("lead", scope.lead), ("why", scope.why))
    )


def body_budget(config: Config, anchor: str, role: str | None = None) -> Body:
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
    return Body(
        anchor=anchor,
        role=role,
        limit=config.schema_for(role).section_max,
        taken=0 if section is None else section.own_words,
        subtree=0 if section is None else section.words,
        written=section is not None,
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
