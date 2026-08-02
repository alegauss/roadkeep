"""Normalizing what is mechanical, so the report left is one somebody acts on (RK16).

A first run against a real backlog reports dozens of violations, and a report that size
gets ignored wholesale — which makes the gate (RK14) worth exactly nothing on the file
that needed it most. So the findings split in two:

* **mechanical** — the dep annotation (derived data, RK8), a pointer the scheme derives
  (RK27), a duplicate or unordered dep, an invisible codepoint stuck to the marker, and
  whitespace around a field. Nothing here is anybody's prose, and every one of them is
  recomputed from the parsed line rather than edited in place;
* **editorial** — an over-long `why`, a symptom that is a sentence, a dep on a task in
  neither file. Each needs a decision, and a tool that made it would be writing prose (L4).

`--fix` applies the first list and leaves the second, which is the whole point: what
remains is short enough to read.

**How this coexists with L3.** Every mutator in :mod:`roadkeep.document` refuses the
*whole file* when any line it parsed would render back differently, because a silent
rewrite of a line the parser misread is unreviewable corruption. That guard is exactly
what a normalizer has to get past — an invisible selector on the marker and a hand-chosen
anchor are both *non-canonical*, and they are the two things most worth fixing. So this
module does not relax the invariant, it discharges it per line:

1. a line is only ever replaced by ``schema.render`` of the task parsed **from that line**;
2. a line nobody chose to fix is carried through byte-for-byte, endings included;
3. the result is re-parsed before anything reaches the disk, and every line this pass
   changed must come back canonical — otherwise **nothing is written at all**.

A line the grammar rejected is never touched: there is no parse to re-render, so a
"fix" would be a guess, and a guess is what rule 1 exists to forbid.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from roadkeep.backlog import Backlog, id_order
from roadkeep.config import Config
from roadkeep.document import Document, ending
from roadkeep.linting import LINE_ROLES
from roadkeep.markers import derive
from roadkeep.schema import Dep, DepKind, Schema, Task

#: The codepoints that make a marker compare unequal to the one it renders as. Stripped
#: here and refused in `roadkeep.toml` (RK3), which is the same rule at both ends.
INVISIBLE = "\ufe0f\u200d\u200b"  # variation selector, ZWJ, zero-width space


@dataclass(frozen=True, slots=True)
class Repair:
    """One line, rewritten, and the mechanical reasons it was."""

    file: str
    lineno: int
    id: str
    before: str
    after: str
    reasons: tuple[str, ...]

    def __str__(self) -> str:
        return f"{self.file}:{self.lineno}  fixed  {self.id}: {', '.join(self.reasons)}"


@dataclass(frozen=True, slots=True)
class Skipped:
    """A mechanical fix that was *not* applied, because applying it breaks the line."""

    file: str
    lineno: int
    id: str
    reason: str

    def __str__(self) -> str:
        return f"{self.file}:{self.lineno}  kept   {self.id}: {self.reason}"


@dataclass(frozen=True, slots=True)
class Fix:
    """What a normalizing pass did, and every file it wrote."""

    repairs: tuple[Repair, ...] = ()
    skipped: tuple[Skipped, ...] = ()
    files: tuple[str, ...] = ()
    #: Why a file was left alone entirely. Non-empty means nothing was written to it.
    refused: tuple[str, ...] = ()

    @property
    def changed(self) -> int:
        return len(self.repairs)


def fix(config: Config) -> Fix:
    """Normalize every governed line that can be normalized. Writes each file once."""
    repairs: list[Repair] = []
    skipped: list[Skipped] = []
    written: list[str] = []
    refused: list[str] = []

    # One backlog for the whole pass: the annotation is derived from the *current* files,
    # and re-reading them per line would let a fix to the roadmap change what the next
    # line derives — a pass whose result depended on its own order.
    backlog = Backlog.load(config)
    for role in LINE_ROLES:
        if not config.has(role) or not config.path(role).is_file():
            continue
        outcome = _fix_file(config, role, backlog)
        repairs.extend(outcome.repairs)
        skipped.extend(outcome.skipped)
        written.extend(outcome.files)
        refused.extend(outcome.refused)
    return Fix(
        repairs=tuple(repairs),
        skipped=tuple(skipped),
        files=tuple(written),
        refused=tuple(refused),
    )


def _fix_file(config: Config, role: str, backlog: Backlog) -> Fix:
    document = config.document(role)
    file = config.relative(config.path(role))
    lines = list(document.lines)
    repairs: list[Repair] = []
    skipped: list[Skipped] = []

    for entry in document.entries:
        fixed, reasons = _normalize(document.schema, entry.task, backlog, role)
        if not reasons:
            continue
        rendered = document.schema.render(fixed)
        if rendered == entry.raw:
            continue  # the change was invisible in the rendering: not a repair
        introduced = _introduced(document.schema, entry.task, fixed)
        if introduced:
            # The one case `markers.refresh` already meets: a derived ✅ makes the line two
            # characters longer, and a line at the cap would go over. Reported, not forced.
            skipped.append(
                Skipped(file, entry.lineno, entry.task.id, f"fixing it would add {introduced}")
            )
            continue
        lines[entry.index] = rendered + ending(lines[entry.index])
        repairs.append(
            Repair(file, entry.lineno, entry.task.id, entry.raw, rendered, tuple(reasons))
        )

    if not repairs:
        return Fix(skipped=tuple(skipped))

    text = "".join(lines)
    problem = _verify(text, document, {r.lineno for r in repairs})
    if problem is not None:
        # Rule 3: the pass proves its own output before the disk sees any of it.
        return Fix(skipped=tuple(skipped), refused=(f"{file}: {problem}",))
    Path(config.path(role)).write_text(text, encoding="utf-8", newline="")
    return Fix(repairs=tuple(repairs), skipped=tuple(skipped), files=(file,))


def _normalize(
    schema: Schema, task: Task, backlog: Backlog, role: str
) -> tuple[Task, list[str]]:
    """The task as the format would write it, and the name of every change made."""
    reasons: list[str] = []
    fixed = task

    marker = fixed.status.strip(INVISIBLE)
    if marker != fixed.status:
        fixed = replace(fixed, status=marker)
        reasons.append("invisible codepoint dropped from the marker")

    for field in ("symptom", "why"):
        value = getattr(fixed, field)
        if value != value.strip():
            fixed = replace(fixed, **{field: value.strip()})
            reasons.append(f"{field} trimmed")

    if schema.deps_field and fixed.deps:
        deps, dep_reasons = _deps(schema, fixed, backlog, role)
        if dep_reasons:
            fixed = replace(fixed, deps=deps)
            reasons.extend(dep_reasons)

    if schema.ref_scheme == "id" and fixed.ref and fixed.ref != fixed.id:
        # The pointer is derived in this scheme, so it is not the author's text — which is
        # also what made RK27's own migration a throwaway script instead of a command.
        fixed = replace(fixed, ref=fixed.id)
        reasons.append("pointer derived from the id")
    return fixed, reasons


def _deps(
    schema: Schema, task: Task, backlog: Backlog, role: str
) -> tuple[tuple[Dep, ...], list[str]]:
    reasons: list[str] = []
    deps = task.deps

    seen: dict[str, Dep] = {}
    for dep in deps:
        seen.setdefault(dep.id, dep)
    if len(seen) != len(deps):
        reasons.append("duplicate dep dropped")
        deps = tuple(seen.values())

    if role == "roadmap":
        derived = derive(backlog, replace(task, deps=deps)).deps
        if derived != deps:
            reasons.append("dep annotation derived")
            deps = derived

    # Ordered only when every token is an id of this project. `Block P` and `real design
    # partners` have no order, and sorting a mixed field would move prose somebody wrote.
    if all(schema.classify_dep(d) is DepKind.TASK for d in deps):
        ordered = tuple(sorted(deps, key=lambda d: id_order(d.id, schema)))
        if ordered != deps:
            reasons.append("deps ordered")
            deps = ordered
    return deps, reasons


def _introduced(schema: Schema, before: Task, after: Task) -> str:
    """Violations the fix would create that the line did not already have."""
    had = {v.code for v in schema.validate(before)}
    new = [v for v in schema.validate(after) if v.code not in had]
    return "; ".join(str(v) for v in new)


def _verify(text: str, before: Document, changed: set[int]) -> str | None:
    """Rule 3: re-parse, and refuse unless every line this pass wrote came back canonical.

    Also refuses a pass that changed how many lines the file has or which ids they carry:
    a normalizer that dropped a task is the failure no per-line check would notice.
    """
    after = Document.parse(text, schema=before.schema, path=before.path)
    if len(after.lines) != len(before.lines):
        return f"the pass changed the line count ({len(before.lines)} → {len(after.lines)})"
    if [e.task.id for e in after.entries] != [e.task.id for e in before.entries]:
        return "the pass changed which ids the file carries"
    if len(after.rejects) != len(before.rejects):
        return "the pass made a line the grammar no longer reads"
    offenders = [e.lineno for e in after.non_canonical if e.lineno in changed]
    if offenders:
        return f"line(s) {offenders} would not round-trip after the fix"
    return None
