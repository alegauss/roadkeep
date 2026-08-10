"""Telling one engine from another (RK79).

The defect this answers was found by hand: two `src/roadkeep/` trees, 14 files apart, both
answering `0.1.0`. What is asserted here is the property that would have made that a
five-second question instead of a session — that the answer names *files*, not a release.

The cases worth holding are the degraded ones. A wheel in `site-packages` has no commit, a
machine without git has no commit, and a package directory sitting under an unrelated
checkout has a HEAD that describes somebody else's work — the last is the one that would
lie rather than say nothing, so it gets a repository built for it.

The same two facts answer a second question (RK155): whether the modules moved after the
process imported them, which is what makes `unknown key 'claims'` legible on a server started
a build ago. Asserted on an :class:`Engine` built over a `tmp_path` rather than on this one —
the running process's own mtimes are whatever the checkout happens to be, so a test reading
them would pass or fail on when the files were last saved.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import roadkeep
from conftest import git_commit, git_init, since_import
from roadkeep.provenance import (
    MODIFIED,
    UNTRACKED,
    Engine,
    engine,
    invocation,
    persisted,
    raised_in,
    witness,
    witnessed,
)

HERE = Path(__file__).resolve().parents[1]


# -- what it reports here ----------------------------------------------------


def test_the_engine_names_the_directory_its_modules_were_imported_from():
    # The half that separates a plugin cache from a checkout, and the half that is always
    # available: `__file__` needs no subprocess and no repository.
    assert engine().home == Path(roadkeep.__file__).resolve().parent
    assert engine().home == HERE / "src" / "roadkeep"


def test_the_version_is_the_packages_and_not_a_second_literal():
    assert engine().version == roadkeep.__version__


def test_this_checkout_reports_the_commit_it_is_at(checkout):
    if engine().commit is None:
        pytest.skip("this tree is not a checkout git can place")
    # The engine answers once per process (below) and `rev-parse` answers now, so a commit
    # landing between them is the one difference this must not read as a defect (RK263).
    checkout.steady(head=True)
    assert len(engine().commit) >= 7
    assert engine().commit in subprocess.run(
        ["git", "-C", str(HERE), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def test_the_answer_is_computed_once_per_process():
    # A git call on the write path would be the tool spending its own budget to say what
    # it already knows, so the cache is the guarantee and not an optimisation.
    assert engine() is engine()


# -- how it reads ------------------------------------------------------------


def test_the_line_leads_with_the_release_number_an_adopter_pins():
    assert str(engine()).startswith(f"roadkeep {roadkeep.__version__} (")


def test_edited_files_are_marked_because_the_commit_then_describes_neither_tree():
    home = Path("cache") / "roadkeep"
    described = Engine(version="0.1.0", home=home, commit="1962ac3", modified=True)
    assert described.revision == f"1962ac3 {MODIFIED}"
    assert str(described) == f"roadkeep 0.1.0 (1962ac3 modified, {home})"


def test_a_tree_git_cannot_place_still_answers_with_its_directory():
    home = Path("site-packages") / "roadkeep"
    unplaced = Engine(version="0.1.0", home=home, commit=None)
    assert unplaced.revision == UNTRACKED
    assert str(unplaced) == f"roadkeep 0.1.0 ({UNTRACKED}, {home})"


# -- the code that moved under the process (RK155) ----------------------------


def test_a_tree_nothing_touched_is_not_stale(tmp_path):
    # The whole value of the note is that it is silent when there is nothing to say: one that
    # fires on every refusal is one an agent learns to skip past.
    home = tmp_path / "roadkeep"
    home.mkdir()
    (home / "config.py").write_text("x = 1\n", encoding="utf-8")
    os.utime(home / "config.py", (since_import(-60), since_import(-60)))
    assert Engine(version="0.1.0", home=home, commit=None).stale == ()


def test_a_module_written_after_the_import_is_named(tmp_path):
    # The measured failure: `[claims] held` reached `roadkeep.toml` and `config.py` in one
    # commit, and every MCP write then refused a key the file legitimately declared.
    home = tmp_path / "roadkeep"
    home.mkdir()
    for name in ("config.py", "schema.py", "notes.txt"):
        (home / name).write_text("x = 1\n", encoding="utf-8")
        os.utime(home / name, (since_import(300), since_import(300)))
    # Only this package's own modules: a fixture or a `.pyc` beside them says nothing about
    # the code that answered.
    assert Engine(version="0.1.0", home=home, commit=None).stale == ("config.py", "schema.py")


def test_staleness_is_read_now_and_not_cached_like_the_identity(tmp_path):
    # `engine()` is cached per process because identity cannot change; this can, and a server
    # that decided at startup whether it was current would be answering the wrong question.
    home = tmp_path / "roadkeep"
    home.mkdir()
    described = Engine(version="0.1.0", home=home, commit=None)
    assert described.stale == ()
    (home / "serving.py").write_text("x = 1\n", encoding="utf-8")
    os.utime(home / "serving.py", (since_import(300), since_import(300)))
    assert described.stale == ("serving.py",)


def test_the_shell_invocation_is_the_one_this_machine_has(tmp_path, monkeypatch):
    # RK254: every message offering a shell command spelled `roadkeep <verb>` literally, and
    # RK57's own finding is that the console script exists only after a `pip install` that put
    # its directory on PATH — so on the machine most likely to read a denial it was advice that
    # answers `command not found`. Three answers, most specific first, each one observed.
    home = tmp_path / "tree" / "src" / "roadkeep"
    home.mkdir(parents=True)
    monkeypatch.setattr("roadkeep.provenance.engine", lambda: Engine("0.1.0", home, None))

    # The console script, where a PATH lookup finds it — nothing else is offered over that.
    # No clear before this one: `conftest._volatile_caches` empties it around every test (RK268),
    # and the clears that stay below are re-derivations after a patch rather than cleanup.
    monkeypatch.setattr("roadkeep.provenance.shutil.which", lambda name: f"/bin/{name}")
    assert invocation() == "roadkeep"

    # Absent, the launcher this package ships beside itself (RK57), if it is on disk.
    monkeypatch.setattr("roadkeep.provenance.shutil.which", lambda name: None)
    launcher = tmp_path / "tree" / "scripts" / "roadkeep.py"
    launcher.parent.mkdir(parents=True)
    launcher.write_text("x = 1\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path / "tree")
    invocation.cache_clear()
    # Relative to the working directory, because an absolute path is a message about one machine
    # — and with forward slashes, because the shell it is copied into reads `\` as an escape.
    assert invocation() == "python scripts/roadkeep.py"

    # And with neither, the module path, which is right whenever the package imports at all.
    launcher.unlink()
    invocation.cache_clear()
    assert invocation() == "python -m roadkeep.cli"


def test_a_stored_invocation_is_absolute_and_names_what_ends_it(tmp_path, monkeypatch):
    # RK255: `merge register` prints a value that lands in `.git/config`, and git executes it at
    # merge time from a shell nobody chose. Both of the answers above are wrong once stored — a
    # PATH name is per-shell and the launcher is spelled relative to a working directory that
    # does not outlive the process — so the same three answers, resolved, each with its expiry.
    home = tmp_path / "tree" / "src" / "roadkeep"
    home.mkdir(parents=True)
    monkeypatch.setattr("roadkeep.provenance.engine", lambda: Engine("0.1.0", home, None))
    console = tmp_path / "bin" / "roadkeep"
    console.parent.mkdir(parents=True)
    console.write_text("x = 1\n", encoding="utf-8")

    monkeypatch.setattr("roadkeep.provenance.shutil.which", lambda name: str(console))
    stored = persisted()
    assert stored.command == console.resolve().as_posix()
    assert Path(stored.command).is_absolute() and stored.invalidated_by

    # The launcher, absolute — and not the relative spelling `invocation` uses, even though the
    # working directory is the one it would have been relative to.
    monkeypatch.setattr("roadkeep.provenance.shutil.which", lambda name: None)
    launcher = tmp_path / "tree" / "scripts" / "roadkeep.py"
    launcher.parent.mkdir(parents=True)
    launcher.write_text("x = 1\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path / "tree")
    persisted.cache_clear()
    stored = persisted()
    assert stored.command == f"python {launcher.resolve().as_posix()}"
    assert "plugin update" in stored.invalidated_by

    # And with neither, the module path — which never refuses, because a `merge register` that
    # failed here would send its author back to the hand edit the driver exists to stop.
    launcher.unlink()
    persisted.cache_clear()
    stored = persisted()
    assert stored.command == "python -m roadkeep.cli"
    assert home.parent.as_posix() in stored.invalidated_by


def test_a_stored_path_holding_a_space_is_quoted_for_the_shell_git_runs(tmp_path, monkeypatch):
    # The value is nested inside the double-quoted argument of a `git config` line, so the quote
    # that survives there is the single one — a second `"` would end the value at the space.
    home = tmp_path / "tree" / "src" / "roadkeep"
    home.mkdir(parents=True)
    console = tmp_path / "Program Files" / "roadkeep"
    console.parent.mkdir(parents=True)
    console.write_text("x = 1\n", encoding="utf-8")
    monkeypatch.setattr("roadkeep.provenance.engine", lambda: Engine("0.1.0", home, None))
    monkeypatch.setattr("roadkeep.provenance.shutil.which", lambda name: str(console))
    stored = persisted()
    assert stored.command.startswith("'") and stored.command.endswith("'")
    assert '"' not in stored.command and "\\" not in stored.command


#: Every string constant in the package that spells `roadkeep <subcommand>` and is **not** an
#: invocation a reader runs, with the reason it keeps the literal (RK256). An inventory and not a
#: blanket exemption: this defect reached ten sites because nothing counted them, and a docstring
#: rule would have exempted the two that print.
KEPT_LITERAL = {
    # Provenance written into a file that gets committed: a machine-specific path there would
    # describe one checkout rather than the command shape that regenerates the artefact.
    ("exporting.py", "roadkeep export"),
    # A GitHub Actions step *name*, in generated YAML. CI reaches the tool by `uvx`, and the
    # label is what a reader scans a workflow log for.
    ("installing.py", "roadkeep lint"),
}

#: Emptied by RK255: `merge register` printed a value stored in `.git/config` and executed by
#: git, and now derives it through :func:`~roadkeep.provenance.persisted`. Kept as an empty set
#: rather than deleted, because the next site that has to derive before it can ship is listed
#: here first — the coupling that made this one fail a test instead of a merge.
PENDING_LITERAL: set[tuple[str, str]] = set()


def _spelled_literally() -> set[tuple[str, str]]:
    """Where a string constant in the package names `roadkeep <subcommand>` (RK256).

    Over the *source* and not over rendered output, because the assertion is about what a future
    message may contain: rendering every message needs every message's arguments, and the site
    that reintroduces the literal is the one no test rendered yet.

    Docstrings are excluded by `ast.get_docstring`'s own positions rather than by a heuristic —
    prose for a reader of the source is where `roadkeep lint` is the right name for the command.
    """
    import ast

    from roadkeep.serving import _parsers

    verbs = sorted({path.split()[0] for path in _parsers()})
    pattern = re.compile(r"roadkeep (" + "|".join(re.escape(verb) for verb in verbs) + r")\b")
    found: set[tuple[str, str]] = set()
    for module in sorted((HERE / "src" / "roadkeep").glob("*.py")):
        tree = ast.parse(module.read_text(encoding="utf-8"))
        docstrings = {
            id(node.body[0].value)
            for node in ast.walk(tree)
            if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
            and ast.get_docstring(node) is not None
        }
        for node in ast.walk(tree):
            if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
                continue
            if id(node) in docstrings:
                continue
            found |= {(module.name, match.group(0)) for match in pattern.finditer(node.value)}
    return found


def test_no_message_spells_an_invocation_it_did_not_derive():
    # The hold RK256 exists for: ten sites across four modules printed `roadkeep <verb>` before
    # anybody counted them, so what is asserted is the *inventory* rather than the fix — a new
    # message naming a command a reader runs fails here instead of in a session.
    assert _spelled_literally() == KEPT_LITERAL | PENDING_LITERAL


def test_the_kept_literals_are_still_there_to_be_kept():
    # An inventory whose entries went away would pass the test above by being empty on both
    # sides, which is the one way this can stop asserting anything.
    modules = {module for module, _ in _spelled_literally()}
    assert modules == {module for module, _ in KEPT_LITERAL | PENDING_LITERAL}


def test_which_wiring_is_answering_is_read_from_where_the_code_lives(tmp_path):
    # RK246: a patch bump reloads a plugin and not a `.mcp.json` server, so the remedy a note
    # names depends on which of the two started this process — and the two differ in exactly
    # this, the plugin's copy being a cache elsewhere and a checkout's sitting under the root.
    root = tmp_path / "project"
    inside = Engine(version="0.1.0", home=root / "src" / "roadkeep", commit=None)
    assert inside.carried_by(root)
    # The cache: beside the project, above it, and the root itself are all the plugin's case.
    for home in (tmp_path / "cache" / "roadkeep", tmp_path / "roadkeep", root):
        assert not Engine(version="0.1.0", home=home, commit=None).carried_by(root)


def test_a_directory_that_cannot_be_read_is_not_evidence(tmp_path):
    # Every other failure in this package allows; a provenance note is the last place to
    # start raising, because it is read only when something has already gone wrong.
    assert Engine(version="0.1.0", home=tmp_path / "gone", commit=None).stale == ()


# -- the case that would lie -------------------------------------------------


def _import_from(tree: Path, code: str) -> str:
    finished = subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(tree),
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PYTHONPATH": str(tree)},
    )
    assert finished.returncode == 0, finished.stderr
    return finished.stdout.strip()


def test_a_copy_under_someone_elses_repository_borrows_no_commit_from_it(tmp_path):
    """An installed package nothing tracks must say `untracked`, not that repo's HEAD.

    Real: a wheel unpacked into a virtualenv inside a project checkout. `rev-parse` alone
    answers happily there, and the answer describes the project rather than the engine.
    """
    git_init(tmp_path)
    (tmp_path / "unrelated.txt").write_text("someone else's work\n", encoding="utf-8")
    git_commit(tmp_path, "theirs")

    # The whole package, as a wheel would land it: nothing about this copy is special
    # except that the repository around it has never heard of it.
    shutil.copytree(
        HERE / "src" / "roadkeep",
        tmp_path / "roadkeep",
        ignore=shutil.ignore_patterns("__pycache__"),
    )

    printed = _import_from(
        tmp_path, "from roadkeep.provenance import engine; print(engine().revision)"
    )
    assert printed == UNTRACKED


# -- which modules decided a refusal (RK267) ---------------------------------


def test_the_modules_that_decided_a_refusal_are_read_off_its_traceback(tmp_path):
    # The half `stale` cannot supply, on the refusal §RK267 measured. An mtime says a file
    # moved; this says which files were executing when the refusal was decided, and only the
    # two together answer whether the drift reaches the verb that refused.
    named = _refusing(tmp_path)
    # Every package frame and not only the raiser: `schema.py` owns the limit and `authoring.py`
    # is the verb it refused, and both decided this. Naming one would put the note back to
    # guessing — and neither `cli.py` nor `merging.py` is here, which is the whole finding.
    assert named == ("authoring.py", "schema.py")


def test_the_frames_read_outermost_first_as_a_printed_traceback_has_them(tmp_path):
    # The order is the traceback's own and not a sort, so a reader comparing the note against a
    # stack trace is reading the same sequence rather than a rearrangement of it.
    assert _refusing(tmp_path).index("authoring.py") == 0


def _refusing(tmp_path: Path) -> tuple[str, ...]:
    """What a `why.too-long` witnesses — the RK255 case, provoked through the real verb."""
    from roadkeep.authoring import add
    from roadkeep.config import Config

    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\n', encoding="utf-8"
    )
    (tmp_path / "ROADMAP.md").write_text("## Block A — The model\n", encoding="utf-8")
    try:
        add(Config.discover(tmp_path), block="A", symptom="s", why="w" * 5000)
    except Exception as error:  # noqa: BLE001 - the type is the verb's, not this test's
        return raised_in(error)
    pytest.fail("the schema accepted a why no limit allows")


def test_a_frame_that_is_not_a_file_on_disk_is_not_evidence_of_anything():
    # `exec` and a REPL give frames whose filename is `<string>`. A provenance note is the
    # last place to start raising, which is `stale`'s own rule one function over.
    try:
        exec(compile("raise ValueError('x')", "<string>", "exec"), {})
    except ValueError as error:
        # This test's own frame is under `tests/`, not under the package, so nothing is named.
        assert raised_in(error) == ()


def test_nothing_witnessed_is_not_the_same_as_nothing_decided_here():
    # The distinction the reporting surface turns on: `None` means relevance is unknown and the
    # full list is what there is to say, `()` means the refusal was decided outside this package.
    witness(None)
    assert witnessed() is None
    try:
        raise ValueError("raised by this test, which is not a module of this package")
    except ValueError as error:
        witness(error)
    assert witnessed() == ()


# -- the second engine: the plugin the harness wired to this project (RK415) --


def registry(config_dir: Path, rows: object) -> None:
    """The harness's own file, written where `CLAUDE_CONFIG_DIR` points this process."""
    import json

    path = config_dir / "plugins" / "installed_plugins.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows), encoding="utf-8")


