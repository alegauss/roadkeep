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

And the same question asked of the prose file, which is RK15's half: **a pointer that
resolves to nothing reads exactly like a design that exists**, which is worse than no
pointer because it makes a reader stop looking. So the `→ §RK<n>` is resolved against
the improvements file, in both directions — a pointer with no section, and a section no
line points at — plus the section's word budget and the paths a line claims. The
pointer is read from the parsed ``ref`` field and never from the line's text: §RK15's
own `why` quotes a pointer as an example, and a scan over the line would report that
quotation as the broken pointer it is not.

What is deliberately *not* here, because each is its own task and a gate that grew all
of them at once would be a gate nobody could adopt: normalizing what is mechanical
(RK16), the always-loaded file budgets (RK30), naming an invisible codepoint (RK34),
and what a commit touched (RK36). This one answers a narrower question completely: *is
every line in the governed files a line this format accepts, and does everything it
points at exist?*
"""

from __future__ import annotations

from dataclasses import dataclass

from roadkeep.backlog import Backlog, DepStatus, number_of
from roadkeep.config import ROLES, Config
from roadkeep.document import Document
from roadkeep.graph import Graph
from roadkeep.markers import derive
from roadkeep.schema import DepKind, Task
from roadkeep.sections import Section, anchored, find
from roadkeep.showing import paths_in

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
    #: Anchored sections read in the prose file — the other half of what was checked.
    sections: int = 0

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

    checked = [config.relative(config.path(role)) for role in documents]
    for role, document in documents.items():
        findings.extend(_within(config, role, document))
    findings.extend(_across(config, documents))

    prose = _prose_file(config)
    sections = ()
    if prose is not None:
        checked.append(config.relative(config.path("improvements")))
        sections = anchored(prose)
        findings.extend(_pointers(config, documents, sections))
        findings.extend(_orphans(config, documents, prose, sections))
    findings.extend(_paths(config, documents))

    order = {name: index for index, name in enumerate(checked)}
    findings.sort(key=lambda f: (order.get(f.file, len(order)), f.lineno or 0, f.code))
    return Report(
        findings=tuple(findings),
        checked=tuple(checked),
        lines=sum(len(d.entries) for d in documents.values()),
        sections=len(sections),
    )


def _prose_file(config: Config) -> Document | None:
    """The improvements file, when this project has one on disk.

    A project that declares none is Shio, not a Shio with an empty one, and a declared
    file that is not there yet is already `file.missing` — neither is a pointer defect.
    """
    if not config.has("improvements") or not config.path("improvements").is_file():
        return None
    return config.document("improvements")


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


def _pointers(
    config: Config, documents: dict[str, Document], sections: tuple[Section, ...]
) -> list[Finding]:
    """Every `→ §<anchor>` on an open line, resolved against the prose file (RK15).

    Read from the parsed ``ref`` and never from the line's text, which is the whole
    subtlety: §RK15's own sentence quotes a pointer as an example of one, and a scan
    over the raw line reports that quotation as a design that does not exist.
    """
    roadmap = documents.get("roadmap")
    if roadmap is None:
        return []
    where = config.relative(config.path("improvements"))
    anchors = {section.anchor for section in sections}
    return [
        Finding(
            "ref.unresolved",
            config.relative(config.path("roadmap")),
            f"points at §{entry.task.ref}, which is not in {where}: a pointer to a "
            f"section that does not exist reads as a design that does",
            entry.lineno,
            entry.task.id,
        )
        for entry in roadmap.entries
        if entry.task.ref and entry.task.ref not in anchors
    ]


def _orphans(
    config: Config,
    documents: dict[str, Document],
    prose: Document,
    sections: tuple[Section, ...],
) -> list[Finding]:
    """The prose file read from its own side: a section, and what points at it.

    A pointer resolves one way only, so nothing in `_pointers` can see a section that
    survived its task. Three ways that happens and one budget, all at the anchor's line.

    The budget is charged against **what a pointer hands a reader**, which is the one
    reading that keeps RK9's rule and this repository's own file both true: a section a
    line points at is measured with its subsections (`show` prints them, so a rationale
    that doubled by growing a `§RK34.1` is caught), and one nothing points at is measured
    on its own prose (`§0` is a container whose three anchored children are each inside
    the budget, and charging it 461 words would fail a file with no long paragraph in it).
    """
    file = config.relative(config.path("improvements"))
    open_ids = documents["roadmap"].by_id() if "roadmap" in documents else {}
    gone = documents["changelog"].by_id() if "changelog" in documents else {}
    pointed = {
        entry.task.ref
        for document in documents.values()
        for entry in document.entries
        if entry.task.ref
    }
    ids = config.schema.id_pattern()
    seen: dict[str, int] = {}
    out: list[Finding] = []

    for section in sections:
        anchor = section.anchor
        first = seen.get(anchor)
        if first is not None:
            out.append(
                Finding(
                    "section.duplicate",
                    file,
                    f"§{anchor} is already at line {first}: an anchor names one "
                    f"section, and a pointer that resolves to two resolves to neither",
                    section.first,
                    anchor,
                )
            )
        seen.setdefault(anchor, section.first)
        out.extend(_budget(config, prose, section, pointed=anchor in pointed, file=file))
        # Only an id-shaped anchor is owned by a task. `§0.1` is prose that belongs to
        # no line and is nobody's orphan — the same rule `section add` applies (RK9).
        if ids.match(anchor) and anchor not in open_ids:
            out.append(_unowned(section, file, shipped=anchor in gone))
    return out


def _budget(
    config: Config, prose: Document, section: Section, *, pointed: bool, file: str
) -> list[Finding]:
    handed = (find(prose, section.anchor) if pointed else None) or section
    if handed.words <= config.schema.section_max:
        return []
    return [
        Finding(
            "section.too-long",
            file,
            f"{handed.words} words, limit is {config.schema.section_max}: a section "
            f"this long is two sections, or a paragraph that belongs in the commit",
            section.first,
            section.anchor,
        )
    ]


def _unowned(section: Section, file: str, *, shipped: bool) -> Finding:
    """An id-shaped anchor that no open line carries — gone, or never there."""
    if shipped:
        return Finding(
            "section.stale",
            file,
            f"{section.anchor} is in the changelog and its rationale is still here: "
            f"`ship` deletes the section, so this survived a hand edit",
            section.first,
            section.anchor,
        )
    return Finding(
        "section.orphan",
        file,
        f"no line in either file carries {section.anchor}, so nothing can ever point "
        f"at this section",
        section.first,
        section.anchor,
    )


def _paths(config: Config, documents: dict[str, Document]) -> list[Finding]:
    """Paths a task *line* claims, resolved against disk (RK15).

    Lines only, and the exemption is the point: an unshipped design's whole job is to
    describe a file that does not exist yet — §RK26 names `.claude-plugin/marketplace.json`
    and is right to — so resolving a section's prose would fail every honest forward
    reference. A line is a claim about the repository as it is now.
    """
    out: list[Finding] = []
    for role, document in documents.items():
        file = config.relative(config.path(role))
        for entry in document.entries:
            out.extend(
                Finding(
                    "path.missing",
                    file,
                    f"names {referenced.path}, which is not in the repository",
                    entry.lineno,
                    entry.task.id,
                )
                for referenced in paths_in(entry.raw, config.root)
                if not referenced.exists
            )
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
