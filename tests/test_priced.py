"""Every note this build can say, measured against a state that says it (RK1559).

`tests/pricing.py` holds the states and this holds the properties, which is `test_prevention`'s
split one register over: the register is the deliverable and the rows are its population.

What this is **not** is a ceiling. RK1491 declined one for the note cadence with the argument
that what a limit should be is the reading it had just taken, and seventeen numbers with no
argument behind them would be seventeen limits that move on the next good clause. What is held
is that the population is covered, that every row's state still produces its code, and that the
figure is recomputed rather than remembered.
"""

from __future__ import annotations

import pytest

from pricing import PRICED
from roadkeep.history import git_available
from roadkeep.kernel.schema import width
from roadkeep.remedying import notes

#: The rows whose state is a commit and a diff against it, skipped where git is not on PATH —
#: the same guard `test_unpaired` and `test_baseline` carry, per row rather than per module so
#: the other thirteen still measure on a machine without it.
NEEDS_GIT = frozenset(
    {
        "section.unpaired",
        "task.worked",
        "block.worked",
        "block.emptied",
        "block.reopened",
    }
)


def test_every_note_this_build_can_say_has_a_state_that_says_it():
    """The closure, and the deliverable rather than any one row: a note code added tomorrow
    with nothing that produces it is red here until somebody writes the state — which is what
    twelve of these were, silently, from the day the population became knowable."""
    assert {one.code for one in PRICED} == set(notes())


def test_no_code_is_priced_twice():
    # One state per code, so a total is a sum over the population and not over the rows.
    assert len({one.code for one in PRICED}) == len(PRICED)


@pytest.mark.parametrize("row", PRICED, ids=lambda one: one.code)
def test_the_state_still_produces_the_note_it_was_written_for(row, tmp_path):
    """Every row, run. The width is what falls out; what is asserted is that the sentence
    exists and is one — a note that stopped firing is a fixture describing a gate that moved,
    and the figure taken over it would be a reading of nothing."""
    if row.code in NEEDS_GIT and not git_available():
        pytest.skip("git is not on PATH")
    note = row.measure(tmp_path)
    assert note.message.strip() == note.message
    assert "\n" not in note.message


def test_the_reading_is_recomputed_and_never_remembered(tmp_path):
    """What one project would pay if it met every one of them at once — the figure `cost
    --notes` cannot take, because composing these needs seventeen states and a package that
    invented them would be pricing its own test data as somebody's repository.

    Bounded by nothing on purpose. What this asserts is that the sum is a real measurement:
    every code contributes, and no contribution is zero."""
    if not git_available():
        pytest.skip("git is not on PATH")
    widths = {}
    for index, row in enumerate(PRICED):
        widths[row.code] = width(row.measure(tmp_path / str(index)).message)
    assert set(widths) == set(notes())
    assert all(one > 0 for one in widths.values())
    # The reading recorded at RK1559, as a shape and not as a number: the widest note is the
    # bound a reader on a machine that meets it pays, and it is many times the narrowest —
    # which is the fact a single figure over the cadence would have hidden.
    assert max(widths.values()) > min(widths.values())
