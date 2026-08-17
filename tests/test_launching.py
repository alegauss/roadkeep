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
import ast
import os
import shutil
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


def test_the_vendored_directory_is_the_one_install_writes():
    """RK1193's half of the closure. `install --vendor` puts an engine in `.roadkeep/` and this
    file resolves one there, and the two names are spelled apart because this file runs before
    the package it would import exists. A rename that reached one of them would leave a pinned
    project running whatever a sibling clone is today, silently."""
    from roadkeep.installing import PROJECT_ENGINE

    assert load().VENDORED == PROJECT_ENGINE


def test_the_home_variable_is_expanded_in_both_spellings(tmp_path, monkeypatch):
    """RK1200. The harness passes `env` values through verbatim, and the spelling a project
    reaches for is the one `install` writes into every hook `command` in the same file:
    `${CLAUDE_PROJECT_DIR}/.roadkeep`. Measured on an adopting project — braces intact,
    `Path(home)` naming nothing, resolution falling through to a neighbour's working tree that
    was a version ahead and mid-refactor, with the guard running a traceback for part of a
    session. Nothing said so, because a second candidate answering looks like a choice."""
    bridge = load()
    repo = tmp_path / "repo"
    engine = repo / "vendored"
    (engine / "scripts").mkdir(parents=True)
    (engine / "scripts" / "roadkeep.py").write_text("", encoding="utf-8")
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(repo))

    for spelling in ("${CLAUDE_PROJECT_DIR}/vendored", "$CLAUDE_PROJECT_DIR/vendored"):
        monkeypatch.setenv("ROADKEEP_HOME", spelling)
        assert bridge._resolve() == engine / "scripts" / "roadkeep.py", spelling


def test_the_project_directory_is_answered_even_where_the_environment_omits_it(
    tmp_path, monkeypatch
):
    """The half a plain `expandvars` gets wrong: the harness interpolates that name into a
    command line without necessarily exporting it, and this file already knows the answer."""
    bridge = load()
    repo = tmp_path / "repo"
    (repo / ".claude" / "hooks").mkdir(parents=True)
    engine = repo / "vendored"
    (engine / "scripts").mkdir(parents=True)
    (engine / "scripts" / "roadkeep.py").write_text("", encoding="utf-8")

    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    monkeypatch.setattr(bridge, "_repo_root", lambda: repo)
    monkeypatch.setenv("ROADKEEP_HOME", "${CLAUDE_PROJECT_DIR}/vendored")
    assert bridge._resolve() == engine / "scripts" / "roadkeep.py"


def test_a_variable_nothing_resolves_is_left_as_written(tmp_path, monkeypatch):
    """Both readings fail and they fail differently: `${NOPE}/.roadkeep` names nothing and
    falls through, while an empty expansion is `/.roadkeep` — a path at the filesystem root
    that could exist and would then be run, which is this task's own defect wearing a fix."""
    bridge = load()
    repo = tmp_path / "repo"
    (repo / ".roadkeep" / "scripts").mkdir(parents=True)
    (repo / ".roadkeep" / "scripts" / "roadkeep.py").write_text("", encoding="utf-8")
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(repo))
    monkeypatch.delenv("NOPE", raising=False)

    assert bridge._expanded("${NOPE}/x") == "${NOPE}/x"
    monkeypatch.setenv("ROADKEEP_HOME", "${NOPE}/x")
    # And what answers instead is the vendored copy, not a sibling nobody chose.
    assert bridge._resolve() == repo / bridge.VENDORED / "scripts" / "roadkeep.py"


def test_a_name_that_merely_starts_with_a_known_one_is_not_substituted(monkeypatch):
    """`$CLAUDE_PROJECT_DIRECTORY` is not `$CLAUDE_PROJECT_DIR` with a suffix glued on."""
    bridge = load()
    monkeypatch.delenv("CLAUDE_PROJECT_DIRECTORY", raising=False)
    assert bridge._expanded("$CLAUDE_PROJECT_DIRECTORY/x") == "$CLAUDE_PROJECT_DIRECTORY/x"


