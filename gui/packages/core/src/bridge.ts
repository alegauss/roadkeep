/**
 * The one way anything reaches the renderer, and the reason the web port is a transport
 * swap rather than a rewrite.
 *
 * The renderer is given exactly one object on `window`, and this file is its type. Under
 * Electron a preload fills it in over IPC; served from a web server the same object would
 * be filled in over HTTP, and the React above it cannot tell, because nothing in front of
 * this interface names a process, a channel or a path. `identify` is what makes that
 * checkable instead of asserted: the renderer can ask which transport answered without
 * knowing how to reach any other one.
 *
 * Widening this interface is the one change that can quietly cost the port, so a method
 * added here is a method a web transport has to be able to implement.
 */

import type { Agent } from './agent'
import type { AskAnswer } from './asking'
import type { BuildIdentity } from './build'
import type { CapabilityReport } from './capabilities'
import type { ProjectCatalogue } from './catalogue'
import type { ResolvedEngine } from './engine-resolution'
import type { GateHealth } from './gate'
import type { Gloss } from './gloss'
import type { Opening } from './opening'
import type { BriefPayload, Declared, HeldClaim } from './payloads'
import type { Actionable } from './repairing'
import type { KnownRoot, ScanRoot } from './roots'
import type { SessionOutcome } from './session'
import type { PreferenceKey } from './preferences'
import type { Settings, SettingsRead } from './settings'
import type { ReadingStands, RememberedReadings } from './readings'
import type { MovedPath } from './watching'
import type { EngineFailure, EngineRequest, EngineResult } from './transport'

/** The single property the preload adds to `window`. */
export const BRIDGE_KEY = 'roadkeep'

/** What is carrying the calls. A packaged desktop build is always `ipc`. */
export type TransportName = 'ipc' | 'http'

export interface BridgeIdentity {
  readonly transport: TransportName
  /**
   * What this build is, so a defect report carries it and an about surface can show it.
   *
   * It rides on `identify` rather than arriving as a method of its own: widening the
   * method set is the change that costs the port, and a web transport answering "which
   * build am I" is answering the same question this already asks.
   */
  readonly build: BuildIdentity
}

/**
 * What the shell holds, as the renderer receives it.
 *
 * The settings themselves plus what reading them lost, which is `SettingsRead` unchanged —
 * and one field the renderer could not work out for itself.
 */
export interface LaunchSettings extends SettingsRead {
  /**
   * Which of the locales this build ships the window is speaking, already chosen.
   *
   * Resolved on the shell's side because `Settings.locale` may be empty, and empty means
   * *whatever the desktop says* — a question only a process can ask. What crosses is the
   * answer, so the renderer never has two ideas of what language it is in.
   */
  readonly locale: string
  /**
   * How many projects a cold start may read at once (RG250), already decided.
   *
   * `locale`'s arrangement and for its reason: the settings may say nothing, and what stands
   * in for nothing is one project per four cores — a count only a process can take. What
   * crosses is the number, so the renderer never works one out from a machine it cannot see.
   */
  readonly projectsAtOnce: number
}

