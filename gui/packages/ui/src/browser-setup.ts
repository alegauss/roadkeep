import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'

// The app's own stylesheet, which is the whole reason these tests run in a browser (RG213): a
// class that bounds a region is a rule here, and a height is the one it computes to.
import './index.css'
import { startSpeaking } from './speaking'

/**
 * The browser project's setup: the jsdom setup less what a real browser already has.
 *
 * i18next is started for the reason `test-setup.ts` gives. No `matchMedia` stand-in, since
 * Chromium answers the query itself; Testing Library's cleanup, since globals are off here as
 * well.
 */
await startSpeaking('en')

afterEach(() => {
  cleanup()
})
