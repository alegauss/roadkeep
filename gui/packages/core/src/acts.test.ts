import { describe, expect, it } from 'vitest'

import {
  actLine,
  actsIn,
  actsOf,
  changeOf,
  CHANGE_LETTER,
  editedIn,
  editsOf,
  editStanding,
  foldedNotes,
  governedIn,
  isRoadkeep,
  marksOf,
  NOTHING_MARKED,
  onDisk,
  originOf,
  subjectOf,
  touched,
  type Edited,
  type Marks,
} from './acts'
import type { EditedFile } from './bridge'
// The captured run, as text: `core` has no filesystem in scope, so the fixture is imported
// the way `boundaries.test.ts` imports this package's own sources.
import EDIT_LINES from './captured/session-edits.jsonl?raw'

/** What this project's `config` and engine resolution would supply. */
const MARKS: Marks = {
  governed: ['docs/ROADMAP.md', 'docs/CHANGELOG.md', 'docs/IMPROVEMENTS.md'],
  engine: ['roadkeep', 'mcp__roadkeep__'],
}

/** Captured from a real `claude -p … --output-format stream-json --verbose`. */
const TOOL_USE = JSON.stringify({
  type: 'assistant',
  message: {
    role: 'assistant',
    content: [
      {
        type: 'tool_use',
        id: 'toolu_012det5yqz7857aQMkbcRPwY',
        name: 'Bash',
        input: { command: 'echo hello', description: 'Echo hello' },
      },
    ],
  },
})

const TOOL_RESULT = JSON.stringify({
  type: 'user',
  message: {
    content: [
      {
        tool_use_id: 'toolu_012det5yqz7857aQMkbcRPwY',
        type: 'tool_result',
        content: 'hello',
        is_error: false,
      },
    ],
  },
})

const THINKING = JSON.stringify({
  type: 'assistant',
  message: { content: [{ type: 'thinking', thinking: '', signature: 'EskDCrIBCBEYAipA' }] },
})

const SAID = JSON.stringify({
  type: 'assistant',
  message: { content: [{ type: 'text', text: 'Working it now.' }] },
})

