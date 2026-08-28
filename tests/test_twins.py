"""A fetchable twin per page, and the index that has to name it (RK1410).

`llms.txt` exists because a model reading this project should not have to render a landing page
to learn what it is. An area published as HTML alone re-creates that problem one page at a
time, and what a read costs an agent is this project's whole premise.

The twin is **converted from the built HTML**, which is the decision this file mostly holds.
Most of these pages are half generated — a verb table off the parser, a finding page off the
gate's own table, the walkthrough off a real run — so a twin written from the Markdown source
would carry the prose and none of that, and a twin written from the same JSON would re-declare
the composition and let the two drift. One render, two outputs.

What is checked, on the built tree where there is one:

* **Every page has a twin**, and the address is derivable rather than looked up.
* **No twin is empty.** A twin that resolves and says nothing is worse than none: it looks
  exactly like an answer.
* **The generated half reaches the twin.** That is the whole reason for converting the render,
  and a twin without the tables would be the quiet failure.
* **The index names every page**, and the hand-written `llms.txt` names the index — an agent
  starting at the site root has to be able to get here.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent.parent
SITE = HERE / "site" / "docs"
BUILT = HERE / "site" / "dist" / "docs"
SCRIPT = SITE / "scripts" / "twins.mjs"
LLMS = HERE / "site" / "public" / "llms.txt"

#: The area's build output is git-ignored, so a clean checkout has none of it. These skip
#: rather than fail, which is what `tests/test_corpora.py` already settled for the other
#: reading this suite makes about something a build produces.
needs_build = pytest.mark.skipif(
    not (BUILT / "index.html").exists(),
    reason="the site has not been built in this checkout (npm --prefix site run build)",
)


def _pages() -> list[Path]:
    return sorted(BUILT.rglob("index.html"))


# -- the declaration, which is readable without a build ------------------------


def test_the_twin_is_converted_from_the_render_and_not_authored_again():
    """The decision this task turns on. A twin written from the source would carry the prose
    and none of the generated tables; one written from the same JSON would re-declare the
    composition. Said in the script, because the next person to touch it will be tempted."""
    source = SCRIPT.read_text(encoding="utf-8")
    assert "sl-markdown-content" in source
    assert "never authored a second time" in re.sub(r"\s*\n//\s*", " ", source)


def test_the_converter_refuses_an_empty_harvest():
    """A theme upgrade that moves the article would leave every twin as navigation or nothing,
    and both resolve, and both look like answers."""
    source = SCRIPT.read_text(encoding="utf-8")
    assert "no page carried" in source
    assert "came out empty" in source


def test_the_converter_refuses_a_root_index_that_does_not_name_it():
    """An agent starting at the site root has to be able to reach these pages. The link is one
    hand-written line in a file the build does not own, so the build checks it rather than
    writing it."""
    source = SCRIPT.read_text(encoding="utf-8")
    assert "does not name docs/llms.txt" in source


def test_the_hand_written_index_names_the_areas_own():
    assert "docs/llms.txt" in LLMS.read_text(encoding="utf-8")


def test_the_converter_runs_after_the_build():
    """Astro empties its output directory before it writes, so a twin written before the build
    is one the build then deletes."""
    scripts = json.loads((SITE / "package.json").read_text(encoding="utf-8"))["scripts"]
    assert scripts["postbuild"] == "node scripts/twins.mjs"
    assert "twins" not in scripts["prebuild"]


def test_the_parser_is_a_build_dependency_and_not_a_runtime_one():
    """Nothing this area publishes may need a service or a script to be up. An HTML parser used
    at build time is not that, and keeping it out of `dependencies` is what says so."""
    declared = json.loads((SITE / "package.json").read_text(encoding="utf-8"))
    assert "node-html-parser" in declared["devDependencies"]
    assert "node-html-parser" not in declared["dependencies"]


# -- and what the build actually produced -------------------------------------


@needs_build
def test_every_page_has_a_twin_at_a_derivable_address():
    """One rule and not a table: an address a caller has to look up is one a link handed to a
    session cannot be built from."""
    missing = [
        str(page.parent.relative_to(BUILT))
        for page in _pages()
        if not (page.parent / "index.md").exists()
    ]
    assert missing == []


@needs_build
def test_no_twin_resolves_and_says_nothing():
    """The failure mode a twin has that a missing file does not: it answers, and the answer is
    empty, and nothing about it looks wrong."""
    thin = [
        str(one.parent.relative_to(BUILT))
        for one in BUILT.rglob("index.md")
        if len(one.read_text(encoding="utf-8").split()) < 20
    ]
    assert thin == []


@needs_build
def test_the_generated_tables_reach_the_twin():
    """The whole reason the twin is converted from the render. A reference twin carrying the
    prose and none of the parser's own table would be the quiet failure this guards."""
    twin = (BUILT / "reference" / "querying" / "index.md").read_text(encoding="utf-8")
    assert "| Argument | Notes | What it is |" in twin
    assert "--json" in twin
    # And it is a table a reader renders, rather than one paragraph.
    assert "| --- |" in twin


@needs_build
def test_the_index_names_every_page_the_build_produced():
    """Generated rather than kept by hand, which is stronger than the check the task asked
    for: a page cannot be added without an entry, because the entry is derived from the page."""
    index = (BUILT / "llms.txt").read_text(encoding="utf-8")
    named = set(re.findall(r"roadkeep/docs/(.*?)index\.md", index))
    built = {
        f"{page.parent.relative_to(BUILT).as_posix()}/".replace("./", "")
        for page in _pages()
    }
    assert built <= named, sorted(built - named)


@needs_build
def test_the_index_addresses_are_the_ones_the_site_publishes():
    """A twin at an address nobody can fetch is a twin nobody has. The base is the area's own,
    which `astro.config.mjs` declares and `tests/test_area.py` holds against the pitch's."""
    base = re.search(r'const BASE = "([^"]+)"', (SITE / "astro.config.mjs").read_text("utf-8"))
    assert base
    index = (BUILT / "llms.txt").read_text(encoding="utf-8")
    for address in re.findall(r"\((https?://[^)]+)\)", index):
        assert base.group(1) in address, address
