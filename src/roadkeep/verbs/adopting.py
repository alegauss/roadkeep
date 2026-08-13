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
    PROJECT_BRIDGE,
    UNPINNABLE,
    engines,
    install,
    plan,
    removal,
    uninstall,
)
from roadkeep.provenance import invocation
from roadkeep.rendering import _estimate_json, _print_estimate, registration_report
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

    files = [created.config, *created.files]
    if args.json:
        print(
            json.dumps(
                {
                    "root": Path(args.directory).resolve().as_posix(),
                    "created": [path.as_posix() for path in files],
                    "prefix": families[0],
                    "prefixes": list(families),
                    "blocks": list(created.blocks),
                },
                indent=2,
            )
        )
        return EXIT_OK
    for path in files:
        print(f"created  {path.as_posix()}")
    print(
        f"{len(files)} file(s), blocks {', '.join(created.blocks)}: "
        f"`{invocation()} add --block {created.blocks[0]} …` writes the first line"
    )
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


#: `install --check` reports the same four states as a run, in the tense of a run that has
#: not happened. `kept` and `unchanged` are already that tense: neither describes a write.
_WOULD = {
    "created": "would create",
    "updated": "would update",
    "unchanged": "unchanged",
    "kept": "kept, yours",
}


#: The same rule for the other direction (RK138). `absent` and `untouched` describe no write
#: either, so only the two states that take something out are put in the conditional.
_WOULD_REMOVE = {
    "deleted": "would delete",
    "reduced": "would reduce",
    "absent": "absent",
    "untouched": "untouched",
}


