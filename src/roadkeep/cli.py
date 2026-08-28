"""The command surface (opened by RK4, extended one subcommand per task).

Design rules for everything added here, so that later commands do not each invent
their own:

* **Plain stdout is composable, `--json` is for reasoning.** `roadkeep next-id` prints
  `RK32` and nothing else, so it can be substituted into another command; `--json`
  carries the provenance — which file and line the answer came from — because an
  answer an agent cannot audit gets verified by reading the file, which is the cost
  the command existed to remove (L5).
* **Exit codes are the contract.** 0 success, 1 the gate says no (`lint`, from RK14),
  2 usage or configuration error. A gate that reports in prose is advice. A refused
  `add` (RK5) exits 2 and not 1: what has to change is the caller's input, not the
  file — 1 is reserved for a file that is already wrong.
* **Every mutator emits the event and stops there (RK38).** A write already succeeds or
  refuses with an exit code, so what a hook is missing is not a listener but a payload:
  the id, the block, and whether that block still holds an open line. Deciding what to do
  next belongs to the `PostToolUse` hook (RK22) or the Action (RK17) — a `[hooks]` table
  running commands would make `uvx roadkeep` an executor of whatever a repo declares.
* **Errors name the fix, and a fault names one more move.** A `ConfigError` prints every
  problem it found, once — and a non-zero exit closes with the `report` command that
  captures it, argv already substituted (RK86). Held here rather than at each of the twenty
  refusals, because the exit code is the contract they all already leave through. Not on a
  **verdict**, which is a read-only command's own 1 (RK271): `lint` naming a finding has
  answered the question it was asked, and doubting itself afterwards is the tool's
  highest-traffic output saying nothing.
* **stdout is forced to UTF-8.** The markers are emoji and the default Windows console
  encoding is cp1252, which raises `UnicodeEncodeError` mid-write and leaves a
  half-printed report. That cost three interrupted runs while this file's own package
  was being written.

`argparse`, not `click`: a tool meant to run as `uvx roadkeep` in someone else's CI
pays for every dependency, and the whole command surface is argument parsing.
"""

from __future__ import annotations

import argparse
import difflib
import sys
import tomllib
import traceback
from collections.abc import Mapping, Sequence

from roadkeep.attesting import attest
from roadkeep.capturing import offer
from roadkeep.config import Config, ConfigError
from roadkeep.locking import LockBusy, exclusive
from roadkeep.provenance import engine, invocation, invoked, read_by
from roadkeep.serving import Prose, spelled
from roadkeep.remaining import declared
from roadkeep.verbs.adopting import declare_wiring
from roadkeep.verbs.authoring import declare_lines
from roadkeep.verbs.linting import declare_gate
from roadkeep.verbs.querying import declare_reads
from roadkeep.verbs.declaring import (
    Answer,
    _A_TYPO,
    _VALUED,
    _Verb,
    writes_when,
)
from roadkeep.verbs.reading import _one_pipe, _piped, harden
from roadkeep.verbs.refusing import EXIT_GATE, EXIT_OK, EXIT_USAGE
from roadkeep.verbs.sections import declare_places
from roadkeep.verbs.shipping import declare_departures




class _Version(argparse.Action):
    """Print which engine answered, not just its number (RK79).

    An `action="version"` string is built with the parser, on every run — and naming the
    tree costs a git call. This defers it to the flag being passed, so the answer a plugin
    cache and a checkout disagree on costs nothing on the commands that do the work.
    """

    def __init__(self, option_strings: Sequence[str], dest: str, **kwargs: object) -> None:
        super().__init__(option_strings, dest, nargs=0, default=argparse.SUPPRESS, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None) -> None:  # type: ignore[no-untyped-def]
        print(engine())
        parser.exit(EXIT_OK)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="roadkeep",
        description="Own the writes to a project's roadmap, changelog and rationale.",
        # The top level too (RK1032): `-C` and `--version` are the only options here, and
        # `--vers` reaching the second is the same class as `--f` reaching `--fix` — one
        # rule for the whole surface, so no parser is the one that kept the affordance.
        allow_abbrev=False,
    )
    parser.add_argument(
        "--version",
        action=_Version,
        help="the version, the commit it is at and the directory it ran from",
    )
    parser.add_argument(
        "-C",
        "--directory",
        default=".",
        metavar="PATH",
        help="where to start looking for roadkeep.toml (default: the current directory)",
    )
    # Every subcommand is a `_Verb` (RK339), and a nested one inherits the class from its
    # parent, so `section add` is one too — a pair of near-twins one level down declares
    # itself the same way.
    subcommands = parser.add_subparsers(
        dest="command", required=True, parser_class=_Verb
    )

    declare_lines(subcommands)
    declare_gate(subcommands)

    declare_places(subcommands)

    declare_departures(subcommands)

    declare_reads(subcommands)

    declare_wiring(subcommands)

    return parser







