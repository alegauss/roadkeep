import {
  briefToCopy,
  folderName,
  alreadyRunning,
  handoverOf,
  mayHandOver,
  hopsOpening,
  opensHere,
  quotedFirst,
  routeOf,
  whereDesignLives,
  reasonOf,
  type Chain,
  type Design,
  type DepStanding,
  type HandedOver,
  type SessionRecord,
  type TaskDetail,
  type Translate,
  type Whereabouts,
} from '@rk/core'
import { Button } from '@viglet/viglet-design-system'
import { BentoEmptyState, BentoHero, BentoPanel } from '@viglet/viglet-design-system/bento'
import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { projectPath, sessionPath, taskPath } from './areas'
import { getBridge } from './bridge'
import { PanelTitle } from './forms'
import { Glyph, Pill, type Intent } from './marks'
import { useTask, type OpenedTask } from './useTask'
import { useWording } from './wording'

/**
 * One line, as brief joins it (RG150). `docs/design/Tarefa.dc.html` is the drawing, reached
 * from a row's Open on the project surface.
 *
 * **One read.** Everything drawn is the brief `useTask` asked for, laid out by `core`: the
 * hero is the line, the left panel is its design as the file stores it — the file's wrapping
 * kept, `**` and `[[…]]` literal, no Markdown parsed — and the right column is what starting it
 * costs. Readiness is the engine's word, the chains are the routes the brief resolved, and the
 * marker and the claim sit side by side where they can disagree (RG74).
 *
 * **What binds the line** is the block's criteria the brief carried and the non-goals, the
 * ones this design quotes first: a quoted lead is one its author already reasoned about.
 *
 * Copy the brief hands on the line as the file writes it and its design as stored, both the
 * file's own text. Hand to Claude Code takes the line and starts a session from that brief
 * (RG153), and a held line names its holder instead of offering one. A paused line opens here
 * too, with the store's entry and the verb that brings it back (RG80).
 */

/** What shipping inside this backlog can do about a dep, in the design system's intents. */
const STANDING: Readonly<Record<DepStanding, Intent>> = {
  settled: 'on',
  waiting: 'warn',
  never: 'error',
}

/** A card's heading: small, spaced, and in the catalogue like every other word. */
type Copying = { readonly kind: 'idle' } | { readonly kind: 'copied' } | { readonly failed: string }

const IDLE: Copying = { kind: 'idle' }

function CopyBrief({ detail }: { readonly detail: TaskDetail }) {
  const say = useWording()
  const [copying, setCopying] = useState<Copying>(IDLE)
  const copy = useCallback(() => {
    const text = briefToCopy(detail)
    // Through a promise from the start, so a window with no clipboard at all is a refusal
    // said beside the button and not an exception out of a click.
    void Promise.resolve()
      .then(() => navigator.clipboard.writeText(text))
      .then(
        () => {
          setCopying({ kind: 'copied' })
        },
        (error: unknown) => {
          setCopying({ failed: error instanceof Error ? error.message : '' })
        },
      )
  }, [detail])

  let said: string | null = null
  if ('failed' in copying) said = say('task.copy.failed', { reason: copying.failed })
  else if (copying.kind === 'copied') said = say('task.copied')

  return (
    <div className="flex flex-col items-end gap-1">
      <Button variant="outline" size="sm" onClick={copy}>
        {say('task.copy')}
      </Button>
      <output data-testid="copied" className="text-muted-foreground min-h-4 text-xs">
        {said}
      </output>
    </div>
  )
}

/** Why a line was not handed over, in this app's words for what the far side answered. */
function saidOfHanded(handed: Exclude<HandedOver, { readonly kind: 'started' }>, say: Translate) {
  if (handed.kind === 'held') {
    const holder = handed.held[0]
    return say('task.held.named', { by: holder?.by ?? '', since: holder?.since ?? '' })
  }
  if (handed.kind === 'unready') return say('task.handOver.unready', handed)
  if (handed.kind === 'refused') return say('task.handOver.refused', { reason: handed.said })
  if (handed.kind === 'unavailable') {
    return say('task.handOver.unavailable', {
      tried: handed.tried.map((command) => command.join(' ')).join(', '),
    })
  }
  return say('task.handOver.withheld', handed)
}

