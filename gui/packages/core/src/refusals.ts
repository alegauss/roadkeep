import {
  aBoolean,
  anything,
  aString,
  listOf,
  orMissing,
  orNull,
  record,
  type Parsed,
  type Reader,
} from './reading'
import type { EngineResult } from './transport'

/**
 * A refusal, read as data rather than as English.
 *
 * Every write the engine refuses under `--json` answers with a `refused` list, and each
 * entry carries three things this app uses differently: the **field** decides which input
 * is marked, the **code** decides whether there is a door, and the **message** is what a
 * person reads when neither resolves.
 *
 * The rule that matters is what this does *not* do. `said` is the whole refusal as the
 * terminal printed it, written for a reader, and nothing here parses it. The code is the
 * contract and the prose is not — a client that scraped a field name out of a sentence
 * would break on the first release that reworded one, silently, and in the direction where
 * the box that was refused simply stops being marked.
 */

export interface RefusedField {
  /** The contract. `symptom.too-long`, `ref.unresolved` — stable, and what `explain` takes. */
  readonly code: string
  /** Which input was refused, so the screen can mark it. Empty where the refusal is not one field's. */
  readonly field: string
  /** The limit or rule it ran into, where the engine names one. */
  readonly bound: string
  /** Written for a person. Shown, never parsed. */
  readonly message: string
}

export const readRefusedField: Reader<RefusedField> = record<RefusedField>({
  code: aString,
  field: orMissing(aString, ''),
  bound: orMissing(aString, ''),
  message: orMissing(aString, ''),
})

export interface Refusal {
  /** Empty for a refusal that is about no particular field — an id that does not exist. */
  readonly refused: readonly RefusedField[]
  readonly beside: string
  readonly about: string
  /** The whole refusal as prose. The fallback, and the thing never read for meaning. */
  readonly said: string
}

export const readRefusal: Reader<Refusal> = record<Refusal>({
  refused: orMissing(listOf(readRefusedField), []),
  beside: orMissing(aString, ''),
  about: orMissing(aString, ''),
  said: aString,
})

/**
 * A refusal or a payload, told apart by the answer itself.
 *
 * `said` is the discriminator and the exit code is not: `lint` exits 1 with an ordinary
 * payload when it finds something, and reading that as a refusal would turn the gate's own
 * findings into an error nobody could act on.
 */
export type Answer<T> =
  | { readonly kind: 'payload'; readonly value: T }
  | { readonly kind: 'refused'; readonly refusal: Refusal }

/** Read one engine result as either the verb's payload or the refusal it answered with. */
export function readAnswer<T>(
  reader: Reader<T>,
  result: EngineResult,
): Parsed<Answer<T>> {
  let source: unknown
  try {
    source = JSON.parse(result.stdout)
  } catch {
    return {
      ok: false,
      failure: {
        path: '',
        expected: 'JSON',
        got: result.stdout.trim().slice(0, 40) || 'nothing on stdout',
      },
    }
  }

  if (looksRefused(source)) {
    const refusal = readRefusal(source, '')
    return refusal.ok ? { ok: true, value: { kind: 'refused', refusal: refusal.value } } : refusal
  }

  const payload = reader(source, '')
  return payload.ok ? { ok: true, value: { kind: 'payload', value: payload.value } } : payload
}

function looksRefused(source: unknown): boolean {
  if (typeof source !== 'object' || source === null || Array.isArray(source)) return false
  const record_ = source as Record<string, unknown>
  return typeof record_['said'] === 'string' && Array.isArray(record_['refused'])
}

/**
 * Which inputs to mark. Only the fields the engine named — never a name recovered from the
 * prose, which is how a refusal about nothing in particular ends up highlighting a box at
 * random.
 */
export function fieldsRefused(refusal: Refusal): string[] {
  return refusal.refused.map((entry) => entry.field).filter((field) => field !== '')
}

/**
 * A move the engine offers, in its own words.
 *
 * The same shape appears twice: `explain <code> --json` publishes it for a refusal's code,
 * and every `lint` finding carries one under `remedy`. They are read by one reader here on
 * purpose — a refusal and a gate finding are the same thing at two moments, and a screen
 * that handled them separately would offer the door in one place and not the other.
 */
export interface Door {
  /** The command line, already split. Handed to the write path, never to a shell. */
  readonly argv: readonly string[]
  /** What taking it does, written for a person. */
  readonly what: string
  /** False where the caller has to fill something in before it can run. */
  readonly complete: boolean
  /** Whether taking it changes a governed file. */
  readonly writes: boolean
  /** The MCP tool and arguments that are the same move, where the engine names one. */
  readonly call: unknown
}

export const readDoor: Reader<Door> = record<Door>({
  argv: listOf(aString),
  what: orMissing(aString, ''),
  complete: orMissing(aBoolean, false),
  writes: orMissing(aBoolean, false),
  call: orMissing(anything, null),
})

export interface Remedy {
  /** The engine's own word for the kind of move this is: `read`, `compose`, and so on. */
  readonly kind: string
  /** True where the doors are a sequence rather than a choice. */
  readonly sequence: boolean
  /** What a person has to settle before any door helps. Empty for most. */
  readonly decision: string
  /** What this is waiting on, where nothing here can close it yet. */
  readonly awaits: string
  readonly doors: readonly Door[]
}

export const readRemedy: Reader<Remedy> = record<Remedy>({
  kind: orMissing(aString, ''),
  sequence: orMissing(aBoolean, false),
  decision: orMissing(aString, ''),
  awaits: orMissing(aString, ''),
  doors: orMissing(listOf(readDoor), []),
})

/** What `explain <code>` answers: the same doors, plus why the code exists at all. */
export interface Explanation {
  readonly code: string
  readonly kind: string
  readonly cause: string
  /** Present where the same code means different things in different places. */
  readonly varies: string | null
  readonly sequence: boolean
  /** What this code waits on, where no door here closes it. */
  readonly awaits: string
  readonly doors: readonly Door[]
}

export const readExplanation: Reader<Explanation> = record<Explanation>({
  code: aString,
  kind: orMissing(aString, ''),
  cause: orMissing(aString, ''),
  varies: orMissing(orNull(aString), null),
  sequence: orMissing(aBoolean, false),
  awaits: orMissing(aString, ''),
  doors: orMissing(listOf(readDoor), []),
})

/** The doors worth offering: the ones that can run as they stand. */
export function offerable(doors: readonly Door[]): Door[] {
  return doors.filter((door) => door.complete)
}
