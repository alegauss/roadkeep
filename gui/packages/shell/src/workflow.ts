import { readFileSync } from 'node:fs'
import path from 'node:path'

/**
 * `ci.yml`, read as text, for the two files that hold promises kept in it.
 *
 * A test instrument and not shipped code — nothing in `main` imports it, as with `live` and
 * `fake-claude`. It is here because RG157 split those promises across the two suites: what the
 * workflow *says* is a fast read, and running the step it declares starts a shell and is
 * therefore live. Both need the same two answers, and a second copy of this is a second idea
 * of where a job ends.
 *
 * **Only as much YAML as the question needs.** A job is the block from its key to the next
 * one's, and a step's script is the indented body under its `run: |`. Neither is a parser, and
 * a workflow that outgrows this reading should be given one rather than a regular expression
 * with more corners.
 */

const REPO = path.resolve(import.meta.dirname, '..', '..', '..')

/** The workflow, whole. Read once: it is a file this repository commits, not a fixture. */
export const WORKFLOW: string = readFileSync(
  path.join(REPO, '.github', 'workflows', 'ci.yml'),
  'utf8',
)

/** One job's block: from its key to the next job's. Empty where no job goes by that name. */
export function job(name: string): string {
  const start = WORKFLOW.indexOf(`\n  ${name}:\n`)
  if (start === -1) return ''
  const rest = WORKFLOW.slice(start + 1)
  const next = rest.slice(1).search(/\n {2}[a-z][\w-]*:\n/)
  return next === -1 ? rest : rest.slice(0, next + 1)
}

/** How far a step's `run: |` body is indented, which is what is stripped to run it. */
const BODY_INDENT = 10

/**
 * The `run:` block of one step, by its name, dedented as a shell will read it.
 *
 * Empty where the step is not there or declares no script, so a caller says what it expected
 * rather than running an empty string and calling it a pass.
 */
export function stepScript(from: string, step: string): string {
  const at = from.indexOf(`- name: ${step}`)
  if (at === -1) return ''
  const run = from.indexOf('run: |', at)
  if (run === -1) return ''

  const lines: string[] = []
  for (const line of from
    .slice(run + 'run: |'.length)
    .split('\n')
    .slice(1)) {
    // The block ends at the first line indented less than its body; a blank line inside it
    // is still inside it.
    const indent = /^\s*/.exec(line)?.[0].length ?? 0
    if (line.trim() !== '' && indent < BODY_INDENT) break
    lines.push(line.slice(BODY_INDENT))
  }
  return lines.join('\n').trim()
}
