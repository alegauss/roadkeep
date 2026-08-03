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

import contextlib
import io
import json
import os
import re
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from roadkeep import claiming, serving
from roadkeep.cli import build_parser
from roadkeep.config import Config
from roadkeep.provenance import _LOADED_AT, engine
from roadkeep.serving import (
    KNOWN_PROTOCOLS,
    METHOD_NOT_FOUND,
    PARSE_ERROR,
    PROTOCOL,
    TOOLS,
    Prose,
    Tool,
    ToolError,
    _action,
    _spent_stdin,
    _subparser,
    argv,
    call,
    descriptor,
    handle,
    prose_of,
    serve,
    tool_named,
)

ROADMAP = "docs/ROADMAP.md"
CHANGELOG = "docs/CHANGELOG.md"
IMPROVEMENTS = "docs/IMPROVEMENTS.md"

CLEAN = """# Roadmap

## Block A — The model

- 📋 **RK1** (deps: —) **A first symptom** — Because of a reason. → §RK1
"""

LEDGER = """# Shipped

## Block A — The model
"""

COLLIDED = "- 📋 **RK2** (deps: RK1) **A second symptom** — Because of a reason. → §RK2\n"

DESIGN = """# Improvements

## Block A — The model

### §RK1 The first design

Because a pointer resolving to nothing reads exactly like a design that exists.
"""

CONFIG = f'prefix = "RK"\n[files]\nroadmap = "{ROADMAP}"\nchangelog = "{CHANGELOG}"\n'
#: A project whose pointers have somewhere to resolve, which is what any call touching a
#: rationale needs — `section add` refuses a role the project declares no file for.
PROSE = CONFIG + f'improvements = "{IMPROVEMENTS}"\n'
#: A project that declares the one id shape the counter cannot spell (RK111). Turing's, and
#: the only config under which `add` offers an id at all.
SUFFIXED = PROSE + "[ids]\nsuffix = true\n"


def project(
    tmp_path: Path,
    *,
    roadmap: str = CLEAN,
    config: str = CONFIG,
    improvements: str | None = None,
) -> Path:
    (tmp_path / "roadkeep.toml").write_text(config, encoding="utf-8")
    files = {ROADMAP: roadmap, CHANGELOG: LEDGER}
    if improvements is not None:
        files[IMPROVEMENTS] = improvements
    for name, body in files.items():
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
        "block_add",
        # And the key that could not close the door (RK144): the caller that opened a label by
        # mistake is the one the guard denies the hand-edit to, which is RK141's own argument.
        "block_drop",
        # `brief --claim` under the name of the act (RK149, RK150): the write a session makes
        # first, split off so the two reads below keep the hint that makes them free to ask.
        "claim",
        "status",
        "amend",
        # The field `amend` excludes, at its own door (RK178): a premise that turned out false
        # is not a different task, and the exit designed for it spends an id and a section.
        "restate",
        # The door a merge that spent one id twice needs (RK97) — beside `amend`, whose
        # every other field it is, and which deliberately refuses this one.
        "renumber",
        "ship",
        "retire",
        # The third and fourth doors a line leaves and returns by (RK91) — beside the two
        # terminal ones, because a session that has to choose between them is at that spot.
        "defer",
        "resume",
        "record_add",
        "record_amend",
        # The move `record_amend` refuses to spell as a correction (RK143): an entry filed
        # under the wrong block is what a wrongly filed roadmap line ships to, which is the
        # agent's own slip and the hand-edit the guard denies that agent.
        "record_move",
        "record_drop",
        "record_renumber",
        "non_goal_add",
        "non_goal_drop",
        "section_add",
        "section_amend",
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
    passed = {"anchor": "RK1", "title": "A design", "body": "Because of a reason."}
    assert argv(tool, passed, Config.default())[:2] == ["section", "add"]


def test_every_tool_is_a_subcommand_the_cli_accepts():
    # The same argument the Action and the pre-commit hook get: a surface that drifts from
    # `cli.py` fails a test instead of failing a call.
    for tool in TOOLS:
        parsed = build_parser().parse_args(argv(tool, _minimal(tool), Config.default()))
        assert parsed.command == tool.argv_head[0]
        assert parsed.json is True  # never exposed, always passed


