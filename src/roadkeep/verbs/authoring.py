"""The verbs whose subject is one line of the roadmap (RK494).

`add`, `status`, `amend`, `restate`, `renumber` and `next-id`, plus the two doors that are
not terminal — `defer` parks a line in the store with its id, its deps and its section, and
`resume` is the return direction the ledger has none of.

Each is a thin call into :mod:`roadkeep.authoring`, :mod:`roadkeep.renumbering` or
:mod:`roadkeep.deferring`. What lives here is the argument reading, the refusal and the
answer — never a rule, which would then be enforced on one surface and not on the other.
"""

from __future__ import annotations

import argparse
import json
import sys

from roadkeep.authoring import add, amend, restate, set_status
from roadkeep.capturing import stamp
from roadkeep.config import Config
from roadkeep.deferring import Carried, defer, resume
from roadkeep.ids import derivation, highest
from roadkeep.provenance import invocation
from roadkeep.queueing import declared as declared_queue
from roadkeep.rendering import (
    _print,
    _carried_json,
    _event,
    _held_json,
    _print_dequeued,
    _event_rows,
    _staging_rows,
    _promise_json,
    _prose_file,
    _wrote_json,
)
from roadkeep.renumbering import renumber
from roadkeep.kernel.schema import width as measured_width
from roadkeep.verbs.reading import STDIN, _body_reader, _one_body, _piped
from roadkeep.verbs.refusing import EXIT_OK, EXIT_USAGE, REFUSALS, _refused



def _next_id(config: Config, args: argparse.Namespace) -> int:
    try:
        derived = derivation(config, args.family)
    except ValueError as error:
        return _refused(error)
    identifier = derived.id
    family = args.family or config.schema.prefix
    if not args.json:
        print(identifier)
        # On stderr, because stdout here is the id and nothing else: this command exists
        # to be captured in a shell, and a second line in that capture is a broken id.
        if derived.promise is not None:
            print(f"roadkeep: {derived.promise.sentence}", file=sys.stderr)
        return EXIT_OK
    top = highest(config, family)
    print(
        json.dumps(
            {
                "next": identifier,
                "prefix": family,
                "prefixes": list(config.schema.prefixes),
                "highest": None
                if top is None
                else {
                    "id": top.id,
                    "file": config.relative(top.path),
                    "line": top.lineno,
                },
                # Beside `highest` and not folded into it (RK431): that field says which
                # occurrence set the maximum, and this says the occurrence was a sentence
                # rather than a line — which is the whole difference nothing recorded.
                "promise": _promise_json(derived.promise),
                "sources": [
                    config.relative(path) for path in config.id_sources() if path.is_file()
                ],
            },
            indent=2,
        )
    )
    return EXIT_OK


