"""Did this change make it worse — the only question an absolute count cannot answer (RK84).

A project adopting this tool arrives with history. One live corpus lints at 317 problems,
none of them the current change's, and the number moves by one or two per task: the gate
cannot be wired to its CI, and "did I add anything" has no command. It was answered by hand
— stash the three files, lint, unstash, lint again, compare — which is four commands, is not
something a hook can do, and once nearly hid a real defect behind a count that *fell*.

So `--baseline REV` runs the same gate over the governed files as they were at REV and
reports the difference. Three properties are what these tests are about:

* **Only the excess fails.** Standing debt is named and forgiven; the exit code is the
  difference alone, which is the shape a repository can adopt before it has paid off.
* **Debt is counted per line and per kind, never per position.** A finding that only moved
  down the file is the same finding, or the first task added at the top makes everything new.
* **What is subtracted is the three files, not the repository.** The configuration is the
  ruler, the code is where it is now — but a budget and a path claim are read at the
  revision, because both are findings a change makes by touching something else.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from conftest import git, git_init

from roadkeep.cli import EXIT_GATE, EXIT_OK, EXIT_USAGE, main
from roadkeep.config import Config
from roadkeep.history import HistoryUnavailable, git_available
from roadkeep import linting as linting_module
from roadkeep.linting import Tree, _spelled, lint
from roadkeep import showing as showing_module
from roadkeep.showing import show

pytestmark = pytest.mark.skipif(not git_available(), reason="git is not on PATH")

CONFIG = """prefix = "RK"
[files]
roadmap = "ROADMAP.md"
changelog = "CHANGELOG.md"
improvements = "IMPROVEMENTS.md"
"""

ROADMAP = """# Roadmap

## Block A — The model

- 📋 **RK1** (deps: —) **A first symptom** — Because of a reason. → §RK1
- 📋 **RK2** (deps: —) **A second symptom** — Because of another reason. → §RK2
"""

LEDGER = """# Shipped

## Block A — The model

- ✅ **RK5** **An earlier symptom** — Because it was done.
"""

#: §RK2 is deliberately absent: one `ref.unresolved` on RK2's line, and that finding is the
#: standing debt every test below is written against.
PROSE = """# Design rationale

## Block A — The model

### §RK1 The first design

