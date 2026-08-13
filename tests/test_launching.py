"""The one file that restates a rule, and the closure that keeps it true (RK1108).

`hooks/roadkeep-launch.py` is committed to an adopting repository so the guard reaches the one
environment the plugin never does: Claude Code on the web installs no marketplace plugin and
reads what the repository carries. It runs *before* an engine has been found, so it may not
import :mod:`roadkeep` — which makes it the only file here that states a rule the package also
states, and the only one where a drift is invisible.

That drift is not hypothetical. It is the defect this task was reported from: a hand-written
copy in an adopting project globbed `~/.claude/plugins` for the engine and stood down on any
hit, so under a `CLAUDE_CONFIG_DIR` pointing elsewhere it deferred to a plugin that was never
loaded, and a hand edit of two governed files passed a session that had a guard. Every rule
below is asked of the shipped file rather than described, because a description is what the
version it replaces had.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from roadkeep.installing import PLUGIN_BRIDGE, PROJECT_BRIDGE

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / PLUGIN_BRIDGE


def load():
    """The bridge as a module, which is how every rule here is asked of the real file."""
    spec = importlib.util.spec_from_file_location("roadkeep_launch", BRIDGE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# -- the closure, which is the deliverable ------------------------------------


def test_the_config_directory_is_the_pair_the_package_resolves(monkeypatch):
    """The rule that drifted, held against the package's own reader. `provenance.installed`
    resolves `$CLAUDE_CONFIG_DIR` or `~/.claude`; so does this, and a change to either without
    the other fails here rather than in somebody's unguarded session."""
    from roadkeep import provenance

    bridge = load()
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", "/somewhere/else")
    assert bridge._config_home() == Path("/somewhere/else")
    monkeypatch.delenv("CLAUDE_CONFIG_DIR")
    assert bridge._config_home() == Path.home() / ".claude"
    # And the package still reads the same pair: the source of both is one line each, and this
    # asserts the *behaviour* rather than the text, so a refactor that keeps the rule passes.
    source = Path(provenance.__file__).read_text(encoding="utf-8")
    assert 'os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude"' in source


def test_the_registry_path_is_the_one_the_package_reads():
    from roadkeep.provenance import _REGISTRY

    assert load().REGISTRY == _REGISTRY


def test_the_plugin_name_is_the_one_the_package_matches():
    from roadkeep.provenance import PLUGIN

    assert load().PLUGIN == PLUGIN


def test_the_engine_path_is_the_one_install_substitutes():
    from roadkeep.installing import LAUNCHER

    assert load().ENGINE_REL.as_posix() == LAUNCHER


# -- defer to the plugin, which is the defect (RK1108) ------------------------


def registry(home: Path, project: Path, *, name: str = "roadkeep@alegauss") -> None:
    """A harness registry wiring one plugin to one project, as the harness writes it."""
    path = home / "plugins" / "installed_plugins.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"plugins": {name: [{"projectPath": str(project), "version": "0.1.0"}]}}),
        encoding="utf-8",
    )


def test_it_stands_down_only_where_this_project_is_the_one_wired(tmp_path, monkeypatch):
    bridge = load()
    home, project = tmp_path / "config", tmp_path / "project"
    project.mkdir()
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(home))
    registry(home, project)
    assert bridge._plugin_is_wired(project) is True
    # Another project's row is not this project's answer, which is what "wired for this
    # project" means and what a glob over the directory could never say.
    other = tmp_path / "other"
    other.mkdir()
    assert bridge._plugin_is_wired(other) is False


