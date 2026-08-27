"""Every place this tool composes a command, and the one instrument that runs one (RK1209).

Four tasks found the same defect and no test found any of them. RK1149: the retry a refusal
offered had to be retyped. RK1198: the path into a fresh block was six calls discovered one at
a time. RK1205: the `section add` an `add` handed over was refused. RK1207: the refusal for
that family named no verb. Two more since: RK1203, whose `path.missing` door named a verb that
refuses every shipped id, and RK1206, whose pointer door named the task id where the missing
section was the anchor.

Each was covered. `test_the_command_offers_a_follow_up_that_runs` is the sharpest reading —
named for the claim, asserting the sentence was *printed*, never running it, green for as long
as the command it described refused. **Matching a composed command tests the composer against
itself**, which is the whole finding.

Two halves live here, and neither works alone.

:data:`SITES` is the census. `invocation()` is the one function every composed command goes
through, so the population is enumerable by an AST walk, and what this adds is a **reason per
site**: exercised, or unreached and why. The shape `test_surfaces` uses for a write that is
wired or exempted, for its reason — an exemption nobody can see reads exactly like a rule
being kept.

:func:`commands` and :func:`runs` are the instrument. The three tasks that fixed one defect
each wrote this by hand — RK1149 executes its retry, RK1198 walks its four steps, RK1207 runs
the chain it names — three copies of one shape, with the next composed command covered by
whichever session remembers to write a fourth.

**Commands are found by their backticks and never by a line prefix**, which is RK1220's
finding taken at the start rather than after: this tool spells its own errors `roadkeep:
refused, …`, so on a machine where the console script is on PATH a prefix scan reads the
preamble as a step and the suite is green or red by whether somebody ran `pip install`.

**The placeholders are filled and never stripped.** `…` and `<its title>` stand for prose only
the author writes (L4), so a harness that dropped them would run a different command from the
one printed; :data:`FILLS` supplies one value per flag, which is what makes the printed
sequence executable without changing it.
"""

from __future__ import annotations

import argparse
import ast
import re
import shlex
from dataclasses import dataclass
from pathlib import Path

from roadkeep.provenance import invocation
from surface import modules


@dataclass(frozen=True, slots=True)
class Site:
    """One function that composes a command, and how this suite accounts for it."""

    #: `module.py:Function.method`, as :func:`census` spells one.
    where: str
    #: `run` — a test in this suite executes what it composes. `exempt` — it does not, and
    #: :attr:`why` says what makes that honest.
    state: str
    why: str = ""


#: Reasons a site is not executed here. Shared where the cause genuinely is the same, and the
#: point of naming them at all is that a reader can see which: `unreached` is a work-list and
#: `deliberate` is a decision, and a table that spelled both as "no" would hide the difference.
NO_FIXTURE = (
    "unreached: the message needs a state no fixture in this suite builds yet, and the "
    "command it composes is runnable once one does"
)
NOT_A_STEP = (
    "deliberate: what it composes is the capture offer, which every refusal ends with and "
    "which is a defect report about the run being tested rather than a step of anything"
)
NOT_A_COMMAND = (
    "deliberate: what it composes is the **engine** and not a call — the notice names what "
    "else answers where a session's tools never arrive (RK1242), so running it as printed "
    "would be running the invocation with no verb"
)
FOREIGN = (
    "deliberate: the command it names is another tool's — git, or the harness — so running "
    "it here would be this suite asserting somebody else's contract"
)