def _verb_reached(parser: argparse.ArgumentParser, argv: Sequence[str]):
    """The deepest subparser this argv named, and its path — `('ship',)`, `('non-goal',
    'list')` (RK1026).

    Read by walking the tree the way argparse does rather than by re-listing the verbs: the
    parser is the authority on what a command is, and a second table would answer about a
    surface that has moved. `-C <path>` is the one option before the verb that consumes what
    follows it, in both spellings, which is `_crossed`'s rule and the same reason for it.
    """
    reached, path, skipping, opened = parser, [], False, len(argv)
    for index, token in enumerate(argv):
        if skipping:
            skipping = False
            continue
        if token.startswith("-"):
            skipping = token in _VALUED
            continue
        choices = next(
            (
                action.choices
                for action in reached._actions
                if isinstance(action, argparse._SubParsersAction)
            ),
            None,
        )
        if not choices or token not in choices:
            break
        opened = min(opened, index)
        reached, _ = choices[token], path.append(token)
    return reached, tuple(path), opened


def _options(parser: argparse.ArgumentParser) -> tuple[str, ...]:
    """Every long option one verb declares, in the order its parser does — `--help` aside."""
    return tuple(
        option
        for action in parser._actions
        for option in action.option_strings
        if option.startswith("--") and option != "--help"
    )


def _positionals(parser: argparse.ArgumentParser) -> tuple[str, ...]:
    """Every argument one verb takes by position, in the order its parser declares (RK1254).

    :func:`_options`' other half, and the reason it needed one: a verb's surface is not only
    its flags, so a refusal built from options alone answers `show --id RK1` with a list that
    cannot contain `show RK1`.

    The **metavar** where the parser declares one and the dest otherwise, because that is what
    `--help` calls it and a refusal spelling it a second way would be a third name for one
    argument. A subcommand slot is not one of these: `section` reaches `section add` through
    an action whose choices are verbs, and naming it here would offer a command as a value.
    """
    return tuple(
        (action.metavar or action.dest)
        for action in parser._actions
        if not action.option_strings and not isinstance(action, argparse._SubParsersAction)
    )


def _first(argv: Sequence[str], token: str) -> int | None:
    """Where a token was typed, or None — `--flag=value` included, which argv splits."""
    for index, one in enumerate(argv):
        if one == token or one.startswith(f"{token}="):
            return index
    return None


