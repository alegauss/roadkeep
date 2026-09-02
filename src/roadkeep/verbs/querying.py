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

from roadkeep import attesting, claiming

from roadkeep.backlog import Backlog, NotOpen, Stage, Standing, Whereabouts
from roadkeep.capturing import debt
from roadkeep.briefing import NothingToBrief, brief
from roadkeep.budgeting import (
    Load,
    Session,
    body_budget,
    budget,
    file_budget,
    notice_budget,
    non_goal_budget,
)
from roadkeep.config import Config, PROSE_ROLES
from roadkeep.counting import Census
from roadkeep.kernel.document import StaleFile, write_all
from roadkeep.exporting import DEFAULTS, project, spec, splice_into
from roadkeep.graph import Dependencies
from roadkeep.history import (
    Unclosed,
    pending,
    Addresses,
    HistoryUnavailable,
    cited_origin,
    families_of_block,
    Gapped,
    gaps,
    indexed,
    origin_of,
    status,
)
from roadkeep.picking import Claim, Picked, pick, take
from roadkeep.provenance import invocation
from roadkeep.remaining import EVIDENCE, QueryError, count, declared
from roadkeep.rendering import (
    CHARACTER_UNIT,
    _claim_event,
    _commits_json,
    _load_json,
    _nothing_json,
)
from roadkeep.serving import Prose, Withheld, detail, surface
from roadkeep.showing import show
from roadkeep.verbs.declaring import (
    _DESIGNED_HELP,
    _HAVE_COUNTING_HELP,
    _HAVE_HELP,
    _JSON_HELP,
    _PIPE,
    _counting_flags,
    _marker_flag,
    answers,
    narrows,
    withheld,
)
from roadkeep.verbs.reading import _body_reader, _one_body, _piped
from roadkeep.verbs.refusing import EXIT_GATE, EXIT_OK, EXIT_USAGE, REFUSALS, _refused
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


def _list_argv(args: argparse.Namespace) -> tuple[str, ...]:
    """The caller's own call, less `--block` — what a narrowing door is composed from (RK1476).

    Rebuilt from the parsed namespace and not from `sys.argv`, because this verb is reached
    over MCP too, where the argv the caller wrote is a JSON object and the command line was
    :func:`~roadkeep.serving.argv`'s. What that composes is a door for the transport in hand.
    """
    out = ["list"]
    if args.role != "roadmap":
        out += ["--role", args.role]
    if getattr(args, "marker", None):
        out += ["--marker", args.marker]
    if args.ids:
        out.append("--ids")
    return tuple(out)


def _list(config: Config, args: argparse.Namespace) -> int:
    try:
        census, standing = _census(config, args)
    except (KeyError, OSError) as error:
        return _refused(error)

    # Composed first and weighed after (RK1476), which is the shape of the problem: this verb
    # already had the whole answer in hand when the transport refused it, and the only thing
    # it could not do was decline to hand it over. Measured on what would be printed, so the
    # three forms of this listing are each held against their own width.
    if args.json:
        # `--have` where the caller passed one, and nothing where it did not (RK1442): the
        # payload's split is `stats`' own, so what a caller declares moves lines across here
        # exactly as it does there. The served tool takes no such flag and never will while
        # `[tools] session` is this close — the agent on that transport is the caller with no
        # hands, which is the population this split already assumes.
        have = getattr(args, "have", ())
        answer = json.dumps(census.listing(standing, have), indent=2)
        bound = census.bounded(
            answer, config.list_read, scoped=bool(args.block), argv=_list_argv(args)
        )
        if bound is None:
            print(answer)
            return EXIT_OK
        print(json.dumps(census.listing(standing, have, bound), indent=2))
        return EXIT_GATE

    listed = census.listed(args.ids)
    bound = census.bounded(
        listed, config.list_read, scoped=bool(args.block), argv=_list_argv(args)
    )
    if bound is not None:
        # Nothing on stdout, which is this verb's own rule about that stream (RK1170): a
        # consumer piping `--ids` gets the empty listing the exit code explains, and never
        # a sentence where the ids were.
        print(bound.stated(), file=sys.stderr)
        return EXIT_GATE
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
    # The capture debt is a second subject and joined here (RK1139): a capture is not a line
    # of the file this counts, so reading one inside the census would make a count of the
    # roadmap depend on a directory git ignores.
    owed = debt(config)
    if args.json:
        print(json.dumps(census.counts(config, standing, owed, args.have), indent=2))
    else:
        print(census.counted_out(config, owed, args.have))
        for note in census.silence(standing):
            print(note, file=sys.stderr)
    return EXIT_OK


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

    answer = claiming.Registry(
        rows=tuple(rows),
        dropped=tuple(dropped),
        pruned=bool(args.prune),
        registry=str(claiming.path(config.root)),
        window=config.held,
    )

    if args.json:
        print(json.dumps(answer.payload(), indent=2))
    else:
        print(answer.stated())
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
    # The subtraction is `claiming`'s (RK294), because `ship` asks for the same lists at the
    # moment of committing and two compositions of one answer is how they come to disagree.
    # Git is asked here and not there: this command was told to answer.
    # `accounted=wrote` (RK1117): here the word means what it always meant on this path — the
    # dirty governed files whose diff carries this id — and the subtraction it feeds is the
    # same one a departure makes, now made in one place rather than by each printer.
    #
    # And `shared` with it (RK1122): this is the read a commit is composed from, so the ids
    # inside a file it is about to stage are exactly what it exists to say. Asked here rather
    # than deep in the split for the same reason git is — this command was told to answer.
    answer = claiming.Claimed(
        task_id=args.id,
        scope=claiming.split(
            config,
            args.id,
            entries,
            seen.changed,
            indexed(config),
            accounted=wrote,
            shared=claiming.sharing(config, args.id, wrote),
            staged=seen.staged,
        ),
        wrote=tuple(wrote),
    )

    # Three registers and not two (RK1170): `--porcelain` is a third reading of one result and
    # not a narrowing of either — a shell consumes it, so it carries paths and nothing else.
    if args.porcelain:
        print(answer.porcelain())
    elif args.json:
        print(json.dumps(answer.payload(), indent=2))
    else:
        print(answer.stated())
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


def _brief(config: Config, args: argparse.Namespace) -> int:
    if args.id is not None and (args.block is not None or args.designed or args.have):
        # Two answers to one question: the id names a task and the others name a search.
        # `--have` joins them for the same reason and not a weaker one (RK1297): it narrows
        # what may be *chosen*, and a caller that named the line has already chosen — the
        # refusal it would otherwise want is `brief <id>`'s own, which this verb does not make.
        narrowed = (
            "--block"
            if args.block is not None
            else ("--designed" if args.designed else "--have")
        )
        print(
            f"roadkeep: give an id or {narrowed}, not both: an id is already the answer "
            f"{narrowed} would look for",
            file=sys.stderr,
        )
        return EXIT_USAGE
    try:
        gathered = brief(
            config, args.id, args.block, args.designed, args.claim, args.have
        )
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


def _cost(config: Config, args: argparse.Namespace) -> int:
    """What this project's surface already spends (RK1321).

    `_budget`'s dispatch for the other tense. The three subjects moved here whole — the same
    readers, the same registers — because what split was the *verb* and not any answer: eight
    subjects under one name made `budget` the largest served tool at 2,741, against a per-tool
    ceiling calibrated on `ship` at 2,466, so whichever arrived last was refused by a limit
    none of them was about.

    Which subject was asked for, and that exactly one was, is `answers` at this verb's own
    `add_parser` and `dispatch`'s to refuse (RK489) — so what is left here is the dispatch.
    """
    # `is not None` and not truth (RK1236): bare `--tools` is the empty string, the flag
    # taking a value, which is `--brief`'s reading one subject over.
    if args.tools is not None:
        return _tools_budget(config, args)
    if args.brief is not None:
        return _brief_budget(config, args)
    if args.session:
        return _session_budget(config, args)
    if args.skill:
        return _skill_budget(config, args)
    if args.deny:
        return _deny_budget(config, args)
    # No subject is the default here, unlike `budget`, whose bare form is about the line `add`
    # would write next. These are five cadences — once at connect, once per turn, once per
    # read, once per turn that loads the write path (RK1424) and once per refused write
    # (RK1428) — and privileging one would make the others look like narrowings of it.
    print(
        "roadkeep: cost takes a subject: --tools for the served surface, --brief for what "
        "that read costs a tool result, --session for both against their cadences, --skill "
        "for the write path on the turns that load it, --deny for one refused write",
        file=sys.stderr,
    )
    return EXIT_USAGE


