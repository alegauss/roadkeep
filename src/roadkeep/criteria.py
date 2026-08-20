"""What must be **true** for a block to be finished — the non-goal's positive twin (RK1265).

`scoping` governs the one durable statement this tool had, and it is negative: a non-goal says
what will not be built. Nothing said what would make a block done, so the only test for
doneness left was a line count reaching zero.

**Measured, and the measurement is why this is a store rather than a paragraph.** A block in a
repository using this tool carried 131 recorded entries and was declared closed and reopened
six times, every close a count reaching zero. Its definition of done *was* written — as a
rationale section on the task that introduced it — and `ship` deleted it, correctly, because
`IMPROVEMENTS` holds rationale for **unshipped** work. Zero occurrences survive; the criterion
moved to a file this tool does not govern.

So the shape is `scoping`'s, mirrored, and the three decisions that module lists hold here for
the same reasons — no ids, opt-in under `[criteria]`, and a wrap that is written and not
judged. Two things are its own:

* **One list per block**, so the address is the pair `(block, lead)`. A criterion is about a
  body of work, and a flat list would make "finished" a property of the backlog rather than of
  the thing being finished.
* **Its own heading, which is not a block declaration.** A heading reading `Block A` declares
  that label wherever it sits and at whatever level (`document._block_label` anchors at the
  start and never asks the level), so a second one under another section is `block.repeated` to
  the gate and refused by every write. The heading is therefore `## Done when — Block A`: the
  region is found by the same prefix match `scoping.HEADING` uses, and the label is read out of
  the tail, where nothing else looks for one.

The scope caution the design names is held by the two limits and by nothing else: this is a
list of leads, and a criterion needing a page belongs in the project's own documents. What
belongs here is the line a reader can check off.

**And the other unit is the task** (RK1268). The pair above is right and this does not
overturn it — it adds the address an agent actually executes against. What a task wants before
the first edit is the spec: the problem, what is out of scope, what must be true when it is
done, and how that is checked. Three of the four were already addressable per task — the
`symptom`, `non-goal list` and the design section — and the fourth was per block, so the
checkable sentence was the one written at the wrong altitude. Half of it was per task already,
and it is the half nobody can read: `evidence <id>` runs a fenced query the design declares and
counts the sites, so the *executable* claim was per task while the *readable* one was per
block, which is the wrong way round.

So a region is addressed by a block label **or** by an id, and nothing else changes: the same
heading prefix, the same bullet, the same two limits, and the same rule that a lead is unique
inside its own list. It binds nothing — presence, not enforcement — because whether the work
satisfies a sentence is a judgement this tool has no model for (L4). What it does own is the
departure: a line that ships takes its own list with it, in the transaction that removes the
line, for the reason the queue entry does (RK327) — there is no state where the line has left
and a heading still asks what would finish it.
"""

from __future__ import annotations

import re
import textwrap
from collections.abc import Sequence
from dataclasses import dataclass, replace
from pathlib import Path

from roadkeep.config import Config, Scope
from roadkeep.kernel.document import Document, blank
from roadkeep.kernel.schema import Schema, SchemaError, Violation, over_by, width

__all__ = [
    "HEADING",
    "LEAD",
    "SHAPE",
    "WHY",
    "Amended",
    "Criterion",
    "DuplicateLead",
    "Dropped",
    "NoSuchCriterion",
    "NotGoverned",
    "Written",
    "AmbiguousLead",
    "add",
    "address",
    "addresses_task",
    "blocks",
    "check",
    "drop",
    "heading_for",
    "leads",
    "named",
    "read",
    "render",
    "validate",
    "without",
]

#: Any heading whose text starts like this holds a block's criteria. A prefix match for
#: `scoping.HEADING`'s reason — an adopting project writes `## Done when (Block A)` as readily
#: as the spelling this writes — and the **block is the tail**, read with the project's own
#: heading pattern so `Fase 2` answers wherever `Block A` does.
HEADING = re.compile(r"^done when\b(?P<tail>.*)$", re.IGNORECASE)
#: What this writes when a block has no heading yet. The separator is the em dash the rest of
#: the format uses, and the label comes through `Schema.block_named` so the project's own word
#: and spelling are what land.
_HEADING_FORM = "## Done when — {named}"