describe('RG40: the stream as a sequence of acts', () => {
  it('reads a tool call as the tool and what it was called on', () => {
    // The pair somebody watching is actually watching for.
    const [act] = actsOf(TOOL_USE, 1, MARKS)

    expect(act?.kind).toBe('used')
    if (act?.kind !== 'used') throw new Error('unreachable')
    expect(act.tool).toBe('Bash')
    expect(act.on).toBe('echo hello')
    expect(act.id).toBe('toolu_012det5yqz7857aQMkbcRPwY')
    expect(actLine(act)).toBe('Bash  echo hello')
  })

  it('reads a tool result, and whether it failed', () => {
    const [act] = actsOf(TOOL_RESULT, 1, MARKS)

    expect(act?.kind).toBe('returned')
    if (act?.kind !== 'returned') throw new Error('unreachable')
    expect(act.id).toBe('toolu_012det5yqz7857aQMkbcRPwY')
    expect(act.ok).toBe(true)
    expect(act.text).toBe('hello')
  })

  it('marks a failed result rather than drawing it as an answer', () => {
    const failed = JSON.stringify({
      type: 'user',
      message: {
        content: [
          { tool_use_id: 't1', type: 'tool_result', content: 'no such file', is_error: true },
        ],
      },
    })
    const [act] = actsOf(failed, 1, MARKS)

    expect(act?.kind === 'returned' && act.ok).toBe(false)
    expect(actLine(act!)).toBe('failed: no such file')
  })

  it('reads text as text, and thinking as a note', () => {
    // Thinking arrives with its content empty and a signature beside it, so rendering it
    // would draw a blank turn.
    expect(actsOf(SAID, 1, MARKS)[0]?.kind).toBe('said')

    const [note] = actsOf(THINKING, 1, MARKS)
    expect(note?.kind).toBe('note')
    if (note?.kind !== 'note') throw new Error('unreachable')
    expect(note.about).toBe('thinking')
  })

  it('keeps one message with several parts as several acts, in order', () => {
    // Flattening them into one act would lose the order they happened in.
    const both = JSON.stringify({
      type: 'assistant',
      message: {
        content: [
          { type: 'text', text: 'First I will look.' },
          { type: 'tool_use', id: 't1', name: 'Read', input: { file_path: 'docs/ROADMAP.md' } },
        ],
      },
    })

    const acts = actsOf(both, 7, MARKS)
    expect(acts.map((act) => act.kind)).toEqual(['said', 'used'])
    expect(acts.map((act) => act.seq)).toEqual([7, 8])
  })

  it('names every other kind rather than dropping it', () => {
    for (const [line, about] of [
      [JSON.stringify({ type: 'rate_limit_event' }), 'rate_limit_event'],
      [JSON.stringify({ type: 'system', subtype: 'init' }), 'system'],
      [JSON.stringify({ type: 'result', is_error: false }), 'result'],
      [JSON.stringify({ foo: 1 }), 'unknown'],
    ] as const) {
      const [act] = actsOf(line, 1, MARKS)
      expect(act?.kind).toBe('note')
      expect(act?.kind === 'note' && act.about).toBe(about)
    }
  })

  it('notes a user line carrying no tool result, rather than losing it', () => {
    // The harness injects one of these to prompt a turn along. Returning nothing would
    // make the act list quietly shorter than the stream it was read from.
    const nudge = JSON.stringify({
      type: 'user',
      message: { content: [{ type: 'text', text: '[Please continue.]' }] },
    })
    const [act] = actsOf(nudge, 1, MARKS)

    expect(act?.kind).toBe('note')
    expect(act?.kind === 'note' && act.about).toBe('user')
    expect(act?.line).toBe(nudge)
  })

  it('reads nothing from a line that is not a JSON object', () => {
    expect(actsOf('not json', 1)).toEqual([])
    expect(actsOf('', 1)).toEqual([])
    expect(actsOf('[1,2]', 1)).toEqual([])
  })
})

describe('RG40: what a tool was called on', () => {
  it('takes the key that carries a subject, in the order they are looked for', () => {
    expect(subjectOf({ command: 'npm test', description: 'run it' })).toBe('npm test')
    expect(subjectOf({ file_path: 'docs/ROADMAP.md' })).toBe('docs/ROADMAP.md')
    expect(subjectOf({ pattern: '\\bRG\\d+' })).toBe('\\bRG\\d+')
    expect(subjectOf({ url: 'https://example.test' })).toBe('https://example.test')
  })

  it('names none rather than guessing, which loses a label and never a fact', () => {
    // The raw line is on every act, so a tool whose subject is under no known key still
    // draws — just without one.
    expect(subjectOf({ somethingNew: 'a value' })).toBe('')
    expect(subjectOf(null)).toBe('')
    expect(subjectOf('a string')).toBe('')

    const [act] = actsOf(
      JSON.stringify({
        type: 'assistant',
        message: { content: [{ type: 'tool_use', id: 't1', name: 'NewTool', input: { x: 1 } }] },
      }),
      1,
      MARKS,
    )
    expect(act?.kind === 'used' && act.on).toBe('')
    expect(actLine(act!)).toBe('NewTool')
    expect(act?.line).toContain('NewTool')
  })
})

