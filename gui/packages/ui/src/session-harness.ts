import {
  bridgedRun,
  EngineCallFailed,
  openedFrom,
  openProject,
  readBriefPayload,
  type EditedFile,
  type FileText,
  type HandedOver,
  type SessionRecord,
  type Topic,
  type TopicEvents,
  type Transport,
} from '@rk/core'
import { act } from '@testing-library/react'

import { drawWindow } from './harness'
import { stubBridge } from './stub-bridge'

/**
 * A window with one session in it, for the tests that draw the session surface (RG153, RG213).
 *
 * A test instrument and not shipped code, like `harness` and `stub-bridge`. It lived inside
 * `session.test.tsx` until RG213 moved the stream's layout tests into a real browser, and two
 * files building the same engine, record and bridge by hand is two fixtures that drift.
 */

export const ROOT = 'D:\\code\\alpha'
export const KEY = 'session-1'

export const key = (
  table: string,
  name: string,
  set: string | null,
  fallback: string | null = null,
) => ({
  table,
  key: name,
  address: `${table}.${name}`,
  declared: set !== null,
  set,
  default: fallback,
})

/** The brief the session was handed: the claiming read's answer, marker moved. */
export const RAW = {
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
export const SHIPPED = { ...RAW, status: '✅', shipped: true, section: null }

/** The record carries the payload as the bridge read it, so the fixture is read the same way. */
function handed() {
  const parsed = readBriefPayload(RAW, '')
  if (!parsed.ok) throw new Error(`the fixture does not match the shape: ${parsed.failure.path}`)
  return parsed.value
}

/** When the fixture session was spawned: what an edited file's time is read against (RG244). */
export const STARTED = '2026-09-11T09:00:00.000Z'

export const RECORD: SessionRecord = {
  key: KEY,
  root: ROOT,
  id: 'AL1',
  started: STARTED,
  handed: handed(),
  agent: { command: ['claude'], version: '2.1.263', said: '2.1.263 (Claude Code)' },
  lines: [JSON.stringify({ type: 'system', subtype: 'init', session_id: 'fake' })],
  outcome: null,
}

/** A call to the engine this project resolved, and a read of a file it governs. */
export const USED = JSON.stringify({
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

export const SAID = JSON.stringify({
  type: 'assistant',
  message: { content: [{ type: 'text', text: 'Working it now.' }] },
})

export function engine(moved: { shipped: boolean }): Transport {
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

export const HOLDER = { by: 'another session', since: 'an hour ago', state: 'held', paths: [] }

/** What the disk says about the files this project governs, as main answers it. */
export const CHANGED = '2026-09-11T10:00:00.000Z'
export const FILES = [
  { role: 'roadmap', path: 'docs/ROADMAP.md', changed: CHANGED, present: true },
  { role: 'decisions', path: 'docs/DECISIONS.md', changed: '', present: false },
]

export interface Listening {
  readonly topic: Topic
  readonly key: string
  readonly heard: (event: TopicEvents[Topic]) => void
}

export interface Wired {
  readonly listeners: Listening[]
  readonly stopped: string[]
  readonly handedOver: string[]
  /** Each `editedAt` ask, as the session's key and the paths it named (RG244). */
  readonly editedAsked: { readonly key: string; readonly paths: readonly string[] }[]
  /** Each `fileText` ask, as the session's key and the path (RG245). */
  readonly fileAsked: { readonly key: string; readonly path: string }[]
  /** What `fileText` answers next for a path, which a test moves between reads (RG245). */
  readonly texts: Map<string, FileText>
  /** What `sessions` answers next, which main moves under a standing list (RG178). */
  holds: SessionRecord[]
}

export async function at(
  path: string,
  over: {
    readonly sessions?: readonly SessionRecord[]
    readonly handOver?: HandedOver
    readonly shipped?: boolean
    /** What the disk says about the edited files, by the path a call spelled (RG244). */
    readonly edited?: readonly EditedFile[]
    /** What each file reads as, by the path a call spelled (RG245). */
    readonly texts?: readonly FileText[]
  } = {},
): Promise<Wired> {
  const moved = { shipped: over.shipped ?? false }
  const transport = engine(moved)
  const opened = openedFrom(await openProject(ROOT, [['roadkeep']], () => transport))
  const wired: Wired = {
    listeners: [],
    stopped: [],
    handedOver: [],
    editedAsked: [],
    fileAsked: [],
    texts: new Map((over.texts ?? []).map((text) => [text.path, text])),
    holds: [],
  }
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
      editedAt: (one, paths) => {
        wired.editedAsked.push({ key: one, paths })
        const known = over.edited ?? []
        return Promise.resolve(known.filter((file) => paths.includes(file.path)))
      },
      fileText: (one, spelled) => {
        wired.fileAsked.push({ key: one, path: spelled })
        return Promise.resolve(
          wired.texts.get(spelled) ?? {
            kind: 'refused',
            path: spelled,
            code: 'missing',
            fields: {},
          },
        )
      },
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
export function hear(wired: Wired, topic: Topic, event: TopicEvents[Topic]): void {
  act(() => {
    for (const one of wired.listeners.filter((listening) => listening.topic === topic)) {
      one.heard(event)
    }
  })
}
