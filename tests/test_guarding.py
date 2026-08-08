"""The barrier an agent cannot route around, and the four ways it must not misfire (RK22).

L1 is only true for text that arrives through a command, and `Edit` is cheaper than reading
a `--help` — so the hook that denies the hand-edit is what makes the law hold rather than
describe an intention. What is worth testing about it is not the happy path, which is one
dict lookup, but the failure modes: every one of them is a *session* somebody cannot work
in, which is how a guardrail gets uninstalled.

* **It denies the governed file and nothing else.** A guard that catches `README.md`
  because the path looked documentary is a guard the user removes on the first false
  refusal, and then nothing enforces anything.
* **It names the command, and the command exists.** The refusal is only useful if what it
  offers actually parses, so every command in `_INSTEAD` is fed to the real CLI parser —
  the same argument `tests/test_surfaces.py` makes about the Action and the pre-commit hook.
  A renamed flag then fails a test instead of teaching an agent a command that does not run.
* **It allows on its own errors.** A broken `roadkeep.toml`, a payload that is not JSON, a
  tool input with no path: allow. The alternative is one typo in a config file making a
  repository unwritable, and RK14 still refuses the file at the commit.
* **It answers per project, not per process.** A session edits across repositories, so the
  configuration that decides is the one above the *file*, and two projects with different
  `[files]` get different answers from one hook.

The `Stop` half is the backstop for the bypass `PreToolUse` deliberately does not match
(`Bash`), and its own failure mode is a loop: blocking a turn whose files the agent has
already failed to repair. `stop_hook_active` is what ends it, and that is asserted here.
"""

from __future__ import annotations

import io
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path

import pytest

from roadkeep.cli import EXIT_OK, build_parser, main
from roadkeep.guarding import (
    _INSTEAD,
    _NOTICE_BUDGET,
    _SCAFFOLD,
    Notice,
    Refusal,
    announce,
    governed,
    guard,
    review,
)
from roadkeep.provenance import invocation
from roadkeep.serving import TOOLS

#: This checkout, which is the tree `install` translates in the two tests that wire a
#: project to one (RK234) — the same source `tests/test_installing.py` copies from.
HERE = Path(__file__).resolve().parents[1]

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


def committed(tmp_path: Path, *, roadmap: str = CLEAN) -> Path:
    """A governed project with a first commit, which is what `HEAD` means (RK60).

    The adopting case has history: the drift is in it, and the turn is answerable for the
    lines it changed since. A repository with no commits is the other branch, asserted below.
    """
    project(tmp_path, roadmap=roadmap)
    for args in (
        ["init", "-q"],
        ["config", "user.email", "t@example.com"],
        ["config", "user.name", "T"],
        ["config", "commit.gpgsign", "false"],
        ["add", "-A"],
        ["commit", "-qm", "adopted with drift in it"],
    ):
        done = subprocess.run(
            ["git", "-C", str(tmp_path), *args], capture_output=True, text=True, check=False
        )
        assert done.returncode == 0, done.stderr
    return tmp_path


def test_the_stop_gate_ignores_drift_the_turn_did_not_touch(tmp_path):
    # Shio adopted the tool with 278 findings in it, and the hook blocked the end of every
    # turn that touched none of them. A gate that fires on somebody else's work is one that
    # gets turned off, which is worth less than no gate.
    drifted = CLEAN.replace("A first symptom", "A first symptom that is far too long " * 6)
    committed(tmp_path, roadmap=drifted)
    assert review({"hook_event_name": "Stop"}, tmp_path) is None


def test_the_stop_gate_still_blocks_a_line_this_turn_changed(tmp_path):
    committed(tmp_path)
    path = tmp_path / ROADMAP
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "Because of a reason.", "Because of a reason. And a second sentence."
        ),
        encoding="utf-8",
    )
    found = review({"hook_event_name": "Stop"}, tmp_path)
    assert found is not None
    assert [f.code for f in found.report.findings] == ["why.sentences"]
    assert "this turn changed" in str(found)


def test_without_history_the_gate_judges_everything(tmp_path):
    # No commits, so nothing can be excused: a file git cannot diff is a file whose every
    # line arrived without one.
    drifted = CLEAN.replace("A first symptom", "A first symptom that is far too long " * 6)
    project(tmp_path, roadmap=drifted)
    assert review({"hook_event_name": "Stop"}, tmp_path) is not None


