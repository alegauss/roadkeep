"""Every command's answer, once it is a string or a payload (RK493).

Split out of :mod:`roadkeep.cli`, which had grown to 8,489 lines holding the parser, the
82 handlers and this — so an edit to one verb's printed sentence was made in the file the
whole surface is in, and that file's growth rule appends to it every task.

The printers went first because theirs is the cut with no import cycle: not one of them
calls a handler or the parser, so the dependency runs one way and `cli` imports what it
prints with. That is also the half a verb's edit reads least — a handler decides what is
computed, and the sentence stating it is read once.

Two kinds live here and they answer the same question in the two registers RK4 declared:
`_print_*` writes the plain stdout a shell composes with, and `*_json` builds the payload
`--json` carries. Neither reads a file or takes a lock: what arrives is already the result
of a transaction, and what leaves is text. Refusals are a code and left where they were.

A third kind arrived with RK494 and belongs by the same rule: the line-makers two verb
families both spell — a section's word count, a governed file's name, the wiring report
`install` and `merge --check` each print. They are not `_print_*` only because they return
their sentence instead of writing it; the alternative was a shared module holding text.

The consequence to expect (RK79): :mod:`roadkeep.provenance` reads module names off a
traceback, so a refusal decided inside a printer now names this file. That is the truth
about which code answered, which is the whole point of that read.
"""

from __future__ import annotations

import argparse
from collections.abc import Iterable, Sequence

from roadkeep import claiming, criteria
from roadkeep.adopting import Estimate
from roadkeep.authoring import StatusChange
from roadkeep.backlog import Backlog, Stage
from roadkeep.briefing import NothingToBrief
from roadkeep.budgeting import Load
from roadkeep.claiming import Followed, Held
from roadkeep.config import Config, PROSE_ROLES
from roadkeep.deferring import Carried
from roadkeep.kernel.document import Document, Entry, Reject
from roadkeep.graph import Leverage
from roadkeep.history import Commit, Origin
from roadkeep.ids import Promise
from roadkeep.merging import (
    ABSENT,
    Attributes,
    CURRENT,
    DRIVER,
    DRIVER_KEY,
    Driver,
    MOVED,
    Registration,
    UNKNOWN,
    UNRUNNABLE,
    Wiring,
)
from roadkeep.picking import Choice, Claim
from roadkeep.provenance import invocation, served_by
from roadkeep.remedying import Door
from roadkeep.kernel.schema import UTF16_UNITS, width as measured_width
from roadkeep.verbs.refusing import EXIT_GATE, EXIT_OK


#: What every character figure this tool publishes is counted in (RK430). Declared in the
#: payload rather than assumed, because the defect was two counters both being right: a
#: consumer's gate reading UTF-16 and a `len` reading code points differ by one on the
#: status marker this tool writes, and neither number carried the unit that settles it.
#: The same string `[limits]`' own vocabulary spells it with (RK437), so the unit a payload
#: declares and the unit a report names are one fact and cannot drift into two spellings.
CHARACTER_UNIT = UTF16_UNITS


def _promise_json(promise: Promise | None) -> dict[str, object] | None:
    """The id a sentence named and the derivation stepped over (RK431), or nothing."""
    if promise is None:
        return None
    return {
        "id": promise.id,
        "where": promise.where,
        "derived": promise.derived,
        "sentence": promise.sentence,
    }


def _followed_rows(change: StatusChange, config: Config) -> list[str]:
    """What the marker did to the claim on its line (RK158), and never silently.

    A marker change is not obviously an assertion of ownership to whoever typed it, so the
    door says which of the two it just made — the same reason `pick` names the claim it took
    rather than only moving it.

    Rows and no longer a printer (RK1170), like every other phrasing two registers share: the
    verb composes its whole answer where the record is, and one seam writes it.
    """
    if change.claim is Followed.CLAIMED:
        return [f"  claimed  held for {config.held}m unless a marker moves it sooner"]
    if change.claim is Followed.RELEASED:
        # `dropped` and not `released`: every label in this output is padded to one width, and
        # the eight-letter word is the one that would not fit it.
        return ["  dropped  the claim on this line is released"]
    return []


def _event(task_id: str, block: str, roadmap: Document, config: Config) -> dict[str, object]:
    """What changed, where, and what became of that place (RK38).

    Three facts and no more. "This block is done" stays a *derived* fact about the files
    every mutator just wrote, so it cannot go stale the way a queued message can, and the
    tool never learns what happens next.

    The third of them is :class:`~roadkeep.backlog.Stage` and no longer a boolean (RK438).
    It was `not roadmap.holds(block)`, printed as `empty` — the roadmap holds no line under
    the label, which is the single moment a heading becomes droppable and is why RK408 hung
    the offer on it. RK429 then gave that word a second meaning, a block nothing has *ever*
    filed under as opposed to one that is `finished`, and the two disagreed out loud:
    shipping the last line of Block C here printed `Block C empty` beside an offer to
    withdraw the heading while `pick --block C` answered `Block C is finished: the ledger
    records 12 filed under it`. Both were right about their own question and one word was
    carrying them.

    So the event asks for the state the tool already computes, through the reader every
    query uses — `Backlog.during`, so the roadmap is the one this transaction just wrote and
    the ledger and the store are read (RK92). What the offer below hangs on is now *which*
    state, which is the thing it always needed: a paused block has nothing open and is not
    droppable, and under the old boolean it was told to run a command that refuses.
    """
    standing = Backlog.during(config, roadmap=roadmap).standing(block)
    # And **what is left**, in the shape `list` answers with (RK1164). The standing was read
    # here and reduced to one word, so a caller driving a block one task at a time followed
    # every ship with a `list` asking what this call already knew — measured at six ships and
    # six calls over one block. `stage` stays beside it: it is what the offer below branches
    # on and what every consumer written before this reads.
    return {
        "id": task_id,
        "block": block,
        "stage": str(standing.stage),
        "standing": None if standing is None else standing.payload(),
        # And **what decided whether the word is true** (RK1300). RK1265 put the definition of
        # done where a ship cannot delete it and said when to read it — before the block's last
        # open line ships — but nobody knows a line is the last one until this call answers, so
        # the reading always happened after, and only where a project's own skill file
        # remembered to say so. Measured on winwright: two blocks emptied in one sitting, both
        # events said `finished` with the standing and the count, and both readings then cost a
        # `criterion list` that this transaction had already read the file for.
        #
        # Only on `finished`, which is the one stage the question is owed at: `empty` is a
        # heading opened before its lines and has nothing to have satisfied, `paused` is not
        # done, and a standing category (RK1180) is caught up rather than finished — so a list
        # printed there would be asked forever and answered never. Nothing is enforced and
        # nothing could be: whether the work satisfies a criterion is a judgement (L4).
        "criteria": [
            {"lead": one.lead, "why": one.why}
            for one in (
                criteria.read(roadmap, block) if standing.stage is Stage.FINISHED else ()
            )
        ],
    }


def _drop_door(config: Config, block: str, stage: Stage) -> Door | None:
    """The heading this state makes droppable, or `None` (RK408).

    One reader for the printed offer, and **deliberately not a payload key**: RK38 decided the
    event carries three facts and no suggestion, on the argument that a consumer deriving the
    next command from the stage would be handed it twice. RK1307 swept the verbs whose payload
    dropped a door by omission and left this one alone, because a decision argued and held by a
    test is not an omission — the case for reopening it is that `[headings] permanent` (RK1121)
    made the offer depend on configuration the event does not carry, and that argument belongs
    on a line of its own rather than inside a task about a different class.
    """
    because = None if config.permanent_headings else _DROPPABLE.get(stage)
    if because is None:
        return None
    return Door(("block", "drop", block), because)


