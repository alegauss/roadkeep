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
import { afterEach, describe, expect, it, vi } from 'vitest'

import { projectPath, taskPath } from './areas'
import { drawWindow } from './harness'
import { stubBridge } from './stub-bridge'

/**
 * RG150: one line, as brief joins it, drawn through the whole window at its route.
 *
 * The far side answers by verb, the way the project test builds one. What is held is that
 * the screen is the one brief — the design as the file stores it, readiness and each dep in
 * the engine's words, the marker beside the claim — and that a paused line opens too.
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

/** The design as the file stores it: its own wrapping, and markup that stays literal. */
const BODY =
  'The detail is one read,\nwrapped where the file wraps it.\n\n**Kept** literal, and [[AL9]] too.'

/** One brief, whole, for the line that opens ready with a design written. */
const DESIGNED = {
  id: 'AL1',
  status: '📋',
  block: 'A',
  shipped: false,
  rendered: '- 📋 **AL1** (deps: AL0 ✅) **the first line is ready** — Nothing holds it. → §AL1',
  symptom: 'the first line is ready to start',
  why: 'Nothing holds it back.',
  deps: ['AL0 ✅', 'roadkeep RK1'],
  requires: ['signing-cert'],
  ref: 'AL1',
  section: {
    anchor: 'AL1',
    title: 'One read and nothing beside it',
    level: 3,
    file: 'docs/IMPROVEMENTS.md',
    first: 40,
    last: 48,
    words: 120,
    own_words: 120,
    body: BODY,
  },
  section_absence: '',
  readiness: 'ready',
  picked: null,
  deps_resolved: [
    { dep: 'AL0', kind: 'task', status: 'shipped', detail: 'in the changelog' },
    { dep: 'roadkeep RK1', kind: 'outside', status: 'unresolvable', detail: 'another backlog' },
  ],
  chains: [{ path: ['AL1', 'AL0'], end: 'shipped', detail: 'shipped, in the ledger' }],
  unblocks: { count: 2, of: 7, transitive: ['AL2'], transitive_elided: 1 },
  non_goals: ['No Markdown parsed in this app', 'No write to a governed file', 'No store'],
  non_goals_elided: 3,
  quotes: ['No write to a governed file'],
  done_when: ['A task opens with everything starting it costs'],
  done_when_elided: 0,
  held: [],
  landed: [],
  budget: {
    id: 'AL1',
    status: '📋',
    deps: [],
    open_line: true,
    line_max: 320,
    structure: 70,
    ref: 'AL1',
    ref_assumed: false,
    prose: 200,
    fields: [],
    section: {
      anchor: 'AL1',
      role: 'improvements',
      written: true,
      unit: 'words',
      limit: 250,
      allowed: 250,
      aim: 233,
      taken: 120,
      left: 130,
      room: 113,
      subtree: 120,
      over: 0,
    },
  },
  claimed: null,
}

/** A started line nobody holds, and one with no section at all. */
const STARTED = {
  ...DESIGNED,
  id: 'AL3',
  status: '🛠',
  block: 'B',
  symptom: 'the third was started and nobody holds it',
  section: null,
  section_absence: 'no section under AL3 in docs/IMPROVEMENTS.md',
  quotes: [],
  budget: null,
}

/** What `brief` refuses a paused line with: every typed field empty, the answer in `said`. */
const PAUSED_REFUSAL = {
  refused: [],
  beside: '',
  about: '',
  said: 'AL5 is paused in docs/DEFERRED.md; `list --stale` prints why and `resume AL5` brings it back',
}

function listed(tasks: readonly Record<string, unknown>[]): string {
  return JSON.stringify({ file: 'docs/ROADMAP.md', total: tasks.length, uncounted: [], tasks })
}

const OPEN_LINE = {
  id: 'AL1',
  status: '📋',
  block: 'A',
  symptom: 'the first line is ready to start',
  why: 'Nothing holds it back.',
  deps: [],
  ref: 'AL1',
  line: 7,
  length: 90,
}

const PAUSED_LINE = {
  id: 'AL5',
  status: '⏸',
  block: 'B',
  symptom: 'this was set aside',
  why: 'set aside (waiting): later.',
  deps: ['AL1'],
  ref: null,
  line: 3,
  length: 80,
}

