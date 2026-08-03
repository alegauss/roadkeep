"""The commands as MCP tools, so the field schema *is* the tool's input schema (RK24, RK59).

A CLI reached through `Bash` puts the field names in prose. `--symptom` is typed from memory,
`--dep` is guessed as `--deps`, and the answer is a usage string the caller pays for after the
sentence was already composed. Over MCP the same fields arrive as a JSON Schema the client
validates *before* the call, which is L1 moved one layer further out: not the write path
refusing bad prose, but the protocol refusing a wrong argument name.

What that costs, and how each cost is avoided here:

* **No second implementation.** A tool call is translated into the argv the CLI accepts and
  dispatched through :func:`~roadkeep.cli.build_parser`'s own handler, in-process. The exit
  code becomes `isError`, and the refusal an agent reads over MCP is byte-identical to the one
  it reads in a terminal. Two code paths that both "add a task" is the drift this repo exists
  to remove, so there is one.
* **No duplicated schema.** Every property is derived: its type and description come from the
  argparse action, its bounds from `roadkeep.toml` — `maxLength` is this project's `symptom`
  and `why` limits, `enum` is its declared markers, `pattern` is its id shape (L6). A tool
  description is the subcommand's own `description`, so a flag renamed in `cli.py` cannot
  leave the schema describing something that is gone.
* **stdio, and no listener.** "No server" is a non-goal about *the store*: this speaks
  JSON-RPC on stdin and stdout, holds no state between messages, binds no port and caches no
  file. The config is re-read per message, so a `roadkeep.toml` edited mid-session is the one
  the next `tools/list` describes — and because the *code* reading it is not, a refusal says so
  when this package's own modules moved after they were imported (RK155).
* **stdin is the transport, so a handler never gets it.** `call` dispatches in-process through
  the CLI's own parser, and three handlers read a paragraph from a pipe (RK9). Given the
  client's pipe, one of them waits for an EOF no live client sends and eats every message queued
  behind it — 18 minutes, holding the lock (RK170). :func:`_spent_stdin` substitutes a stream
  already at EOF, which turns the deadlock into the refusal the format already owns. *Which*
  three is :class:`Prose` on their own parsers rather than a comment in one handler (RK171), so
  the argv is refused before it gets there and a fourth is named by a test and not by a session.
* **A broken config still starts.** `mcp` tolerates a `ConfigError` for the reason `guard`
  does: the process is launched once for the whole session, and refusing to start would take
  the tools away exactly when a typo in the config most needs the gate. `tools/list` then
  describes the defaults, and the error is what the first `tools/call` returns.

The surface is what a task needs end to end, which RK24 got wrong by half. It exposed four
because one roadmap line named four, on the argument that the reads were "one `Bash` call
away" — and RK57 then made a plugin install with no console script at all, so on that machine
there is no shell command to fall back to. Starting a task needs `brief`, writing a rationale
needs `section add`, a line that leaves without shipping needs `retire`.

What stays out is what a tool cannot be: `init` and `adopt` run once, before the project is
governed, and `guard` and `mcp` are the harness's own entry points. `lint` exposes one argument
and deliberately not `--fix` — that one writes, and RK16 belongs where a human is standing (the
pre-commit hook), which is what keeps this tool honestly read-only.

A nested subcommand is one tool: `section add` is `section_add` to the protocol, which has no
space in a name, and two argv words here. One :class:`Tool` holds both spellings rather than a
table mapping between them.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import re
import sys
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, TextIO

from roadkeep import __version__
from roadkeep.config import Config, ConfigError, Scope
from roadkeep.locking import LockBusy
from roadkeep.provenance import engine

#: The protocol revision this server answers with when the client asks for one it does not
#: know. Negotiation is "echo what the client asked for if we understand it": a server that
#: always answers with its own newest version fails clients that pinned an older one.
PROTOCOL = "2025-06-18"
KNOWN_PROTOCOLS = (PROTOCOL, "2025-03-26", "2024-11-05")

#: JSON-RPC's own codes. Only these three are reachable: a tool that fails is *not* a
#: protocol error — it answers with `isError`, so the model reads the refusal and retries,
#: instead of the client reporting a transport failure it cannot act on.
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601


@dataclass(frozen=True, slots=True)
class Prose:
    """A command that takes a paragraph off a pipe, declared beside the argument (RK171).

    Three exposed tools reach `sys.stdin.read()` and neither `TOOLS` nor `cli.py` said which:
    `add` on a section named with no body, `section add` on a body omitted, `section amend` on
    the `-` its own help documents. `record add` cannot, exposing no body at all — and that
    asymmetry is the point, because it is a property of the two files together and a comment in
    one handler was the whole of it. So the parser declares it, the way :attr:`Tool.writes` made
    `reads_only`/`writes_when` the parser's claim rather than a table beside it (RK167).

    What it buys is not the deadlock — :func:`_spent_stdin` closed that whatever this says — but
    that every one of the three refuses by *naming the argument*, and that a fourth exposed
    tomorrow is named by a test rather than by the session that meets it.
    """

    #: The argument carrying the prose. Omitting it or setting it to :attr:`sentinel` is what
    #: sends the handler to the pipe.
    dest: str
    #: The spelling the CLI documents for "read it from stdin". One string, because a second
    #: sentinel would be a second thing a caller has to know.
    sentinel: str = "-"
    #: Whether *omitting* the argument reads the pipe too, or only the sentinel does. False for
    #: `section amend`, which refuses an amend with neither field rather than defaulting to it.
    omitted: bool = True
    #: The argument whose presence makes the read happen at all, where one does. `add` reads
    #: only when a section was named: an `add` with no rationale must never block on a pipe,
    #: which used to be a comment and is now the thing that says so.
    gated_by: str = ""

    def reached_by(self, arguments: Mapping[str, Any]) -> bool:
        """Whether this argv sends the handler to the pipe."""
        if self.gated_by and self.gated_by not in arguments:
            return False
        if self.dest not in arguments:
            return self.omitted
        return arguments[self.dest] == self.sentinel


@dataclass(frozen=True, slots=True)
class Tool:
    """One subcommand, and which of its arguments an agent is allowed to set.

    `exposes` is a whitelist and not a filter: `add --ref` exists for adoption (RK18) and
    would let a caller choose a pointer the tool derives, which is the one thing a schema
    cannot then check.

    :attr:`conditional` is the exception that proves the rule (RK111): where a project
    declares a shape the deriver cannot spell, withholding the field leaves that surface
    unable to write a legal id at all.
    """

    #: The subcommand path, space-separated where it is nested (`"section add"`). The argv
    #: is this split; the tool's name is the same with `_`, because a protocol name may not
    #: carry a space and a client shows what it is given.
    command: str
    exposes: tuple[str, ...] = ()
    #: Arguments this tool always passes, by dest — never exposed, so a caller cannot unset
    #: one. This is how a **flag becomes a tool** (RK150): `readOnlyHint` is one boolean per
    #: tool and `brief --claim` writes while `brief` does not, so the two are two tools over
    #: one command, and the query keeps the hint that makes it free to ask (L5). By dest and
    #: not as literal argv, so the flag is resolved through the same parser every exposed
    #: argument is and a rename cannot leave a tool passing something that is gone.
    always: tuple[str, ...] = ()
    #: The protocol name where it is not the command path. Needed only where :attr:`always`
    #: has put two tools on one command, and it names the **act** rather than the command,
    #: because two names for one path is what a client would otherwise have to tell apart.
    named: str = ""
    #: Arguments exposed only where this project's config makes them the **one** way to spell
    #: a legal value, by dest — the predicate is :data:`_CONDITIONAL` and the bound that then
    #: narrows them to exactly that value is :data:`_BOUNDS` (RK111). By dest and by config,
    #: never by hand: a field a caller may set on one project and not another is a difference
    #: `roadkeep.toml` states (L6), so the tool schema varying is the config being read rather
    #: than this surface holding a second opinion about it.
    conditional: tuple[str, ...] = ()

    def exposed(self, config: Config) -> tuple[str, ...]:
        """Every argument a caller may set on *this* project, in declaration order.

        The conditional ones come last, so the argv stays stable and diffable when a project
        turns one on — a field that reordered the others would make the same call render two
        command lines.
        """
        opened = tuple(dest for dest in self.conditional if _CONDITIONAL[dest](config))
        return (*self.exposes, *opened)

    @property
    def name(self) -> str:
        """The protocol name: the command path with `_` where its space is (RK59).

        A tool name may not carry a space, and a client shows the name it is given — so
        `section add` is `section_add` there and stays two argv words here. A hyphen goes the
        same way (RK70): `non-goal add` is one command spelled in two conventions, and the
        name a client renders should not be where that shows.
        """
        return self.named or self.command.replace(" ", "_").replace("-", "_")

    @property
    def argv_head(self) -> list[str]:
        return self.command.split()

    @property
    def writes(self) -> bool:
        """Whether a successful call changes a governed file — `readOnlyHint`, derived (RK168).

        Stated per tool until now, and the reason given was `lint`: it writes when `--fix` is
        passed and is read-only *here* only because that flag is not exposed. RK167 gave a
        parser the way to say which flag makes a read a write, and RK168 put it on `lint` — so
        the answer is derivable and stops being a boolean two places could disagree about.

        Two clauses and no table: a command whose parser does not call itself a read writes, and
        a read writes exactly when this tool passes the flag its parser names — exposed, so a
        caller may, or in :attr:`always`, so it always does.

        :attr:`conditional` counts as exposed without asking the config, which is the safe
        direction: a hint that flipped to read-only on some projects would be a client caching
        "free to ask" for a tool that writes, and `readOnlyHint` is a promise or it is noise.
        """
        return self.writes_of(_subparser(self.command))

    def writes_of(self, parser: argparse.ArgumentParser) -> bool:
        """:attr:`writes`, read off a parser the caller already resolved (RK174).

        The same two clauses, against a parser passed in rather than looked up: `descriptor`
        holds this tool's own parser by the time it needs the hint, and resolving it a second
        time was half of what `tools/list` spent.
        """
        if not parser.get_default("reads_only"):
            return True
        flag = parser.get_default("writes_when") or ""
        return bool(flag) and flag in (*self.exposes, *self.conditional, *self.always)


#: What a task needs end to end (RK24's four, extended by RK59). Order is the order
#: `tools/list` reports: the write path first, then the reads, because that is the order a
#: session uses them in and a client renders the list as given.
#:
#: `init` and `adopt` are deliberately absent — they run once, before the project is
#: governed — and so are `guard` and `mcp`, which are the harness's own entry points.
TOOLS: tuple[Tool, ...] = (
    # `section` and `section_body` are exposed for the reason `section add`'s body is: the
    # rationale is the second half of one write (RK93), and a client that cannot pass it
    # here is one whose every `add` leaves a pointer for the gate to refuse.
    # `task_id` is conditional and every other id on the write path is derived (RK111): a
    # project that declares `[ids] suffix` has a legal shape `spell_id` never produces, so the
    # split the skill prescribes was an invocation only the CLI could make. Opened only there,
    # and bounded to *require* the letter — so what the field buys is the id the counter cannot
    # reach, and never the number it would have handed out.
    Tool(
        "add",
        ("block", "symptom", "why", "deps", "status", "section", "section_body"),
        conditional=("task_id",),
    ),
    # The key to a deadlock the agent meets first (RK141): `ship` refuses an undeclared
    # block, the guard denies the edit that would declare it, and no other verb writes a
    # heading — so a correctly wired project could not open a block at all.
    # `after` rides with it (RK145): block order is what `list` reports and what a reader takes
    # for the shape of the plan, and without it a phase belonging between two existing ones was
    # appended after both — repaired only by reordering three files by hand.
    Tool("block add", ("label", "title", "after")),
    # And the key that could not close the door (RK144). Exposed for the same reason: the
    # caller that opened a label by mistake is the one the guard denies the hand-edit to, and
    # the removal is refused by name over anything filed under it.
    Tool("block drop", ("label",)),
    # The write a session makes first, and the one flag that became a tool (RK149, RK150): it
    # is `brief --claim`, so the answer is everything needed to start the task *and* the
    # marker that stops the next agent being handed it — while `brief` and `pick` below stay
    # honestly read-only, which is what keeps consulting the backlog free.
    Tool(
        "brief",
        ("id", "block", "designed"),
        always=("claim",),
        named="claim",
    ),
    Tool("status", ("id", "marker")),
    Tool("amend", ("id", "why", "deps", "ref")),
    # The field `amend` excludes, at its own door (RK178). Exposed beside it because the agent
    # that discovers a premise is false is the one executing the line, and the exit designed
    # for it — retire plus add — spends an id and deletes a section that was already right.
    Tool("restate", ("id", "symptom")),
    # The repair a merge needs, exposed for the reason it exists at all (RK97): the agent
    # that hits a doubled id is the one the hook denies a hand-edit to, so a door only a
    # human can reach is no door. `to` is offered because the derived answer is not always
    # the wanted one — it is refused against every source either way.
    Tool("renumber", ("id", "to")),
    # `part` is exposed because the agent shipping half of something is the one that needs
    # it (RK121): without it the only honest options are a ledger entry that overstates and
    # a hand-edited qualifier the grammar reads and no verb maintains.
    # `why` is required on the write path and not merely offered (RK142): the roadmap's
    # sentence is a problem statement, and the entry that inherited it read as a defect
    # report filed under a heading meaning "done".
    Tool("ship", ("id", "why", "part")),
    Tool("retire", ("id", "reason", "superseded_by")),
    Tool("defer", ("id", "reason")),
    Tool("resume", ("id", "marker")),
    Tool("record add", ("block", "symptom", "why")),
    # The ledger's update (RK124). `part` rides with it because a qualifier that stopped
    # being true is the commonest correction an entry needs, and the agent that wrote it is
    # the one the hook denies a hand-edit to.
    # `lines` rides with it for `record drop --line`'s reason (RK179): on a ledger whose
    # bullets wrap, the correction replaces text the parse never held, and the count is the
    # caller saying they read it — a door the agent this ships for has to be able to reach.
    Tool("record amend", ("id", "why", "part", "lines")),
    # The move `record amend` refuses to spell as a correction (RK143). Exposed beside it
    # because an entry filed under the wrong block is what `ship` writes from a line filed
    # under the wrong block — an agent's own slip, and the hand-edit that repaired it is the
    # one the guard denies that agent.
    Tool("record move", ("id", "to_block")),
    # `line` rides with both because the choice is the fix (RK127): two entries for one id
    # can be one slip or two deliveries, and the default picked the entry that earned the id.
    Tool("record drop", ("id", "line")),
    Tool("record renumber", ("id", "line", "to")),
    Tool("non-goal add", ("lead", "why")),
    Tool("non-goal drop", ("lead",)),
    Tool("section add", ("anchor", "title", "body", "role")),
    # The correction an open task's design needs (RK123). Exposed for the reason the whole
    # write path is: the agent that narrowed a hypothesis is the one the hook denies a hand
    # edit to, and until this verb existed the only way through was shipping the task.
    Tool("section amend", ("anchor", "title", "body", "role")),
    Tool("section drop", ("anchor", "role")),
    Tool("non-goal list"),
    Tool("weight", ("block",)),
    # The other pre-`add` read, and the one this transport needs most (RK190): `maxLength`
    # publishes the field's own ceiling and cannot publish the line's, so without this the
    # binding number reaches the author only as a refusal — a linter, one layer in.
    Tool("budget", ("id", "block", "deps", "status", "symptom")),
    # `designed` is exposed on both for the reason it exists (RK83): the caller that asks
    # to execute a block over MCP is the one that was handed a design session, and a flag
    # only the CLI can reach is a flag the agent this ships for cannot pass.
    Tool("brief", ("id", "block", "designed")),
    Tool("pick", ("block", "designed")),
    Tool("list", ("block", "role", "marker")),
    Tool("deps", ("id",)),
    # `baseline` and nothing else (RK84): it is the flag that makes the answer readable on a
    # project with standing debt — "did what I just wrote add anything" rather than a count
    # of 317 the caller cannot attribute — and it reads a revision without writing one.
    Tool("lint", ("baseline",)),
)

#: The subcommands above by their first word. Kept because a caller asking "is this command
#: served as a tool" asks about `section`, not `section add`; the refusal that names one
#: (RK58) resolves the full path itself.
TOOL_NAMES = frozenset(tool.argv_head[0] for tool in TOOLS)

#: What the config knows about a field that argparse does not: the limit, the marker set, the
#: id shape. This is the whole of RK24 — the bound that refuses the prose and the bound the
#: client validates against are read from the same `roadkeep.toml` (L6).
_BOUNDS = {
    "symptom": lambda config: {"maxLength": config.schema.symptom_max},
    # `maxLength` is the field's own ceiling and not the one that binds (RK183): the line
    # is, and how much of it this field has left depends on the symptom and the deps of the
    # call being composed, which no static number can state. So the ceiling is published as
    # what it is, and the joint rule is said in words beside it — a lower number here would
    # refuse on the client a line the server accepts, which is a bound on the client.
    "why": lambda config: {
        "maxLength": config.schema.why_max,
        "note": (
            f"The binding limit is the rendered line ({config.schema.line_max}), which "
            f"this sentence shares with the symptom and with the line's own structure, so "
            f"the usable maximum is lower than {config.schema.why_max} and lower again "
            f"where the line carries deps. `budget` answers it before a word is written "
            f"(RK190); the refusal names what was left."
        ),
    },
    "status": lambda config: {"enum": list(config.schema.markers)},
    "id": lambda config: {"pattern": config.schema.id_pattern().pattern},
    # Not `id_pattern` (RK111): this is the *chosen* id, and the shape that admits a bare
    # number would admit exactly the choice deriving already makes. The narrower pattern is
    # what keeps the field from being a way around the counter, so it is also checked here and
    # not only published — a bound a client may skip is a bound on the client.
    "task_id": lambda config: {"pattern": config.schema.split_id_pattern().pattern},
}

#: What opens a :attr:`Tool.conditional` argument: the declaration that makes the field the
#: only way to write something legal (RK111). One entry, and a table rather than a flag on the
#: dest, because the question is about the *project* and the answer has to be re-read per call
#: — a config edited mid-session is the one this server answers with (RK155's neighbour).
_CONDITIONAL: Mapping[str, Any] = {
    "task_id": lambda config: config.schema.id_suffix,
}

#: The non-goals are their own two limits (RK70), so the same `why` means a different number
#: here — a client validating a bullet against the *task* limit would refuse prose the tool
#: accepts, which is the one way this derivation can be wrong while looking right.
_SCOPE_BOUNDS = {
    "lead": lambda config: {"maxLength": (config.non_goals or Scope()).lead},
    "why": lambda config: {"maxLength": (config.non_goals or Scope()).why},
}


class ToolError(Exception):
    """An argument name or shape the schema already rules out — refused before dispatch."""


# -- describing the tools ----------------------------------------------------


def _action(parser: argparse.ArgumentParser, dest: str) -> argparse.Action:
    for candidate in parser._actions:  # noqa: SLF001 - argparse exposes no public reader
        if candidate.dest == dest:
            return candidate
    raise KeyError(f"{parser.prog} declares no {dest!r}")


def _parsers() -> Mapping[str, argparse.ArgumentParser]:
    """Every subcommand path in the CLI, indexed by it, off **one** `build_parser` (RK174).

    Reaching one subcommand means building the whole CLI, so a caller with more than one to
    resolve pays that per lookup — 58 builds and 195 ms for the `tools/list` a client sends
    first. The walk is the same descent :func:`_subparser` makes, done once and kept.

    Built per call and never memoised: `mcp` re-reads the config per message on purpose, and
    a parser held across messages is the one thing that would stop a mid-session edit from
    being described.
    """
    from roadkeep.cli import build_parser

    index: dict[str, argparse.ArgumentParser] = {}

    def walk(parser: argparse.ArgumentParser, path: str) -> None:
        for action in parser._actions:  # noqa: SLF001 - argparse exposes no public reader
            if not isinstance(action, argparse._SubParsersAction):  # noqa: SLF001
                continue
            for step, sub in action.choices.items():
                index[f"{path} {step}".strip()] = sub
                walk(sub, f"{path} {step}".strip())

    walk(build_parser(), "")
    return index


def _subparser(
    command: str, parsers: Mapping[str, argparse.ArgumentParser] | None = None
) -> argparse.ArgumentParser:
    """The parser for a subcommand path, descending where it is nested (`section add`).

    Takes an index where the caller has one, and builds itself one where it does not — so
    `descriptor(tool, config)` stays callable with a single tool, which is how the tests ask
    what one schema is.
    """
    return (_parsers() if parsers is None else parsers)[command]


def _property(
    action: argparse.Action, config: Config, bounds_for: Mapping[str, Any] = _BOUNDS
) -> dict[str, Any]:
    """One argparse argument, as the JSON Schema a client validates before calling."""
    bounds = dict(bounds_for.get(action.dest, lambda _: {})(config))
    # A bound the schema has no keyword for. `maxLength` says how long the field may be and
    # cannot say what else the length depends on, so the part that is a *joint* rule is
    # appended to the sentence the CLI already prints for the flag rather than dropped.
    note = bounds.pop("note", "")
    described = {
        "description": " ".join(part for part in ((action.help or "").strip(), note) if part)
    }
    if isinstance(action, argparse._StoreTrueAction):  # noqa: SLF001
        return {"type": "boolean", **described}
    if isinstance(action, argparse._AppendAction):  # noqa: SLF001
        return {"type": "array", "items": {"type": "string", **bounds}, **described}
    return {"type": "string", **bounds, **described}


def _required(action: argparse.Action) -> bool:
    # A positional is required by being one; `nargs="?"` is the exception, and `ship id` is
    # not one. Reading it off the action keeps the two lists from disagreeing.
    return bool(action.required) or (not action.option_strings and action.nargs != "?")


def _description(tool: Tool, parser: argparse.ArgumentParser) -> str:
    """The subcommand's own description, plus what an always-passed flag adds to it (RK150).

    Derived and never written here: the flag's help is the sentence the CLI prints for it, so
    two tools over one command cannot come to describe that difference in two ways — and a
    tool whose whole point is a flag it never mentioned would be a tool a client mistakes for
    the read it was split off from.
    """
    described = (parser.description or "").strip()
    for dest in tool.always:
        action = _action(parser, dest)
        flag, help_ = action.option_strings[0], (action.help or "").strip()
        described = f"{described} This tool always passes {flag}, which is to {help_}."
    return described


def descriptor(
    tool: Tool, config: Config, parsers: Mapping[str, argparse.ArgumentParser] | None = None
) -> dict[str, Any]:
    parser = _subparser(tool.command, parsers)
    # Which table holds this tool's numbers: the non-goals are governed by `[non_goals]` and
    # every other command by `[limits]`, and `why` is a field both of them name (RK70).
    bounds_for = _SCOPE_BOUNDS if tool.argv_head[0] == "non-goal" else _BOUNDS
    properties: dict[str, Any] = {}
    required: list[str] = []
    for dest in tool.exposed(config):
        action = _action(parser, dest)
        properties[dest] = _property(action, config, bounds_for)
        if _required(action):
            required.append(dest)
    payload: dict[str, Any] = {
        "name": tool.name,
        "description": _description(tool, parser),
        "inputSchema": {
            "type": "object",
            "properties": properties,
            # Closed on purpose: a misspelt argument is the failure RK24 names, and an open
            # object would forward it to a parser that answers with a usage string.
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": not tool.writes_of(parser)},
    }
    if required:
        payload["inputSchema"]["required"] = required
    return payload


def descriptors(config: Config) -> list[dict[str, Any]]:
    parsers = _parsers()
    return [descriptor(tool, config, parsers) for tool in TOOLS]


# -- calling one ------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Answer:
    """What one `tools/call` returns: the CLI's own output, and its exit code as a flag."""

    text: str
    is_error: bool

    def content(self) -> dict[str, Any]:
        return {"content": [{"type": "text", "text": self.text}], "isError": self.is_error}


