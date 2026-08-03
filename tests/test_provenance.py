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
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import roadkeep
from roadkeep.provenance import _LOADED_AT, MODIFIED, UNTRACKED, Engine, engine

HERE = Path(__file__).resolve().parents[1]


def git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)


# -- what it reports here ----------------------------------------------------


def test_the_engine_names_the_directory_its_modules_were_imported_from():
    # The half that separates a plugin cache from a checkout, and the half that is always
    # available: `__file__` needs no subprocess and no repository.
    assert engine().home == Path(roadkeep.__file__).resolve().parent
    assert engine().home == HERE / "src" / "roadkeep"


def test_the_version_is_the_packages_and_not_a_second_literal():
    assert engine().version == roadkeep.__version__


def test_this_checkout_reports_the_commit_it_is_at():
    if engine().commit is None:
        pytest.skip("this tree is not a checkout git can place")
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
    os.utime(home / "config.py", (_LOADED_AT - 60, _LOADED_AT - 60))
    assert Engine(version="0.1.0", home=home, commit=None).stale == ()


def test_a_module_written_after_the_import_is_named(tmp_path):
    # The measured failure: `[claims] held` reached `roadkeep.toml` and `config.py` in one
    # commit, and every MCP write then refused a key the file legitimately declared.
    home = tmp_path / "roadkeep"
    home.mkdir()
    for name in ("config.py", "schema.py", "notes.txt"):
        (home / name).write_text("x = 1\n", encoding="utf-8")
        os.utime(home / name, (_LOADED_AT + 300, _LOADED_AT + 300))
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
    os.utime(home / "serving.py", (_LOADED_AT + 300, _LOADED_AT + 300))
    assert described.stale == ("serving.py",)


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
    git(tmp_path, "init", "--quiet")
    (tmp_path / "unrelated.txt").write_text("someone else's work\n", encoding="utf-8")
    git(tmp_path, "add", ".")
    git(tmp_path, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "theirs")

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
