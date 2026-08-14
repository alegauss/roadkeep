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
import sys
from collections.abc import Iterable, Sequence

from roadkeep import claiming
from roadkeep.adopting import Estimate
from roadkeep.authoring import StatusChange
from roadkeep.backlog import Backlog, Stage, Standing
from roadkeep.briefing import Brief, NothingToBrief
from roadkeep.budgeting import Load
from roadkeep.claiming import Followed, Held
from roadkeep.config import Config, PROSE_ROLES
from roadkeep.deferring import Carried
from roadkeep.kernel.document import Document, Entry, Reject
from roadkeep.fixing import Fix
from roadkeep.graph import Leverage
from roadkeep.history import Commit, Origin
from roadkeep.ids import Promise
from roadkeep.linting import Finding, Report
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
from roadkeep.remaining import count, declared
from roadkeep.remedying import Door, remedy
from roadkeep.repairing import MAX_PASSES, Repaired, repair
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


def _print_followed(change: StatusChange, config: Config) -> None:
    """What the marker did to the claim on its line (RK158), and never silently.

    A marker change is not obviously an assertion of ownership to whoever typed it, so the
    door says which of the two it just made — the same reason `pick` names the claim it took
    rather than only moving it.
    """
    if change.claim is Followed.CLAIMED:
        print(f"  claimed  held for {config.held}m unless a marker moves it sooner")
    elif change.claim is Followed.RELEASED:
        # `dropped` and not `released`: every label in this output is padded to one width, and
        # the eight-letter word is the one that would not fit it.
        print("  dropped  the claim on this line is released")


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
    }


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


def _print_event(
    event: dict[str, object], indent: str = "", *, config: Config, standing: bool = False
) -> None:
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
    print(f"{indent}event    {event['id']}  Block {event['block']}  {stage}")
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
        print(f"{indent}         {left['sentence']}")
    because = None if config.permanent_headings else _DROPPABLE.get(Stage(stage))
    if because:
        print(
            f"{indent}         {because} — "
            f"`{invocation()} block drop {event['block']}` withdraws the heading, "
            f"where this project drops one"
        )


def _print_dequeued(token: str | None) -> None:
    """What a departure took out of the priority queue (RK327).

    Said and never silent, because a departure that quietly shortened the plan would be an
    ordering changed with no sentence about it — and the printed line is what a reviewer
    reads the diff against (RK298).
    """
    if token is not None:
        print(f"  dequeued {token} left the priority queue with the line")


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


def _print_emptied(parent: str | None) -> None:
    """The parent this drop left introducing children that have all shipped (RK400).

    Beside the citation line and for the same reason: this is the only moment it can be
    said. `ship` deletes the task's own section and names what cited it; under an outline it
    leaves the **parent** standing, and that paragraph was written as an introduction to the
    children — it states the problem they solve, in the present tense, and it is the first
    thing anyone reads about that family.

    Noticing is the tool's; what the introduction should say instead is a `section amend` and
    a judgement (L4). So the sentence names the anchor and the door, and writes nothing.
    """
    if parent is None:
        return
    print(
        f"  emptied  §{parent} now has no subsections — its prose introduces work that has "
        f"shipped; `section amend {parent} --body -` is the edit, in this commit"
    )


def _print_cited(cited: Sequence[str]) -> None:
    """Who is left pointing at prose this command deleted (RK206).

    Said here and gated nowhere, because this is the only moment it can be said: `ship`
    creates the dangling citation, `as_ledger` keeps no pointer, and from the next command
    on a reference to a section that shipped reads exactly like a typo. The ship is right —
    what the author owes is one edit in the same commit, and this is the sentence that asks
    for it.
    """
    if not cited:
        return
    print(
        f"  cited    {', '.join(f'§{a}' for a in cited)} "
        f"{'cites' if len(cited) == 1 else 'cite'} it in prose — now resolving to nothing"
    )


