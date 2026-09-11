import { randomUUID } from 'node:crypto'

import { doorsIn, type Door } from '@rk/core'

/**
 * The doors an answer carried, kept by the side that received them (RG165).
 *
 * A door is the engine's own argv — handed back by a refusal, a gate finding or `explain` —
 * and the carrier's guard runs only what this app's verb tables spell. Widening that guard to
 * every verb `commands` publishes would hand the renderer a command line again, which is the
 * shell §RG85 refused. So the argv never crosses: this keeps it, answers a name for it, and
 * runs the one a caller names.
 *
 * **A name is worth nothing on its own.** It is random, it belongs to one root, and it is
 * dropped the moment that project's governed files move — a door offered against files that
 * have since changed may no longer close anything, and running it then is running a fix for a
 * state nobody is in. It lives in this process and dies with it: another launch knows none of
 * them, which is the honest answer to a page that remembered one.
 *
 * **One batch per root** (RG181). A window draws the doors of the answer it is showing, so an
 * answer two reads ago is one no page has a button for — keeping the most recent batch per
 * project and dropping the one it replaces bounds this table at one per open project, without
 * taking away anything a reader could still press. A count would have been the alternative:
 * twenty batches is a number nobody can derive and a rule that drops the batch a slow reader
 * is about to use.
 *
 * Nothing here decides who may run what. It is a table of what was offered, and the rule that
 * what is offered stops being on offer when the files move.
 */

export interface DoorKeepOptions {
  /**
   * A stamp over the project's governed files, taken when doors are kept and again when one
   * is taken. Whatever this answers, two calls that differ mean the files moved.
   */
  readonly stampOf: (root: string) => Promise<string>
  /** Name a batch. A random one unless a test says otherwise. */
  readonly name?: () => string
}

export interface DoorKeep {
  /**
   * Keep whatever doors this answer carried, and answer the name for them — or null where it
   * carried none, which is nearly every answer.
   */
  keep(root: string, answer: unknown): Promise<string | null>
  /** The door a caller named, or null where nothing here holds it any more. */
  taken(root: string, offered: string, which: number): Promise<Door | null>
  /** How many batches are held, which is what a test counts to find one nothing drops. */
  readonly held: number
}

interface Offered {
  readonly root: string
  readonly stamp: string
  readonly doors: readonly Door[]
}

export function createDoorKeep(options: DoorKeepOptions): DoorKeep {
  const named = options.name ?? randomUUID
  const offered = new Map<string, Offered>()
  /** The batch each root has on offer, which is the only one a screen can still reach. */
  const latest = new Map<string, string>()

  return {
    async keep(root, answer) {
      const doors = doorsIn(answer)
      if (doors.length === 0) return null

      const token = named()
      const stamp = await options.stampOf(root)
      // The batch this replaces is one no page has a button for any more (RG181).
      const before = latest.get(root)
      if (before !== undefined) offered.delete(before)
      latest.set(root, token)
      offered.set(token, { root, stamp, doors })
      return token
    },

    async taken(root, token, which) {
      const kept = offered.get(token)
      // The root is part of the name: a token from one project names nothing in another,
      // even for a caller that has both open.
      if (kept === undefined || kept.root !== root) return null

      const now = await options.stampOf(root)
      if (now !== kept.stamp) {
        // The files moved, so what was offered is no longer offered. Dropped rather than
        // refused once, because every door in this batch is about the state that has gone.
        offered.delete(token)
        if (latest.get(root) === token) latest.delete(root)
        return null
      }
      return kept.doors[which] ?? null
    },

    get held() {
      return offered.size
    },
  }
}
