"""Every cache in the package, counted — and which of them a test can poison (RK268).

The defect reached eleven hand-written `cache_clear()` calls because nothing counted the caches.
So this is an inventory in the shape `KEPT_LITERAL` uses in `tests/test_provenance.py`: each
`lru_cache` in the package is listed with the reason it is or is not cleared around every test,
and a seventh one added later fails here until somebody decides which it is.

The split is not a style. A cache keyed only by its arguments answers the same thing forever, so
clearing it per test spends time to change nothing — and two of those three are what a
measurement asserts about, which an autouse clear would quietly delete. `engine` is a third kind:
process-constant, so a stale entry cannot be a lie — the inventory carries the reason nothing can
poison it and `conftest` enforces that rather than trusting it. What is left is the pair a
monkeypatch replaces and a `tmp_path` outlives, which is the whole failure mode.
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
from pathlib import Path

from conftest import VOLATILE
from surface import address, modules

HERE = Path(__file__).resolve().parents[1]
PACKAGE = HERE / "src" / "roadkeep"

#: `(module, function)` → why it is cleared around every test, or why it is not. The reason is
#: the deliverable: "cached" says nothing about whether a test can leave a lie in it.
INVENTORY = {
    (address("document"), "_task_re"): "pure: the four (marker, symptom) combinations are the domain",
    (address("document"), "_parsed"): "pure: keyed by the bytes and the schema, so a hit is a re-read",
    ("provenance.py", "engine"): (
        "process-constant: `roadkeep.__file__` and one git call in that directory, neither of "
        "which any test patches, so a stale entry cannot be a lie and the clear protects nothing"
    ),
    ("provenance.py", "invocation"): "reads the machine: a PATH scan and the launcher on disk",
    ("provenance.py", "persisted"): "reads the machine: the absolute command git will execute",
    ("provenance.py", "_declared_by"): (
        "reads the machine: whether a project's own `.mcp.json` declares this server, which a "
        "test writes into a `tmp_path` after the first ask"
    ),
    ("provenance.py", "_plugin_name"): (
        "reads the machine: the manifest of the tree this engine runs out of, which a test that "
        "patches `engine` moves"
    ),
    ("remedying.py", "_reading"): (
        "pure: which verbs the CLI declares read-only and the flags that make each a write, "
        "both read off `build_parser()`, which is a function of the code and holds no config "
        "— the same argument `serving._root` makes about the same object (RK1015)"
    ),
    ("serving.py", "_root"): "pure: the parser is a function of the code and holds no config",
    ("linting.py", "_rules"): (
        "pure: the gate's domain is built from this module's own functions and takes no argument "
        "— every project-specific value reaches a rule through the `_Scan` it is handed at call "
        "time, so an entry keyed on nothing cannot be about the wrong project (RK1172)"
    ),
}

#: The two the suite asserts `cache_info` about, where clearing *is* the measurement's setup:
#: `test_listing_the_tools_builds_the_parser_once` and
#: `test_the_same_bytes_are_parsed_once_however_many_times_they_are_read`.
MEASURED = {("serving.py", "_root"), (address("document"), "_parsed")}


def cached() -> set[tuple[str, str]]:
    """Read from the source and never from a registry: a cache is a decorator, and importing the
    package to look for one finds only what happens to have been imported."""
    found = set()
    for module in modules():
        tree = ast.parse(module.text)
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for decorator in node.decorator_list:
                call = decorator.func if isinstance(decorator, ast.Call) else decorator
                name = call.attr if isinstance(call, ast.Attribute) else getattr(call, "id", "")
                if name in ("lru_cache", "cache"):
                    found.add((module.where, node.name))
    return found


def test_every_cache_in_the_package_is_in_the_inventory():
    assert cached() == set(INVENTORY)


def test_the_volatile_set_is_exactly_what_reads_the_machine():
    machine = {name for (_, name), why in INVENTORY.items() if why.startswith("reads")}
    assert machine == set(VOLATILE)


def test_nothing_pure_is_cleared_around_every_test():
    # The check the rationale asked for, and the reason the answer is not "all six".
    pure = {name for (_, name), why in INVENTORY.items() if why.startswith("pure")}
    assert pure.isdisjoint(VOLATILE)
    assert {name for _, name in MEASURED}.isdisjoint(VOLATILE)


def test_the_process_constant_one_is_not_cleared_either():
    # The second thing the obvious answer got wrong: nothing patches what `engine` reads, so a
    # stale entry cannot be a lie and a per-test clear re-runs git to change nothing.
    constant = {name for (_, name), why in INVENTORY.items() if why.startswith("process-constant")}
    assert constant == {"engine"} and constant.isdisjoint(VOLATILE)


def test_every_volatile_cache_starts_each_test_empty():
    # The fixture's own assertion, and it can only be made from inside a test: `currsize` is what
    # a leak looks like, and this one runs among two thousand others that fill and drop them.
    from roadkeep import provenance

    for name in VOLATILE:
        assert getattr(provenance, name).cache_info().currsize == 0, name


#: A test that poisons `invocation` with a path under its own `tmp_path` and then raises, which
#: is the ordering the trailing `cache_clear()` never survived. No `chdir`: the answer has to
#: carry the temp path for the next test to be able to say it leaked.
LEAK = '''
from roadkeep.provenance import Engine, invocation


def test_poisons_the_cache_and_then_raises(tmp_path, monkeypatch):
    home = tmp_path / "tree" / "src" / "roadkeep"
    home.mkdir(parents=True)
    launcher = tmp_path / "tree" / "scripts" / "roadkeep.py"
    launcher.parent.mkdir(parents=True)
    launcher.write_text("x = 1\\n", encoding="utf-8")
    monkeypatch.setattr("roadkeep.provenance.engine", lambda: Engine("0.1.0", home, None))
    monkeypatch.setattr("roadkeep.provenance.shutil.which", lambda name: None)
    # `as_posix`, because that is how the answer spells a path — and comparing against the
    # platform spelling is a check that passes on Windows for the wrong reason.
    assert tmp_path.as_posix() in invocation()
    raise AssertionError("the failure that skips the trailing cache_clear")


def test_the_next_test_reads_the_real_machine(tmp_path):
    # `tmp_path.parent` is the basetemp both tests share, so this names the other test's
    # directory without knowing which one it was.
    assert tmp_path.parent.as_posix() not in invocation()
'''


#: A test that fills the *real* `engine` cache from a patched `roadkeep.__file__`, which is the
#: one thing the inventory's reason for leaving it out would be wrong about.
POISON_IDENTITY = '''
from roadkeep.provenance import engine


def test_caches_an_engine_that_is_not_this_one(tmp_path, monkeypatch):
    monkeypatch.setattr("roadkeep.__file__", str(tmp_path / "roadkeep" / "__init__.py"))
    assert engine().home == tmp_path / "roadkeep"
'''


def nested(tmp_path: Path, source: str) -> subprocess.CompletedProcess:
    """One pytest inside another, over a copy of this conftest — the only place a fixture's own
    teardown can be observed, since in-process it is the thing running the observation."""
    (tmp_path / "conftest.py").write_text(
        Path(__file__).with_name("conftest.py").read_text(encoding="utf-8"), encoding="utf-8"
    )
    (tmp_path / "test_leak.py").write_text(source, encoding="utf-8")
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", str(tmp_path)],
        cwd=tmp_path,
        capture_output=True,
        # Not the locale codec: a nested failure prints the tool's own output, which is UTF-8
        # by `_force_utf8`, into a decode that is cp1252 here — the defect `test_plugin.py`'s
        # validator run measured. Latent while the inner assertions stay ASCII.
        encoding="utf-8",
        errors="replace",
        env={**os.environ, "PYTHONPATH": str(PACKAGE.parent)},
    )


def test_a_cache_a_raising_test_filled_does_not_reach_the_next_one(tmp_path):
    """The failure mode itself: two tests in one file, in order. The first fills the cache from
    its own `tmp_path` and dies before any cleanup it could have written, and the second asserts
    the real answer. Without the fixture both fail, the second about a directory pytest has
    already deleted; the assertion is that exactly one fails now, and it is the one that meant to.
    """
    finished = nested(tmp_path, LEAK)
    assert "1 failed, 1 passed" in finished.stdout, finished.stdout
    assert "FAILED test_leak.py::test_poisons_the_cache_and_then_raises" in finished.stdout


def test_a_test_that_poisons_the_identity_cache_is_told_to_declare_it(tmp_path):
    """The invariant that keeps `engine` out of `VOLATILE`, enforced rather than restated.

    The test body passes — the patch does what it says — and the fixture's teardown fails it,
    naming the file and the list to add it to. Which is the honest shape: the reason `engine` is
    not cleared is that nothing patches what it reads, so the day something does, the run says so
    instead of the inventory quietly becoming wrong.
    """
    finished = nested(tmp_path, POISON_IDENTITY)
    assert "1 error" in finished.stdout, finished.stdout
    assert "adding it to VOLATILE in tests/conftest.py" in finished.stdout
