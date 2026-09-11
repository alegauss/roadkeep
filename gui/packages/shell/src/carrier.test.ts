import {
  buildArgv,
  buildCall,
  createWatching,
  EngineCallFailed,
  EMPTY_CATALOGUE,
  openProject,
  type Opening,
  type ProjectCatalogue,
  type Reconciled,
  type RecordedProject,
  type Transport,
  type Watcher,
} from '@rk/core'
import { describe, expect, it } from 'vitest'

import { createCarrier, type CarrierOptions } from './carrier'

/**
 * RG143: the main-process end of every read a window makes, with nothing started.
 *
 * The opening is `core`'s own over a machine that answers by verb, and the walk is a record
 * handed back, so what is asserted is the carrier's part alone: which folders it will open,
 * that it opens each once, what it refuses before anything starts, and that it gives back
 * what it holds.
 */

const A = '/work/alpha'
const B = '/work/beta'

function recorded(path: string, presence: 'present' | 'missing'): RecordedProject {
  return { path, aliases: [], commonDir: null, root: '/work', confirmed: '', presence }
}

const FOUND: ProjectCatalogue = {
  version: 1,
  roots: [{ path: '/work', depth: 1 }],
  projects: [recorded(A, 'present'), recorded(B, 'missing')],
}

const ENGINES = JSON.stringify({
  writing: { version: '0.2.400', home: '/engines/one', revision: 'abc1234', on_disk: '0.2.400' },
  invoke: 'python /x/launch.py',
  declaration: '',
  verdict: 'agreed',
  agree: true,
  readable: true,
  split: false,
  swapped: false,
})

const SAID: Record<string, string> = {
  engines: ENGINES,
  config: JSON.stringify({
    version: '0.2.400',
    source: 'roadkeep.toml',
    keys: [{ table: 'files', key: 'roadmap', declared: true, set: '"docs/ROADMAP.md"' }],
  }),
  commands: JSON.stringify({ version: '0.2.400', source: null, commands: [] }),
  list: JSON.stringify({ file: 'docs/ROADMAP.md', total: 0, uncounted: [], tasks: [] }),
}

/** Everything the carrier was made to do, counted. */
function world(over: Partial<CarrierOptions> = {}) {
  const walked: ProjectCatalogue[] = []
  const opened: string[] = []
  const closed: string[] = []
  const ran: string[][] = []

  const machine: Transport = {
    run(request) {
      ran.push([...request.argv])
      const verb = request.argv[2] ?? ''
      if (verb === 'lint') return Promise.reject(new EngineCallFailed('timeout', 'ran past 5ms', 5))
      const answer = SAID[verb]
      if (answer === undefined) return Promise.reject(new EngineCallFailed('unspawnable', 'no', 1))
      return Promise.resolve({ code: 0, stdout: answer, stderr: '', durationMs: 1 })
    },
  }

  const carrier = createCarrier({
    looking: () => ({ roots: FOUND.roots, skip: [], width: 2 }),
    rescan: (previous): Promise<Reconciled> => {
      walked.push(previous)
      return Promise.resolve({ catalogue: FOUND, changes: [] })
    },
    open: (root): Promise<Opening> => {
      opened.push(root)
      return openProject(root, [['python', '/x/launch.py']], () => machine, {
        closing: () => {
          closed.push(root)
          return Promise.resolve()
        },
      })
    },
    ...over,
  })

  return { carrier, walked, opened, closed, ran }
}

function listing(root: string) {
  return { argv: buildArgv(root, 'list', {}), call: buildCall('list', {}) }
}

describe('RG143: which projects there are', () => {
  it('answers what the walk of the named roots found, missing ones included', async () => {
    const { carrier } = world()

    expect(await carrier.projects()).toEqual(FOUND)
  })

  it('folds each walk into the record the one before it left', async () => {
    const { carrier, walked } = world()

    await carrier.projects()
    await carrier.projects()

    expect(walked).toEqual([EMPTY_CATALOGUE, FOUND])
  })

  it('shares one walk between two callers asking at once', async () => {
    let walks = 0
    const { carrier } = world({
      rescan: () => {
        walks += 1
        return new Promise((done) => setTimeout(() => done({ catalogue: FOUND, changes: [] }), 5))
      },
    })

    await Promise.all([carrier.projects(), carrier.projects()])

    expect(walks).toBe(1)
  })
})

