import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// GitHub Pages derives this from the repository name, so it is not a preference: the site is
// served at https://alegauss.github.io/roadkeep/ and every canonical, asset path and sitemap
// entry carries the prefix. Written here and in src/routes.tsx, and nowhere else.
export const BASE = "/roadkeep/";

export default defineConfig({
  base: BASE,
  plugins: [react()],
  build: {
    // `docs/` is the governed store this tool owns the writes to — a roadmap, a changelog, a
    // rationale file and a decision ledger — so it is never a web root. The site builds to its
    // own dist/, and the documentation area builds into dist/docs under it.
    outDir: "dist",
    emptyOutDir: true,
  },
});
