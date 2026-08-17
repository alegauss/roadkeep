"""The id two branches spent on different work, moved without a departure (RK97).

Measured here: a branch filed five ids while main shipped a different task under the
first of them, and the merge left both. `lint` named it at once — `id.two-files`, because
open and recorded-as-gone are not both true — and then no command could act on it. `ship`
and `retire` are the only doors that take a line out of the roadmap, and each writes a
*terminal* ledger entry, which is the wrong record for work nobody cancelled; `amend`
reaches the `why`, the deps and the ref, and deliberately not the id. So the only repair
was a hand-edit of the line, its pointer and its section heading, in the files the guard
(RK22) exists to keep hands out of.

This is the door that leaves the work open. An id is an address, and a collision is two
lines claiming one — so the move is an address change and nothing else:

* **The whole address, or none of it.** The line, the `§id` heading its pointer resolves
  to, **every `§id.n` nested under that heading**, and every `(deps: …)` naming it change in
  one transaction, validated before any file is touched. A renumber that wrote the line and
  not the section would leave the pointer dangling, which is the state RK93 exists to
  prevent one verb over; one that wrote the heading and not the subtree beneath it leaves a
  `§RK1.1` claiming a task the backlog no longer has, under a heading naming RK9 — half a
  subtree renamed, written, and called clean by the gate (RK113).
* **The destination is derived unless it is given.** `next_id` in the line's own family
  (RK74) is the answer the repair usually wants, and a given one is refused if *anything*
  mentions it — the same :func:`~roadkeep.authoring.refuse_reuse` `add` calls, because a
  free id is one question with one answer (RK4).
* **The ledger is never opened.** The id the other branch spent stays spent: it is a
  decision already recorded, and renumbering history is how a `git log -S` starts
  returning two unrelated designs.

What it cannot know, and therefore reports: **which line a dep meant**. After the merge
both RK90s existed, so a `(deps: RK90)` elsewhere in the backlog was written about one of
them and nothing in the files says which. Every dep on the old id is moved with the line —
that is what a dependent of *this* task needs — and every line that happened to is named
in the answer, because the one the author has to reconsider is a line they can only
reconsider if they are told it changed. Refusing instead would leave the repair a
hand-edit, which is the defect.

Nothing here crosses the id-scheme non-goal. Non-contiguity is a property of real backlogs
and stays one: the old number is not reclaimed, not filled and not reused — it is left to
the line that already had it.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from pathlib import Path

from roadkeep import claiming
from roadkeep.authoring import refuse_reuse
from roadkeep.claiming import Held
from roadkeep.backlog import Backlog, NotOpen, Whereabouts
from roadkeep.config import Config
from roadkeep.kernel.document import Document, Entry, save_all
from roadkeep.kernel.schema import Task
from roadkeep.ids import id_scanner, next_id
from roadkeep.markers import refresh
from roadkeep.sections import Section, checked, descending, find, heading_of

__all__ = ["NotAnId", "Renumbering", "SameId", "family_of", "renumber"]

#: The files whose unit is a line, in the order a lookup asks them. The deferred store is
#: one (RK96): a paused line carries an id like any other, and a collision does not wait.
LINE_ROLES = ("roadmap", "deferred")


class NotAnId(ValueError):
    """A destination the format cannot read as an id.

    Refused before anything is written, because an unreadable id is worse than the
    collision it was meant to repair: nothing resolves a dep against it, `next_id` cannot
    see it, and the line is invisible to every scan (RK4).
    """

    def __init__(self, wanted: str, pattern: str) -> None:
        self.wanted = wanted
        super().__init__(
            f"{wanted!r} is not an id this project can read ({pattern}): the move needs "
            f"an address, and omitting one derives the next in the line's own family"
        )


class SameId(ValueError):
    """A move to the number the line already carries."""

    def __init__(self, task_id: str) -> None:
        self.task_id = task_id
        super().__init__(
            f"{task_id} already is that id: a renumber that changes nothing would still "
            f"rewrite the file, and an untouched file with a moved mtime reads as an edit"
        )


@dataclass(frozen=True, slots=True)
class Renumbering:
    """Every edit one line's change of address makes, as data, before it is written."""

    task_id: str
    to: str
    #: Which line file held it — the roadmap, or the deferred store (RK96).
    role: str
    #: The line as it now reads, under its new id.
    entry: Entry
    #: The governed files this write leaves changed, by role. A mapping and not three
    #: named fields, because *which* files are in it is a property of the project — a
    #: deferred store is optional and a prose file may hold no section for this line.
    documents: Mapping[str, Document] = field(default_factory=dict)
    #: The heading that moved with the line, or None when the pointer had no section.
    section: Section | None = None
    #: The nested anchors re-addressed with it, as they now read (`RK9.1`). A subsection is
    #: the task's own numbering, so it carries the task's address (RK113).
    subsections: tuple[str, ...] = ()
    #: Every line whose `(deps: …)` now names the new id. Named and never silent: which
    #: of two collided ids a dep meant is the one thing this transaction cannot read.
    moved: tuple[str, ...] = ()
    #: Lines whose annotation this write made true again (RK8).
    refreshed: tuple[str, ...] = ()
    #: The live claim this move carries to the new id, where there is one (RK156). Reported,
    #: because a worker whose line changed number will next ask for it by an id that no longer
    #: exists, and that it is still theirs is the half of the answer the files do not hold.
    claim: Held | None = None
    #: The checkout, because one thing this move carries is *not* a governed file: the claim
    #: registry lives outside the repository (L2) and is keyed by the address that just moved.
    root: Path | None = None

    @property
    def rendered(self) -> str:
        return self.entry.raw

    @property
    def lineno(self) -> int:
        return self.entry.lineno

    def save(self) -> tuple[Path, ...]:
        """Write the files, and answer every path that took (RK1130).

        The claim goes last and never conditions the write: it is transient state whose worst
        failure is a claim lost, which is the behaviour before claims existed — and putting it
        before the files would move an address the files had not moved yet.
        """
        wrote = save_all(*self.documents.values())
        if self.root is not None and self.claim is not None:
            claiming.rename(self.root, self.task_id, self.to)
        return wrote

    def event(self, config: Config) -> dict[str, object]:
        """What the move did to the block it lands in (RK38).

        The roadmap is read back where this write did not touch it: a line moved in the
        deferred store owes the same event line, and the file is already saved.
        """
        from roadkeep.rendering import _event  # noqa: PLC0415 - RK260

        return _event(
            self.to,
            self.entry.task.block,
            self.documents.get("roadmap") or config.document("roadmap"),
            config,
        )

    def stated(self, config: Config, wrote: Sequence[Path]) -> str:
        """Where the line went and what followed it (RK74, RK113, RK156).

        Beside :meth:`payload` since RK1170. `wrote` is the caller's, because :meth:`save` is
        a step this record does not take.
        """
        from roadkeep.rendering import (  # noqa: PLC0415 - RK260
            _event_rows,
            _staging_rows,
        )

        where = config.relative(config.path(self.role))
        prose = (
            config.relative(config.path("improvements")) if config.has("improvements") else ""
        )
        rows = [
            f"{self.task_id} → {self.to}  {where}:{self.lineno}",
            f"  {self.rendered}",
        ]
        if self.section is not None:
            # The section's **own** anchor and not `to` (RK1231): where the ref is the id the
            # two are the same string, and under an outline they are not — the address stayed
            # and the binding moved, so printing the id would name a heading that is not there.
            rows.append(f"  section  §{self.section.anchor} → {prose}:{self.section.first}")
        if self.subsections:
            rows.append(
                f"  nested   {', '.join('§' + a for a in self.subsections)} "
                f"(the id's own numbering)"
            )
        if self.moved:
            rows.append(
                f"  deps     {', '.join(self.moved)} now name {self.to} — "
                f"confirm each meant this line"
            )
        if self.refreshed:
            rows.append(f"  derived  {', '.join(self.refreshed)} (dep annotations re-derived)")
        if self.claim is not None:
            # The half the files do not hold (RK156): the worker holding this will next ask for
            # it by a number that no longer exists, and that it is still theirs is what to say.
            rows.append(f"  claimed  the claim taken {self.claim.since} ago moved with it")
        rows += _staging_rows(config.relative(one) for one in wrote)
        rows += _event_rows(self.event(config), "  ", config=config)
        return "\n".join(rows)

    def payload(self, config: Config, wrote: Sequence[Path]) -> dict[str, object]:
        """The same answer as data, with every file the new address reached."""
        from roadkeep.rendering import _held_json, _wrote_json  # noqa: PLC0415 - RK260

        prose = (
            config.relative(config.path("improvements")) if config.has("improvements") else ""
        )
        return {
            "id": self.task_id,
            "to": self.to,
            "role": self.role,
            "file": config.relative(config.path(self.role)),
            "line": self.lineno,
            "rendered": self.rendered,
            "section": None if self.section is None else self.section.payload(prose),
            # The nested headings that carried the old address, as they now read.
            "subsections": list(self.subsections),
            # The lines this write changed on the author's behalf, because which of two
            # collided ids a dep meant is not a fact any file holds.
            "moved": list(self.moved),
            "refreshed": list(self.refreshed),
            "files": sorted(config.relative(config.path(role)) for role in self.documents),
            "claimed": _held_json(self.claim),
            **_wrote_json(config, wrote),
            "event": self.event(config),
        }


