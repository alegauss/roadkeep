"""The two answers to a tree that moves under the run, tested rather than trusted (RK263/RK315).

A skip is where failures hide, so the thing that decides to skip is the one piece of this
suite that cannot be checked by the tests using it: they pass either way. What is asserted
here is the whole of `conftest.Checkout`'s contract — that an unchanged fact is silent, a
changed one is skipped *and* warned about, and a fact nobody recorded is an error and never a
pass. The drift is fabricated rather than provoked: writing to this repository's own
`__init__.py` mid-suite is the defect, not the fixture for it.

The `governed` snapshot is the same question answered the other way, so its claims are held
here too: that the copy is the tree byte-for-byte, and that :data:`~conftest.GOVERNED` is the
set `lint` actually reads rather than a list that quietly stopped covering it.
"""

from __future__ import annotations

import pytest

from roadkeep.config import Config
from roadkeep.linting import lint

from conftest import GOVERNED, HERE, RECORDED, WATCHED, Checkout, _stamp

MODULE = "src/roadkeep/__init__.py"
MANIFEST = ".claude-plugin/plugin.json"


def half_stale() -> Checkout:
    """This tree's real stamps, with one fact recorded wrong — which is what a rewrite during
    the run leaves behind, without needing a rewrite during the run."""
    real = {name: _stamp(HERE / name) for name in RECORDED}
    return Checkout({**real, MODULE: (10, 20)}, "1962ac3")


def test_a_tree_that_did_not_move_is_silent(checkout):
    # The real one, against the real tree: the suite's own run is the fixture, and asserting
    # this against fabricated stamps would assert about the fabrication.
    assert checkout.moved(*WATCHED, head=True) == ()


def test_a_rewritten_file_is_skipped_and_named():
    with pytest.warns(UserWarning, match=MODULE):
        with pytest.raises(pytest.skip.Exception, match="says nothing about the code"):
            half_stale().steady(MODULE)


def test_a_moved_head_names_both_commits():
    # Both, because which of the two the assertion was about is the question a bare "HEAD
    # moved" leaves the reader to answer by hand.
    drift = half_stale().moved(head=True)
    assert len(drift) == 1 and drift[0].startswith("HEAD moved from 1962ac3 to ")


def test_only_the_fact_asked_about_is_read():
    # Fact by fact and never the whole fingerprint: a test reading the manifest is not one a
    # write to the package should skip, and a fixture that answered for the tree as a whole
    # would spread every skip to every caller.
    assert half_stale().moved(MANIFEST) == ()


def test_a_fact_nobody_recorded_is_an_error_and_not_a_pass():
    # The one failure mode a skip-shaped answer would hide completely: the file was not
    # fingerprinted before the import this defends, so "it did not move" is not knowable.
    with pytest.raises(AssertionError, match="is not in RECORDED"):
        half_stale().steady("pyproject.toml")


def test_the_watched_set_is_what_states_a_version_twice():
    # RK19's rule read from the other end: these two are the only files that write the number,
    # so they are the only ones a mid-run bump can make a test disagree about. The governed
    # files are stamped beside them and kept a separate name (RK315): what they defend is not
    # an import, so folding the two into one set would put one reason on two facts.
    assert set(WATCHED) == {MODULE, MANIFEST}
    assert set(RECORDED) == {MODULE, MANIFEST, *GOVERNED}


# -- the copy taken at collection (RK315) -------------------------------------


def test_the_snapshot_is_this_tree_byte_for_byte(governed, checkout):
    # Bytes and not text: L3 round-trips on line endings, so a copy that normalised them would
    # be a fixture the tool is right to refuse — and every test reading it would say so about
    # the code instead. The comparison is against the *tree*, so it is the one assertion here
    # that a concurrent ship can invalidate: `steady` is what says so, which is this file's
    # own subject used on itself.
    checkout.steady(*GOVERNED)
    assert (governed / "roadkeep.toml").exists(), "no config is no project to discover"
    for name in GOVERNED:
        source = HERE / name
        if source.exists():
            assert (governed / name).read_bytes() == source.read_bytes(), name


def test_the_governed_set_is_what_the_gate_reads(governed):
    # The index held against reality, the way `tests/test_linting.py` holds agents.md's Layout
    # against `src/roadkeep/`: a governed file added to `roadkeep.toml` and not to GOVERNED is
    # one the snapshot stops carrying, and every test reading it would then be asserting about
    # a file that is not there rather than about a file that moved.
    checked = lint(Config.discover(governed)).checked
    assert set(checked) <= set(GOVERNED), sorted(set(checked) - set(GOVERNED))