def _unrecognised(
    parser: argparse.ArgumentParser, argv: Sequence[str], extra: Sequence[str]
) -> str:
    """The refusal this tool writes for a flag its own parser does not declare (RK1026).

    `ship RK1 --note "…"` used to print argparse's usage line, the full list of thirty-odd
    verbs, `unrecognized arguments:` and then **the entire rejected value** — often a
    paragraph meant for `--why`, burying the one line that matters under text the caller had
    just typed. The verb was right; the flag was wrong; nothing on screen said so.

    So the answer is the verb's **own** surface, which is short, rather than the tool's,
    which is not, and the option token alone, never its value. A near miss is named first
    where `difflib` finds one — and where it does not, which is the common case (`--note`
    against `--why` is no edit-distance hit), the list is the whole answer.

    A stray positional keeps its own sentence: `show RK1 RK2` is one argument too many, and
    naming the flags of a verb that takes an id would be advice about a mistake nobody made.

    **And the mirror of that, which was not made** (RK1254). `show --id RK1` was answered with
    `takes --no-body, --json` — short, correct, and unable to contain `show RK1`, because a
    verb's surface is not only its flags. Met four times over on one throwaway project:
    `show --id`, `retire --id`, `renumber --from`, `brief --task`. The mistake is invited
    rather than hypothetical — `add` really does take `--id`, so a caller who learned it
    there spells it that way on the verbs where the id is positional.

    **Which surface answers is decided by where the flag was typed** (RK1032). A flag before
    the verb is the top level's — `roadkeep --vers lint` is somebody reaching for
    `--version`, and answering with `lint`'s options would send them to a `--help` that has
    none of what they wanted.
    """
    reached, path, opened = _verb_reached(parser, argv)
    flags = [token for token in extra if token.startswith("-")]
    if flags and (found := _first(argv, flags[0])) is not None and found < opened:
        reached, path = parser, ()
    # The name and the command are two things: the top level is called `roadkeep` in a
    # sentence and reached as no word at all, so one string for both would print
    # `roadkeep roadkeep --help` — a door that opens nothing.
    verb = " ".join(path) or "roadkeep"
    door = f"{invocation()} {' '.join(path)}".rstrip()
    if not flags:
        loose = ", ".join(repr(token) for token in extra)
        return (
            f"roadkeep: `{verb}` takes no further argument, and got {loose}: "
            f"`{door} --help` is what it does take"
        )
    declared = _options(reached)
    # Matched **dashes off** (RK1254): `--id` against `id` is not an edit-distance hit and is
    # the same word, which is the whole shape this is about — `add` declares `--id`, so a
    # caller who learned it there spells it that way where the id is positional.
    by_position = _positionals(reached)
    near = difflib.get_close_matches(flags[0], declared, n=1, cutoff=_A_TYPO)
    guessed = difflib.get_close_matches(
        flags[0].lstrip("-"), by_position, n=1, cutoff=_A_TYPO
    )
    if near:
        guess = f" — did you mean `{near[0]}`?"
    elif guessed:
        # Named as a *position* and not as a flag, because that is the fact the caller got
        # wrong: printing `` `id` `` alone would read as one more option to pass.
        guess = f" — `{guessed[0]}` is taken by position: `{door} <{guessed[0]}>`"
    else:
        guess = ""
    takes = ", ".join(declared) or "no options of its own"
    rows = [
        f"roadkeep: `{verb}` declares no {flags[0]}{guess}",
        f"  takes    {takes}",
    ]
    if by_position:
        # Its own row and never folded into `takes` (RK1254): which of the two an argument is
        # is exactly what the caller had wrong, and one list holding both would spell `<id>`
        # beside `--json` as though the difference were punctuation.
        rows.append(f"  by order {' '.join(f'<{one}>' for one in by_position)}")
    rows.append(f"  see      `{door} --help`")
    return chr(10).join(rows)


def _crossed(argv: Sequence[str]) -> str | None:
    """The other surface's name for the verb this argv asked for, if that is what it is (RK353).

    Read from :func:`~roadkeep.serving.spelled`, which is the tool table's answer: the parser is
    the authority on what a *command* is and the table is the authority on what a **tool** is
    called, so this asks rather than carrying a second mapping that could disagree with either.

    The first token that is not an option, and nothing after it: the verb is the first positional
    argument, and scanning further would read a `--why` somebody wrote about `scope` as the
    command they typed. `-C <path>` is the one option before the verb that consumes what follows
    it, in both spellings and in the `=` form, which needs no skip at all.
    """
    skipping = False
    for token in argv:
        if skipping:
            skipping = False
            continue
        if token.startswith("-"):
            skipping = token in _VALUED
            continue
        line = spelled(token)
        if line is None or line == token:
            # Silent where the two surfaces agree, which is most of them: `add` is `add`, so a
            # refusal about a missing `--block` would otherwise be told the verb it already used.
            return None
        return (
            f"roadkeep: `{token}` is what this tool publishes that verb as over MCP; at this "
            f"CLI the same act is `{invocation()} {line}`, which takes the arguments you typed."
        )
    return None


