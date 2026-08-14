"""The surfaces that run the gate somewhere other than a developer's machine (RK17).

A gate that runs in one place has a documented bypass, so the same command is declared in
a GitHub Action and a pre-commit hook. Neither is executable here — one needs GitHub and
the other needs `pre-commit` — but the failure worth catching is not the runner's, it is
**a surface that calls a command line the CLI does not accept**: a stale `--strict`, a
flag renamed in `cli.py`, a `-C` after the subcommand. That is decidable right here, by
feeding every declared command to the real parser.

So each declaration is read out of its file, split, and parsed by `build_parser()`. A
surface that drifts from the CLI fails a test instead of failing a push.
"""

from __future__ import annotations

import argparse
import re
import shlex
from pathlib import Path

import pytest

from surface import modules

from roadkeep.cli import build_parser

HERE = Path(__file__).resolve().parents[1]
ACTION = HERE / "action.yml"
HOOKS = HERE / ".pre-commit-hooks.yaml"
WORKFLOW = HERE / ".github" / "workflows" / "gate.yml"

#: A command as a declarative file spells one: the value of `run:` or `entry:`, or a line of
#: the block scalar one of those opens — a surface that has a flag to pass conditionally has
#: a script rather than a one-liner (RK84). Anchored at the start of the line either way, so
#: prose in a comment — this file's own examples included — is never a declaration.
_DECLARED = re.compile(r"^\s*(?:(?:run|entry):\s*)?(roadkeep\b.*)$", re.MULTILINE)


def declarations(path: Path) -> list[str]:
    return _DECLARED.findall(path.read_text(encoding="utf-8"))


def test_every_surface_declares_the_command_the_cli_accepts():
    # The whole point: two files that say `roadkeep lint` four ways, and one parser that
    # decides whether they still mean anything.
    found = declarations(ACTION) + declarations(HOOKS)
    assert len(found) == 4, found
    for declared in found:
        argv = shlex.split(declared)[1:]  # drop the program name
        args = build_parser().parse_args(argv)
        assert args.command == "lint", declared


def test_the_hook_ships_the_normalizing_variant_too():
    # RK16 is only reachable from a hook: a CI run that repaired the file would have to
    # commit it back, so `--fix` is offered where a human is standing there.
    fixes = [
        build_parser().parse_args(shlex.split(d)[1:]).fix for d in declarations(HOOKS)
    ]
    assert fixes == [False, True]


def test_the_hook_compares_against_the_commit_being_written():
    # RK36's check needs a revision, and a hook is the surface that always has one. The
    # action does not pass `--since`: a CI job's base branch is the caller's to name.
    since = [
        build_parser().parse_args(shlex.split(d)[1:]).since for d in declarations(HOOKS)
    ]
    assert since == ["HEAD", None]
    assert all(
        build_parser().parse_args(shlex.split(d)[1:]).since is None
        for d in declarations(ACTION)
    )


def test_the_action_reaches_the_baseline_flag_or_leaves_it_alone():
    # RK84's input, and the reason the action's `run:` is a script: a repository with
    # standing debt fails on the difference, and one without passes the same command it
    # always did. An empty input must not reach `--baseline` — `""` is not a revision.
    passed = [
        build_parser().parse_args(shlex.split(d)[1:]).baseline for d in declarations(ACTION)
    ]
    assert [bool(rev) for rev in passed] == [True, False]


def test_the_action_is_used_and_not_copied():
    # If CI ran its own `roadkeep lint` step, the action could break while the badge
    # stayed green — which is the one failure this repository cannot afford, since the
    # action is what adopting projects get.
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "uses: ./" in workflow
    assert not declarations(WORKFLOW)


def test_the_hook_does_not_pass_filenames():
    # The command reads `roadkeep.toml` to learn what it governs. Handed a list of staged
    # paths it would examine whatever was touched instead of the backlog.
    text = HOOKS.read_text(encoding="utf-8")
    assert text.count("pass_filenames: false") == 2


