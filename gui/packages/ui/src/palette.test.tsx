import { BASE, fill, openedFrom, openProject, type Transport } from '@rk/core'
import { act, fireEvent, screen, waitFor, within } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'

import { drawWindow } from './harness'
import { stubBridge } from './stub-bridge'

/**
 * RG147: lines in the palette.
 *
 * The header's trigger says "find a line in every backlog" and the palette listed only
 * surfaces. RG20 shipped `search` over every open project and nothing put a line into the
 * list a person types at, because the package's palette took nav items and matched them
 * itself — so lines would have been matched in the renderer, which block C's first criterion
 * refuses. VDS123 gave it a group the product fills per query.
 *
 * What is held here: the group is `search`'s answer in `search`'s order, a line the verb did
 * not return is not offered, and how much of the backlog the answer covers is on screen —
 * an empty answer over eleven of seventeen backlogs is exactly when somebody concludes a
 * line does not exist.
 */

const ONE = '/work/alpha'
const TWO = '/work/beta'

function lineOf(id: string, symptom: string) {
  return {
    id,
    status: '📋',
    block: 'A',
    symptom,
    why: 'Something has to answer it.',
    deps: [],
    ref: id,
    line: 7,
    length: 90,
    readiness: 'ready',
  }
}

const LISTED: Readonly<Record<string, ReturnType<typeof lineOf>[]>> = {
  [ONE]: [lineOf('AL1', 'the portfolio forgets a project between launches')],
  [TWO]: [lineOf('BE9', 'a gate finding names no file')],
}

/** What each verb answers, per root. Only the three an open and a listing need. */
const ANSWERS: Readonly<Record<string, (root: string) => string | undefined>> = {
  engines: () =>
    JSON.stringify({
      writing: { version: '0.2.466', home: '/e', revision: 'abc1234', on_disk: '0.2.466' },
      invoke: 'roadkeep',
      declaration: '',
      verdict: 'one copy',
      agree: true,
      readable: true,
      split: false,
      swapped: false,
    }),
  config: () =>
    JSON.stringify({
      version: '0.2.466',
      source: 'roadkeep.toml',
      governed: true,
      keys: [{ table: 'files', key: 'roadmap', declared: true, set: 'docs/ROADMAP.md' }],
    }),
  commands: () => JSON.stringify({ version: '0.2.466', source: null, commands: [] }),
  list: (root) =>
    JSON.stringify({
      file: 'docs/ROADMAP.md',
      total: LISTED[root]?.length ?? 0,
      uncounted: [],
      tasks: LISTED[root] ?? [],
    }),
}

/** Which roots answered a `list`, so a test can hold that nothing was read at launch. */
let listed: string[] = []

/** What a `brief` was asked about, which is how the navigation is read back. */
let briefed: string[] = []

/** A root whose `list` never answers, so the palette's coverage is observable. */
let pendingRoot = ''

async function wired(): Promise<void> {
  listed = []
  const roots = [ONE, TWO]
  const projects = roots.map((path) => ({
    path,
    aliases: [],
    commonDir: null,
    root: '/code',
    confirmed: '',
    presence: 'present' as const,
  }))

  /** One machine per root, so a `list` answers that root's own lines. */
  const machine = (root: string): Transport => ({
    run(request) {
      const verb = request.argv[2] ?? ''
      if (verb === 'list') {
        listed.push(root)
        if (root === pendingRoot) return new Promise(() => undefined)
      }
      if (verb === 'brief') briefed.push(`${root}:${request.argv[3] ?? ''}`)
      const said = ANSWERS[verb]?.(root)
      if (said === undefined) {
        return Promise.reject(new Error(`no ${verb}`))
      }
      return Promise.resolve({ code: 0, stdout: said, stderr: '', durationMs: 1 })
    },
  })

  const opened = new Map(
    await Promise.all(
      roots.map(
        async (root) =>
          [root, openedFrom(await openProject(root, [['roadkeep']], () => machine(root)))] as const,
      ),
    ),
  )

  Object.defineProperty(window, 'roadkeep', {
    value: stubBridge({
      projects: () => Promise.resolve({ version: 1, roots: [], projects }),
      open: (root) => Promise.resolve(opened.get(root) ?? opened.values().next().value!),
      run: (root, request) => {
        const verb = request.argv[2] ?? ''
        if (verb === 'list') {
          listed.push(root)
          if (root === pendingRoot) return new Promise(() => undefined)
        }
        if (verb === 'brief') briefed.push(`${root}:${request.argv[3] ?? ''}`)
        const said = ANSWERS[verb]?.(root)
        return Promise.resolve(
          said === undefined
            ? {
                kind: 'failed' as const,
                reason: 'unspawnable' as const,
                message: `no ${verb}`,
                code: '' as const,
                fields: {},
                durationMs: 1,
              }
            : {
                kind: 'ran' as const,
                result: { code: 0, stdout: said, stderr: '', durationMs: 1 },
              },
        )
      },
    }),
    configurable: true,
  })
}

