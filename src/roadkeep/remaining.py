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
"""

from __future__ import annotations

import re
from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field
from pathlib import Path

#: The info string a fenced block carries to be read as a query. Hyphenated rather than
#: `roadkeep:remaining`, because a colon in an info string is how several renderers spell a
#: language attribute and this has to survive being viewed on a forge.
FENCE = "roadkeep-remaining"

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


@dataclass(frozen=True, slots=True)
class Clause:
    """One pathspec and the pattern that marks a site inside it."""

    #: A glob relative to the project root, as `Path.glob` reads one.
    pathspec: str
    #: The pattern, as the author wrote it — kept as text beside the compiled form so the
    #: report can print the query it ran rather than a repr of a compiled object.
    pattern: str
    matcher: re.Pattern[str]

    def __str__(self) -> str:
        return f"{self.pathspec} {SEPARATOR} {self.pattern}"


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
    #: How many files each clause actually read, so a query whose glob names nothing is
    #: distinguishable from one whose pattern no longer matches. Two very different answers
    #: that both count zero, and the second is done while the first is a typo.
    scanned: tuple[int, ...] = ()
    #: Files a clause matched and this could not read as text, by path. Named and never
    #: skipped in silence: a count over a set that quietly lost a member is the defect this
    #: whole module is against.
    unread: tuple[str, ...] = ()

    @property
    def total(self) -> int:
        return len(self.sites)

    @property
    def files(self) -> int:
        return sum(self.scanned)

    def __str__(self) -> str:
        lines = [f"{self.task_id}  {self.total} site(s) left in {self.files} file(s)"]
        for clause, read in zip(self.clauses, self.scanned, strict=False):
            lines.append(f"  query    {clause}  ({read} file(s))")
        for site in self.sites[:SHOWN]:
            lines.append(f"  site     {site}")
        if self.total > SHOWN:
            lines.append(f"  … and {self.total - SHOWN} more")
        if self.unread:
            lines.append(f"  unread   {', '.join(self.unread)}: not text this could search")
        return "\n".join(lines)

    def payload(self) -> dict[str, object]:
        return {
            "id": self.task_id,
            "total": self.total,
            "files": self.files,
            "query": [
                {"pathspec": one.pathspec, "pattern": one.pattern, "files": read}
                for one, read in zip(self.clauses, self.scanned, strict=False)
            ],
            # Every site and not the printed ten: a consumer acting per address needs them
            # all, and the truncation above is about a terminal (RK146).
            "sites": [{"file": s.file, "line": s.lineno, "text": s.text} for s in self.sites],
            "unread": list(self.unread),
        }


def declared(body: str) -> tuple[Clause, ...]:
    """The query a section's prose declares, or `()` where it declares none.

    One fence per section. A second is refused rather than merged: two blocks are two
    claims about what is left, and the sum of them is a number neither paragraph states.
    """
    found: list[Clause] = []
    fences = list(_fenced(body))
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


def _fenced(body: str) -> Iterator[tuple[int, list[str]]]:
    """Each ``` block tagged :data:`FENCE`, as its 0-based start line and its lines."""
    lines = body.splitlines()
    index = 0
    while index < len(lines):
        opening = lines[index].strip()
        if opening.startswith("```") and opening[3:].strip() == FENCE:
            end = index + 1
            while end < len(lines) and not lines[end].strip().startswith("```"):
                end += 1
            yield index, lines[index + 1 : end]
            index = end + 1
            continue
        index += 1


def _clause(lineno: int, line: str) -> Clause:
    pathspec, separator, pattern = line.partition(SEPARATOR)
    if not separator:
        raise QueryError(lineno, f"no {SEPARATOR!r}: a clause is `<pathspec> {SEPARATOR} <regex>`")
    pathspec, pattern = pathspec.strip(), pattern.strip()
    if not pathspec or not pattern:
        raise QueryError(lineno, "both halves are required: a pathspec, and the pattern")
    try:
        matcher = re.compile(pattern)
    except re.error as error:
        raise QueryError(lineno, f"the pattern is not a regex this can compile: {error}") from None
    return Clause(pathspec=pathspec, pattern=pattern, matcher=matcher)


@dataclass(slots=True)
class _Read:
    """One clause's answer, before the clauses are joined."""

    sites: list[Site] = field(default_factory=list)
    scanned: int = 0
    unread: list[str] = field(default_factory=list)


def count(root: Path, task_id: str, clauses: Sequence[Clause]) -> Remaining:
    """Run a declared query against this tree, now.

    Nothing is cached and nothing is written. The whole value of the read is that it is
    taken at the moment somebody asks, which is what a stored count could never be.
    """
    sites: list[Site] = []
    scanned: list[int] = []
    unread: list[str] = []
    for clause in clauses:
        read = _run(root, clause)
        sites += read.sites
        scanned.append(read.scanned)
        unread += read.unread
    return Remaining(
        task_id=task_id,
        clauses=tuple(clauses),
        sites=tuple(sites),
        scanned=tuple(scanned),
        unread=tuple(dict.fromkeys(unread)),
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
            if clause.matcher.search(line):
                read.sites.append(Site(file=where, lineno=lineno, text=line))
    return read