def project(
    tmp_path: Path, *, roadmap: str = CLEAN, config: str = CONFIG, wired: bool = False
) -> Path:
    """A minimal governed project. Written with `newline=""` like every other fixture:
    the round-trip invariant is about bytes, and a translated line ending is a difference.

    `wired` writes the `.mcp.json` an `install`ed project has, which is what decides the
    spelling of the tools the refusal offers (RK333) — without it the project is the adopting
    one, whose server the plugin provides under a longer name.
    """
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "roadkeep.toml").write_text(config, encoding="utf-8")
    if wired:
        (tmp_path / ".mcp.json").write_text(
            '{"mcpServers": {"roadkeep": {"command": "python", "args": []}}}', encoding="utf-8"
        )
    for name, body in {ROADMAP: roadmap, CHANGELOG: LEDGER}.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            handle.write(body)
    return tmp_path


def write(path: str, *, tool: str = "Edit", cwd: Path | None = None) -> dict[str, object]:
    """A `PreToolUse` payload, as the harness spells one."""
    payload: dict[str, object] = {
        "hook_event_name": "PreToolUse",
        "tool_name": tool,
        "tool_input": {"file_path": path},
    }
    if cwd is not None:
        payload["cwd"] = str(cwd)
    return payload


# -- what is refused ---------------------------------------------------------


#: What a `PreToolUse` decision is allowed to load, beyond `guarding` itself (RK260). The hook
#: runs on every Edit, Write and Bash and the harness waits for it, and the three events this
#: module serves need disjoint thirds — so an import that belongs to `Stop` or `SessionStart`
#: appears here as a failure rather than as 75 ms nobody measured.
DENIAL_REACHES = {
    # The config is the question — which paths this project governs — and `schema` is what
    # `[limits]` parses into. `document` is *not* here (RK261): the guard decides where a write
    # was going and never opens the file, so the model that would is `Config.document`'s own.
    "roadkeep.config",
    "roadkeep.schema",
    # The tool names the denial offers (RK58), and the shell invocation beside them (RK254).
    # `locking` is absent for `document`'s reason: a denial dispatches nothing, so the lock is
    # never taken and `LockBusy` is reached inside `serving.call` (RK261).
    "roadkeep.serving",
    "roadkeep.provenance",
}


def test_a_denial_loads_only_what_a_denial_needs():
    # Measured before this held: 84.5 ms and 25 modules, against 44.6 and 5 — the linter it will
    # not run and the ledger it will not read, on the hook the harness blocks on. A fresh
    # process per call is why deferring is right here and hoisting is right in the server
    # (RK202).
    #
    # The **set** is the assertion and not the milliseconds (RK261): a single-shot import timing
    # on this machine drifts far enough that a five-module tree measured slower than a
    # seven-module one, so a test asserting a duration would fail on load rather than on a
    # regression. The module set is exact, and it is what the duration tracks.
    loaded = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; sys.path.insert(0, 'src'); import roadkeep.guarding; "
            "print('\\n'.join(m for m in sys.modules if m.startswith('roadkeep.')))",
        ],
        cwd=Path(__file__).parents[1],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    assert set(loaded) - {"roadkeep.guarding"} == DENIAL_REACHES


def test_the_roadmap_is_refused_and_the_command_is_named(tmp_path):
    root = project(tmp_path)
    refusal = guard(write(str(root / ROADMAP)), root)
    assert refusal is not None
    assert refusal.role == "roadmap"
    # The path as the project spells it: a reason quoting an absolute path is about one
    # machine, and it is read by an agent that has to type the command next.
    assert refusal.path == ROADMAP
    assert f"{invocation()} add --block" in str(refusal)
    # And the bullet in this file that is not a task line (RK70): a denial that offered only
    # the five commands writing task lines left `sed` as the route to the non-goals.
    assert f"{invocation()} non-goal add --lead" in str(refusal)