def renumber(config: Config, task_id: str, to: str | None = None) -> Renumbering:
    """Move one open line to a free id, with its section and its dependents.

    `to` is derived when it is not given: one past the highest id in this line's own
    family (RK74), which is the address a collision repair almost always wants. Given, it
    is held to the same rule every minted id is — refused if any configured source
    mentions it, including prose, because a number a document already names is a number
    two designs would share in the history.

    Refuses before writing anything: an id in neither line file, a destination the format
    cannot read, a destination already spent, and any line the move would render over the
    limit — a longer number is two more characters, and the cap is the cap.
    """
    schema = config.schema
    documents = _line_documents(config)
    role, entry = _locate(config, documents, task_id)
    if to is None:
        to = next_id(config, family_of(config, task_id))
    if to == task_id:
        raise SameId(task_id)
    if not schema.id_pattern().match(to):
        raise NotAnId(to, schema.id_pattern().pattern)
    # `--to` and not `--id`, which is this verb's own spelling (RK1212): the rule is shared
    # and the argument carrying the number is not.
    refuse_reuse(config, to, flag="--to")

    changed: dict[str, Document] = {}
    # The pointer is the id under `ref_scheme = "id"` (RK27), so it moves with it; under
    # an outline it names a heading this line does not own, and is left exactly as typed.
    pointer = to if schema.ref_scheme == "id" and entry.task.ref else entry.task.ref
    documents[role] = documents[role].replace_task(
        entry,
        checked(
            config,
            replace(entry.task, id=to, ref=pointer),
            schema=documents[role].schema,
        ),
    )
    changed[role] = documents[role]

    moved = _move_deps(documents, task_id, to)
    changed.update({name: documents[name] for name in moved})

    section = None
    subsections: tuple[str, ...] = ()
    prose = _section_document(config, task_id, to) if entry.task.ref == task_id else None
    if prose is not None:
        changed["improvements"], section, subsections = prose
    elif entry.task.ref:
        # The **binding**, where the anchor is not the id (RK1231). Under an outline the ref is
        # an address like `XXVI.14`, so the branch above is skipped and the heading keeps the
        # number the task no longer has — `### XXVI.14 … (SH9001)` after `renumber SH9001
        # SH789`, a heading naming a task that does not exist. The comment above is right that
        # an outline heading is not this line's to move; the trailing `(<id>)` is a different
        # question, and one this tool answered when it *wrote* the id there (RK262).
        #
        # Reported through the same `section` field, because it is the same fact — this write
        # touched the design — and `section: null` was what an author had to read as a signal.
        rebound = _rebound(config, entry.task.ref, entry.task, to)
        if rebound is not None:
            changed["improvements"], section = rebound

    derived = ()
    if "roadmap" in documents:
        # Derived against the state this write creates, for the reason every other door
        # does it (RK8): a dep that now names a different id is a dep whose cached marker
        # was answered by the line that used to carry it.
        refreshed = refresh(replace(Backlog.load(config), roadmap=documents["roadmap"]))
        documents["roadmap"] = refreshed.document
        derived = refreshed.changed
        if derived:
            changed["roadmap"] = refreshed.document

    dependents = tuple(name for names in moved.values() for name in names)
    # Read against the line as it was *before* the move, which is the only state the registry's
    # key still matches (RK156).
    held = claiming.live(config, [entry])
    return Renumbering(
        task_id=task_id,
        to=to,
        role=role,
        entry=next(e for e in documents[role].entries if e.task.id == to),
        documents=changed,
        section=section,
        subsections=subsections,
        moved=dependents,
        refreshed=tuple(n for n in derived if n != to and n not in dependents),
        claim=held[0] if held else None,
        root=config.root,
    )


