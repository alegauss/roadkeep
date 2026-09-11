import { BRIDGE_TOPICS } from '@rk/core'
import { describe, expect, it } from 'vitest'

import { createSubscriptions, type Follow, type Subscriber } from './subscriptions'

/**
 * RG144: who is listening to what, with windows and a disk that are both fakes.
 *
 * What is held is the counting: the first listener starts hearing a source and the last one
 * stops it, an event reaches the windows listening to its key and no others, and a window
 * that goes away gives up everything it held at once.
 */

function window(id: number): Subscriber & { heard: [string, unknown][]; gone: boolean } {
  const heard: [string, unknown][] = []
  const one = {
    id,
    heard,
    gone: false,
    send(channel: string, event: unknown) {
      heard.push([channel, event])
    },
    isDestroyed: () => one.gone,
  }
  return one
}

/** A source per key, counting how many are being heard. */
function sources() {
  const hearing = new Map<string, () => void>()
  let started = 0
  const governed: Follow = (key, heard) => {
    started += 1
    hearing.set(key, heard)
    return Promise.resolve(() => {
      hearing.delete(key)
    })
  }
  return {
    governed,
    started: () => started,
    hearing: () => [...hearing.keys()],
    move: (key: string) => hearing.get(key)?.(),
  }
}

/** Let the stop a source answered with arrive, which is a promise's turn away. */
const settled = (): Promise<void> => new Promise((done) => setTimeout(done, 0))

describe('RG144: subscribing to a project moving', () => {
  it('starts hearing a project once, however many windows listen to it', () => {
    const disk = sources()
    const subscriptions = createSubscriptions(disk)

    subscriptions.subscribe(window(1), 'governed', '/a')
    subscriptions.subscribe(window(2), 'governed', '/a')

    expect(disk.started()).toBe(1)
  })

  it('sends a move to the windows listening to that project and no others', () => {
    const disk = sources()
    const subscriptions = createSubscriptions(disk)
    const one = window(1)
    const two = window(2)

    subscriptions.subscribe(one, 'governed', '/a')
    subscriptions.subscribe(two, 'governed', '/b')
    disk.move('/a')

    expect(one.heard).toEqual([[BRIDGE_TOPICS.governed, { root: '/a' }]])
    expect(two.heard).toEqual([])
  })

  it('stops hearing a project when the last listener gives it up', async () => {
    const disk = sources()
    const subscriptions = createSubscriptions(disk)
    const one = window(1)

    subscriptions.subscribe(one, 'governed', '/a')
    subscriptions.subscribe(one, 'governed', '/a')
    subscriptions.unsubscribe(one, 'governed', '/a')
    await settled()
    const afterFirst = disk.hearing()
    subscriptions.unsubscribe(one, 'governed', '/a')
    await settled()

    expect(afterFirst).toEqual(['/a'])
    expect(disk.hearing()).toEqual([])
    expect(subscriptions.following).toBe(0)
  })

  it('gives up everything a window held when it goes', async () => {
    const disk = sources()
    const subscriptions = createSubscriptions(disk)
    const one = window(1)

    subscriptions.subscribe(one, 'governed', '/a')
    subscriptions.subscribe(one, 'governed', '/b')
    subscriptions.drop(one)
    await settled()

    expect(disk.hearing()).toEqual([])
  })

  it('sends nothing to a window already destroyed', () => {
    const disk = sources()
    const subscriptions = createSubscriptions(disk)
    const one = window(1)

    subscriptions.subscribe(one, 'governed', '/a')
    one.gone = true
    disk.move('/a')

    expect(one.heard).toEqual([])
  })
})

describe('RG144: a session line, published by whoever runs the session', () => {
  it('reaches the windows listening to that session, with no disk behind it', () => {
    const disk = sources()
    const subscriptions = createSubscriptions(disk)
    const one = window(1)

    subscriptions.subscribe(one, 'session', 's1')
    subscriptions.publish('session', 's1', { session: 's1', line: '{"type":"text"}' })
    subscriptions.publish('session', 's2', { session: 's2', line: 'elsewhere' })

    expect(one.heard).toEqual([[BRIDGE_TOPICS.session, { session: 's1', line: '{"type":"text"}' }]])
    expect(disk.started()).toBe(0)
  })
})