describe('RG40: what this project counts as its own', () => {
  it('marks a roadkeep call by what the project said roadkeep looks like', () => {
    expect(isRoadkeep('Bash', 'roadkeep ship RG40 --why "…"', MARKS)).toBe(true)
    expect(isRoadkeep('mcp__roadkeep__ship', '', MARKS)).toBe(true)
    expect(isRoadkeep('Bash', 'npm test', MARKS)).toBe(false)
  })

  it('marks nothing where the project supplied nothing, and still draws the act', () => {
    // What a screen has before `config` has been read.
    const [act] = actsOf(TOOL_USE, 1, NOTHING_MARKED)

    expect(act?.kind === 'used' && act.roadkeep).toBe(false)
    expect(act?.kind === 'used' && act.governed).toEqual([])
    expect(actLine(act!)).toBe('Bash  echo hello')
  })

  it('names the governed files a call touched, from the ones config declared', () => {
    // Never a filename written here: which files are governed is the project's answer.
    expect(governedIn('roadkeep ship RG40', MARKS)).toEqual([])
    expect(governedIn('edit docs/ROADMAP.md and docs/CHANGELOG.md', MARKS)).toEqual([
      'docs/ROADMAP.md',
      'docs/CHANGELOG.md',
    ])
  })

  it('reads a Windows path as the same file', () => {
    expect(governedIn('docs\\ROADMAP.md', MARKS)).toEqual(['docs/ROADMAP.md'])
  })

  it('finds a governed file named anywhere in the call input', () => {
    const write = JSON.stringify({
      type: 'assistant',
      message: {
        content: [
          {
            type: 'tool_use',
            id: 't1',
            name: 'Write',
            input: { file_path: 'docs/IMPROVEMENTS.md', content: 'prose' },
          },
        ],
      },
    })
    const [act] = actsOf(write, 1, MARKS)

    expect(act?.kind === 'used' && act.governed).toEqual(['docs/IMPROVEMENTS.md'])
  })

  it('says which governed files a run has touched so far', () => {
    // The evidence that this session changed the backlog. Watching the files is RG42's.
    const acts = actsIn(
      [
        SAID,
        JSON.stringify({
          type: 'assistant',
          message: {
            content: [
              {
                type: 'tool_use',
                id: 't1',
                name: 'Bash',
                input: { command: 'roadkeep ship RG40' },
              },
              { type: 'tool_use', id: 't2', name: 'Read', input: { file_path: 'docs/ROADMAP.md' } },
              { type: 'tool_use', id: 't3', name: 'Read', input: { file_path: 'docs/ROADMAP.md' } },
            ],
          },
        }),
      ],
      MARKS,
    )

    expect(touched(acts)).toEqual(['docs/ROADMAP.md'])
    expect(acts.filter((act) => act.kind === 'used' && act.roadkeep)).toHaveLength(1)
  })
})

describe('RG40: the raw form stays reachable', () => {
  it('keeps the line on every act, whatever it made of it', () => {
    // A session that went wrong is diagnosed from what it emitted.
    for (const line of [SAID, TOOL_USE, TOOL_RESULT, THINKING]) {
      for (const act of actsOf(line, 1, MARKS)) expect(act.line).toBe(line)
    }
  })

  it('numbers a whole stream in the order it was emitted', () => {
    const acts = actsIn([SAID, THINKING, TOOL_USE, TOOL_RESULT], MARKS)

    expect(acts.map((act) => act.seq)).toEqual([1, 2, 3, 4])
    expect(acts.map((act) => act.kind)).toEqual(['said', 'note', 'used', 'returned'])
  })
})

