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
from pathlib import Path
from roadkeep.document import Document
from roadkeep.history import HistoryUnavailable
from roadkeep.cli import main
from roadkeep.config import Config
from roadkeep.linting import lint, within

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


# -- the helper cannot reach the tree it is pinned against (RK192) ------------


@pytest.mark.parametrize("corpus", corpora.BOTH, ids=lambda c: c.name)
def test_a_read_through_the_pinned_config_cannot_reach_the_checkout(corpus):
    """The property that replaces the discipline RK105 left every caller holding.

    `corpora.config` used to root the pinned declaration at the corpus, so
    `config.document(role)` and `lint(config)` were ordinary calls that read this
    afternoon's file — and the answer looked like a result, which is what made the failure
    silent. It was hit while measuring a retirement: five findings that happened to agree
    with the pin and would not have to.

    So the assertion is structural rather than about a number. The root is not inside the
    checkout, which is what makes reaching it impossible instead of merely discouraged, and
    what comes back through the ordinary door is byte for byte what the revision holds.
    """
    corpora.require(corpus)
    settings = corpora.config(corpus)
    assert not settings.root.is_relative_to(corpus.where)
    for role in settings.paths:
        if not corpora.has(corpus, role):
            continue
        assert settings.document(role).render() == corpora.text(corpus, role)


@pytest.mark.parametrize("corpus", corpora.BOTH, ids=lambda c: c.name)
def test_the_gate_run_at_the_pin_asks_the_repository_the_revision_had(corpus):
    """The call that motivated RK192, and the root that motivated RK210.

    `lint(corpora.config(...))` is the natural thing to write, and it was wrong twice over:
    before RK192 it read this afternoon's governed files, and after it read a tree holding
    four files — so `path.missing`, the one check whose subject is the repository, reported
    three artefacts absent per corpus that both of them carry.

    `at` moves both ends to the revision at once, which is the only arrangement where no
    part of the answer is about now. No magnitude is asserted beyond that: a foreign
    backlog's finding count is that project's business, and what this holds is that none of
    them is about a file the pinned tree simply was not given.
    """
    corpora.require(corpus)
    report = corpora.gate(corpus)
    assert report.checked
    missing = [f for f in report.findings if f.code == "path.missing"]
    for finding in missing:
        # Turing's one true finding survives (RK189); what went are the three per corpus
        # that named artefacts sitting in the checkout the copy does not carry.
        assert "emit-model-catalog" in finding.message, str(finding)
    assert len(missing) <= 1


@pytest.mark.parametrize("corpus", corpora.BOTH, ids=lambda c: c.name)
def test_the_copy_is_what_makes_the_repository_check_unanswerable(corpus):
    """Why `gate` exists rather than a second root on the config.

    Stated as the fact it is, so the next reader does not try the config again: the
    materialised tree holds the governed files and nothing else, which is exactly what makes
    a read through it unable to reach the checkout — and exactly what leaves a question
    about the repository with no repository to ask.
    """
    corpora.require(corpus)
    settings = corpora.config(corpus)
    held = {path.name for path in settings.root.rglob("*") if path.is_file()}
    assert held == {"roadkeep.toml"} | {
        Path(settings.relative(settings.path(role))).name
        for role in settings.paths
        if corpora.has(corpus, role)
    }


@pytest.mark.parametrize("corpus", corpora.BOTH, ids=lambda c: c.name)
def test_a_pin_the_repository_forgot_is_refused_rather_than_answered(corpus):
    """`at` cannot degrade to the working tree, for `baseline`'s reason (RK84): a run that
    could not read the revision it names would report this afternoon under that name."""
    corpora.require(corpus)
    with pytest.raises(HistoryUnavailable):
        lint(corpora.checkout(corpus), at="0000000000000000000000000000000000000000")


@pytest.mark.parametrize("corpus", corpora.BOTH, ids=lambda c: c.name)
def test_the_live_root_is_still_reachable_and_still_named(corpus):
    """`checkout` is the door RK192 kept open, because two reads legitimately need it.

    `Tree(config, rev)` and `tracked_at(config, rev)` run git, so they need the repository
    and are pinned by the argument they already carry; the advisory read is the tree on
    purpose. Naming that config is the whole point — a live root that reads like a live
    root is not the mistake, it is the input.
    """
    corpora.require(corpus)
    settings = corpora.checkout(corpus)
    assert settings.root == corpus.where
    for role in ROLES:
        assert settings.path(role).is_relative_to(corpus.where)


# -- what `repair` does to a corpus it did not write (RK473) ------------------


def _repairable(corpus, tmp_path: Path):
    """A **fresh** copy of the pinned tree, because this one is written into.

    `corpora.config` roots a project at a copy shared per revision, which every other test
    here reads; a `repair` over that would leave the corpus somebody else asserts about in a
    state its pin does not describe. So the copy is copied, under `tmp_path`, and thrown away
    with it — the same rule `materialise` states about the checkout, one layer in.
    """
    import shutil

    from roadkeep.config import Config

    corpora.require(corpus)
    into = tmp_path / corpus.name
    shutil.copytree(corpora.config(corpus).root, into)
    return Config.discover(into)


@pytest.mark.parametrize("corpus", corpora.BOTH, ids=lambda c: c.name)
def test_every_repair_this_corpus_dispatches_closes_or_is_never_offered(corpus, tmp_path):
    """The property three defects in a row broke, on the trees that already prove the others.

    RK468 named `block drop` and dispatched `block merge`; RK470 opened the wrong prose file
    on a project declaring two; RK472 dispatched a drop the file refuses and did it again on
    every run. Each was found by running `repair` over a copy of Turing by hand, one per
    sitting, and this holds all three at once.

    The claim is narrow and exact: a remedy this tool *offers to run* has to run. What it
    cannot close it prints (RK422), and that is the other branch — printed, never dispatched.
    """
    from roadkeep.repairing import repair

    config = _repairable(corpus, tmp_path)
    outcome = repair(config, lambda argv: main(["-C", str(config.root), *argv]))
    refused = [step for step in outcome.steps if not step.ok]
    assert not refused, (
        f"{corpus.name}: {len(refused)} remedy(ies) were dispatched and refused — "
        f"{[' '.join(step.argv) for step in refused]}"
    )


@pytest.mark.parametrize("corpus", corpora.BOTH, ids=lambda c: c.name)
def test_a_second_repair_over_this_corpus_finds_nothing_it_left(corpus, tmp_path):
    """`MAX_PASSES` catches a repair that *succeeds* while its finding survives, and says so
    in the right words: a rule and its own remedy disagree. A repair that never succeeds
    walks past that guard, because nothing changed and nothing looped — which is what RK472
    was, and what this holds from the other end."""
    from roadkeep.repairing import repair

    config = _repairable(corpus, tmp_path)
    run = lambda argv: main(["-C", str(config.root), *argv])  # noqa: E731 - one expression
    first = repair(config, run)
    if not first.steps:
        pytest.skip(f"{corpus.name} at {corpus.rev} offers no runnable remedy to repeat")
    again = repair(Config.discover(config.root), run)
    assert not again.steps, (
        f"{corpus.name}: a second run dispatched "
        f"{[' '.join(step.argv) for step in again.steps]}, so the first closed nothing by them"
    )
