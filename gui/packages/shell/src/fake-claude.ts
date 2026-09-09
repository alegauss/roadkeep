import { mkdtempSync, rmSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import path from 'node:path'

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
      subtype: behaviour.failing === true ? 'error' : 'success',
      is_error: behaviour.failing === true,
      result: behaviour.failing === true ? 'ran out of turns' : 'done',
      num_turns: 3,
      duration_ms: 1234,
      session_id: 'fake-0001',
    },
  ]

  return [
    'const argv = process.argv.slice(2)',
    // The session's own cwd, so a test can prove the process ran where it was told to.
    `const lines = ${JSON.stringify(lines)}`,
    'lines[0].cwd = process.cwd()',
    `if (${String(behaviour.hanging === true)}) { setInterval(() => {}, 1000) } else {`,
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
      rmSync(home, { recursive: true, force: true })
    },
  }
}
