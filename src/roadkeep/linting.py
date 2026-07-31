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

And one file the tool never writes: **an always-loaded instruction file has a budget, and
a budget stated in its own prose is what let Shio's `agents.md` reach 186 KB** while
declaring 150 lines at the bottom of itself (RK30). So `roadkeep.toml` declares it and the
exit code holds it, in lines and in bytes — the two units the reader actually pays.

**Two tiers, because the exit code is the contract.** A :class:`Finding` fails the build;
a :class:`Note` is something the gate says at exit 0. Both exist because two real defects
cannot be refused without failing an honest file: `Block P` is a legitimate dep that
happens to name forty-eight open tasks (RK35), and a rationale section edited without its
task line is the shape of a smuggled requirement *and* of a typo fix (RK36). Refusing
either would produce a gate that gets bypassed, which is worth less than a sentence read
at the moment of the commit — the same split `audit` (RK10) makes.

Everything above is decidable from the files as they are. The one check that is about a
*change* is opt-in through ``since``, because `lint` has to keep working in a checkout with
no history: `--since HEAD` in a commit hook, the base branch in CI.

What is deliberately *not* here: normalizing what is mechanical, which is a write and lives
in :mod:`roadkeep.fixing` (RK16). This module answers one question completely and never
writes: *is every line in the governed files a line this format accepts, does everything it
points at exist, and did anything loaded every turn outgrow what it was allowed?*
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from roadkeep import scoping
from roadkeep.backlog import Backlog, DepStatus, number_of
from roadkeep.config import ROLES, Config
from roadkeep.document import Document, ending
from roadkeep.graph import Graph
from roadkeep.history import (
    HistoryUnavailable,
    content_at,
    resolves,
    touched_since,
)
from roadkeep.markers import derive
from roadkeep.schema import DepKind, Task
from roadkeep.sections import Section, anchored, find
from roadkeep.showing import paths_in

#: The governed files whose unit is a task line. The prose files are paragraphs, so
#: their gate is a pointer and a budget — RK15 and RK30, not this.
LINE_ROLES = ("roadmap", "changelog")

#: Variation selectors, which are `Mn` and not a format category: invisible all the same,
#: and the class the parser already had to defend against (`_looks_like_marker`, RK2).
_VARIATION_SELECTORS = frozenset(
    chr(point) for point in (*range(0xFE00, 0xFE10), *range(0xE0100, 0xE01F0))
)

_ENDING_NAMES = {"\r\n": "CRLF", "\n": "LF", "\r": "CR"}


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
    #: 1-based column, for a finding about one character (RK34). An invisible codepoint
    #: cannot be found by eye, so the offset is half of what makes the report usable.
    column: int | None = None

    @property
    def where(self) -> str:
        if self.lineno is None:
            return self.file
        if self.column is None:
            return f"{self.file}:{self.lineno}"
        return f"{self.file}:{self.lineno}:{self.column}"

    def __str__(self) -> str:
        subject = f"{self.id}: " if self.id else ""
        return f"{self.where}  {self.code}  {subject}{self.message}"


@dataclass(frozen=True, slots=True)
class Note:
    """Something the gate says and does not fail on (RK35).

    A separate list from :class:`Finding` because the exit code is the contract: `Block P`
    is a legitimate dep (RK28) and failing a build over one would fail the honest backlog
    this tool was measured against. But it is one token naming forty-eight open tasks, and
    a reader counting deps to judge how blocked a line is has no way to see that from the
    line — so the expansion is stated, at exit 0, which is the same split `audit` (RK10)
    makes between reporting a miss and being the gate.
    """

    code: str
    file: str
    message: str
    lineno: int | None = None
    id: str = ""

    def __str__(self) -> str:
        where = self.file if self.lineno is None else f"{self.file}:{self.lineno}"
        subject = f"{self.id}: " if self.id else ""
        return f"{where}  {self.code}  {subject}{self.message}"


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
    #: Always-loaded files whose budget was measured (RK30).
    budgets: int = 0
    #: What the gate observed without failing on it (RK35). Never affects the exit code.
    notes: tuple[Note, ...] = ()

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


