"""The live corpora, read at a revision that cannot move underneath a run (RK105).

L3 is proven over real files, and two live backlogs are what make that more than a
self-test: they supply the dep kinds, the outline scheme, the unmarked ledger and the
sheer scale this repository's own `docs/` never reach. The tests read them where they
live and skip where they are absent, which is what lets CI run the same suite.

What that missed is the third state: **present and changing**. A corpus edited in another
session is read mid-flight, so one run failed on a Shio pointer that resolved to nothing
while the same test passed before the change and on every run after; two others began
skipping in the same window because the file had come to conform. Both were correct
readings of a file that moved, and the defect was that the suite reported them as a
verdict on *this* commit — a red about another repository is a red that gets re-run
instead of read.

So every assertion reads a **pinned revision**. The corpora are git checkouts, so the
bytes at a commit cannot move, which turns a floor that somebody else's progress crossed
into a number that is simply true: `lint --baseline` (RK84) already established that this
tool can read a file as it was at a revision, and :func:`document` is the same read.

Three consequences worth stating, because each is a decision:

* **The corpus's own `roadkeep.toml` is read at the pin too.** Both declare one (L6), and
  a test that spelled `prefix = "SH"` for itself would be a second statement of somebody
  else's format — one that goes stale exactly when they change theirs.
* **A pin that does not resolve is an absent corpus**, not a failure. The junction these
  paths go through is re-pointed per version and a commit can be rewritten; either way
  what is missing is the input, and a missing input skips.
* **The live tree is still read** — in `test_corpora.py`, as an advisory that warns and
  never fails. That read is the one that finds a parser defect in content nobody here
  authored, and it is worth keeping for exactly as long as it is not a verdict.

Updating a pin is a commit of its own: the numbers below it are what that revision holds,
so moving it is re-measuring on purpose rather than absorbing somebody else's afternoon.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import pytest

from roadkeep.config import Config
from roadkeep.document import Document
from roadkeep.history import blob_at, git_available, resolves


@dataclass(frozen=True, slots=True)
class Corpus:
    """One foreign backlog, and the commit these tests are written against."""

    name: str
    root: Path
    #: The pinned revision. Full or short, as long as the repository still knows it.
    rev: str

    def __str__(self) -> str:
        return f"{self.name}@{self.rev}"

    @property
    def where(self) -> Path:
        """The root as the filesystem spells it, junctions followed.

        Both corpora are reached through a junction that is re-pointed per version, and
        `Path.resolve()` follows it — so a path built from the declared root and then
        resolved is no longer *under* that root, which is enough to make `relative_to`
        fail and a blob read come back as a file the tree does not carry. Resolving once,
        here, is what keeps both halves of a read spelling the same directory.
        """
        return self.root.resolve()


#: Shio: block deps, an outline rationale file, and a ledger whose lines carry no marker.
SHIO = Corpus("shio", Path("D:/Git/viglet/shio/latest"), "b9302e8e")
#: Turing: ranges, external deps, `[ids] suffix`, a strategy file and the lettered heading.
TURING = Corpus("turing", Path("D:/Git/viglet/turing/latest"), "f08304fcb1")
BOTH = (SHIO, TURING)


def _root(corpus: Corpus) -> Config:
    """A bare config, which is all :func:`blob_at` reads: where to run git."""
    return Config(root=corpus.where)


@lru_cache(maxsize=None)
def present(corpus: Corpus) -> bool:
    """Is the corpus here *and* does it still know the pin?

    One question, because the two absences are the same absence to a caller: there is no
    input, so there is nothing to assert. Which one it was is in :func:`require`'s reason.
    """
    if not git_available() or not corpus.root.is_dir():
        return False
    return resolves(_root(corpus), corpus.rev)


def require(corpus: Corpus) -> None:
    """Skip unless this corpus can be read at its pin."""
    if not corpus.root.is_dir():
        pytest.skip(f"{corpus.root} is not on this machine")
    if not present(corpus):
        pytest.skip(f"{corpus.root} no longer knows {corpus.rev}: re-pin it and re-measure")


@lru_cache(maxsize=None)
def raw(corpus: Corpus, relative: str) -> str | None:
    """One file's text at the pin, or ``None`` when that tree did not carry it.

    Cached, because a parametrized suite asks for the same blob a dozen times and each
    answer is a subprocess. Decoded here and never through universal newlines: the
    round-trip compares bytes, so a CRLF corpus read as LF would fail the property it is
    the corpus *for*.
    """
    found = blob_at(_root(corpus), corpus.rev, corpus.where / relative)
    return None if found is None else found.decode("utf-8")


@lru_cache(maxsize=None)
def config(corpus: Corpus) -> Config:
    """The corpus's own declaration, as it stood at the pin (L6).

    Read from the file rather than restated here: a test that spelled the prefix and the
    ref scheme for itself would hold somebody else's format to what this repository last
    remembered about it, which is the drift the whole tool exists to stop.
    """
    declared = raw(corpus, "roadkeep.toml")
    if declared is None:
        raise AssertionError(f"{corpus} carries no roadkeep.toml to read a format from")
    return Config.parse(tomllib.loads(declared), root=corpus.where)


def text(corpus: Corpus, role: str) -> str:
    """One governed file's bytes at the pin, for a caller bringing its own schema.

    Two callers want the text rather than the parse: the round-trip compares a rendering
    against the source (L3), and the reject list is proved by reading a file under a schema
    that expects the slot it does not carry — which is a *deliberate* misconfiguration and
    therefore not the one :func:`config` reports.
    """
    settings = config(corpus)
    found = raw(corpus, settings.relative(settings.path(role)))
    if found is None:
        raise AssertionError(f"{corpus} declares a {role} its pinned tree does not carry")
    return found


def document(corpus: Corpus, role: str) -> Document:
    """One governed file at the pin, under the schema that corpus declares for it."""
    settings = config(corpus)
    return Document.parse(text(corpus, role), schema=settings.schema_for(role))


def has(corpus: Corpus, role: str) -> bool:
    """Does the corpus declare this role and carry it at the pin?"""
    settings = config(corpus)
    if not settings.has(role):
        return False
    return raw(corpus, settings.relative(settings.path(role))) is not None


def materialise(corpus: Corpus, role: str, into: Path) -> Path:
    """Write the pinned text into ``into`` and return the path, for an API that takes one.

    `adopt` estimates a *file*, because that is what an adopting project points it at, so
    the pinned bytes need somewhere to be a file. Under `tmp_path` and never in the corpus:
    a suite that wrote into somebody else's checkout would be the defect RK105 names, with
    the arrow reversed.
    """
    settings = config(corpus)
    target = into / Path(settings.relative(settings.path(role))).name
    with target.open("w", encoding="utf-8", newline="") as handle:
        handle.write(text(corpus, role))
    return target


def live(corpus: Corpus, role: str) -> str | None:
    """The working tree's text — the advisory read, and the only one that can move."""
    path = config(corpus).path(role)
    if not path.is_file():
        return None
    with path.open("r", encoding="utf-8", newline="") as handle:
        return handle.read()
