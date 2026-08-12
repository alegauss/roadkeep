"""The six things a test cannot get from its own assertion: whether the tree moved under the run
(RK263), whether the docs it asserts about are the ones the run set out to measure (RK315),
whether the answer it reads back is about the call or about the checkout (RK351), whether a cache
outlived the test that filled it (RK268), whether the frontmatter it read is the frontmatter a
loader would (RK331), and whether a fact it guessed from a file's text is the fact the parser
answers (RK1102). Each produces a red — or a green — in a file that
mentions nothing about the cause, so each is answered here rather than at a call site.

## The tree moved under the run (RK263)

Observed while shipping RK261: one run reported six failures and the same source reported 1940
passed, with one genuine fix between them. Five of the six were not about the code. What ran
beside them was `git worktree add` and `git worktree remove` against this repository, and the
mechanism is not the point — the point is that nothing in the output said so, so a red about a
tree being written was indistinguishable from a red about a defect.

These tests are deliberate and stay. This repository is the format's conformance fixture, and
the version checks are what keep RK153's patch bump honest — moving them to a `tmp_path` copy
would assert about the copy. What they have in common is the shape of the comparison: the
process imported `roadkeep` at collection, and each of them holds that import against the live
tree. So a bump landing mid-run makes the disk right and the constant stale, and the test says
`0.1.236 != 0.1.237` as though a file had been forgotten.

:func:`checkout` is the answer, and its precedent is in the suite already:
`test_this_checkout_reports_the_commit_it_is_at` skips where git cannot place the tree, because
a machine without git is not a defect. A tree being written while the run reads it is the same
kind of not-a-defect. Two rules keep the skip from becoming a place failures hide:

* **Fingerprinted once, at session start, for a declared set** (:data:`WATCHED`). A test asking
  about anything else is an error and not a pass: the skip is only honest about facts that were
  recorded before the import it defends.
* **Loud.** Every skip is a `UserWarning` as well, which `pytest -W error` turns into the
  failure a run that wants to be told asks for — the same contract `test_corpora` states.

## The docs the run set out to measure (RK315)

`checkout` defends an assertion the process anchored at *import*. The other half of this
repository is the format's conformance fixture, and an assertion about that is anchored
nowhere: `test_a_file_that_mixes_anchors_is_not_told_to_switch` read `docs/IMPROVEMENTS.md`
from the live checkout and went red once in three runs of the same commit, with a second
session shipping into that file throughout.

A skip would be the wrong answer here, and the reason is in the shape of the assertion rather
than in the odds. The round-trip property tests read the same tree and survive a concurrent
write because they assert a property of whatever they read. These read the file **more than
once** — a projection against the roadmap it was derived from, a README against the ledger it
restates, every open line against the section it points at — so what breaks is not the
freshness of one read but the agreement between two, and a fixture that skipped would be
skipping the tests that are most worth running.

:func:`_snapshot` is the answer, and it is the one §RK315 named: a copy taken at collection.
Every governed file (:data:`GOVERNED`) is copied byte-for-byte at conftest import, and the
copy is re-stamped afterwards and retaken while anything moved — so what a test reads is one
coherent revision, and a ship landing mid-run changes the tree and not the fixture. That is a
narrower claim than the live tree makes and the honest one: this run measures the revision it
started at.

What needs the *live* tree stays on it, and gets the other answer: :data:`GOVERNED` is stamped
at session start too, so `checkout.steady(*GOVERNED)` is available where a copy cannot serve.
Three do. `lint` resolves the paths its prose names against the project root, so on a copy
holding only the governed files it reports `path.missing` for every `.claude/settings.json` the
ledger mentions — a finding about the fixture. `weigh` and `origin_of` read `git log`, which a
copy does not have. The version checks are `checkout`'s for the original reason: there the
disagreement between the import and the disk **is** the defect.

## The answer is about the call, not about the checkout (RK351)

RK315's shape with a different input. There the fixture was the governed docs; here it is the
package's own source, and what reads it is `_answered`: an MCP refusal carries a note naming
the modules that changed on disk after this process imported them, and that note is part of
the string a test reads back with `text_of`.

So a test asserting on a refusal is asserting on a fact about the *repository*. Reproduced
deliberately: `touch src/roadkeep/cli.py` three seconds into `pytest tests/test_serving.py`
fails a test that passes on a quiet tree, and the diff is the note being added rather than any
field changing. The cost is paid by the one workflow this tool is built for — an agent edits,
runs the suite in the background, keeps editing, and is handed a red that says nothing about
the change.

:func:`_pinned_staleness` is the answer §RK351 named second: the baseline staleness is measured
against is moved to *this test's* setup, so what was already on disk when the test began is what
this process imported, as far as this test can tell. A copy cannot serve here — the modules
under test are the ones that would have to be copied — and the seam is one line rather than the
fifty call sites that read a refusal back.

It is a **narrowing** and never a silencing, which is what keeps it from being a place failures
hide: a module written *during* the test is still ahead of the baseline, so every test that
fabricates one goes on working. :func:`since_import` is how they say so — read live, because a
timestamp captured at module import would be measured against a baseline this fixture has since
moved.

## The frontmatter a loader would read (RK331)

Two files here had frontmatter YAML refuses — a description with a colon in it, which is a plain
scalar no parser accepts — and the loader drops **the whole block** when one line fails, so the
skill shipped with no name and no description and `/ship` with no `allowed-tools`. Nothing went
red: both test files split each line on its first colon, so every assertion about a description
passed against text no session ever read. That is two readers of one file disagreeing, which is
the failure this project exists to remove, and it is a *green* rather than a red — the worst kind.

:func:`frontmatter` is the one reader now. It refuses what YAML refuses, naming the file and the
key, and `tests/test_plugin.py` holds it against a real parser wherever `pyyaml` is installed.

## A cache outlived the test that filled it (RK268)

Eight functions in the package are `lru_cache`d, and the suite used to clear them by hand at the
call sites — before *and* after, eleven calls across three files, every one a thing the next
test has to remember. The failure mode is not a wrong assertion: a test raising before its
trailing clear leaves a `tmp_path` pytest has already deleted cached as this machine's launcher,
so the *next* tests fail, in another file, about a path nothing in them mentions.

:data:`VOLATILE` is cleared around every test by an autouse fixture, which is the answer the
rationale said to check rather than assume — and the check moved it off "all six" twice.

Three of the eight are pure functions of their arguments or of the code (`_task_re`, `_parsed`,
`_root`): a stale entry is never wrong, clearing them per test buys nothing, and two tests
**assert** about their `cache_info`, so an autouse clear would quietly delete a measurement.

`engine` is the fourth, and the reason is correctness rather than speed. Nothing patches what it
reads: the tests that appear to patch it replace the *name*
(`monkeypatch.setattr("roadkeep.provenance.engine", …)`), which leaves the real function's cache
untouched, and its only two inputs are `roadkeep.__file__` and one git call in that directory. So
a stale entry cannot be a lie, and clearing it protects nothing. It is also the one clear with a
price — 65 ms of git per re-derivation, measured — though over the four files that read it most
the difference was inside the run-to-run noise, so the price is not the argument. The argument is
a claim, and the fixture enforces it instead of repeating it: at teardown, a populated `engine`
cache is asked for its home — free, being a hit — and a home that is not the package's fails the
test that left it there, naming this file.

That leaves `invocation` and `persisted`, which read a PATH scan, the launcher on disk and the
working directory, cost 9 ms, and are what every poisoning test actually patches.
`tests/test_caches.py` holds the split as an inventory, so a seventh cache is a decision somebody
makes rather than one nobody notices.

## A fact the parser owns, guessed from the text (RK1102)

**Ask the parser, never the line.** Twice a predicate here has decided something about a governed
file by looking at its characters, and both were green until the one day they were not.

RK1090 asked whether a project has a queue by counting entries, so any empty-queue day reported
this repository as having none — the fact is the heading, and `queueing.opened` answers it.
RK1098 asked whether the backlog has an open line by looking for `- ` at the start of one, and the
roadmap's *non-goals* are bullets too: the fixture written for an emptied backlog answered
"populated" on precisely the state it defends, and the two tests it exists for went red.

Both were written in a process that had already imported the parser. That is what makes it a rule
rather than two fixes: the shape is cheap to write, reads as obviously correct, and fails only
against a file arrangement the author was not picturing — which is every arrangement a corpus has
and this repository does not. `Config.discover(HERE).document(role)` is one line and is never
wrong about what a line *is*.

Reading a governed file's **prose** is a different act and stays allowed: `tests/test_linting.py`
counts `agents.md`'s lines against its budget, and that is an assertion about the text as text.
What is forbidden is deriving structure — is there an open line, a block, a queue, a marker —
from anything but the reader that owns it. `tests/test_invariants.py` holds the narrow half of
that mechanically, over this file, because a shared fixture is where a wrong predicate reaches
furthest.
"""

