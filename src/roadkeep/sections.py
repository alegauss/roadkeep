"""Prose files have a different unit, so they get a different schema (RK9).

Three of the four governed files are lines; two are paragraphs. A rationale or a strategy
is prose under a heading, and applying the line schema to it would be the wrong law
twice over: there is no `symptom` to bound and no 320-character cap that means anything
about a paragraph. What a section *does* have is:

* **an anchor**, which is the whole reason the pointer on a task line resolves (RK27) —
  so `§RK9` must name an open task, and a typo names nothing at all. Read **per scheme**
  (RK44): `id` requires the § that tells an id from a word, while an outline numbers its
  own headings and puts the sigil on the pointer alone, so reading one spelling into the
  other turned Shio's 151 headings into 0 sections and 74 pointers into 74 dangling ones;
* **a word budget**, because the failure mode measured here was a rationale file reaching
  539 KB one honest paragraph at a time — a limit in words is the one an author can act
  on before writing, which is the same argument as `add`'s (L1);
* **a place**, which is derived twice over: a section for a task belongs under that task's
  block, and a section for no task belongs under the section its anchor extends (RK45) —
  §0.4 after §0.3, §RK34.1 inside §RK34. So the file's shape is a consequence of the
  backlog's and of the outline's, and nobody chooses where to type.

`amend` is the door that was missing (RK123). Three correct refusals — `drop` while a live
pointer names the anchor, `add` on the duplicate, and the guard on the hand edit — added up
to a rationale that could not be corrected at all while its task was open, which is exactly
when a design changes. It rewrites the heading text and the section's **own** prose, never
the subtree and never the anchor: a subsection has an anchor of its own to be named by, and
an address is `renumber`'s.

`drop` is the operation `ship` (RK6) calls for rule one of its three edits — it lives here
rather than there because deleting a section is a fact about this file's grammar, not
about shipping, and the two would otherwise disagree about where a section ends. It takes
the **whole subtree**, and is refused before it writes when that subtree holds a section
some other open line points at (RK78): a heading nested under another is that other's
prose, right up until a second pointer names it, and then deleting it is a deletion the
transaction never named — measured on Shio, 160 lines removed by a command that reported
dropping one section, leaving two live pointers resolving to nothing.

Reflow is deliberately narrow. A plain paragraph is filled to the configured width, and
anything carrying a Markdown structure — a table, a list, a quote, a fence — is inserted
exactly as written: the tool re-flows prose, and never reformats a shape it did not
author. That is the same line L4 draws, one file down.
"""

from __future__ import annotations

import re
import textwrap
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace

from roadkeep.config import Config
from roadkeep.document import Document, Heading, UnknownBlock, blank
from roadkeep.schema import (
    OUTLINE_ANCHOR_RE,
    Schema,
    SchemaError,
    Task,
    Violation,
    over_by,
)

#: A paragraph whose first characters are any of these is a structure, not prose.
_STRUCTURE = ("|", ">", "-", "*", "+", "#", "```", "~~~", "1.")
#: What opens a block whose contents are quoted or generated rather than written (RK136).
_FENCES = ("```", "~~~")
#: A line that is data rather than argument, so the budget does not charge for it. A list
#: marker is deliberately absent: a bullet is how an argument is written in these files.
_DATA = ("|", ">")


class SectionError(SchemaError):
    """A section the schema refuses, carrying every violation, not the first.

    A :class:`~roadkeep.schema.SchemaError` because it is the same law one file down —
    which also means every caller that already reports violations reports these.
    """


class NoSuchSection(ValueError):
    """An anchor nothing in this file declares."""

    def __init__(self, anchor: str, where: str = "") -> None:
        self.anchor = anchor
        super().__init__(f"no §{anchor} section in {where or 'the document'}")


class SectionExists(ValueError):
    """One anchor, one section: two would make the pointer ambiguous."""

    def __init__(self, anchor: str, where: str, lineno: int) -> None:
        self.anchor = anchor
        self.lineno = lineno
        super().__init__(
            f"§{anchor} is already at {where}:{lineno}: an anchor names one section, "
            f"and a pointer that resolves to two resolves to neither"
        )


class SectionOccupied(ValueError):
    """A drop whose subtree holds prose another open line owns (RK78).

    The counterpart, one level down, of the multi-owner check `ship` already makes about the
    anchor it was given: that one asks who else points *here*, and this one asks who else
    points at anything **nested** here. Both refuse rather than repair, because a drop is
    contiguous — a subtree with a stranger in the middle has no partial deletion that is not
    a decision about someone else's prose — and the author's remedy is to lift the section
    out or to ship the line that claims it.

    Refused *before* the write and not reported after, which is the whole difference this
    closes: `lint` named the damage as two `ref.unresolved` immediately afterwards, by which
    point the only remedy was `git checkout` on the file, discarding the part of the ship
    that was correct along with the part that was not (L1, one verb along from `add`).
    """

    def __init__(
        self, anchor: str, occupied: Sequence[tuple[str, Sequence[str]]], where: str = ""
    ) -> None:
        self.anchor = anchor
        self.occupied = tuple((child, tuple(owners)) for child, owners in occupied)
        named = ", ".join(
            f"§{child} ({', '.join(owners)})" for child, owners in self.occupied
        )
        file = f" in {where}" if where else ""
        super().__init__(
            f"§{anchor}{file} nests {len(self.occupied)} section(s) another open line "
            f"points at: {named} — dropping it deletes prose this transaction never "
            f"named, and leaves those pointers resolving to nothing"
        )