describe('RG153: the marks of one open project', () => {
  it('reads the governed files off the opening and the engine name off its command', () => {
    const marks = marksOf({ roadmap: 'docs/ROADMAP.md', changelog: 'docs/CHANGELOG.md' }, [
      'python',
      'D:\\code\\alpha\\.claude\\hooks\\roadkeep-launch.py',
    ])

    expect(marks.governed).toEqual(['docs/ROADMAP.md', 'docs/CHANGELOG.md'])
    expect(marks.engine).toEqual(['roadkeep-launch', 'mcp__roadkeep__'])
  })

  it('marks a Bash call through the launcher and a call to the project server alike', () => {
    const marks = marksOf({}, ['python', '/home/a/.claude/hooks/roadkeep-launch.py'])

    expect(isRoadkeep('Bash', 'python .claude/hooks/roadkeep-launch.py lint', marks)).toBe(true)
    expect(isRoadkeep('mcp__roadkeep__brief', '', marks)).toBe(true)
    expect(isRoadkeep('Bash', 'npm test', marks)).toBe(false)
  })

  it('is the engine itself where it runs off PATH', () => {
    expect(marksOf({}, ['roadkeep']).engine).toEqual(['roadkeep', 'mcp__roadkeep__'])
  })

  it('marks nothing as roadkeep where no engine was resolved', () => {
    expect(marksOf({}, []).engine).toEqual([])
  })
})

describe('RG243: the files a session edited', () => {
  /** One assistant line holding these calls, each `[id, tool, input]`. */
  const calls = (...made: [string, string, Record<string, unknown>][]) =>
    JSON.stringify({
      type: 'assistant',
      message: {
        content: made.map(([id, name, input]) => ({ type: 'tool_use', id, name, input })),
      },
    })
  const answer = (id: string, failed: boolean) =>
    JSON.stringify({
      type: 'user',
      message: {
        content: [{ tool_use_id: id, type: 'tool_result', content: 'ok', is_error: failed }],
      },
    })

  it('groups the editing calls by path, in the order each file was first edited', () => {
    const acts = actsIn(
      [
        calls(
          ['e1', 'Edit', { file_path: 'src/a.ts', old_string: 'x', new_string: 'y' }],
          ['r1', 'Read', { file_path: 'src/b.ts' }],
          ['w1', 'Write', { file_path: 'src/b.ts', content: 'b' }],
        ),
        answer('e1', false),
        calls(['e2', 'MultiEdit', { file_path: 'src/a.ts', edits: [] }]),
        calls(['n1', 'NotebookEdit', { notebook_path: 'notes.ipynb', new_source: '' }]),
      ],
      MARKS,
    )

    const edited = editedIn(acts)
    // A read is not an edit, and a file edited twice is one row counting both.
    expect(edited.map((one) => [one.path, one.calls])).toEqual([
      ['src/a.ts', 2],
      ['src/b.ts', 1],
      ['notes.ipynb', 1],
    ])
    expect(edited[0]?.last).toBe(acts.find((act) => act.kind === 'used' && act.id === 'e2')?.seq)
  })

  it('says a file failed where the answer to its last call did, and not before one arrives', () => {
    const first = [
      calls(['e1', 'Edit', { file_path: 'src/a.ts' }]),
      answer('e1', true),
      calls(['e2', 'Edit', { file_path: 'src/a.ts' }]),
    ]

    // The last call has no answer yet, so the earlier failure is not what this file is at.
    expect(editedIn(actsIn(first, MARKS))[0]?.failed).toBe(false)
    expect(editedIn(actsIn([...first, answer('e2', true)], MARKS))[0]?.failed).toBe(true)
    expect(editedIn(actsIn([...first, answer('e2', false)], MARKS))[0]?.failed).toBe(false)
  })

  it('lists no file for a tool it does not know, which is still drawn in the stream', () => {
    const acts = actsIn([calls(['x1', 'Rewrite', { file_path: 'src/a.ts' }])], MARKS)

    expect(editedIn(acts)).toEqual([])
    expect(acts.map((act) => act.kind)).toEqual(['used'])
  })

  it('marks a governed file by its path, not by what the edit wrote into another', () => {
    const acts = actsIn(
      [
        calls(
          ['w1', 'Write', { file_path: 'docs/ROADMAP.md', content: 'a line' }],
          ['w2', 'Write', { file_path: 'README.md', content: 'see docs/ROADMAP.md' }],
        ),
      ],
      MARKS,
    )

    expect(editedIn(acts).map((one) => [one.path, one.governed])).toEqual([
      ['docs/ROADMAP.md', true],
      ['README.md', false],
    ])
  })
})

