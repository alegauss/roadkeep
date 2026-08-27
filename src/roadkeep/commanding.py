"""The command surface as data, so nothing outside a terminal declares it twice (RK1401).

`--help` is the only reader of the parser this package builds, and it is text: a usage line
wrapped to a console width, arguments grouped the way `argparse` groups them, sentences
folded at whatever column the terminal is. Anything that wants the *facts* — a reference
page, a completion list, a table in an area a browser serves — either scrapes that output or
types the verbs again, and both go stale in the commit after the one that wrote them.

The package already holds every fact such a reader wants. Each verb declares its help
sentence beside the argument, `reads_only` and `writes_when` say whether running it changes
a file (RK117, RK167), and :data:`~roadkeep.serving.TOOLS` says which of them an agent is
sent and which of their arguments it may set (RK1360). `cost --tools` proves that surface can
be walked as data, because pricing a served description is exactly that walk. What no read
did was **print** it.

**Nothing here is a second statement of the surface.** The verbs come off the subparser tree,
the sentence off the `help=` its author already wrote, the default off the action, and the
exposure off the tool table `tools/list` answers from. The one thing this module decides is
what a *reader outside the process* needs each fact called — which is :class:`Argument`'s
fields and nothing else.

This is :mod:`roadkeep.describing` for the other half of the contract. That module answers
what `roadkeep.toml` may declare; this one answers what may be typed. Both name the build
that gave the answer, for the same reason: what is published is what **this** copy accepts,
so a flag a reader's copy does not have is an upgrade rather than a mistake.

A read about the tool and never about a governed file, so it costs a session nothing until it
is called (L5) and it answers on a tree with no configuration at all — which is the caller who
most needs it, since deciding to adopt comes before there is anything to configure.
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from roadkeep.config import Config

__all__ = ["Argument", "Command", "Listing", "commands", "payload", "stated"]

#: The one action every parser declares and no reader asked about: `--help` is argparse's,
#: not this tool's, and a reference page listing it once per verb would spend a row on the
#: fact that this is a command-line program.
_UNASKED = frozenset({"help"})


def _rendered(value: object) -> str:
    """A default as a reader outside Python needs it spelled.

    :func:`roadkeep.describing._rendered`'s rule for the other half of the contract, and
    deliberately the same one: a project reading both should not have to learn that a boolean
    is `true` in a config listing and `True` in a command listing.
    """
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return f'"{value}"'
    if isinstance(value, tuple | list):
        return "[" + ", ".join(_rendered(one) for one in value) + "]"
    return str(value)


@dataclass(frozen=True, slots=True)
class Argument:
    """One thing a verb takes, as a reader outside the process needs it.

    Keyed by :attr:`dest` rather than by spelling, because that is what the rest of this
    package is keyed by: `writes_when` names a dest, a tool exposes a dest, and a flag
    carrying two spellings — `--status`/`--marker`, `--reason`/`--why` (RK399, RK1038) — is
    one argument under both, which a reader keyed on the first spelling would report as two.
    """

    #: Every spelling, in the order the parser declares them, so a caller can print the
    #: primary and still recognise the alias somebody else's skill was written against. A
    #: positional carries the one name `--help` calls it by.
    spelling: tuple[str, ...]
    dest: str
    #: Whether it is taken by position. The difference is not decoration: `show RK1` and
    #: `show --id RK1` is the mistake RK1254 was filed for, so which of the two a verb wants
    #: is the fact a reference page exists to state.
    positional: bool
    #: What its value is called — the metavar the parser declares, or `""` where the argument
    #: takes no value at all and is a switch.
    takes: str
    #: Whether it may be given more than once, however the parser says so — an append action
    #: or an `nargs` that consumes several.
    repeatable: bool
    required: bool
    #: What the verb uses when it is not given, rendered — or `None`, which says there is no
    #: default rather than that the default is empty.
    default: str | None
    #: The closed set of values, where the parser declares one; empty otherwise.
    choices: tuple[str, ...]
    #: The sentence the parser already carries. Harvested and never restated, which is the
    #: whole of why it is worth publishing: a second copy is the one that goes stale.
    help: str
    #: Whether an agent on **this** project may set it over the served surface (RK1360). Per
    #: project and not per build, because `[files]` and `[ids]` decide it (L6). Spelled the
    #: way :meth:`~roadkeep.serving.Tool.exposed` spells it, and deliberately not `served`:
    #: that word is taken across this package for the prefix a session's tools arrive under
    #: (RK1246), and one field answering for two facts is what `tests/carrying.py` exists to
    #: refuse.
    exposed: bool = False
    #: Whether the served surface passes it on every call without exposing it — which is how
    #: a flag becomes a tool (RK150), and a different fact from being withheld.
    always: bool = False

    @property
    def primary(self) -> str:
        """The spelling `--help` leads with, which is what a reference page prints."""
        return self.spelling[0] if self.spelling else self.dest


@dataclass(frozen=True, slots=True)
class Command:
    """One verb this build declares, and what running it costs.

    A **group** — `section`, `block`, `record` — is one of these too, carrying no arguments
    and reaching nothing. Published rather than filtered out, because `section --help` is a
    real door and a listing that skipped it would leave the nesting to be inferred from the
    spaces in its children's paths.
    """

    #: The subcommand path, space-separated where it is nested (`"section add"`). The argv is
    #: this split, which is the same thing :class:`~roadkeep.serving.Tool` means by it.
    path: str
    help: str
    description: str
    arguments: tuple[Argument, ...]
    #: Whether running it changes a governed file. The parser's own claim (RK117) and never a
    #: table beside it: `lint` is a read and `lint --fix` is not, which a boolean alone gets
    #: backwards and :attr:`turns_on` is the other half of.
    writes: bool
    #: The dests that turn a declared read into a write (RK167, RK307). Empty on a verb that
    #: writes either way, where the question does not arise.
    turns_on: tuple[str, ...] = ()
    #: Whether it reaches a handler at all. False for a group, whose whole content is the
    #: verbs under it.
    runs: bool = True
    #: The protocol names this command is served under, in :data:`~roadkeep.serving.TOOLS`
    #: order. Several where `always` has put two tools on one command (RK150) — `brief` and
    #: the `--claim` that writes — and empty where the CLI keeps a verb to itself.
    tools: tuple[str, ...] = ()
    #: Whether **this** project is sent it, which is a narrower question than having a tool at
    #: all: a verb whose vocabulary the project never declared is withheld (RK1360).
    published: bool = False
    #: The role a withheld tool needs, so the answer names the `declare` that opens it rather
    #: than leaving an absence for a reader to explain.
    needs: str = ""

    @property
    def depth(self) -> int:
        return self.path.count(" ")

    @property
    def leaf(self) -> str:
        """The last word of the path — what `--help` lists it under, one level up."""
        return self.path.rsplit(" ", 1)[-1]


@dataclass(frozen=True, slots=True)
class Listing:
    """Every verb, and the build that answered — which is half of what makes it usable."""

    commands: tuple[Command, ...]
    version: str
    #: The config this project's exposure was read against, or `None` where there is none —
    #: in which case :attr:`Command.published` is what a default project would be sent.
    source: str | None = None

    def under(self, path: str) -> tuple[Command, ...]:
        """One command's own children, for a listing that groups the way `--help` does."""
        return tuple(
            one
            for one in self.commands
            if one.path.startswith(f"{path} ") and one.depth == path.count(" ") + 1
        )

    def top(self) -> tuple[Command, ...]:
        return tuple(one for one in self.commands if one.depth == 0)


