"""Reading a governed file, and the invariant that lets the tool write one (RK2).

A tool that edits a file a human also edits has to prove it understood that file
before it is allowed to replace it, so the ownership test is mechanical: parse →
render → byte-identical, or refuse (L3). Two independent halves of that:

* **The file** round-trips because a :class:`Document` keeps every source line
  verbatim, endings included, and :meth:`Document.render` is a join. Interpretation
  is a layer over the lines, never a replacement for them — so a document can be
  written back untouched even where the parser understood nothing.
* **The line** round-trips only if ``schema.render(parsed) == raw``. Where it does
  not, the entry is *non-canonical* and every mutator refuses the whole file
  (:class:`RoundTripError`) rather than normalizing what it may have misread. A
  formatter that "fixes" what it misunderstood destroys work no diff review catches.

The parser is written to be lossless: every branch either keeps the text in a field
or rejects the line, so no file it accepts comes back changed — 144 lines across
this repository, Shio and Turing, none of them non-canonical. That makes the guard
look redundant until the configuration moves: a file written under one
`roadkeep.toml` and rendered under another (a different marker set, a ledger's
missing deps field) comes back reformatted, and **a configuration change is not a
licence to rewrite the files written before it.** The guard is also what keeps any
future normalizing parser honest, because it fails the corpus instead of a review.

Nothing here silently drops a line it failed to read: a bullet that carries a status
marker but does not match the grammar becomes a :class:`Reject` with a reason, which
is the data `audit` (RK10) exists to print. A count whose misses are invisible is
the failure mode the grep it replaces already had.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass, replace
from pathlib import Path

from roadkeep.schema import ARROW, EM_DASH, NO_DEPS, Dep, Schema, Task

#: A task line, anchored at both ends. `deps` is optional because the ledger has
#: none; the trailing pointer is stripped before this runs (see `_split_ref`).
_TASK_RE = re.compile(
    r"^- (?P<status>\S+) \*\*(?P<id>[A-Za-z0-9]+)\*\*"
    r"(?: \(deps: (?P<deps>[^)]*)\))?"
    rf" \*\*(?P<symptom>.+?)\*\* {EM_DASH} (?P<why>.+)$"
)
_HEADING_RE = re.compile(r"^(?P<hashes>#{1,6}) (?P<text>.*)$")
_BLOCK_LABEL_RE = re.compile(r"^Block (?P<label>[A-Za-z0-9]+)\b")
_BULLET_RE = re.compile(r"^(?P<indent>\s*)[-*+] (?P<rest>.*)$")
_POINTER = f" {ARROW} §"


class UnknownBlock(ValueError):
    """A block is declared by a heading and by nothing else (RK37).

    Raised by every write that files something under a block — a task line (RK5) and a
    rationale section (RK9) — because a heading invented by a write puts the text where
    nothing looks for it, and one that is merely missing is a heading the author can add.
    """

    def __init__(self, label: str, declared: Sequence[str], where: str = "") -> None:
        self.label = label
        self.declared = tuple(declared)
        known = ", ".join(self.declared) or "none"
        file = f"{where} " if where else ""
        super().__init__(
            f"no heading declares Block {label} ({file}declares: {known}): a heading "
            f"invented by a write files the text where nothing looks for it"
        )


class RoundTripError(RuntimeError):
    """The tool may not write a file whose lines it cannot reproduce.

    Refusal is the whole point: the alternative is a rewrite that silently
    normalizes a line the parser misread.
    """

    def __init__(self, offenders: tuple[Entry, ...], path: Path | None = None) -> None:
        self.offenders = offenders
        self.path = path
        where = f"{path}: " if path else ""
        detail = ", ".join(f"{e.task.id} (line {e.lineno})" for e in offenders)
        super().__init__(
            f"{where}{len(offenders)} line(s) do not round-trip and this file will "
            f"not be rewritten: {detail}"
        )


@dataclass(frozen=True, slots=True)
class Entry:
    """A parsed task line, with the provenance needed to refuse or replace it."""

    task: Task
    raw: str
    lineno: int  # 1-based, as an editor counts

    @property
    def index(self) -> int:
        """0-based index into :attr:`Document.lines`."""
        return self.lineno - 1


@dataclass(frozen=True, slots=True)
class Reject:
    """A marker-bearing bullet the grammar did not accept, and why."""

    raw: str
    lineno: int
    reason: str


@dataclass(frozen=True, slots=True)
class Heading:
    """A Markdown heading. ``label`` is set when it names a block."""

    level: int
    text: str
    lineno: int
    label: str | None = None


@dataclass(frozen=True, slots=True)
class Document:
    """A governed Markdown file: verbatim lines, plus what was understood of them."""

    schema: Schema
    lines: tuple[str, ...]  # with their endings, so render() is a join
    entries: tuple[Entry, ...] = ()
    rejects: tuple[Reject, ...] = ()
    headings: tuple[Heading, ...] = ()
    path: Path | None = None

    # -- reading -----------------------------------------------------------

    @classmethod
    def parse(
        cls, text: str, schema: Schema | None = None, path: Path | None = None
    ) -> Document:
        schema = schema or Schema()
        lines = tuple(text.splitlines(keepends=True))
        entries: list[Entry] = []
        rejects: list[Reject] = []
        headings: list[Heading] = []
        block: str | None = None

        for number, raw in enumerate(lines, start=1):
            body = raw.rstrip("\r\n")
            heading = _HEADING_RE.match(body)
            if heading:
                label = _block_label(heading.group("text"))
                headings.append(
                    Heading(
                        level=len(heading.group("hashes")),
                        text=heading.group("text"),
                        lineno=number,
                        label=label,
                    )
                )
                # A non-block heading ends the block it followed: a task under
                # "## Priority queue" belongs to no block, and guessing one would
                # put it in the wrong place on the next write.
                block = label
                continue

            outcome = _read_bullet(body, schema, block or "")
            if outcome is None:
                continue
            if isinstance(outcome, str):
                rejects.append(Reject(raw=body, lineno=number, reason=outcome))
            else:
                entries.append(Entry(task=outcome, raw=body, lineno=number))

        return cls(
            schema=schema,
            lines=lines,
            entries=tuple(entries),
            rejects=tuple(rejects),
            headings=tuple(headings),
            path=path,
        )

    @classmethod
    def load(cls, path: str | Path, schema: Schema | None = None) -> Document:
        path = Path(path)
        # newline="" keeps the file's endings intact; the default would translate
        # CRLF to LF on read and the tool would "own" a file it silently rewrote.
        # (open(), not read_text(newline=…) — that keyword is 3.13+, and this
        # package supports 3.11.)
        with path.open("r", encoding="utf-8", newline="") as handle:
            return cls.parse(handle.read(), schema=schema, path=path)

    def render(self) -> str:
        """The source, exactly. This is what makes L3 a fact rather than a hope."""
        return "".join(self.lines)

    @property
    def newline(self) -> str:
        """The file's dominant ending, so an inserted line matches its neighbours."""
        for line in self.lines:
            if line.endswith("\r\n"):
                return "\r\n"
            if line.endswith("\n"):
                return "\n"
        return "\n"

    def by_id(self) -> dict[str, Entry]:
        """First entry per id. A duplicate id is a lint error (RK14), not a merge."""
        out: dict[str, Entry] = {}
        for entry in self.entries:
            out.setdefault(entry.task.id, entry)
        return out

    def block(self, label: str) -> tuple[Entry, ...]:
        return tuple(e for e in self.entries if e.task.block == label)

    def heading(self, label: str) -> Heading | None:
        """The first heading naming ``label`` — where `add` inserts (RK5)."""
        return next((h for h in self.headings if h.label == label), None)

    # -- the ownership test ------------------------------------------------

    @property
    def non_canonical(self) -> tuple[Entry, ...]:
        """Entries the schema would render differently from how they are written."""
        return tuple(e for e in self.entries if self.schema.render(e.task) != e.raw)

    def ensure_writable(self) -> None:
        offenders = self.non_canonical
        if offenders:
            raise RoundTripError(offenders, self.path)

    # -- writing (every mutator refuses first) -----------------------------

    def replace_line(self, index: int, raw: str) -> Document:
        self.ensure_writable()
        lines = list(self.lines)
        ending = _ending(lines[index])
        lines[index] = raw + ending
        return self._reparse(lines)

    def insert_line(self, index: int, raw: str) -> Document:
        """Insert before ``index``; ``len(lines)`` appends."""
        self.ensure_writable()
        lines = list(self.lines)
        # A file whose last line has no ending would otherwise get the new line
        # glued onto it — the exact corruption this module exists to prevent.
        if lines and index >= len(lines) and not _ending(lines[-1]):
            lines[-1] += self.newline
        lines.insert(index, raw + self.newline)
        return self._reparse(lines)

    def remove_line(self, index: int) -> Document:
        self.ensure_writable()
        lines = list(self.lines)
        del lines[index]
        return self._reparse(lines)

    def replace_task(self, entry: Entry, task: Task) -> Document:
        """Re-render one entry from its data — the only way a task line changes."""
        return self.replace_line(entry.index, self.schema.render(task))

    def save(self, path: str | Path | None = None) -> Path:
        target = Path(path) if path is not None else self.path
        if target is None:
            raise ValueError("no path to save to")
        self.ensure_writable()
        target.write_text(self.render(), encoding="utf-8", newline="")
        return target

    def _reparse(self, lines: list[str]) -> Document:
        # Reparse rather than patch the entry tuples: line numbers shift, and a
        # document that reports stale ones is worse than one that costs a reparse.
        parsed = Document.parse("".join(lines), schema=self.schema, path=self.path)
        return replace(parsed, path=self.path)


