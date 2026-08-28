"""The documentation area's joins to the tree it is built into (RK1398).

The area is a second build in a repository whose `docs/` directory is two things at once: the
governed store `roadkeep.toml` points four roles at, and the directory GitHub Pages serves. So
the joins are not decoration — one of them is the difference between a build that emits pages
and a build that empties the roadmap.

Three, each asserted here against what declares it elsewhere rather than remembered:

* **The base** is the repository name plus the one segment this area occupies. Astro rewrites
  the links it generates and not the ones typed by hand, so a wrong prefix 404s in production
  and nowhere else — which is the class of defect no local preview finds.
* **The output** is a reserved subtree inside the store, and its source is outside it. Astro
  empties `outDir` before it writes, so this constant pointed one level up would delete the
  four governed files. Held here **and** by the gate refusing to be the thing that noticed.
* **Discovery**, because the pitch page ships a hand-written `sitemap.xml` and `robots.txt`
  that will never know a page this build emits.

What is *not* asserted is the built output: whether a page compiled is what the build says
when it runs, and CI running that build is RK1400. This file reads the declarations, so it is
red on a checkout with no `node_modules` in it — which is every CI job that has not installed
the area yet, and every developer who has not.
"""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent.parent
SITE = HERE / "site"
CONFIG = SITE / "astro.config.mjs"

#: The one segment this area occupies under the site root. Named once here because three
#: assertions below are about the same string appearing in three files.
SEGMENT = "guide"


def _declared(name: str) -> str:
    """One `const NAME = "…"` out of the Astro config, read as text.

    The config is JavaScript and this suite has no JavaScript to run it with, so the constants
    are read rather than imported. That is why they are constants at the top of that file and
    not literals inside the exported object: a value this cannot reach is a join nothing holds.
    """
    text = CONFIG.read_text(encoding="utf-8")
    found = re.search(rf'^const {re.escape(name)} = "([^"]*)";$', text, re.MULTILINE)
    assert found, f"{CONFIG.name} declares no `const {name} = \"…\"`"
    return found.group(1)


def test_the_area_is_its_own_project_outside_the_store():
    """The source is not in `docs/`, which is the whole arrangement: a build whose sources sat
    beside the governed files would be one `outDir` typo away from being unable to tell them
    apart."""
    assert (SITE / "package.json").exists()
    assert not str(SITE.resolve()).startswith(str((HERE / "docs").resolve()))


def test_the_output_is_a_reserved_subtree_of_the_store_and_never_the_store():
    """Astro empties `outDir` before writing. `../docs` would take the roadmap with it."""
    out = _declared("OUT_DIR")
    assert out == f"../docs/{SEGMENT}"
    # Resolved against the config's own directory, which is what Astro does with it — a
    # relative path asserted as a string alone would pass for `../../docs/guide` too.
    landed = (SITE / out).resolve()
    assert landed == (HERE / "docs" / SEGMENT).resolve()
    assert landed != (HERE / "docs").resolve()


def test_no_governed_file_is_inside_what_the_build_owns():
    """The property the constant above is only a spelling of: whatever `[files]` declares, none
    of it may live under the subtree a build empties. A role added tomorrow that pointed into
    `docs/guide/` would be a file the next build deletes, and this is what says so."""
    declared = tomllib.loads((HERE / "roadkeep.toml").read_text(encoding="utf-8"))
    owned = (HERE / "docs" / SEGMENT).resolve()
    for role, path in declared["files"].items():
        governed = (HERE / path).resolve()
        assert owned not in governed.parents, f"{role} is inside what the build empties"


def test_the_base_is_the_repository_and_the_one_segment_under_it():
    """Pages serves this repository from `docs/` on the default branch, so the site root is the
    repository name — which the pitch page's own canonical URL is the authority on."""
    base = _declared("BASE")
    assert base == f"/roadkeep/{SEGMENT}"
    published = (HERE / "docs" / "index.html").read_text(encoding="utf-8")
    assert f'content="https://alegauss.github.io{base.rsplit("/", 1)[0]}/"' in published


def test_the_hand_written_robots_names_the_sitemap_this_build_emits():
    """The pitch page's `sitemap.xml` is written by hand and lists one URL, so it will never
    carry a page from here. Both halves of one deploy are crawlable or one of them is not."""
    robots = (HERE / "docs" / "robots.txt").read_text(encoding="utf-8")
    assert f"/roadkeep/{SEGMENT}/sitemap-index.xml" in robots


def _patterns(path: Path) -> list[str]:
    """One `.gitignore`'s patterns, without its prose — both of these files explain themselves,
    so a word-split would find the very paths they are arguing about."""
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def test_nothing_the_build_produces_is_committed():
    """The generated tree is published by the workflow that builds it and never by a commit.

    A committed build output is a second answer to what the site is, and the stale one the
    moment somebody edits a page and does not rebuild — which is the defect the derived README
    block already has a gate against, and one this avoids having to gate at all.
    """
    assert f"docs/{SEGMENT}/" in _patterns(HERE / ".gitignore")
    downloaded = _patterns(SITE / ".gitignore")
    assert "node_modules" in downloaded
    assert ".astro" in downloaded


def test_the_workflow_builds_the_area_and_uploads_the_whole_served_directory():
    """The area and the pitch page are two halves of one deploy: uploading either alone
    publishes a site with the other missing, and the half that goes missing is the generated
    one, because it is the half no commit would have shown was absent."""
    workflow = (HERE / ".github" / "workflows" / "pages.yml").read_text(encoding="utf-8")
    assert "working-directory: site" in workflow
    assert "npm ci" in workflow
    assert "npm run build" in workflow
    assert "actions/upload-pages-artifact" in workflow
    assert re.search(r"^\s+path: docs$", workflow, re.MULTILINE)
    # The setting that cannot be asserted from inside the repository, so it is at least
    # written down where somebody debugging an empty deploy will read it.
    assert "GitHub Actions" in workflow


def test_the_entry_page_carries_the_frontmatter_the_build_validates():
    """`docsSchema` refuses a page with no title at build time, which is this project's own
    trade one repository over. Asserted because the entry page is the one that would otherwise
    only be checked by somebody running the build."""
    page = SITE / "src" / "content" / "docs" / "index.mdx"
    text = page.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    front = text.split("---\n", 2)[1]
    assert re.search(r"^title: \S", front, re.MULTILINE)
    assert re.search(r"^description: \S", front, re.MULTILINE)


def test_the_area_declares_no_dependency_that_runs_at_read_time():
    """Nothing here may need a service to be up. Search is indexed into the output at build
    time, which is the only shape the non-goal against a server allows — so a dependency that
    implied a running backend would be the non-goal broken by a build step."""
    declared = json.loads((SITE / "package.json").read_text(encoding="utf-8"))
    assert set(declared["dependencies"]) == {"@astrojs/starlight", "astro"}
    assert "devDependencies" not in declared or not declared["devDependencies"]
    assert "pagefind: true" in CONFIG.read_text(encoding="utf-8")


@pytest.mark.parametrize("name", ["BASE", "OUT_DIR"])
def test_each_join_is_reachable_as_a_constant(name):
    """The reason those two are `const`s and not literals in the exported object: a join this
    suite cannot read is one it cannot hold, and a comment calling it a join would be the only
    thing saying so."""
    assert _declared(name)
