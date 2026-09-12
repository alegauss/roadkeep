import {
  DECLARES_NOTHING,
  BASE,
  bridgedRun,
  EngineCallFailed,
  fill,
  openedFrom,
  openProject,
  readBriefPayload,
  type HandedOver,
  type SessionRecord,
  type Topic,
  type TopicEvents,
  type Transport,
  BASE_LOCALE,
  timeIn,
  EVERY_SOURCE,
  type SessionOutcome,
  folderName,
} from '@rk/core'
import { act, fireEvent, screen, waitFor, within } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'

import { SESSIONS_ROUTE, sessionPath, taskPath } from './areas'
import i18next, { changeLanguage } from 'i18next'

import { drawWindow } from './harness'
import { startSpeaking } from './speaking'
import { stubBridge } from './stub-bridge'

/**
 * RG153: a line handed to a session, and the session beside it.
 *
 * The bridge is stubbed the way a window sees it — a handover that answers, a record of what
 * is running, and the session topic to hear it on — over the same engine the task test builds.
 * What is held is that the stream is drawn as acts off the raw lines, that a line heard after
 * the record lands in its place, and that what moved comes from a reread and not from the
 * session's own account.
 */

const ROOT = 'D:\\code\\alpha'
const KEY = 'session-1'

const key = (table: string, name: string, set: string | null, fallback: string | null = null) => ({
  table,
  key: name,
  address: `${table}.${name}`,
  declared: set !== null,
  set,
  default: fallback,
})

/** The brief the session was handed: the claiming read's answer, marker moved. */
const RAW = {
  id: 'AL1',
  status: '🛠',
  block: 'A',
  shipped: false,
  rendered: '- 🛠 **AL1** **a line ready to start** — It is. → §AL1',
  symptom: 'a line ready to start',
  why: 'It is.',
  deps: ['AL0 ✅'],
  requires: [],
  ref: 'AL1',
  section: {
    anchor: 'AL1',
    title: 'One read',
    level: 3,
    file: 'docs/IMPROVEMENTS.md',
    first: 1,
    last: 9,
    words: 120,
    own_words: 120,
    body: 'The design.',
  },
  section_absence: '',
  readiness: 'ready',
  deps_resolved: [{ dep: 'AL0', kind: 'task', status: 'shipped', detail: '' }],
  non_goals: ['No Markdown parsed in this app'],
  done_when: ['A session starts from a brief, not from a prompt somebody typed'],
  held: [],
  claimed: { taken: true, from: '📋', to: '🛠' },
}

/** The line as it reads now: shipped, which is what the files say and the stream does not. */
const SHIPPED = { ...RAW, status: '✅', shipped: true, section: null }

/** The record carries the payload as the bridge read it, so the fixture is read the same way. */
function handed() {
  const parsed = readBriefPayload(RAW, '')
  if (!parsed.ok) throw new Error(`the fixture does not match the shape: ${parsed.failure.path}`)
  return parsed.value
}

const RECORD: SessionRecord = {
  key: KEY,
  root: ROOT,
  id: 'AL1',
  handed: handed(),
  agent: { command: ['claude'], version: '2.1.263', said: '2.1.263 (Claude Code)' },
  lines: [JSON.stringify({ type: 'system', subtype: 'init', session_id: 'fake' })],
  outcome: null,
}

/** A call to the engine this project resolved, and a read of a file it governs. */
const USED = JSON.stringify({
  type: 'assistant',
  message: {
    content: [
      {
        type: 'tool_use',
        id: 't1',
        name: 'Bash',
        input: { command: 'roadkeep ship AL1 --why "it works"', description: 'ship it' },
      },
      { type: 'tool_use', id: 't2', name: 'Read', input: { file_path: 'docs/ROADMAP.md' } },
    ],
  },
})

const SAID = JSON.stringify({
  type: 'assistant',
  message: { content: [{ type: 'text', text: 'Working it now.' }] },
})

