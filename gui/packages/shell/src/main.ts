import { app, BrowserWindow } from 'electron'

import { createWindow } from './window.js'

/**
 * The Electron entry point. It owns the window's lifetime and nothing else: no read
 * of a governed file, no spawn and no IPC channel, because each of those is a task
 * of its own and the scaffold's whole claim is that a window opens.
 */
void app.whenReady().then(() => {
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
