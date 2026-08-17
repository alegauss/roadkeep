"""The surfaces a project gets when the plugin is not what installed it (RK100).

`roadkeep install` exists because adoption has five surfaces and `init` scaffolds three. The
missing two are the harness — the server, the guard, the skill — and they ship with the
plugin, which a project can only install from a marketplace. An early adopter runs a sibling
checkout instead, so the first one vendored a copy of `SKILL.md` with a comment saying where
it came from, and nothing kept the two in step.

What the tests below hold, in the order the module's decisions were made:

* **Translated, never restated.** The events, the matcher, the timeouts and the server argv
  are asserted *equal to the plugin's own files* with one substitution applied. A test that
  spelled out the expected matcher would be the third copy of it, and the second one that can
  go stale — the very failure the command is for.
* **The copy is byte-identical, and a gate says so.** `--check` exits 1 on a skill that
  drifted, which is what turns "re-copy it after an upgrade" from a comment into a build
  failure. It is asserted to write nothing, because a check that repaired what it found
  would report a clean tree on the run that changed it.
* **A declaration is merged, never replaced.** Other tools declare in `.claude/settings.json`
  and `.mcp.json`. What is not this project's entry survives; an existing file that will not
  parse refuses the whole run rather than being overwritten.
* **The workflow is written once.** `baseline:` and `directory:` are what an adopting
  repository tunes, so refreshing that file would overwrite the only part of it that is theirs.
* **All-or-nothing, as `init` has it.** Every refusal happens before the first file is opened.
"""

from __future__ import annotations

import json
import shlex
import shutil
from dataclasses import fields
from pathlib import Path

import pytest

from roadkeep.adopting import BlockedParent
from roadkeep.cli import EXIT_GATE, EXIT_OK, build_parser, main
from roadkeep.rendering import registration_report
from roadkeep.merging import Attributes, Driver, Registration, Wiring
from roadkeep.installing import (
    AGREED,
    BEHIND,
    UNPINNABLE,
    CARRIED,
    LAUNCHER,
    PLUGIN_HOOKS,
    PLUGIN_MANIFEST,
    PLUGIN_MCP,
    PLUGIN_ROOT,
    PLUGIN_SKILL,
    PROJECT_MCP,
    PROJECT_SETTINGS,
    PROJECT_SKILL,
    PROJECT_WORKFLOW,
    NotAnAdopter,
    NotShipped,
    Unanchored,
    Unreadable,
    _ENTRY_RE,
    _entry,
    Plan,
    Removal,
    install,
    plan,
    removal,
    uninstall,
)

HERE = Path(__file__).resolve().parents[1]

#: What the fixture below copies: the module's own list (RK235), so a sixth surface reaches
#: this fixture by being declared once. Copied rather than pointed at, so the two directories
#: are siblings on one filesystem and the launcher comes out relative — the case every
#: adopting project is in.
COPIED = CARRIED


@pytest.fixture
def source(tmp_path: Path) -> Path:
    """A checkout of this tool, beside the project that will adopt it."""
    root = tmp_path / "roadkeep"
    for part in COPIED:
        target = root / part
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(HERE / part, target)
    return root


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """A repository that already has CI, so all four surfaces are in play."""
    root = tmp_path / "adopter"
    (root / ".github" / "workflows").mkdir(parents=True)
    return root


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def loaded(path: Path) -> dict:
    return json.loads(read(path))


# -- what it writes ----------------------------------------------------------


def test_it_writes_the_two_surfaces_init_does_not_scaffold(project, source):
    written = {surface.path for surface in install(project, source=source).changing}
    assert written == {
        project / PROJECT_MCP,
        project / PROJECT_SETTINGS,
        project / PROJECT_SKILL,
        project / PROJECT_WORKFLOW,
    }
    for path in written:
        assert path.is_file()


def test_the_skill_is_the_shipped_file_with_its_entry_point_re_addressed(project, source):
    """The defect itself: a vendored authority is read with the trust of the original.

    So the copy is the shipped bytes everywhere except the one sentence that would be false
    here (RK137) — the package is not installed in an adopting project, and `roadkeep` is on
    no PATH, which is a command that fails at exactly the moment the skill is being read.
    """
    install(project, source=source)
    copied = read(project / PROJECT_SKILL)
    shipped = read(HERE / PLUGIN_SKILL)
    assert "`roadkeep` is the installed entry point" in shipped
    assert "`roadkeep` is the installed entry point" not in copied
    assert '`python "../roadkeep/scripts/roadkeep.py"` is this project\'s entry point' in copied
    # And nothing else moved: one sentence out, one sentence in.
    assert _ENTRY_RE.sub("", shipped) == _ENTRY_RE.sub("", copied).replace(
        _entry("../roadkeep/scripts/roadkeep.py"), ""
    )


def test_a_skill_that_stopped_naming_its_entry_point_is_a_refusal(project, source, tmp_path):
    """Never a verbatim copy: that is the defect, and it would be shipped silently."""
    skill = source / PLUGIN_SKILL
    skill.write_text("# roadkeep\n\nNothing about an entry point.\n", encoding="utf-8")
    with pytest.raises(Unanchored) as refused:
        install(project, source=source)
    assert "0 time(s)" in str(refused.value)
    assert not (project / PROJECT_SKILL).exists()


def test_the_hooks_are_the_plugin_s_own_with_the_launcher_re_addressed(project, source):
    """Not a second statement of the events, the matcher or the timeouts.

    A matcher added to `hooks/hooks.json` reaches every adopting project on its next
    `install`, and this test is what says so — it compares against that file, substituted.
    """
    install(project, source=source)
    written = json.dumps(loaded(project / PROJECT_SETTINGS)["hooks"])
    shipped = json.dumps(loaded(HERE / PLUGIN_HOOKS)["hooks"])
    assert written == shipped.replace(PLUGIN_ROOT, "${CLAUDE_PROJECT_DIR}/../roadkeep")


def test_every_command_it_wires_is_one_the_cli_accepts(project, source):
    """The same argument `tests/test_surfaces.py` makes about the Action and the pre-commit
    hook: a surface that drifts from the CLI fails a test instead of failing a session."""
    install(project, source=source)
    settings = loaded(project / PROJECT_SETTINGS)
    commands = [
        hook["command"]
        for groups in settings["hooks"].values()
        for group in groups
        for hook in group["hooks"]
    ]
    assert len(commands) == 3
    for command in commands:
        assert build_parser().parse_args(shlex.split(command)[2:]).command == "guard"
    server = loaded(project / PROJECT_MCP)["mcpServers"]["roadkeep"]
    assert build_parser().parse_args(server["args"][1:]).command == "mcp"


