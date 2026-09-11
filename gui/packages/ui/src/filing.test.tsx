import {
  BASE,
  bridgedRun,
  EngineCallFailed,
  fill,
  openedFrom,
  openProject,
  type BridgedResult,
  type Transport,
} from '@rk/core'
import { fireEvent, screen, waitFor, within } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'

import { filePath } from './areas'
import { drawWindow } from './harness'
import { stubBridge } from './stub-bridge'

/**
 * RG151: filing a line, drawn through the whole window at its route.
 *
 * The engine answers by verb the way the other surface tests build one. What is held is that
 * every number beside a field is the one `budget` printed, that the command shown is the argv
 * that runs, and that a refusal lands on the field it names and offers its doors — taken by
 * name through the bridge, never as an argv this screen built.
 */

const ROOT = 'D:\\code\\alpha'

const key = (table: string, name: string, set: string | null, fallback: string | null = null) => ({
  table,
  key: name,
  address: `${table}.${name}`,
  declared: set !== null,
  set,
  default: fallback,
})

/** What `budget` answers for a draft with no id: the two fields and the section. */
const BUDGET = {
  id: 'AL9',
  status: '📋',
  deps: [],
  open_line: true,
  line_max: 320,
  structure: 41,
  ref: 'RG9',
  ref_assumed: true,
  prose: 279,
  fields: [
    {
      field: 'symptom',
      limit: 120,
      allowed: 120,
      aim: 18,
      taken: 20,
      left: 100,
      over: 0,
      room: 18,
      unit: 'utf-16-code-units',
      bound_by_line: false,
    },
    {
      field: 'why',
      limit: 200,
      allowed: 159,
      aim: 24,
      taken: 0,
      left: 159,
      over: 0,
      room: 24,
      unit: 'utf-16-code-units',
      bound_by_line: true,
    },
  ],
  section: {
    anchor: 'RG9',
    role: 'improvements',
    written: false,
    unit: 'words',
    limit: 250,
    taken: 3,
    over: 0,
  },
}

/** What `add` refuses a too-long symptom with, and the door it offers instead. */
const REFUSAL = {
  refused: [
    {
      code: 'symptom.too-long',
      field: 'symptom',
      bound: '120',
      message: '148 characters, limit is 120',
    },
  ],
  beside: '',
  about: '',
  said: 'roadkeep: refused, nothing written: symptom: 148 characters, limit is 120',
  doors: [
    {
      argv: ['budget', '--block', 'A', '--symptom', '…'],
      what: 'measures the same draft against the same limit and writes nothing',
      complete: false,
      writes: false,
    },
  ],
}

const ADDED = {
  id: 'AL9',
  ref: 'AL9',
  file: 'docs/ROADMAP.md',
  line: 12,
  rendered: '- 📋 **AL9** **a line filed from the window** — It is. → §AL9',
  length: 120,
  section: null,
  near: [],
  near_recorded: 0,
}

interface Wired {
  readonly ran: string[][]
  readonly doors: { which: number; words: readonly string[] }[]
  refuses: boolean
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
        case 'budget':
          return said(BUDGET)
        case 'non-goal':
          return said({
            file: 'docs/ROADMAP.md',
            governed: true,
            non_goals: ['No Markdown parsed in this app'],
            non_goals_elided: 0,
            non_goals_quoted: {},
            non_goals_why: {
              'No Markdown parsed in this app': 'A reader that parses is a second one.',
            },
          })
        default:
          return Promise.reject(new EngineCallFailed('unspawnable', 'no', 1))
      }
    },
  }
}

