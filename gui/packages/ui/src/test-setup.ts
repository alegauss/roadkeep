import { cleanup } from '@testing-library/react'
import { afterEach, beforeEach } from 'vitest'

import { startSpeaking } from './speaking'

/**
 * i18next, started once per worker, because the design system's components resolve their own
 * strings through it and warn on every render without one (RG63, RG88).
 *
 * The package's own guidance says a consumer testing these components needs the same setup
 * it has. The base locale, so a test that says nothing about language is reasoning about the
 * plainest window; `speaking.test.tsx` moves it and puts it back.
 */
await startSpeaking('en')

/**
 * jsdom implements no `matchMedia`, and anything that follows the desktop asks for one —
 * `next-themes` does it on mount, so every render under the ground provider would throw.
 *
 * The default answers no to every query, which is a desktop set to light and no motion
 * preference: the plainest machine, and the one a test that says nothing about the desktop
 * should be reasoning about. A test that cares says so by replacing this.
 */
beforeEach(() => {
  Object.defineProperty(window, 'matchMedia', {
    configurable: true,
    writable: true,
    value: (query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addEventListener: () => undefined,
      removeEventListener: () => undefined,
      addListener: () => undefined,
      removeListener: () => undefined,
      dispatchEvent: () => false,
    }),
  })
})

// Vitest does not enable globals here, so Testing Library's own auto-cleanup never
// registers. Without this, the second `render` in a file finds the first one's tree
// still mounted and every `getBy*` throws on the duplicate rather than on the bug.
afterEach(() => {
  cleanup()
})
