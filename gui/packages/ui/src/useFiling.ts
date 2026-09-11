import {
  boundsFrom,
  composeWrite,
  doorsIn,
  openOver,
  readAddedPayload,
  readAnswerFrom,
  type AddedPayload,
  type BridgedResult,
  type Bounds,
  type BudgetPayload,
  type Composed,
  type DeliveredPayload,
  type Door,
  type OpenProject,
  type Refusal,
  type WriteInputs,
} from '@rk/core'
import { useCallback, useEffect, useState } from 'react'

import { getBridge } from './bridge'

/**
 * Filing one line from the window (RG151).
 *
 * **The draft is the app's; every number about it is the engine's.** What a field has left
 * comes from `budget`, asked again whenever the draft moves — the allowance depends on the
 * rendered line, so adding a dep takes room from the sentence, and a counter this app worked
 * out would be a second implementation of the limit. The asking is spaced out rather than made
 * per keystroke, which the held engine makes cheap enough to do at all.
 *
 * **The command is composed once and shown before it runs.** `composeWrite` builds it from the
 * write table, the screen draws that argv, and filing is the same argv run — so what a person
 * reviewed is what happened.
 *
 * **A refusal is an answer.** It comes back as the engine's own document, with the fields it
 * names and the doors it offers, and the doors are taken by name through the bridge (RG165)
 * rather than by this screen building a second command line.
 */

/** What a person typed. Nothing here is validated: the engine refuses far better. */
export interface Draft {
  readonly block: string
  readonly status: string
  readonly deps: readonly string[]
  readonly symptom: string
  readonly why: string
  readonly section: string
  readonly sectionBody: string
}

export const EMPTY_DRAFT: Draft = {
  block: '',
  status: '',
  deps: [],
  symptom: '',
  why: '',
  section: '',
  sectionBody: '',
}

/** What came back from filing, in the shapes a screen draws differently. */
export type Filed =
  | { readonly kind: 'none' }
  | { readonly kind: 'filing' }
  | { readonly kind: 'wrote'; readonly added: AddedPayload }
  /** The engine refused, with the fields it named and whatever doors it offered. */
  | {
      readonly kind: 'refused'
      readonly refusal: Refusal
      readonly doors: readonly Door[]
      /** What the far side calls those doors, where it kept any. */
      readonly offered: string | null
    }
  /** It never ran, or answered something no reader could take. */
  | { readonly kind: 'failed'; readonly reason: string }

export interface Filing {
  readonly project: OpenProject | null
  /**
   * What this block already delivered, nearest the symptom being written (RG182).
   *
   * Null until a block is typed: the ranking is one block's, so there is nothing to rank
   * against until the form's first field says which. Nothing is refused by it and nothing
   * could be — `delivered` publishes no score, because no threshold separates a true
   * duplicate from a stranger — so it is a list to read and the judgement stays with the
   * person reading it.
   */
  readonly near: DeliveredPayload | null
  /** What `budget` says this draft leaves, or null before the first answer lands. */
  readonly budget: BudgetPayload | null
  /** The constraints a line here is bound by, read once. */
  readonly bounds: Bounds | null
  /** The command this draft would run, composed from the write table. */
  readonly command: Composed
  readonly filed: Filed
  // Both are properties rather than methods: a screen passes them on as callbacks, and a
  // method type says they carry a `this` that this hook never gives them.
  readonly file: () => void
  readonly takeDoor: (which: number, words: readonly string[]) => void
}

/** The write this screen composes, which is one `add` with its section in the same call. */
function asWrite(draft: Draft): WriteInputs['add'] {
  return {
    block: draft.block,
    symptom: draft.symptom,
    why: draft.why,
    ...(draft.status === '' ? {} : { status: draft.status }),
    ...(draft.deps.length === 0 ? {} : { deps: draft.deps }),
    ...(draft.section === '' ? {} : { section: draft.section }),
    ...(draft.sectionBody === '' ? {} : { sectionBody: draft.sectionBody }),
  }
}

/** How long a draft rests before the engine is asked what it leaves. */
const SETTLES_MS = 350