#: The two stages a heading is droppable in, and the clause that says which one it is
#: (RK438). `finished` and `empty` are the states where `block drop` can work: nothing open,
#: and nothing paused holding the label. `live` needs no offer and `paused` must not have
#: one — the store files lines under that heading, so the command refuses, and naming an
#: edit that cannot work is worse than naming no edit at all (RK16). The word beside the
#: event is what tells a paused caller why the offer is absent.
#: No row for :attr:`Stage.CURRENT` (RK1180), which is the whole of that task's first half: a
#: standing category is caught up and not finished, so there is no heading to offer to withdraw —
#: measured as three declare-empty-drop cycles in one session, each drop followed within the hour
#: by a finding that re-declared the block.
_DROPPABLE = {
    Stage.FINISHED: "its last open line just left",
    Stage.EMPTY: "no file files a task line under it",
}


def _event_rows(
    event: dict[str, object], indent: str = "", *, config: Config, standing: bool = False
) -> list[str]:
    """The event, and where the stage allows it the one command that state makes available.

    A heading becomes droppable the moment its block stops holding work, and a project whose
    roadmap reads as a list of what is left has every reason to withdraw it. Until RK408 the
    answer computed that state and stopped one word short of the verb — so the caller was
    told a block is finished and left to remember `block drop` from somewhere other than the
    sentence telling them it applies.

    The same commitment `add` already makes: an `add` without `--section` answers with the
    `section add` that closes the pointer it just created, rather than leaving the gate to
    report the dangling reference a turn later. This is that situation one verb earlier.

    A **suggestion and never an action**. Whether an emptied block is dropped or kept for
    work still to be filed under it is the project's call, `block drop` refuses anyway where
    the subtree is not blank in every file, and a ship that withdrew a heading nobody asked
    it to would be the tool deciding the shape of the plan.

    And since RK1121 the project may answer that call **once** rather than in every run's
    reading: `[headings] permanent` says the headings outlive the work filed under them, and
    the offer is then absent instead of hedged. `config` is a required keyword and not a
    defaulted one, because a printer that fell back to offering would put the old behaviour
    back on whichever call site was added next. The `stage` word stays either way — the state
    is a fact and only the suggestion was a question the file could answer.
    """
    stage = event["stage"]
    rows = [f"{indent}event    {event['id']}  Block {event['block']}  {stage}"]
    # What is left, on the line under it — for the two verbs a caller **drives a block** with
    # (RK1164). `ship` and `retire` are where the follow-up `list` was measured, and where the
    # live count is the question being asked: *is this block finished, and is there another*.
    # Every other write says the stage and no more, which is RK1143's rule about a line that is
    # never the next step; the payload carries the counts for all of them, a key costing a
    # client nothing to skip where a line costs every reader the same attention.
    #
    # `_print_standing` stays silent on a live block for its own reason: there an empty listing
    # was the filter's doing, and here the count is the answer.
    left = event.get("standing") if standing else None
    if isinstance(left, dict) and left.get("sentence"):
        rows.append(f"{indent}         {left['sentence']}")
    # And what decides whether `finished` is true (RK1300), on the two verbs a caller drives a
    # block with and for the reason the count above is there: the word arrives here, so the
    # list it is a claim about has to arrive here too or it is read somewhere else or not at
    # all. One row per criterion and the `why` with it — the lead alone is the address and not
    # the test, and a reader deciding whether to open the next block is reading the test.
    if standing:
        rows += [
            f"{indent}         done when  {one['lead']} — {one['why']}"
            for one in event.get("criteria", ())  # type: ignore[union-attr]
        ]
    # Composed once and rendered here (RK1307's shape, on the one member of that class it
    # left alone): the offer is a decision, and a printer deciding it again is a second
    # answer about whether a heading may go.
    door = _drop_door(config, str(event["block"]), Stage(stage))
    if door is not None:
        rows.append(
            f"{indent}         {door.what} — "
            f"`{invocation()} {' '.join(door.argv)}` withdraws the heading, "
            f"where this project drops one"
        )
    return rows


def _dequeued_rows(token: str | None) -> list[str]:
    """What a departure took out of the priority queue (RK327).

    Said and never silent, because a departure that quietly shortened the plan would be an
    ordering changed with no sentence about it — and the printed line is what a reviewer
    reads the diff against (RK298).

    Rows and no longer a printer (RK1170): three verbs share this sentence and each of them
    is moving its whole answer onto its record, which a function that prints cannot join.
    """
    if token is None:
        return []
    return [f"  dequeued {token} left the priority queue with the line"]


def _unmet_rows(leads: Sequence[str], went_with: str = "the line") -> list[str]:
    """What a departure took out of a criteria list (RK1268, RK1316).

    `_dequeued_rows`' sentence one list over and for its reason: the heading is addressed by an
    address this write spends, so it goes inside the transaction — and a definition of done
    that disappeared with no line about it is exactly the deletion RK1268 was filed against.

    ``went_with`` is **what** was spent, because two writes now spend an address: a departure
    spends the line and `block drop` spends the label (RK1316). One sentence with the noun
    passed in, and not two spellings of it: the fact is the same and only the address differs.
    """
    if not leads:
        return []
    return [f"  finished {lead} — its criterion left with {went_with}" for lead in leads]


def _carried_json(config: Config, carried: Carried | None) -> dict[str, str | None] | None:
    """The same answer as fields, so a caller reads the file rather than parsing a sentence."""
    if carried is None:
        return None
    return {
        "anchor": carried.anchor,
        "role": carried.role,
        "file": None if carried.role is None else config.relative(config.path(carried.role)),
        "absence": carried.absence or None,
    }


def _emptied_rows(parent: str | None) -> list[str]:
    """The parent this drop left introducing children that have all shipped (RK400).

    Beside the citation line and for the same reason: this is the only moment it can be
    said. `ship` deletes the task's own section and names what cited it; under an outline it
    leaves the **parent** standing, and that paragraph was written as an introduction to the
    children — it states the problem they solve, in the present tense, and it is the first
    thing anyone reads about that family.

    Noticing is the tool's; what the introduction should say instead is a `section amend` and
    a judgement (L4). So the sentence names the anchor and the door, and writes nothing.

    Rows and no longer a printer (RK1170): the verbs that say this are moving their whole
    answer onto their records, which a function that prints cannot be part of.
    """
    if parent is None:
        return []
    return [
        f"  emptied  §{parent} now has no subsections — its prose introduces work that has "
        f"shipped; `section amend {parent} --body -` is the edit, in this commit"
    ]


def _premise_rows(edits: Sequence[str], design: str) -> list[str]:
    """The two other places the claim a restatement replaced is also written (RK1196).

    Beside the citation line and the emptied one, and for their reason: this is the only
    moment it can be said. `restate` is the one verb here that *knows* a claim was wrong, and
    the `why` beneath that claim and the section arguing from it are written from the same
    premise — so from the next command on they read as prose somebody meant, and only the
    author who just corrected the symptom is holding the fact that they do not.

    A report and never a refusal, which is the difference between this and a rule. Whether the
    `why` still holds is a judgement about meaning and this tool has none (L4), so it names the
    doors with the id already in them and leaves the reading where it belongs.
    """
    if not edits:
        return []
    also = f"the `why` and §{design} were" if design else "the `why` was"
    return [
        f"  premise  {also} written from the claim this replaced — whether they still hold "
        f"is a reading",
        f"  next     {', '.join(f'`{one}`' for one in edits)} "
        f"{'is the edit' if len(edits) == 1 else 'are the edits'}, in this commit",
    ]