def main(argv: Sequence[str] | None = None) -> int:
    # Before anything is parsed, and in the module that owns the flag: a section's prose
    # arrives on a pipe (RK9), the governed files are UTF-8, and every reader of what stdin
    # allowed is four frames down a handler. See :func:`~roadkeep.verbs.reading.harden`.
    harden()
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    try:
        # `parse_known_args` and not `parse_args`, so the one refusal argparse used to write
        # is one this tool writes (RK1026). Every other parse failure — a missing required
        # argument, a verb that is not a verb — still raises below, where argparse's message
        # is about the thing the caller got wrong and not about thirty verbs they did not.
        args, extra = parser.parse_known_args(argv)
        if extra:
            print(_unrecognised(parser, argv, extra), file=sys.stderr)
            print(offer(argv), file=sys.stderr)
            return EXIT_USAGE
    except SystemExit as exit_:
        # argparse refuses before a handler exists, and its exit 2 is one of the three
        # places RK86 names. The argv is all this knows, and all the offer needs.
        if exit_.code:
            crossed = _crossed(argv)
            if crossed is not None:
                print(crossed, file=sys.stderr)
            print(offer(argv), file=sys.stderr)
        raise
    try:
        config = Config.discover(args.directory)
    except (ConfigError, tomllib.TOMLDecodeError, OSError) as error:
        # A TOML *syntax* error never reached `ConfigError`, so the commands declared to
        # survive a broken config did not survive the way it is most often broken — and
        # `report`, whose whole purpose is the session where something is wrong, crashed
        # on the file it was about to carry as evidence.
        if not getattr(args, "tolerates_config_error", False):
            # And which build read it (RK1150): over MCP that clause has been on this refusal
            # since RK155, and at a terminal the same message named the file, the key and an
            # allowed set that is *this* version's — with no way to tell a typo from a config a
            # newer roadkeep wrote. One spelling for both surfaces, so they cannot drift.
            print(f"roadkeep: {error}{read_by()}", file=sys.stderr)
            return EXIT_USAGE
        # `guard` (RK22) is the one command that has to survive a broken config: it runs
        # before every write in the session, so failing here would turn one typo in
        # `roadkeep.toml` into a repository nobody can edit. It resolves its own config
        # from the payload anyway — one hook process serves every project a session sees.
        config = Config.default(args.directory)
    # Recorded here because this is the one surface that has one: a refusal that computed the
    # address the caller was missing can then offer the same call with it filled in, instead of a
    # sentence to read, extract and retype (RK1149). After `discover`, so a run that never reached
    # a project leaves the slot as the served path expects to find it — empty.
    invoked(argv)
    faulted = False
    try:
        code = dispatch(config, args)
    except LockBusy as busy:
        print(f"roadkeep: {busy}", file=sys.stderr)
        code = EXIT_GATE
    except Exception:
        # A traceback that reaches a terminal raw is a session that ends, and RK86's whole
        # subject is what an agent does next. Printed, then closed with the offer, then
        # answered with an exit code — 1 and not 2, because nothing about the caller's
        # input is what has to change.
        traceback.print_exc()
        code = EXIT_GATE
        # The one thing the exit code cannot say afterwards: this 1 is the tool falling over
        # and not the verdict a read was asked for, which is the difference RK271 turns on.
        faulted = True
    if code != EXIT_OK:
        _may_offer(argv, args, code, faulted=faulted)
    return code