describe('RG164: the record the last launch left', () => {
  /** A walk nobody can finish, so what answers is the record or nothing. */
  const neverWalks = (): Promise<Reconciled> => new Promise(() => undefined)

  it('answers the remembered record at once, with the walk running behind it', async () => {
    const walks: ProjectCatalogue[] = []
    const { carrier } = world({
      remembered: () => FOUND,
      rescan: (previous) => {
        walks.push(previous)
        return neverWalks()
      },
    })

    // The walk never lands, so an answer at all is the record: a launch draws eleven
    // projects while the disk is still being read.
    expect(await carrier.projects()).toEqual(FOUND)
    // And it started, folding against what was remembered rather than against nothing.
    expect(walks).toEqual([FOUND])
  })

  it('opens a project the record remembers before any walk has finished', async () => {
    const { carrier, opened } = world({ remembered: () => FOUND, rescan: neverWalks })

    expect((await carrier.open(A)).kind).toBe('open')
    expect(opened).toEqual([A])
  })

  it('keeps each folded record, so a project that went missing is still on the list', async () => {
    const kept: ProjectCatalogue[] = []
    const { carrier } = world({ remember: (catalogue) => kept.push(catalogue) })

    await carrier.projects()

    expect(kept).toEqual([FOUND])
    expect(kept[0]?.projects.some((one) => one.presence === 'missing')).toBe(true)
  })

  it('waits for the walk where the record is empty, since a list of nothing is no answer', async () => {
    const { carrier } = world({ remembered: () => EMPTY_CATALOGUE })

    expect(await carrier.projects()).toEqual(FOUND)
  })

  it('stands on the record when a walk behind it throws, rather than failing a caller', async () => {
    const { carrier } = world({
      remembered: () => FOUND,
      rescan: () => Promise.reject(new Error('the disk went away')),
    })

    // Nobody awaited that walk, so its failure must not reach a caller or the process as an
    // unhandled rejection: the record is what there is to draw, and it is drawn.
    expect(await carrier.projects()).toEqual(FOUND)
    expect(await carrier.projects()).toEqual(FOUND)
  })
})

describe('RG143: what the carrier will not open, before anything starts', () => {
  it('withholds a folder the walk never found', async () => {
    const { carrier, opened } = world()

    expect(await carrier.open('/somewhere/else')).toMatchObject({ kind: 'withheld' })
    expect(opened).toEqual([])
  })

  it('withholds a project the walk found missing', async () => {
    const { carrier, opened } = world()

    expect(await carrier.open(B)).toMatchObject({ kind: 'withheld', root: B })
    expect(opened).toEqual([])
  })

  it('runs nothing against a folder it would not open', async () => {
    const { carrier, ran } = world()

    const answer = await carrier.run('/somewhere/else', listing('/somewhere/else'))

    expect(answer).toMatchObject({ kind: 'failed', reason: 'withheld' })
    expect(ran).toEqual([])
  })

  it('runs nothing the tables did not compose, and does not open the project to find out', async () => {
    const { carrier, opened } = world()

    const answer = await carrier.run(A, { argv: ['-C', A, 'install', '--json'] })

    expect(answer).toMatchObject({ kind: 'failed', reason: 'withheld' })
    expect(opened).toEqual([])
  })
})

