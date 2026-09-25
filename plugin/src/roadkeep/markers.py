"""The dep annotation as derived data, never as typed data (RK8).

`(deps: RK1 ✅)` is a **cache of another line's status**, and it is the one field in the
format that can be wrong without anybody editing it: the moment RK1 ships, every line
that named it says something false, and the failure is silent in the worst direction — a
ready task reads as blocked, so `pick` (RK11) skips it and the backlog quietly stalls.

So the annotation is derived on every write, from the resolver that already answers the
question (RK28). Three rules, and the second is what keeps derivation from becoming churn:

* **Shipped is always annotated ✅** — a task in the ledger, a block the ledger has
  finished, a range with no open member: one answer, because all three mean "waiting on
  this is over". Nothing open was two states and only one of them is this one (RK432).
  This is the annotation a reader acts on and the only one that goes stale by itself.
* **An annotation that exists is kept true; one that was never written is not invented.**
  Shio annotates `⏳` and `📋` deps and those follow their target's marker, while this
  project writes a bare `(deps: RK14)` for open work and keeps it bare. Deriving a marker
  onto every open dep would rewrite half a backlog to say what `deps <id>` answers better.
* **Unresolvable or unknown → left exactly as written.** Derivation never invents a status
  it cannot read, and never deletes one it did not write; an unknown id is a lint error
  (RK14), not a rendering choice. The rule is about a dep naming **one** line, whose marker
  could be the author's reading of it. A `Block X` or a range names many, so its marker was
  derived by construction and is dropped wherever the collection is not settled (RK432) —
  including a label no heading declares, where a ✅ is the false claim the resolver refuses
  and this rule used to keep in the file.

:func:`refresh` applies this to a whole document, and it is deliberately *whole-file*: any
write is an opportunity to make every annotation true, and a tool that refreshed only the
line it touched would leave the file in a state where some annotations are derived and
some are remembered. What it will not do is write a line that the schema would then
refuse — a derived ✅ makes a line two characters longer, so a line already at the cap is
reported (:class:`~roadkeep.kernel.schema.SchemaError`) and the whole write is refused. That
report names the line's id and `file:line` (RK348): it is a dependent's sentence and never
the one the caller passed, so a bare count sends the author to shorten the wrong prose.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from roadkeep.backlog import Backlog, DepStatus
from roadkeep.kernel.document import Document, Entry
from roadkeep.kernel.schema import Dep, SchemaError, Task


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
    # Every line this write would overflow, and not the first one found (RK1152). A `ship` that
    # ticks three dependents used to refuse three times: each refusal named one line, the author
    # amended it, and the next was discovered only by re-running the command. The scan is
    # unaffected by collecting rather than raising — `derive` reads the backlog and not the
    # document being rebuilt — so the second overflow is as true as the first.
    refused: list[tuple[Entry, SchemaError]] = []
    for entry in backlog.roadmap.entries:
        derived = derive(backlog, entry.task)
        if document.schema.render(derived) == entry.raw:
            continue
        # Only what this write would change is validated: a violation elsewhere in the
        # file is `lint`'s to report, not this command's to refuse.
        try:
            document.schema.check(derived)
        except SchemaError as error:
            refused.append((entry, error))
            continue
        current = next(e for e in document.entries if e.lineno == entry.lineno)
        document = document.replace_task(current, derived)
        changed.append(entry.task.id)
    if refused:
        raise _naming_the_lines(backlog, refused) from None
    return Refresh(document=document, changed=tuple(changed))


def _naming_the_lines(
    backlog: Backlog, refused: list[tuple[Entry, SchemaError]]
) -> SchemaError:
    """The refusal, addressed to the line it is about and not to the caller's text (RK348, RK1152).

    A length reported as a bare number reads as *your sentence is too long*, and here it never is:
    the sentence that went over belongs to a **dependent**, and it went over because this write
    re-derived its `(deps: …)` annotation and a ✅ costs two characters. RK348 put the id and the
    `file:line` in the message and put them at the **end**, after the remedy — so the sentence
    still opened `delete 1 character` about the string the caller had just typed, and the clause
    that redirects it arrived once the reader had already acted. Measured on Shio: `ship DD34`
    refused three times, three amends, each next line found by re-running the command.

    So the address **leads**, and the command that closes it is named the way every `lint` finding
    names one (RK14/15): the edit is `amend <the dependent> --why …`, never a shorter `--why` here.
    What the limit is survives after it, because a refusal that only says what to type teaches
    nobody why the field exists. The repair itself stays the author's — trimming a dependent's
    `why` to make room for a marker nobody typed is a real edit, and only discovering *which*
    line by elimination was the defect.

    Every refused line in one error, so one edit round closes what took three.
    """
    from roadkeep.provenance import invocation  # noqa: PLC0415 - RK260, the refusal path only

    where = backlog.roadmap.path
    violations = []
    for entry, error in refused:
        address = (
            f"{backlog.config.relative(where)}:{entry.lineno}"
            if where is not None
            else f"line {entry.lineno}"
        )
        lead = f"on {entry.task.id}'s line ({address}), not on the text passed here — "
        said = (
            f" — `{invocation()} amend {entry.task.id} --why …` is the edit: this write "
            f"re-derives that line's dep annotation, and a marker is two characters wider"
        )
        violations += [
            replace(one, message=f"{lead}{one.message}{said}") for one in error.violations
        ]
    return SchemaError(tuple(violations))


def _annotate(backlog: Backlog, dep: Dep) -> Dep:
    resolution = backlog.resolve_dep(dep)
    if resolution.status is DepStatus.SHIPPED:
        return replace(dep, marker=backlog.config.schema.shipped_marker)
    if resolution.status is DepStatus.DEFERRED:
        # Written whether or not one was typed, which is ✅'s rule and not the open set's
        # (RK92): a paused blocker is the one state the dependent's own line cannot show,
        # and an unannotated dep on it reads as ordinary open work somebody is doing.
        #
        # On a **block** it claims what `Stage.PAUSED` claims and not what a ⏸ on a line
        # does (RK432): not that every member was set aside, but that the label is at the
        # stage with nothing open and something waiting on a `resume`. That is the reading
        # the resolution's own sentence spells on the row above it, so the marker
        # summarises rather than overstates — which is the test the rule below applies.
        return replace(dep, marker=backlog.config.schema.deferred_marker)
    if resolution.kind.collective:
        # A block or a range is many lines with many markers, so a marker on one is dropped
        # rather than replaced: any single one would claim too much. Reached now for every
        # state the collection is not settled in, and not only for `open` (RK432) — a
        # heading declared before its first line used to derive ✅ here, and leaving it to
        # the preserve rule below would freeze in the file the exact false statement this
        # resolver stopped making. Nothing of the author's is lost: a collective annotation
        # is derived by construction, there being no single line it could have been typed
        # about, which is why the rule below is about a dep naming one.
        return dep if dep.marker is None else replace(dep, marker=None)
    if resolution.status is DepStatus.OPEN:
        if dep.marker is None and not backlog.partial(dep.id):
            return dep  # unannotated open work stays unannotated
        # Written whether or not one was typed where the blocker shipped in halves (RK396),
        # for the reason RK92 writes the paused one: the ledger already records that part of
        # this dep landed, and an unannotated dep reads as work nobody has started on — which
        # is the reading that sends somebody to pick up the half that is still open.
        entry = backlog.entry(dep.id)
        return replace(dep, marker=entry.task.status if entry is not None else None)
    # UNKNOWN and UNRESOLVABLE: nothing to read, so nothing is written — including the
    # marker an author typed, which is preserved rather than judged.
    return dep
