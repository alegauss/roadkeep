"""Reading a governed file, and the invariant that lets the tool write one (RK2).

A tool that edits a file a human also edits has to prove it understood that file
before it is allowed to replace it, so the ownership test is mechanical: parse →
render → byte-identical, or refuse (L3). Two independent halves of that:

* **The file** round-trips because a :class:`Document` keeps every source line
  verbatim, endings included, and :meth:`Document.render` is a join. Interpretation
  is a layer over the lines, never a replacement for them — so a document can be
  written back untouched even where the parser understood nothing.
* **The line** round-trips only if ``schema.render(parsed) == raw``. Where it does
  not, the entry is *non-canonical* and every mutator refuses the whole file
  (:class:`RoundTripError`) rather than normalizing what it may have misread. A
  formatter that "fixes" what it misunderstood destroys work no diff review catches.

The parser is written to be lossless: every branch either keeps the text in a field
or rejects the line, so no file it accepts comes back changed — 144 lines across
this repository, Shio and Turing, none of them non-canonical. That makes the guard
look redundant until the configuration moves: a file written under one
`roadkeep.toml` and rendered under another (a different marker set, a ledger's
missing deps field) comes back reformatted, and **a configuration change is not a
licence to rewrite the files written before it.** The guard is also what keeps any
future normalizing parser honest, because it fails the corpus instead of a review.

Nothing here silently drops a line it failed to read: a bullet that carries a status
marker but does not match the grammar becomes a :class:`Reject` with a reason, and so
does one that puts an *undeclared* marker where the marker goes, **no marker at all**
where a bold id leads (RK43), or GitHub's **task-list checkbox** there (RK103) — otherwise
it reads as prose and leaves no trace. That is
the data `audit` (RK10) prints, because a count whose misses are invisible is the failure
mode the grep it replaces already had. Measured: Shio's changelog is 920 bullets and
parsed as 0 entries *and* 0 rejects, the one shape that made the miss silent twice.

The marker slot is also the one part of the grammar a file may not have. Both live
ledgers write `- **T1** — …`, so `[ledger] marker = false` (L6) says the status is the
file's rather than the line's — every entry in it shipped — and there a marker on a line
is the reject instead, with one exception the file's own claim creates: a **departure** is
what such a ledger does not say about itself, so the retired line is the one that carries a
marker (RK125), and whether a line fills the slot is decided per line by
:meth:`Schema.marks` — the same answer `render` writes from.
"""

from __future__ import annotations

import contextlib
import functools
import os
import re
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

from roadkeep.schema import ARROW, EM_DASH, ID_SHAPE, NO_DEPS, Dep, Schema, Task

if TYPE_CHECKING:  # a name for the annotation only: `config` reads this module, not back
    from roadkeep.config import Config

#: Everything after the marker slot, up to the symptom. `deps` is optional because the
#: ledger has none; the trailing pointer is stripped before this runs (see `_split_ref`).
#: How many times :func:`write_atomically` retries the rename, and how long it pauses
#: between them. Small: the case this covers is a Windows indexer holding the target open
#: for a moment, and anything longer than that is a file somebody means to be holding.
_REPLACE_TRIES = 5
_REPLACE_PAUSE = 0.05

#: How many distinct (text, schema) parses :func:`_parsed` keeps (RK211). Enough for the
#: four governed roles a transaction reads plus the state each is about to become; a bigger
#: number would hold megabytes of somebody else's ledger for no further hit.
_PARSE_CACHE = 12

#: The bold head, and the qualifier a **partial** entry carries inside it (RK121). Inside
#: the bold because that is where the corpus already writes it — Shio has seven, from
#: `- **SH96 (local half)** —` to `- **SH275 (partial)** —` — and a grammar that demanded
#: the qualifier somewhere else would read those seven as no id at all, which is how two
#: deps came to report `SH96` as being in neither file while the roadmap annotated it ✅.
_TASK_HEAD = (
    r"\*\*(?P<id>[A-Za-z0-9]+)(?: \((?P<part>[^)]+)\))?\*\*"
    r"(?: \(deps: (?P<deps>[^)]*)\))?"
)
#: The two slots a file may not have (`[ledger]`, RK43 and RK48), composed rather than
#: written out four times: a grammar per combination is four things that drift apart.
_SYMPTOM = rf" \*\*(?P<symptom>.+?)\*\* {EM_DASH} "
_WHY = r"(?P<why>.+)$"


@functools.lru_cache(maxsize=None)
def _task_re(marker: bool, symptom: bool) -> re.Pattern[str]:
    """The task-line grammar for one file's shape, anchored at both ends.

    Cached because it is rebuilt per line otherwise, and the four combinations are the
    whole domain: with a marker or without, with a symptom slot or without.
    """
    status = r"(?P<status>\S+) " if marker else ""
    middle = _SYMPTOM if symptom else f" {EM_DASH} "
    return re.compile(rf"^- {status}{_TASK_HEAD}{middle}{_WHY}")


_HEADING_RE = re.compile(r"^(?P<hashes>#{1,6}) (?P<text>.*)$")
_BULLET_RE = re.compile(r"^(?P<indent>\s*)[-*+] (?P<rest>.*)$")
#: A fenced code block's delimiter, indented or not — a fence inside a list item is (RK53).
_FENCE_RE = re.compile(r"^\s*(?P<marks>`{3,}|~{3,})")
#: A bullet that puts *something* where a marker goes and a bold id after it — how an
#: undeclared marker is caught instead of read as prose (see `_wears_the_marker_slot`).
#: The qualifier as it appears inside the bold, for the two shape tests below (RK121).
#: They decide whether a bullet *claims* the task line's shape, and a claim they declined
#: is prose — which is how Shio's seven partial entries came to be read as no line at all.
_PART = r"(?: \([^)]+\))?"
_MARKER_SLOT_RE = re.compile(rf"^\S+ \*\*[A-Za-z0-9]+{_PART}\*\*")
#: A line that is nothing but pipe-delimited cells, and the `|---|` rule that makes a run
#: of them a table rather than prose that happens to use pipes. Two shapes and no grammar:
#: what is *inside* the cells is deliberately never read (RK98).
_ROW_RE = re.compile(r"^\s*\|.*\|\s*$")
_RULE_RE = re.compile(r"^\s*\|(?:\s*:?-+:?\s*\|)+\s*$")
#: A **top-level** list item of any Markdown flavour — `-`, `*`, `+` or `1.` / `1)` (RK279).
#: Where a task would be, in the shape an unadopted backlog is actually in. Unindented on
#: purpose: a nested bullet is detail of the item above it, and counting it would price one
#: task as several. What is inside is never read, for the reason :data:`_ROW_RE` gives.
_ITEM_RE = re.compile(r"^(?:[-*+]|\d+[.)]) +\S")
#: A bullet whose first token *is* the bold id, so the marker slot is empty rather than
#: wrong (see `_leads_with_the_id`). Id-shaped and nothing else: the shape is what tells
#: `- **T1** — …` from `- **Delete** the 3 old files`.
_BOLD_ID_RE = re.compile(rf"^\*\*{ID_SHAPE}{_PART}\*\*(?=\s|$)")
#: GitHub's task-list checkbox where the marker goes, with a bold id after it — the shape
#: neither test above catches, because `[ ]` is two tokens where a marker is one and `[x]`
#: carries a letter (see `checkbox`).
_CHECKBOX_RE = re.compile(rf"^(?P<box>\[[ xX]?\]) \*\*{ID_SHAPE}{_PART}\*\*(?=\s|$)")
_POINTER = f" {ARROW} §"


