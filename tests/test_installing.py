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
    PLUGIN_PAGES,
    PLUGIN_ROOT,
    PLUGIN_SKILL,
    PROJECT_BRIDGE,
    PROJECT_ENGINE,
    PROJECT_MCP,
    PROJECT_PAGES,
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
        # The skill is three files since RK1437 — an orientation and the two pages it points
        # at — and they land together because a page the orientation names and the adopter has
        # not got fails by returning nothing, which is quieter than any drift.
        *(project / page for page in PROJECT_PAGES),
        project / PROJECT_WORKFLOW,
    }
    for path in written:
        assert path.is_file()


def test_the_pages_the_orientation_points_at_are_copied_verbatim(project, source):
    """RK1437, and the half `--check` is about: the entry point is the one substituted fact
    and it lives in `SKILL.md`, so a page is bytes and any difference is drift."""
    install(project, source=source)
    for page, landed in zip(PLUGIN_PAGES, PROJECT_PAGES, strict=True):
        assert read(project / landed) == read(HERE / page), landed


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
    # A **note** since RK1308, so the exit code does not move: what this gate is for is whether
    # the governed lines drifted, and whether the wired surface matches the engine is
    # maintenance — true of the machine rather than of the branch.
    (found,) = [one for one in report.notes if one.code == "install.stale"]
    assert not [one for one in report.findings if one.code == "install.stale"]
    # Filed at the surface, unlike `budget.tool`: there is a path a reader can open, and it is
    # the file that drifted.
    assert found.file == PROJECT_SKILL
    assert "install" in found.message


def test_a_stale_surface_does_not_turn_the_ci_gate_red(project, capsys):
    """RK1308, observed in pportal 2026-08-22 mid-task: `lint` exited 1 on a backlog `ship` had
    just written and that had drifted in no way at all, reporting `311 line(s), 32 section(s) …
    clean` in the same breath as returning 1.

    That exit code is the whole contract of the CI job this project publishes, so a repository
    whose only gate is `roadkeep lint` went red on every push, for every contributor, until
    somebody ran `install` — which is a write into `.claude/` and not a backlog edit, and in a
    project holding one task to one commit has to become a commit of its own.
    """
    from roadkeep.cli import EXIT_OK, main
    from roadkeep.config import Config
    from roadkeep.linting import lint

    install(wired(project), source=HERE)
    (project / PROJECT_SKILL).write_text("stale\n", encoding="utf-8")

    # Reported, and reported clean: the drift is said out loud and the verdict is about the
    # files, which is the split `engine.disagreement` has had since RK415.
    report = lint(Config.discover(project))
    assert report.clean and report.problems == 0
    # By code and not the whole list: this project is now wired, so a checkout running the
    # suite with uncommitted work carries `engine.disagreement` beside it (RK1440) — which is
    # the same split said about a different pair, and neither moves the verdict.
    assert "install.stale" in [one.code for one in report.notes]
    assert main(["-C", str(project), "lint"]) == EXIT_OK
    assert "install.stale" in capsys.readouterr().out


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


# -- which side is newer, which nothing asked (RK1462) -------------------------


def _ahead(project: Path, version: str = "9.9.9") -> None:
    """A project whose surfaces were written by an engine this one is behind.

    Through the writer itself, which is the whole reason it is a function: a test appending
    its own `[install]` would declare the table twice on a project `install` had already
    recorded into, and be measuring its own TOML rather than this one's.
    """
    from roadkeep.installing import record_wired

    record_wired(project / "roadkeep.toml", version)


def test_the_write_refuses_to_put_an_older_copy_over_a_newer_one(project):
    """RK1462. `lint` reported `install.stale` on both of a project's surfaces every run and
    the finding names its remedy — running it removed RK1446's Windows branch from the
    committed launcher and wrote back the version whose `mcp` mode exits 0 and serves nothing.
    Nothing misbehaved by its own account: the engine answering was a vendored 0.2.4 and the
    surfaces came from a far later one, so `behind` was true in the sense of *different*,
    which on that file meant ahead."""
    from roadkeep.installing import SurfacesAhead

    install(wired(project), source=HERE)
    (project / PROJECT_SKILL).write_text("newer\n", encoding="utf-8")
    _ahead(project)

    before = (project / PROJECT_SKILL).read_text(encoding="utf-8")
    with pytest.raises(SurfacesAhead) as caught:
        install(project, source=HERE)

    said = str(caught.value)
    assert "install --vendor" in said, "the direction that moves the engine"
    assert "uninstall" in said, "and the downgrade said out loud"
    assert (project / PROJECT_SKILL).read_text(encoding="utf-8") == before


def test_the_gate_says_nothing_where_its_only_word_would_be_wrong(project):
    """`install.stale`'s whole vocabulary is *behind*, *stale*, *refresh*, and the remedy it
    names is the write that deletes the newer copy. So where the surfaces are ahead there is
    nothing for it to say, and `install --check` is where the state is reported in words that
    fit it."""
    from roadkeep.config import Config
    from roadkeep.linting import lint

    install(wired(project), source=HERE)
    (project / PROJECT_SKILL).write_text("newer\n", encoding="utf-8")
    assert "install.stale" in [one.code for one in lint(Config.discover(project)).notes]

    _ahead(project)
    assert "install.stale" not in [
        one.code for one in lint(Config.discover(project)).notes
    ]


def test_the_check_names_the_direction_before_it_lists_the_files(project, capsys):
    from roadkeep.cli import EXIT_GATE

    install(wired(project), source=HERE)
    (project / PROJECT_SKILL).write_text("newer\n", encoding="utf-8")
    _ahead(project)

    assert main(["-C", str(project), "install", "--source", str(HERE), "--check"]) == EXIT_GATE
    printed = capsys.readouterr()
    assert "ahead          written by 9.9.9" in printed.out
    # And the sentence that offered the write, which is the one a caller acts on.
    assert "install --vendor" in printed.err
    assert "refuses" in printed.err


def test_the_write_records_the_version_that_made_it(project, capsys):
    """The record that makes the comparison possible at all, written where a project's own
    decisions are and not stamped into the surfaces — those are byte-compared against the
    plugin's copies, so a version inside one is a difference every check has to ignore."""
    from roadkeep.config import Config
    from roadkeep.provenance import engine

    intent = install(wired(project), source=HERE)
    assert intent.recorded
    assert Config.discover(project).install_wired == engine().version
    # And said out loud, because it is a fifth file this command touched (RK298) — on the run
    # that wrote it, and never on one that found the same version already there.
    capsys.readouterr()
    assert main(["-C", str(project), "install", "--source", str(HERE)]) == 0
    assert "[install] wired" not in capsys.readouterr().out, "unchanged is not a write"

    (project / "roadkeep.toml").write_text(CLEAN[0], encoding="utf-8", newline="")
    assert main(["-C", str(project), "install", "--source", str(HERE)]) == 0
    assert "[install] wired" in capsys.readouterr().out


def test_a_project_wired_before_the_record_behaves_exactly_as_it_did(project):
    # `""` reads as *unknown* and never as *zero*: an absent record cannot order two copies,
    # so the check is what it was and the next `install` writes the version down.
    from roadkeep.config import Config
    from roadkeep.installing import ahead_of
    from roadkeep.linting import lint

    install(wired(project), source=HERE)
    (project / "roadkeep.toml").write_text(CLEAN[0], encoding="utf-8", newline="")
    (project / PROJECT_SKILL).write_text("stale\n", encoding="utf-8")

    assert Config.discover(project).install_wired == ""
    assert ahead_of(project) == ""
    assert "install.stale" in [one.code for one in lint(Config.discover(project)).notes]


def test_the_versions_are_ordered_as_numbers_and_not_as_text(project):
    # `install --vendor`'s own comparison and for its reason (RK1193): `0.1.10` sorts under
    # `0.1.9` as text, and two adopting projects got that right by never having two digits.
    from roadkeep.installing import ahead_of
    from roadkeep.provenance import engine

    install(wired(project), source=HERE)
    major, minor, patch = (int(one) for one in engine().version.split(".")[:3])
    (project / "roadkeep.toml").write_text(CLEAN[0], encoding="utf-8", newline="")
    _ahead(project, f"{major}.{minor}.{patch - 1}")
    assert ahead_of(project) == "", "an older record is not ahead"

    (project / "roadkeep.toml").write_text(CLEAN[0], encoding="utf-8", newline="")
    _ahead(project, f"{major}.{minor}.{patch + 1}")
    assert ahead_of(project) == f"{major}.{minor}.{patch + 1}"


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


