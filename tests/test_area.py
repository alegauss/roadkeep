"""The two builds that make one site, and the joins between them (RK1398).

`site/` is the pitch — a Vite build whose copy lives in one module — and `site/docs/` is the
documentation area, a second npm project with its own toolchain building into the first one's
output. The deploy uploads `site/dist/` and nothing else, so a half that wrote anywhere outside
it is a half no publish carries.

The joins are not decoration. Each of the three fails **in silence**:

* **The build order.** `vite build` empties `dist/`, so the area's build runs after it or is
  deleted by the step that follows — one directory missing from a green deploy.
* **The base** is the site's plus one segment. Astro rewrites the links it generates and not the
  ones typed by hand, so a wrong prefix 404s in production and nowhere else, which is the class
  of defect no local preview finds.
* **Discovery.** `robots.txt` and `sitemap.xml` are generated from the pitch's route table, and
  that table will never know a page the area emits — so the area's own sitemap is named by hand
  in one line, and `site/scripts/docs.test.mjs` is what holds that the file it names was built.

And one property that is no longer a join at all: `docs/` used to be the web root *and* the
governed store, which is why a wrong `outDir` could have deleted the roadmap. It is the store
alone now, and the last test below is what keeps it that way.

What is *not* asserted here is the built output: whether a page compiled is what the build says
when it runs, and the two `node --test` suites beside it are what read `dist/`. This file reads
the declarations, so it is green on a checkout with no `node_modules` in it — which is every CI
job that has not installed yet, and every developer who has not.
"""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent.parent
SITE = HERE / "site"
AREA = SITE / "docs"
VITE = SITE / "vite.config.ts"
ASTRO = AREA / "astro.config.mjs"

#: The one segment the area occupies under the site root. Named once here because three
#: assertions below are about the same string appearing in three files.
SEGMENT = "docs"


def _declared(where: Path, name: str) -> str:
    """One `const NAME = "…"` out of a config, read as text.

    Both configs are JavaScript and this suite has no JavaScript to run them with, so the
    constants are read rather than imported. That is why they are constants at the top of those
    files and not literals inside the exported object: a value this cannot reach is a join
    nothing holds.
    """
    text = where.read_text(encoding="utf-8")
    found = re.search(rf'^(?:export )?const {re.escape(name)} = "([^"]*)";$', text, re.MULTILINE)
    assert found, f'{where.name} declares no `const {name} = "…"`'
    return found.group(1)


def test_the_area_is_its_own_project_inside_the_site_and_outside_the_store():
    """Two npm projects, and neither of them lives in `docs/`.

    The area is a second toolchain because the pitch holds its copy as data and has no Markdown
    pipeline, no highlighting, no sidebar and no search, and writing those four is writing a
    documentation framework. It sits inside `site/` because it builds into `site/dist/`, which
    is the one directory the deploy uploads.
    """
    assert (SITE / "package.json").exists()
    assert (AREA / "package.json").exists()
    store = (HERE / "docs").resolve()
    assert not str(SITE.resolve()).startswith(str(store))


def test_the_output_is_a_subtree_of_what_the_deploy_uploads():
    """Astro empties `outDir` before writing, so where it points is the whole safety of it."""
    out = _declared(ASTRO, "OUT_DIR")
    assert out == f"../dist/{SEGMENT}"
    # Resolved against the config's own directory, which is what Astro does with it — a
    # relative path asserted as a string alone would pass for `../../dist/docs` too.
    landed = (AREA / out).resolve()
    assert landed == (SITE / "dist" / SEGMENT).resolve()
    assert landed != (SITE / "dist").resolve()


def test_no_governed_file_is_inside_what_the_build_owns():
    """Whatever `[files]` declares, none of it may live under a directory a build empties.

    Two of them do empty one: `vite build` clears `site/dist/` and Astro clears `site/dist/docs`.
    A role pointed into either would be a file the next build deletes, and this is what says so.
    """
    declared = tomllib.loads((HERE / "roadkeep.toml").read_text(encoding="utf-8"))
    emptied = [(SITE / "dist").resolve(), (SITE / "dist" / SEGMENT).resolve()]
    for role, path in declared["files"].items():
        governed = (HERE / path).resolve()
        for owned in emptied:
            assert owned not in governed.parents, f"{role} is inside what a build empties"


