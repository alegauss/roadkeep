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
marker but does not match the grammar becomes a :class:`Reject` with a reason, and so
does one that puts an *undeclared* marker where the marker goes, or **no marker at all**
where a bold id leads (RK43) — otherwise it reads as prose and leaves no trace. That is
the data `audit` (RK10) prints, because a count whose misses are invisible is the failure
mode the grep it replaces already had. Measured: Shio's changelog is 920 bullets and
parsed as 0 entries *and* 0 rejects, the one shape that made the miss silent twice.

The marker slot is also the one part of the grammar a file may not have. Both live
ledgers write `- **T1** — …`, so `[ledger] marker = false` (L6) says the status is the
file's rather than the line's — every entry in it shipped — and there a marker on a line
is the reject instead.
"""

from __future__ import annotations

import functools
import re
from collections.abc import Sequence
from dataclasses import dataclass, replace
from pathlib import Path

from roadkeep.schema import ARROW, EM_DASH, ID_SHAPE, NO_DEPS, Dep, Schema, Task

#: Everything after the marker slot, up to the symptom. `deps` is optional because the
#: ledger has none; the trailing pointer is stripped before this runs (see `_split_ref`).
_TASK_HEAD = r"\*\*(?P<id>[A-Za-z0-9]+)\*\*(?: \(deps: (?P<deps>[^)]*)\))?"
#: The two slots a file may not have (`[ledger]`, RK43 and RK48), composed rather than
#: written out four times: a grammar per combination is four things that drift apart.
_SYMPTOM = rf" \*\*(?P<symptom>.+?)\*\* {EM_DASH} "
_WHY = r"(?P<why>.+)$"


@functools.lru_cache(maxsize=None)
def _task_re(marker: bool, symptom: bool) -> re.Pattern[str]:
    """The task-line grammar for one file's shape, anchored at both ends.

    Cached because it is rebuilt per line otherwise, and the four combinations are the
    whole domain: with a marker or without, with a symptom slot or without.
    """
    status = r"(?P<status>\S+) " if marker else ""
    middle = _SYMPTOM if symptom else f" {EM_DASH} "
    return re.compile(rf"^- {status}{_TASK_HEAD}{middle}{_WHY}")


_HEADING_RE = re.compile(r"^(?P<hashes>#{1,6}) (?P<text>.*)$")
_BULLET_RE = re.compile(r"^(?P<indent>\s*)[-*+] (?P<rest>.*)$")
#: A fenced code block's delimiter, indented or not — a fence inside a list item is (RK53).
_FENCE_RE = re.compile(r"^\s*(?P<marks>`{3,}|~{3,})")
#: A bullet that puts *something* where a marker goes and a bold id after it — how an
#: undeclared marker is caught instead of read as prose (see `_wears_the_marker_slot`).
_MARKER_SLOT_RE = re.compile(r"^\S+ \*\*[A-Za-z0-9]+\*\*")
#: A line that is nothing but pipe-delimited cells, and the `|---|` rule that makes a run
#: of them a table rather than prose that happens to use pipes. Two shapes and no grammar:
#: what is *inside* the cells is deliberately never read (RK98).
_ROW_RE = re.compile(r"^\s*\|.*\|\s*$")
_RULE_RE = re.compile(r"^\s*\|(?:\s*:?-+:?\s*\|)+\s*$")
#: A bullet whose first token *is* the bold id, so the marker slot is empty rather than
#: wrong (see `_leads_with_the_id`). Id-shaped and nothing else: the shape is what tells
#: `- **T1** — …` from `- **Delete** the 3 old files`.
_BOLD_ID_RE = re.compile(rf"^\*\*{ID_SHAPE}\*\*(?=\s|$)")
_POINTER = f" {ARROW} §"


class UnknownBlock(ValueError):
    """A block is declared by a heading and by nothing else (RK37).

    Raised by every write that files something under a block — a task line (RK5) and a
    rationale section (RK9) — because a heading invented by a write puts the text where
    nothing looks for it, and one that is merely missing is a heading the author can add.
    """

    def __init__(
        self, label: str, declared: Sequence[str], where: str = "", word: str = "Block"
    ) -> None:
        self.label = label
        self.declared = tuple(declared)
        known = ", ".join(self.declared) or "none"
        file = f"{where} " if where else ""
        super().__init__(
            f"no heading declares {word} {label} ({file}declares: {known}): a heading "
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
    """A marker-bearing bullet the grammar did not accept, and why.

    ``block`` is the heading it sits under, known at parse time and kept because a
    count reported per block has to report its misses per block too (RK10) — a
    total that is honest and a column that is not is the same failure, narrower.
    """

    raw: str
    lineno: int
    reason: str
    block: str = ""


@dataclass(frozen=True, slots=True)
class Row:
    """A table row under a block heading — a task in a shape this format has no reader for.

    A backlog kept as `| ID | Status | Task |` rows parses as **nothing**: not an entry,
    and not a :class:`Reject` either, because a reject is a bullet that claimed the task
    line's shape and a row never claims it. So the file reads exactly as an empty one does,
    which is the single answer an adoption estimate may not give (RK98).

    Never parsed, only counted. Reading the shape is what tells a table from an empty file;
    reading the cells would be a second line format, and one is what L3 keeps singular.
    """

    raw: str
    lineno: int
    block: str


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
    #: Rows of a Markdown table filed under a block heading (RK98). Read here and nowhere
    #: else, because this is the only reader of a file — and a count taken by a second
    #: scanner would be a second fence state machine to keep in step with this one.
    tabular: tuple[Row, ...] = ()
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
        pipes: list[Row] = []
        block: str | None = None

        fence: str | None = None
        for number, raw in enumerate(lines, start=1):
            body = raw.rstrip("\r\n")
            opened = _FENCE_RE.match(body)
            if opened is not None:
                fence = _fenced(fence, opened.group("marks"))
                continue
            if fence is not None:
                # Inside a fence nothing is a list item and nothing is a heading. A quoted
                # example is what a rationale section is for, and reading it as a task gave
                # the file an id nothing wrote and a line that could not round-trip.
                continue
            heading = _HEADING_RE.match(body)
            if heading:
                label = _block_label(heading.group("text"), schema)
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

            if _ROW_RE.match(body):
                # Collected raw and resolved after the loop: whether a run of pipe lines is
                # a table is decided by a rule row further down, which a single pass over
                # the file cannot know at the line it is looking at.
                pipes.append(Row(raw=body, lineno=number, block=block or ""))
                continue

            outcome = _read_bullet(body, schema, block or "")
            if outcome is None:
                continue
            if isinstance(outcome, str):
                rejects.append(
                    Reject(
                        raw=body, lineno=number, reason=outcome, block=block or ""
                    )
                )
            else:
                entries.append(Entry(task=outcome, raw=body, lineno=number))

        return cls(
            schema=schema,
            lines=lines,
            entries=tuple(entries),
            rejects=tuple(rejects),
            headings=tuple(headings),
            tabular=_tables(pipes),
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
        lines[index] = raw + ending(lines[index])
        return self._reparse(lines)

    def insert_line(self, index: int, raw: str) -> Document:
        """Insert before ``index``; ``len(lines)`` appends."""
        self.ensure_writable()
        lines = list(self.lines)
        # A file whose last line has no ending would otherwise get the new line
        # glued onto it — the exact corruption this module exists to prevent.
        if lines and index >= len(lines) and not ending(lines[-1]):
            lines[-1] += self.newline
        lines.insert(index, raw + self.newline)
        return self._reparse(lines)

    def remove_line(self, index: int) -> Document:
        return self.remove_lines(index, index + 1)

    def remove_lines(self, start: int, stop: int) -> Document:
        """Delete ``[start, stop)`` in one edit — validated once, re-parsed once (RK54).

        One edit and not a loop, because every intermediate state of a loop is validated as
        if it were the finished file: deleting a section whose prose quotes a fenced example
        removes the fence's opening line first, and the quoted task line inside it is then
        briefly outside any fence, parses, and refuses the rest of the deletion.
        """
        self.ensure_writable()
        lines = list(self.lines)
        del lines[start:stop]
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


def ending(line: str) -> str:
    """The line's own terminator, or empty at a file that ends without one.

    Public for the same reason as :func:`blank`: a writer that replaces a line has to put
    back the ending that line had, and a second implementation of this would be the one
    that turns a CRLF file into a mixed one on the first fix (RK16).
    """
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


def _wears_the_marker_slot(rest: str, token: str) -> bool:
    """A bullet whose first token sits where a marker sits and is not one.

    The silent miss :mod:`roadkeep.counting` exists to end: a line written with a
    marker this project does not declare — a ✨ from another repository's set, a ✅
    in the roadmap — matches no marker, so it is read as prose and disappears from
    every count without being rejected either.

    The token must carry no letter or digit, which is what separates it from prose:
    ``- See **RK5** for the design.`` also puts a bold id second, and reporting it
    would make the audit the noise its own symptom names.
    """
    return bool(token) and not any(c.isalnum() for c in token) and bool(
        _MARKER_SLOT_RE.match(rest)
    )


def _leads_with_the_id(rest: str) -> bool:
    """A bullet whose first token *is* the bold id: the slot is empty, not wrong (RK43).

    The wider half of the same silent miss, and the one that was measured: Shio's
    changelog is 920 bullets, and it parsed as **0 entries and 0 rejects** — every line
    writes ``- **SH125** — …`` with no marker at all, so none of them wears the slot
    wrongly, they leave it out, and :func:`_wears_the_marker_slot` declines them because
    the first token carries alphanumerics. Turing's writes 755 of the same.

    Id-shaped and nothing after the bold, which is what keeps this off prose that also
    leads with bold: ``- **Delete** the 3 old files`` carries no digit and
    ``- **SH239**: a benchmark …`` puts a colon where the grammar has a space.
    """
    return bool(_BOLD_ID_RE.match(rest))


def _marker_slot(rest: str, token: str, schema: Schema) -> tuple[bool, str | None]:
    """Whether this bullet claims a task line's shape, and the reason if its slot is not.

    A pair because there are three answers and skipping is one of them: ``(False, None)``
    is prose, ``(True, None)`` is a line to go on parsing, and ``(False, reason)`` is a
    claim whose marker slot is wrong — which is the only one that becomes a
    :class:`Reject`, because rejecting prose is what makes a report unread.

    Which slot is right is a fact about the file, not the format (RK43): where the ledger
    declares no marker the slot is absent, so a bold id leads and a marker is the error.
    """
    if not schema.marker_field:
        if _looks_like_marker(token, schema):
            return False, (
                f"{token} is a status marker, in a file whose lines carry none "
                f"([ledger] marker = false): there the marker is the file's, not the line's"
            )
        return _leads_with_the_id(rest), None
    if _looks_like_marker(token, schema):
        return True, None
    if _wears_the_marker_slot(rest, token):
        declared = " ".join((*schema.markers, schema.shipped_marker))
        return False, (
            f"{token} is not a marker this project declares ({declared}): the line "
            f"reads as prose and no count sees it"
        )
    if _leads_with_the_id(rest):
        # The id is deliberately left out of the reason: a `Reject` already carries the
        # line number, and 755 reasons differing only by an id group into 755 rows of one,
        # which is the report `adopt` (RK18) prints instead of a number worth reading.
        reason = (
            "no marker where the status goes: the slot is empty, so the line reads as "
            "prose and no count sees it"
        )
        if schema.is_ledger:
            # The declaration that makes 920 of these into 920 entries. Said here because
            # this reason is the only place a reader of that file will be looking.
            reason += (
                " — a ledger where every entry shipped declares [ledger] marker = false"
            )
        return False, reason
    return False, None


def _fenced(open_marks: str | None, marks: str) -> str | None:
    """The fence still open after this delimiter line, or None (RK53).

    A fence is closed only by its own character and at least as many of them, so ``` inside
    a ~~~ block is text — which is how a renderer reads it, and the only way a section that
    quotes one fence inside another can be read at all.
    """
    if open_marks is None:
        return marks
    if marks[0] == open_marks[0] and len(marks) >= len(open_marks):
        return None
    return open_marks


def _tables(pipes: Sequence[Row]) -> tuple[Row, ...]:
    """The data rows of every table in the file, from the pipe lines it collected (RK98).

    Split into runs of adjacent lines first, because two tables in one file are two
    questions about where the rule row is, and a run interrupted by prose is two runs.
    """
    out: list[Row] = []
    run: list[Row] = []
    for row in pipes:
        if run and row.lineno != run[-1].lineno + 1:
            out += _below_the_rule(run)
            run = []
        run.append(row)
    out += _below_the_rule(run)
    return tuple(out)


def _below_the_rule(run: Sequence[Row]) -> list[Row]:
    """One run's task rows: what sits under the `|---|`, filed under a block.

    Two filters, and each drops a whole class of false report. **Without a rule row** a run
    of pipes is prose that uses them — a leading `|` is not a table, and counting one would
    make this report name itself. **Outside a block** a table is documentation: the legend
    in a roadmap's preamble is not 6 tasks, and a heading is the only thing that says a line
    is filed work (RK37).
    """
    for index, row in enumerate(run):
        if _RULE_RE.match(row.raw):
            return [below for below in run[index + 1 :] if below.block]
    return []


def _block_label(text: str, schema: Schema) -> str | None:
    """The label a heading declares, under this project's own word (RK75).

    Read from the schema and not from a constant here, so the heading and the dep that
    names it cannot disagree about either the word or the label's shape.
    """
    match = schema.heading_pattern().match(text)
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

    Only a bullet that claims the task line's own shape can be rejected: every other one
    is prose, and reporting the non-goals list as malformed would make the report
    worthless. Which shape that is depends on the file — in a markerless ledger (RK43)
    the claim is a leading bold id, and a marker there is the mistake instead.
    """
    bullet = _BULLET_RE.match(body)
    if not bullet:
        return None
    rest = bullet.group("rest").lstrip()
    claimed, wrong = _marker_slot(rest, rest.split(" ", 1)[0], schema)
    if wrong is not None:
        return wrong
    if not claimed:
        return None
    indent = bullet.group("indent")
    if not body.lstrip().startswith("- "):
        return "bullet must be '- ': a task line is one dash and one space"

    # Judged exactly as it would be at column zero (RK49), and the indentation is carried
    # on the task so `render` puts it back: Shio nests four live tasks under a shipped
    # parent, and rejecting them made 4 ids invisible to every count and to `next-id`.
    head, ref = _split_ref(body[len(indent) :])
    match = _task_re(schema.marker_field, schema.symptom_field).match(head)
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
        # Where the file declares no marker, the status is the file's own: every entry in
        # a ledger that carries none shipped, which is the whole content of the claim.
        status=match.group("status") if schema.marker_field else schema.shipped_marker,
        block=block,
        # Absent where the file has no such slot (RK48): the whole tail is the `why`, and
        # an empty string is what `render` then reproduces by omitting the bold entirely.
        symptom=match.group("symptom") if schema.symptom_field else "",
        why=match.group("why"),
        deps=deps,
        ref=ref,
        indent=indent,
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
    markers = schema.dep_markers
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
        where = "after the marker" if schema.marker_field else "where the line starts"
        return f"no bold **<id>** {where}"
    if schema.deps_field and "(deps:" not in head:
        return "no (deps: …) field"
    if not schema.deps_field and "(deps:" in head:
        return "a deps field, in a file that carries none"
    if f" {EM_DASH} " not in head:
        return f"no ' {EM_DASH} ' between the symptom and the why"
    if head.count("**") < 4:
        return "symptom is not delimited by **"
    return "does not match the task-line grammar"
