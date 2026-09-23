// The social card. Every platform that renders a link preview wants a raster, so this draws
// the card to dist/og.png at 1200x630 on every build, and the card is regenerated whenever the
// mark or the copy on it changes.
//
// The card is a template, not a finished drawing. Its mark is spliced in from public/logo.svg
// at build time rather than pasted into the file, because a card carrying its own copy of the
// artwork goes stale the next time the artwork changes. The template lives here and not in
// public/ for the same reason: it is an input to this script and nothing links it.
//
// And the status pill is measured, not typed. The card asks for DejaVu and takes whatever the
// build machine has, so the same markup rasterises at one width on a runner that ships DejaVu
// and at another on a workstation that falls back to something condensed. resvg measures the
// text here and the pill is drawn round the answer, so it fits whatever font resolves.
import { readFileSync, writeFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { Resvg } from '@resvg/resvg-js'

const here = dirname(fileURLToPath(import.meta.url))
const siteDir = join(here, '..')
const cardPath = join(here, 'og-card.svg')
const logoPath = join(siteDir, 'public', 'logo.svg')
const outPath = join(siteDir, 'dist', 'og.png')

// Where the mark sits on the card, and how big. Sized by height and left to find its width, the
// same rule .brand img and .hero-icon follow in src/index.css.
const MARK = { left: 90, top: 96, height: 132 }

// The pill's left edge, and the space left after the text ends. GUTTER is the card's right
// margin, which the pill may not cross.
const CHIP = { left: 90, padding: 26 }
const GUTTER = 1110

// Measurement and final raster have to agree about which font resolved, or the pill is fitted
// to a font the card is not drawn in.
const FONT = { loadSystemFonts: true, defaultFontFamily: 'DejaVu Sans' }

const card = readFileSync(cardPath, 'utf8')
const logo = readFileSync(logoPath, 'utf8')

const viewBox = logo.match(/\bviewBox="([\d.\-\s]+)"/)
if (!viewBox) throw new Error(`og-image: no viewBox on ${logoPath}`)
const [minX, minY, , boxHeight] = viewBox[1].trim().split(/\s+/).map(Number)

// The logo's own root <svg> cannot come along: an svg element nested in the card would bring its
// own viewport and fit the artwork to a box this script did not choose. Its children can. The
// <title> and <desc> go too, since they name the icon and not the card.
const artwork = logo
  .replace(/^[\s\S]*?<svg\b[^>]*>/, '')
  .replace(/<\/svg>\s*$/, '')
  .replace(/<title>[\s\S]*?<\/title>/, '')
  .replace(/<desc>[\s\S]*?<\/desc>/, '')
  .trim()

const scale = MARK.height / boxHeight
const mark = [
  `<g transform="translate(${MARK.left - minX * scale},${MARK.top - minY * scale})`,
  ` scale(${scale.toFixed(6)})">\n${artwork}\n  </g>`,
].join('')

// Where a piece of the card's own markup lands once this font has had its say. The element is
// rendered alone on a card-sized canvas, so the box comes back in the card's coordinates.
function place(element) {
  const canvas = `<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">${element}</svg>`
  const box = new Resvg(canvas, { font: FONT }).getBBox()
  if (!box) throw new Error(`og-image: nothing to measure in ${element.slice(0, 60)}`)
  return { start: box.x, end: box.x + box.width }
}

const chipText = card.match(/<text\b[^>]*\bid="chip"[\s\S]*?<\/text>/)
if (!chipText) throw new Error('og-image: og-card.svg has no <text id="chip">')
const chipWidth = Math.ceil(place(chipText[0]).end + CHIP.padding - CHIP.left)
if (CHIP.left + chipWidth > GUTTER) {
  throw new Error(`og-image: the status pill needs ${chipWidth}px and runs past x=${GUTTER}`)
}

// A slot that is not there is a card drawn without the thing it was supposed to carry, and
// String.replace says nothing about a pattern it never found.
const filled = { '{{mark}}': mark, '{{chip-width}}': String(chipWidth) }
let svg = card
for (const [slot, value] of Object.entries(filled)) {
  if (!svg.includes(slot)) throw new Error(`og-image: og-card.svg has no ${slot} slot`)
  svg = svg.replace(slot, value)
}

const png = new Resvg(svg, { fitTo: { mode: 'width', value: 1200 }, font: FONT }).render()
const buf = png.asPng()

const { width, height } = png
if (width !== 1200 || height !== 630) {
  throw new Error(`og-image: expected 1200x630, got ${width}x${height}`)
}

writeFileSync(outPath, buf)
console.log(`og-image: dist/og.png  ${width}x${height}  (${(buf.length / 1024).toFixed(0)} kB)`)
