import {
  BASE,
  bridgedRun,
  DEFAULT_DEPTH,
  DEPTH_CEILING,
  EMPTY_CATALOGUE,
  EngineCallFailed,
  EVERY_SOURCE,
  fill,
  openedFrom,
  openProject,
  type KnownRoot,
  type OpenedProject,
  type ProjectCatalogue,
  type ProjectGate,
  type RecordedProject,
  type RendererBridge,
  type ScanRoot,
  type Transport,
} from '@rk/core'
import { act, fireEvent, screen, waitFor, within } from '@testing-library/react'
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
  config: JSON.stringify({
    version: '0.2.472',
    source: 'roadkeep.toml',
    keys: [
      // The mark this project declares (RG200). Only the icon: the three projects here
      // answer from one machine, so a declared *name* would rename all of them and the
      // ordering assertions elsewhere are about which row is which.
      { table: 'project', key: 'icon', address: 'project.icon', declared: true, set: '"🔎"' },
      {
        table: 'project',
        key: 'description',
        address: 'project.description',
        declared: true,
        set: '"A search engine, and the console around it"',
      },
    ],
  }),
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
  code: 'none-answered' as const,
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
    subscribe: () => () => undefined,
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
    // The catalogue's sentence for the code the opening carried, not the English one the
    // resolution wrote into `message` for the log (RG168).
    expect(within(row).getByText(BASE['unreadable.none-answered'])).toBeTruthy()
    expect(within(row).queryByText(REFUSED_BECAUSE)).toBeNull()
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

  it('RG148: opens a read row into its backlog, and leaves the others as text', async () => {
    await threeStates()
    drawWindow()
    const row = await waitFor(() => rowOf('alpha'))

    await waitFor(() => {
      expect(within(row).getByTestId('open-project').getAttribute('href')).toBe(
        `/project/${encodeURIComponent(READ)}`,
      )
    })
    expect(within(rowOf('gamma')).queryByTestId('open-project')).toBeNull()
    expect(within(rowOf('beta')).queryByTestId('open-project')).toBeNull()
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
      value: stubBridge({
        projects: () => Promise.reject(new Error('channel closed')),
        subscribe: () => () => undefined,
      }),
      configurable: true,
    })
    drawWindow()

    expect(
      await screen.findByText(fill(BASE['portfolio.failed'], { reason: 'channel closed' })),
    ).toBeTruthy()
  })

  it('says no project was found, rather than drawing an empty table', async () => {
    Object.defineProperty(window, 'roadkeep', {
      value: stubBridge({
        projects: () => Promise.resolve(EMPTY_CATALOGUE),
        subscribe: () => () => undefined,
      }),
      configurable: true,
    })
    drawWindow()

    expect(await screen.findByText(BASE['portfolio.none'])).toBeTruthy()
    expect(screen.queryByRole('table')).toBeNull()
  })
})

