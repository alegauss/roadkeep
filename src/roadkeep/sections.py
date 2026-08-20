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
an address under the id scheme is `renumber`'s.

`move` is the same sentence's other half (RK377). Under an outline the anchor is *not* an id,
so `renumber` never reaches it — line 172 there keeps the pointer as typed — and a doubled
address had no verb at all: `lint` reports `section.ambiguous`, `add` refuses the second one,
and Turing adopted the tool with 13 addresses its two prose files both declared. So the
re-address is a door, taking every refusal `add` computes about a destination
(:func:`unspent`) and moving the whole address in one transaction — the heading, every nested
anchor that extends it, and the `→ §<anchor>` on every line that points at one of them. Which
line meant which of two doubled sections is the thing the files do not say, so the pointers
move with the heading and are **named** in the answer, for the reason
:mod:`~roadkeep.renumbering` names the deps it moved. Only within the address's own parent:
the section stays where it is in the file, and a heading re-addressed across parents would
sit inside a subtree its address no longer names — where the next `drop` takes it.

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
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING

from roadkeep.backlog import Whereabouts
from roadkeep.config import PROSE_ROLES, Config
from roadkeep.kernel.document import Document, Heading, UnknownBlock, blank, save_all
from roadkeep.kernel.schema import (
    OUTLINE_ANCHOR_RE,
    REF_SEPARATOR,
    Schema,
    SchemaError,
    Task,
    Violation,
    over_by,
    split_ref,
)

if TYPE_CHECKING:  # imported for the annotation alone: `history` reads this module back
    from roadkeep.history import Anchor

#: Openers that are a shape whatever follows them: a table row, a blockquote, a fence. No
#: space is required after any of these, `|a|b|` and `>quoted` both being legal Markdown.
_VERBATIM = ("|", ">", "```", "~~~")
#: A list marker or a heading, which is the character **and the space after it** (RK397). The
#: space is the whole rule: `*` was read as a bullet, so a prose line breaking before a
#: `**bold**` span made the paragraph a structure and the tool stopped filling it — silently,
#: `lint` charging a body in words and never in width. `1.5 seconds` fell the same way.
_MARKER = re.compile(r"(?:[-*+]|#{1,6}|\d+[.)])(?:\s|$)")
#: The same characters with no space, which is a thematic break and is still a shape. Kept
#: apart from :data:`_MARKER` rather than folded in, because the two are opposite readings of
#: one prefix and a rule that guessed between them is the defect above with a longer alphabet.
_BREAK = re.compile(r"(?:-{3,}|\*{3,}|_{3,})\s*$")
#: What opens a block whose contents are quoted or generated rather than written (RK136).
_FENCES = ("```", "~~~")
#: A line that is data rather than argument, so the budget does not charge for it. A list
#: marker is deliberately absent: a bullet is how an argument is written in these files.
_DATA = ("|", ">")


class SectionError(SchemaError):
    """A section the schema refuses, carrying every violation, not the first.

    A :class:`~roadkeep.kernel.schema.SchemaError` because it is the same law one file down —
    which also means every caller that already reports violations reports these.
    """


class NoSuchSection(ValueError):
    """An anchor nothing in this file declares."""

    def __init__(self, anchor: str, where: str = "", *, titled_too: bool = False) -> None:
        self.anchor = anchor
        # `titled_too` where the caller also tried the address as a **heading text** (RK1107):
        # `show` and `amend` look an anchor up first and fall through to the title, so a
        # refusal naming only the anchor would describe half the lookup that failed.
        said = f"no §{anchor} section in {where or 'the document'}"
        if titled_too:
            said += f", and no heading reading {anchor!r} either"
        super().__init__(said)


class NotOneOccurrence(ValueError):
    """`--replace` naming a string this prose does not hold exactly once (RK1263).

    The refusal that makes the narrow edit safe. A substitution applied to whatever it happens
    to match is a write whose blast radius the caller cannot see, which is the property the
    whole-body form at least had — so the count is the contract: none means the string was
    mistyped or already corrected, and several mean the call is ambiguous about which.

    Neither is answered by picking one. The first occurrence is a guess, and `str.replace`'s own
    default — all of them — is the edit a caller reaching for a one-clause fix least expects.
    """

    def __init__(self, old: str, found: int, where: str) -> None:
        self.old = old
        self.found = found
        said = (
            f"{where} does not carry {old!r}"
            if found == 0
            else f"{where} carries {old!r} {found} times"
        )
        advice = (
            "check the spelling against `section show`, which prints the prose as it is"
            if found == 0
            else "pass a longer string that occurs once, or --body for the whole prose"
        )
        super().__init__(f"--replace names one occurrence and {said}: {advice}")


@dataclass(frozen=True, slots=True)
class Substitution:
    """One string out and one string in, for an edit whose blast radius is the call (RK1263).

    `amend` takes the whole body, so correcting one stale citation meant copying the section's
    table, fence and block quote out of the file, retyping the clause and passing all of it
    back — eight times over, on a corpus of eight sections whose prose was right except for one
    reference each. Every round trip can drop a pipe from a row or a backtick from a fence, and
    nothing checks: a body is prose to this tool, so a mangled fence validates exactly like a
    clean one.

    A pair and not two arguments threaded separately, because :meth:`applied` is the rule — one
    occurrence or a refusal — and a caller holding the halves apart is a caller who could apply
    it without asking. The whole-body form stays for a real rewrite.
    """

    old: str
    new: str

    def applied(self, prose: str, where: str) -> str:
        """The prose with its one occurrence replaced, or :class:`NotOneOccurrence`."""
        found = prose.count(self.old)
        if found != 1:
            raise NotOneOccurrence(self.old, found, where)
        return prose.replace(self.old, self.new, 1)


