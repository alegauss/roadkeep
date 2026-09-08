import { BRIDGE_KEY, PACKAGED_POLICY, policyText } from '@rk/core'
import { afterAll, beforeAll, describe, expect, it } from 'vitest'

import { startApp, type RunningApp } from './running-app'

/**
 * RG60: the questions that only a running window can answer.
 *
 * Every one of these was run by hand once, against one build, by somebody who happened to
 * think of it. What makes them worth automating is that each has an answer the source
 * cannot give: `require` is undefined because the sandbox is on, not because a constant
 * says it should be, and `window.roadkeep` holds what the preload actually exposed.
 *
 * This is the built app, so it needs `npm run build` to have run — which is why it is not a
 * unit test and why CI runs the build before the suite.
 */
let app: RunningApp

beforeAll(async () => {
  app = await startApp()
}, 120000)

afterAll(async () => {
  await app?.close()
})

describe('RG60: what the renderer was given', () => {
  it('exposes the bridge under the one name the interface declares', async () => {
    expect(await app.evaluate<boolean>(`typeof window['${BRIDGE_KEY}'] === 'object'`)).toBe(true)
  })

  it('exposes exactly the methods it declares and no others', async () => {
    // The preload is a surface, and a surface that grew a method is a surface nobody
    // reviewed. Read off the running object rather than off the type.
    const methods = await app.evaluate<string[]>(`Object.keys(window['${BRIDGE_KEY}']).sort()`)

    expect(methods).toEqual(['identify'])
  })

  it('round-trips a call through it', async () => {
    const identity = await app.evaluate<{ transport?: string; build?: unknown }>(
      `window['${BRIDGE_KEY}'].identify()`,
    )

    expect(identity.transport).toBe('ipc')
    expect(identity.build).toBeDefined()
  })
})

describe('RG60: what the renderer was not given', () => {
  it.each(['require', 'process', 'module', 'exports', 'global'])('has no %s', async (name) => {
    // The sandbox and context isolation, asked rather than read. A `webPreferences` flag
    // dropped by a later edit fails here and nowhere else in this suite.
    expect(await app.evaluate<string>(`typeof window['${name}']`)).toBe('undefined')
  })

  it('has no ipcRenderer, so the bridge is the whole of the channel', async () => {
    expect(await app.evaluate<string>("typeof window['ipcRenderer']")).toBe('undefined')
    expect(await app.evaluate<string>("typeof window['electron']")).toBe('undefined')
  })

  it('cannot reach Node through the bridge object either', async () => {
    // A preload that leaked a live object rather than a value would show up here: the
    // bridge's own properties are what a page can walk.
    const reachable = await app.evaluate<string[]>(
      `Object.values(window['${BRIDGE_KEY}']).map((one) => typeof one)`,
    )

    expect(reachable).toEqual(['function'])
  })
})

describe('RG60: where the page may go', () => {
  it('stays put when something assigns a location outside the bundle', async () => {
    // `will-navigate` fires and the guard cancels it. Asserted by asking where the page is
    // afterwards, because a guard that reported correctly and navigated anyway would pass
    // any check that read the decision instead of the outcome.
    const before = await app.evaluate<string>('location.href')

    await app.evaluate<void>("location.href = 'https://example.com/'")
    await app.evaluate<void>('new Promise((done) => setTimeout(done, 500))')

    expect(await app.evaluate<string>('location.href')).toBe(before)
  })
})

describe('RG60: what the page may load', () => {
  it('refuses a script from another host', async () => {
    // RG59's proof, automated: the tag is added to the live page and its own error event
    // is what answers, so nothing here has to parse a log line.
    const refused = await app.evaluate<boolean>(`
      new Promise((done) => {
        const tag = document.createElement('script')
        tag.src = 'https://cdn.example.com/injected.js'
        tag.onerror = () => done(true)
        tag.onload = () => done(false)
        document.head.append(tag)
        setTimeout(() => done(false), 3000)
      })
    `)

    expect(refused).toBe(true)
  })

  it('reports that refusal against the policy this build declares', async () => {
    // And the renderer says which directive stopped it, which is the line somebody reads
    // when a legitimate resource is blocked.
    const said = app.console.join('\n')

    expect(said).toContain('cdn.example.com')
    expect(said).toContain('Content Security Policy')
    expect(policyText(PACKAGED_POLICY)).toContain("script-src 'self'")
  })

  it('has run its own bundle, which the same policy had to allow', async () => {
    // The control on the control: a policy that blocked everything would also pass the
    // case above, and this is the assertion that says it did not.
    expect(
      await app.evaluate<number>("document.querySelector('#root').childElementCount"),
    ).toBeGreaterThan(0)
  })
})
