import { realpathSync } from 'node:fs'

import { buildArgv } from '@rk/core'
import { describe, expect, it } from 'vitest'

import { buildFixture } from './fixture'
import { CEILING, liveEngine as transport } from './live'

/**
 * RG195: the root a fixture hands out, and the one a process reports.
 *
 * `mkdtempSync(tmpdir())` answers whatever `tmpdir()` spelled. On a Windows account whose
 * name is longer than eight characters — `runneradmin` on a GitHub runner — that is the 8.3
 * short form, `C:\Users\RUNNER~1\…`, while any process that opens the directory reports the
 * long one. One directory, two spellings, and an assertion comparing them says they are
 * different places.
 *
 * It never fails where it is written: this machine's user is five characters, so nothing is
 * shortened and the strings match. The developer sees green and the runner sees red — which
 * is how it reached a tag and stood between it and its installers.
 */
describe('RG195: the two spellings of one directory', () => {
  it('hands out the spelling the filesystem uses, not the one tmpdir answered', async () => {
    const fixture = await buildFixture(transport, { open: 1, shipped: 0, deferred: 0 })
    try {
      // Equal already on an account whose name is short, and the whole of the fix on one
      // whose name is not — so this passes here and would have failed on the runner.
      expect(fixture.root).toBe(realpathSync.native(fixture.root))
    } finally {
      fixture.dispose()
    }
  })

  it('is the root the engine answers with, which is what an assertion compares', async () => {
    // The failure itself, one layer up (RG101's live read): a server started in the fixture
    // answering a long path while the test held a short one.
    const fixture = await buildFixture(transport, { open: 1, shipped: 0, deferred: 0 })
    try {
      const said = await transport.run({
        root: fixture.root,
        argv: buildArgv(fixture.root, 'config', {}),
        timeoutMs: CEILING,
      })

      expect(said.code).toBe(0)
      expect(said.stdout).toContain(fixture.root.replaceAll('\\', '/'))
    } finally {
      fixture.dispose()
    }
  })
})
