import { BRIDGE_KEY, LOCALE_TAGS, PACKAGED_POLICY, policyText } from '@rk/core'
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
  // No `?.`: the declaration says this is assigned, and it is. A `beforeAll` that threw
  // before assigning fails the file on its own error, and vitest reports the hook's second
  // one beside it rather than instead of it.
  await app.close()
})

describe('RG60: what the renderer was given', () => {
  it('exposes the bridge under the one name the interface declares', async () => {
    expect(await app.evaluate<boolean>(`typeof window['${BRIDGE_KEY}'] === 'object'`)).toBe(true)
  })

  it('exposes exactly the methods it declares and no others', async () => {
    // The preload is a surface, and a surface that grew a method is a surface nobody
    // reviewed. Read off the running object rather than off the type.
    const methods = await app.evaluate<string[]>(`Object.keys(window['${BRIDGE_KEY}']).sort()`)

    // RG143 added the three that reach an engine: which projects, open one, run against it.
    expect(methods).toEqual([
      'identify',
      'open',
      'projects',
      'run',
      'saveLocale',
      'saveTheme',
      'settings',
    ])
  })

  it('round-trips a call through it', async () => {
    const identity = await app.evaluate<{ transport?: string; build?: unknown }>(
      `window['${BRIDGE_KEY}'].identify()`,
    )

    expect(identity.transport).toBe('ipc')
    expect(identity.build).toBeDefined()
  })

  it('answers with a locale this build actually ships', async () => {
    // RG86: the whole path in one call — the main process reads the settings file, asks
    // Electron what the desktop speaks where the tag is empty, and what comes back is a
    // tag `wordingFor` has an answer for. A resolution done in the renderer would pass a
    // unit test and still hand the window a language it cannot draw.
    const launch = await app.evaluate<{ locale?: string; settings?: { locale?: string } }>(
      `window['${BRIDGE_KEY}'].settings()`,
    )

    expect(LOCALE_TAGS).toContain(launch.locale)
    expect(launch.settings?.locale).toBeDefined()
  })

  it('answers the launch read far inside the deadline the renderer holds', async () => {
    // RG106 put a two-second bound on the call the first frame waits for, and what makes
    // that number right is how long a real one takes: an IPC round trip and one small file.
    // Measured in the running app, because nothing else can say.
    const took = await app.evaluate<number>(`
      (async () => {
        const at = performance.now()
        await window['${BRIDGE_KEY}'].settings()
        return performance.now() - at
      })()
    `)

    expect(took).toBeLessThan(200)
  })

  it('keeps a ground the page chose, so the file is the source of it', async () => {
    // RG87: the whole write path in one call, which no unit test reaches — the renderer
    // asks, a handler validates the value and rewrites this profile's settings file, and
    // the next read is the one the next launch would get. The profile is a throwaway
    // temporary directory, so nothing here touches a person's own settings.
    await app.evaluate<null>(`window['${BRIDGE_KEY}'].saveTheme('dark')`)

    const after = await app.evaluate<{ settings?: { theme?: string } }>(
      `window['${BRIDGE_KEY}'].settings()`,
    )

    expect(after.settings?.theme).toBe('dark')
  })

  it('refuses a ground that is not one, rather than writing it', async () => {
    // The argument is the renderer's word, and a resolved ground is not a setting. What is
    // held is that a value the reader would reset never reaches the file at all — so the
    // last real choice is still what a read answers.
    await app.evaluate<null>(`window['${BRIDGE_KEY}'].saveTheme('light')`)
    await app.evaluate<null>(`window['${BRIDGE_KEY}'].saveTheme('midnight')`)

    const after = await app.evaluate<{ settings?: { theme?: string } }>(
      `window['${BRIDGE_KEY}'].settings()`,
    )

    expect(after.settings?.theme).toBe('light')
  })

  it('keeps a language the page chose, which is the second write and the same path', async () => {
    // RG116. The menu is the design system's and moves i18next; what reaches the file is
    // this call, and only a running app can say that the channel, the handler and the
    // rewrite all line up. `pt-BR` because a tag with a region is the one a careless
    // comparison against the package's `pt` would drop.
    await app.evaluate<null>(`window['${BRIDGE_KEY}'].saveLocale('pt-BR')`)

    const after = await app.evaluate<{ settings?: { locale?: string } }>(
      `window['${BRIDGE_KEY}'].settings()`,
    )

    expect(after.settings?.locale).toBe('pt-BR')
  })

  it('refuses a language this build cannot draw, rather than writing it', async () => {
    // A tag nobody wrote reads back as English at the next launch, so storing it would
    // look exactly like the setting having never been saved. Refused at the handler, where
    // `LOCALE_TAGS` is the same list the reader uses.
    await app.evaluate<null>(`window['${BRIDGE_KEY}'].saveLocale('en')`)
    await app.evaluate<null>(`window['${BRIDGE_KEY}'].saveLocale('ja')`)

    const after = await app.evaluate<{ locale?: string; settings?: { locale?: string } }>(
      `window['${BRIDGE_KEY}'].settings()`,
    )

    expect(after.settings?.locale).toBe('en')
    expect(LOCALE_TAGS).toContain(after.locale)
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

    expect(reachable).toHaveLength(7)
    expect(reachable.every((one) => one === 'function')).toBe(true)
  })
})