def shading(label: str, declared: Sequence[str]) -> str:
    """The clause that makes an undeclared-block refusal actionable, or "" (RK216).

    A label sharing a prefix with a declared one turns *no heading declares Block A
    (declares: … AJ …)* into a sentence nobody can act on: the only thing it asks for is a
    heading already there under a letter the caller never typed. Measured in Claude Code
    Tray, on a `ship` whose task was in AJ.

    One function and not one sentence per raiser, because four places compose this refusal —
    this module's write refusal, `Census.select`, `pick` and `delivered` — and their *other*
    clauses legitimately differ: a write may not invent a heading, a read is simply asking
    about a block that is not there, and `delivered` has to say the ledger went unread
    because its empty answer is consumed as evidence (RK433). The confusion is the same in
    all four, so it is written once and the tails stay their own.

    Both directions, `A` against a declared `AJ` and `AJ` against a declared `A` being one
    mistake seen from two ends.
    """
    shades = tuple(
        other
        for other in declared
        if other != label and (other.startswith(label) or label.startswith(other))
    )
    if not shades:
        return ""
    verb = "share" if len(shades) > 1 else "shares"
    return (
        f" — but {', '.join(shades)} {verb} a prefix with {label}, so check that the label "
        f"reached this command whole"
    )


def declares(declared: Sequence[str], *, named: bool = False) -> str:
    """What an undeclared-block refusal says about the labels that *are* declared (RK296).

    Which is **nothing**, unless there are none. RK216 put the whole list in the sentence and
    RK257 named the file it came from, and what was left is a project with 90 blocks answering
    a question nobody asked: the two clauses that are the remedy — which file, and `block add`
    — arrive after a line of labels the reader has to scan past.

    The list is load-bearing exactly once, when the label really was mangled, and there the
    neighbours are what makes the mistake visible. That case is :func:`shading`'s, and it
    already answers it *by name* — the labels sharing a prefix are the subset a confused
    author needs. Where nothing shades, the rest are a set the author is not choosing from:
    they typed a label, they are not picking from a menu.

    Not a cap on the list, which is the answer that reads well and helps nobody: an elision
    (`A, AA, AB, … and 87 more`) keeps the length and loses the one label that would have
    settled it — RK68's argument about a bounded list read as the whole one.

    What survives is the empty case, because "this file declares no blocks at all" is a
    different diagnosis rather than a shorter list: there is no label to have mistyped, and
    `block add` is the whole answer. `named` says the refusal already spelled the file, so the
    clause says *it* rather than repeating the path.
    """
    if declared:
        return ""
    return " (it declares none)" if named else " (nothing declares any block)"


class UnknownBlock(ValueError):
    """A block is declared by a heading and by nothing else (RK37).

    Raised by every write that files something under a block — a task line (RK5) and a
    rationale section (RK9) — because a heading invented by a write puts the text where
    nothing looks for it, and one that is merely missing is a heading the author can add.

    Which is the advice that stops being safe when the label **shares a prefix with a
    declared one** (RK216). Measured in Claude Code Tray: a `ship` on a task in Block AJ
    refused with *no heading declares Block A (declares: AG, AE, AB, AC, AI, AJ, …)*, from a
    list containing AJ — a sentence nobody can act on, because the only thing it asks for is
    a heading that is already there under a letter the caller never typed, and taking it at
    its word opens a second heading over the first one's work.

    So the confusion is named here rather than at a caller. Every write that files under a
    block raises this one exception, and the two things needed to spot it — the label asked
    for and the labels declared — are the two it already carries. Whatever mangled the input
    (that incident was PowerShell 5.1 and a long inline argument), the file is untouched and
    the message is the only thing the author has to go on.

    And the **recovery is one command**, so the refusal spells it (RK257). Measured on a
    `ship` whose roadmap plainly declared the block: the labels listed are the ledger's, not
    the roadmap's, so an author reading a list that omits a heading they can see in front of
    them concludes the label is wrong — the one thing it is not. Naming the file the list
    came from and naming `block add`, which opens the heading in every governed file still
    missing it, turns a refusal that had to be researched into one that can be acted on.
    ``where`` is the caller's to render (RK181), and every write that has a
    :class:`~roadkeep.config.Config` passes it.

    The labels themselves are **not** listed (RK296), which is the half of RK257 that was
    left: the file and the verb are the remedy, and a line of labels in front of them is a
    question nobody asked. :func:`declares` is where that decision is written, and
    :attr:`declared` still carries them for a caller that wants them.

    ``into`` is the file the line was going into, said only when it is **not** the file the
    labels came from (RK404). One raiser is in that position: `add` asks the ledger for the
    heading the first `ship` will need (RK380), and the sentence it reuses was written for a
    write into the file it names — so an author adding a line to a roadmap whose `## Block A`
    is on the screen in front of them reads a refusal about `CHANGELOG.md` as *your label is
    wrong*, which is the one thing it is not. The same confusion RK257 measured one surface
    over. Absent where the two are one file, which is every other raiser: there the clause
    would say the thing the sentence already said.

    ``organise`` is the role the remedy needs when the file declares **no** block at all
    (RK405). `block add` skips such a file, so the bare command this sentence names is one
    more refusal — measured on a project whose ledger was prose, where `ship`, `block add
    <its label>` and `block add <a fresh label>` all declined and the guard denied the edit.
    Said only in that state, because where the file declares blocks the argument is spent.
    """

    def __init__(
        self,
        label: str,
        declared: Sequence[str],
        where: str = "",
        word: str = "Block",
        *,
        into: str = "",
        organise: str = "",
    ) -> None:
        self.label = label
        self.declared = tuple(declared)
        self.into = into
        self.organise = organise
        file = f" in {where}" if where else ""
        # The remedy that works on *this* file (RK405). `block add` skips a file organised
        # by nothing, so where the labels came back empty the bare command is one more
        # refusal, and the argument that opens the first heading is the whole answer.
        starting = f" --organise {organise}" if organise and not self.declared else ""
        elsewhere = (
            f", though {into} (where this line goes) declares it"
            if into and into != where
            else ""
        )
        # The tail this refusal adds to the shared diagnosis: at a *write* the danger is
        # taking "add the heading" at its word and opening a second one over the first's work.
        shades = shading(label, self.declared)
        if shades:
            shades += (
                " before declaring a second heading over the first one's work — and if it "
                "did, the verb is"
            )
        else:
            shades = "; the verb that opens it wherever it is missing is"
        super().__init__(
            f"no heading declares {word} {label}{file}"
            f"{declares(self.declared, named=bool(where))}{elsewhere}: a heading "
            f"invented by a write files the text where nothing looks for it{shades} "
            f'`block add {label} --title "<its title>"{starting}`'
        )


class RepeatedHeading(ValueError):
    """One label, two headings — refused at every write that files under it (RK391).

    RK390 shut this door at `init`, which was one of four ways in: a roadmap edited by hand,
    brought under the tool by `adopt`, or merged from two branches arrives at the same file,
    and there `add --block A` filed under the **last** of them. That was never a decision —
    it is what scanning to the end leaves — and a verb resolving an ambiguity by position is
    the part that may not survive whatever the gate does about the state.

    Refused rather than defaulted to the first, which is the same act one line earlier: both
    headings are somebody's, the entries under each are already filed, and a tool that picks
    one files the next line where half the readers are not looking. The **line numbers of
    both** are named, because the fold keeps the first heading and a reader has to see which
    that is — and the remedy is `block merge` (RK403), which does exactly that fold: it is
    the tool's own merge of the two regions, not the hand-edit the guard denies.

    `block.repeated` is the other end, and this is not it: the gate reports the state and
    this stops a write from adding to it.
    """

    def __init__(
        self, label: str, linenos: Sequence[int], where: str = "", word: str = "Block"
    ) -> None:
        self.label = label
        self.linenos = tuple(linenos)
        self.where = where
        file = f"{where}:" if where else "line "
        lines = ", ".join(f"{file}{lineno}" for lineno in self.linenos)
        super().__init__(
            f"{len(self.linenos)} headings declare {word} {label} ({lines}): one label is "
            f"one heading, and a write that chose between them would file this line where "
            f"half the readers are not looking — `block merge {label}` folds them into the first"
        )


