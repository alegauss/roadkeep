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
from pathlib import Path

import pytest

from roadkeep.cli import EXIT_OK, build_parser, main
from roadkeep.guarding import _INSTEAD, _SCAFFOLD, Refusal, governed, guard, review
from roadkeep.serving import TOOL_NAMES

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


def project(tmp_path: Path, *, roadmap: str = CLEAN, config: str = CONFIG) -> Path:
    """A minimal governed project. Written with `newline=""` like every other fixture:
    the round-trip invariant is about bytes, and a translated line ending is a difference."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "roadkeep.toml").write_text(config, encoding="utf-8")
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


def test_the_roadmap_is_refused_and_the_command_is_named(tmp_path):
    root = project(tmp_path)
    refusal = guard(write(str(root / ROADMAP)), root)
    assert refusal is not None
    assert refusal.role == "roadmap"
    # The path as the project spells it: a reason quoting an absolute path is about one
    # machine, and it is read by an agent that has to type the command next.
    assert refusal.path == ROADMAP
    assert "roadkeep add --block" in str(refusal)


def test_the_ledger_names_the_transaction_and_not_add(tmp_path):
    root = project(tmp_path)
    refusal = guard(write(str(root / CHANGELOG), tool="Write"), root)
    assert refusal is not None and refusal.role == "changelog"
    reason = str(refusal)
    assert "Write refused" in reason
    assert "roadkeep ship <id>" in reason
    assert "roadkeep record --block" in reason
    # `add` writes the roadmap. Offering it here would name a command that cannot make
    # this edit, which is worse than naming none.
    assert "roadkeep add " not in reason


def test_the_refusal_names_the_tool_before_the_command(tmp_path):
    # Since RK57 the plugin installs with no console script, so `roadkeep add` may be a
    # `command not found` — and advice that does not run teaches that the tool's advice
    # does not run. The same install serves the tools, so they are named first (RK58).
    root = project(tmp_path)
    reason = str(guard(write(str(root / ROADMAP)), root))
    assert reason.index("mcp__roadkeep__add") < reason.index("roadkeep add --block")
    assert "this session's tools" in reason
    # Both stay: a project that pip-installed is real, and CI has no MCP client at all.
    assert "Or the same engine in a shell" in reason


def test_every_named_tool_is_one_the_server_serves(tmp_path):
    """The same argument the CLI commands get: a name nothing answers is worse than none."""
    root = project(tmp_path)
    for role in ("roadmap", "changelog", "improvements"):
        for name, _ in Refusal(tool="Edit", path="x", role=role).tools:
            assert name.removeprefix("mcp__roadkeep__") in TOOL_NAMES


def test_a_role_with_no_tool_behind_it_names_only_the_commands(tmp_path):
    # `section add` is not a tool yet (RK59), so the prose file's refusal has nothing to
    # promote — and it must not invent `mcp__roadkeep__section`.
    root = project(
        tmp_path,
        config=CONFIG + 'improvements = "docs/IMPROVEMENTS.md"\n',
    )
    (root / "docs" / "IMPROVEMENTS.md").write_text("# Improvements\n", encoding="utf-8")
    reason = str(guard(write(str(root / "docs" / "IMPROVEMENTS.md")), root))
    assert "mcp__roadkeep__" not in reason
    assert "Call instead, from the project root:" in reason


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
    assert "roadkeep init" in str(refusal)


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
    for tool in ("Read", "Bash", "Grep", "Glob", "TodoWrite"):
        assert guard(write(str(root / ROADMAP), tool=tool), root) is None, tool


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
    assert "roadkeep section add" in str(
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
    assert "roadkeep <command> --help" in reason
    # L5: the reason an agent reaches for `Edit` is often to *read* around a line, and a
    # refusal that does not say the query surface exists sends it to open the file.
    assert "roadkeep brief <id>" in reason


def test_an_unknown_role_offers_nothing_rather_than_guessing():
    """A role no table covers is a role added without its commands — silence over a wrong
    command, and the deny still stands."""
    refusal = Refusal(tool="Edit", path="docs/OTHER.md", role="other")
    assert refusal.commands == ()
    assert "roadkeep <command> --help" in str(refusal)


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
    assert "roadkeep lint --fix" in reason


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
    assert "roadkeep add --block" in specific["permissionDecisionReason"]


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
