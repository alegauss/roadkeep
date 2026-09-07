import type { TaskLine } from './payloads'

/**
 * Finding a line by the words on it, across every backlog at once.
 *
 * The symptom is the field a person remembers a task by, and today it is searchable only
 * inside the one backlog already open. This searches all of them — over the payloads
 * already held, never over the files. That is what makes it free on a warm list: no
 * repository is re-read to answer a search, and a search that spawned seventeen processes
 * per keystroke would be one nobody types into.
 *
 * **A project with nothing held is named, not skipped.** A search that quietly covers
 * eleven of seventeen backlogs is one whose empty answer means nothing — and an empty
 * answer is precisely when somebody concludes the task does not exist.
 *
 * The order is the projects' own and then each file's, with no relevance ranking. A
 * relevance score would be a number this app invented, sorted above numbers a verb
 * printed; the same rule that keeps the portfolio from ranking projects keeps this from
 * ranking lines.
 */

/** The three fields worth searching, because they are the three a person recalls. */
export type SearchField = 'id' | 'symptom' | 'why'

export interface SearchableProject {
  readonly path: string
  readonly name: string
  /** The lines held for this project, or null where it has not been read. */
  readonly lines: readonly TaskLine[] | null
}

export interface Hit {
  readonly project: string
  readonly name: string
  readonly line: TaskLine
  /** Which fields the query touched, so a view can show why this is here. */
  readonly matched: readonly SearchField[]
}

export interface SearchAnswer {
  readonly query: string
  readonly hits: readonly Hit[]
  /** Projects the answer does not cover, because nothing is held for them. */
  readonly unsearched: readonly string[]
  /** How many projects the answer does cover. */
  readonly searched: number
}

/** Split a query into terms. Every term has to appear somewhere for a line to match. */
function termsOf(query: string): string[] {
  return query
    .toLowerCase()
    .split(/\s+/)
    .filter((term) => term !== '')
}

function fieldsOf(line: TaskLine): Record<SearchField, string> {
  return {
    id: line.id.toLowerCase(),
    symptom: line.symptom.toLowerCase(),
    why: line.why.toLowerCase(),
  }
}

/** Which fields a term touched. Empty means the line does not match at all. */
function touched(fields: Record<SearchField, string>, term: string): SearchField[] {
  return (['id', 'symptom', 'why'] as const).filter((field) => fields[field].includes(term))
}

export function search(
  projects: readonly SearchableProject[],
  query: string,
): SearchAnswer {
  const terms = termsOf(query)
  const hits: Hit[] = []
  const unsearched: string[] = []
  let searched = 0

  for (const project of projects) {
    if (project.lines === null) {
      unsearched.push(project.path)
      continue
    }
    searched += 1

    // An empty query is not a match-everything. A search box with nothing typed in it
    // should show nothing, not nine hundred lines.
    if (terms.length === 0) continue

    for (const line of project.lines) {
      const fields = fieldsOf(line)
      const matched = new Set<SearchField>()
      let everyTerm = true

      for (const term of terms) {
        const hitFields = touched(fields, term)
        if (hitFields.length === 0) {
          everyTerm = false
          break
        }
        for (const field of hitFields) matched.add(field)
      }

      if (everyTerm) {
        hits.push({
          project: project.path,
          name: project.name,
          line,
          matched: (['id', 'symptom', 'why'] as const).filter((field) => matched.has(field)),
        })
      }
    }
  }

  return { query, hits, unsearched, searched }
}

/** Whether an answer covers everything on the list. An empty answer only means something if it does. */
export function coversEverything(answer: SearchAnswer): boolean {
  return answer.unsearched.length === 0
}
