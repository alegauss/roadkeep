"""Every verb that answers a question, which is why it is the largest of them (RK494).

`list`, `stats`, `audit`, `show`, `brief`, `pick`, `budget`, `deps`, `anchors`, `gaps`,
`origin`, `weight`, `remaining`, `claims`, `claim`, `writes` and `export` — L5's whole
surface, where a question costs a command instead of a file in the context.

The three that can write are here anyway and say so: `brief --claim`, `pick --claim` and
`claims --prune` move a marker or a registry, which is what :func:`roadkeep.cli.dispatch`
reads to take the lock (RK167). Their subject is still the question, and filing a verb by
what one flag makes it would put one verb in two places.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from collections.abc import Mapping, Sequence

from roadkeep import attesting, claiming
from pathlib import Path

from roadkeep.backlog import Backlog, Stage, Standing
from roadkeep.capturing import captures, delivered
from roadkeep.briefing import NothingToBrief, brief
from roadkeep.budgeting import (
    Load,
    body_budget,
    budget,
    file_budget,
    non_goal_budget,
)
from roadkeep.config import Config, PROSE_ROLES
from roadkeep.counting import Census
from roadkeep.kernel.document import StaleFile, write_all
from roadkeep.exporting import project, splice_into
from roadkeep.graph import Dependencies
from roadkeep.history import (
    Anchor,
    HistoryUnavailable,
    anchors,
    cited_origin,
    doubled,
    families_of_block,
    Gapped,
    gaps,
    indexed,
    namespaces,
    next_child,
    next_family,
    origin_of,
    status,
)
from roadkeep.merging import markers
from roadkeep.picking import Claim, Picked, pick, take
from roadkeep.provenance import invocation
from roadkeep.remaining import QueryError, count, declared
from roadkeep.rendering import (
    _print,
    CHARACTER_UNIT,
    _claim_event,
    _commits_json,
    _load_json,
    _nothing_json,
    _scope_rows,
    _print_standing,
)
from roadkeep.kernel.schema import body_aim
from roadkeep.kernel.schema import width as measured_width
from roadkeep.sections import binding
from roadkeep.serving import surface
from roadkeep.showing import show
from roadkeep.verbs.refusing import EXIT_OK, EXIT_USAGE, REFUSALS, _refused
from roadkeep.weighing import Weighed, weigh


def _census(config: Config, args: argparse.Namespace) -> tuple[Census, Standing | None]:
    """The census a `--block` narrows, and what became of the label it named (RK429).

    A count reads one file, and keeping it that way is why `stats` cannot go stale against
    a changelog it never read. So the second file is opened only where a label was named,
    and what it answers is never counted — only said, on stderr, beside a listing that is
    still exactly what the file holds.

    Exactly one state changes what this returns, and it is the narrow one: a label this
    file declares no heading for **and** that has nothing left anywhere — the block whose
    last line shipped and whose roadmap heading `block drop` then took. A **live** block
    missing from the file being counted keeps its refusal, because there the file really
    does not declare a label that work is filed under, and `unknown` keeps its own for the
    reason it exists: it is the only one that is a typo.
    """
    marker = getattr(args, "marker", None)
    census = Census.read(config, args.role)
    if args.block is None:
        return census.select(marker=marker), None
    if not config.has("roadmap") or not config.path("roadmap").is_file():
        # Nothing to join against: the reader below needs the roadmap, and a project
        # counting a ledger before `init` wrote one still gets the count it asked for.
        return census.select(block=args.block, marker=marker), None
    standing = Backlog.load(config).standing(args.block)
    if standing.settled and args.block not in census.blocks:
        # Narrowed by the marker first and *then* emptied, so an undeclared marker is
        # refused here exactly as it is on every other path: a filter nobody validated is
        # a filter that silently matches nothing, which is the answer a clean file gives.
        return census.select(marker=marker).elsewhere(args.block), standing
    if standing.stage is Stage.UNKNOWN and args.block in census.blocks:
        # The file being counted declares a label the roadmap and the ledger do not — a
        # deferred store is the one that can. Saying `unknown` beside the lines it just
        # listed would be the payload contradicting the listing.
        return census.select(block=args.block, marker=marker), None
    return census.select(block=args.block, marker=marker), standing


def _list(config: Config, args: argparse.Namespace) -> int:
    try:
        census, standing = _census(config, args)
    except (KeyError, OSError) as error:
        return _refused(error)

    if args.json:
        print(json.dumps(census.listing(standing), indent=2))
    else:
        listed = census.listed(args.ids)
        if listed:
            print(listed)
        for note in census.notes(standing):
            print(note, file=sys.stderr)
    return EXIT_OK


def _stats(config: Config, args: argparse.Namespace) -> int:
    try:
        census, standing = _census(config, args)
    except (KeyError, OSError) as error:
        return _refused(error)

    longest = census.longest()
    if args.json:
        print(
            json.dumps(
                {
                    "file": census.file,
                    "total": census.total,
                    "uncounted": census.uncounted,
                    "markers": census.markers(),
                    "blocks": [
                        {
                            "block": tally.label,
                            "counted": tally.counted,
                            "uncounted": tally.missed,
                            "markers": dict(tally.markers),
                        }
                        for tally in census.tallies()
                    ],
                    "longest": None
                    if longest is None
                    else {
                        "id": longest.task.id,
                        "length": measured_width(longest.raw),
                        "limit": census.schema.line_max,
                        "unit": CHARACTER_UNIT,
                    },
                    # `None` where no block was named, which is the question rather than a
                    # missing answer (RK429): a listing over the whole file has no standing.
                    "standing": None if standing is None else standing.payload(),
                    # RK1139: a capture nothing counts is a note in a drawer, and this tool's
                    # whole argument is against those. Its own key, because it is debt this
                    # project holds and not a line of the backlog it is reporting.
                    "captures": _captures_json(config),
                },
                indent=2,
            )
        )
        return EXIT_OK

    tallies = census.tallies()
    names = [tally.name for tally in tallies] + ["total", "uncounted"]
    width = max(len(name) for name in names)
    print(census.file)
    for tally in tallies:
        print(
            f"  {tally.name:<{width}}  {tally.counted:>4}  "
            f"{_markers(tally.markers)}".rstrip()
        )
    print(
        f"  {'total':<{width}}  {census.total:>4}  {_markers(census.markers())}".rstrip()
    )
    # Printed at zero too: a field that appears only when it is non-zero is a field a
    # reader learns to stop looking for, which is how the miss became invisible.
    print(f"  {'uncounted':<{width}}  {census.uncounted:>4}")
    if longest is not None:
        print(
            f"  {'longest':<{width}}  {longest.task.id} at {measured_width(longest.raw)} "
            f"of {census.schema.line_max}"
        )
    _print_captures(config, width)
    if not census.total:
        _print_standing(standing)
    return EXIT_OK


@dataclass(frozen=True, slots=True)
class _Read:
    """One capture, and what this project can honestly say about it (RK1162).

    Three states and not two, because `filed` was two facts wearing one number: a stamp resolved
    against this project's own ids is a **resolution**, and a stamp naming another repository is
    a **claim** nothing here can check — which is what RK1160 made the row clear on. A tuple
    growing a third position would have carried the distinction and named neither.
    """

    path: Path
    filed: bool
    #: The repository a delivery names, or `""` for a capture this project resolved itself.
    elsewhere: str = ""


def _unfiled(config: Config) -> tuple[_Read, ...]:
    """Each capture this project holds, and whether the backlog already states its claim.

    The reading RK1139 asked for, and the cheap order matters: the directory is globbed first,
    so a project with no captures — which is every project that has never hit a defect in this
    tool — pays one `glob` and never the parse of three governed files.

    "Filed" is an **exact symptom match**, because the capture's symptom is verbatim what
    `add --symptom` receives: an author who ran the pre-filled command produces one, and an
    author who reworded it reads as unfiled. Wrong in the direction that nags.
    """
    held = captures(config.root)
    if not held:
        return ()
    backlog = Backlog.load(config)
    documents = [
        one for one in (backlog.roadmap, backlog.ledger, backlog.store) if one is not None
    ]
    stated = {entry.task.symptom for one in documents for entry in one.entries}
    ids = {entry.task.id for one in documents for entry in one.entries}
    # The stamp first and the prose second (RK1141): an author who ran the pre-filled `add`
    # cleared this row by the act that closed it, and one who reworded the symptom is why the
    # match alone left a row that could never reach zero. An id no file holds does not clear it
    # — a stamp naming a task that was renumbered away is a link and not an outcome.
    # **Unless the stamp names another repository** (RK1160): a capture of a defect in this tool
    # belongs in this tool's backlog, so its id is one no governed file here will ever hold, and
    # both readings above left a row that could only be silenced by a stamp from the wrong
    # repository or by deleting the evidence. Filed by construction, because this cannot read
    # that backlog and does not pretend to.
    return tuple(
        _Read(
            path=one.path,
            filed=bool(delivered(one.filed))
            or (one.filed in ids if one.filed else one.symptom in stated),
            elsewhere=delivered(one.filed),
        )
        for one in held
    )


def _captures_json(config: Config) -> dict[str, object]:
    """The three states, told apart (RK1162).

    `filed` counted a stamp this project resolved and a stamp nothing here can check as one
    number, so a consumer reading `filed: 2` could not tell two closed rows from one closed row
    and one somebody says is closed elsewhere. `delivered` is that second half, as a list for
    `unfiled`'s reason: the repository is what a client shows, and the count is its length.

    RK1147's rule, one command over — the printed report has said which reading cleared the row
    since RK1160, and the payload is the surface an agent reads.
    """
    held = _unfiled(config)
    return {
        "kept": len(held),
        # Resolutions only now: `kept` is still the total, and a client that added `filed` to
        # `delivered` gets what this key used to mean.
        "filed": sum(1 for one in held if one.filed and not one.elsewhere),
        "delivered": [
            {"path": config.relative(one.path), "repository": one.elsewhere}
            for one in held
            if one.elsewhere
        ],
        "unfiled": [config.relative(one.path) for one in held if not one.filed],
    }


def _print_captures(config: Config, width: int) -> None:
    """The captures this project owes an entry for, and the total behind them (RK1139, RK1143).

    Printed **only where one is unfiled**, which is not the rule the counts above follow — they
    print at zero because a field that appears only when it is non-zero is one a reader stops
    looking for. Two differences decide it. `uncounted` is about the file this command reports
    on and a capture is not; and a row that says nothing is owed is never the next step, which
    is RK1121's finding one command over — measured here, where `captures 2  2 filed` printed on
    every run of a tree with no debt at all, for ever, because nothing deletes a capture.

    The **total rides on the row** rather than being lost with it: the number a reader wants
    beside "one is unfiled" is how many there are. What silence costs is the fact that the
    directory has files at all, and that is what the payload keeps — a key costs a client
    nothing to skip, where a line costs every reader the same attention on every run.
    """
    held = _unfiled(config)
    unfiled = [one.path for one in held if not one.filed]
    if not unfiled:
        return
    print(f"  {'captures':<{width}}  {len(held):>4}  {len(unfiled)} unfiled")
    for path in unfiled:
        # Named and not only counted: this is the list the tool asks every project to hold its
        # debt in, and a count with nothing behind it is the silent file again.
        print(f"  {'unfiled':<{width}}  {config.relative(path)}")


def _audit(config: Config, args: argparse.Namespace) -> int:
    try:
        census, standing = _census(config, args)
    except (KeyError, OSError) as error:
        return _refused(error)

    if args.json:
        print(json.dumps(census.audit(standing), indent=2))
    else:
        print(census.audited())
        for note in census.silence(standing):
            print(note, file=sys.stderr)
    return EXIT_OK


def _claims(config: Config, args: argparse.Namespace) -> int:
    """The registry read against the roadmap (RK161). Nothing here is a failure, so exit 0."""
    try:
        # The whole backlog and not the roadmap alone (RK164): three of the four ways an id can
        # be absent from it are recorded in the other two files.
        if args.prune:
            pruning = claiming.prune(config)
            rows, dropped = pruning.kept, pruning.dropped
        else:
            rows, dropped = claiming.survey(Backlog.load(config)), ()
    except (KeyError, OSError) as error:
        return _refused(error)

    registry = str(claiming.path(config.root))
    held = sum(1 for row in rows if row.state is claiming.State.HELD)
    if args.json:
        print(
            json.dumps(
                {
                    "window": config.held,
                    "registry": registry,
                    "held": held,
                    "claims": [row.payload() for row in rows],
                    # Named and not counted, and present as an empty list when the flag was
                    # passed and dropped nothing (RK165): a prune that hides its own effect is
                    # how "the registry is clean" gets read off a command that emptied it.
                    "pruned": None if not args.prune else [row.payload() for row in dropped],
                },
                indent=2,
            )
        )
        return EXIT_OK

    print(f"{len(rows)} dated, {held} held  (window {config.held}m)")
    for row in rows:
        print(row.listed())
    for row in dropped:
        print(row.listed(pruned=True))
    if args.prune and not dropped:
        print("  pruned   nothing: every row is a claim")
    # Named because the release is a marker and the *file* is what an operator deletes when a
    # whole checkout's worth of claims outlived their workers (RK161).
    print(f"  registry {registry}")
    return EXIT_OK


def _claim(config: Config, args: argparse.Namespace) -> int:
    """One held line's scope: declared, or read back at the commit (RK280).

    The read is the half that earns the command. `git status` shows a tree two sessions wrote
    and says nothing about which half is whose, so the author committing was left an analysis
    to make with no facts to make it from — and `agents.md` carried the answer as advice,
    which RK1 says does not hold. Here the three lists are separate because the caller does
    three different things with them: stage `mine`, leave `theirs`, and decide about `loose`.

    `--add-path` is the same write from the other end (RK307), and passing both is refused
    rather than merged: `--path` says *this is the scope* and `--add-path` says *and this
    too*, so a call making both statements is one whose author has not decided which — and
    reading it as either would be the tool picking.
    """
    backlog = Backlog.load(config)
    entries = backlog.roadmap.entries
    if args.path and args.add_path:
        return _refused(
            ValueError(
                "--path replaces the scope and --add-path keeps it, so a call passing both "
                "says two things about one commit: name the whole scope with --path, or add "
                "to what is already there with --add-path alone"
            )
        )
    try:
        if args.path or args.add_path:
            mine = claiming.scope(
                config,
                args.id,
                args.path or args.add_path,
                extend=bool(args.add_path),
            )
        else:
            held = next((one for one in claiming.live(config, entries) if one.id == args.id), None)
            if held is None:
                raise claiming.NotHeld(args.id)
            mine = held.paths
    except (claiming.NotHeld, KeyError, OSError) as error:
        return _refused(error)

    # What this task's own transactions already wrote (RK342), by the reading `ship` makes
    # off its own `save` — which only exists inside a transaction, so here it is read off
    # the files: a claim moved a marker onto this line and the projections were refreshed
    # from it, and both diffs name the id. Without it the report called them `loose`, which
    # reads as *somebody else touched this*, and the author declared them by hand to
    # silence it — the scope then carrying paths that were never the work.
    seen = status(config)
    wrote = claiming.written(config, args.id, seen.changed)
    if args.porcelain:
        # Nothing but the paths: this form is consumed by `git add --`, so a heading on it
        # would be a filename to a shell and the contract has to be safe to pipe. The
        # written ones join it for the reason they join the stage line: what the author
        # does with both lists is the same `git add`.
        for one in dict.fromkeys((*mine, *wrote)):
            print(one)
        return EXIT_OK

    # The subtraction is `claiming`'s (RK294), because `ship` asks for the same lists at the
    # moment of committing and two compositions of one answer is how they come to disagree.
    # Git is asked here and not there: this command was told to answer.
    # `accounted=wrote` (RK1117): here the word means what it always meant on this path — the
    # dirty governed files whose diff carries this id — and the subtraction it feeds is the
    # same one a departure makes, now made in one place rather than by each printer.
    #
    # And `shared` with it (RK1122): this is the read a commit is composed from, so the ids
    # inside a file it is about to stage are exactly what it exists to say. Asked here rather
    # than deep in the split for the same reason `dirty` is — this command was told to answer.
    scope = claiming.split(
        config,
        args.id,
        entries,
        seen.changed,
        indexed(config),
        accounted=wrote,
        shared=claiming.sharing(config, args.id, wrote),
        staged=seen.staged,
    )
    if args.json:
        print(
            json.dumps(
                {
                    "id": args.id,
                    "paths": list(scope.mine),
                    # Its own key and never merged into `paths` (RK309, RK342): a client
                    # that read them as one would be handed a scope this tool never
                    # received, and the two answer different questions.
                    "wrote": list(wrote),
                    "theirs": [
                        {"path": one, "claimed_by": who} for one, who in scope.theirs
                    ],
                    "unclaimed": list(scope.loose),
                    # Which of them the index already carries (RK1197), the key a departure
                    # answers under the same name: a client acting on `unclaimed` decides, and
                    # one acting on this has already been committed to by a `git add`.
                    "unclaimed_staged": list(scope.staged),
                    # The same list a departure carries, and computed here since RK1122: the
                    # two readers of one contract answering differently was the defect.
                    "shared": [
                        {"path": one, "ids": list(named)} for one, named in scope.shared
                    ],
                    "staging_nothing": list(scope.idle),
                },
                indent=2,
            )
        )
        return EXIT_OK

    print(f"{args.id} claims {len(mine)} path(s)")
    idle = set(scope.idle)
    for one in scope.mine:
        # Annotated where it stands, and not listed again below (RK295): the mistyped path
        # and the real one are two lines apart, and the eye reads the second as somebody
        # else's unless the first says what is wrong with it.
        print(f"  mine     {one}{'  (stages nothing right now)' if one in idle else ''}")
    for one in wrote:
        # Named rather than folded into `mine`, for the reason a departure keeps them
        # apart (RK309): the scope is what the holder said, verbatim, and these are not a
        # declaration to be corrected but a record to be used.
        print(f"  wrote    {one}  (this task's own transactions)")
    _print(_scope_rows(scope, wrote))
    if not mine:
        print(f"  none declared: `claim {args.id} --path <p>` says what this commit owns")
    return EXIT_OK


def _writes(config: Config, args: argparse.Namespace) -> int:
    """The write record read against the files (RK200). Nothing here is a failure, so exit 0."""
    survey = attesting.Survey(
        attesting.survey(config), str(attesting.record_path(config.root))
    )
    if args.json:
        print(json.dumps(survey.payload(), indent=2))
    else:
        print(survey.stated())
    return EXIT_OK


def _markers(markers: Mapping[str, int]) -> str:
    return "  ".join(f"{marker} {count}" for marker, count in markers.items())


def _brief(config: Config, args: argparse.Namespace) -> int:
    if args.id is not None and (args.block is not None or args.designed):
        # Two answers to one question: the id names a task and the others name a search.
        narrowed = "--block" if args.block is not None else "--designed"
        print(
            f"roadkeep: give an id or {narrowed}, not both: an id is already the answer "
            f"{narrowed} would look for",
            file=sys.stderr,
        )
        return EXIT_USAGE
    try:
        gathered = brief(config, args.id, args.block, args.designed, args.claim)
    except NothingToBrief as nothing:
        # The one branch a loop actually reads, and the one `--json` did not cover (RK409).
        # `brief --block <x>` is how a worker asks what to do next, and "nothing is open in
        # Block <x>" is the only answer that means the block is finished — so a loop driving
        # one to completion polls exactly this, and asked for JSON got an empty stdout and
        # the sentence on stderr, where a real failure also lands.
        #
        # Still **not** exit 0, and still not a fourth exit code. An empty answer is nothing
        # to brief, so succeeding would make a typo'd block name look like a finished one;
        # and what the caller could not do at exit 2 was tell those two apart, which the
        # payload now answers directly — `standing.state` is the word, `empty` stays the
        # boolean it always was, and the refusal for a name nothing declares never reaches
        # here at all (RK429 made the sentence say which; this comment predates it).
        if args.json:
            print(json.dumps(_nothing_json(nothing, args), indent=2))
            return EXIT_USAGE
        return _refused(nothing)
    except REFUSALS as error:
        # The whole tuple, because `--claim` makes this a write (RK149): every refusal that
        # guards a marker reaches here, plus the one this door has of its own — a named line
        # somebody else is already holding.
        return _refused(error)

    # Both registers off the record (RK1170), and the last of the verbs that task measured:
    # `Brief` is the answer, and its two readings were 20 prints here and a builder in
    # `rendering.py` — one answer in two files, with neither of them where a brief is composed.
    print(json.dumps(gathered.payload(config), indent=2) if args.json else gathered.stated(config))
    return EXIT_OK


def _show(config: Config, args: argparse.Namespace) -> int:
    """One task, whole, from every file that holds a piece of it (RK9).

    Both registers come off the record (RK1170): `View` is the answer, and its two readings were a
    printer here and a builder in `rendering.py` — one verb spelled in two files, with neither
    holding both. What is left here is the door.
    """
    try:
        view = show(config, args.id)
    except (KeyError, OSError) as error:
        return _refused(error)

    if args.json:
        print(json.dumps(view.payload(body=not args.no_body), indent=2))
    else:
        print(view.stated(config, body=not args.no_body))
    return EXIT_OK


def _budget(config: Config, args: argparse.Namespace) -> int:
    # Which of the four subjects was asked for, and whether `--role` or `--lead` came with
    # the one it narrows, are `answers` and `narrows` at this verb's own `add_parser` and
    # `dispatch`'s to refuse (RK489). What is left here is the dispatch itself.
    if args.anchor:
        return _body_budget(config, args)
    if args.non_goal:
        return _non_goal_budget(config, args)
    if args.file is not None:
        return _file_budget(config, args)
    if args.tools:
        return _tools_budget(config, args)
    if args.session:
        return _session_budget(config, args)
    try:
        answer = budget(
            config,
            args.id,
            block=args.block,
            deps=args.deps,
            status=args.status,
            symptom=args.symptom,
            family=args.family,
            ref=args.ref,
        )
    except REFUSALS as error:
        return _refused(error)

    # Both registers off the record (RK1170): `Budget` already was the result this verb computed,
    # and its two readings were a printer here and a builder in `rendering.py` — one answer in two
    # files, with neither holding both.
    print(json.dumps(answer.payload(), indent=2) if args.json else answer)
    return EXIT_OK


def _body_budget(config: Config, args: argparse.Namespace) -> int:
    """What a section body may say, before it is written (RK283)."""
    try:
        answer = body_budget(config, args.anchor, args.role)
    except REFUSALS as error:
        return _refused(error)
    if args.json:
        print(json.dumps({"subject": "section", **answer.payload()}, indent=2))
        return EXIT_OK
    state = "written" if answer.written else "the section add would write"
    print(f"§{answer.anchor}  {answer.role}  ({state})")
    print(f"  body       {answer.stated(named=False)}")
    return EXIT_OK


def _file_budget(config: Config, args: argparse.Namespace) -> int:
    """What an always-loaded file has left, before the edit is composed (RK345)."""
    try:
        loads = file_budget(config, args.file or None)
    except REFUSALS as error:
        return _refused(error)
    if args.json:
        print(json.dumps({"subject": "file", "files": [_load_json(one) for one in loads]},
                         indent=2))
        return EXIT_OK
    for load in loads:
        # The state `lint` calls `budget.absent`, said here too: a declared file that is not
        # there has its whole budget free, which is the one reading that looks like room.
        state = "on disk" if load.present else "not on disk — the entry holds nothing"
        print(f"{load.path}  budgeted  ({state})")
        for cost in load.costs:
            # No aim and no second unit (RK258): `[budgets]` is declared in what the loader
            # pays, so a word figure beside it would be a number this project never stated.
            over = f", {cost.over} over" if cost.over else f", {cost.left} left"
            print(f"  {cost.unit:<11}{cost.taken} of {cost.limit}{over}")
        if load.translated:
            # The remainder the ceiling does not charge (RK1105). Printed under the units and
            # not beside one, because it is a fact about the checkout and not about the budget:
            # the number above decides, and this one is what a loader here actually reads.
            print(
                f"  {'checkout':<11}{load.translated} more, this tree's lines ending CRLF — "
                f"counted as the commit stores them"
            )
        _print_parts(load)
    return EXIT_OK


#: How many sections the terminal names, for `_LARGEST_TOOLS`' reason: the largest few are
#: where the size went, and a caller reading a report to decide what to cut wants those.
_LARGEST_PARTS = 4


def _print_parts(load: Load) -> None:
    """Where the size is, so the next compression is aimed (RK1092).

    The read `budget --tools` makes about the served surface, one file over: a total says an
    edit will be refused and says nothing about what to take out, and `agents.md` reaching
    eight bytes of room turned *compress the prose* into a preference nothing had re-measured.

    Only where the file is on disk and holds more than one section, because a single-section
    file's breakdown is the total printed twice.
    """
    if len(load.parts) < 2:
        return
    for part in load.parts[:_LARGEST_PARTS]:
        print(f"    {part.bytes:>6}  {part.lines:>3}  {part.heading or '(before the first ##)'}")
    if len(load.parts) > _LARGEST_PARTS:
        print(f"    … and {len(load.parts) - _LARGEST_PARTS} more — `--json` lists every one")


def _non_goal_budget(config: Config, args: argparse.Namespace) -> int:
    """The two limits the roadmap's other bullet has (RK283)."""
    try:
        shares = non_goal_budget(config, args.lead)
    except REFUSALS as error:
        return _refused(error)
    if args.json:
        print(json.dumps({"subject": "non-goal", "lead": args.lead,
                          "fields": [one.payload() for one in shares]}, indent=2))
        return EXIT_OK
    where = config.relative(config.path("roadmap"))
    state = f"the bullet leading {args.lead!r}" if args.lead else "the bullet add would write"
    print(f"non-goals  {where}  ({state})")
    for share in shares:
        # No `bound_by_line`: a non-goal is two fields on two lines and there is no third
        # limit measured across them, which is the whole difference from a task line.
        taken = f", {share.taken} written, {share.left} left" if share.taken else ""
        print(f"  {share.field:<11}{share.limit}{taken}  {share.aimed}")
    return EXIT_OK


