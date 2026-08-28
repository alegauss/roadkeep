// The contents list, told about the headings no page source carries (RK1431).
//
// Starlight builds "On this page" from what Astro extracted out of the compiled MDX, which is
// why a page whose sections a component renders published an empty one. This is the join:
// `headings.ts` states what each of those components emits, and this puts it where the route
// data already had the rest.
//
// Named `starlightRouteData.ts` and not `middleware.ts` because Astro reserves that name for
// its own — Starlight refuses the config outright rather than letting the two collide.
import { defineRouteMiddleware } from "@astrojs/starlight/route-data";
import type { MarkdownHeading } from "astro";

import { configHeadings, sessionHeadings, verbHeadings, type Heading } from "./headings";

/** Where a page's generated headings go, and what they are. */
interface Generated {
  /** The heading they follow, or `null` where the component ends the page. */
  after: string | null;
  headings: Heading[];
}

const REFERENCE = "reference/";

function generatedFor(id: string): Generated | null {
  // One page per verb family, whose whole body is the table: nothing of its own to follow.
  if (id.startsWith(REFERENCE)) {
    return { after: null, headings: verbHeadings(id.slice(REFERENCE.length)) };
  }
  if (id === "configuration") return { after: null, headings: configHeadings() };
  // The one component that is not last on its page — the prose after it argues about the
  // numbers above it, so the sections have to interleave the way the page reads.
  if (id === "session") {
    return { after: "what-it-costs-before-anything-is-called", headings: sessionHeadings() };
  }
  return null;
}

/** The page's own headings with the generated ones in the place that page declares. */
function merged(page: MarkdownHeading[], generated: Generated, id: string): MarkdownHeading[] {
  if (generated.after === null) return [...page, ...generated.headings];
  const at = page.findIndex((one) => one.slug === generated.after);
  if (at < 0) {
    // The one hand-typed fact in this file, so it fails the build rather than going quiet: a
    // renamed heading would otherwise move a page's generated sections to the end of it, and
    // a contents list in the wrong order reads exactly like one in the right order.
    throw new Error(
      `[contents] ${id} places its generated headings after "${generated.after}", which is ` +
        `not one of its own — the page writes ${page.map((one) => one.slug).join(", ")}`,
    );
  }
  return [...page.slice(0, at + 1), ...generated.headings, ...page.slice(at + 1)];
}

interface TocItem extends MarkdownHeading {
  children: TocItem[];
}

/** Starlight's own placement: an entry goes as deep in the tree as its depth requires. */
function inject(items: TocItem[], item: TocItem): void {
  const last = items.at(-1);
  if (!last || last.depth >= item.depth) items.push(item);
  else inject(last.children, item);
}

export const onRequest = defineRouteMiddleware((context) => {
  const route = context.locals.starlightRoute;
  const generated = generatedFor(route.id);
  if (!generated || generated.headings.length === 0) return;

  route.headings = merged(route.headings, generated, route.id);

  // The tree was built before this ran, so it is rebuilt rather than appended to — the
  // page-title entry Starlight put at the top is kept, everything under it re-injected in
  // document order and filtered by the levels this area's contents list declares.
  const { toc } = route;
  if (!toc) return;
  const root = toc.items[0];
  const items: TocItem[] = root ? [{ ...root, children: [] }] : [];
  for (const heading of route.headings) {
    if (heading.depth < toc.minHeadingLevel || heading.depth > toc.maxHeadingLevel) continue;
    inject(items, { ...heading, children: [] });
  }
  toc.items = items;
});
