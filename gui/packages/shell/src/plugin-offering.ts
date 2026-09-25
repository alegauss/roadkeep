import { translator, wordingFor } from '@rk/core'
import { app, BrowserWindow, dialog } from 'electron'

import { exitOf } from './exit-code'
import { localeChoice } from './locale'
import { offerPlugin, type OfferDialog } from './plugin-offer'
import { loadSettings } from './settings-file'

/**
 * The effects `plugin-offer.ts` is handed (RK1700): Electron's dialog and a spawn.
 *
 * Its own file for `menu.ts`'s reason — the decision is data and tested without Electron, and
 * this is the part that needs a running app. Called once the first window exists, so the
 * question is asked over the app it is about rather than before anything is on screen.
 */
export function offerPluginOnFirstLaunch(): void {
  const userData = app.getPath('userData')
  const settings = loadSettings(userData).settings
  const tag = localeChoice(settings.locale, app.getLocale())
  void offerPlugin({
    platform: process.platform,
    packaged: app.isPackaged,
    userData,
    say: translator(wordingFor(tag), tag),
    run: exitOf,
    show,
  }).catch(() => {
    // Nothing here may take the app down: the reader works without the plugin, and a desktop
    // that refused a dialog has left nothing on screen to say so with.
  })
}

async function show(shown: OfferDialog): Promise<number> {
  const options = {
    type: 'question' as const,
    title: shown.title,
    message: shown.message,
    buttons: [...shown.buttons],
    defaultId: 0,
    cancelId: shown.buttons.length - 1,
    noLink: true,
  }
  const parent = BrowserWindow.getAllWindows()[0]
  const answer =
    parent === undefined
      ? await dialog.showMessageBox(options)
      : await dialog.showMessageBox(parent, options)
  return answer.response
}
