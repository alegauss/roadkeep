"""The plugin manifest and the hook it installs — declared in JSON, reasoned about here (RK22).

`.claude-plugin/plugin.json` and `hooks/hooks.json` are the fourth and fifth surfaces that
run this tool somewhere other than a developer's shell, and unlike `action.yml` and
`.pre-commit-hooks.yaml` they cannot explain themselves: **JSON has no comments**. So the
decisions those two files encode live here, next to the assertions that hold them.

* **One command for two events.** Both hooks run `roadkeep guard`, because the event is in
  the payload. A `roadkeep lint` in the `Stop` slot would exit 1, which the harness reads as
  a *non-blocking* error — the report would go to the user and never to the agent that wrote
  the drift, which is the one reader who can fix it in the same turn.
* **The matcher and the code agree.** The `PreToolUse` matcher lists the writing tools, and
  :data:`~roadkeep.guarding.WRITE_TOOLS` filters them again inside the command. Two lists
  that can disagree is exactly the failure this project exists to remove, so a test compares
  them rather than a reviewer.
* **`Bash` is not matched, on purpose.** `sed -i` on the roadmap is a real bypass; matching
  every shell command to catch it is a tax on every command in the session. The `Stop` hook
  is the answer, and that trade is asserted so it stays a decision rather than an oversight.
* **Every hook has a timeout.** A `PreToolUse` hook is synchronous: an unbounded one turns a
  hung interpreter into a session that cannot write anything at all.
* **The MCP server is declared too, and starts the same way the hook does.** `.mcp.json`
  would be auto-discovered at the plugin root, but it is named in the manifest for the reason
  `hooks` is: a declared path is one a test can check exists. Both surfaces run the installed
  console script, so the plugin asks for *one* thing to be on PATH rather than two (RK24).
* **The version is the module's.** This is the *only* second place the number is written
  (`pyproject.toml` reads the module, RK19), because `/plugin` shows a version to whoever
  installed it and "unknown" is not an answer somebody can pin. A duplicate held by a test
  is a duplicate; one held by review is a disagreement waiting for a release.
* **The marketplace entry states what the manifest cannot.** `marketplace.json` makes
  `/plugin install` reach this repository (RK26), and it carries a name, a source and a
  category — *not* the description, author, license, keywords or version, all of which
  `plugin.json` already states in the same commit. That rule is the same sentence as the one
  above: two copies of a description are two descriptions, and the one in the listing is the
  one nobody remembers to update.
* **The source is `./` because this repository is the plugin.** Shio publishes a marketplace
  whose plugin sits in a subdirectory; here the components (`hooks/`, `skills/`, `commands/`,
  `.mcp.json`) are at the root beside the package they run, so the plugin root is the
  repository root. A test resolves it rather than trusting the spelling.
"""

from __future__ import annotations

import json
import shlex
import subprocess
import sys
from pathlib import Path

import roadkeep
from roadkeep.cli import build_parser
from roadkeep.guarding import STOP_EVENTS, WRITE_TOOLS

HERE = Path(__file__).resolve().parents[1]
MANIFEST = HERE / ".claude-plugin" / "plugin.json"
HOOKS = HERE / "hooks" / "hooks.json"
MCP = HERE / ".mcp.json"
MARKETPLACE = HERE / ".claude-plugin" / "marketplace.json"


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def declarations(event: str) -> list[dict]:
    """Every command declared for one event, matcher groups flattened."""
    return [
        hook
        for group in read(HOOKS)["hooks"].get(event, [])
        for hook in group["hooks"]
    ]


# -- the manifest ------------------------------------------------------------


def test_the_manifest_names_the_plugin_and_points_at_its_hooks():
    manifest = read(MANIFEST)
    assert manifest["name"] == "roadkeep"
    assert manifest["description"]
    # Declared rather than left to the directory convention: a path stated in the manifest
    # is a path this test can check exists, which the convention is not.
    declared = HERE / manifest["hooks"].removeprefix("./")
    assert declared == HOOKS and declared.is_file()