#: Every function in the package that composes a command, and how this suite accounts for it
#: (RK1209). Held total against :func:`census`, so a site added tomorrow is a red here until
#: somebody says which of the three it is.
#:
#: The honest shape of it today: six are executed and the rest are a **work-list**, which is
#: what this task buys before it buys coverage. Four separate tasks each found one broken
#: composed command by meeting it; what was missing was not a test for any one of them but the
#: statement that thirty-six others have never been run.
SITES: tuple[Site, ...] = (
    Site("adopting.py:Created.stated", "unreached", NO_FIXTURE),
    # RK1264, and the row above it is the same shape one door over: what `declare` composes is
    # the verb the role it just wrote opens, with the id and the reason left as placeholders —
    # so `test_adopting` builds the state and asserts the line, and running it as printed is
    # what a filled argv would have to buy first.
    Site("adopting.py:Retrofitted.stated", "unreached", NO_FIXTURE),
    # RK1328, and the row above it one axis over: `declare` now opens an opt-in table too, and
    # what this composes is the verb that table gates — `criterion add` for one, `non-goal add`
    # for the other — with the lead and the reason left as placeholders, which is the same
    # reason the role's row is unreached.
    Site("adopting.py:Opened.stated", "unreached", NO_FIXTURE),
    # RK1223. Run by `test_blocking`, which executes the `--organise` call this refusal names
    # rather than matching it — the reading this whole file is about.
    Site("blocking.py:BlockExists.__init__", "run"),
    # The `add` that files a task prints the `section add` closing the pointer it just made.
    Site("authoring.py:Insertion.added", "run"),
    Site("capturing.py:Capture.filing", "unreached", NO_FIXTURE),
    Site("capturing.py:handoff", "unreached", NO_FIXTURE),
    Site("capturing.py:offer", "deliberate", NOT_A_STEP),
    # RK1394. The one door in this family that is takeable here: `--check` prints the delete it
    # would make, and `test_capturing` runs exactly that line — which is the whole reason the
    # offer is composed rather than described, the two runs being one table and one command.
    Site("capturing.py:Sweep.stated", "run"),
    # RK1395, and the one composer both readers that only *report* a stamp now call. Run where
    # the capture recorded where it went, which is when the argv is complete: `test_capturing`
    # types the printed line back and the state moves to the delivery it always was. Where the
    # capture recorded none the repository is a placeholder — the half no project can derive.
    Site("capturing.py:qualifying", "run"),
    # RK1235. Run by `test_installing`, which executes the read this refusal names — the
    # door that keeps a pinned project's guard from being a wall.
    Site("cli.py:_behind", "run"),
    # RK1236. Run by `test_budgeting`, which executes the ranking this refusal names when a
    # tool it does not serve is asked about.
    Site("verbs/querying.py:_tools_budget", "run"),
    # RK1286. Both name `cost --brief`, which `test_budgeting` executes — the gate's finding
    # composes the door with the id substituted and the read composes the sentence a backlog
    # with nothing open gets, and `remedying.Door` is what renders the first for a terminal.
    Site("linting.py:_reads", "run"),
    Site("verbs/querying.py:_brief_budget", "run"),
    # RK1238. Run by `test_installing`, which executes the read this note names — the command
    # that says which of three copies answered, on the report that qualifies.
    Site("linting.py:_judged", "run"),
    # RK1242. The one row whose composed text is the engine alone, and it says so.
    Site("guarding.py:Notice.__str__", "deliberate", NOT_A_COMMAND),
    Site("cli.py:_crossed", "unreached", NO_FIXTURE),
    Site("cli.py:_unrecognised", "unreached", NO_FIXTURE),
    Site("config.py:_skew", "unreached", NO_FIXTURE),
    Site("counting.py:Census.notes", "unreached", NO_FIXTURE),
    Site("deferring.py:NoPlacement.__init__", "unreached", NO_FIXTURE),
    Site("deferring.py:Resumption.requeue", "unreached", NO_FIXTURE),
    Site("history.py:Addresses.stated", "unreached", NO_FIXTURE),
    Site("history.py:opens", "unreached", NO_FIXTURE),
    # RK1230. Run by `test_installing`, which asserts the line it composes *is* the copy the
    # registry names — the one composed command here whose whole point is being pasted.
    Site("installing.py:Engines.invoke", "run"),
    Site("installing.py:Plan.verdict", "unreached", NO_FIXTURE),
    Site("installing.py:Removal.verdict", "unreached", NO_FIXTURE),
    Site("installing.py:_governed", "unreached", NO_FIXTURE),
    Site("installing.py:plan", "unreached", NO_FIXTURE),
    Site("linting.py:_projections", "unreached", NO_FIXTURE),
    # The gate's own report, which is where every door below is rendered for a terminal.
    Site("linting.py:_report_rows", "run"),
    Site("linting.py:_served", "unreached", NO_FIXTURE),
    Site("linting.py:_wired", "unreached", NO_FIXTURE),
    Site("markers.py:_naming_the_lines", "unreached", NO_FIXTURE),
    Site("merging.py:Wiring.repairs", "deliberate", FOREIGN),
    Site("merging.py:_spent", "deliberate", FOREIGN),
    # The two that render a remedy, and so every door the gate offers.
    Site("remedying.py:Door.command", "run"),
    Site("remedying.py:Door.quoted", "run"),
    # The other half of a decision, named by every `ship --decides` (RK1361).
    Site("rendering.py:_decided_body_rows", "run"),
    Site("rendering.py:_event_rows", "unreached", NO_FIXTURE),
    # The stairs RK1198, RK1205 and RK1207 each walked by hand.
    # The address a decision's body needs where the file numbers its own headings (RK1363).
    Site("shipping.py:DecidesUnaddressed.__init__", "run"),
    # RK1378: the read it names is the branch where `anchors` could not be read, and the one
    # `test_the_refusal_names_the_free_address_and_not_only_the_family` exercises is the other
    # — where the address is stated and no command is composed at all.
    Site("sections.py:NotASibling.__init__", "unreached", NO_FIXTURE),
    Site("sections.py:UnknownParent.__init__", "run"),
    Site("sections.py:_the_path_into", "run"),
    Site("sections.py:_where_a_top_level_is", "unreached", NO_FIXTURE),
    Site("sections.py:_where_the_anchor_is", "run"),
    Site("serving.py:_rerouted", "unreached", NO_FIXTURE),
    # RK1272. Both name a read rather than a repair — `config` lists the keys an address was
    # not among, and `init` is what a tree with no config needs — so what a fixture would have
    # to build first is a project that has neither, which is the state `init` is *for*.
    Site("governing.py:NoSuchKey.__init__", "unreached", NO_FIXTURE),
    Site("governing.py:govern", "unreached", NO_FIXTURE),
    Site("shipping.py:AlreadyRecorded.__init__", "unreached", NO_FIXTURE),
    Site("shipping.py:AlsoPaused.__init__", "unreached", NO_FIXTURE),
    Site("shipping.py:Delivered.__str__", "unreached", NO_FIXTURE),
    Site("shipping.py:Divergent.__init__", "unreached", NO_FIXTURE),
    # RK1281. The `govern` it names is the second of two doors and the one that is not a
    # complete argv: which number a wider limit should be is the reading that verb takes, so
    # the command as printed carries a placeholder and is filled the way every blank is.
    Site("shipping.py:InheritedClaim.__init__", "unreached", NO_FIXTURE),
    # RK1269. Run by `test_composing`, which executes the `declare decisions` this refusal
    # names and then makes the `ship --decides` land — the whole reading of this file, on the
    # one door where the remedy is a role a project has not opened yet.
    Site("shipping.py:NoDecisions.__init__", "run"),
    Site("shipping.py:_elsewhere", "run"),
    Site("shipping.py:PartRecorded.__init__", "unreached", NO_FIXTURE),
    Site("shipping.py:Partial.stated", "unreached", NO_FIXTURE),
    Site("shipping.py:SecondPartial.__init__", "unreached", NO_FIXTURE),
    Site("showing.py:_instead", "unreached", NO_FIXTURE),
    Site("showing.py:_paused", "run"),
    Site("showing.py:_where_it_went", "unreached", NO_FIXTURE),
    Site("verbs/querying.py:_anchors", "unreached", NO_FIXTURE),
)