def test_the_check_closes_on_its_own_answer_and_never_on_a_doubt(project, source, capsys):
    """RK1420, and RK1419's rule reaching the third verb. This 1 says the surfaces differ and
    already carries `roadkeep install` as the write that closes it, so RK86's offer would end
    a complete report with two lines about the tool possibly being wrong — on the verb an
    adopter runs while wiring, which is the moment they can least tell.

    Stated by the run rather than by the parser: `install` returns this code from nowhere
    else, so a declaration standing over the whole verb would be about a branch that does not
    exist.
    """
    argv = ["-C", str(project), "install", "--source", str(source), "--check"]
    assert main(argv) == 1
    printed = capsys.readouterr()
    assert "surface(s) differ" in printed.err, "the check said nothing at all"
    assert "capture it before the session ends" not in printed.err


def test_a_real_install_that_refuses_still_offers(project, capsys):
    """The other side of the same run. What `install` returns when the input is wrong is 2,
    and that is RK86's measured case — a caller who thinks the refusal is wrong. Only the
    check's own 1 is the verdict."""
    code = main(["-C", str(project), "install", "--source", str(project / "nowhere")])
    assert code == 2
    assert "capture it before the session ends" in capsys.readouterr().err


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


def test_a_driver_already_routed_stops_the_row_advertising_the_flag(project, source, capsys):
    """RK1387, by RK394's argument one step further: an opt-in already taken is a different
    entry from one nobody has chosen yet. The row stated what `install` does not write and
    never asked whether anything else had — so `merge --check` answered *4 of 4 governed files
    routed* while this one offered to wire them, two reads of one tree.

    The attribute half only: whether this clone can run what the files route to is per
    checkout, and quoting it here would be the second answer this closes."""
    declaring(project, CLEAN)
    assert main(["-C", str(project), "merge", "--register"]) == EXIT_OK
    capsys.readouterr()

    assert main(["-C", str(project), "install", "--source", str(source), "--check"]) in (
        EXIT_OK,
        EXIT_GATE,
    )
    said = capsys.readouterr().out
    assert "route to the merge driver" in said
    assert "`install --register-merge` runs it here" not in said
    # And the read that does answer the other half is named rather than quoted.
    assert "merge --check" in said


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
        # A reference page left behind is a copy of this tool's rules that nothing refreshes,
        # which is the drift `install` exists to remove, one file over (RK1437).
        *(project / page for page in PROJECT_PAGES),
    }
    for path in (PROJECT_MCP, PROJECT_SETTINGS, PROJECT_SKILL, *PROJECT_PAGES):
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
    # wired this project. Absent is absent either way — and six since RK1437 split the skill,
    # counted off `PROJECT_PAGES` so a third page is not a number to remember here.
    assert [w.state for w in taken.withdrawals] == ["absent"] * (4 + len(PROJECT_PAGES))


def test_uninstall_check_is_the_same_answer_and_writes_nothing(project, source, capsys):
    install(project, source=source)
    argv = ["-C", str(project), "uninstall"]
    assert main([*argv, "--check"]) == 1
    printed = capsys.readouterr()
    assert "would delete" in printed.out
    # The same verdict one verb over (RK1420), and the state RK1420's own reading left open:
    # this check was measured only where it exits 0, so what it says when it has something to
    # report was a read nobody had taken.
    assert "capture it before the session ends" not in printed.err
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


# -- vendor, then generate, and never the other way (RK1464) -------------------


def _engine_copy(into: Path, version: str, mark: str) -> Path:
    """A whole engine this command can wire from: everything `CARRIED` names, marked."""
    import shutil

    for part in ("hooks", "skills", "scripts", ".claude-plugin", "src"):
        source, target = HERE / part, into / part
        if source.is_dir():
            shutil.copytree(source, target, dirs_exist_ok=True)
    init = into / "src" / "roadkeep" / "__init__.py"
    held = init.read_text(encoding="utf-8")
    stated = next(one for one in held.splitlines() if one.startswith("__version__"))
    init.write_text(
        held.replace(stated, f'__version__ = "{version}"'), encoding="utf-8", newline=""
    )
    skill = into / PLUGIN_SKILL
    skill.write_text(
        skill.read_text(encoding="utf-8") + f"\n{mark}\n", encoding="utf-8", newline=""
    )
    return into


def test_the_surfaces_come_from_the_engine_being_vendored(tmp_path, monkeypatch, capsys):
    """RK1464. `install --vendor` writes the surfaces and replaces the engine those surfaces
    are generated from, and it did them in that order — so the files it wrote were the
    outgoing engine's. Measured vendoring 0.2.60 over 0.2.4: the run reported `updated`, then
    `vendored 0.2.60`, and the launcher on disk was 0.2.4's, without RK1446's Windows branch.
    Its own `--check` refused the tree immediately after, and a second `install` fixed it.

    Nobody reading that output would know: `vendored` and `answers` are the last two lines and
    `updated` is above them, which reads as the new engine's work."""
    only_here(monkeypatch, tmp_path)
    old = _engine_copy(tmp_path / "old", "0.0.1", "THE OUTGOING ENGINE WROTE THIS.")
    new = _engine_copy(tmp_path / "new", "9.9.9", "THE VENDORED ENGINE WROTE THIS.")
    project = tmp_path / "adopter"
    project.mkdir()
    install(project, source=old)
    assert "OUTGOING" in (project / PROJECT_SKILL).read_text(encoding="utf-8")

    monkeypatch.setenv("ROADKEEP_SRC", str(new))
    capsys.readouterr()
    assert main(["-C", str(project), "install", "--vendor"]) == EXIT_OK

    landed = (project / PROJECT_SKILL).read_text(encoding="utf-8")
    assert "THE VENDORED ENGINE WROTE THIS." in landed
    assert "OUTGOING" not in landed, "one run, and the outgoing engine's copy is gone"


def test_the_run_leaves_a_tree_its_own_check_passes(tmp_path, monkeypatch, capsys):
    # The state the defect ended in: `install --check` exited non-zero on both surfaces
    # immediately after the run called to clear them, and `lint` reported the same
    # `install.stale`. One run has to be enough, which is the whole claim.
    from roadkeep.config import Config
    from roadkeep.linting import lint

    only_here(monkeypatch, tmp_path)
    old = _engine_copy(tmp_path / "old", "0.0.1", "THE OUTGOING ENGINE WROTE THIS.")
    _engine_copy(tmp_path / "new", "9.9.9", "THE VENDORED ENGINE WROTE THIS.")
    project = declaring(tmp_path / "adopter", CLEAN)
    install(project, source=old)

    monkeypatch.setenv("ROADKEEP_SRC", str(tmp_path / "new"))
    capsys.readouterr()
    assert main(["-C", str(project), "install", "--vendor"]) == EXIT_OK
    capsys.readouterr()

    assert main(["-C", str(project), "install", "--check"]) == EXIT_OK
    assert "install.stale" not in [
        one.code for one in lint(Config.discover(project)).notes
    ]


def test_the_record_names_the_engine_that_wrote_them_and_not_this_process(
    tmp_path, monkeypatch, capsys
):
    """RK1462's record, one door over: under `--vendor` the copy that writes the bytes is the
    tree copied in, so a record naming this process would make the next check refuse the
    surfaces the run just installed correctly."""
    from roadkeep.config import Config

    only_here(monkeypatch, tmp_path)
    _engine_copy(tmp_path / "new", "9.9.9", "THE VENDORED ENGINE WROTE THIS.")
    project = declaring(tmp_path / "adopter", CLEAN)

    monkeypatch.setenv("ROADKEEP_SRC", str(tmp_path / "new"))
    capsys.readouterr()
    assert main(["-C", str(project), "install", "--vendor"]) == EXIT_OK
    assert Config.discover(project).install_wired == "9.9.9"


def test_a_plan_keeps_the_engine_the_project_pinned(tmp_path, monkeypatch):
    """`_carrying`'s rule one variant over (RK1113, RK1464): which engine a project runs is a
    fact on its disk, and a plan reading the running checkout instead would offer to re-point
    every declaration at it — undoing the pin, in the vocabulary of a refresh."""
    from roadkeep.installing import _pinned_engine

    only_here(monkeypatch, tmp_path)
    project = tmp_path / "adopter"
    project.mkdir()
    assert _pinned_engine(project) is None, "no pin is no pin"

    _engine_copy(project / ".roadkeep", "9.9.9", "THE VENDORED ENGINE WROTE THIS.")
    assert _pinned_engine(project) == project / ".roadkeep"
    assert plan(project).source == project / ".roadkeep"
    # And a caller who named a tree still wins: that is an answer they gave.
    assert plan(project, source=HERE).source == HERE


def test_a_half_copied_pin_is_not_a_source(tmp_path, monkeypatch):
    # Asked as *does it carry what this command translates* and never as *is it there*: a
    # `.roadkeep/` mid-copy is not an engine, and falling through is what a project with no
    # pin already gets.
    from roadkeep.installing import _pinned_engine

    only_here(monkeypatch, tmp_path)
    project = tmp_path / "adopter"
    (project / ".roadkeep" / "scripts").mkdir(parents=True)
    assert _pinned_engine(project) is None


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