def _budget(config: Config, args: argparse.Namespace) -> int:
    # Which of the three subjects was asked for, and whether `--role` or `--lead` came with
    # the one it narrows, are `answers` and `narrows` at this verb's own `add_parser` and
    # `dispatch`'s to refuse (RK489). What is left here is the dispatch itself.
    if args.anchor:
        return _body_budget(config, args)
    if args.non_goal:
        return _non_goal_budget(config, args)
    if args.file is not None:
        return _file_budget(config, args)
    clash = _one_body("--body", args.body, args.body_file)
    if clash is not None:
        print(f"roadkeep: {clash}", file=sys.stderr)
        return EXIT_USAGE
    try:
        answer = budget(
            config,
            args.id,
            block=args.block,
            deps=args.deps,
            # The second group the line carries (RK1461), and the one `add` adds 21 characters
            # of structure for while this read priced the sentence as if it would not.
            requires=args.requires,
            status=args.status,
            symptom=args.symptom,
            family=args.family,
            ref=args.ref,
            # Read here and not in `budgeting`, which touches no stream: the pipe is this
            # surface's affordance and the module measures whatever it is handed (RK1190).
            why=_piped(args.why),
            # And the other half of the same transaction (RK1224): `add --section` writes a
            # line and a body together, so pricing them in two calls made the retry for a
            # three-character overflow carry the whole paragraph again.
            body=(
                None
                if args.body is None and args.body_file is None
                else _body_reader(args.body, args.body_file)()
            ),
            # The third write off the same line (RK1305). `is not None` and not truth, which is
            # `--tools`' reading: bare `--retire` is the empty string and means abandoned.
            retire=args.retire,
            # The fourth (RK1458), and a flag rather than a value: a ship writes no prefix into
            # the field, so there is nothing about the departure to name here.
            ship=args.ship,
            # And the fifth (RK1479), the subject RK1458 named and left: a pause's reason is
            # wrapped around prose the store carries forward, which `Budget.carried` is.
            defer=args.defer,
        )
    except REFUSALS as error:
        return _refused(error)

    # Both registers off the record (RK1170): `Budget` already was the result this verb computed,
    # and its two readings were a printer here and a builder in `rendering.py` — one answer in two
    # files, with neither holding both.
    print(json.dumps(answer.payload(), indent=2) if args.json else answer)
    # Both halves of the transaction decide it (RK1224): a body three words over is a call the
    # `add` refuses whole, so an exit that spoke only for the line would answer a question
    # narrower than the one the caller asked.
    return _verdict(
        any(share.over for share in answer.shares if share.drafted)
        or bool(answer.section is not None and answer.section.over)
    )


def _verdict(over: bool) -> int:
    """Exit 1 where a draft this call was handed does not fit (RK1190).

    `EXIT_GATE`, and it is that code's own meaning: the write this read stands in for would have
    refused, and a caller asking *will this fit* should not have to parse prose for the one bit
    it asked for. Over MCP the same code becomes `isError`, which is what makes the answer usable
    by the agent this whole read exists for.

    **Only about a draft**, which is the narrowing that keeps this a read. A line the roadmap
    already holds over its allowance is a `lint` finding and the gate's business; reporting it
    here as a failure would make `budget <id>` exit non-zero over a file it was only asked to
    describe, and make one verb answer for two different questions with one code.
    """
    return EXIT_GATE if over else EXIT_OK


def _body_budget(config: Config, args: argparse.Namespace) -> int:
    """What a section body may say, before it is written — and what a draft of it costs.

    The draft is read the way every writing verb reads one (RK381, RK329): a literal, a path,
    or the pipe that `-` names. Unlike those verbs it is **optional here**, so an omitted
    `--body` reads nothing at all rather than blocking on a stream nobody opened — the whole
    subject of this call is a limit, which is answerable with no prose in hand (RK1190).
    """
    clash = _one_body("--body", args.body, args.body_file)
    if clash is not None:
        print(f"roadkeep: {clash}", file=sys.stderr)
        return EXIT_USAGE
    try:
        # Inside the try for `section add`'s reason: prose that is not UTF-8 raises
        # UnicodeDecodeError, which is a ValueError and is refused with the same code.
        draft = (
            None
            if args.body is None and args.body_file is None
            else _body_reader(args.body, args.body_file)()
        )
        answer = body_budget(config, args.anchor, args.role, draft)
    except REFUSALS as error:
        return _refused(error)
    if args.json:
        print(json.dumps({"subject": "section", **answer.payload()}, indent=2))
        return _verdict(bool(answer.over))
    state = "written" if answer.written else "the section add would write"
    print(f"§{answer.anchor}  {answer.role}  ({state})")
    print(f"  body       {answer.stated(named=False)}")
    return _verdict(bool(answer.over))


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
        if load.characters is not None:
            # The figure the author is actually deciding against (RK1250), on the read RK345
            # built for the moment before an edit — `--session` has had it since RK1245 and
            # this one, the more likely to be open, threw it away.
            #
            # A **row** and not a clause on a cost, which is RK258's line kept rather than
            # crossed: that task refused a word figure *beside a declared unit*, because
            # `[budgets]` is stated in what the loader pays and an aim next to it would be a
            # number this project never wrote. This is not next to one and is not an aim — it
            # is a reading, and its clause says outright that nothing limits it.
            #
            # **Last, and under the breakdown** (RK1252). Printed between the limits and the
            # sections, it was the total a reader met immediately before a list ranked in
            # another unit — so the adjacency said *this is what those are of*, which it is
            # not. The breakdown belongs to the ceiling above it; this belongs to neither.
            print(
                f"  {'reader':<11}{load.characters} utf-16-code-units, what a model is "
                f"charged — a reading, and nothing here limits it"
            )
    return EXIT_OK


#: How many sections the terminal names, for `_LARGEST_TOOLS`' reason: the largest few are
#: where the size went, and a caller reading a report to decide what to cut wants those.
_LARGEST_PARTS = 4


def _print_parts(load: Load) -> None:
    """Where the size is, so the next compression is aimed (RK1092).

    The read `cost --tools` makes about the served surface, one file over: a total says an
    edit will be refused and says nothing about what to take out, and `agents.md` reaching
    eight bytes of room turned *compress the prose* into a preference nothing had re-measured.

    Only where the file is on disk and holds more than one section, because a single-section
    file's breakdown is the total printed twice.

    **Ranked by the limit about to refuse** (RK1252), which is :attr:`Load.ranked`'s decision
    and not this renderer's: a file at 104 of 125 lines and 6906 of 8400 bytes is a line
    problem, and a list ordered by bytes names a section that is not the one to cut. The
    ranking unit leads the row, so the column a reader sorts on is the column they scan.
    """
    if len(load.parts) < 2:
        return
    unit = "bytes" if load.tightest is None else load.tightest.unit
    other = "bytes" if unit == "lines" else "lines"
    ranked = load.ranked
    # Three figures need a header, where two did not (RK1253): the leading column varies with
    # the ceiling and the third is a reading rather than a limit, so a row of bare numbers no
    # longer says which is which. Named in the order they are printed, ranking unit first.
    reading = "  reader" if ranked[0].characters is not None else ""
    print(f"    {unit:>6}  {other:>6}{reading}")
    for part in ranked[:_LARGEST_PARTS]:
        first, second = (part.lines, part.bytes) if unit == "lines" else (part.bytes, part.lines)
        # Both declared columns at one width, because which of them leads now varies: a `>3`
        # sized for lines misaligns the byte figure it may now hold.
        said = f"    {first:>6}  {second:>6}"
        if part.characters is not None:
            said += f"  {part.characters:>6}"
        print(f"{said}  {part.heading or '(before the first ##)'}")
    if len(ranked) > _LARGEST_PARTS:
        print(f"    … and {len(ranked) - _LARGEST_PARTS} more — `--json` lists every one")


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
    # The line `Budget.__str__` prints for the same reason (RK1366): `non-goal amend --why`
    # replaces that argument, so each remainder below is the whole limit and a reader given
    # `37 written, 200 left` against 200 otherwise reads the two as adding up.
    if any(share.replaced and share.taken for share in shares):
        print(
            "  replacing  what is written below, so each remainder is the whole limit and "
            "not what is left beside it — an amend rewrites the field"
        )
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
    resident, limit = notice_budget(config)
    answer = Session(
        once=sent.characters,
        tools=len(sent.tools),
        # The records themselves (RK1248): both readings of one file (RK1245) plus the room
        # its own `[budgets]` line declares, all of which `Load` already holds.
        resident=file_budget(config) if config.budgets else (),
        # The third thing a session pays for (RK1243), and the one that had a ceiling nobody
        # could ask about — measured off `announce`, so it is the line this project's sessions
        # actually get rather than a second estimate of it.
        # What the checkout contributes, named apart from what the surface does (RK1334): a
        # session really is sent it, so it stays inside `once`, and no author can edit it, so
        # the ceiling is not about it.
        provenance=sent.provenance,
        notice=resident,
        notice_limit=limit,
        # The ceiling `budget.session` refuses this total against, which is the single one
        # there is (RK1333): read off the config here rather than recomputed, so the row and
        # the gate cannot come apart the way the row and the notice's ceiling already had.
        once_limit=config.tool_session,
    )

    if args.json:
        print(json.dumps(answer.payload(CHARACTER_UNIT), indent=2))
    else:
        print(answer.stated(CHARACTER_UNIT))
    return EXIT_OK