async function openPalette() {
  await act(async () => {
    fireEvent.click(screen.getByTestId('palette-trigger'))
    await Promise.resolve()
  })
  return screen.findByRole('dialog')
}

function type(dialog: HTMLElement, query: string) {
  const box = within(dialog).getByRole('combobox')
  fireEvent.change(box, { target: { value: query } })
}

afterEach(() => {
  listed = []
  briefed = []
  pendingRoot = ''
})

describe('RG147: lines in the palette', () => {
  it('reads no backlog until the palette is opened', async () => {
    await wired()
    drawWindow()

    await waitFor(() => {
      expect(screen.getByTestId('palette-trigger')).toBeTruthy()
    })
    // A listing per project for a window nobody has typed into is the cold start RG17
    // exists to bound.
    expect(listed).toEqual([])
  })

  it('offers a line the search returned, from whichever backlog holds it', async () => {
    await wired()
    drawWindow()
    const dialog = await openPalette()

    await waitFor(() => {
      expect(listed.length).toBe(2)
    })
    type(dialog, 'gate finding')

    await waitFor(() => {
      expect(within(dialog).getByText(/BE9/)).toBeTruthy()
    })
    expect(within(dialog).queryByText(/AL1/)).toBeNull()
  })

  it('opens the task the reader chose, in that line’s own project', async () => {
    await wired()
    drawWindow()
    const dialog = await openPalette()
    await waitFor(() => {
      expect(listed.length).toBe(2)
    })
    type(dialog, 'gate finding')
    await waitFor(() => {
      expect(within(dialog).getByText(/BE9/)).toBeTruthy()
    })

    fireEvent.click(within(dialog).getByText(/BE9/))

    // The router here is a memory one, so what is held is where the window went: the task
    // screen asks `brief` for the line it was routed to, and it is asked of the project
    // that line came from and not of the one the palette was opened over.
    await waitFor(() => {
      expect(screen.queryByRole('dialog')).toBeNull()
    })
    await waitFor(() => {
      expect(briefed).toContain(`${TWO}:BE9`)
    })
    expect(briefed.some((one) => one.startsWith(ONE))).toBe(false)
  })

  it('offers nothing the search did not return, whatever the query looks like', async () => {
    await wired()
    drawWindow()
    const dialog = await openPalette()
    await waitFor(() => {
      expect(listed.length).toBe(2)
    })

    type(dialog, 'a phrase no line carries')

    await waitFor(() => {
      expect(within(dialog).queryByText(/AL1/)).toBeNull()
    })
    expect(within(dialog).queryByText(/BE9/)).toBeNull()
  })

  it('says how much of the backlog the answer covers while one is unread', async () => {
    // One project's listing never lands, which is the state the heading exists for: an
    // empty answer over half the backlogs is exactly when somebody wrongly concludes a
    // line does not exist.
    pendingRoot = TWO
    await wired()
    drawWindow()
    const dialog = await openPalette()

    await waitFor(() => {
      expect(
        within(dialog).getByText(fill(BASE['palette.lines.partial'], { searched: 1, total: 2 })),
      ).toBeTruthy()
    })
    expect(within(dialog).queryByText(BASE['palette.lines'])).toBeNull()
  })

  it('says it covers everything once every backlog has answered', async () => {
    await wired()
    drawWindow()
    const dialog = await openPalette()

    await waitFor(() => {
      expect(within(dialog).getByText(BASE['palette.lines'])).toBeTruthy()
    })
  })
})
