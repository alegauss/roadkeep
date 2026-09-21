import { BASE, DEFAULT_SETTINGS, fill, type SessionCard } from '@rk/core'
import { cleanup, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { page, userEvent } from 'vitest/browser'

import { sessionPath } from './areas'
import { holdSessionLayout } from './preferring'
import { at, KEY, RECORD, ROOT, type Wired } from './session-harness'

/**
 * RG277: a session card moved by its title, in a real layout.
 *
 * A browser and not jsdom, for the reason RG213 gives: where a card lands is a question of
 * which card the pointer is over and which half of it, and jsdom lays nothing out — every box
 * is at zero, so every drop would land at the top of whichever side bar it named.
 */

const TITLE: Readonly<Record<SessionCard, string>> = {
  handed: BASE['session.handed'],
  moved: BASE['session.moved'],
  files: BASE['session.edited'],
}

/** A card's box, found by the region the screen marks it with. */
function box(name: SessionCard | 'stream'): DOMRect {
  return region(name).getBoundingClientRect()
}

function region(name: SessionCard | 'stream'): HTMLElement {
  const found = document.querySelector<HTMLElement>(`[data-region="session-${name}"]`)
  if (found === null) throw new Error(`the session drew no ${name} region`)
  return found
}

function grip(card: SessionCard): HTMLElement {
  return screen.getByRole('button', {
    name: fill(BASE['session.card.grip'], { card: TITLE[card] }),
  })
}

function said(): string {
  return screen.getByTestId('card-said').textContent
}

/** The session's screen, with the three cards drawn. */
async function opened(): Promise<Wired> {
  const wired = await at(sessionPath(ROOT, 'AL1', KEY), { sessions: [RECORD] })
  await screen.findByTestId('edited')
  return wired
}

/** The arrangement RG277's design names: the files card at the top of the left side bar. */
const FILES_LEFT = { left: ['files', 'handed'], right: ['moved'] }

beforeEach(async () => {
  // `xl`, where two side bars exist and the grip is drawn.
  await page.viewport(1280, 800)
})

afterEach(() => {
  // The window holds one arrangement for its life, so a test's move is the next one's start.
  holdSessionLayout(DEFAULT_SETTINGS.sessionLayout)
  Reflect.deleteProperty(window, 'roadkeep')
})

describe('RG277: a card dragged by its title', () => {
  it('drops the files card at the top of the left side bar, keeps it, and draws it on a remount', async () => {
    const wired = await opened()

    // Near the top of what was handed over: above its middle, so the drop lands before it.
    await userEvent.dragAndDrop(grip('files'), region('handed'), {
      targetPosition: { x: 60, y: 8 },
      steps: 12,
    })

    await waitFor(() => {
      expect(wired.preferred).toEqual([{ key: 'sessionLayout', value: FILES_LEFT }])
    })
    // Landed: the files over what was handed over in the left side bar, the stream still in
    // the middle, and what moved alone on the right.
    expect(box('files').bottom).toBeLessThanOrEqual(box('handed').top)
    expect(Math.abs(box('files').left - box('handed').left)).toBeLessThanOrEqual(1)
    expect(box('handed').right).toBeLessThanOrEqual(box('stream').left)
    expect(box('stream').right).toBeLessThanOrEqual(box('moved').left)
    expect(said()).toBe(fill(BASE['session.card.dropped.left'], { card: TITLE.files, place: 1 }))

    cleanup()
    await opened()

    expect(box('files').bottom).toBeLessThanOrEqual(box('handed').top)
    expect(box('stream').right).toBeLessThanOrEqual(box('moved').left)
  })

  it('writes nothing for a card dropped where it already was', async () => {
    const wired = await opened()

    // Picked up by its grip and put down on its own face: above the files card's middle, so
    // the one place that is no move at all.
    await userEvent.dragAndDrop(grip('moved'), region('moved'), {
      targetPosition: { x: 60, y: 30 },
      steps: 12,
    })

    await waitFor(() => {
      expect(said()).toBe(fill(BASE['session.card.back'], { card: TITLE.moved }))
    })
    expect(wired.preferred).toEqual([])
    expect(screen.queryByTestId('card-line')).toBeNull()
  })
})

describe('RG277: a card moved with the keys alone', () => {
  it('picks the card up, says each place the arrows choose, and drops it on Space', async () => {
    const wired = await opened()

    grip('files').focus()
    await userEvent.keyboard(' ')
    expect(said()).toBe(fill(BASE['session.card.lifted'], { card: TITLE.files }))

    // Across to the left side bar at the same place, which is its end; then up, before the
    // card already there. The insertion line shows the place a sighted reader is being told.
    await userEvent.keyboard('{ArrowLeft}')
    expect(said()).toBe(fill(BASE['session.card.at.left'], { card: TITLE.files, place: 2 }))
    await userEvent.keyboard('{ArrowUp}')
    expect(said()).toBe(fill(BASE['session.card.at.left'], { card: TITLE.files, place: 1 }))
    const line = screen.getByTestId('card-line').getBoundingClientRect()
    expect(line.bottom).toBeLessThanOrEqual(box('handed').top)

    await userEvent.keyboard(' ')

    await waitFor(() => {
      expect(wired.preferred).toEqual([{ key: 'sessionLayout', value: FILES_LEFT }])
    })
    expect(box('files').bottom).toBeLessThanOrEqual(box('handed').top)
  })

  it('puts the card back on Escape, and writes nothing', async () => {
    const wired = await opened()

    grip('handed').focus()
    await userEvent.keyboard(' ')
    await userEvent.keyboard('{ArrowRight}')
    await userEvent.keyboard('{Escape}')

    expect(said()).toBe(fill(BASE['session.card.back'], { card: TITLE.handed }))
    expect(wired.preferred).toEqual([])
    expect(box('handed').right).toBeLessThanOrEqual(box('stream').left)
  })

  it('gives an emptied side bar its column, and takes a card back through its strip', async () => {
    const wired = await opened()
    const flanked = box('stream').width

    grip('handed').focus()
    await userEvent.keyboard(' ')
    await userEvent.keyboard('{ArrowRight}')
    await userEvent.keyboard(' ')

    const emptied = { left: [], right: ['handed', 'moved', 'files'] }
    await waitFor(() => {
      expect(wired.preferred).toEqual([{ key: 'sessionLayout', value: emptied }])
    })
    expect(document.querySelector('[data-side="left"]')).toBeNull()
    // The stream takes the left side bar's column and is wider by it.
    expect(box('stream').width).toBeGreaterThan(flanked + 200)
    expect(box('stream').right).toBeLessThanOrEqual(box('handed').left)

    // While a card moves, the empty side bar is a strip that still takes it.
    grip('moved').focus()
    await userEvent.keyboard(' ')
    const strip = screen.getByTestId('card-strip')
    expect(strip.getBoundingClientRect().right).toBeLessThanOrEqual(box('stream').left)
    await userEvent.keyboard('{ArrowLeft}')
    expect(said()).toBe(fill(BASE['session.card.at.left'], { card: TITLE.moved, place: 1 }))
    await userEvent.keyboard(' ')

    await waitFor(() => {
      expect(wired.preferred.at(-1)).toEqual({
        key: 'sessionLayout',
        value: { left: ['moved'], right: ['handed', 'files'] },
      })
    })
    expect(screen.queryByTestId('card-strip')).toBeNull()
    expect(box('moved').right).toBeLessThanOrEqual(box('stream').left)
  })
})
