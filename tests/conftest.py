"""The three things a test cannot get from its own assertion: whether the tree moved under the run
(RK263), whether a cache outlived the test that filled it (RK268), and whether the frontmatter it
read is the frontmatter a loader would (RK331). Each produces a red — or a green — in a file that
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

Six functions in the package are `lru_cache`d, and the suite used to clear them by hand at the
call sites — before *and* after, eleven calls across three files, every one a thing the next
test has to remember. The failure mode is not a wrong assertion: a test raising before its
trailing clear leaves a `tmp_path` pytest has already deleted cached as this machine's launcher,
so the *next* tests fail, in another file, about a path nothing in them mentions.

:data:`VOLATILE` is cleared around every test by an autouse fixture, which is the answer the
rationale said to check rather than assume — and the check moved it off "all six" twice.

Three of the six are pure functions of their arguments or of the code (`_task_re`, `_parsed`,
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
"""

from __future__ import annotations

import subprocess
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
                    f"{name} is not in WATCHED, so nothing recorded it before the import "
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
_AT_START = Checkout({name: _stamp(HERE / name) for name in WATCHED}, _head())


@pytest.fixture(scope="session")
def checkout() -> Checkout:
    """The tree as the run found it — see :class:`Checkout` and :data:`_AT_START`."""
    return _AT_START


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
#: the launcher on disk, the working directory. `engine` is deliberately not one — see above.
VOLATILE = ("invocation", "persisted")


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
