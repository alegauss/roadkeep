/**
 * The boundary every payload crosses, and the only place an `unknown` becomes a type.
 *
 * A payload is JSON with no published schema, produced by a build this app did not
 * choose. Read as `any` it becomes a runtime `undefined` on the day a key is renamed — on
 * somebody's machine, in the one place nobody is watching. So each read declares a shape,
 * and a shape either yields the typed value or a failure that says which field and what
 * was there instead.
 *
 * Hand-written combinators rather than a schema library, for one reason that matters:
 * `core` is the half a web service keeps, and a dependency here is a dependency there. The
 * whole toolkit is below and it is smaller than the package that would replace it.
 *
 * Two rules shape it. **Extra keys are always allowed** — the payloads carry far more than
 * this app reads, and a reader that refused unknown fields would break on every release
 * that added one. **A declared field is strict**, because that is the entire point: what
 * this app says it reads is what it must actually get.
 */

export interface PayloadFailure {
  /** Where it went wrong, in the payload's own terms: `tasks[3].symptom`. */
  readonly path: string
  /** What the shape asked for. */
  readonly expected: string
  /** What was there instead, short enough to put in a sentence. */
  readonly got: string
}

export type Parsed<T> =
  | { readonly ok: true; readonly value: T }
  | { readonly ok: false; readonly failure: PayloadFailure }

export type Reader<T> = (value: unknown, path: string) => Parsed<T>

/**
 * A value as a record of unknown fields, or null where it is not one (RG121).
 *
 * The check every reader begins with, written once. Four files had their own copy of it —
 * two identical `asRecord` functions and two inline pairs of the same two lines — and each
 * carried the same assertion, which is the shape this module exists to hold: the type is
 * asserted immediately after being proved, in view of the proof.
 *
 * An array is not a record here. It is an object to `typeof` and never what a caller
 * asking for named fields means, and every copy this replaced excluded it.
 */
export function asRecord(value: unknown): Record<string, unknown> | null {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null
}

/**
 * The keys of a table, typed as that table's own (RG121).
 *
 * `Object.keys` answers `string[]`, and it has to: a value that crossed a wire may carry
 * keys its type never mentioned. A table written in this repository beside the type that
 * names it is the case where that cannot happen, and eight call sites were each asserting
 * so on their own line. Asserted once here instead, where the reason is written down.
 *
 * Not for a payload. `record` reads those, field by field, and a key list taken off one
 * would be a claim about somebody else's build.
 */
export function keysOf<T extends object>(table: T): (keyof T & string)[] {
  return Object.keys(table) as (keyof T & string)[]
}

/**
 * A table with one entry for every key given, each made by a function of its key (RG129).
 *
 * `keysOf` run the other way, and here for the same reason. `Object.fromEntries` answers
 * `{ [k: string]: V }` because it cannot know which keys it was handed; a caller mapping a
 * closed list of them knows the table holds exactly those, and was saying so by starting an
 * accumulator as `{}` asserted to be the finished record. The claim is made once, here,
 * beside what proves it — every key in `keys` was given a value on the line above.
 */
export function tableOf<K extends string, V>(
  keys: readonly K[],
  valueOf: (key: K) => V,
): Record<K, V> {
  return Object.fromEntries(keys.map((key) => [key, valueOf(key)])) as Record<K, V>
}

const ok = <T>(value: T): Parsed<T> => ({ ok: true, value })

function fail(path: string, expected: string, value: unknown): Parsed<never> {
  return { ok: false, failure: { path, expected, got: describe(value) } }
}

/** What was there, in a few words. Never the whole payload: this ends up in a sentence. */
export function describe(value: unknown): string {
  if (value === null) return 'null'
  if (Array.isArray(value)) return `an array of ${String(value.length)}`
  if (value === undefined) return 'nothing'
  if (typeof value === 'string') {
    return value.length > 30
      ? `the string ${JSON.stringify(value.slice(0, 30))}…`
      : JSON.stringify(value)
  }
  // Only the three that stringify to something a reader can use are stringified. `String`
  // over a wider type is how `[object Object]` reaches a sentence meant to say what was
  // there, which is the one answer this function must never give (RG94).
  if (typeof value === 'number' || typeof value === 'boolean' || typeof value === 'bigint') {
    return `${typeof value} ${String(value)}`
  }
  if (typeof value === 'function') return 'a function'
  if (typeof value === 'symbol') return 'a symbol'
  return 'an object'
}

export const aString: Reader<string> = (value, path) =>
  typeof value === 'string' ? ok(value) : fail(path, 'a string', value)

export const aNumber: Reader<number> = (value, path) =>
  typeof value === 'number' && Number.isFinite(value) ? ok(value) : fail(path, 'a number', value)

export const aBoolean: Reader<boolean> = (value, path) =>
  typeof value === 'boolean' ? ok(value) : fail(path, 'a boolean', value)