def argv(tool: Tool, arguments: Mapping[str, Any], config: Config) -> list[str]:
    """The command line the CLI accepts, or `ToolError` naming what may be set instead.

    Takes the config because what may be set is a question about the project (RK111), and
    because a bound the descriptor published is a bound this has to hold: a client that
    validated is not the same as a call that was checked.
    """
    parser = _subparser(tool.command)
    exposed = tool.exposed(config)
    unknown = [name for name in arguments if name not in exposed]
    if unknown:
        raise ToolError(
            f"{tool.name}: no such argument {', '.join(sorted(unknown))} — "
            f"this tool takes {', '.join(exposed) or 'no arguments'}"
            + _withheld(tool, unknown)
        )
    _companioned(tool, arguments)
    positional: list[str] = []
    optional: list[str] = []
    for dest in exposed:  # declaration order, so the argv is stable and diffable
        if dest not in arguments:
            continue
        action = _action(parser, dest)
        fragment = _rendered(action, dest, arguments[dest])
        _bounded(dest, arguments[dest], config)
        (optional if action.option_strings else positional).extend(fragment)
    # What makes this tool the act it is named for (RK150), resolved through the parser like
    # every exposed argument: a client cannot pass these and cannot unset them.
    always = [_action(parser, dest).option_strings[0] for dest in tool.always]
    # `--json` is never exposed and always passed: the provenance is the difference between
    # an answer an agent can audit and one it re-reads the file to check (L5).
    return [*tool.argv_head, *positional, *optional, *always, "--json"]