function answer(argv: readonly string[]): { stdout: string; code: number } | undefined {
  const verb = argv[2] ?? ''
  const id = argv[3] ?? ''
  const said = (value: unknown, code = 0) => ({ stdout: JSON.stringify(value), code })
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
        keys: [
          key('files', 'roadmap', '"docs/ROADMAP.md"'),
          key('markers', 'open', '["📋", "💭", "🛠"]'),
          key('markers', 'designed', '"📋"'),
          key('markers', 'working', null, '"🛠"'),
        ],
      })
    case 'commands':
      return said({ version: '0.2.400', source: null, commands: [] })
    case 'stats':
      return said({ file: 'docs/ROADMAP.md', total: 1, uncounted: 0, markers: {}, blocks: [] })
    case 'block':
      return said({ file: 'docs/ROADMAP.md', blocks: [] })
    case 'deps':
      return said({ id, readiness: 'ready', blockers: [] })
    case 'list': {
      if (argv.includes('--stale')) return { stdout: listed([PAUSED_LINE]), code: 0 }
      if (argv.includes('--role')) return { stdout: listed([]), code: 0 }
      return { stdout: listed([OPEN_LINE]), code: 0 }
    }
    case 'brief':
      if (id === 'AL1') return said(DESIGNED)
      if (id === 'AL3') return said(STARTED)
      return said(PAUSED_REFUSAL, 1)
    default:
      return undefined
  }
}

function engine(): Transport {
  return {
    run(request) {
      const said = answer(request.argv)
      if (said === undefined) return Promise.reject(new EngineCallFailed('unspawnable', 'no', 1))
      return Promise.resolve({ code: said.code, stdout: said.stdout, stderr: '', durationMs: 1 })
    },
  }
}

const CATALOGUE: ProjectCatalogue = { version: 1, roots: [], projects: [] }

async function at(path: string): Promise<void> {
  const transport = engine()
  const opened = openedFrom(await openProject(ROOT, [['python', 'launch.py']], () => transport))
  Object.defineProperty(window, 'roadkeep', {
    value: stubBridge({
      projects: () => Promise.resolve(CATALOGUE),
      open: () => Promise.resolve(opened),
      run: (root, request) => bridgedRun(() => transport.run({ ...request, root })),
      subscribe: () => () => undefined,
      // The line's own sessions (RG153): none here, which is what a window holds until one
      // is handed over.
      sessions: () => Promise.resolve([]),
    }),
    configurable: true,
  })
  drawWindow({ at: path })
}

afterEach(() => {
  Reflect.deleteProperty(window, 'roadkeep')
  Reflect.deleteProperty(navigator, 'clipboard')
})

describe('RG150: a task opens from its row', () => {
  it('leads from Open on the project surface to the line at its own route', async () => {
    await at(projectPath(ROOT))

    const open = await screen.findByRole('link', {
      name: fill(BASE['project.line.open.named'], { id: 'AL1' }),
    })
    expect(open.getAttribute('href')).toBe(taskPath(ROOT, 'AL1'))
    fireEvent.click(open)

    expect(await screen.findByRole('heading', { name: 'AL1' })).toBeTruthy()
    expect(await screen.findByText('One read and nothing beside it')).toBeTruthy()
  })
})

