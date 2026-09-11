import {
  bridgedRun,
  createWatching,
  EMPTY_CATALOGUE,
  openedFrom,
  watchedFiles,
  composeDoor,
  filledArgv,
  withheldBecause,
  withheldResult,
  type BridgedRequest,
  type BridgedResult,
  type Opening,
  type OpenedProject,
  type ProjectCatalogue,
  type Reconciled,
  type SamePart,
  type ScanRoot,
  type Watching,
} from '@rk/core'

import { createDoorKeep, type DoorKeep } from './door-keep'
import { createGovernedWatcher, REAL_CLOCK } from './governed-watch'
import { stampGoverned } from './governed-stamp'
import { openHere } from './open-here'
import { rescan } from './rescan'
import { rootKey } from './root-paths'

/**
 * The main-process end of every read a window makes (RG143).
 *
 * The renderer has no process, so this is where its projects are found, opened and kept.
 * Three questions, and each is one method of the bridge: which projects are there, open one,
 * run one request against it. Nothing here names Electron, so a test drives it with a fake
 * opening and nothing spawns.
 *
 * **It keeps the catalogue, because the catalogue is the refusal.** A root the last scan did
 * not find present is not opened and not run against, and nothing looks at what the path
 * says — §RG85's first refusal, which rejected validating a path as a rule somebody spells
 * around. The scan is folded into the one before it, so a project that went away is marked
 * missing rather than forgotten, for as long as this process runs.
 *
 * **It keeps the engines, because it is the process that can close them.** One open project
 * per root, held from the first `open` or `run` until `close`. A way of not opening is not
 * kept: it has already given back what it started, and remembering it would answer a
 * problem somebody has since fixed with the reason it had before.
 */

/** Where to look and how widely to read, as the person's settings say today. */
export interface Looking {
  readonly roots: readonly ScanRoot[]
  readonly skip: readonly string[]
  /** How many engine calls one project may have in flight. */
  readonly width: number
}

export interface CarrierOptions {
  /** Read per call: the settings file is the person's to edit while the app runs. */
  readonly looking: () => Looking
  /** Open one project. `openHere` unless a test says otherwise. */
  readonly open?: (root: string, width: number) => Promise<Opening>
  /** Walk and fold. `rescan` unless a test says otherwise. */
  readonly rescan?: (
    previous: ProjectCatalogue,
    roots: readonly ScanRoot[],
    now: string,
    skip: readonly string[],
  ) => Promise<Reconciled>
  readonly now?: () => string
  /** Watch governed files. Real handles and a real clock unless a test says otherwise. */
  readonly watching?: Watching
  /**
   * The record this machine last wrote, read once as this carrier is made (RG164). Absent,
   * the carrier starts from nothing and the first walk is what a screen waits on.
   */
  readonly remembered?: () => ProjectCatalogue
  /** Keep the folded record. Called after every walk; a write that fails costs the next one. */
  readonly remember?: (catalogue: ProjectCatalogue) => void
  /** Where the doors an answer carried are kept (RG165). Its own unless a test says otherwise. */
  readonly doors?: DoorKeep
}

export interface Carrier {
  projects(): Promise<ProjectCatalogue>
  open(root: string): Promise<OpenedProject>
  run(root: string, request: BridgedRequest): Promise<BridgedResult>
  /**
   * Be told when a project's governed files move, for as long as the answer is not called
   * (RG144) — or null where the root is not one this carrier would open.
   *
   * The files are the ones the project's own `config` declared, read off the opening, so
   * watching one opens it. Each move also drops what the cache held for it: an answer keyed
   * on a stamp is never stale, and one nobody will ask for again is only memory.
   */
  follow(root: string, moved: () => void): Promise<(() => void) | null>
  /**
   * Take one door an answer carried (RG165), by the name `run` gave that answer.
   *
   * The argv is the engine's and is never sent: what a caller names is which answer, which
   * door in it, and the prose for the blanks the engine left.
   */
  door(
    root: string,
    offered: string,
    which: number,
    words: readonly string[],
  ): Promise<BridgedResult>
  /** Give back every engine held, awaited to the last exit. What quitting waits on. */
  close(): Promise<void>
}