def prose_of(command: str) -> Prose | None:
    """What this subcommand takes off a pipe, as its own parser declares it (RK171).

    The inventory neither `TOOLS` nor `cli.py` stated. Read from the parser rather than held
    here, so exposing a fourth command that reads a paragraph declares itself instead of being
    found by the session that hangs on it — and so `tests/test_serving.py` can ask the question
    over every tool at once, which is the instrument RK170 was fixed without.
    """
    return _subparser(command).get_default("reads_stdin")


def _companioned(tool: Tool, arguments: Mapping[str, Any]) -> None:
    """Refuse an argv that would have gone to the pipe, naming the argument (RK170, RK171).

    The deadlock is closed by :func:`_spent_stdin` whatever this says, so what is bought here is
    only *which* refusal the caller reads: without it, `add` with a section title and no body
    answers `body.empty` — true, and about the prose, when the fact is that the argument carrying
    it did not arrive. Derived from :func:`prose_of` and not a table beside it, so all three
    declared paths answer the same way and a fourth cannot be the one that was forgotten.
    """
    prose = prose_of(tool.command)
    if prose is None or prose.dest not in tool.exposes or not prose.reached_by(arguments):
        return
    raise ToolError(
        f"{tool.name}: {prose.dest} is the prose itself, and over this transport there is no "
        f"pipe to read it from — pass it as a string. Omitted, or {prose.sentinel!r}, it is an "
        f"empty body, and a section with no prose is a heading"
    )