describe('RG143: what it opens, and keeps', () => {
  it('walks first when asked to open before it was asked to list', async () => {
    const { carrier, walked } = world()

    const answer = await carrier.open(A)

    expect(answer.kind).toBe('open')
    expect(walked).toHaveLength(1)
  })

  it('answers the opening as facts, the engine it resolved among them', async () => {
    const { carrier } = world()

    const answer = await carrier.open(A)

    expect(answer.kind).toBe('open')
    if (answer.kind !== 'open') return
    expect(answer.engine.payload.writing.home).toBe('/engines/one')
    expect(answer.governed).toEqual({ roadmap: 'docs/ROADMAP.md' })
  })

  it('opens a project once, and runs every request through what it holds', async () => {
    const { carrier, opened, ran } = world()

    await carrier.open(A)
    const answer = await carrier.run(A, listing(A))

    expect(opened).toEqual([A])
    expect(answer).toMatchObject({ kind: 'ran', result: { code: 0 } })
    expect(ran.at(-1)).toEqual(buildArgv(A, 'list', {}))
  })

  it('carries a call that failed as its fields, for the far side to rebuild', async () => {
    const { carrier } = world()

    const answer = await carrier.run(A, { argv: buildArgv(A, 'lint', {}) })

    expect(answer).toEqual({
      kind: 'failed',
      reason: 'timeout',
      message: 'ran past 5ms',
      durationMs: 5,
    })
  })

  it('does not keep a way of not opening, so a fixed project opens next time', async () => {
    let attempts = 0
    const { carrier } = world({
      open: (root) => {
        attempts += 1
        return Promise.resolve({ kind: 'unresolved', root, reason: 'no python', tried: [] })
      },
    })

    await carrier.open(A)
    const answer = await carrier.run(A, listing(A))

    expect(attempts).toBe(2)
    expect(answer).toMatchObject({ kind: 'failed', reason: 'withheld' })
    if (answer.kind === 'failed') expect(answer.message).toContain('no python')
  })

  it('gives back every engine it holds when it closes', async () => {
    const { carrier, closed } = world()

    await carrier.open(A)
    await carrier.close()

    expect(closed).toEqual([A])
  })
})

/** A disk driven by hand, under `core`'s own watching, with a clock that never waits. */
function disk() {
  const moving = new Map<string, () => void>()
  const watched: { root: string; files: readonly string[] }[] = []
  const stopped: string[] = []
  const watcher: Watcher = {
    start(root, files, moved) {
      watched.push({ root, files })
      moving.set(root, moved)
    },
    stop(root) {
      stopped.push(root)
      moving.delete(root)
    },
  }
  const watching = createWatching(watcher, {
    after(_ms, run) {
      run()
      return () => undefined
    },
  })
  return { watching, watched, stopped, move: (root: string) => moving.get(root)?.() }
}

describe('RG144: hearing a project move', () => {
  it('watches the files its config declared, and says when they move', async () => {
    const files = disk()
    const { carrier } = world({ watching: files.watching })
    let moves = 0

    const stop = await carrier.follow(A, () => {
      moves += 1
    })
    files.move(A)

    expect(stop).not.toBeNull()
    expect(files.watched).toEqual([{ root: A, files: ['docs/ROADMAP.md', 'roadkeep.toml'] }])
    expect(moves).toBe(1)
  })

  it('watches nothing for a folder it would not open', async () => {
    const files = disk()
    const { carrier } = world({ watching: files.watching })

    expect(await carrier.follow('/somewhere/else', () => undefined)).toBeNull()
    expect(await carrier.follow(B, () => undefined)).toBeNull()
    expect(files.watched).toEqual([])
  })

  it('gives the handle back when the last one listening stops', async () => {
    const files = disk()
    const { carrier } = world({ watching: files.watching })

    const first = await carrier.follow(A, () => undefined)
    const second = await carrier.follow(A, () => undefined)
    first?.()
    const afterFirst = [...files.stopped]
    second?.()

    // Two listeners share one handle, and the second release is what closes it.
    expect(files.watched).toHaveLength(1)
    expect(afterFirst).toEqual([])
    expect(files.stopped).toEqual([A])
  })

  it('stops hearing everything when it closes', async () => {
    const files = disk()
    const { carrier } = world({ watching: files.watching })

    await carrier.follow(A, () => undefined)
    await carrier.close()

    expect(files.stopped).toEqual([A])
  })
})
