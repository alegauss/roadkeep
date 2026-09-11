import { BRIDGE_TOPICS, type Topic, type TopicEvents } from '@rk/core'

/**
 * Who is listening to what, on the main side of the bridge (RG144).
 *
 * The renderer subscribes by topic and key; this counts the subscriptions per window and
 * sends each event to the windows listening to its key. Nothing here names Electron: a
 * window arrives as the three things a subscription needs of it, so a test drives it with a
 * fake window and a fake source.
 *
 * **What hears the disk is started by the first listener and stopped by the last.** A
 * project nobody is looking at holds no handle, and a window that closed without giving its
 * subscriptions up gives them up here, when it is dropped: a listener that outlives its
 * screen is a handle held on a folder for nothing.
 *
 * `session` has no source here yet. RG153 starts sessions from a window, and what it hears
 * is published through `publish`; the channel and its shape are fixed now so that line is
 * one call and not a second design.
 */

/** A window, as far as a subscription needs one. */
export interface Subscriber {
  readonly id: number
  send(channel: string, event: unknown): void
  isDestroyed(): boolean
}

/**
 * Start hearing one source, answering the way to stop — or null where there is nothing to
 * hear, which leaves the subscription standing and silent.
 */
export type Follow = (key: string, heard: () => void) => Promise<(() => void) | null>

export interface Subscriptions {
  subscribe(subscriber: Subscriber, topic: Topic, key: string): void
  unsubscribe(subscriber: Subscriber, topic: Topic, key: string): void
  /** Everything one window held, given up at once. What a closed window calls. */
  drop(subscriber: Subscriber): void
  publish<T extends Topic>(topic: T, key: string, event: TopicEvents[T]): void
  /** How many sources are being heard right now — what a test counts to find a leak. */
  readonly following: number
}

interface Listening {
  /** Subscriber id → how many of its subscriptions are on this key. */
  readonly counts: Map<number, number>
  readonly subscribers: Map<number, Subscriber>
  stop: Promise<(() => void) | null> | null
}

/** NUL, as the cache keys, because neither a topic nor a path can hold one. */
const SEPARATOR = '\u0000'

export function createSubscriptions(sources: { readonly governed: Follow }): Subscriptions {
  const listening = new Map<string, Listening>()

  const stopFollowing = (entry: Listening): void => {
    const stopping = entry.stop
    entry.stop = null
    void stopping?.then((stop) => {
      stop?.()
    })
  }

  const leave = (id: string, entry: Listening, subscriberId: number, all: boolean): void => {
    const count = entry.counts.get(subscriberId) ?? 0
    if (count === 0) return
    if (all || count === 1) {
      entry.counts.delete(subscriberId)
      entry.subscribers.delete(subscriberId)
    } else {
      entry.counts.set(subscriberId, count - 1)
    }
    if (entry.counts.size > 0) return
    listening.delete(id)
    stopFollowing(entry)
  }

  const publish = <T extends Topic>(topic: T, key: string, event: TopicEvents[T]): void => {
    const entry = listening.get(`${topic}${SEPARATOR}${key}`)
    if (entry === undefined) return
    for (const subscriber of [...entry.subscribers.values()]) {
      if (!subscriber.isDestroyed()) subscriber.send(BRIDGE_TOPICS[topic], event)
    }
  }

  return {
    subscribe(subscriber, topic, key) {
      const id = `${topic}${SEPARATOR}${key}`
      let entry = listening.get(id)
      if (entry === undefined) {
        entry = { counts: new Map(), subscribers: new Map(), stop: null }
        listening.set(id, entry)
        if (topic === 'governed') {
          entry.stop = sources.governed(key, () => {
            publish('governed', key, { root: key })
          })
        }
      }
      entry.counts.set(subscriber.id, (entry.counts.get(subscriber.id) ?? 0) + 1)
      entry.subscribers.set(subscriber.id, subscriber)
    },

    unsubscribe(subscriber, topic, key) {
      const id = `${topic}${SEPARATOR}${key}`
      const entry = listening.get(id)
      if (entry !== undefined) leave(id, entry, subscriber.id, false)
    },

    drop(subscriber) {
      for (const [id, entry] of [...listening]) leave(id, entry, subscriber.id, true)
    },

    publish,

    get following() {
      return [...listening.values()].filter((entry) => entry.stop !== null).length
    },
  }
}