def wired(config_dir: Path, project: Path, version: str = "0.1.285") -> None:
    registry(
        config_dir,
        {
            "version": 2,
            "plugins": {
                "roadkeep@alegauss": [
                    {
                        "scope": "project",
                        # As the harness spells it, which on Windows is not how a config
                        # names the same directory — the compare is on resolved paths.
                        "projectPath": str(project),
                        "installPath": str(config_dir / "cache" / version),
                        "version": version,
                        "gitCommitSha": "34523d028e553f7a9acf2e69e878382f88e7d084",
                    }
                ]
            },
        },
    )


def test_the_plugin_wired_to_this_project_is_read_back(tmp_path, monkeypatch):
    from roadkeep.provenance import installed

    project = tmp_path / "project"
    project.mkdir()
    wired(tmp_path / "config", project)
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "config"))

    found = installed(project)
    assert found is not None
    assert found.version == "0.1.285" and found.scope == "project"
    # Short, because the registry stores the full sha and no other revision here is 40 wide.
    assert found.revision == "34523d0"


def test_a_project_the_registry_does_not_name_has_no_plugin(tmp_path, monkeypatch):
    from roadkeep.provenance import installed

    wired(tmp_path / "config", tmp_path / "project")
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "config"))
    # Every tree served by a checkout alone. Not a defect, and not an error either.
    assert installed(tmp_path / "elsewhere") is None


def test_a_registry_naming_another_plugin_answers_about_this_one(tmp_path, monkeypatch):
    from roadkeep.provenance import installed

    project = tmp_path / "project"
    project.mkdir()
    registry(
        tmp_path / "config",
        {"plugins": {"something-else@alegauss": [{"projectPath": str(project), "version": "9.9"}]}},
    )
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "config"))
    assert installed(project) is None


def test_a_registry_this_cannot_parse_is_not_worth_failing_a_write_over(tmp_path, monkeypatch):
    from roadkeep.provenance import installed

    path = tmp_path / "config" / "plugins" / "installed_plugins.json"
    path.parent.mkdir(parents=True)
    path.write_text("{ not json", encoding="utf-8")
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "config"))
    assert installed(tmp_path) is None


def test_no_registry_at_all_is_the_same_silence(tmp_path, monkeypatch):
    from roadkeep.provenance import installed

    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "nowhere"))
    assert installed(tmp_path) is None
