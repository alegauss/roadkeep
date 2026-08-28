// The headings a generated component renders, stated once (RK1431).
//
// Astro extracts a page's headings while it compiles the MDX, and Starlight builds "On this
// page" out of that array — so a heading a component renders at request time is in no source
// it read. The six reference pages published a contents list holding the page title alone,
// with a dozen verbs under it that nothing linked.
//
// `starlightRouteData.ts` merges these into the route's headings. The components render from
// the same declarations rather than from their own copy, because two statements of an anchor
// drift at the first rename — and the drift is silent, an anchor nothing answers still looking
// exactly like a link.
import commands from "./data/commands.generated.json";
import config from "./data/config.generated.json";

/** What Astro would have extracted, had the heading been written in the page. */
export interface Heading {
  depth: number;
  slug: string;
  text: string;
}

//: Every one of these is a section inside a page, so `h3` — the page's own title is the `h1`
//: and the prose around the component writes the `h2`s.
const SECTION = 3;

// -- the reference pages, one per verb family (RK1402) ------------------------

/** A verb's anchor. `add --block` is two words and one address. */
export function anchorOf(command: string): string {
  return command.replace(/ /g, "-");
}

export function verbHeadings(family: string): Heading[] {
  return commands.commands
    .filter((one) => one.family === family)
    .map((one) => ({ depth: SECTION, slug: anchorOf(one.command), text: one.command }));
}

// -- the configuration page (RK1404) ------------------------------------------

/** The tables `roadkeep.toml` may carry, in the order the read published them. */
export function configTables(): string[] {
  return [...new Set(config.keys.map((one) => one.table))];
}

/** The top level is a table with no name, and a page cannot address one by the empty string. */
export function configAnchor(table: string): string {
  return table || "top-level";
}

//: The one heading on that page whose words are written rather than read off a key.
export const FIXED: Heading = {
  depth: SECTION,
  slug: "fixed-by-the-build",
  text: "Fixed by the build, and not yours to declare",
};

export function configHeadings(): Heading[] {
  const found = configTables().map((table) => ({
    depth: SECTION,
    slug: configAnchor(table),
    text: table ? `[${table}]` : "the top level",
  }));
  // Rendered only where this build measures something, as the component renders it.
  if (config.fixed.length > 0) found.push(FIXED);
  return found;
}

// -- what a session costs (RK1405) --------------------------------------------

/** Verbs with a tool this project is not sent, and the role that would open each. */
export function withheldTools(): { command: string; needs: string | null }[] {
  return commands.commands
    .filter((one) => one.tools.length > 0 && !one.published)
    .map((one) => ({ command: one.command, needs: one.needs }));
}

export const SESSION = {
  connect: { depth: SECTION, slug: "at-connect", text: "Once, when the client connects" },
  //: One level down: the ranking is an appendix to what connecting costs, not a section
  //: beside it — and the contents list is configured to stop above it.
  dearest: { depth: SECTION + 1, slug: "dearest", text: "The ten that cost the most" },
  everyTurn: { depth: SECTION, slug: "every-turn", text: "On every turn" },
  withheld: { depth: SECTION, slug: "withheld", text: "What this project is not sent" },
} satisfies Record<string, Heading>;

export function sessionHeadings(): Heading[] {
  const found = [SESSION.connect, SESSION.dearest, SESSION.everyTurn];
  // Published only where a verb is actually withheld, as the component publishes it: a project
  // that declared every role has no such section, and must have no entry for one either.
  if (withheldTools().length > 0) found.push(SESSION.withheld);
  return found;
}
