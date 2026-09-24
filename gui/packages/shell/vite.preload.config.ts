import { defineConfig } from 'vite'

// The preload, and only the preload, because it is the one file here that cannot be an
// ES module. It runs sandboxed, where the module system is Electron's restricted
// CommonJS `require` — it reaches Electron's own modules and nothing else — so an
// import of `@rk/core` has to already be inside the file by the time Electron
// loads it. Hence a separate build: CommonJS output, `electron` left external because
// the sandbox does provide that one.
//
// `emptyOutDir` is off because the main build has already written `dist`.
export default defineConfig({
  build: {
    outDir: 'dist',
    emptyOutDir: false,
    minify: false,
    target: 'node22',
    lib: {
      entry: 'src/preload.ts',
      formats: ['cjs'],
      fileName: () => 'preload.cjs',
    },
    rollupOptions: {
      external: ['electron'],
    },
  },
})
