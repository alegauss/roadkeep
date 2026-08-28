import type { ComponentType } from "react";
import { Landing } from "./pages/Landing";
import { meta } from "./lib/site-content";

// GitHub Pages derives the base from the repository name: the site is served at
// https://alegauss.github.io/roadkeep/, so the canonical, the og:url, the sitemap and every
// output path carry it. Written here and in vite.config.ts, and nowhere else.
export const SITE_ORIGIN = "https://alegauss.github.io";
export const BASE = "/roadkeep/";

// The social card. Absolute, because a platform fetching the card is not on this origin — a
// relative path is dropped by several of them. 1200x630 and not the 1280x640
// `roadkeep-social.png`, which is the size GitHub wants for a repository preview rather than
// the ratio Open Graph crops from; both files ship, and this is the one the meta names.
export const OG_IMAGE = `${SITE_ORIGIN}${BASE}assets/og.png`;

export type RouteMeta = {
  /** app path, leading slash: "/" is the whole site today */
  path: string;
  title: string;
  description: string;
  ogTitle: string;
  ogDescription: string;
};

// The metadata table. One row per route, and the prerender reads it to patch each page's head.
// Adding a page is a row here AND a row in ROUTES below: the assertion at the bottom of this
// module refuses either one on its own, at import time, in both directions.
//
// One row today. The pitch is one scroll on purpose — everything that wanted a second page went
// to the documentation area under /roadkeep/docs/, which is a build with a sidebar and a search
// index rather than a route here.
export const ROUTE_META: RouteMeta[] = [
  {
    path: "/",
    title: meta.title,
    description: meta.description,
    ogTitle: meta.og.title,
    ogDescription: meta.og.description,
  },
];

// The route to component map. The client (App) and the prerender (entry-server) both read this
// single source, so a route cannot render one page on the client and another in the static
// file.
export const ROUTES: { path: string; component: ComponentType }[] = [
  { path: "/", component: Landing },
];

/** The canonical and og:url for a route, carrying the base the URL never drops. */
export function canonicalUrl(path: string): string {
  const rel = path === "/" ? "" : `${path.replace(/^\//, "")}/`;
  return `${SITE_ORIGIN}${BASE}${rel}`;
}

/** The output path of a route's HTML file, relative to dist/. */
export function outputDir(path: string): string {
  return path === "/" ? "" : path.replace(/^\//, "");
}

// --- the pair, asserted in both directions at import time ---
// A route with a component but no metadata prerenders under another route's title; a route with
// metadata but no component never gets a file. Both are silent at runtime, so they are made
// loud at import: this throw fails tsc, the build or the prerender, whichever imports first.
(function assertRoutePair(): void {
  const metaPaths = ROUTE_META.map((r) => r.path);
  const compPaths = ROUTES.map((r) => r.path);
  const metaSet = new Set(metaPaths);
  const compSet = new Set(compPaths);
  if (metaSet.size !== metaPaths.length) {
    throw new Error("routes: a path appears twice in ROUTE_META");
  }
  if (compSet.size !== compPaths.length) {
    throw new Error("routes: a path appears twice in ROUTES");
  }
  for (const p of compSet) {
    if (!metaSet.has(p)) {
      throw new Error(`routes: "${p}" has a page but no metadata row, so add it to ROUTE_META`);
    }
  }
  for (const p of metaSet) {
    if (!compSet.has(p)) {
      throw new Error(`routes: "${p}" has a metadata row but no page, so add it to ROUTES`);
    }
  }
})();

export function componentFor(path: string): ComponentType {
  const found = ROUTES.find((r) => r.path === path);
  if (!found) throw new Error(`routes: no page for "${path}"`);
  return found.component;
}

/** Strip the Vite base from a browser pathname and normalise to an app path. */
export function toAppPath(pathname: string): string {
  let p = pathname;
  if (p.startsWith(BASE)) {
    p = "/" + p.slice(BASE.length);
  } else if (p === BASE.replace(/\/$/, "")) {
    p = "/";
  }
  if (p.length > 1) {
    p = p.replace(/\/+$/, "");
  }
  return p === "" ? "/" : p;
}