The reasoning the first line has no room for.
"""




def write(root: Path, name: str, body: str) -> None:
    (root / name).parent.mkdir(parents=True, exist_ok=True)
    with (root / name).open("w", encoding="utf-8", newline="") as handle:
        handle.write(body)


def repo(
    tmp_path: Path, config: str = CONFIG, files: dict[str, str] | None = None
) -> Config:
    """A committed project carrying one standing problem, plus whatever a test adds."""
    git_init(tmp_path)
    write(tmp_path, "roadkeep.toml", config)
    write(tmp_path, "ROADMAP.md", ROADMAP)
    write(tmp_path, "CHANGELOG.md", LEDGER)
    write(tmp_path, "IMPROVEMENTS.md", PROSE)
    for name, body in (files or {}).items():
        write(tmp_path, name, body)
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "--quiet", "-m", "chore: bootstrap")
    return Config.discover(tmp_path)


def codes(report) -> list[str]:
    return [f"{f.code} {f.id}".strip() for f in report.findings]


# -- the debt, and the difference ---------------------------------------------


def test_the_debt_is_what_lint_reports_without_a_baseline(tmp_path):
    # The premise of every test below: this project is not clean, and plain `lint` says so.
    config = repo(tmp_path)
    assert codes(lint(config)) == ["ref.unresolved RK2"]


def test_a_problem_the_revision_already_had_is_forgiven(tmp_path):
    config = repo(tmp_path)
    report = lint(config, baseline="HEAD")
    assert report.clean and report.findings == ()
    assert report.baseline is not None
    assert report.baseline.standing == 1
    # Forgiven, not lost: the exit code is the difference and the debt is still named.
    assert [f.code for f in report.baseline.forgiven] == ["ref.unresolved"]


def test_a_problem_this_tree_added_is_the_whole_report(tmp_path):
    config = repo(tmp_path)
    write(tmp_path, "ROADMAP.md", ROADMAP + "- 📋 **RK3** (deps: —) **A third symptom** — Because of a third reason. → §RK3\n")
    report = lint(config, baseline="HEAD")
    assert codes(report) == ["ref.unresolved RK3"]
    assert report.baseline.standing == 1


def test_a_finding_that_only_moved_down_the_file_is_not_a_new_one(tmp_path):
    # The property the whole design turns on: an id is not a line number, and the first task
    # inserted above a standing problem would otherwise report the rest of the file as new.
    config = repo(tmp_path)
    write(tmp_path, "ROADMAP.md", ROADMAP.replace(
        "- 📋 **RK2**",
        "- 📋 **RK3** (deps: —) **A third symptom** — Because of a third reason. → §RK3\n"
        "- 📋 **RK2**",
    ))
    write(tmp_path, "IMPROVEMENTS.md", PROSE + "\n### §RK3 The third design\n\nThe reasoning it lacks.\n")
    report = lint(config, baseline="HEAD")
    assert report.clean, codes(report)
    assert report.baseline.forgiven[0].lineno == 7  # was 6, and is the same debt


def test_a_problem_that_left_is_reported_as_resolved(tmp_path):
    # The other direction, and it is here because a count that *fell* is what nearly hid a
    # real defect: eight went away on the run that deleted the rationale it should not have.
    config = repo(tmp_path)
    write(tmp_path, "IMPROVEMENTS.md", PROSE + "\n### §RK2 The second design\n\nThe reasoning the second line has no room for.\n")
    report = lint(config, baseline="HEAD")
    assert report.clean
    assert report.baseline.standing == 0
    assert [f.code for f in report.baseline.resolved] == ["ref.unresolved"]


def test_a_second_finding_of_a_kind_already_standing_is_still_new(tmp_path):
    # Debt is counted, not matched by kind alone: one unresolved pointer already there does
    # not buy the second one, because what a line owes is read per line.
    config = repo(tmp_path)
    write(tmp_path, "IMPROVEMENTS.md", "# Design rationale\n\n## Block A — The model\n")
    report = lint(config, baseline="HEAD")
    assert codes(report) == ["ref.unresolved RK1"]


# -- what a baseline holds constant, and what it does not ---------------------


def test_a_governed_file_deleted_since_the_revision_is_not_inherited(tmp_path):
    # `file.missing` is asked of the tree and not of disk: absent in both runs would forgive
    # the deletion of the file the whole format is about.
    config = repo(tmp_path)
    (tmp_path / "ROADMAP.md").unlink()
    report = lint(config, baseline="HEAD")
    # And §RK1 with it: a section whose line is gone is nobody's rationale, which is the
    # second thing this change did and the second thing it is charged for.
    assert codes(report) == ["section.orphan RK1", "file.missing"]


def test_a_budget_this_change_broke_is_new_debt(tmp_path):
    # RK30's finding is about a file this tool never writes, so both runs would otherwise
    # measure the same bytes — and an `agents.md` pushed over by this commit is exactly the
    # cost a baseline exists to charge.
    config = repo(
        tmp_path,
        config=CONFIG + '[budgets]\n"agents.md" = { lines = 3 }\n',
        files={"agents.md": "one\ntwo\n"},
    )
    write(tmp_path, "agents.md", "one\ntwo\nthree\nfour\n")
    report = lint(config, baseline="HEAD")
    assert codes(report) == ["budget.lines"]


def test_a_budget_already_broken_stays_forgiven_while_it_is_one_finding(tmp_path):
    # The honest edge of counting by kind: an overrun that merely grew is the same finding,
    # so it is standing debt until it is paid off. `lint` without a baseline still fails it.
    config = repo(
        tmp_path,
        config=CONFIG + '[budgets]\n"agents.md" = { lines = 3 }\n',
        files={"agents.md": "one\ntwo\nthree\nfour\n"},
    )
    write(tmp_path, "agents.md", "one\ntwo\nthree\nfour\nfive\n")
    report = lint(config, baseline="HEAD")
    assert report.clean
    assert "budget.lines" in [f.code for f in report.baseline.forgiven]
    assert "budget.lines" in codes(lint(config))


def test_an_artefact_deleted_since_the_revision_is_not_inherited_either(tmp_path):
    # The one finding whose subject is outside the governed files, so it is the one place a
    # baseline resolves against the revision: a rename the ledger did not follow is the true
    # finding this check produced on the corpus it was measured on, and it would be forgiven
    # by a run that asked the working tree twice.
    config = repo(tmp_path, files={"src/kept.py": "x = 1\n"})
    write(tmp_path, "CHANGELOG.md", LEDGER.replace(
        "Because it was done.", "Because it was done, in `src/kept.py`."
    ))
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "--quiet", "-m", "docs: name the file")
    (tmp_path / "src" / "kept.py").unlink()
    report = lint(config, baseline="HEAD")
    assert codes(report) == ["path.missing RK5"]


def test_a_path_relative_to_the_module_it_is_about_resolves(tmp_path):
    # RK173, measured adopting Turing: six of eight `path.missing` findings named artefacts
    # the repository has. A monorepo entry writes the path its reader is standing in — the
    # frontend app, the showcase skill — because that is what a developer pastes from a
    # terminal already inside it, and 2 in 8 is a ratio at which the class stops being read.
    config = repo(
        tmp_path,
        files={
            "frontend/apps/site/package.json": "{}\n",
            "frontend/apps/site/scripts/prerender.mjs": "//\n",
        },
    )
    write(tmp_path, "CHANGELOG.md", LEDGER.replace(
        "Because it was done.", "Because `./package.json` runs `scripts/prerender.mjs`."
    ))
    assert [f for f in lint(config).findings if f.code == "path.missing"] == []


def test_a_line_anchor_is_not_part_of_the_filename(tmp_path):
    # The separate, smaller and unambiguous half: `#L35` addresses a place inside a file,
    # which is how GitHub spells a citation and not how anything spells a name.
    config = repo(tmp_path, files={"src/kept.py": "x = 1\n"})
    write(tmp_path, "CHANGELOG.md", LEDGER.replace(
        "Because it was done.", "Because `src/kept.py#L35` says so."
    ))
    assert [f for f in lint(config).findings if f.code == "path.missing"] == []


def test_an_artefact_in_no_directory_of_the_repository_is_still_reported(tmp_path):
    # The other side, and the finding this check exists for: a rename inside a directory
    # matches no tail, so the one true row Shio's 61 findings came down to survives.
    config = repo(tmp_path, files={"src/main/java/Renamed.java": "//\n"})
    write(tmp_path, "CHANGELOG.md", LEDGER.replace(
        "Because it was done.", "Because `src/main/java/Original.java` does it."
    ))
    missing = next(f for f in lint(config).findings if f.code == "path.missing")
    assert missing.id == "RK5" and "Original.java" in missing.message


def test_a_path_the_revision_did_not_have_either_is_standing_debt(tmp_path):
    config = repo(tmp_path, files={"src/kept.py": "x = 1\n"})
    write(tmp_path, "CHANGELOG.md", LEDGER.replace(
        "Because it was done.", "Because it was done, in `src/gone.py`."
    ))
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "--quiet", "-m", "docs: name a file that is not there")
    write(tmp_path, "ROADMAP.md", ROADMAP.replace("a reason", "another reason"))
    report = lint(config, baseline="HEAD")
    assert report.clean
    assert "path.missing" in [f.code for f in report.baseline.forgiven]


#: A README whose block was derived from nothing. Stale at the revision, so a project that
#: adopts the gate with one already in it is the case the two tests below separate (RK104).
STALE_README = f"""# A project

