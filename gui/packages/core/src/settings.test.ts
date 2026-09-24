import { describe, expect, it } from 'vitest'

import { DEFAULT_LIMITS } from './limits'
import { isRowOrder } from './portfolio'
import { DEPTH_CEILING } from './roots'
import { DEFAULT_POLICY } from './scanning'
import {
  DEFAULT_SETTINGS,
  isSessionCard,
  isSessionLayout,
  isSessionNotes,
  isSessionSides,
  isTheme,
  moveCard,
  placeOf,
  readSettings,
  sameLayout,
  SESSION_CARDS,
  SETTINGS_VERSION,
  settingsText,
  SIDE_SHARE,
  sideShare,
  steppedPlace,
  wasReset,
  type SessionLayout,
} from './settings'

/** An arrangement somebody chose, which is not the default one (RG276). */
const ARRANGED: SessionLayout = { left: ['files', 'handed'], right: ['moved'] }

/** A settings file as this build writes one. */
const WRITTEN = {
  version: SETTINGS_VERSION,
  roots: [{ path: 'D:/Git', depth: 2 }],
  skip: ['node_modules', 'dist'],
  width: 8,
  // Zero is the unset state: the machine's own number stands in for it (RG250).
  projectsAtOnce: 0,
  theme: 'dark',
  locale: 'pt-BR',
  sessionNotes: 'hidden',
  portfolioOrder: 'open-descending',
  sessionLayout: ARRANGED,
  sessionSides: { left: null, right: 31.5 },
}

describe('RG47: the one thing this app owns', () => {
  it('reads back what it wrote', () => {
    const read = readSettings(WRITTEN)

    expect(wasReset(read)).toBe(false)
    expect(read.settings).toEqual({ ...WRITTEN, version: SETTINGS_VERSION })
  })

  it('starts from defaults that come from the modules that own them', () => {
    // Not a second copy of the ignore list or the pool width: the scan and the read limits
    // already declare theirs, and a settings file that disagreed would be a second rule.
    expect(DEFAULT_SETTINGS.skip).toBe(DEFAULT_POLICY.ignore)
    expect(DEFAULT_SETTINGS.width).toBe(DEFAULT_LIMITS.width)
    expect(DEFAULT_SETTINGS.roots).toEqual([])
  })

  it('holds no project data and no cached answer', () => {
    // The project list is the catalogue's and a remembered reading is its own record
    // (RG251); this file is only what somebody chose.
    // The portfolio's order is a choice too, and not the ranking it produced (RG241), and so
    // is where a session's cards sit (RG276).
    expect(Object.keys(DEFAULT_SETTINGS).sort()).toEqual([
      'locale',
      'portfolioOrder',
      'projectsAtOnce',
      'roots',
      'sessionLayout',
      'sessionNotes',
      'sessionSides',
      'skip',
      'theme',
      'version',
      'width',
    ])
  })

  it('writes a file a person can read and edit', () => {
    const text = settingsText(DEFAULT_SETTINGS)

    expect(text.endsWith('\n')).toBe(true)
    expect(text).toContain('\n  "roots"')
    expect(JSON.parse(text)).toEqual(DEFAULT_SETTINGS)
  })

  it('stamps its own version on the way out, whatever it was handed', () => {
    expect(JSON.parse(settingsText({ ...DEFAULT_SETTINGS, version: 99 }))).toHaveProperty(
      'version',
      SETTINGS_VERSION,
    )
  })
})

