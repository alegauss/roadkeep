import {
  actsIn,
  landingBetween,
  type Act,
  type Change,
  type ClaimsPayload,
  type GovernedFile,
  type Marks,
  type MessageKey,
  type Reading,
  type SessionOutcome,
  type SessionRecord,
  type SessionState,
} from '@rk/core'
import { Button } from '@viglet/viglet-design-system'
import { BentoEmptyState, BentoHero, BentoPanel } from '@viglet/viglet-design-system/bento'
import { useCallback, useMemo, type ReactNode } from 'react'
import { useParams } from 'react-router-dom'

import { taskPath } from './areas'
import { getBridge } from './bridge'
import { PanelTitle } from './forms'
import { Glyph, Pill, type Intent } from './marks'
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
 * one that is true.
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
      className={`border-t px-4 py-2.5 first:border-t-0 ${touched ? 'border-l-primary border-l-2' : ''}`}
      data-testid="act"
      data-kind={act.kind}
    >
      <Spoken act={act} />
      <Raw line={act.line} />
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
            : say('session.handed.design', { words: handed.section.words })}
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
  files,
  claims,
}: {
  readonly record: SessionRecord
  readonly now: Reading | null
  readonly outcome: SessionOutcome | null
  readonly files: readonly GovernedFile[]
  readonly claims: ClaimsPayload | null
}) {
  const say = useWording()
  const landing =
    now === null ? null : landingBetween({ kind: 'read', payload: record.handed }, now)

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
      <Files files={files} />
      <Elsewhere claims={claims} id={record.id} />
    </BentoPanel>
  )
}

function Stream({ lines, marks }: { readonly lines: readonly string[]; readonly marks: Marks }) {
  const say = useWording()
  const acts = useMemo(() => actsIn(lines, marks), [lines, marks])

  if (acts.length === 0) {
    return (
      <BentoPanel className="min-w-0" contentClassName="p-6">
        <BentoEmptyState title={say('session.stream.empty')} />
      </BentoPanel>
    )
  }
  return (
    <BentoPanel className="min-w-0" contentClassName="p-0">
      <span className="block px-5 pt-4">
        <PanelTitle>{say('session.stream')}</PanelTitle>
      </span>
      <ul className="mt-2">
        {acts.map((act) => (
          <ActRow key={act.seq} act={act} />
        ))}
      </ul>
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
        <Button variant="outline" size="sm" onClick={stop}>
          {say('session.stop')}
        </Button>
      ) : undefined,
    [running, stop, say],
  )

  return (
    <>
      <BentoHero
        backTo={taskPath(root, id)}
        backLabel={id}
        title={id}
        subtitle={subtitle}
        trailing={trailing}
      />
      {session === null ? null : (
        <div className="grid items-start gap-5 lg:grid-cols-[18rem_minmax(0,1fr)_18rem]">
          <Handed record={session.record} />
          <Stream lines={session.lines} marks={session.marks} />
          <Moved
            record={session.record}
            now={session.now}
            outcome={session.outcome}
            files={session.files}
            claims={session.claims}
          />
        </div>
      )}
    </>
  )
}