#: How many tools the listing names before it stops naming them one by one. The largest few
#: are where the size went, and a caller reading a report to decide what to cut wants those;
#: the rest is the total, which is the number this read exists to state (RK464).
_LARGEST_TOOLS = 5


def _session_budget(config: Config, args: argparse.Namespace) -> int:
    """Both halves of what a session pays, against the cadence each is paid at (RK1095).

    `--tools` totals the served schema and `--file` totals a resident file, and neither knew
    the other existed — so an author deciding whether to cut a tool description or a
    paragraph ran two commands and subtracted by hand. That is the arithmetic RK183 removed
    from the line budget and RK345 from the file one, still standing one level above both.

    **Two figures and never a sum.** The schema is sent once at the handshake and a resident
    file is read on every turn, so adding them produces a number that is wrong for every
    session whose turn count is not one — which is all of them. What is honest is naming each
    against what it is paid for, and letting the reader multiply the half that repeats.

    The skill is not here, deliberately (RK23): it is trigger-loaded, so it costs the turns
    that write and nothing on the turns that do not, and pricing it as resident would be the
    third figure this read exists to avoid inventing.
    """
    # One measurement, two readers (RK1096) — the rule RK345 already states about the file
    # half, applied to the surface: `--tools` ranks what this returns and `--session` totals
    # it, so a change to what the handshake carries moves both or neither.
    sent = surface(config)
    resident = [(load.path, load.bytes) for load in (file_budget(config) if config.budgets else ())]
    once, turn = sent.characters, sum(cost for _path, cost in resident)
    if args.json:
        print(
            json.dumps(
                {
                    # Named by cadence rather than by subject, because that is the fact a
                    # caller is deciding against — and a `total` key would be the sum this
                    # read refuses to compute.
                    "once": {
                        "characters": once,
                        "unit": CHARACTER_UNIT,
                        "of": f"{len(sent.tools)} tool(s) and the handshake",
                    },
                    "each_turn": {
                        "bytes": turn,
                        "files": [
                            {"path": path, "bytes": cost} for path, cost in resident
                        ],
                    },
                },
                indent=2,
            )
        )
        return EXIT_OK

    print(
        f"session    {once} {CHARACTER_UNIT} once, {turn} bytes on every turn — "
        f"two cadences, so they are not added"
    )
    print(f"  once     {once:>6}  {len(sent.tools)} tool(s) and the handshake, at connect")
    for path, cost in resident:
        print(f"  turn     {cost:>6}  {path}")
    if not resident:
        # The state `--file` raises on, said rather than left as an absent row: a project
        # with no `[budgets]` pays the schema and nothing else, which is a real answer.
        print("  turn          0  this project declares no [budgets] file")
    return EXIT_OK


