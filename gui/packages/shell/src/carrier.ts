import {
  bridgedRun,
  EMPTY_CATALOGUE,
  openedFrom,
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
} from '@rk/core'

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
}

export interface Carrier {
  projects(): Promise<ProjectCatalogue>
  open(root: string): Promise<OpenedProject>
  run(root: string, request: BridgedRequest): Promise<BridgedResult>
  /** Give back every engine held, awaited to the last exit. What quitting waits on. */
  close(): Promise<void>
}

/** Two spellings of one folder, compared the way the catalogue compares them. */
const sameRoot: SamePart = (left, right) => rootKey(left) === rootKey(right)

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

  let catalogue: ProjectCatalogue | null = null
  let scanning: Promise<ProjectCatalogue> | null = null
  const held = new Map<string, Promise<Opening>>()

  // One walk at a time: two folded against the same record at once would each fold the
  // other's result away, so a second caller waits on the walk already under way.
  const projects = (): Promise<ProjectCatalogue> => {
    scanning ??= (async () => {
      const looking = options.looking()
      const folded = await fold(catalogue ?? EMPTY_CATALOGUE, looking.roots, now(), looking.skip)
      catalogue = folded.catalogue
      return folded.catalogue
    })().finally(() => {
      scanning = null
    })
    return scanning
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
        return await bridgedRun(() => answer.project.transport.run(full))
      } catch (cause) {
        return bridgedRun(() => Promise.reject(cause))
      }
    },

    async close() {
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
