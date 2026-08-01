"""The four commands over MCP, where the schema replaces the flag names (RK24).

A tool call is not a new way to write a task line — it is the *same* write path reached
without typing a flag from memory. So almost nothing here tests behaviour that
`tests/test_authoring.py` already owns; what is worth asserting is the three claims RK24
actually makes, each of which is a claim about **derivation**:

* **The input schema is the format's schema.** `maxLength` is this project's `symptom` and
  `why` limits, `enum` is its declared markers, `pattern` is its id shape — so a project that
  configures 60 characters gets 60 in the tool, and a project with prefix `SH` gets `^SH…`.
  A number written into this server would be the second declaration of a limit, which is the
  failure the tool exists to prevent, one layer out.
* **The description is the CLI's own.** Both come from the argparse `description`, so a
  subcommand reworded in `cli.py` cannot leave the tool describing something else.
* **A wrong name is answered with the allowed set.** That is the whole symptom: `--deps` for
  `--dep` earns a usage string. Over MCP it earns the list of arguments that exist — and as
  `isError` content, not a JSON-RPC error, because the model that guessed is the reader who
  can retry, and a transport error never reaches it.

The protocol half is asserted at the seams that break sessions rather than exhaustively: a
notification must not be answered, a malformed line must not kill the loop, and a broken
`roadkeep.toml` must not stop the server from starting — the same argument `guard` makes,
since both are processes a session starts once.
"""

from __future__ import annotations

import io
import json
from pathlib import Path

import pytest

from roadkeep.cli import build_parser
from roadkeep.config import Config
from roadkeep.serving import (
    KNOWN_PROTOCOLS,
    METHOD_NOT_FOUND,
    PARSE_ERROR,
    PROTOCOL,
    TOOLS,
    Tool,
    ToolError,
    _subparser,
    argv,
    descriptor,
    handle,
    serve,
    tool_named,
)

ROADMAP = "docs/ROADMAP.md"
CHANGELOG = "docs/CHANGELOG.md"

CLEAN = """# Roadmap

## Block A — The model

- 📋 **RK1** (deps: —) **A first symptom** — Because of a reason. → §RK1
"""

LEDGER = """# Shipped

## Block A — The model
"""

CONFIG = f'prefix = "RK"\n[files]\nroadmap = "{ROADMAP}"\nchangelog = "{CHANGELOG}"\n'


def project(tmp_path: Path, *, roadmap: str = CLEAN, config: str = CONFIG) -> Path:
    (tmp_path / "roadkeep.toml").write_text(config, encoding="utf-8")
    for name, body in {ROADMAP: roadmap, CHANGELOG: LEDGER}.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            handle.write(body)
    return tmp_path


