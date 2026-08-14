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
from roadkeep.verbs.reading import _piped
from roadkeep.verbs.refusing import EXIT_GATE, EXIT_OK, EXIT_USAGE, REFUSALS, _refused



def _ship(config: Config, args: argparse.Namespace) -> int:
    try:
        shipment = ship(
            config,
            args.id,
            # Resolved by `dispatch` from what this verb's parser declares (RK1176), and no
            # longer here: a call site that reads the pipe for one argument is a call site that
            # can be written without it, which is how `--superseded-design` published a dash.
            why=args.why,
            part=args.part,
            lines=args.lines,
            superseded=args.superseded_design,
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
