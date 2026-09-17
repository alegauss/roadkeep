import { describe, expect, it } from 'vitest'

import { readBriefPayload, type BriefPayload } from './payloads'
import { outcomeOf, promptFor, readSessionLine, resumeCall, sessionCall } from './session'

/** Captured from a real `brief --json`, trimmed to the keys the shape declares. */
const RAW = {
  id: 'RG38',
  status: '🛠',
  block: 'F',
  symptom: 'nothing starts Claude Code',
  why: 'The loop this app is for ends in an agent working the line.',
  deps: ['RG1 ✅', 'RG23 ✅'],
  requires: [],
  ref: 'RG38',
  section: {
    anchor: 'RG38',
    title: 'What a session is handed, and what starts it',
    level: 3,
    file: 'docs/IMPROVEMENTS.md',
    first: 491,
    last: 515,
    words: 240,
    own_words: 240,
    body: 'Claude Code runs headless.',
  },
  section_absence: '',
  readiness: 'ready',
  picked: 'lowest ready id',
  deps_resolved: [{ dep: 'RG1', kind: 'task', status: 'shipped', detail: 'in the changelog' }],
  unblocks: { count: 4, of: 45, transitive: ['RG40'], transitive_elided: 0 },
  non_goals: ['No write to a governed file'],
  non_goals_elided: 0,
  done_when: ['A session starts from a brief, not from a prompt somebody typed'],
  done_when_elided: 0,
  held: [],
  landed: [],
}

function brief(over: Record<string, unknown> = {}): BriefPayload {
  const parsed = readBriefPayload({ ...RAW, ...over }, '')
  if (!parsed.ok) throw new Error(`the fixture does not match the shape: ${parsed.failure.path}`)
  return parsed.value
}

/** Captured from a real `claude -p … --output-format stream-json --verbose`. */
const INIT = JSON.stringify({
  type: 'system',
  subtype: 'init',
  cwd: 'D:\\Git\\alegauss\\roadkeep-gui',
  session_id: '8ece7463-132d-4cdc-8d4d-c34a7a5d7e0a',
  tools: ['Bash', 'Read', 'Write'],
  model: 'claude-opus-5[1m]',
  claude_code_version: '2.1.263',
})

const SAID = JSON.stringify({
  type: 'assistant',
  message: { role: 'assistant', content: [{ type: 'text', text: 'Working RG38 now.' }] },
  session_id: '8ece7463',
})

const DONE = JSON.stringify({
  type: 'result',
  subtype: 'success',
  is_error: false,
  result: 'shipped RG38',
  num_turns: 7,
  duration_ms: 42000,
  session_id: '8ece7463',
})

describe('RG38: a session starts from a brief, not from a prompt somebody typed', () => {
  it('frames the payload rather than describing the task in its own words', () => {
    const prompt = promptFor(brief())

    expect(prompt).toContain('RG38')
    // The payload goes in whole. Re-composing it in English would be this app
    // paraphrasing the tool.
    expect(prompt).toContain('"readiness": "ready"')
    expect(prompt).toContain('What a session is handed, and what starts it')
    expect(prompt).toContain('A session starts from a brief')
  })

  it('carries the design, the deps and what binds the line, because the brief did', () => {
    const prompt = promptFor(brief())

    expect(prompt).toContain('No write to a governed file')
    // Each dep with what resolved it, not a list of bare ids — the join `brief` made.
    expect(prompt).toContain('"depsResolved"')
    expect(prompt).toContain('in the changelog')
    expect(prompt).toContain('"unblocks"')
  })

  it('says the payload was not rewritten, because that is the claim it makes', () => {
    expect(promptFor(brief())).toContain('verbatim')
  })
})

describe('RG38: the call, and nothing beside it', () => {
  it('describes a new session as what it is told, and continues nothing', () => {
    // The flags are the Agent SDK's since RG273: what `core` hands over is what was decided.
    expect(sessionCall('claude', '/w/proj', 'do the thing')).toEqual({
      command: 'claude',
      prefix: [],
      cwd: '/w/proj',
      prompt: 'do the thing',
      resume: '',
      allowed: [],
    })
  })

  it('runs in the project root, so the project own wiring answers', () => {
    // Its `roadkeep.toml`, its guard, its skill, its `.mcp.json`.
    expect(sessionCall('claude', '/w/proj', 'x').cwd).toBe('/w/proj')
  })

  it('passes no configuration at all', () => {
    // No model, no permission mode, no extra directory, no system prompt of its own: each would
    // be this app deciding something the project or the person already decides. The call has no
    // field for any of them to go in.
    expect(Object.keys(sessionCall('claude', '/w', 'x')).sort()).toEqual([
      'allowed',
      'command',
      'cwd',
      'prefix',
      'prompt',
      'resume',
    ])
  })

  it('takes the command from the caller and never looks for one', () => {
    // Which `claude` answers is a question about provenance, and it is RG43's.
    expect(sessionCall('/opt/claude/bin/claude', '/w', 'x').command).toBe('/opt/claude/bin/claude')
  })

  it('hands over a whole JSON prompt as it was framed, newlines and quotes included', () => {
    const prompt = promptFor(brief())

    expect(sessionCall('claude', '/w', prompt).prompt).toBe(prompt)
  })
})

