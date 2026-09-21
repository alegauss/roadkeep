import {
  composeWrite,
  readAnswerFrom,
  readValidatePayload,
  saidPlainly,
  type BridgedResult,
  type Refusal,
  type ValidatePayload,
  type Withholding,
} from '@rk/core'
import { useCallback, useState } from 'react'

import { getBridge } from './bridge'

/**
 * Saying what happened, and sending it through `validate` (RG294).
 *
 * `useFiling`'s shape and its rules, for the other write this window makes: the command is
 * composed from the write table, run as composed, and every way of not landing is a state the
 * screen draws rather than a sentence this app made up.
 *
 * **Nothing here checks the sentence.** The engine holds the limit and refuses far better than
 * a copy of it would, and a refusal comes back as its own document with the field it names —
 * which is RG5 working as it was built to. What this refuses is an empty box, and only because
 * an empty box is a call nobody meant to make.
 *
 * **Nothing here decides the verdict either.** The word is the one a button carried, and the
 * buttons are the set `commands` published (RG294).
 */

/** What sending a verdict did, in the shapes a screen draws differently. */
export type Verdict =
  | { readonly kind: 'none' }
  | { readonly kind: 'sending' }
  /** Written, with what the engine answered — including the verdict it wrote over. */
  | { readonly kind: 'wrote'; readonly written: ValidatePayload }
  /** The engine declined, naming the fields. Nothing was written: that is its promise. */
  | { readonly kind: 'refused'; readonly refusal: Refusal }
  /** It never ran, or was refused before it did. A code the screen looks up where it draws. */
  | { readonly kind: 'failed'; readonly reason: Withholding }
  /** It ran and answered a shape no reader could take, so whether it landed is unknown. */
  | { readonly kind: 'unreadable'; readonly reason: string }

export interface Verdicting {
  readonly verdict: Verdict
  /** Send one, which is the whole of what this hook does. */
  readonly send: (word: string, saw: string) => void
  /** Forget what the last send answered, so reopening the form starts clean. */
  readonly forget: () => void
}

export function useVerdict(root: string, id: string): Verdicting {
  const [verdict, setVerdict] = useState<Verdict>({ kind: 'none' })

  const send = useCallback(
    (word: string, saw: string) => {
      const bridge = getBridge()
      if (bridge === undefined || word === '' || saw.trim() === '') return
      setVerdict({ kind: 'sending' })
      const composed = composeWrite(root, 'validate', { id, verdict: word, saw })
      ran(bridge.run(root, { argv: composed.argv }), setVerdict)
    },
    [root, id],
  )

  const forget = useCallback(() => {
    setVerdict({ kind: 'none' })
  }, [])

  return { verdict, send, forget }
}

/** One write, read into the shapes above — `useFiling`'s reading, against this verb's shape. */
function ran(answering: Promise<BridgedResult>, into: (verdict: Verdict) => void): void {
  void answering.then(
    (answered) => {
      if (answered.kind === 'failed') {
        into({ kind: 'failed', reason: answered })
        return
      }
      let source: unknown
      try {
        source = JSON.parse(answered.result.stdout)
      } catch {
        into({ kind: 'failed', reason: saidPlainly(answered.result.stderr) })
        return
      }
      const read = readAnswerFrom(readValidatePayload, source, '')
      if (!read.ok) {
        into({ kind: 'unreadable', reason: read.failure.path })
        return
      }
      if (read.value.kind === 'refused') {
        into({ kind: 'refused', refusal: read.value.refusal })
        return
      }
      into({ kind: 'wrote', written: read.value.value })
    },
    (cause: unknown) => {
      into({ kind: 'failed', reason: saidPlainly(cause instanceof Error ? cause.message : '') })
    },
  )
}