<!-- roadkeep:begin -->
| Block | Open | Shipped |
| --- | --- | --- |
<!-- roadkeep:end -->
"""


def test_a_block_this_change_left_stale_is_new_debt(tmp_path):
    # The symptom RK104 names, at the one revision where it can be attributed: the block was
    # current, this commit shipped a task, and nothing re-derived it.
    config = repo(tmp_path, files={"README.md": STALE_README})
    assert main(["-C", str(tmp_path), "export", "--readme"]) == EXIT_OK
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "--quiet", "-m", "docs: derive the block")
    # The block is current at the revision, so the standing debt is the fixture's own one.
    assert codes(lint(config)) == ["ref.unresolved RK2"]
    write(tmp_path, "ROADMAP.md", ROADMAP.replace("- 📋 **RK2**", "- 🛠 **RK2**"))
    assert codes(lint(config, baseline="HEAD")) == ["export.stale"]


def test_a_block_that_was_already_stale_is_forgiven(tmp_path):
    # The other direction, and the reason the block is derived from the *tree's* documents: a
    # README stale before this change is standing debt, not something every commit after it
    # is charged for. Plain `lint` still fails it, which is what makes it debt and not silence.
    config = repo(tmp_path, files={"README.md": STALE_README})
    write(tmp_path, "ROADMAP.md", ROADMAP.replace("a reason", "another reason"))
    report = lint(config, baseline="HEAD")
    assert report.clean
    assert "export.stale" in [f.code for f in report.baseline.forgiven]
    assert "export.stale" in codes(lint(config))


def test_the_configuration_is_the_ruler_and_not_the_thing_measured(tmp_path):
    # Both runs are held to the config as it is now, so a limit lowered in this change makes
    # the lines it now refuses *standing debt* and not new work. Deliberate, and the reason
    # is one file up: `roadkeep.toml` declares which files are governed and where they are
    # (L6), so two runs under two configs would not be comparing the same documents at all.
    repo(tmp_path)
    write(tmp_path, "roadkeep.toml", CONFIG + "[limits]\nwhy = 20\n")
    config = Config.discover(tmp_path)
    report = lint(config, baseline="HEAD")
    assert report.clean
    assert "why.too-long" in [f.code for f in report.baseline.forgiven]
    # Which is only bearable because the absolute gate is still there and still fails.
    assert "why.too-long" in [f.code for f in lint(config).findings]


# -- the contract -------------------------------------------------------------


def test_the_exit_code_is_the_difference(tmp_path, capsys):
    repo(tmp_path)
    assert main(["-C", str(tmp_path), "lint", "--baseline", "HEAD"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "clean against HEAD (1 standing)" in out
    # And the same tree, judged absolutely, is still failing: the debt was forgiven, not
    # declared paid.
    assert main(["-C", str(tmp_path), "lint"]) == EXIT_GATE


def test_the_summary_says_new_and_names_what_was_forgiven(tmp_path, capsys):
    repo(tmp_path)
    write(tmp_path, "ROADMAP.md", ROADMAP + "- 📋 **RK3** (deps: —) **A third symptom** — Because of a third reason. → §RK3\n")
    assert main(["-C", str(tmp_path), "lint", "--baseline", "HEAD"]) == EXIT_GATE
    out = capsys.readouterr().out
    assert "1 new problem(s)" in out and "against HEAD (1 standing)" in out
    # The 317 the corpus already has are not printed one by one: the point of the flag is
    # that the report is the size of the change.
    assert out.count("ref.unresolved") == 2  # the finding's own line, and the code summary


def test_a_revision_that_is_not_one_is_a_usage_error(tmp_path, capsys):
    # Louder than `--since`, which degrades to silence: here the revision *is* the answer,
    # and a run that could not read its baseline would report the whole debt as new.
    repo(tmp_path)
    assert main(["-C", str(tmp_path), "lint", "--baseline", "no-such-rev"]) == EXIT_USAGE
    assert "no history to resolve against" in capsys.readouterr().err


def test_json_separates_the_difference_from_the_debt(tmp_path, capsys):
    repo(tmp_path)
    write(tmp_path, "ROADMAP.md", ROADMAP + "- 📋 **RK3** (deps: —) **A third symptom** — Because of a third reason. → §RK3\n")
    assert main(["-C", str(tmp_path), "lint", "--baseline", "HEAD", "--json"]) == EXIT_GATE
    payload = json.loads(capsys.readouterr().out)
    assert payload["problems"] == 1 and payload["clean"] is False
    assert payload["baseline"]["rev"] == "HEAD"
    assert payload["baseline"]["standing"] == 1
    assert [f["id"] for f in payload["baseline"]["forgiven"]] == ["RK2"]
    assert [f["id"] for f in payload["findings"]] == ["RK3"]


def test_without_the_flag_nothing_is_compared(tmp_path, capsys):
    # `lint` has to keep answering "is this file correct" — the gate three surfaces call.
    repo(tmp_path)
    assert main(["-C", str(tmp_path), "lint", "--json"]) == EXIT_GATE
    assert "baseline" not in json.loads(capsys.readouterr().out)
# -- the whole gate over a revision (RK210) -----------------------------------


def test_at_a_revision_moves_both_ends_of_every_check(tmp_path):
    """`baseline` already ran the gate over a revision to subtract it; `at` is that read
    given a name, so a caller can make it alone.

    The property that matters is that it moves *both* ends: the governed files come from
    the blob and the tree the path check asks about is the checkout as that commit left it.
    A run that pinned one and not the other is the shape RK192 removed from the corpus
    fixture and RK210 found the other half of.
    """
    config = repo(tmp_path, files={"src/kept.py": "x = 1\n"})
    write(tmp_path, "CHANGELOG.md", LEDGER.replace(
        "Because it was done.", "Because it was done, in `src/kept.py`."
    ))
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "--quiet", "-m", "docs: name the file")

    # Now both ends move: the artefact goes and the ledger stops naming it.
    (tmp_path / "src" / "kept.py").unlink()
    write(tmp_path, "CHANGELOG.md", LEDGER)
    assert "path.missing" not in codes(lint(config))
    # At the revision, the ledger names it and the tree had it — so still nothing.
    assert "path.missing" not in codes(lint(config, at="HEAD"))
    # And the working tree read against the revision's ledger is the finding, which is what
    # says the two ends really did move together rather than one of them.
    assert codes(lint(config, baseline="HEAD")) == []


def test_a_revision_the_repository_does_not_know_is_refused(tmp_path):
    # `baseline`'s reason (RK84), applied to the same read: a run that could not open the
    # revision it names would answer about this afternoon under that name.
    config = repo(tmp_path)
    with pytest.raises(HistoryUnavailable):
        lint(config, at="not-a-revision")


# -- a path the repository declared it will never track (RK213) ---------------


def naming(path: str) -> str:
    return LEDGER.replace("Because it was done.", f"Because it was done, in `{path}`.")


def project(tmp_path: Path) -> Config:
    """The same files with no repository around them, for the fallback case."""
    write(tmp_path, "roadkeep.toml", CONFIG)
    write(tmp_path, "ROADMAP.md", ROADMAP)
    write(tmp_path, "CHANGELOG.md", LEDGER)
    write(tmp_path, "IMPROVEMENTS.md", PROSE)
    return Config.discover(tmp_path)


def paths(report) -> list[str]:
    """Only this check's findings: the fixture carries one standing problem of its own."""
    return [c for c in codes(report) if c.startswith("path.missing")]