def _minimal(tool: Tool) -> dict[str, str]:
    """The required arguments, filled with anything: this is about the argv, not the values.

    Plus the prose argument where leaving it out would go to the pipe (RK171): that argv is one
    this surface refuses, so it is not part of any minimum that is meant to parse.
    """
    required = descriptor(tool, Config.default())["inputSchema"].get("required", [])
    filled = {name: "RK1" if name == "id" else "x" for name in required}
    prose = prose_of(tool.command)
    if prose is not None and prose.dest in tool.exposes and prose.reached_by(filled):
        filled[prose.dest] = "The prose, passed as a string because there is no pipe."
    return filled


def test_the_limits_in_the_schema_are_the_projects_own(tmp_path):
    project(
        tmp_path,
        config=CONFIG + "[limits]\nsymptom = 60\nwhy = 90\n",
    )
    add = listed(tmp_path)["add"]["inputSchema"]["properties"]
    assert add["symptom"]["maxLength"] == 60
    assert add["why"]["maxLength"] == 90


def test_the_why_says_which_limit_actually_binds(tmp_path):
    # RK183: `maxLength` is the field's ceiling, and the line is what refuses. A lower
    # number here would refuse on the client a line the server accepts, so the ceiling
    # stays and the joint rule is said in words — with this project's own line limit.
    project(tmp_path, config=CONFIG + "[limits]\nline = 240\n")
    why = listed(tmp_path)["add"]["inputSchema"]["properties"]["why"]
    assert why["maxLength"] == Config.default().schema.why_max
    assert "240" in why["description"]
    # The flag's own sentence survives it: the note is appended, never a replacement.
    flag = serving._action(serving._subparser("add"), "why")
    assert why["description"].startswith(flag.help.strip())


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
        assert descriptor(tool, Config.default())["description"].startswith(described.strip())


def test_a_flag_that_became_a_tool_describes_itself_out_of_its_own_help():
    # RK150: `claim` is `brief --claim`, and what it adds over `brief` is the flag's own help
    # — quoted rather than restated, so two tools over one command cannot describe the
    # difference in two ways, and neither can go stale when the help is reworded.
    tool = tool_named("claim")
    described = descriptor(tool, Config.default())["description"]
    assert described.startswith(_subparser("brief").description.strip())
    assert "always passes --claim" in described
    assert _action(_subparser("brief"), "claim").help in described


def test_a_write_that_needs_prose_takes_it_as_a_bounded_string(tmp_path):
    # `section add` reads stdin in a shell; over MCP the body is an argument, and the word
    # budget refuses it exactly the same way.
    properties = listed(project(tmp_path))["section_add"]["inputSchema"]["properties"]
    assert set(properties) == {"anchor", "title", "body", "role"}
    assert properties["body"]["type"] == "string"


def test_the_derived_fields_are_not_offered(tmp_path):
    """`add --id` and `add --ref` exist for adoption; offering them lets a caller choose
    what the tool derives, and a hand-set id is the one thing the schema cannot check.

    `task_id` is absent *here* because this project declares no suffix — where one is
    declared it is offered, which is RK111 and the test below."""
    properties = listed(project(tmp_path))["add"]["inputSchema"]["properties"]
    assert "task_id" not in properties and "ref" not in properties
    assert set(properties) == {
        "block",
        "symptom",
        "why",
        "deps",
        "status",
        # The rationale is the other half of one write (RK93), so it is offered here for
        # the reason `section add`'s body is: stdin belongs to the protocol.
        "section",
        "section_body",
    }


def test_a_declared_suffix_opens_the_one_id_the_counter_cannot_spell(tmp_path):
    # RK111: `spell_id` counts and never letters, so on a project declaring `[ids] suffix`
    # the write path an agent is told to prefer could not produce a legal split id at all.
    # Offered there, bounded to *require* the letter, and required nowhere — the number is
    # still derived when the field is left out.
    properties = listed(project(tmp_path, config=SUFFIXED))["add"]["inputSchema"]
    assert "task_id" in properties["properties"]
    assert "task_id" not in properties.get("required", [])
    pattern = properties["properties"]["task_id"]["pattern"]
    assert re.match(pattern, "RK7b") and not re.match(pattern, "RK7")
    # And it is the schema's own spelling of the shape, not a second copy written here.
    schema = Config.discover(project(tmp_path, config=SUFFIXED)).schema
    assert pattern == schema.split_id_pattern().pattern