def test_a_copy_on_disk_is_not_a_plugin_that_runs(tmp_path, monkeypatch):
    """The measured defect. A marketplace clone and every cached version carry
    `scripts/roadkeep.py` whether or not this project uses any of them, so the question is a
    registry row and never a file — the version this replaces answered on the file."""
    bridge = load()
    home, project = tmp_path / "config", tmp_path / "project"
    project.mkdir()
    engine = home / "plugins" / "marketplaces" / "alegauss" / "scripts" / "roadkeep.py"
    engine.parent.mkdir(parents=True, exist_ok=True)
    engine.write_text("# an engine on disk, wired to nothing\n", encoding="utf-8")
    (engine.parent.parent / ".claude-plugin").mkdir(parents=True, exist_ok=True)
    (engine.parent.parent / ".claude-plugin" / "plugin.json").write_text("{}", encoding="utf-8")
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(home))

    assert bridge._plugin_is_wired(project) is False  # nothing enabled it here


def test_the_wrong_config_directory_is_the_whole_reported_defect(tmp_path, monkeypatch):
    """Two config directories, two independent installs, and only one of them running. Under a
    `CLAUDE_CONFIG_DIR` naming the second, reading the first is how a launcher comes to defer
    to a plugin that was never loaded."""
    bridge = load()
    first, second, project = tmp_path / "a", tmp_path / "b", tmp_path / "project"
    project.mkdir()
    registry(first, project)
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(second))
    assert bridge._plugin_is_wired(project) is False
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(first))
    assert bridge._plugin_is_wired(project) is True


def test_a_registry_it_cannot_read_answers_that_nothing_is_wired(tmp_path, monkeypatch):
    # The safe side of the two: a doubled deny message is cosmetic and an absent guard is the
    # drift roadkeep exists to stop, so an unreadable registry means *this launcher answers*.
    bridge = load()
    home = tmp_path / "config"
    (home / "plugins").mkdir(parents=True)
    (home / "plugins" / "installed_plugins.json").write_text("not json", encoding="utf-8")
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(home))
    assert bridge._plugin_is_wired(tmp_path) is False


def test_a_project_reached_through_a_link_is_one_project(tmp_path, monkeypatch):
    # Resolved and never compared as text: the harness writes the path its platform spells,
    # and a worktree reached through a junction is the same project written twice.
    bridge = load()
    home, real = tmp_path / "config", tmp_path / "real"
    real.mkdir()
    link = tmp_path / "link"
    try:
        link.symlink_to(real, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("this platform will not make a link without elevation")
    registry(home, real)
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(home))
    assert bridge._plugin_is_wired(link) is True


# -- never block a turn, and never reach the network --------------------------


def test_no_engine_anywhere_is_silent_and_exits_zero(tmp_path):
    """A missing roadkeep degrades to unenforced, never to a broken session — a hook that
    fails is a hook an adopter switches off, and then nothing is guarded at all."""
    environment = {
        **os.environ,
        "CLAUDE_PROJECT_DIR": str(tmp_path),
        "CLAUDE_CONFIG_DIR": str(tmp_path / "empty"),
        "XDG_CACHE_HOME": str(tmp_path / "cache"),
        "HOME": str(tmp_path / "home"),
        "USERPROFILE": str(tmp_path / "home"),
    }
    environment.pop("ROADKEEP_HOME", None)
    done = subprocess.run(
        [sys.executable, str(BRIDGE), "guard"],
        input=b"{}",
        capture_output=True,
        env=environment,
        check=False,
    )
    assert done.returncode == 0 and done.stdout == b"" and done.stderr == b""


