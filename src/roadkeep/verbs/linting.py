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
from roadkeep.guarding import (
    START_EVENTS,
    STOP_EVENTS,
    announce,
    attested,
    decide,
    review,
)
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
from roadkeep.verbs.declaring import _JSON_HELP, answers, withheld
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
    # One reading of the project for both answers (RK1283): this is the hook the harness
    # waits for before every `Edit`, and the config parse it used to make twice is the part
    # of an allowed call that is not free.
    barrier = decide(payload, root)
    refusal = barrier.refusal
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
    # Allowed, and one path still has something to say (RK1280). **No decision at all**: an
    # `allow` would grant the write and wave through the permission rules the user set for
    # every other file, which is the invariant this whole branch is written around — so what
    # is emitted is the message alone, and the harness decides as it would have anyway.
    if barrier.advice is not None:
        print(json.dumps({"systemMessage": str(barrier.advice)}, indent=2))
    return EXIT_OK


def _payload() -> Mapping[str, object]:
    """The hook payload, or nothing at all — a guard that raises denies every write.

    **And a line on stderr saying which** (RK1202). Silence is the right answer to a tool call
    this gate declines to judge: `permissionDecision: "allow"` would *grant* the write, waving
    through the permission rules the user set for every other file, so consent has to be an
    empty stdout. Nothing forced the *failure* to be silent too, and it was — a payload that
    will not parse produced no output and exit 0, byte for byte what an allowed path produces,
    and what a session with no engine produces, and what an ungoverned file produces. Four
    states, one answer, and the only one of them that is not a decision is this one.

    Measured in pportal. A session probed its guard by piping a payload from PowerShell, whose
    pipe does not deliver the UTF-8 this reader wants, saw exit 0 and filed a project note
    asserting nothing denied a hand edit there. The guard was working: the same bytes written
    to a BOM-less file and redirected in get the full denial. The note stood for four days,
    against a design that was fine.

    So the asymmetry is closed on the side that has no reason to be quiet. **Exit 0 stays** —
    a gate that fails a turn because it could not read its own input is the failure the
    launcher exists to avoid — and the harness ignores stderr, so the only audience is the
    person checking the thing is alive, which is exactly who was misled.

    The count and the opening bytes are named because they are what tells that person which
    of the two happened: a re-encoding pipe delivers the wrong bytes, and an empty read
    delivers none.
    """
    try:
        raw = sys.stdin.read()
    except (ValueError, OSError) as error:
        # `ValueError` covers the half a `read` can fail on: stdin is strict UTF-8 on the way
        # in (see `main`), so a payload in another encoding raises here rather than arriving
        # substituted — which is the failure this whole function is about, one layer down.
        return _unread(f"stdin could not be read ({error})", _ENCODING)
    if not raw.strip():
        return _unread("stdin was empty, so no hook payload arrived", _NOTHING)
    try:
        data = json.loads(raw)
    except ValueError as error:
        return _unread(f"stdin is not JSON ({error}); {_opening(raw)}", _ENCODING)
    if not isinstance(data, Mapping):
        # Valid JSON and not a payload: a list or a bare string parses and names no tool call.
        # The bytes arrived intact, so no encoding advice — this one is the caller's shape.
        return _unread(f"stdin is JSON but not an object; {_opening(raw)}", "")
    return data


#: What to try where the bytes themselves are wrong (RK1202). The measured cause: PowerShell's
#: pipe does not deliver the UTF-8 this reader wants, and the same payload written to a
#: BOM-less file and redirected in gets the full answer.
_ENCODING = (
    "A pipe that re-encodes is the usual cause, so write the payload to a UTF-8 file "
    "without a BOM and redirect it instead of piping."
)
#: And where nothing arrived at all, which is not a broken pipe but a call the harness did not
#: make. Named apart, because telling somebody to check their encoding when they typed the
#: command by hand is advice about a problem they do not have.
_NOTHING = (
    "The harness sends one on stdin, so this reads as the command being run by hand; "
    "redirect a payload in to exercise it."
)


def _opening(raw: str) -> str:
    """What arrived, bounded — the fact that tells a mangled pipe from an empty one (RK1202)."""
    head = raw[:_SHOWN].replace("\n", "\\n")
    more = "…" if len(raw) > _SHOWN else ""
    return f"{len(raw)} character(s) beginning {head!r}{more}"


