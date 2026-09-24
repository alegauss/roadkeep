import { readFileSync, readdirSync } from 'node:fs'
import path from 'node:path'
import { pathToFileURL } from 'node:url'

/**
 * The gate over a responsive class that cannot win (RG230).
 *
 * `index.css` imports Tailwind and then the design system's stylesheets, and the design system
 * ships compiled utilities of its own in the same `utilities` layer. So the page holds two
 * passes of utilities: this app's, then the package's — and a class in both is declared twice,
 * the second time after every responsive rule this app generated.
 *
 * **Measured in Chromium, fourteen pairs, and this rule named every outcome:** a responsive
 * class loses, at every width, when a base class beside it sets the same property and the
 * package ships that base class but not the responsive one. `hidden sm:inline` works, because
 * the package ships `sm:inline` and its copy comes after its `hidden`; `hidden sm:grid` stays
 * hidden, because it ships `hidden` and no `sm:grid`. RG223 shipped `grid-cols-1
 * sm:grid-cols-[…]` that way, and its rows were stacked at 1280 while its test, reading the
 * class strings, passed.
 *
 * **What it cannot see** is a class a component merges in: a design-system `Button` given
 * `max-sm:hidden` carries the package's `inline-flex` on the same element, which is the same
 * defect and invisible in this app's source. The layout tests are what reach that.
 */

/** Where the renderer's sources are, relative to the repository root. */
export const RENDERER = 'packages/ui/src'

/** The stylesheet that decides the order, which names the package's sheets it imports. */
export const ENTRY_CSS = 'packages/ui/src/index.css'

/** The package whose compiled utilities are declared after this app's. */
export const PACKAGE = '@viglet/viglet-design-system'

/** One class split into the conditions it applies under and the utility it applies. */
export interface Split {
  readonly variants: readonly string[]
  readonly utility: string
}

/** A prefix that makes a class apply at some widths and not others. */
const RESPONSIVE = /^(?:(?:max-)?(?:sm|md|lg|xl|2xl)|(?:min|max)-\[[^\]]+\])$/u

/**
 * A class as its variants and its utility, split on the colons outside brackets.
 *
 * Brackets because an arbitrary value may carry a colon of its own — `grid-cols-[a:b]` is one
 * utility and not a variant.
 */
export function splitClass(name: string): Split {
  const parts: string[] = []
  let depth = 0
  let from = 0
  for (let at = 0; at < name.length; at += 1) {
    const char = name[at]
    if (char === '[') depth += 1
    else if (char === ']') depth = Math.max(0, depth - 1)
    else if (char === ':' && depth === 0) {
      parts.push(name.slice(from, at))
      from = at + 1
    }
  }
  parts.push(name.slice(from))
  return { variants: parts.slice(0, -1), utility: parts.at(-1) ?? '' }
}

/** Whether a class applies only by width: every variant it carries is a responsive one. */
export function isResponsive(split: Split): boolean {
  return split.variants.length > 0 && split.variants.every((variant) => RESPONSIVE.test(variant))
}

/**
 * The CSS properties a utility sets, for the properties this app varies by width.
 *
 * Kept to those on purpose: display, the grid's columns, the gaps, flex direction and the
 * alignments are what a phone-width layout changes. A utility outside them answers nothing,
 * which is a pair this gate does not judge rather than one it passes.
 */
export function propertiesOf(utility: string): readonly string[] {
  const bare = utility.replace(/^!/u, '')
  if (
    /^(?:block|inline-block|inline|flex|inline-flex|grid|inline-grid|hidden|contents|table|flow-root)$/u.test(
      bare,
    )
  )
    return ['display']
  if (bare.startsWith('grid-cols-')) return ['grid-template-columns']
  if (bare.startsWith('gap-x-')) return ['column-gap']
  if (bare.startsWith('gap-y-')) return ['row-gap']
  if (bare.startsWith('gap-')) return ['column-gap', 'row-gap']
  if (/^flex-(?:row|col)(?:-reverse)?$/u.test(bare)) return ['flex-direction']
  if (bare.startsWith('items-')) return ['align-items']
  if (bare.startsWith('justify-items-')) return ['justify-items']
  if (/^justify-(?:start|end|center|between|around|evenly|stretch|normal)$/u.test(bare))
    return ['justify-content']
  if (/^text-(?:left|center|right|justify|start|end)$/u.test(bare)) return ['text-align']
  return []
}

/** Every class a stylesheet declares, unescaped: `.sm\:flex` is `sm:flex`. */
export function declaredIn(css: string): Set<string> {
  const names = new Set<string>()
  for (const found of css.matchAll(/\.((?:\\.|[\w-])+)/gu)) {
    names.add((found[1] ?? '').replaceAll(/\\(.)/gu, '$1'))
  }
  return names
}

/** A base class and a responsive class on one element, where the base one wins. */
export interface LosingPair {
  readonly base: string
  readonly responsive: string
}

/** The losing pairs in one list of classes, against what the package ships. */
export function losingPairs(
  classes: readonly string[],
  shipped: ReadonlySet<string>,
): LosingPair[] {
  const splits = classes.map((name) => ({ name, split: splitClass(name) }))
  const bases = splits.filter((one) => one.split.variants.length === 0)
  const found: LosingPair[] = []
  for (const { name, split } of splits) {
    if (!isResponsive(split) || shipped.has(name)) continue
    const sets = propertiesOf(split.utility)
    if (sets.length === 0) continue
    for (const base of bases) {
      if (!shipped.has(base.name)) continue
      if (propertiesOf(base.split.utility).some((property) => sets.includes(property))) {
        found.push({ base: base.name, responsive: name })
      }
    }
  }
  return found
}

