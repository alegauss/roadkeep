import { readdirSync } from 'node:fs'
import path from 'node:path'

import {
  DEFAULT_POLICY,
  scan,
  type Listing,
  type Look,
  type ScanPolicy,
  type ScanResult,
  type ScanRoot,
} from '@rk/core'

import { rootKey } from './root-paths'

/**
 * Looking at one directory, which is the only part of a scan that touches a disk.
 *
 * One `readdir` per directory and nothing else. The marker is found in the entries that
 * call already returned rather than by a second `stat`, which halves the syscalls on the
 * one operation this whole block is trying to make cheap.
 */
export function lookWith(policy: ScanPolicy = DEFAULT_POLICY): Look {
  return (directory: string): Listing | null => {
    let entries
    try {
      entries = readdirSync(directory, { withFileTypes: true })
    } catch {
      // Permission denied, a path that went away mid-walk, a disconnected share. All of
      // them are facts about a directory rather than reasons to abandon the scan.
      return null
    }

    let isProject = false
    const children: { name: string; path: string }[] = []

    for (const entry of entries) {
      if (entry.isDirectory()) {
        children.push({ name: entry.name, path: path.join(directory, entry.name) })
      } else if (!isProject && entry.name === policy.marker && entry.isFile()) {
        isProject = true
      }
    }

    return { isProject, children }
  }
}

/** Walk the roots on this machine. */
export function scanRoots(
  roots: readonly ScanRoot[],
  policy: ScanPolicy = DEFAULT_POLICY,
): ScanResult {
  return scan(roots, lookWith(policy), rootKey, policy)
}
