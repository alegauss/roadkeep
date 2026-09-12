import {
  BASE,
  BASE_LOCALE,
  DEFAULT_SETTINGS,
  EMPTY_CATALOGUE,
  identityFrom,
  isPseudo,
  pseudo,
  PSEUDO_CLOSE,
  PSEUDO_OPEN,
  PRODUCT,
  PT_BR,
  type RendererBridge,
  saidOfBuild,
  translator,
  type Wording,
  wordingFor,
  bridgedRun,
  EngineCallFailed,
  openedFrom,
  openProject,
  readBriefPayload,
  type SessionRecord,
  type Transport,
  composeWrite,
} from '@rk/core'
import { vigDesignSystemTranslations } from '@viglet/viglet-design-system/i18n'
import { fireEvent, screen, waitFor } from '@testing-library/react'
import i18next from 'i18next'
import { afterEach, beforeAll, describe, expect, it } from 'vitest'

import { AREA_WORDING } from './areas'
import { ROUTED } from './routes'
import { drawWindow } from './harness'
import { choicesAtLaunch } from './launch'
import { startSpeaking } from './speaking'
import { stubBridge } from './stub-bridge'

/**
 * RG51: the test the design rests on.
 *
 * The screen is rendered under a locale nobody speaks, in which every catalogue value is
 * wrapped in brackets. Anything visible without them is a string somebody typed into a
 * component — which this sees on the run after they type it, rather than on the day a
 * second locale is added and every screen has to be reopened.
 *
 * **Both halves of the wording, since RG116.** This app's strings reach the screen two ways:
 * the catalogue, and the i18next bundle the package's own components resolve. The second was
 * empty until the language menu arrived and needed a name, so the run now wraps that bundle
 * too — otherwise adding a string there would be adding one this guard cannot see.
 *
 * **And the whole document, with every surface open, since RG123.** Three of this window's
 * surfaces were invisible here and each for its own reason. The shortcuts sheet and the
 * command palette render into a portal, which is a sibling of the render's `container` and
 * not inside it — measured, and not what the design assumed of the third: `Toaster` renders
 * in place, so the toast was inside the container all along and the run simply never raised
 * one. So this reads `document.body`, opens the two dialogs, and launches against a settings
 * file that lost a field. The first look found two things: a literal in the package's dialog
 * markup, and the English detail RG123's other half moved into the catalogue.
 */
const BUILT = identityFrom({ version: '0.0.0', commit: 'abc1234', signed: 'unsigned' })

function withBridge(parts: Partial<RendererBridge>): void {
  const bridge: RendererBridge = stubBridge({
    identify: () => Promise.resolve({ transport: 'ipc', build: BUILT }),
    settings: () => Promise.resolve({ settings: DEFAULT_SETTINGS, reset: [], locale: BASE_LOCALE }),
    saveTheme: () => Promise.resolve(),
    saveLocale: () => Promise.resolve(),
    // A machine with no project under its roots (RG145): the portfolio settles on a sentence
    // of its own, and no payload's prose reaches a screen this run reads.
    projects: () => Promise.resolve(EMPTY_CATALOGUE),
    ...parts,
  })
  Object.defineProperty(window, 'roadkeep', { value: bridge, configurable: true })
}

/**
 * A launch that lost a setting, which is what puts a toast on the screen.
 *
 * The notice is the reason this run has to reach a portal at all: the frame is a
 * `MessageKey` and the detail is what the reader of the settings file said about the field
 * it reset, so a run that could not see the toast could not see the half of a sentence that
 * was never in the catalogue.
 */
async function launchedWithALoss(): Promise<void> {
  withBridge({
    settings: () =>
      Promise.resolve({
        settings: DEFAULT_SETTINGS,
        reset: [{ lost: 'width', fields: { width: DEFAULT_SETTINGS.width } }],
        locale: BASE_LOCALE,
      }),
  })
  await choicesAtLaunch()
}