/** One losing pair, where it is written. */
export interface PairFinding extends LosingPair {
  /** Repository-relative, forward slashes. */
  readonly file: string
  /** One-based. */
  readonly line: number
  /** One-based. */
  readonly column: number
}

/**
 * Every static string in a source that holds a responsive class, with where it starts.
 *
 * Every string and not only `className="…"`, because a class list is also a constant a cell
 * reuses or a ternary's arm. A template's `${…}` parts are cut out and its text read on either
 * side, so a pair split across an interpolation is one this does not see.
 */
export function classListsIn(source: string): { at: number; classes: string[] }[] {
  const lists: { at: number; classes: string[] }[] = []
  for (const found of source.matchAll(
    /'(?:[^'\\\n]|\\.)*'|"(?:[^"\\\n]|\\.)*"|`(?:[^`\\]|\\.)*`/gu,
  )) {
    const text = found[0].slice(1, -1).replaceAll(/\$\{[^}]*\}/gu, ' ')
    const classes = text.split(/\s+/u).filter((one) => one !== '')
    if (!classes.some((one) => isResponsive(splitClass(one)))) continue
    lists.push({ at: found.index, classes })
  }
  return lists
}

/** Where an offset falls, one-based, as an editor counts. */
export function positionOf(source: string, offset: number): { line: number; column: number } {
  const before = source.slice(0, offset)
  const line = before.split('\n').length
  return { line, column: offset - before.lastIndexOf('\n') }
}

/** The findings in one source file. */
export function pairsIn(file: string, source: string, shipped: ReadonlySet<string>): PairFinding[] {
  return classListsIn(source).flatMap(({ at, classes }) =>
    losingPairs(classes, shipped).map((pair) => ({ file, ...positionOf(source, at), ...pair })),
  )
}

/**
 * The package stylesheets `index.css` imports, resolved through the package's own exports.
 *
 * Read off the entry rather than listed here, so a sheet the app starts importing is one this
 * reads the day it does.
 */
export function packageSheets(repo: string): string[] {
  const entry = readFileSync(path.join(repo, ENTRY_CSS), 'utf8')
  const root = path.join(repo, 'node_modules', ...PACKAGE.split('/'))
  const manifest: unknown = JSON.parse(readFileSync(path.join(root, 'package.json'), 'utf8'))
  const exported =
    typeof manifest === 'object' &&
    manifest !== null &&
    'exports' in manifest &&
    typeof manifest.exports === 'object' &&
    manifest.exports !== null
      ? new Map<string, unknown>(Object.entries(manifest.exports))
      : new Map<string, unknown>()

  const sheets: string[] = []
  for (const found of entry.matchAll(/@import\s+['"]([^'"]+)['"]/gu)) {
    const specifier = found[1] ?? ''
    if (!specifier.startsWith(`${PACKAGE}/`)) continue
    const target = exported.get(`.${specifier.slice(PACKAGE.length)}`)
    const file =
      typeof target === 'string'
        ? target
        : typeof target === 'object' && target !== null && 'default' in target
          ? String(target.default)
          : ''
    if (file.endsWith('.css')) sheets.push(path.join(root, file))
  }
  return sheets
}

function renderSources(directory: string): string[] {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const full = path.join(directory, entry.name)
    if (entry.isDirectory()) return renderSources(full)
    return /\.tsx?$/u.test(entry.name) && !/\.test\.tsx?$/u.test(entry.name) ? [full] : []
  })
}

/** Read the renderer and the package, and answer every losing pair. */
export function classPairs(repo: string): readonly PairFinding[] {
  const sheets = packageSheets(repo)
  // A gate that read no stylesheet would find nothing shipped and pass everything, which is
  // the one answer it must never give quietly.
  if (sheets.length === 0) throw new Error(`${ENTRY_CSS} imports no stylesheet from ${PACKAGE}`)
  const shipped = new Set(sheets.flatMap((sheet) => [...declaredIn(readFileSync(sheet, 'utf8'))]))

  const sources = renderSources(path.join(repo, RENDERER))
  if (sources.length === 0) throw new Error(`${RENDERER} holds no sources to read`)
  return sources.flatMap((file) =>
    pairsIn(path.relative(repo, file).replaceAll('\\', '/'), readFileSync(file, 'utf8'), shipped),
  )
}

/** The findings as the report a person reads, each with the form that works. */
export function reportOf(findings: readonly PairFinding[]): string {
  if (findings.length === 0) return ''
  const lines = findings.map(
    (found) =>
      `  ${found.file}:${String(found.line)}:${String(found.column)}  \`${found.base}\` beats \`${found.responsive}\` at every width`,
  )
  const count =
    findings.length === 1 ? '1 responsive class' : `${String(findings.length)} responsive classes`
  return (
    `roadkeep-gui: ${count} cannot win (RG230).\n` +
    `The design system's stylesheet declares the base class after this app's utilities and does not ship the\n` +
    `responsive one, so the base class applies at every width. Write the wide value as a class the package does\n` +
    `not ship with \`max-sm:\` over it, or put the responsive class on a wrapper of its own:\n\n` +
    `${lines.join('\n')}\n`
  )
}

/** Run as `npm run lint:class-pairs`, beside the other gates. */
function main(): void {
  const repo = path.resolve(import.meta.dirname, '..', '..', '..')
  const findings = classPairs(repo)
  if (findings.length === 0) return
  process.stderr.write(reportOf(findings))
  process.exitCode = 1
}

if (process.argv[1] !== undefined && pathToFileURL(process.argv[1]).href === import.meta.url) {
  main()
}
