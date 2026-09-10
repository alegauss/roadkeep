/**
 * The stream, as a sequence of acts.
 *
 * A headless session emits one JSON object per line: turns, thinking, tool calls, results
 * and a final message. Raw it is a log nobody reads. What matters while it runs is which
 * tool it is calling and on what, and whether it has touched a governed file.
 *
 * **Two of those readings belong to the project.** Which files are governed comes from
 * `config`, since a governed filename written here is the literal the non-goals refuse;
 * which calls are roadkeep's comes from the engine already resolved and the tool names the
 * project's own server publishes. Both are passed in, so a screen marks what this project
 * governs rather than what this app remembers.
 *
 * **What a tool was called *on* is Claude Code's schema and not roadkeep's.** It is read
 * from a short list of the input keys that carry a subject and falls back to naming none.
 * Getting that wrong loses a label and never a fact, because the raw line is on every act.
 *
 * **The raw form stays reachable**: a session that went wrong is diagnosed from what it
 * emitted, and an act summarising its line without keeping it is the summary somebody has
 * to work around.
 */

import { asRecord } from './reading'

/**
 * What this project counts as its own, so nothing here is a literal.
 *
 * Empty is a usable answer — an act is still drawn, just unmarked — which is what a screen
 * gets before `config` has been read.
 */
export interface Marks {
  /** The governed files, as `config` publishes their paths. */
  readonly governed: readonly string[]
  /**
   * How a roadkeep call is recognised: the engine command this app resolved, and the tool
   * prefix the project's own server publishes. Matched case-insensitively as substrings,
   * because a Bash command holds the engine's name inside a longer line.
   */
  readonly engine: readonly string[]
}

export const NOTHING_MARKED: Marks = { governed: [], engine: [] }

/**
 * The input keys that carry what a tool was called on, in the order they are looked for.
 *
 * Claude Code's schema and not roadkeep's, so this is a convenience with a fallback rather
 * than a contract. A tool whose subject is under none of these draws without one.
 */
const SUBJECT_KEYS = ['command', 'file_path', 'path', 'pattern', 'url', 'query', 'prompt']

export type Act =
  /** Text the session produced for a person to read. */
  | { readonly kind: 'said'; readonly seq: number; readonly text: string; readonly line: string }
  /** A tool call, with what it was called on and what it touched. */
  | {
      readonly kind: 'used'
      readonly seq: number
      readonly tool: string
      /** What it was called on, or the empty string where no key carried one. */
      readonly on: string
      /** The call's id, which is what a result refers back to. */
      readonly id: string
      /** True where this call is roadkeep's, by the marks the project supplied. */
      readonly roadkeep: boolean
      /** The governed files this call names, out of the ones the project declared. */
      readonly governed: readonly string[]
      readonly line: string
    }
  /** What a tool call answered. */
  | {
      readonly kind: 'returned'
      readonly seq: number
      readonly id: string
      readonly ok: boolean
      /** The answer, as text. Long output is the raw line's business, not this one's. */
      readonly text: string
      readonly line: string
    }
  /** Read and drawn as nothing more: thinking, rate limits, accounting. */
  | { readonly kind: 'note'; readonly seq: number; readonly about: string; readonly line: string }

function contentOf(object: Record<string, unknown>): unknown[] {
  const message = asRecord(object['message'])
  const content = message?.['content']
  return Array.isArray(content) ? content : []
}

/** What a tool was called on, from the keys that carry a subject. */
export function subjectOf(input: unknown): string {
  const record = asRecord(input)
  if (record === null) return ''
  for (const key of SUBJECT_KEYS) {
    const value = record[key]
    if (typeof value === 'string' && value !== '') return value
  }
  return ''
}

/** Whether this call is roadkeep's, by what the project said roadkeep looks like. */
export function isRoadkeep(tool: string, on: string, marks: Marks): boolean {
  const haystack = `${tool} ${on}`.toLowerCase()
  return marks.engine.some((name) => name !== '' && haystack.includes(name.toLowerCase()))
}

/** Which governed files a call names, out of the ones the project declared. */
export function governedIn(text: string, marks: Marks): string[] {
  const haystack = text.replaceAll('\\', '/')
  return marks.governed.filter((file) => file !== '' && haystack.includes(file))
}