export function useFiling(root: string, draft: Draft): Filing {
  const [project, setProject] = useState<OpenProject | null>(null)
  const [budget, setBudget] = useState<BudgetPayload | null>(null)
  const [bounds, setBounds] = useState<Bounds | null>(null)
  const [near, setNear] = useState<DeliveredPayload | null>(null)
  const [filed, setFiled] = useState<Filed>({ kind: 'none' })

  const command = composeWrite(root, 'add', asWrite(draft))

  useEffect(() => {
    const bridge = getBridge()
    if (bridge === undefined) return undefined
    let live = true
    const stillHere = (): boolean => live
    void openOver(bridge, root).then((reached) => {
      if (stillHere() && reached.kind === 'open') setProject(reached.project)
    })
    return () => {
      live = false
    }
  }, [root])

  // What binds a line here, which does not change while this screen is open.
  useEffect(() => {
    if (project === null) return undefined
    let live = true
    const stillHere = (): boolean => live
    void project.client.call(root, 'nonGoalList', {}).then((outcome) => {
      if (stillHere() && outcome.kind === 'read') setBounds(boundsFrom(outcome.value))
    })
    return () => {
      live = false
    }
  }, [project, root])

  // And what the draft leaves, asked again each time it settles: the allowance moves with
  // the deps and the marker, so a number held from an earlier shape is a number about
  // another line. The draft is the dependency itself — one object per change, so a render
  // caused by anything else here does not re-ask a question already answered.
  useEffect(() => {
    if (project === null) return undefined
    let live = true
    const stillHere = (): boolean => live
    const asking = setTimeout(() => {
      void project.client
        .call(root, 'budget', {
          ...(draft.block === '' ? {} : { block: draft.block }),
          ...(draft.status === '' ? {} : { status: draft.status }),
          ...(draft.deps.length === 0 ? {} : { deps: draft.deps }),
          symptom: draft.symptom,
          why: draft.why,
          ...(draft.sectionBody === '' ? {} : { body: draft.sectionBody }),
        })
        .then((outcome) => {
          if (stillHere() && outcome.kind === 'read') setBudget(outcome.value)
        })
    }, SETTLES_MS)

    return () => {
      live = false
      clearTimeout(asking)
    }
  }, [project, root, draft])

  // And what this block already delivered, nearest what is being written (RG182). Asked on
  // the same settle as the budget, since it is the same draft moving, and only where a block
  // has been named: the ranking is one block's corpus and nothing else.
  useEffect(() => {
    if (project === null || draft.block === '' || draft.symptom === '') {
      setNear(null)
      return undefined
    }
    let live = true
    const stillHere = (): boolean => live
    const asking = setTimeout(() => {
      void project.client
        .call(root, 'delivered', { block: draft.block, near: draft.symptom, open: true })
        .then((outcome) => {
          if (stillHere() && outcome.kind === 'read') setNear(outcome.value)
        })
    }, SETTLES_MS)

    return () => {
      live = false
      clearTimeout(asking)
    }
  }, [project, root, draft.block, draft.symptom])

  /** One write, read into the shapes above. The same path for the line and for a door. */
  const ran = useCallback((answering: Promise<BridgedResult>) => {
    setFiled({ kind: 'filing' })
    void answering.then(
      (answered) => {
        if (answered.kind === 'failed') {
          setFiled({ kind: 'failed', reason: answered.message })
          return
        }
        let source: unknown
        try {
          source = JSON.parse(answered.result.stdout)
        } catch {
          setFiled({ kind: 'failed', reason: answered.result.stderr })
          return
        }
        const read = readAnswerFrom(readAddedPayload, source, '')
        if (!read.ok) {
          setFiled({ kind: 'failed', reason: read.failure.path })
          return
        }
        if (read.value.kind === 'refused') {
          setFiled({
            kind: 'refused',
            refusal: read.value.refusal,
            doors: doorsIn(source),
            offered: answered.offered ?? null,
          })
          return
        }
        setFiled({ kind: 'wrote', added: read.value.value })
      },
      (cause: unknown) => {
        setFiled({ kind: 'failed', reason: cause instanceof Error ? cause.message : '' })
      },
    )
  }, [])

  const file = useCallback(() => {
    const bridge = getBridge()
    if (bridge === undefined) return
    // The argv the screen drew, run as it was drawn.
    ran(bridge.run(root, { argv: composeWrite(root, 'add', asWrite(draft)).argv }))
  }, [root, draft, ran])

  const takeDoor = useCallback(
    (which: number, words: readonly string[]) => {
      const bridge = getBridge()
      const offered = filed.kind === 'refused' ? filed.offered : null
      if (bridge === undefined || offered === null) return
      ran(bridge.door(root, offered, which, words))
    },
    [root, filed, ran],
  )

  return { project, budget, bounds, near, command, filed, file, takeDoor }
}