class SectionClaimed(ValueError):
    """A drop of the section an open line points at, refused before the write (RK112).

    :class:`SectionOccupied` one level up, and the level that was missing: that one asks who
    points at anything *nested* under the anchor, `ship` asks who else points *at* it — and
    `section drop`, the verb whose whole job is removing one section, asked neither. Found by
    using the tool: `section drop VIII.11` succeeded on a section stale by every other
    measure, and the next `lint` reported `ref.unresolved` for an open line that owned it.

    A refusal and not a report, because the drop was one of seven in a triage pass: `lint`
    names the damage afterwards, and by then `git checkout` discards the six that were right
    along with the one that was not. `ship` still drops its own task's section — that caller
    passes ``leaving``, so the claim that is the reason for the drop is not one of these.
    """

    def __init__(self, anchor: str, owners: Sequence[str], where: str = "") -> None:
        self.anchor = anchor
        self.owners = tuple(owners)
        file = f" in {where}" if where else ""
        super().__init__(
            f"§{anchor}{file} is pointed at by {', '.join(self.owners)} — dropping it "
            f"leaves {'that pointer' if len(self.owners) == 1 else 'those pointers'} "
            f"resolving to nothing: repoint the line, or ship the one that claims it"
        )


class AnchorClaimed(ValueError):
    """A drop whose anchor an open line's pointer descends from, by name (RK169).

    :class:`SectionOccupied` decides ownership by walking the *sections* inside the span, and
    a section is a **heading**. Measured adopting Turing: `section drop XIV` was accepted and
    took `§XIV.8` with it, and under that heading sat
    `- **XIV.8.7 — ship Cloud default config as a GLOBAL seed ZIP (T373).**` — the design of
    an open task, deleted without a word, because a bullet is not a section and the subtree
    looked unowned.

    Two things were true there and only one of them was a defect. That T373's pointer did not
    resolve is Turing's, and `lint` says so. That the verb whose whole job is *the orphan*
    deleted a live design **because** the pointer was already broken is this tool's: the
    finding made the content invisible to the guard that would have protected it, so two
    reports compounded into data loss.

    So the guard reads the **name** and not the shape. An address under the anchor is claimed
    prose whether the corpus writes it as a heading, as a bullet or as a table row — which
    needs no parsing of the prose at all, and is exactly the check the adoption script had to
    write by hand before it could proceed safely.
    """

    def __init__(
        self, anchor: str, claimed: Sequence[tuple[str, Sequence[str]]], where: str = ""
    ) -> None:
        self.anchor = anchor
        self.claimed = tuple((ref, tuple(owners)) for ref, owners in claimed)
        named = ", ".join(f"§{ref} ({', '.join(owners)})" for ref, owners in self.claimed)
        file = f" in {where}" if where else ""
        super().__init__(
            f"§{anchor}{file} is above {named}, which an open line points at: a drop takes "
            f"everything under the anchor, and an address under it is claimed prose whether "
            f"this file writes it as a heading or as a bullet — repoint the line, or ship "
            f"the one that claims it"
        )


class UnknownParent(ValueError):
    """An anchor states its place, and this file declares nothing it extends (RK45).

    The counterpart of :class:`~roadkeep.document.UnknownBlock`, for prose that belongs to
    no task: a §0.4 appended after the last block reads as that block's rationale, which is
    the mistake this module already refuses one case over. So everything under the top level
    is derived, and a **nested** anchor whose parent is missing stays a refusal — that is a
    typo in an address, and appending it would file somebody's paragraph under a design it
    does not extend.

    What is no longer refused is the **top level itself** (RK166). "A heading that is merely
    missing is a heading they can add" was this class's own argument, and the guard denies
    exactly that edit — RK141's deadlock, one file over: `block add` skips a prose file
    organised by an outline rather than by blocks, so a newly declared block's first section
    was reachable by nothing at all. A top-level anchor under an outline is now placed after
    the last top-level section, which is the same derivation this file already makes one
    level down.
    """

    def __init__(self, anchor: str, declared: Sequence[str], where: str = "") -> None:
        self.anchor = anchor
        self.declared = tuple(declared)
        known = ", ".join(f"§{a}" for a in self.declared) or "none"
        file = f"{where} " if where else ""
        super().__init__(
            f"no section §{anchor} extends ({file}declares: {known}): an anchor states "
            f"its own place, and appending files the prose under the last block"
        )


@dataclass(frozen=True, slots=True)
class Section:
    """A heading, its prose, and the lines it occupies. ``last`` includes the blank."""

    anchor: str
    title: str
    level: int
    first: int  # 1-based, as an editor counts
    last: int
    body: str = ""

    @property
    def words(self) -> int:
        """What the budget charges this section: its argument, not its whole text (RK136)."""
        return words(self.body)

    def names(self, pattern: re.Pattern[str]) -> tuple[str, ...]:
        """The task ids this heading names, in order (RK61).

        Whose section this is, for a project that numbers by hand: under
        `ref_scheme = "outline"` the anchor is `XVI.12` and the id lives in the title —
        `§XVI.12 A design (SH123)` — so ownership is unreadable from the anchor alone, and
        both `section.orphan` and `section.stale` fired for nobody in the two live corpora.

        The **title** and never the body: a section quoting another id is discussing it, not
        owning it, and reading the prose would report every cross-reference in the file.
        """
        return tuple(dict.fromkeys(pattern.findall(self.title)))

    def __str__(self) -> str:
        return f"§{self.anchor} ({self.first}-{self.last})"