def test_it_never_clones():
    """The third rule: a hook that fetches code runs code the repository never committed, in
    the environment that reviews it least.

    Asked of the parsed file and not of its text, because the prose *explains* the rule and a
    substring search over the whole source reads the explanation as a violation. Docstrings are
    skipped for exactly that reason; every other string literal is the program.
    """
    import ast

    tree = ast.parse(BRIDGE.read_text(encoding="utf-8"))
    # `clean=False`, because the cleaned form is dedented and would match no raw literal —
    # which silently left every docstring in the set below and failed on the prose.
    docstrings = {
        ast.get_docstring(node, clean=False)
        for node in ast.walk(tree)
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef))
    }
    literals = [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and node.value not in docstrings
    ]
    assert not [one for one in literals if "clone" in one or "http" in one], literals
    imported = {
        name.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for name in node.names
    } | {
        node.module.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    # The whole standard-library surface it is allowed: no `urllib`, no `http`, no `socket`.
    assert imported == {"__future__", "json", "os", "subprocess", "sys", "pathlib"}


def test_an_unknown_mode_is_a_usage_error(tmp_path):
    done = subprocess.run(
        [sys.executable, str(BRIDGE), "lint"], capture_output=True, check=False
    )
    assert done.returncode == 2 and b"guard|mcp" in done.stderr


# -- what `install --committed` writes ----------------------------------------


def test_the_bridge_is_copied_verbatim_and_the_declarations_name_it(tmp_path):
    """The launcher every declaration names is a path *inside* the repository, which is the
    one thing that resolves in an environment that clones no checkout."""
    from roadkeep.adopting import init
    from roadkeep.installing import install

    init(tmp_path)
    written = install(tmp_path, source=ROOT, committed=True)
    assert written.launcher == PROJECT_BRIDGE
    copied = tmp_path / PROJECT_BRIDGE
    assert copied.read_text(encoding="utf-8") == BRIDGE.read_text(encoding="utf-8")
    server = json.loads((tmp_path / ".mcp.json").read_text(encoding="utf-8"))
    assert PROJECT_BRIDGE in server["mcpServers"]["roadkeep"]["args"][0]
    settings = json.loads((tmp_path / ".claude/settings.json").read_text(encoding="utf-8"))
    assert PROJECT_BRIDGE in settings["hooks"]["PreToolUse"][0]["hooks"][0]["command"]


def test_without_the_flag_nothing_changes(tmp_path):
    # Opt-in and never the default: the exact path to the checkout is what an early adopter
    # developing against one wants, and a search is only better where there is no checkout.
    from roadkeep.adopting import init
    from roadkeep.installing import install

    init(tmp_path)
    written = install(tmp_path, source=ROOT)
    assert written.launcher != PROJECT_BRIDGE
    assert not (tmp_path / PROJECT_BRIDGE).exists()


def test_the_copy_is_refreshed_like_the_skill(tmp_path):
    # A vendored program that drifts is read with the same trust and answers with an older
    # rule, which is exactly how the reported defect survived. `--check` is what holds it.
    from roadkeep.adopting import init
    from roadkeep.installing import install, plan

    init(tmp_path)
    install(tmp_path, source=ROOT, committed=True)
    (tmp_path / PROJECT_BRIDGE).write_text("# somebody edited this\n", encoding="utf-8")
    stale = [one.path.name for one in plan(tmp_path, source=ROOT, committed=True).changing]
    assert "roadkeep-launch.py" in stale


def test_the_plugin_s_own_tree_is_not_an_adopter_of_itself():
    # RK235's narrowing, extended to the fourth surface: a copy beside the original is the
    # drift `install` exists to remove, so it is named as unwritten instead.
    from roadkeep.installing import plan

    named = dict(plan(ROOT, source=ROOT, gauging=False, committed=True).skipped)
    assert PROJECT_BRIDGE in named and "ships" in named[PROJECT_BRIDGE]


def test_uninstall_takes_the_bridge_out_with_the_rest(tmp_path):
    """`removal` reads no checkout — the wiring is recognised by this project's own entries —
    so it cannot know whether `--committed` was passed and asks the disk instead, which is the
    reading RK284 already established for what is kept."""
    from roadkeep.adopting import init
    from roadkeep.installing import install, uninstall

    init(tmp_path)
    install(tmp_path, source=ROOT, committed=True)
    assert (tmp_path / PROJECT_BRIDGE).is_file()
    uninstall(tmp_path)
    assert not (tmp_path / PROJECT_BRIDGE).exists()


def test_uninstall_on_a_project_that_never_had_one_takes_nothing(tmp_path):
    # `held=False` where the file is not there, so a plain `install` un-wires without a
    # withdrawal naming a path that never existed.
    from roadkeep.adopting import init
    from roadkeep.installing import install, removal

    init(tmp_path)
    install(tmp_path, source=ROOT)
    withdrawn = {one.path.name for one in removal(tmp_path).changing}
    assert "roadkeep-launch.py" not in withdrawn


def test_a_second_install_replaces_its_own_entry_and_does_not_append(tmp_path):
    """The bug the flag exposed. `_ours` recognised a hook group by the checkout's
    `scripts/roadkeep.py`, which a `--committed` command does not run — so a re-run appended a
    second identical group to all three events, and the guard fired twice on every turn."""
    from roadkeep.adopting import init
    from roadkeep.installing import install, plan

    init(tmp_path)
    install(tmp_path, source=ROOT, committed=True)
    install(tmp_path, source=ROOT, committed=True)
    settings = json.loads((tmp_path / ".claude/settings.json").read_text(encoding="utf-8"))
    assert [len(groups) for groups in settings["hooks"].values()] == [1, 1, 1]
    # And the second run is idempotent, which is what `--check` reporting clean means.
    assert plan(tmp_path, source=ROOT, committed=True).changing == ()


def test_un_wiring_a_committed_install_takes_the_guard_out(tmp_path):
    # The other half of the same defect: a guard nothing recognised is a guard `uninstall`
    # leaves behind, on a project told it had been un-wired.
    from roadkeep.adopting import init
    from roadkeep.installing import install, uninstall

    init(tmp_path)
    install(tmp_path, source=ROOT, committed=True)
    uninstall(tmp_path)
    assert not (tmp_path / ".claude/settings.json").exists()


def test_switching_from_a_checkout_wiring_to_a_committed_one_leaves_one_guard(tmp_path):
    # The migration an adopter actually makes, and the one that would double the hooks if
    # either spelling went unrecognised.
    from roadkeep.adopting import init
    from roadkeep.installing import install

    init(tmp_path)
    install(tmp_path, source=ROOT)
    install(tmp_path, source=ROOT, committed=True)
    settings = json.loads((tmp_path / ".claude/settings.json").read_text(encoding="utf-8"))
    assert [len(groups) for groups in settings["hooks"].values()] == [1, 1, 1]
    commands = [
        hook["command"]
        for groups in settings["hooks"].values()
        for group in groups
        for hook in group["hooks"]
    ]
    assert all(PROJECT_BRIDGE in one for one in commands), commands


# -- the variant is on the disk, not on the flag (RK1113) ---------------------


def test_a_committed_project_reports_clean_without_the_flag(tmp_path):
    """The defect, as dockerdesk reported it at acc7fc1: `--check` compared against the default
    alone, so a tree with no local edits answered "3 surface(s) differ" on every run — and the
    repair it named rewrote all three to a checkout path."""
    from roadkeep.adopting import init
    from roadkeep.installing import install, plan

    init(tmp_path)
    install(tmp_path, source=ROOT, committed=True)
    intent = plan(tmp_path, source=ROOT, gauging=False)
    assert intent.changing == ()
    assert intent.launcher == PROJECT_BRIDGE and intent.committed and intent.carried


def test_the_plain_install_no_longer_downgrades_the_wiring(tmp_path):
    """The consequence that made it worth a task rather than a wrong number: running the named
    repair is what removes the guard from the environment the bridge exists for."""
    from roadkeep.adopting import init
    from roadkeep.installing import install

    init(tmp_path)
    install(tmp_path, source=ROOT, committed=True)
    install(tmp_path, source=ROOT)
    settings = json.loads((tmp_path / ".claude/settings.json").read_text(encoding="utf-8"))
    commands = [
        hook["command"]
        for groups in settings["hooks"].values()
        for group in groups
        for hook in group["hooks"]
    ]
    assert all(PROJECT_BRIDGE in one for one in commands), commands
    assert (tmp_path / PROJECT_BRIDGE).is_file()


def test_the_session_start_notice_is_silent_on_a_committed_project(tmp_path):
    # The same answer feeds `SessionStart` (RK234), so the session opened by being told its own
    # wiring was stale — and an agent that believes it spends its first turn undoing the
    # adoption. `stale` takes no flag at all, which is why the reading had to move.
    from roadkeep.adopting import init
    from roadkeep.installing import install, stale

    init(tmp_path)
    install(tmp_path, source=ROOT, committed=True)
    assert stale(tmp_path) == ()


def test_a_bridge_nothing_references_is_not_a_committed_project(tmp_path):
    # Both halves, because either alone is another state: this is what a downgrade leaves
    # behind, and reading the file alone would report the wiring as committed while the hook
    # that runs is the checkout's.
    from roadkeep.adopting import init
    from roadkeep.installing import install, plan

    init(tmp_path)
    install(tmp_path, source=ROOT)
    (tmp_path / PROJECT_BRIDGE).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / PROJECT_BRIDGE).write_text("# left behind\n", encoding="utf-8")
    intent = plan(tmp_path, source=ROOT, gauging=False)
    assert not intent.committed and not intent.carried
    assert intent.launcher != PROJECT_BRIDGE


