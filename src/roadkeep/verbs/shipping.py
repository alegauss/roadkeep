"""The verbs a task leaves by, and the two reads only the ledger can answer (RK494).

`ship`, `retire` and the `record` family write the terminal entry; `delivered` and
`reversals` read it back — what a block already shipped, and which of those deliveries was
later undone. Filed by their subject, an entry in the ledger, and not by whether they write
one: a proposal is checked against both, and the two reads come before it, not after.

**Every write here renders both registers off its own record** (RK1170), so each door is the
call, the save and a choice of reading — and this module no longer imports `rendering` at all.
The two reads still compose their answers here, which is the rest of that task.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence

from roadkeep.backlog import Backlog, Stage
from roadkeep.config import Config
from roadkeep.kernel.document import declares, shading
from roadkeep.ranking import NEAREST, nearest
from roadkeep.reverting import Reversed, reversals
from roadkeep.shipping import (
    Delivered,
    Closure,
    Partial,
    amend as amend_record,
    drop as drop_record,
    move as move_record,
    readdress as readdress_record,
    record,
    retire,
    ship,
)
from roadkeep.serving import Prose
from roadkeep.verbs.declaring import (
    _JSON_HELP,
    _PIPE,
    _reason_flag,
    withheld,
)
from roadkeep.verbs.reading import _piped
from roadkeep.verbs.refusing import EXIT_GATE, EXIT_OK, EXIT_USAGE, REFUSALS, _refused



def _ship(config: Config, args: argparse.Namespace) -> int:
    if args.remainder is not None and args.part is None:
        # Refused rather than ignored (RK465, RK1233): a remainder on a whole shipment is a
        # sentence about a line that is being removed, and honouring it silently would write
        # the caller's words into a `why` the same transaction then deletes.
        print(
            "roadkeep: --remainder is what is left after --part, and this ship removes the "
            "line: pass --part <what landed> too, or leave it off",
            file=sys.stderr,
        )
        return EXIT_USAGE
    try:
        shipment = ship(
            config,
            args.id,
            # Resolved by `dispatch` from what this verb's parser declares (RK1176), and no
            # longer here: a call site that reads the pipe for one argument is a call site that
            # can be written without it, which is how `--superseded-design` published a dash.
            why=args.why,
            part=args.part,
            remainder=args.remainder,
            lines=args.lines,
            superseded=args.superseded_design,
            recorded_in=args.recorded_in,
            decides=args.decides,
            decides_ref=args.decides_ref,
        )
        # The files this transaction wrote, answered by the write itself (RK309) — the half
        # of the commit's contents no author declares, and never a second list rebuilt here.
        wrote = shipment.save()
    except REFUSALS as error:
        return _refused(error)

    if isinstance(shipment, Partial):
        # Nothing was removed and nothing was dropped, so the departure's report would be
        # three lines of None (RK121): what happened is an entry and a marker.
        return _partly(config, shipment, args)
    if isinstance(shipment, Closure):
        # The ledger already holds the entry, so there is none to report (RK62): what this
        # call did is remove the line that was left behind, and the evidence is where the
        # entry already was.
        return _closed(config, shipment, args, wrote)

    if args.json:
        print(json.dumps(shipment.payload(config, wrote), indent=2))
    else:
        print(shipment.stated(config, wrote))
    return EXIT_OK


def _partly(config: Config, partial: Partial, args: argparse.Namespace) -> int:
    """Half of a task recorded, with its roadmap line still open (RK121)."""
    if args.json:
        print(json.dumps(partial.payload(config), indent=2))
    else:
        print(partial.stated(config))
    return EXIT_OK


def _closed(
    config: Config, closure: Closure, args: argparse.Namespace, wrote: Sequence[str] = ()
) -> int:
    """A roadmap line closed against an entry the ledger already had (RK62)."""
    if args.json:
        print(json.dumps(closure.payload(config, wrote), indent=2))
    else:
        print(closure.stated(config, wrote))
    return EXIT_OK


def _record(config: Config, args: argparse.Namespace) -> int:
    try:
        entry = record(
            config,
            block=args.block,
            symptom=args.symptom,
            why=_piped(args.why),
            task_id=args.task_id,
            supersedes=args.supersedes,
            lines=args.lines,
        )
        wrote = entry.save()
    except REFUSALS as error:
        return _refused(error)

    if args.json:
        print(json.dumps(entry.payload(config, wrote), indent=2))
    else:
        print(entry.stated(config, wrote))
    return EXIT_OK


def _record_amend(config: Config, args: argparse.Namespace) -> int:
    if args.why is None and args.part is None:
        print("roadkeep: nothing to amend: pass --why or --part", file=sys.stderr)
        return EXIT_USAGE
    try:
        # One read joined to the listing, not a second parse: `reversals` walks the same
        # entries for the same clause, so asking it here is what keeps the two answers one
        # fact (RK1042). Asked **before** the write and not after (RK1052): the mark lives
        # inside the `why` this command is about to replace, so the post-write state cannot
        # answer whether the entry being corrected had been undone. The parse is the one
        # `amend` is about to make of the same bytes, so this costs a cache hit.
        undone_by = {one.undone: one.by for one in reversals(config)}.get(args.id)
        corrected = amend_record(
            config, args.id, why=_piped(args.why), part=args.part, lines=args.lines
        )
        wrote = corrected.save()
    except REFUSALS as error:
        return _refused(error)

    if args.json:
        print(json.dumps(corrected.payload(config, wrote, undone_by), indent=2))
    else:
        print(corrected.stated(config, wrote, undone_by))
    return EXIT_OK


def _record_move(config: Config, args: argparse.Namespace) -> int:
    try:
        refiled = move_record(config, args.id, to_block=args.to_block)
        # Nothing is written where the entry already sits under that heading, so nothing is
        # staged either: an empty list is the honest answer and `_print_staging` says nothing.
        wrote = refiled.save() if refiled.moved else ()
    except REFUSALS as error:
        return _refused(error)

    if args.json:
        print(json.dumps(refiled.payload(config, wrote), indent=2))
    else:
        print(refiled.stated(config, wrote))
    return EXIT_OK


def _record_renumber(config: Config, args: argparse.Namespace) -> int:
    try:
        moved = readdress_record(config, args.id, lineno=args.line, to=args.to)
        wrote = moved.save()
    except REFUSALS as error:
        return _refused(error)

    if args.json:
        print(json.dumps(moved.payload(config, wrote), indent=2))
    else:
        print(moved.stated(config, wrote))
    return EXIT_OK


def _record_drop(config: Config, args: argparse.Namespace) -> int:
    try:
        dropped = drop_record(config, args.id, lineno=args.line)
        wrote = dropped.save()
    except REFUSALS as error:
        return _refused(error)

    if args.json:
        print(json.dumps(dropped.payload(config, wrote), indent=2))
    else:
        print(dropped.stated(config, wrote))
    return EXIT_OK


def _delivered(config: Config, args: argparse.Namespace) -> int:
    """Every claim this block has already made good on (RK385).

    **Symptoms and not entries.** A shipped line states two things — the problem it claimed
    and the outcome it delivered — and a duplicate collides with the first. Printing both
    doubles a read the author makes before every proposal, and the second half is the one
    that never matches: an outcome is written in the vocabulary of the fix.

    Unbounded, unlike `brief`'s carry of the non-goals (RK68). The bound there is what keeps
    a *brief* an answer rather than the file; here the list **is** the answer, and a
    truncated one is the failure mode this exists for — the entry that got elided is exactly
    the one nobody read.

    `--near` is the one bound, and it is not a truncation of this listing (RK442): it is the
    same read asked a **narrower question**, so what bounds it is the sentence the caller
    passed rather than a number this verb chose. That is the whole difference — an elision
    picks entries to drop and this picks the entries that answer — and it is why the header
    says how many of how many, why the plain listing is named beside it, and why the order
    is published with no score under it (RK441).

    Retired lines are in it. A claim that was abandoned is still a claim somebody made and
    argued about, and a proposal restating one wants the argument more than the outcome —
    the marker says which, so nothing is hidden and nothing is conflated.

    **The label is resolved before the ledger is filtered (RK433).** This answer is consumed
    as *evidence* — it is the read that decides whether an `add` is a duplicate — so the one
    thing it may not do is come back empty for a question it never asked. Filtering the
    entries by a literal made `Block Z has delivered nothing yet` the answer to four
    different states: a block still being worked, whose lines are open and none of them
    shipped; one whose work is all set aside; a heading opened before its lines; and a letter
    the project has never used. Only the fourth is a mistake, and it is the one that files
    the duplicate this verb exists to prevent. So :meth:`~roadkeep.backlog.Backlog.standing`
    runs first and its sentence rides with every answer, empty or not: the count is a fact
    about the ledger, the state is the fact about the label, and they say the same thing in
    one of the four states only.

    That sentence goes to **stdout** and on every state, which is where this parts company
    with `_print_standing` (RK429) and for two reasons that are this verb's own. Stdout,
    because there is no raw-file pipe to keep clean here — the header and the rows are
    already derived, reformatted text rather than the file's own lines. Unconditionally,
    because `Standing.settled` answers *which states an empty answer needs explaining by*,
    and nothing filtered this one: the state of the label is the whole reason the count is
    what it is, and three entries under a finished block is a different read from three under
    a live one. `standing.recorded` and the length of the listing are the same number by
    construction — both are `Document.block(label)` — so the figure printed twice is one
    fact stated twice on purpose.

    `unknown` exits **2**, never 0 or 1. Two, because `pick --block <x>`, `brief --block <x>`
    and `list --block <x>` already answer a label nothing declares that way, and one meaning
    per code is what a loop can branch on. Not one: in this tool 1 is a verdict about the
    repository's own contents, and `_may_offer` reads a read-only 1 as exactly that (RK86) —
    it would drop the capture offer a mistyped argv should keep. `--json` gets the refusal
    and no payload, which is the line RK409 drew: a finished block is an answer and deserves
    a shape, a name nothing declares is a refusal on every surface.

    The header and the state row take `Standing.named` rather than an f-string (RK75):
    `heading_word` is per project, and a report saying `Block G` to a project whose headings
    all say `Track` names nothing its author wrote. That is fixed for this verb and not for
    the file — the other reports here still spell it from a literal.
    """
    try:
        backlog = Backlog.load(config)
    except (KeyError, OSError) as error:
        return _refused(error)

    ledger = backlog.ledger
    if ledger is None:
        print(
            "roadkeep: this project declares no changelog, so nothing records what was "
            "delivered — `non-goal list` is the other read before an `add`",
            file=sys.stderr,
        )
        return EXIT_USAGE
    label = args.block.strip()
    standing = backlog.standing(label)
    if standing.stage is Stage.UNKNOWN:
        declared = sorted(backlog.declared_blocks())
        # Printed here rather than raised through `_refused`: this refusal is composed and
        # never raised, and `provenance.witness` on an exception carrying no traceback
        # records `()` — which is not `None`, so `_answered` would take it as evidence and
        # suppress the inventory RK267 reserves for exactly this case. The sibling refusal
        # above, for a project that declares no changelog, already exits this way.
        print(
            f"roadkeep: {standing.sentence}{declares(declared)}: the ledger was not read, "
            f"so this is not a block that delivered nothing{shading(label, declared)}",
            file=sys.stderr,
        )
        return EXIT_USAGE
    # `Document.block` and not a filter written here: it is the same call `Standing.of`
    # makes, which is what makes this count and `standing.recorded` one number rather than
    # two that agree.
    entries = ledger.block(label)
    # RK442: the whole block is what this verb answered with, and the question is whether one
    # sentence collides with it. Ranked here rather than inside the reader, because the
    # ordering is a property of the *query* and the block is the fact — and the unranked
    # tuple stays exactly what it was, so `--near` narrows one answer and does not make a
    # second one. `recorded` below is still the block's count, never the shown count.
    recorded = len(entries)
    if args.near is not None and not args.near.strip():
        # An empty `--near` used to fall through to the unbounded listing, which answers a
        # *different question* than the one asked and looks like the narrow answer until the
        # caller counts the rows: 103 lines where five were asked for. Every prose argument
        # in this tool refuses the empty slot, and a read is where it costs the most —
        # nothing exits non-zero, so a wrong answer is the only signal there is.
        print(
            "roadkeep: --near is the symptom you are about to propose, and it arrived "
            "empty: pass the sentence, or drop the flag for the whole block",
            file=sys.stderr,
        )
        return EXIT_USAGE
    if args.near:
        entries = tuple(
            entries[index]
            for index in nearest(args.near, [e.task.symptom for e in entries], NEAREST)
        )
    where = config.relative(config.path("changelog"))
    # One read joined to the listing, not a second parse: `reversals` walks the same entries
    # for the same clause, so asking it here is what keeps the two answers one fact (RK1042).
    answer = Delivered(
        where=where,
        standing=standing,
        entries=entries,
        recorded=recorded,
        near=args.near or "",
        reversed_by={one.undone: one.by for one in reversals(config)},
    )
    # Both registers off one result (RK1170). This is the read that decides whether an `add` is
    # a duplicate, so the two had better say the same thing — and they were a printer and a
    # payload builder in this handler, agreeing by hand over a header, a bound and a per-entry
    # mark. The payload now carries what the listing shows by construction.
    print(json.dumps(answer.payload(), indent=2) if args.json else answer)
    return EXIT_OK


def _reversals(config: Config, args: argparse.Namespace) -> int:
    """What the ledger already undid (RK416), and with `--id` whether one thing is among it.

    `--id` exits 1 rather than 0 for a reason the plain listing does not need: the caller is
    a script or an agent about to spend an id, and an exit code is what it can branch on
    without reading either stream. Exit 1 is "this was tried and undone" and never "you may
    not" — the read states a fact, and whether the revert was about a broken implementation
    or a wrong idea is the one thing nobody here can tell.
    """
    try:
        found = reversals(config)
    except (KeyError, OSError) as error:
        return _refused(error)

    if args.task_id:
        found = tuple(one for one in found if one.undone == args.task_id)
    answer = Reversed(
        found=found,
        where=config.relative(config.path("changelog")),
        root=config.root.as_posix(),
        asked=args.task_id or "",
    )

    if args.json:
        print(json.dumps(answer.payload(), indent=2))
    else:
        print(answer.stated())
    return EXIT_GATE if answer.gated else EXIT_OK


def _supersede(config: Config, args: argparse.Namespace) -> int:
    """The one door a decision leaves by (RK1274), which is not a departure from a backlog.

    Nothing is deleted and nothing is composed: both entries stay, the marker says which is
    live, and the clause naming the replacement is derived — so this handler passes two ids
    and reads the answer off the record like every other write here.
    """
    from roadkeep.shipping import supersede  # noqa: PLC0415 - RK260

    try:
        found = supersede(config, args.id, by=args.by)
        wrote = found.save()
    except REFUSALS as error:
        return _refused(error)

    if args.json:
        print(json.dumps(found.payload(config, wrote), indent=2))
    else:
        print(found.stated(config, wrote))
    return EXIT_OK


def _retire(config: Config, args: argparse.Namespace) -> int:
    """Record a line leaving without shipping, and say where its replacement is (RK32, RK244).

    Both registers come off the record (RK1170) — the *retirement* pair, one shape carrying two
    doors' answers. The replacement's id moved onto it with them: reading it back off argv was
    the verb answering about the call it received rather than the transaction it made.
    """
    try:
        departure = retire(
            config,
            args.id,
            reason=_piped(args.reason),
            superseded_by=args.superseded_by,
        )
        wrote = departure.save()
    except REFUSALS as error:
        return _refused(error)

    if args.json:
        print(json.dumps(departure.retirement(config, wrote), indent=2))
    else:
        print(departure.retired(config, wrote))
    return EXIT_OK


def declare_departures(subcommands: argparse._SubParsersAction) -> None:
    """This module's verbs, declared where their handlers are (RK1171).

    `build_parser` called forty-nine blocks like these in a row; what it calls now is an index
    over the modules that own them. The move is what RK1169 and RK1170 bought: the flags a verb
    declares, the reasons it withholds and the record it answers with are one file's, so a
    change to any of them is one file's too.

    The order inside is `build_parser`'s own, which is where these blocks sat.
    """
    ship_parser = subcommands.add_parser(
        "ship",
        help="move a task to the ledger, drop its rationale, clear the roadmap line",
        description=(
            "Ship one task in three edits across three files. Everything is validated "
            "before anything is written, because whichever of the three is done by hand "
            "last is the one that gets forgotten. `--why` is the outcome and is required: "
            "the roadmap's sentence states the problem, and inheriting it files a defect "
            "report under a heading that means done."
        ),
    )
    ship_parser.add_argument("id", help="the task to ship, e.g. RK5")
    ship_parser.add_argument(
        "--why",
        help=(
            "the outcome this shipped — required where an entry is written, because the "
            "roadmap's sentence states a problem and is not inherited; refused where the "
            "ledger already holds the id and this call only closes the line. Completing a "
            "wrapped partial with --lines above one, it is the whole span: the first line "
            "is the outcome and the rest is written back as the tail" + _PIPE
        ),
    )
    ship_parser.add_argument(
        "--part",
        help=(
            "record only the half that landed and leave the line open, e.g. 'local "
            "half'; a later ship with no --part completes it"
        ),
    )
    # The open half, as data (RK1233). Beside `--part` and narrowed to it, because a
    # remainder on a whole shipment is a sentence about a line that is being removed.
    ship_parser.add_argument(
        "--remainder",
        help="what is still left, with --part: it becomes the open line's why",
    )
    ship_parser.add_argument(
        "--lines",
        type=int,
        help=(
            "how many lines the completion replaces; required where the partial entry it "
            "completes wraps, and refused where this call replaces no entry — above one it "
            "is also what lets --why carry that span back instead of collapsing it"
        ),
    )
    ship_parser.add_argument(
        "--superseded-design",
        help=(
            "what the design this deletes turned out to be wrong about, e.g. 'the resize "
            "endpoint it called a new subsystem had shipped two blocks earlier'; appended "
            "to the ledger's sentence with the section's address, since the entry is the "
            "one place both survive the deletion" + _PIPE
        ),
    )
    # RK1267. No pipe: a path carries nothing a shell reads first, and the clause around it
    # is derived, so there is no prose here for stdin to be the door to.
    ship_parser.add_argument(
        "--recorded-in",
        dest="recorded_in",
        help="the file the deleted design's durable half moved to; must resolve",
    )
    # RK1269. It reads the pipe for `--why`'s reason: a constraint names types, files and
    # prior ids, so it carries the backtick and the apostrophe a shell reads first.
    ship_parser.add_argument(
        "--decides",
        help=(
            "the constraint the deleted design leaves behind, filed as one line in the "
            "decisions role" + _PIPE
        ),
    )
    # RK1363. The address of the body that record keeps, on a project whose anchors are its
    # own numbering. No pipe: it is an address and not prose, so nothing a shell eats is in it.
    ship_parser.add_argument(
        "--decides-ref",
        dest="decides_ref",
        metavar="ANCHOR",
        help=(
            "where the decision's body goes, as an outline anchor — required beside "
            "--decides where `ref_scheme = \"outline\"` and refused where the anchor is the "
            "id; `anchors --role decisions --next` names a free one"
        ),
    )
    ship_parser.add_argument("--json", action="store_true", help="every edit, as data")
    ship_parser.set_defaults(
        handler=_ship,
        reads_stdin=(
            Prose(dest="why", omitted=False),
            # The argument RK1176 was filed about: the pipe is documented on every prose
            # argument, and this one reached the ledger as a literal `-` because the handler
            # resolved `--why` by hand and this was added after that line was written.
            Prose(dest="superseded_design", omitted=False),
            # RK1269, and declared here rather than remembered: a prose argument that is not
            # on this tuple is one the pipe silently does not reach.
            Prose(dest="decides", omitted=False),
        ),
    )

    record_parser = subcommands.add_parser(
        "record",
        help="write, correct, re-file, renumber or drop a ledger entry directly",
        description=(
            "The ledger's own doors, the ones the roadmap's are not: every other command "
            "starts from a task line, and these start from the entry."
        ),
    )
    entries = record_parser.add_subparsers(dest="action", required=True)

    record_add = entries.add_parser(
        "add",
        help="write a ledger entry directly, for shipped work no open line can carry",
        description=(
            "The fourth door, and the only one that starts nowhere: `ship` and both "
            "retirements begin from an open roadmap line, so this is how the ledger records "
            "work that has none. Never planned is one case and not the definition — a task "
            "that was planned and shipped inside another's sentence needs its own entry too, "
            "and so does a revert (--supersedes). What it does is write the entry and touch "
            "nothing else; without it the only route in was a fictitious line shipped in the "
            "same breath, which teaches that the format can be gamed."
        ),
    )
    record_add.add_argument("--block", required=True, help="the block label, e.g. B")
    record_add.add_argument(
        "--symptom",
        required=True,
        help="what did not work — a phrase, never the name of the patch that closed it",
    )
    record_add.add_argument(
        "--why",
        required=True,
        help="one sentence, ending in a stop: the outcome" + _PIPE,
    )
    record_add.add_argument(
        "--id",
        dest="task_id",
        help=(
            "the id (default: derived, one past the highest anywhere); refused where a "
            "line already holds it, allowed where only a sentence names it — which is how "
            "an id cited but never recorded gets the entry it is missing"
        ),
    )
    record_add.add_argument(
        "--supersedes",
        metavar="ID",
        help=(
            "the entry this one reverts: its sentence gains `(superseded by <id>)` in the "
            "same write, so the ledger's two records of one decision know about each other"
        ),
    )
    record_add.add_argument(
        "--lines",
        type=int,
        # Declared only so a script that spells it gets `NoSpan` rather than argparse's
        # `declares no --lines` (RK1056): the count authorised a span rewrite the pointer
        # stopped making, and the refusal is the one answer that says which of the two
        # changed. Withdrawn from the served tool, which has no script to keep working.
        help=(
            "refused, and kept only to say so: the --supersedes pointer is appended to the "
            "sentence on the entry's first line and replaces no span, so a wrapped bullet "
            "needs no count and keeps the lines under it"
        ),
    )
    record_add.add_argument(
        "--json", action="store_true", help="the entry, with the file and line it landed on"
    )
    withheld(
        record_add,
        task_id="the ledger's id is the roadmap line's, and `ship` is what carries it across; typing one here is inventing an id the backlog never issued",
        lines="the entry's shape is derived from what it records, and a count set by hand is the arrangement the schema replaced",
    )
    record_add.set_defaults(
        handler=_record, reads_stdin=(Prose(dest="why", omitted=False),)
    )

    record_amend = entries.add_parser(
        "amend",
        help="correct a ledger entry's sentence where it stands",
        description=(
            "Rewrite one entry's `why`, or a partial's qualifier, without moving the line. "
            "`drop` and `add` are not equivalent to this: they would remove the entry and "
            "append a new one under its block, so a ledger read in the order work landed "
            "stops being one and a reviewer sees a deletion where a word changed. The "
            "`symptom` is the claim and is not a field, the id is `renumber`'s, and the "
            "block is not offered because filing an entry elsewhere is a move."
        ),
    )
    record_amend.add_argument("id", help="the recorded id, e.g. RK41")
    record_amend.add_argument(
        "--why",
        help=(
            "the corrected sentence, one stop — or, with --lines above one, the whole span: "
            "the first line is the sentence and the rest is written back as the tail" + _PIPE
        ),
    )
    record_amend.add_argument(
        "--part",
        help="correct a partial's qualifier; refused where the entry carries none",
    )
    record_amend.add_argument(
        "--lines",
        type=int,
        help=(
            "how many lines this correction replaces; required where the entry wraps, "
            "because there the sentence runs past the line the parse holds — and above "
            "one it is also what lets --why carry that span back"
        ),
    )
    record_amend.add_argument("--json", action="store_true", help=_JSON_HELP)
    record_amend.set_defaults(
        handler=_record_amend, reads_stdin=(Prose(dest="why", omitted=False),)
    )

    record_move = entries.add_parser(
        "move",
        help="re-file a ledger entry under another block heading",
        description=(
            "The move `amend` deliberately does not pretend is a correction. `ship` files an "
            "entry under the block its roadmap line sat in, so a line filed under the wrong "
            "one ships to the wrong one — and no other verb reaches it: `record add` refuses "
            "an id that exists, `drop` wants the id stated twice, `renumber` changes the "
            "address and not the heading. This removes the line and re-places it under the "
            "named heading, reporting both positions, and refuses a heading the ledger does "
            "not declare — `block add` is what writes one."
        ),
    )
    record_move.add_argument("id", help="the recorded id, e.g. RK41")
    record_move.add_argument(
        "--to-block",
        required=True,
        dest="to_block",
        help="the block label to file it under, e.g. B; refused unless a heading declares it",
    )
    record_move.add_argument(
        "--json", action="store_true", help="both positions, and the blocks they are under"
    )
    record_move.set_defaults(handler=_record_move)

    record_drop = entries.add_parser(
        "drop",
        help="remove the later of two ledger entries for one id",
        description=(
            "Delete a duplicate entry, and only a duplicate: refused unless the ledger states "
            "the id twice, because removing the only record of a decision is deleting history "
            "rather than de-duplicating it. The first entry stays, since that is where a "
            "reader already found the decision, and no other file is opened."
        ),
    )
    record_drop.add_argument("id", help="the id the ledger carries twice, e.g. RK41")
    record_drop.add_argument(
        "--line",
        type=int,
        help=(
            "which of the two entries goes; required when they do not say the same thing, "
            "because then they are two deliveries and not one recorded twice"
        ),
    )
    record_drop.add_argument(
        "--json", action="store_true", help="which line went, and which one answers now"
    )
    record_drop.set_defaults(handler=_record_drop)

    record_renumber = entries.add_parser(
        "renumber",
        help="give one of two entries for an id an address of its own",
        description=(
            "The counterpart of `renumber` for the file that verb never opens. Renumbering "
            "a record is normally how a `git log -S` starts returning two unrelated "
            "designs — and that argument inverts on a collision, where the shared id is "
            "already what makes the history unreadable. Refused on anything but an id the "
            "ledger states twice, and which of the entries moves is yours to name: the one "
            "that earned the id from a roadmap line is the one to leave alone."
        ),
    )
    record_renumber.add_argument("id", help="the id the ledger carries twice, e.g. RK41")
    record_renumber.add_argument(
        "--line", type=int, help="the entry that moves; named, never defaulted"
    )
    record_renumber.add_argument(
        "--to", help="the new id (default: derived, one past the highest in its family)"
    )
    record_renumber.add_argument("--json", action="store_true", help=_JSON_HELP)
    record_renumber.set_defaults(handler=_record_renumber)

    delivered_parser = subcommands.add_parser(
        "delivered",
        help="what a block has already shipped, as claims — the read before an `add`",
        description=(
            "The other list to consult before proposing work, beside `non-goal list` "
            "(RK69). A duplicate is not refused and could not be: RK378 restated RK340 the "
            "day after it shipped and RK382 restated RK178 a day later, and a lexical match "
            "cannot be gated: measured over this ledger it ranks the true pair in the top "
            "three and still scores below what an entry with no duplicate scores against "
            "its own nearest neighbour, so no threshold separates them. Two people "
            "describing one problem use disjoint words, and recognising that takes meaning "
            "this tool has none of (L4). So it states what "
            "the block delivered and you read it. Symptoms alone: the claim is what a "
            "duplicate collides with, and the outcome sentence doubles the length. A letter "
            "no heading declares is refused rather than answered as empty — that answer is "
            "read as evidence — and where the label is declared the reply says which of "
            "live, paused, finished or empty the block is. `--near` is the same read "
            f"bounded by the question (RK442): the {NEAREST} entries nearest the sentence "
            "you are about to propose, in order, instead of the whole block. The order is "
            "the answer and there is no score — RK441 measured that the absolute one "
            "separates nothing, so publishing it would invite a threshold that cannot exist."
        ),
    )
    delivered_parser.add_argument("block", help="the block label, e.g. B")
    delivered_parser.add_argument(
        "--near",
        metavar="SYMPTOM",
        help=(
            f"the symptom about to be proposed: print the {NEAREST} entries nearest it "
            "rather than the block, ranked by word overlap and never refused or warned about"
        ),
    )
    delivered_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    delivered_parser.set_defaults(handler=_delivered, reads_only=True)

    reversals_parser = subcommands.add_parser(
        "reversals",
        help="the decisions this ledger already made and undid, with the argument",
        description=(
            "A revert is filed as a delivery, so a duplicate check answers `yes, shipped` "
            "about the entry that says the work did not hold. This reads the forward "
            "pointer back: every id the ledger marks superseded, the entry that superseded "
            "it, and that entry's sentence — which is the argument a fresh proposal is "
            "against. Read it before an `add`, not after. It refuses nothing: re-proposing "
            "reverted work is sometimes right, and which is a judgement the tool never makes."
        ),
    )
    reversals_parser.add_argument(
        "--id",
        dest="task_id",
        help="ask about one id: exits 1 where that id's decision was reversed",
    )
    reversals_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    reversals_parser.set_defaults(handler=_reversals, reads_only=True)


    supersede_parser = subcommands.add_parser(
        "supersede",
        help="mark one decision replaced by another, in the file that holds both",
        description=(
            "The decisions role's one departure. A roadmap line leaves by three doors and a "
            "decision leaves by being replaced, so nothing in that file is ever deleted: this "
            "appends the forward pointer to the entry that is now stale and moves its marker, "
            "in one write. Both ids have to be decisions this file already records — the "
            "replacement is written by `ship --decides` before it can replace anything — and "
            "there is no reason field, because why one decision replaced another is the "
            "argument in the entry that replaced it, one line away."
        ),
    )
    supersede_parser.add_argument("id", help="the decision being replaced, e.g. RK5")
    supersede_parser.add_argument(
        "--by",
        required=True,
        metavar="ID",
        help="the decision that replaces it, already filed in the same file",
    )
    supersede_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    supersede_parser.set_defaults(handler=_supersede)

    retire_parser = subcommands.add_parser(
        "retire",
        help="record a line leaving without shipping: replaced by another, or abandoned",
        description=(
            "The two departures that are not a ship: the work moved to another id "
            "(--superseded-by), or it is not being done. Both write one ledger line under "
            "the block it belonged to, with the forward pointer where there is one, and no "
            "design — which is what a gap here otherwise reads as, a botched hand-edit."
        ),
    )
    retire_parser.add_argument("id", help="the task leaving, e.g. RK33")
    retire_parser.add_argument(
        "--superseded-by",
        dest="superseded_by",
        metavar="ID",
        help=(
            "the id that takes the work over, which is a replacement and not an "
            "abandonment; omitted, the line is recorded as abandoned"
        ),
    )
    _reason_flag(
        retire_parser, "one sentence, the author's own: the tool never writes it" + _PIPE
    )
    retire_parser.add_argument("--json", action="store_true", help="every edit, as data")
    retire_parser.set_defaults(
        handler=_retire, reads_stdin=(Prose(dest="reason", omitted=False),)
    )

