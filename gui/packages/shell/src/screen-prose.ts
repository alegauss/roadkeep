import path from 'node:path'
import { pathToFileURL } from 'node:url'

import type { Node, SourceFile } from 'typescript/unstable/ast'

/**
 * The gate over prose a screen must not draw (RG191).
 *
 * The pseudo-locale run reads what is on the screen, so it catches an English sentence only
 * in a state the run puts the window into. The window has four surfaces and a dozen states
 * each, and a run reaches a handful — so a screen drawing `unreadable.message` again passes
 * every run that never reaches it.
 *
 * This is the other kind of check: one pass over the renderer's sources for a shape nothing
 * else can see, failing on the line rather than on the screen. It sits beside
 * `lint:duplicates` in `npm run lint` for the same reason that one does.
 *
 * **The list lives on the field, not here.** A field this app wrote in English carries
 * `@notForScreen` in its own docstring, and the tag's text names what to draw instead. So
 * the rule grows with the codes and never with the screens: a new code is a new docstring,
 * and nothing in this file changes.
 *
 * **It reads types, not text.** `cause.message` on a caught `Error` and `answered.message`
 * on an app payload are the same six characters, and only the checker can tell them apart.
 * Every candidate is resolved to the symbol it actually reads, and the tag is looked up on
 * that symbol's declaration — so the rule is about a field and never about a string.
 */

/** The tag a field carries to say a screen must not draw it. Its text names the replacement. */
export const NOT_FOR_SCREEN = 'notForScreen'

/** Where the renderer's sources are, relative to the repository root. */
export const RENDERER = 'packages/ui/src'

/** The project whose sources this reads. The renderer is the half that draws. */
export const RENDERER_PROJECT = 'packages/ui/tsconfig.json'

/** One place a screen reads prose it is not meant to draw. */
export interface ProseFinding {
  /** Repository-relative, forward slashes, so the line is the same on every machine. */
  readonly file: string
  /** One-based, as an editor counts. */
  readonly line: number
  /** One-based, as an editor counts. */
  readonly column: number
  /** The expression as it is written, e.g. `answered.message`. */
  readonly read: string
  /** What the field's own tag says to draw instead. */
  readonly instead: string
}

/**
 * A tag's text as one line.
 *
 * A docstring wraps, so the text arrives with the newlines the author wrapped it at. What
 * goes in a failure is one line, because a report a person scans is a line per finding.
 */
export function oneLine(text: string): string {
  return text.replaceAll(/\s+/gu, ' ').trim()
}

/**
 * What the field says to draw instead, or null where it is not tagged at all.
 *
 * A tag with no text is a field that says *not this* without saying what — which is worth
 * reporting rather than swallowing, so it answers the tag's own name.
 */
export function replacementFrom(
  tags: readonly { readonly name: string; readonly text?: string | undefined }[],
): string | null {
  const tag = tags.find((one) => one.name === NOT_FOR_SCREEN)
  if (tag === undefined) return null
  const text = oneLine(tag.text ?? '')
  return text === '' ? `whatever \`@${NOT_FOR_SCREEN}\` on it names` : text
}

/**
 * The findings as the report a person reads.
 *
 * Every line names the file, the position, what is read and what to read instead — the last
 * being the whole point, since a gate that says only *no* costs the reader the search this
 * already did.
 */
export function reportOf(findings: readonly ProseFinding[]): string {
  if (findings.length === 0) return ''
  const lines = findings.map(
    (found) =>
      `  ${found.file}:${found.line}:${found.column}  \`${found.read}\`\n      draw ${found.instead}`,
  )
  const count = findings.length === 1 ? '1 place draws' : `${String(findings.length)} places draw`
  return (
    `roadkeep-gui: ${count} prose this app wrote in English (RG191).\n` +
    `A screen says it in the window's language, which means the code and not the sentence:\n\n` +
    `${lines.join('\n')}\n`
  )
}

/** Whether a renderer source is one a person ever sees the output of. A test is not. */
export function isDrawn(file: string): boolean {
  return file.includes(`/${RENDERER}/`) && !/\.test\.tsx?$/u.test(file)
}