def lint(config: Config, since: str | None = None) -> Report:
    """Read every governed file and return every defect. Writes nothing, ever.

    ``since`` adds the one check that is about a *change* rather than a state (RK36): a
    revision to diff the governed files against, `HEAD` in a pre-commit hook and the base
    branch in CI.
    """
    findings: list[Finding] = []
    findings.extend(_absent(config))

    documents: dict[str, Document] = {}
    for role in LINE_ROLES:
        if config.has(role) and config.path(role).is_file():
            documents[role] = config.document(role)

    checked = [config.relative(config.path(role)) for role in documents]
    for role, document in documents.items():
        findings.extend(_within(config, role, document))
        findings.extend(_characters(config, role, document))
    findings.extend(_across(config, documents))
    findings.extend(_scope(config, documents.get("roadmap")))
    notes: list[Note] = _collective(config, documents)

    prose = _prose_file(config)
    sections = ()
    if prose is not None:
        checked.append(config.relative(config.path("improvements")))
        sections = anchored(prose)
        findings.extend(_pointers(config, documents, sections))
        findings.extend(_orphans(config, documents, prose, sections))
        if since is not None:
            notes.extend(_unpaired(config, sections, since))
    findings.extend(_paths(config, documents))

    for budget in config.budgets:
        checked.append(config.relative(budget.path))
    findings.extend(_budgets(config))

    # A line carrying a byte nobody typed is not a line this format can judge: the parser
    # read a string the author cannot see, so every other diagnosis of it names a
    # consequence (RK34). Report the codepoint; the rest is decidable on the next run.
    tainted = {
        (f.file, f.lineno) for f in findings if f.code.startswith("char.") and f.lineno
    }
    findings = [
        f
        for f in findings
        if f.code.startswith("char.") or (f.file, f.lineno) not in tainted
    ]

    order = {name: index for index, name in enumerate(checked)}
    findings.sort(key=lambda f: (order.get(f.file, len(order)), f.lineno or 0, f.code))
    return Report(
        findings=tuple(findings),
        checked=tuple(checked),
        lines=sum(len(d.entries) for d in documents.values()),
        sections=len(sections),
        budgets=len(config.budgets),
        notes=tuple(notes),
    )


def _characters(config: Config, role: str, document: Document) -> list[Finding]:
    """Name the byte, not its consequence (RK34).

    The format is structural Unicode — `—`, `→`, `§` and four emoji markers — so every
    lookalike a human editor produces is invisible exactly where it fails. Measured
    against this parser: `📋` plus U+FE0F is reported as `status.unknown`, which prints as
    "'📋️' is not one of 📋"; a no-break space before the pointer is reported as
    `why.no-terminator`, naming the one thing the line does not lack. Both are correct and
    unusable, because the character that caused them cannot be seen.

    Only the line-bearing files. A paragraph has no parse for an invisible byte to corrupt,
    and §RK34 had to *quote* a variation selector to explain the defect — which a scan over
    prose would have reported as the defect itself.
    """
    file = config.relative(config.path(role))
    ids = {entry.lineno: entry.task.id for entry in document.entries}
    out = _endings(document, file)
    for number, raw in enumerate(document.lines, start=1):
        for column, char in enumerate(raw.rstrip("\r\n"), start=1):
            if not suspect(char):
                continue
            out.append(_named(file, number, column, char, ids.get(number, "")))
    return out


def suspect(char: str) -> bool:
    """Is this codepoint invisible, or a space that is not the space?

    Defined by Unicode category rather than a hand-kept list, so a control or format
    character nobody has met yet is caught too: `Cc` and `Cf` are not text, `Zl` and `Zp`
    are line breaks inside a line, and a `Zs` other than U+0020 renders as a space while
    comparing unequal to one. Variation selectors are `Mn` and named explicitly — U+FE0F
    on a marker is the case the parser already had to defend against (RK2).
    """
    if char in _VARIATION_SELECTORS:
        return True
    category = unicodedata.category(char)
    return category in ("Cc", "Cf", "Zl", "Zp") or (category == "Zs" and char != " ")


