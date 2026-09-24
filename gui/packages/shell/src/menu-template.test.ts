import { translator, type UpdateCheck } from '@rk/core'
import type { MenuItemConstructorOptions } from 'electron'
import { describe, expect, it } from 'vitest'

import { askForUpdate, dialogOf, menuTemplate, type UpdateDialog } from './menu-template'
import { RELEASE_PAGES } from './updates'

/**
 * RG50: the menu item and the dialog behind it, without an Electron process.
 *
 * Three promises the line's design makes, each held here: nothing asks the network until the
 * item is clicked, the answer names both versions, and the most a click can lead to is a
 * release page the person chose to open.
 */
const say = translator()
const PAGE = `${RELEASE_PAGES}tag/v0.2.0`
const NEWER: UpdateCheck = { kind: 'newer', current: '0.1.0', latest: '0.2.0', url: PAGE }

function helpOf(template: MenuItemConstructorOptions[]): MenuItemConstructorOptions {
  const help = template.find((item) => item.role === 'help')
  if (help === undefined) throw new Error('no help menu')
  return help
}

describe('RG50: the menu', () => {
  it('keeps the platform`s own menus, and replaces only Help', () => {
    const roles = menuTemplate(say, () => {}, 'win32').map((item) => item.role)

    // Copy, paste, reload and the rest keep the platform's keys and words because they are
    // its roles and not a copy of them.
    expect(roles).toEqual(['fileMenu', 'editMenu', 'viewMenu', 'windowMenu', 'help'])
    expect(menuTemplate(say, () => {}, 'darwin')[0]?.role).toBe('appMenu')
  })

  it('asks nothing until the item is clicked', () => {
    let asked = 0
    const template = menuTemplate(say, () => {
      asked += 1
    })
    const items = helpOf(template).submenu as MenuItemConstructorOptions[]
    const check = items.find((item) => item.label === say('update.check'))

    // Built at launch and on every language change, and the network is asked by neither.
    expect(asked).toBe(0)
    check?.click?.(undefined as never, undefined, undefined as never)
    expect(asked).toBe(1)
  })
})

describe('RG50: the dialog', () => {
  it('names both versions, and offers the page first where there is a newer one', () => {
    const shown = dialogOf(NEWER, say)

    expect(shown.message).toContain('0.1.0')
    expect(shown.message).toContain('0.2.0')
    expect(shown.buttons).toEqual([say('update.open'), say('update.close')])
    expect(shown.opens).toBe(PAGE)
  })

  it('offers nothing to open where there is nothing newer, or the link is not ours', () => {
    expect(dialogOf({ kind: 'none', current: '0.1.0' }, say).buttons).toEqual([say('update.close')])
    // A URL off a network answer is somebody else's word; only this repository's releases open.
    const elsewhere = dialogOf({ ...NEWER, url: 'https://example.com/roadkeep.exe' }, say)
    expect(elsewhere.opens).toBeNull()
    expect(elsewhere.buttons).toEqual([say('update.close')])
  })

  it('opens the page only when the person picks that button', async () => {
    const opened: string[] = []
    const asking = (choice: number) => ({
      current: '0.1.0',
      say,
      check: () => Promise.resolve(NEWER),
      show: (_shown: UpdateDialog) => Promise.resolve(choice),
      open: (url: string) => {
        opened.push(url)
        return Promise.resolve()
      },
    })

    await askForUpdate(asking(1))
    expect(opened).toEqual([])
    await askForUpdate(asking(0))
    expect(opened).toEqual([PAGE])
  })
})
