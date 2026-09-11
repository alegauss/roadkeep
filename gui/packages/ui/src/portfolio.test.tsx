import {
  BASE,
  bridgedRun,
  EMPTY_CATALOGUE,
  EngineCallFailed,
  fill,
  openedFrom,
  openProject,
  type OpenedProject,
  type ProjectCatalogue,
  type RecordedProject,
  type RendererBridge,
  type Transport,
} from '@rk/core'
import { fireEvent, screen, waitFor, within } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'

import { drawWindow } from './harness'
import { stubBridge } from './stub-bridge'

/**
 * RG145: the portfolio, drawn through the whole window against a stub bridge.
 *
 * Three projects in three states, which is what the design asks this test for: one reads,
 * one never answers, one did not open. The far side is `core`'s own opening over a machine
 * answering by verb, so what arrives is what a real carrier would hand over, and every number
 * asserted below is one the machine printed.
 */

const READ = '/code/alpha'
const PENDING = '/code/beta'
const REFUSED = '/code/gamma'

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
  stats: JSON.stringify({
    file: 'docs/ROADMAP.md',
    total: 60,
    uncounted: 0,
    markers: { '📋': 11, '💭': 48, '🛠': 1 },
    startable: { open: 60, startable: 58, waiting: 2, absent: [] },
    blocks: [],
  }),
  pick: JSON.stringify({
    pick: {
      id: 'RG45',
      block: 'G',
      status: '💭',
      symptom: 'nothing watches the files',
      ref: 'RG45',
    },
    tier: 'lowest-ready-id',
    reason: 'lowest ready id',
    ready: 26,
    blocked: 28,
  }),
}

const machine: Transport = {
  run(request) {
    const answer = SAID[request.argv[2] ?? '']
    if (answer === undefined) return Promise.reject(new EngineCallFailed('unspawnable', 'no', 1))
    return Promise.resolve({ code: 0, stdout: answer, stderr: '', durationMs: 1 })
  },
}

function recorded(path: string): RecordedProject {
  return { path, aliases: [], commonDir: null, root: '/code', confirmed: '', presence: 'present' }
}

const THREE: ProjectCatalogue = {
  version: 1,
  roots: [{ path: '/code', depth: 1 }],
  projects: [recorded(READ), recorded(PENDING), recorded(REFUSED)],
}

const REFUSED_BECAUSE = 'no candidate answered `engines --json`'

const REFUSAL: OpenedProject = {
  kind: 'unresolved',
  root: REFUSED,
  reason: REFUSED_BECAUSE,
  tried: [['python', '/code/gamma/launch.py']],
}

async function opened(root: string): Promise<OpenedProject> {
  return openedFrom(await openProject(root, [['python', '/code/launch.py']], () => machine))
}

/**
 * A bridge answering the three, where `beta` answers when the test says so — or never.
 */
async function threeStates(): Promise<{ answerBeta: () => Promise<void> }> {
  const alpha = await opened(READ)
  let letBetaAnswer: (answer: OpenedProject) => void = () => undefined
  const beta = new Promise<OpenedProject>((answer) => {
    letBetaAnswer = answer
  })

  const bridge: RendererBridge = stubBridge({
    projects: () => Promise.resolve(THREE),
    open: (root) =>
      root === READ ? Promise.resolve(alpha) : root === PENDING ? beta : Promise.resolve(REFUSAL),
    run: (root, request) => bridgedRun(() => machine.run({ ...request, root })),
  })
  Object.defineProperty(window, 'roadkeep', { value: bridge, configurable: true })

  return {
    answerBeta: async () => {
      letBetaAnswer(await opened(PENDING))
    },
  }
}

function rowOf(name: string): HTMLElement {
  const row = screen.getAllByTestId('portfolio-row').find((one) => one.textContent.includes(name))
  if (row === undefined) throw new Error(`no row for ${name}`)
  return row
}

afterEach(() => {
  Reflect.deleteProperty(window, 'roadkeep')
})

