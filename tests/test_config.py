"""`roadkeep.toml` (RK3).

The load path is small; what is worth testing is the refusals. A config key that is
silently ignored is a limit its author believes is in force and is not — so every
test below that asserts an error is asserting the *absence* of a silent fallback.

This repository's own `roadkeep.toml` is part of the fixture: the tool configures
itself, and if it could not, "configuration, not convention" (L6) would be a claim
about other people's projects.
"""

from __future__ import annotations

from dataclasses import replace
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


def test_its_own_instruction_files_declare_their_budget_here(tmp_path):
    # RK30: this repository's `agents.md` stated its budget in its own prose, which is the
    # arrangement that let Shio's reach 186 KB. The number lives in the config now — and it is
    # checked here as *headroom over the reading*, not as a literal: a figure repeated in a
    # test is the duplicate the move existed to remove, and a budget left far above the file
    # it governs is room the prose grows back into, which is what RK23's trim had to reclaim.
    config = Config.discover(HERE)
    declared = {config.relative(b.path): b for b in config.budgets}
    assert set(declared) == {"agents.md", "CLAUDE.md"}
    for name, budget in declared.items():
        raw = (HERE / name).read_bytes()
        assert 0 <= budget.lines - len(raw.splitlines()) <= 25, name
        assert 0 <= budget.bytes - len(raw) <= 2000, name


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


def test_a_ledger_can_declare_that_it_carries_no_marker(tmp_path):
    # The declaration Shio needs to adopt at all (RK43): 920 entries, all shipped, and a
    # marker written once here instead of 920 times in the file.
    write(tmp_path, "[ledger]\nmarker = false\n")
    schema = Config.discover(tmp_path).schema
    # Only the ledger's: the roadmap's marker is its status, so that slot never goes.
    assert schema.marker_field and not schema.as_ledger().marker_field


def test_a_role_can_be_held_to_its_own_limit(tmp_path):
    # RK50: a roadmap line is refused at insertion, where the refusal costs a retry; a
    # ledger line is history, and Turing's reads 938 characters at the median against 320.
    write(tmp_path, "[limits]\nwhy = 200\nline = 320\n\n[limits.changelog]\nwhy = 4000\nline = 4200\n")
    config = Config.discover(tmp_path)
    assert (config.schema_for("roadmap").why_max, config.schema_for("roadmap").line_max) == (200, 320)
    assert (config.schema_for("changelog").why_max, config.schema_for("changelog").line_max) == (4000, 4200)
    # And nothing else about the ledger's shape is disturbed by carrying its own numbers.
    assert config.schema_for("changelog").shipped_allowed and not config.schema_for("changelog").deps_field


def test_a_role_can_be_exempted_from_a_prose_rule_its_history_cannot_obey(tmp_path):
    # RK52: `why is one sentence` says the remainder belongs in the section the line points
    # at, and a ledger line has none — so 233 of Shio's entries have no available fix. The
    # project declares the exemption; the tool does not decide the rule never mattered.
    write(tmp_path, "[rules.changelog]\none_sentence = false\nterminator = false\n")
    config = Config.discover(tmp_path)
    ledger = config.schema_for("changelog")
    assert not ledger.one_sentence and not ledger.terminator
    # The roadmap keeps both, which is the whole point of the rule being per role.
    assert config.schema_for("roadmap").one_sentence and config.schema_for("roadmap").terminator


def test_an_exemption_is_read_by_the_write_path_too(tmp_path):
    # Not a lint-only switch: a project that says its ledger holds paragraphs may `record`
    # one, and one that says nothing is still refused at input (`tests/test_recording.py`).
    write(tmp_path, "[rules.changelog]\none_sentence = false\n")
    schema = Config.discover(tmp_path).schema_for("changelog")
    from roadkeep.schema import SHIPPED, Task

    task = Task(id="RK1", status=SHIPPED, block="A", symptom="A symptom", why="Two. Sentences.")
    assert schema.validate(task) == ()