#: `- **<lead>** <why>`, at column zero — `scoping._BULLET` exactly, because the two lists are
#: one grammar and a second spelling of it is the drift both modules exist to prevent.
_BULLET = re.compile(r"^- \*\*(?P<lead>[^*]+)\*\*(?P<why> .*)?$")
_ANY_BULLET = re.compile(r"^[-*+] (?P<rest>.*)$")
_CONTINUATION = "  "
_SENTENCE = ". "

#: The three codes this format can be violated by. Named here because `lint` reports them and
#: a code spelled twice is a code that drifts once.
LEAD = "criterion.lead"
WHY = "criterion.why"
SHAPE = "criterion.shape"


class NotGoverned(KeyError):
    """A write to a list this project has not declared governed (RK1265).

    `scoping.NotGoverned`'s reason, and one more: a project that has never written a criterion
    has an empty list rather than a governed one, so a default would report a finding per block
    on the first run — the adoption gate that gets bypassed instead of adopted.
    """

    def __init__(self, where: str) -> None:
        super().__init__(
            f"{where} declares no [criteria]: add the table to roadkeep.toml to govern what "
            f"finishes a block, since a schema applied to prose nobody wrote to it reports "
            f"on adoption"
        )


class DuplicateLead(ValueError):
    """The lead is the address **within its own list**, so a second one is two answers.

    ``about`` arrives already spelled — `Block A` or an id (RK1268) — because the two
    addresses read differently and a message that prefixed both with the block word would
    name a block that does not exist.
    """

    def __init__(self, lead: str, about: str, where: str, lineno: int) -> None:
        self.lead = lead
        self.about = about
        self.lineno = lineno
        super().__init__(
            f"{where}:{lineno} already leads with {lead!r} under {about}: the lead is "
            f"how a criterion is addressed, so a second one carrying it is two answers about "
            f"the same claim"
        )


class NoSuchCriterion(KeyError):
    """A lead that addresses nothing in this block.

    The leads that exist are named, for `scoping.NoSuchNonGoal`'s reason: a criterion is looked
    up by the words a reader remembers, and the stop inside the bold is invisible.
    """

    def __init__(self, lead: str, about: str, where: str, leads: tuple[str, ...]) -> None:
        self.lead = lead
        self.about = about
        known = ", ".join(repr(one) for one in leads) or "none"
        super().__init__(
            f"no criterion under {about} in {where} leads with {lead!r}: the list "
            f"carries {known}"
        )


class Unshaped(ValueError):
    """A correction to a bullet this module could not have written (`scoping.Unshaped`).

    :func:`read` accepts a bullet with no bold head so that every criterion has an address, and
    that is safe precisely because nothing renders one back. An `amend` is the first verb that
    would render over lines it did not write, and there the render imposes the shape — which
    moves the lead, and the lead is the address.
    """

    def __init__(self, lead: str, where: str, lineno: int) -> None:
        self.lead = lead
        self.lineno = lineno
        super().__init__(
            f"the bullet at {where}:{lineno} carries no bold lead, so {lead!r} is its first "
            f"sentence rather than an address this verb can write around — `criterion drop` "
            f"then `criterion add` is the repair, and it is honest about the lead changing"
        )


@dataclass(frozen=True, slots=True)
class Criterion:
    """One bullet under a `Done when` heading, as data and as the file spells it."""

    #: What the list is addressed to: a block label, or a task id (RK1268). One field and not
    #: two, because every reader here asks *which list is this in* and a pair of nullable
    #: fields would make that question a branch at every call site.
    about: str
    lead: str
    why: str
    #: 1-based, and a span because a filled bullet wraps: `first` is the line the `- ` is on.
    first: int
    last: int
    #: The source lines, verbatim and without their endings — the round-trip's evidence.
    lines: tuple[str, ...] = ()
    #: Did the bold shape hold? False where the lead is the bullet's first sentence instead,
    #: which is `scoping.NonGoal.shaped` and carries its whole argument.
    shaped: bool = True

    def __str__(self) -> str:
        return f"**{self.lead}** {self.why}" if self.shaped else " ".join(self.lines).strip()