describe('RG146: naming where the window looks', () => {
  const HELD: readonly KnownRoot[] = [
    { path: 'D:/code', depth: 2, presence: 'present' },
    { path: 'E:/gone', depth: 1, presence: 'missing' },
  ]

  /** A bridge holding two roots, recording every save and every walk it was asked for. */
  function withRoots(roots: readonly KnownRoot[], picked: string | null = '/picked') {
    const saved: (readonly ScanRoot[])[] = []
    let walks = 0
    Object.defineProperty(window, 'roadkeep', {
      value: stubBridge({
        roots: () => Promise.resolve(roots),
        subscribe: () => () => undefined,
        chooseRoot: () => Promise.resolve(picked),
        saveRoots: (next) => {
          saved.push(next)
          return Promise.resolve(next.map((one) => ({ ...one, presence: 'present' as const })))
        },
        projects: () => {
          walks += 1
          return Promise.resolve(EMPTY_CATALOGUE)
        },
      }),
      configurable: true,
    })
    return { saved, walks: () => walks }
  }

  it('names each root with its depth, and marks a missing one rather than dropping it', async () => {
    withRoots(HELD)
    drawWindow()

    await waitFor(() => {
      expect(screen.getAllByTestId('root')).toHaveLength(2)
    })
    const gone = screen.getAllByTestId('root')[1]
    expect(gone?.dataset['presence']).toBe('missing')
    expect(within(gone ?? document.body).getByText(BASE['roots.missing'])).toBeTruthy()
    expect(screen.getByText(fill(BASE['roots.depth'], { depth: 2 }))).toBeTruthy()
  })

  it('adds the folder the shell answered with, and walks again for it', async () => {
    const { saved, walks } = withRoots(HELD)
    drawWindow()
    await waitFor(() => {
      expect(screen.getAllByTestId('root')).toHaveLength(2)
    })

    fireEvent.click(screen.getByTestId('add-root'))

    await waitFor(() => {
      expect(saved).toEqual([
        [
          { path: 'D:/code', depth: 2 },
          { path: 'E:/gone', depth: 1 },
          { path: '/picked', depth: DEFAULT_DEPTH },
        ],
      ])
    })
    await waitFor(() => {
      expect(walks()).toBe(2)
    })
    expect(screen.getAllByTestId('root')).toHaveLength(3)
  })

  it('writes nothing when the dialog was cancelled', async () => {
    const { saved } = withRoots(HELD, null)
    drawWindow()
    await waitFor(() => {
      expect(screen.getAllByTestId('root')).toHaveLength(2)
    })

    fireEvent.click(screen.getByTestId('add-root'))
    await new Promise((done) => setTimeout(done, 20))

    expect(saved).toEqual([])
  })

  it('stops looking under a root the person removes, by name', async () => {
    const { saved } = withRoots(HELD)
    drawWindow()

    fireEvent.click(
      await screen.findByRole('button', { name: fill(BASE['roots.remove'], { path: 'E:/gone' }) }),
    )

    await waitFor(() => {
      expect(saved).toEqual([[{ path: 'D:/code', depth: 2 }]])
    })
  })

  it('says no root is named, rather than that no project was found', async () => {
    withRoots([])
    drawWindow()

    expect(await screen.findByText(BASE['roots.none'])).toBeTruthy()
    expect(screen.queryByText(BASE['portfolio.none'])).toBeNull()
  })

  it('walks again when asked, over the roots already named', async () => {
    const { walks } = withRoots(HELD)
    drawWindow()
    await waitFor(() => {
      expect(walks()).toBe(1)
    })

    fireEvent.click(screen.getByTestId('rescan'))

    await waitFor(() => {
      expect(walks()).toBe(2)
    })
  })
})

