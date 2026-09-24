// The generated facts, and the few words that turn a number into prose. The copy imports from
// here and never from product.generated.ts directly, so the one place a figure becomes a word
// is this file.
import { product } from './product.generated'

export { product }

const WORDS = [
  'zero',
  'one',
  'two',
  'three',
  'four',
  'five',
  'six',
  'seven',
  'eight',
  'nine',
  'ten',
  'eleven',
  'twelve',
]

/** A count as a word where a word reads better, and as digits past twelve. */
export function spelled(n: number): string {
  return WORDS[n] ?? String(n)
}

/** The same, capitalised, for the start of a sentence or a heading. */
export function spelledTitle(n: number): string {
  const word = spelled(n)
  return word.charAt(0).toUpperCase() + word.slice(1)
}

/** `a`, `a and b`, `a, b and c`: the conjunction a generated list cannot supply for itself. */
export function joined(items: readonly string[]): string {
  if (items.length <= 1) return items.join('')
  return `${items.slice(0, -1).join(', ')} and ${items[items.length - 1]}`
}

export const readCount = product.reads.length
export const writeCount = product.writes.length
export const nonGoalCount = product.nonGoals.length