class RoundTripError(RuntimeError):
    """The tool may not write a file whose lines it cannot reproduce.

    Refusal is the whole point: the alternative is a rewrite that silently
    normalizes a line the parser misread.
    """

    def __init__(self, offenders: tuple[Entry, ...], path: Path | None = None) -> None:
        self.offenders = offenders
        self.path = path
        where = f"{path}: " if path else ""
        detail = ", ".join(f"{e.task.id} (line {e.lineno})" for e in offenders)
        super().__init__(
            f"{where}{len(offenders)} line(s) do not round-trip and this file will "
            f"not be rewritten: {detail}"
        )


class Wrapped(ValueError):
    """A sentence rewrite on an entry the parse holds only the first line of (RK179).

    A ledger written before this tool existed wraps its bullets, and a wrapped entry's `why`
    is only as much of the sentence as fits on line one. Rewriting that line — which is all
    :meth:`Document.replace_task` can reproduce — left the tail of the old sentence beneath
    the new one, and the command printed the first line and called it amended.

    Refused rather than defaulted either way, because both defaults are wrong: rewriting the
    line alone is the entry that states an outcome followed by half a problem, and deleting
    the span silently is prose no field of this task holds, removed by a command that was
    asked to change a word. So the caller says how many lines the rewrite replaces — the
    idiom `record drop --line` already uses, where naming what you read *is* the door — and
    a count that does not match the span is refused too, an off-by-one here being the
    deletion of somebody's paragraph.

    `verb` is what the other doors reaching it asked for. `ship <id>` completing a partial
    replaces that entry with a *different sentence* (RK193), and the roadmap's own `amend`
    and `restate` are the same write one file over (RK195) — same rule, different word for
    what the caller called it.
    """

    def __init__(
        self,
        task_id: str,
        where: str,
        entry: Entry,
        *,
        given: int | None,
        verb: str = "correcting it",
    ) -> None:
        self.task_id = task_id
        self.lineno = entry.lineno
        self.owned = entry.stop - entry.index
        self.given = given
        span = (
            f"lines {entry.lineno}-{entry.stop}"
            if self.owned > 1
            else f"line {entry.lineno}"
        )
        said = (
            (
                f"the parse holds only as much of its sentence as fits on line "
                f"{entry.lineno}, so {verb} replaces all {self.owned} — read them "
                f"with `show {task_id}`, which prints them, and pass --lines {self.owned}, "
                f"which is you saying the text below the first line is the rest of the "
                f"sentence being replaced"
            )
            if given is None
            else (
                f"--lines {given} is not that count: pass --lines {self.owned}, or check "
                f"that this is the entry you read"
            )
        )
        super().__init__(f"{where}:{entry.lineno}: {task_id} is written over {span} and {said}")


def counted(
    task_id: str, where: str, entry: Entry, lines: int | None, *, verb: str
) -> None:
    """Refuse a :meth:`Document.rewrite_entry` the caller has not said they read.

    Beside the write it guards rather than inside any one caller, because the invariant is
    that method's — *no caller reaches it without having said how many lines the write
    replaces* — and three doors now do: `record amend` (RK179), the `ship` that completes a
    partial (RK193), and the roadmap's own `amend` and `restate` (RK195). A rule restated
    once per caller is a rule the fourth caller does not get.

    A count that matches is silence.
    """
    if lines is None:
        if entry.wrapped:
            raise Wrapped(task_id, where, entry, given=None, verb=verb)
    elif lines != entry.stop - entry.index:
        raise Wrapped(task_id, where, entry, given=lines, verb=verb)


class StaleFile(RuntimeError):
    """The file moved between the read and the write, so the write is abandoned (RK116).

    The second half of L3's question. :class:`RoundTripError` asks whether this document
    is one the tool understood; this asks whether it is still the document that was read —
    and `save` truncating a file it last saw seconds ago is how one agent's line disappears
    while both commands exit 0.

    Deliberately blind to *what* changed: a write that lands on top of a file somebody else
    already rewrote is refused whether the other writer was a second roadkeep process, a
    hand edit the hook missed, or a `git checkout` mid-session. Merging is the caller's
    business, and the caller here is asked to re-run the command against the file as it now
    is — which costs one command and loses nothing.
    """

    def __init__(self, path: Path | None = None, *, missing: bool = False) -> None:
        self.path = path
        self.missing = missing
        where = f"{path}: " if path else ""
        became = "no longer exists" if missing else "changed since it was read"
        super().__init__(
            f"{where}the file {became}, so this write was abandoned rather than "
            f"applied on top of it — re-run the command"
        )


@dataclass(frozen=True, slots=True)
class Entry:
    """A parsed task line, with the provenance needed to refuse or replace it."""

    task: Task
    raw: str
    lineno: int  # 1-based, as an editor counts
    #: The last line this entry owns — its own, unless the bullet wraps (RK157). A ledger
    #: written before this tool existed wraps at the median, and the lines under a bullet
    #: parse as nothing at all, so an entry's *end* was a fact no reader held: `place`
    #: answered "the line after the last entry" with the line after that entry's **first**
    #: line, and every continuation below it was re-attributed to whatever shipped next.
    #: 0 means the entry is one line, which is every line of a governed roadmap (the
    #: format has no multi-line task line) — read through :attr:`stop`, never directly.
    last: int = 0

    @property
    def index(self) -> int:
        """0-based index into :attr:`Document.lines`."""
        return self.lineno - 1

    @property
    def stop(self) -> int:
        """0-based index one past the last line this entry owns — where the next one starts.

        What an insertion inserts at and a removal removes up to. The two writes wanted the
        same answer and each had its own arithmetic for it, which is the whole reason this is
        a field: a span computed twice is a span two writes can disagree about.
        """
        return max(self.last, self.lineno)

    @property
    def wrapped(self) -> bool:
        """Does this entry own lines the parse read nothing from?

        The commonest source is a project turning the one-sentence and terminator rules off
        for a role (RK52), which is what a ledger of history written by hand needs. It is
        **not** the only one, and reading it that way is what left RK195 unmeasured: the
        rules bound the bullet, and a wrapped entry is a fact about the *line beneath* it. A
        first line that satisfies every rule and carries a hand-written note underneath is
        wrapped, parses without a reject, and lints clean — on a roadmap, under the default
        schema, with nothing turned off. `add` refuses to write one, which is why every
        governed roadmap reads as zero and why adoption is the whole population.
        """
        return self.last > self.lineno


@dataclass(frozen=True, slots=True)
class Reject:
    """A marker-bearing bullet the grammar did not accept, and why.

    ``block`` is the heading it sits under, known at parse time and kept because a
    count reported per block has to report its misses per block too (RK10) — a
    total that is honest and a column that is not is the same failure, narrower.
    """

    raw: str
    lineno: int
    reason: str
    block: str = ""


@dataclass(frozen=True, slots=True)
class Row:
    """A table row under a block heading — a task in a shape this format has no reader for.

    A backlog kept as `| ID | Status | Task |` rows parses as **nothing**: not an entry,
    and not a :class:`Reject` either, because a reject is a bullet that claimed the task
    line's shape and a row never claims it. So the file reads exactly as an empty one does,
    which is the single answer an adoption estimate may not give (RK98).

    Never parsed, only counted. Reading the shape is what tells a table from an empty file;
    reading the cells would be a second line format, and one is what L3 keeps singular.
    """

    raw: str
    lineno: int
    block: str


@dataclass(frozen=True, slots=True)
class Item:
    """A plain list item under a block heading — the other shape with no reader (RK279).

    :class:`Row` caught a backlog kept as a table. This catches the one almost every
    unadopted roadmap is actually in: `- [ ] fix login`, `- fix login`, `1. fix login`. It
    claims none of the task line's shape, so it is not a :class:`Reject`; it holds no pipes,
    so it is not a :class:`Row` — and the file therefore read exactly as an empty one does,
    which is the single answer an adoption estimate may not give (RK98).

    Counted under a **declared block** and nowhere else, which is what keeps the frame out of
    the number: a roadmap's preamble is bullets, its non-goals are bullets, and a prose aside
    is a bullet. None of those sit under a block heading, and a task does.

    Never parsed, only counted — the line :class:`Row` draws, for the same reason.
    """

    raw: str
    lineno: int
    block: str


