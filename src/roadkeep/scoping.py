"""The one bullet in the roadmap that is not a task line (RK70).

RK22's value is that a denied edit *names the command to call instead*. For the non-goals it
named five commands that all write task lines, so the only content of the roadmap that is not
a task line was also the only content nothing governed: `Edit` denied, `lint` silent — a
bullet carrying no marker is prose — and `sed` through `Bash` the route left, which the
barrier deliberately does not match. L1 held everywhere except on the list that binds what
`add` may be called for at all.

A non-goal is structurally what `add` already governs, a lead and a reason, so this needs no
new law: one renderer, and the fields refused at input. Three decisions are narrower than
they could be, and each is the reason this module is small:

* **No ids.** An id buys a lifecycle — retire, rename, a second file to disagree with — for a
  list of eight lines that changes once a year. The **lead is the address**, so it is unique
  and checked. The trigger that would change that answer is already visible: Turing's backlog
  says "which the Non-goals say is not the path", a reference resolving to nothing, which is
  the defect RK15 catches for `→ §`.
* **Opt-in under `[non_goals]`** (L6), for RK66's reason: Shio and Turing wrote theirs before
  the schema existed, and a default that reports fifteen findings on adoption is a gate that
  gets bypassed rather than adopted. This repository opts in and is the fixture.
* **The wrap is not judged, only written.** A bullet is filled to `prose` at insertion (L1),
  and a hand-wrapped one already in the file is whitespace inside prose — mechanical, so
  reporting it where `--fix` cannot repair it would be a finding with no door (RK16).

The lead is kept **verbatim**, including a trailing stop when the author wrote one inside the
bold: the corpus writes both `**No web UI and no server.** Files and a CLI.` and `**No
issue-tracker sync** (Jira, …).`, and a renderer that normalized either would be rewriting
the author's punctuation to satisfy a rule nobody stated (L4).
"""

from __future__ import annotations

import re
import textwrap
from dataclasses import dataclass

from roadkeep.config import Config, Scope
from roadkeep.document import Document, blank
from roadkeep.schema import SchemaError, Violation

__all__ = [
    "HEADING",
    "LEAD",
    "SHAPE",
    "WHY",
    "DuplicateLead",
    "Dropped",
    "NoNonGoals",
    "NoSuchNonGoal",
    "NonGoal",
    "NotGoverned",
    "Written",
    "add",
    "address",
    "check",
    "drop",
    "read",
    "render",
    "validate",
]

#: Any heading whose text starts like this holds the non-goals. A prefix match rather than a
#: config key, because both live corpora already write it and neither writes it exactly: this
#: repository has "## Non-goals", Shio has "## Non-goals (do NOT add as tasks)".
HEADING = re.compile(r"^non-goals?\b", re.IGNORECASE)

#: `- **<lead>** <why>`, at column zero. The lead is bold and the why is everything after it,
#: which is what lets a parenthetical or a second sentence stay exactly as it was written.
_BULLET = re.compile(r"^- \*\*(?P<lead>[^*]+)\*\*(?P<why> .*)?$")
#: A bullet that is one, without the shape this governs — reported, never guessed at.
_ANY_BULLET = re.compile(r"^[-*+] (?P<rest>.*)$")
#: What a wrapped bullet's continuation looks like: indented, and not a bullet of its own.
_CONTINUATION = "  "

#: The two codes this format can be violated by, and the one a bullet's *shape* is. Named
#: here because `lint` reports them and a code spelled twice is a code that drifts once.
LEAD = "non-goal.lead"
WHY = "non-goal.why"
SHAPE = "non-goal.shape"


class NotGoverned(KeyError):
    """A write to a list this project has not declared governed (RK70).

    Refused rather than defaulted: a project whose non-goals are free prose would have every
    existing bullet judged by the first `add`, which is the adoption gate RK66 measures.
    """

    def __init__(self, where: str) -> None:
        super().__init__(
            f"{where} declares no [non_goals]: add the table to roadkeep.toml to govern the "
            f"list, since a schema applied to prose nobody wrote to it reports on adoption"
        )


class NoNonGoals(KeyError):
    """No heading holds a list to write to. A heading is the only thing that declares one."""

    def __init__(self, where: str) -> None:
        super().__init__(
            f"no non-goals heading in {where}: the heading declares the list, exactly as a "
            f"block heading declares a block (RK37)"
        )


class DuplicateLead(ValueError):
    """The lead is the address, so a second bullet claiming one is two answers to a scope."""

    def __init__(self, lead: str, where: str, lineno: int) -> None:
        self.lead = lead
        self.lineno = lineno
        super().__init__(
            f"{where}:{lineno} already leads with {lead!r}: the lead is how a non-goal is "
            f"addressed, so a second one carrying it is two answers about the same scope"
        )


class NoSuchNonGoal(KeyError):
    """A lead that addresses nothing. The leads that exist are named, because a constraint
    is looked up by the words a reader remembers and the stop inside the bold is invisible."""

    def __init__(self, lead: str, where: str, leads: tuple[str, ...]) -> None:
        self.lead = lead
        known = ", ".join(repr(one) for one in leads) or "none"
        super().__init__(
            f"no non-goal in {where} leads with {lead!r}: the list carries {known}"
        )


