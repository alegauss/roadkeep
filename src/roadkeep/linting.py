"""The gate: every governed line, validated where nothing else was watching (RK14).

`add` refuses a field at the moment it is typed (L1), which is where the saving is — but
a file also drifts by the paths `add` does not own: a hand edit, a merge that resolved
into a half-line, a `roadkeep.toml` limit lowered after the lines were written. So this
is the backstop, and the one thing that makes it a gate rather than advice is the exit
code: **exit 1 when anything drifted**, so a pre-commit hook and an Action (RK17) can
both call the same command and neither has to parse a report.

It re-validates rather than re-implements. Every rule read here comes from
:meth:`Schema.validate`, every line from :class:`Document`, every dep resolution from
:mod:`roadkeep.backlog` — a linter with its own regexes over prose would be a second
statement of the format, and the two would disagree in the direction nobody tests.

What it reports, and why each one is a defect the other commands cannot see:

* **A schema violation** on a line that exists — the limit that was raised after the
  line was written, or the line that never went through `add`.
* **A line that does not round-trip** (L3). Reported and never repaired: normalizing a
  line the parser may have misread is the corruption the whole invariant exists to
  prevent, so what this prints is the canonical rendering and the fix stays a human's.
* **A marker-bearing bullet the grammar rejected** — the silent miss `audit` (RK10)
  prints at exit 0. `audit` reports; this fails.
* **One id in two places** — twice in one file, or in both the roadmap and the ledger.
  Two lines carrying one id is two answers to "is this done?", and nothing says which.
* **A dep nothing can satisfy** — an id in neither file (a typo, or a line deleted by
  hand), a dep on a task that was retired (RK32: the record says the work will not
  happen, so the dependent line is the author's next edit), or `Block X` where no
  heading declares X (RK37). An *external* dep is not a finding: real work waits on
  things this backlog does not track, and Turing writes them on purpose.
* **A stale `(deps: … ✅)` annotation** — derived on every write (RK8), so a divergence
  here means the file was edited by something that is not this tool.
* **A cycle** — three tasks waiting on each other are three tasks nothing can start
  (RK13), which is a defect and not a shape.

What is deliberately *not* here, because each is its own task and a gate that grew all
of them at once would be a gate nobody could adopt: resolving the `→ §RK<n>` pointer
and the spec paths (RK15), normalizing what is mechanical (RK16), the always-loaded
file budgets (RK30), naming an invisible codepoint (RK34), and what a commit touched
(RK36). This one answers a narrower question completely: *is every line in the
governed files a line this format accepts?*
"""

from __future__ import annotations

from dataclasses import dataclass

from roadkeep.backlog import Backlog, DepStatus, number_of
from roadkeep.config import ROLES, Config
from roadkeep.document import Document
from roadkeep.graph import Graph
from roadkeep.markers import derive
from roadkeep.schema import DepKind, Task

#: The governed files whose unit is a task line. The prose files are paragraphs, so
#: their gate is a pointer and a budget — RK15 and RK30, not this.
LINE_ROLES = ("roadmap", "changelog")


@dataclass(frozen=True, slots=True)
class Finding:
    """One defect, at one place. ``code`` is stable; ``message`` names the fix.

    The code is the same string :class:`~roadkeep.schema.Violation` uses where the
    finding came from the schema, so a caller filtering on `why.sentences` filters the
    same rule whether it was refused at `add` or found here.
    """

    code: str
    file: str
    message: str
    #: 1-based, as an editor counts. ``None`` when the finding is about the file itself.
    lineno: int | None = None
    id: str = ""

    @property
    def where(self) -> str:
        return self.file if self.lineno is None else f"{self.file}:{self.lineno}"

    def __str__(self) -> str:
        subject = f"{self.id}: " if self.id else ""
        return f"{self.where}  {self.code}  {subject}{self.message}"


@dataclass(frozen=True, slots=True)
class Report:
    """What was checked, and everything wrong with it. Emptiness is the pass."""

    findings: tuple[Finding, ...]
    #: The files read, as the project spells them — printed even when clean, because a
    #: gate that passed by reading nothing is the failure mode of every gate.
    checked: tuple[str, ...]
    lines: int

    @property
    def clean(self) -> bool:
        return not self.findings

    @property
    def problems(self) -> int:
        return len(self.findings)

    def codes(self) -> dict[str, int]:
        """Findings per code, most first — the summary a report of ninety is read by."""
        found: dict[str, int] = {}
        for finding in self.findings:
            found[finding.code] = found.get(finding.code, 0) + 1
        return dict(sorted(found.items(), key=lambda pair: (-pair[1], pair[0])))


def lint(config: Config) -> Report:
    """Read every governed file and return every defect. Writes nothing, ever."""
    findings: list[Finding] = []
    findings.extend(_absent(config))

    documents: dict[str, Document] = {}
    for role in LINE_ROLES:
        if config.has(role) and config.path(role).is_file():
            documents[role] = config.document(role)

    checked = tuple(config.relative(config.path(role)) for role in documents)
    for role, document in documents.items():
        findings.extend(_within(config, role, document))
    findings.extend(_across(config, documents))

    order = {name: index for index, name in enumerate(checked)}
    findings.sort(key=lambda f: (order.get(f.file, len(order)), f.lineno or 0, f.code))
    return Report(
        findings=tuple(findings),
        checked=checked,
        lines=sum(len(d.entries) for d in documents.values()),
    )


