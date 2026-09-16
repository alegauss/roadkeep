import {
  bridgedRun,
  composeWrite,
  DECLARES_NOTHING,
  EngineCallFailed,
  LOCALE_NAMES,
  openedFrom,
  openProject,
  readBriefPayload,
  type SessionRecord,
  type Theme,
  type Transport,
  type Wording,
} from '@rk/core'
import type { RenderResult } from '@testing-library/react'

import { drawWindow } from './harness'
import { choicesAtLaunch } from './launch'
import { ROUTED } from './routes'
import { stubBridge } from './stub-bridge'

/**
 * One window with every surface filled in, for the runs that read all of them (RG176, RG214).
 *
 * A test instrument and not shipped code, like `harness` and `session-harness`. It was inside
 * `wording.test.tsx` until RG214 asked the same question about width, tab order and focus in a
 * real browser — and a fixture spelled twice is one that drifts, which is the reason RG213 gave
 * for `session-harness` a block earlier.
 *
 * The engine answers by verb, the way each screen's own test builds one. Everything it feeds
 * through is prose a project wrote — a symptom, an id, a path — and `wording.test.tsx` names
 * that set, because what its run is about is the strings this app typed rather than the ones a
 * project did.
 */

export const SURFACE_ROOT = 'D:\\code\\alpha'
export const SURFACE_ID = 'AL1'
export const SURFACE_KEY = 'alpha-AL1-1'

const asJson = (value: unknown) => JSON.stringify(value)

export const SURFACE_LINE = {
  id: SURFACE_ID,
  status: '📋',
  block: 'A',
  symptom: 'the first line is ready',
  why: 'Nothing holds it.',
  deps: [] as string[],
  ref: SURFACE_ID,
  line: 7,
  length: 90,
}

export const SURFACE_SECTION = {
  anchor: SURFACE_ID,
  title: 'The design, as the file keeps it.',
  level: 3,
  file: 'docs/IMPROVEMENTS.md',
  first: 1,
  last: 4,
  words: 9,
  own_words: 9,
  body: 'The design, as the file keeps it.',
}

/** Every string this fixture puts on a screen: a project's own words, never this app's. */
export const SURFACE_DATA: ReadonlySet<string> = new Set([
  SURFACE_ROOT,
  SURFACE_ID,
  SURFACE_KEY,
  'alpha',
  'A',
  'the first line is ready',
  'Nothing holds it.',
  'ready',
  '📋',
  'docs/ROADMAP.md',
  'docs/IMPROVEMENTS.md',
  // The governed roles, drawn as the project's own config spells them (RG149) — a role is
  // that project's word for one of its files, like a marker, and not a sentence.
  'roadmap',
  'python launch.py',
  '0.2.400',
  '/e',
  'The design, as the file keeps it.',
  'No Markdown parsed in this app',
  'A reader that parses is a second one.',
  'Every number is one a verb printed',
  'claude',
  '2.0.0',
  'claude 2.0.0',
  'ref.unresolved',
  'docs/ROADMAP.md:7',
  'points at §AL1, which is not there',
  'section add AL1 --title …',
  'writes the section the line points at',
  // The command the filing screen draws before it runs (RG151): an argv this app composed
  // from the write table, which is a thing to run and not a sentence to translate — derived
  // here rather than typed, so it is the same string the screen builds.
  composeWrite(SURFACE_ROOT, 'add', { block: '', symptom: '', why: '' }).argv.join(' '),
  // Each language by the name it calls itself, which the settings screen offers (RG207). An
  // endonym is a name and the same in every window: wrapping it would hand a Portuguese
  // reader looking for English a word they cannot find.
  ...Object.values(LOCALE_NAMES),
])