def listed(tmp_path: Path) -> dict[str, dict]:
    response = handle(
        {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, str(tmp_path)
    )
    return {tool["name"]: tool for tool in response["result"]["tools"]}


def called(tmp_path: Path, name: str, **arguments) -> dict:
    response = handle(
        {
            "jsonrpc": "2.0",
            "id": 7,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        },
        str(tmp_path),
    )
    return response["result"]


def text_of(result: dict) -> str:
    return result["content"][0]["text"]


# -- the schema is the format's schema ---------------------------------------


def test_the_tools_are_what_a_task_needs_end_to_end():
    # RK24 exposed four because the roadmap line named four; RK59 added the rest a session
    # calls, because since RK57 a plugin installs with no shell command to fall back to.
    assert [tool.name for tool in TOOLS] == [
        "add",
        "status",
        "amend",
        "ship",
        "retire",
        # The third and fourth doors a line leaves and returns by (RK91) — beside the two
        # terminal ones, because a session that has to choose between them is at that spot.
        "defer",
        "resume",
        "record_add",
        "record_drop",
        "non_goal_add",
        "non_goal_drop",
        "section_add",
        "section_drop",
        # The two reads a session that is *proposing* makes, so they head the reads: what
        # may not be proposed at all (RK69), and what a comparable one cost (RK71).
        "non_goal_list",
        "weight",
        "brief",
        "pick",
        "list",
        "deps",
        "lint",
    ]


def test_what_stays_out_stays_out():
    """`init` and `adopt` run once, before the project is governed; `guard` and `mcp` are
    the harness's own entry points, and a tool that started a second server inside the
    first is not a capability."""
    named = {tool.argv_head[0] for tool in TOOLS}
    assert named.isdisjoint({"init", "adopt", "guard", "mcp"})


def test_a_nested_command_is_one_tool_name_and_two_argv_words():
    # A protocol name may not carry a space, and the CLI path is two words: one Tool holds
    # both spellings rather than a table mapping between them.
    tool = tool_named("section_add")
    assert tool.argv_head == ["section", "add"]
    assert argv(tool, {"anchor": "RK1", "title": "A design"})[:2] == ["section", "add"]


def test_every_tool_is_a_subcommand_the_cli_accepts():
    # The same argument the Action and the pre-commit hook get: a surface that drifts from
    # `cli.py` fails a test instead of failing a call.
    for tool in TOOLS:
        parsed = build_parser().parse_args(argv(tool, _minimal(tool)))
        assert parsed.command == tool.argv_head[0]
        assert parsed.json is True  # never exposed, always passed


def _minimal(tool: Tool) -> dict[str, str]:
    """The required arguments, filled with anything: this is about the argv, not the values."""
    required = descriptor(tool, Config.default())["inputSchema"].get("required", [])
    return {name: "RK1" if name == "id" else "x" for name in required}


def test_the_limits_in_the_schema_are_the_projects_own(tmp_path):
    project(
        tmp_path,
        config=CONFIG + "[limits]\nsymptom = 60\nwhy = 90\n",
    )
    add = listed(tmp_path)["add"]["inputSchema"]["properties"]
    assert add["symptom"]["maxLength"] == 60
    assert add["why"]["maxLength"] == 90


def test_the_marker_enum_is_the_projects_declared_open_set(tmp_path):
    project(tmp_path, config=CONFIG + '[markers]\nopen = ["📋", "🛠"]\n')
    assert listed(tmp_path)["add"]["inputSchema"]["properties"]["status"]["enum"] == [
        "📋",
        "🛠",
    ]


def test_the_id_pattern_is_the_projects_prefix(tmp_path):
    project(tmp_path, config='prefix = "SH"\n' + CONFIG.split("\n", 1)[1])
    pattern = listed(tmp_path)["ship"]["inputSchema"]["properties"]["id"]["pattern"]
    assert pattern == Config.discover(tmp_path).schema.id_pattern().pattern
    assert pattern.startswith("^SH")


def test_a_description_is_the_subcommands_own():
    """Not a copy maintained here: the string a client shows is the subparser's own
    `description`, so rewording the help rewords the tool and cannot desynchronise it."""
    for tool in TOOLS:
        described = _subparser(tool.command).description
        assert described
        assert descriptor(tool, Config.default())["description"] == described.strip()


def test_a_write_that_needs_prose_takes_it_as_a_bounded_string(tmp_path):
    # `section add` reads stdin in a shell; over MCP the body is an argument, and the word
    # budget refuses it exactly the same way.
    properties = listed(project(tmp_path))["section_add"]["inputSchema"]["properties"]
    assert set(properties) == {"anchor", "title", "body", "role"}
    assert properties["body"]["type"] == "string"


def test_the_derived_fields_are_not_offered(tmp_path):
    """`add --id` and `add --ref` exist for adoption; offering them lets a caller choose
    what the tool derives, and a hand-set id is the one thing the schema cannot check."""
    properties = listed(project(tmp_path))["add"]["inputSchema"]["properties"]
    assert "task_id" not in properties and "ref" not in properties
    assert set(properties) == {"block", "symptom", "why", "deps", "status"}


def test_the_object_is_closed_so_a_misspelt_argument_never_reaches_the_parser(tmp_path):
    for tool in listed(project(tmp_path)).values():
        assert tool["inputSchema"]["additionalProperties"] is False


def test_the_read_only_hint_says_which_tools_write(tmp_path):
    hints = {
        name: tool["annotations"]["readOnlyHint"]
        for name, tool in listed(project(tmp_path)).items()
    }
    # `lint` is read-only *because* `--fix` is not exposed: RK16 belongs where a human is
    # standing (the pre-commit hook), so the tool cannot repair anything.
    writes = {name for name, only_reads in hints.items() if not only_reads}
    assert writes == {
        "add",
        "status",
        "amend",
        "ship",
        "retire",
        # The third and fourth doors a line leaves and returns by (RK91) — beside the two
        # terminal ones, because a session that has to choose between them is at that spot.
        "defer",
        "resume",
        "record_add",
        "record_drop",
        "non_goal_add",
        "non_goal_drop",
        "section_add",
        "section_drop",
    }
    # `lint` is read-only *because* `--fix` is not exposed, so it takes no arguments at all.
    assert listed(project(tmp_path))["lint"]["inputSchema"]["properties"] == {}


# -- the same write path -----------------------------------------------------


def test_add_writes_the_line_the_cli_would_have_written(tmp_path):
    project(tmp_path)
    result = called(
        tmp_path, "add", block="A", symptom="Nothing states the id", why="Derive it."
    )
    assert result["isError"] is False
    payload = json.loads(text_of(result))
    # `--json` is always passed, so the answer carries the file and line it landed on: an
    # answer an agent cannot audit is one it re-reads the file to check (L5).
    assert payload["id"] == "RK2" and payload["file"] == ROADMAP and payload["line"]
    assert "**RK2**" in (tmp_path / ROADMAP).read_text(encoding="utf-8")


def test_a_repeated_dep_arrives_as_the_array_the_schema_declares(tmp_path):
    project(tmp_path)
    line = argv(tool_named("add"), {"block": "A", "symptom": "s", "why": "w.", "deps": ["RK1", "Block A"]})
    assert line.count("--dep") == 2
    result = called(tmp_path, "add", block="A", symptom="A second", why="A reason.", deps=["RK1"])
    assert result["isError"] is False
    assert "deps: RK1" in (tmp_path / ROADMAP).read_text(encoding="utf-8")


def test_an_over_length_field_is_refused_with_the_limit_and_nothing_is_written(tmp_path):
    project(tmp_path, config=CONFIG + "[limits]\nsymptom = 20\n")
    before = (tmp_path / ROADMAP).read_text(encoding="utf-8")
    result = called(tmp_path, "add", block="A", symptom="x" * 40, why="A reason.")
    assert result["isError"] is True
    assert "20" in text_of(result)
    assert (tmp_path / ROADMAP).read_text(encoding="utf-8") == before


def test_the_exit_code_is_the_error_flag(tmp_path):
    project(tmp_path, roadmap=CLEAN.replace("→ §RK1", ""))  # a pointer nothing resolves
    assert called(tmp_path, "lint")["isError"] is True
    project(tmp_path)
    assert called(tmp_path, "lint")["isError"] is False


def test_a_missing_required_argument_is_answered_and_not_raised(tmp_path):
    # argparse exits on a missing `--why`; a `SystemExit` escaping here would end the
    # session's server, so it becomes the same `isError` any other refusal is.
    result = called(project(tmp_path), "add", block="A")
    assert result["isError"] is True
    assert "--why" in text_of(result) or "why" in text_of(result)


# -- a wrong name earns the allowed set --------------------------------------


def test_an_unknown_argument_names_what_the_tool_takes(tmp_path):
    result = called(project(tmp_path), "add", blok="A")
    assert result["isError"] is True
    assert "blok" in text_of(result) and "block" in text_of(result)


def test_an_unknown_tool_names_the_tools_that_exist(tmp_path):
    result = called(project(tmp_path), "shipit", id="RK1")
    assert result["isError"] is True
    for name in ("add", "ship", "pick", "lint"):
        assert name in text_of(result)


def test_a_value_of_the_wrong_type_is_refused_before_dispatch():
    with pytest.raises(ToolError, match="must be a string"):
        argv(tool_named("ship"), {"id": 5})
    with pytest.raises(ToolError, match="must be an array"):
        argv(tool_named("add"), {"deps": "RK1"})


# -- the protocol ------------------------------------------------------------


@pytest.mark.parametrize("asked", KNOWN_PROTOCOLS)
def test_the_handshake_answers_with_the_version_the_client_asked_for(asked):
    response = handle(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": asked},
        }
    )
    assert response["result"]["protocolVersion"] == asked
    assert response["result"]["capabilities"] == {"tools": {}}
    assert response["result"]["serverInfo"]["name"] == "roadkeep"