describe('RG47: a bad file resets field by field, and says so', () => {
  it('keeps the roots when the pool width is unusable', () => {
    // The whole point: a width typed as a word should not cost somebody the roots they
    // spent a minute naming.
    const read = readSettings({ ...WRITTEN, width: 'eight' })

    expect(read.settings.roots).toEqual(WRITTEN.roots)
    expect(read.settings.width).toBe(DEFAULT_SETTINGS.width)
    // The code and the value it names, since RG123 — the sentence is the catalogue's, and
    // the default this reset to is the field the sentence has a hole for.
    expect(read.reset).toEqual([{ lost: 'width', fields: { width: DEFAULT_SETTINGS.width } }])
  })

  it('drops the roots it cannot read and counts them, keeping the rest', () => {
    const read = readSettings({
      ...WRITTEN,
      roots: [{ path: 'D:/Git', depth: 2 }, { depth: 1 }, 'not a root', { path: '' }],
    })

    expect(read.settings.roots).toEqual([{ path: 'D:/Git', depth: 2 }])
    expect(read.reset).toEqual([{ lost: 'dropped', fields: { count: 3 } }])
  })

  it('holds a root depth to the ceiling rather than dropping the root', () => {
    // A depth of forty is a mistake, not a reason to lose the folder.
    const read = readSettings({ ...WRITTEN, roots: [{ path: 'D:/Git', depth: 40 }] })

    expect(read.settings.roots).toEqual([{ path: 'D:/Git', depth: DEPTH_CEILING }])
    expect(read.reset).toEqual([])
  })

  it('says every field it lost, not only the first', () => {
    const read = readSettings({
      version: SETTINGS_VERSION,
      roots: 'nope',
      skip: [1, 2],
      width: -3,
      theme: 'neon',
      locale: 42,
      sessionNotes: 'whispered',
      portfolioOrder: 'by mood',
      sessionLayout: 'wherever',
      sessionSides: 'wide',
    })

    // One code per field, in the order the fields are read.
    expect(read.reset.map((lost) => lost.lost)).toEqual([
      'roots',
      'skip',
      'width',
      'theme',
      'locale',
      'sessionNotes',
      'portfolioOrder',
      'sessionLayout',
      'sessionSides',
    ])
    expect(read.settings).toEqual(DEFAULT_SETTINGS)
  })

  it('takes a field that is simply absent without calling it a loss', () => {
    // A file written by a build with fewer settings, or by somebody who set what they
    // cared about.
    const read = readSettings({ version: SETTINGS_VERSION, theme: 'light' })

    expect(read.reset).toEqual([])
    expect(read.settings.theme).toBe('light')
    expect(read.settings.width).toBe(DEFAULT_SETTINGS.width)
  })

  it('resets everything for a file that is not an object at all', () => {
    for (const source of [null, 'a string', 42, ['a', 'list']]) {
      const read = readSettings(source)

      expect(read.settings).toEqual(DEFAULT_SETTINGS)
      expect(read.reset).toEqual([{ lost: 'file' }])
    }
  })
})

describe('RG47: the version is read first', () => {
  it('leaves a file from a future build alone and uses defaults', () => {
    // Its fields might mean something else. Guessing is how a newer build's settings get
    // overwritten by an older one.
    const read = readSettings({ ...WRITTEN, version: SETTINGS_VERSION + 1 })

    expect(read.settings).toEqual(DEFAULT_SETTINGS)
    // Both versions travel as fields: what the file said and what this build reads, which
    // is the whole of what makes the sentence worth showing.
    expect(read.reset).toEqual([
      { lost: 'version', fields: { found: SETTINGS_VERSION + 1, reads: SETTINGS_VERSION } },
    ])
  })

  it('reads a file that names no version as this build writes them', () => {
    const read = readSettings({ roots: WRITTEN.roots })

    expect(read.settings.roots).toEqual(WRITTEN.roots)
    expect(read.reset).toEqual([{ lost: 'unversioned' }])
  })

  it('reads an older version, because there is nothing yet to migrate', () => {
    const read = readSettings({ ...WRITTEN, version: 0 })

    expect(read.settings.theme).toBe('dark')
    expect(read.settings.version).toBe(SETTINGS_VERSION)
  })
})

describe('RG208: how a session draws its notes', () => {
  it('draws every note where the file says nothing, which is what every earlier build did', () => {
    // A file from before the choice existed: no loss, and nothing changes on screen.
    const read = readSettings({ version: SETTINGS_VERSION, theme: 'dark' })

    expect(read.settings.sessionNotes).toBe('shown')
    expect(read.reset).toEqual([])
  })

  it('knows the two choices and refuses anything else', () => {
    expect(['shown', 'hidden'].every(isSessionNotes)).toBe(true)
    for (const junk of ['', 'Hidden', 'folded', true, 0, null, undefined]) {
      expect(isSessionNotes(junk)).toBe(false)
    }
  })
})