afterEach(async () => {
  // The notice list lives with the launch, so a clean launch is what empties it for the
  // next test — the same reason `notices.test.tsx` gives.
  withBridge({})
  await choicesAtLaunch()
  Reflect.deleteProperty(window, 'roadkeep')
})

/**
 * The whole window, chrome included. Since RG63 most of this app's own sentences are in the
 * shell — the wordmark, the palette's prompt, the ground — so a run against the page alone
 * would be a guard that stopped watching the strings most likely to be typed in by hand.
 */
function drawIn(over: Wording | undefined) {
  return drawWindow({ over })
}

/**
 * Every piece of text the rendered screen actually shows, deduplicated.
 *
 * Read off the leaf elements rather than off `textContent` at the root, which would join
 * a wrapped string to an unwrapped one and hide exactly what this is looking for.
 *
 * `script` and `style` are skipped: `next-themes` injects one to set the class before the
 * first paint, and it carries the chosen theme in its source rather than on screen.
 */
const UNREAD = new Set(['SCRIPT', 'STYLE'])

function visibleText(root: HTMLElement): string[] {
  const seen = new Set<string>()
  for (const node of root.querySelectorAll('*')) {
    if (node.children.length > 0 || node.tagName === KEYCAP || UNREAD.has(node.tagName)) continue
    const text = node.textContent.trim()
    if (text !== '') seen.add(text)
  }
  return [...seen]
}

/**
 * The attributes a person reads or hears (RG140).
 *
 * `visibleText` is what a sighted reader sees, and a screen reader says more: a button named
 * by `aria-label`, a field's `placeholder`, a `title`. None is a leaf's text, so the run that
 * found the package's `Close` walked past its `Back to top` in the same window.
 */
const SPOKEN = [
  'alt',
  'aria-description',
  'aria-label',
  'aria-roledescription',
  'aria-valuetext',
  'placeholder',
  'title',
] as const

function spokenNames(root: HTMLElement): string[] {
  const seen = new Set<string>()
  for (const node of root.querySelectorAll('*')) {
    for (const attribute of SPOKEN) {
      const value = node.getAttribute(attribute)?.trim()
      if (value) seen.add(value)
    }
  }
  return [...seen]
}

/**
 * The only text on this screen that is a name and not a sentence.
 *
 * The build line joined them at RG118. It is the same characters in every language on
 * purpose — a version, a commit, `packaged` or `source`, `signed` or not — because what it
 * is for is being pasted into a defect report, and a translated stamp is one that has to be
 * read back before it can be used. `build.test.ts` holds what it says.
 */
const IDENTIFIERS = new Set<string>([PRODUCT, saidOfBuild(BUILT)])

// And no exception for the package's own words, which there was until RG132. The close
// button was `<span class="sr-only">Close</span>` in its markup, found the moment this run
// first looked inside a dialog (RG123), and `aria-label="Back to top"` joined it when the
// run began reading names (RG140). Both were listed rather than filtered by shape, so the
// day they were translated the list would go stale and be deleted. The design system moved
// both into its bundle (VDS93, 2026.3.9): a bare word from the package is now a finding like
// any other.

/** What the package says for one of its own keys, read off its bundle rather than typed. */
function packageSays(group: string, key: string): string {
  const bundle = vigDesignSystemTranslations.en as Record<string, unknown>
  const bento = bundle['bento'] as Record<string, Record<string, string>> | undefined
  return bento?.[group]?.[key] ?? ''
}

/**
 * A sentence only the shortcuts sheet says, read at module scope — which is to say before
 * the wrapping below.
 *
 * `initVigI18n` hands i18next the very object `vigDesignSystemTranslations` exposes, and a
 * deep `addResourceBundle` merges into it: after the wrapping, reading the package's bundle
 * gives back the bracketed string. Measured as `⟦⟦Keyboard shortcuts⟧⟧`.
 *
 * The description and not the title, because `visibleText` reads leaves and the sheet's
 * heading is not one — the element holding it holds an element.
 */
