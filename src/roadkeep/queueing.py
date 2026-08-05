"""The queue that outranks the id order, in the file the plan lives in (RK325).

`priority` is the one tier of `pick` a project **declares** rather than derives (RK11), and
until now it lived in `roadkeep.toml` — where :func:`~roadkeep.guarding.governed` is explicit
that nothing governs it: the config is "the per-project declaration, which a human edits by
hand on purpose". That is right about the prefix, the paths and the limits. None of them
stops being true by itself.

The queue is the exception, because **every token in it names work, and work leaves**. An id
that shipped is an entry the tool wrote the ledger for and then left standing in a file it
does not open; a block that emptied is a tier that fires on nothing. Every other list this
format holds — task lines, ledger entries, non-goals — has an insert and a drop, and the one
that outranks the id order had neither, so its only repair was the editor the guard denies.

So it moves to where the plan is, and RK70 is the **pattern** rather than a precedent: a list
that is not task lines, one renderer, refused at insertion, addressed by a verb. `picking`'s
standing objection to a `## Priority` section is about *interpreting prose* — Shio's queue is
a paragraph explaining why reachability comes first — and it does not apply to a section this
tool renders.

Four decisions, each narrower than it could be:

* **No opt-in table.** Non-goals needed one (RK66): both corpora wrote theirs as prose years
  before the schema existed, so a default would report fifteen findings on adoption. Nobody
  has a rendered queue section, so there is nothing to grandfather — **the heading declares
  the list**, exactly as a block heading declares a block (RK37), and a project with no such
  heading has no section and keeps whatever `roadkeep.toml` says.
* **No reason field.** An entry is a token: an id, or `Block X`. Why something jumps the
  queue is the commit that moved it, exactly as `restate` takes none — and a reason in the
  file is a sentence that goes stale one tier below the one nothing was keeping true.
* **No derived annotation.** `- RK14` and not `- RK14 📋 (a symptom)`: the id is the address
  and the roadmap is one file away, so an annotation here is a second thing every write has
  to keep in step for a reader who is already looking at the line above it.
* **The section wins where both exist.** `priority` in the config stays *read*, because Shio
  and Turing may have declared one and a move that silently emptied their queue would be this
  tool changing what `pick` answers without being asked. Which one applied is reported
  (:attr:`Queue.declared_in`), because a queue that quietly came from the other file is the
  failure this module is about.

What the move buys is more than a door, and the three tasks it unblocks are the argument:
`ship` already rewrites the roadmap inside its atomic transaction, so an entry a departure
kills cannot survive it (RK327); the gate reads a file it already reads (RK326); `--fix`
repairs one it already repairs (RK328). A separate store makes each of those a fourth writer.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from roadkeep.config import Config
from roadkeep.document import Document, blank
from roadkeep.schema import Dep, DepKind

__all__ = [
    "HEADING",
    "DuplicateEntry",
    "Dropped",
    "Entry",
    "NoQueue",
    "NoSuchEntry",
    "NotAnEntry",
    "Queue",
    "Written",
    "add",
    "declared",
    "drop",
    "read",
    "render",
    "tokens",
]

#: Any heading whose text starts like this holds the queue. A prefix match for
#: :data:`~roadkeep.scoping.HEADING`'s reason: "## Priority", "## Priority queue" and
#: "## Priority (what jumps the id order)" are one list, and which words a project put
#: after the first is not a fact this tool needs.
HEADING = re.compile(r"^priority\b", re.IGNORECASE)

#: `- <token>`, at column zero and nothing else on the line. Deliberately the whole bullet:
#: an entry is an address, so a trailing note would be prose the renderer cannot reproduce
#: and the round trip is what refuses it (L3).
_BULLET = re.compile(r"^- (?P<token>\S+(?: \S+)?)\s*$")
#: A bullet that is one, without the shape this governs — reported, never guessed at.
_ANY_BULLET = re.compile(r"^[-*+] (?P<rest>.*)$")


class NoQueue(KeyError):
    """No heading holds a queue to write to. A heading is the only thing that declares one."""

    def __init__(self, where: str) -> None:
        super().__init__(
            f"no priority heading in {where}: the heading declares the queue, exactly as a "
            f"block heading declares a block (RK37) — add `## Priority` above the blocks"
        )


class NotAnEntry(ValueError):
    """A token that is neither an id of this project nor `Block X` (RK325).

    The same refusal `[priority]` in the config already makes, from the same typing code, and
    for the reason that one gives: an entry `pick` cannot resolve is a queue the author
    believes is in force and is not.
    """

    def __init__(self, token: str, where: str) -> None:
        self.token = token
        super().__init__(
            f"{token!r} is neither an id of this project nor 'Block X', so nothing in "
            f"{where} can ever be first because of it: a queue is an order over the work "
            f"this backlog holds"
        )


class DuplicateEntry(ValueError):
    """A token the queue already carries. One address, one place in the order."""

    def __init__(self, token: str, where: str, lineno: int) -> None:
        self.token = token
        self.lineno = lineno
        super().__init__(
            f"{where}:{lineno} already queues {token}: an entry is an address, so a second "
            f"one is two answers about where the same work sits in the order"
        )


class NoSuchEntry(KeyError):
    """A token the queue does not carry, at the door that removes one."""

    def __init__(self, token: str, where: str, held: tuple[str, ...]) -> None:
        self.token = token
        known = ", ".join(held) or "nothing"
        super().__init__(f"{where} does not queue {token}: the queue holds {known}")


@dataclass(frozen=True, slots=True)
class Entry:
    """One bullet under the priority heading, as data and as the file spells it."""

    token: str
    #: 1-based. An entry is one line — the renderer writes no wrap, having nothing to wrap.
    lineno: int
    raw: str = ""


@dataclass(frozen=True, slots=True)
class Queue:
    """The order `pick` applies, and which file declared it (RK325).

    Both, because the answer is only checkable with the source: a queue that quietly came
    from `roadkeep.toml` after the author wrote a section is the failure this module exists
    to make visible, and `pick` prints the tier either way.
    """

    tokens: tuple[str, ...] = ()
    #: `"roadmap"` where a heading declares the section, `"config"` where `priority` did,
    #: and `""` where neither — which is not the same as an empty section (RK326's
    #: distinction, made here because the reader is the one place that can see both).
    declared_in: str = ""
    #: The bullets under the heading whose shape the format does not hold, with their line.
    #: Counted apart and never silently dropped, for :func:`~roadkeep.scoping.rejects`'
    #: reason: being unreadable is not being absent, and a count that omitted these would
    #: read as a complete one.
    rejects: tuple[tuple[int, str], ...] = ()

    def __bool__(self) -> bool:
        return bool(self.tokens)


@dataclass(frozen=True, slots=True)
class Written:
    """An entry inserted, and the document it went into. Save writes the roadmap."""

    document: Document
    entry: Entry
    #: Where in the order it landed, 1-based — the field a caller cannot read off the line
    #: number, and the whole point of a list whose order is its content.
    position: int = 1
    #: How long the queue is now, so "3rd of 5" is one answer rather than two calls.
    length: int = 1

    @property
    def lineno(self) -> int:
        return self.entry.lineno

    def save(self) -> None:
        self.document.save()


@dataclass(frozen=True, slots=True)
class Dropped:
    """An entry removed. Save writes the roadmap and nothing else."""

    document: Document
    entry: Entry
    length: int = 0

    @property
    def lineno(self) -> int:
        return self.entry.lineno

    def save(self) -> None:
        self.document.save()


def typed(config: Config, token: str) -> bool:
    """Is this a token a queue may carry — an id of this project, or `Block X`?

    Typed by the code that types a **dep**, so `Block X` cannot come to mean two things
    (RK11's rule, and the one `_check_priority` in `config` already applies). One function,
    called by both the writer and the reader, because a token the write path accepted and the
    gate then failed on is the split L1 exists to prevent.
    """
    schema = config.schema
    kind = schema.classify_dep(Dep(token))
    if kind is DepKind.TASK:
        return bool(schema.id_pattern().match(token))
    return schema.block_of_dep(Dep(token)) is not None


def render(token: str) -> str:
    """The bullet as this format writes it. The only writer of it.

    One line and one token, so there is nothing to fill and nothing to wrap — the shape a
    `prose` width would be about does not exist here.
    """
    return f"- {token.strip()}"


def read(document: Document, config: Config) -> Queue:
    """Every entry under the priority heading, in file order, with what could not be read.

    File order **is** the order: an entry's place in the list is its whole content, so
    nothing here sorts and nothing derives a rank. A bullet the shape does not hold is
    carried as a reject rather than dropped, which is what lets the gate report it against a
    line number and what keeps this count honest.
    """
    start = _heading_index(document)
    if start is None:
        return Queue()
    entries: list[Entry] = []
    rejects: list[tuple[int, str]] = []
    for offset, raw in enumerate(document.lines[start + 1 :], start=start + 2):
        body = raw.rstrip("\r\n")
        if body.startswith("#"):
            break  # the next heading ends the section, whatever its level
        if not _ANY_BULLET.match(body):
            continue
        match = _BULLET.match(body)
        if match is None or not typed(config, match.group("token")):
            rejects.append((offset, body))
            continue
        entries.append(Entry(token=match.group("token"), lineno=offset, raw=body))
    return Queue(
        tokens=tuple(one.token for one in entries),
        declared_in="roadmap",
        rejects=tuple(rejects),
    )


def declared(config: Config) -> Queue:
    """The queue `pick` applies: the roadmap's section, or `roadkeep.toml`'s `priority`.

    **The section wins where both exist**, and the loser is not merged in: two orders
    concatenated is a third order nobody wrote. Which file answered is on the result, because
    a project that wrote a section and is still being ordered by its config has a fact to
    learn and no other way to learn it.

    A heading with no bullets under it is a queue that is **empty**, not one that is absent —
    so it wins over the config too. Declaring the list and then removing every entry is how a
    project turns the tier off, and falling back there would make the last `priority drop`
    silently restore an order the author had just finished dismantling.
    """
    if config.has("roadmap") and config.path("roadmap").is_file():
        found = read(config.document("roadmap"), config)
        if found.declared_in:
            return found
    if config.priority:
        return Queue(tokens=config.priority, declared_in="config")
    return Queue()


def tokens(config: Config) -> tuple[str, ...]:
    """Just the order, for the caller that has no use for where it came from."""
    return declared(config).tokens


def add(
    config: Config, token: str, *, after: str | None = None, first: bool = False
) -> Written:
    """Insert one token into the queue. Validated first, and nothing written on a refusal.

    Appended by default, because a queue grows at the end and the alternative — everything
    new is most urgent — is the order nobody meant. `first` and `after` are the two places
    that are not the end, and they are the reason this is an insert rather than an append:
    moving work up the order is the whole act the config file made unavailable.
    """
    where = config.relative(config.path("roadmap"))
    document = config.document("roadmap")
    heading = _heading_index(document)
    if heading is None:
        raise NoQueue(where)
    entry = token.strip()
    if not typed(config, entry):
        raise NotAnEntry(entry, where)

    held = read(document, config)
    twin = _entries(document, config)
    existing = next((one for one in twin if one.token == entry), None)
    if existing is not None:
        raise DuplicateEntry(entry, where, existing.lineno)
    if after is not None:
        target = next((one for one in twin if one.token == after.strip()), None)
        if target is None:
            raise NoSuchEntry(after.strip(), where, held.tokens)

    at, separate, position = _placement(document, heading, twin, after=after, first=first)
    updated = document
    if separate:
        # The line above is the heading or its prose, and a bullet glued to either reads as
        # part of it — so the blank that separates them is part of this insertion.
        updated = updated.insert_line(at, "")
        at += 1
    updated = updated.insert_line(at, render(entry))
    return Written(
        document=updated,
        entry=Entry(token=entry, lineno=at + 1, raw=render(entry)),
        position=position,
        length=len(twin) + 1,
    )


def drop(config: Config, token: str) -> Dropped:
    """Remove the entry a token addresses. The other half of the door.

    No correction verb between them, and that is the shape of the claim: an entry carries a
    token and nothing else, so there is no field an amend could reach — a token that changed
    is a different entry, and where it sits in the order is a drop and an insert.
    """
    where = config.relative(config.path("roadmap"))
    document = config.document("roadmap")
    if _heading_index(document) is None:
        raise NoQueue(where)

    entries = _entries(document, config)
    going = next((one for one in entries if one.token == token.strip()), None)
    if going is None:
        raise NoSuchEntry(
            token.strip(), where, tuple(one.token for one in entries)
        )
    return Dropped(
        document=_remove_line(document, going.lineno),
        entry=going,
        length=len(entries) - 1,
    )


def _entries(document: Document, config: Config) -> tuple[Entry, ...]:
    """The readable bullets alone, which is what the two writers address against."""
    start = _heading_index(document)
    if start is None:
        return ()
    out: list[Entry] = []
    for offset, raw in enumerate(document.lines[start + 1 :], start=start + 2):
        body = raw.rstrip("\r\n")
        if body.startswith("#"):
            break
        match = _BULLET.match(body)
        if match is not None and typed(config, match.group("token")):
            out.append(Entry(token=match.group("token"), lineno=offset, raw=body))
    return tuple(out)


def _remove_line(document: Document, lineno: int) -> Document:
    """Take the bullet out, and the blank line the removal doubled.

    A queue of one sits between blanks, so removing it leaves a paragraph break the file never
    had — both spellings round-trip, which is exactly why nothing downstream would catch it
    (the care :func:`~roadkeep.scoping._remove_span` takes, one list over).
    """
    start = lineno - 1
    updated = document.remove_line(start)
    lines = updated.lines
    if start > 0 and start < len(lines) and blank(lines[start - 1]) and blank(lines[start]):
        return updated.remove_line(start)
    if start >= len(lines) and start > 0 and blank(lines[start - 1]):
        return updated.remove_line(start - 1)
    return updated


def _heading_index(document: Document) -> int | None:
    """The 0-based index of the priority heading line, or None when there is no section."""
    heading = next((h for h in document.headings if HEADING.match(h.text)), None)
    return None if heading is None else heading.lineno - 1


def _placement(
    document: Document,
    heading: int,
    existing: tuple[Entry, ...],
    *,
    after: str | None,
    first: bool,
) -> tuple[int, bool, int]:
    """Where the bullet goes, whether a blank precedes it, and its 1-based place in the order.

    After the section's *prose* when the list is empty, never straight under the heading, for
    :func:`~roadkeep.scoping._placement`'s reason: a section that opens with a sentence about
    what the queue is for would have that sentence read as a footnote to the first entry.
    """
    if not existing:
        end = len(document.lines)
        for offset, raw in enumerate(document.lines[heading + 1 :], start=heading + 1):
            if raw.lstrip().startswith("#"):
                end = offset
                break
        while end > heading + 1 and blank(document.lines[end - 1]):
            end -= 1
        return end, True, 1
    if first:
        return existing[0].lineno - 1, False, 1
    if after is not None:
        target = next(one for one in existing if one.token == after.strip())
        place = existing.index(target)
        return target.lineno, False, place + 2
    return existing[-1].lineno, False, len(existing) + 1
