import { describe, expect, it, vi } from 'vitest'

import { createCachingTransport } from './cache'
import { EngineCallFailed, type EngineResult, type Transport } from './transport'

function counting(answer = 'first'): { transport: Transport; calls: () => number } {
  let calls = 0
  return {
    calls: () => calls,
    transport: {
      run(): Promise<EngineResult> {
        calls += 1
        return Promise.resolve({
          code: 0,
          stdout: `${answer}:${String(calls)}`,
          stderr: '',
          durationMs: 1,
        })
      },
    },
  }
}

/** A machine whose stamp the test moves by hand. */
function stamps(initial = 'a') {
  let stamp = initial
  return {
    move: (next: string) => {
      stamp = next
    },
    stampFor: () => Promise.resolve(stamp),
  }
}

const always = () => true

describe('RG7: what a remembered answer is keyed on', () => {
  it('answers a repeat without asking the engine again', async () => {
    const { transport, calls } = counting()
    const cache = createCachingTransport(transport, {
      stampFor: stamps().stampFor,
      cacheable: always,
    })

    const first = await cache.run({ root: '/p', argv: ['list'] })
    const second = await cache.run({ root: '/p', argv: ['list'] })

    expect(second).toEqual(first)
    expect(calls()).toBe(1)
  })

  it('asks again when the governed files moved', async () => {
    const { transport, calls } = counting()
    const clock = stamps('a')
    const cache = createCachingTransport(transport, { stampFor: clock.stampFor, cacheable: always })

    await cache.run({ root: '/p', argv: ['list'] })
    clock.move('b')
    await cache.run({ root: '/p', argv: ['list'] })

    // The stamp is the whole expiry mechanism: a write by this app, by a terminal or by an
    // agent all move it the same way, and no answer outlives the file it came off.
    expect(calls()).toBe(2)
  })

  it('keeps two projects apart', async () => {
    const { transport, calls } = counting()
    const cache = createCachingTransport(transport, {
      stampFor: stamps().stampFor,
      cacheable: always,
    })

    await cache.run({ root: '/one', argv: ['list'] })
    await cache.run({ root: '/two', argv: ['list'] })

    expect(calls()).toBe(2)
  })

  it('keeps two argv apart', async () => {
    const { transport, calls } = counting()
    const cache = createCachingTransport(transport, {
      stampFor: stamps().stampFor,
      cacheable: always,
    })

    await cache.run({ root: '/p', argv: ['list', '--block', 'A'] })
    await cache.run({ root: '/p', argv: ['list', '--block', 'B'] })

    expect(calls()).toBe(2)
  })

  it('does not confuse a root with a space for a longer argv', async () => {
    // Joined on a space these two are one key, and the second would be served the first's
    // answer. NUL is the separator for exactly this.
    const { transport, calls } = counting()
    const cache = createCachingTransport(transport, {
      stampFor: stamps().stampFor,
      cacheable: always,
    })

    await cache.run({ root: '/a b', argv: ['c'] })
    await cache.run({ root: '/a', argv: ['b', 'c'] })

    expect(calls()).toBe(2)
  })
})

describe('RG7: what is never remembered', () => {
  it('passes a call through when the caller says it may not be cached', async () => {
    const { transport, calls } = counting()
    const cache = createCachingTransport(transport, {
      stampFor: stamps().stampFor,
      cacheable: () => false,
    })

    await cache.run({ root: '/p', argv: ['ship', 'RG1'] })
    await cache.run({ root: '/p', argv: ['ship', 'RG1'] })

    // A write served from a cache is a write that appears to have happened twice.
    expect(calls()).toBe(2)
    expect(cache.size).toBe(0)
  })

  it('does not stamp a project it is not going to cache', async () => {
    const stampFor = vi.fn(() => Promise.resolve('a'))
    const { transport } = counting()
    const cache = createCachingTransport(transport, { stampFor, cacheable: () => false })

    await cache.run({ root: '/p', argv: ['ship'] })

    expect(stampFor).not.toHaveBeenCalled()
  })

  it('remembers nothing about a call that never happened', async () => {
    const failing: Transport = {
      run: () => Promise.reject(new EngineCallFailed('timeout', 'ran past 100ms', 100)),
    }
    const cache = createCachingTransport(failing, {
      stampFor: stamps().stampFor,
      cacheable: always,
    })

    await expect(cache.run({ root: '/p', argv: ['list'] })).rejects.toBeInstanceOf(EngineCallFailed)
    expect(cache.size).toBe(0)
  })
})

