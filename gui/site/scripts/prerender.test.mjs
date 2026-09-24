// The route pair, the twin per route, and the social card, asserted against the built output.
// These read dist/, so they run after `npm run build`, which is what CI does. A claim that has
// gone false (a route with no file, a duplicate title, a twin that leaked the nav or the call to
// action, a card that is not 1200x630) fails here rather than being invisible until somebody
// reads the page against the product.
import { test, before } from 'node:test'
import assert from 'node:assert/strict'
import { existsSync, readFileSync, statSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const siteDir = join(dirname(fileURLToPath(import.meta.url)), '..')
const distDir = join(siteDir, 'dist')

let manifest
before(() => {
  const mf = join(distDir, 'manifest.json')
  assert.ok(existsSync(mf), 'dist/manifest.json is missing: run `npm run build` first')
  manifest = JSON.parse(readFileSync(mf, 'utf8'))
})

const EXPECTED = [
  '/',
  '/claude-code',
  '/compare',
  '/features/portfolio',
  '/features/project',
  '/features/writing',
  '/features/sessions',
  '/features/engine',
]

test('every expected route is in the manifest, and nothing else', () => {
  const paths = manifest.routes.map((r) => r.path)
  const byName = (a, b) => a.localeCompare(b)
  assert.deepEqual([...paths].sort(byName), [...EXPECTED].sort(byName))
})

test('each route has its HTML and Markdown file at the stated size', () => {
  for (const r of manifest.routes) {
    const html = join(distDir, r.html)
    const md = join(distDir, r.markdown)
    assert.ok(existsSync(html), `${r.html} missing`)
    assert.ok(existsSync(md), `${r.markdown} missing`)
    assert.equal(statSync(html).size, r.htmlBytes, `${r.html} size drifted from manifest`)
    assert.equal(statSync(md).size, r.markdownBytes, `${r.markdown} size drifted from manifest`)
  }
})

test('each page has a unique title, its canonical, and an og:image', () => {
  const titles = new Set()
  for (const r of manifest.routes) {
    const html = readFileSync(join(distDir, r.html), 'utf8')
    const title = html.match(/<title>([\s\S]*?)<\/title>/)?.[1]
    assert.ok(title, `${r.html} has no <title>`)
    assert.ok(!titles.has(title), `duplicate <title>: ${title}`)
    titles.add(title)
    assert.ok(html.includes(`<link rel="canonical" href="${r.url}"`), `${r.html} canonical wrong`)
    assert.ok(html.includes('property="og:image"'), `${r.html} has no og:image`)
  }
})

test('every page is prerendered, not an empty mount point', () => {
  for (const r of manifest.routes) {
    const html = readFileSync(join(distDir, r.html), 'utf8')
    assert.ok(!html.includes('<div id="root"></div>'), `${r.html} was not prerendered`)
  }
})

test('no twin leaks the nav, the footer, the ad or a call to action', () => {
  const banned = [
    'View on GitHub',
    'part of alegauss',
    'Sponsored by',
    'data-japode-ads',
    'Download',
  ]
  for (const r of manifest.routes) {
    const md = readFileSync(join(distDir, r.markdown), 'utf8')
    assert.ok(md.trim().length > 0, `${r.markdown} is empty`)
    for (const b of banned) {
      assert.ok(!md.includes(b), `${r.markdown} leaked "${b}"`)
    }
  }
})

test('the landing twin carries the portfolio rows and the hand-over, as text', () => {
  const md = readFileSync(join(distDir, 'index.md'), 'utf8')
  assert.ok(md.includes('Nothing is summed across projects'), 'the portfolio footnote is missing')
  assert.ok(md.includes('brief BS41 --claim'), 'the hand-over transcript is missing')
})

test('the sitemap lists every route exactly once, and nothing else', () => {
  const xml = readFileSync(join(distDir, 'sitemap.xml'), 'utf8')
  const locs = [...xml.matchAll(/<loc>([^<]+)<\/loc>/g)].map((m) => m[1])
  assert.equal(locs.length, manifest.routes.length, 'sitemap URL count differs from the routes')
  assert.equal(new Set(locs).size, locs.length, 'the sitemap lists a URL twice')
  for (const r of manifest.routes) {
    assert.ok(locs.includes(r.url), `sitemap missing ${r.url}`)
  }
  for (const loc of locs) {
    assert.ok(
      loc.startsWith(`https://alegauss.github.io${manifest.base}`),
      `${loc} does not carry ${manifest.base}`,
    )
  }
})

test('the sitemap states no lastmod it cannot derive', () => {
  const xml = readFileSync(join(distDir, 'sitemap.xml'), 'utf8')
  const stamps = [...xml.matchAll(/<lastmod>([^<]+)<\/lastmod>/g)].map((m) => m[1])
  for (const s of stamps) {
    assert.match(s, /^\d{4}-\d{2}-\d{2}$/, `lastmod ${s} is not a plain date`)
  }
  assert.ok(
    stamps.length === 0 || stamps.length === manifest.routes.length,
    'lastmod is on some routes and not others',
  )
})

test('robots allows everything and names the sitemap that was written', () => {
  const robots = readFileSync(join(distDir, 'robots.txt'), 'utf8')
  assert.match(robots, /^User-agent: \*$/m)
  assert.match(robots, /^Allow: \/$/m)
  const named = robots.match(/^Sitemap: (\S+)$/m)
  assert.ok(named, 'robots.txt names no sitemap')
  assert.equal(named[1], `https://alegauss.github.io${manifest.base}sitemap.xml`)
  assert.ok(existsSync(join(distDir, 'sitemap.xml')), 'robots names a sitemap that is not there')
})

test('the social card is a 1200x630 PNG', () => {
  const png = join(distDir, 'og.png')
  assert.ok(existsSync(png), 'dist/og.png missing')
  const buf = readFileSync(png)
  assert.equal(buf.toString('ascii', 1, 4), 'PNG', 'og.png is not a PNG')
  assert.equal(buf.readUInt32BE(16), 1200, 'og.png width')
  assert.equal(buf.readUInt32BE(20), 630, 'og.png height')
})
