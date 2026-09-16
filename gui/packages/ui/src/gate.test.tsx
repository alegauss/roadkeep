import {
  BASE,
  bridgedRun,
  counted,
  EngineCallFailed,
  fill,
  translator,
  openedFrom,
  openProject,
  type BridgedRequest,
  type BridgedResult,
  type Transport,
  BASE_LOCALE,
  timeIn,
  type GateHealth,
  type ProjectGate,
  withheldResult,
} from '@rk/core'
import { fireEvent, screen, waitFor, within } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'

const say = translator()

import { gatePath } from './areas'
import { drawWindow } from './harness'
import { readDeadline } from './launch'
import { stubBridge } from './stub-bridge'

/**
 * RG152: the gate as a surface, drawn through the whole window at its route.
 *
 * What is held is that the findings are the report's, that each door is offered by the place
 * it holds in the batch the carrier kept — not by where the screen groups it — that taking one
 * runs the gate again, and that a note is not drawn as a finding.
 */

const ROOT = 'D:\\code\\alpha'

const key = (table: string, name: string, set: string | null) => ({
  table,
  key: name,
  address: `${table}.${name}`,
  declared: set !== null,
  set,
  default: null,
})

/**
 * A report whose first `doors` list belongs to a note, ahead of the findings in the
 * document: the case where a screen numbering doors by its own grouping runs the wrong one.
 */
const DRIFTED = {
  root: ROOT,
  clean: false,
  checked: ['docs/ROADMAP.md', 'docs/IMPROVEMENTS.md'],
  lines: 12,
  sections: 4,
  problems: 1,
  codes: { 'ref.unresolved': 1 },
  notes: [
    {
      code: 'install.stale',
      file: '.claude/hooks/roadkeep-launch.py',
      line: null,
      column: null,
      id: null,
      message: 'this surface is behind the roadkeep answering here',
      remedy: {
        kind: 'run',
        decision: '',
        sequence: false,
        awaits: '',
        doors: [
          { argv: ['install'], what: 'rewrites the wired launcher', complete: true, writes: true },
        ],
      },
    },
  ],
  findings: [
    {
      code: 'ref.unresolved',
      file: 'docs/ROADMAP.md',
      line: 5,
      column: null,
      id: 'AL7',
      message: 'points at §AL7, which is not in docs/IMPROVEMENTS.md',
      remedy: {
        kind: 'compose',
        decision: '',
        sequence: false,
        awaits: '',
        doors: [
          {
            argv: ['section', 'add', 'AL7', '--title', '…'],
            what: 'writes the section the line points at',
            complete: false,
            writes: true,
          },
          // A door whose prose the engine reads on standard input (RG261). `complete`, which
          // the engine means about the argv — there is nothing in it left to fill.
          {
            argv: ['section', 'amend', 'AL7', '--body', '-', '--role', 'improvements'],
            what: 'the sentence is this section’s, so the rewrite arrives on stdin',
            complete: true,
            writes: true,
          },
        ],
      },
    },
  ],
}

const CLEAN = {
  root: ROOT,
  clean: true,
  checked: ['docs/ROADMAP.md'],
  lines: 12,
  sections: 4,
  problems: 0,
  codes: {},
  findings: [],
  notes: [],
}

interface Wired {
  /** Every gate run this window asked for, as it asked for it — the deadline included (RG260). */
  readonly gates: BridgedRequest[]
  readonly doors: { which: number; words: readonly string[] }[]
  /** Each code `explain` was asked about, in order (RG258). */
  readonly explained: string[]
  /** What the next gate answers: the first run drifts, and a door closes it. */
  clean: boolean
  /** What the door answers, so a door that would not run can be drawn (RG260). */
  doorFails: string | null
}

/** What `explain` answers about a code, which is the class and not the line (RG258). */
const EXPLAINED = {
  code: 'ref.unresolved',
  kind: 'reference',
  cause: 'a line points at a section no prose file declares',
  varies: 'in the decisions role it means the same about that file',
  sequence: false,
  awaits: '',
  doors: [
    { argv: ['section', 'add', '…'], what: 'writes the section', complete: false, writes: true },
  ],
}

/** The published commands: `explain` among them unless a test says this build lacks it. */
const PUBLISHED = (explains: boolean) =>
  explains
    ? [
        {
          command: 'explain',
          family: 'reading',
          help: 'what a code means',
          writes: false,
          runs: true,
          tool: false,
          arguments: [],
        },
      ]
    : []