def test_the_surfaces_are_valid_yaml():
    # Structure, when a parser is available. Skipped rather than made a dev dependency:
    # the tool never reads YAML, and the test above is the one that must always run.
    yaml = pytest.importorskip("yaml", reason="pyyaml is not installed")
    action = yaml.safe_load(ACTION.read_text(encoding="utf-8"))
    assert action["runs"]["using"] == "composite"
    assert set(action["inputs"]) == {"directory", "python-version", "baseline"}
    # Interpolated into `env:` and never into the script: an input is a string another
    # repository's workflow supplies, and `${{ }}` inside a `run:` is that string becoming
    # shell. The block scalar the two commands live in is where that would have shown.
    assert "${{" not in action["runs"]["steps"][-1]["run"]
    hooks = yaml.safe_load(HOOKS.read_text(encoding="utf-8"))
    assert [hook["id"] for hook in hooks] == ["roadkeep-lint", "roadkeep-lint-fix"]
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    assert set(workflow["jobs"]) == {"lint", "tests", "payload", "drift", "client"}


def test_the_job_that_may_not_skip_fails_where_its_reader_is_missing():
    """The payload check skips without the `claude` CLI, and a skip is a green (RK334).

    `test_the_payload_passes_the_loaders_own_validator` is deliberately skippable: an
    adopting project's CI has no reason to install the Claude CLI, and a check that cannot
    skip would redden somebody else's build over a tool they do not run. That argument covers
    every project except this one, where the payload *is* the release — so the job added for
    it has to fail when the install did not happen, rather than reporting success over a
    validator that never ran. `claude --version` is that assertion, and nothing else in the
    job would notice: pytest exits 0 on a skip.
    """
    yaml = pytest.importorskip("yaml", reason="pyyaml is not installed")
    job = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))["jobs"]["payload"]
    script = "\n".join(step.get("run", "") for step in job["steps"])
    assert "claude.ai/install.sh" in script
    assert "claude --version" in script
    # Installed for this job alone, which is the decision `test_the_surfaces_are_valid_yaml`
    # states from the other side: the tool never reads YAML, so it is no dev dependency.
    assert "pyyaml" in script
    assert "pytest -q tests/test_plugin.py" in script


def test_the_gate_declares_what_its_token_may_do():
    """RK335's half that is not a decision: every job here checks out and reads, and two of
    them run a third-party installer under whatever the repository default grants."""
    yaml = pytest.importorskip("yaml", reason="pyyaml is not installed")
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    assert workflow["permissions"] == {"contents": "read"}


def test_the_reader_that_gates_a_merge_is_a_version_and_not_a_channel():
    """The half that is (RK335). A channel fetched fresh on every push means the tool the
    merge was gated by was chosen by a clock, and the file cannot say which one it was.

    What stays unpinned is named in the workflow rather than here: the loader is still a
    script fetched over TLS from the vendor's URL, and moving that trust to a key is the apt
    repository or the signed manifest. So the assertion is the one this file can make — the
    version is declared, it is what the installer is handed, and the step that proves the
    install happened proves it produced that version.
    """
    yaml = pytest.importorskip("yaml", reason="pyyaml is not installed")
    job = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))["jobs"]["payload"]
    pinned = job["env"]["CLAUDE_VERSION"]
    assert re.fullmatch(r"\d+\.\d+\.\d+", str(pinned)), pinned
    script = "\n".join(step.get("run", "") for step in job["steps"])
    assert 'bash -s "$CLAUDE_VERSION"' in script
    assert "stable" not in script, "a channel beside the pin is two answers about one reader"
    assert 'claude --version | grep -F "$CLAUDE_VERSION"' in script