def test_a_chosen_id_is_refused_when_it_is_one_deriving_would_have_reached(tmp_path):
    # The narrowing is the whole of RK111: the field buys the id the counter cannot mint, so
    # a bare number through it is the choice the surface withholds — checked here and not
    # only published, because a bound a client may skip is a bound on the client.
    config = Config.discover(project(tmp_path, config=SUFFIXED))
    chosen = {"block": "A", "symptom": "s", "why": "w.", "task_id": "RK9"}
    add = tool_named("add")
    with pytest.raises(ToolError) as caught:
        argv(add, chosen, config)
    assert "leave the field out and it is derived" in str(caught.value)


def test_the_refusal_names_the_declaration_that_would_open_the_field(tmp_path):
    # Without the clause the message reads as a misspelling and the caller retries the same
    # spelling: which arguments a tool takes is a fact about `roadkeep.toml` (L6).
    refused = text_of(
        called(project(tmp_path), "add", block="A", symptom="s", why="w.", task_id="RK9b")
    )
    assert "no such argument task_id" in refused
    assert "[ids] suffix" in refused and "this project declares none" in refused


def test_a_split_id_reaches_the_roadmap_over_the_protocol(tmp_path):
    # End to end, because the defect was that this call could not be made: the id is written
    # verbatim, and the same refusals hold — `refuse_reuse` and the project's own id shape.
    tree = project(tmp_path, config=SUFFIXED, improvements=DESIGN)
    written = json.loads(
        text_of(called(tree, "add", block="A", symptom="A split half", why="Because.",
                       task_id="RK1b"))
    )
    assert written["id"] == "RK1b"
    assert "**RK1b**" in (tree / ROADMAP).read_text(encoding="utf-8")
    # The id is still never reused, whichever surface chose it.
    again = text_of(called(tree, "add", block="A", symptom="s", why="w.", task_id="RK1b"))
    assert "already occurs" in again


def test_a_flag_that_became_a_tool_is_always_passed_and_never_settable(tmp_path):
    # RK150's mechanism: the act is the name, the flag is not an argument, and the argv is
    # still the CLI's own — so nothing is reachable here that a terminal cannot run.
    tool = tool_named("claim")
    assert argv(tool, {}, Config.default()) == ["brief", "--claim", "--json"]
    assert argv(tool, {"id": "RK1"}, Config.default()) == ["brief", "RK1", "--claim", "--json"]
    # Unsettable in both directions: a caller cannot ask a claiming tool not to claim.
    with pytest.raises(ToolError) as caught:
        argv(tool, {"claim": False}, Config.default())
    assert "no such argument claim" in str(caught.value)
    assert "claim" not in listed(project(tmp_path))["claim"]["inputSchema"]["properties"]


def test_whether_a_tool_writes_is_derived_and_not_stated(tmp_path):
    # RK168: it was a boolean per tool because `lint` was the exception — read-only *here* only
    # by not exposing `--fix`. With the parser saying which flag makes it a write, the answer
    # comes from the parser and the flags this tool passes.
    assert not tool_named("lint").writes
    # Not vacuous: exposing that flag is what flips it, which is the whole derivation.
    assert Tool("lint", ("baseline", "fix")).writes
    # And a command whose parser never called itself a read writes whatever it exposes.
    assert Tool("add", ()).writes


def test_the_two_reads_a_claim_was_split_off_from_stay_free_to_ask(tmp_path):
    # The cost RK150 records: `readOnlyHint` is one boolean per tool, so a `pick` that could
    # write is a `pick` a client may prompt for — and consulting the backlog is meant to be
    # the thing that costs nothing (L5).
    hints = listed(project(tmp_path))
    assert hints["pick"]["annotations"]["readOnlyHint"] is True
    assert hints["brief"]["annotations"]["readOnlyHint"] is True
    assert hints["claim"]["annotations"]["readOnlyHint"] is False
    for name in ("pick", "brief"):
        assert "claim" not in hints[name]["inputSchema"]["properties"]


def test_claiming_over_the_protocol_moves_the_marker(tmp_path):
    project(tmp_path)
    answer = called(tmp_path, "claim")
    assert not answer["isError"]
    assert json.loads(text_of(answer))["claimed"]["to"] == "🛠"
    # And the read that was split off from it still answers, now about a different line.
    assert json.loads(text_of(called(tmp_path, "pick")))["held"][0]["id"] == "RK1"
    claiming.path(tmp_path).unlink(missing_ok=True)  # it lives outside the checkout