def find(document: Document, anchor: str) -> Section | None:
    """The section this anchor names, or None. Subsections belong to it, not after it."""
    span = _span(document, anchor)
    if span is None:
        return None
    _, end, heading = span
    body = "".join(document.lines[heading.lineno : end]).strip("\r\n")
    return Section(
        anchor=anchor,
        title=_title_of(heading.text, document.schema),
        level=heading.level,
        first=heading.lineno,
        last=end,
        body=body,
    )


def citing(
    document: Document, anchors: Sequence[str], *, ignore: Sequence[str] = ()
) -> tuple[tuple[str, str], ...]:
    """Which sections' prose cites which of ``anchors`` — the other end of a pointer (RK206).

    `_pointers` resolves the ref a *task line* carries, and nothing resolves the references
    a section's prose makes, so `ship` deletes a design that another design cites and every
    check answers clean: `ref.unresolved` reads task lines, `section.orphan` reads what
    points at a section, and citing prose is neither. Measured on claude-tray: `§XVIII.9`
    cited `§XVIII.12`, `ship` took §XVIII.12 with the line that owned it, and `lint`
    reported `clean` for a day.

    **Membership and not shape.** The caller names the anchors that are going away, so an
    anchor-shaped token is interesting only when it is one of them — which removes RK15's
    quotation problem from the pattern entirely: `§RK15` in a sentence about pointers is
    text nobody is deleting. What is left of that problem is prose that quotes a reference
    to a section this very transaction removes, and three exclusions answer it, each
    measured across four trees rather than guessed:

    * a **fenced block** is quoted or generated (the reading :data:`_FENCES` already makes);
    * an **inline code span**, which is how this repository writes a pointer it is talking
      about — 3 of them in `docs/IMPROVEMENTS.md`;
    * a **blockquote**, which is 18 of Shio's anchor-shaped tokens and 19 of Turing's, all
      of them quoted material;
    * a token directly after a **`→`**, which is a task line reproduced as an example — 3 in
      claude-tray, and the shape `Schema.render` writes.

    ``ignore`` is what the transaction is deleting: a section citing its own subtree, or a
    sibling going in the same drop, is prose that leaves with the reference.
    """
    wanted = {anchor for anchor in anchors if anchor}
    if not wanted:
        return ()
    skipped = set(ignore)
    pattern = re.compile(
        r"§(" + "|".join(sorted(map(re.escape, wanted), key=len, reverse=True)) + r")(?![\w.])"
    )
    out: list[tuple[str, str]] = []
    for section in anchored(document):
        if section.anchor in skipped:
            continue
        for found in dict.fromkeys(pattern.findall(_argument(section.body))):
            out.append((found, section.anchor))
    return tuple(out)


def _argument(body: str) -> str:
    """A section's prose with every quotation blanked out, so a reference in one is not one.

    Blanked rather than dropped: the lines keep their positions, which is what lets a caller
    report a place without the two readings of the file disagreeing about which line it is.
    """
    out: list[str] = []
    fence: str | None = None
    for line in body.splitlines():
        stripped = line.strip()
        if fence is not None:
            if stripped.startswith(fence):
                fence = None
            out.append("")
            continue
        if stripped.startswith(_FENCES):
            fence = stripped[:3]
            out.append("")
            continue
        if stripped.startswith(">"):
            out.append("")
            continue
        out.append(_QUOTED.sub(lambda m: " " * len(m.group()), line))
    return "\n".join(out)


#: What is being talked about rather than said: a code span, and a pointer reproduced whole.
_QUOTED = re.compile(r"`[^`]*`|→\s*§[\w.]+")


def anchored(document: Document) -> tuple[Section, ...]:
    """Every `§<anchor>` section in file order, each carrying only its **own** prose.

    The gate (RK15) needs the set and not one lookup: a pointer resolves in one
    direction, and an orphan — a section nothing points at — is only visible from the
    other. **Own** prose, because :func:`find` deliberately returns the subtree (`drop`
    has to delete it whole, and a task's rationale is charged for the subsection it
    grew), and a container like this repository's `§0` has no prose of its own at all —
    counting its children against it would measure the file's shape rather than anyone's
    paragraph. Which of the two the budget uses is the gate's decision, not this one's.
    """
    out: list[Section] = []
    for heading in document.headings:
        anchor = _anchor_of(heading.text, document.schema)
        if anchor is None:
            continue
        end = document.prose_end(heading)
        out.append(
            Section(
                anchor=anchor,
                title=_title_of(heading.text, document.schema),
                level=heading.level,
                first=heading.lineno,
                last=end,
                body="".join(document.lines[heading.lineno : end]).strip("\r\n"),
            )
        )
    return tuple(out)


def nested(document: Document, anchor: str) -> tuple[Section, ...]:
    """The anchored sections a drop of this one would take with it, in file order (RK78).

    What :func:`find` returns as one body, enumerated as the headings it actually is — the
    honest report of a deletion whose size is not the size of the section that was named.
    Empty for an anchor this file does not declare, because "nothing is nested under a
    section that is not there" is the same answer as the refusal :func:`drop` raises, and
    a reader asking this question is not the one to tell about the missing heading.
    """
    span = _span(document, anchor)
    if span is None:
        return ()
    _, end, heading = span
    return tuple(
        section for section in anchored(document) if heading.lineno < section.first <= end
    )


