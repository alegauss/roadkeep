import {
  bridgedRun,
  createGateLedger,
  createLimiter,
  createWatching,
  EMPTY_CATALOGUE,
  buildArgv,
  openedFrom,
  readLintPayload,
  recordGate,
  watchedFiles,
  composeDoor,
  filledArgv,
  withheldBecause,
  withheldResult,
  type BridgedRequest,
  type BridgedResult,
  type GateLedger,
  type OpenProject,
  type Opening,
  type OpenedProject,
  type ProjectCatalogue,
  type ProjectGate,
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
  /** Where gate verdicts are kept (RG152). Its own unless a test says otherwise. */
  readonly gate?: GateLedger
  /**
   * Told when a gate this carrier ran left a verdict (RG166), so a window hears it without
   * asking. Absent — a test, or a carrier nobody is watching — the verdict is still on record
   * and `gates` answers it.
   */
  readonly onGate?: (gate: ProjectGate) => void
  /**
   * How many projects may be gated at once (RG187). One by default: a cold start opens every
   * project the walk found, and the gate is the most expensive read there is, so a launch
   * spends one engine on verdicts and the rest on what the reader is looking at.
   */
  readonly gatesAtOnce?: number
  /**
   * Told when a walk behind the record changed something (RG180) — never when it found
   * exactly what the record held, since a window that redrew on every walk would redraw on
   * a timer nobody set.
   */
  readonly onCatalogue?: (changed: number) => void
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
  /**
   * What the gate last said about each project it has run for (RG152).
   *
   * Read off the ledger and dated against the files as they are now, so a verdict taken
   * before a write says it is stale rather than being thrown away. A project nothing has
   * gated is absent from the answer: `unknown` is the caller's word for that, and this side
   * inventing a clean row is the one thing `gate.ts` refuses to do.
   */
  gates(): Promise<readonly ProjectGate[]>
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

  /**
   * What this project's governed files look like now, as one string.
   *
   * The one place either ledger dates anything from: a door offered against a state that has
   * gone and a verdict taken before a write are the same question asked twice, so they are
   * asked of the same answer.
   */
  const stampOf = async (root: string): Promise<string> => {
    const answer = await opening(root).catch(() => null)
    return answer?.kind === 'open'
      ? stampGoverned(root, Object.values(answer.project.governed))
      : ''
  }

  // What the engine offered, kept here rather than crossing (RG165).
  const doors = options.doors ?? createDoorKeep({ stampOf })

  // What the gate last said, per project (RG152). In memory, because a verdict is about a
  // working tree at a moment and the tree can change while this app is not running.
  const gate: GateLedger = options.gate ?? createGateLedger(rootKey)
  // Which roots it holds one for: the ledger answers about a root it is asked about, and
  // `gates` has to know which to ask about without walking every project on the machine.
  const gated = new Map<string, string>()

  /**
   * Note what the gate said, when a gate is what ran (RG152).
   *
   * The verdict is taken off the answer a screen asked for rather than from a run of this
   * side's own: `lint` is the most expensive read there is, and running a second one to
   * date a row would double the cost of the only read that answers the question. So every
   * `lint` through this bridge dates the ledger, whoever asked for it and whatever screen
   * they were on.
   *
   * The stamp is read after the answer, which is the honest order: a file written while the
   * gate was running makes the verdict stale immediately, and the row says so.
   */
  const noting = async (root: string, argv: readonly string[], parsed: unknown): Promise<void> => {
    if (!argv.includes('lint')) return
    const read = readLintPayload(parsed, '')
    if (!read.ok) return
    const stamp = await stampOf(root)
    gate.note(root, recordGate(read.value, stamp, now()))
    gated.set(rootKey(root), root)
  }

  /**
   * Keep whatever doors an answer carried, and name them on the way back (RG165).
   *
   * Every read goes through here, because a door arrives on a refusal as readily as on a
   * gate finding — and an answer that carries none is the ordinary case and costs a walk of
   * the document it already parsed.
   */
  const keeping = async (
    root: string,
    argv: readonly string[],
    answered: BridgedResult,
  ): Promise<BridgedResult> => {
    if (answered.kind !== 'ran') return answered
    let parsed: unknown
    try {
      parsed = JSON.parse(answered.result.stdout)
    } catch {
      // Not JSON at all, which is an answer this side does not read for anything else either.
      return answered
    }
    await noting(root, argv, parsed)
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
      // And said, where the fold moved something: `reconcile` already answers what changed,
      // so a walk that found what the record held is one nobody needs to hear about (RG180).
      if (folded.changes.length > 0) options.onCatalogue?.(folded.changes.length)
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

  /**
   * Run the gate for one project, where running it would say anything new (RG166).
   *
   * **Driven by the files, never by a draw.** `needsGate` compares what is on record against
   * the stamp the governed files have now, so this is at most one `lint` per project per
   * change — a window redrawing its list seventeen times runs none. It goes through the
   * project's own pooled transport, so it queues behind whatever that project is doing rather
   * than competing with it.
   *
   * Nothing awaits it: a verdict arrives on the `gate` topic when it arrives, and an opening
   * that waited for one would make every project's first draw cost the most expensive read
   * there is. A gate that will not run is a project that stays `unknown`, which is a state a
   * row draws.
   */
  const gating = new Set<string>()
  // Across projects, not within one: each project's own pool bounds what it runs at once,
  // and what was unbounded is how many projects run a gate together (RG187).
  const gateLimit = createLimiter(options.gatesAtOnce ?? 1)
  const gateIfStale = async (root: string, project: OpenProject): Promise<void> => {
    const key = rootKey(root)
    // One at a time per project: two runs against one tree answer the same thing twice.
    if (gating.has(key)) return
    if (!gate.stale(root, await stampOf(root))) return

    gating.add(key)
    try {
      const ran = await gateLimit.hold(() =>
        project.transport.run({ root, argv: buildArgv(root, 'lint', {}) }),
      )
      const read = readLintPayload(JSON.parse(ran.stdout), '')
      if (!read.ok) return
      // Stamped after the run, like every other verdict: a file written while the gate ran
      // makes it stale at once, and the row says so rather than claiming the tree is clean.
      const stamp = await stampOf(root)
      gate.note(root, recordGate(read.value, stamp, now()))
      gated.set(key, root)
      options.onGate?.({ root, health: gate.healthOf(root, stamp) })
    } catch {
      // A gate that would not run says nothing. The project keeps whatever it had, which
      // where nothing has run is `unknown` — never a verdict this side made up.
    } finally {
      gating.delete(key)
    }
  }

  return {
    projects,

    async open(root) {
      try {
        if (!(await catalogued(root))) {
          return { kind: 'withheld', root, reason: notCatalogued(root) }
        }
        const reached = await opening(root)
        // A project that just opened is one whose verdict may be older than its files, and
        // this is the moment the engine to ask with exists. Never awaited: the opening is
        // what a screen is waiting for, and it is handed the project this call already has
        // rather than opening one of its own (RG166).
        if (reached.kind === 'open') void gateIfStale(root, reached.project).catch(() => undefined)
        return openedFrom(reached)
      } catch (cause) {
        // `openProject` answers its failures as states, so reaching here is the scan or the
        // candidates throwing — still an answer a screen draws, and never a rejected call.
        return {
          kind: 'unresolved',
          root,
          reason: cause instanceof Error ? cause.message : String(cause),
          // Nothing was tried, because the throw came from the scan or the candidates
          // before any command line was asked (RG168).
          code: 'nothing-offered',
          tried: [],
        }
      }
    },

    async run(root, request) {
      try {
        if (!(await catalogued(root))) {
          return withheldResult(notCatalogued(root), 'not-catalogued', { root })
        }

        const full = { ...request, root }
        const why = withheldBecause(full, sameRoot)
        // No code, so the sentence is drawn as it was written (RG192). This one names a verb
        // and a flag in an argv *this app* composed, which makes it a defect report rather
        // than a state a person can act on — and a translation of it would say the same
        // English identifiers inside a Portuguese sentence, costing the reader the only part
        // that says which call was wrong.
        if (why !== null) return withheldResult(why)

        const answer = await opening(root)
        if (answer.kind !== 'open') {
          const whyNot = whyNotOpen(answer)
          return withheldResult(`${root} did not open: ${whyNot}`, 'not-open', {
            root,
            why: whyNot,
          })
        }
        return keeping(root, full.argv, await bridgedRun(() => answer.project.transport.run(full)))
      } catch (cause) {
        return bridgedRun(() => Promise.reject(cause))
      }
    },

    async door(root, offered, which, words) {
      try {
        if (!(await catalogued(root))) {
          return withheldResult(notCatalogued(root), 'not-catalogued', { root })
        }

        const kept = await doors.taken(root, offered, which)
        if (kept === null) return withheldResult(NO_SUCH_DOOR, 'no-such-door')

        // The engine's own argv, with the person's prose where the engine left a blank and
        // nowhere else. A caller who sent more words than the door has blanks, or fewer, is
        // refused rather than helped: what runs is what came back.
        const argv = filledArgv(kept.argv, words)
        if (argv === null) return withheldResult(NOT_THE_WORDS, 'not-the-words')

        const answer = await opening(root)
        if (answer.kind !== 'open') {
          const whyNot = whyNotOpen(answer)
          return withheldResult(`${root} did not open: ${whyNot}`, 'not-open', {
            root,
            why: whyNot,
          })
        }
        // Wrapped by `composeDoor`, which adds where to run it and the request for a
        // machine-readable answer and nothing else — and with no tool call beside it, since
        // the held surface answers only the tools its own schema publishes.
        const composed = composeDoor(root, { argv })
        return keeping(
          root,
          composed.argv,
          await bridgedRun(() => answer.project.transport.run({ root, argv: composed.argv })),
        )
      } catch (cause) {
        return bridgedRun(() => Promise.reject(cause))
      }
    },

    async gates() {
      // The catalogue's spelling of each root, so a caller matches these against its own
      // list by the path it was given rather than by guessing this platform's path rules.
      const known = catalogue ?? (await projects())
      const spelled = new Map(
        known.projects.map((project) => [rootKey(project.path), project.path]),
      )
      // One stamp read per project on record, and none for the rest: a machine with
      // seventeen projects and one gated answers with one file read, not seventeen.
      return Promise.all(
        [...gated].map(async ([key, root]) => ({
          root: spelled.get(key) ?? root,
          health: gate.healthOf(root, await stampOf(root)),
        })),
      )
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
        // The files moved, so the verdict on record is about a tree that has gone (RG166).
        void gateIfStale(root, project).catch(() => undefined)
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