def _cited_rows(cited: Sequence[str]) -> list[str]:
    """Who is left pointing at prose this command deleted (RK206).

    Said here and gated nowhere, because this is the only moment it can be said: `ship`
    creates the dangling citation, `as_ledger` keeps no pointer, and from the next command
    on a reference to a section that shipped reads exactly like a typo. The ship is right —
    what the author owes is one edit in the same commit, and this is the sentence that asks
    for it.

    Rows and no longer a printer (RK1170), for the reason its neighbour above is.
    """
    if not cited:
        return []
    return [
        f"  cited    {', '.join(f'§{a}' for a in cited)} "
        f"{'cites' if len(cited) == 1 else 'cite'} it in prose — now resolving to nothing"
    ]


def _scope_rows(scope: claiming.Scope | None, wrote: Sequence[str] = ()) -> list[str]:
    """What the tree holds that this commit's claim does not name (RK280, RK294).

    Silent on a `None`, which is a project no claim spoke for — there the whole answer would
    be `git status` under a heading claiming to have read something.

    `wrote` is what the transaction **itself** just wrote, projections included (RK309), and
    it joins the staging line without joining the scope: the scope is what the holder said,
    verbatim, and these are not a declaration to be corrected but a record to be used. Six
    scopes across one block named the roadmap, the ledger, the rationale file and the README
    by hand, four of ten paths on the longest, and none of the four was a judgement anyone
    made. They leave `loose` for the same reason — a path this command wrote is not a change
    no claim accounts for, and saying both in one answer is the tool contradicting itself.

    **And the scope itself, at a departure** (RK298). `claim <id>` may leave it out, the
    caller having just declared it; a ship may not, because the ship is what *releases* it —
    after it, `claim <id> --porcelain` refuses with "no live claim" and the `status <id> 🛠` it
    names is refused too, the ledger now holding the id. So the one moment a commit needs the
    answer is the one moment the verb for it stops answering, and this is the output the
    committer is already reading. Spelled as the command rather than as a list, the shape
    every other unreachable next step in this tool takes (RK257): what the author does with
    these paths is stage them.

    Rows and no longer a printer (RK1170): a departure composes its whole answer where the
    record is, and the longest list in it cannot be the one part that writes itself.
    """
    if scope is None:
        # The staging line is still owed (RK1130). What needs a claim is the *subtraction* —
        # which paths are somebody else's — and a project that declared none was getting no
        # `git add --` line at all from the two verbs that had one, on the write with the most
        # files in it. So the silence stays where it belongs: on the three lists below.
        return _staging_rows(dict.fromkeys(wrote))
    rows = _staging_rows(dict.fromkeys((*scope.mine, *wrote)))
    rows += [f"  theirs   {one}  ({who} is holding it)" for one, who in scope.theirs]
    # Beside the staging and not instead of it (RK1120): the file is staged either way — this
    # transaction wrote it — and what the author needs is the ids inside it that this commit is
    # not about, which is the hunk to leave out rather than a path to drop.
    rows += [
        f"  shared   {one}  ({', '.join(others)} moved in it too, and staging it takes that)"
        for one, others in scope.shared
    ]
    # No filter here since RK1117: `loose` already excludes what this id explains, and the
    # subtraction moved to `split` because the two callers meant different things by the list
    # this used to read — a departure's `wrote` is what the transaction wrote, and a governed
    # file it wrote *and* somebody else had changed vanished from both reports.
    # And whether the index already carries it (RK1197): a `git commit` takes a staged path
    # whether or not the author reads a diff, and the diff they are reading is the other side.
    rows += [
        f"  loose    {one}  "
        f"({'staged already, and ' if one in set(scope.staged) else ''}no claim names it)"
        for one in scope.loose
    ]
    # The declared paths that would stage nothing (RK295). Named here rather than folded into
    # `mine`, which this list deliberately does not repeat: at a departure the work is done, so
    # a scope naming a file the tree does not have is a typo and not a file yet to be written.
    rows += [f"  typo?    {one}  (declared, and stages nothing)" for one in scope.idle]
    return rows


def _wrote_json(config: Config, paths: Iterable[Path]) -> dict[str, object]:
    """The `wrote` key, spelled once for every write that answers one (RK1129, RK1130).

    A fragment merged into each payload rather than a field on each record, because what a
    client does with it is the same `git add` whichever verb answered — and a key spelled per
    verb is a key that comes to differ per verb. Relative, like every path in every payload
    here: an absolute one is a fact about the machine that ran the command.
    """
    return {"wrote": [config.relative(one) for one in paths]}


def _print(rows: Iterable[str]) -> bool:
    """Write what a row producer returned, and say whether there was anything (RK1170).

    The seam while the verbs move onto their records: a register composes rows where the answer is
    and this writes them, so a caller that used to read *did it print* still can — `pick` closes
    with an event line only where a claim was actually taken.

    One definition and not one per verb file, which is the rule this whole task is about: three of
    them existed within an hour of the first, and a fourth file using the name without one is how
    106 tests found out.
    """
    for row in rows:
        print(row)
    return bool(rows)


def _staging_rows(paths: Iterable[str]) -> list[str]:
    """The `git add --` line, spelled in one place (RK298, RK1129).

    Every write says it — a departure, which releases the scope nothing can read back afterwards,
    an `add` refreshing a projection the commit was leaving behind, and twenty-six others — so the
    quoting and the label are here rather than at each of them. Nothing for an empty list: a
    command that wrote no file has no staging to advise, and a bare `git add --` is a line
    somebody would paste.

    Rows and no longer a print since RK1170: a write verb moving onto its record composes what it
    returns, and a helper that printed could only be reached from a handler.
    """
    staging = tuple(paths)
    if not staging:
        return []
    return [f"  stage    git add -- {' '.join(_shell(one) for one in staging)}"]


def _shell(path: str) -> str:
    """One path as a shell would take it: quoted only where a space would split it (RK298).

    Double quotes, the spelling :func:`~roadkeep.provenance._spelled` already uses for a
    command a reader copies — a path is declared verbatim (RK280) and may hold a blank, and a
    `git add --` line that split one in two would stage two files that do not exist.
    """
    return f'"{path}"' if " " in path else path


def _scope_json(
    scope: claiming.Scope | None, wrote: Sequence[str] = ()
) -> dict[str, object] | None:
    """The same lists as fields, so a caller stages them rather than parsing a sentence.

    `mine` stays the declaration and `wrote` is its own key (RK309): a client that merged them
    would be reading a scope this tool did not receive, and the two answer different questions.
    """
    if scope is None:
        return None
    return {
        "mine": list(scope.mine),
        "wrote": list(wrote),
        "theirs": [{"path": one, "claimed_by": who} for one, who in scope.theirs],
        # Already subtracted (RK1117), so the payload and the printed report cannot disagree
        # about which paths belong to nobody.
        "unclaimed": list(scope.loose),
        # Which of them the index already carries (RK1197). A subset and its own key, because
        # a client acting on `unclaimed` decides, and one acting on this has already been
        # committed to by a `git add` nobody in this session typed.
        "unclaimed_staged": list(scope.staged),
        "staging_nothing": list(scope.idle),
        # RK1120: per governed file, the other ids whose line moved in it. Its own key beside
        # `unclaimed`, because the two are different answers — a path nobody claims, and a path
        # this commit does claim that is carrying somebody else's line.
        "shared": [{"path": one, "ids": list(ids)} for one, ids in scope.shared],
    }


def _tree(root: str) -> str:
    """Which tree the report is about (RK299) — unconditionally, and in the shape `--version`
    already uses for which *engine* answered (RK79).

    Every path above is relative to this and nothing above says what it is relative to, so a
    run in the wrong directory produces a report that is right about a repository nobody asked
    about. Observed: 34 findings and a clean summary line for another project entirely, where
    the only clue was one filename the misread project does not have.

    Never conditional on it differing from the working directory. That is a second rule to
    remember, and it makes the attribution appear exactly when a reader has already stopped
    expecting it — the same argument as naming the files on a clean run.
    """
    return f" (in {root})"