@dataclass(frozen=True, slots=True)
class Heading:
    """A Markdown heading. ``label`` is set when it names a block."""

    level: int
    text: str
    lineno: int
    label: str | None = None


@dataclass(frozen=True, slots=True)
class Document:
    """A governed Markdown file: verbatim lines, plus what was understood of them."""

    schema: Schema
    lines: tuple[str, ...]  # with their endings, so render() is a join
    entries: tuple[Entry, ...] = ()
    rejects: tuple[Reject, ...] = ()
    headings: tuple[Heading, ...] = ()
    #: Rows of a Markdown table filed under a block heading (RK98). Read here and nowhere
    #: else, because this is the only reader of a file — and a count taken by a second
    #: scanner would be a second fence state machine to keep in step with this one.
    tabular: tuple[Row, ...] = ()
    #: Plain list items filed under a block heading (RK279) — the same contract as
    #: :attr:`tabular`, for the shape that is not a table. Read here for the same reason:
    #: this is the only reader of a file, and the block a line sits under is state only
    #: this pass has.
    listed: tuple[Item, ...] = ()
    path: Path | None = None
    #: The bytes :meth:`load` read, kept so :meth:`save` can ask whether the target is
    #: still them (RK116). Carried through every mutation — the point is what was on disk
    #: when this document was *read*, not what it holds now — and None for a document
    #: parsed from a string, which has no disk state to have moved.
    source: str | None = None
    #: The project this file was read for, set by :meth:`config.Config.document` and by
    #: nothing else — what a transaction needs to re-derive the projections its own write
    #: stales (RK188). None for a document parsed from a string or loaded by path alone:
    #: there is no project to project, and a save then writes exactly one file.
    config: Config | None = None

    # -- reading -----------------------------------------------------------

    @classmethod
    def parse(
        cls, text: str, schema: Schema | None = None, path: Path | None = None
    ) -> Document:
        schema = schema or Schema()
        lines = tuple(text.splitlines(keepends=True))
        entries: list[Entry] = []
        rejects: list[Reject] = []
        headings: list[Heading] = []
        pipes: list[Row] = []
        items: list[Item] = []
        loose: set[int] = set()
        block: str | None = None

        fence: str | None = None
        for number, raw in enumerate(lines, start=1):
            body = raw.rstrip("\r\n")
            opened = _FENCE_RE.match(body)
            if opened is not None:
                fence = _fenced(fence, opened.group("marks"))
                continue
            if fence is not None:
                # Inside a fence nothing is a list item and nothing is a heading. A quoted
                # example is what a rationale section is for, and reading it as a task gave
                # the file an id nothing wrote and a line that could not round-trip.
                continue
            heading = _HEADING_RE.match(body)
            if heading:
                label = _block_label(heading.group("text"), schema)
                headings.append(
                    Heading(
                        level=len(heading.group("hashes")),
                        text=heading.group("text"),
                        lineno=number,
                        label=label,
                    )
                )
                # A non-block heading ends the block it followed: a task under
                # "## Priority queue" belongs to no block, and guessing one would
                # put it in the wrong place on the next write.
                block = label
                continue

            if _ROW_RE.match(body):
                # Collected raw and resolved after the loop: whether a run of pipe lines is
                # a table is decided by a rule row further down, which a single pass over
                # the file cannot know at the line it is looking at.
                pipes.append(Row(raw=body, lineno=number, block=block or ""))
                continue

            outcome = _read_bullet(body, schema, block or "")
            if outcome is None:
                if block and _ITEM_RE.match(body):
                    # A task in a shape this format has no reader for (RK279). Counted *as
                    # well as* left loose below, not instead: `loose` decides where an entry's
                    # span ends and this decides what an estimate saw, and one line can
                    # honestly be both — a continuation of the bullet above, and a bullet.
                    items.append(Item(raw=body, lineno=number, block=block))
                if body.strip():
                    # A non-blank line this pass read nothing from: the continuation of the
                    # bullet above it, or a paragraph. Which of the two is decided after the
                    # loop, by whether anything is directly above — and it has to be decided,
                    # because until RK157 an entry's end was nobody's fact (see `Entry.last`).
                    loose.add(number)
                continue
            if isinstance(outcome, str):
                rejects.append(
                    Reject(
                        raw=body, lineno=number, reason=outcome, block=block or ""
                    )
                )
            else:
                entries.append(Entry(task=outcome, raw=body, lineno=number))

        return cls(
            schema=schema,
            lines=lines,
            entries=_spanned(entries, loose),
            rejects=tuple(rejects),
            headings=tuple(headings),
            tabular=_tables(pipes),
            listed=tuple(items),
            path=path,
        )

    @classmethod
    def load(cls, path: str | Path, schema: Schema | None = None) -> Document:
        path = Path(path)
        # newline="" keeps the file's endings intact; the default would translate
        # CRLF to LF on read and the tool would "own" a file it silently rewrote.
        # (open(), not read_text(newline=…) — that keyword is 3.13+, and this
        # package supports 3.11.)
        with path.open("r", encoding="utf-8", newline="") as handle:
            text = handle.read()
        # `source` is set here and nowhere else: a document that was read from disk is the
        # only one that can find the disk changed under it (RK116).
        return replace(_parsed(text, schema), path=path, source=text)

    def render(self) -> str:
        """The source, exactly. This is what makes L3 a fact rather than a hope."""
        return "".join(self.lines)

    @property
    def newline(self) -> str:
        """The file's dominant ending, so an inserted line matches its neighbours."""
        for line in self.lines:
            if line.endswith("\r\n"):
                return "\r\n"
            if line.endswith("\n"):
                return "\n"
        return "\n"

    def by_id(self) -> dict[str, Entry]:
        """First entry per id. A duplicate id is a lint error (RK14), not a merge."""
        out: dict[str, Entry] = {}
        for entry in self.entries:
            out.setdefault(entry.task.id, entry)
        return out

    def block(self, label: str) -> tuple[Entry, ...]:
        return tuple(e for e in self.entries if e.task.block == label)

    def holds(self, label: str) -> bool:
        """Whether any line in **this** file is filed under ``label`` (RK300).

        The one reader of "is that block still occupied", and it exists because there were
        two: `ship`'s event line and the transition `lint --since` notes (RK269) were one
        expression written twice in modules that never call each other. That is the shape
        this project removes everywhere else — one `GUARDED_TOOLS`, one `Schema.validate`,
        `_only_reads` reading the parser's own declaration — and a test holding two outputs
        level is weaker than one caller, because it does not stop a third reader from
        spelling it a fourth way.

        The event has since moved **up** rather than away (RK438): a boolean about this file
        could not tell a finished block from a paused one, so the write path asks
        :meth:`~roadkeep.backlog.Standing.of` for the four-state answer instead. That reader
        is this one plus the ledger and the store, so the question is unchanged and only its
        scope grew. `lint --since` still asks *this* file, because a transition inside one
        document is what it reports.

        Deliberately **not** named for openness. "Open" is not a property of a label, it is a
        property of the file being asked: the roadmap is the active backlog, so
        `roadmap.holds(label)` *is* the open question, while the deferred store answers about
        paused work and the ledger about shipped (RK92). A name carrying the word would make
        the wrong one of those three read as a bug rather than as a different question.

        `any` and not `len(self.block(label))`: the answer is a boolean, so the walk stops at
        the first line instead of building a tuple to measure — which is what the gate wants,
        asking this once per declared heading per tree.
        """
        return any(entry.task.block == label for entry in self.entries)

    def heading(self, label: str) -> Heading | None:
        """The first heading naming ``label`` — where `add` inserts (RK5).

        A **read**, and it keeps the first of two because every question asked of a broken
        file has to have an answer. What may not resolve by position is a *write*, which is
        :func:`~roadkeep.authoring.place`'s refusal off :meth:`declaring` (RK391).
        """
        return next((h for h in self.headings if h.label == label), None)

    def declaring(self, label: str) -> tuple[Heading, ...]:
        """Every heading naming ``label`` — one, in a file any verb can address (RK391).

        The distinction :meth:`heading` cannot make, and the reason it is a method rather
        than a comprehension at the one call site: two headings under one label is a state
        the gate reports and the write path refuses, and both ends have to be reading the
        same thing. A file with none is :class:`UnknownBlock`'s case and returns empty here.
        """
        return tuple(heading for heading in self.headings if heading.label == label)

    def subtree_end(self, heading: Heading) -> int:
        """Where a heading's whole region ends: the next heading of the **same or higher**
        level, as a 0-based index one past the last line it owns (RK115).

        What a deletion takes and what an insertion may not cross. A nested heading is
        *inside* this region — `drop` removes the subsection with the section, and a task
        appended to a block goes after everything filed under it.
        """
        return self._ends_before(heading, lambda later: later.level <= heading.level)

    def prose_end(self, heading: Heading) -> int:
        """Where a heading's **own** prose ends: the next heading of *any* level, as a
        0-based index one past the last line (RK115).

        The other of the two answers, and the narrower one: a paragraph under a nested
        heading belongs to that heading, so a budget charging this one may not count it and
        a line placed past it would read as the nested heading's.
        """
        return self._ends_before(heading, lambda later: True)

    def _ends_before(self, heading: Heading, stops: Callable[[Heading], bool]) -> int:
        """The one loop the two rules above differ only in the predicate of.

        Four call sites used to walk :attr:`headings` themselves — two under each rule —
        which is the id's defect (RK109) one structure over: a question answered where it is
        asked rather than by the thing that read the file. No boolean, because a flag passed
        by hand is what that fix removed: the two rules are two names.
        """
        for later in self.headings:
            if later.lineno > heading.lineno and stops(later):
                return later.lineno - 1
        return len(self.lines)

    # -- the ownership test ------------------------------------------------

    @property
    def non_canonical(self) -> tuple[Entry, ...]:
        """Entries the schema would render differently from how they are written."""
        return tuple(e for e in self.entries if self.schema.render(e.task) != e.raw)

    def ensure_writable(self) -> None:
        offenders = self.non_canonical
        if offenders:
            raise RoundTripError(offenders, self.path)

    # -- writing (every mutator refuses first) -----------------------------

    def replace_line(self, index: int, raw: str) -> Document:
        self.ensure_writable()
        lines = list(self.lines)
        lines[index] = raw + ending(lines[index])
        return self._reparse(lines)

    def insert_line(self, index: int, raw: str) -> Document:
        """Insert before ``index``; ``len(lines)`` appends."""
        self.ensure_writable()
        lines = list(self.lines)
        # A file whose last line has no ending would otherwise get the new line
        # glued onto it — the exact corruption this module exists to prevent.
        if lines and index >= len(lines) and not ending(lines[-1]):
            lines[-1] += self.newline
        lines.insert(index, raw + self.newline)
        return self._reparse(lines)

    def remove_line(self, index: int) -> Document:
        return self.remove_lines(index, index + 1)

    def remove_lines(self, start: int, stop: int) -> Document:
        """Delete ``[start, stop)`` in one edit — validated once, re-parsed once (RK54).

        One edit and not a loop, because every intermediate state of a loop is validated as
        if it were the finished file: deleting a section whose prose quotes a fenced example
        removes the fence's opening line first, and the quoted task line inside it is then
        briefly outside any fence, parses, and refuses the rest of the deletion.
        """
        self.ensure_writable()
        lines = list(self.lines)
        del lines[start:stop]
        return self._reparse(lines)

    def replace_task(self, entry: Entry, task: Task) -> Document:
        """Re-render one entry from its data — the only way a task line changes.

        The **first** line, and deliberately not the span (RK157): every field the schema
        renders was read off that line, so rewriting it is lossless, while replacing the
        whole span with one rendered line would delete continuation lines whose text this
        task never held — somebody's paragraph, removed by a command that was asked to
        change an id. The span is what an insertion and a removal need; a rewrite needs the
        line it can actually reproduce.
        """
        return self.replace_line(entry.index, self.schema.render(task))

    def rewrite_entry(self, entry: Entry, task: Task) -> Document:
        """Re-render one entry over its **whole span**, collapsing a wrap to one line.

        The other half of :meth:`replace_task`'s split (RK179). That one is right where the
        rewrite cannot contradict the lines beneath it — an id, a marker — and wrong the
        moment the *sentence* changes, because a wrapped entry's `why` is only as much of
        the sentence as fits on the first line: rewriting that line alone leaves the tail of
        the old one underneath the new one, in an entry the command just called amended.

        So this one really does delete prose, which is why no caller reaches it without
        having said how many lines the write replaces. What goes is text no field of this
        task holds, and the only reader who can call it the old sentence's tail is the one
        who read it.
        """
        self.ensure_writable()
        lines = list(self.lines)
        # One edit and not a replace-then-delete, for `remove_lines`'s reason (RK54): each
        # intermediate state of a loop is validated as if it were the finished file. The
        # ending is the *last* line's, so a file that ends without one still does.
        lines[entry.index : entry.stop] = [
            self.schema.render(task) + ending(lines[entry.stop - 1])
        ]
        return self._reparse(lines)

    def assert_current(self, path: str | Path | None = None) -> None:
        """Refuse if the target is no longer the file this document was read from (RK116).

        The check `save` makes, callable on its own so a transaction that writes several
        files can ask about all of them before it writes any (RK6): a refusal raised
        halfway through leaves the state the all-or-nothing rule exists to prevent.

        Silent in the two cases where there is nothing to compare: a document parsed from a
        string, which never had disk state, and a save to a path other than the one it was
        read from, where the target is a different file and not a changed one.
        """
        target = Path(path) if path is not None else self.path
        if self.source is None or target is None or target != self.path:
            return
        if not target.is_file():
            raise StaleFile(target, missing=True)
        with target.open("r", encoding="utf-8", newline="") as handle:
            if handle.read() != self.source:
                raise StaleFile(target)

    def save(self, path: str | Path | None = None) -> Path:
        target = Path(path) if path is not None else self.path
        if target is None:
            raise ValueError("no path to save to")
        if target == self.path:
            # The one-document transaction, and not a shorter path around one: a write that
            # stales a derived block owes the refresh whether it touched one file or three
            # (RK188), and `save_all` is where that is stated once.
            save_all(self)
            return target
        self.ensure_writable()
        # Both halves of "may this file be rewritten": one the tool understood, and one
        # nobody else has touched since (RK116). Re-read and not stat'd — a modification
        # time is a second source of truth about the bytes, and the coarser one.
        self.assert_current(target)
        write_atomically(target, self.render())
        return target

    def _reparse(self, lines: list[str]) -> Document:
        # Reparse rather than patch the entry tuples: line numbers shift, and a
        # document that reports stale ones is worse than one that costs a reparse.
        parsed = Document.parse("".join(lines), schema=self.schema, path=self.path)
        # `source` survives the edit: it is what the file held when it was *read*, and an
        # edited document is exactly the one that needs to know that (RK116). So does
        # `config`, for the same reason — an edited document is the one about to be saved.
        return replace(parsed, path=self.path, source=self.source, config=self.config)