def test_the_handshake_names_the_tree_that_will_answer_every_call():
    """RK79: this is the one moment the server gets to say which engine it is.

    `serverInfo.version` stays the release number, because a client may be pinned against
    it — the directory and the commit go to `instructions`, which is the field a session
    actually reads.
    """
    from roadkeep import __version__
    from roadkeep.provenance import engine

    response = handle({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
    assert response["result"]["serverInfo"]["version"] == __version__
    assert response["result"]["instructions"] == str(engine())
    assert str(engine().home) in response["result"]["instructions"]


def test_an_unknown_protocol_version_is_answered_with_one_this_server_knows():
    response = handle(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": "1999-01-01"},
        }
    )
    assert response["result"]["protocolVersion"] == PROTOCOL


def test_a_notification_is_not_answered():
    assert handle({"jsonrpc": "2.0", "method": "notifications/initialized"}) is None


def test_an_unknown_method_is_a_protocol_error_and_not_a_tool_error():
    response = handle({"jsonrpc": "2.0", "id": 2, "method": "resources/list"})
    assert response["error"]["code"] == METHOD_NOT_FOUND


def test_ping_is_answered_empty():
    assert handle({"jsonrpc": "2.0", "id": 3, "method": "ping"})["result"] == {}


def test_a_malformed_line_is_reported_and_the_loop_survives_it(tmp_path):
    reader = io.StringIO(
        "not json\n"
        "\n"
        '{"jsonrpc": "2.0", "method": "notifications/initialized"}\n'
        '{"jsonrpc": "2.0", "id": 9, "method": "ping"}\n'
    )
    writer = io.StringIO()
    assert serve(reader, writer, str(tmp_path)) == 0
    answers = [json.loads(line) for line in writer.getvalue().splitlines()]
    # Three inputs that could have answered, two that should: the blank line and the
    # notification are silent, and the parse error did not end the loop.
    assert [a.get("error", {}).get("code", a.get("id")) for a in answers] == [
        PARSE_ERROR,
        9,
    ]


# -- a broken config still serves --------------------------------------------


def test_a_broken_config_still_lists_the_tools(tmp_path):
    (tmp_path / "roadkeep.toml").write_text("prefix = 12\n", encoding="utf-8")
    add = listed(tmp_path)["add"]["inputSchema"]["properties"]
    # The defaults, which is a schema that is wrong about this project rather than a session
    # with no tools at all — and the first call is what reports the config error.
    assert add["symptom"]["maxLength"] == Config.default().schema.symptom_max
    assert called(tmp_path, "lint")["isError"] is True


def test_the_server_subcommand_tolerates_a_broken_config():
    # `main` reads this flag; without it a typo in `roadkeep.toml` would stop the process
    # the session started once, and take the four tools with it.
    assert build_parser().parse_args(["mcp"]).tolerates_config_error is True
