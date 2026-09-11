import { describe, expect, it } from 'vitest'

import { checkForUpdate, isReleasePage, RELEASE_PAGES, type Fetcher } from './updates'

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
    const offline = await checkForUpdate('0.1.0', () =>
      Promise.reject(new Error('getaddrinfo ENOTFOUND')),
    )
    const odd = await checkForUpdate('0.1.0', answering(200, { name: 'no tag here' }))

    expect(refused).toMatchObject({ kind: 'failed', reason: 'GitHub answered 403' })
    expect(offline).toMatchObject({ kind: 'failed', reason: 'getaddrinfo ENOTFOUND' })
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

describe('RG50: the pages the dialog may open', () => {
  it('is this repository`s releases and nothing else', () => {
    expect(isReleasePage(PAGE)).toBe(true)
    expect(isReleasePage('https://github.com/somebody/else/releases/tag/v9')).toBe(false)
    expect(
      isReleasePage('https://example.com/?https://github.com/alegauss/roadkeep-gui/releases/'),
    ).toBe(false)
  })
})