def _served(config: Config) -> str:
    """The prefix this session's tools arrive under, or `""` where it has none (RK449).

    One reader for the four payloads that publish a remedy, because it is one question about
    one project and four calls to `serving` would be four places to forget it — and since
    RK488 it is `provenance.served_by`'s answer rather than a fourth spelling of it, the guard
    and the attestation having each written the same `or ""` for themselves.
    """
    return served_by(config.root)


def _row_json(entry: Entry) -> dict[str, object]:
    task = entry.task
    return {
        "id": task.id,
        "status": task.status,
        "block": task.block,
        "symptom": task.symptom,
        "why": task.why,
        "deps": [dep.render() for dep in task.deps],
        "ref": task.ref,
        "line": entry.lineno,
        "length": measured_width(entry.raw),
    }


def _miss_json(miss: Reject) -> dict[str, object]:
    return {
        "line": miss.lineno,
        "block": miss.block,
        "reason": miss.reason,
        "raw": miss.raw,
    }


def _nothing_json(nothing: NothingToBrief, args: argparse.Namespace) -> dict[str, object]:
    """The finished-block answer, in the shape it was asked for (RK409).

    `reason` is the sentence `pick` composed, carried verbatim rather than re-derived: the
    two answers about why nothing is ready would otherwise be two, and this is the one place
    a caller reads it without a task beside it.

    `held` is the field the prose already carried (RK154). "Every ready task is claimed by a
    worker who has not finished it" is the one absence a caller cannot act on without the
    ids — its own claim being the one it would otherwise ask about again next turn — so a
    payload that dropped them would make the machine-readable form the poorer answer.
    """
    return {
        "brief": None,
        "empty": True,
        "block": args.block,
        "designed": args.designed,
        "reason": nothing.reason,
        # The boolean could not carry the third state and still cannot (RK429): `empty` is
        # true for a finished block, a heading opened before its lines and a backlog whose
        # every line is blocked. It stays, because a caller reading it is reading the
        # question it asked; this says which of them answered.
        "standing": None if nothing.standing is None else nothing.standing.payload(),
        "held": [{"id": one.id, "since": one.since} for one in nothing.held],
        # `held`'s argument one axis over (RK1297): the absence a caller can act on least by
        # itself is the one whose remedy is another person, so the ids and the requirements
        # are exactly what an empty answer has to carry out of the call.
        "lacking": [
            {"id": one.id, "missing": list(one.missing)} for one in nothing.lacking
        ],
    }


def _load_json(load: Load) -> dict[str, object]:
    return {
        "path": load.path,
        "present": load.present,
        "over": load.over,
        "units": [
            {"unit": c.unit, "limit": c.limit, "taken": c.taken, "left": c.left, "over": c.over}
            for c in load.costs
        ],
        # Every section and not the largest few (RK1092), for `by_tool`'s reason: a caller
        # reading this to decide what to cut is reading a payload, and the terminal is
        # reading a report. Empty where the file is not on disk.
        # In the order the report shows them (RK1252) — ranked by the limit about to refuse,
        # so a consumer acting on the first row acts on the same section a reader would.
        "parts": [
            {
                "heading": part.heading,
                "lines": part.lines,
                "bytes": part.bytes,
                # The reading, per section (RK1253) — beside the two declared units and never
                # the key this list is ordered by, which is the ceiling's.
                "characters": part.characters,
            }
            for part in load.ranked
        ],
        # What this checkout pays over the counted number (RK1105), so a caller comparing two
        # machines has the difference as a field instead of inferring it from a mismatch.
        "translated": load.translated,
        # The same text in the unit a model is charged in (RK1250), and `null` where it does
        # not decode. Outside `units` deliberately: everything in that list is a declared
        # limit and this is a reading, so a caller iterating limits must not meet it.
        "characters": load.characters,
    }


def _pick_json(
    config: Config,
    choice: Choice,
    claim: Claim | None,
    event: dict[str, object] | None,
) -> dict[str, object]:
    """The answer as one object, beside `_brief_json` and for the same reason it exists."""
    entry = choice.entry
    return {
        "pick": None
        if entry is None
        else {
            "id": entry.task.id,
            "block": entry.task.block,
            "status": entry.task.status,
            "file": config.relative(config.path("roadmap")),
            "line": entry.lineno,
            "symptom": entry.task.symptom,
            "ref": entry.task.ref,
        },
        "tier": None if choice.tier is None else str(choice.tier),
        "reason": choice.reason,
        "scope": choice.block,
        # Beside `scope` and never instead of it (RK429): the label is what was asked and
        # this is what became of it, so a loop scoped to a block reads one word rather than
        # matching the sentence `reason` states it in.
        "standing": None if choice.standing is None else choice.standing.payload(),
        "alternatives": list(choice.alternatives),
        "ready": choice.ready,
        "blocked": choice.blocked,
        "outside": choice.outside,
        "paused": choice.paused,
        "needs_design": choice.needs_design,
        "undesigned": choice.undesigned,
        # `claimed` on a stalled line and `held` beside it are two facts with two names
        # (RK152): one is a line somebody is on that nothing could offer, the other is a
        # candidate the ranking stepped around.
        "stalled": [
            {"id": s.id, "blockers": list(s.blockers), "claimed": _held_json(s.claimed)}
            for s in choice.stalled
        ],
        "held": [{"id": h.id, "age": round(h.age), "since": h.since} for h in choice.held],
        "claimed": None
        if claim is None
        else {
            "taken": claim.taken,
            "from": None if claim.change is None else claim.change.before,
            "to": None if claim.change is None else claim.change.after,
        },
        "event": event,
    }


def _held_json(held: Held | None) -> dict[str, object] | None:
    """One claim as an age and a duration, or nothing where the line is not held."""
    if held is None:
        return None
    return {"age": round(held.age), "since": held.since}


def _claim_event(claim: Claim | None, config: Config) -> dict[str, object] | None:
    """RK38's event line for a claim, or nothing where no line was taken."""
    if claim is None or claim.change is None:
        return None
    entry = claim.change.entry
    return _event(entry.task.id, entry.task.block, claim.change.document, config)


# -- the sentences `pick` and `brief` share, as rows (RK1170) ------------------
#
# Rows and no longer prints. Both verbs are moving onto their records, and a register composes
# what it returns — a helper that printed could only be called from a handler, which is what kept
# two verbs' answers in the file that neither of their records is in. Every sentence below is the
# one that was printed, and every guard is where it was: what changed is who does the writing.


def _claim_rows(claim: Claim | None, config: Config) -> list[str]:
    """What a claim moved, on the two commands that can take one (RK119, RK149).

    One sentence and one place, because two commands printing the same fact in two wordings
    is two answers to "what did I just take". Empty where nothing was taken, which is what tells
    `pick` there is no event line to close with. The window comes from the config and is not
    a constant here (RK151): a project that declared its own would otherwise be told the
    default's number by the command that just applied its own.
    """
    if claim is None or claim.change is None:
        return []
    return [
        f"  claimed  {claim.change.before} → {claim.change.after}, held for "
        f"{config.held}m unless a marker moves it sooner"
    ]


def _held_rows(choice: Choice) -> list[str]:
    """Which ready lines a live claim kept out of the answer (RK119).

    Named and not counted, for the reason a claim carries no owner: the caller cannot be
    told whose it is, so the id is the only thing it can recognise its own by — and a line
    silently absent is one the caller asks about again on the next turn.
    """
    return [
        f"  held     {held.id} was claimed {held.since} ago and is not offered"
        for held in choice.held
    ]


def _undesigned_rows(choice: Choice) -> list[str]:
    """What `--designed` set aside, and never silently (RK83).

    Said rather than folded into `backlog`, whose three numbers are facts about the
    file: this one is a fact about the question, and a filter that hides its own effect is
    how "this block is finished" gets read off an answer that never looked at half of it.
    """
    if not choice.undesigned:
        return []
    return [f"  skipped  {choice.undesigned} ready and still needing designing"]


