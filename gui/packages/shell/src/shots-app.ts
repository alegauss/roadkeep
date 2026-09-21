import { spawnSync, type ChildProcess } from 'node:child_process'
import path from 'node:path'
import { setTimeout as after } from 'node:timers/promises'

import { AxeBuilder } from '@axe-core/playwright'
import { _electron, type ElectronApplication, type Page } from 'playwright-core'

import {
  AXE_TAGS,
  CHOSEN_SCRIPT,
  chosenFindings,
  findingsIn,
  judgeChosen,
  readingsFrom,
  type ChosenVerdict,
  type Finding,
} from './accessibility'
import { electronPath, launchEnv, shellRoot } from './launch'
import { SCRIPTED_MADE } from './scripted-agent'
import { settleScript, type Capture } from './shots-plan'

/**
 * The app as the screenshot run drives it, through Playwright (RG209).
 *
 * `running-app.ts` speaks the DevTools protocol by hand for the live suite, and a second
 * hand-written client for pictures would be two of them drifting. Playwright drives Electron
 * itself — `_electron.launch`, `firstWindow`, `setViewportSize`, `screenshot` — and needs no
 * browser of its own, since Electron is the browser.
 *
 * **Its Electron support is marked experimental**, and three things were measured here before
 * anything was built on it, each now a line below:
 * - a window has a minimum width, so 400 is reached by emulating the viewport, never by
 *   resizing the window, which stops at the minimum;
 * - a capture taken while an emulated resize is still landing can wait forever, so a capture
 *   waits two frames, carries a timeout and is tried once more;
 * - `ElectronApplication.close` waits on a quit this app defers until its engines are given
 *   back, so the run closes the windows and gives the process a ceiling instead.
 */

/** How long a quiet document has to stay quiet, and how long a surface is given to settle. */
const QUIET_MS = 400
const SETTLE_CEILING_MS = 10000
const CAPTURE_TIMEOUT_MS = 10000
const GOODBYE_MS = 5000
/** What stops a process that will never die from hanging a run, in seconds. Not the measure. */
const GONE_CEILING_S = 45
/** How often the listing is asked again while the killed tree is still dying. */
const GONE_ASK_MS = 250

/**
 * The most `close` can take: the goodbye it gives the app, then the wait for the tree it kills.
 *
 * What bounds a close is these two and never the app's own quit, which this app defers until
 * its engines are given back and Playwright's `close` would wait on forever (RG209).
 */
export const CLOSE_CEILING_MS = GOODBYE_MS + GONE_CEILING_S * 1000

export interface ShotApp {
  readonly app: ElectronApplication
  readonly page: Page
  /** Whether the app's process is gone. Read off the child, which outlives Playwright's handle. */
  exited(): boolean
  /** Close the windows, give the process a ceiling, and kill what is left. Safe to call twice. */
  close(): Promise<void>
}

const TWO_FRAMES =
  'new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)))'

/**
 * The window has drawn once `#root` holds anything.
 *
 * A selector and not `waitForFunction`: the renderer's content policy refuses `unsafe-eval`,
 * and a predicate given as a string is evaluated in the page with exactly that. Expressions
 * passed to `evaluate` reach the page over the DevTools protocol, which the policy does not
 * govern.
 */
async function drawn(page: Page, wait: DrawWait = DREW): Promise<void> {
  await page.waitForSelector(wait.selector, { state: 'attached', timeout: wait.timeoutMs })
}

/** What a launch waits for before it calls the window drawn, and for how long. */
export interface DrawWait {
  readonly selector: string
  readonly timeoutMs: number
}

const DREW: DrawWait = { selector: '#root > *', timeoutMs: 30000 }

/**
 * End the app's whole process tree, now.
 *
 * Not `child.kill()`, and that was measured (RG220): on Windows the process Playwright hands back
 * is a launcher whose child is the Electron main, so killing it left the main, its GPU process,
 * its renderer and its utility process standing — the same shape `mcp-transport.ts` meets with the
 * engine's launcher, answered the same way. Elsewhere Playwright starts the app in a process group
 * of its own, which a negative pid reaches whole.
 */
function endTree(child: ChildProcess, profile: string): void {
  if (child.pid !== undefined) {
    if (process.platform === 'win32') {
      spawnSync('taskkill', ['/pid', String(child.pid), '/T', '/F'], {
        stdio: 'ignore',
        windowsHide: true,
      })
    } else {
      try {
        process.kill(-child.pid, 'SIGKILL')
      } catch {
        child.kill('SIGKILL')
      }
    }
  }
  untilGone(profile)
}

/**
 * The ids of every process running with this profile on its command line (RG220).
 *
 * Asked of the operating system rather than of Playwright, because the case that matters is a
 * launch that threw and handed nothing back — and because what Playwright hands back is not
 * the app: `app.process()` is a launcher whose child is Electron's main process.
 */