/** Anything at all, kept as `unknown`. For a field this app carries but does not read into. */
export const anything: Reader<unknown> = (value) => ok(value)

/** `true` and nothing else: the flag a second shape of one verb's answer is told apart by. */
export const literalTrue: Reader<true> = (value, path) =>
  value === true ? ok(true) : fail(path, 'true', value)

/**
 * One of two shapes, chosen by a flag the payload carries (RG142).
 *
 * Chosen and not tried: reading the second shape after the first failed would report the
 * second's failure for a payload that was the first shape with one field wrong, which is the
 * sentence that sends somebody to the wrong half. The engine says which shape it printed, so
 * that is what decides.
 */
export function whenFlagged<A, B>(
  flag: string,
  flagged: Reader<A>,
  otherwise: Reader<B>,
): Reader<A | B> {
  return (value, path) =>
    asRecord(value)?.[flag] === true ? flagged(value, path) : otherwise(value, path)
}

/**
 * `null` or the value. This is the default reading rather than the exception: `standing`,
 * `over`, `picked` and `section` all come back null in ordinary answers.
 */
export function orNull<T>(reader: Reader<T>): Reader<T | null> {
  return (value, path) => (value === null ? ok(null) : reader(value, path))
}

/** A key that may be absent entirely, which is not the same as one that is null. */
export function orMissing<T>(reader: Reader<T>, fallback: T): Reader<T> {
  return (value, path) => (value === undefined ? ok(fallback) : reader(value, path))
}

/**
 * A value that is either one thing or a list of them (RG179).
 *
 * The engine answers a field's previous value in the shape that field has: a string for a
 * string field, a list for a list one. A reader declaring only the first refused an answer
 * the engine was right to give — and joining the list here would be this app composing a
 * field, so both shapes come through as they arrived and a screen that wants one line joins
 * what it draws.
 *
 * The list is tried first: an array is never a string, so the order costs nothing and the
 * failure a caller sees names the shape it actually sent.
 */
export function oneOrMany<T>(reader: Reader<T>): Reader<T | readonly T[]> {
  return (value, path) => (Array.isArray(value) ? listOf(reader)(value, path) : reader(value, path))
}

export function listOf<T>(reader: Reader<T>): Reader<T[]> {
  return (value, path) => {
    if (!Array.isArray(value)) return fail(path, 'an array', value)
    const values: T[] = []
    for (const [index, element] of value.entries()) {
      const parsed = reader(element, `${path}[${String(index)}]`)
      if (!parsed.ok) return parsed
      values.push(parsed.value)
    }
    return ok(values)
  }
}

/**
 * An object whose keys are data rather than structure — `markers`, which is keyed by the
 * marker set a project declares and so cannot be written down here.
 */
export function dictionaryOf<T>(reader: Reader<T>): Reader<Record<string, T>> {
  return (value, path) => {
    if (typeof value !== 'object' || value === null || Array.isArray(value)) {
      return fail(path, 'an object', value)
    }
    const built: Record<string, T> = {}
    for (const [key, element] of Object.entries(value as Record<string, unknown>)) {
      const parsed = reader(element, `${path}.${key}`)
      if (!parsed.ok) return parsed
      built[key] = parsed.value
    }
    return ok(built)
  }
}

type Shape<T> = { [K in keyof T]-?: Reader<T[K]> }

/**
 * Read the declared fields of an object and ignore every other key it carries.
 *
 * `sourceKeys` renames: the payloads are snake_case and this app is not, and the failure
 * path stays the payload's spelling so a message names the key somebody can go and find.
 */
export function record<T>(
  shape: Shape<T>,
  sourceKeys: Partial<Record<keyof T & string, string>> = {},
): Reader<T> {
  return (value, path) => {
    if (typeof value !== 'object' || value === null || Array.isArray(value)) {
      return fail(path, 'an object', value)
    }
    const source = value as Record<string, unknown>
    const built: Partial<T> = {}
    for (const key of keysOf(shape)) {
      const from = sourceKeys[key] ?? key
      const parsed = shape[key](source[from], path === '' ? from : `${path}.${from}`)
      if (!parsed.ok) return parsed
      built[key] = parsed.value
    }
    return ok(built as T)
  }
}

/**
 * Read one payload out of a command's stdout.
 *
 * A refusal names the field and the engine that answered, because the useful sentence is
 * *this app is behind the roadkeep answering here* and not a stack trace. The version
 * comes from `engines`, which is why resolving one happens before anything else is read.
 */
export function readPayload<T>(
  reader: Reader<T>,
  stdout: string,
  where: { readonly verb: string; readonly engineVersion: string },
): Parsed<T> {
  let source: unknown
  try {
    source = JSON.parse(stdout)
  } catch {
    return fail(where.verb, 'JSON', stdout.trim().slice(0, 40))
  }
  return reader(source, '')
}
