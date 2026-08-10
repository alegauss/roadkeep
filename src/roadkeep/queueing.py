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
    "entries",
    "read",
    "render",
    "tokens",
    "typed",
    "without",
]

#: Any heading whose text starts like this holds the queue. A prefix match for
#: :data:`~roadkeep.scoping.HEADING`'s reason: "## Priority", "## Priority queue" and
#: "## Priority (what jumps the id order)" are one list, and which words a project put
#: after the first is not a fact this tool needs.
HEADING = re.compile(r"^priority\b", re.IGNORECASE)

#: What a migration *writes*, which the pattern above deliberately cannot say (RK427): the
#: match is a prefix so a project may title its own section, and one that has none yet gets
#: the plainest spelling rather than a guess at which words it would have chosen.
SECTION = "## Priority"

#: `- <token>`, at column zero and nothing else on the line. Deliberately the whole bullet:
#: an entry is an address, so a trailing note would be prose the renderer cannot reproduce
#: and the round trip is what refuses it (L3).
_BULLET = re.compile(r"^- (?P<token>\S+(?: \S+)?)\s*$")
#: A bullet that is one, without the shape this governs — reported, never guessed at.
_ANY_BULLET = re.compile(r"^[-*+] (?P<rest>.*)$")


class NoQueue(KeyError):
    """No heading holds a queue to write to. A heading is the only thing that declares one.

    ``in_config`` is the case that had no door at all (RK427). RK325 moved the queue out of
    `roadkeep.toml` and into the roadmap, and `lint` still reads the old declaration — which
    is right, a project that has not migrated still has a real order. But it reported
    `priority.shipped` naming **roadkeep.toml**, and the verb whose whole job is that repair
    refused with "no priority heading in docs/ROADMAP.md", having never looked at the file
    the finding named. A finding in one file and its door on another is a defect with no
    exit but the hand edit this tool exists to replace, so the refusal names the migration.
    """

    def __init__(self, where: str, tokens: tuple[str, ...] = ()) -> None:
        self.tokens = tokens
        if tokens:
            listed = ", ".join(tokens)
            super().__init__(
                f"this project's queue is still `priority` in roadkeep.toml ({listed}), "
                f"which no verb writes: `priority migrate` moves it into {where} as the "
                f"section RK325 introduced, and then every queue verb reaches it"
            )
            return
        super().__init__(
            f"no priority heading in {where}, so there is no order to take a token out of: "
            f"`priority add <token>` opens the section and writes the first entry (RK1014)"
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
    #: Whether this write also opened the section (RK1014). Reported, because a caller who
    #: asked to queue one token has just had a heading written into a governed file, and a
    #: write nobody sees is the thing the event line exists to stop (RK38).
    opened: bool = False

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
    opened = False
    if heading is None:
        # A queue still in the config is `migrate`'s (RK427): moving it is one act, and
        # opening a second section beside it would be two orders in two files.
        if _in_config(config):
            raise NoQueue(where, _in_config(config))
        # And a project with neither gets the heading written here (RK1014), the way
        # `block add` opens a block heading — the two doors used to name each other and
        # neither wrote it, leaving the hand edit this tool exists to replace.
        document, heading = open_queue(document)
        opened = True
    entry = token.strip()
    if not typed(config, entry):
        raise NotAnEntry(entry, where)

    held = read(document, config)
    twin = entries(document, config)
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
        opened=opened,
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
        raise NoQueue(where, _in_config(config))

    held = entries(document, config)
    going = next((one for one in held if one.token == token.strip()), None)
    if going is None:
        raise NoSuchEntry(
            token.strip(), where, tuple(one.token for one in held)
        )
    return Dropped(
        document=_remove_line(document, going.lineno),
        entry=going,
        length=len(held) - 1,
    )


def without(document: Document, config: Config, token: str) -> tuple[Document, str | None]:
    """The same roadmap with one entry gone, and the token if there was one (RK327).

    A :class:`~roadkeep.document.Document` in, a document out, because every caller is a
    **departure**: `ship`, `retire` and `defer` all rewrite the roadmap inside one atomic
    transaction, and dropping the entry is one more change to a file already in hand. Going
    through :func:`drop` would be a second read of the same file and a second write of it —
    and then a state where the line has left and the queue still names it, which is precisely
    what this closes.

    Silent where nothing is queued, and that is not a fallback: most departures are of work
    nobody put in the order, and a refusal there would make the queue an obstacle at the one
    moment the author is finishing.

    What separates this from `dependents` and `cited`, which the same transaction reports and
    never touches: those are other lines and other prose, and editing them would be composing
    somebody's sentence. **A queue entry is derived dead by the departure itself** — the id it
    names has left the roadmap, so the tier could only ever fire on nothing.
    """
    going = next((one for one in entries(document, config) if one.token == token), None)
    if going is None:
        return document, None
    return _remove_line(document, going.lineno), going.token


def entries(document: Document, config: Config) -> tuple[Entry, ...]:
    """The readable bullets alone, with their lines — what the writers address against.

    Public because the gate reports against a *line* (RK326): :func:`read` answers what the
    order is, and a finding needs where the entry that is dead was written.
    """
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


def _in_config(config: Config) -> tuple[str, ...]:
    """The tokens `roadkeep.toml` still declares, where the roadmap declares no section."""
    return tuple(config.priority)


@dataclass(frozen=True, slots=True)
class Migrated:
    """A config-declared queue written into the roadmap as the section (RK427)."""

    document: Document
    tokens: tuple[str, ...]
    #: The heading's line, 1-based, so the answer names where the section landed.
    lineno: int

    def save(self) -> None:
        self.document.save()


def migrate(config: Config) -> Migrated:
    """Write `roadkeep.toml`'s `priority` into the roadmap as the section RK325 introduced.

    The one door between the two declarations, and it exists because the gate reads the old
    one and every write verb reads the new one — so without it a project that never migrated
    was reported a defect no command could reach.

    **The config line is not deleted**, and that is deliberate rather than a shortcut. Nothing
    in this package writes `roadkeep.toml`: it carries an author's comments and a TOML rewrite
    that preserves them is a parser this tool would have to grow and a dependency it refuses
    to take. What happens instead is already designed — the section wins over the config
    (:func:`declared`), so the order is live the moment this returns, and `lint` reports
    `priority.config` about the line left behind, whose own remedy is the one-line edit the
    guard does not deny because `roadkeep.toml` is not a governed file.

    Refused where the roadmap already declares a section: two orders concatenated is a third
    order nobody wrote, which is the same reason :func:`declared` does not merge them.
    """
    where = config.relative(config.path("roadmap"))
    document = config.document("roadmap")
    if _heading_index(document) is not None:
        raise AlreadyDeclared(where)
    tokens = _in_config(config)
    if not tokens:
        raise NothingToMigrate(where)
    for token in tokens:
        if not typed(config, token):
            raise NotAnEntry(token, _configured(config))

    updated, at = open_queue(document)
    for offset, token in enumerate([render(one) for one in tokens] + [""]):
        updated = updated.insert_line(at + 2 + offset, token)
    return Migrated(document=updated, tokens=tokens, lineno=at + 1)


class AlreadyDeclared(KeyError):
    """The roadmap already holds the section, so there is nothing for a migration to open."""

    def __init__(self, where: str) -> None:
        super().__init__(
            f"{where} already declares a priority section, so the queue is already the one "
            f"every verb writes — take `priority` out of roadkeep.toml, which `lint` reports "
            f"as `priority.config` until you do"
        )


class NothingToMigrate(KeyError):
    """Neither file declares a queue: there is no order to move."""

    def __init__(self, where: str) -> None:
        super().__init__(
            f"roadkeep.toml declares no `priority`, so nothing is waiting to move into "
            f"{where}: `priority add <token>` writes the first entry of a new one"
        )


def _configured(config: Config) -> str:
    return config.relative(config.source) if config.source else "roadkeep.toml"


def _first_block_index(document: Document) -> int:
    """Where the section goes: above the first block heading, which is where it is read.

    The same placement rule `priority add` already assumes and the gate already checks — the
    order is about the work below it, and a queue underneath the blocks is one a reader meets
    after the list it was meant to reorder.
    """
    for at, line in enumerate(document.lines):
        if line.lstrip().startswith("## "):
            return at
    return len(document.lines)


def open_queue(document: Document) -> tuple[Document, int]:
    """Write the heading that declares the queue, above the blocks (RK1014).

    The one writer of :data:`SECTION`, called by `add` when a project has no queue at all and
    by `migrate` when it has one in the config. Before the first block, which is where the
    refusal used to tell a caller to put it by hand — the order is what a reader takes for the
    shape of the plan, and a queue underneath the blocks reads as a seventh block.

    A heading and the blank under it, and nothing else: what goes in the section is the
    caller's, and a section opened with an entry nobody asked for would be this tool writing
    an order (L4).
    """
    at = _first_block_index(document)
    return document.insert_line(at, SECTION).insert_line(at + 1, ""), at


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