function engine(moved: { shipped: boolean }): Transport {
  return {
    run(request) {
      const verb = request.argv[2] ?? ''
      const id = request.argv[3] ?? ''
      const said = (value: unknown) =>
        Promise.resolve({ code: 0, stdout: JSON.stringify(value), stderr: '', durationMs: 1 })
      switch (verb) {
        case 'engines':
          return said({
            writing: { version: '0.2.400', home: '/e', revision: 'abc', on_disk: '0.2.400' },
            invoke: 'roadkeep',
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
              key('markers', 'open', '["📋", "🛠"]'),
              key('markers', 'working', null, '"🛠"'),
            ],
          })
        case 'commands':
          return said({ version: '0.2.400', source: null, commands: [] })
        case 'claims':
          return said({
            window: 60,
            registry: 'C:\\Temp\\roadkeep-alpha.state',
            held: 2,
            claims: [
              // This session's own line, which is not somebody else being on something.
              { id: 'AL1', state: 'held', where: 'open', age: 60, since: '1m', marker: '🛠' },
              { id: 'AL7', state: 'held', where: 'open', age: 900, since: '15m', marker: '🛠' },
              { id: 'AL8', state: 'expired', where: 'open', age: 9000, since: '2h', marker: '🛠' },
            ],
          })
        case 'brief':
          if (id === 'AL2') return said({ ...RAW, id, status: '📋', held: [HOLDER] })
          return said(moved.shipped ? SHIPPED : RAW)
        default:
          return Promise.reject(new EngineCallFailed('unspawnable', 'no', 1))
      }
    },
  }
}

const HOLDER = { by: 'another session', since: 'an hour ago', state: 'held', paths: [] }

/** What the disk says about the files this project governs, as main answers it. */
const CHANGED = '2026-09-11T10:00:00.000Z'
const FILES = [
  { role: 'roadmap', path: 'docs/ROADMAP.md', changed: CHANGED, present: true },
  { role: 'decisions', path: 'docs/DECISIONS.md', changed: '', present: false },
]

interface Listening {
  readonly topic: Topic
  readonly key: string
  readonly heard: (event: TopicEvents[Topic]) => void
}

interface Wired {
  readonly listeners: Listening[]
  readonly stopped: string[]
  readonly handedOver: string[]
  /** What `sessions` answers next, which main moves under a standing list (RG178). */
  holds: SessionRecord[]
}

async function at(
  path: string,
  over: {
    readonly sessions?: readonly SessionRecord[]
    readonly handOver?: HandedOver
    readonly shipped?: boolean
  } = {},
): Promise<Wired> {
  const moved = { shipped: over.shipped ?? false }
  const transport = engine(moved)
  const opened = openedFrom(await openProject(ROOT, [['roadkeep']], () => transport))
  const wired: Wired = { listeners: [], stopped: [], handedOver: [], holds: [] }
  // What this window holds, which a handover adds to — the state RG175 reads to decide
  // whether the line is offered again, and which a test can move under a standing list
  // the way main does (RG178).
  const held = [...(over.sessions ?? [])]
  wired.holds = held

  Object.defineProperty(window, 'roadkeep', {
    value: stubBridge({
      projects: () => Promise.resolve({ version: 1, roots: [], projects: [] }),
      open: () => Promise.resolve(opened),
      run: (root, request) => bridgedRun(() => transport.run({ ...request, root })),
      subscribe: (topic, one, heard) => {
        const listening = { topic, key: one, heard: heard as Listening['heard'] }
        wired.listeners.push(listening)
        return () => {
          wired.listeners.splice(wired.listeners.indexOf(listening), 1)
        }
      },
      sessions: () => Promise.resolve([...held]),
      governedAt: () => Promise.resolve(FILES),
      handOver: (_root, id) => {
        wired.handedOver.push(id)
        const answer = over.handOver ?? { kind: 'withheld' as const, reason: 'nothing asked' }
        if (answer.kind === 'started') held.push(answer.session)
        return Promise.resolve(answer)
      },
      stopSession: (one) => {
        wired.stopped.push(one)
        return Promise.resolve()
      },
    }),
    configurable: true,
  })
  drawWindow({ at: path })
  return wired
}

/** Say one event on a topic, as main would. */
function hear(wired: Wired, topic: Topic, event: TopicEvents[Topic]): void {
  act(() => {
    for (const one of wired.listeners.filter((listening) => listening.topic === topic)) {
      one.heard(event)
    }
  })
}

afterEach(() => {
  Reflect.deleteProperty(window, 'roadkeep')
})

