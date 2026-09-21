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
 * that settles. The last line it writes is a question (RG272), so what is photographed is a
 * session held on a person, which is the moment the screen is for.
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
  /**
   * End the replay on a question nobody has answered (RG272), which is where a real run waits on
   * a person. True unless a caller wants a run that only runs.
   */
  readonly asking?: boolean
}

/**
 * The question a replay ends on (RG272): a Bash call the project's rules leave open, with the rule
 * the engine offers for the rest of the session, as Claude Code 2.1.274 writes one.
 */
export const SCRIPTED_ASK = JSON.stringify({
  type: 'control_request',
  request_id: 'scripted-ask',
  request: {
    subtype: 'can_use_tool',
    tool_name: 'Bash',
    display_name: 'Bash',
    input: { command: 'npm test', description: 'Run the tests' },
    description: 'Run the tests',
    permission_suggestions: [
      {
        type: 'addRules',
        rules: [{ toolName: 'Bash', ruleContent: 'npm test:*' }],
        behavior: 'allow',
        destination: 'localSettings',
      },
    ],
    tool_use_id: 'scripted-ask-call',
  },
})

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
 * Every other call is an edit, spread over four files, so the files a session edited have rows
 * to draw with more than one call among them (RG243). Each stands differently on disk (RG244):
 * one is outside the project, one is not there, and the first is the fixture's roadmap, which
 * is there to be opened in the viewer (RG245). Nothing is written: a replay only reports edits.
 *
 * **And each is a different thing to have done** (RG280, RG282): the changelog is written as a
 * file this session made, `src/scripted.ts` is one it changed and nothing holds now, and the
 * roadmap is one it changed and the disk still has — so the marks and the three comparisons the
 * viewer draws are all in one replay.
 *
 * Each edit carries both its halves, so the viewer has what the session changed to draw (RG246)
 * — the first one puts back a heading the fixture's roadmap really holds, and the rest put text
 * it does not, which are the two answers checking an edit against the file can give.
 *
 * What it says is written the way an agent writes, in Markdown (RG271): every step's sentence has
 * its bold and its code, and every fifth is a choice with a command wider than the stream.
 */
function said(at: number): string {
  const step = String(at)
  if (at % 5 !== 0) return `Step ${step} of the **scripted** run, checked with \`npm test\`.`
  return [
    `Step ${step}: two remedies for the **lint** finding.`,
    '',
    '1. Retire the row',
    '2. Flip the row',
    '',
    '```sh',
    'npx vitest run --project ui packages/ui/src/session.test.tsx --reporter verbose --no-cache',
    '```',
  ].join('\n')
}

/**
 * The files the replay edits, in the order its edits take them.
 *
 * The roadmap first, because it is the one the viewer opens and the one really on disk; then a
 * file nothing holds, a file outside the project, and the changelog, which this run is written
 * as having made.
 */
export const SCRIPTED_EDITS = [
  'docs/ROADMAP.md',
  'src/scripted.ts',
  '../elsewhere/scripted-notes.md',
  'docs/CHANGELOG.md',
] as const

/** The one the replay writes rather than edits, so a created file has a row and a comparison. */
export const SCRIPTED_MADE = 'docs/CHANGELOG.md'

function tailCycle(at: number): string[] {
  const id = `scripted-${String(at)}`
  // Every other step edits, so the rotation counts edits and not steps: over four edits each
  // file is taken once, whatever the tail's length.
  const edited = SCRIPTED_EDITS[(Math.floor(at / 2) - 1) % SCRIPTED_EDITS.length] ?? ''
  const made = edited === SCRIPTED_MADE
  const replaced = `the line step ${String(at)} replaced`
  const wrote = at === 2 ? '## Block A — The model' : `what step ${String(at)} put there`
  const call =
    at % 2 === 0
      ? made
        ? { name: 'Write', input: { file_path: edited, content: `${wrote}\n` } }
        : {
            name: 'Edit',
            input: { file_path: edited, old_string: replaced, new_string: wrote },
          }
      : { name: 'Read', input: { file_path: 'docs/ROADMAP.md' } }
  // An edit answers with the file as it stood before the call, and a write with whether it made
  // the file, the way a real run does (RG280): that is what marks the row and what the viewer
  // compares the file against (RG282).
  const answered =
    at % 2 === 0
      ? {
          tool_use_result: made
            ? {
                type: 'create',
                filePath: edited,
                content: `${wrote}\n`,
                structuredPatch: [],
                originalFile: null,
                userModified: false,
              }
            : {
                filePath: edited,
                oldString: replaced,
                newString: wrote,
                originalFile: `${replaced}\n`,
                structuredPatch: [],
                userModified: false,
              },
        }
      : {}
  return [
    {
      type: 'assistant',
      message: { content: [{ type: 'text', text: said(at) }] },
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
      ...answered,
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
    "if (!argv.includes('--output-format')) { process.stderr.write('the scripted agent is a session: it takes --output-format\\n'); process.exit(2) }",
    // The Agent SDK opens with an `initialize` request (RG273), which a real one answers before
    // anything else; the replay answers it too, and reads nothing else it is sent.
    "import('node:readline').then(({ createInterface }) => {",
    "  createInterface({ input: process.stdin }).on('line', (line) => {",
    '    let message = null',
    '    try { message = JSON.parse(line) } catch { return }',
    "    if (message?.type !== 'control_request' || message.request?.subtype !== 'initialize') return",
    "    process.stdout.write(JSON.stringify({ type: 'control_response', response: { subtype: 'success', request_id: message.request_id, response: {} } }) + '\\n')",
    '  })',
    '})',
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
  const lines = [
    ...scriptedLines(readFileSync(options.stream ?? CAPTURED_STREAM, 'utf8'), options.tail ?? 40),
    ...(options.asking === false ? [] : [SCRIPTED_ASK]),
  ]
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
