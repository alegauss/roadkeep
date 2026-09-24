import {
  bridgedRun,
  buildArgv,
  EngineCallFailed,
  openedFrom,
  openOver,
  openProject,
  type Transport,
} from '@rk/core'
import { afterEach, describe, expect, it } from 'vitest'

import { getBridge } from './bridge'
import { stubBridge } from './stub-bridge'

/**
 * RG143: a project read from the window, with nothing but `core` and what the bridge is.
 *
 * jsdom has no Node in scope, which is the point of running it here: what reads a project is
 * `getBridge()` and `openOver`, and every call leaves as `run`. The far side is `core`'s own
 * opening over a machine answering by verb, so the payload that comes back is one a real
 * carrier would hand over.
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

const SAID: Record<string, string> = {
  engines: ENGINES,
  config: JSON.stringify({ version: '0.2.400', source: 'roadkeep.toml', keys: [] }),
  commands: JSON.stringify({ version: '0.2.400', source: null, commands: [] }),
  'non-goal': JSON.stringify({
    file: 'docs/ROADMAP.md',
    governed: true,
    non_goals: ['No store of its own'],
    non_goals_elided: 0,
    non_goals_quoted: {},
    non_goals_why: { 'No store of its own': 'A cache is a second answer.' },
  }),
}

const machine: Transport = {
  run(request) {
    const answer = SAID[request.argv[2] ?? '']
    if (answer === undefined) return Promise.reject(new EngineCallFailed('unspawnable', 'no', 1))
    return Promise.resolve({ code: 0, stdout: answer, stderr: '', durationMs: 1 })
  },
}

afterEach(() => {
  Reflect.deleteProperty(window, 'roadkeep')
})

describe('RG143: reading a project from the window', () => {
  it('opens through the bridge and reads with the client core builds over run', async () => {
    const opened = openedFrom(await openProject('/proj', [['python', 'launch.py']], () => machine))
    const crossed: string[][] = []
    const bridge = stubBridge({
      open: () => Promise.resolve(opened),
      run: (root, request) => {
        crossed.push([...request.argv])
        return bridgedRun(() => machine.run({ ...request, root }))
      },
    })
    Object.defineProperty(window, 'roadkeep', { value: bridge, configurable: true })

    const here = getBridge()
    if (here === undefined) throw new Error('the window holds no bridge')
    const reached = await openOver(here, '/proj')
    if (reached.kind !== 'open') throw new Error(`did not open: ${reached.kind}`)
    const answer = await reached.project.client.call('/proj', 'nonGoalList', {})

    expect(answer.kind).toBe('read')
    expect(crossed).toEqual([buildArgv('/proj', 'nonGoalList', {})])
  })
})