@dataclass(frozen=True, slots=True)
class NonGoal:
    """One bullet under the non-goals heading, as data and as the file spells it."""

    lead: str
    why: str
    #: 1-based, and a span because a filled bullet wraps: `first` is the line the `- ` is on.
    first: int
    last: int
    #: The source lines, verbatim and without their endings — the round-trip's evidence.
    lines: tuple[str, ...] = ()

    def __str__(self) -> str:
        return f"**{self.lead}** {self.why}"


@dataclass(frozen=True, slots=True)
class Written:
    """A non-goal inserted, and the document it went into. Save writes one file."""

    document: Document
    non_goal: NonGoal

    @property
    def lineno(self) -> int:
        return self.non_goal.first

    @property
    def rendered(self) -> tuple[str, ...]:
        return self.non_goal.lines

    def save(self) -> None:
        self.document.save()


@dataclass(frozen=True, slots=True)
class Dropped:
    """A non-goal removed, whole. Save writes the roadmap and nothing else."""

    document: Document
    non_goal: NonGoal
    #: How many bullets carried this address before the removal — 2 or more means the drop
    #: was also the repair for `lint`'s `non-goal.duplicate`, and the report says so.
    carried: int = 1

    @property
    def lines(self) -> tuple[str, ...]:
        return self.non_goal.lines

    def save(self) -> None:
        self.document.save()


def read(document: Document) -> tuple[NonGoal, ...]:
    """Every non-goal under the heading, in file order, with its continuations joined.

    A bullet the shape does not accept is *skipped*, not guessed at: this is the reader every
    caller shares, and `lint` is where a project that opted in hears about the difference.
    """
    return tuple(
        parsed for _, parsed in _bullets(document) if parsed is not None
    )


def rejects(document: Document) -> tuple[tuple[int, str], ...]:
    """The bullets under the heading that the grammar did not accept, with their line.

    Separate from :func:`read` for the same reason :class:`~roadkeep.document.Reject` is
    separate from an entry: a count that silently omitted them would read as a complete one.
    """
    return tuple(
        (lineno, raw) for (lineno, raw), parsed in _bullets(document) if parsed is None
    )


def address(lead: str) -> str:
    """The lead as an address: case-folded, and without the stop the bold may carry.

    One function, because `add` refuses a duplicate and `lint` reports one — two spellings of
    "the same lead" would mean a bullet the write path accepted and the gate then failed on,
    which is the split L1 exists to prevent.
    """
    return lead.strip().rstrip(".").casefold()


def render(config: Config, lead: str, why: str) -> tuple[str, ...]:
    """The bullet as the schema writes it: one line, filled to `prose`, continuations by two.

    The only writer of the format, exactly as `Schema.render` is for a task line — a bullet
    composed at a call site is the drift this module exists to make impossible.
    """
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
    """Every rule a schema can check about a non-goal, and no rule it cannot.

    Length and shape only. That the lead states a *constraint* rather than a task is the
    author's claim, the same way a symptom's falsifiability is (L4).
    """
    scope = config.non_goals or Scope()
    out: list[Violation] = []
    head, reason = lead.strip(), " ".join(why.split())
    if not head:
        out.append(Violation(LEAD, "lead", "a non-goal is addressed by its lead"))
    if "*" in head:
        out.append(
            Violation(
                LEAD,
                "lead",
                "the lead is bolded by the renderer, so it may not carry '*' itself",
            )
        )
    if len(head) > scope.lead:
        out.append(
            Violation(
                LEAD,
                "lead",
                f"{len(head)} characters, limit {scope.lead}",
            )
        )
    if not reason:
        out.append(Violation(WHY, "why", "a constraint nobody argued is a rule"))
    if len(reason) > scope.why:
        out.append(
            Violation(WHY, "why", f"{len(reason)} characters, limit {scope.why}")
        )
    return tuple(out)


def check(config: Config, lead: str, why: str) -> None:
    """Validate or raise, so a refusal reports every problem at once (as `Schema.check`)."""
    violations = validate(config, lead, why)
    if violations:
        raise SchemaError(violations)


def add(config: Config, lead: str, why: str) -> Written:
    """Insert one non-goal under the heading, after the last one there. Validated first.

    Refused, and nothing written, when the project has not opted in, when no heading declares
    the list, when a field is over its limit, or when the lead is already taken — the four
    refusals being what makes this a door rather than an `Edit` with extra steps.
    """
    if config.non_goals is None:
        raise NotGoverned(config.relative(config.source or config.root))
    document = config.document("roadmap")
    where = config.relative(config.path("roadmap"))
    heading = _heading_index(document)
    if heading is None:
        raise NoNonGoals(where)
    check(config, lead, why)

    head = lead.strip()
    existing = read(document)
    twin = next((n for n in existing if address(n.lead) == address(head)), None)
    if twin is not None:
        raise DuplicateLead(head, where, twin.first)

    lines = render(config, head, why)
    at, separate = _placement(document, heading, existing)
    updated = document
    if separate:
        # The line above is the heading or its prose, and a bullet glued to either reads as
        # part of it — so the blank that separates them is part of this insertion.
        updated = updated.insert_line(at, "")
        at += 1
    for offset, line in enumerate(lines):
        updated = updated.insert_line(at + offset, line)
    return Written(
        document=updated,
        non_goal=NonGoal(
            lead=head,
            why=" ".join(why.split()),
            first=at + 1,
            last=at + len(lines),
            lines=lines,
        ),
    )


