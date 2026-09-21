import {
  arrivedSince,
  foldedNotes,
  FOLLOWING,
  scrolledTo,
  type Act,
  type AskStanding,
  type Follow,
  type MessageKey,
} from '@rk/core'
import { Button } from '@viglet/viglet-design-system'
import { BentoEmptyState, BentoPanel } from '@viglet/viglet-design-system/bento'
import { useCallback, useLayoutEffect, useMemo, useRef, useState, type ReactNode } from 'react'

import { PanelTitle } from './forms'
import { Pill } from './marks'
import { useSessionNotes } from './preferring'
import { Prose } from './prose'
import { useRegionHeight } from './useRegionHeight'
import { useWording } from './wording'

/**
 * A run's stream as rows (RG153, RG297): what the session screen draws, and what the waiting
 * explanation draws while its run is going.
 *
 * Moved out of `Session.tsx` whole when the second reader came: a gloss is the same SDK stream a
 * session is, so it is read by the same `actsIn` and drawn by the same rows — text rendered, each
 * tool on what it was called on, what came back, notes folded by the reader's own setting, and
 * every raw line one disclosure away. Two copies would be two ideas of what a run looks like.
 */
/** The raw line, one disclosure away from every act it was read into. */
function Raw({ line }: { readonly line: string }) {
  const say = useWording()
  return (
    <details className="mt-1 text-[11px]">
      <summary className="text-muted-foreground cursor-pointer">{say('session.act.raw')}</summary>
      <pre className="bg-muted mt-1 max-h-40 overflow-auto rounded p-2 text-[11px] whitespace-pre-wrap">
        {line}
      </pre>
    </details>
  )
}

/**
 * Where a question stands, as drawn (RG272): the lines' own answer, or still open — which past
 * the end of the process is a question nobody answered, and never one still waiting.
 */
export type Standing = AskStanding | 'unanswered'

/** A question's act, which is what its row in the stream is drawn from. */
type AskedAct = Extract<Act, { readonly kind: 'asked' }>

const ASK_TEXT: Readonly<Record<Standing, MessageKey>> = {
  open: 'session.ask.open',
  once: 'session.ask.answered.once',
  session: 'session.ask.answered.session',
  decline: 'session.ask.answered.decline',
  withdrawn: 'session.ask.withdrawn',
  unanswered: 'session.ask.unanswered',
}

/** A question in the stream: what it asked for, and where it stands. Answered under the stream. */
function Asked({ act, standing }: { readonly act: AskedAct; readonly standing: Standing }) {
  const say = useWording()
  return (
    <div className="flex flex-col gap-1">
      <div className="flex flex-wrap items-center gap-2">
        <Pill intent={standing === 'open' ? 'warn' : null}>{say('session.ask.asked')}</Pill>
        <span className="font-mono text-xs font-semibold">{act.ask.tool}</span>
        {act.on === '' ? null : (
          <span className="text-muted-foreground min-w-0 font-mono text-xs wrap-anywhere">
            {act.on}
          </span>
        )}
      </div>
      <span className="text-xs" data-testid="ask-standing" data-standing={standing}>
        {say(ASK_TEXT[standing])}
      </span>
    </div>
  )
}

function Spoken({ act, standing }: { readonly act: Act; readonly standing?: Standing }) {
  const say = useWording()

  if (act.kind === 'asked') return <Asked act={act} standing={standing ?? 'open'} />

  // Its words are written for a person, so they are rendered (RG271); what a tool was called on
  // and what it gave back are measured, so they stay raw.
  if (act.kind === 'said') return <Prose text={act.text} />
  if (act.kind === 'used') {
    return (
      <div className="flex flex-col gap-1">
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-mono text-xs font-semibold">{act.tool}</span>
          {act.on === '' ? null : (
            <span className="text-muted-foreground min-w-0 font-mono text-xs wrap-anywhere">
              {act.on}
            </span>
          )}
          {act.roadkeep ? <Pill intent="on">{say('session.act.roadkeep')}</Pill> : null}
        </div>
        {act.governed.length === 0 ? null : (
          <span className="text-xs font-medium">
            {say('session.act.governed', { files: act.governed.join(', ') })}
          </span>
        )}
      </div>
    )
  }
  if (act.kind === 'returned') {
    return (
      <div className="flex flex-col gap-1">
        {act.ok ? null : <Pill intent="error">{say('session.act.failed')}</Pill>}
        <pre className="text-muted-foreground max-h-32 overflow-auto text-[12px] whitespace-pre-wrap">
          {act.text}
        </pre>
      </div>
    )
  }
  return <span className="text-muted-foreground font-mono text-xs">{act.about}</span>
}

