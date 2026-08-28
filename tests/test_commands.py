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
#: A command line as these files spell one (RK1043). The launcher and not the console
#: script: `${CLAUDE_PLUGIN_ROOT}` resolves anywhere it appears in command *content*, and
#: a marketplace install creates no `roadkeep` on PATH (RK254). The `allowed-tools` scope
#: keeps naming the console script, which no substitution reaches — so these prompt, and
#: that was the cost chosen over a `..` in a permission pattern nobody can read.
LAUNCHER = 'python "${CLAUDE_PLUGIN_ROOT}/scripts/roadkeep.py"'
_RUNS = re.compile(rf"`!?`?\s*{re.escape(LAUNCHER)} ([^`]+)`")


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
        parsed = build_parser().parse_args(shlex.split(declared))
        assert parsed.command, declared


@pytest.mark.parametrize("path", files(), ids=lambda p: p.stem)
def test_the_command_runs_its_own_subcommand(path):
    """`/roadkeep:ship` runs `ship`. A command that ran something else would be a fifth
    behaviour wearing a familiar name."""
    assert any(
        build_parser().parse_args(shlex.split(line)).command == path.stem
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


#: A `!` block: what the harness runs **at expansion**, before the model reads a word of the
#: file. The one place in these four files where text reaches a shell.
_EXPANDED = re.compile(r"!`([^`]*)`")


@pytest.mark.parametrize("path", files(), ids=lambda p: p.stem)
def test_nothing_a_shell_expands_carries_a_bare_variable(path):
    """RK1429. `ship.md` ran `… ship $1` — the caller's own text, into a shell, before the
    model reads the instruction that says what to do when the argument is missing. It is the
    only one of these that writes, and three files in one transaction.

    Everywhere else this package puts text near a shell it quotes it — `capturing.offer`
    composes through `shlex.join` — or refuses to read shell at all, which is `guarding`'s
    whole argument. And `${CLAUDE_PLUGIN_ROOT}` was already quoted on the same line.

    What this does not rest on is an exposure. Whether the harness quotes `$1` before the
    shell sees it is a behaviour this repository cannot assert, and that is the argument for
    quoting rather than for relying on it.

    Held by stripping the double-quoted spans and asking whether a `$` survived, so it is
    about *substitution* rather than about a spelling: a variable that is not there is not a
    variable somebody has to remember to quote.
    """
    for block in _EXPANDED.findall(path.read_text(encoding="utf-8")):
        bare = re.sub(r'"[^"]*"', "", block)
        assert "$" not in bare, f"{path.name}: {block}"


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


# -- the tools the skill says to prefer (RK1043, in part) --------------------


@pytest.mark.parametrize("path", files(), ids=lambda p: p.stem)
def test_every_verb_a_command_runs_is_reachable_as_a_tool(path):
    """Half of RK1043, and the half this checkout can settle.

    Three of the four commands declared `Bash(roadkeep …:*)` and nothing else, so on a
    plugin-installed machine with no `pip install roadkeep` they had **no working path at
    all**: the console script is not there (RK254), the pre-execution answers `command not
    found`, and the only permission granted names the same missing script. `add` was already
    the exception, declaring its tool — which is what the shipped skill tells every session
    to prefer.

    Both spellings, as `add` writes them: `mcp__roadkeep__<v>` where a project's own
    `.mcp.json` declares the server and `mcp__plugin_roadkeep_roadkeep__<v>` where the plugin
    provides it, because which prefix a session sees is a fact about how it was installed.

    What this does **not** fix is the pre-execution line itself, which still spells the
    console script — that is the open half, and it turns on whether a permission pattern
    expands `${CLAUDE_PLUGIN_ROOT}` before it is compared.
    """
    allowed = frontmatter(path)["allowed-tools"]
    served = {tool.command: tool.name for tool in TOOLS}
    for declared in re.findall(r"Bash\(([^)]*)\)", allowed):
        verb = declared.removeprefix("roadkeep ").removesuffix(":*").strip()
        name = served.get(verb)
        if name is None:
            continue  # a verb this session does not publish as a tool has only the shell
        for prefix in ("mcp__roadkeep__", "mcp__plugin_roadkeep_roadkeep__"):
            assert f"{prefix}{name}" in allowed, f"{path.name}: {verb} has no {prefix} spelling"


def test_the_tool_names_are_the_served_ones_and_not_the_cli_spelling():
    """`next-id` is served as `next_id`: a hyphen is not a tool name, and a permission naming
    one grants nothing. Read off `TOOLS` rather than transformed here, so the two surfaces
    cannot disagree about a rename."""
    allowed = " ".join(frontmatter(path)["allowed-tools"] for path in files())
    for name in re.findall(r"mcp__(?:plugin_roadkeep_)?roadkeep__(\w+)", allowed):
        assert name in {tool.name for tool in TOOLS}, name


def test_no_command_spells_the_console_script():
    """The other half of RK1043, and the one that keeps it shut.

    A marketplace install copies files and runs no `pip`, so the console script RK254 found
    missing is missing here too — and these four are the plugin's third executable surface,
    the other two having spelled `${CLAUDE_PLUGIN_ROOT}` all along.

    The variable resolves *anywhere it appears in command content*, which is what makes the
    body the half that could be fixed. It is **not** substituted into `allowed-tools` Bash
    rules — only `${CLAUDE_SKILL_DIR}` and `${CLAUDE_PROJECT_DIR}` are — so the scope still
    names the console script and these commands prompt. That was the cost taken over reaching
    the launcher through `${CLAUDE_SKILL_DIR}/..`, which is a permission pattern nobody can
    read and therefore nobody can review.
    """
    for one in files():
        body = one.read_text(encoding="utf-8").split("---", 2)[2]
        assert "`roadkeep " not in body, f"{one.name}: the console script, not the launcher"
        assert "!`" not in body or LAUNCHER in body, one.name