def test_a_path_the_repository_ignores_is_not_a_missing_artefact(tmp_path):
    """The state an adopter's CI was red in, and the machine's own state decided it.

    Reproduced against Claude Code Tray at the commit before it edited the sentence: a
    bare checkout is clean, a built tree is clean, and the tree with the directory and no
    file is one finding. So the gate answered by whichever of three states a machine
    happened to be in — which is not a defect in the ledger's sentence.
    """
    config = repo(tmp_path, files={".gitignore": "bin/\n"})
    (tmp_path / "bin" / "Release").mkdir(parents=True)
    write(tmp_path, "CHANGELOG.md", naming("bin/Release/app.exe"))
    assert "path.missing" not in codes(lint(config))


def test_the_three_states_the_machine_can_be_in_now_answer_alike(tmp_path):
    """What the fix is *for*: one answer, whatever the developer last ran.

    Bare was already silent (RK55 withholds a claim whose directory is absent) and built was
    already silent, so the whole defect was the third — and the value of the fix is that all
    three agree rather than that any one of them changed.
    """
    config = repo(tmp_path, files={".gitignore": "bin/\n"})
    write(tmp_path, "CHANGELOG.md", naming("bin/Release/app.exe"))
    answers = []
    for state in ("bare", "directory", "built"):
        shutil.rmtree(tmp_path / "bin", ignore_errors=True)
        if state != "bare":
            (tmp_path / "bin" / "Release").mkdir(parents=True)
        if state == "built":
            write(tmp_path, "bin/Release/app.exe", "")
        answers.append(paths(lint(config)))
    assert answers == [[], [], []]


def test_a_path_nothing_ignores_is_still_the_finding_this_check_exists_for(tmp_path):
    """The one true finding the widening may not swallow: a rename the ledger did not
    follow, under a directory the repository tracks."""
    config = repo(tmp_path, files={".gitignore": "bin/\n", "src/kept.py": "x = 1\n"})
    write(tmp_path, "CHANGELOG.md", naming("src/renamed.py"))
    assert paths(lint(config)) == ["path.missing RK5"]


def test_the_declaration_is_the_project_s_and_not_a_table_in_this_tool(tmp_path):
    """L6, and the case a list of conventional directory names gets wrong: a project that
    tracks its `dist/` on purpose has said so, and the gate reads what it said."""
    config = repo(tmp_path, files={".gitignore": "bin/\n", "dist/app.js": "x\n"})
    (tmp_path / "dist").mkdir(exist_ok=True)
    write(tmp_path, "CHANGELOG.md", naming("dist/missing.js"))
    assert paths(lint(config)) == ["path.missing RK5"]


def test_a_repository_that_ignores_nothing_is_unchanged(tmp_path):
    config = repo(tmp_path, files={"src/kept.py": "x = 1\n"})
    write(tmp_path, "CHANGELOG.md", naming("src/gone.py"))
    assert paths(lint(config)) == ["path.missing RK5"]


