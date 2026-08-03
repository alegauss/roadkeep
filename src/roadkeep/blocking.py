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
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from roadkeep.config import Config
from roadkeep.document import Document, Heading, assert_all_current, blank
from roadkeep.schema import Schema

__all__ = [
    "BlockExists",
    "BlockOccupied",
    "Closed",
    "NoSuchBlock",
    "NoSuchNeighbour",
    "NotALabel",
    "NothingToDrop",
    "Opened",
    "drop_block",
    "open_block",
]

#: The governed files a block heading can belong in, in the order the answer reports them.
#: A role is only written when its file already declares one — see the module docstring.
BLOCK_ROLES = ("roadmap", "changelog", "deferred", "improvements", "strategy")

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


class BlockExists(ValueError):
    """A label every file that files work under blocks already declares.

    Reported as a refusal rather than a silent success, because a caller reaching for this
    verb believes the block is missing — and a command that exits 0 having written nothing
    teaches that it wrote something.
    """

    def __init__(self, label: str, where: Sequence[str]) -> None:
        self.label = label
        self.where = tuple(where)
        super().__init__(
            f"{label} is already declared in {', '.join(self.where)}: nothing to open"
        )


class NoSuchBlock(KeyError):
    """A label no governed file declares, at the door that removes a declaration (RK144).

    Distinct from :class:`~roadkeep.document.UnknownBlock`, which every *write* raises and
    whose sentence is about a heading a write may not invent. Here nothing was going to be
    written, and what the caller needs is the list — a label that is merely spelled
    differently from the file's is the commonest reason this door is reached at all.
    """

    def __init__(self, label: str, declared: Sequence[str], word: str = "Block") -> None:
        self.label = label
        self.declared = tuple(declared)
        known = ", ".join(self.declared) or "none"
        super().__init__(
            f"no governed file declares {word} {label} (declares: {known}): there is no "
            f"heading to remove"
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
    """

    def __init__(self, label: str, where: str, named: Sequence[str], word: str = "Block") -> None:
        self.label = label
        self.where = where
        self.named = tuple(named)
        holds = ", ".join(self.named)
        super().__init__(
            f"{where} files {holds} under {word} {label}: a heading over work is not an "
            f"empty heading, and removing it would file all of it under the block above"
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
    #: Roles left alone, each with the reason — the ledger's entries above all, which are
    #: neither a refusal nor a removal and would otherwise be an unexplained silence.
    skipped: tuple[tuple[str, str], ...] = ()

    def save(self) -> None:
        """Write every file, having asked all of them first (RK116, RK6)."""
        assert_all_current(*self.documents.values())
        for document in self.documents.values():
            document.save()


def drop_block(config: Config, label: str) -> Closed:
    """Remove one block's heading from every governed file where it stands over nothing.

    Validates everything before touching anything, as :func:`open_block` does: a label no
    file declares, and a heading with work under it, are refusals that leave the whole tree
    exactly as it was — including the files whose heading *was* removable, because a partial
    removal is the split declaration RK141's last paragraph is about.

    The ledger is skipped rather than refused over (see the module docstring): its headings
    hold history for ever, so entries under one are not an obstacle to clear.
    """
    word = config.schema.heading_word
    declaring = _declaring(config, label)
    if not declaring:
        raise NoSuchBlock(label, _labels(config), word=word)

    changed: dict[str, Document] = {}
    removed: dict[str, int] = {}
    rendered: dict[str, str] = {}
    skipped: list[tuple[str, str]] = []

    for role, where, document, heading in declaring:
        held = _held(document, heading)
        if not held:
            rendered[role] = document.lines[heading.lineno - 1].rstrip("\r\n")
            removed[role] = heading.lineno
            changed[role] = _excise(document, heading)
            continue
        if role != "changelog":
            raise BlockOccupied(label, where, held, word=word)
        plural = "entry" if len(held) == 1 else "entries"
        skipped.append(
            (where, f"{len(held)} {plural} filed under it: history keeps the heading it "
             f"was filed under")
        )

    if not changed:
        # Every file declaring it kept it, which can only be the ledger. A refusal rather
        # than an exit 0, for the reason `BlockExists` is one: a command that writes nothing
        # and reports success teaches that it wrote something.
        raise NothingToDrop(label, [where for _, where, _, _ in declaring], word=word)
    return Closed(
        label=label,
        documents=changed,
        removed=removed,
        rendered=rendered,
        skipped=tuple(skipped),
    )


def _declaring(
    config: Config, label: str
) -> tuple[tuple[str, str, Document, Heading], ...]:
    """Every governed file that declares this label, with the heading that does it."""
    found: list[tuple[str, str, Document, Heading]] = []
    for role in BLOCK_ROLES:
        if not config.has(role) or not config.path(role).is_file():
            continue
        document = config.document(role)
        heading = document.heading(label)
        if heading is not None:
            found.append((role, config.relative(config.path(role)), document, heading))
    return tuple(found)


def _held(document: Document, heading: Heading) -> tuple[str, ...]:
    """What this heading stands over, named as a reader has to see it — empty when nothing.

    Three kinds, because a block heading can own three kinds of thing: task lines or ledger
    entries (named by id), nested headings such as a rationale section (named by their text),
    and loose prose (named by its line, which is the only address it has). Anything non-blank
    counts: a paragraph left behind by a removed heading is filed under the block above it,
    which is the same silent misfiling as an orphaned task line.
    """
    start, end = heading.lineno, document.subtree_end(heading)
    names: list[str] = []
    seen: set[int] = set()
    for entry in document.entries:
        if start < entry.lineno <= end:
            names.append(entry.task.id)
            seen.add(entry.lineno)
    for nested in document.headings:
        if start < nested.lineno <= end:
            names.append(f"{nested.text!r}")
            seen.add(nested.lineno)
    for offset in range(start, end):
        if offset + 1 not in seen and not blank(document.lines[offset]):
            names.append(f"line {offset + 1}")
    return tuple(names)


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


def _excise(document: Document, heading: Heading) -> Document:
    """Take the heading out, with the blanks it owned — the inverse of :func:`_insert`.

    The whole subtree in one edit, which by the time this is reached is the heading and blank
    lines: the deletion is refused above where it is anything else. The trailing blank goes
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

    def save(self) -> None:
        """Write every file, having asked all of them first (RK116, RK6)."""
        assert_all_current(*self.documents.values())
        for document in self.documents.values():
            document.save()


def open_block(
    config: Config, label: str, title: str, *, after: str | None = None
) -> Opened:
    """Declare one block in every governed file already organised by blocks.

    Validates everything before touching anything: an unreadable label, an empty title, a
    label every candidate file already declares, and a neighbour a file that wants the
    heading does not declare are all refusals that leave the tree exactly as it was.

    ``after`` is the neighbour, not an index (RK145): each file places the heading at the end
    of *its own* `<label>` subtree, so the argument stays honest where two files order their
    blocks differently. Omitted, the neighbour is the last block, which is what opening a new
    one means and what every call before this argument existed got.
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
    declared: list[str] = []

    for role in BLOCK_ROLES:
        if not config.has(role) or not config.path(role).is_file():
            continue
        where = config.relative(config.path(role))
        document = config.document(role)
        blocks = tuple(h for h in document.headings if h.label)
        if not blocks:
            # Not a file this verb starts organising: a heading here would be the first of
            # its kind, which is a decision about the file's shape and not about a block.
            skipped.append((where, "declares no block, so there is none to open beside"))
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
            raise BlockExists(label, declared)
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
