import { afterAll } from 'vitest'

import { liveHeld } from './live'

/**
 * What the live suite's held engine is left holding when a file ends (RG130).
 *
 * `live.ts` reads through one `roadkeep mcp` per root, and a fixture gives its root back
 * before removing the directory. What no fixture owns is this repository's own root, which
 * half the suite reads, and a server started for it would outlive the file: the worker is
 * reused for the next one, and a child whose stdin nobody closes is a Python that stays.
 *
 * A setup file rather than a line in each file, for the reason the fixture cache gives for
 * being a global setup: the fact is about every file, and a file that forgot it would leak
 * where the others did not. It runs last among a file's `afterAll`s — Vitest orders "after"
 * hooks as a stack — which is after every fixture was disposed, and that is the right order.
 */
afterAll(async () => {
  await liveHeld.close()
})
