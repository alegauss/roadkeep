import { listedTasks, sawEverything, type ListPayload, type TaskLine } from './payloads'
import type { Refusal } from './refusals'
import { composeWrite, type Composed } from './writing'

/**
 * The deferred store, and telling a paused line from one nothing ever filed.
 *
 * A deferred line kept its id, its deps, its symptom and its section, and only left the
 * block. So the store is a listing like any other — `--stale` names the deferred role
 * without a `--role` — and the lines come back with the pause marker and the sentence the
 * store spells.
 *
 * **The sentence is shown as the store spells it.** `defer` writes the pause's reason
 * wrapped around the design's own why, and splitting the wrapper back out here would be a
 * rule about a format that is roadkeep's. `No store of its own` and `No account, no auth
 * and no remote store in the desktop build` both bound this without forbidding it: the
 * deferred store is one of the roles the config declares, and this app reads it exactly as
 * it reads the roadmap.
 *
 * **The age is not in the payload.** `--stale` orders the store by how long each pause has
 * stood — in commits over the governed files — and prints that for a terminal, on stderr
 * and never in the listing, so a `--json` caller gets the store and no ordering. Nothing
 * here invents one: the lines are in the order the file has them.
 */

export interface Pause {
  readonly id: string
  readonly block: string
  /** The pause marker the project declares, carried rather than compared to a literal. */
  readonly marker: string
  readonly symptom: string
  /** The store's own sentence: the reason `defer` wrote, around the design's why. */
  readonly why: string
  readonly ref: string | null
  readonly line: number
}

export interface Store {
  readonly file: string
  readonly total: number
  /** In the order the file has them, which is by block. Never by age: none is carried. */
  readonly pauses: readonly Pause[]
  /** False when a marker-bearing line in the store was refused, as anywhere else. */
  readonly complete: boolean
}

export function storeFrom(payload: ListPayload): Store {
  return {
    file: payload.file,
    total: payload.total,
    pauses: listedTasks(payload).map(pauseOfLine),
    // A store past `[reads] list` carries its counts and not its lines, and a screen
    // drawing zero pauses over a total of forty is the silence this flag exists to break.
    complete: sawEverything(payload),
  }
}

function pauseOfLine(task: TaskLine): Pause {
  return {
    id: task.id,
    block: task.block,
    marker: task.status,
    symptom: task.symptom,
    why: task.why,
    ref: task.ref,
    line: task.line,
  }
}

/** One paused line by id, or null. The lookup a task screen makes before it despairs. */
export function pauseOf(store: Store, id: string): Pause | null {
  return store.pauses.find((pause) => pause.id === id) ?? null
}

/**
 * Where the backlog has an id.
 *
 * `unfiled` is the answer that used to be given for a paused line too, which is the whole
 * symptom: until the store is read, set aside and never written look identical.
 *
 * **`unknown` is the fifth and it is about the read rather than the id** (RG100). Finding
 * an id in none of three listings only means it is nowhere if all three saw their whole
 * files, and two things stop that being true: a project declaring `[reads] list` answers a
 * listing past the bound with counts and no lines, and a line the grammar could not accept
 * is in `uncounted` rather than in `tasks`. Either way there is nothing to look through,
 * and reporting *nothing in this project carries that id* about a line somebody paused is
 * the failure this state exists to refuse.
 */
export type Filing = 'open' | 'shipped' | 'paused' | 'unfiled' | 'unknown'

/** The three listings an id could be in, each as the engine answered it. */
export interface Filings {
  readonly roadmap?: ListPayload
  readonly ledger?: ListPayload
  readonly store?: ListPayload
}

/**
 * Which file holds an id.
 *
 * A fact each listing states, not a rule worked out here — the question asked of every
 * answer is only whether the id is in it. The order is the order a person means: an id in
 * the roadmap is open whatever else also mentions it, since an id can be cited by a
 * ledger entry that shipped part of it while the line stays open.
 *
 * **Being found is one question and not being found is another.** A listing holding the id
 * settles it whatever the other two did; an id in none of them is `unfiled` only where all
 * three were read and each saw its whole file, and `unknown` otherwise.
 */
