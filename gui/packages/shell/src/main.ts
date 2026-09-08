import { app, BrowserWindow } from 'electron'

import { registerBridge } from './bridge'
import { attachDefaultPolicy } from './content-policy'
import { guardNavigation } from './guard'
import { appUrl, createWindow } from './window'

/**
 * The Electron entry point. It owns the window's lifetime, the one channel the renderer
 * is given and the policy every renderer is held to — and nothing else. No governed file
 * is read here and no process is spawned: that call path is its own task.
 *
 * The guard is installed before the first window exists, because it works by watching for
 * renderers being created and cannot retroactively cover one that already is.
 */
guardNavigation(appUrl())

void app.whenReady().then(() => {
  // Before the first window: the policy hangs off the session, and a response that arrived
  // before it was attached is a response nobody held to it.
  attachDefaultPolicy()
  registerBridge()
  createWindow()

  // macOS keeps the process alive with no windows, so the dock icon has to be able
  // to make one again.
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    }
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})