def test_the_server_is_approved_so_it_starts_unasked(project, source):
    """A project `.mcp.json` waits for approval, and one awaiting approval never ran."""
    install(project, source=source)
    assert loaded(project / PROJECT_SETTINGS)["enabledMcpjsonServers"] == ["roadkeep"]


def test_the_launcher_is_addressed_from_the_project_and_not_from_this_machine(project, source):
    """A sibling pair wires up the same on every machine that has them, so the declaration
    is committable — an absolute path in `.claude/settings.json` is one developer's tree."""
    intent = install(project, source=source)
    assert intent.launcher == f"../roadkeep/{LAUNCHER}"
    for path in (PROJECT_MCP, PROJECT_SETTINGS):
        assert str(source) not in read(project / path)
        assert "${CLAUDE_PROJECT_DIR" in read(project / path)


def test_wiring_this_repository_to_itself_writes_the_declaration_it_already_carries():
    """The conformance case: this repository runs the tool from its own checkout (RK81), and
    what it declares by hand is what this command would have written for it."""
    intent = plan(HERE, source=HERE)
    written, = [s for s in intent.surfaces if s.path == HERE / PROJECT_MCP]
    assert json.loads(written.text) == loaded(HERE / PROJECT_MCP)
    assert not written.stale


def test_the_plugin_s_own_root_is_wired_and_never_copied_into(capsys):
    """The two declarations mean what they mean here; the two copies do not (RK235).

    Run at this root it used to compute a vendored `SKILL.md` beside the `skills/` one it had
    just read, and a `roadkeep.yml` beside the `gate.yml` that already calls the action — so
    `--check` exited 1 on surfaces that were not an installation, at the root every
    contributor is at. A check nobody can act on is a check switched off (RK140's lesson).
    """
    intent = plan(HERE, source=HERE)
    # The settings surface left this list with RK402: this tree declares the guard as a
    # plugin, so writing the same hooks here would run it twice on every turn — the third
    # member of the set the two below were already in, and the one that kept `--check`
    # reporting `1 surface(s) differ` at this root permanently.
    assert [s.path.relative_to(HERE).as_posix() for s in intent.surfaces] == [PROJECT_MCP]
    named = dict(intent.skipped)
    assert "run it twice" in named[PROJECT_SETTINGS]
    assert "ships skills/roadkeep/SKILL.md" in named[PROJECT_SKILL]
    assert "*is* the action" in named[PROJECT_WORKFLOW]
    assert not (HERE / PROJECT_SKILL).exists(), "and nothing was written here"

    # Named, never silent — and under a label that does not tell the reader to write them:
    # `CONTRIBUTING.md`'s own reason is the only place "by hand" belongs.
    assert main(["-C", str(HERE), "install", "--check"]) in (0, 1)
    out = capsys.readouterr().out
    assert "not written    .github/workflows/roadkeep.yml" in out
    assert "  by hand  " not in out


# -- and what it leaves alone ------------------------------------------------


def test_a_declaration_keeps_everything_that_is_not_this_project_s_entry(project, source):
    project.mkdir(parents=True, exist_ok=True)
    (project / ".claude").mkdir()
    (project / PROJECT_SETTINGS).write_text(
        json.dumps(
            {
                "enabledMcpjsonServers": ["another"],
                "permissions": {"allow": ["Bash(pytest:*)"]},
                "hooks": {"Stop": [{"hooks": [{"type": "command", "command": "make lint"}]}]},
            }
        ),
        encoding="utf-8",
    )
    (project / PROJECT_MCP).write_text(
        json.dumps({"mcpServers": {"another": {"command": "node", "args": ["s.js"]}}}),
        encoding="utf-8",
    )
    install(project, source=source)

    settings = loaded(project / PROJECT_SETTINGS)
    assert settings["permissions"] == {"allow": ["Bash(pytest:*)"]}
    assert settings["enabledMcpjsonServers"] == ["another", "roadkeep"]
    stop = [hook["command"] for group in settings["hooks"]["Stop"] for hook in group["hooks"]]
    assert "make lint" in stop and len(stop) == 2
    assert set(loaded(project / PROJECT_MCP)["mcpServers"]) == {"another", "roadkeep"}


def test_a_declaration_it_cannot_parse_refuses_the_whole_run(project, source):
    (project / ".claude").mkdir(parents=True)
    (project / PROJECT_SETTINGS).write_text("{ not json", encoding="utf-8")
    with pytest.raises(Unreadable):
        install(project, source=source)
    # All-or-nothing, as `init` has it: the surfaces that could have been written are not.
    assert not (project / PROJECT_MCP).exists()
    assert not (project / PROJECT_SKILL).exists()


def test_the_workflow_is_written_once_and_is_the_adopter_s_after_that(project, source):
    install(project, source=source)
    tuned = read(project / PROJECT_WORKFLOW).replace(
        "- uses: alegauss/roadkeep@main",
        "- uses: alegauss/roadkeep@main\n        with: {baseline: origin/main}",
    )
    (project / PROJECT_WORKFLOW).write_text(tuned, encoding="utf-8")
    again = install(project, source=source)
    assert read(project / PROJECT_WORKFLOW) == tuned
    kept, = [s for s in again.surfaces if s.path == project / PROJECT_WORKFLOW]
    assert kept.state == "kept"


def test_the_workflow_it_writes_is_valid_yaml_calling_the_action_this_repo_publishes(
    project, source
):
    # Structure, when a parser is available — skipped rather than made a dev dependency, as
    # `tests/test_surfaces.py` has it: the tool never reads YAML.
    yaml = pytest.importorskip("yaml", reason="pyyaml is not installed")
    install(project, source=source)
    workflow = yaml.safe_load(read(project / PROJECT_WORKFLOW))
    step = workflow["jobs"]["lint"]["steps"][-1]
    repository = loaded(HERE / PLUGIN_MANIFEST)["repository"]
    assert step["uses"].split("@")[0] == repository.removeprefix("https://github.com/")


def test_a_project_with_no_ci_gets_no_workflow_and_is_told_so(tmp_path, source):
    bare = tmp_path / "bare"
    intent = install(bare, source=source)
    assert not (bare / PROJECT_WORKFLOW).exists()
    assert any(path == PROJECT_WORKFLOW for path, _ in intent.skipped)


def test_the_line_in_contributing_is_named_and_not_written(project, source):
    """Prose about a project's own contribution policy, which this tool does not write (L4)."""
    intent = install(project, source=source)
    assert any("CONTRIBUTING.md" in why for _, why in intent.skipped)
    assert not (project / "CONTRIBUTING.md").exists()


# -- and what keeps it in step -----------------------------------------------