export function standingOn(profile: string): number[] {
  const listed =
    process.platform === 'win32'
      ? spawnSync(
          'powershell',
          [
            '-NoProfile',
            '-Command',
            'Get-CimInstance Win32_Process | ForEach-Object { "$($_.ProcessId)`t$($_.CommandLine)" }',
          ],
          { encoding: 'utf8', windowsHide: true },
        ).stdout
      : spawnSync('ps', ['-eo', 'pid=,args='], { encoding: 'utf8' }).stdout
  return listed
    .split(/\r?\n/)
    .filter((line) => line.includes(profile))
    .map((line) => Number.parseInt(line.trim(), 10))
    .filter((pid) => Number.isInteger(pid) && pid !== process.pid)
}

/** Block for a moment without a timer, which a synchronous wait cannot await. */
function pause(ms: number): void {
  Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, ms)
}

/**
 * Return once no process on this profile is standing, however long the kill takes (RG226).
 *
 * `taskkill` answers when it has asked for every termination, not when they are done, and a
 * dying Electron still has its memory to give back. On a loaded machine that took longer than
 * the ten seconds RG220's test polled for: the main process, its GPU and its utility process
 * were measured standing past it, with threads and hundreds of handles — dying, not dead.
 *
 * **The listing is the fact, and it is asked again until it is empty.** A process handle would
 * be the better thing to wait on, and was tried: `Wait-Process` returned at once, since
 * Chromium's sandboxed children refuse another process the access a wait needs, and the error
 * was silenced. Whatever is still listed is killed again by id each round, so something the
 * tree did not reach is not waited on forever. The ceiling is only what stops a process that
 * will never die from hanging the run; when it trips, the caller sees what is still standing.
 */
function untilGone(profile: string): void {
  const until = Date.now() + GONE_CEILING_S * 1000
  for (let left = standingOn(profile); left.length > 0; left = standingOn(profile)) {
    if (Date.now() >= until) return
    for (const pid of left) {
      if (process.platform === 'win32') {
        spawnSync('taskkill', ['/pid', String(pid), '/F'], { stdio: 'ignore', windowsHide: true })
        continue
      }
      try {
        process.kill(pid, 'SIGKILL')
      } catch {
        // Gone between the listing and the kill, which is the answer this wanted.
      }
    }
    pause(GONE_ASK_MS)
  }
}

/**
 * Start the built app on a profile somebody seeded, and wait for it to draw.
 *
 * **A launch that fails gives its process back** (RG220). The child is taken the moment the app
 * starts and killed when the window never draws, since a throw out of the waits hands nobody a
 * handle: one Electron outlived its run for hours that way, after the content policy refused a
 * wait.
 *
 * @param extraEnv what this launch adds: `ROADKEEP_AGENT`, where a session is to be started
 *   against a scripted agent (RG210).
 * @param wait what counts as drawn. The window's root holding anything, unless a test needs a
 *   wait that cannot be met.
 */
export async function launchForShots(
  userData: string,
  extraEnv: Record<string, string> = {},
  wait: DrawWait = DREW,
): Promise<ShotApp> {
  const app = await _electron.launch({
    executablePath: electronPath,
    // The switch before the app path, which is how `spawnElectron` orders them too.
    args: [`--user-data-dir=${userData}`, shellRoot],
    env: launchEnv(extraEnv),
  })
  // Taken now: once the app is gone Playwright's handle is disposed, and asking it for the
  // process then throws rather than answering.
  const child = app.process()
  const exited = () => child.exitCode !== null || child.signalCode !== null

  let page: Page
  try {
    page = await app.firstWindow()
    await drawn(page, wait)
  } catch (cause) {
    // Thrown only once nothing on this profile stands, which is what RG220's test asks of it.
    endTree(child, userData)
    throw cause
  }

  return {
    app,
    page,
    exited,
    async close() {
      if (exited()) return
      const gone = new Promise<void>((resolve) => {
        child.once('exit', () => resolve())
      })
      await app.evaluate(({ BrowserWindow }) => {
        for (const window of BrowserWindow.getAllWindows()) window.close()
      })
      await Promise.race([gone, after(GOODBYE_MS)])
      if (!exited()) {
        endTree(child, userData)
        // And the child's own exit, which is what `exited()` reads: `taskkill` returning is
        // not that event having arrived, and the close test read `false` under load (RG226).
        await gone
      }
    },
  }
}

/**
 * Put the window on one ground and one language, as a person choosing them would.
 *
 * Through the preference write and a reload rather than a relaunch: the renderer reads both at
 * launch, the file is the source of both, and the write is the path the settings screen takes.
 */
