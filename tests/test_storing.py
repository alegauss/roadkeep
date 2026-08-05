"""One grammar for everything kept outside the documents (RK330).

Three features needed state a governed file cannot hold and each invented an encoding for
it — a hand-parsed line grammar, JSON, and a filename — so the fourth would have invented a
fourth and no two could be held to one property. What is asserted here is what having one
store buys, which is exactly what it has to keep buying:

* **Round-trip, on the store's own terms (L3).** `render` is the one canonical spelling, so
  `parse` of it is the same rows and `render` of *those* is the same bytes. This is the
  property the two hand-written formats could not have — one of them skipped rows it could
  not read, and the other's absence-as-a-value survived only by convention.
* **The tables do not overwrite each other.** One file with two writers is the failure two
  files did not have, and the read-modify-write at each door is what closes it.
* **Transient stays transient.** No fact about a task, outside the repository, and a
  deletion that loses dates rather than work.
"""

from __future__ import annotations

import tomllib

import pytest

from roadkeep import storing
from roadkeep.storing import ABSENT, Claim, Store, parse, path, read, render, write

STORES = [
    Store(),
    Store(claims={"RK2": Claim(1700000000.5)}),
    Store(claims={"RK2": Claim(1700000000.5, ("src/a.py", "docs/ROADMAP.md"))}),
    # Two ids, out of order on the way in: the renderer sorts, so the file a person opens
    # has them where they left them.
    Store(claims={"RK9": Claim(1.0), "RK2": Claim(2.0, ("a",))}),
    Store(writes={"roadmap": "d0", "changelog": None}),
    Store(claims={"RK2": Claim(3.5, ("x/y.py",))}, writes={"roadmap": None}),
    # The characters a path actually carries on the platforms this runs on.
    Store(claims={"RK2": Claim(4.0, ("C:\\Git\\a b\\c.py", 'q"uote', "tab\there"))}),
    # An id no `[ids] pattern` here would mint, because the store does not get to refuse one:
    # the spelling of a key is the project's (L6), and a temp file may not veto a checkout.
    Store(claims={"a.b c": Claim(5.0)}, writes={"a role": "d1"}),
]


@pytest.mark.parametrize("store", STORES)
def test_a_rendered_store_parses_back_to_itself(store):
    assert parse(render(store)) == store


@pytest.mark.parametrize("store", STORES)
def test_rendering_what_was_parsed_is_the_same_bytes(store):
    # The other half of L3: one canonical spelling, so two runs holding the same rows write
    # the same file and a diff of a temp directory means something.
    once = render(store)
    assert render(parse(once)) == once


@pytest.mark.parametrize("store", STORES)
def test_the_rendering_is_toml_a_reader_can_load(store):
    # Not a private format that happens to round-trip: the point of paying for a renderer
    # was that `tomllib` reads it, so a person debugging a checkout has a parser already.
    assert isinstance(tomllib.loads(render(store)), dict)


def test_an_absent_file_is_a_value_and_not_an_omitted_role():
    # RK175's distinction, which TOML has no null for: a role nothing recorded is not a
    # finding, and a governed file a shell command deleted is the change most worth stating.
    back = parse(render(Store(writes={"gone": None, "here": "d0"})))
    assert back.writes == {"gone": None, "here": "d0"}
    assert f'= "{ABSENT}"' in render(Store(writes={"gone": None}))


def test_a_row_the_grammar_cannot_type_is_dropped_and_never_raised():
    # `read`'s rule one level down: the file is transient, so a half-written row loses a
    # date. Refusing to answer `pick` because a temp file is malformed would make the answer
    # depend on the one thing that is allowed to disappear.
    store = parse(
        '[claims.RK2]\nwhen = "yesterday"\n\n[claims.RK9]\nwhen = 1.0\n\n'
        '[writes]\nroadmap = 7\nchangelog = "d0"\n'
    )
    assert set(store.claims) == {"RK9"} and store.writes == {"changelog": "d0"}


def test_a_file_that_is_not_toml_at_all_is_an_empty_store():
    assert parse("not a claim\nRK2 not-a-number\n") == Store()
    assert parse("[claims\n") == Store()


def test_a_table_that_is_not_a_table_holds_nothing():
    assert parse('claims = "none"\nwrites = 3\n') == Store()


def test_reading_a_store_that_was_never_written_is_empty(tmp_path):
    # Deleting it while nothing is running loses nothing: every claim then reads as expired
    # and every governed file as unrecorded, which is the behaviour before any of this.
    assert read(tmp_path) == Store()


def test_a_write_replaces_the_whole_store_in_one_step(tmp_path):
    write(tmp_path, STORES[5])
    assert read(tmp_path) == STORES[5]
    write(tmp_path, Store())
    assert read(tmp_path) == Store()
    # And nothing is left half-written beside it (the readers take no lock).
    assert not list(path(tmp_path).parent.glob(f"{path(tmp_path).name}.writing"))


def test_the_store_lives_outside_the_checkout(tmp_path):
    # A file the tool creates in a project's root is one every adopting project has to add
    # to its `.gitignore` before the first `git status` reads as dirty (RK117).
    write(tmp_path, STORES[1])
    assert tmp_path not in path(tmp_path).parents
    assert path(tmp_path).is_file()
    path(tmp_path).unlink()


def test_two_checkouts_of_one_project_keep_their_own(tmp_path):
    first, second = tmp_path / "one", tmp_path / "two"
    for root in (first, second):
        root.mkdir()
    assert path(first) != path(second)


def test_the_file_says_what_deleting_it_costs(tmp_path):
    # The one reader who finds this is a person in a temp directory deciding whether it is
    # safe to remove, and the answer is in the file rather than in documentation they may
    # not have.
    assert render(Store()).startswith("#")
    assert "safe to" in storing.HEADER and "delete" in storing.HEADER