def test_a_project_may_declare_that_a_line_needs_no_pointer(tmp_path):
    # RK66: `ref_required` was a Schema field no key reached, so every project was held to
    # "every task points at its rationale section" — including Shio, whose process guide
    # says the opposite and whose three obedient lines were each a finding.
    write(tmp_path, "[rules.roadmap]\nref = false\n")
    config = Config.discover(tmp_path)
    assert not config.schema_for("roadmap").ref_required
    # Declared per role, and the default is *required*: a project that says nothing is
    # unchanged, which is what makes this a declaration and not a loosened default.
    assert Config.parse({}, root=tmp_path).schema.ref_required


def test_a_waived_pointer_is_the_demand_and_never_the_resolution(tmp_path):
    # The two halves of RK15 come apart here: nothing has to be pointed at, and a pointer
    # that is written still has to point at something — a dangling one reads as though the
    # design exists, whatever the project declared.
    from roadkeep.schema import Task

    write(tmp_path, "ref_scheme = \"outline\"\n\n[rules.roadmap]\nref = false\n")
    schema = Config.discover(tmp_path).schema_for("roadmap")
    bare = Task(id="RK1", status=DESIGNED, block="A", symptom="A symptom", why="Because.")
    assert schema.validate(bare) == ()
    codes = [v.code for v in schema.validate(replace(bare, ref="§1.2"))]
    assert codes == ["ref.sigil"]


def test_the_ledger_has_no_pointer_to_require_or_to_waive(tmp_path):
    # `ship` deletes §<id> in the transaction that writes the entry, so `ref = true` on the
    # changelog would put every line that ever ships permanently in violation. Refused where
    # it is typed rather than obeyed into a file nobody can fix.
    path = write(tmp_path, "[rules.changelog]\nref = true\n")
    with pytest.raises(ConfigError, match="rules.changelog.ref: the ledger carries no pointer"):
        Config.load(path)


def test_an_unknown_prose_rule_is_refused_like_any_other_key(tmp_path):
    path = write(tmp_path, "[rules.changelog]\nno_emoji = false\n")
    with pytest.raises(ConfigError, match="rules.changelog.no_emoji"):
        Config.load(path)


def test_a_limit_for_a_role_the_format_does_not_know_is_refused(tmp_path):
    path = write(tmp_path, "[limits.readme]\nline = 900\n")
    with pytest.raises(ConfigError, match="limits.readme: not a governed role"):
        Config.load(path)


def test_an_unknown_key_inside_a_roles_limits_is_refused_like_any_other(tmp_path):
    path = write(tmp_path, "[limits.changelog]\nlines = 900\n")
    with pytest.raises(ConfigError, match="limits.changelog.lines"):
        Config.load(path)


def test_a_project_that_declares_no_role_limit_holds_every_file_to_one_number(tmp_path):
    write(tmp_path, "[limits]\nline = 300\n")
    config = Config.discover(tmp_path)
    assert config.limits == {}
    assert config.schema_for("changelog").line_max == config.schema_for("roadmap").line_max


def test_a_ledger_can_declare_that_its_lines_have_no_symptom_slot(tmp_path):
    # The declaration Shio and Turing both need (RK48): `- **T1** — <prose>` is the shape
    # 234 and 761 lines already have, and the slot has no reader on a line that shipped.
    write(tmp_path, "[ledger]\nsymptom = false\n")
    schema = Config.discover(tmp_path).schema
    assert schema.symptom_field and not schema.as_ledger().symptom_field


def test_the_old_marker_spelling_names_its_replacement_instead_of_being_read(tmp_path):
    # Refused rather than aliased (RK48): two spellings of one flag are two that can
    # disagree, and a setting that silently stops being read is worse than an error.
    path = write(tmp_path, "[markers]\nledger = false\n")
    with pytest.raises(ConfigError, match=r"markers.ledger moved to \[ledger\] marker"):
        Config.load(path)


def test_the_ledger_carries_a_marker_unless_the_project_says_otherwise(tmp_path):
    assert Config.discover(HERE).schema_for("changelog").marker_field


