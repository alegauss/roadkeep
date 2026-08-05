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

import re
import shlex
from pathlib import Path

import pytest

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
    assert set(workflow["jobs"]) == {"lint", "tests", "payload"}


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
