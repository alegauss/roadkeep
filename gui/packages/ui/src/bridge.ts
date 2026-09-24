import type { RendererBridge } from '@rk/core'

/**
 * The renderer's whole view of the outside. `window.roadkeep` is optional and has to stay
 * optional: it is absent in a test, absent in a plain browser tab, and absent for the
 * moment between the page loading and a future transport connecting. Code that assumes it
 * is there is code that only runs under Electron, which is the coupling this seam exists
 * to prevent.
 */
declare global {
  interface Window {
    readonly roadkeep?: RendererBridge
  }
}

export function getBridge(): RendererBridge | undefined {
  return window.roadkeep
}