def _registry(tmp_path: Path, monkeypatch, project: Path, home: Path, version: str) -> None:
    """The harness's own file, naming one install for this project — its format, not ours."""
    config = tmp_path / "config"
    (config / "plugins").mkdir(parents=True, exist_ok=True)
    (config / "plugins" / "installed_plugins.json").write_text(
        json.dumps(
            {
                "version": 2,
                "plugins": {
                    "roadkeep@alegauss": [
                        {
                            "scope": "project",
                            "projectPath": str(project),
                            "installPath": str(home),
                            "version": version,
                            "lastUpdated": "2026-08-17T00:00:00Z",
                        }
                    ]
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(config))



# -- the copy a shell command should invoke (RK1230) ---------------------------


def test_the_wired_copy_is_named_in_one_line(tmp_path, capsys, monkeypatch):
    """The MCP tools always reach the right copy; the shell does not, and a session that needs
    the shell has to know which one — `lint --fix` is withheld from the tool surface, so any
    repair goes there. Nothing said which.

    Observed across one long session: commands were run against a copy found by *listing* a
    plugins cache directory, while the engine the project writes with lived under a different
    plugins root entirely. The stale copy did not fail; it agreed with a rule that had moved.
    """
    root = tmp_path / "project"
    root.mkdir()
    wired = tmp_path / "plugins" / "roadkeep" / "0.1.999"
    (wired / "scripts").mkdir(parents=True)
    _registry(tmp_path, monkeypatch, root, wired, version="0.1.999")

    assert main(["-C", str(root), "engines", "--invoke"]) == EXIT_OK
    said = capsys.readouterr().out
    # One line and nothing else, so a shell can read it into a variable rather than
    # recognise it inside a table — which is what a caller was reduced to grepping.
    assert said.splitlines() == [f"python {(wired / LAUNCHER).as_posix()}"]


def test_it_answers_the_running_copy_where_nothing_is_wired(tmp_path, capsys, monkeypatch):
    """With no plugin registered, the copy the caller reaches *is* the one that answers, and
    naming a second would be inventing a disagreement."""
    from roadkeep.provenance import invocation

    root = tmp_path / "project"
    root.mkdir()
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "empty"))
    assert main(["-C", str(root), "engines", "--invoke"]) == EXIT_OK
    assert capsys.readouterr().out.strip() == invocation()


def test_the_line_carries_no_verdict(tmp_path, capsys, monkeypatch):
    """This answers *which copy to call*, which a caller has to know before they know whether
    the copies agree — so an exit code about agreement would make a shell substitution fail on
    a project that is merely behind. `engines` bare is where the disagreement is read."""
    root = tmp_path / "project"
    root.mkdir()
    wired = tmp_path / "plugins" / "roadkeep" / "0.0.1"
    (wired / "scripts").mkdir(parents=True)
    _registry(tmp_path, monkeypatch, root, wired, version="0.0.1")

    # The copies plainly disagree, which `engines` reports and exits 1 on.
    assert main(["-C", str(root), "engines"]) == EXIT_GATE
    capsys.readouterr()
    # And the one line still answers, at exit 0.
    assert main(["-C", str(root), "engines", "--invoke"]) == EXIT_OK
    assert capsys.readouterr().out.strip().endswith(LAUNCHER)


def test_the_payload_carries_it_without_the_flag(tmp_path, capsys, monkeypatch):
    """A consumer already reading this answer should not make a second call for the one field
    it acts on — and the served surface appends `--json` to every call, so the flag has to
    work with it rather than be refused beside it."""
    root = tmp_path / "project"
    root.mkdir()
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "empty"))

    assert main(["-C", str(root), "engines", "--json"]) == EXIT_OK
    assert "invoke" in json.loads(capsys.readouterr().out)

    assert main(["-C", str(root), "engines", "--invoke", "--json"]) == EXIT_OK
    assert set(json.loads(capsys.readouterr().out)) == {"invoke"}


# -- the write a stale copy should not make (RK1235) --------------------------


#: A project that declared the registered plugin is the copy that should write here — the
#: standing RK1235's refusal and RK1238's note both need, and its own key since RK1240:
#: `pinned` is a decision about a different pair of copies entirely.
ENFORCED = 'prefix = "DX"\n[files]\nroadmap = "ROADMAP.md"\n[install]\nenforced = true\n'
BACKLOG = "# Roadmap\n\n## Block A\n\n"


def _enforcing(tmp_path: Path, config: str = ENFORCED) -> Path:
    (tmp_path / "roadkeep.toml").write_text(config, encoding="utf-8")
    (tmp_path / "ROADMAP.md").write_text(BACKLOG, encoding="utf-8")
    return tmp_path


def _reading(monkeypatch, found):
    """Patched on `installing`, which is where the guard imports both from.

    Both readings and not one (RK1237): the guard asks `behind` on every write and reaches
    `engines` only to compose the refusal, so a fake standing in for one of them would leave
    the other answering about this developer's own checkout.
    """
    from roadkeep import installing

    monkeypatch.setattr(installing, "engines", lambda root=".": found)
    monkeypatch.setattr(installing, "behind", lambda root=".": found.verdict == BEHIND)


def _added(root: Path) -> list[str]:
    return ["-C", str(root), "add", "--block", "A", "--symptom",
            "A symptom plainly long enough", "--why", "Because."]


def test_a_write_from_a_copy_behind_the_pinned_one_is_refused(tmp_path, capsys, monkeypatch):
    """RK1230 named the copy to call and left the write unguarded, which its design said out
    loud. The failure is quiet: a copy behind the wired one does not fail, it agrees with a
    rule that has moved and writes a line its own version thinks legal — reported by the
    project's gate afterwards, as the file's problem rather than as the pen's."""
    root = _enforcing(tmp_path)
    _reading(monkeypatch, _pair(plugin_version="0.1.0"))
    assert main(_added(root)) == EXIT_GATE
    # Nothing written, which is the only thing a guard before the lock is for.
    assert (root / "ROADMAP.md").read_text(encoding="utf-8") == BACKLOG
    assert "refused, nothing written" in capsys.readouterr().err


def test_the_refusal_names_the_copy_to_run_it_through(tmp_path, capsys, monkeypatch):
    """"Either way it names `engines --invoke`, or it is a wall with no door." The caller
    re-runs the same command through the copy that is right, rather than learning a copy
    exists and going to find it."""
    from composing import runs

    root = _enforcing(tmp_path)
    _reading(monkeypatch, _pair(plugin_version="0.1.0"))
    main(_added(root))
    said = capsys.readouterr().err
    assert "engines --invoke" in said
    # Executed as printed, which is the whole difference between a door and a sentence
    # (RK1209): the read it names is accepted here and its answer is the copy to use.
    assert runs(root, said) == (["engines", "--invoke"],)


def test_a_project_that_declared_no_pin_is_not_guarded(tmp_path, monkeypatch):
    """The standing this refusal has, and its whole extent. `[install] pinned` is the project
    saying which copy is right (L6); without it, refusing would be this tool guessing at a
    setup it cannot see — a developer's checkout, a CI ref, a vendored version, all three
    legitimate and all three `behind`."""
    root = _enforcing(tmp_path, config='prefix = "DX"\n[files]\nroadmap = "ROADMAP.md"\n')
    _reading(monkeypatch, _pair(plugin_version="0.1.0"))
    assert main(_added(root)) == EXIT_OK


def test_a_modified_checkout_is_not_behind_and_still_writes(tmp_path, monkeypatch):
    """The other condition, and the reason RK418's third state had to exist first. A checkout
    with uncommitted work is at no commit the plugin could match, so `behind` asserts a
    direction nothing measured — and it is where a developer lives every day."""
    root = _enforcing(tmp_path)
    _reading(monkeypatch, _pair(modified=True))
    assert main(_added(root)) == EXIT_OK


def test_the_wiring_writes_are_how_the_pin_gets_satisfied(tmp_path, monkeypatch):
    """A door and not a wall, in the direction that matters most: `install` is how a project
    takes the version it pinned, so refusing it would leave the pin with no way to be met."""
    from roadkeep.cli import _behind
    from roadkeep.config import Config

    _reading(monkeypatch, _pair(plugin_version="0.1.0"))
    parser = build_parser()
    config = Config.discover(_enforcing(tmp_path))
    for argv in (["install"], ["init"], ["uninstall"], ["capture", "filed", "one.json", "--as", "RK1"]):
        assert _behind(config, parser.parse_args(argv)) is None, argv


