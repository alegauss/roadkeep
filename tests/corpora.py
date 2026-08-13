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

**A pin held by discipline is not held** (RK192). :func:`config` used to parse the pinned
declaration and then root it at the checkout, so `config.document(role)` and `lint(config)`
were ordinary calls that read the file as it is this afternoon — the exact shape RK105 was
written to remove, arriving through the helper written to remove it, and silently, because
the answer looks like a result. So the config a corpus hands out is rooted at a **copy of
the pinned bytes**: nothing reached through it can reach the tree, which is a property
rather than a rule to remember.

That leaves the reads that are pinned by *carrying the revision themselves* — `Tree(…, rev)`
and `tracked_at`, which run git and therefore need the checkout. :func:`checkout` is that
config, named so the one legitimate use of a live root is visible at the call site instead
of indistinguishable from the mistake. The advisory live read (`test_corpora.py`) goes
through :func:`live`, and is the only thing here that is *supposed* to move.
"""

from __future__ import annotations

import atexit
import shutil
import tempfile
import tomllib
from collections.abc import Callable
from dataclasses import dataclass, replace
from functools import lru_cache
from pathlib import Path
from typing import NoReturn

import pytest

from roadkeep.config import Config
from roadkeep.kernel.document import Document
from roadkeep.history import blob_at, git_available, resolves
from roadkeep.linting import Report, lint


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
#: Re-pinned by RK1144 from `b9302e8e`, which the advisory had been naming on every run: 378
#: ledger entries and a roadmap turnover behind, so the shapes this corpus exists to supply
#: were the ones it had two quarters ago.
SHIO = Corpus("shio", Path("D:/Git/viglet/shio/latest"), "9b91a136bc")
#: Turing: ranges, external deps, `[ids] suffix`, a strategy file and the lettered heading.
#: Re-pinned by RK1144 from `f08304fcb1` — 99 entries behind. The path stays the `latest`
#: junction and never the version it resolved to: a pin that does not resolve is an absent
#: corpus and skips, which is the decision this module already made and the reason a re-point
#: costs a skip rather than a red.
TURING = Corpus("turing", Path("D:/Git/viglet/turing/latest"), "2d71c9eac9")
BOTH = (SHIO, TURING)


def _root(corpus: Corpus) -> Config:
    """A bare config, which is all :func:`blob_at` reads: where to run git."""
    return Config(root=corpus.where)


@lru_cache(maxsize=None)
def _materialised(corpus: Corpus) -> Path:
    """The pinned governed files, written once per revision into a directory of our own.

    Under the system temp and removed at exit, never inside the corpus: a suite that wrote
    into somebody else's checkout would be RK105 with the arrow reversed. Written with
    ``newline=""`` because the bytes are the point — a corpus read through newline
    translation would fail the round-trip it is the corpus *for*.
    """
    declared = raw(corpus, "roadkeep.toml")
    if declared is None:
        raise AssertionError(f"{corpus} carries no roadkeep.toml to read a format from")
    into = Path(tempfile.mkdtemp(prefix=f"roadkeep-{corpus.name}-{corpus.rev}-"))
    atexit.register(shutil.rmtree, into, True)
    with (into / "roadkeep.toml").open("w", encoding="utf-8", newline="") as handle:
        handle.write(declared)
    settings = checkout(corpus)
    for role in settings.paths:
        found = raw(corpus, settings.relative(settings.path(role)))
        if found is None:
            # A role the declaration names and the revision does not carry. Left absent, so
            # `missing()` answers here exactly what it answers at the checkout.
            continue
        target = into / settings.relative(settings.path(role))
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8", newline="") as handle:
            handle.write(found)
    return into


def gate(corpus: Corpus) -> Report:
    """The whole gate over this corpus at its pin — every end of every check (RK210).

    :func:`config` copies the governed files and roots a project at the copy, which is what
    makes a read through it unable to reach this afternoon. It also makes the copy the tree,
    and one check does not ask about a file: `path.missing` asks whether the **repository**
    holds an artefact a shipped entry names, so a run through that config reported six
    absent that both corpora carry — three per corpus, every one of them false, and each
    one silent before RK192 only because the root was live.

    A config carries one root and the two ends want different ones, so the answer is not a
    second root: it is `lint(…, at=rev)`, which moves *both* ends to the revision. The
    governed files come from the blob and the tree is the checkout as that commit left it,
    which is the only arrangement where nothing in the report is half about now.
    """
    require(corpus)
    return lint(checkout(corpus), at=corpus.rev)


@lru_cache(maxsize=None)
def checkout(corpus: Corpus) -> Config:
    """The declaration rooted where git can run — for reads that name the revision (RK192).

    `Tree(config, rev)` and `tracked_at(config, rev)` ask git what a revision held, so they
    need the repository and are pinned by the argument they already take. Everything else
    wants :func:`config`, and the two names are what keep those apart: a live root is not a
    mistake here, it is the input, and it should read like one.
    """
    return Config.parse(_declaration(corpus), root=corpus.where)


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


def _declaration(corpus: Corpus) -> dict[str, object]:
    """The corpus's own `roadkeep.toml`, as it stood at the pin (L6).

    Read from the file rather than restated here: a test that spelled the prefix and the
    ref scheme for itself would hold somebody else's format to what this repository last
    remembered about it, which is the drift the whole tool exists to stop.
    """
    declared = raw(corpus, "roadkeep.toml")
    if declared is None:
        raise AssertionError(f"{corpus} carries no roadkeep.toml to read a format from")
    return tomllib.loads(declared)


@lru_cache(maxsize=None)
def config(corpus: Corpus) -> Config:
    """The corpus as a project every one of whose files **is** the pin (RK192).

    The declaration is the corpus's own and the root is a copy of the pinned bytes, so the
    two doors that used to reach this afternoon's tree — `config.document(role)` and
    `lint(config)` — now answer about the revision the test names. Nothing about a caller
    changes; what changes is that being careful is no longer how it holds.

    What it is *not* is a checkout: git cannot run there, no artefact outside the governed
    files exists, and so a check about the repository rather than about a file wants
    :func:`checkout` and the revision it already takes.
    """
    return Config.parse(_declaration(corpus), root=_materialised(corpus))


def text(corpus: Corpus, role: str) -> str:
    """One governed file's bytes at the pin, for a caller bringing its own schema.

    Two callers want the text rather than the parse: the round-trip compares a rendering
    against the source (L3), and the reject list is proved by reading a file under a schema
    that expects the slot it does not carry — which is a *deliberate* misconfiguration and
    therefore not the one :func:`config` reports.
    """
    settings = checkout(corpus)
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
    settings = checkout(corpus)
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
    settings = checkout(corpus)
    target = into / Path(settings.relative(settings.path(role))).name
    with target.open("w", encoding="utf-8", newline="") as handle:
        handle.write(text(corpus, role))
    return target


def live(corpus: Corpus, role: str) -> str | None:
    """The working tree's text — the advisory read, and the only one that can move.

    Through :func:`checkout` and never :func:`config` (RK192): this is the one read whose
    subject *is* the tree, and taking it through the pinned copy would turn the advisory
    that finds parser defects in content nobody here authored into a tautology.
    """
    path = checkout(corpus).path(role)
    if not path.is_file():
        return None
    with path.open("r", encoding="utf-8", newline="") as handle:
        return handle.read()


#: Where a shape that left a live tree is kept, one directory per corpus and revision (RK1145).
#: A frozen excerpt is a **project**: their line, byte for byte, beside a `roadkeep.toml` that
#: declares only what makes it parse — so `Config.discover` reads it the way it reads anything,
#: and nothing here needs a second loader.
FROZEN = Path(__file__).resolve().parent / "frozen"


@dataclass(frozen=True, slots=True)
class Frozen:
    """One shape that outlived the pin that demonstrated it (RK1144, RK1145).

    RK1144 moved both pins and retired coverage while doing it: Shio's block deps and Turing's
    range deps had shipped out of the live trees, so two of the four dep kinds went from *read
    off a real backlog* — RK28's whole argument — to asserted by synthetic fixtures alone. The
    dated citation kept the claim; nothing kept the bytes.

    Bytes and not a reconstruction, which is the only version of this worth having: a line
    written by hand to look like a range dep proves the parser reads what this repository
    imagines, and the corpora exist because that is not the same question.
    """

    corpus: str
    #: The revision the line was read at. In the directory name too, because a second shape
    #: frozen from the same tree at another revision is a second fixture and not an overwrite.
    rev: str
    #: What it is evidence of, for the test that names it and for a reader of the directory.
    shape: str

    @property
    def where(self) -> Path:
        return FROZEN / f"{self.corpus}-{self.rev}"


#: The two RK1144 retired. Declared rather than globbed, so a fixture nobody reads is a row
#: with no test and a test with no row cannot silently stop reading one.
BLOCK_DEP = Frozen("shio", "b9302e8e", "a block dep — `(deps: SH233 ✅, SH182 ✅, Block P)`")
RANGE_DEP = Frozen("turing", "f08304fcb1", "a range dep — `(deps: T451–T457 ✅)`")
FROZEN_SHAPES = (BLOCK_DEP, RANGE_DEP)


def thawed(shape: Frozen) -> Config:
    """The frozen excerpt as a project, read the way every other project is."""
    return Config.discover(shape.where)


#: The revision each pin replaced, kept here because it still resolves (RK1148). Not a second
#: pin anything is measured at — nothing reads it for a number — and that is what answers RK105
#: rather than contradicting it: a **baseline** must not move, the state it holds being the
#: subject of the claim, so it is the one revision nobody re-measures on purpose.
BEFORE = {"shio": "b9302e8e", "turing": "f08304fcb1"}


def retired(
    corpus: Corpus, shape: str, found: Callable[[Corpus], bool], also: str = ""
) -> NoReturn:
    """Skip because a shape is not at this pin, saying whether the pin is what took it.

    Three of the five skips RK1144 left made a **historical** claim — *any more*, *has since*,
    *every one it had has shipped* — and measured against the revisions those pins replaced,
    three of them were false: Shio conformed at `b9302e8e` too, and Turing spelled no lettered
    fourth level at `f08304fcb1` either. RK1146 was filed, worked and shipped on the strength of
    one of them, which is what a clause nobody checks costs.

    So the clause is **derived** rather than written (RK1148). ``found`` is the shape as a
    question about a corpus, asked here at the baseline, and the reason names which of three
    things happened: the pin took it, the shape was gone before either pin, or the baseline no
    longer resolves and nothing can say. A test keeps the sentence it can prove and no other.

    Never a red, deliberately. What a skip reports is an **absent input** — `require`'s rule one
    step along — and a suite going red because somebody else renamed a heading is the arrangement
    RK105 removed. What was wrong was never the skip; it was the history beside it.

    ``also`` is where the coverage went, when it went somewhere: RK1145 froze two shapes, and a
    reader of a skip should not have to discover that the evidence moved rather than ended.
    """
    # So the summary keeps naming the *test* that skipped and not this helper: a report telling
    # a maintainer that `corpora.py` skipped three times is one that cannot be acted on.
    __tracebackhide__ = True
    baseline = replace(corpus, rev=BEFORE[corpus.name])
    if not present(baseline):
        because = f"and {baseline.rev} no longer resolves, so nothing here can say when"
    elif found(baseline):
        because = f"and it was there at {baseline.rev}, which is what the pin took"
    else:
        because = f"and it was not there at {baseline.rev} either, so no pin retired it"
    pytest.skip(f"{corpus} carries no {shape}, {because}{f' ({also})' if also else ''}")
