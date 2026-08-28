"""Prose this repository owns, rendered by the area and restated nowhere in it (RK1408).

This project's own thesis is against what a documentation area usually becomes. The six laws
are written in `agents.md`, in the README and in `llms.txt`; a fourth copy would be exactly the
accretion the tool exists to refuse, and the copy nobody is looking at is the one that drifts.

So the rule is one direction: a page **renders** what a file already owns. The laws come out of
`agents.md`, the non-goals out of `roadkeep non-goal list` — the verb that owns them, since
they are bullets in the roadmap and a second copy is stale from the next write.

Two properties, and the second is the one that lasts:

* **What is rendered is what the owner says.** A harvest that silently found four laws would
  publish four and look complete, so the generator refuses a count that is not six.
* **No page in this area carries its own copy.** Held over every `.mdx` here rather than over
  the pages that exist today, so a page written next month is covered by the rule without
  anybody remembering it.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent.parent
SITE = HERE / "site" / "docs"
PAGES = SITE / "src" / "content" / "docs"
GENERATOR = SITE / "scripts" / "owned.mjs"
COMPONENT = SITE / "src" / "components" / "Owned.astro"

#: The file that owns the laws. Named once: the generator harvests from it, and this reads the
#: same file to say what the harvest should have found.
AGENTS = HERE / "agents.md"

_LAW = re.compile(r"^\|\s*(L\d)\s*\|\s*(.+?)\s*\|$", re.MULTILINE)


def _laws() -> dict[str, str]:
    return {one: text for one, text in _LAW.findall(AGENTS.read_text(encoding="utf-8"))}


def _non_goals() -> list[str]:
    found = subprocess.run(
        [sys.executable, "-m", "roadkeep.cli", "non-goal", "list", "--json"],
        cwd=HERE,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={"PYTHONPATH": str(HERE / "src"), "PYTHONIOENCODING": "utf-8", "PATH": ""},
    )
    assert found.returncode == 0, found.stderr
    return json.loads(found.stdout)["non_goals"]


def _mdx() -> list[Path]:
    """Every hand-written page in the area. The generated ones are absent from a clean
    checkout, which is why this globs the source rather than the built tree."""
    return sorted(one for one in PAGES.rglob("*.mdx") if "findings" not in one.parts)


# -- what is rendered is what the owner says ----------------------------------


def test_the_owner_still_declares_six_laws():
    """The harvest is anchored on a table shape rather than a line number, so the way it fails
    is by finding fewer — and four laws rendered as though they were all of them is a page that
    is wrong in the one way nothing on it shows."""
    assert sorted(_laws()) == ["L1", "L2", "L3", "L4", "L5", "L6"]


def test_the_generator_refuses_a_harvest_that_is_not_the_whole_table():
    source = GENERATOR.read_text(encoding="utf-8")
    assert "this project has six" in source
    assert "throw new Error" in source


def test_the_generator_refuses_a_listing_the_verb_elided():
    """`non-goal list` bounds its output. Some of them rendered without saying so reads as the
    whole list, which is the one way this could quietly mislead."""
    source = GENERATOR.read_text(encoding="utf-8")
    assert "non_goals_elided" in source
    assert "were elided by the read" in source


def test_the_roadmap_still_declares_the_non_goals_the_area_renders():
    assert _non_goals(), "the roadmap declares none, so the area would render nothing"


# -- and nothing in the area carries its own copy -----------------------------


@pytest.mark.parametrize("page", _mdx(), ids=lambda one: one.stem)
def test_no_page_restates_a_law(page):
    """The rule, held over every page here rather than over the ones that exist today. A law
    typed into a page is the fourth copy, and it is the one nobody is looking at.

    Compared on the law's own distinctive phrase rather than the whole sentence: a page is
    allowed to *mention* that the tool never writes prose, and is not allowed to reproduce the
    line `agents.md` carries.
    """
    text = page.read_text(encoding="utf-8")
    for one, law in _laws().items():
        stripped = re.sub(r"[*`]", "", law).strip().rstrip(".")
        assert stripped not in text, f"{page.name} restates {one}"


@pytest.mark.parametrize("page", _mdx(), ids=lambda one: one.stem)
def test_no_page_restates_a_non_goal(page):
    """Same rule, other owner. These are bullets in the roadmap and `non-goal list` prints
    them, so a page holding its own version is stale from the next write of that file."""
    text = page.read_text(encoding="utf-8")
    for one in _non_goals():
        stripped = re.sub(r"[*`]", "", one).strip().rstrip(".")
        assert stripped not in text, f"{page.name} restates a non-goal"


def test_the_page_that_shows_them_renders_them():
    """The other direction: having refused every copy, the area has to actually show them
    somewhere, or the rule has been kept by saying nothing."""
    index = (PAGES / "index.mdx").read_text(encoding="utf-8")
    assert 'shows="laws"' in index
    assert 'shows="non-goals"' in index
    assert "Owned.astro" in index


def test_the_generator_runs_before_the_build():
    scripts = json.loads((SITE / "package.json").read_text(encoding="utf-8"))["scripts"]
    assert "scripts/owned.mjs" in scripts["prebuild"]


def test_the_rendered_markup_is_the_authors_and_never_a_readers():
    """The component sets HTML from the harvested strings, which is safe exactly because those
    strings come from files in this repository. Said in the source, because the next person to
    reuse it will be reusing the dangerous half."""
    source = COMPONENT.read_text(encoding="utf-8")
    assert "set:html" in source
    # Whitespace-normalised, because the sentence is prose in a comment and where it wraps is
    # the author's business — a test that pinned the line break would be asserting formatting.
    assert "never from a reader" in re.sub(r"\s*\n\s*//\s*", " ", source)