describe('RG244: an edited file against the disk', () => {
  const STARTED = '2026-09-15T10:00:00.000Z'
  const EDITED: Edited = {
    path: 'src/a.ts',
    calls: 1,
    last: 3,
    answered: true,
    failed: false,
    governed: false,
  }
  const at = (over: Partial<EditedFile> = {}): EditedFile => ({
    path: 'src/a.ts',
    shown: 'src/a.ts',
    inside: true,
    present: true,
    changed: '2026-09-15T10:05:00.000Z',
    ...over,
  })

  it('says whether the last call has been answered, apart from whether it failed', () => {
    const acts = actsIn(
      [
        JSON.stringify({
          type: 'assistant',
          message: {
            content: [
              { type: 'tool_use', id: 'e1', name: 'Edit', input: { file_path: 'src/a.ts' } },
              { type: 'tool_use', id: 'e2', name: 'Edit', input: { file_path: 'src/b.ts' } },
            ],
          },
        }),
        JSON.stringify({
          type: 'user',
          message: { content: [{ tool_use_id: 'e1', type: 'tool_result', content: 'ok' }] },
        }),
      ],
      MARKS,
    )

    expect(editedIn(acts).map((one) => [one.path, one.answered, one.failed])).toEqual([
      ['src/a.ts', true, false],
      ['src/b.ts', false, false],
    ])
  })

  it('reads a file the disk changed after the session started as changed', () => {
    expect(onDisk(EDITED, at(), STARTED)).toEqual({ standing: 'changed', disagrees: false })
  })

  it('finds the disagreement: a call reported success and the disk has not changed the file', () => {
    const before = at({ changed: '2026-09-15T09:00:00.000Z' })

    expect(onDisk(EDITED, before, STARTED)).toEqual({ standing: 'unchanged', disagrees: true })
    expect(onDisk(EDITED, at({ present: false, changed: '' }), STARTED)).toEqual({
      standing: 'missing',
      disagrees: true,
    })
    // A call that failed, or has not answered, reported nothing to disagree with.
    expect(onDisk({ ...EDITED, failed: true }, before, STARTED).disagrees).toBe(false)
    expect(onDisk({ ...EDITED, answered: false }, before, STARTED).disagrees).toBe(false)
  })

  it('names a path outside the root, and one the disk has not answered for, without a verdict', () => {
    expect(onDisk(EDITED, at({ inside: false, present: false, changed: '' }), STARTED)).toEqual({
      standing: 'outside',
      disagrees: false,
    })
    expect(onDisk(EDITED, undefined, STARTED)).toEqual({ standing: 'unasked', disagrees: false })
  })

  it('never calls a file unchanged against a start it cannot read', () => {
    const before = at({ changed: '2026-09-15T09:00:00.000Z' })

    expect(onDisk(EDITED, before, '').standing).toBe('changed')
  })
})

