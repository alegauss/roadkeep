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
stale against a changelog it never read. The one split that *is* here — startable
against waiting (RK1432) — stays inside that rule because `(requires: …)` is a slot on
the line: what a task needs present to be done at all is stated where the task is, and
no second file has to be opened to say how much of a backlog nobody can begin.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, replace

from roadkeep.backlog import Standing
from roadkeep.capturing import Debt
from roadkeep.config import Config
from roadkeep.kernel.document import Document, Entry, Reject, declares, shading
from roadkeep.kernel.schema import DEFAULT_HEADING_WORD, Schema, width
from roadkeep.remedying import Door


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
class Absent:
    """One requirement nothing here supplies, and how many open lines name it (RK1432)."""

    requirement: str
    lines: int


@dataclass(frozen=True, slots=True)
class Split:
    """The open count divided by what a line needs *present* to be done at all (RK1432).

    The distinction was modelled long before it was counted: `(requires: …)` is a slot,
    `pick --have` sets a line aside by it, `brief` names what is absent. Every part existed
    except the one reaching a reader who is not picking a task — so an adopting project
    re-derived it in a hundred lines of its own code against the file this tool owns, which
    is the one re-parse the whole design exists to make unnecessary.

    **Open, not counted.** The subject is work somebody could begin, so the population is
    `[markers]`' own open set: a ✅ left in the roadmap, a ⏸ and a 🗑 are outside it, and
    none of the three is startable in the sense being asked.

    **`waiting` counts lines and `absent` counts requirements**, which is why they are two
    numbers rather than one summed twice. A line naming a console *and* a signing
    certificate is one line waiting and a row under each, so the rows can total more than
    the count beside them — the arithmetic a split built from requirements instead of from
    lines gets wrong in the direction nobody checks.
    """

    open_lines: int
    startable: int
    absent: tuple[Absent, ...]

    @property
    def waiting(self) -> int:
        """Derived and never stored: two fields that can disagree is the miss again."""
        return self.open_lines - self.startable

    def stated(self, width: int) -> list[str]:
        """The two rows, or none where this file has no open line at all.

        Both rows print when there is one, `waiting 0` included, for the rule the counts
        above them follow: a field that appears only when it is non-zero is a field a reader
        learns to stop looking for. Nothing prints where the count is zero, because the
        split of nothing is not a fact about the axis — it is `total` said twice.

        `startable` is nine characters, exactly `uncounted`'s, so these rows never widen a
        column the totals did not already reserve.
        """
        if not self.open_lines:
            return []
        return [
            f"  {'startable':<{width}}  {self.startable:>4}",
            f"  {'waiting':<{width}}  {self.waiting:>4}  "
            f"{'  '.join(f'{one.requirement} {one.lines}' for one in self.absent)}".rstrip(),
        ]

    def payload(self) -> dict[str, object]:
        """The same answer as data, carried whatever the project declares.

        Printed conditionally and published always, which is :meth:`Debt.payload`'s rule for
        its reason: a key costs a client nothing to skip, where a row costs every reader the
        same attention on every run — and a project wiring this into its own gate wants the
        number to be there before the first `(requires: …)` is written.
        """
        return {
            "open": self.open_lines,
            "startable": self.startable,
            "waiting": self.waiting,
            "absent": [
                {"requirement": one.requirement, "lines": one.lines}
                for one in self.absent
            ],
        }


