"""What a comparable task cost, so granularity is a query and not a feel (RK71).

Sixty-nine shipped tasks here cost between 40 and 1384 lines in the commit that wrote their
ledger entry: median 376, p75 574, p90 826. Nine are above 800 and they are the
architectural ones. The spread is real, nothing in the backlog says it, and a line being
written cannot consult it — so whether a task should be two tasks is decided by feel.

**That reading was taken at 69 entries and is not maintained here** (RK364). `roadkeep
weight` is the current answer, which is the whole argument for deriving it (L5), and a
number restated in prose is one that goes stale while reading as current. What has held
across 359 entries is the *shape* rather than the figures: the tail is the architectural
work, the middle is an ordinary task, and the two are more than an order of magnitude
apart. The middle has more than halved on the way — the tasks got smaller, monotonically,
under one task one commit — and none of the three sentences this module is here to support
depended on where it was.

**Derived, never stored.** The commit that added an entry is findable by pickaxe over the
ledger (RK31), so this is a query over git and not a number anybody maintains: it cannot
rot, it costs nothing on the turns nobody asks (L5), and a reader who doubts it can check
it against `git log`. That is also why there is no field on a line — §RK72 carries that
argument, and the non-goal it produced is binding.

**Two axes, because the corpus disagrees about which one is paid.** What carries that is
the comparison and not either range, so it is stated scale-free (RK367): median to p90,
lines vary 2.7× and files — which is what an agent holds in context — 1.4×, the axis paid
being the flatter one by half. Reporting one would be choosing the author's axis for them,
so both are here and neither is combined into a score.

What this is for: **granularity, at the moment the line is written.** A block whose last
comparables shipped at 800+ lines is a block where the next line is probably two lines.
What it is explicitly not for: **ranking work.** Every tier of `pick` is a fact, and a
cheapness tier would defer exactly the nine tasks above — the ones with the most leverage.

**A commit that wrote N entries is not N costs** (RK94). One task, one commit is the rule
the whole derivation rests on, and history is full of files where it was not kept: a
squashed adoption import writes the entire backlog at once, and this repository itself has
three entries in one commit. Charging that commit's size to each of them put its value in
every percentile at once, and the median offered for judging granularity then described
the batch instead of a task. So a co-shipped entry is **named and left out of the
distributions**, never divided across them: 20963 lines over 47 entries is 446 apiece, a
number no commit contains and `git show` cannot refute, which is the one property a
derived answer has. The entry stays in :attr:`Weights.weighed` carrying its real commit —
that list was the only usable part when the percentiles collapsed, and it is what a reader
checks the exclusion against.
"""

from __future__ import annotations

import statistics
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass

from roadkeep.config import Config
from roadkeep.kernel.document import Entry
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
    #: How many ledger entries this commit wrote (RK94). 1 is the rule kept, and then
    #: `lines` and `files` are this task's own cost; above 1 they are the batch's, shared
    #: by every entry in it and belonging to none of them.
    shared: int = 1

    @property
    def alone(self) -> bool:
        """Whether the commit's size is this task's cost, which is what a spread is over."""
        return self.shared == 1


