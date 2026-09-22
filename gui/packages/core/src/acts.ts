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

import { askOf, type PermissionAsk } from './asking'
import type { EditedFile } from './bridge'
import { asRecord } from './reading'
import { replyOf } from './session'

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
 * The marks of one open project (RG153): the files its `config` governs, and the name its
 * resolved engine runs under.
 *
 * The name is the file the engine's command runs, with no folder and no extension — the
 * launcher a python install goes through, or the engine on PATH — so a Bash call running it
 * is marked. A session reaches the project's own server as `mcp__<server>__<tool>`, and the
 * server is named for that command's first word: a guess, and one that loses a label and
 * never a fact, since the raw line is on every act.
 */
export function marksOf(
  governed: Readonly<Record<string, string>>,
  engine: readonly string[],
): Marks {
  const file = (engine.at(-1) ?? '').split(/[\\/]/).at(-1) ?? ''
  const name = file.replace(/\.[^.]*$/, '')
  const word = /^[a-z0-9]+/i.exec(name)?.[0] ?? ''
  return {
    governed: Object.values(governed).filter((path) => path !== ''),
    engine: [name, word === '' ? '' : `mcp__${word}__`].filter((one) => one !== ''),
  }
}

/**
 * The input keys that carry what a tool was called on, in the order they are looked for.
 *
 * Claude Code's schema and not roadkeep's, so this is a convenience with a fallback rather
 * than a contract. A tool whose subject is under none of these draws without one.
 */
const SUBJECT_KEYS = [
  'command',
  'file_path',
  'notebook_path',
  'path',
  'pattern',
  'url',
  'query',
  'prompt',
]

/**
 * The tools that edit a file, by name (RG243).
 *
 * Claude Code's schema and not roadkeep's, kept the way `SUBJECT_KEYS` is: a tool this does not
 * know loses a row in the list of edited files and never a fact, since its call is still in the
 * stream with its raw line.
 */
const EDITING_TOOLS: ReadonlySet<string> = new Set(['Edit', 'MultiEdit', 'Write', 'NotebookEdit'])

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
  /**
   * A question the session put to the person, holding a call up until it is answered (RG272).
   * Where it stands is read off the lines after it, so the act is the question alone.
   */
  | {
      readonly kind: 'asked'
      readonly seq: number
      readonly ask: PermissionAsk
      /** What the call is on, by the same keys a call's subject is read from. */
      readonly on: string
      readonly line: string
    }
  /**
   * What the person typed as a reply to the session (RG303), on the record where they sent it.
   *
   * An act of its own kind rather than something the session said: the words are not the agent's,
   * and folding them into the notes (RG208) would hide the half of the turn a reader came for.
   */
  | { readonly kind: 'replied'; readonly seq: number; readonly text: string; readonly line: string }
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

  // A question is the one control line drawn as more than a note (RG272). Its answer and a
  // withdrawal stay notes: where the question stands is drawn on the question.
  const ask = askOf(trimmed)
  if (ask !== null)
    return [{ kind: 'asked', seq: next(), ask, on: subjectOf(ask.input), line: trimmed }]

  // The one line in the stream this app wrote itself (RG303). Read before the type is looked at,
  // since it carries a type no branch below claims.
  const reply = replyOf(trimmed)
  if (reply !== null) return [{ kind: 'replied', seq: next(), text: reply, line: trimmed }]

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

/** One row of a stream as drawn: an act, or a run of notes folded into one (RG208). */
export type StreamRow =
  | { readonly kind: 'act'; readonly act: Act }
  | { readonly kind: 'folded'; readonly notes: readonly Act[] }

/**
 * The acts with every run of consecutive notes folded into one row (RG208).
 *
 * **Folded, never dropped.** `actsIn` keeps a note so the act list is never quietly shorter
 * than the stream, and a reader who asked not to see notes has not asked for that to stop
 * being true: each folded row carries the notes it stands for, so its count accounts for them
 * and each is still one disclosure away.
 *
 * **A run, not all of them.** Notes gathered into one row wherever they fell would move a
 * rate limit away from the turn it interrupted; folded where they stand, the order of the
 * stream is the order on screen. Only `note` folds — a failed tool or anything the session
 * said is what a reader is watching for.
 */