export interface RendererBridge {
  identify(): Promise<BridgeIdentity>
  /**
   * A method of its own rather than another field on `identify`, and the line between them
   * is whether the answer can change while the app runs. A build cannot; a settings file is
   * a person's to edit, and one asked for once is one a restart is the only way to reread.
   */
  settings(): Promise<LaunchSettings>
  /**
   * Keep one preference somebody just chose, which is what makes the file the source of it
   * (RG207).
   *
   * The ground and the language were a method each, `saveTheme` (RG87) and `saveLocale`
   * (RG116), and the second said a third would be the moment to ask again. The settings
   * screen is that third, and the answer is one method over `PREFERENCES`: not
   * `Partial<Settings>`, which would hand a page the roots and the ignore list, but the rows a
   * person chooses from a screen and the check each value passes.
   *
   * **Refused out loud.** A key outside the table, or a value its row refuses — a ground that
   * is not one, a tag this build does not ship — rejects and writes nothing, so a page says
   * the choice was not kept rather than finding out at the next launch.
   */
  savePreference<K extends PreferenceKey>(key: K, value: Settings[K]): Promise<void>
  /**
   * The projects under the roots the person named, scanned now and folded into what this
   * carrier already held (RG143). What `open` and `run` accept is exactly this list.
   */
  projects(): Promise<ProjectCatalogue>
  /**
   * Open one project where its engines can be held, and answer what the opening found.
   *
   * A method of its own because the opening is facts no read repeats: which command line
   * resolution chose, whether it reached the copy the project declares, what this build can
   * run. The carrier keeps the engines; the renderer gets the answer.
   */
  open(root: string): Promise<OpenedProject>
  /**
   * Run one request against an open project, through the stack the carrier holds for it.
   *
   * **One method for every verb, and not one per screen.** `core`'s client builds over it as
   * over any transport, so a web service implements this and `open` and the screens above
   * do not change. What it will not run is anything neither verb table composes.
   */
  run(root: string, request: BridgedRequest): Promise<BridgedResult>
  /**
   * Be told, while listening, what the carrier hears that nobody asked about (RG144).
   *
   * **A subscription and not an IPC detail**, because the port is why: over HTTP this is a
   * server-sent stream, and a listener shape only `ipcRenderer.on` could satisfy is the
   * coupling this interface exists to refuse. Synchronous and answering the way to stop, so a
   * screen can give it up in the same effect cleanup that took it.
   *
   * @param key which one of the topic's sources — a root for `governed`, a session's id for
   *   `session` — so a screen hears its own project and not every project the window holds.
   */
  subscribe<T extends Topic>(
    topic: T,
    key: string,
    listener: (event: TopicEvents[T]) => void,
  ): () => void
  /**
   * The roots the settings name, each marked present or missing (RG146). A root that has
   * gone away is kept and marked, never dropped: a disconnected drive is not the person
   * taking the root back. Whether a folder is there is a disk's question, so it is asked here.
   */
  roots(): Promise<readonly KnownRoot[]>
  /**
   * A folder the person picked, or null where they cancelled (RG146).
   *
   * **Chosen by the shell, never typed by the renderer.** The desktop answers with a native
   * dialog and a web service would answer the same call with a text box, and either way what
   * comes back is a folder somebody chose. `saveRoots` keeps a new root only if it came from
   * here.
   */
  chooseRoot(): Promise<string | null>
  /**
   * Keep the roots the window now holds, answered with each one's presence (RG146).
   *
   * The third write, and still a method that names what it writes. Its design took the skip
   * list and the width with it as one statement about where to look; it takes the roots
   * alone, because the window edits nothing else, and writing back a skip list read at launch
   * would undo a hand edit made since — the reason every save here re-reads the file.
   */
  saveRoots(roots: readonly ScanRoot[]): Promise<readonly KnownRoot[]>
  /**
   * Hand one line to a Claude Code session (RG153): take it with `brief --claim` and start the
   * session from that payload, or say why not.
   *
   * **The renderer names a line and nothing else.** The prompt is built on the far side from
   * the brief the far side read, so a page cannot start an agent with words of its own — which
   * over HTTP is the same call, a line in and an answer out. A held line is named and nothing
   * is taken, and a line the engine does not call ready is not taken either.
   */
  handOver(root: string, id: string): Promise<HandedOver>
  /**
   * Hand one gate finding to a Claude Code session (RG263): the door that closes it, and the
   * finding it was offered under, as the prompt.
   *
   * **The renderer names a door and nothing else** — `offered` and `which`, the addressing
   * `door` already uses — for `handOver`'s reason: the prompt is built on the far side out of
   * the answer the far side kept, so a page cannot start an agent with words of its own.
   *
   * No claim is taken, because a finding is not a line: there is no marker to move and nothing
   * to hold. A batch the files have moved under names nothing, which is the door keep's rule
   * and the only staleness there is to report here.
   */
  handOverDoor(root: string, offered: string, which: number): Promise<HandedOver>
  /**
   * Answer a session that stopped, by continuing it (RG269): the reply is the person's words, and
   * the session goes on under the same key, its lines keeping their places.
   *
   * **Nothing about the session crosses but its key and the words.** The far side holds its root,
   * its id and what it was handed, and a reply to a session it does not hold, or to one still
   * running, is withheld. A line somebody else took since the session stopped is named, as a
   * handover names a held one, and nothing is resumed.
   *
   * `allowed` is what the person granted for that turn alone (RG270): tools, each one the session
   * was refused. A tool it was not refused is not a grant this carrier sends.
   */
  replySession(key: string, text: string, allowed: readonly string[]): Promise<HandedOver>
  /**
   * Answer a question a running session is waiting on (RG272): allow the call, allow it for the
   * session, or decline it.
   *
   * **Named by the question, never spelled.** The far side finds the question in the lines it
   * holds and composes the answer out of it, so a page cannot send a session an input or a rule of
   * its own. A question that is not open — answered, withdrawn, or on a session that stopped — is
   * withheld with the reason.
   */
  answerSession(key: string, requestId: string, answer: AskAnswer): Promise<AnsweredAsk>
  /**
   * The project's governed files, each with when the disk last changed it (RG153).
   *
   * Beside the landing rather than in it: what moved in a line is the engine's answer, and
   * which file changed when is the filesystem's — a question only the side with the disk can
   * ask, which over HTTP is the side that has the checkout.
   */
  governedAt(root: string): Promise<readonly GovernedFile[]>
  /**
   * The files a session's calls say it edited, each as the disk has it now (RG244).
   *
   * **Named by the session and not by a root**, so the far side takes the root from its own
   * record of what it started and a page cannot aim a stat at a folder it chose. A path that
   * resolves outside that root is answered as outside and never asked of the disk: an agent
   * may write a memory file or a sibling checkout, and naming it is all this owes a reader.
   *
   * @param paths as the session's own calls spelled them, which is what each answer carries back
   */
  editedAt(key: string, paths: readonly string[]): Promise<readonly EditedFile[]>
  /**
   * One file a session edited, as the disk holds it now, or why it will not be read (RG245).
   *
   * `editedAt`'s arrangement: named by the session, resolved under the root the far side started
   * it in, and refused outside it. Refused as well past `FILE_TEXT_CEILING` and where it is not
   * text, each as a code a screen says in its own language. Nothing is kept on either side: a
   * screen asks again for the file as it is.
   *
   * @param path as the session's own call spelled it
   */
  fileText(key: string, path: string): Promise<FileText>
  /**
   * The gate verdicts this carrier holds, dated against the files they were taken on (RG152).
   *
   * A read of a ledger and never a run: `lint` is the most expensive read there is, so it
   * runs where somebody asked for it — through `run`, like every other verb — and what is on
   * record crosses here. A project nobody has gated is simply not in the answer, which is the
   * difference between `unknown` and clean.
   */
  gates(): Promise<readonly ProjectGate[]>
  /**
   * What a verb printed at some earlier launch, for the projects whose files have not moved
   * since (RG251).
   *
   * A read of a file this app owns and never of a backlog: the repository is the store, and
   * what crosses here is an answer somebody already paid a process start for. Every entry is
   * checked against the files it came off before it crosses, so a screen draws a remembered
   * row only where nothing it was read from has changed.
   */
  readings(): Promise<RememberedReadings>
  /**
   * Whether what was remembered about one project still answers for it (RG252).
   *
   * One process on the far side — the engine resolved, the files stamped — against the four
   * an opening spends. A screen that hears `stands` keeps the row it drew and stops; anything
   * else is a project to read in full.
   */
  check(root: string): Promise<ReadingStands>
  /**
   * Ask Claude Code what one task means, in plain words (RG284).
   *
   * **A read and not a session.** One query with no tool, nothing kept and a schema for its
   * answer: a session (RG153) is a turn that may write and that somebody answers questions for,
   * and asking what a line means is neither. Nothing about it joins `sessions`.
   *
   * **The renderer names a line, never a prompt.** The far side briefs the id itself and frames
   * that payload, for `handOver`'s reason — a page cannot put words of its own to an agent — and
   * the language is the one the window already runs in, which main resolved at launch.
   *
   * **Answered from what was kept, where one was** (RG287): the same line in the same language
   * asks Claude Code nothing and comes back at once, marked stale where the line has moved since.
   *
   * @param again ask anew and replace what was kept, which is what Regenerate does
   */
  gloss(root: string, id: string, again?: boolean): Promise<GlossAnswer>
  /**
   * Give up on a gloss that is still running (RG284). Nothing is kept either way, and a name
   * nothing is running under does nothing.
   */
  cancelGloss(root: string, id: string): Promise<void>
  /** Every session this process started, each with what it has written so far (RG153). */
  sessions(): Promise<readonly SessionRecord[]>
  /**
   * Stop one session (RG153). Its claim is left to the registry's own expiry: the session
   * may have moved the line, and releasing it here would undo a state nobody reviewed.
   */
  stopSession(key: string): Promise<void>
  /**
   * Take one door the engine offered (RG165).
   *
   * **A door is the engine's own argv and never this app's.** The guard in front of `run`
   * runs what the verb tables spell, which a door is not — so this goes the other way round:
   * the side that received the answer kept its doors, and a caller names the answer
   * (`offered`), which door in it, and the prose for the blanks the engine left. What runs is
   * the argv that came back, with those words in those places and nothing else changed.
   *
   * A name the far side no longer holds — the project's files have moved since, or this is
   * another launch — is refused rather than guessed at, since a door offered against files
   * that changed may no longer close anything.
   *
   * @param words one per blank, in the order they appear. A door that needs none takes none.
   */
  door(
    root: string,
    offered: string,
    which: number,
    words: readonly string[],
  ): Promise<BridgedResult>
}

