import {
  BASE,
  bridgedRun,
  EngineCallFailed,
  fill,
  openedFrom,
  openProject,
  type ProjectCatalogue,
  type Transport,
} from '@rk/core'
import { fireEvent, screen, waitFor, within } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'

import { projectPath } from './areas'
import { drawWindow } from './harness'
import { stubBridge } from './stub-bridge'

/**
 * RG148: one backlog, drawn through the whole window at its route.
 *
 * The far side is `core`'s opening over a machine answering by verb, the way the portfolio
 * test builds one, so every row is what `list` printed and every readiness word is what
 * `deps` printed for that id. What is held is that the narrowings reach the verb as
 * arguments, and that the screen says only what the answers said.
 */

const ROOT = 'D:\\code\\alpha'

const key = (table: string, name: string, set: string | null, fallback: string | null = null) => ({
  table,
  key: name,
  address: `${table}.${name}`,
  declared: set !== null,
  set,
  // The engine spells it `default`, which the reader renames.
  default: fallback,
})

const LINES = [
  {
    id: 'AL1',
    status: '📋',
    block: 'A',
    symptom: 'the first line is ready to start',
    why: 'Nothing holds it back.',
    deps: [],
    ref: 'AL1',
    line: 7,
    length: 90,
  },
  {
    id: 'AL2',
    status: '💭',
    block: 'A',
    symptom: 'the second waits on the first',
    why: 'It needs what the first builds.',
    deps: ['AL1'],
    ref: null,
    line: 8,
    length: 90,
  },
  {
    id: 'AL3',
    status: '🛠',
    block: 'B',
    symptom: 'the third was started and nobody holds it',
    why: 'A session moved the marker and its claim lapsed.',
    deps: [],
    ref: 'AL3',
    line: 12,
    length: 90,
  },
]

/** A line in one of the other governed files, shaped as `list` prints it. */
function filed(id: string, status: string, block: string, symptom: string, why: string) {
  return { id, status, block, symptom, why, deps: [] as string[], ref: null, line: 3, length: 80 }
}

/** What `list` answers for each role the roadmap is not. */
const FILED: Record<string, ReturnType<typeof filed>[]> = {
  changelog: [filed('AL0', '✅', 'A', 'the first thing shipped', 'It works now.')],
  decisions: [
    filed('AL9', '✅', 'A', 'a decision was needed', 'The constraint that outlives the work.'),
  ],
  deferred: [
    {
      ...filed('AL5', '⏸', 'B', 'this was set aside', 'set aside (waiting): later.'),
      deps: ['AL1'],
    },
  ],
}

