import { existsSync, readdirSync, readFileSync } from 'node:fs'
import path from 'node:path'

import { BASE } from '@rk/core'
import { describe, expect, it } from 'vitest'

/**
 * RG124: what the renderer would fetch, read off the renderer.
 *
 * `LanguageSelect` and the `BadgeLocale` inside it draw every row's flag as
 * `<img src="https://flagcdn.com/w40/br.png">` — a request per row to a host RG59's policy
 * refuses, so a screen adopting one draws the component's own globe after a load that
 * failed, and on a machine with no network it is the same picture and a slower one.
 *
 * RG116 found that by trying the control and took `LanguageSwitcher` instead. What was
 * missing is anything that would tell the next person before they spend an afternoon on it,
 * and three places that might have are all the wrong shape: the vendored page reference is
 * rewritten by `viglet-ds-page-reference` and cannot hold a note this repository wrote, the
 * duplicates check reads exports rather than hosts, and the refusal lands in a console
 * during a dev run served from a host the dev policy allows — the one run where it may not
 * appear at all.
 *
 * **So the bundle is the subject.** The renderer is one file after a build, and every host
 * it names is either a request or a piece of prose. Both are held here: nothing assigns an
 * absolute URL to an image source, and every host in the bundle at all is one this file
 * accounts for by name. A component adopted next month that reaches out arrives as a red
 * run naming the host, which is the earliest anything here could say so.
 *
 * It is a live test because its subject is on disk. `built-setup` refuses a bundle older
 * than the tree, so a green run here is a run about this code.
 */
const REPO = path.resolve(import.meta.dirname, '..', '..', '..')
const BUNDLE_DIR = path.join(REPO, 'packages', 'ui', 'dist', 'assets')

function bundled(extension: '.js' | '.css'): string {
  if (!existsSync(BUNDLE_DIR)) {
    throw new Error(`${BUNDLE_DIR} is not there, so there is no bundle to look in.`)
  }

  return readdirSync(BUNDLE_DIR)
    .filter((name) => name.endsWith(extension))
    .map((name) => readFileSync(path.join(BUNDLE_DIR, name), 'utf8'))
    .join('\n')
}

/**
 * Every host the built renderer names, and what it is doing there.
 *
 * A table and not a count, because the answer to *is this a request* is different for each
 * one and none of it is derivable from the string. Three kinds are in here and only the
 * third is a hazard:
 *
 *   namespace  an XML namespace URI, which is an identifier and is never fetched
 *   message    a link inside somebody's warning or error text
 *   fetched    a real endpoint, reached under conditions the reason states
 *
 * A host that is not listed fails the run. That is the point: the list is small enough to
 * read, and the day a component arrives with a fourth entry somebody has to say which kind
 * it is before the suite goes green again.
 */
const ACCOUNTED: readonly { readonly host: string; readonly kind: string; readonly why: string }[] =
  [
    {
      host: 'www.w3.org',
      kind: 'namespace',
      why: "React's `createElementNS` namespaces for SVG and MathML. An identifier, not an address.",
    },
    {
      host: 'react.dev',
      kind: 'message',
      why: 'The error decoder link React puts in a minified error message.',
    },
    {
      host: 'reactrouter.com',
      kind: 'message',
      why: 'The docs link in the router error for a hook used outside a data router.',
    },
    {
      host: 'react.i18next.com',
      kind: 'message',
      why: 'The docs link in the warning about `useSuspense` and a missing boundary.',
    },
    {
      host: 'localhost',
      kind: 'message',
      why: 'The synthetic origin the router gives a history with no document. Never requested.',
    },
    {
      host: 'api.iconify.design',
      kind: 'fetched',
      why: "Iconify's default API, reached only for an `icon` name a caller passes — see RG133.",
    },
    { host: 'api.simplesvg.com', kind: 'fetched', why: "The second of Iconify's three, same." },
    { host: 'api.unisvg.com', kind: 'fetched', why: "The third of Iconify's three, same." },
  ]

const ACCOUNTED_FOR = new Set(ACCOUNTED.map((one) => one.host))

