import {
  lineOf,
  marksOf,
  NOTHING_MARKED,
  openOver,
  type ClaimsPayload,
  type GovernedFile,
  type Marks,
  type OpenProject,
  type Reading,
  type SessionOutcome,
  type MovedPath,
  type SessionRecord,
} from '@rk/core'
import { useEffect, useMemo, useRef, useState } from 'react'

import { getBridge } from './bridge'
import { useGovernedMoves } from './following'
import { faceOf, type ProjectFace } from './trail'

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
      /** The project's name, emoji and logo once it opened, or null until then (RG242). */
      readonly face: ProjectFace | null
      /** The line as the engine answers it now, or null before the first reread lands. */
      readonly now: Reading | null
      /** The project's governed files with when each last changed, as the disk says. */
      readonly files: readonly GovernedFile[]
      /** The claim registry, or null where it has not answered. Held elsewhere is a filter. */
      readonly claims: ClaimsPayload | null
      /** What moved on disk under the root while it ran (RG247), as last told. */
      readonly moved: readonly MovedPath[]
      /** How many moved paths the far side left out at its ceiling. */
      readonly movedBeyond: number
    }

/** What was heard on the session's topic, kept apart from the record until both are here. */
interface Heard {
  readonly lines: readonly string[]
  readonly outcome: SessionOutcome | null
  /** The whole folded list each time it is told, or null while nothing has been (RG247). */
  readonly moved: readonly MovedPath[] | null
  readonly movedBeyond: number
}

const NOTHING_HEARD: Heard = { lines: [], outcome: null, moved: null, movedBeyond: 0 }

/** Built once: a fresh array per render is a new dependency for everything below it. */
const NO_FILES: readonly GovernedFile[] = []

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
  const [files, setFiles] = useState<readonly GovernedFile[]>(NO_FILES)
  const [claims, setClaims] = useState<ClaimsPayload | null>(null)
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
      } else if ('resumed' in event) {
        // Answered and running again (RG269): the outcome this screen holds is over, the record's
        // as well as the one heard, or the ended pill would stand over a turn still going.
        setHeard((was) => ({ ...was, outcome: null }))
        setRecord((was) => (was === null || was === undefined ? was : { ...was, outcome: null }))
      } else if ('moved' in event) {
        // The whole folded list each time (RG247), so a screen that missed one event is not
        // behind: what arrives replaces what was held.
        setHeard((was) => ({ ...was, moved: event.moved, movedBeyond: event.beyond }))
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
      // A session handed a gate finding names no line (RG263), so there is none to re-read:
      // `brief` with an empty id is a process spent on a refusal, and the landing it feeds is
      // already drawn as nothing. The claims and the files below are about the project and
      // are still worth asking.
      if (id !== '') {
        void project.client.call(root, 'brief', { id }).then((outcome) => {
          if (!stillHere()) return
          if (outcome.kind === 'refused') setNow({ kind: 'gone', refusal: outcome.refusal })
          if (outcome.kind !== 'read') return
          const line = lineOf(outcome.value)
          if (line !== null) setNow({ kind: 'read', payload: line })
        })
      }
      // Who else is on a line of this project, which is the engine's registry and not a
      // state this app keeps.
      void project.client.call(root, 'claims', {}).then((outcome) => {
        if (stillHere() && outcome.kind === 'read') setClaims(outcome.value)
      })
      // And when each governed file last changed, which only the side with the disk knows.
      void getBridge()
        ?.governedAt(root)
        .then(
          (all) => {
            if (stillHere()) setFiles(all)
          },
          () => undefined,
        )
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

  // Built once per opening, so the trail drawn from it is not a new element every render.
  const face = useMemo(() => faceOf(project, root), [project, root])

  if (getBridge() === undefined) return { kind: 'absent' }
  if (record === undefined) return { kind: 'opening' }
  if (record === null) return { kind: 'missing' }
  return {
    kind: 'open',
    record,
    lines: together(record.lines, heard.lines),
    outcome: heard.outcome ?? record.outcome,
    marks: project === null ? NOTHING_MARKED : marksOf(project.governed, project.engine.engine),
    face,
    now,
    files,
    claims,
    // What was heard stands over what the record carried, being the later answer.
    moved: heard.moved ?? record.moved,
    movedBeyond: heard.moved === null ? record.movedBeyond : heard.movedBeyond,
  }
}
