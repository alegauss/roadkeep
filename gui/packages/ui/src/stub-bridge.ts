import type { RendererBridge } from '@rk/core'

/**
 * A bridge for a test, with every method the test did not name refusing as a closed channel.
 *
 * A test instrument and not shipped code — nothing in `main` imports it, as with `harness`.
 * Each test used to spell the whole bridge, so the method RG143 added broke fifteen stubs
 * that had never called one; a test names the methods its assertion is about, and a method
 * added to the bridge is added here once.
 *
 * Refusing rather than answering, because a default that answered would be a value no test
 * chose, and a test that reached one it did not name should fail saying so.
 */
export function stubBridge(over: Partial<RendererBridge> = {}): RendererBridge {
  const unasked = (): Promise<never> => Promise.reject(new Error('not asked'))
  return {
    identify: unasked,
    settings: unasked,
    saveTheme: unasked,
    saveLocale: unasked,
    projects: unasked,
    open: unasked,
    run: unasked,
    ...over,
  }
}