@dataclass(frozen=True, slots=True)
class Bound:
    """A listing over `[reads] list`, and the shape of the answer it would have been (RK1476).

    An unscoped `list` prints the file. On the project measured that was 117,815 characters of
    ledger — composed here, returned, and then refused by the transport carrying it. The
    refusal is nobody's: roadkeep exited 0 having answered, and never learns that the answer
    did not arrive. So the only bound that can exist is one this verb applies to itself.

    What replaces the listing is its **structure**: the blocks of exactly the selection that
    overran, with their counts, which is smaller than the answer refused and is what a caller
    narrows by. RK1455 argued for that answer and could not act on it.

    **The door has to work.** A narrowing offered here is a command this refusal is telling
    somebody to run, and one that refuses in turn is worse than none (RK1475). So the block
    named is the largest whose share of the listing is estimated to fit — and where no single
    block would, there is no door and the sentence says the ceiling is the thing to re-argue.
    """

    file: str
    #: What the answer would have cost, in the UTF-16 code units every other budget is in
    #: (RK430) — measured on the **composed** answer, so `--ids` and `--json` are each held
    #: against what that form actually returns rather than against a listing neither prints.
    characters: int
    limit: int
    blocks: tuple[Tally, ...]
    total: int
    #: Whether a `--block` was already passed. Where it was, narrowing is spent: the sentence
    #: has nothing to offer but the ceiling itself.
    scoped: bool
    #: The argv this refusal came from, less the block flag — so the door it composes is the
    #: caller's own call and not a reconstruction of it.
    argv: tuple[str, ...] = ()

    @property
    def narrows(self) -> str:
        """The label a listing would fit under, or `""` where none would."""
        if self.scoped or not self.total:
            return ""
        fitting = [
            tally
            for tally in self.blocks
            if tally.label and tally.counted * self.characters <= self.limit * self.total
        ]
        return max(fitting, key=lambda tally: tally.counted).label if fitting else ""

    @property
    def doors(self) -> tuple[Door, ...]:
        """The narrowing, as the one shape every published command in this package has.

        `Door` and not a string, and `doors` and not `door` (RK1324): a consumer offering a
        command here loops over the same list, with the same keys, as one offered by a lint
        finding — and the rendering, quoting and this-engine prefix are that class's.
        """
        label = self.narrows
        if not label:
            return ()
        return (
            Door(
                (*self.argv, "--block", label),
                f"the largest listing under `[reads] list` — {label}",
            ),
        )

    def stated(self) -> str:
        """The structure, for **stderr** — stdout stays what the file says or nothing at all.

        `list`'s own split (RK1170): a sentence in the pipe is a line no `--ids` consumer asked
        for, and one arriving where the lines were expected is worse than the empty stdout an
        exit code already explains.
        """
        pad = max([len(tally.name) for tally in self.blocks] + [len("total")])
        rows = [
            f"roadkeep: {self.file}: the listing is {self.characters} characters against "
            f"`[reads] list` = {self.limit}, so this is its shape instead"
        ]
        rows += [
            f"  {tally.name:<{pad}}  {tally.counted:>4}  {_marker_row(tally.markers)}".rstrip()
            for tally in self.blocks
        ]
        rows.append(f"  {'total':<{pad}}  {self.total:>4}")
        if self.doors:
            rows += [
                f"roadkeep: `{one.command}` is the largest of those that fits"
                for one in self.doors
            ]
        elif self.scoped:
            rows.append(
                "roadkeep: this is one block already, so there is no narrower listing — "
                "what is left is `[reads] list` re-argued in roadkeep.toml"
            )
        else:
            rows.append(
                "roadkeep: no single block would fit either, so there is no narrowing to "
                "offer — what is left is `[reads] list` re-argued in roadkeep.toml"
            )
        return "\n".join(rows)

    def payload(self) -> dict[str, object]:
        """What rides the listing's payload where `tasks` came back `null`.

        Beside the keys the answer already had and never instead of them: a payload that
        changes shape when it is over is one a caller reads as a different answer, and
        `tasks: null` is the one thing here that says *not listed* where `[]` says *none*.
        """
        return {
            "characters": self.characters,
            "limit": self.limit,
            "blocks": [
                {"label": tally.label, "name": tally.name, "counted": tally.counted}
                for tally in self.blocks
            ],
            "scoped": self.scoped,
            # `""` and not `null` where no block would fit: the question was answered — there
            # is no narrowing — and a missing key reads as one nothing looked for.
            "narrows": self.narrows,
            "doors": [one.payload() for one in self.doors],
        }


