import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'

// Vitest does not enable globals here, so Testing Library's own auto-cleanup never
// registers. Without this, the second `render` in a file finds the first one's tree
// still mounted and every `getBy*` throws on the duplicate rather than on the bug.
afterEach(() => {
  cleanup()
})