describe('RG152: the gate column, off the ledger the carrier keeps', () => {
  /** A bridge that answers the read project, and holds one verdict for it. */
  async function withGate(health: {
    verdict: 'clean' | 'drifted'
    problems: number
    taken: string
    stale: boolean
  }): Promise<void> {
    // Two projects that open, so the row with no verdict is a read row and not an
    // unreadable one: unknown is what a gate column says, not what a failed opening says.
    const alpha = await opened(READ)
    const beta = await opened(PENDING)
    Object.defineProperty(window, 'roadkeep', {
      value: stubBridge({
        projects: () => Promise.resolve(THREE),
        subscribe: () => () => undefined,
        open: (root) =>
          root === READ
            ? Promise.resolve(alpha)
            : root === PENDING
              ? Promise.resolve(beta)
              : Promise.resolve(REFUSAL),
        run: (root, request) => bridgedRun(() => machine.run({ ...request, root })),
        gates: () => Promise.resolve([{ root: READ, health }]),
      }),
      configurable: true,
    })
  }

  it('draws the verdict on record, with the count a drifted report gave', async () => {
    await withGate({
      verdict: 'drifted',
      problems: 3,
      taken: '2026-09-11T12:00:00.000Z',
      stale: false,
    })
    drawWindow()

    await waitFor(() => {
      expect(rowOf('alpha').textContent).toContain(BASE['portfolio.gate.drifted'])
    })
    expect(rowOf('alpha').textContent).toContain(
      fill(BASE['portfolio.gate.findings'], { count: 3 }),
    )
  })

  it('keeps the verdict on a list still filling, since the reads land after it', async () => {
    // One project whose opening never answers, so the list stays under way: the verdict has
    // to survive every draw between it landing and the last read finishing, and a merge done
    // once is undone by the next stage that reports.
    const alpha = await opened(READ)
    Object.defineProperty(window, 'roadkeep', {
      value: stubBridge({
        projects: () => Promise.resolve(THREE),
        subscribe: () => () => undefined,
        open: (root) =>
          root === READ ? Promise.resolve(alpha) : new Promise<OpenedProject>(() => undefined),
        run: (root, request) => bridgedRun(() => machine.run({ ...request, root })),
        gates: () =>
          Promise.resolve([
            {
              root: READ,
              health: {
                verdict: 'clean' as const,
                problems: 0,
                taken: '2026-09-11T12:00:00.000Z',
                stale: false,
              },
            },
          ]),
      }),
      configurable: true,
    })
    drawWindow()

    await waitFor(() => {
      expect(rowOf('alpha').textContent).toContain(BASE['portfolio.gate.clean'])
    })
    // Still filling: two rows have not been read, so this is a draw from progress and not
    // the final one.
    expect(screen.getAllByTestId('portfolio-row').map((row) => row.dataset['state'])).toContain(
      'pending',
    )
  })

  it('says a verdict is stale rather than dropping it, where the files moved since', async () => {
    await withGate({
      verdict: 'clean',
      problems: 0,
      taken: '2026-09-11T12:00:00.000Z',
      stale: true,
    })
    drawWindow()

    await waitFor(() => {
      expect(rowOf('alpha').textContent).toContain(BASE['portfolio.gate.stale'])
    })
  })

  it('leaves a project no verdict names unknown, never clean', async () => {
    await withGate({
      verdict: 'clean',
      problems: 0,
      taken: '2026-09-11T12:00:00.000Z',
      stale: false,
    })
    drawWindow()

    await waitFor(() => {
      expect(rowOf('alpha').textContent).toContain(BASE['portfolio.gate.clean'])
    })
    expect(rowOf('beta').textContent).toContain(BASE['portfolio.gate.unknown'])
  })
})

describe('RG166: a verdict that lands while the list is open', () => {
  it('puts it on the row it is about, without the list being read again', async () => {
    const alpha = await opened(READ)
    let tell: ((gate: ProjectGate) => void) | null = null
    let letGatesAnswer: (gates: readonly ProjectGate[]) => void = () => undefined
    let given = 0
    Object.defineProperty(window, 'roadkeep', {
      value: stubBridge({
        projects: () => Promise.resolve(THREE),
        open: (root) => (root === READ ? Promise.resolve(alpha) : Promise.resolve(REFUSAL)),
        run: (root, request) => bridgedRun(() => machine.run({ ...request, root })),
        // The ledger read is the slow one here, and it answers with what was on record
        // before the carrier's own run landed: an older answer, arriving later.
        gates: () =>
          new Promise((answer) => {
            letGatesAnswer = answer
          }),
        subscribe: (topic, key, listener) => {
          if (topic === 'gate' && key === READ) tell = listener as (gate: ProjectGate) => void
          return () => {
            given += 1
          }
        },
      }),
      configurable: true,
    })
    const drawn = drawWindow()

    await waitFor(() => {
      expect(rowOf('alpha').textContent).toContain(BASE['portfolio.gate.unknown'])
    })
    await waitFor(() => {
      expect(tell).not.toBeNull()
    })

    act(() => {
      tell?.({
        root: READ,
        health: {
          verdict: 'drifted',
          problems: 2,
          taken: '2026-09-11T12:00:00.000Z',
          stale: false,
        },
      })
    })

    await waitFor(() => {
      expect(rowOf('alpha').textContent).toContain(BASE['portfolio.gate.drifted'])
    })

    // The ledger read lands now, with what it held before that run. The newer verdict stands:
    // an answer read earlier and delivered later is still the older of the two.
    await act(async () => {
      letGatesAnswer([
        {
          root: READ,
          health: {
            verdict: 'clean',
            problems: 0,
            taken: '2026-09-11T11:00:00.000Z',
            stale: false,
          },
        },
      ])
      await Promise.resolve()
    })
    expect(rowOf('alpha').textContent).toContain(BASE['portfolio.gate.drifted'])

    // And the watch goes with the screen.
    drawn.unmount()
    expect(given).toBeGreaterThan(0)
  })
})