def _tools_budget(config: Config, args: argparse.Namespace) -> int:
    """What this project's tool list costs a session, stated because nothing stated it (RK464).

    RK30 put `[budgets]` on the files a session loads every turn, because resident prose has
    no natural ceiling — the 186 KB `agents.md` in §0.1 is the measurement this project starts
    from — and `lint` refuses one over. The schema this server publishes was counted nowhere:
    measured on a three-file project, 51 tools and 52,892 characters, six times the budget the
    resident file is held to, paid once per session that connects the server.

    That is not a claim the list is too long. It is that the number was not stated, and RK30's
    own argument is that a limit nobody counts is a limit that moves: every task adding a tool
    or a sentence to a description spends this, and each spend looks free where it is written.

    **And the ceiling §RK464 left open** (RK1059), once the number had been looked at: it is
    per tool, declared as `[tools] characters`, and `lint` refuses one over. A total names
    nothing — it fails on whichever tool is added last — where a per-tool figure is refused
    by the tool whose description somebody just edited, which is the ranking this read
    already prints. Reported here as the room a caller has before the gate says no, which is
    the pairing RK345 makes everywhere else: a limit that reaches an author only as a refusal
    is the verdict-after-the-prose this project exists to replace.

    **Both halves of what a session is handed** (RK1062), because one of them was a place to
    hide in. The handshake is the other message sent before the first call, and RK1060 moved
    a paragraph from the tool list into it — a real saving, reported gross, by a read that
    could not see where it went. An edit that saved nothing would have measured the same.
    Not folded into the ranking: no per-tool ceiling is about it, so it is named under them.

    Derived from :func:`~roadkeep.serving.descriptors`, so it is the payload a client is
    actually sent rather than a second estimate of it: a description reworded in `cli.py`
    moves this figure, which is the whole reason the number is worth reading.
    """
    # The same measurement `--session` totals (RK1096), so the ranking and the total cannot
    # come to disagree about what a client is sent.
    sent = surface(config)
    listed = sent.listed
    # The other thing a session is handed before its first call (RK1062). Counted here for
    # the reason the tool list is: RK1060 moved a paragraph out of 13 properties and into
    # this message, and a read that saw only one side reported the gross figure as the net
    # — a number improvable by moving text out of its own view rather than by cutting it.
    # Once and not per call, which is the footing the list is already on.
    handshake = sent.handshake
    total = sent.characters
    ranked = list(sent.tools)
    if args.json:
        print(
            json.dumps(
                {
                    "tools": len(sent.tools),
                    # The session's whole cost, which is what the verb exists to answer; the
                    # two halves are named beside it rather than left to be added.
                    "characters": total,
                    "tool_list": listed,
                    "handshake": handshake,
                    "unit": CHARACTER_UNIT,
                    # Every tool and not the largest few: a caller reading this to decide what
                    # to cut is reading a payload, where the terminal is reading a report.
                    "by_tool": [{"name": name, "characters": size} for name, size in ranked],
                    # What one tool may cost, and null where the project declares none
                    # (RK1059) — the gate's number, so the read and the refusal are one.
                    "each": config.tool_characters,
                    "over": [
                        name
                        for name, size in ranked
                        if config.tool_characters is not None and size > config.tool_characters
                    ],
                },
                indent=2,
            )
        )
        return EXIT_OK
    print(f"session    {len(sent.tools)} tool(s) and the handshake, {total} {CHARACTER_UNIT}")
    for name, size in ranked[:_LARGEST_TOOLS]:
        # The room before the gate says no, said beside the figure it is about: a budget
        # reported only as a total leaves the author to subtract per tool (RK345).
        room = "" if config.tool_characters is None else f"  {config.tool_characters - size:+}"
        print(f"  {name:<16} {size}{room}")
    if len(ranked) > _LARGEST_TOOLS:
        print(f"  … and {len(ranked) - _LARGEST_TOOLS} more — `--json` lists every one")
    # Under the ranking and not folded into it: it is not a tool, no per-tool ceiling is
    # about it, and a row among them would read as one that had escaped the gate.
    print(f"  {'handshake':<16} {handshake}  (instructions, sent once)")
    if config.tool_characters is not None:
        over = sum(1 for _, size in ranked if size > config.tool_characters)
        print(
            f"  each     {config.tool_characters} {CHARACTER_UNIT}, "
            f"{over} over — `lint` is what refuses one"
        )
    return EXIT_OK