describe('RG246: what the session changed inside a file', () => {
  const call = (id: string, name: string, input: Record<string, unknown>) =>
    JSON.stringify({
      type: 'assistant',
      message: { content: [{ type: 'tool_use', id, name, input }] },
    })
  const failed = (id: string) =>
    JSON.stringify({
      type: 'user',
      message: {
        content: [{ tool_use_id: id, type: 'tool_result', content: 'no match', is_error: true }],
      },
    })

  it('reads each tool’s own shape: a pair, a list of pairs, and a whole content', () => {
    const acts = actsIn(
      [
        call('e1', 'Edit', { file_path: 'src/a.ts', old_string: 'one', new_string: 'two' }),
        call('e2', 'MultiEdit', {
          file_path: 'src/a.ts',
          edits: [
            { old_string: 'three', new_string: 'four' },
            { old_string: 'five', new_string: 'six' },
          ],
        }),
        call('w1', 'Write', { file_path: 'src/a.ts', content: 'the whole file' }),
      ],
      MARKS,
    )

    expect(editsOf(acts, 'src/a.ts').map((one) => [one.tool, one.before, one.after])).toEqual([
      ['Edit', 'one', 'two'],
      ['MultiEdit', 'three', 'four'],
      ['MultiEdit', 'five', 'six'],
      // A write replaces whatever was there, so it has no before of its own.
      ['Write', '', 'the whole file'],
    ])
  })

  it('answers about one file, in the order the stream made the calls', () => {
    const acts = actsIn(
      [
        call('e1', 'Edit', { file_path: 'src/b.ts', old_string: 'x', new_string: 'y' }),
        call('e2', 'Edit', { file_path: 'src/a.ts', old_string: 'a', new_string: 'b' }),
        call('r1', 'Read', { file_path: 'src/a.ts' }),
      ],
      MARKS,
    )

    expect(editsOf(acts, 'src/a.ts').map((one) => one.seq)).toEqual([2])
  })

  it('says which edits failed, and draws no block for an input it does not know', () => {
    const acts = actsIn(
      [
        call('e1', 'Edit', { file_path: 'src/a.ts', old_string: 'one', new_string: 'two' }),
        failed('e1'),
        call('n1', 'NotebookEdit', { notebook_path: 'src/a.ts', cell_id: '1' }),
      ],
      MARKS,
    )

    const edits = editsOf(acts, 'src/a.ts')
    expect(edits).toHaveLength(1)
    expect(edits[0]?.failed).toBe(true)
    expect(edits[0]?.answered).toBe(true)
    // The call is still an act with its raw line, which is the fallback and not a loss.
    expect(acts.filter((act) => act.kind === 'used')).toHaveLength(2)
  })

  it('looks for what an edit put there in the text that was read', () => {
    const edit = {
      seq: 1,
      tool: 'Edit',
      before: 'one',
      after: 'two',
      answered: true,
      failed: false,
    }

    expect(editStanding(edit, 'const two = 2\n')).toBe('in-the-file')
    expect(editStanding(edit, 'const one = 1\n')).toBe('not-in-the-file')
    // Nothing to look in, and nothing to look for: neither is a verdict.
    expect(editStanding(edit, null)).toBe('unchecked')
    expect(editStanding({ ...edit, after: '' }, 'anything')).toBe('unchecked')
  })
})

describe('RG208: notes folded where they stand', () => {
  const INIT = JSON.stringify({ type: 'system', subtype: 'init', session_id: 's' })
  const LIMIT = JSON.stringify({ type: 'rate_limit_event' })
  const FAILED = JSON.stringify({
    type: 'user',
    message: {
      content: [{ tool_use_id: 't', type: 'tool_result', content: 'no', is_error: true }],
    },
  })

  /** The rows as kinds, a folded run spelled by how many notes it carries. */
  const shape = (lines: string[]) =>
    foldedNotes(actsIn(lines)).map((row) =>
      row.kind === 'act' ? row.act.kind : `folded:${String(row.notes.length)}`,
    )

  it('folds each run of consecutive notes into one row, in the place the run stood', () => {
    expect(shape([INIT, LIMIT, SAID, THINKING, TOOL_USE, LIMIT])).toEqual([
      'folded:2',
      'said',
      'folded:1',
      'used',
      'folded:1',
    ])
  })

  it('accounts for every act, so the rows are never quietly shorter than the stream', () => {
    const acts = actsIn([INIT, LIMIT, SAID, THINKING, TOOL_USE, TOOL_RESULT, LIMIT])
    const counted = foldedNotes(acts).reduce(
      (sum, row) => sum + (row.kind === 'act' ? 1 : row.notes.length),
      0,
    )

    expect(counted).toBe(acts.length)
  })

  it('never folds a result, a failure or anything the session said', () => {
    expect(shape([SAID, TOOL_RESULT, FAILED])).toEqual(['said', 'returned', 'returned'])
  })

  it('draws nothing for a stream that wrote nothing', () => {
    expect(foldedNotes([])).toEqual([])
  })
})

