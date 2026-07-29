"""`roadkeep.toml` (RK3).

The load path is small; what is worth testing is the refusals. A config key that is
silently ignored is a limit its author believes is in force and is not — so every
test below that asserts an error is asserting the *absence* of a silent fallback.

This repository's own `roadkeep.toml` is part of the fixture: the tool configures
itself, and if it could not, "configuration, not convention" (L6) would be a claim
about other people's projects.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from roadkeep.config import CONFIG_NAME, Config, ConfigError, find_config
from roadkeep.schema import DESIGNED, SHIPPED

HERE = Path(__file__).resolve().parents[1]

MINIMAL = """
prefix = "SH"

[files]
roadmap = "docs/ROADMAP.md"
"""


def write(directory: Path, body: str, name: str = CONFIG_NAME) -> Path:
    path = directory / name
    path.write_text(body, encoding="utf-8")
    return path


# -- this repository ---------------------------------------------------------


def test_the_tool_configures_itself():
    config = Config.discover(HERE)
    assert config.source == HERE / CONFIG_NAME
    assert config.schema.prefix == "RK"
    assert config.missing() == ()
    assert set(config.paths) == {"roadmap", "changelog", "improvements"}


def test_its_own_documents_validate_under_its_own_config():
    config = Config.discover(HERE)
    for role in ("roadmap", "changelog"):
        document = config.document(role)
        assert document.entries
        assert document.non_canonical == ()
        assert [v for e in document.entries for v in document.schema.validate(e.task)] == []


def test_a_project_without_a_strategy_file_declares_none_rather_than_an_empty_one():
    config = Config.discover(HERE)
    assert not config.has("strategy")
    with pytest.raises(KeyError, match="declares no 'strategy'"):
        config.path("strategy")


# -- finding it --------------------------------------------------------------


def test_config_is_found_by_walking_up_like_git(tmp_path):
    write(tmp_path, MINIMAL)
    deep = tmp_path / "src" / "roadkeep" / "nested"
    deep.mkdir(parents=True)
    assert find_config(deep) == tmp_path / CONFIG_NAME
    assert Config.discover(deep).schema.prefix == "SH"


def test_pyproject_configures_roadkeep_when_there_is_no_roadkeep_toml(tmp_path):
    write(tmp_path, '[tool.roadkeep]\nprefix = "T"\n', name="pyproject.toml")
    config = Config.discover(tmp_path)
    assert config.schema.prefix == "T"
    assert config.source.name == "pyproject.toml"


def test_a_pyproject_that_says_nothing_about_roadkeep_is_not_a_config(tmp_path):
    write(tmp_path, "[project]\nname = 'x'\n", name="pyproject.toml")
    assert find_config(tmp_path) is None


def test_roadkeep_toml_wins_over_pyproject(tmp_path):
    write(tmp_path, MINIMAL)
    write(tmp_path, '[tool.roadkeep]\nprefix = "T"\n', name="pyproject.toml")
    assert Config.discover(tmp_path).schema.prefix == "SH"


def test_a_project_with_no_config_still_has_a_layout(tmp_path):
    config = Config.discover(tmp_path)
    assert config.source is None
    assert config.path("roadmap") == tmp_path / "docs" / "ROADMAP.md"
    assert config.missing() == ("roadmap", "changelog", "improvements")


# -- what it declares --------------------------------------------------------


def test_paths_are_resolved_against_the_config_not_the_shell(tmp_path):
    write(tmp_path, 'prefix = "CU"\n\n[files]\nroadmap = "docs/roadmap/ROADMAP.md"\n')
    config = Config.discover(tmp_path)
    # Cursarei keeps its roadmap in a subdirectory; the answer must not depend on
    # which directory the command was run from.
    assert config.path("roadmap") == (tmp_path / "docs" / "roadmap" / "ROADMAP.md")


def test_limits_and_markers_reach_the_schema(tmp_path):
    write(
        tmp_path,
        f"""
[limits]
symptom = 90
line = 240

