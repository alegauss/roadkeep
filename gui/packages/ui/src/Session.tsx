import {
  actsIn,
  arrivedSince,
  editedIn,
  foldedNotes,
  FOLLOWING,
  landingBetween,
  onDisk,
  scrolledTo,
  type Act,
  type Change,
  type ClaimsPayload,
  type DiskStanding,
  type Follow,
  type Edited,
  type EditedFile,
  type GovernedFile,
  type MessageKey,
  type MovedPath,
  type Reading,
  type SessionOutcome,
  type SessionRecord,
  type SessionState,
} from '@rk/core'
import { Button } from '@viglet/viglet-design-system'
import { BentoEmptyState, BentoHero, BentoPanel } from '@viglet/viglet-design-system/bento'
import {
  useCallback,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
  type MouseEvent,
  type ReactNode,
} from 'react'
import { useParams } from 'react-router-dom'

import { getBridge } from './bridge'
import { FileSheet } from './file-sheet'
import { PanelTitle } from './forms'
import { HeroActions } from './hero'
import { Glyph, Pill, type Intent } from './marks'
import { useSessionNotes } from './preferring'
import { ProjectTrail } from './trail'
import { useEditedAt } from './useEditedAt'
import { useRegionHeight } from './useRegionHeight'
import { useSession } from './useSession'
import { useWhen, useWording } from './wording'

/**
 * One session beside the line it was handed (RG153). `docs/design/Sessao.dc.html` is the
 * drawing, reached from Hand to Claude Code on the task.
 *
 * **Three columns, and the middle one is the session's own words.** What was handed over is
 * the brief it was started from, counted and never rewritten. The stream is `actsIn` over the
 * raw lines: text, then each tool on what it was called on, a roadkeep call marked and an act
 * that touched a governed file edged — both by what the project said its own look like — and
 * every raw line stays one disclosure away.
 *
 * **What moved is read off the files, not off the stream.** A session can report shipping a
 * line it did not ship, so the line is briefed again on every move and `landingBetween`
 * compares that with what the session was handed. Where the two disagree, this column is the
 * one that is true. The files it edited are listed off the stream (RG243) and each is then
 * asked of the disk (RG244), so that list is held to the same rule.
 *
 * Stopping kills the process and leaves the claim to the registry's expiry — the session may
 * have moved the line, and releasing it here would undo a state nobody reviewed.
 */

/**
 * Where the session stands, in this app's words for the engine's states. Exported because the
 * list of what is running says the same thing about each one, and two tables would drift.
 */
export const STATE_TEXT: Readonly<Record<SessionState, MessageKey>> = {
  starting: 'session.state.starting',
  running: 'session.state.running',
  done: 'session.state.done',
  failed: 'session.state.failed',
  cancelled: 'session.state.cancelled',
  unavailable: 'session.state.unavailable',
}

export const STATE_INTENT: Readonly<Record<SessionState, Intent>> = {
  starting: null,
  running: null,
  done: 'on',
  failed: 'error',
  cancelled: 'warn',
  unavailable: 'error',
}

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