def blank(line: str) -> bool:
    """A line with no content — what separates a heading from what belongs to it.

    Public because every writer has to reason about it: a task glued to a heading, or a
    doubled blank left where a line was removed, is a change to the file's shape that
    the round-trip cannot catch because both spellings round-trip.
    """
    return not line.strip()


def _ending(line: str) -> str:
    for candidate in ("\r\n", "\n", "\r"):
        if line.endswith(candidate):
            return candidate
    return ""


def _looks_like_marker(token: str, schema: Schema) -> bool:
    """Is this token *meant* to be a status marker?

    Deliberately looser than the schema: a marker followed by U+FE0F renders
    identically in an editor, so a line carrying one would otherwise be skipped in
    silence — invisible drift, uncounted and unreported. Read it instead, and let
    the round-trip refuse the write and lint name the character.
    """
    stripped = token.rstrip("\ufe0f\u200d")  # variation selector, ZWJ
    return any(
        token == marker or stripped == marker
        for marker in (*schema.markers, schema.shipped_marker)
    )


def _block_label(text: str) -> str | None:
    match = _BLOCK_LABEL_RE.match(text)
    return match.group("label") if match else None


def _split_ref(body: str) -> tuple[str, str | None]:
    """Take the pointer off the end, last occurrence first.

    Matching the pointer with a regex over the whole line would find the one
    RK15's own `why` quotes as an example and truncate the sentence at it.
    """
    head, sep, tail = body.rpartition(_POINTER)
    if sep and tail and not any(c.isspace() for c in tail):
        return head, tail
    return body, None