def _takes(action: argparse.Action) -> str:
    """What one argument's value is called, or `""` where it takes none.

    argparse's own two conventions, kept rather than unified: an optional's value is the
    metavar or the dest upper-cased, a positional's is the metavar or the dest as written.
    Printing a third spelling here would name an argument something `--help` never calls it.
    """
    if action.nargs == 0:
        return ""
    if action.metavar:
        return action.metavar if isinstance(action.metavar, str) else action.metavar[0]
    return action.dest if not action.option_strings else action.dest.upper()


def _repeatable(action: argparse.Action) -> bool:
    """Whether it may be given more than once, however the parser declares it."""
    if isinstance(action, argparse._AppendAction | argparse._AppendConstAction):  # noqa: SLF001
        return True
    return action.nargs in {"*", "+"} or isinstance(action.nargs, int) and action.nargs > 1


def _required(action: argparse.Action) -> bool:
    """Whether omitting it is refused — which argparse states one way for each kind."""
    if action.option_strings:
        return bool(action.required)
    return action.nargs not in {"?", "*"}


def _arguments(
    parser: argparse.ArgumentParser, exposed: Sequence[str], always: Sequence[str]
) -> tuple[Argument, ...]:
    """Every argument one verb declares, in its own declaration order.

    A subparser action is not one of these: it is how the next verb is reached, and naming it
    here would offer a command as a value — `_positionals`' rule in :mod:`roadkeep.cli`, for
    its reason.
    """
    out: list[Argument] = []
    for action in parser._actions:  # noqa: SLF001 - argparse exposes no public reader
        if action.dest in _UNASKED or isinstance(action, argparse._SubParsersAction):  # noqa: SLF001
            continue
        default = action.default
        out.append(
            Argument(
                spelling=tuple(action.option_strings) or (_takes(action),),
                dest=action.dest,
                positional=not action.option_strings,
                takes=_takes(action),
                repeatable=_repeatable(action),
                required=_required(action),
                # `SUPPRESS` is argparse saying the attribute is not set at all, which is a
                # different fact from a default of nothing and is published as the absence.
                default=(
                    None
                    if default is None or default is argparse.SUPPRESS
                    else _rendered(default)
                ),
                choices=tuple(str(one) for one in action.choices or ()),
                help=action.help or "",
                exposed=action.dest in exposed,
                always=action.dest in always,
            )
        )
    return tuple(out)


