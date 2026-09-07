import { describe, expect, it } from 'vitest'

import { createPooledTransport } from './pool'
import { EngineCallFailed, type CancelSignal, type EngineResult, type Transport } from './transport'

/**
 * A cancellation this package can build. `AbortController` is neither in the DOM nor in
 * Node as far as `core` is concerned — it has neither in scope — and that is the same
 * constraint `CancelSignal` exists for.
 */
function cancellation(): { signal: CancelSignal; cancel: () => void } {
  const listeners = new Set<() => void>()
  let aborted = false
  return {
    cancel() {
      aborted = true
      for (const listener of listeners) listener()
    },
    signal: {
      get aborted() {
        return aborted
      },
      addEventListener: (_type, listener) => listeners.add(listener),
      removeEventListener: (_type, listener) => listeners.delete(listener),
    },
  }
}

/** A transport whose calls finish only when the test lets them. */
function held(): {
  transport: Transport
  inFlight: () => number
  peak: () => number
  finish: (label: string) => void
} {
  const pending = new Map<string, (result: EngineResult) => void>()
  let peak = 0

  return {
    inFlight: () => pending.size,
    peak: () => peak,
    finish(label) {
      const settle = pending.get(label)
      pending.delete(label)
      settle?.({ code: 0, stdout: label, stderr: '', durationMs: 1 })
    },
    transport: {
      run(request) {
        return new Promise<EngineResult>((resolve) => {
          pending.set(request.argv[0] ?? '', resolve)
          peak = Math.max(peak, pending.size)
        })
      },
    },
  }
}

const at = (label: string) => ({ root: '/p', argv: [label] })

describe('RG8: how many calls run at once', () => {
  it('never runs more than the width', async () => {
    const engine = held()
    const pool = createPooledTransport(engine.transport, { width: 2 })

    const calls = ['a', 'b', 'c', 'd'].map((label) => pool.run(at(label)))
    await Promise.resolve()

    // A hundred candidates must never become a hundred processes.
    expect(engine.inFlight()).toBe(2)

    engine.finish('a')
    engine.finish('b')
    await Promise.all([calls[0], calls[1]])
    await Promise.resolve()

    expect(engine.inFlight()).toBe(2)
    engine.finish('c')
    engine.finish('d')
    await Promise.all(calls)
    expect(engine.peak()).toBe(2)
  })

  it('admits the calls in the order they were asked for', async () => {
    const engine = held()
    const pool = createPooledTransport(engine.transport, { width: 1 })

    const calls = ['first', 'second'].map((label) => pool.run(at(label)))
    await Promise.resolve()

    // A screen that asked for twenty projects is drawing them in that order.
    expect(engine.inFlight()).toBe(1)
    engine.finish('first')
    expect(await calls[0]).toMatchObject({ stdout: 'first' })

    await Promise.resolve()
    engine.finish('second')
    expect(await calls[1]).toMatchObject({ stdout: 'second' })
  })

  it('frees the slot when a call fails', async () => {
    const failing: Transport = {
      run: () => Promise.reject(new EngineCallFailed('unspawnable', 'no engine', 1)),
    }
    const pool = createPooledTransport(failing, { width: 1 })

    await expect(pool.run(at('a'))).rejects.toBeInstanceOf(EngineCallFailed)
    // A slot leaked on failure is a pool that stops after `width` broken projects.
    await expect(pool.run(at('b'))).rejects.toBeInstanceOf(EngineCallFailed)
  })

  it('treats a width below one as one rather than as none', async () => {
    const engine = held()
    const pool = createPooledTransport(engine.transport, { width: 0 })

    void pool.run(at('a'))
    await Promise.resolve()

    // A width of zero that admitted nothing would be a pool that never answers.
    expect(engine.inFlight()).toBe(1)
  })
})

describe('RG8: cancelling a call that has not started', () => {
  it('never starts a process for a call cancelled while queued', async () => {
    const engine = held()
    const pool = createPooledTransport(engine.transport, { width: 1 })
    const controller = cancellation()

    const first = pool.run(at('running'))
    const queued = pool.run({ ...at('queued'), signal: controller.signal })
    await Promise.resolve()
    expect(engine.inFlight()).toBe(1)

    controller.cancel()
    engine.finish('running')
    await first

    await expect(queued).rejects.toMatchObject({ reason: 'aborted' })
    // The one that mattered: the second label never reached the engine at all.
    expect(engine.peak()).toBe(1)
  })
})