def _read_bullet(body: str, schema: Schema, block: str) -> Task | str | None:
    """A task, a reason it was rejected, or None when the line is not a task at all.

    Only marker-bearing bullets can be rejected: every other bullet is prose, and
    reporting the non-goals list as malformed would make the report worthless.
    """
    bullet = _BULLET_RE.match(body)
    if not bullet:
        return None
    rest = bullet.group("rest").lstrip()
    if not _looks_like_marker(rest.split(" ", 1)[0], schema):
        return None
    if bullet.group("indent"):
        return "indented: a task line starts at column zero"
    if not body.startswith("- "):
        return "bullet must be '- ': a task line is one dash and one space"

    head, ref = _split_ref(body)
    match = _TASK_RE.match(head)
    if not match:
        return _diagnose(head, schema)

    raw_deps = match.group("deps")
    if schema.deps_field and raw_deps is None:
        return "no (deps: …) field"
    if not schema.deps_field and raw_deps is not None:
        return "a deps field, in a file that carries none"

    deps: tuple[Dep, ...] = ()
    if raw_deps is not None and raw_deps != NO_DEPS:
        deps = read_deps(raw_deps, schema)

    return Task(
        id=match.group("id"),
        status=match.group("status"),
        block=block,
        symptom=match.group("symptom"),
        why=match.group("why"),
        deps=deps,
        ref=ref,
    )


def read_deps(raw: str, schema: Schema) -> tuple[Dep, ...]:
    """Split the field; never reject the line over it.

    Public because `add` (RK5) reads the deps an author types with the same code that
    reads the ones already in the file — a `(deps: …)` field the writer and the reader
    parse differently is a field that stops round-tripping on the next write.

    A dep token the schema will not accept — Shio's ``Block P``, Turing's ``real
    design partners`` — still round-trips, so it is read as an id and reported by
    `lint` as `deps.format`. Rejecting the whole line instead would drop an
    otherwise perfect task out of every count, which is the silent-miss failure
    the reject list exists to prevent.
    """
    markers = (*schema.markers, schema.shipped_marker)
    out: list[Dep] = []
    for token in raw.split(", "):
        head, _, last = token.rpartition(" ")
        if head and last in markers:
            out.append(Dep(head, marker=last))
        else:
            out.append(Dep(token))
    return tuple(out)


def _diagnose(head: str, schema: Schema) -> str:
    """Name the missing piece. A reason is what makes a reject actionable."""
    if not re.search(r"\*\*[A-Za-z0-9]+\*\*", head):
        return "no bold **<id>** after the marker"
    if schema.deps_field and "(deps:" not in head:
        return "no (deps: …) field"
    if not schema.deps_field and "(deps:" in head:
        return "a deps field, in a file that carries none"
    if f" {EM_DASH} " not in head:
        return f"no ' {EM_DASH} ' between the symptom and the why"
    if head.count("**") < 4:
        return "symptom is not delimited by **"
    return "does not match the task-line grammar"