def _withheld(tool: Tool, unknown: Sequence[str]) -> str:
    """The clause a refusal adds when the argument exists and this project closed it (RK111).

    Without it the message reads as a misspelling and the caller retries the same spelling:
    which arguments a tool takes is a fact about `roadkeep.toml` (L6), so the refusal says
    which declaration would have opened it rather than only that it is absent.
    """
    closed = sorted(set(unknown) & set(tool.conditional))
    if not closed:
        return ""
    return (
        f". {', '.join(closed)}: offered only where `roadkeep.toml` declares an id shape "
        f"the counter cannot spell (`[ids] suffix`), and this project declares none — so "
        f"every legal id here is the one `add` derives"
    )


def _bounded(dest: str, value: Any, config: Config) -> None:
    """Hold a conditional argument to the bound that opened it (RK111).

    Only the conditional ones, and only their `pattern`: every other bound in :data:`_BOUNDS`
    is the schema's, so the write path beneath refuses a violation whatever a client sent. A
    conditional field's is this surface's alone — `add --id T24` stays legal at a terminal,
    where `adopt` writes ids a corpus already spent — so unchecked here is unchecked.
    """
    if dest not in _CONDITIONAL:
        return
    pattern = _BOUNDS[dest](config).get("pattern")
    if pattern and not re.match(pattern, _one(dest, value)):
        raise ToolError(
            f"{dest} must match {pattern}, got {_one(dest, value)!r} — the id you may "
            f"choose is the split of one that already exists, and a number without the "
            f"letter is one the counter derives: leave the field out and it is derived"
        )