@lru_cache(maxsize=_PARSE_CACHE)
def _parsed(text: str, schema: Schema) -> Document:
    """One parse per distinct (bytes, schema), because a command reads a file more than once.

    Measured for RK211, on the write that motivated it: a `status` change parses the three
    counted roles through `Backlog.load`, and the projection RK188 put in the same
    transaction parses them again — 9.1 ms of Turing's 17.1 ms refresh, on a file the
    command had already read a millisecond earlier. `pick`, `budget` and `lint` each read
    the same file two or three ways for the same reason.

    Keyed by the **text**, so the bytes are still read from disk every single time. That is
    what makes it a memo rather than a cache: a file somebody else changed produces a
    different key and a fresh parse, so there is no state to invalidate and no window where
    this answers about a file that has moved (RK116's question is asked of the disk either
    way). What it costs is hashing the text — 0.1 ms on Turing's 800 KB ledger against the
    7.3 ms parse it skips.

    Small on purpose. The entries are immutable and shared, which is safe because every
    mutator returns a new document (L3), but a long-lived process — the MCP server — would
    otherwise hold every revision of a ledger it ever read.
    """
    return Document.parse(text, schema=schema)


def write_atomically(target: Path, text: str) -> None:
    """Replace a file's whole content in one step, so no reader ever sees half of it (RK118).

    `write_text` truncates the target and then fills it, and a reader arriving between those
    two moments does not get an old file or a new one — it gets a **shorter** file that
    parses, because every line still in it is a line the schema accepts. The roadmap simply
    has fewer tasks, and nothing about that is loud enough to notice.

    So the content is written to a temporary file in the target's **own directory** — same
    filesystem, or the rename would be a copy — and :func:`os.replace` puts it in place,
    which is one step on both platforms this runs on. What that buys is not an atomic
    transaction across the three files a `ship` writes: it is that every state a reader can
    catch is a *whole* file, which is the state the tool already knows how to read.

    The two halves are :func:`stage` and :func:`commit` because a transaction needs them
    apart (RK131); a single-file write is the pair called back to back.
    """
    scratch = stage(target, text)
    try:
        commit(scratch, target)
    finally:
        discard(scratch)