describe('RG145: the portfolio at the root route', () => {
  it('draws one row per project, in the record order, each in its own state', async () => {
    await threeStates()
    drawWindow()

    await waitFor(() => {
      expect(screen.getAllByTestId('portfolio-row').map((row) => row.dataset['state'])).toEqual([
        'read',
        'pending',
        'unreadable',
      ])
    })
    expect(screen.getByText(fill(BASE['portfolio.title'], { count: 3 }))).toBeTruthy()
    expect(
      screen.getByText(fill(BASE['portfolio.tally'], { read: 1, pending: 1, unreadable: 1 })),
    ).toBeTruthy()
  })

  it('fills a read row with what the verbs printed, and the engine beside the counts', async () => {
    await threeStates()
    drawWindow()

    const row = await waitFor(() => rowOf('alpha'))
    await waitFor(() => {
      expect(within(row).getByText(fill(BASE['portfolio.open'], { count: 60 }))).toBeTruthy()
    })
    expect(
      within(row).getByText(fill(BASE['portfolio.startable'], { startable: 58, waiting: 2 })),
    ).toBeTruthy()
    // The engine's verdict is its own word, drawn as it came.
    expect(within(row).getByText('0.2.400')).toBeTruthy()
    expect(within(row).getByText('agreed')).toBeTruthy()
    // Nothing has run the gate, and a row says so rather than calling the project clean.
    expect(within(row).getByText(BASE['portfolio.gate.unknown'])).toBeTruthy()
    expect(within(row).getByText(BASE['portfolio.gate.never'])).toBeTruthy()
  })

  it('draws a project still answering as pending, never as zero', async () => {
    await threeStates()
    drawWindow()

    const row = await waitFor(() => rowOf('beta'))

    expect(within(row).getByText(BASE['portfolio.pending'])).toBeTruthy()
    expect(within(row).queryByText(fill(BASE['portfolio.open'], { count: 0 }))).toBeNull()
  })

  it('says why a project did not open, and what was tried', async () => {
    await threeStates()
    drawWindow()

    const row = await waitFor(() => rowOf('gamma'))

    expect(within(row).getByText(BASE['portfolio.unreadable'])).toBeTruthy()
    expect(within(row).getByText(REFUSED_BECAUSE)).toBeTruthy()
    expect(within(row).getByText('python /code/gamma/launch.py')).toBeTruthy()
  })

  it('says what the cold start is doing while it runs', async () => {
    await threeStates()
    drawWindow()

    const progress = await screen.findByTestId('portfolio-progress')

    expect(progress.textContent).toContain(BASE['portfolio.stage.counting'])
  })

  it('adds the next line once every row has had its first read', async () => {
    const { answerBeta } = await threeStates()
    drawWindow()
    await waitFor(() => rowOf('beta'))

    await answerBeta()

    await waitFor(() => {
      expect(within(rowOf('alpha')).getByText('RG45')).toBeTruthy()
    })
    expect(within(rowOf('alpha')).getByText('nothing watches the files')).toBeTruthy()
    await waitFor(() => {
      expect(screen.queryByTestId('portfolio-progress')).toBeNull()
    })
  })

  it('narrows to what a chip names, counting rows and nothing else', async () => {
    await threeStates()
    drawWindow()
    await waitFor(() => rowOf('gamma'))

    const unreadable = screen.getByTestId('filter-unreadable')
    expect(unreadable.textContent).toBe(fill(BASE['portfolio.filter.unreadable'], { count: 1 }))
    fireEvent.click(unreadable)

    expect(unreadable.getAttribute('aria-pressed')).toBe('true')
    expect(screen.getAllByTestId('portfolio-row').map((row) => row.dataset['state'])).toEqual([
      'unreadable',
    ])
  })
})

describe('RG145: the three ways there is no list', () => {
  it('says there is no bridge, which is what a plain browser tab has', () => {
    drawWindow()

    expect(screen.getByText(BASE['transport.absent'])).toBeTruthy()
    expect(screen.queryAllByTestId('portfolio-row')).toEqual([])
    expect(screen.getByText(BASE['portfolio.footnote'])).toBeTruthy()
  })

  it('says the bridge would not answer, with its reason', async () => {
    Object.defineProperty(window, 'roadkeep', {
      value: stubBridge({ projects: () => Promise.reject(new Error('channel closed')) }),
      configurable: true,
    })
    drawWindow()

    expect(
      await screen.findByText(fill(BASE['portfolio.failed'], { reason: 'channel closed' })),
    ).toBeTruthy()
  })

  it('says no project was found, rather than drawing an empty table', async () => {
    Object.defineProperty(window, 'roadkeep', {
      value: stubBridge({ projects: () => Promise.resolve(EMPTY_CATALOGUE) }),
      configurable: true,
    })
    drawWindow()

    expect(await screen.findByText(BASE['portfolio.none'])).toBeTruthy()
    expect(screen.queryByRole('table')).toBeNull()
  })
})