from __future__ import annotations

import atexit
import shutil
import os
import subprocess
import tempfile
import time
import warnings
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[1]

#: What a test may ask about, relative to the repository root. Every entry is a file the
#: running process read at import and something asserts against on disk: `__init__.py` is the
#: version `roadkeep.__version__` came from, and the manifest is the only second place that
#: number is written (RK19). `pyproject.toml` is not one — it reads the module by AST, so it
#: states no number of its own to disagree.
WATCHED = (
    "src/roadkeep/__init__.py",
    ".claude-plugin/plugin.json",
)

#: This repository's own governed files, which are the format's conformance fixture — the set
#: `lint` reports as `checked`, plus the config that declares it. Written out rather than read
#: off `roadkeep.toml`, because these are stamped and copied before pytest has imported a test
#: module and therefore before the package exists to ask; `tests/test_checkout.py` holds the
#: two against each other, so a seventh governed file is a decision somebody makes rather than
#: one that quietly stops being covered.
GOVERNED = (
    "roadkeep.toml",
    "docs/ROADMAP.md",
    "docs/CHANGELOG.md",
    "docs/IMPROVEMENTS.md",
    "README.md",
    "agents.md",
    ".claude/CLAUDE.md",
)

#: Everything fingerprinted at session start, and therefore everything :meth:`Checkout.steady`
#: will answer about (RK315). Two sets because the reason differs: :data:`WATCHED` is what the
#: process read at *import*, and the governed files are what the run set out to *measure*.
RECORDED = WATCHED + GOVERNED