describe('RG153: handing a line to Claude Code', () => {
  it('takes the line and opens the session it started', async () => {
    const started: HandedOver = { kind: 'started', session: RECORD }
    // No session yet, which is the state a line is offered from: the handover is what puts
    // one there, and the far side holds it from that moment (RG175).
    const wired = await at(taskPath(ROOT, 'AL1'), { handOver: started })

    fireEvent.click(await screen.findByRole('button', { name: BASE['task.handOver'] }))

    expect(wired.handedOver).toEqual(['AL1'])
    // The session's own screen, which leads back to the line it was handed.
    expect(await screen.findByText(BASE['session.handed'])).toBeTruthy()
    expect(screen.getByRole('link', { name: 'AL1' }).getAttribute('href')).toBe(
      taskPath(ROOT, 'AL1'),
    )
  })

  it('names the holder of a held line and offers no session', async () => {
    // Block F's third criterion, held on the screen a person would click from.
    await at(taskPath(ROOT, 'AL2'))

    expect(
      await screen.findByText(
        fill(BASE['task.held.named'], { by: 'another session', since: 'an hour ago' }),
      ),
    ).toBeTruthy()
    expect(screen.queryByRole('button', { name: BASE['task.handOver'] })).toBeNull()
  })

  it('says why the line was not taken, in this app words for what came back', async () => {
    const wired = await at(taskPath(ROOT, 'AL1'), {
      handOver: { kind: 'unavailable', tried: [['claude'], ['/home/a/.local/bin/claude']] },
    })

    fireEvent.click(await screen.findByRole('button', { name: BASE['task.handOver'] }))

    expect(
      await screen.findByText(
        fill(BASE['task.handOver.unavailable'], {
          tried: 'claude, /home/a/.local/bin/claude',
        }),
      ),
    ).toBeTruthy()
    expect(wired.handedOver).toEqual(['AL1'])
  })

  it('leads back to a session this window already started for the line', async () => {
    await at(taskPath(ROOT, 'AL1'), { sessions: [RECORD] })

    const open = await screen.findByRole('link', { name: BASE['task.session.open'] })
    expect(open.getAttribute('href')).toBe(sessionPath(ROOT, 'AL1', KEY))
  })
})

