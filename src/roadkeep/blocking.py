"""Declaring a block, which every other write refuses to do for you (RK141).

Measured in Claude Code Tray, shipping the first task of a new block. `ship T179` refused —
*"no heading declares Block AE: a heading invented by a write files the text where nothing
looks for it"* — and wrote nothing, which is right: naming a block is editorial, and a
heading the tool guesses is a heading nobody looks under. The remedy is one line in the
changelog, and the guard denies that `Edit`, listing every verb that may write there —
`ship`, `record add`, `record drop`, `retire` — none of which adds a heading.

Both refusals are right alone and the pair is a deadlock, so neither is weakened. This is the
missing key: a verb that declares a block and takes the title as the argument it is, symmetric
with `non-goal` (RK70), which already writes the roadmap's other non-task line.

What the author gives is the **label and the title**, which is the whole editorial content.
Everything else is derived, and derived **per file** rather than decided here:

* **Which files.** Every governed file that is *already organised by blocks*, because a
  heading is only wanted where something looks for one — the roadmap for `add`, the ledger
  for `ship`, the rationale file for `section add`. A file that declares no block at all is
  not one this verb starts organising; it is named in the answer and left alone.
* **Where.** After the last block's subtree, which is what opening a *new* block means and
  which is also the only placement that cannot land inside another's work. Never at the end
  of the file: the roadmap's `## Non-goals` follows the blocks, and appending would file the
  first task of the new block under it. **Or after a block the author names** (RK145), because
  appended is *a* placement and it was the only one: block order is not decoration — `list`
  reports blocks in the headings' own order, `brief --block <x>` is scoped by it, and a reader
  takes the sequence for the shape of the plan, so a phase belonging between two existing ones
  had no route but reordering three files by hand. `--after <label>` names a **neighbour**
  rather than a position, which is what lets one argument stay honest across files that
  order blocks differently: each file places the heading after the end of *its* `<label>`
  subtree, and a file declaring no such label is a refusal rather than a guess.
* **How it is spelled.** The level and the separator are read off the file's own first block
  heading, so a project writing `## Block A — The model` gets one more of those and one
  writing `### Fase 2 - Execução` gets one more of those. The word is `[headings] word`
  already (RK75), and the label shape is the one a dep resolves against (RK28).

All of the files or none of them. A block declared in the roadmap and not the ledger is a
project where `add` works and `ship` fails on the same label, which is the deadlock again
with one more step in it.

**And the key that could not close the door** (RK144). This verb was the only one that writes a
heading, and nothing took one back out — so a label typed wrongly, or a block whose every line
has left, was three headings only the edit the guard denies could remove: RK138's asymmetry one
surface over. :func:`drop_block` is the inverse, and it is narrow in the one way that matters:
**a heading over work is not an empty heading.** It removes a heading only where its whole
subtree is blank, and where anything is filed under the label it refuses by name — the
roadmap's open lines, the store's paused ones, the rationale file's sections — because
deleting the heading would orphan every one of them.

The **ledger is the exception, and not an inconsistency**: history is filed under its headings
for ever, so entries there are never something to refuse over and never something to remove.
That file is left alone and said so, which is also what keeps the removal from re-opening the
deadlock — the only asymmetry it can leave is a ledger declaring a label the roadmap does not,
where nothing plans and history still reads. The reverse, which would make `add` work and
`ship` fail, is exactly what refusing over open lines prevents.

**And the question all four of them assume has been answered** (RK1188). `add --block <x>` is
the first flag on the first write of any new task, and until :func:`catalogue` nothing said
what `<x>` could be: `stats` prints letters and counts and never a title, `list --block` and
`delivered <block>` both demand the letter as an argument and refuse one nothing declares, so
neither can discover it. The author read `docs/ROADMAP.md` with grep — the file the hook exists
to keep hands off, and the habit every other refusal here is spent unteaching.

A read under this noun rather than a column on `stats`, for the reason `non-goal list` is not
a column on anything: that verb is a report *about a file*, and this is the question asked
before writing *to* one. What it answers with is the label, the title as the file spells it,
and what became of the block — from the same reader `list` and `brief` answer an empty count
with, so the two cannot come to disagree about a block being finished.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from roadkeep.authoring import _after_preamble, remove_entry
from roadkeep.backlog import Backlog, Stage, Standing as Became
from roadkeep.config import Config
from roadkeep.criteria import without as criteria_without
from roadkeep.kernel.document import (
    Document,
    Heading,
    RepeatedHeading,
    blank,
    save_all,
)
from roadkeep.kernel.schema import Schema
from roadkeep.provenance import invocation

__all__ = [
    "BlockExists",
    "BlockOccupied",
    "Catalogue",
    "Closed",
    "Declared",
    "Merged",
    "NoSuchBlock",
    "NoSuchNeighbour",
    "NotALabel",
    "NotOrganisable",
    "NotRepeated",

    "NothingToDrop",
    "Opened",
    "RegionOccupied",
    "catalogue",
    "drop_block",
    "merge_block",
    "open_block",
]

#: The governed files a block heading can belong in, in the order the answer reports them.
#: A role is only written when its file already declares one — see the module docstring.
BLOCK_ROLES = (
    "roadmap",
    "changelog",
    "deferred",
    "improvements",
    "strategy",
    "decisions",
)

#: What separates the label from the title where a file declares no separator of its own.
#: Only reachable when the first block heading is the label alone, which no corpus writes.
DEFAULT_SEPARATOR = " \N{EM DASH} "


class NotALabel(ValueError):
    """A label the format cannot read, refused before anything is written.

    The same shape a dep resolves against (RK28): a heading declaring something else would
    make `pick --block <x>` an answer about a block nothing declares, and the disagreement
    would be invisible because both halves parse.
    """

    def __init__(self, label: str, pattern: str) -> None:
        self.label = label
        super().__init__(
            f"{label!r} is not a label this project can read ({pattern}): a heading "
            f"declares exactly one, and a dep resolves against that same list"
        )


class NoSuchNeighbour(KeyError):
    """A `--after` label a file that wants the new heading does not declare (RK145).

    Refused rather than fallen back on, and that is the whole of the decision: appending in
    the one file that cannot resolve the neighbour would order that file by a rule the others
    did not use, which is a disagreement about the plan's shape that both halves round-trip.
    The labels the file *does* declare are named, because the commonest cause is a neighbour
    that exists in the roadmap and not yet in the file being written beside it.
    """

    def __init__(
        self,
        after: str,
        label: str,
        where: str,
        declared: Sequence[str],
        word: str = "Block",
    ) -> None:
        self.after = after
        self.label = label
        self.where = where
        self.declared = tuple(declared)
        known = ", ".join(self.declared) or "none"
        super().__init__(
            f"{where} declares no {word} {after} to open {word} {label} after (declares: "
            f"{known}): --after names a neighbour, and a file that cannot find it would be "
            f"the one file ordered by a different rule"
        )


class NotOrganisable(ValueError):
    """An `--organise` this project cannot honour, refused before anything is written (RK405).

    Two ways to be that, and the sentence says which. A role the project does not declare, or
    whose file is not on disk, is nothing this verb can write into at all — and the roles it
    *can* are named, because the commonest cause is the role's own spelling.

    The other is subtler and is the rule this argument does not weaken: with **no** governed
    file declaring a block, there is no level and no separator to read, and a heading composed
    out of this module's own punctuation would write a second convention into a project that
    has one (see :func:`_heading`). That project is one `init` scaffolds, not one this verb
    guesses the shape of.
    """

    def __init__(self, role: str, roles: Sequence[str], *, spelling: bool = False) -> None:
        self.role = role
        self.roles = tuple(roles)
        if spelling:
            super().__init__(
                f"--organise {role}: no file this project declares carries a block heading "
                f"to read the level and the separator off, so the first one is not this "
                f"verb's to compose — `init` scaffolds a project that has none"
            )
            return
        known = ", ".join(self.roles) or "none"
        super().__init__(
            f"--organise {role}: this project declares no such file on disk (it declares: "
            f"{known}) — the argument names a role, which is how [files] names one"
        )


class BlockExists(ValueError):
    """A label every file that files work under blocks already declares.

    Reported as a refusal rather than a silent success, because a caller reaching for this
    verb believes the block is missing — and a command that exits 0 having written nothing
    teaches that it wrote something.

    **And the files that lack it are named, with the flag that reaches them** (RK1223).
    Reopening a shipped block is ordinary: a follow-up is filed under the block it belongs to,
    and that block's heading survives only in the ledger, because `drop_block` leaves history
    the heading it was filed under. So `block add J --title "…"` is the obvious move, and on a
    roadmap whose own blocks have all been withdrawn it answered *`J is already declared in
    docs/CHANGELOG.md: nothing to open`* — true of the changelog, false of the request, and
    reading as *you are done here* about the one file the new line was about to go into.

    The reason was already computed and thrown away: this verb skips a file that declares no
    block at all, and records why — `--organise <role> writes the first one`. That row went
    into :attr:`Opened.skipped` on the success path and nowhere on this one, so the caller
    learned it from the *next* command's refusal instead, which is a second failure to reach a
    door this verb owns.

    Named rather than opened, which is RK405's rule and is not weakened here: whether a file is
    to be organised by blocks is a statement only the author can make, and a heading composed
    into a file that has none would be this tool inventing a convention (see
    :func:`open_block`). What changes is that the statement is *asked for* here rather than
    somewhere else.
    """

    def __init__(
        self, label: str, where: Sequence[str], lacking: Sequence[tuple[str, str]] = ()
    ) -> None:
        self.label = label
        self.where = tuple(where)
        #: `(file, role)` per governed file that would take the heading and declares no block.
        self.lacking = tuple(lacking)
        said = f"{label} is already declared in {', '.join(self.where)}"
        if not self.lacking:
            super().__init__(f"{said}: nothing to open")
            return
        files = ", ".join(one for one, _ in self.lacking)
        flags = " ".join(f"--organise {role}" for _, role in self.lacking)
        super().__init__(
            f"{said}, and {files} declares no block at all: that file is where the work "
            f"goes, so this is a heading to open rather than nothing — "
            f"`{invocation()} block add {label} --title \"<its title>\" {flags}`"
        )


class NoSuchBlock(KeyError):
    """A label no governed file declares, at the door that removes a declaration (RK144).

    Distinct from :class:`~roadkeep.kernel.document.UnknownBlock`, which every *write* raises and
    whose sentence is about a heading a write may not invent. Here nothing was going to be
    written, and what the caller needs is the list — a label that is merely spelled
    differently from the file's is the commonest reason this door is reached at all.
    """

    def __init__(
        self,
        label: str,
        declared: Sequence[str],
        word: str = "Block",
        *,
        doing: str = "remove",
    ) -> None:
        self.label = label
        self.declared = tuple(declared)
        known = ", ".join(self.declared) or "none"
        super().__init__(
            f"no governed file declares {word} {label} (declares: {known}): there is no "
            f"heading to {doing}"
        )


class BlockOccupied(ValueError):
    """A heading with something filed under it, which is not an empty heading (RK144).

    The whole safety of the door, and the reason it is worth having at all: removing this
    heading would leave every line beneath it filed under the block above, silently and in a
    way that round-trips. So the occupants are **named** rather than counted — an author who
    typed the wrong label needs to see immediately that they are looking at somebody else's
    work, and a count cannot show that.

    Never raised for the ledger: entries there are history filed under a heading that stays
    for ever, so that file is skipped and reported instead.

    ``prose`` says everything held is a **note**, and then the refusal names the flag that
    takes it (RK237): a door whose existence the author learns from the refusal is the shape
    RK93 argued for, and until it existed this message was the whole exit from the corner.

    ``ending`` is what became of the block, and it is the half that turns this from a dead end
    into an answer (RK1454). A project's end-of-block sweep tells an agent to run
    `block drop <x>` once nothing is open; on a block whose deliveries used `ship --decides`
    the decisions file files entries under that heading, and this refuses — correctly, since
    removing it would refile them silently. The caller was told this was the last step, so a
    non-zero exit with no alternative leaves them deciding alone whether the sweep failed.
    `block list` already prints `empty` and `finished` as different states, so the ending
    existed in the model and was missing only from the message. Named and not acted on: the
    verb does exactly what it did.
    """

    def __init__(
        self,
        label: str,
        where: str,
        named: Sequence[str],
        word: str = "Block",
        *,
        prose: bool = False,
        ending: str = "",
    ) -> None:
        self.label = label
        self.where = where
        self.named = tuple(named)
        self.ending = ending
        holds = ", ".join(self.named)
        # Its own line, because it is an answer and not a clause of the reason: a reader who
        # stopped at the refusal has read why, and the line below says what to do instead.
        tail = f"\n  ends as  {ending}" if ending else ""
        if prose:
            super().__init__(
                f"{where} files {holds} under {word} {label}, which is loose prose and not "
                f"work: pass --prose to take the note with the heading, or keep both{tail}"
            )
            return
        super().__init__(
            f"{where} files {holds} under {word} {label}: a heading over work is not an "
            f"empty heading, and removing it would file all of it under the block above{tail}"
        )


class NothingToDrop(ValueError):
    """A label the ledger declares and no other file does (RK144).

    The terminal shape of the ledger exception: its heading holds history and stays for ever,
    so there is nothing this verb may remove — and nothing it is right to refuse over either.
    A refusal all the same, because the alternative is exit 0 over an untouched tree.
    """

    def __init__(self, label: str, where: Sequence[str], word: str = "Block") -> None:
        self.label = label
        self.where = tuple(where)
        super().__init__(
            f"{word} {label} is declared only in {', '.join(self.where)}, whose heading "
            f"holds the history filed under it: there is nothing to remove"
        )


class NotRepeated(ValueError):
    """A label no file declares more than once — there is nothing to consolidate (RK403).

    The door `merge` exists to close is a **doubled** heading, so a label that is declared
    once (or not at all) is refused rather than exited 0 over, for the reason
    :class:`BlockExists` is: a command that writes nothing and reports success teaches that
    it wrote something. The linenos it does declare are named, because the commonest cause
    is a label spelled differently from the file's — the same help :class:`NoSuchBlock` gives.
    """

    def __init__(self, label: str, where: Sequence[str], word: str = "Block") -> None:
        self.label = label
        self.where = tuple(where)
        listed = ", ".join(self.where) if self.where else "no governed file"
        super().__init__(
            f"{word} {label} is declared once, in {listed}: one heading is not two, and "
            f"there is nothing to merge"
        )


class RegionOccupied(ValueError):
    """A duplicate heading standing over something a mechanical fold may not move (RK403).

    `merge` relocates **entries** — a task line or a ledger entry is keyed by its id and
    filed under a label, so moving it under the surviving heading of the same label changes
    no field and round-trips by construction (L3, L4). Two kinds are not that, and each is
    refused by name rather than folded:

    * A **nested heading** — a rationale section, a sub-block — is a subtree whose placement
      is editorial, and `section move` is its door. Folding it would guess an order the tool
      has no opinion about (L4), which is the same reason :func:`open_block` refuses to invent
      a heading at all.
    * **Loose prose** is carried only under ``--prose``, the flag :class:`BlockOccupied`
      already names (RK237): a paragraph under one of two duplicate headings is a note the
      merge drops, and dropping it silently is the misfiling RK144 refused over.

    Named and not counted, for :class:`BlockOccupied`'s reason: an author who reached this
    door needs to see *what* is in the way, not how much.
    """

    def __init__(
        self,
        label: str,
        where: str,
        named: Sequence[str],
        word: str = "Block",
        *,
        nested: bool,
    ) -> None:
        self.label = label
        self.where = where
        self.named = tuple(named)
        holds = ", ".join(self.named)
        if nested:
            super().__init__(
                f"{where} nests {holds} under a second {word} {label}: a section is not an "
                f"entry, and `section move` places it — `merge` folds entries alone"
            )
            return
        super().__init__(
            f"{where} files loose prose ({holds}) under a second {word} {label}: pass "
            f"--prose to drop the note as the duplicate heading is folded, or move it first"
        )


@dataclass(frozen=True, slots=True)
class Retitled:
    """The words one block's heading is given, in every file that declares it (RK1204).

    A fourth shape and not :class:`Opened` with a flag, for the reason :class:`Closed` is not
    that either: what this one has to carry is the heading **as it read** beside the heading it
    now reads, because the whole answer is a title changing and a reader has to see both. The
    label is on neither side of that pair — it is the identity, and a verb that could move it
    would be `merge` and `add` at once.
    """

    label: str
    title: str
    #: The files this write changes, by role. Written together or not at all.
    documents: Mapping[str, Document] = field(default_factory=dict)
    #: Where the heading is, by role — 1-based, as an editor counts. Unmoved by this write,
    #: which is the point: the subtree is untouched and so is the placement.
    placed: Mapping[str, int] = field(default_factory=dict)
    #: The heading each file held before this write, by role, verbatim.
    was: Mapping[str, str] = field(default_factory=dict)
    #: The heading each file holds after it. Two files can differ in level and in separator,
    #: and each keeps its own: nobody asked for a restyle, and re-rendering from the project's
    #: convention would take a file's own spacing as the silent price of a retitle (RK388).
    rendered: Mapping[str, str] = field(default_factory=dict)
    #: Roles left alone, each with the reason — a file that declares the label with this title
    #: already above all, which is neither a refusal nor a write.
    skipped: tuple[tuple[str, str], ...] = ()

    def save(self) -> tuple[Path, ...]:
        """Write every file, having asked all of them first (RK116, RK6)."""
        return save_all(*self.documents.values())

    def stated(self, config: Config, wrote: Sequence[Path]) -> str:
        """Both readings of the heading, and every file that took the new one (RK1204).

        Through the same row producer its three siblings use, so the four block verbs answer
        in one table shape and none of them pads to a column of its own.
        """
        from roadkeep.rendering import _staging_rows  # noqa: PLC0415 - RK260

        rows = [
            f"{config.schema.block_named(self.label)} retitled: {self.title}",
            *_role_rows(
                config,
                self.documents,
                # Two rows per file, and the second is a left-aligned `was` rather than a
                # column under the first: `restate` prints both readings of a claim that way,
                # and a heading is long enough that an indented pair wraps in a terminal.
                lambda role, where: [
                    f"  {where}:{self.placed[role]}  {self.rendered[role]}",
                    f"  was      {self.was[role]}",
                ],
            ),
            *(f"  not      {where}: {reason}" for where, reason in self.skipped),
            # Said out loud, because it is the whole argument for the verb being narrow: a
            # retitle that moved work would be a merge nobody asked for.
            "  kept     the label, the placement and everything filed under it",
        ]
        rows += _staging_rows(config.relative(one) for one in wrote)
        return "\n".join(rows)

    def payload(self, config: Config, wrote: Sequence[Path]) -> dict[str, object]:
        """The same answer as data, with both readings of every heading it rewrote."""
        from roadkeep.rendering import _wrote_json  # noqa: PLC0415 - RK260

        return {
            "label": self.label,
            "title": self.title,
            "written": [
                {
                    "role": role,
                    "file": config.relative(config.path(role)),
                    "line": self.placed[role],
                    # Both readings, which is what makes the write reviewable: a payload with
                    # only the new heading says a title is right and not that one changed.
                    "was": self.was[role],
                    "rendered": self.rendered[role],
                }
                for role in self.documents
            ],
            "skipped": [
                {"file": where, "reason": reason} for where, reason in self.skipped
            ],
            **_wrote_json(config, wrote),
        }


def amend_block(config: Config, label: str, title: str) -> Retitled:
    """Give one block's heading new words, in every governed file that declares it (RK1204).

    The door the other three left shut. `add` takes a title, `drop` removes a heading and
    `merge` folds a duplicate; none of them changes the words of a heading that exists, and
    `section amend --title` — the verb that does exactly this one file over — had no block
    counterpart. So a title was write-once, and the only repair was `drop` plus `add`, which
    :class:`BlockOccupied` refuses the moment anything is filed under the label. The window
    closed on the first `add`, and after it the hand edit the guard denies was the whole exit.

    Measured in Turing: the ledger's `Analytics & observability gaps` was reopened through a
    layer that escaped the ampersand, and the roadmap took `Analytics &amp; observability
    gaps`. One heading, two spellings, and the skill's own rule is that they stay identical.

    **Narrow, and every part of that is deliberate.** The label is the identity and does not
    move — `merge` is the verb for a label, and a retitle that could change one would be two
    acts wearing one name. The subtree is not touched: this rewrites a heading line and
    nothing beneath it, which is why it is safe over work where `drop` is rightly not. Each
    file keeps its **own** level and separator, read off the heading being rewritten rather
    than off the project's first block, because nobody asked for a restyle and RK388 settled
    that a body-only edit leaves the bytes it was not asked about alone.

    All of the files or none of them, as its three siblings write: a title corrected in the
    roadmap and left standing in the ledger is the exact two-spellings defect this closes.

    A file already holding this title is skipped and said so, and a label where **every** file
    holds it writes nothing: rewriting the same bytes makes a no-op look like an edit to every
    hook watching the file, which is the rule the doors in `authoring` keep.
    """
    schema = config.schema
    if not schema.block_dep_pattern().match(schema.block_named(label)):
        raise NotALabel(label, schema.block_dep_pattern().pattern)
    if not title.strip():
        raise NotALabel(label, "a block is named by its title, and this one is blank")

    wanted = title.strip()
    changed: dict[str, Document] = {}
    placed: dict[str, int] = {}
    was: dict[str, str] = {}
    rendered: dict[str, str] = {}
    skipped: list[tuple[str, str]] = []
    declared: list[str] = []

    for role, (where, document, blocks) in _readable(config).items():
        holding = [one for one in blocks if one.label == label]
        if not holding:
            continue
        declared.append(where)
        if len(holding) > 1:
            # Two headings under one label is `merge`'s state, and picking one to rewrite
            # would leave the other saying the old thing — which is this defect again, inside
            # one file. The refusal names the verb that resolves it (RK391, RK403).
            raise RepeatedHeading(
                label,
                [one.lineno for one in holding],
                where,
                word=schema.heading_word,
            )
        (heading,) = holding
        raw = _heading((heading,), schema.block_named(label), wanted)
        before = document.lines[heading.lineno - 1].rstrip("\r\n")
        if before == raw:
            skipped.append((where, "already reads that"))
            continue
        changed[role] = document.replace_line(heading.lineno - 1, raw)
        was[role] = before
        rendered[role] = raw
        placed[role] = heading.lineno

    if not declared:
        raise NoSuchBlock(label, _labels(config), word=schema.heading_word, doing="retitle")
    if not changed:
        # Every file already reads that, which is success and not a write. A refusal here
        # would be a rule against running the same correction twice.
        return Retitled(label=label, title=wanted, skipped=tuple(skipped))
    return Retitled(
        label=label,
        title=wanted,
        documents=changed,
        placed=placed,
        was=was,
        rendered=rendered,
        skipped=tuple(skipped),
    )


@dataclass(frozen=True, slots=True)
class Merged:
    """What consolidating one label's duplicate headings changes, before it is written (RK403).

    The inverse shape of neither :class:`Opened` nor :class:`Closed`: a merge keeps a heading
    **and** removes one or more, and moves the entries the removed ones stood over into the
    one that stays. So it carries the surviving heading's line, every folded heading's line
    verbatim — the file will not hold them to read afterwards — and the ids that moved, per
    role, because the whole answer is *what went where*.
    """

    label: str
    #: The files this write changes, by role. Written together or not at all.
    documents: Mapping[str, Document] = field(default_factory=dict)
    #: Where the surviving heading is, by role — 1-based, as an editor counts.
    kept: Mapping[str, int] = field(default_factory=dict)
    #: The folded headings, verbatim and by role: the answer's only record of the titles this
    #: removed, since the file no longer holds them.
    folded: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    #: The ids relocated into the surviving region, by role and in the order they moved.
    moved: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    #: Lines of loose prose dropped with a folded heading, by role (RK237). Absent where a
    #: heading stood over entries alone, so the report tells "folded" from "folded the note too".
    notes: Mapping[str, int] = field(default_factory=dict)

    def save(self) -> tuple[Path, ...]:
        """Write every file, having asked all of them first (RK116, RK6)."""
        return save_all(*self.documents.values())

    def stated(self, config: Config, wrote: Sequence[Path]) -> str:
        """What went where, per file (RK403).

        Beside :meth:`payload` since RK1170, through the same row producer its two siblings use.
        """
        from roadkeep.rendering import _staging_rows  # noqa: PLC0415 - RK260

        rows = [
            f"{config.schema.block_named(self.label)} consolidated",
            *_role_rows(config, self.documents, self._rows),
        ]
        rows += _staging_rows(config.relative(one) for one in wrote)
        return "\n".join(rows)

    def _rows(self, role: str, where: str) -> list[str]:
        moved = ", ".join(self.moved[role]) or "nothing"
        rows = [
            f"  {where}:{self.kept[role]}  "
            f"folded {len(self.folded[role])}, moved {moved}"
        ]
        if role in self.notes:
            rows.append(f"  note     {self.notes[role]} line(s) of prose dropped with a heading")
        return rows

    def payload(self, config: Config, wrote: Sequence[Path]) -> dict[str, object]:
        """The same answer as data, carrying the headings no file holds any more."""
        from roadkeep.rendering import _wrote_json  # noqa: PLC0415 - RK260

        return {
            "label": self.label,
            "merged": [
                {
                    "role": role,
                    "file": config.relative(config.path(role)),
                    # Where the surviving heading is, the ids that moved under it, and the
                    # headings folded — verbatim, since the file no longer holds them and this
                    # answer is their only record.
                    "kept": self.kept[role],
                    "moved": list(self.moved[role]),
                    "folded": list(self.folded[role]),
                    # Null where a folded heading stood over entries alone (RK237).
                    "note": self.notes.get(role),
                }
                for role in self.documents
            ],
            **_wrote_json(config, wrote),
        }


@dataclass(frozen=True, slots=True)
class Closed:
    """The heading one block's removal takes out of every file, before it is written.

    The inverse shape of :class:`Opened` and deliberately not that class with a flag: what
    this one has to carry is the heading **as it read**, because after the write there is no
    file left to read it off — and what it does not carry is a title, which is the one thing
    a removal has no opinion about.
    """

    label: str
    #: The files this write changes, by role. Written together or not at all.
    documents: Mapping[str, Document] = field(default_factory=dict)
    #: Where the heading was, by role — 1-based, as an editor counts.
    removed: Mapping[str, int] = field(default_factory=dict)
    #: The heading each file held, by role, verbatim: the answer's only record of the title
    #: this took out, since the file it was read from no longer holds it.
    rendered: Mapping[str, str] = field(default_factory=dict)
    #: How many lines of loose prose went with the heading, by role (RK237). Absent where the
    #: heading stood over nothing, so the report can tell "removed" from "removed the note
    #: too" — which is the one thing `--prose` did that the author has to be able to see.
    notes: Mapping[str, int] = field(default_factory=dict)
    #: Roles left alone, each with the reason — the ledger's entries above all, which are
    #: neither a refusal nor a removal and would otherwise be an unexplained silence.
    skipped: tuple[tuple[str, str], ...] = ()
    #: The leads of the block's own criteria, which left with the label (RK1316). Named for
    #: `Departure.unmet`'s reason one address over: a definition of done that disappeared with
    #: no line about it is a deletion nobody reviewing the diff was told to look for.
    unmet: tuple[str, ...] = ()

    def save(self) -> tuple[Path, ...]:
        """Write every file, having asked all of them first (RK116, RK6)."""
        return save_all(*self.documents.values())

    def stated(self, config: Config, wrote: Sequence[Path]) -> str:
        """The heading as it read, and the files it came out of (RK144, RK237).

        Beside :meth:`payload` since RK1170, through the same row producer its two siblings use.
        """
        from roadkeep.rendering import _staging_rows  # noqa: PLC0415 - RK260

        from roadkeep.rendering import _unmet_rows  # noqa: PLC0415 - RK260

        rows = [
            f"{config.schema.block_named(self.label)} withdrawn",
            *_role_rows(config, self.documents, self._rows),
            *(f"  kept     {where}: {reason}" for where, reason in self.skipped),
            # The same sentence a departure prints for a task's list (RK1268, RK1316), with
            # the address this write spends: a definition of done that went with no line
            # about it is the deletion that task was filed against, one address up.
            *_unmet_rows(self.unmet, "the label"),
        ]
        rows += _staging_rows(config.relative(one) for one in wrote)
        return "\n".join(rows)

    def _rows(self, role: str, where: str) -> list[str]:
        rows = [f"  {where}:{self.removed[role]}  {self.rendered[role]}"]
        if role in self.notes:
            # Said, because this is the one line of the removal that took prose with it and
            # the file no longer holds it to be compared against (RK237).
            rows.append(
                f"  note     {self.notes[role]} line(s) of prose taken with the heading"
            )
        return rows

    def payload(self, config: Config, wrote: Sequence[Path]) -> dict[str, object]:
        """The same answer as data, carrying the heading no file holds any more."""
        from roadkeep.rendering import _wrote_json  # noqa: PLC0415 - RK260

        return {
            "label": self.label,
            "removed": [
                {
                    "role": role,
                    "file": config.relative(config.path(role)),
                    # The line it was on and the heading it was, because after this write no
                    # file holds either and the answer is the only record.
                    "line": self.removed[role],
                    "rendered": self.rendered[role],
                    # Null where the heading stood over nothing, so a caller reads "the note
                    # went too" off a field rather than off a count (RK237).
                    "note": self.notes.get(role),
                }
                for role in self.documents
            ],
            "skipped": [
                {"file": where, "reason": reason} for where, reason in self.skipped
            ],
            # The block's own criteria, which left with the label (RK1316). `[]` and never
            # omitted, as a departure's is: a plan that quietly got shorter is a change with
            # no sentence about it.
            "unmet": list(self.unmet),
            **_wrote_json(config, wrote),
        }


def drop_block(config: Config, label: str, *, prose: bool = False) -> Closed:
    """Remove one block's heading from every governed file where it stands over nothing.

    Validates everything before touching anything, as :func:`open_block` does: a label no
    file declares, and a heading with work under it, are refusals that leave the whole tree
    exactly as it was — including the files whose heading *was* removable, because a partial
    removal is the split declaration RK141's last paragraph is about.

    The ledger is skipped rather than refused over (see the module docstring): its headings
    hold history for ever, so entries under one are not an obstacle to clear.

    ``prose`` takes the heading's **loose prose** with it (RK237), and it is the door a corner
    had none of. An adopted roadmap carries a blockquote under each block heading — what the
    block is, often a "fully shipped, see the changelog" paragraph — because that is what a
    hand-written backlog looks like; Turing's had ten, four of them over blocks with no open
    line left. RK144 is right to count that prose, but no verb wrote or removed a note, so the
    only exits were an `Edit` the guard denies and a `Bash` write RK175 then reports as
    unattested. The block that most needs withdrawing is exactly the one whose note says so.

    **Opt-in, and never over work.** A task line or a nested heading under the label is
    somebody's, and no flag makes a removal the right verb for it — so the refusal stands
    whenever :attr:`Standing.work` is non-empty, and it names the flag only when prose is all
    that is left. Nothing here reads what the note *says*: "loose prose under a heading" is
    what the document model already resolves, and a tool with an opinion about the paragraph
    would be writing prose (L4).
    """
    word = config.schema.heading_word
    declaring = _declaring(config, label)
    if not declaring:
        raise NoSuchBlock(label, _labels(config), word=word)

    changed: dict[str, Document] = {}
    removed: dict[str, int] = {}
    rendered: dict[str, str] = {}
    notes: dict[str, int] = {}
    skipped: list[tuple[str, str]] = []

    for role, where, document, heading in declaring:
        held = _held(document, heading)
        takeable = bool(held) and not held.work and prose
        if not held or takeable:
            rendered[role] = document.lines[heading.lineno - 1].rstrip("\r\n")
            removed[role] = heading.lineno
            changed[role] = _excise(document, heading)
            if takeable:
                notes[role] = len(held.prose)
            continue
        if role != "changelog":
            raise BlockOccupied(
                label,
                where,
                held.names,
                word=word,
                prose=not held.work,
                # Read only here, on the branch that is about to refuse (RK1454): the whole
                # point of this verb is the write, and paying for the roadmap, the ledger and
                # the store on every successful drop would be the read that decides nothing.
                ending=_ending(config, label),
            )
        skipped.append((where, _kept(held)))

    if not changed:
        # Every file declaring it kept it, which can only be the ledger. A refusal rather
        # than an exit 0, for the reason `BlockExists` is one: a command that writes nothing
        # and reports success teaches that it wrote something.
        raise NothingToDrop(label, [where for _, where, _, _ in declaring], word=word)
    # And the list that asked what would finish it (RK1316), inside the same transaction —
    # which is RK1268's rule at the block's own address. RK1265 is right that a block's list
    # outlives its *lines*: an emptied block is a question somebody answered, and RK1300 prints
    # it at the ship that finishes one. Neither is about the **label** leaving. Observed on a
    # fresh tree, 2026-08-23: after `block drop A` the heading was gone from the roadmap and
    # the improvements file, and `## Done when — Block A` stood behind it — reported by
    # `criterion list` under a label `block list` does not carry, and refused by `criterion add
    # --block A` with `no block 'A'`, so what was left had no door but `criterion drop`.
    if "roadmap" in changed:
        without_list, unmet = criteria_without(changed["roadmap"], label)
        changed["roadmap"] = without_list
    else:
        unmet = ()
    return Closed(
        label=label,
        documents=changed,
        removed=removed,
        rendered=rendered,
        notes=notes,
        skipped=tuple(skipped),
        unmet=unmet,
    )


def _ending(config: Config, label: str) -> str:
    """What became of this block, said the way `block list` says it (RK1454).

    :attr:`~roadkeep.backlog.Standing.sentence` and never a second wording, which is that
    record's own rule: a refusal describing a finished block in words `list` does not use is a
    fourth opinion about the state, and the two would come to disagree.

    Extended by the one fact this door has and that read does not — that the heading is
    staying, and that this is how such a block ends rather than a step the caller missed.
    Only where the block is actually over: `paused` and `live` are the sentence alone, each
    already naming what is outstanding, and `empty` says nothing at all here — a block with no
    entry anywhere is one whose obstacle is a note or a nested section, and "is empty" beside a
    refusal naming what is filed under it would read as a contradiction.

    Silent on any failure. This is a sentence attached to a refusal that is already correct,
    and a read that raises here would replace a good message with a traceback.
    """
    try:
        became = Became.of(Backlog.load(config), label)
    except Exception:  # noqa: BLE001 - a refusal is the last place to start raising
        return ""
    if became.stage in (Stage.FINISHED, Stage.CURRENT):
        return f"{became.sentence} — and the heading stays, which is how such a block ends"
    return became.sentence if became.stage in (Stage.LIVE, Stage.PAUSED) else ""


def _kept(held: Standing) -> str:
    """Why the ledger's heading stayed, saying what it actually holds.

    Counted by kind (RK237): "3 entries filed under it" about three lines of prose is a reason
    that names the wrong thing, and the ledger is the one role where the answer is never a
    refusal the author can read the difference off.
    """
    if held.ids:
        plural = "entry" if len(held.ids) == 1 else "entries"
        return (
            f"{len(held.ids)} {plural} filed under it: history keeps the heading it "
            f"was filed under"
        )
    kind = "prose" if held.prose else "heading(s)"
    return f"{len(held.names)} line(s) of {kind} under it: the ledger's heading is not moved"


def _readable(config: Config) -> dict[str, tuple[str, Document, tuple[Heading, ...]]]:
    """Every governed file a block heading can belong in that is on disk, in report order.

    Read once and in one place because :func:`open_block` now asks two questions of the set
    rather than one (RK405): *which files want the heading* and *how does this project spell
    one* — and the second is answered by a file the first may skip.
    """
    found: dict[str, tuple[str, Document, tuple[Heading, ...]]] = {}
    for role in BLOCK_ROLES:
        if not config.has(role) or not config.path(role).is_file():
            continue
        document = config.document(role)
        found[role] = (
            config.relative(config.path(role)),
            document,
            tuple(h for h in document.headings if h.label),
        )
    return found


def removable(document: Document, label: str) -> Heading | None:
    """The heading :func:`drop_block` would take out of this file for ``label``, or None.

    One expression, read by the verb that removes and by the gate that reports a label two
    headings declare (RK391, RK417): a finding naming a command that then refuses is worse
    than one naming none, and the only thing that keeps those two level is asking the same
    function rather than each spelling the rule.

    **The empty one, wherever in the file it is**, which is what makes a duplicate repairable
    at all. Reading the first heading alone was right while a label had one; on a file that
    declares it twice it would refuse over an occupied first while an empty one sat below —
    measured on a real corpus, where the removable heading happened to come first and the
    reverse order would have had no exit at all. A heading over work is still never removed:
    that rule is per *heading* here, which is how it was always written.

    Prose is not empty. `--prose` is a decision the caller makes at the door, and a reader
    asking whether a heading is removable without it must not be told yes.
    """
    return next((h for h in document.declaring(label) if not _held(document, h)), None)


def _declaring(
    config: Config, label: str
) -> tuple[tuple[str, str, Document, Heading], ...]:
    """Every governed file that declares this label, with the heading that does it."""
    found: list[tuple[str, str, Document, Heading]] = []
    for role in BLOCK_ROLES:
        if not config.has(role) or not config.path(role).is_file():
            continue
        document = config.document(role)
        declared = document.declaring(label)
        if declared:
            # The removable one where there is one, and otherwise the first — which is then
            # the heading the refusal is rightly about (RK417).
            heading = removable(document, label) or declared[0]
            found.append((role, config.relative(config.path(role)), document, heading))
    return tuple(found)


@dataclass(frozen=True, slots=True)
class Standing:
    """What one heading stands over, by kind (RK237).

    The three kinds were always read; what they were not was told apart. A count of names is
    all a refusal needs, and it is not enough for the *door*: prose is the one kind a removal
    can honestly take with the heading, because the block above it is where it silently lands
    otherwise — while a task line or a rationale section under this label is work, and moving
    that is not a removal's business.
    """

    #: Task lines or ledger entries, by id.
    ids: tuple[str, ...] = ()
    #: Nested headings, by their text — a rationale section, or a sub-block.
    headings: tuple[str, ...] = ()
    #: Loose prose, by line number: the only address a paragraph has.
    prose: tuple[int, ...] = ()

    def __bool__(self) -> bool:
        return bool(self.ids or self.headings or self.prose)

    @property
    def names(self) -> tuple[str, ...]:
        """Everything, named as a reader has to see it — the order a refusal reports."""
        return (
            *self.ids,
            *(f"{text!r}" for text in self.headings),
            *(f"line {lineno}" for lineno in self.prose),
        )

    @property
    def work(self) -> tuple[str, ...]:
        """What no flag may take: the kinds that are somebody's, rather than the heading's."""
        return (*self.ids, *(f"{text!r}" for text in self.headings))


def _held(document: Document, heading: Heading) -> Standing:
    """What this heading stands over — empty when nothing.

    Anything non-blank counts: a paragraph left behind by a removed heading is filed under the
    block above it, which is the same silent misfiling as an orphaned task line (RK144).
    """
    start, end = heading.lineno, document.subtree_end(heading)
    ids: list[str] = []
    nested: list[str] = []
    loose: list[int] = []
    seen: set[int] = set()
    for entry in document.entries:
        if start < entry.lineno <= end:
            ids.append(entry.task.id)
            seen.add(entry.lineno)
    for below in document.headings:
        if start < below.lineno <= end:
            nested.append(below.text)
            seen.add(below.lineno)
    for offset in range(start, end):
        if offset + 1 not in seen and not blank(document.lines[offset]):
            loose.append(offset + 1)
    return Standing(ids=tuple(ids), headings=tuple(nested), prose=tuple(loose))


def _labels(config: Config) -> tuple[str, ...]:
    """Every label any governed file declares, in file order and without repeats."""
    found: list[str] = []
    for role in BLOCK_ROLES:
        if not config.has(role) or not config.path(role).is_file():
            continue
        for heading in config.document(role).headings:
            if heading.label and heading.label not in found:
                found.append(heading.label)
    return tuple(found)


@dataclass(frozen=True, slots=True)
class Declared:
    """One block, as the question before an `add` needs it answered (RK1188)."""

    label: str
    #: `Block C`, or whatever `[headings] word` spells — the same rendering every refusal
    #: about a label uses, so a project writing `Fase` never reads `Block` back.
    named: str
    #: The words after the label, **read** off the heading and never composed here. The
    #: first file that declares it wins, which is the roadmap wherever the roadmap has it:
    #: two files may legitimately title one block differently (this repository's do), and a
    #: verb that reported both would be answering a question about drift instead of place.
    title: str
    #: What became of it — :class:`roadkeep.backlog.Standing`, so this row and the sentence
    #: `list --block` prints over an empty count are one read and cannot disagree.
    became: Became
    #: The roles declaring it, in :data:`BLOCK_ROLES` order. Roles and not paths, because
    #: :attr:`plannable` is a question about *which* file and a path cannot be asked it.
    roles: tuple[str, ...] = ()

    @property
    def plannable(self) -> bool:
        """Whether an `add --block` could land here — which is the roadmap's heading alone.

        A block whose last line shipped keeps its ledger heading and may have lost the
        roadmap's, and that row is the one whose absence turns an `add` into
        :class:`~roadkeep.kernel.document.UnknownBlock`. Reported rather than filtered out:
        the label exists, and hiding it would answer "no such block" to a caller who can see
        the heading in the changelog.
        """
        return "roadmap" in self.roles


@dataclass(frozen=True, slots=True)
class Catalogue:
    """Where a task may go, in the order the files declare it (RK1188).

    Order is content here, for the reason `--after` exists (RK145): `list` reports blocks in
    the headings' own order and a reader takes the sequence for the shape of the plan, so a
    catalogue sorted alphabetically would be a second opinion about that shape.
    """

    blocks: tuple[Declared, ...] = ()

    def __bool__(self) -> bool:
        return bool(self.blocks)

    def stated(self, config: Config) -> str:
        """The rows, and the labels an `add` would still refuse (RK1188)."""
        where = config.relative(config.path("roadmap"))
        if not self.blocks:
            return (
                f"{where}: no block is declared — `block add <label> --title …` writes the "
                f"first heading, and every other write refuses until one exists"
            )
        pad = max(len(one.named) for one in self.blocks)
        titles = max(len(one.title) for one in self.blocks)
        rows = [f"{len(self.blocks)} block(s), in file order"]
        # **Both counts** (RK1455). The open one alone answers where a task may go, which is
        # RK1188's question; what a caller placing work into an unfamiliar backlog asks first
        # is how much each block has already taken, and that number was in the payload and not
        # in the rows — so the terminal answer sent them to the ledger and the ledger is
        # 117,815 characters. `recorded` is the ledger's own, shipped and retired alike.
        rows += [
            f"  {one.named:<{pad}}  {one.title:<{titles}}  "
            f"{one.became.open:>4} open  {one.became.recorded:>4} recorded  "
            f"{one.became.stage}".rstrip()
            for one in self.blocks
        ]
        elsewhere = [one.label for one in self.blocks if not one.plannable]
        if elsewhere:
            # The one row an author has to act on before typing `add --block`, said once
            # rather than as a column that is empty on every other line.
            rows.append(
                f"  not in {where}: {', '.join(elsewhere)} — `block add <label> --title …` "
                f"re-declares the heading a task can be filed under"
            )
        return "\n".join(rows)

    def payload(self, config: Config) -> dict[str, object]:
        """The same answer as data, with every file each label is declared in."""
        return {
            "file": config.relative(config.path("roadmap")),
            "blocks": [
                {
                    # The state and its counts first and whole, because they are one record
                    # (RK1170): a payload that spelled `block` a second time here would be the
                    # two-readers defect this row exists to keep out of `stats`.
                    **one.became.payload(),
                    "named": one.named,
                    "title": one.title,
                    # Whether `add --block` resolves, which is the roadmap's heading and not
                    # the label existing — the distinction the ledger's own headings create.
                    "plannable": one.plannable,
                    "declared_in": [
                        config.relative(config.path(role)) for role in one.roles
                    ],
                }
                for one in self.blocks
            ],
        }


def catalogue(config: Config) -> Catalogue:
    """Every block this project declares, titled and counted (RK1188).

    Read-only, and reading is never refused: a project with no block at all answers with the
    empty catalogue and the command that opens the first heading, because the caller who most
    needs this verb is the one who has nothing to grep for.

    The walk is :func:`_labels`', so the order and the membership are the ones the three
    writes in this module already resolve against, and the counts are
    :meth:`roadkeep.backlog.Backlog.standing`'s — one read of the roadmap, the ledger and the
    store, which is what keeps this from being a fourth opinion about a finished block.
    """
    backlog = Backlog.load(config)
    readable = _readable(config)
    schema = config.schema
    found: list[Declared] = []
    for label in _labels(config):
        roles = tuple(
            role for role, (_, _, blocks) in readable.items()
            if any(one.label == label for one in blocks)
        )
        heading = next(
            one
            for role in roles
            for one in readable[role][2]
            if one.label == label
        )
        found.append(
            Declared(
                label=label,
                named=schema.block_named(label),
                title=_title(heading),
                became=backlog.standing(label),
                roles=roles,
            )
        )
    return Catalogue(blocks=tuple(found))


def _title(heading: Heading) -> str:
    """The words this heading gives its block, with the separator it spelled them after.

    The inverse of :func:`_heading`, and it reads the same two facts that one writes: what
    follows the label, minus whatever :func:`_separator` says this file puts between them. A
    heading that is the label alone has no title, and the empty string is that answer — not
    an invention this module would then have to keep out of `amend`.
    """
    tail = heading.text[_label_end(heading.text) :]
    separator = _separator(heading)
    if tail.startswith(separator):
        return tail[len(separator) :].strip()
    return tail.strip()


def _excise(document: Document, heading: Heading) -> Document:
    """Take the heading out, with the blanks it owned — the inverse of :func:`_insert`.

    The whole subtree in one edit, which by the time this is reached is the heading, blank
    lines, and — under `--prose` — the note (RK237): the deletion is refused above where it is
    anything a task or a section owns. The trailing blank goes
    with it, and where the block was last in the file the *leading* one does too — a
    paragraph break the file never had is still a change, and both spellings round-trip,
    which is exactly why nothing downstream would catch it (RK54).
    """
    start = heading.lineno - 1
    updated = document.remove_lines(start, document.subtree_end(heading))
    if start >= len(updated.lines) and start > 0 and blank(updated.lines[start - 1]):
        return updated.remove_line(start - 1)
    return updated


@dataclass(frozen=True, slots=True)
class Opened:
    """The heading one block costs, in every file that wanted it, before it is written."""

    label: str
    title: str
    #: The block this one was opened after, where the author named one (RK145). None is the
    #: derived answer — the last block — and it is reported as such rather than resolved to a
    #: label, because "appended" and "after the last one" are the same placement said twice.
    after: str | None = None
    #: The files this write changes, by role. Written together or not at all.
    documents: Mapping[str, Document] = field(default_factory=dict)
    #: Where the heading landed, by role — 1-based, as an editor counts.
    placed: Mapping[str, int] = field(default_factory=dict)
    #: The heading as each file spells it, by role. Two files can differ in level and in
    #: separator, because each is read off its own first block heading.
    rendered: Mapping[str, str] = field(default_factory=dict)
    #: Roles left alone, each with the reason. A file skipped in silence is one the author
    #: discovers was skipped by the next command that refuses on it.
    skipped: tuple[tuple[str, str], ...] = ()

    def save(self) -> tuple[Path, ...]:
        """Write every file, having asked all of them first (RK116, RK6)."""
        return save_all(*self.documents.values())

    def stated(self, config: Config, wrote: Sequence[Path]) -> str:
        """The heading, and every file that took it (RK145).

        Beside :meth:`payload` since RK1170. The three block verbs answer in one table shape —
        role, file, line — and :func:`_role_rows` is where that column width is decided once.
        """
        from roadkeep.rendering import _staging_rows  # noqa: PLC0415 - RK260

        beside = f" (after {config.schema.block_named(self.after)})" if self.after else ""
        rows = [
            f"{config.schema.block_named(self.label)} declared{beside}: {self.title}",
            *_role_rows(
                config,
                self.documents,
                lambda role, where: [
                    f"  {where}:{self.placed[role]}  {self.rendered[role]}"
                ],
            ),
            *(f"  not      {where}: {reason}" for where, reason in self.skipped),
        ]
        rows += _staging_rows(config.relative(one) for one in wrote)
        return "\n".join(rows)

    def payload(self, config: Config, wrote: Sequence[Path]) -> dict[str, object]:
        """The same answer as data, with the files this write left alone."""
        from roadkeep.rendering import _wrote_json  # noqa: PLC0415 - RK260

        return {
            "label": self.label,
            "title": self.title,
            # The neighbour as it was asked for, null where it was derived: "after the last
            # block" and "appended" are the same placement said twice.
            "after": self.after,
            "written": [
                {
                    "role": role,
                    "file": config.relative(config.path(role)),
                    "line": self.placed[role],
                    "rendered": self.rendered[role],
                }
                for role in self.documents
            ],
            # Named, never silent: a file skipped in silence is one the author discovers was
            # skipped by the next command that refuses on it.
            "skipped": [
                {"file": where, "reason": reason} for where, reason in self.skipped
            ],
            **_wrote_json(config, wrote),
        }


def _role_rows(
    config: Config,
    documents: Mapping[str, Document],
    rows: Callable[[str, str], list[str]],
) -> list[str]:
    """Every role's rows, with the paths padded to one column (RK1170).

    The shape all three block verbs answer in, and the reason this is a function rather than
    three loops: the width is a property of *the set of files*, so a verb computing it beside
    its own loop is a verb that can quietly pad to a different column than its siblings.

    The callback is handed the role and its already-padded path, and answers with that role's
    rows — one for the heading and, where the write took prose with it, a second (RK237).
    """
    files = {role: config.relative(config.path(role)) for role in documents}
    width = max((len(one) for one in files.values()), default=0)
    return [row for role in documents for row in rows(role, f"{files[role]:<{width}}")]


def open_block(
    config: Config,
    label: str,
    title: str,
    *,
    after: str | None = None,
    organise: Sequence[str] = (),
) -> Opened:
    """Declare one block in every governed file already organised by blocks.

    Validates everything before touching anything: an unreadable label, an empty title, a
    label every candidate file already declares, and a neighbour a file that wants the
    heading does not declare are all refusals that leave the tree exactly as it was.

    ``after`` is the neighbour, not an index (RK145): each file places the heading at the end
    of *its own* `<label>` subtree, so the argument stays honest where two files order their
    blocks differently. Omitted, the neighbour is the last block, which is what opening a new
    one means and what every call before this argument existed got.

    ``organise`` names the roles this verb may write the **first** block heading into (RK405),
    and it is the key to the one deadlock the rest of this module left. Measured on a project
    whose `CHANGELOG.md` was prose: `ship` refused, naming this verb; this verb skipped that
    file, because a file declaring no block is not one it starts organising; and `block add`
    on a label nothing declares anywhere skipped it too — so no argument to any command put a
    heading there, and the guard denies the `Edit`. Plan freely, ship never.

    The rule being defended is real and is not weakened: the level, the separator and the
    placement are the file's own, and a file with no blocks holds none of them. What this
    argument supplies is the missing **statement** — *this file is to be organised by blocks*
    — which is the author's to make and never the tool's to infer, exactly as the title is.
    Given it, the spelling is derived from a file that does declare one, because the project's
    convention is a project fact and a second punctuation invented here would be the thing
    :func:`_heading` exists to avoid; and the placement is the end of the file, which is the
    only honest answer where there is no block subtree to follow and no `--after` to resolve.

    Refused where the role is not declared, where its file is absent, and where **no** file
    declares a block to read the spelling off — that last one being `init`'s job and not a
    heading this verb may compose out of nothing. A role that already declares blocks is
    written the ordinary way and the argument is simply spent: it says what is already true.
    """
    schema = config.schema
    # The dep's pattern rather than the heading's, because that one is anchored at both
    # ends: a heading stops at the first space, so "a label with spaces" declares `a` and
    # the title would silently absorb the rest.
    if not schema.block_dep_pattern().match(schema.block_named(label)):
        raise NotALabel(label, schema.block_dep_pattern().pattern)
    if not title.strip():
        raise NotALabel(label, "a block is named by its title, and this one is blank")
    if after is not None and after == label:
        raise NotALabel(label, "a block cannot be opened after itself")

    changed: dict[str, Document] = {}
    placed: dict[str, int] = {}
    rendered: dict[str, str] = {}
    skipped: list[tuple[str, str]] = []
    #: `(file, role)` per file that declares no block and was therefore passed over. Kept
    #: apart from `skipped` because the refusal needs the **role** to name the flag (RK1223),
    #: and that row's prose is a sentence for a reader rather than an argument for a command.
    lacking: list[tuple[str, str]] = []
    declared: list[str] = []

    readable = _readable(config)
    asked = tuple(dict.fromkeys(organise))
    for role in asked:
        if role not in readable:
            raise NotOrganisable(role, sorted(readable))
    # The project's own convention, read before anything is written and off the first file
    # that has one — `BLOCK_ROLES` order, so it is the roadmap wherever the roadmap has
    # blocks. A file being organised for the first time has no heading of its own to copy.
    convention = next((blocks for _, _, blocks in readable.values() if blocks), ())

    for role, (where, document, blocks) in readable.items():
        if not blocks:
            if role not in asked:
                # Not a file this verb starts organising unless told to: a heading here
                # would be the first of its kind, which is a decision about the file's
                # shape and not about a block (RK405 names the argument that makes it).
                skipped.append(
                    (where, f"declares no block; --organise {role} writes the first one")
                )
                lacking.append((where, role))
                continue
            if not convention:
                raise NotOrganisable(role, sorted(readable), spelling=True)
            raw = _heading(convention, schema.block_named(label), title.strip())
            index = _region_end(document, convention[0].level)
            changed[role] = _insert(document, index, raw)
            rendered[role] = raw
            placed[role] = _lineno(changed[role], raw)
            continue
        if any(h.label == label for h in blocks):
            declared.append(where)
            continue

        raw = _heading(blocks, schema.block_named(label), title.strip())
        index = document.subtree_end(_neighbour(blocks, after, where, label, schema))
        changed[role] = _insert(document, index, raw)
        rendered[role] = raw
        placed[role] = _lineno(changed[role], raw)

    if not changed:
        if declared:
            # The skipped rows go with it (RK1223): a file that declares no block is not a
            # file with nothing to open, it is the one file the work is about to go into.
            raise BlockExists(label, declared, lacking)
        raise BlockExists(label, ["no file this project declares is organised by blocks"])
    return Opened(
        label=label,
        title=title.strip(),
        after=after,
        documents=changed,
        placed=placed,
        rendered=rendered,
        skipped=tuple(skipped)
        + tuple((where, "already declares it") for where in declared),
    )


def _neighbour(
    blocks: tuple[Heading, ...], after: str | None, where: str, label: str, schema: Schema
) -> Heading:
    """The heading this file places the new one after — the last block, or the named one.

    Read per file on purpose (RK145): `--after C` means *after this file's Block C*, so two
    files that order their blocks differently each keep their own sequence. A file that wants
    the heading and declares no such neighbour is a refusal, because the alternative is
    falling back to the end and leaving one file ordered by an argument the others ignored.
    """
    if after is None:
        return blocks[-1]
    found = next((h for h in blocks if h.label == after), None)
    if found is None:
        raise NoSuchNeighbour(
            after,
            label,
            where,
            [h.label for h in blocks if h.label],
            word=schema.heading_word,
        )
    return found


def _region_end(document: Document, level: int) -> int:
    """Where a file with no blocks yet keeps its block region, as a 0-based index (RK413).

    The end of the file is what the first version of `--organise` used, and it is the one
    placement :func:`open_block` refuses by name everywhere else: a roadmap's `## Non-goals`
    follows its blocks, so appending filed the first task of the new block under it —
    measured, and `lint` called the result clean, because which sections a project puts after
    its blocks is not a rule this format holds.

    So the file is asked instead. A heading at the level the new one is being written at is
    where the next section begins, and the block region stops in front of it. The **level**
    and not any heading, which is what keeps the file's own title out of the answer, and
    `==` rather than `<=` for the same reason: a `# Roadmap` on line 1 is not a section the
    blocks come after.

    None of them is the flat ledger this door was built for, and there the end of the file is
    right after all — one rule for both shapes, read off the file rather than assumed.
    """
    section = next((h for h in document.headings if h.level == level), None)
    return len(document.lines) if section is None else section.lineno - 1


def _heading(blocks: tuple[Heading, ...], named: str, title: str) -> str:
    """The heading line, spelled the way this file already spells one.

    The level and the separator are the file's, never this module's: a project writing
    `### Fase 2 - Execução` gets one more of those, and a tool that answered with its own
    punctuation would be writing a second convention into a file that has one.
    """
    first = blocks[0]
    return f"{'#' * first.level} {named}{_separator(first)}{title}"


def _separator(heading: Heading) -> str:
    """What this file puts between the label and the title — read, never assumed.

    `Block A — The model` → `" — "`, `Fase 2 - Execução` → `" - "`, `Track C notes` →
    `" "`. A heading that is the label alone has no separator to read, and only then is
    :data:`DEFAULT_SEPARATOR` the answer.
    """
    tail = heading.text[_label_end(heading.text) :]
    if not tail.strip():
        return DEFAULT_SEPARATOR
    stripped = tail.lstrip()
    lead = tail[: len(tail) - len(stripped)]
    token, space, rest = stripped.partition(" ")
    if token and not token[0].isalnum() and rest:
        return f"{lead}{token}{space}"
    return lead


def _label_end(text: str) -> int:
    """Where the `<word> <label>` part of this heading stops."""
    head, _, _ = text.partition(" ")
    rest = text[len(head) + 1 :]
    label, _, _ = rest.partition(" ")
    return len(head) + 1 + len(label)


def _insert(document: Document, index: int, raw: str) -> Document:
    """Put the heading in, with the blank lines a heading needs on either side.

    The same care every writer in this package takes about blanks (RK5): a heading glued to
    the block above it reads as that block's text, and a doubled blank is a paragraph break
    the file never had — both of which round-trip, which is exactly why nothing else catches
    them.
    """
    payload: list[str] = []
    if index > 0 and not blank(document.lines[index - 1]):
        payload.append("")
    payload.append(raw)
    if index >= len(document.lines) or not blank(document.lines[index]):
        payload.append("")
    updated = document
    for offset, line in enumerate(payload):
        updated = updated.insert_line(index + offset, line)
    return updated


def _lineno(document: Document, raw: str) -> int:
    """Where the heading this write just rendered ended up, read back off the parse."""
    text = raw.partition(" ")[2]
    return next(h.lineno for h in document.headings if h.text == text)


def merge_block(config: Config, label: str, *, prose: bool = False) -> Merged:
    """Fold every duplicate heading for one label into the first, moving the entries (RK403).

    The key RK391 named and RK141/RK144's pair never cut. Two headings under one label is a
    state the gate reports (`block.repeated`) and every write refuses
    (:class:`~roadkeep.kernel.document.RepeatedHeading`), and the only remedy it could offer was
    *merge the two regions by hand* — which the guard (RK22) denies and the gate (RK14)
    refuses. `drop_block` cannot help: it **skips the ledger**, whose headings hold history
    for ever, so an empty duplicate ledger heading is :class:`NothingToDrop` rather than
    removable; `--fix` (RK16) repairs only derived data. So a doubled changelog heading — the
    shape a textual git merge, an `adopt`, or a hand edit leaves — was the one deadlock with
    no door.

    This is that door, and it is mechanical, not editorial. The surviving heading is the
    **first** one — the same choice `block.repeated` reports and `add` files under by position
    — and every later duplicate's entries move under it. Because both regions share the label,
    an entry's every field is byte-identical before and after, so the relocation round-trips
    by construction (L3) and writes no prose (L4); the move is `record move`'s (RK143) without
    the block changing.

    **The ledger is included, not skipped**, which is the difference from `drop_block` and the
    reason this exists: consolidating two headings of *one* label keeps history under a heading
    of that label, so nothing is orphaned — the danger that made `drop_block` skip the ledger
    does not arise here.

    Validates everything before touching anything, as :func:`open_block` and :func:`drop_block`
    do — all of the files, or none of them. A later duplicate standing over a **nested heading**
    (a rationale section, a sub-block) is :class:`RegionOccupied`, because placing a subtree is
    `section move`'s editorial call and not a fold's; **loose prose** is dropped only under
    ``prose`` and refused by name otherwise (RK237). A label declared once or nowhere is
    :class:`NotRepeated`.
    """
    word = config.schema.heading_word
    declaring = _declaring(config, label)
    if not declaring:
        raise NoSuchBlock(label, _labels(config), word=word)

    doubled = [(role, where, document) for role, where, document, _ in declaring
               if len(document.declaring(label)) > 1]
    if not doubled:
        raise NotRepeated(label, [where for _, where, _, _ in declaring], word=word)

    # Every refusal before any write (RK6): a nested heading or an un-flagged note under a
    # duplicate leaves the whole tree untouched, including the files whose fold was clean.
    for role, where, document in doubled:
        for later in document.declaring(label)[1:]:
            held = _held(document, later)
            if held.headings:
                raise RegionOccupied(label, where, held.headings, word=word, nested=True)
            if held.prose and not prose:
                raise RegionOccupied(
                    label, where, [f"line {n}" for n in held.prose], word=word, nested=False
                )

    changed: dict[str, Document] = {}
    kept: dict[str, int] = {}
    folded: dict[str, tuple[str, ...]] = {}
    moved: dict[str, tuple[str, ...]] = {}
    notes: dict[str, int] = {}
    for role, _, document in doubled:
        result, moved_ids, folded_headings, dropped = _fold(document, label)
        changed[role] = result
        kept[role] = result.declaring(label)[0].lineno
        moved[role] = moved_ids
        folded[role] = folded_headings
        if dropped:
            notes[role] = dropped
    return Merged(
        label=label,
        documents=changed,
        kept=kept,
        folded=folded,
        moved=moved,
        notes=notes,
    )


def _fold(document: Document, label: str) -> tuple[Document, tuple[str, ...], tuple[str, ...], int]:
    """Fold every later heading for ``label`` into the first, entry by entry.

    Re-reads the parse each step (RK54): moving one entry re-numbers every line below it, and
    a heading held across the edit is a heading at a line that has moved. So the loop asks
    :meth:`~roadkeep.kernel.document.Document.declaring` again each time and acts on the first
    remaining duplicate — moving its next entry under the survivor, or, once it holds none,
    excising the emptied heading. It ends when one heading is left, which the entry moves and
    the excises both drive toward.
    """
    result = document
    moved: list[str] = []
    folded: list[str] = []
    notes = 0
    while len(result.declaring(label)) > 1:
        keep, later = result.declaring(label)[:2]
        entries = [
            entry
            for entry in result.entries
            if later.lineno < entry.lineno <= result.subtree_end(later)
        ]
        if entries:
            entry = entries[0]
            # The whole entry, continuation lines included (RK157): a wrapped ledger entry's
            # tail is prose no task holds, so a fold that re-rendered alone would take the
            # paragraph out of the file in the name of moving the bullet.
            carrying = tuple(
                line.rstrip("\r\n") for line in result.lines[entry.lineno : entry.stop]
            )
            moved.append(entry.task.id)
            result = remove_entry(result, entry)
            result = _append_under(result, result.declaring(label)[0], entry.raw, carrying)
        else:
            # Emptied: the heading now stands over blanks alone (a note went with `--prose`
            # to `_held` above, which is why the count is read before the excise removes it).
            held = _held(result, later)
            notes += len(held.prose)
            folded.append(result.lines[later.lineno - 1].rstrip("\r\n"))
            result = _excise(result, later)
    return result, tuple(moved), tuple(folded), notes


def _append_under(
    document: Document, heading: Heading, raw: str, carrying: tuple[str, ...]
) -> Document:
    """Place one entry (and its continuation) at the end of ``heading``'s region.

    After the region's last entry when it has one, which needs no blank reasoning: the line
    that followed it — the block's trailing blank, or the next heading — still follows the
    line now appended. An **empty** surviving region is `place`'s empty-block case (RK108):
    the entry lands after the heading's own prose, with the blanks a first line needs on
    either side, so the introduction stays above the backlog and nothing is glued to a heading.
    """
    region = [
        entry
        for entry in document.entries
        if heading.lineno < entry.lineno <= document.subtree_end(heading)
    ]
    lines = document.lines
    if region:
        index, payload = region[-1].stop, [raw, *carrying]
    else:
        index = _after_preamble(document, heading)
        before: list[str] = []
        if index < len(lines) and blank(lines[index]):
            index += 1
        else:
            before = [""]
        after = [] if index >= len(lines) or blank(lines[index]) else [""]
        payload = [*before, raw, *carrying, *after]
    result = document
    for offset, line in enumerate(payload):
        result = result.insert_line(index + offset, line)
    return result
