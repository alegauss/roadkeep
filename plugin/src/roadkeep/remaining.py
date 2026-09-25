"""What a task has left, derived from the repository rather than written down (RK492).

§RK72's non-goal refuses a **stored** size: nothing can verify a letter, so the field rots
from the first commit that makes it wrong. :mod:`roadkeep.weighing` is what replaced it —
the same question, derived from the commits that shipped comparable work, landing on no line
and rotting never. This is that question's mirror and it takes the same answer.

RK488, RK489, RK490 and RK491 were each one invariant with **sites**: emitters spelling a
command themselves, subparsers validating their own flags, rows repeating what their finding
already carries, rules no property reaches. Every one of them was enumerable by a query the
task could have declared — a grep over the package, a set difference against a table — and
none of them had a way to ask how many were left. So a migration read in every governed file
exactly like a run of unrelated defects, which is how the last fifty commits read here, and
the reading was wrong.

**Where the declaration lives is the whole of the decision.** Three places were possible and
two are wrong. A field on the line is what §RK72 refuses and what `[limits]` would then have
to price. `roadkeep.toml` outlives the task and is per project, so a query about one
migration would sit in it after the migration shipped, with nothing to delete it. What is
left is the **rationale section**, and it is not a fallback: the query is a statement about
the design, it is in the repository (L2), a `ship` deletes it with the section that made the
claim, and a reader who greps for the pattern finds the paragraph that says what it is for.

So a section may carry one fenced block tagged :data:`FENCE`, and each line in it is a
**pathspec and a pattern**. Nothing here interprets either: the glob is the author's and the
regex is the author's, which is L4 one level down — this counts what somebody else declared
and composes no part of the claim. The count is computed on demand, so it cannot go stale, it
costs nothing on the turns nobody asks (L5), and it is checkable by running the query printed
beside it.

What this is **not** is a progress bar. A query that answers `0` says the pattern no longer
matches, not that the work is done: the author chose the pattern, and a migration whose last
site is spelled differently is one this reports clean. That is stated rather than defended
against, for the reason the size field was refused — the alternative is a number the tool
asserts and nobody can check.

**A clause may end on a comparison, for a deliverable that is not text** (RK1687). The
grammar asked whether text is *there*, and a project whose proof is a number out of a PNG, a
WAV, a mesh or a frame time could not write one: measured on Cottony, where the two art lines
carrying a real acceptance test carry it as prose. RK99's is the 99th percentile of saturation
inside the board, 0.683 against a reference's 0.881, and its section ends *"re-run the same
crop and compare the percentile, not the mean"* — an instruction sitting in the one thing
`ship` deletes.

So a third field, on the same separator: `<pathspec> :: <regex> :: <op> <number>`, where the
pattern captures the value and the comparison says what it has to be. **The number is the
project's own**, written by whatever already computes it, and nothing here runs a generator or
opens a picture — this reads a figure somebody else produced and does the arithmetic, which is
`evidence`'s existing shape with a relation where the count was. The non-goal binds and is not
approached: no model, no prompts, no opinion about an image.

It is a **filter on matches** and not a second verdict, which is what keeps every reading
downstream the one it already was — a site is still a place the author's pattern points at,
`evidence` still counts the sites that must exist, and `remaining` still counts what is left.
A match whose capture is not a number is :attr:`Remaining.unparsed` and never a failed
comparison: an `n/a` is a query that did not run over that line, and merging the two is the
failure this module was extended out of.

**And a zero that means neither of those is named** (RK1216). The sentence above has one more
reading it cannot carry: a pathspec that reached **no file at all**, where the pattern was
never run over anything. Measured in pportal declaring its first two queries — `lib/src ::
<regex>` on both, a directory that `Path.glob` matches as one entry that is not a file — and
both answered `0 site(s) left in 0 file(s)` over trees holding 14 and 420 sites. The count
this verb exists to be trusted with had a failure mode indistinguishable from success, and
the tell was a second number beside it. So :attr:`Remaining.unmatched` says it in words, on
the headline and per clause. Refusing was the other candidate and is not this module's to
make: a query is a claim in a file, and a claim nothing answers is the gate's kind of finding.
"""