def _pick(config: Config, args: argparse.Namespace) -> int:
    """The next task this backlog offers, and why that one (RK11).

    Both registers come off one record (RK1170): the choice, the claim and the event reached this
    handler as three values and were rendered here and in `rendering.py`, so the verb's two
    readings sat in two files and neither was where the choice is made.
    """
    claim: Claim | None = None
    try:
        if args.claim:
            claim = take(config, args.block, args.designed)
            choice = claim.choice
        else:
            choice = pick(config, args.block, args.designed)
    except REFUSALS as error:
        # The whole tuple and not `(KeyError, OSError)`: with `--claim` this command writes a
        # marker, so every refusal that guards a marker — a stale file, a sibling stating
        # status — reaches here, and a traceback is what the caller would otherwise read.
        return _refused(error)

    answer = Picked(
        config=config, choice=choice, claim=claim, event=_claim_event(claim, config)
    )
    print(json.dumps(answer.payload(), indent=2) if args.json else answer)
    return EXIT_OK


def _export(config: Config, args: argparse.Namespace) -> int:
    # Both destinations in one run: a README and a page that restate the same backlog have
    # to be refreshed by the same call, or the one nobody remembered is the stale one —
    # which is the whole symptom RK39 names, and it named the site too.
    chosen: list[tuple[str, str | None]] = [
        (flag, name)
        for flag, name in (("readme", args.readme), ("site", args.site))
        if name is not None
    ]
    if args.contents:
        # No path of its own (RK1110): the target is the project's `[files]` rationale file, so
        # a path here would be a second answer to a question the config already answers —
        # `None` is what sends `splice_into` through the resolver the gate reads too.
        chosen.append(("contents", None))
    try:
        projection = project(config)
        if not chosen:
            print(projection.json() if args.json else projection.markdown())
            return EXIT_OK
        planned = [splice_into(config, projection, flag, name) for flag, name in chosen]
        # Both targets or neither (RK187, RK6): the splice is planned per file and the
        # writes are made together, so a README refreshed beside a site refused is a state
        # the command cannot leave — and the re-run it advises meets a whole tree.
        write_all(*[write for write, _ in planned if write is not None])
    except (KeyError, ValueError, OSError, StaleFile) as error:
        return _refused(error)

    for _, line in planned:
        print(line)
    return EXIT_OK