describe('RG38: one line of the stream', () => {
  it('reads the init line as the session naming itself', () => {
    const event = readSessionLine(INIT)

    expect(event?.kind).toBe('started')
    if (event?.kind !== 'started') throw new Error('unreachable')
    expect(event.sessionId).toBe('8ece7463-132d-4cdc-8d4d-c34a7a5d7e0a')
    expect(event.model).toBe('claude-opus-5[1m]')
    expect(event.version).toBe('2.1.263')
    expect(event.tools).toContain('Bash')
  })

  it('reads an assistant turn as what it said', () => {
    const event = readSessionLine(SAID)

    expect(event?.kind).toBe('said')
    if (event?.kind !== 'said') throw new Error('unreachable')
    expect(event.text).toBe('Working RG38 now.')
  })

  it('reads the result as the session own verdict', () => {
    const event = readSessionLine(DONE)

    expect(event?.kind).toBe('finished')
    if (event?.kind !== 'finished') throw new Error('unreachable')
    expect(event.ok).toBe(true)
    expect(event.result).toBe('shipped RG38')
    expect(event.turns).toBe(7)
    expect(event.durationMs).toBe(42000)
  })

  it('reads a failed result as failed, off is_error and not off a code', () => {
    const event = readSessionLine(
      JSON.stringify({ type: 'result', is_error: true, result: 'ran out of turns' }),
    )

    expect(event?.kind).toBe('finished')
    if (event?.kind !== 'finished') throw new Error('unreachable')
    expect(event.ok).toBe(false)
  })

  it('names a kind it has no use for, rather than dropping it', () => {
    // Dropping these would make the reader lie about how much of the stream it saw.
    const event = readSessionLine(JSON.stringify({ type: 'rate_limit_event', foo: 1 }))

    expect(event?.kind).toBe('other')
    if (event?.kind !== 'other') throw new Error('unreachable')
    expect(event.type).toBe('rate_limit_event')
    expect(event.line).toContain('rate_limit_event')
  })

  it('tells a line it could not read from one it read and ignored', () => {
    // Null is a line this app could not read; `other` is one it read and has no use for.
    // Conflating them reports a healthy session as producing garbage.
    expect(readSessionLine('not json at all')).toBeNull()
    expect(readSessionLine('')).toBeNull()
    expect(readSessionLine('   ')).toBeNull()
    expect(readSessionLine('[1,2,3]')).toBeNull()
    expect(readSessionLine(JSON.stringify({ type: 'user' }))?.kind).toBe('other')
  })

  it('reads an assistant turn with no text as other, not as an empty thing said', () => {
    const event = readSessionLine(
      JSON.stringify({
        type: 'assistant',
        message: { content: [{ type: 'tool_use', name: 'Bash' }] },
      }),
    )

    expect(event?.kind).toBe('other')
  })
})

describe('RG38: where a session ended up', () => {
  const events = [readSessionLine(INIT)!, readSessionLine(SAID)!, readSessionLine(DONE)!]

  it('is done when the session said so', () => {
    const outcome = outcomeOf(events, { code: 0, cancelled: false, said: '' })

    expect(outcome.state).toBe('done')
    expect(outcome.sessionId).toBe('8ece7463')
    expect(outcome.result).toBe('shipped RG38')
  })

  it('believes the result line over the exit code', () => {
    // The session's own verdict. A run that finished badly says so there, and the code is
    // the fallback for one that stopped without saying anything.
    const failed = [
      events[0]!,
      readSessionLine(JSON.stringify({ type: 'result', is_error: true, result: 'no' }))!,
    ]

    expect(outcomeOf(failed, { code: 0, cancelled: false, said: '' }).state).toBe('failed')
    expect(outcomeOf(events, { code: 1, cancelled: false, said: '' }).state).toBe('done')
  })

  it('is cancelled when the window stopped it, whatever else it had said', () => {
    const outcome = outcomeOf(events, { code: null, cancelled: true, said: '' })

    expect(outcome.state).toBe('cancelled')
    // It still knows which session it was, which is what a screen has to show afterwards.
    expect(outcome.sessionId).toBe('8ece7463')
  })

  it('is failed when it stopped without ever saying how it went', () => {
    const outcome = outcomeOf([events[0]!], {
      code: 2,
      cancelled: false,
      said: 'something on stderr',
    })

    expect(outcome.state).toBe('failed')
    expect(outcome.code).toBe(2)
    expect(outcome.said).toBe('something on stderr')
  })

  it('has no session id where the session never named one', () => {
    expect(outcomeOf([], { code: 1, cancelled: false, said: '' }).sessionId).toBe('')
  })
})

