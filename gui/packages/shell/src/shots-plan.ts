import {
  filledRoute,
  LOCALE_TAGS,
  routeParams,
  SESSION_ROUTE,
  SURFACE_ROUTES,
  TASK_ROUTE,
  type Theme,
} from '@rk/core'

/**
 * What `npm run shots` photographs, worked out before anything is started (RG209).
 *
 * The half of the screenshot run that needs no window: which surfaces, in which grounds,
 * languages and widths, under which file names. Kept apart from the launch so a surface the
 * router serves and the run cannot fill fails a fast test, rather than a run that starts an
 * app and a python engine to discover it.
 *
 * **Every route, every time.** The list is `core`'s `SURFACE_ROUTES`, the one the router
 * serves, so a surface added to the window is photographed the day it routes. A pattern whose
 * parameter the fixture cannot fill is a refusal naming it, never a surface quietly skipped.
 *
 * **Two grounds and not three.** `system` is a setting and not a ground: it paints whichever of
 * the other two the machine is on, so photographing it would photograph one of them twice.
 */

/** What the fixture puts in a route: its root, one of its lines, and the session a run started. */
export interface ShotValues {
  readonly root: string
  /** The line the task surface shows, which is left as it was: ready, and nobody on it. */
  readonly id: string
  /**
   * The line handed to the scripted agent (RG210), a different one, so the task surface is not
   * photographed with a session on it.
   */
  readonly sessionId: string
  /** The key the handover answered. */
  readonly key: string
}

/**
 * The states the session surface is photographed in (RG210): following its end as a run writes,
 * scrolled up with the way back showing, with its notes folded (RG208), and with a file it
 * edited open in the viewer (RG245).
 *
 * Three files rather than one, since the viewer opens on the file against its original (RG282)
 * and the three answers that comparison can give are different pictures: a file changed, one
 * made — every line new — and one gone, every line removed with the file itself unreadable.
 */
export const SESSION_SHOTS = [
  'following',
  'scrolled',
  'folded',
  'file',
  'file-made',
  'file-gone',
] as const
export type SessionShot = (typeof SESSION_SHOTS)[number]

/**
 * The states the task surface is photographed in: at rest, with the explanation open (RG285),
 * and with that dialog scrolled to where the work lands (RG288).
 *
 * The second explanation shot is the lanes: the dialog is taller than the window it opens in, so
 * a picture of its top is a picture of everything above them.
 */
export const TASK_SHOTS = [null, 'explain', 'explain-where'] as const
export type TaskShot = (typeof TASK_SHOTS)[number]

export const SHOT_GROUNDS: readonly Exclude<Theme, 'system'>[] = ['light', 'dark']

/** The widths a surface is read at: a desktop window, and the phone width the contract names. */
export const SHOT_SIZES: readonly { readonly width: number; readonly height: number }[] = [
  { width: 1280, height: 800 },
  { width: 400, height: 800 },
]

/** Where the pictures go, under the repository, and what `.gitignore` names. */
export const SHOTS_DIRECTORY = '.shots'

export interface Capture {
  /** The surface's name: its pattern's fixed segments, `project-task-session` for a session. */
  readonly surface: string
  readonly pattern: string
  /** The route with its parameters filled, which is what the hash is set to. */
  readonly route: string
  readonly ground: Exclude<Theme, 'system'>
  readonly locale: string
  readonly width: number
  readonly height: number
  /**
   * Which state a surface is put in before the capture, null being at rest: a session has four
   * (RG210, RG282) and the task surface has the explanation open (RG285).
   */
  readonly state: SessionShot | TaskShot
  /** The PNG's name under the output directory. */
  readonly file: string
}

/** A surface's name, from the fixed segments of its pattern: `/` is `home`. */
export function surfaceName(pattern: string): string {
  const fixed = pattern.split('/').filter((segment) => segment !== '' && !segment.startsWith(':'))
  return fixed.length === 0 ? 'home' : fixed.join('-')
}

/**
 * Every capture, in the order a run takes them: ground, then language, then surface, then
 * width — so one window reloads four times and not once per picture.
 *
 * @param only surface names to keep, as `--only` spells them. An unknown name is refused with
 *   the names that exist: a typo narrowed to nothing would be a run that says it succeeded.
 */