def _serving(config: Config) -> Mapping[str, tuple[list[str], list[str], list[str], bool, str]]:
    """The served surface indexed by command path: names, exposed dests, always, published.

    Read off :data:`~roadkeep.serving.TOOLS` and never listed again, which is the same trade
    :attr:`~roadkeep.serving.Tool.writes` makes: exposure is a decision that surface already
    states, and a second table here would answer about a surface that has moved.

    A path may carry several tools, so every field accumulates: `brief` is two of them over
    one command (RK150), and reporting the first would say the query is read-only while the
    argument that writes is exposed.
    """
    from roadkeep.serving import TOOLS  # noqa: PLC0415 - RK260

    out: dict[str, tuple[list[str], list[str], list[str], bool, str]] = {}
    for tool in TOOLS:
        names, exposed, always, published, needs = out.setdefault(
            tool.command, ([], [], [], False, tool.needs)
        )
        names.append(tool.name)
        exposed.extend(tool.exposed(config))
        always.extend(tool.always)
        # Published where **any** tool over this command is: the two halves of `brief` are one
        # verb, and a path a project is sent under either name is one it has.
        out[tool.command] = (
            names,
            exposed,
            always,
            published or tool.published(config),
            needs,
        )
    return out


def commands(config: Config, verb: str | None = None) -> Listing:
    """Every verb this build declares, with what this project is served (RK1401).

    ``verb`` narrows to one path, spelled as the answer spells it (`"section add"`). A name
    this build does not have is refused rather than answered empty, that answer being read as
    evidence that the verb was removed — which is the one conclusion a reader on an older copy
    must not draw.
    """
    from roadkeep import __version__  # noqa: PLC0415 - RK260
    from roadkeep.serving import _parsers  # noqa: PLC0415 - RK260
    from roadkeep.verbs.declaring import writes_when  # noqa: PLC0415 - RK1171

    parsers = _parsers()
    if verb is not None and verb not in parsers:
        known = ", ".join(repr(one) for one in sorted(parsers) if " " not in one)
        raise KeyError(
            f"no command {verb!r} in roadkeep {__version__}: this build declares {known} — "
            f"a nested one is spelled as its path, e.g. 'section add'"
        )
    served = _serving(config)
    out: list[Command] = []
    for path, parser in parsers.items():
        if verb is not None and path != verb:
            continue
        names, exposed, always, published, needs = served.get(path, ([], [], [], False, ""))
        # A group reaches no handler, so `reads_only` is absent on it — and absent is what
        # every writing verb also looks like. The two are told apart by the handler, which is
        # the only thing that makes a path runnable.
        runs = parser.get_default("handler") is not None
        out.append(
            Command(
                path=path,
                help=_help_of(parsers, path),
                description=parser.description or "",
                arguments=_arguments(parser, exposed, always),
                writes=runs and not parser.get_default("reads_only"),
                turns_on=writes_when(parser),
                runs=runs,
                tools=tuple(names),
                published=published,
                needs=needs,
            )
        )
    return Listing(
        commands=tuple(out),
        version=__version__,
        source=None if config.source is None else config.relative(config.source),
    )