def test_the_ledger_names_the_transaction_and_not_add(tmp_path):
    root = project(tmp_path)
    refusal = guard(write(str(root / CHANGELOG), tool="Write"), root)
    assert refusal is not None and refusal.role == "changelog"
    reason = str(refusal)
    assert "Write refused" in reason
    assert f"{invocation()} ship <id>" in reason
    assert f"{invocation()} record add --block" in reason
    assert f"{invocation()} record drop <id>" in reason
    # `add` writes the roadmap. Offering it here would name a command that cannot make
    # this edit, which is worse than naming none.
    assert f"{invocation()} add " not in reason


def test_the_refusal_names_the_tool_before_the_command(tmp_path):
    # Since RK57 the plugin installs with no console script, so the shell half may be a
    # `command not found` — and advice that does not run teaches that the tool's advice
    # does not run. The same install serves the tools, so they are named first (RK58).
    root = project(tmp_path, wired=True)
    reason = str(guard(write(str(root / ROADMAP)), root))
    assert reason.index("mcp__roadkeep__add") < reason.index(f"{invocation()} add --block")
    assert "this session's tools" in reason
    # Both stay: a project that pip-installed is real, and CI has no MCP client at all.
    assert "Or the same engine in a shell" in reason


def test_the_project_that_declares_the_server_is_offered_the_bare_name(tmp_path):
    # What an `install`ed project has, and what this checkout has: `.mcp.json` at the root
    # declaring `roadkeep`, so the tools arrive as `mcp__roadkeep__add`.
    root = project(tmp_path, wired=True)
    refusal = guard(write(str(root / ROADMAP)), root)
    assert refusal is not None and refusal.served == "mcp__roadkeep__"
    assert "mcp__roadkeep__add" in str(refusal)


def test_a_project_the_plugin_serves_is_offered_the_name_that_session_has(tmp_path):
    """RK333, measured with `claude --plugin-dir <tree> -p …` from a project that is not
    this one: the tools come back as `mcp__plugin_roadkeep_roadkeep__add`, and the refusal
    named the bare form — a route that session cannot call, which is worse than the shell
    form it demotes, because that one at least fails loudly."""
    root = project(tmp_path)  # no `.mcp.json`: nothing here declares a server
    refusal = guard(write(str(root / ROADMAP)), root)
    assert refusal is not None
    assert refusal.served == "mcp__plugin_roadkeep_roadkeep__"
    reason = str(refusal)
    assert "mcp__plugin_roadkeep_roadkeep__add" in reason
    # And not both: naming two routes doubles every line of the table for one reader who
    # can only call one of them.
    assert "mcp__roadkeep__add" not in reason


