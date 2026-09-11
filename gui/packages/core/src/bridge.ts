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
import type { BuildIdentity } from './build'
import type { CapabilityReport } from './capabilities'
import type { ProjectCatalogue } from './catalogue'
import type { ResolvedEngine } from './engine-resolution'
import type { Opening } from './opening'
import type { BriefPayload, HeldClaim } from './payloads'
import type { KnownRoot, ScanRoot } from './roots'
import type { SessionOutcome } from './session'
import type { SettingsRead, Theme } from './settings'
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
   * Keep the ground somebody just chose, which is what makes the file the source of it.
   *
   * The switch persists to browser storage on its own, and that copy is a cache: it is read
   * before React runs so the first frame is not the wrong colour. A cache nothing refreshes
   * is a second answer, so the choice comes back through here and the file wins at the next
   * launch.
   *
   * **One field and not a settings patch.** A method that took `Partial<Settings>` would
   * hand the renderer the roots and the ignore list as well, and the screen that needs those
   * does not exist yet — widening this is a decision that belongs to whoever builds it.
   */
  saveTheme(theme: Theme): Promise<void>
  /**
   * Keep the language somebody just chose (RG116).
   *
   * The second of these and not a settings patch, which is the decision `saveTheme` left to
   * whoever needed the second write. A patch would hand the renderer the roots and the
   * ignore list as well, and the screen that needs those still does not exist — so the
   * surface grows by one method that names what it writes. A third would be the moment to
   * ask again; two is a pair, not a list.
   *
   * A tag this build does not ship is refused rather than stored: `Settings.locale` is read
   * back through `localeFor`, so a value nobody can draw would silently become English at
   * the next launch and look like the setting had not been saved.
   */
  saveLocale(locale: string): Promise<void>
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
   * The project's governed files, each with when the disk last changed it (RG153).
   *
   * Beside the landing rather than in it: what moved in a line is the engine's answer, and
   * which file changed when is the filesystem's — a question only the side with the disk can
   * ask, which over HTTP is the side that has the checkout.
   */
  governedAt(root: string): Promise<readonly GovernedFile[]>
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

/**
 * One session, as the process holding it knows it (RG153). Plain data, so it crosses as it is.
 */
export interface SessionRecord {
  /** This process's name for it, which is what its events are keyed on. */
  readonly key: string
  readonly root: string
  /** The line it was handed. */
  readonly id: string
  /** The brief it was started from, as the claiming read answered it: what it was told. */
  readonly handed: BriefPayload
  /** Which Claude Code runs it, as resolution found it. */
  readonly agent: Agent
  /** Every line of its stream so far, raw and in order. */
  readonly lines: readonly string[]
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
}

export type Topic = keyof TopicEvents

/** The channel each topic's events arrive on, main to renderer. */
export const BRIDGE_TOPICS = {
  governed: 'roadkeep:on-governed',
  session: 'roadkeep:on-session',
} as const satisfies Record<Topic, string>

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
      readonly message: string
      readonly durationMs: number
    }

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
  saveTheme: 'roadkeep:save-theme',
  saveLocale: 'roadkeep:save-locale',
  projects: 'roadkeep:projects',
  open: 'roadkeep:open',
  run: 'roadkeep:run',
  subscribe: 'roadkeep:subscribe',
  roots: 'roadkeep:roots',
  chooseRoot: 'roadkeep:choose-root',
  saveRoots: 'roadkeep:save-roots',
  handOver: 'roadkeep:hand-over',
  governedAt: 'roadkeep:governed-at',
  sessions: 'roadkeep:sessions',
  stopSession: 'roadkeep:stop-session',
  door: 'roadkeep:door',
} as const satisfies Record<keyof RendererBridge, string>
