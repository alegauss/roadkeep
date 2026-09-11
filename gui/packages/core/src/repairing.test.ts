import { describe, expect, it } from 'vitest'

import { readLintPayload, readRepairPayload } from './payloads'
import { readDoor, type Door } from './refusals'
import {
  actionableFrom,
  actionableReport,
  anyRunnable,
  gatedReport,
  offerOf,
  passFrom,
  saidOfPass,
  type Actionable,
} from './repairing'
import { composeDoor } from './writing'

/** Captured from a real `lint --json` on a line whose pointer resolves to nothing. */
const LINT = {
  root: '/p',
  clean: false,
  checked: ['docs/ROADMAP.md', 'docs/IMPROVEMENTS.md'],
  lines: 1,
  sections: 0,
  problems: 1,
  codes: { 'ref.unresolved': 1 },
  findings: [
    {
      code: 'ref.unresolved',
      file: 'docs/ROADMAP.md',
      line: 5,
      column: null,
      id: 'FX1',
      message: 'points at §FX1, which is not in docs/IMPROVEMENTS.md',
      remedy: {
        kind: 'compose',
        decision: '',
        sequence: false,
        awaits: '',
        doors: [
          {
            argv: ['section', 'add', 'FX1', '--title', '…'],
            what: 'the line points at a section that does not exist',
            complete: false,
            writes: true,
          },
        ],
      },
    },
  ],
  notes: [],
}

/** Captured from a real `repair --dry-run --json`. */
const DRY = {
  root: '/p',
  clean: false,
  dry_run: true,
  passes: 0,
  exhausted: false,
  steps: [],
  left: [
    {
      code: 'ref.unresolved',
      where: 'docs/ROADMAP.md:5',
      message: 'points at §FX1, which is not in docs/IMPROVEMENTS.md',
      remedy: {
        kind: 'compose',
        decision: '',
        sequence: false,
        awaits: '',
        doors: [
          {
            argv: ['section', 'add', 'FX1', '--title', '…'],
            what: 'the line points at a section that does not exist',
            complete: false,
            writes: true,
          },
        ],
      },
    },
  ],
}

function door(over: Record<string, unknown> = {}) {
  const parsed = readDoor(
    { argv: ['renumber'], what: 'renumber the ids', complete: true, writes: true, ...over },
    '',
  )
  if (!parsed.ok) throw new Error('the fixture does not match the shape')
  return parsed.value
}

function lint(over: Record<string, unknown> = {}) {
  const parsed = readLintPayload({ ...LINT, ...over }, '')
  if (!parsed.ok) throw new Error(`the fixture does not match the shape: ${parsed.failure.path}`)
  return parsed.value
}

function repair(over: Record<string, unknown> = {}) {
  const parsed = readRepairPayload({ ...DRY, ...over }, '')
  if (!parsed.ok) throw new Error(`the fixture does not match the shape: ${parsed.failure.path}`)
  return parsed.value
}

describe('RG33: a door sorted on the engine word', () => {
  it('offers a complete door as one that runs as it stands', () => {
    const offer = offerOf(door())

    expect(offer.kind).toBe('run')
  })

  it('offers an incomplete door as a form, naming the blanks', () => {
    const offer = offerOf(door({ argv: ['section', 'add', '…', '--title', '…'], complete: false }))

    expect(offer.kind).toBe('fill')
    if (offer.kind !== 'fill') throw new Error('unreachable')
    expect(offer.blanks).toEqual([2, 4])
  })

  it('sorts on complete and never on the placeholders', () => {
    // A complete door with a sentinel in a value is still complete, and a screen must not
    // go looking for a form. `complete` is the authority and the blanks are decoration.
    const offer = offerOf(
      door({ argv: ['amend', 'RG1', '--why', 'it ended in …'], complete: true }),
    )

    expect(offer.kind).toBe('run')
  })

  it('leaves the blanks empty for an incomplete door that shows none', () => {
    // A changed sentinel costs the highlighting and never turns a form into a command.
    const offer = offerOf(door({ argv: ['section', 'add', '<id>'], complete: false }))

    expect(offer.kind).toBe('fill')
    if (offer.kind !== 'fill') throw new Error('unreachable')
    expect(offer.blanks).toEqual([])
  })
})

describe('RG33: a door argv is the engine own', () => {
  it('adds where to run it, and nothing else', () => {
    const composed = composeDoor('/w/proj', door({ argv: ['renumber', '--from', 'RG40'] }))

    expect(composed.argv).toEqual(['-C', '/w/proj', 'renumber', '--from', 'RG40', '--json'])
    expect(composed.verb).toBe('renumber')
  })

  it('carries a two-word verb through without touching it', () => {
    // No table lookup and no spelling: whatever the engine put in the array goes out.
    const composed = composeDoor('/w', door({ argv: ['section', 'add', 'FX1', '--title', 'A'] }))

    expect(composed.argv.slice(2, 4)).toEqual(['section', 'add'])
    expect(composed.verb).toBe('section')
  })

  it('composes an incomplete door too, placeholders and all', () => {
    // Composing is not running. `complete` is what a caller checks before it runs one.
    const composed = composeDoor('/w', door({ argv: ['section', 'add', '…'], complete: false }))

    expect(composed.argv).toContain('…')
  })
})