def test_a_ledger_declaration_that_is_not_a_boolean_is_refused(tmp_path):
    path = write(tmp_path, '[ledger]\nmarker = "none"\n')
    with pytest.raises(ConfigError, match="ledger.marker must be true or false"):
        Config.load(path)


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
    # Absolute *on the machine running the test*: a `D:/…` literal is a plain relative
    # name to POSIX, so it would assert nothing on CI. `as_posix` keeps it TOML-safe,
    # a Windows path's backslashes being escapes inside a basic string.
    absolute = (tmp_path / "elsewhere" / "ROADMAP.md").as_posix()
    path = write(tmp_path, f'[files]\nroadmap = "{absolute}"\n')
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


def test_a_budget_reaches_the_config_with_both_units(tmp_path):
    path = write(tmp_path, '[budgets]\n"agents.md" = { lines = 150, bytes = 11000 }\n')
    (budget,) = Config.load(path).budgets
    assert budget.path == (tmp_path / "agents.md").resolve()
    assert (budget.lines, budget.bytes) == (150, 11000)


def test_a_budget_that_declares_nothing_is_refused(tmp_path):
    # It would read as a budget and hold nobody to anything, which is the arrangement
    # RK30 exists to replace rather than reproduce one file over.
    path = write(tmp_path, '[budgets]\n"agents.md" = {}\n')
    with pytest.raises(ConfigError, match="declares neither lines nor bytes"):
        Config.load(path)


def test_a_budget_key_that_is_not_a_unit_is_refused(tmp_path):
    path = write(tmp_path, '[budgets]\n"agents.md" = { tokens = 46000 }\n')
    with pytest.raises(ConfigError, match="budgets.'agents.md'.tokens"):
        Config.load(path)


def test_a_budget_that_is_not_a_positive_integer_is_refused(tmp_path):
    path = write(tmp_path, '[budgets]\n"agents.md" = { lines = 0, bytes = "lots" }\n')
    with pytest.raises(ConfigError) as caught:
        Config.load(path)
    assert len(caught.value.problems) == 2


def test_an_absolute_budget_path_is_refused_like_a_file_path(tmp_path):
    absolute = (tmp_path / "elsewhere" / "agents.md").as_posix()
    path = write(tmp_path, f'[budgets]\n"{absolute}" = {{ lines = 150 }}\n')
    with pytest.raises(ConfigError, match="must be relative"):
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


def test_a_backlog_numbered_by_track_declares_its_families(tmp_path):
    # RK74: cursarei numbers C## for product, L## for the LLM track, V## for the migration
    # to Viglet — and `prefix` as one string made 521 of its lines unreadable, not
    # non-conforming.
    write(tmp_path, 'prefix = ["C", "L", "V"]\n')
    schema = Config.discover(tmp_path).schema
    assert schema.prefixes == ("C", "L", "V")
    # The first is what `add` mints under, and it is the author's choice, not a default
    # the tool picked: it is the one they wrote first.
    assert schema.prefix == "C"


def test_one_family_stays_the_string_every_other_project_writes(tmp_path):
    write(tmp_path, 'prefix = "SH"\n')
    assert Config.discover(tmp_path).schema.prefixes == ("SH",)


def test_a_prefix_that_is_neither_a_string_nor_a_list_is_refused(tmp_path):
    path = write(tmp_path, "prefix = 3\n")
    with pytest.raises(ConfigError, match="prefix must be a string, or a list"):
        Config.load(path)


def test_a_declaration_of_no_families_at_all_is_refused(tmp_path):
    path = write(tmp_path, "prefix = []\n")
    with pytest.raises(ConfigError, match="at least one family"):
        Config.load(path)


def test_a_project_declares_the_word_it_files_work_under(tmp_path):
    # RK75: three of the four adopting corpora spell it otherwise — Dumont files under
    # `## Track A`, cursarei under `## Fase 0` — and each was getting a finding per line
    # for its own vocabulary. The word is the project's; the shape after it is not.
    write(tmp_path, '[headings]\nword = "Track"\n')
    schema = Config.discover(tmp_path).schema
    assert schema.heading_word == "Track"
    assert Config.parse({}, root=tmp_path).schema.heading_word == "Block"


def test_an_unknown_heading_key_is_refused_like_any_other(tmp_path):
    path = write(tmp_path, '[headings]\nlevel = 2\n')
    with pytest.raises(ConfigError, match="headings.level"):
        Config.load(path)
