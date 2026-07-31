"""What a comparable task cost, so granularity is a query and not a feel (RK71).

Sixty-nine shipped tasks here cost between 40 and 1384 lines in the commit that wrote their
ledger entry: median 376, p75 574, p90 826. Nine are above 800 and they are the
architectural ones. The spread is real, nothing in the backlog says it, and a line being
written cannot consult it — so whether a task should be two tasks is decided by feel.

**Derived, never stored.** The commit that added an entry is findable by pickaxe over the
ledger (RK31), so this is a query over git and not a number anybody maintains: it cannot
rot, it costs nothing on the turns nobody asks (L5), and a reader who doubts it can check
it against `git log`. That is also why there is no field on a line — §RK72 carries that
argument, and the non-goal it produced is binding.

**Two axes, because the corpus disagrees about which one is paid.** Lines vary 27-fold;
files, which is what an agent holds in context, vary from 4 to 14. Reporting one would be
choosing the author's axis for them, so both are here and neither is combined into a score.

What this is for: **granularity, at the moment the line is written.** A block whose last
comparables shipped at 800+ lines is a block where the next line is probably two lines.
What it is explicitly not for: **ranking work.** Every tier of `pick` is a fact, and a
cheapness tier would defer exactly the nine tasks above — the ones with the most leverage.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass

from roadkeep.config import Config
from roadkeep.document import Entry
from roadkeep.history import Cost, added_ids, costs_of

#: How many recent comparables a scoped answer names. Three, because the question it serves
#: is "is the next line in this block one task or two", and the fourth is already a trend.
COMPARABLES = 3


@dataclass(frozen=True, slots=True)
class Weight:
    """One shipped task, what it cost, and the commit that says so."""

    task_id: str
    block: str
    lines: int
    files: int
    #: The abbreviated sha, so the number is checkable by hand — the whole claim of a
    #: derived answer is that it can be refuted with `git show`.
    commit: str


@dataclass(frozen=True, slots=True)
class Spread:
    """A distribution over one axis. Empty is a real answer: nothing shipped yet.

    Percentiles rather than a mean: the corpus is 27-fold and the eight architectural tasks
    at the top would pull an average into a number no task ever cost.
    """

    count: int = 0
    low: int = 0
    high: int = 0
    p25: int = 0
    median: int = 0
    p75: int = 0
    p90: int = 0

    @classmethod
    def of(cls, values: tuple[int, ...]) -> Spread:
        if not values:
            return cls()
        ordered = sorted(values)
        return cls(
            count=len(ordered),
            low=ordered[0],
            high=ordered[-1],
            p25=_percentile(ordered, 25),
            median=round(statistics.median(ordered)),
            p75=_percentile(ordered, 75),
            p90=_percentile(ordered, 90),
        )

    def __str__(self) -> str:
        if not self.count:
            return "nothing shipped"
        return (
            f"{self.low}–{self.high}  p25 {self.p25}  median {self.median}  "
            f"p75 {self.p75}  p90 {self.p90}"
        )


@dataclass(frozen=True, slots=True)
class Weights:
    """Every shipped task's cost, and the two distributions it belongs to.

    ``block`` is set when the question was scoped, and then ``lines``/``files`` describe that
    block while ``everywhere`` still describes the ledger: a block median means nothing
    without the one it is being compared against.
    """

    weighed: tuple[Weight, ...] = ()
    lines: Spread = Spread()
    files: Spread = Spread()
    everywhere: Spread = Spread()
    block: str | None = None
    #: Shipped ids whose commit history cannot answer — a squash, a shallow clone, an entry
    #: that never reached a commit. Counted and never guessed at, on RK28's reasoning: an
    #: absent answer is not a cheap task.
    unresolved: tuple[str, ...] = ()

    @property
    def recent(self) -> tuple[Weight, ...]:
        """The last comparables, newest first — what the shipped order already implies."""
        return tuple(reversed(self.weighed[-COMPARABLES:]))

    def by_block(self) -> dict[str, Spread]:
        """The line spread per block, in the order the ledger states them.

        Lines only: the per-block answer is the one a `--block` question refines, and a table
        carrying both axes for every block is the file back rather than an answer (RK29).
        """
        grouped: dict[str, list[int]] = {}
        for weight in self.weighed:
            grouped.setdefault(weight.block, []).append(weight.lines)
        return {label: Spread.of(tuple(values)) for label, values in grouped.items()}


def _percentile(ordered: list[int], at: int) -> int:
    """The value at a percentile, by nearest rank. No interpolation, because every value
    here is a commit somebody can open, and an interpolated 811.4 is nobody's commit."""
    index = max(0, min(len(ordered) - 1, round(at / 100 * (len(ordered) - 1))))
    return ordered[index]


def weigh(config: Config, block: str | None = None) -> Weights:
    """What the ledger's tasks cost, in ledger order, scoped to one block on request.

    Two git calls whatever the size of the ledger: which commit added each id, then how big
    those commits were. Raises :class:`~roadkeep.history.HistoryUnavailable` when git cannot
    answer at all, which the caller reports as an absent answer rather than a zero.
    """
    ledger = config.document("changelog")
    shipped = added_ids(config, "changelog")
    costs = costs_of(config, tuple(dict.fromkeys(shipped.values())))

    every = tuple((entry, _weight(entry, shipped, costs)) for entry in ledger.entries)
    scoped = tuple(
        pair for pair in every if block is None or pair[0].task.block == block
    )
    # In the order they *shipped*, which is what "the last three comparables" means: where a
    # ledger writes its newest entry is a rendering convention, and this repository's own
    # order agreeing with history is exactly why reading position would look correct here.
    order = {task_id: n for n, task_id in enumerate(shipped)}
    weighed = tuple(
        sorted(
            (weight for _, weight in scoped if weight is not None),
            key=lambda weight: order.get(weight.task_id, 0),
        )
    )
    return Weights(
        weighed=weighed,
        lines=Spread.of(tuple(w.lines for w in weighed)),
        files=Spread.of(tuple(w.files for w in weighed)),
        # Always the whole ledger, scoped or not: a block's median says nothing without the
        # number it is being compared against.
        everywhere=Spread.of(tuple(w.lines for _, w in every if w is not None)),
        block=block,
        unresolved=tuple(entry.task.id for entry, weight in scoped if weight is None),
    )


def _weight(
    entry: Entry, shipped: dict[str, str], costs: dict[str, Cost]
) -> Weight | None:
    """One entry as a weight, or None when no commit accounts for it."""
    cost = costs.get(shipped.get(entry.task.id, ""))
    if cost is None:
        return None
    return Weight(
        task_id=entry.task.id,
        block=entry.task.block,
        lines=cost.lines,
        files=cost.files,
        commit=cost.short,
    )
