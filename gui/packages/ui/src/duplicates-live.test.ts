import { execFileSync } from 'node:child_process'
import { mkdtempSync, rmSync, writeFileSync } from 'node:fs'
import { createRequire } from 'node:module'
import { tmpdir } from 'node:os'
import path from 'node:path'

import { afterAll, describe, expect, it } from 'vitest'

/**
 * RG62: the duplicates gate, and the reason it is tested rather than merely run.
 *
 * `viglet-ds-check-duplicates` reads the design system's `exports.json` and fails on any
 * component declared here that the package already exports, naming the import that replaces
 * it. Dumont found nineteen such collisions with nothing failing anywhere.
 *
 * **A gate pointed at the wrong directory reports a clean tree in exactly the same words as
 * a clean tree.** That is what both sibling consoles learned the hard way, and it is why
 * this file plants a duplicate and requires the gate to find it — the roots below are the
 * roots `npm run lint` passes, so what is proven is this project's wiring and not the tool.
 */
const require_ = createRequire(import.meta.url)
const REPO = path.resolve(import.meta.dirname, '..', '..', '..')

/** Where the gate lives, resolved through the package rather than assumed on PATH. */
const GATE = path.join(
  path.dirname(require_.resolve('@viglet/viglet-design-system/styles')),
  '..',
  'scripts',
  'check-duplicates.mjs',
)

/** The roots this project scans. The same list `npm run lint` uses, and that is the point. */
const ROOTS = ['packages/ui/src', 'packages/core/src', 'packages/shell/src']

/** Everything this file put on disk — a planted file, and a directory to point at. */
const planted: string[] = []

afterAll(() => {
  // `recursive` because the list holds both kinds, and a planted duplicate left in the
  // tree is a duplicate the next run of the gate reports.
  //
  // The retries are RG104's, spelled here rather than imported: `shell` owns the helper and
  // the renderer never imports the shell, test or not. Fewer tries than there, because what
  // this removes is a file it wrote a moment ago rather than a directory a process held.
  for (const made of planted) {
    rmSync(made, { force: true, recursive: true, maxRetries: 5, retryDelay: 100 })
  }
})

function runGate(roots: readonly string[]): { code: number; said: string } {
  try {
    const said = execFileSync(process.execPath, [GATE, ...roots], {
      cwd: REPO,
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'pipe'],
    })
    return { code: 0, said }
  } catch (cause) {
    const failed = cause as { status?: number; stdout?: string; stderr?: string }
    return { code: failed.status ?? 1, said: `${failed.stdout ?? ''}${failed.stderr ?? ''}` }
  }
}

describe('RG62: the gate this project answers to', () => {
  it('finds nothing to report, over the roots that hold this app', () => {
    const { code, said } = runGate(ROOTS)

    expect(said, said).toContain('no local copy')
    expect(code).toBe(0)
  })

  it('scanned this app rather than an empty directory', () => {
    // The first half of the wiring: a clean answer over nothing is the failure this file
    // exists for, and the file count is what tells the two apart.
    const scanned = /(\d+) file\(s\) scanned/.exec(runGate(ROOTS).said)?.[1]

    expect(Number(scanned)).toBeGreaterThan(50)
  })

  it('fails on a duplicate planted in a root it scans', () => {
    // The second half, and the one that cannot be inferred. `Badge` is a component the
    // package exports and this app uses; declaring it here is exactly the drift the gate
    // is for.
    const probe = path.join(REPO, 'packages', 'ui', 'src', 'duplicate-probe.tsx')
    planted.push(probe)
    writeFileSync(probe, 'export function Badge() {\n  return null\n}\n', 'utf8')

    const { code, said } = runGate(ROOTS)

    expect(code).toBe(1)
    expect(said).toContain('declares Badge')
    // And it ends in the line the author would have written instead, which is the half
    // that makes a finding actionable rather than merely true.
    expect(said).toContain('import { Badge } from "@viglet/viglet-design-system"')
  })

  it('says nothing about a directory this project does not scan', () => {
    // The control on the control: the same planted file is invisible to a gate pointed
    // somewhere else, which is precisely the mistake a clean report can hide.
    const elsewhere = mkdtempSync(path.join(tmpdir(), 'rk-nothing-'))
    planted.push(elsewhere)

    const { code, said } = runGate([elsewhere])

    expect(code).toBe(0)
    expect(said).toContain('no local copy')
  })
})