const IN_THE_SHEET = packageSays('shortcuts', 'description')

/** The same brackets `pseudo` uses, over the nested shape an i18next bundle has. */
function pseudoDeep(bundle: Record<string, unknown>): Record<string, unknown> {
  return Object.fromEntries(
    Object.entries(bundle).map(([key, value]) => [
      key,
      typeof value === 'string'
        ? `${PSEUDO_OPEN}${value}${PSEUDO_CLOSE}`
        : pseudoDeep(value as Record<string, unknown>),
    ]),
  )
}

beforeAll(async () => {
  // The package's components read i18next and nothing else, so the wrapped bundle has to
  // be in the instance itself rather than handed to a provider.
  //
  // The package's own bundle is wrapped beside this app's (RG123), because the surfaces this
  // run now opens are the package's: the palette and the shortcuts sheet say a dozen things
  // out of `vigDesignSystemTranslations`, and unwrapped they would arrive here as a dozen
  // findings about strings this repository does not own. Wrapped, what is left bare is a
  // literal somebody typed into a component — which is the claim, whoever typed it.
  await startSpeaking(BASE_LOCALE)
  i18next.addResourceBundle(
    BASE_LOCALE,
    'translation',
    pseudoDeep({
      ...(vigDesignSystemTranslations.en as Record<string, unknown>),
      ...AREA_WORDING.en,
    }),
    true,
    true,
  )
})

/**
 * A key on the keyboard is not a sentence.
 *
 * `Ctrl K`, `⌘K` and `?` are drawn in `kbd` and are the platform's own names for its keys —
 * translating them would be telling somebody to press a key their keyboard does not have.
 * The element is the claim: anything outside a `kbd` is prose and is held to the rule.
 */
const KEYCAP = 'KBD'

/** What no catalogue accounts for, of what was found. The whole document, portals included. */
function bare(found: readonly string[]): string[] {
  return found.filter((text) => !isPseudo(text) && !IDENTIFIERS.has(text))
}

const bareText = () => bare(visibleText(document.body))
const bareNames = () => bare(spokenNames(document.body))

/**
 * Every surface this window can show, open at once.
 *
 * Together rather than one render each, because the question is about the window and not
 * about any one of them — and because three renders are three places to add a fourth
 * surface and not notice.
 */
async function everySurface(): Promise<void> {
  // The toast first: it is raised on mount, and waiting for its frame is also what says the
  // launch's notice arrived rather than that the run forgot to cause one.
  await screen.findByText(`${PSEUDO_OPEN}${BASE['settings.reset']}${PSEUDO_CLOSE}`)
  fireEvent.click(screen.getByTestId('shortcuts'))
  fireEvent.click(screen.getByTestId('palette-trigger'))
  await screen.findAllByRole('dialog')
}

