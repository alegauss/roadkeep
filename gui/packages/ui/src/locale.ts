import { BASE_LOCALE, type RendererBridge } from '@rk/core'

import { getBridge } from './bridge'

/**
 * Which language this window opens in, asked once before anything is drawn.
 *
 * **Asked before the first mount, not after it.** A hook would render the whole window in
 * English and replace every sentence a moment later, and a window that rewrites itself once
 * per launch is worse than one that waits a round trip — which, over IPC, is shorter than
 * the frame Electron is already holding the window back for.
 *
 * **Every failure is English.** No bridge is a plain browser tab; a rejection is a channel
 * that is not there. Neither is a reason to show nothing, because the base is a complete
 * catalogue and not a fallback of last resort.
 */
export async function localeFromBridge(bridge: RendererBridge | undefined): Promise<string> {
  if (!bridge) return BASE_LOCALE

  try {
    return (await bridge.settings()).locale
  } catch {
    return BASE_LOCALE
  }
}

/** The same question, of whatever bridge this page was given. */
export function localeAtLaunch(): Promise<string> {
  return localeFromBridge(getBridge())
}
