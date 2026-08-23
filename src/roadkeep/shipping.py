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

**And the design it deletes can have been overtaken, which nothing recorded** (RK310). The
third of the three edits is a deletion, and it was silent about the one thing worth knowing:
a section is written when a task is filed and read when somebody claims it, and in between
the codebase moves. Measured in one block of eleven tasks, twice — a section proposing a
field the implementation found unnecessary, another dismissing a subsystem that had shipped
two blocks earlier. Both times the work got smaller once the design was checked against the
code, and both times `ship` then deleted the reasoning with no trace that it had been wrong.
`--superseded-design` is that trace, appended to the ledger's sentence because the entry is
already the one place the section's address and the outcome meet — and the value is the
*pattern*: a ledger where a third of the claimed designs turn out stale is a fact about how
far ahead this tool should let anybody design.

**And the half of it that was right goes somewhere, which nothing recorded either** (RK1267).
That flag types the deleted section as *stale*, and a section holds three contents with three
half-lives: the investigation, which dies with the ship; the criterion, which becomes a test;
and the decision, the constraint that stays true after the code moves. Deleting is right — a
rationale file reaching 539 KB one honest paragraph at a time is what this tool exists to
refuse — and untyped deletion is what is not: RK1265 records a definition of done written as a
section, deleted correctly, surviving nowhere, after which the block it governed was closed and
reopened six times. `--recorded-in <path>` is that trace, beside `--superseded-design` and
composed by the same writer, because the entry is where the address and the outcome already
meet. It is derived whole — the anchor is the pointer the line is losing and the destination is
a path — so it writes no prose (L4), and it is refused on a path this repository does not have,
as every other path a ledger sentence names already is (RK497). Never an archive: a flag that
copied the section into a second file is the 539 KB with better manners.

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

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path

from roadkeep import claiming, criteria, queueing
from roadkeep.authoring import (
    Insertion,
    place,
    refuse_occupied,
    refuse_reuse,
    remove_entry,
)
from roadkeep.backlog import Backlog, NotOpen, Standing, Whereabouts
from roadkeep.config import PROSE_ROLES, Config
from roadkeep.kernel.document import Document, Entry, Wrapped, counted, save_all
from roadkeep.ids import IdRef, next_id
from roadkeep.markers import refresh
from roadkeep.provenance import invocation
from roadkeep.renumbering import NotAnId, SameId, family_of
from roadkeep.kernel.schema import (
    ELSEWHERE,
    PARTIAL,
    SchemaError,
    Task,
    Violation,
    over_by,
    width,
)
from roadkeep.sections import (
    Section,
    declaring,
    find,
    nested,
    owners,
    pointers,
)
from roadkeep.sections import drop as drop_section

__all__ = [
    "AlreadyRecorded",
    "AlreadyShipped",
    "AlreadySuperseded",
    "Ambiguous",
    "Closure",
    "Corrected",
    "Departure",
    "Divergent",
    "Dropped",
    "InheritedClaim",
    "NoCompletion",
    "NoDecision",
    "NoDecisions",
    "NoDesign",
    "NoOutcome",
    "NoQualifier",
    "NoRestatement",
    "NoSupersession",
    "NoSuchEntry",
    "NoSuchReplacement",
    "NotDuplicated",
    "NotOpen",
    "NotDecided",
    "NotRecorded",
    "NotRedundant",
    "Partial",
    "PartRecorded",
    "Readdressed",
    "Record",
    "Refiled",
    "SecondPartial",
    "Section",
    "Superseded",
    "Shipment",
    "Unchosen",
    "Wrapped",
    "amend",
    "drop",
    "move",
    "readdress",
    "record",
    "recording_cost",
    "retire",
    "retiring",
    "ship",
    "supersede",
]


def _spelled(root: Path | None, written: Sequence[Path]) -> tuple[str, ...]:
    """The paths a departure wrote, as the project spells them (RK309).

    Relative, in the order they were written, because the caller feeds them to a `git add --`
    from the repository root — and an absolute path is an answer about one machine, the rule
    every message here already keeps. Spelled without a :class:`~roadkeep.config.Config`,
    which a saved transaction no longer has: the root is what it carries for the claim, and a
    path this cannot place against it is answered whole rather than dropped.
    """
    if root is None:
        return ()
    spelled: list[str] = []
    for target in written:
        try:
            spelled.append(target.resolve().relative_to(root).as_posix())
        except (OSError, ValueError):  # another tree, or a path this filesystem will not place
            spelled.append(target.as_posix())
    return tuple(spelled)


class AlreadyRecorded(ValueError):
    """A second ledger entry for one id is two records of one decision.

    The message names which door the id already went through, because "already in the
    changelog" sends a reader looking for a ✅ that may be a 🗑 (RK32).
    """

    def __init__(
        self, task_id: str, where: str, lineno: int, marker: str, closable: bool = False
    ) -> None:
        self.task_id = task_id
        self.lineno = lineno
        self.marker = marker
        #: Whether the closure path would take this line, which is the **only** state the
        #: door below is true of (RK1045). RK1044 added the clause unconditionally and it
        #: landed on the one caller it cannot help: a ⏳ line beside a full entry is refused
        #: *by `ship` itself*, so the remedy named was the command that had just failed —
        #: which costs a reader two more attempts before the sentence becomes the suspect.
        #:
        #: Nothing is invented where it is false. A live partial is deliberately outside the
        #: closure path (widening it cost a task and a 224-word section), so what a caller
        #: needs there is the qualifier corrected, not a fourth door composed here.
        self.closable = closable
        door = (
            f" — `{invocation()} ship {task_id}` closes the open line against the entry "
            f"that is already there, writing nothing to the ledger"
            if closable
            else ""
        )
        super().__init__(
            f"{task_id} is already recorded as {marker} in {where}:{lineno}: a second "
            f"entry would make the ledger disagree with itself about how it left{door}"
        )


class SecondPartial(ValueError):
    """A second `ship --part` against an id whose first half the ledger already holds (RK191).

    :class:`AlreadyRecorded` was the answer here, and it is the right answer at the door it
    was written for — an id the ledger already **closed**, where naming the entry in the way
    is the whole of what a caller needs. It is not the answer here. A caller reaching this
    one has work that came in more halves than one id can hold, and was told where the first
    one is.

    The answer exists and is not this tool's guess: Shio hit exactly this and settled it as
    *a step delivered gets an id, not a share of one* (SH361), filing SH366 through SH371 as
    the six steps of two tasks with each qualifier naming its parent in prose. That is also
    what this refusal enforces — one partial per id, then the completion — so the check is
    right and only its sentence was incomplete.

    Which spelling the step takes is `roadkeep.toml`'s and not this module's (L6): where
    `[ids] suffix` is declared the new line keeps the number and takes a letter, and where it
    is not, it is an ordinary `add` whose `why` names the parent.
    """

    def __init__(
        self, task_id: str, where: str, lineno: int, part: str, *, suffix: bool
    ) -> None:
        self.task_id = task_id
        self.lineno = lineno
        self.part = part
        self.suffix = suffix
        door = (
            f"`{invocation()} add --id {task_id}b --block <x> --symptom \"…\" --why \"…\"`, this "
            f"project declaring `[ids] suffix`"
            if suffix
            else f"`{invocation()} add --block <x> --symptom \"…\" --why \"…\"` with a `why` that "
            f"names {task_id}, this project declaring no `[ids] suffix`"
        )
        super().__init__(
            f"{task_id} already records a half in {where}:{lineno} ({part}): one id carries "
            f"one partial and then the completion, so a second would be two answers about "
            f"one piece of work — a step that was delivered gets an id of its own, and here "
            f"that is {door}. `ship {task_id}` instead if what landed is the rest of it, and "
            f"`record amend {task_id} --part \"…\"` if the qualifier stopped being true"
        )


#: The names these had when shipping was the only door (RK6), kept because they read
#: better at a `ship` call site: an id can now be retired as well as shipped, and both are
#: the same refusal and the same transaction.
AlreadyShipped = AlreadyRecorded


class NoSuchPath(ValueError):
    """Ledger prose naming a path this repository does not have (RK497).

    The gate's `path.missing`, asked where the sentence is composed instead of after it lands
    — which is L1, and the one ledger rule that was not held here. Measured at the cost the
    law predicts: a `ship --why` citing a path from its own reproduction reported success,
    the entry landed, the commit was made, and the finding came off an unrelated run
    afterwards; repairing it took a second commit describing nothing shipped.

    Refused rather than reported, and the split is the same one RK295 drew: a *scope* naming
    an absent path is reported, because declaring one before the file exists is the ordinary
    case, while a ledger entry is the opposite claim — the work is done, so the artefact is
    there or the sentence is wrong.

    Only the prose **this call** brought. What a ship inherits from the roadmap line it is
    closing is somebody's earlier sentence, and `restate` is that door: refusing a ship over
    it would price a correction as a shipment, and the gate still names it either way.

    No fix is offered, because there is none to compute (L4): the token is either a typo, a
    file that moved, or a name that should not have been in backticks — and which of the
    three it is, is the thing only the author knows.
    """

    def __init__(self, named: str, missing: Sequence[str], file: str) -> None:
        self.named = named
        self.missing = tuple(missing)
        spelled = ", ".join(self.missing)
        super().__init__(
            f"{named} names {spelled}, which {'are' if len(self.missing) > 1 else 'is'} not "
            f"in the repository: {file} records work that is done, so a path it names has to "
            f"resolve — the gate reports this as `path.missing` once the entry is written"
        )


class NoRestatement(ValueError):
    """A flag that writes the ledger's sentence, where the ledger is not written (RK62).

    On the closing path the entry already exists and this command deliberately leaves it alone,
    so the sentence has nothing to restate. Refused rather than dropped: a flag silently
    ignored is a flag the caller believes took effect.

    Three flags reach it, all of which land in that one sentence: `--why` is the sentence,
    `--superseded-design` is the clause appended to it (RK310), and `--recorded-in` is the
    second clause beside that one (RK1267).
    """

    def __init__(self, task_id: str, recorded: Entry, flag: str = "--why") -> None:
        self.flag = flag
        does = (
            "restates the ledger's sentence"
            if flag == "--why"
            else "is written into the ledger's sentence"
        )
        super().__init__(
            f"{task_id} is already recorded as {recorded.task.status} at line "
            f"{recorded.lineno}, so this call only closes its roadmap line: {flag} {does}"
            f", and the ledger is not written here"
        )


class NoDesign(ValueError):
    """A clause about the deleted design, on a line that pointed at none (RK310, RK1267).

    Both clauses name the address of the rationale this shipment deletes, and a line with no
    pointer has none: there is nothing that went stale and nothing being deleted, so an entry
    saying either would send the next reader of the ledger looking through git for prose
    nobody ever wrote.

    The flag is a field because the two say different things about the same absence, and a
    refusal naming the other one reads as a bug in the tool rather than as an answer.
    """

    #: What each flag's clause claims about the section, and where its value belongs instead.
    _CLAIMS = {
        "--superseded-design": (
            "no design was superseded",
            "the address of the rationale this shipment overtook",
            "the outcome belongs in --why",
        ),
        "--recorded-in": (
            "no design is being deleted",
            "the address of the rationale whose durable half moved",
            "there is nothing for the path to be the destination of",
        ),
    }

    def __init__(self, task_id: str, flag: str = "--superseded-design") -> None:
        self.task_id = task_id
        self.flag = flag
        absent, names, instead = self._CLAIMS[flag]
        super().__init__(
            f"{task_id} carries no pointer, so {absent}: {flag} names {names}, and this "
            f"line never had one — {instead}"
        )


class RemainderRefused(SchemaError):
    """The open half's sentence, refused under the name the caller typed (RK1262).

    `ship <id> --part … --why … --remainder …` validates the remainder as the reopened line's
    `why`, because that is what it becomes — and the refusal then read `why: why is a sentence:
    end it`. Both arguments on that command line are whys by the time the check runs, so the
    message is **true and still does not say which string to fix**. Measured from a session that
    had terminated its `--why` correctly, read the error as being about that argument, and got
    to the right edit only by reasoning that nothing else could be wrong.

    Everywhere else the field a refusal names is the flag that carried the value, which is why
    this one reads as a contradiction rather than as a hint. So the violations about that field
    are reported under `remainder`, and one sentence says where the rule came from — the code
    stays `why.*`, being the rule that was broken and the token anything greppable keys on.

    A :class:`SchemaError` subclass, so a caller catching that class keeps catching this: what
    changed is what the refusal *says*, not which class of refusal it is.
    """

    #: The field the reopened line carries this value in, and the one being renamed.
    BECOMES = "why"

    def __init__(self, task_id: str, violations: tuple[Violation, ...]) -> None:
        renamed = tuple(
            replace(one, field="remainder") if one.field == self.BECOMES else one
            for one in violations
        )
        super().__init__(renamed)
        self.task_id = task_id
        self.about = (
            f"--remainder becomes {task_id}'s {self.BECOMES} when the partial lands, so it is "
            f"held to that field's rules and named below as itself — the --why on this call is "
            f"the ledger entry's own sentence and is not what this refuses"
        )


class SupersessionCrowded(ValueError):
    """A ledger sentence over its limit, reported as the field that has to survive (RK1261).

    `--why` and `--superseded-design` render as one sentence and are refused as one field, so
    the message named `why` and quoted a total neither argument was. Measured here: 183
    characters of outcome beside 166 of supersession note answered `why: 385 characters, limit
    is 200 … delete 185 characters — about 29 words`, which read literally asks for a
    15-character outcome. Read as advice it asks for the **wrong edit** — the obvious response
    is to cut the outcome sentence, and that is the half the entry keeps once the design is
    deleted. The note is the half that can go, and nothing in the message pointed there.

    So the parts are named and the room is attributed to the one that has it. Raised only where
    the composition is what overflowed: a `--why` over the allowance on its own is
    `why.too-long` about the field it really is about, which is :meth:`Schema.why_budget`'s own
    rule — an overrun in one field is never charged to another — applied one file over.
    """

    def __init__(
        self,
        task_id: str,
        *,
        authored: str,
        note: str,
        composed: str,
        limit: int,
        source: str = "",
    ) -> None:
        self.task_id = task_id
        self.limit = limit
        # Derived by subtraction rather than by re-composing the wrapper: `_parenthesised` is
        # the only writer of that shape (L3's rule about one writer), and a second spelling of
        # its brackets here would be the number that drifts when the clause is reworded.
        structure = width(composed) - width(authored) - width(note)
        room = limit - width(authored) - structure
        #: What the author is being asked to do, which is the whole point of naming the parts.
        edit = (
            f"which has {room} characters beside this --why"
            if room > 0
            else "which has none beside this --why, so the outcome is what has to be shorter "
            "first"
        )
        super().__init__(
            f"{task_id}'s ledger sentence is "
            f"{over_by(width(composed), limit, measured=composed, source=source)}, and two "
            f"arguments compose it: --why took {width(authored)}, --superseded-design took "
            f"{width(note)}, and parenthesising them into one sentence added {structure}. The "
            f"outcome is what the entry keeps once the design is deleted, so it is the note "
            f"that gives way, {edit}"
        )


