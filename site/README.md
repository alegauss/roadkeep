# The roadkeep site

The pages at <https://alegauss.github.io/roadkeep/>. Two npm projects, separate from the Python
package, because `docs/` is the governed store this tool owns the writes to and is never a web
root.

```
npm install
npm --prefix docs install     # the documentation area, a second npm project
npm run dev                   # the pitch at http://localhost:5173/roadkeep/
npm run dev:docs              # the area at http://localhost:4321/roadkeep/docs/
npm run build                 # typecheck, build, SSR build, prerender, then the docs
npm test                      # the site's own claims, against what the build produced
```

`npm run dev:docs` runs Astro's dev server as a background daemon: `npx --prefix docs astro dev
status` says whether it is up, `… logs` shows its output and `… stop` ends it. The **first**
start after a clean install generates content types and can exceed the 30 s Astro waits before
reporting a failure — run it again and it comes up in seconds.

## How the pitch is put together

- **The copy lives in `src/lib/site-content.ts`.** Sections render it and never contain it, so
  a claim is an array element a reviewer can check against the tool rather than a string welded
  into the markup that displays it. Inline emphasis is a tagged run list rather than HTML, so
  nothing calls `dangerouslySetInnerHTML` and the twin generator has a structure to walk.
- **A transcript is data too.** Every terminal block is a list of lines carrying the colour
  class the theme gives each run, so what a command printed is a value and not a `<pre>`
  somebody edits with the highlighting in it.
- **The routes are a pair.** `src/routes.tsx` holds one metadata row and one component row per
  route, and an assertion at import time refuses either one without the other, in both
  directions, so a page cannot ship under another page's title. There is one route: the pitch is
  one scroll, and everything that wanted a second page went to the area.
- **Every page is prerendered**, with its `<head>` patched by replace-or-throw: a drifted
  template fails the build rather than publishing a page with the wrong canonical.
- **Every page has a Markdown twin** at the same address with `index.md`, converted from the
  same render as the HTML, so it cannot drift from the page. `manifest.json` lists the routes,
  the twins and their sizes; `robots.txt` and `sitemap.xml` are generated from the same route
  table.
- **Dark, and dark only.** A theme toggle is a control whose value is for a reader who stays,
  and this page is read once from a link — so what it would buy is a preference nobody sets
  against a flash of the wrong palette on first paint for everybody.

## The documentation area (`docs/`)

`/roadkeep/docs` is a **second npm project** with its own toolchain — Astro and Starlight —
building into this one's `dist/docs`. It exists because the renderer above holds its copy as
data and has no Markdown pipeline, no highlighting, no sidebar and no search, and writing those
four is writing a documentation framework. Starlight is those four, plus a Pagefind index built
from the pages, which is why search here needs no service to be up — the only shape this
project's non-goal against a server allows.

It is also the read adoption gates. The README is the only prose this project publishes for a
person and it is one file, so a link to any part of it is a link to the whole thing — and
everything narrower (`--help`, `explain`, `config`, the skill) answers only from an installed
copy. Evaluation comes before installation.

Three lines join the two builds, and each of the three fails in silence:

- **`build:docs` runs last.** `vite build` empties `dist/`, so a docs build placed anywhere
  earlier is deleted by the step after it.
- **The base is the site's plus one segment.** Astro rewrites the links it generates and not the
  ones written by hand, so an absolute href typed into a page 404s in production alone.
- **`outDir` is `../dist/docs`.** The deploy uploads `dist/` and nothing else.

None of them is left as a comment. `tests/test_area.py` reads the three declarations and
`scripts/docs.test.mjs` reads what they built, so a reordered script names its own cause rather
than being read backwards from a folder that went missing.

## What goes on a docs page, and what does not

**Reference pages are generated from the package**, not written beside it. A page that retyped a
flag, a finding code or a config key would be wrong at the first rename and would report
nothing — so the build derives them from the same declarations the tool enforces.

`docs/scripts/commands.mjs` runs as `prebuild`: it calls `roadkeep commands --json`, which emits
this checkout's own parser, and writes `src/data/commands.generated.json` — git-ignored, because
a committed copy is what a build quietly falls back to. `VerbTable.astro` renders one verb
family out of it, and each page under `docs/src/content/docs/reference/` is that component under
prose written by hand. The two stay apart: regenerating never edits an argument, and editing an
argument never touches a table. `tests/test_reference.py` holds the joins — a family with no
page, a page with no family, and a component reading a key the payload does not publish.

`docs/scripts/findings.mjs` does the same for the gate's finding codes: `roadkeep explain
--json` gives the class, what raises it and which doors close it, and one page per code is
written under `docs/src/content/docs/findings/`. Those pages are for the reader who has **not**
adopted the tool — somebody looking at a failed job or a denied write, whose code pasted into a
search engine resolves to nothing today.

The half no read can derive is the **situation**: the ordinary act that put them there. Those
are hand-written in `docs/src/data/situations.json`, which is committed while the pages are not.
Most codes have none yet and the generator prints how many on every build — a coverage figure
nobody sees is one nobody closes. A key naming a code this build does not have fails the build.

`docs/scripts/walkthrough.mjs` runs `../../scripts/walkthrough.py`, which builds a **throwaway
repository** with a genuinely drifted roadmap in it, executes the adoption against it and
captures what every command actually printed. Output pasted into prose is fiction with a shelf
life; this fails the build instead. `tests/test_walkthrough.py` runs the same script, so a
refusal reworded in the commit that changes the code is caught by the suite rather than by a
reader following along. The run redacts its temporary directory, and both the generator and the
suite refuse a run that leaked an absolute path or refused nothing.

**No page restates prose another file owns.** The six laws, the measured problem and the
non-goals each have an owner in the repository and three have a verb that prints them; a fifth
copy here is the accretion this tool exists to refuse, and the copy nobody is looking at is the
one that drifts.

## Publishing

Nothing built is committed. `npm run build` writes into ignored directories, and
`.github/workflows/site.yml` is what runs it for real — so what is published is what the current
source builds into, rather than whatever somebody last remembered to rebuild.

That workflow is two decisions and not one. The **build** runs on every push and pull request,
so a page that stopped compiling is found by whoever pushed it; the **deploy** fires on
`workflow_dispatch` only, because a publish on every push is one nobody can hold still while
reviewing it. The deploy serves the bytes the build already produced — two builds of one commit
are two answers about it, and the published one would be the untested.

One repository setting has to be made once, or the deploy is inert: **Settings → Pages → Build
and deployment → Source: "GitHub Actions"**.