def test_the_plugin_states_the_version_the_package_states():
    assert read(MANIFEST)["version"] == roadkeep.__version__


def test_the_plugin_points_at_the_repository_the_package_does():
    """`/plugin install` is the only route that shows these to somebody deciding to trust
    it, and the same two facts are asserted of the wheel in `tests/test_packaging.py`."""
    manifest = read(MANIFEST)
    assert manifest["license"] == "Apache-2.0"
    assert manifest["repository"] == "https://github.com/alegauss/roadkeep"


# -- the hook it installs ----------------------------------------------------


def test_the_matcher_lists_the_tools_the_command_filters_for():
    matchers = [group["matcher"] for group in read(HOOKS)["hooks"]["PreToolUse"]]
    assert len(matchers) == 1
    assert tuple(sorted(matchers[0].split("|"))) == tuple(sorted(WRITE_TOOLS))


def test_no_hook_matches_bash():
    """The bypass the `Stop` hook exists to catch. Matching every shell command for it
    would cost every command in the session, so the trade is recorded as an assertion."""
    declared = json.dumps(read(HOOKS))
    assert "Bash" not in declared


def test_the_turn_cannot_end_on_a_drifted_file():
    assert declarations("Stop"), "the `Bash` bypass would then be caught by nothing"
    # SubagentStop is handled by the command (STOP_EVENTS) and deliberately not declared:
    # a subagent's writes are in the files when the main turn ends, so the outer hook
    # already judges them, and a second run of `lint` per subagent buys nothing.
    assert "SubagentStop" in STOP_EVENTS
    assert "SubagentStop" not in read(HOOKS)["hooks"]


#: The plugin's own launcher, as a command line spells it (RK57). Everything before the
#: subcommand: an interpreter, and the script the plugin ships at its own root.
LAUNCHER = ("python", "${CLAUDE_PLUGIN_ROOT}/scripts/roadkeep.py")


def subcommand_of(command: str) -> str:
    """The CLI arguments a declared command passes, with the launcher stripped."""
    argv = shlex.split(command)
    assert tuple(argv[:2]) == LAUNCHER, command
    return build_parser().parse_args(argv[2:]).command


def test_every_declared_command_is_one_the_cli_accepts():
    # The same argument `tests/test_surfaces.py` makes about the Action and the pre-commit
    # hook: a surface that drifts from the CLI fails a test instead of failing a session.
    commands = declarations("PreToolUse") + declarations("Stop")
    assert len(commands) == 2
    for hook in commands:
        assert hook["type"] == "command"
        assert subcommand_of(hook["command"]) == "guard", hook["command"]


def test_one_command_answers_both_events():
    """The event is in the payload, so there is one entry point and one place to fix."""
    commands = {hook["command"] for hook in declarations("PreToolUse") + declarations("Stop")}
    assert len(commands) == 1


def test_every_hook_bounds_how_long_it_may_block_the_write():
    for hook in declarations("PreToolUse") + declarations("Stop"):
        assert isinstance(hook.get("timeout"), int) and hook["timeout"] > 0, hook


# -- the MCP server it installs (RK24) ---------------------------------------


def test_the_manifest_points_at_the_server_it_ships():
    declared = HERE / read(MANIFEST)["mcpServers"].removeprefix("./")
    assert declared == MCP and declared.is_file()


def test_one_server_named_for_the_package():
    """The name is a prefix an agent reads: the tools arrive as `mcp__roadkeep__add`. A
    second server here would be a second name for one engine."""
    assert list(read(MCP)["mcpServers"]) == ["roadkeep"]


def test_the_server_runs_a_command_line_the_cli_accepts():
    server = read(MCP)["mcpServers"]["roadkeep"]
    assert (server["command"], server["args"][0]) == LAUNCHER
    assert build_parser().parse_args(server["args"][1:]).command == "mcp"
    assert "env" not in server, "a server that needs configuration is one that fails silently"


# -- and it runs what the plugin carries (RK57) -------------------------------


