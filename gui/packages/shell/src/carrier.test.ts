import { mkdtempSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import nodePath from 'node:path'

import {
  DECLARES_NOTHING,
  buildArgv,
  buildCall,
  createWatching,
  EngineCallFailed,
  EMPTY_CATALOGUE,
  openProject,
  type Opening,
  type ProjectCatalogue,
  type ProjectGate,
  type Reconciled,
  type RecordedProject,
  type Transport,
  type Watcher,
} from '@rk/core'
import { describe, expect, it } from 'vitest'

import { createCarrier, type CarrierOptions } from './carrier'
import { removeTree } from './scratch'

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
  return {
    path,
    aliases: [],
    commonDir: null,
    root: '/work',
    confirmed: '',
    presence,
    branch: '',
    declared: DECLARES_NOTHING,
  }
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

describe('RG165: a door the engine offered', () => {
  /** An answer carrying doors, which is what the machine says for `lint` here. */
  const OFFERED = JSON.stringify({
    clean: false,
    findings: [
      {
        code: 'ref.unresolved',
        remedy: {
          doors: [{ argv: ['section', 'add', 'RG9', '--title', '…'], complete: false }],
        },
      },
    ],
  })

  /** A carrier whose machine answers that for one verb, so `run` has doors to keep. */
  function offering() {
    const ran: string[][] = []
    const machine: Transport = {
      run(request) {
        ran.push([...request.argv])
        const verb = request.argv[2] ?? ''
        // Anything else answers a document with no doors in it, since what this fixture is
        // about is the door being run at all.
        const answer = verb === 'lint' ? OFFERED : (SAID[verb] ?? '{"wrote":[]}')
        return Promise.resolve({ code: 0, stdout: answer, stderr: '', durationMs: 1 })
      },
    }
    const { carrier } = world({
      open: (root) => openProject(root, [['python', '/x/launch.py']], () => machine),
    })
    return { carrier, ran }
  }

  /** The `lint` read, which is the one this fixture answers with doors. */
  const linting = (root: string) => ({
    argv: buildArgv(root, 'lint', {}),
    call: buildCall('lint', {}),
  })

  it('names the doors an answer carried, so a caller can take one without an argv', async () => {
    const { carrier } = offering()

    const answered = await carrier.run(A, linting(A))

    expect(answered.kind).toBe('ran')
    if (answered.kind !== 'ran') throw new Error('unreachable')
    expect(answered.offered).toBeDefined()
  })

  it('runs the argv it kept, with the words only where the engine left a blank', async () => {
    const { carrier, ran } = offering()
    const answered = await carrier.run(A, linting(A))
    if (answered.kind !== 'ran' || answered.offered === undefined) throw new Error('no doors')

    const taken = await carrier.door(A, answered.offered, 0, ['A design'])

    expect(taken.kind).toBe('ran')
    // The engine's own command line, filled: this is the verb the guard in front of `run`
    // refuses, which is the whole of why the door is taken by name.
    expect(ran.at(-1)).toEqual(['-C', A, 'section', 'add', 'RG9', '--title', 'A design', '--json'])
  })

  it('refuses a name nobody offered, and one from another project', async () => {
    const { carrier, ran } = offering()
    const answered = await carrier.run(A, linting(A))
    if (answered.kind !== 'ran' || answered.offered === undefined) throw new Error('no doors')
    const before = ran.length

    expect((await carrier.door(A, 'made-up', 0, ['x'])).kind).toBe('failed')
    expect((await carrier.door(B, answered.offered, 0, ['x'])).kind).toBe('failed')
    expect(ran).toHaveLength(before)
  })

  it('refuses words that are not one per blank, rather than running a placeholder', async () => {
    const { carrier, ran } = offering()
    const answered = await carrier.run(A, linting(A))
    if (answered.kind !== 'ran' || answered.offered === undefined) throw new Error('no doors')
    const before = ran.length

    const none = await carrier.door(A, answered.offered, 0, [])
    const two = await carrier.door(A, answered.offered, 0, ['one', 'two'])

    expect(none.kind).toBe('failed')
    expect(two.kind).toBe('failed')
    expect(ran).toHaveLength(before)
  })

  it('says nothing about doors on an answer that carried none', async () => {
    const { carrier } = offering()

    const answered = await carrier.run(A, listing(A))

    expect(answered.kind === 'ran' && answered.offered).toBeUndefined()
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
      code: '',
      fields: {},
      durationMs: 5,
    })
  })

  it('does not keep a way of not opening, so a fixed project opens next time', async () => {
    let attempts = 0
    const { carrier } = world({
      open: (root) => {
        attempts += 1
        return Promise.resolve({
          kind: 'unresolved' as const,
          root,
          reason: 'no python',
          code: 'none-answered' as const,
          tried: [],
        })
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

describe('RG152: what the gate last said', () => {
  /** A gate answer, clean or not, in the shape `lint --json` prints. */
  const report = (clean: boolean, problems = 0) =>
    JSON.stringify({
      root: A,
      clean,
      checked: ['docs/ROADMAP.md'],
      lines: 4,
      sections: 2,
      problems,
      codes: {},
      findings: [],
      notes: [],
    })

  /** A carrier whose machine answers `lint`, since the default one refuses it. */
  function gating(over: Partial<CarrierOptions> = {}, answer = report(true)) {
    const machine: Transport = {
      run(request) {
        const verb = request.argv[2] ?? ''
        if (verb === 'lint')
          return Promise.resolve({ code: 0, stdout: answer, stderr: '', durationMs: 1 })
        const said = SAID[verb]
        if (said === undefined) return Promise.reject(new EngineCallFailed('unspawnable', 'no', 1))
        return Promise.resolve({ code: 0, stdout: said, stderr: '', durationMs: 1 })
      },
    }
    return world({
      open: (root) => openProject(root, [['python', '/x/launch.py']], () => machine),
      ...over,
    }).carrier
  }

  const linting = (root: string) => ({
    argv: buildArgv(root, 'lint', {}),
    call: buildCall('lint', {}),
  })

  it('says nothing about a project nothing has gated, which is what unknown means', async () => {
    const carrier = gating()

    await carrier.run(A, listing(A))

    expect(await carrier.gates()).toEqual([])
  })

  it('dates the verdict off the answer a window asked for, without running a gate of its own', async () => {
    const carrier = gating({ now: () => '2026-09-11T12:00:00.000Z' })

    await carrier.run(A, linting(A))

    expect(await carrier.gates()).toEqual([
      {
        root: A,
        health: { verdict: 'clean', problems: 0, taken: '2026-09-11T12:00:00.000Z', stale: false },
      },
    ])
  })

  it('carries the count a drifted report gave, which is what a row shows', async () => {
    const carrier = gating({}, report(false, 3))

    await carrier.run(A, linting(A))
    const [gate] = await carrier.gates()

    expect(gate?.health.verdict).toBe('drifted')
    expect(gate?.health.problems).toBe(3)
  })

  it('notes nothing for a read that was not a gate, whatever it answered', async () => {
    const carrier = gating({}, report(true))

    // The list answer is not a lint payload, and a reader that took it for one would
    // record a clean verdict nobody ran.
    await carrier.run(A, listing(A))

    expect(await carrier.gates()).toEqual([])
  })
})

describe('RG166: the gate the carrier runs itself', () => {
  const report = (clean: boolean, problems = 0) =>
    JSON.stringify({
      root: A,
      clean,
      checked: ['docs/ROADMAP.md'],
      lines: 4,
      sections: 2,
      problems,
      codes: {},
      findings: [],
      notes: [],
    })

  /** A carrier that answers `lint`, counting the runs and the verdicts it told. */
  function watching(over: Partial<CarrierOptions> = {}) {
    const lints: string[][] = []
    const told: ProjectGate[] = []
    const machine: Transport = {
      run(request) {
        const verb = request.argv[2] ?? ''
        if (verb === 'lint') {
          lints.push([...request.argv])
          return Promise.resolve({ code: 0, stdout: report(true), stderr: '', durationMs: 1 })
        }
        const said = SAID[verb]
        if (said === undefined) return Promise.reject(new EngineCallFailed('unspawnable', 'no', 1))
        return Promise.resolve({ code: 0, stdout: said, stderr: '', durationMs: 1 })
      },
    }
    const carrier = createCarrier({
      looking: () => ({ roots: FOUND.roots, skip: [], width: 2 }),
      rescan: () => Promise.resolve({ catalogue: FOUND, changes: [] }),
      open: (root) => openProject(root, [['python', '/x/launch.py']], () => machine),
      onGate: (gate) => told.push(gate),
      ...over,
    })
    return { carrier, lints, told }
  }

  /** Wait for the gate the carrier started beside the answer it gave. */
  const settle = () => new Promise((done) => setTimeout(done, 20))

  it('gates a project it just opened, without the opening waiting for it', async () => {
    const { carrier, lints, told } = watching()

    const answer = await carrier.open(A)

    // The opening is what a screen waits for, and it answered before the gate ran.
    expect(answer.kind).toBe('open')
    await settle()
    expect(lints).toHaveLength(1)
    expect(told.map((one) => one.health.verdict)).toEqual(['clean'])
  })

  it('does not run it again while the files have not moved', async () => {
    const { carrier, lints } = watching()

    await carrier.open(A)
    await settle()
    await carrier.open(A)
    await settle()

    // needsGate compares the verdict against the stamp, and nothing wrote in between.
    expect(lints).toHaveLength(1)
  })

  it('says nothing about a project that would not open, rather than a verdict nobody ran', async () => {
    const { carrier, lints, told } = watching({
      open: (root): Promise<Opening> =>
        Promise.resolve({
          kind: 'unresolved',
          root,
          reason: 'no python',
          code: 'none-answered',
          tried: [],
        }),
    })

    await carrier.open(A)
    await settle()

    expect(lints).toEqual([])
    expect(told).toEqual([])
    expect(await carrier.gates()).toEqual([])
  })

  it('keeps the project unknown where the gate itself will not run', async () => {
    const machine: Transport = {
      run(request) {
        const verb = request.argv[2] ?? ''
        if (verb === 'lint') return Promise.reject(new EngineCallFailed('timeout', 'ran past', 5))
        const said = SAID[verb]
        if (said === undefined) return Promise.reject(new EngineCallFailed('unspawnable', 'no', 1))
        return Promise.resolve({ code: 0, stdout: said, stderr: '', durationMs: 1 })
      },
    }
    const { carrier, told } = watching({
      open: (root) => openProject(root, [['python', '/x/launch.py']], () => machine),
    })

    await carrier.open(A)
    await settle()

    expect(told).toEqual([])
    expect(await carrier.gates()).toEqual([])
  })
})

describe('RG180: saying the walk behind the record landed', () => {
  it('says so where the fold changed something, with how many it moved', async () => {
    const told: number[] = []
    const { carrier } = world({
      remembered: () => EMPTY_CATALOGUE,
      onCatalogue: (changed) => told.push(changed),
      rescan: () => Promise.resolve({ catalogue: FOUND, changes: [{ kind: 'added', path: A }] }),
    })

    await carrier.projects()

    expect(told).toEqual([1])
  })

  it('says nothing where the walk found what the record already held', async () => {
    // A window that redrew on every walk would redraw on a timer nobody set.
    const told: number[] = []
    const { carrier } = world({
      onCatalogue: (changed) => told.push(changed),
      rescan: () => Promise.resolve({ catalogue: FOUND, changes: [] }),
    })

    await carrier.projects()

    expect(told).toEqual([])
  })
})

describe('RG187: how many projects gate at once', () => {
  const TWO = '/work/gamma'
  const report = JSON.stringify({
    root: A,
    clean: true,
    checked: ['docs/ROADMAP.md'],
    lines: 4,
    sections: 2,
    problems: 0,
    codes: {},
    findings: [],
    notes: [],
  })

  /** A machine whose `lint` waits to be let go, so what is in flight can be counted. */
  function slowGates(over: Partial<CarrierOptions> = {}) {
    let running = 0
    let most = 0
    const waiting: (() => void)[] = []
    const machine: Transport = {
      async run(request) {
        const verb = request.argv[2] ?? ''
        if (verb !== 'lint') {
          const said = SAID[verb]
          if (said === undefined) throw new EngineCallFailed('unspawnable', 'no', 1)
          return { code: 0, stdout: said, stderr: '', durationMs: 1 }
        }
        running += 1
        most = Math.max(most, running)
        await new Promise<void>((go) => waiting.push(go))
        running -= 1
        return { code: 0, stdout: report, stderr: '', durationMs: 1 }
      },
    }
    // Two projects a launch would open together, both present: what is counted is how many
    // gates run at once across them.
    const both: ProjectCatalogue = {
      version: 1,
      roots: FOUND.roots,
      projects: [recorded(A, 'present'), recorded(TWO, 'present')],
    }
    const carrier = createCarrier({
      looking: () => ({ roots: both.roots, skip: [], width: 2 }),
      rescan: () => Promise.resolve({ catalogue: both, changes: [] }),
      open: (root) => openProject(root, [['python', '/x/launch.py']], () => machine),
      ...over,
    })
    return { carrier, letGo: () => waiting.splice(0).forEach((go) => go()), most: () => most }
  }

  const settle = () => new Promise((done) => setTimeout(done, 20))

  it('runs one at a time by default, whatever a launch opens together', async () => {
    const { carrier, most, letGo } = slowGates()

    // Both projects opened at once, which is what a cold start does.
    await Promise.all([carrier.open(A), carrier.open(TWO)])
    await settle()

    expect(most()).toBe(1)
    letGo()
  })

  it('takes the width it was given, so a machine with room can be told so', async () => {
    const { carrier, most, letGo } = slowGates({ gatesAtOnce: 2 })

    await Promise.all([carrier.open(A), carrier.open(TWO)])
    await settle()

    expect(most()).toBeGreaterThan(1)
    letGo()
  })
})

/** A machine whose `config` declares the logo a test names (RG204). */
function withLogo(logo: string): Transport {
  return {
    run(request) {
      const verb = request.argv[2] ?? ''
      if (verb === 'config') {
        return Promise.resolve({
          code: 0,
          stdout: JSON.stringify({
            version: '0.2.472',
            source: 'roadkeep.toml',
            keys: [
              { table: 'files', key: 'roadmap', declared: true, set: '"docs/ROADMAP.md"' },
              { table: 'project', key: 'logo', declared: true, set: `"${logo}"` },
            ],
          }),
          stderr: '',
          durationMs: 1,
        })
      }
      const said = SAID[verb]
      if (said === undefined) throw new EngineCallFailed('unspawnable', 'no', 1)
      return Promise.resolve({ code: 0, stdout: said, stderr: '', durationMs: 1 })
    },
  }
}

/** A machine whose `config` declares the name a test names (RG203). */
function declaring(name: string): Transport {
  return {
    run(request) {
      const verb = request.argv[2] ?? ''
      if (verb === 'config') {
        return Promise.resolve({
          code: 0,
          stdout: JSON.stringify({
            version: '0.2.472',
            source: 'roadkeep.toml',
            keys: [
              { table: 'files', key: 'roadmap', declared: true, set: '"docs/ROADMAP.md"' },
              {
                table: 'project',
                key: 'name',
                declared: name !== '',
                set: name === '' ? null : `"${name}"`,
              },
            ],
          }),
          stderr: '',
          durationMs: 1,
        })
      }
      const said = SAID[verb]
      if (said === undefined) throw new EngineCallFailed('unspawnable', 'no', 1)
      return Promise.resolve({ code: 0, stdout: said, stderr: '', durationMs: 1 })
    },
  }
}

describe('RG203: what the record remembers about a project', () => {
  it('keeps the name a project declared, the moment it opens', async () => {
    const kept: ProjectCatalogue[] = []
    const { carrier } = world({
      remember: (one) => kept.push(one),
      open: (root) => openProject(root, [['python', '/x/launch.py']], () => declaring('Turing')),
    })

    await carrier.projects()
    await carrier.open(A)

    // A walk reads no config, so the record could only learn this here.
    const last = kept.at(-1)
    expect(last?.projects.find((one) => one.path === A)?.declared.name).toBe('Turing')
  })

  it('writes nothing where the declaration has not changed', async () => {
    const kept: ProjectCatalogue[] = []
    const { carrier } = world({
      remember: (one) => kept.push(one),
      open: (root) => openProject(root, [['python', '/x/launch.py']], () => declaring('Turing')),
    })

    await carrier.projects()
    await carrier.open(A)
    const after = kept.length
    await carrier.open(A)

    // The record is written when it moves, not once per open: a screen that reopens a
    // project would otherwise rewrite the file for nothing.
    expect(kept.length).toBe(after)
  })

  it('takes what a project declares now, including nothing', async () => {
    // A memory and never an override. The record already holds a name; the project this
    // opens declares none, so the record gives way rather than keeping a name no file says.
    const kept: ProjectCatalogue[] = []
    const held: ProjectCatalogue = {
      ...FOUND,
      projects: FOUND.projects.map((one) =>
        one.path === A ? { ...one, declared: { ...DECLARES_NOTHING, name: 'Turing' } } : one,
      ),
    }
    const { carrier } = world({
      remembered: () => held,
      rescan: () => Promise.resolve({ catalogue: held, changes: [] }),
      remember: (one) => kept.push(one),
      open: (root) => openProject(root, [['python', '/x/launch.py']], () => declaring('')),
    })

    await carrier.projects()
    await carrier.open(A)

    expect(kept.at(-1)?.projects.find((one) => one.path === A)?.declared.name).toBe('')
  })
})

describe('RG204: what crosses for a declared logo', () => {
  it('hands over the picture and never the path it came from', async () => {
    const root = mkdtempSync(nodePath.join(tmpdir(), 'rk-carrier-logo-'))
    try {
      writeFileSync(
        nodePath.join(root, 'mark.png'),
        Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a, 0x00]),
      )
      const held: ProjectCatalogue = {
        ...FOUND,
        projects: [{ ...FOUND.projects[0]!, path: root }],
      }
      const { carrier } = world({
        remembered: () => held,
        rescan: () => Promise.resolve({ catalogue: held, changes: [] }),
        open: (at) => openProject(at, [['python', '/x/launch.py']], () => withLogo('mark.png')),
      })

      await carrier.projects()
      const opened = await carrier.open(root)

      if (opened.kind !== 'open') throw new Error(`opened as ${opened.kind}`)
      expect(opened.mark.startsWith('data:image/png;base64,')).toBe(true)
      // A `file://` URL into a renderer would widen what the window can read to whatever a
      // path can reach, and the path was a repository's word rather than this app's.
      expect(opened.declares.logo).toBe('')
      expect(JSON.stringify(opened)).not.toContain('mark.png')
    } finally {
      removeTree(root)
    }
  })

  it('hands over nothing where the declared file is not there', async () => {
    const { carrier } = world({
      open: (at) => openProject(at, [['python', '/x/launch.py']], () => withLogo('absent.png')),
    })

    await carrier.projects()
    const opened = await carrier.open(A)

    if (opened.kind !== 'open') throw new Error(`opened as ${opened.kind}`)
    // Every way of not having a picture is the same way, and the row falls back to the emoji.
    expect(opened.mark).toBe('')
  })
})