def _gaps(config: Config, args: argparse.Namespace) -> int:
    """Which ids below the highest no file carries, and what became of each (RK39, RK95).

    Both registers come off one result (RK1170): `Gapped` renders them beside the reading that
    found the gaps, so the collapsed rows the printed answer shows and the per-id list the payload
    carries are two readings of one thing rather than two functions two files apart.
    """
    answer = Gapped(gaps=gaps(config))
    print(json.dumps(answer.payload(), indent=2) if args.json else answer)
    return EXIT_OK


def _anchors(config: Config, args: argparse.Namespace) -> int:
    """Live and retired addresses across this project's prose (RK247, RK297)."""
    # Every declared role unless one is named. `--role` narrows the *listing* and never the
    # free address, which is computed per namespace (RK340, RK346): where no `[refs]` declares
    # one, both files number into the same namespace and a `next` taken from one of them is
    # the answer this read exists to stop somebody acting on (RK297); where one is declared,
    # the row for that namespace is that file's own and the sibling's is not an answer about
    # it. Reading every role either way is what makes `doubled` visible before a pick (RK383).
    asked = [one for one in PROSE_ROLES if config.has(one)]
    role = args.role or ""
    if (role and not config.has(role)) or not asked:
        print(
            f"roadkeep: this project declares no {role or 'prose'} file "
            f"({', '.join(PROSE_ROLES)} is what an anchor lives in)",
            file=sys.stderr,
        )
        return EXIT_USAGE
    # The block a caller knows, resolved to the family they do not (RK312): under an outline
    # the prose file declares no block heading, so which numeral a block's designs sit under
    # is written nowhere and used to be globbed out of the pointers by hand. Resolved into
    # `--family` rather than carried alongside it, so every line below stays one answer.
    block = args.block or ""
    if block and args.family:
        print(
            "roadkeep: --block resolves to a family, so passing both asks two questions: "
            f"`{invocation()} anchors --block {block}` names the families, and "
            f"`{invocation()} anchors --family <one of them>` narrows to it",
            file=sys.stderr,
        )
        return EXIT_USAGE
    spans: tuple[str, ...] = ()
    if block:
        spans = families_of_block(config, block)
        if not spans:
            print(
                f"roadkeep: no open line in Block {block} carries a pointer, so nothing "
                f"says which family its prose lives under — `anchors` alone lists every "
                f"top-level, and its next free one is where a new block starts",
                file=sys.stderr,
            )
            return EXIT_USAGE
        # One family narrows; two are reported as the listing they are, because which of them
        # a new line belongs under is the caller's judgement and not a fact any file holds.
        if len(spans) == 1:
            args.family = spans[0]
    found = anchors(config, role, args.family)
    whole = found if not role else anchors(config, "", args.family)
    retired = [one for one in found if not one.live]
    # An address that is a task **id** is a question already answered: `add` refuses to
    # reuse one (RK4), and every shipped task leaves its section retired — so on this
    # project they are 287 of the 307 rows and none of them is a choice anybody makes.
    read = [role] if role else asked
    ids = config.schema_for(role or asked[0]).id_pattern()
    outline = [one for one in found if not ids.match(one.anchor.split(".")[0])]
    # The same set over the project, which is what a free address is derived from even when
    # the listing was narrowed to one file (RK297).
    spread = [one for one in whole if not ids.match(one.anchor.split(".")[0])]
    spent = len(found) - len(outline)
    if args.only_next and args.json:
        # The narrow read, in the narrow shape (RK410). `family` and `namespace` are kept
        # because the answer is meaningless without saying which numbering it continues —
        # everything else in the wide payload is the listing this flag exists to leave out.
        print(
            json.dumps(
                {
                    "family": args.family,
                    "next": next_child(whole, args.family) if args.family else None,
                    "next_families": []
                    if args.family
                    else [
                        {
                            "namespace": space or None,
                            "next": next_family(spread, space),
                            # The same sentence the reader gets, as the command it names
                            # (RK1140): a client composing `add --ref <next>.1` walks into the
                            # refusal a person now reads about, and two answers to one question
                            # is what a payload beside a report must not be.
                            "opens": None
                            if not (fresh := next_family(spread, space))
                            else f"section add {fresh} --title …",
                        }
                        for space in namespaces(spread)
                    ],
                },
                indent=2,
            )
        )
        return EXIT_OK
    if args.json:
        print(
            json.dumps(
                {
                    "role": role or None,
                    # Every file the answer was read from, and not one (RK297): a client
                    # comparing two runs needs to know which outline it was handed.
                    "files": [config.relative(config.path(one)) for one in read],
                    "family": args.family,
                    # The block asked about and every family its pointers name (RK312) —
                    # both, because one of them narrowed the listing and two did not, and a
                    # client cannot tell those apart from `family` alone.
                    "block": block or None,
                    "block_families": list(spans),
                    "live": len(found) - len(retired),
                    "retired": len(retired),
                    # The rows are the answer where a family was named, and the families are
                    # the answer where none was (RK264's rule, applied before it was asked):
                    # 287 retired addresses is not a listing anybody reads.
                    # Under `--claims` the rows *are* the answer whatever the family, which
                    # is the whole of RK459: the listing RK264 withholds is the one nobody
                    # reads, and this one is only ever the exceptions.
                    "anchors": [
                        _anchor_row(one)
                        for one in found
                        if args.family or (args.claims and _ownership(one))
                    ],
                    "families": [] if args.family else _families(outline),
                    "id_anchors": spent,
                    # Both free addresses are the **project's** even where the listing was
                    # narrowed (RK297): the field an author acts on may not be per file.
                    "next": next_child(whole, args.family) if args.family else None,
                    # The question one line up, and the one a reused block asks (RK293) —
                    # asked **per namespace** and nowhere else (RK340/RK346). One row where a
                    # project declares no `[refs]`, whose `namespace` is null, and one per
                    # namespace where it does; `next` is null inside a row where those
                    # top-levels are not one numbering, which is an answer and not an absence.
                    # The bare `next_family` that sat beside this is gone: it answered for the
                    # unprefixed namespace alone, so on a project whose roles each declare one
                    # it named a namespace that no longer exists, and on a project with one it
                    # was right by coincidence — two readings of one field with nothing to tell
                    # them apart, which is what `ref.ambiguous` refuses one layer down.
                    "next_families": []
                    if args.family
                    else [
                        {"namespace": space or None, "next": next_family(spread, space)}
                        for space in namespaces(spread)
                    ],
                    # What no question asked and only the gate said (RK297): an address two
                    # headings answer to is one no pointer resolves against.
                    "doubled": [
                        {"anchor": anchor, "files": list(roles)}
                        for anchor, roles in doubled(whole)
                    ],
                },
                indent=2,
            )
        )
        return EXIT_OK

    if args.only_next:
        return _next_anchor(args, whole, spread)

    where = ", ".join(config.relative(config.path(one)) for one in read)
    if args.claims:
        # Its own header and not a second one under the totals (RK459): this listing is the
        # exceptions, so the number a reader wants first is how many there are of them.
        rows = [one for one in found if _ownership(one)]
        # The memos are counted and not listed (RK461): "five of them and none needing
        # anything" is a different answer from silence, and it is the answer an adopting
        # corpus most often has.
        memos = sum(1 for one in found if one.memo)
        counted = f", {memos} standing memo(s)" if memos else ""
        print(
            f"{len(rows)} of {len(found)} address(es) say something about ownership"
            f"{counted}  ({where})"
        )
        for one in rows:
            named = f"  in {one.role}" if len(read) > 1 else ""
            print(f"  {one.anchor}{named}{_ownership(one)}")
        _doubled(whole)
        return EXIT_OK
    print(f"{len(found)} anchor(s), {len(retired)} retired  ({where})")
    if block:
        # Said whichever way it went (RK312): one family is the narrowing the rest of this
        # output is already about, and two is the answer itself — the caller picks, because
        # which subtree a new line belongs under is a judgement no file holds.
        named = ", ".join(f"§{one}" for one in spans)
        # The whole command and not the flag alone (RK1022). A caller arrives here from an
        # `add` refusal that named `--ref`, so a bare `--family` reads as a second flag of
        # the verb they were writing — and `add --family` is an argparse error, which is a
        # worse refusal than the validation one it followed. Spelled with an address off
        # this very listing, so what to run next is a line to copy and not a shape to build.
        print(
            f"  block    Block {block}'s prose is under {named}"
            + (
                ""
                if len(spans) == 1
                else f" — pick one, e.g. `{invocation()} anchors --family {spans[0]}`"
            )
        )
    if args.family:
        for one in found:
            written = f"  written in {one.written_in[:7]}" if one.written_in else ""
            # The file, wherever the project has more than one: two rows spelling the same
            # address are the doubling, and unlabelled they read as one row printed twice.
            named = f"  in {one.role}" if len(read) > 1 else ""
            print(
                f"  {'live' if one.live else 'retired':<8} {one.anchor}{named}{written}"
                f"{_ownership(one)}"
            )
        print(
            f"  next     §{next_child(whole, args.family)} — nothing ever used it"
            f"{_room_left(config, read, args.family)}"
        )
        _doubled(whole)
        return EXIT_OK
    # Beside the totals and above the rows, because it is the question a reused block asks
    # first and the listing cannot be read for it (RK293): the rows are per family, and the
    # last one is only the maximum once they are ordered by the number a numeral spells.
    for space in namespaces(spread) if spread else ():
        # One line per namespace (RK340). Where a project declares no `[refs]` this is the
        # one line it always printed; where it does, the two files each continue their own
        # numbering, and a single answer would give one file the other's next address.
        fresh = next_family(spread, space)
        named = f" in {space}" if space else ""
        print(
            f"  next     §{fresh} — no family{named} ever used it"
            if fresh
            else f"  next     — these families{named} are not one numbering, so none derives"
        )
    for family in _families(outline):
        # The files only where there is more than one to name (RK297): on the single-file
        # project that is every project until it declares a second, it would be noise.
        across = family["files"]
        spans = f"  ({', '.join(across)})" if len(across) > 1 else ""  # type: ignore[arg-type]
        print(
            f"  {family['family']:<8} {family['live']} live, {family['retired']} retired"
            f"  next §{family['next']}{spans}"
        )
    if spent:
        print(f"  {spent} address(es) are task ids, which `add` already refuses to reuse")
    _doubled(whole)
    if outline:
        # Named because the listing above is per family and the addresses are what the
        # caller came for: one flag away, and never printed by the hundred unasked.
        print(
            f"  `{invocation()} anchors --family <anchor>` lists the addresses under one"
        )
    return EXIT_OK


