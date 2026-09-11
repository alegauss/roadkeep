import {
  allLines,
  backlogFrom,
  reversedFrom,
  storeFrom,
  undoneBy,
  type MessageKey,
  type OpenProject,
  type ReadOutcome,
  type Reversed,
  type TaskLine,
} from '@rk/core'
import { BentoEmptyState, BentoPanel } from '@viglet/viglet-design-system/bento'
import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type ReactNode,
  type SyntheticEvent,
} from 'react'

import { Glyph, Pill } from './marks'
import { useWording } from './wording'

/**
 * The four governed files beside the roadmap, as tabs (RG149).
 *
 * **Each tab is a listing of its own file**, read the way the roadmap is: the changelog and
 * the decisions are `list` with their role, the deferred store is `list --stale`, and the
 * improvements tab is the roadmap's designed lines, since a design section is read in its
 * task and not here. Nothing is joined across files that one read does not already join.
 *
 * **The prose is the file's.** A decision's reasoning is its section, read only when a
 * reader opens it and drawn in the text face with the file's own wrapping kept — no Markdown
 * is parsed, which is block H's criterion and the non-goal both. A changelog entry an entry
 * later undid says so beside it, from `reversals`, and is not dropped.
 *
 * The deferred store draws in the order the payload arrived in, and says which order that is
 * where the engine named one — `oldest first` for a `--stale` listing (RG28). How long each
 * pause has stood is the engine's own count of commits, drawn as a number and never as a
 * judgement about whether it has stood too long.
 */

/** What a read answered, or the sentence it failed with. Null while it is out. */
type Answer<T> = { readonly value: T } | { readonly failed: string } | null

/**
 * One read, asked again when the question changes.
 *
 * The answer is kept with the question it answers, so one that lands for an earlier
 * question — a tab left before its read came back — is never drawn under the next. The read
 * itself is the latest one handed in, since a caller builds it afresh every render.
 */
function useAnswer<T>(read: () => Promise<ReadOutcome<T>>, question: string): Answer<T> {
  const latest = useRef(read)
  useEffect(() => {
    latest.current = read
  })
  const [held, setHeld] = useState<{
    readonly question: string
    readonly answer: Answer<T>
  } | null>(null)

  useEffect(() => {
    let live = true
    const stillHere = (): boolean => live
    void latest.current().then((outcome) => {
      if (!stillHere()) return
      const answer: Answer<T> =
        outcome.kind === 'read'
          ? { value: outcome.value }
          : {
              failed:
                outcome.kind === 'refused' ? outcome.refusal.said : outcome.unreadable.message,
            }
      setHeld({ question, answer })
    })
    return () => {
      live = false
    }
  }, [question])

  return held !== null && held.question === question ? held.answer : null
}

function Waiting({
  answer,
  empty,
}: {
  readonly answer: Answer<unknown>
  readonly empty: MessageKey
}) {
  const say = useWording()
  if (answer === null)
    return <p className="text-muted-foreground text-sm">{say('project.listing')}</p>
  if ('failed' in answer) {
    return (
      <p className="text-muted-foreground text-sm">
        {say('project.read.failed', { reason: answer.failed })}
      </p>
    )
  }
  return <BentoEmptyState title={say(empty)} />
}

/** A shipped, decided or paused line: its marker and id, what it claimed, and what it says. */
function Entry({ line, children }: { readonly line: TaskLine; readonly children?: ReactNode }) {
  return (
    <li
      className="grid grid-cols-[6rem_minmax(0,1fr)] gap-4 border-t px-5 py-3 first:border-t-0"
      data-testid="entry"
      data-id={line.id}
    >
      <div className="flex items-start gap-2 pt-0.5">
        <Glyph>{line.status}</Glyph>
        <span className="font-mono text-xs font-semibold">{line.id}</span>
      </div>
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-2">
          <span className="bg-muted text-muted-foreground rounded px-1.5 text-xs font-semibold">
            {line.block}
          </span>
          <span className="text-sm font-medium [overflow-wrap:anywhere]">{line.symptom}</span>
        </div>
        <div className="text-muted-foreground mt-1 text-[13px] [overflow-wrap:anywhere]">
          {line.why}
        </div>
        {children}
      </div>
    </li>
  )
}

function Entries({ children }: { readonly children: ReactNode }) {
  return (
    <BentoPanel className="overflow-hidden" contentClassName="p-0">
      <ul>{children}</ul>
    </BentoPanel>
  )
}

export function ChangelogTab({ project }: { readonly project: OpenProject }) {
  const say = useWording()
  const listed = useAnswer(
    () => project.client.call(project.root, 'list', { role: 'changelog' }),
    `${project.root} changelog`,
  )
  const undone = useAnswer(
    () => project.client.call(project.root, 'reversals', {}),
    `${project.root} reversals`,
  )
  const reversed: Reversed | null =
    undone !== null && 'value' in undone ? reversedFrom(undone.value) : null

  if (listed === null || 'failed' in listed)
    return <Waiting answer={listed} empty="project.changelog.none" />
  const lines = allLines(backlogFrom(listed.value))
  if (lines.length === 0) return <Waiting answer={listed} empty="project.changelog.none" />

  return (
    <Entries>
      {lines.map((line) => {
        const by = reversed === null ? null : undoneBy(reversed, line.id)
        return (
          <Entry key={line.id} line={line}>
            {by === null ? null : (
              <div className="mt-1.5">
                <Pill intent="warn">{say('project.undone', { by: by.by })}</Pill>
              </div>
            )}
          </Entry>
        )
      })}
    </Entries>
  )
}

