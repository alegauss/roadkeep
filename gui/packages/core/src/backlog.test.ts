import { describe, expect, it } from 'vitest'

import { allLines, backlogFrom, refusedSummary } from './backlog'
import type { ListPayload, RefusedLine, TaskLine } from './payloads'

const task = (id: string, block: string, line: number): TaskLine => ({
  id,
  status: '📋',
  block,
  symptom: `what ${id} is about`,
  why: 'A reason.',
  deps: [],
  ref: id,
  line,
  length: 100,
})

const refused = (line: number, block: string, reason: string): RefusedLine => ({
  line,
  block,
  reason,
  raw: `- 📋 something the grammar refused at line ${String(line)}`,
})

const listing = (over: Partial<ListPayload> = {}): ListPayload => ({
  file: 'docs/ROADMAP.md',
  total: 3,
  uncounted: [],
  standing: null,
  startable: null,
  over: null,
  tasks: [task('RG1', 'A', 5), task('RG2', 'A', 6), task('RG9', 'B', 20)],
  ...over,
})

describe('RG21: the lines, in the order the file has them', () => {
  it('groups by block in heading order, not alphabetically', () => {
    // `brief` says a line is under block C. A screen that sorted C above A would make
    // that sentence wrong.
    const backlog = backlogFrom(
      listing({ tasks: [task('RG9', 'Z', 5), task('RG1', 'A', 20)] }),
    )

    expect(backlog.blocks.map((block) => block.block)).toEqual(['Z', 'A'])
  })

  it('keeps the ids under a block in the order they arrived', () => {
    const backlog = backlogFrom(listing())

    expect(backlog.blocks[0]?.lines.map((line) => line.id)).toEqual(['RG1', 'RG2'])
    expect(backlog.blocks[1]?.lines.map((line) => line.id)).toEqual(['RG9'])
  })

  it('flattens back to the same order it was given', () => {
    expect(allLines(backlogFrom(listing())).map((line) => line.id)).toEqual([
      'RG1',
      'RG2',
      'RG9',
    ])
  })

  it('carries the file and the count the listing reported', () => {
    const backlog = backlogFrom(listing())

    expect(backlog.file).toBe('docs/ROADMAP.md')
    expect(backlog.total).toBe(3)
  })

  it('carries the standing when the listing was scoped to a block', () => {
    const backlog = backlogFrom(
      listing({
        standing: {
          block: 'A',
          state: 'live',
          sentence: 'Block A has 2 open',
          open: 2,
          recorded: 0,
          paused: 0,
        },
      }),
    )

    expect(backlog.standing?.sentence).toBe('Block A has 2 open')
  })
})

describe('RG21: the half a listing would otherwise hide', () => {
  it('is complete when nothing was refused', () => {
    const backlog = backlogFrom(listing())

    expect(backlog.complete).toBe(true)
    expect(backlog.refused).toEqual([])
  })

  it('is not complete when a line carried a marker the grammar refused', () => {
    // A line with a marker that no verb can read is invisible to every count and every
    // pick, while sitting in the file looking exactly like the ones that work.
    const backlog = backlogFrom(
      listing({ uncounted: [refused(8, 'A', 'no bold **<id>** after the marker')] }),
    )

    expect(backlog.complete).toBe(false)
    expect(backlog.refused).toHaveLength(1)
  })

  it('puts a refused line under the block the engine placed it in', () => {
    const backlog = backlogFrom(
      listing({ uncounted: [refused(8, 'A', 'no bold **<id>** after the marker')] }),
    )

    expect(backlog.blocks[0]?.refused).toHaveLength(1)
    expect(backlog.blocks[0]?.refused[0]?.line).toBe(8)
    expect(backlog.unplaced).toEqual([])
  })

  it('shows a refused line no block could be worked out for, rather than dropping it', () => {
    const backlog = backlogFrom(
      listing({ uncounted: [refused(2, '', 'no bold **<id>** after the marker')] }),
    )

    expect(backlog.unplaced).toHaveLength(1)
    expect(backlog.blocks.some((block) => block.refused.length > 0)).toBe(false)
    // Still in the whole list: unplaced is a placement, not an exclusion.
    expect(backlog.refused).toHaveLength(1)
  })

  it('opens a block that has only refused lines in it', () => {
    const backlog = backlogFrom(
      listing({ tasks: [], total: 0, uncounted: [refused(9, 'C', 'no marker this grammar knows')] }),
    )

    expect(backlog.blocks.map((block) => block.block)).toEqual(['C'])
    expect(backlog.blocks[0]?.lines).toEqual([])
  })

  it('carries the raw line, so a person can go and find it', () => {
    const backlog = backlogFrom(listing({ uncounted: [refused(8, 'A', 'no bold id')] }))

    expect(backlog.refused[0]?.raw).toContain('line 8')
  })
})

describe('RG21: saying a listing is narrower than its file', () => {
  it('says nothing when nothing was refused', () => {
    expect(refusedSummary(backlogFrom(listing()))).toBe('')
  })

  it('names the count, the file and every distinct reason', () => {
    const backlog = backlogFrom(
      listing({
        uncounted: [
          refused(8, 'A', 'no bold **<id>** after the marker'),
          refused(12, 'B', 'no bold **<id>** after the marker'),
          refused(30, '', 'a marker this project does not declare'),
        ],
      }),
    )

    const summary = refusedSummary(backlog)

    expect(summary).toContain('3 lines')
    expect(summary).toContain('docs/ROADMAP.md')
    expect(summary).toContain('no bold')
    expect(summary).toContain('does not declare')
  })

  it('agrees with itself when there is only one', () => {
    // Prose somebody reads. "1 lines carry" is the kind of thing that makes a person
    // trust the rest of the screen a little less.
    const summary = refusedSummary(backlogFrom(listing({ uncounted: [refused(8, 'A', 'no bold id')] })))

    expect(summary).toContain('1 line in')
    expect(summary).toContain('carries')
    expect(summary).toContain('picks it:')
    expect(summary).not.toContain('1 lines')
  })

  it('does not repeat a reason that applies to several lines', () => {
    const backlog = backlogFrom(
      listing({ uncounted: [refused(8, 'A', 'same reason'), refused(9, 'A', 'same reason')] }),
    )

    expect(refusedSummary(backlog).match(/same reason/g)).toHaveLength(1)
  })
})

describe('RG21: an empty backlog', () => {
  it('has no blocks and is complete', () => {
    const backlog = backlogFrom(listing({ tasks: [], total: 0 }))

    expect(backlog.blocks).toEqual([])
    expect(backlog.complete).toBe(true)
  })
})
