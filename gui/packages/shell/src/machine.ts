import { availableParallelism } from 'node:os'

import { withLimits } from '@rk/core'

/**
 * How many engine calls this machine should run at once.
 *
 * `core` cannot ask — it has no Node in scope, which is what keeps it the half a web
 * service keeps — so the number is worked out here and handed in as a setting like any
 * other. It is a default and not a rule: a person who raises it is raising a setting, and
 * the clamp in `withLimits` is what stops that becoming a hundred processes.
 *
 * Cores, less one, so the machine still has something to draw the window with. A four-core
 * laptop gets three, which is three interpreter starts of the twenty a portfolio wants and
 * still leaves the renderer responsive.
 */
export function machineWidth(): number {
  return withLimits({ width: Math.max(1, availableParallelism() - 1) }).width
}