/** One act, edged where it touched a file this project governs, or asks what nobody answered. */
function ActRow({ act, standing }: { readonly act: Act; readonly standing?: Standing }) {
  const touched = (act.kind === 'used' && act.governed.length > 0) || standing === 'open'
  return (
    <li
      // Named by its seq, so an edit in the file viewer leads back to the act that made it
      // (RG246).
      id={`act-${String(act.seq)}`}
      className={`border-t px-4 py-2.5 first:border-t-0 ${touched ? 'border-l-primary border-l-2' : ''}`}
      data-testid="act"
      data-kind={act.kind}
    >
      <Spoken act={act} standing={standing} />
      <Raw line={act.line} />
    </li>
  )
}

/**
 * A run of notes folded into one quiet row (RG208), counted so the stream is still accounted
 * for, and each note with its raw line one disclosure away.
 */
function FoldedRow({ notes }: { readonly notes: readonly Act[] }) {
  const say = useWording()
  return (
    <li
      className="border-t px-4 py-2 first:border-t-0"
      data-testid="folded"
      data-count={notes.length}
    >
      <details className="text-[11px]">
        <summary className="text-muted-foreground cursor-pointer">
          {say('session.notes.folded', { count: notes.length })}
        </summary>
        <ul className="mt-1.5 flex flex-col gap-1.5">
          {notes.map((note) => (
            <li key={note.seq} data-testid="act" data-kind={note.kind}>
              <Spoken act={note} />
              <Raw line={note.line} />
            </li>
          ))}
        </ul>
      </details>
    </li>
  )
}

interface StreamProps {
  readonly acts: readonly Act[]
  /** What sits under the region inside the panel, which its height leaves room for (RG269). */
  readonly after?: ReactNode
  /** Where each question stands, by its id (RG272). */
  readonly standings: ReadonlyMap<string, Standing>
  /**
   * A class that bounds the region, in place of measuring the room to the window's bottom
   * (RG297). A dialog scrolls itself, so the room under a region inside one is not the room the
   * reader has: there the bound is a height of its own.
   */
  readonly bound?: string
}

/** No question anywhere, for a stream nobody can be asked from (RG297). */
export const NO_STANDINGS: ReadonlyMap<string, Standing> = new Map()

/**
 * The session's words, or the panel that says there are none yet.
 *
 * **Two components, so the one that measures mounts with its region** (RG275). A task opens this
 * screen the moment its session spawns, before the first line. The region was measured then,
 * against nothing, and never again, so it grew the page with every act. The gate only links
 * here and the link is pressed later, when there are acts, which is why its session never grew.
 */
export function Stream({ acts, after, standings, bound }: StreamProps) {
  const say = useWording()
  if (acts.length === 0) {
    return (
      <BentoPanel className="min-w-0" contentClassName="p-6">
        <BentoEmptyState title={say('session.stream.empty')} />
      </BentoPanel>
    )
  }
  return <Flowing acts={acts} after={after} standings={standings} bound={bound} />
}

/**
 * The session's own words, in a region that scrolls by itself and follows its end (RG206).
 *
 * The drawing gives the stream a height of its own; drawn as a list the page grows around, a
 * new act landed below the fold and a running session was read by scrolling the window. The
 * region is bounded by the viewport at every width, so there is one scroller and one rule —
 * `scrolledTo` — rather than a window below `lg` and a region above it.
 *
 * **The bound is measured** (RG217). It was `calc(100dvh - 12rem)`, a guess at what the header
 * and the hero take, and they take about 290 pixels rather than 192 — so the region ran past
 * the bottom of the window and its end, the one thing following exists to keep in view, was
 * below the fold. `useRegionHeight` reads the room under the region's own top instead.
 *
 * Following moves with the reader's own scroll: away from the end it stops and offers the way
 * back with what arrived since, and at the end it follows again. The jump is instant, because
 * a smooth scroll chasing several lines a second never arrives.
 */