def _stamp(path: Path) -> tuple[int, int] | None:
    """Size and mtime, which is what a rewrite moves. Not a digest: this is asked once per
    session and again per test, and hashing the tree to answer "did anything write here" is
    paying for a certainty the question does not have anyway."""
    try:
        stat = path.stat()
    except OSError:
        return None
    return (stat.st_size, stat.st_mtime_ns)


def _head() -> str | None:
    """The commit, or `None` where git cannot place the tree — the state
    `test_this_checkout_reports_the_commit_it_is_at` already skips on."""
    try:
        finished = subprocess.run(
            ["git", "-C", str(HERE), "rev-parse", "HEAD"],
            capture_output=True,
            # Named rather than left to the locale, for the reason `test_plugin.py`'s validator
            # measured: `text=True` is cp1252 here. A SHA is ASCII either way, so this is the
            # shape being made consistent and not a failure being fixed.
            encoding="utf-8",
            check=False,
        )
    except OSError:
        return None
    return finished.stdout.strip() or None


class Checkout:
    """The tree as it was when the process imported it, and whether it still is.

    Held by value and never re-read as a whole: `moved` compares the recorded fact against the
    live one at the moment a test asks, so a rewrite that happens between two tests is reported
    to the second and not to the first, which is exactly the resolution the defect has.
    """

    def __init__(self, stamps: dict[str, tuple[int, int] | None], head: str | None) -> None:
        self.stamps = stamps
        self.head = head

    def moved(self, *paths: str, head: bool = False) -> tuple[str, ...]:
        """Which of the named facts are not what the session started with."""
        drift = []
        for name in paths:
            if name not in self.stamps:
                raise AssertionError(
                    f"{name} is not in RECORDED, so nothing stamped it before the assertion "
                    f"this would defend: add it there or assert without this fixture"
                )
            now = _stamp(HERE / name)
            if now != self.stamps[name]:
                drift.append(f"{name} was rewritten during this run")
        if head and (now_head := _head()) != self.head:
            drift.append(f"HEAD moved from {self.head} to {now_head}")
        return tuple(drift)

    def steady(self, *paths: str, head: bool = False) -> None:
        """Skip — loudly — where the tree moved under the assertion about to be made."""
        drift = self.moved(*paths, head=head)
        if not drift:
            return
        reason = (
            f"the tree moved while this run read it ({'; '.join(drift)}): the process "
            f"imported one revision and the assertion is about another, so this says "
            f"nothing about the code"
        )
        warnings.warn(reason, UserWarning, stacklevel=2)
        pytest.skip(reason)