/**
 * One project's gate verdict as it crosses (RG152).
 *
 * The root is the carrier's spelling of it, so a caller matches it the way the catalogue
 * compares two spellings of one folder, and never by string equality.
 */
export interface ProjectGate {
  readonly root: string
  readonly health: GateHealth
}

/** One governed file, and when the disk last changed it (RG153). */
export interface GovernedFile {
  /** The role the project's config declared it under: roadmap, changelog, and the rest. */
  readonly role: string
  /** The path as the config spells it, which is what an act naming a file is matched against. */
  readonly path: string
  /**
   * When it last changed, as the filesystem says it. Empty where the file is not there, which
   * is a state a project has before anything has written that role.
   */
  readonly changed: string
  readonly present: boolean
}

/** One file a session edited, as the disk has it now (RG244). */
export interface EditedFile {
  /** The path as the session's call spelled it, which is what a row is matched on. */
  readonly path: string
  /**
   * The path to draw: relative to the session's root with forward slashes where it is under
   * that root, and as spelled where it is not. Shortened by the side with the platform, since
   * which two spellings are one folder is a platform's question.
   */
  readonly shown: string
  /** False where the path resolves outside the session's root, which is never asked of the disk. */
  readonly inside: boolean
  readonly present: boolean
  /** When the disk last changed it, or empty where it is not there or was not asked. */
  readonly changed: string
}