@dataclass(frozen=True, slots=True)
class Written:
    """A criterion inserted, and the document it went into. Save writes one file."""

    document: Document
    criterion: Criterion
    #: Whether this write **opened the block's list**, which the answer says out loud: a
    #: heading appearing in a governed file is the one edit a reader should never discover
    #: (`priority add`'s rule, RK427).
    opened: bool = False

    @property
    def lineno(self) -> int:
        return self.criterion.first

    @property
    def rendered(self) -> tuple[str, ...]:
        return self.criterion.lines

    def save(self) -> tuple[Path, ...]:
        return self.document.save()

    def stated(self, config: Config, wrote: Sequence[Path]) -> str:
        """The bullet, as many lines as it took, and the heading where one was opened.

        **No event line**, for `scoping.Written.stated`'s reason (RK38): the payload a hook
        reads is an id and its block's open state, and a criterion has no id — it is what
        would finish the block, not a member of it.
        """
        from roadkeep.rendering import _staging_rows  # noqa: PLC0415 - RK260

        where = config.relative(config.path("roadmap"))
        rows = []
        if self.opened:
            rows.append(
                f"opened   {heading_for(config.schema, self.criterion.about)} — this had "
                f"no list, and writing the first criterion is what opens one"
            )
        rows.append(f"{where}:{self.lineno}  {len(self.rendered)} line(s)")
        rows += [f"  {line}" for line in self.rendered]
        rows += _staging_rows(config.relative(one) for one in wrote)
        return "\n".join(rows)

    def payload(self, config: Config, wrote: Sequence[Path]) -> dict[str, object]:
        from roadkeep.rendering import _wrote_json  # noqa: PLC0415 - RK260

        return {
            # The address as one field, which is what it is (RK1268): a caller branching on
            # a block key that is sometimes an id would be reading the shape out of the value.
            "about": self.criterion.about,
            "lead": self.criterion.lead,
            "why": self.criterion.why,
            "opened": self.opened,
            "file": config.relative(config.path("roadmap")),
            "line": self.lineno,
            "rendered": list(self.rendered),
            **_wrote_json(config, wrote),
        }


@dataclass(frozen=True, slots=True)
class Amended:
    """A criterion's reason rewritten where it already sat."""

    document: Document
    criterion: Criterion
    #: The reason as the file read it. Both readings, because what makes a correction
    #: reviewable is that a word changed and the bullet did not move.
    before: str = ""

    @property
    def changed(self) -> bool:
        return self.before != self.criterion.why

    @property
    def lineno(self) -> int:
        return self.criterion.first

    @property
    def rendered(self) -> tuple[str, ...]:
        return self.criterion.lines

    def save(self) -> tuple[Path, ...]:
        return self.document.save()

    def stated(self, config: Config, wrote: Sequence[Path]) -> str:
        from roadkeep.rendering import _staging_rows  # noqa: PLC0415 - RK260

        if not self.changed:
            return f"{self.criterion.lead} unchanged: the bullet already reads that way"
        where = config.relative(config.path("roadmap"))
        rows = [
            f"{where}:{self.lineno}  amended  {len(self.rendered)} line(s)",
            *(f"  {line}" for line in self.rendered),
        ]
        rows += _staging_rows(config.relative(one) for one in wrote)
        return "\n".join(rows)

    def payload(self, config: Config, wrote: Sequence[Path]) -> dict[str, object]:
        from roadkeep.rendering import _wrote_json  # noqa: PLC0415 - RK260

        return {
            "about": self.criterion.about,
            "lead": self.criterion.lead,
            "was": self.before,
            "now": self.criterion.why,
            "changed": self.changed,
            "file": config.relative(config.path("roadmap")),
            "line": self.lineno,
            "rendered": list(self.rendered),
            **_wrote_json(config, wrote),
        }


