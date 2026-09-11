import { describe, expect, it } from 'vitest'

import { job, stepScript, WORKFLOW } from './workflow'

/**
 * RG50: the release a tag leaves behind, held without running a workflow.
 *
 * Two promises live in `ci.yml` and each fails silently. The first is that a release is a
 * decision somebody makes: the job drafts one and a person publishes it, so the day a flag
 * goes missing a tag starts publishing on its own. The second is that the installers say
 * the version the page says: the stamp reads `package.json`, so a tag naming another version
 * would title a release its files disagree with.
 *
 * What this file holds is what the workflow **says**. Whether the tag check refuses anything
 * is `release-live.test.ts`, which runs it (RG157) — the half no reading can answer.
 */

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

  it('runs that check only on a tag, since every other push has no version to match', () => {
    expect(job('package')).toMatch(/if: startsWith\(github\.ref, 'refs\/tags\/v'\)/)
  })

  it('RG157: finds a script under the step, which is what the live half executes', () => {
    // The instrument itself: a step renamed leaves its script where this reading cannot find
    // it, and an empty script would otherwise pass every assertion made of it.
    const found = stepScript(job('package'), 'the tag names the version the manifest carries')

    expect(found).not.toBe('')
    expect(found).toContain('exit 1')
    expect(stepScript(job('package'), 'no step goes by this name')).toBe('')
  })
})
