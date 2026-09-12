import { describe, expect, it } from 'vitest'

import type { RecordedProject } from './catalogue'
import { coldStart } from './cold-start'
import { openProject, type OpenProject } from './opening'
import { openingUnreadable, rowStages } from './rows'
import { EngineCallFailed, type Transport } from './transport'

/**
 * RG145: the two reads a portfolio row is filled with, as a cold start runs them.
 *
 * `rows-live` counts what `glanceRow` and `withNext` cost against a real engine; this holds
 * the same two moments spelled as `coldStart` stages, over a machine answering by verb.
 */

const SAID: Record<string, string> = {
  engines: JSON.stringify({
    writing: { version: '0.2.400', home: '/engines/one', revision: 'abc1234', on_disk: '0.2.400' },
    invoke: 'python /code/launch.py',
    declaration: '',
    verdict: 'agreed',
    agree: true,
    readable: true,
    split: false,
    swapped: false,
  }),
  config: JSON.stringify({ version: '0.2.400', source: 'roadkeep.toml', keys: [] }),
  commands: JSON.stringify({ version: '0.2.400', source: null, commands: [] }),
  stats: JSON.stringify({ file: 'docs/ROADMAP.md', total: 7, uncounted: 0, markers: { '📋': 7 } }),
  pick: JSON.stringify({ pick: { id: 'FX2', block: 'A', symptom: 'a symptom' }, tier: 'designed' }),
}

/** A machine answering by verb, counting what it was asked, and failing the verbs it is told to. */
function machine(failing: readonly string[] = []) {
  const asked: string[] = []
  const transport: Transport = {
    run(request) {
      const verb = request.argv[2] ?? ''
      asked.push(verb)
      const answer = SAID[verb]
      if (answer === undefined || failing.includes(verb)) {
        return Promise.reject(new EngineCallFailed('timeout', `${verb} ran out`, 5))
      }
      return Promise.resolve({ code: 0, stdout: answer, stderr: '', durationMs: 1 })
    },
  }
  return { transport, asked }
}

function recorded(path: string): RecordedProject {
  return {
    path,
    aliases: [],
    commonDir: null,
    root: '/code',
    confirmed: '',
    presence: 'present',
    branch: '',
  }
}

async function reachOver(
  transport: Transport,
): Promise<(project: RecordedProject) => Promise<OpenProject>> {
  const opened = new Map<string, OpenProject>()
  return async (project) => {
    const held = opened.get(project.path)
    if (held !== undefined) return held
    const opening = await openProject(
      project.path,
      [['python', '/code/launch.py']],
      () => transport,
    )
    if (opening.kind !== 'open') throw openingUnreadable(opening)
    opened.set(project.path, opening.project)
    return opening.project
  }
}

describe('RG145: a row filled in two reads', () => {
  it('counts first, with the engine the opening already read, then asks for the next line', async () => {
    const { transport, asked } = machine()

    const [row] = await coldStart([recorded('/code/a')], rowStages(await reachOver(transport)))

    expect(row?.state).toBe('read')
    expect(row?.counts?.total).toBe(7)
    expect(row?.engine?.version).toBe('0.2.400')
    expect(row?.next?.id).toBe('FX2')
    // `engines` once, by the opening — never again for the row.
    expect(asked.filter((verb) => verb === 'engines')).toHaveLength(1)
    expect(asked.slice(-2)).toEqual(['stats', 'pick'])
  })

  it('names its stages, so a screen can say which one is running', () => {
    expect(rowStages(() => Promise.reject(new Error('unused'))).map((stage) => stage.name)).toEqual(
      ['counting', 'next'],
    )
  })

  it('draws a project whose counts would not come as unreadable, naming the verb', async () => {
    const { transport, asked } = machine(['stats'])

    const [row] = await coldStart([recorded('/code/a')], rowStages(await reachOver(transport)))

    expect(row?.state).toBe('unreadable')
    expect(row?.unreadable?.argv).toEqual(['stats'])
    // A project that failed the first stage is not asked the second.
    expect(asked).not.toContain('pick')
  })

  it('keeps the row it drew when only the next line would not come', async () => {
    const { transport } = machine(['pick'])

    const [row] = await coldStart([recorded('/code/a')], rowStages(await reachOver(transport)))

    expect(row?.state).toBe('read')
    expect(row?.counts?.total).toBe(7)
    expect(row?.next).toBeNull()
  })
})

describe('RG145: a project that did not open, as the row it becomes', () => {
  it('carries what resolution said for a project nothing answered for', () => {
    const unreadable = openingUnreadable({
      kind: 'unresolved',
      root: '/code/a',
      reason: 'no candidate answered',
      code: 'none-answered' as const,
      tried: [['python', 'launch.py']],
    })

    expect(unreadable).toMatchObject({ reason: 'unspawnable', message: 'no candidate answered' })
  })

  it('carries a withheld folder as the carrier withholding it', () => {
    expect(
      openingUnreadable({ kind: 'withheld', root: '/code/a', reason: 'not catalogued' }),
    ).toMatchObject({ reason: 'withheld', message: 'not catalogued' })
  })
})