def test_both_surfaces_run_the_launcher_the_plugin_ships():
    """`/plugin install` is the whole setup: no `pip install`, nothing on PATH.

    The path is `${CLAUDE_PLUGIN_ROOT}`-relative because that is what the harness
    substitutes, and asserted to exist because a plugin whose hook points at a missing file
    installs cleanly and then does nothing at all — which is how this was found.
    """
    launcher = HERE / "scripts" / "roadkeep.py"
    assert launcher.is_file()
    assert LAUNCHER[1].endswith("/scripts/roadkeep.py")
    declared = [hook["command"] for hook in declarations("PreToolUse") + declarations("Stop")]
    declared.append(" ".join([read(MCP)["mcpServers"]["roadkeep"]["command"], *read(MCP)["mcpServers"]["roadkeep"]["args"]]))
    for command in declared:
        assert "${CLAUDE_PLUGIN_ROOT}" in command, command
        assert "roadkeep guard" not in command and "roadkeep mcp" not in command


def test_the_launcher_prefers_the_source_it_ships_over_anything_installed():
    # Position 0, not `append`: a plugin that silently ran an older installed copy would
    # report this version through `/plugin` while another one answered.
    source = (HERE / "scripts" / "roadkeep.py").read_text(encoding="utf-8")
    assert "sys.path.insert(0," in source
    assert '"src"' in source


def test_the_launcher_runs_from_any_directory(tmp_path):
    """A subprocess, because the whole claim is about a process the harness starts."""
    finished = subprocess.run(
        [sys.executable, str(HERE / "scripts" / "roadkeep.py"), "--version"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert finished.returncode == 0, finished.stderr
    assert finished.stdout.strip().startswith(f"roadkeep {roadkeep.__version__} (")


def test_the_launcher_names_the_tree_it_ran_and_not_only_its_number(tmp_path):
    """RK79: a cache and a checkout both answer `0.1.0`, so the number cannot be the answer.

    The launcher is the surface where the two diverge — the hook and the MCP server go
    through it while `python -m roadkeep.cli` does not — so this asserts the directory it
    printed is the `src/` it put first on `sys.path`, and not whatever else was importable.
    """
    finished = subprocess.run(
        [sys.executable, str(HERE / "scripts" / "roadkeep.py"), "--version"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert finished.returncode == 0, finished.stderr
    assert str(HERE / "src" / "roadkeep") in finished.stdout


# -- the marketplace that installs it (RK26) ---------------------------------


def test_the_marketplace_offers_this_plugin_and_nothing_else():
    marketplace = read(MARKETPLACE)
    assert marketplace["$schema"].endswith("marketplace.schema.json")
    assert marketplace["name"] == "alegauss" and marketplace["owner"]["name"]
    # One entry, under the name the manifest states: a listing that renames the plugin is a
    # second name for it, and `/plugin install <name>@alegauss` is the one an install pins.
    entry, = marketplace["plugins"]
    assert entry["name"] == read(MANIFEST)["name"]


def test_the_source_resolves_to_the_directory_holding_the_manifest():
    """`./` and not a subdirectory: the components sit at the repository root beside the
    package they run, so the plugin root *is* the checkout."""
    entry, = read(MARKETPLACE)["plugins"]
    # Relative to the marketplace *root* — the checkout — and not to `.claude-plugin/`,
    # which is where the file happens to sit.
    root = (HERE / entry["source"]).resolve()
    assert root == HERE
    assert (root / ".claude-plugin" / "plugin.json").is_file()


def test_the_entry_states_nothing_the_manifest_already_states():
    """The listing and the manifest travel in one commit, so a description repeated here is
    the copy that goes stale — and a version repeated here is a third place to bump."""
    entry, = read(MARKETPLACE)["plugins"]
    manifest = read(MANIFEST)
    duplicated = sorted(set(entry) & set(manifest) - {"name"})
    assert duplicated == [], duplicated
    assert "version" not in entry
    # What is left is about the *listing* and has nowhere else to live.
    assert set(entry) == {"name", "source", "category"}