def _add(config: Config, args: argparse.Namespace) -> int:
    piped = (
        args.section is not None
        and args.section_body_file is None
        and args.section_body in (None, STDIN)
    )
    # The pipe clash is `dispatch`'s, asked over what this verb's parser declares (RK1176) —
    # this had the only copy of it, which is how `ship` sent two arguments to one stream with
    # the refusal sitting one module away. What is left here is the other question: a body given
    # twice, as a string and as a path, which no declaration can answer.
    clash = _one_body("--section-body", args.section_body, args.section_body_file)
    if clash is not None:
        print(f"roadkeep: {clash}", file=sys.stderr)
        return EXIT_USAGE
    try:
        # The reader is handed over unread (RK381), so the paragraph is fetched below every
        # refusal the *line* raises — an id already spent, a `why` three words over, a block
        # nothing declares — and a pipe does not rewind. Inside the try for the reason
        # `section add` reads there: prose that is not UTF-8 raises UnicodeDecodeError, which
        # is a ValueError, and is refused with the code every other bad input gets. Gated on
        # the title, because an `add` with no rationale must never block on a pipe.
        section = None
        if args.section is not None:
            section = (
                args.section,
                _body_reader(args.section_body, args.section_body_file),
            )
        insertion = add(
            config,
            block=args.block,
            symptom=args.symptom,
            why=_piped(args.why),
            status=args.status,
            deps=args.deps,
            ref=args.ref,
            task_id=args.task_id,
            family=args.family,
            section=section,
        )
    except REFUSALS as error:
        return _refused(error)  # a SchemaError arrives here as the ValueError it is

    event = _event(
        insertion.entry.task.id, insertion.entry.task.block, insertion.document, config
    )
    # After the line is placed and the files are saved, and never a condition of either
    # (RK1141): the capture is evidence in an ignored directory, so a stamp that cannot be
    # written costs the link and not the task — `claiming.follow`'s rule for the same reason.
    stamped = (
        stamp(args.capture, insertion.entry.task.id) if args.capture else False
    )
    written = insertion.section
    # The file the write actually chose (RK230), read off the document `_with_section` left
    # rather than composed from the improvements default: a report that names the role and a
    # write that derives it are two answers, and one of them is wrong on every project that
    # declares `strategy` alone.
    prose = _prose_file(config, insertion.prose)
    if args.json:
        print(
            json.dumps(
                {
                    "id": insertion.entry.task.id,
                    # The other derived address (RK249). Reported for the reason `id` is:
                    # under `ref_scheme = "outline"` the write derives it, and the only
                    # other readings were the tail of `rendered` and the anchor inside the
                    # `needs` sentence — which is null exactly when `--section` wrote the
                    # rationale here, the composition RK93 recommends.
                    "ref": insertion.entry.task.ref,
                    "file": config.relative(config.path("roadmap")),
                    "line": insertion.lineno,
                    "rendered": insertion.rendered,
                    "length": measured_width(insertion.rendered),
                    "section": None if written is None else written.payload(prose),
                    # Not a section this write *created* (RK452): an existing outline heading
                    # stopped belonging to nobody, and a caller reading one key for both
                    # would report a paragraph that was never written.
                    "bound": None
                    if insertion.bound is None
                    else insertion.bound.payload(prose),
                    # The follow-up as data: null when the pointer already resolves, so a
                    # caller acts on a field instead of matching a sentence (RK93).
                    "needs": None
                    if insertion.needs is None
                    else _follow_up(insertion.needs, insertion.needs_role),
                    # Null on almost every add, and the whole point when it is not (RK431):
                    # the id below the one just written was a sentence, not a line.
                    "promise": _promise_json(insertion.promise),
                    # Every path this write touched, projections included (RK1129) — the same
                    # key a departure's scope carries, so a client staging one stages the other.
                    "wrote": [config.relative(one) for one in insertion.wrote],
                    # Which capture this line files, where one was named (RK1141) — null
                    # where none was, and false where the stamp could not be written, so a
                    # client tells "not asked" from "asked and did not land".
                    "capture": None if not args.capture else {
                        "path": args.capture,
                        "stamped": stamped,
                    },
                    "event": event,
                },
                indent=2,
            )
        )
        return EXIT_OK
    print(insertion.rendered)
    if written is not None:
        print(f"design   §{written.anchor} → {prose}:{written.first}  {written.words} words")
    elif insertion.needs is not None:
        # Backticked and carrying the invocation, like every other route this file composes
        # (RK476): the bare argv above is the *field*, and a line printed for a reader is the
        # form `serving._rerouted` already spells as a tool where there is no shell.
        print(
            f"needs    `{invocation()} {_follow_up(insertion.needs, insertion.needs_role)}`  "
            f"(the pointer above resolves to nothing until then)"
        )
    elif insertion.bound is not None:
        # Said, because the write touched a second file the caller did not name (RK452) —
        # and because the heading now carries an id, which is the fact `ship` and the gate
        # both read as "this design belongs to that task".
        print(
            f"bound    §{insertion.bound.anchor} → {prose}:{insertion.bound.first}  "
            f"the design was written first, so this line's id is now in its heading"
        )
    if insertion.promise is not None:
        # Beside the line and not instead of it: the `add` succeeded, and what this reports
        # is a sentence somewhere else that has just stopped being true (RK431).
        print(f"promise  {insertion.promise.sentence}")
    # The projection this write refreshed is in here (RK1129): the roadmap and the rationale are
    # files the caller named, and the README is one they did not — so a commit took the two and
    # left the third, green against the working tree and `export.stale` in a clean checkout.
    if args.capture:
        # Said either way: a stamp that did not land is the row `stats` will still count,
        # and silence about it is how a second step comes to be forgotten (RK86).
        print(
            f"capture  {args.capture} now names {insertion.entry.task.id}"
            if stamped
            else f"capture  {args.capture} could not be stamped: the line is filed, the "
            f"link is not"
        )
    _print(_staging_rows(config.relative(one) for one in insertion.wrote))
    _print(_event_rows(event, config=config))
    return EXIT_OK