def _print_scope(scope: claiming.Scope | None, wrote: Sequence[str] = ()) -> None:
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
    """
    if scope is None:
        # The staging line is still owed (RK1130). What needs a claim is the *subtraction* —
        # which paths are somebody else's — and a project that declared none was getting no
        # `git add --` line at all from the two verbs that had one, on the write with the most
        # files in it. So the silence stays where it belongs: on the three lists below.
        _print_staging(dict.fromkeys(wrote))
        return
    _print_staging(dict.fromkeys((*scope.mine, *wrote)))
    for one, who in scope.theirs:
        print(f"  theirs   {one}  ({who} is holding it)")
    for one, others in scope.shared:
        # Beside the staging and not instead of it (RK1120): the file is staged either way —
        # this transaction wrote it — and what the author needs is the ids inside it that this
        # commit is not about, which is the hunk to leave out rather than a path to drop.
        named = ", ".join(others)
        print(f"  shared   {one}  ({named} moved in it too, and staging it takes that)")
    for one in scope.loose:
        # No filter here since RK1117: `loose` already excludes what this id explains, and the
        # subtraction moved to `split` because the two callers meant different things by the
        # list this used to read — a departure's `wrote` is what the transaction wrote, and a
        # governed file it wrote *and* somebody else had changed vanished from both reports.
        print(f"  loose    {one}  (no claim names it)")
    # The declared paths that would stage nothing (RK295). Named here rather than folded into
    # `mine`, which this printer deliberately does not repeat: at a departure the work is done,
    # so a scope naming a file the tree does not have is a typo and not a file yet to be written.
    for one in scope.idle:
        print(f"  typo?    {one}  (declared, and stages nothing)")


def _wrote_json(config: Config, paths: Iterable[Path]) -> dict[str, object]:
    """The `wrote` key, spelled once for every write that answers one (RK1129, RK1130).

    A fragment merged into each payload rather than a field on each record, because what a
    client does with it is the same `git add` whichever verb answered — and a key spelled per
    verb is a key that comes to differ per verb. Relative, like every path in every payload
    here: an absolute one is a fact about the machine that ran the command.
    """
    return {"wrote": [config.relative(one) for one in paths]}


def _print_staging(paths: Iterable[str]) -> None:
    """The `git add --` line, spelled in one place (RK298, RK1129).

    Two writes print it now — a departure, which releases the scope nothing can read back
    afterwards, and `add`, which refreshes a projection the commit was leaving behind — so the
    quoting and the label are here rather than at each of them. Nothing is printed for an empty
    list: a command that wrote no file has no staging to advise, and a bare `git add --` is a
    line somebody would paste.
    """
    staging = tuple(paths)
    if staging:
        print(f"  stage    git add -- {' '.join(_shell(one) for one in staging)}")


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
        "staging_nothing": list(scope.idle),
        # RK1120: per governed file, the other ids whose line moved in it. Its own key beside
        # `unclaimed`, because the two are different answers — a path nobody claims, and a path
        # this commit does claim that is carrying somebody else's line.
        "shared": [{"path": one, "ids": list(ids)} for one, ids in scope.shared],
    }


def _print_standing(standing: Standing | None) -> None:
    """Say which of the two silences this is, where a listing came back empty (RK429).

    On stderr, for the reason the uncounted note is: stdout stays exactly what the file
    says, so `list` substitutes for the grep it replaces, and a sentence in the pipe is a
    line no `--ids` consumer asked for. Nothing is said about a **live** block — that a
    marker filter matched none of its open lines is a fact about the filter.
    """
    if standing is not None and standing.settled:
        print(f"roadkeep: {standing.sentence}", file=sys.stderr)


def _print_repair(outcome: Repaired, root: str) -> None:
    _print_fix(outcome.applied)
    _print_refusals(outcome.applied)
    for step in outcome.steps:
        print(str(step))
    for left in outcome.left:
        print(str(left))
    if outcome.exhausted:
        print(
            f"roadkeep: stopped after {MAX_PASSES} repairs with work still reported: a "
            f"rule and its own remedy disagree, which is a defect in this tool",
            file=sys.stderr,
        )
    verb = "would run" if outcome.dry_run else "ran"
    # Runs and attempts are two numbers (RK471). This counted the steps, so a run that
    # dispatched three and had two refused closed with `3 repair(s) ran` three lines under
    # two the same output had already marked `FAILED` — and the count is the line a person
    # acts on, so a caller read `3 ran` against `34 left` and concluded the tree moved three
    # findings closer when it moved one. `Step.ok` already separates them at the point they
    # are decided; only the sum did not ask.
    #
    # The exit code is untouched and stays 1 while anything is left (RK422): two refusals are
    # not a failure of `repair`, whose whole design is that what it cannot close it prints.
    failed = [step for step in outcome.steps if not step.ok]
    ran = len(outcome.steps) - len(failed)
    refused = f", {len(failed)} refused" if failed else ""
    print(
        f"{ran} repair(s) {verb}{refused}, {len(outcome.left)} left for you{_tree(root)}"
    )


def _repair_json(outcome: Repaired, root: str, served: str = "") -> dict[str, object]:
    return {
        "root": root,
        "clean": outcome.clean,
        "dry_run": outcome.dry_run,
        "passes": outcome.passes,
        "exhausted": outcome.exhausted,
        "steps": [
            {
                "code": step.code,
                "where": step.where,
                "argv": list(step.argv),
                "what": step.what,
                "exit": step.exit,
            }
            for step in outcome.steps
        ],
        "left": [
            {
                "code": left.finding.code,
                "where": left.finding.where,
                "message": left.finding.message,
                **({} if left.remedy is None else {"remedy": left.remedy.payload(served)}),
            }
            for left in outcome.left
        ],
    }


def _print_report(
    config: Config, report: Report, applied: Fix, root: str, quiet: bool
) -> None:
    if not quiet:
        _print_fix(applied)
        # Notes before the findings and the summary: a note is what the gate says about a
        # file it is passing, and after an exit-1 report nobody would read it (RK35).
        for note in report.notes:
            print(str(note))
    _print_refusals(applied)
    if report.clean:
        # The files are named on the way out even when there is nothing to say: a gate
        # that passed by reading nothing looks exactly like a gate that passed.
        print(
            f"{', '.join(report.checked) or 'nothing'}: {_scope(report)}, clean"
            f"{_standing(report)}{_tree(root)}"
        )
        return
    mechanical = 0
    if not quiet:
        mechanical = _print_findings(config, report)
    added = "new " if report.baseline is not None else ""
    print(
        f"{report.problems} {added}problem(s) in {_scope(report)} across "
        f"{len(report.checked)} file(s): {_codes(report)}{_standing(report)}{_tree(root)}"
    )
    if mechanical:
        # Said once and never per line (RK420): the mechanical class is the one remedy that
        # is identical on every finding it answers, so repeating it under each of them would
        # spend the report's length on the findings that cost the reader nothing.
        print(f"{mechanical} of them need no decision: {invocation()} lint --fix")


def _print_findings(config: Config, report: Report) -> int:
    """Every finding, with a group that is one fact said once (RK469).

    A finding is per line and stays per line — the addresses are the evidence. What is said
    once is the *sentence and the remedy* where a whole run of them shares both: measured on
    Turing, 27 `section.ambiguous` findings and their 26 remedies were 80% of a 15,894-char
    report, two distinct messages once the anchor was taken off, and one `[refs]` line in
    `roadkeep.toml` closes every one.

    The same argument RK420 already makes one line down, where the mechanical remedy is
    counted rather than repeated under each finding, and the same one RK451 made about a file
    a crash left NUL: one finding because the loss is one. A report whose bulk is one sentence
    repeated is one a reader learns to skip (RK146), and it buries the four findings here that
    are each about a different line.

    Grouped by what the **emitter** declared they share, and only for runs of two or more: a
    single member is its own sentence, and a group of one printed as a group would be a
    heading over nothing.
    """
    mechanical = 0
    # By the key and not by adjacency: a report interleaves files, so the members of one
    # group are rarely consecutive — and a grouping that only folded runs would fold Turing's
    # and leave a fixture's alone, which is the shape that passes a test and misses the case.
    # Printed at the first member's place, so the report's order is otherwise the one it had.
    groups: dict[tuple[str, str, str], list[Finding]] = {}
    for finding in report.findings:
        if finding.shared:
            groups.setdefault((finding.code, finding.file, finding.shared), []).append(finding)
    printed: set[tuple[str, str, str]] = set()
    for finding in report.findings:
        key = (finding.code, finding.file, finding.shared)
        run = groups.get(key, []) if finding.shared else []
        if len(run) < 2:
            print(str(finding))
            mechanical += _print_remedy(finding, config)
            continue
        if key in printed:
            continue
        printed.add(key)
        first = finding
        # The pair once, the addresses under it: `file:line` each, which is what an editor
        # opens and what an author choosing which file takes the namespace counts.
        print(f"{first.file}  {first.code}  {len(run)} addresses {first.shared}")
        print(f"    {'  '.join(f'{one.token}:{one.lineno}' for one in run)}")
        mechanical += _print_remedy(first, config)
    return mechanical


def _print_remedy(finding: Finding, config: Config) -> int:
    """Print what closes this finding, and return 1 where that was `--fix`'s (RK420).

    Printed by default rather than behind a flag. The defect being answered is a caller
    spending a *turn* to learn the command, so a report that carries it only on request has
    the cost exactly where it was: the second call is the thing being removed.

    The mechanical class is counted instead of printed, and every other kind gets its line —
    including `decide`, whose whole content is the two doors and what separates them, since
    a decision printed as one word is a decision made by running one and reading its refusal.
    """
    found = remedy(finding, config)
    if found is None or found.kind == "fix":
        return 1 if found is not None else 0
    for line in str(found).splitlines():
        print(f"    {line}" if not line.startswith("    ") else line)
    return 0


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


def _print_fix(applied: Fix) -> None:
    for repair in applied.repairs:
        print(str(repair))
    for kept in applied.skipped:
        print(str(kept))
    if applied.repairs:
        print(f"{applied.changed} line(s) normalized in {', '.join(applied.files)}")
        # Once per run and not on every line (RK357): a `gone` address is a position in the
        # file as this pass *read* it, which is the reading git still has and the written file
        # no longer does. Reporting it before the write is deliberate — the reader who wants to
        # see what was taken needs the line, not the gap — so what was missing was the sentence
        # saying which of the two trees the address is about.
        left = sum(1 for repair in applied.repairs if repair.removed)
        if left:
            print(f"{left} of them removed, at the line each was read from")


def _print_refusals(applied: Fix) -> None:
    """Printed even under `--quiet`: a pass that could not prove its own output wrote
    nothing, and silence about that is the difference between "clean" and "unexamined"."""
    for message in applied.refused:
        print(f"roadkeep: refused, nothing written: {message}", file=sys.stderr)


def _lint_json(config: Config, report: Report, applied: Fix, root: str) -> dict[str, object]:
    baseline = report.baseline
    return {
        # First, because every path below is relative to it and a payload a second tool files
        # against the wrong project is worse than one it cannot file at all (RK299). The same
        # key `install --json` already uses, spelled the same way.
        "root": root,
        "clean": report.clean and not applied.refused,
        # Absent without `--baseline`, so a caller reading `problems` cannot mistake a
        # difference for a total: with it, `findings` holds only what this tree added.
        **(
            {}
            if baseline is None
            else {
                "baseline": {
                    "rev": baseline.rev,
                    "standing": baseline.standing,
                    "forgiven": [_finding_json(f, config) for f in baseline.forgiven],
                    "resolved": [_finding_json(f, config) for f in baseline.resolved],
                }
            }
        ),
        "fixed": [
            {
                "file": repair.file,
                "line": repair.lineno,
                "id": repair.id,
                "reasons": list(repair.reasons),
                "before": repair.before,
                "after": repair.after,
                # A key on the same list rather than a `removed` list beside `fixed` (RK357):
                # `line` means the pre-pass position here, and a consumer resolving addresses
                # has to know that from the payload rather than from an empty `after`.
                "removed": repair.removed,
            }
            for repair in applied.repairs
        ],
        "kept": [
            {"file": s.file, "line": s.lineno, "id": s.id, "reason": s.reason}
            for s in applied.skipped
        ],
        "refused": list(applied.refused),
        "checked": list(report.checked),
        "lines": report.lines,
        "sections": report.sections,
        "budgets": report.budgets,
        "problems": report.problems,
        "codes": report.codes(),
        "findings": [_finding_json(f, config) for f in report.findings],
        "notes": [
            {
                "code": note.code,
                "file": note.file,
                "line": note.lineno,
                "id": note.id or None,
                "message": note.message,
                **_remedy_json(note, config),
            }
            for note in report.notes
        ],
    }


def _standing(report: Report) -> str:
    """What the baseline forgave, and what left — said out loud, both of them (RK84).

    Both, because either number alone is the misreading §RK84 was written about: the run
    that deleted 160 lines of rationale took the count *down* by eight, and the drop read as
    an improvement right up until the two findings it added were looked at individually.
    """
    baseline = report.baseline
    if baseline is None:
        return ""
    counts = f"{baseline.standing} standing"
    if baseline.resolved:
        counts += f", {len(baseline.resolved)} resolved"
    return f" against {baseline.rev} ({counts})"


def _scope(report: Report) -> str:
    """What was read, in its own units: task lines, sections, and budgeted files."""
    scope = f"{report.lines} line(s), {report.sections} section(s)"
    return scope if not report.budgets else f"{scope}, {report.budgets} budget(s)"


def _codes(report: Report) -> str:
    return "  ".join(f"{code} {count}" for code, count in report.codes().items())


def _finding_json(finding: Finding, config: Config) -> dict[str, object]:
    return {
        "code": finding.code,
        "file": finding.file,
        "line": finding.lineno,
        # Only a character finding has one (RK34), and it is what makes an invisible
        # codepoint findable: `file:line:column` is what an editor jumps to.
        "column": finding.column,
        "id": finding.id or None,
        "message": finding.message,
        **_remedy_json(finding, config),
    }


def _served(config: Config) -> str:
    """The prefix this session's tools arrive under, or `""` where it has none (RK449).

    One reader for the four payloads that publish a remedy, because it is one question about
    one project and four calls to `serving` would be four places to forget it — and since
    RK488 it is `provenance.served_by`'s answer rather than a fourth spelling of it, the guard
    and the attestation having each written the same `or ""` for themselves.
    """
    return served_by(config.root)


def _remedy_json(finding: object, config: Config) -> dict[str, object]:
    """The remedy, as a key that is absent rather than null when the table has none (RK420).

    Absent and not `"remedy": null`, because a consumer that reads the key at all is one
    about to run what is in it, and a null is a shape it has to branch on before it can
    tell "no command exists" from "this build predates the field".
    """
    found = remedy(finding, config)
    return {} if found is None else {"remedy": found.payload(_served(config))}


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
    }


def _brief_json(gathered: Brief, config: Config) -> dict[str, object]:
    return {
        **gathered.view.payload(),
        "readiness": str(gathered.readiness),
        "picked": gathered.picked or None,
        "deps_resolved": [
            {
                "dep": r.dep.id,
                "kind": str(r.kind),
                "status": str(r.status),
                "detail": r.detail,
                # Where this dep shipped after the design was last written (RK1163), the two
                # commits that say so — beside the resolution rather than in a list of their
                # own, because it is a fact *about* this dep and a consumer reading the row
                # would otherwise join two arrays to find it.
                **{
                    "settled_since": {
                        "shipped": _dated_json(one.shipped),
                        "revised": _dated_json(one.revised),
                    }
                    for one in gathered.settled
                    if one.dep == r.dep.id
                },
            }
            for r in gathered.deps
        ],
        "chains": [
            {
                "path": [gathered.task.id, *(hop.target for hop in c.hops)],
                "end": str(c.end),
                "detail": c.detail,
            }
            for c in gathered.chains
        ],
        "unblocks": {
            "count": gathered.leverage.count,
            "of": gathered.leverage.of,
            "transitive": list(gathered.leverage.transitive),
        },
        "non_goals": list(gathered.non_goals.leads),
        "non_goals_elided": gathered.non_goals.elided,
        # The whole table here and one line on stdout (RK190): a tool result is read by
        # something that can hold it, and this is the number the next write is measured on.
        "budget": None if gathered.budget is None else gathered.budget.payload(),
        # The same shape for the write about to be made (RK1174), and always published where it
        # exists — unlike the printed line, which is silent when the two agree: a key costs a
        # client nothing to skip and a consumer comparing them wants both numbers present.
        "shipping": None if gathered.shipping is None else gathered.shipping.payload(),
        # Same key and same shape as `pick`'s (RK154): one fact spelled two ways is two facts.
        "held": [{"id": h.id, "age": round(h.age), "since": h.since} for h in gathered.held],
        "claimed": None
        if gathered.claim is None or gathered.claim.change is None
        else {
            "taken": True,
            "from": gathered.claim.change.before,
            "to": gathered.claim.change.after,
        },
        "event": _claim_event(gathered.claim, config),
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
        "parts": [
            {"heading": part.heading, "lines": part.lines, "bytes": part.bytes}
            for part in load.parts
        ],
        # What this checkout pays over the counted number (RK1105), so a caller comparing two
        # machines has the difference as a field instead of inferring it from a mismatch.
        "translated": load.translated,
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
    """The reverse direction, which is the half of prioritisation a tool may supply."""
    shown = ", ".join(leverage.transitive[:4])
    tail = " …" if leverage.count > 4 else ""
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
