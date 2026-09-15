import { mkdtempSync, readFileSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import path from 'node:path'

import { removeTree } from './scratch'

/**
 * A `claude` that replays a run, for the window to be pointed at (RG210).
 *
 * `fake-claude.ts` writes the few lines a live test asserts and exits. The session screen needs
 * something else to be looked at: a run long enough to overflow the stream region, with notes to
 * fold and tool calls to draw, and one still running when it is photographed. So this replays a
 * captured run and a tail after it, then stays up writing nothing — running, with a document
 * that settles.
 *
 * **It answers what resolution asks.** `--version` prints a version line and `auth status` a
 * login, so RG43 resolves it and RG205 decides its environment exactly as for the real one.
 *
 * **It never ends on its own.** The captured run's closing `result` line is left out, since a
 * result is what makes a session done; stopping the session, or quitting the window, ends it.
 */

/**
 * The captured headless run this replays by default.
 *
 * Reached through the package and not beside this file: bundled into `dist/shots.js`, this
 * module's own directory is `dist`, and the capture stays in `src`.
 */
export const CAPTURED_STREAM = path.resolve(
  import.meta.dirname,
  '..',
  'src',
  'captured',
  'session-stream.jsonl',
)

export interface ScriptedAgentOptions {
  /** A `stream-json` file to replay. The captured run unless a caller has another. */
  readonly stream?: string
  /** How many acts to add after it, so the region has more to hold than it shows. */
  readonly tail?: number
  /** The pause between lines, so the stream arrives as a run's does rather than all at once. */
  readonly intervalMs?: number
}

export interface ScriptedAgent {
  /** The argv to start it with: this process's node and the script. */
  readonly command: readonly string[]
  /** How many lines a session will have once the replay is through. */
  readonly lines: number
  dispose(): void
}

/**
 * One cycle of the tail: something said, a call, its answer, and a note between turns.
 *
 * Every other call is an edit, spread over three files, so the files a session edited have rows
 * to draw with more than one call among them (RG243). Each stands differently on disk (RG244):
 * one is outside the project, one is not there, and the first is the fixture's roadmap, which
 * is there to be opened in the viewer (RG245). Nothing is written: a replay only reports edits.
 *
 * Each edit carries both its halves, so the viewer has what the session changed to draw (RG246)
 * — the first one puts back a heading the fixture's roadmap really holds, and the rest put text
 * it does not, which are the two answers checking an edit against the file can give.
 */
function tailCycle(at: number): string[] {
  const id = `scripted-${String(at)}`
  const edited =
    ['../elsewhere/scripted-notes.md', 'src/scripted.ts', 'docs/ROADMAP.md'][at % 3] ?? ''
  const call =
    at % 2 === 0
      ? {
          name: 'Edit',
          input: {
            file_path: edited,
            old_string: `the line step ${String(at)} replaced`,
            new_string: at === 2 ? '## Block A — The model' : `what step ${String(at)} put there`,
          },
        }
      : { name: 'Read', input: { file_path: 'docs/ROADMAP.md' } }
  return [
    {
      type: 'assistant',
      message: { content: [{ type: 'text', text: `Step ${String(at)} of the scripted run.` }] },
    },
    {
      type: 'assistant',
      message: { content: [{ type: 'tool_use', id, ...call }] },
    },
    {
      type: 'user',
      message: {
        content: [{ type: 'tool_result', tool_use_id: id, content: `read ${String(at)}` }],
      },
    },
    { type: 'rate_limit_event', rate_limit_info: { status: 'allowed' } },
  ].map((line) => JSON.stringify(line))
}

/**
 * The lines a replay writes: the captured run without its `result`, then `tail` more acts.
 *
 * Pure over the file's text, so which lines a session will hold is a fact a test reads without
 * starting anything.
 */
export function scriptedLines(captured: string, tail: number): string[] {
  const kept = captured
    .split('\n')
    .map((line) => line.trim())
    .filter((line) => line !== '')
    .filter((line) => {
      try {
        const parsed: unknown = JSON.parse(line)
        return !(
          typeof parsed === 'object' &&
          parsed !== null &&
          'type' in parsed &&
          parsed.type === 'result'
        )
      } catch {
        return true
      }
    })
  const added: string[] = []
  for (let at = 1; added.length < tail; at += 1) added.push(...tailCycle(at))
  return [...kept, ...added.slice(0, tail)]
}

/**
 * The file the replay writes into the project it runs in (RG247).
 *
 * A real session's Bash calls write files no edit call names — a formatter, a generator, an
 * install — and that is the whole of what the watch is for. The replay does the smallest
 * honest version of it: one file, in its own working directory, which is the project's root.
 *
 * Under `src` and not `dist`, because the settings' skip list is what the watch leaves out and
 * a build directory is on it.
 */
const SCRIPTED_WRITE = 'src/scripted-generated.txt'

function script(linesFile: string, intervalMs: number): string {
  return [
    "import { mkdirSync, readFileSync, writeFileSync } from 'node:fs'",
    'const argv = process.argv.slice(2)',
    "if (argv.includes('--version')) { process.stdout.write('2.1.263 (Claude Code, scripted)\\n'); process.exit(0) }",
    "if (argv[0] === 'auth' && argv[1] === 'status') {",
    "  process.stdout.write(JSON.stringify({ loggedIn: true, authMethod: 'scripted' }) + '\\n')",
    '  process.exit(0)',
    '}',
    "if (!argv.includes('-p')) { process.stderr.write('the scripted agent takes -p\\n'); process.exit(2) }",
    // Written as the run starts, the way a command a session runs writes one: no edit call
    // names it, so only a watch on the root can report it.
    'try {',
    "  mkdirSync('src', { recursive: true })",
    `  writeFileSync(${JSON.stringify(SCRIPTED_WRITE)}, 'built by the scripted run\\n')`,
    '} catch {}',
    `const lines = JSON.parse(readFileSync(${JSON.stringify(linesFile)}, 'utf8'))`,
    'let at = 0',
    'const next = () => {',
    '  if (at === lines.length) { setInterval(() => undefined, 1 << 30); return }',
    "  process.stdout.write(lines[at] + '\\n')",
    '  at += 1',
    `  setTimeout(next, ${String(intervalMs)})`,
    '}',
    'next()',
  ].join('\n')
}

export function scriptedAgent(options: ScriptedAgentOptions = {}): ScriptedAgent {
  const lines = scriptedLines(
    readFileSync(options.stream ?? CAPTURED_STREAM, 'utf8'),
    options.tail ?? 40,
  )
  const home = mkdtempSync(path.join(tmpdir(), 'rk-scripted-agent-'))
  const linesFile = path.join(home, 'lines.json')
  const file = path.join(home, 'claude.mjs')
  writeFileSync(linesFile, JSON.stringify(lines), 'utf8')
  writeFileSync(file, script(linesFile, options.intervalMs ?? 15), 'utf8')

  return {
    command: [process.execPath, file],
    lines: lines.length,
    dispose() {
      removeTree(home)
    },
  }
}
