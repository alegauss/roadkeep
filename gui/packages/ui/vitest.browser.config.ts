// With the extension, for the reason `vitest.live.config.ts` gives: a Vite config is loaded by
// Vite's own native loader.
import { playwright } from '@vitest/browser-playwright'

import base from './vite.config.ts'

/**
 * The half of `ui` that needs a layout (RG213).
 *
 * jsdom lays nothing out and fakes its events, so a test about scroll, overflow or focus order
 * in the `ui` project asserts numbers the test itself invented: RG206's follow tests defined
 * `scrollHeight` by hand and would have passed against a stylesheet that never bounded the
 * region. This project runs files named `*.browser.test.tsx` in headless Chromium through
 * Playwright, with the app's CSS loaded, so a class is a real rule and a height is measured.
 *
 * **Beside jsdom, not instead of it.** Most of the renderer's tests are about what is said and
 * not where it lands, and those stay the fast half. This one starts a browser, which is the
 * line RG64 draws: `npm run test:live` runs it, `npm test` does not.
 *
 * The React and Tailwind plugins and the `@` alias are the base config's; the jsdom environment
 * and its setup are not, since a real browser has what they stand in for.
 */
export default {
  ...base,
  test: {
    name: 'ui-browser',
    include: ['src/**/*.browser.test.{ts,tsx}'],
    setupFiles: ['./src/browser-setup.ts'],
    browser: {
      enabled: true,
      provider: playwright(),
      headless: true,
      instances: [{ browser: 'chromium' }],
    },
  },
}