def test_a_vendored_engine_outranks_a_sibling_and_yields_to_the_override(tmp_path, monkeypatch):
    """The order is the decision (RK1193): a copy the project vendored is one it *chose*, so it
    beats whatever `../roadkeep` happens to be — and `$ROADKEEP_HOME` still beats both, because
    a pin nobody can step over for one command is a pin that gets deleted instead of used."""
    bridge = load()
    repo = tmp_path / "repo"

    def engine_at(root: Path) -> Path:
        (root / "scripts").mkdir(parents=True)
        (root / "scripts" / "roadkeep.py").write_text("", encoding="utf-8")
        return root

    engine_at(repo / bridge.VENDORED)
    engine_at(tmp_path / "roadkeep")
    named = engine_at(tmp_path / "elsewhere")
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(repo))

    monkeypatch.delenv("ROADKEEP_HOME", raising=False)
    assert bridge._resolve() == repo / bridge.VENDORED / "scripts" / "roadkeep.py"

    monkeypatch.setenv("ROADKEEP_HOME", str(named))
    assert bridge._resolve() == named / "scripts" / "roadkeep.py"


def test_the_plugin_name_is_the_one_the_package_matches():
    from roadkeep.provenance import PLUGIN

    assert load().PLUGIN == PLUGIN


def test_the_engine_path_is_the_one_install_substitutes():
    from roadkeep.installing import LAUNCHER

    assert load().ENGINE_REL.as_posix() == LAUNCHER


# -- defer to the plugin, which is the defect (RK1108) ------------------------


def registry(
    home: Path,
    project: Path,
    *,
    name: str = "roadkeep@alegauss",
    install: Path | None = None,
) -> None:
    """A harness registry wiring one plugin to one project, as the harness writes it.

    ``install`` is the `installPath` a current harness writes and an older one does not, which
    is why it is optional here as well as there (RK1166).
    """
    path = home / "plugins" / "installed_plugins.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    row: dict[str, str] = {"projectPath": str(project), "version": "0.1.0"}
    if install is not None:
        row["installPath"] = str(install)
    path.write_text(json.dumps({"plugins": {name: [row]}}), encoding="utf-8")


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
    # `re` joined it with RK1200, and the list is asserted whole precisely so that adding one
    # is a decision somebody wrote down: it reads a variable reference out of a settings value,
    # reaches nothing and opens nothing, which is the property this test is about.
    assert imported == {"__future__", "json", "os", "re", "subprocess", "sys", "pathlib"}


# -- the sentence that says where the engine is (RK1119) -----------------------


def test_the_committed_skill_does_not_say_it_was_wired_to_a_checkout(tmp_path):
    """RK1119. `install` substitutes one fact into the skill it copies, and under `--committed`
    the clause around it was false: nothing was wired to a checkout, and the environment the
    flag exists for has none — so the one sentence a session reads before it runs anything
    named the wrong place to look for its engine."""
    from roadkeep.adopting import init
    from roadkeep.installing import PROJECT_SKILL, install

    init(tmp_path)
    install(tmp_path, source=ROOT, committed=True)
    copied = (tmp_path / PROJECT_SKILL).read_text(encoding="utf-8")
    assert f'`python "{PROJECT_BRIDGE}"` is this project\'s entry point' in copied
    assert "wired it to a checkout" not in copied
    # And it says what the launcher does instead, which is the fact a reader acts on.
    assert "finds an engine wherever this environment has one" in copied


def test_the_checkout_variant_still_says_it_was_wired_to_one(tmp_path):
    # Held so the sentence above is a variant and not a rewrite: a project pointed at a
    # checkout has one, and naming it is what RK137 was about.
    from roadkeep.adopting import init
    from roadkeep.installing import PROJECT_SKILL, install

    init(tmp_path)
    install(tmp_path, source=ROOT)
    copied = (tmp_path / PROJECT_SKILL).read_text(encoding="utf-8")
    assert "wired it to a checkout" in copied
    assert "finds an engine wherever" not in copied


def test_a_refresh_that_reads_the_disk_writes_the_committed_sentence(tmp_path):
    # The two fixes meet here (RK1113): a plain `install` on a `--committed` project keeps the
    # variant, so it must keep the sentence too — otherwise the refresh reports clean while
    # the skill it would write says the other thing.
    from roadkeep.adopting import init
    from roadkeep.installing import install, plan

    init(tmp_path)
    install(tmp_path, source=ROOT, committed=True)
    assert plan(tmp_path, source=ROOT, gauging=False).changing == ()


