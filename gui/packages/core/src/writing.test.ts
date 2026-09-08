import { describe, expect, it } from 'vitest'

import { readAddedPayload, readSectionWritten } from './payloads'
import {
  EngineCallFailed,
  type EngineRequest,
  type EngineResult,
  type Transport,
} from './transport'
import { applied, applyWrite, composeWrite } from './writing'
import { EVERY_WRITE_INPUT, WRITES } from './writes'

/** Captured from a real `add --json` that landed. */
const ADDED = JSON.stringify({
  id: 'FX4',
  ref: 'FX4',
  file: 'docs/ROADMAP.md',
  line: 7,
  rendered: '- 📋 **FX4** (deps: —) **a write has no door here yet** — …',
  length: 139,
  section: {
    anchor: 'FX4',
    title: 'Why a write needs a door',
    level: 3,
    file: 'docs/IMPROVEMENTS.md',
    first: 20,
    last: 23,
    words: 21,
    own_words: 21,
  },
  near: [{ id: 'FX2', marker: '📋', symptom: 'nothing answers question 2 yet', line: 5, rank: 1 }],
  near_recorded: 0,
})

/** Captured from a real `add --json` the engine refused. */
const REFUSED = JSON.stringify({
  refused: [
    {
      code: 'symptom.too-long',
      field: 'symptom',
      bound: '',
      message:
        '130 characters, limit is 120 (roadkeep.toml:19 [limits].symptom): delete 10 characters',
    },
  ],
  beside: '',
  about: '',
  said: 'roadkeep: refused, nothing written:\n  symptom: 130 characters…',
})

function answering(stdout: string, code = 0): { transport: Transport; calls: EngineRequest[] } {
  const calls: EngineRequest[] = []
  return {
    calls,
    transport: {
      run(request) {
        calls.push(request)
        const answer: EngineResult = { code, stdout, stderr: '', durationMs: 3 }
        return Promise.resolve(answer)
      },
    },
  }
}

function failing(reason: 'unspawnable' | 'timeout'): Transport {
  return {
    run(request) {
      return Promise.reject(
        new EngineCallFailed(reason, `\`${request.argv.join(' ')}\` did not answer`, 15000),
      )
    },
  }
}

describe('RG29: the app composes an argv and the command writes', () => {
  it('builds the whole command line and runs nothing', () => {
    const composed = composeWrite('/w/proj', 'add', {
      block: 'D',
      symptom: 'a write has no door',
      why: 'The app composes an argv and the command writes.',
    })

    expect(composed.argv).toEqual([
      '-C',
      '/w/proj',
      'add',
      '--block',
      'D',
      '--symptom',
      'a write has no door',
      '--why',
      'The app composes an argv and the command writes.',
      '--json',
    ])
    expect(composed.verb).toBe('add')
    expect(composed.root).toBe('/w/proj')
  })

  it('files the line and the section its pointer needs in one call', () => {
    // A line whose section is missing is a `ref.unresolved` finding the moment it is
    // written, so the follow-up belongs in the call that creates the need for it.
    const composed = composeWrite('/w', 'add', {
      block: 'D',
      symptom: 's',
      why: 'W.',
      section: 'A heading',
      sectionBody: 'Prose.',
    })

    expect(composed.argv).toContain('--section')
    expect(composed.argv).toContain('--section-body')
    expect(composed.argv.indexOf('--section-body')).toBeGreaterThan(
      composed.argv.indexOf('--section'),
    )
  })

  it('repeats a flag per dep rather than joining them into one argument', () => {
    const composed = composeWrite('/w', 'add', {
      block: 'D',
      symptom: 's',
      why: 'W.',
      deps: ['RG1', 'Block C'],
      requires: ['signing-cert'],
    })

    expect(composed.argv.filter((part) => part === '--dep')).toHaveLength(2)
    expect(composed.argv).toContain('Block C')
    expect(composed.argv).toContain('--requires')
  })

  it('leaves out a flag whose input is absent rather than sending an empty one', () => {
    const composed = composeWrite('/w', 'add', { block: 'D', symptom: 's', why: 'W.' })

    expect(composed.argv).not.toContain('--status')
    expect(composed.argv).not.toContain('--dep')
    expect(composed.argv).not.toContain('--section')
  })

  it('passes prose through as one argument, whatever is in it', () => {
    // Never a shell string: an argv is an array, and a symptom with a backtick and a
    // semicolon in it is one element of it.
    const symptom = 'a `backtick`; and a $dollar, and "quotes"'
    const composed = composeWrite('/w', 'add', { block: 'D', symptom, why: 'W.' })

    expect(composed.argv).toContain(symptom)
    expect(composed.argv.filter((part) => part === symptom)).toHaveLength(1)
  })

  it('asks for the machine-readable form on every write', () => {
    // A refusal read as prose is a refusal whose field nobody can mark. Driven off
    // `EVERY_WRITE_INPUT` so a write added to the table cannot skip this.
    for (const verb of Object.keys(WRITES) as (keyof typeof WRITES)[]) {
      const composed = composeWrite('/w', verb, EVERY_WRITE_INPUT[verb])

      expect(composed.argv).toContain('--json')
      expect(composed.argv.slice(0, 2)).toEqual(['-C', '/w'])
    }
  })
})