def _rendered(action: argparse.Action, dest: str, value: Any) -> list[str]:
    """One JSON value as the argv fragment its own argparse action reads."""
    if not action.option_strings:
        return [_one(dest, value)]
    flag = action.option_strings[0]
    if isinstance(action, argparse._StoreTrueAction):  # noqa: SLF001
        return [flag] if value else []
    if isinstance(action, argparse._AppendAction):  # noqa: SLF001
        return [part for item in _many(dest, value) for part in (flag, item)]
    return [flag, _one(dest, value)]


def _one(dest: str, value: Any) -> str:
    if isinstance(value, str):
        return value
    raise ToolError(f"{dest} must be a string, got {type(value).__name__}")


def _many(dest: str, value: Any) -> list[str]:
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise ToolError(f"{dest} must be an array of strings")
    return [_one(dest, item) for item in value]


def call(tool: Tool, arguments: Mapping[str, Any], directory: str = ".") -> Answer:
    """Dispatch through the real parser and handler, with stdout and stderr captured.

    In-process rather than a subprocess: the tool is already running in one, and a second
    interpreter per call would make an `add` cost more over MCP than over `Bash`.
    """
    from roadkeep.cli import build_parser, dispatch

    # Discovered before the argv is built, because which arguments this tool takes is read
    # from it (RK111) — and discovered once, so the call cannot be checked against one config
    # and dispatched against another.
    try:
        config = Config.discover(directory)
    except ConfigError as error:
        # The engine is named on this one refusal unconditionally (RK155): a key the file
        # declares and the code does not know is the shape stale code produces, and which
        # build read the config is the fact that turns the puzzle into an instruction.
        return _answered(f"roadkeep: {error} — read by {engine()}", is_error=True)
    try:
        line = argv(tool, arguments, config)
    except ToolError as error:
        return _answered(str(error), is_error=True)
    out, err = io.StringIO(), io.StringIO()
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err), _spent_stdin():
            args = build_parser().parse_args(["-C", directory, *line])
            # Through the CLI's own dispatch and not straight to the handler, so a write
            # over MCP takes the same lock a write over `Bash` does (RK117) — this is the
            # path an agent uses, so it is the path the duplicate id was minted on.
            code = dispatch(config, args)
    except SystemExit as exit_:  # argparse refused the argv: a missing required argument
        code = exit_.code if isinstance(exit_.code, int) else 2
    except LockBusy as busy:
        return _answered(f"roadkeep: {busy}", is_error=True)
    reported = "\n".join(part for part in (err.getvalue().strip(), out.getvalue().strip()) if part)
    return _answered(reported or f"{tool.name}: exit {code}", is_error=bool(code))