def pointers(config: Config, *, leaving: str = "") -> dict[str, tuple[str, ...]]:
    """Which open lines point at which anchor — the claims a drop may not orphan (RK78).

    Read from the roadmap and never from the prose file, because a claim is a pointer and a
    pointer only exists on a task line: a heading nested under another is that other's prose
    until a line names it, and this is the one place that says which ones do. `leaving` is
    the line being shipped, whose own claim is the reason the drop is happening.
    """
    out: dict[str, list[str]] = {}
    for entry in config.document("roadmap").entries:
        if entry.task.ref and entry.task.id != leaving:
            out.setdefault(entry.task.ref, []).append(entry.task.id)
    return {anchor: tuple(ids) for anchor, ids in out.items()}


def drop(
    document: Document,
    anchor: str,
    *,
    claimed: Mapping[str, Sequence[str]] | None = None,
    where: str = "",
) -> tuple[Document, Section, tuple[str, ...]]:
    """Delete the section whole — subsections included — and report what went, and who is
    left citing it.

    A subsection left behind is orphaned prose under the *next* task's heading, which
    reads as that task's design and is the one outcome worse than deleting too much.

    Unless one of them is not this section's at all. `claimed` is :func:`pointers`' answer,
    and a nested anchor in it stops the whole write with :class:`SectionOccupied` (RK78) —
    the deletion is bounded by ownership rather than by depth, so a level-2 grouping four
    level-3 designs is refused while a task's own `§RK34.1` still goes with `§RK34`. Omitted,
    nothing is claimed: a caller with no roadmap to read cannot be told about a pointer, and
    both callers that have one pass it.

    The anchor that was **named** is asked first and answered the same way (RK112). It is the
    obvious half and it was the missing one: `ship` made that check on its own path and the
    standalone verb inherited nothing, so the one command that exists to delete a section was
    the one that could strand a live pointer.

    ``where`` is the file as the report spells it, rendered by the caller and passed in the
    way ``claimed`` is (RK181): this function takes a :class:`Document` and not a
    :class:`Config`, so `config.relative` — the one function that renders an address — is out
    of its reach, and building the string here from ``document.path`` is what printed an
    absolute path beside a `lint` naming the same file as `IMPROVEMENTS.md:5`.

    The **third** answer is who cited what just went (RK206, RK209), and it is returned
    rather than left to the callers for this module's own reason: what a deletion breaks is
    a fact about this file's grammar, the same argument that puts `drop` here instead of in
    `shipping`. It arrived through the departure path first, so `ship` and `retire` named it
    and the one verb whose whole job is deleting a section stayed silent — and every refusal
    above reads a *pointer*, which is the end of the reference that was already read.

    Reported and never refused, unlike everything above it. Those refuse because a pointer is
    a promise the format makes: a line says `→ §<anchor>` and the anchor has to be there. A
    citation in prose is a sentence, and a sentence that has to be re-worded is an edit and
    not a transaction to abandon. Computed **before** the removal, because afterwards the
    prose is the only end of the reference still in the file.
    """
    span = _span(document, anchor)
    section = find(document, anchor)
    if span is None or section is None:
        raise NoSuchSection(anchor, where)
    if claimed:
        owners = claimed.get(anchor)
        if owners:
            raise SectionClaimed(anchor, owners, where)
        occupied = [
            (child.anchor, claimed[child.anchor])
            for child in nested(document, anchor)
            if child.anchor in claimed
        ]
        if occupied:
            raise SectionOccupied(anchor, occupied, where)
        # And the same question asked of the **name** rather than of the headings (RK169),
        # which is the half a corpus addressing its prose as bullets fell through: the check
        # above proves containment and misses everything that is not a heading, and this one
        # proves nothing about the file and misses nothing an open line has claimed.
        descended = _descended(anchor, claimed)
        if descended:
            raise AnchorClaimed(anchor, descended, where)
    leaving = (anchor, *(child.anchor for child in nested(document, anchor)))
    cited = tuple(dict.fromkeys(by for _, by in citing(document, leaving, ignore=leaving)))
    start, end, _ = span
    # One edit, not one per line (RK54): a loop validates every half-deleted state, and a
    # section quoting a fenced example is briefly a file whose fence has no opening line.
    return document.remove_lines(start, end), section, cited


def add(
    config: Config,
    role: str,
    anchor: str,
    title: str,
    body: str,
    *,
    level: int | None = None,
    task: Task | None = None,
) -> tuple[Document, Section]:
    """Place one section under its block or its anchor, reflowed. Validates first.

    Returns the document unsaved, so a caller mid-transaction (`ship`, `init`) decides
    when the file is touched.

    ``level`` is **derived** where the caller names none (RK166), and it has to be: a
    top-level section written at the depth a subsection uses is not a top-level section at
    all — it lands inside the previous one's subtree, where every reader that asks a heading
    where it ends would find it. So the depth of a new top level is read off the file's own
    existing top level, the way `block add` reads a heading's level off the first block
    heading, and a subsection keeps the depth every caller already got.

    `task` is the line this anchor names, for the one caller holding a line the roadmap
    does not carry yet: `add --section` (RK93) validates both files before writing either,
    so its owner cannot be read back off disk — and read off disk it would be absent,
    which is `anchor.unknown`, a refusal about a line that is one save away. Omitted, the
    owner is read from the roadmap, which is every other caller.
    """
    document = config.document(role)
    where = config.relative(config.path(role))
    if task is None:
        task = _task_for(config, anchor)
    _check(document.schema, anchor, title, body, task)
    existing = find(document, anchor)
    if existing is not None:
        raise SectionExists(anchor, where, existing.first)

    lines = _render(document.schema, anchor, title, body, _depth(document, anchor, level))
    index = _placement(document, anchor, task, where)
    payload = list(lines)
    if index > 0 and not blank(document.lines[index - 1]):
        payload.insert(0, "")
    if index < len(document.lines):
        payload.append("")
    for offset, raw in enumerate(payload):
        document = document.insert_line(index + offset, raw)

    placed = find(document, anchor)
    assert placed is not None  # rendered by this function a moment ago
    return document, placed