describe('RG29: a write ends in three states and no more', () => {
  it('is applied, with the verb own payload', async () => {
    const { transport, calls } = answering(ADDED)
    const outcome = await applyWrite(
      transport,
      composeWrite('/w', 'add', { block: 'D', symptom: 's', why: 'W.' }),
      readAddedPayload,
    )

    expect(outcome.kind).toBe('applied')
    expect(applied(outcome)).toBe(true)
    if (outcome.kind !== 'applied') throw new Error('unreachable')
    expect(outcome.value.id).toBe('FX4')
    expect(outcome.value.section?.title).toBe('Why a write needs a door')
    expect(outcome.value.near[0]?.rank).toBe(1)
    expect(calls[0]?.argv).toContain('add')
  })

  it('is refused, with the fields the engine named', async () => {
    const { transport } = answering(REFUSED)
    const outcome = await applyWrite(
      transport,
      composeWrite('/w', 'add', { block: 'D', symptom: 's', why: 'W.' }),
      readAddedPayload,
    )

    expect(outcome.kind).toBe('refused')
    expect(applied(outcome)).toBe(false)
    if (outcome.kind !== 'refused') throw new Error('unreachable')
    expect(outcome.refusal.refused[0]?.code).toBe('symptom.too-long')
    expect(outcome.refusal.refused[0]?.field).toBe('symptom')
  })

  it('reads a refusal by what it says and never by the exit code', async () => {
    // `lint` exits 1 with an ordinary payload, so an exit code cannot be the
    // discriminator. A refusal that exits 0 is still a refusal.
    const zero = answering(REFUSED, 0)
    const one = answering(ADDED, 1)
    const composed = composeWrite('/w', 'add', { block: 'D', symptom: 's', why: 'W.' })

    expect((await applyWrite(zero.transport, composed, readAddedPayload)).kind).toBe('refused')
    expect((await applyWrite(one.transport, composed, readAddedPayload)).kind).toBe('applied')
  })

  it('is unreadable when the call never happened, and says which argv', async () => {
    const outcome = await applyWrite(
      failing('unspawnable'),
      composeWrite('/w', 'add', { block: 'D', symptom: 's', why: 'W.' }),
      readAddedPayload,
    )

    expect(outcome.kind).toBe('unreadable')
    if (outcome.kind !== 'unreadable') throw new Error('unreachable')
    expect(outcome.unreadable.reason).toBe('unspawnable')
    expect(outcome.unreadable.argv).toContain('add')
  })

  it('is unreadable rather than refused when a write times out', async () => {
    // The state that matters: whether it landed is unknown, and calling that a refusal
    // would promise nothing was written when nobody can say that.
    const outcome = await applyWrite(
      failing('timeout'),
      composeWrite('/w', 'add', { block: 'D', symptom: 's', why: 'W.' }),
      readAddedPayload,
    )

    expect(outcome.kind).toBe('unreadable')
    if (outcome.kind !== 'unreadable') throw new Error('unreachable')
    expect(outcome.unreadable.reason).toBe('timeout')
    expect(outcome.unreadable.elapsedMs).toBe(15000)
  })

  it('is unreadable when the answer is neither a payload nor a refusal', async () => {
    const { transport } = answering('not json at all')
    const outcome = await applyWrite(
      transport,
      composeWrite('/w', 'add', { block: 'D', symptom: 's', why: 'W.' }),
      readAddedPayload,
    )

    expect(outcome.kind).toBe('unreadable')
    if (outcome.kind !== 'unreadable') throw new Error('unreachable')
    expect(outcome.unreadable.reason).toBe('unreadable-payload')
    expect(outcome.unreadable.message).toContain('add')
  })

  it('RG79: shows what the engine said where the refusal never became a payload', async () => {
    // `section amend --replace` with a fragment that does not match writes this and
    // leaves stdout empty. Without it the person reads "answered with nothing on stdout"
    // where the engine had named the fragment and pointed at the verb printing the prose.
    const said =
      'roadkeep: --replace names one occurrence and §FX1 does not carry ' +
      "'a phrase this prose never contained': check the spelling against `section show`"
    const calls: EngineRequest[] = []
    const transport: Transport = {
      run(request) {
        calls.push(request)
        return Promise.resolve({ code: 1, stdout: '', stderr: said, durationMs: 4 })
      },
    }

    const outcome = await applyWrite(
      transport,
      composeWrite('/w', 'sectionAmend', {
        anchor: 'FX1',
        fragment: { replace: 'a phrase this prose never contained', replacement: 'x' },
      }),
      readSectionWritten,
    )

    expect(outcome.kind).toBe('unreadable')
    if (outcome.kind !== 'unreadable') throw new Error('unreachable')
    expect(outcome.unreadable.said).toBe(said)
    expect(outcome.unreadable.message).toBe(said)
  })
})