def test_the_flag_is_still_what_a_project_with_no_variant_asks_with(tmp_path):
    # Read off the disk means read off *a choice already made*: a project that has not made one
    # gets the default, and the flag is the only thing that moves it.
    from roadkeep.adopting import init
    from roadkeep.installing import plan

    init(tmp_path)
    asked = plan(tmp_path, source=ROOT, gauging=False, committed=True)
    assert asked.committed and not asked.carried
    assert not plan(tmp_path, source=ROOT, gauging=False).committed


def test_the_report_says_the_project_chose_it_rather_than_the_default(tmp_path, capsys):
    # The launcher line is a path, so a reader who passed no flag is told where the path came
    # from — and how to leave, which is the door a flag no longer opens by accident.
    from roadkeep.adopting import init
    from roadkeep.cli import main
    from roadkeep.installing import install

    init(tmp_path)
    install(tmp_path, source=ROOT, committed=True)
    assert main(["-C", str(tmp_path), "install", "--source", str(ROOT), "--check"]) == 0
    printed = capsys.readouterr().out
    assert PROJECT_BRIDGE in printed and "uninstall" in printed


def test_the_payload_says_which_of_the_two_answered(tmp_path, capsys):
    from roadkeep.adopting import init
    from roadkeep.cli import main
    from roadkeep.installing import install

    init(tmp_path)
    install(tmp_path, source=ROOT, committed=True)
    argv = ["-C", str(tmp_path), "install", "--source", str(ROOT), "--check", "--json"]
    assert main(argv) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["committed"] and payload["carried"] and payload["changing"] == 0


def test_a_source_that_predates_the_bridge_is_refused_by_name(tmp_path):
    """Not in `CARRIED`, which also decides whether a tree *is* the plugin: a sixth entry there
    would make an older checkout stop being recognised as one. So the file is asked for under
    the flag that needs it, and the refusal names it rather than raising an errno from a copy."""
    from roadkeep.adopting import init
    from roadkeep.installing import CARRIED, NotShipped, plan

    init(tmp_path)
    older = tmp_path / "older-roadkeep"
    for part in CARRIED:  # the real five, copied — and not the bridge
        (older / part).parent.mkdir(parents=True, exist_ok=True)
        (older / part).write_bytes((ROOT / part).read_bytes())
    # Without the flag it translates fine: the bridge is not one of the five.
    assert plan(tmp_path, source=older, gauging=False) is not None
    with pytest.raises(NotShipped) as refusal:
        plan(tmp_path, source=older, gauging=False, committed=True)
    assert PLUGIN_BRIDGE in str(refusal.value)
