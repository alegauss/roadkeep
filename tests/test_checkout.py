"""The fixture that tells a moved tree from a defect, tested rather than trusted (RK263).

A skip is where failures hide, so the thing that decides to skip is the one piece of this
suite that cannot be checked by the tests using it: they pass either way. What is asserted
here is the whole of `conftest.Checkout`'s contract — that an unchanged fact is silent, a
changed one is skipped *and* warned about, and a fact nobody recorded is an error and never a
pass. The drift is fabricated rather than provoked: writing to this repository's own
`__init__.py` mid-suite is the defect, not the fixture for it.
"""

from __future__ import annotations

import pytest

from conftest import HERE, WATCHED, Checkout, _stamp

MODULE = "src/roadkeep/__init__.py"
MANIFEST = ".claude-plugin/plugin.json"


def half_stale() -> Checkout:
    """This tree's real stamps, with one fact recorded wrong — which is what a rewrite during
    the run leaves behind, without needing a rewrite during the run."""
    real = {name: _stamp(HERE / name) for name in WATCHED}
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
    with pytest.raises(AssertionError, match="is not in WATCHED"):
        half_stale().steady("pyproject.toml")


def test_the_watched_set_is_what_states_a_version_twice():
    # RK19's rule read from the other end: these two are the only files that write the number,
    # so they are the only ones a mid-run bump can make a test disagree about.
    assert set(WATCHED) == {MODULE, MANIFEST}
