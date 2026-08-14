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

from roadkeep.backlog import Backlog, Stage, Standing
from roadkeep.capturing import debt
from roadkeep.briefing import NothingToBrief, brief
from roadkeep.budgeting import (
    Load,
    Session,
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
from roadkeep.remaining import QueryError, count, declared
from roadkeep.rendering import (
    CHARACTER_UNIT,
    _claim_event,
    _commits_json,
    _load_json,
    _nothing_json,
)
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
    # The capture debt is a second subject and joined here (RK1139): a capture is not a line
    # of the file this counts, so reading one inside the census would make a count of the
    # roadmap depend on a directory git ignores.
    owed = debt(config)
    if args.json:
        print(json.dumps(census.counts(config, standing, owed), indent=2))
    else:
        print(census.counted_out(config, owed))
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
    answer = Session(
        once=sent.characters,
        tools=len(sent.tools),
        resident=tuple(
            (load.path, load.bytes)
            for load in (file_budget(config) if config.budgets else ())
        ),
    )

    if args.json:
        print(json.dumps(answer.payload(CHARACTER_UNIT), indent=2))
    else:
        print(answer.stated(CHARACTER_UNIT))
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

    if args.json:
        print(json.dumps(sent.payload(CHARACTER_UNIT, config.tool_characters), indent=2))
    else:
        print(sent.stated(CHARACTER_UNIT, config.tool_characters, _LARGEST_TOOLS))
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
            print(
                "roadkeep: no outline family exists yet, so none is spent — `add --ref I.1` "
                "opens the first",
                file=sys.stderr,
            )
            return EXIT_USAGE
        print(chr(10).join(out))
        for note in notes:
            print(note, file=sys.stderr)
        return EXIT_OK

    if args.json:
        print(json.dumps(found.payload(config, args.claims), indent=2))
    else:
        print(found.stated(config, args.claims))
    return EXIT_OK


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