def test_both_spellings_of_a_token_are_asked_about(tmp_path):
    """A token resolves against the ledger's own directory as well as the root (RK51), so
    the ignored one may be either — and the answer has to come back keyed to the token."""
    config = repo(
        tmp_path,
        config=CONFIG.replace('changelog = "CHANGELOG.md"', 'changelog = "docs/CHANGELOG.md"'),
        files={".gitignore": "docs/build/\n", "docs/CHANGELOG.md": LEDGER},
    )
    (tmp_path / "docs" / "build").mkdir(parents=True)
    write(tmp_path, "docs/CHANGELOG.md", naming("build/out.js"))
    assert "path.missing" not in codes(lint(config))


def test_one_escaping_path_does_not_take_the_whole_batch_with_it(tmp_path):
    """RK220: git refuses the whole `check-ignore` invocation over a single path outside
    the repository, and that refusal arrives through the same door as "there is no git" —
    where RK213 withholds nothing. So one `../` in a ledger silently returned the gate to
    its pre-RK213 behaviour for every other path in the file.

    Found by RK217's own measurement, on Shio, whose ledger writes `../package.json`
    because its governed files live under `docs/` — the RK51 convention this check exists
    to accommodate.
    """
    config = repo(
        tmp_path,
        config=CONFIG.replace('changelog = "CHANGELOG.md"', 'changelog = "docs/CHANGELOG.md"'),
        files={".gitignore": "bin/\n", "docs/CHANGELOG.md": LEDGER},
    )
    (tmp_path / "bin" / "out").mkdir(parents=True)
    write(
        tmp_path,
        "docs/CHANGELOG.md",
        LEDGER.replace(
            "Because it was done.",
            "Because it was done, in `bin/out/app.exe` and `../outside.txt`.",
        ),
    )
    reported = paths(lint(config))
    # The ignored one is still withheld, and the escaping one is still reported: a path
    # above the root is not something this repository declared either way.
    assert reported == ["path.missing RK5"]
    assert "bin/out/app.exe" not in " ".join(
        f.message for f in lint(config).findings
    )


# -- a claim is about the repository, not about this disk (RK217) -------------


def test_deleting_the_directory_reports_what_deleting_the_file_reported(tmp_path):
    """The defect, and the shape of it: the larger deletion was the silent one.

    RK55 asked the **filesystem** whether the token's directory was there, so a ledger
    naming `lib/gone.py` reported when that one file went and reported nothing when `lib/`
    went with it. Measured before the change over both pins — 7246 distinct tokens, the
    two rules disagreeing on none — so what RK55 closed stays closed.
    """
    config = repo(tmp_path, files={"lib/gone.py": "x = 1\n"})
    write(tmp_path, "CHANGELOG.md", naming("lib/gone.py"))
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "--quiet", "-m", "docs: name the file")
    assert paths(lint(config)) == []

    (tmp_path / "lib" / "gone.py").unlink()
    assert paths(lint(config)) == ["path.missing RK5"]
    shutil.rmtree(tmp_path / "lib")
    assert paths(lint(config)) == ["path.missing RK5"]


def test_a_token_under_no_directory_the_repository_knows_is_still_not_a_claim(tmp_path):
    """What RK55 closed, and what a tracked-prefix test has to keep closed: 60 of Shio's 61
    findings were a MIME type, an i18n key or two method names sharing a slash. None of
    their heads is a directory anything tracks."""
    config = repo(tmp_path, files={"src/kept.py": "x = 1\n"})
    write(tmp_path, "CHANGELOG.md", naming("application/json"))
    assert paths(lint(config)) == []
    write(tmp_path, "CHANGELOG.md", naming("common/errors.not_found"))
    assert paths(lint(config)) == []


def test_a_directory_on_disk_that_nothing_tracks_is_not_the_repository_s(tmp_path):
    """The other direction, and the one that made the answer per machine: an untracked
    directory somebody happens to have is not evidence about this repository."""
    config = repo(tmp_path, files={"src/kept.py": "x = 1\n"})
    (tmp_path / "scratch").mkdir()
    write(tmp_path, "CHANGELOG.md", naming("scratch/notes.md"))
    assert paths(lint(config)) == []


def test_a_checkout_with_no_history_keeps_the_filesystem_answer(tmp_path):
    """An absent answer is not a negative one (RK95). A tree git cannot list tracks nothing
    and declares nothing, so reading its silence as "no directory here is the repository's"
    would drop every path claim in the file rather than decide any of them."""
    config = project(tmp_path)  # no `git init`
    (tmp_path / "docs" / "specs").mkdir(parents=True)
    write(tmp_path, "CHANGELOG.md", naming("docs/specs/absent.md"))
    assert paths(lint(config)) == ["path.missing RK5"]


def test_a_revision_is_judged_without_asking_this_disk_about_a_path(tmp_path):
    """RK218: half the resolution moved to the revision and half did not.

    `carries` and `anywhere` asked git at the ref while `referenced.exists` still asked
    this disk, so a file created since the ref — untracked, never committed, invisible to
    git — silenced a finding the revision genuinely had. The same commit, two verdicts,
    decided by somebody's scratch file.
    """
    config = repo(tmp_path, files={"lib/kept.py": "x = 1\n"})
    write(tmp_path, "CHANGELOG.md", naming("lib/later.py"))
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "--quiet", "-m", "docs: name a file that is not there yet")
    assert paths(lint(config, at="HEAD")) == ["path.missing RK5"]

    write(tmp_path, "lib/later.py", "z = 3\n")  # untracked: git has never seen it
    assert paths(lint(config, at="HEAD")) == ["path.missing RK5"]
    # And the working tree run does still read the working tree, which is its subject.
    assert paths(lint(config)) == []


