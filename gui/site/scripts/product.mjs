// The numbers come from the source, never from the copy.
//
// A count typed into a sentence is true on the day it is typed and nothing fails the day it
// stops being. So every figure the site states about the app is read here, out of the committed
// file that owns it, by a plain text parse with no build step:
//
//   packages/core/src/verbs.ts      the read verbs, as `commands` publishes their names
//   packages/core/src/writes.ts     the write verbs, the separate table on purpose
//   packages/core/src/locales.ts    the languages the window speaks, by their own names
//   packages/core/src/roots.ts      the default scan depth and its ceiling
//   packages/shell/src/posture.ts   the renderer posture a packaged build must keep
//   packages/shell/src/question.ts  the tools an "Explain" question may use, and its turn cap
//   package.json                    the version and the licence
//   electron-builder.yml            which installers are built, per platform
//   docs/ROADMAP.md                 the non-goals, which roadkeep keeps in that file
//
// Then the copy states the reason and this states the number. A malformed or missing source
// throws: a red build, never a page left confidently stale.
import { readFileSync, writeFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const here = dirname(fileURLToPath(import.meta.url))
const siteDir = join(here, '..')
const repoRoot = join(siteDir, '..')
const outFile = join(siteDir, 'src', 'lib', 'product.generated.ts')

export const SOURCES = {
  verbs: join(repoRoot, 'packages', 'core', 'src', 'verbs.ts'),
  writes: join(repoRoot, 'packages', 'core', 'src', 'writes.ts'),
  locales: join(repoRoot, 'packages', 'core', 'src', 'locales.ts'),
  roots: join(repoRoot, 'packages', 'core', 'src', 'roots.ts'),
  posture: join(repoRoot, 'packages', 'shell', 'src', 'posture.ts'),
  question: join(repoRoot, 'packages', 'shell', 'src', 'question.ts'),
  packageJson: join(repoRoot, 'package.json'),
  builder: join(repoRoot, 'electron-builder.yml'),
  roadmap: join(repoRoot, 'docs', 'ROADMAP.md'),
}

// Line endings normalised, because a Windows checkout may carry CRLF and every pattern below
// is written against `\n`.
function read(path, what) {
  try {
    return readFileSync(path, 'utf8').replace(/\r\n/g, '\n')
  } catch (err) {
    throw new Error(`product: cannot read ${what} at ${path}: ${err.message}`, { cause: err })
  }
}

/**
 * The body of the object literal assigned after `anchor`. It opens at `= {` and not at the
 * first brace, because a table's type annotation (`{ [K in VerbName]: ... }`) has braces too.
 */
function block(text, anchor, what) {
  const at = text.indexOf(anchor)
  if (at < 0) throw new Error(`product: ${what} no longer contains "${anchor}"`)
  const assign = text.indexOf('= {', at + anchor.length)
  if (assign < 0) throw new Error(`product: ${what} has "${anchor}" with no object after it`)
  const open = assign + 2
  let depth = 0
  for (let i = open; i < text.length; i += 1) {
    if (text[i] === '{') depth += 1
    if (text[i] === '}') {
      depth -= 1
      if (depth === 0) return text.slice(open + 1, i)
    }
  }
  throw new Error(`product: ${what} has an unclosed block after "${anchor}"`)
}

/**
 * The keys of a table whose entries each begin a line at two spaces of indent: `  name: (`.
 * Deeper lines are the builders' own bodies, which is why the indent is part of the pattern.
 */
function tableKeys(body, what) {
  const keys = [...body.matchAll(/^ {2}([a-zA-Z]+):/gm)].map((m) => m[1])
  if (keys.length === 0) throw new Error(`product: found no entries in ${what}`)
  return keys
}

/** A spelling map, `key: ['word', 'word']`, as an object of arrays. */
function spellings(body) {
  const out = {}
  for (const m of body.matchAll(/^ {2}([a-zA-Z]+):\s*\[([^\]]*)\]/gm)) {
    out[m[1]] = [...m[2].matchAll(/'([^']+)'/g)].map((w) => w[1])
  }
  return out
}

/** A table's verbs as `commands` publishes them: the spelling's words joined, else the key. */
function published(text, tableAnchor, wordsAnchor, what) {
  const keys = tableKeys(block(text, tableAnchor, what), `${what} ${tableAnchor}`)
  const words = spellings(block(text, wordsAnchor, what))
  for (const key of Object.keys(words)) {
    if (!keys.includes(key)) {
      throw new Error(`product: ${what} spells "${key}", which its table does not carry`)
    }
  }
  return keys.map((key) => (words[key] ?? [key]).join(' '))
}