# -- the entry point the skill names is the one that runs (RK1116) -------------


#: The variable this helper *removes* rather than points somewhere: a project root the harness
#: states is the one route whose fallback — this file's own grandparent — is the checkout the
#: suite runs in, and no value could make that absent.
POPPED = "CLAUDE_PROJECT_DIR"


def nowhere(cwd: Path) -> dict[str, str]:
    """Every variable a resolution route reads, pointed inside ``cwd`` (RK1155).

    `bridged(home=None)` means *nothing to find*, and it used to mean it by setting one variable:
    the override. Three routes were left reading the developer's home — the registry under
    `~/.claude`, the cache under `~/.cache` — so the claim held on the single fact that this
    machine had no plugin installed. A cache appeared and route 3 answered, weeks later, with
    nothing in the launcher or the test changed.

    A function rather than a literal in the helper, because the closure below reads it: what the
    isolation covers has to be comparable against what the file actually reads.
    """
    return {
        "ROADKEEP_HOME": str(cwd / "absent"),
        "XDG_CACHE_HOME": str(cwd / "absent-cache"),
        "CLAUDE_CONFIG_DIR": str(cwd / "absent-config"),
    }


def bridged(argv: list[str], home: Path | None, cwd: Path) -> subprocess.CompletedProcess:
    """The shipped file, run as the agent runs it: an engine named, and a project to answer in."""
    env = {**os.environ, "ROADKEEP_HOME": "" if home is None else str(home)}
    env.pop(POPPED, None)
    if home is None:
        env.update(nowhere(cwd))
    return subprocess.run(
        [sys.executable, str(BRIDGE), *argv],
        capture_output=True,
        check=False,
        cwd=str(cwd),
        env=env,
    )


def test_a_verb_reaches_the_engine_this_file_resolved(tmp_path):
    """RK1116, measured on dockerdesk: the installed skill states this file as the project's
    entry point and then describes `add`, `pick`, `brief`, `lint`, `ship` — and every one of
    them exited 2 on a usage line naming the two modes only the harness calls."""
    from roadkeep.adopting import init

    init(tmp_path)
    done = bridged(["stats"], ROOT, tmp_path)
    assert done.returncode == 0, done.stderr
    assert b"total" in done.stdout


def test_the_engine_owns_the_exit_code_and_the_refusal(tmp_path):
    # This file only decides which copy answers, which is the rule the two modes already
    # keep: a verb the engine refuses is refused in the engine's own words.
    from roadkeep.adopting import init

    init(tmp_path)
    done = bridged(["nonesuch"], ROOT, tmp_path)
    assert done.returncode == 2 and b"guard|mcp" not in done.stderr


def test_a_missing_engine_is_a_refusal_and_not_a_quiet_zero(tmp_path):
    # The one rule a forwarded verb does not keep. "Unenforced beats broken" is right for a
    # hook that fires every turn and wrong here, where the exit code is read as the result.
    done = bridged(["stats"], None, tmp_path)
    assert done.returncode == 2 and b"no engine found" in done.stderr


def test_a_verb_is_answered_even_where_the_plugin_is_wired(tmp_path):
    # The other rule a forwarded verb does not keep. Standing down exists so a *hook* does not
    # double-fire (RK1189 took the server out of that sentence); a command somebody typed has
    # no second copy to double, and silence would be this file answering `pick` with nothing.
    from roadkeep.adopting import init

    init(tmp_path)
    home = tmp_path / "config"
    registry(home, tmp_path)
    env = {**os.environ, "ROADKEEP_HOME": str(ROOT), "CLAUDE_CONFIG_DIR": str(home)}
    env["CLAUDE_PROJECT_DIR"] = str(tmp_path)
    done = subprocess.run(
        [sys.executable, str(BRIDGE), "stats"],
        capture_output=True,
        check=False,
        cwd=str(tmp_path),
        env=env,
    )
    assert done.returncode == 0 and b"total" in done.stdout


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


