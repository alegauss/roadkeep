"""Prose files have a different unit, so they get a different schema (RK9).

Three of the four governed files are lines; two are paragraphs. A rationale or a strategy
is prose under a heading, and applying the line schema to it would be the wrong law
twice over: there is no `symptom` to bound and no 320-character cap that means anything
about a paragraph. What a section *does* have is:

* **an anchor**, which is the whole reason the pointer on a task line resolves (RK27) —
  so `§RK9` must name an open task, and a typo names nothing at all;
* **a word budget**, because the failure mode measured here was a rationale file reaching
  539 KB one honest paragraph at a time — a limit in words is the one an author can act
  on before writing, which is the same argument as `add`'s (L1);
* **a place**, which is derived: a section for a task belongs under that task's block, so
  the file's shape is a consequence of the backlog's and nobody chooses where to type.

`drop` is the operation `ship` (RK6) calls for rule one of its three edits — it lives here
rather than there because deleting a section is a fact about this file's grammar, not
about shipping, and the two would otherwise disagree about where a section ends.

Reflow is deliberately narrow. A plain paragraph is filled to the configured width, and
anything carrying a Markdown structure — a table, a list, a quote, a fence — is inserted
exactly as written: the tool re-flows prose, and never reformats a shape it did not
author. That is the same line L4 draws, one file down.
"""

from __future__ import annotations

import re
import textwrap
from dataclasses import dataclass

from roadkeep.config import Config
from roadkeep.document import Document, Heading, UnknownBlock, blank
from roadkeep.schema import SchemaError, Task, Violation

#: A paragraph whose first characters are any of these is a structure, not prose.
_STRUCTURE = ("|", ">", "-", "*", "+", "#", "```", "~~~", "1.")


class SectionError(SchemaError):
    """A section the schema refuses, carrying every violation, not the first.

    A :class:`~roadkeep.schema.SchemaError` because it is the same law one file down —
    which also means every caller that already reports violations reports these.
    """


class NoSuchSection(ValueError):
    """An anchor nothing in this file declares."""

    def __init__(self, anchor: str, where: str) -> None:
        self.anchor = anchor
        super().__init__(f"no §{anchor} section in {where}")


class SectionExists(ValueError):
    """One anchor, one section: two would make the pointer ambiguous."""

    def __init__(self, anchor: str, where: str, lineno: int) -> None:
        self.anchor = anchor
        self.lineno = lineno
        super().__init__(
            f"§{anchor} is already at {where}:{lineno}: an anchor names one section, "
            f"and a pointer that resolves to two resolves to neither"
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
        return len(self.body.split())

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
        title=_title_of(heading.text),
        level=heading.level,
        first=heading.lineno,
        last=end,
        body=body,
    )


def drop(document: Document, anchor: str) -> tuple[Document, Section]:
    """Delete the section whole — subsections included — and report what went.

    A subsection left behind is orphaned prose under the *next* task's heading, which
    reads as that task's design and is the one outcome worse than deleting too much.
    """
    span = _span(document, anchor)
    section = find(document, anchor)
    if span is None or section is None:
        raise NoSuchSection(anchor, str(document.path or "the document"))
    start, end, _ = span
    for _ in range(end - start):
        document = document.remove_line(start)
    return document, section


def add(
    config: Config,
    role: str,
    anchor: str,
    title: str,
    body: str,
    *,
    level: int = 3,
) -> tuple[Document, Section]:
    """Place one section under its block, reflowed. Validates before it renders.

    Returns the document unsaved, so a caller mid-transaction (`ship`, `init`) decides
    when the file is touched.
    """
    document = config.document(role)
    task = _task_for(config, anchor)
    _check(config, anchor, title, body, task)
    existing = find(document, anchor)
    if existing is not None:
        raise SectionExists(
            anchor, config.relative(config.path(role)), existing.first
        )

    lines = _render(config, anchor, title, body, level)
    index = _placement(document, task)
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


def words(body: str) -> int:
    return len(body.split())


# -- validation --------------------------------------------------------------


def _check(config: Config, anchor: str, title: str, body: str, task: Task | None) -> None:
    schema = config.schema
    out: list[Violation] = []
    if not anchor or anchor.startswith("§"):
        out.append(
            Violation("anchor.sigil", "anchor", f"store the anchor without §: {anchor!r}")
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
                f"{words(body)} words, limit is {schema.section_max}: a section this "
                f"long is two sections, or a paragraph that belongs in the commit",
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
    config: Config, anchor: str, title: str, body: str, level: int
) -> tuple[str, ...]:
    heading = f"{'#' * level} §{anchor} {title.strip()}"
    paragraphs = [p for p in _normalize(body).split("\n\n") if p.strip()]
    out: list[str] = [heading, ""]
    for position, paragraph in enumerate(paragraphs):
        if position:
            out.append("")
        out.extend(_reflow(paragraph, config.schema.prose_width).split("\n"))
    return tuple(out)


def _normalize(body: str) -> str:
    """The body arrives from an argument or a pipe, so its endings are not the file's."""
    return body.replace("\r\n", "\n").replace("\r", "\n").strip("\n")


def _reflow(paragraph: str, width: int) -> str:
    lines = paragraph.split("\n")
    if any(
        line.lstrip().startswith(_STRUCTURE) or line.startswith("    ") for line in lines
    ):
        return paragraph.rstrip()
    return textwrap.fill(
        " ".join(line.strip() for line in lines),
        width=width,
        break_long_words=False,
        break_on_hyphens=False,
    )


def _placement(document: Document, task: Task | None) -> int:
    """Where the section goes: after the last one under its block, else at the end.

    A section for a task belongs under that task's block, so the prose file's order is a
    consequence of the backlog's rather than a decision made per insertion. Prose that
    belongs to no task — this project's `§0` preface — has no block to derive, and goes
    last.

    A block the prose file does not declare is refused rather than appended at the end:
    a Block A section landing after Block F's reads as Block F's, which is the same
    mistake `add` refuses one file over (RK37).
    """
    if task is None or not task.block:
        return len(document.lines)
    heading = document.heading(task.block)
    if heading is None:
        raise UnknownBlock(
            task.block,
            sorted({h.label for h in document.headings if h.label}),
            str(document.path.name if document.path else ""),
        )
    for later in document.headings:
        if later.lineno > heading.lineno and later.level <= heading.level:
            return later.lineno - 1
    return len(document.lines)


def _span(document: Document, anchor: str) -> tuple[int, int, Heading] | None:
    """The `[start, end)` lines to delete, and the heading that names them.

    A section ends where the next heading of the same or higher level begins. When it is
    the last thing in the file, the deletion reaches back over the blank line above it,
    which otherwise survives as a trailing blank nobody put there.
    """
    for position, heading in enumerate(document.headings):
        if not _names(heading.text, anchor):
            continue
        start = heading.lineno - 1
        end = len(document.lines)
        for later in document.headings[position + 1 :]:
            if later.level <= heading.level:
                end = later.lineno - 1
                break
        if end == len(document.lines):
            while start > 0 and blank(document.lines[start - 1]):
                start -= 1
        return start, end, heading
    return None


def _title_of(text: str) -> str:
    """`§RK9 A design` → `A design`. The anchor is one token; the rest is the title."""
    if not text.startswith("§"):
        return text
    return text[1:].partition(" ")[2].strip()


def _names(text: str, anchor: str) -> bool:
    """Does this heading carry `§anchor` — and not `§anchor` as a prefix of another?"""
    marked = f"§{anchor}"
    if not text.startswith(marked):
        return False
    rest = text[len(marked) :]
    return not rest or not (rest[0].isalnum() or rest[0] == ".")