def _engines(config: Config, args: argparse.Namespace) -> int:
    """The three copies this project runs, and whether the two versions agree (RK415).

    `config` is read for its root alone — the registry is keyed by project path, so the
    question is about the tree and not about the governed files in it.

    The exit code is the answer, the way `install --check`'s is: a session that has to grep a
    sentence to learn the pen and the judge are 133 versions apart is one that will not ask.
    """
    found = engines(config.root)
    running, plugin = found.running, found.plugin
    if args.json:
        print(
            json.dumps(
                {
                    "writing": {
                        "version": running.version,
                        "home": running.home.as_posix(),
                        "revision": running.revision,
                    },
                    # Null where no plugin is registered for this project, which is every
                    # tree served by a checkout alone and is not a defect (RK415).
                    "plugin": None
                    if plugin is None
                    else {
                        "version": plugin.version,
                        "home": None if plugin.home is None else plugin.home.as_posix(),
                        "revision": plugin.revision,
                        "scope": plugin.scope,
                    },
                    "gates": [
                        {"file": where, "ref": ref} for where, ref in found.gates
                    ],
                    "agree": found.agree,
                    # Which of the three, because the boolean above cannot carry the state
                    # RK418 added: a checkout with uncommitted work is at no commit the
                    # plugin could match, and `agreed` there was the defect being fixed.
                    "verdict": found.verdict,
                },
                indent=2,
            )
        )
        return EXIT_OK if found.agree else EXIT_GATE

    print(f"writing  {running.version:<10}{running.revision}  {running.home.as_posix()}")
    if plugin is None:
        # Said, never silent: "no plugin" and "a plugin this could not read" look the same
        # to a reader, and only one of them means the writes are unjudged by a second copy.
        print("plugin   —         no plugin is registered for this project")
    else:
        home = "" if plugin.home is None else f"  {plugin.home.as_posix()}"
        print(f"plugin   {plugin.version:<10}{plugin.revision}  {plugin.scope} scope{home}")
    for where, ref in found.gates or ():
        print(f"gate     {ref:<10}{where}")
    if not found.gates:
        print("gate     —         no workflow here calls the action")
    if found.verdict == UNPINNABLE:
        # The state that used to read as agreement, and the one a machine developing this
        # tool is in every day (RK418): the numbers match, the checkout has uncommitted
        # work, and the files the two copies hold are not the same files.
        print(
            f"differ   both state {running.version} and this checkout is modified at "
            f"{running.revision}, so the two cannot be compared: commit, or read a hook's "
            f"refusal as that copy's rule rather than this one's"
        )
        return EXIT_GATE
    if not found.agree:
        print(
            f"differ   the pen is {running.version} at {running.revision} and the judge is "
            f"{plugin.version if plugin else '—'} at "
            f"{plugin.revision if plugin else '—'}: `/plugin update` moves the judge, and "
            f"until then a hook's refusal is that copy's rule and not this one's"
        )
        return EXIT_GATE
    return EXIT_OK


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
        print(
            json.dumps(
                {
                    "root": intent.root.as_posix(),
                    "source": intent.source.as_posix(),
                    "launcher": intent.launcher,
                    # RK1113: which variant, and whether the project said so rather than the
                    # flag. Two keys, because a reader deciding whether to pass `--committed`
                    # needs the second one — with `carried` true, passing it changes nothing.
                    "committed": intent.committed,
                    "carried": intent.carried,
                    "checked": args.check,
                    "debt": intent.debt,
                    "surfaces": [
                        {
                            "path": surface.path.relative_to(intent.root).as_posix(),
                            "state": surface.state,
                            "writes": surface.writes,
                        }
                        for surface in intent.surfaces
                    ],
                    "skipped": [{"path": path, "why": why} for path, why in intent.skipped],
                    "registered": None
                    if intent.registered is None
                    else {
                        "attributes": intent.registered.attributes.as_posix(),
                        "added": list(intent.registered.added),
                        "present": list(intent.registered.present),
                        "command": intent.registered.command,
                        "invalidated_by": intent.registered.invalidated_by,
                        "wiring": None
                        if intent.registered.wiring is None
                        else {
                            "attributes": intent.registered.wiring.attributes.state,
                            "driver": intent.registered.wiring.driver.state,
                        },
                        # Keyed by the field names of `Registration`, and held to them by a
                        # test (RK276): the reading most likely to be automated is the one a
                        # dropped field is quietest in.
                        "left_alone": [list(pair) for pair in intent.registered.left_alone],
                    },
                    "changing": len(intent.changing),
                    # RK393: the surfaces `install` cannot write, each with the file standing
                    # in the way. Its own key and not folded into `changing`, because a reader
                    # acting on that number would run the command this one says will not run.
                    "blocked": [
                        {
                            "path": path.relative_to(intent.root).as_posix(),
                            "blocked_by": parent.relative_to(intent.root).as_posix(),
                        }
                        for path, parent in intent.blocked
                    ],
                    # RK394: what stands in the way of the driver's own file, where anything
                    # does. Null and not absent when nothing does, so a reader tells "checked
                    # and clear" from "this payload predates the field".
                    "driver": None
                    if intent.driver is None
                    else intent.driver.relative_to(intent.root).as_posix(),
                },
                indent=2,
            )
        )
    else:
        print(f"{intent.source.as_posix()}  →  {intent.launcher}")
        if intent.carried:
            # Said because the header alone does not (RK1113): the launcher is a path, and a
            # reader who passed no flag has to be told the path came from their own project
            # rather than from a default that is about to overwrite it.
            print(
                f"  committed      this project already runs {PROJECT_BRIDGE}, so the "
                f"wiring stays on it — `uninstall` then `install` moves it to a checkout"
            )
        for surface in intent.surfaces:
            # `--check` writes nothing, so it reports in the conditional: the same three
            # words in the past tense would claim a file changed that did not.
            state = _WOULD[surface.state] if args.check else surface.state
            print(f"  {state:<14} {surface.path.relative_to(intent.root).as_posix()}")
        if intent.registered is not None:
            # The same lines `merge --register` prints, because it is the same write (RK148) —
            # and now literally the same rendering (RK276), so a field added to `Registration`
            # cannot reach one surface and miss the other. The `git config` half is still
            # printed and not run.
            for line in registration_report(intent.registered, intent.registered.attributes.name, 14):
                print(line)
        if intent.debt:
            # Beside the surfaces, because it is the reason one of them was written the way
            # it was (RK140): a decision taken from a measurement nobody is shown is one the
            # adopter cannot check.
            print(
                f"  baselined      {intent.debt} standing finding(s) here, so the workflow "
                f"fails on what a branch adds — drop the line once `lint` exits 0"
            )
        for _, why in intent.skipped:
            # One label for every surface this command does not write, because they are not
            # one kind: `CONTRIBUTING.md` is the author's, the driver is a flag away, and the
            # two at the plugin's own root are files the tree already ships (RK235). "by hand"
            # said all three, and on the last two it told the reader to write them.
            print(f"  not written    {why}")
        for path, parent in intent.blocked:
            # Beside the surfaces and before the verdict (RK393): this one is not a difference
            # `install` closes, and saying so is the whole repair. The remedy named is the
            # blocker, because that is the file somebody has to move.
            print(
                f"  blocked        {path.relative_to(intent.root).as_posix()}: "
                f"{parent.relative_to(intent.root).as_posix()} is a file, "
                f"so the directory cannot be made"
            )
        if args.check and intent.changing:
            # Two sentences and not one, because they are two states (RK393). A surface that
            # differs is one `install` writes; a surface that is blocked is one it exits 2 on,
            # and a gate whose named remedy is a red command sends a CI job round a loop.
            blocked = {path for path, _ in intent.blocked}
            differing = [s for s in intent.changing if s.path not in blocked]
            if differing:
                print(
                    f"{len(differing)} surface(s) differ from what this checkout ships: "
                    f"`{invocation()} install` writes them",
                    file=sys.stderr,
                )
            if intent.blocked:
                print(
                    f"{len(intent.blocked)} surface(s) cannot be written at all: "
                    f"move what is standing in the directory first, and `{invocation()} "
                    f"install` will not run until you do",
                    file=sys.stderr,
                )
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
    where = config.relative(known.path)
    if args.json:
        print(json.dumps({"path": where, "filed": written}, indent=2))
        return EXIT_OK
    # No staging line: the report directory is git-ignored, so there is nothing to stage —
    # which is the exemption `test_every_write_command_is_either_wired_or_exempted` carries.
    print(f"{where} now names {written}")
    if elsewhere:
        # Said out loud, because this is the one stamp nothing here can check: the row clears on
        # the author's word that the work went there, and a reader should see which claim it is.
        qualified = "" if written == args.task_id else " — the capture recorded where it went"
        print(
            f"  delivered to {elsewhere}, which this project cannot read — taken as filed"
            f"{qualified}"
        )
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
        print(
            json.dumps(
                {
                    "root": intent.root.as_posix(),
                    "checked": args.check,
                    "surfaces": [
                        {
                            "path": withdrawal.path.relative_to(intent.root).as_posix(),
                            "state": withdrawal.state,
                            "writes": withdrawal.writes,
                        }
                        for withdrawal in intent.withdrawals
                    ],
                    "kept": [{"path": path, "why": why} for path, why in intent.kept],
                    "changing": len(intent.changing),
                },
                indent=2,
            )
        )
    else:
        print(f"{intent.root.as_posix()}  ←  this project's own entries")
        for withdrawal in intent.withdrawals:
            state = _WOULD_REMOVE[withdrawal.state] if args.check else withdrawal.state
            print(f"  {state:<14} {withdrawal.path.relative_to(intent.root).as_posix()}")
        for _, why in intent.kept:
            print(f"  kept           {why}")
        if args.check and intent.changing:
            print(
                f"{len(intent.changing)} surface(s) still wire this project to a checkout: "
                f"`{invocation()} uninstall` takes them out",
                file=sys.stderr,
            )
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
    agrees = outcome.ran and outcome.reproduces == expected
    if args.json:
        print(
            json.dumps(
                {
                    "path": args.path,
                    "ran": outcome.ran,
                    "missing": list(outcome.missing),
                    # A second reason not to run, kept apart from the first (RK343): a part the
                    # capture lacks is a redaction, and a file it never carried is a capture to
                    # take again.
                    "unstaged": list(outcome.unstaged),
                    "reproduces": outcome.reproduces,
                    "expected": expected,
                    "recorded_exit": outcome.recorded_exit,
                    "exit": outcome.exit_code,
                    # `null` and not `[]` where the capture recorded no environment (RK341):
                    # "nothing drifted" and "nothing to compare" are different answers, and a
                    # reader that cannot tell them apart is the defect this closes.
                    "drifted": None if outcome.drifted is None else list(outcome.drifted),
                    # The third reason not to trust the verdict (RK443), beside the other two
                    # and never folded into `reproduces` — this one reproduces by
                    # construction, and what it is about is the refusal rather than the
                    # symptom the capture was filed under.
                    "stopped": outcome.stopped,
                    # The fourth (RK1078), and the one that decides whether a report is
                    # closed rather than live: an empty string is "nothing to compare",
                    # which is a different answer from "the same version".
                    "aged": outcome.aged,
                },
                indent=2,
            )
        )
    else:
        print(f"{args.path}  {outcome}")
        if outcome.ran and not agrees:
            # The whole point of the corpus: a verdict that moved is either a fix to record
            # or a regression to answer, and both want the file updated in the same commit.
            print(
                f"  recorded reproduces = {str(expected).lower()}: "
                f"update the capture, or the tree stopped agreeing with it"
            )
    return EXIT_OK if agrees else EXIT_GATE


def _mcp(config: Config, args: argparse.Namespace) -> int:
    """Hand stdin and stdout to the protocol loop (RK24).

    The directory and not the `Config`: the server re-discovers it per message, so a
    `roadkeep.toml` edited during the session is the one the next `tools/list` describes.
    """
    return serve(sys.stdin, sys.stdout, args.directory)