#: The three states a site can be in. `run` is coverage; the other two are both "not run" and
#: are kept apart because only one of them is work somebody should do.
STATES = ("run", "unreached", "deliberate")


#: What stands in for prose in a composed command, by the flag it follows (RK1209). One value
#: per flag and not per verb: the same `--title` is filled the same way wherever it appears,
#: and a table keyed by verb would be a second place to remember a flag exists.
#:
#: Every value is deliberately *minimal and legal* — enough to pass the field's own validation
#: and nothing more — because what is being tested is whether the command lands, not whether
#: this file can write prose.
FILLS: dict[str, str] = {
    "--title": "A title",
    "--body": "Prose enough to matter, and a sentence that ends.",
    "--why": "Because of a reason.",
    "--symptom": "A symptom plainly long enough to read",
    "--reason": "Because of a reason.",
    "--lead": "No second backlog.",
    "--part": "the first half",
}

#: The tokens this tool prints where the author's own words go. Both spellings: `…` is what
#: `remedying.BLANK` renders and `<…>` is what a refusal's prose spells.
_BLANKS = re.compile(r"^(…|<[^>]*>|\"<[^>]*>\"|'<[^>]*>')$")

#: A backticked span, which is how every composed command in this tool is delimited.
_SPAN = re.compile(r"`([^`]+)`")


