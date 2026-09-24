import {
  actionableFrom,
  actionableReport,
  buildArgv,
  doorsIn,
  UNKNOWN_GATE,
  gatedReport,
  openOver,
  readAnswerFrom,
  readLintPayload,
  saidPlainly,
  type BridgedResult,
  type GateHealth,
  type Gated,
  type HandedOver,
  type LintPayload,
  type OpenProject,
  type Withholding,
} from '@rk/core'
import { useCallback, useEffect, useState } from 'react'

import { getBridge } from './bridge'
import { readDeadline } from './launch'

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
  /**
   * The verdict on record, which the files have not moved under (RG185). Not a report: the
   * ledger holds what the gate said and when, never its findings — a report held in memory
   * and drawn later would be this app answering about files it has not read.
   */
  | { readonly kind: 'held'; readonly health: GateHealth }
  /**
   * A call is out, and when it went (RG262).
   *
   * The moment is carried so the screen can draw how much of the deadline has gone. Taking a
   * door is two calls end to end — the door, then the gate — and each sets its own, so the
   * second is not drawn against time the first spent.
   */
  | { readonly kind: 'running'; readonly since: number }
  | {
      readonly kind: 'read'
      readonly payload: LintPayload
      readonly findings: readonly Gated[]
      readonly notes: readonly Gated[]
      /** What the far side calls this answer's doors, where it kept any. */
      readonly offered: string | null
    }
  /**
   * It never ran, or answered something no reader could take.
   *
   * A refusal and not a sentence: the screen looks the code up when it draws, so a window
   * whose language changes while this is on it says the new one (RG192).
   */
  | { readonly kind: 'failed'; readonly reason: Withholding }
  | { readonly kind: 'unreadable'; readonly reason: string }

/**
 * Whether opening this screen should run the gate (RG185, RG254).
 *
 * **A run says something new, or it does not run.** A verdict nobody has taken, and one the
 * files have moved under, are both answers this screen cannot draw without asking — so it
 * asks. A clean verdict against these files is the whole answer, and running `lint` to
 * redraw it would be the most expensive read there is spent on a sentence already on screen.
 *
 * **A drifted one is not the whole answer.** The ledger holds how many findings there were
 * and never which, so `6 findings when it last ran` is a count with no row, no code and no
 * door — and the rows are what somebody opened the gate to read. Running is what produces
 * them, and the held sentence stays drawn while it does.
 */
export function worthRunning(gate: Gate): boolean {
  if (gate.kind !== 'held') return false
  return gate.health.verdict !== 'clean' || gate.health.stale
}

export interface Gating {
  readonly project: OpenProject | null
  readonly gate: Gate
  /**
   * Why the last door taken did not run, where one did not (RG260).
   *
   * Apart from the gate, because a door and the run that follows it are two answers: the gate
   * is run again whatever the door said — what it wrote is not for this screen to guess — and
   * a report that came back unchanged is exactly what a failed door looks like otherwise.
   */
  readonly refused: Withholding | null
  // Properties and not methods, for the reason `useFiling`'s are: a screen passes them on
  // as callbacks, and a method type says they carry a `this` this hook never gives them.
  readonly run: () => void
  readonly takeDoor: (which: number, words: readonly string[]) => void
  /** Hand a door to a Claude Code session (RG263), named by its place in the batch. */
  readonly handDoor: (which: number) => void
  /** Where that went: a session to open, or why none started. */
  readonly handing: Handing
}

/**
 * Handing a door over, as the screen has to draw it (RG263).
 *
 * A key and not a route, because where a session is shown is the screen's question and not
 * this hook's. `said` carries the answer whole rather than a sentence, so the screen words it
 * the way the task screen already words the same six outcomes.
 */
export type Handing =
  | { readonly kind: 'idle' }
  | { readonly kind: 'handing' }
  | { readonly kind: 'started'; readonly key: string }
  | { readonly kind: 'said'; readonly said: Exclude<HandedOver, { readonly kind: 'started' }> }

