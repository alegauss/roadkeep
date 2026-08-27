"""The verbs run once per project, and those whose subject is this tool (RK494).

`init` scaffolds, `declare` retrofits a role, `adopt` estimates what an existing backlog
would cost to bring under the schema, `install` wires the skill, the tools and the guard
into a checkout, `uninstall` is the way back out, and `engines` says whether the copies
that can be in play agree. `mcp` serves the same surface over stdio (RK24).

`report`, `replay` and the `capture` group belong by the same rule and not by exception:
their subject is a defect in this tool, captured as facts a replay re-runs (RK85-89) —
something done to an installation rather than to a backlog.

**Neither list is counted here** (RK1397). This opened with *the two whose subject is this
tool* and named `report` and `replay`, while the module declared four: `capture filed`
arrived with RK1142 and `capture sweep` with RK1394, both by that same rule, and the first
paragraph had lost `declare` (RK1264) the same way. Each drift was one line an author did
not think to touch — the only count in this package that was prose confronted with nothing,
where every other census here is a table held against the population it is a set of. So the
two lists are :data:`ABOUT_THIS_TOOL` and :data:`ABOUT_THE_WIRING`, and `test_surfaces`
holds them against what :func:`declare_wiring` actually declares.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile

from roadkeep.adopting import (
    OPT_IN,
    NoSuchTable,
    declare_table,
    DEFERRED_ROLE,
    SCAFFOLD_ROLES,
    STRATEGY_ROLE,
    adopt,
    declare,
    init,
)
from roadkeep.capturing import (
    Filed,
    REPORTS,
    STOPPED_NOTICE,
    body,
    capture,
    captures,
    check,
    delivered,
    handoff,
    keep,
    replay,
    stamp,
    sweep,
)
from roadkeep.backlog import Backlog
from roadkeep.config import ROLES, Config
from roadkeep.installing import (
    engines,
    install,
    plan,
    removal,
    uninstall,
    vendor,
)
from roadkeep.rendering import _estimate_json, _print_estimate
from roadkeep.serving import serve
from roadkeep.capturing import PARTS
from roadkeep.verbs.declaring import _JSON_HELP
from roadkeep.verbs.refusing import EXIT_GATE, EXIT_OK, EXIT_USAGE, _refused

#: The subcommands here whose subject is a defect in **this tool** rather than a backlog
#: (RK85-89, RK1142, RK1394). Spelled by the full path a caller types, because `capture` is a
#: group and the two verbs under it are what have the subject — a list of top-level words could
#: not say that, and saying it wrongly is what RK1397 was.
ABOUT_THIS_TOOL = ("report", "replay", "capture filed", "capture sweep")

#: And those whose subject is the project's own wiring: which files exist, which copies write,
#: and how the surface is reached. The other half of a partition, so a verb added to this module
#: belongs to one of them and the test says which is missing rather than that a number moved.
ABOUT_THE_WIRING = (
    "init",
    "declare",
    "adopt",
    "install",
    "uninstall",
    "engines",
    "mcp",
)


def _init(config: Config, args: argparse.Namespace) -> int:
    # `config` is deliberately unused: `init` is the one command that runs *before* a
    # project is configured, so it takes the directory it was pointed at. A discovered
    # config would be an ancestor's, and scaffolding under someone else's paths is how a
    # subproject ends up writing into its parent's roadmap.
    del config
    families = tuple(args.prefix or ("RK",))
    try:
        created = init(
            args.directory,
            prefix=families,
            blocks=args.blocks or ("A",),
            # Named at the door and never derived (RK1186): which prose files a project wants
            # is the author's decision, and a scaffold that guessed would create a file
            # somebody has to notice is empty before they can delete it.
            roles=(
                *SCAFFOLD_ROLES,
                *((STRATEGY_ROLE,) if args.strategy else ()),
                *((DEFERRED_ROLE,) if args.deferred else ()),
            ),
        )
    except (ValueError, OSError) as error:
        return _refused(error)

    if args.json:
        print(json.dumps(created.payload(args.directory, families), indent=2))
    else:
        print(created.stated(families))
    return EXIT_OK


def _declare(config: Config, args: argparse.Namespace) -> int:
    """`init`'s door for a project that is already configured (RK1264).

    Unlike `_init` this one **wants** the discovered config: the role is added to the project
    the caller is standing in, and the headings it mirrors are that project's own.
    """
    try:
        # One argument, two vocabularies (RK1328): a **role** retrofits a file and its
        # `[files]` key, and an opt-in **table** opens a list this project may then govern.
        # Both are *this file, one key, refused where it is already declared*, which is why
        # the argument widens rather than the verb list — a third served tool costs about 800
        # characters against 87 of headroom, and the ceiling is not what should give.
        if args.role in OPT_IN:
            written = declare_table(config, args.role)
        elif args.role in ROLES:
            written = declare(config, args.role, args.path)
        else:
            # The word is in neither, and the refusal names both: one argument now carries two
            # vocabularies, and a caller who typed into the wrong one learns nothing from a
            # message about the other. `declare` keeps `NoSuchRole` for its own contract.
            raise NoSuchTable(args.role, OPT_IN)
    except (ValueError, OSError) as error:
        return _refused(error)

    if args.json:
        print(json.dumps(written.payload(config), indent=2))
    else:
        print(written.stated(config))
    return EXIT_OK


def _better_read(config: Config, args: argparse.Namespace, estimate):
    """The reading that fits, where the caller named no role (RK1346).

    Measured on an ungoverned `CHANGELOG.md`: the backlog grammar reported 0 parsed and *361
    would change*, and `--ledger` reported 361 conform and none changing. The file was already
    conforming, the report said it was 361 lines of work, and the word `ledger` appeared
    nowhere in it. The diagnosis was accurate under the grammar it applied — *no marker where
    the status goes* is exactly true of a ledger entry read as a task line — which is what made
    it convincing.

    Not a guess: the two grammars separate by an order of magnitude on real files. Measured on
    this repository, `docs/CHANGELOG.md` reads 843 conform as a ledger and 0 as a backlog,
    while `docs/ROADMAP.md` reads 1 and 0 the other way. So the better reading is the one with
    more conforming lines, and a tie keeps what was asked for.

    Only where nothing was asked. `--ledger` is honoured as typed, for the reason `--prefix`
    is: an override the tool second-guesses is not an override — and the header now names the
    role either way, so a reader can see which grammar answered and pass the other.
    """
    if args.ledger or args.sections or estimate.conforming:
        return estimate
    best = estimate
    # Both other roles and not one (RK1347): a rationale file read as a backlog reported
    # *nothing in 837 line(s) was read in any shape*, where `--sections` read 51 conforming
    # sections and 19 paragraphs over a limit. Tried separately because the two flags are
    # refused together, and the estimator is what declines the pair.
    for role in ({"ledger": True}, {"sections": True}):
        try:
            other = adopt(
                config,
                args.path,
                prefix=args.prefix,
                ref_scheme=args.ref_scheme,
                alongside=args.alongside,
                **role,
            )
        except (ValueError, OSError):
            # A role this file's arguments refuse is not a finding here: what was asked for
            # still answers, and a retry that cannot be taken says nothing about the file.
            continue
        if other.conforming > best.conforming:
            best = other
    return best


def _adopt(config: Config, args: argparse.Namespace) -> int:
    try:
        estimate = adopt(
            config,
            args.path,
            prefix=args.prefix,
            ref_scheme=args.ref_scheme,
            ledger=args.ledger,
            sections=args.sections,
            alongside=args.alongside,
        )
    except (ValueError, OSError) as error:
        return _refused(error)

    estimate = _better_read(config, args, estimate)
    if args.json:
        print(json.dumps(_estimate_json(estimate), indent=2))
        return EXIT_OK
    _print_estimate(estimate)
    # Always 0: this reports on a file the project has not adopted, so there is no
    # contract for it to have broken. `lint` is the command with an exit code.
    return EXIT_OK


def _engines(config: Config, args: argparse.Namespace) -> int:
    """The three copies this project runs, and whether the two versions agree (RK415).

    `config` is read for its root alone — the registry is keyed by project path, so the
    question is about the tree and not about the governed files in it.

    The exit code is the answer, the way `install --check`'s is: a session that has to grep a
    sentence to learn the pen and the judge are 133 versions apart is one that will not ask.
    """
    found = engines(config.root)
    if args.invoke:
        # One line and no verdict (RK1230): this answers *which copy to call*, which is a
        # question a caller has before they know whether the copies agree — and an exit code
        # about agreement would make a shell substitution fail on a project that is merely
        # behind. `engines` bare is where the disagreement is read.
        # `--json` is honoured rather than refused, because the served surface appends it to
        # every call (RK319): a flag that only worked on a terminal would be one this project's
        # own agent could not use, which is the caller the whole task is about.
        print(json.dumps({"invoke": found.invoke()}, indent=2) if args.json else found.invoke())
        return EXIT_OK
    # Both registers off the record (RK1170), the exit code included: whether the pen and the
    # judge are the same copy is a property of the reading and not a second decision here.
    if args.json:
        print(json.dumps(found.payload(), indent=2))
    else:
        print(found.stated())
    return EXIT_OK if found.agree else EXIT_GATE


def _install(config: Config, args: argparse.Namespace) -> int:
    """Wire the harness for a project the plugin did not install (RK100).

    `config` is unused for `init`'s reason one step further along: this writes the surfaces
    that decide *which* engine a session reaches, and none of it is read out of the governed
    files. The exit code carries `--check`'s answer — 1 for a surface that would change,
    because a copy held in step by a gate is the whole point of there being a check.
    """
    del config
    try:
        intent = (
            # `--check` writes nothing, so it reports the driver as unwritten either way: a
            # check that registered one would be a check that changed the repository (RK148).
            plan(args.directory, source=args.source, committed=args.committed)
            if args.check
            else install(
                args.directory,
                source=args.source,
                register_merge=args.register_merge,
                committed=args.committed,
            )
        )
        # After the surfaces and never instead of them (RK1193): the engine is what those
        # declarations *point at*, so a run that vendored one and failed to wire it would
        # leave a copy nothing reaches. Inside the same try, so a machine with no engine to
        # copy refuses in the words every other bad input gets.
        pinned = vendor(args.directory, checked=args.check) if args.vendor else None
    except (ValueError, OSError) as error:
        return _refused(error)

    if args.json:
        payload = intent.payload(args.check)
        if pinned is not None:
            payload["vendored"] = pinned.payload()
        print(json.dumps(payload, indent=2))
    else:
        print(intent.stated(args.check))
        if pinned is not None:
            print(pinned.stated(args.check))
        if args.check:
            for line in intent.verdict():
                print(line, file=sys.stderr)
    if args.check and intent.changing:
        return EXIT_GATE
    return EXIT_OK


def _capture_filed(config: Config, args: argparse.Namespace) -> int:
    """Record which task a capture already on disk was filed as (RK1142).

    `add --capture` closes the row by the act that closes it, and covered every capture filed
    from then on and none of the ones already held: clearing this repository's own row took a
    `python -c`, which is the shape L5 exists against — every question this tool answers is a
    command, and the maintainer reached past the tool.

    Two refusals, both at the door (L1). An **id no governed file holds** is a link to nothing,
    which is the reading `stats` already makes and the reason it does not clear a row. A **path
    that is not a capture** is somebody's file, and a verb that stamped it would be writing a
    key into an artefact this tool did not produce.
    """
    # Against the project `-C` named and not the process's directory (RK1396): the paths this
    # verb is given are the ones `stats` and `capture sweep` print, and those are spelled
    # project-relative — so reading them from wherever the process happens to be refused the
    # tool's own doors, with a message naming the directory the file was in.
    path = config.locate(args.path)
    held = {one.path.resolve(): one for one in captures(config.root)}
    known = held.get(path.resolve())
    if known is None:
        print(
            f"roadkeep: {args.path} is not a capture this project holds: `stats` names the "
            f"ones it does, under {config.relative(config.root / REPORTS)}",
            file=sys.stderr,
        )
        return EXIT_USAGE
    # A stamp naming another repository is not this backlog's to verify (RK1160): a capture of a
    # defect in *this tool* is filed in this tool's backlog — which is what `report --to
    # OWNER/REPO` says — so the id is one no governed file here holds, and the lookup below would
    # refuse the one delivery a capture taken here can have. What is checked is the shape.
    elsewhere = delivered(args.task_id)
    backlog = Backlog.load(config)
    # And a **bare** id the capture's own destination explains (RK1161): `--to` or `[report]
    # upstream` is where a defect in roadkeep was aimed, the capture records it, so asking the
    # author to spell it again is the asymmetry RK1149 took out of the refusals. Only where this
    # backlog does not hold the id — a local id that resolves is a local filing, whatever the
    # capture was aimed at, and a typo stays the refusal below.
    ids = {
        entry.task.id
        for document in (backlog.roadmap, backlog.ledger, backlog.store)
        if document is not None
        for entry in document.entries
    }
    written = args.task_id
    if not elsewhere and args.task_id not in ids and known.upstream:
        written = f"{known.upstream}#{args.task_id}"
        elsewhere = delivered(written)
    if not elsewhere and args.task_id not in ids:
        print(
            f"roadkeep: no governed file holds {args.task_id}, so stamping it would be a "
            f"link to nothing — file the capture first, and `add --capture {args.path}` "
            f"stamps it as it mints the id; a defect in roadkeep itself belongs in roadkeep's "
            f"backlog, and `--as owner/repo#{args.task_id}` records that delivery",
            file=sys.stderr,
        )
        return EXIT_USAGE
    if not stamp(known.path, written):
        print(f"roadkeep: {args.path} could not be written", file=sys.stderr)
        return EXIT_USAGE
    # No staging line: the report directory is git-ignored, so there is nothing to stage —
    # which is the exemption `test_every_write_command_is_either_wired_or_exempted` carries.
    answer = Filed(
        where=config.relative(known.path),
        filed=written,
        elsewhere=elsewhere,
        asked=args.task_id,
    )

    if args.json:
        print(json.dumps(answer.payload(), indent=2))
    else:
        print(answer.stated())
    return EXIT_OK


def _capture_sweep(config: Config, args: argparse.Namespace) -> int:
    """Delete the captures the ledger proves are answered, and name the ones it cannot (RK1394).

    The retention `keep` parks, and the reading is the whole verb: `--check` and the delete print
    the same table, because what a reader needs from a sweep is why four files survived and not
    which three went. Nothing is refused at the door — an empty directory and a directory where
    every capture is still open are both legitimate answers, and a non-zero exit would make a
    project with nothing to sweep fail a hook that ran this.
    """
    found = sweep(config, delete=not args.check)
    if args.json:
        print(json.dumps(found.payload(config), indent=2))
    else:
        print(found.stated(config))
    # A file the reading proved spent and the filesystem would not remove: the directory did not
    # reach the state this reported, which is the one outcome a caller has to be able to branch
    # on. `EXIT_USAGE` because that is where an `OSError` lands in `_refused`, and this is the
    # same class of failure caught one layer earlier so the verdict about the others survives it.
    return EXIT_USAGE if found.refused else EXIT_OK


def _uninstall(config: Config, args: argparse.Namespace) -> int:
    """Take the harness back out of a project that was wired to a checkout (RK138).

    `config` is unused for `_install`'s reason, and no `--source` is taken for the reason the
    module states: the wiring is recognised by this project's own entries, so un-wiring works
    after the checkout it named is gone — which is when it is usually wanted.
    """
    del config
    try:
        intent = removal(args.directory) if args.check else uninstall(args.directory)
    except (ValueError, OSError) as error:
        return _refused(error)

    if args.json:
        print(json.dumps(intent.payload(args.check), indent=2))
    else:
        print(intent.stated(args.check))
        if args.check:
            for line in intent.verdict():
                print(line, file=sys.stderr)
    if args.check and intent.changing:
        return EXIT_GATE
    return EXIT_OK


def _report(config: Config, args: argparse.Namespace) -> int:
    """Capture one defect in this tool (RK85). Exit 2 refuses the claim, never the capture.

    The refusal is the point: a report is a task line for a backlog that holds a limit, so
    the sentence is judged in the session that made the claim rather than in the review of
    an issue. What the observed command exits with is a *fact of the capture* and never this
    command's own code — the whole reason to run it is that it failed.
    """
    argv = list(args.command_argv)
    if argv and argv[0] == "--":
        argv = argv[1:]
    if not argv:
        print("roadkeep: name the command that failed, after a bare --", file=sys.stderr)
        return EXIT_USAGE
    violations = check(args.symptom, args.why, args.block)
    if violations:
        print("roadkeep: refused, nothing captured:", file=sys.stderr)
        for violation in violations:
            print(f"  {violation}", file=sys.stderr)
        return EXIT_USAGE
    # Resolved before the capture is composed and not in the `--issue` branch where it used to
    # be read (RK1161): where this went is a fact of the capture, so the artefact records it and
    # `capture filed` can qualify a bare id from the file instead of asking for it again.
    aimed = args.to or config.upstream
    found = capture(
        args.symptom, args.why, args.block, argv, config.root, embed=args.embed, upstream=aimed
    ).without(*args.without)
    # Written before it is printed (RK89): what only exists on a stdout depends on the
    # caller taking a second step, and this block's own RK86 is the record of second steps
    # not being taken. On stderr, so `--json` and `--issue` stay pipeable.
    kept = keep(found, config.root)
    # The clause on the line that was misread (RK1139): a session ran this twice, read `kept
    # …json` as "filed" and reported the work done — and `stats` answered `total 2` and was
    # right, so nothing disagreed. "File it:" was already printed, at the end of the dump
    # below; what was missing is the **negative**, said where the path is.
    print(f"kept  {kept.path}  (a capture, not a backlog line)", file=sys.stderr)
    # With the flag that closes the row filled in (RK1141): the path is decided here, by
    # `keep`, so the capture cannot name itself — and a command a caller has to complete is a
    # second step, which is what RK86 is this block's own record of.
    print(f"file  {found.filing} --capture {kept.path}", file=sys.stderr)
    if kept.complaint:
        print(f"roadkeep: {kept.complaint}", file=sys.stderr)
    # Which of the two forms this is, said here because this is the only moment anybody can
    # choose (RK481). `replay` refuses a capture that carries no governed files, and by the
    # time it does the reporting session is over — so the flag is named to the one caller who
    # could still pass it. Not the default, and that stays: `--embed` is this project's text
    # leaving it, and a tool that published a private repository's roadmap by being helpful
    # is the worse failure. The silence is what was wrong.
    print(
        "replay  runs it anywhere: the governed files ride along"
        if args.embed
        else "replay  refuses it: no governed files ride along — `--embed` writes the "
        "capture that runs, and sends this project's text with it",
        file=sys.stderr,
    )
    # RK440: the capture carries the annotation for whoever triages it, and this is the same
    # fact said to the session that can still act on it. On stderr with the rest of the
    # narration, so `--json` and `--issue` stay pipeable.
    if found.failure.stopped:
        print(f"roadkeep: {STOPPED_NOTICE}", file=sys.stderr)
    if args.json:
        print(json.dumps(found.as_dict(), indent=2, ensure_ascii=False))
        return EXIT_OK
    if not args.issue:
        print(found)
        return EXIT_OK
    if aimed is None:
        # Guessed, this publishes a private repository's contents in a stranger's tracker.
        print(
            "roadkeep: no upstream to file against: declare [report] upstream = "
            "'owner/repo' in roadkeep.toml, or pass --to",
            file=sys.stderr,
        )
        return EXIT_USAGE
    print(body(found))
    sys.stdout.flush()
    print(handoff(found, aimed), file=sys.stderr)
    return EXIT_OK


def _replay(config: Config, args: argparse.Namespace) -> int:
    """Re-run one stored capture (RK88). Exit 1 when the verdict is not the recorded one.

    A scratch directory and never the working tree: the capture carries a `roadkeep.toml`
    and a governed file, and staging those over somebody's project would be the one write
    this tool makes that nobody asked for.
    """
    try:
        # `locate` for `_capture_filed`'s reason (RK1396): a capture is a file of the project,
        # and the address a reader has is the one `stats` printed. `tolerates_config_error` does
        # not weaken it — a default config still knows the root `-C` named, which is the whole
        # of what this needs.
        recorded = json.loads(config.locate(args.path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        print(f"roadkeep: {error}", file=sys.stderr)
        return EXIT_USAGE
    with tempfile.TemporaryDirectory(prefix="roadkeep-replay-") as scratch:
        outcome = replay(recorded, scratch)
    expected = bool(recorded.get("reproduces", True))

    if args.json:
        print(json.dumps(outcome.payload(args.path, expected), indent=2))
    else:
        print(outcome.stated(args.path, expected))
    return EXIT_OK if outcome.agrees(expected) else EXIT_GATE


def _mcp(config: Config, args: argparse.Namespace) -> int:
    """Hand stdin and stdout to the protocol loop (RK24).

    The directory and not the `Config`: the server re-discovers it per message, so a
    `roadkeep.toml` edited during the session is the one the next `tools/list` describes.
    """
    return serve(sys.stdin, sys.stdout, args.directory)


def declare_wiring(subcommands: argparse._SubParsersAction) -> None:
    """This module's verbs, declared where their handlers are (RK1171).

    `build_parser` called forty-nine blocks like these in a row; what it calls now is an index
    over the modules that own them. The move is what RK1169 and RK1170 bought: the flags a verb
    declares, the reasons it withholds and the record it answers with are one file's, so a
    change to any of them is one file's too.

    The order inside is `build_parser`'s own, which is where these blocks sat.
    """
    report_parser = subcommands.add_parser(
        "report",
        help="capture a defect in this tool, with what the failing session knew",
        description=(
            "Re-run the command that failed, in this process, and emit what identifies the "
            "defect: the argv, the exit code, the engine that answered, this project's "
            "roadkeep.toml, the line the engine objected to and any traceback. The two "
            "facts a machine cannot supply are arguments and are refused here against this "
            "tool's own schema, so a report arrives inside the limits the backlog it is "
            "destined for enforces. Nothing is sent: the capture is printed, and delivery "
            "is a separate decision."
        ),
    )
    report_parser.add_argument(
        "--symptom", required=True, help="what does not work — a phrase, never a fix"
    )
    report_parser.add_argument(
        "--why", required=True, help="one sentence, ending in a stop: why it matters"
    )
    report_parser.add_argument(
        "--block",
        default="F",
        help="the block of roadkeep's own backlog this belongs under (default: F)",
    )
    report_parser.add_argument(
        "--without",
        dest="without",
        action="append",
        default=[],
        metavar="PART",
        choices=PARTS,
        help=(
            "drop one part of the capture, repeatable: what a private repository must not "
            "publish is deleted by name, never scrubbed by a filter"
        ),
    )
    report_parser.add_argument(
        "--issue",
        action="store_true",
        help=(
            "print the tracker body on stdout and the command that files it on stderr; "
            "nothing is sent, and the destination is [report] upstream"
        ),
    )
    report_parser.add_argument(
        "--to",
        metavar="OWNER/REPO",
        help="file against this repository instead of the configured upstream",
    )
    report_parser.add_argument(
        "--embed",
        action="store_true",
        help=(
            "carry the governed files this project declares, so the capture can be replayed "
            "without this repository — a test somewhere else, and files leaving here"
        ),
    )
    report_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    report_parser.add_argument(
        "command_argv",
        nargs=argparse.REMAINDER,
        metavar="-- COMMAND",
        help="the roadkeep command that failed, after a bare --, without the program name",
    )
    report_parser.set_defaults(handler=_report, tolerates_config_error=True, reads_only=True)

    replay_parser = subcommands.add_parser(
        "replay",
        help="re-run a stored capture against the tree that is here now",
        description=(
            "Stage the capture's own configuration and file in a scratch directory, run "
            "the argv it recorded, and answer whether the defect still reproduces. Nothing "
            "from the reporting project is needed: a capture that was never made replayable "
            "says which part it lacks instead of being staged from a guess. Exits 1 when "
            "the answer differs from the `reproduces` the file records — which is what "
            "makes a corpus of field reports a gate rather than a folder."
        ),
    )
    replay_parser.add_argument("path", help="a capture written by `report --json`")
    replay_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    replay_parser.set_defaults(handler=_replay, tolerates_config_error=True, reads_only=True)

    capture_parser = subcommands.add_parser(
        "capture",
        help="what became of a capture already on disk",
        description=(
            "The third of the capture pair's family (RK1142). `report` writes one and "
            "`replay` re-runs it; this says what happened to one that is already there — "
            "which task it was filed as, and whether that answer makes it spent. The "
            "retention `keep` parked arrives here as `sweep` (RK1394), in its exact half "
            "only: rotation, an age limit and a dedup by argv are still open, and they are "
            "what a capture that never gets a stamp waits for."
        ),
    )
    capture_actions = capture_parser.add_subparsers(dest="action", required=True)
    capture_filed = capture_actions.add_parser(
        "filed",
        help="record which task a kept capture was filed as",
        description=(
            "Write into the capture the id it was filed as, so the row `stats` counts is "
            "cleared by a fact in the artefact rather than by a symptom that matches "
            "(RK1141). `add --capture` does this for a capture being filed now; this is the "
            "door for one already on disk, and it is the whole of what RK1142 was: clearing "
            "this repository's own row took a `python -c`, which is what L5 exists against. "
            "Refused where no governed file holds the id — a stamp naming nothing is a link "
            "to nothing — and where the path is not a capture this tool wrote. An id "
            "**qualified by a repository** is the exception (RK1160): a defect in roadkeep is "
            "filed in roadkeep's backlog, so no local file will ever hold that id, and both "
            "readers left a row nothing could clear."
        ),
    )
    capture_filed.add_argument("path", help="a capture under .roadkeep/reports/")
    capture_filed.add_argument(
        "--as",
        dest="task_id",
        required=True,
        metavar="ID",
        help=(
            "the task it was filed as, e.g. RK1138 — refused unless a governed file holds it, "
            "or `owner/repo#ID` for one filed in another backlog this project cannot read"
        ),
    )
    capture_filed.add_argument("--json", action="store_true", help=_JSON_HELP)
    capture_filed.set_defaults(handler=_capture_filed, wiring=True)

    capture_sweep = capture_actions.add_parser(
        "sweep",
        help="delete the captures the ledger records as shipped",
        description=(
            "The retention `keep` parks, keyed on the fact the artefact already carries "
            "(RK1394). A capture whose `filed` id the ledger records as shipped is answered "
            "by this repository's own record, so it is deleted; every other state is named "
            "and left. An age limit would be the weaker key — it says time passed where a "
            "stamp says the work landed — and it deletes exactly the captures an exact "
            "reading protects: one never filed, one open, and one delivered to a backlog "
            "this project cannot read. `--check` prints the same table and removes nothing."
        ),
    )
    capture_sweep.add_argument(
        "--check",
        action="store_true",
        help="say what would go and leave the directory alone",
    )
    capture_sweep.add_argument("--json", action="store_true", help=_JSON_HELP)
    # `reads_only` for `report`'s and `replay`'s reason and not as a claim about the filesystem
    # (RK167): what it declares is that no **governed** file is written, which is what decides
    # whether the lock is taken — the ledger is read here and nothing else is, and the files that
    # go are in a directory git was taught to ignore.
    #
    # And deliberately no `wiring=True`, unlike its sibling. That exemption exists so a pin has a
    # way to be satisfied and a defect a way to be filed (see `cli._enforced`); neither is what
    # this does — it *deletes* evidence, which is the one write a copy the project has pinned
    # away from should be refused, and a sweep postponed until the right copy runs costs
    # kilobytes.
    capture_sweep.set_defaults(handler=_capture_sweep, reads_only=True)

    init_parser = subcommands.add_parser(
        "init",
        help="scaffold roadkeep.toml and the files it declares",
        description=(
            "Write the configuration and the three governed files, or write nothing. The "
            "config is rendered from the schema's own defaults, so a scaffold cannot "
            "declare a format the tool does not implement. No starter task and no prose: "
            "a title, the blocks you name, and where the non-goals go."
        ),
    )
    init_parser.add_argument(
        "--prefix",
        action="append",
        help=(
            "the id prefix, uppercase alphanumeric (default: RK). Repeatable for a "
            "backlog numbered by track; the first is what `add` mints under"
        ),
    )
    init_parser.add_argument(
        "--block",
        action="append",
        dest="blocks",
        metavar="LABEL",
        help=(
            "a block heading, repeatable: 'A' or 'A — The model'. A task is filed "
            "under a heading and a write never invents one (default: A)"
        ),
    )
    init_parser.add_argument(
        "--strategy",
        action="store_true",
        help=(
            "scaffold the strategy file too: a prose role for a document that outlives "
            "every task filed under it, where an improvements section is one task's "
            "rationale and goes when the line ships"
        ),
    )
    init_parser.add_argument(
        "--deferred",
        action="store_true",
        help=(
            "scaffold the deferred store too: the file `defer` moves a line to, which "
            "keeps the id, the deps and the section a retirement deletes. Without it that "
            "verb refuses, and the remedy is a toml key and a skeleton written by hand"
        ),
    )
    init_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    init_parser.set_defaults(handler=_init, wiring=True)

    declare_parser = subcommands.add_parser(
        "declare",
        help="add one governed role or open one opt-in table, past `init`",
        description=(
            "Write one role's file and the `[files]` key governing it, or open an opt-in "
            "table, on a project past `init`. Reach for it when a verb refuses over an "
            "undeclared role or table: `init` writes both once and refuses to run twice, so "
            "either declined at scaffold time was otherwise a hand edit. A role's file "
            "arrives with the block headings the roadmap carries, spelled as that file spells "
            "one; a table arrives empty, which is what opting in means, and `govern` tunes "
            "what is in it. The config keeps every other byte. Refused where it is already "
            "declared."
        ),
    )
    # Not argparse `choices`, for `--role`'s own reason (RK304) read one step further: what is
    # answerable here is the roles this *project* has not declared, which a parser built once
    # per process cannot say — so the closed set is published per project in the tool schema and
    # refused by name in the command.
    declare_parser.add_argument(
        "role",
        help=(
            f"which governed file to declare, one of {', '.join(ROLES)} — or an opt-in "
            f"table to open, one of {', '.join(OPT_IN)}"
        ),
    )
    declare_parser.add_argument(
        "--path",
        help="where it goes, project-relative (default: this role's own docs/ path)",
    )
    declare_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    declare_parser.set_defaults(handler=_declare)

    adopt_parser = subcommands.add_parser(
        "adopt",
        help="what an existing backlog would have to change to pass",
        description=(
            "Run the schema over a backlog this tool does not own yet and report the "
            "delta: what parses, what conforms, the longest field against its limit, the "
            "markers to declare. Writes nothing and never fails — an estimate that "
            "exits 1 is a gate, and the point is to take it before the commitment."
        ),
    )
    adopt_parser.add_argument("path", help="the file to measure, e.g. docs/ROADMAP.md")
    adopt_parser.add_argument(
        "--prefix",
        action="append",
        help=(
            "read the ids under this prefix, repeatable for a backlog numbered by "
            "track; without it the project's own is used, or the one the file's ids "
            "already spell — never all of them, which is a judgement and not a count"
        ),
    )
    adopt_parser.add_argument(
        "--ref-scheme",
        dest="ref_scheme",
        choices=("id", "outline"),
        help=(
            "measure the pointers under this scheme: 'outline' asks what adopting the "
            "tool costs, 'id' what adopting it and renumbering the outline costs"
        ),
    )
    adopt_parser.add_argument(
        "--ledger",
        action="store_true",
        help="measure it as a changelog: shipped marker, no deps field, no pointer",
    )
    adopt_parser.add_argument(
        "--sections",
        action="store_true",
        help=(
            "measure it as a rationale file: sections against `section`, and the width "
            "its prose is already wrapped to — the two limits an adopter has to declare"
        ),
    )
    adopt_parser.add_argument(
        "--with",
        dest="alongside",
        metavar="PATH",
        action="append",
        default=[],
        help=(
            "another prose file an address could be doubled across, repeatable — the one "
            "measure here that is about a set of files rather than this one; requires "
            "--sections, and never inferred from the directory"
        ),
    )
    adopt_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    # Read-only, which RK18 has been true of since this verb existed and nothing declared:
    # `adopt` measures a file and exits 0, writing nothing anywhere. Undeclared it took the
    # write lock for a run that cannot conflict with one, and — since RK1147 published a door
    # that reruns it — said `writes: true` in a payload about a command that writes nothing.
    adopt_parser.set_defaults(handler=_adopt, reads_only=True)

    install_parser = subcommands.add_parser(
        "install",
        help="wire this project to the checkout answering, the way the plugin would",
        description=(
            "Write the surfaces the plugin ships, for a project that runs roadkeep from a "
            "checkout instead: the server, the guard on its three hook events, and the "
            "skill that says which command to call — plus the CI workflow when the "
            "repository already has one. Every byte is translated from what the plugin "
            "carries, the launcher's path being the only substituted fact, so the skill "
            "cannot drift from the file it was copied from. The skill is refreshed on "
            "every run; the declarations keep everything they hold that is not this "
            "project's entry; the workflow is written once and then yours."
        ),
    )
    install_parser.add_argument(
        "--check",
        action="store_true",
        help=(
            "write nothing and exit 1 on anything that would change: the gate that keeps "
            "the copied skill in step, for a CI job or a pre-commit hook"
        ),
    )
    install_parser.add_argument(
        "--source",
        metavar="PATH",
        help=(
            "the roadkeep checkout to wire in (default: the one this command is running "
            "from, which is the one whose hook and tools the project would get)"
        ),
    )
    install_parser.add_argument(
        "--register-merge",
        action="store_true",
        help=(
            "wire the merge driver too — the `.gitattributes` half of `merge --register`, "
            "with the `git config` line printed for you to run: a flag and not a default, "
            "because it is configuration and the other half is outside these files"
        ),
    )
    install_parser.add_argument(
        "--committed",
        action="store_true",
        help=(
            "wire a launcher committed to this repository instead of a path to the checkout, "
            "so the guard reaches an environment that installs no plugin and clones no "
            "checkout — Claude Code on the web. It defers where the harness has the plugin "
            "wired for this project, and never blocks a turn"
        ),
    )
    install_parser.add_argument(
        "--vendor",
        action="store_true",
        help=(
            "copy the highest-versioned roadkeep this machine can reach into .roadkeep/, so "
            "the project runs a pinned engine instead of whichever copy a search order "
            "reaches first; ROADKEEP_SRC names a working checkout, which is otherwise skipped"
        ),
    )
    install_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    install_parser.set_defaults(handler=_install, wiring=True)

    engines_parser = subcommands.add_parser(
        "engines",
        help="which copies of roadkeep write, judge and gate this project",
        description=(
            "An adopting project wires three: the plugin its hook and skill run, the action "
            "its workflow gates on, and whatever `roadkeep` the caller invokes. They are "
            "allowed to differ — a cache may lag a checkout — and what is not survivable is "
            "not being able to say which one answered. A fourth is read and never judged: "
            "the merge driver git would run, a command rather than a version. Exits 1 where "
            "the two that state a version state different ones."
        ),
    )
    # The one line a caller pastes (RK1230). Its own flag rather than a row in the table:
    # what a shell needs is a value it can read into a variable, and the table is exactly the
    # thing a session was reduced to grepping — or, worse, to finding by listing a cache.
    engines_parser.add_argument(
        "--invoke",
        action="store_true",
        help=(
            "print only the command that reaches the copy wired to this project, so a shell "
            "invocation needs no directory listing to find it"
        ),
    )
    engines_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    # A read, and the exit code is its verdict rather than a fault (RK271): the three lines
    # above it have already said everything, and `/plugin update` is the move.
    engines_parser.set_defaults(handler=_engines, reads_only=True)

    uninstall_parser = subcommands.add_parser(
        "uninstall",
        help="take this project's entries back out of the four surfaces install wrote",
        description=(
            "Un-wire a project that ran roadkeep from a checkout — moving to the plugin, or "
            "off the tool entirely (RK138). The inverse of `install` under the same two "
            "rules: the declarations keep every entry that is not this project's, and a "
            "file that is not a JSON object is refused rather than rewritten. A file left "
            "holding nothing but what `install` wrote is deleted, because that is the state "
            "it was created from. It reads no checkout — the wiring is recognised by the "
            "server's name and the launcher a hook runs — so a project can be un-wired "
            "after the tree it pointed at is gone. The CI workflow stays: that gate calls "
            "the published action and not the checkout."
        ),
    )
    uninstall_parser.add_argument(
        "--check",
        action="store_true",
        help=(
            "take nothing out and exit 1 while anything is still wired: the same tense "
            "`install --check` reports in, on the other direction"
        ),
    )
    uninstall_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    uninstall_parser.set_defaults(handler=_uninstall, wiring=True)

    mcp_parser = subcommands.add_parser(
        "mcp",
        help="serve add, ship, pick and lint as MCP tools over stdio",
        description=(
            "Speak JSON-RPC on stdin and stdout so the fields arrive as a schema the "
            "client validates instead of flag names an agent types from memory (RK24). "
            "Every tool is dispatched through this same parser, so the refusal is the one "
            "a terminal prints. Not for a human to call: a session's client starts it."
        ),
    )
    # Same reason as `guard`: the process is started once for a whole session, so refusing
    # to start on a broken `roadkeep.toml` would take the tools away exactly when the gate
    # is what the project needs. `tools/list` describes the defaults and the first call
    # reports the error.
    mcp_parser.set_defaults(handler=_mcp, tolerates_config_error=True, reads_only=True)