export function capturesFor(values: ShotValues, only: readonly string[] = []): Capture[] {
  const surfaces = SURFACE_ROUTES.map((pattern) => {
    // A session's line is the one handed over, not the one the task surface shows.
    const id = pattern === SESSION_ROUTE ? values.sessionId : values.id
    const route = filledRoute(pattern, { root: values.root, id, key: values.key })
    if (route === null) {
      throw new Error(
        `the screenshot run cannot fill ${pattern}: it knows root, id and key, and this names ` +
          routeParams(pattern).join(', '),
      )
    }
    return { surface: surfaceName(pattern), pattern, route }
  })

  const known = surfaces.map((one) => one.surface)
  const unknown = only.filter((name) => !known.includes(name))
  if (unknown.length > 0) {
    throw new Error(`no surface is called ${unknown.join(', ')}; there are ${known.join(', ')}`)
  }
  const kept = only.length === 0 ? surfaces : surfaces.filter((one) => only.includes(one.surface))

  const captures: Capture[] = []
  for (const ground of SHOT_GROUNDS) {
    for (const locale of LOCALE_TAGS) {
      for (const { surface, pattern, route } of kept) {
        const states: readonly (SessionShot | TaskShot)[] =
          pattern === SESSION_ROUTE ? SESSION_SHOTS : pattern === TASK_ROUTE ? TASK_SHOTS : [null]
        for (const state of states) {
          for (const { width, height } of SHOT_SIZES) {
            const named = state === null ? surface : `${surface}.${state}`
            captures.push({
              surface,
              pattern,
              route,
              ground,
              locale,
              width,
              height,
              state,
              file: `${named}.${ground}.${locale}.${String(width)}.png`,
            })
          }
        }
      }
    }
  }
  return captures
}

export interface ShotOptions {
  /** Surface names to keep. Empty is every surface. */
  readonly only: readonly string[]
  /** Scan for accessibility and write no pictures (RG211). */
  readonly a11yOnly: boolean
}

/**
 * Read `--only a --only b`, `--only a,b` and `--a11y-only`. Anything else on the line is
 * refused, since a flag misspelt and ignored is a run that did something else than asked.
 */
export function optionsFrom(argv: readonly string[]): ShotOptions {
  const only: string[] = []
  let a11yOnly = false
  for (let at = 0; at < argv.length; at += 1) {
    const arg = argv[at]
    if (arg === '--a11y-only') {
      a11yOnly = true
      continue
    }
    if (arg !== '--only') {
      throw new Error(`the screenshot run takes --only <surface> and --a11y-only, not ${arg}`)
    }
    const value = argv[at + 1]
    if (value === undefined || value.startsWith('--')) throw new Error('--only names a surface')
    only.push(...value.split(',').filter((name) => name !== ''))
    at += 1
  }
  return { only, a11yOnly }
}

/**
 * Whether a capture is also scanned for accessibility (RG211): once per surface, state and
 * ground, at the desktop width and in the base language.
 *
 * Not at every width and language: what axe and the chosen-state rule read is colour, names
 * and structure, which a translation or a narrower window does not change — and eighty scans
 * would cost the run a minute to say the same thing four times.
 */
export function isScanned(capture: Capture): boolean {
  return capture.width === SHOT_SIZES[0]?.width && capture.locale === LOCALE_TAGS[0]
}

/**
 * A page expression that resolves once the surface has settled, or false at the ceiling.
 *
 * Settled is measured and not slept: nothing marked `aria-busy`, and no change to the document
 * for `quietMs`. A string rather than a function, because this package has no DOM types and
 * the expression runs in the page, where they are.
 */
export function settleScript(quietMs: number, ceilingMs: number): string {
  return `new Promise((resolve) => {
  const started = performance.now()
  let last = started
  const observer = new MutationObserver(() => { last = performance.now() })
  observer.observe(document.documentElement, { subtree: true, childList: true, attributes: true, characterData: true })
  const tick = () => {
    const now = performance.now()
    const busy = document.querySelector('[aria-busy="true"]') !== null
    if (!busy && now - last >= ${String(quietMs)}) { observer.disconnect(); resolve(true); return }
    if (now - started >= ${String(ceilingMs)}) { observer.disconnect(); resolve(false); return }
    setTimeout(tick, 50)
  }
  tick()
})`
}