def _lacking_rows(choice: Choice) -> list[str]:
    """The ready lines this caller has no way to finish, one row each (RK1297).

    A row per line and not a count, unlike `--designed`'s above, and the difference is who
    the row is for: an undesigned line comes back to this caller the moment it writes the
    design, and one of these comes back to *somebody else* — so the id is what gets handed
    over and the requirement is what it is handed over for.

    `absent` and not `waiting`, because nothing here is pending: the line is ready, the
    backlog is right, and what is missing is in the room rather than in the files. Nor
    `needs`, which is the row an `add` prints for the section it left owing (RK1297).
    """
    return [
        f"  absent   {one.id} is ready and requires {', '.join(one.missing)}, "
        f"which this caller did not declare"
        for one in choice.lacking
    ]


def _waiting_rows(choice: Choice) -> list[str]:
    """What the declared priority is waiting on, where nothing ready answers it (RK1304).

    The `reason` above already says the queue names nothing ready, and that sentence is true
    and stops one step short: it does not say which task would change it. This is that step,
    beside the pick rather than instead of it — the pick may still be the right call when the
    blocker is expensive, and the case worth having is the other one.

    The **ids** and not a command, unlike every other door this file prints: releasing a token
    may take several of them and `ship` takes one, so an argv would be a fiction wherever the
    row is most needed. A token blocked on work outside the backlog has no id to name at all
    and says so — nothing this tool could offer would release it.
    """
    rows: list[str] = []
    for one in choice.waiting:
        lines = f"{one.lines} line{'' if one.lines == 1 else 's'}, blocked"
        if not one.releases:
            rows.append(f"  waiting  {one.token} — {lines} on work this backlog does not name")
            continue
        more = f" (of {one.of})" if one.of > len(one.releases) else ""
        released = "it" if one.lines == 1 else "them"
        rows.append(
            f"  waiting  {one.token} — {lines}; "
            f"{', '.join(one.releases)}{more} would release {released}"
        )
    return rows


def _stalled_rows(choice: Choice) -> list[str]:
    """A started task that cannot be continued is the one thing a pick must not hide.

    And whether somebody is holding it (RK152), because "started and stuck" invites
    unblocking the line while "claimed and waiting" invites leaving it alone — two answers
    one sentence used to serve.
    """
    rows: list[str] = []
    for stalled in choice.stalled:
        whose = (
            "" if stalled.claimed is None else f" and claimed {stalled.claimed.since} ago"
        )
        rows.append(
            f"  stalled  {stalled.id} is in progress{whose}, waiting on "
            f"{', '.join(stalled.blockers) or 'nothing this backlog names'}"
        )
    return rows


def _leverage_rows(leverage: Leverage) -> list[str]:
    """The reverse direction, which is the half of prioritisation a tool may supply.

    Bounded by :data:`~roadkeep.briefing.UNBLOCKS`, which is this printer's own number lifted
    to where the payload could read it (RK1301): the row had a cap and the payload had none,
    so one register showed four ids and the other spelled seventy-nine of them.
    """
    from roadkeep.briefing import UNBLOCKS  # noqa: PLC0415 - RK260

    shown = ", ".join(leverage.transitive[:UNBLOCKS])
    tail = " …" if leverage.count > UNBLOCKS else ""
    detail = f": {shown}{tail}" if shown else ""
    return [f"  unblocks {leverage.count} of {leverage.of} open{detail}"]


def _commits_json(origin: Origin) -> dict[str, object]:
    def one(commit: Commit | None) -> dict[str, object] | None:
        if commit is None:
            return None
        return {
            "sha": commit.sha,
            "short": commit.short,
            "date": commit.date,
            "author": commit.author,
            "subject": commit.subject,
            "reasoning": commit.reasoning,
        }

    return {
        "proposed_in": one(origin.proposed_in),
        "shipped_in": one(origin.shipped_in),
    }


#: What each `[ids]` key reads as off the ids themselves, and the condition under which
#: declaring it is right — the second half being the whole discipline of this line: the
#: report says what the ids spell and leaves the judgement where it belongs (RK110, L4).
_ID_SPELLS = {
    "pad": ("carry a leading zero", "if that width is this backlog's spelling"),
    "suffix": ("end in a lowercase letter", "if a split here keeps its number"),
}


#: What choosing each unread reading means, in the words the row's own clause already uses.
#: Keyed by the flag, because the flag is what the door carries and what a reader reruns.
_READING_WHAT = {
    "--prefix": "measure this file again with that family read as a track of the backlog",
    "--ref-scheme": "measure this file again with its sections addressed the way it addresses them",
}


def _readings(estimate: Estimate) -> tuple[tuple[str, str, int, Door], ...]:
    """The readings this file carries that the declared one leaves unread, each with its door.

    One writer for both answers (RK1147). The printed report has named the flag since RK285 and
    the payload published `{"scheme": "outline", "count": 20}` beside `line.non-canonical: 20`,
    leaving the door to be inferred from two counts — by an agent, which is the author this tool
    is built for. Both guards live here now, spelled once: a family the chosen ones already
    cover is not unread, and a scheme is reported only where the declared one left an address
    unread (RK288/RK305, :func:`_misread`).

    The door reruns **this** estimate, so it carries the flags that decided what was measured:
    `--sections` reads a rationale file and `--ledger` applies the changelog limits (RK76). A
    door dropping either would name a command whose answer is about a reading nobody asked for,
    which is worse than the count it was added to explain.
    """
    role: tuple[str, ...] = ()
    if estimate.unit == "section":
        role = ("--sections",)
    elif estimate.ledger:
        role = ("--ledger",)

    def door(flag: str, value: str) -> Door:
        return Door(
            argv=("adopt", estimate.path.as_posix(), *role, flag, value),
            what=_READING_WHAT[flag],
        )

    rows = [
        ("--prefix", prefix, count, door("--prefix", prefix))
        for prefix, count in estimate.prefixes
        if prefix not in estimate.families
    ]
    if _misread(estimate):
        rows += [
            ("--ref-scheme", scheme, count, door("--ref-scheme", scheme))
            for scheme, count in estimate.schemes
            if scheme != estimate.ref_scheme
        ]
    return tuple(rows)


def _reading_door(estimate: Estimate, flag: str, value: str) -> dict[str, object]:
    """One row's door as a payload key, or nothing at all.

    Absent and not ``"door": null``, for the reason a remedy is (see :func:`_remedy_json`): a
    consumer reading the key at all is one that acts on it, and a null is a row it has to
    test before it can use. No ``served`` is threaded here because `adopt` is deliberately
    unserved — it runs once, before the project exists (RK57) — so there is no tool call to
    publish beside the argv.
    """
    found = [d for f, v, _, d in _readings(estimate) if (f, v) == (flag, value)]
    return {"door": found[0].payload()} if found else {}