describe('RG167: a row that follows its project', () => {
  /** A machine whose counts can be changed between reads, the way a terminal changes them. */
  function moving() {
    let total = 60
    const transport: Transport = {
      run(request) {
        const verb = request.argv[2] ?? ''
        if (verb === 'stats') {
          return Promise.resolve({
            code: 0,
            stdout: JSON.stringify({
              file: 'docs/ROADMAP.md',
              total,
              uncounted: 0,
              markers: { '📋': 11 },
              startable: { open: total, startable: total, waiting: 0, absent: [] },
              blocks: [],
            }),
            stderr: '',
            durationMs: 1,
          })
        }
        const answer = SAID[verb]
        if (answer === undefined)
          return Promise.reject(new EngineCallFailed('unspawnable', 'no', 1))
        return Promise.resolve({ code: 0, stdout: answer, stderr: '', durationMs: 1 })
      },
    }
    return { transport, ship: () => (total = 59) }
  }

  /** Draw the list, with the way to tell one project its files moved. */
  async function watching(): Promise<{ moved: () => void; ship: () => void }> {
    const { transport, ship } = moving()
    const alpha = openedFrom(
      await openProject(READ, [['python', '/code/launch.py']], () => transport),
    )
    const moves: (() => void)[] = []
    Object.defineProperty(window, 'roadkeep', {
      value: stubBridge({
        projects: () => Promise.resolve(THREE),
        open: (root) => (root === READ ? Promise.resolve(alpha) : Promise.resolve(REFUSAL)),
        run: (root, request) => bridgedRun(() => transport.run({ ...request, root })),
        gates: () => Promise.resolve([]),
        subscribe: (topic, key, listener) => {
          if (topic === 'governed' && key === READ) moves.push(() => (listener as () => void)())
          return () => undefined
        },
      }),
      configurable: true,
    })
    drawWindow()
    return {
      moved: () => {
        for (const move of moves) move()
      },
      ship,
    }
  }

  it('reads that project again when its files move, and leaves the others alone', async () => {
    const { moved, ship } = await watching()

    await waitFor(() => {
      expect(rowOf('alpha').textContent).toContain('60')
    })
    ship()
    await act(async () => {
      moved()
      await Promise.resolve()
    })

    await waitFor(() => {
      expect(rowOf('alpha').textContent).toContain('59')
    })
    // The other two are what they were: a move is one project's news.
    expect(screen.getAllByTestId('portfolio-row').map((row) => row.dataset['state'])).toEqual([
      'read',
      'unreadable',
      'unreadable',
    ])
  })

  it('keeps the row where the record put it, never where the reread finished', async () => {
    const { moved, ship } = await watching()

    await waitFor(() => {
      expect(rowOf('alpha').textContent).toContain('60')
    })
    ship()
    await act(async () => {
      moved()
      await Promise.resolve()
    })
    await waitFor(() => {
      expect(rowOf('alpha').textContent).toContain('59')
    })

    // By the path each row says it is, and not by a slice of its rendered text: the cell
    // holds a chip, counts and a verdict, so slicing characters off it asserts the layout
    // as much as the order.
    expect(screen.getAllByTestId('portfolio-row').map((row) => row.dataset['path'])).toEqual([
      READ,
      PENDING,
      REFUSED,
    ])
  })
})

