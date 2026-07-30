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
"""

from __future__ import annotations

import json
import shlex
from pathlib import Path

import roadkeep
from roadkeep.cli import build_parser
from roadkeep.guarding import STOP_EVENTS, WRITE_TOOLS

HERE = Path(__file__).resolve().parents[1]
MANIFEST = HERE / ".claude-plugin" / "plugin.json"
HOOKS = HERE / "hooks" / "hooks.json"
MCP = HERE / ".mcp.json"


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


def test_every_declared_command_is_one_the_cli_accepts():
    # The same argument `tests/test_surfaces.py` makes about the Action and the pre-commit
    # hook: a surface that drifts from the CLI fails a test instead of failing a session.
    commands = declarations("PreToolUse") + declarations("Stop")
    assert len(commands) == 2
    for hook in commands:
        assert hook["type"] == "command"
        args = build_parser().parse_args(shlex.split(hook["command"])[1:])
        assert args.command == "guard", hook["command"]


def test_one_command_answers_both_events():
    """The event is in the payload, so there is one entry point and one place to fix."""
    commands = {hook["command"] for hook in declarations("PreToolUse") + declarations("Stop")}
    assert commands == {"roadkeep guard"}


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
    args = build_parser().parse_args(server["args"])
    assert args.command == "mcp"
    # The console script the hooks already require, not a second way in: `python -m` or a
    # `uvx` line would make the plugin depend on the interpreter that happens to be first.
    assert server["command"] == "roadkeep"
    assert "env" not in server, "a server that needs configuration is one that fails silently"
