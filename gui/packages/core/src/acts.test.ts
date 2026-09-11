import { describe, expect, it } from 'vitest'

import {
  actLine,
  actsIn,
  actsOf,
  governedIn,
  isRoadkeep,
  marksOf,
  NOTHING_MARKED,
  subjectOf,
  touched,
  type Marks,
} from './acts'

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