def test_the_revision_s_own_debt_is_seen_even_where_this_tree_has_the_file(tmp_path):
    """Why it bites `--baseline` (RK84) rather than `--at`: the debt is computed from the
    revision, and a revision half-read simply did not have the finding to compare against.

    With both ends at the ref the revision's debt is visible, so creating the file here
    reads as **resolved** — this tree fixed something — rather than as a revision that was
    always clean. Two different sentences about the same pair of trees, and only one of
    them is true."""
    config = repo(tmp_path, files={"lib/kept.py": "x = 1\n"})
    write(tmp_path, "CHANGELOG.md", naming("lib/later.py"))
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "--quiet", "-m", "docs: name a file that is not there yet")
    write(tmp_path, "lib/later.py", "z = 3\n")
    report = lint(config, baseline="HEAD")
    # Standing debt, named and forgiven — not a finding this working tree added.
    assert paths(report) == []
    assert "path.missing" in [f.code for f in report.baseline.resolved]


def test_a_directory_the_revision_tracked_is_held_by_it_too(tmp_path):
    """The regression the first attempt caused, and why `holds` asks git both shapes.

    Skipping the disk at a revision is only half the move: a token can name a *directory*,
    and `carries` compares against a listing of files, so `docs`, `create-shio-app` and
    thirty-three more across the two pins turned into findings the moment the disk stopped
    answering for them. They were never on the strength of the repository — only of
    somebody's checkout.
    """
    config = repo(tmp_path, files={"lib/kept.py": "x = 1\n"})
    write(tmp_path, "CHANGELOG.md", naming("lib"))
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "--quiet", "-m", "docs: name the directory")
    shutil.rmtree(tmp_path / "lib")  # the disk cannot answer; the revision still can
    assert paths(lint(config, at="HEAD")) == []


def test_a_token_that_is_only_separators_names_no_artefact(tmp_path):
    """Unmasked by RK218 rather than caused by it: two of Turing's entries quote a bare
    backslash as a character, and on Windows that *resolves* — to the drive root — so it
    read as a path the repository has for as long as the disk was the reader. What a token
    resolves to may not depend on the platform running the gate."""
    config = repo(tmp_path, files={"lib/kept.py": "x = 1\n"})
    write(tmp_path, "CHANGELOG.md", naming("\\"))
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "--quiet", "-m", "docs: quote a backslash")
    assert paths(lint(config)) == []
    assert paths(lint(config, at="HEAD")) == []


def test_the_ignore_answer_is_keyed_by_the_token_it_is_about(tmp_path):
    """RK219: the cache used to store the first call's answer and return it for every
    later one, which was correct only because `_paths` asks once — a fact no reader of
    that method could see. Keyed by the token, a second question gets a second answer.
    """
    config = repo(tmp_path, files={".gitignore": "bin/\n", "src/kept.py": "x = 1\n"})
    tree = Tree(config)
    near = tmp_path
    assert tree.declared_untracked([("bin/app.exe", near)]) == frozenset({"bin/app.exe"})
    # A different question, asked second: it used to come back with the first one's answer.
    assert tree.declared_untracked([("src/gone.py", near)]) == frozenset()
    # And the first one is still remembered rather than asked again.
    assert tree.declared_untracked(
        [("bin/app.exe", near), ("src/gone.py", near)]
    ) == frozenset({"bin/app.exe"})


def test_a_repeated_question_costs_no_second_subprocess(tmp_path):
    """The property that makes keying it free: every token asked is recorded either way,
    so the batch a caller arrives with shrinks to what is genuinely new."""
    config = repo(tmp_path, files={".gitignore": "bin/\n"})
    tree = Tree(config)
    near = tmp_path
    calls: list[int] = []
    real = linting_module.check_ignore

    def counted(root, paths):
        calls.append(len(paths))
        return real(root, paths)

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(linting_module, "check_ignore", counted)
        tree.declared_untracked([("bin/a.exe", near), ("src/b.py", near)])
        tree.declared_untracked([("bin/a.exe", near), ("src/b.py", near)])
        tree.declared_untracked([("bin/c.exe", near)])
    assert len(calls) == 2  # the repeat asked nothing; the new token asked once


def test_the_reader_and_the_gate_agree_about_a_deleted_artefact(tmp_path):
    """RK221: two readers of one rule, and the reader was the wrong one.

    RK217 established that a claim is decided against the **index** rather than the working
    tree, because `tracked_now` subtracts what git calls deleted — right for "does the tree
    still have this artefact" and exactly wrong for "is this a directory the repository
    knows". `Tree.directories` got that; `show` fell through to the default and did not, so
    `lint` reported `path.missing` while `show` said the task named no path at all.

    RK186 already named which half is worse to leave wrong: `lint` is the backstop and is
    read once, while `show` and `brief` are what start a task.
    """
    config = repo(tmp_path, files={"lib/gone.py": "x = 1\n"})
    write(tmp_path, "CHANGELOG.md", naming("lib/gone.py"))
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "--quiet", "-m", "docs: name the file")
    assert [(r.path, r.exists) for r in show(config, "RK5").paths] == [("lib/gone.py", True)]
    assert paths(lint(config)) == []

    (tmp_path / "lib" / "gone.py").unlink()
    assert [(r.path, r.exists) for r in show(config, "RK5").paths] == [("lib/gone.py", False)]
    assert paths(lint(config)) == ["path.missing RK5"]

    shutil.rmtree(tmp_path / "lib")
    assert [(r.path, r.exists) for r in show(config, "RK5").paths] == [("lib/gone.py", False)]
    assert paths(lint(config)) == ["path.missing RK5"]


