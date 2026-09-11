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
import { contextBridge, ipcRenderer, type IpcRendererEvent } from 'electron'

import {
  BRIDGE_CHANNELS,
  BRIDGE_KEY,
  BRIDGE_TOPICS,
  BRIDGE_UNSUBSCRIBE,
  keyOfEvent,
  type RendererBridge,
  type TopicEvents,
} from '@rk/core'

const bridge: RendererBridge = {
  identify: () => ipcRenderer.invoke(BRIDGE_CHANNELS.identify),
  settings: () => ipcRenderer.invoke(BRIDGE_CHANNELS.settings),
  saveTheme: (theme) => ipcRenderer.invoke(BRIDGE_CHANNELS.saveTheme, theme),
  saveLocale: (locale) => ipcRenderer.invoke(BRIDGE_CHANNELS.saveLocale, locale),
  projects: () => ipcRenderer.invoke(BRIDGE_CHANNELS.projects),
  open: (root) => ipcRenderer.invoke(BRIDGE_CHANNELS.open, root),
  run: (root, request) => ipcRenderer.invoke(BRIDGE_CHANNELS.run, root, request),
  // A listener on the topic's one channel, keeping its own key's events, and main told so it
  // starts hearing that source (RG144). The answer takes both back, once: a screen's cleanup
  // and a second call from somewhere else are the same give-up.
  subscribe: (topic, key, listener) => {
    const channel = BRIDGE_TOPICS[topic]
    const heard = (_sent: IpcRendererEvent, event: TopicEvents[typeof topic]): void => {
      if (keyOfEvent(topic, event) === key) listener(event)
    }
    ipcRenderer.on(channel, heard)
    ipcRenderer.send(BRIDGE_CHANNELS.subscribe, topic, key)

    let given = false
    return () => {
      if (given) return
      given = true
      ipcRenderer.removeListener(channel, heard)
      ipcRenderer.send(BRIDGE_UNSUBSCRIBE, topic, key)
    }
  },
  roots: () => ipcRenderer.invoke(BRIDGE_CHANNELS.roots),
  chooseRoot: () => ipcRenderer.invoke(BRIDGE_CHANNELS.chooseRoot),
  saveRoots: (roots) => ipcRenderer.invoke(BRIDGE_CHANNELS.saveRoots, roots),
  handOver: (root, id) => ipcRenderer.invoke(BRIDGE_CHANNELS.handOver, root, id),
  sessions: () => ipcRenderer.invoke(BRIDGE_CHANNELS.sessions),
  stopSession: (key) => ipcRenderer.invoke(BRIDGE_CHANNELS.stopSession, key),
}

contextBridge.exposeInMainWorld(BRIDGE_KEY, Object.freeze(bridge))