def _move_deps(
    documents: dict[str, Document], task_id: str, to: str
) -> dict[str, tuple[str, ...]]:
    """Rewrite every `(deps: <old>)` to the new id, in place, by file. Refuses first.

    Which lines those are is read once, before any of them is rewritten: `replace_task`
    re-parses, so an entry held across an edit is one whose line number may already have
    moved — the same care every mutator in :mod:`roadkeep.kernel.document` takes.
    """
    out: dict[str, tuple[str, ...]] = {}
    for name, document in documents.items():
        dependents = tuple(
            e.task.id for e in document.entries if task_id in e.task.dep_ids
        )
        for dependent in dependents:
            current = next(e for e in documents[name].entries if e.task.id == dependent)
            rewritten = replace(
                current.task,
                deps=tuple(
                    replace(dep, id=to) if dep.id == task_id else dep
                    for dep in current.task.deps
                ),
            )
            documents[name] = documents[name].replace_task(
                current, documents[name].schema.check(rewritten)
            )
        if dependents:
            out[name] = dependents
    return out


def _line_documents(config: Config) -> dict[str, Document]:
    """Every governed file whose unit is a line, loaded once and mutated in memory."""
    return {
        role: config.document(role)
        for role in LINE_ROLES
        if config.has(role) and config.path(role).is_file()
    }