def _print_estimate(estimate: Estimate) -> None:
    where = estimate.path.as_posix()
    # Which of the three (RK485): a prefix nothing declared and nothing produced is the
    # schema's default, and calling that a reading is the estimate claiming a measurement.
    source = ""
    if estimate.inferred:
        source = " (inferred from the ids)"
    elif estimate.defaulted:
        source = " (the default — no id here was read, so the counts below assume it)"
    # No prefix on a rationale file: a section is addressed by its §, not by a family, so
    # naming one would be a claim the run never made (RK99).
    under = f"prefix {'/'.join(estimate.families)}{source}, " if estimate.families else ""
    print(f"{where}  {under}refs by {estimate.ref_scheme}")
    print(
        f"  read     {estimate.parsed} {estimate.unit}(s), {estimate.conforming} conform, "
        f"{estimate.changing} would change"
    )
    if estimate.lines and not estimate.recognised:
        # First of the three, because it is the one that says the headline above means nothing
        # about a backlog (RK376). A measurement and never a verdict on the file: what was read
        # against what is there, leaving "you named the wrong file" to the reader (L4).
        # Worded off `unit`, for the reason the `loose` line below is: the shapes a run reads
        # are entries and bullets on a backlog and headings on a rationale file (RK387), and
        # one sentence naming both would name neither run's.
        shapes = (
            "no entry, reject, table row, bullet or block heading"
            if estimate.unit == "line"
            else "no anchored section, and no heading carrying prose"
        )
        print(
            f"  unread   nothing in {estimate.lines} line(s) was read in any shape — {shapes}"
        )
    if estimate.tabular:
        # Directly under the headline, because it is the headline it explains: a table-shaped
        # backlog reads as 0 lines, which is what an empty file reads as (RK98).
        print(f"  table    {estimate.tabular} line(s) in a table this format does not read")
    if estimate.listed:
        # Beside it, and for the same reason (RK279, RK281) — this is the shape the headline
        # is most often explaining. Worded off `unit`, because the field holds one idea, "in
        # a shape this format has no reader for", and that is a bullet in a backlog and a
        # heading in a rationale file: one sentence for both would name neither.
        said = (
            f"{estimate.listed} plain bullet(s) under a block"
            if estimate.unit == "line"
            else f"{estimate.listed} heading(s) with prose and no anchor"
        )
        print(f"  loose    {said}, in no shape read here")
    if estimate.blocks:
        print(f"  blocks   {', '.join(estimate.blocks)}")
    # Both guards moved into `_readings` (RK1147), which is now the one place that decides
    # what is unread here — the payload publishes the same rows with the door beside them, and
    # two loops asking the same question in two functions is the drift that put a flag on one
    # surface and a bare count on the other. Only the *sentences* stay here.
    for flag, value, count, _ in _readings(estimate):
        # `prefix` takes a list now (RK74), so this names the flag instead of the limitation:
        # whether the spelling is a second track or a paste from another backlog is the
        # reader's call.
        if flag == "--prefix":
            print(
                f"  also     {count} id(s) spell {value}, unread here: "
                f"--prefix {value} if it is a track of this backlog"
            )
            continue
        scheme = value
        # The same sentence one field over (RK285). Shio read `0 conform, 65 would change`
        # under the default and `63 conform, 2 would change` under `--ref-scheme outline`,
        # with `ref.mismatch` on every line as the only signal — while the prefix half of the
        # same misreading already named its flag. The trailing clause keeps the judgement with
        # the reader for the reason that one does: whether a live outline is what this backlog
        # numbers by is a decision about the project, not a fact about the file.
        # Worded off `unit` for the reason the loose line is (RK288): on a backlog the
        # evidence is the pointers, on a rationale file it is the headings' own anchors,
        # and one sentence for both would name neither.
        spells = "pointer(s) spell" if estimate.unit == "line" else "heading(s) anchored"
        print(
            f"  also     {count} {spells} {scheme}, unread here: "
            f"--ref-scheme {scheme} if that is how this project addresses its sections"
        )
    # The one finding a per-file estimate could not reach (RK347), and a line here rather than
    # a refusal for the reason every other one is: `adopt` writes nothing and exits 0 (RK18),
    # and what an adopter is buying is the number *before* the commitment.
    for roles, taken in _by_files(estimate.ambiguous):
        # Grouped by the files that collide and not one line per address, because the repair is
        # one line of configuration for all of them — printed per address it would state the
        # same declaration four times, which is the shape that reads as four problems. The
        # addresses stay named: a count alone sends somebody to diff two outlines by hand.
        print(
            f"  refs     {len(taken)} address(es) declared by both {' and '.join(roles)} "
            f"({', '.join(taken)}), refused here: {_AMBIGUOUS_FIX[estimate.ref_scheme]}"
        )
    for declaration, count in estimate.ledger_shape:
        # Beside the `[ids]` line and in its shape (RK286): a count, and the keys that close
        # it. The reason on each refused line names the slots; this is what declaring them
        # recovers, which is the number an adopter is deciding on and which used to cost a
        # scratch `roadkeep.toml` to reach.
        print(
            f"  ledger   {count} line(s) parse as entries, refused here: "
            f"[ledger] {declaration}"
        )
    for shape in estimate.id_shape:
        # Beside the prefix line and in its shape (RK110): a count, and the key that closes
        # it. The trailing clause is the whole discipline — what the ids spell, never that
        # the project should therefore declare it.
        spells, when = _ID_SPELLS[shape.key]
        print(
            f"  ids      {shape.count} id(s) {spells}, refused here: "
            f"[ids] {shape.declaration} {when}"
        )
    for measure in estimate.measures:
        # Printed even at zero over: the number an adopting project is here for is the
        # *longest*, which is what a limit gets set from, and a measure that appears only
        # once it is exceeded is one nobody can declare a limit from (RK99).
        print(
            f"  {measure.field:<8} longest {measure.longest} of {measure.limit} "
            f"{measure.unit}, {measure.over} over"
        )
    if estimate.non_goals is not None:
        _print_scoped(estimate.non_goals)
    # The terms of the measurement rather than its result (RK291), the shape `[non_goals] not
    # governed` and `install`'s "no .github/workflows/" already use. Printed always, because a
    # limit stated only where it happened to bite is one the reader cannot rely on: RK290 made
    # the estimate and the gate agree on everything one file decides, so this names the rest.
    print(f"  scope    {_estimate_scope(estimate)}")
    if estimate.gains:
        # A category and not three more measurements (RK1089). Every row above answers what
        # this *file* would cost; these answer what the *project* is missing, and the first
        # of them (RK1087) printed among the numbers read as one more of them. The heading is
        # what keeps the next member from landing somewhere else again.
        print(
            f"  gains    {len(estimate.gains)} the format would add and this project "
            f"has not declared:"
        )
        for gain in estimate.gains:
            print(f"    {gain.name:<9}{gain.because}")
    if estimate.surface:
        # The other side of the transaction, and the only row here that is not about the file
        # (RK1100). An estimate that named four doors this format opens and no cost is one that
        # asks for a decision while holding half the terms — and this half is knowable in
        # advance, being a fact about the package: RK1097 measured three projects serving the
        # same 52 tools within 1.4% of each other.
        #
        # Stated at the cadence it is paid at and never summed with anything (RK1095): once at
        # connect, against a resident file paid every turn. And no verdict on it — whether the
        # doors above are worth this is the adopter's arithmetic, not the tool's (L4).
        print(
            f"  serves   {estimate.surface} characters once at connect, if this project "
            f"serves the tools: `[tools]` is where a ceiling on that is declared"
        )
    for marker, count in estimate.undeclared:
        print(f"  marker   {marker} on {count} line(s), declared by nothing in [markers]")
    for code, count in estimate.codes:
        print(f"  {code:<8} {count}")
    for reason, count in estimate.rejects:
        print(f"  unparsed {count}: {reason}")
    if estimate.non_canonical:
        # Qualified where the reading itself is in doubt (RK285). This states a refusal
        # absolutely, and on Shio it rested on a prefix and a scheme the report had just
        # named as probably wrong — the one claim in this output an adopter cannot discount,
        # and it was the one that was wrong. The number stays; what is added is which reading
        # produced it, so a reader can tell "your file is broken" from "read it another way".
        # The third reader of one list (RK1147). Behind the same predicate as the `also` lines
        # above (RK305) and not behind a second spelling of it: an alternative reading offered
        # here on a file the declared scheme read whole is the same wrong advice, and two
        # conditions for one sentence is where the two drift apart — which is what the payload
        # did, publishing the count these words qualify with no flag beside it.
        under = [f"{flag} {value}" for flag, value, _, _ in _readings(estimate)]
        because = f" — measured under this reading; {', '.join(under)} changes it" if under else ""
        print(
            f"  {estimate.non_canonical} line(s) do not round-trip: the tool would "
            f"refuse to write this file until they are rewritten by hand{because}"
        )