function Spoken({ act }: { readonly act: Act }) {
  const say = useWording()

  if (act.kind === 'said') {
    return <p className="text-[13px] leading-relaxed whitespace-pre-wrap">{act.text}</p>
  }
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

/** One act, edged where it touched a file this project governs. */
function ActRow({ act }: { readonly act: Act }) {
  const touched = act.kind === 'used' && act.governed.length > 0
  return (
    <li
      // Named by its seq, so an edit in the file viewer leads back to the act that made it
      // (RG246).
      id={`act-${String(act.seq)}`}
      className={`border-t px-4 py-2.5 first:border-t-0 ${touched ? 'border-l-primary border-l-2' : ''}`}
      data-testid="act"
      data-kind={act.kind}
    >
      <Spoken act={act} />
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

/** What was handed over: the brief the session was started from, counted and not rewritten. */
function Handed({ record }: { readonly record: SessionRecord }) {
  const say = useWording()
  const handed = record.handed
  const claimed = handed.claimed

  return (
    <BentoPanel contentClassName="p-5">
      <PanelTitle>{say('session.handed')}</PanelTitle>
      <ul className="flex flex-col gap-1.5 text-[13px]">
        {claimed === null ? null : (
          <li className="flex items-center gap-1.5">
            <Glyph>{claimed.from}</Glyph>
            <span>{say('session.claim', { from: claimed.from, to: claimed.to })}</span>
          </li>
        )}
        <li>
          {handed.section === null
            ? say('session.handed.nodesign')
            : say('session.handed.design', { count: handed.section.words })}
        </li>
        <li>{say('session.handed.deps', { count: handed.deps.length })}</li>
        <li>{say('session.handed.criteria', { count: handed.doneWhen.length })}</li>
        <li>{say('session.handed.bounds', { count: handed.nonGoals.length })}</li>
      </ul>
      <p className="text-muted-foreground mt-3 text-xs wrap-anywhere">
        {say('session.handed.agent', {
          command: record.agent.command.join(' '),
          version: record.agent.version,
        })}
      </p>
    </BentoPanel>
  )
}

/** One change to the line, in the engine's own values. */
function ChangeSaid({ change }: { readonly change: Change }) {
  const say = useWording()
  switch (change.kind) {
    case 'marker':
      return <>{say('session.change.marker', { from: change.from, to: change.to })}</>
    case 'design':
      return (
        <>
          {say(
            change.to === 'written'
              ? 'session.change.design.written'
              : 'session.change.design.deleted',
          )}
        </>
      )
    case 'shipped':
      return <>{say('session.change.shipped')}</>
    case 'symptom':
      return <>{say('session.change.symptom')}</>
    case 'why':
      return <>{say('session.change.why')}</>
    case 'deps':
      return (
        <>
          {change.added.length === 0
            ? null
            : say('session.change.depsAdded', { ids: change.added.join(', ') })}
          {change.dropped.length === 0
            ? null
            : say('session.change.depsDropped', { ids: change.dropped.join(', ') })}
        </>
      )
    default:
      return <>{say('session.change.left', { said: change.said })}</>
  }
}

/** When each governed file last changed, written in the language the window speaks. */
function Files({ files }: { readonly files: readonly GovernedFile[] }) {
  const say = useWording()
  const when = useWhen()
  if (files.length === 0) return null

  return (
    <section className="mt-4" data-testid="files">
      <PanelTitle>{say('session.files')}</PanelTitle>
      <ul className="flex flex-col gap-1 text-xs">
        {files.map((file) => (
          <li key={file.path} className="flex flex-col">
            <span className="font-mono wrap-anywhere">{file.path}</span>
            <span className="text-muted-foreground">
              {file.changed === '' ? say('session.file.never') : when(file.changed)}
            </span>
          </li>
        ))}
      </ul>
    </section>
  )
}

/** What the disk says about an edited file, for each place it can stand (RG244). */
const STANDING_TEXT: Readonly<Record<Exclude<DiskStanding, 'unasked' | 'changed'>, MessageKey>> = {
  outside: 'session.edited.outside',
  missing: 'session.edited.missing',
  unchanged: 'session.edited.unchanged',
}

/** One edited file's standing on disk, or nothing before the disk has answered for it. */
function DiskSaid({
  standing,
  changed,
}: {
  readonly standing: DiskStanding
  readonly changed: string
}) {
  const say = useWording()
  const when = useWhen()
  if (standing === 'unasked') return null
  if (standing === 'changed') return <>{say('session.edited.changed', { when: when(changed) })}</>
  return <>{say(STANDING_TEXT[standing])}</>
}

/**
 * The files the session edited, off its own calls and then asked of the disk (RG243, RG244).
 *
 * Every edit call names its path, so the code a session changed is listed rather than found by
 * reading the stream. **The list is the session's word and each row's standing is the disk's**,
 * the rule this column keeps for the backlog: a call that reported success on a file the disk
 * has not changed since the session started is drawn as the disagreement it is. Each row opens
 * the file as the disk holds it now (RG245).
 */
function EditedFiles({
  edited,
  disk,
  started,
  onOpen,
}: {
  readonly edited: readonly Edited[]
  readonly disk: ReadonlyMap<string, EditedFile>
  readonly started: string
  readonly onOpen: (event: MouseEvent<HTMLButtonElement>) => void
}) {
  const say = useWording()

  return (
    <section className="mt-4" data-testid="edited">
      <PanelTitle>{say('session.edited')}</PanelTitle>
      {edited.length === 0 ? (
        <p className="text-muted-foreground text-xs">{say('session.edited.none')}</p>
      ) : (
        <>
          <p className="text-muted-foreground mb-1.5 text-xs">{say('session.edited.about')}</p>
          <ul className="flex flex-col gap-1.5 text-xs">
            {edited.map((file) => {
              const at = disk.get(file.path)
              const read = onDisk(file, at, started)
              return (
                <li
                  key={file.path}
                  className="flex flex-col gap-0.5"
                  data-testid="edited-file"
                  data-path={file.path}
                  data-standing={read.standing}
                >
                  <button
                    type="button"
                    className="text-left font-mono wrap-anywhere hover:underline"
                    data-path={file.path}
                    aria-label={say('session.edited.open', { path: at?.shown ?? file.path })}
                    onClick={onOpen}
                  >
                    {at?.shown ?? file.path}
                  </button>
                  <span className="text-muted-foreground flex flex-wrap items-center gap-1.5">
                    {say('session.edited.calls', { count: file.calls })}
                    {file.governed ? (
                      <Pill intent="on">{say('session.edited.governed')}</Pill>
                    ) : null}
                    {file.failed ? (
                      <Pill intent="error">{say('session.edited.failed')}</Pill>
                    ) : null}
                  </span>
                  {read.standing === 'unasked' ? null : (
                    <span className="text-muted-foreground flex flex-wrap items-center gap-1.5">
                      <DiskSaid standing={read.standing} changed={at?.changed ?? ''} />
                      {read.disagrees ? (
                        <Pill intent="warn">{say('session.edited.disagrees')}</Pill>
                      ) : null}
                    </span>
                  )}
                </li>
              )
            })}
          </ul>
        </>
      )}
    </section>
  )
}

/**
 * What moved on disk under the project while the session ran, that no edit call named (RG247).
 *
 * **Unattributed, and said so.** A formatter or a generator run through Bash writes files the
 * stream never mentions, and git is not this app's to ask — so the shell watches the root and
 * this lists what moved. Anything else writing under the project in that time is in here too,
 * which the caption does not pretend otherwise about.
 */
function MovedOnDisk({
  moved,
  beyond,
  edited,
  onOpen,
}: {
  readonly moved: readonly MovedPath[]
  readonly beyond: number
  /** The paths the edited list already names, which this one does not repeat. */
  readonly edited: readonly string[]
  readonly onOpen: (event: MouseEvent<HTMLButtonElement>) => void
}) {
  const say = useWording()
  const when = useWhen()
  // What the edited list already named is not news: a path it holds is drawn there, with its
  // calls beside it. Compared on the spelling the shell answers with, which is what both carry.
  const rest = moved.filter((one) => !edited.includes(one.path))

  return (
    <section className="mt-4" data-testid="moved-disk">
      <PanelTitle>{say('session.disk')}</PanelTitle>
      {rest.length === 0 ? (
        <p className="text-muted-foreground text-xs">{say('session.disk.none')}</p>
      ) : (
        <>
          <p className="text-muted-foreground mb-1.5 text-xs">{say('session.disk.about')}</p>
          <ul className="flex flex-col gap-1.5 text-xs">
            {rest.map((one) => (
              <li
                key={one.path}
                className="flex flex-col gap-0.5"
                data-testid="moved-file"
                data-path={one.path}
              >
                <button
                  type="button"
                  className="text-left font-mono wrap-anywhere hover:underline"
                  data-path={one.path}
                  aria-label={say('session.edited.open', { path: one.path })}
                  onClick={onOpen}
                >
                  {one.path}
                </button>
                <span className="text-muted-foreground">
                  {say('session.disk.moves', { count: one.moves })} · {when(one.last)}
                </span>
              </li>
            ))}
          </ul>
          {beyond === 0 ? null : (
            <p className="text-muted-foreground mt-1.5 text-xs">
              {say('session.disk.beyond', { count: beyond })}
            </p>
          )}
        </>
      )}
    </section>
  )
}

/** Who else is on a line of this project, off the engine's own registry. */
function Elsewhere({ claims, id }: { readonly claims: ClaimsPayload | null; readonly id: string }) {
  const say = useWording()
  // Held, and not this session's own line: an expired entry was stepped over and a stale one
  // is a marker that moved out from under it, and neither is somebody working.
  const others = (claims?.claims ?? []).filter((claim) => claim.id !== id && claim.state === 'held')

  return (
    <section className="mt-4" data-testid="elsewhere">
      <PanelTitle>{say('session.claims')}</PanelTitle>
      {others.length === 0 ? (
        <p className="text-muted-foreground text-xs">{say('session.claims.none')}</p>
      ) : (
        <ul className="flex flex-col gap-1 text-xs">
          {others.map((claim) => (
            <li key={claim.id} className="flex flex-wrap items-center gap-1.5">
              <Glyph>{claim.marker}</Glyph>
              <span className="font-mono font-semibold">{claim.id}</span>
              <span className="text-muted-foreground">
                {say('session.claim.since', { state: claim.state, since: claim.since })}
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

/** What moved in the backlog: the files' answer, never the session's account of it. */
function Moved({
  record,
  now,
  outcome,
  acts,
  files,
  claims,
  moved,
  movedBeyond,
}: {
  readonly record: SessionRecord
  readonly now: Reading | null
  readonly outcome: SessionOutcome | null
  readonly acts: readonly Act[]
  readonly files: readonly GovernedFile[]
  readonly claims: ClaimsPayload | null
  /** What moved on disk while it ran, as last told (RG247). */
  readonly moved: readonly MovedPath[]
  readonly movedBeyond: number
}) {
  const say = useWording()
  const landing =
    now === null ? null : landingBetween({ kind: 'read', payload: record.handed }, now)
  const ended = outcome !== null
  const edited = useMemo(() => editedIn(acts), [acts])
  const disk = useEditedAt(record.key, edited, ended)
  // Which file is open in the viewer, and what makes it worth rereading (RG245, RG247). One
  // state for both lists, since a file opens the same way whichever named it.
  const [open, setOpen] = useState<string | null>(null)
  const opening = useCallback((event: MouseEvent<HTMLButtonElement>) => {
    setOpen(event.currentTarget.dataset['path'] ?? null)
  }, [])
  const closing = useCallback(() => {
    setOpen(null)
  }, [])
  // An edit's seq leads back to the act that made it (RG246): the viewer closes, since the
  // stream is under it, and the act is brought into view in its own region.
  const showing = useCallback((seq: number) => {
    setOpen(null)
    requestAnimationFrame(() => {
      document.getElementById(`act-${String(seq)}`)?.scrollIntoView({ block: 'center' })
    })
  }, [])
  // Built once per read: the paths the edited list draws, which the moved list does not repeat.
  const drawn = useMemo(
    () => edited.map((file) => disk.get(file.path)?.shown ?? file.path),
    [edited, disk],
  )
  const viewedEdit = edited.find((file) => file.path === open)
  const viewedMove = moved.find((one) => one.path === open)
  // An edited file is read again as its last call answers; a moved one, each time it moves.
  const version =
    viewedEdit === undefined
      ? (viewedMove?.last ?? '')
      : `${String(viewedEdit.last)}:${String(viewedEdit.answered)}`

  return (
    <BentoPanel contentClassName="p-5">
      <PanelTitle>{say('session.moved')}</PanelTitle>
      {landing === null || !landing.moved ? (
        <p className="text-muted-foreground text-xs">{say('session.moved.none')}</p>
      ) : (
        <ul className="flex flex-col gap-1.5 text-[13px]" data-testid="moved">
          {landing.changes.map((change) => (
            <li key={change.kind} className="wrap-anywhere">
              <ChangeSaid change={change} />
            </li>
          ))}
        </ul>
      )}
      {outcome === null || outcome.result === '' ? null : (
        <p className="text-muted-foreground mt-3 text-xs wrap-anywhere">
          {say('session.result', { result: outcome.result })}
        </p>
      )}
      {outcome === null || outcome.said === '' ? null : (
        <pre className="text-muted-foreground mt-2 max-h-32 overflow-auto text-[11px] whitespace-pre-wrap">
          {outcome.said}
        </pre>
      )}
      <EditedFiles edited={edited} disk={disk} started={record.started} onOpen={opening} />
      <MovedOnDisk moved={moved} beyond={movedBeyond} edited={drawn} onOpen={opening} />
      <Files files={files} />
      <Elsewhere claims={claims} id={record.id} />
      {open === null ? null : (
        <FileSheet
          sessionKey={record.key}
          path={open}
          version={version}
          acts={acts}
          onAct={showing}
          onClose={closing}
        />
      )}
    </BentoPanel>
  )
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
function Stream({ acts }: { readonly acts: readonly Act[] }) {
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
  const room = useRegionHeight(region)
  // Built once per measurement: a fresh object every render is a prop the region redraws for,
  // which `react-perf` refuses and a stream redrawn several times a second cannot afford.
  const bound = useMemo(() => (room === null ? undefined : { maxHeight: room }), [room])
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

  if (count === 0) {
    return (
      <BentoPanel className="min-w-0" contentClassName="p-6">
        <BentoEmptyState title={say('session.stream.empty')} />
      </BentoPanel>
    )
  }
  const arrived = arrivedSince(follow, count)
  return (
    <BentoPanel className="min-w-0" contentClassName="relative p-0">
      <span className="block px-5 pt-4">
        <PanelTitle>{say('session.stream')}</PanelTitle>
      </span>
      <div
        ref={region}
        onScroll={scrolled}
        className="mt-2 overflow-y-auto overscroll-contain"
        style={bound}
        data-testid="stream"
      >
        <ul>
          {rows.map((row) =>
            row.kind === 'act' ? (
              <ActRow key={row.act.seq} act={row.act} />
            ) : (
              <FoldedRow key={`folded-${String(row.notes[0]?.seq ?? 0)}`} notes={row.notes} />
            ),
          )}
        </ul>
      </div>
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

export function Session() {
  const say = useWording()
  const params = useParams()
  const root = decodeURIComponent(params['root'] ?? '')
  const id = decodeURIComponent(params['id'] ?? '')
  const key = decodeURIComponent(params['key'] ?? '')
  const view = useSession(root, id, key)
  const session = view.kind === 'open' ? view : null

  const stop = useCallback(() => {
    void getBridge()?.stopSession(key)
  }, [key])

  const state: SessionState =
    session === null
      ? 'starting'
      : (session.outcome?.state ?? (session.lines.length === 0 ? 'starting' : 'running'))
  const running = session !== null && session.outcome === null

  let subtitle: ReactNode = say('session.opening')
  if (view.kind === 'absent') subtitle = say('transport.absent')
  if (view.kind === 'missing') subtitle = say('session.missing')
  if (session !== null) {
    subtitle = (
      <span className="flex flex-col gap-1">
        <span className="wrap-anywhere">{session.record.handed.symptom}</span>
        <span>
          <Pill intent={STATE_INTENT[state]}>{say(STATE_TEXT[state])}</Pill>
        </span>
      </span>
    )
  }
  const trailing = useMemo(
    () =>
      running ? (
        <HeroActions>
          <Button variant="outline" size="sm" onClick={stop}>
            {say('session.stop')}
          </Button>
        </HeroActions>
      ) : undefined,
    [running, stop, say],
  )

  // Which project and which line this session is on (RG242): the task was the only crumb, so a
  // session reached from the sessions list or a handover never said which project it was in.
  const face = session === null ? null : session.face
  const trail = useMemo(() => <ProjectTrail root={root} face={face} task={id} />, [root, face, id])

  // Read once for both columns that need them: the stream draws the acts, and what moved lists
  // the files they edited (RG243).
  const lines = session?.lines
  const marks = session?.marks
  const acts = useMemo(
    () => (lines === undefined || marks === undefined ? [] : actsIn(lines, marks)),
    [lines, marks],
  )

  return (
    <>
      <BentoHero eyebrow={trail} title={id} subtitle={subtitle} trailing={trailing} />
      {session === null ? null : (
        // The stream is written first and placed in the middle (RG225). Stacked below `lg`,
        // the columns fall in the order they are written, and what was handed over and what
        // moved used to come first — so at 400 wide the session's own words, which a reader
        // opened this screen for, started below the fold whatever the region's height did.
        // First in the document is also first for a screen reader, at every width.
        //
        // Laid out as an editor is, across the window's whole width (RG237): from `xl` what was
        // handed over is a side bar on the left, what moved one on the right, and the stream
        // takes the middle. Between `lg` and `xl` the two side panels share the left column —
        // what moved under what was handed, the stream spanning both rows — since three columns
        // at 1024 would leave the stream where the reading column had it. The second row is
        // `1fr` so a stream taller than the two panels grows that row and not the gap between them.
        <div className="grid items-start gap-5 lg:grid-cols-[18rem_minmax(0,1fr)] lg:grid-rows-[auto_1fr] xl:grid-cols-[18rem_minmax(0,1fr)_18rem] xl:grid-rows-none">
          <div
            className="min-w-0 lg:col-start-2 lg:row-span-2 lg:row-start-1 xl:row-span-1"
            data-region="session-stream"
          >
            <Stream acts={acts} />
          </div>
          <div className="min-w-0 lg:col-start-1 lg:row-start-1" data-region="session-handed">
            <Handed record={session.record} />
          </div>
          <div
            className="min-w-0 lg:col-start-1 lg:row-start-2 xl:col-start-3 xl:row-start-1"
            data-region="session-moved"
          >
            <Moved
              record={session.record}
              now={session.now}
              outcome={session.outcome}
              acts={acts}
              files={session.files}
              claims={session.claims}
              moved={session.moved}
              movedBeyond={session.movedBeyond}
            />
          </div>
        </div>
      )}
    </>
  )
}
