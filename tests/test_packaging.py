"""What has to be true for `uvx roadkeep` to be a real answer (RK19).

Distribution is the difference between a standard and a script in one repository, and its
failures are the quiet kind: nothing here breaks a developer's checkout, so every one of
them is found by the first stranger who installs the package. So the metadata is asserted
rather than reviewed, and the assertions are the four that have actually gone wrong:

* **The version is one fact.** It was written in `pyproject.toml` *and* in the module, and
  a number stated twice is two numbers eventually. The build now reads the module, and the
  test is that nothing put the literal back.
* **The dependency list is empty.** `agents.md` and the README both claim zero runtime
  dependencies, and a claim in prose is a claim that gets relaxed by a convenient import.
  This is the same argument as `[budgets]` (RK30): the sentence moves into the gate.
* **Everything is packaged.** A module added to a subdirectory without `__init__.py` is
  found by pytest — which reads `src/` off `pythonpath` — and missing from the wheel.
* **The entry point resolves.** `roadkeep = "roadkeep.cli:main"` is a string until
  something imports it, and renaming `main` is a rename the test suite otherwise passes.

Read with `tomllib` and never by regex: the file is TOML, and a second reading of it here
would be a second reading that can disagree with the builder's.
"""

from __future__ import annotations

import os
import re
import tomllib
from importlib import import_module
from pathlib import Path

import pytest

from conftest import git, git_commit, git_init
from surface import modules

import roadkeep
from roadkeep.history import git_available

HERE = Path(__file__).resolve().parents[1]
PYPROJECT = HERE / "pyproject.toml"
PACKAGE = HERE / "src" / "roadkeep"

#: PEP 440, the subset a release is allowed to be. A local version or a `.dev` suffix is a
#: build nobody should be able to tag: PyPI takes the number once and forever.
_RELEASE = re.compile(r"^[0-9]+(\.[0-9]+)*((a|b|rc)[0-9]+)?$")


def metadata() -> dict:
    with PYPROJECT.open("rb") as handle:
        return tomllib.load(handle)


# -- the version is one fact -------------------------------------------------


def test_the_version_is_declared_dynamic_and_not_written_twice() -> None:
    data = metadata()
    assert "version" not in data["project"], (
        "a literal version here is a second number that will disagree with the module's"
    )
    assert data["project"]["dynamic"] == ["version"]
    assert data["tool"]["setuptools"]["dynamic"]["version"] == {
        "attr": "roadkeep.__version__"
    }


def test_the_version_is_one_pypi_would_take() -> None:
    assert _RELEASE.match(roadkeep.__version__), roadkeep.__version__


def test_the_builder_reads_the_same_number_the_module_states(checkout) -> None:
    """The `attr` above resolved statically, which is the only way it is read at build."""
    checkout.steady("src/roadkeep/__init__.py")
    source = (PACKAGE / "__init__.py").read_text(encoding="utf-8")
    found = re.findall(r'^__version__ = "([^"]+)"$', source, flags=re.MULTILINE)
    assert found == [roadkeep.__version__]


# -- the number moves on every commit (RK153) --------------------------------


def test_a_commit_bumps_the_patch_version() -> None:
    """Claude Code re-reads an installed plugin per *version*, so between two releases a
    number that never moves is a session running code nobody can see. The hook is in the
    tree and not in `.git/hooks`, which a clone does not carry — and it calls the release's
    own script, so the two files that state the number stay one fact."""
    hook = HERE / ".githooks" / "pre-commit"
    assert hook.is_file(), "the hook a clone carries: git config core.hooksPath .githooks"
    body = hook.read_text(encoding="utf-8")
    assert "scripts/bump_version.py" in body and "--level patch" in body
    # Never blocks: a missing interpreter costs a plugin refresh, a refused commit costs the
    # session — so every path out of it is a zero.
    assert "exit 1" not in body


