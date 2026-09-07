import { describe, expect, it } from 'vitest'

import { candidateBoard, inTier } from './candidates'
import type { RecordedProject } from './catalogue'
import type { PickPayload } from './payloads'
import { pendingRow, readRow, unreadableRow, type ProjectRow } from './portfolio'

const project = (path: string): RecordedProject => ({
  path,
  aliases: [],
  commonDir: null,
  root: '/code',
  confirmed: '2026-09-01T10:00:00.000Z',
  presence: 'present',
})

const picked = (id: string | null, tier: string): PickPayload => ({
  pick:
    id === null
      ? null
      : { id, block: 'A', status: '📋', symptom: `what ${id} is about`, ref: id },
  tier,
  reason: 'because',
  ready: 4,
  blocked: 2,
  outside: 0,
  paused: 0,
})

const withPick = (path: string, id: string | null, tier: string): ProjectRow =>
  readRow(project(path), { pick: picked(id, tier) })

describe('RG19: the answers side by side', () => {
  it('takes one candidate per project that offered a line', () => {
    const board = candidateBoard([
      withPick('/code/a', 'RG1', 'in-progress'),
      withPick('/code/b', 'SH9', 'lowest-ready-id'),
    ])

    expect(board.candidates.map((entry) => entry.id)).toEqual(['RG1', 'SH9'])
    expect(board.candidates[0]?.project).toBe('/code/a')
    expect(board.candidates[0]?.name).toBe('a')
  })

  it('carries the tier each was chosen by', () => {
    const board = candidateBoard([withPick('/code/a', 'RG1', 'in-progress')])

    expect(board.candidates[0]?.tier).toBe('in-progress')
  })

  it('carries the block, the marker and the symptom the verb printed', () => {
    const board = candidateBoard([withPick('/code/a', 'RG1', 'priority')])

    expect(board.candidates[0]).toMatchObject({
      block: 'A',
      status: '📋',
      symptom: 'what RG1 is about',
    })
  })
})

describe('RG19: the order this app is allowed to impose', () => {
  it('is the recorded project order and nothing else', () => {
    // An invented total looks obviously derived. An invented ranking looks like advice,
    // which is why this is the more dangerous half of the same rule.
    const board = candidateBoard([
      withPick('/code/z', 'Z1', 'lowest-ready-id'),
      withPick('/code/a', 'A1', 'in-progress'),
      withPick('/code/m', 'M1', 'priority'),
    ])

    expect(board.candidates.map((entry) => entry.project)).toEqual([
      '/code/z',
      '/code/a',
      '/code/m',
    ])
  })

  it('does not put an in-progress line above a lowest-ready-id one', () => {
    const board = candidateBoard([
      withPick('/code/a', 'A1', 'lowest-ready-id'),
      withPick('/code/b', 'B1', 'in-progress'),
    ])

    // Which tier outranks which is roadkeep's, and this app was not told it.
    expect(board.candidates[0]?.tier).toBe('lowest-ready-id')
  })

  it('lists the tiers present without claiming an order between them', () => {
    const board = candidateBoard([
      withPick('/code/a', 'A1', 'lowest-ready-id'),
      withPick('/code/b', 'B1', 'in-progress'),
      withPick('/code/c', 'C1', 'lowest-ready-id'),
    ])

    // First appearance: derived from the data, so it is not a precedence dressed up.
    expect(board.tiers).toEqual(['lowest-ready-id', 'in-progress'])
  })
})

describe('RG19: filtering by a tier', () => {
  const board = candidateBoard([
    withPick('/code/a', 'A1', 'in-progress'),
    withPick('/code/b', 'B1', 'lowest-ready-id'),
    withPick('/code/c', 'C1', 'in-progress'),
  ])

  it('answers everything one tier chose, in project order', () => {
    expect(inTier(board, 'in-progress').map((entry) => entry.id)).toEqual(['A1', 'C1'])
  })

  it('answers nothing for a tier nothing was chosen by', () => {
    expect(inTier(board, 'priority')).toEqual([])
  })
})

describe('RG19: the projects with no candidate', () => {
  it('separates a backlog that offered nothing from one nobody read', () => {
    // A finished backlog and one that has not been read are different things, and a
    // screen that showed them the same way would hide the one worth acting on.
    const board = candidateBoard([
      withPick('/code/done', null, 'lowest-ready-id'),
      pendingRow(project('/code/waiting')),
      unreadableRow(project('/code/broken'), {
        reason: 'timeout',
        message: 'ran past 15000ms',
        said: '',
        elapsedMs: 15001,
        argv: [],
      }),
    ])

    expect(board.candidates).toEqual([])
    expect(board.nothingToPick).toEqual(['/code/done'])
    expect(board.unanswered).toEqual(['/code/waiting', '/code/broken'])
  })

  it('treats a row read without asking pick as unanswered', () => {
    const board = candidateBoard([readRow(project('/code/a'), {})])

    expect(board.unanswered).toEqual(['/code/a'])
    expect(board.nothingToPick).toEqual([])
  })

  it('answers an empty board for no projects', () => {
    expect(candidateBoard([])).toEqual({
      candidates: [],
      nothingToPick: [],
      unanswered: [],
      tiers: [],
    })
  })
})