def amend(
    config: Config,
    role: str,
    anchor: str,
    *,
    title: str | None = None,
    body: str | None = None,
) -> tuple[Document, Section, tuple[str, ...]]:
    """Rewrite one live section's heading text or its prose, in place (RK123).

    The gap this closes is a union of three correct refusals: `drop` refuses while an open
    line points at the anchor, `add` refuses the duplicate, and the guard denies the hand
    edit — so the rationale of an **open** task could not be changed at all, by anybody,
    until it shipped and the section was deleted. That is the ordinary case and not an edge
    one: a design under a marker that is not ✅ is expected to change.

    Its **own** prose and never the subtree. A `§<id>.1` is a section with an anchor of its
    own, amended by naming it — replacing the subtree here would delete somebody's
    subsection as a side effect of correcting a paragraph, which is `drop`'s job and
    `drop`'s refusals.

    The anchor is not a field. An address is `renumber`'s (RK97) at one end and nothing's at
    the other, and a section that changed anchor is a section no pointer resolves to.

    A rewrite that leaves nothing of the original is **not** refused, and the question the
    design left open is answered here: the falsifiable claim is the `symptom` on the task
    line, which `amend` already refuses to touch (RK7). A rationale rewritten under an
    unchanged symptom is still that symptom's rationale; one rewritten because the symptom
    changed is a line the other verb will not let you rewrite. A second guard here would be
    a second opinion about a question already answered one file over.
    """
    document = config.document(role)
    span = _span(document, anchor)
    section = find(document, anchor)
    if span is None or section is None:
        raise NoSuchSection(anchor, config.relative(config.path(role)))
    _, _, heading = span
    own = "".join(document.lines[heading.lineno : document.prose_end(heading)]).strip("\r\n")

    wanted_title = section.title if title is None else title
    wanted_body = own if body is None else body
    changed = tuple(
        name
        for name, before, after in (
            ("title", section.title, wanted_title.strip()),
            ("body", own, _normalize(wanted_body)),
        )
        if before != after
    )
    if not changed:
        return document, section, ()

    _check(document.schema, anchor, wanted_title, wanted_body, _task_for(config, anchor))
    updated = _rewrite(document, heading, replace(section, title=wanted_title.strip()), wanted_body)
    amended = find(updated, anchor)
    assert amended is not None  # the heading this function just wrote
    # Charged against the **subtree**, because that is the number the gate charges a
    # pointed-at section (RK50): a body that clears the limit alone and puts the section
    # over it with its subsections is an amend that passes and a `lint` that refuses.
    if amended.words > document.schema.section_max:
        counted = over_by(
            amended.words,
            document.schema.section_max,
            unit="word",
            because=" with its subsections",
        )
        raise SectionError(
            (
                Violation(
                    "body.too-long",
                    "body",
                    f"{counted}; a section this long is two sections, or a paragraph "
                    f"that belongs in the commit",
                ),
            )
        )
    return updated, amended, changed


def _rewrite(
    document: Document, heading: Heading, section: Section, body: str
) -> Document:
    """Swap a heading's line and the prose under it for the reflowed replacement.

    One removal and one insertion per line rather than a patch, because every mutator in
    :mod:`roadkeep.document` reparses — so the region is taken out first and the new lines
    go in at the heading's own index, where nothing below has moved yet.
    """
    end = document.prose_end(heading)
    payload = ["", *_body_lines(document.schema, body)]
    if end < len(document.lines):
        # The blank that separates this section's prose from the next heading. Kept when
        # there is a next heading and omitted at the end of the file, which is where a
        # trailing blank is one nobody put there.
        payload.append("")
    updated = document.remove_lines(heading.lineno, end)
    for offset, raw in enumerate(payload):
        updated = updated.insert_line(heading.lineno + offset, raw)
    # The heading last and through :func:`heading_of`, so the one writer of that spelling
    # stays one (RK44) — an amend that composed it here would be the second.
    return updated.replace_line(heading.lineno - 1, heading_of(document.schema, section))