from __future__ import annotations

import operator
import re
from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType

#: The info string a fenced block carries to be read as a query. Hyphenated rather than
#: `roadkeep:remaining`, because a colon in an info string is how several renderers spell a
#: language attribute and this has to survive being viewed on a forge.
FENCE = "roadkeep-remaining"

#: The other fence, and the same grammar (RK1184). A design says what is *left* and what would
#: *prove it done*, and the two are one read with the sign flipped — sites that must exist
#: rather than sites still there. A second tag and never a second parser: the clause, the
#: separator, the refusal and the count are all shared, so a query that is legal in one block
#: is legal in the other by construction.
EVIDENCE = "roadkeep-evidence"

#: What separates a pathspec from the pattern that marks a site. Two colons and not one: a
#: glob carries no `::` and a regex that wants one spells it `:{2}`, so the split is
#: unambiguous without anything here parsing either half.
SEPARATOR = "::"

#: How many addresses a report prints before it says how many more there are. The count is
#: the answer; the addresses are what makes it checkable, and a list nobody scrolls is a
#: list that costs context (RK146).
SHOWN = 10


class QueryError(ValueError):
    """A fence this grammar cannot read, naming the line inside it that failed."""

    def __init__(self, line: int, said: str) -> None:
        self.line = line
        super().__init__(f"line {line} of the {FENCE} block: {said}")


#: The comparisons a clause may end on (RK1687), and deliberately only these six. Each is a
#: relation between two numbers and composes nothing: what a project declares is where its own
#: number is written and what it has to be, and the arithmetic here is the whole of what this
#: tool contributes.
COMPARISONS: Mapping[str, Callable[[float, float], bool]] = MappingProxyType(
    {
        ">=": operator.ge,
        "<=": operator.le,
        ">": operator.gt,
        "<": operator.lt,
        "==": operator.eq,
        "!=": operator.ne,
    }
)


@dataclass(frozen=True, slots=True)
class Clause:
    """One pathspec and the pattern that marks a site inside it."""

    #: A glob relative to the project root, as `Path.glob` reads one.
    pathspec: str
    #: The pattern, as the author wrote it — kept as text beside the compiled form so the
    #: report can print the query it ran rather than a repr of a compiled object.
    pattern: str
    matcher: re.Pattern[str]
    #: The comparison this clause ends on, or `""` where it counts matches as it always did
    #: (RK1687). One of :data:`COMPARISONS`.
    op: str = ""
    #: What the captured number is compared against. Meaningless without :attr:`op`.
    threshold: float = 0.0

    @property
    def compares(self) -> bool:
        return bool(self.op)

    def admits(self, captured: str) -> bool | None:
        """Whether this match is a site, or None where the capture is not a number.

        Named away from `holds`, which is `Document`'s and `Backlog`'s word and whose readers
        `tests/test_document.py` keeps enumerable: an unrelated method sharing the spelling
        defeats that scan rather than joining it.

        `None` and not `False`, because they are two different answers: a value that read
        `n/a` is a query that did not run over that line, and counting it as a failing
        comparison would be the `in 0 file(s)` defect this module was extended out of.
        """
        try:
            found = float(captured)
        except (TypeError, ValueError):
            return None
        return COMPARISONS[self.op](found, self.threshold)

    def __str__(self) -> str:
        spelled = f"{self.pathspec} {SEPARATOR} {self.pattern}"
        if self.compares:
            # The third field printed as it was written, so the query beside a count is one a
            # reader can paste back — which is what makes the number checkable.
            spelled += f" {SEPARATOR} {self.op} {self.threshold:g}"
        return spelled


@dataclass(frozen=True, slots=True)
class Site:
    """One place the query still matches."""

    file: str
    lineno: int
    text: str

    def __str__(self) -> str:
        return f"{self.file}:{self.lineno}  {self.text.strip()}"