#: Read at conftest import, which is before pytest imports a test module and therefore before
#: the process imports `roadkeep` — the anchor the whole fixture is about. A session-scoped
#: fixture body would run at the *first test that asks*, which is late enough for a bump landing
#: between collection and that test to be recorded as the starting state and then never reported.
_AT_START = Checkout({name: _stamp(HERE / name) for name in RECORDED}, _head())


@pytest.fixture(scope="session")
def checkout() -> Checkout:
    """The tree as the run found it — see :class:`Checkout` and :data:`_AT_START`."""
    return _AT_START


# -- the docs the run set out to measure (RK315) ------------------------------


def _copy(into: Path) -> None:
    """The governed files, byte-for-byte, under the same relative layout.

    Bytes and not text: line endings are what L3 round-trips on, so a copy that normalised
    them would be a fixture the tool is right to refuse and the tests would say so.
    """
    for name in GOVERNED:
        source = HERE / name
        if not source.exists():
            continue
        target = into / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())


def _snapshot() -> tuple[Path | None, str]:
    """One coherent revision of the governed files, or a reason there is none.

    Stamped before and after, and retaken while anything moved: a copy is several reads, and a
    ship writes the ledger and the roadmap in one transaction but not in one syscall — so a
    copy taken across it would hold an id in two files and fail `lint` about a state that never
    existed on disk. Three attempts, because a session shipping a task cannot keep a checkout
    moving for three of them; a tree that never settles is reported and never quietly used.
    """
    root = Path(tempfile.mkdtemp(prefix="roadkeep-governed-"))
    atexit.register(shutil.rmtree, root, True)
    for _ in range(3):
        before = {name: _stamp(HERE / name) for name in GOVERNED}
        _copy(root)
        if before == {name: _stamp(HERE / name) for name in GOVERNED}:
            return root, ""
    return None, (
        "this checkout's governed files were rewritten throughout three attempts to copy "
        "them, so there is no one revision to assert about: another session is writing here"
    )


#: Taken at conftest import for the reason :data:`_AT_START` is, and after it: what a test reads
#: has to be the tree the run started at, and a session-scoped fixture body runs at the first
#: test that asks — late enough for a ship to land in between and be copied as the start.
_GOVERNED_AT_START, _UNSETTLED = _snapshot()


@pytest.fixture(scope="session")
def governed() -> Path:
    """A project root holding this repository's governed files as the run found them (RK315).

    `Config.discover` finds `roadkeep.toml` here, so every command reads the copy — which is
    the point: two reads inside one test are two reads of the same revision, whatever a
    concurrent session is doing to the checkout meanwhile.
    """
    if _GOVERNED_AT_START is None:
        warnings.warn(_UNSETTLED, UserWarning, stacklevel=2)
        pytest.skip(_UNSETTLED)
    return _GOVERNED_AT_START


# -- a backlog with something open in it (RK1098) -----------------------------

#: The smallest roadmap that keeps the two properties a real one is read for non-vacuous: two
#: blocks, so grouping is a claim, and a line waiting on another, so blocked-versus-ready is
#: one too. Used only where this repository's own backlog has nothing open in it.
_MINIMAL = (
    "# Roadmap\n\n"
    "## Block A \u2014 The model\n\n"
    "- \U0001f4cb **RK1** (deps: \u2014) **A symptom plainly long enough to read** \u2014 "
    "Because there is a reason for it. \u2192 \u00a7RK1\n"
    "- \U0001f4cb **RK2** (deps: RK1) **A second symptom, waiting on the first** \u2014 "
    "Because it cannot start before RK1 does. \u2192 \u00a7RK2\n\n"
    "## Block B \u2014 Authoring\n\n"
    "- \U0001f4cb **RK3** (deps: \u2014) **A third symptom under a second heading** \u2014 "
    "Because grouping is only a claim where there are two. \u2192 \u00a7RK3\n"
)