def test_the_plugin_name_is_read_from_the_manifest_and_not_from_the_directory(tmp_path):
    # A plugin is installed under a path the marketplace chooses; the name in the payload is
    # the one the manifest states.
    from roadkeep.provenance import _plugin_name

    assert _plugin_name() == json.loads(
        (HERE / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
    )["name"]


def test_every_named_tool_is_one_the_server_serves():
    """The same argument the CLI commands get: a name nothing answers is worse than none."""
    served = {tool.name for tool in TOOLS}
    for role in ("roadmap", "changelog", "improvements", "strategy"):
        for name, _ in Refusal(tool="Edit", path="x", role=role).tools:
            assert name.removeprefix("mcp__roadkeep__") in served


def test_a_nested_command_is_promoted_under_the_name_that_answers():
    # `section add` is a tool (RK59) and `section` is not, so matching the first word alone
    # would name `mcp__roadkeep__section` — a route nothing answers.
    reason = str(Refusal(tool="Edit", path="docs/IMPROVEMENTS.md", role="improvements"))
    assert "mcp__roadkeep__section_add" in reason
    assert "mcp__roadkeep__section " not in reason


def test_a_role_with_no_tool_behind_it_names_only_the_commands():
    # `init` is not a tool and must not be invented as one: a governed file that is not on
    # disk yet needs scaffolding, which runs once and from a shell.
    reason = str(Refusal(tool="Write", path="docs/ROADMAP.md", role="roadmap", exists=False))
    assert "mcp__roadkeep__" not in reason
    assert f"{invocation()} init" in reason


def test_every_writing_tool_is_matched(tmp_path):
    root = project(tmp_path)
    for tool in ("Edit", "MultiEdit", "Write"):
        assert guard(write(str(root / ROADMAP), tool=tool), root) is not None


def test_a_notebook_path_is_a_path(tmp_path):
    """`NotebookEdit` spells the key differently, and the question is what reaches disk."""
    root = project(tmp_path)
    payload = {
        "hook_event_name": "PreToolUse",
        "tool_name": "NotebookEdit",
        "tool_input": {"notebook_path": str(root / ROADMAP)},
    }
    assert guard(payload, root) is not None


def test_a_relative_path_is_resolved_against_the_session_directory(tmp_path):
    root = project(tmp_path)
    assert guard(write(ROADMAP, cwd=root)) is not None


def test_a_governed_file_that_is_absent_wants_init_and_not_add(tmp_path):
    """`Write` creating the file the config declares is `init`'s job, not an author's."""
    root = project(tmp_path)
    (root / ROADMAP).unlink()
    refusal = guard(write(str(root / ROADMAP), tool="Write"), root)
    assert refusal is not None and refusal.commands == _SCAFFOLD
    assert f"{invocation()} init" in str(refusal)


# -- the side the barrier used to leave open (RK128) ---------------------------


def shell(command: str, cwd: Path | None = None) -> dict[str, object]:
    """A `Bash` payload, which names a command and never a path."""
    payload: dict[str, object] = {
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": command},
    }
    if cwd is not None:
        payload["cwd"] = str(cwd)
    return payload


def test_a_shell_command_writing_a_governed_file_is_no_longer_silence(tmp_path):
    # The defect: the refusal says "roadkeep owns its writes", and an agent that reached for
    # `sed -i` instead of `Edit` got nothing back at all — no refusal, no record, and no lint
    # until the turn tried to end.
    root = project(tmp_path)
    for command in (
        f"sed -i 's/RK1/RK2/' {ROADMAP}",
        f"python -c \"open('{ROADMAP}','a').write('x')\"",
        f"cat > {ROADMAP} <<'EOF'\n- nope\nEOF",
        f'echo x >> "./{ROADMAP}"',
    ):
        refusal = guard(shell(command, cwd=root), root)
        assert refusal is not None, command
        assert refusal.role == "roadmap" and refusal.path == ROADMAP


def test_the_shell_answer_is_ask_because_the_command_is_not_read(tmp_path):
    # `deny` would refuse `git add docs/ROADMAP.md` and every `git log --` of a governed file,
    # and `allow` is not this hook's to give: the third answer is the only honest one.
    root = project(tmp_path, wired=True)
    refusal = guard(shell(f"git add {ROADMAP}", cwd=root), root)
    assert refusal is not None and refusal.decision == "ask"
    reason = str(refusal)
    assert "the decision is yours" in reason
    # The claim the two decisions do not share, and neither one makes the other's.
    assert "Bash refused" not in reason
    # Everything of value is still there: one command table, not two that can drift.
    assert f"{invocation()} add --block" in reason and "mcp__roadkeep__add" in reason


def test_a_named_write_stays_a_denial(tmp_path):
    root = project(tmp_path)
    for tool in ("Edit", "MultiEdit", "NotebookEdit", "Write"):
        refusal = guard(write(str(root / ROADMAP), tool=tool), root)
        assert refusal is not None and refusal.decision == "deny", tool
        assert f"{tool} refused" in str(refusal)


def test_a_shell_command_naming_no_governed_path_is_silence(tmp_path):
    # The tax this used to be avoided for: the overwhelming majority of commands, answered
    # with one config read and a handful of substring tests.
    root = project(tmp_path)
    for command in (
        "python -m pytest -q",
        "git status",
        "sed -i 's/a/b/' README.md",
        "cat docs/notes.md",
        "grep -rn TODO src/",
    ):
        assert guard(shell(command, cwd=root), root) is None, command


def test_the_verbs_the_refusal_recommends_do_not_trip_it(tmp_path):
    """Nothing is allowlisted because nothing needs to be: roadkeep addresses a task by id
    and role, never by path, so the advice this hook prints is advice it lets through."""
    root = project(tmp_path)
    commands = [command for table in _INSTEAD.values() for command, _ in table]
    commands += [command for command, _ in _SCAFFOLD]
    for command in commands:
        assert guard(shell(f"roadkeep {command}", cwd=root), root) is None, command


def test_the_path_is_matched_however_the_command_spells_it(tmp_path):
    root = project(tmp_path)
    absolute = (root / CHANGELOG).resolve()
    for command in (f'sed -i s/a/b/ "{absolute}"', f"sed -i s/a/b/ {absolute.as_posix()}"):
        refusal = guard(shell(command, cwd=root), root)
        assert refusal is not None and refusal.role == "changelog", command
        # Still spelled as the project spells it: the reason is read on another machine.
        assert refusal.path == CHANGELOG


def test_a_shell_command_outside_a_project_is_silence(tmp_path):
    (tmp_path / "elsewhere").mkdir()
    assert guard(shell(f"sed -i s/a/b/ {ROADMAP}", cwd=tmp_path / "elsewhere")) is None


def test_a_shell_payload_with_no_command_allows(tmp_path):
    root = project(tmp_path)
    for raw in ({}, {"command": ""}, {"command": 7}, "not a mapping"):
        payload = {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": raw}
        assert guard(payload, root) is None, raw


def test_a_broken_config_allows_the_shell_too(tmp_path):
    # The same failure rule as every other path here: one typo must not make a repository
    # unshellable, and `lint` still refuses the file at the commit.
    (tmp_path / "roadkeep.toml").write_text("prefix = [\n", encoding="utf-8")
    assert guard(shell(f"sed -i s/a/b/ {ROADMAP}", cwd=tmp_path), tmp_path) is None


# -- what is allowed, and why each one has to be ------------------------------


def test_an_ungoverned_file_in_the_same_project_is_allowed(tmp_path):
    root = project(tmp_path)
    for name in ("README.md", "docs/notes.md", "src/thing.py", "agents.md"):
        assert guard(write(str(root / name)), root) is None, name


def test_the_configuration_is_not_governed(tmp_path):
    """L6 puts the variability in `roadkeep.toml`, which a human edits on purpose. A tool
    that owned its own configuration could not be reconfigured except by itself."""
    root = project(tmp_path)
    assert guard(write(str(root / "roadkeep.toml")), root) is None


def test_a_tool_that_does_not_write_is_never_judged(tmp_path):
    root = project(tmp_path)
    for tool in ("Read", "Grep", "Glob", "TodoWrite"):
        assert guard(write(str(root / ROADMAP), tool=tool), root) is None, tool
    # `Bash` is guarded since RK128 but only through its `command`: a payload carrying a
    # `file_path` it never sends is not a second way in.
    assert guard(write(str(root / ROADMAP), tool="Bash"), root) is None


def test_a_file_under_no_project_is_allowed(tmp_path):
    """No config above it, so nothing here claims the file — the common case, and the one
    a hook installed globally spends most of its life answering."""
    loose = tmp_path / "docs" / "ROADMAP.md"
    loose.parent.mkdir(parents=True)
    loose.write_text("# not governed\n", encoding="utf-8")
    assert guard(write(str(loose)), tmp_path) is None


def test_a_broken_config_allows_rather_than_denying_everything(tmp_path):
    """The failure rule: a guard that denies on its own error makes one typo in a config
    file into a repository nobody can edit, and the gate still refuses the file."""
    root = project(tmp_path, config='prefix = "RK"\nsymptom_max = 120\n')  # unknown key
    assert guard(write(str(root / ROADMAP)), root) is None


def test_an_unparsable_config_allows(tmp_path):
    root = project(tmp_path, config="prefix = \n")  # not TOML at all
    assert guard(write(str(root / ROADMAP)), root) is None


def test_a_payload_with_nothing_in_it_allows():
    for payload in ({}, {"tool_name": "Edit"}, {"tool_name": "Edit", "tool_input": {}}):
        assert guard(payload) is None


def test_a_tool_input_that_is_not_a_mapping_allows():
    assert guard({"tool_name": "Edit", "tool_input": "docs/ROADMAP.md"}) is None


# -- one hook process, every repository the session touches -------------------


def test_each_project_answers_for_its_own_files(tmp_path):
    """The configuration that decides is the one above the *file*. A hook in
    `~/.claude/settings.json` sees every checkout, and `-C` cannot be right for all of them."""
    here = project(tmp_path / "here")
    there = project(
        tmp_path / "there",
        config='prefix = "SH"\n[files]\nroadmap = "docs/backlog.md"\n',
    )
    (there / "docs" / "backlog.md").write_text("# Backlog\n", encoding="utf-8")

    # Started in `here`, writing `there`: the answer comes from there's own declaration.
    assert guard(write(str(there / "docs" / "backlog.md")), here) is not None
    # And there's roadmap path does not make here's `docs/ROADMAP.md` ungoverned.
    assert guard(write(str(here / ROADMAP)), there) is not None
    # The file `there` does not declare is allowed, even though `here` governs that name.
    assert guard(write(str(there / ROADMAP)), there) is None


def test_the_role_is_the_one_the_project_declared(tmp_path):
    root = project(
        tmp_path, config='prefix = "RK"\n[files]\nimprovements = "docs/WHY.md"\n'
    )
    (root / "docs" / "WHY.md").write_text("# Why\n", encoding="utf-8")
    found = governed(root / "docs" / "WHY.md")
    assert found is not None and found[1] == "improvements"
    assert f"{invocation()} section add" in str(
        Refusal(tool="Edit", path="docs/WHY.md", role="improvements")
    )


@pytest.mark.skipif(
    os.path.normcase("A") != "a", reason="the filesystem distinguishes case"
)
def test_case_is_compared_as_the_filesystem_compares_it(tmp_path):
    """Where `docs/roadmap.md` and `docs/ROADMAP.md` are one file, a comparison that
    misses that allows exactly the write it exists to refuse."""
    root = project(tmp_path)
    assert guard(write(str(root / "docs" / "roadmap.md")), root) is not None


# -- the refusal has to name commands that exist -----------------------------


def test_every_command_a_refusal_offers_is_one_the_cli_accepts():
    # The same check `tests/test_surfaces.py` makes of the Action and the pre-commit hook,
    # for the surface an agent reads most often. A refusal naming a renamed flag teaches a
    # command that does not run, which is how a guardrail becomes a detour.
    for role, commands in {**_INSTEAD, "absent": _SCAFFOLD}.items():
        for declared, purpose in commands:
            args = build_parser().parse_args(shlex.split(declared))
            assert args.command == shlex.split(declared)[0], (role, declared)
            assert purpose, declared


def test_a_refusal_reads_as_an_answer_and_says_reading_is_free():
    reason = str(Refusal(tool="Edit", path=ROADMAP, role="roadmap"))
    assert reason.startswith(f"Edit refused: {ROADMAP} is this project's roadmap")
    assert f"{invocation()} <command> --help" in reason
    # L5: the reason an agent reaches for `Edit` is often to *read* around a line, and a
    # refusal that does not say the query surface exists sends it to open the file.
    assert f"{invocation()} brief <id>" in reason


def test_the_denial_names_the_repair_route_before_the_fourteen_commands():
    """RK424: the barrier is keyed by role and can no longer be the only thing speaking.

    It never reads what the agent was about to write — deliberately — so it cannot narrow
    fourteen commands to one. Since RK420 the *gate* can: a finding carries the command that
    closes it, and this refusal is the one place an agent repairing a reported line will
    certainly look, because it is what stopped the `Edit`. So that route goes first.
    """
    reason = str(Refusal(tool="Edit", path=ROADMAP, role="roadmap"))
    assert f"{invocation()} repair" in reason
    assert f"{invocation()} explain <code>" in reason
    # First, and before the table it is meant to shortcut — a shortcut printed after the
    # long way round is a shortcut nobody takes.
    assert reason.index(f"{invocation()} repair") < reason.index("Call instead")
    # And the fourteen stay, for the write that is not a repair.
    assert f"{invocation()} add --block" in reason or "mcp__roadkeep__add" in reason


def test_the_denial_still_runs_no_linter_to_say_it():
    # The budget RK261 bought: a fresh process per hook call, so naming the command has to
    # cost a string and not an import of the gate. `DENIAL_REACHES` is the real assertion
    # (above); this states the intent that number holds.
    assert "roadkeep.linting" not in DENIAL_REACHES
    assert "roadkeep.remedying" not in DENIAL_REACHES


def test_an_unknown_role_offers_nothing_rather_than_guessing():
    """A role no table covers is a role added without its commands — silence over a wrong
    command, and the deny still stands."""
    refusal = Refusal(tool="Edit", path="docs/OTHER.md", role="other")
    assert refusal.commands == ()
    assert f"{invocation()} <command> --help" in str(refusal)


# -- the turn tries to end ---------------------------------------------------


def stop(cwd: Path, *, active: bool = False) -> dict[str, object]:
    return {"hook_event_name": "Stop", "cwd": str(cwd), "stop_hook_active": active}


def test_a_clean_project_lets_the_turn_end(tmp_path):
    root = project(tmp_path)
    assert review(stop(root), root) is None


def test_a_drifted_file_blocks_and_names_the_line(tmp_path):
    root = project(
        tmp_path,
        roadmap=CLEAN + "- 📋 **RK2** (deps: RK99) **A second symptom** — Because. → §RK2\n",
    )
    found = review(stop(root), root)
    assert found is not None
    reason = str(found)
    assert f"{ROADMAP}:" in reason
    assert "RK99" in reason
    assert f"{invocation()} lint --fix" in reason


def test_blocking_twice_is_a_loop_and_never_happens(tmp_path):
    root = project(
        tmp_path,
        roadmap=CLEAN + "- 📋 **RK2** (deps: RK99) **A second symptom** — Because. → §RK2\n",
    )
    assert review(stop(root), root) is not None
    assert review(stop(root, active=True), root) is None


def test_a_long_report_is_truncated_and_says_so(tmp_path):
    lines = "\n".join(
        f"- 📋 **RK{n}** (deps: RK99) **A symptom number {n}** — Because. → §RK{n}"
        for n in range(2, 22)
    )
    root = project(tmp_path, roadmap=CLEAN + lines + "\n")
    reason = str(review(stop(root), root))
    assert "and 8 more" in reason  # 20 findings, 12 printed
    assert reason.count(f"{ROADMAP}:") == 12


def test_a_directory_under_no_project_lets_the_turn_end(tmp_path):
    assert review(stop(tmp_path), tmp_path) is None


def test_a_broken_config_lets_the_turn_end(tmp_path):
    root = project(tmp_path, config='prefix = "RK"\nsymptom_max = 120\n')
    assert review(stop(root), root) is None


# -- the command, as the harness runs it -------------------------------------


def run(monkeypatch, capsys, payload: object, root: Path) -> dict[str, object]:
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(payload)))
    # Always 0: the harness reads a non-zero exit as the hook itself having failed, which
    # would deny nothing and report a broken hook on every write in the session.
    assert main(["-C", str(root), "guard"]) == EXIT_OK
    out = capsys.readouterr().out
    return json.loads(out) if out.strip() else {}


