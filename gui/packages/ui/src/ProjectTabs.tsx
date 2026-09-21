import {
  allLines,
  backlogFrom,
  counted,
  reversedFrom,
  storeFrom,
  undoneBy,
  reasonOf,
  validationFrom,
  type Validation,
  type MessageKey,
  type OpenProject,
  type ReadOutcome,
  type Reversed,
  type TaskLine,
  type Unreadable,
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

import { Checking } from './checking'
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
/**
 * What a read answered, or why it did not — kept as the state and not as a sentence, so the
 * sentence is looked up where it is drawn and a window that changes language changes it
 * (RG168). A refusal's `said` is the engine's own prose and crosses as it is.
 */
type Answer<T> =
  | { readonly value: T }
  | { readonly failed: { readonly said: string } | { readonly unreadable: Unreadable } }
  | null

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
                outcome.kind === 'refused'
                  ? { said: outcome.refusal.said }
                  : { unreadable: outcome.unreadable },
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
    const reason =
      'said' in answer.failed ? answer.failed.said : reasonOf(answer.failed.unreadable, say)
    return <p className="text-muted-foreground text-sm">{say('project.read.failed', { reason })}</p>
  }
  return <BentoEmptyState title={say(empty)} />
}

/** A shipped, decided or paused line: its marker and id, what it claimed, and what it says. */
function Entry({ line, children }: { readonly line: TaskLine; readonly children?: ReactNode }) {
  return (
    <li
      // Stacked below `sm` for the reason the roadmap tab's row is (RG223), and written the
      // same way for the reason it is (RG229): the desktop grid as the base, `max-sm:` over it.
      className="grid grid-cols-[6rem_minmax(0,1fr)] gap-x-4 gap-y-2 border-t px-5 py-3 first:border-t-0 max-sm:grid-cols-1"
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

/**
 * One designed line, named by its design's own heading (RG171).
 *
 * The heading is a read of its own — `list` carries the pointer and not the title — so each
 * row asks for its section as the tab opens, bounded by the carrier's pool like every other
 * read. Until it lands the row shows the pointer, which is what it showed before, so the tab
 * is never blank while it reads and a section that will not come back stays as it was.
 */
function DesignRow({
  project,
  line,
  anchor,
}: {
  readonly project: OpenProject
  readonly line: TaskLine
  readonly anchor: string
}) {
  const say = useWording()
  const [title, setTitle] = useState('')

  useEffect(() => {
    let live = true
    const stillHere = (): boolean => live
    // The body comes with it: `section show` declares no way to decline one, so what is
    // not asked for here is simply not drawn.
    void project.client
      .call(project.root, 'sectionShow', { anchor, role: 'improvements' })
      .then((outcome) => {
        if (stillHere() && outcome.kind === 'read') setTitle(outcome.value.title)
      })
    return () => {
      live = false
    }
  }, [project, anchor])

  return (
    <Entry line={line}>
      <div
        className="text-muted-foreground mt-1.5 flex flex-wrap items-baseline gap-2 text-xs"
        data-testid="design-name"
      >
        {/* The heading is the author's own words, drawn as the file keeps them — like the
            symptom above it, and unlike the sentence beside it, which is this app's. */}
        {title === '' ? null : <span className="text-foreground font-medium">{title}</span>}
        <span>{say('project.design.written', { ref: anchor })}</span>
      </div>
    </Entry>
  )
}

/**
 * What is shipped and unlooked-at, beside the ledger it comes from (RG293).
 *
 * A narrowing of the changelog, so it belongs among the tabs that read it — one more reading of
 * `unvalidated`, not a second window and not a filter nobody finds.
 *
 * **Newest first**, against the block order every other tab uses, for the deferred tab's reason:
 * what somebody will actually check is what they just shipped, while they still remember what it
 * was for, and the ledger's own order buries that under whatever Block A left behind.
 *
 * **An empty list is three answers**, and `validationFrom` is what tells them apart. Each gets
 * its own sentence, because *this project never asked*, *the history cannot say* and *everything
 * has a verdict* are three different things to do next.
 *
 * **Opening a row is what asks.** Nothing is asked of Claude Code for a list being scrolled past.
 */
/**
 * The sentence for each way the list is empty, by the state's own word.
 *
 * A table and not a chain of conditions, so the three stay three: *this project never asked*,
 * *the history cannot say* and *everything has a verdict* are different things to do next, and a
 * screen that folded two of them together would tell somebody the wrong one.
 */
const NOTHING_AWAITS = {
  ungoverned: 'project.validation.ungoverned',
  unplaced: 'project.validation.unplaced',
  none: 'project.validation.none',
} as const satisfies Record<Exclude<Validation['kind'], 'awaiting'>, MessageKey>

export function ValidationTab({ project }: { readonly project: OpenProject }) {
  const say = useWording()
  const listed = useAnswer(
    () => project.client.call(project.root, 'unvalidated', {}),
    `${project.root} unvalidated`,
  )
  if (listed === null || 'failed' in listed)
    return <Waiting answer={listed} empty="project.validation.none" />

  const validation = validationFrom(listed.value)
  if (validation.kind !== 'awaiting')
    return <BentoEmptyState title={say(NOTHING_AWAITS[validation.kind])} />

  return (
    <>
      <p className="text-muted-foreground mb-2 text-xs" data-testid="validation-order">
        {/* The order, and how much of the ledger is already answered — the engine's own count,
            beside the list rather than summed from it. */}
        {counted(say, [
          ['project.validation.newest', null],
          ['project.validation.validated', validation.validated],
        ])}
      </p>
      <Entries>
        {validation.rows.map((row) => (
          <li
            key={row.id}
            className="grid grid-cols-[6rem_minmax(0,1fr)_auto] gap-x-4 gap-y-2 border-t px-5 py-3 first:border-t-0 max-sm:grid-cols-1"
            data-testid="unvalidated"
            data-id={row.id}
          >
            <span className="pt-0.5 font-mono text-xs font-semibold">{row.id}</span>
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <span className="bg-muted text-muted-foreground rounded px-1.5 text-xs font-semibold">
                  {row.block}
                </span>
                <span className="text-sm font-medium [overflow-wrap:anywhere]">{row.symptom}</span>
              </div>
              {/* Null where the history could not say which commit shipped it, which is a state
                  and not a blank: a screen that drew an empty hash would be inventing one. */}
              {row.commit === null ? null : (
                <div className="text-muted-foreground mt-1 font-mono text-[13px]">
                  {say('project.validation.shipped.in', { commit: row.commit.slice(0, 8) })}
                </div>
              )}
            </div>
            <div className="flex items-start max-sm:justify-start">
              <Checking root={project.root} id={row.id} />
            </div>
          </li>
        ))}
      </Entries>
    </>
  )
}

export function ImprovementsTab({ project }: { readonly project: OpenProject }) {
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
        <DesignRow key={line.id} project={project} line={line} anchor={line.ref ?? ''} />
      ))}
    </Entries>
  )
}
