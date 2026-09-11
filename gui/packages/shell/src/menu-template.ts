import { saidOfUpdate, type Translate, type UpdateCheck } from '@rk/core'
import type { MenuItemConstructorOptions } from 'electron'

import { isReleasePage } from './updates'

/**
 * The application menu and the update dialog, as data (RG50).
 *
 * Kept apart from `menu.ts` so what they promise is tested without an Electron process:
 * the menu is the platform's own with Help replaced by the one item this app adds, the check
 * runs only when that item is clicked, and the dialog opens a release page and nothing else.
 */

/**
 * The menu, built from roles so copy, paste, reload and the rest keep the platform's keys and
 * words. Help is the only menu written here, because Electron's own links to its website are
 * the one part of the default that says something untrue about who made this app.
 */
export function menuTemplate(
  say: Translate,
  onCheck: () => void,
  platform: NodeJS.Platform = process.platform,
): MenuItemConstructorOptions[] {
  return [
    ...(platform === 'darwin' ? [{ role: 'appMenu' } as const] : []),
    { role: 'fileMenu' },
    { role: 'editMenu' },
    { role: 'viewMenu' },
    { role: 'windowMenu' },
    {
      label: say('menu.help'),
      role: 'help',
      // The only way the check runs: nothing asks GitHub anything on launch, because this app
      // reads a person's repositories and a call it did not need is one it has to explain.
      submenu: [{ label: say('update.check'), click: () => onCheck() }],
    },
  ]
}

/** What the dialog shows, and the page its first button opens where there is one. */
export interface UpdateDialog {
  readonly title: string
  readonly message: string
  readonly buttons: readonly string[]
  readonly opens: string | null
}

export function dialogOf(check: UpdateCheck, say: Translate): UpdateDialog {
  const said = saidOfUpdate(check)
  // Offered only where it is one of this project's release pages: the URL came off a network
  // answer, and a dialog that opened whatever it was handed is a link nobody chose.
  const opens = said.opens !== null && isReleasePage(said.opens) ? said.opens : null
  return {
    title: say('update.title'),
    // The half this app wrote goes through the catalogue; the half the network wrote is
    // already in the fill, quoted as it arrived (RG172).
    message: say(said.key, {
      ...said.fill,
      ...(said.because === null ? {} : { reason: say(said.because.key, said.because.fill) }),
    }),
    buttons: opens === null ? [say('update.close')] : [say('update.open'), say('update.close')],
    opens,
  }
}

export interface AskingForUpdate {
  readonly current: string
  readonly say: Translate
  readonly check: (current: string) => Promise<UpdateCheck>
  /** Show the dialog and answer which button was chosen, by index. */
  readonly show: (dialog: UpdateDialog) => Promise<number>
  readonly open: (url: string) => Promise<void>
}

/**
 * A click on the menu item, from the request to the page — and never further. Nothing is
 * downloaded or installed: the most this does is hand a release page to the browser, and
 * only when the person picked the button that says so.
 */
export async function askForUpdate(asking: AskingForUpdate): Promise<void> {
  const shown = dialogOf(await asking.check(asking.current), asking.say)
  const chosen = await asking.show(shown)
  if (shown.opens !== null && chosen === 0) await asking.open(shown.opens)
}