def _locate(
    config: Config, documents: Mapping[str, Document], task_id: str
) -> tuple[str, Entry]:
    """Which line file holds this id, and the line — the roadmap, or the store (RK96).

    A paused line is still a line, so it is renumbered by the same door; the ledger is not
    asked, because an id it records is a decision and not an address to move.
    """
    for role, document in documents.items():
        entry = document.by_id().get(task_id)
        if entry is not None:
            return role, entry
    raise NotOpen(
        task_id,
        ", ".join(config.relative(config.path(role)) for role in documents),
        Whereabouts.of(config, task_id),
    )


def _rebound(
    config: Config, anchor: str, task: Task, to: str
) -> tuple[Document, Section] | None:
    """This section's heading with the id it names moved, the address untouched (RK1231).

    The half `_section_document` cannot do, and the two are deliberately not one function: that
    one rewrites an **address**, which is only this line's to move where the anchor *is* the id;
    this rewrites a **binding**, which is the tool's own writing wherever it appears. Under an
    outline both facts are true of one heading and only the second travels with the id.

    The binding is composed by :func:`~roadkeep.sections._bound` and never spelled here — a
    second place that knew the `(<id>)` shape is exactly what drifts from the writer. Applied
    to the document directly, the way its sibling applies an address, and **not** through
    `amend`: that verb re-binds from the roadmap *on disk*, which at this moment still carries
    the old id, so it would render `A design (SH789) (SH9001)`.

    `None` where there is nothing to do: no prose file, no section at that anchor, or a heading
    that never carried this id — an author's own title mentioning it is not a binding, which is
    :func:`~roadkeep.sections.owners`' reading and not a second one.
    """
    from roadkeep.sections import _bound, owners  # noqa: PLC0415 - RK260

    if not config.has("improvements") or not config.path("improvements").is_file():
        return None
    document = config.document("improvements")
    section = find(document, anchor)
    if section is None or task.id not in owners(section, document.schema.id_pattern()):
        return None
    bare = section.title.replace(f"({task.id})", "").strip()
    rebound = replace(
        section,
        title=_bound(document.schema, anchor, bare, replace(task, id=to)),
    )
    return document.replace_line(
        section.first - 1, heading_of(document.schema, rebound)
    ), rebound


def _section_document(
    config: Config, anchor: str, to: str
) -> tuple[Document, Section, tuple[str, ...]] | None:
    """The prose file with this section's whole address re-written, or None if it has none.

    Every heading and no prose. The paragraphs under them are the author's (L4) — but a
    `§<id>.1` is not prose, it is the same address one segment longer, and leaving it behind
    is what RK113 measured: `renumber RK1 --to RK9` moved the line, moved the pointer, moved
    `§RK1` to `§RK9`, and left `§RK1.1` nested under it naming a task the backlog no longer
    has. `find` deliberately returns the subtree and this function rewrote one line of it;
    that asymmetry was the whole defect.

    Only the anchors this one owns, which is :func:`~roadkeep.sections.descending`'s reading
    and not a second one: a nested heading is renamed when it *extends* the id segment by
    segment, so a `§RK1.1` travels and a `§RK50` someone filed inside the subtree keeps the
    address of the task that owns it — the same question :func:`_move_deps` cannot answer
    about a dep, answered by the anchor itself rather than by depth. The destination cannot
    already carry one of these: `refuse_reuse` refused `to` if anything in any configured
    source so much as mentions it, and `§RK9.1` mentions RK9.
    """
    if not config.has("improvements") or not config.path("improvements").is_file():
        return None
    document = config.document("improvements")
    section = find(document, anchor)
    if section is None:
        return None
    moved = replace(section, anchor=to)
    # Read before any of them is written, and applied by line number: `replace_line` is one
    # line for one line, so no heading below the first edit moves under the edits above it.
    edits = [(section.first - 1, heading_of(document.schema, moved))]
    renamed: list[str] = []
    for child in descending(document, anchor):
        under = replace(child, anchor=f"{to}{child.anchor[len(anchor) :]}")
        edits.append((child.first - 1, heading_of(document.schema, under)))
        renamed.append(under.anchor)
    for index, raw in edits:
        document = document.replace_line(index, raw)
    return document, moved, tuple(renamed)


def family_of(config: Config, task_id: str) -> str:
    """Which track this id belongs to, read off the id itself (RK74).

    Off the id and never off the block: a track is not a block, and the destination of a
    move has to stay in the family the line was numbered in or the repair is a second
    collision waiting for the next `next_id`.

    Public because the ledger's own re-addressing (RK127) asks the same question about the
    same string, and two answers to "which family is this id in" is how one door mints a
    destination the other would have refused.
    """
    match = id_scanner(config.schema).match(task_id)
    return match.group(1) if match else config.schema.prefix