@dataclass(frozen=True, slots=True)
class Dropped:
    """A criterion removed, whole, wrapped lines included."""

    document: Document
    criterion: Criterion
    #: How many bullets carried the address. Above one, the later copy went and the first
    #: stayed — `scoping.drop`'s rule, so a duplicate takes a second call.
    carried: int = 1

    @property
    def lines(self) -> tuple[str, ...]:
        return self.criterion.lines

    def save(self) -> tuple[Path, ...]:
        return self.document.save()

    def stated(self, config: Config, wrote: Sequence[Path]) -> str:
        from roadkeep.rendering import _staging_rows  # noqa: PLC0415 - RK260

        where = config.relative(config.path("roadmap"))
        span = self.criterion
        rows = [f"{where}:{span.first}-{span.last}  dropped  **{span.lead}**"]
        if self.carried > 1:
            rows.append(
                f"  duplicate {self.carried} bullets carried this lead: the later one went, "
                f"the first is where the reader already found it"
            )
        # The heading stays, and it says so: an emptied list is a question somebody answered
        # and a missing one is a question nobody asked.
        if not read(self.document, span.about):
            rows.append(
                f"  {heading_for(config.schema, span.about)} kept and now empty: a list "
                f"whose criteria all went is not one nobody wrote for"
            )
        rows += _staging_rows(config.relative(one) for one in wrote)
        return "\n".join(rows)

    def payload(self, config: Config, wrote: Sequence[Path]) -> dict[str, object]:
        from roadkeep.rendering import _wrote_json  # noqa: PLC0415 - RK260

        span = self.criterion
        return {
            "about": span.about,
            "lead": span.lead,
            "why": span.why,
            "file": config.relative(config.path("roadmap")),
            "removed": [span.first, span.last],
            "carried": self.carried,
            "rendered": list(self.lines),
            **_wrote_json(config, wrote),
        }


def read(document: Document, about: str = "") -> tuple[Criterion, ...]:
    """Every criterion, in file order — the whole roadmap, or one address's list.

    Every bullet, including the ones the shape does not hold, for `scoping.read`'s reason: a
    criterion the gate reports and no verb can address is a finding whose remedy the tool
    refuses (RK16).
    """
    out = tuple(one for span in _regions(document) for one in _bullets(document, *span))
    return out if not about else tuple(one for one in out if one.about == about)


def rejects(document: Document) -> tuple[tuple[int, str], ...]:
    """The bullets whose shape the format does not hold, with their line — the gate's own."""
    return tuple((one.first, one.lines[0]) for one in read(document) if not one.shaped)


def blocks(document: Document) -> tuple[str, ...]:
    """Every address whose list this file declares, in file order — a label or an id (RK1268).

    A heading with no bullet is **still** a declared list, which is the state `criterion drop`
    leaves and the one a reader has to be able to tell from work nobody has written a criterion
    for: the first says the question was asked, the second that it was not.
    """
    return tuple(label for _, label in _regions(document))


def leads(document: Document, about: str) -> tuple[str, ...]:
    """The lead of every criterion under one address, in file order — what `brief` prints."""
    return tuple(one.lead for one in read(document, about))


def addresses_task(schema: Schema, about: str) -> bool:
    """Whether an address is a task id rather than a block label (RK1268).

    Asked of the schema and never by looking for a digit: the two shapes are the project's own
    — `[ids]` may declare padding and a suffix, and a label may be `D.1` — so a reader deciding
    it here would be a second spelling of both, which is the drift `address` exists to prevent.
    """
    return schema.id_pattern().match(about) is not None


def named(schema: Schema, about: str) -> str:
    """How a report spells one of the two addresses: `Block A`, or the id as it is written."""
    return about if addresses_task(schema, about) else schema.block_named(about)


def address(lead: str) -> str:
    """The lead as an address: case-folded, and without the stop the bold may carry.

    One function for `scoping.address`' reason — two spellings of "the same lead" would mean a
    bullet the write path accepted and the gate then failed on.
    """
    return lead.strip().rstrip(".").casefold()


def heading_for(schema: Schema, about: str) -> str:
    """The heading line this writes for a list, spelled with the project's own word or an id."""
    return _HEADING_FORM.format(named=named(schema, about))


def render(config: Config, lead: str, why: str) -> tuple[str, ...]:
    """The bullet as the schema writes it: one line, filled to `prose`, continuations by two."""
    return tuple(
        textwrap.fill(
            f"- **{lead.strip()}** {' '.join(why.split())}",
            width=config.schema.prose_width,
            subsequent_indent=_CONTINUATION,
            break_long_words=False,
            break_on_hyphens=False,
        ).split("\n")
    )