/** What each verb answers, by the verb's first word, and the id where a verb takes one. */
function answer(argv: readonly string[]): string | undefined {
  const verb = argv[2] ?? ''
  const id = argv[3] ?? ''
  const blockArg = argv.indexOf('--block')
  const narrowedTo = blockArg === -1 ? null : argv[blockArg + 1]
  switch (verb) {
    case 'engines':
      return JSON.stringify({
        writing: { version: '0.2.400', home: '/e', revision: 'abc', on_disk: '0.2.400' },
        invoke: 'python launch.py',
        declaration: '',
        verdict: 'agreed',
        agree: true,
        readable: true,
        split: false,
        swapped: false,
      })
    case 'config':
      return JSON.stringify({
        version: '0.2.400',
        source: 'roadkeep.toml',
        keys: [
          key('files', 'roadmap', '"docs/ROADMAP.md"'),
          key('files', 'changelog', '"docs/CHANGELOG.md"'),
          key('files', 'decisions', '"docs/DECISIONS.md"'),
          key('files', 'deferred', '"docs/DEFERRED.md"'),
          key('files', 'improvements', '"docs/IMPROVEMENTS.md"'),
          key('markers', 'open', '["📋", "💭", "⏳", "🛠"]'),
          key('markers', 'working', null, '"🛠"'),
          key('requirements', 'declared', '["signing-cert"]'),
        ],
      })
    case 'commands':
      return JSON.stringify({ version: '0.2.400', source: null, commands: [] })
    case 'stats':
      return JSON.stringify({
        file: 'docs/ROADMAP.md',
        total: 3,
        uncounted: 0,
        markers: { '📋': 1, '💭': 1, '🛠': 1 },
        startable: { open: 3, startable: 3, waiting: 0, absent: [] },
        blocks: [],
      })
    case 'block':
      return JSON.stringify({
        file: 'docs/ROADMAP.md',
        blocks: [
          {
            block: 'A',
            state: 'live',
            sentence: '',
            open: 2,
            recorded: 0,
            paused: 0,
            title: 'The model',
          },
          {
            block: 'B',
            state: 'live',
            sentence: '',
            open: 1,
            recorded: 4,
            paused: 0,
            title: 'The surface',
          },
          {
            block: 'C',
            state: 'finished',
            sentence: '',
            open: 0,
            recorded: 6,
            paused: 0,
            title: 'Done',
          },
        ],
      })
    case 'list': {
      const role = argv.includes('--stale') ? 'deferred' : (argv[argv.indexOf('--role') + 1] ?? '')
      const tasks =
        argv.includes('--role') || argv.includes('--stale') ? (FILED[role] ?? []) : LINES
      return JSON.stringify({
        file: 'docs/ROADMAP.md',
        total: tasks.length,
        uncounted: [],
        tasks: tasks.filter((line) => narrowedTo === null || line.block === narrowedTo),
      })
    }
    case 'reversals':
      return JSON.stringify({
        root: ROOT,
        asked: null,
        reversed: [{ undone: 'AL0', by: 'AL7', line: 9, why: 'It did not hold.' }],
      })
    case 'section':
      return argv[4] === 'AL9'
        ? JSON.stringify({
            anchor: 'AL9',
            title: 'Why the constraint',
            level: 3,
            file: 'docs/DECISIONS.md',
            first: 1,
            last: 4,
            words: 9,
            own_words: 9,
            body: 'The reasoning,\nwrapped as the file keeps it.',
          })
        : undefined
    case 'deps':
      return JSON.stringify(
        id === 'AL2'
          ? { id, readiness: 'blocked', blockers: ['AL1'] }
          : { id, readiness: 'ready', blockers: [] },
      )
    case 'brief':
      return JSON.stringify({
        id,
        status: '🛠',
        block: 'B',
        symptom: 'the third was started and nobody holds it',
        why: 'A session moved the marker and its claim lapsed.',
        deps: [],
        readiness: 'ready',
        held: [],
      })
    default:
      return undefined
  }
}

function engine(): { transport: Transport; asked: string[][] } {
  const asked: string[][] = []
  const transport: Transport = {
    run(request) {
      asked.push([...request.argv])
      const said = answer(request.argv)
      if (said === undefined) return Promise.reject(new EngineCallFailed('unspawnable', 'no', 1))
      return Promise.resolve({ code: 0, stdout: said, stderr: '', durationMs: 1 })
    },
  }
  return { transport, asked }
}

const CATALOGUE: ProjectCatalogue = { version: 1, roots: [], projects: [] }

async function atProject(): Promise<{ asked: string[][] }> {
  const { transport, asked } = engine()
  const opened = openedFrom(await openProject(ROOT, [['python', 'launch.py']], () => transport))
  Object.defineProperty(window, 'roadkeep', {
    value: stubBridge({
      projects: () => Promise.resolve(CATALOGUE),
      open: () => Promise.resolve(opened),
      run: (root, request) => bridgedRun(() => transport.run({ ...request, root })),
      subscribe: () => () => undefined,
    }),
    configurable: true,
  })
  drawWindow({ at: projectPath(ROOT) })
  return { asked }
}

function lineOf(id: string): HTMLElement {
  const line = screen.getAllByTestId('line').find((one) => one.dataset['id'] === id)
  if (line === undefined) throw new Error(`no row for ${id}`)
  return line
}

afterEach(() => {
  Reflect.deleteProperty(window, 'roadkeep')
})

