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
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from roadkeep.config import Config
from roadkeep.document import Document, Entry, Heading, read_deps
from roadkeep.ids import next_id, scan
from roadkeep.schema import Task


class UnknownBlock(ValueError):
    """A block is declared by a heading and by nothing else (RK37)."""

    def __init__(self, label: str, declared: Sequence[str]) -> None:
        self.label = label
        self.declared = tuple(declared)
        known = ", ".join(self.declared) or "none"
        super().__init__(
            f"no heading declares Block {label} (this file declares: {known}): a "
            f"heading invented by a write files the task where nothing looks for it"
        )


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
            task.block, sorted({h.label for h in document.headings if h.label})
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
) -> Insertion:
    """Insert one task into the roadmap and save it. The whole write path.

    The id is derived unless one is given, and a given id that occurs anywhere is
    refused (:class:`IdInUse`) — including in prose, because a number a document
    already mentions is a number two designs would share in the history.
    """
    if task_id is None:
        task_id = next_id(config)
    else:
        _refuse_reuse(config, task_id)
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
    insertion = place(config.document("roadmap"), task)
    insertion.document.save()
    return insertion


def _refuse_reuse(config: Config, task_id: str) -> None:
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
    if index < len(lines) and _blank(lines[index]):
        index += 1
    else:
        before = [""]
    at_end = index >= len(lines)
    after = [] if at_end or _blank(lines[index]) else [""]
    return index, [*before, rendered, *after]


def _blank(line: str) -> bool:
    return not line.strip()
