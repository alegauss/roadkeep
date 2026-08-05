"""The four slash commands, and the line they are not allowed to cross (RK25).

The MCP tools (RK24) are for the caller who reads a JSON Schema. A person driving the same
standard reads `/help`, so the same four operations exist as `/roadkeep:add`, `/roadkeep:ship`,
`/roadkeep:pick` and `/roadkeep:lint` — one engine, three front doors.

A command file is a *prompt*, which is the one component in this plugin that could break L4:
the tool never writes prose, and a command that told the model to "write a concise symptom"
would have moved the prose generation one file to the left while keeping the law's letter. So
these four are written the other way round — every sentence about the user's words is a
**prohibition**, and the tests below assert the prohibitions rather than trusting a reviewer:

* **The user's words, verbatim.** `/roadkeep:add` passes the fields as typed and asks when one
  is missing. It may not shorten a refused field and retry: that is the analysis the refusal
  exists to hand back to the author, and doing it silently is how a 142-word line happens.
* **Deterministic where it can be.** `ship` and `lint` execute the command in the file with
  `` !` `` `` ` ``, so the output the model reasons about is the tool's own, not a
  recollection of it. `add` cannot — multi-word fields do not survive positional splitting —
  so it calls the MCP tool, where the schema refuses a wrong argument name.
* **Bash is scoped to this tool.** `allowed-tools` names `Bash(roadkeep …:*)` and never bare
  `Bash`: a command that can run anything is a command whose permission prompt teaches
  nothing, and every command line in it is fed to the real parser here.
* **Not declared in the manifest.** `./commands` is scanned by default and the manifest's
  `commands` field *supplements* that default — declaring it would register all four twice.
  This was written as the exception, against `hooks` and `mcpServers` — "single files, and
  declared". Half of it was wrong and the manifest paid: `hooks` is found by convention too,
  and naming it failed the whole plugin. Only `mcpServers` is genuinely the exception.
"""

from __future__ import annotations

import argparse
import json
import re
import shlex
from pathlib import Path

import pytest

from conftest import frontmatter
from roadkeep.cli import build_parser
from roadkeep.serving import TOOLS

HERE = Path(__file__).resolve().parents[1]
COMMANDS = HERE / "commands"
MANIFEST = HERE / ".claude-plugin" / "plugin.json"

#: The four the roadmap names, and the four `TOOLS` exposes — the same operations by design.
EXPECTED = {"add", "ship", "pick", "lint"}

#: A command line as a command file spells one: inside `` !` ` `` for the ones that execute,
#: inside backticks for the ones offered to the user. Both start with the program name, so
#: prose about a flag is never mistaken for a declaration.
_RUNS = re.compile(r"`!?`?\s*(roadkeep [^`]+)`")


def files() -> list[Path]:
    return sorted(COMMANDS.glob("*.md"))


def commands_in(path: Path) -> list[str]:
    return [found.strip() for found in _RUNS.findall(path.read_text(encoding="utf-8"))]


def subcommands() -> set[str]:
    """Every subcommand `cli.py` registers, read off the real parser."""
    return {
        name
        for action in build_parser()._actions
        if isinstance(action, argparse._SubParsersAction)
        for name in action.choices
    }


# -- the four ----------------------------------------------------------------


def test_the_commands_are_the_four_the_roadmap_names():
    assert {path.stem for path in files()} == EXPECTED


def test_the_commands_are_operations_the_tools_also_expose():
    """`/roadkeep:add` and `mcp__roadkeep__add` are one command reached two ways. A slash
    command with no tool behind it would be a second engine; the reverse is fine — RK59
    exposes what a task needs, and only four of those are worth a `/help` entry."""
    assert EXPECTED <= {tool.name for tool in TOOLS}


def test_they_sit_where_the_loader_looks_and_are_not_declared_twice():
    assert COMMANDS.is_dir()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    # `commands` supplements the default `./commands`; declaring it registers each file twice.
    assert "commands" not in manifest
    # And `hooks` is the same rule, which this file stated and the manifest did not follow:
    # `hooks/hooks.json` is loaded by convention too, and the duplicate reference failed the
    # whole plugin rather than registering anything twice (see `tests/test_plugin.py`).
    assert "hooks" not in manifest
    # `mcpServers` is the one that is genuinely outside the convention's reach.
    assert manifest["mcpServers"]