def words(body: str) -> int:
    """The words of **argument** in a body — the budget's unit, and never its whole text.

    `len(body.split())` charged every cell of a Markdown table what a word of argument
    costs. Measured while adopting Claude Tray: its `III` is 269 words of which 230 are the
    measured-baseline table the file keeps *because it is data, not design*, and its `XVI.3`
    is 293 of which 72 are a timing table — both under 250 counting prose alone. The remedy
    the finding offered, "this is two sections, or a paragraph that belongs in the commit",
    is advice about prose and applied to neither: splitting a six-row measurement in half
    helps nobody, and the rows are the evidence the design rests on. That adoption ended by
    declaring `section = 300`, a number describing two tables rather than budgeting anybody's
    prose, which is the outcome L6 exists to prevent (RK136).

    So three shapes are data and cost nothing: a **table** row, a **fenced** block with
    everything in it, and a **blockquote**, which is somebody else's words being cited. A
    list is not among them — a bullet is how an argument is written here, and exempting one
    would reopen the budget by reformatting. What the limit is for is an agent's attention
    on an argument, and a row of numbers is not asking for any.
    """
    total = 0
    fence: str | None = None
    for raw in body.splitlines():
        line = raw.lstrip()
        if fence is not None:
            fence = None if line.startswith(fence) else fence
        elif line.startswith(_FENCES):
            fence = line[:3]
        elif not (line.startswith(_DATA) or raw.startswith("    ")):
            total += len(raw.split())
    return total


# -- validation --------------------------------------------------------------


def _check(
    schema: Schema, anchor: str, title: str, body: str, task: Task | None
) -> None:
    """Every rule a section is refused by, under **this file's** schema (RK147).

    The schema is the one the caller loaded the document under — `config.schema_for(role)`,
    which is what `[limits.improvements]` declares (RK50) — and never `config.schema`, which
    is the project's top-level numbers. L1 is the first law: the format is enforced where
    the text is created, and reading a different limit here than the gate charges is exactly
    the failure it names. A project declaring a *tighter* rationale budget got it only after
    the paragraph existed; one declaring a *looser* one had this door refusing prose the gate
    would accept, which is worse — a refusal on legal text is a refusal an author routes
    around. Threaded rather than looked up again, so the two readings cannot disagree.
    """
    out: list[Violation] = []
    if not anchor or anchor.startswith("§"):
        out.append(
            Violation("anchor.sigil", "anchor", f"store the anchor without §: {anchor!r}")
        )
    elif schema.ref_scheme == "outline" and not OUTLINE_ANCHOR_RE.match(anchor):
        # Refused rather than written, because the heading would be read back by nothing:
        # under this scheme the number is what announces a section (RK44), so an anchor
        # that is not one is a section invisible from the moment it reaches the file.
        out.append(
            Violation(
                "anchor.format",
                "anchor",
                f"not an <x.y> outline anchor: {anchor!r} — under ref_scheme = outline "
                f"the heading numbers itself, and a heading with no number is prose",
            )
        )
    elif schema.id_pattern().match(anchor) and task is None:
        # The pointer is the id (RK27), so an id-shaped anchor that names no open task is
        # a section nothing can ever point at — an orphan the moment it is written.
        out.append(
            Violation(
                "anchor.unknown",
                "anchor",
                f"no open task {anchor} points at this section: add the line first, or "
                f"use an outline anchor for prose that belongs to no task",
            )
        )
    if not title.strip():
        out.append(Violation("title.empty", "title", "a section is named by its heading"))
    elif "\n" in title or "\r" in title:
        out.append(Violation("title.newline", "title", "a heading is one line"))
    elif title.lstrip().startswith("#"):
        out.append(
            Violation("title.markup", "title", "the level is a field, not part of the text")
        )
    if not body.strip():
        out.append(Violation("body.empty", "body", "a section with no prose is a heading"))
    elif words(body) > schema.section_max:
        out.append(
            Violation(
                "body.too-long",
                "body",
                f"{over_by(words(body), schema.section_max, unit='word')}; a section "
                f"this long is two sections, or a paragraph that belongs in the commit",
            )
        )
    if out:
        raise SectionError(tuple(out))


def _task_for(config: Config, anchor: str) -> Task | None:
    """The open task this anchor names, if it names one at all."""
    if not config.schema.id_pattern().match(anchor):
        return None
    entry = config.document("roadmap").by_id().get(anchor)
    return entry.task if entry is not None else None


# -- rendering and placement -------------------------------------------------


def _render(
    schema: Schema, anchor: str, title: str, body: str, level: int
) -> tuple[str, ...]:
    heading = f"{'#' * level} {anchor_text(schema, anchor)} {title.strip()}"
    return (heading, "", *_body_lines(schema, body))


def _body_lines(schema: Schema, body: str) -> tuple[str, ...]:
    """The prose as the file carries it: paragraphs filled, structures verbatim.

    Apart from :func:`_render` because `amend` (RK123) writes exactly this and not the
    heading above it — and a second copy of the reflow rules is the one that would fill a
    table the day this one learned not to.
    """
    paragraphs = [p for p in _normalize(body).split("\n\n") if p.strip()]
    out: list[str] = []
    for position, paragraph in enumerate(paragraphs):
        if position:
            out.append("")
        out.extend(_reflow(paragraph, schema.prose_width).split("\n"))
    return tuple(out)


def _normalize(body: str) -> str:
    """The body arrives from an argument or a pipe, so its endings are not the file's."""
    return body.replace("\r\n", "\n").replace("\r", "\n").strip("\n")


def structural(lines: Sequence[str]) -> bool:
    """Is this paragraph a shape inserted verbatim, rather than prose the tool fills?

    Public because `adopt --sections` measures the width a file's prose is *already*
    wrapped to (RK99), and that number only means anything over the paragraphs
    :func:`_reflow` would touch: the widest line in a rationale file is otherwise a table
    row, a heading or a long link — none of which the tool ever wraps, and all of which an
    adopter would read `prose` off by mistake. One predicate, so the width that is measured
    is the width that would be written.
    """
    return any(
        line.lstrip().startswith(_STRUCTURE) or line.startswith("    ") for line in lines
    )


