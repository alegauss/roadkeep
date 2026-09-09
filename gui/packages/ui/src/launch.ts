import { BASE_LOCALE, type RendererBridge, type Theme } from '@rk/core'

import { getBridge } from './bridge'

/**
 * What this window opens as, asked once before anything is drawn.
 *
 * **Asked before the first mount, not after it.** A hook would render the whole window in
 * English on the wrong ground and replace both a moment later, and a window that rewrites
 * itself once per launch is worse than one that waits a round trip — which, over IPC, is
 * shorter than the frame Electron is already holding the window back for.
 *
 * **One call for both.** The language and the ground live in one settings file and arrive
 * in one answer, so asking twice would be two round trips and two moments at which the
 * window could be half-configured.
 *
 * **Every failure is the default.** No bridge is a plain browser tab; a rejection is a
 * channel that is not there. Neither is a reason to show nothing, because the base
 * catalogue is complete and following the desktop is a real answer and not a fallback of
 * last resort.
 *
 * **And an answer that never comes is a failure like the others** (RG106). A promise that
 * neither resolves nor rejects is one React is never told about, and Electron shows the
 * window on the first paint of an empty page — so the window arrives sized, titled and
 * holding nothing. A handler that throws rejects; a main process wedged in a synchronous
 * read settles the channel not at all, and reading the settings file is a synchronous read.
 *
 * **A deadline and not a retry.** Asking again would wait twice on the thing that is not
 * answering. Mounting in English is the answer already given for no bridge and for a
 * refusal, and it is a correct window rather than a degraded one.
 */
export interface LaunchChoices {
  /** A tag this build ships, already resolved against the desktop by the shell. */
  readonly locale: string
  /**
   * The setting as the file holds it — `system` is a choice and not an absence — or `null`
   * where nothing answered.
   *
   * The two are not the same and the ground is the one setting where the difference shows.
   * A page with no bridge has no file to be the source of it, and the copy the browser
   * already holds is then the only record of what somebody chose: handing `system` in as
   * though a file had said so would overwrite that on every reload.
   */
  readonly theme: Theme | null
}

const AT_WORST: LaunchChoices = { locale: BASE_LOCALE, theme: null }

/**
 * How long the first frame waits on the shell.
 *
 * An ordinary answer is one IPC round trip and one small file, which `running-app-live`
 * measures in single-digit milliseconds — so this is three orders of magnitude of room, and
 * a launch that loses its locale to the deadline is a launch where something is wrong. Short
 * enough, at two seconds, that a person reads a hang as a hesitation rather than as a window
 * that opened empty and stayed that way.
 */
export const LAUNCH_CEILING_MS = 2000

export async function choicesFromBridge(
  bridge: RendererBridge | undefined,
  ceilingMs: number = LAUNCH_CEILING_MS,
): Promise<LaunchChoices> {
  if (!bridge) return AT_WORST

  // The timer is cleared either way: a deadline that outlives its answer keeps the process
  // awake for two seconds after the window is already drawn.
  let timer: ReturnType<typeof setTimeout> | undefined
  const deadline = new Promise<LaunchChoices>((settle) => {
    timer = setTimeout(() => {
      settle(AT_WORST)
    }, ceilingMs)
  })

  try {
    return await Promise.race([
      bridge.settings().then((answer) => ({
        locale: answer.locale,
        theme: answer.settings.theme,
      })),
      deadline,
    ])
  } catch {
    return AT_WORST
  } finally {
    clearTimeout(timer)
  }
}

/** The same question, of whatever bridge this page was given. */
export function choicesAtLaunch(): Promise<LaunchChoices> {
  return choicesFromBridge(getBridge())
}