def test_running_it_twice_changes_nothing(project, source):
    install(project, source=source)
    before = {path: read(path) for path in sorted(project.rglob("*")) if path.is_file()}
    again = install(project, source=source)
    assert again.changing == ()
    assert {path: read(path) for path in before} == before


def test_a_drifted_copy_is_refreshed_by_a_rerun(project, source):
    install(project, source=source)
    (project / PROJECT_SKILL).write_text("stale\n", encoding="utf-8")
    refreshed, = install(project, source=source).changing
    assert refreshed.path == project / PROJECT_SKILL
    # The shipped bytes again, entry point included — a rerun is the same translation.
    assert read(project / PROJECT_SKILL) == refreshed.text
    assert _entry("../roadkeep/scripts/roadkeep.py") in read(project / PROJECT_SKILL)


def test_check_reports_the_drift_and_writes_nothing(project, source):
    install(project, source=source)
    (project / PROJECT_SKILL).write_text("stale\n", encoding="utf-8")
    intent = plan(project, source=source)
    assert [s.path for s in intent.changing] == [project / PROJECT_SKILL]
    assert read(project / PROJECT_SKILL) == "stale\n", "a check that repaired reports clean"


# -- and the gate asking it, because nobody runs the check (RK1192) ------------


def wired(project: Path) -> Path:
    """A project installed from **the checkout that answers**, which is what the gate reads.

    The `source` fixture is a copy beside the project, and `stale` re-plans from `_source()` —
    the engine running this process — deliberately (RK1192): three copies are allowed to
    differ and `engines` adjudicates that, so the gate compares against the one that would do
    the writing. Installing from anywhere else makes every surface differ by its launcher
    path, which is a true answer to a question these tests are not asking.
    """
    return declaring(project, CLEAN)


def test_the_gate_reports_a_surface_the_check_would_have(project):
    """The defect: `install --check` answers this exactly and is a command nobody thinks to
    run. Measured on another project — a committed launcher predating RK1116 forwarded only
    `guard` and `mcp`, the server had not connected, and the skill named that launcher as the
    entry point. Every door shut at once, and the way out was guessing a version directory
    under the plugin cache. `lint` fires every turn through the `Stop` hook, so it asks."""
    from roadkeep.config import Config
    from roadkeep.linting import lint

    install(wired(project), source=HERE)
    assert lint(Config.discover(project)).clean, "installed and clean is the starting state"

    (project / PROJECT_SKILL).write_text("stale\n", encoding="utf-8")
    report = lint(Config.discover(project))
    (found,) = [one for one in report.findings if one.code == "install.stale"]
    # Filed at the surface, unlike `budget.tool`: there is a path a reader can open, and it is
    # the file that drifted.
    assert found.file == PROJECT_SKILL
    assert "install" in found.message


def test_a_project_that_pinned_its_version_is_not_told_every_turn(project):
    """The half this could not ship without. The gate fires on every turn, so a project that
    has *decided* to sit on an older surface would be told about its own decision for as long
    as it holds — and a finding a reader learns to skip is how a gate stops being read."""
    from roadkeep.config import Config
    from roadkeep.linting import lint

    install(wired(project), source=HERE)
    (project / PROJECT_SKILL).write_text("stale\n", encoding="utf-8")
    (project / "roadkeep.toml").write_text(
        CLEAN[0] + "\n[install]\npinned = true\n", encoding="utf-8"
    )
    assert lint(Config.discover(project)).clean

    # It silences the finding and never the state: the check still reports the drift, because
    # what was declared is a decision about which version to run and not that the files agree.
    assert [s.path for s in plan(project, source=HERE).changing] == [
        project / PROJECT_SKILL
    ]


def test_an_unwired_project_has_no_vendored_copy_to_be_behind(project, source):
    """Every plugin-served project, which is most of them: there is no copy to drift, and the
    one `is_file` that says so is what the whole check costs them."""
    from roadkeep.config import Config
    from roadkeep.linting import lint

    declaring(project, CLEAN)
    assert not (project / PROJECT_SKILL).exists()
    assert lint(Config.discover(project)).clean


def test_check_is_the_gate_and_the_exit_code_is_the_contract(project, source, capsys):
    argv = ["-C", str(project), "install", "--source", str(source)]
    assert main(argv) == 0
    assert main([*argv, "--check"]) == 0
    (project / PROJECT_SKILL).write_text("stale\n", encoding="utf-8")
    assert main([*argv, "--check"]) == 1
    assert "would update" in capsys.readouterr().out


# -- the fifth surface (RK148) ------------------------------------------------


def test_the_merge_driver_is_named_even_though_it_is_not_written(project, source, capsys):
    """Opt-in was never the problem; being unmentioned was — the failure landed later and
    looked like the tool's: two branches spend one id and the fix is the denied hand edit."""
    intent = install(project, source=source)
    named = dict(intent.skipped)
    assert ".gitattributes" in named
    assert "merge --register" in named[".gitattributes"]
    assert "--register-merge" in named[".gitattributes"]

    assert main(["-C", str(project), "install", "--source", str(source)]) == 0
    assert "not written    .gitattributes" in capsys.readouterr().out


def test_the_flag_writes_the_attribute_half_and_prints_the_config_half(project, source, capsys):
    declaring(project, CLEAN)
    argv = ["-C", str(project), "install", "--source", str(source), "--register-merge"]
    assert main(argv) == 0
    out = capsys.readouterr().out
    assert "ROADMAP.md merge=roadkeep" in (project / ".gitattributes").read_text(
        encoding="utf-8"
    )
    assert "registered     .gitattributes  + ROADMAP.md merge=roadkeep" in out
    # Printed and never run: setting somebody's git config is a write outside these files.
    assert "git config merge.roadkeep.driver" in out
    # And the unwritten list no longer names it, a surface being written not being one skipped.
    assert ".gitattributes" not in dict(plan(project, source=source, registering=True).skipped)


def test_the_json_carries_every_field_the_registration_has(project, source, capsys):
    # RK276. `merge --register` and `install --register-merge` are one write (RK148), and the
    # third line RK274 added reached one surface — so what is asserted is not that line but the
    # *shape*: the next field added to `Registration` fails here rather than going quiet in the
    # reading most likely to be automated.
    declaring(project, CLEAN)
    argv = ["-C", str(project), "install", "--source", str(source), "--register-merge", "--json"]
    assert main(argv) == 0
    registered = json.loads(capsys.readouterr().out)["registered"]
    assert set(registered) == {field.name for field in fields(Registration)}