def test_the_channel_is_asked_where_its_answer_cannot_gate_a_merge():
    """The cost RK335 accepted, given a signal that does not undo it (RK356).

    The pin means the validator drifts behind what an installing user gets, and the drift is
    quiet in the direction that matters: a payload defect the newer reader sees and the pinned
    one does not ships green. So the channel is asked again, in a job that **cannot fail the
    workflow** — which is what makes the question free to ask rather than a second answer about
    the reader a merge was gated by.

    Both halves are asserted, because either alone puts the channel back in the gate: a script
    that exits non-zero reddens the run whatever the flag says it meant to do, and the flag on
    a job that gates nothing is the declaration that it never should. And the pin is not read
    here — one number in two jobs is two numbers that will disagree, so this job compares
    nothing and reports which reader answered.
    """
    yaml = pytest.importorskip("yaml", reason="pyyaml is not installed")
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    job = workflow["jobs"]["drift"]
    assert job["continue-on-error"] is True
    assert job["needs"] == "payload"
    script = "\n".join(step.get("run", "") for step in job["steps"])
    assert "bash -s stable" in script
    assert "::warning::" in script and "::notice::" in script
    assert "exit 1" not in script
    # Named in the advice and never expanded: telling a reader which number to raise is the
    # useful half, and reading it here would be the number living in two jobs.
    assert "$CLAUDE_VERSION" not in script and "CLAUDE_VERSION" not in job.get("env", {})


def test_the_client_job_asserts_its_reader_ran_before_it_reports():
    """RK1010, and `payload`'s lesson one surface over: **a skip is a green**.

    The editor host is the sixth surface and the only one written in a language nothing else
    here speaks. Most of what proves it needs nothing — the manifest, the archive and the scan
    holding it to carrying no rule are read by pytest — but the harness that runs the client
    against the real command needs node, and `tests/test_editor.py` skips those cases without
    it. So the job pins a version and asserts node answered *before* the tests run: without
    that step a runner image that dropped node would report this surface as proven while
    testing none of it, which is exactly what `claude --version` is doing two jobs up.

    And the archive is built here rather than only read: what an installing reader takes is
    written from the files in this tree with no toolchain, so a break in it is this
    repository's own and there is no vendor to wait for.
    """
    yaml = pytest.importorskip("yaml", reason="pyyaml is not installed")
    job = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))["jobs"]["client"]
    pinned = job["env"]["NODE_VERSION"]
    assert re.fullmatch(r"\d+", str(pinned)), pinned
    steps = "\n".join(step.get("run", "") for step in job["steps"])
    assert 'node --version | grep -F "v$NODE_VERSION."' in steps
    assert "pytest -q tests/test_editor.py" in steps
    assert "scripts/build_vsix.py" in steps
    # No dependency and no build step on the Python side, which is the half of RK1010 that is
    # about this repository rather than about the client.
    assert "npm" not in steps and "npx" not in steps


def test_the_client_is_gated_against_this_repository_s_own_docs():
    """The same fixture everything else here is gated on. A client tested against a fixture of
    its own is a client that agrees with a file nobody ships."""
    yaml = pytest.importorskip("yaml", reason="pyyaml is not installed")
    job = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))["jobs"]["client"]
    assert any(step.get("uses", "").startswith("actions/checkout") for step in job["steps"])
    assert any(step.get("uses", "").startswith("actions/setup-node") for step in job["steps"])


# -- every write says what to stage, or says why it does not (RK1130) -----------

#: The write commands that print no `git add --` line, each with the reason. Four of them
#: write a file the caller **named** — `init` scaffolds it, `install` and `uninstall` wire the
#: harness, `adopt` writes nothing at all and estimates — and `export` writes the projection
#: *as the work*, so a line restating it is the answer repeating the question. Declared rather
#: than derived: an exemption nobody wrote down is a verb that quietly stopped answering.
EXEMPT = {
    "init": "scaffolds the files the caller asked for, so the paths are the argument",
    "install": "wires the harness's own surfaces, which are not governed files",
    "uninstall": "un-wires the same surfaces, and names each as it takes it out",
    "export": "the projection *is* the work here, so the staging line restates the argument",
    # Found by the closure below rather than by a reader, which is the whole argument for it.
    "repair": "writes nothing itself: it re-enters the dispatcher per step, and each step's "
    "own output is deliberately not suppressed — so the staging lines are the steps'",
    # RK1142: the one write whose file is not in the repository at all. `.roadkeep/` is
    # git-ignored by the same run that creates it (RK89), so there is nothing to stage and a
    # `git add --` line naming an ignored path would be a command that does nothing.
    "capture filed": "writes into `.roadkeep/reports/`, which the tool teaches git to ignore",
}


