"""`roadkeep.toml` (RK3).

The load path is small; what is worth testing is the refusals. A config key that is
silently ignored is a limit its author believes is in force and is not — so every
test below that asserts an error is asserting the *absence* of a silent fallback.

This repository's own `roadkeep.toml` is part of the fixture: the tool configures
itself, and if it could not, "configuration, not convention" (L6) would be a claim
about other people's projects.
"""

from __future__ import annotations

import tomllib
from dataclasses import replace
from pathlib import Path

import pytest

from roadkeep.config import (
    CONFIG_NAME,
    PATH_ARGUMENTS,
    PATH_SPELLINGS,
    Config,
    ConfigError,
    find_config,
)
from roadkeep.kernel.schema import DESIGNED, IDEA, SHIPPED, Task

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
        # The floor is the ledger's alone: a backlog's finished state is empty, and RK21
        # shipped the last line this one had. A count that fails on progress is a count that
        # gets edited by the commit that crossed it, which is a count nobody re-reads.
        assert document.entries or role == "roadmap"
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
    assert set(declared) == {"agents.md", ".claude/CLAUDE.md"}
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
    from roadkeep.kernel.schema import SHIPPED, Task

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
    from roadkeep.kernel.schema import Task

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


# -- a refusal names where the number was set (RK1067) ------------------------


def test_a_refused_limit_names_the_line_that_set_it(tmp_path):
    # Every code this gate reports resolves to a door and prints it; the one whose remedy is
    # *changing the rule* had none, so an author was left to find where 150 was set — in an
    # adopting project, a file they have never opened.
    write(tmp_path, 'prefix = "RK"\n\n[limits]\nsymptom = 120\nwhy = 150\n')
    schema = Config.discover(tmp_path).schema
    assert schema.source_of("why_max") == " (roadkeep.toml:5 [limits].why)"
    assert schema.source_of("symptom_max") == " (roadkeep.toml:4 [limits].symptom)"


def test_a_limit_the_project_never_declared_says_so_instead_of_citing_one(tmp_path):
    # The distinction that is the whole affordance: *which of these two numbers did I
    # choose* is the question a refusal over a limit raises, and a citation invented for an
    # undeclared one would answer it wrongly in the reassuring direction.
    write(tmp_path, 'prefix = "RK"\n[limits]\nsymptom = 120\n')
    schema = Config.discover(tmp_path).schema
    assert schema.source_of("why_max") == " (this tool's default)"
    assert "roadkeep.toml" in schema.source_of("symptom_max")


def test_a_roles_own_number_is_cited_over_the_shared_one(tmp_path):
    # RK50's whole reason, reaching the author standing over one of the two: a `why` refused
    # in the changelog is about `[limits.changelog]` and not the roadmap's number.
    write(
        tmp_path,
        'prefix = "RK"\n\n[limits]\nwhy = 200\n\n[limits.changelog]\nwhy = 320\n',
    )
    config = Config.discover(tmp_path)
    assert config.schema_for("roadmap").source_of("why_max") == " (roadkeep.toml:4 [limits].why)"
    ledger = config.schema_for("changelog")
    assert ledger.source_of("why_max") == " (roadkeep.toml:7 [limits.changelog].why)"
    # And a limit that role did not restate still cites the shared line rather than nothing.
    assert ledger.source_of("line_max") == " (this tool's default)"


def test_the_citation_reaches_the_refusal_itself(tmp_path):
    # The read is only worth what the refusal carries: a source resolved and never printed
    # is the affordance existing everywhere except where somebody needs it.
    write(tmp_path, 'prefix = "RK"\n\n[limits]\nwhy = 30\n')
    schema = Config.discover(tmp_path).schema
    codes = schema.validate(
        Task(id="RK1", status="📋", block="A", symptom="A symptom", why="Because " + "x" * 40 + ".")
    )
    over = next(v for v in codes if v.code == "why.too-long")
    assert "limit is 30 (roadkeep.toml:4 [limits].why)" in over.message


# -- the shape, declared rather than named (RK1064) ---------------------------


def test_a_role_nobody_declared_still_has_the_grammar_the_tool_ships(tmp_path):
    # Two files and one object: the format's defaults ship with the tool, a project
    # overrides them, or every adopting project declares a grammar it never chose.
    write(tmp_path, 'prefix = "RK"\n')
    config = Config.discover(tmp_path)
    assert config.grammars == {}
    ledger = config.schema_for("changelog")
    assert ledger.is_ledger and not ledger.deps_field and not ledger.ref_required
    assert ledger.markers == (ledger.shipped_marker, ledger.retired_marker)


def test_a_project_can_declare_a_shape_and_not_only_a_number(tmp_path):
    # The half L6 was missing: every limit was per project and no part of the line was, so
    # `as_ledger` — one field dropped — was a method where the numbers beside it were keys.
    write(tmp_path, 'prefix = "RK"\n[grammar.changelog]\ndrop = ["ref"]\n')
    ledger = Config.discover(tmp_path).schema_for("changelog")
    # Declared: the pointer goes. Not declared: the deps field stays, which the shipped
    # grammar drops — so this really is the project's statement and not an edit to it.
    assert not ledger.ref_required and ledger.deps_field


