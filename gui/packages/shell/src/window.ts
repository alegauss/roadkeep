import path from 'node:path'
import { pathToFileURL } from 'node:url'

import { BrowserWindow } from 'electron'

/**
 * Where the renderer comes from, and it is one of exactly two places. In development
 * the dev script starts Vite and hands the URL down in this variable, so the window
 * loads over HTTP and hot-reloads. With the variable unset the window loads the built
 * bundle off disk, which is what a packaged app does.
 */
export const RENDERER_URL_VAR = 'ROADKEEP_GUI_RENDERER_URL'

/** The built renderer, relative to this file once compiled into `shell/dist`. */
const BUILT_RENDERER = path.join(import.meta.dirname, '..', '..', 'ui', 'dist', 'index.html')

/**
 * The preload, as Vite bundles it: CommonJS, because the sandbox the window runs under
 * gives a preload Electron's own `require` and no other.
 */
const PRELOAD = path.join(import.meta.dirname, 'preload.cjs')

/** Where the app itself lives, which is what every navigation is reviewed against. */
export function appUrl(): string {
  return process.env[RENDERER_URL_VAR] ?? pathToFileURL(BUILT_RENDERER).href
}

export function createWindow(): BrowserWindow {
  const window = new BrowserWindow({
    width: 1280,
    height: 820,
    minWidth: 900,
    minHeight: 600,
    // The only colour this repository spells, and it is not a design decision: Electron
    // paints it before the renderer exists and during a resize, so it has to be a literal
    // and cannot read a CSS token. It matches the design system's light ground because
    // that is the only ground the app currently has - RG52, which wires the switch, is
    // what makes this follow the theme instead of guessing it.
    backgroundColor: '#ffffff',
    // The window is shown by the `ready-to-show` handler below rather than at
    // construction, so the first frame a person sees is painted and not white.
    show: false,
    title: 'roadkeep',
    webPreferences: {
      // Every one of these is Electron's default. They are written out anyway: a default
      // is a thing a later edit can turn off without the diff looking like it took
      // anything away, and this list is the difference between a renderer that is a
      // browser and one that can delete a file.
      contextIsolation: true,
      nodeIntegration: false,
      nodeIntegrationInWorker: false,
      sandbox: true,
      webSecurity: true,
      // Not a default. A `<webview>` is a second renderer with its own preferences, and
      // this app has no use for one.
      webviewTag: false,
      preload: PRELOAD,
    },
  })

  window.once('ready-to-show', () => {
    window.show()
  })

  const devServer = process.env[RENDERER_URL_VAR]
  if (devServer) {
    void window.loadURL(devServer)
  } else {
    void window.loadFile(BUILT_RENDERER)
  }

  return window
}