@contextlib.contextmanager
def _spent_stdin() -> Iterator[None]:
    """Hand the handler a stream already at EOF, for the length of one call (RK170).

    stdout and stderr are redirected because their output *is* the answer. stdin is redirected
    because it is the **transport**: `_add --section` with no `--section-body` reads
    `sys.stdin.read()`, and the only guard against that was a comment true of the `add` that
    names no section at all. Over `Bash` the read sees EOF and the call refuses. Over MCP it
    waits for an EOF no live client sends, and swallows every message queued behind it —
    measured in Shio at 18 minutes, 0% CPU, still holding the lock it claimed (RK117), with the
    `add` unanswered and a `status` sent after it unanswered too.

    Exhausted and not closed: `read()` on a closed stream raises `ValueError`, which
    :data:`~roadkeep.cli.REFUSALS` reports as bad input, and the honest answer is the refusal
    the format already owns for prose that is not there — `body.empty`, *a section with no prose
    is a heading*. So every handler that reads the pipe answers the same way instead of hanging,
    whether or not this surface knew it could.
    """
    saved = sys.stdin
    sys.stdin = io.StringIO("")
    try:
        yield
    finally:
        sys.stdin = saved


def _answered(text: str, *, is_error: bool) -> Answer:
    """One tool's answer, plus the note a **refusal** needs when the code answering moved.

    RK155, measured twice in one session: the config is re-read per message on purpose, so a
    `roadkeep.toml` edited mid-session is the one the next `tools/list` describes — but the code
    reading it was imported once at session start. `[claims] held` added to the file and to
    `config.py` in one commit made every MCP write refuse `unknown key 'claims'` while the CLI
    in a terminal accepted it, and the fallback was to stop using the write path this project
    ships. The refusal was correct about the code and wrong about the project.

    Only on a refusal, and only when something actually moved: a successful call has nothing to
    explain, and a note on every answer is a note that stops being read. Nothing reloads — see
    :attr:`~roadkeep.provenance.Engine.stale` for why that is the harness's job and not this
    server's.
    """
    if not is_error:
        return Answer(text, is_error=False)
    changed = engine().stale
    if not changed:
        return Answer(text, is_error=True)
    return Answer(
        f"{text}\n\n"
        f"This server imported roadkeep before {', '.join(changed)} changed on disk, so "
        f"the refusal above may be a build behind rather than a fact about this project — "
        f"the same command in a shell reads the current code. Every commit bumps the patch "
        f"version so the harness reloads the plugin (RK153); restart the session if it has "
        f"not.",
        is_error=True,
    )


