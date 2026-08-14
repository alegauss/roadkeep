"""The verbs a task leaves by, and the two reads only the ledger can answer (RK494).

`ship`, `retire` and the `record` family write the terminal entry; `delivered` and
`reversals` read it back — what a block already shipped, and which of those deliveries was
later undone. Filed by their subject, an entry in the ledger, and not by whether they write
one: a proposal is checked against both, and the two reads come before it, not after.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence

from roadkeep.backlog import Backlog, Stage
from roadkeep.config import Config
from roadkeep.kernel.document import declares, shading
from roadkeep.provenance import invocation
from roadkeep.ranking import NEAREST, nearest
from roadkeep.remaining import declared
from roadkeep.rendering import (
    _print_staging,
    _wrote_json,
    _event,
    _print_cited,
    _print_dequeued,
    _print_emptied,
    _print_event,
    _print_scope,
    _prose_file,
    _scope_json,
)
from roadkeep.reverting import reversals
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
            why=_piped(args.why),
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

    roadmap = config.relative(config.path("roadmap"))
    ledger = config.relative(config.path("changelog"))
    block = shipment.ledger.entry.task.block
    event = _event(shipment.task_id, block, shipment.roadmap, config)
    if args.json:
        print(
            json.dumps(
                {
                    "id": shipment.task_id,
                    "changelog": {
                        "file": ledger,
                        "line": shipment.ledger.lineno,
                        "rendered": shipment.ledger.rendered,
                    },
                    "roadmap": {"file": roadmap, "removed": shipment.removed_from},
                    "improvements": {
                        # The file the drop actually rewrote, which is whichever prose role
                        # declared the anchor (RK196) — not always the improvements file.
                        "file": _prose_file(config, shipment.prose),
                        "dropped": None
                        if shipment.dropped is None
                        else {
                            "anchor": shipment.dropped.anchor,
                            "title": shipment.dropped.title,
                            "first": shipment.dropped.first,
                            "last": shipment.dropped.last,
                        },
                        "nested": list(shipment.nested),
                        "cited": list(shipment.cited),
                        "emptied": shipment.emptied,
                        "kept": shipment.kept,
                        # What the deleted design was overtaken by (RK310), beside the
                        # anchor it was written under: the two are one fact, and a caller
                        # reading them off the rendered sentence would be parsing prose.
                        "superseded": shipment.superseded,
                    },
                    "refreshed": list(shipment.refreshed),
                    # What left the order with the line (RK327), named because a plan
                    # that silently got shorter is a change with no sentence about it.
                    "dequeued": shipment.dequeued,
                    "scope": _scope_json(shipment.scope, wrote),
                    "event": event,
                },
                indent=2,
            )
        )
        return EXIT_OK

    print(f"{shipment.task_id} → {ledger}:{shipment.ledger.lineno} under Block {block}")
    print(f"  removed  {roadmap}:{shipment.removed_from}")
    if shipment.dropped is not None:
        print(f"  dropped  {shipment.dropped} from {_prose_file(config, shipment.prose)}")
        if shipment.nested:
            print(
                f"  nested   {', '.join(f'§{a}' for a in shipment.nested)} went with it"
            )
        _print_cited(shipment.cited)
        _print_emptied(shipment.emptied)
    else:
        print(f"  kept     nothing dropped: {shipment.kept}")
    # Beside the drop rather than inside it (RK310): the deletion is what makes the clause
    # the only surviving trace, and it is reported even where the section stayed — a design
    # another open line still points at can be just as overtaken as one that went.
    if shipment.superseded is not None:
        print(f"  overtook the design it read: {shipment.superseded}")
    if shipment.refreshed:
        print(f"  derived  {', '.join(shipment.refreshed)} (dep annotations re-derived)")
    _print_dequeued(shipment.dequeued)
    # Last before the event line, because it is about the commit this ship precedes rather
    # than about the three edits above it (RK294).
    _print_scope(shipment.scope, wrote)
    _print_event(event, "  ", config=config, standing=True)
    return EXIT_OK


def _partly(config: Config, partial: Partial, args: argparse.Namespace) -> int:
    """Half of a task recorded, with its roadmap line still open (RK121)."""
    roadmap = config.relative(config.path("roadmap"))
    ledger = config.relative(config.path("changelog"))
    block = partial.ledger.entry.task.block
    event = _event(partial.task_id, block, partial.roadmap, config)
    if args.json:
        print(
            json.dumps(
                {
                    "id": partial.task_id,
                    "part": partial.part,
                    "changelog": {
                        "file": ledger,
                        "line": partial.ledger.lineno,
                        "rendered": partial.ledger.rendered,
                    },
                    "roadmap": {
                        "file": roadmap,
                        "line": partial.roadmap.by_id()[partial.task_id].lineno,
                        "status": partial.status,
                        "open": True,
                    },
                    "refreshed": list(partial.refreshed),
                    "event": event,
                },
                indent=2,
            )
        )
        return EXIT_OK

    print(
        f"{partial.task_id} ({partial.part}) → {ledger}:{partial.ledger.lineno} "
        f"under Block {block}"
    )
    print(
        f"  open     {roadmap}:{partial.roadmap.by_id()[partial.task_id].lineno} "
        f"{partial.status} — the rest of it is still a task"
    )
    print(f"  finish   {invocation()} ship {partial.task_id}  (drops the qualifier)")
    if partial.refreshed:
        print(f"  derived  {', '.join(partial.refreshed)} (dep annotations re-derived)")
    _print_event(event, "  ", config=config, standing=True)
    return EXIT_OK


def _closed(
    config: Config, closure: Closure, args: argparse.Namespace, wrote: Sequence[str] = ()
) -> int:
    """A roadmap line closed against an entry the ledger already had (RK62)."""
    roadmap = config.relative(config.path("roadmap"))
    ledger = config.relative(config.path("changelog"))
    event = _event(closure.task_id, closure.recorded.task.block, closure.remaining, config)
    if args.json:
        print(
            json.dumps(
                {
                    "id": closure.task_id,
                    # The file the line actually came out of (RK1088), read off the
                    # closure rather than assumed to be the roadmap: the act is the same
                    # against a different pair, and a payload that named one file by having
                    # only one to name is one a second act would quietly make wrong.
                    "closed": {
                        "file": config.relative(config.path(closure.removed_in)),
                        "role": closure.removed_in,
                        "removed": closure.removed_from,
                    },
                    "recorded": {
                        "file": ledger,
                        "line": closure.recorded.lineno,
                        "marker": closure.marker,
                        "written": False,
                    },
                    "improvements": {
                        "file": _prose_file(config, closure.prose),
                        "dropped": None
                        if closure.dropped is None
                        else {"anchor": closure.dropped.anchor, "title": closure.dropped.title},
                        "nested": list(closure.nested),
                        "cited": list(closure.cited),
                        "emptied": closure.emptied,
                        "kept": closure.kept,
                    },
                    "refreshed": list(closure.refreshed),
                    "dequeued": closure.dequeued,
                    "scope": _scope_json(closure.scope, wrote),
                    "event": event,
                },
                indent=2,
            )
        )
        return EXIT_OK

    print(
        f"{closure.task_id} closed  "
        f"{config.relative(config.path(closure.removed_in))}:{closure.removed_from} removed, "
        f"already {closure.marker} in {ledger}:{closure.recorded.lineno}"
    )
    print("  ledger   untouched: the entry was already there")
    if closure.dropped is not None:
        print(f"  dropped  {closure.dropped} from {_prose_file(config, closure.prose)}")
        if closure.nested:
            print(f"  nested   {', '.join(f'§{a}' for a in closure.nested)} went with it")
        _print_cited(closure.cited)
        _print_emptied(closure.emptied)
    if closure.refreshed:
        print(f"  derived  {', '.join(closure.refreshed)} (dep annotations re-derived)")
    _print_dequeued(closure.dequeued)
    _print_scope(closure.scope, wrote)
    _print_event(event, "  ", config=config)
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

    ledger = config.relative(config.path("changelog"))
    block = entry.ledger.entry.task.block  # as the file reads it back, not as it was typed
    # The event's block state is the *roadmap's*, as it is for every other mutator: a hook
    # asking "is Block B finished" is asking about open work, and a record adds none.
    event = _event(entry.task_id, block, entry.roadmap, config)
    if args.json:
        print(
            json.dumps(
                {
                    "id": entry.task_id,
                    "marker": entry.marker,
                    "changelog": {
                        "file": ledger,
                        "line": entry.ledger.lineno,
                        "rendered": entry.ledger.rendered,
                    },
                    "roadmap": {"touched": bool(entry.refreshed)},
                    "refreshed": list(entry.refreshed),
                    # The other half of the transaction (RK395): null on every record that
                    # supersedes nothing, and the earlier entry as it now reads otherwise.
                    "superseded": None
                    if entry.superseded is None
                    else {
                        "id": entry.superseded.task.id,
                        "line": entry.superseded.lineno,
                        "rendered": entry.superseded.raw,
                    },
                    # The sentence that already named this id, where `--id` was allowed
                    # because no line held it (RK1051): null on every other record.
                    "mentioned": None
                    if entry.mentioned is None
                    else {
                        "file": config.relative(entry.mentioned.path),
                        "line": entry.mentioned.lineno,
                    },
                    "event": event,
                    **_wrote_json(config, wrote),
                },
                indent=2,
            )
        )
        return EXIT_OK

    print(
        f"{entry.task_id} {entry.marker} {ledger}:{entry.ledger.lineno} "
        f"under Block {block}"
    )
    # Said out loud, because the absence is the whole point: a reader of this output has to
    # be able to tell "there was no line" from "the roadmap edit was forgotten". About the
    # write and not about the work (RK1050, RK1051): this door is also how a task that *was*
    # planned gets the entry it is missing, and `planned never` was a claim about the wrong
    # thing on exactly the write that repairs one.
    print("  roadmap  no line to remove: this door writes the entry and nothing else")
    if entry.mentioned is not None:
        # The citation the occupancy check used to refuse over (RK1051). Printed rather than
        # refused *and* rather than swallowed: an entry that keeps a sentence's promise and
        # one that collides with it are the same write, and only the author can tell them
        # apart — so the address is given and the judgement is left where it belongs.
        print(
            f"  cited    {config.relative(entry.mentioned.path)}:{entry.mentioned.lineno} "
            f"already names {entry.task_id}: no line held it, so this entry is what it "
            f"now points at"
        )
    if entry.superseded is not None:
        # The edit the caller did not spell, printed where every other derived write is: the
        # forward pointer is this command's fact, and a reviewer reads the diff against it.
        print(
            f"  pointed  {ledger}:{entry.superseded.lineno} "
            f"{entry.superseded.task.id} now names {entry.task_id} as what replaced it"
        )
    if entry.refreshed:
        print(f"  derived  {', '.join(entry.refreshed)} (dep annotations re-derived)")
    _print_staging(config.relative(one) for one in wrote)
    _print_event(event, "  ", config=config)
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

    where = config.relative(config.path("changelog"))
    if args.json:
        print(
            json.dumps(
                {
                    "id": corrected.task_id,
                    "file": where,
                    # The line it was already on, because not moving it is the claim.
                    "line": corrected.lineno,
                    **_wrote_json(config, wrote),
                    "rendered": corrected.rendered,
                    "changed": list(corrected.changed),
                    # The lines under the bullet this write put back (RK1049): `rendered`
                    # is the first line, so a reader diffing the JSON cannot otherwise
                    # tell a kept tail from a collapsed one.
                    "below": corrected.below,
                    # The id that reverted this one, or null (RK1042, RK1052): read off the
                    # ledger as it stood, since correcting the sentence is what can remove
                    # the mark it is read from.
                    "undone_by": undone_by,
                },
                indent=2,
            )
        )
        return EXIT_OK

    # `below` as well as `changed` (RK1049): a correction that moved no field and rewrote
    # four paragraphs under the bullet is a write, and calling it unchanged here would be
    # the collapse that task closed, reported as a no-op.
    if not corrected.changed and not corrected.below:
        print(f"{corrected.task_id} unchanged: the entry already reads that way")
        return EXIT_OK
    print(
        f"{corrected.task_id} amended  {where}:{corrected.lineno}  "
        f"({', '.join(corrected.changed) or 'tail'})"
    )
    print(f"  {corrected.rendered}")
    if undone_by is not None:
        # The moment the clause matters most (RK1052): the author is composing an outcome
        # for work a later entry says did not hold, and `delivered` would have told them.
        # The two surfaces RK1042 joined are one fact again, said in the same words.
        print(
            f"  undone   by {undone_by}: the decision this entry records was reverted, "
            f"so the outcome being corrected is one that did not hold"
        )
    if corrected.below:
        # Said out loud for the reason the absence is (RK1049): the line printed above is
        # the whole of what this command can render, and a reader who cannot see that four
        # paragraphs are still under it has to diff the file to learn whether they survived.
        print(
            f"  kept     {corrected.below} continuation line(s) under the bullet, "
            f"verbatim: no field holds them"
        )
    _print_staging(config.relative(one) for one in wrote)
    return EXIT_OK


def _record_move(config: Config, args: argparse.Namespace) -> int:
    try:
        refiled = move_record(config, args.id, to_block=args.to_block)
        # Nothing is written where the entry already sits under that heading, so nothing is
        # staged either: an empty list is the honest answer and `_print_staging` says nothing.
        wrote = refiled.save() if refiled.moved else ()
    except REFUSALS as error:
        return _refused(error)

    where = config.relative(config.path("changelog"))
    # The roadmap is read and never written (RK67's rule, for the same reason): a block is
    # where an entry is filed, so re-filing one leaves every open line exactly as it was.
    event = _event(refiled.task_id, refiled.to_block, config.document("roadmap"), config)
    if args.json:
        print(
            json.dumps(
                {
                    "id": refiled.task_id,
                    "file": where,
                    # Both, because the entry does not keep its number and a payload naming
                    # one position would be the pretence this verb exists not to make.
                    "from": {"block": refiled.from_block, "line": refiled.from_line},
                    "to": {"block": refiled.to_block, "line": refiled.lineno},
                    **_wrote_json(config, wrote),
                    "moved": refiled.moved,
                    "rendered": refiled.rendered,
                    "roadmap": {"touched": False},
                    "event": event,
                },
                indent=2,
            )
        )
        return EXIT_OK

    if not refiled.moved:
        print(
            f"{refiled.task_id} unchanged: the ledger already files it under "
            f"Block {refiled.to_block}"
        )
        return EXIT_OK
    print(
        f"{refiled.task_id} moved  Block {refiled.from_block} → Block {refiled.to_block}  "
        f"{where}:{refiled.from_line} → :{refiled.lineno}"
    )
    print(f"  {refiled.rendered}")
    print("  roadmap  untouched: a block is where an entry is filed, not what it records")
    _print_event(event, "  ", config=config)
    _print_staging(config.relative(one) for one in wrote)
    return EXIT_OK


def _record_renumber(config: Config, args: argparse.Namespace) -> int:
    try:
        moved = readdress_record(config, args.id, lineno=args.line, to=args.to)
        wrote = moved.save()
    except REFUSALS as error:
        return _refused(error)

    ledger = config.relative(config.path("changelog"))
    if args.json:
        print(
            json.dumps(
                {
                    "id": moved.task_id,
                    **_wrote_json(config, wrote),
                    "to": moved.to,
                    "file": ledger,
                    # The entry does not move: it keeps its line, so the ledger still reads
                    # in the order work landed and the diff is the number.
                    "line": moved.lineno,
                    "rendered": moved.rendered,
                    "kept": {"line": moved.kept, "marker": moved.kept_marker},
                    "roadmap": {"touched": False},
                },
                indent=2,
            )
        )
        return EXIT_OK

    print(f"{moved.task_id} → {moved.to}  {ledger}:{moved.lineno}")
    print(f"  {moved.rendered}")
    print(
        f"  kept     {moved.kept_marker} line {moved.kept} still carries {moved.task_id}: "
        f"every annotation elsewhere was written about that delivery"
    )
    _print_staging(config.relative(one) for one in wrote)
    return EXIT_OK


def _record_drop(config: Config, args: argparse.Namespace) -> int:
    try:
        dropped = drop_record(config, args.id, lineno=args.line)
        wrote = dropped.save()
    except REFUSALS as error:
        return _refused(error)

    ledger = config.relative(config.path("changelog"))
    # The roadmap is read, never written (RK67): the event's block state is the *roadmap's*
    # for every mutator, and a duplicate entry removed leaves open work exactly as it was.
    event = _event(dropped.task_id, dropped.block, config.document("roadmap"), config)
    if args.json:
        print(
            json.dumps(
                {
                    "id": dropped.task_id,
                    "changelog": {
                        "file": ledger,
                        "removed": dropped.removed_from,
                        "marker": dropped.marker,
                    },
                    "kept": {"line": dropped.kept, "marker": dropped.kept_marker},
                    "roadmap": {"touched": False},
                    **_wrote_json(config, wrote),
                    "event": event,
                },
                indent=2,
            )
        )
        return EXIT_OK

    print(
        f"{dropped.task_id} {dropped.marker} {ledger}:{dropped.removed_from} removed, "
        f"duplicate of {ledger}:{dropped.kept}"
    )
    print(f"  kept     {dropped.kept_marker} line {dropped.kept}: where the decision was found")
    if dropped.kept_marker != dropped.marker:
        # Two entries that disagree about the door are not one decision written twice, and
        # the later one is gone: which marker the ledger now states has to be said out loud.
        print(
            f"  differed the entry removed said {dropped.marker}, so the ledger now states "
            f"{dropped.kept_marker}"
        )
    print("  roadmap  untouched: an id the ledger still records changes no annotation")
    _print_event(event, "  ", config=config)
    _print_staging(config.relative(one) for one in wrote)
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
    if args.json:
        print(
            json.dumps(
                {
                    "root": config.root.as_posix(),
                    "asked": args.task_id,
                    "reversed": [
                        {
                            "undone": one.undone,
                            "by": one.by,
                            "line": one.undone_entry.lineno,
                            "why": one.why,
                        }
                        for one in found
                    ],
                },
                indent=2,
            )
        )
    else:
        for one in found:
            print(str(one))
        where = config.relative(config.path("changelog"))
        print(
            f"{len(found)} reversal(s) in {where}"
            + (f" for {args.task_id}" if args.task_id else "")
        )
    return EXIT_GATE if args.task_id and found else EXIT_OK


def _retire(config: Config, args: argparse.Namespace) -> int:
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

    ledger = config.relative(config.path("changelog"))
    roadmap = config.relative(config.path("roadmap"))
    block = departure.ledger.entry.task.block
    event = _event(departure.task_id, block, departure.roadmap, config)
    if args.json:
        print(
            json.dumps(
                {
                    "id": departure.task_id,
                    "marker": departure.marker,
                    "superseded_by": args.superseded_by,
                    "replacement_in": departure.replacement_in,
                    "changelog": {
                        "file": ledger,
                        "line": departure.ledger.lineno,
                        "rendered": departure.ledger.rendered,
                    },
                    "roadmap": {"file": roadmap, "removed": departure.removed_from},
                    "dropped": None
                    if departure.dropped is None
                    else departure.dropped.anchor,
                    "dependents": list(departure.dependents),
                    "refreshed": list(departure.refreshed),
                    "scope": _scope_json(departure.scope, wrote),
                    "event": event,
                },
                indent=2,
            )
        )
        return EXIT_OK

    print(
        f"{departure.task_id} {departure.marker} {ledger}:{departure.ledger.lineno} "
        f"under Block {block}"
    )
    print(f"  removed  {roadmap}:{departure.removed_from}")
    if departure.replacement_in is not None:
        # Where the replacement was found, because the three files are three different
        # promises (RK244): shipped is a supersession already delivered, open is one being
        # worked, and paused is one waiting on a `resume` nobody is holding.
        print(
            f"  found    {args.superseded_by} in "
            f"{config.relative(config.path(departure.replacement_in))}"
        )
    if departure.dropped is not None:
        print(f"  dropped  {departure.dropped} from {_prose_file(config, departure.prose)}")
    if departure.dependents:
        # Reported, not refused: a supersession is legitimate and these lines are the
        # author's next edit. `deps` now resolves them as unresolvable, not as satisfied.
        print(f"  still    {', '.join(departure.dependents)} name {departure.task_id}")
    # A retirement is committed exactly as a ship is, and it releases the same claim (RK294).
    _print_scope(departure.scope, wrote)
    _print_event(event, "  ", config=config, standing=True)
    return EXIT_OK