describe('RG268: an ended turn is not a finished task', () => {
  /** commitclerk's T65 ended its turn like this: a clean end, and the Edit it asked for refused. */
  const ASKED = JSON.stringify({
    type: 'result',
    subtype: 'success',
    is_error: false,
    result: 'I need permission to edit docs/IMPROVEMENTS.md, and a choice between two remedies.',
    num_turns: 12,
    duration_ms: 90000,
    session_id: 'c0ffee',
    permission_denials: [
      {
        tool_name: 'Edit',
        tool_use_id: 'toolu_01',
        tool_input: { file_path: 'docs/IMPROVEMENTS.md', old_string: 'a', new_string: 'b' },
      },
    ],
  })

  it('reads the calls a result line says were refused, as the engine wrote them', () => {
    const event = readSessionLine(ASKED)

    if (event?.kind !== 'finished') throw new Error('not a result')
    expect(event.denials).toEqual([
      {
        tool: 'Edit',
        callId: 'toolu_01',
        input: { file_path: 'docs/IMPROVEMENTS.md', old_string: 'a', new_string: 'b' },
      },
    ])
    // The engine still calls it a success, which is exactly why it cannot be read as done.
    expect(event.ok).toBe(true)
  })

  it('is waiting, not done, where the turn ended with a call refused', () => {
    const outcome = outcomeOf([readSessionLine(ASKED)!], {
      code: 0,
      cancelled: false,
      said: '',
    })

    expect(outcome.state).toBe('waiting')
    expect(outcome.denials.map((denial) => denial.tool)).toEqual(['Edit'])
  })

  it('is done where nothing was refused, and carries an empty list rather than none', () => {
    const outcome = outcomeOf([readSessionLine(DONE)!], { code: 0, cancelled: false, said: '' })

    expect(outcome.state).toBe('done')
    expect(outcome.denials).toEqual([])
  })

  it('stays failed where the turn erred, with what it was refused beside it', () => {
    const erred = JSON.stringify({ ...JSON.parse(ASKED), is_error: true })
    const outcome = outcomeOf([readSessionLine(erred)!], { code: 1, cancelled: false, said: '' })

    expect(outcome.state).toBe('failed')
    expect(outcome.denials).toHaveLength(1)
  })

  it('keeps no denial that names no tool, since nothing could draw or grant it', () => {
    const odd = JSON.stringify({
      type: 'result',
      is_error: false,
      result: '',
      permission_denials: [{ tool_use_id: 'x' }, 'not a record', { tool_name: 'Bash' }],
    })
    const event = readSessionLine(odd)

    if (event?.kind !== 'finished') throw new Error('not a result')
    expect(event.denials.map((denial) => denial.tool)).toEqual(['Bash'])
  })
})

describe('RG269: the call that answers a session', () => {
  it('continues the session by its own id, from the same root', () => {
    const call = resumeCall('claude', '/w/proj', 's-42', 'The first one.')

    expect(call).toEqual({
      command: 'claude',
      prefix: [],
      cwd: '/w/proj',
      prompt: 'The first one.',
      resume: 's-42',
      allowed: [],
    })
  })

  it('sends the reply as written, whatever it begins with', () => {
    // Prose a person typed, and a reply that begins with a dash is still a reply.
    expect(resumeCall('claude', '/w/proj', 's-42', '--no, the second').prompt).toBe(
      '--no, the second',
    )
  })
})

describe('RG270: a grant is the person’s, for one turn', () => {
  it('names the tools the person allowed, once each, on that resumed turn and no other', () => {
    const call = resumeCall('claude', '/w/proj', 's-42', 'Go on.', ['Edit', 'Bash', 'Edit'])

    expect(call.allowed).toEqual(['Edit', 'Bash'])
    expect(sessionCall('claude', '/w/proj', 'x').allowed).toEqual([])
  })

  it('passes no grant where nothing was allowed', () => {
    expect(resumeCall('claude', '/w/proj', 's-42', 'Go on.').allowed).toEqual([])
  })
})