def tool_named(name: str) -> Tool:
    for tool in TOOLS:
        if tool.name == name:
            return tool
    raise ToolError(
        f"no such tool {name!r} — this server offers "
        f"{', '.join(tool.name for tool in TOOLS)}"
    )


# -- the protocol -----------------------------------------------------------


def handle(message: Any, directory: str = ".") -> dict[str, Any] | None:
    """One JSON-RPC message in, one response out — or `None`, which is a notification.

    A notification answered is a protocol violation, and `notifications/initialized` is the
    first thing every client sends, so the `None` here is load-bearing rather than tidy.
    """
    if not isinstance(message, Mapping) or message.get("jsonrpc") != "2.0":
        return _error(None, INVALID_REQUEST, "expected a JSON-RPC 2.0 object")
    identifier = message.get("id")
    method = message.get("method")
    params = message.get("params") if isinstance(message.get("params"), Mapping) else {}
    if identifier is None:
        return None  # every notification, including the ones a later spec adds
    if method == "initialize":
        return _result(identifier, _handshake(params))
    if method == "ping":
        return _result(identifier, {})
    if method == "tools/list":
        return _result(identifier, {"tools": descriptors(_config(directory))})
    if method == "tools/call":
        return _result(identifier, _called(params, directory))
    return _error(identifier, METHOD_NOT_FOUND, f"unsupported method {method!r}")