def drop(config: Config, lead: str) -> Dropped:
    """Remove the non-goal a lead addresses, whole, wrapped lines included.

    The other half of the door, and the half a *correction* needs: a lead is the address, so a
    constraint whose lead changes is a different constraint — `- **No dates, quarters or
    estimates**` becoming `- **No dates or quarters**` is one retired and one written, which
    is honest in a way an in-place edit of the address would not be.

    Where two bullets carry one address — `lint`'s `non-goal.duplicate` — the later one goes,
    for `record drop`'s reason (RK67): the first is where the reader already found it. So this
    is also that finding's door, and a second call is what a third copy takes.
    """
    if config.non_goals is None:
        raise NotGoverned(config.relative(config.source or config.root))
    document = config.document("roadmap")
    where = config.relative(config.path("roadmap"))
    if _heading_index(document) is None:
        raise NoNonGoals(where)

    existing = read(document)
    wanted = address(lead)
    matches = tuple(one for one in existing if address(one.lead) == wanted)
    if not matches:
        raise NoSuchNonGoal(lead.strip(), where, tuple(one.lead for one in existing))
    going = matches[-1]
    return Dropped(
        document=_remove_span(document, going),
        non_goal=going,
        carried=len(matches),
    )


def _remove_span(document: Document, going: NonGoal) -> Document:
    """Take the bullet out, and the blank line the removal doubled.

    A list of one sits between blanks, so removing it leaves a paragraph break the file never
    had — and both spellings round-trip, which is exactly why nothing downstream would catch
    it (the same care `ship` takes with a task line, RK6).
    """
    start = going.first - 1
    updated = document.remove_lines(start, going.last)
    lines = updated.lines
    if start > 0 and start < len(lines) and blank(lines[start - 1]) and blank(lines[start]):
        return updated.remove_line(start)
    if start >= len(lines) and start > 0 and blank(lines[start - 1]):
        # The list was last in the file: its trailing blank has nothing left to separate.
        return updated.remove_line(start - 1)
    return updated


def _heading_index(document: Document) -> int | None:
    """The 0-based index of the non-goals heading line, or None when there is no list."""
    heading = next((h for h in document.headings if HEADING.match(h.text)), None)
    return None if heading is None else heading.lineno - 1


def _bullets(
    document: Document,
) -> tuple[tuple[tuple[int, str], NonGoal | None], ...]:
    """Every bullet under the heading with its span joined, parsed where the shape allows."""
    start = _heading_index(document)
    if start is None:
        return ()
    out: list[tuple[tuple[int, str], NonGoal | None]] = []
    spans: list[tuple[int, list[str]]] = []
    for offset, raw in enumerate(document.lines[start + 1 :], start=start + 2):
        body = raw.rstrip("\r\n")
        if body.startswith("#"):
            break  # the next heading ends the section, whatever its level
        if _ANY_BULLET.match(body):
            spans.append((offset, [body]))
        elif spans and body.startswith(_CONTINUATION) and not blank(body):
            spans[-1][1].append(body)
        elif blank(body):
            continue
    for first, span in spans:
        joined = " ".join(line.strip() for line in span)
        match = _BULLET.match(joined)
        parsed = None
        if match is not None:
            parsed = NonGoal(
                lead=match.group("lead").strip(),
                why=(match.group("why") or "").strip(),
                first=first,
                last=first + len(span) - 1,
                lines=tuple(span),
            )
        out.append(((first, span[0]), parsed))
    return tuple(out)


def _placement(
    document: Document, heading: int, existing: tuple[NonGoal, ...]
) -> tuple[int, bool]:
    """Where the bullet goes, and whether a blank line has to go in front of it.

    After the last non-goal, so the list stays in the order it was written — and after the
    section's *prose* when there is no bullet yet, never straight under the heading: this
    repository's list opens with a sentence telling a reader to check it, and a bullet above
    that sentence would make the instruction read as a footnote to the first non-goal.

    Whatever blank lines follow the section stay where they are, which is what keeps the
    separation from the next heading (or the file's end) exactly as the author left it.
    """
    if existing:
        # `last` is 1-based, so it is already the 0-based index of the line after it.
        return existing[-1].last, False
    end = len(document.lines)
    for offset, raw in enumerate(document.lines[heading + 1 :], start=heading + 1):
        if raw.lstrip().startswith("#"):
            end = offset
            break
    while end > heading + 1 and blank(document.lines[end - 1]):
        end -= 1
    return end, True
