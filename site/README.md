# The documentation area

The pages at <https://alegauss.github.io/roadkeep/guide/>. A separate npm project from the
Python package, with its own toolchain — Astro and Starlight — because `docs/` is the governed
store and is never a source directory.

```
npm install
npm run dev       # the area at http://localhost:4321/roadkeep/guide/
npm run build     # static HTML into ../docs/guide/
npm run preview   # serve what the build produced
```

`npm run dev` runs Astro's dev server as a background daemon: `npx astro dev status` says
whether it is up, `npx astro dev logs` shows its output and `npx astro dev stop` ends it. The
**first** start after a clean `npm install` generates content types and can exceed the 30 s
Astro waits before reporting a failure — run it again and it comes up in seconds.

## Where it may write, and what it must stay invisible to

`docs/` is two things at once. It is the governed store — `roadkeep.toml` points `roadmap`,
`changelog`, `improvements` and `decisions` at files in it — and it is what GitHub Pages
serves, which is why `index.html`, `llms.txt`, `robots.txt` and `assets/` sit beside the
Markdown. A build whose output directory is that directory writes over the store.

So this build owns exactly one reserved subtree of it, `docs/guide/`, and its source lives
here, outside. Astro empties `outDir` before writing, so that constant pointed one level up
would delete the roadmap; `tests/test_area.py` holds it, and holds that no path `[files]`
declares is inside what the build empties.

Nothing built is committed. `npm run build` writes into an ignored directory, and
`.github/workflows/site.yml` is what runs it for real — so what is published is what the
current source builds into, rather than whatever somebody last remembered to rebuild.

That workflow is two decisions and not one. The **build** runs on every push and pull request,
so a page that stopped compiling is found by whoever pushed it; the **deploy** fires on
`workflow_dispatch` only, because a publish on every push is one nobody can hold still while
reviewing it. The deploy serves the bytes the build already produced — two builds of one commit
are two answers about it, and the published one would be the untested.

## What goes on a page, and what does not

**Reference pages are generated from the package**, not written beside it. A page that retyped
a flag, a finding code or a config key would be wrong at the first rename and would report
nothing — so the build derives them from the same declarations the tool enforces.

`scripts/commands.mjs` runs as `prebuild` on both `dev` and `build`: it calls
`roadkeep commands --json`, which emits this checkout's own parser, and writes
`src/data/commands.generated.json` — git-ignored, because a committed copy is what a build
quietly falls back to. `VerbTable.astro` renders one verb family out of it, and each page under
`src/content/docs/reference/` is that component under prose written by hand. The two stay
apart: regenerating never edits an argument, and editing an argument never touches a table.
`tests/test_reference.py` holds the joins — a family with no page, a page with no family, and a
component reading a key the payload does not publish.

`scripts/findings.mjs` does the same for the gate's finding codes: `roadkeep explain --json`
gives the class, what raises it and which doors close it, and one page per code is written
under `src/content/docs/findings/`. Those pages are for the reader who has **not** adopted the
tool — somebody looking at a failed job or a denied write, whose code pasted into a search
engine resolves to nothing today.

The half no read can derive is the **situation**: the ordinary act that put them there. Those
are hand-written in `src/data/situations.json`, which is committed while the pages are not. Most
codes have none yet and the generator prints how many on every build — a coverage figure nobody
sees is one nobody closes. A key naming a code this build does not have fails the build.

`scripts/walkthrough.mjs` runs `../scripts/walkthrough.py`, which builds a **throwaway
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