describe('RG51: nothing on the screen is typed into a component', () => {
  it('wraps every sentence, leaving only the package names bare', async () => {
    await launchedWithALoss()
    drawIn(pseudo())
    // Wait for the bridge to answer, so the portfolio is a settled string and not `asking`.
    await screen.findByText(`${PSEUDO_OPEN}${BASE['portfolio.none']}${PSEUDO_CLOSE}`)
    await everySurface()

    expect(bareText()).toEqual([])
    expect(bareNames()).toEqual([])
  })

  it('finds the literal a component would have kept', () => {
    // The guard on the guard: with nothing wrapped, the check above has to fail — otherwise
    // a green run would prove only that the test does not look.
    drawIn(undefined)

    expect(bareText().length).toBeGreaterThan(0)
  })

  it('finds a name a component would have kept, read off its attributes alone', () => {
    // The same guard for the names (RG140). The shell's two named controls take their names
    // from the catalogue, so unwrapped they are English — and a run that never read an
    // attribute would pass here as it passed over the package's back-to-top button.
    drawIn(undefined)

    expect(bareNames().length).toBeGreaterThan(0)
  })

  it('reads a row that could not be opened, where the reason is this app’s own (RG168)', async () => {
    // The gap RG168 closed. This run drew an empty portfolio, so no row's reason had ever
    // been on the screen it reads — and every one of those sentences was composed in
    // English in `core`. One project that does not open puts one on screen.
    const path = '/code/unresolved'
    withBridge({
      // The portfolio watches each row it lists (RG166, RG167), so a stub that refuses to
      // be subscribed to is a list that never arrives.
      subscribe: () => () => undefined,
      projects: () =>
        Promise.resolve({
          version: 1,
          roots: [{ path: '/code', depth: 1 }],
          projects: [
            {
              path,
              aliases: [],
              commonDir: null,
              root: '/code',
              confirmed: '',
              presence: 'present' as const,
            },
          ],
        }),
      // Nothing answered, and nothing was tried: the tried panel then draws nothing, so
      // what is left on the row is the sentence alone.
      open: () =>
        Promise.resolve({
          kind: 'unresolved' as const,
          root: path,
          reason: 'no candidate answered `engines --json`',
          code: 'none-answered' as const,
          tried: [],
        }),
    })
    await choicesAtLaunch()
    drawIn(pseudo())
    await screen.findByText(`${PSEUDO_OPEN}${BASE['portfolio.unreadable']}${PSEUDO_CLOSE}`)

    // The folder's own name and its path are identifiers, like the product's name.
    const named = new Set([path, 'unresolved'])
    expect(bare(visibleText(document.body)).filter((text) => !named.has(text))).toEqual([])
  })

  it('looks inside a portal, which is where two of these surfaces render', async () => {
    // The gap RG123 closed, held as its own claim rather than left to the check above: the
    // sheet and the palette render into `document.body`, so a run reading the render's own
    // container saw nothing of either — and a literal in one of them read as an empty list.
    // The one this found on its first look was the package's `Close`, translated since RG132.
    await launchedWithALoss()
    const { container } = drawIn(pseudo())
    await everySurface()
    const inTheSheet = `${PSEUDO_OPEN}${IN_THE_SHEET}${PSEUDO_CLOSE}`

    expect(visibleText(container)).not.toContain(inTheSheet)
    expect(visibleText(document.body)).toContain(inTheSheet)
  })

  it('says the same screen in English, which is the base and not a translation', () => {
    drawIn(undefined)

    expect(screen.getByRole('heading', { name: BASE['portfolio.title.unknown'] })).toBeTruthy()
    expect(screen.getByText(BASE['portfolio.footnote'])).toBeTruthy()
  })
})

describe('RG51: a translation reaches the screen', () => {
  it('draws what the locale says, per key, leaving the rest in English', async () => {
    withBridge({ identify: () => Promise.resolve({ transport: 'http', build: BUILT }) })
    drawIn({ 'portfolio.footnote': 'Cada número nesta tela foi impresso por um verbo.' })

    expect(screen.getByText('Cada número nesta tela foi impresso por um verbo.')).toBeTruthy()
    // Untranslated, so English — and never the key.
    expect(await screen.findByText(BASE['portfolio.none'])).toBeTruthy()
  })
})

describe('RG86: the locale this build ships', () => {
  // Through `translator` rather than off `PT_BR` directly: the type is `Partial`, and a
  // test reading a key straight out of it would compare against `undefined` the day one
  // goes missing instead of failing on the sentence that is not there.
  const inPtBr = translator(PT_BR)

  it('draws the screen in Portuguese, from the tag alone', async () => {
    withBridge({})
    drawIn(wordingFor('pt-BR'))

    expect(screen.getByText(inPtBr('portfolio.footnote'))).toBeTruthy()
    expect(await screen.findByText(inPtBr('portfolio.none'))).toBeTruthy()
  })

  it('says the base for a tag nobody wrote, which is what an unshipped locale is', () => {
    drawIn(wordingFor('ja'))

    expect(screen.getByText(BASE['portfolio.footnote'])).toBeTruthy()
  })
})