/**
 * RG280: what the session did to each file, off the answers a real run wrote.
 *
 * `captured/session-edits.jsonl` is one headless run — a `Write` on a path that was not there,
 * an `Edit` on it, and a `Write` over a file that was — kept as it printed but for the usage
 * accounting. What it proves is that this reader handles the shapes Claude Code answered with
 * on the day it was captured: a `type` of `create` or `update` on a `Write`, and `originalFile`
 * on an `Edit`.
 */
const CAPTURED_EDITS = EDIT_LINES.split('\n').filter((line) => line.trim() !== '')

/** The paths that run's calls carried, spelled as the machine it ran on spells one. */
const NEW_FILE = String.raw`D:\tmp\rk-capture\new.txt`
const OLD_FILE = String.raw`D:\tmp\rk-capture\old.txt`
const NEVER_EDITED = String.raw`D:\tmp\rk-capture\never.txt`

describe('RG280: created, changed or deleted', () => {
  const acts = actsIn(CAPTURED_EDITS)

  it('reads a created file off the answer to the call that made it', () => {
    expect(originOf(acts, NEW_FILE)).toBe('created')
  })

  it('reads a changed file off the answer to the write that replaced it', () => {
    expect(originOf(acts, OLD_FILE)).toBe('changed')
  })

  it('takes the first answered call on the path, so a later edit does not restate it', () => {
    // `new.txt` was written and then edited: created is what the session did to it, and the
    // `Edit` answering with the file it replaced does not make it a file that was there.
    const edited = editedIn(acts).find((file) => file.path.endsWith('new.txt'))

    expect(edited?.calls).toBe(2)
    expect(originOf(acts, NEW_FILE)).toBe('created')
  })

  it('says nothing about a path no call named, or one nothing has answered yet', () => {
    expect(originOf(acts, NEVER_EDITED)).toBeNull()
    // The call alone, with its answer left out of the stream.
    const unanswered = actsIn(CAPTURED_EDITS.filter((line) => !line.includes('tool_use_result')))
    expect(originOf(unanswered, NEW_FILE)).toBeNull()
  })

  it('does not read a line answering two calls, since one payload cannot say whose it is', () => {
    const doubled = CAPTURED_EDITS.map((line) => {
      const object: unknown = JSON.parse(line)
      const record = object as { message?: { content?: unknown[] } }
      const content = record.message?.content
      if (!Array.isArray(content) || content[0] === undefined) return line
      const part = content[0] as { type?: string }
      if (part.type !== 'tool_result') return line
      return JSON.stringify({
        ...(object as object),
        message: {
          ...record.message,
          content: [content[0], { ...content[0], type: 'tool_result' }],
        },
      })
    })

    expect(originOf(actsIn(doubled), NEW_FILE)).toBeNull()
  })

  it('lets the disk finish it: gone is deleted, and gone after being made is its own word', () => {
    expect(changeOf('changed', 'missing')).toBe('deleted')
    expect(changeOf('created', 'missing')).toBe('undone')
    expect(changeOf('created', 'changed')).toBe('created')
    expect(changeOf('changed', 'unchanged')).toBe('changed')
    // Outside the project the disk is never asked, and the session's own answer stands.
    expect(changeOf('created', 'outside')).toBe('created')
    expect(changeOf(null, 'missing')).toBeNull()
  })

  it('marks each change with the letter a source-control list marks it with', () => {
    expect(CHANGE_LETTER.created).toBe('A')
    expect(CHANGE_LETTER.changed).toBe('M')
    expect(CHANGE_LETTER.deleted).toBe('D')
    expect(new Set(Object.values(CHANGE_LETTER)).size).toBe(4)
  })
})