/**
 * Why a file a session edited was not read (RG245). A code and not a sentence, as `WithheldCode`
 * is one: the catalogue says each in every language this build ships.
 */
export type FileRefusal =
  /** No session this process started goes by that key. */
  | 'no-session'
  /** The path resolves outside the session's root, so the disk was not asked. */
  | 'outside'
  /** Nothing is there. */
  | 'missing'
  /** There, and something other than a file: a folder, or what this process may not read. */
  | 'unreadable'
  /** Larger than `FILE_TEXT_CEILING`; the fields carry its size and the ceiling. */
  | 'too-large'
  /** A NUL in its first block, which is what a file that is not text has. */
  | 'not-text'

/** One edited file as the disk holds it now, or the refusal (RG245). */
export type FileText =
  | {
      readonly kind: 'read'
      /** As the call spelled it. */
      readonly path: string
      /** Under the root with forward slashes, as `EditedFile.shown` is. */
      readonly shown: string
      /** The file's characters, decoded as UTF-8 and nothing more. */
      readonly text: string
      readonly bytes: number
    }
  | {
      readonly kind: 'refused'
      readonly path: string
      readonly code: FileRefusal
      /** What the sentence's holes are filled with: `bytes` and `ceiling` for `too-large`. */
      readonly fields: Readonly<Record<string, string>>
    }

/**
 * What a session was started about (RG263).
 *
 * Two shapes because there are two, and a screen that had only the first drew a session about
 * a gate finding as a line with no symptom, no design and no deps. A union rather than a brief
 * with everything optional: the landing compares a line's brief before and after, which is a
 * question a finding cannot be asked, and `kind` is what stops that being asked of it.
 */
export type Handed =
  | { readonly kind: 'line'; readonly brief: BriefPayload }
  | {
      readonly kind: 'finding'
      readonly finding: Actionable
      /** The door's own argv, blanks and all — what the agent was told to run. */
      readonly argv: readonly string[]
    }

/**
 * One session, as the process holding it knows it (RG153). Plain data, so it crosses as it is.
 */
