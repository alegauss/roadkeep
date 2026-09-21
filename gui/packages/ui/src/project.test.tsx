import {
  BASE,
  bridgedRun,
  counted,
  EngineCallFailed,
  fill,
  translator,
  openedFrom,
  openProject,
  type ProjectCatalogue,
  type RendererBridge,
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
    readiness: 'ready',
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
    readiness: 'blocked',
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
    readiness: 'ready',
  },
]

/** A line in one of the other governed files, shaped as `list` prints it. */
function filed(id: string, status: string, block: string, symptom: string, why: string) {
  return {
    id,
    status,
    block,
    symptom,
    why,
    deps: [] as string[],
    ref: null as string | null,
    line: 3,
    length: 80,
    // What only a `--stale` listing carries (RG28); every other role answers without them.
    since: 0,
    reason: '',
  }
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
      since: 40,
      reason: 'waiting',
    },
    {
      ...filed('AL8', '⏸', 'A', 'this was set aside second', 'set aside (waiting): later.'),
      since: 2,
      reason: 'waiting',
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
          // What the project calls itself (RG202): the folder here is `alpha`, so a header
          // saying `Turing` is a header reading the config and not the path.
          key('project', 'name', declaredName === '' ? null : `"${declaredName}"`),
        ],
      })
    case 'commands':
      // Empty unless a case asks for the validation verb (RG293): most projects on a machine
      // run an engine older than the build that grew it, and the tab is withheld for those.
      return JSON.stringify({
        version: '0.2.400',
        source: null,
        commands: publishesUnvalidated
          ? [
              {
                command: 'unvalidated',
                family: 'shipping',
                help: 'shipped entries no person has left a verdict on',
                writes: false,
                runs: true,
                published: true,
                needs: '',
                description: '',
                arguments: [
                  { spelling: ['--block'], primary: '--block', takes: 'BLOCK' },
                  { spelling: ['--json'], primary: '--json', takes: '' },
                ],
              },
              {
                command: 'validate',
                family: 'shipping',
                help: 'say what a person saw when they tried a shipped entry',
                writes: true,
                runs: true,
                published: true,
                needs: '',
                description: '',
                // The verdicts are the engine's, published here and nowhere spelled in the
                // client (RG294): what a screen offers is exactly this list.
                arguments: [
                  { spelling: ['id'], primary: 'id', positional: true, takes: 'id' },
                  {
                    spelling: ['verdict'],
                    primary: 'verdict',
                    positional: true,
                    takes: 'verdict',
                    choices: ['worked', 'failed', 'nothing to see'],
                  },
                  { spelling: ['--saw'], primary: '--saw', takes: 'SAW' },
                  { spelling: ['--files'], primary: '--files', takes: 'SYMPTOM' },
                  { spelling: ['--json'], primary: '--json', takes: '' },
                ],
              },
            ]
          : [],
      })
    case 'validate': {
      // The engine's own refusal when a case asks for one: nothing written, and the field it
      // named is what the form marks (RG5).
      const sentence = argv[argv.indexOf('--saw') + 1] ?? ''
      if (verdictRefuses)
        return JSON.stringify({
          refused: [{ code: 'saw.too-long', field: 'saw', bound: '', message: 'too long' }],
          beside: '',
          about: '',
          said: 'roadkeep: refused, nothing written: saw too long',
        })
      return JSON.stringify({
        id,
        file: 'docs/CHANGELOG.md',
        line: 12,
        verdict: argv[4] ?? '',
        rendered: `  validated **${argv[4] ?? ''}** ${sentence}`,
        replaced: verdictReplaces ? 'worked' : null,
        changed: true,
        filed: null,
        wrote: ['docs/CHANGELOG.md'],
      })
    }
    case 'unvalidated':
      return JSON.stringify({
        file: 'docs/CHANGELOG.md',
        block: null,
        governed: unvalidatedState !== 'ungoverned',
        placed: unvalidatedState !== 'unplaced',
        from: null,
        validated: 2,
        // The engine answers in the ledger's file order; the tab draws them reversed.
        unvalidated:
          unvalidatedState === 'awaiting'
            ? [
                {
                  id: 'AL0',
                  block: 'A',
                  symptom: 'the first thing shipped',
                  line: 9,
                  commit: '216066b89561b6e9c68f9bab67fe9ffe9ae014a9',
                },
                {
                  id: 'AL4',
                  block: 'B',
                  symptom: 'the newest thing shipped',
                  line: 21,
                  commit: null,
                },
              ]
            : [],
      })
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
        // One line the grammar refused, so the narrowing sentence has something to say.
        uncounted:
          argv.includes('--role') || argv.includes('--stale')
            ? []
            : [
                {
                  line: 30,
                  block: '',
                  reason: 'a marker this project does not declare',
                  raw: '- ? x',
                },
              ],
        // The order is the engine's, and only `--stale` names one (RG28).
        ...(argv.includes('--stale') ? { order: 'oldest first' } : {}),
        tasks: tasks
          .filter((line) => narrowedTo === null || line.block === narrowedTo)
          .map((line) =>
            readinessOverride === undefined ? line : { ...line, readiness: readinessOverride },
          ),
      })
    }
    case 'reversals':
      return JSON.stringify({
        root: ROOT,
        asked: null,
        reversed: [{ undone: 'AL0', by: 'AL7', line: 9, why: 'It did not hold.' }],
      })
    case 'section': {
      // Every design has a heading of its own, which is what the improvements tab draws
      // (RG171); the decisions tab asks for the same verb and reads the body.
      const headings: Record<string, string> = {
        AL9: 'Why the constraint',
        AL1: 'The first design, named',
      }
      const heading = headings[argv[4] ?? '']
      return heading === undefined
        ? undefined
        : JSON.stringify({
            anchor: argv[4],
            title: heading,
            level: 3,
            file: argv.includes('decisions') ? 'docs/DECISIONS.md' : 'docs/IMPROVEMENTS.md',
            first: 1,
            last: 4,
            words: 9,
            own_words: 9,
            body: 'The reasoning,\nwrapped as the file keeps it.',
          })
    }
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