/**
 * Where a node's own text starts.
 *
 * A node begins at the end of the one before it, so `pos` is the whitespace in between and
 * a position taken from it points at the end of the previous line. What an editor opens at
 * is the first character of the word.
 */
export function wordAt(text: string, from: number): number {
  let at = from
  while (at < text.length && /\s/u.test(text[at] ?? '')) at += 1
  return at
}

/**
 * Every candidate name node in one file.
 *
 * Three ways a field is read, and each resolves through the same call: `x.message`, the
 * `{ message }` a destructuring binds, and the `x['message']` neither of those covers. What
 * is collected is the *name*, because that is the node the checker resolves to the property.
 */
function candidatesIn(sf: SourceFile, ast: typeof import('typescript/unstable/ast')): Node[] {
  const found: Node[] = []
  const walk = (node: Node): void => {
    if (ast.isPropertyAccessExpression(node)) found.push(node.name)
    else if (ast.isBindingElement(node)) {
      // Both are optional in the grammar: an array pattern binds by position and names no
      // property, and a rest element binds neither.
      const named = node.propertyName ?? node.name
      if (named !== undefined && ast.isIdentifier(named)) found.push(named)
    } else if (ast.isElementAccessExpression(node) && ast.isStringLiteral(node.argumentExpression))
      found.push(node.argumentExpression)
    node.forEachChild(walk)
  }
  sf.forEachChild(walk)
  return found
}

/**
 * Read a project and answer every place it draws a tagged field.
 *
 * The whole program is loaded because the rule needs the checker: the project's own
 * `tsconfig` is what says which files it holds and what each name in them means.
 *
 * **The scope is an argument so that the rule can be pointed at code that breaks it.** The
 * renderer is clean, and a gate only ever run against clean code is a gate nobody has seen
 * work — so the suite points this at `core`, where reading the prose is correct and the
 * same three steps have to resolve for it to be found.
 */
export async function screenProse(
  repo: string,
  config: string = RENDERER_PROJECT,
  drawnBy: (file: string) => boolean = isDrawn,
): Promise<readonly ProseFinding[]> {
  const ast = await import('typescript/unstable/ast')
  const { API } = await import('typescript/unstable/sync')

  const api = new API({ cwd: repo })
  try {
    const snapshot = api.updateSnapshot({ openProjects: [config] })
    const project = snapshot.getProjects()[0]
    if (project === undefined) throw new Error(`no project loaded from ${config}`)

    const drawn = project.program.getSourceFileNames().filter(drawnBy)
    // A gate that reads nothing reports nothing, which is the one answer it must never give
    // quietly: a moved directory or a renamed config would otherwise read as green.
    if (drawn.length === 0) throw new Error(`${config} holds no sources to read`)

    const findings: ProseFinding[] = []
    for (const name of drawn) {
      const sf = project.program.getSourceFile(name)
      if (sf === undefined) continue
      const candidates = candidatesIn(sf, ast)
      if (candidates.length === 0) continue
      const symbols = project.checker.getSymbolAtLocation(candidates)
      for (const [index, symbol] of symbols.entries()) {
        if (symbol === undefined) continue
        const instead = replacementFrom(project.checker.getJsDocTagsOfSymbol(symbol))
        if (instead === null) continue
        const node = candidates[index]
        if (node === undefined) continue
        // The whole read — `unreadable.message` and not `message` — because the field's name
        // alone does not say which of a file's dozen `message`s this is.
        const read = node.parent
        const start = wordAt(sf.text, read.pos)
        const at = sf.getLineAndCharacterOfPosition(start)
        findings.push({
          file: path.relative(repo, name).replaceAll('\\', '/'),
          line: at.line + 1,
          column: at.character + 1,
          read: oneLine(sf.text.slice(start, read.end)),
          instead,
        })
      }
    }
    return findings
  } finally {
    api.close()
  }
}

/** Run as `npm run lint:screen-prose`, and in CI beside the other gates. */
async function main(): Promise<void> {
  const repo = path.resolve(import.meta.dirname, '..', '..', '..')
  const findings = await screenProse(repo)
  if (findings.length === 0) return
  process.stderr.write(reportOf(findings))
  process.exitCode = 1
}

if (process.argv[1] !== undefined && pathToFileURL(process.argv[1]).href === import.meta.url) {
  await main()
}
