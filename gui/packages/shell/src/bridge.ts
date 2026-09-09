import { BRIDGE_CHANNELS, type BridgeIdentity, type LaunchSettings } from '@rk/core'
import { app, ipcMain } from 'electron'

import { localeChoice } from './locale'
import { loadSettings } from './settings-file'
import { readStamp } from './stamp'

/**
 * The main-process end of the renderer's one channel. Every handler registered here is a
 * power the renderer gains, so the list is meant to stay short and to stay readable in one
 * screen: what this file handles is exactly what a compromised renderer can reach.
 *
 * The build is read once, as the bridge is registered. It cannot change while the app runs,
 * and reading a file on every call would be a file read a renderer gets to ask for.
 */
export function registerBridge(): void {
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
}
