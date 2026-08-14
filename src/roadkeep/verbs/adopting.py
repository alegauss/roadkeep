"""The verbs run once per project, and the two whose subject is this tool (RK494).

`init` scaffolds, `adopt` estimates what an existing backlog would cost to bring under the
schema, `install` wires the skill, the tools and the guard into a checkout, `uninstall` is
the way back out, and `engines` says whether the three copies that can be in play agree.
`mcp` serves the same surface over stdio (RK24).

`report` and `replay` belong by the same rule and not by exception: their subject is a
defect in this tool, captured as facts a replay re-runs (RK85-89) — something done to an
installation rather than to a backlog.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

from roadkeep.adopting import adopt, init
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
)
from roadkeep.backlog import Backlog
from roadkeep.config import Config
from roadkeep.installing import (
    engines,
    install,
    plan,
    removal,
    uninstall,
)
from roadkeep.rendering import _estimate_json, _print_estimate
from roadkeep.serving import serve
from roadkeep.verbs.refusing import EXIT_GATE, EXIT_OK, EXIT_USAGE, _refused


def _init(config: Config, args: argparse.Namespace) -> int:
    # `config` is deliberately unused: `init` is the one command that runs *before* a
    # project is configured, so it takes the directory it was pointed at. A discovered
    # config would be an ancestor's, and scaffolding under someone else's paths is how a
    # subproject ends up writing into its parent's roadmap.
    del config
    families = tuple(args.prefix or ("RK",))
    try:
        created = init(args.directory, prefix=families, blocks=args.blocks or ("A",))
    except (ValueError, OSError) as error:
        return _refused(error)

    if args.json:
        print(json.dumps(created.payload(args.directory, families), indent=2))
    else:
        print(created.stated(families))
    return EXIT_OK


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
    path = Path(args.path)
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
        recorded = json.loads(Path(args.path).read_text(encoding="utf-8"))
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
