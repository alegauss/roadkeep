// Source rules the build cannot see.
//
// Only the reader moves the window: a panel that keeps its own content in view scrolls its own
// element, never scrollIntoView, which scrolls every scrollable ancestor including the document
// and drags a reader who has scrolled past an autoplaying transcript back to it.
//
// And the site fetches no third-party font at page load, which is a stated rule of the page.
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readdirSync, readFileSync, statSync } from 'node:fs'
import { dirname, join, extname, relative } from 'node:path'
import { fileURLToPath } from 'node:url'

const siteDir = join(dirname(fileURLToPath(import.meta.url)), '..')

function walk(dir, out = []) {
  for (const name of readdirSync(dir)) {
    if (name === 'node_modules' || name === 'dist' || name === 'dist-server') continue
    const full = join(dir, name)
    if (statSync(full).isDirectory()) walk(full, out)
    else out.push(full)
  }
  return out
}

const sourceFiles = walk(join(siteDir, 'src')).filter((f) =>
  ['.ts', '.tsx', '.js', '.jsx', '.css'].includes(extname(f)),
)
const rel = (f) => relative(siteDir, f)

test('no source calls scrollIntoView', () => {
  // the call, not the word: a comment explaining why it is avoided is fine
  const offenders = sourceFiles.filter((f) => readFileSync(f, 'utf8').includes('scrollIntoView('))
  assert.deepEqual(
    offenders.map(rel),
    [],
    'a panel must scroll its own element (scrollTop), never scrollIntoView',
  )
})

test('no source fetches a third-party font at page load', () => {
  const all = [...sourceFiles, join(siteDir, 'index.html')]
  const offenders = all.filter((f) =>
    /fonts\.(googleapis|gstatic)\.com/.test(readFileSync(f, 'utf8')),
  )
  assert.deepEqual(offenders.map(rel), [])
})

test('no page links a route without the base prefix', () => {
  // A bare "/compare/" resolves against the domain root on GitHub Pages and 404s there. Both
  // spellings are read: the JSX attribute and the `href:` of a link in the content module.
  const offenders = sourceFiles.filter((f) =>
    /href(?:=|:\s*)["'`{]*["'`]\/(?!roadkeep-gui\/)[a-z]/.test(readFileSync(f, 'utf8')),
  )
  assert.deepEqual(offenders.map(rel), [])
})