def writes() -> dict[str, str]:
    """Every command the parser declares that is not `reads_only`, as `<path>` → handler."""
    found: dict[str, tuple[str, bool]] = {}

    def walk(parser, path=()):
        for action in parser._actions:
            if isinstance(action, argparse._SubParsersAction):
                for name, sub in action.choices.items():
                    walk(sub, (*path, name))
        handler = parser.get_default("handler")
        if handler is not None:
            found[" ".join(path)] = (handler.__name__, bool(parser.get_default("reads_only")))

    walk(build_parser())
    return {name: handler for name, (handler, reads) in found.items() if not reads}


def test_every_write_command_is_either_wired_or_exempted():
    """RK1130's closure. The sweep was mechanical and that is exactly why it needs one: a verb
    added tomorrow inherits the defect silently, and what the defect costs is a commit that
    passes the gate locally and fails it in a clean checkout."""
    declared = set(writes())
    assert set(EXEMPT) <= declared, sorted(set(EXEMPT) - declared)
    wired = declared - set(EXEMPT)
    # The number in RK1130's own line was 32 — read as `63 - 31 reads_only`, one command
    # short. Stated here as the parser answers it, because that is the reading that binds.
    # 34 since `capture filed` (RK1142), which is exempt: its file is not in the repository.
    # 33 since RK1147: `adopt` was exempt with the reason *writes nothing*, which is a
    # `reads_only` declaration written as a comment in a test — so the parser says it now, the
    # verb is out of the write lock, and this row is gone rather than restating it.
    # 34 since `refs` (RK1168), which is wired: it writes a prose file and `roadkeep.toml`, and
    # the staging line names both — the config being the half a reviewer would otherwise miss.
    assert len(declared) == 34 and len(wired) == 28


def test_every_wired_write_reaches_the_one_printer():
    """Executed rather than asserted, which is `test_doors`' rule: each handler is read for the
    call, because a staging line composed per verb is a line that comes to differ per verb."""
    # `surface.modules` and never a glob of its own (RK496): the one module allowed to ask the
    # filesystem what this package holds is the one every survey quantifies over, so a layout
    # that moves takes this reader with it instead of leaving it quietly covering nothing.
    source = {one.where: one.text for one in modules() if one.where.startswith("verbs/")}
    handlers = {handler for name, handler in writes().items() if name not in EXEMPT}
    missing = []
    for handler in sorted(handlers):
        body = next(
            (
                text.split(f"def {handler}(", 1)[1]
                for text in source.values()
                if f"def {handler}(" in text
            ),
            "",
        )
        # Up to the next top-level def: a handler that delegates is read through its own body.
        body = body.split("\ndef ", 1)[0]
        # `_staging_rows` since RK1170: the sentence is composed where the answer is and written
        # by the one seam, so what a handler must reach is the producer rather than a printer.
        if "_staging_rows" in body or "_scope_rows" in body:
            continue
        # **One hop, where the verb moved onto its record** (RK1170): a handler that renders
        # through `stated` composes the line inside that method, so this follows the delegation
        # rather than calling a moved verb a missing one. Not vacuous — some record's own `stated`
        # has to name the producer, which is what the second half asks.
        composed = any(
            "_staging_rows" in one.text.split("def stated(", 1)[-1].split("\n    def ", 1)[0]
            for one in modules()
            if "def stated(" in one.text
        )
        if ".stated(" in body and composed:
            continue
        missing.append(handler)
    assert not missing, missing
