"""The carriers of the served prefix, held total against their sites (RK1246).

See `tests/carrying.py` for what the census is and why it is derived rather than listed.
"""

from __future__ import annotations

import pytest

from carrying import CARRIERS, FIELD, SOURCE, carriers, filled_in, unaccounted


def test_every_record_that_carries_the_prefix_is_accounted_for():
    """The population is found in the source, so a fifth carrier is red here until somebody
    says which site fills it — and a *renamed* field empties the population, which does not
    match a table with four rows in it."""
    declared = {one.where for one in CARRIERS}
    found = set(carriers())
    assert declared == found, unaccounted(found, declared)


def test_the_message_names_both_acts_and_asserts_neither():
    """RK1563. The sweep is by name and `served` is two words, so a record reaching for the
    second sense lands here — `budgeting.Noted.served` did, and was told it *carries the
    prefix*, which it did not and could not.

    Held as a message rather than as a shape. Narrowing the sweep to `str` fields would have
    let that collision through in silence, and the red is what made somebody look."""
    said = unaccounted({"budgeting.py:Noted"}, set())
    assert said[f"a field named {FIELD!r}, with no row here"] == ["budgeting.py:Noted"]
    claim = said["a row claims"]
    # Both acts, so the reader decides which their field is rather than being told.
    assert "Add a row" in claim and "rename the field" in claim
    # And no assertion about the field that met it, which is the sentence that was wrong.
    assert "carries the prefix, unaccounted" not in str(said)


def test_the_message_reads_the_two_names_the_census_is_built_on():
    # Composed from `FIELD` and `SOURCE` and never spelled again: a message naming a field
    # this sweep no longer looks for is the drift the derived population exists to avoid.
    claim = unaccounted(set(), set())["a row claims"]
    assert SOURCE in claim and f"`{FIELD}`" in claim


def test_the_population_is_never_empty():
    """The one way a derived census fails silently: a rename leaves nothing to compare, and a
    survey that covers nothing passes exactly like one that covers everything."""
    assert carriers(), f"nothing carries {FIELD!r} — was it renamed?"


def test_every_carrier_is_filled_from_the_one_reader():
    """The stronger half. *Constructed somewhere* would have caught RK479 and nothing else;
    what is asserted is that the named site sets the field from `served_by`, which also
    catches a site filling it from something the answer is not."""
    for carrier in CARRIERS:
        module, record = carrier.where.split(":")
        found = filled_in(module, record)
        assert set(carrier.sites) <= set(found), {
            "record": carrier.where,
            "declared": carrier.sites,
            f"actually fills it from {SOURCE}": found,
        }


def test_no_site_fills_it_and_goes_unnamed():
    """The other direction, and the one that catches a door added beside an existing one:
    `guard` and `_mentioned` both build a `Refusal`, and a third would be a row to write."""
    for carrier in CARRIERS:
        module, record = carrier.where.split(":")
        assert set(filled_in(module, record)) == set(carrier.sites), carrier.where


def test_every_row_says_what_the_message_is():
    """A table a reader cannot act on is a list. What each row buys is knowing what a missing
    site would cost — a session handed a route it cannot call, on the message that blocks it."""
    for carrier in CARRIERS:
        assert carrier.what, carrier.where
        assert carrier.sites, carrier.where


def test_a_carrier_whose_site_stops_reading_the_one_answer_is_caught():
    """Measured against real source rather than trusted. `Finding` is a record `linting.py`
    constructs everywhere and never with this field, so a census reporting a site for it
    would be one reporting a site for anything."""
    assert filled_in("linting.py", "Finding") == ()


def test_a_site_setting_it_from_a_literal_is_not_a_site():
    """The distinction the cheap reading cannot make, which is the whole of what this census
    adds over *the record is constructed somewhere*: the keyword being present is not the
    field being filled from the one reader (RK488)."""
    import ast

    from carrying import _names

    tree = ast.parse("def announce():\n    return Notice(files=(), served='mcp__x__')\n")
    (call,) = [one for one in ast.walk(tree) if isinstance(one, ast.Call)]
    assert _names(call.func, "Notice")
    (keyword,) = [one for one in call.keywords if one.arg == FIELD]
    # Present, and not a call — which is exactly the pair `filled_in` declines to count.
    assert not isinstance(keyword.value, ast.Call)


@pytest.mark.parametrize("carrier", CARRIERS, ids=lambda one: one.where)
def test_every_carrier_defaults_to_having_no_route(carrier):
    """RK1247. `Refusal` defaulted to the bare prefix and the other three to `""`, which is
    RK333's argument — from when the choice was *between two prefixes* — outliving RK447,
    which ended it: a project with neither scope has no tools at all, and naming a route it
    cannot call is worse than naming none.

    Held here rather than in one module, because what makes it a rule is that the four agree:
    a fifth carrier defaulting the other way is this defect arriving again, and the row that
    declares it is already in this table.
    """
    from dataclasses import fields
    from importlib import import_module

    module, record = carrier.where.split(":")
    built = getattr(import_module(f"roadkeep.{module[:-3]}"), record)
    (field,) = [one for one in fields(built) if one.name == FIELD]
    assert field.default == "", carrier.where


@pytest.mark.parametrize("carrier", CARRIERS, ids=lambda one: one.where)
def test_every_row_names_a_module_and_a_class_that_exist(carrier):
    """A table addressing something that has moved is a table that stops being read. The
    population test above catches a *renamed field*; this catches a row whose address the
    package no longer answers to."""
    from importlib import import_module

    module, record = carrier.where.split(":")
    assert hasattr(import_module(f"roadkeep.{module[:-3]}"), record), carrier.where
