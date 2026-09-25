import { existsSync, mkdtempSync } from 'node:fs'
import { tmpdir } from 'node:os'
import path from 'node:path'

import { BASE, BASE_LOCALE, translator } from '@rk/core'
import { afterAll, describe, expect, it } from 'vitest'

import {
  OFFERED_FILE,
  PLUGIN_COMMANDS,
  askDialog,
  offerPlugin,
  offerWanted,
  type Offering,
} from './plugin-offer'
import { removeTree } from './scratch'

/**
 * RK1700: the first launch of an AppImage or a dmg offers the Claude Code plugin, once.
 *
 * Every promise here fails silently. An offer made on every launch is a nag; one made on
 * Windows asks twice what the installer asked; one made where no `claude` answers is an error
 * dialog wearing a question; one that ran without asking is a network call nobody chose.
 */

const say = translator(BASE, BASE_LOCALE)
const scratches: string[] = []

function userData(): string {
  const at = mkdtempSync(path.join(tmpdir(), 'rk-offer-'))
  scratches.push(at)
  return at
}

afterAll(() => {
  for (const at of scratches) removeTree(at)
})

interface Seen {
  readonly ran: string[][]
  readonly shown: string[]
}

function offering(
  over: Partial<Offering> & { answers?: number[]; exits?: (argv: readonly string[]) => number },
): { offering: Offering; seen: Seen } {
  const seen: Seen = { ran: [], shown: [] }
  const answers = [...(over.answers ?? [0, 0])]
  const offered: Offering = {
    platform: 'linux',
    packaged: true,
    userData: userData(),
    say,
    // A home with no Claude Code under it, so the one candidate is the name on PATH.
    home: userData(),
    run: (argv) => {
      seen.ran.push([...argv])
      return Promise.resolve(over.exits === undefined ? 0 : over.exits(argv))
    },
    show: (dialog) => {
      seen.shown.push(dialog.message)
      return Promise.resolve(answers.shift() ?? 1)
    },
    ...over,
  }
  return { offering: offered, seen }
}

describe('RK1700: when the first launch asks', () => {
  it('asks a packaged AppImage or dmg, and nothing else', () => {
    const at = userData()
    expect(offerWanted({ platform: 'linux', packaged: true, userData: at })).toBe(true)
    expect(offerWanted({ platform: 'darwin', packaged: true, userData: at })).toBe(true)
    // Windows: the installer already asked.
    expect(offerWanted({ platform: 'win32', packaged: true, userData: at })).toBe(false)
    // A checkout: a developer's, wired by hand.
    expect(offerWanted({ platform: 'linux', packaged: false, userData: at })).toBe(false)
  })

  it('asks once, whichever the answer was', async () => {
    const { offering: first } = offering({ answers: [1] })
    expect(await offerPlugin(first)).toBe('declined')
    expect(existsSync(path.join(first.userData, OFFERED_FILE))).toBe(true)
    expect(await offerPlugin(first)).toBe('not-wanted')
  })

  it('does not ask where no claude answers, and does not ask again', async () => {
    const { offering: none, seen } = offering({ exits: () => 127 })
    expect(await offerPlugin(none)).toBe('no-claude')
    expect(seen.shown).toEqual([])
    expect(await offerPlugin(none)).toBe('not-wanted')
  })
})

describe('RK1700: what it runs', () => {
  it('names the two commands before running either', () => {
    const message = askDialog(say).message
    expect(message).toContain('claude plugin marketplace add alegauss/roadkeep')
    expect(message).toContain('claude plugin install roadkeep@alegauss')
  })

  it('runs nothing past the probe when declined', async () => {
    const { offering: asked, seen } = offering({ answers: [1] })
    await offerPlugin(asked)
    expect(seen.ran).toEqual([['claude', '--version']])
  })

  it('runs both through the claude that answered, and says it worked', async () => {
    const { offering: asked, seen } = offering({})
    expect(await offerPlugin(asked)).toBe('installed')
    expect(seen.ran.slice(1)).toEqual(PLUGIN_COMMANDS.map((argv) => ['claude', ...argv]))
    expect(seen.shown.at(-1)).toBe(say('plugin.done'))
  })

  it('reads a marketplace already added as fine, and a failed install as failed', async () => {
    const { offering: added } = offering({ exits: (argv) => (argv[2] === 'marketplace' ? 1 : 0) })
    expect(await offerPlugin(added)).toBe('installed')

    const { offering: broken, seen } = offering({
      exits: (argv) => (argv[2] === 'install' ? 3 : 0),
    })
    expect(await offerPlugin(broken)).toBe('failed')
    expect(seen.shown.at(-1)).toContain('exited 3')
  })
})