describe('RG169: moving a root’s depth from the window', () => {
  const HELD: readonly KnownRoot[] = [
    { path: 'D:/code', depth: 2, presence: 'present' },
    { path: 'E:/deep', depth: DEPTH_CEILING, presence: 'present' },
    { path: 'F:/flat', depth: 0, presence: 'present' },
  ]

  function withRoots(roots: readonly KnownRoot[]) {
    const saved: (readonly ScanRoot[])[] = []
    let walks = 0
    Object.defineProperty(window, 'roadkeep', {
      value: stubBridge({
        roots: () => Promise.resolve(roots),
        subscribe: () => () => undefined,
        saveRoots: (next) => {
          saved.push(next)
          return Promise.resolve(next.map((one) => ({ ...one, presence: 'present' as const })))
        },
        projects: () => {
          walks += 1
          return Promise.resolve(EMPTY_CATALOGUE)
        },
      }),
      configurable: true,
    })
    return { saved, walks: () => walks }
  }

  const chipFor = (path: string): HTMLElement => {
    const chip = screen.getAllByTestId('root').find((one) => one.textContent.includes(path))
    if (chip === undefined) throw new Error(`no chip for ${path}`)
    return chip
  }

  it('saves the whole list with one depth moved, keeping every root in its place', async () => {
    const { saved, walks } = withRoots(HELD)
    drawWindow()
    await screen.findAllByTestId('root')
    const before = walks()

    fireEvent.click(
      within(chipFor('D:/code')).getByRole('button', {
        name: fill(BASE['roots.deeper'], { path: 'D:/code' }),
      }),
    )

    await waitFor(() => {
      expect(saved).toHaveLength(1)
    })
    expect(saved[0]).toEqual([
      { path: 'D:/code', depth: 3 },
      { path: 'E:/deep', depth: DEPTH_CEILING },
      { path: 'F:/flat', depth: 0 },
    ])
    // And the list is walked again, the way adding a root walks it.
    await waitFor(() => {
      expect(walks()).toBeGreaterThan(before)
    })
  })

  it('goes one level less deep the same way', async () => {
    const { saved } = withRoots(HELD)
    drawWindow()
    await screen.findAllByTestId('root')

    fireEvent.click(
      within(chipFor('D:/code')).getByRole('button', {
        name: fill(BASE['roots.shallower'], { path: 'D:/code' }),
      }),
    )

    await waitFor(() => {
      expect(saved[0]?.[0]).toEqual({ path: 'D:/code', depth: 1 })
    })
  })

  it('disables each end rather than refusing the click after it, at the rule’s own bounds', async () => {
    withRoots(HELD)
    drawWindow()
    await screen.findAllByTestId('root')

    const deepest = within(chipFor('E:/deep')).getByRole('button', {
      name: fill(BASE['roots.deeper'], { path: 'E:/deep' }),
    })
    const flattest = within(chipFor('F:/flat')).getByRole('button', {
      name: fill(BASE['roots.shallower'], { path: 'F:/flat' }),
    })

    expect(deepest.hasAttribute('disabled')).toBe(true)
    expect(flattest.hasAttribute('disabled')).toBe(true)
    // And the other end of each is open: 0 is a folder read by itself, not a floor to stop at.
    expect(
      within(chipFor('F:/flat'))
        .getByRole('button', { name: fill(BASE['roots.deeper'], { path: 'F:/flat' }) })
        .hasAttribute('disabled'),
    ).toBe(false)
  })

  it('draws the depth the save answered with, so a level shows at once', async () => {
    withRoots(HELD)
    drawWindow()
    await screen.findAllByTestId('root')

    fireEvent.click(
      within(chipFor('D:/code')).getByRole('button', {
        name: fill(BASE['roots.deeper'], { path: 'D:/code' }),
      }),
    )

    await waitFor(() => {
      expect(within(chipFor('D:/code')).getByTestId('root-depth').textContent).toBe(
        fill(BASE['roots.depth'], { depth: 3 }),
      )
    })
  })
})

