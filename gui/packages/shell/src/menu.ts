import { translator, wordingFor } from '@rk/core'
import { app, BrowserWindow, dialog, Menu, shell as desktop } from 'electron'

import { localeChoice } from './locale'
import { askForUpdate, menuTemplate, type UpdateDialog } from './menu-template'
import { loadSettings } from './settings-file'
import { readStamp } from './stamp'
import { checkForUpdate } from './updates'

/**
 * Put the application menu in place, in the language the window speaks (RG50).
 *
 * Called at launch and again whenever the language is saved, so the menu never speaks one
 * language while the window speaks another. The words are the catalogue's, looked up here
 * because the menu belongs to this process and never crosses the bridge.
 */
export function installMenu(): void {
  const settings = loadSettings(app.getPath('userData')).settings
  const say = translator(wordingFor(localeChoice(settings.locale, app.getLocale())))
  const current = readStamp(import.meta.dirname, app.isPackaged).version

  const ask = (): void => {
    void askForUpdate({ current, say, check: checkForUpdate, show, open }).catch(() => {
      // The check itself never throws — every failure is a sentence in the dialog. What can
      // is the desktop refusing to show a dialog or to open a browser, and there is nothing
      // left on screen to say that with.
    })
  }

  Menu.setApplicationMenu(Menu.buildFromTemplate(menuTemplate(say, ask)))
}

async function show(shown: UpdateDialog): Promise<number> {
  const options = {
    type: 'info' as const,
    title: shown.title,
    message: shown.message,
    buttons: [...shown.buttons],
    defaultId: 0,
    cancelId: shown.buttons.length - 1,
    noLink: true,
  }
  const parent = BrowserWindow.getFocusedWindow()
  const answer =
    parent === null
      ? await dialog.showMessageBox(options)
      : await dialog.showMessageBox(parent, options)
  return answer.response
}

function open(url: string): Promise<void> {
  return desktop.openExternal(url)
}
