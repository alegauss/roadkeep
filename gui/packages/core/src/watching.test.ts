import { describe, expect, it } from 'vitest'

import { CHANGE_LETTER } from './acts'
import {
  CONFIG_FILE,
  createWatching,
  MOVED_CEILING,
  MOVED_LETTER,
  QUIET_MS,
  sessionMoves,
  watchedFiles,
  type Clock,
  type Watcher,
} from './watching'

/** A clock driven by hand, so nothing here waits. */
function handClock(): Clock & { tick(): void; readonly pending: number } {
  let queued: (() => void)[] = []
  return {
    after(_ms, run) {
      queued.push(run)
      return () => {
        queued = queued.filter((one) => one !== run)
      }
    },
    tick() {
      const running = queued
      queued = []
      for (const run of running) run()
    },
    get pending() {
      return queued.length
    },
  }
}

/** A watcher that records what it was asked to hold, and can be made to fire. */
function fakeWatcher() {
  const started: { root: string; files: readonly string[] }[] = []
  const stopped: string[] = []
  const movers = new Map<string, () => void>()

  const watcher: Watcher = {
    start(root, files, moved) {
      started.push({ root, files })
      movers.set(root, moved)
    },
    stop(root) {
      stopped.push(root)
      movers.delete(root)
    },
  }

  return {
    watcher,
    started,
    stopped,
    move(root: string) {
      movers.get(root)?.()
    },
    get watching() {
      return [...movers.keys()]
    },
  }
}

describe('RG45: what to watch is read, never guessed', () => {
  it('watches the governed files and the config that decides which they are', () => {
    // Editing `roadkeep.toml` changes *which* files are governed, so a watch that missed
    // it would be watching the wrong set.
    expect(watchedFiles(['docs/ROADMAP.md', 'docs/CHANGELOG.md'])).toEqual([
      'docs/CHANGELOG.md',
      'docs/ROADMAP.md',
      CONFIG_FILE,
    ])
  })

  it('watches the config even for a project that governs nothing else', () => {
    expect(watchedFiles([])).toEqual([CONFIG_FILE])
  })

  it('says the same thing twice, whatever order the roles arrived in', () => {
    const one = watchedFiles(['b.md', 'a.md', CONFIG_FILE])
    const two = watchedFiles([CONFIG_FILE, 'a.md', 'b.md'])

    expect(one).toEqual(two)
    expect(one.filter((file) => file === CONFIG_FILE)).toHaveLength(1)
  })
})

describe('RG45: a transaction is one change', () => {
  it('fans out once for a burst of writes', () => {
    // `ship` writes three files at once. Told per file, a screen would redraw three times
    // and read a half-written backlog twice.
    const clock = handClock()
    const fake = fakeWatcher()
    const watching = createWatching(fake.watcher, clock)
    const told: string[] = []
    watching.onChanged((root) => told.push(root))
    watching.hold('/w/proj', watchedFiles(['docs/ROADMAP.md']))

    fake.move('/w/proj')
    fake.move('/w/proj')
    fake.move('/w/proj')
    expect(told).toEqual([])

    clock.tick()
    expect(told).toEqual(['/w/proj'])
  })

  it('tells again for a change after the quiet moment has passed', () => {
    const clock = handClock()
    const fake = fakeWatcher()
    const watching = createWatching(fake.watcher, clock)
    const told: string[] = []
    watching.onChanged((root) => told.push(root))
    watching.hold('/w/proj', [CONFIG_FILE])

    fake.move('/w/proj')
    clock.tick()
    fake.move('/w/proj')
    clock.tick()

    expect(told).toEqual(['/w/proj', '/w/proj'])
  })

  it('tells about each project separately', () => {
    const clock = handClock()
    const fake = fakeWatcher()
    const watching = createWatching(fake.watcher, clock)
    const told: string[] = []
    watching.onChanged((root) => told.push(root))
    watching.hold('/w/one', [CONFIG_FILE])
    watching.hold('/w/two', [CONFIG_FILE])

    fake.move('/w/two')
    clock.tick()

    expect(told).toEqual(['/w/two'])
  })

  it('holds a burst for the quiet moment the module declares', () => {
    let asked = 0
    const clock: Clock = {
      after(ms) {
        asked = ms
        return () => {}
      },
    }
    const fake = fakeWatcher()
    createWatching(fake.watcher, clock).hold('/w', [CONFIG_FILE])
    fake.move('/w')

    expect(asked).toBe(QUIET_MS)
  })
})

