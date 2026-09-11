import {
  folderName,
  NO_FILTER,
  refusedSummary,
  withField,
  type BacklogFilter,
  type BlockStanding,
  type DepsPayload,
  type OpenProject,
  type TaskLine,
  type Underway,
} from '@rk/core'
import { Button } from '@viglet/viglet-design-system'
import { BentoEmptyState, BentoHero, BentoPanel } from '@viglet/viglet-design-system/bento'
import { useCallback, useState, type ReactNode } from 'react'
import { useParams } from 'react-router-dom'

import { HOME_ROUTE } from './areas'
import { Glyph, Pill } from './marks'
import { ChangelogTab, DecisionsTab, DeferredTab, ImprovementsTab } from './ProjectTabs'
import { useProject, type OpenedSurface } from './useProject'
import { useWording } from './wording'

/**
 * One backlog, as rows (RG148). `docs/design/Projeto.dc.html` is the drawing, reached from
 * a portfolio row.
 *
 * **Every narrowing is the verb's.** A block chip, a marker and a requirement each become an
 * argument `list` takes, through `filterAsInput`, so the rows are what `roadkeep list`
 * returned for that narrowing and never a filter run in React. Choosing the same chip again
 * clears it.
 *
 * **A row keeps the symptom and the why whole**, since a symptom is what a reader scans and
 * §RG63 chose rows to keep it at full length. Its deps are drawn as the engine spells them,
 * with their own marks, and whether a design is written is the line's pointer.
 *
 * **Readiness is the engine's word** — `deps` for each line, never worked out here. A line
 * carrying the working marker says, beside it, whether anybody holds it (RG74): the marker
 * and the claim are two facts, and where they disagree that is drawn and not resolved.
 *
 * Absent rather than disabled: Run the gate and File a line, which are RG152's and RG151's,
 * and Open on a row, which is RG150's. The other governed files are tabs of their own (RG149),
 * and a role this window does not read is a tab drawn disabled rather than left out.
 */

/**
 * The governed roles as tabs, the roadmap first: it is the one this surface reads, and the
 * others follow in the order `config` gave them.
 */
function tabsOf(roles: readonly string[]): string[] {
  return [
    ...roles.filter((role) => role === 'roadmap'),
    ...roles.filter((role) => role !== 'roadmap'),
  ]
}

/** A chip in a group of narrowings, pressed where it is the one in force. */
function Choice({
  value,
  active,
  onPick,
  children,
}: {
  readonly value: string
  readonly active: boolean
  readonly onPick: (value: string) => void
  readonly children: ReactNode
}) {
  const choose = useCallback(() => {
    onPick(value)
  }, [value, onPick])

  return (
    <Button
      variant={active ? 'default' : 'outline'}
      size="sm"
      className="rounded-full"
      aria-pressed={active ? 'true' : 'false'}
      onClick={choose}
    >
      {children}
    </Button>
  )
}

function BlockLabel({ block }: { readonly block: BlockStanding }) {
  const say = useWording()
  const finished = block.open === 0 && block.state === 'finished'
  return (
    <span className="inline-flex items-center gap-1.5">
      <span className="font-semibold">{block.block}</span>
      {block.title === '' ? null : (
        <span className="max-w-48 truncate font-normal" title={block.title}>
          {block.title}
        </span>
      )}
      <span className={finished ? 'text-muted-foreground' : 'tabular-nums'}>
        {finished ? say('project.block.finished') : block.open}
      </span>
    </span>
  )
}

/** Readiness in the engine's words, and what the engine says holds it back. */
function Readiness({
  deps,
  state,
}: {
  readonly deps: DepsPayload | undefined
  readonly state: Underway | undefined
}) {
  const say = useWording()
  if (deps === undefined) return <Pill intent={null}>{say('project.readiness.asking')}</Pill>

  return (
    <div className="flex flex-col items-start gap-1">
      <Pill intent={deps.readiness === 'ready' ? 'on' : 'warn'}>{deps.readiness}</Pill>
      {deps.blockers.length > 0 ? (
        <span className="text-muted-foreground text-xs">
          {say('project.waiting', { ids: deps.blockers.join(', ') })}
        </span>
      ) : null}
      {deps.cycle.length > 0 ? (
        <span className="text-muted-foreground text-xs">
          {say('project.cycle', { ids: deps.cycle.join(', ') })}
        </span>
      ) : null}
      {state?.disagree === true && state.held === null ? (
        <>
          <Pill intent="warn">{say('project.unheld')}</Pill>
          <span className="text-muted-foreground text-xs">{say('project.unheld.why')}</span>
        </>
      ) : null}
      {state?.held === null || state === undefined ? null : (
        <span className="text-muted-foreground text-xs">
          {say('project.held', { by: state.held.by })}
        </span>
      )}
    </div>
  )
}