/** A decision's own section, read when somebody opens it and drawn as the file keeps it. */
function Reasoning({ project, id }: { readonly project: OpenProject; readonly id: string }) {
  const say = useWording()
  const [open, setOpen] = useState(false)
  const [body, setBody] = useState<string | null | undefined>(undefined)
  const toggle = useCallback(
    (event: SyntheticEvent<HTMLDetailsElement>) => {
      const opened = event.currentTarget.open
      setOpen(opened)
      if (!opened || body !== undefined) return
      void project.client
        .call(project.root, 'sectionShow', { anchor: id, role: 'decisions' })
        .then((outcome) => {
          setBody(outcome.kind === 'read' ? (outcome.value.body ?? '') : null)
        })
    },
    [project, id, body],
  )

  let shown: ReactNode = null
  if (open && body === undefined) shown = say('project.decision.asking')
  if (open && body === null) shown = say('project.decision.bare')

  return (
    <details className="mt-1.5 text-xs" onToggle={toggle}>
      <summary className="text-primary cursor-pointer font-medium">
        {say('project.decision.reasoning')}
      </summary>
      {typeof body === 'string' && body !== '' ? (
        <pre className="text-foreground mt-2 font-sans text-[13px] leading-relaxed whitespace-pre-wrap">
          {body}
        </pre>
      ) : (
        <p className="text-muted-foreground mt-1">{shown}</p>
      )}
    </details>
  )
}

export function DecisionsTab({ project }: { readonly project: OpenProject }) {
  const listed = useAnswer(
    () => project.client.call(project.root, 'list', { role: 'decisions' }),
    `${project.root} decisions`,
  )
  if (listed === null || 'failed' in listed)
    return <Waiting answer={listed} empty="project.decisions.none" />
  const lines = allLines(backlogFrom(listed.value))
  if (lines.length === 0) return <Waiting answer={listed} empty="project.decisions.none" />

  return (
    <Entries>
      {lines.map((line) => (
        <Entry key={line.id} line={line}>
          <Reasoning project={project} id={line.id} />
        </Entry>
      ))}
    </Entries>
  )
}

export function DeferredTab({ project }: { readonly project: OpenProject }) {
  const say = useWording()
  const listed = useAnswer(
    () => project.client.call(project.root, 'list', { stale: true }),
    `${project.root} deferred`,
  )
  if (listed === null || 'failed' in listed)
    return <Waiting answer={listed} empty="project.deferred.none" />
  const store = storeFrom(listed.value)
  if (store.pauses.length === 0) return <Waiting answer={listed} empty="project.deferred.none" />
  const lines = allLines(backlogFrom(listed.value))
  const lineOf = new Map(lines.map((line) => [line.id, line]))

  return (
    <>
      {store.order === '' ? null : (
        <p className="text-muted-foreground mb-2 text-xs" data-testid="store-order">
          {say('project.deferred.order', { order: store.order })}
        </p>
      )}
      <Entries>
        {/* In the store's own order, which is the engine's where it named one (RG28) — and
            never the block order the other tabs draw, since the oldest pause is the point. */}
        {store.pauses.map((pause) => {
          const line = lineOf.get(pause.id)
          return line === undefined ? null : (
            <Entry key={pause.id} line={line}>
              <div className="mt-1.5 flex flex-wrap items-center gap-2 text-xs">
                {/* Silent where the engine counted nothing: zero would read as
                 *set aside just now*, which is the opposite of what null means. */}
                {pause.since === null ? null : (
                  <span className="text-muted-foreground" data-testid="stood">
                    {say('project.deferred.since', { count: pause.since })}
                  </span>
                )}
                {line.deps.length === 0 ? (
                  <span className="text-muted-foreground">{say('project.deps.none')}</span>
                ) : (
                  line.deps.map((dep) => (
                    <span key={dep} className="font-mono">
                      {dep}
                    </span>
                  ))
                )}
              </div>
            </Entry>
          )
        })}
      </Entries>
    </>
  )
}

export function ImprovementsTab({ project }: { readonly project: OpenProject }) {
  const say = useWording()
  const listed = useAnswer(
    () => project.client.call(project.root, 'list', {}),
    `${project.root} designed`,
  )
  if (listed === null || 'failed' in listed)
    return <Waiting answer={listed} empty="project.improvements.none" />
  const designed = allLines(backlogFrom(listed.value)).filter((line) => line.ref !== null)
  if (designed.length === 0) return <Waiting answer={listed} empty="project.improvements.none" />

  return (
    <Entries>
      {designed.map((line) => (
        <Entry key={line.id} line={line}>
          <div className="text-muted-foreground mt-1.5 text-xs">
            {say('project.design.written', { ref: line.ref ?? '' })}
          </div>
        </Entry>
      ))}
    </Entries>
  )
}