def clone_of_the_hook(root: Path) -> None:
    """The smallest checkout the hook runs in: the three files that state the number, the
    bumper they are written by, and the hook itself on `core.hooksPath`.

    Three since RK1011: `bump_version` compares each against the index and treats a file it
    cannot find as "nothing to compare against", so a clone missing one silently stops
    staging the bump — which is this fixture reporting that the hook broke when it did not.
    """
    import shutil
    import subprocess

    for relative in (
        "scripts/bump_version.py",
        "src/roadkeep/__init__.py",
        ".claude-plugin/plugin.json",
        "editor/package.json",
    ):
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(HERE / relative, target)
    (root / ".githooks").mkdir()
    shutil.copy2(HERE / ".githooks" / "pre-commit", root / ".githooks" / "pre-commit")

    git_init(root)
    # The one setting this fixture is actually about: the hook path is what it asserts on.
    git(root, "config", "core.hooksPath", ".githooks")
    git_commit(root, "chore: bootstrap")


@pytest.mark.skipif(not git_available(), reason="git is not on PATH")
def test_the_bump_is_not_staged_over_an_edit_the_hook_did_not_write(tmp_path) -> None:
    """RK320, measured: another agent's manifest edit sat unstaged, the hook staged the whole
    file to write the number into it, and the edit landed under a subject about something
    else. Whichever way the number moves, what a commit carries is what somebody staged."""
    import json
    import subprocess

    clone_of_the_hook(tmp_path)
    manifest = tmp_path / ".claude-plugin" / "plugin.json"
    at_head = json.loads(
        subprocess.run(
            ["git", "-C", str(tmp_path), "show", "HEAD:.claude-plugin/plugin.json"],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        ).stdout
    )["version"]
    foreign = manifest.read_text(encoding="utf-8").replace('"version"', '"foreign-marker"', 1)
    manifest.write_text(foreign, encoding="utf-8")

    (tmp_path / "unrelated.txt").write_text("a commit about something else\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(tmp_path), "add", "--", "unrelated.txt"], check=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "commit", "--quiet", "-m", "fix: something else"],
        check=True,
        capture_output=True,
    )

    committed = subprocess.run(
        ["git", "-C", str(tmp_path), "show", "HEAD:.claude-plugin/plugin.json"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout
    assert "foreign-marker" not in committed, "the hook staged an edit nobody declared"
    # And the bump still reached the working tree: the plugin a session loads is the point.
    assert "foreign-marker" in manifest.read_text(encoding="utf-8")
    # Neither file alone either: the number the commit carries is still the one before it.
    assert json.loads(committed)["version"] == at_head


@pytest.mark.skipif(not git_available(), reason="git is not on PATH")
def test_a_clean_tree_still_carries_the_bump_into_the_commit(tmp_path) -> None:
    """The refusal above is a fallback, not the path: with nothing else in either file the
    number moves in the commit, which is what RK153 asked the hook for."""
    import json
    import subprocess

    clone_of_the_hook(tmp_path)
    before = json.loads((tmp_path / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))

    (tmp_path / "unrelated.txt").write_text("a commit of its own\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(tmp_path), "add", "--", "unrelated.txt"], check=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "commit", "--quiet", "-m", "feat: a change"],
        check=True,
        capture_output=True,
    )

    for relative in (".claude-plugin/plugin.json", "src/roadkeep/__init__.py"):
        shown = subprocess.run(
            ["git", "-C", str(tmp_path), "show", f"HEAD:{relative}"],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        ).stdout
        assert before["version"] not in shown, relative


def _version_at_head(root: Path) -> str:
    import json
    import subprocess

    return json.loads(
        subprocess.run(
            ["git", "-C", str(root), "show", "HEAD:.claude-plugin/plugin.json"],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        ).stdout
    )["version"]


def _commit(root: Path, name: str) -> None:
    import subprocess

    (root / name).write_text(f"{name}\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(root), "add", "--", name], check=True)
    subprocess.run(
        ["git", "-C", str(root), "commit", "--quiet", "-m", f"feat: {name}"],
        check=True,
        capture_output=True,
    )


@pytest.mark.skipif(not git_available(), reason="git is not on PATH")
def test_the_hooks_own_unstaged_bump_does_not_refuse_the_next_one(tmp_path) -> None:
    """RK398, measured over eight commits: RK320's guard writes the bump into the working
    tree and then reads that write back as somebody else's edit, so once the two files are
    dirty nothing is ever staged again. The checkout reached 0.1.392 and HEAD said 0.1.388.

    What makes an edit foreign is the difference being wider than the number, so a tree
    holding nothing but a bump this hook could not stage is still its own."""
    import subprocess
    import sys

    clone_of_the_hook(tmp_path)
    # The state another session leaves behind: both files bumped, neither staged.
    subprocess.run(
        [sys.executable, str(tmp_path / "scripts" / "bump_version.py"), "--level", "patch"],
        check=True,
        capture_output=True,
    )

    numbers = [_version_at_head(tmp_path)]
    for name in ("first.txt", "second.txt"):
        _commit(tmp_path, name)
        numbers.append(_version_at_head(tmp_path))
    # Three distinct numbers: the second commit is the one that used to carry the first's.
    assert len(set(numbers)) == 3, numbers


@pytest.mark.skipif(not git_available(), reason="git is not on PATH")
def test_the_number_a_commit_carries_follows_the_one_before_it(tmp_path) -> None:
    """Derived from the index and never from the working tree (RK398): a checkout that ran
    ahead is put back on the sequence the commits are in, rather than committing the drift."""
    import subprocess
    import sys

    clone_of_the_hook(tmp_path)
    at_head = _version_at_head(tmp_path)
    for _ in range(3):  # a tree three bumps ahead of anything committed
        subprocess.run(
            [sys.executable, str(tmp_path / "scripts" / "bump_version.py"), "--level", "patch"],
            check=True,
            capture_output=True,
        )

    _commit(tmp_path, "a-change.txt")
    major, minor, patch = (int(part) for part in at_head.split("."))
    assert _version_at_head(tmp_path) == f"{major}.{minor}.{patch + 1}"


def test_the_bumper_moves_both_files_and_nothing_else(tmp_path, checkout) -> None:
    """`--dry-run` is asserted rather than the write: this repository's own version is not a
    fixture, and a test that bumped it would put its own number in the next commit."""
    import subprocess
    import sys

    # The script reads the module off disk and this compares against the imported constant, so
    # a bump landing mid-run makes both readings right and the comparison meaningless (RK263).
    checkout.steady("src/roadkeep/__init__.py")

    finished = subprocess.run(
        [sys.executable, str(HERE / "scripts" / "bump_version.py"), "--level", "patch", "--dry-run"],
        capture_output=True,
        text=True,
        check=True,
        cwd=tmp_path,
    )
    major, minor, patch = (int(part) for part in roadkeep.__version__.split(".")[:3])
    assert finished.stdout.strip().endswith(f"-> {major}.{minor}.{patch + 1}")


# -- the claims that live in prose everywhere else ---------------------------


def test_there_are_no_runtime_dependencies() -> None:
    """The README's headline claim, held by something other than the README."""
    assert metadata()["project"]["dependencies"] == []


def test_the_only_extra_is_the_one_ci_installs() -> None:
    extras = metadata()["project"]["optional-dependencies"]
    assert set(extras) == {"dev"}


def test_every_plugin_addopts_names_is_one_the_dev_extra_installs() -> None:
    """RK457. `addopts = ["-n", "auto"]` makes the parallel run the default — 36-58 s here
    against 5m07s — and a flag in the config is a contract this file has to keep: a tree that
    installs `[dev]` and then cannot start pytest would be worse than the serial run it
    replaced. The runtime dependency count is untouched, which is the law that matters.
    """
    data = metadata()
    installed = " ".join(data["project"]["optional-dependencies"]["dev"])
    options = data["tool"]["pytest"]["ini_options"]["addopts"]
    if "-n" in options or any(one.startswith("-n") for one in options):
        assert "pytest-xdist" in installed
    assert data["project"]["dependencies"] == []


def test_the_floor_is_where_tomllib_became_stdlib() -> None:
    """3.11 is not a preference: below it `tomllib` is a dependency, and there are none."""
    assert metadata()["project"]["requires-python"] == ">=3.11"


# -- what PyPI renders, and what it refuses ----------------------------------


def test_the_page_pypi_renders_exists() -> None:
    data = metadata()["project"]
    assert (HERE / data["readme"]).is_file()
    assert data["description"]
    assert data["urls"]["Homepage"].startswith("https://")


def test_the_licence_is_declared_and_present() -> None:
    data = metadata()["project"]
    assert data["license"] == "Apache-2.0"
    assert data["license-files"] == ["LICENSE"]
    for name in data["license-files"]:
        assert (HERE / name).is_file()


def test_no_licence_classifier_beside_the_spdx_expression() -> None:
    """PEP 639 replaced it, and setuptools refuses the pair rather than picking one."""
    assert not [c for c in metadata()["project"]["classifiers"] if c.startswith("License")]


def test_every_supported_interpreter_is_claimed() -> None:
    classifiers = metadata()["project"]["classifiers"]
    for minor in (11, 12, 13):
        assert f"Programming Language :: Python :: 3.{minor}" in classifiers


# -- the wheel holds what the checkout does ----------------------------------


def test_every_module_is_inside_a_package_find_would_collect() -> None:
    """A module in a directory with no `__init__.py` imports here and is absent there."""
    assert metadata()["tool"]["setuptools"]["packages"]["find"]["where"] == ["src"]
    for module in modules():
        assert (module.path.parent / "__init__.py").is_file(), module.where


def test_the_console_script_resolves_to_something_callable() -> None:
    scripts = metadata()["project"]["scripts"]
    assert set(scripts) == {"roadkeep"}
    module_name, _, attribute = scripts["roadkeep"].partition(":")
    assert callable(getattr(import_module(module_name), attribute))


def test_the_cli_reports_the_package_version(capsys) -> None:
    """`--version` is what an adopter checks against a pin, so it is not a second literal."""
    from roadkeep.cli import build_parser

    parser = build_parser()
    with pytest.raises(SystemExit) as exited:
        parser.parse_args(["--version"])
    assert exited.value.code == 0
    assert capsys.readouterr().out.startswith(f"roadkeep {roadkeep.__version__} (")


def test_the_version_costs_nothing_until_it_is_asked_for() -> None:
    """RK79 names the tree with a git call — one the commands doing the work never pay.

    An `action="version"` string is built with the parser, so the cost would land on every
    run; the assertion is that no literal was baked in at build time.
    """
    from roadkeep.cli import build_parser

    action = next(a for a in build_parser()._actions if "--version" in a.option_strings)
    assert not hasattr(action, "version")
    assert action.nargs == 0


# -- what the distribution does not promise (RK205) ----------------------------


def test_no_py_typed_ships_and_the_reason_is_declared() -> None:
    """A typed package nobody may type-check was the symptom; the answer is a decision.

    Every module here is annotated and PEP 561 makes a consumer's checker ignore all of it
    without a `py.typed` marker. Two answers were coherent — ship the marker, or say the
    Python surface is not a promise — and the wrong one was doing neither, because RK199 had
    already spent the argument ("no checker reads this package") as if it were settled.

    Both halves are asserted together on purpose: the marker's absence is only honest while
    the non-goal is declared, and shipping one without dropping the other is the state this
    test exists to catch.
    """
    from roadkeep import scoping
    from roadkeep.config import Config

    assert not (PACKAGE / "py.typed").exists()
    data = metadata()
    assert "package-data" not in data.get("tool", {}).get("setuptools", {})

    config = Config.discover(HERE)
    leads = scoping.leads(config.document("roadmap"))
    assert "No supported Python API." in leads


# -- the surface a lazy `__init__` still owes (RK199) -------------------------


def test_every_re_export_resolves_to_the_schemas_own_object():
    """`__all__` is a promise, and PEP 562 is what keeps it without paying for it.

    The package `__init__` runs before any module in it does, so re-exporting `schema`
    eagerly cost 27.7ms on every entry point — including the screen (RK176) whose whole
    argument is that it imports nothing but the standard library. Resolved on first access
    it is 0.6ms, and what the eager import used to guarantee is guaranteed here instead.
    """
    import roadkeep
    from roadkeep import schema

    for name in roadkeep.__all__:
        assert getattr(roadkeep, name) is getattr(schema, name), name


def test_a_name_the_package_does_not_export_still_raises():
    import roadkeep

    with pytest.raises(AttributeError, match="no attribute 'Nope'"):
        roadkeep.Nope  # noqa: B018 - the access is the assertion


def test_dir_answers_what_all_promises():
    # A lazy name is invisible to `dir` until it is touched, and a surface that cannot be
    # discovered is one a reader has to already know about.
    import roadkeep

    assert set(roadkeep.__all__) <= set(dir(roadkeep))


def test_importing_the_package_does_not_import_the_schema():
    """The saving itself, asserted rather than measured — a timing test would be flaky.

    In a fresh interpreter, because `sys.modules` in this one is full of everything the
    suite has already imported.
    """
    import subprocess
    import sys

    done = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; sys.path.insert(0, r'"
            + str(Path(__file__).parents[1] / "src")
            + "'); import roadkeep; print('roadkeep.schema' in sys.modules)",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert done.stdout.strip() == "False", done.stderr


# -- what `-n auto` resolves to (RK460) ---------------------------------------


class _Asked:
    """A stand-in for the config xdist hands the hook: what the invocation named."""

    def __init__(self, *args: str) -> None:
        self.args = list(args)


def test_a_run_that_named_one_thing_is_not_spread_over_every_core() -> None:
    """RK457 bought the full run five minutes and charged the narrow one: 28 workers each
    import `conftest`, and that import fingerprints the checkout and copies the governed
    files (RK263, RK315) — so one file went from 1.3 s to 43.2 s, which is the loop an agent
    actually runs. Measured after: 0.93 s for the file and 0.68 s for a single test."""
    from conftest import pytest_xdist_auto_num_workers

    assert pytest_xdist_auto_num_workers(_Asked("tests/test_ranking.py")) == 0
    assert pytest_xdist_auto_num_workers(_Asked("tests/test_ranking.py::test_a_tie")) == 0
    # One narrow argument decides it: a caller naming a file alongside a tree still named one.
    assert pytest_xdist_auto_num_workers(_Asked("tests", "tests/test_ranking.py")) == 0


def test_several_things_named_are_a_pool_and_not_a_serial_run() -> None:
    """RK462: one file is narrow where six are a pool, and where the break-even sits is a
    thing to measure. Serial against one worker per file: 1 file 0.93 s / 1.79 s, 2 files a
    wash, 3 files 4.2 s / 3.0 s, 6 files 7.9 s / 4.8 s, 16 files 68 s / 11.3 s. So two is
    where it stops costing and past that the pool wins by more the more there is."""
    from conftest import pytest_xdist_auto_num_workers

    assert pytest_xdist_auto_num_workers(_Asked("a.py", "b.py")) == 2
    assert pytest_xdist_auto_num_workers(_Asked("a.py", "b.py", "c.py::t")) == 3
    # Capped at the cores there are, which is the same ceiling the whole-tree run gets.
    many = [f"f{n}.py" for n in range((os.cpu_count() or 1) + 5)]
    assert pytest_xdist_auto_num_workers(_Asked(*many)) == os.cpu_count()


def test_a_whole_tree_still_gets_every_core() -> None:
    """`testpaths` makes `tests` the default argument, so this is the no-argument run — the
    one RK457 is about, and the one that has 2891 tests to distribute."""
    from conftest import pytest_xdist_auto_num_workers

    assert pytest_xdist_auto_num_workers(_Asked("tests")) == os.cpu_count()
    assert pytest_xdist_auto_num_workers(_Asked("tests/", "tests/captures")) == os.cpu_count()
