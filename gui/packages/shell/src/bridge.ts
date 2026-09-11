import {
  BRIDGE_CHANNELS,
  isTheme,
  LOCALE_TAGS,
  requestFrom,
  withheldResult,
  type BridgedResult,
  type BridgeIdentity,
  type LaunchSettings,
  type OpenedProject,
} from '@rk/core'
import { app, ipcMain } from 'electron'

import { createCarrier, type Carrier } from './carrier'
import { localeChoice } from './locale'
import { loadSettings, saveSettings } from './settings-file'
import { readStamp } from './stamp'

/**
 * The main-process end of the renderer's one channel. Every handler registered here is a
 * power the renderer gains, so the list is meant to stay short and to stay readable in one
 * screen: what this file handles is exactly what a compromised renderer can reach. Since
 * RG143 that includes the engine, bounded by what `carrier.ts` refuses.
 *
 * The build is read once, as the bridge is registered. It cannot change while the app runs,
 * and reading a file on every call would be a file read a renderer gets to ask for.
 */
export interface BridgeHooks {
  /** Called once a language is saved, so what this process draws itself can follow (RG50). */
  readonly localeSaved?: () => void
}

/**
 * Register every handler, and hand back the carrier behind the three that reach an engine —
 * the one thing registered here that holds processes, and so the one thing quitting awaits.
 */
export function registerBridge(hooks: BridgeHooks = {}): Carrier {
  const build = readStamp(import.meta.dirname, app.isPackaged)

  ipcMain.handle(BRIDGE_CHANNELS.identify, (): BridgeIdentity => ({ transport: 'ipc', build }))

  // The settings, unlike the build, are read per call: the file is documented as one a
  // person may edit by hand, and a copy taken at startup is one only a restart refreshes.
  // The path read is this app's own settings file and never one the renderer names, which
  // is what keeps a handler that touches the filesystem off the list of powers it gains.
  ipcMain.handle(BRIDGE_CHANNELS.settings, (): LaunchSettings => {
    const read = loadSettings(app.getPath('userData'))
    return { ...read, locale: localeChoice(read.settings.locale, app.getLocale()) }
  })

  // The one write the renderer can ask for, and it reaches exactly one field. The file is
  // re-read rather than remembered so a root somebody added by hand a moment ago survives
  // a click on the ground switch, and the value is checked here because a channel argument
  // is the renderer's word: `isTheme` is the same set the reader uses, so nothing gets in
  // that a later read would reset.
  ipcMain.handle(BRIDGE_CHANNELS.saveTheme, (_event, theme: unknown): void => {
    if (!isTheme(theme)) return
    const userData = app.getPath('userData')
    saveSettings(userData, { ...loadSettings(userData).settings, theme })
  })

  // The same shape for the language (RG116), and the same reason for checking here: a tag
  // is the renderer's word, and one this build does not ship reads back as English at the
  // next launch — which looks like the setting was never saved.
  ipcMain.handle(BRIDGE_CHANNELS.saveLocale, (_event, locale: unknown): void => {
    if (typeof locale !== 'string' || !LOCALE_TAGS.includes(locale)) return
    const userData = app.getPath('userData')
    saveSettings(userData, { ...loadSettings(userData).settings, locale })
    hooks.localeSaved?.()
  })

  // The three that reach an engine (RG143). Where to look is read per call, like the
  // settings above, so a root somebody added by hand is scanned the next time the window
  // asks. Every argument is still the renderer's word: a root that is not a string opens
  // nothing, and a request that is not one runs nothing — both before the carrier is asked.
  const carrier = createCarrier({
    looking: () => {
      const { roots, skip, width } = loadSettings(app.getPath('userData')).settings
      return { roots, skip, width }
    },
  })

  ipcMain.handle(BRIDGE_CHANNELS.projects, () => carrier.projects())

  ipcMain.handle(BRIDGE_CHANNELS.open, (_event, root: unknown): Promise<OpenedProject> => {
    if (typeof root !== 'string') {
      return Promise.resolve({ kind: 'withheld', root: '', reason: 'no root was named' })
    }
    return carrier.open(root)
  })

  ipcMain.handle(
    BRIDGE_CHANNELS.run,
    (_event, root: unknown, request: unknown): Promise<BridgedResult> => {
      const asked = requestFrom(request)
      if (typeof root !== 'string' || asked === null) {
        return Promise.resolve(withheldResult('the request is not one this bridge carries'))
      }
      return carrier.run(root, asked)
    },
  )

  return carrier
}
