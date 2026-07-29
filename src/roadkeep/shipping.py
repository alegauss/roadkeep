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

The dep annotations of every line that named this task are re-derived in the same
transaction (RK8), because `(deps: RK5)` becomes a false statement at exactly the moment
this command runs and nothing else would ever revisit it.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from roadkeep.authoring import Insertion, place
from roadkeep.backlog import Backlog, NotOpen
from roadkeep.config import Config
from roadkeep.document import Document, Heading, blank
from roadkeep.markers import refresh
from roadkeep.schema import Task
from roadkeep.sections import NoSuchSection, Section
from roadkeep.sections import drop as drop_section

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
    #: Open lines whose `(deps: …)` this ship made true again (RK8).
    refreshed: tuple[str, ...] = ()

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
    # Resolved against the state this ship *creates* — the id is in the ledger and gone
    # from the roadmap — so a dependent's annotation is derived from what will be on
    # disk and not from what was (RK8).
    derived = refresh(
        Backlog(config=config, roadmap=remaining, ledger=insertion.document)
    )

    return Shipment(
        task_id=task_id,
        ledger=insertion,
        roadmap=derived.document,
        removed_from=entry.lineno,
        improvements=improvements,
        dropped=dropped,
        kept=kept,
        refreshed=derived.changed,
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
    # The grammar of a section lives in one place (RK9), so shipping calls it rather than
    # keeping a second opinion about where a section ends.
    try:
        document, section = drop_section(config.document("improvements"), anchor)
    except NoSuchSection:
        return (
            None,
            None,
            f"no §{anchor} section in {config.relative(config.path('improvements'))}",
        )
    return document, section, None


