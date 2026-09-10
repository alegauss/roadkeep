// The only code that runs on both sides of the isolation boundary, and therefore the
// only file where a mistake hands the renderer something a browser would not have.
//
// It exposes one frozen object built from `core`'s interface and nothing else: no
// `ipcRenderer`, no module, no path. `contextBridge` copies values across, so the renderer
// receives a structured clone and never a live reference into this context.
//
// This file is bundled to CommonJS by `vite.preload.config.ts` because the preload runs
// sandboxed, where `require` reaches Electron's own modules and nothing else — an import
// of `core` has to already be inside the file by the time Electron loads it.
import { contextBridge, ipcRenderer } from 'electron'

import { BRIDGE_CHANNELS, BRIDGE_KEY, type RendererBridge } from '@rk/core'

const bridge: RendererBridge = {
  identify: () => ipcRenderer.invoke(BRIDGE_CHANNELS.identify),
  settings: () => ipcRenderer.invoke(BRIDGE_CHANNELS.settings),
  saveTheme: (theme) => ipcRenderer.invoke(BRIDGE_CHANNELS.saveTheme, theme),
  saveLocale: (locale) => ipcRenderer.invoke(BRIDGE_CHANNELS.saveLocale, locale),
}

contextBridge.exposeInMainWorld(BRIDGE_KEY, Object.freeze(bridge))