describe('RG241: the order the portfolio opens in', () => {
  it("opens in the record's order where the file says nothing, which is what every earlier build did", () => {
    const read = readSettings({ version: SETTINGS_VERSION, theme: 'dark' })

    expect(read.settings.portfolioOrder).toBe('record')
    expect(read.reset).toEqual([])
  })

  it('resets an order this build does not know, says so, and keeps every other field', () => {
    const read = readSettings({ ...WRITTEN, portfolioOrder: 'open' })

    expect(read.settings).toEqual({ ...WRITTEN, portfolioOrder: 'record' })
    expect(read.reset).toEqual([{ lost: 'portfolioOrder' }])
  })

  it('knows the five orders and refuses anything else', () => {
    expect(
      ['record', 'name-ascending', 'name-descending', 'open-descending', 'open-ascending'].every(
        isRowOrder,
      ),
    ).toBe(true)
    // `toString` is inherited by every object, and not an order.
    for (const junk of ['', 'open', 'name', 'Record', 'toString', 0, null, undefined, ['record']]) {
      expect(isRowOrder(junk)).toBe(false)
    }
  })
})

describe("RG276: where the session screen's cards sit", () => {
  it('draws the grid every earlier build drew where the file says nothing', () => {
    // What was handed over on the left, what moved and the files it touched on the right: an
    // upgrade changes nothing on screen, and the field's arrival is not a new version.
    const read = readSettings({ version: SETTINGS_VERSION, theme: 'dark' })

    expect(read.settings.sessionLayout).toEqual({ left: ['handed'], right: ['moved', 'files'] })
    expect(read.reset).toEqual([])
    expect(SETTINGS_VERSION).toBe(1)
  })

  it('names every card the default draws, and never the stream', () => {
    const { left, right } = DEFAULT_SETTINGS.sessionLayout

    expect([...left, ...right].sort()).toEqual([...SESSION_CARDS].sort())
    expect(SESSION_CARDS).not.toContain('stream')
  })

  it('drops an id this build does not draw, keeping the rest where the file put them', () => {
    const read = readSettings({
      ...WRITTEN,
      sessionLayout: { left: ['files', 'stream', 7, 'handed'], right: ['moved', 'gates'] },
    })

    expect(read.settings.sessionLayout).toEqual(ARRANGED)
    expect(read.reset).toEqual([])
  })

  it('keeps the first place of a card named twice', () => {
    const read = readSettings({
      ...WRITTEN,
      sessionLayout: { left: ['moved', 'handed'], right: ['files', 'moved', 'handed'] },
    })

    expect(read.settings.sessionLayout).toEqual({ left: ['moved', 'handed'], right: ['files'] })
    expect(read.reset).toEqual([])
  })

  it('puts a card the file never names where the default puts it', () => {
    // How a card a later build adds still appears in a file written before it existed.
    const read = readSettings({
      ...WRITTEN,
      sessionLayout: { left: ['moved'], right: [] },
    })

    expect(read.settings.sessionLayout).toEqual({ left: ['handed', 'moved'], right: ['files'] })
    expect(read.reset).toEqual([])

    const empty = readSettings({ ...WRITTEN, sessionLayout: { left: [], right: [] } })

    expect(empty.settings.sessionLayout).toEqual(DEFAULT_SETTINGS.sessionLayout)
  })

  it('resets a value that is not two lists, says so, and keeps every other field', () => {
    for (const junk of [
      'left',
      null,
      ['handed', 'moved', 'files'],
      { left: ['handed'] },
      { left: 'handed', right: ['moved', 'files'] },
    ]) {
      const read = readSettings({ ...WRITTEN, sessionLayout: junk })

      expect(read.settings).toEqual({
        ...WRITTEN,
        sessionLayout: DEFAULT_SETTINGS.sessionLayout,
      })
      expect(read.reset).toEqual([{ lost: 'sessionLayout' }])
    }
  })

  it('reads back through the file text exactly what was arranged', () => {
    const arranged = { ...DEFAULT_SETTINGS, sessionLayout: ARRANGED }
    const read = readSettings(JSON.parse(settingsText(arranged)))

    expect(read).toEqual({ settings: arranged, reset: [] })
  })

  it('accepts an arrangement only as this build writes one', () => {
    expect(isSessionLayout(DEFAULT_SETTINGS.sessionLayout)).toBe(true)
    // Every card on one side, and none on the other, is an arrangement.
    expect(isSessionLayout({ left: [], right: ['files', 'handed', 'moved'] })).toBe(true)
    for (const junk of [
      { left: ['handed'], right: ['moved'] },
      { left: ['handed', 'handed'], right: ['moved', 'files'] },
      { left: ['handed', 'stream'], right: ['moved', 'files'] },
      { left: ['handed'], right: ['moved', 'files'], width: 20 },
      { left: 'handed', right: ['moved', 'files'] },
      ['handed', 'moved', 'files'],
      null,
      undefined,
    ]) {
      expect(isSessionLayout(junk)).toBe(false)
    }
  })
})

