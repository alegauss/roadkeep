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
from dataclasses import dataclass, replace
from pathlib import Path

from roadkeep.config import Config, Scope
from roadkeep.kernel.document import Document, blank
from roadkeep.kernel.schema import SchemaError, Violation, over_by, width

__all__ = [
    "HEADING",
    "LEAD",
    "SHAPE",
    "WHY",
    "Amended",
    "DuplicateLead",
    "Dropped",
    "NoNonGoals",
    "NoSuchNonGoal",
    "NonGoal",
    "NotGoverned",
    "Unshaped",
    "Written",
    "add",
    "address",
    "amend",
    "check",
    "drop",
    "leads",
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
#: Where a lead ends in a bullet that carries no bold head. A stop *and a space*, so an
#: abbreviation or a version number inside the sentence is not read as its end.
_SENTENCE = ". "

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


class Unshaped(ValueError):
    """A correction to a bullet this module could not have written (RK368).

    :func:`read` accepts a bullet with no bold head so that every constraint has an address
    (RK233), and that is safe precisely because nothing renders one back: `drop` removes the
    source span and :func:`render` writes only what `add` composed. An `amend` is the first
    verb that would render over lines it did not write, and on an unshaped bullet the render
    imposes the shape — which moves the lead, and the lead is the address.

    So the gate's `non-goal.shape` keeps the door it already had, and this refusal names it: a
    bullet whose head is its first sentence is repaired by `drop` and `add`, the pair that is
    honest about a changed address.
    """

    def __init__(self, lead: str, where: str, lineno: int) -> None:
        self.lead = lead
        self.lineno = lineno
        super().__init__(
            f"the bullet at {where}:{lineno} carries no bold lead, so {lead!r} is its first "
            f"sentence rather than an address this verb can write around — `non-goal drop` "
            f"then `non-goal add` is the repair, and it is honest about the lead changing"
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
    #: Did the bold shape hold? False where the lead is the bullet's first sentence instead
    #: (RK233). Carried rather than answered by a second parse, because every caller that
    #: needs the distinction — the gate's `non-goal.shape`, `adopt`'s unread count — is
    #: asking about a bullet this reader already read.
    shaped: bool = True

    def __str__(self) -> str:
        # Only what the file spells: a bullet that carries no bold head is not given one here,
        # because a rendering that invented the shape would read as prose the tool wrote (L4).
        return f"**{self.lead}** {self.why}" if self.shaped else " ".join(self.lines).strip()


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

    def save(self) -> tuple[Path, ...]:
        return self.document.save()


@dataclass(frozen=True, slots=True)
class Amended:
    """A non-goal's reason rewritten where it already sat. Save writes one file."""

    document: Document
    non_goal: NonGoal
    #: The reason as the file read it. Both readings, because what makes a correction
    #: reviewable is that a word changed and the bullet did not move.
    before: str = ""

    @property
    def changed(self) -> bool:
        return self.before != self.non_goal.why

    @property
    def lineno(self) -> int:
        return self.non_goal.first

    @property
    def rendered(self) -> tuple[str, ...]:
        return self.non_goal.lines

    def save(self) -> tuple[Path, ...]:
        return self.document.save()


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

    def save(self) -> tuple[Path, ...]:
        return self.document.save()


def read(document: Document) -> tuple[NonGoal, ...]:
    """Every non-goal under the heading, in file order, with its continuations joined.

    **Every bullet, including the ones the shape does not hold** (RK233). Skipping those made
    two readers of one list: `leads` gave them an address on purpose (RK68) so `brief` prints
    the whole scope, this one dropped them, and `drop` resolves against this one — so a
    constraint printed by one command answered to no address in the other. On an opted-in
    project that closed the last door: the gate reports `non-goal.shape` and names the
    rewrite, `Edit` is denied (RK22), and the pair that would do it — `drop` then `add` —
    could not reach the bullet. A finding whose remedy the tool refuses (RK16).

    The **round-trip question that decided it** (L3): nothing renders a parsed non-goal back
    into the file. :attr:`NonGoal.lines` is the source verbatim, `drop` removes that span, and
    :func:`render` writes only what `add` composed — so accepting a bullet this module could
    not have written costs no rendering it cannot do. What the shape *does* still decide is
    what the gate says about the bullet, which is :attr:`NonGoal.shaped` and not this filter.
    """
    return _bullets(document)


def rejects(document: Document) -> tuple[tuple[int, str], ...]:
    """The bullets under the heading whose shape the format does not hold, with their line.

    Still the gate's own answer and still counted apart (RK139): being addressable is not
    being in the format, and a count that omitted these would read as a complete one. What
    changed is that they are no longer *unread* — :func:`read` returns them, so the finding
    reported here has the door the finding is asking for.
    """
    return tuple(
        (goal.first, goal.lines[0]) for goal in _bullets(document) if not goal.shaped
    )


def leads(document: Document) -> tuple[str, ...]:
    """The lead of every bullet under the heading, in file order — what `brief` prints.

    Here rather than at the reader's call site so that the reader and the writer cannot
    disagree about what a lead *is*, exactly as :data:`HEADING` settles where the list is
    (RK68). One line now, because :func:`read` reads what this reads (RK233) — the agreement
    is the reader rather than two functions applying the same rule.

    Where the shape holds a lead is the bold run and only that. Where it does not, it is the
    first sentence of the bullet **joined across its continuations** — never a bold run found
    mid-sentence, which is emphasis and not an address: Turing writes ``is **not** a path``,
    whose middle bold made the printed non-goal the word ``not``.
    """
    return tuple(goal.lead for goal in _bullets(document))


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
    if width(head) > scope.lead:
        out.append(
            Violation(
                LEAD,
                "lead",
                over_by(width(head), scope.lead, measured=head),
            )
        )
    if not reason:
        out.append(Violation(WHY, "why", "a constraint nobody argued is a rule"))
    if width(reason) > scope.why:
        out.append(
            Violation(WHY, "why", over_by(width(reason), scope.why, measured=reason))
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


def amend(config: Config, lead: str, why: str) -> Amended:
    """Rewrite one non-goal's reason where it already sits, keeping its place (RK368).

    The door the other two bullet grammars have and this one did not. `record amend` exists so
    a ledger correction is not a move — never drop-and-re-add, which shows a reviewer a
    deletion where a word changed — and `section amend` is the same door for a live design.
    The non-goals had only `drop` plus `add`, and `add` inserts after the last bullet: measured
    at RK367, a constraint that sat fifth of eight moved to eighth for a reason no commit was
    about, and the order a reader takes for the shape of the list changed with it.

    **The lead is not a field**, exactly as a task's `symptom` is not `amend`'s: it is the
    address, so a constraint whose lead changes is one retired and one written, which is what
    `drop` already says and what the skill already tells an author. The asymmetry needs no
    refusal of its own — there is no argument to pass — and this sentence is where it is stated.

    Where two bullets carry one address the **first** is corrected, which is the other half of
    `drop`'s rule (RK67): that verb removes the later copy because the first is where the
    reader already found it, so the one that stays is the one a correction is about.

    Nothing is written when nothing differs, as at every other door: rewriting the same bytes
    makes a no-op look like an edit to every hook watching the file.
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
    standing = matches[0]
    if not standing.shaped:
        raise Unshaped(standing.lead, where, standing.first)

    # Its own lead and not the address the caller typed: `address` folds case and drops the
    # stop, so composing from the argument would rewrite the head this verb promises not to.
    check(config, standing.lead, why)
    reason = " ".join(why.split())
    if reason == standing.why:
        return Amended(document=document, non_goal=standing, before=standing.why)

    lines = render(config, standing.lead, reason)
    start = standing.first - 1
    updated = document.remove_lines(start, standing.last)
    for offset, line in enumerate(lines):
        updated = updated.insert_line(start + offset, line)
    return Amended(
        document=updated,
        non_goal=replace(
            standing, why=reason, last=start + len(lines), lines=lines
        ),
        before=standing.why,
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


def _bullets(document: Document) -> tuple[NonGoal, ...]:
    """Every bullet under the heading, spans joined, each one addressable (RK233).

    The continuation lines are folded in before a lead is taken, which is what lets it come
    from the whole bullet instead of from its first physical line (RK68) — the difference
    between Turing's first non-goal forbidding ten things and appearing to forbid three.

    Where the bold shape does not hold, the lead is the first sentence and the `why` is what
    follows it. Both **verbatim**, stop included where the sentence is the whole bullet,
    exactly as the bold lead is kept: normalizing an author's punctuation to satisfy a rule
    nobody stated is the rewrite this refuses to be (L4).
    """
    start = _heading_index(document)
    if start is None:
        return ()
    spans: list[tuple[int, list[str]]] = []
    for offset, raw in enumerate(document.lines[start + 1 :], start=start + 2):
        body = raw.rstrip("\r\n")
        if body.startswith("#"):
            break  # the next heading ends the section, whatever its level
        if _ANY_BULLET.match(body):
            spans.append((offset, [body]))
        elif spans and body.startswith(_CONTINUATION) and not blank(body):
            spans[-1][1].append(body)
    out: list[NonGoal] = []
    for first, span in spans:
        joined = " ".join(line.strip() for line in span)
        where = {"first": first, "last": first + len(span) - 1, "lines": tuple(span)}
        match = _BULLET.match(joined)
        if match is not None:
            out.append(
                NonGoal(
                    lead=match.group("lead").strip(),
                    why=(match.group("why") or "").strip(),
                    **where,
                )
            )
            continue
        marker = _ANY_BULLET.match(joined)
        rest = marker.group("rest") if marker is not None else joined
        head, _, tail = rest.partition(_SENTENCE)
        out.append(NonGoal(lead=head.strip(), why=tail.strip(), shaped=False, **where))
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