class RecordingCrowded(ValueError):
    """A ledger sentence over its limit because the recording clause joined it (RK1267).

    :class:`SupersessionCrowded`'s sibling with the giving-way half swapped, and that is the
    whole difference: there the note is the author's and can be cut, and here the clause is an
    address and a path — derived whole, so nothing in it is prose anybody can shorten. So the
    outcome is what has to give, and the message says so rather than quoting a total neither
    argument is and leaving the author to guess which end to cut.

    Raised only where the composition is what overflowed, for the reason that one is: a `--why`
    already over its allowance is `why.too-long` about the field it is really about.
    """

    def __init__(
        self,
        task_id: str,
        *,
        outcome: str,
        clause: str,
        composed: str,
        limit: int,
        source: str = "",
    ) -> None:
        self.task_id = task_id
        self.limit = limit
        room = limit - (width(composed) - width(outcome))
        super().__init__(
            f"{task_id}'s ledger sentence is "
            f"{over_by(width(composed), limit, measured=composed, source=source)}, and the "
            f"recording clause is derived whole: {clause} spends "
            f"{width(composed) - width(outcome)} of it, and none of that is prose to cut. So "
            f"the outcome is what gives way, which has {max(room, 0)} characters here"
        )


class NoDecisions(KeyError):
    """`--decides` on a project that declares no decisions file (RK1269).

    Refused and never scaffolded on the way past, which is `defer`'s rule about the deferred
    store and its reason: a governed file invented at the moment one is needed is a format
    decided by a verb, and the door that writes one is `declare`. So the refusal names it, and
    the sentence the caller just composed is the one thing that has to be retyped — which is
    why it is refused **before** the ledger is read and not after the entry lands.
    """

    def __init__(self, task_id: str, where: str) -> None:
        self.task_id = task_id
        super().__init__(
            f"{where} declares no decisions file, so {task_id} has nowhere to record what "
            f"outlives it: `{invocation()} declare decisions` opens the role and writes the "
            f"file with this project's own block headings, and then this call lands"
        )


class InheritedClaim(SchemaError):
    """A decision refused over the claim it inherited, and the two doors that are real (RK1281).

    `ship --decides` composes the decision from the task's own claim and the author's sentence,
    which is right: a decision is *about* the problem the line stated, and restating it would
    be the second sentence RK142 refuses to inherit one file over. What it inherits with it is
    the claim's **length**, measured against a limit the caller cannot reach — and the refusal
    then offered the remedy every symptom overrun gets, which is to put the remainder in the
    rationale section. That section is the one this ship is deleting.

    So the refusal stands and its door changes. Two are real: `restate` rewrites the claim in
    both files, and a wider `[limits.decisions] symptom` says the decisions file takes what the
    roadmap already does. Neither is composed here — which of them is right depends on whether
    the claim or the limit was wrong, and that is a judgement (L4).

    A :class:`SchemaError` subclass, so a caller catching that class keeps catching this: what
    changed is what the refusal *says*, and never which class of refusal it is.
    """

    def __init__(self, task_id: str, refused: SchemaError, where: str) -> None:
        # The clause the schema appends is removed **by identity** (RK1285): `ELSEWHERE` is
        # the one writer of it, so a rewording moves both ends at once — and here it is
        # false, which is the case that made it a constant. `RemainderRefused`'s shape at the
        # other end of the same message: there the field named was wrong, here the door is.
        super().__init__(
            tuple(
                replace(one, message=one.message.removesuffix(ELSEWHERE))
                if one.field == "symptom"
                else one
                for one in refused.violations
            )
        )
        self.task_id = task_id
        self.about = (
            f"--decides writes no symptom: {task_id}'s claim is the roadmap line's, carried "
            f"into {where} whole, so the remainder cannot go in the rationale section this "
            f"ship is deleting. Either `restate {task_id} --symptom \"…\"`, which rewrites "
            f"the claim in both files, or declare a wider limit — `{invocation()} govern "
            f"limits.symptom <n> --role decisions` takes the reading first"
        )


class NoDecision(ValueError):
    """`--decides` on a `ship --part` (RK310's refusal, one file over — RK1269).

    A partial keeps its section, so nothing has been deleted and there is no reading of the
    design that survived it. The completion is the call that deletes, and it is the one that
    knows which constraint outlived the code.
    """

    def __init__(self, task_id: str, part: str) -> None:
        self.task_id = task_id
        self.part = part
        super().__init__(
            f"a partial keeps {task_id}'s design, so nothing has outlived it yet: pass "
            f"--decides on the `ship {task_id}` that completes ({part}), which is the call "
            f"that deletes the section"
        )