def test_every_write_this_surface_has_is_guarded_or_says_why_not():
    """The census, because the exemption is a hand list and a verb added beside them would
    otherwise join it by accident: a write is governed unless its parser declares `wiring`,
    and these four are the ones that change which copies exist or record what this tool did
    wrong."""
    parser = build_parser()
    (actions,) = [one for one in parser._actions if getattr(one, "choices", None)]
    exempt = {
        name
        for name, one in actions.choices.items()
        if not one.get_default("reads_only") and one.get_default("wiring")
    }
    assert exempt == {"init", "install", "uninstall"}
    # `capture` declares it one level down, on the action that writes.
    filed = actions.choices["capture"]
    (nested,) = [one for one in filed._actions if getattr(one, "choices", None)]
    assert nested.choices["filed"].get_default("wiring")


def test_a_read_is_never_asked_which_copy_it_came_from(tmp_path, monkeypatch):
    """Reads answer from whatever copy the caller reached, which is `provenance`'s rule and
    not this one's: what is refused is a *write* judged by rules the pen does not hold."""
    root = _enforcing(tmp_path)
    _reading(monkeypatch, _pair(plugin_version="0.1.0"))
    assert main(["-C", str(root), "list"]) == EXIT_OK


# -- what the guard in front of the write costs (RK1237) ----------------------


def _asked(monkeypatch, plugin, *, calls: list[bool]) -> None:
    """A registry answering ``plugin``, with every `engine()` reading recorded.

    The cache on `engine` is per process and this suite is one, so it is cleared here: a
    second test would otherwise measure the first one's answer and pass by measuring nothing.
    """
    from roadkeep import installing
    from roadkeep.provenance import Engine, engine

    engine.cache_clear()
    monkeypatch.setattr(installing, "installed", lambda base: plugin)

    def reading(placed: bool = True) -> Engine:
        calls.append(placed)
        return Engine(
            version="0.1.1",
            home=Path("/tree/src/roadkeep"),
            commit="abc1234" if placed else None,
        )

    monkeypatch.setattr(installing, "engine", reading)
    monkeypatch.setattr("roadkeep.provenance.engine", reading)


def _installed(version: str, commit: str | None = "abc1234"):
    from roadkeep.provenance import Installed

    return Installed(version=version, home=Path("/cache"), commit=commit, scope="user")


def test_a_copy_at_another_version_is_answered_without_asking_git(tmp_path, monkeypatch):
    """The measurement RK1235 shipped without: `engines` is 45 ms — `ls-files`, `rev-parse`
    and `status --porcelain` at 14, 14 and 16 — against RK176's 43 ms floor for a whole
    command, and cached per *process*, which on a CLI is once per write and never twice.

    The version is a module attribute, and it is what decides the case this guard is for."""
    from roadkeep.installing import behind

    calls: list[bool] = []
    _asked(monkeypatch, _installed("0.1.0"), calls=calls)
    assert behind(tmp_path) is True
    assert calls == [False], "the placed reading is the one that costs, and nothing needed it"


def test_no_plugin_is_answered_without_asking_git_either(tmp_path, monkeypatch):
    from roadkeep.installing import behind

    calls: list[bool] = []
    _asked(monkeypatch, None, calls=calls)
    assert behind(tmp_path) is False
    assert calls == [False]


def test_two_copies_at_one_version_are_worth_the_sha(tmp_path, monkeypatch):
    """The case the cheap reading cannot decide, and the one RK418 exists for: two
    `src/roadkeep/` trees fourteen files apart answered the same number."""
    from roadkeep.installing import behind

    calls: list[bool] = []
    _asked(monkeypatch, _installed("0.1.1", commit="def5678"), calls=calls)
    assert behind(tmp_path) is True
    assert calls == [False, True], "the versions matched, so the sha is what tells them apart"


def test_the_narrowing_this_task_filed_was_the_wrong_one(tmp_path, monkeypatch):
    """Filed as *drop `status --porcelain`*, and that reading was wrong. `modified` is exactly
    what separates `unpinnable` from `behind`, and this guard has to make that separation: a
    developer's checkout with uncommitted work, at the plugin's version and on another commit,
    is where a developer lives and refusing it is the failure the design exists to avoid."""
    from roadkeep.installing import Engines
    from roadkeep.provenance import Engine

    working = Engines(
        running=Engine(
            version="0.1.1", home=Path("/tree"), commit="abc1234", modified=True
        ),
        plugin=_installed("0.1.1", commit="def5678"),
    )
    assert working.verdict == UNPINNABLE
    # Which is not `behind`, so the write stands — and dropping the read that says so would
    # have turned every such checkout into a refusal.
    assert working.verdict != BEHIND


def test_the_unplaced_reading_is_the_same_verdict_with_poorer_facts(tmp_path, monkeypatch):
    """One verdict and never two (RK300): what changes between the two calls is the facts,
    never the judgement — an unplaced engine is the state a marketplace row with no sha
    already puts every reader in, and `verdict` already answers for it."""
    from roadkeep.provenance import engine

    engine.cache_clear()
    unplaced = engine(placed=False)
    assert unplaced.version and unplaced.commit is None and unplaced.modified is False
    # And both questions are cached, so a process asking each asks it once.
    assert engine(placed=False) is unplaced
    engine.cache_clear()


# -- and the gate that judged it (RK1238) -------------------------------------


def _linted(tmp_path: Path, config: str = ENFORCED):
    from roadkeep.config import Config
    from roadkeep.linting import lint

    return lint(Config.discover(_enforcing(tmp_path, config)))


def test_a_clean_report_says_whose_clean_it_is(tmp_path, monkeypatch):
    """RK1235 guards the pen and left the judge, which is the same copy. So on a pinned
    project running a stale engine the writes stop and `lint` keeps answering from rules that
    have moved: it reports clean, and the action CI runs at its own ref disagrees."""
    _reading(monkeypatch, _pair(plugin_version="0.1.4"))
    report = _linted(tmp_path)
    assert report.clean, [str(one) for one in report.findings]
    (said,) = [one for one in report.notes if one.code == "gate.behind"]
    assert "0.1.1" in said.message and "0.1.4" in said.message
    # Filed where the decision is written, which is the file a reader would open to change it.
    assert said.file == "roadkeep.toml"


def test_it_is_a_note_and_never_a_finding(tmp_path, monkeypatch):
    """The whole shape. A refusal is wrong — `lint` exiting 2 because a copy is old turns one
    stale plugin into a repository nobody can commit in, which is the state `guard` is written
    to survive — and a finding is wrong for RK1192's reason, firing every turn until somebody
    updates."""
    _reading(monkeypatch, _pair(plugin_version="0.1.4"))
    report = _linted(tmp_path)
    assert "gate.behind" not in {one.code for one in report.findings}
    assert "gate.behind" in {one.code for one in report.notes}


def test_a_project_that_declared_no_pin_is_told_nothing(tmp_path, monkeypatch):
    """The same standing RK1235's refusal has, and its whole extent: `[install] pinned` is the
    project saying which copy is right (L6), and without it three copies differing is the
    ordinary state of a machine that develops this tool."""
    _reading(monkeypatch, _pair(plugin_version="0.1.4"))
    report = _linted(tmp_path, 'prefix = "DX"\n[files]\nroadmap = "ROADMAP.md"\n')
    assert [one for one in report.notes if one.code == "gate.behind"] == []


def test_a_modified_checkout_is_not_behind_and_is_not_qualified(tmp_path, monkeypatch):
    """`behind` and never `unpinnable`, for the reason RK418 separated them: a checkout with
    uncommitted work is at no commit the plugin could match, and it is where a developer
    lives every day."""
    _reading(monkeypatch, _pair(modified=True))
    assert [one for one in _linted(tmp_path).notes if one.code == "gate.behind"] == []


def test_the_note_is_printed_on_a_report_that_passes(tmp_path, monkeypatch, capsys):
    """Where the whole value is. A refused write is a message read at the moment somebody
    asked for something; a gate that passes is silence, which is what the shipped `Stop` hook
    produces on every turn that changed nothing."""
    from composing import runs

    root = _enforcing(tmp_path)
    _reading(monkeypatch, _pair(plugin_version="0.1.4"))
    assert main(["-C", str(root), "lint"]) == EXIT_OK
    printed = capsys.readouterr().out
    assert "gate.behind" in printed and "clean" in printed
    # And the read it names runs as printed (RK1209), which is what makes it a door.
    assert runs(root, printed) == (["engines"],)


def test_the_door_names_all_three_rather_than_the_update(tmp_path, monkeypatch):
    """Which copy is right is a decision about a setup this tool can read and never make, so
    the remedy is the command that names all three."""
    from roadkeep.config import Config
    from roadkeep.remedying import remedy

    _reading(monkeypatch, _pair(plugin_version="0.1.4"))
    config = Config.discover(_enforcing(tmp_path))
    (said,) = [one for one in _linted(tmp_path).notes if one.code == "gate.behind"]
    rule = remedy(said, config)
    assert rule.kind == "read"
    assert [one.argv for one in rule.doors] == [("engines",)]


# -- two keys, because they are about two pairs of copies (RK1240) ------------