def _absent(config: Config) -> list[Finding]:
    """A declared file that is not on disk (`init` creates it: RK18)."""
    return [
        Finding(
            "file.missing",
            config.relative(config.path(role)),
            f"declared as the {role} file and not on disk",
        )
        for role in ROLES
        if config.has(role) and not config.path(role).is_file()
    ]


def _within(config: Config, role: str, document: Document) -> list[Finding]:
    """Everything decidable from one file alone."""
    file = config.relative(config.path(role))
    out: list[Finding] = []

    for reject in document.rejects:
        # The line the parser could not read at all. It is reported here and counted
        # nowhere else, which is the difference between `audit` and a gate.
        out.append(Finding("line.unparsed", file, reject.reason, reject.lineno))

    seen: dict[str, int] = {}
    for entry in document.entries:
        task = entry.task
        for violation in document.schema.validate(task):
            out.append(
                Finding(violation.code, file, violation.message, entry.lineno, task.id)
            )
        canonical = document.schema.render(task)
        if canonical != entry.raw:
            # Named, not fixed (L3): the tool may not rewrite a line it might have
            # misread, so the report carries the rendering and the edit stays a human's.
            out.append(
                Finding(
                    "line.non-canonical",
                    file,
                    f"written differently from what the schema renders: {canonical!r}",
                    entry.lineno,
                    task.id,
                )
            )
        first = seen.get(task.id)
        if first is not None:
            out.append(
                Finding(
                    "id.duplicate",
                    file,
                    f"already carried by line {first}: two lines with one id are two "
                    f"answers to whether it is done",
                    entry.lineno,
                    task.id,
                )
            )
        seen.setdefault(task.id, entry.lineno)
    return out


def _across(config: Config, documents: dict[str, Document]) -> list[Finding]:
    """What needs both files: one id in two of them, and every dep resolved."""
    roadmap = documents.get("roadmap")
    if roadmap is None:
        return []
    ledger = documents.get("changelog")
    backlog = Backlog(config=config, roadmap=roadmap, ledger=ledger)
    file = config.relative(config.path("roadmap"))
    out: list[Finding] = []

    if ledger is not None:
        shipped = ledger.by_id()
        for task_id, entry in roadmap.by_id().items():
            if task_id in shipped:
                out.append(
                    Finding(
                        "id.two-files",
                        file,
                        f"also on line {shipped[task_id].lineno} of "
                        f"{config.relative(config.path('changelog'))}: open and "
                        f"recorded as gone are not both true",
                        entry.lineno,
                        task_id,
                    )
                )

    for entry in roadmap.entries:
        out.extend(_deps(backlog, entry.task, file, entry.lineno))
        derived = derive(backlog, entry.task)
        if derived.deps != entry.task.deps:
            out.append(
                Finding(
                    "deps.stale",
                    file,
                    f"the annotation caches another line's status and this one is out "
                    f"of date: derived, it reads "
                    f"({', '.join(d.render() for d in derived.deps)})",
                    entry.lineno,
                    entry.task.id,
                )
            )

    out.extend(_cycles(backlog, file))
    return out


def _deps(backlog: Backlog, task: Task, file: str, lineno: int) -> list[Finding]:
    """Deps nothing will ever satisfy — three of the four kinds, for three reasons."""
    out: list[Finding] = []
    for resolution in backlog.resolve(task):
        kind, dep = resolution.kind, resolution.dep
        if resolution.status is DepStatus.UNKNOWN:
            out.append(
                Finding(
                    "deps.unknown",
                    file,
                    f"waits on {dep.id}, which is in neither the roadmap nor the "
                    f"changelog: nothing can say whether it is done",
                    lineno,
                    task.id,
                )
            )
        elif resolution.status is not DepStatus.UNRESOLVABLE:
            continue
        elif kind is DepKind.TASK:
            out.append(
                Finding(
                    "deps.retired",
                    file,
                    f"waits on {dep.id}, which left without shipping: "
                    f"{resolution.detail}",
                    lineno,
                    task.id,
                )
            )
        elif kind is DepKind.BLOCK:
            out.append(
                Finding(
                    "deps.block",
                    file,
                    f"waits on {dep.id} and {resolution.detail}",
                    lineno,
                    task.id,
                )
            )
        # An external dep falls through on purpose: waiting on work this backlog does
        # not track is a fact about the work, and reporting it would fail every file
        # that states one honestly.
    return out


def _cycles(backlog: Backlog, file: str) -> list[Finding]:
    """A group of tasks that wait on each other, anchored on its lowest id."""
    out: list[Finding] = []
    prefix = backlog.config.schema.prefix
    for group in Graph.of(backlog).cycles():
        anchor = min(group, key=lambda i: (number_of(i, prefix) or 0, i))
        entry = backlog.entry(anchor)
        # A group of one is the same defect through a `Block X` dep the task is itself a
        # member of: the block cannot empty until this line ships, so the line waits on
        # itself. Worth its own sentence — "wait on each other" reads as a tool bug.
        message = (
            f"{' ↔ '.join(group)} wait on each other, so nothing in the group can be "
            f"started"
            if len(group) > 1
            else f"{anchor} is in its own blocker set, so no amount of shipping "
            f"anything else makes it ready"
        )
        out.append(
            Finding(
                "deps.cycle",
                file,
                message,
                None if entry is None else entry.lineno,
                anchor,
            )
        )
    return out
