"""Counting a backlog so that what the count missed is part of the count (RK10).

`grep -c` answers exactly the question it was asked and says nothing about the lines
it failed to match, so a file with eight tasks and one broken line reports eight —
byte-identical output to a clean file. The miss is not merely unreported, it is
*unrepresentable*: there is no number in that answer where it could have appeared.

So every count here carries two: what it counted and what it could not. `stats` prints
the second one even when it is zero, because a field that only appears when it is
non-zero is a field a reader learns to stop looking for; `audit` prints those lines one
by one with the reason the parser gave, which is what makes the first number trustable.

Two consequences worth naming:

* **A declared block with no tasks is a row, not an absence.** Block A of this
  repository is finished and Block A of a fresh `init` is empty; both are facts, and a
  table that omits them makes the two look like a block that does not exist (RK37 in
  miniature).
* **A task under no block heading is counted under no block**, never folded into the
  heading above it. Shio parks lines under "## Priority queue"; attributing them to
  whatever block preceded it would make the per-block column disagree with the total
  in the one direction nobody checks.

This module resolves nothing: readiness, blockers and leverage are RK11 and RK13, which
need both files. A count needs one, and keeping it that way is why `stats` cannot go
stale against a changelog it never read.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace

from roadkeep.config import Config
from roadkeep.kernel.document import Document, Entry, Reject, declares, shading
from roadkeep.kernel.schema import DEFAULT_HEADING_WORD, Schema, width


@dataclass(frozen=True, slots=True)
class Tally:
    """One block's two numbers, and its markers in the order the project declares."""

    label: str
    counted: int
    missed: int
    markers: Mapping[str, int]
    #: The word this project files work under (RK75). Carried on the row rather than read
    #: from a constant, because a report is read by the author of the file it counts and
    #: `Block G` on a project whose headings all say `Track` names nothing they wrote.
    word: str = DEFAULT_HEADING_WORD

    @property
    def name(self) -> str:
        return f"{self.word} {self.label}" if self.label else NO_BLOCK


#: What a line under no block heading is called in a report. Not "Block —": it is the
#: absence of a block, which is a lint error (RK14) rather than a place.
NO_BLOCK = "(no block)"


@dataclass(frozen=True, slots=True)
class Census:
    """One governed file, counted: what parsed, what did not, what blocks exist."""

    role: str
    file: str
    schema: Schema
    #: Every block a heading declares, in file order — including the empty ones.
    blocks: tuple[str, ...]
    counted: tuple[Entry, ...]
    missed: tuple[Reject, ...]

    @classmethod
    def read(cls, config: Config, role: str = "roadmap") -> Census:
        return cls.of(config, role, config.document(role))

    @classmethod
    def of(cls, config: Config, role: str, document: Document) -> Census:
        """The same count over a document somebody else read.

        The seam a caller holding a file it did not open off disk needs — a projection
        derived at a revision (RK104), or a transaction counting what it is about to write.
        Nothing here touches the filesystem, so what is counted is what was handed over.
        """
        return cls(
            role=role,
            file=config.relative(config.path(role)),
            schema=document.schema,
            blocks=tuple(
                dict.fromkeys(h.label for h in document.headings if h.label)
            ),
            counted=document.entries,
            missed=document.rejects,
        )

    # -- narrowing ---------------------------------------------------------

    def elsewhere(self, block: str) -> Census:
        """This file counted for a label only the *other* file declares (RK429).

        :meth:`select` refuses a block no heading here declares, and it is right to: a
        filter matching nothing reads as a clean file. But a block whose last task shipped
        keeps its heading in the ledger and may have lost the one in the roadmap, so the
        same refusal fires for a label that exists and is done — which is the answer this
        module's own docstring says a table must not omit.

        Nothing is read: the caller has already established the label elsewhere, and what
        comes back is this file's honest zero rather than a second file folded into a count
        that promises to read one.
        """
        return replace(self, counted=(), missed=(), blocks=(block,))

    def select(self, block: str | None = None, marker: str | None = None) -> Census:
        """The same census over fewer lines. A filter that matches nothing is refused.

        An undeclared block or an undeclared marker would return zero lines, and zero
        is the answer a clean file gives — the ambiguity this module exists to remove.
        Both raise instead, naming what the project does declare.
        """
        counted, missed, blocks = self.counted, self.missed, self.blocks
        if block is not None:
            if block not in self.blocks:
                raise KeyError(
                    f"no heading declares {self.schema.block_named(block)} in {self.file}"
                    # The labels are not listed (RK296) — a filter nobody can correct from the
                    # list alone is not corrected by a longer one.
                    f"{declares(self.blocks, named=True)}"
                    # The same diagnosis the write refusal gives (RK216): `--block A` against
                    # a file declaring AJ reads as "that block is empty" dressed as "absent".
                    f"{shading(block, self.blocks)}"
                )
            counted = tuple(e for e in counted if e.task.block == block)
            missed = tuple(r for r in missed if r.block == block)
            blocks = (block,)
        if marker is not None:
            allowed = (*self.schema.markers, self.schema.shipped_marker)
            if marker not in allowed:
                raise KeyError(
                    f"{marker} is not a marker this project declares "
                    f"({' '.join(allowed)})"
                )
            counted = tuple(e for e in counted if e.task.status == marker)
            # A reject has no status the schema trusts — it is why it was rejected —
            # so a marker filter cannot claim to have counted its misses.
            missed = ()
        return Census(
            role=self.role,
            file=self.file,
            schema=self.schema,
            blocks=blocks,
            counted=counted,
            missed=missed,
        )

    # -- the numbers -------------------------------------------------------

    @property
    def total(self) -> int:
        return len(self.counted)

    @property
    def uncounted(self) -> int:
        return len(self.missed)

    def markers(self) -> dict[str, int]:
        """Markers to counts, in declaration order. Zeroes are omitted here.

        A marker with no lines is not a fact about the project the way an empty block
        is: the set is declared in `roadkeep.toml` and the reader can already see it.
        """
        return self._markers(self.counted)

    def _markers(self, entries: tuple[Entry, ...]) -> dict[str, int]:
        found: dict[str, int] = {}
        for entry in entries:
            found[entry.task.status] = found.get(entry.task.status, 0) + 1
        ordered = (*self.schema.markers, self.schema.shipped_marker)
        out = {m: found[m] for m in ordered if m in found}
        # Anything left is a marker the schema does not declare, which the parser only
        # accepts through a variation selector. Kept, so the columns add up to the total.
        out.update({m: n for m, n in found.items() if m not in out})
        return out

    def tallies(self) -> tuple[Tally, ...]:
        """One row per declared block, plus the blockless one if any line is."""
        labels = list(self.blocks)
        if any(not e.task.block for e in self.counted) or any(
            not r.block for r in self.missed
        ):
            labels.append("")
        out = []
        for label in labels:
            inside = tuple(e for e in self.counted if e.task.block == label)
            out.append(
                Tally(
                    label=label,
                    counted=len(inside),
                    missed=sum(1 for r in self.missed if r.block == label),
                    markers=self._markers(inside),
                    word=self.schema.heading_word,
                )
            )
        return tuple(out)

    def longest(self) -> Entry | None:
        """The line closest to the limit — the measurement this repo did by hand."""
        return max(self.counted, key=lambda e: width(e.raw), default=None)
