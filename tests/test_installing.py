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
from pathlib import Path

import pytest

from roadkeep.cli import build_parser, main
from roadkeep.installing import (
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
    NotShipped,
    Unanchored,
    Unreadable,
    _ENTRY_RE,
    _entry,
    install,
    plan,
)

HERE = Path(__file__).resolve().parents[1]

#: Everything the command reads out of the tree it is wiring in. Copied into a fixture rather
#: than pointed at, so the two directories are siblings on one filesystem and the launcher
#: comes out relative — which is the case every adopting project is in.
CARRIED = (LAUNCHER, PLUGIN_HOOKS, PLUGIN_MCP, PLUGIN_SKILL, PLUGIN_MANIFEST)


@pytest.fixture
def source(tmp_path: Path) -> Path:
    """A checkout of this tool, beside the project that will adopt it."""
    root = tmp_path / "roadkeep"
    for part in CARRIED:
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


def test_check_is_the_gate_and_the_exit_code_is_the_contract(project, source, capsys):
    argv = ["-C", str(project), "install", "--source", str(source)]
    assert main(argv) == 0
    assert main([*argv, "--check"]) == 0
    (project / PROJECT_SKILL).write_text("stale\n", encoding="utf-8")
    assert main([*argv, "--check"]) == 1
    assert "would update" in capsys.readouterr().out


def test_a_tree_carrying_no_plugin_names_what_it_lacks(project, tmp_path):
    """An installed wheel is the package alone. The answer for one is the plugin, and this
    says so rather than writing three surfaces that point at files which are not there."""
    empty = tmp_path / "wheel"
    empty.mkdir()
    with pytest.raises(NotShipped) as refused:
        install(project, source=empty)
    assert PLUGIN_SKILL in refused.value.missing
    assert not (project / PROJECT_MCP).exists()