#: What closes a doubled address, per scheme (RK347). Under an outline it is a line of
#: configuration and never a renumbering of somebody's document: `[refs]` reads each file's
#: outline as its own, so the two `I`s stop being one address. Under `id` there is nothing to
#: namespace — the anchor is the task's own id, unique across the project by construction — so
#: two headings answering to one is a heading somebody has to delete.
_AMBIGUOUS_FIX = {
    "outline": '[refs] <role> = "<prefix>" puts each file\'s outline in its own namespace',
    "id": "an id addresses one section, so one of the two headings is the one to delete",
}


#: The findings that mean "the declared scheme could not read this address" (RK305). Under
#: `id` a pointer the author chose is `ref.mismatch`; under an outline one shaped like an id
#: is `ref.format`. Both are the signal RK285 said arrived with no sentence naming the flag.
_MISREAD_CODES = ("ref.mismatch", "ref.format")


def _by_files(ambiguous) -> list[tuple[tuple[str, ...], list[str]]]:
    """The doubled addresses gathered under the files that declare them, in first-seen order."""
    grouped: dict[tuple[str, ...], list[str]] = {}
    for anchor, roles in ambiguous:
        grouped.setdefault(roles, []).append(anchor)
    return list(grouped.items())


def _misread(estimate) -> bool:
    """Whether the declared scheme left any address in this file unread (RK305).

    RK288 asked a **majority**: print `--ref-scheme <other>` only where the other scheme
    accounts for more of the file than the declared one. That is a proxy for *this file is
    really addressed the other way*, and it holds on a file nothing writes to. It does not
    hold here. This repository's rationale file carries a permanent preamble anchored `§0.1`
    and one `§RK<n>` section per **open** design, and a ship deletes the second kind — so the
    ratio falls with every task delivered and, at the moment the open designs stop
    outnumbering the preamble, a fully conforming file is told to be read the other way.
    Measured while shipping Block B: five and five, one ship from the alarm.

    What the count cannot see is that the two kinds of heading are not competing readings of
    one file — one is prose the project keeps and the other is a queue. So the question asked
    here is the one RK288 was written about: did the declared scheme leave something *unread*?
    A file whose scheme parses every address it was asked about has no minority reading to
    report, whatever the ratio; Shio's `0.1` headings and its hand-chosen pointers are unread
    under `id`, and still say so.

    Two shapes because the evidence is: a rationale file's unread headings are the ones
    :attr:`~roadkeep.adopting.Estimate.listed` already counts, and a backlog's are the
    pointers the gate refuses.
    """
    if estimate.unit == "section":
        return estimate.listed > 0
    return any(code in _MISREAD_CODES for code, _ in estimate.codes)


def _estimate_scope(estimate) -> str:
    """What this estimate could not decide, said in names the reader can act on (RK291/292).

    Three sentences, because the fact has three shapes and one wording made two of them wrong.
    Where the target is declared, the siblings are what handing over would complete, so they are
    named. Where it is declared and alone, there is nothing to hand over and the limit is still
    real. Where it is **not** declared — the case `adopt` exists for — this project's `[files]`
    belong to somebody else: naming them said Turing's `docs/IMPROVEMENTS.md` was measured while
    this repository's went unread, which reads as not having read what was read.
    """
    across = "deps and pointers resolve across files"
    if not estimate.declared:
        return (
            f"one file read, declared by no project here: {across}, so neither was checked — "
            f"`lint` is the answer inside the project that owns them"
        )
    named = ", ".join(estimate.unopened) if estimate.unopened else "no other governed file"
    return (
        f"{named} not read: {across}, so neither was checked here — `lint` is the answer "
        f"once they are declared"
    )


def _print_scoped(scoped) -> None:
    """The roadmap's other bullet, under the two limits it would be held to (RK139).

    Printed even at zero, and even where `[non_goals]` is undeclared, for the reason every
    measure is: what an adopter is asking is what the rule would cost, and a section that
    appeared only once it was already expensive is one nobody can decide from. Whether the
    project opted in is said in the same line, because it is what decides whether these
    bullets are in the headline count or beside it.
    """
    governed = "governed" if scoped.governed else "not governed, so measured at the defaults"
    print(
        f"  non-goals {scoped.parsed} bullet(s), {scoped.unparsed} unread, "
        f"{scoped.over} over — [non_goals] {governed}"
    )
    for measure in scoped.measures:
        print(
            f"    {measure.field:<8} longest {measure.longest} of {measure.limit} "
            f"{measure.unit}, {measure.over} over"
        )


def _estimate_json(estimate: Estimate) -> dict[str, object]:
    return {
        "file": estimate.path.as_posix(),
        "prefix": estimate.prefix,
        "families": list(estimate.families),
        "inferred": estimate.inferred,
        # The third state, published rather than left to be read off a false `false` (RK485):
        # a consumer that saw `inferred: false` on a defaulted prefix read it as *declared*,
        # which is the same two-words-for-three the printed line had.
        "defaulted": estimate.defaulted,
        # Empty where the project has them all, and empty where no project declared the
        # target at all (RK1089) — a consumer telling those apart reads `declared`.
        "gains": [
            {"name": gain.name, "because": gain.because} for gain in estimate.gains
        ],
        # Beside the gains and not among the counts, because it is the one figure here that is
        # not about the file (RK1100). Its own object, so the cadence travels with the number:
        # a client adding this to a per-turn cost is the arithmetic RK1095 refused to print.
        "serves": {"characters": estimate.surface, "cadence": "once, at connect"},
        "unit": estimate.unit,
        # Which role decided the numbers (RK1147): `unit` says lines for a backlog and for a
        # ledger alike, and a ledger is measured under `[limits.changelog]` (RK76) — so a
        # consumer rerunning this estimate needs the flag rather than a guess, and every door
        # below carries it for the same reason.
        "ledger": estimate.ledger,
        "ref_scheme": estimate.ref_scheme,
        "parsed": estimate.parsed,
        "conforming": estimate.conforming,
        "changing": estimate.changing,
        "blocks": list(estimate.blocks),
        # The door beside the count, on exactly the rows the printed report names a flag for
        # (RK1147) — absent on the rest, because a family the chosen ones already cover is not
        # an unread reading and a door there would be a command with nothing to change.
        "prefixes": [
            {"prefix": p, "count": n, **_reading_door(estimate, "--prefix", p)}
            for p, n in estimate.prefixes
        ],
        "measures": [
            {
                "field": m.field,
                "limit": m.limit,
                "longest": m.longest,
                "over": m.over,
                # RK437: which counter the two figures beside it are in. `[limits]` is one
                # table in three units, and a payload that named none left a caller to assume
                # the wrong one on exactly the row where assuming is wrong.
                "unit": m.unit,
            }
            for m in estimate.measures
        ],
        "undeclared": [{"marker": m, "count": n} for m, n in estimate.undeclared],
        "id_shape": [
            {"key": s.key, "value": s.value, "count": s.count, "declaration": s.declaration}
            for s in estimate.id_shape
        ],
        "codes": [{"code": c, "count": n} for c, n in estimate.codes],
        "non_goals": None
        if estimate.non_goals is None
        else {
            "parsed": estimate.non_goals.parsed,
            "unparsed": estimate.non_goals.unparsed,
            "over": estimate.non_goals.over,
            "governed": estimate.non_goals.governed,
            "changing": estimate.non_goals.changing,
            "measures": [
                {
                    "field": m.field,
                    "limit": m.limit,
                    "longest": m.longest,
                    "over": m.over,
                    "unit": m.unit,
                }
                for m in estimate.non_goals.measures
            ],
        },
        "rejects": [{"reason": r, "count": n} for r, n in estimate.rejects],
        "non_canonical": estimate.non_canonical,
        "schemes": [
            {"scheme": s, "count": n, **_reading_door(estimate, "--ref-scheme", s)}
            for s, n in estimate.schemes
        ],
        # Each file under the key that says what its name **is** (RK371): a role `[files]`
        # answers, or a path it does not. The printed line can leave this to the sentence
        # around it; a payload read so that an answer costs no file read (L5) cannot, and a
        # `roles` list holding filenames sent an agent to look up something that was never
        # there. Never resolved into roles to make one key true — a file this project does not
        # govern has none, and inventing one is what RK292 keeps out of the report.
        "ambiguous": [
            {
                "anchor": anchor,
                "declared_by": [
                    {"path": name} if name in estimate.by_path else {"role": name}
                    for name in names
                ],
            }
            for anchor, names in estimate.ambiguous
        ],
        # Beside them and not merely inside them: how the run named each file is the same
        # answer when nothing collided at all, and it is not a claim about who owns one.
        "by_path": list(estimate.by_path),
        "ledger_shape": [{"declaration": d, "count": n} for d, n in estimate.ledger_shape],
        "unopened": list(estimate.unopened),
        "declared": estimate.declared,
        "tabular": estimate.tabular,
        "listed": estimate.listed,
        # RK376: the pair that tells an empty roadmap apart from a file nothing was read in.
        "lines": estimate.lines,
        "recognised": estimate.recognised,
    }