describe('RG45: a handle has a cost, so interest is explicit', () => {
  it('opens the handles once and closes them when the last interest goes', () => {
    // Two screens on one project share the handles, and the second release is what closes
    // them.
    const fake = fakeWatcher()
    const watching = createWatching(fake.watcher, handClock())

    const first = watching.hold('/w/proj', [CONFIG_FILE])
    const second = watching.hold('/w/proj', [CONFIG_FILE])
    expect(fake.started).toHaveLength(1)
    expect(watching.held).toEqual(['/w/proj'])

    first.release()
    expect(fake.stopped).toEqual([])
    expect(watching.held).toEqual(['/w/proj'])

    second.release()
    expect(fake.stopped).toEqual(['/w/proj'])
    expect(watching.held).toEqual([])
  })

  it('ignores a release taken twice', () => {
    const fake = fakeWatcher()
    const watching = createWatching(fake.watcher, handClock())
    const interest = watching.hold('/w', [CONFIG_FILE])
    watching.hold('/w', [CONFIG_FILE])

    interest.release()
    interest.release()

    // The second release was this interest's own, not the other holder's.
    expect(fake.stopped).toEqual([])
    expect(watching.held).toEqual(['/w'])
  })

  it('drops a burst still waiting when the project stops being watched', () => {
    // A screen that closed should not redraw afterwards.
    const clock = handClock()
    const fake = fakeWatcher()
    const watching = createWatching(fake.watcher, clock)
    const told: string[] = []
    watching.onChanged((root) => told.push(root))

    const interest = watching.hold('/w', [CONFIG_FILE])
    fake.move('/w')
    interest.release()
    clock.tick()

    expect(told).toEqual([])
  })

  it('watches nothing at all until somebody is interested', () => {
    const fake = fakeWatcher()
    const watching = createWatching(fake.watcher, handClock())

    expect(fake.started).toEqual([])
    expect(watching.held).toEqual([])
  })

  it('hands the watcher exactly the files it was told to watch', () => {
    const fake = fakeWatcher()
    const files = watchedFiles(['docs/ROADMAP.md'])
    createWatching(fake.watcher, handClock()).hold('/w', files)

    expect(fake.started[0]?.files).toEqual(files)
  })
})

describe('RG45: who is told', () => {
  it('stops telling a listener that let go', () => {
    const clock = handClock()
    const fake = fakeWatcher()
    const watching = createWatching(fake.watcher, clock)
    const told: string[] = []
    const stop = watching.onChanged((root) => told.push(root))
    watching.hold('/w', [CONFIG_FILE])

    stop()
    fake.move('/w')
    clock.tick()

    expect(told).toEqual([])
  })

  it('tells every listener holding on', () => {
    const clock = handClock()
    const fake = fakeWatcher()
    const watching = createWatching(fake.watcher, clock)
    const first: string[] = []
    const second: string[] = []
    watching.onChanged((root) => first.push(root))
    watching.onChanged((root) => second.push(root))
    watching.hold('/w', [CONFIG_FILE])

    fake.move('/w')
    clock.tick()

    expect(first).toEqual(['/w'])
    expect(second).toEqual(['/w'])
  })
})