/**
 * Read one line of the stream into the acts it holds.
 *
 * A list, because one assistant message can carry thinking, text and several tool calls,
 * and flattening them into one act would lose the order they happened in.
 */
export function actsOf(line: string, from: number, marks: Marks = NOTHING_MARKED): Act[] {
  const trimmed = line.trim()
  if (trimmed === '') return []

  let source: unknown
  try {
    source = JSON.parse(trimmed)
  } catch {
    return []
  }
  const object = asRecord(source)
  if (object === null) return []

  const type = typeof object['type'] === 'string' ? object['type'] : ''
  let seq = from
  const next = () => seq++

  if (type === 'assistant') {
    return contentOf(object).flatMap((part): Act[] => {
      const item = asRecord(part)
      const kind = typeof item?.['type'] === 'string' ? item['type'] : ''

      if (kind === 'text' && typeof item?.['text'] === 'string' && item['text'] !== '') {
        return [{ kind: 'said', seq: next(), text: item['text'], line: trimmed }]
      }
      if (kind === 'tool_use') {
        const tool = typeof item?.['name'] === 'string' ? item['name'] : ''
        const on = subjectOf(item?.['input'])
        return [
          {
            kind: 'used',
            seq: next(),
            tool,
            on,
            id: typeof item?.['id'] === 'string' ? item['id'] : '',
            roadkeep: isRoadkeep(tool, on, marks),
            governed: governedIn(`${on} ${JSON.stringify(item?.['input'] ?? '')}`, marks),
            line: trimmed,
          },
        ]
      }
      // Thinking arrives with its content empty and a signature beside it, so there is
      // nothing to render and drawing it as text would be a blank turn.
      return [{ kind: 'note', seq: next(), about: kind === '' ? 'assistant' : kind, line: trimmed }]
    })
  }

  if (type === 'user') {
    const results = contentOf(object).flatMap((part): Act[] => {
      const item = asRecord(part)
      if (item?.['type'] !== 'tool_result') return []
      const content = item['content']
      return [
        {
          kind: 'returned',
          seq: next(),
          id: typeof item['tool_use_id'] === 'string' ? item['tool_use_id'] : '',
          ok: item['is_error'] !== true,
          text: typeof content === 'string' ? content : JSON.stringify(content ?? ''),
          line: trimmed,
        },
      ]
    })
    // A `user` line carrying no tool result is still a line — the harness injects one to
    // prompt a turn along. Returning nothing for it would make the act list quietly
    // shorter than the stream it was read from.
    return results.length > 0
      ? results
      : [{ kind: 'note', seq: next(), about: type, line: trimmed }]
  }

  return [{ kind: 'note', seq: next(), about: type === '' ? 'unknown' : type, line: trimmed }]
}

/**
 * Every act in a whole stream, numbered in the order they were emitted.
 *
 * The numbering is the stream's own order and not a clock: what a reader needs from a log
 * is which came first.
 */
export function actsIn(lines: readonly string[], marks: Marks = NOTHING_MARKED): Act[] {
  const acts: Act[] = []
  for (const line of lines) acts.push(...actsOf(line, acts.length + 1, marks))
  return acts
}

/**
 * The governed files a session has touched so far.
 *
 * The question a person watching actually has: it is the evidence that this run changed
 * the backlog, and RG42 is what watches the files themselves.
 */
export function touched(acts: readonly Act[]): string[] {
  const seen = new Set<string>()
  for (const act of acts) {
    if (act.kind === 'used') for (const file of act.governed) seen.add(file)
  }
  return [...seen]
}

/**
 * One act as a line, for a log a person reads down.
 *
 * A tool call leads with the tool and what it was on, because that pair is the whole of
 * what somebody is watching for.
 */
export function actLine(act: Act): string {
  switch (act.kind) {
    case 'said':
      return act.text
    case 'used': {
      const mark = act.roadkeep ? 'roadkeep ' : ''
      const on = act.on === '' ? '' : `  ${act.on}`
      return `${mark}${act.tool}${on}`
    }
    case 'returned':
      return act.ok ? act.text : `failed: ${act.text}`
    default:
      return act.about
  }
}
