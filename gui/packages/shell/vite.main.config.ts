import { builtinModules } from 'node:module'

import { defineConfig } from 'vite'

// Everything in this package that Node runs: the Electron entry point, and the two
// launchers behind `npm run dev` and `npm start`. Vite builds them rather than `tsc`
// so that a relative import can be written the way a TypeScript file is normally
// written — without an extension — instead of naming the `.js` file the compiler is
// going to produce. `tsc -b` still typechecks every one of them; it just emits
// declarations rather than the code that runs.
//
// Node's own builtins, Electron and Vite itself stay external: they are present at
// runtime and bundling them would either fail or produce a second copy.
export default defineConfig({
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    minify: false,
    target: 'node22',
    lib: {
      entry: {
        main: 'src/main.ts',
        dev: 'src/dev.ts',
        start: 'src/start.ts',
        // The build step behind `npm run package`: it stamps what this build is and
        // refuses to package one that lost the posture it claims.
        'stamp-build': 'src/stamp-build.ts',
        // The gate behind `npm run audit`: it reads `npm audit --json` against the list of
        // advisories this project has answered, and fails on anything else (RG95).
        audit: 'src/audit.ts',
        // The command behind `npm run shots`: every surface photographed through Playwright,
        // for an agent to read (RG209).
        shots: 'src/shots.ts',
      },
      formats: ['es'],
    },
    rollupOptions: {
      // Playwright stays external for the reason Electron does: it is present at runtime,
      // and it resolves its own files relative to where it is installed.
      // axe likewise (RG211): its builder reads axe's own source off disk at runtime.
      //
      // `builtinModules` and not `/^node:/` alone (RG273): the Agent SDK imports `fs`, `path` and
      // a dozen more by their bare names, and bundled rather than left to Node those become a
      // module with nothing in it — an app that threw `Cannot read properties of undefined` on
      // load, which no test but the packaged run could see.
      external: [
        /^node:/,
        ...builtinModules,
        'electron',
        'vite',
        /^playwright-core/,
        /^@axe-core\//,
        'axe-core',
      ],
    },
  },
})