def dispatch(config: Config, args: argparse.Namespace) -> int:
    """Run one command's handler, under the write lock unless its parser only reads (RK117).

    Here and not inside :func:`main`, because the MCP server dispatches the same parsed
    args in-process and never goes through `main` (RK24) — which is the write path an agent
    actually uses, so a lock only `main` took would be a lock the defect walks around.

    Every command writes unless its parser said otherwise. The default is the locked one
    because that is the safe way to be wrong: a query serialised against a write costs
    milliseconds, and a write that is not serialised is two lines with one id.

    A read that *can* write says which flag makes it one (RK167). Three commands do —
    `pick --claim`, `brief --claim`, `claims --prune` — and until they declared it, each
    arranged its own lock somewhere else while `reads_only=True` described their default flags
    rather than the command. The decision stays here, where the one rule is; what the flag's
    own writer still keeps is a re-entrant lock of its own, because indivisibility is a promise
    to *every* caller and not only to this dispatcher (RK117).
    """
    # One question per call, before either branch (RK489): a verb asked two answers one of
    # them for, and the write lock is the wrong place to discover it.
    refused = _one_answer(args)
    if refused is not None:
        return refused
    # Which arguments read a pipe is the parser's claim, resolved once (RK1176). Here for
    # `_one_answer`'s reason: a handler resolving its own is a handler that can be written
    # without one, which is exactly what happened — `ship --superseded-design -` published the
    # dash, and `--why - --superseded-design -` was not refused although the refusal existed.
    refused = _read_prose(args)
    if refused is not None:
        return refused
    if _only_reads(args):
        return args.handler(config, args)
    refused = _behind(config, args)
    if refused is not None:
        return refused
    with exclusive(config.root):
        code = args.handler(config, args)
        # Still under the lock, and after the handler rather than before: what is recorded
        # is the bytes a verb left, so a later turn can say that bytes which are not these
        # arrived some other way (RK175). A refusal wrote nothing and re-records the same
        # digests, which is the right answer and not a special case.
        attest(config)
        return code


def _behind(config: Config, args: argparse.Namespace) -> int | None:
    """Refuse a governed write from a copy older than the one this project pinned (RK1235).

    RK1230 handed a shell caller the command reaching the right copy and left the write
    unguarded, which its own design said out loud. The failure it leaves is quiet: a copy
    behind the wired one does not fail, it agrees with a rule that has *moved* and writes a
    line its own version thinks legal — which the project's gate then reports, after the line
    has landed and by then as the file's problem rather than as the pen's. `engines` already
    exits 1 on that, and nothing consulted it before a write.

    **Two conditions, and both are the point.** Most disagreement between three copies is
    legitimate: a developer runs a checkout on purpose, CI runs the action at a ref,
    `install --vendor` exists so a project can hold a version. A refusal firing on those gets
    routed around within a week, so this fires only where

    * the verdict is `behind` and not merely `unpinnable` — the modified checkout is where a
      developer lives, and RK418 separated the two exactly so this could tell them apart; and
    * `[install] enforced` is declared — the project *saying* the registered plugin is the
      copy that should write here (L6), and the whole standing this has. Without it, refusing
      would be this tool guessing at a setup it cannot see. Its own key since RK1240: it read
      `pinned` first, which is a decision about a **different pair** — the surfaces vendored
      into a project against the engine answering — so a project that had quieted one finding
      was being read as having asked for a refusal on every write.

    So it costs an attribute read on every project that has not asked, which is every project
    by default. Past that flag it costs a **version comparison**, and git only where the two
    versions match — :func:`~roadkeep.installing.behind` is what pays for the sha, and its
    docstring carries the measurement RK1235 shipped without (RK1237).

    **A door and not a wall**, which is the other half of the design: the message carries
    `engines --invoke`, so the caller re-runs the same command through the copy that is right
    rather than learning that a copy exists. And `wiring=True` writes are let through — `init`,
    `install` and `uninstall` are how a project changes *which copies exist*, and `capture
    filed` records what this tool did wrong. Refusing those would leave the pin with no way
    to be satisfied and a defect in this tool with no way to be filed.

    `EXIT_GATE` and not `EXIT_USAGE`: nothing about the caller's input has to change. The
    argv is right and the copy running it is not.
    """
    if not config.install_enforced or getattr(args, "wiring", False):
        return None
    from roadkeep.installing import behind, engines  # noqa: PLC0415 - RK260

    if not behind(config.root):
        return None
    # Only now, and only to say the two versions: the refusal is already decided, so the read
    # that composes its message is off the path every allowed write takes (RK1237).
    read = engines(config.root)
    print(
        f"roadkeep: refused, nothing written: this copy is {read.running.version} at "
        f"{read.running.revision} and the project pinned "
        f"{read.plugin.version if read.plugin else '—'} — a write from here would be judged "
        f"by rules it does not hold\n"
        f"  the copy to run this command through is what `{invocation()} engines --invoke` "
        f"prints, so the same argv reaches the pen the pin names",
        file=sys.stderr,
    )
    return EXIT_GATE