export interface SessionRecord {
  /** This process's name for it, which is what its events are keyed on. */
  readonly key: string
  readonly root: string
  /** The line it was handed, or empty where it was handed a finding instead (RG263). */
  readonly id: string
  /**
   * When the process was spawned, as an ISO time (RG244): what an edited file's time is read
   * against, so a file the disk has not changed since is told from one it has.
   */
  readonly started: string
  /** What it was started from, unrewritten: a line's claiming brief, or a gate finding. */
  readonly handed: Handed
  /** Which Claude Code runs it, as resolution found it. */
  readonly agent: Agent
  /**
   * Every line of its stream so far, raw and in order — with each answer this window wrote back
   * to a question it asked (RG272), at the place it was sent, so a question reads as answered off
   * the lines alone.
   */
  readonly lines: readonly string[]
  /**
   * Every path under the root that moved on disk while it ran (RG247), folded per path.
   *
   * What the stream cannot name: a formatter or a generator run through Bash moves files no
   * edit call mentions. Unattributed on purpose — anything else writing under the project in
   * that time is in here too.
   */
  readonly moved: readonly MovedPath[]
  /** How many paths were left out at the ceiling. */
  readonly movedBeyond: number
  /** How it ended, or null while it runs. */
  readonly outcome: SessionOutcome | null
}

/**
 * What handing a line over did (RG153). Every way of not starting is its own kind, since each
 * is a different thing for a screen to say and none of them is the session going wrong.
 */
export type HandedOver =
  | { readonly kind: 'started'; readonly session: SessionRecord }
  /** Somebody holds the line: named, and nothing taken — block F's third criterion. */
  | { readonly kind: 'held'; readonly held: readonly HeldClaim[] }
  /** The engine does not call the line ready. Its word, carried and not worked out. */
  | { readonly kind: 'unready'; readonly readiness: string }
  /** The engine refused to brief the line or to take it. Its sentence, quoted. */
  | { readonly kind: 'refused'; readonly said: string }
  /** No Claude Code answered on this machine, so nothing was taken. Every command tried. */
  | { readonly kind: 'unavailable'; readonly tried: readonly (readonly string[])[] }
  /** Not a project the carrier opens, or not a line id. */
  | { readonly kind: 'withheld'; readonly reason: string }

/**
 * What asking for a gloss did (RG284).
 *
 * Every way of not answering is its own kind, as a hand-over's is: no Claude Code on the machine,
 * one that is not signed in, a run that failed with what it said, and one the reader gave up on.
 * A screen says a different thing about each, and none of them is the gloss being wrong.
 */
export type GlossAnswer =
  | {
      readonly kind: 'said'
      readonly gloss: Gloss
      /** The model that answered and the Claude Code it ran under, as the run named them. */
      readonly model: string
      readonly version: string
      /** True where this was kept from an earlier asking rather than asked for now (RG287). */
      readonly kept: boolean
      /** True where the line has moved since it was written: still shown, and said to be old. */
      readonly stale: boolean
    }
  /** No Claude Code answered on this machine. Every command tried, as a hand-over reports it. */
  | { readonly kind: 'unavailable'; readonly tried: readonly (readonly string[])[] }
  /** It ran and said nothing usable: its own words, quoted. */
  | { readonly kind: 'failed'; readonly said: string }
  /** The reader gave up on it, or the window closed under it. */
  | { readonly kind: 'cancelled' }
  /** Not a project the carrier opens, or not a line id. */
  | { readonly kind: 'withheld'; readonly reason: string }

/** What answering a session's question did (RG272): sent, or why not. */
export type AnsweredAsk =
  { readonly kind: 'answered' } | { readonly kind: 'withheld'; readonly reason: string }

/**
 * What each topic carries, one event at a time (RG144). The table main, the preload and a
 * screen all read, so none of them can drift on a name or on a shape.
 */