def _help_of(parsers: Mapping[str, argparse.ArgumentParser], path: str) -> str:
    """The one-line sentence a verb is listed under, which its **parent** holds.

    argparse keeps `help=` on the subparsers action that created the child and never on the
    child itself, so a verb asked for its own help string answers with nothing. Read back off
    the parent's choices rather than restated here, for this module's whole rule: the sentence
    is the one its author wrote at the `add_parser` call.
    """
    from roadkeep.serving import _root  # noqa: PLC0415 - RK260

    parent, _, leaf = path.rpartition(" ")
    # The root is cached for the life of the process (RK202) and is the same object the index
    # was walked from, so reaching it here is a lookup and not a second build.
    holder = parsers.get(parent) if parent else _root()
    if holder is None:
        return ""
    for action in holder._actions:  # noqa: SLF001 - argparse exposes no public reader
        if isinstance(action, argparse._SubParsersAction):  # noqa: SLF001
            for choice in action._choices_actions:  # noqa: SLF001
                if choice.dest == leaf:
                    return choice.help or ""
    return ""


def stated(found: Listing) -> str:
    """The surface as a reader is told it: one block per verb, nested under its group."""
    rows = [
        f"{len(found.commands)} command(s) this build declares",
        f"  build    roadkeep {found.version} — what is listed is what *this* copy takes, "
        f"which is how a flag it predates is told from a typo",
    ]
    for one in found.commands:
        rows.extend(_block(one))
    return "\n".join(rows)


def _block(one: Command) -> list[str]:
    """One verb as a reader is told it, indented by how deep its path is."""
    pad = "  " * one.depth
    kind = "group" if not one.runs else ("writes" if one.writes else "reads")
    rows = [f"{pad}{one.path:<22} {kind:<7} {one.help}"]
    if one.turns_on:
        turns = ", ".join(f"--{dest.replace('_', '-')}" for dest in one.turns_on)
        rows.append(f"{pad}  writes when {turns} is given")
    if one.tools:
        # Named, and said as withheld where the project has not declared the role: an absence
        # a reader cannot explain is what sends them to the source (RK1360).
        where = "served" if one.published else f"withheld until `declare {one.needs}`"
        rows.append(f"{pad}  {where} as {', '.join(one.tools)}")
    for argument in one.arguments:
        rows.append(f"{pad}  {_argument_row(argument)}")
    return rows


def _argument_row(one: Argument) -> str:
    """One argument on one line — what it is spelled, what it takes, and what it costs."""
    spelled = ", ".join(one.spelling)
    value = f" {one.takes}" if one.takes and not one.positional else ""
    notes = []
    if one.required:
        notes.append("required")
    if one.repeatable:
        notes.append("repeatable")
    if one.default is not None and not one.required:
        notes.append(f"default {one.default}")
    if one.choices:
        notes.append("one of " + ", ".join(one.choices))
    if one.always:
        notes.append("always passed by the served tool")
    elif one.exposed:
        notes.append("exposed")
    marked = f"({'; '.join(notes)})" if notes else ""
    head = f"{spelled + value:<34}{marked}".rstrip()
    return f"{head}\n      {one.help}".rstrip() if one.help else head


def payload(found: Listing) -> dict[str, object]:
    """The same answer as data — what a reference page and a completion list read."""
    return {
        "version": found.version,
        "source": found.source,
        "commands": [
            {
                "command": one.path,
                "help": one.help,
                "description": one.description,
                "writes": one.writes,
                # The dests that make a read a write (RK167). `[]` and never omitted: a
                # consumer reading a missing key cannot tell "never" from "this build is
                # older than the answer".
                "writes_when": list(one.turns_on),
                "runs": one.runs,
                "tools": list(one.tools),
                "published": one.published,
                "needs": one.needs,
                "arguments": [
                    {
                        "dest": argument.dest,
                        "spelling": list(argument.spelling),
                        "primary": argument.primary,
                        "positional": argument.positional,
                        "takes": argument.takes,
                        "repeatable": argument.repeatable,
                        "required": argument.required,
                        "default": argument.default,
                        "choices": list(argument.choices),
                        "help": argument.help,
                        "exposed": argument.exposed,
                        "always": argument.always,
                    }
                    for argument in one.arguments
                ],
            }
            for one in found.commands
        ],
    }
