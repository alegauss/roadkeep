import { spawnSync } from 'node:child_process'
import { mkdtempSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import path from 'node:path'

import { afterAll, describe, expect, it } from 'vitest'

import { removeTree } from './scratch'
import { job, stepScript } from './workflow'

/**
 * RG157: the tag-against-manifest check, run rather than read.
 *
 * Finding the step's text proves it is written and nothing about what it does: a condition
 * inverted, or an `exit 1` lost, keeps every string `release.test.ts` looks for and stops
 * refusing anything. So the script is lifted out of the workflow and executed against a
 * manifest written here, with the tag in the variable the runner sets.
 *
 * Live because it starts a shell, which is the line RG64 draws — the design asked for this in
 * the fast suite and the suite's own rule is the one that binds. It costs three shells of a
 * few milliseconds.
 *
 * `bash` is the shell the step declares, so a machine without one cannot run this; on Windows
 * it is the one git installs.
 */

const STEP = 'the tag names the version the manifest carries'
const scratches: string[] = []

/** A directory whose `package.json` carries one version, which is all the step reads. */
function manifest(version: string): string {
  const at = mkdtempSync(path.join(tmpdir(), 'rk-release-'))
  scratches.push(at)
  writeFileSync(path.join(at, 'package.json'), JSON.stringify({ name: 'x', version }), 'utf8')
  return at
}

function ran(tag: string, version: string) {
  const script = stepScript(job('package'), STEP)
  expect(script, `ci.yml has no script under "${STEP}"`).not.toBe('')
  return spawnSync('bash', ['-c', script], {
    cwd: manifest(version),
    env: { ...process.env, GITHUB_REF_NAME: tag },
    encoding: 'utf8',
    shell: false,
    windowsHide: true,
  })
}

afterAll(() => {
  for (const at of scratches) removeTree(at)
})

describe('RG157: the tag check, run rather than read', () => {
  it('lets a tag naming the manifest version through', () => {
    const answer = ran('v1.2.3', '1.2.3')

    expect(answer.error, `bash did not run: ${answer.error?.message ?? ''}`).toBeUndefined()
    expect(answer.status).toBe(0)
  })

  it('refuses a tag naming another version, and says both', () => {
    // The half a text search cannot see: this is the exit that fails the job, and the
    // sentence somebody reads in the log to know which of the two to fix.
    const answer = ran('v9.9.9', '1.2.3')

    expect(answer.status).not.toBe(0)
    expect(answer.stdout).toContain('v9.9.9')
    expect(answer.stdout).toContain('1.2.3')
  })

  it('reads the tag without its leading v, which is how a version is written', () => {
    // `v1.2.3` and `1.2.3` name the same release; a step comparing them whole refuses both.
    expect(ran('1.2.3', '1.2.3').status).toBe(0)
  })
})