def _handshake(params: Mapping[str, Any]) -> dict[str, Any]:
    asked = params.get("protocolVersion")
    return {
        "protocolVersion": asked if asked in KNOWN_PROTOCOLS else PROTOCOL,
        "capabilities": {"tools": {}},
        "serverInfo": {"name": "roadkeep", "version": __version__},
        # The startup line RK79 asks for. `serverInfo.version` stays the release number a
        # client may have pinned against, so which tree answered goes here — the one field
        # of the handshake that reaches a session, and the only moment this server has one.
        "instructions": str(engine()),
    }


def _called(params: Mapping[str, Any], directory: str) -> dict[str, Any]:
    arguments = params.get("arguments") if isinstance(params.get("arguments"), Mapping) else {}
    try:
        tool = tool_named(str(params.get("name")))
    except ToolError as error:
        # `isError` and not a JSON-RPC error, so the allowed set reaches the model that
        # guessed the name rather than the client that forwarded it.
        return Answer(str(error), is_error=True).content()
    return call(tool, arguments, directory).content()


def _config(directory: str) -> Config:
    try:
        return Config.discover(directory)
    except ConfigError:
        # The limits are then the defaults, which is a schema that is wrong about this
        # project rather than no schema at all — and `lint` is the tool that says why.
        return Config.default(directory)


def _result(identifier: Any, result: Mapping[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": identifier, "result": dict(result)}


def _error(identifier: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": identifier, "error": {"code": code, "message": message}}


def serve(reader: TextIO, writer: TextIO, directory: str = ".") -> int:
    """Read line-delimited JSON-RPC until the client closes stdin.

    The loop never raises: a malformed line is a parse error the client can read, and a
    server that dies on one takes every tool in the session with it.
    """
    for line in reader:
        if not line.strip():
            continue
        try:
            message = json.loads(line)
        except ValueError:
            response: dict[str, Any] | None = _error(None, PARSE_ERROR, "invalid JSON")
        else:
            response = handle(message, directory)
        if response is not None:
            writer.write(json.dumps(response) + "\n")
            writer.flush()
    return 0
