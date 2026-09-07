import type { EngineRequest, EngineResult, Transport } from './transport'

/**
 * A read, remembered only for as long as the files it came off have not moved.
 *
 * One call measures around 360 ms, and a portfolio screen over twenty projects pays twenty
 * of them to redraw. Nothing about that is fixable inside the engine, so what is fixable
 * is asking it fewer times.
 *
 * **What keys an answer is the project root, the argv, and a stamp of the governed files
 * that project declares.** Anything else is a guess: a timer expires an answer that is
 * still good and keeps one that is not, and a count of writes this app made misses every
 * write a terminal or an agent made beside it.
 *
 * **Nothing persists across launches.** The non-goals refuse a store, and a cache that
 * survived a restart would be one that can be wrong about a repository somebody edited
 * while the app was closed. That is structural here rather than a promise: this package
 * has no filesystem in scope at all, which its own boundary test enforces.
 *
 * It is a transport and not a layer above one, so nothing that reads knows it exists — the
 * same reason the transport is one interface with one method.
 */

export interface CachingOptions {
  /**
   * A short string that changes when the project's governed files do. Same stamp means the
   * remembered answer is still the answer. Computing one needs a filesystem, so it belongs
   * to whoever has one.
   */
  stampFor(root: string): Promise<string>
  /**
   * Whether this call's answer may be remembered at all. There is no default that caches:
   * a write cached is a write that appears to have happened twice, and which verbs write
   * is the engine's answer rather than a list kept here.
   */
  cacheable(argv: readonly string[]): boolean
  /** How many answers to keep. Least recently used goes first. */
  max?: number
}

export interface CachingTransport extends Transport {
  /** Forget everything about one project. What a file watcher calls. */
  invalidate(root: string): void
  clear(): void
  readonly size: number
}

interface Entry {
  readonly stamp: string
  readonly result: EngineResult
}

/**
 * NUL is the separator because it is the one character neither a path nor a command-line
 * argument can contain. A space would make `{root: '/a b', argv: ['c']}` and
 * `{root: '/a', argv: ['b', 'c']}` the same entry, which is a wrong answer served quickly.
 * Written as an escape rather than typed: a raw NUL in source is invisible to every reader.
 */
const SEPARATOR = '\u0000'

/** Root and argv, joined into the one string that identifies this exact call. */
function keyOf(request: EngineRequest): string {
  return [request.root, ...request.argv].join(SEPARATOR)
}

export function createCachingTransport(
  inner: Transport,
  options: CachingOptions,
): CachingTransport {
  const max = options.max ?? 200
  const entries = new Map<string, Entry>()

  return {
    async run(request: EngineRequest): Promise<EngineResult> {
      if (!options.cacheable(request.argv)) {
        return inner.run(request)
      }

      const key = keyOf(request)
      const stamp = await options.stampFor(request.root)

      const held = entries.get(key)
      if (held !== undefined && held.stamp === stamp) {
        // Re-insert so the most recently used is last, which is what makes eviction LRU
        // rather than insertion-ordered.
        entries.delete(key)
        entries.set(key, held)
        return held.result
      }

      // A call that throws is a call that did not happen — unspawnable, timed out or
      // cancelled — and remembering it would make one bad moment permanent.
      const result = await inner.run(request)

      entries.set(key, { stamp, result })
      while (entries.size > max) {
        const oldest = entries.keys().next()
        if (oldest.done === true) break
        entries.delete(oldest.value)
      }
      return result
    },

    invalidate(root: string): void {
      const prefix = `${root}${SEPARATOR}`
      for (const key of [...entries.keys()]) {
        if (key.startsWith(prefix)) entries.delete(key)
      }
    },

    clear(): void {
      entries.clear()
    },

    get size(): number {
      return entries.size
    },
  }
}