/** What each verb answers, for a window drawing every surface at once. */
export function surfaceAnswer(argv: readonly string[]): string | undefined {
  switch (argv[2] ?? '') {
    case 'engines':
      return asJson({
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
      return asJson({
        version: '0.2.400',
        source: 'roadkeep.toml',
        keys: [
          {
            table: 'files',
            key: 'roadmap',
            address: 'files.roadmap',
            declared: true,
            set: '"docs/ROADMAP.md"',
            default: null,
          },
        ],
      })
    case 'commands':
      return asJson({ version: '0.2.400', source: null, commands: [] })
    case 'stats':
      return asJson({
        file: 'docs/ROADMAP.md',
        total: 1,
        uncounted: 0,
        markers: {},
        startable: { open: 1, startable: 1, waiting: 0, absent: [] },
        blocks: [],
      })
    case 'block':
      return asJson({ file: 'docs/ROADMAP.md', blocks: [] })
    case 'list':
      return asJson({ file: 'docs/ROADMAP.md', total: 1, uncounted: [], tasks: [SURFACE_LINE] })
    case 'deps':
      return asJson({ id: SURFACE_ID, readiness: 'ready', blockers: [] })
    case 'pick':
      return asJson({ pick: null, tier: '', reason: '', ready: 1, blocked: 0 })
    case 'reversals':
      return asJson({ root: SURFACE_ROOT, asked: null, reversed: [] })
    case 'claims':
      return asJson({ file: 'docs/ROADMAP.md', held: [], expired: [], stale: [] })
    case 'section':
      return asJson(SURFACE_SECTION)
    case 'non-goal':
      return asJson({
        file: 'docs/ROADMAP.md',
        governed: true,
        non_goals: ['No Markdown parsed in this app'],
        non_goals_elided: 0,
        non_goals_quoted: {},
        non_goals_why: {
          'No Markdown parsed in this app': 'A reader that parses is a second one.',
        },
      })
    case 'budget':
      return asJson({
        id: SURFACE_ID,
        status: '📋',
        deps: [],
        open_line: true,
        line_max: 320,
        structure: 41,
        ref: SURFACE_ID,
        ref_assumed: true,
        prose: 279,
        fields: [],
        section: {
          anchor: SURFACE_ID,
          role: 'improvements',
          written: false,
          unit: 'words',
          limit: 250,
          taken: 0,
          over: 0,
        },
      })
    case 'lint':
      return asJson({
        root: SURFACE_ROOT,
        clean: false,
        checked: ['docs/ROADMAP.md'],
        lines: 1,
        sections: 1,
        problems: 1,
        codes: {},
        findings: [
          {
            code: 'ref.unresolved',
            file: 'docs/ROADMAP.md',
            line: 7,
            column: null,
            id: SURFACE_ID,
            message: 'points at §AL1, which is not there',
            remedy: {
              kind: 'compose',
              decision: '',
              sequence: false,
              awaits: '',
              doors: [
                {
                  argv: ['section', 'add', SURFACE_ID, '--title', '…'],
                  what: 'writes the section the line points at',
                  complete: false,
                  writes: true,
                },
              ],
            },
          },
        ],
        notes: [],
      })
    case 'brief':
      return asJson({
        ...SURFACE_LINE,
        rendered: 'the first line is ready',
        readiness: 'ready',
        picked: null,
        deps_resolved: [],
        chains: [],
        unblocks: null,
        non_goals: ['No Markdown parsed in this app'],
        non_goals_elided: 0,
        quotes: [],
        done_when: ['Every number is one a verb printed'],
        done_when_elided: 0,
        done_when_own: [],
        done_when_own_elided: 0,
        done_when_folded: {},
        held: [],
        landed: [],
        budget: null,
        claimed: null,
        section: SURFACE_SECTION,
        section_absence: '',
      })
    default:
      return undefined
  }
}

/** The engine behind every surface: whatever `surfaceAnswer` has, and a refusal otherwise. */
export const surfaceTransport: Transport = {
  run(request) {
    const answered = surfaceAnswer(request.argv)
    if (answered === undefined) {
      return Promise.reject(new EngineCallFailed('unspawnable', 'no', 1))
    }
    return Promise.resolve({ code: 0, stdout: answered, stderr: '', durationMs: 1 })
  },
}

/** One session this window started, so the two session surfaces have something to draw. */
export function surfaceSession(): SessionRecord {
  const brief = surfaceAnswer(['-C', SURFACE_ROOT, 'brief']) ?? '{}'
  const read = readBriefPayload(JSON.parse(brief), '')
  if (!read.ok) throw new Error('the brief fixture does not match the shape')
  return {
    key: SURFACE_KEY,
    root: SURFACE_ROOT,
    id: SURFACE_ID,
    started: '2026-09-15T10:00:00.000Z',
    handed: { kind: 'line', brief: read.value },
    agent: { command: ['claude'], version: '2.0.0', said: 'claude 2.0.0' },
    lines: [],
    moved: [],
    movedBeyond: 0,
    outcome: null,
  }
}

/** Each route with its parameters filled in, which is where a reader can actually be. */
export function everyRoute(): string[] {
  return ROUTED.map((path) =>
    path
      .replace(':root', encodeURIComponent(SURFACE_ROOT))
      .replace(':id', SURFACE_ID)
      .replace(':key', SURFACE_KEY),
  )
}

/**
 * One surface, drawn with the fixture behind it.
 *
 * The bridge is rebuilt per route rather than shared, because `choicesAtLaunch` reads it and a
 * window is launched once — which is also what empties the notice list between surfaces.
 */
export async function atSurface(
  route: string,
  options: {
    /** A translation to force, for the run that reads what is on the screen (RG176). */
    readonly over?: Wording
    /** The ground to draw in, for the run that reads a colour (RG214). */
    readonly initial?: Theme
  } = {},
): Promise<RenderResult> {
  const opened = openedFrom(
    await openProject(SURFACE_ROOT, [['python', 'launch.py']], () => surfaceTransport),
  )
  const sessions = [surfaceSession()]

  Object.defineProperty(window, 'roadkeep', {
    value: stubBridge({
      projects: () =>
        Promise.resolve({
          version: 1,
          roots: [{ path: 'D:\\code', depth: 1 }],
          projects: [
            {
              path: SURFACE_ROOT,
              aliases: [],
              commonDir: null,
              root: 'D:\\code',
              confirmed: '',
              presence: 'present' as const,
              branch: '',
              declared: DECLARES_NOTHING,
            },
          ],
        }),
      open: () => Promise.resolve(opened),
      run: (root, request) => bridgedRun(() => surfaceTransport.run({ ...request, root })),
      subscribe: () => () => undefined,
      gates: () => Promise.resolve([]),
      sessions: () => Promise.resolve(sessions),
      governedAt: () => Promise.resolve([]),
    }),
    configurable: true,
  })
  await choicesAtLaunch()
  return drawWindow({ ...options, at: route })
}
