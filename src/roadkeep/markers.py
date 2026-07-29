"""The dep annotation as derived data, never as typed data (RK8).

`(deps: RK1 ✅)` is a **cache of another line's status**, and it is the one field in the
format that can be wrong without anybody editing it: the moment RK1 ships, every line
that named it says something false, and the failure is silent in the worst direction — a
ready task reads as blocked, so `pick` (RK11) skips it and the backlog quietly stalls.

So the annotation is derived on every write, from the resolver that already answers the
question (RK28). Three rules, and the second is what keeps derivation from becoming churn:

* **Shipped is always annotated ✅** — a task in the ledger, a block with nothing open, a
  range with no open member: one answer, because all three mean "waiting on this is over".
  This is the annotation a reader acts on and the only one that goes stale by itself.
* **An annotation that exists is kept true; one that was never written is not invented.**
  Shio annotates `⏳` and `📋` deps and those follow their target's marker, while this
  project writes a bare `(deps: RK14)` for open work and keeps it bare. Deriving a marker
  onto every open dep would rewrite half a backlog to say what `deps <id>` answers better.
* **Unresolvable or unknown → left exactly as written.** Derivation never invents a status
  it cannot read, and never deletes one it did not write; an unknown id is a lint error
  (RK14), not a rendering choice.

:func:`refresh` applies this to a whole document, and it is deliberately *whole-file*: any
write is an opportunity to make every annotation true, and a tool that refreshed only the
line it touched would leave the file in a state where some annotations are derived and
some are remembered. What it will not do is write a line that the schema would then
refuse — a derived ✅ makes a line two characters longer, so a line already at the cap is
reported (:class:`~roadkeep.schema.SchemaError`) and the whole write is refused.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from roadkeep.backlog import Backlog, DepStatus
from roadkeep.document import Document
from roadkeep.schema import Dep, DepKind, Task


@dataclass(frozen=True, slots=True)
class Refresh:
    """The document with every annotation derived, and whose lines that changed."""

    document: Document
    changed: tuple[str, ...] = ()


def derive(backlog: Backlog, task: Task) -> Task:
    """The same task with every dep annotation re-derived from the backlog."""
    return replace(task, deps=tuple(_annotate(backlog, dep) for dep in task.deps))


def refresh(backlog: Backlog) -> Refresh:
    """Re-derive every annotation in the roadmap. Refuses rather than write a bad line.

    Returns the document unsaved: the caller is usually mid-transaction (`ship` has a
    ledger entry to write in the same breath), and a refresh that saved on its own would
    make the third of three edits the first one on disk.
    """
    document = backlog.roadmap
    changed: list[str] = []
    for entry in backlog.roadmap.entries:
        derived = derive(backlog, entry.task)
        if document.schema.render(derived) == entry.raw:
            continue
        # Only what this write would change is validated: a violation elsewhere in the
        # file is `lint`'s to report, not this command's to refuse.
        document.schema.check(derived)
        current = next(e for e in document.entries if e.lineno == entry.lineno)
        document = document.replace_task(current, derived)
        changed.append(entry.task.id)
    return Refresh(document=document, changed=tuple(changed))


def _annotate(backlog: Backlog, dep: Dep) -> Dep:
    resolution = backlog.resolve_dep(dep)
    if resolution.status is DepStatus.SHIPPED:
        return replace(dep, marker=backlog.config.schema.shipped_marker)
    if resolution.status is DepStatus.OPEN:
        if dep.marker is None:
            return dep  # unannotated open work stays unannotated
        if resolution.kind is not DepKind.TASK:
            # A block or a range is many lines with many markers, so a stale ✅ on one
            # is dropped rather than replaced: any single marker would claim too much.
            return replace(dep, marker=None)
        entry = backlog.entry(dep.id)
        return replace(dep, marker=entry.task.status if entry is not None else None)
    # UNKNOWN and UNRESOLVABLE: nothing to read, so nothing is written — including the
    # marker an author typed, which is preserved rather than judged.
    return dep
