import { describe, expect, it } from 'vitest'

import { checkForUpdate, isReleasePage, reasonOf, RELEASE_PAGES, type Fetcher } from './updates'

/**
 * RG50: the request, against a network described by hand.
 *
 * Every way of not getting an answer has to arrive as a sentence the dialog can show, never
 * as a throw — a check that could take the main process down is a menu item nobody should be
 * offered.
 */
function answering(status: number, body: unknown): Fetcher {
  return () => Promise.resolve(new Response(JSON.stringify(body), { status }))
}

const PAGE = `${RELEASE_PAGES}tag/v0.2.0`

describe('RG50: asking GitHub for the newest published release', () => {
  it('names a newer release and its page', async () => {
    const check = await checkForUpdate(
      '0.1.0',
      answering(200, { tag_name: 'v0.2.0', html_url: PAGE }),
    )

    expect(check).toEqual({ kind: 'newer', current: '0.1.0', latest: '0.2.0', url: PAGE })
  })

  it('reads a 404 as nothing published yet, which is what a repository of drafts answers', async () => {
    expect(await checkForUpdate('0.1.0', answering(404, { message: 'Not Found' }))).toEqual({
      kind: 'none',
      current: '0.1.0',
    })
  })

  it('says why, for every answer it could not use', async () => {
    const refused = await checkForUpdate('0.1.0', answering(403, { message: 'rate limited' }))
    const odd = await checkForUpdate('0.1.0', answering(200, { name: 'no tag here' }))

    expect(refused).toMatchObject({ kind: 'failed', reason: 'GitHub answered 403' })
    expect(odd).toMatchObject({ kind: 'failed' })
  })

  it('asks the API with a name, and bounded', async () => {
    let asked: RequestInit | undefined
    await checkForUpdate('0.1.0', (_url, init) => {
      asked = init
      return Promise.resolve(new Response('{}', { status: 404 }))
    })

    expect(new Headers(asked?.headers).get('user-agent')).toBe('roadkeep-gui')
    expect(asked?.signal).toBeInstanceOf(AbortSignal)
  })
})

describe('RG156: why a check did not get an answer', () => {
  /** What `fetch` really throws when the network refuses: the reason is on `cause`. */
  function fetchFailed(because: string): Error {
    // Built the way undici builds it, since a test written against a shape fetch never
    // throws is a test that proves nothing about being offline.
    return new TypeError('fetch failed', { cause: new Error(because) })
  }

  it('names what the network did, which fetch keeps on the cause', async () => {
    const offline = await checkForUpdate('0.1.0', () =>
      Promise.reject(fetchFailed('getaddrinfo ENOTFOUND api.github.com')),
    )

    expect(offline).toMatchObject({ kind: 'failed' })
    if (offline.kind !== 'failed') throw new Error('unreachable')
    // `fetch failed` alone tells somebody offline nothing they did not know.
    expect(offline.reason).toContain('ENOTFOUND')
    expect(offline.reason).toContain('fetch failed')
  })

  it('says what a timeout was, rather than reporting it as something else', async () => {
    const timedOut = await checkForUpdate('0.1.0', (_url, init) =>
      // The signal this call was given, aborting the way a real deadline aborts it.
      Promise.reject(init.signal?.reason ?? new Error('no signal')),
    )

    expect(timedOut).toMatchObject({ kind: 'failed' })
  })

  it('reports a body that never arrived as what it was, and not as bad JSON', async () => {
    // A dropped connection while the body is read lands in the same catch as a parse error,
    // and calling it "not JSON" names the wrong thing.
    const dropped = await checkForUpdate('0.1.0', () =>
      Promise.resolve({
        status: 200,
        ok: true,
        json: () => Promise.reject(fetchFailed('terminated')),
      } as unknown as Response),
    )

    expect(dropped).toMatchObject({ kind: 'failed' })
    if (dropped.kind !== 'failed') throw new Error('unreachable')
    expect(dropped.reason).toContain('terminated')
    expect(dropped.reason).not.toContain('not JSON')
  })

  it('still says not JSON for an answer that is not JSON', async () => {
    const garbage = await checkForUpdate('0.1.0', () =>
      Promise.resolve(new Response('<html>no</html>', { status: 200 })),
    )

    expect(garbage).toMatchObject({
      kind: 'failed',
      reason: 'GitHub answered something that is not JSON',
    })
  })

  it('bounds the call, and the deadline is the one that aborts it', async () => {
    // The ceiling is an argument so this is a millisecond and not ten seconds of waiting.
    const late = await checkForUpdate(
      '0.1.0',
      (_url, init) =>
        new Promise<Response>((_resolve, reject) => {
          init.signal?.addEventListener('abort', () => {
            reject(init.signal?.reason ?? new Error('aborted'))
          })
        }),
      1,
    )

    expect(late).toMatchObject({ kind: 'failed' })
    if (late.kind !== 'failed') throw new Error('unreachable')
    expect(late.reason).not.toBe('')
  })

  it('says a thrown thing that is not an error as it was, rather than nothing', () => {
    expect(reasonOf('a string')).toBe('a string')
    expect(reasonOf(new Error('plain'))).toBe('plain')
    expect(reasonOf(new TypeError('outer', { cause: 'not an error' }))).toBe('outer')
  })
})