def _skill_budget(config: Config, args: argparse.Namespace) -> int:
    """What the write path costs the turns that load it (RK1424).

    The fourth cadence and the one nothing counted. `[budgets]` prices what loads on *every*
    turn and excludes the skill on purpose — pricing a trigger-loaded file as resident is the
    third figure `_session_budget` exists to avoid inventing (RK23) — which settles the table
    it is not in and never said the number was not worth having. Measured when this was
    filed: 65,180 code units, against a served schema of 64,258 with a ceiling of 64,300.

    Beside the served figure and never added to it, which is `--session`'s own rule about two
    cadences: the schema is sent once at the handshake and this is paid per triggered turn, so
    a sum is wrong for every session whose count of those is not one.

    **And no ceiling.** `govern` refuses a limit this corpus already breaks, so declaring one
    would be a number chosen before the reading that decides it. This is that reading, and it
    reports the way `weight` and `adopt` do: the figure, where it went, and the judgement left
    with whoever takes it.
    """
    from roadkeep.budgeting import skill_cost  # noqa: PLC0415 - RK260

    # One measurement and two readers (RK1096), as `--session` totals what `--tools` ranks:
    # the comparison is the whole point of the number, so it comes off the same reader rather
    # than from a second walk that could disagree with it.
    schema = surface(config).characters
    found = skill_cost(config)
    if args.json:
        print(json.dumps(found.payload(CHARACTER_UNIT, schema), indent=2))
    else:
        print(found.stated(CHARACTER_UNIT, schema))
    return EXIT_OK


def _deny_budget(config: Config, args: argparse.Namespace) -> int:
    """What one refused write costs the session that meets it (RK1428).

    The fifth cadence. `guarding.py` hands a session two texts and only the small one was
    measured — the session-start notice is held to a ceiling and printed beside it by
    `--session`, while the denial, thirteen times larger here, was priced by nothing. It is
    also the one paid per denial, by a plugin whose whole purpose is to produce them.

    Composed from a real `Refusal` and never from a fixture, which is `notice_budget`'s rule
    one message over: a door reworded in `guarding.py` moves this figure or it is measuring
    something else.

    **And no ceiling**, for `--skill`'s reason: `govern` refuses a limit this corpus already
    breaks, so declaring one would be a number picked before the reading that decides it.
    """
    from roadkeep.budgeting import deny_cost  # noqa: PLC0415 - RK260

    found = deny_cost(config)
    if args.json:
        print(json.dumps(found.payload(CHARACTER_UNIT), indent=2))
    else:
        print(found.stated(CHARACTER_UNIT))
    return EXIT_OK


def _brief_budget(config: Config, args: argparse.Namespace) -> int:
    """What a brief costs a tool result, per open line or for the one named (RK1286).

    The sixth subject, and the one about a **read** rather than about prose or a file. Every
    resident file has a budget and the served surface has two, on RK30's argument that a limit
    nobody counts is a limit that moves — and the read this project recommends over reading
    the file had none, while growing four arithmetic rows in one session.
    """
    from roadkeep.budgeting import brief_budget  # noqa: PLC0415 - RK260

    try:
        found = brief_budget(config, args.brief or None)
    except (KeyError, OSError) as error:
        return _refused(error)

    if args.json:
        print(
            json.dumps(
                {
                    "unit": CHARACTER_UNIT,
                    "limit": found.limit,
                    "briefs": [
                        {"id": one.id, "characters": one.characters, "over": one.over(found.limit)}
                        for one in found.briefs
                    ],
                    # What the ranking could not measure (RK1288), which is the fact the
                    # widest is wrong without: `[]` is an answer and never an absence.
                    "unpriced": [
                        {"id": one.id, "because": one.because} for one in found.unpriced
                    ],
                    # Carried and never reconstructed (RK1289): priced, refused and not asked
                    # for are three numbers that add up to this one.
                    "elided": found.elided,
                    "open_lines": found.open_lines,
                },
                indent=2,
            )
        )
        return EXIT_OK
    # Both, because a ranking that is empty and a ranking whose every line refused are two
    # answers (RK1288): the second has everything to report and nothing in the first column.
    if not (found.briefs or found.unpriced):
        print(
            f"roadkeep: no open line to brief, so there is nothing to price — "
            f"`{invocation()} list` says what the backlog holds"
        )
        return EXIT_OK
    # The verdict says what it was taken over (RK1292). `0 over` beside a listing that names
    # a line nobody could measure is a claim the ranking is not entitled to: the widest is
    # the bound, and an unmeasured line is the shape most likely to be it. The gate has no
    # such problem — there the absence is its own finding and the exit code is 1 either way —
    # and here one string carried both the count and the confidence. Silent where nothing
    # went unmeasured, which keeps the ordinary answer exactly as short as it was.
    qualified = f", {len(found.unpriced)} unpriced" if found.unpriced else ""
    ceiling = (
        "no [reads] brief — this project declares no ceiling for the read that replaces "
        "reading the file"
        if found.limit is None
        else f"{found.limit} allowed, {len(found.over)} over{qualified}"
    )
    rows = [f"{len(found.briefs)} brief(s), widest first, in {CHARACTER_UNIT}: {ceiling}"]
    for one in found.briefs:
        room = "" if found.limit is None else f"  {found.limit - one.characters:+d}"
        rows.append(f"  {one.id:<10} {one.characters}{room}")
    # Named under the ranking (RK1288): a line the read could not compose is the one most
    # likely to have been the widest, so the top of the rest is not the answer while it is
    # unaccounted for — and what refused it is the tool's own sentence, not one composed here.
    rows += [f"  {one.id:<10} unpriced — {one.because}" for one in found.unpriced]
    print("\n".join(rows))
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
    if args.tools:
        # Named, so the question is which of *this* tool's fields spent the bytes (RK1236) —
        # the one the ranking below cannot answer, and the one a caller has the moment `lint`
        # names a tool that is over.
        try:
            one = detail(config, args.tools)
        except Withheld as withheld:
            # The one refusal here with a remedy (RK1360): the tool exists and this project is
            # not sent it, so the answer is the `declare` that changes that and never the
            # ranking, which is a list this verb is correctly absent from.
            print(f"roadkeep: refused: {withheld}", file=sys.stderr)
            return EXIT_USAGE
        except KeyError:
            print(
                f"roadkeep: refused: {args.tools!r} is not a tool this project serves — "
                f"`{invocation()} cost --tools` ranks every one, and `--json` lists them",
                file=sys.stderr,
            )
            return EXIT_USAGE
        if args.json:
            print(json.dumps(one.payload(CHARACTER_UNIT, config.tool_characters), indent=2))
        else:
            print(one.stated(CHARACTER_UNIT, config.tool_characters))
        return EXIT_OK

    # The same measurement `--session` totals (RK1096), so the ranking and the total cannot
    # come to disagree about what a client is sent.
    sent = surface(config)

    if args.json:
        print(json.dumps(sent.payload(CHARACTER_UNIT, config.tool_characters, config.tool_session), indent=2))
    else:
        print(sent.stated(
            CHARACTER_UNIT, config.tool_characters, _LARGEST_TOOLS, config.tool_session
        ))
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
            claim = take(config, args.block, args.designed, available=args.have)
            choice = claim.choice
        else:
            choice = pick(config, args.block, args.designed, available=args.have)
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
    # One task as a document, which is a different subject and not a fourth destination
    # (RK1362): the backlog projection answers about every line and this answers about one,
    # so composing them would be two documents spliced into one file.
    if args.spec is not None:
        try:
            print(spec(config, args.spec).markdown(), end="")
        except (KeyError, ValueError) as error:
            return _refused(error)
        return EXIT_OK
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


def _govern(config: Config, args: argparse.Namespace) -> int:
    """A governed number, read and then declared in the same call (RK1272).

    The read alone where no value is passed, which is the half that already existed under four
    other verbs and nowhere near the declaration. Writes and so is not `reads_only`.
    """
    from roadkeep.governing import govern, reading  # noqa: PLC0415 - RK260

    try:
        if args.at is None:
            found = reading(config, args.key, file=args.file or "", role=args.role or "")
            print(json.dumps(_reading_json(found), indent=2) if args.json else found.stated())
            return EXIT_OK
        written = govern(
            config,
            args.key,
            args.at,
            file=args.file or "",
            role=args.role or "",
            because=args.because or "",
            instead=args.instead or "",
        )
    except REFUSALS as error:
        return _refused(error)

    if args.json:
        print(json.dumps(written.payload(config), indent=2))
    else:
        print(written.stated(config))
    return EXIT_OK


def _reading_json(found) -> dict:
    """The measurement alone, shaped as the write's own `reading` block is (RK1272)."""
    return {
        "address": found.address,
        "unit": found.unit,
        "sites": found.sites,
        "worst": found.worst,
        "where": found.where,
        "declared": found.declared,
        # Beside it in both registers (RK1343): a consumer reading `declared: null` cannot
        # tell a key this build falls back on from one nothing holds, and the two are the
        # difference between a lenient gate and no gate.
        "default": found.default,
        "unmeasured": found.unmeasured or None,
        "because": list(found.because),
    }


