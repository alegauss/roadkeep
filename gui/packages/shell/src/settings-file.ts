import { mkdirSync, readFileSync, renameSync, writeFileSync } from 'node:fs'
import path from 'node:path'

import {
  DEFAULT_SETTINGS,
  readSettings,
  settingsText,
  type Settings,
  type SettingsRead,
} from '@rk/core'

/**
 * Where the settings file lives, and how it is written.
 *
 * The half that needs an operating system. `core` says what a settings file *is* — the
 * fields, the version, what a bad one recovers to — and this puts it somewhere and gets it
 * back.
 *
 * **A file that is not JSON is a different failure from one of the wrong shape**, and only
 * the second is `core`'s. This one is reported here, and both end the same way: defaults,
 * and a sentence saying so.
 *
 * **Written by rename.** A half-written settings file is the one that loses somebody's
 * roots, and a crash mid-write is exactly when it would happen. The temporary file is
 * beside the real one so the rename stays on one filesystem.
 */

/** The file, inside whatever directory the caller says is this app's. */
export const SETTINGS_FILE = 'settings.json'

export function settingsPath(userData: string): string {
  return path.join(userData, SETTINGS_FILE)
}

/**
 * Read the settings, or say what happened instead.
 *
 * A missing file is not a failure and says nothing: it is the first launch, which is the
 * ordinary way to arrive here.
 */
export function loadSettings(userData: string): SettingsRead {
  let text: string
  try {
    text = readFileSync(settingsPath(userData), 'utf8')
  } catch {
    return { settings: DEFAULT_SETTINGS, reset: [] }
  }

  let parsed: unknown
  try {
    parsed = JSON.parse(text)
  } catch {
    // Kept, not replaced: a file somebody hand-edited into invalidity is a file they may
    // want to fix, and overwriting it is how the fix becomes impossible.
    //
    // The one loss this side raises, and it is a code like the other nine rather than the
    // sentence it used to be (RG123): the notice is shown in whatever language the window
    // is speaking, and a process with no locale cannot compose one.
    return {
      settings: DEFAULT_SETTINGS,
      reset: [{ lost: 'unparsable', fields: { file: SETTINGS_FILE } }],
    }
  }

  return readSettings(parsed)
}

/**
 * Write the settings.
 *
 * Creates the directory if it is not there — a first launch has neither — and replaces the
 * file by rename so a crash cannot leave half of one.
 */
export function saveSettings(userData: string, settings: Settings): void {
  mkdirSync(userData, { recursive: true })
  const target = settingsPath(userData)
  const temporary = `${target}.writing`
  writeFileSync(temporary, settingsText(settings), 'utf8')
  renameSync(temporary, target)
}
