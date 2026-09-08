import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import path from 'node:path'

import { createWatching } from '@rk/core'
import { afterAll, describe, expect, it } from 'vitest'

import { REAL_CLOCK } from './governed-watch'
import { createSourceWatcher, REBUILD_QUIET_MS } from './source-watch'

/**
 * RG57: real directories and a real watcher, because a fake filesystem cannot say whether
 * a recursive watch reaches three folders down — which is the one thing this adds over the
 * governed watcher beside it.
 */
const scratch: string[] = []

function tree(): string {
  const root = mkdtempSync(path.join(tmpdir(), 'rk-source-'))
  scratch.push(root)
  mkdirSync(path.join(root, 'packages', 'shell', 'src', 'deep', 'deeper'), { recursive: true })
  mkdirSync(path.join(root, 'packages', 'core', 'src'), { recursive: true })
  mkdirSync(path.join(root, 'packages', 'ui', 'src'), { recursive: true })
  return root
}

/** Wait for one fan-out, or answer that none came. */
function moved(watching: { onChanged(listener: (root: string) => void): () => void }): {
  within(ms: number): Promise<string | null>
} {
  let seen: string | null = null
  const stop = watching.onChanged((root) => {
    seen ??= root
  })

  return {
    async within(ms) {
      const until = Date.now() + ms
      while (seen === null && Date.now() < until) {
        await new Promise((resolve) => setTimeout(resolve, 25))
      }
      stop()
      return seen
    },
  }
}

const WATCHED = ['packages/shell/src', 'packages/core/src']
/** Comfortably past the debounce, and short enough that a failure is quick. */
const PATIENCE = REBUILD_QUIET_MS * 8

afterAll(() => {
  for (const root of scratch) rmSync(root, { recursive: true, force: true })
})

describe('RG57: what a source watch sees', () => {
  it('notices a file written at the top of a watched tree', async () => {
    const root = tree()
    const watching = createWatching(createSourceWatcher(), REAL_CLOCK, REBUILD_QUIET_MS)
    const held = watching.hold(root, WATCHED)
    const change = moved(watching)

    writeFileSync(path.join(root, 'packages', 'shell', 'src', 'main.ts'), 'export {}\n')

    expect(await change.within(PATIENCE)).toBe(root)
    held.release()
  })

  it('notices one three folders down, which is what recursive is for', async () => {
    const root = tree()
    const watching = createWatching(createSourceWatcher(), REAL_CLOCK, REBUILD_QUIET_MS)
    const held = watching.hold(root, WATCHED)
    const change = moved(watching)

    writeFileSync(
      path.join(root, 'packages', 'shell', 'src', 'deep', 'deeper', 'buried.ts'),
      'export {}\n',
    )

    expect(await change.within(PATIENCE)).toBe(root)
    held.release()
  })

  it('watches every tree it was given, not only the first', async () => {
    const root = tree()
    const watching = createWatching(createSourceWatcher(), REAL_CLOCK, REBUILD_QUIET_MS)
    const held = watching.hold(root, WATCHED)
    const change = moved(watching)

    writeFileSync(path.join(root, 'packages', 'core', 'src', 'pure.ts'), 'export {}\n')

    expect(await change.within(PATIENCE)).toBe(root)
    held.release()
  })

  it('ignores a tree nobody asked for, so a renderer edit does not restart the app', async () => {
    // `ui` hot-reloads through Vite. Rebuilding and restarting Electron for it would throw
    // away the renderer state that made the change worth looking at.
    const root = tree()
    const watching = createWatching(createSourceWatcher(), REAL_CLOCK, REBUILD_QUIET_MS)
    const held = watching.hold(root, WATCHED)
    const change = moved(watching)

    writeFileSync(path.join(root, 'packages', 'ui', 'src', 'App.tsx'), 'export {}\n')

    expect(await change.within(REBUILD_QUIET_MS * 4)).toBeNull()
    held.release()
  })

  it('counts a burst as one change, which is what a build wants', async () => {
    // `tsc -b` writes several files and an editor can save twice; a rebuild per event is a
    // rebuild per event.
    const root = tree()
    const watching = createWatching(createSourceWatcher(), REAL_CLOCK, REBUILD_QUIET_MS)
    const held = watching.hold(root, WATCHED)

    let announced = 0
    const stop = watching.onChanged(() => {
      announced += 1
    })

    const src = path.join(root, 'packages', 'shell', 'src')
    for (let file = 0; file < 6; file += 1) {
      writeFileSync(path.join(src, `burst-${String(file)}.ts`), 'export {}\n')
    }

    await new Promise((resolve) => setTimeout(resolve, PATIENCE))
    stop()
    held.release()

    expect(announced).toBe(1)
  })

  it('stops when the interest is released, so a closed run watches nothing', async () => {
    const root = tree()
    const watching = createWatching(createSourceWatcher(), REAL_CLOCK, REBUILD_QUIET_MS)
    watching.hold(root, WATCHED).release()

    expect(watching.held).toEqual([])

    const change = moved(watching)
    writeFileSync(path.join(root, 'packages', 'shell', 'src', 'after.ts'), 'export {}\n')

    expect(await change.within(REBUILD_QUIET_MS * 4)).toBeNull()
  })

  it('starts anyway when one of the trees is not there', async () => {
    // A fresh clone with no `core/src` yet is a run that should still watch `shell/src`.
    const root = tree()
    const watching = createWatching(createSourceWatcher(), REAL_CLOCK, REBUILD_QUIET_MS)
    const held = watching.hold(root, [...WATCHED, 'packages/nothing/src'])
    const change = moved(watching)

    writeFileSync(path.join(root, 'packages', 'shell', 'src', 'still.ts'), 'export {}\n')

    expect(await change.within(PATIENCE)).toBe(root)
    held.release()
  })
})
