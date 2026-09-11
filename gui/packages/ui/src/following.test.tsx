import { UNKNOWN_GATE, type RendererBridge } from '@rk/core'
import { render } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'

import { useGovernedMoves } from './following'
import { stubBridge } from './stub-bridge'

/**
 * RG144: a screen hears its project move, and stops hearing it when it goes.
 *
 * The leak the design names is a subscription outliving its screen, which in the running app
 * is a watch main holds on a folder for nothing. So what is held here is the pairing: every
 * subscription taken is given back on unmount, and on a change of project, exactly once.
 */

interface Taken {
  readonly topic: string
  readonly key: string
  readonly listener: () => void
  given: number
}

function recording(): { bridge: RendererBridge; taken: Taken[] } {
  const taken: Taken[] = []
  const bridge = stubBridge({
    subscribe: (topic, key, listener) => {
      const one: Taken = {
        topic,
        key,
        // One object that satisfies every topic's event, since this stub does not know
        // which topic the caller subscribed to.
        listener: () =>
          listener({
            root: key,
            session: key,
            index: 0,
            line: '',
            health: UNKNOWN_GATE,
            changed: 0,
          }),
        given: 0,
      }
      taken.push(one)
      return () => {
        one.given += 1
      }
    },
  })
  Object.defineProperty(window, 'roadkeep', { value: bridge, configurable: true })
  return { bridge, taken }
}

function Following({ root, moved }: { root: string | null; moved: () => void }) {
  useGovernedMoves(root, moved)
  return null
}

/** A `moved` that does nothing, made once so no render hands a fresh one. */
const NOTHING = (): void => undefined

/** Two `moved`s that say which of them was called. */
function saying(): { heard: string[]; first: () => void; second: () => void } {
  const heard: string[] = []
  return {
    heard,
    first: () => {
      heard.push('first')
    },
    second: () => {
      heard.push('second')
    },
  }
}

afterEach(() => {
  Reflect.deleteProperty(window, 'roadkeep')
})

describe('RG144: a screen hears its project move', () => {
  it('subscribes to the governed files of the project it shows', () => {
    const { taken } = recording()
    const said = saying()

    render(<Following root="/proj" moved={said.first} />)
    taken[0]?.listener()

    expect(taken.map((one) => [one.topic, one.key])).toEqual([['governed', '/proj']])
    expect(said.heard).toEqual(['first'])
  })

  it('gives the subscription back when the screen unmounts, once', () => {
    const { taken } = recording()

    const drawn = render(<Following root="/proj" moved={NOTHING} />)
    drawn.unmount()

    expect(taken[0]?.given).toBe(1)
  })

  it('moves the subscription with the project, rather than holding both', () => {
    const { taken } = recording()

    const drawn = render(<Following root="/one" moved={NOTHING} />)
    drawn.rerender(<Following root="/two" moved={NOTHING} />)

    expect(taken.map((one) => [one.key, one.given])).toEqual([
      ['/one', 1],
      ['/two', 0],
    ])
  })

  it('keeps one subscription through a render that hands it a new function', () => {
    const { taken } = recording()
    const said = saying()

    const drawn = render(<Following root="/proj" moved={said.first} />)
    drawn.rerender(<Following root="/proj" moved={said.second} />)
    taken[0]?.listener()

    expect(taken).toHaveLength(1)
    expect(said.heard).toEqual(['second'])
  })

  it('hears nothing and throws nothing with no bridge, or no project yet', () => {
    const drawn = render(<Following root="/proj" moved={NOTHING} />)
    expect(() => drawn.unmount()).not.toThrow()

    const { taken } = recording()
    render(<Following root={null} moved={NOTHING} />)
    expect(taken).toEqual([])
  })
})
