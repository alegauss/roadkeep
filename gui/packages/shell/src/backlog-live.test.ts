import { appendFileSync } from 'node:fs'
import path from 'node:path'

import { allLines, backlogFrom, refusedSummary, type Backlog } from '@rk/core'
import { afterAll, beforeAll, describe, expect, it } from 'vitest'

import { liveEngine as engine, read, REPO } from './live'
import { buildFixture, type Fixture } from './fixture'

/**
 * A real backlog read out of a real file, including the half that is easy to lose: a
 * marker-bearing line the grammar refuses. That line is written by hand into the fixture
 * on purpose — it is exactly what a person editing a governed file by mistake produces,
 * and it is the case a listing must not quietly drop.
 */

let fixture: Fixture

async function backlogOf(root: string, input = {}): Promise<Backlog> {
  return backlogFrom(await read(root, 'list', input))
}

beforeAll(async () => {
  fixture = await buildFixture(engine, { open: 4, shipped: 1, deferred: 1 })
}, 180000)

afterAll(() => {
  fixture.dispose()
})

describe('RG21: a real backlog', () => {
  it('opens this repository into blocks with lines under them', async () => {
    const backlog = await backlogOf(REPO)

    expect(backlog.file).toContain('ROADMAP.md')
    expect(backlog.blocks.length).toBeGreaterThan(1)
    expect(allLines(backlog).length).toBe(backlog.total)
  })

  it('keeps the blocks in the order the headings run', async () => {
    const backlog = await backlogOf(REPO)
    const seen = backlog.blocks.map((block) => block.block)

    // This repository declares A through H in that order, and the listing speaks in it.
    expect(seen).toEqual([...seen].sort())
    expect(seen[0]).toBe('A')
  })

  it('narrows to one block and reports that block standing', async () => {
    const backlog = await backlogOf(REPO, { block: 'A' })

    expect(backlog.blocks.map((block) => block.block)).toEqual(['A'])
    expect(backlog.standing?.block).toBe('A')
    expect(backlog.standing?.sentence).toContain('Block A')
  })

  it('reads a listing of another governed role', async () => {
    const backlog = await backlogOf(fixture.root, { role: 'changelog' })

    expect(backlog.file).toContain('CHANGELOG.md')
    expect(allLines(backlog).length).toBeGreaterThan(0)
  })
})

describe('RG21: a line the grammar refuses', () => {
  it('is drawn rather than dropped, with the reason and the raw text', async () => {
    const before = await backlogOf(fixture.root)
    expect(before.complete).toBe(true)

    appendFileSync(
      path.join(fixture.root, 'docs', 'ROADMAP.md'),
      '\n- 📋 this line has a marker and no id at all\n',
      'utf8',
    )

    const after = await backlogOf(fixture.root)

    expect(after.complete).toBe(false)
    expect(after.refused).toHaveLength(1)
    expect(after.refused[0]?.raw).toContain('no id at all')
    expect(after.refused[0]?.reason).not.toBe('')
    expect(after.refused[0]?.line).toBeGreaterThan(0)
  })

  it('does not count toward the total, which is the whole danger', async () => {
    // It is in the file, it has a marker, and every count and every pick steps over it.
    const backlog = await backlogOf(fixture.root)

    expect(allLines(backlog).length).toBe(backlog.total)
    expect(backlog.refused.length).toBeGreaterThan(0)
  })

  it('turns into a sentence naming the file and the reason', async () => {
    const summary = refusedSummary(await backlogOf(fixture.root))

    expect(summary).toContain('ROADMAP.md')
    expect(summary).toContain('1 line in')
    expect(summary).toContain('carries')
  })
})