def _config_shape(config: Config, args: argparse.Namespace) -> int:
    """What `roadkeep.toml` may declare, and what this project did (RK1270).

    Never refused over the project's *state* — a tree with no config at all is answered, that
    being the caller who most needs the list — and refused over the **argument**, a table name
    this build does not have being a typo rather than a table somebody has yet to declare.
    """
    from roadkeep.describing import payload, shape, stated  # noqa: PLC0415 - RK260

    try:
        # Straight through, and the default is `None` rather than `""` for exactly one
        # reason: the top level's own name *is* the empty string, so a default of `""` would
        # make `--table ""` unaskable — the one table a reader starts from.
        found = shape(config, args.table)
    except KeyError as error:
        return _refused(error)

    if args.json:
        print(json.dumps(payload(found), indent=2))
    else:
        print(stated(found))
    return EXIT_OK


def _commands(config: Config, args: argparse.Namespace) -> int:
    """What this build's command line takes, as data rather than as terminal text (RK1401).

    `_config_shape`'s twin, and refused the same way: never over the project's *state* — a
    tree with no config at all is answered, that being the reader deciding whether to adopt —
    and refused over the **argument**, a verb this build does not have being a typo rather
    than one somebody has yet to install.
    """
    from roadkeep.commanding import commands, payload, stated  # noqa: PLC0415 - RK260

    try:
        found = commands(config, args.command)
    except KeyError as error:
        return _refused(error)

    if args.json:
        print(json.dumps(payload(found), indent=2))
    else:
        print(stated(found))
    return EXIT_OK


def _anchors(config: Config, args: argparse.Namespace) -> int:
    """Live and retired addresses across this project's prose (RK247, RK297).

    Four readings off one record (RK1170) — the wide report and its payload, and the free
    address alone in each register. What stays here is the three **argv** refusals: which
    prose file, which of two narrowings, and a block whose lines point nowhere. Those are
    about the call and not about the answer, which is why they never reached the record.
    """
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
    # is written nowhere and used to be globbed out of the pointers by hand.
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
        if len(spans) == 1:
            args.family = spans[0]

    found = Addresses.of(
        config, role, args.family or "", [role] if role else asked, block, spans
    )
    if args.only_next:
        if args.json:
            print(json.dumps(found.free_payload(), indent=2))
            return EXIT_OK
        out, notes = found.freely()
        if not out:
            # The one refusal the narrow read has of its own: an empty stdout here reads as a
            # command that failed quietly, and this form exists to be captured.
            #
            # **Both spellings, because the first address chooses the system** (RK1211). This
            # named `I.1` by hand, on the one file with no family to read a system off — which
            # is exactly why `next_family` answers None here at all. So one half of the command
            # declined to guess and the other half guessed, and following the guess made the
            # file this tool then cannot read: measured on a project holding `1` and `1.1`,
            # offered `I.1`, which took its top levels to `1` and `I` — two systems tying at 1,
            # RK1210's nondeterminism, entered through a message that never mentions it.
            #
            # Naming both is what shows the choice exists. Naming one keeps a decision that is
            # the author's (L4, L6): a project outlining `1`, `2`, `3` is as ordinary as one
            # outlining `I`, `II`, `III`, and every address after the first is spelled the way
            # the first one was.
            print(
                "roadkeep: no outline family exists yet, so none is spent — the first "
                "address decides the system every address after it is spelled in, and that "
                "is yours: `add --ref I.1` or `add --ref 1.1`, whichever this project "
                "numbers in",
                file=sys.stderr,
            )
            return EXIT_USAGE
        print(chr(10).join(out))
        for note in notes:
            print(note, file=sys.stderr)
        return EXIT_OK

    if args.json:
        print(json.dumps(found.payload(config, args.claims, args.retired), indent=2))
    else:
        # RK1466. The retired half is what grows — one address per shipped task, pruned by
        # nothing — so the wide listing on a project with no families carries the live ones
        # and names the flag that prints the rest.
        print(found.stated(config, args.claims, args.retired))
    return EXIT_OK


def _deps(config: Config, args: argparse.Namespace) -> int:
    try:
        backlog = Backlog.load(config)
    except (KeyError, OSError) as error:
        return _refused(error)  # a declared file that is not there yet: `init` (RK18)
    try:
        found = Dependencies.of(backlog, args.id)
    except KeyError:
        # The shared refusal and no longer a second spelling of it (RK1342). `NotOpen` says
        # of itself that *the sentence has one spelling for every caller that asks*, and
        # answers three ways — in the changelog, paused with the store's own sentence and the
        # `resume` that undoes it, or nothing carries the id. This site hand-rolled two of
        # them, so the pause RK1213 taught that class to name was the one case it could not:
        # a sentence with two writers agrees until one of them grows a case.
        return _refused(
            NotOpen(
                args.id,
                config.relative(config.path("roadmap")),
                Whereabouts.of(config, args.id),
            )
        )

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



def _unclosed(config: Config, args: argparse.Namespace) -> int:
    """Open lines the history already speaks for (RK1201). Nothing here fails, so exit 0.

    Both registers come off one record (RK1170), and the exit code is not one of them: a
    commit naming an id is not evidence the work is done, so a non-zero here would fail every
    session that is mid-task — which is the shape a report must not take.
    """
    try:
        answer = Unclosed(rows=pending(config))
    except (KeyError, OSError) as error:
        return _refused(error)

    if args.json:
        print(json.dumps(answer.payload(), indent=2))
    else:
        print(answer.stated())
    return EXIT_OK



def _evidence(config: Config, args: argparse.Namespace) -> int:
    """What a task's own design says would prove it done, counted now (RK1184).

    `remaining` with the sign flipped, and the same read: sites that must **exist** rather
    than sites still there. Never a verdict — the pattern is the author's claim and the count
    is the answer, so `0` says the evidence is not there yet and whether that is the work
    being done is the caller's judgement (L4).

    The exit code says the call was answered and never what the answer was, for `remaining`'s
    reason: a criterion unmet is work outstanding, which is not a failing gate.
    """
    try:
        view = show(config, args.id)
    except (KeyError, OSError) as error:
        return _refused(error)
    if view.section is None:
        print(f"roadkeep: {args.id} has no section: {view.section_absence}", file=sys.stderr)
        return EXIT_USAGE
    try:
        clauses = declared(view.section.body, EVIDENCE)
    except QueryError as error:
        return _refused(error)
    if not clauses:
        # An answer and not a refusal, exactly as `remaining` reads an absent query: *this
        # design declares no criterion* is a fact about the task, and the grammar is named
        # because writing one is the next thing a caller wants.
        if args.json:
            print(json.dumps({"id": args.id, "kind": EVIDENCE, "query": [], "total": None}, indent=2))
        else:
            print(
                f"{args.id} declares no criterion: a `{EVIDENCE}` fenced block in "
                f"§{view.entry.task.ref or args.id}, one `<pathspec> :: <regex>` per line"
            )
        return EXIT_OK
    found = count(config.root, args.id, clauses, EVIDENCE)
    print(json.dumps(found.payload(), indent=2) if args.json else str(found))
    return EXIT_OK