async function at(path: string): Promise<Wired> {
  const transport = engine()
  const opened = openedFrom(await openProject(ROOT, [['python', 'launch.py']], () => transport))
  const wired: Wired = { ran: [], doors: [], refuses: false }

  Object.defineProperty(window, 'roadkeep', {
    value: stubBridge({
      projects: () => Promise.resolve({ version: 1, roots: [], projects: [] }),
      open: () => Promise.resolve(opened),
      subscribe: () => () => undefined,
      sessions: () => Promise.resolve([]),
      run: (root, request): Promise<BridgedResult> => {
        wired.ran.push([...request.argv])
        // A write is what this screen sends; everything else is a read the engine answers.
        if (!request.argv.includes('add')) {
          return bridgedRun(() => transport.run({ ...request, root }))
        }
        const answer = wired.refuses ? REFUSAL : ADDED
        return Promise.resolve({
          kind: 'ran',
          result: {
            code: wired.refuses ? 1 : 0,
            stdout: JSON.stringify(answer),
            stderr: '',
            durationMs: 1,
          },
          ...(wired.refuses ? { offered: 'token-1' } : {}),
        })
      },
      door: (_root, _offered, which, words) => {
        wired.doors.push({ which, words })
        return Promise.resolve({
          kind: 'ran',
          result: { code: 0, stdout: JSON.stringify(ADDED), stderr: '', durationMs: 1 },
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

/** Type into the field its label names. */
function typeIn(label: string, text: string): void {
  const field = screen.getAllByTestId('field').find((one) => one.textContent.startsWith(label))
  if (field === undefined) throw new Error(`no field labelled ${label}`)
  const box = field.querySelector('textarea, input')
  if (box === null) throw new Error(`${label} has nothing to type in`)
  fireEvent.change(box, { target: { value: text } })
}

describe('RG151: the form, priced by the engine', () => {
  it('draws each counter in the numbers budget printed, and what the line costs in structure', async () => {
    await at(filePath(ROOT))
    typeIn(BASE['filing.symptom'], 'a line filed from the window')

    expect(
      await screen.findByText(
        fill(BASE['filing.counter.aim'], { left: 100, allowed: 120, room: 18 }),
      ),
    ).toBeTruthy()
    // The why's allowance is the rendered line's, and the counter says so.
    expect(
      screen.getByText(
        `${fill(BASE['filing.counter.aim'], { left: 159, allowed: 159, room: 24 })} · ${BASE['filing.counter.line']}`,
      ),
    ).toBeTruthy()
    expect(
      screen.getByText(fill(BASE['filing.structure'], { structure: 41, max: 320, prose: 279 })),
    ).toBeTruthy()
  })

  it('names the id this would be, which is the one budget answered and not a count', async () => {
    await at(filePath(ROOT))

    expect((await screen.findByTestId('next-id')).textContent).toBe(
      fill(BASE['filing.id'], { id: 'AL9' }),
    )
  })

  it('names what binds a line here, with the reason each lead carries', async () => {
    await at(filePath(ROOT))

    expect(await screen.findByText('No Markdown parsed in this app')).toBeTruthy()
    expect(screen.getByText('A reader that parses is a second one.')).toBeTruthy()
  })

  it('shows the command before it runs, and runs that argv', async () => {
    const wired = await at(filePath(ROOT))
    typeIn(BASE['filing.symptom'], 'a line filed from the window')
    typeIn(BASE['filing.why'], 'It is.')

    const command = await screen.findByTestId('command')
    expect(command.textContent).toContain('add')
    expect(command.textContent).toContain('--symptom')

    fireEvent.click(screen.getByRole('button', { name: BASE['filing.save'] }))

    await waitFor(() => {
      expect(wired.ran.some((argv) => argv.includes('add'))).toBe(true)
    })
    const written = wired.ran.find((argv) => argv.includes('add')) ?? []
    expect(written).toContain('a line filed from the window')
    expect(written).toContain('It is.')
    expect(written.at(-1)).toBe('--json')
  })

  it('follows the line it wrote, which is what makes filing one act', async () => {
    await at(filePath(ROOT))
    typeIn(BASE['filing.symptom'], 'a line filed from the window')
    fireEvent.click(screen.getByRole('button', { name: BASE['filing.save'] }))

    // The task screen for the id the write answered with, which no other screen heads with.
    expect(await screen.findByRole('heading', { name: 'AL9' })).toBeTruthy()
    expect(screen.queryByTestId('command')).toBeNull()
  })
})

describe('RG151: what a refusal answers with', () => {
  it('says the engine sentence and marks the field it named', async () => {
    const wired = await at(filePath(ROOT))
    wired.refuses = true
    typeIn(BASE['filing.symptom'], 'a symptom past the limit')

    fireEvent.click(screen.getByRole('button', { name: BASE['filing.save'] }))

    const refusal = await screen.findByTestId('refusal')
    expect(
      within(refusal).getByText(fill(BASE['filing.refused'], { said: REFUSAL.said })),
    ).toBeTruthy()
    // On the field, never in a toast.
    expect(screen.getAllByTestId('refused-field').length).toBeGreaterThan(0)
  })

  it('offers the doors it carried, and takes one by name with the words it asked for', async () => {
    const wired = await at(filePath(ROOT))
    wired.refuses = true
    typeIn(BASE['filing.symptom'], 'a symptom past the limit')
    fireEvent.click(screen.getByRole('button', { name: BASE['filing.save'] }))

    const door = await screen.findByTestId('door')
    // The engine's own argv, and a blank of its own to fill.
    expect(within(door).getByText(/budget --block A --symptom/)).toBeTruthy()
    const take = within(door).getByRole('button', { name: BASE['door.take'] })
    expect(take.hasAttribute('disabled')).toBe(true)

    fireEvent.change(within(door).getByLabelText(BASE['door.blank']), {
      target: { value: 'a shorter symptom' },
    })
    fireEvent.click(within(door).getByRole('button', { name: BASE['door.take'] }))

    await waitFor(() => {
      expect(wired.doors).toEqual([{ which: 0, words: ['a shorter symptom'] }])
    })
  })
})

describe('RG151: reaching the form', () => {
  it('is offered from the project surface, once the project opened', async () => {
    await at(`/project/${encodeURIComponent(ROOT)}`)

    const offered = await screen.findByRole('link', { name: BASE['filing.title'] })
    expect(offered.getAttribute('href')).toBe(filePath(ROOT))
  })

  it('goes back to the project it files into', async () => {
    await at(filePath(ROOT))

    expect((await screen.findByRole('link', { name: 'alpha' })).getAttribute('href')).toBe(
      `/project/${encodeURIComponent(ROOT)}`,
    )
  })
})
