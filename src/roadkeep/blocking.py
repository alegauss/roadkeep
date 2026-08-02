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
  first task of the new block under it.
* **How it is spelled.** The level and the separator are read off the file's own first block
  heading, so a project writing `## Block A — The model` gets one more of those and one
  writing `### Fase 2 - Execução` gets one more of those. The word is `[headings] word`
  already (RK75), and the label shape is the one a dep resolves against (RK28).

All of the files or none of them. A block declared in the roadmap and not the ledger is a
project where `add` works and `ship` fails on the same label, which is the deadlock again
with one more step in it.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from roadkeep.config import Config
from roadkeep.document import Document, Heading, assert_all_current, blank

__all__ = ["BlockExists", "NotALabel", "Opened", "open_block"]

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


@dataclass(frozen=True, slots=True)
class Opened:
    """The heading one block costs, in every file that wanted it, before it is written."""

    label: str
    title: str
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


def open_block(config: Config, label: str, title: str) -> Opened:
    """Declare one block in every governed file already organised by blocks.

    Validates everything before touching anything: an unreadable label, an empty title, and
    a label every candidate file already declares are all refusals that leave the tree
    exactly as it was.
    """
    schema = config.schema
    # The dep's pattern rather than the heading's, because that one is anchored at both
    # ends: a heading stops at the first space, so "a label with spaces" declares `a` and
    # the title would silently absorb the rest.
    if not schema.block_dep_pattern().match(schema.block_named(label)):
        raise NotALabel(label, schema.block_dep_pattern().pattern)
    if not title.strip():
        raise NotALabel(label, "a block is named by its title, and this one is blank")

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
        index = document.subtree_end(blocks[-1])
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
        documents=changed,
        placed=placed,
        rendered=rendered,
        skipped=tuple(skipped)
        + tuple((where, "already declares it") for where in declared),
    )


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