export async function speakAndPaint(shot: ShotApp, ground: string, locale: string): Promise<void> {
  await shot.page.evaluate(
    `Promise.all([window.roadkeep.savePreference('theme', ${JSON.stringify(ground)}), ` +
      `window.roadkeep.savePreference('locale', ${JSON.stringify(locale)})])`,
  )
  await shot.page.reload()
  await drawn(shot.page)
}

/**
 * Hand one line to the agent the app was pointed at, through the bridge a window uses (RG210),
 * and wait until the session holds every line the agent will write.
 *
 * @returns the session's key, for its route.
 */
export async function startSession(
  shot: ShotApp,
  root: string,
  id: string,
  lines: number,
): Promise<string> {
  const { page } = shot
  // The carrier opens only a root its catalogue holds, so the scan the portfolio asks for runs
  // first; a window arriving at a line has always passed through it.
  await page.evaluate('window.roadkeep.projects()')
  const handed: unknown = await page.evaluate(
    `window.roadkeep.handOver(${JSON.stringify(root)}, ${JSON.stringify(id)})`,
  )
  const key =
    typeof handed === 'object' &&
    handed !== null &&
    'kind' in handed &&
    handed.kind === 'started' &&
    'session' in handed &&
    typeof handed.session === 'object' &&
    handed.session !== null &&
    'key' in handed.session &&
    typeof handed.session.key === 'string'
      ? handed.session.key
      : ''
  if (key === '') throw new Error(`the handover did not start a session: ${JSON.stringify(handed)}`)

  const held = await page.evaluate(`new Promise((resolve) => {
  const started = performance.now()
  const ask = () => window.roadkeep.sessions().then((all) => {
    const one = all.find((record) => record.key === ${JSON.stringify(key)})
    const count = one === undefined ? 0 : one.lines.length
    if (count >= ${String(lines)} || performance.now() - started > ${String(SETTLE_CEILING_MS * 3)}) resolve(count)
    else setTimeout(ask, 100)
  })
  ask()
})`)
  if (held !== lines) {
    const count = typeof held === 'number' ? held : 0
    throw new Error(
      `the session held ${String(count)} of the ${String(lines)} lines the agent writes`,
    )
  }
  return key
}

/** Move a preference and reload, as the settings screen's write and a relaunch would. */
async function prefer(shot: ShotApp, key: string, value: string): Promise<void> {
  await shot.page.evaluate(
    `window.roadkeep.savePreference(${JSON.stringify(key)}, ${JSON.stringify(value)})`,
  )
  await shot.page.reload()
  await drawn(shot.page)
}

/** Scroll the session's stream back to its start, which is a reader leaving its end (RG206). */
const SCROLL_STREAM_UP =
  '(() => { const region = document.querySelector(\'[data-testid="stream"]\'); if (region) region.scrollTop = 0 })()'

/**
 * Open the first file the session edited in the viewer, which is a reader clicking its row (RG245).
 *
 * The row is a tree's since RG265, and a tree's row is its own control — so it is the row that is
 * clicked, and the button only for a file outside the project, which keeps a row of its own.
 */
const OPEN_EDITED_FILE =
  '(() => { const file = document.querySelector(\'[data-testid="edited-file"]\'); const row = file && (file.closest(\'[role="treeitem"]\') || file.querySelector("button")); if (row) row.click() })()'

/**
 * The same, for the row of one path: which file the viewer opens is what makes the comparison a
 * created, a changed or a deleted one (RG282), and each of the three is its own picture.
 */
function openEdited(file: string): string {
  const selector = `[data-testid="edited-file"][data-path="${file}"]`
  return `(() => { const row = document.querySelector('${selector}'); const click = row && (row.closest('[role="treeitem"]') || row.querySelector("button")); if (click) click.click() })()`
}

/** Which file each viewer state opens, by the path the scripted run's own calls name. */
const VIEWER_FILES: Readonly<Record<string, string>> = {
  'file-made': SCRIPTED_MADE,
  'file-gone': 'src/scripted.ts',
}

/** Whether this state opens the viewer at all, which three of them do. */
function opensViewer(state: string | null): boolean {
  return state !== null && state.startsWith('file')
}

/** The task surface's explanation, opened as a reader opens it (RG285). */
const OPEN_EXPLAIN = `(() => { const button = document.querySelector('[data-testid="explain"]'); if (button) button.click() })()`

/** How long the viewer takes to slide in, which a quiet document does not wait for: CSS moves it. */
const SHEET_OPENS_MS = 600

async function settle(page: Page): Promise<boolean> {
  await page.evaluate(TWO_FRAMES)
  return (await page.evaluate(settleScript(QUIET_MS, SETTLE_CEILING_MS))) === true
}

