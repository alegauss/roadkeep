/**
 * Which advisories this project has already answered, and what to do with the rest.
 *
 * Nothing here runs `npm audit` — that is `audit.ts`, which has the process. This is the
 * reading and the rule, so both are testable against a report captured from a real run
 * rather than against a description of one.
 *
 * **The exception list is the whole design** (RG95). A gate over `npm audit` that could not
 * be satisfied would be a gate somebody adds a flag to silence, and an advisory with no
 * published fix is the ordinary case rather than the exception. So an advisory is accepted
 * by writing down its id, why it does not reach this executable, and the date that was
 * established — and everything not on that list fails the run.
 *
 * **An exception that no longer matches anything also fails.** That is the half a list like
 * this normally lacks: entries accumulate, nobody removes them, and after a while the list
 * is a record of what somebody once worried about rather than of what is true. Here, the day
 * an advisory is gone the gate says so and the answer is to delete four lines.
 *
 * **GHSA ids and not npm's numbers.** `npm audit` reports both — a numeric `source` and a
 * URL — and the numeric one is npm's own registry key. The GHSA id is GitHub's, appears in
 * the URL, and is what a person searching for the advisory will find.
 */

/** How bad an advisory has to be before this project is told about it. */
export const SEVERITIES = ['info', 'low', 'moderate', 'high', 'critical'] as const
export type Severity = (typeof SEVERITIES)[number]

/** The floor. Below it an advisory is reported by Dependabot and gates nothing. */
export const GATED_AT: Severity = 'high'

export interface Accepted {
  /** The GHSA id, as it appears in the advisory URL. */
  readonly id: string
  /** The package it is against, so a reader can see it without opening the link. */
  readonly of: string
  /** Why it does not reach anybody who installs this app. */
  readonly why: string
  /** When that was established, so an answer nobody has re-read is visible as old. */
  readonly established: string
}

/**
 * The advisories this project has read and accepted.
 *
 * Both are the same package arriving the same way, and both are answered by RG61 at length:
 * `advisory-live.test.ts` holds that the code is in no bundle and `electron-builder.yml`
 * packages no dependency tree at all. What is written here is the summary and the pointer,
 * not a second copy of that argument.
 */
export const ACCEPTED: readonly Accepted[] = [
  {
    id: 'GHSA-4r6h-8v6p-xvw6',
    of: 'xlsx',
    why: 'prototype pollution in an unmaintained SheetJS build that arrives with the design system and is imported by nothing here, so it is in no bundle and the installer packages no dependency tree — RG61, held by advisory-live.test.ts',
    established: '2026-09-09',
  },
  {
    id: 'GHSA-5pgg-2g8v-p4x9',
    of: 'xlsx',
    why: 'a ReDoS in the same unmaintained build, reaching this tree the same way and answered the same way — RG61',
    established: '2026-09-09',
  },
]

/** One advisory, as this project reads one. */
export interface Advisory {
  /** The GHSA id, taken from the URL. Empty where the report carried none. */
  readonly id: string
  readonly of: string
  readonly severity: Severity
  readonly title: string
  readonly url: string
}

function severityOf(value: unknown): Severity | null {
  return SEVERITIES.includes(value as Severity) ? (value as Severity) : null
}

/** Whether one severity is at or above another, by the order they are declared in. */
export function atLeast(severity: Severity, floor: Severity): boolean {
  return SEVERITIES.indexOf(severity) >= SEVERITIES.indexOf(floor)
}

/** The GHSA id out of an advisory URL, or the empty string. */
export function idIn(url: string): string {
  return /GHSA-[\da-z-]+/i.exec(url)?.[0] ?? ''
}

interface WireVia {
  source?: unknown
  title?: unknown
  severity?: unknown
  url?: unknown
  dependency?: unknown
}

interface WireVulnerability {
  via?: unknown
}

/**
 * Every advisory a report names, at or above the floor.
 *
 * Read off `via` rather than off the top-level entries, because those are packages and this
 * is about advisories: one package answers for several, and a package that is only affected
 * *through* another carries the string name of that other rather than an advisory of its
 * own. Deduplicated by id, since the same advisory reaches several packages.
 */
export function advisoriesIn(report: unknown, floor: Severity = GATED_AT): Advisory[] {
  const found = new Map<string, Advisory>()
  const vulnerabilities = (report as { vulnerabilities?: unknown } | null)?.vulnerabilities
  if (typeof vulnerabilities !== 'object' || vulnerabilities === null) return []

  for (const entry of Object.values(vulnerabilities as Record<string, WireVulnerability>)) {
    if (!Array.isArray(entry.via)) continue
    for (const via of entry.via as WireVia[]) {
      // A string here is another package's name, not an advisory. The advisory is on that
      // package's own entry, and this walk reaches it there.
      if (typeof via !== 'object') continue

      const severity = severityOf(via.severity)
      const url = typeof via.url === 'string' ? via.url : ''
      // npm's own numeric key, only where the URL carried no GHSA id. Narrowed rather than
      // stringified from `unknown`: a report that answered with an object there would put
      // `[object Object]` in the list as an advisory nobody can look up.
      const numbered = typeof via.source === 'number' ? String(via.source) : ''
      const id = idIn(url) || numbered
      if (severity === null || id === '' || !atLeast(severity, floor)) continue

      found.set(id, {
        id,
        of: typeof via.dependency === 'string' ? via.dependency : '',
        severity,
        title: typeof via.title === 'string' ? via.title : '',
        url,
      })
    }
  }

  return [...found.values()]
}

/** The advisories nobody has written down a reason for. Empty is a clean run. */
export function unexcused(
  found: readonly Advisory[],
  accepted: readonly Accepted[] = ACCEPTED,
): Advisory[] {
  const excused = new Set(accepted.map((one) => one.id))
  return found.filter((one) => !excused.has(one.id))
}

/** Exceptions the report no longer names — an answer to a question nobody is asking. */
export function outlived(
  found: readonly Advisory[],
  accepted: readonly Accepted[] = ACCEPTED,
): Accepted[] {
  const reported = new Set(found.map((one) => one.id))
  return accepted.filter((one) => !reported.has(one.id))
}