def _status(config: Config, args: argparse.Namespace) -> int:
    """Write one task's marker, and say what that did to the claim on its line (RK7, RK158).

    Both registers come off the record (RK1170), the no-op reading included: a marker that did
    not move still followed its claim, so the branch belongs with the answer and not in a door.
    """
    try:
        change = set_status(config, args.id, args.marker)
    except REFUSALS as error:
        return _refused(error)

    if args.json:
        print(json.dumps(change.payload(config), indent=2))
    else:
        print(change.stated(config))
    return EXIT_OK


def _amend(config: Config, args: argparse.Namespace) -> int:
    """Correct one open line's why, deps or pointer, keeping its symptom and its id (RK65).

    Both registers come off the record (RK1170), exactly as `restate`'s do: this door chooses
    which reading to print and composes neither.
    """
    if args.why is None and args.deps is None and args.ref is None:
        print(
            "roadkeep: nothing to amend: pass --why, --dep or --ref",
            file=sys.stderr,
        )
        return EXIT_USAGE
    try:
        amended = amend(
            config,
            args.id,
            why=_piped(args.why),
            deps=args.deps,
            ref=args.ref,
            lines=args.lines,
        )
    except REFUSALS as error:
        return _refused(error)

    if args.json:
        print(json.dumps(amended.payload(config), indent=2))
    else:
        print(amended.stated(config))
    return EXIT_OK


def _restate(config: Config, args: argparse.Namespace) -> int:
    """Correct one open line's symptom, keeping its id, its deps and its section (RK178).

    Both registers come off the record (RK1170): a write verb's answer is what the transaction
    produced, and this door only chooses which reading to print.
    """
    try:
        restated = restate(
            config, args.id, args.symptom, lines=args.lines, typo=args.typo
        )
    except REFUSALS as error:
        return _refused(error)

    if args.json:
        print(json.dumps(restated.payload(config), indent=2))
    else:
        print(restated.stated(config))
    return EXIT_OK


def _renumber(config: Config, args: argparse.Namespace) -> int:
    try:
        moved = renumber(config, args.id, args.to)
        wrote = moved.save()
    except REFUSALS as error:
        return _refused(error)

    where = config.relative(config.path(moved.role))
    prose = config.relative(config.path("improvements")) if config.has("improvements") else ""
    # Read back when this write did not touch the roadmap — a line moved in the deferred
    # store still owes the same event line (RK38), and the file is already saved.
    event = _event(
        moved.to,
        moved.entry.task.block,
        moved.documents.get("roadmap") or config.document("roadmap"),
        config,
    )
    if args.json:
        print(
            json.dumps(
                {
                    "id": moved.task_id,
                    "to": moved.to,
                    "role": moved.role,
                    "file": where,
                    "line": moved.lineno,
                    "rendered": moved.rendered,
                    "section": None
                    if moved.section is None
                    else moved.section.payload(prose),
                    # The nested headings that carried the old address, as they now read.
                    "subsections": list(moved.subsections),
                    # The lines this write changed on the author's behalf, because which
                    # of two collided ids a dep meant is not a fact any file holds.
                    "moved": list(moved.moved),
                    "refreshed": list(moved.refreshed),
                    "files": sorted(config.relative(config.path(role)) for role in moved.documents),
                    "claimed": _held_json(moved.claim),
                    **_wrote_json(config, wrote),
                    "event": event,
                },
                indent=2,
            )
        )
        return EXIT_OK

    print(f"{moved.task_id} → {moved.to}  {where}:{moved.lineno}")
    print(f"  {moved.rendered}")
    if moved.section is not None:
        print(f"  section  §{moved.to} → {prose}:{moved.section.first}")
    if moved.subsections:
        print(f"  nested   {', '.join('§' + a for a in moved.subsections)} (the id's own numbering)")
    if moved.moved:
        print(f"  deps     {', '.join(moved.moved)} now name {moved.to} — confirm each meant this line")
    if moved.refreshed:
        print(f"  derived  {', '.join(moved.refreshed)} (dep annotations re-derived)")
    if moved.claim is not None:
        # The half the files do not hold (RK156): the worker holding this will next ask for it
        # by a number that no longer exists, and that it is still theirs is what to say.
        print(f"  claimed  the claim taken {moved.claim.since} ago moved with it")
    _print(_staging_rows(config.relative(one) for one in wrote))
    _print(_event_rows(event, "  ", config=config))
    return EXIT_OK