#: A registration carrying something in every field, so the report below has all of them to
#: drop. Built rather than measured: the state that exercises `left_alone` and `present` at
#: once is one a real project reaches only after somebody wired another driver by hand.
FULL = Registration(
    attributes=Path(".gitattributes"),
    added=("docs/ROADMAP.md merge=roadkeep",),
    present=("docs/CHANGELOG.md merge=roadkeep",),
    command='git config merge.roadkeep.driver "somewhere merge %O %A %B --path %P"',
    invalidated_by="a plugin update",
    wiring=Wiring(
        attributes=Attributes(
            path=Path(".gitattributes"),
            wanted=("docs/ROADMAP.md merge=roadkeep",),
            present=(),
            resolved=(("docs/ROADMAP.md", "roadkeep"),),
        ),
        driver=Driver(stored="", wanted="somewhere", known=True),
    ),
    left_alone=(("docs/IMPROVEMENTS.md", "theirs"),),
)


def test_the_report_carries_every_field_of_the_registration(capsys):
    # RK276, over the text. RK274 added a third line and it reached one of two surfaces, under
    # a comment claiming they printed the same. There is one rendering now, and this asserts
    # what it must not drop — a field whose content appears nowhere is the same silence again.
    said = "\n".join(registration_report(FULL, ".gitattributes", 0))
    assert FULL.added[0] in said and FULL.present[0] in said
    assert FULL.left_alone[0][0] in said and FULL.left_alone[0][1] in said
    assert FULL.command in said and FULL.invalidated_by in said
    assert "merge.roadkeep.driver" in said


def test_the_two_indents_are_the_only_difference_between_the_surfaces(capsys):
    # One rendering, two callers, one parameter between them: the install report pads its verbs
    # to a column the merge report does not, and that column was what pushed them apart.
    plain = registration_report(FULL, ".gitattributes", 0)
    padded = registration_report(FULL, ".gitattributes", 14)
    assert len(plain) == len(padded)
    for bare, wide in zip(plain, padded):
        # Same words in the same order, once the padding and the install report's own verb go.
        assert bare.split() == [word for word in wide.split() if word != "registered"]


def test_the_flag_refuses_a_project_that_declares_no_governed_file(project, source):
    """A driver is wired per governed file, so a default config's paths are nobody's."""
    with pytest.raises(ValueError, match="declares no roadkeep.toml"):
        install(project, source=source, register_merge=True)


def test_a_check_never_registers_anything(project, source):
    declaring(project, CLEAN)
    assert main(["-C", str(project), "install", "--source", str(source), "--check"]) == 1
    assert not (project / ".gitattributes").exists()


# -- the workflow's own default (RK140) ---------------------------------------

#: A project the gate would pass, and one it would not: a roadmap line with no pointer is a
#: finding, and a finding on the day the workflow lands is a gate switched off rather than read.
CLEAN = (
    'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\n',
    "# Roadmap\n\n## Block A\n\n",
)
IN_DEBT = (
    CLEAN[0],
    "# Roadmap\n\n## Block A\n\n- 📋 **RK1** (deps: —) **A symptom** — Because of a reason.\n",
)


def declaring(project: Path, config_and_roadmap) -> Path:
    config, roadmap = config_and_roadmap
    project.mkdir(parents=True, exist_ok=True)
    (project / "roadkeep.toml").write_text(config, encoding="utf-8")
    (project / "ROADMAP.md").write_text(roadmap, encoding="utf-8")
    return project


def test_a_clean_project_gets_the_strict_gate(project, source):
    install(declaring(project, CLEAN), source=source)
    written = read(project / PROJECT_WORKFLOW)
    # The advice is still in the comment; what a clean project does not get is the setting.
    assert "github.base_ref" not in written and "fetch-depth" not in written
    assert plan(project, source=source).debt == 0


def test_a_backlog_with_standing_debt_gets_the_baseline_and_the_count(project, source):
    """The projects that most need the gate carry the most debt, so the strict default is
    the one that lands red — and a baseline nobody remembers to remove is the other half."""
    intent = install(declaring(project, IN_DEBT), source=source)
    written = read(project / PROJECT_WORKFLOW)
    assert intent.debt == 1
    assert "baseline: origin/${{ github.base_ref" in written
    assert "fetch-depth: 0" in written  # a baseline is a rev, so the diff needs the history
    assert "reported 1 finding(s) here" in written
    assert "Drop the `baseline:` line" in written


def test_a_project_declaring_nothing_is_not_reported_as_clean_or_in_debt(project, source):
    """No governed file is nothing to be in debt about, and the strict gate is honest there."""
    assert plan(project, source=source).debt is None
    install(project, source=source)
    assert "github.base_ref" not in read(project / PROJECT_WORKFLOW)