type Handing =
  | { readonly kind: 'idle' }
  | { readonly kind: 'handing' }
  | { readonly kind: 'said'; readonly text: string }

const NOT_HANDING: Handing = { kind: 'idle' }

/**
 * Hand to Claude Code, and the way back to a session already started from this line (RG153).
 *
 * **A held line is named and nothing is offered**, which is block F's third criterion, and the
 * same answer comes back from the far side — the check here is what a reader sees, and the one
 * there is what holds. A line the engine does not call ready offers nothing either: the
 * readiness card beside this says what it is waiting for.
 */
function HandOver({ root, task }: { readonly root: string; readonly task: OpenedTask }) {
  const say = useWording()
  const navigate = useNavigate()
  const line = task.detail.payload
  const id = line.id
  const handover = handoverOf(line)
  const [handing, setHanding] = useState<Handing>(NOT_HANDING)
  const [session, setSession] = useState<SessionRecord | null>(null)
  // Handing over takes as long as resolving an agent and starting a process, which is long
  // enough to press Back — and a window moved to a session after that is a window moved
  // somewhere nobody chose (RG190). Every read here guards; this is a callback, so it needs
  // its own.
  const onScreen = useRef(true)
  useEffect(() => {
    onScreen.current = true
    return () => {
      onScreen.current = false
    }
  }, [])

  useEffect(() => {
    const bridge = getBridge()
    if (bridge === undefined) return undefined
    let live = true
    const stillHere = (): boolean => live
    void bridge.sessions().then(
      (all) => {
        if (!stillHere()) return
        setSession(all.findLast((one) => one.root === root && one.id === id) ?? null)
      },
      // A bridge that will not say is the same as one holding none: this offers a way back
      // to a session and never a reason the line cannot be handed over.
      () => undefined,
    )
    return () => {
      live = false
    }
  }, [root, id])

  const hand = useCallback(() => {
    const bridge = getBridge()
    if (bridge === undefined) return
    setHanding({ kind: 'handing' })
    void bridge.handOver(root, id).then(
      (handed) => {
        if (handed.kind !== 'started') {
          setHanding({ kind: 'said', text: saidOfHanded(handed, say) })
          return
        }
        setSession(handed.session)
        setHanding(NOT_HANDING)
        // The session did start and is on the sessions list either way; what is withheld is
        // taking a reader somewhere they have already left.
        if (onScreen.current) void navigate(sessionPath(root, id, handed.session.key))
      },
      (cause: unknown) => {
        const reason = cause instanceof Error ? cause.message : ''
        setHanding({ kind: 'said', text: say('task.handOver.withheld', { reason }) })
      },
    )
  }, [root, id, navigate, say])

  const holder = handover.held[0]
  return (
    <div className="flex flex-col items-end gap-1">
      {session === null ? null : (
        <Button asChild variant="outline" size="sm">
          <Link to={sessionPath(root, id, session.key)}>{say('task.session.open')}</Link>
        </Button>
      )}
      {/* Not offered where this window already has a session running on the line: the
          engine would refuse the second claim, and the offer is what is wrong (RG175). */}
      {holder === undefined && !alreadyRunning(session) && mayHandOver(handover) ? (
        <Button size="sm" onClick={hand} disabled={handing.kind === 'handing'}>
          {say('task.handOver')}
        </Button>
      ) : null}
      <output className="text-muted-foreground max-w-72 text-right text-xs">
        {holder === undefined
          ? null
          : say('task.held.named', { by: holder.by, since: holder.since })}
        {handing.kind === 'handing' ? say('task.handing') : null}
        {handing.kind === 'said' ? handing.text : null}
      </output>
    </div>
  )
}

/** The count against the limit, in the engine's numbers and its unit. */
function Counted({ design }: { readonly design: Design }) {
  const say = useWording()
  const budget = design.budget
  if (budget !== null && budget.written && budget.limit > 0) {
    const fill = { taken: budget.taken, limit: budget.limit, unit: budget.unit, over: budget.over }
    return <span>{say(budget.over > 0 ? 'task.design.over' : 'task.design.budget', fill)}</span>
  }
  return design.words === 0 ? null : (
    <span>{say('task.design.count', { words: design.words })}</span>
  )
}

