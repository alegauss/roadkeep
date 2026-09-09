import { describe, expect, it } from 'vitest'

import { openProject, readsOnly } from './opening'
import { EngineCallFailed, type EngineResult, type Transport } from './transport'

/**
 * RG103: the order six pieces compose in, asserted as an order.
 *
 * The machine below answers by argv, records every call, and can be told to fail one of
 * them. What each case is about is which calls happened, in what sequence, and how many —
 * because that is the whole of what a composition is.
 */

const ENGINES = JSON.stringify({
  writing: { version: '0.2.400', home: '/engines/one', revision: 'abc1234', on_disk: '0.2.400' },
  invoke: 'python /proj/launch.py',
  declaration: '',
  verdict: 'agreed',
  agree: true,
  readable: true,
  split: false,
  swapped: false,
})

const CONFIG = JSON.stringify({
  version: '0.2.400',
  source: 'roadkeep.toml',
  keys: [
    { table: 'files', key: 'roadmap', declared: true, set: '"docs/ROADMAP.md"' },
    { table: 'files', key: 'changelog', declared: true, set: '"docs/CHANGELOG.md"' },
    { table: 'ids', key: 'prefix', declared: true, set: '"RG"' },
  ],
})

const COMMANDS = JSON.stringify({ version: '0.2.400', source: null, commands: [] })

const LIST = JSON.stringify({
  file: 'docs/ROADMAP.md',
  total: 0,
  uncounted: [],
  standing: null,
  startable: null,
  over: null,
  tasks: [],
})

/** A machine described by what each verb answers, remembering every call in order. */
function machine(answers: Record<string, string> = {}) {
  const asked: string[][] = []
  const said: Record<string, string> = {
    engines: ENGINES,
    config: CONFIG,
    commands: COMMANDS,
    list: LIST,
    ...answers,
  }

  const transportFor = (engine: readonly string[]): Transport => ({
    run(request) {
      asked.push([...request.argv])
      // `-C <root> <verb> … --json`, so the verb is the third element.
      const verb = request.argv[2] ?? ''
      const answer = said[verb]
      if (answer === undefined) {
        return Promise.reject(new EngineCallFailed('unspawnable', `no ${engine.join(' ')}`, 1))
      }
      const result: EngineResult = { code: 0, stdout: answer, stderr: '', durationMs: 1 }
      return Promise.resolve(result)
    },
  })

  return {
    transportFor,
    verbs: () => asked.map((argv) => argv[2] ?? ''),
    calls: () => asked.length,
  }
}

const LAUNCHER = ['python', '/proj/launch.py']

describe('RG103: the order a project opens in', () => {
  it('asks the three questions every later read depends on, in that order', async () => {
    const held = machine()

    const opened = await openProject('/proj', [LAUNCHER], held.transportFor)

    expect(opened.kind).toBe('open')
    // Which copy answers, then what it governs, then what it can run. Nothing else opens
    // a project, and none of the three can be moved: the second keys the cache and the
    // third says whether the first two would have been accepted at all.
    expect(held.verbs()).toEqual(['engines', 'config', 'commands'])
  })

  it('hands back a client that reads through the stack it built', async () => {
    const held = machine()

    const opened = await openProject('/proj', [LAUNCHER], held.transportFor)
    if (opened.kind !== 'open') return

    const answer = await opened.project.client.call('/proj', 'list', {})

    expect(answer.kind).toBe('read')
    expect(held.verbs()).toEqual(['engines', 'config', 'commands', 'list'])
  })

  it('reads what the project governs, which is what a stamp is taken over', async () => {
    const held = machine()

    const opened = await openProject('/proj', [LAUNCHER], held.transportFor)
    if (opened.kind !== 'open') return

    expect(opened.project.governed).toEqual({
      roadmap: 'docs/ROADMAP.md',
      changelog: 'docs/CHANGELOG.md',
    })
  })

  it('names the engine that answered, so a screen never has to ask again', async () => {
    const held = machine()

    const opened = await openProject('/proj', [LAUNCHER], held.transportFor)
    if (opened.kind !== 'open') return

    expect(opened.project.engine.payload.writing.version).toBe('0.2.400')
    expect(opened.project.capabilities.version).toBe('0.2.400')
  })
})

