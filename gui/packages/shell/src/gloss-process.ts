import { spawn, type ChildProcess } from 'node:child_process'

import {
  query,
  type Options,
  type SpawnedProcess,
  type SpawnOptions,
} from '@anthropic-ai/claude-agent-sdk'
import { asRecord } from '@rk/core'

/**
 * One read-only query to Claude Code (RG284): what a task means, and nothing it may write.
 *
 * A session (RG153) is a turn that may write, held open, answered by a person. A gloss is none
 * of those — one question, no tool, nobody to ask — so it is its own call beside `startSession`,
 * sharing what belongs to the machine and not to a session: the `claude` RG43 resolved, the
 * environment RG205 decided, and the way a child is spawned under Electron.
 *
 * **Nothing it runs can change anything.** Three tools and all of them reads (RG288): `Read`,
 * `Grep` and `Glob`, so the design's own files can be read before the task is explained. No MCP
 * server is configured and strict configuration keeps the project's own out, and permissions are
 * never asked about: a call the run tries beyond those three is denied where it stands. So *no
 * write to a governed file* holds here by there being nothing to write with.
 *
 * **And every line is told** (RG297). A structured answer arrives at the end and says nothing on
 * the way, so its stream is the only progress there is: each message is handed to the caller as
 * the line it was — `startSession`'s spelling of it — and a screen draws it with a session's rows.
 *
 * **And nothing is kept.** `persistSession: false` keeps a gloss out of the sessions a person
 * can resume, which is right for a read nobody named: what comes back is an answer, not a
 * conversation to continue.
 *
 * **The project's own words, though.** The working directory is the project root and the
 * settings sources are the session's, so its `CLAUDE.md` and its skills supply the vocabulary
 * the line is written in. That is the whole reason this runs in the project at all.
 */

/** The settings a gloss loads, which are the session's: the project's own words come from them. */
const SETTING_SOURCES: Options['settingSources'] = ['user', 'project', 'local']

/** Claude Code's own system prompt, as a `claude` started by hand runs with. */
const CLAUDE_CODE_PROMPT: Options['systemPrompt'] = { type: 'preset', preset: 'claude_code' }

/** The tools a gloss is given (RG288). Three, all reads, and the list is the whole permission. */
export const GLOSS_TOOLS = ['Read', 'Grep', 'Glob']

/**
 * How many turns one question may take.
 *
 * Above one because the engine answers a schema by taking a turn to write it, and well above it
 * since RG288: reading the files a design names is a turn each, and a run cut off mid-reading
 * answers nothing at all. Still bounded, because nothing here is a conversation and a run that
 * wanders is a run to stop.
 */
export const GLOSS_TURNS = 24

export interface GlossCall {
  /** The executable Claude Code resolved to, and the rest of its command line. */
  readonly command: string
  readonly prefix: readonly string[]
  /** The project root, so the project's own configuration answers. */
  readonly cwd: string
  readonly prompt: string
  /** The shape the answer is held to, which is `GLOSS_SCHEMA`'s. */
  readonly schema: Record<string, unknown>
  /**
   * Told of each line of the stream as it passes (RG297), which is the only progress a schema
   * has: the files it reads, what it says, and the notes that show it is still thinking.
   */
  readonly line?: (line: string) => void
}

/** What one query came back with. Every way of not answering is its own kind. */
export type GlossRead =
  | {
      readonly kind: 'said'
      /** The `structured_output` the result carried, unread: `readGloss` is `core`'s. */
      readonly structured: unknown
      readonly model: string
      readonly version: string
    }
  /** The process never started: no `claude` on this machine. */
  | { readonly kind: 'unavailable'; readonly said: string }
  /** It ran and answered nothing usable — its own words, or the SDK's. */
  | { readonly kind: 'failed'; readonly said: string }
  | { readonly kind: 'cancelled' }

export interface GlossRun {
  readonly answered: Promise<GlossRead>
  /** Give it up. Answering `cancelled` is what a reader who closed the screen gets. */
  cancel(): void
}