describe('RG148: one backlog, as rows', () => {
  it('names the project and its counts as stats printed them', async () => {
    await atProject()

    expect(await screen.findByRole('heading', { name: 'alpha' })).toBeTruthy()
    expect(
      await screen.findByText(
        fill(BASE['project.counts'], { open: 3, startable: 3, waiting: 0, uncounted: 0 }),
      ),
    ).toBeTruthy()
  })

  it('draws every line the list answered, symptom and why whole, in file order', async () => {
    await atProject()

    await waitFor(() => {
      expect(screen.getAllByTestId('line').map((line) => line.dataset['id'])).toEqual([
        'AL1',
        'AL2',
        'AL3',
      ])
    })
    expect(within(lineOf('AL2')).getByText('It needs what the first builds.')).toBeTruthy()
    expect(
      within(lineOf('AL1')).getByText(fill(BASE['project.design.written'], { ref: 'AL1' })),
    ).toBeTruthy()
    expect(within(lineOf('AL2')).getByText(BASE['project.design.none'])).toBeTruthy()
  })

  it('draws readiness in the engine words, with what holds a line back', async () => {
    await atProject()

    await waitFor(() => {
      expect(within(lineOf('AL2')).getByText('blocked')).toBeTruthy()
    })
    expect(
      within(lineOf('AL2')).getByText(fill(BASE['project.waiting'], { ids: 'AL1' })),
    ).toBeTruthy()
    expect(within(lineOf('AL1')).getByText('ready')).toBeTruthy()
  })

  it('says a started line nobody holds is marked and unheld, rather than choosing', async () => {
    await atProject()

    await waitFor(() => {
      expect(within(lineOf('AL3')).getByText(BASE['project.unheld'])).toBeTruthy()
    })
    // Only the working-marker line pays for a brief.
    expect(within(lineOf('AL1')).queryByText(BASE['project.unheld'])).toBeNull()
  })

  it('narrows to a block by asking list for it, and clears it on a second press', async () => {
    const { asked } = await atProject()
    await waitFor(() => {
      expect(screen.getAllByTestId('line')).toHaveLength(3)
    })

    const blocks = within(screen.getByRole('group', { name: BASE['project.blocks'] }))
    fireEvent.click(blocks.getByRole('button', { name: /B/ }))

    await waitFor(() => {
      expect(screen.getAllByTestId('line').map((line) => line.dataset['id'])).toEqual(['AL3'])
    })
    expect(asked.some((argv) => argv[2] === 'list' && argv.includes('--block'))).toBe(true)

    fireEvent.click(blocks.getByRole('button', { name: /B/ }))
    await waitFor(() => {
      expect(screen.getAllByTestId('line')).toHaveLength(3)
    })
  })

  it('draws each block with its title and open count, a finished one said so', async () => {
    await atProject()

    const blocks = within(await screen.findByRole('group', { name: BASE['project.blocks'] }))

    expect(blocks.getByText('The model')).toBeTruthy()
    expect(blocks.getByText(BASE['project.block.finished'])).toBeTruthy()
  })
})

describe('RG149: the other governed files, as tabs', () => {
  async function onTab(role: string): Promise<void> {
    await atProject()
    const tabs = within(await screen.findByRole('tablist', { name: BASE['project.roles'] }))
    fireEvent.click(tabs.getByRole('tab', { name: role }))
  }

  it('opens on the roadmap, the one tab selected', async () => {
    await atProject()

    const tabs = within(await screen.findByRole('tablist', { name: BASE['project.roles'] }))
    expect(tabs.getByRole('tab', { name: 'roadmap' }).getAttribute('aria-selected')).toBe('true')
    expect(tabs.getByRole('tab', { name: 'changelog' }).getAttribute('aria-selected')).toBe('false')
  })

  it('reads the changelog, and marks an entry the ledger later undid', async () => {
    await onTab('changelog')

    const entry = await screen.findByText('the first thing shipped')
    const row = entry.closest('li')
    expect(row).not.toBeNull()
    await waitFor(() => {
      expect(
        within(row as HTMLElement).getByText(fill(BASE['project.undone'], { by: 'AL7' })),
      ).toBeTruthy()
    })
  })

  it('reads the decisions, and a decision reasoning only when somebody opens it', async () => {
    await onTab('decisions')

    expect(await screen.findByText('The constraint that outlives the work.')).toBeTruthy()
    const reasoning = screen.getByText(BASE['project.decision.reasoning']).closest('details')
    if (reasoning === null) throw new Error('no disclosure')
    reasoning.open = true
    fireEvent(reasoning, new Event('toggle'))

    // The body as the file keeps it: its line break is still there, drawn and not reflowed.
    const body = await screen.findByText(/The reasoning,/)
    expect(body.textContent).toBe('The reasoning,\nwrapped as the file keeps it.')
  })

  it('reads the deferred store as the file has it, deps and all', async () => {
    await onTab('deferred')

    expect(await screen.findByText('this was set aside')).toBeTruthy()
    expect(screen.getByText('AL1')).toBeTruthy()
  })

  it('lists the open lines with a design written, and no other', async () => {
    await onTab('improvements')

    await waitFor(() => {
      expect(screen.getAllByTestId('entry').map((one) => one.dataset['id'])).toEqual(['AL1', 'AL3'])
    })
  })
})
