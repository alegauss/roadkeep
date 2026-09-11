import {
  lineOf,
  marksOf,
  NOTHING_MARKED,
  openOver,
  type Marks,
  type OpenProject,
  type Reading,
  type SessionOutcome,
  type SessionRecord,
} from '@rk/core'
import { useEffect, useRef, useState } from 'react'

import { getBridge } from './bridge'
import { useGovernedMoves } from './following'

export type SessionView =
  | { readonly kind: 'absent' }
  | { readonly kind: 'opening' }
  /** This window holds no session by that key: another launch's, or a mistyped route. */
  | { readonly kind: 'missing' }
  | {
      readonly kind: 'open'
      readonly record: SessionRecord
      /** Every line so far, what `sessions` answered and what was heard since, put together. */
      readonly lines: readonly string[]
      readonly outcome: SessionOutcome | null
      /** What the project counts as its own, once it opened: nothing marked until then. */
      readonly marks: Marks
      /** The line as the engine answers it now, or null before the first reread lands. */
      readonly now: Reading | null
    }

/** What was heard on the session's topic, kept apart from the record until both are here. */
interface Heard {
  readonly lines: readonly string[]
  readonly outcome: SessionOutcome | null
}

const NOTHING_HEARD: Heard = { lines: [], outcome: null }

/**
 * A line in its place, whichever of the record and the topic brought it first.
 *
 * A place nothing has reached yet is empty rather than absent: a hole in the array is an
 * `undefined` where every reader expects a line, and a line that arrives out of order is
 * enough to make one.
 */
function placed(lines: readonly string[], index: number, line: string): string[] {
  const next = [...lines]
  while (next.length < index) next.push('')
  next[index] = line
  return next
}

/** The record's lines under what was heard, which is never behind it. */
function together(record: readonly string[], heard: readonly string[]): string[] {
  let lines = [...record]
  heard.forEach((line, index) => {
    if (line !== '') lines = placed(lines, index, line)
  })
  return lines
}

/**
 * One session this window started, as it runs (RG153).
 *
 * **Heard first, then asked.** The topic is subscribed before `sessions` is asked for the lines
 * so far, and every line carries its place in the stream, so a line written between the two is
 * in one or the other and in its place in both. The ending arrives the same way.
 *
 * **What moved is read, not heard.** The session says what it did and the files say what is
 * true, so on every move of the governed files the line is briefed again and a screen compares
 * that with the brief the session was handed (`landingBetween`). A line that stopped briefing
 * is an answer too: the refusal says where it went.
 */
export function useSession(root: string, id: string, key: string): SessionView {
  const [record, setRecord] = useState<SessionRecord | null | undefined>(undefined)
  const [heard, setHeard] = useState<Heard>(NOTHING_HEARD)
  const [project, setProject] = useState<OpenProject | null>(null)
  const [now, setNow] = useState<Reading | null>(null)
  // The read for the line on screen, swapped with it: a move asks whichever one is current.
  const reread = useRef<() => void>(() => undefined)
  useGovernedMoves(project === null ? null : root, () => {
    reread.current()
  })

  useEffect(() => {
    const bridge = getBridge()
    if (bridge === undefined) return undefined
    let live = true
    const stillHere = (): boolean => live
    const stop = bridge.subscribe('session', key, (event) => {
      if ('outcome' in event) {
        setHeard((was) => ({ ...was, outcome: event.outcome }))
      } else {
        setHeard((was) => ({ ...was, lines: placed(was.lines, event.index, event.line) }))
      }
    })
    void bridge.sessions().then((all) => {
      if (stillHere()) setRecord(all.find((one) => one.key === key) ?? null)
    })
    return () => {
      live = false
      stop()
    }
  }, [key])

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

  useEffect(() => {
    if (project === null) return undefined
    let live = true
    const stillHere = (): boolean => live
    const read = (): void => {
      void project.client.call(root, 'brief', { id }).then((outcome) => {
        if (!stillHere()) return
        if (outcome.kind === 'refused') setNow({ kind: 'gone', refusal: outcome.refusal })
        if (outcome.kind !== 'read') return
        const line = lineOf(outcome.value)
        if (line !== null) setNow({ kind: 'read', payload: line })
      })
    }
    // Asked once on opening, since the session may have moved the line before this screen
    // did, and again on every move after.
    reread.current = read
    read()
    return () => {
      live = false
      reread.current = () => undefined
    }
  }, [project, root, id])

  if (getBridge() === undefined) return { kind: 'absent' }
  if (record === undefined) return { kind: 'opening' }
  if (record === null) return { kind: 'missing' }
  return {
    kind: 'open',
    record,
    lines: together(record.lines, heard.lines),
    outcome: heard.outcome ?? record.outcome,
    marks: project === null ? NOTHING_MARKED : marksOf(project.governed, project.engine.engine),
    now,
  }
}