def _named(file: str, lineno: int, column: int, char: str, task_id: str) -> Finding:
    point = f"U+{ord(char):04X}"
    name = unicodedata.name(char, "unnamed control character").lower()
    if lineno == 1 and column == 1 and char == "﻿":
        # Its own answer: a byte-order mark is not text at all, and it lands on whatever
        # the first line happens to be — which is a heading, so nothing else reports it.
        return Finding(
            "char.bom",
            file,
            f"{point} byte-order mark at the start of the file: not text, and a byte the "
            f"round-trip compares",
            lineno,
            task_id,
            column,
        )
    if unicodedata.category(char) == "Zs":
        return Finding(
            "char.space",
            file,
            f"{point} {name} at column {column}: renders as a space and is not one, so "
            f"the grammar reads a word where a separator was meant",
            lineno,
            task_id,
            column,
        )
    return Finding(
        "char.invisible",
        file,
        f"{point} {name} at column {column}: invisible in an editor, so every other "
        f"diagnosis of this line names the consequence instead",
        lineno,
        task_id,
        column,
    )


def _endings(document: Document, file: str) -> list[Finding]:
    """Two kinds of line ending in one file — one line edited by something else.

    A file that is *uniformly* CRLF is not a defect and is not reported: `Document` keeps
    every ending verbatim, so it round-trips, and a repository that checks out CRLF is a
    configuration rather than a mistake (L6). Mixed is the byte nobody typed.
    """
    found: dict[str, int] = {}
    for line in document.lines:
        terminator = ending(line)
        if terminator:
            found[terminator] = found.get(terminator, 0) + 1
    if len(found) < 2:
        return []
    spelled = ", ".join(
        f"{count}× {_ENDING_NAMES[terminator]}" for terminator, count in sorted(found.items())
    )
    return [
        Finding(
            "char.mixed-endings",
            file,
            f"two kinds of line ending in one file ({spelled}): one of them was written "
            f"by something that is not this tool, and the round-trip compares bytes",
        )
    ]


def _budgets(config: Config) -> list[Finding]:
    """Every always-loaded file, against what it declared it may cost (RK30).

    Measured in bytes off the disk and lines by counting terminators, so nothing here has
    to decode a file the tool does not govern: a budget is about what a loader pays, and
    an instruction file is not a format this tool has any business parsing (L4).
    """
    out: list[Finding] = []
    for budget in config.budgets:
        where = config.relative(budget.path)
        if not budget.path.is_file():
            out.append(
                Finding(
                    "budget.absent",
                    where,
                    "declares a budget and is not on disk: the entry holds nothing",
                )
            )
            continue
        raw = budget.path.read_bytes()
        lines = raw.count(b"\n") + (0 if raw.endswith(b"\n") or not raw else 1)
        for unit, measured, allowed in (
            ("lines", lines, budget.lines),
            ("bytes", len(raw), budget.bytes),
        ):
            if allowed is not None and measured > allowed:
                out.append(
                    Finding(
                        f"budget.{unit}",
                        where,
                        f"{measured} {unit}, budget is {allowed}: this is loaded every "
                        f"turn, so the overrun is paid on every turn",
                    )
                )
    return out


def _collective(config: Config, documents: dict[str, Document]) -> list[Note]:
    """What a `Block X` or a range actually names, said out loud (RK35).

    Only when it expands to **two or more** open tasks, which is precisely the case the
    line hides: at one there is no surprise to report, and at zero the annotation already
    reads ✅ because the dep is satisfied (RK8). A note per token below that threshold
    would be output nobody reads, which is the failure mode RK16 exists to avoid.
    """
    roadmap = documents.get("roadmap")
    if roadmap is None:
        return []
    backlog = Backlog(
        config=config, roadmap=roadmap, ledger=documents.get("changelog")
    )
    file = config.relative(config.path("roadmap"))
    out: list[Note] = []
    for entry in roadmap.entries:
        for dep in entry.task.deps:
            if config.schema.classify_dep(dep) not in (DepKind.BLOCK, DepKind.RANGE):
                continue
            members = backlog.expand(dep)
            if len(members) < 2:
                continue
            shown = ", ".join(members[:6]) + (" …" if len(members) > 6 else "")
            out.append(
                Note(
                    "deps.collective",
                    file,
                    f"{dep.id} is one token naming {len(members)} open tasks: {shown}",
                    entry.lineno,
                    entry.task.id,
                )
            )
    return out


