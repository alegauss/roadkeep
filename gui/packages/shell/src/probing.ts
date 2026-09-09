import { createLimiter, SCAN_WIDTH, type Limiter } from '@rk/core'

/**
 * One bound over every filesystem probe this process makes (RG102).
 *
 * RG71 made the walk asynchronous and left what surrounds it synchronous: whether each root
 * a person declared is there, which git directory each project found shares, and when each
 * project's governed files last moved. Seventeen projects is around ninety stats, and every
 * one of them ran in the process the window's IPC goes through — so a sleeping external
 * drive still froze the app, with the walk simply no longer being where it happened.
 *
 * **One limiter and not three.** The design's own question, answered: these are ninety
 * reads of one disk, and three widths would be three answers to a question that has one.
 * The scan's own is the same bound for the same reason, so this is `SCAN_WIDTH` rather than
 * a second number — a machine whose disk wants a different figure wants it once.
 *
 * What this does not do is make anything faster. A bound is what keeps a burst from
 * becoming a queue nothing can interrupt; the speed came from the reads no longer blocking.
 */

/** How many probes are in flight at once. The scan's number, for the scan's reason. */
export const PROBE_WIDTH = SCAN_WIDTH

const probes: Limiter = createLimiter(PROBE_WIDTH)

/** Run one filesystem probe under the shared bound. */
export function probing<T>(read: () => Promise<T>): Promise<T> {
  return probes.hold(read)
}
