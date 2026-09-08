import type { Composed, WriteOutcome } from './writing'

/**
 * The command, on screen — before it runs and after.
 *
 * Before a write runs the argv is shown as a line a person could paste; after it runs it
 * stays in a transcript with its exit code. Two things that buys over a confirmation
 * dialog: the flags can be checked against what was meant, and a defect in this app is
 * reportable as a command rather than as a description of a screen.
 *
 * **Nothing here ever hands the result to a shell.** The rendered line is a string for
 * reading and pasting by a person; the argv stays an array everywhere it is actually run,
 * which is Block A's criterion and not a preference.
 *
 * **Ordered, not dated.** A sequence number says which came first, which is what a log is
 * for, and it keeps `No dates, estimates, velocity or burndown` without an argument about
 * whether a timestamp is a schedule.
 *
 * **Memory, not a store.** Nothing here writes the transcript down, exactly as the cache
 * does not, so `No store of its own` holds: a session is as long as it lasts.
 */

/**
 * Which shell the rendered line is for.
 *
 * Named because quoting belongs to a shell and the two escape a quote differently. One
 * rendering that worked in neither would be worse than none.
 */
export type Shell = 'posix' | 'powershell'

/** Characters that make a word need quoting in either shell. Space included, obviously. */
const BARE = /^[A-Za-z0-9_@%+=:,./-]+$/

/**
 * One argument, quoted for the shell named.
 *
 * Single quotes in both, because inside them neither shell expands anything: the only
 * question is how a single quote itself gets in. POSIX closes, escapes and reopens;
 * PowerShell doubles it.
 */
export function quoteFor(argument: string, shell: Shell): string {
  if (argument !== '' && BARE.test(argument)) return argument
  if (shell === 'powershell') return `'${argument.replaceAll("'", "''")}'`
  return `'${argument.replaceAll("'", String.raw`'\''`)}'`
}

/**
 * The whole command as one line.
 *
 * `roadkeep` leads, because the argv this app composes starts at `-C` — the program is
 * whatever the engine resolution named, and a person pasting this wants the name they
 * would type rather than the interpreter and script path behind it.
 */
export function commandLine(
  composed: Composed,
  shell: Shell = 'posix',
  program = 'roadkeep',
): string {
  return [program, ...composed.argv.map((part) => quoteFor(part, shell))].join(' ')
}

/** What became of one command, in the words the transcript shows. */
export type Ran = 'applied' | 'refused' | 'unreadable'

export interface Entry {
  /** Which came first. Not a time: order is what a log is for. */
  readonly seq: number
  readonly verb: string
  readonly root: string
  readonly argv: readonly string[]
  readonly ran: Ran
  /** The process's exit code, or null where it never got that far. */
  readonly code: number | null
  readonly durationMs: number
  /** What the engine wrote on stderr, where it wrote anything. */
  readonly said: string
}

export interface Transcript {
  readonly entries: readonly Entry[]
  /** Add what one command did. Returns the transcript that includes it. */
  remember<T>(composed: Composed, outcome: WriteOutcome<T>): Transcript
}

/**
 * How many commands to keep.
 *
 * Enough to cover a session's worth of work and bounded because this is memory: a window
 * left open for a week should not grow without end.
 */
const KEPT = 200

export function createTranscript(entries: readonly Entry[] = []): Transcript {
  return {
    entries,
    remember<T>(composed: Composed, outcome: WriteOutcome<T>): Transcript {
      const entry: Entry = {
        seq: (entries.at(-1)?.seq ?? 0) + 1,
        verb: composed.verb,
        root: composed.root,
        argv: composed.argv,
        ran: outcome.kind,
        code: outcome.kind === 'unreadable' ? null : outcome.code,
        durationMs:
          outcome.kind === 'unreadable' ? outcome.unreadable.elapsedMs : outcome.durationMs,
        said: outcome.kind === 'unreadable' ? outcome.unreadable.said : '',
      }
      return createTranscript([...entries, entry].slice(-KEPT))
    },
  }
}

/**
 * One entry as a line, for a log a person reads down.
 *
 * The exit code is shown beside the outcome rather than instead of it: they answer
 * different questions, and a write refused with exit 0 is exactly the pair worth seeing.
 */
export function entryLine(entry: Entry, shell: Shell = 'posix'): string {
  const code = entry.code === null ? 'no exit' : `exit ${String(entry.code)}`
  const line = commandLine({ verb: entry.verb, root: entry.root, argv: entry.argv }, shell)
  return `${String(entry.seq)}  ${entry.ran}  ${code}  ${String(entry.durationMs)}ms  ${line}`
}