def _follow_up(anchor: str, role: str | None) -> str:
    """The `section add` that closes a pointer `add` just created (RK93, RK197).

    `--role` only where it is not the default, which keeps the sentence every project sees
    the one it already saw — and makes the exception the case that needs it: a project whose
    only prose file is the strategy one would otherwise be handed `section add`'s default and
    a role it does not declare, which is a follow-up that cannot run.
    """
    named = "" if role in (None, "improvements") else f" --role {role}"
    return f"section add {anchor} --title …{named}"


def _carried_line(config: Config, carried: Carried) -> str:
    """The one line saying where a paused design stayed (RK229).

    `kept in <file>` only where a file holds it. An absence spells itself instead of being
    dressed as a location: "kept in IMPROVEMENTS.md" about a section that is not there sends
    a reader to look, and the pause is right either way.
    """
    if carried.role is None:
        return f"{carried.anchor} — {carried.absence}"
    return f"{carried.anchor} kept in {config.relative(config.path(carried.role))}"


def _defer(config: Config, args: argparse.Namespace) -> int:
    try:
        pause = defer(config, args.id, reason=_piped(args.reason))
        wrote = pause.save()
    except REFUSALS as error:
        return _refused(error)

    roadmap = config.relative(config.path("roadmap"))
    store = config.relative(config.path("deferred"))
    block = pause.store.entry.task.block
    event = _event(pause.task_id, block, pause.roadmap, config)
    if args.json:
        print(
            json.dumps(
                {
                    "id": pause.task_id,
                    "marker": pause.marker,
                    "deferred": {
                        "file": store,
                        "line": pause.store.lineno,
                        "rendered": pause.store.rendered,
                    },
                    "roadmap": {"file": roadmap, "removed": pause.removed_from},
                    "carried": _carried_json(config, pause.carried),
                    "dequeued": pause.dequeued,
                    "dependents": list(pause.dependents),
                    "refreshed": list(pause.refreshed),
                    **_wrote_json(config, wrote),
                    "event": event,
                },
                indent=2,
            )
        )
        return EXIT_OK

    print(f"{pause.task_id} {pause.marker} {store}:{pause.store.lineno} under Block {block}")
    print(f"  removed  {roadmap}:{pause.removed_from}")
    if pause.carried is not None:
        # Named, because every other door that moves a line deletes this section: silence
        # about a design that was kept reads exactly like the deletion (RK6). The *file* is
        # the pause's answer and never this line's (RK229) — composing it here from the
        # improvements default is what named a path a strategy-only project does not declare.
        print(f"  carried  {_carried_line(config, pause.carried)}")
    if pause.dependents:
        print(f"  still    {', '.join(pause.dependents)} name {pause.task_id}")
    if pause.refreshed:
        print(f"  derived  {', '.join(pause.refreshed)} (dep annotations re-derived)")
    _print_dequeued(pause.dequeued)
    _print(_staging_rows(config.relative(one) for one in wrote))
    _print(_event_rows(event, "  ", config=config))
    return EXIT_OK