def stage(target: Path, text: str) -> Path:
    """Write the new content beside its target, under a name only this process uses.

    The target's **own directory**, or the rename that follows would be a copy across
    filesystems and no longer one step. Nothing about the target is touched here, which is
    what lets a transaction stage every file it writes before it commits any of them.
    """
    scratch = target.with_name(f".{target.name}.roadkeep-{os.getpid()}.tmp")
    scratch.write_text(text, encoding="utf-8", newline="")
    return scratch


def commit(scratch: Path, target: Path) -> None:
    """Put a staged file in place with :func:`os.replace`, which is one step on both platforms.

    The retry is Windows: a rename over a file another process has open can fail while an
    indexer or a virus scanner holds it for a moment. A failure that outlasts the retries is
    raised as the :class:`OSError` it is, and every writing command already refuses on one.
    """
    for remaining in reversed(range(_REPLACE_TRIES)):
        try:
            os.replace(scratch, target)
            return
        except PermissionError:
            if not remaining:
                raise
            time.sleep(_REPLACE_PAUSE)


def discard(scratch: Path) -> None:
    # The scratch file is this process's own and named after it, so removing it can never
    # take somebody else's — and a temporary file left behind by a failed write is litter
    # in a directory the tool asked to be trusted with.
    with contextlib.suppress(OSError):
        scratch.unlink()


@dataclass(frozen=True, slots=True)
class Write:
    """One file a transaction will replace, as :func:`write_all` needs it (RK187).

    Three things and no document: where the bytes go, what they are, and the question that
    still has to be true when they land. The third is a callable rather than a source
    string because what "unchanged" means is the caller's — a governed file compares the
    text it parsed (RK116), and a README this tool does not own compares the bytes it read
    (RK132), which is the same question asked of a file with no format to parse.
    """

    target: Path
    text: str
    #: Raises :class:`StaleFile` where the target stopped being the file that was read.
    assert_current: Callable[[], None]


def write_all(*writes: Write) -> tuple[Path, ...]:
    """Stage every file, ask every target, then rename in order (RK131, RK187, RK6).

    The obvious arrangement — ask every target first, then write each in turn — leaves the
    rendering and the writing of file *n-1* inside the window between the question and file
    *n*'s write, and a writer landing in it is refused on the second file after the first
    has already been written. That is the half-applied state the question was asked to
    prevent, made rarer rather than impossible.

    So the order is inverted: every file is rendered to its scratch name first, where it
    costs nothing and is visible to nobody, *then* every target is asked whether it is still
    the file that was read, and only then are the renames made. What is left between the
    question and the last write is the renames themselves — no rendering, no I/O on any
    source, nothing that can raise for a reason of its own — which is as close to one step
    as three files on a filesystem get.

    The argument order is the rename order, and every caller's ordering rationale is about
    which halfway state a crash leaves (see :meth:`shipping.Departure.save`).

    One function for the rule, because the two callers are two kinds of file and one
    guarantee: `ship` writes three documents it parsed, `export` splices two projections
    into files it does not own, and a second phrasing of "all or none" is a second thing to
    keep true.
    """
    staged: list[tuple[Path, Write]] = []
    try:
        for write in writes:
            staged.append((stage(write.target, write.text), write))
        for _, write in staged:
            write.assert_current()
        for scratch, write in staged:
            commit(scratch, write.target)
    finally:
        for scratch, _ in staged:
            discard(scratch)
    return tuple(write.target for _, write in staged)


def save_all(*documents: Document | None) -> tuple[Path, ...]:
    """:func:`write_all` for the files this tool parsed, plus what they derive (RK188).

    A None is skipped, because a transaction's optional file is absent and not stale.
    """
    writes: list[Write] = []
    for document in documents:
        if document is None:
            continue
        target = document.path
        if target is None:
            raise ValueError("no path to save to")
        # Before anything is staged: a document that would not round-trip is refused for
        # the whole transaction, not for the file it happened to be discovered on (L3).
        document.ensure_writable()
        writes.append(Write(target, document.render(), document.assert_current))
    # Derived last, so the rename order leaves the recoverable halfway state: a crash after
    # the governed files land is a block `lint` names and one command repairs, where the
    # reverse would be a README stating counts no file holds.
    return write_all(*writes, *_projected(documents))


def _projected(documents: Sequence[Document | None]) -> tuple[Write, ...]:
    """The derived blocks this transaction stales, refreshed *inside* it (RK188).

    Every governed write changes what a README or a landing page would render, and RK104
    put the gate over that block without giving any verb the job of writing it — so ten
    claims and ten ships each left this repository failing its own conformance run on a
    file the task never touched. The block is derived wholly from documents this call
    already holds, which makes it the same kind of thing as a dep annotation or a pointer:
    the write that invalidates it is the write that owes it.

    Imported inside the function because the dependency runs the other way — a projection
    reads documents, so `exporting` imports this module and a module-level import here
    would be a cycle. It belongs here anyway: this is where a transaction is assembled,
    and a refresh planned anywhere else would land outside `write_all`'s all-or-nothing
    rule (RK187), which is the one thing that keeps a half-refreshed pair impossible.
    """
    held = [document for document in documents if document is not None]
    config = next((document.config for document in held if document.config), None)
    if config is None:
        return ()
    from roadkeep.exporting import refreshes

    return refreshes(config, held)


def _spanned(entries: list[Entry], loose: set[int]) -> tuple[Entry, ...]:
    """Give every entry its end: the run of non-blank unparsed lines directly beneath it.

    The rule §RK157 names, and the reason it is the parser's to state rather than a writer's
    guess: an entry ends at the line before the next bullet, heading, table row or blank. A
    blank breaks the run because a paragraph one line down belongs to the block, not to the
    bullet above it — which is also what keeps a block's own introduction (RK108) out of the
    last entry of the block before it.
    """
    return tuple(
        replace(entry, last=_run(entry.lineno, loose)) for entry in entries
    )


def _run(lineno: int, loose: set[int]) -> int:
    last = lineno
    while last + 1 in loose:
        last += 1
    return last


def blank(line: str) -> bool:
    """A line with no content — what separates a heading from what belongs to it.

    Public because every writer has to reason about it: a task glued to a heading, or a
    doubled blank left where a line was removed, is a change to the file's shape that
    the round-trip cannot catch because both spellings round-trip.
    """
    return not line.strip()


def ending(line: str) -> str:
    """The line's own terminator, or empty at a file that ends without one.

    Public for the same reason as :func:`blank`: a writer that replaces a line has to put
    back the ending that line had, and a second implementation of this would be the one
    that turns a CRLF file into a mixed one on the first fix (RK16).
    """
    for candidate in ("\r\n", "\n", "\r"):
        if line.endswith(candidate):
            return candidate
    return ""