describe('RG60: where the page may go', () => {
  it('stays put when something assigns a location outside the bundle', async () => {
    // `will-navigate` fires and the guard cancels it. Asserted by asking where the page is
    // afterwards, because a guard that reported correctly and navigated anyway would pass
    // any check that read the decision instead of the outcome.
    //
    // A `file:` path and not an `https:` one, and that is not arbitrary. The guard's correct
    // answer for `https:` is `open-externally`, which really does call `shell.openExternal`
    // — so a test that navigated there proved the page stayed put by opening a tab in the
    // developer's own browser, once per run. This target is refused outright and goes
    // nowhere at all, and it is the case the guard exists for in a packaged run: `file:`
    // URLs share an empty host, so any absolute path on the machine is what gets past a
    // boundary drawn on origin. `navigation.test.ts` holds the `https:` decision, where
    // asserting it costs nothing.
    const before = await app.evaluate<string>('location.href')

    await app.evaluate<void>("location.href = 'file:///nowhere-outside-the-bundle.html'")
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

  it('reports that refusal against the policy this build declares', () => {
    // And the renderer says which directive stopped it, which is the line somebody reads
    // when a legitimate resource is blocked.
    const said = app.console.join('\n')

    expect(said).toContain('cdn.example.com')
    expect(said).toContain('Content Security Policy')
    expect(policyText(PACKAGED_POLICY)).toContain("script-src 'self'")
  })

  it('names the build on screen, which is the criterion a mechanism could not meet', async () => {
    // RG118, asked of the window rather than of a component: the stamp is read in the main
    // process, crosses the bridge and is drawn by the renderer, and only a running app
    // exercises all three. The version comes from the package this was built from, so it
    // is read from the identity rather than written down here.
    const said = await app.evaluate<string>(`
      (async () => {
        const identity = await window['${BRIDGE_KEY}'].identify()
        const footer = document.querySelector('footer')
        return JSON.stringify([footer ? footer.textContent : '', identity.build.version])
      })()
    `)
    const [drawn, version] = JSON.parse(said) as [string, string]

    expect(drawn).toContain(version)
    expect(drawn).toContain('source')
  })

  it('leaves no ground below the footer, which is the half jsdom cannot answer', async () => {
    // `AppFooter` is written `mt-auto` and there is no layout in a unit test, so this is
    // the only place that margin can be checked at all -- and it was wrong when written:
    // a percentage `min-height` resolves against `body`'s auto height, so the chain stopped
    // short and the window drew 66px of ground under the footer.
    //
    // At or below the fold, not exactly at it: a page taller than the window puts the
    // footer past the bottom, which is the same rule and not a second one.
    const measured = await app.evaluate<string>(`
      (() => {
        const footer = document.querySelector('footer')
        return JSON.stringify({
          bottom: Math.round(footer.getBoundingClientRect().bottom),
          viewport: document.documentElement.clientHeight,
        })
      })()
    `)
    const { bottom, viewport } = JSON.parse(measured) as { bottom: number; viewport: number }

    expect(bottom).toBeGreaterThanOrEqual(viewport - 1)
  })

  it('has run its own bundle, which the same policy had to allow', async () => {
    // The control on the control: a policy that blocked everything would also pass the
    // case above, and this is the assertion that says it did not.
    expect(
      await app.evaluate<number>("document.querySelector('#root').childElementCount"),
    ).toBeGreaterThan(0)
  })
})
