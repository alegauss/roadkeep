/**
 * The one way anything reaches the renderer, and the reason the web port is a transport
 * swap rather than a rewrite.
 *
 * The renderer is given exactly one object on `window`, and this file is its type. Under
 * Electron a preload fills it in over IPC; served from a web server the same object would
 * be filled in over HTTP, and the React above it cannot tell, because nothing in front of
 * this interface names a process, a channel or a path. `identify` is what makes that
 * checkable instead of asserted: the renderer can ask which transport answered without
 * knowing how to reach any other one.
 *
 * Widening this interface is the one change that can quietly cost the port, so a method
 * added here is a method a web transport has to be able to implement.
 */

import type { BuildIdentity } from './build'
import type { SettingsRead, Theme } from './settings'

/** The single property the preload adds to `window`. */
export const BRIDGE_KEY = 'roadkeep'

/** What is carrying the calls. A packaged desktop build is always `ipc`. */
export type TransportName = 'ipc' | 'http'

export interface BridgeIdentity {
  readonly transport: TransportName
  /**
   * What this build is, so a defect report carries it and an about surface can show it.
   *
   * It rides on `identify` rather than arriving as a method of its own: widening the
   * method set is the change that costs the port, and a web transport answering "which
   * build am I" is answering the same question this already asks.
   */
  readonly build: BuildIdentity
}

/**
 * What the shell holds, as the renderer receives it.
 *
 * The settings themselves plus what reading them lost, which is `SettingsRead` unchanged —
 * and one field the renderer could not work out for itself.
 */
export interface LaunchSettings extends SettingsRead {
  /**
   * Which of the locales this build ships the window is speaking, already chosen.
   *
   * Resolved on the shell's side because `Settings.locale` may be empty, and empty means
   * *whatever the desktop says* — a question only a process can ask. What crosses is the
   * answer, so the renderer never has two ideas of what language it is in.
   */
  readonly locale: string
}

export interface RendererBridge {
  identify(): Promise<BridgeIdentity>
  /**
   * A method of its own rather than another field on `identify`, and the line between them
   * is whether the answer can change while the app runs. A build cannot; a settings file is
   * a person's to edit, and one asked for once is one a restart is the only way to reread.
   */
  settings(): Promise<LaunchSettings>
  /**
   * Keep the ground somebody just chose, which is what makes the file the source of it.
   *
   * The switch persists to browser storage on its own, and that copy is a cache: it is read
   * before React runs so the first frame is not the wrong colour. A cache nothing refreshes
   * is a second answer, so the choice comes back through here and the file wins at the next
   * launch.
   *
   * **One field and not a settings patch.** A method that took `Partial<Settings>` would
   * hand the renderer the roots and the ignore list as well, and the screen that needs those
   * does not exist yet — widening this is a decision that belongs to whoever builds it.
   */
  saveTheme(theme: Theme): Promise<void>
}

/**
 * The IPC channel behind each method. Named here rather than in the preload so that the
 * two ends cannot drift: main handles what this says, the preload invokes what this says.
 */
export const BRIDGE_CHANNELS = {
  identify: 'roadkeep:identify',
  settings: 'roadkeep:settings',
  saveTheme: 'roadkeep:save-theme',
} as const satisfies Record<keyof RendererBridge, string>