def _looks_like_marker(token: str, schema: Schema) -> bool:
    """Is this token *meant* to be a status marker?

    Deliberately looser than the schema: a marker followed by U+FE0F renders
    identically in an editor, so a line carrying one would otherwise be skipped in
    silence — invisible drift, uncounted and unreported. Read it instead, and let
    the round-trip refuse the write and lint name the character.
    """
    stripped = _bare(token)
    return any(
        token == marker or stripped == marker
        for marker in (*schema.markers, schema.shipped_marker)
    )


def _bare(token: str) -> str:
    """A marker token without the codepoints that render as nothing.

    One function because two tests read a marker off a line \u2014 is this one at all, and is it
    the departure a markerless ledger may carry (RK125) \u2014 and a second copy of the pair is a
    second answer to "does a trash marker with a variation selector count".
    """
    return token.rstrip("\ufe0f\u200d")  # variation selector, ZWJ


def _wears_the_marker_slot(rest: str, token: str) -> bool:
    """A bullet whose first token sits where a marker sits and is not one.

    The silent miss :mod:`roadkeep.counting` exists to end: a line written with a
    marker this project does not declare — a ✨ from another repository's set, a ✅
    in the roadmap — matches no marker, so it is read as prose and disappears from
    every count without being rejected either.

    The token must carry no letter or digit, which is what separates it from prose:
    ``- See **RK5** for the design.`` also puts a bold id second, and reporting it
    would make the audit the noise its own symptom names.
    """
    return bool(token) and not any(c.isalnum() for c in token) and bool(
        _MARKER_SLOT_RE.match(rest)
    )


def _retirement(token: str, schema: Schema) -> bool:
    """The one marker a line in a markerless ledger may carry: a departure (RK125).

    Asked of :meth:`Schema.marks`, so the grammar and the renderer cannot disagree about
    which line writes the slot — the parser reads a marker exactly where `render` would put
    one, which is what keeps the round-trip (L3) an identity rather than a hope.

    Tolerant of the variation selector for the same reason :func:`_looks_like_marker` is: a
    🗑️ renders identically in an editor, so reading it as prose would hide the line from
    every count instead of letting `lint --fix` name the codepoint.
    """
    if schema.marker_field or not schema.marks(schema.retired_marker):
        return False
    return schema.retired_marker in (token, _bare(token))


def _leads_with_the_id(rest: str) -> bool:
    """A bullet whose first token *is* the bold id: the slot is empty, not wrong (RK43).

    The wider half of the same silent miss, and the one that was measured: Shio's
    changelog is 920 bullets, and it parsed as **0 entries and 0 rejects** — every line
    writes ``- **SH125** — …`` with no marker at all, so none of them wears the slot
    wrongly, they leave it out, and :func:`_wears_the_marker_slot` declines them because
    the first token carries alphanumerics. Turing's writes 755 of the same.

    Id-shaped and nothing after the bold, which is what keeps this off prose that also
    leads with bold: ``- **Delete** the 3 old files`` carries no digit and
    ``- **SH239**: a benchmark …`` puts a colon where the grammar has a space.
    """
    return bool(_BOLD_ID_RE.match(rest))


def checkbox(rest: str) -> str | None:
    """The task-list checkbox this bullet puts where the status goes, or None (RK103).

    ``- [ ] **C40** · …`` is GitHub's task-list syntax, which is what a Markdown backlog
    looks like when nobody chose a format — and it was the last shape read as prose by
    everything. The first whitespace-delimited token is ``[`` and never ``[ ]``, so it
    matches no marker; :func:`_wears_the_marker_slot` wants the bold id second and this
    puts it third; :func:`_leads_with_the_id` wants the bullet to open with the bold.
    Measured on cursarei: 16 such lines, **0 entries and 0 rejects**, the silent miss the
    reject list exists to end, one shape further out than Shio's 920.

    A reject and not a reading, and not `[markers]` either: the slot is one token by
    construction, so declaring ``[ ]`` would widen it to two and make every two-word prose
    bullet a candidate. The bold id after the box is what keeps this off a prose checklist,
    and ``[x]`` is here beside ``[ ]`` because a checked box is the same convention and was
    missed by the same three tests.

    Public because :mod:`roadkeep.adopting` reads it: a box is not a marker anybody has to
    declare, so the `[markers]` delta an estimate prints has to leave this one out.
    """
    match = _CHECKBOX_RE.match(rest)
    return match.group("box") if match else None


def _marker_slot(rest: str, token: str, schema: Schema) -> tuple[bool, str | None]:
    """Whether this bullet claims a task line's shape, and the reason if its slot is not.

    A pair because there are three answers and skipping is one of them: ``(False, None)``
    is prose, ``(True, None)`` is a line to go on parsing, and ``(False, reason)`` is a
    claim whose marker slot is wrong — which is the only one that becomes a
    :class:`Reject`, because rejecting prose is what makes a report unread.

    Which slot is right is a fact about the file, not the format (RK43): where the ledger
    declares no marker the slot is absent, so a bold id leads and a marker is the error.
    A checkbox is judged before either, because it is another convention's whole line and
    is one whether this file's slot holds a marker or nothing (RK103).
    """
    box = checkbox(rest)
    if box is not None:
        return False, (
            f"{box} is a task-list checkbox where the status goes: the line is a task in "
            f"another convention, so it reads as prose and no count sees it"
        )
    if not schema.marker_field:
        if _retirement(token, schema):
            # The one line such a file writes a marker on (RK125): a departure is the status
            # the file does not state about itself, so the line has to.
            return True, None
        if _looks_like_marker(token, schema):
            return False, (
                f"{token} is a status marker, in a file whose lines carry none "
                f"([ledger] marker = false): there the marker is the file's, not the "
                f"line's — {schema.retired_marker} alone carries one, a departure not "
                f"being a shipment"
            )
        return _leads_with_the_id(rest), None
    if _looks_like_marker(token, schema):
        return True, None
    if _wears_the_marker_slot(rest, token):
        declared = " ".join((*schema.markers, schema.shipped_marker))
        return False, (
            f"{token} is not a marker this project declares ({declared}): the line "
            f"reads as prose and no count sees it"
        )
    if _leads_with_the_id(rest):
        # The id is deliberately left out of the reason: a `Reject` already carries the
        # line number, and 755 reasons differing only by an id group into 755 rows of one,
        # which is the report `adopt` (RK18) prints instead of a number worth reading.
        reason = (
            "no marker where the status goes: the slot is empty, so the line reads as "
            "prose and no count sees it"
        )
        if schema.is_ledger:
            # The declaration(s) that make these into entries. Said here because this reason
            # is the only place a reader of that file will be looking — and **both** slots are
            # named where both are needed (RK286): Turing's ledger was told `marker = false`
            # alone, and taking exactly that advice left `827 would change` unmoved because
            # its lines carry no symptom slot either. Which of the two shapes the line lacks
            # is a fact this pass has, so it is stated rather than guessed at by the reader.
            reason += f" — a ledger of these lines declares {_ledger_slots(rest)}"
        return False, reason
    return False, None


#: The four shapes a ledger line can be declared into, and the `[ledger]` slots each gives up.
#: Ordered by how much they give up, so the first that reads a line is the smallest that does.
LEDGER_SHAPES: tuple[tuple[bool, bool, tuple[str, ...]], ...] = (
    (True, True, ()),
    (False, True, ("marker = false",)),
    (True, False, ("symptom = false",)),
    (False, False, ("marker = false", "symptom = false")),
)


def reads_as_entry(line: str, marker: bool, symptom: bool) -> bool:
    """Whether this line is a task line under a `[ledger]` declared with these two slots.

    The shape test on its own, so an estimate can ask what a *whole* declaration would read
    (RK286) rather than adding up what each line separately wants — the two slots are not
    independent, and a project declares one `[ledger]`.
    """
    return _task_re(marker, symptom).match(line) is not None