BOTH = (
    'prefix = "DX"\n[files]\nroadmap = "ROADMAP.md"\n'
    "[install]\npinned = true\nenforced = true\n"
)
JUST_PINNED = 'prefix = "DX"\n[files]\nroadmap = "ROADMAP.md"\n[install]\npinned = true\n'


def test_quieting_a_finding_does_not_buy_a_refusal_on_every_write(tmp_path, capsys, monkeypatch):
    """The defect this splits. `pinned` is RK1192's decision about the surfaces vendored into
    a project, measured against the engine answering; RK1235 and RK1238 borrowed it for the
    engine measured against the registered plugin, which is a different pair of copies.

    So a project that pinned to stop a finding it found noisy was being read as having asked
    for a write refusal — and the way back was unsetting the key and taking the noise again.
    """
    root = _enforcing(tmp_path, config=JUST_PINNED)
    _reading(monkeypatch, _pair(plugin_version="0.1.0"))
    assert main(_added(root)) == EXIT_OK
    assert [one for one in _linted(tmp_path, JUST_PINNED).notes if one.code == "gate.behind"] == []


def test_holding_the_engine_does_not_quiet_the_surfaces(tmp_path, monkeypatch):
    """And the other direction: `enforced` says the registered plugin is the copy that should
    write, which says nothing about whether this project's vendored launcher, hook and skill
    are where it wants them."""
    from roadkeep.config import Config

    config = Config.discover(_enforcing(tmp_path))
    assert config.install_enforced and not config.install_pinned
    # `_wired` reads `pinned` and nothing else, so the finding it silences is still live here.
    assert not config.install_pinned


def test_a_project_may_declare_both(tmp_path):
    from roadkeep.config import Config

    config = Config.discover(_enforcing(tmp_path, config=BOTH))
    assert config.install_pinned and config.install_enforced


def test_neither_key_is_on_by_default(tmp_path):
    """Off by default is the same choice `pinned` made and for its reason: nothing changes
    for a project that has not spoken, and it matters more here — a refusal nobody asked for
    is worse than a finding nobody asked for."""
    from roadkeep.config import Config

    config = Config.discover(
        _enforcing(tmp_path, config='prefix = "DX"\n[files]\nroadmap = "ROADMAP.md"\n')
    )
    assert not config.install_pinned and not config.install_enforced


def test_a_value_that_is_not_a_boolean_is_refused_the_same_way_for_both(tmp_path):
    from roadkeep.config import Config, ConfigError

    for key in ("pinned", "enforced"):
        _enforcing(
            tmp_path,
            config=f'prefix = "DX"\n[files]\nroadmap = "ROADMAP.md"\n[install]\n{key} = "yes"\n',
        )
        with pytest.raises(ConfigError) as refused:
            Config.discover(tmp_path)
        assert f"install.{key} must be true or false" in str(refused.value)


def test_a_third_key_under_install_is_still_refused(tmp_path):
    """The table stays closed, which is what makes a typo in either of these a refusal rather
    than a setting silently off."""
    from roadkeep.config import Config, ConfigError

    _enforcing(
        tmp_path,
        config='prefix = "DX"\n[files]\nroadmap = "ROADMAP.md"\n[install]\nenforce = true\n',
    )
    with pytest.raises(ConfigError) as refused:
        Config.discover(tmp_path)
    assert "install.enforce" in str(refused.value)


def test_the_report_heads_with_the_project_and_not_the_engine(project):
    """RK1359. The header named `source` — the checkout being wired in — while every row under
    it named a file in another tree, and the project written to appeared nowhere. Measured on a
    reader: running `install -C <elsewhere>` from a neutral directory, that header read as
    *this is where it wrote*, and two commands went by before listing the filesystem showed the
    files in the target and `-C` honoured all along.

    Both, and never twice: the two trees collapse in the checkout that ships this package, so a
    second identical path would say nothing; they differ for an adopter, which is who `install`
    is for, and the launcher a hook runs months later lives in the engine's tree."""
    adopter = project
    said = plan(adopter, source=HERE).stated(checked=True)
    head, *rest = said.splitlines()

    # The project heads it, which is the reader's first question on a write.
    assert head.startswith(adopter.as_posix()), head
    # And the engine is named beside it, because it is a different tree here.
    assert any(HERE.as_posix() in line and "not this project" in line for line in rest), said

    # Where the two are one tree, the second path is not printed: it would repeat the first.
    alone = plan(HERE, source=HERE).stated(checked=True)
    assert alone.splitlines()[0].startswith(HERE.as_posix())
    assert "not this project" not in alone


# -- what the surfaces let a session do (RK1438) ------------------------------


def test_the_write_ends_by_saying_what_the_surfaces_now_let_a_session_do(project, source):
    """RK1438. The report is an accurate account of files and said nothing about the tool it
    installs. For an agent that output is often the first contact and the first refusal is the
    second; the skill is the third, arrives on a later turn, and is long enough to be skimmed
    — so the two surfaces a session reliably reads were the two saying least about the shape
    of the thing. Not more documentation: the smallest useful part of it, where somebody is
    already looking."""
    said = install(project, source=source).stated(checked=False)
    orientation = [line for line in said.splitlines() if "from here" in line]
    assert len(orientation) == 5, said
    joined = " ".join(orientation)
    # The verbs a day uses, the gate, the two reads that save a refusal, and the check.
    for verb in ("brief", "add", "ship", "lint", "repair", "budget", "show", "install --check"):
        assert f"`roadkeep {verb}" in joined or f"{verb}`" in joined, verb
    # And what stopped being hand-editable, which is the fact the guard enforces.
    assert "roadkeep.toml" in joined
    # After the surfaces, never among them: a reader scanning states is not reading prose.
    assert said.index("from here") > said.rindex("not written")


def test_the_check_prints_no_orientation_because_ci_runs_it_every_push(project, source):
    """An adopter runs the write once and reads it. The check runs on every push, and five
    lines of orientation there are five lines nobody reads, every time."""
    install(project, source=source)
    assert "from here" not in plan(project, source=source).stated(checked=True)


def test_the_payload_carries_the_same_sentences_the_report_prints(project, source):
    """RK1447. RK1438 put those lines on stdout and left the payload saying only which files
    moved — and the caller most likely to run `install --json` is the one wiring a project from
    a script or a session, which is exactly the reader they were written for. Block C's rule:
    both registers come off one record, because a printer and a payload builder agreeing by
    hand is how an agent comes to be told less than the person at the terminal."""
    intent = install(project, source=source)
    said = intent.stated(checked=False)
    published = intent.payload(checked=False)["orientation"]
    assert published == intent.orientation()
    # The label and its column are the terminal's; the sentence is what both carry.
    for sentence in published:
        assert f"  from here      {sentence}" in said


def test_the_key_is_empty_under_a_check_and_never_missing(project, source):
    """The `driver` key's rule for its reason: the register split is deliberate, and a reader
    has to tell "nothing was wired here" from "this payload predates the field"."""
    install(project, source=source)
    payload = plan(project, source=source).payload(checked=True)
    assert payload["orientation"] == []


# -- the fourth copy, and the one that runs unwatched (RK1385) -----------------


def test_the_driver_is_a_row_and_says_when_nothing_is_wired():
    """RK1385. `engines` named three copies and git runs a fourth: the merge driver, invoked
    mid-merge on the files whose whole claim is that their merge is decidable. `merge --check`
    answers whether git can run it, which is a different question (RK266) — this says which.

    Said either way, for the reason every absence here is: a driver nothing wired and one this
    could not read look the same to a reader, and only one means git merges these textually."""
    from dataclasses import replace

    bare = replace(_pair(), driver="")
    assert "merge    —" in bare.stated()
    # And which half it read (RK1388): this row is the config, and the attribute lines are
    # a committed file — a tree can hold either without the other.
    assert "this clone's git config" in bare.stated()
    assert "attribute half" in bare.stated()
    assert bare.payload()["driver"] == ""


def test_the_driver_row_says_whether_it_is_this_tree():
    """The comparison the reader came for, and the whole of what a path can answer: a console
    script installed months ago and a working checkout both resolve, both pass `--check`, and
    only one of them is the tree whose rules the merge is about."""
    from dataclasses import replace

    here = replace(_pair(), driver="/tree/.venv/bin/roadkeep merge %O %A %B --path %P")
    assert "this tree" in here.stated()
    other = replace(_pair(), driver="/elsewhere/roadkeep merge %O %A %B --path %P")
    assert "another copy" in other.stated()
    assert other.payload()["driver"].startswith("/elsewhere/")


def test_the_version_is_never_read_because_reading_it_would_run_it():
    """`merging._resolves` refuses to execute a stored driver to find out whether it executes,
    and asking it for a version is that same side effect. So the row carries the command, and
    nothing here spawns anything: what a reader compares is a path."""
    import ast
    from pathlib import Path as _Path

    source = (_Path(__file__).resolve().parents[1] / "src" / "roadkeep" / "installing.py")
    (driver,) = [
        node
        for node in ast.walk(ast.parse(source.read_text(encoding="utf-8")))
        if isinstance(node, ast.FunctionDef) and node.name == "_driver"
    ]
    called = {
        node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", "")
        for node in ast.walk(driver)
        if isinstance(node, ast.Call)
    }
    assert not called & {"run", "check_output", "Popen", "system"}, called