export function filingOf(id: string, filings: Filings): Filing {
  if (holds(filings.roadmap, id)) return 'open'
  if (holds(filings.ledger, id)) return 'shipped'
  if (holds(filings.store, id)) return 'paused'
  return looked(filings) ? 'unfiled' : 'unknown'
}

function holds(payload: ListPayload | undefined, id: string): boolean {
  return payload !== undefined && listedTasks(payload).some((task) => task.id === id)
}

/**
 * Whether an absence is evidence.
 *
 * All three listings, each whole. A listing nobody read is the same silence as one whose
 * lines the bound withdrew — in both cases there was nothing to find the id in.
 */
function looked(filings: Filings): boolean {
  return [filings.roadmap, filings.ledger, filings.store].every(
    (payload) => payload !== undefined && sawEverything(payload),
  )
}

/**
 * What a refused task read turns out to have been about.
 *
 * `brief FX1` and `show FX1` on a set-aside line both refuse with `refused`, `beside` and
 * `about` all empty and the whole answer in `said` — a sentence that names the store, the
 * line, the listing that prints the reason and the verb that brings it back, and gives a
 * screen nothing typed to draw. Reading `is paused in` back out of that sentence is the
 * prose-scraping this client refuses everywhere else, so this asks instead.
 *
 * **It goes behind the refusal and never in front of it.** `filingOf` wants three listings
 * where opening a task made one call, so the ordinary open task pays nothing: only a read
 * that already failed goes looking for why.
 *
 * `said` is carried whole and unparsed, because a filing this could not settle — three
 * listings none of which was read — leaves the engine's own sentence as the best thing on
 * the screen.
 */
export interface Whereabouts {
  readonly id: string
  readonly filing: Filing
  /** The store's own entry, where the id is paused and the store was among the listings. */
  readonly pause: Pause | null
  /**
   * The move that brings it back, or null.
   *
   * Composed from this app's own verb table, which is the one kind of command line it is
   * allowed to build: the app chose `resume`, so the app spells it. A door the engine
   * published would arrive on the refusal, and this refusal publishes none.
   */
  readonly back: Composed | null
  /** What to show, in a sentence built from the filing rather than read out of `said`. */
  readonly sentence: string
  /** The engine's whole refusal, kept as it was written. */
  readonly said: string
}

export function whereaboutsOf(
  root: string,
  id: string,
  refusal: Refusal,
  filings: Filings,
): Whereabouts {
  const filing = filingOf(id, filings)
  const store = filings.store === undefined ? null : storeFrom(filings.store)
  const paused = filing === 'paused'

  return {
    id,
    filing,
    // A `paused` verdict came off the store listing itself, so there is an entry behind it
    // — `filingOf` and `storeFrom` read the same lines. The guard is what the types ask
    // for and not a case: no store means no paused verdict to have.
    pause: paused && store !== null ? pauseOf(store, id) : null,
    back: paused ? composeWrite(root, 'resume', { id }) : null,
    sentence: whereFiled(filing, store, id),
    said: refusal.said,
  }
}

/**
 * What to say about an id that is not open, in a sentence rather than a word.
 *
 * `unfiled` gets the shortest answer and the most important one: nothing in this project
 * has ever carried that id, which is different from a line somebody paused — and different
 * again from `unknown`, which is a sentence about the read and says so out loud rather than
 * claiming the id is nowhere (RG100).
 */
export function whereFiled(filing: Filing, store: Store | null = null, id = ''): string {
  switch (filing) {
    case 'open':
      return 'open in the roadmap'
    case 'shipped':
      return 'shipped, and in the ledger'
    case 'paused': {
      const pause = store === null ? null : pauseOf(store, id)
      const where = store?.file ?? 'the deferred store'
      return pause === null ? `set aside in ${where}` : `set aside in ${where}: ${pause.why}`
    }
    case 'unknown':
      return 'not found, in a read that did not see every line'
    default:
      return 'nothing in this project carries that id'
  }
}