def test_the_baseline_is_named_in_the_report_and_in_the_json(project, source, capsys):
    argv = ["-C", str(declaring(project, IN_DEBT)), "install", "--source", str(source)]
    assert main(argv) == 0
    assert "1 standing finding(s) here" in capsys.readouterr().out
    assert main([*argv, "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["debt"] == 1


# -- the way out (RK138) ------------------------------------------------------


def test_uninstall_returns_the_project_to_the_state_install_found_it_in(project, source):
    """Three surfaces removed with `rm` was the measured alternative, safe only by luck."""
    install(project, source=source)
    taken = uninstall(project)
    assert {w.path for w in taken.changing} == {
        project / PROJECT_MCP,
        project / PROJECT_SETTINGS,
        project / PROJECT_SKILL,
    }
    for path in (PROJECT_MCP, PROJECT_SETTINGS, PROJECT_SKILL):
        assert not (project / path).exists()
    # And the directories the copy was alone in, so nothing reads as a vendored skill.
    assert not (project / ".claude").exists()
    # The gate stays: it calls the published action, not the checkout being un-wired.
    assert (project / PROJECT_WORKFLOW).is_file()


def test_it_keeps_every_entry_that_is_not_this_project_s(project, source):
    """The rule the write path has, applied on the way out — which is the whole task."""
    install(project, source=source)
    mcp = loaded(project / PROJECT_MCP)
    mcp["mcpServers"]["other"] = {"command": "node", "args": ["server.js"]}
    (project / PROJECT_MCP).write_text(json.dumps(mcp, indent=2), encoding="utf-8")
    settings = loaded(project / PROJECT_SETTINGS)
    settings["model"] = "opus"
    settings["hooks"]["Stop"].append({"hooks": [{"type": "command", "command": "make docs"}]})
    (project / PROJECT_SETTINGS).write_text(json.dumps(settings, indent=2), encoding="utf-8")

    uninstall(project)
    assert loaded(project / PROJECT_MCP) == {
        "mcpServers": {"other": {"command": "node", "args": ["server.js"]}}
    }
    left = loaded(project / PROJECT_SETTINGS)
    assert left["model"] == "opus"
    assert left["hooks"] == {"Stop": [{"hooks": [{"type": "command", "command": "make docs"}]}]}
    # The approval goes with the server it approves, and the emptied events go entirely:
    # an event declaring no group is a project that declares a hook.
    assert "enabledMcpjsonServers" not in left and "PreToolUse" not in left["hooks"]


def test_un_wiring_the_plugin_from_itself_is_refused(capsys):
    """The other direction of RK235, and the one with no narrowing available: the entries at
    this root are the tree's own (RK81), not a copy of somebody's wiring to withdraw."""
    with pytest.raises(NotAnAdopter, match="ships the plugin rather than adopting it"):
        uninstall(HERE)
    assert main(["-C", str(HERE), "uninstall", "--check"]) == 2
    assert "git checkout" in capsys.readouterr().err
    assert (HERE / PROJECT_MCP).is_file()


def test_un_wiring_a_project_that_was_never_wired_takes_nothing(project):
    taken = uninstall(project)
    assert taken.changing == ()
    # Four since RK1108 added the committed bridge, which `removal` asks the disk about for the
    # reason it asks about everything else: it reads no checkout, so it cannot know which flag
    # wired this project. Absent is absent either way.
    assert [w.state for w in taken.withdrawals] == ["absent"] * 4


def test_uninstall_check_is_the_same_answer_and_writes_nothing(project, source, capsys):
    install(project, source=source)
    argv = ["-C", str(project), "uninstall"]
    assert main([*argv, "--check"]) == 1
    assert "would delete" in capsys.readouterr().out
    assert (project / PROJECT_MCP).is_file(), "a check that un-wired reports clean"
    assert main(argv) == 0
    assert main([*argv, "--check"]) == 0


def test_nothing_is_reported_kept_where_nothing_is_there(project, source, capsys):
    # RK284: `install` told this project "no .github/workflows/ — this project has no CI to
    # gate", and `uninstall` then said it kept the workflow and to delete it. Neither the file
    # nor `.github` existed. A surface never present was not kept, and naming it does what
    # this field exists to prevent — "a surface silently kept reads as missed" — from the
    # other side.
    install(project, source=source)
    # The state a project with no CI is in — this fixture has a `.github/`, so the workflow
    # was written; the case RK284 was measured on had neither the file nor the directory.
    shutil.rmtree(project / ".github")
    assert not (project / PROJECT_WORKFLOW).exists()
    assert removal(project).kept == ()
    assert main(["-C", str(project), "uninstall"]) == 0
    # By line, not by substring: pytest's own tmp directory is named after this test.
    printed = capsys.readouterr().out.splitlines()
    assert not [line for line in printed if line.strip().startswith("kept")]


def test_a_workflow_that_is_there_is_still_reported_kept(project, source, capsys):
    """The other direction, so the fix is an `exists` test and not a deletion: the gate calls
    the published action, so a workflow left behind really does keep CI wired."""
    install(project, source=source)
    workflow = project / PROJECT_WORKFLOW
    workflow.parent.mkdir(parents=True, exist_ok=True)
    workflow.write_text("name: gate\n", encoding="utf-8")
    assert [path for path, _ in removal(project).kept] == [PROJECT_WORKFLOW]
    assert main(["-C", str(project), "uninstall"]) == 0
    printed = capsys.readouterr().out
    assert f"kept           {PROJECT_WORKFLOW}" in printed and "CI stays wired" in printed
    # And it is kept in the sense the word means: still on disk afterwards.
    assert workflow.is_file()


#: The one rename each of these payloads makes (RK289), declared for the reason the estimate's
#: is: `withdrawals` is what the code took out and `surfaces` is what a reader outside this
#: package calls them. `Plan` renames nothing, and an empty map is the honest way to say so.
PLAN_RENAMES: dict[str, str] = {}
REMOVAL_RENAMES = {"withdrawals": "surfaces"}


def test_the_install_payload_carries_every_field_of_the_plan(project, source, capsys):
    # RK289: RK276 bound `Registration` after a dropped field went quiet in exactly this
    # reading, and the guard was written for that one dataclass only.
    argv = ["-C", str(project), "install", "--source", str(source), "--check", "--json"]
    assert main(argv) == 1
    payload = json.loads(capsys.readouterr().out)
    named = {PLAN_RENAMES.get(field.name, field.name) for field in fields(Plan)}
    assert named <= set(payload)


def test_a_surface_whose_directory_a_file_is_standing_in_stops_the_write(project, source):
    """RK393: RK392's question one command over. The directories were made as the surfaces
    were written, so a `.claude` that is a file left the server declaration on disk with no
    hook and no skill beside it — and `install` states the opposite order in its own prose."""
    project.mkdir(parents=True, exist_ok=True)
    (project / ".claude").write_text("not a directory\n", encoding="utf-8")
    with pytest.raises(BlockedParent):
        install(project, source=source)
    # The one the caller put there, and nothing this command reached for: `.mcp.json` is the
    # surface that used to land before the failure, and its absence is what says nothing ran.
    assert not (project / ".mcp.json").exists()


def test_the_gate_tells_a_blocked_surface_apart_from_a_stale_one(project, source, capsys):
    # The half that matters most: `--check` used to answer "1 surface differs, `install` writes
    # them" about files `install` exits 2 on, so a CI job's red gate named a red command.
    project.mkdir(parents=True, exist_ok=True)
    (project / ".claude").write_text("not a directory\n", encoding="utf-8")
    argv = ["-C", str(project), "install", "--source", str(source), "--check"]
    assert main(argv) == EXIT_GATE
    out, err = capsys.readouterr()
    assert ".claude is a file, so the directory cannot be made" in out
    # Two sentences, because they are two states and only one of them `install` can close.
    assert "cannot be written at all" in err
    assert "surface(s) differ" in err and "3 surface(s) differ" not in err


def test_the_driver_is_refused_before_the_surfaces_land(project, source):
    """RK394: the config `--register-merge` needs was resolved before the first write and the
    `.gitattributes` write was not, so a directory in its place exited 2 with all four
    surfaces on disk — the state this command's own prose says the ordering prevents."""
    project.mkdir(parents=True, exist_ok=True)
    (project / ".gitattributes").mkdir()
    with pytest.raises(BlockedParent):
        install(project, source=source, register_merge=True)
    assert not (project / PROJECT_MCP).exists()
    # And without the flag it is not in anybody's way: the driver is written by `--register-
    # merge` alone, so the same tree wires the four surfaces and says why the fifth is absent.
    assert install(project, source=source).changing


def test_a_surface_that_is_itself_a_directory_is_in_its_own_way(project, source):
    # The half `blocking` missed twice: it answered about ancestors, and a `.mcp.json` that is
    # a directory stops the write as completely as a parent that is a file (RK394).
    project.mkdir(parents=True, exist_ok=True)
    (project / PROJECT_MCP).mkdir()
    with pytest.raises(BlockedParent) as caught:
        install(project, source=source)
    assert "is a directory" in str(caught.value)
    assert not (project / PROJECT_SETTINGS).exists()


def test_the_report_stops_advertising_a_flag_that_would_refuse(project, source, capsys):
    """The question §RK394 left open. `not written` names a remedy on every run, and a remedy
    that exits 2 is a different entry from one the caller has simply not chosen yet."""
    project.mkdir(parents=True, exist_ok=True)
    (project / ".gitattributes").mkdir()
    assert main(["-C", str(project), "install", "--source", str(source), "--check"]) in (
        EXIT_OK,
        EXIT_GATE,
    )
    said = capsys.readouterr().out
    assert "the merge driver cannot be wired here at all" in said
    assert "`install --register-merge` runs it here" not in said


def test_the_uninstall_payload_carries_every_field_of_the_removal(project, source, capsys):
    install(project, source=source)
    capsys.readouterr()
    assert main(["-C", str(project), "uninstall", "--check", "--json"]) == 1
    payload = json.loads(capsys.readouterr().out)
    named = {REMOVAL_RENAMES.get(field.name, field.name) for field in fields(Removal)}
    assert named <= set(payload)


def test_a_declaration_this_command_cannot_parse_is_refused(project, source):
    """Somebody's configuration, on the way out as on the way in."""
    install(project, source=source)
    (project / PROJECT_MCP).write_text("[]\n", encoding="utf-8")
    with pytest.raises(Unreadable):
        uninstall(project)
    assert (project / PROJECT_SKILL).is_file(), "nothing was taken out"


def test_a_tree_carrying_no_plugin_names_what_it_lacks(project, tmp_path):
    """An installed wheel is the package alone. The answer for one is the plugin, and this
    says so rather than writing three surfaces that point at files which are not there."""
    empty = tmp_path / "wheel"
    empty.mkdir()
    with pytest.raises(NotShipped) as refused:
        install(project, source=empty)
    assert PLUGIN_SKILL in refused.value.missing
    assert not (project / PROJECT_MCP).exists()


# -- the three engines one project runs (RK415) ------------------------------


def test_every_workflow_that_calls_the_action_is_read_not_only_the_written_one(project):
    from roadkeep.installing import gated_at

    workflows = project / ".github" / "workflows"
    (workflows / "roadkeep.yml").write_text(
        "jobs:\n  lint:\n    steps:\n      - uses: actions/checkout@v4\n"
        "      - uses: alegauss/roadkeep@main\n",
        encoding="utf-8",
    )
    # An adopter is free to call the gate from a pipeline of their own, and a reader that
    # only knew `roadkeep.yml` would report *no gate* about a repository that has one.
    (workflows / "ci.yaml").write_text(
        "steps:\n  - uses: someone/roadkeep@v0.2.1  # pinned\n", encoding="utf-8"
    )
    assert gated_at(project) == (
        (".github/workflows/ci.yaml", "v0.2.1"),
        (".github/workflows/roadkeep.yml", "main"),
    )


def test_the_tree_that_is_the_action_gates_on_its_own_working_copy(project):
    from roadkeep.installing import gated_at

    (project / ".github" / "workflows" / "gate.yml").write_text(
        "steps:\n  - uses: ./\n", encoding="utf-8"
    )
    # `./` carries no ref and is said as the caller spelled it: resolving it to a revision
    # is a question this reader has no business asking git.
    assert gated_at(project) == ((".github/workflows/gate.yml", "./"),)


def test_a_repository_that_has_not_asked_for_ci_reports_no_gate(tmp_path):
    from roadkeep.installing import gated_at

    assert gated_at(tmp_path) == ()


def test_the_pen_and_the_judge_are_read_back_together(project, tmp_path, monkeypatch):
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from roadkeep.installing import engines
    from test_provenance import wired

    project.mkdir(parents=True, exist_ok=True)
    wired(tmp_path / "config", project)
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "config"))

    found = engines(project)
    # The checkout running this suite is not 0.1.285, which is the measured shape: the pen
    # and the judge are two versions and nothing before this could say so.
    assert found.plugin is not None and found.plugin.version == "0.1.285"
    assert found.running.version != "0.1.285"
    assert not found.agree


