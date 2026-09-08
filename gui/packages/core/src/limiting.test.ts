import { describe, expect, it } from 'vitest'

import { createLimiter } from './limiting'

/**
 * Yield the turn back, a given number of times.
 *
 * A timer would say this more directly and this package has none — no Node and no DOM, so
 * no `setTimeout` (RG1). Microtasks are enough for what is being asserted: work that has
 * started and not finished is work in flight, and a turn is what lets the next one start.
 */
async function yieldTurns(count: number): Promise<void> {
  for (let turn = 0; turn < count; turn += 1) await Promise.resolve()
}

/** Work that stays in flight for a few turns and reports how much of it overlapped. */
function counting(turns = 2) {
  let running = 0
  let most = 0
  const started: number[] = []

  const work = (id: number) => async () => {
    running += 1
    most = Math.max(most, running)
    started.push(id)
    await yieldTurns(turns)
    running -= 1
    return id
  }

  return { work, most: () => most, started: () => started }
}

describe('RG71: how many things may happen at once', () => {
  it('runs them together, which is the whole point of the wait being asynchronous', async () => {
    const held = counting()
    const limiter = createLimiter(4)

    await Promise.all([1, 2, 3, 4].map((id) => limiter.hold(held.work(id))))

    expect(held.most()).toBe(4)
  })

  it('runs up to the width and no more', async () => {
    const held = counting()
    const limiter = createLimiter(2)

    const answers = await Promise.all([1, 2, 3, 4, 5].map((id) => limiter.hold(held.work(id))))

    expect(held.most()).toBe(2)
    expect(answers).toEqual([1, 2, 3, 4, 5])
  })

  it('admits in the order they asked', async () => {
    const held = counting()
    const limiter = createLimiter(1)

    await Promise.all([1, 2, 3, 4].map((id) => limiter.hold(held.work(id))))

    // First in, first out. A caller that asked for four gets them in the order it asked,
    // which is the order it is drawing them.
    expect(held.started()).toEqual([1, 2, 3, 4])
  })

  it('gives the slot back when the work threw', async () => {
    const limiter = createLimiter(1)

    await expect(limiter.hold(() => Promise.reject(new Error('the disk said no')))).rejects.toThrow(
      'the disk said no',
    )

    // The whole reason for the `finally`: one failure must not close the door behind it.
    await expect(limiter.hold(() => Promise.resolve('through'))).resolves.toBe('through')
  })

  it('treats a width below one as one, rather than as none', async () => {
    // A width of zero would be a limiter that admits nobody, which is not slower work but
    // work that never finishes.
    await expect(createLimiter(0).hold(() => Promise.resolve('ran'))).resolves.toBe('ran')
    await expect(createLimiter(-3).hold(() => Promise.resolve('ran'))).resolves.toBe('ran')
    await expect(createLimiter(2.7).hold(() => Promise.resolve('ran'))).resolves.toBe('ran')
  })
})
