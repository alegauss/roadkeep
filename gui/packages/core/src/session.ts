import type { BriefPayload } from './payloads'

/**
 * What a Claude Code session is handed, and what it says back.
 *
 * Claude Code runs headless — `claude -p <prompt> --output-format stream-json --verbose`,
 * a child process writing one JSON object per line. That call is the whole integration,
 * and everything difficult about it sits on either side of it.
 *
 * **`--verbose` is not optional.** With `--print`, `--output-format stream-json` is
 * refused without it — `Error: When using --print, --output-format=stream-json requires
 * --verbose` — so it is part of the call and not a setting somebody might turn off.
 *
 * **What goes in is not a prompt somebody typed.** It is the payload `brief` returned for
 * the task: the tier it was chosen by, its deps, its design section, what shipping it
 * unblocks, and the criteria and non-goals that bind it. That is the read roadkeep's own
 * skill tells an agent to start from, and re-composing it here in English would be this
 * app paraphrasing the tool. The prompt is a short frame around a payload.
 *
 * **Where it runs decides what it can do.** The session's working directory is the project
 * root, so the project's own wiring answers: its `roadkeep.toml`, its guard, its skill, its
 * `.mcp.json`. This app passes no configuration and installs nothing — the same engine rule
 * as everywhere else, so the session runs the project's roadkeep and not this app's idea of
 * one.
 *
 * **This app never writes the backlog on the session's behalf.** The agent writes through
 * the same verbs a person does.
 */

/**
 * The frame around the payload.
 *
 * Short on purpose. Everything the agent needs is in the payload, and a paragraph of
 * this app's prose about the task would be a second account of a line roadkeep already
 * stated — which is the paraphrasing the design refuses.
 */
export function promptFor(payload: BriefPayload): string {
  return [
    `Work roadkeep task ${payload.id} in this project, start to finish.`,
    '',
    'Below is the `brief` payload roadkeep answered for it, verbatim: the line, its design',
    'section, its deps and what resolves them, what shipping it unblocks, and the criteria',
    'and non-goals that bind it. Nothing in it was rewritten.',
    '',
    JSON.stringify(payload, null, 2),
  ].join('\n')
}

export interface SessionCall {
  /** The command to run. Named by the caller: which `claude` answers is RG43's question. */
  readonly command: string
  readonly argv: readonly string[]
  /** The project root, which is where the session's own wiring is found. */
  readonly cwd: string
}

/**
 * Build the call.
 *
 * Nothing is passed but the prompt and the format. No model, no permission mode, no
 * `--add-dir`, no system prompt: every one of those would be this app deciding something
 * the project or the person already decides, and the session is meant to run under the
 * project's own configuration.
 */
export function sessionCall(command: string, cwd: string, prompt: string): SessionCall {
  return {
    command,
    cwd,
    argv: ['-p', prompt, '--output-format', 'stream-json', '--verbose'],
  }
}

/**
 * One line of the stream, read into something a screen can use.
 *
 * `other` is deliberate: the stream carries kinds this app has no use for today — rate
 * limits, tool calls, per-turn accounting — and dropping them would make the reader lie
 * about how much it saw. RG40 draws them; this names them.
 */
export type SessionEvent =
  | {
      readonly kind: 'started'
      readonly sessionId: string
      readonly cwd: string
      readonly model: string
      readonly version: string
      /** What the session may use, in its own words. Read, never checked against a list. */
      readonly tools: readonly string[]
    }
  | { readonly kind: 'said'; readonly text: string; readonly sessionId: string }
  | {
      readonly kind: 'finished'
      /** The engine's own verdict. `is_error` is the field, not the exit code. */
      readonly ok: boolean
      readonly result: string
      readonly turns: number
      readonly durationMs: number
      readonly sessionId: string
    }
  | { readonly kind: 'other'; readonly type: string; readonly line: string }