[markers]
open = ["{DESIGNED}"]
shipped = "{SHIPPED}"
""",
    )
    schema = Config.discover(tmp_path).schema
    assert (schema.symptom_max, schema.line_max) == (90, 240)
    assert schema.why_max == 200  # undeclared keys keep the default
    assert schema.markers == (DESIGNED,)


def test_the_changelog_is_the_same_format_in_its_ledger_configuration(tmp_path):
    config = Config.discover(HERE)
    assert config.schema_for("changelog").shipped_allowed
    assert not config.schema_for("changelog").deps_field
    assert config.schema_for("roadmap") == config.schema


def test_id_sources_are_every_file_that_can_carry_an_id(tmp_path):
    names = [p.name for p in Config.discover(HERE).id_sources()]
    # The governed files first, then the extras — an id missed here is an id reused.
    assert names[-1] == "agents.md"
    assert "ROADMAP.md" in names and "CHANGELOG.md" in names


def test_missing_reports_a_declared_file_that_is_not_on_disk(tmp_path):
    write(tmp_path, MINIMAL)
    assert Config.discover(tmp_path).missing() == ("roadmap",)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "ROADMAP.md").write_text("", encoding="utf-8")
    assert Config.discover(tmp_path).missing() == ()


# -- refusals ----------------------------------------------------------------


def test_an_unknown_key_is_refused_and_names_the_allowed_ones(tmp_path):
    path = write(tmp_path, 'sections = ["docs/SPEC.md"]\n')
    with pytest.raises(ConfigError) as caught:
        Config.load(path)
    assert "unknown key 'sections'" in str(caught.value)
    assert "prefix" in str(caught.value)  # the allowed set, so the fix is one edit


def test_the_pointer_scheme_is_a_declared_choice(tmp_path):
    assert Config.discover(HERE).schema.ref_scheme == "id"
    outline = write(tmp_path, 'ref_scheme = "outline"\n')
    assert Config.load(outline).schema.ref_scheme == "outline"


def test_an_unknown_pointer_scheme_is_refused_by_name(tmp_path):
    path = write(tmp_path, 'ref_scheme = "roman"\n')
    with pytest.raises(ConfigError, match="ref_scheme must be one of"):
        Config.load(path)


def test_a_mistyped_limit_is_refused_rather_than_defaulted(tmp_path):
    # The failure this rule exists for: `symptom_max = 40` would load, be ignored,
    # and leave its author believing a limit is in force.
    path = write(tmp_path, "[limits]\nsymptom_max = 40\n")
    with pytest.raises(ConfigError, match="limits.symptom_max"):
        Config.load(path)


def test_an_absolute_path_is_refused_because_it_is_checked_in(tmp_path):
    path = write(tmp_path, '[files]\nroadmap = "D:/Git/other/ROADMAP.md"\n')
    with pytest.raises(ConfigError, match="must be relative"):
        Config.load(path)


def test_an_invisible_marker_is_refused_where_it_is_typed(tmp_path):
    # 📋 + U+FE0F is the same picture and a different string: declaring one would
    # put every line in the file permanently out of round-trip.
    path = write(tmp_path, f'[markers]\nopen = ["{DESIGNED}\ufe0f"]\n')
    with pytest.raises(ConfigError, match="U\\+FE0F"):
        Config.load(path)


def test_a_marker_set_that_can_say_done_is_refused(tmp_path):
    path = write(tmp_path, f'[markers]\nopen = ["{DESIGNED}", "{SHIPPED}"]\n')
    with pytest.raises(ConfigError, match="shipped marker"):
        Config.load(path)


def test_a_wrongly_typed_value_names_the_type_it_wanted(tmp_path):
    path = write(tmp_path, "prefix = 3\n[limits]\nwhy = 'lots'\n")
    with pytest.raises(ConfigError) as caught:
        Config.load(path)
    assert "prefix must be a string" in str(caught.value)
    assert "limits.why must be an integer" in str(caught.value)


def test_every_problem_is_reported_at_once(tmp_path):
    path = write(
        tmp_path,
        'nonsense = 1\nid_sources = "agents.md"\n[files]\nspec = "docs/SPEC.md"\n',
    )
    with pytest.raises(ConfigError) as caught:
        Config.load(path)
    # Three independent mistakes, one run: a config fixed one error per run is a
    # config fixed over four runs.
    assert len(caught.value.problems) == 3