def test_a_project_with_no_plugin_registered_is_not_a_disagreement(project, tmp_path, monkeypatch):
    from roadkeep.installing import engines

    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "nowhere"))
    # Every tree served by a checkout alone. There is one engine, so there is nothing to
    # differ with — `agree` is about two versions and not about how many there are.
    found = engines(project)
    assert found.plugin is None and found.agree


def test_the_verb_prints_the_three_and_the_exit_code_is_the_verdict(project, tmp_path, monkeypatch, capsys):
    import sys

    from roadkeep.cli import EXIT_GATE, main

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from test_provenance import wired

    project.mkdir(parents=True, exist_ok=True)
    (project / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\n', encoding="utf-8"
    )
    (project / "ROADMAP.md").write_text("# Roadmap\n\n## Block A — X\n", encoding="utf-8")
    (project / ".github" / "workflows" / "roadkeep.yml").write_text(
        "steps:\n  - uses: alegauss/roadkeep@main\n", encoding="utf-8"
    )
    wired(tmp_path / "config", project)
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "config"))

    # The exit code is the answer, the way `install --check`'s is: a session that has to
    # grep a sentence to learn the pen and the judge are apart is one that will not ask.
    assert main(["-C", str(project), "engines"]) == EXIT_GATE
    printed = capsys.readouterr()
    assert "writing  " in printed.out and "plugin   0.1.285" in printed.out
    assert "gate     main" in printed.out
    assert "differ   " in printed.out
    # A read, so the verdict closes with nothing (RK271): the lines above already said it.
    assert "capture it before the session ends" not in printed.err


# -- three states, because two were not enough (RK418) ------------------------


def _pair(version="0.1.1", plugin_version="0.1.1", commit="abc1234",
          plugin_commit="abc1234", modified=False):
    from roadkeep.installing import Engines
    from roadkeep.provenance import Engine, Installed

    return Engines(
        running=Engine(
            version=version, home=Path("/tree/src/roadkeep"), commit=commit, modified=modified
        ),
        plugin=Installed(
            version=plugin_version, home=Path("/cache"), commit=plugin_commit, scope="user"
        ),
    )


