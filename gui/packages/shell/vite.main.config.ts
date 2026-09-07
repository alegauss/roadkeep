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
      },
      formats: ['es'],
    },
    rollupOptions: {
      external: [/^node:/, 'electron', 'vite'],
    },
  },
})
