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

**A fourth door starts nowhere** (RK41). All three above begin from an open roadmap line,
so work that was finished before it was ever planned — a defect found on the way to
something else, fixed, real, shipped — has no route into the ledger except a fictitious
roadmap line shipped in the same breath. :func:`record` is that route made honest: it
writes the ledger entry and touches nothing else, which is why RK7 survives it untouched
— the line never exists open, so there is no second file to disagree with.

**And a door out of the ledger, for exactly one shape** (RK67). Every door above only ever
adds an entry, which is right for history and wrong for a duplicate: an id the ledger states
twice states one decision twice, `lint`'s `id.duplicate` reports it, and until now nothing but
the hand-edit the hook denies could act. :func:`drop` is the inverse of the door that wrote it
and refuses unless the id is there **twice** — removing the only record of a decision is
deleting history rather than de-duplicating it. The later entry goes: the first is where the
reader already found it. Prose that is wrong is `amend`'s question one file over, and an entry
that should never have existed is a decision the author states in the commit that removes it.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from roadkeep.authoring import Insertion, place, refuse_reuse
from roadkeep.backlog import Backlog, NotOpen
from roadkeep.config import Config
from roadkeep.document import Document, Entry, Heading, blank
from roadkeep.ids import next_id
from roadkeep.markers import refresh
from roadkeep.schema import Task
from roadkeep.sections import NoSuchSection, Section, nested, pointers
from roadkeep.sections import drop as drop_section