def test_one_version_and_one_commit_is_agreement():
    assert _pair().verdict == AGREED
    assert _pair().agree


def test_a_different_version_is_behind():
    assert _pair(plugin_version="0.1.0").verdict == BEHIND
    assert not _pair(plugin_version="0.1.0").agree


def test_one_version_and_two_commits_is_behind():
    """The fact the release string could not carry: two `src/roadkeep/` trees fourteen files
    apart answered the same number, which is why the running engine carries its commit."""
    assert _pair(plugin_commit="def5678").verdict == BEHIND


def test_a_modified_checkout_is_unpinnable_and_never_agreement():
    """The case a machine developing this tool is in every day: a checkout at the plugin's
    own version with uncommitted work writes, the plugin judges, the numbers match — and the
    files do not. `behind` would assert a direction nothing measured."""
    found = _pair(modified=True)
    assert found.verdict == UNPINNABLE
    assert not found.agree


def test_a_missing_commit_leaves_the_version_deciding():
    # A marketplace row that recorded no sha is not evidence of a difference, so the best
    # fact available still decides rather than the answer collapsing to "cannot tell".
    assert _pair(plugin_commit=None).verdict == AGREED
    assert _pair(commit=None).verdict == AGREED
    assert _pair(commit=None, plugin_version="0.1.0").verdict == BEHIND


def test_no_plugin_is_agreement_and_not_a_defect():
    from roadkeep.installing import Engines
    from roadkeep.provenance import Engine

    alone = Engines(
        running=Engine(version="0.1.1", home=Path("/tree"), commit="abc1234")
    )
    assert alone.verdict == AGREED and alone.agree


def test_the_unpinnable_state_exits_one_and_says_which_it_is(tmp_path, capsys, monkeypatch):
    from roadkeep.cli import EXIT_GATE, main
    from roadkeep.verbs import adopting

    # Patched where the command *reads* it: the handler imports the name directly, so setting
    # it on `installing` would leave that handler holding the original — the shape of a test
    # that passes by measuring nothing.
    monkeypatch.setattr(adopting, "engines", lambda root=".": _pair(modified=True))
    (tmp_path / "roadkeep.toml").write_text('prefix = "DX"\n', encoding="utf-8")
    assert main(["-C", str(tmp_path), "engines"]) == EXIT_GATE
    out = capsys.readouterr().out
    assert "cannot be compared" in out
    assert "modified" in out


# -- the tree that ships the plugin is not asked to wire it twice (RK402) -----


def test_a_tree_that_declares_the_plugin_is_not_asked_to_wire_the_hooks(tmp_path):
    """`install --check` reported `1 surface(s) differ` here permanently, because the guard's
    hooks are not in `.claude/settings.json` — and they are not in it because this tree ships
    them as a plugin. A check that can never report clean is one nobody reads."""
    root = _plugin_tree(tmp_path)
    made = plan(root, source=root)
    written = {surface.path.name for surface in made.surfaces}
    assert "settings.json" not in written
    reason = next(text for name, text in made.skipped if name == PROJECT_SETTINGS)
    assert "run it twice" in reason
    assert PLUGIN_MANIFEST in reason and PLUGIN_HOOKS in reason


def test_the_mcp_declaration_is_still_written(tmp_path):
    # Only the hooks would fire twice: a plugin's server and a project's are two entries the
    # harness reads separately, so the narrowing is to one surface and not to the pair.
    root = _plugin_tree(tmp_path)
    made = plan(root, source=root)
    assert any(surface.path.name == ".mcp.json" for surface in made.surfaces)


def test_half_a_declaration_is_not_one(tmp_path):
    """Either file alone is a different state: a manifest with no hooks file declares nothing
    that runs, and a hooks file no manifest names is one the harness never loads — and in
    both, `.claude/settings.json` is still the only place the guard could live.

    Asked of the predicate rather than through `plan`, and that is the honest level: both
    files are in `CARRIED`, so a *source* tree missing either is refused as not carrying the
    plugin at all — a different answer, and the right one. What this pins is the question the
    skip asks of the tree being **wired**.
    """
    from roadkeep.installing import _provides_plugin

    whole = _plugin_tree(tmp_path / "whole")
    assert _provides_plugin(whole)
    for missing in (PLUGIN_MANIFEST, PLUGIN_HOOKS):
        half = _plugin_tree(tmp_path / missing.replace("/", "_"))
        (half / missing).unlink()
        assert not _provides_plugin(half), missing
    assert not _provides_plugin(tmp_path / "nothing-here")


def test_an_adopting_project_is_unaffected(tmp_path):
    # The narrowing is about a tree that provides the plugin, and an adopter provides none —
    # so the surface it has always been offered is the surface it is still offered.
    root = tmp_path / "adopter"
    root.mkdir(parents=True)
    (root / "roadkeep.toml").write_text('prefix = "DX"\n', encoding="utf-8")
    made = plan(root, source=_plugin_tree(tmp_path / "origin"))
    assert any(s.path.name == "settings.json" for s in made.surfaces)


def _plugin_tree(root: Path) -> Path:
    """A checkout that declares the guard as a plugin, which is what the skip is asked of.

    Everything `install` requires of a source tree, plus the two files that make the claim:
    the manifest and the hooks it names.
    """
    for part in COPIED:
        target = root / part
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(HERE / part, target)
    (root / "roadkeep.toml").write_text('prefix = "DX"\n', encoding="utf-8")
    for name in (PLUGIN_MANIFEST, PLUGIN_HOOKS):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.is_file():
            path.write_text("{}\n", encoding="utf-8")
    return root


# -- vendoring an engine into the project (RK1193) ----------------------------


def engine_tree(root: Path, version: str, *, working: bool = False) -> Path:
    """A tree that answers `--version` and nothing else — the one question `candidates` asks."""
    (root / "scripts").mkdir(parents=True, exist_ok=True)
    (root / "scripts" / "roadkeep.py").write_text(
        f"import sys\nprint('roadkeep {version}')\n", encoding="utf-8"
    )
    (root / "src").mkdir(exist_ok=True)
    (root / "src" / "marker.txt").write_text(version, encoding="utf-8")
    if working:
        (root / ".git").mkdir(exist_ok=True)
        (root / ".git" / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
    return root


def only_here(monkeypatch, tmp_path):
    """Point every discovery at this tmp tree, so the developer's own machine is not read."""
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.delenv("ROADKEEP_SRC", raising=False)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path / "home"))