def validate(config: Config, lead: str, why: str) -> tuple[Violation, ...]:
    """Every rule a schema can check about a criterion, and no rule it cannot.

    Length and shape only. That the lead states something *checkable* rather than an aspiration
    is the author's claim, exactly as a symptom's falsifiability is (L4).
    """
    scope = config.criteria or Scope()
    out: list[Violation] = []
    head, reason = lead.strip(), " ".join(why.split())
    if not head:
        out.append(Violation(LEAD, "lead", "a criterion is addressed by its lead"))
    if "*" in head:
        out.append(
            Violation(
                LEAD,
                "lead",
                "the lead is bolded by the renderer, so it may not carry '*' itself",
            )
        )
    if width(head) > scope.lead:
        out.append(Violation(LEAD, "lead", over_by(width(head), scope.lead, measured=head)))
    if not reason:
        out.append(
            Violation(WHY, "why", "a criterion nobody argued is a wish with a checkbox")
        )
    if width(reason) > scope.why:
        out.append(Violation(WHY, "why", over_by(width(reason), scope.why, measured=reason)))
    return tuple(out)


def check(config: Config, lead: str, why: str) -> None:
    """Validate or raise, so a refusal reports every problem at once (as `Schema.check`)."""
    violations = validate(config, lead, why)
    if violations:
        raise SchemaError(violations)


def add(config: Config, about: str, lead: str, why: str) -> Written:
    """Insert one criterion under its heading, after the last one there.

    **It writes the heading where the block has none**, which is `priority add`'s rule (RK427)
    and not `add`'s: a task line goes under a heading no write invents, because a block is a
    decision about the plan — and a block's *criteria list* is opened by the act of writing the
    first one, there being nothing else the heading could mean. Said out loud in the answer, a
    heading appearing in a governed file being the edit a reader should never discover.

    The address is never invented either way: a block has to be one the roadmap already
    declares, and a task has to be a line it still carries (RK1268), so a typo in either opens
    no list.
    """
    if config.criteria is None:
        raise NotGoverned(config.relative(config.source or config.root))
    document = config.document("roadmap")
    where = config.relative(config.path("roadmap"))
    label = _addressed(config, document, about, where)
    check(config, lead, why)

    head = lead.strip()
    existing = read(document, label)
    twin = next((one for one in existing if address(one.lead) == address(head)), None)
    if twin is not None:
        raise DuplicateLead(head, named(config.schema, label), where, twin.first)

    opened = _heading_index(document, label) is None
    updated = document
    if opened:
        updated = _open(updated, config.schema, label)
    lines = render(config, head, why)
    at, separate = _placement(updated, label, read(updated, label))
    if separate:
        updated = updated.insert_line(at, "")
        at += 1
    for offset, line in enumerate(lines):
        updated = updated.insert_line(at + offset, line)
    return Written(
        document=updated,
        criterion=Criterion(
            about=label,
            lead=head,
            why=" ".join(why.split()),
            first=at + 1,
            last=at + len(lines),
            lines=lines,
        ),
        opened=opened,
    )


def amend(config: Config, about: str, lead: str, why: str) -> Amended:
    """Rewrite one criterion's reason where it already sits, keeping its place.

    `scoping.amend`'s door and its whole argument: `add` appends, so drop-and-re-add moves a
    line in a list a reader takes for the shape of what finishing means. The **lead is not a
    field** — it is the address, so a criterion whose lead changes is one dropped and one
    written.
    """
    if config.criteria is None:
        raise NotGoverned(config.relative(config.source or config.root))
    document = config.document("roadmap")
    where = config.relative(config.path("roadmap"))
    label = _resolved(config, document, about, lead, where)

    existing = read(document, label)
    matches = tuple(one for one in existing if address(one.lead) == address(lead))
    if not matches:
        raise NoSuchCriterion(
            lead.strip(),
            named(config.schema, label),
            where,
            tuple(one.lead for one in existing),
        )
    standing = matches[0]
    if not standing.shaped:
        raise Unshaped(standing.lead, where, standing.first)

    # Its own lead and not the address the caller typed, for `scoping.amend`'s reason:
    # `address` folds case and drops the stop, so composing from the argument would rewrite
    # the head this verb promises not to.
    check(config, standing.lead, why)
    reason = " ".join(why.split())
    if reason == standing.why:
        return Amended(document=document, criterion=standing, before=standing.why)

    lines = render(config, standing.lead, reason)
    start = standing.first - 1
    updated = document.remove_lines(start, standing.last)
    for offset, line in enumerate(lines):
        updated = updated.insert_line(start + offset, line)
    return Amended(
        document=updated,
        criterion=replace(standing, why=reason, last=start + len(lines), lines=lines),
        before=standing.why,
    )


