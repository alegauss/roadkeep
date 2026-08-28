"""The contents list, on the pages whose sections a component renders (RK1431).

Astro extracts a page's headings while it compiles the MDX, and Starlight builds "On this
page" out of that array. Half this area's pages are a component — the six reference pages are
one almost entirely — so their sections were in no source Astro read, and every one of them
published a contents list holding the page title alone.

The fix is a route middleware, and what it needs held is the two joins it introduces:

* **A heading is stated once.** The components render from `headings.ts` and the middleware
  reads the same declarations, because two lists drift at the first rename and the drift is
  silent — an anchor nothing answers still looks exactly like a link.
* **Every page that renders headings is a page the middleware covers.** A component added
  tomorrow, or an existing one used on a second page, is a page that goes quietly back to an
  empty list. That is the failure this file exists for: nothing about the build says no.

Nothing here runs the build, for the reason `test_reference.py` gives — these read the
declarations, so they are green on a checkout with no `node_modules` in it.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent.parent
SITE = HERE / "site" / "docs"
PAGES = SITE / "src" / "content" / "docs"
COMPONENTS = SITE / "src" / "components"
DECLARED = SITE / "src" / "headings.ts"
MIDDLEWARE = SITE / "src" / "starlightRouteData.ts"
CONFIG = SITE / "astro.config.mjs"

#: A heading in an Astro template, with whatever the `id` is written as.
HEADING = re.compile(r"<h([1-6])\s+id=(\{[^}]*\}|\"[^\"]*\")")


def slugged(title: str) -> str:
    """A heading's anchor, as the Markdown pipeline derives one. Enough of the rule for the
    prose headings on these pages, which are words and spaces."""
    return re.sub(r"[^a-z0-9 -]", "", title.lower()).replace(" ", "-")


def components_that_render_headings() -> dict[Path, list[tuple[str, str]]]:
    """Every component emitting a heading, with the level and the `id` expression."""
    found = {}
    for one in sorted(COMPONENTS.glob("*.astro")):
        headings = HEADING.findall(one.read_text(encoding="utf-8"))
        if headings:
            found[one] = headings
    return found


def pages_importing(component: Path) -> list[str]:
    """The route ids of the pages rendering that component — the slug, as Starlight has it."""
    found = []
    for page in sorted(PAGES.rglob("*.mdx")):
        if component.name in page.read_text(encoding="utf-8"):
            found.append(page.relative_to(PAGES).with_suffix("").as_posix())
    return found


# -- the join to the middleware -----------------------------------------------


def test_the_area_wires_the_middleware_in():
    """Without this line the whole file is dead code that reads exactly like a fix."""
    assert MIDDLEWARE.is_file()
    assert "routeMiddleware" in CONFIG.read_text(encoding="utf-8")
    assert MIDDLEWARE.name.removesuffix(".ts") in CONFIG.read_text(encoding="utf-8")


def test_every_page_that_renders_a_heading_is_one_the_middleware_covers():
    """The failure this file exists for. A component added tomorrow, or an existing one put on
    a second page, publishes a page whose sections nothing links — and the build is green, the
    contents list having no way to know it is short."""
    middleware = MIDDLEWARE.read_text(encoding="utf-8")
    for component, _ in components_that_render_headings().items():
        for page in pages_importing(component):
            covered = f'"{page}"' in middleware or f'"{page.split("/")[0]}/"' in middleware
            assert covered, f"{page} renders {component.name} and the middleware says nothing"


def test_the_page_that_interleaves_names_a_heading_its_own_prose_writes():
    """`SessionCost` is the one component that is not last on its page, so where its sections
    go is declared by naming the heading they follow — the one hand-typed fact in the join.
    Renamed in the prose alone, the generated half would move to the end of the page."""
    after = re.findall(r'after:\s*"([^"]+)"', MIDDLEWARE.read_text(encoding="utf-8"))
    assert after, "nothing interleaves any more, and this test is what says so"
    written = {
        slugged(title)
        for page in PAGES.rglob("*.mdx")
        for title in re.findall(r"^#{2,6} (.+)$", page.read_text(encoding="utf-8"), re.M)
    }
    for one in after:
        assert one in written, f"the middleware follows {one!r}, which no page writes"


# -- the join to the components -----------------------------------------------


@pytest.mark.parametrize(
    "component", sorted(components_that_render_headings(), key=lambda one: one.name)
)
def test_no_component_writes_an_anchor_of_its_own(component: Path):
    """Every anchor is an expression reading `headings.ts`, never a literal. A component and a
    middleware each spelling one is a link that stops resolving the day either is edited, and
    nothing reports it: the page still renders and the entry still looks like a link."""
    text = component.read_text(encoding="utf-8")
    literal = [spelling for _, spelling in HEADING.findall(text) if spelling.startswith('"')]
    assert not literal, {"anchors written into the component": literal}
    assert "../headings" in text, "it renders a heading and reads no declaration"


def test_the_declarations_are_derived_and_not_a_second_listing():
    """`headings.ts` states where a heading goes, never which ones there are: the reference
    tables, the config tables and the withheld verbs all come off the same payloads the
    components render, so a verb renamed moves the anchor and the entry together."""
    text = DECLARED.read_text(encoding="utf-8")
    assert "commands.generated.json" in text
    assert "config.generated.json" in text