/** Set by a test that wants every row's readiness replaced, and cleared between them. */
let readinessOverride: string | undefined

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

/** What this project declares it is called, or empty for one that declares nothing. */
let declaredName = ''

/** Whether this engine publishes `unvalidated`, which is what offers the tab (RG293). */
let publishesUnvalidated = false

/** Which of the four answers `unvalidated` gives, for the tab's four screens. */
let unvalidatedState: 'awaiting' | 'none' | 'ungoverned' | 'unplaced' = 'awaiting'

/** Whether the engine refuses the sentence a verdict carries (RG294). */
let verdictRefuses = false

/** Whether the entry already carried a verdict this one writes over. */
let verdictReplaces = false

async function atProject(
  over: {
    readiness?: string
    name?: string
    unvalidated?: 'awaiting' | 'none' | 'ungoverned' | 'unplaced'
    walkthrough?: RendererBridge['walkthrough']
    verdictRefuses?: boolean
    verdictReplaces?: boolean
  } = {},
): Promise<{ ran: string[][] }> {
  declaredName = over.name ?? ''
  publishesUnvalidated = over.unvalidated !== undefined
  unvalidatedState = over.unvalidated ?? 'awaiting'
  verdictRefuses = over.verdictRefuses === true
  verdictReplaces = over.verdictReplaces === true
  // A build that does not answer the field leaves it empty on every row, which is what the
  // reader falls back to (RG170).
  readinessOverride = over.readiness
  const { transport, asked } = engine()
  const opened = openedFrom(await openProject(ROOT, [['python', 'launch.py']], () => transport))
  Object.defineProperty(window, 'roadkeep', {
    value: stubBridge({
      projects: () => Promise.resolve(CATALOGUE),
      open: () => Promise.resolve(opened),
      run: (root, request) => bridgedRun(() => transport.run({ ...request, root })),
      subscribe: () => () => undefined,
      ...(over.walkthrough === undefined ? {} : { walkthrough: over.walkthrough }),
    }),
    configurable: true,
  })
  drawWindow({ at: projectPath(ROOT) })
  return { ran: asked }
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
    // Four fragments, joined (RG216): one sentence carrying four numbers agreed with none.
    expect(
      await screen.findByText(
        counted(translator(), [
          ['counts.open', 3],
          ['counts.startable', 3],
          ['counts.requirement', 0],
          ['counts.uncounted', 0],
        ]),
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

  it('draws readiness in the engine words, off the listing (RG170)', async () => {
    const wired = await atProject()

    await waitFor(() => {
      expect(within(lineOf('AL2')).getByText('blocked')).toBeTruthy()
    })
    expect(within(lineOf('AL1')).getByText('ready')).toBeTruthy()
    // And nothing was asked per row to draw it: `list` already classified every line.
    expect(wired.ran.filter((argv) => argv.includes('deps'))).toEqual([])
  })

  it('draws no readiness where the build does not answer it, rather than a guess', async () => {
    // A project on a roadkeep older than the field: a state, not a failure, and block D's
    // second criterion says the word is never worked out here.
    const wired = await atProject({ readiness: '' })

    await waitFor(() => {
      expect(lineOf('AL1')).toBeTruthy()
    })
    expect(within(lineOf('AL1')).queryByText('ready')).toBeNull()
    expect(within(lineOf('AL2')).queryByText('blocked')).toBeNull()
    expect(wired.ran.filter((argv) => argv.includes('deps'))).toEqual([])
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
    const { ran: asked } = await atProject()
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
    const tabs = within(await screen.findByRole('tablist', { name: BASE['project.tabs'] }))
    fireEvent.click(tabs.getByRole('tab', { name: role }))
  }

  it('opens on the roadmap, the one tab selected', async () => {
    await atProject()

    const tabs = within(await screen.findByRole('tablist', { name: BASE['project.tabs'] }))
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

  it('writes a line and a ledger entry in the responsive form that wins (RG223, RG229)', async () => {
    // Not a layout check — that is `surfaces.browser.test.tsx`, measured, since RG223's version
    // of this asserted `grid-cols-1 sm:grid-cols-[…]` and the rows carrying exactly that were
    // stacked at 1280. The design system ships `grid-cols-1` after this app's utilities, so a
    // base class it holds beats an `sm:` override. What is held here is the form: the desktop
    // grid as the base and `max-sm:` over it, on both rows, and never the form that loses. The
    // entry is held this way because no fixture opens the changelog in a browser.
    await atProject()
    const [line] = await screen.findAllByTestId('line')
    await onTab('changelog')
    const [entry] = await screen.findAllByTestId('entry')

    for (const row of [line as HTMLElement, entry as HTMLElement]) {
      expect(row.className).toContain('max-sm:grid-cols-1')
      expect(row.className).not.toMatch(/(^|\s)(grid-cols-1|sm:grid-cols-)/)
    }
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

  it('draws each pause with how long it has stood, in the order the payload came in', async () => {
    await onTab('deferred')

    await screen.findByText('this was set aside')
    // Not block order, which would put AL8 first: the store's order is the engine's (RG28).
    expect(screen.getAllByTestId('entry').map((one) => one.dataset['id'])).toEqual(['AL5', 'AL8'])
    expect(screen.getAllByTestId('stood').map((one) => one.textContent)).toEqual([
      fill(BASE['project.deferred.since'], { count: 40 }),
      fill(BASE['project.deferred.since'], { count: 2 }),
    ])
  })

  it('says which order it is looking at, in the word the engine used', async () => {
    await onTab('deferred')

    expect((await screen.findByTestId('store-order')).textContent).toBe(
      fill(BASE['project.deferred.order'], { order: 'oldest first' }),
    )
  })

  it('lists the open lines with a design written, and no other', async () => {
    await onTab('improvements')

    await waitFor(() => {
      expect(screen.getAllByTestId('entry').map((one) => one.dataset['id'])).toEqual(['AL1', 'AL3'])
    })
  })

  describe('RG171: a design named by its own heading', () => {
    it('draws each design by the heading its author gave it, beside the pointer', async () => {
      await onTab('improvements')

      await waitFor(() => {
        expect(screen.getAllByTestId('design-name')[0]?.textContent).toBe(
          `The first design, named${fill(BASE['project.design.written'], { ref: 'AL1' })}`,
        )
      })
    })

    it('keeps the pointer where the heading never comes back, rather than emptying the row', async () => {
      // AL3's section is one the engine has nothing to say about, which is the state the
      // row is in before any of them land and the one it stays in if a read fails.
      await onTab('improvements')

      await waitFor(() => {
        expect(screen.getAllByTestId('design-name')[0]?.textContent).toContain('named')
      })
      expect(screen.getAllByTestId('design-name')[1]?.textContent).toBe(
        fill(BASE['project.design.written'], { ref: 'AL3' }),
      )
    })
  })
})

describe('RG172: a narrowed listing, in the window’s language', () => {
  it('says which case it is from the catalogue, and quotes the gate’s own reasons', async () => {
    await atProject()

    const narrowed = await screen.findByTestId('narrowed')
    expect(narrowed.textContent).toContain(
      fill(BASE['backlog.refused.one'], { file: 'docs/ROADMAP.md', count: '1' }),
    )
    // The engine's words after this app's sentence, not instead of it.
    expect(narrowed.textContent).toContain('a marker this project does not declare')
  })
})

describe('RG170: the narrowing the engine does', () => {
  it('asks list for the startable ones, rather than deciding here', async () => {
    const { ran: asked } = await atProject()
    await waitFor(() => {
      expect(screen.getAllByTestId('line')).toHaveLength(3)
    })

    fireEvent.click(screen.getByRole('button', { name: BASE['project.filter.startable'] }))

    await waitFor(() => {
      expect(asked.some((argv) => argv[2] === 'list' && argv.includes('--startable'))).toBe(true)
    })
  })

  it('clears it on a second press, so the flag stops being sent', async () => {
    const { ran: asked } = await atProject()
    await waitFor(() => {
      expect(screen.getAllByTestId('line')).toHaveLength(3)
    })
    const chip = screen.getByRole('button', { name: BASE['project.filter.startable'] })

    fireEvent.click(chip)
    await waitFor(() => {
      expect(asked.some((argv) => argv.includes('--startable'))).toBe(true)
    })
    const before = asked.length
    fireEvent.click(chip)

    await waitFor(() => {
      expect(asked.length).toBeGreaterThan(before)
    })
    expect(asked.slice(before).some((argv) => argv.includes('--startable'))).toBe(false)
  })
})

describe('RG202: the name this screen shows', () => {
  it('is what the project declares, and not the folder it sits in', async () => {
    await atProject({ name: 'Turing' })

    await waitFor(() => {
      expect(screen.getByText('Turing')).toBeTruthy()
    })
    // The fixture's folder, which is what a worktree's path says and a product's name is not.
    expect(screen.queryByRole('heading', { name: 'alpha' })).toBeNull()
  })

  it('falls back to the folder where the project declares nothing', async () => {
    await atProject()

    await waitFor(() => {
      expect(screen.getByText('alpha')).toBeTruthy()
    })
  })
})

describe('RG293: what is shipped and unlooked-at, beside the ledger', () => {
  it('draws the entries awaiting a person, newest first', async () => {
    await atProject({ unvalidated: 'awaiting' })

    fireEvent.click(await screen.findByTestId('validation-tab'))

    const rows = await screen.findAllByTestId('unvalidated')
    // The engine answered in the ledger's file order; the tab reads it from the end, because
    // what somebody will actually check is what they just shipped.
    expect(rows.map((row) => row.dataset['id'])).toEqual(['AL4', 'AL0'])
    expect(within(rows[1] as HTMLElement).getByText('the first thing shipped')).toBeTruthy()
    // The shipping commit where the history could say, and nothing drawn where it could not.
    expect(within(rows[1] as HTMLElement).getByText(/216066b8/)).toBeTruthy()
    expect(within(rows[0] as HTMLElement).queryByText(/216066b8/)).toBeNull()
    // The order said out loud, with the engine's own count of what already has a verdict.
    expect(screen.getByTestId('validation-order').textContent).toContain(
      BASE['project.validation.newest'],
    )
    expect(screen.getByTestId('validation-order').textContent).toContain(
      fill(BASE['project.validation.validated'], { count: 2 }),
    )
  })

  it('says which of the three ways the list is empty', async () => {
    // Every entry answered, which is the screen this whole block exists to produce.
    await atProject({ unvalidated: 'none' })
    fireEvent.click(await screen.findByTestId('validation-tab'))
    expect(await screen.findByText(BASE['project.validation.none'])).toBeTruthy()
    expect(screen.queryAllByTestId('unvalidated')).toEqual([])
  })

  it('says a project that never asked the question is not asking it', async () => {
    await atProject({ unvalidated: 'ungoverned' })
    fireEvent.click(await screen.findByTestId('validation-tab'))

    expect(await screen.findByText(BASE['project.validation.ungoverned'])).toBeTruthy()
  })

  it('says a history that cannot place where looking starts, which is not the same', async () => {
    await atProject({ unvalidated: 'unplaced' })
    fireEvent.click(await screen.findByTestId('validation-tab'))

    expect(await screen.findByText(BASE['project.validation.unplaced'])).toBeTruthy()
  })

  it('withholds the whole tab where this engine cannot run the read', async () => {
    // RG6's mechanism, and why nothing here waited on the upstream work: a project whose
    // engine publishes no `unvalidated` is offered no door rather than one that is refused.
    await atProject()

    await waitFor(() => {
      expect(screen.getAllByTestId('line')).toHaveLength(3)
    })
    expect(screen.queryByTestId('validation-tab')).toBeNull()
  })

  it('asks nothing of Claude Code for a list being scrolled past', async () => {
    await atProject({ unvalidated: 'awaiting' })
    fireEvent.click(await screen.findByTestId('validation-tab'))
    await screen.findAllByTestId('unvalidated')

    // The dialog is what asks, and nothing has opened one: a walkthrough costs a wait and
    // somebody's tokens, so it is never speculative.
    expect(screen.queryByTestId('check-dialog')).toBeNull()
    expect(screen.getAllByTestId('check')).toHaveLength(2)
  })
})

describe('RG293: how to check one entry, on asking', () => {
  const WALKED = {
    kind: 'said' as const,
    walkthrough: {
      before: ['a build of the app'],
      steps: [{ does: 'open the entry', sees: 'the steps are drawn' }],
      where: [{ path: 'packages/core/src/verbs.ts', said: 'the row lives here' }],
      nothingToSee: '',
    },
    model: 'claude-opus-5',
    version: '2.1.278',
    kept: true,
    stale: false,
    commit: '216066b89561b6e9c68f9bab67fe9ffe9ae014a9',
  }

  /** Open the tab and press the button on the newest row. */
  async function openCheck(walkthrough: RendererBridge['walkthrough']) {
    await atProject({ unvalidated: 'awaiting', walkthrough })
    fireEvent.click(await screen.findByTestId('validation-tab'))
    const rows = await screen.findAllByTestId('unvalidated')
    fireEvent.click(within(rows[0] as HTMLElement).getByTestId('check'))
    return within(await screen.findByTestId('check-dialog'))
  }

  it('draws the steps as pairs, each with what it should produce', async () => {
    const dialog = await openCheck(() => Promise.resolve(WALKED))

    await dialog.findByTestId('check-said')
    expect(dialog.getByText('open the entry')).toBeTruthy()
    expect(dialog.getByText(/the steps are drawn/)).toBeTruthy()
    expect(dialog.getByText('a build of the app')).toBeTruthy()
    expect(dialog.getByText('packages/core/src/verbs.ts')).toBeTruthy()
    // Who wrote it and what it was written about, which is what makes it checkable at all.
    expect(dialog.getByTestId('check-commit').textContent).toContain('216066b8')
    expect(dialog.queryByTestId('check-stale')).toBeNull()
  })

  it('draws a change nobody can open as that, with no steps beside it', async () => {
    const dialog = await openCheck(() =>
      Promise.resolve({
        ...WALKED,
        walkthrough: {
          before: [],
          steps: [],
          where: [],
          nothingToSee: 'Two rows in a verb table: nothing is drawn.',
        },
      }),
    )

    expect(await dialog.findByTestId('check-nothing')).toBeTruthy()
    expect(dialog.queryByTestId('check-steps')).toBeNull()
  })

  it('says one written about another commit is old, and still draws it', async () => {
    const dialog = await openCheck(() => Promise.resolve({ ...WALKED, stale: true }))

    expect(await dialog.findByTestId('check-stale')).toBeTruthy()
    expect(dialog.getByText('open the entry')).toBeTruthy()
  })

  it('says why there is none, in this app words for what the far side answered', async () => {
    const dialog = await openCheck(() =>
      Promise.resolve({ kind: 'unavailable', tried: [['claude'], ['claude.cmd']] }),
    )

    expect((await dialog.findByTestId('check-failed')).textContent).toContain('claude.cmd')
  })
})

/** The verdict radios, typed as what they are: inputs a test reads the checked state of. */
function radios(dialog: ReturnType<typeof within>): HTMLInputElement[] {
  return dialog.getAllByRole('radio').map((one: HTMLElement) => {
    if (!(one instanceof HTMLInputElement)) throw new Error('a verdict is not a radio input')
    return one
  })
}

/** The sentence box, typed as what it is: a textarea a test reads the value of. */
function dialogTextarea(dialog: ReturnType<typeof within>): HTMLTextAreaElement {
  const box = dialog.getByTestId('verdict-saw')
  if (!(box instanceof HTMLTextAreaElement)) throw new Error('the sentence box is not a textarea')
  return box
}

describe('RG294: saying what happened, under the steps', () => {
  const WALKED = {
    kind: 'said' as const,
    walkthrough: {
      before: [],
      steps: [{ does: 'open the entry', sees: 'the steps are drawn' }],
      where: [],
      nothingToSee: '',
    },
    model: 'claude-opus-5',
    version: '2.1.278',
    kept: true,
    stale: false,
    commit: '216066b89561b6e9c68f9bab67fe9ffe9ae014a9',
  }

  async function openForm(
    over: {
      walkthrough?: RendererBridge['walkthrough']
      verdictRefuses?: boolean
      verdictReplaces?: boolean
    } = {},
  ) {
    const { ran } = await atProject({
      unvalidated: 'awaiting',
      walkthrough: over.walkthrough ?? (() => Promise.resolve(WALKED)),
      ...(over.verdictRefuses === undefined ? {} : { verdictRefuses: over.verdictRefuses }),
      ...(over.verdictReplaces === undefined ? {} : { verdictReplaces: over.verdictReplaces }),
    })
    fireEvent.click(await screen.findByTestId('validation-tab'))
    const rows = await screen.findAllByTestId('unvalidated')
    fireEvent.click(within(rows[0] as HTMLElement).getByTestId('check'))
    const dialog = within(await screen.findByTestId('check-dialog'))
    await dialog.findByTestId('verdict-form')
    return { dialog, ran }
  }

  it('offers exactly the verdicts the engine published, and none of its own', async () => {
    const { dialog } = await openForm()

    const chips = dialog.getAllByTestId('verdict-choice')
    expect(chips.map((chip) => chip.dataset['verdict'])).toEqual([
      'worked',
      'failed',
      'nothing to see',
    ])
    // Each said in this window's language, which is a label and not the set.
    expect(dialog.getByText(BASE['project.validation.verdict.worked'])).toBeTruthy()
  })

  it('sends the verdict and the sentence through validate, as the write table spells it', async () => {
    const { dialog, ran } = await openForm()

    fireEvent.click(dialog.getByText(BASE['project.validation.verdict.worked']))
    fireEvent.change(dialog.getByTestId('verdict-saw'), {
      target: { value: 'Opened it and the listing came back.' },
    })
    fireEvent.click(dialog.getByTestId('verdict-send'))

    await waitFor(() => {
      expect(dialog.queryByTestId('verdict-wrote')).toBeTruthy()
    })
    const sent = ran.find((argv) => argv.includes('validate'))
    // Two positionals in the verb's order, then the sentence as one argument.
    expect(sent?.slice(sent.indexOf('validate') + 1, sent.indexOf('validate') + 3)).toEqual([
      'AL4',
      'worked',
    ])
    expect(sent).toContain('Opened it and the listing came back.')
  })

  it('will not send a verdict with no account of it, which is a tick box', async () => {
    const { dialog, ran } = await openForm()

    fireEvent.click(dialog.getByText(BASE['project.validation.verdict.failed']))
    fireEvent.click(dialog.getByTestId('verdict-send'))

    expect(ran.some((argv) => argv.includes('validate'))).toBe(false)
  })

  it('marks a sentence the engine refused, rather than closing the sheet', async () => {
    const { dialog } = await openForm({ verdictRefuses: true })

    fireEvent.click(dialog.getByText(BASE['project.validation.verdict.worked']))
    fireEvent.change(dialog.getByTestId('verdict-saw'), { target: { value: 'far too much' } })
    fireEvent.click(dialog.getByTestId('verdict-send'))

    // The engine's own sentence, quoted, and the form still there to correct.
    expect((await dialog.findByTestId('verdict-refused')).textContent).toContain('saw too long')
    expect(dialog.getByTestId('verdict-form')).toBeTruthy()
  })

  it('says a second verdict wrote over the first, since the last one wins', async () => {
    const { dialog } = await openForm({ verdictReplaces: true })

    fireEvent.click(dialog.getByText(BASE['project.validation.verdict.worked']))
    fireEvent.change(dialog.getByTestId('verdict-saw'), { target: { value: 'It worked.' } })
    fireEvent.click(dialog.getByTestId('verdict-send'))

    expect(await dialog.findByTestId('verdict-replaced')).toBeTruthy()
  })

  it('pre-selects the one answer it suggests, with the run own sentence in the box', async () => {
    const { dialog } = await openForm({
      walkthrough: () =>
        Promise.resolve({
          ...WALKED,
          walkthrough: {
            before: [],
            steps: [],
            where: [],
            nothingToSee: 'Two rows in a verb table: nothing is drawn.',
          },
        }),
    })

    const chosen = radios(dialog).find((radio) => radio.checked)
    expect(chosen?.value).toBe('nothing to see')
    // The agent's own words, to accept or rewrite — the only answer this app ever suggests.
    expect(dialogTextarea(dialog).value).toBe('Two rows in a verb table: nothing is drawn.')
  })

  it('suggests nothing where the run found something to open', async () => {
    const { dialog } = await openForm()

    expect(radios(dialog).every((radio) => !radio.checked)).toBe(true)
    expect(dialogTextarea(dialog).value).toBe('')
  })

  it('asks the list again once a verdict lands, since the list is a query', async () => {
    const { dialog, ran } = await openForm()
    const before = ran.filter((argv) => argv.includes('unvalidated')).length

    fireEvent.click(dialog.getByText(BASE['project.validation.verdict.worked']))
    fireEvent.change(dialog.getByTestId('verdict-saw'), { target: { value: 'It worked.' } })
    fireEvent.click(dialog.getByTestId('verdict-send'))

    await waitFor(() => {
      expect(ran.filter((argv) => argv.includes('unvalidated')).length).toBeGreaterThan(before)
    })
  })
})
