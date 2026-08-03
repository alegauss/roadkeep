"""The cheap test in front of the guard, and the one direction it may never be wrong (RK176).

RK128 put `Bash` in the `PreToolUse` matcher and paid for it on an argument. Measured, the
harness waits 184 ms for a hook that spends 148 ms of it before looking at anything, on
every shell command in a governed project. The screen is what takes that back — and a
screen in front of a guardrail is the most dangerous thing in this package, because a hole
in it is silent: no refusal is printed, no test fails, and the boundary quietly stops
holding a side it claims.

So the property asserted here is **one-directional**, and it is the only one worth having:
whatever this skips, :func:`roadkeep.guarding.guard` would have allowed anyway. Everything
else it may get wrong at no cost but time — an uncertain answer loads the package and the
real decision is made there, which is why an over-approximation is safe where a second copy
of the rule would not be.

The second thing held here is that it stays cheap: a module that grew an `import roadkeep`
would still pass every behavioural test above while costing exactly what it was written to
save, so the import list is asserted from the source rather than trusted.
"""

from __future__ import annotations

import ast
import io
import json
import sys
from pathlib import Path

import pytest

from roadkeep.config import CONFIG_NAME
from roadkeep.guarding import ASK_TOOLS, guard
from roadkeep.screening import SCREENED, worth_loading

ROADMAP = "docs/ROADMAP.md"
CHANGELOG = "docs/CHANGELOG.md"

CLEAN = """# Roadmap

## Block A — The model

- 📋 **RK1** (deps: —) **A first symptom** — Because of a reason. → §RK1
"""

CONFIG = f'prefix = "RK"\n[files]\nroadmap = "{ROADMAP}"\nchangelog = "{CHANGELOG}"\n'

#: Commands a session actually runs, plus the ones that must survive the screen. The point
#: of the list is the *ratio*: everything above the last two is what a turn is made of.
COMMANDS = (
    "git status --short",
    "python -m pytest -q",
    "ls",
    "npm run build && npm test",
    "grep -rn TODO src",
    "cat pyproject.toml",
    "git log --oneline -5",
    "echo 'docs are governed'",
    "python -m roadkeep.cli list --block A",
    f"sed -i s/a/b/ {ROADMAP}",
    f"git add {ROADMAP}",
    f"cat {CHANGELOG}",
    f"cat ./{ROADMAP}",
)


def project(tmp_path: Path, *, config: str = CONFIG) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "roadkeep.toml").write_text(config, encoding="utf-8")
    for name, body in {ROADMAP: CLEAN, CHANGELOG: "# Shipped\n"}.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            handle.write(body)
    return tmp_path


def payload(command: str, root: Path, *, tool: str = "Bash") -> str:
    return json.dumps(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": tool,
            "cwd": str(root),
            "tool_input": {"command": command},
        }
    )


@pytest.mark.parametrize("command", COMMANDS)
def test_what_the_screen_skips_the_guard_would_have_allowed(tmp_path, command):
    # The whole safety argument, per command: `False` here is a claim about the guard's
    # answer, and the guard is right there to be asked.
    root = project(tmp_path)
    text = payload(command, root)
    if not worth_loading(text, root):
        assert guard(json.loads(text), root) is None


@pytest.mark.parametrize("command", COMMANDS)
def test_every_command_the_guard_refuses_survives_the_screen(tmp_path, command):
    root = project(tmp_path)
    text = payload(command, root)
    if guard(json.loads(text), root) is not None:
        assert worth_loading(text, root)


def test_the_ordinary_shell_command_never_loads_the_package(tmp_path):
    root = project(tmp_path)
    assert not worth_loading(payload("git status --short", root), root)


def test_a_command_that_names_a_governed_file_loads(tmp_path):
    root = project(tmp_path)
    assert worth_loading(payload(f"sed -i s/a/b/ {ROADMAP}", root), root)


def test_a_project_that_declares_nothing_is_never_loaded_for(tmp_path):
    # No `roadkeep.toml` above `cwd`: the guard is silent in every repository but one, and
    # a hook installed in `~/.claude/settings.json` sees all of them.
    (tmp_path / "notes.md").write_text("nothing here\n", encoding="utf-8")
    assert not worth_loading(payload("git status --short", tmp_path), tmp_path)


def test_a_write_tool_is_not_screened(tmp_path):
    # It names its file, so the config that decides is the one above the *path* and not the
    # one above `cwd` — a distinction this module deliberately does not try to make.
    root = project(tmp_path)
    assert worth_loading(payload("irrelevant", root, tool="Edit"), root)


def test_the_events_that_are_not_a_tool_call_are_not_screened(tmp_path):
    root = project(tmp_path)
    for event in ("SessionStart", "Stop"):
        assert worth_loading(json.dumps({"hook_event_name": event, "cwd": str(root)}), root)


def test_a_config_without_files_is_an_uncertainty_and_loads(tmp_path):
    # `Config` fills in defaults for a table that is absent, and reproducing them here would
    # be the second copy of the rule this module exists not to be.
    root = project(tmp_path, config='prefix = "RK"\n')
    assert worth_loading(payload("git status --short", root), root)


def test_a_broken_config_is_an_uncertainty_and_loads(tmp_path):
    root = project(tmp_path, config="prefix = \n[files\n")
    assert worth_loading(payload("git status --short", root), root)


def test_a_payload_that_is_not_json_loads(tmp_path):
    root = project(tmp_path)
    assert worth_loading("{not json", root)
    assert worth_loading("", root)


def test_the_screened_set_is_the_guards_own(tmp_path):
    # Widening `ASK_TOOLS` again without widening this would leave the new tool paying the
    # full price in silence, which is the failure mode nothing else here would report.
    assert SCREENED == ASK_TOOLS
    assert CONFIG_NAME == "roadkeep.toml"


def test_the_screen_imports_nothing_from_the_package():
    # The cost it saves *is* the absence of these imports, so the absence is the assertion.
    source = Path(__file__).parents[1] / "src" / "roadkeep" / "screening.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    named = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            named.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            named.add(node.module)
    assert not [name for name in named if name.split(".")[0] == "roadkeep"]


def test_the_launcher_answers_a_screened_payload_without_the_cli(tmp_path, capsys, monkeypatch):
    launcher = _launcher()
    root = project(tmp_path)
    monkeypatch.setattr(sys, "stdin", io.StringIO(payload("git status --short", root)))
    assert launcher.run(["guard"]) == 0
    assert capsys.readouterr().out == ""


def test_the_launcher_still_refuses_what_it_has_to(tmp_path, capsys, monkeypatch):
    # The screen is in front of the guard and never instead of it: the same payload that
    # was refused before RK176 is refused after it, through the same code.
    launcher = _launcher()
    root = project(tmp_path)
    monkeypatch.setattr(sys, "stdin", io.StringIO(payload(f"sed -i s/a/b/ {ROADMAP}", root)))
    assert launcher.run(["guard"]) == 0
    answer = json.loads(capsys.readouterr().out)
    output = answer["hookSpecificOutput"]
    assert output["permissionDecision"] == "ask"
    assert "ROADMAP.md" in output["permissionDecisionReason"]


def _launcher():
    """`scripts/roadkeep.py`, loaded by path: it is not on the import path and must not be."""
    import importlib.util

    path = Path(__file__).parents[1] / "scripts" / "roadkeep.py"
    spec = importlib.util.spec_from_file_location("roadkeep_launcher", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