/** What the `init` line names about the run: which model answered, and which Claude Code. */
function initOf(message: unknown): { readonly model: string; readonly version: string } | null {
  const line = asRecord(message)
  if (line?.['type'] !== 'system' || line['subtype'] !== 'init') return null
  const model = line['model']
  const version = line['claude_code_version']
  return {
    model: typeof model === 'string' ? model : '',
    version: typeof version === 'string' ? version : '',
  }
}

/**
 * Ask one question and read the answer (RG284).
 *
 * @param env the environment the run is given, as RG205 decided it
 */
export function askGloss(call: GlossCall, env: NodeJS.ProcessEnv = process.env): GlossRun {
  const abort = new AbortController()
  const standing = {
    cancelled: false,
    stderr: '',
    failure: null as NodeJS.ErrnoException | null,
    child: null as ChildProcess | null,
  }

  // The agent's own command line, then the SDK's flags — `startSession`'s arrangement, and for
  // its reason: the SDK names the executable back as the command, or as the argument after a
  // runtime, and what follows it is the SDK's.
  const spawnAgent = (options: SpawnOptions): SpawnedProcess => {
    const flags =
      options.command === call.command
        ? options.args
        : options.args.slice(options.args.indexOf(call.command) + 1)
    const child: ChildProcess = spawn(call.command, [...call.prefix, ...flags], {
      cwd: options.cwd,
      env: options.env,
      shell: false,
      windowsHide: true,
      stdio: ['pipe', 'pipe', 'pipe'],
    })
    standing.child = child
    child.once('error', (cause: NodeJS.ErrnoException) => {
      // ENOENT is a machine with no `claude`, which is a state of its own and not a failure of
      // the question: the process never started, so nothing else will end the run.
      standing.failure = cause
      abort.abort()
    })
    const { stdin, stdout, stderr: errors } = child
    if (stdin === null || stdout === null || errors === null) {
      throw new Error('the gloss was spawned without the pipes it is read over')
    }
    stdin.on('error', () => undefined)
    errors.setEncoding('utf8')
    errors.on('data', (chunk: string) => {
      standing.stderr += chunk
    })
    options.signal.addEventListener('abort', () => child.kill(), { once: true })
    return Object.assign(child, { stdin, stdout })
  }

  const answered = (async (): Promise<GlossRead> => {
    let named = { model: '', version: '' }
    let structured: unknown
    let said = ''
    let thrown = ''
    try {
      const messages = query({
        prompt: call.prompt,
        options: {
          abortController: abort,
          cwd: call.cwd,
          env: { ...env },
          pathToClaudeCodeExecutable: call.command,
          spawnClaudeCodeProcess: spawnAgent,
          settingSources: SETTING_SOURCES,
          systemPrompt: CLAUDE_CODE_PROMPT,
          outputFormat: { type: 'json_schema', schema: call.schema },
          // Nothing to write with: three reads and no more, no server configured, and a mode
          // that denies where it stands rather than asking a person who is not there.
          allowedTools: GLOSS_TOOLS,
          disallowedTools: [],
          mcpServers: {},
          strictMcpConfig: true,
          permissionMode: 'dontAsk',
          persistSession: false,
          maxTurns: GLOSS_TURNS,
        },
      })
      for await (const message of messages) {
        named = initOf(message) ?? named
        const line = asRecord(message)
        call.line?.(JSON.stringify(message))
        if (line?.['type'] !== 'result') continue
        structured = line['structured_output']
        const text = line['result']
        said = typeof text === 'string' ? text : ''
      }
    } catch (cause) {
      thrown = cause instanceof Error ? cause.message : String(cause)
    }

    if (standing.cancelled) return { kind: 'cancelled' }
    const failure = standing.failure
    if (failure !== null) return { kind: 'unavailable', said: failure.message }
    if (structured === undefined || structured === null) {
      // What it said on its own error channel first, then what it answered in words, then what
      // the SDK threw: the most specific account of a run that gave no answer.
      const stderr = standing.stderr.trim()
      return { kind: 'failed', said: stderr === '' ? (said === '' ? thrown : said) : stderr }
    }
    return { kind: 'said', structured, model: named.model, version: named.version }
  })()

  return {
    answered,
    cancel() {
      standing.cancelled = true
      abort.abort()
      standing.child?.kill()
    },
  }
}