class NoSupersession(ValueError):
    """A clause about a deleted design, on a `ship --part` (RK310, RK1267).

    A partial keeps its section, because the design still has work left to describe (RK121).
    So a premise that turned out stale is not yet settled: what the rest of the work reads
    the design for may still be right, and the completion is the moment the whole of it is
    known — and the same holds of where the durable half went, which is not decided while the
    section is still being read. Refused rather than carried, there being no second entry for
    the clause to be corrected onto.
    """

    def __init__(self, task_id: str, part: str, flag: str = "--superseded-design") -> None:
        self.task_id = task_id
        self.part = part
        self.flag = flag
        super().__init__(
            f"a partial keeps {task_id}'s design, because the rest of the work still reads "
            f"it: pass {flag} on the `ship {task_id}` that completes ({part}), "
            f"which is the call that deletes the section"
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
            f"`{invocation()} renumber {task_id}` gives the open one an address of its own"
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

    **What it named was not a door** (RK1138). Observed on Shio's `SH698`: an intermittent red
    was instrumented, the cure refuted, the remainder abandoned — and the hint sent the author
    to `record amend --part`, which restates the entry and leaves this refusal exactly as it
    was, because the entry still exists. Three shapes for a real door were measured and each is
    blocked by a rule this project keeps: a **second entry** is the gate's own `id.duplicate`;
    **appending a sentence** to the entry's `why` is `why.sentences`, the ledger holding one
    sentence per outcome; and appending *inside* it would be this tool rewriting somebody's
    prose (L4). The qualifier has room for neither the reason nor the fact.

    So the exit is the completion, and the message now says so as the intended one. `ship <id>
    --why "…"` replaces the qualified entry with **the author's own sentence** and drops the
    qualifier — which is where "and the rest was abandoned" belongs, because ✅ marks the line
    leaving by the delivering door and something here did deliver. 🗑 would say nothing ever
    did, which is the other direction's lie and the one RK129 refuses.
    """

    def __init__(
        self, task_id: str, where: str, lineno: int, part: str, marker: str
    ) -> None:
        self.task_id = task_id
        self.lineno = lineno
        self.part = part
        super().__init__(
            f"{where}:{lineno} already records {marker} {task_id} ({part}), and retiring "
            f"{task_id} would replace that entry: the half that shipped would leave the only "
            f"file that holds it. An entry holds one outcome per id, so an abandonment cannot "
            f"be a second one — `{invocation()} ship {task_id} --why \"…\"` is the exit, and "
            f"its sentence is where the rest being abandoned is recorded: the qualifier goes, "
            f"and {marker} stays because this line left by the door something did deliver "
            f"through"
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


class NoCompletion(ValueError):
    """`--lines` on a ship that replaces no entry (RK193).

    The count is the caller saying they read the span a write deletes, so it is only ever
    about the partial entry a completion rewrites. On every other path `ship` *places* a new
    entry and deletes nothing, and a count accepted there is a flag the caller believes took
    effect — the reason `--why` is refused on the closure path rather than ignored.

    **Two sentences, because the paths here are two states** (RK1128). Where the ledger holds
    nothing to replace, naming that is the answer. Where the call still passes `--part` it is
    not a completion *whatever the ledger holds*, and reporting the ledger as empty sent a
    caller to look for an entry that was there: measured in Turing, `ship T898 --part … --lines
    1` answered "records no partial for T898" over a `**T898 (the lint half)**` on line 693, and
    dropping the flag produced the refusal that names the real rule. So the narrower sentence is
    said at the narrower door, which is the shape every refusal here already takes.
    """

    def __init__(self, task_id: str, where: str, *, also_part: bool = False) -> None:
        self.task_id = task_id
        because = (
            f"this call passes --part, so it is not one: a half is **placed** and nothing is "
            f"deleted whatever {where} holds — `ship {task_id}` with no --part is the "
            f"completion a count belongs to"
            if also_part
            else f"this call replaces none: {where} records no partial for {task_id}, so the "
            f"entry is placed and nothing is deleted"
        )
        super().__init__(f"--lines says how many lines a completion replaces, and {because}")


class NoSpan(ValueError):
    """`--lines` on the `--supersedes` pointer, which no longer replaces a span (RK1053).

    :class:`NoCompletion`'s shape one write over, and refused for its reason rather than
    ignored: a count accepted where nothing is deleted is a flag the caller believes took
    effect. What changed is the write beneath it. The forward pointer is appended to the
    `why`, which is the text of the entry's **first** line, so re-rendering that line
    reproduces every field the task holds — and the span the count used to authorise was
    prose the parse never held, deleted by a call that asked to add a pointer.

    So the flag is not merely unnecessary here, it is a claim about a deletion that cannot
    happen, and the refusal says so rather than leaving a caller to assume it mattered.
    """

    def __init__(self, task_id: str, where: str) -> None:
        self.task_id = task_id
        super().__init__(
            f"--lines says how many lines a write replaces, and the forward pointer onto "
            f"{task_id} replaces none: it is appended to the sentence on that entry's "
            f"first line at {where}, and the lines under it are left where they are"
        )


class AlsoPaused(ValueError):
    """A departure for an id the deferred store still carries (RK1081).

    Neither door removes the other file's line, so `ship` and `retire` both *succeeded* here
    and left the work recorded as shipped — or retired — and still set aside, with the gate
    calling that tree clean. Two files answering differently about one id is what
    :class:`AlreadyRecorded` refuses one pair over, and the store was the pair RK96 added and
    nothing widened for.

    Refused rather than made to remove the store entry, which is the same choice `ship`
    makes about a second ledger entry: a departure writes the files its own transaction is
    about, and reconciling a contradiction is a decision with its own verb. `resume` is that
    verb since RK1081 — the roadmap already says the work is open, so the store's copy is
    the stale half — and this refusal names it.
    """

    def __init__(self, task_id: str, where: str, lineno: int) -> None:
        self.task_id = task_id
        self.lineno = lineno
        super().__init__(
            f"{task_id} is also set aside in {where}:{lineno}: leaving it now would record "
            f"the work as gone while the store still says it is paused — "
            f"`{invocation()} resume {task_id}` removes the store's copy first, placing no "
            f"line, because the roadmap already carries one"
        )


class NoSuchReplacement(KeyError):
    """A forward pointer to an id no file holds, or to the retiring line itself (RK32).

    Refused, because a pointer to nothing is the exact defect this records against: the
    reader of the gap would be sent somewhere else that does not explain it either.

    *No file* is three of them (RK244). An id that was set aside is findable — the store is
    a file and `resume` brings the line back — so reading only the roadmap and the ledger
    refused the supersession most worth recording, and did it by saying "in neither file"
    about a line that was in one.
    """

    def __init__(self, replacement: str, task_id: str, *, itself: bool = False) -> None:
        if itself:
            where = f"{replacement} is {task_id}, and a line cannot replace itself"
        else:
            where = (
                f"{replacement} is in none of the three files this reads — not the "
                f"roadmap, not the ledger, not the deferred store"
            )
        super().__init__(
            f"{where}, so it cannot be what replaces {task_id}: retire it against an "
            f"id that exists, or as abandoned"
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
    #: The prose file this drop rewrote — **whichever role declared the anchor** (RK196), so
    #: it carries its own path and a caller naming the improvements file would be guessing.
    prose: Document | None = None
    dropped: Section | None = None
    #: Why nothing was dropped, when nothing was: a task can ship without a rationale
    #: section, and silence about that would read as a section that was deleted.
    kept: str | None = None
    #: The anchors that went with it, nested under the one named (RK78). Reported because a
    #: drop is a subtree, and a transaction that says "one section" about five is one whose
    #: size the author only learns from the diff.
    nested: tuple[str, ...] = ()
    #: Sections whose prose cited what this drop deleted (RK206). Named and never refused:
    #: the ship is right and the citing prose is the author's next edit, in this commit.
    cited: tuple[str, ...] = ()
    #: The parent anchor this drop left with no subsections (RK400), or None. The one thing
    #: a ship leaves standing that nothing named: an introduction to children that have all
    #: shipped, in the present tense, and the first thing anyone reads about that family.
    emptied: str | None = None
    #: Open lines whose `(deps: …)` this write made true again (RK8).
    refreshed: tuple[str, ...] = ()
    #: The marker the ledger line carries: ✅ shipped, 🗑 retired.
    marker: str = ""
    #: What the deleted design turned out to have been wrong about (RK310), as the author
    #: wrote it — the clause this transaction appended to the ledger's sentence. `None` on
    #: every ordinary shipment, which is the ordinary case: the design held.
    superseded: str | None = None
    #: Where the deleted design's durable half now lives (RK1267), as the path the caller
    #: named. Beside the field above and not inside it: one says the reasoning was wrong and
    #: the other says where the part that was right went, and a shipment may report both.
    recorded_in: str | None = None
    #: The line this departure filed into the decisions role (RK1269), or `None`. An
    #: :class:`Insertion` and not the sentence, because it is a **write** and the answer owes a
    #: file and a line for it exactly as it does for the ledger's.
    decided: Insertion | None = None
    #: The priority entry this departure took out with the line (RK327), or `None` where the
    #: queue never named it. Removed inside the same rewrite rather than reported, because it
    #: is derived dead by the departure — unlike :attr:`dependents` and :attr:`cited`, which
    #: are somebody else's lines and somebody else's prose.
    dequeued: str | None = None
    #: The leads of this task's own criteria list, which left with the line (RK1268). Empty on
    #: every departure of a task nobody wrote one for, which is the ordinary case.
    unmet: tuple[str, ...] = ()
    #: Open lines that still name this id. Reported and not refused: a supersession is
    #: legitimate and those lines are the author's next edit, which `lint` (RK14) gates.
    dependents: tuple[str, ...] = ()
    #: The role whose file holds `--superseded-by`'s target — `roadmap`, `changelog` or
    #: `deferred` (RK244). In the answer and never in the ledger line: a paused replacement
    #: is a supersession waiting on a `resume`, which the retired line's id alone cannot
    #: say, and a prefix saying it would go stale the moment the pause ends.
    replacement_in: str | None = None
    #: **The id that role is about** (RK1170). Set with the field above and for its reason: the
    #: two are halves of one fact, and the record held only the second — so both registers read
    #: the id back off argv, which is a verb answering about a call rather than a transaction.
    replacement: str | None = None
    #: The checkout, so the claim on a line that left for good is released (RK162) — the one
    #: thing this transaction touches that is not a governed file.
    root: Path | None = None
    #: What the working tree holds, split by whose claim names it (RK294) — read **before**
    #: :meth:`save` releases this line's claim, and `None` where no live claim declared a
    #: path. Reported and never refused: a loose path is a legitimate state, and a departure
    #: that failed over one would be an obstacle at the moment the author cannot route around
    #: it — the direction :func:`_drop_section` already chooses.
    scope: claiming.Scope | None = None

    def save(self) -> tuple[str, ...]:
        """Write the files, and answer which ones (RK309). Nothing here can fail on the
        format — that was decided.

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

        **What it answers is which paths it wrote** (RK309), the projections RK188 refreshed
        included, because that is the half of a commit's contents no author should have to
        declare: a scope is what the holder *said* (RK280) and this is what the tool *did*.
        Read off :func:`~roadkeep.kernel.document.save_all`'s own return and never rebuilt from the
        config — a second list of the files a transaction touches is one that can be wrong.
        """
        # The decisions line goes **second**, between the two records and before the deletion
        # (RK1269): it is the only trace of what the section held that outlives the code, so a
        # crash after the roadmap or the prose write would take it with the design it survived.
        written = save_all(
            self.ledger.document,
            None if self.decided is None else self.decided.document,
            self.roadmap,
            self.prose,
        )
        if self.root is not None:
            # Last, and never a condition of the writes: a terminal marker is not the
            # in-progress one, so the rule every marker write obeys says *release* (RK162).
            # The entry is inert either way — an id is never reused — but a row that can never
            # mean anything is noise in the listing `claims` exists to be read (RK161).
            claiming.follow(self.root, self.task_id, self.marker, self.roadmap.entries)
        return _spelled(self.root, written)

    @property
    def block(self) -> str:
        return self.ledger.entry.task.block

    def event(self, config: Config) -> dict[str, object]:
        """What the departure did to the block it left (RK38), off the roadmap it wrote."""
        from roadkeep.rendering import _event  # noqa: PLC0415 - RK260

        return _event(self.task_id, self.block, self.roadmap, config)

    def stated(self, config: Config, wrote: Sequence[str]) -> str:
        """Three edits across three files, as a reader is told them (RK6, RK32).

        Beside :meth:`payload` since RK1170. `wrote` is the caller's, because :meth:`save` is
        the door's step and a record naming paths it has not written would be answering about
        a transaction that may not have landed.
        """
        from roadkeep.rendering import (  # noqa: PLC0415 - RK260
            _cited_rows,
            _dequeued_rows,
            _unmet_rows,
            _emptied_rows,
            _event_rows,
            _prose_file,
            _scope_rows,
        )

        roadmap = config.relative(config.path("roadmap"))
        ledger = config.relative(config.path("changelog"))
        rows = [
            f"{self.task_id} → {ledger}:{self.ledger.lineno} under Block {self.block}",
            f"  removed  {roadmap}:{self.removed_from}",
        ]
        if self.dropped is not None:
            rows.append(f"  dropped  {self.dropped} from {_prose_file(config, self.prose)}")
            if self.nested:
                rows.append(f"  nested   {', '.join(f'§{a}' for a in self.nested)} went with it")
            rows += _cited_rows(self.cited)
            rows += _emptied_rows(self.emptied)
        else:
            rows.append(f"  kept     nothing dropped: {self.kept}")
        # Beside the drop rather than inside it (RK310): the deletion is what makes the clause
        # the only surviving trace, and it is reported even where the section stayed — a design
        # another open line still points at can be just as overtaken as one that went.
        if self.superseded is not None:
            rows.append(f"  overtook the design it read: {self.superseded}")
        # Under it and in the same place for the same reason (RK1267): the deletion is what
        # makes the address the only surviving trace, and this is where it went.
        if self.recorded_in is not None:
            rows.append(f"  recorded the part that outlives it: {self.recorded_in}")
        # The fourth file, reported as a write and not as a note (RK1269): it has a line
        # number, so a reviewer reads the diff against it the way they read the ledger's.
        if self.decided is not None:
            rows.append(
                f"  decided  {config.relative(config.path('decisions'))}:"
                f"{self.decided.lineno}  {self.decided.rendered}"
            )
        if self.refreshed:
            rows.append(f"  derived  {', '.join(self.refreshed)} (dep annotations re-derived)")
        rows += _dequeued_rows(self.dequeued)
        rows += _unmet_rows(self.unmet)
        # Last before the event line, because it is about the commit this ship precedes rather
        # than about the three edits above it (RK294).
        rows += _scope_rows(self.scope, wrote)
        rows += _event_rows(self.event(config), "  ", config=config, standing=True)
        return "\n".join(rows)

    def payload(self, config: Config, wrote: Sequence[str]) -> dict[str, object]:
        """The same answer as data, with every file the three edits reached."""
        from roadkeep.rendering import _prose_file, _scope_json  # noqa: PLC0415 - RK260

        return {
            "id": self.task_id,
            "changelog": {
                "file": config.relative(config.path("changelog")),
                "line": self.ledger.lineno,
                "rendered": self.ledger.rendered,
            },
            "roadmap": {
                "file": config.relative(config.path("roadmap")),
                "removed": self.removed_from,
            },
            "improvements": {
                # The file the drop actually rewrote, which is whichever prose role declared
                # the anchor (RK196) — not always the improvements file.
                "file": _prose_file(config, self.prose),
                "dropped": None
                if self.dropped is None
                else {
                    "anchor": self.dropped.anchor,
                    "title": self.dropped.title,
                    "first": self.dropped.first,
                    "last": self.dropped.last,
                },
                "nested": list(self.nested),
                "cited": list(self.cited),
                "emptied": self.emptied,
                "kept": self.kept,
                # What the deleted design was overtaken by (RK310), beside the anchor it was
                # written under: the two are one fact, and a caller reading them off the
                # rendered sentence would be parsing prose.
                "superseded": self.superseded,
                # And where the half of it that was right went (RK1267), read off the same
                # anchor: the pair is what types the deletion, so one without the other is
                # half an answer to the question this write exists to record.
                "recorded_in": self.recorded_in,
            },
            "refreshed": list(self.refreshed),
            # What left the order with the line (RK327), named because a plan that silently
            # got shorter is a change with no sentence about it.
            "dequeued": self.dequeued,
            # And the task's own criteria that went with it (RK1268), for the same reason.
            "unmet": list(self.unmet),
            # The fourth file (RK1269), shaped as the ledger's own block above: a write with a
            # file and a line, never the sentence alone.
            "decisions": None
            if self.decided is None
            else {
                "file": config.relative(config.path("decisions")),
                "line": self.decided.lineno,
                "rendered": self.decided.rendered,
            },
            "scope": _scope_json(self.scope, wrote),
            "event": self.event(config),
        }

    def retired(self, config: Config, wrote: Sequence[str]) -> str:
        """The **other** door's reading of this record (RK32), as a reader is told it.

        One shape for both doors and two registers each, which is four methods and not a flag:
        a retirement's subject is where the replacement was found and who still names the line,
        and a shipment's is the design that was deleted. A branch inside one method would be
        those two answers sharing a name because they share a dataclass.
        """
        from roadkeep.rendering import (  # noqa: PLC0415 - RK260
            _event_rows,
            _prose_file,
            _scope_rows,
        )

        roadmap = config.relative(config.path("roadmap"))
        ledger = config.relative(config.path("changelog"))
        rows = [
            f"{self.task_id} {self.marker} {ledger}:{self.ledger.lineno} "
            f"under Block {self.block}",
            f"  removed  {roadmap}:{self.removed_from}",
        ]
        if self.replacement_in is not None:
            # Where the replacement was found, because the three files are three different
            # promises (RK244): shipped is a supersession already delivered, open is one being
            # worked, and paused is one waiting on a `resume` nobody is holding.
            rows.append(
                f"  found    {self.replacement} in "
                f"{config.relative(config.path(self.replacement_in))}"
            )
        if self.dropped is not None:
            rows.append(f"  dropped  {self.dropped} from {_prose_file(config, self.prose)}")
        if self.dependents:
            # Reported, not refused: a supersession is legitimate and these lines are the
            # author's next edit. `deps` now resolves them as unresolvable, not as satisfied.
            rows.append(f"  still    {', '.join(self.dependents)} name {self.task_id}")
        # A retirement is committed exactly as a ship is, and it releases the same claim (RK294).
        rows += _scope_rows(self.scope, wrote)
        rows += _event_rows(self.event(config), "  ", config=config, standing=True)
        return "\n".join(rows)

    def retirement(self, config: Config, wrote: Sequence[str]) -> dict[str, object]:
        """The retirement as data, with both halves of where the replacement is (RK244)."""
        from roadkeep.rendering import _scope_json  # noqa: PLC0415 - RK260

        return {
            "id": self.task_id,
            "marker": self.marker,
            "superseded_by": self.replacement,
            "replacement_in": self.replacement_in,
            "changelog": {
                "file": config.relative(config.path("changelog")),
                "line": self.ledger.lineno,
                "rendered": self.ledger.rendered,
            },
            "roadmap": {
                "file": config.relative(config.path("roadmap")),
                "removed": self.removed_from,
            },
            "dropped": None if self.dropped is None else self.dropped.anchor,
            "dependents": list(self.dependents),
            "refreshed": list(self.refreshed),
            "scope": _scope_json(self.scope, wrote),
            "event": self.event(config),
        }


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
    #: What the caller said is **left**, where they said it (RK1233). Written into the open
    #: line's own `why`, so the remainder is a field rather than a subtraction the next reader
    #: makes across two files. `None` is every call before this argument and every one that
    #: declines it — the line keeps the sentence it had, which is what it always did.
    remainder: str | None = None
    #: What the roadmap line's marker became — ⏳, or the one it already carried at a
    #: project that declares no such marker. Reported because the two differ and a caller
    #: reading "partial" would otherwise not know which of them happened.
    status: str = ""
    refreshed: tuple[str, ...] = ()
    #: The marker the ledger entry carries: ✅, on the part that shipped.
    marker: str = ""

    def save(self) -> tuple[Path, ...]:
        # The ledger first, as everywhere else (RK118): the record of what landed is the
        # thing that cannot be reconstructed, and a marker not yet ⏳ is a state a second
        # run of the same command corrects.
        return save_all(self.ledger.document, self.roadmap)

    @property
    def block(self) -> str:
        return self.ledger.entry.task.block

    @property
    def lineno(self) -> int:
        """Where the line this did **not** remove still stands."""
        return self.roadmap.by_id()[self.task_id].lineno

    def event(self, config: Config) -> dict[str, object]:
        from roadkeep.rendering import _event  # noqa: PLC0415 - RK260

        return _event(self.task_id, self.block, self.roadmap, config)

    def stated(self, config: Config) -> str:
        """Half of a task recorded, with its roadmap line still open (RK121).

        Beside :meth:`payload` since RK1170. Nothing was removed and nothing was dropped, so a
        departure's report would be three lines of None: what happened is an entry and a marker.

        **And the door the open half leaves** (RK1302). This is the one ship that deliberately
        leaves work open, and the state it leaves is the one `pick` trusts most — so the line
        comes back on the very next call, ahead of everything, and did until two unrelated tasks
        shipped. Measured on quickshell: QS3 landed a corpus and a harness, its remainder waited
        on a parser and a renderer that were not written, and the answer stopped exactly where
        the caller needed the next sentence. The remedy is one command, `amend <id> --dep …`,
        and nothing said so — so a caller who does not know it re-picks the same line while the
        file goes on saying in progress.

        Named the way `finish` below is named, and not taken in this transaction: `--part --dep`
        would amend the group here, on the argument that the moment a remainder is described is
        the moment its blockers are known. That is a real shape and RK1302 left it open rather
        than guessing at it — what the measurement showed missing was the sentence, not the
        keystroke. It is a **row and not a payload key** for the reason `finish` is: the doors
        this answer carries are all on stdout — a gap RK1307 has since closed, and
        :meth:`doors` is where both now come from.
        """
        from roadkeep.rendering import _event_rows  # noqa: PLC0415 - RK260

        roadmap = config.relative(config.path("roadmap"))
        ledger = config.relative(config.path("changelog"))
        rows = [
            f"{self.task_id} ({self.part}) → {ledger}:{self.ledger.lineno} "
            f"under Block {self.block}",
            f"  open     {roadmap}:{self.lineno} {self.status} — the rest of it is still a task",
            *(
                # The other half, where the caller named it (RK1233): the line now *states*
                # what is left, so the next reader is handed it rather than subtracting.
                [f"  left     {self.remainder}"] if self.remainder else []
            ),
            # Before `finish`, because it is what to do **now** and that one is what to do at
            # the end: the line is open, so it is picked again before either happens.
            f"  waits    this line is offered again until it says what it is waiting on — "
            f"`{invocation()} {' '.join(self.doors()[0].argv)}` names it, where the rest of "
            f"the work waits on something still open",
            f"  finish   {invocation()} {' '.join(self.doors()[1].argv)}"
            f"  (drops the qualifier)",
        ]
        if self.refreshed:
            rows.append(f"  derived  {', '.join(self.refreshed)} (dep annotations re-derived)")
        rows += _event_rows(self.event(config), "  ", config=config, standing=True)
        return "\n".join(rows)

    def doors(self) -> tuple[Door, ...]:
        """The two commands this half-written state makes available (RK1302, RK1307).

        In the order a caller reaches them: what to do **now** with the work that is left, and
        what closes the line at the end. One reader for both registers, because a printer that
        composed its own argv beside a payload that composed another is two answers about the
        same next step — which is the shape RK1307 is a class of.
        """
        return (
            Door(
                ("amend", self.task_id, "--dep", "<id>"),
                "the remainder waits on something still open, and this names it",
            ),
            Door(("ship", self.task_id), "the rest of it landed, and this drops the qualifier"),
        )

    def payload(self, config: Config) -> dict[str, object]:
        """The same answer as data, saying the line is still open (RK121).

        And the two doors the rows carry (RK1307): this is the one write that deliberately
        leaves work open, so the commands that resolve that state are the answer — and the
        caller reaching it through the served payload is the one that had neither.
        """
        from roadkeep.rendering import _served  # noqa: PLC0415 - RK260

        return {
            "id": self.task_id,
            "part": self.part,
            "doors": [one.payload(_served(config)) for one in self.doors()],
            # What is left, where the caller said it (RK1233). Null and not omitted: a
            # consumer reading a missing key cannot tell "not stated" from "older server".
            "remainder": self.remainder,
            "changelog": {
                "file": config.relative(config.path("changelog")),
                "line": self.ledger.lineno,
                "rendered": self.ledger.rendered,
            },
            "roadmap": {
                "file": config.relative(config.path("roadmap")),
                "line": self.lineno,
                "status": self.status,
                "open": True,
            },
            "refreshed": list(self.refreshed),
            "event": self.event(config),
        }


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
    #: The file this write leaves behind: without the line, dependents re-annotated. Named
    #: for what it *is* rather than for the role it happens to be (RK1088), because the role
    #: is the field below and a pair that can disagree is a pair that will: `Resumption` had
    #: exactly this shape until RK1086, where a document called `roadmap` was the answer for
    #: an act that touched the store.
    remaining: Document
    removed_from: int
    #: The ledger entry that already existed, and its marker — ✅ or 🗑, because a reader has
    #: to know which door this id went through before its line was left behind.
    recorded: Entry
    #: **Which file the line came out of** (RK1086). `roadmap` on every closure this verb
    #: makes today, and named rather than assumed because the assumption is what blocks the
    #: next one: RK1084 found an id the ledger records and the *store* still carries, which
    #: is the same act — remove the leftover, write nothing — against a different pair, and
    #: a result that can only say `removed_from` has nowhere to put the answer.
    removed_in: str = "roadmap"
    #: The prose file this drop rewrote, as :class:`Departure` carries it (RK196).
    prose: Document | None = None
    dropped: Section | None = None
    kept: str | None = None
    #: The anchors nested under the one dropped, as :class:`Departure` reports them (RK78).
    nested: tuple[str, ...] = ()
    #: Sections left citing what the drop deleted, as :class:`Departure` reports them (RK206).
    cited: tuple[str, ...] = ()
    #: The parent this drop left with no subsections, as :class:`Departure` reports it (RK400).
    emptied: str | None = None
    refreshed: tuple[str, ...] = ()
    dependents: tuple[str, ...] = ()
    #: The priority entry this closure took out (RK327). Here for the reason every other
    #: field of the departure is: the line leaves, so the order naming it could only fire on
    #: nothing — and a door that is `ship` minus the ledger edit is still a departure.
    dequeued: str | None = None
    #: The task's own criteria, which left with the line (RK1268) — :class:`Departure`'s field
    #: and its argument: this door is the rest of a transaction, so it owes the same edits.
    unmet: tuple[str, ...] = ()
    #: The line filed into the decisions role (RK1269). Reached on this door and not by the
    #: two clauses beside it: those restate a ledger sentence this path does not write, and a
    #: decision is a line in a file of its own, filed where the section is deleted.
    decided: Insertion | None = None
    #: The tree split by whose claim names it (RK294), as :class:`Departure` carries it. Read
    #: here too because the moment is the same one — this door is `ship` on a line whose entry
    #: is already on disk, and the commit it precedes stages exactly the same files.
    scope: claiming.Scope | None = None
    #: The checkout, so this door releases the claim its sibling releases (RK306).
    root: Path | None = None

    @property
    def marker(self) -> str:
        return self.recorded.task.status

    def save(self) -> tuple[str, ...]:
        """Write the roadmap and the prose file, and answer which. The ledger is never opened
        for writing, so it is not in the answer either (RK309).

        And reconcile the claim, which this was the one departure not to do (RK306). RK162
        made every marker write a release and :meth:`Departure.save` obeys it; this shape is
        the same departure minus the ledger edit, and skipped it — so the interrupted
        transaction RK130 opened this door for closed its line and left the dated row and the
        scope it carried behind, for `claims` to list against an id no file holds and for a
        `--prune` the author was never told they needed.

        The marker passed is the **ledger's**, which is what this door has: the line is gone,
        so there is no roadmap marker to write, and the entry's ✅ or 🗑 is the terminal one
        the rule reads as a release either way. Last and never a condition of the writes, for
        the reason its sibling states.
        """
        # The decision first, for the reason its sibling states (RK1269): it is the only
        # trace of what the section held, and the prose write is the deletion.
        written = save_all(
            None if self.decided is None else self.decided.document,
            self.remaining,
            self.prose,
        )
        if self.root is not None:
            claiming.follow(self.root, self.task_id, self.marker, self.remaining.entries)
        return _spelled(self.root, written)

    def event(self, config: Config) -> dict[str, object]:
        from roadkeep.rendering import _event  # noqa: PLC0415 - RK260

        return _event(self.task_id, self.recorded.task.block, self.remaining, config)

    def stated(self, config: Config, wrote: Sequence[str]) -> str:
        """A roadmap line closed against an entry the ledger already had (RK62).

        Beside :meth:`payload` since RK1170, and the file the line came out of is read off this
        record rather than assumed to be the roadmap (RK1088).
        """
        from roadkeep.rendering import (  # noqa: PLC0415 - RK260
            _cited_rows,
            _dequeued_rows,
            _unmet_rows,
            _emptied_rows,
            _event_rows,
            _prose_file,
            _scope_rows,
        )

        ledger = config.relative(config.path("changelog"))
        rows = [
            f"{self.task_id} closed  "
            f"{config.relative(config.path(self.removed_in))}:{self.removed_from} removed, "
            f"already {self.marker} in {ledger}:{self.recorded.lineno}",
            "  ledger   untouched: the entry was already there",
        ]
        if self.dropped is not None:
            rows.append(f"  dropped  {self.dropped} from {_prose_file(config, self.prose)}")
            if self.nested:
                rows.append(f"  nested   {', '.join(f'§{a}' for a in self.nested)} went with it")
            rows += _cited_rows(self.cited)
            rows += _emptied_rows(self.emptied)
        if self.refreshed:
            rows.append(f"  derived  {', '.join(self.refreshed)} (dep annotations re-derived)")
        rows += _dequeued_rows(self.dequeued)
        rows += _unmet_rows(self.unmet)
        if self.decided is not None:
            rows.append(
                f"  decided  {config.relative(config.path('decisions'))}:"
                f"{self.decided.lineno}  {self.decided.rendered}"
            )
        rows += _scope_rows(self.scope, wrote)
        rows += _event_rows(self.event(config), "  ", config=config)
        return "\n".join(rows)

    def payload(self, config: Config, wrote: Sequence[str]) -> dict[str, object]:
        """The same answer as data, naming the file the line came out of (RK1088)."""
        from roadkeep.rendering import _prose_file, _scope_json  # noqa: PLC0415 - RK260

        return {
            "id": self.task_id,
            # The file the line actually came out of (RK1088), read off the closure rather than
            # assumed to be the roadmap: the act is the same against a different pair, and a
            # payload that named one file by having only one to name is one a second act would
            # quietly make wrong.
            "closed": {
                "file": config.relative(config.path(self.removed_in)),
                "role": self.removed_in,
                "removed": self.removed_from,
            },
            "recorded": {
                "file": config.relative(config.path("changelog")),
                "line": self.recorded.lineno,
                "marker": self.marker,
                "written": False,
            },
            "improvements": {
                "file": _prose_file(config, self.prose),
                "dropped": None
                if self.dropped is None
                else {"anchor": self.dropped.anchor, "title": self.dropped.title},
                "nested": list(self.nested),
                "cited": list(self.cited),
                "emptied": self.emptied,
                "kept": self.kept,
            },
            "refreshed": list(self.refreshed),
            "dequeued": self.dequeued,
            # And the task's own criteria that went with it (RK1268), for the same reason.
            "unmet": list(self.unmet),
            # The fourth file this door may write (RK1269), shaped as `recorded` above is.
            "decisions": None
            if self.decided is None
            else {
                "file": config.relative(config.path("decisions")),
                "line": self.decided.lineno,
                "rendered": self.decided.rendered,
            },
            "scope": _scope_json(self.scope, wrote),
            "event": self.event(config),
        }


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
    #: The earlier entry this one supersedes, as it now reads with the forward pointer on it
    #: (RK395). None on every `record add` that supersedes nothing, which is most of them.
    superseded: Entry | None = None
    #: Where a sentence already named this id, on the `--id` that was allowed because no
    #: line held it (RK1051). Reported and never swallowed: writing the entry a citation
    #: promised is the repair, and writing one it did not promise is the author's to see.
    mentioned: IdRef | None = None

    def save(self) -> tuple[Path, ...]:
        """Write the ledger, and the roadmap only if a line in it actually changed."""
        # The roadmap is passed only where a line in it changed, so it is not rewritten to
        # the same bytes: an untouched file with a moved mtime reads as an edit to every
        # hook watching it, and "touched nothing else" has to be true on disk.
        return save_all(self.ledger.document, self.roadmap if self.refreshed else None)

    @property
    def block(self) -> str:
        """As the file reads it back, and not as it was typed."""
        return self.ledger.entry.task.block

    def event(self, config: Config) -> dict[str, object]:
        """The **roadmap's** block state, as it is for every other mutator: a hook asking "is
        Block B finished" is asking about open work, and a record adds none."""
        from roadkeep.rendering import _event  # noqa: PLC0415 - RK260

        return _event(self.task_id, self.block, self.roadmap, config)

    def stated(self, config: Config, wrote: Sequence[Path]) -> str:
        """A ledger entry that had no roadmap line to leave (RK41).

        Beside :meth:`payload` since RK1170.
        """
        from roadkeep.rendering import _event_rows, _staging_rows  # noqa: PLC0415 - RK260

        ledger = config.relative(config.path("changelog"))
        rows = [
            f"{self.task_id} {self.marker} {ledger}:{self.ledger.lineno} "
            f"under Block {self.block}",
            # Said out loud, because the absence is the whole point: a reader of this output
            # has to be able to tell "there was no line" from "the roadmap edit was forgotten".
            # About the write and not about the work (RK1050, RK1051): this door is also how a
            # task that *was* planned gets the entry it is missing, and `planned never` was a
            # claim about the wrong thing on exactly the write that repairs one.
            "  roadmap  no line to remove: this door writes the entry and nothing else",
        ]
        if self.mentioned is not None:
            # The citation the occupancy check used to refuse over (RK1051). Printed rather
            # than refused *and* rather than swallowed: an entry that keeps a sentence's promise
            # and one that collides with it are the same write, and only the author can tell
            # them apart — so the address is given and the judgement is left where it belongs.
            rows.append(
                f"  cited    {config.relative(self.mentioned.path)}:{self.mentioned.lineno} "
                f"already names {self.task_id}: no line held it, so this entry is what it "
                f"now points at"
            )
        if self.superseded is not None:
            # The edit the caller did not spell, printed where every other derived write is:
            # the forward pointer is this command's fact, and a reviewer reads the diff by it.
            rows.append(
                f"  pointed  {ledger}:{self.superseded.lineno} "
                f"{self.superseded.task.id} now names {self.task_id} as what replaced it"
            )
        if self.refreshed:
            rows.append(f"  derived  {', '.join(self.refreshed)} (dep annotations re-derived)")
        rows += _staging_rows(config.relative(one) for one in wrote)
        rows += _event_rows(self.event(config), "  ", config=config)
        return "\n".join(rows)

    def payload(self, config: Config, wrote: Sequence[Path]) -> dict[str, object]:
        """The same answer as data, with the entry this one supersedes (RK395)."""
        from roadkeep.rendering import _wrote_json  # noqa: PLC0415 - RK260

        return {
            "id": self.task_id,
            "marker": self.marker,
            "changelog": {
                "file": config.relative(config.path("changelog")),
                "line": self.ledger.lineno,
                "rendered": self.ledger.rendered,
            },
            "roadmap": {"touched": bool(self.refreshed)},
            "refreshed": list(self.refreshed),
            # The other half of the transaction (RK395): null on every record that supersedes
            # nothing, and the earlier entry as it now reads otherwise.
            "superseded": None
            if self.superseded is None
            else {
                "id": self.superseded.task.id,
                "line": self.superseded.lineno,
                "rendered": self.superseded.raw,
            },
            # The sentence that already named this id, where `--id` was allowed because no
            # line held it (RK1051): null on every other record.
            "mentioned": None
            if self.mentioned is None
            else {
                "file": config.relative(self.mentioned.path),
                "line": self.mentioned.lineno,
            },
            "event": self.event(config),
            **_wrote_json(config, wrote),
        }


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

    def save(self) -> tuple[Path, ...]:
        """Write the ledger, and answer it (RK1130). Nothing else was opened, so nothing
        else can be touched — and the answer is what a `git add --` takes."""
        return self.ledger.save()

    def event(self, config: Config) -> dict[str, object]:
        """The roadmap is read, never written (RK67): the event's block state is the
        *roadmap's* for every mutator, and a duplicate removed leaves open work as it was."""
        from roadkeep.rendering import _event  # noqa: PLC0415 - RK260

        return _event(self.task_id, self.block, config.document("roadmap"), config)

    def stated(self, config: Config, wrote: Sequence[Path]) -> str:
        """Which of two entries went, and which line the decision keeps (RK67).

        Beside :meth:`payload` since RK1170.
        """
        from roadkeep.rendering import _event_rows, _staging_rows  # noqa: PLC0415 - RK260

        ledger = config.relative(config.path("changelog"))
        rows = [
            f"{self.task_id} {self.marker} {ledger}:{self.removed_from} removed, "
            f"duplicate of {ledger}:{self.kept}",
            f"  kept     {self.kept_marker} line {self.kept}: where the decision was found",
        ]
        if self.kept_marker != self.marker:
            # Two entries that disagree about the door are not one decision written twice, and
            # the later one is gone: which marker the ledger now states has to be said aloud.
            rows.append(
                f"  differed the entry removed said {self.marker}, so the ledger now states "
                f"{self.kept_marker}"
            )
        rows.append("  roadmap  untouched: an id the ledger still records changes no annotation")
        rows += _event_rows(self.event(config), "  ", config=config)
        rows += _staging_rows(config.relative(one) for one in wrote)
        return "\n".join(rows)

    def payload(self, config: Config, wrote: Sequence[Path]) -> dict[str, object]:
        """The same answer as data, with both entries' markers (RK67)."""
        from roadkeep.rendering import _wrote_json  # noqa: PLC0415 - RK260

        return {
            "id": self.task_id,
            "changelog": {
                "file": config.relative(config.path("changelog")),
                "removed": self.removed_from,
                "marker": self.marker,
            },
            "kept": {"line": self.kept, "marker": self.kept_marker},
            "roadmap": {"touched": False},
            **_wrote_json(config, wrote),
            "event": self.event(config),
        }


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
    #: How many continuation lines the write put back under the bullet (RK1049). Reported
    #: rather than inferred from the entry, because a caller reading `rendered` sees the
    #: first line only: a correction that kept four paragraphs and one that deleted them
    #: print identically, and this is the difference.
    below: int = 0

    @property
    def rendered(self) -> str:
        return self.entry.raw

    @property
    def lineno(self) -> int:
        return self.entry.lineno

    def save(self) -> tuple[Path, ...]:
        """Write the ledger, and answer it (RK1130). Nothing else was opened, so nothing
        else can be touched — and the answer is what a `git add --` takes."""
        return self.ledger.save()

    def stated(self, config: Config, wrote: Sequence[Path], undone_by: str | None) -> str:
        """What the correction moved, and whether it was written about work that held (RK124).

        Beside :meth:`payload` since RK1170. `undone_by` is a parameter for `wrote`'s reason and
        one more (RK1052): it is read off the ledger *before* the write, because correcting the
        sentence is what can remove the mark it is read from — so the record cannot hold it.
        """
        from roadkeep.rendering import _staging_rows  # noqa: PLC0415 - RK260

        where = config.relative(config.path("changelog"))
        # `below` as well as `changed` (RK1049): a correction that moved no field and rewrote
        # four paragraphs under the bullet is a write, and calling it unchanged here would be
        # the collapse that task closed, reported as a no-op.
        if not self.changed and not self.below:
            return f"{self.task_id} unchanged: the entry already reads that way"
        rows = [
            f"{self.task_id} amended  {where}:{self.lineno}  "
            f"({', '.join(self.changed) or 'tail'})",
            f"  {self.rendered}",
        ]
        if undone_by is not None:
            # The moment the clause matters most (RK1052): the author is composing an outcome
            # for work a later entry says did not hold, and `delivered` would have told them.
            # The two surfaces RK1042 joined are one fact again, said in the same words.
            rows.append(
                f"  undone   by {undone_by}: the decision this entry records was reverted, "
                f"so the outcome being corrected is one that did not hold"
            )
        if self.below:
            # Said out loud for the reason the absence is (RK1049): the line printed above is
            # the whole of what this command can render, and a reader who cannot see that four
            # paragraphs are still under it has to diff the file to learn whether they survived.
            rows.append(
                f"  kept     {self.below} continuation line(s) under the bullet, "
                f"verbatim: no field holds them"
            )
        rows += _staging_rows(config.relative(one) for one in wrote)
        return "\n".join(rows)

    def payload(
        self, config: Config, wrote: Sequence[Path], undone_by: str | None
    ) -> dict[str, object]:
        """The same answer as data, with the tail this write put back (RK1049)."""
        from roadkeep.rendering import _wrote_json  # noqa: PLC0415 - RK260

        return {
            "id": self.task_id,
            "file": config.relative(config.path("changelog")),
            # The line it was already on, because not moving it is the claim.
            "line": self.lineno,
            **_wrote_json(config, wrote),
            "rendered": self.rendered,
            "changed": list(self.changed),
            # The lines under the bullet this write put back (RK1049): `rendered` is the first
            # line, so a reader diffing the JSON cannot otherwise tell a kept tail from a
            # collapsed one.
            "below": self.below,
            # The id that reverted this one, or null (RK1042, RK1052): read off the ledger as
            # it stood, since correcting the sentence is what can remove the mark it is read
            # from.
            "undone_by": undone_by,
        }


def amend(
    config: Config,
    task_id: str,
    *,
    why: str | None = None,
    part: str | None = None,
    lines: int | None = None,
) -> Corrected:
    """Correct one ledger entry's sentence, or a partial's qualifier, in place (RK124).

    Validated before the write exactly as `record add` validates its fields (L1), against
    the ledger's own schema — so an over-length `why` is refused with the number, and the
    line that reaches disk is one this tool can read back (L3).

    Refused on an id the ledger states twice: which of two entries a correction was written
    about is not a fact any file holds, and `record drop` is the door for a duplicate.

    And refused on an entry that **wraps** unless `lines` says how many it replaces (RK179):
    the correction is written over the whole span, so on a hand-written ledger it deletes
    text the parse never held — and a write that silently removes prose is the one thing
    this door was narrow enough to be incapable of.

    Once `lines` above one says the caller read that span, a `why` carrying newlines writes
    it back (RK1049). The refusal that stood there is right about a task line and wrong about
    a ledger entry — the parser accepts a five-line entry and this was the verb offering to
    correct one it could only collapse, so the only lossless spelling was joining four
    paragraphs with `<br>` into a 2,400-character line. The first line is the `why` the
    schema checks, exactly as before; the rest is the tail, written verbatim because no
    field holds it. `lines` is what makes this legible rather than a mode: it is already the
    caller saying they read the span, and a multi-line `why` without it is still a shell
    that expanded something.
    """
    _refuse_absent(config, **{"--why": why, "--part": part})
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
        # Unless the roadmap still carries it as a **live partial**, which is the one state
        # this refusal's own sentence names and never asked about (RK1046). A ⏳ line beside
        # an unqualified entry is the two files contradicting each other — the line says a
        # half landed, the entry says the whole did — and every verb refused it: `ship` and
        # `retire` both raise `AlreadyRecorded`, the gate is deliberately silent (RK121), and
        # this door sent the caller to `ship --part`, which sent them back here. A cycle, and
        # each refusal correct about its own invariant.
        #
        # The docstring above is why this is the door that gives: adding a qualifier is wrong
        # where the line "is gone or closed", and here it is neither. So the write is exactly
        # the correction that makes the two files agree, after which the completion path a
        # partial already has — `ship <id>` with no `--part` — closes it.
        open_line = config.document("roadmap").by_id().get(task_id)
        if open_line is None or open_line.task.status != PARTIAL:
            raise NoQualifier(task_id, entry.lineno)

    sentence, below = _unwrapped(why, lines)
    wanted = replace(
        entry.task,
        why=entry.task.why if sentence is None else sentence,
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
    # The tail is not a field, so it is not in `changed` and cannot be compared to one: a
    # `why` whose first line already reads that way still rewrites the paragraphs under it,
    # and reporting "unchanged" there would be the collapse this task closed, silently.
    if not changed and not below:
        return Corrected(task_id=task_id, ledger=ledger, entry=entry)

    # Asked after `changed`, so an amend that alters nothing never demands a count for a
    # write it is not going to make.
    counted(task_id, where, entry, lines, verb="correcting it", keeps_tail=True)

    document = ledger.rewrite_entry(entry, ledger.schema.check(wanted), below)
    return Corrected(
        task_id=task_id,
        ledger=document,
        entry=document.by_id()[task_id],
        changed=changed,
        below=len(below),
    )


def _unwrapped(why: str | None, lines: int | None) -> tuple[str | None, tuple[str, ...]]:
    """Split a `why` the caller wrote as a span into its first line and its tail (RK1049).

    Only where `lines` above one says the caller read a wrapped entry, which is the whole
    door: everywhere else a newline in a one-line field is a shell that expanded something,
    and passing it through would turn `why.newline` — the refusal that names the cause and
    the remedy — into an entry silently grown by four lines.

    `splitlines` and not `split("\\n")`, because the terminator here is the pipe's: a stdin
    stream written on Windows arrives CRLF, and a tail split on the newline alone carries a
    stray carriage return into a file whose endings :meth:`Document.rewrite_entry` supplies.
    """
    if why is None or lines is None or lines < 2 or not why.splitlines()[1:]:
        return why, ()
    first, *tail = why.splitlines()
    return first, tuple(tail)


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

    def save(self) -> tuple[Path, ...]:
        """Write the ledger, and answer it (RK1130). Nothing else was opened, so nothing
        else can be touched — and the answer is what a `git add --` takes."""
        return self.ledger.save()

    def event(self, config: Config) -> dict[str, object]:
        """The roadmap is read and never written (RK67's rule, for the same reason): a block is
        where an entry is filed, so re-filing one leaves every open line exactly as it was."""
        from roadkeep.rendering import _event  # noqa: PLC0415 - RK260

        return _event(self.task_id, self.to_block, config.document("roadmap"), config)

    def stated(self, config: Config, wrote: Sequence[Path]) -> str:
        """Both positions, because the line does not keep its number (RK143).

        Beside :meth:`payload` since RK1170.
        """
        from roadkeep.rendering import _event_rows, _staging_rows  # noqa: PLC0415 - RK260

        where = config.relative(config.path("changelog"))
        if not self.moved:
            return (
                f"{self.task_id} unchanged: the ledger already files it under "
                f"Block {self.to_block}"
            )
        rows = [
            f"{self.task_id} moved  Block {self.from_block} → Block {self.to_block}  "
            f"{where}:{self.from_line} → :{self.lineno}",
            f"  {self.rendered}",
            "  roadmap  untouched: a block is where an entry is filed, not what it records",
        ]
        rows += _event_rows(self.event(config), "  ", config=config)
        rows += _staging_rows(config.relative(one) for one in wrote)
        return "\n".join(rows)

    def payload(self, config: Config, wrote: Sequence[Path]) -> dict[str, object]:
        """The same answer as data, naming both positions (RK143)."""
        from roadkeep.rendering import _wrote_json  # noqa: PLC0415 - RK260

        return {
            "id": self.task_id,
            "file": config.relative(config.path("changelog")),
            # Both, because the entry does not keep its number and a payload naming one
            # position would be the pretence this verb exists not to make.
            "from": {"block": self.from_block, "line": self.from_line},
            "to": {"block": self.to_block, "line": self.lineno},
            **_wrote_json(config, wrote),
            "moved": self.moved,
            "rendered": self.rendered,
            "roadmap": {"touched": False},
            "event": self.event(config),
        }


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
        role="changelog",
        config=config,
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

    def save(self) -> tuple[Path, ...]:
        """Write the ledger, and answer it (RK1130). Nothing else was opened, so nothing
        else can be touched — and the answer is what a `git add --` takes."""
        return self.ledger.save()

    def stated(self, config: Config, wrote: Sequence[Path]) -> str:
        """The new address, and the line that keeps the old one (RK127).

        Beside :meth:`payload` since RK1170.
        """
        from roadkeep.rendering import _staging_rows  # noqa: PLC0415 - RK260

        ledger = config.relative(config.path("changelog"))
        rows = [
            f"{self.task_id} → {self.to}  {ledger}:{self.lineno}",
            f"  {self.rendered}",
            f"  kept     {self.kept_marker} line {self.kept} still carries {self.task_id}: "
            f"every annotation elsewhere was written about that delivery",
        ]
        rows += _staging_rows(config.relative(one) for one in wrote)
        return "\n".join(rows)

    def payload(self, config: Config, wrote: Sequence[Path]) -> dict[str, object]:
        """The same answer as data, with the delivery the id stayed on (RK127)."""
        from roadkeep.rendering import _wrote_json  # noqa: PLC0415 - RK260

        return {
            "id": self.task_id,
            **_wrote_json(config, wrote),
            "to": self.to,
            "file": config.relative(config.path("changelog")),
            # The entry does not move: it keeps its line, so the ledger still reads in the
            # order work landed and the diff is the number.
            "line": self.lineno,
            "rendered": self.rendered,
            "kept": {"line": self.kept, "marker": self.kept_marker},
            "roadmap": {"touched": False},
        }


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
        if not _one_entry_twice(ledger, twins):
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
    # `--to`, this verb's own spelling for the number (RK1212).
    refuse_reuse(config, to, flag="--to")

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


def _one_entry_twice(document: Document, twins: tuple[Entry, ...]) -> bool:
    """Do these entries state the same thing, id and position aside?

    What the tool can read, and the whole of it: a slip records the same work again, so the
    marker, the symptom, the sentence, any qualifier and every line the bullet wraps onto
    all match. Anything else is a difference somebody wrote on purpose, and reading prose to
    decide whether it was a correction or a second delivery is the judgement L4 keeps out of
    this tool.

    The wrapped lines are compared and not the fields alone (RK179): on a hand-written
    ledger a `why` is only as much of the sentence as fits on line one, so two entries whose
    every parsed field matches can still diverge two lines down — and this door answering
    "the same" there is `drop` removing a delivery it was built to be incapable of removing.

    The **block** is deliberately not compared. It says where the entry was filed and not
    what it records, and the same entry appearing under two headings is exactly the slip
    this door was written for.
    """
    stated = {
        (t.task.status, t.task.symptom, t.task.why, t.task.part, _wrapped_onto(document, t))
        for t in twins
    }
    return len(stated) == 1


def _wrapped_onto(document: Document, entry: Entry) -> tuple[str, ...]:
    """The lines an entry owns below its first, verbatim — empty for every governed one."""
    return tuple(
        line.rstrip("\r\n") for line in document.lines[entry.index + 1 : entry.stop]
    )


def _refuse_absent(config: Config, **prose: str | None) -> None:
    """Refuse ledger prose that names a path this repository lacks (RK497, L1).

    Called with the arguments **this** verb was given, keyed by the flag that carries each,
    so the refusal names the one the caller has to correct rather than the sentence it landed
    in. Every one of them is asked, and the refusal names every token, for the reason a
    schema refusal states every violation at once: one problem per run turns a single fix
    into a conversation.

    Cheap on the sentences anybody means to write: :func:`~roadkeep.linting.unresolved` asks
    the filesystem per token and asks git only for one that fails (RK222).
    """
    # Deferred, and it is the gate: `linting` reads the files this module writes, so the
    # top-level edge would run the wrong way (RK260).
    from roadkeep.linting import unresolved  # noqa: PLC0415 - RK497

    file = config.relative(config.path("changelog"))
    for named, text in prose.items():
        if not text:
            continue
        missing = unresolved(config, text)
        if missing:
            raise NoSuchPath(named, missing, file)


def ship(
    config: Config,
    task_id: str,
    *,
    why: str | None = None,
    part: str | None = None,
    remainder: str | None = None,
    lines: int | None = None,
    superseded: str | None = None,
    recorded_in: str | None = None,
    decides: str | None = None,
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

    That completion is a **span** rewrite where the ledger arrived wrapped (RK193), and
    `lines` is the caller saying how many it replaces — the count `record amend` already
    takes, at the one other door reaching the same write. It is a flag on this verb rather
    than a detour through that one because the caller asked to finish work; it is refused on
    every path that replaces no entry, and its absence over a wrapped partial is refused too.

    `superseded` is the fourth, and the only one about the file this command **deletes**
    (RK310). A design is written when a task is filed and read when somebody claims it, and
    in between the codebase moves — measured in one block of eleven tasks, twice, where the
    section argued at length from a fact that had stopped being true and the implementation
    was smaller and better once it was checked against the code. Both times `ship` then
    deleted the section with no trace that its reasoning had been overtaken, so the only
    reader who could ever find out was the one who had already done the work. The clause is
    appended to the ledger's sentence, which is the one place the section's address and the
    outcome already meet: derived up to the address, prose from there on (L4), and refused at
    the two doors where it would be untrue — a line that pointed at no design, and a partial,
    whose section stays because the rest of the work still reads it.

    `recorded_in` is the fifth, and the other half of that one (RK1267). A section holds the
    investigation, the criterion and the decision, and the flag above types the deletion only
    as *stale*: nothing said where the part that outlives the code went, so a definition of
    done written as a design is deleted correctly and survives nowhere. The clause is composed
    by the same writer, into the same sentence, after the supersession where both were passed —
    and it is derived whole, the anchor being the pointer the line is losing and the value a
    path, so this writes no prose (L4). Refused at the same two doors, and at a third of its
    own: a path this repository does not have, which is `path.missing` asked before the entry
    lands rather than by the gate afterwards (RK497).

    `decides` is the sixth, and the only one that writes a **fourth file** (RK1269). The other
    two type the deleted section — stale, or moved — and this one takes the third of its three
    contents out whole: the decision, the constraint that has to stay true after the code
    moves. It lands as one line in the decisions role, under the same block and the same
    limits, with the task's own symptom as the claim and this sentence as the reason — which
    is a record this format already writes, an ADR being the pair it has had all along. Never
    the section copied over, which is the accreting rationale file this tool exists to refuse;
    refused where the project declares no such role, naming `declare decisions`, and on a
    partial, whose section stays and so has outlived nothing yet.
    """
    _refuse_absent(
        config,
        **{
            "--why": why,
            "--part": part,
            "--decides": decides,
            "--superseded-design": superseded,
            # Backticked so the one definition of missing can see it (RK497, RK1267): the
            # reader takes paths out of *prose*, and this argument is a bare token until the
            # clause is composed — which happens after every refusal this call can raise.
            "--recorded-in": None if recorded_in is None else f"`{recorded_in}`",
        },
    )
    if part is not None:
        if lines is not None:
            # Before the ledger is read at all (RK1128): what refuses here is the flag pair and
            # not the file, so a message about what the ledger holds would be an answer to a
            # question this path never asks.
            raise NoCompletion(
                task_id, config.relative(config.path("changelog")), also_part=True
            )
        if superseded is not None:
            raise NoSupersession(task_id, part)
        if recorded_in is not None:
            raise NoSupersession(task_id, part, "--recorded-in")
        if decides is not None:
            raise NoDecision(task_id, part)
        return _partial(config, task_id, part, why, remainder)
    recorded = _already_recorded(config, task_id)
    if recorded is None:
        return _depart(
            config,
            task_id,
            config.schema.shipped_marker,
            why,
            lines,
            superseded=superseded,
            recorded_in=recorded_in,
            decides=decides,
        )
    if why is not None:
        raise NoRestatement(task_id, recorded)
    if superseded is not None:
        raise NoRestatement(task_id, recorded, "--superseded-design")
    if recorded_in is not None:
        raise NoRestatement(task_id, recorded, "--recorded-in")
    if lines is not None:
        raise NoCompletion(task_id, config.relative(config.path("changelog")))
    # And this one is **not** refused here (RK1269): the two flags above land in a ledger
    # sentence this path does not write, and a decision lands in a file of its own — which
    # this path does write, because it is the closure that deletes the section.
    return _close(config, task_id, recorded, decides=decides)


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
    _refuse_absent(config, **{"--reason": reason})
    holder: str | None = None
    if superseded_by is not None:
        if superseded_by == task_id:
            raise NoSuchReplacement(superseded_by, task_id, itself=True)
        holder = _holding(Backlog.load(config), superseded_by)
        if holder is None:
            raise NoSuchReplacement(superseded_by, task_id)
    why = retiring(reason, superseded_by)
    return _depart(
        config,
        task_id,
        config.schema.retired_marker,
        why,
        replacement_in=holder,
        replacement=superseded_by,
    )


def _holding(backlog: Backlog, task_id: str) -> str | None:
    """The role whose file holds this id, or `None` when none of the three does (RK244).

    :class:`~roadkeep.backlog.Backlog` and not three `config.document` calls, because that
    is the reader that already knows how many files an id can live in — the set built by
    hand here counted two, and RK96 had made it three.
    """
    for role, document in (
        ("roadmap", backlog.roadmap),
        ("changelog", backlog.ledger),
        ("deferred", backlog.store),
    ):
        if document is not None and task_id in document.by_id():
            return role
    return None


#: How an entry names the one that replaced it (RK395). Parenthesised into the ledger's own
#: sentence by :func:`_parenthesised`, for `--superseded-design`'s reason (RK310): the line has
#: one prose slot, and the clause is a fact this command holds rather than prose it writes
#: (L4, RK8). The wording is `retire`'s, the shape being that verb with the target file changed.
_SUPERSEDED = "superseded by {replacement}"


class NotDecided(KeyError):
    """An id the decisions file does not carry, at the door that only reads it (RK1274).

    :class:`NotRecorded` one file over, and separate for its reason: a caller superseding a
    decision holds *that* file's address, and being told the ledger does not have it would
    send them to the file where it correctly is not. Which of the two ids is missing is named,
    because this call takes two and a message that said neither would be read twice.
    """

    def __init__(self, task_id: str, where: str, flag: str) -> None:
        self.task_id = task_id
        self.flag = flag
        super().__init__(
            f"{where} records no decision {task_id}, which is what {flag} names: a decision "
            f"is written by `ship --decides` at the moment a design is deleted, so the one "
            f"replacing this must already be filed before it can replace anything"
        )


class AlreadySuperseded(ValueError):
    """A decision this file already marks as replaced (RK1274).

    Refused rather than pointed a second time, which is the role's whole rule read forwards:
    nothing here is ever deleted, so an entry carrying two forward pointers is a chain a
    reader has to date to walk — and the file records no dates (a non-goal). One decision is
    superseded once; what replaces its replacement supersedes *that*.
    """

    def __init__(self, task_id: str, where: str, lineno: int, marker: str) -> None:
        self.task_id = task_id
        self.lineno = lineno
        super().__init__(
            f"{where}:{lineno} already marks {task_id} {marker}: a decision is superseded "
            f"once and the entry that replaced it is named in its own sentence — what "
            f"replaces the replacement supersedes that one, which is the chain read forwards"
        )


@dataclass(frozen=True, slots=True)
class Superseded:
    """One decision marked replaced, and the entry that replaced it."""

    task_id: str
    replacement: str
    document: Document
    lineno: int
    #: The sentence as it now reads, which is the whole of what the write changed.
    rendered: str = ""

    def save(self) -> tuple[Path, ...]:
        return self.document.save()

    def stated(self, config: Config, wrote: Sequence[Path]) -> str:
        from roadkeep.rendering import _staging_rows  # noqa: PLC0415 - RK260

        where = config.relative(config.path("decisions"))
        rows = [
            f"{where}:{self.lineno}  {self.task_id} superseded by {self.replacement}",
            f"  {self.rendered}",
            # The rule, said at the one door that could be mistaken for a deletion: both
            # lines stay and the marker is what says which is live.
            f"  kept     {self.replacement} stands and {self.task_id} is history — nothing "
            f"in this file is ever deleted",
        ]
        rows += _staging_rows(config.relative(one) for one in wrote)
        return "\n".join(rows)

    def payload(self, config: Config, wrote: Sequence[Path]) -> dict[str, object]:
        from roadkeep.rendering import _wrote_json  # noqa: PLC0415 - RK260

        return {
            "id": self.task_id,
            "superseded_by": self.replacement,
            "file": config.relative(config.path("decisions")),
            "line": self.lineno,
            "rendered": self.rendered,
            **_wrote_json(config, wrote),
        }


def supersede(config: Config, task_id: str, *, by: str) -> Superseded:
    """Mark one decision replaced by another, in the file that holds both (RK1274).

    The role's **one** departure, and what separates it from the ledger. A roadmap line leaves
    by three doors; a decision leaves by being replaced, so nothing here is deleted and the
    file grows only by decisions somebody actually made.

    `retire` is the wrong verb and its shape is the right one: that one starts from an open
    roadmap line, and a decision has none — the line it came from was in the ledger before
    the decision was written. So this starts from the decisions file itself and makes the two
    edits `record add --supersedes` makes one file over: the forward pointer onto the entry
    that is now stale, and its marker, in one write. Two records of one reversal that do not
    name each other is the state RK395 closed for the ledger, and this is that closure here.

    Derived end to end (RK8, L4): the clause names the replacing entry and the marker is the
    role's own retired one, so there is no sentence for a caller to spell two ways — and no
    reason field, because *why* one decision replaced another is the argument in the entry
    that replaced it, already written and one line away.
    """
    if not config.has("decisions"):
        raise NoDecisions(task_id, config.relative(config.source or config.root))
    where = config.relative(config.path("decisions"))
    document = config.document("decisions")
    if task_id == by:
        # Its own refusal and not `retire`'s, which names that verb and the abandoned door:
        # neither exists here, and a message about them would send the caller to the backlog.
        raise ValueError(
            f"{task_id} cannot supersede itself: what replaces a decision is a *second* "
            f"decision, filed by the `ship --decides` of the work that changed it — and this "
            f"call is the one that then says which of the two is live"
        )
    standing = _only(document, task_id, where, "the id")
    replacement = _only(document, by, where, "--by")
    schema = config.schema_for("decisions")
    if standing.task.status != schema.shipped_marker:
        raise AlreadySuperseded(task_id, where, standing.lineno, standing.task.status)
    wanted = replace(
        standing.task,
        status=schema.retired_marker,
        why=_parenthesised(standing.task.why, _SUPERSEDED.format(replacement=by)),
    )
    # `replace_task` and not a span rewrite, for `_supersede`'s reason (RK1053): the clause
    # lands in the `why`, which is the first line's text, so re-rendering that line reproduces
    # every field this entry holds and anything beneath it is not this write's to touch.
    updated = document.replace_task(standing, document.schema.check(wanted))
    return Superseded(
        task_id=task_id,
        replacement=replacement.task.id,
        document=updated,
        lineno=standing.lineno,
        rendered=updated.by_id()[task_id].raw.rstrip("\r\n"),
    )


def _only(document: Document, task_id: str, where: str, flag: str) -> Entry:
    """The one entry an id names in the decisions file, refused where there are none or two.

    `_supersede`'s two refusals, kept here rather than shared with it: that one reads the
    ledger and names `record` in what it says, and a caller holding a decision's address
    would be sent to the wrong file by a message that was right about the other one.
    """
    twins = tuple(entry for entry in document.entries if entry.task.id == task_id)
    if not twins:
        raise NotDecided(task_id, where, flag)
    if len(twins) > 1:
        raise Ambiguous(task_id, where, tuple(entry.lineno for entry in twins))
    return twins[0]


def record(
    config: Config,
    *,
    block: str,
    symptom: str,
    why: str,
    task_id: str | None = None,
    supersedes: str | None = None,
    lines: int | None = None,
) -> Record:
    """Write one ledger entry directly, for shipped work no open line can carry (RK41).

    The job, stated as the job rather than as the case that produced it (RK1050): every
    other door into the ledger begins from a roadmap line, so this is the one for work that
    has none. Never planned is the first instance and not the definition — a task that was
    planned, shipped, and recorded inside a *second* task's sentence is invisible to every
    reader that keys on an id and needs its own entry, and so does a revert
    (``supersedes``). A description naming only the first case reads as a refusal for the
    others, and the search moves on to verbs that really do refuse.

    The fields are refused at input exactly as `add` refuses them (L1), against
    :meth:`~roadkeep.kernel.schema.Schema.as_ledger` rather than the roadmap's schema — so the
    marker is ✅, the block heading must already be declared in the ledger, and a dep or a
    pointer is not accepted rather than dropped: there is no open line for a dep to be a
    planning fact about, and no rationale section for a pointer to resolve to.

    The id is derived like any other (RK4) and refused if anything anywhere already
    mentions it, so recording cannot quietly claim an id the roadmap is holding. The
    `symptom` rule is the one that must not soften: what did not work, stated so it could
    have been falsified — never the name of the patch that closed it (L4 leaves that to
    the caller, here as everywhere).

    ``supersedes`` is the **revert**, and it is one transaction rather than two (RK395).
    Measured on Turing: T922 and T924 shipped and were reverted an hour later, and recording
    that took three attempts at the wrong verb. `retire` starts from a roadmap line `ship`
    had already removed; `record drop` refuses anything but a duplicate, rightly, because
    removing the only record of a decision is deleting history. What was left was this
    command — which wrote the revert as an entry the earlier one knew nothing about, so a
    reader who found T922 read an entry saying it shipped with no pointer to the one saying
    it did not hold. Both entries stay, because both happened; what is added is the forward
    pointer `retire --superseded-by` already writes one file over, appended to the earlier
    sentence in **this** write rather than in a second one a crash can lose.
    """
    mention: IdRef | None = None
    if task_id is None:
        task_id = next_id(config)
    else:
        # `refuse_occupied` and not `refuse_reuse` (RK1051): the other doors move a task
        # *onto* a number and this one gives a number the entry it lacks, so a sentence
        # citing the id is the state being repaired rather than the collision being avoided.
        mention = refuse_occupied(config, task_id)

    _refuse_absent(config, **{"--symptom": symptom, "--why": why})
    ledger = config.document("changelog")
    marker = config.schema.shipped_marker
    if supersedes is not None:
        ledger = _supersede(config, ledger, supersedes, task_id, lines)
    insertion = place(
        ledger,
        Task(id=task_id, status=marker, block=block, symptom=symptom, why=why),
        role="changelog",
        config=config,
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
        # Read back off the document the insertion left, because the entry above it moved if
        # the new line landed first — a report naming the line it was read at would name
        # whatever came up into its place (the care RK357 takes about the same address).
        superseded=(
            None if supersedes is None else insertion.document.by_id()[supersedes]
        ),
        mentioned=mention,
    )


def _supersede(
    config: Config,
    ledger: Document,
    task_id: str,
    replacement: str,
    lines: int | None,
) -> Document:
    """Append the forward pointer to the entry this write replaces (RK395).

    The rewrite `record amend` makes, with the sentence derived rather than passed: what a
    reverted entry is missing is not a better `why`, it is the address of the entry that says
    it did not hold — and an author asked to compose that clause is an author who can spell it
    two ways (RK8's split, and `retire --superseded-by`'s exactly).

    Its refusals are that verb's, for the same reasons: an id the ledger does not carry has no
    sentence to append to, and an id it carries **twice** leaves which entry unanswerable by
    any file. Nothing is written by this function; the caller places the new entry into what it
    returns, so the two edits reach disk together or neither does.

    A **wrapped** entry costs nothing here, and used to cost a `--lines` (RK179, RK1053). The
    clause is appended to the `why`, which is the text of the first line, so that line alone
    reproduces every field this task holds — and rewriting the span was authorising a deletion
    the write does not need, in a call that asked to change no word of somebody's paragraph.
    The count is therefore refused rather than accepted-and-ignored: see :class:`NoSpan`.
    """
    # No self-pointer check: the replacement is derived, or `refuse_reuse` refused an id any
    # file already mentions, so an entry naming itself is a state neither door can reach.
    where = config.relative(config.path("changelog"))
    twins = tuple(entry for entry in ledger.entries if entry.task.id == task_id)
    if not twins:
        raise NotRecorded(
            task_id, where, open_line=task_id in config.document("roadmap").by_id()
        )
    if len(twins) > 1:
        raise Ambiguous(task_id, where, tuple(entry.lineno for entry in twins))

    entry = twins[0]
    if lines is not None:
        raise NoSpan(task_id, where)
    wanted = replace(
        entry.task,
        why=_parenthesised(entry.task.why, _SUPERSEDED.format(replacement=replacement)),
    )
    # `replace_task` and not `rewrite_entry` (RK1053): the clause is appended to the `why`,
    # which is the text of the **first** line, so re-rendering that line alone reproduces
    # every field this task holds and the continuation beneath it is not this write's to
    # touch. Rewriting the span was the wider call — a caller who asked to add a pointer,
    # losing an entry's paragraphs, on the file whose purpose is that history survives.
    return ledger.replace_task(entry, ledger.schema.check(wanted))


def _partial(
    config: Config, task_id: str, part: str, why: str | None, remainder: str | None = None
) -> Partial:
    """Record the half that landed and leave the line open (RK121)."""
    roadmap = config.document("roadmap")
    ledger = config.document("changelog")

    entry = roadmap.by_id().get(task_id)
    if entry is None:
        raise NotOpen(
            task_id,
            config.relative(config.path("roadmap")),
            Whereabouts.of(config, task_id),
        )
    recorded = ledger.by_id().get(task_id)
    if recorded is not None:
        # A second partial would state the id twice in the ledger, which `lint` reports as
        # `id.duplicate` and which is the shape RK127 is about. One partial per task and
        # then a completion: `amend` is where a qualifier that has changed is corrected.
        #
        # Two refusals and not one (RK191): an id whose recorded entry carries a qualifier is
        # work that came in more halves than the model allows, and the answer there is the id
        # the next step is filed under — which the shared message, written for an id the
        # ledger *closed*, has nowhere to put.
        where = config.relative(config.path("changelog"))
        if recorded.task.in_halves:
            raise SecondPartial(
                task_id,
                where,
                recorded.lineno,
                recorded.task.part,
                suffix=config.schema.id_suffix,
            )
        # Closable exactly where `_already_recorded` would take the line (RK1045), which
        # since RK1075 is decided by the **entry's** qualifier and not by the roadmap's
        # marker: a ⏳ line beside an entry naming no half is the state that had no verb at
        # all, and the door that closes it is the one this refusal now names.
        raise AlreadyRecorded(
            task_id,
            where,
            recorded.lineno,
            recorded.task.status,
            closable=not recorded.task.in_halves,
        )

    if why is None:
        # A partial states an outcome too — this much of it works — so the half that
        # landed is no more entitled to the problem statement than the whole (RK142).
        raise NoOutcome(task_id, entry.task.why)
    landed = replace(
        as_recorded(entry.task, config.schema.shipped_marker, why), part=part
    )
    insertion = place(ledger, landed, role="changelog", config=config)
    # ⏳ where the project declares it, and the line's own marker where it does not: the
    # marker set is the project's (L6), and a command that invented one would write a line
    # its own gate refuses. Either way the line stays open, which is the claim.
    status = PARTIAL if PARTIAL in config.schema.markers else entry.task.status
    # The **open half, as data** (RK1233). `--part` records what landed and RK1226 put that on
    # the brief; what stayed an inference is the remainder — a reader handed `landed the parser
    # half` beside a symptom describing the whole, working out the rest. `--remainder` is the
    # caller's sentence for what is left, written into the line's own `why` in this same
    # transaction, so the open line states it and `brief` prints both halves as fields.
    #
    # The **roadmap line** and never a second field on the entry, which is the decision RK1226
    # declined to take and RK1233 settles: a forward-looking clause in the ledger is history
    # stating work that has not happened, and nothing would update it when the rest ships. The
    # open line is maintained by definition — `amend` reaches it and the final `ship` removes it.
    #
    # The `why` and not the symptom, because the symptom is the falsifiable claim `amend`
    # refuses to touch (RK7): a task half-delivered is still that symptom's task, and narrowing
    # the claim itself is `restate`'s act and not a shipment's.
    #
    # Validated like any other `why` before it is rendered: `replace_task` re-renders from data
    # and checks nothing, so a remainder over its limit would land as a line the gate refuses.
    reopened = replace(entry.task, status=status)
    if remainder is not None:
        reopened = replace(reopened, why=remainder)
        violations = config.schema_for("roadmap").validate(reopened)
        if violations:
            # Under the flag that carried it, but only where the rule broken is one this
            # argument could have broken (RK1262): a line already carrying drift in some other
            # field is not the remainder's fault, and framing it as one would send the caller
            # to edit the string they had just written correctly — this task's own defect,
            # pointed the other way.
            if any(one.field == RemainderRefused.BECOMES for one in violations):
                raise RemainderRefused(task_id, tuple(violations))
            raise SchemaError(tuple(violations))
    remaining = roadmap.replace_task(entry, reopened)
    derived = refresh(
        Backlog.during(config, roadmap=remaining, ledger=insertion.document)
    )
    return Partial(
        task_id=task_id,
        ledger=insertion,
        roadmap=derived.document,
        part=part,
        remainder=remainder,
        status=status,
        refreshed=derived.changed,
        marker=config.schema.shipped_marker,
    )


def _depart(
    config: Config,
    task_id: str,
    marker: str,
    why: str | None,
    lines: int | None = None,
    *,
    replacement_in: str | None = None,
    replacement: str | None = None,
    superseded: str | None = None,
    recorded_in: str | None = None,
    decides: str | None = None,
) -> Departure:
    """The one transaction both doors are: validate everything, then write nothing yet."""
    roadmap = config.document("roadmap")
    ledger = config.document("changelog")

    entry = roadmap.by_id().get(task_id)
    if entry is None:
        raise NotOpen(
            task_id,
            config.relative(config.path("roadmap")),
            Whereabouts.of(config, task_id),
        )
    where = config.relative(config.path("changelog"))
    # Before the ledger is consulted (RK1081): a departure that lands while the store still
    # carries the id writes a contradiction rather than resolving one, and the file that can
    # hold a third line for it is the one RK96 added and no pairwise check reached.
    if config.has("deferred") and config.path("deferred").is_file():
        paused = config.document("deferred").by_id().get(task_id)
        if paused is not None:
            raise AlsoPaused(
                task_id, config.relative(config.path("deferred")), paused.lineno
            )
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
        and duplicate.task.in_halves
        and marker == config.schema.shipped_marker
        else None
    )
    if duplicate is not None and completing is None:
        if duplicate.task.in_halves:
            raise PartRecorded(
                task_id, where, duplicate.lineno, duplicate.task.part, duplicate.task.status
            )
        raise AlreadyRecorded(
            task_id,
            where,
            duplicate.lineno,
            duplicate.task.status,
            # Reached only where the entry carries no qualifier — a duplicate that does is
            # `PartRecorded` above — so the closure path takes this line (RK1075).
            closable=not duplicate.task.in_halves,
        )
    if why is None:
        # `retire` always arrives with a derived sentence, so this is the ship path alone.
        raise NoOutcome(task_id, entry.task.why)

    # Split before `--superseded-design` is appended and before anything else reads the
    # field (RK1053): the clause belongs at the end of the *sentence*, and appending it to
    # a `why` that carries the whole span would land it under the last paragraph. Guarded
    # by `completing`, so the count cannot open the span on a path that places a new line.
    why, below = _unwrapped(why, lines if completing is not None else None)

    # The author's half, kept so a refusal about the composed sentence can name the parts
    # (RK1261): from here on `why` may be two arguments and a wrapper, and by the time a gate
    # reads it there is one field to blame.
    authored = why
    if superseded is not None:
        # Derived up to the address and prose from there on, the split every field this tool
        # fills in takes (RK8, RK310): the anchor is the pointer the line is losing, which is
        # the one fact about the deleted design that survives nowhere else, and what it turned
        # out to be wrong about is the author's. Into the `why` rather than into a slot of its
        # own, because the ledger's sentence is already where the outcome is read and a second
        # field is a second thing every projection, every limit and every parse has to learn.
        if entry.task.ref is None:
            raise NoDesign(task_id)
        why = _superseding(why, entry.task.ref, superseded)

    # After the supersession and never before it (RK1267): the two clauses read as a pair —
    # what the design was wrong about, then where the part that was right went — and the
    # order the ledger publishes them in is decided here rather than by which flag was typed
    # first. Derived whole, there being no prose in an address and a path (L4).
    overtaken = why
    if recorded_in is not None:
        if entry.task.ref is None:
            raise NoDesign(task_id, "--recorded-in")
        why = _recording(why, entry.task.ref, recorded_in)

    # The count is about the entry a completion rewrites, so it is refused wherever there is
    # no such entry rather than dropped (RK193): every other path places a new one.
    if completing is None and lines is not None:
        raise NoCompletion(task_id, where)

    recorded = as_recorded(entry.task, marker, why)
    if superseded is not None or recorded_in is not None:
        # Before `place` validates, because from there on the two arguments are one field
        # (RK1261). The allowance is the ledger's own and not `why_max` — `why_budget` is what
        # refuses, so a message quoting anything else would name a number the write does not
        # use, which is the defect RK183 closed for the roadmap's line.
        grammar = config.schema_for("changelog")
        allowed = grammar.why_budget(recorded)
        # Each clause against the sentence it joined, in the order they were composed, so the
        # refusal names the one that pushed the total over and attributes the room to what can
        # actually give way (RK1267) — a single check over the pair would charge the overrun
        # to whichever class was written first.
        if superseded is not None and width(overtaken) > allowed >= width(authored):
            raise SupersessionCrowded(
                task_id,
                authored=authored,
                note=superseded,
                composed=overtaken,
                limit=allowed,
                source=grammar.source_of("why_max"),
            )
        if recorded_in is not None and width(why) > allowed >= width(overtaken):
            raise RecordingCrowded(
                task_id,
                outcome=overtaken,
                clause=f"`{recorded_in}` under §{entry.task.ref}",
                composed=why,
                limit=allowed,
                source=grammar.source_of("why_max"),
            )
    if completing is not None:
        # The same write `record amend` makes, so the same count (RK193). A completion drops
        # the qualifier *and states a different outcome*, and a wrapped entry's `why` is only
        # as much of the sentence as fits on line one — so rewriting that line alone leaves
        # the half's old tail under a sentence claiming the whole delivery, which is the
        # majority shape on the corpus (10 of Shio's 12 partials wrap). The count is a flag on
        # `ship` and not a detour through `record amend` because the caller asked to finish
        # work, not to fix a word; what it may never be is absent, `rewrite_entry` deleting
        # prose no field of this task holds.
        #
        # And the same tail, for the same reason (RK1053): the count says the caller read
        # the span, so `--why` may write it back rather than only collapse it. Otherwise
        # finishing the majority-shape partial is what deletes the paragraphs under it.
        counted(
            task_id, where, completing, lines, verb="completing it", keeps_tail=True
        )
        # Checked here, where `place` checks it on every other path (L1): this branch
        # rewrites an entry instead of placing one and was the one call that reached disk
        # unvalidated — a `why` carrying a newline landed as a two-line entry whose second
        # line no field held. Found writing the tail above, which is what made it matter:
        # the split is authorised by `--lines`, and without this the first line is not.
        replaced = ledger.rewrite_entry(completing, ledger.schema.check(recorded), below)
        insertion = Insertion(document=replaced, entry=replaced.by_id()[task_id])
    else:
        insertion = place(ledger, recorded, role="changelog", config=config)
    remaining = remove_entry(roadmap, entry)
    # One more change to a document already in hand (RK327): the queue names work, this line
    # is the work, and no state exists where the line has left and the order still names it.
    # Composed before the roadmap is touched, like everything else here: a decisions file that
    # refuses this line costs three untouched files rather than a departure half made.
    decided = _decided(config, entry.task, decides)
    remaining, dequeued = queueing.without(remaining, config, task_id)
    # And the task's own criteria list, in the same rewrite and for the same reason (RK1268):
    # the heading is addressed by an id this write is spending, so leaving it would file a
    # question about work the ledger already answers. A block's list is untouched — that one
    # outlives its lines, which is the whole difference between the two addresses.
    remaining, unmet = criteria.without(remaining, task_id)
    prose, dropped, kept, taken, cited, emptied = _drop_section(
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
        prose=prose,
        dropped=dropped,
        kept=kept,
        nested=taken,
        cited=cited,
        emptied=emptied,
        refreshed=derived.changed,
        marker=marker,
        superseded=superseded,
        recorded_in=recorded_in,
        decided=decided,
        dequeued=dequeued,
        unmet=unmet,
        dependents=tuple(
            e.task.id for e in derived.document.entries if task_id in e.task.dep_ids
        ),
        replacement_in=replacement_in,
        replacement=replacement,
        root=config.root,
        # Read off the roadmap as it *was*, and before `save` releases the claim (RK294): the
        # line still carries 🛠 here, and a claim is only ever read against that marker.
        scope=claiming.departing(config, task_id, roadmap.entries),
    )


def _decided(config: Config, task: Task, decides: str | None) -> Insertion | None:
    """The one line a departure files into the decisions role, or `None` (RK1269).

    An ADR read as this format is an id, a marker, one falsifiable claim and a reason, so the
    record is composed the way the ledger's is: the task's own symptom is the claim — a
    decision is *about* the problem the line stated, and restating it here would be the second
    sentence RK142 refuses to inherit for the other file — and the author's `--decides` is the
    reason. Under the role's own grammar, so the marker is the project's ✅ and the deps and
    the pointer are refused rather than dropped: the section this line survives is being
    deleted in the same transaction, and a pointer to it could not resolve.

    Validated here and written by nobody yet, which is what makes the fourth edit part of the
    same all-or-none: a `--decides` over its limit costs a refusal and leaves four files
    exactly as they were.
    """
    if decides is None:
        return None
    if not config.has("decisions"):
        raise NoDecisions(task.id, config.relative(config.source or config.root))
    try:
        return place(
            config.document("decisions"),
            as_recorded(task, config.schema_for("decisions").shipped_marker, decides),
            role="decisions",
            config=config,
        )
    except SchemaError as error:
        # The claim is inherited and the remedy is not the one every symptom overrun gets
        # (RK1281): that message sends the author to the rationale section, which *this ship
        # is deleting*, and `--decides` writes no symptom for them to shorten. Re-raised
        # rather than widened, because the refusal is right and only its door was wrong.
        if any(one.field == "symptom" for one in error.violations):
            raise InheritedClaim(task.id, error, config.relative(config.path("decisions")))
        raise


def _superseding(why: str, anchor: str, superseded: str) -> str:
    """The outcome with the overtaken design named inside it, as one sentence (RK310).

    The note is the author's verbatim. A full stop *inside* it is still two sentences and is
    still refused, which is right — the second sentence belongs in the design file the same
    way it does anywhere else, and there is no case for saying it in the one clause whose
    subject is a design that no longer exists.
    """
    return _parenthesised(why, f"design §{anchor} superseded: {superseded}")


def _recording(why: str, anchor: str, path: str) -> str:
    """The outcome with the deleted design's new address named inside it (RK1267).

    Derived end to end, which is what separates it from :func:`_superseding`: the anchor is the
    pointer the line is losing and the path is a file this repository has, so there is no half
    of this clause the author writes and none of it is prose (L4). Backticked because that is
    how every other path in a ledger sentence is spelled, and how the gate recognises one.
    """
    return _parenthesised(why, f"design §{anchor} recorded in `{path}`")


def retiring(reason: str, superseded_by: str | None) -> str:
    """The ledger's sentence for a line that left without shipping (RK1305).

    A derived prefix and the author's own sentence, which is the split every field the tool
    fills in already makes (RK8): *superseded by RK41* is a fact this command holds, and the
    reason is prose it will not write (L4).

    Its own function so that :func:`~roadkeep.budgeting.budget` can price the sentence before
    it exists. That prefix is **structure spent inside a prose field** — mandatory, derived,
    and counted against the same 200 the reason is refused by — so a caller drafting against
    the published limit is drafting against a number the write does not use. Measured while
    retiring a task in an adopting project: the reason was refused three times running, at
    250, 212 and 205, and each rewrite cut a clause out of the one field whose job is to carry
    evidence. One writer, so the price and the write cannot come apart.
    """
    if superseded_by is not None:
        return f"superseded by {superseded_by}: {reason}"
    return f"abandoned: {reason}"


def supersession_cost(anchor: str) -> int:
    """What `--superseded-design` costs the ledger's sentence before its note (RK1261).

    The other half of that task, and the one that arrives in time to be useful: `brief` quotes
    a shipping allowance without knowing a supersession will be appended to it, and a task
    about to lose its design is exactly when that allowance is read — so the number was wrong
    precisely when it was asked for. Unlike a `--part` qualifier, this one is **knowable**: the
    anchor is the pointer the line already carries, so only the note's own length is the
    caller's.

    Measured by composing with an empty note rather than by counting brackets, so it cannot
    drift when the clause is reworded — :func:`_superseding` stays the only writer of it.
    """
    stem = "x."
    return width(_superseding(stem, anchor, "")) - width(stem)


def recording_cost(anchor: str) -> int:
    """What `--recorded-in` costs that same sentence before the path (RK1275).

    :func:`supersession_cost`'s twin, and filed for the reason that one was: two flags landed
    in the ledger's sentence after the allowance learned to name one of them, so the figure a
    brief quotes was wrong by a clause whose size this tool knows. The **wrapper** is knowable
    for the same reason — the anchor is the pointer the line already carries — and the path is
    the caller's, which is the shape a `--part` qualifier is already described in.

    Measured through :func:`_recording` and never by counting brackets, so a reworded clause
    moves this number rather than leaving it behind.
    """
    stem = "x."
    return width(_recording(stem, anchor, "")) - width(stem)


def _parenthesised(why: str, clause: str) -> str:
    """A `why` carrying a derived clause **inside its terminator** (RK310, RK395).

    That placement is the whole of what this function is for: a `why` is one sentence and has
    to end like one, so a clause bolted on behind the full stop is two — refused by
    `why.sentences` and `why.no-terminator` at the door, which is the right refusal about the
    wrong thing. The author's own punctuation is what closes the composed sentence, so a `why`
    that never ended like one is still refused, and the terminator is moved rather than
    chosen: this writes no prose (L4), it parenthesises.

    One writer for both clauses the ledger derives — the design a ship overtook, and the entry
    a revert replaced — because two call sites composing the same shape is how one of them
    comes to be refused by the gate the other passes.
    """
    stem = why.rstrip()
    terminator = ""
    if stem and stem[-1] in ".!?":
        stem, terminator = stem[:-1].rstrip(), stem[-1]
    return f"{stem} ({clause}){terminator}"


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
      line that is still open is a leftover **unless the entry names a half**, which is the
      distinction RK121 made representable.

    **The marker alone is not that distinction** (RK1075). This read a ⏳ line as a live
    partial whatever the ledger said, and the state where the two disagree — a partial
    marker beside an entry carrying *no* qualifier — is then a line no verb closes: `ship`
    and `retire` refuse through this function, `defer` refuses because a pause is between
    open and terminal, and the gate is silent by design (RK121). Shio filed three capture
    reports on it and closed it with the editor. RK1046 had already made the same reading
    one door over — a ⏳ line beside an unqualified entry is the two files contradicting
    each other, the line saying a half landed and the entry saying the whole did — and the
    entry is the record of what shipped. So the qualifier is what refuses here, and the
    marker is what it used to be mistaken for.

    RK1046's exit stays and stops being the only one. It is the right door where the entry
    *should* carry a qualifier and does not; this is the door where the ledger is already
    right and the line is what is stale, and asking an author to write `--part "…"` to open
    it was asking them to claim a half nothing delivered.

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
    # The qualifier and not the marker (RK1075): an entry naming a half is a live partial and
    # closing it would drop the half that has not landed, where a ⏳ line beside an entry that
    # names none is the two files disagreeing about one delivery — and the ledger is the file
    # that records what shipped. Through `Task.in_halves`, which the gate reads too (RK1080).
    if recorded.task.in_halves:
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


def _close(
    config: Config, task_id: str, recorded: Entry, decides: str | None = None
) -> Closure:
    """Everything a departure does except the entry, which is already on disk (RK62).

    `decides` reaches here and the other two clauses do not (RK1269), and the split is what
    each is about: those land in the ledger's sentence, which this path deliberately leaves
    alone, and this one is a line in a file of its own — filed at the moment the section is
    deleted, which is an edit this door does make.
    """
    roadmap = config.document("roadmap")
    entry = roadmap.by_id()[task_id]
    decided = _decided(config, entry.task, decides)
    remaining = remove_entry(roadmap, entry)
    remaining, dequeued = queueing.without(remaining, config, task_id)
    # The rest of the transaction that stopped halfway (RK62, RK1268): the entry is on disk,
    # so what is left is every edit the roadmap side owes — the list among them.
    remaining, unmet = criteria.without(remaining, task_id)
    prose, dropped, kept, taken, cited, emptied = _drop_section(
        config, entry.task.ref, leaving=task_id
    )
    derived = refresh(
        Backlog.during(config, roadmap=remaining, ledger=config.document("changelog"))
    )
    return Closure(
        task_id=task_id,
        remaining=derived.document,
        removed_from=entry.lineno,
        recorded=recorded,
        prose=prose,
        dropped=dropped,
        kept=kept,
        nested=taken,
        cited=cited,
        emptied=emptied,
        refreshed=derived.changed,
        dependents=tuple(
            e.task.id for e in derived.document.entries if task_id in e.task.dep_ids
        ),
        dequeued=dequeued,
        unmet=unmet,
        decided=decided,
        scope=claiming.departing(config, task_id, roadmap.entries),
        root=config.root,
    )


def as_recorded(task: Task, marker: str, why: str | None) -> Task:
    """The same task as the ledger states it: one marker, no deps, no pointer.

    The pointer is dropped because the section it names is deleted in the same command,
    and the deps because a dependency is a planning fact that a departed line has none
    left to state — both of which the ledger schema (`as_ledger`) already refuses.

    **Public since RK1199**, and that is the whole of that defect. `brief` priced the ledger
    line by handing :func:`~roadkeep.budgeting.budget_of` the *roadmap's* task under the
    ledger's schema — and `Schema.render` appends `→ §<anchor>` whenever the task carries one,
    the pointer being split off before the grammar's own slot loop runs. So the structure it
    measured was ten characters wider than the line this function hands `ship`: `→ §RK1199` is
    exactly those ten, and the figure that existed to be composed against had ten it could not
    spend. `ref_required` is not the gate to close it with — that flag says a pointer is not
    *demanded*, and a schema that refused to render one a line carries would stop the file
    round-tripping (L3). The gate is this function, asked by both.
    """
    return replace(
        task,
        status=marker,
        deps=(),
        # And the requirements, for the deps' own reason one group over (RK1297): a
        # requirement says what has to be present for work to be finishable, and a line that
        # left has nothing to finish — the DualSense was on the desk or the work did not
        # ship. Cleared here rather than refused by the ledger's schema, because the slot is
        # written off the field and a ledger entry carrying one would render it.
        requires=(),
        ref=None,
        why=why if why is not None else task.why,
        # And at column zero (RK49): the nesting said which roadmap line this one belonged
        # under, and that line is not in the ledger — an indented entry would be nested
        # beneath whatever entry happened to precede it.
        indent="",
    )


def _drop_section(
    config: Config, anchor: str | None, *, leaving: str = ""
) -> tuple[
    Document | None,
    Section | None,
    str | None,
    tuple[str, ...],
    tuple[str, ...],
    str | None,
]:
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

    **Which file, is asked and not assumed** (RK196). RK172 taught the gate that a pointer
    addresses every governed prose role and RK186 taught the reader; this is the third and the
    one that *writes*. Reading `improvements` alone meant a project declaring `strategy` was
    told "this project declares no improvements file" while the section the departing line
    pointed at stayed — a prose file becoming a second changelog, which is what RK6 exists to
    stop. So the anchor is resolved across the declared roles, exactly as :func:`show` resolves
    it, and the drop is made against the file that declares it.

    Two roles declaring one anchor is **reported and not resolved**, for the reason absence is:
    which of the two a line meant is what `ref.ambiguous` asks the author, and a ship that
    deleted one of them would be answering that question by picking. The section stays, the
    ship is right, and the gate still says so.

    And a departure deletes only the section it **owns** (RK236), which is `lint`'s own reading
    of ownership and not a second one: under `ref_scheme = "id"` the anchor is the id, so a
    line's own design is always owned and always deleted; under an outline the anchor is an
    address in a file the project already keeps, and a section whose heading names no task is
    prose belonging to none — the gate says so by never reporting it orphaned. Turing's Block O
    lines pointed at `STRATEGY.md` §X.3 and §X.4, subsections of a standing GEO memo whose
    siblings survived only because no line happened to name them; retiring the last owner of
    each deleted 39 lines of positioning, and restoring it took the hand edit the guard denies.
    RK64 could not see it (four of five lines were live until the fifth) and neither could
    RK196 (§X.1 survived by the accident of also being an improvements heading).

    Kept and never refused, the direction the costs choose: prose left behind is one
    `section drop` away and a `lint` that reports nothing, while prose deleted is somebody's
    memo and a `git show`. No heuristic about what the prose *says* — only who it names, which
    is the claim RK61 already reads.
    """
    if anchor is None:
        return None, None, "the line carried no pointer", (), (), None
    roles = tuple(role for role in PROSE_ROLES if config.has(role))
    if not roles:
        return (
            None,
            None,
            f"this project declares no {' or '.join(PROSE_ROLES)} file",
            (),
            (),
            None,
        )
    others = _others_pointing(config, anchor, leaving)
    if others:
        return (
            None,
            None,
            f"§{anchor} is also pointed at by {', '.join(others)}",
            (),
            (),
            None,
        )

    named = " or ".join(config.relative(config.path(role)) for role in roles)
    # One resolver, called and not repeated (RK229): three verbs ask which file declares an
    # anchor, and the copy that answered it here is the copy `defer` did not have.
    holders = declaring(config, anchor)
    if len(holders) > 1:
        both = " and ".join(config.relative(config.path(role)) for role in holders)
        return (
            None,
            None,
            f"§{anchor} is declared by {both}: one anchor names one section, and a ship "
            f"that deleted one of two would be choosing which the line meant",
            (),
            (),
            None,
        )
    if not holders:
        return None, None, f"no §{anchor} section in {named}", (), (), None

    role = holders[0]
    # The grammar of a section lives in one place (RK9), so shipping calls it rather than
    # keeping a second opinion about where a section ends.
    prose = config.document(role)
    held = find(prose, anchor)
    if held is not None:
        claim = owners(held, config.schema.id_pattern())
        if leaving and leaving not in claim:
            return None, None, _unowned(anchor, claim), (), (), None
    deleted = drop_section(
        prose,
        anchor,
        claimed=pointers(config, leaving=leaving),
        where=config.relative(config.path(role)),
    )
    # `cited` and `nested` are both `drop`'s own answers (RK209, RK1170): the deletion knows
    # what it breaks and what it took, and a second reading of the same file here would be two
    # more things to keep true.
    return (
        deleted.document,
        deleted.section,
        None,
        deleted.nested,
        deleted.cited,
        _emptied(config, deleted.document, anchor),
    )


def _emptied(config: Config, document: Document, anchor: str) -> str | None:
    """The parent this drop left with no subsections under it (RK400).

    A `ship` deletes the task's own `§<id>` and names any section whose prose cited it. Under
    an outline it leaves one thing standing that nothing named: the **parent** the deleted
    children hung under. That paragraph was written as an introduction to them — it states
    the problem they solve, in the present tense — so shipping the last of `§X.1`–`§X.4`
    leaves `§X` telling a reader the work is open, and it is the first thing anyone reads
    about that family.

    Named and never rewritten. What the introduction should say instead is a `section amend`
    and a judgement (L4); noticing is not, and the tool is the only party that can.

    Silent under `ref_scheme = "id"`, where an anchor has no parent — and silent for a parent
    that still holds children, which is the ordinary case and not worth a line.
    """
    parent, dot, _ = anchor.rpartition(".")
    if not dot or config.schema.ref_scheme != "outline":
        return None
    if find(document, parent) is None or nested(document, parent):
        return None
    return parent


def _unowned(anchor: str, claim: tuple[str, ...]) -> str:
    """Why a section this line pointed at stayed (RK236), in the field a departure reports.

    Names who it belongs to where the heading says, because that is the author's next question
    and the answer is what makes the outcome checkable — and says "no task" where it names
    none, which is the standing-memo case and the one this was filed from.
    """
    if claim:
        return f"§{anchor} belongs to {', '.join(claim)}, so it is not this line's to delete"
    return (
        f"§{anchor} names no task in its heading, so it is prose belonging to none — the "
        f"reading `lint` makes when it declines to report it orphaned"
    )


@dataclass(frozen=True, slots=True)
class Delivered:
    """Every claim one block has already made good on, as one result (RK385, RK1170).

    The read that decides whether an `add` is a duplicate, so its two registers had better say
    the same thing: they were a printer and a payload builder in the same handler, agreeing by
    hand over a header, a state row, a bound and a per-entry mark.

    **Symptoms and not outcomes.** A shipped line states two things, and a duplicate collides
    with the problem it claimed rather than with the fix it delivered — an outcome is written in
    the vocabulary of the fix and never matches. So the rows carry the symptom.

    Unbounded unless a question narrows it. `--near` is not a truncation of this listing (RK442):
    it is the same read asked a narrower question, so what bounds it is the caller's sentence and
    not a number this verb chose — which is why the header says how many of how many, and why the
    order is published with no score under it (RK441).
    """

    #: The ledger, as the project spells it, and the label this was asked about.
    where: str
    standing: Standing
    entries: tuple[Entry, ...]
    #: What the block holds, beside what this call chose to show (RK442): a consumer handed five
    #: rows and no total reads a five-entry block.
    recorded: int
    #: The sentence `--near` narrowed by, or empty where the whole block is the answer.
    near: str
    #: Which of these the ledger later undid, by the entry that undid it (RK1042).
    reversed_by: Mapping[str, str]

    def __str__(self) -> str:
        rows: list[str] = []
        if not self.entries:
            # Said, never an empty stdout: "this block has delivered nothing" and "this command
            # found nothing to read" look the same to a caller, and only one of them is an answer.
            rows.append(f"{self.where}  {self.standing.named} has delivered nothing yet")
        elif self.near:
            # The count of what is *shown* against the count of what is there (RK442). This verb
            # was deliberately unbounded, because the entry that got elided is exactly the one
            # nobody read — so a bounded answer has to say it is bounded, in the header, or it
            # inherits the guarantee it just gave up.
            rows.append(
                f"{self.where}  {self.standing.named}, {len(self.entries)} nearest of "
                f"{self.recorded} delivered"
            )
        else:
            rows.append(f"{self.where}  {self.standing.named}, {self.recorded} delivered")
        rows.append(f"  block    {self.standing.sentence}")
        if self.near:
            # Said once, above the rows: the ordering is the whole answer and there is no
            # threshold under it, which is the sentence that keeps a reader from taking #1 as a
            # verdict (RK441). The rest of the block is one command away and named here.
            rows.append(
                f"  near     ranked by word overlap, nearest first — an order and not a "
                f"verdict; `{invocation()} delivered {self.standing.label}` is all "
                f"{self.recorded}"
            )
        for entry in self.entries:
            # Marked and never dropped (RK1042). This verb's own rule about retired lines: a
            # claim that did not hold is still a claim somebody made and argued about, so the
            # marker says which and nothing is conflated. A superseded entry carries no marker
            # of its own — the ledger spells it in the sentence — so the mark is written here.
            undone = self.reversed_by.get(entry.task.id)
            said = f" (undone by {undone})" if undone else ""
            rows.append(f"  {entry.task.status} {entry.task.id:<8} {entry.task.symptom}{said}")
        return "\n".join(rows)

    def payload(self) -> dict[str, object]:
        return {
            "file": self.where,
            "block": self.standing.label,
            # Beside the list and not instead of it (RK429): an empty `delivered` is the answer
            # to what was asked, and this is what the label it was asked about turned out to be.
            "standing": self.standing.payload(),
            "recorded": self.recorded,
            "near": self.near or None,
            "delivered": [
                {
                    "id": entry.task.id,
                    "marker": entry.task.status,
                    "symptom": entry.task.symptom,
                    "line": entry.lineno,
                    # Null and not omitted (RK1042): a consumer reading a missing key cannot
                    # tell "this held" from "this server is older", and the whole use of this
                    # payload is deciding a duplicate.
                    "undone_by": self.reversed_by.get(entry.task.id),
                    # The order and never a score (RK441): the absolute figure separates
                    # nothing, so a payload carrying it is one turn from the threshold that
                    # measurement rules out. Absent without `--near`, where the order is the
                    # ledger's and not an answer.
                    **({"rank": at} if self.near else {}),
                }
                for at, entry in enumerate(self.entries, start=1)
            ],
        }