def test_the_command_answers_a_pretooluse_payload_with_a_denial(tmp_path, monkeypatch, capsys):
    root = project(tmp_path)
    answer = run(monkeypatch, capsys, write(str(root / ROADMAP)), root)
    specific = answer["hookSpecificOutput"]
    assert specific["hookEventName"] == "PreToolUse"
    assert specific["permissionDecision"] == "deny"
    assert f"{invocation()} add --block" in specific["permissionDecisionReason"]


def test_an_allowed_write_is_answered_with_silence(tmp_path, monkeypatch, capsys):
    """Never `permissionDecision: "allow"`: that *grants* the write, waving through the
    permission rules the user set for every file this tool has no opinion about."""
    root = project(tmp_path)
    assert run(monkeypatch, capsys, write(str(root / "README.md")), root) == {}


def test_the_command_answers_a_stop_payload_with_a_block(tmp_path, monkeypatch, capsys):
    root = project(
        tmp_path,
        roadmap=CLEAN + "- 📋 **RK2** (deps: RK99) **A second symptom** — Because. → §RK2\n",
    )
    answer = run(monkeypatch, capsys, stop(root), root)
    assert answer["decision"] == "block"
    assert "RK99" in answer["reason"]


def test_a_payload_that_is_not_json_is_answered_with_silence(tmp_path, monkeypatch, capsys):
    root = project(tmp_path)
    monkeypatch.setattr("sys.stdin", io.StringIO("not json at all"))
    assert main(["-C", str(root), "guard"]) == EXIT_OK
    assert capsys.readouterr().out == ""


