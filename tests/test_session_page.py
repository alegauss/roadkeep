"""What a session receives, priced where a person can read it (RK1405).

Half of this tool's surface is not a command line, and the README covers installing those five
things rather than what they then do. The questions that reader has have **numbers** in them —
what connecting costs before a call is made, which tool is the expensive one, how much room is
left under `[tools] session` — and every one of them is a read this tool already makes about
itself.

So the figures are generated and the prose beside them is not, for the reason every other page
here splits that way. What is held here is the join, plus two failures this page had:

* **The component reads keys the payload publishes**, which is `VerbTable`'s failure and has
  now caught something on three of four components.
* **The numbers do not carry the build machine's locale.** `toLocaleString()` with no argument
  formats to whatever the builder's environment says, so 64,556 published as `64.556` — read
  by an English page as sixty-four point five, and wrong on a page whose whole subject is
  what a number is.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

from generated import read_by

HERE = Path(__file__).resolve().parent.parent
SITE = HERE / "site" / "docs"
PAGE = SITE / "src" / "content" / "docs" / "session.mdx"
COMPONENT = SITE / "src" / "components" / "SessionCost.astro"
GENERATOR = SITE / "scripts" / "session.mjs"


def _ask(*argv: str) -> dict:
    found = subprocess.run(
        [sys.executable, "-m", "roadkeep.cli", *argv, "--json"],
        cwd=HERE,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={"PYTHONPATH": str(HERE / "src"), "PYTHONIOENCODING": "utf-8", "PATH": ""},
    )
    assert found.returncode == 0, found.stderr
    return json.loads(found.stdout)


# -- the join, in the direction that has broken before ------------------------


def test_the_component_reads_only_keys_the_two_payloads_publish():
    """Three payloads reach this component — the tool prices, the session totals and the
    command surface — so a name that agrees with none of them is caught only by asking each."""
    tools = _ask("cost", "--tools")
    session = _ask("cost", "--session")
    component = COMPONENT.read_text(encoding="utf-8")
    assert read_by(component, "tools") <= set(tools), {
        "read off the tool prices, not published": sorted(
            read_by(component, "tools") - set(tools)
        )
    }
    assert read_by(component, "tool") <= set(tools["by_tool"][0])
    assert read_by(component, "session") <= set(session), {
        "read off the session totals, not published": sorted(
            read_by(component, "session") - set(session)
        )
    }
    assert read_by(component, "file") <= set(session["each_turn"]["files"][0])


def test_the_page_names_all_five_surfaces():
    """The symptom this closed was that nothing described what a session receives — so a page
    that covered four of them would leave the same gap in a smaller place."""
    text = PAGE.read_text(encoding="utf-8").lower()
    for surface in ("hook", "skill", "slash command", "mcp server", "launcher"):
        assert surface in text, surface


# -- the locale leak, which shipped once --------------------------------------


def test_no_number_is_formatted_in_the_build_machines_locale():
    """`toLocaleString()` with no argument formats to whatever the builder's environment says.
    This page published `64.556` for 64,556 — a decimal point where an English reader expects
    a thousands separator, on the one page whose entire subject is what a number is.

    The published site has one language, so the locale is the page's and never the builder's.
    """
    component = COMPONENT.read_text(encoding="utf-8")
    assert "toLocaleString(" in component, "the numbers stopped being formatted at all"
    assert not re.search(r"toLocaleString\(\s*\)", component), (
        "a bare toLocaleString() takes the build machine's locale"
    )


def test_every_figure_on_the_page_is_rendered_and_none_typed():
    """A number typed into the prose is one that was true on the day it was typed. Every figure
    comes through the component or it is not on the page."""
    prose = PAGE.read_text(encoding="utf-8")
    # Four or more digits, which is what every cost here is; a `[tools]` name or a heading
    # level is not. Nothing in the prose may carry one.
    assert not re.findall(r"\b\d{4,}\b", prose)


# -- what the generator must refuse -------------------------------------------


def test_the_generator_refuses_a_project_with_nothing_budgeted():
    """A project with no `[budgets]` prices nothing per turn, and the page would say a session
    pays nothing on every turn — true of that project and false of the one being described."""
    source = GENERATOR.read_text(encoding="utf-8")
    assert "nothing is budgeted per turn" in source
    assert "throw new Error" in source


def test_the_generator_runs_before_the_build():
    scripts = json.loads((SITE / "package.json").read_text(encoding="utf-8"))["scripts"]
    assert "scripts/session.mjs" in scripts["prebuild"]


def test_the_page_is_reachable_from_the_sidebar():
    config = (SITE / "astro.config.mjs").read_text(encoding="utf-8")
    assert 'link: "/session/"' in config


def test_the_withheld_list_is_derived_and_this_project_has_one():
    """The fact an adopter meets as a tool that is not there. It is only a worked example while
    this repository actually withholds something — a project that declared every role would
    render the section empty and say nothing."""
    surface = _ask("commands")
    withheld = [
        one["command"]
        for one in surface["commands"]
        if one["tools"] and not one["published"]
    ]
    assert withheld, "this project publishes every tool, so the section demonstrates nothing"
    assert all(
        one["needs"]
        for one in surface["commands"]
        if one["tools"] and not one["published"]
    ), "a withheld tool with no role names no door out"
