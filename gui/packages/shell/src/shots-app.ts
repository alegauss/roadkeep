import path from 'node:path'
import { setTimeout as after } from 'node:timers/promises'

import { _electron, type ElectronApplication, type Page } from 'playwright-core'

import { electronPath, launchEnv, shellRoot } from './launch'
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
async function drawn(page: Page): Promise<void> {
  await page.waitForSelector('#root > *', { state: 'attached' })
}

/** Start the built app on a profile somebody seeded, and wait for it to draw. */
export async function launchForShots(userData: string): Promise<ShotApp> {
  const app = await _electron.launch({
    executablePath: electronPath,
    // The switch before the app path, which is how `spawnElectron` orders them too.
    args: [`--user-data-dir=${userData}`, shellRoot],
    env: launchEnv(),
  })
  const page = await app.firstWindow()
  await drawn(page)

  // Taken now: once the app is gone Playwright's handle is disposed, and asking it for the
  // process then throws rather than answering.
  const child = app.process()
  const exited = () => child.exitCode !== null || child.signalCode !== null

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
      if (!exited()) child.kill()
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
 * Take one picture: the width, the route, a settled document, the capture.
 *
 * @returns whether the surface settled before the ceiling. A surface that never did is still
 *   photographed, and the index says so.
 */
export async function takeCapture(
  shot: ShotApp,
  capture: Capture,
  directory: string,
): Promise<boolean> {
  const { page } = shot
  await page.setViewportSize({ width: capture.width, height: capture.height })
  await page.evaluate(
    `location.hash = ${JSON.stringify(`#${capture.route}`)}; window.scrollTo(0, 0)`,
  )
  await page.evaluate(TWO_FRAMES)
  const settled = (await page.evaluate(settleScript(QUIET_MS, SETTLE_CEILING_MS))) === true

  const file = path.join(directory, capture.file)
  try {
    await page.screenshot({ path: file, timeout: CAPTURE_TIMEOUT_MS })
  } catch {
    // Once more after the frames an emulated resize takes to land, which is the case measured.
    await page.evaluate(TWO_FRAMES)
    await page.screenshot({ path: file, timeout: CAPTURE_TIMEOUT_MS })
  }
  return settled
}

/** What the window says it is, for the index: the build every picture came from. */
export async function buildOf(shot: ShotApp): Promise<unknown> {
  const identity: unknown = await shot.page.evaluate('window.roadkeep.identify()')
  return typeof identity === 'object' && identity !== null && 'build' in identity
    ? identity.build
    : null
}