def test_the_guard_never_names_the_claiming_tool_for_a_plain_read(tmp_path):
    # `_tool_for` matches by argv head and two tools now share one (RK150): a suggestion to
    # run `brief` must not be answered with the tool that also takes the line.
    from roadkeep.guarding import _tool_for

    assert _tool_for("brief RK1") == "brief"


def test_the_pick_can_be_narrowed_to_written_designs_over_the_protocol(tmp_path):
    # RK83's flag reaches the caller it was written for: the agent asking to execute a
    # block is the one this server exists for, and a CLI-only flag is one it cannot pass.
    properties = listed(project(tmp_path))["pick"]["inputSchema"]["properties"]
    assert properties["designed"]["type"] == "boolean"
    assert argv(tool_named("pick"), {"designed": True}, Config.default()) == [
        "pick",
        "--designed",
        "--json",
    ]
    # False is the default, and a flag argparse reads as present cannot say "no".
    assert argv(tool_named("pick"), {"designed": False}, Config.default()) == ["pick", "--json"]


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
        "block_add",
        "block_drop",
        "status",
        "amend",
        "restate",
        "renumber",
        "ship",
        "retire",
        # The third and fourth doors a line leaves and returns by (RK91) — beside the two
        # terminal ones, because a session that has to choose between them is at that spot.
        "defer",
        "resume",
        "record_add",
        "record_amend",
        "record_move",
        "record_drop",
        "record_renumber",
        "non_goal_add",
        "non_goal_drop",
        "section_add",
        "section_amend",
        "section_drop",
        # `brief --claim` moves a marker, so the tool that always passes it says so — and
        # `brief` and `pick` stay read-only *because* it is a separate tool (RK150), which is
        # the same reason `lint` is read-only: the writing flag is not reachable from it.
        "claim",
    }
    # `lint` is read-only *because* `--fix` is not exposed, and `--baseline` (RK84) is the
    # one argument it takes: a revision to subtract, which reads history and writes none.
    assert set(listed(project(tmp_path))["lint"]["inputSchema"]["properties"]) == {"baseline"}


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


def test_a_rationale_arrives_as_an_argument_because_stdin_is_the_protocol(tmp_path):
    # A client that could not pass the prose here would leave every `add` pointing at a
    # section that does not exist (RK93) — and the pipe a shell uses is the JSON-RPC
    # channel in this process, so the body has to be an argument.
    project(
        tmp_path,
        config=CONFIG + f'improvements = "{IMPROVEMENTS}"\n',
        improvements=DESIGN,
    )
    result = called(
        tmp_path,
        "add",
        block="A",
        symptom="A second symptom",
        why="A reason.",
        section="A design",
        section_body="Because the gate said so.",
    )
    assert result["isError"] is False
    payload = json.loads(text_of(result))
    assert payload["needs"] is None
    assert payload["section"]["anchor"] == "RK2"
    written = (tmp_path / IMPROVEMENTS).read_text(encoding="utf-8")
    assert "### §RK2 A design" in written
    assert called(tmp_path, "lint")["isError"] is False


def test_an_add_with_no_rationale_reports_the_follow_up_the_gate_would_find(tmp_path):
    project(
        tmp_path,
        config=CONFIG + f'improvements = "{IMPROVEMENTS}"\n',
        improvements=DESIGN,
    )
    payload = json.loads(
        text_of(called(tmp_path, "add", block="A", symptom="A second", why="A reason."))
    )
    assert payload["needs"].startswith("section add RK2 --title")
    assert called(tmp_path, "lint")["isError"] is True


def test_the_merge_repair_is_reachable_by_the_caller_the_hook_denies(tmp_path):
    # The agent that hits a doubled id is exactly the one `Edit` is denied to (RK22), so a
    # renumber only a terminal can run is a door that is closed where it is needed.
    project(tmp_path, roadmap=CLEAN + COLLIDED, config=CONFIG + f'improvements = "{IMPROVEMENTS}"\n', improvements=DESIGN)
    payload = json.loads(text_of(called(tmp_path, "renumber", id="RK1", to="RK9")))
    assert payload["to"] == "RK9"
    assert "**RK9**" in (tmp_path / ROADMAP).read_text(encoding="utf-8")


def test_a_repeated_dep_arrives_as_the_array_the_schema_declares(tmp_path):
    project(tmp_path)
    line = argv(
        tool_named("add"),
        {"block": "A", "symptom": "s", "why": "w.", "deps": ["RK1", "Block A"]},
        Config.default(),
    )
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
        argv(tool_named("ship"), {"id": 5}, Config.default())
    with pytest.raises(ToolError, match="must be an array"):
        argv(tool_named("add"), {"deps": "RK1"}, Config.default())


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


