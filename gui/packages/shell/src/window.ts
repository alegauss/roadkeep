import path from 'node:path'

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

export function createWindow(): BrowserWindow {
  const window = new BrowserWindow({
    width: 1280,
    height: 820,
    minWidth: 900,
    minHeight: 600,
    backgroundColor: '#0a0a0a',
    // The window is shown by the `ready-to-show` handler below rather than at
    // construction, so the first frame a person sees is painted and not white.
    show: false,
    title: 'roadkeep',
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