#: Every place this package returns `EXIT_GATE` whose 1 is an **answer**, addressed as
#: `<module under the package>:<function>` and valued by how that is said (RK1421).
#:
#: A census, because two of these were found by running the command and reading the stderr.
#: RK271 exempted `lint`; RK1419 found `lint --fix` and `repair` still offering, a year later,
#: by reading one; RK1420 found the identical thing at `install --check` the next day. Neither
#: was a red, and there was nothing anywhere that could have made one — so a fourteenth site
#: arrives with whatever a future verb decides its non-zero means.
#:
#: `tests/test_capturing.py` walks the package for those returns and holds the two tables
#: below to be exactly what it found, which is the shape `FIELDS` and `_PASSES` already use.
#: It settles nothing about a new site: what it refuses is one arriving unnamed. **The
#: behaviour is held per verb** by the tests that measured each of these, and never here — a
#: list saying `lint` is a verdict is not evidence that its stderr is empty.
GATE_VERDICTS: Mapping[str, str] = {
    "verbs/adopting.py:_engines": (
        "the copies answering here disagree, which is the whole of what this read was asked; "
        "`reads_only` is where the parser says so"
    ),
    "verbs/adopting.py:_install": (
        "`--check` found surfaces that differ and already named `install` as the write that "
        "closes them; stated by the run, this verb reaching the code from nowhere else"
    ),
    "verbs/adopting.py:_uninstall": (
        "`--check` found entries still wiring this project, and the write that takes them out "
        "is the same verb without the flag; stated by the run"
    ),
    "verbs/adopting.py:_replay": (
        "the capture stopped reproducing, which is the answer this verb exists to give — and "
        "a capture is already a report about this tool, so offering to file one is a regress"
    ),
    "verbs/linting.py:_merge_check": (
        "git would not run this driver, which is the one query that command takes; `reads_only`"
    ),
    "verbs/linting.py:_lint": (
        "the gate found something, which is RK271's own case and this tool's highest-traffic "
        "output; declared by the parser, so `--fix` is the same answer by the same reader"
    ),
    "verbs/linting.py:_repair": (
        "findings are left, which is what `lint` says about the same files; declared by the "
        "parser and withdrawn by the run for a step whose argv came back non-zero"
    ),
    "verbs/querying.py:_verdict": (
        "a draft this read was handed does not fit, which is the one bit the caller asked for"
    ),
    "verbs/shipping.py:_reversals": (
        "the decision asked about was reversed, which is the answer and not a failure to give "
        "one; `reads_only`"
    ),
}

#: The other half, and the reason each keeps the offer (RK1421). Three, and every one of them
#: is a place where the rule that just ran might be the wrong rule — which is what RK86
#: measured and the only thing the offer is for.
GATE_FAULTS: Mapping[str, str] = {
    "cli.py:_behind": (
        "a write refused because the copy answering is behind the plugin this project "
        "registered: the refusal is about the wiring, and whether that rule is right is "
        "exactly what a caller who thinks it is not should be able to say"
    ),
    "verbs/linting.py:_merge": (
        "the driver could not prove its own output and left git's conflict markers, which is "
        "the verb RK484 wrote an offer specifically for"
    ),
    "verbs/refusing.py:_refused": (
        "a round trip that stopped holding, or a file that moved between the read and the "
        "write — where what may be wrong is this package's own parser"
    ),
}