# -- the read that ate the transport (RK170) -----------------------------------


class _Transport(io.StringIO):
    """A stand-in for the client's pipe that reports being read rather than blocking on one."""

    def read(self, *args, **kwargs):  # noqa: ANN002, ANN003 - matches the stream it replaces
        raise AssertionError("the transport this call arrived on was read")


@contextlib.contextmanager
def _watched_transport():
    saved = sys.stdin
    sys.stdin = _Transport()
    try:
        yield
    finally:
        sys.stdin = saved


def _variants(tool: Tool) -> list[dict[str, str]]:
    """The argvs worth trying: the minimum, plus the two shapes a `Prose` calls a pipe read."""
    base = _minimal(tool)
    out = [dict(base)]
    prose = prose_of(tool.command)
    if prose is None or prose.dest not in tool.exposes:
        return out
    omitted = {name: value for name, value in base.items() if name != prose.dest}
    if prose.gated_by:
        omitted[prose.gated_by] = "A design"
    return [*out, omitted, {**base, prose.dest: prose.sentinel}]


def test_no_exposed_argv_reaches_a_read_of_the_transport():
    """RK171: the question is not which handler reads stdin, it is which one *can*.

    Three tools could, and neither `TOOLS` nor `cli.py` said so — `add` on a section named with
    no body, `section add` on a body omitted, `section amend` on the `-` its help documents. The
    deadlock was met on `add` because that is the verb a task is filed with, and fixing the path
    that was met leaves the other two waiting for the session that meets them.

    Asserted at the argv, which is where the answer is decided and where `_spent_stdin` is not in
    scope to mask it: every tool, over every shape a `Prose` calls a pipe read, either refused
    here or declared unreachable. The assertion survives a fourth tool being exposed, which a
    reviewer reading two diffs does not.
    """
    for tool in TOOLS:
        prose = prose_of(tool.command)
        for arguments in _variants(tool):
            reaches = prose is not None and prose.dest in tool.exposes
            reaches = reaches and prose.reached_by(arguments)
            if not reaches:
                argv(tool, arguments, Config.default())  # parses, and goes nowhere near a pipe
                continue
            with pytest.raises(ToolError) as caught:
                argv(tool, arguments, Config.default())
            assert "no pipe to read it from" in str(caught.value), (tool.name, arguments)


def test_a_call_can_never_be_handed_the_transport_either(tmp_path):
    # The belt behind that brace (RK170): even an argv the refusal above did not catch — a
    # handler this surface does not expose the body of, a flag added tomorrow — is dispatched
    # against a stream at EOF, so the worst case is a refusal and never a session that stops.
    tree = str(project(tmp_path, config=PROSE, improvements=DESIGN))
    for tool in TOOLS:
        for arguments in _variants(tool):
            with _watched_transport():
                answered = call(tool, arguments, tree)
            # What it answers is not this test's business — only that it answered at all.
            assert answered.text


def test_the_three_paths_that_could_reach_it_are_the_ones_declared():
    # The inventory §RK171 says neither file stated, now derived from the parsers. `record add`
    # is the asymmetry that makes it a real question: it writes a ledger entry and exposes no
    # body at all, so it cannot reach the read however it is called.
    reaching = {tool.name for tool in TOOLS if prose_of(tool.command) is not None}
    assert reaching == {"add", "section_add", "section_amend"}
    assert prose_of("record add") is None


def test_each_declaration_says_which_argv_goes_to_the_pipe():
    # Three commands, three different answers, which is why one comment in one handler was not
    # the statement of it: `add` is gated on a section being named, `section add` reads on a
    # plain omission, and `section amend` only on the `-` it documents.
    assert prose_of("add") == Prose(dest="section_body", gated_by="section")
    assert prose_of("section add") == Prose(dest="body")
    assert prose_of("section amend") == Prose(dest="body", omitted=False)
    # An `add` naming no section must never block on a pipe — the comment that was the guard.
    assert not prose_of("add").reached_by({"block": "A", "symptom": "s", "why": "w."})
    assert prose_of("add").reached_by({"section": "A design"})
    assert not prose_of("section amend").reached_by({"title": "A new heading"})
    assert prose_of("section amend").reached_by({"body": "-"})