describe('RG153: the session beside its task', () => {
  it('draws what was handed over, counted off the brief it was started from', async () => {
    await at(sessionPath(ROOT, 'AL1', KEY), { sessions: [RECORD] })

    expect(
      await screen.findByText(fill(BASE['session.claim'], { from: '📋', to: '🛠' })),
    ).toBeTruthy()
    expect(screen.getByText(fill(BASE['session.handed.design'], { words: 120 }))).toBeTruthy()
    expect(screen.getByText(fill(BASE['session.handed.deps'], { count: 1 }))).toBeTruthy()
    expect(screen.getByText(fill(BASE['session.handed.criteria'], { count: 1 }))).toBeTruthy()
    expect(
      screen.getByText(
        fill(BASE['session.handed.agent'], { command: 'claude', version: '2.1.263' }),
      ),
    ).toBeTruthy()
  })

  it('draws the stream as acts, a roadkeep call marked and a governed file named', async () => {
    const wired = await at(sessionPath(ROOT, 'AL1', KEY), { sessions: [RECORD] })
    await screen.findByText(BASE['session.handed'])

    hear(wired, 'session', { session: KEY, index: 1, line: USED })

    const call = (await screen.findByText('Bash')).closest('li')
    if (call === null) throw new Error('no act')
    expect(within(call).getByText(BASE['session.act.roadkeep'])).toBeTruthy()
    // The raw line is one disclosure away from the act it was read into.
    expect(within(call).getByText(BASE['session.act.raw'])).toBeTruthy()

    const read = screen.getByText('Read').closest('li')
    if (read === null) throw new Error('no act')
    expect(
      within(read).getByText(fill(BASE['session.act.governed'], { files: 'docs/ROADMAP.md' })),
    ).toBeTruthy()
    expect(within(read).queryByText(BASE['session.act.roadkeep'])).toBeNull()
  })

  it('puts a line heard after the record in its own place in the stream', async () => {
    const wired = await at(sessionPath(ROOT, 'AL1', KEY), { sessions: [RECORD] })
    await screen.findByText(BASE['session.handed'])

    hear(wired, 'session', { session: KEY, index: 2, line: USED })
    hear(wired, 'session', { session: KEY, index: 1, line: SAID })

    // The record's line, then what was heard, each in its place: the tool line carries two.
    await waitFor(() => {
      expect(screen.getAllByTestId('act').map((one) => one.dataset['kind'])).toEqual([
        'note',
        'said',
        'used',
        'used',
      ])
    })
  })

  it('says what the files moved, which is not what the session said it did', async () => {
    // The session's stream says it shipped; this column is the reread that settles it.
    await at(sessionPath(ROOT, 'AL1', KEY), { sessions: [RECORD], shipped: true })

    const moved = within(await screen.findByTestId('moved'))
    expect(
      moved.getByText(fill(BASE['session.change.marker'], { from: '🛠', to: '✅' })),
    ).toBeTruthy()
    expect(moved.getByText(BASE['session.change.shipped'])).toBeTruthy()
    expect(moved.getByText(BASE['session.change.design.deleted'])).toBeTruthy()
  })

  it('says nothing moved while the line reads as it was handed over', async () => {
    await at(sessionPath(ROOT, 'AL1', KEY), { sessions: [RECORD] })

    expect(await screen.findByText(BASE['session.moved.none'])).toBeTruthy()
  })

  it('stops the session, and says how it ended when it does', async () => {
    const wired = await at(sessionPath(ROOT, 'AL1', KEY), { sessions: [RECORD] })

    fireEvent.click(await screen.findByRole('button', { name: BASE['session.stop'] }))
    expect(wired.stopped).toEqual([KEY])

    hear(wired, 'session', {
      session: KEY,
      outcome: { state: 'cancelled', sessionId: 'fake', code: null, said: '', result: '' },
    })

    expect(await screen.findByText(BASE['session.state.cancelled'])).toBeTruthy()
    expect(screen.queryByRole('button', { name: BASE['session.stop'] })).toBeNull()
  })

  it('names each governed file and when the disk last changed it', async () => {
    // The landing says which fields moved; this says which file the session actually wrote.
    await at(sessionPath(ROOT, 'AL1', KEY), { sessions: [RECORD] })

    // The same wait as the claims below: this column stands before the disk has answered.
    await screen.findByText('docs/ROADMAP.md')
    const files = within(screen.getByTestId('files'))
    // In the window's language and not the desktop's, which RG177 separated.
    expect(files.getByText(timeIn(CHANGED, BASE_LOCALE))).toBeTruthy()
    // A role nothing has written yet is a state, drawn rather than dropped.
    expect(files.getByText('docs/DECISIONS.md')).toBeTruthy()
    expect(files.getByText(BASE['session.file.never'])).toBeTruthy()
  })

  it('names a claim held elsewhere, and neither its own line nor a lapsed one', async () => {
    await at(sessionPath(ROOT, 'AL1', KEY), { sessions: [RECORD] })

    // The panel draws before the registry answers, so the wait is for the entry and not for
    // the section — the container is there from the first frame, saying nothing is claimed.
    await screen.findByText('AL7')
    const elsewhere = within(screen.getByTestId('elsewhere'))
    expect(
      elsewhere.getByText(fill(BASE['session.claim.since'], { state: 'held', since: '15m' })),
    ).toBeTruthy()
    // The session's own claim is not somebody else, and an expired one is not somebody at all.
    expect(elsewhere.queryByText('AL1')).toBeNull()
    expect(elsewhere.queryByText('AL8')).toBeNull()
  })

  it('says so where this window holds no session by that name', async () => {
    await at(sessionPath(ROOT, 'AL1', 'nobody'))

    expect(await screen.findByText(BASE['session.missing'])).toBeTruthy()
  })
})

describe('RG153: every session this window started', () => {
  it('lists what is running, each leading to its own screen', async () => {
    await at(SESSIONS_ROUTE, { sessions: [RECORD] })

    const row = await screen.findByTestId('session')
    expect(row.dataset['id']).toBe('AL1')
    expect(within(row).getByText('a line ready to start')).toBeTruthy()
    expect(
      within(row)
        .getByRole('link', { name: fill(BASE['sessions.open'], { id: 'AL1' }) })
        .getAttribute('href'),
    ).toBe(sessionPath(ROOT, 'AL1', KEY))
    // One line written and no outcome: running, in the same words its own screen uses.
    expect(within(row).getByText(BASE['session.state.running'])).toBeTruthy()
  })

  it('says nothing has been started, which is what a window holds until one is', async () => {
    await at(SESSIONS_ROUTE)

    expect(await screen.findByText(BASE['sessions.none'])).toBeTruthy()
    expect(screen.getByText(BASE['sessions.none.hint'])).toBeTruthy()
  })
})

