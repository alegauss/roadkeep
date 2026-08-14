"""The verbs whose subject is one line of the roadmap (RK494).

`add`, `status`, `amend`, `restate`, `renumber` and `next-id`, plus the two doors that are
not terminal — `defer` parks a line in the store with its id, its deps and its section, and
`resume` is the return direction the ledger has none of.

Each is a thin call into :mod:`roadkeep.authoring`, :mod:`roadkeep.renumbering` or
:mod:`roadkeep.deferring`. What lives here is the argument reading, the refusal and the
answer — never a rule, which would then be enforced on one surface and not on the other.

**And no longer the answer either** (RK1170): every write renders both registers off its own
record, so each door is the call, the save and a choice of reading. `next-id` renders three, the
id being stdout a shell captures and the promise a sentence that must not reach it.
"""

from __future__ import annotations

import argparse
import json
import sys

from roadkeep.authoring import add, amend, restate, set_status
from roadkeep.capturing import stamp
from roadkeep.config import Config
from roadkeep.deferring import defer, resume
from roadkeep.ids import derivation
from roadkeep.renumbering import renumber
from roadkeep.verbs.reading import _body_reader, _one_body, _piped
from roadkeep.verbs.refusing import EXIT_OK, EXIT_USAGE, REFUSALS, _refused



def _next_id(config: Config, args: argparse.Namespace) -> int:
    try:
        derived = derivation(config, args.family)
    except ValueError as error:
        return _refused(error)
    family = args.family or config.schema.prefix
    # Three streams and not two (RK1170): the id is stdout because this command exists to be
    # captured in a shell, and the promise is stderr because a second line in that capture is
    # a broken id — so the branch is which reading, never whether to add a sentence.
    if args.json:
        print(json.dumps(derived.payload(config, family), indent=2))
        return EXIT_OK
    print(derived.stated())
    for note in derived.notice():
        print(note, file=sys.stderr)
    return EXIT_OK


def _add(config: Config, args: argparse.Namespace) -> int:
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

    # After the line is placed and the files are saved, and never a condition of either
    # (RK1141): the capture is evidence in an ignored directory, so a stamp that cannot be
    # written costs the link and not the task — `claiming.follow`'s rule for the same reason.
    stamped = (
        stamp(args.capture, insertion.entry.task.id) if args.capture else False
    )
    if args.json:
        print(json.dumps(insertion.addition(config, args.capture, stamped), indent=2))
    else:
        print(insertion.added(config, args.capture, stamped))
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
    """Move one line to a free id, with its section, its subsections and its claim (RK74).

    Both registers come off the record (RK1170); `wrote` is passed because saving is this
    door's step, so the paths are a fact about the call and not about the transaction.
    """
    try:
        moved = renumber(config, args.id, args.to)
        wrote = moved.save()
    except REFUSALS as error:
        return _refused(error)

    if args.json:
        print(json.dumps(moved.payload(config, wrote), indent=2))
    else:
        print(moved.stated(config, wrote))
    return EXIT_OK


def _defer(config: Config, args: argparse.Namespace) -> int:
    """Set one open line aside in the store, keeping its design where it is (RK229, RK327).

    Both registers come off the record (RK1170); `wrote` is passed because saving is this
    door's step, so the paths are a fact about the call and not about the transaction.
    """
    try:
        pause = defer(config, args.id, reason=_piped(args.reason))
        wrote = pause.save()
    except REFUSALS as error:
        return _refused(error)

    if args.json:
        print(json.dumps(pause.payload(config, wrote), indent=2))
    else:
        print(pause.stated(config, wrote))
    return EXIT_OK


def _resume(config: Config, args: argparse.Namespace) -> int:
    try:
        resumption = resume(config, args.id, marker=args.marker)
        wrote = resumption.save()
    except REFUSALS as error:
        return _refused(error)

    if args.json:
        print(json.dumps(resumption.payload(config, wrote), indent=2))
    else:
        print(resumption.stated(config, wrote))
    return EXIT_OK


