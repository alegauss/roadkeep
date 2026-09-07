import { BRIDGE_CHANNELS, type BridgeIdentity } from '@rk/core'
import { ipcMain } from 'electron'

/**
 * The main-process end of the renderer's one channel. Every handler registered here is a
 * power the renderer gains, so the list is meant to stay short and to stay readable in one
 * screen: what this file handles is exactly what a compromised renderer can reach.
 */
export function registerBridge(): void {
  ipcMain.handle(BRIDGE_CHANNELS.identify, (): BridgeIdentity => ({ transport: 'ipc' }))
}