def test_the_areas_base_is_the_sites_plus_one_segment():
    """Pages derives the site root from the repository name, so it is `/roadkeep/` — and the
    area is one segment under it. Read off the pitch's own config rather than spelled again:
    the two are one prefix, and a rename that moved one would leave the other 404ing."""
    site_base = _declared(VITE, "BASE")
    assert site_base == "/roadkeep/"
    assert _declared(ASTRO, "BASE") == f"{site_base}{SEGMENT}"


def test_the_docs_build_runs_last_because_the_step_before_it_empties_the_output():
    """The join that fails with no error at all: `vite build` empties `dist/`, so an area built
    before it is deleted by it and the deploy publishes a site with the documentation missing.

    Asserted as an order inside one script and not as the presence of a step, because the step
    was always there — what went wrong is where it sat.
    """
    scripts = json.loads((SITE / "package.json").read_text(encoding="utf-8"))["scripts"]
    build = scripts["build"]
    assert "build:docs" in build, "the site build does not build the area at all"
    assert build.index("vite build") < build.index("build:docs")
    assert build.index("prerender.mjs") < build.index("build:docs")
    assert scripts["build:docs"] == "npm --prefix docs run build"


def _patterns(path: Path) -> list[str]:
    """One `.gitignore`'s patterns, without its prose — these files explain themselves, so a
    word-split would find the very paths they are arguing about."""
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
    built = _patterns(SITE / ".gitignore")
    assert "dist" in built and "dist-server" in built
    assert "node_modules" in built
    assert ".astro" in _patterns(AREA / ".gitignore")


def test_the_store_is_the_store_and_nothing_else_is_in_it():
    """`docs/` used to be two things at once — the governed store and the directory Pages
    served — which is why `index.html`, `llms.txt`, `robots.txt` and `assets/` sat beside the
    Markdown, and why a build with a wrong `outDir` could have deleted the roadmap.

    It is the store alone now: the site is served out of `site/dist/`, and everything the web
    root needed moved to `site/public/`. Asserted as a closed set rather than as the absence of
    a page, because the property is that a file here is one a role declares — the weaker claim
    passes again the first time somebody puts an asset back.
    """
    declared = tomllib.loads((HERE / "roadkeep.toml").read_text(encoding="utf-8"))["files"]
    governed = {(HERE / path).resolve() for path in declared.values()}
    present = {p.resolve() for p in (HERE / "docs").iterdir()}
    assert present == governed, "docs/ holds something no role declares"
    # And the two the pitch needs are where the pitch is, or its build would emit neither.
    assert (SITE / "public" / "llms.txt").exists()
    assert (SITE / "public" / "assets" / "og.png").exists()


WORKFLOW = HERE / ".github" / "workflows" / "site.yml"


def test_the_workflow_builds_both_halves_and_uploads_the_one_directory():
    """The pitch and the area are two halves of one deploy: uploading either alone publishes a
    site with the other missing, and the half that goes missing is the generated one, because
    it is the half no commit would have shown was absent.

    One `npm run build` reaches both — that is what the script order above buys — so what this
    asserts is that the job runs it from the right place and keeps the right directory.
    """
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "working-directory: site" in workflow
    assert "npm ci" in workflow
    assert "npm run build" in workflow
    # The suites that read what the build produced, in the job that has it.
    assert "npm test" in workflow
    assert "actions/upload-pages-artifact" in workflow
    assert re.search(r"^\s+path: site/dist$", workflow, re.MULTILINE)
    # The setting that cannot be asserted from inside the repository, so it is at least written
    # down where somebody debugging an empty deploy will read it.
    assert "GitHub Actions" in workflow


def test_the_gate_runs_on_every_push_and_the_deploy_only_when_asked():
    """Two decisions, not one. A build that ran only before a publish would be a page found
    broken by whoever published weeks later; a publish on every push is one nobody can hold
    still while reviewing it, on the one artefact where a defect is immediately public."""
    yaml = pytest.importorskip("yaml", reason="pyyaml is not installed")
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    # `on` is YAML 1.1's boolean true, which is what safe_load makes of the unquoted key.
    triggers = workflow.get("on", workflow.get(True))
    assert set(triggers) == {"push", "pull_request", "workflow_dispatch"}
    jobs = workflow["jobs"]
    assert "workflow_dispatch" in jobs["deploy"]["if"]
    assert "if" not in jobs["build"], "the gate must not be conditional on the publish"