@dataclass(frozen=True, slots=True)
class Remaining:
    """What one task's declared query answers right now."""

    task_id: str
    clauses: tuple[Clause, ...]
    sites: tuple[Site, ...]
    #: Which fence this counted (RK1184). The numbers are identical and the sentences are
    #: opposites: `3 site(s) left` is work outstanding, and `3 site(s) of evidence` is what
    #: the author said would prove the task done. A field and not two classes, because every
    #: other property of the read — the scan, the refusal, the truncation — is one thing.
    kind: str = FENCE
    #: How many files each clause actually read, so a query whose glob names nothing is
    #: distinguishable from one whose pattern no longer matches. Two very different answers
    #: that both count zero, and the second is done while the first is a typo.
    scanned: tuple[int, ...] = ()
    #: Files a clause matched and this could not read as text, by path. Named and never
    #: skipped in silence: a count over a set that quietly lost a member is the defect this
    #: whole module is against.
    unread: tuple[str, ...] = ()
    #: Sites a comparing clause matched whose capture is not a number, as `file:line`
    #: (RK1687). :attr:`unread`'s rule one field in: the pattern found the place and the
    #: value there is `n/a`, a blank, or text — which is a query that did not run over that
    #: line, not a number that failed to clear the bar. Empty for every clause that counts
    #: matches, which is every clause written before the third field existed.
    unparsed: tuple[str, ...] = ()

    @property
    def total(self) -> int:
        return len(self.sites)

    @property
    def files(self) -> int:
        return sum(self.scanned)

    @property
    def unmatched(self) -> tuple[str, ...]:
        """The pathspecs that reached no file at all, in declaration order (RK1216).

        The distinction :attr:`scanned` was added to make and nothing then said out loud.
        Measured on pportal declaring its first two queries: both were given `lib/src ::
        <regex>`, which reads as a directory and which `Path.glob` matches as one entry that
        is not a file, so both answered `0 site(s) left in 0 file(s)`. The regexes were right
        — counted by hand the same trees hold 14 and 420, and corrected to `lib/src/**/*.c`
        this tool agrees exactly. Nothing was wrong but the glob.

        Which way the failure points is the whole finding. `0` is documented here to mean
        *the pattern stopped matching*, so the reading an author gets is **the migration is
        done**, and the truth was the opposite: the query never ran over anything. A failure
        mode indistinguishable from success, on the one question the verb exists to answer.

        The tell was already printed — `in 0 file(s)` sits beside the count — so this is
        about which of the two the eye lands on. Named rather than left to that arithmetic,
        and named per pathspec, because a query of three clauses where one reached nothing is
        short by an unknown amount while still looking like a total.
        """
        return tuple(
            clause.pathspec
            for clause, read in zip(self.clauses, self.scanned, strict=False)
            if not read
        )

    @property
    def counting(self) -> str:
        """`left` or `of evidence` — never a verdict either way (RK1184).

        The pattern is the author's claim and the count is the answer, so `0` says the
        evidence is not there yet and whether that is the work being done is the caller's
        judgement. This tool has no model of one (L4).
        """
        return "left" if self.kind == FENCE else "of evidence"

    def __str__(self) -> str:
        # On the **headline**, because the headline is the number being misread (RK1216): a
        # note under the clauses is the `in 0 file(s)` problem again one line down.
        never = ""
        if self.unmatched:
            never = (
                f" — {len(self.unmatched)} pathspec(s) matched no file, so this count is "
                f"a query that did not run and not work that is done"
            )
        lines = [
            f"{self.task_id}  {self.total} site(s) {self.counting} in {self.files} "
            f"file(s){never}"
        ]
        for clause, read in zip(self.clauses, self.scanned, strict=False):
            # Marked per clause too, so a three-clause query says *which* one reached nothing
            # rather than leaving the reader to find the zero among the counts.
            missed = "  ← matched no file" if not read else ""
            lines.append(f"  query    {clause}  ({read} file(s)){missed}")
        for site in self.sites[:SHOWN]:
            lines.append(f"  site     {site}")
        if self.total > SHOWN:
            lines.append(f"  … and {self.total - SHOWN} more")
        if self.unread:
            lines.append(f"  unread   {', '.join(self.unread)}: not text this could search")
        if self.unparsed:
            # Beside `unread` and for its reason (RK1687): the pattern found the place and
            # what stood there is not a number, which is a query that did not run over that
            # line rather than a value that failed the comparison.
            shown = ", ".join(self.unparsed[:SHOWN])
            more = f" … and {len(self.unparsed) - SHOWN} more" if len(self.unparsed) > SHOWN else ""
            lines.append(
                f"  unparsed {shown}{more}: matched, and the capture is not a number — "
                f"not a value that failed the comparison"
            )
        return "\n".join(lines)

    def payload(self) -> dict[str, object]:
        return {
            "id": self.task_id,
            # Which question was asked, because the two payloads are otherwise identical and
            # a consumer acting on `total` means opposite things by it (RK1184).
            "kind": self.kind,
            "total": self.total,
            "files": self.files,
            "query": [
                {
                    "pathspec": one.pathspec,
                    "pattern": one.pattern,
                    "files": read,
                    # Null where the clause counts matches (RK1687), which distinguishes a
                    # query with no comparison from one comparing against zero.
                    "op": one.op or None,
                    "threshold": one.threshold if one.compares else None,
                }
                for one, read in zip(self.clauses, self.scanned, strict=False)
            ],
            # Every site and not the printed ten: a consumer acting per address needs them
            # all, and the truncation above is about a terminal (RK146).
            "sites": [{"file": s.file, "line": s.lineno, "text": s.text} for s in self.sites],
            "unread": list(self.unread),
            # The pathspecs that reached no file (RK1216). Its own key beside the per-clause
            # `files`, because a consumer deciding whether a migration is finished is reading
            # `total` — and the one state where `total` means nothing at all has to be
            # answerable without summing a list to find a zero in it.
            "unmatched": list(self.unmatched),
            # Sites a comparison matched whose capture is not a number (RK1687), for
            # `unmatched`'s reason: a consumer reading `total` needs the states where that
            # number is short by an amount nothing else names.
            "unparsed": list(self.unparsed),
        }