/** The design as the file stores it: its heading, where it lives, and the prose whole. */
function DesignPanel({ design }: { readonly design: Design }) {
  const say = useWording()
  if (design.state === 'absent') {
    return (
      <BentoPanel className="min-w-0" contentClassName="p-6">
        <BentoEmptyState
          title={say('task.design.none')}
          description={design.absence === '' ? undefined : design.absence}
        />
      </BentoPanel>
    )
  }

  return (
    <BentoPanel className="min-w-0" contentClassName="p-6">
      <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
        <h2 className="text-base font-semibold">{design.title}</h2>
        <span className="text-muted-foreground font-mono text-xs wrap-anywhere">
          {say('task.design.where', { anchor: design.anchor, where: whereDesignLives(design) })}
        </span>
      </div>
      <p className="text-muted-foreground mt-1 flex flex-wrap gap-x-2 text-xs">
        <Counted design={design} />
        <span>{say('task.design.face')}</span>
      </p>
      <pre
        data-testid="design"
        className="text-foreground mt-4 font-sans text-[13.5px] leading-relaxed whitespace-pre-wrap wrap-anywhere"
      >
        {design.prose}
      </pre>
    </BentoPanel>
  )
}

/**
 * One route, drawn hop by hop so each hop that opens is a way to its line (RG173).
 *
 * The arrow between them is the one thing composed here, as `routeOf` composes it for a
 * route drawn whole; the head is this line itself and is drawn plainly, since a link to the
 * screen you are on is not a way anywhere.
 */
function Route({ root, chain }: { readonly root: string; readonly chain: Chain }) {
  const say = useWording()
  const opening = hopsOpening(chain)

  return (
    <p className="mt-2 text-xs" data-testid="chain">
      <span className="font-mono">
        {chain.path[0] ?? ''}
        {chain.hops.map((hop, at) => (
          <span key={hop}>
            {' → '}
            {opening[at] === true ? (
              <Link
                to={taskPath(root, hop)}
                aria-label={say('task.dep.open', { id: hop })}
                data-testid="hop-open"
              >
                {hop}
              </Link>
            ) : (
              <span data-testid="hop-text">{hop}</span>
            )}
          </span>
        ))}
      </span>{' '}
      <span className="text-muted-foreground">{chain.detail}</span>
    </p>
  )
}

/** Readiness in the engine's word, each dep with its own, the routes, and what a ship frees. */
function ReadinessCard({ task, root }: { readonly task: OpenedTask; readonly root: string }) {
  const say = useWording()
  const { detail, graph } = task
  const line = detail.payload

  return (
    <BentoPanel contentClassName="p-5">
      <div className="mb-3">
        {line.shipped ? (
          <Pill intent="on">{say('task.shipped')}</Pill>
        ) : (
          <Pill intent={graph.readiness === 'ready' ? 'on' : 'warn'}>
            {say('task.readiness', { readiness: graph.readiness })}
          </Pill>
        )}
      </div>
      <div className="flex flex-wrap items-center gap-2 text-xs">
        {graph.edges.length === 0 ? (
          <span className="text-muted-foreground">{say('project.deps.none')}</span>
        ) : (
          graph.edges.map((edge) => {
            const pill = (
              <Pill intent={STANDING[edge.standing]}>
                <span className="font-mono">{edge.dep}</span>
                <span>{edge.status}</span>
              </Pill>
            )
            // A dep this window can open is a way to its line; one it cannot stays text,
            // because a link that opened a refusal would draw it as merely missing (RG173).
            return opensHere(edge) ? (
              <Link
                key={edge.dep}
                to={taskPath(root, edge.dep)}
                aria-label={say('task.dep.open', { id: edge.dep })}
                data-testid="dep-open"
              >
                {pill}
              </Link>
            ) : (
              <span key={edge.dep} data-testid="dep-text">
                {pill}
              </span>
            )
          })
        )}
      </div>
      {line.requires.length === 0 ? null : (
        <p className="text-muted-foreground mt-2 text-xs">
          {say('task.requires', { what: line.requires.join(', ') })}
        </p>
      )}
      {graph.chains.map((chain) => (
        <Route key={routeOf(chain)} root={root} chain={chain} />
      ))}
      {graph.unblocks === null ? null : (
        <p className="text-muted-foreground mt-2 text-xs">
          {say('task.unblocks', { count: graph.unblocks.count, of: graph.unblocks.of })}
        </p>
      )}
    </BentoPanel>
  )
}

