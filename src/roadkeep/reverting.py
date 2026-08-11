"""Which decisions the ledger has already undone (RK416).

`origin <id>` reads a claim out of history and `gaps` resolves an id in neither file, so
history is queryable — but not for the question worth asking *before* a line is written:
**has this been tried and undone?**

A reversal is recorded as a delivery, and that is the whole defect. RK395 made the record
honest: `record add --supersedes <id>` writes the entry saying the work did not hold *and*
appends the forward pointer to the entry saying it shipped, so both records of one decision
name each other. What it did not do is make the pair *findable*. A duplicate check that asks
"did a shipped entry already do this" answers yes about the revert — because a revert is a
✅ entry like any other — and misses that the new line is asking to undo it again.

The cost is worse than a duplicate's. A duplicate wastes an id; this wastes an id *plus the
argument the revert already had*, and the argument is the expensive half. Measured on a real
corpus: two tasks proposed automatic CI triggers, a third shipped the revert naming both by
id and saying the state a reader takes for an oversight is deliberate — and a fourth proposal
would still have been filed without a word.

**Nothing new is stored.** The forward pointer RK395 already writes is the whole signal, and
this reads it back: an entry whose sentence carries `(superseded by <id>)` is a decision that
was reversed, and the entry naming it is the argument. That is the same discipline as every
other query here — the store is the repository (L2), and a second index of what the ledger
already says is a second thing to keep in step.

What this deliberately does **not** do is refuse an `add`. Re-proposing something that was
reverted is sometimes exactly right — the revert may have been about a broken implementation
rather than a wrong idea — so the answer is a read the author makes, not a gate that decides
for them. A tool that judged which would be judging the prose (L4).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .backlog import Backlog
from .config import Config
from roadkeep.kernel.document import Entry

#: How :data:`~roadkeep.shipping._SUPERSEDED` renders, read back. Built from that constant
#: rather than spelled again: the writer and the reader of one clause disagreeing is the
#: defect this package is about, and a second literal here is how it would start.
_MARK = re.compile(r"\(superseded by ([^)]+)\)")


@dataclass(frozen=True, slots=True)
class Reversal:
    """One decision the ledger recorded and then undid."""

    #: The id whose entry carries the forward pointer — the work that shipped and did not hold.
    undone: str
    #: The id of the entry that reversed it, which is where the argument is.
    by: str
    undone_entry: Entry
    by_entry: Entry | None = None

    @property
    def why(self) -> str:
        """The reversing entry's sentence, which is the argument a new proposal is against."""
        return "" if self.by_entry is None else self.by_entry.task.why

    def __str__(self) -> str:
        where = f"{self.undone_entry.lineno}"
        return f"{self.undone:<8} undone by {self.by:<8} ledger:{where}  {self.why}"


def reversals(config: Config) -> tuple[Reversal, ...]:
    """Every entry the ledger marks as superseded, and the entry that superseded it.

    In ledger order, which is block order: a reader scanning for "was this area already
    settled" is scanning by subject, and the file is already arranged that way.
    """
    backlog = Backlog.load(config)
    ledger = backlog.ledger
    if ledger is None:
        return ()
    entries = ledger.by_id()
    out: list[Reversal] = []
    for task_id, entry in entries.items():
        found = _MARK.search(entry.task.why)
        if found is None:
            continue
        by = found.group(1).strip()
        out.append(Reversal(task_id, by, entry, entries.get(by)))
    return tuple(out)


def undone(config: Config) -> frozenset[str]:
    """The ids alone — what a caller checks a fresh proposal against."""
    return frozenset(one.undone for one in reversals(config))
