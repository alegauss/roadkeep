import { spawn, type ChildProcess } from 'node:child_process'

import {
  query,
  type HookCallback,
  type Options,
  type SpawnedProcess,
  type SpawnOptions,
} from '@anthropic-ai/claude-agent-sdk'
import { asRecord } from '@rk/core'

/**
 * One read-only query to Claude Code (RG284): a question about the project, and nothing it may
 * write.
 *
 * A session (RG153) is a turn that may write, held open, answered by a person. A question here is
 * none of those — asked once, answered against a schema, nobody to ask — so it is its own call
 * beside `startSession`, sharing what belongs to the machine and not to a session: the `claude`
 * RG43 resolved, the environment RG205 decided, and the way a child is spawned under Electron.
 *
 * **Two questions are asked through it.** A gloss says what a task means (RG284); a walkthrough
 * says how to check one that shipped (RG291). They differ in the prompt, the schema and what they
 * are allowed to read, and in nothing else — so the tools are a field of the call rather than a
 * constant of this file, and adding a question is a list beside the prompt it goes with.
 *
 * **Nothing it runs can change anything.** Every tool any question is given is a read (RG288):
 * `Read`, `Grep` and `Glob`, and for a walkthrough one bounded `git show`. No MCP server is
 * configured and strict configuration keeps the project's own out, and permissions are never
 * asked about: a call the run tries beyond its list is denied where it stands. So *no write to a
 * governed file* holds here by there being nothing to write with.
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
 * The tools a walkthrough is allowed outright (RG291). The gloss's three, and no more.
 *
 * `Bash` is deliberately absent: it is the one a walkthrough needs and the one nothing may have
 * unconditionally, so it is not granted here at all and reaches `permits` instead.
 */
export const WALKTHROUGH_TOOLS = GLOSS_TOOLS

/** A chained or redirected command, whatever it starts with. */
const CHAINED = /[;&|`$<>\n\r]/

/**
 * Whether a shell command is the one read a walkthrough may make (RG291).
 *
 * **The agent runs git, not this app**, which is how *No git command run by this app* holds
 * here: what the shell supplies is the permission and the bound, and the run spends it the way
 * it spends `Read`. The bound has to be this side because the list does not hold it — a
 * `Bash(git show:*)` entry in `allowedTools` grants the whole shell, which a captured run proved
 * by reaching for `ls`, `python` and `grep` under it.
 *
 * So: `git show`, and nothing chained or redirected onto the end of it. Staging, committing and
 * pushing — the writes that non-goal is about — are unreachable from here, and a person still
 * reviews every write this app makes, because it makes none.
 */
export function isGitRead(command: string): boolean {
  const said = command.trim()
  return said.startsWith('git show ') && !CHAINED.test(said)
}

/**
 * What a gate says about one call.
 *
 * Three and not two, because a gate that answered every call would answer for the ones it is not
 * about: the tools in the list, and the one the SDK writes a schema's answer with. Deciding those
 * is how the first gate here denied `StructuredOutput` and the run came back with no answer at
 * all. `defer` is the only honest word for a call this gate has no opinion on.
 */
export type Permit = 'allow' | 'deny' | 'defer'

/**
 * The gate a walkthrough runs under: one bounded `git show`, and no other shell call.
 *
 * It governs `Bash` and defers the rest, which is the whole of its reach: the read tools are the
 * list's as they always were, and anything else the run tries is denied where it stands because
 * nothing granted it.
 */
export function permitsGitRead(tool: string, input: Record<string, unknown>): Permit {
  if (tool !== 'Bash') return 'defer'
  const command = input['command']
  return typeof command === 'string' && isGitRead(command) ? 'allow' : 'deny'
}

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
  /** The shape the answer is held to: `GLOSS_SCHEMA`'s, or a walkthrough's. */
  readonly schema: Record<string, unknown>
  /**
   * What this question may read outright. `GLOSS_TOOLS` unless a caller says, which is the list
   * that was a constant here before a second question had a different one.
   */
  readonly tools?: readonly string[]
  /**
   * One more thing it may do, decided per call (RG291).
   *
   * Absent, nothing outside `tools` is reachable: the run is refused where it stands and nobody
   * is asked. Given, it decides the calls it is about before the list and before the project's
   * own allowlist — which is how a walkthrough gets `git show` and no other shell command. A
   * list entry cannot say this: `Bash(git show:*)` in `allowedTools` grants the whole shell.
   */
  readonly permits?: (tool: string, input: Record<string, unknown>) => Permit
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

/**
 * A caller's gate, as a `PreToolUse` hook (RG291).
 *
 * **A hook and not `canUseTool`**, which is the second thing this had to be. Permission *rules*
 * are read before a prompt surface is asked, and the settings a question loads for the project's
 * vocabulary carry that project's own allowlist — so a gate on the prompt surface is never
 * consulted for anything the checkout already allows, and a captured run proved it by running
 * `npx vitest` under one. A hook decision is taken before the rules, so this one holds whatever
 * the project permits its own sessions.
 *
 * It answers in both directions and neither is a prompt: allowed, or denied with the sentence
 * the run reads. The input is never rewritten — a gate that edited a command would be this app
 * composing one, and what it approved would not be what ran.
 */
function gate(permits: (tool: string, input: Record<string, unknown>) => Permit): HookCallback {
  return (input) => {
    if (input.hook_event_name !== 'PreToolUse') return Promise.resolve({})
    const said = permits(input.tool_name, asRecord(input.tool_input) ?? {})
    if (said === 'defer') return Promise.resolve({})
    return Promise.resolve({
      hookSpecificOutput: {
        hookEventName: 'PreToolUse',
        permissionDecision: said,
        permissionDecisionReason:
          said === 'allow'
            ? 'the one read this question may make'
            : `${input.tool_name} is not one of the reads this question may make`,
      },
    })
  }
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
          // Nothing to write with: this question's reads and no more, and no server configured.
          allowedTools: [...(call.tools ?? GLOSS_TOOLS)],
          disallowedTools: [],
          mcpServers: {},
          strictMcpConfig: true,
          // Nobody is there to ask, so anything past the list is denied where it stands. A gate
          // decides before that, and before the project's own allowlist, which is why it is a
          // hook: it is the only answer taken ahead of the rules a checkout carries.
          permissionMode: 'dontAsk',
          ...(call.permits === undefined
            ? {}
            : { hooks: { PreToolUse: [{ hooks: [gate(call.permits)] }] } }),
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