def ledger_slots(line: str) -> tuple[str, ...]:
    """Which `[ledger]` slots this line needs declared before it parses (RK286).

    Asked of the line and never assumed: `- **T1** — because.` needs `marker = false` alone,
    `- **T1** because.` needs `symptom = false` as well, and `- ✅ **T1** because.` needs only
    `symptom = false`. Naming one where two are wanted is advice that does not survive being
    taken — measured on Turing, where declaring exactly what the reason said left the count
    where it was.

    The **fewest** slots that read it, so the declaration reported is the smallest one that
    works: each shape is tried in order of how much it gives up. Empty when none reads the
    line, which is a line no declaration reaches and so is not evidence about one.
    """
    for marker, symptom, slots in LEDGER_SHAPES:
        if reads_as_entry(line, marker, symptom):
            return slots
    return ()


def _ledger_slots(rest: str) -> str:
    """:func:`ledger_slots` as the reject reason spells it, from the bullet's body."""
    slots = ledger_slots(f"- {rest}")
    if not slots:
        return "no [ledger] shape this line reads under"
    return "[ledger] " + ", ".join(slots)


def _fenced(open_marks: str | None, marks: str) -> str | None:
    """The fence still open after this delimiter line, or None (RK53).

    A fence is closed only by its own character and at least as many of them, so ``` inside
    a ~~~ block is text — which is how a renderer reads it, and the only way a section that
    quotes one fence inside another can be read at all.
    """
    if open_marks is None:
        return marks
    if marks[0] == open_marks[0] and len(marks) >= len(open_marks):
        return None
    return open_marks


def _tables(pipes: Sequence[Row]) -> tuple[Row, ...]:
    """The data rows of every table in the file, from the pipe lines it collected (RK98).

    Split into runs of adjacent lines first, because two tables in one file are two
    questions about where the rule row is, and a run interrupted by prose is two runs.
    """
    out: list[Row] = []
    run: list[Row] = []
    for row in pipes:
        if run and row.lineno != run[-1].lineno + 1:
            out += _below_the_rule(run)
            run = []
        run.append(row)
    out += _below_the_rule(run)
    return tuple(out)


def _below_the_rule(run: Sequence[Row]) -> list[Row]:
    """One run's task rows: what sits under the `|---|`, filed under a block.

    Two filters, and each drops a whole class of false report. **Without a rule row** a run
    of pipes is prose that uses them — a leading `|` is not a table, and counting one would
    make this report name itself. **Outside a block** a table is documentation: the legend
    in a roadmap's preamble is not 6 tasks, and a heading is the only thing that says a line
    is filed work (RK37).
    """
    for index, row in enumerate(run):
        if _RULE_RE.match(row.raw):
            return [below for below in run[index + 1 :] if below.block]
    return []


def _block_label(text: str, schema: Schema) -> str | None:
    """The label a heading declares, under this project's own word (RK75).

    Read from the schema and not from a constant here, so the heading and the dep that
    names it cannot disagree about either the word or the label's shape.
    """
    match = schema.heading_pattern().match(text)
    return match.group("label") if match else None


def _split_ref(body: str) -> tuple[str, str | None]:
    """Take the pointer off the end, last occurrence first.

    Matching the pointer with a regex over the whole line would find the one
    RK15's own `why` quotes as an example and truncate the sentence at it.
    """
    head, sep, tail = body.rpartition(_POINTER)
    if sep and tail and not any(c.isspace() for c in tail):
        return head, tail
    return body, None


def _read_bullet(body: str, schema: Schema, block: str) -> Task | str | None:
    """A task, a reason it was rejected, or None when the line is not a task at all.

    Only a bullet that claims the task line's own shape can be rejected: every other one
    is prose, and reporting the non-goals list as malformed would make the report
    worthless. Which shape that is depends on the file — in a markerless ledger (RK43)
    the claim is a leading bold id, and a marker there is the mistake instead, 🗑 excepted
    (RK125).

    So whether *this line* fills the marker slot is a question per line and not per file:
    the grammar is chosen from the same answer `render` writes from, which is what keeps
    the retirement a markerless ledger carries byte-identical through the round trip.
    """
    bullet = _BULLET_RE.match(body)
    if not bullet:
        return None
    rest = bullet.group("rest").lstrip()
    token = rest.split(" ", 1)[0]
    marked = schema.marker_field or _retirement(token, schema)
    claimed, wrong = _marker_slot(rest, token, schema)
    if wrong is not None:
        return wrong
    if not claimed:
        return None
    indent = bullet.group("indent")
    if not body.lstrip().startswith("- "):
        return "bullet must be '- ': a task line is one dash and one space"

    # Judged exactly as it would be at column zero (RK49), and the indentation is carried
    # on the task so `render` puts it back: Shio nests four live tasks under a shipped
    # parent, and rejecting them made 4 ids invisible to every count and to `next-id`.
    head, ref = _split_ref(body[len(indent) :])
    match = _task_re(marked, schema.symptom_field).match(head)
    if not match:
        return _diagnose(head, schema, marked)

    raw_deps = match.group("deps")
    if schema.deps_field and raw_deps is None:
        return "no (deps: …) field"
    if not schema.deps_field and raw_deps is not None:
        return "a deps field, in a file that carries none"

    deps: tuple[Dep, ...] = ()
    if raw_deps is not None and raw_deps != NO_DEPS:
        deps = read_deps(raw_deps, schema)

    return Task(
        id=match.group("id"),
        # The qualifier a partial entry carries (RK121). Read wherever the grammar finds
        # one and refused by the schema where it is not legal, which is the split every
        # other slot takes: the parser's job is to lose nothing, the schema's is to judge.
        part=match.group("part"),
        # Where the file declares no marker, the status is the file's own: every entry in
        # a ledger that carries none shipped, which is the whole content of the claim.
        status=match.group("status") if marked else schema.shipped_marker,
        block=block,
        # Absent where the file has no such slot (RK48): the whole tail is the `why`, and
        # an empty string is what `render` then reproduces by omitting the bold entirely.
        symptom=match.group("symptom") if schema.symptom_field else "",
        why=match.group("why"),
        deps=deps,
        ref=ref,
        indent=indent,
    )


def read_deps(raw: str, schema: Schema) -> tuple[Dep, ...]:
    """Split the field; never reject the line over it.

    Public because `add` (RK5) reads the deps an author types with the same code that
    reads the ones already in the file — a `(deps: …)` field the writer and the reader
    parse differently is a field that stops round-tripping on the next write.

    A dep token the schema will not accept — Shio's ``Block P``, Turing's ``real
    design partners`` — still round-trips, so it is read as an id and reported by
    `lint` as `deps.format`. Rejecting the whole line instead would drop an
    otherwise perfect task out of every count, which is the silent-miss failure
    the reject list exists to prevent.
    """
    markers = schema.dep_markers
    out: list[Dep] = []
    for token in raw.split(", "):
        head, _, last = token.rpartition(" ")
        if head and last in markers:
            out.append(Dep(head, marker=last))
        else:
            out.append(Dep(token))
    return tuple(out)


def _diagnose(head: str, schema: Schema, marked: bool) -> str:
    """Name the missing piece. A reason is what makes a reject actionable.

    ``marked`` is whether *this line* filled the marker slot rather than whether the file's
    lines do, so a retirement in a markerless ledger (RK125) is told where the id is missing
    from and not sent to look at the start of a line that begins with 🗑.
    """
    if not re.search(r"\*\*[A-Za-z0-9]+\*\*", head):
        where = "after the marker" if marked else "where the line starts"
        return f"no bold **<id>** {where}"
    if schema.deps_field and "(deps:" not in head:
        return "no (deps: …) field"
    if not schema.deps_field and "(deps:" in head:
        return "a deps field, in a file that carries none"
    if f" {EM_DASH} " not in head:
        return f"no ' {EM_DASH} ' between the symptom and the why"
    if head.count("**") < 4:
        return "symptom is not delimited by **"
    return "does not match the task-line grammar"
