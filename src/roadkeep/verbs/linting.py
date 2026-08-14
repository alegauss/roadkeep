"""The gate, its two repairs, and the surfaces that run it for you (RK494).

`lint` reports, `--fix` repairs only what is derived, `repair` spends the whole report in
one call and `explain` says what a code is. `guard` is the same gate at the agent boundary
(RK22) and `merge` is git's own driver for a governed file (RK120) — both here because what
they refuse is what `lint` would.

Two function-level imports of :mod:`roadkeep.cli` live in this module, for the reason
:mod:`roadkeep.verbs` gives: `repair` runs whole commands back through the parser and the
dispatcher, and `merge` names the flag its parser declared.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

from roadkeep.config import Config
from roadkeep.kernel.document import write_atomically
from roadkeep.fixing import Fix, fix
from roadkeep.guarding import START_EVENTS, STOP_EVENTS, announce, attested, guard, review
from roadkeep.history import HistoryUnavailable
from roadkeep.linting import lint
from roadkeep.merging import markers, merge, register, role_of, wiring
from roadkeep.remedying import codes as remedy_codes, explain
from roadkeep.rendering import (
    _served,
    registration_report,
)
from roadkeep.repairing import repair
from roadkeep.verbs.reading import _verbatim
from roadkeep.verbs.refusing import EXIT_GATE, EXIT_OK, EXIT_USAGE, REFUSALS, _refused


def _merge(config: Config, args: argparse.Namespace) -> int:
    """Git's driver contract: leave the result in `ours`, exit 0 clean and 1 conflicted.

    The refusal writes too, and that is deliberate: git has handed the merge over by the
    time this runs, so a non-zero exit that left `%A` untouched would leave the reviewer a
    file that reads as though one side simply won.
    """
    # `--json` is the form of one argument on this command, and a request nothing else here can
    # honour (RK317). Argparse scopes a flag to the subparser rather than to the branch, so `merge
    # %O %A %B --json` parsed, was ignored, and exited as though the caller had been served —
    # worse than a refusal, because it tells them the request was understood. Named rather than
    # made to work: the driver has no answer to structure, git reading its exit code and the bytes
    # it leaves in `%A`, and the registration's report is one rendering for two surfaces (RK276)
    # rather than a second one for a flag.
    #
    # Read off the declaration and not off this branch's position (RK319), so the one surface that
    # passes `--json` on every call can know which argument makes that legal — and so the flag is
    # spelled from the parser rather than written twice.
    # Imported here and not at module scope: `cli` imports this module to wire the parser,
    # so a top-level import would be the cycle RK494 exists to keep out (RK260).
    from roadkeep.verbs.declaring import json_needs  # noqa: PLC0415 - RK1171

    needed = json_needs(args)
    if args.json and needed and not getattr(args, needed, False):
        print(
            f"roadkeep: --json is the form of --{needed}, which reads the wiring and writes "
            f"nothing; the driver leaves its answer in git's %A and an exit code, and "
            f"--register prints the lines it wrote",
            file=sys.stderr,
        )
        return EXIT_USAGE
    if args.check:
        # Before `--register`, so the two together read as the check: a `--check` that wrote
        # the attribute lines anyway would be the one thing this flag promises not to do.
        return _merge_check(config, args)
    if args.register:
        return _merge_register(config)
    if not (args.base and args.ours and args.theirs):
        print(
            "roadkeep: merge takes three files (git's %O %A %B), or --register, or --check",
            file=sys.stderr,
        )
        return EXIT_USAGE

    role = role_of(config, args.path or args.ours)
    if role is None:
        print(
            f"roadkeep: {args.path or args.ours} is not a file this project declares "
            f"(has: {', '.join(sorted(config.paths)) or 'none'}) — the driver merges "
            f"governed files and declines everything else",
            file=sys.stderr,
        )
        return EXIT_USAGE
    try:
        base, ours, theirs = (_verbatim(Path(p)) for p in (args.base, args.ours, args.theirs))
        merged = merge(config, role, base, ours, theirs)
    except REFUSALS as error:
        return _refused(error)

    if merged.clean:
        write_atomically(Path(args.ours), merged.text or "")
        summary = [f"merged {config.relative(config.path(role))} as {role}"]
        if merged.took:
            summary.append(f"took {', '.join(merged.took)}")
        if merged.removed:
            summary.append(f"removed {', '.join(merged.removed)}")
        if merged.reason:
            summary.append(merged.reason)
        print("roadkeep: " + "; ".join(summary))
        return EXIT_OK

    write_atomically(Path(args.ours), markers(ours, theirs))
    print(f"roadkeep: {merged.reason}", file=sys.stderr)
    return EXIT_GATE


def _merge_register(config: Config) -> int:
    try:
        registration = register(config)
    except REFUSALS as error:
        return _refused(error)
    for line in registration_report(registration, config.relative(registration.attributes), 0):
        print(line)
    return EXIT_OK


def _merge_check(config: Config, args: argparse.Namespace) -> int:
    """Ask whether git would run this driver at all, and write nothing (RK266, RK270).

    The verb RK266 exists for. `lint` was the other candidate and is the wrong one: it is the
    gate, it runs in CI, and there `.git/config` is a runner's rather than an author's — a
    stale-driver finding would fail builds over a fact about somebody else's machine. This is
    per-checkout, so it is asked per checkout, by someone who chose to ask.

    **Two lines and one exit code** (RK270). A driver is two writes that go missing for
    different reasons: the attribute is committed and travels, the config is per-clone and is
    the half a fresh clone lacks. Reporting them separately is what lets an answer be specific;
    exiting on their conjunction is what stops half a wiring from reading as a whole one.

    The halves are read independently and joined once, here (RK277): the config is only asked
    for where something routes to it. It is still *reported* either way — this narrows what the
    check demands and never what it says, because a driver configured where nothing reaches it
    is harmless and a driver silently not asked for is the silence this command exists to end.

    **And it is the one query on this command, so it is the one that answers as JSON** (RK275).
    The MCP surface reaches it as `merge_check` and passes `--json` on every call, and the halves
    are fields there for the reason they are two lines here: a caller that got one string would
    have to parse which half is broken out of prose this file is free to reword. `sound` is the
    exit code as a boolean, so nothing has to infer it from the absence of repairs.
    """
    wired = wiring(config)
    if args.json:
        print(json.dumps(wired.payload(config), indent=2))
    else:
        print(wired.stated())
    return EXIT_OK if wired.sound else EXIT_GATE


def _lint(config: Config, args: argparse.Namespace) -> int:
    try:
        # The mechanical pass runs first and the report is taken afterwards, so what is
        # printed is what is left — the whole point of RK16.
        applied = fix(config) if args.fix else Fix()
        report = lint(config, since=args.since, baseline=args.baseline)
    except HistoryUnavailable as error:
        print(f"roadkeep: no history to resolve against ({error})", file=sys.stderr)
        return EXIT_USAGE
    except (KeyError, OSError) as error:
        return _refused(error)

    passed = report.clean and not applied.refused
    # Absolute, and never relative to the working directory (RK299): the defect this answers
    # *is* a wrong working directory, so a spelling relative to one would print `.` and
    # attribute the report to wherever it was misread from.
    root = config.root.as_posix()
    if args.json:
        print(json.dumps(report.payload(config, applied, root), indent=2))
    else:
        report.stated(config, applied, root, quiet=args.quiet)
    return EXIT_OK if passed else EXIT_GATE


def _repair(config: Config, args: argparse.Namespace) -> int:
    """Apply what the gate already knows how to close, and print what it does not (RK422).

    The runner handed down is this module's own dispatcher, re-entered per step: the write
    lock is re-entrant by depth (RK117), so a step runs under the lock this command already
    holds rather than releasing it between repairs — which is what keeps a concurrent session
    from writing into the middle of one run.

    Stdout of each step is deliberately *not* suppressed. A repair that renumbered a line
    printed where it went, and a caller reading this run's output is the same caller who
    would have read that one — hiding it to make this report tidy would cost exactly the
    context the verb was written to save.
    """
    try:
        outcome = repair(config, _step(config), dry_run=args.dry_run)
    except (KeyError, OSError) as error:
        return _refused(error)

    root = config.root.as_posix()
    if args.json:
        print(json.dumps(outcome.payload(root, _served(config)), indent=2))
    else:
        print(outcome.stated(root))
        for line in outcome.warnings():
            print(line, file=sys.stderr)
    # Clean means clean, and `--dry-run` is never that: a run that wrote nothing has not
    # closed anything, so reporting 0 would tell a CI job the tree passes when it does not.
    if outcome.dry_run:
        return EXIT_OK if outcome.clean else EXIT_GATE
    return EXIT_OK if outcome.clean and not outcome.failed else EXIT_GATE


def _step(config: Config) -> Callable[[Sequence[str]], int]:
    """One repair step, parsed and dispatched the way any other invocation would be.

    Through the parser rather than by calling the handler: a remedy's argv is a command line
    and nothing else, so anything this accepts is something a caller could have typed — and
    a step that argparse would reject is a defect in the table (RK421 asserts the verb, this
    proves the flags) rather than a shortcut that only works from in here.

    Both names are imported inside the closure rather than at module scope, for the reason
    :mod:`roadkeep.verbs`' docstring gives: `cli` imports this module to wire its parser, so
    the dependency runs one way and the one edge back is taken at call time (RK260).
    """

    def run(argv: Sequence[str]) -> int:
        from roadkeep.cli import build_parser, dispatch  # noqa: PLC0415 - RK494

        parser = build_parser()
        try:
            args = parser.parse_args([*argv])
        except SystemExit:
            # argparse exits on a bad argv. A remedy that does not parse is this tool's
            # defect and not the caller's, so it is reported as a failed step rather than
            # taking the whole process down mid-repair.
            return EXIT_USAGE
        return dispatch(config, args)

    return run


def _explain(config: Config, args: argparse.Namespace) -> int:
    """The vocabulary, as a command (RK423) — which is L5 applied to the gate's own codes.

    Read-only and config-aware at once: the two rows L6 makes per-project (RK420) answer
    differently here than in the abstract, so the explanation a caller reads is the one that
    holds for *this* project rather than the one the table would give any project.
    """
    if args.code is None:
        listing = [explain(code, config) for code in remedy_codes()]
        if args.json:
            print(json.dumps([one.payload(_served(config)) for one in listing if one], indent=2))
        else:
            for one in listing:
                if one is not None:
                    # One line each: the listing is a menu, and a caller that wants the
                    # three fields asks for the code it found here.
                    print(f"{one.code:26} {one.kind:8} {one.remedy.doors[0].command}")
            print(f"{len(listing)} code(s) this gate can report")
        return EXIT_OK

    found = explain(args.code, config)
    if found is None:
        near = [code for code in remedy_codes() if code.startswith(args.code.split(".")[0])]
        print(
            f"roadkeep: {args.code} is not a code this gate reports"
            + (f"; did you mean {', '.join(near)}?" if near else ""),
            file=sys.stderr,
        )
        return EXIT_USAGE
    print(json.dumps(found.payload(_served(config)), indent=2) if args.json else str(found))
    return EXIT_OK


def _guard(config: Config, args: argparse.Namespace) -> int:
    """One command for every hook: the event is in the payload, not in the flags (RK22).

    Three shapes of answer, because the harness reads three: a `SessionStart` line of
    context, a `PreToolUse` decision, and a `Stop` block. None of them is ever an
    *approval* — a governed file is denied or asked about, and everything else is answered
    with an empty stdout, since `permissionDecision: "allow"` would grant the write rather
    than decline to judge it, waving through the permission rules the user set for every
    other file in the repository.

    The config discovered from `-C` is only this command's fallback: the payload names the
    directory, and the paths in it may belong to another project entirely.

    **The one door RK1170 left composing its own JSON**, and the reason is that there is no
    second register to unify it with: this verb has no plain answer at all. The three shapes
    are the *harness's* protocol keyed by hook event, not readings of one result — and they
    are three contracts rather than one shape written three times. What belongs to this tool
    is already on the records it prints: `str(refusal)` and `refusal.decision`.
    """
    payload = _payload()
    root = config.root
    if payload.get("hook_event_name") in START_EVENTS:
        notice = announce(payload, root)
        if notice is not None:
            print(
                json.dumps(
                    {
                        "hookSpecificOutput": {
                            "hookEventName": "SessionStart",
                            "additionalContext": str(notice),
                        }
                    },
                    indent=2,
                )
            )
        return EXIT_OK
    if payload.get("hook_event_name") in STOP_EVENTS:
        # Two questions and one answer: RK175's attestation says whether roadkeep wrote the
        # file, `lint` says whether it is correct, and the harness reads a single
        # `decision`. Attestation first because where both fire it is the cause of the
        # other, and a conforming hand-edit is the case where only it has anything to say.
        said = [
            str(found)
            for found in (attested(payload, root), review(payload, root))
            if found is not None
        ]
        if said:
            print(json.dumps({"decision": "block", "reason": "\n\n".join(said)}, indent=2))
        return EXIT_OK
    refusal = guard(payload, root)
    if refusal is not None:
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        # Derived from the tool the payload named (RK128): `deny` where it
                        # said which file it writes, `ask` where a shell command only
                        # mentioned one and what it does with it is nobody's to guess here.
                        "permissionDecision": refusal.decision,
                        "permissionDecisionReason": str(refusal),
                    }
                },
                indent=2,
            )
        )
    return EXIT_OK


def _payload() -> Mapping[str, object]:
    """The hook payload, or nothing at all — a guard that raises denies every write."""
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except (ValueError, OSError):
        # `ValueError` covers both halves: a payload that is not JSON, and one that is not
        # UTF-8 — stdin is strict on the way in (see `main`), and neither is worth a crash.
        return {}
    return data if isinstance(data, Mapping) else {}