/** The marker and the claim, and whether they agree — drawn, never settled here (RG74). */
function UnderwayCard({ task }: { readonly task: OpenedTask }) {
  const say = useWording()
  const { underway: state, detail, asksWorking } = task
  const held = state.held

  let said = say('task.underway.idle')
  if (held !== null && state.marked) {
    said = say('task.underway.working', { by: held.by, since: held.since })
  } else if (held !== null) {
    said = say('task.underway.held', { by: held.by, since: held.since })
  } else if (state.marked) {
    said = say('task.underway.started')
  }

  return (
    <BentoPanel contentClassName="p-5">
      <PanelTitle>{say('task.underway')}</PanelTitle>
      <div className="flex items-center gap-2 text-sm">
        <Glyph>{detail.payload.status}</Glyph>
        <span>{said}</span>
      </div>
      {asksWorking ? (
        <div className="mt-2 text-xs">
          {state.disagree ? (
            <Pill intent="warn">{say('task.underway.disagree')}</Pill>
          ) : (
            <span className="text-muted-foreground">{say('task.underway.agree')}</span>
          )}
        </div>
      ) : null}
    </BentoPanel>
  )
}

/** A group of leads as chips. The group's label says which, so no colour carries it alone. */
function Leads({ leads, quoted }: { readonly leads: readonly string[]; readonly quoted: boolean }) {
  const face = quoted ? 'border font-medium' : 'bg-muted text-muted-foreground'
  return (
    <ul className="flex flex-wrap gap-1.5">
      {leads.map((lead) => (
        <li key={lead} className={`rounded-md px-2 py-0.5 text-xs ${face}`}>
          {lead}
        </li>
      ))}
    </ul>
  )
}

/** The block's criteria the brief carried, and the non-goals, the quoted ones first. */
function BindsCard({ detail }: { readonly detail: TaskDetail }) {
  const say = useWording()
  const line = detail.payload
  const bounds = quotedFirst(detail)

  return (
    <BentoPanel contentClassName="p-5">
      {/* The line's own leads first, and apart: these are the ones `ship --checked` names,
          and merging them with the block's would assert the block's finish line about this
          one line (RG174). */}
      {line.doneWhenOwn.length === 0 ? null : (
        <section className="mb-4" data-testid="own-criteria">
          <PanelTitle>{say('task.criteria.own')}</PanelTitle>
          <ul className="flex flex-col gap-1.5">
            {line.doneWhenOwn.map((lead) => (
              <li key={lead} className="text-[13px] font-medium">
                {lead}
                {line.doneWhenFolded[lead] === undefined ? null : (
                  <span className="text-muted-foreground ml-2 text-xs font-normal">
                    {say('task.criteria.folded', { id: line.doneWhenFolded[lead] })}
                  </span>
                )}
              </li>
            ))}
          </ul>
          {line.doneWhenOwnElided > 0 ? (
            <p className="text-muted-foreground mt-1 text-xs">
              {say('task.criteria.elided', { count: line.doneWhenOwnElided })}
            </p>
          ) : null}
        </section>
      )}
      <PanelTitle>{say('task.binds', { block: line.block })}</PanelTitle>
      {line.doneWhen.length === 0 ? (
        <p className="text-muted-foreground text-xs">{say('task.criteria.none')}</p>
      ) : (
        <ul className="flex flex-col gap-1.5">
          {line.doneWhen.map((lead) => (
            <li key={lead} className="text-[13px] font-medium">
              {lead}
            </li>
          ))}
        </ul>
      )}
      {line.doneWhenElided > 0 ? (
        <p className="text-muted-foreground mt-1 text-xs">
          {say('task.criteria.elided', { count: line.doneWhenElided })}
        </p>
      ) : null}

      {bounds.quoted.length === 0 ? null : (
        <section className="mt-4" data-testid="quoted">
          <PanelTitle>{say('task.quoted')}</PanelTitle>
          <Leads leads={bounds.quoted} quoted />
        </section>
      )}
      <section className="mt-4" data-testid="bounds">
        <PanelTitle>{say('task.bounds')}</PanelTitle>
        <Leads leads={bounds.rest} quoted={false} />
        {bounds.elided > 0 ? (
          <p className="text-muted-foreground mt-1.5 text-xs">
            {say('task.bounds.elided', { count: bounds.elided })}
          </p>
        ) : null}
      </section>
    </BentoPanel>
  )
}