def test_no_two_reads_of_the_wiring_can_be_read_as_contradicting(project, source, capsys):
    """RK1388. This wiring has two halves — the attribute lines a repository commits and the
    config a clone holds — and a tree can hold either without the other. `merge --check` says
    which of the two each of its rows is about; the rows RK1385 and RK1387 added inherited one
    half each and said neither, so running all three answered *unwired* and then *routed*, and
    reconciling them meant already knowing which half had been read.

    Driven against the state that makes the two disagree: attributes written, config unset."""
    declaring(project, CLEAN)
    assert main(["-C", str(project), "merge", "--register"]) == EXIT_OK
    capsys.readouterr()

    assert main(["-C", str(project), "engines"]) in (EXIT_OK, EXIT_GATE)
    engines_said = [
        line for line in capsys.readouterr().out.splitlines() if line.startswith("merge")
    ]
    assert engines_said, "the engines read stopped carrying the driver row"
    assert "git config" in engines_said[0]

    assert main(["-C", str(project), "install", "--source", str(source), "--check"]) in (
        EXIT_OK,
        EXIT_GATE,
    )
    (install_said,) = [
        line for line in capsys.readouterr().out.splitlines() if ".gitattributes:" in line
    ]
    assert "attribute half" in install_said
    # And both defer to the verb that owns the question rather than answering the other half.
    assert "merge --check" in engines_said[0]
    assert "merge --check" in install_said


def test_the_count_a_sentence_states_says_which_question_it_is_about():
    """RK1392. RK1385 added a fourth row and eight sentences across five files went on counting
    three — but not wrongly in one way, which is the whole of it. The **read** answers four; the
    **verdict** compares three, the driver being a command this tool refuses to execute rather
    than a version it could compare. A find and replace would have made the second set false.

    Read off the record rather than off prose: what a sentence may say is decided by what the
    dataclass answers, so this fails when a row is added and the distinction is not restated."""
    from dataclasses import replace, fields

    from roadkeep.installing import Engines

    read = {one.name for one in fields(Engines)} - {"running"}
    # Five rows: the pen, the plugin, the vendored copy, the gates and the driver — and the
    # declaration, which is not a copy at all (RK1469): it is what this project says it runs,
    # read so `--invoke` answers off the file instead of restating the launcher's own order.
    assert read == {"plugin", "vendored", "gates", "driver", "declared"}, sorted(read)
    # And the verdict still compares two: adding a driver never moves it, whatever it holds,
    # and neither does a vendored copy — that one is `split`, which is a different pair
    # (RK1451) and deliberately has no standing to refuse a write.
    pair = _pair()
    for command in ("", "/elsewhere/roadkeep merge %O %A %B --path %P"):
        assert replace(pair, driver=command).verdict == pair.verdict
        assert replace(pair, driver=command).agree == pair.agree


# -- the copy inside the project, which the launcher finds first (RK1451) ------


def _vendoring(root: Path, version: str) -> Path:
    """A project holding a vendored engine, as `install --vendor` leaves one."""
    home = root / ".roadkeep" / "src" / "roadkeep"
    home.mkdir(parents=True)
    (home / "__init__.py").write_text(f'__version__ = "{version}"\n', encoding="utf-8")
    (root / ".roadkeep" / "scripts").mkdir()
    return home


def test_a_second_local_engine_is_a_row_rather_than_a_silence(tmp_path, capsys, monkeypatch):
    """RK1451. Observed in Japode/cloud: `roadkeep engines` said `writing 0.2.58` and the same
    command through the launcher said `writing 0.1.1269`. Both exited 0, both reported no
    plugin, and neither had a row for the other — so the read that exists to reconcile the
    copies in play was the one place a second local engine was invisible.

    It decides who writes. `.mcp.json` runs the launcher and so does the guard, so every tool
    call and every denied hand edit went through 0.1, while a shell reaching `roadkeep` got
    0.2 and judged the same files by it."""
    root = tmp_path / "project"
    root.mkdir()
    _vendoring(root, "0.1.1269")
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "empty"))

    # The exit code is the answer, the way it is for the pen and the judge: a session that has
    # to grep a sentence to learn two engines are in play is one that will not ask.
    assert main(["-C", str(root), "engines"]) == EXIT_GATE
    said = capsys.readouterr().out
    (row,) = [line for line in said.splitlines() if line.startswith("vendored")]
    assert "0.1.1269" in row and ".roadkeep/src/roadkeep" in row
    assert "the copy the launcher runs" in row
    # And its own `differ` sentence: these two are both pens, so `/plugin update` is not the
    # move and naming a judge that does not exist is how the wrong pair got read.
    (differs,) = [line for line in said.splitlines() if line.startswith("differ")]
    assert "the launcher runs the vendored 0.1.1269" in differs
    assert "judge" not in differs


def test_the_copy_answering_out_of_the_vendored_tree_says_so(tmp_path, monkeypatch):
    """Run through the launcher the two rows are one copy, and the row is still the whole of
    what a reader there was missing: which of the engines on this machine answered."""
    from roadkeep.installing import Engines, Vendor
    from roadkeep.provenance import Engine

    home = _vendoring(tmp_path, "0.1.1269")
    same = Engines(
        running=Engine(version="0.1.1269", home=home, commit=None),
        vendored=Vendor(version="0.1.1269", home=home),
    )
    assert "this is the copy answering" in same.stated()
    # Trivially agreed, the two reading one `__init__.py` — and no `differ` invented for it.
    assert same.agree and not same.split
    assert "differ" not in same.stated()


def test_a_project_that_vendored_nothing_gets_no_row(tmp_path, capsys, monkeypatch):
    """Unlike the plugin, the gate and the driver, an absent `.roadkeep/` is not an absence a
    reader can act on: it is every project that never ran `install --vendor`, and a row saying
    so on all of them is the noise this report refuses everywhere else."""
    root = tmp_path / "project"
    root.mkdir()
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "empty"))

    assert main(["-C", str(root), "engines", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["vendored"] is None and payload["split"] is False
    assert main(["-C", str(root), "engines"]) == EXIT_OK
    assert "vendored" not in capsys.readouterr().out


def test_the_line_a_shell_pastes_is_the_one_this_project_declares(tmp_path, capsys, monkeypatch):
    """RK1230 answers *which copy to call*, and RK1451 taught it to name the vendored copy —
    both restatements of a resolution order the launcher owns, of which this knew the middle
    and neither end (RK1469). What it answers now is what the project wrote down, which is
    literally what the harness runs."""
    only_here(monkeypatch, tmp_path)
    root = declaring(tmp_path / "project", CLEAN)
    _engine_copy(root / PROJECT_ENGINE, "9.9.9", "THE VENDORED ENGINE WROTE THIS.")
    install(root)
    capsys.readouterr()

    assert main(["-C", str(root), "engines", "--invoke"]) == EXIT_OK
    (said,) = capsys.readouterr().out.splitlines()
    # The declaration, resolved and up to the program: a command carrying
    # `${CLAUDE_PROJECT_DIR}` is one nobody can paste, and one ending in `mcp` is one no verb
    # can follow. The vendored copy is where `install` pointed it (RK1464).
    assert "${CLAUDE_PROJECT_DIR" not in said
    assert not said.endswith(" mcp"), said
    assert said.endswith(f"{PROJECT_ENGINE}/{LAUNCHER}"), said


def _declaring_mcp(root: Path, command: str, args: list[str]) -> None:
    """A `.mcp.json` written by hand, which is what this file is: a declaration `install`
    merges into rather than owns, and other tools declare in it too."""
    (root / ".mcp.json").write_text(
        json.dumps({"mcpServers": {"roadkeep": {"command": command, "args": args}}}),
        encoding="utf-8",
    )


def test_a_declaration_this_tool_did_not_write_is_not_guessed_at(tmp_path, capsys, monkeypatch):
    """RK1492. RK1469 found the cut before `mcp` by taking the last argument ending in `.py`,
    which is one shape of a file this command merges into rather than owns. A declaration whose
    program is not a Python file returned the **whole** argv, `mcp` included, so the line a
    caller pasted started a server instead of running the verb they appended."""
    from roadkeep.provenance import invocation

    only_here(monkeypatch, tmp_path)
    root = tmp_path / "project"
    root.mkdir()
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "empty"))
    # A console script, which is how this tool is meant to be installed and carries no `.py`
    # anywhere. The old reader returned `roadkeep mcp`; a verb appended to that runs a server.
    _declaring_mcp(root, "roadkeep", ["mcp"])
    assert main(["-C", str(root), "engines", "--invoke"]) == EXIT_OK
    said = capsys.readouterr().out.strip()
    assert said == invocation()
    assert not said.endswith(" mcp")


