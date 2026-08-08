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
from roadkeep import cli
from roadkeep.cli import EXIT_OK, EXIT_USAGE, build_parser, main
from roadkeep.config import Config
from conftest import since_import
from roadkeep.provenance import engine, invocation
from roadkeep.schema import body_aim
from roadkeep.serving import (
    KNOWN_PROTOCOLS,
    _CONDITIONAL,
    METHOD_NOT_FOUND,
    PARSE_ERROR,
    PROTOCOL,
    TOOLS,
    Conditional,
    Prose,
    Tool,
    ToolError,
    _action,
    _spent_stdin,
    _subparser,
    argv,
    call,
    descriptor,
    descriptors,
    Watch,
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
#: A project whose anchors are an outline and not the id (RK241). Shio's, and the only config
#: under which `add` offers a pointer — the field it withheld from itself until then.
OUTLINED = (
    f'prefix = "RK"\nref_scheme = "outline"\n[files]\nroadmap = "{ROADMAP}"\n'
    f'changelog = "{CHANGELOG}"\nimprovements = "{IMPROVEMENTS}"\n'
)


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
        # The key RK141/RK144's pair never cut (RK403): a doubled heading is the state every
        # write refuses with `merge by hand`, and over MCP there is no hand-edit at all.
        "block_merge",
        # `brief --claim` under the name of the act (RK149, RK150): the write a session makes
        # first, split off so the two reads below keep the hint that makes them free to ask.
        "claim",
        # The other verb with that word on it (RK308): the tool above takes a line, this one
        # says which paths the commit owns — `claim <id> --path`, which was CLI-only, so the
        # agent this ships for declared no scope and got every changed path back as loose.
        "scope",
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
        # The correction the other two bullet grammars had and this one did not (RK368).
        "non_goal_amend",
        "non_goal_drop",
        # The queue, once it had a governed home (RK325): the agent that ships a queued
        # id is the one that has to take it out, and the file it lives in is one the
        # guard denies an edit to.
        "priority_add",
        "priority_drop",
        "section_add",
        "section_amend",
        # The address `renumber` cannot reach under an outline (RK377), beside the two
        # writes that reach everything else about a section.
        "section_move",
        "section_drop",
        # The two reads a session that is *proposing* makes, so they head the reads: what
        # may not be proposed at all (RK69), and what a comparable one cost (RK71).
        "non_goal_list",
        "priority_list",
        "weight",
        # And the third (RK190): what the line being proposed leaves its prose, which
        # `maxLength` cannot publish because it moves with the deps and the symptom.
        "budget",
        "brief",
        "pick",
        "list",
        "deps",
        "lint",
        # The read the agent is the subject of (RK415): its writes go through whatever
        # `roadkeep` the session reaches and its hand edits are denied by whatever the
        # harness installed, and those are allowed to be two versions of this tool.
        "engines",
        # The one query that is not its own subcommand (RK275): `merge --check` writes nothing
        # and answers in three lines, and the verb around it is git's driver contract — so the
        # flag becomes the tool, by the mechanism `claim` already is (RK150).
        "merge_check",
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


def test_every_served_command_that_gates_json_is_served_through_the_gate(tmp_path):
    # RK319: `argv` ends every command line with `--json` and never exposes it, and RK317 made
    # `merge` refuse that flag outside the branch it is the form of. Together those make a command
    # servable only through a tool whose `always` carries the gating argument — and the coupling
    # held by coincidence, one tool over that command happening to carry it. A served tool that
    # did not would refuse every call it ever received, over a flag the caller cannot remove.
    from roadkeep.cli import json_needs

    gated = 0
    for tool in TOOLS:
        needed = json_needs(serving._subparser(tool.command))
        if not needed:
            continue
        gated += 1
        assert needed in tool.always, f"{tool.name} would refuse its own --json"
    # Named rather than counted, so a command that grows the declaration is a deliberate addition:
    # `merge_check` is the one, and `merge` itself is deliberately not served.
    assert gated == 1


def test_the_gate_is_read_from_the_parser_and_not_from_a_branch_position(tmp_path, capsys):
    # The refusal used to sit after the `--check` branch and mean "everything past here", which is
    # a claim no surface can read. Declared, the same argv answers the same way and the flag in the
    # message is spelled from the parser rather than written a second time.
    from roadkeep.cli import json_needs

    assert json_needs(build_parser().parse_args(["merge", "--check"])) == "check"
    served = called(project(tmp_path), "merge_check")
    # The one tool over that command still answers as JSON, which is what the coupling protects.
    assert json.loads(text_of(served))["sound"] is False


def test_every_divergent_verb_is_one_the_cli_still_spells_that_way():
    # RK316: the selection used to be an `if` chain, and its failure was silent and in the
    # forbidden direction — a command renamed in `cli.py` left every `Tool` correct, no branch
    # matching, and the fields falling back to bounds narrower than the verb accepts, which is a
    # bound on the client. RK167's answer to a declaration that can stop matching, one file over.
    spelled = {tool.argv_head[0] for tool in TOOLS}
    for verb in serving._DIVERGENT:
        assert verb in spelled, f"{verb} names no served command"
        # And the CLI's own, not only this surface's: both halves have to agree or the table
        # describes a tool that dispatches somewhere else.
        assert serving._subparser(verb) is not None


def test_the_verbs_that_diverge_are_named_and_not_counted():
    # The list is the point: a third is a deliberate addition and not something a copied
    # override brought along. `non-goal` is `[non_goals]`' two limits (RK70) and `list` is the
    # one read whose `role` and `marker` mean every governed file (RK304, RK314).
    assert set(serving._DIVERGENT) == {"non-goal", "list"}
    # Every other tool gets the common table, which is what makes those two legible as exceptions.
    for tool in TOOLS:
        if tool.argv_head[0] not in serving._DIVERGENT:
            assert serving._bounds_for(tool) is serving._BOUNDS


def _minimal(tool: Tool) -> dict[str, str]:
    """The required arguments, filled with anything: this is about the argv, not the values.

    Plus the prose argument where leaving it out would go to the pipe (RK171): that argv is one
    this surface refuses, so it is not part of any minimum that is meant to parse.
    """
    required = descriptor(tool, Config.default())["inputSchema"].get("required", [])
    filled = {name: "RK1" if name == "id" else "x" for name in required}
    for prose in prose_of(tool.command):
        if prose.dest in tool.exposes and prose.reached_by(filled):
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


def test_the_prose_bodies_publish_the_word_budget_that_refuses_them(tmp_path):
    # RK258: `symptom` and `why` published a ceiling and a word aim, and the three bodies said
    # what the field was and never that a bound existed — so `section = 250` reached an author
    # only as a refusal, at the cost of re-sending a paragraph already composed.
    tree = project(tmp_path, config=PROSE + "[limits]\nsection = 40\n")
    described = listed(tree)
    for tool, field in (("add", "section_body"), ("section_add", "body"),
                        ("section_amend", "body")):
        published = described[tool]["inputSchema"]["properties"][field]
        assert "40 is what refuses" in published["description"]
        # The aim beside the gate, and under it (RK301): a ceiling published as its own
        # target is one hit from above, which is what the thirteen measured refusals were.
        assert f"Aim for {body_aim(40)} words" in published["description"]
        # And no `maxLength`: JSON Schema counts characters, so a ceiling derived from a word
        # count would refuse on the client prose this server accepts (RK183's rule).
        assert "maxLength" not in published
    # The number is this project's and not a literal here, which is the whole of RK24 (L6).
    assert Config.discover(tree).schema.section_max == 40


def test_a_role_with_its_own_budget_is_named_beside_the_default(tmp_path):
    # `[limits.<role>]` can give one prose file its own number (RK50), and this one field reaches
    # two — so a single figure would be true of neither and averaging them would be a third.
    tree = project(
        tmp_path,
        config=PROSE + 'strategy = "docs/STRATEGY.md"\n[limits]\nsection = 250\n'
        "[limits.strategy]\nsection = 90\n",
    )
    said = listed(tree)["section_add"]["inputSchema"]["properties"]["body"]["description"]
    assert "250 is what refuses" in said
    assert "strategy 90" in said and "that file's own number binds" in said


def test_a_role_the_project_never_declared_is_not_named(tmp_path):
    # RK259: `schema_for` answers for any role, composing `[limits.<role>]` over the base with no
    # reason to check for a file — so a limit left behind without a `[files]` entry published a
    # figure for a role `section add --role` refuses, which is a claim about one declaration.
    tree = project(
        tmp_path, config=PROSE + "[limits]\nsection = 250\n[limits.strategy]\nsection = 90\n"
    )
    assert not Config.discover(tree).has("strategy")
    said = listed(tree)["section_add"]["inputSchema"]["properties"]["body"]["description"]
    assert "250 is what refuses" in said
    assert "strategy" not in said and "90" not in said


def test_a_project_with_no_prose_file_still_gets_the_base_number(tmp_path):
    # The field is on the tool whatever `[files]` says, so the honest answer is the base limit —
    # not silence, which would read as "no bound", and not a role nobody declared.
    tree = project(tmp_path, config=CONFIG + "[limits]\nsection = 120\n")
    assert not any(Config.discover(tree).has(role) for role in ("improvements", "strategy"))
    said = listed(tree)["section_add"]["inputSchema"]["properties"]["body"]["description"]
    assert "120 is what refuses" in said


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
    assert "task_id is declared by the CLI and closed by this project's config" in refused
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


def test_an_outline_scheme_opens_the_anchor_nothing_derives(tmp_path):
    # RK241: under `ref_scheme = "outline"` the pointer is the caller's field, so withholding
    # it left every `add` over this transport refusing `ref.missing` — a tool that could not
    # make its own principal call. Offered there, and required nowhere the CLI does not.
    properties = listed(project(tmp_path, config=OUTLINED))["add"]["inputSchema"]
    assert "ref" in properties["properties"]
    assert "ref" not in properties.get("required", [])
    # And no pattern published here: `<x.y>` is `ref.format` from the schema, so a copy of it
    # on this surface would be the second declaration of one rule (RK24's own failure mode).
    assert "pattern" not in properties["properties"]["ref"]


def test_the_anchor_reaches_the_roadmap_over_the_protocol(tmp_path):
    # End to end, because the defect was that this call could not be made at all: the CLI was
    # the only door, and on the project that found it a source checkout was the only CLI.
    tree = project(tmp_path, config=OUTLINED, improvements=DESIGN)
    written = json.loads(
        text_of(called(tree, "add", block="A", symptom="An outlined symptom",
                       why="Because of a reason.", ref="4.2"))
    )
    assert written["rendered"].endswith("→ §4.2")
    assert "→ §4.2" in (tree / ROADMAP).read_text(encoding="utf-8")
    # And the prose the anchor names is still the caller's next call, not this one's silence.
    assert written["needs"].startswith("section add 4.2")


def test_a_closed_field_is_refused_by_the_table_that_would_open_it(tmp_path):
    # One clause per field and not one sentence for both (RK241): a caller told to declare
    # `[ids] suffix` to name an anchor is a caller sent to edit the wrong table.
    refused = text_of(
        called(project(tmp_path), "add", block="A", symptom="s", why="w.", ref="4.2")
    )
    assert "ref is declared by the CLI and closed by this project's config" in refused
    assert 'ref_scheme = "outline"' in refused and "[ids] suffix" not in refused
    # And where both are closed, both are named — the refusal is per field, so a call that
    # guessed twice does not read as one table being the answer to both.
    both = text_of(
        called(project(tmp_path), "add", block="A", symptom="s", why="w.",
               ref="4.2", task_id="RK9b")
    )
    assert 'ref_scheme = "outline"' in both and "[ids] suffix" in both


def test_a_closed_field_is_not_reported_as_one_that_does_not_exist(tmp_path):
    # RK253: `--ref` is declared by the CLI, printed by its help and reachable at a terminal, so
    # "no such argument" sends the caller looking for a typo in a name spelled correctly. The two
    # facts are stated over their own names, and a call that guessed both ways earns both.
    closed = text_of(
        called(project(tmp_path), "add", block="A", symptom="s", why="w.", ref="4.2")
    )
    assert "no such argument" not in closed
    # A name nothing declares still reads the way it always did.
    absent = text_of(
        called(project(tmp_path), "add", block="A", symptom="s", why="w.", deeps=["RK1"])
    )
    assert "no such argument deeps" in absent
    assert "closed by this project's config" not in absent
    # And mixed, each clause over its own names — never one verdict covering both.
    mixed = text_of(
        called(project(tmp_path), "add", block="A", symptom="s", why="w.",
               ref="4.2", deeps=["RK1"])
    )
    assert "no such argument deeps" in mixed
    assert "ref is declared by the CLI and closed by this project's config" in mixed
    assert "no such argument deeps, ref" not in mixed


def test_a_conditional_field_carries_its_reason_with_its_predicate():
    # RK251 needed a fallback because the predicate and the sentence were two tables that could
    # disagree, and the miss surfaced only on the path composing the refusal — for the caller who
    # most needed it. RK252 made them one record, so half of that is now unrepresentable.
    declared = {dest for tool in TOOLS for dest in tool.conditional}
    assert declared, "the assertion is about a set the surface still has"
    assert declared <= set(_CONDITIONAL), "a field with no record cannot be opened"
    for dest in declared:
        opened = _CONDITIONAL[dest]
        assert isinstance(opened, Conditional)
        # The sentence reads after `<dest>: `, so it is prose and not a name the caller retries.
        assert opened.because and opened.because[0].islower()
        assert callable(opened.opens)


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


def test_listing_the_tools_builds_the_parser_once(monkeypatch):
    # RK174: reaching one subcommand builds the whole CLI, and every descriptor wanted two
    # lookups — the schema and the read-only hint — so the first message a client sends paid
    # 58 builds and 195 ms for a parser that is a pure function of the code.
    builds = 0
    original = cli.build_parser

    def counted():
        nonlocal builds
        builds += 1
        return original()

    monkeypatch.setattr(cli, "build_parser", counted)
    serving._root.cache_clear()
    assert len(descriptors(Config.default())) == len(TOOLS)
    assert builds == 1
    # And nothing after it: what stopped a mid-session `[ids] suffix` from being described
    # was never the parser, which holds no configured value at all, but the config read that
    # is still per message (RK202) — asserted below rather than argued here.
    descriptors(Config.default())
    assert builds == 1


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
        "block_merge",
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
        # The correction the other two bullet grammars had and this one did not (RK368).
        "non_goal_amend",
        "non_goal_drop",
        "priority_add",
        "priority_drop",
        "section_add",
        "section_amend",
        # The address `renumber` cannot reach under an outline (RK377), beside the two
        # writes that reach everything else about a section.
        "section_move",
        "section_drop",
        # `brief --claim` moves a marker, so the tool that always passes it says so — and
        # `brief` and `pick` stay read-only *because* it is a separate tool (RK150), which is
        # the same reason `lint` is read-only: the writing flag is not reachable from it.
        "claim",
        # `claim --path` and `--add-path` are both writes (RK307, RK308), and both are exposed,
        # so this tool writes whichever one a call passes. The read half of that command is not
        # served: `ship` prints the scope it releases at the moment it is wanted (RK298).
        "scope",
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
    # `listChanged` is declared because the schema varies by config and this server now
    # sends the notification (RK177): a client never told the list can change is entitled
    # to ignore one saying it did.
    assert response["result"]["capabilities"] == {"tools": {"listChanged": True}}
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
    """The argvs worth trying: the minimum, plus every shape a `Prose` calls a pipe read.

    Plural since RK329, `add` declaring two: the section body and the `why`. A loop over
    one of them would have left the other's shapes untried, which is the gap RK171 closed
    for commands and this closes for arguments.
    """
    base = _minimal(tool)
    out = [dict(base)]
    for prose in prose_of(tool.command):
        if prose.dest not in tool.exposes:
            continue
        omitted = {name: value for name, value in base.items() if name != prose.dest}
        if prose.gated_by:
            omitted[prose.gated_by] = "A design"
        out += [omitted, {**base, prose.dest: prose.sentinel}]
    return out


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
        declared = prose_of(tool.command)
        for arguments in _variants(tool):
            reaches = any(
                prose.dest in tool.exposes and prose.reached_by(arguments)
                for prose in declared
            )
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


def test_the_paths_that_could_reach_it_are_the_ones_declared():
    # The inventory §RK171 says neither file stated, now derived from the parsers — and one
    # `--why` per prose-writing verb since RK329, because the field a shell most reliably
    # eats is the sentence and not the paragraph.
    reaching = {tool.name for tool in TOOLS if prose_of(tool.command)}
    assert reaching == {
        "add",
        "amend",
        "ship",
        "record_add",
        "record_amend",
        "non_goal_add",
        "non_goal_amend",
        "retire",
        "defer",
        "section_add",
        "section_amend",
    }
    # `pick` is the asymmetry that makes it a real question: it writes no prose at all, so
    # it cannot reach the read however it is called.
    assert prose_of("pick") == ()


def test_each_declaration_says_which_argv_goes_to_the_pipe():
    # Three commands, three different answers, which is why one comment in one handler was not
    # the statement of it: `add` is gated on a section being named, `section add` reads on a
    # plain omission, and `section amend` only on the `-` it documents.
    assert prose_of("add") == (
        Prose(dest="section_body", gated_by="section"),
        Prose(dest="why", omitted=False),
    )
    assert prose_of("section add") == (Prose(dest="body"),)
    assert prose_of("section amend") == (Prose(dest="body", omitted=False),)
    body, why = prose_of("add")
    # An `add` naming no section must never block on a pipe — the comment that was the guard.
    assert not body.reached_by({"block": "A", "symptom": "s", "why": "w."})
    assert body.reached_by({"section": "A design"})
    # And the `why` is ungated and sentinel-only (RK329): omitting a required argument is
    # argparse's refusal, so only an outright `-` is the caller asking for the pipe.
    assert why.reached_by({"why": "-"})
    assert not why.reached_by({"why": "A reason."})
    assert not prose_of("section amend")[0].reached_by({"title": "A new heading"})
    assert prose_of("section amend")[0].reached_by({"body": "-"})


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


# -- one name, two acts, and the one an agent could not reach (RK308) -----------


def test_the_scope_a_commit_owns_can_be_declared_over_the_protocol(tmp_path, monkeypatch):
    # RK150's own sentence, applied to the whole of RK280: a flag only the CLI can reach is a
    # flag the agent this ships for cannot pass. The `claim` tool is `brief --claim` and takes a
    # line; the verb that says which paths the commit owns was exposed nowhere.
    monkeypatch.setattr(claiming, "path", lambda root: tmp_path / "claims.json")
    where = project(tmp_path)
    assert called(where, "claim", id="RK1")["isError"] is False  # take the line first
    declared = called(where, "scope", id="RK1", path=["src/a.py", "src/b.py"])
    assert declared["isError"] is False
    assert json.loads(text_of(declared))["paths"] == ["src/a.py", "src/b.py"]


def test_a_path_the_work_turned_up_is_one_argument_and_not_the_whole_scope_again(
    tmp_path, monkeypatch
):
    # Both writing flags travel (RK307): `--path` replaces the scope and `--add-path` extends it,
    # and a surface offering only the first would make every correction a full restatement.
    monkeypatch.setattr(claiming, "path", lambda root: tmp_path / "claims.json")
    where = project(tmp_path)
    called(where, "claim", id="RK1")
    called(where, "scope", id="RK1", path=["src/a.py"])
    extended = called(where, "scope", id="RK1", add_path=["tests/test_a.py"])
    assert json.loads(text_of(extended))["paths"] == ["src/a.py", "tests/test_a.py"]


def test_the_tool_that_declares_a_scope_is_not_the_tool_that_takes_the_line(tmp_path):
    # Two acts under one word, which is why this stayed invisible: `named=` is what tells them
    # apart, and the collision is the argument for using it rather than against exposing this.
    served = listed(project(tmp_path))
    assert served["claim"]["inputSchema"]["properties"].keys() == {"id", "block", "designed"}
    assert served["scope"]["inputSchema"]["properties"].keys() == {"id", "path", "add_path"}
    # Both write, and neither claims to be free to ask.
    assert served["scope"]["annotations"]["readOnlyHint"] is False
    # The read half is not served: `ship` prints the scope it releases (RK298), so a second
    # answer here would be about a `git status` in whichever tree happened to answer.
    assert "porcelain" not in served["scope"]["inputSchema"]["properties"]


# -- the dest the enum missed (RK314) -------------------------------------------


def test_the_tool_that_writes_a_marker_publishes_the_set_the_one_that_prices_one_did(tmp_path):
    # RK304 published `role` and its own line asserted `status` already published its markers.
    # Measured after that shipped: `budget --status` is dest `status`, which the table keyed on,
    # and the `status` command's positional is dest `marker`, which nothing keyed on — so the
    # enum reached the tool that prices a line and missed the tool that writes one.
    served = listed(project(tmp_path))
    open_set = ["📋", "💭", "⏳", "🛠"]
    for name in ("status", "resume", "budget", "add"):
        published = served[name]["inputSchema"]["properties"]
        dest = "marker" if "marker" in published else "status"
        assert published[dest]["enum"] == open_set, name
    # The roadmap's set and not the ledger's: `status RK1 ✅` is refused as `status.shipped`, so
    # the shipped marker is not a value any of these may carry.
    assert "✅" not in served["status"]["inputSchema"]["properties"]["marker"]["enum"]


def test_the_filter_that_reads_any_governed_file_offers_every_marker_one_can_carry(tmp_path):
    # `list --marker` is checked against `schema_for(--role)`, and the changelog declares `✅ 🗑`
    # where the roadmap declares the open four. A schema cannot make one enum depend on another
    # field, so the union is published — and the direction is the one rule that binds.
    offered = listed(project(tmp_path))["list"]["inputSchema"]["properties"]["marker"]["enum"]
    assert offered == ["📋", "💭", "⏳", "🛠", "✅", "🗑"]
    # The call a narrow enum would have refused on the client, which the tool accepts.
    answered = called(project(tmp_path), "list", role="changelog", marker="✅")
    assert answered["isError"] is False


def test_the_marker_the_union_admits_for_another_role_is_still_refused_beneath(tmp_path):
    # Over-permissive by exactly the markers legal on a role the call did not name, and every one
    # of those is refused by the read beneath with the set that role does declare.
    answered = called(project(tmp_path), "list", role="roadmap", marker="🗑")
    assert answered["isError"] is True
    assert "is not a marker this project declares" in text_of(answered)


# -- the bound that stayed prose (RK304) ----------------------------------------


def test_the_prose_role_is_published_as_the_files_this_project_declares(tmp_path):
    # RK24's claim is that the input schema *is* the format's schema, and `role` was the closed
    # set that published a sentence: four tools described it as "which prose file" and gave the
    # client nothing to validate, so `role = "notes"` was refused after the call.
    served = listed(project(tmp_path, config=PROSE, improvements=DESIGN))
    for name in ("section_add", "section_amend", "section_drop", "budget"):
        assert served[name]["inputSchema"]["properties"]["role"]["enum"] == ["improvements"]
    # `strategy` is a prose role this project declares no file for, so it is not offered: the
    # same narrowing every other reader of this question makes (RK259).
    assert "strategy" not in served["section_add"]["inputSchema"]["properties"]["role"]["enum"]


def test_the_read_that_means_any_governed_file_is_not_narrowed_to_the_prose_ones(tmp_path):
    # `list --role` is *which governed file* and defaults to `roadmap`, so an enum of the prose
    # files would refuse the most common call this surface makes.
    served = listed(project(tmp_path, config=PROSE, improvements=DESIGN))
    offered = served["list"]["inputSchema"]["properties"]["role"]["enum"]
    assert offered == ["roadmap", "changelog", "improvements"]


def test_a_project_with_no_prose_file_publishes_no_enum_rather_than_an_empty_one(tmp_path):
    # `"enum": []` is a keyword no value satisfies, so a client holding it could not make the
    # call that earns the refusal explaining why — which is the one useful thing left to say.
    served = listed(project(tmp_path))  # CONFIG declares roadmap and changelog only
    assert "enum" not in served["section_add"]["inputSchema"]["properties"]["role"]
    # And the field is still there, describing itself as the CLI does.
    assert "prose file" in served["section_add"]["inputSchema"]["properties"]["role"]["description"]


def test_the_role_the_enum_withholds_is_still_the_one_the_write_path_refuses(tmp_path):
    # Nothing is checked on this surface: every role the enum narrows away is one `Config.path`
    # already refuses by name, and a check here would be a second spelling of that refusal.
    answered = called(
        project(tmp_path, config=PROSE, improvements=DESIGN),
        "section_add",
        anchor="RK1",
        title="A design",
        body="Because a pointer resolving to nothing reads like a design that exists.",
        role="notes",
    )
    assert answered["isError"] is True
    assert "declares no 'notes' file" in text_of(answered)


# -- the check the agent it was built for could not call (RK275) ----------------


def test_the_driver_check_is_a_tool_and_the_driver_itself_is_not(tmp_path):
    # L5 is that every question is a command. `merge --check` is exactly that shape and was the
    # one query off this surface, so the agent the plugin exists for reached it by shelling out
    # or — in practice, nothing prompting the question — not at all.
    served = listed(project(tmp_path))
    assert "merge_check" in served
    # The verb around it stays off: three positional paths and an exit code git reads is git's
    # contract, and none of it belongs in a tool an agent calls.
    assert "merge" not in served
    # Free to ask, which is the whole of L5 — and read off the parser, not written here.
    assert served["merge_check"]["annotations"]["readOnlyHint"] is True
    # It takes nothing: the flag *is* the tool, so there is no argument to get wrong.
    assert served["merge_check"]["inputSchema"]["properties"] == {}
    # And it says which flag it always passes, derived from that flag's own help (RK150).
    assert "--check" in served["merge_check"]["description"]


def test_the_check_answers_the_two_halves_as_fields_and_not_as_prose(tmp_path):
    # A caller handed one string would have to parse which half is broken out of prose the CLI
    # is free to reword — and the halves are two because they go missing for different reasons.
    answered = called(project(tmp_path), "merge_check")
    reported = json.loads(text_of(answered))
    assert set(reported) == {"attributes", "driver", "sound", "fix"}
    # An unregistered project: nothing is wired, so the check is the refusal it exists to be.
    assert reported["sound"] is False
    assert answered["isError"] is True
    # `sound` is the exit code as a boolean, so nothing infers it from an empty `fix`.
    assert reported["fix"]


def test_the_check_takes_no_write_lock_because_it_writes_nothing(tmp_path):
    # The claim `writes_when` was built for, inverted the only way it can be: the command reads,
    # and the two arguments that make it a write say so.
    parser = build_parser()
    parsed = parser.parse_args(["-C", str(tmp_path), "merge", "--check"])
    assert cli._only_reads(parsed) is True
    # The driver path writes into `ours`, which is where git has it put the result.
    driving = parser.parse_args(["-C", str(tmp_path), "merge", "a", "b", "c"])
    assert cli._only_reads(driving) is False
    registering = parser.parse_args(["-C", str(tmp_path), "merge", "--register"])
    assert cli._only_reads(registering) is False


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
    assert f"{DECIDES} decided this refusal and changed on disk" in refused
    assert "restarting the session is the only remedy" in refused


def test_the_remedy_named_is_the_one_that_restarts_this_server(tmp_path, monkeypatch):
    # RK246: a patch bump reloads a *plugin*, and the tree the note fires in most is the one
    # wired by `.mcp.json` to `scripts/roadkeep.py`, which carries no version — measured here
    # at five bumps in one session with the note still naming the bump as the fix.
    monkeypatch.setattr(
        "roadkeep.serving.engine",
        lambda: replace(engine(), home=_moved(tmp_path)),
    )
    # The package under the governed root: this process runs the checkout it is governing.
    own = text_of(called(project(tmp_path), "status", id="RK99", marker="🛠"))
    assert "inside the tree it is governing" in own and "RK153" not in own
    # And it claims no more than the relation established (RK250): the launcher was never read,
    # so naming one would be true of this repository and of nothing else satisfying the same
    # relation — a `pip install -e .` into a `.venv` under the root satisfies it too. Asserted
    # against the *remedy* clause and not the whole answer, because the clause after it names a
    # command `invocation()` resolved on this machine rather than a wiring it assumed (RK254,
    # RK313) — and on a machine with the console script that is `roadkeep`, not a launcher path.
    remedy = own.split("Available now")[0]
    assert ".mcp.json" not in remedy and "scripts/roadkeep.py" not in remedy
    # And the plugin's own copy, which is a cache *outside* the governed root: the bump applies.
    monkeypatch.setattr(
        "roadkeep.serving.engine",
        lambda: replace(engine(), home=_moved(tmp_path.parent / f"{tmp_path.name}-cache")),
    )
    cached = text_of(called(project(tmp_path), "status", id="RK99", marker="🛠"))
    assert "bumps the patch version" in cached and "RK153" in cached


def test_the_wiring_is_read_from_the_project_root_and_not_the_launch_path(tmp_path, monkeypatch):
    # RK248: `Config.discover` walks up, so a server started in `docs/` has a root above its
    # `-C` — and reading the launch path there put the package outside it and named the bump on
    # the one tree RK246 measured the bump never reaching.
    monkeypatch.setattr(
        "roadkeep.serving.engine",
        lambda: replace(engine(), home=_moved(tmp_path)),
    )
    below = project(tmp_path) / "docs"
    assert below.is_dir()  # the subdirectory is real, so this is the walk and not a fallback
    refused = text_of(called(below, "status", id="RK99", marker="🛠"))
    assert "inside the tree it is governing" in refused


def test_the_drift_is_a_fact_beside_the_refusal_and_not_a_doubt_about_it(tmp_path, monkeypatch):
    # RK242: the note cannot know whether the files that moved reach the verb that refused, so
    # a sentence calling the refusal a possible build artefact doubted every refusal alike —
    # and the measured cost was calls spent disproving a constraint that was right.
    monkeypatch.setattr(
        "roadkeep.serving.engine",
        lambda: replace(engine(), home=_moved(tmp_path)),
    )
    refused = text_of(called(project(tmp_path), "status", id="RK99", marker="🛠"))
    # The refusal is first and is the answer, not a candidate for one.
    assert refused.index("RK99") < refused.index("Separately")
    assert "may be a build behind" not in refused
    assert "not about the refusal above" in refused
    assert "read it first" in refused


def test_a_module_that_could_not_have_decided_it_earns_no_note_at_all(tmp_path, monkeypatch):
    # RK267, the measured case: a `why.too-long` decided by `schema.py`, unchanged, arrived
    # naming `cli.py`, `merging.py` and `provenance.py` — 450 characters of correct and
    # irrelevant text, on every error in every session that edits this package.
    monkeypatch.setattr(
        "roadkeep.serving.engine",
        lambda: replace(engine(), home=_moved(tmp_path, "merging.py", "linting.py")),
    )
    answered = called(project(tmp_path), "status", id="RK99", marker="🛠")
    # Still a refusal, and still the whole answer: nothing was suppressed except the note.
    assert answered["isError"] is True
    refused = text_of(answered)
    assert "RK99" in refused
    assert "Separately" not in refused and "changed on disk" not in refused


def test_the_modules_that_moved_and_did_not_decide_stay_behind_the_one_that_did(tmp_path, monkeypatch):
    # The miss §RK267 accepts is a helper whose frame has already returned, so the others are
    # kept rather than dropped — behind the module that is named, never instead of it.
    monkeypatch.setattr(
        "roadkeep.serving.engine",
        lambda: replace(engine(), home=_moved(tmp_path, DECIDES, "merging.py")),
    )
    refused = text_of(called(project(tmp_path), "status", id="RK99", marker="🛠"))
    assert f"{DECIDES} decided this refusal" in refused
    assert "merging.py also changed and did not." in refused
    # And the judgement leads: the relevance question is answered here, not handed back.
    assert refused.index(DECIDES) < refused.index("merging.py")
    assert "re-run only where the changed files" not in refused


def test_a_refusal_this_process_did_not_witness_still_gets_the_full_list(tmp_path, monkeypatch):
    # Suppressing on no evidence is the opposite mistake. argparse refusing an argv exits without
    # raising through this package, so nothing decided it *here* and relevance is unknown.
    monkeypatch.setattr(
        "roadkeep.serving.engine",
        lambda: replace(engine(), home=_moved(tmp_path, "merging.py")),
    )
    # A tool whose required argument is missing: `SystemExit` from the parser, never `_refused`.
    answered = called(project(tmp_path), "status", id="RK1")
    assert answered["isError"] is True
    refused = text_of(answered)
    assert "imported roadkeep before merging.py changed on disk" in refused
    # What it may not do is ask the reader to establish the relevance it could not.
    assert "re-run only where the changed files" not in refused


def test_the_note_is_never_composed_from_an_earlier_call_refusal(tmp_path, monkeypatch):
    # The slot is one call's out-parameter, so it is cleared where the call begins: a refusal
    # witnessed by the call before would otherwise name a module this one never executed.
    monkeypatch.setattr(
        "roadkeep.serving.engine",
        lambda: replace(engine(), home=_moved(tmp_path, DECIDES)),
    )
    where = project(tmp_path)
    assert called(where, "status", id="RK99", marker="🛠")["isError"] is True
    # Now a refusal the parser raises, which witnesses nothing: the note must fall back to the
    # inventory rather than reuse the module the previous call recorded.
    refused = text_of(called(where, "status", id="RK1"))
    assert f"imported roadkeep before {DECIDES} changed on disk" in refused
    assert "decided this refusal" not in refused


def test_the_note_closes_with_the_one_remedy_the_reader_can_run(tmp_path, monkeypatch):
    # RK313: every remedy this note named was a patch bump or a session restart, and the agent it
    # is written for can perform neither — measured as one session abandoning the protocol surface
    # and driving the CLI for all thirteen of its filings.
    monkeypatch.setattr(
        "roadkeep.serving.engine",
        lambda: replace(engine(), home=_moved(tmp_path, DECIDES)),
    )
    refused = text_of(called(project(tmp_path), "status", id="RK99", marker="🛠"))
    # The verb, spelled as this machine reaches it (RK254) — never `roadkeep` literally, which
    # answers `command not found` wherever the console script was never installed.
    assert f"`{invocation()} status` runs the changed files" in refused
    # And after the remedy, not instead of it: the restart is still the cause's own answer.
    assert refused.index("remedy") < refused.index("Available now")


def test_the_verb_named_is_the_one_this_call_asked_for(tmp_path, monkeypatch):
    # The verb and never the arguments: the reader has those, and a rendered argv would have to
    # quote a `--why` sentence to be correct — a second grammar for a call this surface takes
    # as JSON. So a refusal from a different tool names that tool.
    monkeypatch.setattr(
        "roadkeep.serving.engine",
        lambda: replace(engine(), home=_moved(tmp_path, "authoring.py", "schema.py")),
    )
    refused = text_of(
        called(project(tmp_path), "add", block="A", symptom="s", why="w" * 5000)
    )
    assert f"`{invocation()} add` runs the changed files" in refused
    assert "--why" not in refused.split("Available now")[1]


def test_the_command_offered_is_the_act_and_not_the_verb_under_it(tmp_path, monkeypatch):
    # RK318: the sentence spelled `tool.command`, and RK150's mechanism is that a tool may *be* a
    # flag on a command — so `claim` is `brief --claim` and the note advised `brief`, which
    # succeeds, prints a briefing and takes no line. Worse than an error: the write the caller
    # asked for silently does not happen.
    monkeypatch.setattr(claiming, "path", lambda root: tmp_path / "claims.json")
    monkeypatch.setattr(
        "roadkeep.serving.engine",
        lambda: replace(engine(), home=_moved(tmp_path, "picking.py", "briefing.py")),
    )
    refused = text_of(called(project(tmp_path), "claim", id="RK99"))
    assert f"`{invocation()} brief --claim` runs the changed files" in refused
    # And never the verb alone, which is the read this tool was split off from.
    assert f"`{invocation()} brief` runs" not in refused


def test_the_act_is_resolved_through_the_parser_for_every_tool_that_is_a_flag(tmp_path):
    # Read by dest and through the parser, exactly as `argv` resolves the same flags, so a rename
    # in `cli.py` cannot leave this sentence naming something that is gone.
    assert serving._spelled(tool_named("merge_check")) == "merge --check"
    assert serving._spelled(tool_named("claim")) == "brief --claim"
    # `scope` is the real `claim` command and has no always flag, which is why it was already
    # right — asserted so that a flag added to it does not silently go unnamed.
    assert serving._spelled(tool_named("scope")) == "claim"
    for tool in TOOLS:
        spelled = serving._spelled(tool)
        assert spelled.startswith(tool.command)
        # Every always dest renders as its option string alone, so there is no value to quote.
        assert len(spelled.split()) == len(tool.argv_head) + len(tool.always)


def test_the_table_answers_for_a_name_the_parser_does_not_know(tmp_path):
    """RK353: the same act, named for the surface the reader is not on. The tool table is the
    authority — it is what publishes the other spelling — so the answer comes from here."""
    assert serving.spelled("scope") == "claim"
    assert serving.spelled("merge_check") == "merge --check"
    assert serving.spelled("section_add") == "section add"
    # A name nothing publishes is a typo, and a typo told about a tool is a second wrong turn.
    assert serving.spelled("nonsense") is None


def test_a_name_pasted_out_of_a_tool_list_arrives_with_its_prefix(tmp_path):
    # Both prefixes, which is RK333 one surface along: a session reads the qualified name off
    # its own tool list, and a refusal that only knew the bare form is the same defect.
    assert serving.spelled("mcp__roadkeep__scope") == "claim"
    assert serving.spelled("mcp__plugin_roadkeep_roadkeep__scope") == "claim"


def test_a_refusal_with_no_drift_offers_nothing_because_a_re_run_answers_the_same(tmp_path):
    # The advice is not circular, which is RK272's bar: it is offered only where the drift is a
    # fact about this process, so a fresh import is the one place a different answer comes from.
    answered = called(project(tmp_path), "status", id="RK99", marker="🛠")
    assert answered["isError"] is True
    assert "Available now" not in text_of(answered)


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


#: The module that decides the refusal these tests provoke — `status` on an id no line carries,
#: which `authoring.py` raises out of. Named because the note now fires on the intersection of
#: what moved and what decided (RK267), so a fabricated engine has to move a module that did.
DECIDES = "authoring.py"


def _moved(tmp_path: Path, *args: str) -> Path:
    """A package directory whose named modules are newer than this process's import of them.

    Defaults to the module that decides the refusal under test, because a `_moved` naming an
    uninvolved file is the disjoint case and says nothing at all (RK267) — which is a thing to
    assert deliberately, never the accident of a helper's default.
    """
    home = tmp_path / "engine" / "roadkeep"
    home.mkdir(parents=True, exist_ok=True)
    for name in args or (DECIDES,):
        (home / name).write_text("x = 1\n", encoding="utf-8")
        os.utime(home / name, (since_import(300), since_import(300)))
    return home


# -- the list that changed under the client (RK177) ---------------------------


def _messages(tmp_path: Path, *sent: dict, between=None) -> list[dict]:
    """Drive the real loop, optionally editing the config between the two messages.

    Through :func:`serve` and not through `handle`, because the notification is the loop's
    to write: `handle` answers one message and the whole point here is the second one.
    """
    written: list[dict] = []
    reader = _Edited(sent, tmp_path, between)
    writer = io.StringIO()
    assert serve(reader, writer, str(tmp_path)) == 0
    for line in writer.getvalue().splitlines():
        if line.strip():
            written.append(json.loads(line))
    return written


class _Edited(io.StringIO):
    """The client's pipe, with a side effect between the first message and the second.

    A `StringIO` holding both lines would be read before the edit happened, and the defect
    is precisely that the config moves *while* a session is open.
    """

    def __init__(self, sent, tmp_path: Path, between) -> None:
        super().__init__()
        self._sent = [json.dumps(message) + "\n" for message in sent]
        self._tmp_path = tmp_path
        self._between = between
        self._read = 0

    def __iter__(self):
        for line in self._sent:
            yield line
            self._read += 1
            if self._read == 1 and self._between is not None:
                self._between(self._tmp_path)


def _lists(identifier: int = 1) -> dict:
    return {"jsonrpc": "2.0", "id": identifier, "method": "tools/list"}


def _declare_a_suffix(tmp_path: Path) -> None:
    # The exact edit RK111 opened `add`'s id for: on this config `task_id` exists, and on
    # the one the client cached it does not.
    (tmp_path / "roadkeep.toml").write_text(SUFFIXED, encoding="utf-8")


def _pings(identifier: int) -> dict:
    return {"jsonrpc": "2.0", "id": identifier, "method": "ping"}


def test_a_config_that_gains_a_field_mid_session_is_announced(tmp_path):
    # The shape of a real session: a client lists once at the handshake and then only calls.
    # Between those, `[ids] suffix` appears and `add` gains an argument the client has no
    # schema for — which is the call it refuses on this server's behalf.
    project(tmp_path, config=PROSE, improvements=DESIGN)
    written = _messages(tmp_path, _lists(1), _pings(2), between=_declare_a_suffix)
    assert [m.get("id", m.get("method")) for m in written] == [
        1,
        2,
        "notifications/tools/list_changed",
    ]
    first = {tool["name"]: tool for tool in written[0]["result"]["tools"]}
    assert "task_id" not in first["add"]["inputSchema"]["properties"]


def test_the_field_is_there_when_the_client_asks_again(tmp_path):
    # The notification is only worth sending if the answer behind it differs, so the answer
    # is asserted rather than assumed: a re-list carries the argument the cached one lacked.
    project(tmp_path, config=PROSE, improvements=DESIGN)
    written = _messages(tmp_path, _lists(1), _pings(2), _lists(3), between=_declare_a_suffix)
    third = {tool["name"]: tool for tool in written[-1]["result"]["tools"]}
    assert "task_id" in third["add"]["inputSchema"]["properties"]


def test_the_notification_arrives_after_the_answer_it_follows(tmp_path):
    # A notification written first would sit in front of the response the client is blocked
    # on, which turns a staleness fix into a stall.
    project(tmp_path, config=PROSE, improvements=DESIGN)
    written = _messages(tmp_path, _lists(1), _pings(2), between=_declare_a_suffix)
    assert written[1]["id"] == 2
    assert written[2]["method"] == "notifications/tools/list_changed"


def test_a_session_that_never_listed_is_never_told(tmp_path):
    # Nothing was cached, so there is nothing to correct — and the descriptors are never
    # built, which is the cost this is arranged to avoid paying per message.
    project(tmp_path, config=PROSE, improvements=DESIGN)
    written = _messages(tmp_path, _pings(1), _pings(2), between=_declare_a_suffix)
    assert [m["id"] for m in written] == [1, 2]


def test_a_config_that_did_not_move_says_nothing(tmp_path):
    project(tmp_path, config=PROSE, improvements=DESIGN)
    written = _messages(tmp_path, _lists(1), _pings(2), _pings(3))
    assert [m["id"] for m in written] == [1, 2, 3]


def test_an_edit_that_leaves_the_schema_alone_says_nothing(tmp_path):
    # A comment added, a `[report]` line changed: the file moved and the tools did not, so
    # a client that re-listed would be handed exactly what it already has.
    project(tmp_path, config=PROSE, improvements=DESIGN)

    def comment(root: Path) -> None:
        (root / "roadkeep.toml").write_text(
            PROSE + "\n# a sentence about nothing the schema reads\n", encoding="utf-8"
        )

    written = _messages(tmp_path, _lists(1), _pings(2), between=comment)
    assert [m["id"] for m in written] == [1, 2]


def test_one_edit_is_announced_once(tmp_path):
    # A client that ignores the notification is not told again about the same edit, which
    # is what keeps this from becoming a message on every message.
    project(tmp_path, config=PROSE, improvements=DESIGN)
    written = _messages(tmp_path, _lists(1), _pings(2), _pings(3), between=_declare_a_suffix)
    assert sum("method" in m for m in written) == 1


def test_the_watch_holds_nothing_about_the_project(tmp_path):
    # The claim the module docstring makes, asserted: a digest of what was *sent*, a stat of
    # the config, and a flag. No task, no path, no file contents.
    project(tmp_path, config=PROSE, improvements=DESIGN)
    watch = Watch()
    handle(_lists(1), str(tmp_path), watch)
    assert set(vars(watch)) == {"described", "stamp", "told"}
    assert watch.told is True
    assert watch.stamp[0].endswith("roadkeep.toml")


def test_the_capability_is_declared_wherever_the_notification_can_be_sent():
    # A client never told the list can change may ignore one that says it did, so the two
    # halves are asserted together rather than in two files that can drift.
    handshake = handle({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
    assert handshake["result"]["capabilities"]["tools"]["listChanged"] is True


# -- one parser, per call and then per process (RK198, RK202) ----------------


def _builds(monkeypatch) -> list[int]:
    """A counter on `build_parser`, which is the only thing the cost is made of.

    The cache is cleared first: it lives for the process, and a test asking "how many builds
    does this call make" is asking about a cold one.
    """
    counted = [0]
    real = cli.build_parser

    def build():
        counted[0] += 1
        return real()

    monkeypatch.setattr(cli, "build_parser", build)
    serving._root.cache_clear()
    return counted


@pytest.mark.parametrize(
    "name, arguments",
    [("list", {"block": "A"}), ("brief", {}), ("add", {"block": "A"})],
)
def test_a_tool_call_builds_the_parser_once(tmp_path, monkeypatch, name, arguments):
    # Three, before RK198: `argv` resolved the subcommand for the actions, `_companioned`
    # resolved it again through `prose_of`, and `call` built a third to parse the argv it
    # had just rendered. Reaching one subcommand builds the whole CLI, so each cost the lot.
    project(tmp_path, config=PROSE, improvements=DESIGN)
    counted = _builds(monkeypatch)
    call(tool_named(name), arguments, str(tmp_path))
    assert counted[0] == 1


def test_a_second_call_builds_nothing(tmp_path, monkeypatch):
    # RK202's own claim: the parser is a pure function of `cli.py`, so a session making
    # twenty writes builds it once and not twenty times.
    project(tmp_path, config=PROSE, improvements=DESIGN)
    counted = _builds(monkeypatch)
    for _ in range(5):
        call(tool_named("list"), {"block": "A"}, str(tmp_path))
    descriptors(Config.discover(tmp_path))
    assert counted[0] == 1


def test_the_parser_holds_nothing_the_config_declares(tmp_path, monkeypatch):
    """Why holding one is safe, counted rather than argued (RK202).

    `_parsers` used to say a cached parser would stop a mid-session config edit from being
    described. Two builds under two different `roadkeep.toml` files are identical action for
    action — every configured value reaches a descriptor through `_BOUNDS`, off a config
    this server re-reads per message.
    """
    def shape(parser):
        return [
            (path, action.dest, action.help, tuple(action.option_strings), repr(action.default))
            for path, sub in sorted(serving._parsers(parser).items())
            for action in sub._actions  # noqa: SLF001 - argparse exposes no public reader
        ]

    monkeypatch.chdir(project(tmp_path, config=PROSE, improvements=DESIGN))
    lean = shape(cli.build_parser())
    (tmp_path / "roadkeep.toml").write_text(SUFFIXED + "[limits]\nwhy = 400\n", encoding="utf-8")
    assert shape(cli.build_parser()) == lean


def test_a_shared_parser_is_not_changed_by_using_it(tmp_path):
    # The one assumption the cache makes. `parse_args` builds a Namespace and the readers
    # read; if any of them ever wrote to an action, every later call would inherit it.
    root = project(tmp_path, config=PROSE, improvements=DESIGN)
    config = Config.discover(root)
    parser = serving._root()
    before = [(a.dest, repr(a.default), a.required) for a in parser._actions]  # noqa: SLF001
    for _ in range(3):
        parser.parse_args(["-C", str(root), "list", "--json"])
    descriptors(config)
    argv(tool_named("list"), {"block": "A"}, config)
    assert [(a.dest, repr(a.default), a.required) for a in parser._actions] == before  # noqa: SLF001


def test_a_refused_argument_still_builds_the_parser_once(tmp_path, monkeypatch):
    # The refusal path renders no argv and must not be the one that pays twice.
    project(tmp_path, config=PROSE, improvements=DESIGN)
    counted = _builds(monkeypatch)
    answered = call(tool_named("list"), {"blokk": "A"}, str(tmp_path))
    assert answered.is_error and counted[0] == 1


def test_the_whole_tool_list_still_builds_it_once(tmp_path, monkeypatch):
    # RK174's own guarantee, held here because RK198 and RK202 both changed how `_parsers`
    # gets its root.
    counted = _builds(monkeypatch)
    descriptors(Config.discover(project(tmp_path)))
    assert counted[0] == 1


def test_an_index_handed_in_is_the_one_that_is_used(tmp_path, monkeypatch):
    # The threading itself: given an index, nothing on the path reaches for a parser.
    config = Config.discover(project(tmp_path, config=PROSE, improvements=DESIGN))
    parsers = serving._parsers()
    counted = _builds(monkeypatch)
    assert argv(tool_named("list"), {"block": "A"}, config, parsers) == [
        "list",
        "--block",
        "A",
        "--json",
    ]
    assert serving.prose_of("add", parsers) is not None
    assert counted[0] == 0


def test_the_lookups_answer_the_same_with_an_index_and_without(tmp_path):
    # An index is an optimisation and never a second resolver, so both routes agree — which
    # is what keeps `tests/test_serving.py` free to ask about one tool at a time.
    config = Config.discover(project(tmp_path, config=PROSE, improvements=DESIGN))
    parsers = serving._parsers()
    for tool in TOOLS:
        assert serving.prose_of(tool.command, parsers) == serving.prose_of(tool.command)
    assert argv(tool_named("list"), {"block": "A"}, config, parsers) == argv(
        tool_named("list"), {"block": "A"}, config
    )


# -- the argument that needed the pipe is the one that did not have it (RK329) -


def test_a_why_arrives_off_the_pipe_wherever_it_appears(tmp_path, monkeypatch, capsys):
    # A `why` is the field that reliably carries an apostrophe, a backtick, an em dash and a
    # `§` — its sentence names types, files and prior ids — and every one of those is read by
    # a shell before this program sees it. The failure is silent in the bad direction.
    tree = str(project(tmp_path, config=PROSE, improvements=DESIGN))
    sentence = "The `--why` survives now, T293's backtick included.\n"
    monkeypatch.setattr(sys, "stdin", io.StringIO(sentence))
    assert (
        main(["-C", tree, "add", "--block", "A", "--symptom", "A symptom", "--why", "-"])
        == EXIT_OK
    )
    # Read off the rendered line the command printed, which is what reached the file.
    assert "The `--why` survives now, T293's backtick included." in capsys.readouterr().out


def test_the_line_terminator_is_the_pipes_and_the_trailing_space_is_the_authors(tmp_path, monkeypatch):
    # `echo`, `printf` and every heredoc end with one, so `why.whitespace` firing on it would
    # make the affordance unusable by the tools that reach for it — the refusal correct about
    # the bytes and wrong about who wrote them. A trailing *space* is still refused.
    tree = str(project(tmp_path, config=PROSE, improvements=DESIGN))
    monkeypatch.setattr(sys, "stdin", io.StringIO("A reason. \n"))
    assert (
        main(["-C", tree, "add", "--block", "A", "--symptom", "A symptom", "--why", "-"])
        == EXIT_USAGE
    )


def test_two_arguments_cannot_split_one_pipe(tmp_path, monkeypatch, capsys):
    # A body that silently absorbed the sentence meant for the line would be the quiet
    # corruption this whole task is about, one layer further in.
    tree = str(project(tmp_path, config=PROSE, improvements=DESIGN))
    monkeypatch.setattr(sys, "stdin", io.StringIO("prose"))
    assert (
        main(
            [
                "-C", tree, "add", "--block", "A", "--symptom", "A symptom",
                "--why", "-", "--section", "A design",
            ]
        )
        == EXIT_USAGE
    )
    err = capsys.readouterr().err
    assert "--why and --section-body both read stdin" in err


def test_every_verb_that_takes_prose_declares_the_pipe(tmp_path):
    # A caller who learns the convention on one verb reaches for it on the next, so the
    # inventory is the claim rather than the five the design happened to list.
    for command, dest in (
        ("add", "why"),
        ("amend", "why"),
        ("ship", "why"),
        ("record add", "why"),
        ("record amend", "why"),
        ("non-goal add", "why"),
        ("retire", "reason"),
        ("defer", "reason"),
    ):
        assert dest in {one.dest for one in prose_of(command)}, command
