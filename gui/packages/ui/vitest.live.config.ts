// With the extension, unlike every other relative import in this repository: a Vite config
// is loaded by Vite's own native loader rather than compiled by the bundler, and that
// loader warns on an extensionless specifier it will one day refuse.
import base from './vite.config.ts'

/**
 * The half of `ui` that reaches outside the process (RG64).
 *
 * Two files: one reads the built bundle to establish what the renderer actually ships, and
 * one runs the design system's duplicates gate in a child process. Neither is about a
 * component, both need something to have happened first, and neither belongs in the suite
 * somebody runs between edits.
 *
 * The base config is imported rather than restated: the React and Tailwind plugins, the
 * `@` alias and the jsdom setup are all the same, and two spellings of them is how one of
 * the two suites comes to resolve an import the other does not.
 */
export default {
  ...base,
  test: {
    ...base.test,
    name: 'ui-live',
    include: ['src/**/*-live.test.{ts,tsx}'],
    exclude: ['**/node_modules/**', '**/dist/**'],
  },
}