export interface TopicEvents {
  /**
   * A root whose governed files moved — the whole event. What moved is answered by reading
   * again, and the carrier's cache is keyed on a stamp of the same files, so a spurious one
   * costs a read and never a wrong answer.
   */
  readonly governed: { readonly root: string }
  /**
   * One line of a session's stream, raw, with its place in the stream — or how it ended.
   *
   * The index is what lets a screen that asked `sessions` for the lines so far and then heard
   * the rest put them together with nothing doubled and nothing missed (RG153).
   */
  readonly session:
    | { readonly session: string; readonly index: number; readonly line: string }
    | { readonly session: string; readonly outcome: SessionOutcome }
    /**
     * The session was answered and runs again (RG269), so the outcome a screen holds is over. Its
     * own event because nothing else says so: the lines that follow could be a turn still going.
     */
    | { readonly session: string; readonly resumed: true }
    /**
     * What has moved on disk under the session's root so far (RG247), the whole list each time.
     *
     * The list and not the difference, because it is folded per path and a screen that missed
     * one event would otherwise be wrong until the session ended. Held for a quiet moment on
     * the far side, so a formatter touching two hundred files is one event and not two hundred.
     */
    | {
        readonly session: string
        readonly moved: readonly MovedPath[]
        readonly beyond: number
      }
  /**
   * The walk behind the remembered record landed, and it changed something (RG180).
   *
   * **Keyed on nothing, because there is one catalogue.** `governed` is keyed on a root and
   * `session` on a session; what moved here is the one list this window holds, so the key is
   * `EVERY_SOURCE` and a screen subscribes to it once.
   *
   * The event carries no record — it says how many entries the fold changed, and a screen
   * asks `projects` again for what they are. An event is a reason to read, which is the same
   * arrangement `governed` chose and for the same reason: a copy of what was read is a second
   * answer that can disagree with the first.
   */
  readonly catalogue: { readonly changed: number }
  /**
   * A verdict the carrier's gate left, for the project it is about (RG166).
   *
   * Its own topic rather than a `governed` event, because the files did not move: a screen
   * told that they had would read the backlog again for nothing, and a row that wanted the
   * verdict would have to ask for it separately anyway. The health is the whole event —
   * `gates` answers the same shape, so a row fills the same way whichever it came from.
   */
  readonly gate: ProjectGate
  /**
   * One line of a gloss's stream, raw, while it is being written (RG297).
   *
   * A structured answer arrives all at once, so its stream is the only progress there is: the
   * files it reads (RG288), what it says on the way, and the notes that show it is still thinking.
   * The line is the one a session's event carries, so a screen reads it with `actsIn` and draws
   * it with the session's own rows.
   *
   * **Keyed on the project, carrying the line**, as `governed` is keyed: a window has one dialog
   * open at a time, and which line it is about is the dialog's to check.
   */
  readonly gloss: {
    readonly root: string
    readonly id: string
    /** Its place in the run's stream, from 0, which a new asking starts again. */
    readonly index: number
    readonly line: string
  }
}

export type Topic = keyof TopicEvents

/** The channel each topic's events arrive on, main to renderer. */
export const BRIDGE_TOPICS = {
  governed: 'roadkeep:on-governed',
  session: 'roadkeep:on-session',
  gate: 'roadkeep:on-gate',
  catalogue: 'roadkeep:on-catalogue',
  gloss: 'roadkeep:on-gloss',
} as const satisfies Record<Topic, string>

/**
 * The key that means every source of a topic (RG178).
 *
 * A list wants the lot and cannot name them: it does not know which sessions there are until
 * it has asked, and one started after that has a key it never heard of. So the topic carries
 * one key standing for all of them — one subscription and one shape, rather than one per row
 * and still blind to the next.
 *
 * A source can never be called this: a session's key is this process's own name for it, built
 * from a root and an id, and a root is a path.
 */
export const EVERY_SOURCE = '*'

/**
 * Giving a subscription up. No method of its own — it is the function `subscribe` answered —
 * so it is named here beside the channels rather than among them.
 */
export const BRIDGE_UNSUBSCRIBE = 'roadkeep:unsubscribe'

/**
 * A request as it crosses: the root is the method's own argument, and a cancellation cannot
 * cross at all — a signal is not a value, and the renderer honours its own.
 */
export type BridgedRequest = Omit<EngineRequest, 'root' | 'signal'>

/**
 * What `run` answers. The engine's result, or the failure as its fields: a thrown class does
 * not survive the crossing, and `EngineCallFailed` is rebuilt on the far side from these.
 */