/** Two spellings of one folder, compared the way the catalogue compares them. */
const sameRoot: SamePart = (left, right) => rootKey(left) === rootKey(right)

/**
 * Why a door did not run (RG165). Neither says which door or what was sent: a name that
 * names nothing and a name whose batch has been dropped are one answer to a caller, and the
 * only thing to do about either is to read again and take the door that answer offers.
 */
const NO_SUCH_DOOR =
  'no door by that name is on offer for this project: read again and take one the answer carries'
const NOT_THE_WORDS = 'that is not one word for each blank the door has'

function notCatalogued(root: string): string {
  return `${root} is not a project the scan of the person's roots found`
}

/** The sentence a way of not opening carries, for a request that needed it open. */
function whyNotOpen(opening: Exclude<Opening, { readonly kind: 'open' }>): string {
  if (opening.kind === 'unresolved') return opening.reason
  if (opening.kind === 'unreadable') return opening.unreadable.message
  return 'no roadkeep project governs it'
}

export function createCarrier(options: CarrierOptions): Carrier {
  const open = options.open ?? ((root, width) => openHere(root, { width }))
  const fold = options.rescan ?? rescan
  const now = options.now ?? (() => new Date().toISOString())
  const watching = options.watching ?? createWatching(createGovernedWatcher(), REAL_CLOCK)
  const following = new Set<() => void>()
  // What the engine offered, kept here rather than crossing (RG165).
  const doors =
    options.doors ??
    createDoorKeep({
      stampOf: async (root) => {
        const answer = await opening(root).catch(() => null)
        return answer?.kind === 'open'
          ? stampGoverned(root, Object.values(answer.project.governed))
          : ''
      },
    })

  /**
   * Keep whatever doors an answer carried, and name them on the way back (RG165).
   *
   * Every read goes through here, because a door arrives on a refusal as readily as on a
   * gate finding — and an answer that carries none is the ordinary case and costs a walk of
   * the document it already parsed.
   */
  const keeping = async (root: string, answered: BridgedResult): Promise<BridgedResult> => {
    if (answered.kind !== 'ran') return answered
    let parsed: unknown
    try {
      parsed = JSON.parse(answered.result.stdout)
    } catch {
      // Not JSON at all, which is an answer this side does not read for anything else either.
      return answered
    }
    const offered = await doors.keep(root, parsed)
    return offered === null ? answered : { ...answered, offered }
  }

  // What was written last time, if anything (RG164). A record read here is a list every
  // question below can answer from while the walk behind it runs.
  const remembered = options.remembered?.()
  let catalogue: ProjectCatalogue | null =
    remembered === undefined || remembered.projects.length === 0 ? null : remembered
  let scanning: Promise<ProjectCatalogue> | null = null
  const held = new Map<string, Promise<Opening>>()

  // One walk at a time: two folded against the same record at once would each fold the
  // other's result away, so a second caller waits on the walk already under way.
  const walk = (): Promise<ProjectCatalogue> => {
    scanning ??= (async () => {
      const looking = options.looking()
      const folded = await fold(catalogue ?? EMPTY_CATALOGUE, looking.roots, now(), looking.skip)
      catalogue = folded.catalogue
      // Kept as it is folded, so a project that went missing is remembered as missing rather
      // than forgotten at the quit that follows.
      options.remember?.(folded.catalogue)
      return folded.catalogue
    })().finally(() => {
      scanning = null
    })
    return scanning
  }

  /**
   * The record, and a walk (RG164).
   *
   * **The record answers first where there is one**: a launch that remembers eleven projects
   * draws them while the disk is still being read, and the walk it started lands in the next
   * call. With no record this waits, because a list of nothing is not an answer worth having.
   */
  const projects = (): Promise<ProjectCatalogue> => {
    const known = catalogue
    if (known === null) return walk()
    // Nobody is waiting on this one, so a walk that throws must not become an unhandled
    // rejection: the record stands, and the next call starts another walk.
    void walk().catch(() => undefined)
    return Promise.resolve(known)
  }

  // Asked of the record, scanning first where there is none yet: a window can open a project
  // it remembers before it asks for the list, and the answer is the same list either way.
  const catalogued = async (root: string): Promise<boolean> => {
    const known = catalogue ?? (await projects())
    const key = rootKey(root)
    return known.projects.some(
      (project) => project.presence === 'present' && rootKey(project.path) === key,
    )
  }

  const opening = (root: string): Promise<Opening> => {
    const key = rootKey(root)
    const kept = held.get(key)
    if (kept !== undefined) return kept

    const started = open(root, options.looking().width).then(
      (answer) => {
        if (answer.kind !== 'open') held.delete(key)
        return answer
      },
      (cause: unknown) => {
        held.delete(key)
        throw cause
      },
    )
    held.set(key, started)
    return started
  }

  return {
    projects,

    async open(root) {
      try {
        if (!(await catalogued(root))) {
          return { kind: 'withheld', root, reason: notCatalogued(root) }
        }
        return openedFrom(await opening(root))
      } catch (cause) {
        // `openProject` answers its failures as states, so reaching here is the scan or the
        // candidates throwing — still an answer a screen draws, and never a rejected call.
        return {
          kind: 'unresolved',
          root,
          reason: cause instanceof Error ? cause.message : String(cause),
          tried: [],
        }
      }
    },

    async run(root, request) {
      try {
        if (!(await catalogued(root))) return withheldResult(notCatalogued(root))

        const full = { ...request, root }
        const why = withheldBecause(full, sameRoot)
        if (why !== null) return withheldResult(why)

        const answer = await opening(root)
        if (answer.kind !== 'open') {
          return withheldResult(`${root} did not open: ${whyNotOpen(answer)}`)
        }
        return keeping(root, await bridgedRun(() => answer.project.transport.run(full)))
      } catch (cause) {
        return bridgedRun(() => Promise.reject(cause))
      }
    },

    async door(root, offered, which, words) {
      try {
        if (!(await catalogued(root))) return withheldResult(notCatalogued(root))

        const kept = await doors.taken(root, offered, which)
        if (kept === null) return withheldResult(NO_SUCH_DOOR)

        // The engine's own argv, with the person's prose where the engine left a blank and
        // nowhere else. A caller who sent more words than the door has blanks, or fewer, is
        // refused rather than helped: what runs is what came back.
        const argv = filledArgv(kept.argv, words)
        if (argv === null) return withheldResult(NOT_THE_WORDS)

        const answer = await opening(root)
        if (answer.kind !== 'open') {
          return withheldResult(`${root} did not open: ${whyNotOpen(answer)}`)
        }
        // Wrapped by `composeDoor`, which adds where to run it and the request for a
        // machine-readable answer and nothing else — and with no tool call beside it, since
        // the held surface answers only the tools its own schema publishes.
        const composed = composeDoor(root, { argv })
        return keeping(
          root,
          await bridgedRun(() => answer.project.transport.run({ root, argv: composed.argv })),
        )
      } catch (cause) {
        return bridgedRun(() => Promise.reject(cause))
      }
    },

    async follow(root, moved) {
      if (!(await catalogued(root))) return null
      const answer = await opening(root).catch(() => null)
      if (answer?.kind !== 'open') return null

      const { project } = answer
      const interest = watching.hold(root, watchedFiles(Object.values(project.governed)))
      const key = rootKey(root)
      const stopHearing = watching.onChanged((changed) => {
        if (rootKey(changed) !== key) return
        project.invalidate()
        moved()
      })

      let stopped = false
      const stop = (): void => {
        if (stopped) return
        stopped = true
        following.delete(stop)
        stopHearing()
        interest.release()
      }
      following.add(stop)
      return stop
    },

    async close() {
      // The watches first: a handle held on a folder is the same trouble on Windows as an
      // engine standing in it.
      for (const stop of [...following]) stop()
      const openings = [...held.values()]
      held.clear()
      await Promise.all(
        openings.map(async (pending) => {
          const answer = await pending.catch(() => null)
          if (answer?.kind === 'open') await answer.project.close()
        }),
      )
    },
  }
}
