// The docs collection, as Starlight's loader defines it. Pages live in src/content/docs and
// their frontmatter is validated against docsSchema at build time, so a page with no title
// fails the build rather than publishing a heading-less entry into the sidebar.
//
// That validation is the same trade the whole tool makes: refuse the page where the text is
// created, rather than report a malformed one after it has been published.
import { defineCollection } from "astro:content";
import { docsLoader } from "@astrojs/starlight/loaders";
import { docsSchema } from "@astrojs/starlight/schema";

export const collections = {
  docs: defineCollection({ loader: docsLoader(), schema: docsSchema() }),
};