def test_a_task_whose_paths_all_resolve_asks_git_nothing(tmp_path):
    """RK222: the directory listing is bought only where the question is actually asked.

    RK217 needed it to decide whether a token is a claim, and it is needed only for a token
    that **fails** `exists` — which on a healthy repository is none of them. Computing it up
    front took `show` from 1.1 ms to 36.6 ms here and 4.2 ms to 73.4 ms on Turing, on the
    read `brief` makes to start every task.
    """
    config = repo(tmp_path, files={"lib/kept.py": "x = 1\n"})
    write(tmp_path, "CHANGELOG.md", naming("lib/kept.py"))
    calls: list[str] = []
    real = showing_module.indexed

    def counted(cfg):
        calls.append("indexed")
        return real(cfg)

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(showing_module, "indexed", counted)
        view = show(config, "RK5")
    assert [(r.path, r.exists) for r in view.paths] == [("lib/kept.py", True)]
    assert calls == []


def test_a_task_naming_something_absent_still_gets_the_answer(tmp_path):
    """The other half: lazy is not absent. A token that fails `exists` is exactly the one
    the listing was for, and it is bought then."""
    config = repo(tmp_path, files={"lib/kept.py": "x = 1\n"})
    write(tmp_path, "CHANGELOG.md", naming("lib/gone.py"))
    view = show(config, "RK5")
    assert [(r.path, r.exists) for r in view.paths] == [("lib/gone.py", False)]


def test_every_ledger_entry_is_read_once(tmp_path):
    """RK223: the gate is what a pre-commit hook waits for (RK17), so a pass it makes twice
    is a pass somebody starts passing `--no-verify` to.

    RK213 has to gather every candidate before asking `.gitignore`, because one call for
    all of them is what keeps that question cheap — and gathering them with a comprehension
    of its own made the findings comprehension repeat the whole scan. Measured at Turing's
    pin: `paths_in` entered 1602 times for 801 entries, and `_paths` cost 2.9 s; one pass
    is 559 ms, so the repetition was most of it rather than half.
    """
    config = repo(tmp_path, files={"lib/kept.py": "x = 1\n"})
    write(tmp_path, "CHANGELOG.md", naming("lib/gone.py"))
    entries = len(config.document("changelog").entries)
    assert entries
    seen: list[str] = []
    real = linting_module.paths_in

    def counted(text, root, **kwargs):
        seen.append(text)
        return real(text, root, **kwargs)

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(linting_module, "paths_in", counted)
        assert paths(lint(config)) == ["path.missing RK5"]
    assert len(seen) == entries


def test_a_revision_run_touches_the_filesystem_for_no_path(tmp_path):
    """RK225: `exists` was computed before anything asked which tree was being judged.

    RK218 established that a run naming a revision does not *read* the disk, and `paths_in`
    went on computing the read anyway — 34070 `stat` calls at Turing's pin, all discarded.
    Worse, `exists` also decides **candidacy**, so the candidate set stayed half decided by
    this afternoon while the findings were about a commit.
    """
    config = repo(tmp_path, files={"lib/kept.py": "x = 1\n"})
    write(tmp_path, "CHANGELOG.md", naming("lib/later.py"))
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "--quiet", "-m", "docs: name a file that is not there yet")

    touched: list[str] = []
    real = linting_module.on_disk

    def counted(token, root, near):
        touched.append(token)
        return real(token, root, near)

    # `Tree.holds` is the one door to the disk once `has` is supplied, so this is the
    # module that has to be watched rather than the one the function is defined in.
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(linting_module, "on_disk", counted)
        assert paths(lint(config, at="HEAD")) == ["path.missing RK5"]
    assert touched == []
    # And the working tree run still reads the working tree, which is its subject.
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(linting_module, "on_disk", counted)
        lint(config)
    assert touched


def test_a_spelling_is_decided_without_asking_the_filesystem(tmp_path):
    """`Config.relative` resolves, which is right where a junction has to be followed and
    ruinous per token: the first attempt at RK225 took Turing's run from 559 ms to 11.5 s,
    of which 7.4 s was `realpath`. Every path compared against git's listing is built from
    the config's own root, so the prefix already agrees and `..` normalises textually."""
    config = repo(tmp_path, files={"docs/deep/kept.py": "x = 1\n"})
    # The root arrives already normalised, because it is the half that cannot vary (RK228).
    root = os.path.normpath(str(config.root))
    docs = str(tmp_path / "docs")
    assert _spelled(root, docs, "deep/kept.py") == "docs/deep/kept.py"
    assert _spelled(root, docs, "../top.md") == "top.md"
    # Above the root: git has nothing to say, and one of them refuses a batch (RK220).
    assert _spelled(root, str(tmp_path), "../outside.txt") is None
    # The root itself keeps the spelling `known_directories` holds it under (RK217).
    assert _spelled(root, docs, "..") == "."