def drop(config: Config, about: str, lead: str) -> Dropped:
    """Remove the criterion a lead addresses in this list, whole, wrapped lines included.

    The heading stays. A list whose criteria have all been dropped is one somebody asked the
    question about and answered "none of these any more", which is not the same as one nobody
    asked — and a verb that took the heading with the last bullet would erase that difference
    as a side effect of a correction.
    """
    if config.criteria is None:
        raise NotGoverned(config.relative(config.source or config.root))
    document = config.document("roadmap")
    where = config.relative(config.path("roadmap"))
    label = _resolved(config, document, about, lead, where)

    existing = read(document, label)
    matches = tuple(one for one in existing if address(one.lead) == address(lead))
    if not matches:
        raise NoSuchCriterion(
            lead.strip(),
            named(config.schema, label),
            where,
            tuple(one.lead for one in existing),
        )
    going = matches[-1]
    return Dropped(
        document=_remove_span(document, going), criterion=going, carried=len(matches)
    )


class AmbiguousLead(ValueError):
    """One lead, two lists, and neither `--block` nor `--task` to say which (RK1265, RK1268).

    The address is the pair, so a lead alone answers only where one list carries it. Refused
    rather than resolved to the first: a criterion is what finishes a body of work, and closing
    the wrong one's is the quiet corruption the whole grammar exists to prevent.
    """

    def __init__(self, lead: str, holders: tuple[str, ...]) -> None:
        self.lead = lead
        self.blocks = holders
        spelled = ", ".join(holders)
        super().__init__(
            f"{lead!r} leads a criterion under {spelled}: the address is the list and "
            f"the lead together, so pass --block or --task to say which of them this is about"
        )


def _holding(document: Document, lead: str) -> tuple[str, ...]:
    """Every address whose list carries this lead, in file order and each named once."""
    wanted = address(lead)
    out: list[str] = []
    for one in read(document):
        if address(one.lead) == wanted and one.about not in out:
            out.append(one.about)
    return tuple(out)


def _resolved(config: Config, document: Document, about: str, lead: str, where: str) -> str:
    """Which list this lead is in: the one named, or the one list that carries it.

    The address is optional on the two verbs that reach an existing bullet, and required on the
    one that creates it — there is nothing to look up before a criterion exists. What it buys
    is a **complete door**: the gate's `criterion.duplicate` names the drop that closes it, and
    a remedy that could not spell the address would be the guess RK420 exists to remove.
    """
    if about:
        return _addressed(config, document, about, where)
    holding = _holding(document, lead)
    if len(holding) > 1:
        raise AmbiguousLead(
            lead.strip(), tuple(named(document.schema, one) for one in holding)
        )
    if not holding:
        raise NoSuchCriterion(lead.strip(), "?", where, leads_everywhere(document))
    return holding[0]


def leads_everywhere(document: Document) -> tuple[str, ...]:
    """Every lead this file carries, in file order — what a refusal names when no list is."""
    return tuple(one.lead for one in read(document))


