// The generated half of the site, held to the sources it was generated from.
//
// scripts/product.mjs writes src/lib/product.generated.ts during the build, and the copy reads
// every count out of it. What this file adds is the check that the committed module is the one
// the sources produce today: a verb added to packages/core and a page that still lists the old
// table is the drift this fails on, before anybody publishes it.
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

import { readProduct } from './product.mjs'

const siteDir = join(dirname(fileURLToPath(import.meta.url)), '..')
const repoRoot = join(siteDir, '..')

function generated() {
  const text = readFileSync(join(siteDir, 'src', 'lib', 'product.generated.ts'), 'utf8')
  const json = text.slice(text.indexOf('= {') + 2)
  return JSON.parse(json)
}

test('the generated module is what the sources say today', () => {
  assert.deepEqual(generated(), readProduct(), 'run `npm run generate` and commit the result')
})

test('the two verb tables are disjoint and neither is empty', () => {
  const { reads, writes } = readProduct()
  assert.ok(reads.length > 0 && writes.length > 0)
  assert.deepEqual(
    reads.filter((v) => writes.includes(v)),
    [],
  )
})

// Lowercase words that open a code run in the copy and are not verbs the window sends. A new
// one fails the test below until somebody decides which it is, which is the point: a verb named
// on the page that neither table carries is a capability the page claims and the app lacks.
const NOT_VERBS = new Set([
  'mcp', // `roadkeep mcp` is the long-lived server process, not a call in either table
  'pip',
  'npm',
  'node_modules',
  'dist',
])

test('every verb the copy names in code is one of the two tables', () => {
  const { reads, writes } = readProduct()
  const verbs = new Set([...reads, ...writes].map((v) => v.split(' ')[0]))
  const sources = ['site-content.ts', 'features.ts'].map((f) =>
    readFileSync(join(siteDir, 'src', 'lib', f), 'utf8'),
  )
  const unknown = new Set()
  for (const text of sources) {
    for (const m of text.matchAll(/\{ code: '([^']+)' \}/g)) {
      const words = m[1].trim().split(/\s+/)
      // `at` rather than an index, because `roadkeep` alone has no second word
      const word = words.at(words[0] === 'roadkeep' ? 1 : 0)
      // Only a bare lowercase word can be a verb: a flag, a path, a file, an id or a sentence
      // of flags is something else and is left to the reader.
      if (word === undefined || !/^[a-z][a-z_]*$/.test(word)) continue
      if (!verbs.has(word) && !NOT_VERBS.has(word)) unknown.add(word)
    }
  }
  assert.deepEqual([...unknown], [], 'the copy names a verb neither table carries')
})

test('every roadkeep law a generated non-goal cites is explained on the page', () => {
  const { nonGoals } = readProduct()
  const cited = new Set(
    nonGoals.flatMap((g) => [...g.why.matchAll(/\bL(\d+)\b/g)].map((m) => `L${m[1]}`)),
  )
  const content = readFileSync(join(siteDir, 'src', 'lib', 'site-content.ts'), 'utf8')
  const explained = content.match(/explainedLaws: \[([^\]]*)\]/)
  assert.ok(explained, 'site-content.ts no longer declares explainedLaws')
  const listed = new Set([...explained[1].matchAll(/'(L\d+)'/g)].map((m) => m[1]))
  assert.deepEqual(
    [...cited].filter((l) => !listed.has(l)),
    [],
    'a non-goal cites a law the intro does not explain',
  )
  assert.deepEqual(
    [...listed].filter((l) => !cited.has(l)),
    [],
    'the intro explains a law no non-goal cites',
  )
})

test('the site mark is the app icon, byte for byte', () => {
  const site = readFileSync(join(siteDir, 'public', 'logo.svg'), 'utf8').replace(/\r\n/g, '\n')
  const app = readFileSync(join(repoRoot, 'build', 'icon.svg'), 'utf8').replace(/\r\n/g, '\n')
  assert.equal(site, app, 'copy build/icon.svg over site/public/logo.svg')
})