def test_every_route_the_launcher_reads_is_one_this_suite_can_make_absent():
    """RK1155. The isolation `bridged(home=None)` claims, held against the file it isolates.

    A route added to the launcher reads a variable, falls back to the home directory, and is then
    found on any machine that has one — which is how a test asserting *no engine found* passed
    for weeks and went red the afternoon somebody installed the plugin. So the set is read off
    the launcher's own source: every `os.environ.get` in it is either pointed inside `tmp_path`
    or declared as the one that gets popped.

    Both directions, RK491's rule: a variable the launcher stops reading leaves a row here that
    fails, and a new one fails until the isolation covers it.
    """
    read = {
        node.args[0].value
        for node in ast.walk(ast.parse(BRIDGE.read_text(encoding="utf-8")))
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "get"
        and isinstance(node.func.value, ast.Attribute)
        and node.func.value.attr == "environ"
        and node.args
        and isinstance(node.args[0], ast.Constant)
    }
    assert read, "nothing in the launcher reads the environment any more"
    assert read == {*nowhere(Path("x")), POPPED}, {
        "read, not isolated": sorted(read - {*nowhere(Path("x")), POPPED}),
        "isolated, not read": sorted({*nowhere(Path("x")), POPPED} - read),
    }


def test_a_row_whose_install_was_pruned_is_a_record_and_not_a_wired_plugin(tmp_path, monkeypatch):
    """RK1166, measured in one corpus: the row pinned an old version while only three later ones
    were on disk, so this answered True, the launcher stood down, and the plugin it deferred to
    could not load — both guards absent at once, through the reading written to stop that.

    Three rows and one rule: a live install binds, a pruned one does not, and a row that names
    none is unchanged, there being nothing to check and an identity claim that still holds.
    """
    bridge = load()
    home, project = tmp_path / "config", tmp_path / "project"
    project.mkdir()
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(home))

    live = tmp_path / "cache" / "0.1.727"
    live.mkdir(parents=True)
    registry(home, project, install=live)
    assert bridge._plugin_is_wired(project) is True

    registry(home, project, install=tmp_path / "cache" / "0.1.285")  # pruned by the harness
    assert bridge._plugin_is_wired(project) is False

    registry(home, project)  # an older harness, which writes no path
    assert bridge._plugin_is_wired(project) is True


def test_the_guard_runs_where_the_plugin_it_would_defer_to_cannot_load(tmp_path):
    """The end of it, and why the row alone was not enough: what this file decides is whether
    **anything** guards the write. Asserted on the answer a `PreToolUse` carries rather than on
    the predicate, because that is the fact a session gets — measured as an `Edit` on a governed
    file that was not refused, reached the tool, and failed on its own arguments instead.
    """
    from roadkeep.adopting import init

    init(tmp_path)
    home = tmp_path / "config"
    registry(home, tmp_path, install=tmp_path / "cache" / "gone")
    environment = {
        **os.environ,
        "CLAUDE_PROJECT_DIR": str(tmp_path),
        "CLAUDE_CONFIG_DIR": str(home),
        "ROADKEEP_HOME": str(ROOT),
    }
    payload = json.dumps(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Edit",
            "tool_input": {"file_path": str(tmp_path / "docs" / "ROADMAP.md")},
        }
    )
    done = subprocess.run(
        [sys.executable, str(BRIDGE), "guard"],
        input=payload.encode("utf-8"),
        capture_output=True,
        env=environment,
        check=False,
    )
    assert done.returncode == 0
    assert b"deny" in done.stdout, done.stdout


# -- a checkout that does not parse (RK1179) ----------------------------------


def unparsable(tmp_path: Path) -> Path:
    """A copy of the engine whose `backlog.py` has one stray indent in it — an edit in progress,
    which is the state this was met in from another repository."""
    engine = tmp_path / "roadkeep"
    shutil.copytree(ROOT / "src", engine / "src")
    shutil.copytree(ROOT / "scripts", engine / "scripts")
    broken = engine / "src" / "roadkeep" / "backlog.py"
    lines = broken.read_text(encoding="utf-8").split("\n")
    at = next(i for i, line in enumerate(lines) if line.startswith(("def ", "class ")))
    lines.insert(at, "    stray = 1")
    broken.write_text("\n".join(lines), encoding="utf-8")
    return engine / "scripts" / "roadkeep.py"