/** Where a line went when brief refused it: the store's entry and the way back, or nothing. */
function Elsewhere({ whereabouts }: { readonly whereabouts: Whereabouts }) {
  const say = useWording()
  const { filing, pause, back, id } = whereabouts

  if (filing === 'paused' && pause !== null) {
    return (
      <BentoPanel contentClassName="p-6">
        <PanelTitle>{say('task.paused')}</PanelTitle>
        <div className="flex flex-wrap items-center gap-2">
          <Glyph>{pause.marker}</Glyph>
          <span className="bg-muted text-muted-foreground rounded px-1.5 text-xs font-semibold">
            {pause.block}
          </span>
          <span className="text-sm font-medium wrap-anywhere">{pause.symptom}</span>
        </div>
        <p className="text-muted-foreground mt-2 text-[13px] wrap-anywhere">{pause.why}</p>
        {back === null ? null : (
          <p className="mt-3 font-mono text-xs">
            {say('task.paused.back', { verb: back.verb, id })}
          </p>
        )}
      </BentoPanel>
    )
  }

  let title = say('task.refused', { reason: whereabouts.said })
  if (filing === 'unfiled') title = say('task.unfiled', { id })
  if (filing === 'unknown') title = say('task.unknown')
  return (
    <BentoPanel contentClassName="p-6">
      <BentoEmptyState
        title={title}
        description={filing === 'unknown' ? whereabouts.said : undefined}
      />
    </BentoPanel>
  )
}

/** The block, what the marker is for here, then the line's symptom and why whole. */
function Heading({ task }: { readonly task: OpenedTask }) {
  const say = useWording()
  const line = task.detail.payload
  return (
    <span className="flex flex-col gap-1">
      <span className="flex flex-wrap items-center gap-2 text-xs">
        <span className="font-semibold tracking-wider uppercase">
          {say('task.block', { block: line.block })}
        </span>
        {task.meaning === '' ? null : <span className="text-muted-foreground">{task.meaning}</span>}
      </span>
      <span className="text-foreground text-base font-medium wrap-anywhere">{line.symptom}</span>
      <span className="text-[13px] wrap-anywhere">{line.why}</span>
    </span>
  )
}

export function Task() {
  const say = useWording()
  const params = useParams()
  const root = decodeURIComponent(params['root'] ?? '')
  const id = decodeURIComponent(params['id'] ?? '')
  const view = useTask(root, id)
  const task = view.kind === 'open' ? view : null

  let subtitle: ReactNode = null
  if (view.kind === 'absent') subtitle = say('transport.absent')
  if (view.kind === 'opening') subtitle = say('task.opening')
  if (view.kind === 'refused')
    subtitle = say('task.refused', { reason: reasonOf(view.unreadable, say) })
  if (task !== null) subtitle = <Heading task={task} />
  // Built once per answer: the hero takes them as props, and a fresh element every render
  // would redraw it for nothing.
  const leading = useMemo(
    () =>
      task === null ? undefined : (
        <span className="text-2xl">
          <Glyph>{task.detail.payload.status}</Glyph>
        </span>
      ),
    [task],
  )
  const trailing = useMemo(
    () =>
      task === null ? undefined : (
        <div className="flex items-start gap-3">
          <CopyBrief detail={task.detail} />
          <HandOver root={root} task={task} />
        </div>
      ),
    [root, task],
  )

  return (
    <>
      <BentoHero
        backTo={projectPath(root)}
        backLabel={view.kind === 'open' ? view.name : folderName(root)}
        leading={leading}
        title={id}
        subtitle={subtitle}
        trailing={trailing}
      />
      {task === null ? null : (
        <div className="grid items-start gap-5 lg:grid-cols-[minmax(0,1fr)_24rem]">
          <DesignPanel design={task.design} />
          <div className="flex min-w-0 flex-col gap-3">
            <ReadinessCard task={task} root={root} />
            <UnderwayCard task={task} />
            <BindsCard detail={task.detail} />
          </div>
        </div>
      )}
      {view.kind === 'elsewhere' ? <Elsewhere whereabouts={view.whereabouts} /> : null}
    </>
  )
}