def _unpaired(config: Config, sections: tuple[Section, ...], since: str) -> list[Note]:
    """A rationale section edited without touching the line that carries its status (RK36).

    RK15 refuses a pointer at a section that does not exist; this is the mirror, and the
    more expensive direction: the line is the only thing `pick` reads and the section is
    deleted on ship, so a requirement written only into the rationale cannot be picked,
    cannot be shipped, and leaves with the section that held it. It happened three times in
    one session here, every time by an author who had just learned something and wrote it
    where the reasoning was rather than where the status is.

    A **note**, not a finding, and this is the whole judgement: the check cannot tell a
    typo in a paragraph from a smuggled requirement, and a gate that failed every honest
    rationale edit would be bypassed within a week — which is worth less than a sentence
    read at the moment of the commit. It is deliberately not semantic (§RK36 says so): the
    signal is that the section was open and the line was not.
    """
    if not resolves(config, since):
        # A repository with no commits has no HEAD, which is the shipped hook's default —
        # so the initial commit is not the thing this fails on.
        if since == "HEAD":
            return []
        raise HistoryUnavailable(f"{since} is not a revision this repository knows")

    edited = touched_since(config, since, "improvements")
    if not edited.changes:
        return []
    ids = config.schema.id_pattern()
    mentioned = re.compile(rf"\*\*({re.escape(config.schema.prefix)}[1-9][0-9]*)\*\*")
    touched_ids = {
        found
        for role in LINE_ROLES
        for line in touched_since(config, since, role).lines
        for found in mentioned.findall(line)
    }
    # The file as it was, so a *removal* is attributed to the section that held it. Without
    # this a deleted section lands in whichever one now precedes the hole — and the section
    # `ship` just deleted would be reported against its innocent neighbour every time.
    before = anchored(
        Document.parse(content_at(config, since, "improvements"), schema=config.schema)
    )

    opened: set[str] = set()
    for change in edited.changes:
        if not change.text.strip():
            # A blank belongs to no section's prose, and counting it would attribute an
            # appended section to the one whose trailing blank line it starts on.
            continue
        anchor = _section_at(sections if change.added else before, change.lineno)
        if anchor is not None:
            opened.add(anchor)

    here = {section.anchor: section for section in sections}
    out: list[Note] = []
    for anchor in sorted(opened):
        section = here.get(anchor)
        if section is None or not ids.match(anchor) or anchor in touched_ids:
            continue
        out.append(
            Note(
                "section.unpaired",
                config.relative(config.path("improvements")),
                f"§{anchor} was edited and {anchor}'s line was not: the line is the only "
                f"thing `pick` reads, and this section is deleted on ship — so a "
                f"requirement written only here goes with it",
                section.first,
                anchor,
            )
        )
    return out


