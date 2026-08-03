"""The live corpora, read as an advisory and never as a verdict (RK105).

Every *assertion* about a foreign backlog is made at a pin (`corpora.py`), because a red
about another repository's afternoon is a red that gets re-run instead of read. That leaves
the value the live read had: it is the one that meets content nobody here authored, written
after this parser was last changed — a heading shape, a dep spelling, an encoding that no
fixture anticipated. Deleting it would trade a flake for a blind spot.

So the live tree is read here and the outcome is a **warning**. Three consequences:

* `pytest -W error` turns these into failures on purpose, which is what a run that *wants*
  to be told about the corpora asks for. The default run stays green.
* A warning names the corpus, the file and what diverged — enough to re-pin, which is the
  action it is asking for and the only one that makes an assertion out of it.
* Nothing here writes. The corpora are other people's repositories, and a suite that
  wrote into one would be this defect with the arrow reversed.

The pin's own health is the exception: :func:`test_the_pins_are_readable` fails, because a
pin nothing can resolve silently turns every pinned assertion into a skip — and a suite that
tests the corpora by skipping all of them is the failure mode this file exists to avoid.
"""

from __future__ import annotations

import warnings

import pytest

import corpora
from roadkeep.document import Document
from roadkeep.linting import within

#: The roles a corpus is read for. The prose file has no task line to round-trip, so it is
#: read by the section tests at the pin and not here.
ROLES = ("roadmap", "changelog")


def _advise(message: str) -> None:
    """Say it, and let the run stay green — the whole of what advisory means here."""
    warnings.warn(message, UserWarning, stacklevel=2)


@pytest.mark.parametrize("corpus", corpora.BOTH, ids=lambda c: c.name)
def test_the_pins_are_readable(corpus):
    """A pin that resolves to nothing turns every assertion about this corpus into a skip.

    Which is the one thing a suite must not do quietly: `require` skips on a missing corpus
    *and* on an unknown revision, so a stale pin reads exactly like a machine that never had
    the files. Absent is fine; present-but-unpinnable is a pin to move.
    """
    if not corpus.root.is_dir():
        pytest.skip(f"{corpus.root} is not on this machine")
    assert corpora.present(corpus), (
        f"{corpus.root} is here and does not know {corpus.rev}: re-pin it and re-measure "
        f"the numbers the pinned tests state"
    )


@pytest.mark.parametrize("corpus", corpora.BOTH, ids=lambda c: c.name)
def test_the_live_tree_still_round_trips(corpus):
    """L3 over content written since the pin — advisory, because the input is not ours.

    A file that stopped rendering back is either a parser defect or a shape this format has
    not met, and both are worth knowing before the pin moves. Neither is worth a red on a
    commit that touched nothing.
    """
    corpora.require(corpus)
    settings = corpora.config(corpus)
    for role in ROLES:
        source = corpora.live(corpus, role)
        if source is None:
            continue
        document = Document.parse(source, schema=settings.schema_for(role))
        if document.render() != source:
            _advise(
                f"{corpus.name}: the live {role} no longer renders back byte for byte — "
                f"either a shape this parser has not met or a defect in it, and the pin "
                f"({corpus.rev}) is where the assertion still stands"
            )
        if document.non_canonical:
            _advise(
                f"{corpus.name}: {len(document.non_canonical)} live {role} line(s) render "
                f"differently from what the schema spells, first at line "
                f"{document.non_canonical[0].lineno}"
            )


@pytest.mark.parametrize("corpus", corpora.BOTH, ids=lambda c: c.name)
def test_the_live_tree_has_moved_since_the_pin(corpus):
    """What the pin costs, said out loud once per corpus.

    A pin is a decision to stop reading somebody's latest, so the one thing it must not be
    is forgotten: this reports how far behind it has fallen, in the units the pinned tests
    are written in. Every number a pinned test states is re-measured when it moves, which is
    why moving it is a commit and not a convenience.
    """
    corpora.require(corpus)
    settings = corpora.config(corpus)
    drift = []
    for role in ROLES:
        source = corpora.live(corpus, role)
        if source is None:
            continue
        here = len(Document.parse(source, schema=settings.schema_for(role)).entries)
        pinned = len(corpora.document(corpus, role).entries)
        if here != pinned:
            drift.append(f"{role} {pinned} → {here}")
    if drift:
        _advise(
            f"{corpus.name}: the live tree has moved past {corpus.rev} ({', '.join(drift)}) "
            f"— the pinned numbers still hold, and re-pinning re-measures them"
        )


@pytest.mark.parametrize("corpus", corpora.BOTH, ids=lambda c: c.name)
def test_the_gate_reads_the_live_tree_without_throwing(corpus):
    """The gate over foreign content, which is a smoke property and not a magnitude.

    `within` is every check decidable from one file, and what it must never do on a file it
    did not write is raise: a report is actionable and an exception is a bug report about
    this tool. The count belongs to the pinned test; here only the *reason* on each finding
    is asserted, because a finding nobody can act on is the one thing worse than none.
    """
    corpora.require(corpus)
    settings = corpora.config(corpus)
    for role in ROLES:
        source = corpora.live(corpus, role)
        if source is None:
            continue
        document = Document.parse(source, schema=settings.schema_for(role))
        for finding in within(settings, role, document):
            assert finding.message, finding.code