def test_a_payload_that_is_not_an_object_is_answered_with_silence(tmp_path, monkeypatch, capsys):
    root = project(tmp_path)
    assert run(monkeypatch, capsys, ["Edit", ROADMAP], root) == {}


def test_the_command_survives_the_config_error_every_other_command_exits_on(
    tmp_path, monkeypatch, capsys
):
    """`guard` runs before every write in the session. Exiting 2 here — which is right for
    `add` — would report a broken hook on every edit until somebody fixed the TOML."""
    root = project(tmp_path, config='prefix = "RK"\nsymptom_max = 120\n')
    assert run(monkeypatch, capsys, write(str(root / ROADMAP)), root) == {}


# -- what a session is told before it reads anything (RK82) -------------------


def start(cwd: Path) -> dict[str, object]:
    return {"hook_event_name": "SessionStart", "cwd": str(cwd)}


def test_the_notice_names_the_files_this_project_governs(tmp_path):
    """Derived from `[files]`, never a sentence about three paths (L6). The whole point is
    that the session knows which paths are covered *before* it greps for one."""
    root = project(tmp_path)
    notice = announce(start(root), root)
    assert notice.files == (ROADMAP, CHANGELOG)
    assert ROADMAP in str(notice) and CHANGELOG in str(notice)


def test_the_notice_states_that_reading_is_a_command_too():
    """The asymmetry RK82 measured: the write side had a hook and the read side had prose
    in two non-resident places, so the rule arrived in the same result set as the file."""
    said = str(Notice(files=(ROADMAP,)))
    assert "brief" in said and "show" in said and "list" in said


