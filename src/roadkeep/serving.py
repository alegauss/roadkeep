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
  the next `tools/list` describes.
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
governed, and `guard` and `mcp` are the harness's own entry points. `lint` deliberately exposes
**no** arguments — `--fix` writes, and RK16 belongs where a human is standing (the pre-commit
hook), which keeps that one honestly read-only.

A nested subcommand is one tool: `section add` is `section_add` to the protocol, which has no
space in a name, and two argv words here. One :class:`Tool` holds both spellings rather than a
table mapping between them.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, TextIO

from roadkeep import __version__
from roadkeep.config import Config, ConfigError, Scope
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
class Tool:
    """One subcommand, and which of its arguments an agent is allowed to set.

    `exposes` is a whitelist and not a filter: `add --id` and `add --ref` exist for adoption
    (RK18) and would let a caller choose an id the tool derives, which is the one thing a
    schema cannot then check.
    """

    #: The subcommand path, space-separated where it is nested (`"section add"`). The argv
    #: is this split; the tool's name is the same with `_`, because a protocol name may not
    #: carry a space and a client shows what it is given.
    command: str
    exposes: tuple[str, ...] = ()
    #: Whether a successful call changes a governed file — `readOnlyHint`, which a client
    #: uses to decide whether to ask. Stated per tool because it is not derivable: `lint`
    #: writes when `--fix` is passed, and is only read-only here because that flag is not
    #: exposed above.
    writes: bool = False

    @property
    def name(self) -> str:
        """The protocol name: the command path with `_` where its space is (RK59).

        A tool name may not carry a space, and a client shows the name it is given — so
        `section add` is `section_add` there and stays two argv words here. A hyphen goes the
        same way (RK70): `non-goal add` is one command spelled in two conventions, and the
        name a client renders should not be where that shows.
        """
        return self.command.replace(" ", "_").replace("-", "_")

    @property
    def argv_head(self) -> list[str]:
        return self.command.split()


