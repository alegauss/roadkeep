"""Writing the line, so the limit is met before the sentence exists (RK5).

This is the module the whole tool is for. Everything before it proves the format can
be read; `add` is where the format starts being *enforced at the moment of writing*
(L1), and the difference is not convenience:

* A linter reports after the prose exists. The tokens are already spent, and the
  author is being asked to delete work they just justified — which is why the ninety-two
  over-length lines that motivated this tool were written by authors who knew the rule.
* `add` refuses an over-length ``why`` **before** a second sentence is composed to fill
  it, and the refusal names the limit, the actual length, and the file the remainder
  belongs in. *The saving is the analysis, not the characters:* the author stops asking
  "is this too long, what would I cut?" and starts calling a command.

Three decisions that are the point of the module rather than details of it:

* **Nothing is written unless everything validates.** :func:`place` renders, inserts and
  re-reads in memory, and the file is touched only after the result round-trips (L3). A
  partial write to a governed file is the failure mode the tool exists to remove.
* **The pointer is derived, never asked for.** Under ``ref_scheme = "id"`` the anchor is
  the task's own id (RK27), so `add` supplies it; passing a different one is refused
  rather than honoured, because a pointer an author can choose is a pointer an author
  can get wrong.
* **The block must already be declared.** A heading is the only thing that declares a
  block (RK37), so `add` files a task under one and never creates one — a heading
  invented by a write puts the task where nothing looks for it.

What it deliberately does not do: write prose (L4 — it has no opinion on the sentence,
only its length and count), derive the dep markers (RK8 does that on every write, and
until then a marker is passed through exactly as typed), or fix a file that has drifted.

:func:`set_status` (RK7) lives here for the same reason `add` does — it is a write to the
roadmap — and adds exactly one rule: the marker has one home, so a sibling file carrying
one for the same id is refused instead of reconciled.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace

from roadkeep.backlog import Backlog, NotOpen
from roadkeep.config import ROLES, Config
from roadkeep.document import Document, Entry, Heading, UnknownBlock, blank, read_deps
from roadkeep.ids import next_id, scan
from roadkeep.markers import derive, refresh
from roadkeep.schema import Task


class IdInUse(ValueError):
    """An id is the one decision that cannot be taken back once it is committed."""

    def __init__(self, task_id: str, where: str, lineno: int) -> None:
        self.task_id = task_id
        self.where = where
        self.lineno = lineno
        super().__init__(
            f"{task_id} already occurs at {where}:{lineno}: an id is never reused, "
            f"not even one that was retired — omit --id and it is derived"
        )


class StatusElsewhere(ValueError):
    """A marker in a second file is a status two files can come to disagree about."""

    def __init__(
        self, task_id: str, role: str, where: str, lineno: int, marker: str
    ) -> None:
        self.task_id = task_id
        self.role = role
        super().__init__(
            f"{task_id} already carries {marker} in the {role} at {where}:{lineno}: "
            f"status lives in exactly one file, because two files that both express it "
            f"will eventually express different ones and nothing says which is right"
        )


class DuplicateId(ValueError):
    """Two lines for one id are two statuses for one task, in one file."""

    def __init__(self, task_id: str, where: str, linenos: Sequence[int]) -> None:
        self.task_id = task_id
        self.linenos = tuple(linenos)
        lines = ", ".join(str(number) for number in self.linenos)
        super().__init__(
            f"{task_id} appears at {where}:{lines}: one line per task, and two lines "
            f"carry two statuses — `lint` reports this, and it is fixed by hand"
        )


class DerivedPointer(ValueError):
    """Under the id scheme there is no anchor to choose (RK27)."""

    def __init__(self, task_id: str, given: str) -> None:
        super().__init__(
            f"the pointer is derived from the id (§{task_id}), so --ref {given!r} "
            f"names a section chosen by hand: drop it, or set ref_scheme = \"outline\""
        )


@dataclass(frozen=True, slots=True)
class Insertion:
    """The line that was written, and the document that now holds it."""

    document: Document
    entry: Entry

    @property
    def rendered(self) -> str:
        return self.entry.raw

    @property
    def lineno(self) -> int:
        return self.entry.lineno


def compose(
    config: Config,
    *,
    task_id: str,
    block: str,
    symptom: str,
    why: str,
    status: str | None = None,
    deps: Sequence[str] = (),
    ref: str | None = None,
) -> Task:
    """The fields, as a :class:`Task`. Fills in what is derivable; validates nothing.

    Validation stays in :func:`place` so that every violation is reported at once — a
    constructor that raises can only ever name the first thing wrong with a line.
    """
    schema = config.schema
    if schema.ref_scheme == "id":
        if ref is not None and ref != task_id:
            raise DerivedPointer(task_id, ref)
        ref = task_id
    return Task(
        id=task_id,
        # The default is the first marker this project declares, not a hardcoded 📋:
        # the marker set is configuration (L6), so the default has to come from it.
        status=status or schema.markers[0],
        block=block,
        symptom=symptom,
        why=why,
        deps=read_deps(", ".join(deps), schema) if deps else (),
        ref=ref,
    )


def place(document: Document, task: Task) -> Insertion:
    """Validate, render, insert — in memory, and refuse before any of it.

    Raises :class:`~roadkeep.schema.SchemaError` with every violation,
    :class:`UnknownBlock` when no heading declares the block, and
    :class:`~roadkeep.document.RoundTripError` when either the file already carries a
    line the schema would rewrite or the new line does not read back as it was written.
    """
    document.schema.check(task)
    heading = document.heading(task.block)
    if heading is None:
        raise UnknownBlock(
            task.block,
            sorted({h.label for h in document.headings if h.label}),
            word=document.schema.heading_word,
        )

    rendered = document.schema.render(task)
    index, payload = _placement(document, heading, rendered)
    updated = document
    for offset, raw in enumerate(payload):
        updated = updated.insert_line(index + offset, raw)
    # The new line is canonical by construction — and the guard is the point: a line
    # this tool wrote and cannot read back is exactly what must never reach the disk.
    updated.ensure_writable()

    lineno = index + payload.index(rendered) + 1
    entry = next(e for e in updated.entries if e.lineno == lineno)
    return Insertion(document=updated, entry=entry)


def add(
    config: Config,
    *,
    block: str,
    symptom: str,
    why: str,
    status: str | None = None,
    deps: Sequence[str] = (),
    ref: str | None = None,
    task_id: str | None = None,
    family: str | None = None,
) -> Insertion:
    """Insert one task into the roadmap and save it. The whole write path.

    The id is derived unless one is given, and a given id that occurs anywhere is
    refused (:class:`IdInUse`) — including in prose, because a number a document
    already mentions is a number two designs would share in the history.

    ``family`` picks which track the derived id counts in (RK74) and defaults to the first
    the project declares, which is the only answer for the projects that declare one. It
    is never inferred from the block: a track is not a block, and a tool that mapped one
    to the other would be holding an opinion about someone else's backlog.

    The dep annotations are derived here too (RK8), so `--dep RK1` renders `RK1 ✅` when
    RK1 has shipped and the author never types a marker. Only this line is derived: no
    existing line can name an id that did not exist a moment ago.
    """
    if task_id is None:
        task_id = next_id(config, family)
    else:
        refuse_reuse(config, task_id)
    task = compose(
        config,
        task_id=task_id,
        block=block,
        symptom=symptom,
        why=why,
        status=status,
        deps=deps,
        ref=ref,
    )
    insertion = place(config.document("roadmap"), derive(Backlog.load(config), task))
    insertion.document.save()
    return insertion


@dataclass(frozen=True, slots=True)
class StatusChange:
    """The line as it now reads, and the marker it carried before (RK7)."""

    document: Document
    entry: Entry
    before: str
    #: Other lines whose dep annotation this write made true again (RK8).
    refreshed: tuple[str, ...] = ()

    @property
    def after(self) -> str:
        return self.entry.task.status

    @property
    def changed(self) -> bool:
        return self.before != self.after

    @property
    def rendered(self) -> str:
        return self.entry.raw

    @property
    def lineno(self) -> int:
        return self.entry.lineno


def set_status(config: Config, task_id: str, marker: str) -> StatusChange:
    """Write one task's marker in the roadmap, and refuse if a sibling carries one.

    A marker is maturity, and maturity has one home. Two files that both express it will
    eventually express different values, and at that point there is no rule that says
    which one is the status — so the second one is refused rather than reconciled
    (:class:`StatusElsewhere`), and so is a second line for the same id in this file
    (:class:`DuplicateId`).

    ✅ is refused here by the schema itself, not by a special case: shipped work is the
    ledger's to state, and `ship` (RK6) is the only thing that puts it there.

    A marker this task's dependents cached is stale the moment it changes, so the write
    re-derives every annotation in the file (RK8) and names the lines it corrected.
    """
    backlog = Backlog.load(config)
    roadmap = backlog.roadmap
    entry = roadmap.by_id().get(task_id)
    if entry is None:
        raise NotOpen(
            task_id,
            config.relative(config.path("roadmap")),
            shipped=task_id in backlog.shipped(),
        )
    twins = tuple(e.lineno for e in roadmap.entries if e.task.id == task_id)
    if len(twins) > 1:
        raise DuplicateId(task_id, config.relative(config.path("roadmap")), twins)
    _refuse_sibling_status(config, task_id)

    updated = config.schema.check(replace(entry.task, status=marker))
    if updated.status == entry.task.status:
        # Nothing to write: rewriting the same bytes would make a no-op look like an
        # edit to every tool that watches the file.
        return StatusChange(document=roadmap, entry=entry, before=entry.task.status)
    derived = refresh(replace(backlog, roadmap=roadmap.replace_task(entry, updated)))
    derived.document.save()
    return StatusChange(
        document=derived.document,
        entry=next(e for e in derived.document.entries if e.lineno == entry.lineno),
        before=entry.task.status,
        refreshed=tuple(name for name in derived.changed if name != task_id),
    )


@dataclass(frozen=True, slots=True)
class Amendment:
    """One line as it now reads, and as it read before (RK65).

    Not a :class:`StatusChange` with more fields: the marker has its own door because status is
    maturity, and this one exists for the fields a project *adopting* the tool has to correct —
    which is a different question with a different refusal.
    """

    document: Document
    entry: Entry
    before: Task
    #: Other lines whose dep annotation this write made true again (RK8).
    refreshed: tuple[str, ...] = ()

    @property
    def changed(self) -> tuple[str, ...]:
        """Which fields actually differ, in field order — empty when nothing was written."""
        return tuple(
            name
            for name in ("why", "deps", "ref")
            if getattr(self.before, name) != getattr(self.entry.task, name)
        )

    @property
    def rendered(self) -> str:
        return self.entry.raw


def amend(
    config: Config,
    task_id: str,
    *,
    why: str | None = None,
    deps: Sequence[str] | None = None,
    ref: str | None = None,
) -> Amendment:
    """Correct one open line's `why`, `deps` or `ref`. Validated at input, or nothing (RK65).

    The three fields a project that adopted the tool has to be able to fix: a pointer it never
    had, a dep naming an id that is in neither file, and the compression of a `why` that was a
    paragraph before the limit existed. `retire` plus `add` would lose the id, and the id is
    what the history is keyed on.

    `symptom` is deliberately absent: it is the falsifiable claim the line *is*, so a different
    one is a different task — and the corpus says it is not the problem (0 of Shio's 78 over the
    limit, against 70 of its whys). `status` is absent because :func:`set_status` is its door.

    Nothing is written when nothing differs: rewriting the same bytes makes a no-op look like an
    edit to every hook watching the file.
    """
    backlog = Backlog.load(config)
    roadmap = backlog.roadmap
    entry = roadmap.by_id().get(task_id)
    if entry is None:
        raise NotOpen(
            task_id,
            config.relative(config.path("roadmap")),
            shipped=task_id in backlog.shipped(),
        )
    twins = tuple(e.lineno for e in roadmap.entries if e.task.id == task_id)
    if len(twins) > 1:
        raise DuplicateId(task_id, config.relative(config.path("roadmap")), twins)

    wanted = replace(
        entry.task,
        why=entry.task.why if why is None else why,
        deps=entry.task.deps if deps is None else read_deps(", ".join(deps), config.schema),
        ref=entry.task.ref if ref is None else ref,
    )
    # Derived on write like every other annotation (RK8): the author names the dep and the
    # tool states whether it shipped.
    updated = config.schema.check(derive(backlog, wanted))
    if updated == entry.task:
        return Amendment(document=roadmap, entry=entry, before=entry.task)
    derived = refresh(replace(backlog, roadmap=roadmap.replace_task(entry, updated)))
    derived.document.save()
    return Amendment(
        document=derived.document,
        entry=next(e for e in derived.document.entries if e.lineno == entry.lineno),
        before=entry.task,
        refreshed=tuple(name for name in derived.changed if name != task_id),
    )


def _refuse_sibling_status(config: Config, task_id: str) -> None:
    """Any other governed file carrying a marker for this id is the disagreement."""
    for role in ROLES:
        if role == "roadmap" or not config.has(role) or not config.path(role).is_file():
            continue
        found = config.document(role).by_id().get(task_id)
        if found is not None:
            raise StatusElsewhere(
                task_id,
                role,
                config.relative(config.path(role)),
                found.lineno,
                found.task.status,
            )


def refuse_reuse(config: Config, task_id: str) -> None:
    """Refuse an id anything already mentions, anywhere (RK4).

    Public because every door that mints an id needs the same refusal, and an id rule
    with a second implementation is an id rule two commands can disagree about: `add`
    (RK5) and `record` (RK41) both call this one.
    """
    clash = next((ref for ref in scan(config) if ref.id == task_id), None)
    if clash is not None:
        raise IdInUse(task_id, config.relative(clash.path), clash.lineno)


def _placement(
    document: Document, heading: Heading, rendered: str
) -> tuple[int, list[str]]:
    """Where the line goes, and the lines to insert there — blank ones included.

    After the block's last task when it has one, which needs no blank-line reasoning at
    all. An empty block does: the heading may be followed by a blank line, by the next
    heading, or by nothing, and a task glued to either side of a heading reads as
    belonging to the wrong one.
    """
    entries = document.block(heading.label)
    if entries:
        return entries[-1].index + 1, [rendered]

    lines = document.lines
    index = heading.lineno  # 0-based: the line after the heading
    before: list[str] = []
    if index < len(lines) and blank(lines[index]):
        index += 1
    else:
        before = [""]
    at_end = index >= len(lines)
    after = [] if at_end or blank(lines[index]) else [""]
    return index, [*before, rendered, *after]
