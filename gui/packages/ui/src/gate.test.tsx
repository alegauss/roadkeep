import {
  BASE,
  bridgedRun,
  EngineCallFailed,
  fill,
  openedFrom,
  openProject,
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

import { gatePath } from './areas'
import { drawWindow } from './harness'
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
  readonly gates: number[]
  readonly doors: { which: number; words: readonly string[] }[]
  /** What the next gate answers: the first run drifts, and a door closes it. */
  clean: boolean
}

function engine(): Transport {
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
          return said({ version: '0.2.400', source: null, commands: [] })
        default:
          return Promise.reject(new EngineCallFailed('unspawnable', 'no', 1))
      }
    },
  }
}

async function at(path: string, held: readonly ProjectGate[] = []): Promise<Wired> {
  const transport = engine()
  const opened = openedFrom(await openProject(ROOT, [['python', 'launch.py']], () => transport))
  const wired: Wired = { gates: [], doors: [], clean: false }

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
        wired.gates.push(wired.gates.length)
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
      fill(BASE['gate.problems'], { problems: 1, lines: 12, sections: 4 }),
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
    const door = within(finding).getByTestId('door')
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
    const door = within(finding).getByTestId('door')
    fireEvent.change(within(door).getByLabelText(BASE['door.blank']), {
      target: { value: 'A design' },
    })
    fireEvent.click(within(door).getByRole('button', { name: BASE['door.take'] }))

    expect(
      await screen.findByText(fill(BASE['gate.clean'], { lines: 12, sections: 4 })),
    ).toBeTruthy()
    expect(screen.queryAllByTestId('finding')).toHaveLength(0)
    expect(wired.gates).toHaveLength(2)
  })

  it('is offered from the project surface, once the project opened', async () => {
    await at(`/project/${encodeURIComponent(ROOT)}`)

    const offered = await screen.findByRole('link', { name: BASE['gate.run'] })
    expect(offered.getAttribute('href')).toBe(gatePath(ROOT))
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

  it('opens on the verdict on record, running nothing, where the files have not moved', async () => {
    const wired = await at(gatePath(ROOT), [verdict()])

    expect((await screen.findByTestId('held')).textContent).toBe(
      fill(BASE['gate.held.drifted'], { problems: 3 }),
    )
    expect(wired.gates).toEqual([])
  })

  it('says when it last ran, in the language the window speaks', async () => {
    await at(gatePath(ROOT), [verdict()])

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
    const wired = await at(gatePath(ROOT), [verdict()])

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