def _is_verdict(args: argparse.Namespace) -> bool:
    """Whether this parser said its `EXIT_GATE` is an answer rather than a fall (RK1419).

    Read off `args` for `_only_reads`'s reason: the fact belongs to whoever knows it. A
    parser declares it where every exit of that verb means one thing (`lint`, `repair`); a
    handler writes it where a flag decides — `repair` sets it back to false for a step that
    came back non-zero, and `install --check` sets it true, its verb having no other route
    to that code.

    Absent on every verb that never declared one, which is the default and is right: a write
    exiting 1 is a fall unless somebody has said what else it could be.
    """
    return bool(getattr(args, "verdict", False))


def _only_reads(args: argparse.Namespace) -> bool:
    """Whether this argv is the query its parser declared, or the write a flag turned it into.

    Read off `args` and not from a list here, so the answer comes from the parser that already
    declares it — and a `writes_when` naming an argument that parser does not accept is a test
    failure rather than a lock silently not taken (`tests/test_locking.py`).

    One argument or several (RK307): `claim` writes on either of two, and a declaration that
    could only name one would have left the second taking no lock at all — the failure this
    mechanism exists to make impossible, arriving through the one shape it could not state.
    """
    if not getattr(args, "reads_only", False):
        return False
    return not any(getattr(args, flag, False) for flag in writes_when(args))


def _reaches(args: argparse.Namespace, one: Prose) -> bool:
    """Whether this argv sends that argument to the pipe (RK1176).

    :meth:`Prose.reached_by` asks the same question of a tool's arguments mapping, where an
    argument nobody set is *absent*; on a namespace every dest exists and `None` is how absence
    arrives, so the reading is spelled here rather than bent into that one.
    """
    if one.gated_by and getattr(args, one.gated_by, None) is None:
        return False
    if one.unless and getattr(args, one.unless, None) is not None:
        return False
    value = getattr(args, one.dest, None)
    return one.omitted if value is None else value == one.sentinel


def _spelled(one: Prose) -> str:
    """A declared prose argument as the CLI documents it — a refusal names what was typed."""
    return f"--{one.dest.replace('_', '-')}"


def _read_prose(args: argparse.Namespace) -> int | None:
    """Resolve every prose argument this argv sent to the pipe, or refuse (RK1176).

    ``None`` where nothing asked for stdin, which is every call to a verb that declares no
    prose. Run from :func:`dispatch`, so one pass answers for both surfaces and no handler
    carries a copy — the shape `_one_answer` and `_only_reads` already have.

    **The refusal is asked here and can no longer be skipped.** `_one_pipe` existed and was
    consulted in one handler, so `ship --why - --superseded-design -` sent two arguments to one
    stream and the second kept its dash: a refusal that is documented and not asked is worse
    than none, because the documentation promises it.

    Only the sentinel, and never the *omitted* argument. Whether a verb with no value at all
    should block on a pipe is that verb's own question — `section add` reads, `section amend`
    refuses — and answering it here would turn `Prose.omitted` into a rule about arguments the
    caller never mentioned.
    """
    declared: tuple[Prose, ...] = getattr(args, "reads_stdin", ()) or ()
    # The clash first and over *every* argument that reaches the pipe, including one reaching it
    # by being omitted: resolving the sentinel first is what made `add --why - --section X` stop
    # being refused, because by the time the handler looked, `--why` no longer held a dash.
    reaching = [one for one in declared if _reaches(args, one)]
    if len(reaching) > 1:
        clash = _one_pipe(*[(_spelled(one), True) for one in reaching])
        print(f"roadkeep: {clash}", file=sys.stderr)
        return EXIT_USAGE
    asked = [one for one in declared if getattr(args, one.dest, None) == one.sentinel]
    if not asked:
        return None
    if len(asked) > 1:
        # Spelled as the CLI documents them, because that is what the caller typed: a refusal
        # naming `superseded_design` is about a flag nobody passed.
        clash = _one_pipe(*[(_spelled(one), True) for one in asked])
        print(f"roadkeep: {clash}", file=sys.stderr)
        return EXIT_USAGE
    (one,) = asked
    try:
        setattr(args, one.dest, _piped(getattr(args, one.dest)))
    except (OSError, UnicodeDecodeError, ValueError) as error:
        # The same codes the handlers gave this read: prose that is not UTF-8 is bad input, and
        # a stream this tool could not harden says so in the words RK455 composed for it.
        print(f"roadkeep: {error}", file=sys.stderr)
        return EXIT_USAGE
    return None


