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
from roadkeep.serving import Prose
from roadkeep.verbs.declaring import (
    _BODY_FILE,
    _JSON_HELP,
    _PIPE,
    _marker_flag,
    _reason_flag,
    withheld,
)
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
            requires=args.requires,
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
    # The third copy of the argument RK1396 was about, resolved the same way: this one is the
    # path the *capture offer* printed, so a project-relative address read from the process's
    # directory left the line filed and the row it was meant to clear still open — the one
    # failure this stamp is not allowed to have, being the half that costs nothing to get right.
    stamped = (
        stamp(config.locate(args.capture), insertion.entry.task.id) if args.capture else False
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
    # `--requires` counts (RK1311). The flag is in the parser, documented in the help two lines
    # above this message, and works — and the guard that decides whether anything was asked for
    # did not know it. So the only way to attach a requirement to a line that already exists
    # was to pass a field that is not changing: measured in pportal over five lines, where one
    # of them meant re-sending a `why` that then failed the line limit, because the annotation
    # had made the line longer. Two round trips for a field the verb has.
    if args.why is None and args.deps is None and args.ref is None and not args.requires:
        # Named only where the project declares a vocabulary (L6): a flag offered here and
        # refused by `requires.unknown` one call later is the detour RK16 keeps out of a
        # remedy, and a project that declared none has no requirement to attach.
        fields = "--why, --dep or --ref"
        if config.schema.requirements:
            fields = "--why, --dep, --requires or --ref"
        print(f"roadkeep: nothing to amend: pass {fields}", file=sys.stderr)
        return EXIT_USAGE
    try:
        amended = amend(
            config,
            args.id,
            why=_piped(args.why),
            deps=args.deps,
            requires=args.requires,
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


def declare_lines(subcommands: argparse._SubParsersAction) -> None:
    """This module's verbs, declared where their handlers are (RK1171).

    `build_parser` called forty-nine blocks like these in a row; what it calls now is an index
    over the modules that own them. The move is what RK1169 and RK1170 bought: the flags a verb
    declares, the reasons it withholds and the record it answers with are one file's, so a
    change to any of them is one file's too.

    The order inside is `build_parser`'s own, which is where these blocks sat.
    """
    next_id_parser = subcommands.add_parser(
        "next-id",
        help="the next unused task id, one past the highest anywhere",
        description=(
            "Print the next id. Never the first unused number: a retired id is never "
            "reused, so filling its hole would make two tasks share it in the history."
        ),
    )
    next_id_parser.add_argument(
        "--prefix",
        dest="family",
        help=(
            "count in this track (default: the first declared) — two tracks sharing a "
            "counter are two tracks that renumber each other"
        ),
    )
    next_id_parser.add_argument(
        "--json",
        action="store_true",
        help="include where the highest id was found, so the answer can be audited",
    )
    # `reads_only` is what keeps a command out of the write lock (RK117), declared here
    # beside `tolerates_config_error` because both are claims about the command rather than
    # about its arguments. Absent means locked, so a new command is serialised until someone
    # says it only reads — and `next-id` only reads: the race is not in the scan, it is in
    # the span between this answer and the `add` that spends it.
    next_id_parser.set_defaults(handler=_next_id, reads_only=True)

    add_parser = subcommands.add_parser(
        "add",
        help="insert a task line under its block, refusing the fields at input",
        description=(
            "Compose, validate and insert one task line. Nothing is written unless "
            "every field passes: a limit reported after the prose exists is a limit "
            "discovered too late to save the tokens it was meant to save. With "
            "--section the rationale the line points at is written in the same "
            "transaction; without it, the follow-up the pointer needs is named."
        ),
    )
    add_parser.add_argument("--block", required=True, help="the block label, e.g. B")
    add_parser.add_argument(
        "--symptom", required=True, help="what does not work — a phrase, never a fix"
    )
    add_parser.add_argument(
        "--why", required=True, help="one sentence, ending in a stop" + _PIPE
    )
    add_parser.add_argument(
        "--dep",
        action="append",
        default=[],
        dest="deps",
        metavar="DEP",
        help="a dep, repeatable: an id, 'Block X', a range, or work outside the backlog",
    )
    add_parser.add_argument(
        "--requires",
        action="append",
        default=[],
        dest="requires",
        metavar="REQUIREMENT",
        help=(
            "what must be present to finish this, repeatable and declared in "
            "`[requirements]`: not a dep — `pick` offers it only to a caller that has one"
        ),
    )
    _marker_flag(
        add_parser,
        "the status marker (default: the first marker roadkeep.toml declares)",
    )
    add_parser.add_argument(
        "--id",
        dest="task_id",
        help="the id (default: derived, one past the highest anywhere)",
    )
    add_parser.add_argument(
        "--prefix",
        dest="family",
        help=(
            "which track the derived id counts in (default: the first declared); only "
            "a backlog that numbers by track has a second one to name"
        ),
    )
    add_parser.add_argument(
        "--ref",
        help=(
            "the rationale anchor, for ref_scheme = 'outline' only; otherwise derived — "
            "<prefix>:<x.y> for a prose file [refs] gives a namespace"
        ),
    )
    add_parser.add_argument(
        "--section",
        metavar="TITLE",
        help=(
            "write the rationale under this heading, in the same transaction: the "
            "pointer every line carries resolves to nothing until a section exists"
        ),
    )
    add_parser.add_argument(
        "--section-body",
        dest="section_body",
        help="the rationale prose; omitted or '-' reads stdin. Read only with --section",
    )
    add_parser.add_argument(
        "--section-body-file",
        dest="section_body_file",
        metavar="PATH",
        help=_BODY_FILE.format(what="rationale"),
    )
    add_parser.add_argument(
        "--capture",
        metavar="PATH",
        help=(
            "the kept capture this line files, stamped with the id this call mints (RK1141) "
            "— `report` prints this flag already filled in, so the row `stats` counts is "
            "cleared by the act that closes it and never by a second step somebody remembers"
        ),
    )
    add_parser.add_argument(
        "--json", action="store_true", help="the line, with the file and line it landed on"
    )
    # `reads_stdin` is declared here for the reason `reads_only` is (RK171): it is a claim about
    # this command that a surface serving it has to know, and the only statement of it used to be
    # the comment two lines above the read. Gated, because an `add` naming no section must never
    # block on a pipe — which is what that comment said and nothing enforced.
    withheld(
        add_parser,
        family="the id's prefix is `[ids]`' and `next-id` derives it; a caller choosing one is a caller numbering into another project's range",
        capture='a path to a local artefact this transport does not share, and the verb that writes one is not a tool here',
    )
    add_parser.set_defaults(
        handler=_add,
        # Two, and this is the command that has two (RK329): the body was the obvious
        # affordance because it is long, and the `why` is the one that actually needed it
        # because it is the field that reliably carries what a shell reads first. Ungated,
        # unlike the body: a `--why -` is the caller asking for the pipe outright.
        reads_stdin=(
            Prose(dest="section_body", gated_by="section", unless="section_body_file"),
            Prose(dest="why", omitted=False),
        ),
    )

    status_parser = subcommands.add_parser(
        "status",
        help="set a task's marker in the roadmap, and nowhere else",
        description=(
            "Write one task's status marker. Refused if a sibling file already carries "
            "one for that id: two files that both express status will eventually "
            "express different status, and nothing says which is right."
        ),
    )
    status_parser.add_argument("id", help="the task, e.g. RK7")
    status_parser.add_argument(
        "marker", help="the new marker, from the open set this project declares"
    )
    status_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    status_parser.set_defaults(
        handler=_status,
        twin=(
            "status writes a marker onto one line and needs both: `status <id> <marker>`."
            " The backlog's numbers are `stats`, which needs neither — one character "
            "apart, and this is the one that writes"
        ),
    )

    amend_parser = subcommands.add_parser(
        "amend",
        help="correct one open line's why, deps or pointer",
        description=(
            "Correct the three fields a project that adopted the tool has to be able to fix: "
            "a pointer it never had, a dep naming an id in neither file, and the compression "
            "of a `why` that was a paragraph before the limit existed. Validated at input "
            "exactly as `add` validates it, or nothing is written. The `symptom` is not "
            "amendable — it is the claim the line is, so a different one is a different task."
        ),
    )
    amend_parser.add_argument("id", help="the task, e.g. RK7")
    amend_parser.add_argument(
        "--why", help="the sentence, re-validated against the limit" + _PIPE
    )
    amend_parser.add_argument(
        "--dep",
        action="append",
        dest="deps",
        metavar="DEP",
        help="a dep, repeatable: given at all, it replaces the whole group",
    )
    amend_parser.add_argument(
        "--requires",
        action="append",
        dest="requires",
        metavar="REQUIREMENT",
        help="a requirement, repeatable: given at all, it replaces the whole group",
    )
    amend_parser.add_argument(
        "--ref", help="the rationale anchor, for ref_scheme = 'outline'"
    )
    amend_parser.add_argument(
        "--lines",
        type=int,
        help=(
            "how many lines this correction replaces; required where the line wraps, which "
            "on a roadmap only an adopted backlog can be"
        ),
    )
    amend_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    amend_parser.set_defaults(
        handler=_amend, reads_stdin=(Prose(dest="why", omitted=False),)
    )

    restate_parser = subcommands.add_parser(
        "restate",
        help="correct one open line's symptom, keeping its id",
        description=(
            "The one field `amend` does not reach, at a door of its own. A different symptom "
            "is normally a different task, which is why that verb excludes it — and a premise "
            "that turns out false is not a different task, it is this file asserting "
            "something untrue in the field a reader sees first. `retire` plus `add` is the "
            "exit that was designed for it, and it spends an id, deletes a section that was "
            "already right and records a departure that never happened. This keeps all three. "
            "A verb rather than a flag, so the act has a name a reviewer can see."
        ),
    )
    restate_parser.add_argument("id", help="the task, e.g. RK7")
    restate_parser.add_argument(
        "--symptom",
        required=True,
        help="what does not work — re-validated against the limit, exactly as `add` does"
        + _PIPE,
    )
    restate_parser.add_argument(
        "--lines",
        type=int,
        help="how many lines this restatement replaces; required where the line wraps",
    )
    restate_parser.add_argument(
        "--typo",
        action="store_true",
        help=(
            "a slip of the pen rather than a false premise: the claim is the one intended "
            "and a word in it was wrong, so the answer and the payload say so"
        ),
    )
    restate_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    restate_parser.set_defaults(
        handler=_restate,
        # The field the pipe convention skipped, and the verb whose only prose argument it is
        # (RK1187). A symptom carries the backtick and the apostrophe exactly as a `why` does,
        # and is the one a shell corrupts most quietly — a symptom that lost an apostrophe
        # still reads like prose somebody wrote, so nothing downstream calls it wrong. Ungated
        # and sentinel-only, like `amend --why`: `--symptom` is required, so the omitted read
        # is a shape argparse already refuses.
        reads_stdin=(Prose(dest="symptom", omitted=False),),
    )

    renumber_parser = subcommands.add_parser(
        "renumber",
        help="move one open line to a free id, with its section and its dependents",
        description=(
            "Change one line's address, without a departure. The line, the section its "
            "pointer resolves to and every dep naming it move in one transaction; the "
            "ledger is never opened, because an id it records is a decision and not an "
            "address. This is the repair a merge that allocated one id twice needs, and "
            "the door `ship`, `retire` and `amend` all deliberately refuse to be."
        ),
    )
    renumber_parser.add_argument("id", help="the line to move, e.g. RK90")
    renumber_parser.add_argument(
        "--to",
        help="the new id (default: derived, one past the highest in the line's family)",
    )
    renumber_parser.add_argument("--json", action="store_true", help="every edit, as data")
    renumber_parser.set_defaults(handler=_renumber)

    defer_parser = subcommands.add_parser(
        "defer",
        help="set a line aside without retiring it: the store, not the ledger",
        description=(
            "A pause spelled as a retirement is terminal — the id cannot come back, the "
            "resolver reads the dep as never, and the rationale is deleted. This moves the "
            "line to the deferred store instead, keeping every slot and the section."
        ),
    )
    defer_parser.add_argument("id", help="the task being set aside, e.g. RK33")
    _reason_flag(
        defer_parser,
        "one sentence, the author's own: it wraps the why and a resume unwraps it" + _PIPE,
    )
    defer_parser.add_argument("--json", action="store_true", help="every edit, as data")
    defer_parser.set_defaults(
        handler=_defer, reads_stdin=(Prose(dest="reason", omitted=False),)
    )

    resume_parser = subcommands.add_parser(
        "resume",
        help="return a set-aside line to its block — the direction the ledger has none of",
        description=(
            "The store is revivable, which is what separates it from the two terminal "
            "doors: the same id, the same deps, the same section, back under the block "
            "the line left. The open marker is the one thing the store could not keep."
        ),
    )
    resume_parser.add_argument("id", help="the task coming back, e.g. RK33")
    _marker_flag(
        resume_parser,
        "the open marker it returns with; omitted, the first this project declares — "
        "the store holds one marker, so which one it was is not a fact any file kept",
        dest="marker",
    )
    resume_parser.add_argument("--json", action="store_true", help="every edit, as data")
    resume_parser.set_defaults(handler=_resume)