def _resume(config: Config, args: argparse.Namespace) -> int:
    try:
        resumption = resume(config, args.id, marker=args.marker)
        wrote = resumption.save()
    except REFUSALS as error:
        return _refused(error)

    roadmap = config.relative(config.path("roadmap"))
    store = config.relative(config.path("deferred"))
    # The line this call placed, or the one already there on a reconciling call (RK1086):
    # the shape no longer pretends the second is a placement, so the printer asks for the
    # one it is going to describe rather than reading a field that had to be faked.
    placed = resumption.placed
    standing = placed or config.document("roadmap").by_id().get(resumption.task_id)
    block = standing.task.block if standing else ""
    event = _event(resumption.task_id, block, resumption.roadmap, config)
    if args.json:
        print(
            json.dumps(
                {
                    "id": resumption.task_id,
                    "marker": resumption.marker,
                    # Null on a reconciling call, which places no line — a `line` there
                    # would be an address for a write nobody made (RK1086).
                    "roadmap": None
                    if placed is None
                    else {
                        "file": roadmap,
                        "line": placed.lineno,
                        "rendered": placed.raw,
                    },
                    "deferred": {"file": store, "removed": resumption.removed_from},
                    "was": resumption.was,
                    # Which of the two acts this was (RK1083): a reconciliation removes the
                    # store's stale copy and places nothing, so `roadmap.line` is where the
                    # line already was rather than where one landed.
                    "reconciled": resumption.reconciled,
                    "refreshed": list(resumption.refreshed),
                    # The half of the pause this does not undo (RK327): the entry the
                    # pause removed is the author's to put back, because where in the
                    # order it belonged is not a fact the store kept.
                    "requeue": _requeue(config, resumption.task_id),
                    **_wrote_json(config, wrote),
                    "event": event,
                },
                indent=2,
            )
        )
        return EXIT_OK

    # Two acts under one verb, said apart (RK1083). `ship` answers the same shape the same
    # way — `RK1 closed` against `RK1 →` — because a caller holding an id should not have to
    # know which of two states the files are in, and the *output* is where they find out.
    if resumption.reconciled:
        print(
            f"{resumption.task_id} reconciled  {store}:{resumption.removed_from} removed, "
            f"already {resumption.marker} in {roadmap}:{standing.lineno}"
        )
        print("  roadmap  untouched: the open line is what the files should say")
    else:
        print(
            f"{resumption.task_id} {resumption.marker} {roadmap}:{placed.lineno} "
            f"under Block {block}"
        )
        print(f"  removed  {store}:{resumption.removed_from}")
    if resumption.was is not None:
        # The last time the reason is visible: what comes back is a design, and the pause
        # it went through is history the commit states rather than the line.
        print(f"  was      set aside: {resumption.was}")
    if resumption.refreshed:
        print(f"  derived  {', '.join(resumption.refreshed)} (dep annotations re-derived)")
    follow = _requeue(config, resumption.task_id)
    if follow is not None:
        print(f"  requeue  {follow}")
    _print(_staging_rows(config.relative(one) for one in wrote))
    _print(_event_rows(event, "  ", config=config))
    return EXIT_OK


def _requeue(config: Config, task_id: str) -> str | None:
    """The `priority add` a resumed line may want, where this project has a queue (RK327).

    Offered and never done. `defer` took the entry out because a paused line is one `pick`
    can never offer; what it could not keep is **where in the order it sat**, the store
    holding a line and not a rank — so a resume that re-queued would be choosing a position
    nobody stated. Silent where no heading declares a section, which is most projects: a
    follow-up naming a list that does not exist is a command that cannot run.
    """
    try:
        queue = declared_queue(config)
    except (KeyError, OSError):  # a roadmap this command already reported on
        return None
    if queue.declared_in != "roadmap" or task_id in queue.tokens:
        return None
    return (
        f"`{invocation()} priority add {task_id}` if it goes back in the order — the "
        f"pause took it out, and where it sat is not something the store kept"
    )
