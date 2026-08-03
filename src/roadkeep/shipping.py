"""A line leaving the roadmap: three edits across three files, or none of them (RK6, RK32).

Shipping is the moment the format is most likely to break, because it is the only
operation that is not one edit. The line leaves the roadmap, the entry appears in the
ledger, and the rationale section is deleted — and whichever of the three is done by
hand last is the one that gets forgotten, which is how a backlog comes to have a task
that is shipped in one file and open in another.

So the three edits are one command, and the ordering is deliberate: **everything is
computed and validated in memory before any file is touched.** A refusal — no such open
task, already in the ledger, no block heading there to file it under, a file that
already drifted (L3) — costs nothing and leaves three untouched files. Writing is the
last thing that happens, and by then nothing is left that can fail except the disk.

Two decisions worth stating, because both are narrower than they could be:

* **The roadmap line is removed, not replaced by a stub.** A pointer left behind is a
  second place a reader can ask about status, and the ledger is already greppable — the
  answer to "did RK5 ship?" has to have exactly one home (RK7).
* **The `why` is the author's, and it is required** (RK142). The roadmap's sentence is a
  problem and the ledger's is an outcome, so copying it across was writing the entry by
  omission — a defect report filed under a heading meaning "done". It is refused at input
  now, where every other field of every other write is already refused (L1); the tool still
  never writes the sentence itself (L4), it only declines to inherit the wrong one.

The dep annotations of every line that named this task are re-derived in the same
transaction (RK8), because `(deps: RK5)` becomes a false statement at exactly the moment
this command runs and nothing else would ever revisit it.

**Half of it is a state, and retiring the rest is not a verdict on the half** (RK121, RK129).
A ledger entry carrying a qualifier is the first half of *this* decision, so the departure
completes it in place — and only where the departure is a **ship**. Reaching the same code
with the retired marker replaced a `✅ **RK1 (local half)**` with a `🗑 **RK1**`, taking the
sentence about what actually landed out of the only file that held it: completing says the
rest landed too, retiring says it never will, and the second leaves the half that did ship as
history. That choice is refused back to the author rather than made silently.

**A line leaves by three doors and this module now records all three** (RK32). `ship` is
the first; :func:`retire` is the other two, superseded and abandoned, and it is the *same*
transaction with a different marker rather than a second one — because the failure being
fixed is that two of the three doors wrote nothing at all, not that they wrote it wrongly.
What survives a retirement is one line under the block it belonged to: the symptom moved
verbatim, and a `why` whose derived prefix names the replacement so the pointer is forward
and written at the moment of the decision. Never the design it replaced — an accreting
rationale file is the 539 KB this project exists to refuse.

**And the way out of the middle of one** (RK130). RK118 ordered a departure's three writes
so that every state a crash can leave is loud and lossless — the ledger first, so stopping
after it puts the id in two files and `lint` says so — and established no way out: `ship`
refused the id, :class:`Closure` wanted a marker the abandoned line does not carry, and
`record drop` wants a second entry. So the only exit was the edit the hook denies, on the
file this tool exists to own. :func:`_already_recorded` now reads the **ledger** side as well:
an entry for a line still open is a leftover unless the files say it is a live partial — a ⏳
line, or an entry naming a half. What that widening opened is refused rather than guessed: an
interrupted transaction wrote its entry from the line, so two that describe different work are
two tasks sharing an id, and `renumber` is their repair.

**A fourth door starts nowhere** (RK41). All three above begin from an open roadmap line,
so work that was finished before it was ever planned — a defect found on the way to
something else, fixed, real, shipped — has no route into the ledger except a fictitious
roadmap line shipped in the same breath. :func:`record` is that route made honest: it
writes the ledger entry and touches nothing else, which is why RK7 survives it untouched
— the line never exists open, so there is no second file to disagree with.

**And a door out of the ledger, for exactly one shape** (RK67). Every door above only ever
adds an entry, which is right for history and wrong for a duplicate: an id the ledger states
twice states one decision twice, `lint`'s `id.duplicate` reports it, and until now nothing but
the hand-edit the hook denies could act. :func:`drop` is the inverse of the door that wrote it
and refuses unless the id is there **twice** — removing the only record of a decision is
deleting history rather than de-duplicating it. The later entry goes: the first is where the
reader already found it — **and only when the two entries say the same thing** (RK127). Two
that do not are two deliveries under one id rather than one recorded twice, and the verb's
default picks exactly the wrong one of them: the entry that earned the id. So the guess is
refused and the reader chooses, either by naming the line that goes or by calling
:func:`readdress`, which gives the other delivery an address of its own. Prose that is wrong
is :func:`amend`'s, below, and an entry that should never have existed is a decision the
author states in the commit that removes it.

**And an update, because insert and delete are not one** (RK124). A `why` written under
pressure is the field most likely to be wrong, and the two doors above are not equivalent to
a correction: `drop` removes the entry and `add` appends a new one under its block, so fixing
a word **moves the line** — a ledger read in the order work landed stops being one, and a
reviewer diffing it sees a deletion and an insertion where a word changed. Worse on a shipped
entry, where `ship` wrote it from a roadmap line that no longer exists to re-derive it from.
:func:`amend` is that update, and it reaches exactly what the roadmap's own `amend` reaches:
the sentence, and never the claim. `symptom` is refused there and absent here for the same
reason, and the two fields this file adds are answered the same way — the **id** is
`renumber`'s, and the **block** is not a field at all, because filing an entry elsewhere is a
move and a flag that pretends nothing happened is the thing this verb exists to stop being.
The one addition is `part`: the qualifier of a partial (RK121) is a phrase that stops being
true, and correcting it is why that comment said `amend` all along.

**And the move that reasoning was right about, which no verb then made** (RK143). That
argument holds and what it left is a hole: `ship` derives the block from the roadmap line it
read, so a line filed under the wrong one ships to the wrong one — and from there `record add
--block` is refused for an id that exists, `drop` wants the id stated twice, `readdress`
changes the address and not the heading. So the only route left was the hand-edit the hook
denies. :func:`move` is the verb that *says* it is a move: the line is taken out and re-placed
under the named heading, **both** positions are reported because the entry does not keep its
number, and a heading the ledger does not declare is refused naming the ones it does — the
heading being `block add`'s to write (RK141). A move is what the diff shows either way, and a
command that names it is not the same as a flag that hides one inside a correction.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from roadkeep import claiming
from roadkeep.authoring import Insertion, place, refuse_reuse, remove_entry
from roadkeep.backlog import Backlog, NotOpen
from roadkeep.config import Config
from roadkeep.document import Document, Entry, Heading, save_all
from roadkeep.ids import next_id
from roadkeep.markers import refresh
from roadkeep.renumbering import NotAnId, SameId, family_of
from roadkeep.schema import PARTIAL, Task
from roadkeep.sections import NoSuchSection, Section, nested, pointers
from roadkeep.sections import drop as drop_section

__all__ = [
    "AlreadyRecorded",
    "AlreadyShipped",
    "Ambiguous",
    "Closure",
    "Corrected",
    "Departure",
    "Divergent",
    "Dropped",
    "NoOutcome",
    "NoQualifier",
    "NoRestatement",
    "NoSuchEntry",
    "NoSuchReplacement",
    "NotDuplicated",
    "NotOpen",
    "NotRecorded",
    "NotRedundant",
    "Partial",
    "PartRecorded",
    "Readdressed",
    "Record",
    "Refiled",
    "Section",
    "Shipment",
    "Unchosen",
    "amend",
    "drop",
    "move",
    "readdress",
    "record",
    "retire",
    "ship",
]


class AlreadyRecorded(ValueError):
    """A second ledger entry for one id is two records of one decision.

    The message names which door the id already went through, because "already in the
    changelog" sends a reader looking for a ✅ that may be a 🗑 (RK32).
    """

    def __init__(self, task_id: str, where: str, lineno: int, marker: str) -> None:
        self.task_id = task_id
        self.lineno = lineno
        self.marker = marker
        super().__init__(
            f"{task_id} is already recorded as {marker} in {where}:{lineno}: a second "
            f"entry would make the ledger disagree with itself about how it left"
        )


#: The names these had when shipping was the only door (RK6), kept because they read
#: better at a `ship` call site: an id can now be retired as well as shipped, and both are
#: the same refusal and the same transaction.
AlreadyShipped = AlreadyRecorded


class NoRestatement(ValueError):
    """`--why` where the ledger is not written (RK62).

    On the closing path the entry already exists and this command deliberately leaves it alone,
    so the sentence has nothing to restate. Refused rather than dropped: a flag silently
    ignored is a flag the caller believes took effect.
    """

    def __init__(self, task_id: str, recorded: Entry) -> None:
        super().__init__(
            f"{task_id} is already recorded as {recorded.task.status} at line "
            f"{recorded.lineno}, so this call only closes its roadmap line: --why restates "
            f"the ledger's sentence, and the ledger is not written here"
        )


class NoOutcome(ValueError):
    """A ledger entry that would inherit the roadmap's problem statement (RK142).

    A roadmap line states a problem; that is what it is for. A ledger entry states an
    **outcome**: what now works. This transaction used to bridge the two by copying the
    `why` across verbatim unless `--why` said otherwise, so the default was the wrong genre
    — and the default is what an author who does not know about the flag gets. Measured in
    Claude Code Tray: a shipped entry reading *"`UsageSample` and `PaceSnapshot` carry four
    numbers and none is overage"*, a defect report filed under a heading meaning "done".

    Refused at input, which is where every other field of every other write is already
    refused (L1). It is the one field that was accepted silently when it was merely the
    wrong sentence — and one argument at the moment the author still has the context beats
    a correction made later by somebody who does not.
    """

    def __init__(self, task_id: str, why: str) -> None:
        self.task_id = task_id
        self.why = why
        super().__init__(
            f"{task_id} needs the outcome it shipped: the roadmap's sentence states the "
            f"problem ({why[:60]}…) and the ledger's states what now works, so it is not "
            f"inherited — pass --why \"…\" while you still have the context to write it"
        )


class Divergent(ValueError):
    """A roadmap line and a ledger entry for one id that describe different work (RK130).

    The reading that opened when closing a still-open line became possible. A transaction
    that stopped after its ledger write wrote that entry **from** this line, so the two state
    the same symptom; two that do not are two tasks that were never one — the merge RK97 is
    about, where one branch shipped under an id another branch had spent.

    Closing that would delete a roadmap line and its rationale section on the strength of an
    entry describing something else, which is a loss no crash caused. `renumber` is the
    repair, and it is the one this refusal names.
    """

    def __init__(
        self, task_id: str, roadmap: str, line: int, ledger: str, entry: int
    ) -> None:
        self.task_id = task_id
        super().__init__(
            f"{roadmap}:{line} and {ledger}:{entry} both carry {task_id} and describe "
            f"different work: an interrupted transaction writes its entry from the line, so "
            f"the two would match — these are two tasks sharing an id, and "
            f"`roadkeep renumber {task_id}` gives the open one an address of its own"
        )


class PartRecorded(ValueError):
    """A retirement against a task whose half the ledger already records (RK129).

    RK121 gave the departure a completion path: an entry carrying a qualifier is not a second
    record of one decision, it is the *first half* of this one, so it is replaced rather than
    added to. That is right for `ship`, whose entry describes the whole of the work the
    partial described part of.

    `retire` reached the same code with a different marker, and there replacing is a
    **deletion**: `✅ **RK1 (local half)**` became `🗑 **RK1** — abandoned: …`, and the
    sentence describing what actually shipped left the only file whose job is to answer what
    happened to this. The two are not one decision — completing says *the rest landed too*
    and superseding that sentence is honest; retiring says *the rest never will*, which
    leaves the half that did ship as history, the kind :func:`drop` refuses to remove even
    when the id is stated twice.

    So the choice is handed back rather than made silently, which is the whole defect: the
    current behaviour made it, and made it in the direction that loses work.
    """

    def __init__(
        self, task_id: str, where: str, lineno: int, part: str, marker: str
    ) -> None:
        self.task_id = task_id
        self.lineno = lineno
        self.part = part
        super().__init__(
            f"{where}:{lineno} already records {marker} {task_id} ({part}), and retiring "
            f"{task_id} would replace that entry: the half that shipped would leave the "
            f"only file that holds it — say what happens to it first (`ship {task_id}` if "
            f"the rest landed after all, or `record amend {task_id} --part \"…\" --why "
            f"\"…\"` to restate the entry as the whole of what ever will)"
        )


class NotRedundant(ValueError):
    """Two entries for one id that are not one entry twice (RK127).

    `drop` reads "duplicate" as "the same work recorded again", which holds when it is a
    slip. Shio's `SH347` is the other kind: one entry records an unplanned fix and ends by
    naming what it left open, the other records exactly that, shipped later — two true
    entries, two deliveries, one id, because the first was written by hand before there was
    a verb to give unplanned work an id of its own. Dropping either destroys a delivery, and
    the one the verb picked is the entry that actually earned the id.

    So the guess is refused rather than defaulted. What the tool can read is whether the two
    entries state the same thing; what it cannot read is whether two that differ are one
    correction or two deliveries, and both doors out of that are the caller's: `--line` says
    which entry goes, and `record renumber` says this one is different work.
    """

    def __init__(self, task_id: str, where: str, linenos: tuple[int, ...]) -> None:
        self.task_id = task_id
        self.linenos = linenos
        lines = ", ".join(str(n) for n in linenos)
        super().__init__(
            f"{where} states {task_id} at {lines}, and those entries do not say the same "
            f"thing: two entries for one id can be one slip or two deliveries, and only a "
            f"reader knows which — `record drop {task_id} --line <n>` removes the one you "
            f"name, `record renumber {task_id} --line <n>` gives the other its own address"
        )


class Unchosen(ValueError):
    """A re-addressing that did not say which of the entries moves (RK127).

    There is no default to fall back on, and that absence is the point: the entry that
    earned the id from a roadmap line is the one to leave alone, and nothing in the file
    says which that is. So the candidates are named and the caller picks.
    """

    def __init__(self, task_id: str, where: str, linenos: tuple[int, ...]) -> None:
        self.task_id = task_id
        self.linenos = linenos
        lines = ", ".join(str(n) for n in linenos)
        super().__init__(
            f"{where} states {task_id} at {lines} and which of them moves is yours to say: "
            f"pass --line <n>, leaving the entry the rest of the repository already names"
        )


class NoSuchEntry(KeyError):
    """A line number that is not one of the entries for this id (RK127).

    Named rather than ignored, because the caller is choosing between two lines they were
    just shown: an off-by-one that silently fell back to "the later one" would be the same
    guess this door exists to stop making.
    """

    def __init__(self, task_id: str, lineno: int, linenos: tuple[int, ...]) -> None:
        self.task_id = task_id
        self.lineno = lineno
        lines = ", ".join(str(n) for n in linenos)
        super().__init__(
            f"line {lineno} is not an entry for {task_id} (it is at {lines})"
        )


class NotDuplicated(ValueError):
    """`drop` against an id the ledger does not state twice (RK67).

    The narrow condition is this door's whole safety: de-duplicating is the one removal that
    cannot lose a decision, because the decision stays on the line the reader already found.
    So the message names the count it *did* find — "not a duplicate" reads as "no such entry"
    when it is one entry, which is the case where the author has to hear the difference.
    """

    def __init__(self, task_id: str, where: str, linenos: tuple[int, ...]) -> None:
        self.task_id = task_id
        self.linenos = linenos
        found = f"once, at line {linenos[0]}" if linenos else "nowhere"
        super().__init__(
            f"{task_id} is in {where} {found}: this removes the later of two entries for one "
            f"id, and the only record of a decision is history rather than a duplicate"
        )


class NotRecorded(KeyError):
    """An id the ledger does not carry, at the one door that only reads the ledger (RK124).

    Distinct from :class:`~roadkeep.backlog.NotOpen`, which is about the roadmap: a caller
    correcting an entry is holding the ledger's own address, and being told "not open" would
    send them to the file where it correctly is not.
    """

    def __init__(self, task_id: str, where: str, *, open_line: bool) -> None:
        self.task_id = task_id
        elsewhere = (
            " — it is an open roadmap line, and `amend` is the verb for one"
            if open_line
            else ""
        )
        super().__init__(f"{task_id} is not in {where}{elsewhere}")


class Ambiguous(ValueError):
    """A write against a single entry, on an id the ledger states twice (RK124, RK143).

    Refused rather than applied to one of them: which entry a `--why` — or a `--to-block` —
    was written about is the one thing this transaction cannot read, and the two may be two
    different pieces of work sharing an id (RK127). `record drop` is the door for a real
    duplicate; a reader who has two decisions here needs to decide that first.

    Shared by both doors that address one entry by its id alone, and the reason neither takes
    a `--line` the way `drop` and `readdress` do: there the choice *is* the fix, and here two
    entries under one id is a defect to resolve before either of them is rewritten.
    """

    def __init__(self, task_id: str, where: str, linenos: tuple[int, ...]) -> None:
        self.task_id = task_id
        self.linenos = linenos
        lines = ", ".join(str(n) for n in linenos)
        super().__init__(
            f"{where} states {task_id} at {len(linenos)} lines ({lines}): which of them "
            f"this call is about is not a fact any file holds — de-duplicate it first"
        )


class NoQualifier(ValueError):
    """`--part` against an entry that records a whole shipment (RK121, RK124).

    The qualifier is written by `ship --part` and removed by the completion, so this door
    only ever *corrects* the phrase. Adding one here would make an entry claim a partial
    delivery while the roadmap line it was written from is gone or closed.
    """

    def __init__(self, task_id: str, lineno: int) -> None:
        self.task_id = task_id
        super().__init__(
            f"{task_id} at line {lineno} carries no qualifier, so there is none to "
            f"correct: `ship --part` is what writes one, on a line that is still open"
        )


class NoSuchReplacement(KeyError):
    """A forward pointer to an id that is in neither file (RK32).

    Refused, because a pointer to nothing is the exact defect this records against: the
    reader of the gap would be sent somewhere else that does not explain it either.
    """

    def __init__(self, replacement: str, task_id: str) -> None:
        super().__init__(
            f"{replacement} is in neither file, so it cannot be what replaces "
            f"{task_id}: retire it against an id that exists, or as abandoned"
        )


@dataclass(frozen=True, slots=True)
class Departure:
    """Every edit one line's departure makes, as data, before or after it is written.

    One shape for both doors (RK6, RK32): the marker is the only thing that differs, and a
    second dataclass would be a second place to add the next field to.
    """

    task_id: str
    ledger: Insertion
    roadmap: Document
    removed_from: int
    improvements: Document | None = None
    dropped: Section | None = None
    #: Why nothing was dropped, when nothing was: a task can ship without a rationale
    #: section, and silence about that would read as a section that was deleted.
    kept: str | None = None
    #: The anchors that went with it, nested under the one named (RK78). Reported because a
    #: drop is a subtree, and a transaction that says "one section" about five is one whose
    #: size the author only learns from the diff.
    nested: tuple[str, ...] = ()
    #: Open lines whose `(deps: …)` this write made true again (RK8).
    refreshed: tuple[str, ...] = ()
    #: The marker the ledger line carries: ✅ shipped, 🗑 retired.
    marker: str = ""
    #: Open lines that still name this id. Reported and not refused: a supersession is
    #: legitimate and those lines are the author's next edit, which `lint` (RK14) gates.
    dependents: tuple[str, ...] = ()
    #: The checkout, so the claim on a line that left for good is released (RK162) — the one
    #: thing this transaction touches that is not a governed file.
    root: Path | None = None

    def save(self) -> None:
        """Write the files. Nothing here can fail on the format — that was decided.

        What can still fail is the disk: all three files are rendered to their scratch
        names, then asked whether they are still the files that were read, and only then
        renamed into place (RK116, RK131), each write landing whole (RK118). Three renames
        are still three moments, so **the order is the rest of the answer** — it decides
        which halfway states a crash can leave:

        * **Ledger first**, because it is the only one of the three that records that this
          shipped. Stopping here leaves the id in two files, which `lint` reports as
          `id.two-files`. Reversed, stopping after the roadmap would remove the line while
          nothing recorded where it went — the task simply gone, and no gate able to say so,
          because a roadmap with one fewer line is a roadmap.
        * **Roadmap second.** Stopping here leaves a rationale section nothing points at,
          which `lint` reports as an orphan (RK15) and `section drop` removes.
        * **The rationale file last**, because its write is the only *deletion*. Earlier, it
          would take the design out while the line still named it: a pointer to nothing, and
          prose recoverable only from git.

        So the bar every reachable middle state clears is the same one: **loud and
        lossless** — every file still holds what it held, and the gate names the state.
        Nothing here claims the three writes are one; what is claimed is that stopping
        between them costs a command and never a design.
        """
        save_all(self.ledger.document, self.roadmap, self.improvements)
        if self.root is not None:
            # Last, and never a condition of the writes: a terminal marker is not the
            # in-progress one, so the rule every marker write obeys says *release* (RK162).
            # The entry is inert either way — an id is never reused — but a row that can never
            # mean anything is noise in the listing `claims` exists to be read (RK161).
            claiming.follow(self.root, self.task_id, self.marker, self.roadmap.entries)


Shipment = Departure


@dataclass(frozen=True, slots=True)
class Partial:
    """Half a departure: the ledger records what landed, the roadmap keeps the line (RK121).

    The third state the model did not have. Open in the roadmap and recorded in the ledger
    were the only two, so work delivered in halves was neither — and every project using
    this invented the same escape, a parenthetical on the ledger id that the grammar could
    not read. This is that escape given a verb, which is the half that can be *maintained*:
    only a command knows when the qualifier stops being true, and :func:`ship` completing
    the line is what removes it.

    Not a :class:`Departure` with a flag: a departure's subject is a line that left, and
    this one's is a line that stayed. Nothing is removed and nothing is deleted — in
    particular the rationale section stays, because the design still has work left to
    describe.
    """

    task_id: str
    ledger: Insertion
    #: The roadmap as this write leaves it: the same line, marked ⏳ where the project
    #: declares that marker, and every dependent's annotation re-derived from it (RK8).
    roadmap: Document
    part: str
    #: What the roadmap line's marker became — ⏳, or the one it already carried at a
    #: project that declares no such marker. Reported because the two differ and a caller
    #: reading "partial" would otherwise not know which of them happened.
    status: str = ""
    refreshed: tuple[str, ...] = ()
    #: The marker the ledger entry carries: ✅, on the part that shipped.
    marker: str = ""

    def save(self) -> None:
        # The ledger first, as everywhere else (RK118): the record of what landed is the
        # thing that cannot be reconstructed, and a marker not yet ⏳ is a state a second
        # run of the same command corrects.
        save_all(self.ledger.document, self.roadmap)


@dataclass(frozen=True, slots=True)
class Closure:
    """The rest of a transaction that never completed (RK62).

    A roadmap line whose id the ledger *already* records has nowhere to go: `ship` cannot write
    a second entry, `retire` would claim a departure that did not happen, and the hook denies
    the hand-edit. So closing the line is its own outcome — the same edits a departure makes
    minus the one that is already done, and the ledger is opened only to be read.

    Not a :class:`Departure` with a None: the field that would be None is the entry, which is
    the whole subject of that shape. Here the entry is the *evidence*, and it is somebody
    else's write.
    """

    task_id: str
    #: The roadmap as this write leaves it: without the line, dependents re-annotated.
    roadmap: Document
    removed_from: int
    #: The ledger entry that already existed, and its marker — ✅ or 🗑, because a reader has
    #: to know which door this id went through before its line was left behind.
    recorded: Entry
    improvements: Document | None = None
    dropped: Section | None = None
    kept: str | None = None
    #: The anchors nested under the one dropped, as :class:`Departure` reports them (RK78).
    nested: tuple[str, ...] = ()
    refreshed: tuple[str, ...] = ()
    dependents: tuple[str, ...] = ()

    @property
    def marker(self) -> str:
        return self.recorded.task.status

    def save(self) -> None:
        """Write the roadmap and the prose file. The ledger is never opened for writing."""
        save_all(self.roadmap, self.improvements)


@dataclass(frozen=True, slots=True)
class Record:
    """A ledger entry that had no roadmap line to leave (RK41).

    Not a :class:`Departure`: there is no line removed, no section dropped and no
    `removed_from` to report, and a shared shape would carry three fields that are
    permanently None plus the invitation to make them meaningful later.
    """

    task_id: str
    ledger: Insertion
    #: The roadmap as this write leaves it — the same document unless an annotation
    #: elsewhere became derivable (RK8), which is what :attr:`refreshed` names.
    roadmap: Document
    refreshed: tuple[str, ...] = ()
    #: The marker the entry carries: ✅, the only one a record can mean.
    marker: str = ""

    def save(self) -> None:
        """Write the ledger, and the roadmap only if a line in it actually changed."""
        # The roadmap is passed only where a line in it changed, so it is not rewritten to
        # the same bytes: an untouched file with a moved mtime reads as an edit to every
        # hook watching it, and "touched nothing else" has to be true on disk.
        save_all(self.ledger.document, self.roadmap if self.refreshed else None)


@dataclass(frozen=True, slots=True)
class Dropped:
    """One of two ledger entries for a single id, removed (RK67).

    No roadmap field, and that is the shape of the guarantee rather than an omission: an id
    the ledger still records once is an id every annotation elsewhere is still true about, so
    there is nothing to re-derive (RK8) and no second file to open. :class:`Record` had to say
    "touched nothing else" in a docstring; here there is nothing that could.
    """

    task_id: str
    #: The ledger as this write leaves it: one entry for the id, and no doubled blank.
    ledger: Document
    removed_from: int
    #: The line the decision keeps, and the marker it carries there — printed, because a
    #: duplicate whose two entries disagree about the door is a fact the author has to see.
    kept: int
    kept_marker: str
    #: The block the ledger still files this decision under — the kept entry's, since that is
    #: the one that is left to answer for it.
    block: str = ""
    #: The marker the removed entry carried, which is normally the same one.
    marker: str = ""

    def save(self) -> None:
        """Write the ledger. Nothing else was opened, so nothing else can be touched."""
        self.ledger.save()


@dataclass(frozen=True, slots=True)
class Corrected:
    """One ledger entry rewritten where it stands (RK124).

    No `removed_from` and no insertion, which is the whole shape of the claim: the line
    keeps its number, so the ledger still reads in the order work landed and the diff shows
    a word. Nothing else is opened either — a `why` is prose, and no annotation anywhere is
    derived from it.
    """

    task_id: str
    #: The ledger as this write leaves it: one line rewritten, everything else verbatim.
    ledger: Document
    entry: Entry
    #: Which fields moved — empty when the entry already read that way, so a caller can
    #: tell "corrected" from "already correct" without diffing the file.
    changed: tuple[str, ...] = ()

    @property
    def rendered(self) -> str:
        return self.entry.raw

    @property
    def lineno(self) -> int:
        return self.entry.lineno

    def save(self) -> None:
        """Write the ledger. Nothing else was opened, so nothing else can be touched."""
        self.ledger.save()


def amend(
    config: Config, task_id: str, *, why: str | None = None, part: str | None = None
) -> Corrected:
    """Correct one ledger entry's sentence, or a partial's qualifier, in place (RK124).

    Validated before the write exactly as `record add` validates its fields (L1), against
    the ledger's own schema — so an over-length `why` is refused with the number, and the
    line that reaches disk is one this tool can read back (L3).

    Refused on an id the ledger states twice: which of two entries a correction was written
    about is not a fact any file holds, and `record drop` is the door for a duplicate.
    """
    ledger = config.document("changelog")
    where = config.relative(config.path("changelog"))
    twins = tuple(entry for entry in ledger.entries if entry.task.id == task_id)
    if not twins:
        raise NotRecorded(
            task_id, where, open_line=task_id in config.document("roadmap").by_id()
        )
    if len(twins) > 1:
        raise Ambiguous(task_id, where, tuple(entry.lineno for entry in twins))

    entry = twins[0]
    if part is not None and entry.task.part is None:
        raise NoQualifier(task_id, entry.lineno)

    wanted = replace(
        entry.task,
        why=entry.task.why if why is None else why,
        part=entry.task.part if part is None else part,
    )
    changed = tuple(
        name
        for name, before, after in (
            ("why", entry.task.why, wanted.why),
            ("part", entry.task.part, wanted.part),
        )
        if before != after
    )
    if not changed:
        return Corrected(task_id=task_id, ledger=ledger, entry=entry)

    document = ledger.replace_task(entry, ledger.schema.check(wanted))
    return Corrected(
        task_id=task_id,
        ledger=document,
        entry=document.by_id()[task_id],
        changed=changed,
    )


@dataclass(frozen=True, slots=True)
class Refiled:
    """One ledger entry taken out from under one heading and re-placed under another (RK143).

    The shape is the difference from :class:`Corrected`, and it is the whole argument for
    this being a verb rather than a flag on that one: **two positions**, because the line
    does not keep its number and a report that named one would be the pretence `amend`
    refused to make. The ledger and nothing else is opened, for the reason :class:`Dropped`
    is — a block says where an entry is filed and not what it records, so no annotation, dep
    or pointer anywhere is derived from it.
    """

    task_id: str
    #: The ledger as this write leaves it: the line gone from one block and re-placed under
    #: the other, and the blank a block emptied by the removal no longer needs.
    ledger: Document
    entry: Entry
    from_block: str
    to_block: str
    #: The line it was filed on, which is the half a caller cannot read off the file after.
    from_line: int

    @property
    def moved(self) -> bool:
        """False where the entry was already filed there, and then nothing was written."""
        return self.from_block != self.to_block

    @property
    def rendered(self) -> str:
        return self.entry.raw

    @property
    def lineno(self) -> int:
        return self.entry.lineno

    def save(self) -> None:
        """Write the ledger. Nothing else was opened, so nothing else can be touched."""
        self.ledger.save()


def move(config: Config, task_id: str, *, to_block: str) -> Refiled:
    """Re-file one ledger entry under another block heading (RK143).

    The door :func:`amend` was right to leave shut and nothing else opened. `ship` files an
    entry under the block its roadmap line sat in, so a line filed wrongly ships wrongly —
    and every other verb here declines the repair for a reason of its own: `record add`
    refuses an id that exists, `drop` wants the id stated twice, :func:`readdress` changes
    the address and not the heading. What was left was the hand-edit the guard denies.

    Nothing is written until everything validates, as everywhere on the write path (L1): the
    line is removed and re-placed in memory, so a heading the ledger does not declare raises
    :class:`~roadkeep.authoring.UnknownBlock` — naming the labels it *does* — over a file
    still holding every byte it held. Re-placed and not spliced, so the entry lands after the
    destination's last one exactly as any other write to that block would leave it.

    Refused on an id the ledger states twice, for the reason :func:`amend` is: which of two
    entries a move was meant for is not a fact any file holds.
    """
    ledger = config.document("changelog")
    where = config.relative(config.path("changelog"))
    twins = tuple(entry for entry in ledger.entries if entry.task.id == task_id)
    if not twins:
        raise NotRecorded(
            task_id, where, open_line=task_id in config.document("roadmap").by_id()
        )
    if len(twins) > 1:
        raise Ambiguous(task_id, where, tuple(entry.lineno for entry in twins))

    entry = twins[0]
    if entry.task.block == to_block:
        # Already there. Reported rather than refused, and the file is not rewritten to the
        # same bytes: an unchanged file with a moved mtime reads as an edit to every hook
        # watching it, which is the rule `amend`'s no-op path holds too.
        return Refiled(
            task_id=task_id,
            ledger=ledger,
            entry=entry,
            from_block=entry.task.block,
            to_block=to_block,
            from_line=entry.lineno,
        )
    # The whole entry moves, continuation lines included (RK157): the schema renders one line
    # and a wrapped entry's remaining lines are prose no task holds, so a move that re-rendered
    # alone would take the paragraph out of the file in the name of re-filing it.
    carrying = tuple(
        line.rstrip("\r\n") for line in ledger.lines[entry.lineno : entry.stop]
    )
    insertion = place(
        remove_entry(ledger, entry),
        replace(entry.task, block=to_block),
        carrying=carrying,
    )
    return Refiled(
        task_id=task_id,
        ledger=insertion.document,
        entry=insertion.entry,
        from_block=entry.task.block,
        to_block=to_block,
        from_line=entry.lineno,
    )


@dataclass(frozen=True, slots=True)
class Readdressed:
    """One of two entries for an id, given an address of its own (RK127).

    The ledger and nothing else, and the entry does not move: it keeps its line, so the file
    still reads in the order work landed and the diff is the number. Nothing elsewhere is
    re-derived either — every `(deps: <id> ✅)` in the backlog was written about the entry
    that keeps the id, which is the one this leaves alone.
    """

    task_id: str
    to: str
    ledger: Document
    entry: Entry
    #: The line that keeps the original id — the delivery the rest of the repository names.
    kept: int
    kept_marker: str = ""

    @property
    def rendered(self) -> str:
        return self.entry.raw

    @property
    def lineno(self) -> int:
        return self.entry.lineno

    def save(self) -> None:
        """Write the ledger. Nothing else was opened, so nothing else can be touched."""
        self.ledger.save()


def drop(config: Config, task_id: str, *, lineno: int | None = None) -> Dropped:
    """Remove one of two ledger entries for an id, and never guess which (RK67, RK127).

    Refused unless the id is recorded **twice**, so the operation is de-duplication and can
    never be a deletion of history: what stays is the first entry, where a reader who already
    found this decision found it. With three, the last goes and a second call is the next one —
    convergent by construction, rather than one command that decides how many to remove.

    And refused again unless the entries **say the same thing**. "Duplicate" reads as "the
    same work recorded again", which is a slip; two entries that state different outcomes are
    two deliveries that were never one, and dropping either destroys one of them (RK127). The
    reader who has both in front of them says which with `lineno`, and the entry they name is
    the one that goes — including the first, which the default never picks.

    The whole write is the ledger, which is what makes this narrow enough to exist at all: no
    dep annotation changes when an id the file still records goes from two entries to one.
    """
    ledger = config.document("changelog")
    where = config.relative(config.path("changelog"))
    twins = tuple(entry for entry in ledger.entries if entry.task.id == task_id)
    if len(twins) < 2:
        raise NotDuplicated(task_id, where, tuple(entry.lineno for entry in twins))

    linenos = tuple(entry.lineno for entry in twins)
    if lineno is None:
        if not _one_entry_twice(twins):
            raise NotRedundant(task_id, where, linenos)
        going = twins[-1]
    else:
        found = next((entry for entry in twins if entry.lineno == lineno), None)
        if found is None:
            raise NoSuchEntry(task_id, lineno, linenos)
        going = found

    kept = next(entry for entry in twins if entry.lineno != going.lineno)
    return Dropped(
        task_id=task_id,
        ledger=remove_entry(ledger, going),
        removed_from=going.lineno,
        kept=kept.lineno,
        kept_marker=kept.task.status,
        block=kept.task.block,
        marker=going.task.status,
    )


def readdress(
    config: Config, task_id: str, *, lineno: int | None = None, to: str | None = None
) -> Readdressed:
    """Give one of two entries for an id an address of its own (RK127).

    The counterpart of `renumber` (RK97) for the file that verb deliberately never opens —
    and the reason the two are not one door is the reason it does not: renumbering a *record*
    is how a `git log -S` starts returning two unrelated designs. That argument holds for an
    id one entry carries. It inverts for an id two carry, because the collision is already
    what makes the history unreadable, and until one of them has its own number there is no
    query that separates them.

    So it is refused on anything but a collision, and which of the entries moves is the
    caller's: the one that earned the id from a roadmap line is normally the one to leave
    alone, and nothing in the file says which that is.
    """
    ledger = config.document("changelog")
    where = config.relative(config.path("changelog"))
    twins = tuple(entry for entry in ledger.entries if entry.task.id == task_id)
    if len(twins) < 2:
        raise NotDuplicated(task_id, where, tuple(entry.lineno for entry in twins))

    linenos = tuple(entry.lineno for entry in twins)
    if lineno is None:
        raise Unchosen(task_id, where, linenos)
    going = next((entry for entry in twins if entry.lineno == lineno), None)
    if going is None:
        raise NoSuchEntry(task_id, lineno, linenos)

    if to is None:
        to = next_id(config, family_of(config, task_id))
    if to == task_id:
        raise SameId(task_id)
    if not config.schema.id_pattern().match(to):
        raise NotAnId(to, config.schema.id_pattern().pattern)
    refuse_reuse(config, to)

    document = ledger.replace_task(going, ledger.schema.check(replace(going.task, id=to)))
    kept = next(entry for entry in twins if entry.lineno != going.lineno)
    return Readdressed(
        task_id=task_id,
        to=to,
        ledger=document,
        entry=document.by_id()[to],
        kept=kept.lineno,
        kept_marker=kept.task.status,
    )


def _one_entry_twice(twins: tuple[Entry, ...]) -> bool:
    """Do these entries state the same thing, id and position aside?

    What the tool can read, and the whole of it: a slip records the same work again, so the
    marker, the symptom, the sentence and any qualifier all match. Anything else is a
    difference somebody wrote on purpose, and reading prose to decide whether it was a
    correction or a second delivery is the judgement L4 keeps out of this tool.

    The **block** is deliberately not compared. It says where the entry was filed and not
    what it records, and the same entry appearing under two headings is exactly the slip
    this door was written for.
    """
    stated = {(t.task.status, t.task.symptom, t.task.why, t.task.part) for t in twins}
    return len(stated) == 1


def ship(
    config: Config, task_id: str, *, why: str | None = None, part: str | None = None
) -> Departure | Closure | Partial:
    """Move one task from the backlog to the ledger. Validates all three edits first.

    Or, when the ledger already records the id, close the roadmap line alone (RK62): that is
    not a second entry, it is the rest of a transaction that never completed — which is the
    shape adoption produces, because a project that moved a task to its changelog by hand and
    left a pointer behind was following its own convention.

    `why` is refused on that path rather than ignored: it restates the *ledger's* sentence, and
    the ledger is not written here. A flag silently dropped is a flag the caller believes took
    effect.

    `part` is the third answer (RK121): **this much of it landed**. The entry is written with
    the qualifier and the roadmap line stays, because the work is not finished. A later
    `ship` with no `part` *completes* it — replacing the entry rather than adding a second —
    which is the whole reason this is a verb and not a spelling convention: only a command
    knows when "local half" stopped being true.
    """
    if part is not None:
        return _partial(config, task_id, part, why)
    recorded = _already_recorded(config, task_id)
    if recorded is None:
        return _depart(config, task_id, config.schema.shipped_marker, why)
    if why is not None:
        raise NoRestatement(task_id, recorded)
    return _close(config, task_id, recorded)


def retire(
    config: Config,
    task_id: str,
    *,
    reason: str,
    superseded_by: str | None = None,
) -> Departure:
    """Record a line leaving without shipping: superseded by a named id, or abandoned.

    The `why` is a derived prefix plus the author's own sentence — the same split as every
    other field the tool fills in (RK8): "superseded by RK41" is a fact this command holds
    and the reason is prose it will not write (L4).
    """
    if superseded_by is not None:
        if superseded_by == task_id:
            raise NoSuchReplacement(superseded_by, task_id)
        known = set(config.document("roadmap").by_id())
        if config.has("changelog") and config.path("changelog").is_file():
            known |= set(config.document("changelog").by_id())
        if superseded_by not in known:
            raise NoSuchReplacement(superseded_by, task_id)
        why = f"superseded by {superseded_by}: {reason}"
    else:
        why = f"abandoned: {reason}"
    return _depart(config, task_id, config.schema.retired_marker, why)


def record(
    config: Config,
    *,
    block: str,
    symptom: str,
    why: str,
    task_id: str | None = None,
) -> Record:
    """Write a ledger entry for work that shipped without ever being planned (RK41).

    The fields are refused at input exactly as `add` refuses them (L1), against
    :meth:`~roadkeep.schema.Schema.as_ledger` rather than the roadmap's schema — so the
    marker is ✅, the block heading must already be declared in the ledger, and a dep or a
    pointer is not accepted rather than dropped: there is no open line for a dep to be a
    planning fact about, and no rationale section for a pointer to resolve to.

    The id is derived like any other (RK4) and refused if anything anywhere already
    mentions it, so recording cannot quietly claim an id the roadmap is holding. The
    `symptom` rule is the one that must not soften: what did not work, stated so it could
    have been falsified — never the name of the patch that closed it (L4 leaves that to
    the caller, here as everywhere).
    """
    if task_id is None:
        task_id = next_id(config)
    else:
        refuse_reuse(config, task_id)

    ledger = config.document("changelog")
    marker = config.schema.shipped_marker
    insertion = place(
        ledger,
        Task(id=task_id, status=marker, block=block, symptom=symptom, why=why),
    )
    # Resolved against the state this write creates, for the same reason `_depart` does it
    # (RK8): an id is normally too new for any line to name, but a range dep can already
    # span it, and an annotation left un-derived by one door is one nothing revisits.
    derived = refresh(
        Backlog.during(
            config, roadmap=config.document("roadmap"), ledger=insertion.document
        )
    )
    return Record(
        task_id=task_id,
        ledger=insertion,
        roadmap=derived.document,
        refreshed=derived.changed,
        marker=marker,
    )


def _partial(
    config: Config, task_id: str, part: str, why: str | None
) -> Partial:
    """Record the half that landed and leave the line open (RK121)."""
    roadmap = config.document("roadmap")
    ledger = config.document("changelog")

    entry = roadmap.by_id().get(task_id)
    if entry is None:
        raise NotOpen(
            task_id,
            config.relative(config.path("roadmap")),
            shipped=task_id in ledger.by_id(),
        )
    recorded = ledger.by_id().get(task_id)
    if recorded is not None:
        # A second partial would state the id twice in the ledger, which `lint` reports as
        # `id.duplicate` and which is the shape RK127 is about. One partial per task and
        # then a completion: `amend` is where a qualifier that has changed is corrected.
        raise AlreadyRecorded(
            task_id,
            config.relative(config.path("changelog")),
            recorded.lineno,
            recorded.task.status,
        )

    if why is None:
        # A partial states an outcome too — this much of it works — so the half that
        # landed is no more entitled to the problem statement than the whole (RK142).
        raise NoOutcome(task_id, entry.task.why)
    landed = replace(
        _as_recorded(entry.task, config.schema.shipped_marker, why), part=part
    )
    insertion = place(ledger, landed)
    # ⏳ where the project declares it, and the line's own marker where it does not: the
    # marker set is the project's (L6), and a command that invented one would write a line
    # its own gate refuses. Either way the line stays open, which is the claim.
    status = PARTIAL if PARTIAL in config.schema.markers else entry.task.status
    remaining = roadmap.replace_task(entry, replace(entry.task, status=status))
    derived = refresh(
        Backlog.during(config, roadmap=remaining, ledger=insertion.document)
    )
    return Partial(
        task_id=task_id,
        ledger=insertion,
        roadmap=derived.document,
        part=part,
        status=status,
        refreshed=derived.changed,
        marker=config.schema.shipped_marker,
    )


def _depart(
    config: Config, task_id: str, marker: str, why: str | None
) -> Departure:
    """The one transaction both doors are: validate everything, then write nothing yet."""
    roadmap = config.document("roadmap")
    ledger = config.document("changelog")

    entry = roadmap.by_id().get(task_id)
    if entry is None:
        raise NotOpen(
            task_id,
            config.relative(config.path("roadmap")),
            shipped=task_id in ledger.by_id(),
        )
    where = config.relative(config.path("changelog"))
    duplicate = ledger.by_id().get(task_id)
    # A duplicate carrying a qualifier is not a second record of one decision — it is the
    # *first* half of this one (RK121), and a **ship** is the completion. So the entry is
    # replaced rather than added to, which is what keeps "local half" from outliving the
    # local half: five of the corpus's thirteen say something that stopped being true.
    #
    # Only a ship. `retire` reaches this same transaction with a different marker, and there
    # the replacement is a deletion of the record that a half landed (RK129) — the one
    # decision this module hands back rather than making.
    completing = (
        duplicate
        if duplicate is not None
        and duplicate.task.part
        and marker == config.schema.shipped_marker
        else None
    )
    if duplicate is not None and completing is None:
        if duplicate.task.part:
            raise PartRecorded(
                task_id, where, duplicate.lineno, duplicate.task.part, duplicate.task.status
            )
        raise AlreadyRecorded(task_id, where, duplicate.lineno, duplicate.task.status)
    if why is None:
        # `retire` always arrives with a derived sentence, so this is the ship path alone.
        raise NoOutcome(task_id, entry.task.why)

    recorded = _as_recorded(entry.task, marker, why)
    if completing is not None:
        replaced = ledger.replace_task(completing, recorded)
        insertion = Insertion(document=replaced, entry=replaced.by_id()[task_id])
    else:
        insertion = place(ledger, recorded)
    remaining = remove_entry(roadmap, entry)
    improvements, dropped, kept, taken = _drop_section(
        config, entry.task.ref, leaving=task_id
    )
    # Resolved against the state this write *creates* — the id is in the ledger and gone
    # from the roadmap — so a dependent's annotation is derived from what will be on
    # disk and not from what was (RK8).
    derived = refresh(
        Backlog.during(config, roadmap=remaining, ledger=insertion.document)
    )

    return Departure(
        task_id=task_id,
        ledger=insertion,
        roadmap=derived.document,
        removed_from=entry.lineno,
        improvements=improvements,
        dropped=dropped,
        kept=kept,
        nested=taken,
        refreshed=derived.changed,
        marker=marker,
        dependents=tuple(
            e.task.id for e in derived.document.entries if task_id in e.task.dep_ids
        ),
        root=config.root,
    )


def _others_pointing(config: Config, anchor: str, leaving: str) -> tuple[str, ...]:
    """Open lines other than this one whose pointer names the same anchor (RK64)."""
    return tuple(
        entry.task.id
        for entry in config.document("roadmap").entries
        if entry.task.ref == anchor and entry.task.id != leaving
    )


def _already_recorded(config: Config, task_id: str) -> Entry | None:
    """The ledger entry this roadmap line was left behind by, or None if it is not one.

    A ledger entry and a roadmap line for one id is *several* different situations, and only
    some of them are a leftover. Two answers, read off two different sides:

    * **The roadmap's** (RK62). A line carrying a marker the roadmap may not carry — ✅ or 🗑
      — was already treated as gone, which is the shape adoption produces: a project that
      moved a task to its changelog by hand and left a pointer behind.
    * **The ledger's** (RK130). RK118 ordered a departure's writes so the ledger goes first,
      which makes stopping between them *loud and lossless* — `id.two-files` names it — and
      left no way out: `ship` refused the id, this function's roadmap-side condition did not
      match a line still marked 📋, and `record drop` wants a second entry. So an entry for a
      line that is still open is a leftover **unless the files say it is a live partial**,
      which is the distinction RK121 made representable: a ⏳ line, or an entry naming a
      half. Shio's `⏳ SH238` is the first of those and stays :class:`AlreadyRecorded` — the
      case where widening this cost a real task and a 224-word section.

    And a refusal, because widening it opened one more reading. An interrupted transaction
    wrote its entry **from this line**, so the two state the same symptom; two that do not are
    two tasks sharing an id (RK97), and closing one of them would delete work no crash
    touched. Compared only where the ledger carries a symptom at all: a file with no such
    slot holds no fact to tell them apart, and the marker and the qualifier are then the whole
    of what the files say.
    """
    if not config.has("changelog") or not config.path("changelog").is_file():
        return None
    open_line = config.document("roadmap").by_id().get(task_id)
    if open_line is None:
        return None
    ledger = config.document("changelog")
    recorded = ledger.by_id().get(task_id)
    if recorded is None:
        return None

    schema = config.schema
    if open_line.task.status in (schema.shipped_marker, schema.retired_marker):
        return recorded
    if open_line.task.status == PARTIAL or recorded.task.part:
        return None
    if (
        ledger.schema.symptom_field
        and open_line.task.symptom != recorded.task.symptom
    ):
        raise Divergent(
            task_id,
            config.relative(config.path("roadmap")),
            open_line.lineno,
            config.relative(config.path("changelog")),
            recorded.lineno,
        )
    return recorded


def _close(config: Config, task_id: str, recorded: Entry) -> Closure:
    """Everything a departure does except the entry, which is already on disk (RK62)."""
    roadmap = config.document("roadmap")
    entry = roadmap.by_id()[task_id]
    remaining = remove_entry(roadmap, entry)
    improvements, dropped, kept, taken = _drop_section(
        config, entry.task.ref, leaving=task_id
    )
    derived = refresh(
        Backlog.during(config, roadmap=remaining, ledger=config.document("changelog"))
    )
    return Closure(
        task_id=task_id,
        roadmap=derived.document,
        removed_from=entry.lineno,
        recorded=recorded,
        improvements=improvements,
        dropped=dropped,
        kept=kept,
        nested=taken,
        refreshed=derived.changed,
        dependents=tuple(
            e.task.id for e in derived.document.entries if task_id in e.task.dep_ids
        ),
    )


def _as_recorded(task: Task, marker: str, why: str | None) -> Task:
    """The same task as the ledger states it: one marker, no deps, no pointer.

    The pointer is dropped because the section it names is deleted in the same command,
    and the deps because a dependency is a planning fact that a departed line has none
    left to state — both of which the ledger schema (`as_ledger`) already refuses.
    """
    return replace(
        task,
        status=marker,
        deps=(),
        ref=None,
        why=why if why is not None else task.why,
        # And at column zero (RK49): the nesting said which roadmap line this one belonged
        # under, and that line is not in the ledger — an indented entry would be nested
        # beneath whatever entry happened to precede it.
        indent="",
    )


def _drop_section(
    config: Config, anchor: str | None, *, leaving: str = ""
) -> tuple[Document | None, Section | None, str | None, tuple[str, ...]]:
    """Delete the rationale section the departing line pointed at, if it is only that line's.

    Absence is reported, never refused: a task can ship without a section, and a command
    that fails over it would be an obstacle at the one moment the author is finishing.

    So is a section with **more than one owner** (RK64). Under `ref_scheme = "id"` the anchor
    is the id and nothing else can name it; under an outline, four of Shio's lines point at one
    epic design, and deleting it when the first of them ships left three live pointers resolving
    to nothing. The section stays and the reason is reported in the same field.

    A section **nesting** one of those is the same fact one level down, and it is a refusal
    rather than a report (RK78): keeping the section is a legitimate outcome of shipping,
    while a subtree that cannot be deleted whole is a transaction the author has to resolve —
    so :class:`~roadkeep.sections.SectionOccupied` propagates, and by the ordering this module
    already guarantees, no file has been touched when it does. What the drop *did* take is
    returned with it, because a deletion that reports one section and removes five is how the
    same defect stayed invisible for 160 lines.
    """
    if anchor is None:
        return None, None, "the line carried no pointer", ()
    if not config.has("improvements"):
        return None, None, "this project declares no improvements file", ()
    others = _others_pointing(config, anchor, leaving)
    if others:
        return None, None, f"§{anchor} is also pointed at by {', '.join(others)}", ()
    # The grammar of a section lives in one place (RK9), so shipping calls it rather than
    # keeping a second opinion about where a section ends.
    improvements = config.document("improvements")
    taken = tuple(child.anchor for child in nested(improvements, anchor))
    try:
        document, section = drop_section(
            improvements, anchor, claimed=pointers(config, leaving=leaving)
        )
    except NoSuchSection:
        return (
            None,
            None,
            f"no §{anchor} section in {config.relative(config.path('improvements'))}",
            (),
        )
    return document, section, None, taken


