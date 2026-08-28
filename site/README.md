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

**No page restates prose another file owns.** The six laws, the measured problem and the
non-goals each have an owner in the repository and three have a verb that prints them; a fifth
copy here is the accretion this tool exists to refuse, and the copy nobody is looking at is the
one that drifts.
