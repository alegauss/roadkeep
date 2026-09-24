import { readExplanation, type Explanation, type OpenProject } from '@rk/core'
import { useCallback, useRef, useState } from 'react'

/**
 * What a finding's code means, asked of `explain` when somebody opens one (RG258).
 *
 * **Once per code per screen.** A report of six findings over three codes costs at most three
 * reads, and only for the codes a person opened: a code is a class, its explanation does not
 * change while a screen is up, and asking again per row would be six processes for three
 * answers.
 *
 * **Asked and never composed.** What comes back is the engine's own prose, drawn untranslated
 * as every payload's is — this app has no table of what a code means, and one written here
 * would be the rule compiled into the client that the non-goals refuse.
 */
export type Explained =
  | { readonly kind: 'asking' }
  | { readonly kind: 'read'; readonly explanation: Explanation }
  /** The read did not come back. The pill stays, and the row says nothing it cannot say. */
  | { readonly kind: 'failed' }

export interface Explaining {
  /** What is known about each code asked about so far. */
  readonly explained: ReadonlyMap<string, Explained>
  /** Ask about one code, unless it has been asked about already. */
  explain(code: string): void
}

export function useExplained(root: string, project: OpenProject | null): Explaining {
  const [explained, setExplained] = useState<ReadonlyMap<string, Explained>>(new Map())
  // What has been asked, apart from what has answered: two rows opened in the same frame
  // would otherwise both see an empty map and both spawn a process.
  const asked = useRef(new Set<string>())

  const explain = useCallback(
    (code: string) => {
      if (project === null || asked.current.has(code)) return
      asked.current.add(code)
      setExplained((was) => new Map(was).set(code, { kind: 'asking' }))

      void project.client.call(root, 'explain', { code }).then(
        (outcome) => {
          const parsed = outcome.kind === 'read' ? readExplanation(outcome.value, '') : null
          setExplained((was) =>
            new Map(was).set(
              code,
              parsed?.ok === true
                ? { kind: 'read', explanation: parsed.value }
                : { kind: 'failed' },
            ),
          )
        },
        () => {
          setExplained((was) => new Map(was).set(code, { kind: 'failed' }))
        },
      )
    },
    [project, root],
  )

  return { explained, explain }
}