def declared(body: str, tag: str = FENCE) -> tuple[Clause, ...]:
    """The query a section's prose declares under ``tag``, or `()` where it declares none.

    One fence per section **per tag** (RK1184). A second of the same kind is refused rather
    than merged: two blocks are two claims about what is left, and the sum of them is a number
    neither paragraph states. The two *kinds* are a different matter — a design may say both
    what remains and what would prove it done, and neither is the other's total.
    """
    found: list[Clause] = []
    fences = list(_fenced(body, tag))
    if len(fences) > 1:
        raise QueryError(
            fences[1][0] + 1, "a section declares one query, and this is the second"
        )
    for offset, block in fences:
        # 1-based lines of the section body, so the number the refusal prints is one a
        # reader counts down the paragraph — the fence itself is `offset + 1`.
        for index, line in enumerate(block, start=offset + 2):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            found.append(_clause(index, stripped))
    return tuple(found)


def _fenced(body: str, tag: str = FENCE) -> Iterator[tuple[int, list[str]]]:
    """Each ``` block carrying ``tag``, as its 0-based start line and its lines."""
    lines = body.splitlines()
    index = 0
    while index < len(lines):
        opening = lines[index].strip()
        if opening.startswith("```") and opening[3:].strip() == tag:
            end = index + 1
            while end < len(lines) and not lines[end].strip().startswith("```"):
                end += 1
            yield index, lines[index + 1 : end]
            index = end + 1
            continue
        index += 1


