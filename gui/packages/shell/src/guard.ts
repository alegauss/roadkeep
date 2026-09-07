import { app, shell as desktop, type WebContents } from 'electron'

import { reviewNavigation, reviewWindowOpen } from './navigation'

/**
 * Apply the navigation policy to every renderer this app ever creates.
 *
 * It hangs off `web-contents-created` rather than off the window, because a guard attached
 * to the one window it was written for is a guard the second window does not have — and
 * the second window is exactly the one somebody else asked for.
 *
 * The remote module needs no switch here: Electron removed it, so there is nothing left to
 * turn off. Nothing replaced it either, and this bridge is what stands in its place.
 *
 * @param appUrl where the app itself was loaded from.
 */
export function guardNavigation(appUrl: string): void {
  app.on('web-contents-created', (_event, contents) => {
    guardContents(contents, appUrl)
  })
}

function guardContents(contents: WebContents, appUrl: string): void {
  contents.on('will-navigate', (event, target) => {
    const decision = reviewNavigation(target, appUrl)
    if (decision === 'allow') {
      return
    }
    event.preventDefault()
    if (decision === 'open-externally') {
      void desktop.openExternal(target)
    }
  })

  contents.setWindowOpenHandler(({ url }) => {
    if (reviewWindowOpen(url) === 'open-externally') {
      void desktop.openExternal(url)
    }
    // Always. A window Electron opened is a window carrying the preload.
    return { action: 'deny' }
  })

  // A frame that has already committed cannot be un-navigated, so an attach here is the
  // last line rather than the first: it catches a redirect no `will-navigate` saw.
  contents.on('will-attach-webview', (event) => {
    event.preventDefault()
  })
}
