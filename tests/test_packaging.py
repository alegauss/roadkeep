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

import re
import tomllib
from importlib import import_module
from pathlib import Path

import pytest

import roadkeep

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


def test_the_builder_reads_the_same_number_the_module_states() -> None:
    """The `attr` above resolved statically, which is the only way it is read at build."""
    source = (PACKAGE / "__init__.py").read_text(encoding="utf-8")
    found = re.findall(r'^__version__ = "([^"]+)"$', source, flags=re.MULTILINE)
    assert found == [roadkeep.__version__]


# -- the claims that live in prose everywhere else ---------------------------


def test_there_are_no_runtime_dependencies() -> None:
    """The README's headline claim, held by something other than the README."""
    assert metadata()["project"]["dependencies"] == []


def test_the_only_extra_is_the_one_ci_installs() -> None:
    extras = metadata()["project"]["optional-dependencies"]
    assert set(extras) == {"dev"}


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
    for module in PACKAGE.rglob("*.py"):
        if "__pycache__" in module.parts:
            continue
        assert (module.parent / "__init__.py").is_file(), module


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