def _room_left(config: Config, roles: Sequence[str], family: str) -> str:
    """What the parent of an offered child address has left, where it has too little (RK1024).

    An address `add` will refuse is an address this listing should not hand over silently.
    Measured: `anchors --block AJ` offered `§L.1`, `§L` was 299 words of its own 300, and
    every child of it — the empty one included — was over before a word was composed. The
    listing said nothing, `budget` said 51 words were left, and `lint` was the first reader
    to mention it, after the prose existed.

    Said and never refused, because `anchors` is a read (L5): the caller may be about to
    shorten the parent, which is a plan no count can see. The threshold is the aim rather
    than the limit — an address with a handful of words under it is one nobody can write a
    rationale at, and stating a number that small is the same service as stating none left.
    """
    for role in roles:
        answer = binding(config, role, family)
        if answer is None:
            continue
        taken, limit = answer
        if taken >= body_aim(limit):
            return (
                f", but §{family} already spends {taken} of its {limit} words, "
                f"so a child of it is charged over the limit before it is written"
            )
    return ""


def _doubled(taken: Sequence[Anchor]) -> None:
    """The addresses two prose files both declare, named here rather than only at the gate.

    `lint` reports them as `ref.ambiguous`, and by then both headings exist and four verbs
    refuse to resolve between them (RK297). This is the read an author makes *before*
    choosing, so it is where the state is cheapest to hear about.
    """
    for anchor, roles in doubled(taken):
        print(f"  doubled  §{anchor} is declared by {' and '.join(roles)}")