def test_the_markers_are_named_and_never_spelled(tmp_path):
    # A grammar naming `✅` would be a second declaration of the one `[markers] shipped`
    # already makes, and the two would disagree the first time a project changed a glyph.
    write(
        tmp_path,
        'prefix = "RK"\n[markers]\nshipped = "🎉"\n'
        '[grammar.changelog]\nmarkers = ["shipped"]\n',
    )
    assert Config.discover(tmp_path).schema_for("changelog").markers == ("🎉",)


def test_a_drop_naming_a_slot_the_format_has_not_got_is_refused(tmp_path):
    # The boundary the declaration is worth having: a name taken rather than checked is a
    # slot the author believes is gone, which is the failure an ignored typo already is.
    path = write(tmp_path, 'prefix = "RK"\n[grammar.changelog]\ndrop = ["symptoms"]\n')
    with pytest.raises(ConfigError, match="grammar.changelog.drop names symptoms"):
        Config.load(path)


def test_a_grammar_for_a_file_the_project_does_not_govern_is_refused(tmp_path):
    path = write(tmp_path, 'prefix = "RK"\n[grammar.readme]\ndrop = ["deps"]\n')
    with pytest.raises(ConfigError, match="grammar.readme is not a role"):
        Config.load(path)


def test_an_unknown_key_in_a_grammar_is_refused_like_every_other_table(tmp_path):
    path = write(tmp_path, 'prefix = "RK"\n[grammar.changelog]\nstates = "shipped"\n')
    with pytest.raises(ConfigError, match="grammar.changelog.states"):
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


def test_which_markers_still_need_designing_is_declared(tmp_path):
    # RK83's whole configuration surface: `pick` acts on this distinction, and which
    # codepoint carries it is the project's to say (L6).
    path = write(tmp_path, f'[markers]\nopen = ["{DESIGNED}", "{IDEA}"]\nundesigned = ["{IDEA}"]\n')
    assert Config.load(path).schema.undesigned == (IDEA,)
    assert Config.load(path).schema.needs_design(IDEA)


def test_an_undesigned_marker_no_line_may_carry_is_refused(tmp_path):
    # Refused where it is typed, like the shipped/deferred clash: a `--designed` that
    # silently sets nothing aside is a filter its author believes is in force and is not.
    path = write(tmp_path, f'[markers]\nopen = ["{DESIGNED}"]\nundesigned = ["{IDEA}"]\n')
    with pytest.raises(ConfigError, match="markers.open does not"):
        Config.load(path)


def test_the_default_narrows_to_the_markers_the_project_opens_with(tmp_path):
    # Undeclared, and 💭 not in the open set: an empty list rather than a default naming
    # a codepoint no line here can carry.
    path = write(tmp_path, f'[markers]\nopen = ["{DESIGNED}"]\n')
    assert Config.load(path).schema.undesigned == ()
    assert Config.load(write(tmp_path, "prefix = \"RK\"\n")).schema.undesigned == (IDEA,)


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


def test_a_project_declares_the_shape_its_ids_are_spelled_in(tmp_path):
    # RK106: Dumont pads D01-D09 and Turing sub-letters T24b, and both were reported as
    # malformed by a format that had never been asked whether a declared shape is legal.
    write(tmp_path, '[ids]\npad = 2\nsuffix = true\n')
    schema = Config.discover(tmp_path).schema
    assert (schema.id_pad, schema.id_suffix) == (2, True)


def test_a_project_that_declares_no_shape_reads_the_one_it_always_did(tmp_path):
    assert Config.parse({}, root=tmp_path).schema.id_pad == 1
    assert Config.parse({}, root=tmp_path).schema.id_suffix is False


def test_a_width_that_is_not_a_positive_integer_is_refused(tmp_path):
    path = write(tmp_path, "[ids]\npad = 0\n")
    with pytest.raises(ConfigError, match="ids.pad must be a positive integer"):
        Config.load(path)


def test_an_unknown_id_key_is_refused_like_any_other(tmp_path):
    path = write(tmp_path, '[ids]\nseparator = "-"\n')
    with pytest.raises(ConfigError, match="ids.separator"):
        Config.load(path)


# -- the statement that was not the problem (RK1030) -------------------------


MARK = b"\xef\xbb\xbf"


def test_a_config_saved_with_a_mark_is_answered_with_the_byte(tmp_path):
    """The reproduction. `Invalid statement (at line 1, column 1)` is `tomllib` answering
    about `prefix = "RK"`, which is correct — and the file is the first one a project writes,
    on the platform whose default way to write it adds the mark."""
    path = tmp_path / "roadkeep.toml"
    path.write_bytes(MARK + b'prefix = "RK"\n')
    with pytest.raises(ConfigError) as caught:
        Config.load(path)
    said = str(caught.value)
    assert "byte-order mark (U+FEFF)" in said
    # The original refusal is carried rather than replaced: it is still what `tomllib` said,
    # and a reader who knows TOML should not have to take this sentence's word for it.
    assert "Invalid statement (at line 1, column 1)" in said
    assert "Set-Content -Encoding utf8" in said
    assert str(path) in said