def declare_reads(subcommands: argparse._SubParsersAction) -> None:
    """This module's verbs, declared where their handlers are (RK1171).

    `build_parser` called forty-nine blocks like these in a row; what it calls now is an index
    over the modules that own them. The move is what RK1169 and RK1170 bought: the flags a verb
    declares, the reasons it withholds and the record it answers with are one file's, so a
    change to any of them is one file's too.

    The order inside is `build_parser`'s own, which is where these blocks sat.
    """
    list_parser = subcommands.add_parser(
        "list",
        help="the task lines, filtered, printed verbatim",
        description=(
            "Print the lines a filter selects, exactly as the file spells them. A "
            "marker-bearing line the grammar did not accept is reported on stderr with "
            "the count, so a filtered listing can never look complete when it is not. "
            "`block list` names the labels this takes and cannot enumerate. Where the "
            "project declares `[reads] list`, a listing past it comes back as its blocks "
            "and counts with the narrowing that fits, not one this transport refuses."
        ),
    )
    _counting_flags(list_parser)
    _marker_flag(list_parser, "only this status marker", dest="marker")
    list_parser.add_argument(
        "--ids", action="store_true", help="print ids alone, one per line"
    )
    # The same flag `stats` takes, because the payload now carries that verb's split (RK1442)
    # and a number a caller cannot move lines across is the half-answer this axis exists to
    # avoid. It changes no printed line: stdout here is what the file says, verbatim.
    list_parser.add_argument(
        "--have",
        action="append",
        default=[],
        metavar="REQUIREMENT",
        help=_HAVE_COUNTING_HELP,
    )
    withheld(
        list_parser,
        ids='how a terminal prints: the payload carries every id in `tasks`, so a caller over this transport already has what the flag composes',
        have='the caller on this transport is the one with no hands, which is what the split already assumes — and the flag `brief` and `pick` expose costs the connect budget a read that answers without it does not',
    )
    # `verdict=True` for `lint`'s reason (RK1421): the one non-zero exit this verb has is the
    # answer *your listing is past `[reads] list`, and here is its shape* — a bound this verb
    # applies to itself, not a fall, so offering to file a defect about it would be a regress.
    list_parser.set_defaults(handler=_list, reads_only=True, verdict=True)
    # Two output *forms* of one read are two answers, exactly as `budget`'s subjects are
    # (RK465's rule, RK467's find): the payload came back whole with nothing said about the
    # flag that shaped nothing.
    answers(list_parser, ("ids", "the listing as bare ids"), ("json", "the payload"))

    stats_parser = subcommands.add_parser(
        "stats",
        help="counts per block and per marker, with what was not counted",
        description=(
            "Count the file. Every count carries the number of marker-bearing lines it "
            "could *not* read, printed even when it is zero: a grep reports the "
            "remainder with no indication that anything is missing. Where the project "
            "declares `[requirements]`, the open count is split into what nothing absent "
            "is holding up and what the rest are waiting for."
        ),
    )
    _counting_flags(stats_parser)
    stats_parser.add_argument(
        "--have",
        action="append",
        default=[],
        metavar="REQUIREMENT",
        help=_HAVE_COUNTING_HELP,
    )
    stats_parser.set_defaults(handler=_stats, reads_only=True)

    audit_parser = subcommands.add_parser(
        "audit",
        help="every marker-bearing line the count did not count, and why",
        description=(
            "Print the misses. This is what makes a count trustable rather than an "
            "extra: exit stays 0, because reporting is not the gate (`lint`, RK14) — "
            "an audit that failed a build would be a gate nobody could adopt first."
        ),
    )
    _counting_flags(audit_parser)
    audit_parser.set_defaults(handler=_audit, reads_only=True)

    claims_parser = subcommands.add_parser(
        "claims",
        help="which lines a worker is holding, oldest first, and where that is recorded",
        description=(
            "List the claim registry against the roadmap: held, expired — stepped over, so "
            "the line is offered again — or stale, meaning the marker moved and nothing "
            "reads the entry. Ranks nothing and offers nothing: `pick` decides what to work "
            "on, and the release is a marker."
        ),
    )
    claims_parser.add_argument(
        "--prune",
        action="store_true",
        help=(
            "drop the rows that are not claims and keep the ones that are, which is the "
            "reconciliation a marker write performs and the only other remedy is the file"
        ),
    )
    claims_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    # A read that can write, so it declares which flag makes it one (RK167): `dispatch` keeps
    # deciding the lock, and reading the registry never waits on one.
    withheld(
        claims_parser,
        prune='it writes the registry, exactly as `lint --fix` writes the files (RK16)',
    )
    claims_parser.set_defaults(handler=_claims, reads_only=True, writes_when="prune")

    claim_parser = subcommands.add_parser(
        "claim",
        help="the paths one held line's commit owns, declared once and answered on demand",
        description=(
            "Say which paths this task will touch, and read them back at the moment of "
            "committing. Without --path it answers what was declared, plus what the tree "
            "holds that another live claim says is its own — the analysis `git add -A` "
            "cannot make. Declared verbatim: nothing here reads the disk or the task's "
            "prose to guess a path, and nothing here dates a claim."
        ),
    )
    claim_parser.add_argument("id", help="the task id, which a live claim must already hold")
    claim_parser.add_argument(
        "--path",
        action="append",
        default=[],
        metavar="PATH",
        help=(
            "a path this task's commit owns, repeatable; replaces the whole scope, so a "
            "correction is one call and not a file to edit"
        ),
    )
    claim_parser.add_argument(
        "--add-path",
        action="append",
        default=[],
        metavar="PATH",
        dest="add_path",
        help=(
            "a path this task's commit *also* owns, repeatable; keeps what was declared, so "
            "a file the work turned up is one argument and not the whole scope again"
        ),
    )
    claim_parser.add_argument(
        "--porcelain",
        action="store_true",
        help="the paths alone, one per line — what a commit script feeds to `git add --`",
    )
    claim_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    # A read that can write, declared the way `claims --prune` declares it (RK167) — and by
    # two arguments (RK307), because either of them is the write.
    withheld(
        claim_parser,
        porcelain='how a terminal prints, for a caller that is already reading JSON',
    )
    claim_parser.set_defaults(
        handler=_claim,
        reads_only=True,
        writes_when=("path", "add_path"),
        # The second pair, found by the read RK339 asked for: same one-edit distance, same
        # asymmetry, and the same verb typed wanting the listing.
        twin=(
            "claim reads one line's scope back and needs it: `claim <id>`, or "
            "`claim <id> --path …` to declare what this commit owns. The registry "
            "listing is `claims`, which needs no id"
        ),
    )
    # The sixth pair, and the first one the *declaration* found rather than a sweep (RK489):
    # `--porcelain` returned before `--json` was read, so a caller asking for the payload got
    # the paths, byte for byte. RK467's sweep could never see it — it runs against a fixture
    # with no live claim, where every `claim` pair exits 2 for want of one — which is the
    # limit of finding a class by probing, one probe away from the class being declarable.
    answers(
        claim_parser,
        ("porcelain", "the paths alone, for `git add --`"),
        ("json", "the payload"),
    )

    writes_parser = subcommands.add_parser(
        "writes",
        help="which governed files a verb wrote, which nothing did, and where that is recorded",
        description=(
            "Read the write record against the files: attested — the bytes a verb left — "
            "unattested, meaning something else produced them, or unrecorded, meaning no "
            "verb has run here yet. Moves no baseline, so asking twice answers twice; the "
            "`Stop` hook states it once and consumes it (RK175)."
        ),
    )
    writes_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    # Never a write, not even behind a flag: re-baselining is what the `Stop` block does, and a
    # query offering it would be the laundering `dispatch` refuses queries in the first place.
    writes_parser.set_defaults(handler=_writes, reads_only=True)

    unclosed_parser = subcommands.add_parser(
        "unclosed",
        help="open lines whose work the history already names, and what closes each",
        description=(
            "Which open lines already have commits naming them, and no ledger entry. A "
            "session that shipped the code and forgot the line leaves a state `gaps` "
            "cannot see — that verb explains an id in neither file, and this one is in "
            "the roadmap — and `origin` answers one id at a time, so it is a confirmation "
            "and never a discovery. The commit that *filed* each id is dropped: `add` "
            "mints the id, so nothing could name one before the line existed. A report "
            "and never a gate: work under way is exactly this shape, and what a partial "
            "landing wants is `ship --part`."
        ),
    )
    unclosed_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    unclosed_parser.set_defaults(handler=_unclosed, reads_only=True)

    brief_parser = subcommands.add_parser(
        "brief",
        help="everything it costs to start one task, in one call",
        description=(
            "Compose the line, its rationale, its resolved deps, the blocker chain, what "
            "shipping it unblocks and the non-goals that bind it. With no id, briefs "
            "whatever `pick` would choose, which makes the first call the only one."
        ),
    )
    brief_parser.add_argument(
        "id", nargs="?", help="the task; omitted, `pick` chooses it"
    )
    brief_parser.add_argument(
        "--block", help="scope the pick to one block, e.g. C (only without an id)"
    )
    brief_parser.add_argument(
        "--designed",
        action="store_true",
        help=_DESIGNED_HELP,
    )
    brief_parser.add_argument(
        "--have",
        action="append",
        default=[],
        metavar="REQUIREMENT",
        help=_HAVE_HELP,
    )
    brief_parser.add_argument(
        "--claim",
        action="store_true",
        help=(
            "take the line as well as describing it: the marker moves to in-progress in the "
            "same transaction, and a named id another worker holds is refused"
        ),
    )
    brief_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    withheld(
        brief_parser,
        claim='it writes, and a read that writes is a read a caller stops making freely (L5) — so the writing door is a tool of its own with its own hint',
    )
    brief_parser.set_defaults(handler=_brief, reads_only=True, writes_when="claim")

    budget_parser = subcommands.add_parser(
        "budget",
        help="how many characters a line has left for prose, before one is written",
        description=(
            "Report what a line leaves its prose fields, derived from the id, the marker, "
            "the deps and the pointer — all known before the first word. The drafts "
            "(--symptom, --why, --body) are measured, never composed, and exit 1 when "
            "over: the refusal, without the write."
        ),
    )
    budget_parser.add_argument(
        "id",
        nargs="?",
        help="an existing line, e.g. RK12 — omitted, the line `add` would write next",
    )
    budget_parser.add_argument(
        "--block", default="", help="the block the line would be filed under, e.g. B"
    )
    budget_parser.add_argument(
        "--dep",
        action="append",
        default=[],
        dest="deps",
        metavar="DEP",
        help="a dep the line would carry, repeatable: the group is what moves the number",
    )
    # RK1461. The other group the write adds and this read could not be told about: 21
    # characters for `(requires: upstream) `, on the lines whose sentence is longest because
    # it has to say what is missing as well as what is wrong. Repeatable for `--dep`'s reason
    # — two of them cost two words and a separator, and one flag would mis-price the rest.
    budget_parser.add_argument(
        "--requires",
        action="append",
        default=[],
        dest="requires",
        metavar="REQUIREMENT",
        help="a requirement the line would carry, repeatable: `add` puts it on the line",
    )
    _marker_flag(
        budget_parser, "the marker the line would carry (default: the first declared)"
    )
    budget_parser.add_argument(
        "--symptom",
        default="",
        help="the symptom, drafted or written: what it takes is what the why loses",
    )
    # The draft, at the door that already states the allowance (RK1190). Measured and never
    # composed: a `why` twice its limit is a number here and a refusal on `add`, and that
    # difference is the whole reason this argument exists rather than a `--dry-run`.
    budget_parser.add_argument(
        "--why",
        help=(
            "a draft of the why, measured against its allowance instead of refused by it"
            + _PIPE
        ),
    )
    budget_parser.add_argument(
        "--prefix",
        dest="family",
        help="count the derived id in this track (default: the first declared)",
    )
    budget_parser.add_argument(
        "--ref",
        help=(
            "the anchor the line would point at, for ref_scheme = 'outline' only: the "
            "pointer is structure, so unnamed the budget assumes the widest on file"
        ),
    )
    # The other two prose limits, at the same door and never as a `--dry-run` (RK283): both
    # are facts about the file and the role, so both are answerable with no prose in hand.
    budget_parser.add_argument(
        "--anchor",
        metavar="ANCHOR",
        help="a section, e.g. RK12: what its body may say in words, and what it spends",
    )
    budget_parser.add_argument(
        "--role",
        choices=PROSE_ROLES,
        help="which prose file --anchor is priced against (default: the one holding it)",
    )
    # The section's own draft, beside the field's (RK1190). Two flags rather than one, for
    # `section add`'s reason (RK381): a body is the longest thing an author composes, and a
    # path is what a caller reaches for when the prose will not fit in a shell argument.
    # And each answers to **both** spellings the write path uses (RK1459). `section add` takes
    # `--body-file` because a body is the only thing it writes; `add` takes
    # `--section-body-file` because there the body is one of two and the prefix says which.
    # Both are right where they are, and this verb is the one asked about both subjects — so a
    # caller moving from the price to the write was refused by the parser for the name it had
    # been told to use one call earlier. An alias and not a rename; the first spelling is what
    # the served schema publishes, so the surface is unchanged.
    # Printed by argparse itself, which is the half an alias needs to be findable: `--body,
    # --section-body BODY` stands in the option list, so neither `help` restates it and neither
    # pays for it over a transport where no flag is ever typed.
    budget_parser.add_argument(
        "--body",
        "--section-body",
        help="a draft body: what it costs the section this call is about" + _PIPE,
    )
    budget_parser.add_argument(
        "--body-file",
        "--section-body-file",
        dest="body_file",
        metavar="PATH",
        help="read the draft body from a file instead, with --anchor",
    )
    # The third write off the same line (RK1305), and the one this read did not answer for: a
    # retirement's reason shares the ledger's limit with a derived prefix, so the usable
    # maximum is neither the published one nor the one a ship is quoted. A value and not a
    # flag, for `--tools`' reason: bare is the abandonment and named is the supersession, which
    # spends more of the field before the author starts.
    budget_parser.add_argument(
        "--retire",
        nargs="?",
        const="",
        metavar="SUPERSEDED_BY",
        help=(
            "what a retirement's reason has — bare, abandoned; named, superseded by that "
            "id, which costs more of the field"
        ),
    )
    # RK1458. Two limits govern one sentence and this read knew one: `brief` quotes both and
    # this quoted the roadmap line's, so a ship sentence was priced against a write nobody was
    # making. A flag and not a value, unlike `--retire`: a ship writes no prefix into the field.
    budget_parser.add_argument(
        "--ship",
        action="store_true",
        help=(
            "price the sentence a `ship` writes instead of this line's: the ledger's limit, "
            "which is a different number"
        ),
    )
    # RK1479, and the subject RK1458 named and could not price: a pause writes its reason
    # *wrapped*, with the roadmap's own sentence carried whole after it, so the field holds
    # three pieces and only two had a reading. A flag and not a value, like `--ship`.
    budget_parser.add_argument(
        "--defer",
        action="store_true",
        help=(
            "price the reason a `defer` writes: the store's limit, less the wrapper and the "
            "design carried forward"
        ),
    )
    budget_parser.add_argument(
        "--non-goal",
        dest="non_goal",
        action="store_true",
        help="the two limits `non-goal add` enforces, which are the list's own",
    )
    budget_parser.add_argument(
        "--lead",
        help="a non-goal that exists, with --non-goal: what its reason has left",
    )
    # The fourth subject, and the one limit this format holds that had no pre-write read
    # (RK345): every other budget is derived from a line, and this one from the file on disk.
    budget_parser.add_argument(
        "--file",
        nargs="?",
        const="",
        metavar="PATH",
        help=(
            "an every-turn file `[budgets]` declares, e.g. agents.md: what it costs and "
            "what is left — bare, every declared budget"
        ),
    )
    budget_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    withheld(
        budget_parser,
        family="`add`'s reason read back: the answer is about the id this project would issue next, and a prefix typed here asks about one it would not",
        body_file="this read exists because a refusal over the transport costs the whole payload again, and the three verbs that write a body now take a path (RK1260), which is refused for the corrected field alone — so the draft still worth pricing here is the one that arrived in the call",
    )
    # Declared although this verb writes nothing (RK1260). `reads_stdin` is not about the
    # write lock: it is what a surface with no pipe reads to refuse `-` by name instead of
    # measuring a one-character draft and answering about it. Two of the three drafts reach the
    # pipe — `--symptom` never did, though the description above claimed all three, which is
    # what the declaration makes checkable.
    budget_parser.set_defaults(
        handler=_budget,
        reads_only=True,
        reads_stdin=(
            Prose(dest="why", omitted=False),
            Prose(dest="body", omitted=False, unless="body_file"),
        ),
    )
    # The subjects this verb keeps (RK283/RK345), declared rather than checked by hand (RK489).
    # Named rather than inferred from the positional: under the id scheme `RK12` is both a
    # line and an anchor, and a command that guessed which one was meant would be a budget
    # the caller has to check before trusting.
    # The three departures are answers too (RK1479). They were not, while `--retire` was the
    # only one and a second could not be passed; `--ship` made two and `--defer` three, and
    # the dispatch below returns on the first it sees — so `budget --ship --defer` answered as
    # `--ship` and said nothing about the flag it dropped, which is RK465's finding exactly.
    answers(
        budget_parser,
        ("anchor", "one section's prose"),
        ("non_goal", "the roadmap's other bullet"),
        ("file", "an every-turn file"),
        ("retire", "the reason a retirement writes"),
        ("ship", "the sentence a ship writes"),
        ("defer", "the reason a pause writes"),
    )

    # The other half of what `budget` was (RK1321). Eight subjects under one name made it the
    # largest served tool — 2,741 against a per-tool ceiling calibrated on `ship` at 2,466 —
    # so whichever subject arrived last was refused by a limit none of them was about. The
    # seam is the tense: `budget` says what a write **may** spend before a word exists, and
    # this says what a surface **does** spend, already, every session.
    cost_parser = subcommands.add_parser(
        "cost",
        help="what this project's surface costs a session, and where",
        description=(
            "Report what a caller already pays: the tool list once at connect, the files "
            "loaded on every turn, and what the read that replaces opening a file costs a "
            "tool result. `budget` is the other tense — what a write may spend before a "
            "word of it exists. Reads; never writes."
        ),
    )
    # A value and not a flag (RK1236): bare is the ranking over every tool, and named is the
    # ranking inside one — the question a caller has the moment the gate names a tool.
    cost_parser.add_argument(
        "--tools",
        nargs="?",
        const="",
        metavar="TOOL",
        help=(
            "what the tool list costs a session — bare, every tool ranked; named, e.g. "
            "ship, what each of that one's fields spent"
        ),
    )
    cost_parser.add_argument(
        "--brief",
        nargs="?",
        const="",
        metavar="ID",
        help="what a brief costs a tool result — bare, every open line, widest first",
    )
    cost_parser.add_argument(
        "--session",
        action="store_true",
        help=(
            "what one session pays: the served schema once at connect and every "
            "`[budgets]` file each turn, against the cadence of each"
        ),
    )
    # Kept to one clause because this surface is what it is about: adding the subject at the
    # length the other three are written to put the served schema 74 characters past `[tools]
    # session`, and `lint` said so (RK1424). What the answer carries — the comparison, the
    # sections, the absent ceiling — is in the answer, where it costs the callers who ask.
    cost_parser.add_argument(
        "--skill",
        action="store_true",
        help="what the write path costs the turns that load it",
    )
    cost_parser.add_argument(
        "--deny",
        action="store_true",
        help="what one refused write costs the session that meets it",
    )
    cost_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    cost_parser.set_defaults(handler=_cost, reads_only=True)
    answers(
        cost_parser,
        ("tools", "what this tool surface costs a session"),
        ("brief", "what the read that replaces the file costs a tool result"),
        ("session", "both halves of what a session pays, against their cadences"),
        # The fourth cadence (RK1424): trigger-loaded, so it is neither the schema's once at
        # connect nor `[budgets]`' every turn, and it is larger than either.
        ("skill", "what the write path costs the turns that load it"),
        # And the fifth (RK1428), paid per refused write by the surface this plugin is for.
        ("deny", "what one refused write costs the session that meets it"),
    )
    # The one subject of this verb the surface does not offer (RK1428), and `list --ids`'
    # reason exactly: a caller over that transport is *handed the denial itself*, so the
    # figure adds nothing it could not count from the text already in front of it — while the
    # author who can shorten the tables is at a terminal. Measured before it was decided:
    # exposing it costs 102 characters against 19 of room under `[tools] session`, and a
    # ceiling raised to admit the next subject is the reviewer's limit RK30 replaced.
    withheld(
        cost_parser,
        deny=(
            "the caller over this transport is handed the denial itself, so the figure adds "
            "nothing it could not count from the text in front of it — and exposing it costs "
            "102 characters against 19 of room under `[tools] session`"
        ),
    )
    narrows(budget_parser, "role", "anchor")
    # `--body` is **not** narrowed to `--anchor` (RK1224). It was, and that was the last thing
    # standing between this verb and one call for a whole `add --section`: the line subject
    # already reports the section its pointer names (RK301), so a draft body handed to it has
    # somewhere to be measured — and without that, the transaction `add` validates as one unit
    # took two reads to price. Measured filing one Shio task: four calls, three of them `why`
    # overflows of 176, 171 and 170 against 167, each throwing away the 250-word body that
    # travelled beside it. The field that failed was three characters too long and the payload
    # re-sent to fix it was two orders of magnitude larger.
    #
    # Still refused beside a subject with no section at all — `--file`, `--tools`, `--session`
    # — which is what `_one_answer` decides from `answers` above, and which is RK465's rule
    # kept where it applies: a draft measured against nothing is a number the caller misreads.
    narrows(budget_parser, "lead", "non_goal")

    show_parser = subcommands.add_parser(
        "show",
        help="one task: its line, its rationale section and the paths it names",
        description=(
            "Join what a task is out of the files that hold a piece of it. Nothing is "
            "stored to make this possible: the section is found by the pointer, and a "
            "pointer that resolves to nothing is reported as the absence it is."
        ),
    )
    show_parser.add_argument("id", help="the task, e.g. RK12")
    show_parser.add_argument(
        "--no-body",
        dest="no_body",
        action="store_true",
        help="omit the section's prose, keeping the line and where the prose is",
    )
    show_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    show_parser.set_defaults(handler=_show, reads_only=True)

    pick_parser = subcommands.add_parser(
        "pick",
        help="the next task to work on, and the reason it was chosen",
        description=(
            "Apply three tiers — work already in progress, the declared priority, then "
            "the lowest ready id — and print which one answered. A task blocked outside "
            "the backlog is never offered: shipping cannot unblock it."
        ),
    )
    pick_parser.add_argument(
        "--block",
        help=(
            "scope every part of the answer to one block, so 'nothing to pick' is a "
            "statement about that block and not about a lower id somewhere else"
        ),
    )
    pick_parser.add_argument(
        "--designed",
        action="store_true",
        help=_DESIGNED_HELP,
    )
    pick_parser.add_argument(
        "--have",
        action="append",
        default=[],
        metavar="REQUIREMENT",
        help=_HAVE_HELP,
    )
    pick_parser.add_argument(
        "--claim",
        action="store_true",
        help=(
            "take the line as well as read it: the marker moves to in-progress in the same "
            "transaction, so the next caller is answered with something else"
        ),
    )
    pick_parser.add_argument(
        "--json", action="store_true", help="the pick, the tier and the counts"
    )
    # The query it is without `--claim`, and the write it is with one (RK167). `take` still
    # holds a lock of its own over the answer *and* the marker, that pair being what has to be
    # indivisible for every caller — re-entrant, so declaring it here costs nothing twice.
    withheld(
        pick_parser,
        claim="`brief`'s reason, and its answer too: the writing door is already served as the `claim` tool, so a second flag here would be a second spelling of it",
    )
    pick_parser.set_defaults(handler=_pick, reads_only=True, writes_when="claim")

    export_parser = subcommands.add_parser(
        "export",
        help="project the backlog onto a README block, a page, or a JSON payload",
        description=(
            "Derive what another file would restate: counts per block and the next ready "
            "line. Idempotent and stamped with nothing, so a refresh with nothing to say "
            "makes no diff — and every character of content already passed `add`."
        ),
    )
    export_parser.add_argument(
        "--readme",
        nargs="?",
        const=DEFAULTS["readme"].name,
        metavar="PATH",
        help=(
            f"write the block between the roadkeep markers in this file "
            f"(default {DEFAULTS['readme'].name})"
        ),
    )
    export_parser.add_argument(
        "--site",
        nargs="?",
        const=DEFAULTS["site"].name,
        metavar="PATH",
        help=(
            f"the same projection as HTML, between the same two markers "
            f"(default {DEFAULTS['site'].name})"
        ),
    )
    export_parser.add_argument(
        "--contents",
        action="store_true",
        help=(
            "refresh the table of contents inside this project's rationale file, between the "
            "same two markers: every row is a heading that file already carries, so a `ship` "
            "that drops a section leaves the list wrong until this runs. Takes no path — the "
            "target is `[files]`' own"
        ),
    )
    export_parser.add_argument(
        "--spec",
        metavar="ID",
        help=(
            "one task as a document: its claim, what it depends on, what would finish it, "
            "the non-goals that bind it and its design section whole. `brief` is the same "
            "join bounded to a tool result; this one is bounded by a file, for a reviewer, "
            "a second agent or a CI job that cannot run the read"
        ),
    )
    export_parser.add_argument(
        "--json", action="store_true", help="the payload a site build reads"
    )
    export_parser.set_defaults(handler=_export)
    # `--json` is a subject and a destination is a write, so asking for both asks two
    # questions (RK466). `--readme` and `--site` are not that shape — they are two
    # destinations of one projection and compose, which RK39 asked for, so they are one
    # group: the whole reason :class:`Answer` holds a group rather than a flag.
    answers(
        export_parser,
        ("json", "the projection printed"),
        (("readme", "site"), "the projection written into a file"),
        # A third subject and not a third destination (RK1362): this one is about one task,
        # so it answers a different question rather than putting the same answer somewhere
        # else. `brief <id> --json` is the payload read; this verb's `--json` is the site
        # build's, and the two are about different documents.
        ("spec", "one task as a document"),
    )

    gaps_parser = subcommands.add_parser(
        "gaps",
        help="ids in neither file, resolved against the commit that removed them",
        description=(
            "Every id below the highest that no line carries. Each resolves to the commit "
            "whose message holds the decision, to 'never carried' when a complete history "
            "mentions it nowhere, or to 'unresolvable' when there is no history to search "
            "— three different answers from 'retired', none of them a weaker one."
        ),
    )
    gaps_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    gaps_parser.set_defaults(handler=_gaps, reads_only=True)

    govern_parser = subcommands.add_parser(
        "govern",
        help="declare one number roadkeep.toml governs, against the reading that decides it",
        description=(
            "Take the reading and write the number in one call. `[limits]`, `[budgets]`, "
            "`[tools]` and `[claims]` hold the values that are a judgement about a figure, "
            "and each already had the read that decides it somewhere else. With no value it "
            "prints the reading alone. A limit this project already breaks is refused rather "
            "than written. Why this number and not the next is yours to write and this "
            "verb's to place: `--because` stacks your sentence above the key, and `--instead` "
            "replaces the argument standing there, for a reading that has moved."
        ),
    )
    govern_parser.add_argument(
        "key",
        help="the address, as `config` prints one — e.g. limits.symptom, tools.session",
    )
    govern_parser.add_argument(
        "at",
        nargs="?",
        type=int,
        help="the number to declare; omitted, the reading is printed and nothing is written",
    )
    govern_parser.add_argument(
        "--role",
        help="which role's limits, for a `[limits.<role>]` table (default: the shared one)",
    )
    govern_parser.add_argument(
        "--file",
        help="which every-turn file, for a `[budgets]` entry — the path the config spells",
    )
    govern_parser.add_argument(
        "--because",
        default="",
        help="your argument for this number, wrapped into comments above the key",
    )
    govern_parser.add_argument(
        "--instead",
        default="",
        help=(
            "the same sentence, replacing the run above the key instead of stacking on it; "
            "the answer names every line it took out"
        ),
    )
    govern_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    govern_parser.set_defaults(handler=_govern)

    config_parser = subcommands.add_parser(
        "config",
        help="what roadkeep.toml may declare: every table, key, type and default",
        description=(
            "Print the shape of this project's own configuration, answered by the package "
            "that refuses everything else (RK1270). One row per key — its table, its type, "
            "what this build uses when nobody declares it, and whether this project did — "
            "with the sentence the source already carries above each table. What is listed "
            "is what *this* copy accepts, which is how a key it predates is told from a typo, "
            "so the build that answered is named. Last, what this build *fixes* from its own "
            "corpus and no project declares, with the reading behind it. It reads and never "
            "writes."
        ),
    )
    config_parser.add_argument(
        "--table",
        default=None,
        help=(
            "one table, spelled as the answer spells it — omitted, every one; the top level "
            "is the empty string, and a table declared per role or per path carries the "
            "placeholder, e.g. rules.<role>"
        ),
    )
    config_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    config_parser.set_defaults(handler=_config_shape, reads_only=True)

    commands_parser = subcommands.add_parser(
        "commands",
        help="what may be typed: every verb, its arguments, defaults and served exposure",
        description=(
            "Print this build's own command surface as data (RK1401). One block per verb — "
            "whether it reads or writes, the flag that turns a read into a write, and one "
            "row per argument with its spellings, what it takes, its default and the "
            "sentence the parser already carries — plus which tool an agent is served it as, "
            "and which of its arguments that surface exposes on *this* project. `config` "
            "answers what roadkeep.toml may declare; this answers what may be typed. What is "
            "listed is what *this* copy takes, so the build that answered is named. It reads "
            "and never writes."
        ),
    )
    commands_parser.add_argument(
        "--command",
        default=None,
        metavar="VERB",
        help=(
            "one verb, spelled as the answer spells it — omitted, every one; a nested one "
            "carries its path, e.g. 'section add'"
        ),
    )
    commands_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    commands_parser.set_defaults(handler=_commands, reads_only=True)

    anchors_parser = subcommands.add_parser(
        "anchors",
        help="which outline addresses this project has ever declared, live or retired",
        description=(
            "Read the anchors out of every declared prose file and out of its diffs: live "
            "ones a heading declares now, and retired ones a ship deleted while every entry "
            "citing them stayed. An address is spent once a heading used it (RK4's rule for "
            "ids), so this is the read that says which number a reopened family may take — "
            "and which top-level is free, which is what a reused block needs."
        ),
    )
    anchors_parser.add_argument(
        "--family",
        default="",
        metavar="ANCHOR",
        help="only this subtree, e.g. XXXVII — omitted, one row per top-level family",
    )
    anchors_parser.add_argument(
        "--block",
        default="",
        metavar="LABEL",
        help=(
            "the subtree this block's prose already lives under, e.g. Q — the address a "
            "caller knows, since a prose file under an outline declares no block heading; "
            "refused with --family, and names both where a block spans two families"
        ),
    )
    anchors_parser.add_argument(
        "--role",
        default="",
        help=(
            "list only this prose file's addresses (default: every declared one) — the "
            "free top-level is per namespace, so it stays the project's where no [refs] "
            "declares one and is that file's own where one does"
        ),
    )
    anchors_parser.add_argument(
        "--next",
        dest="only_next",
        action="store_true",
        help=(
            "the free address alone, without the listing of spent ones — the `next-id` of "
            "anchors, and the read an `add --ref` makes every time"
        ),
    )
    anchors_parser.add_argument(
        "--claims",
        action="store_true",
        help=(
            "only the addresses whose ownership is not the ordinary one: a heading binding "
            "nobody, and one binding a task no open line claims — the audit, over every "
            "family at once, since the rows it leaves out are the ones nobody reads"
        ),
    )
    # RK1466. On a project whose addresses have no families the listing is the rows, and the
    # retired half of them grows by one per shipped task with nothing to prune it — 943 of this
    # repository's 983. So the wide read carries the live ones and this is the door to the rest.
    anchors_parser.add_argument(
        "--retired",
        action="store_true",
        help="list the retired addresses too, which the wide listing counts and withholds",
    )
    anchors_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    withheld(
        anchors_parser,
        retired="the listing this flag widens is exactly the one the bound exists for: 943 of this repository's 983 addresses are retired, so an answer carrying them is a tool result three times the size of the surface that published the read",
    )
    anchors_parser.set_defaults(handler=_anchors, reads_only=True)
    # Two subjects, as `budget`'s four are (RK466): `--next` returned before the `--claims`
    # branch was reached, so a caller asking for the audit and the free address read the
    # address alone with nothing said about the other.
    # Three since RK1466: `--retired` is a listing of its own, so a caller who asked for it
    # and for the free address or the audit asked two questions and would be answered one.
    answers(
        anchors_parser,
        ("only_next", "the free address"),
        ("claims", "the ownership audit"),
        ("retired", "the retired addresses"),
    )

    deps_parser = subcommands.add_parser(
        "deps",
        help="resolve one task's deps, naming the ones nothing can resolve",
        description=(
            "Resolve each dep against the roadmap and the changelog. A dep nothing now "
            "open will satisfy is reported as unresolvable rather than open — work "
            "outside the backlog, a task that retired, and a block label with nothing "
            "filed under it."
        ),
    )
    deps_parser.add_argument("id", help="the task to resolve, e.g. RK5")
    deps_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    deps_parser.set_defaults(handler=_deps, reads_only=True)

    origin_parser = subcommands.add_parser(
        "origin",
        help="the commits that proposed and shipped a task, with the reasoning",
        description=(
            "Resolve a task's history from git. The pointer is derived, never stored: "
            "a hash written into the ledger would be rewritten by the first squash or "
            "amend, and a dead hash reads exactly like a live one. A leading § asks the "
            "same question of a rationale anchor instead — the dangling cross-reference a "
            "ship leaves in somebody else's prose, which no file records the answer to."
        ),
    )
    origin_parser.add_argument(
        "id", help="the task to look up, e.g. RK1 — or §<anchor>, as the prose spells it"
    )
    origin_parser.add_argument(
        "--why",
        action="store_true",
        help="print the shipping commit's full message — the rationale the ledger drops",
    )
    origin_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    origin_parser.set_defaults(handler=_origin, reads_only=True)

    weight_parser = subcommands.add_parser(
        "weight",
        help="what comparable tasks cost, derived from the commits that shipped them",
        description=(
            "What a comparable task cost, so granularity is a query instead of a feel: a "
            "block whose last comparables shipped at 800+ lines is a block where the next "
            "line is probably two lines. Derived from the commit that wrote each ledger "
            "entry, so nothing stores it and `git show` refutes it. Two axes and no score — "
            "median to p90 lines vary 2.7× here and files, which is what an agent holds in "
            "context, 1.4×. An entry whose commit wrote several is named and left out "
            "rather than given a share of it, a divided cost being one no commit contains. "
            "This ranks nothing: every tier of `pick` is a fact, and a cheapness tier would "
            "defer the architectural tasks, which is where the leverage is."
        ),
    )
    weight_parser.add_argument("--block", help="only this block's comparables, e.g. C")
    weight_parser.add_argument(
        "--records",
        action="store_true",
        help=(
            "every weighed entry, which the percentiles summarise: the evidence for the "
            "figure, wanted when you dispute it and not when you are sizing a line (RK264)"
        ),
    )
    weight_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    weight_parser.set_defaults(handler=_weight, reads_only=True)

    remaining_parser = subcommands.add_parser(
        "remaining",
        help="how many sites a task's own declared query still matches",
        description=(
            "The mirror of `weight`, and derived the same way (RK492): that one says what a "
            "comparable task cost, from the commits that shipped it, and this says what one "
            "has left, from the repository as it is now. A migration declares the query in "
            "its rationale section — a fenced `roadkeep-remaining` block, one `<pathspec> :: "
            "<regex>` per line — and this runs it. Nothing is stored, so nothing goes stale: "
            "the first commit that closes a site changes the answer, which a number written "
            "onto a line could not. It is a count and never a verdict — the pattern is the "
            "author's, so a query answering 0 says the pattern stopped matching, and whether "
            "that is the work being done is a judgement this tool does not make."
        ),
    )
    remaining_parser.add_argument("id", help="the task whose design declares the query, e.g. RK12")
    remaining_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    remaining_parser.set_defaults(handler=_remaining, reads_only=True)

    evidence_parser = subcommands.add_parser(
        "evidence",
        help="what this task's design says would prove it done, counted now",
        description=(
            "Run the criterion a design declares, against this tree, now. `remaining` "
            "with the sign flipped: a `roadkeep-evidence` fenced block names sites that "
            "must **exist** where the other names sites still to change, and both are one "
            "`<pathspec> :: <regex>` per line read by one grammar. Never a verdict — the "
            "pattern is the author's claim and the count is the answer, so 0 says the "
            "evidence is not there yet and whether that is the work being done is yours "
            "to judge. Nothing is stored, so nothing goes stale."
        ),
    )
    evidence_parser.add_argument("id", help="the task whose design declares the criterion")
    evidence_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    evidence_parser.set_defaults(handler=_evidence, reads_only=True)