def census() -> tuple[str, ...]:
    """Every function in the package that calls `invocation()`, by address.

    Derived and never listed, for the reason `surface.py` exists: a second view of the
    population agrees with the first right up to the moment somebody adds a site, which is the
    single moment either of them matters.
    """
    found: list[str] = []
    for module in modules():
        tree = ast.parse(module.text)
        stack: list[str] = []

        class Walk(ast.NodeVisitor):
            def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
                stack.append(node.name)
                self.generic_visit(node)
                stack.pop()

            visit_AsyncFunctionDef = visit_FunctionDef  # type: ignore[assignment]

            def visit_ClassDef(self, node: ast.ClassDef) -> None:
                stack.append(node.name)
                self.generic_visit(node)
                stack.pop()

            def visit_Call(self, node: ast.Call) -> None:
                if isinstance(node.func, ast.Name) and node.func.id == "invocation":
                    where = f"{module.where}:{'.'.join(stack) or '<module>'}"
                    if where not in found:
                        found.append(where)
                self.generic_visit(node)

        Walk().visit(tree)
    return tuple(sorted(found))


def commands(said: str) -> tuple[list[str], ...]:
    """Every command a message composes, as argv, with this engine's own prefix removed.

    Backticks and not line prefixes (see the module docstring): `roadkeep: refused, nothing
    written:` begins with the invocation wherever the console script is installed, and a scan
    that took it for a step failed on a machine whose only difference was a `pip install`.

    A span that is not a command — a flag being named, a file being quoted — is skipped rather
    than refused: a message is prose and backticks are how it emphasises anything.
    """
    prefix = invocation()
    out: list[list[str]] = []
    for span in _SPAN.findall(" ".join(said.split())):
        if not span.startswith(prefix):
            continue
        rest = span[len(prefix):].strip()
        if not rest:
            continue
        try:
            argv = shlex.split(rest)
        except ValueError:
            # An unbalanced quote is prose, not a command this could have run.
            continue
        if argv:
            out.append(argv)
    return tuple(out)


def filled(argv: list[str], *, continuation: bool = False) -> list[str]:
    """The same command with the author's placeholders replaced by legal values (RK1209).

    Filled and never stripped: `add --why …` with the flag removed is a *different* command,
    and one that would be refused for a reason this sweep is not about.

    A dangling flag — the trailing `…` in `add --block Z --ref XXI.1 …`, which stands for the
    rest of a call rather than for one field — is dropped, because there is no flag in front
    of it to fill from.
    """
    out: list[str] = []
    for index, token in enumerate(argv):
        if not _BLANKS.match(token):
            out.append(token)
            continue
        before = argv[index - 1] if index else ""
        if before in FILLS:
            out.append(FILLS[before])
        elif before.startswith("--"):
            # A flag this table does not know: better to fail loudly in the sweep than to
            # quietly drop the argument and run something else.
            out.append(f"<unfilled {before}>")
        elif not continuation:
            # A blank in a *positional*, which the loud branch above never saw (RK1339). The
            # drop below is right only where the ellipsis stands for the rest of the caller's
            # own call, and that is a property of where the command was read: `runs` takes
            # them out of refusal prose and asks `abridged` which kind it has, while a remedy
            # door has no such ellipsis and no such question. Dropping one there turns
            # `block add … --title …` into `block add --title A title` — a different command,
            # which is exactly what the branch above refuses to let happen to a flag.
            out.append("<unfilled positional>")
        # else: a bare ellipsis standing for "and the rest", which has nothing to fill.
    return out


def abridged(argv: list[str]) -> bool:
    """Whether this printed command ends in a bare `…` meaning *and the rest of your call*.

    The one place a composed command is deliberately **incomplete**, and telling it apart is
    what keeps this sweep honest. A stair's retry reads `add --block Z --ref XXI.1 …`: the
    ellipsis stands for the caller's own `--symptom` and `--why`, which they already typed and
    the refusal is not going to repeat. Filling those in is right there and is *hiding a
    defect* anywhere else — a composed command that simply forgot a required flag is precisely
    what this file exists to catch, so the two cases may not share a rule.
    """
    return bool(argv) and bool(_BLANKS.match(argv[-1])) and not argv[-2:-1][0].startswith("--")