def test_every_other_toml_error_is_handed_back_as_it_was_written(tmp_path):
    """The bound. This reads the bytes only after a refusal, and only to answer the one
    question the refusal could not — so a file with a real syntax error is unchanged."""
    path = tmp_path / "roadkeep.toml"
    path.write_bytes(b'prefix = "RK"\nthis is not toml\n')
    with pytest.raises(tomllib.TOMLDecodeError) as caught:
        Config.load(path)
    assert "byte-order mark" not in str(caught.value)


def test_a_marked_pyproject_is_found_and_refused_rather_than_walked_past(tmp_path):
    """The same byte through the other door, where it failed *silently*: the probe that
    decides whether a `pyproject.toml` configures roadkeep swallowed the decode error, so
    discovery walked past a file declaring `[tool.roadkeep]` and every verb ran on defaults."""
    (tmp_path / "pyproject.toml").write_bytes(MARK + b'[tool.roadkeep]\nprefix = "RK"\n')
    assert find_config(tmp_path) == tmp_path / "pyproject.toml"
    with pytest.raises(ConfigError) as caught:
        Config.discover(tmp_path)
    assert "byte-order mark (U+FEFF)" in str(caught.value)


def test_a_pyproject_that_configures_nothing_is_still_walked_past(tmp_path):
    """The strip is a question about *which file* and never about its content: a marked
    pyproject with no `[tool.roadkeep]` is not this project's config, mark or no mark."""
    (tmp_path / "pyproject.toml").write_bytes(MARK + b'[tool.black]\nline-length = 88\n')
    assert find_config(tmp_path) is None


# -- which directory a path argument is read from (RK1103) --------------------


def _arguments() -> dict[str, set[str]]:
    """Every dest this CLI declares, by subcommand path — `""` for the top-level parser."""
    import argparse

    from roadkeep.cli import build_parser

    out: dict[str, set[str]] = {}

    def walk(parser, prefix: str = "") -> None:
        for action in parser._actions:
            if isinstance(action, argparse._SubParsersAction):
                for name, sub in action.choices.items():
                    walk(sub, f"{prefix}{name} ".strip() if not prefix else f"{prefix} {name}")
                continue
            if action.dest not in ("help", "handler"):
                out.setdefault(prefix, set()).add(action.dest)

    walk(build_parser())
    return out


def test_every_classified_path_argument_is_one_this_cli_declares():
    """`_DIVERGENT`'s rule, applied to the classification RK1103 made.

    A key naming no argument is the failure a table has: the entry stops matching, nothing
    says so, and the rule it encoded quietly stops applying to a renamed flag.
    """
    declared = _arguments()
    for command, rows in PATH_ARGUMENTS.items():
        assert command in declared, f"{command!r} is not a subcommand of this CLI"
        missing = set(rows) - declared[command]
        assert not missing, f"{command}: {sorted(missing)} is not an argument it takes"


def test_every_class_is_one_of_the_three_the_rule_names():
    # Three and not two, which is the finding RK1103 produced: a claim's scope is repo-relative
    # text that is never resolved, because resolving `src/` would stop it covering `src/a.py`.
    assert {one for rows in PATH_ARGUMENTS.values() for one in rows.values()} == {
        "project",
        "caller",
        "repo",
    }


def test_a_path_argument_spelled_the_obvious_way_is_classified():
    """The partial guard, and its limit is the honest part (RK1103).

    No property of an argparse argument marks it as carrying a path — `--with` is `alongside`
    and `install --source` reads as neither — so completeness cannot be checked. What can is
    the common spelling: a new `--out-dir` or `--body-file` that nobody classified is a red.
    """
    import re

    spelled = re.compile(rf"(^|_)({'|'.join(PATH_SPELLINGS)})$")
    unclassified = {
        (command, dest)
        for command, dests in _arguments().items()
        for dest in dests
        if spelled.search(dest) and dest not in PATH_ARGUMENTS.get(command, {})
    }
    assert not unclassified, (
        f"{sorted(unclassified)} looks like a path and is in no class: add it to "
        f"PATH_ARGUMENTS as project, caller or repo"
    )


def test_a_claims_scope_is_never_resolved(tmp_path):
    """The class that would break if the rule were applied everywhere (RK1103).

    `claim --path src/` becomes a `git add --` argument matched against what git reports, and
    git reports repo-relative paths. `Config.locate` would make it absolute and `_covers` would
    stop answering — the directory scope RK495 exists for would cover nothing.
    """
    write(tmp_path, 'prefix = "RK"\n')
    config = Config.discover(tmp_path)
    assert PATH_ARGUMENTS["claim"] == {"path": "repo", "add_path": "repo"}
    # And the rule itself still does what it says on the class that takes it.
    assert config.locate("docs/ROADMAP.md") == config.root / "docs" / "ROADMAP.md"
    assert config.locate(tmp_path / "elsewhere.md") == tmp_path / "elsewhere.md"
