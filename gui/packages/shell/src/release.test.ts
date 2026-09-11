import { readFileSync } from 'node:fs'
import path from 'node:path'

import { describe, expect, it } from 'vitest'

/**
 * RG50: the release a tag leaves behind, held without running a workflow.
 *
 * Two promises live in `ci.yml` and each fails silently. The first is that a release is a
 * decision somebody makes: the job drafts one and a person publishes it, so the day a flag
 * goes missing a tag starts publishing on its own. The second is that the installers say
 * the version the page says: the stamp reads `package.json`, so a tag naming another version
 * would title a release its files disagree with.
 */
const REPO = path.resolve(import.meta.dirname, '..', '..', '..')
const WORKFLOW = readFileSync(path.join(REPO, '.github', 'workflows', 'ci.yml'), 'utf8')

/** One job's block: from its key to the next job's, which is all this needs of YAML. */
function job(name: string): string {
  const start = WORKFLOW.indexOf(`\n  ${name}:\n`)
  expect(start, `ci.yml has no ${name} job`).toBeGreaterThan(-1)
  const rest = WORKFLOW.slice(start + 1)
  const next = rest.slice(1).search(/\n {2}[a-z][\w-]*:\n/)
  return next === -1 ? rest : rest.slice(0, next + 1)
}

describe('RG50: the release a tag drafts', () => {
  it('is a draft, made only on a tag, after both installers exist', () => {
    const release = job('release')

    expect(release).toMatch(/if: startsWith\(github\.ref, 'refs\/tags\/v'\)/)
    expect(release).toMatch(/needs: \[package\]/)
    expect(release).toContain('gh release create')
    expect(release).toContain('--draft')
  })

  it('is the one job that may write to the repository', () => {
    // The workflow reads by default, so a job that forgot to ask could not publish — and one
    // that asked without needing to would be write access sitting beside a test suite.
    expect(WORKFLOW).toMatch(/^permissions:\n {2}contents: read$/m)
    expect(job('release')).toMatch(/permissions:\n\s+contents: write/)
    expect(job('package')).not.toMatch(/contents: write/)
    expect(job('suite')).not.toMatch(/contents: write/)
  })

  it('refuses a tag that names a version the manifest does not carry', () => {
    const packaging = job('package')

    expect(packaging).toContain('the tag names the version the manifest carries')
    expect(packaging).toMatch(/GITHUB_REF_NAME#v/)
    expect(packaging).toMatch(/require\('\.\/package\.json'\)\.version/)
  })
})
