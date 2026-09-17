import { asRecord } from './reading'

/**
 * A question a running session asks a person, and the answer that goes back (RG272).
 *
 * Headless Claude Code has nobody to ask. A call the project's own rules leave to a question was
 * refused on the spot, and the agent retried into the same refusal while the window drew each
 * failure. `--permission-prompt-tool stdio` is the engine's door for this: every such question is
 * written as a `control_request` line, and the session blocks until a `control_response` arrives
 * on its standard input.
 *
 * **It decides nothing.** The project's rules still answer every call they cover; what reaches
 * this module is only what they left open, and every answer is a person's.
 *
 * **The engine's schema, read with a fallback.** A request that does not carry a tool is not a
 * question this module can put to anybody, and reads as none — its line is still in the stream.
 *
 * **Kept as lines.** An answer is written to the session and kept in its record beside the
 * question, so every window reads a question as answered off the same lines, and a screen opened
 * later loses nothing.
 */

/** One question, as the engine wrote it. */
export interface PermissionAsk {
  /** The engine's id for the question, which its answer names. */
  readonly requestId: string
  readonly tool: string
  /** What the call would run with. Whatever that tool takes, carried unread. */
  readonly input: unknown
  /** The engine's own short account of the call, or empty where it gave none. */
  readonly description: string
  /** The call this question holds up, which its act in the stream carries as its id. */
  readonly callId: string
  /**
   * What the engine offers as the way not to be asked again, verbatim. Answering for the session
   * sends these back narrowed to the session, and never composes one.
   */
  readonly suggestions: readonly Record<string, unknown>[]
}

/** The three answers a person gives. */
export type AskAnswer = 'once' | 'session' | 'decline'

/** Where a question stands, off the lines that follow it. */
export type AskStanding = AskAnswer | 'withdrawn' | 'open'

/** What an agent reads when a person declines, in the language it was prompted in. */
export const DECLINED =
  'The person watching this session declined this call from the roadkeep window.'

/** The session scope, which is the only one an answer from this window ever names. */
const SESSION = 'session'

function parsed(line: string): Record<string, unknown> | null {
  try {
    return asRecord(JSON.parse(line.trim()))
  } catch {
    return null
  }
}

function text(source: Record<string, unknown> | null, key: string): string {
  const value = source?.[key]
  return typeof value === 'string' ? value : ''
}

/** The question a line asks, or null where it asks none. */
export function askOf(line: string): PermissionAsk | null {
  const object = parsed(line)
  if (text(object, 'type') !== 'control_request') return null
  const request = asRecord(object?.['request'])
  if (text(request, 'subtype') !== 'can_use_tool') return null
  const tool = text(request, 'tool_name')
  const requestId = text(object, 'request_id')
  if (tool === '' || requestId === '') return null
  const offered = request?.['permission_suggestions']
  return {
    requestId,
    tool,
    input: request?.['input'],
    description: text(request, 'description'),
    callId: text(request, 'tool_use_id'),
    suggestions: Array.isArray(offered)
      ? offered.flatMap((one) => {
          const suggestion = asRecord(one)
          return suggestion === null ? [] : [suggestion]
        })
      : [],
  }
}

/**
 * The line that answers a question, as the session reads it on standard input.
 *
 * Allowing sends the call's input back unchanged, since editing it would be this app rewriting the
 * agent's call. For the session, the engine's own suggestions go back with every destination set
 * to the session: a suggestion aimed at the project's settings would write a file that is the
 * project's, and the person answered for this run.
 */
export function answerLine(ask: PermissionAsk, answer: AskAnswer): string {
  const response =
    answer === 'decline'
      ? { behavior: 'deny', message: DECLINED }
      : {
          behavior: 'allow',
          updatedInput: ask.input ?? {},
          ...(answer === 'session'
            ? {
                updatedPermissions: ask.suggestions.map((suggestion) => ({
                  ...suggestion,
                  destination: SESSION,
                })),
              }
            : {}),
        }
  return JSON.stringify({
    type: 'control_response',
    response: { subtype: 'success', request_id: ask.requestId, response },
  })
}

/** The question a line answers and how, or null where it is not an answer this app wrote. */
export function answeredBy(
  line: string,
): { readonly requestId: string; readonly answer: AskAnswer } | null {
  const object = parsed(line)
  if (text(object, 'type') !== 'control_response') return null
  const outer = asRecord(object?.['response'])
  const inner = asRecord(outer?.['response'])
  const requestId = text(outer, 'request_id')
  const behavior = text(inner, 'behavior')
  if (requestId === '' || (behavior !== 'allow' && behavior !== 'deny')) return null
  if (behavior === 'deny') return { requestId, answer: 'decline' }
  return { requestId, answer: Array.isArray(inner?.['updatedPermissions']) ? 'session' : 'once' }
}

/** The question a line says the engine withdrew, or null. */
function withdrawnBy(line: string): string | null {
  const object = parsed(line)
  if (text(object, 'type') !== 'control_cancel_request') return null
  const requestId = text(object, 'request_id')
  return requestId === '' ? null : requestId
}

/** Every question the lines asked, each with where it stands, in the order they were asked. */
export function asksIn(
  lines: readonly string[],
): readonly { readonly ask: PermissionAsk; readonly standing: AskStanding }[] {
  const asks: PermissionAsk[] = []
  const settled = new Map<string, AskStanding>()
  for (const line of lines) {
    const ask = askOf(line)
    if (ask !== null) {
      asks.push(ask)
      continue
    }
    const answered = answeredBy(line)
    if (answered !== null) {
      // The first word on a question is the one the session acted on.
      if (!settled.has(answered.requestId)) settled.set(answered.requestId, answered.answer)
      continue
    }
    const withdrawn = withdrawnBy(line)
    if (withdrawn !== null && !settled.has(withdrawn)) settled.set(withdrawn, 'withdrawn')
  }
  return asks.map((ask) => ({ ask, standing: settled.get(ask.requestId) ?? 'open' }))
}

/** The questions still waiting on a person. */
export function openAsks(lines: readonly string[]): PermissionAsk[] {
  return asksIn(lines).flatMap((one) => (one.standing === 'open' ? [one.ask] : []))
}

/**
 * What allowing for the session would grant, as the engine's suggestions spell it, for a person to
 * read before choosing it. A suggestion of a shape this does not know is left out of the sentence
 * and still sent back.
 */
export function grantsOf(ask: PermissionAsk): string[] {
  return ask.suggestions.flatMap((suggestion) => {
    const type = text(suggestion, 'type')
    if (type === 'setMode') return text(suggestion, 'mode') === '' ? [] : [text(suggestion, 'mode')]
    if (type === 'addDirectories') {
      const directories = suggestion['directories']
      return Array.isArray(directories)
        ? directories.filter((one): one is string => typeof one === 'string')
        : []
    }
    if (type !== 'addRules' && type !== 'replaceRules') return []
    const rules = suggestion['rules']
    if (!Array.isArray(rules)) return []
    return rules.flatMap((one) => {
      const rule = asRecord(one)
      const tool = text(rule, 'toolName')
      if (tool === '') return []
      const content = text(rule, 'ruleContent')
      return [content === '' ? tool : `${tool}(${content})`]
    })
  })
}