describe('RG150: the line, as brief joins it', () => {
  it('draws the line: its block, what its marker is for, its symptom and why', async () => {
    await at(taskPath(ROOT, 'AL1'))

    expect(await screen.findByText('the first line is ready to start')).toBeTruthy()
    expect(screen.getByText('Nothing holds it back.')).toBeTruthy()
    expect(screen.getByText(fill(BASE['task.block'], { block: 'A' }))).toBeTruthy()
    // What the marker is for is the config's own key name, not a word this app keeps.
    expect(screen.getByText('designed')).toBeTruthy()
  })

  it('draws the design exactly as the file stores it, wrapping and markup kept', async () => {
    await at(taskPath(ROOT, 'AL1'))

    const design = await screen.findByTestId('design')
    expect(design.textContent).toBe(BODY)
    expect(
      screen.getByText(
        fill(BASE['task.design.where'], { anchor: 'AL1', where: 'docs/IMPROVEMENTS.md:40-48' }),
      ),
    ).toBeTruthy()
    expect(
      screen.getByText(fill(BASE['task.design.budget'], { taken: 120, limit: 250, unit: 'words' })),
    ).toBeTruthy()
  })

  it('draws readiness and each dep in the engine words, with the route and what a ship frees', async () => {
    await at(taskPath(ROOT, 'AL1'))

    expect(
      await screen.findByText(fill(BASE['task.readiness'], { readiness: 'ready' })),
    ).toBeTruthy()
    expect(screen.getByText('unresolvable')).toBeTruthy()
    expect(screen.getByText('roadkeep RK1')).toBeTruthy()
    expect(screen.getByText(fill(BASE['task.requires'], { what: 'signing-cert' }))).toBeTruthy()
    expect(within(screen.getByTestId('chain')).getByText('AL1 → AL0')).toBeTruthy()
    expect(screen.getByText(fill(BASE['task.unblocks'], { count: 2, of: 7 }))).toBeTruthy()
  })

  it('says what binds the line, the non-goals its design quotes first', async () => {
    await at(taskPath(ROOT, 'AL1'))

    expect(await screen.findByText('A task opens with everything starting it costs')).toBeTruthy()
    const quoted = within(screen.getByTestId('quoted'))
    expect(quoted.getByText('No write to a governed file')).toBeTruthy()
    const bounds = within(screen.getByTestId('bounds'))
    expect(bounds.queryByText('No write to a governed file')).toBeNull()
    expect(bounds.getByText('No Markdown parsed in this app')).toBeTruthy()
    // The brief sampled the list, and the screen says so rather than drawing three as all.
    expect(bounds.getByText(fill(BASE['task.bounds.elided'], { count: 3 }))).toBeTruthy()
  })

  it('hands on the line and its design when the brief is copied', async () => {
    const writeText = vi.fn(() => Promise.resolve())
    Object.defineProperty(navigator, 'clipboard', { value: { writeText }, configurable: true })
    await at(taskPath(ROOT, 'AL1'))

    fireEvent.click(await screen.findByRole('button', { name: BASE['task.copy'] }))

    expect(await screen.findByText(BASE['task.copied'])).toBeTruthy()
    expect(writeText).toHaveBeenCalledWith(`${DESIGNED.rendered}\n\n${BODY}`)
  })

  it('says the brief was not copied where there is no clipboard, rather than throwing', async () => {
    await at(taskPath(ROOT, 'AL1'))

    fireEvent.click(await screen.findByRole('button', { name: BASE['task.copy'] }))

    await waitFor(() => {
      expect(screen.getByTestId('copied').textContent).not.toBe('')
    })
    expect(screen.queryByText(BASE['task.copied'])).toBeNull()
  })
})

describe('RG150: the marker and the claim, and a line with no design', () => {
  it('says a started line nobody holds disagrees with the registry, rather than choosing', async () => {
    await at(taskPath(ROOT, 'AL3'))

    expect(await screen.findByText(BASE['task.underway.started'])).toBeTruthy()
    expect(screen.getByText(BASE['task.underway.disagree'])).toBeTruthy()
  })

  it('says no design is written, with the engine sentence about it', async () => {
    await at(taskPath(ROOT, 'AL3'))

    expect(await screen.findByText(BASE['task.design.none'])).toBeTruthy()
    expect(screen.getByText('no section under AL3 in docs/IMPROVEMENTS.md')).toBeTruthy()
    expect(screen.queryByTestId('design')).toBeNull()
  })
})

describe('RG150: a paused line opens too (RG80)', () => {
  it('draws the store entry and the verb that brings it back', async () => {
    await at(taskPath(ROOT, 'AL5'))

    expect(await screen.findByText(BASE['task.paused'])).toBeTruthy()
    expect(screen.getByText('this was set aside')).toBeTruthy()
    expect(screen.getByText('set aside (waiting): later.')).toBeTruthy()
    expect(
      screen.getByText(fill(BASE['task.paused.back'], { verb: 'resume', id: 'AL5' })),
    ).toBeTruthy()
  })
})