describe('RG247: what moved on disk while a session ran', () => {
  const AT = '2026-09-15T10:00:00.000Z'
  const LATER = '2026-09-15T10:05:00.000Z'

  it('folds each path into one row, keeping when it first moved and when it last did', () => {
    const moves = sessionMoves()

    moves.moved('src/a.ts', AT)
    moves.moved('src/b.ts', AT)
    moves.moved('src/a.ts', LATER)

    expect(moves.paths).toEqual([
      { path: 'src/a.ts', first: AT, last: LATER, moves: 2, kind: null },
      { path: 'src/b.ts', first: AT, last: AT, moves: 1, kind: null },
    ])
    expect(moves.beyond).toBe(0)
  })

  it('keeps a path as the side with the filesystem spelled it (RG65, RG98)', () => {
    const moves = sessionMoves()

    moves.moved('src/deep/a.ts', AT)

    // `spelledMove` in the shell is what turns a platform's own separator into this.
    expect(moves.paths.map((one) => one.path)).toEqual(['src/deep/a.ts'])
  })

  it('never counts git, nor a folder the settings skip, nor an empty path', () => {
    const moves = sessionMoves(['node_modules'])

    moves.moved('.git/index', AT)
    moves.moved('node_modules/pkg/index.js', AT)
    moves.moved('packages/node_modules/x.js', AT)
    moves.moved('', AT)
    moves.moved('src/a.ts', AT)

    expect(moves.paths.map((one) => one.path)).toEqual(['src/a.ts'])
  })

  it('stops at the ceiling and counts the rest, so a generator cannot fill the record', () => {
    const moves = sessionMoves()

    for (let at = 0; at < MOVED_CEILING + 7; at += 1) moves.moved(`src/${String(at)}.ts`, AT)
    // A path already kept still folds into its row past the ceiling.
    moves.moved('src/0.ts', LATER)

    expect(moves.paths).toHaveLength(MOVED_CEILING)
    expect(moves.beyond).toBe(7)
    expect(moves.paths[0]?.moves).toBe(2)
  })
})

describe('RG281: what each moved file was', () => {
  const STARTED = '2026-09-15T10:00:00.000Z'
  const AT = '2026-09-15T10:00:30.000Z'
  const LATER = '2026-09-15T10:05:00.000Z'
  const BEFORE = '2026-09-15T09:00:00.000Z'

  it('reads a file born after the session started, and still there, as one that appeared', () => {
    const moves = sessionMoves([], STARTED)

    moves.moved('src/made.ts', AT, { present: true, born: AT })

    expect(moves.paths[0]?.kind).toBe('appeared')
  })

  it('reads one that was already there as changed, however often it moved', () => {
    const moves = sessionMoves([], STARTED)

    moves.moved('src/a.ts', AT, { present: true, born: BEFORE })
    moves.moved('src/a.ts', LATER, { present: true, born: BEFORE })

    expect(moves.paths[0]?.kind).toBe('changed')
    expect(moves.paths[0]?.moves).toBe(2)
  })

  it('reads one that is not there at its last move as gone', () => {
    const moves = sessionMoves([], STARTED)

    moves.moved('src/a.ts', AT, { present: true, born: BEFORE })
    moves.moved('src/a.ts', LATER, { present: false, born: '' })

    expect(moves.paths[0]?.kind).toBe('gone')
  })

  it('reads one born after the start and gone by the end as one that came and went', () => {
    const moves = sessionMoves([], STARTED)

    moves.moved('tmp/scratch.txt', AT, { present: true, born: AT })
    moves.moved('tmp/scratch.txt', LATER, { present: false, born: '' })

    // The first birth is kept: a stat of a file that is gone answers nothing about when it was.
    expect(moves.paths[0]?.kind).toBe('came-and-went')
  })

  it('reads a filesystem that keeps no birth time as a file that was already there', () => {
    // Zero is what such a filesystem answers, and a false new is the one wrong answer here.
    const moves = sessionMoves([], STARTED)

    moves.moved('src/a.ts', AT, { present: true, born: '' })
    moves.moved('src/gone.ts', AT, { present: false, born: '' })

    expect(moves.paths.map((one) => one.kind)).toEqual(['changed', 'gone'])
  })

  it('says nothing about a move nothing was read of, rather than guessing', () => {
    const moves = sessionMoves([], STARTED)

    moves.moved('src/a.ts', AT)

    expect(moves.paths[0]?.kind).toBeNull()
  })

  it('marks each kind with the letter an edited row carries, and no two alike', () => {
    expect(MOVED_LETTER.appeared).toBe(CHANGE_LETTER.created)
    expect(MOVED_LETTER.changed).toBe(CHANGE_LETTER.changed)
    expect(MOVED_LETTER.gone).toBe(CHANGE_LETTER.deleted)
    expect(MOVED_LETTER['came-and-went']).toBe(CHANGE_LETTER.undone)
    expect(new Set(Object.values(MOVED_LETTER)).size).toBe(4)
  })
})