#: What a task needs end to end (RK24's four, extended by RK59). Order is the order
#: `tools/list` reports: the write path first, then the reads, because that is the order a
#: session uses them in and a client renders the list as given.
#:
#: `init` and `adopt` are deliberately absent — they run once, before the project is
#: governed — and so are `guard` and `mcp`, which are the harness's own entry points.
TOOLS: tuple[Tool, ...] = (
    Tool("add", ("block", "symptom", "why", "deps", "status"), writes=True),
    Tool("status", ("id", "marker"), writes=True),
    Tool("amend", ("id", "why", "deps", "ref"), writes=True),
    Tool("ship", ("id", "why"), writes=True),
    Tool("retire", ("id", "reason", "superseded_by"), writes=True),
    Tool("defer", ("id", "reason"), writes=True),
    Tool("resume", ("id", "marker"), writes=True),
    Tool("record add", ("block", "symptom", "why"), writes=True),
    Tool("record drop", ("id",), writes=True),
    Tool("non-goal add", ("lead", "why"), writes=True),
    Tool("non-goal drop", ("lead",), writes=True),
    Tool("section add", ("anchor", "title", "body", "role"), writes=True),
    Tool("section drop", ("anchor", "role"), writes=True),
    Tool("non-goal list"),
    Tool("weight", ("block",)),
    Tool("brief", ("id", "block")),
    Tool("pick", ("block",)),
    Tool("list", ("block", "role", "marker")),
    Tool("deps", ("id",)),
    Tool("lint"),
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
    "why": lambda config: {"maxLength": config.schema.why_max},
    "status": lambda config: {"enum": list(config.schema.markers)},
    "id": lambda config: {"pattern": config.schema.id_pattern().pattern},
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


def _subparser(command: str) -> argparse.ArgumentParser:
    """The parser for a subcommand path, descending where it is nested (`section add`)."""
    from roadkeep.cli import build_parser

    parser = build_parser()
    for step in command.split():
        parser = _choices(parser)[step]
    return parser


def _choices(parser: argparse.ArgumentParser) -> Mapping[str, argparse.ArgumentParser]:
    for action in parser._actions:  # noqa: SLF001
        if isinstance(action, argparse._SubParsersAction):  # noqa: SLF001
            return action.choices
    raise KeyError(parser.prog)  # pragma: no cover - every path here has subcommands


def _property(
    action: argparse.Action, config: Config, bounds_for: Mapping[str, Any] = _BOUNDS
) -> dict[str, Any]:
    """One argparse argument, as the JSON Schema a client validates before calling."""
    bounds = bounds_for.get(action.dest, lambda _: {})(config)
    described = {"description": (action.help or "").strip()}
    if isinstance(action, argparse._StoreTrueAction):  # noqa: SLF001
        return {"type": "boolean", **described}
    if isinstance(action, argparse._AppendAction):  # noqa: SLF001
        return {"type": "array", "items": {"type": "string", **bounds}, **described}
    return {"type": "string", **bounds, **described}


def _required(action: argparse.Action) -> bool:
    # A positional is required by being one; `nargs="?"` is the exception, and `ship id` is
    # not one. Reading it off the action keeps the two lists from disagreeing.
    return bool(action.required) or (not action.option_strings and action.nargs != "?")


def descriptor(tool: Tool, config: Config) -> dict[str, Any]:
    parser = _subparser(tool.command)
    # Which table holds this tool's numbers: the non-goals are governed by `[non_goals]` and
    # every other command by `[limits]`, and `why` is a field both of them name (RK70).
    bounds_for = _SCOPE_BOUNDS if tool.argv_head[0] == "non-goal" else _BOUNDS
    properties: dict[str, Any] = {}
    required: list[str] = []
    for dest in tool.exposes:
        action = _action(parser, dest)
        properties[dest] = _property(action, config, bounds_for)
        if _required(action):
            required.append(dest)
    payload: dict[str, Any] = {
        "name": tool.name,
        "description": (parser.description or "").strip(),
        "inputSchema": {
            "type": "object",
            "properties": properties,
            # Closed on purpose: a misspelt argument is the failure RK24 names, and an open
            # object would forward it to a parser that answers with a usage string.
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": not tool.writes},
    }
    if required:
        payload["inputSchema"]["required"] = required
    return payload


def descriptors(config: Config) -> list[dict[str, Any]]:
    return [descriptor(tool, config) for tool in TOOLS]


# -- calling one ------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Answer:
    """What one `tools/call` returns: the CLI's own output, and its exit code as a flag."""

    text: str
    is_error: bool

    def content(self) -> dict[str, Any]:
        return {"content": [{"type": "text", "text": self.text}], "isError": self.is_error}


def argv(tool: Tool, arguments: Mapping[str, Any]) -> list[str]:
    """The command line the CLI accepts, or `ToolError` naming what may be set instead."""
    parser = _subparser(tool.command)
    unknown = [name for name in arguments if name not in tool.exposes]
    if unknown:
        raise ToolError(
            f"{tool.name}: no such argument {', '.join(sorted(unknown))} — "
            f"this tool takes {', '.join(tool.exposes) or 'no arguments'}"
        )
    positional: list[str] = []
    optional: list[str] = []
    for dest in tool.exposes:  # declaration order, so the argv is stable and diffable
        if dest not in arguments:
            continue
        action = _action(parser, dest)
        fragment = _rendered(action, dest, arguments[dest])
        (optional if action.option_strings else positional).extend(fragment)
    # `--json` is never exposed and always passed: the provenance is the difference between
    # an answer an agent can audit and one it re-reads the file to check (L5).
    return [*tool.argv_head, *positional, *optional, "--json"]


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
    from roadkeep.cli import build_parser

    try:
        line = argv(tool, arguments)
    except ToolError as error:
        return Answer(str(error), is_error=True)
    out, err = io.StringIO(), io.StringIO()
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            args = build_parser().parse_args(["-C", directory, *line])
            code = args.handler(Config.discover(directory), args)
    except SystemExit as exit_:  # argparse refused the argv: a missing required argument
        code = exit_.code if isinstance(exit_.code, int) else 2
    except ConfigError as error:
        return Answer(f"roadkeep: {error}", is_error=True)
    reported = "\n".join(part for part in (err.getvalue().strip(), out.getvalue().strip()) if part)
    return Answer(reported or f"{tool.name}: exit {code}", is_error=bool(code))


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