/** What a scan of one surface in one state and ground found (RG211). */
export interface Scan {
  /** Every violation axe named, at any impact. */
  readonly findings: readonly Finding[]
  /** Every chosen option read beside a sibling, told apart or not. */
  readonly chosen: readonly ChosenVerdict[]
}

/**
 * Scan the page as it is drawn: axe at WCAG A and AA, then the chosen-state rule axe lacks.
 *
 * Axe is injected over the DevTools protocol by `AxeBuilder`, which the renderer's content
 * policy does not govern — the same reason every expression here reaches the page that way.
 *
 * **In legacy mode, and that was measured.** The builder's default finishes a run in a blank
 * page it opens beside the window, and Electron refuses `Target.createTarget`: every scan failed
 * with *not supported*. Legacy mode runs axe in the window's own frame, which is all a single
 * window with no iframes has.
 */
async function scanPage(page: Page, capture: Capture): Promise<Scan> {
  const result = await new AxeBuilder({ page })
    .withTags([...AXE_TAGS])
    .setLegacyMode(true)
    .analyze()
  const chosen = readingsFrom(await page.evaluate(CHOSEN_SCRIPT)).map((one) => judgeChosen(one))
  const named = capture.state === null ? capture.surface : `${capture.surface}.${capture.state}`
  return {
    findings: [
      ...findingsIn(result, named, capture.ground),
      ...chosenFindings(chosen, named, capture.ground),
    ],
    chosen,
  }
}

export interface Taking {
  /** Write the PNG. False for a scan-only run. */
  readonly picture: boolean
  /** Scan the page before it moves on (RG211). */
  readonly scan: boolean
}

/**
 * Take one capture: the width, the route, the state a session is put in, a settled document,
 * then the picture and the scan it was asked for — both of the page in that state.
 *
 * @returns whether the surface settled before the ceiling, and what a scan found. A surface
 *   that never settled is still photographed, and the index says so.
 */
export async function takeCapture(
  shot: ShotApp,
  capture: Capture,
  directory: string,
  taking: Taking = { picture: true, scan: false },
): Promise<{ readonly settled: boolean; readonly scan: Scan | null }> {
  const { page } = shot
  // Folded notes are a preference the stream reads at launch (RG208), so it is set and taken
  // back around the one capture that needs it.
  if (capture.state === 'folded') await prefer(shot, 'sessionNotes', 'hidden')
  try {
    await page.setViewportSize({ width: capture.width, height: capture.height })
    await page.evaluate(
      `location.hash = ${JSON.stringify(`#${capture.route}`)}; window.scrollTo(0, 0)`,
    )
    let settled = await settle(page)
    if (capture.state === 'scrolled') {
      await page.evaluate(SCROLL_STREAM_UP)
      settled = await settle(page)
    }
    if (capture.state === 'explain') {
      await page.evaluate(OPEN_EXPLAIN)
      await page.waitForSelector('[data-testid="explain-dialog"]', { timeout: SETTLE_CEILING_MS })
      await page.waitForTimeout(SHEET_OPENS_MS)
      settled = await settle(page)
    }
    if (opensViewer(capture.state)) {
      const named = VIEWER_FILES[capture.state ?? '']
      await page.evaluate(named === undefined ? OPEN_EDITED_FILE : openEdited(named))
      await page.waitForSelector('[data-testid="file-sheet"]', { timeout: SETTLE_CEILING_MS })
      await page.waitForTimeout(SHEET_OPENS_MS)
      settled = await settle(page)
    }

    if (taking.picture) {
      const file = path.join(directory, capture.file)
      try {
        await page.screenshot({ path: file, timeout: CAPTURE_TIMEOUT_MS })
      } catch {
        // Once more after the frames an emulated resize takes to land, which is the case
        // measured.
        await page.evaluate(TWO_FRAMES)
        await page.screenshot({ path: file, timeout: CAPTURE_TIMEOUT_MS })
      }
    }
    return { settled, scan: taking.scan ? await scanPage(page, capture) : null }
  } finally {
    if (capture.state === 'folded') await prefer(shot, 'sessionNotes', 'shown')
    // The viewer is the screen's own state and survives a hash set to the same route, so it is
    // closed as a reader closes it before the next capture draws the session without it.
    // Both are the screen's own state and survive a hash set to the same route, so each is
    // closed as a reader closes it before the next capture draws the surface without it.
    if (opensViewer(capture.state) || capture.state === 'explain') {
      await page.keyboard.press('Escape')
    }
  }
}

/** What the window says it is, for the index: the build every picture came from. */
export async function buildOf(shot: ShotApp): Promise<unknown> {
  const identity: unknown = await shot.page.evaluate('window.roadkeep.identify()')
  return typeof identity === 'object' && identity !== null && 'build' in identity
    ? identity.build
    : null
}
