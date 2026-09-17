import { describe, expect, it } from 'vitest'

import { actsIn } from './acts'
import {
  answeredBy,
  answerLine,
  askOf,
  asksIn,
  DECLINED,
  grantsOf,
  openAsks,
  type PermissionAsk,
} from './asking'
import { drawnState } from './landing'

/**
 * RG272: a question a running session asks, and the answer that goes back.
 *
 * The lines are the shapes Claude Code 2.1.274 wrote under `--permission-prompt-tool stdio`,
 * captured from a run: a `control_request` asking to use a tool, and the `control_response` the
 * host writes to its standard input. What is held is that a question is read with what the
 * engine offered, that an answer is composed out of the question and read back as the same
 * answer, and that where a question stands comes off the lines alone.
 */

const WRITE_ASK = JSON.stringify({
  type: 'control_request',
  request_id: '934b7299-9ff0-4e8b-b595-eb1602b003f1',
  request: {
    subtype: 'can_use_tool',
    tool_name: 'Write',
    display_name: 'Write',
    input: { file_path: 'work/hello.txt', content: 'hi' },
    description: 'hello.txt',
    permission_suggestions: [{ type: 'setMode', mode: 'acceptEdits', destination: 'session' }],
    tool_use_id: 'toolu_01Khie1EZqJgHr7AR7eegHu7',
  },
})

const BASH_ASK = JSON.stringify({
  type: 'control_request',
  request_id: 'ask-bash',
  request: {
    subtype: 'can_use_tool',
    tool_name: 'Bash',
    input: { command: 'npm test', description: 'Run the tests' },
    permission_suggestions: [
      {
        type: 'addRules',
        rules: [{ toolName: 'Bash', ruleContent: 'npm test:*' }],
        behavior: 'allow',
        destination: 'localSettings',
      },
    ],
    tool_use_id: 'toolu_bash',
  },
})

function asked(line: string): PermissionAsk {
  const ask = askOf(line)
  if (ask === null) throw new Error('not a question')
  return ask
}

describe('RG272: a question, as the engine asks it', () => {
  it('reads the tool, the call, the id it is answered by and what the engine offers', () => {
    expect(asked(WRITE_ASK)).toEqual({
      requestId: '934b7299-9ff0-4e8b-b595-eb1602b003f1',
      tool: 'Write',
      input: { file_path: 'work/hello.txt', content: 'hi' },
      description: 'hello.txt',
      callId: 'toolu_01Khie1EZqJgHr7AR7eegHu7',
      suggestions: [{ type: 'setMode', mode: 'acceptEdits', destination: 'session' }],
    })
  })

  it('reads no question out of a line that asks none', () => {
    expect(askOf('{"type":"assistant","message":{"content":[]}}')).toBeNull()
    expect(
      askOf('{"type":"control_request","request_id":"x","request":{"subtype":"interrupt"}}'),
    ).toBeNull()
    expect(askOf('not json')).toBeNull()
  })

  it('draws a question as an act of its own, on what the call is on', () => {
    const [act] = actsIn([BASH_ASK])

    expect(act?.kind).toBe('asked')
    if (act?.kind !== 'asked') return
    expect(act.ask.tool).toBe('Bash')
    expect(act.on).toBe('npm test')
  })

  it('says what allowing for the session grants, as the engine spelled it', () => {
    expect(grantsOf(asked(WRITE_ASK))).toEqual(['acceptEdits'])
    expect(grantsOf(asked(BASH_ASK))).toEqual(['Bash(npm test:*)'])
  })
})

describe('RG272: the answer that goes back', () => {
  it('allows the call with its own input, unchanged', () => {
    const line = answerLine(asked(WRITE_ASK), 'once')

    expect(JSON.parse(line)).toEqual({
      type: 'control_response',
      response: {
        subtype: 'success',
        request_id: '934b7299-9ff0-4e8b-b595-eb1602b003f1',
        response: {
          behavior: 'allow',
          updatedInput: { file_path: 'work/hello.txt', content: 'hi' },
        },
      },
    })
  })

  it('allows for the session with the engine suggestions, narrowed to the session', () => {
    // The project's local settings are the project's: an answer from this window is for this run.
    const line = answerLine(asked(BASH_ASK), 'session')

    expect(JSON.parse(line)).toMatchObject({
      response: {
        response: {
          behavior: 'allow',
          updatedPermissions: [
            {
              type: 'addRules',
              rules: [{ toolName: 'Bash', ruleContent: 'npm test:*' }],
              behavior: 'allow',
              destination: 'session',
            },
          ],
        },
      },
    })
    expect(line).not.toContain('localSettings')
  })

  it('declines with a sentence the agent reads', () => {
    expect(JSON.parse(answerLine(asked(WRITE_ASK), 'decline'))).toMatchObject({
      response: { response: { behavior: 'deny', message: DECLINED } },
    })
  })

  it('reads each answer back as the one that was given', () => {
    for (const answer of ['once', 'session', 'decline'] as const) {
      expect(answeredBy(answerLine(asked(WRITE_ASK), answer))).toEqual({
        requestId: '934b7299-9ff0-4e8b-b595-eb1602b003f1',
        answer,
      })
    }
    // The engine's own answer to an initialize is not an answer to a question.
    expect(
      answeredBy('{"type":"control_response","response":{"subtype":"success","request_id":"i"}}'),
    ).toBeNull()
  })
})

describe('RG272: where a question stands, off the lines', () => {
  it('is open until an answer or a withdrawal follows it', () => {
    const answered = answerLine(asked(WRITE_ASK), 'session')
    const withdrawn = JSON.stringify({ type: 'control_cancel_request', request_id: 'ask-bash' })

    expect(openAsks([WRITE_ASK, BASH_ASK]).map((ask) => ask.tool)).toEqual(['Write', 'Bash'])
    expect(asksIn([WRITE_ASK, BASH_ASK, answered, withdrawn]).map((one) => one.standing)).toEqual([
      'session',
      'withdrawn',
    ])
    expect(openAsks([WRITE_ASK, answered])).toEqual([])
  })

  it('draws a running session with an open question as asking, and nothing else as asking', () => {
    expect(drawnState('running', null, 1)).toBe('asking')
    expect(drawnState('running', null, 0)).toBe('running')
    // An ended session has nothing waiting on an answer, whatever its lines left open.
    expect(drawnState('failed', null, 1)).toBe('failed')
  })
})