function Line({
  line,
  deps,
  state,
}: {
  readonly line: TaskLine
  readonly deps: DepsPayload | undefined
  readonly state: Underway | undefined
}) {
  const say = useWording()
  return (
    <li
      className="grid grid-cols-[6rem_minmax(0,1fr)_11rem] gap-4 border-t px-5 py-3 first:border-t-0"
      data-testid="line"
      data-id={line.id}
    >
      <div className="flex items-start gap-2 pt-0.5">
        <Glyph>{line.status}</Glyph>
        <span className="font-mono text-xs font-semibold">{line.id}</span>
      </div>
      <div className="min-w-0">
        <div className="text-sm font-medium [overflow-wrap:anywhere]">{line.symptom}</div>
        <div className="text-muted-foreground mt-1 text-[13px] [overflow-wrap:anywhere]">
          {line.why}
        </div>
        <div className="mt-1.5 flex flex-wrap items-center gap-2 text-xs">
          <span className="bg-muted text-muted-foreground rounded px-1.5 font-semibold">
            {line.block}
          </span>
          {line.deps.length === 0 ? (
            <span className="text-muted-foreground">{say('project.deps.none')}</span>
          ) : (
            line.deps.map((dep) => (
              <span key={dep} className="font-mono">
                {dep}
              </span>
            ))
          )}
          <span className="text-muted-foreground">
            {line.ref === null
              ? say('project.design.none')
              : say('project.design.written', { ref: line.ref })}
          </span>
        </div>
      </div>
      <Readiness deps={deps} state={state} />
    </li>
  )
}

/** The roadmap tab: the three narrowings, and the rows `list` answered for them. */
function Roadmap({
  surface,
  filter,
  onFilter,
}: {
  readonly surface: OpenedSurface
  readonly filter: BacklogFilter
  readonly onFilter: (next: BacklogFilter) => void
}) {
  const say = useWording()
  const pickBlock = useCallback(
    (block: string) => {
      onFilter(withField(filter, 'block', filter.block === block ? undefined : block))
    },
    [filter, onFilter],
  )
  const pickMarker = useCallback(
    (marker: string) => {
      onFilter(withField(filter, 'marker', filter.marker === marker ? undefined : marker))
    },
    [filter, onFilter],
  )
  const pickRequirement = useCallback(
    (requirement: string) => {
      const held = filter.have?.[0] === requirement
      onFilter(withField(filter, 'have', held ? undefined : [requirement]))
    },
    [filter, onFilter],
  )

  const { backlog } = surface
  const lines = backlog === null ? [] : backlog.blocks.flatMap((block) => block.lines)
  const narrower = backlog === null ? '' : refusedSummary(backlog)

  return (
    <>
      <fieldset className="m-0 flex flex-wrap items-center gap-2 border-0 p-0">
        <legend className="sr-only">{say('project.blocks')}</legend>
        {surface.blocks.map((block) => (
          <Choice
            key={block.block}
            value={block.block}
            active={filter.block === block.block}
            onPick={pickBlock}
          >
            <BlockLabel block={block} />
          </Choice>
        ))}
      </fieldset>

      <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
        <fieldset className="m-0 flex flex-wrap items-center gap-2 border-0 p-0">
          <legend className="text-muted-foreground float-left mr-1 text-xs">
            {say('project.filter.marker')}
          </legend>
          {surface.markers.map((marker) => (
            <Choice
              key={marker}
              value={marker}
              active={filter.marker === marker}
              onPick={pickMarker}
            >
              <Glyph>{marker}</Glyph>
            </Choice>
          ))}
        </fieldset>
        {surface.choices.requirements.length === 0 ? null : (
          <fieldset className="m-0 flex flex-wrap items-center gap-2 border-0 p-0">
            <legend className="text-muted-foreground float-left mr-1 text-xs">
              {say('project.filter.requirement')}
            </legend>
            {surface.choices.requirements.map((requirement) => (
              <Choice
                key={requirement}
                value={requirement}
                active={filter.have?.[0] === requirement}
                onPick={pickRequirement}
              >
                {requirement}
              </Choice>
            ))}
          </fieldset>
        )}
        <span className="text-muted-foreground ml-auto text-xs">{say('project.filter.note')}</span>
      </div>

      {narrower === '' ? null : <p className="text-muted-foreground text-xs">{narrower}</p>}

      {backlog === null ? (
        <p className="text-muted-foreground text-sm">{say('project.listing')}</p>
      ) : lines.length === 0 ? (
        <BentoEmptyState title={say('project.none')} />
      ) : (
        <BentoPanel className="overflow-hidden" contentClassName="p-0">
          <ul>
            {lines.map((line) => (
              <Line
                key={line.id}
                line={line}
                deps={surface.readiness[line.id]}
                state={surface.underway[line.id]}
              />
            ))}
          </ul>
        </BentoPanel>
      )}
    </>
  )
}

