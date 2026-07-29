"""A line leaving the roadmap: three edits across three files, or none of them (RK6, RK32).

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

**A line leaves by three doors and this module now records all three** (RK32). `ship` is
the first; :func:`retire` is the other two, superseded and abandoned, and it is the *same*
transaction with a different marker rather than a second one — because the failure being
fixed is that two of the three doors wrote nothing at all, not that they wrote it wrongly.
What survives a retirement is one line under the block it belonged to: the symptom moved
verbatim, and a `why` whose derived prefix names the replacement so the pointer is forward
and written at the moment of the decision. Never the design it replaced — an accreting
rationale file is the 539 KB this project exists to refuse.
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

__all__ = [
    "AlreadyRecorded",
    "AlreadyShipped",
    "Departure",
    "NoSuchReplacement",
    "NotOpen",
    "Section",
    "Shipment",
    "retire",
    "ship",
]


class AlreadyRecorded(ValueError):
    """A second ledger entry for one id is two records of one decision.

    The message names which door the id already went through, because "already in the
    changelog" sends a reader looking for a ✅ that may be a 🗑 (RK32).
    """

    def __init__(self, task_id: str, where: str, lineno: int, marker: str) -> None:
        self.task_id = task_id
        self.lineno = lineno
        self.marker = marker
        super().__init__(
            f"{task_id} is already recorded as {marker} in {where}:{lineno}: a second "
            f"entry would make the ledger disagree with itself about how it left"
        )


#: The names these had when shipping was the only door (RK6), kept because they read
#: better at a `ship` call site: an id can now be retired as well as shipped, and both are
#: the same refusal and the same transaction.
AlreadyShipped = AlreadyRecorded


class NoSuchReplacement(KeyError):
    """A forward pointer to an id that is in neither file (RK32).

    Refused, because a pointer to nothing is the exact defect this records against: the
    reader of the gap would be sent somewhere else that does not explain it either.
    """

    def __init__(self, replacement: str, task_id: str) -> None:
        super().__init__(
            f"{replacement} is in neither file, so it cannot be what replaces "
            f"{task_id}: retire it against an id that exists, or as abandoned"
        )


@dataclass(frozen=True, slots=True)
class Departure:
    """Every edit one line's departure makes, as data, before or after it is written.

    One shape for both doors (RK6, RK32): the marker is the only thing that differs, and a
    second dataclass would be a second place to add the next field to.
    """

    task_id: str
    ledger: Insertion
    roadmap: Document
    removed_from: int
    improvements: Document | None = None
    dropped: Section | None = None
    #: Why nothing was dropped, when nothing was: a task can ship without a rationale
    #: section, and silence about that would read as a section that was deleted.
    kept: str | None = None
    #: Open lines whose `(deps: …)` this write made true again (RK8).
    refreshed: tuple[str, ...] = ()
    #: The marker the ledger line carries: ✅ shipped, 🗑 retired.
    marker: str = ""
    #: Open lines that still name this id. Reported and not refused: a supersession is
    #: legitimate and those lines are the author's next edit, which `lint` (RK14) gates.
    dependents: tuple[str, ...] = ()

    def save(self) -> None:
        """Write the files. Nothing here can fail on the format — that was decided."""
        self.ledger.document.save()
        self.roadmap.save()
        if self.improvements is not None:
            self.improvements.save()


Shipment = Departure


def ship(config: Config, task_id: str, *, why: str | None = None) -> Departure:
    """Move one task from the backlog to the ledger. Validates all three edits first."""
    return _depart(config, task_id, config.schema.shipped_marker, why)


def retire(
    config: Config,
    task_id: str,
    *,
    reason: str,
    superseded_by: str | None = None,
) -> Departure:
    """Record a line leaving without shipping: superseded by a named id, or abandoned.

    The `why` is a derived prefix plus the author's own sentence — the same split as every
    other field the tool fills in (RK8): "superseded by RK41" is a fact this command holds
    and the reason is prose it will not write (L4).
    """
    if superseded_by is not None:
        if superseded_by == task_id:
            raise NoSuchReplacement(superseded_by, task_id)
        known = set(config.document("roadmap").by_id())
        if config.has("changelog") and config.path("changelog").is_file():
            known |= set(config.document("changelog").by_id())
        if superseded_by not in known:
            raise NoSuchReplacement(superseded_by, task_id)
        why = f"superseded by {superseded_by}: {reason}"
    else:
        why = f"abandoned: {reason}"
    return _depart(config, task_id, config.schema.retired_marker, why)


def _depart(
    config: Config, task_id: str, marker: str, why: str | None
) -> Departure:
    """The one transaction both doors are: validate everything, then write nothing yet."""
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
        raise AlreadyRecorded(
            task_id,
            config.relative(config.path("changelog")),
            duplicate.lineno,
            duplicate.task.status,
        )

    insertion = place(ledger, _as_recorded(entry.task, marker, why))
    remaining = _remove_entry(roadmap, entry.index)
    improvements, dropped, kept = _drop_section(config, entry.task.ref)
    # Resolved against the state this write *creates* — the id is in the ledger and gone
    # from the roadmap — so a dependent's annotation is derived from what will be on
    # disk and not from what was (RK8).
    derived = refresh(
        Backlog(config=config, roadmap=remaining, ledger=insertion.document)
    )

    return Departure(
        task_id=task_id,
        ledger=insertion,
        roadmap=derived.document,
        removed_from=entry.lineno,
        improvements=improvements,
        dropped=dropped,
        kept=kept,
        refreshed=derived.changed,
        marker=marker,
        dependents=tuple(
            e.task.id for e in derived.document.entries if task_id in e.task.dep_ids
        ),
    )


def _as_recorded(task: Task, marker: str, why: str | None) -> Task:
    """The same task as the ledger states it: one marker, no deps, no pointer.

    The pointer is dropped because the section it names is deleted in the same command,
    and the deps because a dependency is a planning fact that a departed line has none
    left to state — both of which the ledger schema (`as_ledger`) already refuses.
    """
    return replace(
        task,
        status=marker,
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