def test_the_notice_does_not_restate_the_write_path():
    """The skill is the authority on which command to call (RK23), and this loads on every
    session in every governed project. Repeating it here would be a second copy of a rule
    that can disagree — and the cost would be paid by the turns that write nothing."""
    said = str(Notice(files=(ROADMAP,)))
    assert "add --block" not in said and "ship" not in said


def test_the_notice_fits_the_budget_that_makes_it_worth_injecting():
    """Resident for the whole session, so its size is the argument for it. A number a test
    holds, because prose about being brief is what stops holding."""
    assert len(str(Notice(files=(ROADMAP, CHANGELOG)))) <= _NOTICE_BUDGET


def test_the_notice_names_a_vendored_copy_that_has_drifted(tmp_path):
    """The gate RK100 named as holding the copy in step, run where it is cheap (RK234).

    Measured on Turing before this: 78 lines behind, and a `PreToolUse` matcher missing
    `Bash` — a guard narrower than the one the plugin ships, in the file that decides whether
    the guard fires at all. Nothing ran `--check` there, so nothing said so.
    """
    from roadkeep.installing import PROJECT_SKILL, install

    root = project(tmp_path)
    install(root, source=HERE)
    (root / PROJECT_SKILL).write_text("a copy somebody edited\n", encoding="utf-8")
    notice = announce(start(root), root)
    assert notice.stale == (PROJECT_SKILL.replace("\\", "/"),)
    assert "has drifted from the checkout answering here" in str(notice)
    assert f"`{invocation()} install` refreshes it" in str(notice)