export function useGate(root: string): Gating {
  const [project, setProject] = useState<OpenProject | null>(null)
  const [gate, setGate] = useState<Gate>({ kind: 'idle' })
  const [held, setHeld] = useState<GateHealth | null>(null)
  const [refused, setRefused] = useState<Withholding | null>(null)
  const [handing, setHanding] = useState<Handing>({ kind: 'idle' })

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

  // What the ledger already holds for this project (RG185). A read of a record, so it costs
  // nothing, and it is what decides whether the screen opens on a run or on an answer.
  useEffect(() => {
    const bridge = getBridge()
    if (bridge === undefined) return undefined
    let live = true
    const stillHere = (): boolean => live
    void bridge.gates().then(
      (all) => {
        if (!stillHere()) return
        setHeld(all.find((one) => one.root === root)?.health ?? UNKNOWN_GATE)
      },
      // A carrier that will not say leaves this unknown, which is what makes the screen run.
      () => {
        if (stillHere()) setHeld(UNKNOWN_GATE)
      },
    )
    return () => {
      live = false
    }
  }, [root])

  /** One answer, read into the shapes above. The same path for a run and for a door. */
  const ran = useCallback((answering: Promise<BridgedResult>) => {
    setGate({ kind: 'running', since: Date.now() })
    void answering.then(
      (answered) => {
        if (answered.kind === 'failed') {
          setGate({ kind: 'failed', reason: answered })
          return
        }
        let source: unknown
        try {
          source = JSON.parse(answered.result.stdout)
        } catch {
          setGate({ kind: 'failed', reason: saidPlainly(answered.result.stderr) })
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
          setGate({ kind: 'failed', reason: saidPlainly(read.value.refusal.said) })
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
        setGate({
          kind: 'failed',
          reason: saidPlainly(cause instanceof Error ? cause.message : ''),
        })
      },
    )
  }, [])

  // The verdict on record, until a run replaces it. A person pressing Run the gate is a
  // person saying they want it run whatever the ledger holds, so this only ever fills the
  // opening state.
  useEffect(() => {
    if (held === null) return
    setGate((was) => (was.kind === 'idle' ? { kind: 'held', health: held } : was))
  }, [held])

  /**
   * Run the gate, carrying what the door before it refused (RG260).
   *
   * **Bounded by the declared deadline**, like every other read this window waits on. The
   * request names no tool, so it takes the held engine's fallback and is spawned — where an
   * absent `timeoutMs` is no ceiling at all, and `running` has nothing under it.
   */
  const rerun = useCallback(
    (after: Withholding | null) => {
      const bridge = getBridge()
      if (bridge === undefined) return
      setRefused(after)
      ran(bridge.run(root, { argv: buildArgv(root, 'lint', {}), timeoutMs: readDeadline() }))
    },
    [root, ran],
  )

  // Taking no argument on purpose: a screen hands this to `onClick`, which would call it with
  // the event, and a refusal the reader never saw would be drawn over the run they asked for.
  const run = useCallback(() => {
    rerun(null)
  }, [rerun])

  const takeDoor = useCallback(
    (which: number, words: readonly string[]) => {
      const bridge = getBridge()
      const offered = gate.kind === 'read' ? gate.offered : null
      if (bridge === undefined || offered === null) return
      // What a door answers is not a report, so the gate is what this waits for: the row
      // goes when the finding does, and nothing here decides that it did. The door's own
      // refusal is carried into that run, since a fix that never ran and a fix that found
      // nothing to do leave the same report behind.
      void bridge.door(root, offered, which, words).then(
        (answered) => {
          rerun(answered.kind === 'failed' ? answered : null)
        },
        (cause: unknown) => {
          rerun(saidPlainly(cause instanceof Error ? cause.message : ''))
        },
      )
      setGate({ kind: 'running', since: Date.now() })
    },
    [root, gate, rerun],
  )

  const handDoor = useCallback(
    (which: number) => {
      const bridge = getBridge()
      const offered = gate.kind === 'read' ? gate.offered : null
      if (bridge === undefined || offered === null) return
      setHanding({ kind: 'handing' })
      // The gate is not run again here, and the finding stays where it is: whether a session
      // closed it is a question only a run answers, and this one has not started yet.
      void bridge.handOverDoor(root, offered, which).then(
        (handed) => {
          setHanding(
            handed.kind === 'started'
              ? { kind: 'started', key: handed.session.key }
              : { kind: 'said', said: handed },
          )
        },
        (cause: unknown) => {
          setHanding({
            kind: 'said',
            said: { kind: 'withheld', reason: cause instanceof Error ? cause.message : '' },
          })
        },
      )
    },
    [root, gate],
  )

  return { project, gate, refused, run, takeDoor, handDoor, handing }
}
