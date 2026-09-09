import { spawn } from 'node:child_process'
import { existsSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import path from 'node:path'

import { afterAll, describe, expect, it } from 'vitest'

import { removeTree } from './scratch'

/**
 * RG104: removing a directory the operating system has not let go of.
 *
 * The failure this is about cannot be written as a fast test, because what makes it happen
 * is another process. So this makes one: a child that holds a directory as its working
 * directory and exits a moment later, which is what an engine call had just finished doing
 * when a fixture teardown reported `EPERM` and reddened a file whose tests all passed.
 *
 * **Windows only, and the skip is the finding.** A directory that is a process's working
 * directory can be removed on Linux and macOS, so there is nothing to retry there and a
 * test asserting otherwise would be asserting about this machine rather than about the
 * code. Named rather than silently green.
 */
const HOLDS_A_CWD = process.platform === 'win32'
const scratch: string[] = []

function tree(): string {
  const root = mkdtempSync(path.join(tmpdir(), 'rk-scratch-'))
  writeFileSync(path.join(root, 'inside.txt'), 'something', 'utf8')
  scratch.push(root)
  return root
}

/** A child that sits in a directory and leaves. Long enough to lose a race, short to win. */
function holding(root: string, forMs: number): void {
  spawn(process.execPath, ['-e', `setTimeout(() => undefined, ${String(forMs)})`], {
    cwd: root,
    stdio: 'ignore',
  })
}

afterAll(() => {
  for (const root of scratch) removeTree(root)
})

describe('RG104: a directory another process is standing in', () => {
  it('removes an ordinary one, which is the control', () => {
    const root = tree()

    removeTree(root)

    expect(existsSync(root)).toBe(false)
  })

  it('forgives one that is already gone', () => {
    const root = tree()
    removeTree(root)

    expect(() => {
      removeTree(root)
    }).not.toThrow()
  })

  it.skipIf(!HOLDS_A_CWD)('is what `force` alone throws on', async () => {
    // The failure itself, reproduced. Without this the test below would pass on a machine
    // where nothing was ever locked, and prove nothing.
    const root = tree()
    holding(root, 600)
    await new Promise((done) => setTimeout(done, 150))

    expect(() => {
      rmSync(root, { recursive: true, force: true })
    }).toThrow(/EPERM|EBUSY|ENOTEMPTY/)
  })

  it.skipIf(!HOLDS_A_CWD)(
    'waits it out rather than failing a run that proved everything',
    async () => {
      const root = tree()
      holding(root, 600)
      await new Promise((done) => setTimeout(done, 150))

      removeTree(root)

      expect(existsSync(root)).toBe(false)
    },
  )
})