class SectionExists(ValueError):
    """One anchor, one section: two would make the pointer ambiguous.

    Asked of **the project's declarations and not the file's** (RK302). This checked the
    document it was writing into and nobody else, so on a project declaring two prose roles
    the same four `section add` calls into each file all succeeded and printed their line
    counts — and `lint` then reported four `section.ambiguous` findings whose own message is
    the argument for refusing here: one anchor names one section, so no pointer resolves and
    every verb that reads one refuses. The write path was building a state its own gate calls
    unresolvable, out of which `drop` was the only exit — and that deletes prose somebody
    wrote.

    No `--force`, deliberately. RK297's measurement is that the doubled anchors in both live
    corpora were made by hand rather than by this verb, so a door that never opens is the
    cheaper answer than one whose only correct use is a hand edit the guard already denies.
    """

    def __init__(
        self, anchor: str, where: str, lineno: int, *, elsewhere: bool = False
    ) -> None:
        self.anchor = anchor
        self.lineno = lineno
        self.elsewhere = elsewhere
        span = (
            "an anchor names one section across every prose file this project declares"
            if elsewhere
            else "an anchor names one section"
        )
        super().__init__(
            f"§{anchor} is already at {where}:{lineno}: {span}, "
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


class AnchorRetired(ValueError):
    """An outline address a heading already used, and a ship deleted (RK247).

    :class:`SectionExists` for the anchors that are no longer there. Under an outline the
    caller names the anchor, and the only list they are ever shown is of the sections that
    **exist** — so after a fully-shipped family "the next one" looks like `.1`, and writing
    it silently re-points every ledger entry whose prose cites that address at prose about
    something else. `as_ledger` keeps no pointer, so nothing in the files says the address
    was ever spent; the diff does, which is where this reads it.

    The same rule ids have had since RK4, one file over: retired-never-reused. The remedy is
    an address nobody used, so the refusal carries the derived one rather than sending the
    author to grep a ledger — which is how the safe number was found before this existed.
    """

    def __init__(self, anchor: str, written_in: str, free: str = "", where: str = "") -> None:
        self.anchor = anchor
        self.written_in = written_in
        #: The derived free child, or empty for a **top-level** address: what follows
        #: `XXXVII` is somebody's numbering — roman, lettered, a phase — and inventing the
        #: next one would be this tool choosing an author's outline (L4).
        self.free = free
        file = f" in {where}" if where else ""
        commit = f" ({written_in[:7]})" if written_in else ""
        remedy = (
            f"§{free} is the next one nothing ever used"
            if free
            else "name an address this file has never declared"
        )
        super().__init__(
            f"§{anchor}{file} was declared before{commit} and its section is gone: the "
            f"entries whose prose cites it are still there, and reusing the address makes "
            f"them cite this — {remedy}"
        )


class UnknownParent(ValueError):
    """An anchor states its place, and this file declares nothing it extends (RK45).

    The counterpart of :class:`~roadkeep.kernel.document.UnknownBlock`, for prose that belongs to
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

    ``opens`` is every ancestor of this anchor the file does not declare, outermost first
    (RK1207). Until it existed every clause of this sentence was true and none of them was a
    verb: the listing of what the file declares came closest, and on a file whose outline has
    not started that listing is the word `none`. The write that makes room is the **same
    command one address up**, which is why it reads as a wall rather than a step — a caller
    told `section add` refuses naturally looks for a different verb, and there is none.

    Derived rather than described, so what is left for the author is the title, which is
    editorial and L4's to leave alone. A chain, because `§I.1.2` on an empty outline is two
    calls before this one: reporting the first alone is the staircase RK1198 took out of the
    door one file over, and this is the same staircase met by a caller who arrived directly —
    writing a design before the line, which is the order an outline invites.

    ``role`` rides with it for RK197's reason: a project whose only prose file is the strategy
    one would be handed `section add`'s default, which is a remedy that cannot run.
    """

    def __init__(
        self,
        anchor: str,
        declared: Sequence[str],
        where: str = "",
        *,
        opens: Sequence[str] = (),
        role: str = "",
    ) -> None:
        from roadkeep.provenance import invocation  # noqa: PLC0415 - RK260

        self.anchor = anchor
        self.declared = tuple(declared)
        self.opens = tuple(opens)
        known = ", ".join(f"§{a}" for a in self.declared) or "none"
        file = f"{where} " if where else ""
        named = "" if role in ("", "improvements") else f" --role {role}"
        steps = ", then ".join(
            f"`{invocation()} section add {one} --title …{named}`" for one in self.opens
        )
        # Silent where nothing derives one, which is a one-segment anchor under the id scheme:
        # there this refusal means the id names no open line, and a `section add` above it
        # would be an address invented out of a task number.
        opening = f" — {steps} opens what it extends" if self.opens else ""
        super().__init__(
            f"no section §{anchor} extends ({file}declares: {known}): an anchor states "
            f"its own place, and appending files the prose under the last block{opening}"
        )


class SameAnchor(ValueError):
    """A move to the address the section already carries (RK377)."""

    def __init__(self, anchor: str) -> None:
        self.anchor = anchor
        super().__init__(
            f"§{anchor} already is that address: a move that changes nothing would still "
            f"rewrite the file, and an untouched file with a moved mtime reads as an edit"
        )


class AnchorIsId(ValueError):
    """A re-address under `ref_scheme = "id"`, where the address is the task's (RK377).

    The one scheme this verb has nothing to do. There the anchor *is* the id, so a section
    whose address moved and whose line did not is a section its own task no longer points at
    — and moving both is :func:`~roadkeep.renumbering.renumber`, which does it in one
    transaction with every dep. The other reason to be here is a doubled anchor, and under
    this scheme that is two files holding one task's design rather than two addresses
    colliding: one of them is the design and the other is a copy, which is `section drop`.
    """

    def __init__(self, anchor: str, where: str = "") -> None:
        self.anchor = anchor
        file = f" in {where}" if where else ""
        super().__init__(
            f"§{anchor}{file} is addressed by its task's id, so the address is not this "
            f"verb's to move: `renumber {anchor} --to <id>` moves the line, the heading, the "
            f"subtree and every dep together, and a second file holding the same design is "
            f"`section drop`"
        )


class NotASibling(ValueError):
    """A destination under a different parent, which is a relocation and not a move (RK377).

    The bound that keeps this verb honest about what it does. A section's **place** is derived
    from its address (RK45), and this write changes the address without moving a line of prose
    — which is right while the parent is the same, and wrong the moment it is not: a `§XIV.5`
    re-addressed in place still sits inside `§I`'s subtree, where :func:`_span` ends it, `drop`
    takes it and `_extends` reads the file's shape past it. So the two would disagree, and the
    disagreement is invisible until a deletion acts on it.

    Refused rather than relocated, because relocating carries prose the caller never named:
    a subtree holds sections other lines point at (:class:`SectionOccupied`'s whole argument),
    and re-levelling one to fit a new depth is a rewrite of headings nobody asked about.
    """

    def __init__(self, anchor: str, to: str, parent: str) -> None:
        self.anchor = anchor
        self.to = to
        self.parent = parent
        under = f"under §{parent}" if parent else "at the top level"
        super().__init__(
            f"§{anchor} cannot move to §{to}: this write changes the address and not the "
            f"place, so a destination under another parent leaves the heading inside the "
            f"subtree it no longer names — name an address {under}"
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
    #: This section's **own** prose, where :attr:`body` is a subtree (RK287). None where the
    #: two are the same string — :func:`anchored`'s reading — and set by :func:`find`, which
    #: is the constructor that returns the children with the parent. The **text** and not a
    #: count of it since RK1112: `amend` replaces exactly this, so a reader that could state
    #: its size but not print it left `show` unable to offer what the write takes.
    own: str | None = None

    @property
    def words(self) -> int:
        """What the budget charges this section: its argument, not its whole text (RK136)."""
        return words(self.body)

    @property
    def prose(self) -> str:
        """This section's own text, subsections excluded — what `amend --body` replaces."""
        return self.body if self.own is None else self.own

    @property
    def own_words(self) -> int:
        """The same count over this section's own prose, with no subsection in it (RK287).

        Equal to :attr:`words` for a leaf, and the whole point for a parent: a container
        like this repository's `§0` has no paragraph of its own, so :attr:`words` measures
        the file's shape rather than anyone's argument.
        """
        return words(self.prose)

    @property
    def nests(self) -> bool:
        """Whether the two counts differ, which is when printing only one of them misleads.

        The rule RK245 and RK265 each found at another door: a verb printing a number beside
        a limit is claiming the two are the same number. Here they are two numbers, and which
        one the gate charges depends on whether a line points at this anchor (RK215) — so
        both are said, and neither is presented as the verdict.
        """
        return self.own_words != self.words

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

    def counted(self, limit: int) -> str:
        """This section's size as every verb that prints it says it (RK287).

        Both figures where they differ, and the limit beside them either way. A bare `310 words`
        on a section whose own prose is 48 invites cutting prose that was never over — and the
        limit is what makes the number act on something, which is the whole of RK283 one door
        over. Which of the two the gate charges depends on whether a line points at the anchor
        (RK215), so neither is spelled as the verdict and the refusal states its own.

        Here since RK1170: three verb files and a view all print this, and a helper in
        `rendering.py` was the fifth place a fact about a section was spelled.
        """
        if not self.nests:
            return f"{self.words} words (limit {limit})"
        return f"{self.own_words} words, {self.words} with subsections (limit {limit})"

    def payload(self, where: str) -> dict[str, object]:
        """This section as data, at every door that publishes one (RK1170).

        `where` is passed and not stored, for `counted`'s reason: the file a section was read
        from is a fact about the project, and an `add` publishes the same record about a file it
        is writing into.
        """
        return {
            "anchor": self.anchor,
            "title": self.title,
            "level": self.level,
            "file": where,
            "first": self.first,
            "last": self.last,
            "words": self.words,
            # The figure the limit is measured on, beside the one a reader pays (RK287). `words`
            # keeps its meaning — the subtree, which is what a drop takes — and this is the
            # section's own argument, which for a container is none of it.
            "own_words": self.own_words,
        }


def local(schema: Schema, anchor: str) -> str | None:
    """This address as the *file* writes it, or None where it is another role's (RK340).

    The one seam between the project's namespace and a document's own. A role that declares
    `[refs] <role> = "S"` answers `S:I` and never a bare `I`; a role that declares none
    answers the bare address and never a prefixed one — which is what makes the two
    addresses rather than one anchor read twice, and it is symmetric on purpose: a project
    that prefixed only one of its files would otherwise have `S:I` and `I` both resolving in
    strategy, and the collision back one file over.

    None and not a raise, because every caller already has an answer for an anchor this file
    does not hold: `find` returns nothing, `declaring` leaves the role out, and the gate says
    `ref.unresolved` naming the files it looked in.
    """
    prefix, bare = split_ref(anchor)
    return bare if prefix == schema.ref_prefix else None


def qualified(schema: Schema, anchor: str) -> str:
    """This file's address as a *pointer* writes it — `I.2` → `S:I.2` (RK340).

    The inverse of :func:`local`, and the one writer of the prefixed spelling for the reason
    :func:`anchor_text` is the one writer of the heading's: an address rendered by hand at a
    call site is how the two ends of a pointer come to disagree.
    """
    return f"{schema.ref_prefix}{REF_SEPARATOR}{anchor}" if schema.ref_prefix else anchor


def find(document: Document, anchor: str) -> Section | None:
    """The section this anchor names, or None. Subsections belong to it, not after it."""
    span = _span(document, anchor)
    if span is None:
        return None
    _, end, heading = span
    body = "".join(document.lines[heading.lineno : end]).strip("\r\n")
    # Both spans off the one heading (RK287). The subtree is what a drop deletes and what a
    # reader pays; the prose is what the argument costs — and a Section that carried only the
    # first left every printer stating a figure no limit is measured against.
    own = "".join(document.lines[heading.lineno : document.prose_end(heading)]).strip("\r\n")
    return Section(
        anchor=anchor,
        title=_title_of(heading.text, document.schema),
        level=heading.level,
        first=heading.lineno,
        last=end,
        body=body,
        own=own,
    )


def declaring(config: Config, anchor: str) -> tuple[str, ...]:
    """Which declared prose roles actually hold this anchor, in `[files]` order (RK196).

    The resolution no verb may assume: `ship` deletes the design and `defer` reports where it
    stayed, and both were written naming `improvements` outright — the reason a project
    declaring `strategy` alone was told its own section is missing while the section sat
    there. `show` asks the same question with one distinction more, a declared file that is
    not on disk yet being an answer of its own, so it keeps its own reading and this stays
    the shape a writer needs.

    A **tuple**, because the answers to none and to two are not this function's: an absence
    is where the design would go for one caller and a refusal for another, and two roles
    declaring one anchor is the `ref.ambiguous` the gate reports and no verb resolves by
    picking. Only which files say so is the same question everywhere.
    """
    return tuple(
        role
        for role in PROSE_ROLES
        if config.has(role)
        and config.path(role).is_file()
        and find(config.document(role), anchor) is not None
    )


def bind(document: Document, section: Section, task_id: str) -> Document:
    """Append a task's id to a heading that names none, changing nothing else (RK452).

    The binding written from the **pointer's** end. :func:`_bound` renders it into a title a
    caller passed; this one is for the write where nobody passed a title at all — `add --ref`
    on an outline anchor whose design was written first — so what it may touch is the id and
    not one byte more.

    Which is why it appends to the heading's own line rather than re-rendering it. RK388
    settled that a `--title` amend restyles on purpose: the caller asked for the heading to
    change, so the canonical spelling is right there. Nobody asked here, and re-rendering
    would take the `§` an author wrote and whatever spacing that heading had (RK44) as the
    silent price of a binding — the exact restyle RK388 removed from the body-only path.

    The caller has already established that the heading names no task: this appends, and
    deciding whether it should is :func:`owners`'.
    """
    heading = next(
        (one for one in document.headings if anchor_of(one.text, document.schema) == section.anchor),
        None,
    )
    if heading is None:  # pragma: no cover - the caller found this section a moment ago
        return document
    line = document.lines[heading.lineno - 1]
    body = line.rstrip("\r\n")
    return document.replace_line(heading.lineno - 1, f"{body.rstrip()} ({task_id})")


def owners(section: Section, ids: re.Pattern[str]) -> tuple[str, ...]:
    """The tasks this section belongs to, whichever scheme addresses it (RK61).

    Under `ref_scheme = "id"` the anchor *is* the id. Under an outline the anchor is
    `XVI.12` and the id is in the heading — `§XVI.12 A design (SH123)` — which is why both
    checks below fired for nobody in the two live corpora until this read it.

    So **naming a task in a heading is the claim to be its rationale**, with no exemption for
    where the section sits. The first attempt made one — "a task's section is under a `Block X`
    heading", read off this repository's own file — and it disabled the check on the corpus it
    was written for: Shio files its rationale under `## VIII. The Agent Gateway (Block H)`,
    which is an outline heading, so all 146 of its sections looked unowned. A section that
    means to cite a task rather than belong to it says so in its prose, which this never reads.

    A **sub-anchor under the id scheme is derived from an id** and belongs to it (RK114):
    `§RK34.1` is `RK34`'s subsection and the anchor says so, segment by segment — the same
    reading :func:`~roadkeep.sections._extends` gives it one module over. Matching the whole
    anchor cannot see that, which exempted every sub-anchor from both checks and let a
    `renumber RK1 --to RK9` leave `§RK1.1` behind on a file `lint` then called clean. Only
    the first segment is asked, so `§0.1` and `§XVI.12` still reach the heading below: prose
    belonging to no task stays nobody's orphan.

    Here rather than inside `lint` because the **writer needs the same answer** (RK236): a
    departure deletes the section it owns, and ownership read one way by the gate and another
    by the drop is how Turing's standing GEO memo lost two subsections to a retirement.
    """
    if ids.match(section.anchor):
        return (section.anchor,)
    root = section.anchor.split(".")[0]
    if root != section.anchor and ids.match(root):
        return (root,)
    return section.names(re.compile(rf"\b{ids.pattern.strip('^$')}\b"))


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

    Membership is the **filter** and no longer the scan (RK1106): :func:`references` reads the
    prose once and this selects from it, because the gate asks the same file the opposite
    question — which citations resolve to nothing — and two scanners would give a project two
    counts of its own dead citations.
    """
    wanted = {anchor for anchor in anchors if anchor}
    if not wanted:
        return ()
    skipped = set(ignore)
    return tuple(
        (cited.anchor, cited.by)
        for cited in references(document)
        if cited.anchor in wanted and cited.by not in skipped
    )


@dataclass(frozen=True, slots=True)
class Cite:
    """One `§<anchor>` a section's prose makes, and where it is written (RK1106).

    The record the fourth relation resolves — a citation, beside the dep, the pointer and the
    queue entry :mod:`roadkeep.referring` already declares. It carries the place because the
    gate reports `file:line`, and the citing section because that is who has to make the edit:
    a dangling reference is a defect in the prose that makes it, not in the section it names.
    """

    #: What is cited, as the prose spells it — namespaced (`S:I.2`) where the pointer is.
    anchor: str
    #: The anchor of the section whose prose cites it.
    by: str
    #: 1-based, as an editor counts.
    lineno: int


#: An anchor-shaped token after a `§`, in either scheme (RK1106). Deliberately looser than
#: :data:`~roadkeep.kernel.schema.OUTLINE_ANCHOR_RE` and than any id shape, because the two
#: questions are different: a *reference* is anything an author wrote as one, and whether the
#: token is a well-formed address of this project is what resolving it answers. A pattern that
#: only matched valid anchors would read a typo as prose and report nothing about it, which is
#: the citation this exists to find.
#:
#: **Atomic**, which is the whole of RK1111: the address is taken whole or not at all. The
#: earlier boundary `(?![\w.])` refused a sentence-final `.` — punctuation the address does not
#: own — and the engine answered by *shortening the match* until the lookahead passed, so the
#: prose `§S:V.` was read as a citation of `§S` and `§I.2.` as no citation at all. Both silent:
#: one reported a live anchor as dangling in every project that namespaces a second file, the
#: other reported nothing over a dead one. What follows a whole address may be anything that is
#: not a word character — a period, a comma, a paren, a fence — and a token that runs on into
#: `\w` after the scheme's own separators is not an address in either scheme.
_CITED_RE = re.compile(r"§((?>[A-Za-z0-9]+(?::[A-Za-z0-9]+)?(?:\.[A-Za-z0-9]+)*))(?!\w)")


def cited_in(body: str) -> tuple[str, ...]:
    """Every anchor a body cites, in order and without repeats (RK1227).

    :func:`references` asks this of a **document**, for the gate; this asks it of a paragraph
    somebody is about to write, for the door. Both go through :func:`_argument` and
    :data:`_CITED_RE`, so what counts as a citation — the four exclusions, each measured
    across four trees — is decided once and the two cannot come to disagree about a quotation.

    Distinct here and every occurrence there, which is the same split :func:`citing` makes:
    the gate reports a place per dead citation because each is an edit, and a refusal is about
    *which addresses do not resolve*, where naming one twice is noise.
    """
    return tuple(dict.fromkeys(_CITED_RE.findall(_argument(body))))


def references(document: Document) -> tuple[Cite, ...]:
    """Every citation this file's prose makes, unresolved (RK1106).

    One scan, two questions. :func:`citing` asks which of *these* anchors are cited, at the
    moment a transaction deletes them; the gate asks which citations name nothing at all. The
    reading of what counts as a citation — :func:`_argument`'s four exclusions, each measured
    across four trees — belongs to neither of them and is made once, here.

    Every occurrence and not the distinct set: two dead citations on two lines are two edits,
    and a reader handed one of them fixes the file halfway. `citing` de-duplicates on its own
    side, where the answer is *which* section to warn about and saying it twice is noise.
    """
    out: list[Cite] = []
    for section in anchored(document):
        # Off the document's own lines and **not** off `Section.body`, which is stripped of the
        # blank after the heading — measured: that shift reported claude-tray's §I.7 two lines
        # early, onto prose carrying no citation at all. `_argument` blanks a quotation in
        # place rather than dropping it, so this slice and its output stay index-for-index.
        raw = "".join(document.lines[section.first : section.last])
        for offset, line in enumerate(_argument(raw).splitlines()):
            for found in _CITED_RE.findall(line):
                out.append(
                    Cite(anchor=found, by=section.anchor, lineno=section.first + 1 + offset)
                )
    return tuple(out)


#: A mark that **carries its file**: the outward citation (RK1181). Prose in a governed file
#: legitimately argues from another document's numbered sections — a spec, an RFC, a standard —
#: and those documents number themselves with the same mark, so `§3.1` written plainly is read as
#: a pointer into this file and refused as dangling. Met twice in one session in a project whose
#: specs live beside the governed files; both times the repair was to strike the mark and spell
#: the reference in words, which is a worse sentence, and both times the turn was already spent.
#:
#: Not a suppression flag, which is what this must never become: an author who can silence the
#: check silences it for the typo too, and a bare mark naming nothing is usually exactly that —
#: the case the rule was built for, which it goes on catching. What earns the silence is the
#: **file**, named the way a Markdown link already names one. This repository's own `agents.md`
#: writes `[§0.3](docs/IMPROVEMENTS.md)`, so the form is the corpus's and not an invention.
#:
#: A fragment (`[§I.2](#i-2)`) is *this* document and buys nothing: a target that names no path
#: would be the suppression flag with an extra two characters.
_OUTWARD_RE = re.compile(r"\[(§[^\]]*)\]\(\s*(?!#)([^)\s]+)[^)]*\)")


def _argument(body: str) -> str:
    """A section's prose with every quotation blanked out, so a reference in one is not one.

    Blanked rather than dropped: the lines keep their positions, which is what lets a caller
    report a place without the two readings of the file disagreeing about which line it is.

    The **outward citation** is blanked the same way (RK1181): a mark inside a Markdown link
    whose target is a path is a reference into that document, which this file's outline cannot
    answer for and the gate has nothing to resolve it against.
    """
    out: list[str] = []
    fence: str | None = None
    #: Whether an **indented** code block is open, and what the last line was — the two the
    #: fourth exclusion needs (RK1151). A block and not a line, because four spaces mean two
    #: different things: sample output where a blank line came before, and a list item's own
    #: continuation where a bullet did. A rule reading indentation alone would blank the
    #: second, and a citation nobody scans is worse than one falsely reported — this is the
    #: backstop that is supposed to notice.
    indented = False
    previous = ""
    for raw in body.splitlines():
        # The link text first and in place, so an address inside one is gone before any other
        # rule reads the line and every column after it still lines up.
        line = _OUTWARD_RE.sub(lambda m: " " * len(m[0]), raw)
        stripped = line.strip()
        if fence is not None:
            if stripped.startswith(fence):
                fence = None
            out.append("")
            previous = stripped
            continue
        if stripped.startswith(_FENCES):
            fence = stripped[:3]
            out.append("")
            previous = stripped
            continue
        if stripped.startswith(">"):
            out.append("")
            previous = stripped
            continue
        if indented and stripped and not line.startswith(_INDENT):
            # Closed by the first line indented less, which is Markdown's own rule — a blank
            # line inside an indented block does not end it.
            indented = False
        elif not indented and stripped and line.startswith(_INDENT) and not previous:
            # Opened only after a blank line: indented code cannot interrupt a paragraph, and
            # under a bullet the blank is the item's, so `_BULLET` is what tells them apart.
            indented = not _BULLET.match(_before(out))
        if indented:
            out.append("")
            previous = stripped
            continue
        out.append(_QUOTED.sub(lambda m: " " * len(m.group()), line))
        previous = stripped
    return "\n".join(out)


#: Four spaces: Markdown's other code block, and the width a list item's continuation shares
#: with it. A tab is deliberately not read as one — no line in any of the four trees measured
#: for RK1151 opens a block that way, and treating one as code would blank a Markdown table.
_INDENT = "    "
#: What opens a list item, whose continuation is prose (RK1151). Ordered and unordered both:
#: a numbered argument's second paragraph is indented exactly like sample output.
_BULLET = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s")


def _before(rendered: list[str]) -> str:
    """The last line that said anything, for deciding what an indent belongs to.

    Read off what is already rendered rather than off the source, so a blockquote or a fence —
    both blanked above — cannot be mistaken for the bullet an indent hangs from.
    """
    for line in reversed(rendered):
        if line.strip():
            return line
    return ""


#: What is being talked about rather than said: a code span, and a pointer reproduced whole.
_QUOTED = re.compile(r"`[^`]*`|→\s*§[\w.]+")


def unanchored(document: Document) -> tuple[Heading, ...]:
    """Headings that are where a section would be, and carry no anchor (RK281).

    :func:`anchored` finds `§<anchor>` headings, and the sigil is **this tool's convention**
    rather than Markdown's — so `adopt --sections` read a rationale file correctly exactly
    when that file had already adopted the format, which is the one case nobody needs an
    estimate for. A real `DESIGN.md` answered 0 sections and 0 would change: RK98's zero,
    one command over from where RK279 closed it.

    A second reader over the same headings and never a second grammar, the line RK98 drew
    when it counted table rows without parsing cells. Nothing here composes an anchor — an
    address the file does not have is not this tool's to invent (L4) — so what comes back is
    the heading, and the estimate takes a count and a word measure off its span.

    Two exclusions, both because they are frame rather than work: a level-1 heading is the
    document's title and not a section in it, and a heading with no prose of its own is a
    container — `## Block B` above a list of subsections describes them, and counting it
    would measure the file's shape rather than anyone's paragraph, which is the distinction
    :func:`anchored` already makes for `§0`.
    """
    out: list[Heading] = []
    for heading in document.headings:
        if heading.level < 2 or anchor_of(heading.text, document.schema) is not None:
            continue
        end = document.prose_end(heading)
        if any(not blank(line) for line in document.lines[heading.lineno : end]):
            out.append(heading)
    return tuple(out)


def anchored(document: Document) -> tuple[Section, ...]:
    """Every `§<anchor>` section in file order, each carrying only its **own** prose.

    The gate (RK15) needs the set and not one lookup: a pointer resolves in one
    direction, and an orphan — a section nothing points at — is only visible from the
    other. **Own** prose, because :func:`find` deliberately returns the subtree (`drop`
    has to delete it whole, and a task's rationale is charged for the subsection it
    grew), and a container like this repository's `§0` has no prose of its own at all —
    counting its children against it would measure the file's shape rather than anyone's
    paragraph. Which of the two the budget uses is the gate's decision, not this one's.

    Each anchor is the **project's** address and not the heading's (RK340): a heading writes
    `I` and a pointer writes `S:I` where `[refs]` gives this role a namespace, and the gate
    reads these sections into one index across both prose files — which is the index the
    collision was in. So the qualification happens here, once, and every reader downstream
    compares addresses that are comparable. :func:`anchor_text` is the way back.
    """
    out: list[Section] = []
    for heading in document.headings:
        anchor = anchor_of(heading.text, document.schema)
        if anchor is None:
            continue
        end = document.prose_end(heading)
        out.append(
            Section(
                anchor=qualified(document.schema, anchor),
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


def descending(document: Document, anchor: str) -> tuple[Section, ...]:
    """The nested sections that are this address's own numbering — `I.2.1`, never `XIV.8`.

    :func:`nested` bounded by the **name** rather than by the span, which is the difference
    that matters to anything re-addressing a subtree: a `§I.2.1` travels with `§I.2` because
    the address says it is part of it, and a `§XIV.8` somebody filed inside that subtree keeps
    the address of the thing that owns it. Segment by segment and never as a string prefix,
    the care :func:`_extends` takes at the other end of the same question — `§0.1` is not
    above `§0.10`.

    Public and here rather than beside either caller (RK377): `renumber` asks it of an id's
    subtree and `move` of an outline address's, and two readings of "which anchors are this
    one's own" is how one door renames half a subtree the other would have renamed whole.
    """
    segments = anchor.split(".")
    return tuple(
        child
        for child in nested(document, anchor)
        if child.anchor.split(".")[: len(segments)] == segments
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


@dataclass(frozen=True, slots=True)
class Shown:
    """One section as `show` answers it: the extent asked for, and what carries the rest.

    The result that read had none of (RK1170). The door looked the address up two ways, chose
    an extent off a flag, gathered the nested anchors and composed both registers from the
    four — so neither reading had a result to derive from, which is that task's whole subject.
    """

    section: Section
    #: The extent the caller asked for (RK1112): the subtree is what a reader of the design
    #: wants and the own prose is what `amend` replaces, so the flag says which question this
    #: call is. `body` stays the key either way — it is the body of what was asked for, and
    #: `own_words` beside it already states that the two extents differ.
    body: str
    #: The anchors nested under it, named rather than left as a blank line (RK1118): a
    #: container has no prose of its own, so `--own` on this repository's `§0` answered with a
    #: heading and nothing — correct, and indistinguishable from a command that printed nothing.
    nested: tuple[str, ...]
    #: The file, as this project spells it.
    where: str

    @classmethod
    def of(cls, config: Config, role: str, address: str, own: bool) -> Shown:
        """Look the address up the way every reader here does, or raise `NoSuchSection`.

        **An anchor first and a heading text second** (RK1107): an anchor is the project's
        chosen name and wins, and the fall-through is what makes `section show 'Table of
        contents'` an answer instead of a refusal.
        """
        document = config.document(role)
        where = config.relative(config.path(role))
        section = find(document, address)
        if section is None:
            heading = titled(document, address)
            section = (
                None
                if heading is None
                else next(
                    (one for one in untitled(document) if one.first == heading.lineno),
                    None,
                )
            )
        if section is None:
            raise NoSuchSection(address, where, titled_too=True)
        return cls(
            section=section,
            body=section.prose if own else section.body,
            nested=tuple(one.anchor for one in nested(document, section.anchor)),
            where=where,
        )

    def stated(self, schema: Schema) -> str:
        """The heading, a blank line, and the prose — which is what an `amend --body-file` is
        composed from, so nothing else may reach stdout."""
        return chr(10).join([heading_of(schema, self.section), "", self.body])

    def silence(self) -> list[str]:
        """Which of the two empty answers this is, for **stderr** (RK1118).

        Two, because a section with no text has two shapes and one of them is a defect: a
        **container** is the ordinary structure of a rationale file — this repository's `§0`,
        and every `## <Block>` heading over subsections — while a leaf with nothing in it is
        what the gate calls `body.empty`. Saying "no prose" to both would send half the readers
        to `lint` and the other half looking for a bug in the reader.

        On stderr and not beside the prose, for the reason above: this output is piped into a
        file, and a sentence on stdout would end up in it.
        """
        if self.body.strip():
            return []
        if self.nested:
            named = ", ".join("§" + one for one in self.nested)
            return [
                f"roadkeep: §{self.section.anchor} carries no prose of its own — its "
                f"{self.section.words} words are {named}, each amended by its own anchor"
            ]
        return [
            f"roadkeep: §{self.section.anchor} is empty in {self.where}: a heading with no "
            f"paragraph under it, which `lint` reports as `body.empty`"
        ]

    def payload(self) -> dict[str, object]:
        """The same answer as data, with the nested anchors under their own key — so the
        payload and the report cannot disagree about why a body came back empty."""
        return {
            **self.section.payload(self.where),
            "body": self.body,
            "nested": list(self.nested),
        }


@dataclass(frozen=True, slots=True)
class Deleted:
    """One section removed whole, and who is left citing it (RK78, RK206).

    A record and no longer a three-tuple (RK1170): the design that task rests on is that both
    registers come off **one result**, and a tuple has no place to put a method. What the change
    bought beyond that is :attr:`nested` — the door recomputed the subtree with a second reader
    to say what went with the heading, and :func:`drop` had the same list in hand to delete it.
    """

    #: The file without the section, unsaved: the caller mid-transaction decides when.
    document: Document
    section: Section
    #: Sections whose **prose** still names what this deleted (RK206). Reported and never
    #: refused: a citation is a sentence, and re-wording one is an edit rather than a
    #: transaction to abandon.
    cited: tuple[str, ...] = ()
    #: The anchors that went with it, nested under the one named (RK78). On the record because
    #: after the write no file holds them, and this answer is their only record.
    nested: tuple[str, ...] = ()
    #: The file this was dropped from, as the caller spells it — the same string the refusals
    #: above take, so a report and a refusal can never name two different files.
    where: str = ""

    def stated(self, config: Config, wrote: Sequence[Path]) -> str:
        """What went, and who is left pointing at it."""
        from roadkeep.rendering import _cited_rows, _staging_rows  # noqa: PLC0415 - RK260

        rows = [f"dropped {self.section} from {self.where}"]
        if self.nested:
            rows.append(f"  nested   {', '.join(f'§{a}' for a in self.nested)} went with it")
        rows += _cited_rows(self.cited)
        rows += _staging_rows(config.relative(one) for one in wrote)
        return "\n".join(rows)

    def payload(self, config: Config, wrote: Sequence[Path]) -> dict[str, object]:
        """The same answer as data, with the subtree the anchor does not state (RK78)."""
        from roadkeep.rendering import _wrote_json  # noqa: PLC0415 - RK260

        return {
            **self.section.payload(self.where),
            "nested": list(self.nested),
            "cited": list(self.cited),
            **_wrote_json(config, wrote),
        }


@dataclass(frozen=True, slots=True)
class Written:
    """One section placed under its block or its anchor (RK93).

    A record and no longer a two-tuple, for :class:`Deleted`'s reason (RK1170). It carries the
    role because both registers need it — the path to name, and the word limit to count the
    prose against, which is per role and not per project.
    """

    document: Document
    section: Section
    role: str = "improvements"

    def stated(self, config: Config, wrote: Sequence[Path]) -> str:
        from roadkeep.rendering import _staging_rows  # noqa: PLC0415 - RK260

        where = config.relative(config.path(self.role))
        rows = [
            f"§{self.section.anchor} → {where}:{self.section.first}  "
            f"{self.section.counted(config.schema_for(self.role).section_max)}"
        ]
        rows += _staging_rows(config.relative(one) for one in wrote)
        return "\n".join(rows)

    def payload(self, config: Config, wrote: Sequence[Path]) -> dict[str, object]:
        from roadkeep.rendering import _wrote_json  # noqa: PLC0415 - RK260

        return {
            **self.section.payload(config.relative(config.path(self.role))),
            **_wrote_json(config, wrote),
        }


@dataclass(frozen=True, slots=True)
class Rewritten:
    """One section's heading text or prose corrected in place (RK123, RK1107).

    One record for both doors — anchored and unanchored — because what differs between them is
    what the write *may* do and not what it answers with: an unanchored section is named by its
    heading and carries no word count, and :attr:`Section.anchor` being empty is what says so.
    """

    document: Document
    section: Section
    #: Which fields moved. Empty when the file already read that way, and then nothing was
    #: written — the one answer here with nothing in it to read (RK1109).
    changed: tuple[str, ...] = ()
    role: str = "improvements"

    def stated(self, config: Config, wrote: Sequence[Path], read_body: bool) -> str:
        """What moved, or why nothing did (RK1109).

        `read_body` is the caller's: whether this call looked at the prose at all is a fact
        about the argv — a piped body and a `--title` land in the unchanged answer together,
        and one of them means the paragraph was never read.
        """
        from roadkeep.rendering import _staging_rows  # noqa: PLC0415 - RK260
        from roadkeep.verbs.reading import unread_prose  # noqa: PLC0415 - RK260

        where = config.relative(config.path(self.role))
        # An unanchored section is named by its heading and never by a bare sigil (RK1107), and
        # it carries no word count: `section = <n>` is what a *rationale* may spend, and printing
        # a figure beside a limit is claiming the two are the same number — which the file's
        # opening paragraph and its contents table are not measured by. `[budgets]` counts bytes.
        named = f"§{self.section.anchor}" if self.section.anchor else f"'{self.section.title}'"
        if not self.changed:
            # RK1109. `unchanged` at exit 0 is the one answer here with nothing in it to read:
            # the changed path lists its fields, so a caller sees `(title)` and knows the prose
            # was left alone, and this path listed nothing at all.
            aside = "" if read_body else f" — {unread_prose()}"
            return f"{named} unchanged: it already reads that way{aside}"
        counted = (
            f"  {self.section.counted(config.schema_for(self.role).section_max)}"
            if self.section.anchor
            else ""
        )
        rows = [
            f"{named} amended  {where}:{self.section.first}  "
            f"({', '.join(self.changed)}){counted}"
        ]
        rows += _staging_rows(config.relative(one) for one in wrote)
        return "\n".join(rows)

    def payload(
        self, config: Config, wrote: Sequence[Path], read_body: bool
    ) -> dict[str, object]:
        from roadkeep.rendering import _wrote_json  # noqa: PLC0415 - RK260

        return {
            **self.section.payload(config.relative(config.path(self.role))),
            "changed": list(self.changed),
            # The same fact as a field (RK1109): whether this call looked at the prose at all.
            # `changed: []` says nothing moved and cannot say why, which is the ambiguity a
            # piped body and a `--title` land in together.
            "read_body": read_body,
            **_wrote_json(config, wrote),
        }


def drop(
    document: Document,
    anchor: str,
    *,
    claimed: Mapping[str, Sequence[str]] | None = None,
    where: str = "",
) -> Deleted:
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
    return Deleted(
        document.remove_lines(start, end),
        section,
        cited=cited,
        # The subtree, from the list the deletion itself was computed from — the door
        # used to read it again with a second reader (RK1170).
        nested=leaving[1:],
        where=where,
    )


def add(
    config: Config,
    role: str,
    anchor: str,
    title: str,
    body: str,
    *,
    level: int | None = None,
    task: Task | None = None,
    opens: tuple[str, str] | None = None,
) -> Written:
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

    ``opens`` is the family this same write declares first, as ``(anchor, title)`` (RK1258) —
    the one caller being a block's **first** task, whose child address extends a top level no
    prose file has opened. Without it that call is refused (:class:`UnknownParent`) and the
    only address available is the family itself, so a block's first design was filed *as* the
    family heading and every later one as a child of it: two shapes for one thing, and the
    difference was never a choice anybody made. What is opened is a **container** — a heading
    and no prose — which is the ordinary structure of a rationale file and the one shape
    ``body.empty`` does not name, that finding being about a leaf a pointer resolves to.
    """
    document = config.document(role)
    where = config.relative(config.path(role))
    if task is None:
        task = _task_for(config, anchor)
    # Bound before it is checked and before it is rendered, so the title this function
    # validates is the one it writes (RK262) — a heading checked in one spelling and filed
    # in another is the disagreement L3 refuses a file over.
    title = _bound(document.schema, anchor, title, task)
    # The files are read only where nothing live answered *and* the anchor is an id (RK238,
    # narrowed by RK240): a section written for an open line, or under an outline anchor,
    # costs no second parse for a door it will never be handed.
    try:
        _check(
            document.schema,
            anchor,
            title,
            body,
            task,
            elsewhere=_elsewhere(config, document.schema, anchor, task),
            known=known(config, anchor, task),
            # The same question `amend` now asks (RK1227), so the two writers into one file
            # cannot come to disagree about which addresses a paragraph may cite.
            resolves=resolvable(config, anchor),
        )
    except SectionError as error:
        # The third door onto the same gap (RK349). `anchor.format` fires on the caller who
        # typed an id where this scheme numbers its own headings, and the address they now
        # need is the free child of this block's family — which is what the line writes have
        # been told since RK312. An anchor naming no task is answered too (RK360), with the
        # free top-level: that caller has no address at all, which is more and not less.
        raise naming_the_anchor(
            config,
            task.block if task is not None else None,
            error,
            namespace=document.schema.ref_prefix or "",
            anchor=anchor,
        ) from None
    unspent(config, role, anchor, document=document, where=where)

    # The file as it was read, for the delta :func:`_refuse_overflow` charges (RK1033).
    was = document
    # After every refusal the child can raise and before its placement is computed (RK1258):
    # the family has to exist for :func:`_extended` to find it, and a transaction that opened
    # one and then refused the design would leave a heading nobody asked for.
    if opens is not None:
        document = _opening(config, role, document, opens, where)
    lines = _render(document.schema, anchor, title, body, _depth(document, anchor, level))
    index = _placement(document, anchor, task, where, role)
    document = _inserted(document, index, lines)

    placed = find(document, anchor)
    assert placed is not None  # rendered by this function a moment ago
    _refuse_overflow(config, document, anchor, was)
    return Written(document, placed, role)


#: The second half of the overage refusal, by the door that raised it (RK1034). The
#: arithmetic above it is one number and is shared; what changes is the list of ways out,
#: which is what a refusal is *for* — and RK1033 shipped `add`'s list at both doors.
#:
#: At an `add` the address has not been chosen, so "put it somewhere else" is one flag away.
#: At an `amend` the section is already there and the prose being handed over replaces prose
#: that exists: `anchors --next` opens nothing, and taking the subtree elsewhere is `section
#: move`, a different act with consequences for every pointer at it. What is left is shorten
#: this, or shorten the parent — and the second is invisible from here, the overage being the
#: parent's while the paragraph in front of the caller is the child's.
_WAYS_OUT = {
    "add": (
        "a subsection is charged to the address that owns it, so this prose belongs at a "
        "free top-level anchor (`anchors --next`) rather than under §{parent}"
    ),
    "amend": (
        "the overage is §{parent}'s and this paragraph is §{anchor}'s, so the ways out are "
        "shortening this body or amending §{parent}'s own prose — `section move {anchor} "
        "--to <free anchor>` is what takes the subtree out from under it"
    ),
}


def _refuse_overflow(
    config: Config,
    document: Document,
    anchor: str,
    before: Document | None = None,
    door: str = "add",
) -> None:
    """Refuse a write that leaves an ancestor over its own limit and worse than it was.

    RK1024 for an `add`, and RK1033 for the `amend` that door left open — which is the one an
    author reaches more often, a design being amended more than once and written once.

    `add` opens its help with the promise that nothing is written unless every field passes,
    because *a limit reported after the prose exists is a limit discovered too late to save
    the tokens it was meant to save*. Charged on the child alone, that promise was false for
    every nested address: measured in one sitting, `anchors --block AJ` offered `§L.1`,
    `budget` reported 51 words left, `add` **accepted** a 278-word section, and `lint` then
    failed the parent by 277. `§L` was 299 words of its own 300 — so every child of it,
    including an empty one, was over before a word of it was composed, and no writer said so.

    Measured against the file this call has already built rather than against a sum, so the
    number is the one the gate will read: the walk is the same :func:`find`, the limit is the
    same `section_max`, and the pointer decides the charge exactly as `_pointed_at` says
    (RK215). An ancestor nothing points at is a container, and counting its children against
    it here would refuse prose the gate calls clean — which is the disagreement that made
    this a defect rather than a limit.

    Every ancestor and not only the immediate one: `L.1.2` is inside `L.1` and inside `L`,
    and a parent with room under a grandparent with none is still a write `lint` fails.

    ``before`` is the file as it was read, and it makes the rule a **delta** rather than a
    state: a shorter body that leaves an already-over parent over is a correction in the
    right direction, and refusing it is RK215's deadlock exactly — every door closed and the
    file left saying something untrue. So what is refused is a write that makes the total
    worse, never one that arrives at a file somebody else left over. An `add` passes it too:
    a section body cannot be empty, so an insert is always worse by its own words, and
    stating the rule once is what keeps the two doors from disagreeing about it.
    """
    limit = document.schema.section_max
    parent = _parent(anchor)
    while parent:
        whole = find(document, parent)
        if whole is None or whole.words <= limit or not _pointed_at(config, parent):
            parent = _parent(parent)
            continue
        was = find(before, parent) if before is not None else None
        if was is not None and whole.words <= was.words:
            parent = _parent(parent)
            continue
        raise SectionError(
            (
                Violation(
                    "body.too-long",
                    "body",
                    f"§{parent} would be "
                    f"{over_by(whole.words, limit, unit='word', because=' with this section under it')}"
                    f" — {_WAYS_OUT[door].format(parent=parent, anchor=anchor)}",
                ),
            )
        )


def unspent(config: Config, role: str, anchor: str, *, document: Document, where: str) -> None:
    """Refuse an address anything has already taken — this file, a sibling, or history.

    The three questions `add` asks about a destination, asked once (RK377). `move` asks the
    same three about the address it is re-writing to, and a second call site spelling them out
    is how one door comes to refuse what the other writes: the whole reason RK302 exists is
    that the doubling check was made against the file being written and not against the
    project, and a repair verb that inherited two of the three would recreate the state it was
    added to fix.

    ``document`` is the caller's own parse rather than a fourth read of the same file: both
    callers already hold it, and reading it again is what makes two readings possible.
    """
    existing = find(document, anchor)
    if existing is not None:
        raise SectionExists(anchor, where, existing.first)
    _refuse_doubling(config, role, anchor)
    _refuse_reuse(config, role, anchor, where)


def _refuse_doubling(config: Config, role: str, anchor: str) -> None:
    """Refuse an anchor a **sibling** prose file already declares (RK302).

    :func:`_refuse_reuse` catches the address a heading in history spent, which is the case
    where history is the only witness. A live one is visible in the file next to it, and until
    this ran nothing looked: RK297 taught the *read* that an outline spans every declared prose
    file, and the write kept asking the document it was writing into.

    :func:`declaring` and not a fourth reading of the same question (RK229) — the one resolver
    three verbs already ask which file holds an anchor. The target role is skipped because the
    caller checked it a line earlier, against the document it has open, and that refusal names
    the file the author is writing to rather than one they did not mention.

    Both schemes, unlike :func:`_refuse_reuse`: under `id` the anchor is the id and
    :func:`~roadkeep.authoring.refuse_reuse` covers the roadmap, but two prose files can still
    hold `§RK2` between them, which is the same `section.ambiguous` by the same reading.
    """
    for other in declaring(config, anchor):
        if other == role:
            continue
        held = find(config.document(other), anchor)
        if held is not None:
            raise SectionExists(
                anchor,
                config.relative(config.path(other)),
                held.first,
                elsewhere=True,
            )


def _refuse_reuse(config: Config, role: str, anchor: str, where: str) -> None:
    """Refuse an outline address a heading in this file's history already spent (RK247).

    **Outline only.** Under the id scheme the anchor is the id, so reuse is refused one file
    over by `refuse_reuse` (RK4) and an anchor whose task shipped fails `anchor.unknown`
    before ever reaching here — a second check would be a second opinion about a closed
    question, on every `add --section` this project makes.

    Silence where history cannot answer, the rule every reader of it keeps: a shallow clone
    and a directory that is not a repository must not stop a write, and what is lost is a
    refusal and never a file. Imported here rather than at the top because `history` reads
    this module (RK260), and the cycle is only avoided at the direction the caller is in.
    """
    if config.schema_for(role).ref_scheme == "id":
        return
    from roadkeep.history import anchors, next_child  # noqa: PLC0415 - RK260

    # The project's addresses and not this file's (RK297): an outline spans every prose file
    # a project declares, so a write refused against one of them is a write that takes an
    # address the sibling spent — which is the doubled anchor, made by the check against it.
    taken = anchors(config)
    spent = next((one for one in taken if one.anchor == anchor and not one.live), None)
    if spent is None:
        return
    free = next_child(taken, anchor.rsplit(".", 1)[0]) if "." in anchor else ""
    raise AnchorRetired(anchor, spent.written_in, free, where)


def _refuse_subtree(document: Document, anchor: str, body: str) -> None:
    """Refuse a body that carries a subsection's own heading (RK1112).

    `show` prints the subtree and this verb replaces the own prose, so the obvious round-trip
    — show a section, correct one sentence, amend it back — arrived at the word limit instead:
    measured in claude-tray, 1692 words against 300 on a `§XXIII` with six subsections. That
    refusal is right about the number and says nothing about the cause, and an author reads
    *"a section this long is two sections"* as a verdict on prose they only meant to pass
    through. Asked **before** the limit, because a mistake about extent is not a mistake about
    length and the two have no remedy in common.

    Read off the file's own heading lines and never by parsing the pasted text: what a child's
    heading is, this document already decided, so the check is whether the body carries one of
    those strings — no second grammar for headings, and a body carrying none of them is prose
    however long. The remedy is the extent, so the message names both halves of it: the
    reader that prints what this verb takes, and the anchor a subsection is amended by.
    """
    lines = {line.strip() for line in body.splitlines() if line.strip()}
    for child in nested(document, anchor):
        heading = document.lines[child.first - 1].strip()
        if heading in lines:
            raise SectionError(
                (
                    Violation(
                        "body.subtree",
                        "body",
                        f"the body carries §{child.anchor}'s own heading, so this is "
                        f"§{anchor}'s subtree and not its prose: `section show {anchor} "
                        f"--own` prints the extent this replaces, and §{child.anchor} is "
                        f"amended by its own anchor",
                    ),
                )
            )


def amend(
    config: Config,
    role: str,
    anchor: str,
    *,
    title: str | None = None,
    body: str | None = None,
    substitute: Substitution | None = None,
) -> Rewritten:
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

    The anchor is not a field. An address is `renumber`'s (RK97) under the id scheme and
    :func:`move`'s under an outline (RK377), and either way a section that changed anchor is a
    section every pointer at it has to change with — which is a transaction and not a field.

    A rewrite that leaves nothing of the original is **not** refused, and the question the
    design left open is answered here: the falsifiable claim is the `symptom` on the task
    line, which `amend` already refuses to touch (RK7). A rationale rewritten under an
    unchanged symptom is still that symptom's rationale; one rewritten because the symptom
    changed is a line the other verb will not let you rewrite. A second guard here would be
    a second opinion about a question already answered one file over.

    ``substitute`` is the **narrow** form of the same write (RK1263): one string out, one in,
    derived from the prose already on disk so a table or a fence is never retyped. What it
    changes about the rules is one thing, and it is the reason this parameter is not just sugar
    at the verb layer — a section already over the word limit for reasons the edit has nothing
    to do with was refused for a four-character correction, and the way out was shortening
    prose the caller never came to touch. So an edit that does not *grow* the prose inherits
    the overrun instead of being charged it, which is `lint --baseline`'s argument arriving at
    a door: the standing debt stays a finding, and this call is not what it is about. Only
    here, because only here is the growth bounded by the replacement's own delta — a
    whole-body rewrite that happens to come back no longer is still a body somebody composed.
    """
    document = config.document(role)
    span = _span(document, anchor)
    section = find(document, anchor)
    if span is None or section is None:
        raise NoSuchSection(anchor, config.relative(config.path(role)))
    _, _, heading = span
    # The one reading of "this section's own prose", off the record `find` already built
    # (RK1112): a second slice here is the second answer that let `show` print one extent and
    # this verb take another.
    own = section.prose
    if body is not None:
        _refuse_subtree(document, anchor, body)

    # Read before the no-op check rather than after it, because a `--title` has to be bound
    # before it can be compared (RK262): the title that differs from the file only by the id
    # it omits is a no-op, and comparing the unbound spelling would report a change and
    # rewrite the heading to the bytes it already holds. The cost is one roadmap parse on the
    # path that returns without writing, which is the rarest one here.
    owner = _task_for(config, anchor)
    # Only a title that was **passed** is bound. A body-only amend leaves the heading alone,
    # id or no id: correcting a paragraph is not the call in which a heading silently changes.
    wanted_title = (
        section.title if title is None else _bound(document.schema, anchor, title, owner)
    )
    # The prose on disk is what a substitution is applied to, which is the whole point: the
    # bytes the caller never named are the bytes that cannot be lost (RK1263).
    wanted_body = own if body is None else body
    if substitute is not None:
        wanted_body = substitute.applied(own, f"§{anchor}")
    changed = tuple(
        name
        for name, before, after in (
            ("title", section.title, wanted_title.strip()),
            ("body", own, _normalize(wanted_body)),
        )
        if before != after
    )
    if not changed:
        return Rewritten(document, section, (), role)

    _check(
        document.schema,
        anchor,
        wanted_title,
        wanted_body,
        owner,
        elsewhere=_elsewhere(config, document.schema, anchor, owner),
        known=known(config, anchor, owner),
        # The addresses this body may cite (RK1227), read from the project because `_check`
        # takes a schema and cannot.
        resolves=resolvable(config, anchor),
        # What the prose already spent, where this edit did not compose it (RK1263).
        standing=None if substitute is None else words(own),
    )
    updated = _rewrite(
        document,
        heading,
        replace(section, title=wanted_title.strip()),
        wanted_body,
        retitle="title" in changed,
    )
    amended = find(updated, anchor)
    assert amended is not None  # the heading this function just wrote
    # Charged against the subtree **only where a line points at this anchor**, which is
    # exactly what the gate charges (RK215). The subtree unconditionally was a writer holding
    # a file to a limit `lint` does not: measured in Claude Code Tray, a nine-word correction
    # to a two-sentence intro was refused for 934 words — 900 of them three live
    # subsections' — on a file that passes the gate. With `drop` refused by those same live
    # pointers and the guard denying the hand edit, every door was closed and the file left
    # saying something untrue, which is RK141's deadlock one level over.
    #
    # So an intro **is** a section like any other, which is the question the design left open:
    # `add` already writes a top-level anchor's own prose (RK166), `_rewrite` above already
    # replaces only that prose, and where nothing points at the anchor `_check` has already
    # charged it — so there is nothing further to ask.
    # And the same inheritance one measurement over (RK1263): the subtree is what a pointed-at
    # section is billed, so a narrow edit inside an already-over subtree is refused here for
    # words in somebody's subsections — which is the deadlock above with one more layer of
    # prose the caller never came to touch.
    if (
        _pointed_at(config, anchor)
        and amended.words > document.schema.section_max
        and not (substitute is not None and amended.words <= section.words)
    ):
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
    # The door RK1024 and RK1029 left open (RK1033): a rewrite of `§L.3` that puts `§L`
    # eighty words over was accepted and reported by `lint` afterwards, which is the
    # sequence both of those closed at `add`. The delta is what makes it safe here — an
    # amend is where the prose already exists, and refusing a *shortening* is RK215's
    # deadlock in the one direction an author can act in.
    _refuse_overflow(config, updated, anchor, document, door="amend")
    return Rewritten(updated, amended, changed, role)


def amend_untitled(
    config: Config,
    role: str,
    title: str,
    *,
    body: str | None = None,
    retitle: str | None = None,
    substitute: Substitution | None = None,
) -> Rewritten:
    """Rewrite an unanchored section's prose or its heading, in place (RK1107).

    :func:`amend`'s twin for the two regions a prose file has that carry no address — its
    opening, and a `## Table of contents`. The same three properties and one fewer: own prose
    and never the subtree, nothing written unless something changed, and **no `owner`** —
    an unanchored section belongs to no task, so there is no id to bind into the heading and no
    pointer that a re-titling has to move with it. That last is the whole reason this is a
    second function rather than a branch in the first: `amend`'s body is about the anchor, the
    task that owns it, and the budget the two decide between them, and an unanchored section
    has none of the three.

    Not budgeted, deliberately. `section = <n>` is what a *rationale* may spend, measured
    against a corpus of rationale sections; a file's opening paragraph and a contents table are
    neither, and charging them a limit nobody measured them against is how a ceiling comes to
    refuse the prose it was derived from. What holds them is `[budgets]` on the whole file,
    which already counts every byte of both.
    """
    document = config.document(role)
    heading = titled(document, title)
    if heading is None:
        raise NoSuchSection(title, config.relative(config.path(role)))
    end = document.prose_end(heading)
    own = "".join(document.lines[heading.lineno : end]).strip("\r\n")
    section = Section(
        anchor="",
        title=heading.text.strip(),
        level=heading.level,
        first=heading.lineno,
        last=end,
        body=own,
    )
    wanted_title = section.title if retitle is None else retitle.strip()
    # The narrow form reaches here too (RK1263), and this is the region it is most obviously
    # for: a `## Table of contents` is a table whose every row is a heading somebody's ship
    # moved, and retyping the whole of it to correct one row is the risk that task is about.
    wanted_body = own if body is None else body
    if substitute is not None:
        wanted_body = substitute.applied(own, repr(section.title))
    changed = tuple(
        name
        for name, before, after in (
            ("title", section.title, wanted_title),
            ("body", own, _normalize(wanted_body)),
        )
        if before != after
    )
    if not changed:
        return Rewritten(document, section, (), role)
    if not wanted_title:
        raise SectionError(
            (
                Violation(
                    "title.empty",
                    "title",
                    "an unanchored section is addressed by its heading, so a blank one "
                    "leaves it with no address at all",
                ),
            )
        )
    updated = _rewrite(
        document,
        heading,
        replace(section, title=wanted_title),
        wanted_body,
        retitle="title" in changed,
    )
    return Rewritten(
        updated,
        replace(section, title=wanted_title, body=_normalize(wanted_body)),
        changed,
        role,
    )


#: The governed files whose lines carry a `→ §<anchor>`, which is the end of a pointer a
#: re-address has to move with the heading. The deferred store is one (RK96): pausing a line
#: keeps its section, so its pointer is as live as the roadmap's and the gate reads both.
POINTING_ROLES = ("roadmap", "deferred")


@dataclass(frozen=True, slots=True)
class Moved:
    """Every edit one section's change of address makes, as data, before it is written."""

    anchor: str
    to: str
    role: str
    #: The section as it now reads, at its new address.
    section: Section
    #: The nested addresses re-written with it, `(before, after)` in file order.
    subsections: tuple[tuple[str, str], ...] = ()
    #: The governed files this write leaves changed, by role. A mapping and not named fields
    #: for :class:`~roadkeep.renumbering.Renumbering`'s reason: which files are in it is a
    #: property of the project, a deferred store being optional and a pointer being a line
    #: some backlogs carry none of.
    documents: Mapping[str, Document] = field(default_factory=dict)
    #: Every line whose pointer followed, as `(id, address)`. Its own address and not the
    #: named one: a line pointing at a subsection follows to `§I.11.1` while the section this
    #: was called about lands at `§I.11`, and one destination for both would be a report
    #: nobody can check against the file. Named and never silent — a pointer is the other end
    #: of the address that moved, and the author is who can say whether it should have.
    repointed: tuple[tuple[str, str], ...] = ()
    #: Lines left pointing at the old address because a sibling prose file still declares it,
    #: as `(id, address)` — the doubling this verb is usually called for, resolving to the
    #: section that stayed rather than following the one that moved.
    kept: tuple[tuple[str, str], ...] = ()
    #: Sections whose **prose** still cites an address that moved, as `(address, by)`.
    #: Reported and never rewritten, for the reason `drop` reports the same thing: a pointer
    #: is a promise the format makes and a citation is a sentence (L4).
    cited: tuple[tuple[str, str], ...] = ()

    def save(self) -> tuple[Path, ...]:
        """Write every file this move touched, and answer them all (RK1130)."""
        return save_all(*self.documents.values())

    def stated(self, config: Config, wrote: Sequence[Path]) -> str:
        """Where the address went, and every line that followed it (RK377).

        Beside :meth:`payload` since RK1170. Four lists and never a count: a pointer is the
        other end of an address that moved, and the line that changed is the one whose author
        has to agree it should have (RK97).
        """
        from roadkeep.rendering import _staging_rows  # noqa: PLC0415 - RK260

        where = config.relative(config.path(self.role))
        rows = [
            f"§{self.anchor} → §{self.to}  {where}:{self.section.first}",
            *(f"  nested   §{before} → §{after}" for before, after in self.subsections),
            *(f"  pointer  {one} follows it to §{a}" for one, a in self.repointed),
            # The doubling this verb is usually called for: the address still resolves, to the
            # section that stayed, and that is the answer rather than a thing left half done.
            *(
                f"  kept     {one} still points at §{a}, which the other file declares"
                for one, a in self.kept
            ),
            *(
                f"  cited    §{by} names §{a} in its prose — that address has moved"
                for a, by in self.cited
            ),
        ]
        rows += _staging_rows(config.relative(one) for one in wrote)
        return "\n".join(rows)

    def payload(self, config: Config, wrote: Sequence[Path]) -> dict[str, object]:
        """The same answer as data, with each list as pairs a caller can act on."""
        from roadkeep.rendering import _wrote_json  # noqa: PLC0415 - RK260

        where = config.relative(config.path(self.role))
        return {
            **self.section.payload(where),
            "from": self.anchor,
            "subsections": [
                {"from": before, "to": after} for before, after in self.subsections
            ],
            "repointed": [{"id": one, "to": a} for one, a in self.repointed],
            "kept": [{"id": one, "address": a} for one, a in self.kept],
            "cited": [{"address": a, "by": by} for a, by in self.cited],
            **_wrote_json(config, wrote),
        }


def move(config: Config, role: str, anchor: str, to: str) -> Moved:
    """Re-address one live section, its own subtree and every pointer at it (RK377).

    The verb an outline had none of. `renumber` moves an **id**, and keeps the pointer as
    typed wherever the scheme is not `id` — which is precisely the scheme a project with a
    hand-kept outline is on — so a doubled address, the thing `lint` reports as
    `section.ambiguous` and the write path refuses to create, was repairable only by the hand
    edit the guard denies. Turing adopted the tool with 13 of them.

    Everything the address owns, or nothing. The heading, every nested anchor that
    :func:`descending` says is this one's own numbering, and the `→ §<anchor>` on every line
    in :data:`POINTING_ROLES` naming one of them, validated before a file is touched — a
    re-address that moved the heading and not the pointer is the dangling reference this
    module exists to prevent, one verb over.

    The destination takes :func:`unspent`, which is every refusal `add` computes about an
    address: taken here, declared by a sibling prose file, or spent by a heading in this
    file's history. Each **new** address is asked, not only the named one, because a
    subsection's is derived from its parent's and a collision on `§I.14.1` is the same
    collision one segment down.

    **A pointer follows the section when nothing else answers its address, or when this
    heading names its task.** Both halves are readings this module already makes, and neither
    is a guess. The ordinary re-address is the first: nothing else declares the old address,
    so a pointer left behind is the dangling reference, and it moves. The doubling this verb
    exists for is the second, and moving every pointer there would be exactly wrong — the
    address resolved to two sections, one of them names the task in its heading
    (:func:`owners`), and repairing the *other* file must leave that line pointing where its
    design still is. What stays is reported as :attr:`Moved.kept`, because a line the caller
    expected to move and that did not is the half of the answer the files no longer state.

    What it does not do is move prose. The section stays exactly where it is in the file and
    only its address changes, which is why :class:`NotASibling` bounds the destination to the
    parent the source already had — see that class for why the two cannot be separated.
    """
    document = config.document(role)
    where = config.relative(config.path(role))
    schema = document.schema
    if schema.ref_scheme == "id":
        raise AnchorIsId(anchor, where)
    section = find(document, anchor)
    if section is None:
        raise NoSuchSection(anchor, where)
    # The project's spelling of the address and not the caller's: `find` resolves a bare `I.2`
    # in a namespaced file, and every comparison below is against anchors :func:`anchored`
    # already qualified (RK340).
    anchor = section.anchor
    if (bad := _address_violation(schema, to)) is not None:
        raise SectionError((bad,))
    if to == anchor:
        raise SameAnchor(anchor)
    if _parent(to) != _parent(anchor):
        raise NotASibling(anchor, to, _parent(anchor))

    children = descending(document, anchor)
    subsections = tuple(
        (child.anchor, f"{to}{child.anchor[len(anchor) :]}") for child in children
    )
    for address in (to, *(after for _, after in subsections)):
        unspent(config, role, address, document=document, where=where)

    ids = schema.id_pattern()
    carried = {
        moving.anchor: Carried(
            to=after,
            owns=owners(moving, ids),
            # Whichever files answer the old address once this one stops: empty is the plain
            # re-address, where a pointer left behind resolves to nothing.
            answered_by=tuple(r for r in declaring(config, moving.anchor) if r != role),
        )
        for moving, after in ((section, to), *zip(children, (a for _, a in subsections), strict=True))
    }
    # Read before the rewrite, while the prose and the addresses it names still agree. Nothing
    # is ignored: a citation inside the moving subtree is as stale afterwards as one outside it.
    cited = citing(document, tuple(carried))
    # By line number and applied to a document that reparses, which is why the headings are
    # collected first: one `replace_line` is one line for one line, so no heading below an edit
    # has moved under the edits above it (the care :func:`_rewrite` takes for the same reason).
    updated = document.replace_line(
        section.first - 1, heading_of(schema, replace(section, anchor=to))
    )
    for child, after in zip(children, (after for _, after in subsections), strict=True):
        updated = updated.replace_line(
            child.first - 1, heading_of(schema, replace(child, anchor=after))
        )
    documents: dict[str, Document] = {role: updated}
    repointed, kept = _repoint(config, carried, documents)

    landed = find(updated, to)
    assert landed is not None  # the heading this function wrote a moment ago
    return Moved(
        anchor=anchor,
        to=to,
        role=role,
        section=landed,
        subsections=subsections,
        documents=documents,
        repointed=repointed,
        kept=kept,
        cited=cited,
    )


@dataclass(frozen=True, slots=True)
class Carried:
    """One address on the move, and what decides whether a pointer at it goes too (RK377)."""

    to: str
    #: The task ids this heading names, which is the claim to be their design (:func:`owners`).
    owns: tuple[str, ...]
    #: The other prose roles still declaring the address after this write — the doubling.
    answered_by: tuple[str, ...]

    def follows(self, task_id: str) -> bool:
        """Whether this line's pointer moves with the heading — see :func:`move`."""
        return not self.answered_by or task_id in self.owns


def _repoint(
    config: Config, carried: Mapping[str, Carried], documents: dict[str, Document]
) -> tuple[tuple[tuple[str, str], ...], tuple[tuple[str, str], ...]]:
    """Rewrite every `→ §<old>` that follows its heading, by line file (RK377).

    Which lines those are is read once, before any of them is rewritten, and re-fetched by id
    inside the loop: `replace_task` reparses, so an entry held across an edit is one whose line
    number may already have moved — the care every mutator in :mod:`roadkeep.kernel.document` takes.

    Through `schema.check`, which is what refuses a longer address that pushes the rendered
    line past its limit. That refusal belongs here rather than after the write: a pointer left
    behind because the line would not fit is the dangling reference, and this transaction has
    touched nothing yet.
    """
    moved: list[tuple[str, str]] = []
    stayed: list[tuple[str, str]] = []
    for name in POINTING_ROLES:
        if not config.has(name) or not config.path(name).is_file():
            continue
        lines = config.document(name)
        pointing = _following(lines, carried, stayed)
        for task_id in pointing:
            current = next(e for e in lines.entries if e.task.id == task_id)
            lines = lines.replace_task(
                current,
                lines.schema.check(
                    replace(current.task, ref=carried[current.task.ref].to)
                ),
            )
        if pointing:
            documents[name] = lines
            moved.extend((one, carried[ref].to) for one, ref in pointing.items())
    return tuple(moved), tuple(stayed)


def _following(
    lines: Document, carried: Mapping[str, Carried], stayed: list[tuple[str, str]]
) -> dict[str, str]:
    """Which of this file's lines follow their heading, by id, and which are left behind."""
    out: dict[str, str] = {}
    for entry in lines.entries:
        one = carried.get(entry.task.ref)
        if one is None:
            continue
        if one.follows(entry.task.id):
            out[entry.task.id] = entry.task.ref
        else:
            stayed.append((entry.task.id, entry.task.ref))
    return out


def _parent(anchor: str) -> str:
    """The address one segment up — `S:I.2` → `S:I`, and `''` for a top level.

    The namespace is not a segment (RK340): `S:I` is one address whose separator is a colon,
    so a top level keeps its prefix and answers `''` here like any other.
    """
    return anchor.rsplit(".", 1)[0] if "." in anchor else ""


def _rewrite(
    document: Document,
    heading: Heading,
    section: Section,
    body: str,
    *,
    retitle: bool = True,
) -> Document:
    """Swap a heading's line and the prose under it for the reflowed replacement.

    One removal and one insertion per line rather than a patch, because every mutator in
    :mod:`roadkeep.kernel.document` reparses — so the region is taken out first and the new lines
    go in at the heading's own index, where nothing below has moved yet.

    ``retitle`` is false where only the prose changed, and then the heading line is not
    touched at all (RK388). It used to be re-rendered unconditionally, and under an outline
    that is a **silent rewrite of something nobody named**: the reader accepts `## §I A
    design` because a sigil an author wrote is not a spelling to punish (RK44), and
    :func:`anchor_text` then writes the canonical `## I A design` — so a `section amend
    --body` on any section in the file took the `§` off the one it was passed, along with
    whatever spacing that heading had. `lint` called the result clean, because L3 is held
    over task lines and a prose file has none.

    Of the three repairs the design weighed — refuse the file, make the sigil canonical, or
    narrow the reader — this is a fourth, and it is the one that costs nothing: the writer
    stops reproducing a line it was not asked about. An amend that *does* pass `--title` is
    the caller asking for the heading to change, and there the canonical spelling is right.
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
    if not retitle:
        return updated
    # The heading last and through :func:`heading_of`, so the one writer of that spelling
    # stays one (RK44) — an amend that composed it here would be the second.
    return updated.replace_line(heading.lineno - 1, heading_of(document.schema, section))


def paragraphs(body: str) -> tuple[int, ...]:
    """What each paragraph of a body costs, in the same unit :func:`words` charges (RK311).

    The half a refusal was missing. `budget` prices the ceiling before a word exists, which
    is the right half and the one L1 is about; what had no answer was a draft that already
    exists — measured over one session of thirteen filings, **fifteen** `body.too-long`
    refusals, three of them over one or two words, each discarding about 250 words to remove
    a handful. The overage alone does not shorten the second attempt: it says a cut is needed
    and leaves the author counting by hand for somewhere to make it, against a number this
    module has already computed exactly.

    So the refusal says **where**. Paragraphs are blank-line separated, a fenced block is one
    paragraph however many blanks are inside it, and each is charged by the same reading the
    limit uses — so the three shapes :func:`words` exempts show as `0` rather than as
    something a cut could reach. That zero is the answer to the other half of the question: a
    section over the limit whose longest paragraph is a table is not one to split.
    """
    out: list[int] = []
    current: list[str] = []
    fence: str | None = None
    for raw in body.splitlines():
        line = raw.lstrip()
        if fence is not None:
            current.append(raw)
            if line.startswith(fence):
                fence = None
            continue
        if line.startswith(_FENCES):
            # A fence opens *inside* whatever paragraph is being read, so an intro line and
            # the block under it stay one unit — which is how the author sees them.
            fence = line[:3]
            current.append(raw)
            continue
        if not line:
            if current:
                out.append(words("\n".join(current)))
                current = []
            continue
        current.append(raw)
    if current:
        out.append(words("\n".join(current)))
    return tuple(out)


def _where_the_words_are(body: str) -> str:
    """The per-paragraph counts, as the clause a refusal ends with (RK311).

    Named for what it answers rather than for what it formats: the author has been told a cut
    is needed and this is the sentence that says where one is available. Silent on a
    single-paragraph body — "¶1 335" restates the total the same message already gave, and a
    refusal that repeats itself is one an author stops reading.
    """
    counted = paragraphs(body)
    if len(counted) < 2:
        return ""
    listed = ", ".join(f"¶{n} {count}" for n, count in enumerate(counted, 1))
    # The longest is named because it is the one the author is looking for, and a tie names
    # the first — the cut has to start somewhere and the file reads top down.
    fattest = counted.index(max(counted)) + 1
    return f"; by paragraph {listed} — ¶{fattest} is the longest"


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


#: The violations that are an author holding no address, and that `anchors` answers (RK349).
#: `ref.missing` is a line with no pointer and `anchor.format` a section written at one that
#: is not an address at all; both leave the caller looking for the same free number, and both
#: used to state a rule and name nothing that satisfies it.
_UNANCHORED = ("ref.missing", "anchor.format")


@dataclass(frozen=True, slots=True)
class Namespaced:
    """A prose file's addresses moved into a namespace, with its own citations carried (RK1168).

    Declaring `[refs]` re-addresses every heading in a file at once — 48 of them in the run this
    was measured on — and carried none of that file's own citations: seven dangled and twenty-one
    kept resolving, into the other file's section of the same address. The first half of this task
    made the second population a finding (`ref.crossed`); this is the transaction that stops
    creating it.

    **Why it has to be one act.** At the moment the key is declared, every bare citation in that
    file *was* local by construction — they resolved to it before the namespace existed, which is
    what a namespace changes. A minute later the same citation is ambiguous, which is why the
    finding's remedy is `compose` and this one can be a rewrite: the transaction is what makes the
    answer knowable, and outside it nobody can say which section was meant.

    An address and never a word of prose (L4): what changes is `§I.2` to `§S:I.2` inside a
    sentence nobody else touches — the same act `move` performs on the pointers at a section.
    """

    role: str
    namespace: str
    #: The file, with the citations rewritten. Saved by the caller, so the config write and this
    #: one land together or not at all.
    document: Document
    #: What was re-addressed, as `(anchor, line)`, so the report names every one.
    carried: tuple[tuple[str, int], ...]
    #: The configuration as it will read, rendered from the file that is there — a targeted
    #: insertion and never a serialiser, for `bump_version`'s reason: the rest of somebody's
    #: `roadkeep.toml` has to come back byte-identical.
    config_text: str

    def stated(self, config: Config, wrote: Sequence[Path]) -> str:
        """The key declared, and every citation carried into it (RK1168).

        Beside :meth:`payload` since RK1170. The config's own path joins the staging line here
        and not in :attr:`config_text`'s write: it is the file this transaction's *other* half
        touched, and a commit that staged the prose and left the key is the half-declared state.
        """
        from roadkeep.rendering import _staging_rows  # noqa: PLC0415 - RK260

        where = config.relative(config.path(self.role))
        source = config.relative(config.source)
        rows = [f'{source}  [refs] {self.role} = "{self.namespace}"']
        # Named and not counted: this is a rewrite inside somebody's prose, and a number alone
        # is the diff a reviewer has to reconstruct to see what moved.
        rows += [
            f"  carried  §{anchor} → §{self.namespace}:{anchor}  ({where}:{line})"
            for anchor, line in self.carried
        ]
        if not self.carried:
            rows.append(f"  carried  nothing: {where} cites none of its own sections")
        rows += _staging_rows([where, source])
        return "\n".join(rows)

    def payload(self, config: Config, wrote: Sequence[Path]) -> dict[str, object]:
        """The same answer as data, naming both files the transaction wrote."""
        from roadkeep.rendering import _wrote_json  # noqa: PLC0415 - RK260

        return {
            "role": self.role,
            "namespace": self.namespace,
            "file": config.relative(config.path(self.role)),
            "config": config.relative(config.source),
            "carried": [
                {"anchor": anchor, "line": line} for anchor, line in self.carried
            ],
            **_wrote_json(config, (*wrote, config.source)),
        }


def namespaced(config: Config, role: str, prefix: str) -> Namespaced:
    """Declare `[refs] <role>` and carry that file's own citations into it (RK1168).

    Refuses rather than guesses in the three states it cannot answer for: a role this project
    does not declare as prose, a namespace this project already gives that role — where every
    citation is already qualified and there is nothing to carry — and a *different* namespace,
    which is a re-addressing whose citations carry the old prefix and whose answer is a different
    transaction from this one.
    """
    if role not in PROSE_ROLES or not config.has(role):
        raise ValueError(
            f"{role} is not a prose file this project declares: `[refs]` names the namespace a "
            f"prose file's outline lives in, and the roles are {', '.join(sorted(PROSE_ROLES))}"
        )
    if not _NAMESPACE_RE.match(prefix):
        raise ValueError(
            f"'{prefix}' is not a namespace: one is the letters and digits before the colon of "
            f"an address like `S:I.2`, and a separator inside it would be a second address"
        )
    already = config.refs.get(role)
    if already == prefix:
        raise ValueError(
            f"{role} already lives in `{prefix}:`, so its citations are already qualified and "
            f"there is nothing to carry"
        )
    if already:
        raise ValueError(
            f"{role} already lives in `{already}:`, and moving it to `{prefix}:` re-addresses "
            f"citations that carry the old namespace — a different transaction from declaring one"
        )
    document = config.document(role)
    own = {section.anchor for section in anchored(document)}
    carried: list[tuple[str, int]] = []
    for cited in references(document):
        # The file's **own** addresses and no others, read as they stand *before* the key is
        # declared — which is the whole reason this is one transaction: right now a bare anchor
        # this file declares is unambiguously its own, and a citation of the other file's section
        # is already right and must not be moved into a namespace it has no section in.
        if cited.anchor not in own:
            continue
        at = cited.lineno - 1
        replaced = document.lines[at].replace(f"§{cited.anchor}", f"§{prefix}:{cited.anchor}")
        if replaced == document.lines[at]:
            continue
        carried.append((cited.anchor, cited.lineno))
        document = document.replace_line(at, replaced)
    return Namespaced(
        role=role,
        namespace=prefix,
        document=document,
        carried=tuple(carried),
        config_text=_with_namespace(config, role, prefix),
    )


#: What a namespace may be: the letters and digits before the colon of an address (RK340). A
#: separator inside one would make `S:I` two addresses rather than one.
_NAMESPACE_RE = re.compile(r"^[A-Za-z0-9]+$")


def _with_namespace(config: Config, role: str, prefix: str) -> str:
    """This project's `roadkeep.toml` with one key added, and every other byte as it was.

    A targeted insertion and never a serialiser, which is `bump_version`'s rule about the two
    files that state a version: a `tomllib` round-trip is not one — it drops the comments a
    scaffolded config is mostly made of, and rewriting somebody's file to add a line is the
    destructive formatting L3 refuses one layer down.
    """
    if config.source is None:
        raise ValueError("this project declares no roadkeep.toml to add a namespace to")
    text = config.source.read_text(encoding="utf-8")
    row = f'{role} = "{prefix}"\n'
    if "\n[refs]\n" in text or text.startswith("[refs]\n"):
        at = text.index("[refs]\n") + len("[refs]\n")
        return text[:at] + row + text[at:]
    # A table of its own, at the end: a key appended under whatever table happens to be last
    # would belong to that table, which is the one way this write can be silently wrong.
    joined = "" if text.endswith("\n") else "\n"
    return f"{text}{joined}\n[refs]\n{row}"


def naming_the_anchor(
    config: Config,
    block: str | None,
    error: SchemaError,
    *,
    namespace: str = "",
    anchor: str = "",
) -> SchemaError:
    """The same refusal, told which command answers it (RK312, widened by RK349).

    This project's own standard applied to itself. `ref: every task points at its rationale
    section` states the rule and names nothing that satisfies it — and `--ref` is the one
    required field of the write path that is neither derived nor guessable, wrong *silently*
    if the number picked is one some heading already spent. `anchors` answers it exactly, and
    there was no way to learn that from the refusal; the two reads it replaced were a glob of
    the pointers per block and a grep of the prose file's headings, done four times by hand.

    Here rather than in `authoring`, which is where RK312 wrote it, because the doors that
    reach it are on both sides of that import: `place` validates the line `add`, `defer` and
    `resume` each write, and :func:`add` below validates the anchor `section add` passes.
    One function, so a fifth door is a call and not a fifth copy of the sentence.

    Every other violation rides through untouched, the error keeps its own class, and the
    sentence is **appended** rather than replaced: what the rule is has to survive, because
    a refusal that only says what to type teaches nobody why the field exists.

    ``block`` is `None` where the anchor names no live task, and that is not the caller to
    stay silent for (RK360) — it is the one holding no address at all, since typing a task id
    is what produces a block to read. What changes is which address is offered, and that is
    :func:`_where_a_top_level_is`'s to decide from the anchor itself: a family the caller
    already typed gets its next child, and everything else gets the free top-level. Never a
    family derived from whichever one happened to be last, which is the guess the two-family
    branch below also refuses to make.

    Silent where history cannot be searched, which is where the free address cannot be
    derived: naming a number this could not verify is the failure the whole read exists to
    prevent, and the command that can say so is still named.
    """
    named = tuple(one for one in error.violations if one.code in _UNANCHORED)
    if not named:
        return error
    clause, free = (
        _where_a_top_level_is(config, namespace, anchor)
        if block is None
        else _where_the_anchor_is(config, block)
    )
    refusal = type(error)(
        tuple(
            replace(one, message=f"{one.message}{clause}") if one in named else one
            for one in error.violations
        )
    )
    # The address as **data** on the refusal, for the surface that can turn it into a retry
    # (RK1149). On the exception and not in a slot somewhere: it is one refusal's fact, it
    # travels with the object that carries the refusal, and a reader that finds no attribute
    # gets today's behaviour rather than a stale answer about an earlier call.
    if free:
        refusal.offered = free
    return refusal


def checked(config: Config, task: Task, *, schema: Schema | None = None) -> Task:
    """`schema.check`, with the anchor named — the seam a **rewrite** passes (RK379).

    RK312 enriched the refusal an `add` raises and RK349 widened it to the other doors that
    *insert* a line, by putting the call in :func:`~roadkeep.authoring.place`. Every door that
    rewrites a line already on the file misses that seam entirely: `amend`, `restate`, `status`
    and `renumber` each validate the task they composed and none of them goes through `place`.

    So the bare rule survived exactly where an adopting project meets it. `ref.missing` on an
    insertion is a field the author forgot; on a rewrite it is a line that was **imported
    without a pointer**, which is the whole population `amend` exists for — the author is
    correcting that line's `why`, is told a pointer is required, and is told nothing about
    which address is free. That is the same measured cost RK312 removed, on the door the
    correction path actually uses.

    Not folded into `place`, which takes a :class:`~roadkeep.kernel.document.Document` and an optional
    config: these callers hold a :class:`Config` unconditionally, and a rewrite has no
    insertion to make. The enrichment stays :func:`naming_the_anchor`, so this is a call and
    still not a copy of the sentence.

    ``schema`` is which grammar validates, and it is a parameter because `renumber` moves an
    id that may be the **ledger's**: a shipped entry is `as_ledger()`, which requires no
    pointer at all, and validating one against the roadmap's schema would refuse an entry for
    lacking a field its own file has no column for. The default is this project's roadmap
    schema, which is every other caller.
    """
    try:
        return (schema or config.schema).check(task)
    except SchemaError as error:
        raise naming_the_anchor(config, task.block, error) from None


def _where_the_anchor_is(config: Config, block: str) -> tuple[str, str]:
    """The clause an unanchored refusal ends with, and the address it offers (RK1149).

    A pair, because the sentence and the anchor are read by different surfaces: the clause is
    what a human reads and the anchor is what a **retry** needs, and until this the second only
    existed inside the first. `""` where none could be derived — the two cases this already
    refused to guess in — so a caller has nothing to substitute and says so by having nothing.
    """
    # Deferred for RK260's reason, and because git belongs on no successful write path.
    from roadkeep.history import (  # noqa: PLC0415
        HistoryUnavailable,
        anchors,
        families_of_block,
        next_child,
    )
    from roadkeep.provenance import invocation  # noqa: PLC0415

    spans = families_of_block(config, block)
    if len(spans) > 1:
        # A block that reopened under a fresh top-level. Two families is a real answer and the
        # tool must not pick between them (RK312), so the command that lists both is still the
        # whole of it — the one case here where the path forks on a judgement, and so the one
        # RK1198 leaves exactly as it was.
        return (
            f" — `{invocation()} anchors --block {block}` says which family this block's "
            f"prose lives under, and `anchors` alone names the free top-level"
        ), ""
    if not spans:
        # And none is a block whose prose has not started, which is not the same question
        # (RK1198): the two shared a sentence, and the sentence sent an author who was six
        # calls from a first write to a command that answers one of them.
        return _the_path_into(config, block)
    family = spans[0]
    try:
        free = next_child(anchors(config), family)
    except (HistoryUnavailable, OSError):
        return (
            f" — Block {block}'s prose is under §{family}, and "
            f"`{invocation()} anchors --family {family}` says which address is free"
        ), ""
    return (
        f" — Block {block}'s prose is under §{family}, where §{free} is free "
        f"(`{invocation()} anchors --block {block}` lists it)"
    ), free


def _the_path_into(config: Config, block: str) -> tuple[str, str]:
    """Every verb between this refusal and the line that lands, with its arguments (RK1198).

    Observed filing three tasks into a project whose `ref_scheme` is `outline`, into blocks
    whose every line had shipped. Each refusal was individually correct and named the next
    verb; together they were a staircase, and six calls stood between prose that was ready at
    call one and the first write. The information was there at the first refusal — it knew the
    block, whether a heading declared it, that its families were spent and what the next free
    top-level was, which is everything the remaining five calls established.

    So reporting one step is right when a caller is one step from done and wrong when they are
    six, because a staircase discovered a stair at a time reads as a tool changing its mind.
    The refusal carries the path rather than a `--plan` flag doing it, for the reason the
    whole clause exists: this is the moment the author is actually in, and a flag is one more
    thing to have learnt first.

    Filled in and not described: the block, the address and the ledger's own spelling are all
    derived here, so what is left in angle brackets is the title, which is editorial and L4's
    to leave alone. `""` for the address wherever the outline's numbering does not derive one
    — the same silence :func:`_where_a_top_level_is` keeps, since a path opening on a number
    this could not verify is worse than the command that reads it.
    """
    # Deferred for RK260's reason, and because git belongs on no successful write path.
    from roadkeep.authoring import prose_role  # noqa: PLC0415
    from roadkeep.blocking import BLOCK_ROLES  # noqa: PLC0415
    from roadkeep.history import (  # noqa: PLC0415
        HistoryUnavailable,
        anchors,
        next_child,
        next_family,
    )
    from roadkeep.provenance import invocation  # noqa: PLC0415

    role = prose_role(config, on_disk=True)
    started = f" — Block {block}'s prose has not started"
    try:
        taken = () if role is None else anchors(config)
    except (HistoryUnavailable, OSError):
        taken = ()
    family = None if role is None else next_family(taken, config.schema_for(role).ref_prefix)
    if family is None:
        # An outline with no family at all, one whose top-levels are not one numbering, or a
        # history that cannot be read: all three are numbers this could not verify, and a path
        # opening on a guessed address is worse than the command that reads the real one
        # (RK340, RK293).
        return (
            f"{started}, and `{invocation()} anchors` names the free top-level it opens at"
        ), ""
    # The task's design is a **child** of that family, through
    # :func:`~roadkeep.history.next_child` rather than spelled here, so the one writer of a
    # child address stays the one writer of it.
    free = next_child(taken, family)
    steps = [
        # The family first, and it is the stair nobody sees coming: `section add <free>`
        # refuses with nothing to extend, and so does an `add --section` naming the same
        # address, because an anchor states its own place and a fresh top-level has no prose
        # yet. A free family exists nowhere by construction, so this step is unconditional.
        f'section add {family} --title "<its title>"',
        f"add --block {block} --ref {free} …",
        # Named although the `add` above prints it on success: the whole point is that the
        # path is legible at call one, and a last step that only appears once the fourth call
        # lands is the staircase again with one stair left on it.
        f"section add {free} --title …",
    ]
    if any(
        not config.document(one).declaring(block)
        for one in BLOCK_ROLES
        if config.has(one) and config.path(one).is_file()
    ):
        # Ahead of them all, because it is the refusal the retry walks into next: a label no
        # heading declares is `add`'s own second door, one call further down the stairs.
        steps.insert(0, f'block add {block} --title "<its title>"')
    return (
        f"{started} and §{family} is its free top-level, so filing here is "
        + ", then ".join(f"`{invocation()} {one}`" for one in steps)
    ), free


def _where_a_top_level_is(config: Config, namespace: str, anchor: str = "") -> tuple[str, str]:
    """The same clause for an anchor belonging to nobody: a free address, or the command.

    A pair for :func:`_where_the_anchor_is`' reason (RK1149): the second half is the address a
    retry substitutes, and `""` wherever this declines to name one.

    **Which** free address is decided by what the caller typed (RK363). A malformed anchor
    whose leading segment is a family that exists is a typo inside that family — `XVII-1`
    is a hyphen where a dot belongs — and answering it with a new top-level says *start a
    new subtree*, which is the one thing that author was not doing. So the segment is read
    and, where it names a live family, that family's next child is the answer.

    That is not the guess RK360 refused to make. Deriving a family from whichever one
    happened to be last is context this cannot verify; reading the front of the address the
    caller wrote down is the same read :func:`split_ref` already makes, and it answers
    nothing where the segment names no family.

    The top-level is what remains, per namespace, for :func:`~roadkeep.history.next_family`'s
    reason (RK340): two prose files each numbering themselves from `I` have two free
    top-levels, and the taller file's number is not an answer about the shorter one.
    """
    # Deferred for RK260's reason, and because git belongs on no successful write path.
    from roadkeep.history import (  # noqa: PLC0415
        HistoryUnavailable,
        anchors,
        next_child,
        next_family,
    )
    from roadkeep.provenance import invocation  # noqa: PLC0415

    try:
        taken = anchors(config)
    except (HistoryUnavailable, OSError):
        return f" — `{invocation()} anchors` names the addresses this outline has taken", ""
    family = _family_typed(taken, namespace, anchor)
    if family is not None:
        child = next_child(taken, family)
        return (
            f" — §{family} is a family that exists, where §{child} is "
            f"free (`{invocation()} anchors --family {family}` lists it)"
        ), child
    free = next_family(taken, namespace)
    if free is None:
        # None is the honest answer where the top-levels are not one numbering, and a guess
        # printed beside a rule reads exactly like a fact.
        return f" — `{invocation()} anchors` names the addresses this outline has taken", ""
    return (
        f" — a section belonging to no task takes a top-level, and §{free} is free "
        f"(`{invocation()} anchors` lists what is taken)"
    ), free


#: What counts as the segment a malformed address opens with: the letters and digits before
#: whatever separator was typed wrong. `XVII-1` and `XVII 1` are one mistake (RK363).
_LEADING = re.compile(r"[A-Za-z0-9]+")


def _family_typed(taken: Sequence[Anchor], namespace: str, anchor: str) -> str | None:
    """The live family this malformed address opens with, spelled as its anchors spell it."""
    if not anchor:
        return None
    head = _LEADING.match(split_ref(anchor)[1])
    if head is None:
        return None
    for one in taken:
        space, bare = split_ref(one.anchor)
        if space == namespace and bare.split(".")[0] == head.group():
            return one.anchor.split(".")[0]
    return None


def _outline_violation(schema: Schema, anchor: str) -> Violation | None:
    """What is wrong with this address under an outline — its namespace, or its shape.

    Namespace first, because it is the question the other one cannot answer: `S:I` fails
    every reading of `<x.y>` and saying so would send an author to fix a spelling that is
    correct for the file they meant (RK340).
    """
    here = local(schema, anchor)
    if here is None:
        # An address in another role's namespace, written into this file: refused rather
        # than resolved, because the write was told which role it is for and the anchor
        # names a different one — and the heading drops the prefix, so the disagreement
        # would not survive in the file to be seen.
        return Violation(
            "anchor.namespace",
            "anchor",
            f"{anchor!r} is not an address in this file's namespace ("
            f"{schema.ref_prefix or 'none'}, per [refs]): a section written here is one "
            f"every pointer to that address resolves somewhere else",
        )
    if not OUTLINE_ANCHOR_RE.match(here):
        # Refused rather than written, because the heading would be read back by nothing:
        # under this scheme the number is what announces a section (RK44), so an anchor
        # that is not one is a section invisible from the moment it reaches the file.
        return Violation(
            "anchor.format",
            "anchor",
            f"not an <x.y> outline anchor: {anchor!r} — under ref_scheme = outline "
            f"the heading numbers itself, and a heading with no number is prose",
        )
    return None


def addressable(schema: Schema, anchor: str) -> bool:
    """Whether this scheme could read the token as a section address at all (RK1025).

    The public half of :func:`_address_violation`, for a reader that has an argument and no
    section: `show` refuses a token that is not a task id, and whether the token is one this
    file's outline *numbers* is what decides between "never written" and "you want the other
    verb". A predicate rather than the violation, because nothing here is being refused —
    the caller is deciding which sentence to print.

    **Only decidable under an outline**, and it says so by answering `False` everywhere
    else: under the `id` scheme an anchor is an id, so every token this could be asked about
    is either already a task or nothing at all, and answering `True` would name a section
    verb for an argument that is simply a typo.
    """
    if schema.ref_scheme != "outline":
        return False
    return _address_violation(schema, anchor) is None


def _address_violation(schema: Schema, anchor: str) -> Violation | None:
    """What is wrong with this address as an address, whichever scheme reads it (RK377).

    The half of :func:`_check` a verb that writes no prose still has to make: `move` validates
    a destination and has no title and no body to be told about, and re-spelling two branches
    at that call site is the second reader of a rule this module keeps one of.
    """
    if not anchor or anchor.startswith("§"):
        return Violation("anchor.sigil", "anchor", f"store the anchor without §: {anchor!r}")
    if schema.ref_scheme == "outline":
        return _outline_violation(schema, anchor)
    return None


def _inherited(body: str, standing: int | None) -> bool:
    """Whether this overrun was already in the file before the call (RK1263).

    ``standing`` is what the prose spent before the edit, and `None` is every caller that
    composed the whole body — there the overrun is theirs by construction. Where it is a
    number, an edit that leaves the count where it was or below it is one the file's standing
    debt refuses, not the caller: `lint` still reports the section, and the finding is about
    the paragraph rather than about the four characters somebody corrected inside it.

    Not *equal* and not a tolerance: the comparison is `<=`, so shortening an over-long section
    towards the limit is always allowed and growing it never is.
    """
    return standing is not None and words(body) <= standing


def _check(
    schema: Schema,
    anchor: str,
    title: str,
    body: str,
    task: Task | None,
    *,
    elsewhere: Whereabouts | None = None,
    known: frozenset[str] | None = None,
    resolves: frozenset[str] | None = None,
    standing: int | None = None,
) -> None:
    """Every rule a section is refused by, under **this file's** schema (RK147).

    ``elsewhere`` is where an id no live role holds actually is, threaded in rather than read
    here (RK238): this function takes a schema and not a project, which is what keeps it the
    one place the *rules* live — and the door an unknown anchor should be handed is a fact
    about the caller's files. `None` is the caller saying there is nothing to say, which
    `_elsewhere` decides.

    The schema is the one the caller loaded the document under — `config.schema_for(role)`,
    which is what `[limits.improvements]` declares (RK50) — and never `config.schema`, which
    is the project's top-level numbers. L1 is the first law: the format is enforced where
    the text is created, and reading a different limit here than the gate charges is exactly
    the failure it names. A project declaring a *tighter* rationale budget got it only after
    the paragraph existed; one declaring a *looser* one had this door refusing prose the gate
    would accept, which is worse — a refusal on legal text is a refusal an author routes
    around. Threaded rather than looked up again, so the two readings cannot disagree.

    The **binding** is not refused here and is not checked here at all: :func:`_bound` has
    already rendered it (RK262), so by the time a title reaches this function it names the
    task the anchor names, and a violation for the state that cannot arrive is a rule nobody
    can trip.
    """
    out: list[Violation] = []
    if (bad := _address_violation(schema, anchor)) is not None:
        out.append(bad)
    elif schema.id_pattern().match(anchor) and task is None:
        # The pointer is the id (RK27), so an id-shaped anchor that names no live task is
        # a section nothing can ever point at — an orphan the moment it is written. *Live*
        # and not open (RK231): a paused line keeps its id and its pointer, so its design is
        # amendable, and the word here is the one `_task_for` reads.
        out.append(Violation("anchor.unknown", "anchor", _unknown(anchor, elsewhere)))
    if not title.strip():
        out.append(Violation("title.empty", "title", "a section is named by its heading"))
    elif "\n" in title or "\r" in title:
        out.append(Violation("title.newline", "title", "a heading is one line"))
    elif title.lstrip().startswith("#"):
        out.append(
            Violation("title.markup", "title", "the level is a field, not part of the text")
        )
    out += promised(schema, body, known)
    # The one thing prose can be wrong about mechanically, asked where the text is created
    # (RK1227, L1). Found in Shio filing SH763: its rationale cited `§XVII.100`, an anchor a
    # task had removed when it shipped, and this write took it without complaint — surfacing
    # two commits later as a **red gate in that project**, on a docs-only commit that had
    # touched nothing else. Length was checked and paragraph shape was checked; whether the
    # address resolves was not asked, though the file was open and the answer is a lookup.
    #
    # Threaded like `known` and never resolved here (RK238): this function takes a schema and
    # not a project, which is what keeps it the one place the *rules* live — and which
    # addresses exist is a fact about the caller's files. `None` is a caller with nothing to
    # say, which is every call that cannot open them.
    if resolves is not None:
        dangling = [one for one in cited_in(body) if one not in resolves]
        if dangling:
            out.append(
                Violation(
                    "ref.dangling",
                    "body",
                    f"cites {', '.join('§' + one for one in dangling)}, which no prose file "
                    f"declares: a citation of an address a ship removed reads as an argument "
                    f"the reader can follow, and the gate finds it in somebody else's commit",
                )
            )
    if not body.strip():
        out.append(Violation("body.empty", "body", "a section with no prose is a heading"))
    elif words(body) > schema.section_max and not _inherited(body, standing):
        out.append(
            Violation(
                "body.too-long",
                "body",
                f"{over_by(words(body), schema.section_max, unit='word')}; a section "
                f"this long is two sections, or a paragraph that belongs in the commit"
                # Where the words are, on the refusal that discards them (RK311): the
                # overage says a cut is needed, and this says where one is available, so
                # the second draft is composed once instead of counted by hand.
                f"{_where_the_words_are(body)}",
            )
        )
    if out:
        raise SectionError(tuple(out))


def binding(config: Config, role: str, anchor: str) -> tuple[int, int] | None:
    """What this address charges anything written **under** it, and against what limit.

    `(words, limit)`, or `None` where nothing written under this anchor is charged to it —
    which is two states and not one: the address names no section, or it names a container
    nothing points at. A pointer hands a reader the whole subtree, so a *pointed-at* section
    is billed with its children and therefore binds them; a container is billed its own
    prose, and charging its children to it would price a body against a heading the gate does
    not bill (RK215). Both readers of this — `anchors` offering a child address (RK1024), and
    `budget` pricing one (RK1029) — want exactly the second question, and asking it here is
    what keeps them from deriving two answers to it.

    A read, so it decides nothing: `anchors` states the number and still prints the address,
    because an author about to shorten the parent is holding a plan no count can see.
    """
    if not config.has(role) or not _pointed_at(config, anchor):
        return None
    section = find(config.document(role), anchor)
    if section is None:
        return None
    return section.words, config.schema_for(role).section_max


def known(config: Config, anchor: str, task: Task | None) -> frozenset[str]:
    """The ids a design may name: every one some file carries, plus this task's own.

    The task's own is added because `add --section` writes the line and the prose in one
    transaction and the prose is checked first — so at this moment the id it explains is not
    yet carried by anything, and refusing a design for naming the task it is the design of
    would be the refusal reading the transaction backwards.
    """
    # Deferred: `ids` reads the documents this module writes into (RK260).
    from roadkeep.ids import carried  # noqa: PLC0415 - RK1002

    own = {anchor} if task is None else {task.id, anchor}
    return carried(config) | frozenset(own)


def resolvable(config: Config, anchor: str) -> frozenset[str]:
    """Every anchor a body may cite: those the prose files declare, plus the one being written.

    Across **every** prose role and never one document's (RK1227, following RK1106's reading):
    a citation of `§S:I.2` from the improvements file is a reference into the strategy file,
    and asking one document would refuse the correct half of a project's prose.

    The anchor being written is included for :func:`known`'s reason one field over: `section
    add` is checked before it writes, so a design citing the address it *is* would be refused
    by the transaction reading itself backwards.
    """
    out = {anchor}
    for role in PROSE_ROLES:
        if not config.has(role) or not config.path(role).is_file():
            continue
        out.update(one.anchor for one in anchored(config.document(role)))
    return frozenset(out)


def promised(schema: Schema, body: str, known: frozenset[str] | None) -> list[Violation]:
    """An id-shaped token in a design that no line carries (RK1002).

    RK431 made deriving an id read prose, and that is right: a ledger entry promising *filed
    as RK499* before the line exists has to reserve the number, or two things carry one id.
    What deriving cannot do is tell a promise from an illustration — deciding would take the
    model L4 forbids — so it warns, hedged, in another command's output, two sessions later.

    This is where the same rule is enforceable without judgement. **A design does not promise
    an id**: it explains a task that already has one, so an id-shaped token in a rationale
    body either names a line this backlog carries or it is an example, and an example that is
    spelled in this project's own prefix spends an address. §RK498 was composed with `add
    --dep RK999` in it, `section add` said nothing, and the next task filed was RK1000.

    The ledger is deliberately not held to this — that is where RK431's promise is legitimate,
    and refusing it there would refuse the one sentence the mechanism exists for.

    ``known`` is the ids some file carries as a line, plus the one this transaction is about
    to write. ``None`` means the caller had no project to ask, and the check is skipped rather
    than guessed at.
    """
    if known is None:
        return []
    # Deferred beside :func:`known`, and the same one-way edge (RK260).
    from roadkeep.ids import id_scanner  # noqa: PLC0415 - RK1002

    scanner = id_scanner(schema)
    loose = [
        match for match in scanner.finditer(body) if match.group(0) not in known
    ]
    if not loose:
        return []
    named = ", ".join(dict.fromkeys(match.group(0) for match in loose))
    ceiling = _highest_carried(scanner, known)
    ahead = [
        match
        for match in loose
        if 0
        < int(match.group("number")) - ceiling.get(match.group("family"), 0)
        <= _IN_FLIGHT
    ]
    return [
        Violation(
            "body.promise",
            "body",
            f"names {named}, which no line carries: an id in this project's own prefix is "
            f"read as spent, so the next `add` derives past it (RK431) — "
            + (
                # The case both old remedies missed (RK1027). An id past everything a line
                # carries is not a typo and not a retirement: it is work in flight, and the
                # caller is authoring two tasks that cite each other in the only order a
                # shell allows. Told first, because the other two ask them to rename or
                # delete a cross-reference the backlog wanted.
                f"{named} is past every id a line carries, so file that task first and "
                f"write this section after — or spell the example outside "
                f"{'/'.join(schema.prefixes)}"
                if len(ahead) == len(loose)
                else f"spell the example outside {'/'.join(schema.prefixes)}, name the id "
                f"actually meant, or read `gaps` for where it went"
            ),
        )
    ]


#: How far past the highest id a line carries a token may sit and still read as work in
#: flight (RK1027). Three zones, not two: below the maximum a missing id is a hole `gaps`
#: answers; **just** past it is the sibling being authored alongside this one; far past it
#: is an illustration, which is the case RK1002 was filed for — §RK498 named `RK999` against
#: a backlog whose next id was RK1000, and calling that a forward reference would take the
#: refusal RK1002 bought and blunt it.
#:
#: Not configuration (L6), and the same argument `ranking.NEAREST` makes: a project declares
#: how long its lines may be, and this is a property of how a sitting authors — measured on
#: this repository's own two batches of cross-citing tasks, which spanned three ids each.
_IN_FLIGHT = 8


def _highest_carried(
    scanner: re.Pattern[str], known: frozenset[str]
) -> dict[str, int]:
    """The largest number each family holds as a line, read off ``known`` (RK1027).

    The discriminator between a forward reference and a mistake, and it needs no second view
    of the surface: `known` is already every id some file carries, and the same scanner that
    found the loose token names the family and the number of each one. A maximum and not
    `next_id`: this function takes no project, which is what keeps `promised` the one place
    the *rule* lives — and `next_id` derives past everything a line carries, so the two
    disagree only about ids that are ahead either way.
    """
    ceiling: dict[str, int] = {}
    for one in known:
        match = scanner.fullmatch(one)
        if match is None:
            continue
        family = match.group("family")
        ceiling[family] = max(ceiling.get(family, 0), int(match.group("number")))
    return ceiling


def violations(
    schema: Schema,
    anchor: str,
    title: str,
    body: str,
    task: Task | None = None,
    *,
    elsewhere: Whereabouts | None = None,
    known: frozenset[str] | None = None,
) -> tuple[Violation, ...]:
    """The same rules, collected rather than raised (RK426).

    `add --section` refuses the line and the section in two passes, so a call whose `why` is
    fifteen characters over and whose body is fifty words over costs **two** full
    resubmissions — the second for a limit the first refusal already knew was breached. That
    is the cost `--section-body-file` exists to avoid, charged for a field the tool had not
    looked at, and re-passing the prose is the expensive half.

    So the caller that holds both sets asks for them and raises once. This is the collector
    and :func:`_check` is the raiser above it, rather than the reverse, because every other
    caller wants the refusal at the point of the check — a function that returned violations
    to twelve call sites would put the raise in twelve places, which is the shape L1 exists
    to avoid one layer up.
    """
    try:
        _check(schema, anchor, title, body, task, elsewhere=elsewhere, known=known)
    except SectionError as error:
        return tuple(error.violations)
    return ()


def _bound(schema: Schema, anchor: str, title: str, task: Task | None) -> str:
    """The heading text with the task named in it, which is what makes it that task's (RK262).

    Under an outline the anchor is an address and the **id in the heading is the binding** —
    `§XVI.12 A design (SH123)` — so `add --section "A design"` wrote a section belonging to
    nobody, and every reader afterwards was correct and useless: `ship` reported it *kept*,
    as prose belonging to none; `lint` declined to call it orphaned on exactly that reading;
    and the rationale for shipped work stayed in the prose file, which is what RK6 exists to
    prevent. The recovery was a `section amend --title "<title> (<id>)"` the author had to
    derive from a field named `kept`.

    **Rendered and not refused**, which is the door the design listed first and the only one
    `add --section` can take: that command *derives* the id, so an author composing the title
    does not yet know what to type, and refusing would be the tool telling them the answer and
    asking them to send it back. Nor is it prose (L4) — the id is the pointer's other end, and
    rendering a binding into the text that carries it is what `Schema.render` does one file
    over with `→ §<anchor>`.

    Whose it is, is :func:`owners` and never a second reading of it: that function already
    answers the question for the gate and for the drop, and a writer that agreed with neither
    is how a heading passes the door and fails the departure. A throwaway :class:`Section`
    because that is what it takes — every field but the two it reads is a placeholder. Under
    `ref_scheme = "id"` the anchor satisfies it, so nothing is ever appended there: no branch
    on the scheme, because the exemption *is* the reading.
    """
    if task is None or not title.strip():
        # An empty title stays empty: appending the id would render `§X.1 (CT1)`, a heading
        # that names its task and nothing else, and would take `title.empty` — the refusal
        # that is the whole reason nothing composes a heading out of a blank field — with it.
        return title.strip()
    probe = Section(anchor=anchor, title=title.strip(), level=0, first=0, last=0)
    if task.id in owners(probe, schema.id_pattern()):
        return title.strip()
    return f"{title.strip()} ({task.id})"


def _unknown(anchor: str, elsewhere: Whereabouts | None) -> str:
    """The refusal for an id no live line names, carrying a door the author can take (RK238).

    `add the line first` is the remedy for the one state it fits — an id that never existed.
    For an id the ledger holds it is the single door RK4 closes: `refuse_reuse` reads every
    governed file, so the `add` this advises is `IdInUse`, and retired-never-reused is the rule
    saying so. A finding whose named remedy the tool refuses is worse than one with no remedy,
    because the author spends the attempt before learning that (RK16).

    So the state is named the way :class:`~roadkeep.deferring.NotSetAside` names it — where the
    id *is* — and the two doors that do open are the ones offered: `record amend` for the entry
    sentence, which is what actually needs correcting when a shipped design reads wrong, and an
    outline anchor for prose belonging to no task, which this message already offered.

    The door is chosen from :class:`~roadkeep.backlog.Where` and not from whether a sentence
    is empty (RK240): `record amend` is the remedy for an id the **ledger** holds, and a
    branch that infers that from the truthiness of prose is a branch reading prose.
    """
    if elsewhere is not None and elsewhere.recorded:
        return (
            f"no live task {anchor} points at this section: {elsewhere.sentence}, so its "
            f"design ended at the departure — correct that entry with `record amend`, or use "
            f"an outline anchor for prose that belongs to no task"
        )
    return (
        f"no live task {anchor} points at this section: add the line first, or "
        f"use an outline anchor for prose that belongs to no task"
    )


def _elsewhere(config: Config, schema: Schema, anchor: str, task: Task | None) -> Whereabouts | None:
    """Where the id is, read only where the refusal can use the answer (RK240).

    `None` is "nothing to say", and it covers two cases rather than one: a live line already
    owns this anchor, or the anchor is not an id at all. An outline anchor named a section
    and never a task, so reading a ledger for it is a parse spent on a question `_unknown`
    will not ask — the one this used to make before the shape was checked.
    """
    if task is not None or not schema.id_pattern().match(anchor):
        return None
    return Whereabouts.of(config, anchor)


def _pointed_at(config: Config, anchor: str) -> bool:
    """Does a live task line point at this anchor — the gate's own question (RK215).

    What decides which of the two numbers a section is charged. A pointer hands a reader the
    whole subtree, so a *pointed-at* section is measured with it; a container nothing points
    at is measured on its own prose, because counting its children against it would measure
    the file's shape rather than anybody's paragraph. That is `lint`'s rule, and this asks it
    the same way so the writer and the gate cannot disagree — the disagreement being the
    defect, not the limit.

    Both live roles, as the gate reads them: a deferred line keeps its pointer and its
    section (RK96), so work set aside still claims its rationale. The ledger is not among
    them — a departure deletes the section in the transaction that writes the entry.

    And **only where one prose role declares the anchor** (RK232), which is the last condition
    RK215's agreement was missing. An anchor two files declare is charged as pointed at by
    nobody, because which of the two a line meant is what `ref.ambiguous` asks the author and
    billing one of them the other's subtree is the silent half of that defect. Counted before
    it was written: Turing at `f08304fcb1` declares 13 such anchors, one of them — `X.1`,
    pointed at by T354 — where the gate charges 73 words and this charged 365, so a correction
    to the intro was refused for 292 words of somebody else's subsections while the gate
    called that check clean. RK215's finding exactly, in the state RK215 did not reach.
    """
    if len(declaring(config, anchor)) != 1:
        return False
    return any(
        entry.task.ref == anchor
        for document in _live(config)
        for entry in document.entries
    )


def _task_for(config: Config, anchor: str) -> Task | None:
    """The live task this anchor names, if it names one at all.

    Both live roles, for the reason `_pointed_at` reads both (RK231) — and this is the half
    that *refuses*. Reading the roadmap alone, `section amend RK1` on a paused line answered
    `anchor.unknown`: "no open task RK1 points at this section: add the line first", about a
    line that exists, in the file `resume` restores from. That closed the last door on a
    state the tool creates on purpose, RK123's deadlock displaced — `drop` refused while the
    store's pointer claimed the anchor, `amend` refused because it read a different file than
    the pointer lived in, and the guard denied the `Edit`.

    Which leaves `anchor.unknown` with nothing to distinguish: a paused task is found here,
    so the refusal only ever fires for an anchor no live line names. An id the *ledger* holds
    is one of those, and rightly — a departure deletes the design, so there is no section to
    amend and no line to add back (RK4).

    **Under an outline the pointer is the answer** (RK262), and until this read it there was
    none: the anchor is an address, so the id test above matched nothing and every outline
    section looked ownerless to every caller here — which is why `section add` and `amend`
    could compose a heading naming no task while `add --section`, the one caller that passes
    its own, could not. The scan is `_pointed_at`'s and the rule is RK64's: **exactly one**
    live line, because four of Shio's point at one epic design, and picking one of four would
    be this function answering a question the format leaves open. Nothing refuses on the None
    that returns — an outline anchor never reaches `anchor.unknown` — so the cost of the
    ambiguous case is a heading the author binds by hand, which is where it started.
    """
    if config.schema.id_pattern().match(anchor):
        for document in _live(config):
            entry = document.by_id().get(anchor)
            if entry is not None:
                return entry.task
        return None
    owners_here = [
        entry.task
        for document in _live(config)
        for entry in document.entries
        if entry.task.ref == anchor
    ]
    return owners_here[0] if len(owners_here) == 1 else None


def _live(config: Config) -> Iterator[Document]:
    """The files a task line is live in, in the order a reader should trust them.

    One place, because the two questions above are the same question about one set of files:
    a pointer that claims a section and a task that owns one are both facts a ⏸ line still
    carries (RK96). The changelog is deliberately absent from both.
    """
    for role in ("roadmap", "deferred"):
        if config.has(role) and config.path(role).is_file():
            yield config.document(role)


# -- rendering and placement -------------------------------------------------


def _render(
    schema: Schema, anchor: str, title: str, body: str, level: int
) -> tuple[str, ...]:
    heading = f"{'#' * level} {anchor_text(schema, anchor)} {title.strip()}"
    return (heading, "", *_body_lines(schema, body))


def _inserted(document: Document, index: int, lines: Sequence[str]) -> Document:
    """Put these lines at ``index``, separated from what is already there.

    Factored out for the second writer (RK1258): a family opened in the same transaction is
    placed exactly as the design under it is, and two copies of the blank-line rule is how one
    of them comes to write a heading flush against the paragraph above it.
    """
    payload = list(lines)
    if index > 0 and not blank(document.lines[index - 1]):
        payload.insert(0, "")
    if index < len(document.lines):
        payload.append("")
    for offset, raw in enumerate(payload):
        document = document.insert_line(index + offset, raw)
    return document


def _opening(
    config: Config, role: str, document: Document, opens: tuple[str, str], where: str
) -> Document:
    """Declare the family this write's design extends, as a heading and nothing else (RK1258).

    A container and not a section with prose, and the difference is the whole shape: what a
    reader wants under `## XXXI` is the tasks, and what the tool may not do is compose the
    paragraph that would otherwise have to sit there (L4). The title is the **block's own**,
    which is a string the author already wrote — read at the door and passed in, so this
    function derives no words either.

    The address is asked the three questions every destination is asked, against the document
    this transaction holds: a family the file, a sibling or history already spent is a refusal
    here, before the child is placed inside it.
    """
    family, title = opens
    unspent(config, role, family, document=document, where=where)
    heading = (
        f"{'#' * _depth(document, family, None)} "
        f"{anchor_text(document.schema, family)} {title.strip()}"
    )
    return _inserted(document, _placement(document, family, None, where, role), (heading,))


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
    return any(_shape(line) for line in lines)


def _shape(line: str) -> bool:
    """Is this one line a Markdown structure rather than a sentence in a paragraph? (RK397)

    Read as three questions because the prefixes answer to three rules. A pipe, a quote and a
    fence are shapes on sight. A bullet, a number and a heading are a character **followed by
    a space** — that is what CommonMark says a marker is, and the space is what tells `* item`
    from `*emphasis*` and `1. one` from `1.5 seconds`. A run of three or more is a thematic
    break, which has no space and is a shape anyway.

    Four indented spaces stay a code block. Asked of the raw line and not the stripped one,
    which is the only place in here where the leading whitespace is the meaning.
    """
    if line.startswith("    "):
        return True
    head = line.lstrip()
    return bool(
        head.startswith(_VERBATIM) or _BREAK.match(head) or _MARKER.match(head)
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


def _placement(
    document: Document, anchor: str, task: Task | None, where: str = "", role: str = ""
) -> int:
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
        return _extended(document, anchor, where, role)
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


def _extended(
    document: Document, anchor: str, where: str = "", role: str = ""
) -> int:
    """The end of the subtree of the section this anchor extends, or a refusal (RK45).

    Or, for a top-level anchor under an outline, the end of the last top-level section
    (RK166): that is the one place a section extending nothing can go without reading as
    somebody else's, and until this existed a new block's first design was reachable by no
    verb at all. The file's *own* order decides it — after the last one, never sorted, since
    whether `XXII` follows `XXI` is a question about somebody's numbering (L4, L6) and the
    author is the one who wrote the anchor.

    ``role`` reaches the refusal alone, for RK197's reason: the remedy it names is a
    `section add`, and on a project declaring only a strategy file the default role is one
    that cannot run. Read here and not resolved from a config this function does not hold.

    **A prefix found is not an address that is well-formed** (RK1208). :func:`_extends`
    answers the *longest declared* prefix, and reading that as a parent wrote `§I.9.1` into a
    file holding only `§I` — a `###` at a child's depth, so `I.9.1` reads as a sibling of
    `I.1`, while `anchors --family I` derives its next child from the `9` inside it and spends
    a `§I.9` nothing ever claimed. `section add I.1` on that same file is refused, which is
    the same mistake with the same author and the other answer.
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
            opens=_ancestry(anchor),
            role=role,
        )
    # Every generation between the prefix found and the anchor typed. None of them is declared
    # by construction — `_extends` returned the longest that is — so this asks *how far* the
    # prefix falls short and never re-asks what the file holds.
    missing = _ancestry(anchor)[len(parent.split(".")) :]
    if missing:
        raise UnknownParent(
            anchor,
            [section.anchor for section in anchored(document)],
            where,
            opens=missing,
            role=role,
        )
    span = _span(document, parent)
    assert span is not None  # `_extends` read the anchor out of this document
    return span[1]


def _ancestry(anchor: str) -> tuple[str, ...]:
    """Every ancestor of this anchor, outermost first — the address alone (RK1207, RK1208).

    Not filtered against what the file declares, and the two callers are why that is an
    invariant rather than an omission: :func:`_extends` answers the **longest declared
    prefix**, so where it answered None every ancestor is missing, and where it answered one
    the callers take the tail past it. Either way the set handed to the refusal is undeclared
    by construction, and a filter here would re-ask what that function already decided.

    Outermost first, because that is the order the calls have to run in: `section add I.1` on
    a file with no §I is this same refusal, one address down. Empty for a one-segment anchor,
    which has no ancestor to be missing.
    """
    segments = anchor.split(".")
    return tuple(".".join(segments[:depth]) for depth in range(1, len(segments)))


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


def untitled(document: Document) -> tuple[Section, ...]:
    """Every heading this file carries that declares no anchor, in file order (RK1107).

    The other half of :func:`anchored`, and until this the half no verb could reach. A prose
    file's opening — the `#` that names it, and the prose under it saying what the file is —
    declares no address, and neither does a `## Table of contents`; both go stale the instant
    a `ship` drops a section, and the only door onto either was the hand edit the guard denies.
    Measured: `section show 'Table of contents'` answered *no §Table of contents section*, which
    was true and left the caller nowhere to go.

    **The heading's text is the address, and that is not a second addressing scheme.** An
    anchor is a name the project chose and never reuses; this is the heading a reader already
    sees, matched as it is written. §RK1107 assumed a positional name (`preamble`, `contents`)
    would be needed and would have to be declared per project (L6) — measuring the two live
    files says otherwise: the opening prose is the `#`'s **own** body, which
    :meth:`~roadkeep.kernel.document.Document.prose_end` already delimits, so the file's title
    is its address and no new word is invented anywhere.

    Own prose and never the subtree, for :func:`anchored`'s reason: the `#` heading's body is
    the preamble and stops at the first `##`, so amending it can never reach a section that has
    an address of its own.
    """
    out: list[Section] = []
    for heading in document.headings:
        if anchor_of(heading.text, document.schema) is not None:
            continue
        end = document.prose_end(heading)
        out.append(
            Section(
                anchor="",
                title=heading.text.strip(),
                level=heading.level,
                first=heading.lineno,
                last=end,
                body="".join(document.lines[heading.lineno : end]).strip("\r\n"),
            )
        )
    return tuple(out)


def titled(document: Document, title: str) -> Heading | None:
    """The one unanchored heading whose text is *title*, or None (RK1107).

    Compared on the stripped text and nothing cleverer: the caller has the file open, and a
    fuzzy match would make *which section did I just edit* a question. Refused rather than
    guessed where two headings carry one text — :class:`AmbiguousTitle` — because a file whose
    contents heading is written twice has two regions and no address distinguishes them.

    Asked **only of the unanchored**, so this can never become a second way to reach a section
    that has an anchor: one address per addressable thing, which is the property every reader
    downstream of `_span` already depends on.
    """
    wanted = title.strip()
    found = [
        heading
        for heading in document.headings
        if anchor_of(heading.text, document.schema) is None and heading.text.strip() == wanted
    ]
    if len(found) > 1:
        raise AmbiguousTitle(wanted, tuple(heading.lineno for heading in found))
    return found[0] if found else None


class AmbiguousTitle(ValueError):
    """One heading text, two headings — so the text is not an address (RK1107)."""

    def __init__(self, title: str, linenos: tuple[int, ...]) -> None:
        self.title = title
        self.linenos = linenos
        spelled = ", ".join(str(one) for one in linenos)
        super().__init__(
            f"{len(linenos)} headings read '{title}' (lines {spelled}): an unanchored section "
            f"is addressed by its heading, so two with one text have no address between them — "
            f"give one of them a different heading, or an anchor"
        )


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

    The **namespace stays on the pointer** (RK340): `[refs]` says which file an address is
    in, and a heading is already in one, so writing `S:I` above the prose in `STRATEGY.md`
    would put the answer to "which file" inside the file that is the answer.
    """
    if schema.ref_scheme == "id":
        return f"§{anchor}"
    return local(schema, anchor) or anchor


def heading_of(schema: Schema, section: Section) -> str:
    """The heading line this section is written as — one spelling, one writer (RK44).

    An empty anchor is the unanchored section (RK1107) and writes its title alone: under the
    id scheme :func:`anchor_text` would otherwise render the sigil with nothing after it, so a
    re-titled `## Table of contents` came back as `## § Table of contents`. Answered here
    because this is the one writer, and a caller composing the exception would be the second.
    """
    if not section.anchor:
        return f"{'#' * section.level} {section.title}"
    return f"{'#' * section.level} {anchor_text(schema, section.anchor)} {section.title}"


def anchor_of(text: str, schema: Schema) -> str | None:
    """The anchor this heading declares, or None when it declares none (RK27, RK44).

    Public because a heading is read outside a parsed document too (RK247): the anchors a
    file *used to* declare are in its diffs, and a second reader of this spelling one module
    over is the drift :func:`anchor_text` refuses at the writing end.

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
      :data:`~roadkeep.kernel.schema.OUTLINE_ANCHOR_RE`'s to say, at both ends of the pointer.
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
    if anchor_of(text, schema) is None:
        return text
    return text.lstrip().partition(" ")[2].strip()


def _names(text: str, anchor: str, schema: Schema) -> bool:
    """Does this heading declare exactly this anchor?

    Asked of the parsed anchor rather than of the text, which is what keeps `§0` from
    claiming `§0.1` and `VIII.1` from claiming `VIII.10` without a second opinion about
    where an anchor ends.

    And asked in **this file's namespace** (RK340): the heading writes the bare address, so
    an anchor naming another role's is one no heading here declares. One comparison rather
    than a check at every reader, because this is the comparison every reader already makes.
    """
    here = local(schema, anchor)
    # Both sides answer None — a heading that declares no anchor, and an address that is
    # another role's — and the two Nones are not a match.
    return here is not None and anchor_of(text, schema) == here