describe('RG7: forgetting', () => {
  it('forgets one project and keeps the rest', async () => {
    const { transport, calls } = counting()
    const cache = createCachingTransport(transport, {
      stampFor: stamps().stampFor,
      cacheable: always,
    })

    await cache.run({ root: '/one', argv: ['list'] })
    await cache.run({ root: '/two', argv: ['list'] })
    cache.invalidate('/one')

    await cache.run({ root: '/two', argv: ['list'] })
    expect(calls()).toBe(2)
    await cache.run({ root: '/one', argv: ['list'] })
    expect(calls()).toBe(3)
  })

  it('does not forget a project whose name merely starts the same', async () => {
    const { transport, calls } = counting()
    const cache = createCachingTransport(transport, {
      stampFor: stamps().stampFor,
      cacheable: always,
    })

    await cache.run({ root: '/one-more', argv: ['list'] })
    cache.invalidate('/one')

    await cache.run({ root: '/one-more', argv: ['list'] })
    expect(calls()).toBe(1)
  })

  it('drops the least recently used when it is full', async () => {
    const { transport } = counting()
    const cache = createCachingTransport(transport, {
      stampFor: stamps().stampFor,
      cacheable: always,
      max: 2,
    })

    await cache.run({ root: '/p', argv: ['a'] })
    await cache.run({ root: '/p', argv: ['b'] })
    await cache.run({ root: '/p', argv: ['a'] }) // touches a, so b is now the oldest
    await cache.run({ root: '/p', argv: ['c'] })

    expect(cache.size).toBe(2)
  })

  it('clears everything', async () => {
    const { transport } = counting()
    const cache = createCachingTransport(transport, {
      stampFor: stamps().stampFor,
      cacheable: always,
    })

    await cache.run({ root: '/p', argv: ['list'] })
    cache.clear()

    expect(cache.size).toBe(0)
  })
})

describe('RG189: the place a refreshed entry keeps', () => {
  it('moves a refreshed key to the end, so eviction does not take what is being used', async () => {
    const { transport, calls } = counting()
    const clock = stamps()
    const cache = createCachingTransport(transport, {
      stampFor: clock.stampFor,
      cacheable: always,
      max: 2,
    })

    await cache.run({ root: '/p', argv: ['a'] })
    await cache.run({ root: '/p', argv: ['b'] })
    // The files move, and `a` is read again: a refresh, which is a write on a key the table
    // already holds. A `Map` leaves such a key where it was, which would make `a` the next
    // to go — the entry somebody is actually using.
    clock.move('b')
    await cache.run({ root: '/p', argv: ['a'] })
    const refreshed = calls()

    // `c` fills the table and evicts the oldest, which is now `b` and not `a`.
    await cache.run({ root: '/p', argv: ['c'] })
    await cache.run({ root: '/p', argv: ['a'] })

    expect(cache.size).toBe(2)
    expect(calls()).toBe(refreshed + 1)
  })

  it('evicts the one nobody asked for, which is what least-recently-used means', async () => {
    const { transport, calls } = counting()
    const clock = stamps()
    const cache = createCachingTransport(transport, {
      stampFor: clock.stampFor,
      cacheable: always,
      max: 2,
    })

    await cache.run({ root: '/p', argv: ['a'] })
    await cache.run({ root: '/p', argv: ['b'] })
    clock.move('b')
    await cache.run({ root: '/p', argv: ['a'] })
    await cache.run({ root: '/p', argv: ['c'] })
    const before = calls()

    // `b` is the one that went, so asking for it runs the engine again.
    await cache.run({ root: '/p', argv: ['b'] })

    expect(calls()).toBe(before + 1)
  })
})