@dataclass(frozen=True, slots=True)
class Spread:
    """A distribution over one axis. Empty is a real answer: nothing shipped yet.

    Percentiles rather than a mean: the corpus spans two orders of magnitude and the
    architectural tasks at the top would pull an average into a number no task ever cost.
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
    #: Ids whose commit wrote more than one entry (RK94), in scope and left out of every
    #: distribution above. Named for `unresolved`'s reason: an exclusion the answer does not
    #: state is a count that reads as the whole ledger.
    co_shipped: tuple[str, ...] = ()

    @property
    def recent(self) -> tuple[Weight, ...]:
        """The last comparables, newest first — what the shipped order already implies.

        Only entries whose commit is their own: "the last three comparables" is a question
        about what a task costs, and a batch is not comparable to the line being written.
        """
        return tuple(reversed([w for w in self.weighed if w.alone][-COMPARABLES:]))

    def by_block(self) -> dict[str, Spread]:
        """The line spread per block, in the order the ledger states them.

        Lines only: the per-block answer is the one a `--block` question refines, and a table
        carrying both axes for every block is the file back rather than an answer (RK29).
        """
        grouped: dict[str, list[int]] = {}
        for weight in self.weighed:
            # The block keeps its row even when every entry in it was co-shipped: an empty
            # spread reads as "nothing comparable here", and a missing row reads as no block.
            values = grouped.setdefault(weight.block, [])
            if weight.alone:
                values.append(weight.lines)
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
    # Counted over the whole ledger and never over the scope (RK94): how many entries a
    # commit wrote is a fact about that commit, and a `--block` question that only saw its
    # own two of the forty-seven would call a batch a task.
    entries_per_commit = Counter(shipped.values())

    every = tuple(
        (entry, _weight(entry, shipped, costs, entries_per_commit))
        for entry in ledger.entries
    )
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
    alone = tuple(w for w in weighed if w.alone)
    return Weights(
        weighed=weighed,
        lines=Spread.of(tuple(w.lines for w in alone)),
        files=Spread.of(tuple(w.files for w in alone)),
        # Always the whole ledger, scoped or not: a block's median says nothing without the
        # number it is being compared against.
        everywhere=Spread.of(
            tuple(w.lines for _, w in every if w is not None and w.alone)
        ),
        block=block,
        unresolved=tuple(entry.task.id for entry, weight in scoped if weight is None),
        co_shipped=tuple(w.task_id for w in weighed if not w.alone),
    )


def _weight(
    entry: Entry,
    shipped: dict[str, str],
    costs: dict[str, Cost],
    entries_per_commit: Mapping[str, int],
) -> Weight | None:
    """One entry as a weight, or None when no commit accounts for it."""
    sha = shipped.get(entry.task.id, "")
    cost = costs.get(sha)
    if cost is None:
        return None
    return Weight(
        task_id=entry.task.id,
        block=entry.task.block,
        lines=cost.lines,
        files=cost.files,
        commit=cost.short,
        shared=entries_per_commit.get(sha, 1),
    )


@dataclass(frozen=True, slots=True)
class Weighed:
    """What `weight` answers, as one result both registers are derived from (RK1170).

    `rendering.py` was cut out of a `cli.py` that had reached 8,489 lines, and the printers went
    first because theirs is the cut with no import cycle. That fixed a file's size and not where a
    verb's answer lives: counted for RK1170, `verbs/` makes 386 `print` calls of its own against
    102 delegations, and this verb was the shape of it — the plain answer spelled inside the
    handler and `_weight_json` in the other file, one verb's two registers two files apart.

    **The two registers are meant to differ.** Plain stdout is the value a shell composes with;
    `--json` carries the provenance that makes an answer auditable. So this is not one output: it
    is one result, and both readings are derived from it here, where the numbers were computed.
    What the payload carries is then what the plain answer showed by construction, which is
    today's `test_weighing` assertion turned into a property of the code.

    Here and not in `verbs/querying.py`: the record is the *answer*, and the verb is the door.
    A handler that owned the type would be the layer this task is unwinding, one file over.
    """

    #: The ledger this weighed, as the project spells it.
    where: str
    weights: Weights
    #: Whether the caller asked for the sample behind the percentiles (RK264).
    records: bool

    def __str__(self) -> str:
        """The plain register: the value a shell composes with, one fact per line."""
        scope = f"  Block {self.weights.block}" if self.weights.block else ""
        rows = [
            f"{self.where}{scope}  {self.weights.lines.count} weighed",
            f"  lines    {self.weights.lines}",
            f"  files    {self.weights.files}",
        ]
        if self.weights.block:
            # The number the block is being compared against, without a second command.
            rows.append(f"  ledger   {self.weights.everywhere}")
            rows += [
                f"  last     {one.task_id:<6} {one.lines:>5} lines  "
                f"{one.files:>3} files  {one.commit}"
                for one in self.weights.recent
            ]
        else:
            rows += [
                f"  block {label:<3} {spread}"
                for label, spread in self.weights.by_block().items()
            ]
        if self.weights.co_shipped:
            # Named for the reason `missing` is (RK94): the numbers above are over fewer entries
            # than the ledger holds, and a spread that does not say so reads as all of it.
            rows.append(
                f"  batched  {len(self.weights.co_shipped)} entr(ies) left out, whose commit "
                f"wrote more than one: {', '.join(self.weights.co_shipped)}"
            )
        if self.weights.unresolved:
            # An absent answer is not a cheap task (RK28): a squash or a shallow clone leaves an
            # entry no commit accounts for, and a count that hid them would read as complete.
            rows.append(
                f"  missing  {len(self.weights.unresolved)} entr(ies) no commit accounts for: "
                f"{', '.join(self.weights.unresolved)}"
            )
        if self.records:
            rows += [
                f"  record   {one.task_id:<6} {one.lines:>5} lines  {one.files:>3} files  "
                f"{one.commit}"
                + (f"  shared with {one.shared - 1} more" if one.shared > 1 else "")
                for one in self.weights.weighed
            ]
        elif self.weights.weighed:
            # Named and never silent (RK10): a listing that looked complete is the whole symptom
            # one command over, and an elision the answer does not state is the same defect here.
            rows.append(
                f"  records  {len(self.weights.weighed)} not shown — `--records` prints them"
            )
        return "\n".join(rows)

    def payload(self) -> dict[str, object]:
        """The distribution, the counts, and the sample only where it was asked for (RK264).

        The percentiles **are** the answer — 22.7k of 23.7k characters here were the sample they
        summarise, and scoping to a block only moved that to 89%, so the read priced to save
        context was the one that spent it. What replaces the array is a count and never a cap: a
        top-N would make the p90 a statement about a sample nobody chose, and the figure is the
        one thing this command may not get wrong.

        `unresolved` and `co_shipped` stay unconditionally. They are ids and not records, and they
        are what says the distribution is over fewer entries than the ledger holds — the half of
        this that must never be behind a flag.
        """
        return {
            "file": self.where,
            "block": self.weights.block,
            "lines": _spread_json(self.weights.lines),
            "files": _spread_json(self.weights.files),
            "ledger": _spread_json(self.weights.everywhere),
            "blocks": {
                label: _spread_json(one) for label, one in self.weights.by_block().items()
            },
            "weighed": [
                {
                    "id": one.task_id,
                    "block": one.block,
                    "lines": one.lines,
                    "files": one.files,
                    "commit": one.commit,
                    # The entry keeps its real numbers and says what they are the size of, so
                    # the list stays checkable against `git show` (RK94).
                    "shared": one.shared,
                }
                for one in self.weights.weighed
            ]
            if self.records
            else [],
            # `brief`'s `non_goals_elided`, one command over: the caller knows the list it read
            # was cut, and 0 is the honest answer where nothing was.
            "weighed_elided": 0 if self.records else len(self.weights.weighed),
            "unresolved": list(self.weights.unresolved),
            "co_shipped": list(self.weights.co_shipped),
        }


def _spread_json(one: Spread) -> dict[str, int]:
    """One distribution as the fields both registers name it by."""
    return {
        "count": one.count,
        "low": one.low,
        "high": one.high,
        "p25": one.p25,
        "median": one.median,
        "p75": one.p75,
        "p90": one.p90,
    }