def _clause(lineno: int, line: str) -> Clause:
    pathspec, separator, rest = line.partition(SEPARATOR)
    if not separator:
        raise QueryError(lineno, f"no {SEPARATOR!r}: a clause is `<pathspec> {SEPARATOR} <regex>`")
    # The third field, on the same separator as the second (RK1687): a regex that wants a
    # `::` already spells it `:{2}`, which is what made two colons unambiguous for the first
    # split and makes them unambiguous for this one.
    pattern, _, compared = rest.partition(SEPARATOR)
    pathspec, pattern, compared = pathspec.strip(), pattern.strip(), compared.strip()
    if not pathspec or not pattern:
        raise QueryError(lineno, "both halves are required: a pathspec, and the pattern")
    try:
        matcher = re.compile(pattern)
    except re.error as error:
        raise QueryError(lineno, f"the pattern is not a regex this can compile: {error}") from None
    if not compared:
        return Clause(pathspec=pathspec, pattern=pattern, matcher=matcher)
    op, _, threshold = compared.partition(" ")
    if op not in COMPARISONS:
        raise QueryError(
            lineno,
            f"{op!r} is not a comparison: a third field is `<op> <number>`, where the "
            f"operator is one of {' '.join(COMPARISONS)}",
        )
    try:
        against = float(threshold.strip())
    except ValueError:
        raise QueryError(
            lineno, f"{threshold.strip()!r} is not a number to compare against"
        ) from None
    if not matcher.groups:
        # Refused rather than run, because the alternative counts nothing and says the
        # evidence is absent: the pattern has to say *which* text is the number, and a
        # comparison with nothing captured is a query that can only ever answer zero.
        raise QueryError(
            lineno,
            "a comparison needs the pattern to capture the number: put the value in a "
            "group, as `saturation=([0-9.]+)`",
        )
    return Clause(
        pathspec=pathspec,
        pattern=pattern,
        matcher=matcher,
        op=op,
        threshold=against,
    )


@dataclass(slots=True)
class _Read:
    """One clause's answer, before the clauses are joined."""

    sites: list[Site] = field(default_factory=list)
    scanned: int = 0
    unread: list[str] = field(default_factory=list)
    unparsed: list[str] = field(default_factory=list)


def count(
    root: Path, task_id: str, clauses: Sequence[Clause], kind: str = FENCE
) -> Remaining:
    """Run a declared query against this tree, now.

    Nothing is cached and nothing is written. The whole value of the read is that it is
    taken at the moment somebody asks, which is what a stored count could never be.
    """
    sites: list[Site] = []
    scanned: list[int] = []
    unread: list[str] = []
    unparsed: list[str] = []
    for clause in clauses:
        read = _run(root, clause)
        sites += read.sites
        scanned.append(read.scanned)
        unread += read.unread
        unparsed += read.unparsed
    return Remaining(
        task_id=task_id,
        kind=kind,
        clauses=tuple(clauses),
        sites=tuple(sites),
        scanned=tuple(scanned),
        unread=tuple(dict.fromkeys(unread)),
        unparsed=tuple(dict.fromkeys(unparsed)),
    )


def _run(root: Path, clause: Clause) -> _Read:
    read = _Read()
    for path in sorted(root.glob(clause.pathspec)):
        if not path.is_file():
            continue
        where = path.relative_to(root).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            # Not an error and not silence: a clause whose glob reached a binary has read
            # fewer files than it looks like, and the count is only honest if it says so.
            read.unread.append(where)
            continue
        read.scanned += 1
        for lineno, line in enumerate(text.splitlines(), start=1):
            found = clause.matcher.search(line)
            if found is None:
                continue
            if not clause.compares:
                read.sites.append(Site(file=where, lineno=lineno, text=line))
                continue
            # The comparison is a **filter on matches** and never a second verdict (RK1687),
            # which is what keeps every reading downstream the one it already was: a site is
            # still a place the author's pattern points at, and `evidence` still counts the
            # sites that must exist. What the third field adds is which matches qualify.
            admitted = clause.admits(found.group(1))
            if admitted is None:
                # Matched, and the capture is not a number — an `n/a`, a blank, a value the
                # project's own tool wrote as text. Counted and named rather than read as a
                # failing comparison: those are two answers, and silently merging them is
                # the failure indistinguishable from success this module exists against.
                read.unparsed.append(f"{where}:{lineno}")
            elif admitted:
                read.sites.append(Site(file=where, lineno=lineno, text=line))
    return read