def _one_answer(args: argparse.Namespace) -> int | None:
    """Refuse a call that asked two questions, out of what its parser declared (RK489).

    ``None`` where the call is one question, which is every call to a verb that declares
    nothing. Run from :func:`dispatch`, so the refusal is the same on both surfaces and no
    handler carries a copy of it.
    """
    subjects: tuple[Answer, ...] = getattr(args, "subjects", ())
    given = [one for one in subjects if one.given(args)]
    if len(given) > 1:
        print(
            f"roadkeep: one answer per call: {given[0].asked(args)} or "
            f"{given[1].asked(args)}, not both",
            file=sys.stderr,
        )
        return EXIT_USAGE
    asked = given[0] if given else None
    for (flag, option, default), (subject, names, _) in getattr(args, "narrowing", ()):
        if getattr(args, flag, default) == default:
            continue
        if asked is None or not asked.holds(subject):
            # Both halves, because the two states are different mistakes: a subject was named
            # and it is not this flag's, or none was and the flag cannot stand alone.
            beside = (
                f"and {asked.given(args)[0]} is a different subject"
                if asked is not None
                else "so pass it too"
            )
            print(f"roadkeep: {option} narrows {names}, {beside}", file=sys.stderr)
            return EXIT_USAGE
    return None


def _may_offer(
    argv: Sequence[str], args: argparse.Namespace, code: int, *, faulted: bool = False
) -> None:
    """Close a **fault** with the capture command, and a verdict with nothing (RK86, RK271).

    One place and not twenty: every refusal in this file already leaves through an exit
    code, so the affordance rides the contract instead of being remembered at each of them.

    Which is also what made it unable to tell the two apart. `lint` exiting 1 with
    `ref.unresolved 1` has already said everything — the finding names the file, the line and
    the rule, and the next move is `--fix` or an edit — so two further lines saying roadkeep
    itself may be wrong ride the tool's highest-traffic output, where the action and the
    pre-commit hook both live and where there is no session to capture before the end of.

    The split needs no new judgement, which is why it is this one and not a longer exemption
    list: a **verdict** is what a command returns when it read the files and they did not
    pass, and a fault is everything else. `pick --claim` refusing a held line is a write
    refusal and keeps the offer, and a `lint` that *crashed* keeps it too — `faulted` is how
    that 1 says it was not a verdict.

    Which of the two an exit is comes from **the declaration** and not from whether the
    command writes (RK1419). RK271 read `_only_reads`, and that is a different question:
    `lint --fix` is the same report by the same reader and takes the lock, so it closed the
    busiest correct answer this tool gives by suggesting the tool was wrong — and so did
    `repair`, which the report tells a reader to reach for. `_only_reads` stays beside it
    because it is true of every read that never declared one.

    `verdict` is written from **either end** (RK1420). A parser states what its exit usually
    means, and a run states what this one did: `repair` withdraws it for a step whose argv
    came back non-zero, and `install --check` asserts it, that verb returning `EXIT_GATE`
    from nowhere else — so a declaration standing over the whole of it would be a claim
    about a branch that does not exist. Which end says it is decided by where the fact is:
    on the verb where every exit means one thing, and on the run where a flag decides.

    A validation refusal keeps the offer either way: that is the case RK86 measured, and the
    one where the limit really might be wrong.
    """
    if args.command in ("report", "guard", "mcp"):
        # `report` offering to report itself is a regress; `guard` and `mcp` answer a
        # protocol, and a sentence on their stderr is read by no agent at all.
        return
    if not faulted and code == EXIT_GATE and (_only_reads(args) or _is_verdict(args)):
        return
    # The report this closes went to stdout and this goes to stderr: unflushed, the offer
    # lands above the findings it is about, and a line out of order is a line misread.
    sys.stdout.flush()
    print(offer(argv), file=sys.stderr)


if __name__ == "__main__":  # pragma: no cover - exercised via the console script
    raise SystemExit(main())
