import type { LintFinding, LintPayload, RepairLeft, RepairPayload } from './payloads'
import type { Door, Remedy } from './refusals'

/**
 * A finding that can be run.
 *
 * Every gate finding carries a code, a file and line, and the argv that closes it;
 * `explain` says what a code means and which doors it has; `repair` spends a whole report
 * in one call and will do it dry first. All of it is data already, and this is the
 * translation into something a screen can offer.
 *
 * **It decides nothing.** `complete` is the engine's word and it is what sorts a door: a
 * complete one runs as it stands, an incomplete one is a form with blanks a person fills.
 * Which slots are blank comes off the placeholder the door writes, and that is a rendering
 * aid only — `complete` stays the authority, so a changed sentinel costs the highlighting
 * and never turns a form into a command.
 *
 * **A door's argv is the engine's.** `composeDoor` adds where to run it and nothing else.
 * Nothing here works out what the fix should be.
 */

/**
 * The character a door puts where the caller has to supply something.
 *
 * A sentinel in a structured field rather than prose, and deliberately not load-bearing:
 * it is read to highlight the blanks, and `complete` is what decides whether a door may be
 * run at all. If the engine ever spells it differently the highlighting goes and the
 * sorting does not.
 */
const BLANK = '…'

/** What a screen can do with one door. */
export type Offer =
  /** Runs as it stands. The engine said so. */
  | { readonly kind: 'run'; readonly door: Door }
  /** Needs something typed first, at the argv positions named. */
  | { readonly kind: 'fill'; readonly door: Door; readonly blanks: readonly number[] }

/**
 * Sort one door, on the engine's word and not on the placeholders.
 *
 * The blanks are found either way, because a complete door with a stray sentinel in a
 * value is still complete and a screen should not go looking for a form.
 */
export function offerOf(door: Door): Offer {
  if (door.complete) return { kind: 'run', door }
  const blanks = door.argv.flatMap((part, index) => (part === BLANK ? [index] : []))
  return { kind: 'fill', door, blanks }
}

export interface Actionable {
  readonly code: string
  /** Where it is, as the answer addressed it: a file and line, or a joined place. */
  readonly where: string
  readonly message: string
  /** The id the finding is about, where it is about one. */
  readonly id: string
  /** What a person has to settle before any door helps. Empty for most. */
  readonly decision: string
  /** What this waits on, where nothing offered here closes it. */
  readonly awaits: string
  /** True where the doors are a sequence rather than a choice — order matters then. */
  readonly sequence: boolean
  readonly offers: readonly Offer[]
}

function offersOf(remedy: Remedy | null): Offer[] {
  return (remedy?.doors ?? []).map(offerOf)
}

/** Where a lint finding is, spelled the way a repair pass already spells it. */
function placeOf(finding: LintFinding): string {
  if (finding.file === '') return ''
  return finding.line === null ? finding.file : `${finding.file}:${String(finding.line)}`
}

export function actionableFrom(finding: LintFinding): Actionable {
  return {
    code: finding.code,
    where: placeOf(finding),
    message: finding.message,
    id: finding.id ?? '',
    decision: finding.remedy?.decision ?? '',
    awaits: finding.remedy?.awaits ?? '',
    sequence: finding.remedy?.sequence ?? false,
    offers: offersOf(finding.remedy),
  }
}

/**
 * The same, for what a repair pass could not close.
 *
 * One shape over both because a finding and what is left after a repair are the same thing
 * at two moments — a screen that handled them separately would offer the door in one place
 * and not the other.
 */
export function actionableLeft(left: RepairLeft): Actionable {
  return {
    code: left.code,
    where: left.where,
    message: left.message,
    id: '',
    decision: left.remedy?.decision ?? '',
    awaits: left.remedy?.awaits ?? '',
    sequence: left.remedy?.sequence ?? false,
    offers: offersOf(left.remedy),
  }
}

export function actionableReport(payload: LintPayload): Actionable[] {
  return payload.findings.map(actionableFrom)
}

/**
 * Whether anything in a report can be closed without somebody typing first.
 *
 * What a screen needs before offering a repair pass at all: a report whose every finding
 * wants prose is one the pass cannot advance, and offering it would spend a confirmation
 * on nothing.
 */
export function anyRunnable(report: readonly Actionable[]): boolean {
  return report.some((one) => one.offers.some((offer) => offer.kind === 'run'))
}

export interface Pass {
  /** Whether it printed the commands and ran none of them. */
  readonly dry: boolean
  readonly clean: boolean
  readonly passes: number
  /** The passes stopped because they stopped helping, not because the files are clean. */
  readonly exhausted: boolean
  /** What it did, or would do. */
  readonly steps: RepairPayload['steps']
  /** What it could not close, ready to offer. */
  readonly left: readonly Actionable[]
}

export function passFrom(payload: RepairPayload): Pass {
  return {
    dry: payload.dryRun,
    clean: payload.clean,
    passes: payload.passes,
    exhausted: payload.exhausted,
    steps: payload.steps,
    left: payload.left.map(actionableLeft),
  }
}

/**
 * What the pass did, in one line.
 *
 * A dry run says so first, because the difference between "would run" and "ran" is the
 * whole reason it is offered dry.
 */
export function saidOfPass(pass: Pass): string {
  const what = `${String(pass.steps.length)} step(s), ${String(pass.left.length)} left`
  if (pass.dry) return `dry run: ${what}`
  if (pass.clean) return `${what} — clean`
  return pass.exhausted ? `${what} — the passes stopped helping` : what
}
