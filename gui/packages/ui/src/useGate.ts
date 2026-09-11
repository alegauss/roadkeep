import {
  actionableFrom,
  actionableReport,
  buildArgv,
  doorsIn,
  gatedReport,
  openOver,
  readAnswerFrom,
  readLintPayload,
  type BridgedResult,
  type Gated,
  type LintPayload,
  type OpenProject,
} from '@rk/core'
import { useCallback, useEffect, useState } from 'react'

import { getBridge } from './bridge'

/**
 * Running the gate from the window (RG152).
 *
 * **`lint` is a read like any other**, composed by the read table and run through `run`, so
 * the carrier dates its ledger off the same answer this screen draws (RG152) and no second
 * run is needed to keep the portfolio's column honest.
 *
 * **A finding's doors are the engine's**, and they are taken by the place they hold in the
 * batch the carrier kept — which is `doorsIn`'s order over the whole answer, not the order a
 * screen groups them in. `gatedReport` is what matches the two, so a note carrying doors
 * ahead of the findings cannot shift what a button runs.
 *
 * **A door that ran means the report is old**, so the gate runs again after one is taken. The
 * row goes when the finding does, which is the only way a screen can say a finding is closed
 * without deciding for itself that it is.
 */

export type Gate =
  | { readonly kind: 'idle' }
  | { readonly kind: 'running' }
  | {
      readonly kind: 'read'
      readonly payload: LintPayload
      readonly findings: readonly Gated[]
      readonly notes: readonly Gated[]
      /** What the far side calls this answer's doors, where it kept any. */
      readonly offered: string | null
    }
  /** It never ran, or answered something no reader could take. */
  | { readonly kind: 'failed'; readonly reason: string }
  | { readonly kind: 'unreadable'; readonly reason: string }

export interface Gating {
  readonly project: OpenProject | null
  readonly gate: Gate
  // Properties and not methods, for the reason `useFiling`'s are: a screen passes them on
  // as callbacks, and a method type says they carry a `this` this hook never gives them.
  readonly run: () => void
  readonly takeDoor: (which: number, words: readonly string[]) => void
}

export function useGate(root: string): Gating {
  const [project, setProject] = useState<OpenProject | null>(null)
  const [gate, setGate] = useState<Gate>({ kind: 'idle' })

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

  /** One answer, read into the shapes above. The same path for a run and for a door. */
  const ran = useCallback((answering: Promise<BridgedResult>) => {
    setGate({ kind: 'running' })
    void answering.then(
      (answered) => {
        if (answered.kind === 'failed') {
          setGate({ kind: 'failed', reason: answered.message })
          return
        }
        let source: unknown
        try {
          source = JSON.parse(answered.result.stdout)
        } catch {
          setGate({ kind: 'failed', reason: answered.result.stderr })
          return
        }
        // A gate that found something exits non-zero and is still an answer, which is the
        // whole point of it — so the report is read before the code is looked at.
        const read = readAnswerFrom(readLintPayload, source, '')
        if (!read.ok) {
          setGate({ kind: 'unreadable', reason: read.failure.path })
          return
        }
        if (read.value.kind === 'refused') {
          setGate({ kind: 'failed', reason: read.value.refusal.said })
          return
        }
        const payload = read.value.value
        const batch = doorsIn(source)
        setGate({
          kind: 'read',
          payload,
          findings: gatedReport(actionableReport(payload), batch),
          notes: gatedReport(payload.notes.map(actionableFrom), batch),
          offered: answered.offered ?? null,
        })
      },
      (cause: unknown) => {
        setGate({ kind: 'failed', reason: cause instanceof Error ? cause.message : '' })
      },
    )
  }, [])

  const run = useCallback(() => {
    const bridge = getBridge()
    if (bridge === undefined) return
    ran(bridge.run(root, { argv: buildArgv(root, 'lint', {}) }))
  }, [root, ran])

  const takeDoor = useCallback(
    (which: number, words: readonly string[]) => {
      const bridge = getBridge()
      const offered = gate.kind === 'read' ? gate.offered : null
      if (bridge === undefined || offered === null) return
      // What a door answers is not a report, so the gate is what this waits for: the row
      // goes when the finding does, and nothing here decides that it did.
      void bridge.door(root, offered, which, words).then(
        () => {
          run()
        },
        () => {
          run()
        },
      )
      setGate({ kind: 'running' })
    },
    [root, gate, run],
  )

  return { project, gate, run, takeDoor }
}