export type BridgedResult =
  | {
      readonly kind: 'ran'
      readonly result: EngineResult
      /**
       * What to call this answer's doors by, where it carried any (RG165).
       *
       * The doors themselves are in the answer and the renderer reads them; what crosses is
       * a name for the ones the far side kept, so running one is a caller naming which and
       * never a caller handing over an argv.
       */
      readonly offered?: string
    }
  | {
      readonly kind: 'failed'
      readonly reason: EngineFailure
      /**
       * The sentence, in English, for a log and a defect report.
       *
       * @notForScreen `refusalOf(answered, say)`, which reads `code`
       */
      readonly message: string
      /** Which of this app's sentences applies, or empty where the prose is not translated. */
      readonly code: WithheldCode
      /** What the sentence's holes are filled with. Empty for the codes that take none. */
      readonly fields: Readonly<Record<string, string>>
      readonly durationMs: number
    }

/**
 * Which of this app's own sentences explains a request the carrier would not run (RG192).
 *
 * A code and not the sentence, for the reason `UnreadableCode` is one: the sentence is a
 * translation, the catalogue holds one per code in every language this build ships, and a
 * screen looks it up rather than drawing what the far side wrote.
 *
 * **The empty string is the state to read twice.** Two different things arrive as it and
 * both are drawn as they came: prose that is not this app's — a transport's, an engine's —
 * and this app's own report of a command line it composed wrongly. The second is a defect
 * report naming a verb and a flag, so translating it would say the same English words in a
 * Portuguese sentence and cost a reader the one thing that identifies the bug.
 */
export type WithheldCode =
  /** No method by that name crosses this bridge. */
  | 'not-carried'
  /** No door by that name is on offer for this project. */
  | 'no-such-door'
  /** A door takes one word for each blank it has, and that was not it. */
  | 'not-the-words'
  /** Not a project the scan of the person's roots found. */
  | 'not-catalogued'
  /** The project would not open, so a request that needed it open never ran. */
  | 'not-open'
  /** The prose is somebody else's, or this app's own report of what it composed. */
  | ''

/** The carrier would not open it: a folder no root the person named holds (RG143). */
export interface Withheld {
  readonly kind: 'withheld'
  readonly root: string
  readonly reason: string
}

/**
 * An opening as it crosses: every fact it found and none of the process behind it. The
 * three ways of not opening are plain data already and cross unchanged; an open project
 * crosses without its client, which the renderer builds over `run`.
 */
export type OpenedProject =
  | Exclude<Opening, { readonly kind: 'open' }>
  | Withheld
  | {
      readonly kind: 'open'
      readonly root: string
      readonly engine: ResolvedEngine
      readonly capabilities: CapabilityReport
      readonly governed: Readonly<Record<string, string>>
      /**
       * What the project says about itself (RG198), read once where it was opened.
       *
       * `logo` is blank here whatever the file declares: it is a path into a repository on
       * the machine, and the renderer gets the picture as `mark` or gets nothing (RG204).
       */
      readonly declares: Declared
      /**
       * The declared logo as a data URL, or empty for every way of not having one.
       *
       * Resolved, refused and read by the side that has the disk. A `file://` URL into an
       * Electron renderer would widen what the window can read to whatever a path can
       * reach — and that path was written by a repository rather than by this app.
       */
      readonly mark: string
      /** Why its engine could not be held, as of the opening, or null. */
      readonly unheld: string | null
    }

/**
 * The IPC channel behind each method. Named here rather than in the preload so that the
 * two ends cannot drift: main handles what this says, the preload invokes what this says.
 */
export const BRIDGE_CHANNELS = {
  identify: 'roadkeep:identify',
  settings: 'roadkeep:settings',
  savePreference: 'roadkeep:save-preference',
  projects: 'roadkeep:projects',
  open: 'roadkeep:open',
  run: 'roadkeep:run',
  subscribe: 'roadkeep:subscribe',
  roots: 'roadkeep:roots',
  chooseRoot: 'roadkeep:choose-root',
  saveRoots: 'roadkeep:save-roots',
  handOver: 'roadkeep:hand-over',
  handOverDoor: 'roadkeep:hand-over-door',
  replySession: 'roadkeep:reply-session',
  answerSession: 'roadkeep:answer-session',
  governedAt: 'roadkeep:governed-at',
  editedAt: 'roadkeep:edited-at',
  fileText: 'roadkeep:file-text',
  gates: 'roadkeep:gates',
  readings: 'roadkeep:readings',
  check: 'roadkeep:check',
  sessions: 'roadkeep:sessions',
  stopSession: 'roadkeep:stop-session',
  gloss: 'roadkeep:gloss',
  cancelGloss: 'roadkeep:cancel-gloss',
  door: 'roadkeep:door',
} as const satisfies Record<keyof RendererBridge, string>
