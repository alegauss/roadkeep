import { describe, expect, it } from 'vitest'

import { commandLine, createTranscript, entryLine, quoteFor } from './transcript'
import type { WriteOutcome } from './writing'
import { composeWrite } from './writing'

const applied: WriteOutcome<{ id: string }> = {
  kind: 'applied',
  value: { id: 'RG34' },
  durationMs: 412,
  code: 0,
}

const refused: WriteOutcome<{ id: string }> = {
  kind: 'refused',
  refusal: { refused: [], beside: '', about: '', said: 'roadkeep: refused' },
  durationMs: 88,
  // Exit 0 with a refusal, which is the pair worth seeing side by side.
  code: 0,
}

const unreadable: WriteOutcome<{ id: string }> = {
  kind: 'unreadable',
  unreadable: {
    reason: 'timeout',
    message: 'ran past 15000ms',
    elapsedMs: 15001,
    argv: [],
    said: '',
  },
}

describe('RG34: an argument quoted for the shell it is going to', () => {
  it('leaves a plain word alone, so a command reads as a command', () => {
    expect(quoteFor('add', 'posix')).toBe('add')
    expect(quoteFor('--block', 'posix')).toBe('--block')
    expect(quoteFor('docs/ROADMAP.md', 'posix')).toBe('docs/ROADMAP.md')
    expect(quoteFor('RG34', 'powershell')).toBe('RG34')
  })

  it('quotes anything with a space in it', () => {
    expect(quoteFor('a symptom in words', 'posix')).toBe("'a symptom in words'")
    expect(quoteFor('a symptom in words', 'powershell')).toBe("'a symptom in words'")
  })

  it('escapes a quote the way each shell does, which is why the shell is named', () => {
    // POSIX closes, escapes and reopens. PowerShell doubles it. One rendering that worked
    // in neither would be worse than none.
    expect(quoteFor("it's here", 'posix')).toBe(String.raw`'it'\''s here'`)
    expect(quoteFor("it's here", 'powershell')).toBe("'it''s here'")
  })

  it('quotes an empty argument, which a bare rendering would lose entirely', () => {
    // `--with ''` is how a fragment is deleted. Dropped, the command means something else.
    expect(quoteFor('', 'posix')).toBe("''")
    expect(quoteFor('', 'powershell')).toBe("''")
  })

  it('quotes a shell metacharacter rather than trusting it', () => {
    for (const argument of ['a && b', 'a; b', '$HOME', '`whoami`', 'a|b', 'a>b']) {
      expect(quoteFor(argument, 'posix').startsWith("'")).toBe(true)
    }
  })

  it('leaves prose the file would hold alone where it needs no quoting', () => {
    expect(quoteFor('one.two-three_four', 'posix')).toBe('one.two-three_four')
  })
})

describe('RG34: the command, as a line to paste', () => {
  it('renders the whole argv with the program in front', () => {
    const composed = composeWrite('/w/proj', 'add', {
      block: 'D',
      symptom: "a write cannot be read before it's run",
      why: 'A person approving it has only the app word.',
    })

    expect(commandLine(composed)).toBe(
      "roadkeep -C /w/proj add --block D --symptom 'a write cannot be read before it'\\''s run' " +
        "--why 'A person approving it has only the app word.' --json",
    )
  })

  it('renders the same command for PowerShell, differing only in the escape', () => {
    const composed = composeWrite('/w', 'add', {
      block: 'D',
      symptom: "it's one",
      why: 'A sentence.',
    })

    expect(commandLine(composed, 'powershell')).toContain("'it''s one'")
    expect(commandLine(composed, 'powershell')).not.toContain(String.raw`\'`)
  })

  it('quotes a Windows path, because an unquoted backslash is an escape', () => {
    // Not only for the space: a backslash left bare in a POSIX shell escapes what follows
    // it, and inside single quotes both shells take the whole path literally.
    const composed = composeWrite('C:\\Users\\a b\\proj', 'status', { id: 'RG1', marker: '🛠' })

    expect(commandLine(composed, 'powershell')).toContain("'C:\\Users\\a b\\proj'")
    expect(commandLine(composed, 'posix')).toContain("'C:\\Users\\a b\\proj'")
    expect(quoteFor('C:\\Users\\proj', 'posix')).toBe("'C:\\Users\\proj'")
  })

  it('takes the program name, because the argv starts at -C', () => {
    // What is actually run is an interpreter and a script path. A person pasting this
    // wants the name they would type.
    const composed = composeWrite('/w', 'repair', { dryRun: true })

    expect(commandLine(composed, 'posix', 'rk')).toBe('rk -C /w repair --dry-run --json')
  })
})

describe('RG34: the transcript, ordered and in memory', () => {
  it('numbers what ran, so a log says which came first', () => {
    const composed = composeWrite('/w', 'status', { id: 'RG1', marker: '🛠' })
    const log = createTranscript().remember(composed, applied).remember(composed, refused)

    expect(log.entries.map((one) => one.seq)).toEqual([1, 2])
    expect(log.entries.map((one) => one.ran)).toEqual(['applied', 'refused'])
  })

  it('keeps the argv it ran, so the entry is reproducible', () => {
    const composed = composeWrite('/w', 'defer', { id: 'RG1', reason: 'Waiting.' })
    const log = createTranscript().remember(composed, applied)

    expect(log.entries[0]?.argv).toEqual(composed.argv)
    expect(commandLine({ ...composed, argv: log.entries[0]!.argv })).toContain('defer')
  })

  it('shows the exit code beside the outcome and not instead of it', () => {
    // A write refused with exit 0 is exactly the pair worth seeing: the code answers one
    // question and the outcome another.
    const composed = composeWrite('/w', 'add', { block: 'A', symptom: 's', why: 'W.' })
    const log = createTranscript().remember(composed, refused)

    expect(log.entries[0]?.code).toBe(0)
    expect(log.entries[0]?.ran).toBe('refused')
    expect(entryLine(log.entries[0]!)).toContain('refused  exit 0')
  })

  it('has no exit code for a call that never got one', () => {
    const composed = composeWrite('/w', 'add', { block: 'A', symptom: 's', why: 'W.' })
    const log = createTranscript().remember(composed, unreadable)

    expect(log.entries[0]?.code).toBeNull()
    expect(log.entries[0]?.durationMs).toBe(15001)
    expect(entryLine(log.entries[0]!)).toContain('no exit')
  })

  it('carries what the engine said where the answer could not be read', () => {
    const composed = composeWrite('/w', 'sectionAmend', { anchor: 'RG1' })
    const log = createTranscript().remember(composed, {
      ...unreadable,
      unreadable: { ...unreadable.unreadable, said: 'roadkeep: --replace names one occurrence' },
    })

    expect(log.entries[0]?.said).toContain('--replace names one occurrence')
  })

  it('does not grow without end, because this is memory and not a store', () => {
    const composed = composeWrite('/w', 'status', { id: 'RG1', marker: '🛠' })
    let log = createTranscript()
    for (let index = 0; index < 250; index += 1) log = log.remember(composed, applied)

    expect(log.entries).toHaveLength(200)
    // The newest are what is kept, and the numbering does not restart.
    expect(log.entries[0]?.seq).toBe(51)
    expect(log.entries.at(-1)?.seq).toBe(250)
  })

  it('leaves the transcript it was given alone, so an entry cannot be lost', () => {
    const composed = composeWrite('/w', 'status', { id: 'RG1', marker: '🛠' })
    const before = createTranscript().remember(composed, applied)
    before.remember(composed, applied)

    expect(before.entries).toHaveLength(1)
  })
})