def test_a_windows_spelling_and_a_posix_one_are_one_claim(tmp_path):
    r"""RK226: a backslash separates on Windows and is an ordinary filename character
    everywhere else, so both halves of this check answered by host.

    `docs\specs\x.md` resolved for the author who pasted it from a terminal and was a
    single unheard-of name in CI, where git's listing has only ever held forward slashes —
    RK213's shape ("green for whoever ran it, red where it runs") through another door.
    """
    config = repo(tmp_path, files={"docs/specs/kept.md": "x\n"})
    for spelling in ("docs/specs/kept.md", r"docs\specs\kept.md"):
        write(tmp_path, "CHANGELOG.md", naming(spelling))
        assert paths(lint(config)) == [], spelling
        assert [r.path for r in show(config, "RK5").paths] == ["docs/specs/kept.md"], spelling


def test_the_normalised_spelling_is_what_a_finding_names(tmp_path):
    """One token throughout: the same string is asked of the disk, spelled for git, keyed
    in the ignore answer and printed. Toward the repository's own spelling, because that is
    the one every platform's git agrees on."""
    config = repo(tmp_path, files={"docs/specs/kept.md": "x\n"})
    write(tmp_path, "CHANGELOG.md", naming(r"docs\specs\gone.md"))
    finding = next(f for f in lint(config).findings if f.code == "path.missing")
    assert "docs/specs/gone.md" in finding.message


def test_a_drive_relative_spelling_is_still_a_claim_about_one_machine(tmp_path):
    """Normalising does not admit what was refused: `\foo` becomes `/foo`, which is the
    absolute path this check has always dropped — wrong on every other machine."""
    config = repo(tmp_path, files={"docs/specs/kept.md": "x\n"})
    write(tmp_path, "CHANGELOG.md", naming(r"\etc\passwd"))
    assert paths(lint(config)) == []


def test_a_token_is_spelled_once_per_base_and_not_once_per_question(tmp_path):
    """RK228: `holds` asked `carries`, which spelled the token, and then spelled it again
    for the directory set — two answers to one question, and the profile's largest row was
    the second one. One spelling per base, computed once and passed down."""
    config = repo(tmp_path, files={"lib/kept.py": "x = 1\n"})
    write(tmp_path, "CHANGELOG.md", naming("lib/gone.py"))
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "--quiet", "-m", "docs: name a file that is not there")
    tree = Tree(config, rev="HEAD")
    tree.directories()
    spelled: list[str] = []
    real = linting_module._spelled

    def counted(root, base, token):
        spelled.append(token)
        return real(root, base, token)

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(linting_module, "_spelled", counted)
        assert tree.holds("lib/gone.py", tmp_path) is False
    # Two bases, one spelling each — never four for the two questions `holds` asks.
    assert len(spelled) == 2


# -- a path that left the repository, not the working tree (RK1217) ------------


def test_a_path_the_repository_had_and_committed_away_is_history_and_not_drift(tmp_path):
    """Turing's `T759` names a script that existed when the work shipped and was later
    extracted into its own repository with the model catalog it built. The entry is accurate,
    the file is gone, and the gate reported it every run and would have kept reporting it.

    A shipped sentence is a claim about the tree that shipped it. What made it worse than
    noise was the door: the remedy rewrites the entry's sentence, which on that entry is about
    1,500 characters of as-built record — so the offered fix for a stale path was deleting the
    thing that made the entry worth keeping, nobody took it, and the finding sat forgiven by a
    baseline for ever.
    """
    config = repo(tmp_path, files={"lib/gone.py": "x = 1\n"})
    write(tmp_path, "CHANGELOG.md", naming("lib/gone.py"))
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "--quiet", "-m", "docs: name the file")
    assert paths(lint(config)) == []

    # Extracted elsewhere: removed **and committed**, which is what leaving the repository is.
    (tmp_path / "lib" / "gone.py").unlink()
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "--quiet", "-m", "chore: it moved to its own repository")
    assert paths(lint(config)) == []


def test_a_deletion_nobody_committed_is_still_the_repositorys(tmp_path):
    """The narrowing that keeps this from swallowing the rule. A file removed from a working
    tree and not committed is still in `HEAD` — forgiving that would stop the gate reporting a
    deletion at exactly the moment it is worth reporting, which is before it lands."""
    config = repo(tmp_path, files={"lib/gone.py": "x = 1\n"})
    write(tmp_path, "CHANGELOG.md", naming("lib/gone.py"))
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "--quiet", "-m", "docs: name the file")

    (tmp_path / "lib" / "gone.py").unlink()
    assert paths(lint(config)) == ["path.missing RK5"]


def test_a_path_this_repository_never_had_is_still_the_finding(tmp_path):
    """What the rule is for, and what survives the narrowing. RK1217 knowingly stops catching
    a rename the ledger did not follow — the old path was held once — because the alternative
    is a correct statement about the past reported for ever."""
    config = repo(tmp_path, files={"lib/kept.py": "x = 1\n"})
    write(tmp_path, "CHANGELOG.md", naming("lib/never-was.py"))
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "--quiet", "-m", "docs: name a file that never existed")
    assert paths(lint(config)) == ["path.missing RK5"]


def test_a_healthy_repository_asks_history_nothing(tmp_path, monkeypatch):
    """The cost, bounded where it is paid. Every other reading answers first — `exists`,
    `anywhere`, `check-ignore` — so a repository whose ledger resolves never reaches this."""
    from roadkeep import history

    config = repo(tmp_path, files={"lib/kept.py": "x = 1\n"})
    write(tmp_path, "CHANGELOG.md", naming("lib/kept.py"))
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "--quiet", "-m", "docs: name the file")

    asked: list[str] = []
    real = history.left_the_repository
    monkeypatch.setattr(
        history, "left_the_repository", lambda root, token: asked.append(token) or real(root, token)
    )
    assert paths(lint(config)) == []
    assert asked == []
