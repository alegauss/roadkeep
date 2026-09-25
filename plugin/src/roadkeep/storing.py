"""The one grammar for everything this tool keeps outside the documents (RK330).

Three features needed state a governed file cannot hold, and each invented an encoding for
it: `claiming` (RK119) wrote `<id> <epoch>` with tab-separated paths and parsed it by hand,
skipping any line it could not read; `attesting` (RK175) wrote JSON; `locking` (RK117) put
its whole state in a filename. Each was right alone, and the third was the trend — a fourth
feature would have invented a fourth, and no two of them could be held to one property test.

So the two that hold *rows* share this one, and the lock does not: its state is the
existence of a file, which is the one atomic primitive both platforms give (`O_CREAT |
O_EXCL`), and a lock that had to be parsed to be taken would be a lock with a race in it.
What it shares instead is :func:`~roadkeep.locking.sidecar` — one answer to "which checkout
is this", which is what kept a third spelling of it from appearing here.

**Exactly one writer**, which is what makes the grammar cheap. `roadkeep.toml` cannot be
governed because a person wrote its comments and chose its spellings (RK325); a file only
this tool writes has a canonical rendering, so L3's parse-render-compare is a property test
over :func:`render` rather than a negotiation with somebody's formatting. TOML is what that
costs: `tomllib` reads and does not write, and the runtime has zero dependencies on purpose
(`agents.md`), so the renderer below is the price — paid once, for a store several features
share, and not for the queue.

Two boundaries keep it from becoming the database L2 refuses:

* **No fact about a task.** Status, deps and order live in the documents, which is why the
  priority queue went to the roadmap and not here. What this holds is *when* a claim was
  taken, *what* its commit says it owns, and the digest of bytes a verb left — three things
  that are true of a checkout and of no task.
* **Transient stays transient.** It lives in the temp directory beside the lock, keyed by
  the resolved root, and deleting it while nothing is running loses nothing: every claim
  reads as expired and every file as unrecorded, which is the behaviour before any of this
  existed. A committed store is a second decision, and this one does not presume it.

Which is also the answer to the format change itself. A session upgrading across it loses
the dates it was holding, and that is the same loss as a temp directory swept between two
commands — the 🛠 lines are still in the roadmap, and they are offered again as half-done
work. Nothing reads the old spellings, because a reader kept for one release is the second
grammar this exists to remove.

Every failure is silence, on the argument :mod:`roadkeep.guarding` already makes: an
unreadable sidecar loses a date and never a task, so a `pick` is not refused because a temp
file went missing.
"""

from __future__ import annotations

import os
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from roadkeep.locking import sidecar

#: The sidecar's suffix. One file, because the point of the exercise is one door: two files
#: sharing a renderer would still be two things to find, and the writers are already
#: serialised by the same lock (:func:`roadkeep.cli.dispatch`).
SUFFIX = "state"

#: What a rendered store opens with. Not decoration: a person who finds this in a temp
#: directory is deciding whether deleting it costs them anything, and the answer is here
#: rather than in the documentation of a tool they may not have.
HEADER = (
    "# roadkeep transient state for this checkout. Written only by roadkeep; safe to\n"
    "# delete while nothing is running — every claim then reads as expired and every\n"
    "# governed file as unrecorded. Nothing here is a fact about a task (RK330).\n"
)


@dataclass(frozen=True, slots=True)
class Claim:
    """One held line as it is on disk: when it was taken, and what it says it will touch."""

    when: float
    paths: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Store:
    """Everything one checkout keeps outside its documents.

    Two tables and one type, so a third feature extends *this* rather than opening a fourth
    file. Both default empty, because the store is allowed to be missing and a caller that
    had to distinguish "absent" from "empty" would be reading durability into a temp file.
    """

    #: Task id → the claim on it. See :mod:`roadkeep.claiming` for what a date means.
    claims: Mapping[str, Claim] = field(default_factory=dict)
    #: Role → digest of the bytes the last verb left, ``None`` where the file was absent.
    #: Absence is a value: a governed file deleted by a shell command is the change
    #: :mod:`roadkeep.attesting` most wants to state (RK175).
    writes: Mapping[str, str | None] = field(default_factory=dict)


def path(root: Path | str) -> Path:
    """Where this checkout's transient state lives — outside it, keyed by its resolved path."""
    return sidecar(root, SUFFIX)