describe('RG103: what an open project remembers', () => {
  const stampFor = (_root: string, governed: readonly string[]) =>
    Promise.resolve(governed.join('|'))

  it('serves a repeated read without asking again', async () => {
    const held = machine()

    const opened = await openProject('/proj', [LAUNCHER], held.transportFor, { stampFor })
    if (opened.kind !== 'open') return

    await opened.project.client.call('/proj', 'list', {})
    await opened.project.client.call('/proj', 'list', {})

    // The cache is keyed on the files `config` named, which is why it could not have been
    // built before that read happened.
    expect(held.verbs().filter((verb) => verb === 'list')).toHaveLength(1)
  })

  it('asks again once the files it was keyed on have moved', async () => {
    const held = machine()
    let disk = 'first'

    const opened = await openProject('/proj', [LAUNCHER], held.transportFor, {
      stampFor: () => Promise.resolve(disk),
    })
    if (opened.kind !== 'open') return

    await opened.project.client.call('/proj', 'list', {})
    disk = 'second'
    await opened.project.client.call('/proj', 'list', {})

    expect(held.verbs().filter((verb) => verb === 'list')).toHaveLength(2)
  })

  it('forgets this project when told the disk moved', async () => {
    const held = machine()

    const opened = await openProject('/proj', [LAUNCHER], held.transportFor, { stampFor })
    if (opened.kind !== 'open') return

    await opened.project.client.call('/proj', 'list', {})
    opened.project.invalidate()
    await opened.project.client.call('/proj', 'list', {})

    // What a file watcher calls. Without it a screen would show yesterday's backlog for
    // as long as the window stayed open.
    expect(held.verbs().filter((verb) => verb === 'list')).toHaveLength(2)
  })

  it('remembers nothing at all where no stamp was supplied', async () => {
    // An answer kept against a constant is one that never expires, which is worse on a
    // screen than one that was never kept.
    const held = machine()

    const opened = await openProject('/proj', [LAUNCHER], held.transportFor)
    if (opened.kind !== 'open') return

    await opened.project.client.call('/proj', 'list', {})
    await opened.project.client.call('/proj', 'list', {})

    expect(held.verbs().filter((verb) => verb === 'list')).toHaveLength(2)
  })
})

describe('RG103: a project that does not open', () => {
  it('says nothing answered, with everything it tried', async () => {
    const held = machine({ engines: undefined as unknown as string })

    const opened = await openProject('/proj', [LAUNCHER, ['roadkeep']], held.transportFor)

    expect(opened.kind).toBe('unresolved')
    if (opened.kind !== 'unresolved') return
    expect(opened.reason).toContain('which roadkeep governs this project is unknown')
    expect(opened.tried).toEqual([LAUNCHER, ['roadkeep']])
  })

  it('carries the engine when it answered and then said something unreadable', async () => {
    const held = machine({ config: '{"version":"0.2.400"}' })

    const opened = await openProject('/proj', [LAUNCHER], held.transportFor)

    // The useful half of the sentence: a screen can name the build that is ahead of this
    // app rather than reporting the project as absent.
    expect(opened.kind).toBe('unreadable')
    if (opened.kind !== 'unreadable') return
    expect(opened.engine.payload.writing.version).toBe('0.2.400')
    // The sentence is the reader's now rather than this file's, so what is held is that it
    // names the key that moved. Which verb was being read is `argv`, beside it.
    expect(opened.unreadable.message).toContain('expected an array')
    expect(opened.unreadable.argv.join(' ')).toContain('config')
  })

  it('opens against a build too old to publish what it can run', async () => {
    const held = machine({
      commands: JSON.stringify({ refused: [], said: 'roadkeep: unrecognised command' }),
    })

    const opened = await openProject('/proj', [LAUNCHER], held.transportFor)

    // A build that cannot answer `commands` is a state, not a failure: the project opens
    // and every door is withheld, which is what `unsupported` is for.
    expect(opened.kind).toBe('open')
    if (opened.kind !== 'open') return
    expect(opened.project.capabilities.kind).toBe('unsupported')
    expect(opened.project.capabilities.version).toBe('0.2.400')
  })
})

describe('RG103: which answers may be remembered', () => {
  it('remembers a read', () => {
    expect(readsOnly(['-C', '/proj', 'list', '--json'])).toBe(true)
    expect(readsOnly(['-C', '/proj', 'non-goal', 'list', '--json'])).toBe(true)
  })

  it('never remembers the one read that writes', () => {
    // `brief --claim` takes the line. Serving it twice would report a claim that happened
    // once as though it happened again.
    expect(readsOnly(['-C', '/proj', 'brief', 'RG1', '--claim', '--json'])).toBe(false)
  })

  it('does not remember a verb this table has never heard of', () => {
    // Absent is not safe. A write verb, or a door's own argv, is not this table's to
    // approve, so the answer is no rather than a guess.
    expect(readsOnly(['-C', '/proj', 'ship', 'RG1', '--json'])).toBe(false)
    expect(readsOnly(['-C', '/proj', 'section', 'add', 'RG1', '--json'])).toBe(false)
  })
})