def _marker_row(markers: Mapping[str, int]) -> str:
    """One row's markers as `📋 3  🛠 1` (RK1170).

    Beside the report it belongs to, and named apart from :meth:`Census._markers`: that one
    counts entries into a mapping and this one spells a mapping for a reader.
    """
    return "  ".join(f"{marker} {count}" for marker, count in markers.items())


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
                from roadkeep.provenance import invocation  # noqa: PLC0415 - RK260

                raise KeyError(
                    f"no heading declares {self.schema.block_named(block)} in {self.file}"
                    # The labels are not listed (RK296) — a filter nobody can correct from the
                    # list alone is not corrected by a longer one.
                    f"{declares(self.blocks, named=True)}"
                    # The same diagnosis the write refusal gives (RK216): `--block A` against
                    # a file declaring AJ reads as "that block is empty" dressed as "absent".
                    f"{shading(block, self.blocks)}"
                    # And the read that answers the question this filter was asked with
                    # (RK1455). RK296 is right that a caller who mistyped a label is not
                    # picking from a menu, and the caller measured here had no label at all:
                    # an unscoped listing of the ledger was 117,815 characters, `--block`
                    # wanted the letter being looked for, and what they did next was grep the
                    # governed file — the one move the hook exists to prevent. A door and not
                    # a list, which is what RK296 removed.
                    f" — `{invocation()} block list` names every label, its title and what "
                    f"each holds"
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

    def _is_open(self, status: str) -> bool:
        """Whether a line carrying this marker is work somebody could still begin (RK1432).

        Two questions and both have to be asked. The **file**: a ledger's own status is ✅
        and a deferred store's is ⏸, so each declares its whole contents settled — and a
        ledger may drop the marker slot entirely (RK43), where reading the status would
        find nothing to exclude. Then the **line**: a roadmap may hold a ✅ or a 🗑 that
        `total` counts and nobody can start, so the three terminal markers are named rather
        than assumed absent from `[markers]`.
        """
        if self.schema.is_ledger or self.schema.is_deferred:
            return False
        terminal = {
            self.schema.shipped_marker,
            self.schema.deferred_marker,
            self.schema.retired_marker,
        }
        return status in self.schema.markers and status not in terminal

    def split(self, available: Iterable[str] = ()) -> Split:
        """How many open lines nothing absent is holding up, and what the rest wait for.

        ``available`` is the caller's and empty by default, which is the same decision
        `pick` made (RK1297): the reader who cannot press a button is the one who does not
        think to say so, and a count that assumed otherwise would report as startable
        exactly the work this split exists to separate out. A person at the desk says
        `--have` and the lines they can reach move across.

        A parameter and not a field, for the reason `debt` is one: what a caller has is a
        fact about the caller, and a census that read it would be a count of the file
        depending on the machine it ran on.
        """
        has = frozenset(available)
        open_lines = tuple(
            entry for entry in self.counted if self._is_open(entry.task.status)
        )
        counts: dict[str, int] = {}
        waiting = 0
        for entry in open_lines:
            missing = [one for one in entry.task.requires if one not in has]
            if not missing:
                continue
            waiting += 1
            for one in missing:
                counts[one] = counts.get(one, 0) + 1
        return Split(
            open_lines=len(open_lines),
            startable=len(open_lines) - waiting,
            # Most-waited-on first, ties by the word. A reader scanning this wants the
            # requirement holding the most work at the top; a tie broken by nothing at all
            # is a row order that moves between two runs over an unchanged file.
            absent=tuple(
                Absent(requirement=name, lines=lines)
                for name, lines in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
            ),
        )

    # -- the two registers, and the third stream ---------------------------

    def listed(self, ids: bool) -> str:
        """The lines this filter selected, exactly as the file spells them (RK10).

        Beside :meth:`listing` since RK1170. `ids` is the caller's: which of two shapes a
        terminal wants is a fact about the argv, and this record does not read one.
        """
        return "\n".join(entry.task.id if ids else entry.raw for entry in self.counted)

    def bounded(
        self, answer: str, limit: int | None, *, scoped: bool, argv: Iterable[str] = ()
    ) -> Bound | None:
        """The composed answer weighed against `[reads] list`, or `None` where it fits (RK1476).

        Takes the answer rather than composing one: `--ids` and `--json` return different
        widths of the same selection, and a bound measured on a listing neither of them prints
        is a bound refusing the wrong calls in both directions.

        Silent where the project declares no ceiling, which is every project until it looks —
        `[reads]`' rule, and the reason this can be added to a verb everything already calls.
        """
        if limit is None or width(answer) <= limit:
            return None
        return Bound(
            file=self.file,
            characters=width(answer),
            limit=limit,
            blocks=self.tallies(),
            total=self.total,
            scoped=scoped,
            argv=tuple(argv),
        )

    def notes(self, standing: Standing | None) -> list[str]:
        """What goes to **stderr** beside a listing (RK10, RK429).

        Its own method and not the tail of :meth:`listed` (RK1170): stdout stays exactly what
        the file says, so `list` substitutes for the grep it replaces — a sentence in the pipe
        is a line no `--ids` consumer asked for, and a miss that could corrupt one is worse.

        Two, and they answer different questions. **Which silence this is** where the listing
        came back empty: nothing is said about a *live* block, because a marker filter matching
        none of its open lines is a fact about the filter. And **what was not counted**, printed
        whenever anything was — a listing that looked complete is the whole symptom.
        """
        rows = self.silence(standing)
        if self.missed:
            from roadkeep.provenance import invocation  # noqa: PLC0415 - RK260

            rows.append(
                f"roadkeep: {self.uncounted} marker-bearing line(s) in {self.file} "
                f"were not counted; run '{invocation()} audit' to see them"
            )
        return rows

    def silence(self, standing: Standing | None) -> list[str]:
        """Which of the two silences an empty count is (RK429), for **stderr**.

        The half of :meth:`notes` `audit` and `stats` want on their own: those two report the
        misses as their subject, so the sentence about what was *not* counted would be the
        report saying its own contents twice.
        """
        if self.counted or standing is None or not standing.settled:
            return []
        return [f"roadkeep: {standing.sentence}"]

    def listing(
        self,
        standing: Standing | None,
        available: Iterable[str] = (),
        bound: Bound | None = None,
    ) -> dict[str, object]:
        """The same answer as data, with what the label it was scoped to turned out to be.

        ``bound`` is the ceiling this answer did not fit under (RK1476). Every key it had
        stays: only `tasks` is withdrawn, to `null` — which says *not listed* where `[]` says
        *none selected*, a distinction a payload that simply came back shorter cannot make.
        """
        from roadkeep.rendering import _miss_json, _row_json  # noqa: PLC0415 - RK260

        return {
            "file": self.file,
            "total": self.total,
            "uncounted": [_miss_json(one) for one in self.missed],
            # Beside the count and not instead of it (RK429): a total of 0 is the answer to
            # what was asked, and this is what the label it was scoped to turned out to be.
            # `None` where no block was named, which is the question rather than a missing
            # answer: a listing over the whole file has no standing.
            "standing": None if standing is None else standing.payload(),
            # The split, riding a payload instead of arriving as a tool (RK1442). RK1432 gave
            # `stats` a division of the open count and `stats` is the one counting verb this
            # surface withholds, so the answer reached a terminal and not the caller this
            # project ships for. A forty-fifth tool is paid for by every session at connect
            # and this key is paid for by nobody — and it is the same number, computed over
            # exactly the lines this call selected, which makes a filtered listing say what
            # its own selection is waiting on rather than what the whole file is.
            "startable": self.split(available).payload(),
            # `None` where the project declares no ceiling, which is the answer *no bound was
            # applied* and not *it fitted*: a key that appears only on the refusal is one a
            # caller has to have met before to check for.
            "over": None if bound is None else bound.payload(),
            "tasks": None if bound is not None else [_row_json(entry) for entry in self.counted],
        }

    def counted_out(
        self, config: Config, debt: Debt, available: Iterable[str] = ()
    ) -> str:
        """The tallies, the totals, and the capture debt beside them (RK10, RK1139).

        Beside :meth:`counts` since RK1170. `debt` is a parameter and not a field: a capture is
        not a line of the file this counts, and reading one here would make a count of the
        roadmap depend on a directory git ignores.

        The startable split prints **only where the project declares requirements** (RK1432),
        which is `Debt.stated`'s rule for its reason: the axis is opt-in, and two rows saying
        `startable = total` on every run of a backlog that never names a requirement is the
        row a reader stops looking at. Declaring `[requirements]` is the opt-in, not writing
        the first `(requires: …)` — a project that declared the vocabulary is asking the
        question, and `waiting 0` is the answer it is checking for.
        """
        from roadkeep.kernel.schema import width as measured  # noqa: PLC0415 - RK260

        tallies = self.tallies()
        names = [tally.name for tally in tallies] + ["total", "uncounted"]
        pad = max(len(name) for name in names)
        rows = [self.file]
        rows += [
            f"  {tally.name:<{pad}}  {tally.counted:>4}  "
            f"{_marker_row(tally.markers)}".rstrip()
            for tally in tallies
        ]
        rows.append(
            f"  {'total':<{pad}}  {self.total:>4}  {_marker_row(self.markers())}".rstrip()
        )
        # Printed at zero too: a field that appears only when it is non-zero is a field a
        # reader learns to stop looking for, which is how the miss became invisible.
        rows.append(f"  {'uncounted':<{pad}}  {self.uncounted:>4}")
        if self.schema.requirements:
            rows += self.split(available).stated(pad)
        longest = self.longest()
        if longest is not None:
            rows.append(
                f"  {'longest':<{pad}}  {longest.task.id} at {measured(longest.raw)} "
                f"of {self.schema.line_max}"
            )
        rows += debt.stated(config, pad)
        return "\n".join(rows)

    def counts(
        self,
        config: Config,
        standing: Standing | None,
        debt: Debt,
        available: Iterable[str] = (),
    ) -> dict[str, object]:
        """The same answer as data, with the debt this project holds under its own key."""
        from roadkeep.rendering import CHARACTER_UNIT  # noqa: PLC0415 - RK260
        from roadkeep.kernel.schema import width as measured  # noqa: PLC0415 - RK260

        longest = self.longest()
        return {
            "file": self.file,
            "total": self.total,
            "uncounted": self.uncounted,
            "markers": self.markers(),
            # RK1432, and always — the text register hides this where the axis is unused,
            # because a row costs a reader on every run and a key costs a client nothing.
            "startable": self.split(available).payload(),
            "blocks": [
                {
                    "block": tally.label,
                    "counted": tally.counted,
                    "uncounted": tally.missed,
                    "markers": dict(tally.markers),
                }
                for tally in self.tallies()
            ],
            "longest": None
            if longest is None
            else {
                "id": longest.task.id,
                "length": measured(longest.raw),
                "limit": self.schema.line_max,
                "unit": CHARACTER_UNIT,
            },
            # `None` where no block was named, which is the question rather than a missing
            # answer (RK429): a listing over the whole file has no standing.
            "standing": None if standing is None else standing.payload(),
            # RK1139: a capture nothing counts is a note in a drawer, and this tool's whole
            # argument is against those. Its own key, because it is debt this project holds
            # and not a line of the backlog it is reporting.
            "captures": debt.payload(config),
        }

    def audited(self) -> str:
        """Every marker-bearing line the count did not count, and why (RK10).

        The empty answer is a sentence and not a blank: exit stays 0, because reporting is
        not the gate — and :meth:`silence` is what says why a count came back at zero, on the
        stream that cannot corrupt a pipe.
        """
        if not self.missed:
            return f"{self.file}: {self.total} counted, none uncounted"
        rows = []
        for miss in self.missed:
            where = f"Block {miss.block}" if miss.block else "no block"
            rows.append(f"{self.file}:{miss.lineno}  ({where})  {miss.reason}")
            rows.append(f"    {miss.raw.strip()}")
        rows.append(f"{self.file}: {self.total} counted, {self.uncounted} uncounted")
        return "\n".join(rows)

    def audit(self, standing: Standing | None) -> dict[str, object]:
        """The misses as data. `counted` and not `total`: this verb's subject is what was not."""
        from roadkeep.rendering import _miss_json  # noqa: PLC0415 - RK260

        return {
            "file": self.file,
            "counted": self.total,
            "uncounted": [_miss_json(one) for one in self.missed],
            "standing": None if standing is None else standing.payload(),
        }