describe('RG33: a report a screen can act on', () => {
  it('turns each finding into where it is and what closes it', () => {
    const report = actionableReport(lint())

    expect(report).toHaveLength(1)
    expect(report[0]?.code).toBe('ref.unresolved')
    expect(report[0]?.where).toBe('docs/ROADMAP.md:5')
    expect(report[0]?.id).toBe('FX1')
    expect(report[0]?.offers[0]?.kind).toBe('fill')
  })

  it('names a finding about a whole file without a line nobody can go to', () => {
    const one = actionableFrom({
      code: 'engine.disagreement',
      file: '.',
      line: null,
      column: null,
      id: null,
      message: 'this gate is a modified checkout',
      remedy: null,
    })

    expect(one.where).toBe('.')
    expect(one.id).toBe('')
    expect(one.offers).toEqual([])
  })

  it('carries what a person has to settle before any door helps', () => {
    const report = actionableReport(
      lint({
        findings: [
          {
            ...LINT.findings[0],
            remedy: {
              kind: 'decide',
              decision: 'whether the line was replaced or abandoned',
              sequence: true,
              awaits: 'a decision that is not this project',
              doors: [],
            },
          },
        ],
      }),
    )

    expect(report[0]?.decision).toContain('replaced or abandoned')
    expect(report[0]?.awaits).toContain('not this project')
    expect(report[0]?.sequence).toBe(true)
  })

  it('says whether anything can be closed without somebody typing first', () => {
    // A report whose every finding wants prose is one a repair pass cannot advance, and
    // offering the pass would spend a confirmation on nothing.
    expect(anyRunnable(actionableReport(lint()))).toBe(false)

    const fixable = lint({
      findings: [
        {
          ...LINT.findings[0],
          remedy: {
            kind: 'compose',
            decision: '',
            sequence: false,
            awaits: '',
            doors: [{ argv: ['renumber'], what: 'renumber', complete: true, writes: true }],
          },
        },
      ],
    })
    expect(anyRunnable(actionableReport(fixable))).toBe(true)
  })
})

describe('RG33: a repair pass, offered dry first', () => {
  it('reads a dry run as one that ran nothing', () => {
    const pass = passFrom(repair())

    expect(pass.dry).toBe(true)
    expect(pass.steps).toEqual([])
    expect(pass.left).toHaveLength(1)
    expect(saidOfPass(pass)).toBe('dry run: 0 step(s), 1 left')
  })

  it('reads what it left in the same shape a finding arrives in', () => {
    // One reader for the gate and its repair: a screen handling them separately offers
    // the door in one place and not the other.
    const pass = passFrom(repair())

    expect(pass.left[0]?.code).toBe('ref.unresolved')
    expect(pass.left[0]?.where).toBe('docs/ROADMAP.md:5')
    expect(pass.left[0]?.offers[0]?.kind).toBe('fill')
  })

  it('says what a real pass did, and whether it finished the job', () => {
    const pass = passFrom(
      repair({
        dry_run: false,
        clean: true,
        passes: 2,
        steps: [{ code: 'ref.unresolved', argv: ['renumber'], what: 'renumbered', ran: true }],
        left: [],
      }),
    )

    expect(pass.dry).toBe(false)
    expect(pass.clean).toBe(true)
    expect(saidOfPass(pass)).toBe('1 step(s), 0 left — clean')
  })

  it('says when the passes stopped helping rather than stopping clean', () => {
    const pass = passFrom(repair({ dry_run: false, clean: false, passes: 3, exhausted: true }))

    expect(saidOfPass(pass)).toContain('stopped helping')
  })
})

describe('RG152: numbering a report against the batch the far side kept', () => {
  const offered = (argv: readonly string[]) => {
    const read = readDoor({ argv, what: '', complete: true, writes: false }, 'door')
    if (!read.ok) throw new Error('the fixture is not a door')
    return read.value
  }

  /** A finding with nothing on it but the one door under test. */
  const row = (one: Door): Actionable => ({
    code: 'ref.unresolved',
    where: '',
    message: '',
    id: '',
    decision: '',
    awaits: '',
    sequence: false,
    offers: [offerOf(one)],
  })

  it('names each door by where it sits in the batch, not by where its row does', () => {
    // The batch is every door the answer carried, in document order, and a note's door
    // ahead of the findings is exactly what shifts the numbers a screen would have guessed.
    const batch = [offered(['explain', 'x']), offered(['section', 'add', 'FX1', '--title', '…'])]
    const [first] = gatedReport(actionableReport(lint()), batch)

    expect(first?.doors).toHaveLength(1)
    expect(first?.doors[0]?.which).toBe(1)
  })

  it('gives two rows offering one argv the two places it has, and not the first twice', () => {
    const same = ['repair']
    const batch = [offered(same), offered(same)]
    const rows = gatedReport([row(offered(same)), row(offered(same))], batch)

    expect(rows.map((one) => one.doors[0]?.which)).toEqual([0, 1])
  })

  it('offers no door the batch has no place for, since nothing could run it', () => {
    const rows = gatedReport([row(offered(['repair']))], [])

    expect(rows[0]?.doors).toEqual([])
  })
})