# -- what /help shows --------------------------------------------------------


@pytest.mark.parametrize("path", files(), ids=lambda p: p.stem)
def test_every_command_describes_itself_in_one_line(path):
    description = frontmatter(path)["description"]
    assert description and "\n" not in description
    # `/help` truncates: a description that does not fit is one nobody reads to the end.
    assert len(description) <= 60, len(description)


@pytest.mark.parametrize("path", files(), ids=lambda p: p.stem)
def test_a_command_that_takes_arguments_says_what_they_are(path):
    hint = frontmatter(path).get("argument-hint")
    if path.stem == "lint":
        # It takes none: the gate reads the whole project, and `--fix` is deliberately not
        # offered here (RK16 belongs where a human is standing, in the pre-commit hook).
        assert hint is None
    else:
        assert hint, path.name


# -- one engine --------------------------------------------------------------


@pytest.mark.parametrize("path", files(), ids=lambda p: p.stem)
def test_every_command_line_in_the_file_is_one_the_cli_accepts(path):
    found = commands_in(path)
    assert found, path.name
    for declared in found:
        argv = shlex.split(declared)[1:]
        parsed = build_parser().parse_args(argv)
        assert parsed.command, declared


@pytest.mark.parametrize("path", files(), ids=lambda p: p.stem)
def test_the_command_runs_its_own_subcommand(path):
    """`/roadkeep:ship` runs `ship`. A command that ran something else would be a fifth
    behaviour wearing a familiar name."""
    assert any(
        build_parser().parse_args(shlex.split(line)[1:]).command == path.stem
        for line in commands_in(path)
    )


@pytest.mark.parametrize("path", files(), ids=lambda p: p.stem)
def test_bash_is_scoped_to_this_tool(path):
    allowed = frontmatter(path)["allowed-tools"]
    assert "Bash(" in allowed or "mcp__roadkeep__" in allowed
    for pattern in re.findall(r"Bash\(([^)]*)\)", allowed):
        assert pattern.startswith("roadkeep "), pattern
        # The scoped part names a real subcommand, not one the CLI renamed: a permission
        # scoped to a command that no longer exists silently grants nothing.
        scoped = pattern.removeprefix("roadkeep ").removesuffix(":*").strip()
        assert scoped in subcommands(), scoped
    assert "Bash(*" not in allowed and "allowed-tools: *" not in allowed


@pytest.mark.parametrize("path", files(), ids=lambda p: p.stem)
def test_no_command_grants_a_tool_that_writes_a_governed_file_directly(path):
    """The hook would deny it anyway (RK22); granting it here would make the denial the
    first thing a user of these commands sees."""
    allowed = frontmatter(path)["allowed-tools"]
    for forbidden in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
        assert forbidden not in allowed, forbidden


# -- the line these prompts may not cross (L4) -------------------------------


def test_the_add_command_forbids_writing_the_users_fields():
    body = (COMMANDS / "add.md").read_text(encoding="utf-8")
    assert "verbatim" in body
    assert "never compose one that was not typed" in body
    # The retry is the specific failure: a shortened field that passes is the analysis the
    # refusal handed to the author, done by the model instead and never seen.
    assert "Do not retry with a shortened field." in body


def test_the_add_command_keeps_the_one_rule_no_schema_can_check():
    body = (COMMANDS / "add.md").read_text(encoding="utf-8")
    assert "cannot be falsified" in body


def test_the_lint_command_hands_the_editorial_findings_back():
    body = (COMMANDS / "lint.md").read_text(encoding="utf-8")
    assert "Never rewrite their line for them." in body
    # `--fix` writes, so it is offered and never run unasked — the same split RK16 makes.
    assert "do not run it" in body


def test_no_command_asks_the_model_to_author_a_field():
    banned = ("write a symptom", "write the symptom", "generate a", "compose a symptom")
    for path in files():
        body = path.read_text(encoding="utf-8").lower()
        for phrase in banned:
            assert phrase not in body, f"{path.name}: {phrase}"