def test_a_project_the_plugin_serves_is_asked_nothing_about_a_copy(tmp_path):
    """The discriminator is the vendored file itself: no copy, nothing to drift, and the
    cost of asking is one `is_file` — 0.07ms against RK176's 43ms floor."""
    root = project(tmp_path)
    assert announce(start(root), root).stale == ()
    assert "drifted" not in str(announce(start(root), root))


def test_a_session_outside_a_roadkeep_project_is_told_nothing(tmp_path):
    """Silence is the same decision the barrier makes about `allow`: a hook that speaks in
    every repository is one every repository pays for."""
    assert announce(start(tmp_path), tmp_path) is None


def test_a_broken_config_says_nothing_rather_than_failing_the_session_start(tmp_path):
    root = project(tmp_path, config="prefix = [")
    assert announce(start(root), root) is None


def test_the_command_answers_a_sessionstart_payload_with_context(
    tmp_path, monkeypatch, capsys
):
    root = project(tmp_path)
    specific = run(monkeypatch, capsys, start(root), root)["hookSpecificOutput"]
    assert specific["hookEventName"] == "SessionStart"
    assert ROADMAP in specific["additionalContext"]


def test_a_session_start_outside_a_project_prints_nothing(tmp_path, monkeypatch, capsys):
    (tmp_path / "elsewhere").mkdir()
    assert run(monkeypatch, capsys, start(tmp_path / "elsewhere"), tmp_path / "elsewhere") == {}