describe('RG180: hearing the walk behind the record land', () => {
  it('asks for the list again when the fold changed something, and not otherwise', async () => {
    const alpha = await opened(READ)
    let tell: (() => void) | null = null
    let walks = 0
    let listed: ProjectCatalogue = { version: 1, roots: [], projects: [recorded(READ)] }
    Object.defineProperty(window, 'roadkeep', {
      value: stubBridge({
        projects: () => {
          walks += 1
          return Promise.resolve(listed)
        },
        open: () => Promise.resolve(alpha),
        run: (root, request) => bridgedRun(() => machine.run({ ...request, root })),
        gates: () => Promise.resolve([]),
        subscribe: (topic, key, listener) => {
          if (topic === 'catalogue' && key === EVERY_SOURCE) tell = listener as () => void
          return () => undefined
        },
      }),
      configurable: true,
    })
    drawWindow()

    await waitFor(() => {
      expect(rowOf('alpha')).toBeTruthy()
    })
    const asked = walks

    // The walk found a project the record did not hold, and main says so.
    listed = { ...listed, projects: [recorded(READ), recorded(PENDING)] }
    act(() => {
      tell?.()
    })

    await waitFor(() => {
      expect(screen.getAllByTestId('portfolio-row')).toHaveLength(2)
    })
    expect(walks).toBeGreaterThan(asked)
  })

  it('subscribes once, to the one key a catalogue has', async () => {
    const alpha = await opened(READ)
    const asked: { topic: string; key: string }[] = []
    Object.defineProperty(window, 'roadkeep', {
      value: stubBridge({
        projects: () => Promise.resolve({ version: 1, roots: [], projects: [recorded(READ)] }),
        open: () => Promise.resolve(alpha),
        run: (root, request) => bridgedRun(() => machine.run({ ...request, root })),
        gates: () => Promise.resolve([]),
        subscribe: (topic, key) => {
          asked.push({ topic, key })
          return () => undefined
        },
      }),
      configurable: true,
    })
    drawWindow()

    await waitFor(() => {
      expect(rowOf('alpha')).toBeTruthy()
    })
    expect(asked.filter((one) => one.topic === 'catalogue')).toEqual([
      { topic: 'catalogue', key: EVERY_SOURCE },
    ])
  })
})

describe('RG200: the chip a row is recognised by', () => {
  it('draws the emoji the project declared, in the chip that was already there', async () => {
    await threeStates()
    drawWindow()

    await waitFor(() => {
      expect(within(rowOf('alpha')).getByText('🔎')).toBeTruthy()
    })
  })

  it('keeps the folder glyph where a project declares nothing', async () => {
    // `gamma` never opens, so nothing was ever read for it to declare — which is also the
    // state every project is in before a single repository adopts the key.
    await threeStates()
    drawWindow()

    await waitFor(() => {
      expect(rowOf('gamma')).toBeTruthy()
    })
    expect(within(rowOf('gamma')).queryByText('🔎')).toBeNull()
  })

  it('leaves the chip presentational, so a reader by ear hears the name and not a glyph', async () => {
    await threeStates()
    drawWindow()

    await waitFor(() => {
      expect(within(rowOf('alpha')).getByText('🔎')).toBeTruthy()
    })
    // The emoji sits inside the `aria-hidden` chip: announced before the project's name it
    // would be noise, and the name is already there.
    const chip = within(rowOf('alpha')).getByText('🔎').closest('[aria-hidden="true"]')
    expect(chip).not.toBeNull()
  })
})

describe('RG201: what a row is for, not where it is', () => {
  const SAYS = 'A search engine, and the console around it'

  it('puts the declared description on the line the path was on', async () => {
    await threeStates()
    drawWindow()

    await waitFor(() => {
      expect(within(rowOf('alpha')).getByText(SAYS)).toBeTruthy()
    })
    // One line, not two: this cell sits in a table and a row that grows for some projects
    // and not others makes it ragged.
    expect(within(rowOf('alpha')).queryByText(READ)).toBeNull()
  })

  it('keeps the path in the tooltip, which is where a path belongs', async () => {
    await threeStates()
    drawWindow()

    await waitFor(() => {
      expect(within(rowOf('alpha')).getByText(SAYS)).toBeTruthy()
    })
    expect(within(rowOf('alpha')).getByText(SAYS).getAttribute('title')).toBe(READ)
  })

  it('leaves the path on the line where nothing is declared', async () => {
    // `gamma` never opens, so nothing was read for it to declare — a mixed portfolio has
    // to be readable in both states.
    await threeStates()
    drawWindow()

    await waitFor(() => {
      expect(rowOf('gamma')).toBeTruthy()
    })
    expect(within(rowOf('gamma')).getByText(REFUSED)).toBeTruthy()
  })
})