function textOf(message: unknown): string {
  if (typeof message !== 'object' || message === null) return ''
  const content = (message as { content?: unknown }).content
  if (!Array.isArray(content)) return ''
  return content
    .filter(
      (part): part is { type: string; text: string } =>
        typeof part === 'object' &&
        part !== null &&
        (part as { type?: unknown }).type === 'text' &&
        typeof (part as { text?: unknown }).text === 'string',
    )
    .map((part) => part.text)
    .join('')
}

function stringAt(source: Record<string, unknown>, key: string): string {
  const value = source[key]
  return typeof value === 'string' ? value : ''
}

function numberAt(source: Record<string, unknown>, key: string): number {
  const value = source[key]
  return typeof value === 'number' ? value : 0
}

/**
 * Read one line, or null where the line is not JSON at all.
 *
 * Null and `other` are different answers: null is a line this app could not read, and
 * `other` is one it read and has no use for. A screen that conflated them would report
 * a healthy session as producing garbage.
 */
export function readSessionLine(line: string): SessionEvent | null {
  const trimmed = line.trim()
  if (trimmed === '') return null

  let source: unknown
  try {
    source = JSON.parse(trimmed)
  } catch {
    return null
  }
  if (typeof source !== 'object' || source === null || Array.isArray(source)) return null

  const object = source as Record<string, unknown>
  const type = stringAt(object, 'type')
  const sessionId = stringAt(object, 'session_id')

  if (type === 'system' && stringAt(object, 'subtype') === 'init') {
    const tools = object['tools']
    return {
      kind: 'started',
      sessionId,
      cwd: stringAt(object, 'cwd'),
      model: stringAt(object, 'model'),
      version: stringAt(object, 'claude_code_version'),
      tools: Array.isArray(tools) ? tools.filter((one): one is string => typeof one === 'string') : [],
    }
  }

  if (type === 'assistant') {
    const text = textOf(object['message'])
    return text === '' ? { kind: 'other', type, line: trimmed } : { kind: 'said', text, sessionId }
  }

  if (type === 'result') {
    return {
      kind: 'finished',
      // The engine's verdict, and the reason the exit code is not read for it — the same
      // rule the payload reader follows for a refusal.
      ok: object['is_error'] !== true,
      result: stringAt(object, 'result'),
      turns: numberAt(object, 'num_turns'),
      durationMs: numberAt(object, 'duration_ms'),
      sessionId,
    }
  }

  return { kind: 'other', type, line: trimmed }
}

/**
 * Where a session stands.
 *
 * `unavailable` is its own state and not a failure of the run: no `claude` on the machine
 * is a fact about the machine, and it is the one a screen has to say plainly rather than
 * reporting as a session that went wrong.
 */
export type SessionState = 'starting' | 'running' | 'done' | 'failed' | 'cancelled' | 'unavailable'

export interface SessionOutcome {
  readonly state: SessionState
  /** The session's own id, once it named one. Empty where it never started. */
  readonly sessionId: string
  /** What it exited with. Null where it never ran or was killed before exiting. */
  readonly code: number | null
  /** What went wrong, in the engine's words or the operating system's. */
  readonly said: string
  /** The last thing the session reported as its result. */
  readonly result: string
}

/**
 * Read the outcome off what the session said and what the process did.
 *
 * The `result` line is believed first: it carries the session's own verdict, and a run
 * that finished badly says so there. The exit code is the fallback for a session that
 * stopped without one — killed, crashed, or never started.
 */
export function outcomeOf(
  events: readonly SessionEvent[],
  exit: { readonly code: number | null; readonly cancelled: boolean; readonly said: string },
): SessionOutcome {
  const started = events.find((event) => event.kind === 'started')
  const finished = events.find((event) => event.kind === 'finished')
  const sessionId = finished?.sessionId ?? started?.sessionId ?? ''

  if (exit.cancelled) {
    return { state: 'cancelled', sessionId, code: exit.code, said: exit.said, result: '' }
  }
  if (finished !== undefined) {
    return {
      state: finished.ok ? 'done' : 'failed',
      sessionId,
      code: exit.code,
      said: exit.said,
      result: finished.result,
    }
  }
  return { state: 'failed', sessionId, code: exit.code, said: exit.said, result: '' }
}