def _addressed(config: Config, document: Document, about: str, where: str) -> str:
    """The address, if the roadmap declares it. A criteria list is never its own door.

    A heading nobody planned under is a list about work that does not exist, and the typo that
    produces one is invisible afterwards: the bullets read exactly like a block's. Which is why
    a **task** address is held to the same rule and to the stricter half of it (RK1268): a block
    is declared by a heading and outlives its lines, while a task is a line — so the id has to
    be one this file still carries, a list about work the ledger already holds being a question
    somebody answered by shipping.

    **Which of the three absences it is, is said** (RK1276). An id can be missing from the
    roadmap because it shipped, because it was retired, or because it is **paused** — and a
    pause is not a departure: the line keeps its id, its deps, its symptom and its section
    (RK96), so its criteria are still the right question and the answer is `resume`. A message
    that named shipping for all three sent an author who paused the line yesterday to spend a
    second id. `Whereabouts` is the reader every other write reaching a line by id already
    asks, so this asks it rather than composing a fourth reading of the same three files.
    """
    from roadkeep.backlog import Whereabouts  # noqa: PLC0415 - RK260

    label = about.strip().lstrip("#").strip()
    if addresses_task(document.schema, label):
        if label not in document.by_id():
            carried = ", ".join(sorted(document.by_id())) or "none"
            raise KeyError(
                f"no open line {label} in {where}: a criterion addressed to a task says what "
                f"would finish that line, and the ids this file carries are {carried} — "
                f"{Whereabouts.of(config, label).sentence}"
            )
        return label
    declared = {one.label for one in document.headings if one.label}
    if label not in declared:
        known = ", ".join(sorted(declared)) or "none"
        raise KeyError(
            f"no block {label!r} in {where}: a criteria list says what finishes a block this "
            f"file plans, and the labels declared here are {known} — `block add` opens one"
        )
    return label


def _open(document: Document, schema: Schema, about: str) -> Document:
    """Write a `Done when` heading, after the last one there is or after the blocks.

    Kept together and after every block, never beside the block it is about: any heading ends
    the region above it, so one placed under a block's tasks would cut that block's subtree in
    two — which `block drop`, `block merge` and the gate all read as the block ending there.
    A task's list is placed by the same rule and for the same reason (RK1268): it is addressed
    by an id, so nothing about it wants to sit next to the line.
    """
    at = _regions_end(document)
    updated = document
    if at > 0 and not blank(document.lines[at - 1]):
        updated = updated.insert_line(at, "")
        at += 1
    updated = updated.insert_line(at, heading_for(schema, about))
    return updated.insert_line(at + 1, "")


def _regions_end(document: Document) -> int:
    """Where a new `Done when` heading goes: after the last one, else before the non-goals.

    The non-goals close the roadmap in both live corpora and this repository, so a list opened
    after them would read as a footnote to the constraints rather than as part of the plan.
    """
    from roadkeep.scoping import HEADING as NON_GOALS  # noqa: PLC0415 - RK260

    regions = _regions(document)
    if regions:
        # The next heading's own line, blanks left where they are: that run already separates
        # two sections, and a heading placed above it borrows the separator instead of adding
        # a second one — the doubled blank both spellings round-trip through, which is exactly
        # why nothing downstream would catch it (`scoping._remove_span`'s care, inverted).
        end = _region_end(document, regions[-1][0])
        return end if end < len(document.lines) else _trimmed(document)
    for heading in document.headings:
        if NON_GOALS.match(heading.text):
            return heading.lineno - 1
    return _trimmed(document)


def _trimmed(document: Document) -> int:
    """The index one past the file's last non-blank line — where a section appended goes."""
    end = len(document.lines)
    while end > 0 and blank(document.lines[end - 1]):
        end -= 1
    return end


def _regions(document: Document) -> tuple[tuple[int, str], ...]:
    """Every `Done when` heading, as `(0-based index, address)`, in file order.

    A heading whose tail names neither a block this project could spell nor an id it could
    number is skipped rather than guessed at: both shapes are read off the schema, so `Fase 2`
    answers wherever `Block A` does and a `## Done when` with nothing after it addresses
    nothing. The block is tried first — the two shapes cannot collide, an id carrying a prefix
    the label grammar has no room for, and the order is what makes that a fact rather than a
    coincidence nobody would notice changing.
    """
    out: list[tuple[int, str]] = []
    for heading in document.headings:
        match = HEADING.match(heading.text)
        if match is None:
            continue
        tail = match.group("tail").strip().lstrip("—-–").strip()
        block = document.schema.heading_pattern().match(tail)
        if block is not None:
            out.append((heading.lineno - 1, block.group("label")))
        elif document.schema.id_pattern().match(tail):
            out.append((heading.lineno - 1, tail))
    return tuple(out)


def _heading_index(document: Document, about: str) -> int | None:
    """The 0-based index of this address's `Done when` heading, or None where it has none."""
    return next((at for at, label in _regions(document) if label == about), None)


