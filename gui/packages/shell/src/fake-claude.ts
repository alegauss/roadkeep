import { mkdtempSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import path from 'node:path'

import { removeTree } from './scratch'

/**
 * A `claude` that is not Claude, for testing the process half of a session.
 *
 * A real headless session costs money and does work, so nothing in this suite starts one.
 * What it does start is a Node script that writes the same `stream-json` lines a real one
 * writes — captured from an actual run — and then exits however the test asked it to.
 *
 * That is enough to prove the part this app owns: the argv it spawns, lines assembled
 * across chunk boundaries, an owned process that can be killed, and each of the three
 * failures becoming a state. What it cannot prove is that Claude Code still emits those
 * lines, and nothing here pretends otherwise — the shapes are asserted against a captured
 * run and go stale the way any recorded fixture does.
 */

export interface FakeClaude {
  /** The interpreter to spawn, which is this process's own Node. */
  readonly command: string
  /** Arguments that come before the session's own, so the script runs. */
  readonly prefixArgs: readonly string[]
  dispose: () => void
}

export interface FakeBehaviour {
  /** Exit with this code once the lines are out. */
  readonly exitCode?: number
  /** Say the run failed, in the result line the session itself writes. */
  readonly failing?: boolean
  /** Write nothing and stay up, so a test can kill it. */
  readonly hanging?: boolean
  /** Write a line that is not JSON, which a reader has to tell from one it ignores. */
  readonly garbage?: boolean
  /** Split every line across two writes, so the reader has to assemble them. */
  readonly chunked?: boolean
  /**
   * Run as a session under `--input-format stream-json` does (RG272): read the prompt off standard
   * input and say it back, ask one question, end the turn with the answer it was given as its
   * result — and exit only when standard input closes, which a real one does too.
   */
  readonly asking?: boolean
}

/** The question an asking fake puts, shaped as Claude Code writes one. */
export const FAKE_ASK = {
  type: 'control_request',
  request_id: 'fake-ask',
  request: {
    subtype: 'can_use_tool',
    tool_name: 'Write',
    input: { file_path: 'notes.md', content: 'hi' },
    description: 'notes.md',
    permission_suggestions: [{ type: 'setMode', mode: 'acceptEdits', destination: 'session' }],
    tool_use_id: 'fake-call',
  },
}

/** The lines, as a captured run wrote them. */
function script(behaviour: FakeBehaviour): string {
  const lines = [
    {
      type: 'system',
      subtype: 'init',
      cwd: '<cwd>',
      session_id: 'fake-0001',
      tools: ['Bash', 'Read', 'Write'],
      model: 'claude-opus-5[1m]',
      claude_code_version: '2.1.263',
    },
    { type: 'rate_limit_event', rate_limit_info: { status: 'allowed' } },
    {
      type: 'assistant',
      message: { role: 'assistant', content: [{ type: 'text', text: 'Working it now.' }] },
      session_id: 'fake-0001',
    },
    {
      type: 'result',
      subtype: behaviour.failing === true ? 'error_during_execution' : 'success',
      is_error: behaviour.failing === true,
      result: behaviour.failing === true ? 'ran out of turns' : 'done',
      // A failed run lists what went wrong, and the Agent SDK reads the list (RG273).
      ...(behaviour.failing === true ? { errors: ['ran out of turns'] } : {}),
      num_turns: 3,
      duration_ms: 1234,
      session_id: 'fake-0001',
    },
  ]

  return [
    "import { createInterface } from 'node:readline'",
    'const argv = process.argv.slice(2)',
    // The session's own cwd, so a test can prove the process ran where it was told to.
    `const lines = ${JSON.stringify(lines)}`,
    'lines[0].cwd = process.cwd()',
    'const write = (value) => process.stdout.write(JSON.stringify(value) + "\\n")',
    `if (${String(behaviour.asking === true)}) {`,
    '  let prompted = false',
    '  const input = createInterface({ input: process.stdin })',
    "  input.on('line', (line) => {",
    '    const message = JSON.parse(line)',
    // The Agent SDK opens with `initialize` (RG273), and a real session answers it first.
    "    if (message.type === 'control_request' && message.request.subtype === 'initialize') {",
    "      write({ type: 'control_response', response: { subtype: 'success', request_id: message.request_id, response: {} } })",
    '      return',
    '    }',
    "    if (!prompted && message.type === 'user') {",
    '      prompted = true',
    '      write(lines[0])',
    // A message's content is a string or a list of parts, and the prompt is said back as its text.
    '      const content = message.message.content',
    "      const text = typeof content === 'string' ? content : content.map((part) => part.text ?? '').join('')",
    "      write({ type: 'assistant', message: { role: 'assistant', content: [{ type: 'text', text }] }, session_id: 'fake-0001' })",
    `      write(${JSON.stringify(FAKE_ASK)})`,
    '      return',
    '    }',
    "    if (message.type === 'control_response') {",
    '      const answer = message.response.response',
    "      write({ type: 'result', subtype: 'success', is_error: false, result: answer.behavior, num_turns: 1, duration_ms: 1, session_id: 'fake-0001' })",
    '    }',
    '  })',
    // Only closing standard input ends it, so a test that hangs is a session never let go of.
    "  input.on('close', () => process.exit(0))",
    `} else if (${String(behaviour.hanging === true)}) { setInterval(() => {}, 1000) } else {`,
    `  if (${String(behaviour.garbage === true)}) process.stdout.write('not json at all\\n')`,
    '  for (const line of lines) {',
    '    const text = JSON.stringify(line) + "\\n"',
    `    if (${String(behaviour.chunked === true)}) {`,
    '      const cut = Math.floor(text.length / 2)',
    '      process.stdout.write(text.slice(0, cut))',
    '      process.stdout.write(text.slice(cut))',
    '    } else {',
    '      process.stdout.write(text)',
    '    }',
    '  }',
    `  if (argv.includes('--say-on-stderr')) process.stderr.write('a warning\\n')`,
    `  process.exit(${String(behaviour.exitCode ?? 0)})`,
    '}',
  ].join('\n')
}

export function fakeClaude(behaviour: FakeBehaviour = {}): FakeClaude {
  const home = mkdtempSync(path.join(tmpdir(), 'rk-fake-claude-'))
  const file = path.join(home, 'claude.mjs')
  writeFileSync(file, script(behaviour), 'utf8')

  return {
    command: process.execPath,
    prefixArgs: [file],
    dispose() {
      removeTree(home)
    },
  }
}