function Flowing({ acts, after, standings, bound: fixed }: StreamProps) {
  const say = useWording()
  // Folded where the reader chose it, and applied here rather than in `actsIn`: the acts stay
  // whole, and following still counts every one of them (RG208).
  const notes = useSessionNotes()
  const rows = useMemo(
    () =>
      notes === 'hidden' ? foldedNotes(acts) : acts.map((act) => ({ kind: 'act' as const, act })),
    [acts, notes],
  )
  const region = useRef<HTMLDivElement>(null)
  const tail = useRef<HTMLDivElement>(null)
  // The reply box under the region is kept in view (RG269): the region's room is measured to the
  // bottom of the window, and a box under it would otherwise open below the fold at the very
  // moment the session is asking for it.
  const room = useRegionHeight(region, tail, after !== undefined)
  // Built once per measurement: a fresh object every render is a prop the region redraws for,
  // which `react-perf` refuses and a stream redrawn several times a second cannot afford. A
  // region given a bound of its own (RG297) takes no measured one: the class is its height.
  const bound = useMemo(
    () => (fixed !== undefined || room === null ? undefined : { maxHeight: room }),
    [fixed, room],
  )
  const [follow, setFollow] = useState<Follow>(FOLLOWING)
  const count = acts.length
  // What the region was last put at the end for, so only a change moves it: a redraw for
  // anything else — a reread of the line, a raw line opened — leaves it be.
  //
  // The room as well as the count, since RG217. The bound arrives after the first paint —
  // it is measured off the page — so a stream that was placed while it was still unbounded
  // had nowhere to scroll to, and stayed at its top with the newest act out of sight. A
  // window the reader resizes is the same moment: while following, the end stays in view.
  const placed = useRef({ count: 0, room: null as number | null })

  // Before paint, so an act that lands while following is never seen below the fold first.
  useLayoutEffect(() => {
    const element = region.current
    if (element === null || follow.leftAt !== null) return
    if (placed.current.count === count && placed.current.room === room) return
    placed.current = { count, room }
    element.scrollTop = element.scrollHeight
  }, [count, follow, room])

  const scrolled = useCallback(() => {
    const element = region.current
    if (element === null) return
    const where = {
      top: element.scrollTop,
      height: element.scrollHeight,
      visible: element.clientHeight,
    }
    setFollow((was) => scrolledTo(was, where, count))
  }, [count])

  const jump = useCallback(() => {
    const element = region.current
    if (element !== null) element.scrollTop = element.scrollHeight
    setFollow(FOLLOWING)
  }, [])

  const arrived = arrivedSince(follow, count)
  return (
    <BentoPanel className="min-w-0" contentClassName="relative p-0">
      <span className="block px-5 pt-4">
        <PanelTitle>{say('session.stream')}</PanelTitle>
      </span>
      <div
        ref={region}
        onScroll={scrolled}
        className={`mt-2 overflow-y-auto overscroll-contain ${fixed ?? ''}`}
        style={bound}
        data-testid="stream"
      >
        <ul>
          {rows.map((row) =>
            row.kind === 'act' ? (
              <ActRow
                key={row.act.seq}
                act={row.act}
                standing={
                  row.act.kind === 'asked' ? standings.get(row.act.ask.requestId) : undefined
                }
              />
            ) : (
              <FoldedRow key={`folded-${String(row.notes[0]?.seq ?? 0)}`} notes={row.notes} />
            ),
          )}
        </ul>
      </div>
      <div ref={tail}>{after}</div>
      {follow.leftAt === null ? null : (
        <div className="pointer-events-none absolute inset-x-0 bottom-3 flex justify-center">
          <Button size="sm" className="pointer-events-auto shadow-md" onClick={jump}>
            {arrived === 0
              ? say('session.follow')
              : say('session.follow.since', { count: arrived })}
          </Button>
        </div>
      )}
    </BentoPanel>
  )
}