def test_the_trigger_names_every_input_the_pages_are_generated_from():
    """The area's reference pages are a function of `src/` (RK1412): the verbs come off
    `commands --json`, the findings off `explain --json`, the keys off `config --json` and the
    prices off `cost`. A path filter that names only `site/**` and `docs/**` is one that skips
    the build on exactly the commits that can break it — a renamed flag, a new verb family — and
    the next run is somebody else's, on a commit that did not cause the failure.

    `roadkeep.toml` is here for a different reason than `docs/**`: `config --json` reports which
    keys *this project* declared, so that file is read as data by a page rather than served as a
    governed store. `skills/**` joined them for the first reason (RK1444): the session page
    prices what the skill costs the turns that load it, off `cost --skill`, so an edit to the
    skill moves a figure on a built page and a filter naming only the package would skip the
    build on exactly the commit that changed it.

    Both events, because a filter is per-event: covering the push and leaving the pull request
    behind is a break found after the merge.
    """
    yaml = pytest.importorskip("yaml", reason="pyyaml is not installed")
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    triggers = workflow.get("on", workflow.get(True))
    generated_from = {"src/**", "skills/**", "roadkeep.toml"}
    for event in ("push", "pull_request"):
        paths = set(triggers[event]["paths"])
        assert generated_from <= paths, f"{event} does not rebuild the area when the package moves"
    assert set(triggers["push"]["paths"]) == set(triggers["pull_request"]["paths"])


def test_the_deploy_serves_the_bytes_the_gate_built():
    """Two builds of one commit are two answers about it, and the published one would be the
    untested. So the deploy downloads what the build kept rather than running npm again."""
    yaml = pytest.importorskip("yaml", reason="pyyaml is not installed")
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    deploy = workflow["jobs"]["deploy"]
    assert deploy["needs"] == "build"
    uses = [step.get("uses", "") for step in deploy["steps"]]
    assert any(one.startswith("actions/download-artifact") for one in uses)
    assert not [step for step in deploy["steps"] if "npm" in str(step.get("run", ""))]
    # And the two halves name the same artefact, which is the join that would otherwise fail
    # only at deploy time, on the one run nobody wants to debug.
    kept = next(
        step for step in workflow["jobs"]["build"]["steps"]
        if step.get("uses", "").startswith("actions/upload-artifact")
    )
    downloaded = next(
        step for step in deploy["steps"]
        if step.get("uses", "").startswith("actions/download-artifact")
    )
    assert kept["with"]["name"] == downloaded["with"]["name"]


def test_the_entry_page_carries_the_frontmatter_the_build_validates():
    """`docsSchema` refuses a page with no title at build time, which is this project's own
    trade one repository over. Asserted because the entry page is the one that would otherwise
    only be checked by somebody running the build."""
    page = AREA / "src" / "content" / "docs" / "index.mdx"
    text = page.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    front = text.split("---\n", 2)[1]
    assert re.search(r"^title: \S", front, re.MULTILINE)
    assert re.search(r"^description: \S", front, re.MULTILINE)


def test_neither_build_declares_a_dependency_that_runs_at_read_time():
    """Nothing here may need a service to be up. The area's search is indexed into the output at
    build time and the pitch is static files, which is the only shape the non-goal against a
    server allows — so a dependency implying a running backend would be that non-goal broken by
    a build step.

    **What is held is the runtime set, not the total.** This first asserted there were no
    development dependencies at all, which was a stricter rule than the reason for it: an HTML
    parser used to convert a page into its plain-text twin runs in the build and ships nothing,
    and refusing it would have been refusing a tool for a claim about a server.
    """
    area = json.loads((AREA / "package.json").read_text(encoding="utf-8"))
    assert set(area["dependencies"]) == {"@astrojs/starlight", "astro"}
    assert "pagefind: true" in ASTRO.read_text(encoding="utf-8")

    pitch = json.loads((SITE / "package.json").read_text(encoding="utf-8"))
    assert set(pitch["dependencies"]) == {"react", "react-dom"}
    # And what ships is the prerendered file: the client hydrates what is already in the HTML,
    # so a reader with no JavaScript still has the whole page.
    assert "prerender.mjs" in pitch["scripts"]["build"]


@pytest.mark.parametrize(
    "where,name", [(VITE, "BASE"), (ASTRO, "BASE"), (ASTRO, "OUT_DIR")]
)
def test_each_join_is_reachable_as_a_constant(where, name):
    """The reason those are `const`s and not literals in the exported object: a join this suite
    cannot read is one it cannot hold, and a comment calling it a join would be the only thing
    saying so."""
    assert _declared(where, name)