def test_a_command_gets_the_tools_own_sentence_and_not_a_traceback(tmp_path):
    """RK1179, met from another repository mid-task: a `budget` call came back as a nine-line
    traceback ending `IndentationError: unexpected indent`. Nothing in it said which checkout
    answered, that the checkout is what is wrong rather than the call, or that the caller's own
    files were untouched — the one path where this tool stopped explaining itself.

    Exit 2 and not 1: the command did not run, and 1 in this tool is a verdict about the
    repository's own contents (RK86).
    """
    ran = subprocess.run(
        [sys.executable, str(unparsable(tmp_path)), "list"],
        capture_output=True, text=True, cwd=str(ROOT), check=False,
    )
    assert ran.returncode == 2
    assert "Traceback" not in ran.stderr
    said = ran.stderr
    assert "does not parse, so no command ran" in said
    # The three facts a caller cannot get anywhere else: which copy, which file, and that their
    # own files are untouched.
    assert "engine" in said and str(tmp_path) in said
    assert "backlog.py:" in said and "unexpected indent" in said
    assert "your own files were not read" in said
    # And the neighbouring read is named, which is the shape every refusal here has (RK14/15).
    assert "roadkeep engines" in said


def test_the_hook_still_degrades_to_unenforced(tmp_path):
    """The launcher's own second rule, which this must not break: a hook that fires on every turn
    degrades to *unenforced* and never to a broken session — the harness reads a non-zero exit as
    the hook having failed, so a refusal printed there takes the turn down with it."""
    ran = subprocess.run(
        [sys.executable, str(unparsable(tmp_path)), "guard"],
        input='{"tool_name":"Edit","tool_input":{"file_path":"docs/ROADMAP.md"}}',
        capture_output=True, text=True, cwd=str(ROOT), check=False,
    )
    assert ran.returncode == 0
    assert ran.stdout == "" and "Traceback" not in ran.stderr


# -- the server stands down for nobody (RK1189) -------------------------------

#: One handshake, which is all it takes to tell a server from a process that exited.
HANDSHAKE = json.dumps(
    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {"protocolVersion": "2024-11-05", "capabilities": {}},
    }
)


def served(argv: list[str], home: Path | None, cwd: Path, config: Path | None = None):
    """The shipped file in ``mcp`` mode, driven the way `.mcp.json` starts it."""
    env = {**os.environ, "ROADKEEP_HOME": "" if home is None else str(home)}
    env[POPPED] = str(cwd)
    if home is None:
        env.update(nowhere(cwd))
    if config is not None:
        env["CLAUDE_CONFIG_DIR"] = str(config)
    return subprocess.run(
        [sys.executable, str(BRIDGE), *argv],
        input=f"{HANDSHAKE}\n".encode("utf-8"),
        capture_output=True,
        check=False,
        cwd=str(cwd),
        env=env,
    )


def test_the_server_answers_where_the_plugin_is_wired(tmp_path):
    """RK1189, measured in Shio with everything installed correctly: the deferral exited 0 before
    a frame was read, the harness read that as the server having failed, and — both entries being
    named `roadkeep` — the session it showed `✗ failed` in had no roadkeep tools at all.

    Asserted on a frame coming back rather than on the predicate, because *speaks the protocol*
    is the only thing an exit here cannot also mean.
    """
    from roadkeep.adopting import init

    init(tmp_path)
    home = tmp_path / "config"
    registry(home, tmp_path)  # the plugin, wired for this very project
    done = served(["mcp"], ROOT, tmp_path, config=home)
    assert done.returncode == 0, done.stderr
    answer = json.loads(done.stdout.splitlines()[0])
    assert answer["id"] == 1 and "serverInfo" in answer["result"]


def test_a_missing_engine_is_a_named_refusal_on_the_server_too(tmp_path):
    """The other rule it keeps neither of. A server the harness will mark failed regardless is
    one whose log should say why: exit 0 and silence there is a crash with no cause in it."""
    done = served(["mcp"], None, tmp_path)
    assert done.returncode == 2 and b"no engine found" in done.stderr