export function foldedNotes(acts: readonly Act[]): StreamRow[] {
  const rows: StreamRow[] = []
  let run: Act[] = []
  for (const act of acts) {
    if (act.kind === 'note') {
      run.push(act)
      continue
    }
    if (run.length > 0) rows.push({ kind: 'folded', notes: run })
    run = []
    rows.push({ kind: 'act', act })
  }
  if (run.length > 0) rows.push({ kind: 'folded', notes: run })
  return rows
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

/** One file a session edited, as its own calls account for it (RG243). */
export interface Edited {
  /** The path as the tool was called with it, never shortened or resolved here (§RG65). */
  readonly path: string
  /** How many editing calls named it. */
  readonly calls: number
  /** The seq of the last of them. */
  readonly last: number
  /** True where the result answering that last call has arrived (RG244). */
  readonly answered: boolean
  /** True where the result answering that last call failed. A result not yet in is not failed. */
  readonly failed: boolean
  /** True where the path is one of the files the project governs. */
  readonly governed: boolean
}

/**
 * The files a session edited, grouped by path in the order each was first edited (RG243).
 *
 * `touched` keeps the governed files a call names, which is the backlog; this keeps every file
 * an editing call was made on, which is the code. It is the session's own account — whether
 * the disk agrees is a different read — so a call is counted as made, and a failure is the one
 * its answer reported.
 */
export function editedIn(acts: readonly Act[]): Edited[] {
  const answered = new Map<string, boolean>()
  for (const act of acts) if (act.kind === 'returned' && act.id !== '') answered.set(act.id, act.ok)

  const byPath = new Map<string, Edited>()
  for (const act of acts) {
    if (act.kind !== 'used' || act.on === '' || !EDITING_TOOLS.has(act.tool)) continue
    const answer = answered.get(act.id)
    const was = byPath.get(act.on)
    byPath.set(act.on, {
      path: act.on,
      calls: (was?.calls ?? 0) + 1,
      last: act.seq,
      answered: answer !== undefined,
      failed: answer === false,
      // Named by the path and not by the input, whose content may mention a governed file.
      governed:
        was?.governed ?? governedIn(act.on, { governed: act.governed, engine: [] }).length > 0,
    })
  }
  return [...byPath.values()]
}

/** What a session's own answer says the file was before it touched it (RG280). */
export type FileOrigin = 'created' | 'changed'

/**
 * What a session did to a file (RG280), its answer and the disk together: created it, changed
 * one that was there, deleted one that was there, or created one that is gone now.
 */
export type FileChange = 'created' | 'changed' | 'deleted' | 'undone'

/**
 * The letter each change is marked with, as a source-control list marks one.
 *
 * Here and not in the catalogue because a letter is not prose: `A` and `M` are what a diff and
 * every review tool write, in whatever language the window speaks, and the word beside it is
 * what the catalogue says.
 */
export const CHANGE_LETTER: Readonly<Record<FileChange, string>> = {
  created: 'A',
  changed: 'M',
  deleted: 'D',
  undone: 'X',
}

/**
 * The `tool_use_result` a raw line carries, where it can only be about one call.
 *
 * A `user` line holding two `tool_result`s carries one `tool_use_result` beside them, and
 * nothing in it says which of the two it answers — so that line is not read rather than
 * attributed to the first.
 */
function resultOf(line: string): Record<string, unknown> | null {
  let source: unknown
  try {
    source = JSON.parse(line)
  } catch {
    return null
  }
  const object = asRecord(source)
  if (object === null) return null
  const results = contentOf(object).filter((part) => asRecord(part)?.['type'] === 'tool_result')
  return results.length === 1 ? asRecord(object['tool_use_result']) : null
}

/**
 * Whether the session created the file or changed one that was there (RG280), off the first
 * answered call on the path that succeeded.
 *
 * **The answer is already in the stream.** Claude Code answers a `Write` with a `type` of
 * `create` or `update`, and an `Edit` with `originalFile`, the file as it stood before the call.
 * An `Edit` only lands on a file that was there, so it changed one whatever that field holds —
 * which is why a `null` there, a file too large to carry back, decides nothing.
 *
 * Null where no call on the path has been answered yet: a mark drawn before the answer is a
 * guess, and this list is watched while it fills.
 *
 * *No git command run by this app* bounds it: what the file was before is the session's own
 * answer, never the repository's, so a file somebody else changed in the same minute is not this
 * reader's business.
 */
export function originOf(acts: readonly Act[], path: string): FileOrigin | null {
  const first = firstAnswered(acts, path)
  if (first === null) return null

  const type = first.result['type']
  if (type === 'create') return 'created'
  if (type === 'update') return 'changed'
  // A `Write` from a build that answered without a type says the same thing by what it
  // replaced; every other editing tool needed the file to be there.
  if (first.tool === 'Write') return first.result['originalFile'] === null ? 'created' : 'changed'
  return 'changed'
}

/**
 * The file as it stood before the session first touched it (RG282), out of the same answer
 * `originOf` reads: empty for a file the session created, since every line of it is new.
 *
 * Null where nothing says what it was — no answered call on the path, or an answer that carried
 * no `originalFile` because the file was too large to send back. A comparison is not drawn from
 * a guess: the viewer says it does not know instead.
 */
export function originalIn(acts: readonly Act[], path: string): string | null {
  const first = firstAnswered(acts, path)
  if (first === null) return null

  const original = first.result['originalFile']
  if (typeof original === 'string') return original
  // A `Write` that made the file answers `null` here and says so with its type; anything else
  // answering `null` is a file that was there and did not fit in the answer.
  return original === null && first.result['type'] === 'create' ? '' : null
}

/** The first answered, successful editing call on a path, with what it answered. */
function firstAnswered(
  acts: readonly Act[],
  path: string,
): { readonly tool: string; readonly result: Record<string, unknown> } | null {
  const answers = new Map<string, Extract<Act, { kind: 'returned' }>>()
  for (const act of acts) if (act.kind === 'returned' && act.id !== '') answers.set(act.id, act)

  for (const act of acts) {
    if (act.kind !== 'used' || act.on !== path || !EDITING_TOOLS.has(act.tool)) continue
    const answer = answers.get(act.id)
    if (answer === undefined || !answer.ok) continue
    const result = resultOf(answer.line)
    if (result !== null) return { tool: act.tool, result }
  }
  return null
}

/**
 * What the session did to a file, with the disk's answer finishing it (RG280).
 *
 * Was there and missing now is deleted; created and missing now is its own word, since nobody
 * reading a list wants a file the session made and then lost drawn as one it deleted. Where the
 * disk has not answered, or the file is outside the session's root and so never asked about, the
 * session's own answer stands.
 */
export function changeOf(origin: FileOrigin | null, standing: DiskStanding): FileChange | null {
  if (origin === null) return null
  if (standing === 'missing') return origin === 'created' ? 'undone' : 'deleted'
  return origin
}

/** One edit a session made to a file, as its own call carried it (RG246). */
export interface FileEdit {
  /** The seq of the call that made it, which is where it stands in the stream. */
  readonly seq: number
  readonly tool: string
  /** What it replaced. Empty for a `Write`, which replaces whatever was there. */
  readonly before: string
  /** What it put there; for a `Write`, the content it wrote. */
  readonly after: string
  /** True where the call has been answered at all. */
  readonly answered: boolean
  /** True where the answer failed. */
  readonly failed: boolean
}

/** One tool call's input, out of the raw line the act kept. */
function inputOf(act: Act): Record<string, unknown> | null {
  if (act.kind !== 'used') return null
  let source: unknown
  try {
    source = JSON.parse(act.line)
  } catch {
    return null
  }
  const object = asRecord(source)
  if (object === null) return null
  for (const part of contentOf(object)) {
    const item = asRecord(part)
    if (item?.['type'] === 'tool_use' && item['id'] === act.id) return asRecord(item['input'])
  }
  return null
}

function said(input: Record<string, unknown>, key: string): string {
  const value = input[key]
  return typeof value === 'string' ? value : ''
}

/**
 * What the session changed inside one file, in stream order (RG246).
 *
 * **The before comes from the session and never from git**, which `No git command run by this
 * app` refuses: an `Edit` carries what it replaced and what it put there, a `MultiEdit` a list
 * of those pairs, and a `Write` the whole content. Read back out of the raw line every act
 * keeps, so nothing had to be stored for this.
 *
 * **The input is Claude Code's schema**, so a call whose input carries none of those keys draws
 * no block and keeps its raw line — the fallback `subjectOf` already takes.
 */
export function editsOf(acts: readonly Act[], path: string): FileEdit[] {
  const answered = new Map<string, boolean>()
  for (const act of acts) if (act.kind === 'returned' && act.id !== '') answered.set(act.id, act.ok)

  const edits: FileEdit[] = []
  for (const act of acts) {
    if (act.kind !== 'used' || act.on !== path || !EDITING_TOOLS.has(act.tool)) continue
    const input = inputOf(act)
    if (input === null) continue
    const answer = answered.get(act.id)
    edits.push(
      ...carriedBy(input).map((carried) => ({
        seq: act.seq,
        tool: act.tool,
        answered: answer !== undefined,
        failed: answer === false,
        ...carried,
      })),
    )
  }
  return edits
}

/** The pairs one call's input carries: a list for a `MultiEdit`, one for the rest, none for a
 * call whose input names neither what it replaced nor what it put there. */
function carriedBy(
  input: Record<string, unknown>,
): { readonly before: string; readonly after: string }[] {
  const pairs = input['edits']
  if (Array.isArray(pairs)) {
    return pairs.flatMap((pair) => {
      const one = asRecord(pair)
      return one === null
        ? []
        : [{ before: said(one, 'old_string'), after: said(one, 'new_string') }]
    })
  }
  const before = said(input, 'old_string')
  const after =
    said(input, 'new_string') === '' ? said(input, 'content') : said(input, 'new_string')
  return before === '' && after === '' ? [] : [{ before, after }]
}

/**
 * Whether an edit is in the file as it was read (RG246): found, gone, or not checkable.
 *
 * Gone says only that the text is not there now — a later edit may have overwritten it,
 * something may have reverted it, or it may never have applied.
 */
export type EditStanding = 'in-the-file' | 'not-in-the-file' | 'unchecked'

/**
 * Look for what an edit put there in the text the viewer read (RG246).
 *
 * A plain substring test over two strings the screen already holds: nothing is parsed and
 * nothing is diffed. An edit that put nothing there — a deletion — has nothing to look for,
 * and a file that was not read has nothing to look in.
 */
export function editStanding(edit: FileEdit, text: string | null): EditStanding {
  if (text === null || edit.after === '') return 'unchecked'
  return text.includes(edit.after) ? 'in-the-file' : 'not-in-the-file'
}

/**
 * Where an edited file stands on disk (RG244): not answered for yet, outside the session's
 * root, not there, or there and changed or not since the session started.
 */
export type DiskStanding = 'unasked' | 'outside' | 'missing' | 'changed' | 'unchanged'

export interface OnDisk {
  readonly standing: DiskStanding
  /**
   * True where the session's last call on the file reported success and the disk does not
   * hold it: the file is not there, or has not changed since the session started. The
   * disagreement a reader opens the list to find.
   */
  readonly disagrees: boolean
}

/**
 * What the disk says about one file the session edited, read against when it started (RG244).
 *
 * **Unchanged is proved, never assumed.** A file reads as unchanged only where its time is
 * earlier than a start that parses; anything else that is there reads as changed, which says
 * when the disk changed it and nothing about the session.
 *
 * @param at the side with the disk's answer for this path, or undefined before it answered
 * @param started the session's `started`, an ISO time
 */
export function onDisk(edited: Edited, at: EditedFile | undefined, started: string): OnDisk {
  const standing = standingOf(at, started)
  const reported = edited.answered && !edited.failed
  return {
    standing,
    disagrees: reported && (standing === 'missing' || standing === 'unchanged'),
  }
}

function standingOf(at: EditedFile | undefined, started: string): DiskStanding {
  if (at === undefined) return 'unasked'
  if (!at.inside) return 'outside'
  if (!at.present) return 'missing'
  const since = Date.parse(started)
  const changed = Date.parse(at.changed)
  return !Number.isNaN(since) && !Number.isNaN(changed) && changed < since ? 'unchanged' : 'changed'
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
    case 'replied':
      return act.text
    case 'used': {
      const mark = act.roadkeep ? 'roadkeep ' : ''
      const on = act.on === '' ? '' : `  ${act.on}`
      return `${mark}${act.tool}${on}`
    }
    case 'returned':
      return act.ok ? act.text : `failed: ${act.text}`
    case 'asked':
      return act.on === '' ? `asks for ${act.ask.tool}` : `asks for ${act.ask.tool}  ${act.on}`
    default:
      return act.about
  }
}