describe('RG276: moving one card', () => {
  const layout = DEFAULT_SETTINGS.sessionLayout

  it('moves a card to the top of the other side bar', () => {
    expect(moveCard(layout, 'files', 'left', 0)).toEqual({
      left: ['files', 'handed'],
      right: ['moved'],
    })
  })

  it('reorders a card along its own side bar, at the index it reads once it has left', () => {
    // The index a sortable list reports for a drop, so a drag and a keyboard call one rule.
    expect(moveCard(layout, 'moved', 'right', 1)).toEqual({
      left: ['handed'],
      right: ['files', 'moved'],
    })
    expect(moveCard(layout, 'files', 'right', 0)).toEqual({
      left: ['handed'],
      right: ['files', 'moved'],
    })
  })

  it('lands a card at the end an index past either end names', () => {
    expect(moveCard(layout, 'handed', 'right', 99)).toEqual({
      left: [],
      right: ['moved', 'files', 'handed'],
    })
    expect(moveCard(layout, 'files', 'left', -4)).toEqual({
      left: ['files', 'handed'],
      right: ['moved'],
    })
  })

  it('leaves the layout it was handed alone, and hands back one the table accepts', () => {
    const moved = moveCard(layout, 'handed', 'right', 1)

    expect(layout).toEqual({ left: ['handed'], right: ['moved', 'files'] })
    expect(isSessionLayout(moved)).toBe(true)
  })
})

describe('RG277: the place a card is moved to', () => {
  const layout = DEFAULT_SETTINGS.sessionLayout

  it('says where a card sits in the terms a move takes, so moving it there moves nothing', () => {
    expect(placeOf(layout, 'handed')).toEqual({ side: 'left', index: 0 })
    expect(placeOf(layout, 'files')).toEqual({ side: 'right', index: 1 })

    const place = placeOf(layout, 'moved')
    if (place === null) throw new Error('lost a card the default draws')
    expect(sameLayout(moveCard(layout, 'moved', place.side, place.index), layout)).toBe(true)
  })

  it('tells two arrangements apart by every place, not by what they hold', () => {
    expect(sameLayout(layout, { left: ['handed'], right: ['moved', 'files'] })).toBe(true)
    expect(sameLayout(layout, { left: ['handed'], right: ['files', 'moved'] })).toBe(false)
    expect(sameLayout(layout, { left: [], right: ['handed', 'moved', 'files'] })).toBe(false)
  })

  it('steps along a side bar by one place and stops at either end', () => {
    // `files` counted without itself: the right side bar is `moved` alone, so two places.
    const last = { side: 'right', index: 1 } as const

    expect(steppedPlace(layout, 'files', last, 'up')).toEqual({ side: 'right', index: 0 })
    expect(steppedPlace(layout, 'files', last, 'down')).toEqual(last)
    expect(steppedPlace(layout, 'files', { side: 'right', index: 0 }, 'up')).toEqual({
      side: 'right',
      index: 0,
    })
  })

  it('crosses to the other side bar at the same place, or at its end where it is shorter', () => {
    expect(steppedPlace(layout, 'files', { side: 'right', index: 1 }, 'left')).toEqual({
      side: 'left',
      index: 1,
    })
    // Third on the left, and the right side bar is empty: its one place is its end.
    const piled = { left: ['handed', 'moved', 'files'], right: [] } satisfies SessionLayout
    expect(steppedPlace(piled, 'files', { side: 'left', index: 2 }, 'right')).toEqual({
      side: 'right',
      index: 0,
    })
    expect(
      steppedPlace(
        { left: ['handed', 'moved'], right: ['files'] },
        'moved',
        { side: 'left', index: 1 },
        'right',
      ),
    ).toEqual({ side: 'right', index: 1 })
    // Left of the left side bar is still the left side bar.
    expect(steppedPlace(layout, 'handed', { side: 'left', index: 0 }, 'left')).toEqual({
      side: 'left',
      index: 0,
    })
  })

  it('knows the cards this build draws and nothing else, for the ids a drag hands back', () => {
    expect(SESSION_CARDS.every(isSessionCard)).toBe(true)
    for (const junk of ['stream', 'side-left', '', 'Handed', 0, null, undefined]) {
      expect(isSessionCard(junk)).toBe(false)
    }
  })
})