#: How much of an unreadable payload the sentence quotes. Enough to recognise a BOM, a shell's
#: quoting or an HTML error page, and short enough that a hook's stderr stays one line.
_SHOWN = 40


def _unread(said: str, remedy: str) -> Mapping[str, object]:
    """Say that the gate did not run, and answer as though it had nothing to say (RK1202).

    Both halves matter. The empty mapping is what every caller already handles — no event, no
    tool, no decision — so nothing downstream learns a fourth state. The sentence is what stops
    that emptiness from being read as consent by the one reader who can act on it, and the
    clause that never varies is the one that was missing: **this is not a write being allowed.**
    """
    print(
        f"roadkeep: guard did not judge this call: {said}. This is the gate failing to read "
        f"its input, not a write being allowed."
        + (f" {remedy}" if remedy else ""),
        file=sys.stderr,
    )
    return {}


def declare_gate(subcommands: argparse._SubParsersAction) -> None:
    """This module's five verbs, declared where their handlers are (RK1171).

    `build_parser` called forty-nine blocks like this one in a row; what it calls now is an
    index over the modules that own them. The move is what RK1169 and RK1170 bought: the flags
    a verb declares, the reasons it withholds and the record it answers with are one file's,
    so a change to any of them is one file's too.

    The order inside is `build_parser`'s own — `merge` before the rest because that is where
    the block sat, and a verb's place in `--help` is a fact about the surface rather than
    about this module.
    """
    merge_parser = subcommands.add_parser(
        "merge",
        help="git's merge driver for a governed file: entries by id, prose by one side",
        description=(
            "Merge three versions of one governed file structurally. Every id is decided "
            "on its own against the ancestor, so two branches appending under one heading "
            "is two additions and not a conflict; an id both branches created is reported "
            "by name, because `renumber` moves one of them and a driver that picked a side "
            "would be choosing whose task disappears. Anything it cannot prove falls back "
            "to git's conflict markers and exits 1. `--register` wires it up, and `--check` "
            "reads the wiring back: a driver git can no longer run is otherwise silent until "
            "the merge it was registered for."
        ),
    )
    merge_parser.add_argument("base", nargs="?", help="the ancestor version (git's %%O)")
    merge_parser.add_argument(
        "ours", nargs="?", help="this branch's version, and where the result is written (%%A)"
    )
    merge_parser.add_argument("theirs", nargs="?", help="the other branch's version (%%B)")
    merge_parser.add_argument(
        "--path",
        help="the file's pathname in the repository (%%P) — which governed file this is",
    )
    merge_parser.add_argument(
        "--register",
        action="store_true",
        help="write the .gitattributes lines and print the git config this driver needs",
    )
    merge_parser.add_argument(
        "--check",
        action="store_true",
        help="read the driver back out of git config and say whether it still runs; write nothing",
    )
    # For `--check` and for nothing else on this command (RK275). The MCP surface passes `--json`
    # on every call and never exposes it, because a structured answer is the difference between
    # one an agent can audit and one it re-reads the file to check (L5) — and the driver path has
    # no answer to structure: git reads its exit code and its bytes in `%A`, not its stdout.
    # Argparse scopes a flag to the subparser and not to the branch, so the help says which
    # branch honours it and `_merge` refuses the others (RK317).
    merge_parser.add_argument(
        "--json",
        action="store_true",
        help="machine-readable form of --check; refused on the driver and on --register",
    )
    # `--check` is a pure query wearing the driver's subparser (RK275), so the claim this parser
    # makes is the one `writes_when` was built for, inverted the only way it can be: the command
    # reads, and the two arguments that turn it into a write say so. `ours` is where git has the
    # driver put the result, so a merge that names it writes; `--register` writes `.gitattributes`.
    # Neither is set by a `--check`, which is what lets it take no lock and be free to ask (L5).
    # `json_needs` beside them for the reason they are here (RK319): which argument this command's
    # `--json` is the form of is a fact about the command, and left as an `if` in the handler it
    # was a constraint on every surface serving it that no surface could read.
    merge_parser.set_defaults(
        handler=_merge,
        reads_only=True,
        writes_when=("register", "ours"),
        json_needs="check",
    )

    lint_parser = subcommands.add_parser(
        "lint",
        help="validate every governed line; exit 1 when anything drifted",
        description=(
            "The backstop for what bypassed `add`. Reports every violation, every line "
            "that does not round-trip and every dep nothing can satisfy — and exits "
            "non-zero, which is the entire difference between a gate and advice."
        ),
    )
    lint_parser.add_argument(
        "--fix",
        action="store_true",
        help="normalize what is mechanical first, then report what needs a decision",
    )
    lint_parser.add_argument(
        "--since",
        metavar="REV",
        help=(
            "also report a rationale section edited since REV whose task line was not "
            "(RK36): HEAD in a commit hook, the base branch in CI"
        ),
    )
    lint_parser.add_argument(
        "--baseline",
        metavar="REV",
        help=(
            "report only what this working tree added since REV, forgiving the standing "
            "debt (RK84): the gate a repository can adopt before it has paid it off"
        ),
    )
    lint_parser.add_argument(
        "--quiet",
        action="store_true",
        help="print only the summary line, for a hook that wants the exit code",
    )
    lint_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    # The gate is a read and `--fix` is the write in it (RK168). Until it said so, the command
    # a hook, a CI job and every turn's end run took the *write* lock — so a checkout somebody
    # else was writing answered with exit 1, which from this command means the format drifted.
    #
    # `--fix` still refuses on a busy checkout rather than repairing half of it, and that is
    # deliberate: the refusal names the other process, re-running is the answer, and splitting
    # one command into a locked half and an unlocked half is a second mechanism for the rarer
    # case. What the flag buys is that the *report* never waits on a write at all.
    withheld(
        lint_parser,
        fix='it writes, and RK16 keeps the derived-only repair where a human is standing',
        since="a git revision, which is a fact about the checkout the caller cannot see from here — and the gate's answer is about the tree as it is",
        quiet='how a terminal prints, which is not a thing a JSON payload has',
    )
    lint_parser.set_defaults(handler=_lint, reads_only=True, writes_when="fix")
    # `list`'s pair, one verb over: `--quiet` shortens the printed report and `--json` is a
    # different form of the same read (RK467).
    answers(
        lint_parser, ("quiet", "the report as its summary line"), ("json", "the payload")
    )

    repair_parser = subcommands.add_parser(
        "repair",
        help="run the report back: apply every finding whose remedy is one command",
        description=(
            "The gate says what is wrong and, since RK420, what closes it. This spends "
            "that: the mechanical pass, then every finding whose remedy is a complete "
            "command, one at a time with the report re-read between them. What needs a "
            "sentence or a choice is printed instead — that half is yours, and the tool "
            "writing it would be the generator this project refuses. Exits 1 while "
            "anything is left, which is the gate's own contract and not a second one."
        ),
    )
    repair_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the commands and run none of them",
    )
    repair_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    repair_parser.set_defaults(handler=_repair, reads_only=False)

    explain_parser = subcommands.add_parser(
        "explain",
        help="what one gate code means, what produces it, and which doors close it",
        description=(
            "A finding is about one line; a code is about a class, and there has never "
            "been anywhere to look the second one up. Three fields and no more — the "
            "worked example is the argv the finding already carries. With no code, lists "
            "every one this gate can report, which is the vocabulary it never published."
        ),
    )
    explain_parser.add_argument(
        "code",
        nargs="?",
        help="a code as `lint` prints it, e.g. id.duplicate; omitted, lists them all",
    )
    explain_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    explain_parser.set_defaults(handler=_explain, reads_only=True)

    guard_parser = subcommands.add_parser(
        "guard",
        help="answer a Claude Code hook: deny a hand-edit, or lint as the turn ends",
        description=(
            "Read one hook payload on stdin and answer it on stdout (RK22). A "
            "`PreToolUse` payload naming a governed file is denied with the command to "
            "call instead; a `Stop` payload runs `lint` and blocks on what it refuses. "
            "Everything else is answered with silence. Not for a human to call: the "
            "harness runs it before every write, so it always exits 0 — a non-zero exit "
            "is read as the hook itself having failed, which would deny nothing and "
            "report a broken hook on every edit in the session."
        ),
    )
    guard_parser.set_defaults(handler=_guard, tolerates_config_error=True, reads_only=True)