/**
 * RG176: the same run, over every surface a reader can route to.
 *
 * Derived from the route table rather than listed, so a surface added to `ROUTED` is one this
 * reads without anybody remembering to add it here. One render per surface and not per state:
 * a state a person cannot reach without a refusal is one this would have to arrange, and
 * chasing those would be a second copy of the screens' own tests.
 *
 * The engine answers by verb the way each screen's own test builds one. Everything it feeds
 * through is prose the project owns — a symptom, an id, a path — and those are named in
 * `DATA`, because what this run is about is the strings this app typed, not the ones a
 * project wrote.
 */
const SURFACE_ROOT = 'D:\\code\\alpha'
const SURFACE_ID = 'AL1'
const SURFACE_KEY = 'alpha-AL1-1'

/** Every string the fixture below puts on a screen: the project's words, never this app's. */
const DATA = new Set([
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
])

const asJson = (value: unknown) => JSON.stringify(value)

const SURFACE_LINE = {
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

const SURFACE_SECTION = {
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

/** What each verb answers, for a window drawing every surface at once. */
function surfaceAnswer(argv: readonly string[]): string | undefined {
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

/** One session this window started, so the two session surfaces have something to draw. */
function surfaceSession(): SessionRecord {
  const brief = surfaceAnswer(['-C', SURFACE_ROOT, 'brief']) ?? '{}'
  const read = readBriefPayload(JSON.parse(brief), '')
  if (!read.ok) throw new Error('the brief fixture does not match the shape')
  return {
    key: SURFACE_KEY,
    root: SURFACE_ROOT,
    id: SURFACE_ID,
    handed: read.value,
    agent: { command: ['claude'], version: '2.0.0', said: 'claude 2.0.0' },
    lines: [],
    outcome: null,
  }
}

/** Each route with its parameters filled in, which is where a reader can actually be. */
function everyRoute(): string[] {
  return ROUTED.map((path) =>
    path
      .replace(':root', encodeURIComponent(SURFACE_ROOT))
      .replace(':id', SURFACE_ID)
      .replace(':key', SURFACE_KEY),
  )
}

describe('RG176: every surface a reader can route to, under the pseudo-locale', () => {
  it('wraps every sentence on each of them, leaving only what the project wrote bare', async () => {
    const transport: Transport = {
      run(request) {
        const answered = surfaceAnswer(request.argv)
        if (answered === undefined) {
          return Promise.reject(new EngineCallFailed('unspawnable', 'no', 1))
        }
        return Promise.resolve({ code: 0, stdout: answered, stderr: '', durationMs: 1 })
      },
    }
    const opened = openedFrom(
      await openProject(SURFACE_ROOT, [['python', 'launch.py']], () => transport),
    )
    const sessions = [surfaceSession()]
    const bareHere = (found: readonly string[]) => found.filter((text) => !DATA.has(text))

    for (const route of everyRoute()) {
      withBridge({
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
              },
            ],
          }),
        open: () => Promise.resolve(opened),
        run: (root, request) => bridgedRun(() => transport.run({ ...request, root })),
        subscribe: () => () => undefined,
        gates: () => Promise.resolve([]),
        sessions: () => Promise.resolve(sessions),
        governedAt: () => Promise.resolve([]),
      })
      await choicesAtLaunch()
      const drawn = drawWindow({ over: pseudo(), at: route })
      // Waited on rather than rendered and read at once: what this is about is the screen
      // filled in from its reads, and its first frame has none of them.
      await waitFor(() => {
        expect({ route, bare: bareHere(bareText()), names: bareHere(bareNames()) }).toEqual({
          route,
          bare: [],
          names: [],
        })
      })
      drawn.unmount()
    }
  }, 30000)
})
