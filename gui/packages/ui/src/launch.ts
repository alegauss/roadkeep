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

export async function choicesFromBridge(
  bridge: RendererBridge | undefined,
): Promise<LaunchChoices> {
  if (!bridge) return AT_WORST

  try {
    const answer = await bridge.settings()
    return { locale: answer.locale, theme: answer.settings.theme }
  } catch {
    return AT_WORST
  }
}

/** The same question, of whatever bridge this page was given. */
export function choicesAtLaunch(): Promise<LaunchChoices> {
  return choicesFromBridge(getBridge())
}