describe('RG279: how wide the session side bars are drawn', () => {
  it('draws the width every earlier build drew where the file says nothing', () => {
    const read = readSettings({ version: SETTINGS_VERSION, theme: 'dark' })

    expect(read.settings.sessionSides).toEqual({ left: null, right: null })
    expect(read.reset).toEqual([])
  })

  it('holds a share outside the bounds to the nearest one, and says so', () => {
    // The design's own case: a file holding ninety per cent, which leaves the stream nothing.
    const read = readSettings({ ...WRITTEN, sessionSides: { left: 90, right: 4 } })

    expect(read.settings.sessionSides).toEqual({ left: SIDE_SHARE.max, right: SIDE_SHARE.min })
    expect(read.reset).toEqual([
      { lost: 'sidesClamped', fields: { min: SIDE_SHARE.min, max: SIDE_SHARE.max } },
    ])
    // Every other field is kept, the arrangement above all.
    expect(read.settings.sessionLayout).toEqual(ARRANGED)
  })

  it('keeps a side the file names no share for at the width it always had', () => {
    const read = readSettings({ ...WRITTEN, sessionSides: { right: 22 } })

    expect(read.settings.sessionSides).toEqual({ left: null, right: 22 })
    expect(read.reset).toEqual([])
  })

  it('puts both back for a value that is not two shares, and says so', () => {
    for (const junk of [
      'wide',
      null,
      [30, 30],
      { left: 'wide', right: 30 },
      { left: Number.NaN },
    ]) {
      const read = readSettings({ ...WRITTEN, sessionSides: junk })

      expect(read.settings.sessionSides).toEqual(DEFAULT_SETTINGS.sessionSides)
      expect(read.reset).toEqual([{ lost: 'sessionSides' }])
    }
  })

  it('keeps a share to a tenth of a per cent and within the bounds', () => {
    expect(sideShare(27.345_678)).toBe(27.3)
    expect(sideShare(11.96)).toBe(SIDE_SHARE.min)
    expect(sideShare(55)).toBe(SIDE_SHARE.max)
  })

  it('accepts widths only as this build writes them', () => {
    expect(isSessionSides(DEFAULT_SETTINGS.sessionSides)).toBe(true)
    expect(isSessionSides({ left: 20, right: null })).toBe(true)
    for (const junk of [
      { left: 90, right: null },
      { left: 20 },
      { left: 20, right: null, stream: 60 },
      { left: '20', right: null },
      null,
      [20, 20],
    ]) {
      expect(isSessionSides(junk)).toBe(false)
    }
  })

  it('reads back through the file text exactly what was dragged', () => {
    const dragged = { ...DEFAULT_SETTINGS, sessionSides: { left: 17.5, right: null } }

    expect(readSettings(JSON.parse(settingsText(dragged)))).toEqual({
      settings: dragged,
      reset: [],
    })
  })
})

describe('RG87: which grounds this build knows', () => {
  it('accepts the three the setting has, `system` included', () => {
    expect(['system', 'light', 'dark'].every(isTheme)).toBe(true)
  })

  it('refuses anything else, which is what the bridge leans on', () => {
    // The main process takes a theme the renderer named, and this is the check standing
    // between that argument and the settings file. A resolved ground is not a setting.
    for (const junk of ['', 'Dark', 'auto', 'light dark', 0, null, undefined, {}, ['dark']]) {
      expect(isTheme(junk)).toBe(false)
    }
  })
})