def _reflow(paragraph: str, width: int) -> str:
    lines = paragraph.split("\n")
    if structural(lines):
        return paragraph.rstrip()
    return textwrap.fill(
        " ".join(line.strip() for line in lines),
        width=width,
        break_long_words=False,
        break_on_hyphens=False,
    )


def _placement(document: Document, anchor: str, task: Task | None, where: str = "") -> int:
    """Where the section goes: after the last one under its block, or after what it extends.

    A section for a task belongs under that task's block, so the prose file's order is a
    consequence of the backlog's rather than a decision made per insertion. Prose that
    belongs to no task — this project's `§0` preface — has no block to derive it from, and
    derives it from the anchor instead (RK45): `§0.4` follows `§0.3` and `§RK34.1` belongs
    inside `§RK34`, so the place is the end of the subtree of the longest anchor this file
    declares that the new one extends.

    **Under an outline the anchor decides even for a task** (RK166), because there the
    author chose that anchor and it states a place, while the prose file is organised by the
    outline and not by blocks — measured on all three outline projects on this machine, whose
    prose files declare no block heading at all, so the block branch could only ever refuse.
    Under the id scheme the anchor is the id and carries no place, which is why that scheme
    is the one that reads the block.

    Neither is ever appended at the end as a fallback. A block the prose file does not
    declare is refused (RK37) and so is a *nested* anchor extending nothing: a Block A section
    landing after Block F's reads as Block F's, which is the same mistake `add` refuses one
    file over, and appending is the one answer that is always plausible and frequently
    wrong. A task whose line sits under no heading at all is the one case with nothing to
    derive from either side, and only that one goes last.
    """
    if task is None or document.schema.ref_scheme != "id":
        return _extended(document, anchor, where)
    if not task.block:
        return len(document.lines)
    heading = document.heading(task.block)
    if heading is None:
        raise UnknownBlock(
            task.block,
            sorted({h.label for h in document.headings if h.label}),
            where,
            word=document.schema.heading_word,
        )
    return document.subtree_end(heading)


def _extended(document: Document, anchor: str, where: str = "") -> int:
    """The end of the subtree of the section this anchor extends, or a refusal (RK45).

    Or, for a top-level anchor under an outline, the end of the last top-level section
    (RK166): that is the one place a section extending nothing can go without reading as
    somebody else's, and until this existed a new block's first design was reachable by no
    verb at all. The file's *own* order decides it — after the last one, never sorted, since
    whether `XXII` follows `XXI` is a question about somebody's numbering (L4, L6) and the
    author is the one who wrote the anchor.
    """
    parent = _extends(document, anchor)
    if parent is None:
        if _top_level(document, anchor):
            tops = [s for s in anchored(document) if _is_top(s.anchor)]
            if not tops:
                return len(document.lines)
            span = _span(document, tops[-1].anchor)
            assert span is not None  # read out of this document a line ago
            return span[1]
        raise UnknownParent(
            anchor,
            [section.anchor for section in anchored(document)],
            where,
        )
    span = _span(document, parent)
    assert span is not None  # `_extends` read the anchor out of this document
    return span[1]


#: The depth a section with nothing to derive one from is written at: a one-segment anchor
#: under the id scheme, which is a task's own design, and the last resort for anything else.
NESTED_LEVEL = 3


def _depth(document: Document, anchor: str, level: int | None) -> int:
    """The heading level this section is written at — the caller's, or the file's own (RK166).

    Named, it is used: a project whose outline nests four deep has a depth no rule here
    knows. Omitted, a **new top level** gets the depth this file already writes one at —
    falling back to one under its shallowest heading, which is the file's title in every
    corpus read here — and a **subsection** gets one under the section it extends (RK180).

    That last one was :data:`NESTED_LEVEL` flat, which is the same defect one level down:
    in a file whose designs are `####` under `###` parts, `section add XXI.6` wrote `###
    XXI.6`, a *sibling* of `### XXI` that ends the subtree it was meant to be inside — and
    depth is what says where a section ends (RK115), so `drop XXI` then takes the parent and
    orphans this one.

    The parent's level and not the depth of the file's other sections at the same number of
    segments: those are the same answer in a consistently nested file and different in one
    that mixes schemes, and there the sibling count is wrong in exactly this task's
    direction — this repository declares `§0.3` at level 3, so a `§RK34.1` read off it would
    be written level with the `§RK34` it belongs inside.
    """
    if level is not None:
        return level
    if _top_level(document, anchor):
        tops = [s.level for s in anchored(document) if _is_top(s.anchor)]
        if tops:
            return tops[0]
        levels = [h.level for h in document.headings]
        return min(levels) + 1 if levels else NESTED_LEVEL - 1
    parent = _extends(document, anchor)
    if parent is None:
        # Either a one-segment anchor under the id scheme — a task's design, which has no
        # parent by construction — or a nested one whose parent this file does not declare,
        # and that one never reaches a write: `_extended` refuses it by name.
        return NESTED_LEVEL
    return next(s.level for s in anchored(document) if s.anchor == parent) + 1