def test_the_transport_is_intact_after_a_call_that_reads_it(tmp_path):
    # The half that matters most: the deadlock was not that one call failed, it was that every
    # message queued behind it was consumed. A second call on the same server must answer.
    tree = project(tmp_path, config=PROSE, improvements=DESIGN)
    called(tree, "section_add", anchor="RK2", title="A second design")
    answered = called(tree, "list", block="A")
    assert answered["isError"] is False and "RK1" in text_of(answered)


def test_the_substituted_stream_is_exhausted_and_not_closed():
    # The distinction the fix rests on: `read()` on a *closed* stream raises `ValueError`,
    # which `REFUSALS` would report as bad input — a second wrong answer instead of the one
    # the format already owns for prose that is not there.
    with _spent_stdin():
        assert sys.stdin.read() == ""
        assert sys.stdin.closed is False


def test_the_real_stdin_is_given_back(tmp_path):
    # A server whose loop reads the next message off a `StringIO` it substituted for one call
    # is a server that answers exactly one.
    before = sys.stdin
    called(project(tmp_path), "lint")
    assert sys.stdin is before


def test_an_argv_that_would_have_gone_to_the_pipe_names_the_argument(tmp_path):
    # `_spent_stdin` closes the deadlock whatever this says, so what this buys is which refusal
    # is read: `body.empty` is true and about the prose, when the fact is that the argument
    # carrying it did not arrive. All three declared paths answer the same way (RK171).
    tree = project(tmp_path, config=PROSE, improvements=DESIGN)
    refusals = [
        text_of(called(tree, "add", block="A", symptom="s", why="w.", section="A design")),
        text_of(called(tree, "section_add", anchor="RK2", title="A second design")),
        text_of(called(tree, "section_amend", anchor="RK1", body="-")),
    ]
    for refused in refusals:
        assert "there is no pipe to read it from" in refused
        assert "pass it as a string" in refused
    # And the pair still goes through when both halves are there, which is RK93's whole point.
    written = called(
        project(tmp_path, config=PROSE, improvements=DESIGN),
        "add",
        block="A",
        symptom="A second symptom",
        why="Because of a reason.",
        section="A second design",
        section_body="Because a pointer resolving to nothing reads like a design that exists.",
    )
    assert written["isError"] is False


# -- the refusal that was about the code and read as being about the project ----


def test_a_config_refusal_names_the_build_that_read_the_config(tmp_path):
    # RK155, measured: `[claims] held` reached `roadkeep.toml` and `config.py` in one commit,
    # and every MCP write refused `unknown key 'claims'` while the CLI in a terminal accepted
    # it — a refusal correct about the code and wrong about the project. Which build read the
    # file is the fact that turns that puzzle into an instruction, and it cannot be wrong.
    (tmp_path / "roadkeep.toml").write_text("prefix = 12\n", encoding="utf-8")
    refused = text_of(called(tmp_path, "add", block="A", symptom="s", why="w."))
    assert "roadkeep:" in refused
    assert f"read by {engine()}" in refused


def test_a_refusal_says_when_the_code_answering_it_moved(tmp_path, monkeypatch):
    # The note rides on any refusal, because a build behind can be wrong about anything — and
    # nothing reloads: the harness restarts a plugin whose version moved (RK153).
    monkeypatch.setattr(
        "roadkeep.serving.engine",
        lambda: replace(engine(), home=_moved(tmp_path)),
    )
    answered = called(project(tmp_path), "status", id="RK99", marker="🛠")
    assert answered["isError"] is True
    refused = text_of(answered)
    assert "imported roadkeep before config.py changed on disk" in refused
    assert "restart the session" in refused


def test_an_answer_that_worked_explains_nothing(tmp_path, monkeypatch):
    # A note on every answer is a note that stops being read, and a call that succeeded has
    # nothing to explain about the build that succeeded at it.
    monkeypatch.setattr(
        "roadkeep.serving.engine",
        lambda: replace(engine(), home=_moved(tmp_path)),
    )
    answered = called(project(tmp_path), "list", block="A")
    assert answered["isError"] is False
    assert "changed on disk" not in text_of(answered)


def _moved(tmp_path: Path) -> Path:
    """A package directory whose `config.py` is newer than this process's import of one."""
    home = tmp_path / "engine" / "roadkeep"
    home.mkdir(parents=True, exist_ok=True)
    (home / "config.py").write_text("x = 1\n", encoding="utf-8")
    os.utime(home / "config.py", (_LOADED_AT + 300, _LOADED_AT + 300))
    return home
