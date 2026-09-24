import {
  DEFAULT_POLICY,
  groupProjects,
  reconcile,
  rowsFrom,
  type ProjectCatalogue,
  type Reconciled,
  type ScanRoot,
} from '@rk/core'

import { gitSite } from './git-worktree'
import { rootKey } from './root-paths'
import { scanRoots } from './scan-fs'

/**
 * Walk the roots, group what was found into families, and fold that into the record.
 *
 * Block B end to end, and the one place it is composed: the catalogue test and the carrier
 * the renderer asks (RG143) run this, where the test used to spell the same four steps
 * itself and nothing a window ran spelled them at all.
 *
 * @param skip directory names the person said a scan never enters.
 * @param now an ISO timestamp, passed in so a test can say when.
 */
export async function rescan(
  previous: ProjectCatalogue,
  roots: readonly ScanRoot[],
  now: string,
  skip: readonly string[] = DEFAULT_POLICY.ignore,
): Promise<Reconciled> {
  const scanned = await scanRoots(roots, { policy: { ...DEFAULT_POLICY, ignore: skip } })
  const families = groupProjects(
    await Promise.all(
      scanned.found.map(async (entry) => ({ path: entry.path, ...(await gitSite(entry.path)) })),
    ),
    rootKey,
  )
  const rootOf = (candidate: string): string =>
    scanned.found.find((entry) => rootKey(entry.path) === rootKey(candidate))?.root ?? ''

  return reconcile(previous, roots, rowsFrom(families, rootOf, now), rootKey, now)
}