def supplied(argv: list[str], *, template: bool = False) -> list[str]:
    """The same command with a body added where omitting one sends it to the pipe (RK1209).

    Read off the parser's own :class:`~roadkeep.serving.Prose` declaration and never from a
    list here (RK171): which verbs take a paragraph off stdin is a claim the subparser makes,
    and a second copy of it would drift the moment a fourth one did.

    Not a change to the composed command, which is the distinction that matters. A refusal
    printing `section add I.1 --title "<its title>"` is *correct*: the body arrives on stdin,
    and a human running it types one. What this suite has is no stdin — under pytest the
    stream is the runner's and cannot be made strict UTF-8 (RK455) — so the harness supplies
    what a person would, rather than the sweep reporting a refusal about its own environment.
    """
    from roadkeep.cli import build_parser  # noqa: PLC0415 - the suite's own edge

    verbs = next(
        one for one in build_parser()._actions  # noqa: SLF001 - argparse exposes no reader
        if getattr(one, "choices", None) and one.dest == "command"
    ).choices
    parser = verbs.get(argv[0]) if argv else None
    for token in argv[1:]:
        # Subparsers and never *any* action carrying `choices`: an option declaring a value
        # set — `--role`, `--marker` — carries a list, and `.get` on it raises. Found by the
        # first composed command whose verb has one (RK1236), which is the same descent
        # `serving._parsers` makes and the reason it names the type.
        nested = next(
            (
                one.choices.get(token)
                for one in getattr(parser, "_actions", ())  # noqa: SLF001
                if isinstance(one, argparse._SubParsersAction)  # noqa: SLF001
            ),
            None,
        )
        if nested is None:
            break
        parser = nested
    declared = getattr(parser, "get_default", lambda _: None)("reads_stdin") or ()
    for prose in declared:
        flag = f"--{prose.dest.replace('_', '-')}"
        if not prose.omitted or flag in argv or f"{flag}-file" in argv:
            continue
        gate = getattr(prose, "gated_by", "")
        if gate and f"--{gate.replace('_', '-')}" not in argv:
            # `add` reads only where a section was named: an `add` with no rationale must
            # never block on a pipe, so there is nothing to supply.
            continue
        argv = [*argv, flag, FILLS.get(flag, "Prose enough to matter, and it ends.")]
    if not template:
        return argv
    # The caller's own fields, which a template stands in for and never states. Read off the
    # parser's `required`, so what is supplied is exactly what the printed line assumed the
    # caller still had — and never more, a flag this table cannot fill being a red rather than
    # a silent omission.
    for action in getattr(parser, "_actions", ()):  # noqa: SLF001 - argparse exposes no reader
        flags = getattr(action, "option_strings", ())
        if not action.required or not flags or any(one in argv for one in flags):
            continue
        argv = [*argv, flags[0], FILLS.get(flags[0], f"<unfilled {flags[0]}>")]
    return argv


def runs(root: Path, said: str, *, expect: int = 0) -> tuple[list[str], ...]:
    """Execute every command a message composed, in order, against ``root``.

    In the order printed, which is half the claim: RK1198's finding was a *path*, and a
    sequence whose second step refuses is a sequence, not a set.

    Returns what it ran, so a caller can assert the shape as well as the outcome.
    """
    from roadkeep.cli import main  # noqa: PLC0415 - the suite's own edge

    ran: list[list[str]] = []
    for printed in commands(said):
        # The one caller whose trailing ellipsis may be a continuation, so the one that says
        # so: `abridged` answers it for this text, and `filled` no longer assumes it (RK1339).
        continuation = abridged(printed)
        argv = supplied(filled(printed, continuation=continuation), template=continuation)
        if argv[:1] == ["report"]:
            # The capture offer, which every refusal ends with and which is not a step of
            # anything: running it would file a defect report about the run being tested.
            continue
        code = main(["-C", str(root), *argv])
        assert code == expect, (argv, code)
        ran.append(argv)
    return tuple(ran)