describe('RG50: the pages the dialog may open', () => {
  it('is this repository`s releases and nothing else', () => {
    expect(isReleasePage(PAGE)).toBe(true)
    expect(isReleasePage('https://github.com/somebody/else/releases/tag/v9')).toBe(false)
    expect(
      isReleasePage('https://example.com/?https://github.com/alegauss/roadkeep-gui/releases/'),
    ).toBe(false)
  })
})

describe('RG155: a path, not a prefix', () => {
  it('refuses a URL whose dot segments climb out of the releases', () => {
    // It starts with the right characters and is another repository's page: the browser
    // normalises `..` after a prefix check has already said yes. The parser normalises the
    // same way, which is what makes what was checked what gets opened.
    expect(isReleasePage(`${RELEASE_PAGES}../../somebody/else`)).toBe(false)
    expect(isReleasePage(`${RELEASE_PAGES}tag/../../../somebody/else`)).toBe(false)
    // `%2E%2E` is `..` to the parser too, so an encoded climb is the same climb.
    expect(isReleasePage(`${RELEASE_PAGES}%2E%2E/%2E%2E/somebody/else`)).toBe(false)
  })

  it('keeps an encoded segment that stays inside, since this refuses climbing and not encoding', () => {
    // `%2F` is not a separator to a parser and is not one to the server either: this is a
    // segment with an odd name under the releases, and it is still a release page.
    expect(isReleasePage(`${RELEASE_PAGES}..%2F..%2Fsomebody%2Felse`)).toBe(true)
    expect(isReleasePage(`${RELEASE_PAGES}tag/v0.2.0%2Bbuild`)).toBe(true)
  })

  it('refuses a host that merely reads like the right one', () => {
    for (const url of [
      'https://github.com.example.test/alegauss/roadkeep-gui/releases/tag/v9',
      'https://notgithub.com/alegauss/roadkeep-gui/releases/tag/v9',
      'https://github.com:8443/alegauss/roadkeep-gui/releases/tag/v9',
      // The authority ends at the first slash, so this one's host is `example.test` and
      // everything that reads like the right page is a password and a path.
      'https://someone:github.com@example.test/alegauss/roadkeep-gui/releases/',
      'https://github.com@example.test/alegauss/roadkeep-gui/releases/',
    ]) {
      expect(isReleasePage(url), url).toBe(false)
    }
  })

  it('refuses credentials in front of the right host, which is a page nobody typed', () => {
    expect(isReleasePage('https://someone@github.com/alegauss/roadkeep-gui/releases/')).toBe(false)
  })

  it('refuses a scheme that is not https, and a string that is no URL at all', () => {
    expect(isReleasePage('http://github.com/alegauss/roadkeep-gui/releases/')).toBe(false)
    expect(isReleasePage('javascript:alert(1)')).toBe(false)
    expect(isReleasePage('')).toBe(false)
    expect(isReleasePage('github.com/alegauss/roadkeep-gui/releases/')).toBe(false)
  })
})