/** Every host the bundle names, deduplicated, in the order a reader would find them. */
function hostsNamed(): string[] {
  return [...new Set(bundled('.js').match(/https?:\/\/[A-Za-z0-9.-]+/g) ?? [])]
    .map((url) => url.replace(/^https?:\/\//, ''))
    .sort()
}

describe('RG124: what the renderer ships an address for', () => {
  it('reads a bundle that is this app, which is what makes the answers below mean anything', () => {
    // The control, and the same one RG61 uses: a bundle that was not built, or read from
    // the wrong place, names no hosts for a reason that is not the good one.
    const bundle = bundled('.js')

    expect(bundle.length).toBeGreaterThan(1000)
    expect(bundle).toContain(BASE['transport.absent'])
  })

  it('names no host this file has not accounted for', () => {
    const unaccounted = hostsNamed().filter((host) => !ACCOUNTED_FOR.has(host))

    expect(
      unaccounted,
      'a host arrived in the renderer that nothing here explains. If it is fetched, the' +
        ' packaged policy (RG59) refuses it and a screen shows whatever the component falls' +
        ' back to; if it is prose, say so in ACCOUNTED and move on.',
    ).toEqual([])
  })

  it('accounts for nothing the bundle has stopped naming', () => {
    // The guard on the guard, and the reason the check above means anything: a reader that
    // found no hosts at all would pass it in silence. This is also what deletes an entry
    // whose dependency dropped the URL — the list is worth reading only while every line
    // of it is still true.
    const named = new Set(hostsNamed())
    const gone = ACCOUNTED.filter((one) => !named.has(one.host)).map((one) => one.host)

    expect(gone, 'the renderer no longer names these, so their reasons are stale').toEqual([])
  })

  it('does not carry the flag CDN, which is the request this line is about', () => {
    // Named rather than left to the check above, because the host is the one measured case
    // and this is the sentence somebody adopting `LanguageSelect` needs to read.
    expect(
      bundled('.js'),
      'a component reaching flagcdn.com is in the renderer — `LanguageSelect` and' +
        ' `BadgeLocale` are the two that do. `LanguageSwitcher` draws no image and is what' +
        ' the header uses (RG116).',
    ).not.toContain('flagcdn')
  })
})

describe('RG124: what it would load a picture from', () => {
  /**
   * An image source assigned an absolute URL.
   *
   * Both spellings, because JSX compiles to a property and a string of HTML does not:
   * `src: "https://…"` and `src="https://…"`. A template literal counts — the flag URL is
   * one — which is why the quote class includes a backtick and why the match stops at the
   * scheme rather than trying to read the rest of the address.
   */
  const ABSOLUTE_IMAGE = /(?:src|srcSet|srcset)\s*[:=]\s*[`"']https?:\/\//g

  it('assigns no image source a host of its own', () => {
    const found = bundled('.js').match(ABSOLUTE_IMAGE) ?? []

    expect(
      found,
      'an image in this renderer loads from an absolute URL. The packaged policy refuses' +
        ' anything but this app`s own origin, so what a person sees is the broken-image' +
        ' fallback — and an offline desktop app should not be asking at all.',
    ).toEqual([])
  })

  it('finds the one that exists, read out of the package that ships it', () => {
    // The guard on the guard, against the real component rather than a string written here
    // to be matched: `BadgeLocale` is the measured case, its built file carries the flag
    // `img`, and a pattern that could not see it there would pass the check above for the
    // wrong reason. The file is found by prefix because its name carries a content hash.
    const dist = path.join(REPO, 'node_modules', '@viglet', 'viglet-design-system', 'dist')
    const specimen = readdirSync(dist).find(
      (name) => name.startsWith('badge-locale') && name.endsWith('.js'),
    )
    if (specimen === undefined) {
      throw new Error(
        'the design system no longer ships a `badge-locale` module, so read RG124 again:' +
          ' this pattern has nothing left to prove itself against.',
      )
    }

    const source = readFileSync(path.join(dist, specimen), 'utf8')

    expect(source).toContain('flagcdn')
    expect(source.match(ABSOLUTE_IMAGE) ?? []).not.toEqual([])
  })

  it('and neither does the stylesheet', () => {
    // The same defect one layer down: a `background-image` from a CDN is refused by the
    // same policy and is invisible in the source, being somebody else's CSS. The fonts are
    // why this is worth holding — eleven `url()` calls, every one of them a woff2 vendored
    // into `assets`, and a release that started fetching them instead would look identical
    // until the app went offline.
    const css = bundled('.css')
    const found = css.match(/url\(\s*['"]?https?:\/\//g) ?? []

    expect(css.match(/url\(/g) ?? []).not.toEqual([])
    expect(found).toEqual([])
  })
})