def test_a_py_option_value_no_longer_decides_where_the_command_ends(tmp_path, capsys, monkeypatch):
    # The other half of the same guess: a `.py` that is an *option value* stopped the cut in
    # the wrong place, so the program never made it into the line.
    only_here(monkeypatch, tmp_path)
    root = tmp_path / "project"
    root.mkdir()
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "empty"))
    _declaring_mcp(root, "uv", ["run", "--with", "of.py", "roadkeep", "mcp"])
    assert main(["-C", str(root), "engines", "--invoke"]) == EXIT_OK
    assert "of.py" not in capsys.readouterr().out


def test_the_program_is_the_launcher_this_command_writes(tmp_path, capsys, monkeypatch):
    """The fact in place of the guess: both spellings `install` writes, wherever they are
    addressed from — a relative walk, a placeholder, three arguments in."""
    from roadkeep.installing import declared_launcher

    only_here(monkeypatch, tmp_path)
    root = tmp_path / "project"
    root.mkdir()
    _declaring_mcp(root, "uv", ["run", "python", f"../engine/{LAUNCHER}", "mcp"])
    assert declared_launcher(root).endswith(f"../engine/{LAUNCHER}")
    assert not declared_launcher(root).endswith(" mcp")
    # And the bridge a project commits where no plugin can be (RK1108), under its placeholder.
    _declaring_mcp(root, "python", ["${CLAUDE_PROJECT_DIR:-.}/" + PROJECT_BRIDGE, "mcp"])
    assert declared_launcher(root).endswith(PROJECT_BRIDGE)
    assert "${CLAUDE_PROJECT_DIR" not in declared_launcher(root)


def test_a_project_that_declares_nothing_names_the_copy_answering(tmp_path, capsys, monkeypatch):
    # A `.roadkeep/` nothing points at is a directory: with no declaration the copy the caller
    # reaches *is* the one that answers, and naming a second would invent a disagreement.
    from roadkeep.provenance import invocation

    root = tmp_path / "project"
    root.mkdir()
    _vendoring(root, "0.1.1269")
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "empty"))

    assert main(["-C", str(root), "engines", "--invoke"]) == EXIT_OK
    assert capsys.readouterr().out.strip() == invocation()


def test_a_directory_with_no_package_in_it_is_not_an_engine(tmp_path, monkeypatch):
    """A `.roadkeep/` this cannot read a version out of is a directory, not a second copy —
    the same direction every other absence in this report takes."""
    from roadkeep.installing import vendored_at

    (tmp_path / ".roadkeep" / "src" / "roadkeep").mkdir(parents=True)
    assert vendored_at(tmp_path) is None
    (tmp_path / ".roadkeep" / "src" / "roadkeep" / "__init__.py").write_text(
        '"""No literal here."""\n', encoding="utf-8"
    )
    assert vendored_at(tmp_path) is None


def test_the_vendored_row_is_read_and_never_run(tmp_path):
    """`candidates` spends a subprocess per engine because ranking one to pin has to prove it
    imports. This reader is choosing nothing, and it sits on the path `lint` takes through
    `engines` — a 30-second probe of that shape is a gate that hangs. So the literal is the
    answer, RK19 making it the one place the number is written."""
    import ast
    from pathlib import Path as _Path

    source = _Path(__file__).resolve().parents[1] / "src" / "roadkeep" / "installing.py"
    (reader,) = [
        node
        for node in ast.walk(ast.parse(source.read_text(encoding="utf-8")))
        if isinstance(node, ast.FunctionDef) and node.name == "vendored_at"
    ]
    called = {
        node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", "")
        for node in ast.walk(reader)
        if isinstance(node, ast.Call)
    }
    assert not called & {"run", "check_output", "Popen", "system", "_asked"}, called


# -- one home, two versions, and a verdict of agreed (RK1452) ------------------


def test_a_home_swapped_under_the_process_is_not_agreement(tmp_path):
    """RK1452, reproduced in Japode/cloud. An MCP server was started on a vendored
    `.roadkeep/` at 0.1.1269 and `install --vendor` then replaced that directory **in place**
    with 0.2.4. Python had already loaded the modules, so the server kept answering 0.1.1269
    for a path that had not held it since — and the payload said `"agree": true`.

    That verdict is the defect and not the version. This verb's own contract is that copies
    may differ and what is not survivable is being unable to say which one answered; here it
    named a version the home has not held, then certified agreement about it. Nothing in the
    answer looked stale: the number was plausible and the home was right."""
    from roadkeep.installing import Engines
    from roadkeep.provenance import Engine

    home = tmp_path / ".roadkeep" / "src" / "roadkeep"
    home.mkdir(parents=True)
    (home / "__init__.py").write_text('__version__ = "0.2.4"\n', encoding="utf-8")

    read = Engines(running=Engine(version="0.1.1269", home=home, commit=None))
    assert read.swapped and not read.agree
    (row,) = [line for line in read.stated().splitlines() if line.startswith("swapped")]
    # Both numbers, because either alone is plausible: the one running and the one that path
    # holds now, which is what tells a reader the answer is about a copy that is gone.
    assert "0.2.4" in row and "0.1.1269" in row
    assert "restart the session" in row
    assert read.payload()["swapped"] is True
    assert read.payload()["writing"]["on_disk"] == "0.2.4"


def test_the_version_a_home_states_is_read_at_answer_time(tmp_path):
    """Never cached, for `Engine.stale`'s reason one field along: identity is a fact about the
    process and this is a fact about the directory right now. A reading decided at start-up is
    the one this exists to correct."""
    from roadkeep.provenance import Engine

    home = tmp_path / "roadkeep"
    home.mkdir()
    (home / "__init__.py").write_text('__version__ = "0.1.1269"\n', encoding="utf-8")
    running = Engine(version="0.1.1269", home=home, commit=None)
    assert running.on_disk == "0.1.1269"

    (home / "__init__.py").write_text('__version__ = "0.2.4"\n', encoding="utf-8")
    assert running.on_disk == "0.2.4"


def test_a_home_that_states_nothing_is_not_a_disagreement(tmp_path):
    """A frozen build, a wheel with no source, a tree half-written by a copy in progress. The
    honest answer is that this directory says nothing, and reading that as a swap would refuse
    agreement on every project a wheel is installed into."""
    from roadkeep.installing import Engines
    from roadkeep.provenance import Engine, stated_at

    assert stated_at(tmp_path / "nowhere") == ""
    (tmp_path / "__init__.py").write_text('"""No literal here."""\n', encoding="utf-8")
    assert stated_at(tmp_path) == ""

    read = Engines(running=Engine(version="0.1.1269", home=tmp_path, commit=None))
    assert not read.swapped and read.agree
    assert "swapped" not in read.stated()
    assert read.payload()["writing"]["on_disk"] is None


def test_the_number_is_read_to_the_closing_quote(tmp_path):
    """A quoted literal and nothing else. Stripped at the ends instead, a trailing comment
    became part of the number and every comparison against it was a disagreement — and a
    right-hand side this would have to evaluate states nothing, a version a build backend
    could not read being one this has no business guessing at either."""
    from roadkeep.provenance import stated_at

    (tmp_path / "__init__.py").write_text(
        '__version_info__ = (0, 1)\n__version__ = "0.2.4"  # bumped by the hook\n',
        encoding="utf-8",
    )
    assert stated_at(tmp_path) == "0.2.4"

    (tmp_path / "__init__.py").write_text(
        "__version__ = _read_from_metadata()\n", encoding="utf-8"
    )
    assert stated_at(tmp_path) == ""


def test_a_rewrite_at_the_same_version_is_not_a_swap(tmp_path):
    """The reading `Engine.stale` could not have given. An mtime moves for a swap and also for
    every save a developer makes in a checkout, which is why that one is the note a session
    learns to ignore; a version moves only where somebody released or bumped."""
    from roadkeep.installing import Engines
    from roadkeep.provenance import Engine

    home = (tmp_path / "roadkeep").resolve()
    home.mkdir()
    (home / "__init__.py").write_text('__version__ = "0.1.1269"\n', encoding="utf-8")
    running = Engine(version="0.1.1269", home=home, commit=None)
    # Every file under it rewritten, and nothing about which copy is running has changed.
    (home / "cli.py").write_text("# edited\n", encoding="utf-8")
    (home / "__init__.py").write_text('__version__ = "0.1.1269"  # edited\n', encoding="utf-8")
    assert running.on_disk == running.version
    assert not Engines(running=running).swapped


# -- the finding that is about the reader, not the project (RK1482) ------------