/** The governed roles this window reads, each with the tab that draws it. */
const TABS: Readonly<Record<string, (props: { readonly project: OpenProject }) => ReactNode>> = {
  changelog: ChangelogTab,
  decisions: DecisionsTab,
  deferred: DeferredTab,
  improvements: ImprovementsTab,
}

function RoleTab({
  role,
  active,
  readable,
  onPick,
}: {
  readonly role: string
  readonly active: boolean
  readonly readable: boolean
  readonly onPick: (role: string) => void
}) {
  const say = useWording()
  const choose = useCallback(() => {
    onPick(role)
  }, [role, onPick])

  return (
    <button
      type="button"
      role="tab"
      aria-selected={active ? 'true' : 'false'}
      disabled={!readable}
      title={readable ? undefined : say('project.tab.unread')}
      onClick={choose}
      className={`-mb-px px-3 py-2 text-sm disabled:opacity-50 ${
        active ? 'border-primary border-b-2 font-semibold' : 'text-muted-foreground'
      }`}
    >
      {role}
    </button>
  )
}

/** The surface once the project opened: a tab per governed file, the roadmap first. */
function Opened({
  surface,
  filter,
  onFilter,
}: {
  readonly surface: OpenedSurface
  readonly filter: BacklogFilter
  readonly onFilter: (next: BacklogFilter) => void
}) {
  const say = useWording()
  const [role, setRole] = useState('roadmap')
  const pick = useCallback((next: string) => {
    setRole(next)
  }, [])
  const Tab = TABS[role]

  return (
    <>
      <div
        role="tablist"
        aria-label={say('project.roles')}
        className="flex flex-wrap gap-1 border-b"
      >
        {tabsOf(surface.choices.roles).map((one) => (
          <RoleTab
            key={one}
            role={one}
            active={one === role}
            readable={one === 'roadmap' || Object.hasOwn(TABS, one)}
            onPick={pick}
          />
        ))}
      </div>
      {role === 'roadmap' || Tab === undefined ? (
        <Roadmap surface={surface} filter={filter} onFilter={onFilter} />
      ) : (
        <Tab project={surface.project} />
      )}
    </>
  )
}

export function Project() {
  const say = useWording()
  const params = useParams()
  const root = decodeURIComponent(params['root'] ?? '')
  const [filter, setFilter] = useState<BacklogFilter>(NO_FILTER)
  const view = useProject(root, filter)

  let subtitle: ReactNode = say('project.opening')
  if (view.kind === 'absent') subtitle = say('transport.absent')
  if (view.kind === 'refused')
    subtitle = say('project.refused', { reason: view.unreadable.message })
  if (view.kind === 'open') {
    const stats = view.stats
    subtitle = (
      <span className="flex flex-col gap-0.5">
        <span className="font-mono text-xs">{root}</span>
        {stats === null ? null : (
          <span>
            {say('project.counts', {
              open: stats.total,
              startable: stats.startable?.startable ?? 0,
              waiting: stats.startable?.waiting ?? 0,
              uncounted: stats.uncounted,
            })}
          </span>
        )}
      </span>
    )
  }

  return (
    <>
      <BentoHero
        backTo={HOME_ROUTE}
        backLabel={say('project.back')}
        title={folderName(root)}
        subtitle={subtitle}
      />
      {view.kind === 'open' ? <Opened surface={view} filter={filter} onFilter={setFilter} /> : null}
    </>
  )
}
