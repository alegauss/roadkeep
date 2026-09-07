/**
 * The one way anything reaches the renderer, and the reason the web port is a transport
 * swap rather than a rewrite.
 *
 * The renderer is given exactly one object on `window`, and this file is its type. Under
 * Electron a preload fills it in over IPC; served from a web server the same object would
 * be filled in over HTTP, and the React above it cannot tell, because nothing in front of
 * this interface names a process, a channel or a path. `identify` is what makes that
 * checkable instead of asserted: the renderer can ask which transport answered without
 * knowing how to reach any other one.
 *
 * Widening this interface is the one change that can quietly cost the port, so a method
 * added here is a method a web transport has to be able to implement.
 */

/** The single property the preload adds to `window`. */
export const BRIDGE_KEY = 'roadkeep'

/** What is carrying the calls. A packaged desktop build is always `ipc`. */
export type TransportName = 'ipc' | 'http'

export interface BridgeIdentity {
  readonly transport: TransportName
}

export interface RendererBridge {
  identify(): Promise<BridgeIdentity>
}

/**
 * The IPC channel behind each method. Named here rather than in the preload so that the
 * two ends cannot drift: main handles what this says, the preload invokes what this says.
 */
export const BRIDGE_CHANNELS = {
  identify: 'roadkeep:identify',
} as const satisfies Record<keyof RendererBridge, string>