def registration_report(registration: Registration, where: str, label: int) -> list[str]:
    """Everything one registration has to say, rendered once for both its surfaces (RK276).

    `merge --register` and `install --register-merge` are the same write — RK148 said so, and
    the install branch carried a comment claiming the two printed the same lines. RK274 then
    added a third line and it reached one of them, so the comment asserting the invariant
    became the record of it breaking. Two renderings of one dataclass drift the moment the
    dataclass grows a field, and the only fix that holds is that there is one rendering.

    `label` is the column the install report pads its own verbs to and the merge report does
    not — the difference that pushed the two apart, reduced to the one parameter it is.

    What it says about the config half is `Wiring`'s (RK278): the `then` line is advice, and
    advice to wire a driver no governed file routes to is what `--check` had already stopped
    giving. The state line is printed either way, because narrowing a demand is not licence to
    stop reporting.
    """
    prefix = f"  {'registered':<{label}} " if label else ""
    lines = [f"{prefix}{where}  + {line}" for line in registration.added]
    lines += [f"{prefix}{where}    {line} (already there)" for line in registration.present]
    # RK274: named where the writes are named, because "what this command did" has to include
    # the file it deliberately did not touch — a skip nobody is told about is indistinguishable
    # from a skip nobody intended.
    lines += [
        f"{prefix}{where}    {path} → {value} (another driver, left alone)"
        for path, value in registration.left_alone
    ]
    pad = label or 8
    if registration.wiring is None or registration.wiring.demands_driver:
        # Printed and not run: a driver command names a path into this checkout, and setting
        # somebody's git config is a write outside the files this tool was given (L2).
        lines.append(f"  {'then':<{pad}} {registration.command}")
        # What the stored value cannot promise, said where it is stored (RK255): git executes
        # it long after this process, and a driver that stopped resolving is silent till a merge.
        lines.append(f"  {'re-run':<{pad}} after {registration.invalidated_by}")
    if registration.wiring is not None:
        # Read after the attribute lines were written (RK266). This is the line that carries a
        # re-run: three attributes "already there" is the answer where the config is the half
        # that moved, and without this the output that says nothing changed would be all of it.
        lines.append(f"  {'config':<{pad}} {_wiring_line(registration.wiring)}")
    return lines


def _wiring_line(wired: Wiring) -> str:
    """The config half's state, with the qualifier only both halves together can add (RK278).

    One function, so the check and the verb cannot say it two ways — which is what happened the
    commit RK277 shipped, where `--check` knew nothing routed here and `--register` did not.
    """
    tail = "" if wired.attributes.routes_here else " — and no governed file routes here"
    return f"{_driver_line(wired.driver)}{tail}"


#: What each state of the stored driver says, and what a `--check` exits with (RK266). Only two
#: are failures: git has no driver it can run. `MOVED` is a driver that works and is not what
#: this machine would write, and exiting 1 on it would make the check unusable on any repository
#: two people registered from — which is every repository the driver is for.
_DRIVER_STATES = {
    ABSENT: (EXIT_GATE, "not set, so a conflict falls back to git's own markers"),
    # Not "the command above": `--check` prints no command, and a state line that only reads
    # right under the other surface is one of the two that must stand on its own.
    CURRENT: (EXIT_OK, "set to the command this machine would write"),
    MOVED: (EXIT_OK, "set to a command that runs, and is not this machine's"),
    UNRUNNABLE: (EXIT_GATE, "set to a command this machine no longer has"),
    UNKNOWN: (EXIT_OK, "could not be read: no git, or no repository here"),
}


def _driver_line(driver: Driver) -> str:
    """One line for the state, quoting the stored value only where it is the evidence."""
    _, said = _DRIVER_STATES[driver.state]
    line = f"{DRIVER_KEY} {said}"
    if driver.state in (MOVED, UNRUNNABLE):
        return f"{line}: {driver.stored}"
    return line


def _attributes_line(attributes: Attributes) -> str:
    """What git sends to the driver, counted — and named where some of it is not.

    "git sends" and no longer "`.gitattributes` sends" (RK273): the answer is `check-attr`'s,
    so it holds for a rule set in a subdirectory or in `.git/info/attributes`, and naming one
    file as the authority would be naming the one this tool happens to write.
    """
    if attributes.state == UNKNOWN:
        return "could not be read: no git, or no repository here"
    counted = f"{len(attributes.sent)} of {len(attributes.resolved)} governed files"
    line = f"git sends {counted} to the {DRIVER} driver"
    if attributes.state != CURRENT:
        line = f"git sends {counted}: {', '.join(attributes.unsent)} would merge textually"
    if attributes.claimed:
        # Said in every state, including the passing one (RK274): a claimed file is settled, so
        # it does not hold the answer open — but dropping it from the line would leave a count
        # short of its total with nothing explaining the gap, which reads as the failure it
        # is not. Said, never corrected: it is somebody's decision and this tool can see it.
        named = ", ".join(f"{path} → {value}" for path, value in attributes.claimed)
        return f"{line} ({named}, left alone)"
    return line


def _prose_file(config: Config, prose: Document | None) -> str:
    """The prose file a drop actually rewrote, as the project spells it (RK196).

    Read off the document rather than off `config.path("improvements")`, because which role
    declared the anchor is what the drop resolved and a caller restating it would be
    guessing — the guess that reported "no §X.1 section in IMPROVEMENTS.md" about a section
    sitting in `STRATEGY.md`. Nothing dropped means no document, and then the answer is the
    first declared prose role, which is where a design would have been.
    """
    if prose is not None and prose.path is not None:
        return config.relative(prose.path)
    declared = tuple(role for role in PROSE_ROLES if config.has(role))
    return config.relative(config.path(declared[0])) if declared else ""


def _dated_json(commit: Commit) -> dict[str, str]:
    """A commit as an **address**: where to look, and when it landed (RK1163).

    Four fields and not five. The message body belongs to an answer *about* that commit, and this
    rides inside a `brief` — a bounded answer whose whole argument is that it costs less than
    reading the file (RK29), where one long commit message would be a paragraph nobody asked for.

    A name of its own since RK1170 found the duplicate: this was written as a second
    `_commit_json`, which shadowed the nullable one above and made `origin '§<anchor>' --json`
    raise on the half of its answer that is `None` by construction.
    """
    return {
        "sha": commit.sha,
        "short": commit.short,
        "date": commit.date,
        "subject": commit.subject,
    }