function engine(explains = true, asked: string[] = []): Transport {
  return {
    run(request) {
      const verb = request.argv[2] ?? ''
      const said = (value: unknown) =>
        Promise.resolve({ code: 0, stdout: JSON.stringify(value), stderr: '', durationMs: 1 })
      switch (verb) {
        case 'engines':
          return said({
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
          return said({
            version: '0.2.400',
            source: 'roadkeep.toml',
            keys: [key('files', 'roadmap', '"docs/ROADMAP.md"')],
          })
        case 'commands':
          return said({ version: '0.2.400', source: null, commands: PUBLISHED(explains) })
        case 'explain':
          asked.push(request.argv[3] ?? '')
          return said({ ...EXPLAINED, code: request.argv[3] ?? '' })
        default:
          return Promise.reject(new EngineCallFailed('unspawnable', 'no', 1))
      }
    },
  }
}

async function at(
  path: string,
  held: readonly ProjectGate[] = [],
  explains = true,
): Promise<Wired> {
  const explained: string[] = []
  const transport = engine(explains, explained)
  const opened = openedFrom(await openProject(ROOT, [['python', 'launch.py']], () => transport))
  const wired: Wired = { gates: [], doors: [], clean: false, doorFails: null, explained }

  Object.defineProperty(window, 'roadkeep', {
    value: stubBridge({
      projects: () => Promise.resolve({ version: 1, roots: [], projects: [] }),
      open: () => Promise.resolve(opened),
      subscribe: () => () => undefined,
      sessions: () => Promise.resolve([]),
      gates: () => Promise.resolve(held),
      run: (root, request): Promise<BridgedResult> => {
        if (!request.argv.includes('lint')) {
          return bridgedRun(() => transport.run({ ...request, root }))
        }
        wired.gates.push(request)
        const answer = wired.clean ? CLEAN : DRIFTED
        return Promise.resolve({
          kind: 'ran',
          // A gate that found something exits 1 and is still an answer.
          result: {
            code: wired.clean ? 0 : 1,
            stdout: JSON.stringify(answer),
            stderr: '',
            durationMs: 1,
          },
          offered: 'batch-1',
        })
      },
      door: (_root, _offered, which, words) => {
        wired.doors.push({ which, words })
        if (wired.doorFails !== null) return Promise.resolve(withheldResult(wired.doorFails))
        // The door wrote the section, so the gate that follows finds nothing.
        wired.clean = true
        return Promise.resolve({
          kind: 'ran',
          result: { code: 0, stdout: '{"wrote":[]}', stderr: '', durationMs: 1 },
        })
      },
    }),
    configurable: true,
  })
  drawWindow({ at: path })
  return wired
}

afterEach(() => {
  Reflect.deleteProperty(window, 'roadkeep')
})

describe('RG152: the gate as a surface', () => {
  it('runs as it opens, and says what the run counted', async () => {
    const wired = await at(gatePath(ROOT))

    expect(await screen.findByTestId('counted')).toBeTruthy()
    expect(screen.getByTestId('counted').textContent).toBe(
      // One finding, so the singular, over a row of what was read (RG216).
      fill(BASE['gate.problems.one'], {
        count: 1,
        counted: counted(say, [
          ['counts.lines', 12],
          ['counts.sections', 4],
        ]),
      }),
    )
    expect(wired.gates).toHaveLength(1)
  })

  it('draws a finding as a row, with the code, the place and the sentence lint wrote', async () => {
    await at(gatePath(ROOT))

    const finding = await screen.findByTestId('finding')
    expect(within(finding).getByText('ref.unresolved')).toBeTruthy()
    expect(within(finding).getByText('docs/ROADMAP.md:5')).toBeTruthy()
    expect(
      within(finding).getByText('points at §AL7, which is not in docs/IMPROVEMENTS.md'),
    ).toBeTruthy()
  })

  it('says what the gate says without failing for it, apart from the findings', async () => {
    await at(gatePath(ROOT))

    // Two reports, and the count is the findings' alone: a note drawn as a finding would
    // report a project as having twice the problems the gate gave it.
    await screen.findByTestId('counted')
    expect(screen.getByText(BASE['gate.notes'])).toBeTruthy()
    expect(screen.getAllByTestId('finding')).toHaveLength(1)
    expect(screen.getAllByTestId('note')).toHaveLength(1)
  })

  it('takes a door by the place it holds in the batch, not by the row it is drawn in', async () => {
    const wired = await at(gatePath(ROOT))

    const finding = await screen.findByTestId('finding')
    // The first of the finding's two: the one whose blank is a word (RG261).
    const door = within(finding).getAllByTestId('door')[0]
    if (door === undefined) throw new Error('no door')
    fireEvent.change(within(door).getByLabelText(BASE['door.blank']), {
      target: { value: 'A design' },
    })
    fireEvent.click(within(door).getByRole('button', { name: BASE['door.take'] }))

    // The note's door is first in the document, so the finding's is the second of the batch.
    await waitFor(() => {
      expect(wired.doors).toEqual([{ which: 1, words: ['A design'] }])
    })
  })

  it('runs the gate again after a door, so the row goes when the finding does', async () => {
    const wired = await at(gatePath(ROOT))

    const finding = await screen.findByTestId('finding')
    // The first of the finding's two: the one whose blank is a word (RG261).
    const door = within(finding).getAllByTestId('door')[0]
    if (door === undefined) throw new Error('no door')
    fireEvent.change(within(door).getByLabelText(BASE['door.blank']), {
      target: { value: 'A design' },
    })
    fireEvent.click(within(door).getByRole('button', { name: BASE['door.take'] }))

    expect(
      await screen.findByText(
        fill(BASE['gate.clean'], {
          counted: counted(say, [
            ['counts.lines', 12],
            ['counts.sections', 4],
          ]),
        }),
      ),
    ).toBeTruthy()
    expect(screen.queryAllByTestId('finding')).toHaveLength(0)
    expect(wired.gates).toHaveLength(2)
  })

  it('asks for the prose a dash door reads, instead of offering it as one click (RG261)', async () => {
    const wired = await at(gatePath(ROOT))

    const finding = await screen.findByTestId('finding')
    const reads = within(finding).getAllByTestId('door')[1]
    if (reads === undefined) throw new Error('no second door')

    // It was offered as a fix to press, and the engine then waited on prose nobody wrote.
    const take = within(reads).getByRole('button', { name: BASE['door.take'] })
    expect(take.hasAttribute('disabled')).toBe(true)

    fireEvent.change(within(reads).getByLabelText(BASE['door.body']), {
      target: { value: 'The sentence, repointed.\n\nA second paragraph.' },
    })
    fireEvent.click(within(reads).getByRole('button', { name: BASE['door.take'] }))

    // The finding's doors are second and third in the batch, the note's being first.
    await waitFor(() => {
      expect(wired.doors).toEqual([
        { which: 2, words: ['The sentence, repointed.\n\nA second paragraph.'] },
      ])
    })
  })

  it('draws that field as prose, since a body runs to paragraphs (RG261)', async () => {
    await at(gatePath(ROOT))

    const finding = await screen.findByTestId('finding')
    const reads = within(finding).getAllByTestId('door')[1]
    if (reads === undefined) throw new Error('no second door')

    expect(within(reads).getByLabelText(BASE['door.body']).tagName).toBe('TEXTAREA')
    // And the one-word blank on the door above it is still a one-line box.
    const fills = within(finding).getAllByTestId('door')[0]
    expect(within(fills ?? reads).getByLabelText(BASE['door.blank']).tagName).toBe('INPUT')
  })

  it('bounds its own run by the declared deadline, so running has a floor (RG260)', async () => {
    const wired = await at(gatePath(ROOT))
    await screen.findByTestId('counted')

    // The request names no tool, so it is spawned — and a spawn with no `timeoutMs` has no
    // ceiling at all, which is what left this screen saying `Running the gate.` for good.
    expect(wired.gates[0]?.timeoutMs).toBe(readDeadline())
  })

  it('bounds the run a door starts too, since that is the one somebody pressed (RG260)', async () => {
    const wired = await at(gatePath(ROOT))

    const finding = await screen.findByTestId('finding')
    // The first of the finding's two: the one whose blank is a word (RG261).
    const door = within(finding).getAllByTestId('door')[0]
    if (door === undefined) throw new Error('no door')
    fireEvent.change(within(door).getByLabelText(BASE['door.blank']), {
      target: { value: 'A design' },
    })
    fireEvent.click(within(door).getByRole('button', { name: BASE['door.take'] }))

    await waitFor(() => {
      expect(wired.gates).toHaveLength(2)
    })
    expect(wired.gates[1]?.timeoutMs).toBe(readDeadline())
  })

  it('says a door that would not run, above the report it left unchanged (RG260)', async () => {
    const wired = await at(gatePath(ROOT))
    wired.doorFails = 'the engine ran past 15000ms'

    const finding = await screen.findByTestId('finding')
    // The first of the finding's two: the one whose blank is a word (RG261).
    const door = within(finding).getAllByTestId('door')[0]
    if (door === undefined) throw new Error('no door')
    fireEvent.change(within(door).getByLabelText(BASE['door.blank']), {
      target: { value: 'A design' },
    })
    fireEvent.click(within(door).getByRole('button', { name: BASE['door.take'] }))

    // The gate ran again and found the finding still there, which is what a door that did
    // nothing and a door that never ran both look like. The refusal is what tells them apart.
    expect(
      await screen.findByText(fill(BASE['door.failed'], { reason: 'the engine ran past 15000ms' })),
    ).toBeTruthy()
    expect(screen.getAllByTestId('finding')).toHaveLength(1)
  })

  it('drops that refusal when the reader runs the gate themselves (RG260)', async () => {
    const wired = await at(gatePath(ROOT))
    wired.doorFails = 'the engine ran past 15000ms'

    const finding = await screen.findByTestId('finding')
    // The first of the finding's two: the one whose blank is a word (RG261).
    const door = within(finding).getAllByTestId('door')[0]
    if (door === undefined) throw new Error('no door')
    fireEvent.change(within(door).getByLabelText(BASE['door.blank']), {
      target: { value: 'A design' },
    })
    fireEvent.click(within(door).getByRole('button', { name: BASE['door.take'] }))
    await screen.findByTestId('door-failed')

    fireEvent.click(screen.getByRole('button', { name: BASE['gate.run'] }))

    // A run the reader asked for answers for itself, and the door before it is over. The
    // click also passes an event as the handler's first argument, which a `run` taking the
    // refusal directly would have drawn back over this screen.
    await waitFor(() => {
      expect(screen.queryByTestId('door-failed')).toBeNull()
    })
  })

  it('is a tab of the project, counted off the ledger and opened by a click (RG255)', async () => {
    const wired = await at(`/project/${encodeURIComponent(ROOT)}`, [
      {
        root: ROOT,
        health: {
          verdict: 'drifted',
          problems: 3,
          taken: '2026-09-11T12:00:00.000Z',
          stale: false,
        },
      },
    ])

    // The count a reader saw on the portfolio row is on the tab, before it is opened. Awaited,
    // because the ledger is a read: the tab is drawn as soon as the project is, and the count
    // lands when `gates` answers.
    const tab = await screen.findByTestId('gate-tab')
    expect(
      await within(tab).findByText(fill(BASE['portfolio.gate.findings'], { count: 3 })),
    ).toBeTruthy()
    expect(wired.gates).toEqual([])

    fireEvent.click(tab)

    // And opening it is what runs the gate, drawing the rows the count never held (RG254).
    await screen.findByTestId('counted')
    expect(wired.gates).toHaveLength(1)
    expect(screen.getByTestId('gate-tab').getAttribute('aria-selected')).toBe('true')
  })
})

describe('RG258: what a finding’s code means', () => {
  it('asks explain once per code, and draws what it answered in the engine’s words', async () => {
    const wired = await at(gatePath(ROOT))
    await screen.findByTestId('counted')

    // Two rows, two codes: the note carries `install.stale` and the finding `ref.unresolved`.
    const [first] = screen.getAllByTestId('explain')
    if (first === undefined) throw new Error('no disclosure')
    fireEvent.click(within(first).getByText('ref.unresolved'))

    expect(await within(first).findByTestId('explained')).toBeTruthy()
    expect(
      within(first).getByText('a line points at a section no prose file declares'),
    ).toBeTruthy()
    // What the class means where it means something else, which is what `varies` is for.
    expect(
      within(first).getByText('in the decisions role it means the same about that file'),
    ).toBeTruthy()
    expect(wired.explained).toEqual(['ref.unresolved'])
  })

  it('reads nothing a second time for a code it has already asked about', async () => {
    const wired = await at(gatePath(ROOT))
    await screen.findByTestId('counted')
    const [first] = screen.getAllByTestId('explain')
    if (first === undefined) throw new Error('no disclosure')

    fireEvent.click(within(first).getByText('ref.unresolved'))
    await within(first).findByTestId('explained')
    // Closed and opened again: a code is a class, and its explanation does not change while
    // a screen is up.
    fireEvent.click(within(first).getByText('ref.unresolved'))
    fireEvent.click(within(first).getByText('ref.unresolved'))
    await within(first).findByTestId('explained')

    expect(wired.explained).toEqual(['ref.unresolved'])
  })

  it('draws no disclosure at all where this build does not answer explain', async () => {
    const wired = await at(gatePath(ROOT), [], false)
    await screen.findByTestId('counted')

    // A control that opens on a refusal is a control that lies: the code stays a pill.
    expect(screen.queryAllByTestId('explain')).toEqual([])
    expect(screen.getAllByText('ref.unresolved').length).toBeGreaterThan(0)
    expect(wired.explained).toEqual([])
  })
})

describe('RG185: opening on the verdict already held', () => {
  const verdict = (over: Partial<GateHealth> = {}): ProjectGate => ({
    root: ROOT,
    health: {
      verdict: 'drifted',
      problems: 3,
      taken: '2026-09-11T12:00:00.000Z',
      stale: false,
      ...over,
    },
  })

  it('opens on a clean verdict, running nothing, where the files have not moved', async () => {
    const wired = await at(gatePath(ROOT), [verdict({ verdict: 'clean', problems: 0 })])

    expect((await screen.findByTestId('held')).textContent).toBe(BASE['gate.held.clean'])
    expect(wired.gates).toEqual([])
  })

  it('runs for a drifted verdict, since its rows are what the ledger never held (RG254)', async () => {
    // `6 findings when it last ran` is a count with no row, no code and no door, and the
    // rows are what somebody opened this screen to read.
    const wired = await at(gatePath(ROOT), [verdict()])

    // The held sentence is drawn while the run happens, so the count does not vanish.
    expect((await screen.findByTestId('held')).textContent).toBe(
      fill(BASE['gate.held.drifted'], { count: 3 }),
    )
    await screen.findByTestId('counted')
    expect(wired.gates).toHaveLength(1)
    expect(screen.getAllByTestId('finding').length).toBeGreaterThan(0)
  })

  it('says when it last ran, in the language the window speaks', async () => {
    await at(gatePath(ROOT), [verdict({ verdict: 'clean', problems: 0 })])

    await screen.findByTestId('held')
    expect(
      screen.getByText(
        fill(BASE['gate.taken'], { taken: timeIn('2026-09-11T12:00:00.000Z', BASE_LOCALE) }),
      ),
    ).toBeTruthy()
  })

  it('runs where the files moved under the verdict, since it is about a state that has gone', async () => {
    const wired = await at(gatePath(ROOT), [verdict({ stale: true })])

    await screen.findByTestId('counted')
    expect(wired.gates).toHaveLength(1)
  })

  it('runs where nothing is on record, which is what unknown means', async () => {
    const wired = await at(gatePath(ROOT), [])

    await screen.findByTestId('counted')
    expect(wired.gates).toHaveLength(1)
  })

  it('runs when a person presses it, whatever the ledger holds', async () => {
    const wired = await at(gatePath(ROOT), [verdict({ verdict: 'clean', problems: 0 })])

    await screen.findByTestId('held')
    fireEvent.click(screen.getByRole('button', { name: BASE['gate.run'] }))

    await screen.findByTestId('counted')
    expect(wired.gates).toHaveLength(1)
  })
})

describe('RG192: a refusal drawn in the window’s language', () => {
  /** The window at the gate, where the carrier refuses the read rather than running it. */
  async function refusing(answer: BridgedResult): Promise<void> {
    const transport = engine()
    const opened = openedFrom(await openProject(ROOT, [['python', 'launch.py']], () => transport))

    Object.defineProperty(window, 'roadkeep', {
      value: stubBridge({
        projects: () => Promise.resolve({ version: 1, roots: [], projects: [] }),
        open: () => Promise.resolve(opened),
        subscribe: () => () => undefined,
        sessions: () => Promise.resolve([]),
        gates: () => Promise.resolve([]),
        run: (_root, request): Promise<BridgedResult> =>
          request.argv.includes('lint')
            ? Promise.resolve(answer)
            : bridgedRun(() => transport.run({ ...request, root: ROOT })),
      }),
      configurable: true,
    })
    drawWindow({ at: gatePath(ROOT) })
  }

  it('says the catalogue sentence for the code, and not the English it carried', async () => {
    const english = `${ROOT} is not a project the scan of the person’s roots found`
    await refusing(withheldResult(english, 'not-catalogued', { root: ROOT }))

    const said = fill(BASE['withheld.not-catalogued'], { root: ROOT })
    expect(await screen.findByText(fill(BASE['gate.failed'], { reason: said }))).toBeTruthy()
    // The whole point: the sentence the far side wrote is on no screen.
    expect(screen.queryByText(fill(BASE['gate.failed'], { reason: english }))).toBeNull()
  })

  it('quotes prose nobody translates, which is what an empty code means', async () => {
    // This app's own report of a command line it composed: a defect report naming a flag,
    // drawn as written because a translation of it would say the same identifiers.
    const said = '`--nope` is not an option this app composes `lint` with'
    await refusing(withheldResult(said))

    expect(await screen.findByText(fill(BASE['gate.failed'], { reason: said }))).toBeTruthy()
  })
})