def read(root: Path | str) -> Store:
    """The store as it is on disk, or an empty one where it cannot be read.

    Unreadable is *empty* and never an error, for the reason the hand-parsed registry had
    the same rule: the file is transient, and refusing to answer a query because a temp file
    is half-written would make the answer depend on the one thing allowed to disappear.
    """
    try:
        raw = path(root).read_text(encoding="utf-8")
    except OSError:
        return Store()
    return parse(raw)


def write(root: Path | str, store: Store) -> None:
    """Replace the store in one step, and never fail the command that was answering.

    Written aside and renamed because the *readers* take no lock — `pick` is a query (RK117)
    — so a reader catching a half-written file would lose the tail of it, which is claims
    read as expired and lines handed out twice. Best-effort: an OSError here loses a date,
    never a task.
    """
    target = path(root)
    staged = target.parent / f"{target.name}.writing"
    try:
        staged.write_text(render(store), encoding="utf-8")
        os.replace(staged, target)
    except OSError:
        pass


def parse(raw: str) -> Store:
    """Read a rendered store back, keeping every row this grammar can type.

    A row it cannot is dropped and never raised, which is :func:`read`'s rule one level
    down: a claim whose date is not a number says nothing about a task, and the file it is
    in is one a caller is allowed to delete.
    """
    try:
        data = tomllib.loads(raw)
    except ValueError:  # TOMLDecodeError is one, and a half-written file is not an error.
        return Store()
    claims: dict[str, Claim] = {}
    for task_id, row in _table(data.get("claims")).items():
        if not isinstance(row, dict) or not isinstance(row.get("when"), (int, float)):
            continue
        paths = row.get("paths", [])
        claims[task_id] = Claim(
            when=float(row["when"]),
            paths=tuple(one for one in paths if isinstance(one, str) and one)
            if isinstance(paths, list)
            else (),
        )
    writes = {
        role: (None if value == ABSENT else value)
        for role, value in _table(data.get("writes")).items()
        if isinstance(value, str)
    }
    return Store(claims=claims, writes=writes)


#: How a file that is not on disk is spelled. TOML has no null and the distinction is load
#: bearing — an omitted role means *never recorded*, which is not a finding, while a
#: recorded absence means a verb watched the file go (RK175). The empty string is free for
#: it: no digest is empty.
ABSENT = ""


def render(store: Store) -> str:
    """The store's one canonical spelling — the thing L3's round-trip is a property of.

    Sorted throughout, so two runs that hold the same rows produce the same bytes and a
    person reading the file finds an id where they left it. Paths keep the order they were
    declared in: that order is what a `git add --` consumes (RK280), so it is data.
    """
    out = [HEADER]
    for task_id, claim in sorted(store.claims.items()):
        out.append(f"\n[claims.{_key(task_id)}]\n")
        out.append(f"when = {claim.when:.6f}\n")
        if claim.paths:
            out.append("paths = [" + ", ".join(_string(p) for p in claim.paths) + "]\n")
    if store.writes:
        out.append("\n[writes]\n")
        for role, digest in sorted(store.writes.items()):
            out.append(f"{_key(role)} = {_string(ABSENT if digest is None else digest)}\n")
    return "".join(out)


def _table(value: object) -> dict[str, object]:
    """One declared table, or nothing — a store whose `claims` is a string holds no claims."""
    return {k: v for k, v in value.items() if isinstance(k, str)} if isinstance(value, dict) else {}


def _key(name: str) -> str:
    """A task id or a role as a TOML key: bare where it can be, quoted where it cannot.

    Ids are `[ids] pattern`'s to shape and roles are the project's to name (L6), so neither
    is this module's to constrain — and a store that refused a key would take a checkout out
    of service over the spelling of a temp file.
    """
    ok = name and all(c.isalnum() and c.isascii() or c in "-_" for c in name)
    return name if ok else _string(name)


def _string(value: str) -> str:
    """A TOML basic string. Enough escaping for a path and a digest, and no more.

    A Windows path carries backslashes and the registry's old grammar used a tab as its
    separator, so both have reached this data; anything else TOML forbids unescaped is a
    typo somebody still gets to read back, rather than a file that stops parsing.
    """
    body = value.replace("\\", "\\\\").replace('"', '\\"')
    return '"' + "".join(_escaped(c) for c in body) + '"'


def _escaped(char: str) -> str:
    """One character as TOML will read it back — control codes and U+007F spelled out."""
    if char in _SHORT:
        return _SHORT[char]
    if char < " " or char == "\x7f":
        return f"\\u{ord(char):04x}"
    return char


_SHORT = {"\n": "\\n", "\r": "\\r", "\t": "\\t", "\b": "\\b", "\f": "\\f"}