def _next_anchor(args: argparse.Namespace, whole, spread) -> int:
    """The free address alone, which is the read this command answers most often (RK410).

    `anchors` answers two questions at once: which addresses a family has spent, asked once
    before reopening a shipped subtree, and which one nothing ever used, asked by every `add
    --ref`. Under a 27-anchor family the second answer was the 28th row — so the caller
    taking the next child scrolled past 27 lines it had not asked for, and on a tool result
    the rows are what gets truncated first, which made the one line that mattered the one
    most likely to be cut.

    A filter over a list already computed, so nothing here re-derives an address: the point
    is to leave the listing out, not to answer differently. `--role` still narrows the
    listing and never the number (RK297), which is why the wide read stays the way to see
    where an address came from.
    """
    if args.family:
        # No note here, and the difference is the whole of RK1140: a free **child** is
        # placeable the moment it is answered, because the family's heading already exists —
        # `add --ref XXII.3` resolves. It is the top-level below that is an address and not
        # yet a section.
        print(f"§{next_child(whole, args.family)}")
        return EXIT_OK
    if not spread:
        # No outline family at all: the free address is the first numeral, and saying so is
        # the answer — an empty stdout here reads as a command that failed quietly.
        print(
            "roadkeep: no outline family exists yet, so none is spent — `add --ref I.1` "
            "opens the first",
            file=sys.stderr,
        )
        return EXIT_USAGE
    for space in namespaces(spread):
        fresh = next_family(spread, space)
        named = f"  {space}" if space else ""
        # The same refusal the wide read gives, in one line: a namespace whose top-levels
        # are not one numbering derives nothing, and a blank row would read as an address.
        print(f"§{fresh}{named}" if fresh else f"—{named}  not one numbering, so none derives")
        if fresh:
            # What the answer left to the next refusal (RK1140). `anchors` reads which
            # addresses the outline has **spent**, so a free top-level is a fact about
            # numbering — and `add --ref XXII.1` then refuses, because a pointer resolves to a
            # section and nothing declares `XXII` yet. Captured in this repository: the read
            # answered `XXII` and the write answered "no section XXII.1 extends".
            #
            # On stderr for `next-id`'s reason: stdout here is the address and nothing else,
            # because this command exists to be captured in a shell. RK93's shape one command
            # earlier — the read that creates an expectation names what closes it.
            print(f"roadkeep: {_opens(fresh)}", file=sys.stderr)
    return EXIT_OK


def _opens(family: str) -> str:
    """The sentence a free top-level owes, and the command that makes it a section (RK1140)."""
    return (
        f"§{family} is free and not yet a section, so `{invocation()} add --ref {family}.1` "
        f"refuses until one exists — `{invocation()} section add {family} --title \"…\"` "
        f"declares it, and the pointer resolves from then on"
    )


def _ownership(one: Anchor) -> str:
    """Who binds this address and who points at it, where either is worth saying (RK453).

    Silent on the ordinary row — a heading bound to the one line that claims it is the state
    every write produces, and repeating it on every address would bury the two that are not.
    What it names is exactly the two ways they come apart, and each is a different act: an
    unbound heading a line claims is `section amend --title` away from bound, and a bound
    heading nothing claims is prose whose task has left, which is the reader's to keep or
    delete. Retired addresses say nothing: there is no heading to have an opinion about.
    """
    # Three silences and not one (RK461). A retired address has no heading to have an
    # opinion about; the bound-and-claimed row is what every write produces; and a **memo**
    # — naming no task and claimed by none — is the state RK236 protects and nothing ever
    # closes. Reported beside the two that are actionable, that third one was five of the
    # five rows this project's audit printed, and a list whose majority is noise is what
    # teaches somebody to stop reading a report.
    if not one.live or one.memo:
        return ""
    if one.binds and one.claimed == (one.binds,):
        return ""
    if not one.binds:
        return f"  binds nobody, claimed by {', '.join(one.claimed)}"
    if not one.claimed:
        return f"  binds {one.binds}, which no open line claims"
    return f"  binds {one.binds}, claimed by {', '.join(one.claimed)}"