__all__ = [
    "AlreadyRecorded",
    "AlreadyShipped",
    "Closure",
    "Departure",
    "Dropped",
    "NoRestatement",
    "NoSuchReplacement",
    "NotDuplicated",
    "NotOpen",
    "Record",
    "Section",
    "Shipment",
    "drop",
    "record",
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


class NoRestatement(ValueError):
    """`--why` where the ledger is not written (RK62).

    On the closing path the entry already exists and this command deliberately leaves it alone,
    so the sentence has nothing to restate. Refused rather than dropped: a flag silently
    ignored is a flag the caller believes took effect.
    """

    def __init__(self, task_id: str, recorded: Entry) -> None:
        super().__init__(
            f"{task_id} is already recorded as {recorded.task.status} at line "
            f"{recorded.lineno}, so this call only closes its roadmap line: --why restates "
            f"the ledger's sentence, and the ledger is not written here"
        )


class NotDuplicated(ValueError):
    """`drop` against an id the ledger does not state twice (RK67).

    The narrow condition is this door's whole safety: de-duplicating is the one removal that
    cannot lose a decision, because the decision stays on the line the reader already found.
    So the message names the count it *did* find — "not a duplicate" reads as "no such entry"
    when it is one entry, which is the case where the author has to hear the difference.
    """

    def __init__(self, task_id: str, where: str, linenos: tuple[int, ...]) -> None:
        self.task_id = task_id
        self.linenos = linenos
        found = f"once, at line {linenos[0]}" if linenos else "nowhere"
        super().__init__(
            f"{task_id} is in {where} {found}: this removes the later of two entries for one "
            f"id, and the only record of a decision is history rather than a duplicate"
        )


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
    #: The anchors that went with it, nested under the one named (RK78). Reported because a
    #: drop is a subtree, and a transaction that says "one section" about five is one whose
    #: size the author only learns from the diff.
    nested: tuple[str, ...] = ()
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


@dataclass(frozen=True, slots=True)
class Closure:
    """The rest of a transaction that never completed (RK62).

    A roadmap line whose id the ledger *already* records has nowhere to go: `ship` cannot write
    a second entry, `retire` would claim a departure that did not happen, and the hook denies
    the hand-edit. So closing the line is its own outcome — the same edits a departure makes
    minus the one that is already done, and the ledger is opened only to be read.

    Not a :class:`Departure` with a None: the field that would be None is the entry, which is
    the whole subject of that shape. Here the entry is the *evidence*, and it is somebody
    else's write.
    """

    task_id: str
    #: The roadmap as this write leaves it: without the line, dependents re-annotated.
    roadmap: Document
    removed_from: int
    #: The ledger entry that already existed, and its marker — ✅ or 🗑, because a reader has
    #: to know which door this id went through before its line was left behind.
    recorded: Entry
    improvements: Document | None = None
    dropped: Section | None = None
    kept: str | None = None
    #: The anchors nested under the one dropped, as :class:`Departure` reports them (RK78).
    nested: tuple[str, ...] = ()
    refreshed: tuple[str, ...] = ()
    dependents: tuple[str, ...] = ()

    @property
    def marker(self) -> str:
        return self.recorded.task.status

    def save(self) -> None:
        """Write the roadmap and the prose file. The ledger is never opened for writing."""
        self.roadmap.save()
        if self.improvements is not None:
            self.improvements.save()


@dataclass(frozen=True, slots=True)
class Record:
    """A ledger entry that had no roadmap line to leave (RK41).

    Not a :class:`Departure`: there is no line removed, no section dropped and no
    `removed_from` to report, and a shared shape would carry three fields that are
    permanently None plus the invitation to make them meaningful later.
    """

    task_id: str
    ledger: Insertion
    #: The roadmap as this write leaves it — the same document unless an annotation
    #: elsewhere became derivable (RK8), which is what :attr:`refreshed` names.
    roadmap: Document
    refreshed: tuple[str, ...] = ()
    #: The marker the entry carries: ✅, the only one a record can mean.
    marker: str = ""

    def save(self) -> None:
        """Write the ledger, and the roadmap only if a line in it actually changed."""
        self.ledger.document.save()
        if self.refreshed:
            # The roadmap is not part of this transaction, so it is not rewritten to the
            # same bytes: an untouched file with a moved mtime reads as an edit to every
            # hook watching it, and "touched nothing else" has to be true on disk.
            self.roadmap.save()


@dataclass(frozen=True, slots=True)
class Dropped:
    """One of two ledger entries for a single id, removed (RK67).

    No roadmap field, and that is the shape of the guarantee rather than an omission: an id
    the ledger still records once is an id every annotation elsewhere is still true about, so
    there is nothing to re-derive (RK8) and no second file to open. :class:`Record` had to say
    "touched nothing else" in a docstring; here there is nothing that could.
    """

    task_id: str
    #: The ledger as this write leaves it: one entry for the id, and no doubled blank.
    ledger: Document
    removed_from: int
    #: The line the decision keeps, and the marker it carries there — printed, because a
    #: duplicate whose two entries disagree about the door is a fact the author has to see.
    kept: int
    kept_marker: str
    #: The block the ledger still files this decision under — the kept entry's, since that is
    #: the one that is left to answer for it.
    block: str = ""
    #: The marker the removed entry carried, which is normally the same one.
    marker: str = ""

    def save(self) -> None:
        """Write the ledger. Nothing else was opened, so nothing else can be touched."""
        self.ledger.save()


def drop(config: Config, task_id: str) -> Dropped:
    """Remove the later of two ledger entries for one id (RK67).

    Refused unless the id is recorded **twice**, so the operation is de-duplication and can
    never be a deletion of history: what stays is the first entry, where a reader who already
    found this decision found it. With three, the last goes and a second call is the next one —
    convergent by construction, rather than one command that decides how many to remove.

    The whole write is the ledger, which is what makes this narrow enough to exist at all: no
    dep annotation changes when an id the file still records goes from two entries to one.
    """
    ledger = config.document("changelog")
    twins = tuple(entry for entry in ledger.entries if entry.task.id == task_id)
    if len(twins) < 2:
        raise NotDuplicated(
            task_id,
            config.relative(config.path("changelog")),
            tuple(entry.lineno for entry in twins),
        )
    later = twins[-1]
    return Dropped(
        task_id=task_id,
        ledger=_remove_entry(ledger, later.index),
        removed_from=later.lineno,
        kept=twins[0].lineno,
        kept_marker=twins[0].task.status,
        block=twins[0].task.block,
        marker=later.task.status,
    )


def ship(config: Config, task_id: str, *, why: str | None = None) -> Departure | Closure:
    """Move one task from the backlog to the ledger. Validates all three edits first.

    Or, when the ledger already records the id, close the roadmap line alone (RK62): that is
    not a second entry, it is the rest of a transaction that never completed — which is the
    shape adoption produces, because a project that moved a task to its changelog by hand and
    left a pointer behind was following its own convention.

    `why` is refused on that path rather than ignored: it restates the *ledger's* sentence, and
    the ledger is not written here. A flag silently dropped is a flag the caller believes took
    effect.
    """
    recorded = _already_recorded(config, task_id)
    if recorded is None:
        return _depart(config, task_id, config.schema.shipped_marker, why)
    if why is not None:
        raise NoRestatement(task_id, recorded)
    return _close(config, task_id, recorded)


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


def record(
    config: Config,
    *,
    block: str,
    symptom: str,
    why: str,
    task_id: str | None = None,
) -> Record:
    """Write a ledger entry for work that shipped without ever being planned (RK41).

    The fields are refused at input exactly as `add` refuses them (L1), against
    :meth:`~roadkeep.schema.Schema.as_ledger` rather than the roadmap's schema — so the
    marker is ✅, the block heading must already be declared in the ledger, and a dep or a
    pointer is not accepted rather than dropped: there is no open line for a dep to be a
    planning fact about, and no rationale section for a pointer to resolve to.

    The id is derived like any other (RK4) and refused if anything anywhere already
    mentions it, so recording cannot quietly claim an id the roadmap is holding. The
    `symptom` rule is the one that must not soften: what did not work, stated so it could
    have been falsified — never the name of the patch that closed it (L4 leaves that to
    the caller, here as everywhere).
    """
    if task_id is None:
        task_id = next_id(config)
    else:
        refuse_reuse(config, task_id)

    ledger = config.document("changelog")
    marker = config.schema.shipped_marker
    insertion = place(
        ledger,
        Task(id=task_id, status=marker, block=block, symptom=symptom, why=why),
    )
    # Resolved against the state this write creates, for the same reason `_depart` does it
    # (RK8): an id is normally too new for any line to name, but a range dep can already
    # span it, and an annotation left un-derived by one door is one nothing revisits.
    derived = refresh(
        Backlog(config=config, roadmap=config.document("roadmap"), ledger=insertion.document)
    )
    return Record(
        task_id=task_id,
        ledger=insertion,
        roadmap=derived.document,
        refreshed=derived.changed,
        marker=marker,
    )


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
    improvements, dropped, kept, taken = _drop_section(
        config, entry.task.ref, leaving=task_id
    )
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
        nested=taken,
        refreshed=derived.changed,
        marker=marker,
        dependents=tuple(
            e.task.id for e in derived.document.entries if task_id in e.task.dep_ids
        ),
    )