describe('RG177: a time in the window’s language', () => {
  afterEach(async () => {
    if (i18next.isInitialized) await changeLanguage(BASE_LOCALE)
  })

  it('writes a file’s stamp in the language the window speaks, not the desktop’s', async () => {
    await startSpeaking('pt-BR')
    await at(sessionPath(ROOT, 'AL1', RECORD.key), { sessions: [RECORD] })

    const files = await screen.findByTestId('files')
    expect(within(files).getByText(timeIn(CHANGED, 'pt-BR'))).toBeTruthy()
  })

  it('writes the same instant differently once the window speaks another language', async () => {
    await startSpeaking(BASE_LOCALE)
    await at(sessionPath(ROOT, 'AL1', RECORD.key), { sessions: [RECORD] })

    const files = await screen.findByTestId('files')
    // The same stamp, and not the string the other language writes for it.
    expect(within(files).queryByText(timeIn(CHANGED, 'pt-BR'))).toBeNull()
    expect(within(files).getByText(timeIn(CHANGED, BASE_LOCALE))).toBeTruthy()
  })
})

describe('RG178: a list that hears what it lists', () => {
  it('takes one subscription that means every session, not one per row', async () => {
    const wired = await at(SESSIONS_ROUTE, { sessions: [RECORD] })

    await screen.findByTestId('session')
    const heard = wired.listeners.filter((one) => one.topic === 'session')
    expect(heard.map((one) => one.key)).toEqual([EVERY_SOURCE])
  })

  it('reads again when a session says something, so an ending stops reading as running', async () => {
    const wired = await at(SESSIONS_ROUTE, { sessions: [RECORD] })

    expect(
      within(await screen.findByTestId('session')).getByText(BASE['session.state.running']),
    ).toBeTruthy()

    // Main's own record moves, and then main says so on the topic.
    wired.holds[0] = {
      ...RECORD,
      outcome: { state: 'done', sessionId: KEY, code: 0, said: '', result: 'shipped' },
    }
    hear(wired, 'session', { session: KEY, outcome: wired.holds[0].outcome as SessionOutcome })

    await waitFor(() => {
      expect(
        within(screen.getByTestId('session')).getByText(BASE['session.state.done']),
      ).toBeTruthy()
    })
  })

  it('hears a session it never listed, since the key it listens to is all of them', async () => {
    const wired = await at(SESSIONS_ROUTE)

    expect(await screen.findByText(BASE['sessions.none'])).toBeTruthy()

    // Started from another screen: a key this list had never heard of when it asked.
    wired.holds.push(RECORD)
    hear(wired, 'session', { session: KEY, index: 0, line: '{}' })

    await waitFor(() => {
      expect(screen.getByTestId('session').dataset['id']).toBe('AL1')
    })
  })
})

describe('RG190: the screen a handover moves after it is gone', () => {
  it('leaves a reader who went back where they went, when the handover lands', async () => {
    let landing: ((handed: HandedOver) => void) | null = null
    const alpha = openedFrom(
      await openProject(ROOT, [['roadkeep']], () => engine({ shipped: false })),
    )
    Object.defineProperty(window, 'roadkeep', {
      value: stubBridge({
        projects: () =>
          Promise.resolve({
            version: 1,
            roots: [],
            projects: [
              {
                path: ROOT,
                aliases: [],
                commonDir: null,
                root: '/code',
                confirmed: '',
                presence: 'present' as const,
                branch: '',
                declared: DECLARES_NOTHING,
              },
            ],
          }),
        open: () => Promise.resolve(alpha),
        run: (root, request) =>
          bridgedRun(() => engine({ shipped: false }).run({ ...request, root })),
        sessions: () => Promise.resolve([]),
        governedAt: () => Promise.resolve(FILES),
        // Held open, so the press and the answer are two moments a test can stand between.
        handOver: () =>
          new Promise<HandedOver>((answer) => {
            landing = answer
          }),
      }),
      configurable: true,
    })
    drawWindow({ at: taskPath(ROOT, 'AL1') })

    fireEvent.click(await screen.findByRole('button', { name: BASE['task.handOver'] }))
    await waitFor(() => {
      expect(landing).not.toBeNull()
    })

    // Back to the project, which is the screen this window is on when the answer arrives.
    fireEvent.click(screen.getByRole('link', { name: folderName(ROOT) }))
    await screen.findByText(BASE['project.blocks'])

    await act(async () => {
      landing?.({ kind: 'started', session: RECORD })
      await Promise.resolve()
    })

    // Still where the reader put themselves: the session started and is on the list, and
    // nothing moved the window to it.
    expect(screen.queryByText(BASE['session.handed'])).toBeNull()
    expect(screen.getByText(BASE['project.blocks'])).toBeTruthy()
  })
})