@pytest.fixture(scope="session")
def populated(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A root whose backlog has open lines: this checkout's, or a stand-in (RK1098).

    Two tests read `docs/` for what a *client* sees — the editor's tree and the `--json` row
    keys — and both asserted that the read produced something. Shipping the last line of a
    block turned both red, on the state `ship` itself announces as normal: a backlog with
    nothing open is what a finished project looks like, and the suite called it a broken build.

    A skip would have been the easy answer and the wrong one, because the day it fires is the
    day the contract goes unchecked. So the fixture supplies what the assertion needs instead:
    the real files whenever they carry an open line — which keeps this repository the
    conformance fixture it is — and a three-line stand-in when they do not.

    Session-scoped and read once, like :func:`governed`, so every test asking sees one answer.

    **The question is asked of the tool and not of the text.** The first predicate here read
    the file for a line starting with `- `, and the roadmap's *non-goals* are bullets too — so
    it answered "populated" on a backlog with nothing open in it, which is the one day this
    fixture exists for. The same false positive RK1090 made against the same kind of guess.
    """
    from roadkeep.config import Config

    document = Config.discover(HERE).document("roadmap")
    if document.entries:
        return HERE
    root = tmp_path_factory.mktemp("populated")
    (root / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\n', encoding="utf-8"
    )
    (root / "ROADMAP.md").write_text(_MINIMAL, encoding="utf-8", newline="")
    return root


# -- the answer is about the call, not about the checkout (RK351) -------------


@pytest.fixture(autouse=True)
def _pinned_staleness():
    """Every test starts with the package on disk being the package this process imported.

    Autouse for the reason :func:`_volatile_caches` is: an opt-in fixture only helps the tests
    that already remembered, and every test that reads an MCP refusal back is exposed — the one
    that failed was not asserting about staleness at all.

    Set and restored by hand rather than through `monkeypatch`, which is the shape to prefer
    everywhere else and is wrong here. `monkeypatch` is function-scoped and **shared** with the
    test body, so an autouse fixture requesting it makes it set up earlier and therefore undone
    *later* — after `_volatile_caches`' teardown, which is where the invariant keeping `engine`
    out of :data:`VOLATILE` is enforced. `tests/test_caches.py` measured it: the nested run that
    must report an error reported a pass, because `roadkeep.__file__` was still patched when the
    check ran. One global, restored in this fixture's own teardown, moves nobody else's.

    The import inside the body keeps conftest's own import from pulling the package in before
    :data:`_AT_START` has fingerprinted the tree it would be read from.
    """
    from roadkeep import provenance  # noqa: PLC0415 - see above

    was = provenance._LOADED_AT
    provenance._LOADED_AT = time.time()
    yield
    provenance._LOADED_AT = was


def since_import(seconds: float) -> float:
    """A timestamp that far past the baseline staleness is measured from (RK351).

    Read live and never captured at module import, because :func:`_pinned_staleness` moves that
    baseline at every setup: a fixture writing `_LOADED_AT + 300` off the imported constant is
    writing against a clock that has since advanced, and on a long enough run it stops being
    ahead. The tests that fabricate a moved module are the ones this exists for, and they are
    also the ones a pin must not disarm.
    """
    from roadkeep import provenance  # noqa: PLC0415 - RK260

    return provenance._LOADED_AT + seconds


# -- the frontmatter a loader would read (RK331) ------------------------------

#: What a YAML plain scalar may not begin with: a flow collection, an anchor, an alias, a tag, a
#: block scalar, a directive, a comment, a quote — every one of them read as structure and not as
#: the text it looks like. `argument-hint: [block]` is the live case: a one-item *list*.
_INDICATORS = tuple("-?:,[]{}#&*!|>'\"%@`")


def frontmatter(path: Path) -> dict[str, str]:
    """The head of a skill or command file, read as the loader reads it — or refused by name.

    Flat keys only, which is all a skill or a command declares, and quotes are taken off so an
    assertion is about the value and never about how it was spelled. What this does not do is
    accept a plain scalar YAML would reject: the loader's answer to one bad line is to drop the
    whole block and load the file with *empty metadata*, so a test reading past the mistake is a
    test that certifies a surface no session can see (RK331).
    """
    body = path.read_text(encoding="utf-8")
    assert body.startswith("---\n"), f"{path.name}: no frontmatter is nothing to trigger on"
    head = body.split("---\n", 2)[1]
    fields: dict[str, str] = {}
    for line in head.splitlines():
        if not line.strip() or line.startswith(" "):
            continue
        key, separator, value = line.partition(":")
        assert separator, f"{path.name}: {line!r} declares no key"
        fields[key.strip()] = _scalar(path, key.strip(), value.strip())
    return fields


def _scalar(path: Path, key: str, value: str) -> str:
    """One value, quoted or plain — and a plain one held to what a parser will take."""
    for quote in ('"', "'"):
        if len(value) >= 2 and value.startswith(quote) and value.endswith(quote):
            inner = value[1:-1]
            return inner.replace(quote * 2, quote) if quote == "'" else inner
    named = f"{path.name}: `{key}`"
    assert ": " not in value and not value.endswith(":"), (
        f"{named} is a plain scalar with a colon in it, which YAML refuses — and the loader "
        f"drops every field in the block, not the line (RK331). Quote the value."
    )
    assert not value.startswith(_INDICATORS), (
        f"{named} begins with {value[:1]!r}, which YAML reads as structure rather than as text "
        f"(RK331). Quote the value."
    )
    assert " #" not in value, f"{named} carries an unquoted `#`, which starts a comment (RK331)."
    return value


# -- a cache outlived the test that filled it (RK268) ------------------------

#: The `lru_cache`d functions in `roadkeep.provenance` whose value is read off *this machine* and
#: can therefore be a lie the moment a test that patched what they read has ended: a PATH scan,
#: the launcher on disk, the working directory, and — since RK333 — whether a project declares
#: this server itself and what the tree this engine runs out of calls itself, both of which a
#: `tmp_path` outlives. `engine` is deliberately not one — see above.
VOLATILE = ("invocation", "persisted", "_declared_by", "_plugin_name")


@pytest.fixture(autouse=True)
def _volatile_caches():
    """Cleared before and after **every** test, which is the point: an opt-in fixture only helps
    the tests that already remembered, and forgetting is what the defect was.

    Both ends on purpose. The trailing clear is what a raising test skips, so it is the half that
    stops the leak; the leading one is what makes a test's own first derivation the test's, rather
    than whatever an earlier file left behind. The mid-test clears stay at their call sites, where
    they are the assertion — "the patch above changes what this reads" — and not cleanup.

    The imports are inside the body so that conftest's own import does not pull the package in
    before :data:`_AT_START` has fingerprinted the tree it would be read from.
    """
    import roadkeep
    from roadkeep import provenance

    # Resolved at setup, before the test can patch a name away: the objects are what get cleared,
    # so a test that replaced `provenance.invocation` with a lambda still has its cache emptied.
    caches = tuple(getattr(provenance, name) for name in VOLATILE)
    identity = provenance.engine
    for cache in caches:
        cache.cache_clear()
    yield
    for cache in caches:
        cache.cache_clear()
    # The invariant that keeps `engine` out of the set above, and the only cost is a cache hit:
    # an empty cache is nothing to check, and a populated one already paid for its git call.
    if identity.cache_info().currsize:
        home = Path(roadkeep.__file__).resolve().parent
        assert identity().home == home, (
            f"this test left {identity().home} cached as the running engine, which is not "
            f"{home}: `engine` is process-constant and cleared for nothing, so patching what "
            f"it reads means adding it to VOLATILE in tests/conftest.py"
        )


# -- one repository, one author (RK456) ---------------------------------------

#: What identity and configuration a test repository gets, without spending a process on
#: either. Four of the seven `git` calls a fixture used to make bought nothing that this
#: environment does not: identity is what `user.email` and `user.name` were for, and the two
#: `GIT_CONFIG_*` paths make the fixture independent of whatever this machine declares — a
#: global `commit.gpgsign` or `init.defaultBranch` is a fact these tests used to inherit, so
#: this is hermeticity first and 214 ms → 161 ms per repository second.
GIT_ENVIRONMENT = {
    "GIT_AUTHOR_NAME": "Test",
    "GIT_AUTHOR_EMAIL": "test@example.invalid",
    "GIT_COMMITTER_NAME": "Test",
    "GIT_COMMITTER_EMAIL": "test@example.invalid",
    # A path git can read and will find nothing in, on both platforms this runs on.
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_SYSTEM": os.devnull,
    # Set here rather than passed per call, so a repository built by one helper and read by
    # another agrees with itself about what its first branch is called.
    "GIT_CONFIG_COUNT": "0",
}


def git(root: Path, *args: str) -> str:
    """Run one git command in ``root`` and return its stdout.

    The suite's one runner (RK456). Eleven files each held a copy — `test_history` clones and
    moves files, `test_weighing` only ships — so a change to how a test repository is built
    was a change eleven files had to agree to make, which is the divergence `Schema.render`
    is the only writer of a line to avoid, one layer out.
    """
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
        env={**os.environ, **GIT_ENVIRONMENT},
    )
    return result.stdout


def git_init(root: Path) -> None:
    """One process, where a fixture used to spend four (RK456)."""
    root.mkdir(parents=True, exist_ok=True)
    git(root, "init", "--quiet")


def git_commit(root: Path, message: str) -> str:
    """Stage everything and commit it, returning the sha.

    `-c commit.gpgsign=false` on the one call that commits, rather than a `config` process
    per repository: signing is a property of this call and of nothing else the fixture does.
    """
    git(root, "add", "-A")
    git(root, "-c", "commit.gpgsign=false", "commit", "--quiet", "-m", message)
    return git(root, "rev-parse", "HEAD").strip()


# -- how many workers the run asked for (RK460) -------------------------------


def pytest_xdist_auto_num_workers(config: pytest.Config) -> int:
    """What `-n auto` resolves to here, decided by what the invocation asked for.

    RK457 made the parallel run the default and the full run went 5m07s to 41 s. It charged
    the narrow one, measured straight after on 28 cores:

        one file (13 tests)   -n auto  43.2 s      -n0  1.3 s
        one test              -n auto   5.9 s      -n0  0.8 s

    The multiplier is this suite's own setup rather than xdist's. A worker imports this file
    before it runs anything, and that import fingerprints the checkout and copies the
    governed files (RK263, RK315) — so 28 workers pay it 28 times to run 13 assertions, and
    the loop an agent actually runs (edit a module, run its file, edit again) got thirty-three
    times slower while the run made least often got faster.

    **Decided from the arguments and not from the collection**, which is the question §RK460
    left open: pytest knows the count before it distributes, but xdist asks this before either,
    so a hook that wanted the count could not have it. What is knowable here is what was
    *asked for*, and it answers the same question — a caller who named a file or a node id
    wants that file, and nobody who names one wants twenty-eight processes started for it.

    Zero and not one, which is a measurement rather than a preference: on that file, one
    worker is 1.79 s and none is 0.99 s, the serial time. `auto` means *pick the number*, and
    picking none for a single file is a pick — where one worker would spend a spawn to
    distribute one thing among itself. An explicit `-n 4` is untouched; this hook is only
    ever asked what `auto` resolves to.

    **And a count rather than a kind** (RK462). One file is narrow where six are a pool, and
    where the break-even sits is a thing to measure rather than to reason about — a worker
    costs this suite's own conftest import, so the answer is not obvious in either direction.
    Measured here, serial against one worker per file:

        1 file    0.93 s   1.79 s
        2 files   1.5-2.0  1.9-2.3
        3 files   4.2 s    3.0 s
        6 files   7.9 s    4.8 s
        16 files  68.0 s   11.3 s

    So one thing is spawned for nobody, two is a wash, and past that the pool wins by more
    the more there is. One worker per thing named, capped at the cores there are, which is
    the same rule the no-argument run gets — it names one tree and asks for every core.
    """
    named = [one for one in config.args if _narrow(one)]
    if not named:
        return os.cpu_count() or 1
    return 0 if len(named) < 2 else min(len(named), os.cpu_count() or 1)


def _narrow(argument: str) -> bool:
    """Whether this argument names something smaller than a test tree.

    A node id (`::`) or a file, which is every way a caller says "this one". A directory is
    not narrow: `pytest tests/` is the whole suite spelled out, and `testpaths` makes that
    the default argument anyway.
    """
    return "::" in argument or argument.split("::")[0].endswith(".py")
