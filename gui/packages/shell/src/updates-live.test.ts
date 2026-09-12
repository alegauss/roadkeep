import { readLatestRelease, verdictOf, type UpdateCheck } from '@rk/core'
import { beforeAll, describe, expect, it } from 'vitest'

import { checkForUpdate, RELEASE_PAGES } from './updates'

/**
 * RG154: the check, against GitHub's own answer.
 *
 * RG50's check has only ever been read against answers described by hand — `tag_name` and
 * `html_url` written into a fake because that is the shape the API documents. What nobody
 * had seen was the shape this repository's own `releases/latest` returns: GitHub keeps
 * drafts out of that answer, so the endpoint was a 404 for the whole life of the feature and
 * the reader was held against a description of a payload rather than one. v0.1.0 is
 * published, so the payload exists.
 *
 * **Asked once, through the call that ships.** `checkForUpdate` is what the menu runs, so
 * the endpoint, the headers and the timeout under test are the shipped ones rather than a
 * second spelling of them here. One request for the whole file, which is also what keeps a
 * runner clear of the unauthenticated rate limit.
 *
 * **A run that cannot reach GitHub skips, and says so.** Rate-limited, offline or behind a
 * proxy, the question this file asks goes unanswered — and a red meaning *the runner had no
 * network* is not the news a red here should carry. Named rather than silently green, which
 * is the rule `scratch-live` states for the same shape. What is never skipped is an answer
 * that arrived: a payload GitHub changed fails, loudly.
 */

/** What the one request answered: the verdict, and the body it was read from. */
let checked: UpdateCheck
let body: unknown

/** `0.0.0` is what every build before the first tag stamped — the build this was written for. */
const BEFORE = '0.0.0'

beforeAll(async () => {
  checked = await checkForUpdate(BEFORE)
  // The same endpoint again only where the first call worked, so the reader can be held
  // against the raw body. Skipped entirely when there is nothing to hold it against.
  if (checked.kind === 'newer' || checked.kind === 'current' || checked.kind === 'ahead') {
    const answered = await fetch(
      'https://api.github.com/repos/alegauss/roadkeep-gui/releases/latest',
      {
        headers: { Accept: 'application/vnd.github+json', 'User-Agent': 'roadkeep-gui' },
        signal: AbortSignal.timeout(15000),
      },
    )
    if (answered.ok) body = await answered.json()
  }
}, 40000)

/**
 * Why this run could not reach GitHub, or empty where it did.
 *
 * **Only the network skips.** `checkForUpdate` codes its failures, and the difference is the
 * whole value of this file: a bare code is the network's own words — offline, a refused
 * connection, a name that did not resolve — and `status` with a 403 or 429 is the
 * unauthenticated rate limit, which a shared runner IP will meet. Those are questions this
 * run cannot ask. Every other failure is an answer that arrived and could not be read, which
 * is exactly the news this file exists to carry, so it is returned as reachable and fails
 * below. Measured: mapping `tag_name` to a key GitHub does not send made all four skip, which
 * is the shape of a gate that reports nothing in the same words as a gate that found nothing.
 */
function unreachable(): string {
  if (checked.kind !== 'failed') return ''
  if (checked.code === '') return `the network did not answer: ${checked.reason}`
  const status = checked.fields['status']
  if (checked.code === 'status' && (status === '403' || status === '429')) {
    return `GitHub rate-limited this runner: ${checked.reason}`
  }
  return ''
}

describe('RG154: the first release, read by the check', () => {
  it('finds a published release at all, which is what the rest rests on', (ctx) => {
    const why = unreachable()
    if (why !== '') ctx.skip(why)

    // `none` is the state the whole feature lived in until v0.1.0 was published, and it is
    // the one this asserts is over. `failed` reaching here is an answer that could not be
    // read, since the network's own failures skipped above.
    expect(checked.kind, checked.kind === 'failed' ? checked.reason : '').not.toBe('failed')
    expect(checked.kind).not.toBe('none')
  })

  it("reads GitHub's own payload with the shape this app holds, not a described one", (ctx) => {
    const why = unreachable()
    if (why !== '') ctx.skip(why)
    if (body === undefined) ctx.skip('the payload was not re-read')

    const read = readLatestRelease(body, '')

    expect(read.ok, read.ok ? '' : `${read.failure.path}: ${read.failure.expected}`).toBe(true)
    if (!read.ok) return
    // The two fields the dialog uses, from the live body: a payload that renamed either
    // would have gone on reading as `ok` against a hand-written fake that never moved.
    expect(read.value.tag).toMatch(/^v\d+\.\d+\.\d+$/)
    expect(read.value.url.startsWith(RELEASE_PAGES)).toBe(true)
  })

  it('names both versions and offers that page, asked from an older build', (ctx) => {
    const why = unreachable()
    if (why !== '') ctx.skip(why)

    expect(checked.kind).toBe('newer')
    if (checked.kind !== 'newer') return
    expect(checked.current).toBe(BEFORE)
    expect(checked.latest).toMatch(/^\d+\.\d+\.\d+$/)
    expect(checked.latest).not.toBe(BEFORE)
    // The page is the release's own and nothing else is ever opened from that dialog.
    expect(checked.url.startsWith(RELEASE_PAGES)).toBe(true)
  })

  it('says the build carrying that version is current, which is the other half', async (ctx) => {
    const why = unreachable()
    if (why !== '') ctx.skip(why)
    if (body === undefined) ctx.skip('the payload was not re-read')

    const read = readLatestRelease(body, '')
    if (!read.ok) throw new Error(`unreadable: ${read.failure.path}`)

    // Compared rather than re-requested: `verdictOf` is the whole of the comparison, and
    // asking GitHub twice for one assertion is a second call against the rate limit.
    const verdict = verdictOf(read.value.tag.replace(/^v/, ''), read.value)

    expect(verdict.kind).toBe('current')
    await Promise.resolve()
  })
})