def _others_pointing(config: Config, anchor: str, leaving: str) -> tuple[str, ...]:
    """Open lines other than this one whose pointer names the same anchor (RK64)."""
    return tuple(
        entry.task.id
        for entry in config.document("roadmap").entries
        if entry.task.ref == anchor and entry.task.id != leaving
    )


def _already_recorded(config: Config, task_id: str) -> Entry | None:
    """The ledger entry this roadmap line was left behind by — three conditions, not two.

    A ledger entry and a roadmap line for one id is *two* different situations, and only one of
    them is a leftover. The roadmap line has to carry a marker the roadmap may not carry —
    ✅ or 🗑 — because that is what says the line was already treated as gone. A line with a
    legal open marker is a live task whose id the ledger also mentions: Shio's `⏳ SH238` names
    the half that has not shipped, and closing it deleted a real task and a 224-word section
    until this condition was added. That case stays :class:`AlreadyRecorded`, and `lint`'s
    `id.two-files` is what reports it, because deciding whose id it is belongs to the author.
    """
    if not config.has("changelog") or not config.path("changelog").is_file():
        return None
    open_line = config.document("roadmap").by_id().get(task_id)
    if open_line is None:
        return None
    schema = config.schema
    if open_line.task.status not in (schema.shipped_marker, schema.retired_marker):
        return None
    return config.document("changelog").by_id().get(task_id)


def _close(config: Config, task_id: str, recorded: Entry) -> Closure:
    """Everything a departure does except the entry, which is already on disk (RK62)."""
    roadmap = config.document("roadmap")
    entry = roadmap.by_id()[task_id]
    remaining = _remove_entry(roadmap, entry.index)
    improvements, dropped, kept, taken = _drop_section(
        config, entry.task.ref, leaving=task_id
    )
    derived = refresh(
        Backlog(config=config, roadmap=remaining, ledger=config.document("changelog"))
    )
    return Closure(
        task_id=task_id,
        roadmap=derived.document,
        removed_from=entry.lineno,
        recorded=recorded,
        improvements=improvements,
        dropped=dropped,
        kept=kept,
        nested=taken,
        refreshed=derived.changed,
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
        # And at column zero (RK49): the nesting said which roadmap line this one belonged
        # under, and that line is not in the ledger — an indented entry would be nested
        # beneath whatever entry happened to precede it.
        indent="",
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
    config: Config, anchor: str | None, *, leaving: str = ""
) -> tuple[Document | None, Section | None, str | None, tuple[str, ...]]:
    """Delete the rationale section the departing line pointed at, if it is only that line's.

    Absence is reported, never refused: a task can ship without a section, and a command
    that fails over it would be an obstacle at the one moment the author is finishing.

    So is a section with **more than one owner** (RK64). Under `ref_scheme = "id"` the anchor
    is the id and nothing else can name it; under an outline, four of Shio's lines point at one
    epic design, and deleting it when the first of them ships left three live pointers resolving
    to nothing. The section stays and the reason is reported in the same field.

    A section **nesting** one of those is the same fact one level down, and it is a refusal
    rather than a report (RK78): keeping the section is a legitimate outcome of shipping,
    while a subtree that cannot be deleted whole is a transaction the author has to resolve —
    so :class:`~roadkeep.sections.SectionOccupied` propagates, and by the ordering this module
    already guarantees, no file has been touched when it does. What the drop *did* take is
    returned with it, because a deletion that reports one section and removes five is how the
    same defect stayed invisible for 160 lines.
    """
    if anchor is None:
        return None, None, "the line carried no pointer", ()
    if not config.has("improvements"):
        return None, None, "this project declares no improvements file", ()
    others = _others_pointing(config, anchor, leaving)
    if others:
        return None, None, f"§{anchor} is also pointed at by {', '.join(others)}", ()
    # The grammar of a section lives in one place (RK9), so shipping calls it rather than
    # keeping a second opinion about where a section ends.
    improvements = config.document("improvements")
    taken = tuple(child.anchor for child in nested(improvements, anchor))
    try:
        document, section = drop_section(
            improvements, anchor, claimed=pointers(config, leaving=leaving)
        )
    except NoSuchSection:
        return (
            None,
            None,
            f"no §{anchor} section in {config.relative(config.path('improvements'))}",
            (),
        )
    return document, section, None, taken


