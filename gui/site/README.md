# roadkeep-gui site

The public site, at <https://alegauss.github.io/roadkeep/gui/>: a self-contained Vite +
React 19 + TypeScript workspace, prerendered to static files with a Markdown twin beside every
route. It is standalone: the app's own `npm run build` neither builds nor needs it, and it never
writes into `docs/`, which is roadkeep's.

It follows the shape of the freewilly and roadkeep sites by the same author, so the conventions
below are shared rather than invented here.

## Commands

```
npm install        # once
npm run dev        # dev server at /roadkeep/gui/
npm run build      # generate → tsc → client → social card → SSR → prerender
npm test           # the site's own claims, against the sources and the built output
npm run typecheck  # tsc -b, no emit
npm run preview    # serve the built dist/
```

`npm run build` is the gate, and it is one command on purpose. It regenerates the product facts
from this repository's source, type-checks, builds the client, rasterises the social card,
builds the SSR bundle and prerenders every route with its Markdown twin, `manifest.json`,
`sitemap.xml` and `robots.txt`. A drifted `<head>` template or a route with no page fails it.
`npm test` then asserts the built output, so it runs after the build rather than instead of it.

## Where things live

| Path                              | What                                                                                                                         |
| --------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `src/lib/site-content.ts`         | **All copy.** Sections only render it, so a claim is an array element a reviewer can check                                   |
| `src/lib/features.ts`             | The depth pages, one record each; routes, metadata and the landing index read the same list                                  |
| `scripts/product.mjs`             | **Every count the copy states**, read out of `packages/`, `package.json`, `electron-builder.yml` and the roadmap's non-goals |
| `src/lib/product.generated.ts`    | What that script wrote. Never edited by hand; `npm run generate` rewrites it                                                 |
| `src/routes.tsx`                  | The route table and its metadata, asserted against each other at import time                                                 |
| `src/lib/theme.ts` + `index.html` | The theme follows the OS, a stored choice overrides it, applied before first paint                                           |
| `src/components/sections/`        | One component per landing section; the order in `pages/Landing.tsx` is the argument                                          |
| `scripts/*.test.mjs`              | The site's claims: generated facts against their sources, routes and twins against `dist/`                                   |

## Rules this workspace keeps

- **A number is generated or it is not on the page.** The verb counts, the languages, the scan
  depth, the renderer posture and the non-goals come from the source. A figure typed into the
  copy is the defect `product.test.mjs` exists to catch.
- **Only the reader moves the window.** A panel scrolls its own element; no source calls
  `scrollIntoView`.
- **No third-party font at page load, no analytics.** The one outside script is the author's
  house ad, which counts nothing and stores nothing.
- **The mark is the app's.** `public/logo.svg` is `build/icon.svg`, byte for byte, and a test
  holds them equal.

It publishes as a path of roadkeep's own site (RK1704): roadkeep's `npm run build` in `site/`
runs this build last and copies `dist/` to its `dist/gui/`, and `site.yml` in the repository
root's `.github/workflows/` is the gate on every push that touches what this site reads, and
the one deploy.