export function readProduct() {
  // --- the two verb tables ---
  const verbsText = read(SOURCES.verbs, 'the read verbs')
  const reads = published(verbsText, 'export const VERBS:', 'export const VERB_WORDS:', 'verbs.ts')
  const writesText = read(SOURCES.writes, 'the write verbs')
  const writes = published(
    writesText,
    'export const WRITES:',
    'export const WRITE_WORDS:',
    'writes.ts',
  )
  const overlap = reads.filter((verb) => writes.includes(verb))
  if (overlap.length > 0) {
    throw new Error(`product: ${overlap.join(', ')} is in both the read and the write table`)
  }

  // --- the languages, by the name each calls itself ---
  const localesText = read(SOURCES.locales, 'the locales')
  const languages = [
    ...block(localesText, 'export const LOCALE_NAMES', 'locales.ts').matchAll(
      /^\s*\[[A-Z_]+\]:\s*'([^']+)'/gm,
    ),
  ].map((m) => m[1])
  if (languages.length === 0) throw new Error('product: locales.ts names no language')

  // --- the scan ---
  const rootsText = read(SOURCES.roots, 'the scan roots')
  const number = (name) => {
    const m = rootsText.match(new RegExp(`export const ${name} = (\\d+)`))
    if (!m) throw new Error(`product: roots.ts no longer declares ${name} as a number`)
    return Number(m[1])
  }
  const scan = { defaultDepth: number('DEFAULT_DEPTH'), depthCeiling: number('DEPTH_CEILING') }
  if (!/export const NO_DEFAULT_ROOTS[^=]*=\s*\[\]/.test(rootsText)) {
    throw new Error('product: roots.ts no longer declares NO_DEFAULT_ROOTS as empty')
  }

  // --- the renderer posture a packaged build must keep ---
  const postureText = read(SOURCES.posture, 'the renderer posture')
  const posture = Object.fromEntries(
    [
      ...block(postureText, 'export const REQUIRED_POSTURE', 'posture.ts').matchAll(
        /^\s*([a-zA-Z]+):\s*(true|false)/gm,
      ),
    ].map((m) => [m[1], m[2] === 'true']),
  )
  if (Object.keys(posture).length === 0) throw new Error('product: posture.ts requires nothing')

  // --- what an "Explain" question may do ---
  const questionText = read(SOURCES.question, 'the question runner')
  const toolsMatch = questionText.match(/export const READ_TOOLS = \[([^\]]*)\]/)
  const turnsMatch = questionText.match(/export const QUESTION_TURNS = (\d+)/)
  if (!toolsMatch || !turnsMatch) {
    throw new Error('product: question.ts no longer declares READ_TOOLS and QUESTION_TURNS')
  }
  const question = {
    tools: [...toolsMatch[1].matchAll(/'([^']+)'/g)].map((m) => m[1]),
    turns: Number(turnsMatch[1]),
  }

  // --- the version and the licence ---
  const pkg = JSON.parse(read(SOURCES.packageJson, 'package.json'))
  if (typeof pkg.version !== 'string' || typeof pkg.license !== 'string') {
    throw new Error('product: package.json has no version or licence string')
  }

  // --- the installers ---
  // A line parse rather than a YAML parser, because a dependency to read three keys is a
  // dependency to keep. It reads the targets under each platform's own `target:` list.
  const builder = read(SOURCES.builder, 'electron-builder.yml')
  const targetsOf = (platform) => {
    const section = builder.match(new RegExp(`^${platform}:\\n((?:[ #].*\\n|\\n)*)`, 'm'))
    if (!section) return []
    return [...section[1].matchAll(/^ {4}- (?:target: )?([A-Za-z0-9]+)\s*$/gm)].map((m) => m[1])
  }
  const installers = { win: targetsOf('win'), linux: targetsOf('linux'), mac: targetsOf('mac') }
  if (installers.win.length === 0 || installers.linux.length === 0) {
    throw new Error('product: electron-builder.yml builds no Windows or no Linux target')
  }

  // --- the non-goals, as roadkeep keeps them ---
  const roadmap = read(SOURCES.roadmap, 'the roadmap')
  const ngStart = roadmap.search(/^## Non-goals\s*$/m)
  if (ngStart < 0) throw new Error('product: ROADMAP.md has no "## Non-goals" section')
  const ngRest = roadmap.slice(ngStart).split('\n').slice(1).join('\n')
  const ngEnd = ngRest.search(/^## /m)
  const ngBody = ngEnd < 0 ? ngRest : ngRest.slice(0, ngEnd)
  const nonGoals = ngBody
    .split(/^- /m)
    .slice(1)
    .map((item) => {
      const m = item.match(/^\*\*(.+?)\*\*\s+([\s\S]*)$/)
      if (!m) throw new Error(`product: a non-goal does not open with a bold title: ${item}`)
      return {
        title: m[1].trim(),
        why: m[2]
          .replace(/\s+/g, ' ')
          .replace(/\s*\((?:RG\d+(?:, RG\d+)*)\)/g, '')
          .trim(),
      }
    })
  if (nonGoals.length === 0) throw new Error('product: ROADMAP.md declares no non-goal')

  return {
    version: pkg.version,
    license: pkg.license,
    reads,
    writes,
    languages,
    scan,
    posture,
    question,
    installers,
    nonGoals,
  }
}

// Written only when run as the script, so a test can import readProduct and parse the sources
// again without touching the generated module.
if (process.argv[1] && fileURLToPath(import.meta.url) === join(process.argv[1])) {
  const product = readProduct()
  const header = [
    "// Generated by scripts/product.mjs from this repository's own source. Do not edit:",
    '// `npm run generate` rewrites it, and scripts/product.test.mjs fails a build whose copy of',
    '// it no longer matches what the sources say.',
    "import type { Product } from './product-types'",
    '',
  ].join('\n')
  writeFileSync(
    outFile,
    `${header}\nexport const product: Product = ${JSON.stringify(product, null, 2)}\n`,
  )
  console.log(
    `product: ${product.reads.length} reads, ${product.writes.length} writes, ` +
      `${product.languages.length} languages, ${product.nonGoals.length} non-goals, v${product.version}`,
  )
}
