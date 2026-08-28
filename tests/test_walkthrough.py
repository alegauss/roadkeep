"""The adoption walkthrough, executed rather than believed (RK1406).

Output pasted into prose is fiction with a shelf life. The page an adopter follows is generated
from `scripts/walkthrough.py`, which builds a throwaway repository with a genuinely drifted
roadmap in it and runs the adoption against it — so a refusal whose wording changed fails a
build instead of misleading somebody halfway through.

This file **runs that script**, which is the half the site build cannot be trusted to do alone:
a build only runs where somebody pushes, and the failure this guards against is a message that
changed in the same commit as the code that prints it.

What it holds is the shape of the run rather than the exact English, because the English is the
thing that is allowed to change: how many refusals there are, that the tree it measured was the
throwaway one and never this repository, that no absolute path reached the output, and that the
run ends where the friction actually is — the first ordinary session, not the install.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent.parent
SCRIPT = HERE / "scripts" / "walkthrough.py"
PAGE = HERE / "site" / "docs" / "src" / "content" / "docs" / "adopting.mdx"
COMPONENT = HERE / "site" / "docs" / "src" / "components" / "Walkthrough.astro"
GENERATOR = HERE / "site" / "docs" / "scripts" / "walkthrough.mjs"


@pytest.fixture(scope="module")
def steps() -> list[dict]:
    """The run itself. Once per module: it builds a repository and executes a dozen commands."""
    # The whole environment, plus the path to the package. The script narrows it itself, and
    # handing it a bare dictionary here starved it of `PATH` — so `lint --baseline` could not
    # find git and reported no history, which is a green build producing a page that teaches a
    # baseline does not work. The suite runs it the way a build does or it proves nothing.
    import os

    found = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=HERE,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, "PYTHONPATH": str(HERE / "src"), "PYTHONIOENCODING": "utf-8"},
    )
    assert found.returncode == 0, found.stderr
    return json.loads(found.stdout)


def test_the_walkthrough_runs_and_produces_steps(steps):
    assert len(steps) >= 10


def test_it_ends_with_the_first_ordinary_session_and_not_the_install(steps):
    """The friction adopters report is rarely the install. It is the first write they made by
    hand out of habit, and the denial they then had to interpret — so a walkthrough that
    stopped at a green `lint` would stop before the part that decides anything."""
    commands = [step["command"] for step in steps if step["command"]]
    assert any(one.startswith("roadkeep add ") for one in commands)
    assert any(one.startswith("roadkeep ship ") for one in commands)
    # And the write path actually worked, rather than being shown refusing throughout.
    shipped = next(one for one in steps if one["command"].startswith("roadkeep ship "))
    assert shipped["exit_code"] == 0, shipped["stderr"]


def test_the_refusals_are_present_because_they_are_the_point(steps):
    """Being refused on a file that has always been there is where an adoption stops, and what
    the refusal says is the whole difference. A run where nothing was refused would demonstrate
    a path nobody is on."""
    refused = [step for step in steps if step["exit_code"] == 2]
    assert len(refused) >= 2
    # Each one names what to do instead, which is this tool's contract for a refusal and the
    # only reason showing one is useful rather than discouraging.
    for step in refused:
        assert re.search(r"roadkeep [a-z-]+|`[a-z-]+ ", step["stderr"]), step["command"]


def test_the_gate_reports_the_rule_before_it_reports_the_lines(steps):
    """A file where no bullet parses is not one somebody hand-edited — it is one written under
    another format, and saying so is what turns a wall of findings into one decision."""
    first_lint = next(one for one in steps if one["command"] == "roadkeep lint")
    assert "grammar.unreadable" in first_lint["stdout"]


def test_the_baseline_forgives_the_standing_debt_by_name(steps):
    """The answer to a repository with years of lines that were never written against these
    rules. Without it the gate cannot go into CI until after a cleanup nobody has time for."""
    baseline = next(
        one for one in steps if one["command"].startswith("roadkeep lint --baseline")
    )
    assert baseline["exit_code"] == 0, baseline["stdout"] or baseline["stderr"]
    assert "standing" in baseline["stdout"]


# -- what must never reach the page -------------------------------------------


def test_no_absolute_path_reaches_the_output(steps):
    """The run happens in a `tempfile` directory under whoever built the site, so an
    unredacted path publishes a username and makes every build differ from the last for a
    reason that is not about the tool."""
    for step in steps:
        blob = step["stdout"] + step["stderr"] + json.dumps(step["wrote"])
        assert not re.search(r"[A-Za-z]:\\|/(home|Users)/", blob), step["command"]


def test_the_run_measured_the_sample_and_never_this_repository(steps):
    """Three silent routes end with a probe answering about the project it was launched from,
    and the answer looks exactly like a correct one. What proves it did not: the ids are the
    sample's, and this repository's prefix appears nowhere."""
    blob = "\n".join(step["stdout"] + step["stderr"] for step in steps)
    assert "PROJ1" in blob
    assert not re.search(r"\bRK\d{3,}\b", blob)


def test_the_script_writes_nothing_outside_its_temporary_directory(steps):
    """It runs in the suite and in a build, so a stray file would land in somebody's checkout.
    Asserted against the tree rather than argued: the run has already happened by now."""
    del steps
    assert not list(HERE.glob("roadkeep-walkthrough-*"))
    assert not list((HERE / "docs").glob("roadkeep-walkthrough-*"))
    # And nothing named after an environment variable that was not there to expand. A run with
    # a hand-built environment starved Windows of `SystemDrive`, and a subprocess created a
    # directory literally called `%SystemDrive%` in this repository — a stray tree that git
    # reports as untracked and that nothing else here would have looked for.
    assert not [one for one in HERE.iterdir() if "%" in one.name]
    # And this repository's own governed files were not the ones it wrote into: the sample's
    # ids are the tell, and none of them may appear here.
    for role in ("ROADMAP", "CHANGELOG", "IMPROVEMENTS"):
        text = (HERE / "docs" / f"{role}.md").read_text(encoding="utf-8")
        assert "PROJ1" not in text, role


# -- the joins to the page ----------------------------------------------------


def test_the_page_renders_the_run_and_carries_no_output_of_its_own():
    """A command or a captured line typed into the prose is one that was true the day it was
    typed. Everything shown comes through the component or it is not there."""
    text = PAGE.read_text(encoding="utf-8")
    assert "<Walkthrough />" in text
    fenced = re.findall(r"```.*?```", text, re.S)
    assert not fenced, "the page carries a code block of its own"


def test_the_generator_refuses_a_run_that_demonstrates_nothing():
    """Two ways this page could go quietly useless: a run where nothing was refused, and one
    that leaked the build machine's paths. Both fail the build."""
    source = GENERATOR.read_text(encoding="utf-8")
    assert "nothing was refused" in source
    assert "an absolute path reached the output" in source


def test_the_component_says_what_each_exit_code_means():
    """Exit codes are the contract — 0, 1 for a gate that says no, 2 for an input that has to
    change — and a page showing a red 2 without saying which of the two it is teaches that the
    tool broke."""
    component = COMPONENT.read_text(encoding="utf-8")
    assert re.search(r"\b0:\s*\{", component)
    assert re.search(r"\b1:\s*\{", component)
    assert re.search(r"\b2:\s*\{", component)


def test_the_command_block_wraps_because_a_command_carries_a_sentence(steps):
    """`add --symptom <the symptom>` is a whole sentence on one line, so the shown commands are
    wider than any column the page has. Unwrapped they ran off the block and over the page
    (RK1430); and scrolling would be no better, since the argument is the half worth reading."""
    assert max(len(step["command"]) for step in steps) > 80
    component = COMPONENT.read_text(encoding="utf-8")
    block = re.search(r"pre\.cmd code[^}]*\{[^}]*\}", component)
    assert block, "the command block has no rule of its own"
    assert "pre-wrap" in block.group(0)