def test_the_highest_version_wins_and_never_the_first_one_found(tmp_path, monkeypatch):
    """The defect two adopters each wrote 147 lines to solve. Six engines were resolvable on
    the machine this was measured on, and a search order answers differently per machine —
    which is the one thing a pin exists to stop."""
    from roadkeep.installing import candidates, vendor

    only_here(monkeypatch, tmp_path)
    plugins = tmp_path / "config" / "plugins"
    engine_tree(plugins / "a" / "roadkeep", "0.1.9")
    engine_tree(plugins / "b" / "roadkeep", "0.1.10")
    project = tmp_path / "adopter"
    project.mkdir()

    found = candidates(project)
    # Compared as integers: `0.1.9` sorts above `0.1.10` as text, which both vendored copies
    # got right only by never having had a two-digit patch.
    assert [one.version for one in found] == ["0.1.10", "0.1.9"]
    assert vendor(project).chosen.version == "0.1.10"


def test_a_working_checkout_is_skipped_unless_it_is_named(tmp_path, monkeypatch):
    """The rule an hour paid for: a tree mid-refactor answers a version and then raises out of
    a half-edited module. Naming it is a caller saying which tree they mean."""
    from roadkeep.installing import vendor

    only_here(monkeypatch, tmp_path)
    project = tmp_path / "adopter"
    project.mkdir()
    engine_tree(tmp_path / "roadkeep", "9.9.9", working=True)
    engine_tree(tmp_path / "config" / "plugins" / "a" / "roadkeep", "0.1.1")

    # The sibling is the higher version and loses anyway.
    assert vendor(project).chosen.version == "0.1.1"
    monkeypatch.setenv("ROADKEEP_SRC", str(tmp_path / "roadkeep"))
    assert vendor(project).chosen.version == "9.9.9"


def test_the_copy_is_an_artefact_and_not_a_second_repository(tmp_path, monkeypatch):
    """`.git` above all: with it, `git status` walks the copy and the project has two roots."""
    from roadkeep.installing import PROJECT_ENGINE, vendor

    only_here(monkeypatch, tmp_path)
    monkeypatch.setenv("ROADKEEP_SRC", str(engine_tree(tmp_path / "src-tree", "1.0.0", working=True)))
    project = tmp_path / "adopter"
    project.mkdir()

    written = vendor(project)
    assert written.into == project / PROJECT_ENGINE
    assert not (written.into / ".git").exists()
    assert (written.into / "src" / "marker.txt").read_text(encoding="utf-8") == "1.0.0"


def test_what_landed_is_asked_what_it_is(tmp_path, monkeypatch):
    """The fourth rule, and the one that makes the other three mean anything: picking by
    version proves nothing about a tree that arrived different."""
    from roadkeep.installing import NotVerified, vendor

    only_here(monkeypatch, tmp_path)
    source = engine_tree(tmp_path / "src-tree", "1.0.0")
    monkeypatch.setenv("ROADKEEP_SRC", str(source))
    project = tmp_path / "adopter"
    project.mkdir()
    assert vendor(project).verified == "1.0.0"

    # A tree that says one thing when asked and another after it lands.
    (source / "scripts" / "roadkeep.py").write_text(
        "import sys, pathlib\n"
        "print('roadkeep 1.0.0' if 'src-tree' in str(pathlib.Path(__file__)) else 'roadkeep 0.0.1')\n",
        encoding="utf-8",
    )
    with pytest.raises(NotVerified) as refused:
        vendor(project)
    assert "0.0.1" in str(refused.value)
    # Left on disk: what is wrong with it is what it just said.
    assert (project / ".roadkeep").is_dir()


def test_a_machine_with_no_engine_refuses_rather_than_reporting_success(tmp_path, monkeypatch):
    """`--vendor` is asked for, so a run that copied nothing and exited 0 would leave a
    project believing it is pinned."""
    from roadkeep.installing import ENGINE_SOURCE, NoEngine, vendor

    only_here(monkeypatch, tmp_path)
    project = tmp_path / "adopter"
    project.mkdir()
    with pytest.raises(NoEngine) as refused:
        vendor(project)
    assert ENGINE_SOURCE in str(refused.value)


def test_the_check_reports_the_choice_and_copies_nothing(tmp_path, monkeypatch):
    from roadkeep.installing import vendor

    only_here(monkeypatch, tmp_path)
    monkeypatch.setenv("ROADKEEP_SRC", str(engine_tree(tmp_path / "src-tree", "1.0.0")))
    project = tmp_path / "adopter"
    project.mkdir()
    written = vendor(project, checked=True)
    assert written.chosen.version == "1.0.0"
    assert not (project / ".roadkeep").exists()


def test_a_rerun_replaces_the_tree_rather_than_merging_into_it(tmp_path, monkeypatch):
    """A half-old tree is the state every rule here is about, and `copytree` onto a populated
    directory is how one is made."""
    from roadkeep.installing import vendor

    only_here(monkeypatch, tmp_path)
    monkeypatch.setenv("ROADKEEP_SRC", str(engine_tree(tmp_path / "src-tree", "1.0.0")))
    project = tmp_path / "adopter"
    project.mkdir()
    vendor(project)
    (project / ".roadkeep" / "src" / "left-behind.txt").write_text("x", encoding="utf-8")
    vendor(project)
    assert not (project / ".roadkeep" / "src" / "left-behind.txt").exists()


def test_the_ignore_line_is_printed_and_never_written(tmp_path, monkeypatch):
    """`.gitignore` is the project's file, so this is `merge --register`'s rule about the `git
    config` half: the line is stated and running it is the author's. Said only where nothing
    covers it already, so a project that did this once is not advised about it every run."""
    from roadkeep.installing import vendor

    only_here(monkeypatch, tmp_path)
    monkeypatch.setenv("ROADKEEP_SRC", str(engine_tree(tmp_path / "src-tree", "1.0.0")))
    project = tmp_path / "adopter"
    project.mkdir()

    written = vendor(project)
    assert written.ignore and ".gitignore" in written.stated(checked=False)
    assert not (project / ".gitignore").exists(), "advice, not an edit"

    (project / ".gitignore").write_text(".roadkeep/\n", encoding="utf-8")
    assert not vendor(project).ignore


def test_the_version_is_read_out_of_the_line_and_not_off_its_end():
    """Measured end to end, and it is why this function exists: `--version` prints the number
    followed by the provenance RK79 added — the commit, whether the tree is modified, and where
    the package is. Taking the last token reads the *path* as the version, every candidate ties
    at nothing, and the verification after the copy then compares two paths and refuses."""
    from roadkeep.installing import _version_in

    said = r"roadkeep 0.1.963 (479d7266 modified, D:\Git\alegauss\roadkeep\src\roadkeep)"
    assert _version_in(said) == "0.1.963"
    assert _version_in("roadkeep 1.2\n") == "1.2"
    assert _version_in("no numbers here") == ""
