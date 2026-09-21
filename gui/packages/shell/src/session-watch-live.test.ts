import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import path from 'node:path'

import { sessionMoves } from '@rk/core'
import { afterAll, describe, expect, it } from 'vitest'

import { removeTree } from './scratch'
import { watchSessionRoot } from './session-watch'

/**
 * RG247: the recursive watch, against a real directory.
 *
 * The policy is `core`'s and driven by fakes; what only a filesystem answers is whether a
 * recursive `fs.watch` on this platform reports a file written in a folder under the root, and
 * whether closing it stops that. Both are the claim the section rests on.
 */

const made: string[] = []

afterAll(() => {
  for (const one of made) removeTree(one)
})

function watchable(): string {
  const one = mkdtempSync(path.join(tmpdir(), 'rk-session-watch-'))
  made.push(one)
  return one
}

/** Wait until the moves hold the path, or give up: a watch is asynchronous, a test is not. */
async function until(has: () => boolean, ceilingMs = 5000): Promise<boolean> {
  const until_ = Date.now() + ceilingMs
  while (Date.now() < until_) {
    if (has()) return true
    await new Promise((resolve) => setTimeout(resolve, 25))
  }
  return has()
}

describe('RG247: watching one session root for real', () => {
  it('sees a file written deeper than the root, and stops once the watch is given back', async () => {
    const where = watchable()
    mkdirSync(path.join(where, 'src'), { recursive: true })
    const moves = sessionMoves()
    const watching = watchSessionRoot(where, (spelled, at) => {
      moves.moved(spelled.replaceAll('\\', '/'), at)
    })

    try {
      writeFileSync(path.join(where, 'src', 'a.ts'), 'const a = 1\n', 'utf8')
      const saw = await until(() => moves.paths.some((one) => one.path.endsWith('src/a.ts')))

      expect(saw).toBe(true)
      const seen = moves.paths.find((one) => one.path.endsWith('src/a.ts'))
      expect(seen?.first).not.toBe('')
      expect(Number.isNaN(Date.parse(seen?.last ?? ''))).toBe(false)
    } finally {
      watching.stop()
    }

    const before = moves.paths.length
    writeFileSync(path.join(where, 'src', 'b.ts'), 'const b = 2\n', 'utf8')
    await new Promise((resolve) => setTimeout(resolve, 250))

    expect(moves.paths).toHaveLength(before)
  }, 20000)

  it('names the file that was written and not the folder it is in', async () => {
    const where = watchable()
    const moves = sessionMoves()
    const watching = watchSessionRoot(where, (spelled, at) => {
      moves.moved(spelled, at)
    })

    try {
      // Writing a file changes its directory too, and the watch reports both.
      mkdirSync(path.join(where, 'made'), { recursive: true })
      writeFileSync(path.join(where, 'made', 'b.ts'), 'const b = 2\n', 'utf8')
      await until(() => moves.paths.some((one) => one.path.endsWith('made/b.ts')))

      expect(moves.paths.map((one) => one.path)).not.toContain('made')
    } finally {
      watching.stop()
    }
  }, 20000)

  it('answers a root that is not there without throwing, and stops cleanly', () => {
    const watching = watchSessionRoot(path.join(tmpdir(), 'rk-session-watch-not-here'), () => {
      throw new Error('nothing to report')
    })

    expect(() => {
      watching.stop()
      watching.stop()
    }).not.toThrow()
  })
})

describe('RG281: what the real watch says each file was', () => {
  it('sees a file it watched appear, and one it watched go away', async () => {
    const where = watchable()
    // There before the session: its birth is early, so a change to it is a change.
    writeFileSync(path.join(where, 'old.ts'), 'const old = 1\n', 'utf8')
    await new Promise((resolve) => setTimeout(resolve, 50))
    const started = new Date().toISOString()
    const moves = sessionMoves([], started)
    const watching = watchSessionRoot(where, (spelled, at, seen) => {
      moves.moved(spelled, at, seen)
    })
    const kindOf = (name: string) =>
      moves.paths.find((one) => one.path.endsWith(name))?.kind ?? null

    try {
      writeFileSync(path.join(where, 'made.ts'), 'const made = 1\n', 'utf8')
      writeFileSync(path.join(where, 'old.ts'), 'const old = 2\n', 'utf8')
      await until(() => kindOf('made.ts') !== null && kindOf('old.ts') !== null)

      expect(kindOf('made.ts')).toBe('appeared')
      // A filesystem that keeps no birth time answers zero, which reads as already there —
      // never a false new, which is the one wrong answer here.
      expect(kindOf('old.ts')).toBe('changed')

      rmSync(path.join(where, 'old.ts'))
      await until(() => kindOf('old.ts') === 'gone')

      expect(kindOf('old.ts')).toBe('gone')
      rmSync(path.join(where, 'made.ts'))
      await until(() => kindOf('made.ts') === 'came-and-went')

      expect(kindOf('made.ts')).toBe('came-and-went')
    } finally {
      watching.stop()
    }
  }, 20000)
})