def _section_at(sections: tuple[Section, ...], lineno: int) -> str | None:
    """The anchor whose span holds this line, or None for prose under no anchor."""
    return next(
        (s.anchor for s in sections if s.first <= lineno <= s.last),
        None,
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


def _scope(config: Config, roadmap: Document | None) -> list[Finding]:
    """The non-goals, for a project that declared them governed (RK70).

    Silent otherwise, and that is the whole of the opt-in: two live corpora wrote their lists
    as free prose years before this grammar existed, and a gate that reported fifteen findings
    on the first run is a gate that gets bypassed rather than adopted (RK66).

    What is judged is what the schema can judge — the shape, the two lengths, and a lead
    claimed twice. Not the wrap: a filled bullet is written at insertion (L1) and a
    hand-wrapped one is whitespace inside prose, which `--fix` is the door for (RK16).
    """
    if roadmap is None or config.non_goals is None:
        return []
    file = config.relative(config.path("roadmap"))
    out: list[Finding] = []
    for lineno, raw in scoping.rejects(roadmap):
        out.append(
            Finding(
                scoping.SHAPE,
                file,
                f"a governed non-goal is `- **<lead>** <why>`, so this bullet has no lead "
                f"to be addressed by: {raw.strip()[:60]!r}",
                lineno,
            )
        )
    seen: dict[str, int] = {}
    for non_goal in scoping.read(roadmap):
        for violation in scoping.validate(config, non_goal.lead, non_goal.why):
            out.append(Finding(violation.code, file, violation.message, non_goal.first))
        lead = scoping.address(non_goal.lead)
        first = seen.get(lead)
        if first is not None:
            out.append(
                Finding(
                    "non-goal.duplicate",
                    file,
                    f"already led on line {first}: the lead is the address, so two bullets "
                    f"carrying it are two answers about one scope",
                    non_goal.first,
                )
            )
        seen.setdefault(lead, non_goal.first)
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
        out.extend(_budget(prose, section, pointed=anchor in pointed, file=file))
        owners = _owners(section, ids)
        # Prose that belongs to no task is nobody's orphan — `§0.1` under the id scheme, and
        # any outline heading that names no id — the same rule `section add` applies (RK9).
        if owners and not any(owner in open_ids for owner in owners):
            out.append(
                _unowned(
                    section,
                    file,
                    shipped=any(owner in gone for owner in owners),
                    owners=owners,
                )
            )
    return out


def _owners(section: Section, ids: re.Pattern[str]) -> tuple[str, ...]:
    """The tasks this section belongs to, whichever scheme addresses it (RK61).

    Under `ref_scheme = "id"` the anchor *is* the id. Under an outline the anchor is
    `XVI.12` and the id is in the heading — `§XVI.12 A design (SH123)` — which is why both
    checks below fired for nobody in the two live corpora until this read it.

    So **naming a task in a heading is the claim to be its rationale**, with no exemption for
    where the section sits. The first attempt made one — "a task's section is under a `Block X`
    heading", read off this repository's own file — and it disabled the check on the corpus it
    was written for: Shio files its rationale under `## VIII. The Agent Gateway (Block H)`,
    which is an outline heading, so all 146 of its sections looked unowned. A section that
    means to cite a task rather than belong to it says so in its prose, which this never reads.
    """
    if ids.match(section.anchor):
        return (section.anchor,)
    return section.names(re.compile(rf"\b{ids.pattern.strip('^$')}\b"))


def _budget(
    prose: Document, section: Section, *, pointed: bool, file: str
) -> list[Finding]:
    handed = (find(prose, section.anchor) if pointed else None) or section
    # The prose file's own budget where it declares one (RK50): `[limits.improvements]` is
    # the same declaration `[limits.changelog]` is, and this is the file it governs.
    limit = prose.schema.section_max
    if handed.words <= limit:
        return []
    return [
        Finding(
            "section.too-long",
            file,
            f"{handed.words} words, limit is {limit}: a section "
            f"this long is two sections, or a paragraph that belongs in the commit",
            section.first,
            section.anchor,
        )
    ]


def _unowned(
    section: Section, file: str, *, shipped: bool, owners: tuple[str, ...]
) -> Finding:
    """A section whose task no open line carries — gone, or never there.

    `owners` is what the section says it belongs to, which is the anchor under the id scheme
    and the ids in the heading under an outline (RK61). Named in the message, because
    `§XVI.12` alone tells a reader nothing about which task left.
    """
    named = ", ".join(owners)
    if shipped:
        return Finding(
            "section.stale",
            file,
            f"{named} is in the changelog and this rationale is still here: "
            f"`ship` deletes the section, so this survived a hand edit",
            section.first,
            section.anchor,
        )
    return Finding(
        "section.orphan",
        file,
        f"no line in either file carries {named}, so nothing can ever point "
        f"at this section",
        section.first,
        section.anchor,
    )


def _paths(config: Config, documents: dict[str, Document]) -> list[Finding]:
    """Paths a *shipped* line claims, resolved against disk (RK15, narrowed by RK46).

    Two exemptions, and both turn on which file is being read rather than on the token.

    Lines only: an unshipped design's whole job is to describe a file that does not exist
    yet — §RK26 names `.claude-plugin/marketplace.json` and is right to — so resolving a
    section's prose would fail every honest forward reference.

    And the ledger only, which is the same reasoning applied one file up. A roadmap
    describes work that has **not happened**, so the paths in it are disproportionately
    the artefacts its tasks exist to write; naming one is what a task line is for. Shio
    had eight such findings and all eight were false. A shipped line is the opposite
    claim — the work is done, so a path it names and the repository lacks is a real
    defect, and the only one here worth exit 1.
    """
    document = documents.get("changelog")
    if document is None:
        return []
    file = config.relative(config.path("changelog"))
    return [
        Finding(
            "path.missing",
            file,
            f"names {referenced.path}, which is not in the repository",
            entry.lineno,
            entry.task.id,
        )
        for entry in document.entries
        # `near` is the ledger's own directory (RK51): a link written the way Markdown
        # reads it points at a file that is there, and 886 of Shio's are written that way.
        for referenced in paths_in(entry.raw, config.root, near=config.path("changelog").parent)
        if not referenced.exists
    ]


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