def _region_end(document: Document, start: int) -> int:
    """The 0-based index one past the last line the region at ``start`` owns."""
    for offset, raw in enumerate(document.lines[start + 1 :], start=start + 1):
        if raw.lstrip().startswith("#"):
            return offset
    return len(document.lines)


def _bullets(document: Document, start: int, about: str) -> tuple[Criterion, ...]:
    """Every bullet under one heading, spans joined, each one addressable.

    `scoping._bullets` with the address carried through: the continuations are folded in before
    a lead is taken, which is what lets it come from the whole bullet instead of from its first
    physical line.
    """
    spans: list[tuple[int, list[str]]] = []
    for offset, raw in enumerate(document.lines[start + 1 :], start=start + 2):
        body = raw.rstrip("\r\n")
        if body.startswith("#"):
            break
        if _ANY_BULLET.match(body):
            spans.append((offset, [body]))
        elif spans and body.startswith(_CONTINUATION) and not blank(body):
            spans[-1][1].append(body)
    out: list[Criterion] = []
    for first, span in spans:
        joined = " ".join(line.strip() for line in span)
        where = {
            "about": about,
            "first": first,
            "last": first + len(span) - 1,
            "lines": tuple(span),
        }
        match = _BULLET.match(joined)
        if match is not None:
            out.append(
                Criterion(
                    lead=match.group("lead").strip(),
                    why=(match.group("why") or "").strip(),
                    **where,
                )
            )
            continue
        marker = _ANY_BULLET.match(joined)
        rest = marker.group("rest") if marker is not None else joined
        head, _, tail = rest.partition(_SENTENCE)
        out.append(Criterion(lead=head.strip(), why=tail.strip(), shaped=False, **where))
    return tuple(out)


def _placement(
    document: Document, about: str, existing: tuple[Criterion, ...]
) -> tuple[int, bool]:
    """Where the bullet goes, and whether a blank line has to go in front of it.

    After the last criterion, so the list stays in the order it was written — and after the
    section's prose where there is no bullet yet, `scoping._placement`'s rule exactly.
    """
    if existing:
        return existing[-1].last, False
    start = _heading_index(document, about)
    assert start is not None  # the heading this call just wrote, or the one that was there
    end = _region_end(document, start)
    while end > start + 1 and blank(document.lines[end - 1]):
        end -= 1
    return end, True


def without(document: Document, task_id: str) -> tuple[Document, tuple[str, ...]]:
    """The same roadmap with one task's whole list gone, and the leads it held (RK1268).

    `queueing.without`'s shape and its whole argument: every caller is a **departure**, so the
    heading and its bullets go inside the transaction that removes the line rather than through
    a second read and a second write — and there is no state where the line has left and a
    heading still asks what would finish it.

    A block's list is untouched here, and that difference is the point: a block outlives the
    lines filed under it, so an emptied one is a question somebody answered, while a task's list
    is addressed by an id that this write is spending.

    Silent where the task declared none, which is the ordinary departure — a refusal there would
    make the list an obstacle at the one moment the author is finishing.
    """
    at = _heading_index(document, task_id)
    if at is None:
        return document, ()
    held = tuple(one.lead for one in read(document, task_id))
    end = _region_end(document, at)
    # The blank the heading was separated by goes with it, for `_remove_span`'s reason: both
    # spellings round-trip, so a doubled blank is the one drift nothing downstream would catch.
    while end > at + 1 and blank(document.lines[end - 1]):
        end -= 1
    updated = document.remove_lines(at, end)
    lines = updated.lines
    if at > 0 and at < len(lines) and blank(lines[at - 1]) and blank(lines[at]):
        updated = updated.remove_line(at)
    return updated, held


def _remove_span(document: Document, going: Criterion) -> Document:
    """Take the bullet out, and the blank line the removal doubled (`scoping._remove_span`)."""
    start = going.first - 1
    updated = document.remove_lines(start, going.last)
    lines = updated.lines
    if start > 0 and start < len(lines) and blank(lines[start - 1]) and blank(lines[start]):
        return updated.remove_line(start)
    if start >= len(lines) and start > 0 and blank(lines[start - 1]):
        return updated.remove_line(start - 1)
    return updated
