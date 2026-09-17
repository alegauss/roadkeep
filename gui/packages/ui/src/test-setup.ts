import { cleanup, configure } from '@testing-library/react'
import { afterEach, beforeEach } from 'vitest'

import { recordScrolls } from './scroll-record'
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
 * How long a `findBy*` may wait, which is a budget and not an assertion (RG232).
 *
 * Testing Library allows one second. Every surface here draws after a read — the bridge, then
 * `config` and `brief` — so every one of these tests waits, and one second is wall clock on a
 * worker sharing a machine. RG232 came out of a single red test nobody could explain; put
 * under load (28 busy cores beside the suite) three runs in a row went red, and the reports
 * `.vitest/failures/` kept name the same defect every time: five files, nine failures, all of
 * them `Unable to find …` at a one-second deadline, in tests that pass in milliseconds on an
 * idle machine. None of the nine was the app doing anything wrong.
 *
 * **Five seconds is not that defect buried.** A budget only decides how long a run waits
 * before calling something absent: a screen that never draws still fails, with the same
 * message, five seconds later. What it stops being is a suite that is red when the machine is
 * busy and green when it is not, which is a suite whose red says nothing.
 *
 * It has to stay under `testTimeout`, which `vite.config.ts` raises to match — a wait that
 * outlives its test reports *test timed out* and loses the message naming what was missing.
 *
 * The browser project sets none of this: its own flake has never been seen, and it now has
 * the same report to prove one if it happens.
 */
configure({ asyncUtilTimeout: 5000 })

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

/**
 * jsdom implements no `scrollIntoView` either (RG266), and the session screen calls one on the
 * frame after an edit leads back to its act. The one given here records what it was asked, for
 * the reason and in the module `scroll-record` says.
 */
beforeEach(() => {
  recordScrolls()
})

// Vitest does not enable globals here, so Testing Library's own auto-cleanup never
// registers. Without this, the second `render` in a file finds the first one's tree
// still mounted and every `getBy*` throws on the duplicate rather than on the bug.
afterEach(() => {
  cleanup()
})