def test_a_page_this_project_never_had_is_told_apart_from_one_that_drifted(project):
    """RK1482, measured on one long session: it read past three `install.stale` notes for
    hours and only looked when it ran out of roadmap work. What it was reading past was two
    pages that did not exist — so it never learnt that `budget --anchor` measures a section
    before it is sent, and one design took five refusals against the word limit for want of a
    page one command away. *Behind* and *absent* wear the same shape and cost different
    things."""
    from roadkeep.config import Config
    from roadkeep.linting import lint

    install(wired(project), source=HERE)
    beside = project / ".claude" / "skills" / "roadkeep" / "asking.md"
    assert beside.is_file(), "the page this test is about is one `install` writes"
    beside.unlink()
    (project / PROJECT_SKILL).write_text("stale\n", encoding="utf-8")

    codes = {one.code: one for one in lint(Config.discover(project)).notes}
    assert set(codes) >= {"install.stale", "install.absent"}
    assert codes["install.absent"].file.endswith("asking.md")
    assert "no copy of it" in codes["install.absent"].message
    assert codes["install.stale"].file == PROJECT_SKILL


def test_the_summary_line_carries_what_a_skimming_reader_would_miss(project, capsys):
    """On the summary because that is the line a reader who skims one line a run sees, and the
    notes above it are the fifteen they do not."""
    from roadkeep.cli import EXIT_OK, main
    from roadkeep.provenance import invocation

    install(wired(project), source=HERE)
    (project / ".claude" / "skills" / "roadkeep" / "asking.md").unlink()
    assert main(["-C", str(project), "lint"]) == EXIT_OK
    summary = capsys.readouterr().out.splitlines()[-1]
    assert "wired surface(s) behind this engine" in summary
    assert "1 of them missing entirely" in summary
    assert f"{invocation()} install" in summary


def test_the_clause_is_absent_where_the_wiring_is_current(project, capsys):
    # A clause that appears on every run is one a reader stops seeing, which is the failure
    # being repaired rather than a smaller version of it.
    from roadkeep.cli import EXIT_OK, main

    install(wired(project), source=HERE)
    assert main(["-C", str(project), "lint"]) == EXIT_OK
    assert "behind this engine" not in capsys.readouterr().out


def test_the_absent_page_names_the_same_door(project):
    # Two codes and one command: what differs is what the reader is missing, not what they run.
    from roadkeep.config import Config
    from roadkeep.linting import lint
    from roadkeep.remedying import remedy

    install(wired(project), source=HERE)
    (project / ".claude" / "skills" / "roadkeep" / "asking.md").unlink()
    config = Config.discover(project)
    (note,) = [one for one in lint(config).notes if one.code == "install.absent"]
    found = remedy(note, config)
    assert found is not None and found.doors[0].argv == ("install",)


# -- the guard with no way in (RK1485) -----------------------------------------


def test_the_check_says_when_nothing_records_which_engine_wrote_the_surfaces(project, capsys):
    """RK1485. RK1462 gave `install` a record so a refresh cannot be a downgrade, and every
    project already wired has none — which is exactly the population the defect was measured
    in. The record arrives on the next `install`, and the next `install` is the write being
    guarded against, so on the tree that needs it most the guard is inert until somebody makes
    the very edit it exists to refuse."""
    install(wired(project), source=HERE)
    source = project / "roadkeep.toml"
    source.write_text(
        "\n".join(
            one
            for one in source.read_text(encoding="utf-8").splitlines()
            if not one.startswith("wired =")
        )
        + "\n",
        encoding="utf-8",
    )
    assert main(["-C", str(project), "install", "--check"]) in (EXIT_OK, EXIT_GATE)
    said = capsys.readouterr().out
    assert "record         none" in said
    assert "cannot be told from a downgrade" in said


def test_the_absence_is_its_own_answer_and_not_the_absence_of_ahead(project, capsys):
    """`ahead: null` says *not ahead*; on a project that recorded nothing that is *not known
    to be ahead*, and a consumer branching on one key cannot tell the two apart."""
    install(wired(project), source=HERE)
    source = project / "roadkeep.toml"
    source.write_text(
        "\n".join(
            one
            for one in source.read_text(encoding="utf-8").splitlines()
            if not one.startswith("wired =")
        )
        + "\n",
        encoding="utf-8",
    )
    main(["-C", str(project), "install", "--check", "--json"])
    held = json.loads(capsys.readouterr().out)
    assert held["ahead"] is None and held["unrecorded"] is True


def test_a_project_that_recorded_one_is_not_told_the_direction_is_unknown(project, capsys):
    # `install` writes the record, so the run after it establishes what the run before could
    # only guess — which is the whole of what this task adds.
    assert main(["-C", str(wired(project)), "install", "--source", str(HERE)]) == EXIT_OK
    capsys.readouterr()
    main(["-C", str(project), "install", "--check", "--json"])
    assert json.loads(capsys.readouterr().out)["unrecorded"] is False


def test_the_note_says_the_direction_is_unestablished_where_nothing_records_one(project):
    """The gate's own sentence claims *behind*, and where no record exists that claim is a
    guess with a write attached. Saying so costs a clause and tells the one population RK1462
    could not reach."""
    from roadkeep.config import Config
    from roadkeep.linting import lint

    install(wired(project), source=HERE)
    source = project / "roadkeep.toml"
    source.write_text(
        "\n".join(
            one
            for one in source.read_text(encoding="utf-8").splitlines()
            if not one.startswith("wired =")
        )
        + "\n",
        encoding="utf-8",
    )
    (project / PROJECT_SKILL).write_text("stale\n", encoding="utf-8")
    (found,) = [
        one for one in lint(Config.discover(project)).notes if one.code == "install.stale"
    ]
    assert "which way that goes is unestablished" in found.message


def test_nothing_wired_is_not_a_record_that_is_missing(project, capsys):
    # There is no surface whose provenance could be unknown, and a row about a record that
    # would govern nothing is noise.
    main(["-C", str(project), "install", "--check", "--json"])
    assert json.loads(capsys.readouterr().out)["unrecorded"] is False


# -- the copy a refusal does not mention (RK1487) ------------------------------


def test_a_vendor_that_lands_and_then_refuses_says_what_is_on_disk(
    tmp_path, monkeypatch, capsys
):
    """RK1487. RK1464 moved the vendor in front of the surfaces and accepted the hazard RK1193
    had put it behind them for: a run that copies an engine and then fails to wire it leaves a
    copy nothing points at. The trade is right — a downgrade somebody commits is worse than a
    directory one more `install` clears — and it was silent, so the caller read what stopped
    the surfaces and nothing about what landed."""
    only_here(monkeypatch, tmp_path)
    _engine_copy(tmp_path / "new", "9.9.9", "THE VENDORED ENGINE WROTE THIS.")
    project = tmp_path / "adopter"
    project.mkdir()
    # A `.claude` that is a file, which is RK393's own blocker: the vendor lands and the
    # surfaces cannot be written, which is exactly the shape this refusal is about.
    (project / ".claude").write_text("not a directory\n", encoding="utf-8")

    monkeypatch.setenv("ROADKEEP_SRC", str(tmp_path / "new"))
    capsys.readouterr()
    assert main(["-C", str(project), "install", "--vendor"]) != EXIT_OK
    err = capsys.readouterr().err
    assert "9.9.9 landed in" in err and "nothing is wired to it" in err
    assert "install --check" in err
    # And the copy is on disk, which is what the sentence is about.
    assert (project / ".roadkeep" / "src" / "roadkeep").is_dir()


def test_a_run_that_wires_says_nothing_about_a_stranded_copy(tmp_path, monkeypatch, capsys):
    # The sentence is about a refusal, so a run that finished has nothing to say with it.
    only_here(monkeypatch, tmp_path)
    _engine_copy(tmp_path / "new", "9.9.9", "THE VENDORED ENGINE WROTE THIS.")
    project = declaring(tmp_path / "adopter", CLEAN)

    monkeypatch.setenv("ROADKEEP_SRC", str(tmp_path / "new"))
    capsys.readouterr()
    assert main(["-C", str(project), "install", "--vendor"]) == EXIT_OK
    assert "nothing is wired to it" not in capsys.readouterr().err


def test_a_check_that_refuses_names_no_copy_because_it_made_none(tmp_path, monkeypatch, capsys):
    # Silent under `--check`, which copied nothing: a sentence about a landing that did not
    # happen is the report describing a tree it did not write.
    only_here(monkeypatch, tmp_path)
    _engine_copy(tmp_path / "new", "9.9.9", "THE VENDORED ENGINE WROTE THIS.")
    project = tmp_path / "adopter"
    project.mkdir()
    (project / ".claude").write_text("not a directory\n", encoding="utf-8")

    monkeypatch.setenv("ROADKEEP_SRC", str(tmp_path / "new"))
    capsys.readouterr()
    main(["-C", str(project), "install", "--vendor", "--check"])
    assert "nothing is wired to it" not in capsys.readouterr().err
