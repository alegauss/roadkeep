"""Shipping a task: three edits across three files, or none of them (RK6).

Shipping is the moment the format is most likely to break, because it is the only
operation that is not one edit. The line leaves the roadmap, the entry appears in the
ledger, and the rationale section is deleted — and whichever of the three is done by
hand last is the one that gets forgotten, which is how a backlog comes to have a task
that is shipped in one file and open in another.

So the three edits are one command, and the ordering is deliberate: **everything is
computed and validated in memory before any file is touched.** A refusal — no such open
task, already in the ledger, no block heading there to file it under, a file that
already drifted (L3) — costs nothing and leaves three untouched files. Writing is the
last thing that happens, and by then nothing is left that can fail except the disk.

Two decisions worth stating, because both are narrower than they could be:

* **The roadmap line is removed, not replaced by a stub.** A pointer left behind is a
  second place a reader can ask about status, and the ledger is already greppable — the
  answer to "did RK5 ship?" has to have exactly one home (RK7).
* **The `why` is copied verbatim unless the author restates it.** The roadmap's sentence
  is a design and the ledger's is an outcome, so `--why` exists — but the tool never
  rewrites the sentence itself (L4), and it validates whichever one it is given.

What it does not do: derive the dep annotations of the tasks that named this one. That
is RK8, and until it lands `ship` *reports* the lines whose `(deps: …)` now read as
pending — naming the stale cache is not the same as writing it, and a report that hides
the gap would be worse than the hand-edit it replaces.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from roadkeep.authoring import Insertion, place
from roadkeep.backlog import NotOpen
from roadkeep.config import Config
from roadkeep.document import Document, Heading, blank
from roadkeep.schema import Task

__all__ = ["AlreadyShipped", "NotOpen", "Section", "Shipment", "ship"]


class AlreadyShipped(ValueError):
    """A second ledger entry for one id is two records of one decision."""

    def __init__(self, task_id: str, where: str, lineno: int) -> None:
        self.task_id = task_id
        self.lineno = lineno
        super().__init__(
            f"{task_id} is already in {where}:{lineno}: shipping it twice would make "
            f"the ledger disagree with itself about when it shipped"
        )


@dataclass(frozen=True, slots=True)
class Section:
    """The rationale section that was dropped, and the lines it occupied."""

    anchor: str
    text: str
    first: int  # 1-based, as an editor counts
    last: int

    def __str__(self) -> str:
        return f"§{self.anchor} ({self.first}-{self.last})"


@dataclass(frozen=True, slots=True)
class Shipment:
    """Every edit shipping one task makes, as data, before or after it is written."""

    task_id: str
    ledger: Insertion
    roadmap: Document
    removed_from: int
    improvements: Document | None = None
    dropped: Section | None = None
    #: Why nothing was dropped, when nothing was: a task can ship without a rationale
    #: section, and silence about that would read as a section that was deleted.
    kept: str | None = None
    #: Open lines whose `(deps: …)` still annotate this task as unfinished (RK8).
    stale: tuple[str, ...] = ()

    def save(self) -> None:
        """Write the files. Nothing here can fail on the format — that was decided."""
        self.ledger.document.save()
        self.roadmap.save()
        if self.improvements is not None:
            self.improvements.save()


def ship(config: Config, task_id: str, *, why: str | None = None) -> Shipment:
    """Move one task from the backlog to the ledger. Validates all three edits first."""
    roadmap = config.document("roadmap")
    ledger = config.document("changelog")

    entry = roadmap.by_id().get(task_id)
    if entry is None:
        raise NotOpen(
            task_id,
            config.relative(config.path("roadmap")),
            shipped=task_id in ledger.by_id(),
        )
    duplicate = ledger.by_id().get(task_id)
    if duplicate is not None:
        raise AlreadyShipped(
            task_id, config.relative(config.path("changelog")), duplicate.lineno
        )

    insertion = place(ledger, _as_shipped(config, entry.task, why))
    remaining = _remove_entry(roadmap, entry.index)
    improvements, dropped, kept = _drop_section(config, entry.task.ref)

    return Shipment(
        task_id=task_id,
        ledger=insertion,
        roadmap=remaining,
        removed_from=entry.lineno,
        improvements=improvements,
        dropped=dropped,
        kept=kept,
        stale=_stale_dependents(config, remaining, task_id),
    )


def _as_shipped(config: Config, task: Task, why: str | None) -> Task:
    """The same task as the ledger states it: ✅, no deps, no pointer.

    The pointer is dropped because the section it names is deleted in the same command,
    and the deps because a dependency is a planning fact that a shipped line has none
    left to state — both of which the ledger schema (`as_ledger`) already refuses.
    """
    return replace(
        task,
        status=config.schema.shipped_marker,
        deps=(),
        ref=None,
        why=why if why is not None else task.why,
    )


def _remove_entry(document: Document, index: int) -> Document:
    """Take the line out, and the blank line the removal doubled.

    A task line sits between blanks when it is the last one in its block, so removing it
    leaves a paragraph break the file never had. Both spellings round-trip, which is
    exactly why nothing downstream would catch it.
    """
    updated = document.remove_line(index)
    lines = updated.lines
    if index > 0 and index < len(lines) and blank(lines[index - 1]) and blank(lines[index]):
        return updated.remove_line(index)
    if index >= len(lines) and index > 0 and blank(lines[index - 1]):
        # The block was last in the file: its trailing blank has nothing left to separate.
        return updated.remove_line(index - 1)
    return updated


def _drop_section(
    config: Config, anchor: str | None
) -> tuple[Document | None, Section | None, str | None]:
    """Delete the rationale section the shipped line pointed at, if there is one.

    Absence is reported, never refused: a task can ship without a section, and a command
    that fails over it would be an obstacle at the one moment the author is finishing.
    """
    if anchor is None:
        return None, None, "the line carried no pointer"
    if not config.has("improvements"):
        return None, None, "this project declares no improvements file"
    document = config.document("improvements")
    span = _span(document, anchor)
    if span is None:
        return (
            None,
            None,
            f"no §{anchor} section in {config.relative(config.path('improvements'))}",
        )
    start, end, heading = span
    # Reported from the heading, not from `start`: the deletion may reach back over the
    # blank line above it, and a report has to name the section a reader can see.
    section = Section(anchor=anchor, text=heading.text, first=heading.lineno, last=end)
    for _ in range(end - start):
        document = document.remove_line(start)
    return document, section, None


def _span(document: Document, anchor: str) -> tuple[int, int, Heading] | None:
    """The `[start, end)` lines of the `§anchor` section, subsections included.

    A section ends where the next heading of the same or higher level begins, so a
    rationale that grew subsections is deleted whole — the alternative leaves orphaned
    prose under the heading of the next task, attributed to it.
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
            # Last in the file: the blank that separated it from the section above has
            # nothing left to separate.
            while start > 0 and blank(document.lines[start - 1]):
                start -= 1
        return start, end, heading
    return None


def _names(text: str, anchor: str) -> bool:
    """Does this heading carry `§anchor` — and not `§anchor` as a prefix of another?"""
    marked = f"§{anchor}"
    if not text.startswith(marked):
        return False
    rest = text[len(marked) :]
    return not rest or not (rest[0].isalnum() or rest[0] == ".")


def _stale_dependents(config: Config, roadmap: Document, task_id: str) -> tuple[str, ...]:
    """Open lines whose dep annotation for this task no longer matches its status."""
    shipped = config.schema.shipped_marker
    return tuple(
        entry.task.id
        for entry in roadmap.entries
        for dep in entry.task.deps
        if dep.id == task_id and dep.marker != shipped
    )