def _descended(
    anchor: str, claimed: Mapping[str, Sequence[str]]
) -> list[tuple[str, tuple[str, ...]]]:
    """Every claimed pointer that descends from this anchor, segment by segment (RK169).

    Segment-wise and never as a string, the care :func:`_extends` already takes: `§0.1` is
    not above `§0.10`, and a guard that read it as one would refuse a drop nobody claimed.
    The anchor itself is not a descendant of itself — that is :class:`SectionClaimed`, asked
    first and answered with the message about the pointer that names it exactly.
    """
    segments = anchor.split(".")
    out: list[tuple[str, tuple[str, ...]]] = []
    for ref, owners in claimed.items():
        parts = ref.split(".")
        if len(parts) > len(segments) and parts[: len(segments)] == segments:
            out.append((ref, tuple(owners)))
    return out


def _is_top(anchor: str) -> bool:
    """One segment, so there is nothing above it in the outline: `XXII`, `0`, `IX`."""
    return "." not in anchor


def _top_level(document: Document, anchor: str) -> bool:
    """May this anchor open a new top level of the file? (RK166)

    Only under an outline, and only for a one-segment anchor. Under the id scheme the anchor
    *is* the id, so it carries no place and no level: a `§RK9` that extends nothing is a
    section for a task, placed under that task's block, and reaching here with one means the
    id names no open line — which stays the refusal it was.
    """
    return document.schema.ref_scheme != "id" and _is_top(anchor)


def _extends(document: Document, anchor: str) -> str | None:
    """The longest anchor this file declares that `anchor` continues: `0.4.2` → `0.4`, `0`.

    Segment by segment rather than by string, which is what keeps `§0.1` from being read as
    the parent of `§0.10` — the same care :func:`_names` takes about where an anchor ends.
    """
    segments = anchor.split(".")
    best: list[str] = []
    for section in anchored(document):
        candidate = section.anchor.split(".")
        if len(best) < len(candidate) < len(segments):
            if candidate == segments[: len(candidate)]:
                best = candidate
    return ".".join(best) or None


def _span(document: Document, anchor: str) -> tuple[int, int, Heading] | None:
    """The `[start, end)` lines to delete, and the heading that names them.

    A section ends where the next heading of the same or higher level begins — the
    document's own answer (RK115), because a drop takes the subtree. When it is the last
    thing in the file, the deletion reaches back over the blank line above it, which
    otherwise survives as a trailing blank nobody put there.
    """
    for heading in document.headings:
        if not _names(heading.text, anchor, document.schema):
            continue
        start = heading.lineno - 1
        end = document.subtree_end(heading)
        if end == len(document.lines):
            while start > 0 and blank(document.lines[start - 1]):
                start -= 1
        return start, end, heading
    return None


def anchor_text(schema: Schema, anchor: str) -> str:
    """The anchor as a *heading* spells it: `§RK9` under `id`, `VIII.1` under `outline`.

    The one place that spelling is decided, so a reader that echoes a heading (`section
    show`, `brief`) cannot print a file back differently from how it is written. On the
    pointer the § is unconditional — that is the end of the reference where a sigil is
    what tells an anchor from a word, in either scheme.
    """
    return f"§{anchor}" if schema.ref_scheme == "id" else anchor


def heading_of(schema: Schema, section: Section) -> str:
    """The heading line this section is written as — one spelling, one writer (RK44)."""
    return f"{'#' * section.level} {anchor_text(schema, section.anchor)} {section.title}"


def _anchor_of(text: str, schema: Schema) -> str | None:
    """The anchor this heading declares, or None when it declares none (RK27, RK44).

    Read **per scheme**, because the two write it differently and requiring one spelling
    read the other as prose: measured on Shio, 151 headings yielded 0 sections and
    therefore 74 pointers reported as resolving to nothing against a file that answers
    every one of them — RK15's argument inverted, which is how a gate teaches its reader
    to skip a category.

    * ``id`` — `§RK9 A design` → `RK9`. The anchor is a task id, so the § is what marks
      it as an anchor rather than a word, and it is required.
    * ``outline`` — `VIII.1 MCP server host` → `VIII.1`, Shio's `0. Strategy` → `0`, and
      Turing's lettered fourth level `IX.4.d The pivot` → `IX.4.d` (RK47) and commitclerk's
      block letters `B.2 Ticket trailers` → `B.2` (RK101), where the bare `B — Context`
      above it is still a block: the number *is*
      the announcement, so the sigil belongs on the pointer alone. It is accepted where an
      author wrote one anyway, because a heading nothing can see is the defect this closes
      and not a spelling to punish. What a segment may be is
      :data:`~roadkeep.schema.OUTLINE_ANCHOR_RE`'s to say, at both ends of the pointer.
    """
    head = text.lstrip()
    if schema.ref_scheme == "id":
        if not head.startswith("§"):
            return None
        return head[1:].split(" ", 1)[0].strip() or None
    # The trailing period is Shio's numbering ("## VIII. The Agent Gateway"), not part of
    # the anchor a pointer writes — the pointer says `§VIII.7`.
    token = head.split(" ", 1)[0].lstrip("§").rstrip(".")
    return token if OUTLINE_ANCHOR_RE.match(token) else None


def _title_of(text: str, schema: Schema) -> str:
    """`§RK9 A design` → `A design`. The anchor is one token; the rest is the title."""
    if _anchor_of(text, schema) is None:
        return text
    return text.lstrip().partition(" ")[2].strip()


def _names(text: str, anchor: str, schema: Schema) -> bool:
    """Does this heading declare exactly this anchor?

    Asked of the parsed anchor rather than of the text, which is what keeps `§0` from
    claiming `§0.1` and `VIII.1` from claiming `VIII.10` without a second opinion about
    where an anchor ends.
    """
    return _anchor_of(text, schema) == anchor