def _anchor_row(one: Anchor) -> dict[str, object]:
    return {
        "anchor": one.anchor,
        # Which file declared it, which is the whole of RK297 in one field: two rows with
        # one address are two headings, and unlabelled they read as a listing that repeated.
        "role": one.role,
        "live": one.live,
        "written_in": one.written_in or None,
        # The two facts RK453 adds, and they are two because they come apart in both
        # directions: a heading binding nobody that a line claims is RK452's write left
        # undone on an older corpus, and one binding a task no live line claims is prose
        # whose task has shipped. Null and `[]` on a retired address, which has no heading.
        "binds": one.binds or None,
        "claimed": list(one.claimed),
        "orphaned": one.orphaned,
        # The third state, told apart from the two that are (RK461): a memo is prose that was
        # never anybody's, so it is neither bound nor left behind, and a client filtering on
        # `orphaned` alone used to catch it.
        "memo": one.memo,
    }


def _families(found: Sequence[Anchor]) -> list[dict[str, object]]:
    """One row per top-level address, in numeral order (RK293), with the files it spans.

    The counts are the project's and so is ``next`` (RK297): a family declared in two prose
    files is one family, and a per-file count would be the number this read exists to stop
    somebody taking. ``files`` is what a row says once it spans two — named rather than
    summed away, because which file spent an address is what a reader checks it against.
    """
    out: dict[str, dict[str, object]] = {}
    for one in found:
        top = one.anchor.split(".")[0]
        row = out.setdefault(top, {"family": top, "live": 0, "retired": 0, "files": []})
        row["live" if one.live else "retired"] = int(row["live" if one.live else "retired"]) + 1
        if one.role not in row["files"]:  # type: ignore[operator]
            row["files"].append(one.role)  # type: ignore[attr-defined]
    for top, row in out.items():
        row["next"] = next_child(found, top)
    return list(out.values())


def _deps(config: Config, args: argparse.Namespace) -> int:
    try:
        backlog = Backlog.load(config)
    except (KeyError, OSError) as error:
        return _refused(error)  # a declared file that is not there yet: `init` (RK18)
    try:
        found = Dependencies.of(backlog, args.id)
    except KeyError:
        print(
            f"roadkeep: no open task {args.id} in {config.relative(config.path('roadmap'))}"
            + (" (it is in the changelog)" if args.id in backlog.shipped() else ""),
            file=sys.stderr,
        )
        return EXIT_USAGE

    if args.json:
        print(json.dumps(found.payload(), indent=2))
    else:
        print(found.stated())
    return EXIT_OK


def _origin(config: Config, args: argparse.Namespace) -> int:
    if args.id.startswith("§"):
        return _cited(config, args)
    try:
        origin = origin_of(config, args.id)
    except HistoryUnavailable as error:
        print(f"roadkeep: no history to resolve against ({error})", file=sys.stderr)
        return EXIT_USAGE

    if args.json:
        print(json.dumps({"id": origin.task_id, **_commits_json(origin)}, indent=2))
        return EXIT_OK

    if origin.proposed_in is None and origin.shipped_in is None:
        print(f"{args.id}: nothing in history mentions it yet")
        return EXIT_OK
    for label, commit in (("proposed", origin.proposed_in), ("shipped", origin.shipped_in)):
        if commit is None:
            print(f"  {label:<9} —")
            continue
        print(f"  {label:<9} {commit.short}  {commit.date[:10]}  {commit.subject}")
    if args.why and origin.shipped_in is not None:
        print()
        print(origin.shipped_in.reasoning)
    return EXIT_OK


def _cited(config: Config, args: argparse.Namespace) -> int:
    """Where the design behind a dangling citation went (RK212).

    `ship` names the sections left citing what it deleted (RK206), which serves the author
    at the moment of the write. This serves the reader who meets `§XVIII.12` a year later:
    the files hold no answer, because `as_ledger` keeps no pointer, so a citation of a
    shipped design and a typo read exactly alike.

    A question and not a check, decided by counting: 37 such references across this
    repository, claude-tray, Shio and Turing, of which 36 are in outline projects whose
    anchor carries no id at all. A finding would fail four files whose prose is correct;
    28 notes in one Turing report would be output nobody reads. So it costs nothing until
    somebody meets the reference and asks (L5).
    """
    anchor = args.id.lstrip("§")
    found = cited_origin(config, anchor)
    # Both registers off the record (RK1170), and the role spelled by this project (RK75): the
    # answer is `Cited`'s, and what the printed one needs beyond the fact is the file's name.
    where = config.relative(config.path(found.role)) if config.has(found.role) else found.role
    if args.json:
        print(json.dumps(found.payload(), indent=2))
    else:
        print(found.stated(where, why=args.why))
    return EXIT_OK


def _weight(config: Config, args: argparse.Namespace) -> int:
    """Print what comparable tasks cost (RK71). Numbers only — the judgement is the author's.

    No advice line: what a spread means for the line being written is an editorial call, and
    a tool that phrased it would be writing the reasoning it exists not to write (L4).

    Both registers come off one result (RK1170): this verb was the shape the task measured — the
    plain answer spelled here and its payload in `rendering.py`, one verb's two readings two files
    apart, with neither file holding both. `Weighed` is that result, beside the numbers it is
    derived from, and what is left here is the door: run it, and say which register was asked for.
    """
    try:
        weights = weigh(config, args.block)
    except HistoryUnavailable as error:
        print(f"roadkeep: no history to weigh against ({error})", file=sys.stderr)
        return EXIT_USAGE
    except (KeyError, OSError) as error:
        return _refused(error)

    answer = Weighed(
        where=config.relative(config.path("changelog")),
        weights=weights,
        records=args.records,
    )
    print(json.dumps(answer.payload(), indent=2) if args.json else answer)
    return EXIT_OK


def _remaining(config: Config, args: argparse.Namespace) -> int:
    """Run the query a task's own design declares, against this tree, now (RK492).

    A read in the strict sense: nothing is written, nothing is cached, and the exit code says
    the call was answered rather than what the answer was. A migration with sites left is not
    a failing gate — `lint` is what refuses — and a `remaining` that exited 1 while work was
    outstanding would be a verb nobody could put in a loop.
    """
    try:
        view = show(config, args.id)
    except (KeyError, OSError) as error:
        return _refused(error)
    if view.section is None:
        # The pointer's own failure, in the words `show` already composed for it: a task with
        # no design has no query, and which of the four absences it is matters to the repair.
        print(f"roadkeep: {args.id} has no section: {view.section_absence}", file=sys.stderr)
        return EXIT_USAGE
    try:
        clauses = declared(view.section.body)
    except QueryError as error:
        return _refused(error)
    if not clauses:
        # An answer and not a refusal: *this design declares no query* is a fact about the
        # task, and a read that refused it would be read as evidence the id was wrong. The
        # grammar is named, because the next thing a caller wants is to write one.
        if args.json:
            print(json.dumps({"id": args.id, "query": [], "total": None}, indent=2))
        else:
            print(
                f"{args.id} declares no query: a `roadkeep-remaining` fenced block in "
                f"§{view.entry.task.ref or args.id}, one `<pathspec> :: <regex>` per line"
            )
        return EXIT_OK
    found = count(config.root, args.id, clauses)
    print(json.dumps(found.payload(), indent=2) if args.json else str(found))
    return EXIT_OK


